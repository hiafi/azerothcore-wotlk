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

// The Blackrock Depths build's instance script (handoff section 3.2, WP-S0), registered under the stock name
// `instance_blackrock_depths` (section 7 #1): modules load after the core scripts, and a database-bound script
// registered later under the same name replaces the earlier one (ScriptRegistry::AddALScripts), so map 230's
// instance_template row is untouched and the stock InstanceMapScript is replaced at load. The other scripts of the
// stock folder stay registered and keep working, none of them copied: their AIs check the instance name
// (GetBlackrockDepthsAI), which is unchanged. That covers npc_rocknot, npc_mistress_nagmara, go_shadowforge_brazier,
// brd_ironhand_guardian, at_ring_of_law, npc_grimstone and the six champions (until D4 / D5 bind theirs), npc_phalanx,
// the Tomb's boss_gloomrel / boss_doomrel and the stock wave 2 bosses until wave 2 binds.
//
// Re-implemented from the stock instance (src/server/scripts/EasternKingdoms/BlackrockMountain/BlackrockDepths/
// instance_blackrock_depths.cpp at Playerbot 5252a82cf, which stays untouched; its last upstream change is 60bac7405,
// NickKononovich, "Stop the Tomb of Seven event reading past its boss list", AzerothCore #28271, after d05ad7f82 /
// abc45e7ab / 7d3f30f80, moostigre, the Dark Iron Ale patrons, Nagmara's love event and Rocknot's ale run (#27271,
// #27287, #27288), and a7ba226a6, Øyvind, the Black Vault warder event (#26973); the file goes back to Kargatum's,
// Kitzunu's, Yehonal's and Francesco Borzì's commits, with UltraNix, patou01 and others): every stock data id with its
// stock meaning (TYPE_RING_OF_LAW .. TYPE_IRON_HALL as GetData / SetData, DATA_EMPEROR .. DATA_LOVE_POTION_EVENT, the
// Dark Iron Ale patron keys), the Ring of Law's start (Grimstone's summon, the FAIL block, the spectators), the Vault,
// the bar (the ale count, Phalanx's state, the love potion), the Tomb of the Seven, the Lyceum braziers, the Iron
// Hall, Argelmach's hall release (wave 1 only), the senators' push to Dagran, the Moira / High Priestess swap, every
// GetGuidData key, and the stock save, which still loads. Each upstream merge re-diffs the stock file against
// 60bac7405 (handoff section 6, section 8 #47).
//
// What is new: 24 boss states (BlackrockDepthsRework.h: 0-18 the DungeonEncounter bits, 19 the Vault, 20-23 the hard
// mode kills); the TYPE_* mirrors of those slots; the Ring's rolls saved (Sentence, wave type, ordered pair) with the
// banner flags; the Vault's trigger moved to the Dark Coffer behind Stilgiss and Verek (section 7 #17; the coffer
// doors' "set data 30" is counted only) with a wipe reset and a cold-load restart; Phalanx's death opens the Bar Door;
// the doors restored on every load (the Ring's north gate, the Bar Door, the Tomb, the Golem Room, the throne room, the
// Secret Door and Safe); the stock MoiraGUID bug fixed (DATA_MOIRA is the princess on the dais, Moira or the
// Priestess); the four hard mode flags with their kill slots and loot bits; the guard on the three slots stock BossAI
// ids collide with (Flamelash 0, Magmus 6, Dagran 10) while wave 2 is unbound; the "BDW" save string. While kWave2Bound
// is false the section 3-4 bosses run stock and their instance paths are the stock ones (Argelmach's release, the
// Tomb's 30 s releases, the Ironhand Gout timer).

#include "BlackrockDepthsRework.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureGroups.h"
#include "DungeonKit.h"
#include "EventProcessor.h"
#include "GameObject.h"
#include "GameTime.h"
#include "Group.h"
#include "InstanceMapScript.h"
#include "InstanceScript.h"
#include "LFGMgr.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SmartAI.h"
#include "TemporarySummon.h"
#include "TheSevenFight.h"
#include <algorithm>
#include <array>
#include <list>
#include <optional>

using namespace BlackrockDepthsRework;

static_assert(DungeonKit::State::NotStarted == NOT_STARTED && DungeonKit::State::InProgress == IN_PROGRESS
    && DungeonKit::State::Fail == FAIL && DungeonKit::State::Done == DONE
    && DungeonKit::State::Special == SPECIAL && DungeonKit::State::ToBeDecided == TO_BE_DECIDED,
    "DungeonKitState.h mirrors InstanceScript.h's EncounterState");

namespace
{
    char constexpr kLog[] = "module.dungeonbosses";

    uint32 constexpr kSpellStoned = 10255;              // the Vault's dormant constructs (stock)

    // Never summoned twice (cpp-scripts.md, the ObjectData pitfall): the spawned bosses under kGuidBossBase + slot,
    // Dagran, Phalanx and Magmus under their stock keys, and the single objects under their stock DATA keys or their
    // entries (the stock GetGuidData keys). Grimstone, the champions, the Encore, Doomgrip, Moira, the Priestess,
    // Verek, the Seven, Coren and every add are tracked by hand.
    ObjectData const creatureData[] =
    {
        { NPC_GERSTAHN,     kGuidBossBase + BOSS_GERSTAHN       },
        { NPC_ROCCOR,       kGuidBossBase + BOSS_ROCCOR         },
        { NPC_GREBMAR,      kGuidBossBase + BOSS_GREBMAR        },
        { NPC_LOREGRAIN,    kGuidBossBase + BOSS_LOREGRAIN      },
        { NPC_INCENDIUS,    kGuidBossBase + BOSS_INCENDIUS      },
        { NPC_STILGISS,     kGuidBossBase + BOSS_STILGISS_VEREK },
        { NPC_FINEOUS,      kGuidBossBase + BOSS_FINEOUS        },
        { NPC_BAELGAR,      kGuidBossBase + BOSS_BAELGAR        },
        { NPC_ANGERFORGE,   kGuidBossBase + BOSS_ANGERFORGE     },
        { NPC_ARGELMACH,    kGuidBossBase + BOSS_ARGELMACH      },
        { NPC_HURLEY,       kGuidBossBase + BOSS_HURLEY         },
        { NPC_RIBBLY,       kGuidBossBase + BOSS_RIBBLY         },
        { NPC_PLUGGER,      kGuidBossBase + BOSS_PLUGGER        },
        { NPC_FLAMELASH,    kGuidBossBase + BOSS_FLAMELASH      },
        { NPC_EMPEROR,      DATA_EMPEROR                        },
        { NPC_PHALANX,      DATA_PHALANX                        },
        { NPC_MAGMUS,       DATA_MAGMUS                         },
        { 0,                0                                   }
    };

    ObjectData const gameObjectData[] =
    {
        { GO_ARENA1,                DATA_ARENA1             },
        { GO_ARENA2,                DATA_ARENA2             },
        { GO_ARENA3,                DATA_ARENA3             },
        { GO_ARENA4,                DATA_ARENA4             },
        { GO_BAR_KEG_SHOT,          DATA_GO_BAR_KEG         },
        { GO_BAR_KEG_TRAP,          DATA_GO_BAR_KEG_TRAP    },
        { GO_BAR_DOOR,              DATA_GO_BAR_DOOR        },
        { GO_SPECTRAL_CHALICE,      DATA_GO_CHALICE         },
        { GO_GOLEM_ROOM_N,          DATA_GOLEM_DOOR_N       },
        { GO_GOLEM_ROOM_S,          DATA_GOLEM_DOOR_S       },
        { GO_THRONE_ROOM,           DATA_THRONE_DOOR        },
        { GO_SF_BRAZIER_N,          DATA_SF_BRAZIER_N       },
        { GO_SF_BRAZIER_S,          DATA_SF_BRAZIER_S       },
        { GO_SHADOW_LOCK,           GO_SHADOW_LOCK          },
        { GO_SHADOW_MECHANISM,      GO_SHADOW_MECHANISM     },
        { GO_SHADOW_GIANT_DOOR,     GO_SHADOW_GIANT_DOOR    },
        { GO_SHADOW_DUMMY,          GO_SHADOW_DUMMY         },
        { GO_TOMB_ENTER,            GO_TOMB_ENTER           },
        { GO_TOMB_EXIT,             GO_TOMB_EXIT            },
        { GO_LYCEUM,                GO_LYCEUM               },
        { GO_CHEST_SEVEN,           GO_CHEST_SEVEN          },
        { GO_SECRET_DOOR,           GO_SECRET_DOOR          },
        { GO_SECRET_SAFE,           GO_SECRET_SAFE          },
        { GO_DARK_COFFER_DOOR,      GO_DARK_COFFER_DOOR     },
        { GO_DARK_COFFER,           GO_DARK_COFFER          },
        { GO_BLACK_ANVIL,           GO_BLACK_ANVIL          },
        { 0,                        0                       }
    };

    enum BrdInstanceEvents
    {
        EVENT_VAULT_WATCH       = 1,    // the Vault's idle watch (an attempt nobody fights ends)
        EVENT_VAULT_RESPAWN     = 2,    // a dead Vault construct after a cold load or a reset comes back
        EVENT_TOMB_RELEASE      = 3,    // stock: one ghost every 30 s (wave 1 only)
        EVENT_MOIRA_SWAP        = 4,    // R-2-C m2: the princess swap skipped mid-fight, once Dagran's attempt ended
    };

