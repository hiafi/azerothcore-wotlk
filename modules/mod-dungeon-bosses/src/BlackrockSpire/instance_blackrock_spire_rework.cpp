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

// The Blackrock Spire build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_blackrock_spire` (section 7 #2): modules load after the core scripts, and a database-bound script
// registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 229's
// instance_template row is untouched and the stock InstanceMapScript is replaced at load. The other scripts of the
// stock folder stay registered and keep working, none of them copied: their AIs check the instance name
// (GetBlackrockSpireAI), which is unchanged. That covers boss_lord_valthalak (BossAI on 14) and boss_mor_grayhoof
// (BossAI on 24, which persists now), npc_vaelastrasz_the_red and spell_blackrock_spire_call_of_vaelastrasz
// (DATA_VAELASTRASZ 25), the area triggers
// at_dragonspire_hall (SetData(1, 2046)), at_blackrock_stadium (Rend), the Beast's 2066 / 2067 and the Scarshield
// Infiltrator's, and the stock bosses of the wave not yet bound (wave 2: Emberseer, Solakar, Rend, Gyth, the Beast,
// Drakkisath).
//
// Re-implemented from the stock instance (src/server/scripts/EasternKingdoms/BlackrockMountain/BlackrockSpire/
// instance_blackrock_spire.cpp at Playerbot c699808d5, which stays untouched; its last upstream change is 8eb009fdf,
// Kitzunu, "east-const", AzerothCore #26492, after 2c4b7c3cd, Andrew, "register macros", #25178, and 53238a68d /
// 9c49349e1, 天鹭, #23141 / #23121; the file goes back to Francesco Borzì's and Yehonal's first commits, with Kargatum,
// Nefertumm and others): the boss slots and their stock data ids, the minion and door data, the Dragonspire room check
// (the seven hall runes go DONE as their Blackhand packs die, then the room and its two doors), the Blackrock Altar
// (event 4884: Emberseer's cage), the Urok pile (event 4845 and the challenge reset on SetData(4, FAIL)), the five-wave
// Solakar event (SetData(23, IN_PROGRESS)), Rend's respawn on a FAIL with Nefarius's line 11, the Vaelastrasz data, the
// Beast's skinning surprise, the GetGuidData keys (boss data ids 0-13 and the stock GO entries), and the stock save
// "BRS", which still loads. Each upstream merge re-diffs the stock file against 8eb009fdf (handoff section 6).
//
// What is new: 28 boss states (BlackrockSpireRework.h; Solakar's 23 and Mor Grayhoof's 24 persist, 26 and 27 are the
// hard mode kills); the rune room hardening (section 10: the room check also starts on its own when a player stands in
// the hall and the room is not DONE, on load, on entry and on a watch; a DONE rune is never snapshotted again; a rune
// whose grid is not loaded is never closed; SetData(2046, x) stays a no-op); the stock notes fixed (SP notes 1, 3, 4: a
// failed Solakar event starts again, a boss that is not a BossAI still records its death, Emberseer's Out door is door
// data and the room check no longer re-opens the In door twice); the saved insult, Urok pile and Solakar state; the war
// horn and the General's Army per-pull flags with their kill slots and loot bits; the "BRW" save string; the Solakar
// event rewritten by B11 (one pair, Solakar at 30 s, a working reset; Father Flame 175245 is B11's go_brs_father_flame,
// boss_solakar_flamewreath_rework.cpp). While kWave2Bound is false the UBRS bosses run stock and their instance paths
// are the stock ones.

#include "BlackrockSpireRework.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GridNotifiers.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "RendGythLogic.h"
#include "ScriptedCreature.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <list>
#include <optional>

