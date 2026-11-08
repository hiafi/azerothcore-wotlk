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

// The Scholomance build's instance script (handoff section 3.2, WP-KS), registered under the stock name
// `instance_scholomance` (user ruling 2026-11-08 on section 7 #2): modules load after the core scripts, and a
// database-bound script registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts),
// so map 289's instance_template row is untouched and the stock InstanceMapScript is replaced at load. The other
// scripts of the stock file stay registered and keep working: spell_scholomance_fixate_aura,
// spell_scholomance_boon_of_life_aura (Ras's quest human form; it calls SetData(DATA_RAS_HUMAN)) and
// npc_scholomance_occultist, as do boss_kirtonos_the_herald and boss_kormok: their AIs check the instance name
// (GetScholomanceAI), which is unchanged, so none of them is copied.
//
// Kept from the stock instance (src/server/scripts/EasternKingdoms/Scholomance/instance_scholomance.cpp at Playerbot
// 590b1c00c, which stays untouched; the Kirtonos event by patou01, AzerothCore #8401 and #15131, on Yehonal's
// original):
// the DATA_KIRTONOS_THE_HERALD cases (the brazier's summon of Kirtonos at his spawn point, the gate, the brazier reset
// on FAIL; copied), DATA_RAS_HUMAN, DATA_DARKMASTER_GANDLING's entrance gate, the Viewing Room Door's saved state
// (AllowSaveToDB), and GetGuidData by the stock gameobject entries and Gandling's entry.
//
// What is new: 11 boss states (ScholomanceRework.h; Gandling keeps the stock slot 3); door data for the six classroom
// gates (each closes while its instructor fights, user ruling 2026-11-08, and all six plus the entrance while Gandling
// fights, handoff section 3.8); Gandling's reveal by the six instructor states (section 7 #11; the stock raw counter
// DATA_MINI_BOSSES is read-only now); the detention rooms (who is detained where, S11's gate control); the Passing
// Grades (ruling 22); Ras's keepsake pages, the bound book and both hard mode flags and kill flags with their loot bit;
// and the "S C" save string, which still reads the stock "<kirtonos> <miniBosses>".

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "StringFormat.h"
#include "TemporarySummon.h"

using namespace ScholomanceRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Each classroom gate closes while its instructor fights (user ruling 2026-11-08: keep the fight in the room; the
    // arena leash stays the backstop) and while Gandling fights (the three lower gates lie inside his arena, and a
    // detained student must stay in the room, handoff sections 3.7, 3.8). The entrance closes while Gandling fights
    // (stock). DOOR_TYPE_ROOM: open unless one of its bosses is IN_PROGRESS.
    DoorData const doorData[] =
    {
        { GO_GATE_GANDLING_DOWN_NORTH, BOSS_ILLUCIA,   DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_DOWN_EAST,  BOSS_ALEXEI,    DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_DOWN_SOUTH, BOSS_RAVENIAN,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_NORTH,   BOSS_POLKELT,   DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_EAST,    BOSS_KRASTINOV, DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_SOUTH,   BOSS_MALICIA,   DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_DOWN_NORTH, BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_DOWN_EAST,  BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_DOWN_SOUTH, BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_NORTH,   BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_EAST,    BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_UP_SOUTH,   BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { GO_GATE_GANDLING_ENTRANCE,   BOSS_GANDLING,  DOOR_TYPE_ROOM },
        { 0,                           0,              DOOR_TYPE_ROOM }
    };

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the twelve spawned bosses. Kirtonos is summoned
    // again after every FAIL, so he is tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_JANDICE,    DATA_JANDICE_GUID    },
        { NPC_RATTLEGORE, DATA_RATTLEGORE_GUID },
        { NPC_MARDUK,     DATA_MARDUK_GUID     },
        { NPC_VECTUS,     DATA_VECTUS_GUID     },
        { NPC_RAS,        DATA_RAS_GUID        },
        { NPC_MALICIA,    DATA_MALICIA_GUID    },
        { NPC_KRASTINOV,  DATA_KRASTINOV_GUID  },
        { NPC_POLKELT,    DATA_POLKELT_GUID    },
        { NPC_RAVENIAN,   DATA_RAVENIAN_GUID   },
        { NPC_ALEXEI,     DATA_ALEXEI_GUID     },
        { NPC_ILLUCIA,    DATA_ILLUCIA_GUID    },
        { NPC_GANDLING,   DATA_GANDLING_GUID   },
        { 0,              0                    }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_VIEWING_ROOM_DOOR,        DATA_VIEWING_ROOM_DOOR_GUID },
        { GO_GATE_GANDLING_ENTRANCE,   DATA_GANDLING_ENTRANCE_GUID },
        { GO_EMBALMING_FLUID,          DATA_EMBALMING_FLUID_GUID   },
        { GO_GATE_GANDLING_DOWN_NORTH, DataClassroomGateGuid(Classroom::ShadowVault)     },
        { GO_GATE_GANDLING_DOWN_EAST,  DataClassroomGateGuid(Classroom::BarovVault)      },
        { GO_GATE_GANDLING_DOWN_SOUTH, DataClassroomGateGuid(Classroom::RavenianVault)   },
        { GO_GATE_GANDLING_UP_NORTH,   DataClassroomGateGuid(Classroom::HallOfSecrets)   },
        { GO_GATE_GANDLING_UP_EAST,    DataClassroomGateGuid(Classroom::HallOfTheDamned) },
        { GO_GATE_GANDLING_UP_SOUTH,   DataClassroomGateGuid(Classroom::Coven)           },
        { 0,                           0                           }
    };

    constexpr bool IsInstructorBoss(uint32 id)
    {
        return InstructorOfBoss(id).has_value();
    }
}