    // Stock (RestoreAttack in the stock instance): Argelmach's release ends 3 s after his shout (wave 1 only).
    class ArgelmachRestoreAttack : public BasicEvent
    {
    public:
        explicit ArgelmachRestoreAttack(Creature* boss) : _boss(boss) { }

        bool Execute(uint64 /*execTime*/, uint32 /*diff*/) override
        {
            _boss->SetReactState(REACT_AGGRESSIVE);
            if (_boss->IsAIEnabled && _boss->AI())
                _boss->AI()->SetData(DATA_GOLEM_LORD_ARGELMACH_INIT, DONE);
            if (Unit* victim = _boss->GetVictim())
            {
                _boss->SetTarget(victim->GetGUID());
                _boss->GetMotionMaster()->MoveChase(victim);
            }
            return true;
        }

    private:
        Creature* _boss;
    };
}

class instance_blackrock_depths_rework : public InstanceMapScript
{
public:
    instance_blackrock_depths_rework() : InstanceMapScript(kInstanceScriptName, kMapBlackrockDepths) { }

    struct instance_blackrock_depths_rework_InstanceMapScript : public InstanceScript, public BrdTheSeven::PoolHost
    {
        explicit instance_blackrock_depths_rework_InstanceMapScript(Map* map) : InstanceScript(map)
        {
            SetHeaders(kSaveHeader);
            SetBossNumber(kBossCount);
            LoadObjectData(creatureData, gameObjectData);
        }

        // D21 the Seven: the shared health pool and the ghosts in the rotation order (TheSevenFight.h PoolHost; KT-D2
        // "pool owner": the instance outlives every ghost). Nothing of it is saved: a reload starts a fresh pool.
        DungeonKit::SharedHealthPool& TheSevenPool() override { return _sevenPool; }

        ObjectGuid TheSevenGuid(std::size_t ghost) const override
        {
            return ghost < _seven.size() ? _seven[ghost] : ObjectGuid::Empty;
        }

        void OnPlayerEnter(Player* player) override
        {
            InstanceScript::OnPlayerEnter(player);
            ReplaceMoiraIfSaved();      // stock: a player joining mid-run

            // Section 10 / R-1-RING MJ-1: the Ring gallery stands down for a group whose instance starts at S2.
            uint32 lfgDungeon = 0;
            if (Group* group = player->GetGroup(); group && group->isLFGGroup())
                lfgDungeon = sLFGMgr->GetDungeon(group->GetGUID());
            bool const firstEntry = !_anyPlayerEntered && !AnySlotStarted();
            _anyPlayerEntered = true;
            FinderSection const& s2 = kSections[1];
            float const fromStart = player->GetDistance2d(s2.start.x, s2.start.y);
            if (GalleryStandsDownOnEntry(_galleryStoodDown != 0, Slot(BOSS_RING_OF_LAW), lfgDungeon, s2.lfgNormal,
                s2.lfgHeroic, firstEntry, fromStart))
            {
                LOG_INFO(kLog, "brd instance gallery stands down (player {}, lfg dungeon {}, first entry {}, {:.1f} yd "
                    "from the S2 start)", player->GetName(), lfgDungeon, firstEntry, fromStart);
                StandDownGallery();
            }
        }

        // ------------------------------------------------------------------------------------------------------------
        // Objects
        // ------------------------------------------------------------------------------------------------------------
        void OnCreatureCreate(Creature* creature) override
        {
            InstanceScript::OnCreatureCreate(creature);

            if (std::optional<uint32> const seven = SevenIndex(creature->GetEntry()))
            {
                _seven[*seven] = creature->GetGUID();
                return;
            }

            switch (creature->GetEntry())
            {
                case NPC_VEREK:
                    _verek = creature->GetGUID();
                    break;
                case NPC_GRIMSTONE:
                    _grimstone = creature->GetGUID();
                    break;
                case NPC_MOIRA:
                    _moira = creature->GetGUID();
                    ApplyMoiraStandDown(creature);
                    break;
                case NPC_PRIESTESS:
                    _priestess = creature->GetGUID();
                    ApplyMoiraStandDown(creature);
                    break;
                case NPC_COREN_DIREBREW:
                    _coren = creature->GetGUID();
                    break;
                case NPC_MAGMUS:
                    if (!creature->IsAlive())
                        HandleGameObject(DATA_THRONE_DOOR, true);   // stock: Magmus dead, the throne door is open
                    break;
                case NPC_WEAPON_TECHNICIAN:
                case NPC_DOOMFORGE_ARCANASMITH:
                case NPC_RAGEREAVER_GOLEM:
                case NPC_WRATH_HAMMER_CONSTRUCT:
                    // Stock: the Argelmach hall's adds (wave 1 only; ruling 56 retires the release once D15 binds).
                    if (!kWave2Bound && creature->IsAlive() && creature->GetPositionZ() < kArgelmachHallZMax
                        && creature->GetPositionZ() > kArgelmachHallZMin)
                        _argelmachAdds.push_back(creature->GetGUID());
                    break;
                case NPC_IRONHAND_GUARDIAN:
                    _ironhands.push_back(creature->GetGUID());
                    break;
                case NPC_ARENA_SPECTATOR:
                    _arenaSpectators.push_back(creature->GetGUID());
                    if (Slot(BOSS_RING_OF_LAW) == DONE)
                        StandDownSpectator(creature);
                    TrackGalleryUnit(creature);
                    break;
                case NPC_SHADOWFORGE_PEASANT:
                case NPC_SHADOWFORGE_CITIZEN:
                    if (creature->GetDistance2d(kRingCenter.x, kRingCenter.y) < kRingSpectatorRadius)
                        _arenaSpectators.push_back(creature->GetGUID());
                    if (Slot(BOSS_RING_OF_LAW) == DONE)
                        StandDownSpectator(creature);
                    TrackGalleryUnit(creature);
                    break;
                case NPC_SHADOWFORGE_SENATOR:
                    // Stock: the senators of the Emperor's room (some stand at the Ring of Law).
                    if (creature->GetDistance2d(kEmperorRoomCenter.x, kEmperorRoomCenter.y) < kEmperorRoomRadius)
                        _senators.push_back(creature->GetGUID());
                    TrackGalleryUnit(creature);
                    break;
                case NPC_ANVILRAGE_FOOTMAN:
                case NPC_ANVILRAGE_SOLDIER:
                case NPC_ANVILRAGE_MEDIC:
                case NPC_ANVILRAGE_OFFICER:
                    TrackGalleryUnit(creature);
                    break;
                case NPC_WARBRINGER_CONSTRUCT:
                case NPC_BRD_VAULT_SENTINEL:
                    OnVaultConstructCreate(creature);
                    break;
                case NPC_DOOMGRIP:
                    _doomgrip = creature->GetGUID();
                    break;
                default:
                    break;
            }
        }

        void OnCreatureRemove(Creature* creature) override
        {
            InstanceScript::OnCreatureRemove(creature);

            ObjectGuid const guid = creature->GetGUID();
            if (guid == _grimstone)
                _grimstone.Clear();
            else if (guid == _doomgrip)
                _doomgrip.Clear();
            else if (guid == _priestess)
                _priestess.Clear();
            else if (guid == _moira)
                _moira.Clear();
        }

