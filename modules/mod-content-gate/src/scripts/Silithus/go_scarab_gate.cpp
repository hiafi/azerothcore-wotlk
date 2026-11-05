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

// Ported from mod-progression by Revision <tkn963@gmail.com> (GPL-2):
// src/phase_00/scripts/Kalimdor/Silithus/go_scarab_gate.cpp at 8c765a1.

#include "AreaDefines.h"
#include "ContentGate.h"
#include "GameObjectAI.h"
#include "GameObjectScript.h"
#include "WorldState.h"

enum
{
    WORLD_STATE_AQ_GATE_OPENED = 50000
};

class go_scarab_gate : public GameObjectScript
{
public:
    go_scarab_gate() : GameObjectScript("go_scarab_gate") {}

    struct go_scarab_gateAI : GameObjectAI
    {
        explicit go_scarab_gateAI(GameObject* object) : GameObjectAI(object) {}

        void Reset() override
        {
            // Was "phase >= 5" in mod-progression: the gate stays shut until the AQ tier is open in the gate conf.
            bool const aqOpen = sContentGate->IsInstanceOpen(MAP_RUINS_OF_AHN_QIRAJ, DUNGEON_DIFFICULTY_NORMAL) ||
                sContentGate->IsInstanceOpen(MAP_AHN_QIRAJ_TEMPLE, RAID_DIFFICULTY_10MAN_NORMAL);
            if (aqOpen && sWorldState->getWorldState(WORLD_STATE_AQ_GATE_OPENED))
            {
                me->ResetDoorOrButton();
                me->UseDoorOrButton();
            }
        }
    };

    GameObjectAI* GetAI(GameObject* object) const override
    {
        return new go_scarab_gateAI(object);
    }
};

void AddSC_go_scarab_gate()
{
    new go_scarab_gate();
}
