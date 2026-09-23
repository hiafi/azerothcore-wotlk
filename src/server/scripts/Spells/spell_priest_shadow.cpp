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
 * Priest Shadow rework (docs/reworks/priest-shadow-rework.md,
 * .agents/plans/priest-rework/priest-rework.SHADOW.md) - every genuinely new script class this
 * pass needs goes here, same "spell_pri_" naming convention as spell_priest.cpp /
 * spell_priest_new.cpp / spell_priest_disc.cpp / spell_priest_holy.cpp. Talents that only retune
 * an existing stock script are edited in place in their existing files instead (spell_priest.cpp,
 * spell_priest_new.cpp - see SHADOW.md's "Scripts on stock spells" list). Hooks that can't be a
 * SpellScript/AuraScript/CreatureAI at all (the Madness resource, tentacle spawn/despawn) live in
 * PriestMechanics.h/.cpp next to the core call sites that need them.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Containers.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "PlayerScript.h"
#include "PriestMechanics.h"
#include "Random.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"

enum PriestShadowSpells
{
    // Stock spells this file's scripts key on by id.
    SPELL_PRIEST_SHADOW_WORD_PAIN            = 589,
    SPELL_PRIEST_MIND_FLAY                   = 15407,
    SPELL_PRIEST_MIND_BLAST                  = 8092,

    // Void Eruption's buff (spell_priest_new.cpp / PriestMechanics.cpp's own PRIEST_ICON_VOIDFORM
    // comment) - Void-touched Mind's capstone extends its live duration.
    SPELL_PRIEST_VOIDFORM                    = 200140,

    // Shadow rework spells (SHADOW.md "ID map").
    SPELL_PRIEST_DARKNESS_BUFF               = 200243,
    SPELL_PRIEST_TENTACLES_OF_MADNESS        = 200244,   // talent rank passive marker (3,0)
    SPELL_PRIEST_SUMMON_TENTACLE_OF_MADNESS  = 200245,
    SPELL_PRIEST_TENTACLE_MIND_FLAY          = 200246,   // channeled clone, shares Mind Flay's bit
    SPELL_PRIEST_CORRUPTED_SOUL              = 200247,
    SPELL_PRIEST_CALL_OF_THE_VOID            = 200248,
    SPELL_PRIEST_CALL_OF_THE_VOID_BUFF       = 200249,
    SPELL_PRIEST_VOID_TOUCHED_MIND_R3        = 200262,   // (7,2) rank 3 - Voidform extension capstone
    SPELL_PRIEST_SURRENDER_TO_MADNESS        = 200269,   // (10,1)
    SPELL_PRIEST_SUNDERED_MIND                = 200270,
    SPELL_PRIEST_MADNESS                      = 200271,   // visible stacking resource aura
    SPELL_PRIEST_TENTACLE_SCALING             = 200272,

    NPC_PRIEST_TENTACLE_OF_MADNESS            = 300102
};

namespace
{
    // Family mask bit (dword1) this file's tentacle-targeting code matches Shadow Word: Pain by -
    // copied from apps/dbc-tools/source/classes/priest/_masks.py (C++ can't import that DSL
    // module; PLAN sec 4.4), same value PriestMechanics.cpp and the stock scripts already use.
    constexpr uint32 PRIEST_MASK_DW1_SHADOW_WORD_PAIN = 0x00008000;

    constexpr float PRIEST_TENTACLE_TARGET_RANGE_YD = 40.0f;
    // How far from the priest a tentacle erupts, in a random direction (user call
    // 2026-09-23). Spell 200245 targets TARGET_UNIT_CASTER, and Spell::SummonGuardian uses
    // destTarget verbatim for a lone guardian, so without this they all stack inside the
    // player's own model.
    constexpr float PRIEST_TENTACLE_SPAWN_DIST_YD = 4.0f;
    constexpr uint32 PRIEST_TENTACLE_UPDATE_INTERVAL_MS = 500;
    // Matches Summon Tentacle of Madness' (200245) own `duration_ms=10000` (SHADOW.md "ID map") -
    // reused as the value UpdateAI keeps stamping onto the tentacle's own despawn timer every
    // update while Surrender to Madness is active, so it never counts down to 0 (design doc sec
    // 4.5 "your Tentacles of Madness do not expire"). Surrender's own OnRemove force-despawns every
    // live tentacle regardless (Priest::DespawnTentacles), so this never needs to "remember" how
    // much time was really left - it only has to stay non-zero for as long as Surrender is up.
    constexpr uint32 PRIEST_TENTACLE_DESPAWN_REFRESH_MS = 10000;

    constexpr float PRIEST_SURRENDER_PEACEFUL_CHECK_RANGE_YD = 100.0f;

    enum PriestShadowEvents
    {
        EVENT_TENTACLE_UPDATE = 1
    };

    /*
     * "In combat with the owner OR in combat with any of the owner's group members" - shared by
     * the tentacle's own target search (design doc sec 4.1) and Surrender to Madness' peaceful-exit
     * check (design doc sec 4.5, "checks enemies... not the priest's own combat state" - a group
     * member's own attacker/threat state counts too). Same group-iteration idiom
     * spell_pri_void_eruption::CountHit (spell_priest_new.cpp) already uses for its own
     * "already engaged" check; `Unit::IsInCombatWith` itself is what walks each side's own
     * attacker/threat list (Unit.cpp ~16764), so this doesn't need to re-implement that.
     */
    bool IsEngagedWithOwnerOrGroup(Unit* hostile, Player* owner)
    {
        if (hostile->IsInCombatWith(owner))
            return true;

        if (Group* group = owner->GetGroup())
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player* member = ref->GetSource())
                    if (member != owner && hostile->IsInCombatWith(member))
                        return true;

        return false;
    }

    // Surrender to Madness' exit condition 1 (design doc sec 4.5): "If no enemies remain in combat
    // with you or your party." Scans a flat radius around the owner rather than the tentacles'
    // positions - the drawback is meant to key off the *priest's* combat exposure, not wherever a
    // tentacle happens to be idling.
    bool HasEngagedEnemyNearby(Player* owner)
    {
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(owner, owner, PRIEST_SURRENDER_PEACEFUL_CHECK_RANGE_YD);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(owner, nearby, check);
        Cell::VisitObjects(owner, searcher, PRIEST_SURRENDER_PEACEFUL_CHECK_RANGE_YD);

        for (Unit* hostile : nearby)
            if (IsEngagedWithOwnerOrGroup(hostile, owner))
                return true;

        return false;
    }
}

