/*
 * mod-dungeon-bosses, Gnomeregan (map 90): the shared ids, boss slots, data ids, the instance's pure rules (the
 * Workshop Door, the Final Chamber, the End NPCs, Crowd Pummeler's chest, the hard mode's console and arming, the
 * Finder sections), measured points, arenas, health and the save string of the Gnomeregan build
 * (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md sections 3.1 to 3.3, 3.6 to 3.8, 3.12, 7 and the user's
 * rulings in section 10; build spec docs/dungeons/gnomeregan-rework.md, "SP", whose later rulings win; the Pummeler
 * window ruling of section 10 wins over rulings 33, 35, 36 and 65).
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKit*.h), so every <Boss>Logic.h and its host test can
 * include it. Engine glue: GnomereganKit.h, the machines contract GnomereganMachines.h, and the shared kit (src/Kit/).
 *
 * Ownership: this file belongs to WP-S0 until it reports, then to the orchestrator. A boss WP keeps its spell ids
 * (inside its slice below), its script-local enums and its tuning (`namespace Tune`, section 3.5 rule 24) in its own
 * <Boss>Logic.h, and asks for a change here in its report ("Shared-file request").
 *
 * Mirrored stock code (AGENTS.md credit rule): none. The stock instance (src/server/scripts/EasternKingdoms/Gnomeregan/
 * instance_gnomeregan.cpp at aa32e0dde, untouched) is replaced at load, not copied: only its facts are kept (the stock
 * data id 0 TYPE_GRUBBIS, the "G N O <n>" save, the four door entries). Its authors: Yehonal, Hanabi, Kargatum,
 * Francesco Borzi, Skjalf, Kitzunu, Jelle Meeus (FACTS-STOCK 1.4).
 *
 * Frame: +x is north, +y is west (WoW's own; SP's compass words mean the same); bearing 0 is +x, 90 is +y. DB positions
 * are exact; every other point and polygon is [navmesh estimate]: the polygons were cut from the map 90 mmtiles on a
 * 0.5 yd raster by WP-S0 (the flooded floor's outer ring, Douglas-Peucker 1 to 1.5 yd, holes filled; the dish by its
 * 6 yd core, as NAVMESH measured it). The playtest checks key points with `.dbtest gnomer where` and .gps.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_REWORK_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_REWORK_H

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

namespace GnomereganRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapGnomeregan = 90;
    // The stock instance name (section 7 #2 A): modules load after the core scripts, and a database-bound script
    // registered later under the same name replaces the earlier one, so instance_template 90 is untouched and
    // npc_kernobee's GetGnomereganAI (gnomeregan.h: GetInstanceAI<AI>(obj, "instance_gnomeregan")) keeps finding it.
    // Kernobee reads no instance data: the name is all he needs.
    char constexpr kInstanceScriptName[] = "instance_gnomeregan";
    // `.dbtest gnomer <key> <subcommand>`: the kit shell's command name, nested under the shared `.dbtest` root.
    char constexpr kTestCommand[] = "dbtest gnomer";
    // DungeonKit::LogMechanic(kLogDungeon, "<boss>", "<mechanic>", ...) = "gnomer-build <boss> <mechanic> ..." (s3.5).
    char constexpr kLogDungeon[] = "gnomer-build";

    // ----------------------------------------------------------------------------------------------------------------
    // Boss slots (InstanceScript::SetBossNumber(kBossCount)). Slot = the DungeonEncounter bit (section 3.2 item 1): the
    // completed-encounter mask and the slots agree; slot 6 has no DBC row. The order is fixed: the save string stores
    // the states by position.
    // ----------------------------------------------------------------------------------------------------------------
    enum GnomereganBosses : std::uint32_t
    {
        BOSS_ALERT_SYSTEM       = 0,    // D4, encounter 1107 (new; heroic 1111). Its death opens the Workshop Door
        BOSS_VISCOUS_FALLOUT    = 1,    // D2, encounter 378 (heroic 1109)
        BOSS_TECHBOT            = 2,    // D1, encounter 379 (re-pointed from Grubbis; heroic 1108)
        BOSS_ELECTROCUTIONER    = 3,    // D3, encounter 380 (section 1's end, Finder 14; heroic 1110)
        BOSS_CROWD_PUMMELER     = 4,    // D5, encounter 381 (heroic 1112)
        BOSS_THERMAPLUGG        = 5,    // D6, encounter 382 (section 2's end, Finder 320; heroic 1113)
        BOSS_WHOLE_WORKSHOP     = 6,    // D6Ha: the hard mode kill (DONE inside slot 5's DONE with the flag armed)
    };
    std::uint32_t constexpr kBossCount = 7;
    std::uint32_t constexpr kEncounterBossCount = 6;    // slots 0 to 5 carry DungeonEncounter bits 0 to 5

    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "The Mobile Alert System", "Viscous Fallout", "Techbot", "Electrocutioner 6000", "Crowd Pummeler 9-60",
        "Mekgineer Thermaplugg", "The Whole Workshop (hard mode)",
    } };

    // The DungeonEncounter rows of each slot (section 3.3, WP-H writes them): normal and heroic.
    inline std::array<std::uint32_t, kEncounterBossCount> constexpr kEncounterNormal{ {
        1107, 378, 379, 380, 381, 382 } };
    inline std::array<std::uint32_t, kEncounterBossCount> constexpr kEncounterHeroic{ {
        1111, 1109, 1108, 1110, 1112, 1113 } };

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids. 0 keeps its stock number for its stock readers (section 3.2 item 2); the
    // rest are the build's own.
    // ----------------------------------------------------------------------------------------------------------------
    enum GnomereganData : std::uint32_t
    {
        // Stock: TYPE_GRUBBIS. Its only writer (Grubbis's death SmartAI) and reader (Emi's create) are gone with Emi
        // (ruling 2, section 7 #18 A): Get answers NOT_STARTED, a Set is ignored with a debug line.
        DATA_GRUBBIS            = 0,

        // The Workshop Door 90858 (section 7 #15 A, #16 B): WorkshopDoorState. Get: the state now. Set(state): refused
        // below the state the slots give; the instance raises it itself (Electrocutioner DONE: 1; Alert System DONE:
        // 2) and go_gnomer_workshop_door raises it to 2 when a player opens the unlocked door. Saved.
        DATA_WORKSHOP_DOOR      = 10,
        // The Final Chamber 142207 (section 7 #17 A): Get 1, the instance holds it open from the load on.
        DATA_FINAL_CHAMBER      = 11,
        // The Finder section of the run (the first entering LFG group's dungeon, 0 when none): 1 (Finder 14 or 321)
        // or 2 (320 or 322). Get only (saved; DC and `.dbtest gnomer state` read it).
        DATA_SECTION            = 12,

        // The hard mode (section 3.2 item 6, section 3.7). Get: the flag (saved; holds through wipes, never unset by a
        // card's expiry). Set(1): the console (D6Ha's go_gnomer_clearance_console), after its own checks; the instance
        // checks again (HardModeFlagAllowed) and saves. Set(0) is refused (GM only: DATA_GM_HARD_MODE).
        DATA_HARD_MODE          = 20,
        // Thermaplugg's pull (RB-24): Set(kVerdictArmed) when his pull built the hard mode packages, Set(kVerdictPlain)
        // when it did not; the hard mode loot bit and slot 6 follow the verdict, never the flag alone. Get: the pull's
        // verdict (0 between pulls).
        DATA_HARD_MODE_VERDICT  = 21,
        // Get: 1 when slot 6 is DONE.
        DATA_HARD_MODE_KILLED   = 22,
        // Get: 1 while the console would set the flag now (heroic, Thermaplugg neither fighting nor DONE, not set).
        DATA_HARD_MODE_KEY      = 23,

        // Crowd Pummeler's chest (section 3.2 item 5, section 7 #38 k A): PummelerChestState. Get only: the instance
        // places it when slot 4 goes DONE and again after a reload until it is looted (saved).
        DATA_PUMMELER_CHEST     = 30,
        // The End NPCs (section 3.2 item 4, section 7 #24 A, ruling 60): Get(DATA_END_NPC_BASE + 1 or + 2): 1 while the
        // instance keeps that exile standing (normal, Electrocutioner or Thermaplugg DONE).
        DATA_END_NPC_BASE       = 40,

        // GM test commands (.dbtest gnomer; never sent by a boss)
        DATA_GM_DOOR            = 90,   // Set(WorkshopDoorState): force the door's state, any direction
        DATA_GM_HARD_MODE       = 91,   // Set(0|1): the flag, heroic only, never while Thermaplugg fights or is DONE
        DATA_GM_CHEST           = 92,   // Set(1): place the chest now (any slot state); Set(0): remove it, not
                                        // looted, and hold it off until Set(1) or a reload
        DATA_GM_END_NPC         = 93,   // Set(1|2): summon that exile now (any difficulty, any slot); Set(0): both off
        DATA_GM_SECTION         = 94,   // Set(0|1|2): the run's section
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Guid keys (GetGuidData): the spawned bosses by slot through ObjectData, the doors; summons are tracked by hand.
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kGuidBossBase = 100;            // + slot: 100 to 105 (106 = Thermaplugg, the hard mode)
    std::uint32_t constexpr kGuidWorkshopDoor = 120;
    std::uint32_t constexpr kGuidFinalChamber = 121;
    std::uint32_t constexpr kGuidPummelerChest = 122;       // the placed chest (tracked by hand)
    std::uint32_t constexpr kGuidEndNpcBase = 130;          // + 1 / + 2: the summoned exiles (tracked by hand)

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum GnomereganCreatures : std::uint32_t
    {
        // Stock units the rework scripts or reads
        NPC_VISCOUS_FALLOUT         = 7079,     // boss_viscous_fallout_rework (D2)
        NPC_ELECTROCUTIONER         = 6235,     // boss_electrocutioner_rework (D3)
        NPC_CROWD_PUMMELER          = 6229,     // boss_crowd_pummeler_rework (D5)
        NPC_THERMAPLUGG             = 7800,     // boss_thermaplugg_rework (D6; the hard mode on the same entry)
        NPC_TECHBOT_OUTSIDE         = 6231,     // map 0, stays stock (section 7 #14 A); D1's 301105 copies it
        NPC_DUPE_BUG_STOCK          = 7732,     // stock, never summoned in here (D1's 301106 copies it)
        NPC_MOBILE_ALERT_SYSTEM     = 7849,     // stock trash, stays (D4's 301110 copies it)
        NPC_WALKING_BOMB_STOCK      = 7915,     // stock, never summoned in here (the faces' SmartAI is dropped)
        NPC_DARK_IRON_AMBASSADOR    = 6228,     // the rare (ruling 5; WP-H's health)
        NPC_KERNOBEE                = 7850,     // npc_kernobee (stock, quest 2904): needs kInstanceScriptName only
        NPC_EMI_SHORTFUSE           = 7998,     // cut (ruling 2): the S0 rev deletes her spawn
        NPC_GRUBBIS                 = 7361,     // cut with Emi (no spawn)
        NPC_MEKGINEER_TRIGGER       = 13876,    // stock, neutral, no script
        NPC_GEAR_LAUNCHED_BOMB      = 301100,   // the gear's Walking Bomb Launcher bomb: never key a bomb rule on it

        // The build's own (section 3.3; ids.yaml reservation `gnomeregan`, creature 301105-301199)
        NPC_TECHBOT                 = 301105,   // D1: boss_techbot_rework (a copy of 6231)
        NPC_DUPE_BUG                = 301106,   // D1
        NPC_LAG_ECHO                = 301107,   // D1 (the after-image)
        NPC_ALERT_SYSTEM            = 301110,   // D4: boss_mobile_alert_system_rework (a copy of 7849)
        NPC_SECURITY_ASSISTANT      = 301111,   // D4
        NPC_SECURITY_DEFENDER       = 301112,   // D4
        NPC_LIGHT_STALKER           = 301113,   // D4
        NPC_FRAME_STALKER           = 301115,   // D5 (the punch frame's owner, if D5 needs one)
        NPC_WALKING_BOMB            = 301120,   // D6
        NPC_INCENDIARY_BOMB         = 301121,   // D6
        NPC_FROST_BOMB              = 301122,   // D6
        NPC_RADIOACTIVE_BOMB        = 301123,   // D6
        NPC_THE_BIG_ONE             = 301124,   // D6
        NPC_FACE_STALKER            = 301125,   // D6
        NPC_MINE                    = 301126,   // D6
        NPC_ZONE_STALKER            = 301127,   // D6
        NPC_POOL_STALKER            = 301130,   // D2 (if needed)
        NPC_BLAST_STALKER           = 301132,   // D3
        NPC_WANDERING_PUDDLE        = 301135,   // D6Ha
        NPC_PUMMELERS_FIST          = 301136,   // D6Hb
        NPC_ROOM_ALARM              = 301137,   // D6Ha
        NPC_VENT_STALKER            = 301138,   // D6Ha
        NPC_EXILE                   = 301190,   // Q: the quest exile (template); the instance summons the End NPCs
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Game objects
    // ----------------------------------------------------------------------------------------------------------------
    enum GnomereganGameObjects : std::uint32_t
    {
        GO_WORKSHOP_DOOR            = 90858,    // go_gnomer_workshop_door (the S0 rev binds it, keyless)
        GO_FINAL_CHAMBER_DOOR       = 142207,   // held open by the instance (section 7 #17 A)
        GO_CAVE_IN_1                = 146085,   // stays shut, scenery (section 7 #18 A)
        GO_CAVE_IN_2                = 146086,
        GO_GNOME_FACE_04            = 142208,   // the faces: SmartAI dropped by the S0 rev, D6 drives them
        GO_GNOME_FACE_03            = 142209,
        GO_GNOME_FACE_02            = 142210,
        GO_GNOME_FACE_01            = 142211,
        GO_GNOME_FACE_06            = 142212,
        GO_GNOME_FACE_05            = 142213,
        GO_BUTTON_01                = 142214,   // the buttons: SmartAI dropped, not selectable (section 7 #38 m A)
        GO_BUTTON_02                = 142215,
        GO_BUTTON_03                = 142216,
        GO_BUTTON_04                = 142217,
        GO_BUTTON_05                = 142218,
        GO_BUTTON_06                = 142219,
        GO_PUNCHOGRAPH_A            = 142345,   // the 3005-A copy inside (section 7 #34 A; the S0 rev spawns it)
        GO_PUNCHOGRAPH_B            = 142475,
        GO_PUNCHOGRAPH_C            = 142476,
        GO_PUNCHOGRAPH_D            = 142696,
        GO_THERMAPLUGGS_SAFE        = 142477,

        // The build's own (gameobject 301380-301399)
        GO_PUMMELER_CHEST           = 301380,   // D5's template (normal); the instance places it
        GO_PUMMELER_CHEST_HEROIC    = 301381,   // D5's template (heroic)
        GO_CLEARANCE_CONSOLE        = 301382,   // D6Ha's template; the S0 rev spawns it (heroic only)
    };

    // The faces by their number 01 to 06 (ruling 64; index 0 = face 01), their buttons, their bearings from the room's
    // center (degrees) and their DB spots.
    std::uint32_t constexpr kFaceCount = 6;
    inline std::array<std::uint32_t, kFaceCount> constexpr kFaceEntries{ { GO_GNOME_FACE_01, GO_GNOME_FACE_02,
        GO_GNOME_FACE_03, GO_GNOME_FACE_04, GO_GNOME_FACE_05, GO_GNOME_FACE_06 } };
    inline std::array<std::uint32_t, kFaceCount> constexpr kButtonEntries{ { GO_BUTTON_01, GO_BUTTON_02, GO_BUTTON_03,
        GO_BUTTON_04, GO_BUTTON_05, GO_BUTTON_06 } };
    inline std::array<float, kFaceCount> constexpr kFaceBearingDeg{ { 127.0f, 75.6f, 24.4f, 333.2f, 282.0f, 230.2f } };

    constexpr std::optional<std::uint32_t> FaceIndexOf(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kFaceCount; ++i)
            if (kFaceEntries[i] == entry || kButtonEntries[i] == entry)
                return i;
        return std::nullopt;
    }

    // Items the instance or the console reads
    std::uint32_t constexpr ITEM_PRISMATIC_PUNCH_CARD = 9316;
    std::uint32_t constexpr ITEM_WHITE_PUNCH_CARD = 9279;
    std::uint32_t constexpr ITEM_WORKSHOP_KEY = 6893;       // still drops (ruling 58); the door no longer asks for it
    std::uint32_t constexpr ITEM_MEMORY_CORE = 9277;

    // ----------------------------------------------------------------------------------------------------------------
    // Id slices (section 3.3; ids.yaml reservation `gnomeregan`). Each WP declares its spells inside its own slice.
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 214280, 214679 };
    IdSlice constexpr kSpellsShared{ 214280, 214299 };          // S0 (214280 the Weakened copy, reserved), spare
    IdSlice constexpr kSpellsTechbot{ 214300, 214339 };         // D1
    IdSlice constexpr kSpellsFallout{ 214340, 214379 };         // D2
    IdSlice constexpr kSpellsElectrocutioner{ 214380, 214419 }; // D3
    IdSlice constexpr kSpellsAlertSystem{ 214420, 214459 };     // D4
    IdSlice constexpr kSpellsPummeler{ 214460, 214489 };        // D5
    IdSlice constexpr kSpellsThermaplugg{ 214490, 214539 };     // D6
    IdSlice constexpr kSpellsHardModeA{ 214540, 214579 };       // D6Ha
    IdSlice constexpr kSpellsHardModeB{ 214580, 214619 };       // D6Hb
    IdSlice constexpr kSpellsConsoleAndSpare{ 214620, 214679 }; // D6Ha's console, then spare (ask the orchestrator)

    inline std::array<IdSlice, 10> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsTechbot, kSpellsFallout, kSpellsElectrocutioner, kSpellsAlertSystem, kSpellsPummeler,
        kSpellsThermaplugg, kSpellsHardModeA, kSpellsHardModeB, kSpellsConsoleAndSpare,
    } };

    std::uint32_t constexpr kSpellWeakenedCopy = 214280;        // reserved (rule 22): a script-applied Weakened copy
    IdSlice constexpr kCreaturesReservation{ 301105, 301199 };
    IdSlice constexpr kGameObjectsReservation{ 301380, 301399 };

    // ----------------------------------------------------------------------------------------------------------------
    // Points (section 3.8, appendix A, the rulings; [DB] exact, the rest [navmesh estimate], z the floor's)
    // ----------------------------------------------------------------------------------------------------------------
    struct Point3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        float o = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
    };

    // The bosses' spots
    Point3 constexpr kTechbotSpawn{ -519.92f, -107.67f, -155.87f, 2.01f };      // ruling 61 (the S0 rev spawns him)
    Point3 constexpr kFalloutStockSpawn{ -471.39f, 48.48f, -207.95f, 6.03f };   // [DB] guid 30137 before the move
    // Section 7 #19 A: area C, the far end of his dropped path 70790; facing the cave's mouth (the spawn corner).
    Point3 constexpr kFalloutSpawn{ -391.0f, 132.0f, -209.1f, 3.95f };
    Point3 constexpr kElectrocutionerSpawn{ -552.05f, 502.90f, -216.73f, 5.76f };   // [DB] guid 30133, wander 0 now
    Point3 constexpr kPlatformCenter{ -550.8f, 504.8f, -216.7f, 0.f };          // section 7 #20 A
    Point3 constexpr kAlertSystemSpawn{ -756.67f, 224.55f, -273.08f, 3.82f };   // ruling 66 (the S0 rev spawns it)
    // The window ruling (section 10): in the glass, 4.8 yd under the pocket floor, scale 5 (D5 sets it).
    Point3 constexpr kPummelerSpot{ -883.5655f, 363.25467f, -277.38113f, 2.9751785f };
    Point3 constexpr kThermapluggSpawn{ -531.32f, 670.16f, -325.18f, 2.91f };   // [DB] guid 30139
    // Section 2.7 #7: every "from the center" of Thermaplugg's room means from his spawn.
    Point3 constexpr kRoomCenter{ -531.32f, 670.16f, -325.18f, 0.f };

    // Crowd Pummeler's frame (section 7 #28 A): origin on the pocket's equal-area center line, the center line due
    // south (o = pi), the near line 12 yd from the origin.
    Point3 constexpr kPummelerFrameOrigin{ -887.0f, 364.2f, -272.6f, 3.14159265f };
    // Section 7 #38 k A: the chest on the pocket floor (clearance 11.8), facing the glass.
    Point3 constexpr kPummelerChestSpot{ -899.0f, 365.0f, -272.3f, 0.f };
    // The pocket box (section 3.8): his arena guard and the damage filter's "inside the pocket".
    float constexpr kPocketBoxMinX = -913.f;
    float constexpr kPocketBoxMaxX = -884.f;
    float constexpr kPocketBoxMinY = 342.f;
    float constexpr kPocketBoxMaxY = 391.f;
    float constexpr kPocketBoxMinZ = -276.f;
    float constexpr kPocketBoxMaxZ = -262.f;

    constexpr bool InPocketBox(float x, float y, float z)
    {
        return x >= kPocketBoxMinX && x <= kPocketBoxMaxX && y >= kPocketBoxMinY && y <= kPocketBoxMaxY
            && z >= kPocketBoxMinZ && z <= kPocketBoxMaxZ;
    }

    // Thermaplugg's room (section 3.8, section 7 #30 A, #31 B): the faces' DB spots, the plates 25 yd from the
    // center on each face's bearing, the bomb starts at the alcove mouths 37 yd out.
    inline std::array<Point3, kFaceCount> constexpr kFaceSpots{ {
        { -561.24f, 709.88f, -327.48f, -0.881392f },    // 01 [DB] guid 9593
        { -518.90f, 718.47f, -327.51f, -1.78024f },     // 02 [DB] guid 9265
        { -485.72f, 690.87f, -327.50f, -2.67908f },     // 03 [DB] guid 11994
        { -486.67f, 647.65f, -327.48f, 2.70526f },      // 04 [DB] guid 6388
        { -521.02f, 621.55f, -327.48f, 1.81514f },      // 05 [DB] guid 6755
        { -562.96f, 632.16f, -327.48f, 0.916298f },     // 06 [DB] guid 28327
    } };
    float constexpr kPlateRadiusYd = 25.f;      // ruling 39 (section 7 #30 A)
    inline std::array<Point3, kFaceCount> constexpr kPlateSpots{ {
        { -546.37f, 690.13f, -326.9f, 0.f },
        { -525.10f, 694.37f, -326.7f, 0.f },
        { -508.55f, 680.49f, -326.6f, 0.f },
        { -509.01f, 658.89f, -326.3f, 0.f },
        { -526.12f, 645.71f, -326.6f, 0.f },
        { -547.32f, 650.95f, -326.5f, 0.f },
    } };
    float constexpr kBombStartRadiusYd = 37.f;  // section 7 #31: the alcove mouth (a wall 12 yd in front of the face)
    inline std::array<Point3, kFaceCount> constexpr kBombStarts{ {
        { -553.59f, 699.71f, -327.3f, 0.f },
        { -522.12f, 706.00f, -327.3f, 0.f },
        { -497.62f, 685.44f, -327.3f, 0.f },
        { -498.29f, 653.48f, -327.3f, 0.f },
        { -523.63f, 633.97f, -327.3f, 0.f },
        { -555.00f, 641.73f, -327.3f, 0.f },
    } };

    // The Workshop Door and the Final Chamber [DB]
    Point3 constexpr kWorkshopDoorSpot{ -758.54f, 260.39f, -273.05f, 2.22529f };   // guid 12003
    Point3 constexpr kFinalChamberSpot{ -618.61f, 691.12f, -327.05f, 2.88852f };   // guid 6910

    // The Finder starts (section 7 #26 A) and the quest NPC spots (section 4.Q, section 7 #49 A)
    Point3 constexpr kSection1Start{ -329.098f, -3.207f, -152.851f, 2.96706f };    // [DB] area trigger 324's target
    Point3 constexpr kSection2Start{ -736.51f, 2.71f, -249.99f, 3.14f };           // [DB] area trigger 523's target
    Point3 constexpr kEntranceNpcSpot{ -338.12f, -6.55f, -152.85f, 1.16f };        // Q's static spawn
    Point3 constexpr kWorkshopNpcSpot{ -753.00f, -4.04f, -252.22f, 1.40f };        // Q's static spawn
    // Ruling 60: the End NPCs, summoned by the instance on normal when their boss is DONE (section 7 #24 A).
    Point3 constexpr kEndNpc1Spot{ -538.76f, 527.40f, -216.27f, 3.89f };           // Electrocutioner's walkway mouth
    Point3 constexpr kEndNpc2Spot{ -607.63f, 677.98f, -327.04f, 6.21f };           // Thermaplugg's south entrance

    // The objects the S0 rev spawns
    Point3 constexpr kPunchographACopySpot{ -502.5f, 67.2f, -154.8f, 5.70f };      // section 7 #34 A
    Point3 constexpr kConsoleSpot{ -580.00f, 681.49f, -327.08f, 6.06f };           // ruling 63, facing the center

    // Section 7 #25 A: mod-dungeon-checkpoint's rows (CP data/sql/db-world/u_dungeon_checkpoint_2026_11_26_00.sql,
    // pinned by lib/test_gnomeregan_npcs.py): the Depot landing (reached only, 25 yd), Electrocutioner's walkway mouth
    // (once he is DONE) and Pummeler's pocket (once he is DONE).
    Point3 constexpr kCheckpointDepot{ -736.51f, 2.71f, -249.99f, 3.14f };
    float constexpr kCheckpointDepotReachYd = 25.f;
    Point3 constexpr kCheckpointElectrocutioner{ -543.8f, 530.9f, -216.6f, 1.31f };
    Point3 constexpr kCheckpointPummeler{ -898.8f, 359.8f, -272.4f, 3.14f };

    // ----------------------------------------------------------------------------------------------------------------
    // The Finder sections (section 7 #5 A, #6 A; the BRD pattern): the LFG ids (WP-H writes the rows), the start, the
    // end slot whose kill completes the section (lastEncounterDungeon), the doors on its path.
    // ----------------------------------------------------------------------------------------------------------------
    struct FinderSection
    {
        std::uint32_t number;
        char const* name;
        std::uint32_t lfgNormal;
        std::uint32_t lfgHeroic;
        Point3 start;
        std::uint32_t endSlot;
        std::array<std::uint32_t, 2> doors;     // GO entries on the path (0 = none)
    };

    inline std::array<FinderSection, 2> constexpr kSections{ {
        { 1, "Gnomeregan", 14, 321, kSection1Start, BOSS_ELECTROCUTIONER, { { 0, 0 } } },
        { 2, "Gnomeregan - The Workshop", 320, 322, kSection2Start, BOSS_THERMAPLUGG,
            { { GO_WORKSHOP_DOOR, GO_FINAL_CHAMBER_DOOR } } },
    } };

    constexpr FinderSection const* SectionByNumber(std::uint32_t number)
    {
        for (FinderSection const& s : kSections)
            if (s.number == number)
                return &s;
        return nullptr;
    }

    // The section an LFG dungeon id runs (0: none of Gnomeregan's).
    constexpr std::uint32_t SectionOfLfgDungeon(std::uint32_t lfgDungeon)
    {
        for (FinderSection const& s : kSections)
            if (lfgDungeon && (lfgDungeon == s.lfgNormal || lfgDungeon == s.lfgHeroic))
                return s.number;
        return 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Workshop Door (section 7 #15 A, #16 B; ruling 26, 30, 58). The door is keyless (the S0 rev clears lock 92 and
    // GO_FLAG_LOCKED: the 3.3.5 client enforces a door's lock from the query data). Sealed: shut and not selectable
    // (a carried key, a rogue or an engineer cannot skip the Alert System). Unlocked: Electrocutioner is DONE, shut
    // and clickable by anyone. Open: the Alert System is DONE, or a player opened it while unlocked: open, latched,
    // not selectable. Saved; the state never drops back on its own.
    // ----------------------------------------------------------------------------------------------------------------
    enum WorkshopDoorState : std::uint32_t
    {
        WORKSHOP_DOOR_SEALED    = 0,
        WORKSHOP_DOOR_UNLOCKED  = 1,
        WORKSHOP_DOOR_OPEN      = 2,
    };
    inline std::array<char const*, 3> constexpr kWorkshopDoorNames{ { "sealed", "unlocked", "open" } };

    // The least state the slots give.
    constexpr std::uint32_t WorkshopDoorFromSlots(std::uint32_t electrocutionerSlot, std::uint32_t alertSlot)
    {
        if (alertSlot == DungeonKit::State::Done)
            return WORKSHOP_DOOR_OPEN;
        if (electrocutionerSlot == DungeonKit::State::Done)
            return WORKSHOP_DOOR_UNLOCKED;
        return WORKSHOP_DOOR_SEALED;
    }

    // The state after a raise to `wanted` (never lower than the slots' state or the saved one; out of range ignored).
    constexpr std::uint32_t RaiseWorkshopDoor(std::uint32_t saved, std::uint32_t wanted,
        std::uint32_t electrocutionerSlot, std::uint32_t alertSlot)
    {
        std::uint32_t const floor = std::max(std::min(saved, std::uint32_t(WORKSHOP_DOOR_OPEN)),
            WorkshopDoorFromSlots(electrocutionerSlot, alertSlot));
        return wanted <= WORKSHOP_DOOR_OPEN ? std::max(floor, wanted) : floor;
    }

    // A player's open counts only while the door is unlocked (a sealed door is not selectable: a GM's `.gobject
    // activate` or a script's use is refused and shut again).
    constexpr bool WorkshopDoorOpenByUseAllowed(std::uint32_t state)
    {
        return state >= WORKSHOP_DOOR_UNLOCKED;
    }

    constexpr bool WorkshopDoorSelectable(std::uint32_t state)
    {
        return state == WORKSHOP_DOOR_UNLOCKED;
    }

    // The engine's GOState values (GameObjectData.h; the instance static_asserts them): open 0, shut 1.
    std::uint32_t constexpr kGoStateActive = 0;
    std::uint32_t constexpr kGoStateReady = 1;

    constexpr std::uint32_t WorkshopDoorGoState(std::uint32_t state)
    {
        return state == WORKSHOP_DOOR_OPEN ? kGoStateActive : kGoStateReady;
    }

    // The latch's loop guards (R-1-FW B1). GameObject::SetLootState always calls the door AI's OnStateChanged, the AI
    // tells the instance, and the instance latches the door open, which sets the loot state again. Two guards break
    // that loop, each one alone enough:
    // - the latch sets GO_ACTIVATED only on a door that is not already open and activated (the engine assigns the loot
    //   state before it calls the AI, so a click's own callback already sees GO_ACTIVATED);
    // - the AI forwards an open to the instance only while the saved state is below open.
    constexpr bool OpenLatchSetsLootState(bool goActive, bool lootActivated)
    {
        return !(goActive && lootActivated);
    }

    constexpr bool WorkshopDoorUseForwarded(std::uint32_t state)
    {
        return state < WORKSHOP_DOOR_OPEN;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Crowd Pummeler's chest (section 3.2 item 5, section 7 #38 k A, ZF RB-23 M4): placed by the instance when slot 4
    // goes DONE and again after a reload until it is emptied. Looted: the chest is gone (consumed) or found despawned.
    // ----------------------------------------------------------------------------------------------------------------
    enum PummelerChestState : std::uint32_t
    {
        PUMMELER_CHEST_NONE     = 0,
        PUMMELER_CHEST_PLACED   = 1,
        PUMMELER_CHEST_LOOTED   = 2,
    };
    inline std::array<char const*, 3> constexpr kChestNames{ { "none", "placed", "looted" } };

    // Place it now? `standing`: a chest object of ours is in the world; `gridLoaded`: the spot's grid is loaded.
    constexpr bool ChestPlaceDue(std::uint32_t pummelerSlot, std::uint32_t chest, bool standing, bool gridLoaded)
    {
        return pummelerSlot == DungeonKit::State::Done && chest != PUMMELER_CHEST_LOOTED && !standing && gridLoaded;
    }

    // Was it emptied? `tracked`: a chest was placed during this load (a reload starts untracked, so an unlooted chest
    // is placed again); `found`: its object is still in the map; `spawned`: it is. The chest is consumable: emptied, it
    // is deleted and leaves the map a tick later (R-1-FW M1), so a tracked chest that is gone was looted. Instance
    // grids unload only with the whole map (Map::UnloadAll), so nothing else removes it inside a live instance.
    constexpr bool ChestEmptied(bool tracked, bool found, bool spawned)
    {
        return tracked && (!found || !spawned);
    }

    constexpr std::uint32_t ChestEntry(bool heroic)
    {
        return heroic ? GO_PUMMELER_CHEST_HEROIC : GO_PUMMELER_CHEST;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The End NPCs (section 3.2 item 4, section 7 #24 A, ruling 60; skill section 9): the exile at Electrocutioner's
    // walkway mouth (End 1) and at Thermaplugg's south entrance (End 2), normal only, once their boss is DONE; the
    // instance summons them (at the DONE and after a reload), so the boss files do nothing for them.
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kEndNpcCount = 2;

    constexpr std::uint32_t EndNpcSlot(std::uint32_t endNpc)
    {
        return endNpc == 1 ? BOSS_ELECTROCUTIONER : BOSS_THERMAPLUGG;
    }

    constexpr Point3 EndNpcSpot(std::uint32_t endNpc)
    {
        return endNpc == 1 ? kEndNpc1Spot : kEndNpc2Spot;
    }

    constexpr bool EndNpcStands(bool heroic, std::uint32_t slot)
    {
        return !heroic && slot == DungeonKit::State::Done;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hard mode (section 3.2 item 6, section 3.7, rulings 43 to 53; RB-24)
    // ----------------------------------------------------------------------------------------------------------------
    // The console's answer (D6Ha's gossip shows a line per refusal; the instance repeats the check on the Set).
    enum ConsoleVerdict : std::uint32_t
    {
        CONSOLE_ACCEPTED        = 0,
        CONSOLE_NOT_HEROIC      = 1,
        CONSOLE_BOT             = 2,    // bots never set it (section 3.5 rule 34)
        CONSOLE_IN_COMBAT       = 3,
        CONSOLE_NO_CARD         = 4,
        CONSOLE_BOSS_ENGAGED    = 5,    // Thermaplugg fights or is DONE
        CONSOLE_ALREADY_SET     = 6,
    };

    constexpr ConsoleVerdict ConsoleCheck(bool heroic, bool isBot, bool inCombat, bool hasCard,
        std::uint32_t thermapluggSlot, std::uint32_t flag)
    {
        if (!heroic)
            return CONSOLE_NOT_HEROIC;
        if (isBot)
            return CONSOLE_BOT;
        if (flag)
            return CONSOLE_ALREADY_SET;
        if (thermapluggSlot == DungeonKit::State::InProgress || thermapluggSlot == DungeonKit::State::Done)
            return CONSOLE_BOSS_ENGAGED;
        if (inCombat)
            return CONSOLE_IN_COMBAT;
        if (!hasCard)
            return CONSOLE_NO_CARD;
        return CONSOLE_ACCEPTED;
    }

    // The instance's own check on SetData(DATA_HARD_MODE, 1) (the console already checked the player).
    constexpr bool HardModeFlagAllowed(bool heroic, std::uint32_t thermapluggSlot)
    {
        return heroic && thermapluggSlot != DungeonKit::State::InProgress
            && thermapluggSlot != DungeonKit::State::Done;
    }

    // DATA_HARD_MODE_VERDICT values (RB-24: the pull passes its decision as data).
    std::uint32_t constexpr kVerdictNone = 0;
    std::uint32_t constexpr kVerdictPlain = 1;      // a pull with no hard mode packages (plain heroic)
    std::uint32_t constexpr kVerdictArmed = 2;      // the pull built the packages: 800,000, the loot bit, slot 6

    // The pull arms only on an armed verdict with the flag set on heroic.
    constexpr bool HardModeArmed(bool heroic, std::uint32_t flag, std::uint32_t verdict)
    {
        return heroic && flag && verdict == kVerdictArmed;
    }

    // The loot bit (LootMode 2 on 7800's heroic lootid): lit while the pull is armed and he is not dead yet; at the
    // pull and at the verdict, never in JustDied (rule 1).
    constexpr bool HardModeLootLit(bool armed, std::uint32_t thermapluggSlot)
    {
        return armed && thermapluggSlot != DungeonKit::State::Done;
    }

    constexpr bool GmHardModeAllowed(bool heroic, std::uint32_t thermapluggSlot, std::uint32_t value)
    {
        return (value == 0 || heroic) && thermapluggSlot != DungeonKit::State::InProgress
            && thermapluggSlot != DungeonKit::State::Done;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (cut by WP-S0 from the map 90 mesh; z bands about 2 yd under to 6 to 9 yd over the floor). A boss WP that
    // needs an inset leash or a narrower pick area cuts it in its own Logic header.
    // ----------------------------------------------------------------------------------------------------------------
    // Techbot's dish: its 6 yd core grown back 6.5 yd (NAVMESH's 2,434 sq yd room; the Cave Ins at its mouths).
    inline std::array<Vec2, 40> constexpr kDishPolygon{ {
        { -553.5f, -73.5f }, { -547.0f, -80.5f }, { -548.0f, -86.5f }, { -543.0f, -94.5f }, { -543.0f, -103.5f },
        { -539.5f, -107.0f }, { -533.5f, -107.0f }, { -528.5f, -111.5f }, { -533.5f, -115.0f }, { -531.5f, -131.5f },
        { -525.5f, -134.0f }, { -520.5f, -133.0f }, { -518.0f, -129.5f }, { -515.5f, -132.5f }, { -508.5f, -131.5f },
        { -506.5f, -129.0f }, { -507.0f, -126.0f }, { -502.5f, -125.5f }, { -500.5f, -120.5f }, { -500.5f, -111.5f },
        { -507.0f, -104.5f }, { -504.5f, -98.0f }, { -502.5f, -97.0f }, { -503.5f, -90.0f }, { -510.0f, -88.0f },
        { -511.0f, -81.0f }, { -514.0f, -79.5f }, { -515.0f, -76.0f }, { -517.5f, -75.0f }, { -519.5f, -71.5f },
        { -524.5f, -70.5f }, { -525.5f, -67.5f }, { -532.5f, -64.5f }, { -532.0f, -59.5f }, { -535.5f, -56.0f },
        { -541.0f, -56.0f }, { -541.5f, -57.5f }, { -546.5f, -54.5f }, { -551.0f, -56.0f }, { -553.5f, -62.0f },
    } };
    float constexpr kDishZMin = -158.f;
    float constexpr kDishZMax = -145.f;

    // Viscous Fallout's cave (x -545 to -358, y 30 to 215; the floor band -211.5 to -203).
    inline std::array<Vec2, 90> constexpr kCavePolygon{ {
        { -545.0f, 96.5f }, { -544.5f, 91.5f }, { -538.0f, 90.0f }, { -534.5f, 94.0f }, { -533.0f, 93.0f },
        { -529.0f, 101.5f }, { -513.0f, 101.5f }, { -511.5f, 96.5f }, { -516.0f, 95.5f }, { -516.0f, 82.0f },
        { -511.0f, 81.5f }, { -508.5f, 74.5f }, { -504.0f, 71.0f }, { -503.0f, 63.5f }, { -474.5f, 35.0f },
        { -472.0f, 37.5f }, { -465.0f, 35.5f }, { -463.0f, 34.0f }, { -463.5f, 30.0f }, { -410.5f, 30.0f },
        { -410.0f, 35.0f }, { -402.0f, 37.5f }, { -399.5f, 34.5f }, { -380.5f, 47.5f }, { -384.0f, 70.5f },
        { -365.5f, 75.0f }, { -363.5f, 81.5f }, { -358.5f, 82.5f }, { -358.5f, 91.0f }, { -362.0f, 94.0f },
        { -363.5f, 91.5f }, { -368.0f, 93.5f }, { -370.5f, 101.0f }, { -369.5f, 104.5f }, { -366.5f, 101.5f },
        { -366.5f, 107.0f }, { -370.5f, 107.0f }, { -368.5f, 112.5f }, { -367.0f, 113.5f }, { -365.0f, 110.0f },
        { -358.5f, 119.0f }, { -358.5f, 135.5f }, { -361.5f, 134.5f }, { -363.5f, 136.5f }, { -366.0f, 143.5f },
        { -362.5f, 146.0f }, { -374.5f, 160.5f }, { -389.5f, 159.5f }, { -398.5f, 169.5f }, { -401.0f, 181.5f },
        { -403.0f, 180.0f }, { -410.5f, 183.0f }, { -410.5f, 187.5f }, { -414.0f, 187.5f }, { -415.5f, 184.0f },
        { -420.0f, 185.0f }, { -418.5f, 215.0f }, { -454.0f, 215.0f }, { -454.0f, 197.0f }, { -448.5f, 193.5f },
        { -451.0f, 191.0f }, { -451.5f, 185.0f }, { -454.0f, 184.0f }, { -455.0f, 187.5f }, { -463.5f, 187.5f },
        { -463.0f, 184.0f }, { -469.5f, 180.5f }, { -471.5f, 180.0f }, { -473.5f, 183.5f }, { -478.0f, 182.5f },
        { -493.5f, 168.5f }, { -495.0f, 159.0f }, { -492.0f, 157.5f }, { -495.0f, 153.5f }, { -497.0f, 155.5f },
        { -501.0f, 153.0f }, { -500.5f, 150.0f }, { -504.5f, 148.5f }, { -511.0f, 151.5f }, { -513.5f, 146.5f },
        { -509.5f, 145.0f }, { -508.5f, 141.5f }, { -512.5f, 135.0f }, { -516.0f, 135.5f }, { -516.0f, 121.0f },
        { -512.0f, 120.0f }, { -513.0f, 115.5f }, { -529.0f, 115.5f }, { -537.5f, 125.5f }, { -544.5f, 125.5f },
    } };
    float constexpr kCaveZMin = -214.f;
    float constexpr kCaveZMax = -201.f;

    // Electrocutioner's platform out to 30 yd from its center (the disc and the walkway mouth). Picks, landings and the
    // ranged band stay within kPlatformPickRadius of the center (section 7 #20 A): the rim drops 56 yd on three sides.
    inline std::array<Vec2, 13> constexpr kPlatformPolygon{ {
        { -578.0f, 505.5f }, { -565.5f, 482.0f }, { -549.5f, 478.5f }, { -531.0f, 488.0f }, { -523.5f, 503.5f },
        { -534.0f, 524.0f }, { -538.0f, 525.5f }, { -536.5f, 531.5f }, { -549.0f, 535.0f }, { -550.5f, 535.0f },
        { -552.5f, 528.0f }, { -557.0f, 529.0f }, { -572.0f, 520.5f },
    } };
    float constexpr kPlatformZMin = -219.f;
    float constexpr kPlatformZMax = -210.f;
    float constexpr kPlatformPickRadius = 21.f;

    // The Alert hall (the diagonal band, cut at the Workshop Door's line; section 7 #21 A: the fight's floor is within
    // kAlertLightReachYd of the boss).
    inline std::array<Vec2, 55> constexpr kHallPolygon{ {
        { -821.5f, 146.5f }, { -821.0f, 138.5f }, { -807.5f, 137.0f }, { -807.5f, 161.5f }, { -811.0f, 160.5f },
        { -812.0f, 163.5f }, { -810.0f, 165.0f }, { -807.5f, 163.0f }, { -807.5f, 173.5f }, { -803.0f, 181.5f },
        { -801.0f, 182.5f }, { -796.5f, 178.0f }, { -760.0f, 206.5f }, { -756.5f, 204.0f }, { -752.0f, 206.5f },
        { -751.0f, 211.5f }, { -748.0f, 210.0f }, { -743.0f, 214.0f }, { -745.0f, 217.5f }, { -741.0f, 221.0f },
        { -738.0f, 222.0f }, { -735.5f, 219.0f }, { -731.5f, 222.0f }, { -736.0f, 224.0f }, { -736.5f, 229.5f },
        { -732.5f, 231.5f }, { -736.5f, 237.0f }, { -729.0f, 244.0f }, { -737.5f, 255.0f }, { -742.0f, 252.5f },
        { -754.0f, 263.0f }, { -761.5f, 257.0f }, { -755.5f, 248.5f }, { -755.0f, 243.5f }, { -760.0f, 238.5f },
        { -760.0f, 234.5f }, { -769.0f, 228.0f }, { -774.5f, 233.0f }, { -776.5f, 231.5f }, { -775.0f, 227.0f },
        { -779.0f, 223.5f }, { -782.5f, 222.5f }, { -786.0f, 227.0f }, { -798.5f, 217.5f }, { -799.0f, 214.0f },
        { -802.0f, 214.5f }, { -799.5f, 212.5f }, { -802.0f, 210.0f }, { -801.0f, 207.5f }, { -808.5f, 202.0f },
        { -808.0f, 197.0f }, { -812.5f, 198.5f }, { -809.0f, 193.0f }, { -818.0f, 184.5f }, { -821.0f, 175.0f },
    } };
    float constexpr kHallZMin = -276.f;
    float constexpr kHallZMax = -266.f;
    float constexpr kAlertLightReachYd = 30.f;      // section 7 #21 A

    // Crowd Pummeler's pocket floor (the box above, cut to the mesh). He himself floats outside it, in the glass.
    inline std::array<Vec2, 19> constexpr kPocketPolygon{ {
        { -913.0f, 351.0f }, { -910.0f, 349.0f }, { -910.5f, 346.5f }, { -907.0f, 345.5f }, { -907.5f, 342.0f },
        { -898.5f, 342.0f }, { -897.0f, 345.0f }, { -891.0f, 344.5f }, { -889.5f, 347.0f }, { -887.0f, 347.0f },
        { -884.0f, 382.0f }, { -886.5f, 375.0f }, { -892.5f, 375.5f }, { -892.0f, 391.0f }, { -901.0f, 391.0f },
        { -902.0f, 388.5f }, { -905.0f, 388.5f }, { -906.0f, 385.0f }, { -908.5f, 385.5f },
    } };

    // Thermaplugg's room out to 52 yd from the center (the bowl, the six arms' roots, the south entrance with the
    // console), plus the 38.5 yd bowl disc that holds the alcove mouths (the bomb starts).
    inline std::array<Vec2, 38> constexpr kRoomPolygon{ {
        { -583.5f, 668.0f }, { -580.0f, 651.0f }, { -570.0f, 635.0f }, { -558.5f, 645.5f }, { -550.0f, 638.5f },
        { -558.5f, 625.5f }, { -546.0f, 620.0f }, { -528.5f, 618.0f }, { -528.0f, 633.0f }, { -517.5f, 635.5f },
        { -513.5f, 621.0f }, { -501.0f, 627.5f }, { -490.5f, 637.5f }, { -488.0f, 641.5f }, { -499.0f, 646.5f },
        { -500.0f, 649.5f }, { -495.5f, 659.0f }, { -482.0f, 653.5f }, { -479.5f, 677.0f }, { -481.5f, 685.5f },
        { -493.5f, 680.0f }, { -496.5f, 683.0f }, { -500.0f, 691.5f }, { -487.5f, 698.5f }, { -498.0f, 710.5f },
        { -512.5f, 718.5f }, { -516.5f, 705.0f }, { -525.5f, 706.5f }, { -528.0f, 708.0f }, { -525.5f, 722.0f },
        { -538.0f, 722.0f }, { -557.0f, 715.5f }, { -549.0f, 704.5f }, { -557.0f, 696.0f }, { -559.0f, 695.5f },
        { -568.0f, 707.0f }, { -572.0f, 703.0f }, { -581.0f, 686.5f },
    } };
    float constexpr kRoomZMin = -330.f;
    float constexpr kRoomZMax = -319.f;
    float constexpr kRoomBowlRadius = 38.5f;

    template <std::size_t N>
    inline ArenaRegion PolygonRegion(std::array<Vec2, N> const& polygon, float zMin, float zMax)
    {
        return ArenaRegion::Polygon(std::vector<Vec2>(polygon.begin(), polygon.end()), zMin, zMax);
    }

    inline Arena DishArena() { return Arena(PolygonRegion(kDishPolygon, kDishZMin, kDishZMax)); }
    inline Arena CaveArena() { return Arena(PolygonRegion(kCavePolygon, kCaveZMin, kCaveZMax)); }
    inline Arena PlatformArena() { return Arena(PolygonRegion(kPlatformPolygon, kPlatformZMin, kPlatformZMax)); }
    inline Arena HallArena() { return Arena(PolygonRegion(kHallPolygon, kHallZMin, kHallZMax)); }
    inline Arena PocketArena() { return Arena(PolygonRegion(kPocketPolygon, kPocketBoxMinZ, kPocketBoxMaxZ)); }

    // Crowd Pummeler's arena: the pocket floor plus his own spot in the glass (he floats 4.8 yd under the floor, out of
    // the pocket's z band; without it his leash would see him off his arena at once).
    float constexpr kPummelerSpotRadius = 3.f;
    inline Arena PummelerArena()
    {
        Arena arena = PocketArena();
        arena.Add(ArenaRegion::Circle(kPummelerSpot.XY(), kPummelerSpotRadius, kPummelerSpot.z - 3.f, kPocketBoxMaxZ));
        return arena;
    }

    inline Arena RoomArena()
    {
        Arena arena(PolygonRegion(kRoomPolygon, kRoomZMin, kRoomZMax));
        arena.Add(ArenaRegion::Circle(kRoomCenter.XY(), kRoomBowlRadius, kRoomZMin, kRoomZMax));
        return arena;
    }

    // The platform's pick disc (inside the platform arena).
    inline Arena PlatformPickArena()
    {
        return Arena(ArenaRegion::Circle(kPlatformCenter.XY(), kPlatformPickRadius, kPlatformZMin, kPlatformZMax));
    }

    // The arena of a slot (the hard mode is Thermaplugg's room).
    inline Arena ArenaFor(std::uint32_t slot)
    {
        switch (slot)
        {
            case BOSS_ALERT_SYSTEM:
                return HallArena();
            case BOSS_VISCOUS_FALLOUT:
                return CaveArena();
            case BOSS_TECHBOT:
                return DishArena();
            case BOSS_ELECTROCUTIONER:
                return PlatformArena();
            case BOSS_CROWD_PUMMELER:
                return PummelerArena();
            case BOSS_THERMAPLUGG:
            case BOSS_WHOLE_WORKSHOP:
                return RoomArena();
            default:
                return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Health (section 3.6, section 7 #1 A: normal x2.0 of the spec, heroic and hard mode x4/3). Normal = the engine's
    // ceil(853 x HealthModifier) of the DT rows (the S0 stubs; the boss WPs own them now); heroic = WP-H's overrides.
    // A boss WP reads these and never restates one.
    // ----------------------------------------------------------------------------------------------------------------
    struct ReferenceRow
    {
        std::uint32_t nonTank;
        std::uint32_t tank;
    };
    // BM conf ReferenceHealth.MapLevels "90:28 90h:60" (section 7 #4 A, interpolated). Host arithmetic only.
    ReferenceRow constexpr kReferenceNormal{ 1694, 1707 };
    ReferenceRow constexpr kReferenceHeroic{ 4120, 4110 };

    std::uint32_t constexpr kBaseHealthWarrior28 = 853;     // creature_classlevelstats, level 28, exp 0
    std::uint32_t constexpr kBaseHealthCaster28 = 732;

    namespace Health
    {
        NH<std::uint32_t> constexpr kTechbot{ 60001, 333333 };          // 70.34 on 853 (spec 30,000 / 250,000)
        NH<std::uint32_t> constexpr kViscousFallout{ 65997, 466667 };   // 77.37 (spec 33,000 / 350,000)
        NH<std::uint32_t> constexpr kElectrocutioner{ 68002, 400000 };  // 79.72 (spec 34,000 / 300,000)
        NH<std::uint32_t> constexpr kAlertSystem{ 56000, 333333 };      // 65.65 (spec 28,000 / 250,000)
        NH<std::uint32_t> constexpr kCrowdPummeler{ 60001, 373333 };    // 70.34 (spec 30,000 / 280,000)
        NH<std::uint32_t> constexpr kThermaplugg{ 80003, 466667 };      // 93.79 (spec 40,000 / 350,000)
        std::uint32_t constexpr kWholeWorkshop = 800000;                // section 7 #1 A (spec 600,000 x4/3)
        NH<std::uint32_t> constexpr kDarkIronAmbassador{ 42017, 260000 };   // 57.4 on 732 (section 7 #41 A; WP-H)

        // Unscaled kit units (LESSONS 1 #5): the spec's numbers.
        NH<std::uint32_t> constexpr kDupeBug{ 300, 4000 };
        NH<std::uint32_t> constexpr kSecurityAssistant{ 450, 6000 };
        NH<std::uint32_t> constexpr kSecurityDefender{ 1200, 12000 };
        NH<std::uint32_t> constexpr kWalkingBomb{ 400, 5000 };
        std::uint32_t constexpr kWalkingBombHardMode = 7000;
    }

    // The normal HealthModifier of each slot's DT row (S0's stubs; the boss WPs own the rows now).
    namespace HealthModifier
    {
        float constexpr kTechbot = 70.34f;
        float constexpr kViscousFallout = 77.37f;
        float constexpr kElectrocutioner = 79.72f;
        float constexpr kAlertSystem = 65.65f;
        float constexpr kCrowdPummeler = 70.34f;
        float constexpr kThermaplugg = 93.79f;
    }

    // Section 3.5 rule 24: no hit under a 1.5 s warning on normal (SYS 4).
    std::uint32_t constexpr kWarningFloorMs = 1500;

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string (section 3.2 item 2): header "GNR" (the stock "G N O" shares its first two characters:
    // a stock "G N O <n>" fails at "O" and goes to the stock reader), the 7 boss states, then the extras. New fields go
    // in as new extras (an older save loads them as 0).
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "GNR";
    char constexpr kStockSaveHeader[] = "GNO";

    enum SaveExtra : std::size_t
    {
        EXTRA_WORKSHOP_DOOR     = 0,    // WorkshopDoorState
        EXTRA_HARD_MODE         = 1,    // the console's flag
        EXTRA_PUMMELER_CHEST    = 2,    // PummelerChestState
        EXTRA_SECTION           = 3,    // the run's Finder section (0, 1, 2)
    };
    std::size_t constexpr kSaveExtraCount = 4;

    using BossStates = std::array<std::uint32_t, kBossCount>;

    struct GnrSave
    {
        BossStates states{};
        std::uint32_t workshopDoor = WORKSHOP_DOOR_SEALED;
        std::uint32_t hardMode = 0;
        std::uint32_t pummelerChest = PUMMELER_CHEST_NONE;
        std::uint32_t section = 0;
    };

    inline std::string FormatGnrSave(GnrSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_WORKSHOP_DOOR] = s.workshopDoor;
        extras[EXTRA_HARD_MODE] = s.hardMode;
        extras[EXTRA_PUMMELER_CHEST] = s.pummelerChest;
        extras[EXTRA_SECTION] = s.section;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The states a completed-encounter mask records (DONE): bits 0 to 5 are slots 0 to 5.
    inline void ApplyEncounterMask(std::uint32_t mask, BossStates& states)
    {
        for (std::uint32_t bit = 0; bit < kEncounterBossCount; ++bit)
            if (mask & (1u << bit))
                states[bit] = DungeonKit::State::Done;
    }

    // One consistent run (states already through SanitizeLoadedState): slot 6 only with slot 5 DONE and the flag;
    // the door at least what the slots give; the chest only with slot 4 DONE (placed again on load unless looted);
    // flags and the section back in range.
    inline void SanitizeGnrSave(GnrSave& s)
    {
        s.hardMode = s.hardMode ? 1 : 0;
        if (s.states[BOSS_THERMAPLUGG] != DungeonKit::State::Done || !s.hardMode)
            s.states[BOSS_WHOLE_WORKSHOP] = DungeonKit::State::NotStarted;
        std::uint32_t const door = s.workshopDoor <= WORKSHOP_DOOR_OPEN ? s.workshopDoor
            : std::uint32_t(WORKSHOP_DOOR_SEALED);
        s.workshopDoor = RaiseWorkshopDoor(door, door, s.states[BOSS_ELECTROCUTIONER], s.states[BOSS_ALERT_SYSTEM]);
        if (s.states[BOSS_CROWD_PUMMELER] != DungeonKit::State::Done)
            s.pummelerChest = PUMMELER_CHEST_NONE;
        else if (s.pummelerChest != PUMMELER_CHEST_LOOTED)
            s.pummelerChest = PUMMELER_CHEST_PLACED;
        if (s.section > kSections.size())
            s.section = 0;
    }

    // The stock save (instance_gnomeregan.cpp at aa32e0dde: SetHeaders("GNO"), no boss states, then "<grubbis>"): its
    // one field is dropped (Grubbis is gone); the completed-encounter mask gives the slots (stock wrote none, so it is
    // 0 in practice: the live "G N O 0" row loads as a fresh run). False on anything else.
    inline bool ReadStockSave(std::string const& in, std::uint32_t encounterMask, GnrSave& out)
    {
        std::vector<std::uint32_t> fields;
        if (!DungeonKit::ReadSaveFields(in, kStockSaveHeader, 1, 1, fields))
            return false;
        out = GnrSave{};
        ApplyEncounterMask(encounterMask, out.states);
        return true;
    }

    // Reads this script's "G N R" string or the stock "G N O" one; `encounterMask` is the instance's
    // completed-encounter mask (Map::CreateInstanceData sets it before Load), applied to a stock save only. False on
    // anything else (ignored).
    inline bool ParseGnrSave(std::string const& in, GnrSave& out, std::uint32_t encounterMask = 0)
    {
        out = GnrSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        GnrSave stockSave;
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
            out.workshopDoor = raw.extras[EXTRA_WORKSHOP_DOOR];
            out.hardMode = raw.extras[EXTRA_HARD_MODE];
            out.pummelerChest = raw.extras[EXTRA_PUMMELER_CHEST];
            out.section = raw.extras[EXTRA_SECTION];
        }
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        SanitizeGnrSave(out);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Section 3.5 rule 29 (LESSONS L1): every boss calls NoAssist (GnomereganKit.h) each UpdateAI, before
    // UpdateVictim. The files of the boss WPs (host-tested: each `struct boss_...` in them has a
    // GnomereganRework::NoAssist(me) call; every boss_*.cpp of the folder is listed).
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<char const*, 6> constexpr kBossFiles{ {
        "boss_techbot_rework.cpp", "boss_viscous_fallout_rework.cpp", "boss_electrocutioner_rework.cpp",
        "boss_mobile_alert_system_rework.cpp", "boss_crowd_pummeler_rework.cpp", "boss_thermaplugg_rework.cpp",
    } };

    // A slot's state, TO_BE_DECIDED read as NOT_STARTED (before the first Update settles it).
    constexpr std::uint32_t SettledSlotState(std::uint32_t state)
    {
        return state == DungeonKit::State::ToBeDecided ? DungeonKit::State::NotStarted : state;
    }
}

#endif