using namespace BlackrockSpireRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    // The Elite Guards are Drakkisath's (stock).
    MinionData const minionData[] =
    {
        { NPC_CHROMATIC_ELITE_GUARD, BOSS_DRAKKISATH },
        { 0,                         0               }
    };

    // Stock: Rend's exit and Drakkisath's two gates. New: Emberseer's Out door opens once he is DONE (SP note 4; the
    // stock boss script opens it on his death too, and the passage keeps it open on every reload).
    DoorData const doorData[] =
    {
        { GO_GYTH_EXIT_DOOR,    BOSS_REND,          DOOR_TYPE_PASSAGE },
        { GO_DRAKKISATH_DOOR_1, BOSS_DRAKKISATH,    DOOR_TYPE_PASSAGE },
        { GO_DRAKKISATH_DOOR_2, BOSS_DRAKKISATH,    DOOR_TYPE_PASSAGE },
        { GO_EMBERSEER_OUT,     BOSS_EMBERSEER,     DOOR_TYPE_PASSAGE },
        { 0,                    0,                  DOOR_TYPE_ROOM    }
    };

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the spawned bosses under their stock data ids
    // (the stock GetGuidData keys 0-13; the Beast's area triggers read 12) and the single objects under their entries
    // (the stock GetGuidData keys). Urok, Gizrul, Gyth, Solakar, Rend (stock's own rule while Gyth fights), Nefarius,
    // the Urok challenge and its circles are tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_OMOKK,        BOSS_OMOKK       },
        { NPC_VOSHGAJIN,    BOSS_VOSHGAJIN   },
        { NPC_VOONE,        BOSS_VOONE       },
        { NPC_SMOLDERWEB,   BOSS_SMOLDERWEB  },
        { NPC_ZIGRIS,       BOSS_ZIGRIS      },
        { NPC_HALYCON,      BOSS_HALYCON     },
        { NPC_WYRMTHALAK,   BOSS_WYRMTHALAK  },
        { NPC_EMBERSEER,    BOSS_EMBERSEER   },
        { NPC_BEAST,        BOSS_BEAST       },
        { NPC_DRAKKISATH,   BOSS_DRAKKISATH  },
        { 0,                0                }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_EMBERSEER_IN,      GO_EMBERSEER_IN      },
        { GO_EMBERSEER_DOORS,   GO_EMBERSEER_DOORS   },
        { GO_EMBERSEER_OUT,     GO_EMBERSEER_OUT     },
        { GO_HALL_RUNE_1,       GO_HALL_RUNE_1       },
        { GO_HALL_RUNE_2,       GO_HALL_RUNE_2       },
        { GO_HALL_RUNE_3,       GO_HALL_RUNE_3       },
        { GO_HALL_RUNE_4,       GO_HALL_RUNE_4       },
        { GO_HALL_RUNE_5,       GO_HALL_RUNE_5       },
        { GO_HALL_RUNE_6,       GO_HALL_RUNE_6       },
        { GO_HALL_RUNE_7,       GO_HALL_RUNE_7       },
        { GO_EMBERSEER_RUNE_1,  GO_EMBERSEER_RUNE_1  },
        { GO_EMBERSEER_RUNE_2,  GO_EMBERSEER_RUNE_2  },
        { GO_EMBERSEER_RUNE_3,  GO_EMBERSEER_RUNE_3  },
        { GO_EMBERSEER_RUNE_4,  GO_EMBERSEER_RUNE_4  },
        { GO_EMBERSEER_RUNE_5,  GO_EMBERSEER_RUNE_5  },
        { GO_EMBERSEER_RUNE_6,  GO_EMBERSEER_RUNE_6  },
        { GO_EMBERSEER_RUNE_7,  GO_EMBERSEER_RUNE_7  },
        { GO_GYTH_ENTRY_DOOR,   GO_GYTH_ENTRY_DOOR   },
        { GO_UROK_PILE,         GO_UROK_PILE         },
        { GO_BLACKROCK_ALTAR,   GO_BLACKROCK_ALTAR   },
        { GO_FATHER_FLAME,      GO_FATHER_FLAME      },
        { 0,                    0                    }
    };

    enum BrsInstanceEvents
    {
        EVENT_ROOM_STORE    = 1,    // stock EVENT_DRAGONSPIRE_ROOM_STORE
        EVENT_ROOM_CHECK    = 2,    // stock EVENT_DRAGONSPIRE_ROOM_CHECK
        EVENT_SOLAKAR_ARRIVE = 3,   // B11: Solakar shows himself 30 s after Father Flame is taken
        EVENT_ROOM_WATCH    = 4,    // the self-start (section 10)
        EVENT_HALYCON_RESPAWN = 5,  // B7: a dead Halycon after a restart mid-attempt
    };

    enum StockTexts
    {
        SAY_NEFARIUS_REND_WIPE      = 11,
        SAY_SOLAKAR_FIRST_HATCHER   = 0,
        SAY_FINKLE_GANG             = 0,
    };

    uint32 constexpr kSpellFinkleIsEinhorn = 16710;

    // The Blackhand packs of the hall runes (stock DragonspireMobs).
    std::array<uint32, 3> constexpr kDragonspireMobs{ { NPC_BLACKHAND_DREADWEAVER, NPC_BLACKHAND_SUMMONER,
        NPC_BLACKHAND_VETERAN } };
}

class instance_blackrock_spire_rework : public InstanceMapScript
{
public:
    instance_blackrock_spire_rework() : InstanceMapScript(kInstanceScriptName, kMapBlackrockSpire) { }

    struct instance_blackrock_spire_rework_InstanceMapScript : public InstanceScript
    {
        explicit instance_blackrock_spire_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadMinionData(minionData);
            LoadDoorData(doorData);
            LoadObjectData(creatureData, gameObjectData);
            _runeSnapshotted.fill(false);
            // The self-start watch runs from the first tick (a new instance: the first player may enter in the hall).
            events.ScheduleEvent(EVENT_ROOM_WATCH, Milliseconds(kRoomWatchMs));
        }

