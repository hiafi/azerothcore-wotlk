/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Warlock rework - Destruction pass (S2) spell/aura scripts
 * (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5, warlock-rework.DESTRUCTION.md §2.6/§7).
 * Replacement classes for stock spell_warlock.cpp bindings the Destruction tree displaces - stock
 * spell_warlock.cpp stays unedited and every class it replaces is left unbound (unbind_script,
 * WP-A's job) rather than rewritten in place (.agents/docs/upstream-merge.md).
 *
 * One class (or SpellScript/AuraScript pair) per row in DESTRUCTION.md §2.6's binding table; each
 * class's header comment cites the exact §7 subsection it implements. Script names below must
 * match WP-A's `scripted_by`/`unbind_script` calls byte for byte (case-sensitive) - see the
 * DESTRUCTION-WP-BRIEF.md checklist. `npc_warl_chaos_rift` (CreatureAI) lives here too, not in a
 * Pet/ file, because Demonology's pet file doesn't exist until S3 (DESTRUCTION.md §2.6).
 *
 * One extra class beyond the WP brief's 22-name checklist: `spell_warl_nether_protection_destruction`
 * (§11 Q23's resolved default, "+1 script class" per DESTRUCTION.md §13). WP-A's `scripted_by`
 * table does not list it (it was resolved after the brief was written) - bind it to 30302 (Nether
 * Protection r3) alongside the kept stock `-30299` binding.
 */

#include "WarlockMechanics.h"
#include "Cell.h"
#include "CellImpl.h"
#include "Containers.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "DynamicObject.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <vector>

namespace
{
    // Stock/talent ids this file needs that aren't part of the frozen WarlockMechanics.h block
    // (moved or retained-stock talents Destruction didn't mint a new id for) - duplicated here
    // rather than widening the frozen header, same shape as Affliction's own local
    // SPELL_IMMOLATE/SPELL_SHADOW_WORD_PAIN block in spell_warlock_affliction.cpp.
    constexpr uint32 SPELL_SHADOW_BOLT = 686;
    constexpr uint32 SPELL_SEARING_PAIN = 5676;
    constexpr uint32 SPELL_REPLENISHMENT = 57669;
    constexpr uint32 SPELL_EMBERSTORM_R3 = 17956;          // capstone rank - Chaos Bolt CD reduction
    constexpr uint32 SPELL_EMPOWERED_IMP_R3 = 47223;       // capstone rank - Firebolt -> instant Soul Fire
    constexpr uint32 SPELL_GLYPH_OF_CONFLAGRATE = 56235;

    constexpr uint32 EVENT_CHAOS_RIFT_BOLT = 1;
    constexpr uint32 EVENT_CHAOS_RIFT_DESPAWN = 2;
    constexpr uint32 CHAOS_RIFT_DURATION_MS = 12000;
    constexpr float CHAOS_RIFT_RANGE = 40.0f;

    // Shared by spell_warl_chaos_bolt (primary target) and spell_warl_chaos_bolt_copy (Havoc/
    // Soulburn extra targets) - DESTRUCTION.md §7.7: "perTick = hit x 0.25 / 3 / taken", the taken
    // multiplier divided out so the DoT's own live SpellDamageBonusTaken doesn't apply it twice.
    void ApplyChaoticBurn(Unit* caster, Unit* target, int32 hitDamage)
    {
        if (!caster || !target || hitDamage <= 0)
            return;

        SpellInfo const* burnInfo = sSpellMgr->AssertSpellInfo(Warlock::SPELL_CHAOTIC_BURN);
        if (!burnInfo)
            return;

        float const taken = float(target->SpellDamageBonusTaken(caster, burnInfo, 10000, DOT)) / 10000.0f;
        if (taken <= 0.0f)
            return;

        int32 const perTick = int32(float(hitDamage) * 0.25f / 3.0f / taken);
        if (perTick <= 0)
            return;

        caster->CastCustomSpell(Warlock::SPELL_CHAOTIC_BURN, SPELLVALUE_BASE_POINT0, perTick, target,
            TRIGGERED_FULL_MASK);
    }

    // Conflagrate's BeforeHit (§7.3): the *full-duration* total of a periodic effect - its live
    // per-tick amount (done-mods, SP, Emberstorm/Pyroclasm/Ruin already baked in by the engine)
    // times the number of ticks the aura's *current* (duration-modded, Kindling-included) max
    // duration actually spans. Never "ticks remaining" (QA #19-20).
    int32 ComputeFullDurationTotal(AuraEffect const* eff)
    {
        if (!eff)
            return 0;

        int32 const amplitude = eff->GetAmplitude();
        if (amplitude <= 0)
            return 0;

        Aura const* base = eff->GetBase();
        if (!base)
            return 0;

        float const ticks = float(base->GetMaxDuration()) / float(amplitude);
        return int32(float(eff->GetAmount()) * ticks);
    }
}

// ===========================================================================================
// 5740, 42223 - Rain of Fire (ground-effect snapshot rework) - DESTRUCTION.md §7.1 (R5, C5, C21,
// G9, QA #34-35)
// ===========================================================================================
class spell_warl_rain_of_fire : public SpellScript
{
    PrepareSpellScript(spell_warl_rain_of_fire);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_RAIN_OF_FIRE_TICK });
    }

    void RemoveExisting()
    {
        // One Rain of Fire per caster (SYSTEMS §13; EffectAddFarsight "remove old farsight"
        // precedent, SpellEffects.cpp:2896-2897) - a recast always tears down any earlier ground
        // effect first, so BeforeCast rather than AfterCast (G9/QA #34).
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->RemoveDynObject(Warlock::SPELL_RAIN_OF_FIRE);
        caster->RemoveAurasDueToSpell(Warlock::SPELL_RAIN_OF_FIRE, caster->GetGUID());
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_warl_rain_of_fire::RemoveExisting);
    }
};