class instance_scholomance_rework : public InstanceMapScript
{
public:
    instance_scholomance_rework() : InstanceMapScript(kInstanceScriptName, kMapScholomance) { }

    struct instance_scholomance_rework_InstanceMapScript : public InstanceScript, public InstanceApi
    {
        explicit instance_scholomance_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadDoorData(doorData);
            LoadObjectData(creatureData, gameObjectData);
        }

        // ------------------------------------------------------------------------------------------------------------
        // InstanceApi
        // ------------------------------------------------------------------------------------------------------------
        PassingGrades const& Grades() const override { return _grades; }

        void ClearGrades() override
        {
            _grades.Clear();
            SaveToDB();
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_GANDLING:
                    // Hidden until the sixth instructor dies (stock: invisible, faction 35); S11's Reset applies the
                    // same from DATA_GANDLING_REVEALED.
                    ApplyGandlingReveal(creature, Revealed());
                    ApplyHardModeLoot(creature, _gandlingHardMode, BOSS_GANDLING);
                    break;
                case NPC_RAS:
                    ApplyHardModeLoot(creature, _rasHardMode, BOSS_RAS);
                    break;
                case NPC_KIRTONOS:
                    _kirtonos = creature->GetGUID();
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
                case GO_VIEWING_ROOM_DOOR:
                    go->AllowSaveToDB(true);    // stock: the door stays open once the key opened it
                    break;
                case GO_GATE_KIRTONOS:
                    _gateKirtonos = go->GetGUID();
                    break;
                case GO_BRAZIER_KIRTONOS:
                    _brazierKirtonos = go->GetGUID();
                    break;
                default:
                    break;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            // Stock keys (instance_scholomance GetGuidData): the gameobject or creature entry itself.
            switch (type)
            {
                case GO_GATE_KIRTONOS:
                    return _gateKirtonos;
                case GO_BRAZIER_KIRTONOS:
                    return _brazierKirtonos;
                case GO_GATE_GANDLING_ENTRANCE:
                    return InstanceScript::GetGuidData(DATA_GANDLING_ENTRANCE_GUID);
                case NPC_GANDLING:
                    return InstanceScript::GetGuidData(DATA_GANDLING_GUID);
                case NPC_KIRTONOS:
                    return _kirtonos;
                default:
                    break;
            }
            if (std::optional<Classroom> const room = ClassroomOfGate(type))
                return InstanceScript::GetGuidData(DataClassroomGateGuid(*room));
            if (type >= DATA_DETAINED && type < DATA_DETAINED + kClassroomCount)
                return _detained[type - DATA_DETAINED];
            return InstanceScript::GetGuidData(type);
        }

