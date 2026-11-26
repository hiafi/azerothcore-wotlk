/*
 * mod-dungeon-bosses, Zul'Farrak (map 209): the shared ids, boss states, data ids, crew modes, the Pyramid's stage
 * machine, the instance's pure rules, measured points, arenas, health and the save string of the Zul'Farrak build
 * (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md sections 3.1 to 3.3, 3.6 to 3.8, 3.12, 7 and the user's
 * rulings in section 10; build spec docs/dungeons/zul-farrak-rework.md, "SP", whose rulings 45 to 47 and Build spec
 * rows win over older text in it).
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKit*.h), so every <Boss>Logic.h and its host test can
 * include it. Engine glue is ZulFarrakKit.h and the shared kit (src/Kit/).
 *
 * Ownership: this file belongs to WP-S0 until it reports, then to the orchestrator. A boss WP keeps its spell ids
 * (inside its slice below), its script-local enums and its tuning (`namespace Tune`, rule 32) in its own
 * <Boss>Logic.h, and asks for a change here in its report ("Shared-file request").
 *
 * Mirrored stock code (AGENTS.md credit rule): the Pyramid's stage order, the wave tables, the crew's stair, descent
 * and gather points and Weegli's door spot are re-implemented from src/server/scripts/Kalimdor/ZulFarrak/
 * (instance_zulfarrak.cpp, zulfarrak.cpp; untouched): c9315e3ec moostigre <moostigre@proton.me> (#27731, the pyramid
 * event fixes, the End Door save, Weegli's door walk), 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>
 * (#7855, the crew scripts' origin), df82d1be9 jrad7 <106174524+jrad7@users.noreply.github.com> (#26183, Sezz'ziz's add
 * points). Every upstream merge re-diffs those files against c9315e3ec.
 *
 * Frame: +x is north, +y is west (WoW's own; SP's compass words mean the same). DB positions are exact; every other
 * point and polygon is [navmesh estimate]: the polygons were cut from the 209 mmtiles on a 0.5 yd raster by WP-S0 (the
 * outer ring of each room's flooded floor, Douglas-Peucker 1 to 2 yd, holes filled). The playtest checks key points
 * with `.dbtest zf instance where` and .gps.
 */