        void OnGameObjectCreate(GameObject* go) override
        {
            InstanceScript::OnGameObjectCreate(go);

            switch (go->GetEntry())
            {
                case GO_DARK_IRON_ALE_MUG:
                    AssignAleMug(go);
                    break;
                case GO_BAR_DOOR:
                    go->AllowSaveToDB(true);    // stock
                    RestoreBarDoor(go);
                    break;
                case GO_TOMB_ENTER:
                    HandleGameObject(ObjectGuid::Empty, TombDoorsFor(Slot(BOSS_THE_SEVEN)).enterOpen, go);
                    break;
                case GO_TOMB_EXIT:
                    HandleGameObject(ObjectGuid::Empty, TombDoorsFor(Slot(BOSS_THE_SEVEN)).exitOpen, go);
                    break;
                case GO_GOLEM_ROOM_N:
                case GO_GOLEM_ROOM_S:
                    if (_lyceum == DONE)
                        HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case GO_THRONE_ROOM:
                    if (Slot(BOSS_MAGMUS) == DONE)
                        HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case GO_ARENA3:
                    if (Slot(BOSS_RING_OF_LAW) == DONE)
                        HandleGameObject(ObjectGuid::Empty, true, go);   // the north gate: section 2's way out
                    break;
                case GO_SECRET_DOOR:
                    if (Slot(BOSS_VAULT) == DONE)
                        HandleGameObject(ObjectGuid::Empty, true, go);
                    break;
                case GO_SECRET_SAFE:
                    // non-interactable through gameobject_template_addon flags until the Vault is DONE (stock)
                    if (Slot(BOSS_VAULT) == DONE)
                        go->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                    break;
                case GO_DARK_COFFER_DOOR:
                    // Section 10: the coffer refuses to open (the key stays unspent) while Stilgiss or Verek lives.
                    if (!DarkCofferSelectable(Slot(BOSS_STILGISS_VEREK)))
                        go->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                    break;
                case GO_DARK_COFFER:
                case GO_CHEST_SEVEN:
                    // The heroic chest rolls its Heroic-tier groups (LootMode 2) instead of the normal ones (ruling 34;
                    // replace the mode, never add: groups 3+ are LootMode 3 and roll under either; R-1-LOOT M-2, L-2).
                    if (instance->IsHeroic())
                        go->SetLootMode(LOOT_MODE_HARD_MODE_1);
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
            switch (entry)
            {
                case NPC_WEAPON_TECHNICIAN:
                case NPC_DOOMFORGE_ARCANASMITH:
                case NPC_RAGEREAVER_GOLEM:
                case NPC_WRATH_HAMMER_CONSTRUCT:
                    _argelmachAdds.remove(creature->GetGUID());
                    return;
                case NPC_MAGMUS:
                    SetData(TYPE_IRON_HALL, DONE);      // stock (the throne door; D22's BossAI writes the slot too)
                    return;
                case NPC_WARBRINGER_CONSTRUCT:
                case NPC_BRD_VAULT_SENTINEL:
                case NPC_DOOMGRIP:
                    OnVaultWarderDeath(creature);
                    return;
                case NPC_SHADOWFORGE_SENATOR:
                    PushSenatorsDead();
                    return;
                case NPC_STILGISS:
                case NPC_VEREK:
                    // One encounter (D8): DONE once both are dead, whoever dies last.
                    if (Slot(BOSS_STILGISS_VEREK) != DONE && StilgissAndVerekDead())
                    {
                        LOG_INFO(kLog, "brd instance stilgiss and verek dead: boss state {} DONE, credit spell {}",
                            uint32(BOSS_STILGISS_VEREK), kSpellStilgissVerekCredit);
                        // D8 Q1: the encounter credit when both are dead (instance_encounters 233 is a spell credit).
                        instance->UpdateEncounterState(ENCOUNTER_CREDIT_CAST_SPELL, kSpellStilgissVerekCredit,
                            creature);
                        ForceBossState(BOSS_STILGISS_VEREK, DONE);
                    }
                    return;
                default:
                    break;
            }

            if (SevenIndex(entry))
            {
                // Stock: seven ghost deaths finish the Tomb (D21's seven die together, the count reaches 7 too).
                if (++_ghostKills >= 7 && Slot(BOSS_THE_SEVEN) != DONE)
                    SetData(TYPE_TOMB_OF_SEVEN, DONE);
                return;
            }

            // A boss whose slot its own script does not write (a stock boss before its wave binds, Ribbly and Plugger
            // on SmartAI) records its death here.
            std::optional<uint32> const boss = BossOfEntry(entry);
            if (!boss || *boss == BOSS_VAULT || *boss == BOSS_THE_SEVEN || *boss == BOSS_STILGISS_VEREK)
                return;
            if (SlotWrittenByScript(*boss) || Slot(*boss) == DONE)
                return;
            LOG_INFO(kLog, "brd instance {} died: boss state {} DONE (written by the instance)", entry, *boss);
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
            if (!bypass && id < kBossCount && !SlotWriteAccepted(id, state, before, OwnersOf(id)))
            {
                LOG_DEBUG(kLog, "brd instance refused boss state {} -> {} (a stock BossAI id on a wave 1 slot)", id,
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
                case TYPE_RING_OF_LAW:
                    SetRingOfLaw(data);
                    return;
                case TYPE_VAULT:
                    ForceBossState(BOSS_VAULT, EncounterState(data == FAIL ? uint32(NOT_STARTED) : data));
                    return;
                case TYPE_BAR:
                    if (data == SPECIAL)
                        ++_barAleCount;
                    else if (_bar != data)
                    {
                        _bar = data;
                        if (data == DONE)
                            SaveToDB();
                    }
                    return;
                case DATA_LOVE_POTION_EVENT:
                    _lovePotion = data;
                    if (data == DONE)
                    {
                        _bar = DONE;            // stock
                        SaveToDB();
                    }
                    return;
                case TYPE_TOMB_OF_SEVEN:
                    ForceBossState(BOSS_THE_SEVEN, EncounterState(data == FAIL ? uint32(NOT_STARTED) : data));
                    return;
                case TYPE_LYCEUM:
                    SetLyceum(data);
                    return;
                case TYPE_IRON_HALL:
                    ForceBossState(BOSS_MAGMUS, EncounterState(data == FAIL ? uint32(NOT_STARTED) : data));
                    return;
                case DATA_OPEN_COFFER_DOORS:
                    // Inert (section 7 #17): the twelve doors no longer start the Vault, the Dark Coffer does.
                    ++_cofferDoorsOpened;
                    return;
                case DATA_VAULT_TRIGGER:
                    if (data && VaultTriggerAccepted(Slot(BOSS_VAULT), Slot(BOSS_STILGISS_VEREK)))
                    {
                        LOG_INFO(kLog, "brd instance vault trigger: the Dark Coffer starts the Vault");
                        NoteNearestCofferPlayer();
                        SetData(TYPE_VAULT, IN_PROGRESS);
                    }
                    else if (data)
                        LOG_INFO(kLog, "brd instance vault trigger refused (vault {}, stilgiss and verek {})",
                            Slot(BOSS_VAULT), Slot(BOSS_STILGISS_VEREK));
                    return;
                case DATA_VAULT_RESET:
                    if (data && Slot(BOSS_VAULT) == IN_PROGRESS)
                        ForceBossState(BOSS_VAULT, NOT_STARTED);
                    return;
                case DATA_VAULT_CLOCK:
                    _vaultClock = data;
                    SaveToDB();
                    return;
                case DATA_GOLEM_LORD_ARGELMACH_INIT:
                    if (!kWave2Bound)
                        StockArgelmachInit();
                    return;
                case DATA_GOLEM_LORD_ARGELMACH_ADDS:
                    if (!kWave2Bound)
                        StockArgelmachAdds();
                    return;
                case DATA_PHALANX_ACTIVATED:
                    _phalanxActivated = data;
                    if (data == DONE)
                        SaveToDB();
                    return;
                case DATA_RING_FAVOR:
                    _ringFavor = std::min<uint32>(data, kRingFavorMax);
                    return;
                case DATA_BANNER_THROWN:
                    if (!BannerThrowAllowed(data, instance->IsHeroic(), Slot(BOSS_RING_OF_LAW)))
                        return;
                    _bannerThrown = data ? 1 : 0;
                    if (!_bannerThrown)
                        _bannerBurned = 0;
                    LOG_INFO(kLog, "brd instance banner thrown {}", _bannerThrown);
                    SaveToDB();
                    return;
                case DATA_BANNER_BURNED:
                    if (!BannerBurnAllowed(data, instance->IsHeroic(), _bannerThrown != 0, Slot(BOSS_RING_OF_LAW)))
                        return;
                    _bannerBurned = data ? 1 : 0;
                    LOG_INFO(kLog, "brd instance banner burned {}: the Encore is {}", _bannerBurned,
                        _bannerBurned ? "armed" : "off");
                    SaveToDB();
                    return;
                case DATA_GUZZLER_ROPE:
                    if (!RopeChangeAllowed(_rope, data))
                        return;
                    _rope = data;
                    LOG_INFO(kLog, "brd instance guzzler rope {}", RopeStateName(_rope));
                    SaveToDB();
                    return;
                case DATA_CINDER_USED:
                    if (!CinderAllowed(data, instance->IsHeroic(), Slot(BOSS_INCENDIUS)))
                        return;
                    _cinderUsed = data ? 1 : 0;
                    LOG_INFO(kLog, "brd instance cinder used {}: Lord of the Lake is {}", _cinderUsed,
                        _cinderUsed ? "armed" : "off");
                    ApplyHardModeLoot(GetCreature(kGuidBossBase + BOSS_INCENDIUS), _cinderUsed, BOSS_INCENDIUS);
                    SaveToDB();
                    return;
                case DATA_CONSOLE_ARMED:
                    if (!ConsoleAllowed(data, instance->IsHeroic(), kWave2Bound, Slot(BOSS_ARGELMACH)))
                        return;
                    _consoleArmed = data ? 1 : 0;
                    LOG_INFO(kLog, "brd instance console armed {}", _consoleArmed);
                    ApplyHardModeLoot(GetCreature(kGuidBossBase + BOSS_ARGELMACH), _consoleArmed, BOSS_ARGELMACH);
                    return;
                case DATA_AVATAR:
                    if (!AvatarAllowed(data, instance->IsHeroic(), kWave2Bound, Slot(BOSS_EMPEROR)))
                        return;
                    _avatar = data ? 1 : 0;
                    LOG_INFO(kLog, "brd instance avatar {}", _avatar);
                    ApplyHardModeLoot(GetCreature(DATA_EMPEROR), _avatar, BOSS_EMPEROR);
                    return;
                case DATA_GM_SLOT_WRITE:
                    _gmSlotWrite = data != 0;
                    return;
                case DATA_VAULT_DOOMGRIP_ITEM:
                    _doomgripItem = data;
                    SaveToDB();
                    return;
                case DATA_ENCORE_WON:
                    if (!EncoreWonAccepted(data, instance->IsHeroic(), _bannerBurned != 0, Slot(BOSS_RING_OF_LAW)))
                    {
                        LOG_INFO(kLog, "brd instance encore won refused (heroic {}, burned {}, ring {})",
                            instance->IsHeroic(), _bannerBurned, Slot(BOSS_RING_OF_LAW));
                        return;
                    }
                    _encoreWon = true;
                    LOG_INFO(kLog, "brd instance encore won reported");
                    return;
                case DATA_ENCORE_RUNNING:
                    _encoreRunning = data != 0;
                    return;
                case DATA_GALLERY_STOOD_DOWN:
                    if (data)
                        StandDownGallery();
                    return;
                case DATA_STILGISS_VEREK_FIGHT:
                    // R-1-A m7: the pair's pull and reset (DONE stays the instance's, on both deaths).
                    if (data && Slot(BOSS_STILGISS_VEREK) == NOT_STARTED)
                        ForceBossState(BOSS_STILGISS_VEREK, IN_PROGRESS);
                    else if (!data && Slot(BOSS_STILGISS_VEREK) == IN_PROGRESS)
                        ForceBossState(BOSS_STILGISS_VEREK, NOT_STARTED);
                    return;
                default:
                    return;
            }
        }

        uint32 GetData(uint32 type) const override
        {
            switch (type)
            {
                case TYPE_RING_OF_LAW:
                    return Slot(BOSS_RING_OF_LAW);
                case TYPE_VAULT:
                    return Slot(BOSS_VAULT);
                case TYPE_BAR:
                    // Stock: three ale turn-ins while the run is IN_PROGRESS read as SPECIAL.
                    return _bar == IN_PROGRESS && _barAleCount == 3 ? uint32(SPECIAL) : _bar;
                case TYPE_TOMB_OF_SEVEN:
                    return Slot(BOSS_THE_SEVEN);
                case TYPE_LYCEUM:
                    return _lyceum;
                case TYPE_IRON_HALL:
                    return Slot(BOSS_MAGMUS);
                case DATA_TIME_RING_FAIL:
                    return uint32(_timeRingFail);
                case DATA_ARENA_MOBS:
                case DATA_RING_WAVE:
                    return _ring.wave ? _ring.wave - 1 : 0;
                case DATA_ARENA_BOSS:
                case DATA_RING_FIRST:
                    return _ring.first ? _ring.first - 1 : 0;
                case DATA_RING_SECOND:
                    return _ring.second ? _ring.second - 1 : 0;
                case DATA_RING_SENTENCE:
                    return _ring.sentence ? _ring.sentence - 1 : 0;
                case DATA_RING_FAVOR:
                    return _ringFavor;
                case DATA_PHALANX_ACTIVATED:
                    return _phalanxActivated;
                case DATA_LOVE_POTION_EVENT:
                    return _lovePotion;
                case DATA_BANNER_THROWN:
                    return _bannerThrown;
                case DATA_BANNER_BURNED:
                    return _bannerBurned;
                case DATA_VAULT_CLOCK:
                    return _vaultClock;
                case DATA_GUZZLER_ROPE:
                    return _rope;
                case DATA_CINDER_USED:
                    return _cinderUsed;
                case DATA_MOIRA_SAVED:
                    return _moiraSaved;
                case DATA_CONSOLE_ARMED:
                    return _consoleArmed;
                case DATA_AVATAR:
                    return _avatar;
                case DATA_COFFER_DOORS_OPENED:
                    return _cofferDoorsOpened;
                case DATA_VAULT_DOOMGRIP_ITEM:
                    return _doomgripItem;
                case DATA_ENCORE_WON:
                    return _encoreWon ? 1 : 0;
                case DATA_ENCORE_RUNNING:
                    return _encoreRunning ? 1 : 0;
                case DATA_GALLERY_STOOD_DOWN:
                    return _galleryStoodDown;
                default:
                    return 0;
            }
        }

        // Stock (d05ad7f82): the Dark Iron Ale patrons' SmartAI hands the instance a patron to send home, re-form,
        // disband or reset the emote of.
        void SetGuidData(uint32 type, ObjectGuid guid) override
        {
            if (type == DATA_VAULT_OPENER)
            {
                // The opener of this attempt: before the start, or in the tick the coffer started it (the SmartAI
                // rows run in id order; the start row may come first). A later click on the open coffer is not one.
                if (guid.IsPlayer() && (Slot(BOSS_VAULT) == NOT_STARTED
                    || (Slot(BOSS_VAULT) == IN_PROGRESS && _vaultSinceStartMs == 0)))
                    _vaultOpener = guid;
                return;
            }
            if (type != DATA_DARK_IRON_ALE_HOME && type != DATA_DARK_IRON_ALE_REFORM
                && type != DATA_DARK_IRON_ALE_DISBAND && type != DATA_DARK_IRON_ALE_EMOTE)
                return;

            Creature* patron = instance->GetCreature(guid);
            if (!patron)
                return;

            switch (type)
            {
                case DATA_DARK_IRON_ALE_EMOTE:
                    if (CreatureAddon const* addon = patron->GetCreatureAddon())
                        patron->SetEmoteState(static_cast<Emote>(addon->emote));
                    return;
                case DATA_DARK_IRON_ALE_DISBAND:
                    if (CreatureGroup* formation = patron->GetFormation())
                        sFormationMgr->RemoveCreatureFromGroup(formation, patron);
                    return;
                case DATA_DARK_IRON_ALE_REFORM:
                    if (!patron->GetFormation())
                        patron->SearchFormation();
                    return;
                default:
                    if (patron->IsAlive() && !patron->IsInCombat())
                    {
                        if (!patron->GetFormation())
                            patron->SearchFormation();
                        patron->GetMotionMaster()->MoveTargetedHome(true);
                    }
                    return;
            }
        }

        ObjectGuid GetGuidData(uint32 type) const override
        {
            switch (type)
            {
                case DATA_MOIRA:
                    // The princess on the dais: the Priestess while she stands in (the stock MoiraGUID bug fixed).
                    return _priestess ? _priestess : _moira;
                case DATA_PRIESTESS:
                    return _priestess;
                case DATA_COREN:
                    return _coren;
                case kGuidVerek:
                    return _verek;
                case kGuidDoomgrip:
                    return _doomgrip;
                case kGuidGrimstone:
                    return _grimstone;
                default:
                    break;
            }
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
                    case EVENT_VAULT_WATCH:
                        VaultWatch();
                        break;
                    case EVENT_VAULT_RESPAWN:
                        RespawnVaultConstructs();
                        break;
                    case EVENT_TOMB_RELEASE:
                        StockTombRelease();
                        break;
                    case EVENT_MOIRA_SWAP:
                        ReplaceMoiraIfSaved();
                        break;
                    default:
                        break;
                }
            }

            if (!kWave2Bound && Slot(BOSS_THE_SEVEN) == IN_PROGRESS)
                StockTombResetCheck(diff);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Save
        // ------------------------------------------------------------------------------------------------------------
        std::string GetSaveData() override
        {
            BrdSave save;
            for (uint32 i = 0; i < kBossCount; ++i)
                save.states[i] = Slot(i);
            save.ring = _ring;
            save.bannerThrown = _bannerThrown;
            save.bannerBurned = _bannerBurned;
            save.rope = _rope;
            save.cinderUsed = _cinderUsed;
            save.vaultClock = _vaultClock;
            save.moiraSaved = _moiraSaved;
            save.bar = _bar;
            save.phalanxActivated = _phalanxActivated;
            save.lovePotion = _lovePotion;
            save.lyceum = _lyceum;
            save.galleryStoodDown = _galleryStoodDown;
            save.doomgripItem = _doomgripItem;
            return FormatBrdSave(save);
        }

        // Reads this script's "B D W" string, or the stock one (no header; with the completed-encounter mask, which
        // Map::CreateInstanceData sets before Load).
        void Load(char const* in) override
        {
            if (!in || !*in)
                return;

            BrdSave save;
            if (!ParseBrdSave(in, save, GetCompletedEncounterMask()))
            {
                LOG_DEBUG(kLog, "brd instance: ignored save '{}'", in);
                return;
            }

            _ring = save.ring;
            _bannerThrown = save.bannerThrown;
            _bannerBurned = save.bannerBurned;
            _rope = save.rope;
            _cinderUsed = save.cinderUsed;
            _vaultClock = save.vaultClock;
            _moiraSaved = save.moiraSaved;
            _bar = save.bar;
            _phalanxActivated = save.phalanxActivated;
            _lovePotion = save.lovePotion;
            _lyceum = save.lyceum;
            _galleryStoodDown = save.galleryStoodDown;
            _doomgripItem = save.doomgripItem;
            if (save.states[BOSS_THE_SEVEN] == DONE)
                _ghostKills = 7;
            // Loading: each slot is TO_BE_DECIDED, so the base stores the state and skips the switch (no kill flag,
            // no guard); the doors follow from the create hooks.
            for (uint32 i = 0; i < kBossCount; ++i)
                InstanceScript::SetBossState(i, EncounterState(save.states[i]));
        }

    private:
        // A slot's state, TO_BE_DECIDED read as NOT_STARTED (before the first Update settles it).
        uint32 Slot(uint32 id) const
        {
            return SettledSlotState(uint32(GetBossState(id)));
        }

        // A write the instance makes itself (the TYPE_* mirrors, deaths, the hard mode kills): past the guard.
        bool ForceBossState(uint32 id, EncounterState state)
        {
            _bypassGuard = true;
            bool const changed = SetBossState(id, state);
            _bypassGuard = false;
            return changed;
        }

        // The first Update (Load, if any, ran before it): every slot still TO_BE_DECIDED becomes NOT_STARTED through
        // the base's loading branch (stored, no save, no switch), so the first real write saves and runs the switch
        // (BRS K-m1, F-1a). The Ring's rolls are made once and saved (S1 613; section 7 #16), and a cold load restarts
        // the Vault (its dead constructs come back while it is not DONE).
        void Settle()
        {
            _settled = true;
            for (uint32 i = 0; i < kBossCount; ++i)
            {
                uint32 const state = GetBossState(i);
                if (SettledSlotState(state) != state)
                    InstanceScript::SetBossState(i, EncounterState(SettledSlotState(state)));
            }
            if (!_ring.Rolled())
            {
                _ring = RollRing(urand(0, 0xFFFF), urand(0, 0xFFFF), urand(0, 0xFFFF), urand(0, 0xFFFF));
                LOG_INFO(kLog, "brd instance ring rolls: sentence {}, wave {}, champions {} then {}", _ring.sentence,
                    _ring.wave, _ring.first, _ring.second);
                SaveToDB();
            }
            if (Slot(BOSS_VAULT) != DONE)
                events.ScheduleEvent(EVENT_VAULT_RESPAWN, 1s);
        }

        ObjectGuid BossGuid(uint32 bossId) const
        {
            switch (bossId)
            {
                case BOSS_RING_OF_LAW:
                case BOSS_ENCORE:
                    return _grimstone;
                case BOSS_THE_SEVEN:
                    return _seven[6];       // Doom'rel
                case BOSS_MAGMUS:
                    return InstanceScript::GetGuidData(DATA_MAGMUS);
                case BOSS_PHALANX:
                    return InstanceScript::GetGuidData(DATA_PHALANX);
                case BOSS_EMPEROR:
                case BOSS_AVATAR:
                    return InstanceScript::GetGuidData(DATA_EMPEROR);
                case BOSS_VAULT:
                    return _doomgrip;
                case BOSS_LORD_OF_THE_LAKE:
                    return InstanceScript::GetGuidData(kGuidBossBase + BOSS_INCENDIUS);
                case BOSS_PROTOTYPE:
                    return InstanceScript::GetGuidData(kGuidBossBase + BOSS_ARGELMACH);
                default:
                    return InstanceScript::GetGuidData(kGuidBossBase + bossId);
            }
        }

        // The stock-collision guard's view of a slot's own bosses (BlackrockDepthsRework.h SlotWriteAccepted).
        SlotOwners OwnersOf(uint32 bossId)
        {
            SlotOwners owners;
            if (!IsStockCollisionSlot(bossId))
                return owners;
            std::array<ObjectGuid, 2> const guids{ { BossGuid(bossId),
                bossId == BOSS_STILGISS_VEREK ? _verek : ObjectGuid::Empty } };
            owners.allDead = true;
            for (ObjectGuid const& guid : guids)
            {
                Creature* owner = guid ? instance->GetCreature(guid) : nullptr;
                if (!owner)
                    continue;
                owners.anyFound = true;
                if (owner->IsAlive() && !owner->isDying())
                {
                    owners.allDead = false;
                    if (owner->IsInCombat())
                        owners.anyInCombat = true;
                }
            }
            if (!owners.anyFound)
                owners.allDead = false;
            return owners;
        }

        bool StilgissAndVerekDead()
        {
            for (ObjectGuid const& guid : { BossGuid(BOSS_STILGISS_VEREK), _verek })
            {
                Creature* unit = guid ? instance->GetCreature(guid) : nullptr;
                if (!unit || (unit->IsAlive() && !unit->isDying()))
                    return false;
            }
            return true;
        }

        void OnSlotChanged(uint32 id, uint32 before, uint32 state)
        {
            switch (id)
            {
                case BOSS_RING_OF_LAW:
                    if (state == DONE)
                    {
                        for (ObjectGuid const& guid : _arenaSpectators)
                            if (Creature* spectator = instance->GetCreature(guid))
                                StandDownSpectator(spectator);
                        HandleGameObject(DATA_ARENA3, true);
                        // D4 request 2 / D6: only an explicit DATA_ENCORE_WON records the Encore's kill.
                        if (_encoreWon)
                        {
                            LOG_INFO(kLog, "brd instance encore won");
                            ForceBossState(BOSS_ENCORE, DONE);
                        }
                        _encoreWon = false;
                        _encoreRunning = false;
                    }
                    break;
                case BOSS_INCENDIUS:
                    if (state == DONE && _cinderUsed)
                    {
                        // The kill flag (the loot is already filled: Unit::Kill runs before JustDied).
                        LOG_INFO(kLog, "brd instance lord of the lake killed");
                        _cinderUsed = 0;
                        ForceBossState(BOSS_LORD_OF_THE_LAKE, DONE);
                    }
                    ApplyHardModeLoot(GetCreature(kGuidBossBase + BOSS_INCENDIUS), _cinderUsed, BOSS_INCENDIUS);
                    break;
                case BOSS_ARGELMACH:
                    if (state == DONE && _consoleArmed)
                    {
                        LOG_INFO(kLog, "brd instance prototype killed");
                        _consoleArmed = 0;
                        ForceBossState(BOSS_PROTOTYPE, DONE);
                    }
                    else if (AttemptEnded(before, state) && _consoleArmed)
                    {
                        LOG_INFO(kLog, "brd instance console reset (the attempt ended)");
                        _consoleArmed = 0;
                    }
                    ApplyHardModeLoot(GetCreature(kGuidBossBase + BOSS_ARGELMACH), _consoleArmed, BOSS_ARGELMACH);
                    break;
                case BOSS_EMPEROR:
                    if (state == DONE && _avatar)
                    {
                        LOG_INFO(kLog, "brd instance avatar killed");
                        _avatar = 0;
                        ForceBossState(BOSS_AVATAR, DONE);
                    }
                    else if (AttemptEnded(before, state) && _avatar)
                    {
                        LOG_INFO(kLog, "brd instance avatar reset (the attempt ended)");
                        _avatar = 0;
                    }
                    // R-2-C m2: a swap skipped mid-fight, 1 s later (never inside her own evade's call).
                    if (AttemptEnded(before, state))
                        events.RescheduleEvent(EVENT_MOIRA_SWAP, 1s);
                    ApplyHardModeLoot(GetCreature(DATA_EMPEROR), _avatar, BOSS_EMPEROR);
                    break;
                case BOSS_AVATAR:
                    if (state == DONE)
                    {
                        _moiraSaved = 1;
                        LOG_INFO(kLog, "brd instance moira saved");
                        SaveToDB();
                    }
                    break;
                case BOSS_STILGISS_VEREK:
                    if (state == DONE)
                        if (GameObject* coffer = GetGameObject(GO_DARK_COFFER_DOOR))
                            coffer->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                    break;
                case BOSS_PHALANX:
                    if (state == DONE)
                        if (GameObject* door = GetGameObject(DATA_GO_BAR_DOOR))
                            RestoreBarDoor(door);
                    break;
                case BOSS_THE_SEVEN:
                    OnTombChanged(state);
                    break;
                case BOSS_MAGMUS:
                    if (state == DONE)
                        HandleGameObject(DATA_THRONE_DOOR, true);
                    else if (!kWave2Bound && (state == NOT_STARTED || state == IN_PROGRESS))
                        for (ObjectGuid const& guid : _ironhands)    // stock Gout of Flames (wave 1 only)
                            if (Creature* ironhand = instance->GetCreature(guid))
                                if (ironhand->IsAIEnabled && ironhand->AI())
                                    ironhand->AI()->SetData(DATA_IRONHAND_FLAMES, state == IN_PROGRESS ? 1 : 0);
                    break;
                case BOSS_VAULT:
                    if (state == IN_PROGRESS)
                        StartVault();
                    else if (state == DONE)
                    {
                        events.CancelEvent(EVENT_VAULT_WATCH);
                        HandleGameObject(GO_SECRET_DOOR, true);
                        if (GameObject* safe = GetGameObject(GO_SECRET_SAFE))
                            safe->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
                        TakeDarkKeeperKey();
                    }
                    else if (before == IN_PROGRESS)
                        ResetVault();
                    break;
                default:
                    break;
            }
        }

        // Item variants IV7 (the Deadmines pattern): the heroic lootid holds the hard mode list at LootMode 2; the bit
        // rides the boss's loot mode while the flag is lit and he is not dead yet.
        void ApplyHardModeLoot(Creature* boss, uint32 lit, uint32 bossId)
        {
            if (boss)
                DungeonKit::SetHardModeLoot(boss, lit != 0 && Slot(bossId) != DONE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Ring of Law (stock start and fail; D4 owns the rest)
        // ------------------------------------------------------------------------------------------------------------
        void SetRingOfLaw(uint32 data)
        {
            switch (data)
            {
                case IN_PROGRESS:
                    if (Slot(BOSS_RING_OF_LAW) == IN_PROGRESS || Slot(BOSS_RING_OF_LAW) == DONE)
                        return;
                    // Stock: at_ring_of_law starts it; Grimstone comes in (stock npc_grimstone until D4 binds its own).
                    instance->SummonCreature(NPC_GRIMSTONE, Position(kGrimstoneSummon.x, kGrimstoneSummon.y,
                        kGrimstoneSummon.z, kGrimstoneSummon.o));
                    ForceBossState(BOSS_RING_OF_LAW, IN_PROGRESS);
                    return;
                case FAIL:
                    // Stock: Grimstone goes, the area trigger waits 2 min, the slot is NOT_STARTED again.
                    if (Creature* grimstone = instance->GetCreature(_grimstone))
                        grimstone->DespawnOrUnsummon();
                    _timeRingFail = GameTime::GetGameTime().count();
                    if (EncoreWipeUnlights(_encoreRunning, _bannerBurned != 0))
                    {
                        // Section 10: a wipe in the Encore puts the banner out (it stays thrown: burnable again).
                        LOG_INFO(kLog, "brd instance encore wipe: the banner is out");
                        _bannerBurned = 0;
                        SaveToDB();
                    }
                    _encoreRunning = false;
                    _encoreWon = false;
                    ForceBossState(BOSS_RING_OF_LAW, NOT_STARTED);
                    return;
                default:
                    ForceBossState(BOSS_RING_OF_LAW, EncounterState(data));
                    return;
            }
        }

        void StandDownSpectator(Creature* spectator)
        {
            spectator->SetFaction(kFactionNeutral);
            spectator->SetReactState(REACT_DEFENSIVE);
        }

        // Section 10: the gallery stand-down for a section 2 start (every gallery unit; stock stands down only the
        // spectators, peasants and citizens after a real Ring win).
        void TrackGalleryUnit(Creature* creature)
        {
            if (!IsGalleryUnit(creature->GetEntry(), creature->GetDistance2d(kRingCenter.x, kRingCenter.y),
                creature->GetPositionZ()))
                return;
            _gallery.push_back(creature->GetGUID());
            if (_galleryStoodDown && creature->IsAlive() && !creature->IsInCombat())
                StandDownSpectator(creature);
        }

        void StandDownGallery()
        {
            if (!_galleryStoodDown)
            {
                _galleryStoodDown = 1;
                SaveToDB();
            }
            uint32 count = 0;
            for (ObjectGuid const& guid : _gallery)
                if (Creature* unit = instance->GetCreature(guid))
                    if (unit->IsAlive() && !unit->IsInCombat())
                    {
                        StandDownSpectator(unit);
                        ++count;
                    }
            LOG_INFO(kLog, "brd instance gallery stood down: {} unit(s)", count);
        }

        // No slot started yet (a first entry into a fresh instance).
        bool AnySlotStarted() const
        {
            for (uint32 i = 0; i < kBossCount; ++i)
                if (Slot(i) == IN_PROGRESS || Slot(i) == DONE)
                    return true;
            return false;
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Vault (section 7 #17; D9 owns the fight)
        // ------------------------------------------------------------------------------------------------------------
        // At create only (the four of the room, by entry, or an 8905 inside the room); a death counts by entry and by
        // the list (CountsAsVaultWarder), never by where the unit died.
        bool IsVaultConstruct(Creature const* creature) const
        {
            return IsVaultConstructAt(creature->GetEntry(),
                creature->GetDistance2d(kVaultCenter.x, kVaultCenter.y));
        }

        bool IsListedVaultConstruct(ObjectGuid const& guid) const
        {
            return std::find(_vaultConstructs.begin(), _vaultConstructs.end(), guid) != _vaultConstructs.end();
        }

        void OnVaultConstructCreate(Creature* creature)
        {
            // Only the four constructs in the Relic Coffer room belong to the Vault; the rest of the Black Vault's are
            // trash (stock). A dead one with a pending respawn is loaded too: it comes back (EVENT_VAULT_RESPAWN) while
            // the Vault is not DONE, so a cold load can always restart the event (rule 7).
            if (!IsVaultConstruct(creature))
                return;
            if (std::find(_vaultConstructs.begin(), _vaultConstructs.end(), creature->GetGUID())
                == _vaultConstructs.end())
                _vaultConstructs.push_back(creature->GetGUID());
            // NOT_STARTED: stoned until the start. DONE (R-1-KIT m3, section 10 default): one that respawns after the
            // Vault is done stays a statue for good.
            if (creature->IsAlive() && (Slot(BOSS_VAULT) == NOT_STARTED || Slot(BOSS_VAULT) == DONE))
                FreezeVaultConstruct(creature);
            else if (!creature->IsAlive() && Slot(BOSS_VAULT) != DONE && _settled)
                events.RescheduleEvent(EVENT_VAULT_RESPAWN, 1s);    // never Respawn inside AddToMap
        }

        // Stock: Stoned (cast, not an addon aura: an evade re-applies addon auras), immune to players, not selectable
        // (the reference video; vmangos), passive until the Vault starts.
        // R-2-A MA-2: a Vault Sentinel takes D9's Stoned copy (its immunity set 1972 drops the stock aura's FREEZE
        // mechanic); its dormant state is NOT_SELECTABLE, which its script reads.
        void FreezeVaultConstruct(Creature* construct)
        {
            uint32 const stoned = construct->GetEntry() == NPC_BRD_VAULT_SENTINEL ? kSpellVaultStoned : kSpellStoned;
            if (!construct->HasAura(stoned))
                construct->CastSpell(construct, stoned, true);
            construct->SetImmuneToPC(true);
            construct->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            construct->SetReactState(REACT_PASSIVE);
        }

        void WakeVaultConstruct(Creature* construct)
        {
            construct->RemoveAurasDueToSpell(kSpellStoned);
            construct->RemoveAurasDueToSpell(kSpellVaultStoned);
            construct->SetImmuneToPC(false);
            construct->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            construct->SetReactState(REACT_AGGRESSIVE);
        }

        void StartVault()
        {
            // D9 request 1: the Vault Sentinels wake on the Safe's clock (D9), never here; only a stock 8905 construct
            // (no D9 script) is woken by the instance.
            for (ObjectGuid const& guid : _vaultConstructs)
                if (Creature* construct = instance->GetCreature(guid))
                    if (construct->IsAlive() && construct->GetEntry() != NPC_BRD_VAULT_SENTINEL)
                        WakeVaultConstruct(construct);

            // Stock: Doomgrip at the room entrance (cmangos), never ObjectData (summoned per attempt).
            if (TempSummon* doomgrip = instance->SummonCreature(NPC_DOOMGRIP, Position(kDoomgripSummon.x,
                kDoomgripSummon.y, kDoomgripSummon.z, kDoomgripSummon.o)))
                doomgrip->SetTempSummonType(TEMPSUMMON_MANUAL_DESPAWN);

            _vaultSinceStartMs = 0;
            _vaultIdleMs = 0;
            events.ScheduleEvent(EVENT_VAULT_WATCH, Milliseconds(kVaultWatchMs));
            LOG_INFO(kLog, "brd instance vault started");
        }

        // A wipe (section 3.7): the sentinels re-stone, Doomgrip despawns; the Dark Coffer's gossip starts it again.
        void ResetVault()
        {
            events.CancelEvent(EVENT_VAULT_WATCH);
            if (Creature* doomgrip = instance->GetCreature(_doomgrip))
                doomgrip->DespawnOrUnsummon();
            _doomgrip.Clear();
            _doomgripItem = 0;
            for (ObjectGuid const& guid : _vaultConstructs)
            {
                Creature* construct = instance->GetCreature(guid);
                if (!construct || !construct->IsAlive())
                    continue;
                if (construct->IsInCombat() && construct->IsAIEnabled && construct->AI())
                    construct->AI()->EnterEvadeMode();
                FreezeVaultConstruct(construct);
            }
            events.ScheduleEvent(EVENT_VAULT_RESPAWN, 1s);
            LOG_INFO(kLog, "brd instance vault reset");
        }

        void RespawnVaultConstructs()
        {
            if (Slot(BOSS_VAULT) == DONE)
                return;
            for (ObjectGuid const& guid : _vaultConstructs)
            {
                Creature* construct = instance->GetCreature(guid);
                if (!construct)
                    continue;
                if (!construct->IsAlive())
                {
                    if (ObjectGuid::LowType const spawnId = construct->GetSpawnId())
                        instance->ForceCreatureRespawn(spawnId);
                    else
                        construct->Respawn(true);
                }
                else if (Slot(BOSS_VAULT) == NOT_STARTED)
                    FreezeVaultConstruct(construct);
            }
        }

        void OnVaultWarderDeath(Creature* creature)
        {
            if (Slot(BOSS_VAULT) != IN_PROGRESS)
                return;
            if (!CountsAsVaultWarder(creature->GetEntry(), IsListedVaultConstruct(creature->GetGUID())))
                return;     // the Black Vault's 8905 trash (stock) is not listed
            if (!AnyVaultWarderAlive())
            {
                LOG_INFO(kLog, "brd instance vault done");
                SetData(TYPE_VAULT, DONE);
            }
        }

        bool AnyVaultWarderAlive()
        {
            if (Creature* doomgrip = instance->GetCreature(_doomgrip))
                if (doomgrip->IsAlive() && !doomgrip->isDying())
                    return true;
            for (ObjectGuid const& guid : _vaultConstructs)
                if (Creature* construct = instance->GetCreature(guid))
                    if (construct->IsAlive() && !construct->isDying())
                        return true;
            return false;
        }

        bool AnyVaultWarderInCombat()
        {
            if (Creature* doomgrip = instance->GetCreature(_doomgrip))
                if (doomgrip->IsAlive() && doomgrip->IsInCombat())
                    return true;
            for (ObjectGuid const& guid : _vaultConstructs)
                if (Creature* construct = instance->GetCreature(guid))
                    if (construct->IsAlive() && construct->IsInCombat())
                        return true;
            return false;
        }

        // An attempt nobody fights ends (a wipe with the stock SmartAI warders, who never report one).
        void VaultWatch()
        {
            if (Slot(BOSS_VAULT) != IN_PROGRESS)
                return;
            _vaultSinceStartMs += kVaultWatchMs;
            _vaultIdleMs = AnyVaultWarderInCombat() ? 0 : _vaultIdleMs + kVaultWatchMs;
            switch (VaultWatchFor(_vaultSinceStartMs, _vaultIdleMs, AnyVaultWarderAlive()))
            {
                case VaultWatchVerdict::Done:
                    // R-1-KIT B1: every warder is dead but no death finished it (the fallback).
                    LOG_INFO(kLog, "brd instance vault done (watch: no warder alive)");
                    SetData(TYPE_VAULT, DONE);
                    return;
                case VaultWatchVerdict::Lost:
                    LOG_INFO(kLog, "brd instance vault idle {} ms: the attempt is over", _vaultIdleMs);
                    ForceBossState(BOSS_VAULT, NOT_STARTED);
                    return;
                default:
                    break;
            }
            events.ScheduleEvent(EVENT_VAULT_WATCH, Milliseconds(kVaultWatchMs));
        }

        // Without the SmartAI opener row (DATA_VAULT_OPENER): the player nearest the coffer when it fired (the clicker
        // stands at it); the row's guid, sent in the same tick, replaces it.
        void NoteNearestCofferPlayer()
        {
            GameObject const* coffer = GetGameObject(GO_DARK_COFFER_DOOR);
            if (!coffer)
                return;
            Player* nearest = nullptr;
            float best = 0.f;
            for (MapReference const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    float const d = player->GetDistance(coffer);
                    if (player->IsAlive() && d <= kDarkCofferReachYd && (!nearest || d < best))
                    {
                        nearest = player;
                        best = d;
                    }
                }
            if (nearest)
                _vaultOpener = nearest->GetGUID();
        }

        // Section 10 (orchestrator ruling): the Dark Keeper Key is spent only when the Vault completes, one per
        // instance (the Vault is DONE once): the opener's, else any member of the opener's group (or any player when
        // the opener is gone) in the instance carrying one, else none.
        void TakeDarkKeeperKey()
        {
            Player* opener = _vaultOpener ? ObjectAccessor::GetPlayer(instance, _vaultOpener) : nullptr;
            Player* holder = opener && opener->HasItemCount(kItemDarkKeeperKey, 1) ? opener : nullptr;
            if (!holder)
                for (MapReference const& ref : instance->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (player && player->HasItemCount(kItemDarkKeeperKey, 1)
                        && (!opener || !opener->GetGroup() || player->GetGroup() == opener->GetGroup()))
                    {
                        holder = player;
                        break;
                    }
                }
            _vaultOpener.Clear();
            if (!holder)
            {
                LOG_INFO(kLog, "brd instance vault done: nobody carries a Dark Keeper Key");
                return;
            }
            holder->DestroyItemCount(kItemDarkKeeperKey, 1, true);
            LOG_INFO(kLog, "brd instance vault done: took {}'s Dark Keeper Key (opener {})", holder->GetName(),
                holder == opener ? "yes" : "no");
        }

        // ------------------------------------------------------------------------------------------------------------
        // The bar, the Lyceum, the senators, the Moira swap (stock)
        // ------------------------------------------------------------------------------------------------------------
        void RestoreBarDoor(GameObject* door)
        {
            switch (BarDoorState(_lovePotion == DONE, _bar, Slot(BOSS_PHALANX) == DONE))
            {
                case BarDoor::Open:
                    door->SetGoState(GO_STATE_ACTIVE);
                    break;
                case BarDoor::Blasted:
                    door->SetGoState(GO_STATE_ACTIVE_ALTERNATIVE);
                    break;
                default:
                    break;
            }
        }

        // Stock (d05ad7f82): a mug set down sends the nearest idle patron to drink it.
        void AssignAleMug(GameObject* go)
        {
            std::list<Creature*> patrons;
            go->GetCreatureListWithEntryInGrid(patrons, { NPC_GRIM_PATRON, NPC_GUZZLING_PATRON, NPC_HAMMERED_PATRON },
                kDarkIronAleRange);

            Creature* closestPatron = nullptr;
            SmartAI* closestPatronAI = nullptr;
            float closestDistance = kDarkIronAleRange;
            for (Creature* patron : patrons)
            {
                SmartAI* patronAI = CAST_AI(SmartAI, patron->AI());
                float const distance = go->GetDistance(patron);
                if (!patronAI || !patron->IsAlive() || patron->IsInCombat()
                    || patronAI->GetData(DATA_DARK_IRON_ALE) == DATA_DARK_IRON_ALE_DRINK || distance >= closestDistance)
                    continue;
                closestPatron = patron;
                closestPatronAI = patronAI;
                closestDistance = distance;
            }

            if (closestPatronAI)
            {
                closestPatron->SetEmoteState(EMOTE_STATE_NONE);
                closestPatronAI->SetData(DATA_DARK_IRON_ALE, DATA_DARK_IRON_ALE_DRINK, go);
            }
        }

        void SetLyceum(uint32 data)
        {
            _lyceum = data;
            if (data != DONE)
                return;
            HandleGameObject(DATA_GOLEM_DOOR_N, true);
            HandleGameObject(DATA_GOLEM_DOOR_S, true);
            if (Creature* magmus = GetCreature(DATA_MAGMUS))
                if (magmus->IsAIEnabled && magmus->AI())
                    magmus->AI()->Talk(kSayMagmusBraziersLit);
            ReplaceMoiraIfSaved();      // stock: the final boss is placed once she is spawned
            SaveToDB();
        }

        // Stock: each senator death pushes the share of the room's senators dead to Dagran's AI (his yells). Fixed:
        // Unit::setDeathState sets JUST_DIED before OnUnitDeath here, so the dying senator counts itself (the stock
        // "+1" counted it twice).
        void PushSenatorsDead()
        {
            if (_senators.empty())
                return;
            uint32 dead = 0;
            for (ObjectGuid const& guid : _senators)
                if (Creature* senator = instance->GetCreature(guid))
                    if (!senator->IsAlive() || senator->isDying())
                        ++dead;
            if (Creature* emperor = GetCreature(DATA_EMPEROR))
                if (emperor->IsAIEnabled && emperor->AI())
                    emperor->AI()->SetData(DATA_EMPEROR_SENATORS_DEAD,
                        std::min<uint32>(100, 100 * dead / uint32(_senators.size())));
        }

        // Stock: if every player in the instance finished Moira's quest (4004 / 4363) the High Priestess stands in
        // for her, else Moira. Fixed: the princess's guid follows the swap (DATA_MOIRA), and a failed summon keeps the
        // one on the dais.
        void ReplaceMoiraIfSaved()
        {
            // R-2-C m2: never mid-fight (the summon would be out of combat, untracked, and a caged Moira would come
            // back uncaged); the attempt's end (BOSS_EMPEROR NOT_STARTED / FAIL) runs it again.
            if (!MoiraSwapAllowed(Slot(BOSS_EMPEROR)))
                return;
            bool moiraSaved = true;
            for (MapReference const& ref : instance->GetPlayers())
                if (Player* player = ref.GetSource())
                    moiraSaved = moiraSaved && (player->GetQuestStatus(kQuestPrincessHorde) == QUEST_STATUS_REWARDED
                        || player->GetQuestStatus(kQuestPrincessAlliance) == QUEST_STATUS_REWARDED);

            ObjectGuid const toReplace = moiraSaved ? _moira : _priestess;
            uint32 const spawnEntry = moiraSaved ? uint32(NPC_PRIESTESS) : uint32(NPC_MOIRA);
            Creature* replaced = toReplace ? instance->GetCreature(toReplace) : nullptr;
            if (!replaced)
                return;
            // Her home spot: at an attempt's end she may still be walking back.
            if (instance->SummonCreature(spawnEntry, replaced->GetHomePosition()))
                replaced->RemoveFromWorld();
        }

        // Section 7 #19: she stands down after Dagran's death, and after the Avatar kill saved her, on every load.
        void ApplyMoiraStandDown(Creature* princess)
        {
            if (!princess->IsAlive() || !MoiraStandsDown(Slot(BOSS_EMPEROR), _moiraSaved != 0))
                return;
            princess->SetFaction(kFactionFriend);
            princess->SetReactState(REACT_PASSIVE);
        }

        // ------------------------------------------------------------------------------------------------------------
        // The Tomb of the Seven (stock: Doom'rel's gossip starts it, one ghost every 30 s, seven deaths end it; wave 2:
        // D21's rotation, the instance keeps the doors and the chest)
        // ------------------------------------------------------------------------------------------------------------
        void OnTombChanged(uint32 state)
        {
            TombDoors const doors = TombDoorsFor(state);
            HandleGameObject(GO_TOMB_ENTER, doors.enterOpen);
            HandleGameObject(GO_TOMB_EXIT, doors.exitOpen);
            switch (state)
            {
                case IN_PROGRESS:
                    _tombReleased = 0;
                    _tombResetMs = kTombResetMs;
                    if (!kWave2Bound)
                        events.ScheduleEvent(EVENT_TOMB_RELEASE, Milliseconds(kTombFirstReleaseMs));
                    break;
                case DONE:
                    _ghostKills = 7;
                    events.CancelEvent(EVENT_TOMB_RELEASE);
                    DoRespawnGameObject(GetObjectGuid(GO_CHEST_SEVEN), DAY);
                    break;
                default:
                    // R-1-KIT m2: a failed attempt (stock reset or D21's) starts the next one at no ghost.
                    events.CancelEvent(EVENT_TOMB_RELEASE);
                    _ghostKills = 0;
                    _tombReleased = 0;
                    if (kWave2Bound)
                    {
                        // D21: an attempt ended (the AI's wipe, a GM's state write): a full pool, and a ghost a GM
                        // killed alone back for the next challenge (the stock reset did both).
                        _sevenPool.Reset();
                        for (ObjectGuid const& guid : _seven)
                            if (Creature* ghost = instance->GetCreature(guid))
                                if (!ghost->IsAlive())
                                    ghost->Respawn();
                    }
                    break;
            }
        }

        void StockTombRelease()
        {
            if (Slot(BOSS_THE_SEVEN) != IN_PROGRESS || _ghostKills >= 7)
                return;
            if (_tombReleased < _seven.size())
            {
                if (Creature* ghost = instance->GetCreature(_seven[_tombReleased]))
                {
                    ++_tombReleased;
                    ghost->SetFaction(kFactionDarkIronDwarves);
                    ghost->SetImmuneToPC(false);
                    Player* target = ghost->SelectNearestPlayer(130.f);
                    if (target && ghost->CanCreatureAttack(target, true) && ghost->IsAIEnabled && ghost->AI())
                    {
                        ghost->AI()->AttackStart(target);
                        ghost->AI()->DoZoneInCombat();
                        _tombResetMs = kTombResetMs;
                    }
                }
            }
            events.ScheduleEvent(EVENT_TOMB_RELEASE, Milliseconds(kTombReleaseMs));
        }

        // Stock: no released ghost in combat for 15 s resets the Tomb (the dead ones come back, all turn friendly).
        void StockTombResetCheck(uint32 diff)
        {
            bool anyAlive = false;
            for (uint32 i = 0; i < _tombReleased && i < _seven.size(); ++i)
                if (Creature* ghost = instance->GetCreature(_seven[i]))
                {
                    anyAlive |= ghost->IsAlive();
                    if (ghost->IsAlive() && ghost->IsInCombat())
                    {
                        _tombResetMs = kTombResetMs;
                        return;
                    }
                }
            if (!anyAlive)
            {
                _tombResetMs = kTombResetMs;
                return;
            }
            if (_tombResetMs > diff)
            {
                _tombResetMs -= diff;
                return;
            }
            StockTombReset();
        }

        void StockTombReset()
        {
            for (uint32 i = 0; i < _seven.size(); ++i)
            {
                Creature* ghost = instance->GetCreature(_seven[i]);
                if (!ghost)
                    continue;
                if (!ghost->IsAlive())
                {
                    // stock: no EnterEvadeMode (it loops)
                    ghost->Respawn();
                    ghost->RemoveAllAuras();
                    ghost->GetThreatMgr().ClearAllThreat();
                    ghost->CombatStop(true);
                    ghost->LoadCreaturesAddon(true);
                    ghost->GetMotionMaster()->MoveTargetedHome();
                    ghost->SetLootRecipient(nullptr);
                }
                ghost->SetFaction(kFactionFriend);
                ghost->SetImmuneToPC(true);
                if (ghost->GetEntry() == NPC_DOOMREL && ghost->IsAIEnabled && ghost->AI())
                    ghost->AI()->Reset();       // stock: Doom'rel needs an explicit reset
            }
            _ghostKills = 0;
            _tombReleased = 0;
            SetData(TYPE_TOMB_OF_SEVEN, NOT_STARTED);
        }

        // ------------------------------------------------------------------------------------------------------------
        // Argelmach's hall release (stock, wave 1 only; ruling 56 removes it once D15 binds)
        // ------------------------------------------------------------------------------------------------------------
        void StockArgelmachInit()
        {
            Creature* argelmach = GetCreature(kGuidBossBase + BOSS_ARGELMACH);
            if (!argelmach || !argelmach->IsAIEnabled || !argelmach->AI())
                return;

            GuidList adds = _argelmachAdds;
            for (auto itr = adds.begin(); itr != adds.end();)
            {
                Creature* add = instance->GetCreature(*itr);
                bool const wakes = add && (add->GetEntry() == NPC_WRATH_HAMMER_CONSTRUCT
                    || (add->GetEntry() == NPC_RAGEREAVER_GOLEM && add->IsWithinDist2d(argelmach,
                        kArgelmachNearRange)));
                if (wakes)
                {
                    add->RemoveAurasDueToSpell(kSpellStoned);
                    if (add->IsAIEnabled && add->AI())
                        add->AI()->AttackStart(argelmach->GetVictim());
                    itr = adds.erase(itr);
                }
                else
                    ++itr;
            }

            if (!adds.empty())
            {
                argelmach->SetReactState(REACT_PASSIVE);
                argelmach->SetTarget();
                argelmach->AI()->SetData(DATA_GOLEM_LORD_ARGELMACH_INIT, IN_PROGRESS);
            }
            else
                argelmach->AI()->SetData(DATA_GOLEM_LORD_ARGELMACH_INIT, DONE);
        }

        void StockArgelmachAdds()
        {
            Creature* argelmach = GetCreature(kGuidBossBase + BOSS_ARGELMACH);
            if (!argelmach)
                return;
            argelmach->HandleEmoteCommand(EMOTE_ONESHOT_SHOUT);
            argelmach->m_Events.AddEventAtOffset(new ArgelmachRestoreAttack(argelmach), 3s);
            for (ObjectGuid const& guid : _argelmachAdds)
                if (Creature* add = instance->GetCreature(guid))
                    if (!add->IsInCombat())
                    {
                        add->RemoveAurasDueToSpell(kSpellStoned);
                        if (add->IsAIEnabled && add->AI())
                            add->AI()->AttackStart(argelmach->GetVictim());
                    }
        }

        EventMap events;
        bool _settled = false;
        bool _bypassGuard = false;
        bool _gmSlotWrite = false;

        // Tracked by hand (summoned, or a pair)
        ObjectGuid _verek;
        ObjectGuid _grimstone;
        ObjectGuid _doomgrip;
        ObjectGuid _moira;
        ObjectGuid _priestess;
        ObjectGuid _coren;
        std::array<ObjectGuid, 7> _seven{};
        DungeonKit::SharedHealthPool _sevenPool{ BrdTheSeven::PoolSpec() };     // D21 (TheSevenFight.h)
        GuidVector _ironhands;
        GuidVector _arenaSpectators;
        GuidVector _senators;
        GuidVector _gallery;            // section 10: every Ring gallery unit (TrackGalleryUnit)
        GuidVector _vaultConstructs;
        GuidList _argelmachAdds;

        // The Ring
        RingRolls _ring;
        uint32 _ringFavor = kRingFavorStart;
        time_t _timeRingFail = 0;
        uint32 _bannerThrown = 0;
        uint32 _bannerBurned = 0;
        bool _encoreWon = false;        // DATA_ENCORE_WON this attempt
        bool _encoreRunning = false;    // DATA_ENCORE_RUNNING
        uint32 _galleryStoodDown = 0;   // saved
        bool _anyPlayerEntered = false;

        // The Vault
        uint32 _cofferDoorsOpened = 0;
        uint32 _vaultClock = 0;
        uint32 _vaultSinceStartMs = 0;
        uint32 _vaultIdleMs = 0;
        uint32 _doomgripItem = 0;       // DATA_VAULT_DOOMGRIP_ITEM (saved)
        ObjectGuid _vaultOpener;        // DATA_VAULT_OPENER (in memory: a reload takes any member's key)

        // The bar, the Lyceum, the Tomb
        uint32 _bar = NOT_STARTED;
        uint32 _barAleCount = 0;
        uint32 _phalanxActivated = NOT_STARTED;
        uint32 _lovePotion = NOT_STARTED;
        uint32 _lyceum = NOT_STARTED;
        uint32 _ghostKills = 0;
        uint32 _tombReleased = 0;
        uint32 _tombResetMs = kTombResetMs;

        // The rope and the hard modes
        uint32 _rope = ROPE_NONE;
        uint32 _cinderUsed = 0;
        uint32 _consoleArmed = 0;
        uint32 _avatar = 0;
        uint32 _moiraSaved = 0;
    };

    InstanceScript* GetInstanceScript(InstanceMap* map) const override
    {
        return new instance_blackrock_depths_rework_InstanceMapScript(map);
    }
};

void AddSC_instance_blackrock_depths_rework()
{
    new instance_blackrock_depths_rework();
}
