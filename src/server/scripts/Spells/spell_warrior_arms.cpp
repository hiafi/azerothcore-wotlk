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
 * Warrior rework - Arms SpellScripts (warrior-rework S2; docs/reworks/warrior-arms-rework.md). Thin bindings: every
 * mechanic body lives in WarriorMechanics (Warrior::), the damage hooks in warrior_hooks.cpp.
 *
 * spell_warr_mortal_strike_arms       12294    D25: landed main target, once -> Warrior::OnMortalStrikeHit
 * spell_warr_rend_arms                772      D20/D23: Rend apply/remove -> Warrior::UpdateBloodFrenzy
 * spell_warr_deep_wounds_rework       -12834   D5: talent proc (crit) -> Warrior::ApplyDeepWounds (players only;
 *                                               replaces the unbound stock spell_warr_deep_wounds_aura)
 * spell_warr_deep_wounds_holder       204496   D5/D20: ticks 204497 with the stored share; Blood Frenzy on apply/remove
 * spell_warr_sudden_death_reset       -29723   D9: CAST-phase proc -> Warrior::ResetMortalStrike
 * spell_warr_heroic_leap_landing      204401   D8/D13: Weight of the Earth's engaged outer ring and Colossus Smash;
 *                                               Juggernaut grant
 * spell_warr_bladestorm_whirl         204495   D10: once per whirl -> Warrior::RollOncePerCastMeleeProcs
 * spell_warr_whirlwind_seismic        1680     D19: Warrior::ScheduleSeismicEcho; S3: off-hand 44949 under
 *                                               Warrior::PressChargeGuard (one Recklessness charge per press)
 * spell_warr_anger_management         -12296   D12: the rage trickle only in combat
 * spell_warr_weapon_spec_sword        204514, 204517, 204520   D17: the sword strike 204511 on the struck target
 * spell_warr_sweeping_strikes_rework  204493   D4/R6: puts Blade Flurry on a 30 s cooldown
 */

#include "EngagementMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SharedDefines.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include "WarriorMechanics.h"
#include <algorithm>
#include <list>

namespace
{
    // Stock rows not in WarriorData.
    constexpr uint32 SPELL_BLADE_FLURRY = 13877; // rogue; spell_rog_blade_flurry_rework sets the other direction

    // D4/R6: the peer's lock-out after a Sweeping Strikes cast (full, never haste-scaled), in ms.
    constexpr uint32 SWEEPING_PEER_LOCKOUT_MS = 30000;

    // CAST-phase procs see every non-triggered melee-class cast (Unit::ProcSkillsAndAuras forces
    // PROC_SPELL_TYPE_MASK_ALL there), stances and utility included. Only a strike counts: a spell with a direct damage
    // effect, plus Execute 5308 (damage in its triggered 20647) and Heroic Leap 204400 (damage in the landing).
    bool IsStrikeCast(SpellInfo const* spellInfo)
    {
        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    return true;
                default:
                    break;
            }
        }

        if (spellInfo->SpellFamilyName != SPELLFAMILY_WARRIOR)
            return false;

        return (spellInfo->SpellFamilyFlags[0] & 0x20000000) || (spellInfo->SpellFamilyFlags[2] & 0x1);
    }
}

// 12294 - Mortal Strike (D25). AfterHit runs only for a landed target; once per cast, the main target only.
class spell_warr_mortal_strike_arms : public SpellScript
{
    PrepareSpellScript(spell_warr_mortal_strike_arms);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_OVERPOWER_204403, WarriorData::SPELL_REND,
            WarriorData::SPELL_COLOSSUS_SMASH_DEBUFF, WarriorData::SPELL_STRENGTH_OF_ARMS_BUFF_R1,
            WarriorData::SPELL_STRENGTH_OF_ARMS_BUFF_R2, WarriorData::SPELL_ENDLESS_RAGE_OVERFLOW,
            WarriorData::SPELL_EXPLOITER_DEBUFF, WarriorData::SPELL_JUGGERNAUT_BUFF });
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (_done || !player || !target || target != GetExplTargetUnit())
            return;

        _done = true;
        Warrior::OnMortalStrikeHit(player, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warr_mortal_strike_arms::HandleAfterHit);
    }

private:
    bool _done = false;
};

