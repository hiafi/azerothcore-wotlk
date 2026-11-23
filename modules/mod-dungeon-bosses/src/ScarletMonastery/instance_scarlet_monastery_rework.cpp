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

// The Scarlet Monastery build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_scarlet_monastery` (section 7 #1 A): modules load after the core scripts, and a database-bound script
// registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 189's
// instance_template row is untouched and the stock InstanceMapScript is replaced at load. The other scripts the stock
// AddSC_instance_scarlet_monastery registers (spell_forgiveness_dummy_visual, spell_transform_ghost_visual: the
// Ashbringer cameo) stay registered and keep working, none of them copied; hallows_end.cpp's Horseman and
// go_pumpkin_shrine reach this script through GetInstanceScript() and keep their live behavior (data id 5, below).
//
// Re-implemented from the stock instance (src/server/scripts/EasternKingdoms/ScarletMonastery/
// instance_scarlet_monastery.cpp at Playerbot 81d92fc05, which stays untouched; its last upstream change is b70b14ed6,
// daobashun, "More NPCs become friendly during the Ashbringer Event", AzerothCore #27257, after 7069d99dc and
// 9db9c42cb, daobashun (the Forgiveness visual #26454, the Scarlet Monastery improvement #17558), ebe89b875,
// Alexandru-Mihai Maftei (Whitemane before Mograine's resurrection, #18082), and 7549eb59b, avarishd (the whole
// Cathedral pull, #11766); the file goes back to Yehonal's, Kargatum's, Kitzunu's and Francesco Borzì's commits, with
// UltraNix, Nefertumm and others): every stock data id with its stock meaning (TYPE_MOGRAINE_AND_WHITE_EVENT and
// DATA_HORSEMAN_EVENT 6 sharing `_encounter`, TYPE_ASHBRINGER_EVENT, the four GetGuidData keys), the Ashbringer
// event (Whitemane's despawn, the Chapel Door, the friendly sweep over every creature but the Graveyard list), and,
// while wave 2 is unbound, the stock Cathedral pull (the six entries within 80 yd of Mograine) and the stock FAIL
// block. Each upstream merge re-diffs the stock file and hallows_end.cpp against b70b14ed6 (handoff section 6).
//
// What is new: 18 boss states (ScarletMonasteryRework.h: 0-13 the DungeonEncounter bits, 14-17 the hard mode kills);
// the Horseman quirk kept as live (GetData(5) answers 0; SetData(5) writes a private field); the Ashbringer guard
// (refused while a Cathedral slot fights; the rework's own units left out of the sweep; section 7 #16 A); the council's
// DONE and credit when both are dead; the Cathedral pair split once wave 2 binds (the Chapel Door's GameObjectAI and
// the crossing restart start the Last Stand, slot 5; Whitemane's slot 6 only after it; GetData(1) / GetData(6) mirror
// the two; section 7 #19 A); the keyless interior doors (section 7 #14 A), Herod's Door shut while he fights and the
// lever inert; the wing portals (section 7 #15 A) spawned from the slots and restored after a reload; the four hard
// mode flags (the Desecration's touch order and judge, Doan's four pages, Herod's taunt, the Torch) with their kill
// slots and loot bits; the "SCR" save string with the stock "SM" reader.

#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitWings.h"
#include "EventMap.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScriptedCreature.h"
#include <algorithm>
#include <array>
#include <list>
#include <optional>

using namespace ScarletMonasteryRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // Stock: CATHEDRAL_PULL_RANGE (the distance from the Cathedral doors to where Mograine stands); wave 1 only.
    float constexpr kStockCathedralPullRange = 80.0f;

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the spawned bosses under kGuidBossBase + slot
    // (Mograine, Whitemane and Doan under their stock keys), Azshir and Fairbanks under their hand keys, Vorrel under
    // the stock DATA_VORREL, the stock doors under their stock keys, and the other single objects under their entries.
    // The companies, risen heroes, parts, books, anchors, recruits, trainees, brambles, the vigil Fairbanks, the spirit
    // and the portals are tracked by their own scripts or by hand.
    ObjectData const creatureData[] =
    {
        { NPC_VISHAS,           kGuidBossBase + BOSS_VISHAS         },
        { NPC_THALNOS,          kGuidBossBase + BOSS_THALNOS        },
        { NPC_LOKSEY,           kGuidBossBase + BOSS_LOKSEY         },
        { NPC_DOAN,             DATA_ARCANIST_DOAN                  },
        { NPC_HEROD,            kGuidBossBase + BOSS_HEROD          },
        { NPC_MOGRAINE,         DATA_MOGRAINE                       },
        { NPC_WHITEMANE,        DATA_WHITEMANE                      },
        { NPC_IRONSPINE,        kGuidBossBase + BOSS_IRONSPINE      },
        { NPC_FALLEN_CHAMPION,  kGuidBossBase + BOSS_COUNCIL        },
        { NPC_AZSHIR,           kGuidAzshir                         },
        { NPC_SM_KELL,          kGuidBossBase + BOSS_KELL           },
        { NPC_SM_HOLLIS_GREY,   kGuidBossBase + BOSS_HOLLIS_GREY    },
        { NPC_SM_CRELL,         kGuidBossBase + BOSS_CRELL          },
        { NPC_SM_HALDEN,        kGuidBossBase + BOSS_HALDEN         },
        { NPC_SM_THORNE,        kGuidBossBase + BOSS_THORNE         },
        { NPC_FAIRBANKS,        kGuidFairbanks                      },
        { NPC_VORREL,           DATA_VORREL                         },
        { 0,                    0                                   }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_CHAPEL_DOOR,           DATA_DOOR_CHAPEL        },
        { GO_HIGH_INQUISITOR_DOOR,  DATA_DOOR_WHITEMANE     },
        { GO_CHAPEL_LEVER,          GO_CHAPEL_LEVER         },
        { GO_HERODS_DOOR,           GO_HERODS_DOOR          },
        { GO_HERODS_LEVER,          GO_HERODS_LEVER         },
        { GO_SECRET_DOOR,           GO_SECRET_DOOR          },
        { GO_TORCH,                 GO_TORCH                },
        { GO_DOANS_STRONGBOX,       GO_DOANS_STRONGBOX      },
        { 0,                        0                       }
    };

    enum SmInstanceEvents
    {
        EVENT_PORTALS       = 1,    // every second: the portals the slots call for stand (a reload, a grid unload)
        EVENT_CROSSING      = 2,    // every second: the crossing restart of the Last Stand (section 7 #19 A)
    };
}

