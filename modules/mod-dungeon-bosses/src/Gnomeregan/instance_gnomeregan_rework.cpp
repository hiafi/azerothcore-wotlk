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

// The Gnomeregan build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_gnomeregan` (section 7 #2 A): modules load after the core scripts, and a database-bound script registered
// later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 90's instance_template row
// is untouched and the stock InstanceMapScript is replaced at load. The other scripts the stock AddSC_gnomeregan
// registers (npc_kernobee 7850 with quest 2904, spell_gnomeregan_radiation_bolt 9771) stay registered and keep working:
// npc_kernobee's GetGnomereganAI only asks the map's script name (gnomeregan.h:25-30) and reads no instance data.
//
// It replaces src/server/scripts/EasternKingdoms/Gnomeregan/instance_gnomeregan.cpp at aa32e0dde (the upstream merge
// 20260920; untouched), and mirrors none of its code: the stock data id 0 (TYPE_GRUBBIS) keeps its number and answers
// NOT_STARTED (Emi, its only reader, is gone: ruling 2); the stock "G N O <n>" save loads as a fresh run (its one field
// was Grubbis's); the four doors the stock instance saved are this script's now (the Workshop Door and the Final
// Chamber below; the Cave Ins stay shut as scenery, section 7 #18 A). Stock authors: Yehonal, Hanabi, Kargatum,
// Francesco Borzi, Skjalf, Kitzunu, Jelle Meeus (FACTS-STOCK 1.4). Each upstream merge re-diffs the stock file.
//
// What is new: 7 boss slots (slot = DungeonEncounter bit; slot 6 the hard mode kill); the Workshop Door (section 7 #15
// A, #16 B: sealed, unlocked once Electrocutioner is DONE, open once the Alert System is DONE or a player opens it);
// the Final Chamber held open (section 7 #17 A); the End NPCs at Electrocutioner's and Thermaplugg's DONE on normal and
// after a reload (section 7 #24 A); Crowd Pummeler's chest at his DONE and after a reload until looted (section 7 #38 k
// A); the hard mode flag (the console's), the pull's verdict (RB-24), slot 6 and the loot bit; the run's Finder
// section; the "GNR" save with the stock "G N O" reader.

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "EventMap.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "Group.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "LFGMgr.h"
#include "Log.h"
#include "Map.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <array>
#include <cmath>

using namespace GnomereganRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");
static_assert(kMapGnomeregan == MAP_GNOMEREGAN, "map 90");
static_assert(kGoStateActive == GO_STATE_ACTIVE && kGoStateReady == GO_STATE_READY, "GameObjectData.h GOState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // The spawned bosses (never summoned: cpp-scripts.md, the ObjectData pitfall) and the two doors. The exiles share
    // one entry with the quests WP's static spawns, the chest is a summon: both tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_ALERT_SYSTEM,     kGuidBossBase + BOSS_ALERT_SYSTEM       },
        { NPC_VISCOUS_FALLOUT,  kGuidBossBase + BOSS_VISCOUS_FALLOUT    },
        { NPC_TECHBOT,          kGuidBossBase + BOSS_TECHBOT            },
        { NPC_ELECTROCUTIONER,  kGuidBossBase + BOSS_ELECTROCUTIONER    },
        { NPC_CROWD_PUMMELER,   kGuidBossBase + BOSS_CROWD_PUMMELER     },
        { NPC_THERMAPLUGG,      kGuidBossBase + BOSS_THERMAPLUGG        },
        { 0,                    0                                       }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_WORKSHOP_DOOR,         kGuidWorkshopDoor   },
        { GO_FINAL_CHAMBER_DOOR,    kGuidFinalChamber   },
        { 0,                        0                   }
    };

    enum GnomereganInstanceEvents
    {
        EVENT_WATCH = 1,    // every kWatchMs: the doors' latches, the chest, the End NPCs
    };

    uint32 constexpr kWatchMs = 2000;
    uint32 constexpr kChestRespawnSecs = DAY;   // a summoned chest's respawn time (it is consumed when emptied)

    // Open, latched and not selectable (a click can neither shut nor reopen it; the SM / ZF pattern). The loot state
    // is set last and only when it changes something: SetLootState calls the door AI, which may call back here
    // (R-1-FW B1, OpenLatchSetsLootState).
    void OpenLatched(GameObject* go)
    {
        if (!go)
            return;
        go->SetGameObjectFlag(GO_FLAG_IN_USE);
        go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (go->GetGoState() != GO_STATE_ACTIVE)
            go->SetGoState(GO_STATE_ACTIVE);
        if (OpenLatchSetsLootState(go->GetGoState() == GO_STATE_ACTIVE, go->getLootState() == GO_ACTIVATED))
            go->SetLootState(GO_ACTIVATED);
    }

    // Shut by hand (GO_STATE_READY, GO_READY), never through ResetDoorOrButton: its GO_JUST_DEACTIVATED path despawns a
    // door with its respawn delay (LESSONS A.2 #13).
    void ShutDoor(GameObject* go, bool selectable)
    {
        if (!go)
            return;
        if (go->GetGoState() != GO_STATE_READY)
            go->SetGoState(GO_STATE_READY);
        if (go->getLootState() != GO_READY)
            go->SetLootState(GO_READY);
        go->RemoveGameObjectFlag(GO_FLAG_IN_USE);
        if (selectable)
            go->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else
            go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }
}