class spell_warl_rain_of_fire_aura : public AuraScript
{
    PrepareAuraScript(spell_warl_rain_of_fire_aura);

    int32 _snapshot = 0;

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        SpellInfo const* rofInfo = GetSpellInfo();
        int32 const base = rofInfo->Effects[EFFECT_0].CalcValue(caster);
        int32 snap = int32(caster->SpellDamageBonusDone(caster, rofInfo, uint32(std::max(0, base)),
            SPELL_DIRECT_DAMAGE, EFFECT_0));

        // Ruin's aura-303 ">75%" clause is judged against the caster (the reference victim here)
        // by the native done-bonus calc above - divide it back out so §7.1's per-tick OnHit can
        // re-apply it live, per target, instead of baking in the caster's own health state.
        float const factor = Warlock::GetAuraStateDoneFactor(caster, caster, rofInfo);
        if (factor > 0.0f)
            snap = int32(float(snap) / factor);

        _snapshot = snap;
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        DynamicObject* dyn = caster->GetDynObject(Warlock::SPELL_RAIN_OF_FIRE);
        if (!dyn)
            return;

        SpellInfo const* tickInfo = sSpellMgr->AssertSpellInfo(Warlock::SPELL_RAIN_OF_FIRE_TICK);
        if (!tickInfo)
            return;

        int32 const amount = int32(float(_snapshot) * aurEff->GetFinalTickBonusMultiplier());

        SpellCastTargets targets;
        targets.SetDst(*dyn);

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, amount);

        caster->CastSpell(targets, tickInfo, &values, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(Warlock::SPELL_RAIN_OF_FIRE);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_rain_of_fire_aura::HandleApply, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_rain_of_fire_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_rain_of_fire_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

class spell_warl_rain_of_fire_tick : public SpellScript
{
    PrepareSpellScript(spell_warl_rain_of_fire_tick);

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Ruin's ">75%" clause judged per target, live (the snapshot had it divided out above) -
        // the *same* SpellInfo (5740, Rain of Fire itself, not this tick's own 42223) the apply
        // handler used to divide it out, so the two factors are symmetric even if 42223 ever
        // carries different SPELL_ATTR6 flags than 5740.
        SpellInfo const* rofInfo = sSpellMgr->AssertSpellInfo(Warlock::SPELL_RAIN_OF_FIRE);
        if (!rofInfo)
            return;

        SetHitDamage(int32(float(GetHitDamage()) * Warlock::GetAuraStateDoneFactor(caster, target, rofInfo)));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warl_rain_of_fire_tick::HandleHit);
    }
};

// ===========================================================================================
// 200978 - Chaos Rift - DESTRUCTION.md §7.2 (R1, G4, G5, QA #1-7, #12)
// ===========================================================================================
class spell_warl_chaos_rift : public SpellScript
{
    PrepareSpellScript(spell_warl_chaos_rift);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_RIFT_BOLT });
    }

    void SummonRift(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        float const angle = roll_chance_i(50) ? float(M_PI) / 2.0f : -(float(M_PI) / 2.0f);
        Position const pos = caster->GetNearPosition(2.0f, angle);

        // TEMPSUMMON_MANUAL_DESPAWN: the AI owns the lifetime end-to-end (bolt schedule, owner
        // gone/dead/other map) - see npc_warl_chaos_rift below, which also schedules its own
        // EVENT_CHAOS_RIFT_DESPAWN as a backstop (bugs-and-fixes: MANUAL_DESPAWN never times out on
        // its own, TemporarySummon.cpp:70-79).
        caster->SummonCreature(Warlock::NPC_CHAOS_RIFT, pos, TEMPSUMMON_MANUAL_DESPAWN);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_warl_chaos_rift::SummonRift, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// Frozen Orb precedent (spell_mage.cpp, npc_mage_frozen_orb): a plain TempSummon has no
// SUMMONEDBY field / spell-mod owner (TemporarySummon.cpp:204-240), so its own casts never
// register/spend the warlock's charged SpellMods (§7.9) - store the owner GUID and cast with an
// explicit original-caster override instead (PLAN §3.9).
class npc_warl_chaos_rift : public CreatureAI
{
public:
    explicit npc_warl_chaos_rift(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* owner = summoner->ToUnit();
        if (!owner)
            return;

        _ownerGUID = owner->GetGUID();
        me->SetFaction(owner->GetFaction());
        // bugs-and-fixes: "A plain (non-Guardian) summoned Creature can't attack faction-neutral
        // targets a real player could" - without this the Rift is stuck on the strict CvC
        // attackability branch.
        me->SetUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED);
        // bugs-and-fixes: "IsTrigger() creatures floor their effective level at the triggered
        // spell's own SpellLevel" - the template's default level 1 would resist almost everything
        // without this (same fix pet_priest.cpp's Lightwell and npc_mage_frozen_orb apply).
        me->SetLevel(owner->GetLevel(), false);

        // Snapshot once at summon (QA #1) - later haste changes don't retune an already-running Rift.
        float const castSpeed = owner->GetFloatValue(UNIT_MOD_CAST_SPEED);
        _interval = castSpeed > 0.0f ? uint32(2000.0f * castSpeed) : 2000;
        if (!_interval)
            _interval = 2000;

        // Whole intervals only (QA #4): 6 bolts at 0 haste, more with haste, never a partial tick.
        uint32 const bolts = CHAOS_RIFT_DURATION_MS / _interval;
        for (uint32 k = 1; k <= bolts; ++k)
            _events.ScheduleEvent(EVENT_CHAOS_RIFT_BOLT, Milliseconds(k * _interval));
        _events.ScheduleEvent(EVENT_CHAOS_RIFT_DESPAWN, Milliseconds(CHAOS_RIFT_DURATION_MS + 1));
    }

    void UpdateAI(uint32 diff) override
    {
        // Never moves, never melees (no UpdateVictim) - just checks the owner is still around.
        Unit* owner = ObjectAccessor::GetUnit(*me, _ownerGUID);
        if (!owner || !owner->IsInWorld() || !owner->IsAlive() || owner->GetMap() != me->GetMap())
        {
            me->DespawnOrUnsummon();
            return;
        }

        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            if (eventId == EVENT_CHAOS_RIFT_BOLT)
                FireBolt(owner);
            else if (eventId == EVENT_CHAOS_RIFT_DESPAWN)
                me->DespawnOrUnsummon();
        }
    }

