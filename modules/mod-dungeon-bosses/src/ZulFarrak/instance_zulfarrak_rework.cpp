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

// The Zul'Farrak build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_zulfarrak` (section 7 #2 A): modules load after the core scripts, and a database-bound script registered
// later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 209's instance_template
// row is untouched and the stock InstanceMapScript is replaced at load. The other scripts the stock
// AddSC_instance_zulfarrak registers (spell_zulfarrak_summon_zulfarrak_zombies 10247, spell_zulfarrak_unlocking 10738)
// stay registered and keep working; the stock zulfarrak.cpp scripts (npc_sergeant_bly, npc_weegli_blastfuse,
// npc_shadowpriest_sezziz, go_troll_cage) stay registered too, unbound by the S0 rev and the dbc-tools rows.
//
// Re-implemented from the stock event (src/server/scripts/Kalimdor/ZulFarrak/instance_zulfarrak.cpp and zulfarrak.cpp,
// untouched): the stock data ids 0 to 2 with their stock meaning for the stock readers, the stage order of the Pyramid
// (the cages, the stair, the waves, the descent, the gather), the End Door's save and restore on create, the crew's
// points and the wave tables (ZulFarrakRework.h). Upstream: c9315e3ec moostigre <moostigre@proton.me> (#27731, "pyramid
// event fixes": the door walk, the barrel, the End Door save), 048025ceb UltraNix
// <80540499+UltraNix@users.noreply.github.com> (#7855, Bly's script, Weegli and the cage), df82d1be9 jrad7
// <106174524+jrad7@users.noreply.github.com> (#26183, Sezz'ziz's add points), 0dbb8c814 Skjalf (the save split); the
// file goes back to Yehonal, Kargatum, Kitzunu, Francesco Borzi and Jelle Meeus. Each upstream merge re-diffs both
// files against c9315e3ec (handoff section 6).
//
// What is new: 9 boss states (slot = DungeonEncounter bit; slot 8 the hard mode kill); the Pyramid's stage machine
// (section 7 #11 A: snapshots, restores, the landing restart, the stage directors of ZulFarrakKit.h); slots 5 and 6
// written here only; the crew's mask and modes (section 7 #12 A, #14 A, #16 A) with their restore by spawn id (RB-20);
// the paths and the Test's key (section 7 #18 A); the End Door opened at the end of the crew's fight with a fallback
// (section 7 #13 A); Gahz'rilla summoned by the instance at Velratha's strike, the gong inert (section 3.2 item 6); the
// hard mode flag, its kill slot and loot bit (section 3.2 item 7); the "ZFR" save with the stock "Z F" reader.

#include "CrewFightLogic.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitWings.h"
#include "EventMap.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GameTime.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include <array>
#include <cmath>
#include <memory>

using namespace ZulFarrakRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");
static_assert(kMapZulFarrak == MAP_ZUL_FARRAK, "map 209");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the spawned bosses, the Executioner, Ruuzlu and
    // the crew; the End Door and the gong. Gahz'rilla, Sezz'ziz and Nekrum are summons, tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_VELRATHA,     kGuidBossBase + BOSS_VELRATHA   },
        { NPC_ANTUSUL,      kGuidBossBase + BOSS_ANTUSUL    },
        { NPC_THEKA,        kGuidBossBase + BOSS_THEKA      },
        { NPC_ZUMRAH,       kGuidBossBase + BOSS_ZUMRAH     },
        { NPC_UKORZ,        kGuidBossBase + BOSS_UKORZ      },
        { NPC_EXECUTIONER,  kGuidExecutioner                },
        { NPC_RUUZLU,       kGuidRuuzlu                     },
        { NPC_BLY,          kGuidCrewBase + CREW_BLY        },
        { NPC_RAVEN,        kGuidCrewBase + CREW_RAVEN      },
        { NPC_ORO,          kGuidCrewBase + CREW_ORO        },
        { NPC_WEEGLI,       kGuidCrewBase + CREW_WEEGLI     },
        { NPC_MURTA,        kGuidCrewBase + CREW_MURTA      },
        { 0,                0                               }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_END_DOOR,  kGuidEndDoor    },
        { GO_GONG,      kGuidGong       },
        { 0,            0               }
    };

    enum ZfInstanceEvents
    {
        EVENT_PYRAMID_WATCH = 1,    // every second: the wipe check, the landing restart
        EVENT_ALTAR_START   = 2,    // stage 2 won: the descent kAltarDelayMs later
        EVENT_DOOR_WATCH    = 3,    // every 2 s once slot 6 is DONE: the End Door's fallback and latch
    };
}

// The five Troll Cages 141070-141074 (bound by the S0 rev in place of go_troll_cage): the key's open lock, the
// Unlocking spell 10738 (spell_zulfarrak_unlocking opens all five) and a click all end in UseDoorOrButton, which sets
// the loot state to GO_ACTIVATED; the instance opens the stage 2 gate on the first one and the other four with it
// (refused before the Executioner is dead: the key drops from him).
//
// R-1-FW M3: a refused open (a spare key 8444 used while the Executioner lives) shuts the cage again on the next
// update, or it would stay GO_ACTIVATED (no auto close) and never fire again: the Pyramid would be stuck at the Block.
// Shut by hand (GO_STATE_READY, GO_READY), never through ResetDoorOrButton: its GO_JUST_DEACTIVATED path despawns a
// door with a respawn delay (the cages' 86,400 s).
struct go_zf_troll_cage : public GameObjectAI
{
    explicit go_zf_troll_cage(GameObject* go) : GameObjectAI(go) { }

    void OnStateChanged(uint32 state, Unit* /*unit*/) override
    {
        if (state != GO_ACTIVATED)
            return;
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        instance->SetData(DATA_PYRAMID_CAGES, 1);
        _shutPending = instance->GetData(DATA_PYRAMID_CAGES) == 0;
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!_shutPending)
            return;
        _shutPending = false;
        Shut(me);
        DungeonKit::LogMechanic(kLogDungeon, "pyramid", "cage-refused", "shut again (the Block is not won)");
    }

    // A cage back to its shut, usable state (the refusal above, and the instance at the Block's win).
    static void Shut(GameObject* cage)
    {
        if (!cage || cage->getLootState() == GO_READY)
            return;
        cage->SetGoState(GO_STATE_READY);
        cage->SetLootState(GO_READY);
    }

private:
    bool _shutPending = false;
};

