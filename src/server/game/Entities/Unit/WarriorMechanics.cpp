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

    // ---- W0a rage model (docs/reworks/warrior-shared-rework.md "Rage generation", W0a D11-D14) ----
    //
    // Worked example (level 60, 3.6 s two-hander, non-crit white hit 450, Battle Stance, k 0.43, m 1.8):
    //   c(60) = 230.60; damage term 7.5 * 450 / 230.60 = 14.64 -> * k = 6.29
    //   speed part 3.6 * 3.5 * 1.8 = 22.68 (factor 2268 in hundredths)
    //   (6.29 + 22.68) / 2 = 14.49; stock cap 15 * 450 / 230.60 = 29.27 not hit; * 1.10 (aura 213) = 15.94 rage
    //   (stock: (14.64 + 12) / 2 = 13.32). Crit 900, factor doubled: (12.59 + 45.36) / 2 * 1.10 = 31.87.
    //   30% haste (swing 2.77 s): speed 17.45 -> (6.29 + 17.45) / 2 * 1.10 = 13.06 per swing (per second unchanged
    //   apart from the damage term). Off hand 2.6 s, hit 200: (0.43 * 6.51 + 2.275) / 2 = 2.54.

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

        // The hasted swing (the raw field, not GetAttackTime, which divides haste back out), so more haste means
        // smaller rage per swing and rage per second stays neutral.
        float const hastedSwingMs = attacker->GetFloatValue(static_cast<uint16>(UNIT_FIELD_BASEATTACKTIME) + attType);
        float const handFactor = attType == BASE_ATTACK
            ? WarriorData::RAGE_MH_SPEED_FACTOR * GetRageConstants(attacker->GetLevel()).m
            : WarriorData::RAGE_OH_SPEED_FACTOR;

        // In hundredths (RAGE_SPEED_FIXED_POINT) so m's decimals survive the uint32 the callers carry.
        return uint32(std::lround(hastedSwingMs / 1000.0f * handFactor * WarriorData::RAGE_SPEED_FIXED_POINT));
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
}