private:
    void FireBolt(Unit* owner)
    {
        Unit* havocTarget = Warlock::GetHavocTarget(owner);

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(me, owner, CHAOS_RIFT_RANGE);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(me, nearby, check);
        Cell::VisitObjects(me, searcher, CHAOS_RIFT_RANGE);

        nearby.remove_if([&](Unit* unit)
        {
            return unit == havocTarget || !unit->IsAlive() || !owner->IsValidAttackTarget(unit) ||
                   !unit->IsInCombatWith(owner) || !me->IsWithinLOSInMap(unit) ||
                   (!unit->HasAura(Warlock::SPELL_IMMOLATE, owner->GetGUID()) &&
                    !unit->HasAura(Warlock::SPELL_CONFLAGRATE, owner->GetGUID()));
        });

        Unit* target = nullptr;
        bool fallback = false;
        if (!nearby.empty())
            target = Acore::Containers::SelectRandomContainerElement(nearby);
        else if (havocTarget && havocTarget->IsAlive() && me->IsWithinDist(havocTarget, CHAOS_RIFT_RANGE) &&
                 me->IsWithinLOSInMap(havocTarget))
        {
            target = havocTarget;
            fallback = true;
        }

        if (!target)
            return;

        // Original caster = the warlock: SP/crit/hit/Versatility/procs are theirs, range/LoS/
        // missile origin are the Rift's (PLAN §3.9).
        me->CastSpell(target, Warlock::SPELL_RIFT_BOLT, TRIGGERED_FULL_MASK, nullptr, nullptr, owner->GetGUID());

        bool const havocValid = !fallback && havocTarget && havocTarget != target && havocTarget->IsAlive() &&
                                 me->IsWithinDist(havocTarget, CHAOS_RIFT_RANGE) && me->IsWithinLOSInMap(havocTarget);
        if (havocValid)
            me->CastSpell(havocTarget, Warlock::SPELL_RIFT_BOLT, TRIGGERED_FULL_MASK, nullptr, nullptr,
                owner->GetGUID());

        if (owner->HasAura(Warlock::SPELL_CHAOTIC_RESONANCE_R3))
        {
            Player* player = owner->ToPlayer();
            float const mult = player ? 1.0f + player->GetProcChancePercentage() / 100.0f : 1.0f;
            if (roll_chance_f(5.0f * mult))
            {
                me->CastSpell(target, Warlock::SPELL_CHAOS_ECHO_RIFT, TRIGGERED_FULL_MASK, nullptr, nullptr,
                    owner->GetGUID());
                if (havocValid)
                    me->CastSpell(havocTarget, Warlock::SPELL_CHAOS_ECHO_RIFT, TRIGGERED_FULL_MASK, nullptr, nullptr,
                        owner->GetGUID());
            }
        }
    }

    ObjectGuid _ownerGUID;
    EventMap _events;
    uint32 _interval = 2000;
};

// ===========================================================================================
// 17962 - Conflagrate - DESTRUCTION.md §7.3 (R3, C12, G1, G2, QA #18-22)
// ===========================================================================================
class spell_warl_conflagrate : public SpellScript
{
    PrepareSpellScript(spell_warl_conflagrate);