// The Chapel Door 104591 (section 7 #14 A, #19 A; HUB gap 18): no stock event exists (FACTS-STOCK section 3.3). Its
// use by a player, the lever 104589 (SmartGameObjectAI "activate guid 11875") and the Ashbringer path all set its loot
// state to GO_ACTIVATED; the instance tells them apart (the Ashbringer flag is set before the door opens) and starts
// the Last Stand once wave 2 binds. Bound by S0's SQL rev (gameobject_template.ScriptName).
struct go_sm_chapel_door : public GameObjectAI
{
    explicit go_sm_chapel_door(GameObject* go) : GameObjectAI(go) { }

    void OnStateChanged(uint32 state, Unit* unit) override
    {
        if (state != GO_ACTIVATED)
            return;
        if (InstanceScript* instance = me->GetInstanceScript())
            instance->SetData(DATA_CHAPEL_DOOR_OPENED, unit ? 1 : 0);
    }
};

// The wing portal 301324 (section 7 #15 A): its use moves the group on (ScarletMonasteryKit.h UseWingPortal); which
// portal it is follows from where it stands (kPortals). Bound by S0's SQL rev (the template's ScriptName).
struct go_sm_wing_portal : public GameObjectAI
{
    explicit go_sm_wing_portal(GameObject* go) : GameObjectAI(go) { }

    bool GossipHello(Player* player, bool /*reportUse*/) override
    {
        if (WingPortal const* portal = PortalNear(DungeonKit::PlaneOf(me)))
            UseWingPortal(*portal, me, player);     // the kit's PortalTravel (ScarletMonasteryKit.cpp)
        else
            LOG_ERROR(kLog, "sm portal at ({:.1f}, {:.1f}) matches no kPortals spot", me->GetPositionX(),
                me->GetPositionY());
        return true;
    }
};

class instance_scarlet_monastery_rework : public InstanceMapScript
{
public:
    instance_scarlet_monastery_rework() : InstanceMapScript(kInstanceScriptName, kMapScarletMonastery) { }

