/*
 * mod-dungeon-bosses, Scholomance (map 289): the shared ids, boss states, data fields, texts, measured points, arenas,
 * the save string, the Passing Grades and the keepsake rules of the Scholomance build
 * (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md sections 3.1-3.3, 3.7, 3.8, 3.12 and the user rulings
 * of section 10; build spec docs/dungeons/scholomance-rework.md, "SC").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h), so
 * every <Boss>Logic.h and its host test can include it. Engine glue: the shared kit (src/Kit/DungeonKit.h) and the
 * Scholomance kit (ScholomanceKit.h, SoloLesson.h).
 *
 * Ownership: this file belongs to WP-KS (the Scholomance kit). A boss WP keeps its own spell ids (inside its slice
 * below), tuning constants and script-local enums in its own <Boss>Logic.h (convention: `enum <Boss>Spells :
 * std::uint32_t { SPELL_<BOSS>_... = <id in its slice> }` and `inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), and asks the orchestrator, in its report, for any change here.
 *
 * Measured points, frames and arenas are [navmesh estimate] (scholomance-build.NAVMESH-REPORT.md: the mesh sits about
 * 0.53 yd inside every wall) unless marked [db] (creature, gameobject or spell_target_position rows, exact). Arenas are
 * the report's leash circles with a z band per floor (the instructor rooms are stacked: upper rooms at z 85 over the
 * lower vaults at z 72 to 76), so no boss's spawn sits in another boss's arena (tests/scholomance_test.cpp). A boss WP
 * may tighten its own arena in its own file; WP-P's playtest guide checks the key points with `.gps`.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_REWORK_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_REWORK_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace ScholomanceRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Box2;
    using DungeonKit::FrameRect;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapScholomance = 289;
    // The stock instance name (handoff section 10, ruling on section 7 #2): the rework replaces the stock
    // InstanceMapScript of that name at load (same-named scripts registered later win; modules load after the core
    // scripts), so instance_template is untouched and the stock Kirtonos, Kormok and Scholomance Occultist AIs
    // (GetScholomanceAI checks this name) keep working with no copies.
    char constexpr kInstanceScriptName[] = "instance_scholomance";
    // `.dbtest scholo <boss> <mechanic>` (handoff section 7 #25): the K0 shell's command name; the chat command map
    // splits it at the space, so it nests under a shared `.dbtest` root (ScholomanceTestCommand.cpp).
    char constexpr kTestCommand[] = "dbtest scholo";
    char constexpr kLogDungeon[] = "scholo";        // DungeonKit::LogMechanic("scholo", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The order is fixed: the save string stores them by position. BOSS_GANDLING must stay 3:
    // the stock boss_darkmaster_gandling is a BossAI on the stock DATA_DARKMASTER_GANDLING (3), so if the stock AI ever
    // runs under this instance (a data rollback) it writes Gandling's own slot, never another boss's (the SFK Hummel
    // lesson).
    // ----------------------------------------------------------------------------------------------------------------
    enum ScholomanceBosses : std::uint32_t
    {
        BOSS_JANDICE                = 0,    // S1 Jandice Barov
        BOSS_RATTLEGORE             = 1,    // S2
        BOSS_MARDUK_VECTUS          = 2,    // S3: one encounter, DONE when both are dead (shared health)
        BOSS_GANDLING               = 3,    // S11 Darkmaster Gandling (stock slot 3, see above)
        BOSS_RAS                    = 4,    // S4 Ras Frostwhisper (and S12's hard mode fight)
        BOSS_MALICIA                = 5,    // S5 Instructor Malicia
        BOSS_KRASTINOV              = 6,    // S6 Doctor Theolen Krastinov
        BOSS_POLKELT                = 7,    // S7 Lorekeeper Polkelt
        BOSS_RAVENIAN               = 8,    // S8 The Ravenian (and Master Corvane)
        BOSS_ALEXEI                 = 9,    // S9 Lord Alexei Barov
        BOSS_ILLUCIA                = 10,   // S10 Lady Illucia Barov
    };
    std::uint32_t constexpr kBossCount = 11;
    std::uint32_t constexpr kStockGandlingBossId = 3;   // scholomance.h DATA_DARKMASTER_GANDLING
    static_assert(BOSS_GANDLING == kStockGandlingBossId, "the stock Gandling BossAI writes boss slot 3");

    // Names by boss state id (`.dbtest scholo state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Jandice Barov", "Rattlegore", "Marduk Blackpool and Vectus", "Darkmaster Gandling", "Ras Frostwhisper",
        "Instructor Malicia", "Doctor Theolen Krastinov", "Lorekeeper Polkelt", "The Ravenian",
        "Lord Alexei Barov", "Lady Illucia Barov",
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The six instructors (Passing Grades, Gandling's reveal) and their classrooms (detention, the gates)
    // ----------------------------------------------------------------------------------------------------------------

    // Grade order (the VISUALS-REPORT icon order: Malicia, Krastinov, Polkelt, the Ravenian, Alexei, Illucia).
    enum class Instructor : std::uint8_t
    {
        Malicia = 0,
        Krastinov = 1,
        Polkelt = 2,
        Ravenian = 3,
        Alexei = 4,
        Illucia = 5,
    };
    std::size_t constexpr kInstructorCount = 6;

    // Classrooms in the stock order of boss_darkmaster_gandling.cpp (GandlingGateIds, GandlingPortalSpells and
    // SummonPos index alike; never reorder).
    enum class Classroom : std::uint8_t
    {
        ShadowVault = 0,        // lower north: Illucia
        BarovVault = 1,         // lower east: Alexei
        RavenianVault = 2,      // lower south: the Ravenian
        HallOfSecrets = 3,      // upper north: Polkelt
        HallOfTheDamned = 4,    // upper east: Krastinov
        Coven = 5,              // upper south: Malicia
    };
    std::size_t constexpr kClassroomCount = 6;

    inline std::array<char const*, kInstructorCount> constexpr kInstructorNames{ {
        "Malicia", "Krastinov", "Polkelt", "Ravenian", "Alexei", "Illucia" } };
    inline std::array<char const*, kClassroomCount> constexpr kClassroomNames{ {
        "the Shadow Vault", "the Barov Family Vault", "the Vault of the Ravenian", "the Hall of Secrets",
        "the Hall of the Damned", "the Coven" } };

    constexpr std::uint32_t InstructorBoss(Instructor i)
    {
        switch (i)
        {
            case Instructor::Malicia:   return BOSS_MALICIA;
            case Instructor::Krastinov: return BOSS_KRASTINOV;
            case Instructor::Polkelt:   return BOSS_POLKELT;
            case Instructor::Ravenian:  return BOSS_RAVENIAN;
            case Instructor::Alexei:    return BOSS_ALEXEI;
            case Instructor::Illucia:   return BOSS_ILLUCIA;
        }
        return BOSS_MALICIA;
    }

    constexpr std::optional<Instructor> InstructorOfBoss(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_MALICIA:   return Instructor::Malicia;
            case BOSS_KRASTINOV: return Instructor::Krastinov;
            case BOSS_POLKELT:   return Instructor::Polkelt;
            case BOSS_RAVENIAN:  return Instructor::Ravenian;
            case BOSS_ALEXEI:    return Instructor::Alexei;
            case BOSS_ILLUCIA:   return Instructor::Illucia;
            default:             return std::nullopt;
        }
    }

    constexpr Classroom InstructorClassroom(Instructor i)
    {
        switch (i)
        {
            case Instructor::Malicia:   return Classroom::Coven;
            case Instructor::Krastinov: return Classroom::HallOfTheDamned;
            case Instructor::Polkelt:   return Classroom::HallOfSecrets;
            case Instructor::Ravenian:  return Classroom::RavenianVault;
            case Instructor::Alexei:    return Classroom::BarovVault;
            case Instructor::Illucia:   return Classroom::ShadowVault;
        }
        return Classroom::Coven;
    }

    constexpr Instructor ClassroomInstructor(Classroom c)
    {
        switch (c)
        {
            case Classroom::ShadowVault:     return Instructor::Illucia;
            case Classroom::BarovVault:      return Instructor::Alexei;
            case Classroom::RavenianVault:   return Instructor::Ravenian;
            case Classroom::HallOfSecrets:   return Instructor::Polkelt;
            case Classroom::HallOfTheDamned: return Instructor::Krastinov;
            case Classroom::Coven:           return Instructor::Malicia;
        }
        return Instructor::Malicia;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids above)
    // ----------------------------------------------------------------------------------------------------------------
    enum ScholomanceData : std::uint32_t
    {
        // Stock ids (scholomance.h DataTypes), kept for the stock scripts that stay:
        DATA_KIRTONOS_THE_HERALD    = 0,    // the brazier's SmartAI (SetData(0, 1)) and Kirtonos's AI (FAIL, DONE);
                                            // the stock summon / gate logic, copied; saved
        DATA_MINI_BOSSES            = 1,    // stock raw counter: SetData is ignored (the six instructor states own the
                                            // reveal, handoff section 7 #11); GetData = instructors DONE (0..6)
        DATA_RAS_HUMAN              = 2,    // the stock Boon of Life aura script sets it (quest 5466); not saved,
                                            // as stock
        DATA_DARKMASTER_GANDLING    = 3,    // stock: Gandling's entrance gate (IN_PROGRESS closes it); GetData =
                                            // BOSS_GANDLING's state
        // New (20 on):
        DATA_KEEPSAKE_PAGE          = 20,   // SetData(20, page 0..2): S12's page GO found a page (heroic); GetData =
                                            // the page mask (bit per page); saved
        DATA_KEEPSAKE_PAGE_COUNT    = 21,   // GetData only: pages found (0..3)
        DATA_KEEPSAKE_BOUND         = 22,   // SetData(22, 1): S12's book GO binds the keepsake (all 3 pages,
                                            // heroic); GetData 0 / 1; saved
        DATA_RAS_HARD_MODE          = 23,   // SetData(23, 1): the alchemy table starts "the Torn Keepsake" (bound
                                            // book, heroic, Ras not fighting and not dead); 0 clears it unless Ras is
                                            // dead; saved
        DATA_RAS_HARD_MODE_KILLED   = 24,   // GetData only: Ras died with DATA_RAS_HARD_MODE lit (the loot flag);
                                            // saved
        DATA_GANDLING_HARD_MODE     = 25,   // SetData(25, 1): the honors program paper is signed ("the Graduate
                                            // Exam"; honors open, heroic, Gandling revealed, not fighting, not dead);
                                            // saved
        DATA_GANDLING_HARD_MODE_KILLED = 26, // GetData only: Gandling died with DATA_GANDLING_HARD_MODE lit; saved
        DATA_GANDLING_REVEALED      = 27,   // GetData only: 1 when all six instructors are DONE
        DATA_HONORS_OPEN            = 28,   // GetData only: 1 when every instructor has kHonorsMinHolders grades
        DATA_GRADE_HOLDERS          = 30,   // GetData(30 + Instructor): how many players hold that Passing Grade
        DATA_CLASSROOM_GATE         = 40,   // SetData(40 + Classroom, 0 closed / 1 open): S11's detention gate
                                            // control; GetData: 1 open, 0 closed, 2 not loaded
    };
    std::uint32_t constexpr DataGradeHolders(Instructor i) { return DATA_GRADE_HOLDERS + std::uint32_t(i); }
    std::uint32_t constexpr DataClassroomGate(Classroom c) { return DATA_CLASSROOM_GATE + std::uint32_t(c); }

    // SetGuidData / GetGuidData ids. ObjectData ids for units that are never summoned twice (cpp-scripts.md, the
    // ObjectData pitfall): the bosses and stock gameobjects. Never the adds, stalkers, copies or examiners.
    enum ScholomanceObjects : std::uint32_t
    {
        DATA_JANDICE_GUID           = 100,
        DATA_RATTLEGORE_GUID        = 101,
        DATA_MARDUK_GUID            = 102,
        DATA_VECTUS_GUID            = 103,
        DATA_RAS_GUID               = 104,
        DATA_MALICIA_GUID           = 105,
        DATA_KRASTINOV_GUID         = 106,
        DATA_POLKELT_GUID           = 107,
        DATA_RAVENIAN_GUID          = 108,
        DATA_ALEXEI_GUID            = 109,
        DATA_ILLUCIA_GUID           = 110,
        DATA_GANDLING_GUID          = 111,

        DATA_VIEWING_ROOM_DOOR_GUID = 120,
        DATA_GANDLING_ENTRANCE_GUID = 121,
        DATA_EMBALMING_FLUID_GUID   = 122,
        DATA_CLASSROOM_GATE_GUID    = 130,  // 130 + Classroom: the six Gandling gates (GetGuidData)

        // SetGuidData(150 + Instructor, player): award that instructor's Passing Grade to `player` (heroic; the
        // instructor's GradeWatch at its death, ScholomanceKit.h). GetGuidData: empty.
        DATA_PASSING_GRADE          = 150,
        // SetGuidData(160 + Classroom, player | Empty): S11 records who is detained in a classroom; GetGuidData reads
        // it back. Cleared on every Gandling state change away from IN_PROGRESS.
        DATA_DETAINED               = 160,
    };
    std::uint32_t constexpr DataClassroomGateGuid(Classroom c) { return DATA_CLASSROOM_GATE_GUID + std::uint32_t(c); }
    std::uint32_t constexpr DataPassingGrade(Instructor i) { return DATA_PASSING_GRADE + std::uint32_t(i); }
    std::uint32_t constexpr DataDetained(Classroom c) { return DATA_DETAINED + std::uint32_t(c); }

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum ScholomanceCreatures : std::uint32_t
    {
        // bosses (stock entries; script names bound by apps/dbc-tools source/npcs/scholomance/<boss>.py)
        NPC_JANDICE                 = 10503,    // boss_jandice_barov_rework
        NPC_RATTLEGORE              = 11622,    // boss_rattlegore_rework
        NPC_MARDUK                  = 10433,    // boss_marduk_blackpool_rework
        NPC_VECTUS                  = 10432,    // boss_vectus_rework
        NPC_RAS                     = 10508,    // boss_ras_frostwhisper_rework
        NPC_MALICIA                 = 10505,    // boss_instructor_malicia_rework
        NPC_KRASTINOV               = 11261,    // boss_doctor_theolen_krastinov_rework (civilian, faction 21)
        NPC_POLKELT                 = 10901,    // boss_lorekeeper_polkelt_rework
        NPC_RAVENIAN                = 10507,    // boss_the_ravenian_rework
        NPC_ALEXEI                  = 10504,    // boss_lord_alexei_barov_rework
        NPC_ILLUCIA                 = 10502,    // boss_lady_illucia_barov_rework
        NPC_GANDLING                = 1853,     // boss_darkmaster_gandling_rework

        // stock units (kept stock; their AIs run on the stock instance name)
        NPC_KIRTONOS                = 10506,    // boss_kirtonos_the_herald, summoned by this instance
        NPC_KORMOK                  = 16118,    // boss_kormok
        NPC_SCHOLOMANCE_OCCULTIST   = 10472,    // npc_scholomance_occultist (Malicia's room trash)
        NPC_DARK_SHADE              = 11284,    // the Occultist's 30% form
        NPC_RISEN_GUARDIAN          = 11598,    // retired (the stock portal's summon; S11 drops it)
        NPC_ILLUSION_OF_JANDICE     = 11439,    // reused by S1 as the Shell Game copy
        NPC_SCHOLOMANCE_STUDENT     = 10475,    // reworked as props by S3
        NPC_RISEN_GUARD             = 10489,    // Alexei's stock formation members (S9 removes the formation)

        // boss kit (new entries, creature 300530-300579, ids.yaml reservation `scholomance`; each declared by its boss
        // WP in source/npcs/scholomance/<boss>.py; handoff section 3.3)
        NPC_SC_REFLECTION           = 300530,   // S1 Jandice's Reflection
        NPC_SC_LOOSE_PART           = 300531,   // S2 the loose part (bone pile)
        NPC_SC_UNFINISHED_CONSTRUCT = 300532,   // S2
        NPC_SC_GRADUATE             = 300533,   // S3
        NPC_SC_BLIZZARD_ANCHOR      = 300534,   // S4
        NPC_SC_ICE_TOMB             = 300535,   // S12 (hard mode)
        NPC_SC_MALICIAS_SHADE       = 300536,   // S5
        NPC_SC_LOOSE_SOUL           = 300537,   // S5
        NPC_SC_WORK_BENCH           = 300538,   // S6 (VehicleId 6, seat 441)
        NPC_SC_FAILED_PATIENT       = 300539,   // S6
        NPC_SC_UNSTABLE_SPECIMEN    = 300540,   // S7
        NPC_SC_ROOTED_SPECIMEN      = 300541,   // S7
        NPC_SC_MASTER_CORVANE       = 300542,   // S8
        NPC_SC_BAROV_FORTUNE        = 300543,   // S9
        NPC_SC_EXPELLED_STUDENT     = 300544,   // S11
        NPC_SC_RAVENIANS_ECHO       = 300545,   // S11 (detention, Vault of the Ravenian)
        NPC_SC_LESSON_STALKER       = 300546,   // S11: a solo lesson's owner (SoloLesson.h)
        NPC_SC_PORTAL_STALKER       = 300547,   // S11
        NPC_SC_EXAMINER_MALICIA     = 300548,   // S13 Graduate Examiners (300548-300554)
        NPC_SC_EXAMINER_KRASTINOV   = 300549,
        NPC_SC_EXAMINER_POLKELT     = 300550,
        NPC_SC_EXAMINER_RAVENIAN    = 300551,
        NPC_SC_EXAMINER_CORVANE     = 300552,
        NPC_SC_EXAMINER_ALEXEI      = 300553,
        NPC_SC_EXAMINER_ILLUCIA     = 300554,
        // 300555-300579 spare (ask the orchestrator)
    };

    // The twelve reworked boss entries (a heroic copy's GetEntry() is its base entry).
    constexpr bool IsScholoBossEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_JANDICE:
            case NPC_RATTLEGORE:
            case NPC_MARDUK:
            case NPC_VECTUS:
            case NPC_RAS:
            case NPC_MALICIA:
            case NPC_KRASTINOV:
            case NPC_POLKELT:
            case NPC_RAVENIAN:
            case NPC_ALEXEI:
            case NPC_ILLUCIA:
            case NPC_GANDLING:
                return true;
            default:
                return false;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum ScholomanceGameObjects : std::uint32_t
    {
        // stock (scholomance.h GameobjectIds and the DB-REPORT section 5)
        GO_BRAZIER_KIRTONOS         = 175564,   // its SmartAI starts Kirtonos (SetData(0, IN_PROGRESS))
        GO_GATE_KIRTONOS            = 175570,
        GO_VIEWING_ROOM_DOOR        = 175167,   // lock 1199, the Viewing Room Key 13873 from Rattlegore
        GO_GATE_GANDLING_ENTRANCE   = 177374,   // closes while Gandling fights
        GO_GATE_GANDLING_DOWN_NORTH = 177371,   // Classroom::ShadowVault (Illucia)
        GO_GATE_GANDLING_DOWN_EAST  = 177373,   // Classroom::BarovVault (Alexei)
        GO_GATE_GANDLING_DOWN_SOUTH = 177372,   // Classroom::RavenianVault
        GO_GATE_GANDLING_UP_NORTH   = 177376,   // Classroom::HallOfSecrets (Polkelt)
        GO_GATE_GANDLING_UP_EAST    = 177377,   // Classroom::HallOfTheDamned (Krastinov)
        GO_GATE_GANDLING_UP_SOUTH   = 177375,   // Classroom::Coven (Malicia)
        GO_EMBALMING_FLUID          = 175965,   // Frostwhisper's Embalming Fluid (stock chest, kept)
        GO_KRASTINOVS_WORK_BENCH    = 176561,   // the static stock bench (S6's vehicle unit 300538 sits on it)
        GO_DEED_TO_CAER_DARROW      = 176485,
        GO_ALCHEMY_LAB              = 177387,   // the stock focus beside the hard mode table
        GO_JOURNAL_OF_JANDICE       = 180794,   // spell 26096 on her death

        // new (gameobject 301150-301199, ids.yaml reservation `scholomance`; templates and spawns: S12 / S13)
        GO_SC_TORN_PAGE             = 301150,   // S12: 3 spawns at kKeepsakePages (heroic spawnMask 2)
        GO_SC_KEEPSAKE_BOOK         = 301151,   // S12: the empty book at kKeepsakeBook
        GO_SC_KEEPSAKE_BOOK_BOUND   = 301152,   // S12: the bound book (or a GO state of 301151)
        GO_SC_HONORS_PAPER          = 301153,   // S13: the honors program paper at kHonorsPaper
        GO_SC_ALCHEMY_TABLE         = 301154,   // S12: the clickable alchemy table that starts Ras's hard mode
                                                // (user ruling 2026-11-08, in place of the fluid's click)
        // 301155-301199 spare
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 206100-206399, ids.yaml reservation `scholomance`; declared in apps/dbc-tools
    // source/npcs/scholomance/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h. The kit-wide
    // 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h).
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 206100, 206399 };
    IdSlice constexpr kSpellsShared{ 206100, 206109 };          // KS / S11: detention teleport, return, lesson pass
                                                                // and fail (none declared yet)
    IdSlice constexpr kSpellsJandice{ 206110, 206129 };         // S1
    IdSlice constexpr kSpellsRattlegore{ 206130, 206149 };      // S2
    IdSlice constexpr kSpellsMardukVectus{ 206150, 206169 };    // S3
    IdSlice constexpr kSpellsRas{ 206170, 206189 };             // S4
    IdSlice constexpr kSpellsRasHardMode{ 206190, 206204 };     // S12
    IdSlice constexpr kSpellsMalicia{ 206205, 206224 };         // S5
    IdSlice constexpr kSpellsKrastinov{ 206225, 206249 };       // S6
    IdSlice constexpr kSpellsPolkelt{ 206250, 206269 };         // S7
    IdSlice constexpr kSpellsRavenian{ 206270, 206289 };        // S8
    IdSlice constexpr kSpellsAlexei{ 206290, 206314 };          // S9
    IdSlice constexpr kSpellsIllucia{ 206315, 206329 };         // S10
    IdSlice constexpr kSpellsGandling{ 206330, 206364 };        // S11
    IdSlice constexpr kSpellsGandlingHardMode{ 206365, 206384 }; // S13
    IdSlice constexpr kSpellsSpare{ 206385, 206399 };

    inline std::array<IdSlice, 15> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsJandice, kSpellsRattlegore, kSpellsMardukVectus, kSpellsRas, kSpellsRasHardMode,
        kSpellsMalicia, kSpellsKrastinov, kSpellsPolkelt, kSpellsRavenian, kSpellsAlexei, kSpellsIllucia,
        kSpellsGandling, kSpellsGandlingHardMode, kSpellsSpare,
    } };

    IdSlice constexpr kCreaturesReservation{ 300530, 300579 };
    IdSlice constexpr kGameObjectsReservation{ 301150, 301199 };

    // Stock spells the build specs keep or read (DD scales the kept ones on heroic; handoff section 3.6).
    enum ScholomanceStockSpells : std::uint32_t
    {
        SPELL_FROST_ARMOR           = 18100,    // Ras
        SPELL_BLAST_WAVE            = 17277,    // Vectus
        SPELL_VOLATILE_INFECTION    = 18149,    // Polkelt
        SPELL_DEFILING_AURA         = 17695,
        SPELL_CORRUPTION            = 18376,    // Malicia
        SPELL_SLOW                  = 13747,
        SPELL_UNHOLY_AURA           = 17467,    // Alexei
        SPELL_SHADOW_SHOCK          = 19460,
        SPELL_CURSE_OF_AGONY        = 18266,
        SPELL_STRIKE                = 18368,
        SPELL_SUMMON_JOURNAL        = 26096,    // Jandice's death: the journal GO 180794
        SPELL_SHADOW_PORTAL         = 17950,    // Gandling's stock detention cast (retired by S11)
        // The six stock detention landings (spell_target_position; the portal spells themselves are never cast by
        // the rework, S11 copies the points: kClassroomLandings)
        SPELL_SHADOW_PORTAL_UP_NORTH    = 17863,
        SPELL_SHADOW_PORTAL_UP_EAST     = 17939,
        SPELL_SHADOW_PORTAL_UP_SOUTH    = 17943,
        SPELL_SHADOW_PORTAL_DOWN_NORTH  = 17944,
        SPELL_SHADOW_PORTAL_DOWN_EAST   = 17946,
        SPELL_SHADOW_PORTAL_DOWN_SOUTH  = 17948,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // creature_text groups (SC "Text" tables). Texts are inserted by each boss WP's own SQL rev; stock lines stay.
    // ----------------------------------------------------------------------------------------------------------------
    enum JandiceTexts : std::uint8_t
    {
        EMOTE_JANDICE_JOURNAL           = 0,    // stock, death
        EMOTE_JANDICE_SHELL_GAME        = 1,
        EMOTE_JANDICE_SIGILS            = 2,
        EMOTE_JANDICE_BLOODLINES        = 3,
    };
    enum RattlegoreTexts : std::uint8_t
    {
        EMOTE_RATTLEGORE_PART_LOOSE     = 0,
        EMOTE_RATTLEGORE_ERUPTION       = 1,
        EMOTE_RATTLEGORE_SALVAGE        = 2,
    };
    enum VectusTexts : std::uint8_t
    {
        SAY_VECTUS_IDLE                 = 0,    // stock group 0: 7 lecture says plus one stray type 16 emote row
                                                // (DB-REPORT 0.7): S3 fixes the row or talks by id
        YELL_VECTUS_AGGRO               = 1,    // stock
        YELL_VECTUS_FLAMESTRIKE         = 2,
        YELL_VECTUS_GROUP_EXERCISE      = 3,
        YELL_VECTUS_POP_QUIZ            = 4,
        YELL_VECTUS_DOUBLE_PERIOD       = 5,    // heroic
    };
    enum MardukTexts : std::uint8_t
    {
        SAY_MARDUK_BETRAYED             = 0,    // stock 0 and 1: Dawn's Gambit
        SAY_MARDUK_BETRAYED_2           = 1,
        EMOTE_MARDUK_EBON_SWEEP         = 2,
        EMOTE_MARDUK_WHIRLWIND          = 3,    // heroic
    };
    enum RasTexts : std::uint8_t
    {
        YELL_RAS_THIS_CANNOT_BE         = 0,    // stock (Boon of Life, the hard mode transition)
        EMOTE_RAS_FROST_MARK            = 1,
        EMOTE_RAS_SIPHON_WARMTH         = 2,    // hard mode
    };
    enum MaliciaTexts : std::uint8_t
    {
        EMOTE_MALICIA_SOUL_DRAIN        = 0,
        EMOTE_MALICIA_DRAIN_ALL         = 1,
        EMOTE_MALICIA_CALL_A_STUDENT    = 2,
        EMOTE_MALICIA_SOULSTORM         = 3,
    };
    enum KrastinovTexts : std::uint8_t
    {
        EMOTE_KRASTINOV_FRENZY_OOC      = 0,    // stock
        YELL_KRASTINOV_AGGRO            = 1,    // stock
        YELL_KRASTINOV_SUCCESS          = 2,    // stock (on kill; also a successful operation)
        YELL_KRASTINOV_DEATH            = 3,    // stock
        EMOTE_KRASTINOV_HANDS           = 4,    // stock frenzy, moved to the hands graft
        EMOTE_KRASTINOV_STRAPS          = 5,
        EMOTE_KRASTINOV_EYES            = 6,
        EMOTE_KRASTINOV_HEART           = 7,
    };
    enum PolkeltTexts : std::uint8_t
    {
        EMOTE_POLKELT_RAISE             = 0,
        YELL_POLKELT_AGGRO              = 1,
        YELL_POLKELT_DEATH              = 2,
    };
    enum RavenianTexts : std::uint8_t
    {
        EMOTE_RAVENIAN_TEARS_FREE       = 0,
    };
    enum CorvaneTexts : std::uint8_t
    {
        YELL_CORVANE_AGGRO              = 0,
        YELL_CORVANE_TRAMPLE            = 1,
        YELL_CORVANE_SWEEP              = 2,
        YELL_CORVANE_SMASH              = 3,
        YELL_CORVANE_TRANSITION         = 4,
        YELL_CORVANE_DEATH              = 5,
        YELL_CORVANE_RAVENIAN_DIES      = 6,
    };
    enum AlexeiTexts : std::uint8_t
    {
        YELL_ALEXEI_AGGRO               = 0,
        YELL_ALEXEI_NO_RUNNING          = 1,
        YELL_ALEXEI_ASSEMBLY            = 2,
        YELL_ALEXEI_KEEP_DISTANCE       = 3,
        YELL_ALEXEI_CORNER              = 4,
        YELL_ALEXEI_LINE_UP             = 5,    // heroic
        YELL_ALEXEI_DESKS               = 6,    // heroic
        EMOTE_ALEXEI_DEMERIT            = 7,
        YELL_ALEXEI_DEATH               = 8,
    };
    enum IlluciaTexts : std::uint8_t
    {
        YELL_ILLUCIA_AGGRO              = 0,
        YELL_ILLUCIA_FORESIGHT          = 1,
        EMOTE_ILLUCIA_FEAR              = 2,
        YELL_ILLUCIA_DEATH              = 3,
    };
    enum GandlingTexts : std::uint8_t
    {
        YELL_GANDLING_SCHOOL_IN_SESSION = 0,    // stock: the sixth instructor dies (the instance says it)
        YELL_GANDLING_DETENTION         = 1,
        EMOTE_GANDLING_PORTAL_VOLLEY    = 2,
        EMOTE_GANDLING_TRANSFER         = 3,
        YELL_GANDLING_HARD_MODE         = 4,
        YELL_GANDLING_FINAL_EXAM        = 5,
        YELL_GANDLING_DEATH             = 6,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (handoff section 3.8; scholomance-build.NAVMESH-REPORT.md). Axes: +x north, +y west.
    // ----------------------------------------------------------------------------------------------------------------
    struct Point3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
    };

    struct Point4
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        float o = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
        constexpr Point3 P3() const { return { x, y, z }; }
    };

    // Boss spawns [db] (creature rows).
    Point4 constexpr kJandiceSpawn{ 268.223f, 73.633f, 95.9245f, 1.64061f };
    Point4 constexpr kRattlegoreSpawn{ 137.145f, 171.676f, 95.9664f, 3.28122f };
    Point4 constexpr kVectusSpawn{ 143.481f, 99.0964f, 104.659f, 3.26377f };
    Point4 constexpr kMardukSpawn{ 150.368f, 116.22f, 104.661f, 3.83972f };
    Point4 constexpr kRasSpawn{ -25.1079f, 141.284f, 83.9083f, 0.034907f };
    Point4 constexpr kMaliciaSpawn{ 86.6634f, -1.96039f, 85.3117f, 0.017453f };
    Point4 constexpr kKrastinovSpawn{ 182.246f, -95.4371f, 85.3117f, 4.72984f };
    Point4 constexpr kPolkeltSpawn{ 274.877f, 1.33366f, 85.3117f, 3.22886f };
    Point4 constexpr kRavenianSpawn{ 103.305f, -1.67752f, 75.2183f, 6.17846f };
    Point4 constexpr kAlexeiSpawn{ 178.724f, -91.0232f, 70.8568f, 1.64061f };
    Point4 constexpr kIlluciaSpawn{ 265.956f, 0.903429f, 75.3334f, 3.07178f };
    Point4 constexpr kGandlingSpawn{ 180.771f, -5.4286f, 75.5702f, 1.29154f };

    // Kirtonos the Herald's summon point (stock instance_scholomance.cpp KirtonosSpawn, copied).
    Point4 constexpr kKirtonosSpawn{ 315.028f, 70.5385f, 102.15f, 0.385971f };

    // The classrooms [db]: the Gandling gate of each, its stock portal spell and the spell's landing point
    // (spell_target_position: each lands on the room's instructor spawn).
    inline std::array<std::uint32_t, kClassroomCount> constexpr kClassroomGates{ {
        GO_GATE_GANDLING_DOWN_NORTH, GO_GATE_GANDLING_DOWN_EAST, GO_GATE_GANDLING_DOWN_SOUTH,
        GO_GATE_GANDLING_UP_NORTH, GO_GATE_GANDLING_UP_EAST, GO_GATE_GANDLING_UP_SOUTH } };
    inline std::array<std::uint32_t, kClassroomCount> constexpr kClassroomPortalSpells{ {
        SPELL_SHADOW_PORTAL_DOWN_NORTH, SPELL_SHADOW_PORTAL_DOWN_EAST, SPELL_SHADOW_PORTAL_DOWN_SOUTH,
        SPELL_SHADOW_PORTAL_UP_NORTH, SPELL_SHADOW_PORTAL_UP_EAST, SPELL_SHADOW_PORTAL_UP_SOUTH } };
    inline std::array<Point4, kClassroomCount> constexpr kClassroomLandings{ {
        { 266.774f, 0.886003f, 75.2501f, 3.07178f },        // 17944 the Shadow Vault
        { 179.141f, -91.118f, 71.5433f, 1.64061f },         // 17946 the Barov Family Vault
        { 103.305f, -1.67752f, 75.2183f, 6.17846f },        // 17948 the Vault of the Ravenian
        { 274.877f, 1.33366f, 85.3117f, 3.22886f },         // 17863 the Hall of Secrets
        { 182.423f, -95.8264f, 85.2284f, 1.58984f },        // 17939 the Hall of the Damned
        { 83.2952f, -1.70237f, 85.2284f, 0.0174533f } } };  // 17943 the Coven
    inline std::array<Point3, kClassroomCount> constexpr kClassroomGatePoints{ {
        { 204.326f, 0.011124f, 76.1678f }, { 181.054f, -21.3466f, 76.1317f }, { 159.746f, -0.767021f, 76.1678f },
        { 209.065f, 0.011116f, 88.9113f }, { 181.244f, -29.1116f, 88.9104f }, { 151.773f, -0.602287f, 88.9039f } } };
    Point3 constexpr kGandlingEntranceGate{ 179.137f, 29.0423f, 88.8537f };
    Point3 constexpr kViewingRoomDoor{ 174.378f, 77.9398f, 104.802f };

    constexpr std::uint32_t ClassroomGate(Classroom c) { return kClassroomGates[std::size_t(c)]; }

    constexpr std::optional<Classroom> ClassroomOfGate(std::uint32_t goEntry)
    {
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            if (kClassroomGates[i] == goEntry)
                return Classroom(i);
        return std::nullopt;
    }

    // --- Jandice Barov's east aisle (S1) -----------------------------------------------------------------------------
    // The hall is four aisles split by dividers; hers is 21 yd wide, not 30 (handoff section 7 #12).
    FrameRect constexpr kJandiceAisle{ { 228.0f, 84.0f }, 0.f, 55.5f, 21.0f };     // x 228-283.5, y 84-105, z 95.9
    float constexpr kJandiceFloorZ = 95.9f;
    // Heroic sigil grid, 8 points of 8 yd (97.5% of the frame); a ninth point burns the alcove if needed.
    inline std::array<Vec2, 8> constexpr kJandiceSigilGrid{ { { 234.9f, 99.8f }, { 248.8f, 99.8f }, { 262.7f, 99.8f },
        { 276.6f, 99.8f }, { 234.9f, 89.2f }, { 248.8f, 89.2f }, { 262.7f, 89.2f }, { 276.6f, 89.2f } } };
    Vec2 constexpr kJandiceAlcoveSigil{ 268.0f, 74.0f };

    // --- Rattlegore's Great Ossuary (S2) -----------------------------------------------------------------------------
    FrameRect constexpr kOssuaryFloor{ { 96.0f, 150.0f }, 0.f, 69.0f, 47.5f };    // z 93-95
    float constexpr kOssuaryFloorZ = 94.0f;
    // Unfinished Construct spots (NW, SW, NE, SE), each 2 yd disc on the floor.
    inline std::array<Point3, 4> constexpr kConstructSpots{ { { 158.0f, 192.0f, 93.5f }, { 103.0f, 192.0f, 93.5f },
        { 158.0f, 155.0f, 93.5f }, { 103.0f, 155.0f, 93.5f } } };
    Point3 constexpr kOssuaryStairFoot{ 151.0f, 171.0f, 94.0f };   // the stair up to the z 109.6 hatchling floor

    // --- The Viewing Room: Marduk and Vectus (S3) --------------------------------------------------------------------
    FrameRect constexpr kViewingRoomHall{ { 89.5f, 59.5f }, 0.f, 41.5f, 62.5f };  // the student hall, z 97-102
    Point3 constexpr kVectusStep{ 141.75f, 98.75f, 104.3f };       // the one floor step that reaches his lectern
    // A group stack center and its 9 drill circles (6 yd, disjoint, 7 yd off the group).
    Vec2 constexpr kViewingStackCenter{ 128.0f, 100.0f };
    inline std::array<Vec2, 9> constexpr kViewingDrillCircles{ { { 113.0f, 100.0f }, { 119.0f, 88.0f },
        { 119.0f, 112.0f }, { 134.0f, 114.0f }, { 130.0f, 82.0f }, { 143.0f, 85.0f }, { 146.0f, 112.0f },
        { 107.0f, 89.0f }, { 107.0f, 111.0f } } };

    // --- Ras Frostwhisper's study (S4, S12) --------------------------------------------------------------------------
    FrameRect constexpr kRasStudy{ { -55.0f, 121.0f }, 0.f, 35.0f, 28.0f };       // z 83.6-84; desk block inside
    FrameRect constexpr kRasStudyAndHall{ { -52.0f, 126.0f }, 0.f, 66.0f, 23.0f }; // the band open to x 14
    Point3 constexpr kRasDeskCenter{ -32.7f, 141.5f, 83.8f };
    Point4 constexpr kEmbalmingFluid{ -17.8299f, 124.581f, 84.8528f, 1.53589f };  // [db] GO 175965 (kept stock)
    std::uint32_t constexpr kRasPatrolPathId = 488500;              // stock, kept out of combat (S4)

    // Ras's keepsake (user ruling 2026-11-08, handoff section 10: measured in game, exact). Pages in any order.
    std::size_t constexpr kKeepsakePageCount = 3;
    inline std::array<Point4, kKeepsakePageCount> constexpr kKeepsakePages{ {
        { 233.51549f, 4.6665864f, 116.66063f, 2.3726962f },     // page 1: the z 115.8 floor over the study
        { 211.28065f, 174.21268f, 109.67556f, 5.677647f },      // page 2: the z 110 hall (section A)
        { 152.4498f, 109.95338f, 105.6674f, 4.173605f } } };    // page 3: the Viewing Room (section B)
    Point4 constexpr kKeepsakeBook{ 42.15418f, 121.35609f, 83.54561f, 4.7194448f };     // the lab hall
    // The hard mode start: a clickable alchemy table (GO_SC_ALCHEMY_TABLE), beside the stock Alchemy Lab 177387.
    Point4 constexpr kHardModeTable{ 41.380466f, 161.82669f, 86.786736f, 0.59217954f };

    // --- The Coven: Instructor Malicia (S5) --------------------------------------------------------------------------
    FrameRect constexpr kCovenFloor{ { 90.0f, -10.5f }, 0.f, 47.0f, 19.0f };      // z 85
    float constexpr kCovenShadeMinX = 102.0f;                       // shades rise at x 102-112, full width
    float constexpr kCovenShadeMaxX = 112.0f;

    // --- Krastinov's room, the Hall of the Damned (S6) ---------------------------------------------------------------
    FrameRect constexpr kKrastinovHall{ { 170.0f, -92.0f }, 0.f, 21.5f, 50.0f };  // z 85
    Point4 constexpr kWorkBenchGo{ 182.5f, -100.1f, 85.2f, 1.59f };                // [db] GO 176561
    Point3 constexpr kFailedPatientRise{ 166.0f, -86.0f, 85.4f };  // the south alcove, 21.7 yd from the bench

    // --- The Hall of Secrets: Lorekeeper Polkelt (S7) ----------------------------------------------------------------
    FrameRect constexpr kHallOfSecrets{ { 223.0f, -10.0f }, 0.f, 48.5f, 21.0f };   // z 85
    inline std::array<Point3, 3> constexpr kRootedSpecimenSpots{ { { 236.0f, -6.0f, 85.1f }, { 249.0f, 6.0f, 85.1f },
        { 262.0f, -5.0f, 85.1f } } };

    // --- The Vault of the Ravenian (S8) ------------------------------------------------------------------------------
    FrameRect constexpr kRavenianVault{ { 92.0f, -11.5f }, 0.f, 58.0f, 19.5f };    // z 74.5-76 (the central band)
    FrameRect constexpr kRavenianNorthHall{ { 128.0f, -18.0f }, 0.f, 22.0f, 34.0f };
    // Corvane's perch: on top of the block at (108.6, 13.8), x 107-111, y 7-21; no navmesh, top height unknown
    // (read it in game with .gps; guessed z 78 to 81). Second choice: the block at (123.1, 10.8).
    Vec2 constexpr kCorvanePerch{ 108.6f, 13.8f };
    // Corvane's landing, at least 15 yd from the Ravenian's fighting spot: recommended, farther, nearer.
    inline std::array<Point3, 3> constexpr kCorvaneLandings{ { { 128.0f, -1.0f, 75.4f }, { 140.0f, -1.0f, 75.4f },
        { 122.0f, 0.0f, 75.4f } } };
    // User 2026-11-08 (handoff section 10): a seat "right behind the Ravenian" (his spawn is (103.3, -1.7)), at the
    // vault's west end. Whose seat it is (Corvane sitting before he takes his perch, or the Ravenian himself) is
    // confirmed with the user before S8 uses it. The user's first point (175.8, -14.0) was on Gandling's study floor.
    Point4 constexpr kRavenianUserSpot{ 91.4206f, -0.7772341f, 75.558846f, 6.282406f };

    // --- The Barov Family Vault: Lord Alexei Barov (S9) --------------------------------------------------------------
    FrameRect constexpr kBarovVault{ { 168.0f, -93.0f }, 0.f, 29.0f, 58.0f };     // z 72 (east) to 75 (gate side)
    // Out of bounds thirds along y (gate third, middle, Alexei's third): [yMin, yMax].
    inline std::array<std::array<float, 2>, 3> constexpr kBarovThirdsY{ { { -53.5f, -34.0f }, { -73.5f, -53.5f },
        { -94.0f, -73.5f } } };
    float constexpr kBarovLaneMinX = 186.0f;                        // the north lane, 11 yd wide, full length
    float constexpr kBarovLaneMaxX = 197.0f;
    inline std::array<Vec2, 5> constexpr kBarovDesks{ { { 192.5f, -45.0f }, { 192.5f, -53.0f }, { 192.5f, -61.0f },
        { 192.5f, -69.0f }, { 192.5f, -77.0f } } };
    Point4 constexpr kDeedToCaerDarrow{ 185.3f, -90.6f, 72.6f, -1.03f };          // [db] GO 176485

    // --- The Shadow Vault: Lady Illucia Barov (S10) ------------------------------------------------------------------
    FrameRect constexpr kShadowVaultHall{ { 211.0f, -8.0f }, 0.f, 40.0f, 17.0f };  // z 73-75.7
    FrameRect constexpr kIlluciaInnerRoom{ { 258.5f, -6.0f }, 0.f, 14.0f, 14.0f };
    Point3 constexpr kIlluciaHallPoint{ 243.0f, 0.5f, 74.6f };     // handoff section 7 #14: she steps out to here

    // --- The Headmaster's Study: Darkmaster Gandling (S11, S13) ------------------------------------------------------
    FrameRect constexpr kStudyFloor{ { 162.0f, -20.0f }, 0.f, 38.0f, 39.0f };     // z 75.6, no pillars
    float constexpr kStudyFloorZ = 75.6f;
    // Portal points on the room edge (1.5 to 2.5 yd inside the walls; gate thresholds and the stair block clear).
    // For six, drop #2 and #4 (indexes 1, 3) or #7 and #8 (indexes 6, 7).
    inline std::array<Vec2, 8> constexpr kStudyPortalPoints{ { { 198.0f, -12.0f }, { 198.0f, 12.0f },
        { 163.5f, -12.0f }, { 163.5f, 12.0f }, { 172.0f, -18.5f }, { 190.0f, -18.5f }, { 168.0f, 17.0f },
        { 192.0f, 17.0f } } };
    // The honors program paper (S13) on the z 115.8 floor over the study, beside "The Birth of the Lich King"; the
    // route up is untraced (handoff section 7 #17: check in game). Option nearer the opening: kHonorsPaperAlt.
    Point3 constexpr kHonorsPaper{ 171.0f, 8.0f, 116.0f };
    Point3 constexpr kHonorsPaperAlt{ 166.5f, -1.0f, 115.8f };

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (handoff section 3.8 leash circles, user ruling on section 7 #8: the boss holds at the edge and evades
    // when no target has been inside for 10 s; no player grips). Each is a circle with the room's z band, so the
    // stacked rooms stay apart. ScholomanceKit.h LeashOptions() builds the guard's options.
    // ----------------------------------------------------------------------------------------------------------------
    inline Arena CircleArena(Vec2 center, float radius, float zMin, float zMax)
    {
        return Arena(ArenaRegion::Circle(center, radius, zMin, zMax));
    }

    // The aisle and both end strips (and her alcove); z under the z 110 floor above.
    inline Arena JandiceArena() { return CircleArena({ 256.0f, 94.5f }, 30.f, 93.0f, 101.0f); }
    // z <= 98: the north stair foot (151, 171) is inside the circle; above z 98 he would be on the stair.
    inline Arena RattlegoreArena() { return CircleArena({ 130.5f, 173.5f }, 35.f, 85.0f, 98.0f); }
    // The tiered student hall and the stage; both gates and the door are outside.
    inline Arena ViewingRoomArena() { return CircleArena({ 128.0f, 95.0f }, 32.f, 95.0f, 108.0f); }
    // The study and the west part of the Kormok hall (no door between them).
    inline Arena RasArena() { return CircleArena({ -35.0f, 138.0f }, 28.f, 81.0f, 89.0f); }
    // The Coven, over the Vault of the Ravenian (z 85 over 75); the slab rises to z 91. Radius 32.5, not the report's
    // 28: her apse runs back to x 80 (32 yd out) and the stock Coven landing (17943, x 83.3) must be inside; the gate
    // corridor (x 146 on) stays out.
    inline Arena MaliciaArena() { return CircleArena({ 112.0f, -1.0f }, 32.5f, 83.0f, 93.0f); }
    // The Hall of the Damned, over the Barov Family Vault.
    inline Arena KrastinovArena() { return CircleArena({ 181.0f, -70.0f }, 30.f, 83.0f, 91.0f); }
    // The Hall of Secrets, over the Shadow Vault.
    inline Arena PolkeltArena() { return CircleArena({ 250.0f, 0.5f }, 32.f, 83.0f, 91.0f); }
    // The Vault of the Ravenian (under the Coven; Corvane's perch block top is about z 78 to 81).
    inline Arena RavenianArena() { return CircleArena({ 122.0f, -1.0f }, 32.f, 72.0f, 82.0f); }
    // The Barov Family Vault: two tiers (72, 75) and the central pit (down to about z 66).
    inline Arena AlexeiArena() { return CircleArena({ 182.5f, -63.0f }, 33.f, 64.0f, 79.0f); }
    // The Shadow Vault's hall and Illucia's inner room (the fight belongs in the hall, handoff section 7 #14).
    inline Arena IlluciaArena() { return CircleArena({ 243.0f, 0.5f }, 32.f, 71.0f, 79.0f); }
    // The study and the stair block up to z 82 (the z 89 ring and the west gate are outside); the three lower gates
    // lie inside the circle, so they stay shut while he fights (the instance's door data).
    inline Arena GandlingArena() { return CircleArena({ 181.0f, -0.5f }, 25.f, 73.0f, 84.0f); }

    // The arena of a boss state (S3's encounter: the Viewing Room).
    inline Arena ArenaFor(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_JANDICE:       return JandiceArena();
            case BOSS_RATTLEGORE:    return RattlegoreArena();
            case BOSS_MARDUK_VECTUS: return ViewingRoomArena();
            case BOSS_GANDLING:      return GandlingArena();
            case BOSS_RAS:           return RasArena();
            case BOSS_MALICIA:       return MaliciaArena();
            case BOSS_KRASTINOV:     return KrastinovArena();
            case BOSS_POLKELT:       return PolkeltArena();
            case BOSS_RAVENIAN:      return RavenianArena();
            case BOSS_ALEXEI:        return AlexeiArena();
            case BOSS_ILLUCIA:       return IlluciaArena();
            default:                 return Arena();
        }
    }

    // A classroom's arena (detention, S11; the gauntlet, S13): its instructor's.
    inline Arena ClassroomArena(Classroom c)
    {
        return ArenaFor(InstructorBoss(ClassroomInstructor(c)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gandling's reveal (handoff section 7 #11): by the six instructor boss states, not the stock raw counter
    // ----------------------------------------------------------------------------------------------------------------
    inline std::uint32_t InstructorsDone(std::array<std::uint32_t, kBossCount> const& states)
    {
        std::uint32_t done = 0;
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            if (states[InstructorBoss(Instructor(i))] == DungeonKit::State::Done)
                ++done;
        return done;
    }

    inline bool GandlingRevealed(std::array<std::uint32_t, kBossCount> const& states)
    {
        return InstructorsDone(states) == kInstructorCount;
    }

    // Gandling's faction while hidden (stock: 35, friendly; invisible too) and once revealed (stock: 21).
    std::uint32_t constexpr kGandlingHiddenFaction = 35;
    std::uint32_t constexpr kGandlingRevealedFaction = 21;

    // ----------------------------------------------------------------------------------------------------------------
    // Ras's keepsake and the two hard modes (rulings 9, 11, 22; handoff section 10)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kKeepsakeAllPages = (1u << kKeepsakePageCount) - 1;

    constexpr std::uint32_t KeepsakePageCount(std::uint32_t mask)
    {
        std::uint32_t n = 0;
        for (std::size_t i = 0; i < kKeepsakePageCount; ++i)
            if (mask & (1u << i))
                ++n;
        return n;
    }

    // A page counts on heroic only (the pages spawn on heroic), once each, and never after Ras is dead.
    constexpr bool KeepsakePageAllowed(std::uint32_t page, bool heroic, std::uint32_t rasState)
    {
        return heroic && page < kKeepsakePageCount && rasState != DungeonKit::State::Done;
    }

    // The book binds with all three pages, on heroic, before Ras dies.
    constexpr bool KeepsakeBindAllowed(std::uint32_t mask, bool heroic, std::uint32_t rasState)
    {
        return heroic && (mask & kKeepsakeAllPages) == kKeepsakeAllPages && rasState != DungeonKit::State::Done;
    }

    // SetData(DATA_RAS_HARD_MODE, value): lit only with the bound book, on heroic, while Ras neither fights nor is
    // dead; cleared any time before his death (a wipe of the hard mode fight keeps it lit: the group tries again).
    constexpr bool RasHardModeChangeAllowed(std::uint32_t value, bool bound, bool heroic, std::uint32_t rasState)
    {
        if (rasState == DungeonKit::State::Done)
            return false;
        if (!value)
            return true;
        return bound && heroic && rasState != DungeonKit::State::InProgress;
    }

    // SetData(DATA_GANDLING_HARD_MODE, value): signed only with the honors program open, on heroic, with Gandling
    // revealed and neither fighting nor dead; cleared any time before his death.
    constexpr bool GandlingHardModeChangeAllowed(std::uint32_t value, bool honorsOpen, bool heroic, bool revealed,
        std::uint32_t gandlingState)
    {
        if (gandlingState == DungeonKit::State::Done)
            return false;
        if (!value)
            return true;
        return honorsOpen && heroic && revealed && gandlingState != DungeonKit::State::InProgress;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Passing Grades (ruling 22, handoff section 7 #18): per player, a bit per instructor; saved in instance data, so
    // a death, a release or a logout never loses one. The honors program opens when every instructor has grades from
    // at least kHonorsMinHolders players. Players are stored by their guid counter (the low guid).
    // ----------------------------------------------------------------------------------------------------------------
    std::size_t constexpr kGradeSlots = 10;             // room for group changes (5-man; anyone who earned one)
    std::uint32_t constexpr kHonorsMinHolders = 3;      // "3 of 5" (round 4)
    std::uint32_t constexpr kAllGradesMask = (1u << kInstructorCount) - 1;

    class PassingGrades
    {
    public:
        struct Slot
        {
            std::uint32_t player = 0;   // 0: free
            std::uint32_t mask = 0;     // bit per Instructor
        };

        // Awards `i`'s grade to `player` (non-zero). False when the player already holds it, or every slot is taken
        // by other players (the first kGradeSlots players to earn a grade keep theirs).
        bool Award(std::uint32_t player, Instructor i)
        {
            if (!player)
                return false;
            std::uint32_t const bit = 1u << std::uint32_t(i);
            Slot* free = nullptr;
            for (Slot& s : _slots)
            {
                if (s.player == player)
                {
                    if (s.mask & bit)
                        return false;
                    s.mask |= bit;
                    return true;
                }
                if (!s.player && !free)
                    free = &s;
            }
            if (!free)
                return false;
            free->player = player;
            free->mask = bit;
            return true;
        }

        bool Has(std::uint32_t player, Instructor i) const
        {
            return player && (MaskOf(player) & (1u << std::uint32_t(i)));
        }

        std::uint32_t MaskOf(std::uint32_t player) const
        {
            for (Slot const& s : _slots)
                if (player && s.player == player)
                    return s.mask;
            return 0;
        }

        std::uint32_t Holders(Instructor i) const
        {
            std::uint32_t n = 0;
            for (Slot const& s : _slots)
                if (s.player && (s.mask & (1u << std::uint32_t(i))))
                    ++n;
            return n;
        }

        bool HonorsOpen(std::uint32_t minHolders = kHonorsMinHolders) const
        {
            for (std::size_t i = 0; i < kInstructorCount; ++i)
                if (Holders(Instructor(i)) < minHolders)
                    return false;
            return true;
        }

        void Clear() { _slots = {}; }
        std::array<Slot, kGradeSlots> const& Slots() const { return _slots; }

        // Save fields: player, mask per slot (2 x kGradeSlots).
        void Write(std::vector<std::uint32_t>& out) const
        {
            for (Slot const& s : _slots)
            {
                out.push_back(s.player);
                out.push_back(s.player ? s.mask & kAllGradesMask : 0);
            }
        }

        // Reads Write's fields from `in` at `at` (missing fields: free slots); a slot without a player or a grade is
        // dropped, a player listed twice keeps the first slot, unknown bits are cleared.
        void Read(std::vector<std::uint32_t> const& in, std::size_t at)
        {
            Clear();
            std::size_t next = 0;
            for (std::size_t i = 0; i < kGradeSlots; ++i)
            {
                std::size_t const p = at + 2 * i;
                std::uint32_t const player = p < in.size() ? in[p] : 0;
                std::uint32_t const mask = p + 1 < in.size() ? in[p + 1] & kAllGradesMask : 0;
                if (!player || !mask || MaskOf(player))
                    continue;
                _slots[next++] = { player, mask };
            }
        }

    private:
        std::array<Slot, kGradeSlots> _slots{};
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string: header "SC", the 11 boss states, then the extras below. A stock save
    // (instance_scholomance: no header, no boss states, just "<kirtonos> <miniBosses>") is still read (handoff section
    // 3.2 item 11): Kirtonos's state comes over (IN_PROGRESS / FAIL back to NOT_STARTED, fixing the stock reload bug),
    // a count of 6 marks the six instructors DONE, and the instance's completed-encounter mask (set before Load, from
    // the DBC bits) fills in every boss state it records.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "SC";

    enum SaveExtra : std::size_t
    {
        EXTRA_KIRTONOS              = 0,
        EXTRA_KEEPSAKE_PAGES        = 1,
        EXTRA_KEEPSAKE_BOUND        = 2,
        EXTRA_RAS_HARD_MODE         = 3,
        EXTRA_RAS_HARD_MODE_KILLED  = 4,
        EXTRA_GANDLING_HARD_MODE    = 5,
        EXTRA_GANDLING_HARD_MODE_KILLED = 6,
        EXTRA_GRADES                = 7,    // kGradeSlots x (player, mask)
    };
    std::size_t constexpr kSaveExtraCount = EXTRA_GRADES + 2 * kGradeSlots;

    struct ScholoSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        std::uint32_t kirtonos = DungeonKit::State::NotStarted;
        std::uint32_t keepsakePages = 0;
        std::uint32_t keepsakeBound = 0;
        std::uint32_t rasHardMode = 0;
        std::uint32_t rasHardModeKilled = 0;
        std::uint32_t gandlingHardMode = 0;
        std::uint32_t gandlingHardModeKilled = 0;
        PassingGrades grades;
    };

    // Kirtonos's stored state (DATA_KIRTONOS_THE_HERALD): a state that cannot survive a reload (IN_PROGRESS, FAIL,
    // SPECIAL, junk) goes back to NOT_STARTED, so the brazier summons him again (the stock reader kept 1 and blocked
    // it).
    inline std::uint32_t SanitizeKirtonos(std::uint32_t v)
    {
        return DungeonKit::SanitizeLoadedState(v);
    }

    inline std::string FormatScholoSave(ScholoSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras{ s.kirtonos, s.keepsakePages, s.keepsakeBound, s.rasHardMode,
            s.rasHardModeKilled, s.gandlingHardMode, s.gandlingHardModeKilled };
        s.grades.Write(extras);
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The DBC encounter bits of map 289 (DungeonEncounter 451-463, Bit 0..12; the completed-encounter mask) and the
    // boss state each completes. Marduk (bit 3) and Vectus (bit 4) complete BOSS_MARDUK_VECTUS together.
    std::uint32_t constexpr kEncounterBitKirtonos = 0;
    std::uint32_t constexpr kEncounterBitMarduk = 3;
    std::uint32_t constexpr kEncounterBitVectus = 4;

    // The boss states a completed-encounter mask records (DONE), OR-ed into `states`; Kirtonos's bit sets `kirtonos`.
    inline void ApplyEncounterMask(std::uint32_t mask, std::array<std::uint32_t, kBossCount>& states,
        std::uint32_t& kirtonos)
    {
        auto done = [mask](std::uint32_t bit) { return (mask & (1u << bit)) != 0; };
        std::array<std::pair<std::uint32_t, std::uint32_t>, 10> constexpr single{ {
            { 1, BOSS_JANDICE }, { 2, BOSS_RATTLEGORE }, { 5, BOSS_RAS }, { 6, BOSS_MALICIA }, { 7, BOSS_KRASTINOV },
            { 8, BOSS_POLKELT }, { 9, BOSS_RAVENIAN }, { 10, BOSS_ALEXEI }, { 11, BOSS_ILLUCIA }, { 12, BOSS_GANDLING },
        } };
        for (auto const& [bit, boss] : single)
            if (done(bit))
                states[boss] = DungeonKit::State::Done;
        if (done(kEncounterBitMarduk) && done(kEncounterBitVectus))
            states[BOSS_MARDUK_VECTUS] = DungeonKit::State::Done;
        if (done(kEncounterBitKirtonos))
            kirtonos = DungeonKit::State::Done;
    }

    // The stock "<kirtonos> <miniBosses>" (instance_scholomance WriteSaveDataMore; both fields required).
    inline bool ReadStockSave(std::string const& in, std::uint32_t& kirtonos, std::uint32_t& miniBosses)
    {
        std::vector<std::uint32_t> fields;
        if (!DungeonKit::ReadSaveFields(in, "", 2, 2, fields))
            return false;
        kirtonos = SanitizeKirtonos(fields[0]);
        miniBosses = fields[1];
        return true;
    }

    // Reads this script's "S C" string, or a stock one; `encounterMask` is the instance's completed-encounter mask
    // (applied to a stock save only: an "S C" save carries its own states). False on anything else (ignored).
    // Loaded values are sanitized: states (SanitizeLoadedState), Kirtonos, the page mask, 0 / 1 flags, the grades.
    inline bool ParseScholoSave(std::string const& in, ScholoSave& out, std::uint32_t encounterMask = 0)
    {
        out = ScholoSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        DungeonKit::LegacySaveReader const legacy = [&stock, encounterMask](std::string const& s,
            DungeonKit::StateSave& o)
        {
            std::uint32_t kirtonos = 0;
            std::uint32_t miniBosses = 0;
            if (!ReadStockSave(s, kirtonos, miniBosses))
                return false;
            std::array<std::uint32_t, kBossCount> states{};
            if (miniBosses >= kInstructorCount)
                for (std::size_t i = 0; i < kInstructorCount; ++i)
                    states[InstructorBoss(Instructor(i))] = DungeonKit::State::Done;
            ApplyEncounterMask(encounterMask, states, kirtonos);
            o.states.assign(states.begin(), states.end());
            o.extras[EXTRA_KIRTONOS] = kirtonos;
            stock = true;
            return true;
        };
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw, legacy))
            return false;
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        out.kirtonos = SanitizeKirtonos(raw.extras[EXTRA_KIRTONOS]);
        if (stock)
            return true;
        out.keepsakePages = raw.extras[EXTRA_KEEPSAKE_PAGES] & kKeepsakeAllPages;
        out.keepsakeBound = raw.extras[EXTRA_KEEPSAKE_BOUND] ? 1 : 0;
        out.rasHardMode = raw.extras[EXTRA_RAS_HARD_MODE] ? 1 : 0;
        out.rasHardModeKilled = raw.extras[EXTRA_RAS_HARD_MODE_KILLED] ? 1 : 0;
        out.gandlingHardMode = raw.extras[EXTRA_GANDLING_HARD_MODE] ? 1 : 0;
        out.gandlingHardModeKilled = raw.extras[EXTRA_GANDLING_HARD_MODE_KILLED] ? 1 : 0;
        out.grades.Read(raw.extras, EXTRA_GRADES);
        return true;
    }
}

#endif