/*
 * Tentacle of Madness (docs/reworks/priest-shadow-rework.md sec 4.1, priest-rework.SHADOW.md talent
 * table 3,0). Creature 300102, ScriptName 'npc_pri_tentacle_of_madness' (creature_template already
 * inserted by WP-0 prep, data/sql/updates/pending_db_world/rev_1790124445361169072.sql).
 *
 * Owner resolution: `me->GetOwner()` - a Guardian's owner is set at *construction* time
 * (Minion::Minion's `m_owner(owner)` member-init, TemporarySummon.cpp), well before any AI hook
 * runs, so it's already valid by Reset(). IsSummonedBy() is overridden only to scatter the spawn
 * point (below) - unlike npc_pri_divine_star it doesn't need the hook to resolve its owner, and it
 * never moves under its own power afterwards.
 *
 * Threat: REACT_PASSIVE + no threat table of its own (design doc sec 4.1: "Generates no threat for
 * the priest and holds no threat table of its own") - this AI never calls UpdateVictim()/AddThreat,
 * targeting is fully custom via FindTarget() below. The Mind Flay clone (200246) itself also
 * carries SPELL_ATTR1_NO_THREAT (WP-A data, SHADOW.md ID map row 200246), so its damage generates
 * no threat for the owner either.
 */
class npc_pri_tentacle_of_madness : public CreatureAI
{
public:
    explicit npc_pri_tentacle_of_madness(Creature* creature) : CreatureAI(creature) { }

    // Runs before Spell::SummonGuardian's own MoveFollow(), and NearTeleportTo works on a rooted
    // unit, so the scatter below survives both.
    void IsSummonedBy(WorldObject* summoner) override
    {
        if (!summoner)
            return;

        // Random direction, fixed distance. GetFirstCollisionPosition takes an angle relative to
        // the summoner's own orientation - irrelevant for a uniformly random one - and walks the
        // line for collisions/ground, so a tentacle never erupts inside a wall or in mid-air.
        float const angle = frand(0.0f, static_cast<float>(2 * M_PI));
        Position const pos = summoner->GetFirstCollisionPosition(PRIEST_TENTACLE_SPAWN_DIST_YD, angle);
        me->NearTeleportTo(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ(), me->GetOrientation());
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        _targetGUID.Clear();

        // The tentacle is stationary (design doc sec 4.1), but Spell::SummonGuardian puts every
        // non-trigger guardian on MoveFollow(caster, PET_FOLLOW_DIST) *after* this hook runs, so
        // clearing the motion master here would just be overwritten. Root instead: a rooted unit's
        // follow generator can't actually move it. Without this, 200246's ChannelInterruptFlags
        // include AURA_INTERRUPT_FLAG_MOVE, and Unit::UpdatePosition drops move-interrupted auras
        // for any unit (not just players), so every step the owner took would cancel the channel.
        me->SetControlled(true, UNIT_STATE_ROOT);

        // Stat snapshot (design doc sec 4.1: "Reads spell power, haste, crit, Mastery and
        // Versatility once at summon and holds them for its full life") - spell_pri_tentacle_scaling
        // (below) does the actual reading/storing, triggered by this cast.
        DoCastSelf(SPELL_PRIEST_TENTACLE_SCALING, true);

        events.ScheduleEvent(EVENT_TENTACLE_UPDATE, Milliseconds(PRIEST_TENTACLE_UPDATE_INTERVAL_MS));
    }

