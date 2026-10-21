/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_SIMHEALBOSSAI_H
#define MODULE_DPSSIM_SIMHEALBOSSAI_H

#include "Define.h"
#include "ObjectGuid.h"
#include <vector>

class Creature;
class Player;

// Registers npc_healsim_boss (SimHealBossAI.cpp) - the AI of the healing sim's "Sim Raid Boss" (creature entries
// 900015-900017, declared in apps/dbc-tools/source/npcs/training_dummies.py). Called once from Addmod_dpssimScripts()
// (dpssim_loader.cpp), same as every other script this module registers.
//
// The boss never swings, never moves, never evades and never dies. Its damage to the group comes only from the sim's
// damage drivers (the Sim Damage Pulse 202900 and Sim Pin Hit 202901 casts, SimHealScenario.cpp); the AI itself only
// keeps its victim on the group's main tank (below).
void AddSC_SimHealBossAI();

namespace SimHealBoss
{
    // Sim Raid Boss entries, one per level bracket like the training dummies (SimTarget::EntryForLevel)
    constexpr uint32 ENTRY_LEVEL_60 = 900015;
    constexpr uint32 ENTRY_LEVEL_70 = 900016;
    constexpr uint32 ENTRY_LEVEL_80 = 900017;

    // The entry for `level`; anything but 60/70/80 falls back to the bracket at or below it (60 below 60), like the
    // dummies
    uint32 EntryForLevel(uint8 level);

    // The player the boss keeps as its victim while it is in combat: Unit::Attack(tank, false), so it never swings. The
    // Holy Paladin values read attacker->GetVictim() to find the tank. The AI re-applies it whenever the victim is lost
    // or changed. Empty = no victim pin.
    void SetMainTank(ObjectGuid tank);

    // The pull: the boss engages every living member (Unit::EngageWithTarget(), a zero-threat entry on its list plus
    // combat; a hit from the NO_THREAT damage spells never starts combat on its own), then takes the main tank as its
    // victim. Returns how many members are still not in combat with the boss afterwards.
    uint32 Engage(Creature* boss, std::vector<Player*> const& members);
}

#endif