        void SetGuidData(uint32 type, ObjectGuid data) override
        {
            if (type >= DATA_PASSING_GRADE && type < DATA_PASSING_GRADE + kInstructorCount)
            {
                AwardGrade(Instructor(type - DATA_PASSING_GRADE), data);
                return;
            }
            if (type >= DATA_DETAINED && type < DATA_DETAINED + kClassroomCount)
            {
                _detained[type - DATA_DETAINED] = data;
                return;
            }
            InstanceScript::SetGuidData(type, data);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            bool const wasRevealed = Revealed();
            if (!InstanceScript::SetBossState(id, state))
                return false;

            if (IsInstructorBoss(id) && state == DONE && !wasRevealed && Revealed())
                RevealGandling();

            switch (id)
            {
                case BOSS_RAS:
                    if (state == DONE && _rasHardMode)
                    {
                        // The kill flag (the loot is already filled: Unit::Kill runs before JustDied).
                        _rasHardModeKilled = 1;
                        SaveToDB();
                    }
                    ApplyHardModeLoot(GetCreature(DATA_RAS_GUID), _rasHardMode, BOSS_RAS);
                    break;
                case BOSS_GANDLING:
                    if (state == DONE && _gandlingHardMode)
                    {
                        _gandlingHardModeKilled = 1;
                        SaveToDB();
                    }
                    ApplyHardModeLoot(GetCreature(DATA_GANDLING_GUID), _gandlingHardMode, BOSS_GANDLING);
                    // Detention safety (handoff section 3.7): his fight is over or reset, nobody is detained any more;
                    // the door data has opened every gate.
                    if (state != IN_PROGRESS)
                        for (ObjectGuid& guid : _detained)
                            guid.Clear();
                    break;
                default:
                    break;
            }
            return true;
        }