    void UpdateAI(uint32 diff) override
    {
        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            if (eventId == EVENT_TENTACLE_UPDATE)
            {
                UpdateTentacle();
                events.ScheduleEvent(EVENT_TENTACLE_UPDATE, Milliseconds(PRIEST_TENTACLE_UPDATE_INTERVAL_MS));
            }
        }
    }

private:
    void UpdateTentacle()
    {
        Player* owner = me->GetOwner() ? me->GetOwner()->ToPlayer() : nullptr;
        if (!owner)
            return;

        // "While the owner has Surrender to Madness active: refresh/extend its own despawn timer
        // each update instead of expiring at the natural 10 s" (design doc sec 4.5).
        if (owner->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            if (TempSummon* summon = me->ToTempSummon())
                summon->SetTimer(PRIEST_TENTACLE_DESPAWN_REFRESH_MS);

        if (me->GetCurrentSpell(CURRENT_CHANNELED_SPELL))
        {
            // Already channelling - only retarget on death/LoS loss (design doc sec 4.1 / 10.2-3);
            // an idle-but-valid channel just keeps running untouched.
            CheckCurrentTarget(owner);
            return;
        }

        if (Unit* target = FindTarget(owner))
        {
            _targetGUID = target->GetGUID();
            DoCast(target, SPELL_PRIEST_TENTACLE_MIND_FLAY);
        }
        // else: no valid target - idle in place, keep counting down its own duration (design doc
        // sec 4.1: "If no valid target exists, idles in place. Does not despawn, does not fail to
        // spawn.").
    }

    void CheckCurrentTarget(Player* owner)
    {
        Unit* target = ObjectAccessor::GetUnit(*me, _targetGUID);
        bool stillValid = target && target->IsAlive() && me->IsWithinLOSInMap(target);
        if (stillValid)
            return;

        // "On target death, retargets to another valid Shadow Word: Pain target." / "On LoS loss:
        // interrupt the channel and immediately try to retarget (don't despawn)" (design doc sec
        // 4.1, items 2-3 in sec 10's verification list).
        me->InterruptSpell(CURRENT_CHANNELED_SPELL);
        _targetGUID.Clear();

        if (Unit* newTarget = FindTarget(owner))
        {
            _targetGUID = newTarget->GetGUID();
            DoCast(newTarget, SPELL_PRIEST_TENTACLE_MIND_FLAY);
        }
    }

    // "Picks a random enemy afflicted by the caster's Shadow Word: Pain. May not target an enemy
    // that is not already in combat with the caster's party." (design doc sec 4.1).
    Unit* FindTarget(Player* owner)
    {
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(me, me, PRIEST_TENTACLE_TARGET_RANGE_YD);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(me, nearby, check);
        Cell::VisitObjects(me, searcher, PRIEST_TENTACLE_TARGET_RANGE_YD);

        std::vector<Unit*> candidates;
        for (Unit* unit : nearby)
        {
            if (!unit->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, PRIEST_MASK_DW1_SHADOW_WORD_PAIN, 0, 0, owner->GetGUID()))
                continue;
            if (!me->IsWithinLOSInMap(unit))
                continue;
            if (!IsEngagedWithOwnerOrGroup(unit, owner))
                continue;

            candidates.push_back(unit);
        }

        if (candidates.empty())
            return nullptr;

        return Acore::Containers::SelectRandomContainerElement(candidates);
    }

    ObjectGuid _targetGUID;
};