class instance_zulfarrak_rework : public InstanceMapScript
{
public:
    instance_zulfarrak_rework() : InstanceMapScript(kInstanceScriptName, MAP_ZUL_FARRAK) { }

    struct instance_zulfarrak_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_zulfarrak_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadObjectData(creatureData, gameObjectData);
            _crewModes.fill(CrewMode::Caged);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_EXECUTIONER:
                    SettleDeadExecutioner(creature);
                    break;
                case NPC_SEZZZIZ:
                    _sezzziz = creature->GetGUID();
                    _sezzzizSeen = true;
                    break;
                case NPC_NEKRUM:
                    _nekrum = creature->GetGUID();
                    _nekrumSeen = true;
                    break;
                case NPC_GAHZRILLA:
                    _gahzrilla = creature->GetGUID();
                    ApplyHardModeLoot(creature);
                    break;
                default:
                    break;
            }
            if (_director)
                _director->OnCreatureCreate(creature);
        }

        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            switch (go->GetEntry())
            {
                case GO_END_DOOR:
                    // Stock (OnGameObjectCreate): a blown door is restored on create; also once slot 6 is DONE.
                    // R-1-FW m2: never selectable, shut or blown (lock 0: a click would open it and skip the crew).
                    go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                    if (_endDoor == DONE || Slot(BOSS_CREW) == DONE)
                        OpenEndDoor(go);
                    break;
                case GO_TROLL_CAGE_1:
                case GO_TROLL_CAGE_2:
                case GO_TROLL_CAGE_3:
                case GO_TROLL_CAGE_4:
                case GO_TROLL_CAGE_5:
                    _cages[go->GetEntry() - GO_TROLL_CAGE_1] = go->GetGUID();
                    break;
                case GO_ZF_CREW_STASH:
                case GO_ZF_CREW_STASH_HEROIC:
                    _stash = go->GetGUID();
                    break;
                case GO_GONG:
                    go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);     // inert (the S0 rev sets it too)
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

            if (std::optional<uint32> const member = CrewIndexOf(creature->GetEntry()))
                OnCrewDeath(*member, "death");

            switch (creature->GetEntry())
            {
                case NPC_EXECUTIONER:
                    if (_pyramid.running && _pyramid.stage == PYRAMID_STAGE_BLOCK)
                        CompleteStage(PYRAMID_STAGE_BLOCK, "executioner");
                    break;
                case NPC_SEZZZIZ:
                case NPC_NEKRUM:
                    if (_pyramid.running && _pyramid.stage == PYRAMID_STAGE_ALTAR
                        && AltarCleared(_sezzzizSeen, UnitAlive(_sezzziz), _nekrumSeen, UnitAlive(_nekrum)))
                        CompleteStage(PYRAMID_STAGE_ALTAR, "altar");
                    break;
                default:
                    break;
            }
            if (_director)
                _director->OnCreatureDeath(creature);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            uint32 const before = id < kBossCount ? Slot(id) : uint32(TO_BE_DECIDED);
            // Loading, or a slot's first write (a BossAI's _Reset): the base stores it onto TO_BE_DECIDED and returns
            // false, so nothing below fires from it.
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_GAHZRILLA:
                    if (state == DONE)
                    {
                        // His loot is already filled (Unit::Kill, before JustDied), hard mode list included. A first
                        // write on an unsettled slot is not saved, so save explicitly (RB-2).
                        if (_hardMode)
                        {
                            ForceBossState(BOSS_CREW_AT_THE_POOL, DONE);
                            DungeonKit::LogMechanic(kLogDungeon, "pool", "hardmode-kill");
                        }
                        SaveToDB();
                        break;
                    }
                    ApplyHardModeLoot();        // the pull (BossAI::_Reset cleared the loot mode), a wipe
                    [[fallthrough]];
                case BOSS_VELRATHA:
                    if (PoolWiped(id, before, state))
                        OnPoolWipe(id, before, state);
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
            if (type >= DATA_CREW_MODE_BASE && type < DATA_CREW_MODE_BASE + kCrewCount)
            {
                if (ValidCrewMode(data))
                    SetModeOf(type - DATA_CREW_MODE_BASE, CrewMode(data), "set");
                return;
            }

            switch (type)
            {
                case DATA_PYRAMID:
                case DATA_GAHZRILLA:
                    // Their stock writers (go_troll_cage, the crew scripts, SmartAI 7273) are unbound by the S0 rev.
                    LOG_DEBUG(kLog, "zf instance ignored stock SetData({}, {})", type, data);
                    return;
                case DATA_END_DOOR:
                    SetEndDoor(data, "weegli");
                    return;
                case DATA_PYRAMID_CAGES:
                    OpenCages();
                    return;
                case DATA_BLOOD_PRICE:
                    if (instance->IsHeroic() && _pyramid.stage != PYRAMID_STAGE_DONE && data != _pyramid.bloodPrice)
                    {
                        _pyramid.bloodPrice = data;
                        if (BloodPriceWriteSaves(_pyramid.running))     // a running stage saves its snapshot
                            SaveToDB();
                    }
                    return;
                case DATA_PYRAMID_START:
                    StartStage(data, "owner");
                    return;
                case DATA_PYRAMID_COMPLETE:
                    CompleteStage(data, "owner");
                    return;
                case DATA_PYRAMID_FAIL:
                    WipeStage(data, "owner");
                    return;
                case DATA_CREW_PATH:
                    SetCrewPath(data);
                    return;
                case DATA_CREW_FIGHT:
                    SetCrewFight(data);
                    return;
                case DATA_CREW_LOST:
                    OnCrewDeath(data, "reported");
                    return;
                case DATA_CREW_AT_POOL:
                    if (Slot(BOSS_CREW) == DONE && _crewPath == CREW_PATH_TEST && _crewAtPool != (data ? 1u : 0u))
                    {
                        _crewAtPool = data ? 1 : 0;
                        DungeonKit::LogMechanic(kLogDungeon, "crew", "at-pool", Acore::StringFormat("{}", _crewAtPool));
                        SaveToDB();
                    }
                    return;
                case DATA_GONG_STRUCK:
                    if (data)
                        OnGongStruck(data);
                    return;
                case DATA_GM_STAGE:
                    GmStage(data);
                    return;
                case DATA_GM_CREW_MASK:
                    _pyramid.crewAlive = (data & kCrewAll) | kCrewWeegliBit;
                    _pyramid.snapshot.crewAlive = _pyramid.crewAlive;
                    RestoreCrew("gm");
                    SaveToDB();
                    return;
                case DATA_GM_DOOR:
                    if (data)
                        SetEndDoor(DONE, "gm");
                    else
                        CloseEndDoor();
                    return;
                case DATA_GM_TEST_ARM:
                    GmTestArm();
                    return;
                case DATA_GM_HARD_MODE:
                    if (GmHardModeAllowed(instance->IsHeroic(), Slot(BOSS_GAHZRILLA), data))
                        SetHardMode(data ? 1 : 0, "gm");
                    return;
                default:
                    return;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            if (type >= DATA_CREW_MODE_BASE && type < DATA_CREW_MODE_BASE + kCrewCount)
                return uint32(_crewModes[type - DATA_CREW_MODE_BASE]);

            switch (type)
            {
                case DATA_PYRAMID:
                    return StockPyramidPhase(_pyramid, Slot(BOSS_CREW) == DONE);
                case DATA_GAHZRILLA:
                    return Slot(BOSS_GAHZRILLA) == DONE ? 4 : 0;
                case DATA_END_DOOR:
                    return _endDoor;
                case DATA_PYRAMID_STAGE:
                    return _pyramid.stage;
                case DATA_PYRAMID_RUNNING:
                    return _pyramid.running ? 1 : 0;
                case DATA_PYRAMID_CAGES:
                    return _pyramid.cagesOpen ? 1 : 0;
                case DATA_OFFERINGS:
                    return _pyramid.offerings;
                case DATA_BLOOD_PRICE:
                    return _pyramid.bloodPrice;
                case DATA_CREW_ALIVE:
                    return _pyramid.crewAlive;
                case DATA_CREW_PATH:
                    return _crewPath;
                case DATA_CREW_DONE:
                    return Slot(BOSS_CREW) == DONE ? 1 : 0;
                case DATA_CREW_FIGHT:
                    return Slot(BOSS_CREW);
                case DATA_CREW_AT_POOL:
                    return CrewAtPool();
                case DATA_CREW_AT_END:
                    return _crewAtEnd;
                case DATA_TEST_KEY:
                    return TestAllowed(instance->IsHeroic(), _pyramid.stage, _crewAtEnd, Slot(BOSS_CREW)) ? 1 : 0;
                case DATA_HARD_MODE:
                    return _hardMode;
                case DATA_HARD_MODE_KILLED:
                    return Slot(BOSS_CREW_AT_THE_POOL) == DONE ? 1 : 0;
                case DATA_HARD_MODE_KEY:
                    return HardModeKey(instance->IsHeroic(), _crewPath, Slot(BOSS_CREW), CrewAtPool(),
                        Slot(BOSS_CREW_AT_THE_POOL)) ? 1 : 0;
                default:
                    return 0;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            switch (type)
            {
                case kGuidGahzrilla:
                case kGuidBossBase + BOSS_GAHZRILLA:
                case kGuidBossBase + BOSS_CREW_AT_THE_POOL:
                    return _gahzrilla;
                case kGuidSezzziz:
                    return _sezzziz;
                case kGuidNekrum:
                    return _nekrum;
                case kGuidBossBase + BOSS_PYRAMID:
                    return InstanceScript::GetGuidData(kGuidExecutioner);
                case kGuidBossBase + BOSS_CREW:
                    return InstanceScript::GetGuidData(kGuidCrewBase + CREW_BLY);
                default:
                    return InstanceScript::GetGuidData(type);
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Update
        // ------------------------------------------------------------------------------------------------------------
        void Update(uint32 diff) override
        {
            InstanceScript::Update(diff);
            if (!_settled)
                Settle();
            if (_director)
                _director->OnUpdate(diff);
            events.Update(diff);

            while (uint32 const eventId = events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_PYRAMID_WATCH:
                        WatchPyramid();
                        events.ScheduleEvent(EVENT_PYRAMID_WATCH, Milliseconds(kPyramidWatchMs));
                        break;
                    case EVENT_ALTAR_START:
                        StartStage(PYRAMID_STAGE_ALTAR, "descent");
                        break;
                    case EVENT_DOOR_WATCH:
                        WatchEndDoor();
                        events.ScheduleEvent(EVENT_DOOR_WATCH, Milliseconds(kEndDoorWatchMs));
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
            ZfrSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
                save.states[i] = Slot(i);
            PyramidSnapshot const kept = _pyramid.Saved();
            save.pyramidStage = _pyramid.stage;
            save.cagesOpen = _pyramid.cagesOpen ? 1 : 0;
            save.crewAlive = kept.crewAlive;
            save.offerings = kept.offerings;
            save.bloodPrice = kept.bloodPrice;
            save.crewAtEnd = _crewAtEnd;
            save.crewPath = _crewPath;
            save.endDoor = _endDoor;
            save.hardMode = _hardMode;
            save.crewAtPool = _crewAtPool;
            save.stashLooted = _stashLooted;
            return FormatZfrSave(save);
        }

        // Reads this script's "Z F R" string, or the stock "Z F" one (Map::CreateInstanceData set the
        // completed-encounter mask before Load).
        void Load(char const* in) override
        {
            if (!in || !*in)
                return;

            ZfrSave save;
            if (!ParseZfrSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "zf instance: ignored save '{}'", in);
                return;
            }
            _pyramid = PyramidState{};
            _pyramid.stage = save.pyramidStage;
            _pyramid.cagesOpen = save.cagesOpen != 0;
            _pyramid.crewAlive = save.crewAlive;
            _pyramid.offerings = save.offerings;
            _pyramid.bloodPrice = save.bloodPrice;
            _pyramid.snapshot = _pyramid.Live();
            if (_pyramid.cagesOpen)
                _pyramid.attempted |= 1u << PYRAMID_STAGE_STAIR;
            _crewAtEnd = save.crewAtEnd;
            _crewPath = save.crewPath;
            _endDoor = save.endDoor;
            _hardMode = save.hardMode;
            _crewAtPool = save.crewAtPool;
            _stashLooted = save.stashLooted;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips the switch.
            for (uint32 i = 0; i < kBossCount; ++i)
                InstanceScript::SetBossState(i, EncounterState(save.states[i]));
            // A crew member created before the first Update reads its resting mode already.
            _crewModes.fill(CrewModeFor(Context()));
        }

    private:
        // ------------------------------------------------------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------------------------------------------------------
        uint32 Slot(uint32 id) const
        {
            return SettledSlotState(uint32(GetBossState(id)));
        }

        // A write the instance makes itself (slots 5, 6 and 8, a reopened slot 0).
        void ForceBossState(uint32 id, EncounterState state)
        {
            if (Slot(id) != uint32(state))
                SetBossState(id, state);
        }

        bool UnitAlive(ObjectGuid const& guid) const
        {
            Creature* unit = guid ? instance->GetCreature(guid) : nullptr;
            return unit && unit->IsAlive() && !unit->isDying();
        }

        CrewContext Context() const
        {
            CrewContext c;
            c.stage = _pyramid.stage;
            c.cagesOpen = _pyramid.cagesOpen;
            c.crewSlot = Slot(BOSS_CREW);
            c.path = _crewPath;
            return c;
        }

        uint32 CrewAtPool() const
        {
            if (!_crewAtPool || Slot(BOSS_CREW) != DONE || _crewPath != CREW_PATH_TEST)
                return 0;
            return _pyramid.crewAlive & kCrewAll;
        }

        bool Heroic() const
        {
            return instance->IsHeroic();
        }

        // The first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED through
        // the base's loading branch, so the first live write saves and runs the switch. Every event restarts here
        // (RB-2): the Pyramid's director for the stage in play (idle), the crew's modes and restore, the door watch.
        void Settle()
        {
            _settled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                uint32 const state = GetBossState(i);
                if (SettledSlotState(state) != state)
                    InstanceScript::SetBossState(i, EncounterState(SettledSlotState(state)));
            }
            if (_pyramid.stage >= PYRAMID_STAGE_BLOCK && _pyramid.stage <= PYRAMID_STAGE_ALTAR)
                EnterStage(_pyramid.stage);
            // R-1-FW M2: a save with Velratha DONE and Gahz'rilla not reopened slot 0 (SanitizeZfrSave); her corpse
            // loaded with its respawn time, so she stands up for the next strike.
            if (Slot(BOSS_VELRATHA) != DONE)
                RestoreVelratha("load");
            ApplyCrewModes("load");
            RestoreCrew("load");
            events.ScheduleEvent(EVENT_PYRAMID_WATCH, Milliseconds(kPyramidWatchMs));
            if (Slot(BOSS_CREW) == DONE)
            {
                _crewDoneMs = kEndDoorFallbackMs;       // a reload: the door opens at the first watch
                events.ScheduleEvent(EVENT_DOOR_WATCH, Milliseconds(kEndDoorWatchMs));
            }
            DungeonKit::LogMechanic(kLogDungeon, "instance", "settle", Acore::StringFormat(
                "stage={} cages={} crew={} path={} door={} hardmode={}", kPyramidStageNames[_pyramid.stage],
                _pyramid.cagesOpen ? 1 : 0, _pyramid.crewAlive, _crewPath, _endDoor, _hardMode));
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Pyramid's stage machine
        // ------------------------------------------------------------------------------------------------------------

        // The stage `stage` comes into play (idle): its director is made and waits.
        void EnterStage(uint32 stage)
        {
            if (_director && _directorStage == stage)
            {
                _director->OnWait();
                return;
            }
            _director = CreatePyramidStage(stage, this);
            _directorStage = stage;
            if (_director)
                _director->OnWait();
        }

        void StartStage(uint32 stage, char const* how)
        {
            PyramidVerdict const verdict = PyramidStart(_pyramid, stage);
            if (verdict == PyramidVerdict::Refused)
            {
                LOG_DEBUG(kLog, "zf instance pyramid start {} refused ({}; stage {} running {} cages {})", stage, how,
                    _pyramid.stage, _pyramid.running ? 1 : 0, _pyramid.cagesOpen ? 1 : 0);
                return;
            }
            bool const restart = verdict == PyramidVerdict::Restarted;
            _landingMs = 0;
            ForceBossState(BOSS_PYRAMID, IN_PROGRESS);
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", restart ? "restart" : "start", Acore::StringFormat(
                "stage={} how={} crew={} offerings={} bloodprice={}", kPyramidStageNames[stage], how,
                _pyramid.crewAlive, _pyramid.offerings, _pyramid.bloodPrice));
            if (!_director || _directorStage != stage)
            {
                _director = CreatePyramidStage(stage, this);
                _directorStage = stage;
            }
            if (_director)
                _director->OnStart(restart);
            // R-1-FW m3: a member that fell while no stage ran kept its bit; it stands up for the stage.
            RestoreCrew("start");
            ApplyCrewModes("stage");
            NotifyCrew(ACTION_ZF_PYRAMID_STAGE);
            ActionTo(GetCreature(kGuidExecutioner), ACTION_ZF_PYRAMID_STAGE);
        }

        void CompleteStage(uint32 stage, char const* how)
        {
            if (PyramidComplete(_pyramid, stage) == PyramidVerdict::Refused)
            {
                LOG_DEBUG(kLog, "zf instance pyramid complete {} refused ({})", stage, how);
                return;
            }
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", "won", Acore::StringFormat("stage={} how={} crew={}",
                kPyramidStageNames[stage], how, _pyramid.crewAlive));
            if (_director)
                _director->OnEnd(true);
            _director.reset();
            _directorStage = 0;

            switch (stage)
            {
                case PYRAMID_STAGE_BLOCK:
                    ForceBossState(BOSS_PYRAMID, NOT_STARTED);      // idle until the cages open
                    ShutCages();                                    // R-1-FW M3: any cage left open is usable again
                    EnterStage(PYRAMID_STAGE_STAIR);
                    break;
                case PYRAMID_STAGE_STAIR:
                    ForceBossState(BOSS_PYRAMID, NOT_STARTED);
                    _sezzziz.Clear();
                    _nekrum.Clear();
                    _sezzzizSeen = false;
                    _nekrumSeen = false;
                    EnterStage(PYRAMID_STAGE_ALTAR);
                    events.ScheduleEvent(EVENT_ALTAR_START, Milliseconds(kAltarDelayMs));
                    break;
                case PYRAMID_STAGE_ALTAR:
                    OnPyramidDone();
                    break;
                default:
                    break;
            }
            ApplyCrewModes("stage");
            NotifyCrew(ACTION_ZF_PYRAMID_STAGE);
            ActionTo(GetCreature(kGuidExecutioner), ACTION_ZF_PYRAMID_STAGE);
            SaveToDB();
        }

        void WipeStage(uint32 stage, char const* how)
        {
            if (PyramidWipe(_pyramid, stage) == PyramidVerdict::Refused)
                return;
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", "wipe", Acore::StringFormat(
                "stage={} how={} crew={} offerings={} bloodprice={}", kPyramidStageNames[stage], how,
                _pyramid.crewAlive, _pyramid.offerings, _pyramid.bloodPrice));
            if (_director)
                _director->OnEnd(false);
            ForceBossState(BOSS_PYRAMID, NOT_STARTED);
            _landingMs = 0;
            if (stage == PYRAMID_STAGE_ALTAR)
            {
                _sezzziz.Clear();
                _nekrum.Clear();
                _sezzzizSeen = false;
                _nekrumSeen = false;
            }
            if (stage == PYRAMID_STAGE_BLOCK)
                if (Creature* executioner = GetCreature(kGuidExecutioner))
                    if (executioner->IsAlive() && executioner->IsEngaged() && executioner->IsAIEnabled
                        && executioner->AI())
                        executioner->AI()->EnterEvadeMode();
            RestoreCrew("wipe");
            ApplyCrewModes("wipe");
            NotifyCrew(ACTION_ZF_PYRAMID_STAGE);
            ActionTo(GetCreature(kGuidExecutioner), ACTION_ZF_PYRAMID_STAGE);
            EnterStage(stage);
            SaveToDB();
        }

        void OpenCages()
        {
            if (!PyramidOpenCages(_pyramid))
            {
                LOG_DEBUG(kLog, "zf instance cages ignored (stage {} cages {})", _pyramid.stage,
                    _pyramid.cagesOpen ? 1 : 0);
                return;
            }
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", "cages", "open");
            // R-1-B nt-1: one cage opened (a bot's UseGO, a click) opens all five, as the key's spell does; each one's
            // OnStateChanged then finds the cages open and keeps it so.
            for (ObjectGuid const& guid : _cages)
                if (GameObject* cage = guid ? instance->GetGameObject(guid) : nullptr)
                    if (cage->getLootState() == GO_READY)
                        cage->UseDoorOrButton();
            StartStage(PYRAMID_STAGE_STAIR, "cages");
            SaveToDB();
        }

        void ShutCages()
        {
            for (ObjectGuid const& guid : _cages)
                go_zf_troll_cage::Shut(guid ? instance->GetGameObject(guid) : nullptr);
        }

        // Stage 3 is won: slot 5 DONE with its credit, the crew's mask kept for the Test, and every member stands up
        // at the gather spot for Bly's fight (section 7 #12 A).
        void OnPyramidDone()
        {
            _crewAtEnd = _pyramid.crewAlive & kCrewAll;
            _pyramid.crewAlive = kCrewAll;
            _pyramid.snapshot = _pyramid.Live();
            ForceBossState(BOSS_PYRAMID, DONE);
            Unit* source = GetCreature(kGuidCrewBase + CREW_BLY);
            DungeonKit::CreditEncounterBySpell(instance, SPELL_ZF_PYRAMID_CREDIT, source, kLogDungeon, "pyramid");
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", "done", Acore::StringFormat("crew={} testkey={}",
                _crewAtEnd, TestAllowed(Heroic(), _pyramid.stage, _crewAtEnd, Slot(BOSS_CREW)) ? 1 : 0));
            RestoreCrew("pyramid-done");
        }

        // Every second: a running stage with no living player in the Pyramid region is a wipe; stage 2 waiting after a
        // wipe or a reload restarts after kStairRestartMs of a living player on the landing.
        void WatchPyramid()
        {
            if (_pyramid.running)
            {
                uint32 living = 0;
                for (MapReference const& ref : instance->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (player && player->IsAlive() && !player->IsGameMaster()
                        && InPyramidRegion({ player->GetPositionX(), player->GetPositionY() }))
                        ++living;
                }
                if (PyramidWiped(_pyramid.running, living))
                    WipeStage(_pyramid.stage, "region");
                return;
            }
            if (!StairRestartWaits(_pyramid))
            {
                _landingMs = 0;
                return;
            }
            Arena const landing = LandingArena();
            bool onLanding = false;
            for (MapReference const& ref : instance->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (player && player->IsAlive() && !player->IsGameMaster()
                    && landing.Contains({ player->GetPositionX(), player->GetPositionY() }, player->GetPositionZ()))
                {
                    onLanding = true;
                    break;
                }
            }
            _landingMs = onLanding ? _landingMs + kPyramidWatchMs : 0;
            if (_landingMs >= kStairRestartMs)
                StartStage(PYRAMID_STAGE_STAIR, "landing");
        }

        // L9: the Executioner loads dead (his corpse kept) with the Block not won in the save: settle it quietly.
        void SettleDeadExecutioner(Creature* creature)
        {
            if (creature->IsAlive() || creature->GetRespawnTime() <= GameTime::GetGameTime().count())
                return;
            if (_pyramid.stage > PYRAMID_STAGE_BLOCK)
                return;
            _pyramid.stage = PYRAMID_STAGE_STAIR;
            _pyramid.running = false;
            _pyramid.snapshot = _pyramid.Live();
            DungeonKit::LogMechanic(kLogDungeon, "instance", "dead-load", "executioner: the Block counts as won");
            if (_settled)
                EnterStage(PYRAMID_STAGE_STAIR);
        }

        void GmStage(uint32 stage)
        {
            if (stage > PYRAMID_STAGE_DONE)
                return;
            if (_director)
                _director->OnEnd(false);
            _director.reset();
            _directorStage = 0;
            events.CancelEvent(EVENT_ALTAR_START);
            _pyramid.running = false;
            _pyramid.stage = stage;
            _pyramid.cagesOpen = stage >= PYRAMID_STAGE_STAIR;
            _pyramid.attempted = 0;
            _pyramid.snapshot = _pyramid.Live();
            _landingMs = 0;
            if (stage == PYRAMID_STAGE_DONE)
            {
                if (Slot(BOSS_PYRAMID) != DONE)
                {
                    _crewAtEnd = _pyramid.crewAlive & kCrewAll;
                    _pyramid.crewAlive = kCrewAll;
                    ForceBossState(BOSS_PYRAMID, DONE);
                }
            }
            else
            {
                if (Slot(BOSS_PYRAMID) != NOT_STARTED)
                    ForceBossState(BOSS_PYRAMID, NOT_STARTED);
                _crewAtEnd = 0;
                if (stage >= PYRAMID_STAGE_BLOCK)
                    EnterStage(stage);
            }
            DungeonKit::LogMechanic(kLogDungeon, "pyramid", "gm-stage", kPyramidStageNames[stage]);
            RestoreCrew("gm");
            ApplyCrewModes("gm");
            NotifyCrew(ACTION_ZF_PYRAMID_STAGE);
            SaveToDB();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The crew
        // ------------------------------------------------------------------------------------------------------------
        void OnCrewDeath(uint32 member, char const* how)
        {
            if (member >= kCrewCount)
                return;
            if (_pyramid.stage != PYRAMID_STAGE_DONE)
            {
                CrewLoss const loss = PyramidCrewLost(_pyramid, member, Heroic());
                if (!loss.counted)
                    return;
                DungeonKit::LogMechanic(kLogDungeon, "crew", "lost", Acore::StringFormat(
                    "{} how={} stage={} offerings+{} bloodprice+{} crew={}", kCrewNames[member], how,
                    kPyramidStageNames[_pyramid.stage], loss.offerings, loss.bloodPrice, _pyramid.crewAlive));
                SaveToDB();
                return;
            }

            uint32 const crewSlot = Slot(BOSS_CREW);
            if (crewSlot == IN_PROGRESS)
            {
                if (CrewFightOverByDeaths(crewSlot, _crewPath, FightersAlive()))
                    FinishCrewFight("deaths");
                return;
            }
            if (crewSlot == DONE && _crewPath == CREW_PATH_TEST && (_pyramid.crewAlive & CrewBit(member)))
            {
                // At the pool: for this attempt only (section 7 #16 A); a pool wipe brings all five back.
                _pyramid.crewAlive &= ~CrewBit(member);
                DungeonKit::LogMechanic(kLogDungeon, "crew", "pool-death", Acore::StringFormat("{} crew={}",
                    kCrewNames[member], _pyramid.crewAlive));
                SaveToDB();
            }
        }

        uint32 FightersAlive() const
        {
            uint32 mask = 0;
            for (uint32 m = 0; m < kCrewCount; ++m)
                if (Creature* unit = instance->GetCreature(InstanceScript::GetGuidData(kGuidCrewBase + m)))
                    if (unit->IsAlive() && !unit->isDying())
                        mask |= CrewBit(m);
            return mask;
        }

        void SetModeOf(uint32 member, CrewMode mode, char const* how, bool notify = true)
        {
            if (member >= kCrewCount || _crewModes[member] == mode)
                return;
            LOG_INFO(kLog, "{} crew {} {} {} ({})", kLogDungeon, kCrewEntries[member],
                kCrewModeNames[uint32(_crewModes[member])], kCrewModeNames[uint32(mode)], how);
            _crewModes[member] = mode;
            if (notify)
                ActionTo(CrewCreature(this, member), ACTION_ZF_CREW_MODE);
        }

        // Every member's resting mode from the run's state (a create reads it; a transient mode a WP set live stays
        // until the next transition calls this).
        void ApplyCrewModes(char const* how)
        {
            CrewMode const mode = CrewModeFor(Context());
            for (uint32 m = 0; m < kCrewCount; ++m)
                SetModeOf(m, mode, how);
        }

        // Every member that must stand and is dead or gone comes back (RB-20: a dead DB spawn with dynamic spawning
        // leaves the store, so by spawn id; a respawn time in the future means dead).
        void RestoreCrew(char const* how)
        {
            CrewContext const c = Context();
            time_t const now = GameTime::GetGameTime().count();
            for (uint32 m = 0; m < kCrewCount; ++m)
            {
                if (!CrewMemberStands(c, _pyramid.crewAlive, m))
                    continue;
                Creature* unit = CrewCreature(this, m);
                if (unit)
                {
                    if (unit->IsAlive())
                        continue;
                    unit->Respawn(true);
                }
                else if (instance->GetCreatureRespawnTime(kCrewSpawnIds[m]) > now)
                    instance->ForceCreatureRespawn(kCrewSpawnIds[m]);
                else
                    continue;
                DungeonKit::LogMechanic(kLogDungeon, "crew", "restored", Acore::StringFormat("{} how={}",
                    kCrewNames[m], how));
            }
        }

        void NotifyCrew(int32 action)
        {
            for (uint32 m = 0; m < kCrewCount; ++m)
                ActionTo(CrewCreature(this, m), action);
        }

        static void ActionTo(Creature* unit, int32 action)
        {
            if (unit && unit->IsAlive() && unit->IsAIEnabled && unit->AI())
                unit->AI()->DoAction(action);
        }

        void SetCrewPath(uint32 path)
        {
            if (!CrewPathAllowed(path, Heroic(), _pyramid.stage, _crewAtEnd, Slot(BOSS_CREW)))
            {
                LOG_INFO(kLog, "{} crew path {} refused (stage {} crew at end {} slot 6 {} heroic {})", kLogDungeon,
                    path, _pyramid.stage, _crewAtEnd, Slot(BOSS_CREW), Heroic() ? 1 : 0);
                return;
            }
            if (path == _crewPath)
                return;
            _crewPath = path;
            DungeonKit::LogMechanic(kLogDungeon, "crew", "path", path == CREW_PATH_TEST ? "test"
                : path == CREW_PATH_BETRAYAL ? "betrayal" : "open");
            // Section 7 #12 A: a member that fell after the Pyramid (a stray pull at the gather spot) stands up for
            // the fight.
            if (path != CREW_PATH_OPEN)
                RestoreCrew("path");
        }

        // D5: IN_PROGRESS at the pull, NOT_STARTED (or FAIL) at a wipe, DONE at the end.
        void SetCrewFight(uint32 state)
        {
            uint32 const crewSlot = Slot(BOSS_CREW);
            switch (state)
            {
                case IN_PROGRESS:
                    if (!CrewFightStartAllowed(_pyramid.stage, _crewPath, crewSlot))
                        return;
                    ForceBossState(BOSS_CREW, IN_PROGRESS);
                    DungeonKit::LogMechanic(kLogDungeon, "crew", "fight", Acore::StringFormat("start path={}",
                        _crewPath));
                    for (uint32 m = 0; m < kCrewCount; ++m)
                        if (CrewBit(m) & kCrewFighters)
                            SetModeOf(m, CrewMode::Boss, "fight");
                    NotifyCrew(ACTION_ZF_CREW_FIGHT);
                    break;
                case NOT_STARTED:
                case FAIL:
                    if (crewSlot != IN_PROGRESS)
                        return;
                    ForceBossState(BOSS_CREW, NOT_STARTED);
                    _crewPath = CREW_PATH_OPEN;     // offered again (section 7 #18 A)
                    _pyramid.crewAlive = kCrewAll;
                    DungeonKit::LogMechanic(kLogDungeon, "crew", "fight", "wipe");
                    RestoreCrew("crew-wipe");
                    ApplyCrewModes("crew-wipe");
                    NotifyCrew(ACTION_ZF_CREW_FIGHT);
                    SaveToDB();
                    break;
                case DONE:
                    if (crewSlot == IN_PROGRESS)
                        FinishCrewFight("d5");
                    break;
                default:
                    break;
            }
        }

        // The crew's fight is over (section 7 #13 A, #14 A, #19 A): slot 6 DONE with its credit; the betrayal's crew
        // are Gone (Weegli leaves for good), the Test's go to the pool; the door watch starts (Weegli blows it, or the
        // fallback does).
        void FinishCrewFight(char const* how)
        {
            ForceBossState(BOSS_CREW, DONE);
            Unit* source = GetCreature(kGuidCrewBase + CREW_BLY);
            DungeonKit::CreditEncounterBySpell(instance, SPELL_ZF_CREW_CREDIT, source, kLogDungeon, "crew");
            if (_crewPath == CREW_PATH_TEST)
                _pyramid.crewAlive = kCrewAll;
            else
                _pyramid.crewAlive = 0;
            DungeonKit::LogMechanic(kLogDungeon, "crew", "fight", Acore::StringFormat("done how={} path={}", how,
                _crewPath == CREW_PATH_TEST ? "test" : "betrayal"));
            ApplyCrewModes("crew-done");
            // R-1-FW m1: a fighter killed past the yield floor stands up (Init places it at the pool).
            if (_crewPath == CREW_PATH_TEST)
                RestoreCrew("crew-done");
            NotifyCrew(ACTION_ZF_CREW_FIGHT);
            _crewDoneMs = 0;
            events.ScheduleEvent(EVENT_DOOR_WATCH, Milliseconds(kEndDoorWatchMs));
            SaveToDB();
        }

        void GmTestArm()
        {
            if (!Heroic() || Slot(BOSS_CREW) == DONE || Slot(BOSS_CREW) == IN_PROGRESS)
            {
                LOG_INFO(kLog, "{} instance test arm refused (heroic {} slot 6 {})", kLogDungeon, Heroic() ? 1 : 0,
                    Slot(BOSS_CREW));
                return;
            }
            _pyramid.crewAlive = kCrewAll;
            if (_pyramid.stage != PYRAMID_STAGE_DONE)
                GmStage(PYRAMID_STAGE_DONE);
            _crewAtEnd = kCrewAll;
            _crewPath = CREW_PATH_OPEN;
            DungeonKit::LogMechanic(kLogDungeon, "crew", "test-armed", "gm");
            RestoreCrew("gm");
            SaveToDB();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The End Door (section 7 #13 A)
        // ------------------------------------------------------------------------------------------------------------
        void SetEndDoor(uint32 state, char const* how)
        {
            switch (state)
            {
                case IN_PROGRESS:       // Weegli on his way: not saved (stock)
                    if (_endDoor == NOT_STARTED)
                        _endDoor = IN_PROGRESS;
                    break;
                case NOT_STARTED:
                    if (_endDoor == IN_PROGRESS)
                        _endDoor = NOT_STARTED;
                    break;
                case DONE:
                    if (_endDoor != DONE)
                    {
                        _endDoor = DONE;
                        DungeonKit::LogMechanic(kLogDungeon, "instance", "door", Acore::StringFormat("blown how={}",
                            how));
                        SaveToDB();
                    }
                    OpenEndDoor(GetGameObject(kGuidEndDoor));
                    break;
                default:
                    break;
            }
        }

        // Stock: the blown look (GO_STATE_ACTIVE_ALTERNATIVE). Not selectable (set at create too), so a click can
        // neither open nor shut it (the watch reopens one a GM shut while slot 6 is DONE).
        static void OpenEndDoor(GameObject* door)
        {
            if (!door)
                return;
            door->SetGoState(GO_STATE_ACTIVE_ALTERNATIVE);
            door->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        }

        void CloseEndDoor()
        {
            _endDoor = NOT_STARTED;
            if (GameObject* door = GetGameObject(kGuidEndDoor))
            {
                door->SetGoState(GO_STATE_READY);      // still not selectable (R-1-FW m2)
            }
            _crewDoneMs = 0;
            DungeonKit::LogMechanic(kLogDungeon, "instance", "door", "shut (gm)");
            SaveToDB();
        }

        void WatchEndDoor()
        {
            if (Slot(BOSS_CREW) != DONE)
                return;
            _crewDoneMs += kEndDoorWatchMs;
            if (EndDoorFallbackDue(Slot(BOSS_CREW), _endDoor, _crewDoneMs))
                SetEndDoor(DONE, "fallback");
            if (_endDoor == DONE)
                if (GameObject* door = GetGameObject(kGuidEndDoor))
                    if (door->GetGoState() == GO_STATE_READY)
                        OpenEndDoor(door);
            WatchStash();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The crew's stash (section 7 #19 A; D5 summons it at the fight's end): an emptied chest (consumable, so not
        // spawned once looted) is saved as looted; a chest lost to a reload or a restart is summoned again.
        // ------------------------------------------------------------------------------------------------------------
        void WatchStash()
        {
            if (_stashLooted)
                return;
            GameObject* chest = _stash ? instance->GetGameObject(_stash) : nullptr;
            if (chest && !chest->isSpawned())
            {
                _stashLooted = 1;
                _stash.Clear();
                DungeonKit::LogMechanic(kLogDungeon, "crew", "stash", "emptied");
                SaveToDB();
                return;
            }
            Point3 const& at = ZfCrewFight::kStashSpot;
            if (!StashRestoreDue(Slot(BOSS_CREW), _stashLooted, chest != nullptr, instance->IsGridLoaded(at.x, at.y),
                _crewDoneMs))
                return;
            float z = instance->GetHeight(at.x, at.y, at.z + 2.f);
            if (z <= INVALID_HEIGHT)
                z = at.z;
            float const half = at.o / 2.f;
            uint32 const entry = ZfCrewFight::StashEntry(Heroic());
            if (GameObject* stash = instance->SummonGameObject(entry, at.x, at.y, z, at.o, 0.f, 0.f, std::sin(half),
                std::cos(half), DAY))
            {
                _stash = stash->GetGUID();
                DungeonKit::LogMechanic(kLogDungeon, "crew", "stash", Acore::StringFormat("restored entry={}", entry));
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // The pool and the hard mode (section 3.2 items 6 and 7)
        // ------------------------------------------------------------------------------------------------------------

        // D7's Velratha strikes the gong (GZ10): the hard mode arms on its key, then Gahz'rilla rises (the instance's
        // summon at the stock point; D7 walks him ashore).
        // F-1 MA-1: `value` is 2 when Velratha's pull built the hard mode packages, 1 when it did not; only 2 arms.
        void OnGongStruck(uint32 value)
        {
            if (Slot(BOSS_GAHZRILLA) == DONE)
                return;
            bool const allowed = HardModeArmAllowed(Heroic(), _crewPath, Slot(BOSS_CREW), CrewAtPool(),
                Slot(BOSS_GAHZRILLA), Slot(BOSS_CREW_AT_THE_POOL));
            if (!_hardMode && GongArmsHardMode(value, allowed))
                SetHardMode(1, "gong");
            else if (!_hardMode && allowed)
                DungeonKit::LogMechanic(kLogDungeon, "pool", "hardmode-not-armed",
                    "the key opened after Velratha's pull (no packages)");
            if (UnitAlive(_gahzrilla))
                return;
            Position const at(kGahzrillaSummon.x, kGahzrillaSummon.y, kGahzrillaSummon.z, kGahzrillaSummon.o);
            if (TempSummon* gahzrilla = instance->SummonCreature(NPC_GAHZRILLA, at))
            {
                _gahzrilla = gahzrilla->GetGUID();
                ApplyHardModeLoot(gahzrilla);
                DungeonKit::LogMechanic(kLogDungeon, "pool", "gahzrilla", Acore::StringFormat("summoned hardmode={}",
                    _hardMode));
            }
        }

        void SetHardMode(uint32 value, char const* how)
        {
            if (value == _hardMode)
                return;
            _hardMode = value;
            ApplyHardModeLoot();
            SaveToDB();
            DungeonKit::LogMechanic(kLogDungeon, "pool", Acore::StringFormat("hardmode={}", value).c_str(), how);
            if (value)
            {
                ActionTo(GetCreature(kGuidBossBase + BOSS_VELRATHA), ACTION_ZF_HARD_MODE_ARMED);
                ActionTo(_gahzrilla ? instance->GetCreature(_gahzrilla) : nullptr, ACTION_ZF_HARD_MODE_ARMED);
            }
        }

        // Item variants IV7 (the Deadmines pattern): Gahz'rilla's heroic lootid holds the hard mode list at LootMode 2;
        // the bit rides him while the flag is lit and he is not dead (rule 1: at the trigger and the pull, never in
        // JustDied).
        void ApplyHardModeLoot(Creature* gahzrilla = nullptr)
        {
            if (!gahzrilla && _gahzrilla)
                gahzrilla = instance->GetCreature(_gahzrilla);
            if (gahzrilla)
                DungeonKit::SetHardModeLoot(gahzrilla, HardModeLootLit(_hardMode, Slot(BOSS_GAHZRILLA)));
        }

        // A pool attempt lost (section 7 #16 A, #43 h A): the crew at the pool all come back; Gahz'rilla's wipe after
        // Velratha died reopens her slot and brings her body back; a Gahz'rilla left standing out of combat sinks.
        void OnPoolWipe(uint32 slot, uint32 before, uint32 now)
        {
            DungeonKit::LogMechanic(kLogDungeon, "pool", "wipe", Acore::StringFormat("slot={} hardmode={}", slot,
                _hardMode));
            if (PoolWipeReopensVelratha(slot, before, now, Slot(BOSS_VELRATHA)))
            {
                ForceBossState(BOSS_VELRATHA, NOT_STARTED);
                RestoreVelratha("pool-wipe");
            }
            // Either slot: a Gahz'rilla risen but never pulled must not wait in the pool for the next strike.
            if (Creature* gahzrilla = _gahzrilla ? instance->GetCreature(_gahzrilla) : nullptr)
                if (gahzrilla->IsAlive() && !gahzrilla->IsEngaged())
                    gahzrilla->DespawnOrUnsummon(1s);
            if (Slot(BOSS_CREW) == DONE && _crewPath == CREW_PATH_TEST)
            {
                _pyramid.crewAlive = kCrewAll;
                RestoreCrew("pool-wipe");
                ApplyCrewModes("pool-wipe");
                NotifyCrew(ACTION_ZF_POOL_RESET);
            }
            SaveToDB();
        }

        // Velratha's body back (RB-20: by spawn id when the dead DB spawn left the store).
        void RestoreVelratha(char const* how)
        {
            Creature* velratha = GetCreature(kGuidBossBase + BOSS_VELRATHA);
            if (velratha)
            {
                if (velratha->IsAlive())
                    return;
                velratha->Respawn(true);
            }
            else if (instance->GetCreatureRespawnTime(kSpawnVelratha) > GameTime::GetGameTime().count())
                instance->ForceCreatureRespawn(kSpawnVelratha);
            else
                return;
            DungeonKit::LogMechanic(kLogDungeon, "pool", "velratha-restored", how);
        }

        EventMap events;
        bool _settled = false;

        // Saved run data
        PyramidState _pyramid;
        uint32 _crewAtEnd = 0;
        uint32 _crewPath = CREW_PATH_OPEN;
        uint32 _endDoor = NOT_STARTED;
        uint32 _hardMode = 0;
        uint32 _crewAtPool = 0;
        uint32 _stashLooted = 0;

        // Per attempt (rebuilt after a reload)
        std::array<CrewMode, kCrewCount> _crewModes{};
        std::unique_ptr<PyramidStageDirector> _director;
        uint32 _directorStage = 0;
        uint32 _landingMs = 0;
        uint32 _crewDoneMs = 0;
        ObjectGuid _gahzrilla;
        ObjectGuid _sezzziz;
        ObjectGuid _nekrum;
        std::array<ObjectGuid, 5> _cages{};
        ObjectGuid _stash;
        bool _sezzzizSeen = false;
        bool _nekrumSeen = false;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_zulfarrak_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_zulfarrak_rework()
{
    new instance_zulfarrak_rework();
    RegisterDungeonReworkGameObjectAI(go_zf_troll_cage, ZulFarrakRework::kInstanceScriptName);
}