// The Workshop Door 90858 (bound by the S0 rev, keyless: lock 92 and GO_FLAG_LOCKED cleared). Section 7 #15 A: once
// Electrocutioner is DONE anyone may open it (the instance makes it selectable); the open counts as the door's open
// state (saved, latched). A use while sealed (a GM's activate, a script) is refused: shut again on the next update.
struct go_gnomer_workshop_door : public GameObjectAI
{
    explicit go_gnomer_workshop_door(GameObject* go) : GameObjectAI(go) { }

    void OnStateChanged(uint32 state, Unit* /*unit*/) override
    {
        if (state != GO_ACTIVATED)
            return;
        InstanceScript* instance = me->GetInstanceScript();
        // Already open: this is the instance's own latch (R-1-FW B1), nothing to tell it.
        if (!instance || !WorkshopDoorUseForwarded(instance->GetData(DATA_WORKSHOP_DOOR)))
            return;
        instance->SetData(DATA_WORKSHOP_DOOR, WORKSHOP_DOOR_OPEN);
        _shutPending = instance->GetData(DATA_WORKSHOP_DOOR) != WORKSHOP_DOOR_OPEN;
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!_shutPending)
            return;
        _shutPending = false;
        ShutDoor(me, false);
        DungeonKit::LogMechanic(kLogDungeon, "instance", "door-refused", "shut again (sealed)");
    }

private:
    bool _shutPending = false;
};

class instance_gnomeregan_rework : public InstanceMapScript
{
public:
    instance_gnomeregan_rework() : InstanceMapScript(kInstanceScriptName, MAP_GNOMEREGAN) { }

