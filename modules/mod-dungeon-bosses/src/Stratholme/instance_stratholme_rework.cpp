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

// The Stratholme build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_stratholme` (user ruling 2026-11-08 on section 7 #2): modules load after the core scripts, and a
// database-bound script registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts),
// so map 329's instance_template row is untouched and the stock InstanceMapScript is replaced at load. The other
// scripts of the stock folder stay registered and keep working: go_enchanted_scarlet_thread (it calls
// SetGuidData(DATA_SCARLET_THREAD_LOOTED)), boss_jarien and boss_sothos (BossAI on boss slots 2 and 3, kept theirs
// here) and boss_baroness_anastari (unbound once 10436 is rebound): their AIs check the instance name
// (GetStratholmeAI), which is unchanged, so none of them is copied.
//
// Re-implemented from the stock instance (src/server/scripts/EasternKingdoms/Stratholme/instance_stratholme.cpp at
// Playerbot 97f46f56a, which stays untouched; its last upstream change is 9ce0f3dcc, moostigre, AzerothCore #27834,
// "recover events after a restart/persist in instance state", after 13cb5db8e, moostigre, #27342, "Restore Scarlet
// Threads"; Barthilas's run by daobashun, #17669; the file's history goes back to Yehonal's first commit, with
// Kargatum, Francesco Borzi, Nefertumm, Kitzunu, Skjalf and others): the Baron Run (the 45 minute clock, aura 27861,
// the yells at 10 / 5 / 0, Ysida's execution held while the Baron fights), the ziggurat states and doors, the
// Gauntlet and Slaughter gates, the slaughter event's abominations, Ramstein and Black Guards, the two gate traps and
// their cooldowns, the scarlet thread spawner, the postboxes, the event recovery after a restart, and the stock save
// "STR", which still loads. The data ids keep their stock numbers and meanings (the stock SmartAI and
// mod-dungeon-clear read and write them). Each upstream merge re-diffs the stock file against 9ce0f3dcc (handoff
// section 6).
//
// What is new: 17 boss states (StratholmeRework.h; Jarien 2 and Sothos 3 keep the stock slots); the Service Entrance
// Gate 175368 opens on create (section 10); the ziggurat softlock fix (a crystal that breaks before its boss dies is
// remembered, ST implementation note 1); the slaughter event without the Mindless Undead stage (Ramstein's death goes
// straight to the Black Guards, ST 3395-3400); Barthilas's portcullises as door data (his run is gone, S9); the Baron's
// door by his boss state; the Baron's hard mode flag DATA_ULTIMATUM and Balnazzar's DATA_GRAND_LIE with their kill
// slots and loot bits; the exit gate on the Baron's death when Ysida is dead (ST implementation note 9); the "S R" save
// string. While kWave2Bound is false the Main Gate bosses run stock: a stock boss's death sets its boss state.

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameTime.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StratholmeRework.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <list>
#include <unordered_set>

using namespace StratholmeRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Barthilas's two portcullises (his stock SmartAI closed them on aggro and opened them on death and reset; the
    // rework drops it, S9): DOOR_TYPE_ROOM on his boss state, open unless he fights.
    DoorData const doorData[] =
    {
        { GO_BARTHILAS_PORTCULLIS_1, BOSS_BARTHILAS, DOOR_TYPE_ROOM },
        { GO_BARTHILAS_PORTCULLIS_2, BOSS_BARTHILAS, DOOR_TYPE_ROOM },
        { 0,                         0,              DOOR_TYPE_ROOM }
    };

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the twelve spawned bosses and Ysida. Ramstein is
    // summoned by the slaughter event and Balnazzar is Dathrohan after UpdateEntry: both are tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_UNFORGIVEN,   DATA_UNFORGIVEN_GUID },
        { NPC_FORRESTEN,    DATA_FORRESTEN_GUID  },
        { NPC_TIMMY,        DATA_TIMMY_GUID      },
        { NPC_WILLEY,       DATA_WILLEY_GUID     },
        { NPC_MALOR,        DATA_MALOR_GUID      },
        { NPC_GALFORD,      DATA_GALFORD_GUID    },
        { NPC_DATHROHAN,    DATA_DATHROHAN_GUID  },
        { NPC_BARONESS,     DATA_BARONESS_GUID   },
        { NPC_NERUBENKAN,   DATA_NERUBENKAN_GUID },
        { NPC_MALEKI,       DATA_MALEKI_GUID     },
        { NPC_BARTHILAS,    DATA_BARTHILAS_GUID  },
        { NPC_BARON,        DATA_BARON_GUID      },
        { NPC_YSIDA,        DATA_YSIDA_GUID      },
        { 0,                0                    }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_YSIDA_CAGE,    DATA_YSIDA_CAGE_GUID },
        { GO_EXIT_GATE,     DATA_EXIT_GATE_GUID  },
        { 0,                0                    }
    };

    enum StratholmeEvents
    {
        EVENT_BARON_TIME            = 1,
        EVENT_FORCE_SLAUGHTER_EVENT = 3,
        EVENT_SPAWN_BLACK_GUARD     = 4,
        EVENT_EXECUTE_PRISONER      = 5,
        EVENT_GATE1_TRAP            = 6,
        EVENT_GATE1_DELAY           = 7,
        EVENT_GATE1_CRITTER_DELAY   = 8,
        EVENT_GATE2_TRAP            = 9,
        EVENT_GATE2_DELAY           = 10,
        EVENT_GATE2_CRITTER_DELAY   = 11,
    };

    enum GateTrapIndexes
    {
        GATE_TRAP_SCARLET,
        GATE_TRAP_UNDEAD,
        MAX_GATE_TRAPS
    };

    constexpr uint8 MAX_GATE_TRAP_GATES = 4;
    constexpr uint32 GATE_TRAP_COOLDOWN = 30 * MINUTE;
    constexpr uint32 YSIDA_ACTION_FIVE_MINUTES = 1;     // stock: Ysida's SmartAI reacts to SetData(1, 1)

    // Creatures spawned during the gate trap events (stock aPlaguedCritters).
    std::array<uint32, 3> const kPlaguedCritters{ { NPC_PLAGUED_RAT, NPC_PLAGUED_MAGGOT, NPC_PLAGUED_INSECT } };
}