/*
 * 200272 - Tentacle of Madness: Scaling. Stat snapshot cast on self by
 * npc_pri_tentacle_of_madness::Reset() at spawn (design doc sec 4.1). Native per-Unit-field stats
 * (spell power/crit/haste) are inherited via DoEffectCalcAmount, same shape as
 * spell_pri_shadowfiend_scaling (spell_priest.cpp); Mastery/Versatility have no native per-Unit
 * field on this server (PLAN sec 3.8/6's custom stats), so they're captured into
 * Priest::TentacleSnapshot's manual backing map instead (PriestMechanics.h/.cpp), read later from
 * the tentacle's own damage path in Priest::ApplyDoneDamagePctMods.
 *
 * Best-effort note (flagged in the WP-B report): the exact AuraType each of 200272's three effects
 * carries is WP-A's concurrent data pass (apps/dbc-tools/source/classes/priest/
 * priest_trigger_spells.py), which this file cannot read reliably mid-edit. The three AuraTypes
 * bound below - MOD_DAMAGE_DONE (school Shadow) for spell power, matching
 * spell_pri_shadowfiend_scaling's own CalculateSPAmount; MOD_CRIT_PCT and MELEE_SLOW for
 * crit/haste, per priest-rework.PLAN.md sec 1's "generalized stats" convention for flat spell
 * crit%/haste% grants - are the best-supported guess available without that file. If WP-A declared
 * different AuraTypes for these three effects, these calc-amount handlers simply never fire (a
 * silent no-op, not a crash/Validate() failure) and the tentacle keeps whatever static amount the
 * DSL set; the Mastery/Versatility snapshot and its cleanup below are unaffected either way, since
 * those are bound to EFFECT_0/SPELL_AURA_ANY rather than a specific type.
 */
class spell_pri_tentacle_scaling : public AuraScript
{
    PrepareAuraScript(spell_pri_tentacle_scaling);

    void CalculateSpellPower(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* owner = GetUnitOwner()->GetOwner())
            amount = std::max<int32>(0, owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_SHADOW));
    }

    void CalculateCritChance(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* owner = GetUnitOwner()->GetOwner())
            if (Player* player = owner->ToPlayer())
                amount = int32(player->GetFloatValue(PLAYER_SPELL_CRIT_PERCENTAGE1 + uint32(SPELL_SCHOOL_SHADOW)));
    }

    void CalculateHaste(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            float castSpeed = owner->GetFloatValue(UNIT_MOD_CAST_SPEED);
            if (castSpeed > 0.0f)
                amount = int32((1.0f / castSpeed - 1.0f) * 100.0f);
        }
    }

    void HandleEffectApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* tentacle = GetUnitOwner();
        Unit* owner = tentacle ? tentacle->GetOwner() : nullptr;
        Player* ownerPlr = owner ? owner->ToPlayer() : nullptr;
        if (!tentacle || !ownerPlr)
            return;

        Priest::TentacleSnapshot snapshot;
        snapshot.mastery = ownerPlr->GetMasteryPercentage();
        snapshot.versatility = ownerPlr->GetVersatilityPercentage();
        Priest::SetTentacleSnapshot(tentacle->GetGUID(), snapshot);
    }

    void HandleEffectRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* tentacle = GetUnitOwner())
            Priest::ClearTentacleSnapshot(tentacle->GetGUID());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_tentacle_scaling::CalculateSpellPower, EFFECT_ALL, SPELL_AURA_MOD_DAMAGE_DONE);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_tentacle_scaling::CalculateCritChance, EFFECT_ALL, SPELL_AURA_MOD_CRIT_PCT);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_tentacle_scaling::CalculateHaste, EFFECT_ALL, SPELL_AURA_MELEE_SLOW);
        OnEffectApply += AuraEffectApplyFn(spell_pri_tentacle_scaling::HandleEffectApply, EFFECT_0, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        OnEffectRemove += AuraEffectRemoveFn(spell_pri_tentacle_scaling::HandleEffectRemove, EFFECT_0, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 200246 - Mind Flay (Tentacle). "Generates 1 Madness per Mind Flay tick. This is the unit's own
// behaviour, not inherited, and is unaffected by the exclusion list" (design doc sec 4.1) - always
// 1, never x3, even during Surrender to Madness.
class spell_pri_tentacle_mind_flay : public AuraScript
{
    PrepareAuraScript(spell_pri_tentacle_mind_flay);

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* tentacle = GetCaster();
        if (!tentacle)
            return;

        if (Player* owner = tentacle->GetOwner() ? tentacle->GetOwner()->ToPlayer() : nullptr)
            Priest::AddMadness(owner, 1, Priest::MadnessSource::TentacleMindFlay);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_tentacle_mind_flay::OnPeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DAMAGE);
    }
};

