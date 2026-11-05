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
// src/phase_00/scripts/Kalimdor/Silithus/go_scarab_gong.cpp at 8c765a1.

#include "GameObjectAI.h"
#include "GameObjectScript.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "WorldState.h"

enum
{
    QUEST_BANG_A_GONG           = 8743,

    GO_AHN_QIRAJ_GATE           = 176146,
    GO_AHN_QIRAJ_GATE_ROOTS     = 176147,
    GO_AHN_QIRAJ_GATE_RUNES     = 176148,

    SOUND_AHN_QIRAJ_GATE        = 7115,
    SOUND_AHN_QIRAJ_GATE_ROOTS  = 7114,
    SOUND_AHN_QIRAJ_GATE_RUNES  = 7116,

    STAGE_ACTIVATE_ROOTS        = 1,
    STAGE_ACTIVATE_RUNES        = 2,
    STAGE_ACTIVATE_GATE         = 3,
    STAGE_GATE_OPENED           = 4,

    WORLD_STATE_AQ_GATE_OPENED  = 50000
};

class go_scarab_gong : public GameObjectScript
{
public:
    go_scarab_gong() : GameObjectScript("go_scarab_gong") {}

    struct go_scarab_gongAI : GameObjectAI
    {
        explicit go_scarab_gongAI(GameObject* object) : GameObjectAI(object) {}

        void UpdateAI(uint32 diff) override
        {
            if (timer)
            {
                if (timer <= diff)
                {
                    switch (stage)
                    {
                    case STAGE_ACTIVATE_ROOTS:
                        goRoots->ResetDoorOrButton();
                        goRoots->UseDoorOrButton();
                        me->PlayDirectSound(SOUND_AHN_QIRAJ_GATE_ROOTS);
                        stage = STAGE_ACTIVATE_RUNES;
                        timer = 5000;
                        break;
                    case STAGE_ACTIVATE_RUNES:
                        goRunes->ResetDoorOrButton();
                        goRunes->UseDoorOrButton();
                        me->PlayDirectSound(SOUND_AHN_QIRAJ_GATE_RUNES);
                        stage = STAGE_ACTIVATE_GATE;
                        timer = 8000;
                        break;
                    case STAGE_ACTIVATE_GATE:
                        goGate->ResetDoorOrButton();
                        goGate->UseDoorOrButton();
                        me->PlayDirectSound(SOUND_AHN_QIRAJ_GATE);
                        stage = STAGE_GATE_OPENED;
                        timer = 18000;
                        break;
                    case STAGE_GATE_OPENED:
                        sWorldState->setWorldState(WORLD_STATE_AQ_GATE_OPENED, 1);
                        timer = 0;
                        break;
                    }
                }
                else
                    timer -= diff;
            }
        }

        void OpenGate()
        {
            goGate = GetClosestGameObjectWithEntry(me, GO_AHN_QIRAJ_GATE, 150.0f, true);
            goRoots = GetClosestGameObjectWithEntry(me, GO_AHN_QIRAJ_GATE_ROOTS, 150.0f, true);
            goRunes = GetClosestGameObjectWithEntry(me, GO_AHN_QIRAJ_GATE_RUNES, 150.0f, true);

            if (!goGate || !goRoots || !goRunes)
                return;

            if (goGate->GetGoState() == GO_STATE_ACTIVE || goRoots->GetGoState() == GO_STATE_ACTIVE ||
                goRunes->GetGoState() == GO_STATE_ACTIVE)
                return;

            timer = 1000;
            stage = STAGE_ACTIVATE_ROOTS;
        }

    private:
        uint32 timer = 0;
        GameObject* goGate = nullptr;
        GameObject* goRoots = nullptr;
        GameObject* goRunes = nullptr;
        uint8 stage = 0;
    };

    GameObjectAI* GetAI(GameObject* object) const override
    {
        return new go_scarab_gongAI(object);
    }

    bool OnQuestReward(Player* /*player*/, GameObject* go, Quest const* quest, uint32 /*opt*/) override
    {
        if (quest->GetQuestId() != QUEST_BANG_A_GONG)
            return false;

        if (sWorldState->getWorldState(WORLD_STATE_AQ_GATE_OPENED))
            return true;

        if (auto* gongAI = dynamic_cast<go_scarab_gongAI*>(go->AI()))
            gongAI->OpenGate();

        return true;
    }
};

void AddSC_go_scarab_gong()
{
    new go_scarab_gong();
}
