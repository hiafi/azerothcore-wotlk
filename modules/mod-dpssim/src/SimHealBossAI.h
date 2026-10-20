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

// Registers npc_healsim_boss (SimHealBossAI.cpp) - the AI of the healing sim's "Sim Raid Boss" (creature entries
// 900015-900017, declared in apps/dbc-tools/source/npcs/training_dummies.py). Called once from Addmod_dpssimScripts()
// (dpssim_loader.cpp), same as every other script this module registers.
//
// HS0 ships only the passive shell: it never swings, never moves, never evades and never dies. HS1 adds, in the same
// struct, the engagement of every group member, the main-tank victim pin and the drain / pin damage drivers (the Sim
// Damage Pulse 202900 and Sim Pin Hit 202901 casts) - see .agents/plans/healing-sim/healing-sim.PLAN.md section 1.
void AddSC_SimHealBossAI();

#endif