    int32 _direct = 0;
    int32 _perTick = 0;
    uint32 _consumedSpellId = 0;

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        bool const hasDot = target->HasAura(Warlock::SPELL_IMMOLATE, caster->GetGUID()) ||
                             target->HasAura(Warlock::SPELL_SHADOWFLAME_DOT, caster->GetGUID());
        return hasDot ? SPELL_CAST_OK : SPELL_FAILED_TARGET_AURASTATE;
    }

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // A miss/resist/evade still runs BeforeHit/OnHit/AfterHit for this target (they fire once
        // per entry in the spell's target list regardless of outcome) - without this check, the
        // consumed DoT is removed and direct damage is computed even though nothing landed.
        if (missInfo != SPELL_MISS_NONE)
        {
            _consumedSpellId = 0;
            _direct = 0;
            return;
        }

        int32 const immolateTotal =
            ComputeFullDurationTotal(target->GetAuraEffect(Warlock::SPELL_IMMOLATE, EFFECT_0, caster->GetGUID()));
        int32 const shadowflameTotal = ComputeFullDurationTotal(
            target->GetAuraEffect(Warlock::SPELL_SHADOWFLAME_DOT, EFFECT_0, caster->GetGUID()));

        // Tie -> Immolate (Q21).
        bool const useShadowflame = shadowflameTotal > immolateTotal;
        int32 const total = useShadowflame ? shadowflameTotal : immolateTotal;
        _consumedSpellId = useShadowflame ? Warlock::SPELL_SHADOWFLAME_DOT : Warlock::SPELL_IMMOLATE;
        if (total <= 0)
        {
            _consumedSpellId = 0;
            return;
        }

        Player* player = caster->ToPlayer();
        float mult = player ? 1.0f + player->GetMasteryPercentage() / 100.0f : 1.0f;
        // Chaotic Burn read at cast (QA #14/#22): a live aura-271 read would drop the +20% from
        // ticks landing after Chaotic Burn's own 6 s window expires.
        if (target->HasAura(Warlock::SPELL_CHAOTIC_BURN, caster->GetGUID()))
            mult *= 1.2f;

        _direct = int32(float(total) * mult);
        _perTick = int32(float(total) * 0.85f * mult / 3.0f);

        // The value passed here is what the aura is created with (Spell.cpp:2703 -> :3255);
        // SetSpellValue's own CalcBaseValue already subtracts the 1 die_sides adds back - pass the
        // live value, not value-1 (SHARED §4's "custom base points" convention).
        GetSpell()->SetSpellValue(SPELLVALUE_BASE_POINT1, _perTick);
    }

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || _direct <= 0)
            return;

        // eff0 is bp 0 + die 1, no coefficient - the engine already ran done/taken on that base 1;
        // only live taken-side mods are left to apply here. The crit rolled at launch with
        // Conflagrate's own chance (F&B/Devastation) is applied afterwards by the engine.
        SetHitDamage(int32(target->SpellDamageBonusTaken(caster, GetSpellInfo(), uint32(_direct), SPELL_DIRECT_DAMAGE)));
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !_consumedSpellId)
            return;

        // Glyph of Conflagrate keeps the consumed DoT alive (§11 Q7 default).
        if (caster->HasAura(SPELL_GLYPH_OF_CONFLAGRATE))
            return;

        target->RemoveAura(_consumedSpellId, caster->GetGUID());
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_conflagrate::CheckCast);
        BeforeHit += BeforeSpellHitFn(spell_warl_conflagrate::HandleBeforeHit);
        OnHit += SpellHitFn(spell_warl_conflagrate::HandleOnHit);
        AfterHit += SpellHitFn(spell_warl_conflagrate::HandleAfterHit);
    }
};

class spell_warl_conflagrate_aura : public AuraScript
{
    PrepareAuraScript(spell_warl_conflagrate_aura);

    // AuraEffect::CalculateAmount already ran SpellDamageBonusDone before this hook fires
    // (SpellAuraEffects.cpp:563-568 vs :581) - discard that bake and use exactly the per-tick value
    // the SpellScript's BeforeHit computed and passed via SetSpellValue (m_baseAmount = _perTick-1,
    // so +1 recovers the live value; G1: Emberstorm/Pyroclasm/Ruin/Versatility are already inside
    // that value, and this doesn't re-run SpellDamageBonusDone).
    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = aurEff->GetBaseAmount() + 1;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_conflagrate_aura::CalculateAmount, EFFECT_1,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// ===========================================================================================
// 200966-200968, 200989, 1949 - Hellstorm - DESTRUCTION.md §7.4 (R4, C4, G7, G8, QA #26, #36-37)
// ===========================================================================================
class spell_warl_hellstorm_proc : public AuraScript
{
    PrepareAuraScript(spell_warl_hellstorm_proc);

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        // "Cannot overlap" - the row itself (§8, chance 3, ICD 10 s) drives the actual
        // PROC_TRIGGER_SPELL -> 200989 application; this is the sole gate.
        Unit* caster = GetTarget();
        return caster && !caster->HasAura(Warlock::SPELL_HELLSTORM_BUFF);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_hellstorm_proc::CheckProc);
    }
};

