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
 * Death Knight rework - shared spell scripts (death-knight-rework DK0a; docs/reworks/death-knight-shared-rework.md).
 */

#include "DeathKnightMechanics.h"
#include "EngagementMechanics.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <list>

namespace
{
    // Stock ids the DSL does not declare (they are not edited by the rework), so DeathKnightData has no name for them.
    constexpr uint32 SPELL_DK_BLOOD_PLAGUE = 55078;
    constexpr uint32 SPELL_DK_FROST_FEVER = 55095;
    // Army of the Dead passive (49040); the pet-scaling ids are in PetDefines.h
    constexpr uint32 SPELL_DK_ARMY_PASSIVE = 49040;
}

// 49998 - Death Strike (main hand only; the off-hand 66188 has no binding and never heals). EFFECT_2 is a DUMMY whose
// value is the heal percent of the recent damage taken (shared doc "Death Strike": 25). The heal is the larger of that
// share and the minimum health share, computed by DeathKnight::ComputeDeathStrikeHeal. The dummy effect only fires on
// a hit, so a miss, dodge or parry heals nothing.
class spell_dk_death_strike_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_death_strike_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DEATH_STRIKE_HEAL });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !GetHitUnit())
            return;

        int32 const heal = int32(DeathKnight::ComputeDeathStrikeHeal(player, GetEffectValue()));
        if (heal <= 0)
            return;

        player->CastCustomSpell(DeathKnightData::SPELL_DEATH_STRIKE_HEAL, SPELLVALUE_BASE_POINT0, heal, player,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dk_death_strike_rework::HandleDummy, EFFECT_2, SPELL_EFFECT_DUMMY);
    }
};

// 48707 - Anti-Magic Shell (on self). A second script beside the stock spell_dk_anti_magic_shell_self: the damage the
// shell absorbs counts toward Death Strike's record (shared doc "Death Strike": "counts damage absorbed by the Death
// Knight's own shields"). AfterEffectAbsorb receives the amount actually absorbed after clamping to the hit.
class spell_dk_ams_damage_record : public AuraScript
{
    PrepareAuraScript(spell_dk_ams_damage_record);

    void HandleAfterAbsorb(AuraEffect* /*aurEff*/, DamageInfo& /*dmgInfo*/, uint32& absorbAmount)
    {
        if (!absorbAmount)
            return;

        Player* player = GetTarget()->ToPlayer();
        if (player && DeathKnight::TracksDamageTaken(player))
            DeathKnight::RecordDamageTaken(player, absorbAmount);
    }

    void Register() override
    {
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_dk_ams_damage_record::HandleAfterAbsorb, EFFECT_0);
    }
};

// 203001 - Death's Caress. EFFECT_0 hits the explicit target; EFFECT_1 is the extra-target area around it. The area
// keeps at most DEATHS_CARESS_EXTRA_TARGETS enemies already in combat with the Death Knight or the group, nearest to
// the explicit target first, and never the explicit target itself (EFFECT_0 owns it) or the caster. Every unit hit by
// either damage effect gets Blood Plague from the Death Knight, triggered; the helper is never cast at the caster.
class spell_dk_deaths_caress : public SpellScript
{
    PrepareSpellScript(spell_dk_deaths_caress);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DK_BLOOD_PLAGUE });
    }

    void FilterExtraTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* explicitTarget = GetExplTargetUnit();
        if (!player || !explicitTarget)
        {
            targets.clear();
            return;
        }

        targets.remove_if([player, explicitTarget](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || unit == explicitTarget || unit == player ||
                !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });

        targets.sort([explicitTarget](WorldObject const* a, WorldObject const* b)
        {
            return explicitTarget->GetExactDist(a) < explicitTarget->GetExactDist(b);
        });

        if (targets.size() > uint32(DeathKnightData::DEATHS_CARESS_EXTRA_TARGETS))
            targets.resize(uint32(DeathKnightData::DEATHS_CARESS_EXTRA_TARGETS));
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster)
            return;

        // Each unit sits in exactly one of the two damage effects; the guid set is a guard against a double apply
        if (!_infected.insert(target->GetGUID()).second)
            return;

        caster->CastSpell(target, SPELL_DK_BLOOD_PLAGUE, true);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_deaths_caress::FilterExtraTargets, EFFECT_1,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_dk_deaths_caress::HandleHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        OnEffectHitTarget += SpellEffectFn(spell_dk_deaths_caress::HandleHit, EFFECT_1, SPELL_EFFECT_SCHOOL_DAMAGE);
    }

    GuidSet _infected;
};