// 772 - Rend (D20, D23). Blood Frenzy follows this warrior's bleeds: re-evaluated whenever Rend lands or ends (death
// included). The aura has already left the target's applied list in AfterEffectRemove.
// D23 (Q9, user rulings 2026-10-30): Rend keeps the stock weapon gate, and the weapon talents boost it like any other
// weapon ability: Unit::SpellPctDamageModsDone folds the weapon-gated physical aura-79 mods (Two-Handed Weapon
// Specialization, Two-Handed Weapon Mastery, One-Handed Weapon Specialization) into the bleed at application through
// the core's normal path; nothing is divided out here. Fury's ungated aura-79 auras (Enrage 204636, the Titan's Grip
// penalty 204651, both EquippedItemClass -1) reach it the same way; stock 49152 is forced to 0.
class spell_warr_rend_arms : public AuraScript
{
    PrepareAuraScript(spell_warr_rend_arms);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R1,
            WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R2 });
    }

    void HandleApplyOrRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (Player* player = caster ? caster->ToPlayer() : nullptr)
            Warrior::UpdateBloodFrenzy(player, GetTarget());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warr_rend_arms::HandleApplyOrRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_rend_arms::HandleApplyOrRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

// 12834, 12849, 12867 - Deep Wounds talent ranks (D5, R2). The stock trigger (12162+) is replaced by the accumulating
// percent bleed on 204496. NPCs (9084, 9238, 14520; SAI 14513, 14520) cast 12867 as a plain spell: nothing for them.
class spell_warr_deep_wounds_rework : public AuraScript
{
    PrepareAuraScript(spell_warr_deep_wounds_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_DEEP_WOUNDS_HOLDER, WarriorData::SPELL_DEEP_WOUNDS_TICK });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        // NPC casters keep the default proc; it triggers 12162+, which is unbound now, so they get no bleed either way.
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        PreventDefaultAction();

        Unit* target = eventInfo.GetActionTarget();
        if (!target)
            return;

        // White swings carry the hand in the type mask; melee abilities carry it there and in the damage info.
        WeaponAttackType attType = BASE_ATTACK;
        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_OFFHAND_ATTACK)
            attType = OFF_ATTACK;
        else if (DamageInfo const* damageInfo = eventInfo.GetDamageInfo())
            if (damageInfo->GetAttackType() == OFF_ATTACK)
                attType = OFF_ATTACK;

        Warrior::ApplyDeepWounds(player, target, attType);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_deep_wounds_rework::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 204496 - Deep Wounds holder (D5, Bloodstorm shape). Every second the holder deals this warrior's stored per-tick
// share through 204497 (no crit, no caster modifiers, ignores armor). Blood Frenzy follows it like Rend (D20).
class spell_warr_deep_wounds_holder : public AuraScript
{
    PrepareAuraScript(spell_warr_deep_wounds_holder);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_DEEP_WOUNDS_HOLDER, WarriorData::SPELL_DEEP_WOUNDS_TICK,
            WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R1, WarriorData::SPELL_BLOOD_FRENZY_DEBUFF_R2 });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Player* warrior = caster ? caster->ToPlayer() : nullptr;
        Unit* target = GetUnitOwner();
        if (!warrior || !target || !target->IsAlive())
            return;

        uint32 const tick = Warrior::GetPercentBleedTick(warrior, target, WarriorData::SPELL_DEEP_WOUNDS_HOLDER);
        if (!tick)
            return;

        // A final value (custom base points are not reduced by DieSides). No triggering aura, so the bleed keeps
        // ticking if the warrior dies (Doomblade / Bloodstorm precedent).
        int32 basePoints = int32(tick);
        warrior->CastCustomSpell(target, WarriorData::SPELL_DEEP_WOUNDS_TICK, &basePoints, nullptr, nullptr, true);
    }

    void HandleApplyOrRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (Player* player = caster ? caster->ToPlayer() : nullptr)
            Warrior::UpdateBloodFrenzy(player, GetTarget());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_deep_wounds_holder::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_warr_deep_wounds_holder::HandleApplyOrRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_deep_wounds_holder::HandleApplyOrRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 29723, 29725, 29724 - Sudden Death (D9, R10). The CAST-phase row (white swings once per landed swing, abilities once
// per cast, 6 s ICD on the aura) resets Mortal Strike. Mortal Strike itself never rolls. Effect 0 stays aura 42 and
// effect 1 the rage the stock Execute script keeps; the default trigger is suppressed.
class spell_warr_sudden_death_reset : public AuraScript
{
    PrepareAuraScript(spell_warr_sudden_death_reset);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_MORTAL_STRIKE });
    }

    // A white swing has no spell; an ability cast carries its own and must be a strike (IsStrikeCast).
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetTarget()->IsPlayer())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return true;

        return spellInfo->Id != WarriorData::SPELL_MORTAL_STRIKE
            && !spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS) && IsStrikeCast(spellInfo);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        if (Player* player = GetTarget()->ToPlayer())
            Warrior::ResetMortalStrike(player);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_sudden_death_reset::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_sudden_death_reset::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 204401 - Heroic Leap landing (D8, D13, R9). Cast triggered by the player at the jump's end (TARGET_DEST_DEST, area
