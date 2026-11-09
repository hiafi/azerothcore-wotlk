/*
 * mod-dungeon-bosses, Shadowfang Keep (map 33): the shared ids, boss states, data fields, texts, measured points and
 * arenas of the Shadowfang Keep build (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md sections
 * 3.1, 3.3, 3.4, 3.8; build spec docs/dungeons/shadowfang-keep-rework.md, "SK").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h), so
 * every <Boss>Logic.h and its host test can include it. Engine glue is the shared kit (src/Kit/DungeonKit.h).
 *
 * Ownership: this file belongs to WP-K (the SFK layer). A boss WP keeps its own spell ids (inside its slice below),
 * tuning constants and script-local enums in its own <Boss>Logic.h (convention: `enum <Boss>Spells : std::uint32_t
 * { SPELL_<BOSS>_... = <id in its slice> }` and `inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`),
 * and asks the orchestrator, in its report, for any change here.
 *
 * Measured points and arenas are [navmesh estimate] (shadowfang-keep-build.NAVMESH-REPORT.md: the mesh sits about
 * 0.53 yd inside every wall); the arenas are generous boxes around each room's floor (about 0.75 yd past the mesh
 * edge), so a player standing at a real wall is never gripped. A boss WP may tighten its own arena in its own file;
 * WP-P's playtest guide checks the key points with .gps.
 */

#ifndef MOD_DUNGEON_BOSSES_SHADOWFANG_KEEP_REWORK_H
#define MOD_DUNGEON_BOSSES_SHADOWFANG_KEEP_REWORK_H