class spell_warl_hellstorm : public AuraScript
{
    PrepareAuraScript(spell_warl_hellstorm);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // StartHellstormAcceleration itself checks for a live Hellfire periodic-trigger aura and
        // no-ops otherwise (WarlockMechanics.cpp) - no need to duplicate that check here, which
        // would require exposing the deliberately file-local SPELL_HELLFIRE constant.
        if (Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr)
            Warlock::StartHellstormAcceleration(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_hellstorm::HandleApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

class spell_warl_hellfire_hellstorm : public AuraScript
{
    PrepareAuraScript(spell_warl_hellfire_hellstorm);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (player && player->HasAura(Warlock::SPELL_HELLSTORM_BUFF))
            Warlock::StartHellstormAcceleration(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_hellfire_hellstorm::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 63349-63351 - Molten Skin (Hellfire self-damage reduction + Shadowfury CD reset capstone) -
// DESTRUCTION.md §6 row (1,1), B17/CORE-AUDIT precedent
// ===========================================================================================
class spell_warl_molten_skin : public AuraScript
{
    PrepareAuraScript(spell_warl_molten_skin);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Drops Hellfire's own self-damage ticks (actor == actionTarget == the warlock) - they
        // carry the same family bit and DONE_PERIODIC as the row's enemy-facing Rain of
        // Fire/Hellfire hits (C33), so without this the reset would also fire off self-damage.
        return eventInfo.GetActor() != eventInfo.GetActionTarget();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        if (Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr)
            player->RemoveSpellCooldown(Warlock::SPELL_SHADOWFURY, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_molten_skin::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warl_molten_skin::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 50796, 200979-200982 - Chaos Bolt, Rift Bolt, Chaos Bolt copy, Chaos Echo - DESTRUCTION.md
// §7.5-§7.7 (R2, G3, G6, QA #8-17, #28)
// ===========================================================================================
class spell_warl_chaos_bolt : public SpellScript
{
    PrepareSpellScript(spell_warl_chaos_bolt);

    bool _soulburned = false;

    void HandleAfterCast()
    {
        _soulburned = false;
        if (GetSpell()->IsTriggered())
            return;

        if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
            _soulburned = Warlock::TryConsumeSoulburnMarker(player);
    }

    void HandleAfterHit()
    {
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        Unit* primary = GetHitUnit();
        if (!caster || !primary)
            return;

        Unit* havoc = Warlock::GetHavocTarget(caster);
        bool const havocValid = havoc && havoc != primary && havoc->IsAlive() && caster->IsWithinLOSInMap(havoc);

        // R2 Havoc duplication (§7.5) - only the primary (non-triggered) cast duplicates; the
        // copy's own 30 yd + Reach range is enforced by the engine's range check on the trigger.
        if (havocValid)
            caster->CastSpell(havoc, Warlock::SPELL_CHAOS_BOLT_COPY, TRIGGERED_FULL_MASK);

        // Chaotic Burn (§7.7) - primary target only; spell_warl_chaos_bolt_copy applies it to
        // Havoc/Soulburn extra targets.
        ApplyChaoticBurn(caster, primary, GetHitDamage());

        // Chaotic Resonance r3 - Chaos Echo (§7.7); duplicated to the Havoc target too.
        if (caster->HasAura(Warlock::SPELL_CHAOTIC_RESONANCE_R3))
        {
            Player* player = caster->ToPlayer();
            float const mult = player ? 1.0f + player->GetProcChancePercentage() / 100.0f : 1.0f;
            if (roll_chance_f(5.0f * mult))
            {
                caster->CastSpell(primary, Warlock::SPELL_CHAOS_ECHO_BOLT, TRIGGERED_FULL_MASK);
                if (havocValid)
                    caster->CastSpell(havoc, Warlock::SPELL_CHAOS_ECHO_BOLT, TRIGGERED_FULL_MASK);
            }
        }

        // Soulburn: Chaos Bolt (§7.6) - the 2 enemies closest to the primary target, excluding the
        // primary and the Havoc target, within the copy's own range and LoS of the caster.
        if (_soulburned)
        {
            SpellInfo const* copyInfo = sSpellMgr->AssertSpellInfo(Warlock::SPELL_CHAOS_BOLT_COPY);
            float const range = copyInfo ? copyInfo->GetMaxRange(false, caster) : 30.0f;

            std::list<Unit*> candidates;
            Acore::AnyUnfriendlyUnitInObjectRangeCheck check(caster, caster, range);
            Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(caster, candidates, check);
            Cell::VisitObjects(caster, searcher, range);

            candidates.remove_if([&](Unit* unit)
            {
                return unit == primary || (havocValid && unit == havoc) || !unit->IsAlive() ||
                       !caster->IsValidAttackTarget(unit) || !unit->IsInCombatWith(caster) ||
                       !caster->IsWithinLOSInMap(unit);
            });

            candidates.sort(Acore::ObjectDistanceOrderPred(primary));

            uint8 placed = 0;
            for (Unit* unit : candidates)
            {
                if (placed >= 2)
                    break;
                caster->CastSpell(unit, Warlock::SPELL_CHAOS_BOLT_COPY, TRIGGERED_FULL_MASK);
                ++placed;
            }
        }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_warl_chaos_bolt::HandleAfterCast);
        AfterHit += SpellHitFn(spell_warl_chaos_bolt::HandleAfterHit);
    }
};

class spell_warl_chaos_bolt_copy : public SpellScript
{
    PrepareSpellScript(spell_warl_chaos_bolt_copy);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (caster && target)
            ApplyChaoticBurn(caster, target, GetHitDamage());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_chaos_bolt_copy::HandleAfterHit);
    }
};

// Bound to 50796, 200980, 200979, 200981, 200982 - Mastery is read live per hit (QA #5), including
// for the Rift's own bolts/echoes via GetOriginalCaster() (GetCaster() there is the Rift).
class spell_warl_chaos_bolt_mastery : public SpellScript
{
    PrepareSpellScript(spell_warl_chaos_bolt_mastery);

    void HandleHit()
    {
        Unit* original = GetOriginalCaster();
        Player* player = original ? original->ToPlayer() : nullptr;
        if (!player || !player->HasSpell(Warlock::SPELL_CHAOS_BOLT))
            return;

        SetHitDamage(int32(float(GetHitDamage()) * (1.0f + player->GetMasteryPercentage() / 100.0f)));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warl_chaos_bolt_mastery::HandleHit);
    }
};

// ===========================================================================================
// 29341 - Shadowburn (Destruction additive) - DESTRUCTION.md §7.8 (QA #16, #31)
// ===========================================================================================
class spell_warl_shadowburn_destruction : public AuraScript
{
    PrepareAuraScript(spell_warl_shadowburn_destruction);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        if (caster->isHonorOrXPTarget(target))
            caster->RemoveSpellCooldown(Warlock::SPELL_SHADOWBURN, true);

        // Independent of the XP/honor gate above (§11 Q21) - each qualifying death grants its own
        // 4 s off Chaos Bolt.
        if (caster->HasAura(SPELL_EMBERSTORM_R3))
            Warlock::ReduceChaosBoltCooldown(caster, 4000);
    }

    void Register() override
    {
        // AFFLICTION.md's B9 replacement changes 29341's eff0 from aura 86 to DUMMY - bind on
        // SPELL_AURA_ANY so this class survives either shape.
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_shadowburn_destruction::HandleRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 6353 - Soul Fire (Destruction additive) - DESTRUCTION.md §7.6, §7.14 (F&B stack consumption)
// ===========================================================================================
class spell_warl_soul_fire_destruction : public SpellScript
{
    PrepareSpellScript(spell_warl_soul_fire_destruction);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (caster && target)
            target->RemoveAura(Warlock::SPELL_FIRE_AND_BRIMSTONE_DEBUFF, caster->GetGUID());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_soul_fire_destruction::HandleAfterHit);
    }
};

// ===========================================================================================
// 17834, 200986 - Improved Immolate eruption - DESTRUCTION.md §7.10 (G15, QA #25)
// ===========================================================================================
class spell_warl_improved_immolate_eruption : public AuraScript
{
    PrepareAuraScript(spell_warl_improved_immolate_eruption);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_IMMOLATE_ERUPTION });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        AuraEffect const* immolate = target->GetAuraEffect(Warlock::SPELL_IMMOLATE, EFFECT_0, caster->GetGUID());
        if (!immolate)
            return;

        // The tick's own snapshot (done-mods in, target-mods and crit out) - half of it.
        int32 const bp = immolate->GetAmount() / 2;
        if (bp <= 0)
            return;

        caster->CastCustomSpell(Warlock::SPELL_IMMOLATE_ERUPTION, SPELLVALUE_BASE_POINT0, bp, target,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warl_improved_immolate_eruption::HandleProc, EFFECT_2,
            SPELL_AURA_DUMMY);
    }
};