// 50842 - Pestilence (replaces the stock spell_dk_pestilence). EFFECT_2 is the 10 yd script-effect area around the
// target. The area keeps only enemies already in combat with the Death Knight or the group (never pulls). For each such
// unit other than the primary target, every disease the Death Knight has on the primary is copied fresh (triggered, at
// the Death Knight's current stats) unless that unit already carries the Death Knight's own copy: a copy never
// overwrites or refreshes. No Glyph of Disease refresh (glyphs are retired). Then DeathKnight::OnPestilenceCopy, once
// per enemy reached (wound copies and On a Pale Horse hang off it in S3).
class spell_dk_pestilence_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_pestilence_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DK_BLOOD_PLAGUE, SPELL_DK_FROST_FEVER });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
        {
            targets.clear();
            return;
        }

        Unit* primary = GetExplTargetUnit();
        targets.remove_if([player, primary](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            if (!unit)
                return true;

            // The primary target is the one the player chose; it is not copied onto, so leave it alone
            return unit != primary && !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });
    }

    void HandleScriptEffect(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* primary = GetExplTargetUnit();
        Unit* hitUnit = GetHitUnit();
        if (!player || !primary || !hitUnit || hitUnit == primary)
            return;

        for (uint32 const disease : { SPELL_DK_BLOOD_PLAGUE, SPELL_DK_FROST_FEVER })
        {
            if (!primary->HasAura(disease, player->GetGUID()) || hitUnit->HasAura(disease, player->GetGUID()))
                continue;

            player->CastSpell(hitUnit, disease, true);
        }

        DeathKnight::OnPestilenceCopy(player, primary, hitUnit);
    }

    // S3 U26 (WP-R M1): On a Pale Horse also hits the primary ("each enemy it hits"), once per cast and after every
    // copy, so a killing hit on the primary can no longer wipe its diseases and wounds before they are copied.
    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* primary = GetExplTargetUnit();
        if (!player || !primary || !primary->IsAlive())
            return;

        DeathKnight::OnPestilencePrimary(player, primary);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_pestilence_rework::FilterTargets, EFFECT_2,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_dk_pestilence_rework::HandleScriptEffect, EFFECT_2,
            SPELL_EFFECT_SCRIPT_EFFECT);
        AfterCast += SpellCastFn(spell_dk_pestilence_rework::HandleAfterCast);
    }
};

// 50461 - Anti-Magic Zone (the aura on each party member, cast by the zone creature; the DK is the zone's owner).
// Each member's copy is unlimited (amount -1): the shared pool lives on the zone (DeathKnight::ConsumeZoneAbsorb),
// so the area aura re-applying a copy never refills it. AMZ_SPELL_REDUCTION_PCT% of every hit it covers is wanted;
// the pool decides how much of that is absorbed, and unsummons the zone when it runs dry.
class spell_dk_anti_magic_zone_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_anti_magic_zone_rework);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = -1;
    }

    void HandleAbsorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        absorbAmount = 0;

        Unit* zone = GetCaster();
        Unit* ownerUnit = zone ? zone->GetOwner() : nullptr;
        Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        uint32 const wanted = CalculatePct(dmgInfo.GetDamage(), DeathKnightData::AMZ_SPELL_REDUCTION_PCT);
        if (!wanted)
            return;

        absorbAmount = DeathKnight::ConsumeZoneAbsorb(zone, owner, wanted);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_anti_magic_zone_rework::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_dk_anti_magic_zone_rework::HandleAbsorb, EFFECT_0);
    }
};

