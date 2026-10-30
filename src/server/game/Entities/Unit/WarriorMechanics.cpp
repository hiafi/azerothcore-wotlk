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

#include "WarriorMechanics.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "Unit.h"
#include "Util.h"
#include "World.h"
#include <algorithm>
#include <cmath>

namespace Warrior
{
    namespace
    {
        // Bare icon literal, not an enum shared with spell_warrior.cpp - this core file has no
        // access to that scripts/ file's WarriorSpellIcons enum. Keep in sync with
        // WARRIOR_ICON_ID_CRITICAL_BLOCK (spell_warrior.cpp) if it ever changes.
        constexpr uint32 ICON_CRITICAL_BLOCK = 2778;
    }

    void ApplyBlockDamageReduction(Unit* defender, uint32& damage)
    {
        if (Player const* player = defender->ToPlayer())
            if (AuraEffect const* aurEff = player->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, ICON_CRITICAL_BLOCK, EFFECT_1))
                AddPct(damage, -int32(aurEff->GetAmount()));
    }

    // ---- W0a rage model (docs/reworks/warrior-shared-rework.md "Rage generation", W0a D11-D14), W0b spell haste ----
    //
    // Worked example (level 60, 3.6 s two-hander, non-crit white hit 450, Battle Stance aura 213 +10%, k 0.43, m 1.35):
    //   c(60) = 230.60; damage term 7.5 * 450 / 230.60 = 14.64 -> * k = 6.29
    //   speed part 3.6 * 3.5 * 1.35 = 17.01 (factor 1701 in hundredths)
    //   (6.29 + 17.01) / 2 = 11.65; stock cap 15 * 450 / 230.60 = 29.27 not hit; * 1.10 = 12.82 rage
    //   (stock, before Battle Stance: (14.64 + 12) / 2 = 13.32). Crit 900, factor doubled: (12.59 + 34.02) / 2 * 1.10
    //   = 25.63.
    //   Bloodlust (30% melee and spell haste): swing 2.77 s, cast speed 1 / 1.30, so the speed part reads
    //   2.77 * 1.30 = 3.6 s of swing again: 12.82 per swing, rage per second x1.30. An attack-speed-only 30% (Slice and
    //   Dice style, cast speed untouched): speed part 13.09 -> 10.66 per swing, rage per second x1.08. A casting slow
    //   (cast speed > 1) changes nothing. Off hand 2.6 s, hit 200, no aura: (0.43 * 6.51 + 2.275) / 2 = 2.54.

    float RageConversion(uint8 level)
    {
        // Mirrors the stock constants in Unit::RewardRage (wowwiki rage formulae), including its linear adjustment
        // above level 70. Keep the two in sync.
        float conversion = ((0.0091107836f * level * level) + 3.225598133f * level) + 4.2652911f;
        if (level > 70)
            conversion += 13.27f * (level - 70);

        return conversion;
    }

    RageConstants GetRageConstants(uint8 /*level*/)
    {
        // D13: one table keyed on level; only the level-60 bracket is set, so it applies at every level until the
        // 70/80 brackets open.
        return { WarriorData::RAGE_K_60, WarriorData::RAGE_M_60 };
    }

    uint32 RageSpeedFactor(Unit const* attacker, WeaponAttackType attType)
    {
        // D11: creatures and pets keep the stock factor (whole rage points, unhasted swing).
        if (!attacker->IsPlayer())
            return attacker->GetRageWeaponSpeedHitFactor(attType);

        // The hasted swing (the raw field, not GetAttackTime, which divides haste back out): attack speed alone
        // shortens the swing and its rage, so it only adds the damage term's share per second.
        float const hastedSwingMs = attacker->GetFloatValue(static_cast<uint16>(UNIT_FIELD_BASEATTACKTIME) + attType);

        // W0b D21: spell haste is the haste for haste-scaled resources (the rogue energy rule, GetEnergyHastePct).
        // UNIT_MOD_CAST_SPEED holds haste rating, casting-speed and combat-speed auras, never melee-only attack speed;
        // lower = faster. Scaling the swing by 1 / castSpeed gives back what spell haste took from the swing, so
        // rage per swing holds and rage per second rises with it. A net slow (castSpeed > 1) never lowers rage; no cap.
        float const castSpeed = attacker->GetFloatValue(UNIT_MOD_CAST_SPEED);
        float const spellHasteFactor = castSpeed > 0.0f ? std::max(1.0f, 1.0f / castSpeed) : 1.0f;

        float const handFactor = attType == BASE_ATTACK
            ? WarriorData::RAGE_MH_SPEED_FACTOR * GetRageConstants(attacker->GetLevel()).m
            : WarriorData::RAGE_OH_SPEED_FACTOR;

        // In hundredths (RAGE_SPEED_FIXED_POINT) so m's decimals survive the uint32 the callers carry.
        return uint32(std::lround(hastedSwingMs * spellHasteFactor / 1000.0f * handFactor
            * WarriorData::RAGE_SPEED_FIXED_POINT));
    }

    bool RewardRage(Unit* unit, uint32 damage, uint32 weaponSpeedHitFactor, bool attacker)
    {
        // Rage taken (Berserker Rage x3 included) and every non-player keep the stock body.
        if (!unit->IsPlayer() || !attacker)
            return false;

        // D12: an attacker call with factor 0 is the fully-absorbed duplicate (Unit::DealDamage); it grants nothing.
        if (!weaponSpeedHitFactor)
            return true;

        RageConstants const constants = GetRageConstants(unit->GetLevel());
        float const conversion = RageConversion(unit->GetLevel());

        float const stockDamageTerm = damage / conversion * 7.5f;
        float const speedPart = weaponSpeedHitFactor / float(WarriorData::RAGE_SPEED_FIXED_POINT);

        float addRage = (constants.k * stockDamageTerm + speedPart) / 2.0f;
        // The stock cap (2 * 7.5 * d / c), on the undampened damage term, so it does not clip normal swings.
        addRage = std::min(addRage, stockDamageTerm * 2.0f);
        AddPct(addRage, unit->GetTotalAuraModifier(SPELL_AURA_MOD_RAGE_FROM_DAMAGE_DEALT));
        addRage *= sWorld->getRate(RATE_POWER_RAGE_INCOME);

        unit->ModifyPower(POWER_RAGE, uint32(addRage * 10));
        return true;
    }

    // ---- W0b: Charge in combat (D4) ----
    int32 ChargeCombatRage(float distanceYd)
    {
        constexpr float span = WarriorData::CHARGE_COMBAT_MAX_YD - WarriorData::CHARGE_COMBAT_MIN_YD;
        static_assert(span > 0.0f, "CHARGE_COMBAT_MAX_YD must exceed CHARGE_COMBAT_MIN_YD");

        float const t = std::clamp((distanceYd - WarriorData::CHARGE_COMBAT_MIN_YD) / span, 0.0f, 1.0f);
        // 5 to 10 rage, in power units (tenths of a rage point).
        return int32(std::lround(10.0f * (5.0f + 5.0f * t)));
    }
}