/*
 * 15407 - Mind Flay: Madness generation + forced Surrender spawns.
 *
 * Bound to EFFECT_2, not EFFECT_0: this server's Mind Flay row (apps/dbc-tools/source/classes/
 * priest/priest_spells.py's mind_flay_15407) is E1 APPLY_AURA/DUMMY, E2 MOD_DECREASE_SPEED,
 * E3 PERIODIC_TRIGGER_SPELL_WITH_VALUE (aura 227, amplitude 1000) firing the damage helper 58381
 * - there is no PERIODIC_DAMAGE effect on the row at all, so an EFFECT_0/SPELL_AURA_PERIODIC_DAMAGE
 * binding silently never fires. Verified against live acore_world.spell_dbc. The tentacle's own
 * clone (200246) is the opposite shape - a real PERIODIC_DAMAGE on EFFECT_0 - which is why
 * spell_pri_tentacle_mind_flay above binds differently.
 */
class spell_pri_mind_flay_madness : public AuraScript
{
    PrepareAuraScript(spell_pri_mind_flay_madness);

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        Priest::AddMadness(player, 1, Priest::MadnessSource::PlayerMindFlay);

        // "While active ... every Shadow Word: Pain and Mind Flay damage event summons one,
        // ignoring the shared cooldown" (design doc sec 4.5).
        if (player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            Priest::TrySummonTentacle(player, Priest::TentacleTrigger::MindFlay);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_mind_flay_madness::OnPeriodic, EFFECT_2, SPELL_AURA_PERIODIC_TRIGGER_SPELL_WITH_VALUE);
    }
};

/*
 * -589 - Shadow Word: Pain: forced Surrender spawns only. Normal, non-Surrender SW:P-tick spawns
 * come from Writhing Agony's own proc (spell_pri_writhing_agony below) - this class fires only
 * while Surrender to Madness is active.
 */
class spell_pri_shadow_word_pain_surrender : public AuraScript
{
    PrepareAuraScript(spell_pri_shadow_word_pain_surrender);

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            return;

        Priest::TrySummonTentacle(player, Priest::TentacleTrigger::ShadowWordPain);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_shadow_word_pain_surrender::OnPeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DAMAGE);
    }
};

/*
 * -8092 - Mind Blast: one class for all three Mind Blast hooks (SHADOW.md talent table 3,0 / 7,2,
 * "Scripts on stock spells"): (a) Madness generation, (b) Tentacles of Madness spawn roll +
 * 25 s guarantee, (c) Void-touched Mind's Voidform-extension capstone.
 */
class spell_pri_mind_blast_shadow : public SpellScript
{
    PrepareSpellScript(spell_pri_mind_blast_shadow);

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        // (a) "Mind Blast generates 5 [15 during Surrender]" (design doc sec 4.3) - the x3 is
        // AddMadness's own gate, keyed on Priest::MadnessSource::MindBlast.
        Priest::AddMadness(caster, 5, Priest::MadnessSource::MindBlast);

        // (b) Tentacles of Madness (3,0): "15% chance to summon one, and always summons one if none
        // has been summoned this way in the last 25 sec" - the 25 s guarantee does not scale with
        // Proc Chance (design doc sec 4.2/9); always bypasses the shared ICD.
        if (caster->HasAura(SPELL_PRIEST_TENTACLES_OF_MADNESS))
        {
            float chance = 15.0f * (1.0f + caster->GetProcChancePercentage() / 100.0f);
            if (roll_chance_f(chance) || Priest::IsMindBlastTentacleGuaranteed(caster))
                Priest::TrySummonTentacle(caster, Priest::TentacleTrigger::MindBlast);
        }

        // (c) Void-touched Mind (7,2) capstone: "extends the duration of Void Eruption by 1 sec."
        // The 1 s value is load-bearing (design doc: at 3 s the window gains more duration per
        // second than it loses and Voidform becomes permanent) - reads/writes the live Aura
        // directly (SetDuration/SetMaxDuration), not the SpellInfo.
        if (caster->HasAura(SPELL_PRIEST_VOID_TOUCHED_MIND_R3))
            if (Aura* voidform = caster->GetAura(SPELL_PRIEST_VOIDFORM))
            {
                voidform->SetDuration(voidform->GetDuration() + 1000);
                voidform->SetMaxDuration(voidform->GetMaxDuration() + 1000);
            }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pri_mind_blast_shadow::HandleAfterCast);
    }
};