#ifndef MOD_DUNGEON_BOSSES_ZUL_FARRAK_REWORK_H
#define MOD_DUNGEON_BOSSES_ZUL_FARRAK_REWORK_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace ZulFarrakRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapZulFarrak = 209;
    // The stock instance name (section 7 #2 A): modules load after the core scripts, and a database-bound script
    // registered later under the same name replaces the earlier one, so instance_template 209 is untouched.
    char constexpr kInstanceScriptName[] = "instance_zulfarrak";
    // `.dbtest zf <key> <subcommand>`: the kit shell's command name, nested under the shared `.dbtest` root.
    char constexpr kTestCommand[] = "dbtest zf";
    // DungeonKit::LogMechanic(kLogDungeon, "<boss>", "<mechanic>", ...) = "zf-build <boss> <mechanic> ..." (s3.5).
    char constexpr kLogDungeon[] = "zf-build";

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)). Slot = the DungeonEncounter bit of encounters 593 to 600
    // (section 3.2 item 1), so the completed-encounter mask and the slots agree; slot 8 has no DBC row. The order is
    // fixed: the save string stores them by position.
    // ----------------------------------------------------------------------------------------------------------------
    enum ZfBosses : std::uint32_t
    {
        BOSS_VELRATHA           = 0,    // D7, encounter 593: the pool's phase 1 (reopened with slot 1 on a pool wipe)
        BOSS_GAHZRILLA          = 1,    // D7, encounter 594: the pool encounter
        BOSS_ANTUSUL            = 2,    // D2, encounter 595
        BOSS_THEKA              = 3,    // D1, encounter 596
        BOSS_ZUMRAH             = 4,    // D3, encounter 597
        BOSS_PYRAMID            = 5,    // D4a / D4b, encounter 598 (re-pointed: credit spell 213840); the INSTANCE
                                        // writes it (the stage machine), never a BossAI
        BOSS_CREW               = 6,    // D5, encounter 599 (re-pointed: credit spell 213841); the INSTANCE writes it
                                        // (DATA_CREW_FIGHT), never a BossAI
        BOSS_UKORZ              = 7,    // D6, encounter 600 (the Finder end, kill credit on Ukorz)
        BOSS_CREW_AT_THE_POOL   = 8,    // D7Ha: the hard mode kill (DONE = Gahz'rilla died with DATA_HARD_MODE)
    };
    std::uint32_t constexpr kBossCount = 9;
    std::uint32_t constexpr kEncounterBossCount = 8;    // slots 0 to 7 carry DungeonEncounter bits 0 to 7

    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Hydromancer Velratha", "Gahz'rilla", "Antu'sul", "Theka the Martyr", "Witch Doctor Zum'rah", "The Pyramid",
        "Sergeant Bly's Crew", "Chief Ukorz Sandscalp", "The Crew at the Pool (hard mode)",
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids. 0, 1 and 2 keep their stock meaning for the stock readers (handoff 2.2,
    // appendix A1: DC's events, the Finder); the rest are the build's own (section 3.2 item 2).
    // ----------------------------------------------------------------------------------------------------------------
    enum ZfData : std::uint32_t
    {
        // Stock (Get only; a stock SetData is ignored with a debug line: its writers are dropped by the S0 rev).
        DATA_PYRAMID            = 0,    // the stock phase 0 to 12 derived from the stage (StockPyramidPhase)
        DATA_GAHZRILLA          = 1,    // 0 until slot 1 is DONE, then 4 (the stock SmartAI's value)
        DATA_END_DOOR           = 2,    // 0 shut, 1 Weegli on his way (not saved), 3 blown (saved). Set: CR's Weegli
                                        // sends 1 when he starts his walk and 3 when the barrel goes off

        // The Pyramid (Get)
        DATA_PYRAMID_STAGE      = 20,   // PyramidStage: the stage in play (or next to play); 4 when done
        DATA_PYRAMID_RUNNING    = 21,   // 1 while the stage in play is in progress
        DATA_PYRAMID_CAGES      = 22,   // Get 1 once the cages opened (stage 2 began). Set(1): go_zf_troll_cage
        DATA_OFFERINGS          = 23,   // normal: Offerings stacks, 0 to 4 (PY3; the instance counts them)
        DATA_BLOOD_PRICE        = 24,   // heroic: Blood Price stacks (PY16). Set(n): D4a / D4b's per-second tick
                                        // writes the new total; a crew loss on the Block adds kBloodPricePerCrew

        // The Pyramid (Set only: the stage machine's commands; the argument is the stage)
        DATA_PYRAMID_START      = 30,   // Set(stage): the stage begins (refused unless it is the one in play, idle)
        DATA_PYRAMID_COMPLETE   = 31,   // Set(stage): its owner says it is won (D4b: stage 2's last troll)
        DATA_PYRAMID_FAIL       = 32,   // Set(stage): its owner says it is lost (D4a: the Executioner evaded)

        // The crew
        DATA_CREW_ALIVE         = 40,   // Get: the CrewMember bit mask of the living crew (saved)
        DATA_CREW_PATH          = 41,   // Get / Set: CrewPath (Set refused by CrewPathAllowed); 0 again after a wipe
        DATA_CREW_DONE          = 42,   // Get: 1 when slot 6 is DONE
        DATA_CREW_FIGHT         = 43,   // Set: D5, IN_PROGRESS at the pull, NOT_STARTED at a wipe, DONE at the end
        DATA_CREW_LOST          = 44,   // Set(member): a crew member's death the instance did not see (it watches
                                        // OnUnitDeath itself; a second report is harmless)
        DATA_CREW_AT_POOL       = 45,   // Get: the mask of living crew standing at the pool (0 until CR's Set(1)
                                        // says they arrived); saved
        DATA_CREW_AT_END        = 46,   // Get: the crew mask when the Pyramid was won (the Test's key; saved)
        DATA_TEST_KEY           = 47,   // Get: 1 while Bly may offer the Test (TestAllowed)
        DATA_CREW_MODE_BASE     = 50,   // 50 + CrewMember: Get / Set the member's CrewMode (Set logs the change and
                                        // sends ACTION_ZF_CREW_MODE to the member)

        // The pool and the hard mode
        DATA_GONG_STRUCK        = 60,   // Set(1): Velratha struck the gong (GZ10): the hard mode arms if
                                        // HardModeArmAllowed, then the instance summons Gahz'rilla
        DATA_HARD_MODE          = 61,   // Get: The Crew at the Pool is armed (saved; holds for the lockout)
        DATA_HARD_MODE_KILLED   = 62,   // Get: slot 8 DONE
        DATA_HARD_MODE_KEY      = 63,   // Get: 1 when the hard mode would arm now (D7Ha reads it at Velratha's pull)

        // GM test commands (.dbtest zf; never sent by a boss)
        DATA_GM_STAGE           = 90,   // Set(stage): force that stage in play, idle (4: the Pyramid DONE)
        DATA_GM_CREW_MASK       = 91,   // Set(mask): the living crew (Weegli is always alive)
        DATA_GM_DOOR            = 92,   // Set(0|1): shut / blow the End Door
        DATA_GM_TEST_ARM        = 93,   // Set(1): heroic only: the Pyramid DONE with all five alive (the Test's key)
        DATA_GM_HARD_MODE       = 94,   // Set(0|1): heroic only, never while slot 1 fights or is DONE
    };

    // GetGuidData keys (ObjectData: spawned single units only; the summons by hand, never in ObjectData).
    std::uint32_t constexpr kGuidBossBase = 100;    // + slot: Velratha 100, Antu'sul 102, Theka 103, Zum'rah 104,
                                                    // Ukorz 107 (Gahz'rilla 101 and 108: the tracked summon below)
    std::uint32_t constexpr kGuidExecutioner = 110;
    std::uint32_t constexpr kGuidRuuzlu = 111;
    std::uint32_t constexpr kGuidGahzrilla = 112;   // summoned by the instance (tracked by hand)
    std::uint32_t constexpr kGuidSezzziz = 113;     // summoned by D4b (tracked by hand from OnCreatureCreate)
    std::uint32_t constexpr kGuidNekrum = 114;      // idem
    std::uint32_t constexpr kGuidCrewBase = 120;    // + CrewMember
    std::uint32_t constexpr kGuidEndDoor = 130;
    std::uint32_t constexpr kGuidGong = 131;

    // DoAction values the instance sends (never on a load: a create reads the data instead).
    enum ZfActions : std::int32_t
    {
        ACTION_ZF_CREW_MODE         = 20901,    // to a crew member: its mode changed (read DATA_CREW_MODE_BASE + m)
        ACTION_ZF_PYRAMID_STAGE     = 20902,    // to every crew member and the Executioner: a stage began, ended or
                                                // was lost (read DATA_PYRAMID_STAGE / _RUNNING)
        ACTION_ZF_CREW_FIGHT        = 20903,    // to every crew member: slot 6 changed (read DATA_CREW_FIGHT's state
                                                // with GetBossState(BOSS_CREW) and DATA_CREW_PATH)
        ACTION_ZF_HARD_MODE_ARMED   = 20904,    // to Velratha and Gahz'rilla: DATA_HARD_MODE went 0 -> 1
        ACTION_ZF_POOL_RESET        = 20905,    // to every crew member: a pool wipe brought the five back
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures. Script names in the comments are fixed (section 3.1). A boss stub's is bound by its DT file; an add's
    // is registered by its WP in the change that declares the creature (an unbound registered name logs "not
    // assigned").
    // ----------------------------------------------------------------------------------------------------------------
    enum ZfCreatures : std::uint32_t
    {
        NPC_THEKA                   = 7272,     // boss_theka_rework (D1)
        NPC_ANTUSUL                 = 8127,     // boss_antusul_rework (D2)
        NPC_ANTUSUL_SERVANT         = 8156,     // npc_antusul_servant_rework (D2; no spawn)
        NPC_ZUMRAH                  = 7271,     // boss_zumrah_rework (D3)
        NPC_EXECUTIONER             = 7274,     // boss_sandfury_executioner_rework (D4a)
        NPC_SEZZZIZ                 = 7275,     // boss_sezzziz_rework (D4b; summoned by wave 3)
        NPC_NEKRUM                  = 7796,     // boss_nekrum_rework (D4b; summoned by wave 3)
        NPC_BLY                     = 7604,     // npc_bly_crew_bly (CR; D5 fights on it)
        NPC_RAVEN                   = 7605,     // npc_bly_crew_raven (CR)
        NPC_ORO                     = 7606,     // npc_bly_crew_oro (CR)
        NPC_WEEGLI                  = 7607,     // npc_bly_crew_weegli (CR)
        NPC_MURTA                   = 7608,     // npc_bly_crew_murta (CR)
        NPC_UKORZ                   = 7267,     // boss_ukorz_rework (D6)
        NPC_RUUZLU                  = 7797,     // boss_ruuzlu_rework (D6)
        NPC_VELRATHA                = 7795,     // boss_velratha_rework (D7)
        NPC_GAHZRILLA               = 7273,     // boss_gahzrilla_rework (D7; summoned by the instance)

        // stock units the scripts meet (stock SmartAI kept)
        NPC_SANDFURY_CRETIN         = 7789,
        NPC_SANDFURY_SLAVE          = 7787,
        NPC_SANDFURY_ACOLYTE        = 8876,
        NPC_SANDFURY_DRUDGE         = 7788,
        NPC_SANDFURY_ZEALOT         = 8877,
        NPC_SCARAB                  = 7269,
        NPC_WARD_OF_ZUMRAH          = 7785,
        NPC_SKELETON_OF_ZUMRAH      = 7786,

        // build creatures (creature 301005-301099, ids.yaml reservation `zul_farrak`); declared by their WP
        NPC_ZF_PERSECUTOR_SWARM     = 301005,   // D1
        NPC_ZF_PENITENT_SWARM       = 301006,   // D1
        NPC_ZF_THEKA_STALKER        = 301007,   // D1
        NPC_ZF_EMPTY_VESSEL         = 301010,   // D3 (the husk)
        NPC_ZF_LOST_SOUL            = 301011,   // D3
        NPC_ZF_BOUND_DEAD           = 301012,   // D3
        NPC_ZF_GRAVE_STALKER        = 301013,   // D3
        NPC_ZF_SANDFURY_BERSERKER   = 301015,   // D4b
        NPC_ZF_SANDFURY_HEXMASTER   = 301016,   // D4b
        NPC_ZF_SANDFURY_WITCH_DOCTOR = 301017,  // D4b
        NPC_ZF_WEEGLI_BARREL        = 301018,   // D4b
        NPC_ZF_PYRAMID_STALKER      = 301019,   // D4a / D4b (the chain and the lane)
        NPC_ZF_QUICKSAND            = 301025,   // D6
        NPC_ZF_CREEPING_SANDS       = 301026,   // D6
        NPC_ZF_PUDDLE               = 301030,   // D7
        NPC_ZF_WELLSPRING           = 301031,   // D7Ha
        NPC_ZF_SECOND_HEAD          = 301032,   // D7Hb
        NPC_ZF_STRIKE_STALKER       = 301033,   // D7Hb
        NPC_ZF_ENTRANCE_GOBLIN      = 301090,   // the quests WP ("Kizzi Fuseboot", section 10 #53)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum ZfGameObjects : std::uint32_t
    {
        GO_TROLL_CAGE_1         = 141070,   // go_zf_troll_cage (S0, the instance file), all five
        GO_TROLL_CAGE_2         = 141071,
        GO_TROLL_CAGE_3         = 141072,
        GO_TROLL_CAGE_4         = 141073,
        GO_TROLL_CAGE_5         = 141074,
        GO_END_DOOR             = 146084,   // opened by the instance (Weegli's DATA_END_DOOR 3 or the fallback)
        GO_WEEGLIS_BARREL       = 141612,   // stock look (spell 10772); its SmartAI dropped by the S0 rev
        GO_GONG                 = 141832,   // inert (S0 rev: no SmartAI, NOT_SELECTABLE); Velratha's GZ10 strikes it
        GO_ZF_CREW_STASH        = 301360,   // D5: the crew's stash chest, normal (gameobject 301360-301379)
        GO_ZF_CREW_STASH_HEROIC = 301361,   // D5: heroic
    };

    constexpr bool IsTrollCage(std::uint32_t entry)
    {
        return entry >= GO_TROLL_CAGE_1 && entry <= GO_TROLL_CAGE_5;
    }

    // Spawn ids the instance restores with Map::ForceCreatureRespawn (RB-20: DB spawns, 86,400 s respawn, dynamic
    // spawning, so a dead one leaves the object store) [verified: creature 2026-11-25].
    std::uint32_t constexpr kSpawnExecutioner = 81552;
    std::uint32_t constexpr kSpawnVelratha = 81570;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 213840-214239; the gear's `zul_farrak_items` 213800-213839 and its spell_zf_* script names, among
    // them spell_zf_static_discharge, are not ours). Each WP names its own ids, inside its slice, in its <Boss>Logic.h.
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 213840, 214239 };
    IdSlice constexpr kSpellsShared{ 213840, 213859 };          // S0 (credits, Weakened copy) and CR (213845-213859)
    IdSlice constexpr kSpellsTheka{ 213860, 213889 };           // D1
    IdSlice constexpr kSpellsAntusul{ 213890, 213919 };         // D2
    IdSlice constexpr kSpellsZumrah{ 213920, 213959 };          // D3
    IdSlice constexpr kSpellsBlock{ 213960, 213989 };           // D4a
    IdSlice constexpr kSpellsStair{ 213990, 214029 };           // D4b
    IdSlice constexpr kSpellsCrewFight{ 214030, 214069 };       // D5
    IdSlice constexpr kSpellsUkorz{ 214070, 214109 };           // D6
    IdSlice constexpr kSpellsPool{ 214110, 214149 };            // D7
    IdSlice constexpr kSpellsPoolCrew{ 214150, 214189 };        // D7Ha
    IdSlice constexpr kSpellsDeluge{ 214190, 214209 };          // D7Hb
    IdSlice constexpr kSpellsSpare{ 214210, 214239 };

    inline std::array<IdSlice, 11> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsTheka, kSpellsAntusul, kSpellsZumrah, kSpellsBlock, kSpellsStair, kSpellsCrewFight,
        kSpellsUkorz, kSpellsPool, kSpellsPoolCrew, kSpellsDeluge,
    } };

    IdSlice constexpr kSpellsCrewAlly{ 213845, 213859 };        // CR's part of the shared slice (the ally kits)
    IdSlice constexpr kCreaturesReservation{ 301005, 301099 };
    IdSlice constexpr kGameObjectsReservation{ 301360, 301379 };

    enum ZfSharedSpells : std::uint32_t
    {
        SPELL_ZF_PYRAMID_CREDIT     = 213840,   // S0 (DT instance.py): encounter 598's credit (the Pyramid DONE)
        SPELL_ZF_CREW_CREDIT        = 213841,   // S0: encounter 599's credit (the crew's fight DONE)
        SPELL_ZF_WEAKENED_COPY      = 213842,   // reserved (a script-applied Weakened, if a WP needs one)
        // 213843-213844 spare; 213845-213859 CR's ally kits
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The crew (section 3.2 item 4, 3.12): five members, one bit each; CR owns their behavior, the instance their mode
    // ----------------------------------------------------------------------------------------------------------------
    enum CrewMember : std::uint32_t
    {
        CREW_BLY        = 0,
        CREW_RAVEN      = 1,
        CREW_ORO        = 2,
        CREW_WEEGLI     = 3,    // never dies (CR: 1 health until the pool), never offered, never taken to the Block
        CREW_MURTA      = 4,
    };
    std::uint32_t constexpr kCrewCount = 5;
    std::uint32_t constexpr kCrewAll = (1u << kCrewCount) - 1;
    std::uint32_t constexpr kCrewWeegliBit = 1u << CREW_WEEGLI;
    // Bly, Raven, Oro and Murta: the Block's pool, the crew fight's four
    std::uint32_t constexpr kCrewFighters = kCrewAll & ~kCrewWeegliBit;

    constexpr std::uint32_t CrewBit(std::uint32_t member) { return 1u << member; }

    inline std::array<std::uint32_t, kCrewCount> constexpr kCrewEntries{ { NPC_BLY, NPC_RAVEN, NPC_ORO, NPC_WEEGLI,
        NPC_MURTA } };
    // [verified: creature 2026-11-25] guids 81555, 81557, 81554, 81553, 81556
    inline std::array<std::uint32_t, kCrewCount> constexpr kCrewSpawnIds{ { 81555, 81557, 81554, 81553, 81556 } };
    inline std::array<char const*, kCrewCount> constexpr kCrewNames{ { "Bly", "Raven", "Oro", "Weegli", "Murta" } };

    constexpr std::optional<std::uint32_t> CrewIndexOf(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kCrewCount; ++i)
            if (kCrewEntries[i] == entry)
                return i;
        return std::nullopt;
    }

    // What a crew member is doing (section 3.2 item 4). The instance stores it; CR's AI applies it (faction, react
    // state, gossip, movement); D4a, D5 and D7Ha set the transient ones through CR's BlyCrew.h.
    enum class CrewMode : std::uint8_t
    {
        Caged       = 0,    // in the cages (Block and before): faction 35, passive
        Prisoner    = 1,    // D4a: torn from the cage and chained at the Executioner's feet (transient)
        Ally        = 2,    // stages 2 and 3: fights beside the group (faction 495)
        Gather      = 3,    // the plaza gather spots after the Pyramid: Bly's gossip
        Boss        = 4,    // D5: the crew fight (faction 41); Weegli never
        Yielded     = 5,    // D5, the Test: yielded at 30% (transient until the fight ends)
        PoolAlly    = 6,    // the Test path: at the pool with the group (faction 35, D7Ha's allies)
        Gone        = 7,    // the betrayal is over: dead, or Weegli left for good
    };
    std::uint32_t constexpr kCrewModeCount = 8;

    inline std::array<char const*, kCrewModeCount> constexpr kCrewModeNames{ {
        "caged", "prisoner", "ally", "gather", "boss", "yielded", "poolally", "gone",
    } };

    constexpr bool ValidCrewMode(std::uint32_t mode) { return mode < kCrewModeCount; }

    enum CrewPath : std::uint32_t
    {
        CREW_PATH_OPEN      = 0,    // not chosen (or chosen and wiped: offered again)
        CREW_PATH_BETRAYAL  = 1,    // Bly's stock gossip option, the fight to the death (normal and heroic)
        CREW_PATH_TEST      = 2,    // Bly's Test (heroic, all five alive at the Pyramid's end)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The Pyramid's stage machine (section 3.2 item 3, section 7 #11 A): the last completed stage is kept; each start
    // snapshots the crew mask, the Offerings and the Blood Price; a wipe restores the snapshot and the stage waits to
    // be played again; a crew loss is permanent only once its stage is won.
    // ----------------------------------------------------------------------------------------------------------------
    enum PyramidStage : std::uint32_t
    {
        PYRAMID_STAGE_NONE  = 0,    // nothing begun: the Executioner never pulled, the cages closed
        PYRAMID_STAGE_BLOCK = 1,    // stage 1, the Block: from the Executioner's pull to his death
        PYRAMID_STAGE_STAIR = 2,    // stage 2, the Stair: from the cages opening to wave 2's last troll
        PYRAMID_STAGE_ALTAR = 3,    // stage 3, the Altar: from the descent to the deaths of Sezz'ziz and Nekrum
        PYRAMID_STAGE_DONE  = 4,    // slot 5 DONE
    };

    inline std::array<char const*, 5> constexpr kPyramidStageNames{ { "none", "block", "stair", "altar", "done" } };

    std::uint32_t constexpr kOfferingsCap = 4;              // PY3, normal: one per crew member lost on the Block
    std::uint32_t constexpr kBloodPricePerCrew = 30;        // PY16, heroic: a crew member lost on the Block
    std::uint32_t constexpr kAltarDelayMs = 5000;           // wave 2 dead to the descent (stock "home spots" timer)
    std::uint32_t constexpr kStairRestartMs = 10000;        // a living player 10 s on the landing restarts stage 2
    std::uint32_t constexpr kPyramidWatchMs = 1000;         // the wipe and landing poll

    struct PyramidSnapshot
    {
        std::uint32_t crewAlive = kCrewAll;
        std::uint32_t offerings = 0;
        std::uint32_t bloodPrice = 0;
    };

    struct PyramidState
    {
        std::uint32_t stage = PYRAMID_STAGE_NONE;   // the stage in play (or next to play)
        bool running = false;
        bool cagesOpen = false;
        std::uint32_t crewAlive = kCrewAll;
        std::uint32_t offerings = 0;
        std::uint32_t bloodPrice = 0;
        std::uint32_t attempted = 0;                // bit per stage: begun at least once (a restart, for the logs)
        PyramidSnapshot snapshot;

        // The stage a start may name: NONE plays the Block.
        constexpr std::uint32_t InPlay() const { return stage == PYRAMID_STAGE_NONE ? PYRAMID_STAGE_BLOCK : stage; }
        constexpr PyramidSnapshot Live() const { return { crewAlive, offerings, bloodPrice }; }
        // What a save keeps: the snapshot while a stage runs (its losses are not permanent yet).
        constexpr PyramidSnapshot Saved() const { return running ? snapshot : Live(); }
    };

    enum class PyramidVerdict : std::uint8_t
    {
        Refused,
        Started,        // the stage's first start
        Restarted,      // a start after a wipe (or after a reload)
        Completed,
        Wiped,
    };

    // Start `stage`: it must be the one in play, idle, and stage 2 needs the cages open.
    constexpr PyramidVerdict PyramidStart(PyramidState& s, std::uint32_t stage)
    {
        if (s.running || stage < PYRAMID_STAGE_BLOCK || stage > PYRAMID_STAGE_ALTAR || stage != s.InPlay())
            return PyramidVerdict::Refused;
        if (stage == PYRAMID_STAGE_STAIR && !s.cagesOpen)
            return PyramidVerdict::Refused;
        bool const again = (s.attempted & (1u << stage)) != 0;
        s.stage = stage;
        s.running = true;
        s.attempted |= 1u << stage;
        s.snapshot = s.Live();
        return again ? PyramidVerdict::Restarted : PyramidVerdict::Started;
    }

    // The running stage `stage` is won: its losses stand, the next stage is in play (idle; the Altar is started by the
    // instance kAltarDelayMs later, the Stair by the cages).
    constexpr PyramidVerdict PyramidComplete(PyramidState& s, std::uint32_t stage)
    {
        if (!s.running || stage != s.stage)
            return PyramidVerdict::Refused;
        s.running = false;
        s.stage = stage + 1;
        s.snapshot = s.Live();
        return PyramidVerdict::Completed;
    }

    // The running stage `stage` is lost: back to its start.
    constexpr PyramidVerdict PyramidWipe(PyramidState& s, std::uint32_t stage)
    {
        if (!s.running || stage != s.stage)
            return PyramidVerdict::Refused;
        s.running = false;
        s.crewAlive = s.snapshot.crewAlive;
        s.offerings = s.snapshot.offerings;
        s.bloodPrice = s.snapshot.bloodPrice;
        return PyramidVerdict::Wiped;
    }

    // The cages open (go_zf_troll_cage): only once the Block is won (stage 2 in play). Returns whether they opened now.
    constexpr bool PyramidOpenCages(PyramidState& s)
    {
        if (s.stage != PYRAMID_STAGE_STAIR || s.cagesOpen)
            return false;
        s.cagesOpen = true;
        return true;
    }

    struct CrewLoss
    {
        bool counted = false;           // the bit was set and is now clear
        std::uint32_t offerings = 0;    // stacks added (normal, the Block)
        std::uint32_t bloodPrice = 0;   // stacks added (heroic, the Block)
    };

    // A crew member died during the Pyramid (section 3.2 item 3, PY3, PY16). Weegli never counts. On the Block, while
    // it runs: one Offering (normal, cap kOfferingsCap) or kBloodPricePerCrew Blood Price (heroic). Elsewhere only the
    // bit (stage 3's Blood Offering adds nothing). Outside a running stage nothing counts (a reload's settle).
    constexpr CrewLoss PyramidCrewLost(PyramidState& s, std::uint32_t member, bool heroic)
    {
        CrewLoss loss;
        if (member >= kCrewCount || member == CREW_WEEGLI || !(s.crewAlive & CrewBit(member)))
            return loss;
        s.crewAlive &= ~CrewBit(member);
        loss.counted = true;
        if (!s.running || s.stage != PYRAMID_STAGE_BLOCK)
            return loss;
        if (heroic)
        {
            loss.bloodPrice = kBloodPricePerCrew;
            s.bloodPrice += kBloodPricePerCrew;
        }
        else if (s.offerings < kOfferingsCap)
        {
            loss.offerings = 1;
            ++s.offerings;
        }
        return loss;
    }

    // "Wipe" (section 3.2 item 3): a stage runs and no living player is on the map inside the Pyramid region; crew
    // alone never keep it going.
    constexpr bool PyramidWiped(bool running, std::uint32_t livingPlayersInRegion)
    {
        return running && livingPlayersInRegion == 0;
    }

    // Stage 2 waits for kStairRestartMs of a living player on the landing (after a wipe or a reload).
    constexpr bool StairRestartWaits(PyramidState const& s)
    {
        return s.stage == PYRAMID_STAGE_STAIR && s.cagesOpen && !s.running;
    }

    // The stock DATA_PYRAMID phase (ZFPyramidPhases) for the stock readers: 0 before the cages, 3 (WAVE_1) on the
    // Stair, 7 (WAVE_3) at the Altar, 9 (MOVED_DOWNSTAIRS) once the Pyramid is won, 12 (DONE) once the crew's fight
    // is.
    constexpr std::uint32_t StockPyramidPhase(PyramidState const& s, bool crewDone)
    {
        if (crewDone)
            return 12;
        switch (s.stage)
        {
            case PYRAMID_STAGE_DONE:
                return 9;
            case PYRAMID_STAGE_ALTAR:
                return 7;
            case PYRAMID_STAGE_STAIR:
                return s.cagesOpen ? 3 : 0;
            default:
                return 0;
        }
    }

    // Stage 3 is won once both Sezz'ziz and Nekrum came into the world this attempt and neither is alive.
    constexpr bool AltarCleared(bool sezzzizSeen, bool sezzzizAlive, bool nekrumSeen, bool nekrumAlive)
    {
        return sezzzizSeen && nekrumSeen && !sezzzizAlive && !nekrumAlive;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The crew's mode by the run's state (a create, a reload, a stage change, a wipe)
    // ----------------------------------------------------------------------------------------------------------------
    struct CrewContext
    {
        std::uint32_t stage = PYRAMID_STAGE_NONE;
        bool cagesOpen = false;
        std::uint32_t crewSlot = DungeonKit::State::NotStarted;     // slot 6
        std::uint32_t path = CREW_PATH_OPEN;
    };

    // The resting mode of a member (alive or about to be restored): what a reload or a wipe puts it back to. The
    // transient modes (Prisoner, Boss, Yielded) are set live by D4a / D5 and never come back from a save.
    constexpr CrewMode CrewModeFor(CrewContext const& c)
    {
        if (c.crewSlot == DungeonKit::State::Done)
            return c.path == CREW_PATH_TEST ? CrewMode::PoolAlly : CrewMode::Gone;
        if (c.stage == PYRAMID_STAGE_DONE)
            return CrewMode::Gather;
        if ((c.stage == PYRAMID_STAGE_STAIR && c.cagesOpen) || c.stage == PYRAMID_STAGE_ALTAR)
            return CrewMode::Ally;
        return CrewMode::Caged;
    }

    // Whether a member must stand (be restored) now: during the Pyramid only the living mask's; after it all five stand
    // up for Bly's fight (section 7 #12 A) and on the Test path at the pool (a pool death is for the attempt only,
    // section 7 #16 A); the betrayal's fallen stay down.
    constexpr bool CrewMemberStands(CrewContext const& c, std::uint32_t crewAlive, std::uint32_t member)
    {
        if (c.crewSlot == DungeonKit::State::Done)
            return c.path == CREW_PATH_TEST && (crewAlive & CrewBit(member));
        if (c.stage == PYRAMID_STAGE_DONE)
            return true;
        return (crewAlive & CrewBit(member)) != 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bly's fight, the paths and the Test (section 7 #12, #14, #18, rulings 24 and 26)
    // ----------------------------------------------------------------------------------------------------------------

    // The Test's key: heroic, the Pyramid won with all five alive, the fight neither done nor running.
    constexpr bool TestAllowed(bool heroic, std::uint32_t pyramidStage, std::uint32_t crewAtEnd, std::uint32_t crewSlot)
    {
        return heroic && pyramidStage == PYRAMID_STAGE_DONE && crewAtEnd == kCrewAll
            && crewSlot != DungeonKit::State::Done && crewSlot != DungeonKit::State::InProgress;
    }

    // SetData(DATA_CREW_PATH, path): the choice is made out of combat before the pull; OPEN is a wipe's reset.
    constexpr bool CrewPathAllowed(std::uint32_t path, bool heroic, std::uint32_t pyramidStage, std::uint32_t crewAtEnd,
        std::uint32_t crewSlot)
    {
        if (crewSlot == DungeonKit::State::Done || crewSlot == DungeonKit::State::InProgress)
            return false;
        switch (path)
        {
            case CREW_PATH_OPEN:
                return true;
            case CREW_PATH_BETRAYAL:
                return pyramidStage == PYRAMID_STAGE_DONE;
            case CREW_PATH_TEST:
                return TestAllowed(heroic, pyramidStage, crewAtEnd, crewSlot);
            default:
                return false;
        }
    }

    // SetData(DATA_CREW_FIGHT, IN_PROGRESS): a path is chosen and the fight is not won.
    constexpr bool CrewFightStartAllowed(std::uint32_t pyramidStage, std::uint32_t path, std::uint32_t crewSlot)
    {
        return pyramidStage == PYRAMID_STAGE_DONE && path != CREW_PATH_OPEN && crewSlot != DungeonKit::State::Done
            && crewSlot != DungeonKit::State::InProgress;
    }

    // The betrayal's fallback end: the fight runs on the betrayal path and none of the four fighters is alive (D5 ends
    // the fight itself; this is for a stub, a GM kill or a missed message). The Test path ends only by D5 (a yield is
    // no death).
    constexpr bool CrewFightOverByDeaths(std::uint32_t crewSlot, std::uint32_t path, std::uint32_t fightersAlive)
    {
        return crewSlot == DungeonKit::State::InProgress && path == CREW_PATH_BETRAYAL
            && (fightersAlive & kCrewFighters) == 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The End Door (section 7 #13 A): Weegli's barrel opens it at the end of the crew's fight; the instance opens it
    // itself when slot 6 is DONE and the door is still shut kEndDoorFallbackMs later (or at once after a reload).
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kEndDoorFallbackMs = 60000;     // Weegli's 89 yd walk, the plant and the 2 s fuse
    std::uint32_t constexpr kEndDoorWatchMs = 2000;

    constexpr std::uint32_t SanitizeDoorState(std::uint32_t door)
    {
        return door == DungeonKit::State::Done ? DungeonKit::State::Done : DungeonKit::State::NotStarted;
    }

    // Whether the instance blows the door itself now (`sinceCrewDoneMs`: how long slot 6 has been DONE; a reload counts
    // as long ago).
    constexpr bool EndDoorFallbackDue(std::uint32_t crewSlot, std::uint32_t door, std::uint32_t sinceCrewDoneMs)
    {
        return crewSlot == DungeonKit::State::Done && door != DungeonKit::State::Done
            && sinceCrewDoneMs >= kEndDoorFallbackMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pool and the hard mode (section 3.2 items 6 and 7, 3.7; section 7 #16 A, #43 h A)
    // ----------------------------------------------------------------------------------------------------------------

    // The hard mode would arm now: heroic, the Test path won, all five living crew at the pool, its kill not done.
    constexpr bool HardModeKey(bool heroic, std::uint32_t path, std::uint32_t crewSlot, std::uint32_t crewAtPool,
        std::uint32_t hardModeSlot)
    {
        return heroic && path == CREW_PATH_TEST && crewSlot == DungeonKit::State::Done && crewAtPool == kCrewAll
            && hardModeSlot != DungeonKit::State::Done;
    }

    // The gong is struck (GZ10): the flag arms on the key, never once Gahz'rilla fights or is dead. Once armed it holds
    // for the lockout (a later pull with a crew member down stays the hard mode, section 7 #16 A).
    constexpr bool HardModeArmAllowed(bool heroic, std::uint32_t path, std::uint32_t crewSlot, std::uint32_t crewAtPool,
        std::uint32_t gahzrillaSlot, std::uint32_t hardModeSlot)
    {
        return HardModeKey(heroic, path, crewSlot, crewAtPool, hardModeSlot)
            && gahzrillaSlot != DungeonKit::State::Done && gahzrillaSlot != DungeonKit::State::InProgress;
    }

    // `.dbtest zf test hardmode [0|1]`: heroic to arm; never while Gahz'rilla fights or is dead.
    constexpr bool GmHardModeAllowed(bool heroic, std::uint32_t gahzrillaSlot, std::uint32_t value)
    {
        if (gahzrillaSlot == DungeonKit::State::Done || gahzrillaSlot == DungeonKit::State::InProgress)
            return false;
        return value == 0 || heroic;
    }

    // The hard mode loot bit rides Gahz'rilla while the flag is lit and he is not dead (rule 1: never in JustDied).
    constexpr bool HardModeLootLit(std::uint32_t hardMode, std::uint32_t gahzrillaSlot)
    {
        return hardMode != 0 && gahzrillaSlot != DungeonKit::State::Done;
    }

    // A pool attempt is lost: Velratha's slot 0 or Gahz'rilla's slot 1 went from IN_PROGRESS back to NOT_STARTED or
    // FAIL.
    constexpr bool PoolWiped(std::uint32_t slot, std::uint32_t before, std::uint32_t now)
    {
        return (slot == BOSS_VELRATHA || slot == BOSS_GAHZRILLA) && before == DungeonKit::State::InProgress
            && (now == DungeonKit::State::NotStarted || now == DungeonKit::State::Fail);
    }

    // Section 7 #43 h A: Gahz'rilla's wipe after Velratha died brings her back (slot 0 reopened, her body respawned).
    constexpr bool PoolWipeReopensVelratha(std::uint32_t slot, std::uint32_t before, std::uint32_t now,
        std::uint32_t velrathaSlot)
    {
        return slot == BOSS_GAHZRILLA && PoolWiped(slot, before, now) && velrathaSlot == DungeonKit::State::Done;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (section 3.8; DB rows exact; [navmesh estimate] otherwise, z from the mesh)
    // ----------------------------------------------------------------------------------------------------------------
    struct Point3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        float o = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
    };

    Point3 constexpr kFinderStart{ 1213.52f, 841.59f, 8.93f, 6.09f };           // [DB] areatrigger 924's target
    Point3 constexpr kEntranceGoblin{ 1219.16f, 848.49f, 10.05f, 4.71f };       // [user] the quests WP's NPC
    // Section 7 #26 A: the boss row of mod-dungeon-checkpoint, used once Zum'rah is dead (the bowl's edge, facing the
    // stair foot): CP data/sql/db-world/u_dungeon_checkpoint_2026_11_25_00.sql.
    Point3 constexpr kCheckpoint{ 1874.8f, 1042.2f, 9.5f, 1.50f };

    // --- Theka's courtyard (D1) ---
    Point3 constexpr kThekaSpawn{ 1778.01f, 859.67f, 8.88f, 4.40f };            // [DB] guid 81463 (patrol stopped)
    // Section 7 #27 A: rise points 30 yd out, two per open sector (NW 50-80, NE 310-345); the heroic pair is one of
    // each.
    inline std::array<Point3, 4> constexpr kThekaRisePoints{ {
        { 1795.2f, 884.2f, 9.7f }, { 1785.8f, 888.6f, 9.1f }, { 1799.2f, 838.5f, 10.0f }, { 1806.2f, 849.4f, 9.4f },
    } };
    inline std::array<Point3, 2> constexpr kThekaRiseAlternates{ { { 1788.3f, 887.9f, 9.1f },
        { 1804.0f, 844.7f, 9.7f } } };
    Point3 constexpr kCourtyardDisc{ 1810.8f, 842.8f, 9.3f };                   // the best free disc, r 17.5

    // --- Antu'sul's den and chamber (D2) ---
    Point3 constexpr kAntusulSpawn{ 1815.85f, 670.39f, 15.02f, 2.02f };         // [DB] guid 81519
    Point3 constexpr kAntusulChamber{ 1806.0f, 730.0f, 15.2f };                 // the chamber's center (section 7 #28)
    Point3 constexpr kDenMouth{ 1812.0f, 710.0f, 15.3f };
    Point3 constexpr kAntusulTrigger{ 1811.05f, 700.98f, 15.29f };              // [DBC] area trigger 1447, sphere 30
    float constexpr kAntusulTriggerRadius = 30.f;
    inline std::array<Point3, 8> constexpr kServantRisePoints{ {
        { 1809.2f, 682.8f, 16.0f }, { 1817.8f, 691.2f, 14.2f }, { 1808.8f, 699.2f, 15.3f },     // the throat
        { 1827.8f, 709.2f, 16.7f }, { 1811.8f, 745.2f, 17.0f }, { 1799.8f, 747.2f, 16.2f },     // the chamber
        { 1789.8f, 740.2f, 16.8f }, { 1786.2f, 751.8f, 16.9f },
    } };

    // --- Zum'rah's bowl and tongue (D3) ---
    Point3 constexpr kZumrahSpawn{ 1912.17f, 1016.11f, 11.60f, 3.11f };         // [DB] guid 81524
    Point3 constexpr kCauldron{ 1909.48f, 1016.13f, 11.52f };                   // [DB] GO 141851
    Point3 constexpr kZumrahTrigger{ 1909.27f, 1015.11f, 11.52f };              // [DBC] area trigger 962, sphere 10
    inline std::array<Point3, 4> constexpr kBoundDeadSpots{ {
        { 1907.1f, 1016.8f, 11.6f }, { 1907.3f, 1014.9f, 11.5f }, { 1908.8f, 1013.7f, 11.6f },
        { 1910.7f, 1014.0f, 11.9f },
    } };
    Point3 constexpr kBoundDeadOverflow{ 1897.0f, 1014.0f, 11.7f };             // the neck mouth (section 7 #30 A)
    float constexpr kGraveReachYd = 60.f;                                       // section 7 #29 A

    // --- The Pyramid (D4a, D4b; CR's crew points) ---
    Point3 constexpr kExecutionerSpawn{ 1886.80f, 1289.89f, 45.96f, 3.39f };    // [DB] guid 81552
    Point3 constexpr kLanding{ 1885.8f, 1271.2f, 42.6f };                       // the landing's best disc, r 10
    float constexpr kLandingRadius = 10.f;
    float constexpr kLandingZMin = 39.f;
    float constexpr kLandingZMax = 46.f;
    // Section 3.2 item 3: the wipe region (any height).
    DungeonKit::Box2 constexpr kPyramidRegion{ 1826.f, 1945.f, 1130.f, 1335.f };
    // [DB] the five cages (GO 141070-141074, guids 27093, 27092, 27091, 27089, 27090)
    inline std::array<Point3, 5> constexpr kCages{ {
        { 1890.96f, 1294.47f, 48.15f }, { 1881.33f, 1297.46f, 48.33f }, { 1889.76f, 1297.68f, 48.17f },
        { 1886.88f, 1298.94f, 48.23f }, { 1883.33f, 1298.99f, 48.29f },
    } };
    // [DB] the crew's spawns (in the cages), by CrewMember
    inline std::array<Point3, kCrewCount> constexpr kCrewSpawns{ {
        { 1882.89f, 1299.27f, 48.38f, 4.83f }, { 1886.64f, 1299.11f, 48.31f, 4.36f },
        { 1889.62f, 1298.01f, 48.26f, 3.94f }, { 1881.05f, 1297.36f, 48.42f, 5.41f },
        { 1891.07f, 1294.78f, 48.23f, 3.32f },
    } };
    // Stock (go_troll_cage): the stair points the freed crew walk to (POINT_CREW_STAIRS), by CrewMember
    inline std::array<Point3, kCrewCount> constexpr kCrewStairPoints{ {
        { 1886.96f, 1263.49f, 41.54f, 4.78f }, { 1882.5f, 1263.0f, 41.52f, 4.78f },
        { 1886.47f, 1270.68f, 41.68f, 4.78f }, { 1890.0f, 1263.0f, 41.52f, 4.78f },
        { 1891.19f, 1272.03f, 41.60f, 4.78f },
    } };
    // Stock (instance_zulfarrak.cpp PYRAMID_PRE_WAVE_3): the stair foot (POINT_CREW_DESCENT), by CrewMember
    inline std::array<Point3, kCrewCount> constexpr kCrewDescentPoints{ {
        { 1887.92f, 1228.18f, 9.98f, 4.78f }, { 1883.68f, 1227.95f, 9.543f, 4.78f },
        { 1897.23f, 1228.34f, 9.43f, 4.78f }, { 1878.02f, 1227.65f, 9.485f, 4.78f },
        { 1891.57f, 1228.68f, 9.69f, 4.78f },
    } };
    // Stock gather points (POINT_CREW_GATHER) with section 7 #33 A: the four fighters 8 yd west (+y), Weegli stays; z
    // from the mesh. Bly's gossip happens here.
    inline std::array<Point3, kCrewCount> constexpr kCrewGatherPoints{ {
        { 1883.82f, 1208.83f, 9.41f, 1.32f }, { 1874.11f, 1214.17f, 9.91f, 1.32f },
        { 1894.50f, 1212.40f, 9.13f, 1.32f }, { 1877.52f, 1199.63f, 8.95f, 1.32f },
        { 1891.83f, 1209.45f, 9.29f, 1.32f },
    } };
    // Stock (zulfarrak.cpp, TBC Classic Anniversary 2.5.6.69795): Weegli's barrel spot at the End Door; his escape
    // path.
    Point3 constexpr kWeegliDoorSpot{ 1857.1129f, 1145.692f, 15.184351f, 3.85f };
    std::uint32_t constexpr kWeegliEscapePath = 815530;
    Point3 constexpr kEndDoor{ 1854.53f, 1142.89f, 16.08f, 0.67f };            // [DB] GO 146084 guid 27086

    // The Stair (section 3.8, 7 #31 A): the lane is the whole stair from y 1227 to y 1259; the landing starts at 1260.
    float constexpr kStairLaneYMin = 1227.f;
    float constexpr kStairLaneYMax = 1259.f;
    float constexpr kLandingYMin = 1260.f;
    Point3 constexpr kStairFoot{ 1888.0f, 1227.0f, 13.7f };
    Point3 constexpr kStairLip{ 1888.0f, 1260.0f, 40.0f };
    std::uint32_t constexpr kWavePath = 81553;                                  // stock PATH_ADDS: foot, then the lip

    // The wave tables (stock instance_zulfarrak.cpp pyramidSpawns, 23 + 24 + 5 trolls, then Sezz'ziz and Nekrum;
    // section 3.2 item 11): stock entries, z from the mesh (the 8 points under the ramp at 11.3 to 13.2). D4b maps
    // the Cretins, Acolytes and Zealots to its three specialists.
    struct WaveSpawn
    {
        std::uint8_t wave;
        std::uint32_t entry;
        Point3 at;
    };
    float constexpr kWaveFacing = 4.78f;
    float constexpr kAltarFacing = 1.32f;

    inline std::array<WaveSpawn, 54> constexpr kWaveSpawns{ {
        { 1, NPC_SANDFURY_CRETIN,  { 1894.64f, 1206.29f, 9.46f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1890.08f, 1218.68f, 10.17f, kWaveFacing } },
        { 1, NPC_SANDFURY_ACOLYTE, { 1883.76f, 1222.30f, 11.70f, kWaveFacing } },
        { 1, NPC_SANDFURY_CRETIN,  { 1874.18f, 1221.24f, 9.67f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1892.28f, 1225.49f, 12.76f, kWaveFacing } },
        { 1, NPC_SANDFURY_DRUDGE,  { 1889.94f, 1212.21f, 9.19f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1879.02f, 1223.06f, 12.17f, kWaveFacing } },
        { 1, NPC_SANDFURY_CRETIN,  { 1874.45f, 1204.44f, 9.76f, kWaveFacing } },
        { 1, NPC_SANDFURY_ACOLYTE, { 1898.23f, 1217.97f, 9.63f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1882.07f, 1225.70f, 13.16f, kWaveFacing } },
        { 1, NPC_SANDFURY_ZEALOT,  { 1896.46f, 1205.62f, 9.26f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1886.97f, 1225.86f, 13.10f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1894.72f, 1221.91f, 11.31f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1883.50f, 1218.25f, 10.05f, kWaveFacing } },
        { 1, NPC_SANDFURY_SLAVE,   { 1886.93f, 1221.40f, 11.25f, kWaveFacing } },
        { 1, NPC_SANDFURY_ACOLYTE, { 1889.82f, 1222.51f, 11.83f, kWaveFacing } },
        { 1, NPC_SANDFURY_DRUDGE,  { 1893.07f, 1215.26f, 9.03f, kWaveFacing } },
        { 1, NPC_SANDFURY_DRUDGE,  { 1878.57f, 1214.16f, 9.25f, kWaveFacing } },
        { 1, NPC_SANDFURY_DRUDGE,  { 1883.74f, 1212.35f, 9.27f, kWaveFacing } },
        { 1, NPC_SANDFURY_ZEALOT,  { 1877.00f, 1207.27f, 9.09f, kWaveFacing } },
        { 1, NPC_SANDFURY_ZEALOT,  { 1873.63f, 1204.65f, 9.88f, kWaveFacing } },
        { 1, NPC_SANDFURY_ACOLYTE, { 1877.40f, 1216.41f, 9.23f, kWaveFacing } },
        { 1, NPC_SANDFURY_ZEALOT,  { 1899.63f, 1202.52f, 8.93f, kWaveFacing } },
        { 2, NPC_SANDFURY_CRETIN,  { 1902.83f, 1223.41f, 9.21f, kWaveFacing } },
        { 2, NPC_SANDFURY_ACOLYTE, { 1889.82f, 1222.51f, 11.83f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1883.50f, 1218.25f, 10.05f, kWaveFacing } },
        { 2, NPC_SANDFURY_DRUDGE,  { 1883.74f, 1212.35f, 9.27f, kWaveFacing } },
        { 2, NPC_SANDFURY_ZEALOT,  { 1877.00f, 1207.27f, 9.09f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1890.08f, 1218.68f, 10.17f, kWaveFacing } },
        { 2, NPC_SANDFURY_CRETIN,  { 1894.64f, 1206.29f, 9.46f, kWaveFacing } },
        { 2, NPC_SANDFURY_ACOLYTE, { 1877.40f, 1216.41f, 9.23f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1892.28f, 1225.49f, 12.76f, kWaveFacing } },
        { 2, NPC_SANDFURY_DRUDGE,  { 1893.07f, 1215.26f, 9.03f, kWaveFacing } },
        { 2, NPC_SANDFURY_ZEALOT,  { 1896.46f, 1205.62f, 9.26f, kWaveFacing } },
        { 2, NPC_SANDFURY_CRETIN,  { 1874.45f, 1204.44f, 9.76f, kWaveFacing } },
        { 2, NPC_SANDFURY_CRETIN,  { 1874.18f, 1221.24f, 9.67f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1879.02f, 1223.06f, 12.17f, kWaveFacing } },
        { 2, NPC_SANDFURY_ACOLYTE, { 1898.23f, 1217.97f, 9.63f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1882.07f, 1225.70f, 13.16f, kWaveFacing } },
        { 2, NPC_SANDFURY_ZEALOT,  { 1873.63f, 1204.65f, 9.88f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1886.97f, 1225.86f, 13.10f, kWaveFacing } },
        { 2, NPC_SANDFURY_DRUDGE,  { 1878.57f, 1214.16f, 9.25f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1894.72f, 1221.91f, 11.31f, kWaveFacing } },
        { 2, NPC_SANDFURY_SLAVE,   { 1886.93f, 1221.40f, 11.25f, kWaveFacing } },
        { 2, NPC_SANDFURY_ACOLYTE, { 1883.76f, 1222.30f, 11.70f, kWaveFacing } },
        { 2, NPC_SANDFURY_DRUDGE,  { 1889.94f, 1212.21f, 9.19f, kWaveFacing } },
        { 2, NPC_SANDFURY_ZEALOT,  { 1899.63f, 1202.52f, 8.93f, kWaveFacing } },
        { 3, NPC_SANDFURY_DRUDGE,  { 1878.57f, 1214.16f, 9.25f, kWaveFacing } },
        { 3, NPC_SANDFURY_SLAVE,   { 1894.72f, 1221.91f, 11.31f, kWaveFacing } },
        { 3, NPC_SANDFURY_SLAVE,   { 1886.93f, 1221.40f, 11.25f, kWaveFacing } },
        { 3, NPC_SANDFURY_ACOLYTE, { 1883.76f, 1222.30f, 11.70f, kWaveFacing } },
        { 3, NPC_SANDFURY_DRUDGE,  { 1889.94f, 1212.21f, 9.19f, kWaveFacing } },
        { 3, NPC_SEZZZIZ,          { 1886.30f, 1199.65f, 9.49f, kAltarFacing } },
        { 3, NPC_NEKRUM,           { 1881.06f, 1199.70f, 9.15f, kAltarFacing } },
    } };

    // Sezz'ziz's add points (stock zulfarrak.cpp shadowpriestSezzizAdds, df82d1be9 jrad7's coordinates; PY14).
    inline std::array<Point3, 2> constexpr kSezzzizAddPoints{ { { 1874.12f, 1198.90f, 9.21f },
        { 1895.26f, 1199.09f, 9.39f } } };

    // --- The plaza (D4b's Altar, D5's crew fight) ---
    Point3 constexpr kPlazaCenter{ 1888.0f, 1210.0f, 9.3f };
    Point3 constexpr kPlazaDisc{ 1893.8f, 1163.8f, 9.0f };                     // r 22.6
    Point3 constexpr kPlazaDiscWest{ 1862.8f, 1189.2f, 9.0f };                 // r 14.6

    // --- Ukorz's mesa (D6) ---
    Point3 constexpr kUkorzSpawn{ 1727.48f, 1017.35f, 54.91f, 1.01f };          // [DB] guid 37996
    Point3 constexpr kRuuzluSpawn{ 1730.28f, 1015.17f, 54.91f, 0.90f };         // [DB] guid 37997
    Point3 constexpr kMesaDonutCenter{ 1736.2f, 1033.2f, 53.5f };              // section 7 #34 A, disc r 13.2
    inline std::array<Point3, 2> constexpr kMesaHoles{ { { 1741.6f, 1017.9f, 53.5f }, { 1721.9f, 1033.0f, 53.5f } } };
    Point3 constexpr kMesaRampHead{ 1760.2f, 1043.2f, 49.2f };

    // --- The pool (D7, D7Ha, D7Hb) ---
    Point3 constexpr kVelrathaSpawn{ 1698.24f, 1210.74f, 9.42f, 5.46f };        // [DB] guid 81570 (patrol stopped)
    Point3 constexpr kGong{ 1650.91f, 1171.88f, 10.90f };                       // [DB] GO 141832 guid 27140
    Point3 constexpr kGahzrillaSummon{ 1659.43f, 1180.50f, 1.05f, 0.f };        // [DB] the stock summon, 11.5 yd down
    Point3 constexpr kGahzrillaAshore{ 1677.0f, 1167.0f, 9.3f };               // section 7 #35 A, disc r 14.8
    inline std::array<Point3, 7> constexpr kShoreDiscs{ {
        { 1706.0f, 1235.0f, 9.5f }, { 1659.0f, 1216.0f, 9.5f }, { 1648.0f, 1206.0f, 9.5f }, { 1677.0f, 1167.0f, 9.3f },
        { 1687.0f, 1178.0f, 9.5f }, { 1643.0f, 1155.0f, 9.5f }, { 1627.0f, 1186.0f, 9.5f },
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas: the rooms' floors (WP-S0 cut, [navmesh estimate]); z bands from 2 yd under the floor to 8 yd over it (a
    // knocked up player stays inside). A boss WP that needs a tighter shape (an inset leash, a lane) cuts it in its own
    // Logic header.
    // ----------------------------------------------------------------------------------------------------------------
    // courtyard: 49 points, 5,488 sq yd (floor 5,205 within x 1735-1845, y 805-915), mesh z 9.1 to 15.0
    inline std::array<Vec2, 49> constexpr kCourtyardPolygon{ {
        { 1735.0f, 821.5f }, { 1748.0f, 827.5f }, { 1753.5f, 835.0f }, { 1756.0f, 834.0f }, { 1773.0f, 853.5f },
        { 1780.5f, 844.0f }, { 1811.0f, 819.5f }, { 1806.5f, 814.0f }, { 1793.0f, 823.5f }, { 1807.5f, 811.5f },
        { 1805.0f, 809.0f }, { 1809.0f, 805.0f }, { 1812.0f, 805.0f }, { 1812.0f, 810.0f }, { 1820.5f, 812.5f },
        { 1824.5f, 807.5f }, { 1845.0f, 831.5f }, { 1845.0f, 862.5f }, { 1842.0f, 862.0f }, { 1842.0f, 832.5f },
        { 1827.0f, 817.0f }, { 1821.0f, 819.0f }, { 1824.5f, 826.5f }, { 1833.0f, 832.5f }, { 1834.0f, 840.5f },
        { 1832.0f, 846.0f }, { 1834.5f, 849.5f }, { 1834.5f, 887.0f }, { 1827.5f, 898.5f }, { 1819.5f, 898.5f },
        { 1820.0f, 904.0f }, { 1829.0f, 915.0f }, { 1819.0f, 915.0f }, { 1812.0f, 905.5f }, { 1803.0f, 915.0f },
        { 1788.5f, 915.0f }, { 1787.5f, 906.5f }, { 1783.5f, 905.0f }, { 1778.0f, 892.5f }, { 1779.5f, 887.0f },
        { 1775.0f, 885.5f }, { 1770.5f, 874.5f }, { 1772.0f, 869.5f }, { 1768.0f, 869.0f }, { 1766.0f, 859.5f },
        { 1747.5f, 843.0f }, { 1748.5f, 840.0f }, { 1743.5f, 835.0f }, { 1735.0f, 833.0f },
    } };
    float constexpr kCourtyardZMin = 7.f;
    float constexpr kCourtyardZMax = 23.f;
    // the den: throat, chamber, tail (x 1775-1845, y 655-752): 65 points, 2,662 sq yd (floor 2,560), z 13.5 to 20.0
    inline std::array<Vec2, 65> constexpr kDenPolygon{ {
        { 1775.0f, 720.0f }, { 1778.5f, 719.0f }, { 1791.0f, 724.5f }, { 1792.5f, 723.5f }, { 1796.5f, 709.0f },
        { 1798.0f, 708.0f }, { 1797.5f, 701.0f }, { 1799.0f, 697.0f }, { 1800.5f, 700.0f }, { 1803.5f, 696.5f },
        { 1806.5f, 699.5f }, { 1809.5f, 697.0f }, { 1807.0f, 694.0f }, { 1807.0f, 687.0f }, { 1809.0f, 684.0f },
        { 1804.5f, 679.0f }, { 1806.5f, 677.0f }, { 1806.0f, 672.5f }, { 1803.5f, 671.0f }, { 1805.0f, 664.5f },
        { 1806.5f, 666.0f }, { 1809.0f, 666.0f }, { 1810.0f, 664.0f }, { 1812.5f, 665.0f }, { 1810.0f, 667.0f },
        { 1812.0f, 669.5f }, { 1816.5f, 669.0f }, { 1818.0f, 666.5f }, { 1821.5f, 666.5f }, { 1824.0f, 670.5f },
        { 1823.5f, 677.5f }, { 1819.0f, 681.5f }, { 1819.0f, 685.0f }, { 1816.5f, 681.5f }, { 1814.0f, 682.5f },
        { 1817.0f, 685.5f }, { 1816.0f, 689.0f }, { 1818.5f, 690.5f }, { 1816.5f, 694.5f }, { 1817.5f, 700.0f },
        { 1815.0f, 706.0f }, { 1818.0f, 710.0f }, { 1822.5f, 710.0f }, { 1824.0f, 707.5f }, { 1827.5f, 708.5f },
        { 1829.5f, 706.5f }, { 1828.0f, 702.0f }, { 1832.5f, 699.5f }, { 1832.5f, 707.5f }, { 1836.5f, 722.0f },
        { 1845.0f, 723.5f }, { 1845.0f, 726.5f }, { 1836.5f, 727.0f }, { 1824.0f, 732.0f }, { 1822.0f, 734.0f },
        { 1819.5f, 745.0f }, { 1814.5f, 750.5f }, { 1813.0f, 749.5f }, { 1811.5f, 751.0f }, { 1802.0f, 752.0f },
        { 1775.0f, 752.0f }, { 1775.0f, 743.0f }, { 1777.5f, 741.0f }, { 1776.5f, 739.5f }, { 1775.0f, 740.5f },
    } };
    float constexpr kDenZMin = 11.5f;
    float constexpr kDenZMax = 28.f;
    // the bowl and the tongue (x 1815-1920, y 950-1065): 64 points, 4,154 sq yd (floor 4,085), z 9.1 to 12.6
    inline std::array<Vec2, 64> constexpr kBowlPolygon{ {
        { 1829.5f, 1031.5f }, { 1832.0f, 1026.0f }, { 1845.5f, 1017.5f }, { 1848.0f, 1019.5f }, { 1853.5f, 1017.5f },
        { 1855.5f, 1011.5f }, { 1855.0f, 1015.5f }, { 1859.0f, 1017.0f }, { 1861.0f, 1012.5f }, { 1857.5f, 1010.5f },
        { 1873.5f, 1001.0f }, { 1866.0f, 992.5f }, { 1858.5f, 977.0f }, { 1840.0f, 950.0f }, { 1849.5f, 950.0f },
        { 1855.5f, 956.0f }, { 1866.5f, 977.5f }, { 1872.5f, 974.5f }, { 1874.0f, 971.0f }, { 1882.0f, 970.5f },
        { 1884.0f, 965.5f }, { 1891.0f, 963.5f }, { 1909.0f, 996.5f }, { 1900.0f, 997.5f }, { 1902.0f, 993.5f },
        { 1898.5f, 992.5f }, { 1896.5f, 997.5f }, { 1893.0f, 999.0f }, { 1893.0f, 1004.0f }, { 1899.0f, 1005.0f },
        { 1899.0f, 1011.5f }, { 1906.5f, 1011.5f }, { 1907.5f, 1008.0f }, { 1914.0f, 1008.0f }, { 1913.0f, 1022.5f },
        { 1911.0f, 1022.5f }, { 1909.5f, 1018.5f }, { 1898.5f, 1018.5f }, { 1897.5f, 1026.5f }, { 1893.5f, 1027.5f },
        { 1892.5f, 1036.5f }, { 1896.0f, 1037.5f }, { 1897.0f, 1034.0f }, { 1902.0f, 1034.5f }, { 1890.5f, 1041.5f },
        { 1886.0f, 1040.5f }, { 1883.0f, 1046.0f }, { 1876.0f, 1050.5f }, { 1870.5f, 1050.0f }, { 1869.0f, 1054.5f },
        { 1865.5f, 1053.5f }, { 1860.5f, 1057.0f }, { 1858.5f, 1060.5f }, { 1860.5f, 1065.0f }, { 1848.5f, 1065.0f },
        { 1847.0f, 1061.0f }, { 1849.0f, 1059.0f }, { 1846.5f, 1055.0f }, { 1849.5f, 1053.0f }, { 1843.5f, 1051.5f },
        { 1841.5f, 1053.5f }, { 1835.5f, 1043.0f }, { 1840.5f, 1039.0f }, { 1831.5f, 1037.0f },
    } };
    float constexpr kBowlZMin = 7.f;
    float constexpr kBowlZMax = 20.5f;
    // the Pyramid top and the landing (from z 39): 27 points, 3,360 sq yd (floor 2,937), z 39.0 to 48.5
    inline std::array<Vec2, 27> constexpr kPyramidTopPolygon{ {
        { 1857.0f, 1295.0f }, { 1857.5f, 1291.5f }, { 1861.0f, 1290.5f }, { 1859.5f, 1274.5f }, { 1864.5f, 1270.0f },
        { 1875.5f, 1269.0f }, { 1874.0f, 1257.5f }, { 1879.5f, 1256.5f }, { 1880.5f, 1260.0f }, { 1893.5f, 1260.0f },
        { 1895.5f, 1255.0f }, { 1902.0f, 1256.0f }, { 1898.0f, 1270.0f }, { 1915.0f, 1270.5f }, { 1913.5f, 1285.5f },
        { 1915.0f, 1303.0f }, { 1911.5f, 1304.5f }, { 1911.0f, 1313.0f }, { 1913.0f, 1315.5f }, { 1913.0f, 1325.0f },
        { 1891.5f, 1325.0f }, { 1890.0f, 1331.5f }, { 1880.5f, 1331.5f }, { 1879.5f, 1325.0f }, { 1857.5f, 1324.5f },
        { 1859.0f, 1304.0f }, { 1857.0f, 1302.5f },
    } };
    float constexpr kTopZMin = 37.f;
    float constexpr kTopZMax = 56.5f;
    // The Stair from the foot (y 1226) to 1 yd past the lip (y 1261), the main run's width per 3 yd (section 3.8;
    // the side ledges 3 to 4 yd higher are not on it).
    inline std::array<Vec2, 12> constexpr kStairPolygon{ {
        { 1874.5f, 1226.0f }, { 1875.5f, 1235.0f }, { 1877.5f, 1241.0f }, { 1879.0f, 1247.0f }, { 1880.0f, 1253.0f },
        { 1881.5f, 1261.0f }, { 1893.5f, 1261.0f }, { 1895.5f, 1253.0f }, { 1896.5f, 1247.0f }, { 1898.5f, 1241.0f },
        { 1900.5f, 1235.0f }, { 1902.5f, 1226.0f },
    } };
    float constexpr kStairZMin = 11.f;
    float constexpr kStairZMax = 46.f;
    // the plaza, z 7.5 to 11 (x 1800-1980, y 1100-1260): 62 points, 7,574 sq yd (floor 7,103), z 8.9 to 11.0
    inline std::array<Vec2, 62> constexpr kPlazaPolygon{ {
        { 1800.0f, 1145.0f }, { 1803.5f, 1151.5f }, { 1806.5f, 1150.5f }, { 1820.0f, 1163.5f }, { 1822.5f, 1169.0f },
        { 1827.5f, 1170.5f }, { 1825.0f, 1175.5f }, { 1831.0f, 1181.0f }, { 1839.0f, 1171.5f }, { 1852.0f, 1173.0f },
        { 1857.5f, 1176.0f }, { 1870.5f, 1165.5f }, { 1878.0f, 1130.5f }, { 1901.0f, 1119.5f }, { 1914.0f, 1120.5f },
        { 1912.0f, 1123.5f }, { 1914.0f, 1126.0f }, { 1916.5f, 1121.0f }, { 1919.5f, 1126.0f }, { 1929.5f, 1130.5f },
        { 1923.0f, 1135.5f }, { 1920.5f, 1145.0f }, { 1915.0f, 1152.0f }, { 1915.0f, 1157.0f }, { 1920.0f, 1163.5f },
        { 1920.5f, 1172.0f }, { 1935.5f, 1182.5f }, { 1943.0f, 1192.0f }, { 1948.0f, 1192.5f }, { 1948.0f, 1197.0f },
        { 1944.0f, 1197.5f }, { 1942.0f, 1201.0f }, { 1929.0f, 1208.0f }, { 1931.0f, 1211.5f }, { 1922.0f, 1218.0f },
        { 1920.0f, 1233.5f }, { 1912.0f, 1243.0f }, { 1906.0f, 1243.0f }, { 1909.5f, 1232.0f }, { 1901.5f, 1230.0f },
        { 1898.0f, 1221.0f }, { 1890.0f, 1220.5f }, { 1878.0f, 1220.5f }, { 1875.0f, 1229.5f }, { 1866.5f, 1231.0f },
        { 1869.5f, 1242.0f }, { 1865.5f, 1242.0f }, { 1864.5f, 1227.0f }, { 1869.5f, 1217.0f }, { 1869.0f, 1206.0f },
        { 1851.0f, 1200.5f }, { 1834.5f, 1200.0f }, { 1831.5f, 1196.5f }, { 1819.5f, 1194.0f }, { 1818.5f, 1192.5f },
        { 1822.5f, 1192.0f }, { 1827.0f, 1186.5f }, { 1820.5f, 1180.0f }, { 1816.0f, 1183.0f }, { 1812.5f, 1175.5f },
        { 1808.0f, 1175.5f }, { 1800.0f, 1168.0f },
    } };
    float constexpr kPlazaZMin = 6.5f;
    float constexpr kPlazaZMax = 19.f;
    // Ukorz's mesa, z 49 to 58: 45 points, 4,442 sq yd (floor 4,052), z 49.0 to 58.0
    inline std::array<Vec2, 45> constexpr kMesaPolygon{ {
        { 1693.0f, 1030.5f }, { 1710.5f, 1034.5f }, { 1713.0f, 1030.5f }, { 1711.5f, 1025.5f }, { 1695.5f, 1022.5f },
        { 1700.0f, 1018.5f }, { 1700.0f, 1014.0f }, { 1731.0f, 988.5f }, { 1739.5f, 988.0f }, { 1737.5f, 1004.0f },
        { 1730.5f, 999.0f }, { 1725.0f, 1007.0f }, { 1708.0f, 1017.5f }, { 1712.5f, 1025.5f }, { 1737.0f, 1006.5f },
        { 1745.0f, 1008.5f }, { 1747.5f, 988.5f }, { 1755.0f, 988.5f }, { 1763.0f, 999.0f }, { 1759.0f, 1005.0f },
        { 1761.0f, 1007.0f }, { 1768.0f, 1006.0f }, { 1775.0f, 1015.0f }, { 1771.0f, 1020.0f }, { 1772.0f, 1022.5f },
        { 1776.5f, 1024.0f }, { 1779.0f, 1021.0f }, { 1783.5f, 1027.0f }, { 1780.5f, 1043.0f }, { 1772.5f, 1050.0f },
        { 1767.5f, 1049.5f }, { 1762.5f, 1056.0f }, { 1751.5f, 1048.5f }, { 1753.0f, 1068.5f }, { 1743.5f, 1078.0f },
        { 1736.5f, 1076.5f }, { 1730.5f, 1079.5f }, { 1720.5f, 1067.5f }, { 1724.0f, 1062.5f }, { 1721.5f, 1060.0f },
        { 1717.0f, 1062.5f }, { 1708.0f, 1051.5f }, { 1712.0f, 1046.5f }, { 1709.0f, 1044.5f }, { 1704.0f, 1046.5f },
    } };
    float constexpr kMesaZMin = 47.f;
    float constexpr kMesaZMax = 66.f;
    // the shore, its pool filled in (x 1615-1730, y 1125-1250): 80 points, 11,230 sq yd (floor 10,401), z 8.9 to 14.0
    inline std::array<Vec2, 80> constexpr kShorePolygon{ {
        { 1615.0f, 1125.5f }, { 1631.5f, 1125.0f }, { 1639.0f, 1138.5f }, { 1646.0f, 1133.5f }, { 1645.0f, 1131.0f },
        { 1641.0f, 1132.5f }, { 1643.5f, 1128.5f }, { 1639.5f, 1128.5f }, { 1639.0f, 1125.0f }, { 1657.5f, 1125.0f },
        { 1672.5f, 1136.5f }, { 1678.0f, 1136.5f }, { 1676.5f, 1140.5f }, { 1682.0f, 1146.0f }, { 1691.0f, 1138.0f },
        { 1687.0f, 1136.0f }, { 1682.5f, 1140.0f }, { 1678.5f, 1136.0f }, { 1694.5f, 1125.0f }, { 1708.0f, 1126.5f },
        { 1720.0f, 1134.0f }, { 1706.5f, 1145.0f }, { 1707.0f, 1134.5f }, { 1701.0f, 1130.5f }, { 1696.0f, 1133.0f },
        { 1696.0f, 1136.5f }, { 1689.5f, 1142.0f }, { 1690.0f, 1146.5f }, { 1695.0f, 1148.5f }, { 1699.0f, 1145.0f },
        { 1702.0f, 1149.0f }, { 1697.0f, 1147.0f }, { 1690.5f, 1153.0f }, { 1694.0f, 1158.0f }, { 1692.5f, 1166.0f },
        { 1697.0f, 1165.5f }, { 1722.5f, 1140.5f }, { 1730.0f, 1140.0f }, { 1730.0f, 1148.5f }, { 1726.0f, 1149.0f },
        { 1711.0f, 1166.0f }, { 1704.0f, 1167.5f }, { 1700.5f, 1173.5f }, { 1701.5f, 1177.0f }, { 1709.5f, 1175.0f },
        { 1714.0f, 1178.5f }, { 1721.5f, 1171.5f }, { 1717.5f, 1168.5f }, { 1726.0f, 1160.5f }, { 1730.0f, 1160.5f },
        { 1729.5f, 1163.5f }, { 1722.5f, 1165.0f }, { 1727.0f, 1169.5f }, { 1722.0f, 1175.5f }, { 1725.5f, 1180.5f },
        { 1730.0f, 1178.5f }, { 1730.0f, 1185.5f }, { 1726.0f, 1181.0f }, { 1719.5f, 1187.0f }, { 1722.0f, 1191.0f },
        { 1716.0f, 1195.0f }, { 1716.0f, 1205.5f }, { 1730.0f, 1210.5f }, { 1730.0f, 1250.0f }, { 1652.5f, 1250.0f },
        { 1647.5f, 1233.5f }, { 1642.5f, 1231.5f }, { 1637.0f, 1219.5f }, { 1629.5f, 1216.0f }, { 1629.0f, 1209.5f },
        { 1620.0f, 1207.5f }, { 1617.0f, 1213.5f }, { 1615.0f, 1175.0f }, { 1618.0f, 1171.5f }, { 1615.0f, 1164.0f },
        { 1615.0f, 1147.5f }, { 1623.5f, 1151.0f }, { 1624.5f, 1158.0f }, { 1629.5f, 1147.0f }, { 1615.0f, 1140.5f },
    } };
    float constexpr kShoreZMin = 6.5f;
    float constexpr kShoreZMax = 22.f;
    // the sacred pool's water surface (mesh area 8): 23 points, 803 sq yd (floor 796), z 8.4 to 10.8
    inline std::array<Vec2, 23> constexpr kPoolWaterPolygon{ {
        { 1642.5f, 1179.5f }, { 1650.5f, 1170.5f }, { 1655.5f, 1167.5f }, { 1658.0f, 1170.5f }, { 1659.5f, 1170.0f },
        { 1672.0f, 1184.0f }, { 1673.5f, 1183.5f }, { 1679.0f, 1189.0f }, { 1679.5f, 1191.5f }, { 1681.0f, 1191.0f },
        { 1685.0f, 1194.5f }, { 1687.5f, 1199.0f }, { 1689.0f, 1198.5f }, { 1692.0f, 1201.5f }, { 1680.0f, 1213.5f },
        { 1671.5f, 1204.5f }, { 1672.0f, 1203.0f }, { 1669.5f, 1202.5f }, { 1660.5f, 1194.0f }, { 1655.5f, 1186.5f },
        { 1653.5f, 1187.0f }, { 1647.5f, 1179.5f }, { 1645.0f, 1181.0f },
    } };
    float constexpr kWaterZMin = -5.f;          // the bed at -2.9, 11.3 yd under the surface (section 3.8)
    float constexpr kWaterZMax = 12.f;

    template <std::size_t N>
    inline ArenaRegion PolygonRegion(std::array<Vec2, N> const& polygon, float zMin, float zMax)
    {
        return ArenaRegion::Polygon(std::vector<Vec2>(polygon.begin(), polygon.end()), zMin, zMax);
    }

    inline Arena CourtyardArena() { return Arena(PolygonRegion(kCourtyardPolygon, kCourtyardZMin, kCourtyardZMax)); }
    inline Arena DenArena() { return Arena(PolygonRegion(kDenPolygon, kDenZMin, kDenZMax)); }
    inline Arena BowlArena() { return Arena(PolygonRegion(kBowlPolygon, kBowlZMin, kBowlZMax)); }
    inline Arena PyramidTopArena() { return Arena(PolygonRegion(kPyramidTopPolygon, kTopZMin, kTopZMax)); }
    inline Arena StairArena() { return Arena(PolygonRegion(kStairPolygon, kStairZMin, kStairZMax)); }
    inline Arena PlazaArena() { return Arena(PolygonRegion(kPlazaPolygon, kPlazaZMin, kPlazaZMax)); }
    inline Arena MesaArena() { return Arena(PolygonRegion(kMesaPolygon, kMesaZMin, kMesaZMax)); }
    inline Arena PoolWater() { return Arena(PolygonRegion(kPoolWaterPolygon, kWaterZMin, kWaterZMax)); }
    // The shore and the water under it (a swimmer is on the pool's arena).
    inline Arena PoolArena()
    {
        Arena arena(PolygonRegion(kShorePolygon, kShoreZMin, kShoreZMax));
        arena.Add(PolygonRegion(kPoolWaterPolygon, kWaterZMin, kWaterZMax));
        return arena;
    }
    // The landing (stage 2's restart spot, the Stair's hold).
    inline Arena LandingArena()
    {
        return Arena(ArenaRegion::Circle(kLanding.XY(), kLandingRadius, kLandingZMin, kLandingZMax));
    }

    constexpr bool InPyramidRegion(Vec2 p)
    {
        return p.x >= kPyramidRegion.minX && p.x <= kPyramidRegion.maxX && p.y >= kPyramidRegion.minY
            && p.y <= kPyramidRegion.maxY;
    }

    // The leash arena of a slot (the Pyramid: the top, where stage 1 fights; the crew: the plaza; the hard mode: the
    // pool). Empty for an unknown slot.
    inline Arena ArenaFor(std::uint32_t slot)
    {
        switch (slot)
        {
            case BOSS_VELRATHA:
            case BOSS_GAHZRILLA:
            case BOSS_CREW_AT_THE_POOL:
                return PoolArena();
            case BOSS_ANTUSUL:
                return DenArena();
            case BOSS_THEKA:
                return CourtyardArena();
            case BOSS_ZUMRAH:
                return BowlArena();
            case BOSS_PYRAMID:
                return PyramidTopArena();
            case BOSS_CREW:
                return PlazaArena();
            case BOSS_UKORZ:
                return MesaArena();
            default:
                return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Health (section 3.6, section 7 #1 A: normal x1.6, heroic x4/3; hard mode 200,000 / 500,000). Normal = the
    // engine's ceil(base x HealthModifier) of the DT rows (S0 stubs, the boss WPs own them now); heroic = WP-H's
    // overrides. A boss WP reads these and never restates one.
    // ----------------------------------------------------------------------------------------------------------------
    struct ReferenceRow
    {
        std::uint32_t nonTank;
        std::uint32_t tank;
    };
    // BM conf ReferenceHealth.MapLevels "209:46 209h:60" (section 7 #4 A). Host arithmetic only.
    ReferenceRow constexpr kReferenceNormal{ 2655, 2717 };
    ReferenceRow constexpr kReferenceHeroic{ 4120, 4110 };

    namespace Health
    {
        NH<std::uint32_t> constexpr kTheka{ 175973, 373260 };           // 91.7 on 1,919 / 122.3 on 3,052
        NH<std::uint32_t> constexpr kAntusul{ 159947, 266666 };         // 104.2 on 1,535 / 109.2 on 2,442
        NH<std::uint32_t> constexpr kZumrah{ 176065, 293284 };          // 114.7 on 1,535 / 120.1 on 2,442
        NH<std::uint32_t> constexpr kExecutioner{ 136058, 226764 };     // 70.9 on 1,919 / 74.3 on 3,052
        NH<std::uint32_t> constexpr kSezzziz{ 95938, 159951 };          // 62.5 on 1,535 / 65.5 on 2,442
        NH<std::uint32_t> constexpr kNekrum{ 48048, 79962 };            // 26.0 on 1,848 / 26.2 on 3,052
        NH<std::uint32_t> constexpr kBly{ 63941, 113229 };              // 34.6 on 1,848 / 37.1 on 3,052
        NH<std::uint32_t> constexpr kRaven{ 39917, 73248 };             // 22.4 on 1,782 / 24.0 on 3,052
        NH<std::uint32_t> constexpr kOro{ 40029, 73265 };               // 32.1 on 1,247 / 34.3 on 2,136
        NH<std::uint32_t> constexpr kMurta{ 40071, 73260 };             // 28.1 on 1,426 / 30.0 on 2,442
        NH<std::uint32_t> constexpr kUkorz{ 143925, 266745 };           // 75.0 on 1,919 / 87.4 on 3,052
        NH<std::uint32_t> constexpr kRuuzlu{ 128067, 233478 };          // 69.3 on 1,848 / 76.5 on 3,052
        NH<std::uint32_t> constexpr kVelratha{ 112007, 199930 };        // 83.4 on 1,343 / 93.6 on 2,136
        NH<std::uint32_t> constexpr kGahzrilla{ 208020, 386688 };       // 108.4 on 1,919 / 126.7 on 3,052
        std::uint32_t constexpr kHardModeVelratha = 200000;             // section 7 #1 A (SP 180,000 raised)
        std::uint32_t constexpr kHardModeGahzrilla = 500000;            // section 3.7's enrage arithmetic
        std::uint32_t constexpr kWeegliPoolAlly = 55000;                // the crew as pool allies: heroic boss health
    }

    // Section 3.5 rule 32: no hit under a 1.5 s warning on normal (SYS 4).
    std::uint32_t constexpr kWarningFloorMs = 1500;

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string (section 3.2 item 2): header "ZFR" (the stock "Z F" is its prefix, never the other way:
    // a stock "Z F <phase> ..." save fails at "R" and goes to the stock reader), the 9 boss states, then the extras.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "ZFR";
    char constexpr kStockSaveHeader[] = "ZF";

    enum SaveExtra : std::size_t
    {
        EXTRA_PYRAMID_STAGE = 0,    // PyramidStage (never running: a reload waits to replay it)
        EXTRA_CAGES_OPEN    = 1,
        EXTRA_CREW_ALIVE    = 2,    // the snapshot's while a stage runs (its losses are not permanent yet)
        EXTRA_OFFERINGS     = 3,    // idem
        EXTRA_BLOOD_PRICE   = 4,    // idem
        EXTRA_CREW_AT_END   = 5,    // the Test's key mask
        EXTRA_CREW_PATH     = 6,    // only with slot 6 DONE (a chosen, unfought path is offered again)
        EXTRA_END_DOOR      = 7,    // 0 or 3
        EXTRA_HARD_MODE     = 8,
        EXTRA_CREW_AT_POOL  = 9,    // CR said the crew arrived at the pool (0 / 1)
    };
    std::size_t constexpr kSaveExtraCount = 10;

    using BossStates = std::array<std::uint32_t, kBossCount>;

    struct ZfrSave
    {
        BossStates states{};
        std::uint32_t pyramidStage = PYRAMID_STAGE_NONE;
        std::uint32_t cagesOpen = 0;
        std::uint32_t crewAlive = kCrewAll;
        std::uint32_t offerings = 0;
        std::uint32_t bloodPrice = 0;
        std::uint32_t crewAtEnd = 0;
        std::uint32_t crewPath = CREW_PATH_OPEN;
        std::uint32_t endDoor = DungeonKit::State::NotStarted;
        std::uint32_t hardMode = 0;
        std::uint32_t crewAtPool = 0;
    };

    inline std::string FormatZfrSave(ZfrSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_PYRAMID_STAGE] = s.pyramidStage;
        extras[EXTRA_CAGES_OPEN] = s.cagesOpen;
        extras[EXTRA_CREW_ALIVE] = s.crewAlive;
        extras[EXTRA_OFFERINGS] = s.offerings;
        extras[EXTRA_BLOOD_PRICE] = s.bloodPrice;
        extras[EXTRA_CREW_AT_END] = s.crewAtEnd;
        extras[EXTRA_CREW_PATH] = s.crewPath;
        extras[EXTRA_END_DOOR] = s.endDoor;
        extras[EXTRA_HARD_MODE] = s.hardMode;
        extras[EXTRA_CREW_AT_POOL] = s.crewAtPool;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The states a completed-encounter mask records (DONE): bits 0 to 7 are slots 0 to 7.
    inline void ApplyEncounterMask(std::uint32_t mask, BossStates& states)
    {
        for (std::uint32_t bit = 0; bit < kEncounterBossCount; ++bit)
            if (mask & (1u << bit))
                states[bit] = DungeonKit::State::Done;
    }

    // One consistent run (states already through SanitizeLoadedState): the Pyramid's stage agrees with slot 5, the
    // crew's data with slot 6, the hard mode kill with slot 1; masks, flags and counts back in range.
    inline void SanitizeZfrSave(ZfrSave& s)
    {
        if (s.states[BOSS_PYRAMID] == DungeonKit::State::Done || s.states[BOSS_CREW] == DungeonKit::State::Done)
        {
            s.states[BOSS_PYRAMID] = DungeonKit::State::Done;
            s.pyramidStage = PYRAMID_STAGE_DONE;
        }
        else if (s.pyramidStage > PYRAMID_STAGE_ALTAR)
            s.pyramidStage = PYRAMID_STAGE_ALTAR;
        s.cagesOpen = (s.pyramidStage == PYRAMID_STAGE_ALTAR || s.pyramidStage == PYRAMID_STAGE_DONE
            || (s.pyramidStage == PYRAMID_STAGE_STAIR && s.cagesOpen)) ? 1 : 0;
        s.crewAlive = (s.crewAlive & kCrewAll) | kCrewWeegliBit;
        s.offerings = std::min(s.offerings, kOfferingsCap);
        s.crewAtEnd = s.pyramidStage == PYRAMID_STAGE_DONE ? (s.crewAtEnd & kCrewAll) : 0;
        bool const crewDone = s.states[BOSS_CREW] == DungeonKit::State::Done;
        s.crewPath = (crewDone && (s.crewPath == CREW_PATH_BETRAYAL || s.crewPath == CREW_PATH_TEST)) ? s.crewPath
            : crewDone ? CREW_PATH_BETRAYAL : CREW_PATH_OPEN;
        s.endDoor = crewDone ? DungeonKit::State::Done : DungeonKit::SanitizeLoadedState(s.endDoor);
        s.endDoor = SanitizeDoorState(s.endDoor);
        s.hardMode = s.hardMode ? 1 : 0;
        s.crewAtPool = (crewDone && s.crewPath == CREW_PATH_TEST && s.crewAtPool) ? 1 : 0;
        if (s.states[BOSS_GAHZRILLA] != DungeonKit::State::Done || !s.hardMode)
            s.states[BOSS_CREW_AT_THE_POOL] = DungeonKit::State::NotStarted;
    }

    // The stock save (instance_zulfarrak.cpp at c9315e3ec: SetHeaders("ZF"), no boss states, then "<pyramid phase>
    // <gahz'rilla> [<end door>]"; a missing door field derives from the phase). False on anything else.
    inline bool ReadStockSave(std::string const& in, std::uint32_t encounterMask, ZfrSave& out)
    {
        std::vector<std::uint32_t> fields;
        if (!DungeonKit::ReadSaveFields(in, kStockSaveHeader, 2, 3, fields))
            return false;
        out = ZfrSave{};
        ApplyEncounterMask(encounterMask, out.states);
        std::uint32_t const phase = fields[0];
        if (phase >= 8)
            out.states[BOSS_PYRAMID] = DungeonKit::State::Done;    // KILLED_ALL_TROLLS and on: the Pyramid was won
        else if (phase >= 1)
        {
            out.pyramidStage = PYRAMID_STAGE_STAIR;             // the cages were open: replay the Stair
            out.cagesOpen = 1;
        }
        if (phase >= 12)
            out.states[BOSS_CREW] = DungeonKit::State::Done;    // Bly died: the betrayal
        if (fields[1] == 3 || fields[1] == 4)
            out.states[BOSS_GAHZRILLA] = DungeonKit::State::Done;
        std::uint32_t const door = fields.size() > 2 ? fields[2]
            : (phase >= 11 ? std::uint32_t(DungeonKit::State::Done) : std::uint32_t(DungeonKit::State::NotStarted));
        out.endDoor = SanitizeDoorState(door);
        out.crewAtEnd = 0;                                      // the stock run knew no Test: the key stays closed
        return true;
    }

    // Reads this script's "Z F R" string or the stock "Z F" one; `encounterMask` is the instance's completed-encounter
    // mask (Map::CreateInstanceData sets it before Load), applied to a stock save only. False on anything else
    // (ignored).
    inline bool ParseZfrSave(std::string const& in, ZfrSave& out, std::uint32_t encounterMask = 0)
    {
        out = ZfrSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        ZfrSave stockSave;
        DungeonKit::LegacySaveReader const legacy = [&](std::string const& s, DungeonKit::StateSave& o)
        {
            if (!ReadStockSave(s, encounterMask, stockSave))
                return false;
            o.states.assign(stockSave.states.begin(), stockSave.states.end());
            stock = true;
            return true;
        };
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw, legacy))
            return false;
        if (stock)
            out = stockSave;
        else
        {
            out.pyramidStage = raw.extras[EXTRA_PYRAMID_STAGE];
            out.cagesOpen = raw.extras[EXTRA_CAGES_OPEN];
            out.crewAlive = raw.extras[EXTRA_CREW_ALIVE];
            out.offerings = raw.extras[EXTRA_OFFERINGS];
            out.bloodPrice = raw.extras[EXTRA_BLOOD_PRICE];
            out.crewAtEnd = raw.extras[EXTRA_CREW_AT_END];
            out.crewPath = raw.extras[EXTRA_CREW_PATH];
            out.endDoor = raw.extras[EXTRA_END_DOOR];
            out.hardMode = raw.extras[EXTRA_HARD_MODE];
            out.crewAtPool = raw.extras[EXTRA_CREW_AT_POOL];
        }
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        SanitizeZfrSave(out);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Section 3.5 rule 27: every boss calls NoAssist (ZulFarrakKit.h) each UpdateAI, before UpdateVictim. The files of
    // the boss WPs (host-tested: each `struct boss_...` in them has a NoAssist(me) call; the crew are exempt).
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<char const*, 7> constexpr kBossFiles{ {
        "boss_theka_rework.cpp", "boss_antusul_rework.cpp", "boss_zumrah_rework.cpp",
        "boss_sandfury_executioner_rework.cpp", "boss_sezzziz_rework.cpp", "boss_ukorz_rework.cpp",
        "boss_gahzrilla_rework.cpp",
    } };

    // A slot's state, TO_BE_DECIDED read as NOT_STARTED (before the first Update settles it).
    constexpr std::uint32_t SettledSlotState(std::uint32_t state)
    {
        return state == DungeonKit::State::ToBeDecided ? DungeonKit::State::NotStarted : state;
    }
}

#endif