        void OnPlayerEnter(Player* player) override
        {
            InstanceScript::OnPlayerEnter(player);
            ScheduleRoomWatch(1s);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            switch (creature->GetEntry())
            {
                case NPC_UROK_MAGUS:
                case NPC_UROK_ENFORCER:
                    _urokMobs.push_back(creature->GetGUID());
                    break;
                case NPC_UROK:
                    _urok = creature->GetGUID();
                    break;
                case NPC_GIZRUL:
                    _gizrul = creature->GetGUID();
                    break;
                case NPC_HALYCON:
                    // B7: created dead (a restart or a grid reload after she fell first): respawned a moment later
                    // unless the pair is DONE or Gizrul still fights.
                    if (!creature->IsAlive() && GetBossState(BOSS_HALYCON) != DONE)
                    {
                        events.CancelEvent(EVENT_HALYCON_RESPAWN);
                        events.ScheduleEvent(EVENT_HALYCON_RESPAWN, Milliseconds(kHalyconRespawnDelayMs));
                    }
                    break;
                case NPC_GYTH:
                    _gyth = creature->GetGUID();
                    break;
                case NPC_SOLAKAR:
                    _solakar = creature->GetGUID();
                    break;
                case NPC_EMBERSEER:
                    if (GetBossState(BOSS_EMBERSEER) == DONE)
                        creature->DisappearAndDie();
                    break;
                case NPC_REND:
                    // Stock: the Rend that Gyth carries is not the one the instance tracks. B12 (wave 2): there is one
                    // Rend, the balcony spawn, all show long.
                    if (kWave2Bound || GetBossState(BOSS_GYTH) != IN_PROGRESS)
                        _rend = creature->GetGUID();
                    if (RendShowOver())
                        creature->DisappearAndDie();
                    break;
                case NPC_LORD_VICTOR_NEFARIUS:
                case NPC_BRS_NEFARIUS:
                    _nefarius = creature->GetGUID();
                    if (RendShowOver())
                        creature->DisappearAndDie();
                    break;
                case NPC_FINKLE_EINHORN:
                    if (creature->IsAIEnabled && creature->AI())
                        creature->AI()->Talk(SAY_FINKLE_GANG);
                    break;
                case NPC_WYRMTHALAK:
                    ApplyHardModeLoot(creature, _warHorn, BOSS_WYRMTHALAK);
                    break;
                case NPC_DRAKKISATH:
                    ApplyHardModeLoot(creature, _generalsArmy, BOSS_DRAKKISATH);
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
                case GO_EMBERSEER_IN:
                    HandleGameObject(ObjectGuid::Empty, GetBossState(BOSS_DRAGONSPIRE_ROOM) == DONE, go);
                    break;
                case GO_EMBERSEER_DOORS:
                    if (GetBossState(BOSS_DRAGONSPIRE_ROOM) == DONE)
                        HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case GO_EMBERSEER_RUNE_1:
                case GO_EMBERSEER_RUNE_2:
                case GO_EMBERSEER_RUNE_3:
                case GO_EMBERSEER_RUNE_4:
                case GO_EMBERSEER_RUNE_5:
                case GO_EMBERSEER_RUNE_6:
                case GO_EMBERSEER_RUNE_7:
                    if (GetBossState(BOSS_EMBERSEER) == DONE)
                        HandleGameObject(ObjectGuid::Empty, false, go);
                    break;
                case GO_GYTH_ENTRY_DOOR:
                    if (RendShowOver())
                        HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case GO_UROK_CIRCLE:
                    _urokCircles.push_back(go->GetGUID());
                    break;
                case GO_UROK_CHALLENGE:
                    _urokChallenge = go->GetGUID();
                    break;
                case GO_FATHER_FLAME:
                case GO_ROOKERY_EGG:
                    RespawnSolakarObject(go);
                    break;
                default:
                    if (std::optional<uint32> const rune = HallRuneIndex(go->GetEntry()))
                        if (GetBossState(BOSS_HALL_RUNE_1 + *rune) == DONE)
                            HandleGameObject(ObjectGuid::Empty, false, go);
                    break;
            }
        }

        void OnGameObjectRemove(GameObject* go) override
        {
            InstanceScript::OnGameObjectRemove(go);

            if (go->GetEntry() == GO_UROK_CHALLENGE && go->GetGUID() == _urokChallenge)
                _urokChallenge.Clear();
        }

        void CreatureLooted(Creature* creature, LootType loot) override
        {
            // Stock: skinning the Beast reveals Finkle Einhorn.
            if (creature->GetEntry() == NPC_BEAST && loot == LOOT_SKINNING)
                creature->CastSpell(creature, kSpellFinkleIsEinhorn, true);
        }