class spell_warl_immolate_eruption : public SpellScript
{
    PrepareSpellScript(spell_warl_immolate_eruption);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        // The source target stays in (it already satisfies this, C3) - only drops units not in
        // combat with the caster.
        targets.remove_if([caster](WorldObject const* obj)
        {
            Unit const* unit = obj->ToUnit();
            return !unit || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warl_immolate_eruption::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// ===========================================================================================
// 47268, 200990 - Fire and Brimstone (stacks) - DESTRUCTION.md §7.14 (C1, C4, QA #39)
// ===========================================================================================
class spell_warl_fire_and_brimstone : public AuraScript
{
    PrepareAuraScript(spell_warl_fire_and_brimstone);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Spell const* procSpell = eventInfo.GetProcSpell();
        if (procSpell && procSpell->IsTriggered())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->Id == Warlock::SPELL_SOUL_FIRE)
            return false;

        if (!spellInfo->HasEffect(SPELL_EFFECT_SCHOOL_DAMAGE))
            return false;

        if (!(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_FIRE))
            return false;

        // Judged by *base* cast time, not the current (possibly instant) one - C1: Backlash's
        // instant Immolate and Chaotic Inferno's instant Chaos Bolt still count. This also
        // excludes Molten Bolts (triggered, base cast time 0) without a separate check.
        return spellInfo->CastTimeEntry && spellInfo->CastTimeEntry->CastTime > 0;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        // DESTRUCTION.md §7.14: "OnProc (PreventDefault)" - 47268's own eff2 is a native
        // PROC_TRIGGER_SPELL -> 200990 that the row's disable_effects_mask (0x3) deliberately
        // leaves live (only eff0/eff1 are disabled), since the native trigger can't express "2
        // stacks for Incinerate". Without PreventDefaultAction() here, both the native trigger and
        // this handler apply 200990 on the same proc, double-stacking every hit.
        PreventDefaultAction();

        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        uint8 const stacks = (spellInfo && spellInfo->Id == Warlock::SPELL_INCINERATE) ? 2 : 1;

        // AddAura on an existing same-caster cumulative aura adds a stack (TryRefreshStackOrCreate),
        // capped at 10 by the row's own CumulativeAura.
        for (uint8 i = 0; i < stacks; ++i)
            caster->AddAura(Warlock::SPELL_FIRE_AND_BRIMSTONE_DEBUFF, target);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_fire_and_brimstone::CheckProc);
        OnProc += AuraProcFn(spell_warl_fire_and_brimstone::HandleProc);
    }
};