// Runes (death-knight-rework DK0b). Each rune is a self aura (group 1271, one at a time); the proc effect is EFFECT_0.
// 53344 Fallen Crusader, 53343 Razorice, 203040 Exsanguination, 203042 Boiling Blight, 203044 Apocalypse,
// 203049 Unending Thirst. The weapon glow follows the active rune (DeathKnight::ApplyRuneGlow / RestoreRuneGlow); the
// CheckProc guard is DeathKnight::RuneProcAllowed with per-rune flags.
class spell_dk_rune_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_rune_rework);

    // Writes the glow of whichever rune is up now (the aura being applied, or the one left after a removal), or puts
    // the real enchant visuals back when none is up or the one up has no glow (a rune with glow 0).
    void RefreshGlow()
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        uint32 const activeRune = DeathKnight::GetActiveRune(player);
        if (activeRune && DeathKnight::GetRuneGlowEnchant(activeRune))
            DeathKnight::ApplyRuneGlow(player);
        else
            DeathKnight::RestoreRuneGlow(player);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        RefreshGlow();
    }

    // By now the aura is already gone from the target (Unit::_UnapplyAura), so the active rune is the other one, if any
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        RefreshGlow();
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        bool dualWieldHalf = false;
        bool oncePerCast = true;
        switch (GetId())
        {
            case DeathKnightData::SPELL_RUNE_OF_THE_FALLEN_CRUSADER:
            case DeathKnightData::SPELL_RUNE_OF_THE_APOCALYPSE:
                dualWieldHalf = true;
                break;
            case DeathKnightData::SPELL_RUNE_OF_BOILING_BLIGHT:
                oncePerCast = false;
                break;
            default:
                break;
        }

        return DeathKnight::RuneProcAllowed(GetTarget(), eventInfo, GetId(), dualWieldHalf, oncePerCast);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dk_rune_rework::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dk_rune_rework::HandleRemove, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        DoCheckProc += AuraCheckProcFn(spell_dk_rune_rework::CheckProc);
    }
};

// 53343 - Rune of Razorice (second script beside spell_dk_rune_rework). Every proc deals Razor Frost: Frost damage of
// RAZORICE_DAMAGE_PCT% of the triggering hit's damage (never per weapon), and adds a Frost Vulnerability stack. Both
// are cast by the Death Knight at the hit target: the explicit target is what an effect with an enemy implicit target
// resolves to, and 51714 only amplifies its own caster's Frost spells.
class spell_dk_rune_of_razorice_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_rune_of_razorice_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_RAZOR_FROST, DeathKnightData::SPELL_FROST_VULNERABILITY });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!caster || !target || !damageInfo || caster == target)
            return;

        int32 const damage = int32(CalculatePct(damageInfo->GetDamage(), DeathKnightData::RAZORICE_DAMAGE_PCT));
        if (damage > 0)
            caster->CastCustomSpell(DeathKnightData::SPELL_RAZOR_FROST, SPELLVALUE_BASE_POINT0, damage, target,
                TRIGGERED_FULL_MASK, nullptr, aurEff);

        caster->CastSpell(target, DeathKnightData::SPELL_FROST_VULNERABILITY, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dk_rune_of_razorice_rework::HandleProc, EFFECT_0, SPELL_AURA_ANY);
    }
};

// 203044 - Rune of the Apocalypse (second script beside spell_dk_rune_rework). A proc grants one of the four blessings
// at random (Conquest: Haste, War: Critical Strike, Famine: Versatility, Death: Mastery), on the Death Knight.
class spell_dk_rune_of_the_apocalypse : public AuraScript
{
    PrepareAuraScript(spell_dk_rune_of_the_apocalypse);

    static constexpr std::array<uint32, 4> Blessings =
    {
        DeathKnightData::SPELL_CONQUEST,
        DeathKnightData::SPELL_WAR,
        DeathKnightData::SPELL_FAMINE,
        DeathKnightData::SPELL_DEATH
    };

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Blessings[0], Blessings[1], Blessings[2], Blessings[3] });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        target->CastSpell(target, Blessings[urand(0, uint32(Blessings.size() - 1))], TRIGGERED_FULL_MASK, nullptr,
            aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dk_rune_of_the_apocalypse::HandleProc, EFFECT_0, SPELL_AURA_ANY);
    }
};

