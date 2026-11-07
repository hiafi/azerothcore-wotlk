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

// The Shadowfang Keep build's instance script (handoff section 3.3 item 2), registered under the stock name
// `instance_shadowfang_keep` (handoff section 7 #1): modules load after the core scripts, and a database-bound script
// registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 33's
// instance_template row is untouched and the stock InstanceMapScript is replaced at load. The stock spell scripts of
// that file (spell_shadowfang_keep_haunting_spirits_aura, ..._forsaken_skills_aura) stay registered.
//
// Apothecary Hummel's holiday event keeps working: his three scripts check the instance name
// (RegisterShadowfangKeepCreatureAI), Hummel is a BossAI on boss slot 4 (BOSS_APOTHECARY_HUMMEL), and the Hummel cases
// below (the Crazed Apothecary Generators, Hummel's guid, the Crazed Apothecaries forwarded to his AI, and
// DATA_SPAWN_VALENTINE_ADDS) are copied from AzerothCore's
// src/server/scripts/EasternKingdoms/ShadowfangKeep/instance_shadowfang_keep.cpp (at Playerbot 2c20fdb7b), which
// stays untouched. The stock courtyard field (TYPE_COURTYARD, set DONE by the prisoners' action lists) and the
// Courtyard Door's open-on-load are kept as well.
//
// What is new: 11 boss states (ShadowfangKeepRework.h; Hummel keeps slot 4), door data for the Sorcerer's Gate
// (Fenrus) and Arugal's Lair (Nandos), Rethilgore's cell doors and levers, the Deathsworn Captain's saved 15% roll,
// DATA_PRISONER and the lair prisoner summon, Arugal's hard mode flag and loot bit, and the "S R" save string.

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "ShadowfangKeepRework.h"
#include "TemporarySummon.h"

using namespace ShadowfangKeepRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");
static_assert(kMapShadowfangKeep == MAP_SHADOWFANG_KEEP, "map 33");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Each opens on its boss's DONE. The stock levers still toggle them (a lever-opened door closes again when its
    // boss's state changes). The Courtyard Door is the stock data field's (DATA_COURTYARD), the cell doors are
    // Rethilgore's (SetBossState below), so neither is door data.
    DoorData const doorData[] =
    {
        { GO_SORCERERS_GATE, BOSS_FENRUS, DOOR_TYPE_PASSAGE },
        { GO_ARUGALS_LAIR,   BOSS_NANDOS, DOOR_TYPE_PASSAGE },
        { 0,                 0,           DOOR_TYPE_ROOM    }
    };

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall).
    ObjectData const creatureData[] =
    {
        { NPC_RETHILGORE,         DATA_RETHILGORE_GUID         },
        { NPC_RAZORCLAW,          DATA_RAZORCLAW_GUID          },
        { NPC_SILVERLAINE,        DATA_SILVERLAINE_GUID        },
        { NPC_SPRINGVALE,         DATA_SPRINGVALE_GUID         },
        { NPC_ODO,                DATA_ODO_GUID                },
        { NPC_DEATHSWORN_CAPTAIN, DATA_DEATHSWORN_CAPTAIN_GUID },
        { NPC_FENRUS,             DATA_FENRUS_GUID             },
        { NPC_NANDOS,             DATA_NANDOS_GUID             },
        { NPC_ARUGAL,             DATA_ARUGAL_GUID             },
        { NPC_ADAMANT,            DATA_ADAMANT_GUID            },
        { NPC_ASHCROMBE,          DATA_ASHCROMBE_GUID          },
        { NPC_LANDEN_STILWELL,    DATA_LANDEN_GUID             },
        { 0,                      0                            }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_COURTYARD_DOOR, DATA_COURTYARD_DOOR_GUID },
        { GO_SORCERERS_GATE, DATA_SORCERERS_GATE_GUID },
        { GO_ARUGALS_LAIR,   DATA_ARUGALS_LAIR_GUID   },
        { GO_CELL_DOOR_S,    DATA_CELL_DOOR_S_GUID    },
        { GO_CELL_DOOR_M,    DATA_CELL_DOOR_M_GUID    },
        { GO_CELL_DOOR_N,    DATA_CELL_DOOR_N_GUID    },
        { GO_CELL_LEVER_S,   DATA_CELL_LEVER_S_GUID   },
        { GO_CELL_LEVER_M,   DATA_CELL_LEVER_M_GUID   },
        { GO_CELL_LEVER_N,   DATA_CELL_LEVER_N_GUID   },
        { GO_ARUGALS_FOCUS,  DATA_ARUGALS_FOCUS_GUID  },
        { 0,                 0                        }
    };

    std::array<uint32, kCellCount> constexpr kCellDoorData{ { DATA_CELL_DOOR_S_GUID, DATA_CELL_DOOR_M_GUID,
        DATA_CELL_DOOR_N_GUID } };
    std::array<uint32, kCellCount> constexpr kCellLeverData{ { DATA_CELL_LEVER_S_GUID, DATA_CELL_LEVER_M_GUID,
        DATA_CELL_LEVER_N_GUID } };

    Milliseconds constexpr kCaptainDespawnDelay = 500ms;    // stock SmartAI 3872: despawn 500 ms after AI init

    bool IsCellDoor(uint32 entry)
    {
        return entry == GO_CELL_DOOR_S || entry == GO_CELL_DOOR_M || entry == GO_CELL_DOOR_N;
    }

    bool IsCellLever(uint32 entry)
    {
        return entry == GO_CELL_LEVER_S || entry == GO_CELL_LEVER_M || entry == GO_CELL_LEVER_N;
    }
}