        void OnUnitDeath(Unit* unit) override
        {
            Creature* creature = unit ? unit->ToCreature() : nullptr;
            if (!creature)
                return;

            // A boss that is not a BossAI (a stock SmartAI boss: Gizrul, Vosh'gajin and Smolderweb before wave 1 binds
            // them, or a data rollback) sets no boss state itself: its death does it here (SP note 3).
            std::optional<uint32> const boss = BossOfEntry(creature->GetEntry());
            if (!boss || GetBossState(*boss) == DONE)
                return;
            if (creature->IsAIEnabled && dynamic_cast<BossAI*>(creature->AI()))
                return;     // a BossAI: its own _JustDied sets DONE
            LOG_INFO(kLog, "brs instance stock boss {} died: boss state {} DONE", creature->GetEntry(), *boss);
            SetBossState(*boss, DONE);
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            switch (type)
            {
                case BOSS_UROK:
                    return _urok;
                case BOSS_GIZRUL:
                    return _gizrul;
                case BOSS_REND:
                    return _rend;
                case BOSS_GYTH:
                    return _gyth;
                case BOSS_SOLAKAR:
                    return _solakar;
                case GO_UROK_CHALLENGE:
                    return _urokChallenge;
                default:
                    return InstanceScript::GetGuidData(type);
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Boss states
        // ------------------------------------------------------------------------------------------------------------
        bool SetBossState(uint32 id, EncounterState state) override
        {
            uint32 const before = id < kBossCount ? uint32(GetBossState(id)) : uint32(TO_BE_DECIDED);
            if (!InstanceScript::SetBossState(id, state))
                return false;

            switch (id)
            {
                case BOSS_OMOKK:
                case BOSS_UROK:
                    if (id == BOSS_UROK && state == DONE)
                        _pileInUse = false;
                    UpdateUrokPile();
                    break;
                case BOSS_WYRMTHALAK:
                    if (state == DONE && _warHorn)
                    {
                        // The kill flag (the loot is already filled: Unit::Kill runs before JustDied).
                        LOG_INFO(kLog, "brs instance war horn killed");
                        _warHorn = 0;
                        SetBossState(BOSS_WAR_HORN, DONE);
                    }
                    else if (AttemptEnded(before, state) && _warHorn)
                    {
                        LOG_INFO(kLog, "brs instance war horn reset (the attempt ended)");
                        _warHorn = 0;
                    }
                    ApplyHardModeLoot(GetCreature(BOSS_WYRMTHALAK), _warHorn, BOSS_WYRMTHALAK);
                    break;
                case BOSS_DRAKKISATH:
                    if (state == DONE && _generalsArmy)
                    {
                        LOG_INFO(kLog, "brs instance general's army killed");
                        _generalsArmy = 0;
                        SetBossState(BOSS_GENERALS_ARMY, DONE);
                    }
                    else if (AttemptEnded(before, state) && _generalsArmy)
                    {
                        LOG_INFO(kLog, "brs instance general's army reset (the attempt ended)");
                        _generalsArmy = 0;
                    }
                    ApplyHardModeLoot(GetCreature(BOSS_DRAKKISATH), _generalsArmy, BOSS_DRAKKISATH);
                    break;
                case BOSS_SOLAKAR:
                    if (state == DONE)
                    {
                        // B11: the event is over for good; what is left of the pair goes with it.
                        _solakarEvent = DONE;
                        events.CancelEvent(EVENT_SOLAKAR_ARRIVE);
                        DespawnSolakarSummons(false);
                    }
                    break;
                case BOSS_REND:
                    // B12 (R-2 B-1): the arena entry door is shut only while the show runs; it opens on the kill (the
                    // arena's only way out, as stock JustDied), the wipe and the reset.
                    static_assert(uint32(IN_PROGRESS) == BrsRendGyth::kRendStateInProgress);
                    if (kWave2Bound)
                        HandleGameObject(ObjectGuid::Empty, BrsRendGyth::EntryDoorOpen(uint32(state)),
                            GetGameObject(GO_GYTH_ENTRY_DOOR));
                    // Stock: a failed Rend event respawns him on the balcony, and Nefarius taunts.
                    if (state == FAIL)
                    {
                        if (Creature* rend = instance->GetCreature(_rend))
                            rend->Respawn(true);
                        if (Creature* nefarius = instance->GetCreature(_nefarius))
                            if (nefarius->IsAIEnabled && nefarius->AI())
                                nefarius->AI()->Talk(SAY_NEFARIUS_REND_WIPE);
                    }
                    break;
                default:
                    break;
            }
            return true;
        }

        void ProcessEvent(WorldObject* /*obj*/, uint32 eventId) override
        {
            switch (eventId)
            {
                case kEventBlackrockAltar:
                    // Stock: the altar starts Emberseer's cage while he waits (B10 keeps the SetData(1, 1) protocol or
                    // asks for a change).
                    if (GetBossState(BOSS_EMBERSEER) == NOT_STARTED)
                        if (Creature* emberseer = GetCreature(BOSS_EMBERSEER))
                            if (emberseer->IsAIEnabled && emberseer->AI())
                                emberseer->AI()->SetData(1, 1);
                    break;
                case kEventUrokPile:
                    // Stock path (the pile's SmartGO): the challenge starts. B5's GO script replaces it.
                    if (GetBossState(BOSS_UROK) == NOT_STARTED)
                    {
                        SetBossState(BOSS_UROK, IN_PROGRESS);
                        _pileInUse = true;
                        UpdateUrokPile();
                        if (GameObject* pile = GetGameObject(GO_UROK_PILE))
                            pile->SetLootState(GO_JUST_DEACTIVATED);
                    }
                    break;
                default:
                    break;
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Data
        // ------------------------------------------------------------------------------------------------------------
        void SetData(uint32 type, uint32 data) override
        {
            switch (type)
            {
                case DATA_AREATRIGGER:
                    // at_dragonspire_hall. Any other type, 2046 included (mod-dungeon-clear's SetData(2046, 26)),
                    // falls through to the default: a no-op (section 10).
                    if (data == kAreaTriggerDragonspireHall && GetBossState(BOSS_DRAGONSPIRE_ROOM) != DONE)
                        ScheduleRoomStore("area trigger 2046");
                    return;
                case DATA_ROOM_CHECK:
                    if (data && GetBossState(BOSS_DRAGONSPIRE_ROOM) != DONE)
                        ScheduleRoomStore("gm test");
                    return;
                case DATA_UROK_EVENT:
                    if (data == FAIL)
                        ResetUrokChallenge();
                    return;
                case DATA_SOLAKAR_EVENT:
                    WriteSolakarEvent(data);
                    break;
                case DATA_VAELASTRASZ:
                    _vaelastrasz = data;
                    return;
                case DATA_NEF_INSULTED:
                    if (!InsultChangeAllowed(data, kWave2Bound, GetBossState(BOSS_DRAKKISATH)))
                    {
                        LOG_DEBUG(kLog, "brs instance insult={} refused", data);
                        return;
                    }
                    _nefInsulted = data ? 1 : 0;
                    LOG_INFO(kLog, "brs instance insult={}", _nefInsulted);
                    break;
                case DATA_UROK_PILE:
                    if (data == PILE_IN_USE && _urokPile == PILE_READY)
                        _pileInUse = true;
                    else if (data == PILE_READY && _urokPile == PILE_IN_USE)
                        _pileInUse = false;
                    else
                    {
                        LOG_DEBUG(kLog, "brs instance urok pile {} -> {} refused", _urokPile, data);
                        return;
                    }
                    UpdateUrokPile();
                    break;
                case DATA_SOLAKAR_FLAME:
                    if (data > kSolakarFlameMax)
                        return;
                    _solakarFlame = data;
                    if (!SolakarFlameSaved(data))
                        return;     // a toss, a snatch or a drop: per attempt, not saved
                    break;
                case DATA_WAR_HORN:
                    if (!WarHornChangeAllowed(data, instance->IsHeroic(), GetBossState(BOSS_WYRMTHALAK)))
                    {
                        LOG_DEBUG(kLog, "brs instance war horn={} refused", data);
                        return;
                    }
                    _warHorn = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(BOSS_WYRMTHALAK), _warHorn, BOSS_WYRMTHALAK);
                    LOG_INFO(kLog, "brs instance war horn={}", _warHorn);
                    return;     // per pull: not saved
                case DATA_GENERALS_ARMY:
                    if (!GeneralsArmyChangeAllowed(data, instance->IsHeroic(), kWave2Bound, _nefInsulted != 0,
                        GetBossState(BOSS_DRAKKISATH)))
                    {
                        LOG_DEBUG(kLog, "brs instance general's army={} refused", data);
                        return;
                    }
                    _generalsArmy = data ? 1 : 0;
                    ApplyHardModeLoot(GetCreature(BOSS_DRAKKISATH), _generalsArmy, BOSS_DRAKKISATH);
                    LOG_INFO(kLog, "brs instance general's army={}", _generalsArmy);
                    return;     // per pull: not saved
                default:
                    return;     // stock: Valthalak's SetData(14, DONE) and everything else are ignored
            }

            SaveToDB();
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_SOLAKAR_EVENT:
                    return _solakarEvent;
                case DATA_VAELASTRASZ:
                    return _vaelastrasz;
                case DATA_NEF_INSULTED:
                    return _nefInsulted;
                case DATA_UROK_PILE:
                    return _urokPile;
                case DATA_SOLAKAR_FLAME:
                    return _solakarFlame;
                case DATA_WAR_HORN:
                    return _warHorn;
                case DATA_GENERALS_ARMY:
                    return _generalsArmy;
                case DATA_HALL_RUNES_DONE:
                {
                    uint32 mask = 0;
                    for (uint32 i = 0; i < kHallRuneCount; ++i)
                        if (GetBossState(BOSS_HALL_RUNE_1 + i) == DONE)
                            mask |= 1u << i;
                    return mask;
                }
                case DATA_ROOM_CHECK:
                    return _roomCheckRunning ? 1 : 0;
                default:
                    return 0;
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Update
        // ------------------------------------------------------------------------------------------------------------
        void Update(uint32 diff) override
        {
            InstanceScript::Update(diff);
            if (!_slotsSettled)
                SettleSlots();
            events.Update(diff);

            while (uint32 const eventId = events.ExecuteEvent())
            {
                switch (eventId)
                {
                    case EVENT_ROOM_STORE:
                        RoomStore();
                        break;
                    case EVENT_ROOM_CHECK:
                        RoomCheck();
                        break;
                    case EVENT_ROOM_WATCH:
                        RoomWatch();
                        break;
                    case EVENT_HALYCON_RESPAWN:
                        RespawnHalyconIfStuck();
                        break;
                    case EVENT_SOLAKAR_ARRIVE:
                        if (Creature* solakar = instance->GetCreature(_solakar))
                            if (solakar->IsAlive() && solakar->IsAIEnabled && solakar->AI())
                                solakar->AI()->DoAction(ACTION_SOLAKAR_ARRIVE);
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
            BrsSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                EncounterState const s = GetBossState(i);
                save.states[i] = s == TO_BE_DECIDED ? uint32(NOT_STARTED) : uint32(s);
            }
            save.nefInsulted = _nefInsulted;
            save.urokPile = _urokPile;
            save.solakarEvent = _solakarEvent;
            save.solakarFlame = _solakarFlame;
            return FormatBrsSave(save);
        }

        // Reads this script's "B R W" string, or the stock "B R S" (with the completed-encounter mask, which
        // Map::CreateInstanceData sets before Load).
        void Load(char const* in) override
        {
            if (!in)
                return;

            BrsSave save;
            if (!ParseBrsSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "brs instance: ignored save '{}'", in);
                return;
            }

            _nefInsulted = save.nefInsulted;
            _solakarEvent = save.solakarEvent;
            _solakarFlame = save.solakarFlame;
            _pileInUse = false;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips our switch (no kill flag);
            // the doors and the loot bits follow from the create hooks.
            for (uint32 i = 0; i < kBossCount; ++i)
                SetBossState(i, EncounterState(save.states[i]));
            _urokPile = save.urokPile;      // derived from Omokk and Urok by the parser (no save from inside Load)

            if (GetBossState(BOSS_DRAGONSPIRE_ROOM) != DONE)
                ScheduleRoomWatch(Milliseconds(kRoomWatchMs));
        }

    private:
        // K-m1: the first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED
        // through the base's loading branch (stored, no save, no switch), so the first real write of a rune, the room
        // or a hard mode kill slot saves and runs the switch.
        void SettleSlots()
        {
            _slotsSettled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                uint32 const state = GetBossState(i);
                if (SettledSlotState(state) != state)
                    InstanceScript::SetBossState(i, EncounterState(SettledSlotState(state)));
            }
        }

        // B7: Halycon dead, her slot not DONE, no living Gizrul: the pair can never finish, so she comes back.
        void RespawnHalyconIfStuck()
        {
            Creature* halycon = GetCreature(BOSS_HALYCON);
            if (!halycon)
                return;
            Creature* gizrul = instance->GetCreature(_gizrul);
            if (!HalyconNeedsRespawn(GetBossState(BOSS_HALYCON), halycon->IsAlive(), gizrul && gizrul->IsAlive()))
                return;
            LOG_INFO(kLog, "brs instance: Halycon is dead with her pair unfinished and no Gizrul: respawned");
            halycon->Respawn(true);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Dragonspire room check (stock STORE / CHECK, hardened; section 10)
        // ------------------------------------------------------------------------------------------------------------
        void ScheduleRoomWatch(Milliseconds delay)
        {
            if (GetBossState(BOSS_DRAGONSPIRE_ROOM) == DONE)
                return;
            events.CancelEvent(EVENT_ROOM_WATCH);
            events.ScheduleEvent(EVENT_ROOM_WATCH, delay);
        }

        void ScheduleRoomStore(char const* why)
        {
            LOG_DEBUG(kLog, "brs instance room store scheduled ({})", why);
            events.CancelEvent(EVENT_ROOM_STORE);
            events.ScheduleEvent(EVENT_ROOM_STORE, Milliseconds(kRoomStoreDelayMs));
        }

        bool PlayerInHall() const
        {
            for (auto const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (player->IsAlive() && !player->IsGameMaster()
                        && InDragonspireHall(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ()))
                        return true;
            return false;
        }

        bool AnyRuneUnsnapshotted() const
        {
            for (uint32 i = 0; i < kHallRuneCount; ++i)
                if (GetBossState(BOSS_HALL_RUNE_1 + i) != DONE && !_runeSnapshotted[i])
                    return true;
            return false;
        }

        // The self-start: while the room is not DONE, a player in the hall starts the room check (once per rune that
        // still lacks a snapshot), so a reload, a Finder start or a checkpoint inside the hall cannot leave the room
        // stuck behind an area trigger nobody crosses again.
        void RoomWatch()
        {
            if (GetBossState(BOSS_DRAGONSPIRE_ROOM) == DONE)
                return;
            if (RoomNeedsSelfStart(GetBossState(BOSS_DRAGONSPIRE_ROOM), PlayerInHall(), AnyRuneUnsnapshotted()))
            {
                LOG_INFO(kLog, "brs instance room check self-start (a player is in the Dragonspire Hall)");
                RoomStore();
            }
            events.ScheduleEvent(EVENT_ROOM_WATCH, Milliseconds(kRoomWatchMs));
        }

        // Stock Dragonspireroomstore: each rune's Blackhand pack within 15 yd. A rune already DONE is never
        // snapshotted again; a rune whose grid is not loaded waits for the next store.
        void RoomStore()
        {
            for (uint32 i = 0; i < kHallRuneCount; ++i)
            {
                GameObject* rune = GetGameObject(kHallRunes[i]);
                if (!rune)
                    continue;
                bool const gridLoaded = instance->IsGridLoaded(rune->GetPositionX(), rune->GetPositionY());
                if (!RuneShouldSnapshot(GetBossState(BOSS_HALL_RUNE_1 + i), gridLoaded))
                    continue;

                _runeCreatures[i].clear();
                for (uint32 const entry : kDragonspireMobs)
                {
                    std::list<Creature*> creatures;
                    GetCreatureListWithEntryInGrid(creatures, rune, entry, kHallRunePackRadius);
                    for (Creature* creature : creatures)
                        _runeCreatures[i].push_back(creature->GetGUID());
                }
                _runeSnapshotted[i] = true;
            }

            if (!_roomCheckRunning)
            {
                _roomCheckRunning = true;
                events.ScheduleEvent(EVENT_ROOM_CHECK, Milliseconds(kRoomCheckMs));
            }
        }

        // Stock Dragonspireroomcheck: a lit rune whose pack is dead closes and goes DONE; all seven open the room and
        // its two doors (stock re-opened the In door twice and never the second door's twin: SP note 4).
        void RoomCheck()
        {
            for (uint32 i = 0; i < kHallRuneCount; ++i)
            {
                uint32 const bossId = BOSS_HALL_RUNE_1 + i;
                GameObject* rune = GetGameObject(kHallRunes[i]);
                if (!rune)
                    continue;

                bool anyAlive = false;
                for (ObjectGuid const& guid : _runeCreatures[i])
                    if (Creature* mob = instance->GetCreature(guid))
                        if (mob->IsAlive())
                            anyAlive = true;

                bool const gridLoaded = instance->IsGridLoaded(rune->GetPositionX(), rune->GetPositionY());
                if (!RuneShouldClose(GetBossState(bossId), _runeSnapshotted[i], rune->GetGoState() == GO_STATE_ACTIVE,
                    gridLoaded, anyAlive))
                    continue;

                HandleGameObject(ObjectGuid::Empty, false, rune);
                SetBossState(bossId, DONE);
                LOG_INFO(kLog, "brs instance hall rune {} done", i + 1);
            }

            std::array<uint32, kHallRuneCount> runeStates{};
            for (uint32 i = 0; i < kHallRuneCount; ++i)
                runeStates[i] = GetBossState(BOSS_HALL_RUNE_1 + i);

            if (AllRunesDone(runeStates))
            {
                _roomCheckRunning = false;
                events.CancelEvent(EVENT_ROOM_WATCH);
                SetBossState(BOSS_DRAGONSPIRE_ROOM, DONE);
                if (GameObject* door = GetGameObject(GO_EMBERSEER_IN))
                    HandleGameObject(ObjectGuid::Empty, true, door);
                if (GameObject* door = GetGameObject(GO_EMBERSEER_DOORS))
                    HandleGameObject(ObjectGuid::Empty, true, door);
                LOG_INFO(kLog, "brs instance dragonspire room done: the doors open");
                return;
            }

            events.ScheduleEvent(EVENT_ROOM_CHECK, Milliseconds(kRoomCheckMs));
        }

        // ------------------------------------------------------------------------------------------------------------
        // Urok's pile (stock reset, plus the saved pile state)
        // ------------------------------------------------------------------------------------------------------------
        void UpdateUrokPile()
        {
            uint32 const pile = UrokPileState(GetBossState(BOSS_OMOKK), GetBossState(BOSS_UROK), _pileInUse);
            if (pile == _urokPile)
                return;
            LOG_INFO(kLog, "brs instance urok pile: {} -> {}", UrokPileName(_urokPile), UrokPileName(pile));
            _urokPile = pile;
            SaveToDB();
        }

        // Stock SetData(4, FAIL): the challenge's objects and ogres go, the pile comes back (ruling 39: usable again
        // after a wipe).
        void ResetUrokChallenge()
        {
            if (GetBossState(BOSS_UROK) == DONE || (GetBossState(BOSS_UROK) == NOT_STARTED && !_pileInUse))
                return;
            SetBossState(BOSS_UROK, NOT_STARTED);
            if (GameObject* challenge = instance->GetGameObject(_urokChallenge))
                challenge->Delete();
            if (GameObject* pile = GetGameObject(GO_UROK_PILE))
            {
                pile->SetLootState(GO_READY);
                pile->Respawn();
            }
            for (ObjectGuid const& guid : _urokCircles)
                if (GameObject* circle = instance->GetGameObject(guid))
                    circle->Delete();
            _urokCircles.clear();
            for (ObjectGuid const& guid : _urokMobs)
                if (Creature* mob = instance->GetCreature(guid))
                    mob->DespawnOrUnsummon();
            _urokMobs.clear();
            _pileInUse = false;
            UpdateUrokPile();
            LOG_INFO(kLog, "brs instance urok challenge reset");
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Solakar event (B11, SK1 / SK12; SP notes 1 and 3)
        // ------------------------------------------------------------------------------------------------------------
        // Taking Father Flame (go_brs_father_flame) writes IN_PROGRESS: one Rookery Guardian and one Rookery Hatcher at
        // the stock spots (the Hatcher yells its stock line) and Solakar himself, hidden at his stock spot: his AI owns
        // the flame from the first second (the burn, the toss, the Hatcher's snatch, the eggs) and shows himself at the
        // 30 s mark (ACTION_SOLAKAR_ARRIVE) whatever is left. A FAIL (his AI's wipe, or a GM) ends NOT_STARTED: his AI
        // clears the flame, the items, the eggs and the whelps (ACTION_SOLAKAR_RESET), the event's units go, and Father
        // Flame comes back ready, so the event can start again (stock left it dead at FAIL, note 1). DONE is final.
        void WriteSolakarEvent(uint32 data)
        {
            uint32 const before = _solakarEvent;
            _solakarEvent = SolakarEventAfterWrite(before, data);
            if (SolakarEventStarts(before, _solakarEvent))
                StartSolakarEvent();
            if (data == FAIL && before != DONE)
                ResetSolakarEvent();
            if (before != _solakarEvent)
                LOG_INFO(kLog, "brs instance solakar event {} -> {}", before, _solakarEvent);
        }

        void StartSolakarEvent()
        {
            DespawnSolakarSummons(true);    // a GM restart over a live one
            if (Creature* guardian = instance->SummonCreature(NPC_ROOKERY_GUARDIAN, Position(kSolakarPosLeft.x,
                kSolakarPosLeft.y, kSolakarPosLeft.z, kSolakarPosLeft.o)))
                _solakarSummons.push_back(guardian->GetGUID());
            if (Creature* hatcher = instance->SummonCreature(NPC_ROOKERY_HATCHER, Position(kSolakarPosRight.x,
                kSolakarPosRight.y, kSolakarPosRight.z, kSolakarPosRight.o)))
            {
                _solakarSummons.push_back(hatcher->GetGUID());
                if (hatcher->IsAIEnabled && hatcher->AI())
                    hatcher->AI()->Talk(SAY_SOLAKAR_FIRST_HATCHER);
            }
            // His AI reads the event (IN_PROGRESS, not arrived) at its creation and hides until the arrival.
            if (Creature* solakar = instance->SummonCreature(NPC_SOLAKAR, Position(kSolakarPosBoss.x,
                kSolakarPosBoss.y, kSolakarPosBoss.z, kSolakarPosBoss.o)))
                _solakarSummons.push_back(solakar->GetGUID());
            events.CancelEvent(EVENT_SOLAKAR_ARRIVE);
            events.ScheduleEvent(EVENT_SOLAKAR_ARRIVE, Milliseconds(kSolakarArriveMs));
            LOG_INFO(kLog, "brs instance solakar event started: the pair is out, Solakar arrives in {} s",
                kSolakarArriveMs / 1000);
        }

        void ResetSolakarEvent()
        {
            events.CancelEvent(EVENT_SOLAKAR_ARRIVE);
            DespawnSolakarSummons(true);
            _solakarFlame = FLAME_NONE;
            if (GameObject* flame = GetGameObject(GO_FATHER_FLAME))
            {
                flame->SetLootState(GO_READY);
                flame->Respawn();
            }
            LOG_INFO(kLog, "brs instance solakar event reset: Father Flame is ready again");
        }

        // R-2 M-2: Father Flame and the hatched eggs are despawned with a 2 h respawn, which a dungeon saves at once; a
        // restart or crash mid-event loads the event NOT_STARTED (SanitizeBrsSave) with the chest still gone, so
        // nobody could start Solakar. Whenever the event is not running and he is not dead, a loaded chest or egg is
        // brought back (Respawn only clears a pending respawn: a spawned one is untouched).
        void RespawnSolakarObject(GameObject* go)
        {
            if (_solakarEvent != NOT_STARTED || GetBossState(BOSS_SOLAKAR) == DONE)
                return;
            if (go->GetEntry() == GO_FATHER_FLAME)
                go->SetLootState(GO_READY);
            go->Respawn();
        }

        // The event's units: the pair, and Solakar too `withBoss` (not on his death: his corpse stays). His AI is told
        // first, so it clears what it owns (flame, items, eggs, whelps) before he goes.
        void DespawnSolakarSummons(bool withBoss)
        {
            for (ObjectGuid const& guid : _solakarSummons)
            {
                Creature* creature = instance->GetCreature(guid);
                if (!creature)
                    continue;
                if (creature->GetEntry() == NPC_SOLAKAR)
                {
                    if (!withBoss)
                        continue;
                    if (creature->IsAlive() && creature->IsAIEnabled && creature->AI())
                        creature->AI()->DoAction(ACTION_SOLAKAR_RESET);
                }
                creature->DespawnOrUnsummon();
            }
            _solakarSummons.clear();
        }

        // ------------------------------------------------------------------------------------------------------------
        // The hard modes
        // ------------------------------------------------------------------------------------------------------------
        // Item variants IV7 (the Deadmines pattern): the heroic lootid holds the hard mode list at LootMode 2
        // (LOOT_MODE_HARD_MODE_1); the bit rides the boss's loot mode while the flag is lit and he is not dead yet. The
        // flex bits (4 and 8) are the boss's own, set at its pull (DungeonKit::Flex::OnPull / SetFlexLoot).
        void ApplyHardModeLoot(Creature* boss, uint32 lit, uint32 bossId)
        {
            if (boss)
                DungeonKit::SetHardModeLoot(boss, lit != 0 && GetBossState(bossId) != DONE);
        }

        // Rend's show is over for good (B12): Rend is dead (wave 2; Gyth may fall mid-show and the show goes on, so his
        // slot no longer decides it). Stock until wave 2 binds: Gyth DONE.
        bool RendShowOver() const
        {
            return GetBossState(kWave2Bound ? BOSS_REND : BOSS_GYTH) == DONE;
        }

        EventMap events;

        // Tracked by hand (summoned, or stock's own rule)
        ObjectGuid _urok;
        ObjectGuid _gizrul;
        ObjectGuid _rend;
        ObjectGuid _gyth;
        ObjectGuid _solakar;
        ObjectGuid _nefarius;
        ObjectGuid _urokChallenge;
        GuidVector _urokCircles;
        GuidVector _urokMobs;

        // The Dragonspire room check
        std::array<GuidVector, kHallRuneCount> _runeCreatures{};
        std::array<bool, kHallRuneCount> _runeSnapshotted{};
        bool _roomCheckRunning = false;

        // K-m1: the first Update settles the slots no Load wrote
        bool _slotsSettled = false;

        // The Urok pile
        uint32 _urokPile = PILE_LOCKED;
        bool _pileInUse = false;

        // The Solakar event
        uint32 _solakarEvent = NOT_STARTED;
        uint32 _solakarFlame = FLAME_NONE;
        GuidVector _solakarSummons;

        // Stock data
        uint32 _vaelastrasz = NOT_STARTED;

        // The insult and the hard modes
        uint32 _nefInsulted = 0;
        uint32 _warHorn = 0;
        uint32 _generalsArmy = 0;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_blackrock_spire_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_blackrock_spire_rework()
{
    new instance_blackrock_spire_rework();
}