// ===========================================================================================
// 30302 - Nether Protection capstone self-damage filter (Destruction additive) -
// DESTRUCTION.md §11 Q23 (resolved default: exclude self-inflicted damage)
// ===========================================================================================
class spell_warl_nether_protection_destruction : public AuraScript
{
    PrepareAuraScript(spell_warl_nether_protection_destruction);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // The kept stock class (-30299) only filters by school; without this, every Hellfire
        // self-damage tick (actor == actionTarget == the warlock) also rolls the 20% proc, keeping
        // -10% Fire damage taken up almost permanently while channelling.
        return eventInfo.GetActor() != eventInfo.GetActionTarget();
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_nether_protection_destruction::CheckProc);
    }
};

// ===========================================================================================
// 30283 - Shadowfury (Fury of the Void capstone) - DESTRUCTION.md §7.13 (G13, QA #38)
// ===========================================================================================
class spell_warl_fury_of_the_void : public SpellScript
{
    PrepareSpellScript(spell_warl_fury_of_the_void);

    bool _hit = false;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_IMMOLATE });
    }

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        // AfterHit alone can't tell a miss/resist from a hit (it carries no SpellMissInfo and the
        // target reference stays valid either way) - capture it here, same pattern as
        // spell_warl_conflagrate, so an enemy Shadowfury missed/resisted doesn't also get a free
        // Immolate.
        _hit = (missInfo == SPELL_MISS_NONE);
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!_hit || !caster || !target || !caster->HasAura(Warlock::SPELL_FURY_OF_THE_VOID_R3))
            return;

        // AddAura applies only Immolate's aura effects (DoT + the F&B aura-271 effect), no direct
        // hit and no cast - Backlash's charge is untouched (G13/QA #23).
        caster->AddAura(Warlock::SPELL_IMMOLATE, target);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_warl_fury_of_the_void::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_warl_fury_of_the_void::HandleAfterHit);
    }
};

// ===========================================================================================
// 18096, 18073, 63245 - Pyroclasm - DESTRUCTION.md §7.15
// ===========================================================================================
class spell_warl_pyroclasm : public AuraScript
{
    PrepareAuraScript(spell_warl_pyroclasm);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // The row's own family is 0 (matches everything) precisely so this class can filter across
        // families - Scorch is mage, not warlock (B4 Classless clause).
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARLOCK)
            return spellInfo->SpellFamilyFlags.HasFlag(0x100, 0x800000, 0); // Searing Pain, Conflagrate

        if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE)
            return spellInfo->SpellFamilyFlags.HasFlag(0x10, 0, 0); // Scorch

        return false;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_pyroclasm::CheckProc);
    }
};

// ===========================================================================================
// 47258-47260 - Backdraft - DESTRUCTION.md §7.15
// ===========================================================================================
class spell_warl_backdraft : public AuraScript
{
    PrepareAuraScript(spell_warl_backdraft);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Spell const* procSpell = eventInfo.GetProcSpell();
        if (procSpell && procSpell->IsTriggered())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Family 0 on the row (Classless, Mind Blast is priest); filtered here.
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARLOCK)
            return spellInfo->SpellFamilyFlags.HasFlag(0x80, 0x801000, 0); // Shadowburn, Shadowfury, Conflagrate

        if (spellInfo->SpellFamilyName == SPELLFAMILY_PRIEST)
            return spellInfo->SpellFamilyFlags.HasFlag(0x2000, 0, 0); // Mind Blast

        return false;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_backdraft::CheckProc);
    }
};

// ===========================================================================================
// 3110 - Imp Firebolt (Empowered Imp capstone) - DESTRUCTION.md §7.15 (G11)
// ===========================================================================================
class spell_warl_empowered_imp : public SpellScript
{
    PrepareSpellScript(spell_warl_empowered_imp);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_EMPOWERED_IMP_BUFF });
    }

    void HandleAfterCast()
    {
        // Wild Imps' Firebolt is a different Demonology spell id - excluded automatically since
        // this class is bound only to the (Fel)Imp's own Firebolt, 3110.
        Unit* imp = GetCaster();
        if (!imp)
            return;

        Unit* owner = imp->GetOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player || !player->HasAura(SPELL_EMPOWERED_IMP_R3))
            return;

        if (roll_chance_f(5.0f * Warlock::GetOwnerProcChanceMultiplier(imp)))
            player->CastSpell(player, Warlock::SPELL_EMPOWERED_IMP_BUFF, true);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_warl_empowered_imp::HandleAfterCast);
    }
};

// ===========================================================================================
// 30293, 30295, 30296 - Soul Leech - DESTRUCTION.md §7.11 (G3)
// ===========================================================================================
class spell_warl_soul_leech_destruction : public AuraScript
{
    PrepareAuraScript(spell_warl_soul_leech_destruction);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_SOUL_LEECH_HEAL, SPELL_REPLENISHMENT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Non-triggered ids only - copies/echoes/Rift Bolts are triggered anyway and never reach
        // this filter.
        switch (spellInfo->Id)
        {
            case SPELL_SHADOW_BOLT:
            case Warlock::SPELL_IMMOLATE:
            case Warlock::SPELL_SHADOWBURN:
            case SPELL_SEARING_PAIN:
            case Warlock::SPELL_INCINERATE:
            case Warlock::SPELL_SOUL_FIRE:
            case Warlock::SPELL_CHAOS_BOLT:
            case Warlock::SPELL_CONFLAGRATE:
                return true;
            default:
                return false;
        }
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Player* player = caster ? caster->ToPlayer() : nullptr;