// 200248 - Call of the Void
class spell_pri_call_of_the_void : public SpellScript
{
    PrepareSpellScript(spell_pri_call_of_the_void);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_CALL_OF_THE_VOID_BUFF });
    }

    // "Locked out while Surrender to Madness is active. Button greys out, no cooldown consumed"
    // (design doc sec 4.4) - a CheckCast failure genuinely doesn't start the cooldown: cooldowns
    // are started later in Spell::cast()/finish(), which a SPELL_FAILED_* return from OnCheckCast
    // never reaches (Spell::CheckCast() runs before TakePower/TakeReagents/cooldown handling).
    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster && caster->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            return SPELL_FAILED_CASTER_AURASTATE;

        return SPELL_CAST_OK;
    }

    void HandleOnCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        int32 consumed = Priest::ConsumeMadness(caster, -1);
        caster->CastCustomSpell(SPELL_PRIEST_CALL_OF_THE_VOID_BUFF, SPELLVALUE_BASE_POINT0, consumed / 2, caster, true);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_pri_call_of_the_void::CheckCast);
        OnCast += SpellCastFn(spell_pri_call_of_the_void::HandleOnCast);
    }
};

// 200269 - Surrender to Madness (cast-time gate)
class spell_pri_surrender_to_madness : public SpellScript
{
    PrepareSpellScript(spell_pri_surrender_to_madness);

    // "Requires Call of the Void" (design doc sec 4.5) - enforced by requiring Madness > 0 rather
    // than a talent-tree depends_on arrow (PLAN sec 1/top of SHADOW.md: the (4,0)->(10,1) arrow is
    // impossible to draw and is dropped; this CheckCast is the only gate).
    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster || Priest::GetMadness(caster->ToPlayer()) <= 0)
            return SPELL_FAILED_CASTER_AURASTATE;

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_pri_surrender_to_madness::CheckCast);
    }
};

/*
 * 200269 - Surrender to Madness (aura). Per-second drain, two distinct exit paths (design doc sec
 * 4.5/4.6 - these are NOT the same thing, see each branch's own comment):
 *   1. Peaceful (no enemies engaged): removes immediately, this tick does not drain, no Sundered
 *      Mind follows.
 *   2. Madness-exhausted (the normal/expected end state): drains this tick's amount, and if
 *      Madness is now 0, removes - Sundered Mind DOES follow.
 * "Was this the peaceful exit" is tracked via a plain member bool, set immediately before the
 * early Remove() call in the peaceful branch and read back in OnRemoveEffect - simplest and safest
 * of the two approaches considered (the alternative, inferring it from GetRemoveMode(), can't
 * distinguish "removed because peaceful" from "removed because Madness hit 0" - both are the same
 * AURA_REMOVE_BY_DEFAULT manual removal from this class's own Remove() call).
 */
class spell_pri_surrender_to_madness_aura : public AuraScript
{
    PrepareAuraScript(spell_pri_surrender_to_madness_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_SUNDERED_MIND });
    }

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* caster = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!caster)
            return;

        // Exit 1 (peaceful), checked BEFORE draining this tick - "the combat exemption checks
        // enemies, not the priest's own combat state ... keying it to the priest would let any
        // Classless build carrying Feign Death, Vanish, Invisibility or Shadowmeld bypass the
        // drawback entirely" (design doc sec 4.5).
        if (!HasEngagedEnemyNearby(caster))
        {
            PreventDefaultAction();
            _peacefulExit = true;
            GetAura()->Remove();
            return;
        }

        // "Your Madness drains at 13 per second, increasing by 1 per second each second" -
        // `drain = 13 + elapsed`, `elapsed` starting at 0 on the very first tick so the first
        // drain is exactly 13, not 14 (design doc sec 4.5's literal formula, incremented after
        // computing this tick's drain so the NEXT tick sees elapsed=1 -> drain=14, etc).
        int32 drain = 13 + _elapsed;
        ++_elapsed;

        Priest::ConsumeMadness(caster, drain);

        // Exit 2 (Madness-exhausted, the normal end state) - Sundered Mind follows via
        // OnRemoveEffect below (this is NOT the peaceful branch, so `_peacefulExit` stays false).
        if (Priest::GetMadness(caster) <= 0)
        {
            PreventDefaultAction();
            GetAura()->Remove();
        }
    }

    void OnRemoveEffect(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* caster = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!caster)
            return;

        // Always despawn tentacles on end, regardless of which exit path (design doc sec 4.5:
        // "your Tentacles of Madness are destroyed" on the Madness-exhausted exit; the peaceful
        // exit's own tooltip doesn't repeat this, but leaving live, now-drawback-free tentacles
        // behind after a *voluntary* early end would be a strictly better outcome than letting the
        // drain finish - despawning unconditionally avoids that loophole).
        Priest::DespawnTentacles(caster);

        // Sundered Mind follows every removal EXCEPT the peaceful no-enemies exit (design doc sec
        // 4.5 "you do not suffer Sundered Mind" / sec 4.6 "Does not apply when Surrender ends
        // because no enemies remain").
        if (!_peacefulExit)
            caster->CastSpell(caster, SPELL_PRIEST_SUNDERED_MIND, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_surrender_to_madness_aura::OnPeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY);
        OnEffectRemove += AuraEffectRemoveFn(spell_pri_surrender_to_madness_aura::OnRemoveEffect, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

private:
    int32 _elapsed = 0;
    bool _peacefulExit = false;
};

