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

// Custom: Hit is no longer a meaningful player stat - players always land white melee/ranged
// auto-attacks against non-player targets (PvE only; PvP hit/miss is untouched). Expertise is
// handled the same way: melee auto-attacks against non-player targets can no longer be dodged or
// parried either (block is untouched - that's governed by the victim's block stat, not
// expertise). Spell hit/dodge/parry chance vs. NPCs is handled separately in
// Unit::MeleeSpellHitResult / Unit::MagicSpellHitResult (Unit.cpp), since no equivalent script
// hook exists on those paths.

#include "ScriptMgr.h"
#include "Unit.h"

class Custom_PvEAlwaysHit : public UnitScript
{
public:
    Custom_PvEAlwaysHit() : UnitScript("Custom_PvEAlwaysHit") { }

    void OnBeforeRollMeleeOutcomeAgainst(Unit const* attacker, Unit const* victim, WeaponAttackType /*attType*/,
        int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/,
        int32& /*attackerWeaponSkill*/, int32& /*victimDefenseSkill*/, int32& /*crit_chance*/,
        int32& miss_chance, int32& dodge_chance, int32& parry_chance, int32& /*block_chance*/) override
    {
        if (attacker->IsPlayer() && !victim->IsPlayer())
        {
            miss_chance = 0;
            dodge_chance = 0;
            parry_chance = 0;
        }
    }
};

void AddSC_custom_pve_always_hit()
{
    new Custom_PvEAlwaysHit();
}