        // ------------------------------------------------------------------------------------------------------------
        // Data
        // ------------------------------------------------------------------------------------------------------------
        void SetData(uint32 type, uint32 data) override
        {
            switch (type)
            {
                case DATA_KIRTONOS_THE_HERALD:
                    SetKirtonos(data);
                    SaveToDB();
                    return;
                case DATA_MINI_BOSSES:
                    // The six stock death rows (SET_INST_DATA 1 1) go with each instructor's SmartAI; a stray call is
                    // ignored: the instructor states own the reveal (handoff section 7 #11).
                    LOG_DEBUG(kLog, "scholo instance: ignored legacy SetData(DATA_MINI_BOSSES, {})", data);
                    return;
                case DATA_RAS_HUMAN:
                    _rasHuman = data;       // stock: stored, not saved
                    return;
                case DATA_DARKMASTER_GANDLING:
                    // Stock: the entrance gate follows Gandling's fight (the door data does the same on BOSS_GANDLING).
                    if (GameObject* gate = GetGameObject(DATA_GANDLING_ENTRANCE_GUID))
                        HandleGameObject(ObjectGuid::Empty, data != IN_PROGRESS, gate);
                    return;
                case DATA_KEEPSAKE_PAGE:
                    CollectPage(data);
                    return;
                case DATA_KEEPSAKE_BOUND:
                    if (data && !_keepsakeBound
                        && KeepsakeBindAllowed(_keepsakePages, instance->IsHeroic(), GetBossState(BOSS_RAS)))
                    {
                        _keepsakeBound = 1;
                        LOG_INFO(kLog, "scholo instance keepsake bound");
                        SaveToDB();
                    }
                    return;
                case DATA_RAS_HARD_MODE:
                    if (!RasHardModeChangeAllowed(data, _keepsakeBound != 0, instance->IsHeroic(),
                        GetBossState(BOSS_RAS)))
                        return;
                    _rasHardMode = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(DATA_RAS_GUID), _rasHardMode, BOSS_RAS);
                    LOG_INFO(kLog, "scholo instance ras hard-mode={}", _rasHardMode);
                    SaveToDB();
                    return;
                case DATA_GANDLING_HARD_MODE:
                    if (!GandlingHardModeChangeAllowed(data, _grades.HonorsOpen(), instance->IsHeroic(), Revealed(),
                        GetBossState(BOSS_GANDLING)))
                        return;
                    _gandlingHardMode = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(DATA_GANDLING_GUID), _gandlingHardMode, BOSS_GANDLING);
                    LOG_INFO(kLog, "scholo instance gandling hard-mode={}", _gandlingHardMode);
                    SaveToDB();
                    return;
                default:
                    break;
            }
            if (type >= DATA_CLASSROOM_GATE && type < DATA_CLASSROOM_GATE + kClassroomCount)
            {
                // S11's detention: a room's gate by hand (the door data sets every gate again on the next state
                // change of its bosses).
                if (GameObject* gate = GetGameObject(DataClassroomGateGuid(Classroom(type - DATA_CLASSROOM_GATE))))
                    HandleGameObject(ObjectGuid::Empty, data != 0, gate);
            }
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_KIRTONOS_THE_HERALD:
                    return _kirtonosState;
                case DATA_MINI_BOSSES:
                    return InstructorsDone(States());
                case DATA_RAS_HUMAN:
                    return _rasHuman;
                case DATA_DARKMASTER_GANDLING:
                    return GetBossState(BOSS_GANDLING);
                case DATA_KEEPSAKE_PAGE:
                    return _keepsakePages;
                case DATA_KEEPSAKE_PAGE_COUNT:
                    return KeepsakePageCount(_keepsakePages);
                case DATA_KEEPSAKE_BOUND:
                    return _keepsakeBound;
                case DATA_RAS_HARD_MODE:
                    return _rasHardMode;
                case DATA_RAS_HARD_MODE_KILLED:
                    return _rasHardModeKilled;
                case DATA_GANDLING_HARD_MODE:
                    return _gandlingHardMode;
                case DATA_GANDLING_HARD_MODE_KILLED:
                    return _gandlingHardModeKilled;
                case DATA_GANDLING_REVEALED:
                    return Revealed() ? 1 : 0;
                case DATA_HONORS_OPEN:
                    return _grades.HonorsOpen() ? 1 : 0;
                default:
                    break;
            }
            if (type >= DATA_GRADE_HOLDERS && type < DATA_GRADE_HOLDERS + kInstructorCount)
                return _grades.Holders(Instructor(type - DATA_GRADE_HOLDERS));
            if (type >= DATA_CLASSROOM_GATE && type < DATA_CLASSROOM_GATE + kClassroomCount)
            {
                GameObject const* gate = instance->GetGameObject(
                    InstanceScript::GetGuidData(DataClassroomGateGuid(Classroom(type - DATA_CLASSROOM_GATE))));
                return !gate ? 2 : gate->GetGoState() == GO_STATE_ACTIVE ? 1 : 0;
            }
            return 0;
        }

        // ------------------------------------------------------------------------------------------------------------
        // Save
        // ------------------------------------------------------------------------------------------------------------
        std::string GetSaveData() override
        {
            ScholoSave save;
            save.states = States();
            save.kirtonos = _kirtonosState;
            save.keepsakePages = _keepsakePages;
            save.keepsakeBound = _keepsakeBound;
            save.rasHardMode = _rasHardMode;
            save.rasHardModeKilled = _rasHardModeKilled;
            save.gandlingHardMode = _gandlingHardMode;
            save.gandlingHardModeKilled = _gandlingHardModeKilled;
            save.grades = _grades;
            return FormatScholoSave(save);
        }

        // Reads this script's "S C" string, or the stock "<kirtonos> <miniBosses>" (with the completed-encounter mask,
        // which Map::CreateInstanceData sets before Load).
        void Load(char const* in) override
        {
            if (!in)
                return;

            ScholoSave save;
            if (!ParseScholoSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "scholo instance: ignored save '{}'", in);
                return;
            }

            _kirtonosState = save.kirtonos;
            _keepsakePages = save.keepsakePages;
            _keepsakeBound = save.keepsakeBound;
            _rasHardMode = save.rasHardMode;
            _rasHardModeKilled = save.rasHardModeKilled;
            _gandlingHardMode = save.gandlingHardMode;
            _gandlingHardModeKilled = save.gandlingHardModeKilled;
            _grades = save.grades;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips our switch (no reveal yell,
            // no kill flag); Gandling's visibility and the loot bits follow from OnCreatureCreate.
            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.states[i]));
        }

    private:
        std::array<uint32, kBossCount> States() const
        {
            std::array<uint32, kBossCount> states{};
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                EncounterState const s = GetBossState(i);
                states[i] = s == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(s);
            }
            return states;
        }

        bool Revealed() const
        {
            return GandlingRevealed(States());
        }

        // The sixth instructor died (live, not a load): "School is in session!" and Gandling shows himself (stock:
        // Talk(0) and Reset() on the sixth SetData(DATA_MINI_BOSSES)).
        void RevealGandling()
        {
            LOG_INFO(kLog, "scholo instance gandling revealed (six instructors done)");
            Creature* gandling = GetCreature(DATA_GANDLING_GUID);
            if (!gandling || !gandling->IsAlive())
                return;
            ApplyGandlingReveal(gandling, true);
            if (gandling->IsAIEnabled && gandling->AI())
            {
                gandling->AI()->Talk(YELL_GANDLING_SCHOOL_IN_SESSION);
                gandling->AI()->DoAction(kActionGandlingRevealed);
            }
        }

        // Stock DATA_KIRTONOS_THE_HERALD (instance_scholomance.cpp SetData, copied; see the file comment).
        void SetKirtonos(uint32 data)
        {
            switch (data)
            {
                case IN_PROGRESS:
                    // summon kirtonos and close door
                    if (_kirtonosState == NOT_STARTED)
                    {
                        Position const at(kKirtonosSpawn.x, kKirtonosSpawn.y, kKirtonosSpawn.z, kKirtonosSpawn.o);
                        if (Creature* kirtonos = instance->SummonCreature(NPC_KIRTONOS, at))
                        {
                            _kirtonos = kirtonos->GetGUID();
                            kirtonos->AI()->DoAction(IN_PROGRESS);
                        }
                        if (GameObject* gate = instance->GetGameObject(_gateKirtonos))
                            gate->SetGoState(GO_STATE_READY);
                    }
                    _kirtonosState = data;
                    break;
                case FAIL:
                    // open door and reset brazier
                    if (GameObject* gate = instance->GetGameObject(_gateKirtonos))
                        gate->SetGoState(GO_STATE_ACTIVE);
                    if (GameObject* brazier = instance->GetGameObject(_brazierKirtonos))
                    {
                        brazier->SetGoState(GO_STATE_READY);
                        brazier->SetLootState(GO_JUST_DEACTIVATED);
                        brazier->Respawn();
                    }
                    _kirtonosState = NOT_STARTED;
                    break;
                case DONE:
                    // open door
                    if (GameObject* gate = instance->GetGameObject(_gateKirtonos))
                        gate->SetGoState(GO_STATE_ACTIVE);
                    [[fallthrough]];
                default:
                    _kirtonosState = data;
                    break;
            }
        }

        // S12's page GOs (heroic): SetData(DATA_KEEPSAKE_PAGE, page 0..2), once each.
        void CollectPage(uint32 page)
        {
            if (!KeepsakePageAllowed(page, instance->IsHeroic(), GetBossState(BOSS_RAS)))
                return;
            uint32 const bit = 1u << page;
            if (_keepsakePages & bit)
                return;
            _keepsakePages |= bit;
            LOG_INFO(kLog, "scholo instance keepsake page={} pages={}/{}", page + 1,
                KeepsakePageCount(_keepsakePages), kKeepsakePageCount);
            SaveToDB();
        }

        // Ruling 22: heroic only; grades live here (saved), the auras are only their display (S13).
        void AwardGrade(Instructor who, ObjectGuid player)
        {
            if (!instance->IsHeroic() || !player.IsPlayer())
                return;
            if (!_grades.Award(player.GetCounter(), who))
                return;
            LOG_INFO(kLog, "scholo instance passing-grade instructor={} player={} holders={} honors={}",
                kInstructorNames[std::size_t(who)], player.ToString(), _grades.Holders(who),
                _grades.HonorsOpen() ? 1 : 0);
            SaveToDB();
        }

        // Item variants IV7 (the Deadmines pattern): the heroic lootid holds the hard mode list in group 2 at LootMode
        // 2 (LOOT_MODE_HARD_MODE_1); the bit rides the boss's loot mode while the flag is lit and he is not dead yet.
        void ApplyHardModeLoot(Creature* boss, uint32 lit, uint32 bossId)
        {
            if (boss)
                DungeonKit::SetHardModeLoot(boss, lit != 0 && GetBossState(bossId) != DONE);
        }

        // Stock (Kirtonos's event)
        ObjectGuid _gateKirtonos;
        ObjectGuid _brazierKirtonos;
        ObjectGuid _kirtonos;
        uint32 _kirtonosState = NOT_STARTED;
        uint32 _rasHuman = 0;

        // The rework
        uint32 _keepsakePages = 0;
        uint32 _keepsakeBound = 0;
        uint32 _rasHardMode = 0;
        uint32 _rasHardModeKilled = 0;
        uint32 _gandlingHardMode = 0;
        uint32 _gandlingHardModeKilled = 0;
        PassingGrades _grades;
        std::array<ObjectGuid, kClassroomCount> _detained{};
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_scholomance_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_scholomance_rework()
{
    new instance_scholomance_rework();
}