        // §0.5 Q15a: only the highest-% leech talent heals; other leech sources (spell drains,
        // items, buffs) are untouched and stack. The r3 mana/Replenishment part below shares this
        // proc and its 3 s ICD regardless of which leech talent currently wins.
        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        if (player && damageInfo && damageInfo->GetDamage() &&
            Warlock::GetActiveLeechTalent(player) == Warlock::LeechTalent::SoulLeech)
        {
            int32 amount = CalculatePct(int32(damageInfo->GetDamage()), aurEff->GetAmount());
            int32 const cap = int32(CalculatePct(caster->GetMaxHealth(), 15));
            if (amount > cap)
                amount = cap;

            if (amount > 0)
                caster->CastCustomSpell(Warlock::SPELL_SOUL_LEECH_HEAL, SPELLVALUE_BASE_POINT0, amount, caster, true);
        }

        if (caster && GetSpellInfo()->Id == Warlock::SPELL_SOUL_LEECH_R3)
        {
            int32 const selfMissing = int32(caster->GetMaxPower(POWER_MANA)) - int32(caster->GetPower(POWER_MANA));
            int32 const selfEnergize = int32(CalculatePct(selfMissing, 4));
            if (selfEnergize > 0)
                caster->EnergizeBySpell(caster, Warlock::SPELL_SOUL_LEECH_HEAL, selfEnergize, POWER_MANA);

            if (player)
                if (Pet* pet = player->GetPet())
                {
                    int32 const petMissing = int32(pet->GetMaxPower(POWER_MANA)) - int32(pet->GetPower(POWER_MANA));
                    int32 const petEnergize = int32(CalculatePct(petMissing, 4));
                    if (petEnergize > 0)
                        pet->EnergizeBySpell(pet, Warlock::SPELL_SOUL_LEECH_HEAL, petEnergize, POWER_MANA);
                }

            caster->CastSpell(caster, SPELL_REPLENISHMENT, true);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_soul_leech_destruction::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warl_soul_leech_destruction::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

void AddSC_warlock_destruction_spell_scripts()
{
    RegisterSpellAndAuraScriptPair(spell_warl_rain_of_fire, spell_warl_rain_of_fire_aura);
    RegisterSpellScript(spell_warl_rain_of_fire_tick);
    RegisterSpellScript(spell_warl_chaos_rift);
    RegisterCreatureAI(npc_warl_chaos_rift);
    RegisterSpellAndAuraScriptPair(spell_warl_conflagrate, spell_warl_conflagrate_aura);
    RegisterSpellScript(spell_warl_hellstorm_proc);
    RegisterSpellScript(spell_warl_hellstorm);
    RegisterSpellScript(spell_warl_hellfire_hellstorm);
    RegisterSpellScript(spell_warl_molten_skin);
    RegisterSpellScript(spell_warl_chaos_bolt);
    RegisterSpellScript(spell_warl_chaos_bolt_copy);
    RegisterSpellScript(spell_warl_chaos_bolt_mastery);
    RegisterSpellScript(spell_warl_shadowburn_destruction);
    RegisterSpellScript(spell_warl_soul_fire_destruction);
    RegisterSpellScript(spell_warl_improved_immolate_eruption);
    RegisterSpellScript(spell_warl_immolate_eruption);
    RegisterSpellScript(spell_warl_fire_and_brimstone);
    RegisterSpellScript(spell_warl_nether_protection_destruction);
    RegisterSpellScript(spell_warl_fury_of_the_void);
    RegisterSpellScript(spell_warl_pyroclasm);
    RegisterSpellScript(spell_warl_backdraft);
    RegisterSpellScript(spell_warl_empowered_imp);
    RegisterSpellScript(spell_warl_soul_leech_destruction);

    // Soul Fire's instant-cast sources (SHARED §4 arbiter, priority = registration order):
    // Empowered Imp > Soulburn > Molten Core (Demonology registers the third in S3). Chaos Bolt's
    // list has one member - Soulburn: Chaos Bolt is not an instant-cast source (§7.6).
    Warlock::RegisterInstantCastSource(Warlock::SPELL_SOUL_FIRE, Warlock::InstantCastSource::EmpoweredImp,
        [](Player* p) { return p->HasAura(Warlock::SPELL_EMPOWERED_IMP_BUFF); },
        [](Player* p) { p->RemoveAurasDueToSpell(Warlock::SPELL_EMPOWERED_IMP_BUFF); });

    Warlock::RegisterInstantCastSource(Warlock::SPELL_SOUL_FIRE, Warlock::InstantCastSource::Soulburn,
        [](Player* p) { return p->HasSpell(Warlock::SPELL_CHAOS_BOLT) && p->HasAura(Warlock::SPELL_SOULBURN_MARKER); },
        [](Player* p) { Warlock::TryConsumeSoulburnMarker(p); });

    Warlock::RegisterInstantCastSource(Warlock::SPELL_CHAOS_BOLT, Warlock::InstantCastSource::ChaoticInferno,
        [](Player* p) { return p->HasAura(Warlock::SPELL_CHAOTIC_INFERNO); },
        [](Player* p) { p->RemoveAurasDueToSpell(Warlock::SPELL_CHAOTIC_INFERNO); });
}