#include "DungeonKitArena.h"
#include "DungeonKitIds.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace ShadowfangKeepRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Box2;
    using DungeonKit::FrameRect;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapShadowfangKeep = 33;
    // The stock instance name (handoff section 7 #1): the rework replaces the stock InstanceMapScript of that name at
    // load (same-named scripts registered later win), so instance_template is untouched and Apothecary Hummel's
    // holiday scripts (RegisterShadowfangKeepCreatureAI checks this name) keep their AI.
    char constexpr kInstanceScriptName[] = "instance_shadowfang_keep";
    char constexpr kTestCommand[] = "sfktest";      // `.sfktest <boss> <mechanic>` (ShadowfangKeepTestCommand.cpp)
    char constexpr kLogDungeon[] = "sfk";           // DungeonKit::LogMechanic("sfk", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The order is fixed: the save string stores them by position. BOSS_APOTHECARY_HUMMEL
    // must stay 4: the stock Love is in the Air boss is a BossAI on the stock DATA_APOTHECARY_HUMMEL (4) and writes its
    // own slot (core src/server/scripts/EasternKingdoms/ShadowfangKeep/shadowfang_keep.h, boss_apothecary_hummel.cpp).
    // ----------------------------------------------------------------------------------------------------------------
    enum ShadowfangKeepBosses : std::uint32_t
    {
        BOSS_RETHILGORE             = 0,    // S1
        BOSS_RAZORCLAW              = 1,    // S2
        BOSS_SILVERLAINE            = 2,    // S3
        BOSS_SPRINGVALE             = 3,    // S4
        BOSS_APOTHECARY_HUMMEL      = 4,    // stock event boss (Love is in the Air), kept as is
        BOSS_ODO                    = 5,    // S5
        BOSS_DEATHSWORN_CAPTAIN     = 6,    // S6 (rare: only when the saved roll is Present)
        BOSS_FENRUS                 = 7,    // S7: DONE on his final death (heroic phase 2 included)
        BOSS_NANDOS                 = 8,    // S8: DONE on Nandos's death (the pack is his encounter)
        BOSS_ARUGAL                 = 9,    // S9
        BOSS_FACE_HIM_ALONE         = 10,   // S10: the hard mode kill flag (DONE = Arugal died with DATA_HARD_MODE)
    };
    std::uint32_t constexpr kBossCount = 11;
    std::uint32_t constexpr kStockHummelBossId = 4;     // shadowfang_keep.h DATA_APOTHECARY_HUMMEL
    static_assert(BOSS_APOTHECARY_HUMMEL == kStockHummelBossId, "Hummel's BossAI writes boss slot 4");

    // Names by boss state id (`.sfktest state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Rethilgore", "Razorclaw the Butcher", "Baron Silverlaine", "Commander Springvale",
        "Apothecary Hummel (event)", "Odo the Blindwatcher", "Deathsworn Captain", "Fenrus the Devourer",
        "Wolf Master Nandos", "Archmage Arugal", "Face Him Alone (hard mode)",
    } };

    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids above).
    enum ShadowfangKeepData : std::uint32_t
    {
        // Stock ids kept for the stock SmartAI and Hummel (shadowfang_keep.h DataTypes):
        DATA_COURTYARD              = 0,    // TYPE_COURTYARD: the prisoners' action lists 384900 / 385000 set it DONE
                                            // when they open the Courtyard Door; saved
        DATA_LEGACY_FENRUS          = 1,    // TYPE_FENRUS_THE_DEVOURER: read-only (GetData mirrors BOSS_FENRUS)
        DATA_LEGACY_NANDOS          = 2,    // TYPE_WOLF_MASTER_NANDOS: read-only (GetData mirrors BOSS_NANDOS)
        DATA_SPAWN_VALENTINE_ADDS   = 5,    // Hummel's AI: every Crazed Apothecary Generator casts 68610
        // New:
        DATA_PRISONER               = 21,   // which prisoner opened the Courtyard Door (Prisoner::*; S9's edited action
                                            // lists set it); saved
        DATA_HARD_MODE              = 22,   // 1 once Face Him Alone is chosen (S10's gossip); saved, an instance reset
                                            // clears it
        DATA_CAPTAIN_ROLL           = 23,   // DungeonKit::Roll::{Unrolled, Present, Absent}; RollOnce, saved
        DATA_HARD_MODE_KILLED       = 24,   // GetData only: 1 when BOSS_FACE_HIM_ALONE is DONE (the loot flag)
    };

    namespace Prisoner
    {
        std::uint32_t constexpr None = 0;           // not known: the instance picks by the players' team
        std::uint32_t constexpr Ashcrombe = 1;      // Sorcerer Ashcrombe 3850 (Alliance side)
        std::uint32_t constexpr Adamant = 2;        // Deathstalker Adamant 3849 (Horde side)
    }

    // The Deathsworn Captain's spawn chance (stock SmartAI 3872: despawn on AI init, a rare spawn; SK 1040: 15%).
    std::uint32_t constexpr kCaptainPresentChancePct = 15;

    // GetGuidData ids. ObjectData only for units that are never summoned twice (cpp-scripts.md, the ObjectData
    // pitfall): the nine bosses, the two stock prisoners and the stock gameobjects. Never the echoes, guardsmen,
    // voidwalkers, pack wolves, fragments, door stand-ins or the lair prisoner (DATA_LAIR_PRISONER_GUID is the
    // instance's own summon, kept in a member).
    enum ShadowfangKeepObjects : std::uint32_t
    {
        DATA_RETHILGORE_GUID        = 100,
        DATA_RAZORCLAW_GUID         = 101,
        DATA_SILVERLAINE_GUID       = 102,
        DATA_SPRINGVALE_GUID        = 103,
        DATA_ODO_GUID               = 104,
        DATA_DEATHSWORN_CAPTAIN_GUID = 105,
        DATA_FENRUS_GUID            = 106,
        DATA_NANDOS_GUID            = 107,
        DATA_ARUGAL_GUID            = 108,
        DATA_ADAMANT_GUID           = 109,  // the stock cell prisoner (S cell)
        DATA_ASHCROMBE_GUID         = 110,  // the stock cell prisoner (M cell)
        DATA_LANDEN_GUID            = 111,  // Landen Stilwell (N cell)
        DATA_LAIR_PRISONER_GUID     = 112,  // 300513 / 300514 at the lair door (summoned by the instance)

        DATA_COURTYARD_DOOR_GUID    = 120,
        DATA_SORCERERS_GATE_GUID    = 121,
        DATA_ARUGALS_LAIR_GUID      = 122,
        DATA_CELL_DOOR_S_GUID       = 123,
        DATA_CELL_DOOR_M_GUID       = 124,
        DATA_CELL_DOOR_N_GUID       = 125,
        DATA_CELL_LEVER_S_GUID      = 126,
        DATA_CELL_LEVER_M_GUID      = 127,
        DATA_CELL_LEVER_N_GUID      = 128,
        DATA_ARUGALS_FOCUS_GUID     = 129,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum ShadowfangKeepCreatures : std::uint32_t
    {
        // bosses (stock entries; script names bound by apps/dbc-tools source/npcs/shadowfang_keep/<boss>.py)
        NPC_RETHILGORE              = 3914,     // boss_rethilgore_rework
        NPC_RAZORCLAW               = 3886,     // boss_razorclaw_rework
        NPC_SILVERLAINE             = 3887,     // boss_baron_silverlaine_rework
        NPC_SPRINGVALE              = 4278,     // boss_commander_springvale_rework
        NPC_ODO                     = 4279,     // boss_odo_the_blindwatcher_rework
        NPC_DEATHSWORN_CAPTAIN      = 3872,     // boss_deathsworn_captain_rework
        NPC_FENRUS                  = 4274,     // boss_fenrus_the_devourer_rework
        NPC_NANDOS                  = 3927,     // boss_wolf_master_nandos_rework
        NPC_ARUGAL                  = 4275,     // boss_archmage_arugal_rework

        // stock units the scripts refer to
        NPC_ADAMANT                 = 3849,     // Deathstalker Adamant (cell prisoner, SmartAI kept)
        NPC_ASHCROMBE               = 3850,     // Sorcerer Ashcrombe (cell prisoner, SmartAI kept)
        NPC_LANDEN_STILWELL         = 17822,
        NPC_ARUGALS_VOIDWALKER      = 4627,     // rebound to npc_sfk_voidwalker by S7
        NPC_BLEAK_WORG              = 3861,
        NPC_SLAVERING_WORG          = 3862,
        NPC_LUPINE_HORROR           = 3863,
        NPC_WOLFGUARD_WORG          = 5058,
        NPC_LUPINE_DELUSION         = 5097,
        NPC_ARUGAL_CUTSCENE         = 10000,
        NPC_SHADOWFANG_GLUTTON      = 3857,     // the Turned transform's look (display 202)

        // Hummel's holiday event (stock shadowfang_keep.h SKCreatures; the instance keeps the stock cases)
        NPC_DND_CRAZED_APOTHECARY_GENERATOR = 36212,
        NPC_APOTHECARY_HUMMEL       = 36296,
        NPC_CRAZED_APOTHECARY       = 36568,

        // boss kit (new entries, creature 300500-300529, ids.yaml reservation `shadowfang_keep`; each declared by its
        // boss WP in source/npcs/shadowfang_keep/<boss>.py unless noted)
        NPC_SFK_CELL_DOOR           = 300500,   // S1 npc_sfk_cell_door (invisible stand-in, display 11686)
        NPC_SFK_SOUL_FRAGMENT       = 300501,   // S1 npc_sfk_soul_fragment
        NPC_SFK_TAINTED_FRAGMENT    = 300502,   // S1 (heroic)
        NPC_SFK_ECHO_OF_RETHILGORE  = 300503,   // S3 npc_sfk_echo
        NPC_SFK_ECHO_OF_RAZORCLAW   = 300504,   // S3 npc_sfk_echo
        NPC_SFK_ECHO_OF_ODO         = 300505,   // S3 npc_sfk_echo
        NPC_SFK_GUARDSMAN_LIGHT     = 300506,   // S4 npc_sfk_risen_guardsman, Risen Guardsman of the Light
        NPC_SFK_GUARDSMAN_HAMMER    = 300507,   // S4 ... of the Hammer
        NPC_SFK_GUARDSMAN_ALTAR     = 300508,   // S4 ... of the Altar
        NPC_SFK_PACK_BLEAK_WORG     = 300509,   // S8 npc_sfk_pack_wolf, copy of 3861
        NPC_SFK_PACK_LUPINE_HORROR  = 300510,   // S8, copy of 3863
        NPC_SFK_PACK_SLAVERING_WORG = 300511,   // S8, copy of 3862
        NPC_SFK_PACK_WOLFGUARD_WORG = 300512,   // S8, copy of 5058
        NPC_SFK_LAIR_ASHCROMBE      = 300513,   // K declares (archmage_arugal.py), S9 scripts: npc_sfk_lair_prisoner
        NPC_SFK_LAIR_ADAMANT        = 300514,   // K declares (archmage_arugal.py), S9 scripts: npc_sfk_lair_prisoner
        NPC_SFK_WARD_STALKER        = 300515,   // S9
        NPC_SFK_STRIKE_STALKER      = 300516,   // strike / visual stalker (the first WP that needs it declares it)
        // 300517-300529 spare (ask the orchestrator)
    };

    // The nine rework bosses (a heroic copy's GetEntry() is its base entry). Every boss's ArenaGuard skips a unit in
    // combat with another live one of them (DungeonKit::SkipEngagedWithOtherBoss; R2 S-2: Odo and the Captain).
    constexpr bool IsSfkBossEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_RETHILGORE:
            case NPC_RAZORCLAW:
            case NPC_SILVERLAINE:
            case NPC_SPRINGVALE:
            case NPC_ODO:
            case NPC_DEATHSWORN_CAPTAIN:
            case NPC_FENRUS:
            case NPC_NANDOS:
            case NPC_ARUGAL:
                return true;
            default:
                return false;
        }
    }

    // The lair prisoner the instance summons for a DATA_PRISONER value (0 for Prisoner::None).
    constexpr std::uint32_t LairPrisonerEntry(std::uint32_t prisoner)
    {
        return prisoner == Prisoner::Ashcrombe ? std::uint32_t(NPC_SFK_LAIR_ASHCROMBE)
            : prisoner == Prisoner::Adamant ? std::uint32_t(NPC_SFK_LAIR_ADAMANT) : 0u;
    }

    // Whether the lair prisoner waits at the lair door: Nandos is dead, Arugal is not, and Face Him Alone was not
    // chosen (the prisoner leaves for good then). The instance asks on Nandos's DONE and again after a load, which
    // stores the saved states without running SetBossState's switch (R1 S-1).
    constexpr bool LairPrisonerWaits(std::uint32_t nandosState, std::uint32_t arugalState, std::uint32_t hardMode)
    {
        return nandosState == DungeonKit::State::Done && arugalState != DungeonKit::State::Done && hardMode == 0;
    }

    // Whether the instance accepts SetData(DATA_HARD_MODE, value): never once Arugal is dead, and the flag is never lit
    // while he fights (S10 section 6, R2 N-6; `.sfktest instance hardmode` included). Clearing it mid-fight is allowed.
    constexpr bool HardModeChangeAllowed(std::uint32_t arugalState, std::uint32_t value)
    {
        return arugalState != DungeonKit::State::Done && !(value && arugalState == DungeonKit::State::InProgress);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum ShadowfangKeepGameObjects : std::uint32_t
    {
        GO_COURTYARD_DOOR           = 18895,    // opens on DATA_COURTYARD DONE (as stock); lever 101812
        GO_SORCERERS_GATE           = 18972,    // opens on BOSS_FENRUS DONE (door data)
        GO_ARUGALS_LAIR             = 18971,    // opens on BOSS_NANDOS DONE (door data); lever 18899
        GO_CELL_DOOR_S              = 18934,    // spawn 32445; lever 18900 (spawn 32442)
        GO_CELL_DOOR_M              = 18936,    // spawn 33219; lever 18901 (spawn 34006)
        GO_CELL_DOOR_N              = 18935,    // spawn 32446; lever 101811 (spawn 32444)
        GO_CELL_LEVER_S             = 18900,
        GO_CELL_LEVER_M             = 18901,
        GO_CELL_LEVER_N             = 101811,
        GO_LAIR_LEVER               = 18899,
        GO_COURTYARD_LEVER          = 101812,
        GO_ARUGALS_FOCUS            = 18973,
        GO_BOOTY_BAY_ALARM_BELL     = 175948,   // the bell's stock template (not spawned on map 33)

        // new (gameobject 301100-301149, ids.yaml reservation `shadowfang_keep`; templates in WP-K's core rev)
        GO_SFK_CELL_KEY             = 301100,   // S1: the Cell Key's look (a Pickups goEntry, no script)
        GO_SFK_ALARM_BELL           = 301101,   // S5: go_sfk_alarm_bell (spawns: S5's rev, spawnMask 3)
        GO_SFK_OFFAL_SLICK          = 301103,   // S2: the heroic Offal Slick's blood pools (template in S2's rev)
        // 301102 and 301104-301149 spare
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 205900-206099, ids.yaml reservation `shadowfang_keep`; declared in apps/dbc-tools
    // source/npcs/shadowfang_keep/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h.
    // The kit-wide 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h).
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 205900, 206099 };
    IdSlice constexpr kSpellsShared{ 205900, 205909 };          // K: named cast bars, the hard mode flag aura
    IdSlice constexpr kSpellsRethilgore{ 205910, 205929 };      // S1
    IdSlice constexpr kSpellsRazorclaw{ 205930, 205944 };       // S2
    IdSlice constexpr kSpellsSilverlaine{ 205945, 205964 };     // S3
    IdSlice constexpr kSpellsSpringvale{ 205965, 205989 };      // S4
    IdSlice constexpr kSpellsOdo{ 205990, 206009 };             // S5
    IdSlice constexpr kSpellsDeathswornCaptain{ 206010, 206019 }; // S6
    IdSlice constexpr kSpellsFenrus{ 206020, 206039 };          // S7
    IdSlice constexpr kSpellsNandos{ 206040, 206059 };          // S8
    IdSlice constexpr kSpellsArugal{ 206060, 206089 };          // S9 (and S10's sub-slice below)
    IdSlice constexpr kSpellsFaceHimAlone{ 206085, 206089 };    // S10, the last five of Arugal's slice
    IdSlice constexpr kSpellsSpare{ 206090, 206099 };

    inline std::array<IdSlice, 10> constexpr kBossSpellSlices{ {
        kSpellsShared, kSpellsRethilgore, kSpellsRazorclaw, kSpellsSilverlaine, kSpellsSpringvale, kSpellsOdo,
        kSpellsDeathswornCaptain, kSpellsFenrus, kSpellsNandos, kSpellsArugal,
    } };

    IdSlice constexpr kCreaturesReservation{ 300500, 300529 };
    IdSlice constexpr kGameObjectsReservation{ 301100, 301149 };

    // Stock spells the build specs keep (DD scales them on heroic; handoff section 3.7).
    enum ShadowfangKeepStockSpells : std::uint32_t
    {
        SPELL_TOXIC_SALIVA          = 7125,     // Fenrus
        SPELL_WAVERING_WILL         = 7127,     // Bleak Worg (NA1)
        SPELL_SUMMON_LUPINE_DELUSIONS = 7132,   // Lupine Horror (NA2)
        SPELL_HOWLING_RAGE_1        = 7481,     // Odo 70%
        SPELL_HOWLING_RAGE_2        = 7483,     // Odo 50%
        SPELL_HOWLING_RAGE_3        = 7484,     // Odo 30%
        SPELL_SUMMON_VALENTINE_ADD  = 68610,    // Hummel's generators (stock instance)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // creature_text groups (SK "Text" tables). Texts are inserted by each boss WP's own SQL rev; stock lines stay.
    // ----------------------------------------------------------------------------------------------------------------
    enum RethilgoreTexts : std::uint8_t
    {
        YELL_RETHILGORE_AGGRO           = 0,    // "More meat for the cells!"
        EMOTE_RETHILGORE_LOCK_UP        = 1,    // RG1, $n
        EMOTE_RETHILGORE_KEYS           = 2,    // RG3
    };
    enum CellPrisonerTexts : std::uint8_t
    {
        SAY_ADAMANT_CELLMATE            = 5,    // Deathstalker Adamant: a player lands in her cell (S1)
        SAY_ASHCROMBE_CELLMATE          = 5,    // Sorcerer Ashcrombe: a player lands in his cell (S1)
        SAY_LANDEN_CELLMATE             = 0,    // Landen Stilwell: a player lands in his cell (S1)
        SAY_PRISONER_LAIR_PULL          = 6,    // lair prisoner copies 300513 / 300514: Arugal's pull (S9)
        SAY_PRISONER_HARD_MODE          = 7,    // lair prisoner copies: Face Him Alone chosen; inserted by S9's
                                                // rev, said by S10 through SfkLairPrisoner::LeaveForHardMode
        SAY_PRISONER_FAREWELL           = 8,    // stock prisoners at the Courtyard Door, replaces stock 2 / 3 (S9)
    };
    enum RazorclawTexts : std::uint8_t
    {
        YELL_RAZORCLAW_AGGRO            = 0,
        EMOTE_RAZORCLAW_MEAT_HOOK       = 1,    // RC1, $n
        EMOTE_RAZORCLAW_BUTCHERS_CUT    = 2,    // RC3
    };
    enum SilverlaineTexts : std::uint8_t
    {
        YELL_SILVERLAINE_AGGRO          = 0,    // stock
        YELL_SILVERLAINE_ECHO_RETHILGORE = 1,
        YELL_SILVERLAINE_ECHO_RAZORCLAW = 2,
        YELL_SILVERLAINE_ECHO_ODO       = 3,
        YELL_SILVERLAINE_NIGHT_ENDS     = 4,    // heroic, BS7
    };
    enum SpringvaleTexts : std::uint8_t
    {
        YELL_SPRINGVALE_AGGRO           = 0,    // stock
        YELL_SPRINGVALE_DEATH           = 1,    // stock
        EMOTE_SPRINGVALE_HAMMER         = 2,    // SP1, $n
        YELL_SPRINGVALE_OATH            = 3,    // SP6
        YELL_SPRINGVALE_WRATH_OF_GOD    = 4,    // heroic, SP8
        EMOTE_SPRINGVALE_PRAYER_ENDS    = 5,    // heroic, SP8
    };
    enum OdoTexts : std::uint8_t
    {
        EMOTE_ODO_HUNT                  = 0,    // OD1, $n
        EMOTE_ODO_BELL                  = 1,    // OD4
        EMOTE_ODO_FRENZY                = 2,    // heroic, OD6
    };
    enum DeathswornCaptainTexts : std::uint8_t
    {
        EMOTE_CAPTAIN_CHARGE            = 0,    // DC1, $n
        EMOTE_CAPTAIN_CLEAVE            = 1,    // DC3
    };
    enum FenrusTexts : std::uint8_t
    {
        EMOTE_FENRUS_SHADOW_LEAP        = 0,    // heroic, FN6
    };
    enum NandosTexts : std::uint8_t
    {
        YELL_NANDOS_PACK_DEAD           = 0,    // stock, on the last wolf's death
        EMOTE_NANDOS_MARK_THE_PREY      = 1,    // NA6, $n
    };
    enum ArugalTexts : std::uint8_t
    {
        YELL_ARUGAL_FENRUS_PULL         = 0,    // stock, now on Fenrus's pull (S7)
        YELL_ARUGAL_AGGRO               = 1,    // stock: Arugal's aggro (S9); Fenrus heroic FN5 (S7)
        YELL_ARUGAL_RELEASE_YOUR_RAGE   = 2,    // stock: AR4 (S9); the first FN1 (S7)
        YELL_ARUGAL_ANOTHER_FALLS       = 3,    // stock: a kill and AR6
        YELL_ARUGAL_MOONRISE            = 4,    // heroic, AR9
        EMOTE_ARUGAL_MOONRISE           = 5,    // heroic, AR9
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (handoff section 3.8; shadowfang-keep-build.NAVMESH-REPORT.md). DB positions are exact; the rest
    // are [navmesh estimate].
    // ----------------------------------------------------------------------------------------------------------------
    struct Point3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
    };

    // The report's map frames: "up" is `upAngle` (a WoW orientation), "right" is upAngle - 90 degrees, and a map point
    // (u right, v up) from `origin` is x = x0 + u * cos(up - 90) + v * cos(up),
    // y = y0 + u * sin(up - 90) + v * sin(up).
    // As a kit FrameRect (X along `angle`, Y along angle + 90 degrees): angle = upAngle, frame x = v, frame y = -u.
    float constexpr kKeepUp = -0.376f;          // the keep grid (NNE), 21.5 degrees east of north
    float constexpr kSpringvaleUp = 0.262f;     // Springvale's hall (15 degrees west of north)
    float constexpr kNorthUp = 0.f;             // Fenrus, Nandos, Arugal maps: up = north (+x)

    inline FrameRect ReportFrame(Vec2 origin, float upAngle)
    {
        return { origin, upAngle, 0.f, 0.f };
    }

    // A box of the report's map, u in [uMin, uMax] and v in [vMin, vMax], in ReportFrame coordinates.
    constexpr Box2 ReportBox(float uMin, float uMax, float vMin, float vMax)
    {
        return { vMin, vMax, -uMax, -uMin };
    }

    // A map point of the report (u right, v up) in world coordinates.
    inline Vec2 ReportPoint(Vec2 origin, float upAngle, float u, float v)
    {
        return DungeonKit::FramePoint(ReportFrame(origin, upAngle), v, -u);
    }

    // --- Rethilgore's cell block (map origin: the middle cell door) --------------------------------------------------
    Point3 constexpr kRethilgoreSpawn{ -252.1f, 2123.1f, 81.2f };
    float constexpr kCellBlockFloorZ = 81.4f;

    enum CellId : std::uint8_t
    {
        CELL_S = 0,     // ESE: Deathstalker Adamant (SK's "South")
        CELL_M = 1,     // Sorcerer Ashcrombe
        CELL_N = 2,     // WNW: Landen Stilwell (SK's "North"; the corridor narrows to 4.6 yd in front of it)
    };
    std::size_t constexpr kCellCount = 3;

    // Cell doors (DB), levers (DB), the stock occupants (DB) and the landing points (navmesh) per CellId.
    inline std::array<Point3, kCellCount> constexpr kCellDoors{ {
        { -251.2f, 2116.4f, 81.2f }, { -247.8f, 2125.2f, 81.1f }, { -244.1f, 2134.4f, 81.1f } } };
    inline std::array<std::uint32_t, kCellCount> constexpr kCellDoorEntries{ {
        GO_CELL_DOOR_S, GO_CELL_DOOR_M, GO_CELL_DOOR_N } };
    inline std::array<std::uint32_t, kCellCount> constexpr kCellLeverEntries{ {
        GO_CELL_LEVER_S, GO_CELL_LEVER_M, GO_CELL_LEVER_N } };
    inline std::array<Point3, kCellCount> constexpr kCellLevers{ {
        { -252.7f, 2114.2f, 82.8f }, { -249.2f, 2123.1f, 82.8f }, { -245.6f, 2132.3f, 82.8f } } };
    inline std::array<std::uint32_t, kCellCount> constexpr kCellOccupants{ {
        NPC_ADAMANT, NPC_ASHCROMBE, NPC_LANDEN_STILWELL } };
    inline std::array<Point3, kCellCount> constexpr kCellLandings{ {
        { -248.2f, 2115.2f, 81.7f }, { -243.8f, 2123.8f, 81.4f }, { -240.8f, 2135.8f, 81.6f } } };
    // Fragment points (corridor side, 3 to 6 yd from the door): 3 / 2 / 3 per cell (only two clear him at M).
    inline std::array<Vec2, 3> constexpr kFragmentPointsS{ { { -254.8f, 2118.2f }, { -254.8f, 2120.8f },
        { -254.2f, 2115.8f } } };
    inline std::array<Vec2, 2> constexpr kFragmentPointsM{ { { -251.2f, 2127.2f }, { -249.8f, 2129.2f } } };
    inline std::array<Vec2, 3> constexpr kFragmentPointsN{ { { -246.2f, 2137.8f }, { -247.2f, 2134.8f },
        { -248.8f, 2132.2f } } };
    // Key landings (8 to 12 yd from him, along the corridor; a throw across it hits the wall).
    inline std::array<Point3, 2> constexpr kKeyLandings{ { { -248.2f, 2132.8f, 81.3f }, { -258.2f, 2117.8f, 81.6f } } };

    inline Vec2 CellBlockOrigin()
    {
        return kCellDoors[CELL_M].XY();
    }

    // Corridor and cells in the report's frame (origin the M door, keep grid). The cells start 0.25 yd past the door
    // line, so a player pressed against a closed door from inside still counts as inside.
    Box2 constexpr kCorridorBox = ReportBox(-14.75f, 12.75f, -9.25f, 0.25f);
    inline std::array<Box2, kCellCount> constexpr kCellBoxes{ {
        ReportBox(5.75f, 13.25f, 0.25f, 15.f),     // S
        ReportBox(-3.75f, 3.75f, 0.25f, 15.f),     // M
        ReportBox(-14.5f, -5.75f, 0.25f, 13.f),    // N
    } };
    float constexpr kCellBlockZMin = 80.f;
    float constexpr kCellBlockZMax = 84.f;          // the stair at the WNW end climbs to z 87

    inline Arena CellArena(CellId cell)
    {
        return Arena(ArenaRegion::Frame(ReportFrame(CellBlockOrigin(), kKeepUp), kCellBoxes[cell], kCellBlockZMin,
            kCellBlockZMax));
    }

    inline Arena CorridorArena()
    {
        return Arena(ArenaRegion::Frame(ReportFrame(CellBlockOrigin(), kKeepUp), kCorridorBox, kCellBlockZMin,
            kCellBlockZMax));
    }

    // Rethilgore's arena: the corridor and the three cells.
    inline Arena RethilgoreArena()
    {
        Arena arena = CorridorArena();
        for (std::size_t i = 0; i < kCellCount; ++i)
            arena.Add(CellArena(CellId(i)).regions.front());
        return arena;
    }

    // A point in the corridor `outYd` in front of a cell's door (where a unit kept out of a closed cell is put).
    inline Vec2 InFrontOfCell(CellId cell, float outYd = 2.5f)
    {
        Vec2 const door = kCellDoors[cell].XY();
        return { door.x - std::cos(kKeepUp) * outYd, door.y - std::sin(kKeepUp) * outYd };
    }

    // --- Razorclaw's kitchen (map origin: Razorclaw) -----------------------------------------------------------------
    Point3 constexpr kRazorclawSpawn{ -202.6f, 2258.0f, 76.3f };

    inline Arena RazorclawArena()
    {
        return Arena(ArenaRegion::Frame(ReportFrame(kRazorclawSpawn.XY(), kKeepUp),
            ReportBox(-12.f, 9.75f, -11.75f, 13.f), 75.f, 79.f));
    }

    // --- Baron Silverlaine's alcove and hall (map origin: Silverlaine) -----------------------------------------------
    Point3 constexpr kSilverlaineSpawn{ -275.3f, 2297.4f, 76.2f };

    inline Arena SilverlaineArena()
    {
        FrameRect const frame = ReportFrame(kSilverlaineSpawn.XY(), kKeepUp);
        Arena arena(ArenaRegion::Frame(frame, ReportBox(-6.75f, 5.75f, -1.75f, 10.5f), 74.5f, 79.f));   // alcove
        arena.Add(ArenaRegion::Frame(frame, ReportBox(-12.75f, 11.75f, 10.5f, 62.75f), 74.5f, 79.f));   // hall
        return arena;
    }

    // --- Commander Springvale's hall (map origin: Springvale; up = 0.262) --------------------------------------------
    Point3 constexpr kSpringvaleSpawn{ -222.6f, 2259.4f, 102.8f };
    // Risen Guardsman rise points: two flanks and the middle, 10 to 14.5 yd from him (120 degree spacing does not fit).
    inline std::array<Point3, 3> constexpr kGuardsmanRisePoints{ { { -232.8f, 2262.2f, 102.6f },
        { -235.8f, 2253.2f, 101.6f }, { -226.8f, 2250.2f, 101.9f } } };

    inline Arena SpringvaleArena()
    {
        return Arena(ArenaRegion::Frame(ReportFrame(kSpringvaleSpawn.XY(), kSpringvaleUp),
            ReportBox(-10.75f, 11.75f, -44.75f, 2.75f), 99.5f, 105.5f));
    }

    // --- Odo the Blindwatcher's room (map origin: Odo) ---------------------------------------------------------------
    Point3 constexpr kOdoSpawn{ -236.7f, 2146.1f, 100.1f };
    Point3 constexpr kOdoDoor{ -247.3f, 2110.8f, 100.2f };      // the room's one door, 42 yd from him
    // Bell spots (handoff section 7 #24: at least 19 yd apart, only 3.4 to 3.9 yd clear).
    inline std::array<Point3, 3> constexpr kBellSpots{ { { -248.8f, 2148.2f, 100.7f },
        { -245.8f, 2129.2f, 101.3f }, { -260.8f, 2117.2f, 101.1f } } };

    inline Arena OdoArena()
    {
        return Arena(ArenaRegion::Frame(ReportFrame(kOdoSpawn.XY(), kKeepUp), ReportBox(-2.75f, 41.f, -17.25f, 3.5f),
            99.f, 103.5f));
    }

    // --- The Deathsworn Captain's north hall and walkway (map origin: Odo; handoff section 7 #25) --------------------
    Point3 constexpr kCaptainSpawn{ -192.0f, 2124.5f, 97.4f };
    std::uint32_t constexpr kCaptainPathId = 1345170;           // 10 points, kept; he turns in Odo's doorway

    // Region 0 the north hall; 1 the walkway (navmesh floor u 33.75 to 38.5, v 3 to 44, z 97.3 to 100.2; side niches
    // reach u 32.25 and 40, the west ones over the drop are left 0.5 yd out so no hall charge cuts across the void);
    // 2 Odo's ESE alcove (floor u 33 to 39.75, v -16 to 3, z 100.2 to 101.2): he turns in Odo's door, so a pull there
    // fights in the alcove behind it (bot clear 2026-11-08: 38 grips in 77 s). Odo's own end of the room (his spawn,
    // u 0) stays off. The inner yard under the walkway (z 77 to 81) and the jail under the alcove (z 81 to 87) are
    // below the z bands.
    inline Arena DeathswornCaptainArena()
    {
        FrameRect const frame = ReportFrame(kOdoSpawn.XY(), kKeepUp);
        Arena arena(ArenaRegion::Frame(frame, ReportBox(-31.f, 39.f, 39.25f, 52.75f), 95.5f, 99.f));      // north hall
        arena.Add(ArenaRegion::Frame(frame, ReportBox(32.75f, 40.75f, 2.75f, 41.f), 95.5f, 101.5f));     // walkway
        arena.Add(ArenaRegion::Frame(frame, ReportBox(31.25f, 41.25f, -17.25f, 3.5f), 99.f, 103.5f));    // Odo's alcove
        return arena;
    }

    // --- Fenrus the Devourer's round room ----------------------------------------------------------------------------
    Point3 constexpr kFenrusSpawn{ -135.6f, 2168.7f, 128.8f };
    Vec2 constexpr kFenrusRoomCenter{ -146.5f, 2173.1f };
    float constexpr kFenrusRoomRadius = 17.f;                   // walls 12.5 to 16.6 yd from the centre
    // FN1 strike points on the room edge, every 30 degrees from the centre (the 0 degree point, 4.6 yd from him, is
    // dropped: handoff section 3.8).
    inline std::array<Vec2, 10> constexpr kFenrusStrikePoints{ { { -136.8f, 2178.8f }, { -139.8f, 2184.8f },
        { -146.8f, 2184.8f }, { -151.2f, 2181.2f }, { -157.2f, 2179.2f }, { -158.2f, 2173.2f }, { -155.8f, 2167.8f },
        { -151.8f, 2164.2f }, { -146.8f, 2161.2f }, { -141.8f, 2164.8f } } };
    float constexpr kFenrusFloorZ = 129.2f;
    Point3 constexpr kFenrusBaitPoint{ -159.8f, 2178.2f, 129.4f };     // farthest with 2 yd clearance, 26.0 yd
    // Arugal's Voidwalker 4627: the stock summon group 4275/1 points (unused by the rework, kept for reference).
    Point3 constexpr kSorcerersGate{ -129.0f, 2166.2f, 129.2f };

    inline Arena FenrusArena()
    {
        return Arena(ArenaRegion::Circle(kFenrusRoomCenter, kFenrusRoomRadius, 127.5f, 132.5f));
    }

    // --- Wolf Master Nandos's room -----------------------------------------------------------------------------------
    Point3 constexpr kNandosSpawn{ -120.7f, 2162.0f, 155.8f };
    Vec2 constexpr kNandosRoomCenter{ -134.1f, 2168.1f };
    float constexpr kNandosRoomRadius = 19.25f;                 // walls 15.8 to 18 yd from the centre
    float constexpr kNandosRoomMaxX = -117.75f;                 // the lair door's line (door at x -118.1)
    Point3 constexpr kNandosOpenPoint{ -128.8f, 2165.2f, 155.9f };     // the most open point (Mark the Prey ring)
    // The pack's stock spawns (guids 16238-16241; S8 repoints them to the copies 300509-300512).
    inline std::array<Point3, 4> constexpr kPackSpawns{ { { -118.7f, 2173.4f, 155.8f },      // Lupine Horror 16238
        { -127.6f, 2153.3f, 155.8f },                                                      // Bleak Worg 16239
        { -139.4f, 2182.9f, 155.8f },                                                      // Slavering Worg 16240
        { -149.2f, 2163.2f, 155.8f } } };                                                  // Wolfguard Worg 16241

    // The round room as a 24-gon, cut at the lair door's line so the antechamber beyond the door is Arugal's.
    inline Arena NandosArena()
    {
        std::vector<Vec2> ring;
        int constexpr kSides = 24;
        for (int i = 0; i < kSides; ++i)
        {
            float const a = 2.f * 3.14159265f * float(i) / float(kSides);
            Vec2 p{ kNandosRoomCenter.x + kNandosRoomRadius * std::cos(a),
                kNandosRoomCenter.y + kNandosRoomRadius * std::sin(a) };
            p.x = std::min(p.x, kNandosRoomMaxX);
            ring.push_back(p);
        }
        return Arena(ArenaRegion::Polygon(std::move(ring), 154.5f, 159.5f));
    }

    // --- Archmage Arugal's room: platform, gallery, antechamber, ramps and the lower floor --------------------------
    Point3 constexpr kArugalSpawn{ -76.8f, 2152.4f, 155.8f };
    Point3 constexpr kArugalsLairDoor{ -118.1f, 2161.9f, 155.7f };
    // Shadow Port spots (spell_target_position, DB): 7136 next to the antechamber floor, 7586 on his platform, 7587
    // 9.7 yd above the lower floor, off the mesh (user ruling 2026-11-07, handoff section 10: he keeps his stock
    // spots; S9 redesigns around them). S9 uses 7136 and 7586 plus his spawn; 7587 is dropped (unreachable) and kept
    // here for reference only.
    inline std::array<Point3, 3> constexpr kShadowPortSpots{ { { -105.654f, 2154.98f, 156.43f },    // 7136
        { -84.99f, 2151.01f, 155.62f },                                                           // 7586
        { -103.46f, 2122.1f, 155.655f } } };                                                      // 7587
    inline std::array<std::uint32_t, 3> constexpr kShadowPortSpells{ { 7136, 7586, 7587 } };
    // The lair prisoner: summoned at the wait point on Nandos's side of the lair door (the instance, on Nandos DONE);
    // S9 moves it to the gallery over the lower floor for the fight.
    Point3 constexpr kLairPrisonerWait{ -121.2f, 2165.2f, 156.0f };
    float constexpr kLairPrisonerWaitFacing = 5.47f;            // toward the lair door
    Point3 constexpr kLairPrisonerGallery{ -96.0f, 2167.0f, 155.8f };

    inline Arena ArugalArena()
    {
        auto rect = [](float x0, float x1, float y0, float y1, float z0, float z1)
        {
            return ArenaRegion::Polygon({ { x0, y0 }, { x1, y0 }, { x1, y1 }, { x0, y1 } }, z0, z1);
        };
        Arena arena(rect(-118.5f, -66.5f, 2137.5f, 2174.5f, 152.5f, 159.f));    // platform, gallery, antechamber
        arena.Add(rect(-125.5f, -74.f, 2112.f, 2172.5f, 143.5f, 153.f));        // ramps and the lower floor
        return arena;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string (handoff section 7 #2): a new header "SR", the 11 boss states, then the 4 saved data
    // fields. A stock "S K a b c" save (instance_shadowfang_keep) is ignored: none is live and instances reset daily.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "SR";

    enum SaveExtra : std::size_t
    {
        EXTRA_COURTYARD     = 0,
        EXTRA_PRISONER      = 1,
        EXTRA_HARD_MODE     = 2,
        EXTRA_CAPTAIN_ROLL  = 3,
    };
    std::size_t constexpr kSaveExtraCount = 4;

    struct SfkSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        std::uint32_t courtyard = DungeonKit::State::NotStarted;
        std::uint32_t prisoner = Prisoner::None;
        std::uint32_t hardMode = 0;
        std::uint32_t captainRoll = DungeonKit::Roll::Unrolled;
    };

    inline std::string FormatSfkSave(SfkSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_COURTYARD] = s.courtyard;
        extras[EXTRA_PRISONER] = s.prisoner;
        extras[EXTRA_HARD_MODE] = s.hardMode;
        extras[EXTRA_CAPTAIN_ROLL] = s.captainRoll;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // False on a missing or foreign header (a stock "S K" save): the save is ignored. Loaded values are sanitized:
    // states through SanitizeLoadedState, the courtyard to DONE or NOT_STARTED, the prisoner to Prisoner::*, the hard
    // mode to 0 / 1, the roll through SanitizeLoadedRoll.
    inline bool ParseSfkSave(std::string const& in, SfkSave& out)
    {
        out = SfkSave{};
        DungeonKit::StateSave raw;
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw))
            return false;
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        out.courtyard = raw.extras[EXTRA_COURTYARD] == DungeonKit::State::Done ? DungeonKit::State::Done
            : DungeonKit::State::NotStarted;
        std::uint32_t const prisoner = raw.extras[EXTRA_PRISONER];
        out.prisoner = prisoner <= Prisoner::Adamant ? prisoner : Prisoner::None;
        out.hardMode = raw.extras[EXTRA_HARD_MODE] ? 1 : 0;
        out.captainRoll = DungeonKit::SanitizeLoadedRoll(raw.extras[EXTRA_CAPTAIN_ROLL]);
        return true;
    }
}

#endif
