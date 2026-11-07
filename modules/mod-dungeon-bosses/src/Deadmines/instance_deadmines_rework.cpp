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

// The Deadmines Pilot's instance script (handoff section 3.2 item 2), bound to map 36 by instance_template. The door
// handling (AllowSaveToDB, the Factory Door's loot state, the Iron Clad Door's despawn on load) and the "D E" save
// fields are mirrored from AzerothCore's src/server/scripts/EasternKingdoms/Deadmines/instance_deadmines.cpp (at
// Playerbot d28cf6df6), which stays untouched and inert once map 36 is rebound.

#include "Creature.h"
#include "CreatureAI.h"
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "GameObject.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Random.h"
#include "UnitDefines.h"

using namespace DeadminesRework;

static_assert(DeadminesKit::State::NotStarted == NOT_STARTED && DeadminesKit::State::InProgress == IN_PROGRESS
    && DeadminesKit::State::Fail == FAIL && DeadminesKit::State::Done == DONE
    && DeadminesKit::State::Special == SPECIAL && DeadminesKit::State::ToBeDecided == TO_BE_DECIDED,
    "DeadminesKitMath.h mirrors InstanceScript.h's EncounterState");

namespace
{
    // Each opens on its boss's DONE; the stock levers still toggle them (a lever-opened door closes again when its
    // boss's state changes, e.g. on the pull).
    DoorData const doorData[] =
    {
        { GO_FACTORY_DOOR,   BOSS_RHAHKZOR, DOOR_TYPE_PASSAGE },
        { GO_FOUNDRY_DOOR,   BOSS_GILNID,   DOOR_TYPE_PASSAGE },
        { GO_MAST_ROOM_DOOR, BOSS_SNEED,    DOOR_TYPE_PASSAGE },
        { 0,                 0,             DOOR_TYPE_ROOM    }
    };

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall). Sneed is left out: the Shredder re-summons him on
    // every eject, so boss_sneeds_shredder_rework tracks him itself.
    ObjectData const creatureData[] =
    {
        { NPC_RHAHKZOR,          DATA_RHAHKZOR_GUID        },
        { NPC_MINER_JOHNSON,     DATA_MINER_JOHNSON_GUID   },
        { NPC_SNEEDS_SHREDDER,   DATA_SNEEDS_SHREDDER_GUID },
        { NPC_GILNID,            DATA_GILNID_GUID          },
        { NPC_MR_SMITE,          DATA_MR_SMITE_GUID        },
        { NPC_COOKIE,            DATA_COOKIE_GUID          },
        { NPC_CAPTAIN_GREENSKIN, DATA_GREENSKIN_GUID       },
        { NPC_EDWIN_VANCLEEF,    DATA_VANCLEEF_GUID        },
        { 0,                     0                         }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_DM_POWDER_KEG, DATA_POWDER_KEG_GUID },
        { 0,                0                    }
    };

    Milliseconds constexpr kJohnsonDespawnDelay = 500ms;  // stock SmartAI 3586: despawn 500 ms after AI init
}

class instance_deadmines_rework : public InstanceMapScript
{
public:
    instance_deadmines_rework() : InstanceMapScript(kInstanceScriptName, MAP_DEADMINES) { }