// UNIT_DEST_AREA_ENEMY). Weight of the Earth's RADIUS mod widens the search to 16 yd; this filter keeps the stock
// inner ring for everyone (measured like the core's area search, 2D, plus an NPC's combat reach) and the outer ring
// only for enemies already engaged with the warrior or group, so the wider ring never pulls. With the talent each
// landed target also gets the Colossus Smash debuff; every landing (zero targets included) may grant Juggernaut.
class spell_warr_heroic_leap_landing : public SpellScript
{
    PrepareSpellScript(spell_warr_heroic_leap_landing);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_WEIGHT_OF_THE_EARTH, WarriorData::SPELL_COLOSSUS_SMASH_DEBUFF,
            WarriorData::SPELL_JUGGERNAUT_BUFF, WarriorData::SPELL_JUGGERNAUT_CRIT });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Player* player = GetCaster()->ToPlayer();
        WorldLocation const* dest = GetExplTargetDest();
        if (!player || !dest)
            return;

        // No caster: the radius without Weight of the Earth's mod (8 yd).
        float const innerRadius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius();
        bool const wide = player->HasAura(WarriorData::SPELL_WEIGHT_OF_THE_EARTH);

        targets.remove_if([player, dest, innerRadius, wide](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            if (!unit)
                return true;

            float const reach = unit->IsControlledByPlayer() ? 0.0f : unit->GetCombatReach();
            if (unit->GetExactDist2d(dest) <= innerRadius + reach)
                return false;

            return !wide || !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });
    }

    // AfterHit runs only for a landed target.
    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (player && target && player->HasAura(WarriorData::SPELL_WEIGHT_OF_THE_EARTH))
            Warrior::ApplyColossusSmash(player, target);
    }

    void HandleAfterCast()
    {
        if (Player* player = GetCaster()->ToPlayer())
            Warrior::GrantJuggernaut(player);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_heroic_leap_landing::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
        AfterHit += SpellHitFn(spell_warr_heroic_leap_landing::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warr_heroic_leap_landing::HandleAfterCast);
    }
};

// 204495 - Bladestorm whirl (D10). Triggered and proc-suppressed, so no data proc rolls on it: once per whirl it rolls
// Sudden Death, Wrecking Crew and the sword strike by hand. The first landed target is preferred (the sword strike's
// target), else the first target struck at all (a fully avoided whirl still rolls, like an ability's CAST phase).
class spell_warr_bladestorm_whirl : public SpellScript
{
    PrepareSpellScript(spell_warr_bladestorm_whirl);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_WRECKING_CREW_BUFF_R1, WarriorData::SPELL_WRECKING_CREW_BUFF_R2,
            WarriorData::SPELL_WRECKING_CREW_BUFF_R3, WarriorData::SPELL_WEAPON_SPECIALIZATION_STRIKE });
    }

    void HandleBeforeHit(SpellMissInfo /*missInfo*/)
    {
        if (!_firstTarget)
            _firstTarget = GetHitUnit();
    }

    void HandleAfterHit()
    {
        if (!_firstLanded)
            _firstLanded = GetHitUnit();
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = _firstLanded ? _firstLanded : _firstTarget;
        if (!player || !target)
            return;

        Warrior::RollOncePerCastMeleeProcs(player, target);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_warr_bladestorm_whirl::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_warr_bladestorm_whirl::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warr_bladestorm_whirl::HandleAfterCast);
    }

private:
    Unit* _firstTarget = nullptr;
    Unit* _firstLanded = nullptr;
};

// 1680 - Whirlwind (D19). Seismic Reverberation: the echo is scheduled +500 ms after the cast (the off-hand 44949 hits
// may land after this AfterCast); Warrior::ScheduleSeismicEcho checks the talent and counts the targets then.
// S3 (Q3 / D6): effect 1 triggers the off-hand 44949 at launch, before this cast's own crit rolls; 44949 carries
// Recklessness' bit and would spend its own charge (on the last one, before the main-hand hits read it). The default
// trigger runs unchanged (same targets and flags) inside Warrior::PressChargeGuard, so one Whirlwind spends one charge.
class spell_warr_whirlwind_seismic : public SpellScript
{
    PrepareSpellScript(spell_warr_whirlwind_seismic);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_SEISMIC_REVERBERATION_ECHO });
    }

    void HandleOffhandLaunch(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);
        Warrior::PressChargeGuard const chargeGuard(GetCaster()->ToPlayer());
        GetSpell()->EffectTriggerSpell(effIndex);
    }

    void HandleAfterCast()
    {
        if (Player* player = GetCaster()->ToPlayer())
            Warrior::ScheduleSeismicEcho(player);
    }

    void Register() override
    {
        OnEffectLaunch += SpellEffectFn(spell_warr_whirlwind_seismic::HandleOffhandLaunch, EFFECT_1,
            SPELL_EFFECT_TRIGGER_SPELL);
        AfterCast += SpellCastFn(spell_warr_whirlwind_seismic::HandleAfterCast);
    }
};

