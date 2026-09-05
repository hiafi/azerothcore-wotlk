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

class Unit;

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
}

#endif
