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

#ifndef MODULE_DPSSIM_SIMDUMMYAI_H
#define MODULE_DPSSIM_SIMDUMMYAI_H

// Registers npc_dpssim_training_dummy (SimDummyAI.cpp) - called once from Addmod_dpssimScripts()
// (dpssim_loader.cpp), same as every other script this module registers.
void AddSC_SimDummyAI();

namespace SimDummyAI
{
    // Off by default: the dummy zeroes all damage it takes, so its health never moves. On: it takes real damage but
    // never drops below 1 health, so health-threshold effects ("target below 20%") can fire without the dummy
    // dying. Set from SimTarget::Create() (profile keys DummyHealthDrain / DummyMaxHealth); the sim is
    // single-threaded (see EventRecorder.h), so a plain flag is enough.
    void SetHealthDrain(bool enabled);
    [[nodiscard]] bool IsHealthDrainEnabled();
}

#endif