// 203053 - Rune Haste Sync (hidden, every DK through Runic Focus). Every 500 ms DeathKnight::SyncRuneHaste keeps
// 203052's three rune-regen amounts equal to the spell haste percent, rescaling the runes already recharging first.
class spell_dk_rune_haste_sync : public AuraScript
{
    PrepareAuraScript(spell_dk_rune_haste_sync);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_RUNE_HASTE });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* player = GetUnitOwner()->ToPlayer();
        Aura* runeHaste = player ? player->GetAura(DeathKnightData::SPELL_RUNE_HASTE) : nullptr;
        if (!runeHaste)
            return;

        DeathKnight::SyncRuneHaste(player, runeHaste);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_rune_haste_sync::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 203056 - Minion Mirror (hidden, cast on the minion by its owner; the owner is the aura's caster). EFFECT_0 is the
// minion's attack power, EFFECT_1 its spell power (Gargoyle only), EFFECT_2 the 1 s tick that has
// DeathKnight::RefreshMinionMirror update all three mirror auras (203056, 203057, 203058) from the owner, changing an
// amount only when it differs. The calc-amount hooks seed the first values (and any core recalculation) with the same
// shares RefreshMinionMirror applies. ALWAYS_HIT keeps these off the stock immunity block.
class spell_dk_minion_mirror : public AuraScript
{
    PrepareAuraScript(spell_dk_minion_mirror);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_MINION_MIRROR_CRIT_HASTE,
            DeathKnightData::SPELL_MINION_MIRROR_VERSATILITY });
    }

    void CalcAttackPower(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Unit* caster = GetCaster();
        Player* owner = caster ? caster->ToPlayer() : nullptr;
        if (!owner)
            return;

        // S3 D12: the same per-kind share as RefreshMinionMirror (shared party AP out, the ghoul kind minus its base
        // AP and unclamped, every other kind clamped at 0).
        amount = DeathKnight::GetMinionMirrorAttackPower(owner, GetUnitOwner());
    }

    void CalcSpellPower(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Unit* owner = GetCaster();
        if (!owner)
            return;

        if (DeathKnight::GetMinionKind(GetUnitOwner()) != DeathKnight::MinionKind::Gargoyle)
        {
            amount = 0;
            return;
        }

        amount = int32(CalculatePct(std::max<int32>(0, int32(owner->GetTotalAttackPowerValue(BASE_ATTACK))),
            DeathKnightData::MINION_SP_SHARE_PCT));
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Player* owner = caster ? caster->ToPlayer() : nullptr;
        if (!owner)
            return;

        DeathKnight::RefreshMinionMirror(GetUnitOwner(), owner);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_mirror::CalcAttackPower, EFFECT_0,
            SPELL_AURA_MOD_ATTACK_POWER);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_mirror::CalcSpellPower, EFFECT_1,
            SPELL_AURA_MOD_DAMAGE_DONE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_minion_mirror::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 51996 - Death Knight Pet Scaling 02
// 54566 - Death Knight Pet Scaling 01
// 61697 - Death Knight Pet Scaling 03
// 49040 - Army of the Dead Passive
// A fork of the stock spell_dk_pet_scaling and spell_dk_army_of_the_dead_passive, rebound by the rework (the stock
// scripts are unbound on these four ids). Same hooks as stock, but the stats the Minion Mirror (203056-203058) now
// carries are no longer shared here: Strength 0, attack power 0, spell power 0, haste 0. Stamina (54566) and the Army
// ghouls' health (49040 EFFECT_1) are read live from the owner, with no snapshot. The stock state-immunity block, the
// Bloodlust/Heroism immunity of 49040 and the periodic recalculation stay (ALWAYS_HIT mirrors bypass the immunities).
class spell_dk_minion_passthrough : public AuraScript
{
    PrepareAuraScript(spell_dk_minion_passthrough);

    void CalculateZero(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        amount = 0;
        canBeRecalculated = false;
    }

    void CalculateStatAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = 0;

        // Only Stamina is shared; Strength (and anything else) is 0
        if (Stats(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue) != STAT_STAMINA)
            return;

        Unit* minion = GetUnitOwner();
        Player* owner = DeathKnight::GetMinionOwner(minion);
        if (!owner || DeathKnight::GetMinionKind(minion) == DeathKnight::MinionKind::None)
            return;

