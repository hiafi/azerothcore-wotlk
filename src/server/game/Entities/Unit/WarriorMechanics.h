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

#ifndef __WARRIORMECHANICS_H
#define __WARRIORMECHANICS_H

#include "Define.h"
#include "Generated/WarriorData.h"

class Unit;
enum WeaponAttackType : uint8;

/*
 * Warrior-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors MageMechanics.h's own
 * shape and rationale (see that file). Lives in game/Entities/Unit/ (core), not scripts/, because
 * Unit.cpp (core) can't depend on scripts/.
 */
namespace Warrior
{
    // Unit::CalculateMeleeDamage's MELEE_HIT_BLOCK case - Critical Block's guaranteed extra
    // damage-taken reduction on a successful block (Protection Warrior rework,
    // docs/prot_warrior_rework.md Row 7): "successful blocks now further reduce the damage you
    // take from the blocked hit by 8/16/25%." A flat guaranteed reduction, distinct from the
    // stock chance-based MOD_BLOCK_CRIT_CHANCE "double block" mechanic - no SpellScript hook
    // exists for "the block-value subtraction just happened", hence this core-side check.
    void ApplyBlockDamageReduction(Unit* defender, uint32& damage);

    // ---- W0a: the dampened, haste-neutral rage model (docs/reworks/warrior-shared-rework.md "Rage generation") ----
    // Every player rage user (warriors, Bear and Dire Bear Form); creatures and pets keep the stock formula. No hook
    // sees rage, so Unit.cpp calls these at three places (// Custom: warrior-rework W0a).

    // The weapon-speed factor Unit::RewardRage's dealt formula takes, for a white swing by `attacker`. Non-players:
    // the stock Unit::GetRageWeaponSpeedHitFactor value. Players: the hasted swing time (not GetAttackTime, so haste
    // is rage-neutral per second) * RAGE_MH_SPEED_FACTOR * m (main hand) or RAGE_OH_SPEED_FACTOR (off hand), in
    // hundredths (RAGE_SPEED_FIXED_POINT) so m's decimals survive. The caller's crit doubling stays linear.
    uint32 RageSpeedFactor(Unit const* attacker, WeaponAttackType attType);

    // First line of Unit::RewardRage. Returns false (the stock body runs) unless `unit` is a player and `attacker`
    // is true (rage taken stays stock, Berserker Rage x3 included). Factor 0 from an attacker call grants nothing
    // (the fully-absorbed duplicate). Otherwise: r = (k * 7.5 * d / c + speed / RAGE_SPEED_FIXED_POINT) / 2, capped at
    // the stock 15 * d / c, then aura 213 (Battle Stance +10%), then RATE_POWER_RAGE_INCOME, ModifyPower(r * 10).
    bool RewardRage(Unit* unit, uint32 damage, uint32 weaponSpeedHitFactor, bool attacker);

    // The stock rage conversion c(level) (same constants as Unit::RewardRage).
    float RageConversion(uint8 level);

    struct RageConstants
    {
        float k;
        float m;
    };

    // D13: one table keyed on level; the level-60 bracket applies at every level until 70/80 open.
    RageConstants GetRageConstants(uint8 level);
}

#endif