    struct instance_gnomeregan_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_gnomeregan_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadObjectData(creatureData, gameObjectData);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Players: the run's Finder section (the first LFG group to enter decides; saved)
        // ------------------------------------------------------------------------------------------------------------
        void OnPlayerEnter(Player* player) override
        {
            InstanceScript::OnPlayerEnter(player);
            if (_section || !player)
                return;
            Group* group = player->GetGroup();
            if (!group || !group->isLFGGroup())
                return;
            uint32 const lfgDungeon = sLFGMgr->GetDungeon(group->GetGUID());
            if (uint32 const section = SectionOfLfgDungeon(lfgDungeon))
            {
                _section = section;
                DungeonKit::LogMechanic(kLogDungeon, "instance", "section", Acore::StringFormat("{} lfg={} player={}",
                    section, lfgDungeon, player->GetName()));
                SaveToDB();
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            switch (go->GetEntry())
            {
                case GO_WORKSHOP_DOOR:
                    ApplyWorkshopDoor(go);
                    break;
                case GO_FINAL_CHAMBER_DOOR:
                    OpenLatched(go);        // section 7 #17 A: open from the load on
                    break;
                case GO_PUMMELER_CHEST:
                case GO_PUMMELER_CHEST_HEROIC:
                    _chest = go->GetGUID();
                    break;
                case GO_BUTTON_01:
                case GO_BUTTON_02:
                case GO_BUTTON_03:
                case GO_BUTTON_04:
                case GO_BUTTON_05:
                case GO_BUTTON_06:
                    go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);     // section 7 #38 m A (the S0 rev sets it too)
                    break;
                default:
                    break;
            }
        }

        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            // Thermaplugg's loot bit follows the pull's verdict (a respawned body starts unlit).
            if (creature->GetEntry() == NPC_THERMAPLUGG)
                ApplyHardModeLoot(creature);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            // Loading, or a slot's first write (a BossAI's _Reset): the base stores it onto TO_BE_DECIDED and returns
            // false, so nothing below fires from it.
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_ELECTROCUTIONER:
                    if (state == DONE)
                    {
                        RaiseWorkshopDoorTo(WORKSHOP_DOOR_UNLOCKED, "electrocutioner");
                        RefreshEndNpc(1, "electrocutioner");
                        SaveToDB();     // a first write on an unsettled slot is not saved (RB-2)
                    }
                    break;
                case BOSS_ALERT_SYSTEM:
                    if (state == DONE)
                    {
                        RaiseWorkshopDoorTo(WORKSHOP_DOOR_OPEN, "alert-system");
                        SaveToDB();
                    }
                    break;
                case BOSS_CROWD_PUMMELER:
                    if (state == DONE)
                    {
                        if (_chestState == PUMMELER_CHEST_NONE)
                            _chestState = PUMMELER_CHEST_PLACED;
                        WatchChest("pummeler");
                        SaveToDB();
                    }
                    break;
                case BOSS_THERMAPLUGG:
                    OnThermapluggState(state);
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
                case DATA_GRUBBIS:
                    // Its stock writer (Grubbis's death SmartAI) is unreachable: Grubbis has no spawn and Emi is gone.
                    LOG_DEBUG(kLog, "gnomer instance ignored stock SetData({}, {})", type, data);
                    return;
                case DATA_WORKSHOP_DOOR:
                    RaiseWorkshopDoorTo(data, "use", true);
                    return;
                case DATA_HARD_MODE:
                    SetHardModeFlag(data, "console");
                    return;
                case DATA_HARD_MODE_VERDICT:
                    SetVerdict(data);
                    return;
                case DATA_GM_DOOR:
                    if (data <= WORKSHOP_DOOR_OPEN)
                    {
                        _door = data;
                        ApplyWorkshopDoor(GetGameObject(kGuidWorkshopDoor));
                        DungeonKit::LogMechanic(kLogDungeon, "instance", "door", Acore::StringFormat("{} (gm)",
                            kWorkshopDoorNames[_door]));
                        SaveToDB();
                    }
                    return;
                case DATA_GM_HARD_MODE:
                    if (GmHardModeAllowed(Heroic(), Slot(BOSS_THERMAPLUGG), data))
                    {
                        _hardMode = data ? 1 : 0;
                        DungeonKit::LogMechanic(kLogDungeon, "thermaplugg", "hardmode-flag", Acore::StringFormat(
                            "{} (gm)", _hardMode));
                        SaveToDB();
                    }
                    return;
                case DATA_GM_CHEST:
                    GmChest(data);
                    return;
                case DATA_GM_END_NPC:
                    GmEndNpc(data);
                    return;
                case DATA_GM_SECTION:
                    if (data <= kSections.size())
                    {
                        _section = data;
                        SaveToDB();
                    }
                    return;
                default:
                    return;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            if (type == DATA_END_NPC_BASE + 1 || type == DATA_END_NPC_BASE + 2)
                return EndNpcAlive(type - DATA_END_NPC_BASE) ? 1 : 0;