    struct instance_scarlet_monastery_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_scarlet_monastery_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadObjectData(creatureData, gameObjectData);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            // Stock: every creature created in the map joins the Ashbringer set, except the Graveyard list; the rework
            // also leaves its own entries out (section 7 #16 A) and keeps it to the Cathedral's spawns (RF-1 m-1).
            bool const spawned = creature->GetSpawnId() != 0;
            uint32 const wing = WingOf(DungeonKit::PlaneOf(creature));
            if (AshbringerSweepsUnit(creature->GetEntry(), spawned, wing))
                _ashbringerNpcs.insert(creature->GetGUID());
            // A reload after the Ashbringer event: the sweep holds for every creature created again (R-1-KIT m-2).
            if (AshbringerKeepsFriendly(_ashbringer, creature->GetEntry(), creature->IsAlive(), spawned, wing))
                creature->SetFaction(kFactionFriendly);
        }

        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            switch (go->GetEntry())
            {
                case GO_CHAPEL_DOOR:
                    // Section 7 #14 A: keyless (S0's SQL clears the template flag too; the outdoor doors stay keyed).
                    go->RemoveGameObjectFlag(GO_FLAG_LOCKED);
                    if (_ashbringer || (kWave2Bound && Slot(BOSS_LAST_STAND) == DONE))
                        OpenDoorLatched(go);
                    break;
                case GO_HERODS_DOOR:
                    go->RemoveGameObjectFlag(GO_FLAG_LOCKED);
                    if (Slot(BOSS_HEROD) == DONE)
                        OpenDoorLatched(go);
                    break;
                case GO_HERODS_LEVER:
                    ApplyHerodsLever(go);
                    break;
                case GO_HIGH_INQUISITOR_DOOR:
                    // Wave 1: the stock Whitemane SmartAI opens it (guid 11877). Bound: Whitemane walked out; latched
                    // like the Chapel and Herod's doors (R-1-KIT M-2: one click must not shut it after a reload).
                    if (kWave2Bound && Slot(BOSS_LAST_STAND) == DONE)
                        OpenDoorLatched(go);
                    break;
                case GO_SECRET_DOOR:
                    if (_torchPulled)
                        HandleGameObject(ObjectGuid::Empty, true, go);
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

            uint32 const entry = creature->GetEntry();
            if (entry == NPC_AZSHIR || entry == NPC_FALLEN_CHAMPION)
            {
                // One encounter (D3): DONE once both are dead, whoever dies last; the credit by spell (3.11 #3).
                if (Slot(BOSS_COUNCIL) != DONE && CouncilDead())
                {
                    LOG_INFO(kLog, "sm instance council dead: boss state {} DONE, credit spell {}",
                        uint32(BOSS_COUNCIL), kSpellCouncilCredit);
                    // The kit's spell credit (KT-SM, section 3.11 #3): the row 212300 names, plus the heroic bind.
                    DungeonKit::CreditEncounterBySpell(instance, kSpellCouncilCredit, creature, kLogDungeon,
                        "council");
                    ForceBossState(BOSS_COUNCIL, DONE);
                }
                return;
            }

            // A boss whose slot its own script does not write (Herod, Mograine and Whitemane while wave 2 is unbound)
            // records its death here. Once wave 2 binds the Last Stand is written through DATA_LAST_STAND only (his
            // real death is in Whitemane's fight).
            std::optional<uint32> const boss = BossOfEntry(entry);
            if (!boss || *boss == BOSS_COUNCIL || SlotWrittenByScript(*boss) || Slot(*boss) == DONE)
                return;
            if (*boss == BOSS_LAST_STAND && kWave2Bound)
                return;
            LOG_INFO(kLog, "sm instance {} died: boss state {} DONE (written by the instance)", entry, *boss);
            ForceBossState(*boss, DONE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            uint32 const before = id < kBossCount ? Slot(id) : uint32(TO_BE_DECIDED);
            bool const bypass = _bypassGuard || _gmSlotWrite;
            _gmSlotWrite = false;
            if (!bypass && id == BOSS_WHITEMANE && !WhitemaneWriteAccepted(state, Slot(BOSS_LAST_STAND)))
            {
                LOG_DEBUG(kLog, "sm instance refused boss state {} -> {} (the Last Stand is not DONE)", id,
                    uint32(state));
                return false;
            }
            if (!InstanceScript::SetBossState(id, state))
                return false;

            OnSlotChanged(id, before, state);
            return true;
        }

        // ------------------------------------------------------------------------------------------------------------
        // Data
        // ------------------------------------------------------------------------------------------------------------
        void SetData(uint32 type, uint32 data) override
        {
            switch (type)
            {
                case TYPE_MOGRAINE_AND_WHITE_EVENT:
                case DATA_HORSEMAN_EVENT:
                    if (kWave2Bound)
                    {
                        // Its writers (Mograine's and Whitemane's stock SmartAI) are dropped with wave 2's rev.
                        LOG_DEBUG(kLog, "sm instance ignored SetData({}, {}) (the Cathedral pair is slots 5-6)", type,
                            data);
                        return;
                    }
                    if (type == DATA_HORSEMAN_EVENT)
                        _encounter = data;      // stock: data 6 writes the same field
                    else
                        StockCathedral(data);
                    return;
                case TYPE_ASHBRINGER_EVENT:
                    SetAshbringer(data);
                    return;
                case kHallowsEndHorsemanData:
                    // HUB ruling 9, section 7 #17 A: hallows_end.cpp's id 5; never a slot, never saved.
                    LOG_DEBUG(kLog, "sm instance horseman state {} -> {} (private; GetData(5) stays 0)",
                        _horsemanState, data);
                    _horsemanState = data;
                    return;
                case DATA_CHAPEL_DOOR_OPENED:
                    OnChapelDoorOpened(data != 0);
                    return;
                case DATA_LAST_STAND:
                    SetLastStand(data);
                    return;
                case DATA_DESECRATION_TOUCH:
                    TouchGravestone(data);
                    return;
                case DATA_DOAN_PAGE_READ:
                    ReadDoanPage(data);
                    return;
                case DATA_HARD_MODE_HEROD:
                    if (data && HerodTauntAllowed(instance->IsHeroic(), Slot(BOSS_HEROD), _herodTaunted != 0))
                        LightHardMode(BOSS_CALL_TO_ARMS, "taunt");
                    return;
                case DATA_HARD_MODE_WHITEMANE:
                    if (data && TorchAllowed(instance->IsHeroic(), Slot(BOSS_LAST_STAND), Slot(BOSS_WHITEMANE),
                        _torchPulled != 0))
                        LightHardMode(BOSS_THE_TRUTH, "torch");
                    return;
                case DATA_GM_HARD_MODE:
                    if (IsHardModeSlot(data))
                        LightHardMode(data, "gm");
                    return;
                case DATA_GM_PORTAL:
                    _gmPortals |= PortalBit(data);
                    RefreshPortals();
                    return;
                case DATA_GM_SLOT_WRITE:
                    _gmSlotWrite = data != 0;
                    return;
                default:
                    break;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case TYPE_MOGRAINE_AND_WHITE_EVENT:
                case DATA_HORSEMAN_EVENT:
                    return kWave2Bound ? CathedralMirror(Slot(BOSS_LAST_STAND), Slot(BOSS_WHITEMANE)) : _encounter;
                case TYPE_ASHBRINGER_EVENT:
                    return _ashencounter;
                case kHallowsEndHorsemanData:
                    return HorsemanGetData(_horsemanState);
                case DATA_HORSEMAN_PRIVATE:
                    return _horsemanState;
                case DATA_LAST_STAND:
                    return Slot(BOSS_LAST_STAND);
                case DATA_CATHEDRAL_STAGE:
                    return uint32(CathedralStageFor(Slot(BOSS_LAST_STAND), Slot(BOSS_WHITEMANE)));
                case DATA_DESECRATION_TOUCH:
                    return _touchCount;
                case DATA_DESECRATION_RESULT:
                    return uint32(_desecrationResult);
                case DATA_HARD_MODE_THALNOS:
                    return _desecration;
                case DATA_DOAN_PAGE_READ:
                    return DoanPagesRead(_doanPages);
                case DATA_HARD_MODE_DOAN:
                    return _heresy;
                case DATA_HARD_MODE_HEROD:
                    return _herodTaunted;
                case DATA_HARD_MODE_WHITEMANE:
                    return _torchPulled;
                case DATA_PORTALS:
                    return PortalsOpenMask(States()) | _gmPortals;
                case DATA_DOAN_PAGES_MASK:
                    return _doanPages;
                case DATA_ASHBRINGER_REFUSED:
                    return _ashbringerRefused;
                default:
                    return 0;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            if (type >= kGuidBossBase && type < kGuidBossBase + kBossCount)
                return BossGuid(type - kGuidBossBase);
            return InstanceScript::GetGuidData(type);
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
                    case EVENT_PORTALS:
                        RefreshPortals();
                        HoldAshbringerDespawn();
                        events.ScheduleEvent(EVENT_PORTALS, 1s);
                        break;
                    case EVENT_CROSSING:
                        CrossingCheck();
                        events.ScheduleEvent(EVENT_CROSSING, Milliseconds(kCrossingCheckMs));
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
            SmSave save;
            save.states = States();
            save.desecration = _desecration;
            save.doanPages = _doanPages;
            save.heresy = _heresy;
            save.herodTaunted = _herodTaunted;
            save.torchPulled = _torchPulled;
            save.ashbringer = _ashbringer ? 1 : 0;
            return FormatSmSave(save);
        }

        // Reads this script's "S C R" string, or the stock "S M" one (no data; with the completed-encounter mask, which
        // Map::CreateInstanceData sets before Load).
        void Load(char const* in) override
        {
            if (!in || !*in)
                return;

            SmSave save;
            if (!ParseSmSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "sm instance: ignored save '{}'", in);
                return;
            }

            _desecration = save.desecration;
            _doanPages = save.doanPages;
            _heresy = save.heresy;
            _herodTaunted = save.herodTaunted;
            _torchPulled = save.torchPulled;
            _ashbringer = save.ashbringer != 0;
            _ashencounter = _ashbringer ? uint32(IN_PROGRESS) : 0;     // stock wrote the SmartTrigger's value (1)
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips the switch (no guard, no
            // kill flag); the doors follow from the create hooks, the portals from the first Update.
            for (uint32 i = 0; i < kBossCount; ++i)
                InstanceScript::SetBossState(i, EncounterState(save.states[i]));
        }

    private:
        // A slot's state, TO_BE_DECIDED read as NOT_STARTED (before the first Update settles it).
        uint32 Slot(uint32 id) const
        {
            return SettledSlotState(uint32(GetBossState(id)));
        }

        std::array<uint32, kBossCount> States() const
        {
            std::array<uint32, kBossCount> states{};
            for (uint32 i = 0; i < kBossCount; ++i)
                states[i] = Slot(i);
            return states;
        }

        // A write the instance makes itself (the council, the Last Stand, deaths, the hard mode kills): past the guard.
        bool ForceBossState(uint32 id, EncounterState state)
        {
            _bypassGuard = true;
            bool const changed = SetBossState(id, state);
            _bypassGuard = false;
            return changed;
        }

        // The first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED through
        // the base's loading branch (stored, no save, no switch), so the first real write saves and runs the switch.
        // Every event restarts from here: the portals the slots call for, the crossing watch.
        void Settle()
        {
            _settled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                uint32 const state = GetBossState(i);
                if (SettledSlotState(state) != state)
                    InstanceScript::SetBossState(i, EncounterState(SettledSlotState(state)));
            }
            events.ScheduleEvent(EVENT_PORTALS, 1s);
            if (kWave2Bound)
                events.ScheduleEvent(EVENT_CROSSING, Milliseconds(kCrossingCheckMs));
        }

        ObjectGuid BossGuid(uint32 bossId) const
        {
            switch (bossId)
            {
                case BOSS_DOAN:
                case BOSS_HERESY:
                    return InstanceScript::GetGuidData(DATA_ARCANIST_DOAN);
                case BOSS_LAST_STAND:
                    return InstanceScript::GetGuidData(DATA_MOGRAINE);
                case BOSS_WHITEMANE:
                case BOSS_THE_TRUTH:
                    return InstanceScript::GetGuidData(DATA_WHITEMANE);
                case BOSS_DESECRATION:
                    return InstanceScript::GetGuidData(kGuidBossBase + BOSS_THALNOS);
                case BOSS_CALL_TO_ARMS:
                    return InstanceScript::GetGuidData(kGuidBossBase + BOSS_HEROD);
                default:
                    return InstanceScript::GetGuidData(kGuidBossBase + bossId);
            }
        }

        Creature* BossCreature(uint32 bossId)
        {
            ObjectGuid const guid = BossGuid(bossId);
            return guid ? instance->GetCreature(guid) : nullptr;
        }

        bool CouncilDead()
        {
            for (ObjectGuid const& guid : { BossGuid(BOSS_COUNCIL), InstanceScript::GetGuidData(kGuidAzshir) })
            {
                Creature* unit = guid ? instance->GetCreature(guid) : nullptr;
                if (!unit || (unit->IsAlive() && !unit->isDying()))
                    return false;
            }
            return true;
        }

        // The hard mode flag of a kill slot (lit or not).
        bool HardModeLit(uint32 killSlot) const
        {
            switch (killSlot)
            {
                case BOSS_DESECRATION:  return _desecration != 0;
                case BOSS_HERESY:       return _heresy != 0;
                case BOSS_CALL_TO_ARMS: return _herodTaunted != 0;
                case BOSS_THE_TRUTH:    return _torchPulled != 0;
                default:                return false;
            }
        }

        // Item variants IV7 (the Deadmines pattern): the heroic lootid holds the hard mode list at LootMode 2; the bit
        // rides the boss's loot mode while the flag is lit and he is not dead yet (rule 1: at the trigger, at the
        // pull).
        void ApplyHardModeLoot(uint32 bossId)
        {
            uint32 const killSlot = HardModeKillSlot(bossId);
            if (killSlot >= kBossCount)
                return;
            if (Creature* boss = BossCreature(bossId))
                DungeonKit::SetHardModeLoot(boss, HardModeLit(killSlot) && Slot(bossId) != DONE);
        }

        void OnSlotChanged(uint32 id, uint32 before, uint32 state)
        {
            // An end boss's kill with its hard mode lit records the hard mode kill (the loot is already filled:
            // Unit::Kill runs before JustDied); a pull carries the loot bit.
            uint32 const killSlot = HardModeKillSlot(id);
            if (killSlot < kBossCount)
            {
                if (state == DONE && HardModeLit(killSlot))
                {
                    LOG_INFO(kLog, "sm instance {} killed", kBossNames[killSlot]);
                    ForceBossState(killSlot, DONE);
                }
                else if (state == IN_PROGRESS)
                    ApplyHardModeLoot(id);
            }

            switch (id)
            {
                case BOSS_HEROD:
                    // The close is D11's SealedArena (3 s after the pull, stragglers pulled in: section 7 #22 A);
                    // the instance opens it on his death or a reset (the seal's Release opens it too).
                    if (HerodsDoorMoveFor(before, state) == DoorMove::Open)
                        OpenDoorLatched(GetGameObject(GO_HERODS_DOOR));
                    if (GameObject* lever = GetGameObject(GO_HERODS_LEVER))
                        ApplyHerodsLever(lever);
                    break;
                case BOSS_LAST_STAND:
                    if (!kWave2Bound)
                        break;
                    if (state == DONE)
                        OnLastStandDone();
                    else if (state == IN_PROGRESS)
                        if (Creature* mograine = BossCreature(BOSS_LAST_STAND))
                            if (mograine->IsAIEnabled && mograine->AI())
                                mograine->AI()->DoAction(ACTION_SM_LAST_STAND_START);
                    break;
                default:
                    break;
            }

            if (state == DONE)
                RefreshPortals();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Cathedral (stock while wave 2 is unbound; the Last Stand and Whitemane once it binds)
        // ------------------------------------------------------------------------------------------------------------

        // Stock (instance_scarlet_monastery.cpp SetData case TYPE_MOGRAINE_AND_WHITE_EVENT, 7549eb59b avarishd and
        // ebe89b875 Alexandru-Mihai Maftei): IN_PROGRESS pulls the six Cathedral entries within 80 yd of Mograine; FAIL
        // despawns or resets the pair by who is alive. Wave 1 only (the stock SmartAI is its only writer).
        void StockCathedral(uint32 data)
        {
            if (data == IN_PROGRESS)
            {
                if (Creature* mograine = instance->GetCreature(InstanceScript::GetGuidData(DATA_MOGRAINE)))
                {
                    std::list<Creature*> creatureList;
                    for (uint32 entry : { NPC_SCARLET_MONK, NPC_SCARLET_ABBOT, NPC_SCARLET_CHAMPION,
                        NPC_SCARLET_CENTURION, NPC_SCARLET_WIZARD, NPC_SCARLET_CHAPLAIN })
                        GetCreatureListWithEntryInGrid(creatureList, mograine, entry, kStockCathedralPullRange);
                    for (Creature* creature : creatureList)
                        if (creature && creature->AI())
                            creature->AI()->AttackStart(mograine->GetVictim());
                }
                _encounter = IN_PROGRESS;
            }
            if (data == FAIL)
            {
                Creature* whitemane = instance->GetCreature(InstanceScript::GetGuidData(DATA_WHITEMANE));
                Creature* mograine = instance->GetCreature(InstanceScript::GetGuidData(DATA_MOGRAINE));
                if (!whitemane || !mograine)
                    return;

                if (whitemane->IsAlive() && mograine->IsAlive())
                {
                    // Whitemane stands next to Mograine's corpse once she came out: she does not reset alone.
                    if (whitemane->IsEngaged() || whitemane->IsInEvadeMode())
                        whitemane->DespawnOnEvade(20s);
                    mograine->DespawnOnEvade(20s);
                    _encounter = NOT_STARTED;
                    return;
                }
                if (!whitemane->IsAlive())
                {
                    mograine->DespawnOrUnsummon();
                    _encounter = data;
                    return;
                }
                if (whitemane->IsAlive() && !mograine->IsAlive())
                {
                    whitemane->DespawnOnEvade(20s);
                    _encounter = data;
                    return;
                }
                _encounter = data;
            }
            if (data == DONE)
                _encounter = DONE;
        }

        // Stock (SetData case TYPE_ASHBRINGER_EVENT, b70b14ed6 daobashun) behind the section 7 #16 A guard. The flag is
        // set before the door opens, so the Chapel Door's AI does not read the opening as the Last Stand's start.
        void SetAshbringer(uint32 data)
        {
            if (data == IN_PROGRESS)
            {
                if (!AshbringerAllowed(Slot(BOSS_LAST_STAND), Slot(BOSS_WHITEMANE), Slot(BOSS_THORNE), _encounter))
                {
                    ++_ashbringerRefused;
                    LOG_INFO(kLog, "sm instance ashbringer refused (a Cathedral encounter is in progress)");
                    return;
                }
                _ashbringer = true;
                _ashencounter = data;
                LOG_INFO(kLog, "sm instance ashbringer event");

                // The Ashbringer incident did not sniff out any data from Whitemane (stock comment).
                if (Creature* whitemane = instance->GetCreature(InstanceScript::GetGuidData(DATA_WHITEMANE)))
                    if (whitemane->IsAlive() && !whitemane->IsEngaged())
                        whitemane->DespawnOrUnsummon();

                OpenDoorLatched(GetGameObject(DATA_DOOR_CHAPEL));

                for (ObjectGuid const& guid : _ashbringerNpcs)
                    if (Creature* npc = instance->GetCreature(guid))
                        if (npc->IsAlive() && !npc->IsEngaged())
                            npc->SetFaction(kFactionFriendly);

                // The cameo (HANDOFF section 10, R-1-KIT m-1 default c): told to Mograine here, on acceptance only (AT
                // 4089's rows 2-3 that told him whatever the guard said are dropped by W2-SETUP's rev).
                if (Creature* mograine = BossCreature(BOSS_LAST_STAND))
                    if (mograine->IsAlive() && mograine->IsAIEnabled && mograine->AI())
                        mograine->AI()->DoAction(ACTION_SM_ASHBRINGER);
                SaveToDB();
                return;
            }
            _ashencounter = data;
        }

        // The Ashbringer event despawned Whitemane; after a reload (or her respawn) she goes again once she is in the
        // world and out of combat (R-1-KIT m-2; not from OnCreatureCreate: no despawn while she is being added).
        void HoldAshbringerDespawn()
        {
            if (!_ashbringer)
                return;
            if (Creature* whitemane = instance->GetCreature(InstanceScript::GetGuidData(DATA_WHITEMANE)))
                if (whitemane->IsAlive() && !whitemane->IsEngaged())
                    whitemane->DespawnOrUnsummon();
        }

        void OnChapelDoorOpened(bool byUnit)
        {
            if (_ashbringer)
                return;     // the Ashbringer path opened it
            if (!LastStandStartAllowed(Slot(BOSS_LAST_STAND), _ashbringer))
                return;
            StartLastStand(byUnit ? "door" : "door (no unit)");
        }

        void StartLastStand(char const* how)
        {
            LOG_INFO(kLog, "sm instance last stand starts ({})", how);
            ForceBossState(BOSS_LAST_STAND, IN_PROGRESS);
        }

        // D13's protocol: DONE when Mograine falls at 1% (LethalGuard), FAIL / NOT_STARTED when the stand resets;
        // IN_PROGRESS starts it like the door (D13's own start path, if it has one).
        void SetLastStand(uint32 data)
        {
            if (!kWave2Bound)
                return;
            uint32 const current = Slot(BOSS_LAST_STAND);
            switch (data)
            {
                case IN_PROGRESS:
                    if (LastStandStartAllowed(current, _ashbringer))
                        StartLastStand("d13");
                    break;
                case DONE:
                    if (current != DONE)
                        ForceBossState(BOSS_LAST_STAND, DONE);
                    break;
                case FAIL:
                case NOT_STARTED:
                    if (current == IN_PROGRESS)
                    {
                        LOG_INFO(kLog, "sm instance last stand reset (the crossing re-arms while the door is open)");
                        ForceBossState(BOSS_LAST_STAND, NOT_STARTED);
                    }
                    break;
                default:
                    break;
            }
        }

        // The Last Stand is DONE: its credit by spell, the High Inquisitor's Door opens, Whitemane walks out to her
        // vigil, Mograine stays fallen (D13 / D14 do the walking and the kneeling).
        void OnLastStandDone()
        {
            Creature* mograine = BossCreature(BOSS_LAST_STAND);
            Unit* source = mograine;
            if (!source)
                for (MapReference const& ref : instance->GetPlayers())
                    if (Player* player = ref.GetSource())
                    {
                        source = player;
                        break;
                    }
            LOG_INFO(kLog, "sm instance last stand done: credit spell {}", kSpellLastStandCredit);
            if (source)     // the kit's spell credit (KT-SM, section 3.11 #3), plus the heroic bind
                DungeonKit::CreditEncounterBySpell(instance, kSpellLastStandCredit, source, kLogDungeon, "last-stand");
            OpenDoorLatched(GetGameObject(DATA_DOOR_WHITEMANE));
            if (mograine && mograine->IsAIEnabled && mograine->AI())
                mograine->AI()->DoAction(ACTION_SM_MOGRAINE_FALLEN);
            if (Creature* whitemane = BossCreature(BOSS_WHITEMANE))
                if (whitemane->IsAIEnabled && whitemane->AI())
                    whitemane->AI()->DoAction(ACTION_SM_WHITEMANE_VIGIL);
        }

        bool ChapelDoorOpen()
        {
            GameObject* door = GetGameObject(DATA_DOOR_CHAPEL);
            return door && door->GetGoState() == GO_STATE_ACTIVE;
        }

        // Section 7 #19 A: after a wipe the door stays open; a living player crossing the door line restarts the stand.
        void CrossingCheck()
        {
            if (!CrossingRestartArmed(Slot(BOSS_LAST_STAND), ChapelDoorOpen(), _ashbringer))
                return;
            for (MapReference const& ref : instance->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!player || !player->IsAlive() || player->IsGameMaster())
                    continue;
                if (InCrossingLine({ player->GetPositionX(), player->GetPositionY() }, player->GetPositionZ()))
                {
                    LOG_INFO(kLog, "sm instance last stand restart: {} crossed the door line", player->GetName());
                    StartLastStand("crossing");
                    return;
                }
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Herod's Door and lever (section 7 #14 A, HB0)
        // ------------------------------------------------------------------------------------------------------------
        // Opens a door the way the stock Ashbringer path does (R-1-KIT M-2): open, in use and activated. A door opened
        // with HandleGameObject alone stays GO_READY, so one click closes it; with autoCloseTime 0 nothing resets it
        // and UseDoorOrButton (the click, the lever's SmartAI) refuses anything but GO_READY, so it would stay shut.
        static void OpenDoorLatched(GameObject* go)
        {
            if (!go)
                return;
            go->SetGoState(GO_STATE_ACTIVE);
            go->SetLootState(GO_ACTIVATED);
            go->SetGameObjectFlag(GO_FLAG_IN_USE);
        }

        void ApplyHerodsLever(GameObject* lever)
        {
            if (HerodsLeverUsable(Slot(BOSS_HEROD)))
                lever->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            else
                lever->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The wing portals (section 7 #15 A): stood from the slots (and the GM's), restored once their grid is loaded
        // ------------------------------------------------------------------------------------------------------------
        void RefreshPortals()
        {
            uint32 const mask = PortalsOpenMask(States()) | _gmPortals;
            for (std::size_t i = 0; i < kPortals.size(); ++i)
            {
                WingPortal const& p = kPortals[i];
                GameObject* go = _portals[i] ? instance->GetGameObject(_portals[i]) : nullptr;
                if (mask & PortalBit(p.id))
                {
                    if (go || !instance->IsGridLoaded(p.spot.x, p.spot.y))
                        continue;
                    go = instance->SummonGameObject(GO_SM_WING_PORTAL, p.spot.x, p.spot.y, p.spot.z, p.spot.o, 0.f,
                        0.f, 0.f, 0.f, 0);
                    if (!go)
                        continue;
                    _portals[i] = go->GetGUID();
                    DungeonKit::LogMechanic(kLogDungeon, "portal", p.name, "stands");
                }
                else if (go)
                {
                    go->DespawnOrUnsummon();
                    _portals[i].Clear();
                }
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // The hard mode triggers (section 3.7; the effects are the hard mode WPs': the instance keeps the flags)
        // ------------------------------------------------------------------------------------------------------------
        void LightHardMode(uint32 killSlot, char const* how)
        {
            if (HardModeLit(killSlot))
                return;
            switch (killSlot)
            {
                case BOSS_DESECRATION:
                    _desecration = 1;
                    break;
                case BOSS_HERESY:
                    _doanPages = kDoanPagesAll;
                    _heresy = 1;
                    break;
                case BOSS_CALL_TO_ARMS:
                    _herodTaunted = 1;
                    break;
                case BOSS_THE_TRUTH:
                    _torchPulled = 1;
                    break;
                default:
                    return;
            }
            LOG_INFO(kLog, "sm instance {} lit ({})", kBossNames[killSlot], how);
            ApplyHardModeLoot(HardModeBoss(killSlot));
            SaveToDB();
        }

        // D4H's stones: SetData(DATA_DESECRATION_TOUCH, stone 0-3); D4H reads DATA_DESECRATION_RESULT right after.
        void TouchGravestone(uint32 stone)
        {
            if (!DesecrationTouchAllowed(instance->IsHeroic(), Slot(BOSS_THALNOS), Slot(BOSS_COUNCIL),
                _desecration != 0) || stone >= kDesecrationStones)
            {
                _desecrationResult = DesecrationVerdict::Refused;
                return;
            }
            if (std::find(_touchOrder.begin(), _touchOrder.begin() + _touchCount, stone)
                != _touchOrder.begin() + _touchCount)
            {
                _desecrationResult = DesecrationVerdict::Repeat;
                return;
            }
            _touchOrder[_touchCount++] = stone;
            _desecrationResult = DesecrationVerdict::None;
            if (_touchCount < kDesecrationStones)
                return;

            _desecrationResult = JudgeDesecration(_touchOrder);
            _touchCount = 0;
            _touchOrder.fill(0);
            LOG_INFO(kLog, "sm instance desecration judged: {}",
                _desecrationResult == DesecrationVerdict::Right ? "right" : "wrong");
            if (_desecrationResult == DesecrationVerdict::Right)
                LightHardMode(BOSS_DESECRATION, "stones");
        }

        // D8H's pages: SetData(DATA_DOAN_PAGE_READ, page 0-3), each once per instance; the fourth lights the Heresy.
        void ReadDoanPage(uint32 page)
        {
            if (!DoanPageAllowed(instance->IsHeroic(), Slot(BOSS_DOAN), _doanPages, page))
                return;
            _doanPages |= 1u << page;
            LOG_INFO(kLog, "sm instance doan page {} read ({} of {})", page, DoanPagesRead(_doanPages), kDoanPages);
            if (_doanPages == kDoanPagesAll)
                LightHardMode(BOSS_HERESY, "pages");
            else
                SaveToDB();
        }

        EventMap events;
        bool _settled = false;
        bool _bypassGuard = false;
        bool _gmSlotWrite = false;

        // Stock fields (their stock meaning)
        uint32 _encounter = 0;          // the stock Cathedral pair (wave 1: SetData(1) / SetData(6)); not saved (stock)
        uint32 _ashencounter = 0;       // GetData(2): AT 4089's condition reads it as 0
        GuidSet _ashbringerNpcs;

        // The Horseman (private; never saved)
        uint32 _horsemanState = 0;

        // Saved run data
        bool _ashbringer = false;
        uint32 _desecration = 0;
        uint32 _doanPages = 0;
        uint32 _heresy = 0;
        uint32 _herodTaunted = 0;
        uint32 _torchPulled = 0;

        // Per attempt (not saved)
        std::array<uint32, kDesecrationStones> _touchOrder{};
        uint32 _touchCount = 0;
        DesecrationVerdict _desecrationResult = DesecrationVerdict::None;
        uint32 _ashbringerRefused = 0;

        // The portals (tracked by hand: summoned)
        std::array<ObjectGuid, kPortals.size()> _portals{};
        uint32 _gmPortals = 0;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_scarlet_monastery_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_scarlet_monastery_rework()
{
    new instance_scarlet_monastery_rework();
    RegisterDungeonReworkGameObjectAI(go_sm_chapel_door, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_sm_wing_portal, ScarletMonasteryRework::kInstanceScriptName);
}