        amount = int32(CalculatePct(std::max<int32>(0, int32(owner->GetStat(STAT_STAMINA))),
            DeathKnightData::MINION_STAMINA_SHARE_PCT));
    }

    void CalculateHealthAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // Army ghoul health: 20% of the owner's maximum health, read live
        if (Unit* owner = GetUnitOwner()->GetOwner())
            amount = owner->CountPctFromMaxHealth(20);
    }

    void HandleEffectApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* minion = GetUnitOwner();

        if (GetId() == SPELL_DK_ARMY_PASSIVE)
        {
            if (minion->IsPet())
                return;

            ApplyStatImmunities(minion);
            // Heroism / Bloodlust immunity
            minion->ApplySpellImmune(0, IMMUNITY_ID, 32182, true);
            minion->ApplySpellImmune(0, IMMUNITY_ID, 2825, true);
            return;
        }

        // The pet-scaling immunities hang off PS02's aura 193 effect (stock)
        if (aurEff->GetAuraType() != SPELL_AURA_MELEE_SLOW)
            return;

        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_CASTING_SPEED_NOT_STACK, true,
            SPELL_BLOCK_TYPE_POSITIVE);
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_MELEE_RANGED_HASTE, true, SPELL_BLOCK_TYPE_POSITIVE);
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MELEE_SLOW, true, SPELL_BLOCK_TYPE_POSITIVE);

        if (!minion->IsPet())
            ApplyStatImmunities(minion);
    }

    static void ApplyStatImmunities(Unit* minion)
    {
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_STAT, true, SPELL_BLOCK_TYPE_POSITIVE);
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE, true,
            SPELL_BLOCK_TYPE_POSITIVE);
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_ATTACK_POWER, true, SPELL_BLOCK_TYPE_POSITIVE);
        minion->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_ATTACK_POWER_PCT, true, SPELL_BLOCK_TYPE_POSITIVE);
    }

    void CalcPeriodic(AuraEffect const* /*aurEff*/, bool& isPeriodic, int32& amplitude)
    {
        // Stock ticked pets only; every minion ticks here so Stamina and Army health follow the owner live (no
        // snapshot)
        isPeriodic = true;
        amplitude = 2 * IN_MILLISECONDS;
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();

        Unit* minion = GetUnitOwner();
        // Stamina and the Army ghouls' health effect both move max health: keep the current health (the core's health
        // handler would otherwise refill the minion when the amount changes)
        bool const changesMaxHealth = aurEff->GetAuraType() == SPELL_AURA_MOD_INCREASE_HEALTH ||
            (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT && aurEff->GetMiscValue() == STAT_STAMINA);
        if (changesMaxHealth)
        {
            int32 const currentAmount = aurEff->GetAmount();
            int32 const newAmount = GetEffect(aurEff->GetEffIndex())->CalculateAmount(GetCaster());
            if (newAmount != currentAmount)
            {
                uint32 const health = minion->GetHealth();
                GetEffect(aurEff->GetEffIndex())->ChangeAmount(newAmount, false);
                minion->SetHealth(std::min<uint32>(minion->GetMaxHealth(), health));
            }
        }
        else
            GetEffect(aurEff->GetEffIndex())->RecalculateAmount();
    }

    void Register() override
    {
        switch (m_scriptSpellId)
        {
            case SPELL_DK_PET_SCALING_01:
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateStatAmount,
                    EFFECT_ALL,
                    SPELL_AURA_MOD_STAT);
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateZero, EFFECT_ALL,
                    SPELL_AURA_MOD_DAMAGE_DONE);
                break;
            case SPELL_DK_PET_SCALING_02:
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateZero, EFFECT_ALL,
                    SPELL_AURA_MELEE_SLOW);
                break;
            case SPELL_DK_ARMY_PASSIVE:
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateZero, EFFECT_ALL,
                    SPELL_AURA_MOD_ATTACK_POWER);
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateHealthAmount,
                    EFFECT_ALL, SPELL_AURA_MOD_INCREASE_HEALTH);
                DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_minion_passthrough::CalculateZero, EFFECT_ALL,
                    SPELL_AURA_MOD_DAMAGE_DONE);
                break;
            default:
                break;
        }

        OnEffectApply += AuraEffectApplyFn(spell_dk_minion_passthrough::HandleEffectApply, EFFECT_ALL, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(spell_dk_minion_passthrough::CalcPeriodic, EFFECT_ALL,
            SPELL_AURA_ANY);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dk_minion_passthrough::HandlePeriodic, EFFECT_ALL,
            SPELL_AURA_ANY);
    }
};

void AddSC_deathknight_shared_spell_scripts()
{
    RegisterSpellScript(spell_dk_death_strike_rework);
    RegisterSpellScript(spell_dk_ams_damage_record);
    RegisterSpellScript(spell_dk_deaths_caress);
    RegisterSpellScript(spell_dk_pestilence_rework);
    RegisterSpellScript(spell_dk_anti_magic_zone_rework);
    RegisterSpellScript(spell_dk_rune_rework);
    RegisterSpellScript(spell_dk_rune_of_razorice_rework);
    RegisterSpellScript(spell_dk_rune_of_the_apocalypse);
    RegisterSpellScript(spell_dk_rune_haste_sync);
    RegisterSpellScript(spell_dk_minion_mirror);
    RegisterSpellScript(spell_dk_minion_passthrough);
}