/*
 * 200270 - Sundered Mind. THE highest-scrutiny item in this pass (design doc sec 4.6): "This
 * damage cannot be reduced, absorbed or prevented by any effect, including Dispersion." Calls
 * Unit::DealDamage directly with a pre-computed raw amount instead of going through a DBC
 * SCHOOL_DAMAGE/PERIODIC_DAMAGE effect - see the WP-B report for the full function-by-function
 * bypass trace (PW:S, Shadowform, Improved Shadowform, Dispersion, Versatility).
 */
class spell_pri_sundered_mind : public AuraScript
{
    PrepareAuraScript(spell_pri_sundered_mind);

    void OnPeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetTarget();
        if (!owner || !owner->IsAlive())
            return;

        PreventDefaultAction();

        uint32 damage = owner->CountPctFromMaxHealth(20);
        Unit::DealDamage(owner, owner, damage, nullptr, SELF_DAMAGE, SPELL_SCHOOL_MASK_SHADOW, GetSpellInfo(), false);
        owner->SendSpellNonMeleeDamageLog(owner, GetSpellInfo(), damage, SPELL_SCHOOL_MASK_SHADOW, 0, 0, false, 0, false, false);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pri_sundered_mind::OnPeriodic, EFFECT_0, SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 200271 - Madness (visible stack aura)
class spell_pri_madness : public AuraScript
{
    PrepareAuraScript(spell_pri_madness);

    void OnRemoveEffect(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // Every removal mode, not just the natural 30 s lapse (design doc sec 4.3). Death removes
        // this aura through RemoveAllAurasOnDeath with AURA_REMOVE_BY_DEFAULT, and a dispel is
        // AURA_REMOVE_BY_ENEMY_SPELL - an expire-only guard left the internal Madness value alive
        // and invisible in both cases. Priest::ConsumeMadness erases its own entry before removing
        // the aura, so the manual path just finds nothing left here.
        Priest::ClearMadness(GetTarget()->GetGUID());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_pri_madness::OnRemoveEffect, EFFECT_0, SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// Darkness (0,2), all 3 ranks. "2/4/6% chance to reset the cooldown of Mind Blast and cause your
// next Mind Blast to have no cooldown and cost no mana" (design doc). eff3 (EFFECT_2) is the
// proc-triggering DUMMY per SHADOW.md's talent table row.
class spell_pri_darkness : public AuraScript
{
    PrepareAuraScript(spell_pri_darkness);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_DARKNESS_BUFF });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        Unit* caster = GetTarget();
        if (Player* player = caster->ToPlayer())
            player->RemoveSpellCooldown(SPELL_PRIEST_MIND_BLAST, true);

        caster->CastSpell(caster, SPELL_PRIEST_DARKNESS_BUFF, true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_darkness::HandleProc, EFFECT_2, SPELL_AURA_DUMMY);
    }
};

// Shadow Reach (3,2) Capstone Bonus - bound to rank 2 (17323) only, so it activates at max rank
// like every other capstone. "Dealing direct magic damage to a target further than 20 yards away
// ... has a 10% chance to corrupt their soul, dealing Shadow damage over 3 seconds" (design doc).
// The 10% and the 5 s ICD are spell_proc data (procs_on in priest_trigger_spells.py), not here.
class spell_pri_shadow_reach_capstone : public AuraScript
{
    PrepareAuraScript(spell_pri_shadow_reach_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_CORRUPTED_SOUL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        if (!caster || !target)
            return false;

        return caster->GetDistance(target) > 20.0f;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        Unit* target = eventInfo.GetActionTarget();
        if (!damageInfo || !target || !damageInfo->GetDamage())
            return;

        // "Corrupted Soul DoT, 20% of the triggering direct damage spread over 3 ticks" (PLAN sec
        // 2's default; SHADOW.md talent table 3,2).
        int32 basepoints0 = int32(float(damageInfo->GetDamage()) * 0.2f / 3.0f);
        GetTarget()->CastCustomSpell(SPELL_PRIEST_CORRUPTED_SOUL, SPELLVALUE_BASE_POINT0, basepoints0, target, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_shadow_reach_capstone::CheckProc);
        OnProc += AuraProcFn(spell_pri_shadow_reach_capstone::HandleProc);
    }
};