// 12296, 204541, 204542 - Anger Management (D12). Effect 0 is a PERIODIC_ENERGIZE (rage through ModifyPower, so
// Endless Rage sees it); it only ticks in combat. The talent aura is permanent, and the core's energize tick returns
// before ModifyPower for a permanent aura at full power, so at the exact cap the tick's rage is handed to the Endless
// Rage overflow by hand (OnRageOverflow returns at once for anyone without the capstone).
class spell_warr_anger_management : public AuraScript
{
    PrepareAuraScript(spell_warr_anger_management);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* target = GetTarget();
        if (!target->IsInCombat())
        {
            PreventDefaultAction();
            return;
        }

        if (target->GetPower(POWER_RAGE) == target->GetMaxPower(POWER_RAGE))
        {
            PreventDefaultAction();
            Warrior::OnRageOverflow(target, std::max(aurEff->GetAmount(), 0));
        }
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_anger_management::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_ENERGIZE);
    }
};

// 204514, 204517, 204520 - Weapon Specialization, sword passives (D17). Present only while the main hand is a sword
// (Warrior::UpdateWeaponSpecialization). CAST-phase events carry no victim, so the target is the swing's victim or the
// ability's explicit unit target. Main hand only (an off-hand swing never procs), a hostile target in melee range.
// Casts the strike 204511 (proc-suppressed in data), never 16459 (a real extra swing makes rage and procs).
class spell_warr_weapon_spec_sword : public AuraScript
{
    PrepareAuraScript(spell_warr_weapon_spec_sword);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_WEAPON_SPECIALIZATION_STRIKE });
    }

    static Unit* GetStrikeTarget(ProcEventInfo const& eventInfo)
    {
        if (Unit* target = eventInfo.GetActionTarget())
            return target;

        if (Spell const* spell = eventInfo.GetProcSpell())
            return spell->m_targets.GetUnitTarget();

        return nullptr;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player || (eventInfo.GetTypeMask() & PROC_FLAG_DONE_OFFHAND_ATTACK))
            return false;

        if (SpellInfo const* spellInfo = eventInfo.GetSpellInfo())
            if (spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS) || !IsStrikeCast(spellInfo))
                return false;

        Unit* target = GetStrikeTarget(eventInfo);
        return target && target->IsAlive() && player->IsValidAttackTarget(target)
            && player->IsWithinMeleeRange(target);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        if (Unit* target = GetStrikeTarget(eventInfo))
            GetTarget()->CastSpell(target, WarriorData::SPELL_WEAPON_SPECIALIZATION_STRIKE, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_weapon_spec_sword::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_weapon_spec_sword::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 204493 - Sweeping Strikes (D4, R6). Shares its lock-out with Blade Flurry across families (a category can't): the
// peer gets the full 30 s (never shortened), resent so the client shows it. The capture and copies are the hooks'.
class spell_warr_sweeping_strikes_rework : public SpellScript
{
    PrepareSpellScript(spell_warr_sweeping_strikes_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_BLADE_FLURRY });
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || !player->HasSpell(SPELL_BLADE_FLURRY)
            || player->GetSpellCooldownDelay(SPELL_BLADE_FLURRY) >= SWEEPING_PEER_LOCKOUT_MS)
            return;

        player->AddSpellCooldown(SPELL_BLADE_FLURRY, 0, SWEEPING_PEER_LOCKOUT_MS, true);
        player->ResendSpellCooldown(SPELL_BLADE_FLURRY);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_warr_sweeping_strikes_rework::HandleAfterCast);
    }
};

void AddSC_warrior_arms_spell_scripts()
{
    RegisterSpellScript(spell_warr_mortal_strike_arms);
    RegisterSpellScript(spell_warr_rend_arms);
    RegisterSpellScript(spell_warr_deep_wounds_rework);
    RegisterSpellScript(spell_warr_deep_wounds_holder);
    RegisterSpellScript(spell_warr_sudden_death_reset);
    RegisterSpellScript(spell_warr_heroic_leap_landing);
    RegisterSpellScript(spell_warr_bladestorm_whirl);
    RegisterSpellScript(spell_warr_whirlwind_seismic);
    RegisterSpellScript(spell_warr_anger_management);
    RegisterSpellScript(spell_warr_weapon_spec_sword);
    RegisterSpellScript(spell_warr_sweeping_strikes_rework);
}