class instance_shadowfang_keep_rework : public InstanceMapScript
{
public:
    instance_shadowfang_keep_rework() : InstanceMapScript(kInstanceScriptName, MAP_SHADOWFANG_KEEP) { }

    struct instance_shadowfang_keep_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_shadowfang_keep_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadDoorData(doorData);
            LoadObjectData(creatureData, gameObjectData);
        }

        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                // Hummel's event: the stock instance_shadowfang_keep cases, copied (see the file comment).
                case NPC_DND_CRAZED_APOTHECARY_GENERATOR:
                    _crazedApothecaryGeneratorGUIDs.push_back(creature->GetGUID());
                    break;
                case NPC_APOTHECARY_HUMMEL:
                    _apothecaryHummel = creature->GetGUID();
                    break;
                case NPC_CRAZED_APOTHECARY:
                    if (Creature* hummel = instance->GetCreature(_apothecaryHummel))
                    {
                        hummel->AI()->JustSummoned(creature);
                    }
                    break;
                // The rework.
                case NPC_DEATHSWORN_CAPTAIN:
                    // Handoff section 3.3: rolled once per instance (15%) and saved, so a reset never rerolls him. His
                    // spawn row stays (mod-dungeon-clear's roster comes from spawns); on Absent he despawns as the
                    // stock SmartAI did.
                    if (GetBossState(BOSS_DEATHSWORN_CAPTAIN) != DONE
                        && DungeonKit::RollOnce(this, DATA_CAPTAIN_ROLL, kCaptainPresentChancePct)
                            == DungeonKit::Roll::Absent)
                        creature->DespawnOrUnsummon(kCaptainDespawnDelay);
                    break;
                case NPC_ARUGAL:
                    ApplyHardModeLoot(creature);
                    break;
                default:
                    break;
            }
        }

        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            uint32 const entry = go->GetEntry();
            if (entry == GO_COURTYARD_DOOR)
            {
                // Stock: open on load once the prisoners opened it.
                if (_courtyard == DONE)
                    HandleGameObject(ObjectGuid::Empty, true, go);
            }
            else if (IsCellDoor(entry))
            {
                if (GetBossState(BOSS_RETHILGORE) == DONE)
                    HandleGameObject(ObjectGuid::Empty, true, go);
            }
            else if (IsCellLever(entry))
                SetLeverLocked(go, GetBossState(BOSS_RETHILGORE) == IN_PROGRESS);
        }

        bool SetBossState(uint32 id, EncounterState state) override
        {
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_RETHILGORE:
                    // His cell doors (handoff section 3.3): the levers are locked while he fights (Lock-Up owns the
                    // doors then; S1 opens a door it closed on his evade or reset), and all three open on his death.
                    for (uint32 lever : kCellLeverData)
                        SetLeverLocked(GetGameObject(lever), state == IN_PROGRESS);
                    if (state == DONE)
                        for (uint32 door : kCellDoorData)
                            if (GameObject* go = GetGameObject(door))
                                HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case BOSS_NANDOS:
                    // The lair prisoner waits at the lair door once Nandos is dead (handoff section 3.3; a load with
                    // him DONE summons it again, Update checks Arugal).
                    if (state == DONE)
                        _lairPrisonerPending = true;
                    break;
                case BOSS_ARUGAL:
                    if (state == DONE && _hardMode)
                    {
                        // The hard mode kill flag (loot reads BOSS_FACE_HIM_ALONE DONE / DATA_HARD_MODE_KILLED). His
                        // loot is already filled (Unit::Kill, before JustDied), hard mode item included. A first-time
                        // state on a TO_BE_DECIDED slot is stored but not saved (InstanceScript treats it as loading),
                        // so save explicitly or a reload loses the kill flag.
                        SetBossState(BOSS_FACE_HIM_ALONE, DONE);
                        SaveToDB();
                    }
                    ApplyHardModeLoot();
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
                case DATA_COURTYARD:
                    _courtyard = data == DONE ? uint32(DONE) : uint32(NOT_STARTED);
                    if (_courtyard == DONE)
                    {
                        if (GameObject* door = GetGameObject(DATA_COURTYARD_DOOR_GUID))
                            HandleGameObject(ObjectGuid::Empty, true, door);
                        SaveToDB();
                    }
                    break;
                case DATA_LEGACY_FENRUS:
                case DATA_LEGACY_NANDOS:
                    // Stock SmartAI ids (Fenrus 4274 and Nandos 3927 set them on death); the boss states own the
                    // doors now, so a stray write is ignored.
                    LOG_DEBUG(kLog, "sfk instance: ignored legacy SetData({}, {})", type, data);
                    break;
                case DATA_SPAWN_VALENTINE_ADDS:
                    // Hummel's event: the stock case, copied (see the file comment).
                    for (ObjectGuid guid : _crazedApothecaryGeneratorGUIDs)
                    {
                        if (Creature* generator = instance->GetCreature(guid))
                        {
                            generator->CastSpell(nullptr, SPELL_SUMMON_VALENTINE_ADD);
                        }
                    }
                    break;
                case DATA_PRISONER:
                    if (data <= Prisoner::Adamant)
                    {
                        _prisoner = data;
                        SaveToDB();
                    }
                    break;
                case DATA_HARD_MODE:
                    // Face Him Alone (S10): chosen once, before Arugal dies; an instance reset clears it.
                    if (GetBossState(BOSS_ARUGAL) == DONE)
                        break;
                    _hardMode = data ? 1 : 0;
                    ApplyHardModeLoot();
                    SaveToDB();
                    break;
                case DATA_CAPTAIN_ROLL:     // RollOnce, and `.sfktest instance captain` forcing the saved roll
                    if (data == DungeonKit::Roll::Present || data == DungeonKit::Roll::Absent)
                    {
                        _captainRoll = data;
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
                case DATA_COURTYARD:
                    return _courtyard;
                case DATA_LEGACY_FENRUS:
                    return GetBossState(BOSS_FENRUS) == DONE ? uint32(DONE) : uint32(NOT_STARTED);
                case DATA_LEGACY_NANDOS:
                    return GetBossState(BOSS_NANDOS) == DONE ? uint32(DONE) : uint32(NOT_STARTED);
                case DATA_PRISONER:
                    return _prisoner;
                case DATA_HARD_MODE:
                    return _hardMode;
                case DATA_CAPTAIN_ROLL:
                    return _captainRoll;
                case DATA_HARD_MODE_KILLED:
                    return GetBossState(BOSS_FACE_HIM_ALONE) == DONE ? 1 : 0;
                default:
                    return 0;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            if (type == DATA_LAIR_PRISONER_GUID)
                return _lairPrisoner;
            return InstanceScript::GetGuidData(type);
        }

        void Update(uint32 diff) override
        {
            InstanceScript::Update(diff);

            if (!_lairPrisonerPending)
                return;
            if (GetBossState(BOSS_ARUGAL) == DONE || GetBossState(BOSS_NANDOS) != DONE)
            {
                _lairPrisonerPending = false;
                return;
            }
            // Summoned beside the lair door once its grid is loaded (the door is created with it).
            if (GameObject* door = GetGameObject(DATA_ARUGALS_LAIR_GUID); door && door->IsInWorld())
                SummonLairPrisoner(door);
        }

        std::string GetSaveData() override
        {
            SfkSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                EncounterState const state = GetBossState(i);
                save.states[i] = state == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(state);
            }
            save.courtyard = _courtyard;
            save.prisoner = _prisoner;
            save.hardMode = _hardMode;
            save.captainRoll = _captainRoll;
            return FormatSfkSave(save);
        }

        // Reads this script's "S R" string; a stock "S K" save is ignored (handoff section 7 #2).
        void Load(char const* in) override
        {
            if (!in)
                return;

            SfkSave save;
            if (!ParseSfkSave(in, save))
            {
                LOG_DEBUG(kLog, "sfk instance: ignored save '{}'", in);
                return;
            }

            _courtyard = save.courtyard;
            _prisoner = save.prisoner;
            _captainRoll = save.captainRoll;
            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.states[i]));
            // After the states: the flag never re-fires BOSS_ARUGAL's DONE branch while loading.
            _hardMode = save.hardMode;
        }

    private:
        // Rethilgore's levers: not usable while he fights.
        static void SetLeverLocked(GameObject* lever, bool locked)
        {
            if (!lever)
                return;
            if (locked)
                lever->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            else
                lever->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        }

        // The prisoner who opened the Courtyard Door (DATA_PRISONER, set by S9's edited action lists); unknown, the
        // one of the players' side (Ashcrombe for the Alliance, Adamant for the Horde).
        uint32 LairPrisoner() const
        {
            if (_prisoner != Prisoner::None)
                return _prisoner;
            for (auto const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                    return player->GetTeamId() == TEAM_ALLIANCE ? Prisoner::Ashcrombe : Prisoner::Adamant;
            return Prisoner::Ashcrombe;
        }

        void SummonLairPrisoner(GameObject* door)
        {
            _lairPrisonerPending = false;
            if (Creature* old = instance->GetCreature(_lairPrisoner); old && old->IsAlive())
                return;

            uint32 const prisoner = LairPrisoner();
            uint32 const entry = LairPrisonerEntry(prisoner);
            Position const at(kLairPrisonerWait.x, kLairPrisonerWait.y, kLairPrisonerWait.z, kLairPrisonerWaitFacing);
            if (TempSummon* summon = door->SummonCreature(entry, at, TEMPSUMMON_MANUAL_DESPAWN))
            {
                _lairPrisoner = summon->GetGUID();
                LOG_INFO(kLog, "sfk instance lair-prisoner summoned entry={} prisoner={} (data {})", entry, prisoner,
                    _prisoner);
            }
            else
                LOG_ERROR(kLog, "sfk instance lair-prisoner: summoning entry {} failed", entry);
        }

        // Item variants IV7 (the Deadmines pattern): Arugal's heroic lootid holds the hard mode list in group 2 with
        // LootMode 2 (LOOT_MODE_HARD_MODE_1). Unit::Kill fills the loot with the creature's loot mode before JustDied,
        // so the bit rides his loot mode exactly while DATA_HARD_MODE is lit and he is not dead yet.
        void ApplyHardModeLoot(Creature* arugal = nullptr)
        {
            if (!arugal)
                arugal = GetCreature(DATA_ARUGAL_GUID);
            if (!arugal)
                return;
            DungeonKit::SetHardModeLoot(arugal, _hardMode != 0 && GetBossState(BOSS_ARUGAL) != DONE);
        }

        // Hummel's event (stock).
        GuidVector _crazedApothecaryGeneratorGUIDs;
        ObjectGuid _apothecaryHummel;

        uint32 _courtyard = NOT_STARTED;
        uint32 _prisoner = Prisoner::None;
        uint32 _hardMode = 0;
        uint32 _captainRoll = DungeonKit::Roll::Unrolled;
        bool _lairPrisonerPending = false;
        ObjectGuid _lairPrisoner;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_shadowfang_keep_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_shadowfang_keep_rework()
{
    new instance_shadowfang_keep_rework();
}