// Lash of Insanity (5,0), all 3 ranks. "Your Mind Flay damage has a 5/10/15% chance to summon a
// Tentacle of Madness" (design doc) - subject to the shared ICD. The Mastery capstone half of this
// talent (player-only, tentacles never inherit it) lives in Priest::ApplyDoneDamagePctMods instead.
class spell_pri_lash_of_insanity : public AuraScript
{
    PrepareAuraScript(spell_pri_lash_of_insanity);

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        // While Surrender to Madness is up, spell_pri_mind_flay_madness already summons one on
        // *every* Mind Flay damage event, ICD-free (design doc sec 4.5). Rolling this talent's
        // percentage on the same event too would be a second ICD-free attempt per tick - the
        // MindFlay trigger is ICD-exempt during Surrender - which blows past the deliberate
        // ~19.35 spawn attempts/min budget in SHADOW.md "Spawn budget / ICD rules". Outside
        // Surrender this roll is the only Mind Flay spawn source, so normal play is unchanged.
        if (player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            return;

        Priest::TrySummonTentacle(player, Priest::TentacleTrigger::MindFlay);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_lash_of_insanity::HandleProc);
    }
};

// Writhing Agony (8,0), all 3 ranks. "Your Shadow Word: Pain damage has a 5/10/15% chance to
// summon a Tentacle of Madness" (design doc) - subject to the shared ICD. The x1.5 Mastery
// capstone half of this talent lives in the tentacle's own damage path in
// Priest::ApplyDoneDamagePctMods instead.
class spell_pri_writhing_agony : public AuraScript
{
    PrepareAuraScript(spell_pri_writhing_agony);

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        // Same rule as spell_pri_lash_of_insanity above: during Surrender,
        // spell_pri_shadow_word_pain_surrender already covers every SW:P tick ICD-free, so this
        // roll would only add a redundant second attempt on the same damage event.
        if (player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            return;

        Priest::TrySummonTentacle(player, Priest::TentacleTrigger::ShadowWordPain);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_writhing_agony::HandleProc);
    }
};

/*
 * Per-player Shadow state (Madness value, shared tentacle-spawn ICD, last Mind Blast spawn stamp)
 * lives in PriestMechanics.cpp's own file-scope maps, keyed by ObjectGuid. Auras cover the Madness
 * value's lifetime (spell_pri_madness above), but nothing covers the two timestamp maps, which
 * would otherwise keep an entry per priest who ever spawned a tentacle for the life of the process.
 * Same shape as FrostMageIcicleCombatReset (spell_mage.cpp) - a PlayerScript in a spell-script file
 * for the one hook a SpellScript/AuraScript can't reach.
 */
class PriestShadowStateCleanup : public PlayerScript
{
public:
    PriestShadowStateCleanup() : PlayerScript("PriestShadowStateCleanup", { PLAYERHOOK_ON_LOGOUT }) { }

    void OnPlayerLogout(Player* player) override
    {
        Priest::ClearShadowPlayerState(player->GetGUID());
    }
};

void AddSC_priest_shadow_spell_scripts()
{
    new PriestShadowStateCleanup();
    RegisterCreatureAI(npc_pri_tentacle_of_madness);
    RegisterSpellScript(spell_pri_tentacle_scaling);
    RegisterSpellScript(spell_pri_tentacle_mind_flay);
    RegisterSpellScript(spell_pri_mind_flay_madness);
    RegisterSpellScript(spell_pri_shadow_word_pain_surrender);
    RegisterSpellScript(spell_pri_mind_blast_shadow);
    RegisterSpellScript(spell_pri_call_of_the_void);
    RegisterSpellAndAuraScriptPair(spell_pri_surrender_to_madness, spell_pri_surrender_to_madness_aura);
    RegisterSpellScript(spell_pri_sundered_mind);
    RegisterSpellScript(spell_pri_madness);
    RegisterSpellScript(spell_pri_darkness);
    RegisterSpellScript(spell_pri_shadow_reach_capstone);
    RegisterSpellScript(spell_pri_lash_of_insanity);
    RegisterSpellScript(spell_pri_writhing_agony);
}