    struct instance_deadmines_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_deadmines_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders("DE");
            SetBossNumber(kBossCount);
            LoadDoorData(doorData);
            LoadObjectData(creatureData, gameObjectData);
        }

        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_MINER_JOHNSON:
                    // Handoff section 7 #15: rolled once per instance and saved, so a reset never rerolls him.
                    // boss_miner_johnson_rework checks the same roll when he respawns.
                    if (GetBossState(BOSS_MINER_JOHNSON) != DONE && RollJohnson() == DeadminesKit::JohnsonRoll::Absent)
                        creature->DespawnOrUnsummon(kJohnsonDespawnDelay);
                    break;
                case NPC_EDWIN_VANCLEEF:
                    // Ruling 26: his spawn row stays (mod-dungeon-clear's roster comes from spawns); he is hidden
                    // until Greenskin is DONE. With Greenskin stored DONE he simply appears.
                    if (GetBossState(BOSS_CAPTAIN_GREENSKIN) != DONE && GetBossState(BOSS_EDWIN_VANCLEEF) != DONE)
                        SetVanCleefHidden(creature, true);
                    break;
                default:
                    break;
            }
        }

        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            switch (go->GetEntry())
            {
                case GO_HEAVY_DOOR_1:
                case GO_HEAVY_DOOR_2:
                case GO_DOOR_LEVER_FACTORY:
                case GO_DOOR_LEVER_MAST_ROOM:
                case GO_DOOR_LEVER_IRON_CLAD:
                case GO_DOOR_LEVER_FOUNDRY:
                case GO_DEFIAS_CANNON:
                    go->AllowSaveToDB(true);
                    break;
                case GO_FACTORY_DOOR:
                case GO_FOUNDRY_DOOR:
                case GO_MAST_ROOM_DOOR:
                    go->AllowSaveToDB(true);
                    // Stock (Factory Door): the open state is restored at creation, but the loot state must be set
                    // too or the lever closes the door again. Applied to all three boss doors.
                    if (GetBossState(DoorBoss(go->GetEntry())) == DONE)
                        go->SetLootState(GO_ACTIVATED);
                    break;
                case GO_IRON_CLAD_DOOR:
                    // Stock: blown by the cannon; a door stored open is gone on load.
                    go->AllowSaveToDB(true);
                    if (GetStoredGameObjectState(go->GetSpawnId()) == GO_STATE_ACTIVE)
                        go->DespawnOrUnsummon();
                    break;
                default:
                    break;
            }
        }

        bool SetBossState(uint32 id, EncounterState state) override
        {
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_CAPTAIN_GREENSKIN:
                    if (state == DONE)
                        RevealVanCleef();
                    break;
                case BOSS_EDWIN_VANCLEEF:
                    if (_hardMode && state == DONE)
                    {
                        // The hard mode kill flag (E5 loot reads BOSS_BURN_IT_DOWN DONE / DATA_HARD_MODE_KILLED).
                        _hardMode = 0;
                        SetBossState(BOSS_BURN_IT_DOWN, DONE);
                        // A first-time state on a TO_BE_DECIDED slot is stored but not saved (InstanceScript treats
                        // it as loading), so save explicitly or a reload loses the kill flag.
                        SaveToDB();
                    }
                    else if (_hardMode && (state == NOT_STARTED || state == FAIL))
                    {
                        _hardMode = 0;
                        SaveToDB();
                    }
                    break;
                default:
                    break;
            }
            return true;
        }

        void SetData(uint32 type, uint32 data) override
        {
            switch (type)
            {
                case DATA_CANNON:
                    _cannon = data;
                    if (data == DONE)
                        SaveToDB();
                    break;
                case DATA_HARD_MODE:
                    _hardMode = data ? 1 : 0;
                    SaveToDB();
                    break;
                case DATA_JOHNSON_ROLL: // `.dmtest johnson present`: force the saved roll
                    if (data == DeadminesKit::JohnsonRoll::Present || data == DeadminesKit::JohnsonRoll::Absent)
                    {
                        _johnsonRoll = data;
                        SaveToDB();
                    }
                    break;
                default:
                    break;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_CANNON:
                    return _cannon;
                case DATA_HARD_MODE:
                    return _hardMode;
                case DATA_JOHNSON_ROLL:
                    return _johnsonRoll;
                case DATA_HARD_MODE_KILLED:
                    return GetBossState(BOSS_BURN_IT_DOWN) == DONE ? 1 : 0;
                default:
                    return 0;
            }
        }

        std::string GetSaveData() override
        {
            DeadminesKit::Save save;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                EncounterState const state = GetBossState(i);
                save.bosses[i] = state == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(state);
            }
            save.cannon = _cannon;
            save.hardMode = _hardMode;
            save.johnsonRoll = _johnsonRoll;
            return DeadminesKit::FormatSave(save);
        }

        // Reads both the stock "D E <rhahkzor> <cannon>" string and this script's longer one (DeadminesKitMath.h).
        void Load(char const* in) override
        {
            if (!in)
                return;

            DeadminesKit::Save save;
            if (!DeadminesKit::ParseSave(in, save))
                return;

            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.bosses[i]));
            _cannon = save.cannon;
            _hardMode = save.hardMode;
            _johnsonRoll = save.johnsonRoll;
        }

    private:
        static uint32 DoorBoss(uint32 doorEntry)
        {
            switch (doorEntry)
            {
                case GO_FACTORY_DOOR:
                    return BOSS_RHAHKZOR;
                case GO_FOUNDRY_DOOR:
                    return BOSS_GILNID;
                default:
                    return BOSS_SNEED;
            }
        }

        uint32 RollJohnson()
        {
            if (_johnsonRoll == DeadminesKit::JohnsonRoll::Unrolled)
            {
                _johnsonRoll = DeadminesKit::ResolveJohnsonRoll(urand(0, 99));
                SaveToDB();
            }
            return _johnsonRoll;
        }

        static void SetVanCleefHidden(Creature* vanCleef, bool hidden)
        {
            vanCleef->SetVisible(!hidden);
            vanCleef->SetImmuneToAll(hidden);
            vanCleef->SetReactState(hidden ? REACT_PASSIVE : REACT_AGGRESSIVE);
            if (hidden)
                vanCleef->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            else
                vanCleef->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        }

        // On Greenskin's DONE: VanCleef appears and yells line 10 (a load with Greenskin stored DONE never hides
        // him, so the yell plays only on the kill).
        void RevealVanCleef()
        {
            Creature* vanCleef = GetCreature(DATA_VANCLEEF_GUID);
            if (!vanCleef || !vanCleef->IsAlive())
                return;
            SetVanCleefHidden(vanCleef, false);
            if (vanCleef->IsAIEnabled && vanCleef->AI())
                vanCleef->AI()->Talk(YELL_VANCLEEF_ARRIVAL);
        }

        uint32 _cannon = NOT_STARTED;
        uint32 _hardMode = 0;
        uint32 _johnsonRoll = DeadminesKit::JohnsonRoll::Unrolled;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_deadmines_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_deadmines_rework()
{
    new instance_deadmines_rework();
}