            switch (type)
            {
                case DATA_GRUBBIS:
                    return NOT_STARTED;
                case DATA_WORKSHOP_DOOR:
                    return _door;
                case DATA_FINAL_CHAMBER:
                    return 1;
                case DATA_SECTION:
                    return _section;
                case DATA_HARD_MODE:
                    return _hardMode;
                case DATA_HARD_MODE_VERDICT:
                    return _verdict;
                case DATA_HARD_MODE_KILLED:
                    return Slot(BOSS_WHOLE_WORKSHOP) == DONE ? 1 : 0;
                case DATA_HARD_MODE_KEY:
                    return (!_hardMode && HardModeFlagAllowed(Heroic(), Slot(BOSS_THERMAPLUGG))) ? 1 : 0;
                case DATA_PUMMELER_CHEST:
                    return _chestState;
                default:
                    return 0;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            switch (type)
            {
                case kGuidBossBase + BOSS_WHOLE_WORKSHOP:
                    return InstanceScript::GetGuidData(kGuidBossBase + BOSS_THERMAPLUGG);
                case kGuidPummelerChest:
                    return _chest;
                case kGuidEndNpcBase + 1:
                case kGuidEndNpcBase + 2:
                    return _endNpc[type - kGuidEndNpcBase - 1];
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
            events.Update(diff);

            while (uint32 const eventId = events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_WATCH:
                        Watch();
                        events.ScheduleEvent(EVENT_WATCH, Milliseconds(kWatchMs));
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
            GnrSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
                save.states[i] = Slot(i);
            save.workshopDoor = _door;
            save.hardMode = _hardMode;
            save.pummelerChest = _chestState;
            save.section = _section;
            return FormatGnrSave(save);
        }

        // Reads this script's "G N R" string, or the stock "G N O" one (Map::CreateInstanceData set the
        // completed-encounter mask before Load).
        void Load(char const* in) override
        {
            if (!in || !*in)
                return;

            GnrSave save;
            if (!ParseGnrSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "gnomer instance: ignored save '{}'", in);
                return;
            }
            _door = save.workshopDoor;
            _hardMode = save.hardMode;
            _chestState = save.pummelerChest;
            _section = save.section;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips the switch.
            for (uint32 i = 0; i < kBossCount; ++i)
                InstanceScript::SetBossState(i, EncounterState(save.states[i]));
        }

    private:
        // ------------------------------------------------------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------------------------------------------------------
        uint32 Slot(uint32 id) const
        {
            return SettledSlotState(uint32(GetBossState(id)));
        }

        // A write the instance makes itself (slot 6).
        void ForceBossState(uint32 id, EncounterState state)
        {
            if (Slot(id) != uint32(state))
                SetBossState(id, state);
        }

        bool Heroic() const
        {
            return instance->IsHeroic();
        }

        // The first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED through
        // the base's loading branch, so the first live write saves and runs the switch. Every event restarts here
        // (RB-2): the door from the slots, the chest and the End NPCs at the first watch.
        void Settle()
        {
            _settled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                uint32 const state = GetBossState(i);
                if (SettledSlotState(state) != state)
                    InstanceScript::SetBossState(i, EncounterState(SettledSlotState(state)));
            }
            _door = RaiseWorkshopDoor(_door, _door, Slot(BOSS_ELECTROCUTIONER), Slot(BOSS_ALERT_SYSTEM));
            ApplyWorkshopDoor(GetGameObject(kGuidWorkshopDoor));
            events.ScheduleEvent(EVENT_WATCH, Milliseconds(kWatchMs));
            DungeonKit::LogMechanic(kLogDungeon, "instance", "settle", Acore::StringFormat(
                "door={} hardmode={} chest={} section={} heroic={}", kWorkshopDoorNames[_door], _hardMode,
                kChestNames[_chestState], _section, Heroic() ? 1 : 0));
        }