class instance_stratholme_rework : public InstanceMapScript
{
public:
    instance_stratholme_rework() : InstanceMapScript(kInstanceScriptName, kMapStratholme) { }

    struct instance_stratholme_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_stratholme_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadDoorData(doorData);
            LoadObjectData(creatureData, gameObjectData);
            _gateTrapsCooldown.fill(false);
            _gateTrapCooldownEnd.fill(0);
            _gateTrapNeedsRecovery.fill(true);
        }

        void OnPlayerEnter(Player* player) override
        {
            InstanceScript::OnPlayerEnter(player);

            if (_baronRunTime > 0)
                if (Aura* aura = player->AddAura(SPELL_BARON_ULTIMATUM, player))
                    aura->SetDuration(_baronRunTime * MINUTE * IN_MILLISECONDS);

            SpawnScarletThread();
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_VENOM_BELCHER:
                case NPC_BILE_SPEWER:
                    if (_slaughter == SLAUGHTER_ABOMINATIONS && creature->GetSpawnId())
                        _abominationSpawnIds.insert(creature->GetSpawnId());
                    break;
                case NPC_RAMSTEIN:
                    _ramstein = creature->GetGUID();
                    if (_slaughter == SLAUGHTER_RAMSTEIN)
                        ++_slaughterNPCs;
                    break;
                case NPC_BLACK_GUARD:
                    if (_slaughter == SLAUGHTER_BLACK_GUARD)
                        ++_slaughterNPCs;
                    break;
                case NPC_BARON:
                    ApplyHardModeLoot(creature, _ultimatum, BOSS_BARON);
                    break;
                case NPC_DATHROHAN:
                    ApplyHardModeLoot(creature, _grandLie, BOSS_BALNAZZAR);
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
                case GO_CRUSADER_SQUARE_DOOR:
                case GO_HOARD_DOOR:
                case GO_HALL_OF_HIGH_COMMAND:
                case GO_GAUNTLET_DOOR_1:
                case GO_GAUNTLET_DOOR_2:
                    go->AllowSaveToDB(true);
                    break;
                case GO_ZIGGURAT_DOORS1:
                case GO_ZIGGURAT_DOORS2:
                case GO_ZIGGURAT_DOORS3:
                {
                    uint32 const z = go->GetEntry() == GO_ZIGGURAT_DOORS1 ? 0 : go->GetEntry() == GO_ZIGGURAT_DOORS2
                        ? 1 : 2;
                    go->AllowSaveToDB(true);
                    _zigguratDoors[z] = go->GetGUID();
                    if (_ziggurats[z].state >= kZigguratBossDead)
                        go->SetGoState(GO_STATE_ACTIVE);
                    break;
                }
                case GO_GAUNTLET_GATE:
                    go->AllowSaveToDB(true);
                    _gauntletGate = go->GetGUID();
                    if (AllZigguratsBroken(_ziggurats))
                        go->SetGoState(GO_STATE_ACTIVE);
                    break;
                case GO_SLAUGHTER_GATE:
                    go->AllowSaveToDB(true);
                    _slaughterGate = go->GetGUID();
                    if (AllZigguratsBroken(_ziggurats))
                        go->SetGoState(GO_STATE_ACTIVE);
                    break;
                case GO_ZIGGURAT_DOORS4:
                    go->AllowSaveToDB(true);
                    _ramsteinDoor = go->GetGUID();
                    if (_slaughter == SLAUGHTER_COMPLETE)
                        go->SetGoState(GO_STATE_ACTIVE);
                    break;
                case GO_ZIGGURAT_DOORS5:
                    go->AllowSaveToDB(true);
                    _baronDoor = go->GetGUID();
                    UpdateBaronDoor();
                    break;
                case GO_SLAUGHTER_GATE_SIDE:
                    go->AllowSaveToDB(true);
                    _sideGate = go->GetGUID();
                    if (SideGateOpen(_slaughter))
                        go->SetGoState(GO_STATE_ACTIVE);
                    break;
                case GO_PORT_TRAP_GATE_1:
                    HandleGateTrapCreate(go, 0);
                    break;
                case GO_PORT_TRAP_GATE_2:
                    HandleGateTrapCreate(go, 1);
                    break;
                case GO_PORT_TRAP_GATE_3:
                    HandleGateTrapCreate(go, 2);
                    break;
                case GO_PORT_TRAP_GATE_4:
                    HandleGateTrapCreate(go, 3);
                    break;
                case GO_SERVICE_ENTRANCE_GATE:
                    // Section 10 (ruling on section 7 #4): the Service Entrance is open from the start, on create and
                    // on every reload; the Gauntlet Gates stay keyed.
                    go->SetGoState(GO_STATE_ACTIVE);
                    break;
                case GO_EXIT_GATE:
                    // Opened by Ysida (her SmartAI) or by the Baron's death when she is dead: keep it open on reload.
                    go->AllowSaveToDB(true);
                    break;
                default:
                    break;
            }
        }

        void OnUnitDeath(Unit* unit) override
        {
            Creature* creature = unit ? unit->ToCreature() : nullptr;
            if (!creature)
                return;

            switch (creature->GetEntry())
            {
                case NPC_VENOM_BELCHER:
                case NPC_BILE_SPEWER:
                    if (_slaughter != SLAUGHTER_ABOMINATIONS || !_abominationSpawnIds.count(creature->GetSpawnId())
                        || HasLivingAbominations(creature->GetSpawnId()))
                        break;
                    _abominationSpawnIds.clear();
                    AdvanceSlaughterEvent();
                    break;
                case NPC_RAMSTEIN:
                case NPC_BLACK_GUARD:
                    if (IsCurrentSlaughterTarget(creature->GetEntry()) && _slaughterNPCs && --_slaughterNPCs == 0)
                        AdvanceSlaughterEvent();
                    break;
                case NPC_BARON:
                    events.CancelEvent(EVENT_BARON_TIME);
                    DoRemoveAurasDueToSpellOnPlayers(SPELL_BARON_ULTIMATUM);
                    break;
                default:
                    break;
            }

            // A boss that is not a BossAI (a Main Gate boss on its stock SmartAI until wave 2 binds it, or a data
            // rollback) sets no boss state itself: its death does it here.
            std::optional<uint32> const boss = BossOfEntry(creature->GetEntry());
            if (!boss || GetBossState(*boss) == DONE)
                return;
            if (creature->IsAIEnabled && dynamic_cast<BossAI*>(creature->AI()))
                return;     // a rework boss: its own BossAI::_JustDied sets DONE
            LOG_INFO(kLog, "strat instance stock boss {} died: boss state {} DONE", creature->GetEntry(), *boss);
            SetBossState(*boss, DONE);
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            if (type == DATA_RAMSTEIN_GUID)
                return _ramstein;
            return InstanceScript::GetGuidData(type);
        }

        void SetGuidData(uint32 type, ObjectGuid data) override
        {
            if (type != DATA_SCARLET_THREAD_LOOTED)
            {
                InstanceScript::SetGuidData(type, data);
                return;
            }
            if (data != _scarletThreadGuid)
                return;

            _scarletThreadUsedLocations |= 1 << _scarletThreadLocation;
            _scarletThreadGuid.Clear();
            SpawnScarletThread();
            SaveToDB();
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            if (!InstanceScript::SetBossState(id, state))
                return false;

            // A ziggurat boss's death opens its ziggurat (stock: the boss's own death row wrote DATA_ZIGGURATx 1; the
            // instance does it now, so no boss script has to; a stock row that still writes it changes nothing).
            if (state == DONE)
                if (std::optional<uint32> const z = ZigguratOfBoss(id))
                    SetData(DATA_ZIGGURAT1 + *z, kZigguratBossDead);

            switch (id)
            {
                case BOSS_BARON:
                    UpdateBaronDoor();
                    if (state == DONE)
                        OnBaronDone();
                    ApplyHardModeLoot(GetCreature(DATA_BARON_GUID), _ultimatum, BOSS_BARON);
                    break;
                case BOSS_BALNAZZAR:
                    if (state == DONE && _grandLie)
                    {
                        // The kill flag (the loot is already filled: Unit::Kill runs before JustDied).
                        LOG_INFO(kLog, "strat instance grand lie killed");
                        _grandLie = 0;
                        SetBossState(BOSS_GRAND_LIE, DONE);
                        SaveToDB();
                    }
                    ApplyHardModeLoot(GetCreature(DATA_DATHROHAN_GUID), _grandLie, BOSS_BALNAZZAR);
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
                case DATA_BARON_RUN:
                    if (_baronRunProgress == 0)
                    {
                        _baronRunProgress = 1;
                        _baronRunTime = kBaronRunMinutes;
                        DoCastSpellOnPlayers(SPELL_BARON_ULTIMATUM);
                        events.ScheduleEvent(EVENT_BARON_TIME, 60s);
                        BaronTalk(YELL_BARON_RUN_START);
                        LOG_INFO(kLog, "strat instance baron run started ({} min)", _baronRunTime);
                    }
                    break;
                case DATA_ZIGGURAT1:
                case DATA_ZIGGURAT2:
                case DATA_ZIGGURAT3:
                    WriteZiggurat(type - DATA_ZIGGURAT1, data);
                    break;
                case DATA_BARON_FIGHT:
                    // Stock: the Baron's SmartAI reported his fight; the rework's BossAI state does the same.
                    _baronFightData = data == IN_PROGRESS;
                    UpdateBaronDoor();
                    return;
                case DATA_MALLOW:
                    ++_postboxesOpened;
                    break;
                case DATA_BARTHILAS_RUN:
                    // Barthilas's run is gone (S9: he fights in his yard); a stray stock write is stored, nothing more.
                    _barthilasRun = data;
                    break;
                case DATA_ULTIMATUM:
                    if (!UltimatumChangeAllowed(data, instance->IsHeroic(), _baronRunTime, GetBossState(BOSS_BARON)))
                    {
                        LOG_DEBUG(kLog, "strat instance ultimatum={} refused", data);
                        return;
                    }
                    _ultimatum = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(DATA_BARON_GUID), _ultimatum, BOSS_BARON);
                    LOG_INFO(kLog, "strat instance ultimatum={}", _ultimatum);
                    break;
                case DATA_GRAND_LIE:
                    if (!GrandLieChangeAllowed(data, instance->IsHeroic(), kWave2Bound, GetBossState(BOSS_BALNAZZAR)))
                    {
                        LOG_DEBUG(kLog, "strat instance grand-lie={} refused", data);
                        return;
                    }
                    _grandLie = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(DATA_DATHROHAN_GUID), _grandLie, BOSS_BALNAZZAR);
                    LOG_INFO(kLog, "strat instance grand-lie={}", _grandLie);
                    break;
                case DATA_BARON_RUN_MINUTES:
                    // GM test (`.dbtest strat instance clock <minutes>`): the minutes left, while the clock runs.
                    if (!_baronRunTime)
                        return;
                    _baronRunTime = std::clamp<uint32>(data, 1, kBaronRunMinutes);
                    RefreshBaronRunAuras();
                    LOG_INFO(kLog, "strat instance baron run clock set to {} min", _baronRunTime);
                    break;
                default:
                    return;
            }

            SaveToDB();
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_BARON_RUN:
                    return _baronRunProgress;
                case DATA_ZIGGURAT1:
                case DATA_ZIGGURAT2:
                case DATA_ZIGGURAT3:
                    return _ziggurats[type - DATA_ZIGGURAT1].state;
                case DATA_BARON_FIGHT:
                    return BaronFighting() ? 1 : 0;
                case DATA_MALLOW:
                    return _postboxesOpened;
                case DATA_BARTHILAS_RUN:
                    return _barthilasRun;
                case DATA_ULTIMATUM:
                    return _ultimatum;
                case DATA_GRAND_LIE:
                    return _grandLie;
                case DATA_SLAUGHTER_STAGE:
                    return _slaughter;
                case DATA_BARON_RUN_MINUTES:
                    return _baronRunTime;
                case DATA_ZIGGURAT_PENDING:
                    return ZigguratPendingMask(_ziggurats);
                default:
                    return 0;
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Update (stock: the gate traps and the event timers)
        // ------------------------------------------------------------------------------------------------------------
        void Update(uint32 diff) override
        {
            InstanceScript::Update(diff);
            events.Update(diff);

            // The two gate traps: a player (not a GM) at the trap springs it unless it is on cooldown.
            Map::PlayerList const& players = instance->GetPlayers();
            for (uint8 i = 0; i < MAX_GATE_TRAPS; ++i)
            {
                if (_gateTrapsCooldown[i])
                    continue;
                for (auto const& ref : players)
                {
                    Player* player = ref.GetSource();
                    if (player && !player->IsGameMaster()
                        && player->IsWithinDist2d(kGateTraps[i].x, kGateTraps[i].y, kGateTrapRadius))
                    {
                        StartGateTrap(i, player);
                        break;
                    }
                }
            }

            while (uint32 const eventId = events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_GATE1_TRAP:
                    case EVENT_GATE2_TRAP:
                    {
                        uint8 const gate = eventId == EVENT_GATE1_TRAP ? GATE_TRAP_SCARLET : GATE_TRAP_UNDEAD;
                        _gateTrapsCooldown[gate] = false;
                        _gateTrapCooldownEnd[gate] = 0;
                        SaveToDB();
                        break;
                    }
                    case EVENT_GATE1_DELAY:
                        OpenTrapGates(GATE_TRAP_SCARLET);
                        break;
                    case EVENT_GATE2_DELAY:
                        OpenTrapGates(GATE_TRAP_UNDEAD);
                        break;
                    case EVENT_GATE1_CRITTER_DELAY:
                        SpawnTrapCritters(GATE_TRAP_SCARLET);
                        break;
                    case EVENT_GATE2_CRITTER_DELAY:
                        SpawnTrapCritters(GATE_TRAP_UNDEAD);
                        break;
                    case EVENT_BARON_TIME:
                        BaronRunTick();
                        break;
                    case EVENT_EXECUTE_PRISONER:
                        ExecutePrisoner();
                        break;
                    case EVENT_FORCE_SLAUGHTER_EVENT:
                        if (AnyPlayerNearSlaughter())
                            ProcessSlaughterEvent();
                        else
                            events.ScheduleEvent(EVENT_FORCE_SLAUGHTER_EVENT, 3s);
                        break;
                    case EVENT_SPAWN_BLACK_GUARD:
                        SpawnBlackGuards();
                        break;
                    default:
                        break;
                }
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Save
        // ------------------------------------------------------------------------------------------------------------
        std::string GetSaveData() override
        {
            StratSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                EncounterState const s = GetBossState(i);
                save.states[i] = s == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(s);
            }
            save.baronRunProgress = _baronRunProgress;
            save.baronRunMinutes = _baronRunTime;
            save.ziggurats = _ziggurats;
            save.slaughter = _slaughter;
            save.postboxes = _postboxesOpened;
            save.barthilasRun = _barthilasRun;
            save.scarletThreads = _scarletThreadUsedLocations;
            save.gateTrapEnd[GATE_TRAP_SCARLET] = uint32(_gateTrapCooldownEnd[GATE_TRAP_SCARLET]);
            save.gateTrapEnd[GATE_TRAP_UNDEAD] = uint32(_gateTrapCooldownEnd[GATE_TRAP_UNDEAD]);
            save.ultimatum = _ultimatum;
            save.grandLie = _grandLie;
            return FormatStratSave(save);
        }

        // Reads this script's "S R" string, or the stock "S T R ..." (with the completed-encounter mask, which
        // Map::CreateInstanceData sets before Load), then restarts the timers a restart lost (stock ReadSaveDataMore).
        void Load(char const* in) override
        {
            if (!in)
                return;

            StratSave save;
            if (!ParseStratSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "strat instance: ignored save '{}'", in);
                return;
            }

            _baronRunProgress = save.baronRunProgress;
            _baronRunTime = save.baronRunMinutes;
            _ziggurats = save.ziggurats;
            _slaughter = save.slaughter;
            _postboxesOpened = save.postboxes;
            _barthilasRun = save.barthilasRun;
            _scarletThreadUsedLocations = uint8(save.scarletThreads);
            _gateTrapCooldownEnd[GATE_TRAP_SCARLET] = time_t(save.gateTrapEnd[GATE_TRAP_SCARLET]);
            _gateTrapCooldownEnd[GATE_TRAP_UNDEAD] = time_t(save.gateTrapEnd[GATE_TRAP_UNDEAD]);
            _ultimatum = save.ultimatum;
            _grandLie = save.grandLie;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips our switch (no ziggurat
            // write, no kill flag); the doors and the loot bits follow from the create hooks.
            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.states[i]));

            if (_baronRunTime)
                events.ScheduleEvent(EVENT_BARON_TIME, 60s);
            if (_slaughter > SLAUGHTER_ABOMINATIONS && _slaughter < SLAUGHTER_COMPLETE)
                events.ScheduleEvent(EVENT_FORCE_SLAUGHTER_EVENT, 5s);
            RestoreGateTrapCooldown(GATE_TRAP_SCARLET);
            RestoreGateTrapCooldown(GATE_TRAP_UNDEAD);
        }

    private:
        // ------------------------------------------------------------------------------------------------------------
        // The Baron Run and the Baron
        // ------------------------------------------------------------------------------------------------------------
        void BaronTalk(uint8 group)
        {
            if (Creature* baron = GetCreature(DATA_BARON_GUID))
                if (baron->IsAIEnabled && baron->AI())
                    baron->AI()->Talk(group);
        }

        bool BaronFighting() const
        {
            return _baronFightData || GetBossState(BOSS_BARON) == IN_PROGRESS;
        }

        void UpdateBaronDoor()
        {
            if (GameObject* door = instance->GetGameObject(_baronDoor))
                door->SetGoState(BaronDoorOpen(_slaughter, BaronFighting()) ? GO_STATE_ACTIVE : GO_STATE_READY);
        }

        void RefreshBaronRunAuras()
        {
            for (auto const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (Aura* aura = player->GetAura(SPELL_BARON_ULTIMATUM))
                        aura->SetDuration(_baronRunTime * MINUTE * IN_MILLISECONDS);
        }

        // Stock EVENT_BARON_TIME: a minute off the clock; the yells only while he is out of combat.
        void BaronRunTick()
        {
            if (_baronRunTime)
                --_baronRunTime;
            Creature* baron = GetCreature(DATA_BARON_GUID);
            if (baron && !baron->IsInCombat())
            {
                switch (_baronRunTime)
                {
                    case 10:
                        BaronTalk(YELL_BARON_RUN_10M);
                        break;
                    case 5:
                        BaronTalk(YELL_BARON_RUN_5M);
                        if (Creature* ysida = GetCreature(DATA_YSIDA_GUID))
                            if (ysida->IsAlive() && ysida->IsAIEnabled && ysida->AI())
                                ysida->AI()->SetData(YSIDA_ACTION_FIVE_MINUTES, 1);
                        break;
                    case 0:
                        BaronTalk(YELL_BARON_RUN_0M);
                        DoRemoveAurasDueToSpellOnPlayers(SPELL_BARON_ULTIMATUM);
                        break;
                    default:
                        break;
                }
            }

            if (_baronRunTime > 0)
                events.ScheduleEvent(EVENT_BARON_TIME, 60s);
            else
                events.ScheduleEvent(EVENT_EXECUTE_PRISONER, 0ms);
            SaveToDB();
        }

        // Stock EVENT_EXECUTE_PRISONER: held while he fights (an Ultimatum attempt still going at 0 plays out); the
        // execution ends the Ultimatum (ruling 60: the next pull is the heroic fight).
        void ExecutePrisoner()
        {
            Creature* baron = GetCreature(DATA_BARON_GUID);
            if (!baron || !baron->IsAlive())
                return;
            if (baron->IsInCombat())
            {
                events.ScheduleEvent(EVENT_EXECUTE_PRISONER, 1s);
                return;
            }
            baron->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
            if (Creature* ysida = GetCreature(DATA_YSIDA_GUID))
                if (ysida->IsAlive())
                    Unit::Kill(baron, ysida);
            if (_ultimatum)
            {
                _ultimatum = 0;
                ApplyHardModeLoot(baron, _ultimatum, BOSS_BARON);
                LOG_INFO(kLog, "strat instance ultimatum cleared: the clock ran out");
            }
            SaveToDB();
        }

        // The Baron's death: the Ultimatum's kill slot, and the exit gate when Ysida is dead (ST note 9).
        void OnBaronDone()
        {
            if (_ultimatum)
            {
                LOG_INFO(kLog, "strat instance ultimatum killed");
                _ultimatum = 0;
                SetBossState(BOSS_ULTIMATUM, DONE);
            }
            Creature* ysida = GetCreature(DATA_YSIDA_GUID);
            if (ExitGateOpensOnBaronDeath(ysida && ysida->IsAlive()))
                if (GameObject* gate = GetGameObject(DATA_EXIT_GATE_GUID))
                {
                    gate->SetGoState(GO_STATE_ACTIVE);
                    LOG_INFO(kLog, "strat instance exit gate opened (Ysida is dead)");
                }
            SaveToDB();
        }

        // Item variants IV7 (the Deadmines pattern): the heroic lootid holds the hard mode list at LootMode 2
        // (LOOT_MODE_HARD_MODE_1); the bit rides the boss's loot mode while the flag is lit and he is not dead yet.
        void ApplyHardModeLoot(Creature* boss, uint32 lit, uint32 bossId)
        {
            if (boss)
                DungeonKit::SetHardModeLoot(boss, lit != 0 && GetBossState(bossId) != DONE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The ziggurats
        // ------------------------------------------------------------------------------------------------------------
        void WriteZiggurat(uint32 z, uint32 data)
        {
            bool const wasAllBroken = AllZigguratsBroken(_ziggurats);
            Ziggurat const before = _ziggurats[z];
            _ziggurats[z] = ZigguratAfterWrite(before, data);
            if (!(_ziggurats[z] == before))
                LOG_INFO(kLog, "strat instance ziggurat {} write {}: state {} -> {}{}", z + 1, data, before.state,
                    _ziggurats[z].state, _ziggurats[z].pending ? " (crystal pending)" : "");

            if (_ziggurats[z].state >= kZigguratBossDead)
                if (GameObject* door = instance->GetGameObject(_zigguratDoors[z]))
                    door->SetGoState(GO_STATE_ACTIVE);

            if (!wasAllBroken && AllZigguratsBroken(_ziggurats))
            {
                BaronTalk(YELL_BARON_ZIGGURATS_FALL);
                if (GameObject* gate = instance->GetGameObject(_gauntletGate))
                    gate->SetGoState(GO_STATE_ACTIVE);
                if (GameObject* gate = instance->GetGameObject(_slaughterGate))
                    gate->SetGoState(GO_STATE_ACTIVE);
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // The slaughter event
        // ------------------------------------------------------------------------------------------------------------
        void ProcessSlaughterEvent()
        {
            switch (_slaughter)
            {
                case SLAUGHTER_RAMSTEIN:
                    BaronTalk(YELL_BARON_SUMMON_RAMSTEIN);
                    instance->SummonCreature(NPC_RAMSTEIN, Position(kRamsteinSummon.x, kRamsteinSummon.y,
                        kRamsteinSummon.z, kRamsteinSummon.o));
                    break;
                case SLAUGHTER_BLACK_GUARD:
                    // ST 3395-3400: no Mindless Undead stage. The side gate opens as the stock Mindless stage opened
                    // it (S13 may have opened it at his first meat wave already).
                    if (GameObject* gate = instance->GetGameObject(_sideGate))
                        gate->SetGoState(GO_STATE_ACTIVE);
                    events.ScheduleEvent(EVENT_SPAWN_BLACK_GUARD, Milliseconds(kBlackGuardDelayMs));
                    break;
                case SLAUGHTER_COMPLETE:
                    BaronTalk(YELL_BARON_GUARDS_DEAD);
                    UpdateBaronDoor();
                    break;
                default:
                    break;
            }
        }

        void AdvanceSlaughterEvent()
        {
            uint32 const from = _slaughter;
            _slaughter = NextSlaughterStage(_slaughter);
            _slaughterNPCs = 0;
            LOG_INFO(kLog, "strat instance slaughter stage {} -> {}", from, _slaughter);
            SaveToDB();
            ProcessSlaughterEvent();
        }

        bool IsCurrentSlaughterTarget(uint32 entry) const
        {
            switch (_slaughter)
            {
                case SLAUGHTER_RAMSTEIN:
                    return entry == NPC_RAMSTEIN;
                case SLAUGHTER_BLACK_GUARD:
                    return entry == NPC_BLACK_GUARD;
                default:
                    return false;
            }
        }

        bool HasLivingAbominations(ObjectGuid::LowType dyingSpawnId) const
        {
            auto const& creatures = instance->GetCreatureBySpawnIdStore();
            for (ObjectGuid::LowType spawnId : _abominationSpawnIds)
            {
                if (spawnId == dyingSpawnId)
                    continue;

                auto const range = creatures.equal_range(spawnId);
                if (range.first == range.second)
                {
                    // An unloaded spawn still blocks the event unless it is waiting to respawn.
                    if (instance->GetCreatureRespawnTime(spawnId) <= GameTime::GetGameTime().count())
                        return true;
                }
                else
                    for (auto itr = range.first; itr != range.second; ++itr)
                        if (itr->second->IsAlive())
                            return true;
            }
            return false;
        }

        bool AnyPlayerNearSlaughter() const
        {
            for (auto const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (player->GetDistance2d(kSlaughterRecoveryCenter.x, kSlaughterRecoveryCenter.y)
                        < kSlaughterRecoveryRadius)
                        return true;
            return false;
        }

        void SpawnBlackGuards()
        {
            for (uint32 i = 0; i < kBlackGuardCount; ++i)
            {
                Point4 const& from = kBlackGuardPos[i];
                Point4 const& to = kBlackGuardPos[i + kBlackGuardCount];
                if (Creature* guard = instance->SummonCreature(NPC_BLACK_GUARD, Position(from.x, from.y, from.z,
                    from.o)))
                {
                    Position const home(to.x, to.y, to.z, to.o);
                    guard->SetWalk(true);
                    guard->GetMotionMaster()->MovePoint(0, home);
                    guard->SetHomePosition(home);
                    if (i == 0 && guard->IsAIEnabled && guard->AI())
                        guard->AI()->Talk(SAY_BLACK_GUARD_INIT);
                }
            }
            if (GameObject* door = instance->GetGameObject(_ramsteinDoor))
                door->SetGoState(GO_STATE_ACTIVE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The gate traps (stock)
        // ------------------------------------------------------------------------------------------------------------
        void HandleGateTrapCreate(GameObject* gate, uint8 index)
        {
            gate->AllowSaveToDB(true);
            _trapGates[index] = gate->GetGUID();

            // EventMap timers do not survive an instance unload. Finish an interrupted trap in its safe open state
            // instead of restoring a permanently closed gate.
            if (_gateTrapNeedsRecovery[index])
            {
                _gateTrapNeedsRecovery[index] = false;
                gate->SetGoState(GO_STATE_ACTIVE);
            }
        }

        void RestoreGateTrapCooldown(uint8 gate)
        {
            time_t const now = GameTime::GetGameTime().count();
            if (_gateTrapCooldownEnd[gate] <= now)
            {
                _gateTrapCooldownEnd[gate] = 0;
                return;
            }

            _gateTrapsCooldown[gate] = true;
            events.ScheduleEvent(gate == GATE_TRAP_SCARLET ? EVENT_GATE1_TRAP : EVENT_GATE2_TRAP,
                Seconds(_gateTrapCooldownEnd[gate] - now));
        }

        void StartGateTrap(uint8 gate, Player* player)
        {
            _gateTrapsCooldown[gate] = true;
            _gateTrapCooldownEnd[gate] = GameTime::GetGameTime().count() + GATE_TRAP_COOLDOWN;
            _trappedPlayers[gate] = player->GetGUID();

            HandleGameObject(_trapGates[2 * gate], false);
            HandleGameObject(_trapGates[2 * gate + 1], false);

            bool const scarlet = gate == GATE_TRAP_SCARLET;
            events.ScheduleEvent(scarlet ? EVENT_GATE1_TRAP : EVENT_GATE2_TRAP, Seconds(GATE_TRAP_COOLDOWN));
            events.ScheduleEvent(scarlet ? EVENT_GATE1_DELAY : EVENT_GATE2_DELAY, 20s);
            events.ScheduleEvent(scarlet ? EVENT_GATE1_CRITTER_DELAY : EVENT_GATE2_CRITTER_DELAY, 2s);
            SaveToDB();
        }

        void OpenTrapGates(uint8 gate)
        {
            HandleGameObject(_trapGates[2 * gate], true);
            HandleGameObject(_trapGates[2 * gate + 1], true);
        }

        void SpawnTrapCritters(uint8 gate)
        {
            Player* player = _trappedPlayers[gate] ? ObjectAccessor::GetPlayer(instance, _trappedPlayers[gate])
                : nullptr;
            if (!player)
                return;

            uint32 const entry = kPlaguedCritters[urand(0, kPlaguedCritters.size() - 1)];
            for (uint8 i = 0; i < 30; ++i)
            {
                float x = 0.f;
                float y = 0.f;
                float z = 0.f;
                player->GetRandomPoint(player->GetPosition(), 8.0f, x, y, z);
                z = player->GetPositionZ() + 1;
                if (Creature* critter = player->SummonCreature(entry, x, y, z, 0, TEMPSUMMON_DEAD_DESPAWN, 0))
                    if (critter->IsAIEnabled && critter->AI())
                        critter->AI()->AttackStart(player);
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // The scarlet threads (stock, AzerothCore #27342)
        // ------------------------------------------------------------------------------------------------------------
        void SpawnScarletThread()
        {
            if (_scarletThreadGuid || _scarletThreadUsedLocations == kAllScarletThreads)
                return;

            std::array<uint8, kScarletThreadLocations> availableLocations{};
            uint8 availableLocationCount = 0;
            for (uint8 location = 0; location < kScarletThreadLocations; ++location)
                if (!(_scarletThreadUsedLocations & (1 << location)))
                    availableLocations[availableLocationCount++] = location;

            if (!availableLocationCount)
                return;

            _scarletThreadLocation = availableLocations[urand(0, availableLocationCount - 1)];

            std::list<GameObject*> threads;
            instance->SummonGameObjectGroup(_scarletThreadLocation, &threads);
            if (threads.empty())
                return;

            _scarletThreadGuid = threads.front()->GetGUID();
            threads.front()->setActive(true);
        }

        EventMap events;

        // The Baron Run
        uint32 _baronRunProgress = 0;
        uint32 _baronRunTime = 0;
        bool _baronFightData = false;
        ObjectGuid _baronDoor;

        // The ziggurats and the gates they open
        std::array<Ziggurat, kZigguratCount> _ziggurats{};
        std::array<ObjectGuid, kZigguratCount> _zigguratDoors{};
        ObjectGuid _gauntletGate;
        ObjectGuid _slaughterGate;

        // The slaughter event
        uint32 _slaughter = SLAUGHTER_ABOMINATIONS;
        uint32 _slaughterNPCs = 0;
        std::unordered_set<ObjectGuid::LowType> _abominationSpawnIds;
        ObjectGuid _ramstein;
        ObjectGuid _ramsteinDoor;
        ObjectGuid _sideGate;

        // Stock odds and ends
        uint32 _postboxesOpened = 0;
        uint32 _barthilasRun = 0;

        // The gate traps
        std::array<bool, MAX_GATE_TRAPS> _gateTrapsCooldown{};
        std::array<bool, MAX_GATE_TRAP_GATES> _gateTrapNeedsRecovery{};
        std::array<time_t, MAX_GATE_TRAPS> _gateTrapCooldownEnd{};
        std::array<ObjectGuid, MAX_GATE_TRAPS> _trappedPlayers{};
        std::array<ObjectGuid, MAX_GATE_TRAP_GATES> _trapGates{};

        // The scarlet threads
        uint8 _scarletThreadUsedLocations = 0;
        uint8 _scarletThreadLocation = 0;
        ObjectGuid _scarletThreadGuid;

        // The hard modes
        uint32 _ultimatum = 0;
        uint32 _grandLie = 0;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_stratholme_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_stratholme_rework()
{
    new instance_stratholme_rework();
}