        void Watch()
        {
            WatchWorkshopDoor();
            if (GameObject* chamber = GetGameObject(kGuidFinalChamber))
                if (chamber->GetGoState() != GO_STATE_ACTIVE)
                    OpenLatched(chamber);
            WatchChest("watch");
            RefreshEndNpc(1, "watch");
            RefreshEndNpc(2, "watch");
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Workshop Door (section 7 #15 A, #16 B)
        // ------------------------------------------------------------------------------------------------------------
        // `byUse`: a player opened the door (go_gnomer_workshop_door): counted only while it is unlocked, so a sealed
        // door that a GM or a script opened is shut again by the AI.
        void RaiseWorkshopDoorTo(uint32 wanted, char const* how, bool byUse = false)
        {
            if (byUse && !WorkshopDoorOpenByUseAllowed(_door))
                return;
            uint32 const before = _door;
            _door = RaiseWorkshopDoor(_door, wanted, Slot(BOSS_ELECTROCUTIONER), Slot(BOSS_ALERT_SYSTEM));
            // _door is set first: the latch below may fire the door's OnStateChanged, which forwards nothing once
            // _door is open (WorkshopDoorUseForwarded), and the latch skips a door already open and activated
            // (OpenLatchSetsLootState): either guard alone ends the AI -> SetData -> latch loop (R-1-FW B1).
            ApplyWorkshopDoor(GetGameObject(kGuidWorkshopDoor));
            if (_door != before)
            {
                DungeonKit::LogMechanic(kLogDungeon, "instance", "door", Acore::StringFormat("{} how={}",
                    kWorkshopDoorNames[_door], how));
                SaveToDB();
            }
        }

        void ApplyWorkshopDoor(GameObject* door)
        {
            if (!door)
                return;
            if (_door == WORKSHOP_DOOR_OPEN)
                OpenLatched(door);
            else
                ShutDoor(door, WorkshopDoorSelectable(_door));
        }

        // The latch: an open door found shut (a GM, a reset) opens again; a shut one keeps its selectability. A door
        // found open below the open state is the AI's to judge (a player's use raises it, a refused one is shut).
        void WatchWorkshopDoor()
        {
            GameObject* door = GetGameObject(kGuidWorkshopDoor);
            if (!door)
                return;
            bool const open = door->GetGoState() != GO_STATE_READY;
            if (_door == WORKSHOP_DOOR_OPEN)
            {
                if (!open)
                    OpenLatched(door);
                return;
            }
            if (open)
                return;
            if (WorkshopDoorSelectable(_door))
                door->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            else
                door->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Crowd Pummeler's chest (section 3.2 item 5, section 7 #38 k A): an emptied chest (consumed: deleted, then
        // gone from the map, R-1-FW M1) is saved as looted; a chest lost to a reload or a restart is placed again.
        // ------------------------------------------------------------------------------------------------------------
        void WatchChest(char const* how)
        {
            if (_chestState == PUMMELER_CHEST_LOOTED)
                return;
            GameObject* chest = _chest ? instance->GetGameObject(_chest) : nullptr;
            if (ChestEmptied(!_chest.IsEmpty(), chest != nullptr, chest && chest->isSpawned()))
            {
                _chestState = PUMMELER_CHEST_LOOTED;
                _chest.Clear();
                DungeonKit::LogMechanic(kLogDungeon, "pummeler", "chest", "emptied");
                SaveToDB();
                return;
            }
            if (_chestGmHeld)
                return;
            Point3 const& at = kPummelerChestSpot;
            if (!ChestPlaceDue(Slot(BOSS_CROWD_PUMMELER), _chestState, chest != nullptr,
                instance->IsGridLoaded(at.x, at.y)))
                return;
            PlaceChest(how);
        }

        void PlaceChest(char const* how)
        {
            Point3 const& at = kPummelerChestSpot;
            float z = instance->GetHeight(at.x, at.y, at.z + 2.f);
            if (z <= INVALID_HEIGHT)
                z = at.z;
            float const half = at.o / 2.f;
            uint32 const entry = ChestEntry(Heroic());
            if (GameObject* chest = instance->SummonGameObject(entry, at.x, at.y, z, at.o, 0.f, 0.f, std::sin(half),
                std::cos(half), kChestRespawnSecs))
            {
                _chest = chest->GetGUID();
                if (_chestState == PUMMELER_CHEST_NONE)
                    _chestState = PUMMELER_CHEST_PLACED;
                DungeonKit::LogMechanic(kLogDungeon, "pummeler", "chest", Acore::StringFormat("placed entry={} how={}",
                    entry, how));
            }
        }

        void GmChest(uint32 data)
        {
            if (GameObject* chest = _chest ? instance->GetGameObject(_chest) : nullptr)
                chest->Delete();
            _chest.Clear();     // untracked first: the deleted chest must not read as emptied
            _chestGmHeld = !data;   // Set(0) holds the watch off until Set(1) or a reload (R-1-FW n1)
            if (data)
            {
                _chestState = PUMMELER_CHEST_PLACED;
                PlaceChest("gm");
            }
            else
                _chestState = PUMMELER_CHEST_NONE;
            SaveToDB();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The End NPCs (section 3.2 item 4, section 7 #24 A): the instance summons them, the boss files do nothing.
        // ------------------------------------------------------------------------------------------------------------
        bool EndNpcAlive(uint32 endNpc) const
        {
            if (endNpc < 1 || endNpc > kEndNpcCount || !_endNpc[endNpc - 1])
                return false;
            Creature* exile = instance->GetCreature(_endNpc[endNpc - 1]);
            return exile && exile->IsAlive();
        }

        void RefreshEndNpc(uint32 endNpc, char const* how)
        {
            if (!EndNpcStands(Heroic(), Slot(EndNpcSlot(endNpc))) || EndNpcAlive(endNpc))
                return;
            Point3 const at = EndNpcSpot(endNpc);
            if (!instance->IsGridLoaded(at.x, at.y))
                return;
            SummonEndNpc(endNpc, how);
        }

        void SummonEndNpc(uint32 endNpc, char const* how)
        {
            // The quests WP owns the exile's template (R-1-FW m1): until it lands, say so once per load instead of a
            // missing-template error from Creature::Create on every watch.
            if (!sObjectMgr->GetCreatureTemplate(NPC_EXILE))
            {
                if (!_exileMissingLogged)
                    LOG_ERROR(kLog, "gnomer instance: End NPC {} has no creature_template; the End NPCs stay off",
                        uint32(NPC_EXILE));
                _exileMissingLogged = true;
                return;
            }
            Point3 const at = EndNpcSpot(endNpc);
            if (TempSummon* exile = instance->SummonCreature(NPC_EXILE, Position(at.x, at.y, at.z, at.o)))
            {
                _endNpc[endNpc - 1] = exile->GetGUID();
                DungeonKit::LogMechanic(kLogDungeon, "instance", "end-npc", Acore::StringFormat("{} summoned how={}",
                    endNpc, how));
            }
        }

        void GmEndNpc(uint32 data)
        {
            if (data == 1 || data == 2)
            {
                if (!EndNpcAlive(data))
                    SummonEndNpc(data, "gm");
                return;
            }
            for (ObjectGuid& guid : _endNpc)
            {
                if (Creature* exile = guid ? instance->GetCreature(guid) : nullptr)
                    exile->DespawnOrUnsummon();
                guid.Clear();
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // The hard mode (section 3.2 item 6, section 3.7; RB-24)
        // ------------------------------------------------------------------------------------------------------------
        void SetHardModeFlag(uint32 data, char const* how)
        {
            if (data != 1 || _hardMode)
                return;
            if (!HardModeFlagAllowed(Heroic(), Slot(BOSS_THERMAPLUGG)))
            {
                DungeonKit::LogMechanic(kLogDungeon, "thermaplugg", "hardmode-refused", Acore::StringFormat(
                    "heroic={} slot5={} how={}", Heroic() ? 1 : 0, Slot(BOSS_THERMAPLUGG), how));
                return;
            }
            _hardMode = 1;
            DungeonKit::LogMechanic(kLogDungeon, "thermaplugg", "hardmode-flag", Acore::StringFormat("1 how={}", how));
            SaveToDB();
        }

        // Thermaplugg's pull (D6): the packages were built (kVerdictArmed) or not (kVerdictPlain). Only during the
        // pull (slot 5 IN_PROGRESS); a wipe or the kill clears it.
        void SetVerdict(uint32 data)
        {
            if (Slot(BOSS_THERMAPLUGG) != IN_PROGRESS || (data != kVerdictPlain && data != kVerdictArmed))
            {
                LOG_INFO(kLog, "{} instance verdict {} refused (slot 5 {})", kLogDungeon, data,
                    Slot(BOSS_THERMAPLUGG));
                return;
            }
            _verdict = data;
            ApplyHardModeLoot();
            DungeonKit::LogMechanic(kLogDungeon, "thermaplugg", "verdict", Acore::StringFormat("{} armed={}", data,
                HardModeArmed(Heroic(), _hardMode, _verdict) ? 1 : 0));
        }

        void OnThermapluggState(EncounterState state)
        {
            switch (state)
            {
                case IN_PROGRESS:
                    _verdict = kVerdictNone;    // a fresh pull: D6 sends its verdict next
                    ApplyHardModeLoot();
                    break;
                case DONE:
                {
                    // His loot is already filled (Unit::Kill, before JustDied), hard mode list included.
                    bool const armed = HardModeArmed(Heroic(), _hardMode, _verdict);
                    if (armed)
                    {
                        ForceBossState(BOSS_WHOLE_WORKSHOP, DONE);
                        DungeonKit::LogMechanic(kLogDungeon, "thermaplugg", "hardmode-kill");
                    }
                    _verdict = kVerdictNone;
                    RefreshEndNpc(2, "thermaplugg");
                    SaveToDB();     // a first write on an unsettled slot is not saved (RB-2)
                    break;
                }
                default:                        // a wipe or an evade: the flag stays (section 3.7), the verdict goes
                    _verdict = kVerdictNone;
                    ApplyHardModeLoot();
                    break;
            }
        }

        // Item variants IV7 (the Deadmines pattern): Thermaplugg's heroic lootid holds the hard mode list at LootMode
        // 2; the bit rides him while the pull is armed and he is not dead (rule 1: at the pull and the verdict, never
        // in JustDied).
        void ApplyHardModeLoot(Creature* thermaplugg = nullptr)
        {
            if (!thermaplugg)
                thermaplugg = GetCreature(kGuidBossBase + BOSS_THERMAPLUGG);
            if (thermaplugg && thermaplugg->IsAlive())
                DungeonKit::SetHardModeLoot(thermaplugg, HardModeLootLit(HardModeArmed(Heroic(), _hardMode, _verdict),
                    Slot(BOSS_THERMAPLUGG)));
        }

        EventMap events;
        bool _settled = false;

        // Saved run data
        uint32 _door = WORKSHOP_DOOR_SEALED;
        uint32 _hardMode = 0;
        uint32 _chestState = PUMMELER_CHEST_NONE;
        uint32 _section = 0;

        // Per pull or per load (rebuilt after a reload)
        uint32 _verdict = kVerdictNone;
        ObjectGuid _chest;
        bool _chestGmHeld = false;          // `.dbtest gnomer chest 0`: the watch places nothing
        bool _exileMissingLogged = false;
        std::array<ObjectGuid, kEndNpcCount> _endNpc{};
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_gnomeregan_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_gnomeregan_rework()
{
    new instance_gnomeregan_rework();
    RegisterDungeonReworkGameObjectAI(go_gnomer_workshop_door, GnomereganRework::kInstanceScriptName);
}
