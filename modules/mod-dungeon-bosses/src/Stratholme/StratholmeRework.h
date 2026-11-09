/*
 * mod-dungeon-bosses, Stratholme (map 329): the shared ids, boss states, data fields, texts, measured points, frames,
 * arenas, the save string and the instance rules of the Stratholme build
 * (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md sections 3.1-3.3, 3.7, 3.8 and the user rulings of
 * section 10; build spec docs/dungeons/stratholme-rework.md, "ST").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h), so
 * every <Boss>Logic.h and its host test can include it. Engine glue: the shared kit (src/Kit/DungeonKit.h) and the
 * Stratholme glue (StratholmeKit.h).
 *
 * Ownership: this file belongs to WP-S0 (the Stratholme skeleton) until it reports, then to the orchestrator. A boss WP
 * keeps its own spell ids (inside its slice below), tuning constants and script-local enums in its own <Boss>Logic.h
 * (convention: `enum <Boss>Spells : std::uint32_t { SPELL_<BOSS>_... = <id in its slice> }` and
 * `inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), and asks the orchestrator, in its report, for any
 * change here.
 *
 * Measured points, frames and arenas are [navmesh estimate] (stratholme-build.NAVMESH-REPORT.md: the mesh sits about
 * 0.53 yd inside every wall) unless marked [db] (creature or gameobject rows, exact). Axes: +x north, +y west. A boss
 * WP may tighten its own arena in its own file; the playtest guide checks the key points with `.gps`.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_REWORK_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_REWORK_H

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

namespace StratholmeRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Box2;
    using DungeonKit::FrameRect;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapStratholme = 329;
    // The stock instance name (handoff section 10, ruling on section 7 #2): the rework replaces the stock
    // InstanceMapScript of that name at load (same-named scripts registered later win; modules load after the core
    // scripts), so instance_template is untouched and the stock Jarien, Sothos and go_enchanted_scarlet_thread
    // (GetStratholmeAI checks this name) keep working with no copies.
    char constexpr kInstanceScriptName[] = "instance_stratholme";
    // `.dbtest strat <boss> <mechanic>` (handoff section 3.2 item 4): the K0 shell's command name; the chat command map
    // splits it at the space, so it nests under the shared `.dbtest` root (StratholmeTestCommand.cpp).
    char constexpr kTestCommand[] = "dbtest strat";
    char constexpr kLogDungeon[] = "strat";         // DungeonKit::LogMechanic("strat", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The order is fixed: the save string stores them by position. Slots 2 and 3 belong to
    // the stock event bosses Jarien and Sothos: boss_jarien / boss_sothos are BossAI on stratholme.h DATA_JARIEN (2)
    // and DATA_SOTHOS (3), so their engage, reset and death write those slots; no reworked boss may sit there (the SFK
    // Hummel and Scholomance Gandling lesson). 15 and 16 are the two hard mode kills.
    // ----------------------------------------------------------------------------------------------------------------
    enum StratholmeBosses : std::uint32_t
    {
        BOSS_UNFORGIVEN     = 0,    // S1, wave 2
        BOSS_FORRESTEN      = 1,    // S2, wave 2
        BOSS_JARIEN         = 2,    // stock boss_jarien (event boss, kept stock)
        BOSS_SOTHOS         = 3,    // stock boss_sothos (event boss, kept stock)
        BOSS_TIMMY          = 4,    // S3, wave 2
        BOSS_WILLEY         = 5,    // S5, wave 2
        BOSS_MALOR          = 6,    // S4, wave 2
        BOSS_GALFORD        = 7,    // S6, wave 2
        BOSS_BALNAZZAR      = 8,    // S7, wave 2 (Dathrohan 10812 and Balnazzar 10813, one encounter)
        BOSS_BARONESS       = 9,    // S10, ziggurat 1
        BOSS_NERUBENKAN     = 10,   // S11, ziggurat 2
        BOSS_MALEKI         = 11,   // S12, ziggurat 3
        BOSS_BARTHILAS      = 12,   // S9
        BOSS_RAMSTEIN       = 13,   // S13
        BOSS_BARON          = 14,   // S14
        BOSS_GRAND_LIE      = 15,   // S8: Balnazzar killed with DATA_GRAND_LIE lit (set by the instance)
        BOSS_ULTIMATUM      = 16,   // S15: the Baron killed with DATA_ULTIMATUM lit (set by the instance)
    };
    std::uint32_t constexpr kBossCount = 17;
    std::uint32_t constexpr kStockJarienBossId = 2;     // stratholme.h DATA_JARIEN
    std::uint32_t constexpr kStockSothosBossId = 3;     // stratholme.h DATA_SOTHOS
    static_assert(BOSS_JARIEN == kStockJarienBossId, "the stock Jarien BossAI writes boss slot 2");
    static_assert(BOSS_SOTHOS == kStockSothosBossId, "the stock Sothos BossAI writes boss slot 3");
    static_assert(BOSS_ULTIMATUM + 1 == kBossCount, "every boss state has a slot");

    // Names by boss state id (`.dbtest strat state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "The Unforgiven", "Hearthsinger Forresten", "Jarien (event)", "Sothos (event)", "Timmy the Cruel",
        "Cannon Master Willey", "Malor the Zealous", "Archivist Galford", "Dathrohan and Balnazzar",
        "Baroness Anastari", "Nerub'enkan", "Maleki the Pallid", "Magistrate Barthilas", "Ramstein the Gorger",
        "Baron Rivendare", "The Grand Lie (Balnazzar hard mode)", "The Ultimatum (Baron hard mode)" } };

    // The stock event bosses keep their stock AI; the two hard mode slots are written by the instance only.
    constexpr bool IsStockEventBoss(std::uint32_t bossId)
    {
        return bossId == BOSS_JARIEN || bossId == BOSS_SOTHOS;
    }

    constexpr bool IsHardModeSlot(std::uint32_t bossId)
    {
        return bossId == BOSS_GRAND_LIE || bossId == BOSS_ULTIMATUM;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Wave switch (handoff section 10: wave 1 is the Service Entrance, wave 2 the Main Gate; the Scholomance pattern).
    // Until wave 2 flips it, the Main Gate bosses keep their stock ScriptName, AIName, SmartAI and health (the DT twin
    // BIND_WAVE_2 in apps/dbc-tools source/npcs/stratholme/_common.py must agree: lib/test_stratholme_kit.py), their
    // stub C++ stays registered but bound to nothing, and the instance treats them as stock: a stock boss's death sets
    // its boss state DONE (OnUnitDeath), and the wave 2 instance code (DATA_GRAND_LIE, the relic spawns) stays off.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr bool kWave2Bound = false;

    constexpr bool IsWave2Boss(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_UNFORGIVEN:
            case BOSS_FORRESTEN:
            case BOSS_TIMMY:
            case BOSS_WILLEY:
            case BOSS_MALOR:
            case BOSS_GALFORD:
            case BOSS_BALNAZZAR:
            case BOSS_GRAND_LIE:
                return true;
            default:
                return false;
        }
    }

    // A reworked boss whose wave is bound (the event bosses are never reworked).
    constexpr bool IsReworkBound(std::uint32_t bossId, bool wave2Bound = kWave2Bound)
    {
        if (bossId >= kBossCount || IsStockEventBoss(bossId))
            return false;
        return !IsWave2Boss(bossId) || wave2Bound;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids above)
    // ----------------------------------------------------------------------------------------------------------------
    enum StratholmeData : std::uint32_t
    {
        // Stock ids (stratholme.h DataTypes), kept with their meanings for the stock SmartAI and mod-dungeon-clear:
        DATA_BARON_RUN              = 0,    // the Gauntlet Gate's SmartAI (SetData(0, 1)): starts the 45 min clock
        DATA_ZIGGURAT1              = 1,    // the Baroness's ziggurat: 1 = boss dead (door), 2 = crystal shattered
        DATA_ZIGGURAT2              = 2,    // Nerub'enkan's
        DATA_ZIGGURAT3              = 3,    // Maleki's (all three at 2: the Gauntlet and Slaughter gates open)
        DATA_BARON_FIGHT            = 4,    // stock: IN_PROGRESS closes the Baron's door; BOSS_BARON does it too
        DATA_MALLOW                 = 5,    // the postboxes' SmartAI: one more opened
        DATA_BARTHILAS_RUN          = 6,    // stock: Barthilas's run (retired by S9); stored and saved only
        DATA_SCARLET_THREAD_LOOTED  = 7,    // SetGuidData from the stock go_enchanted_scarlet_thread
        // New (20 on):
        DATA_ULTIMATUM              = 20,   // SetData(20, 1): Ysida's gossip opts in to the Baron's hard mode (S15's
                                            // SmartAI row); heroic, the Baron Run clock running, the Baron neither
                                            // fighting nor dead; 0 clears it (not while he fights). Saved. Cleared
                                            // when she is executed at the end of the clock and when he dies
        DATA_GRAND_LIE              = 21,   // SetData(21, 1): the Letter of Proof lights Balnazzar's hard mode (S8);
                                            // heroic, wave 2 bound, Balnazzar neither fighting nor dead. Saved.
                                            // Stays lit through wipes; cleared when he dies
        DATA_SLAUGHTER_STAGE        = 22,   // GetData only: the slaughter event's stage (SlaughterStage)
        DATA_BARON_RUN_MINUTES      = 23,   // GetData: minutes left on the clock (0: none or out). SetData (GM test,
                                            // `.dbtest strat instance clock`): set the minutes left while it runs
        DATA_ZIGGURAT_PENDING       = 24,   // GetData only: a mask of ziggurats whose crystal broke before their boss
                                            // died (the softlock fix, bit 0 = ziggurat 1)
    };

    // SetGuidData / GetGuidData ids. ObjectData ids for units and objects that are never summoned twice
    // (cpp-scripts.md, the ObjectData pitfall): the twelve spawned bosses, Ysida, her cage and the exit gate. Never
    // Ramstein (the instance summons him), Balnazzar (Dathrohan's UpdateEntry), the Black Guards, the meat, skeletons,
    // rats, playmates, riflemen, phantoms, Infernals, cocoons, tombs or crawlers.
    enum StratholmeObjects : std::uint32_t
    {
        DATA_UNFORGIVEN_GUID        = 100,
        DATA_FORRESTEN_GUID         = 101,
        DATA_TIMMY_GUID             = 102,
        DATA_WILLEY_GUID            = 103,
        DATA_MALOR_GUID             = 104,
        DATA_GALFORD_GUID           = 105,
        DATA_DATHROHAN_GUID         = 106,      // Balnazzar after the transform (same unit)
        DATA_BARONESS_GUID          = 107,
        DATA_NERUBENKAN_GUID        = 108,
        DATA_MALEKI_GUID            = 109,
        DATA_BARTHILAS_GUID         = 110,
        DATA_BARON_GUID             = 111,
        DATA_YSIDA_GUID             = 112,

        DATA_YSIDA_CAGE_GUID        = 120,
        DATA_EXIT_GATE_GUID         = 121,
        DATA_RAMSTEIN_GUID          = 130,      // GetGuidData only: the summoned Ramstein (tracked by hand)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum StratholmeCreatures : std::uint32_t
    {
        // bosses (stock entries; script names bound by apps/dbc-tools source/npcs/stratholme/<boss>.py)
        NPC_UNFORGIVEN              = 10516,    // boss_the_unforgiven_rework (wave 2)
        NPC_FORRESTEN               = 10558,    // boss_hearthsinger_forresten_rework (wave 2)
        NPC_TIMMY                   = 10808,    // boss_timmy_the_cruel_rework (wave 2)
        NPC_MALOR                   = 11032,    // boss_malor_the_zealous_rework (wave 2)
        NPC_WILLEY                  = 10997,    // boss_cannon_master_willey_rework (wave 2)
        NPC_GALFORD                 = 10811,    // boss_archivist_galford_rework (wave 2)
        NPC_DATHROHAN               = 10812,    // boss_dathrohan_balnazzar_rework (wave 2)
        NPC_BALNAZZAR               = 10813,    // boss_dathrohan_balnazzar_rework (wave 2; the transform's entry)
        NPC_BARTHILAS               = 10435,    // boss_magistrate_barthilas_rework
        NPC_BARONESS                = 10436,    // boss_baroness_anastari_rework (the stock boss_baroness_anastari
                                                // stays registered, unbound)
        NPC_NERUBENKAN              = 10437,    // boss_nerubenkan_rework
        NPC_MALEKI                  = 10438,    // boss_maleki_the_pallid_rework
        NPC_RAMSTEIN                = 10439,    // boss_ramstein_the_gorger_rework (summoned by the slaughter event)
        NPC_BARON                   = 10440,    // boss_baron_rivendare_rework

        // stock units the instance or the kit uses
        NPC_YSIDA                   = 16031,    // Ysida Harmon (stock SmartAI; S15 adds a gossip select row)
        NPC_JARIEN                  = 16101,    // stock boss_jarien (slot 2)
        NPC_SOTHOS                  = 16102,    // stock boss_sothos (slot 3)
        NPC_BILE_SPEWER             = 10416,    // the slaughter event's abominations
        NPC_VENOM_BELCHER           = 10417,
        NPC_BLACK_GUARD             = 10394,    // Black Guard Sentry (the slaughter event's last stage)
        NPC_PLAGUED_RAT             = 10441,    // the gate traps' critters
        NPC_PLAGUED_INSECT          = 10461,
        NPC_PLAGUED_MAGGOT          = 10536,
        NPC_ASH_ARI_CRYSTAL         = 10415,
        NPC_THUZADIN_ACOLYTE        = 10399,
        NPC_AURIUS                  = 10917,
        // stock-id boss-kit adds (each boss's alone; handoff section 1 table)
        NPC_VENGEFUL_PHANTOM        = 10387,    // The Unforgiven (S1)
        NPC_CRIMSON_RIFLEMAN        = 11054,    // Willey (S5)
        NPC_UNDEAD_SCARAB           = 10876,    // Nerub'enkan (S11)
        NPC_MINDLESS_UNDEAD         = 11030,    // Ramstein's meat (S13)
        NPC_MINDLESS_SKELETON       = 11197,    // the Baron (S14)

        // new boss-kit creatures (ids.yaml reservation `stratholme`, 300580-300649; declared by the boss WPs in
        // apps/dbc-tools source/npcs/stratholme/). Wave 1 300580-300599, wave 2 300600-300619 (the heroic mint order).
        NPC_ST_GRAIN_PILE           = 300580,   // S9: grain pile / cough puddle stalker
        NPC_ST_WARD                 = 300581,   // S9: ward stalker
        NPC_ST_WEB_COCOON           = 300582,   // S11: Web Cocoon (display 16213), combat add
        NPC_ST_WEB_PATCH            = 300583,   // S11: web patch stalker
        NPC_ST_ICE_TOMB             = 300584,   // S12: Ice Tomb (display 30890, rescaled), combat add
        NPC_ST_EYE                  = 300585,   // S12: eye stalker (heroic)
        NPC_ST_HALF_DIGESTED_CORPSE = 300586,   // S13: crawler, combat add
        NPC_ST_GUT_PUDDLE           = 300587,   // S13: gut puddle stalker
        NPC_ST_ROT                  = 300588,   // S14 / S15: rot stalker (Death and Decay, the Deathcharger trail)
        NPC_ST_YSIDA_RISEN          = 300589,   // S15: Ysida, Risen (40k, hard mode only, no heroic template)
        NPC_ST_SPECTRAL_FOOTMAN     = 300600,   // S1: rank and cordon (display 30978, unattackable)
        NPC_ST_HOUSE_FIRE           = 300601,   // S1: house fire stalker
        NPC_ST_GUTTER_RAT           = 300602,   // S2: Gutter Rat, combat add
        NPC_ST_HEARTH               = 300603,   // S2: hearth stalker
        NPC_ST_PLAYMATE             = 300604,   // S3: Playmate, combat add
        NPC_ST_MEDALLION            = 300605,   // S4: Medallion stalker
        NPC_ST_HOLY_FIRE_PUDDLE     = 300606,   // S6: holy fire puddle stalker
        NPC_ST_PYRE_WALL            = 300607,   // S6: Pyre and north wall stalker
        NPC_ST_INFERNAL             = 300608,   // S7: Infernal (display 7029), combat add
        NPC_ST_SWARM                = 300609,   // S8: moving swarm stalker (hard mode)
    };

    // The boss state of a boss entry (a heroic copy's GetEntry() is its base entry); nullopt for anything else. The
    // stock event bosses (Jarien, Sothos) are BossAI and write their own slots, so they are not listed.
    constexpr std::optional<std::uint32_t> BossOfEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_UNFORGIVEN:    return BOSS_UNFORGIVEN;
            case NPC_FORRESTEN:     return BOSS_FORRESTEN;
            case NPC_TIMMY:         return BOSS_TIMMY;
            case NPC_WILLEY:        return BOSS_WILLEY;
            case NPC_MALOR:         return BOSS_MALOR;
            case NPC_GALFORD:       return BOSS_GALFORD;
            case NPC_DATHROHAN:
            case NPC_BALNAZZAR:     return BOSS_BALNAZZAR;
            case NPC_BARONESS:      return BOSS_BARONESS;
            case NPC_NERUBENKAN:    return BOSS_NERUBENKAN;
            case NPC_MALEKI:        return BOSS_MALEKI;
            case NPC_BARTHILAS:     return BOSS_BARTHILAS;
            case NPC_RAMSTEIN:      return BOSS_RAMSTEIN;
            case NPC_BARON:         return BOSS_BARON;
            default:                return std::nullopt;
        }
    }

    constexpr bool IsStratBossEntry(std::uint32_t entry)
    {
        return BossOfEntry(entry).has_value();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum StratholmeGameObjects : std::uint32_t
    {
        // stock (stratholme.h GameobjectIds and the gates of handoff section 2.3)
        GO_CRUSADER_SQUARE_DOOR     = 175967,   // the Bastion Door (lock 1634)
        GO_HOARD_DOOR               = 175968,
        GO_HALL_OF_HIGH_COMMAND     = 176194,
        GO_GAUNTLET_DOOR_1          = 175357,   // Gauntlet Gate (lock 879; its SmartAI starts the Baron Run)
        GO_GAUNTLET_DOOR_2          = 175356,
        GO_ZIGGURAT_DOORS1          = 175380,   // the Baroness's
        GO_ZIGGURAT_DOORS2          = 175379,   // Nerub'enkan's
        GO_ZIGGURAT_DOORS3          = 175381,   // Maleki's
        GO_ZIGGURAT_DOORS4          = 175405,   // Ramstein's pen
        GO_ZIGGURAT_DOORS5          = 175796,   // the Baron's door
        GO_GAUNTLET_GATE            = 175374,
        GO_SLAUGHTER_GATE           = 175373,
        GO_SLAUGHTER_GATE_SIDE      = 175358,   // Slaughter Square Gate (the meat's passage)
        GO_EXIT_GATE                = 176424,
        GO_PORT_TRAP_GATE_1         = 175351,   // the rat trap portcullises (scarlet side)
        GO_PORT_TRAP_GATE_2         = 175350,
        GO_PORT_TRAP_GATE_3         = 175355,   // (undead side)
        GO_PORT_TRAP_GATE_4         = 175354,
        GO_SERVICE_ENTRANCE_GATE    = 175368,   // lock 879; opened on create (handoff section 10, section 7 #4)
        GO_BARTHILAS_PORTCULLIS_1   = 175377,   // closed while Barthilas fights (door data)
        GO_BARTHILAS_PORTCULLIS_2   = 175372,
        GO_YSIDA_CAGE               = 181071,
        GO_SCARLET_ARCHIVE          = 176245,   // untouched (Galford)
        GO_MALORS_STRONGBOX         = 176112,   // untouched (Malor)
        GO_SCARLET_CANNON_EAST      = 176216,   // stock cannons, replaced in the fight by Mercy and Zeal (S5)
        GO_SCARLET_CANNON_WEST      = 176217,
        GO_CANNONBALL_STACK         = 176215,
        GO_SUPPLY_CRATE_HOLY_WATER  = 176224,
        GO_JARIEN_AND_SOTHOS_HEIRLOOMS = 181083,

        // new (ids.yaml reservation `stratholme`, 301200-301249; templates and spawns in the boss WPs' SQL revs)
        GO_ST_MERCY                 = 301200,   // S5 (east half, in front of 176216)
        GO_ST_ZEAL                  = 301201,   // S5 (west half, in front of 176217)
        GO_ST_CANNONBALL            = 301202,   // S5: the dropped Scarlet Cannonball (GO display 153)
        GO_ST_LETTER_OF_PROOF       = 301203,   // S8: by the Scarlet Archive (heroic, Galford's DONE)
        GO_ST_SCARLET_STANDARD      = 301204,   // S8: Willey's yard (heroic, Willey's DONE)
        GO_ST_MEDALLION_LIGHT       = 301205,   // S8: at Malor's strongbox (heroic, Malor's DONE)
        GO_ST_BLESSED_CRATE         = 301206,   // S8: Crusaders' Square (spawnMask 2)
        GO_ST_BONE_PILE             = 301207,   // S14: bone pile (GO displays 6328 / 6329)
    };

    // The relic items of Balnazzar's hard mode (S8; hand-picked `item` block, after the Haunted tokens).
    enum StratholmeItems : std::uint32_t
    {
        ITEM_ENCHANTED_SCARLET_THREAD = 12734,  // stock quest item (the scarlet thread spawner)
        ITEM_ST_LETTER_OF_PROOF     = 70600,
        ITEM_ST_SCARLET_STANDARD    = 70601,
        ITEM_ST_BLESSED_HOLY_WATER  = 70602,
        ITEM_ST_RELIC_OF_THE_MEDALLION = 70603,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 206400-206799, ids.yaml reservation `stratholme`; declared in apps/dbc-tools
    // source/npcs/stratholme/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h. The kit-wide
    // 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h).
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 206400, 206799 };
    IdSlice constexpr kSpellsShared{ 206400, 206419 };          // lethal wall strike, Terrified, shared cast bars
    IdSlice constexpr kSpellsUnforgiven{ 206420, 206439 };      // S1  (UF)
    IdSlice constexpr kSpellsForresten{ 206440, 206459 };       // S2  (HF)
    IdSlice constexpr kSpellsTimmy{ 206460, 206479 };           // S3  (TC)
    IdSlice constexpr kSpellsMalor{ 206480, 206499 };           // S4  (MZ)
    IdSlice constexpr kSpellsWilley{ 206500, 206519 };          // S5  (WY)
    IdSlice constexpr kSpellsGalford{ 206520, 206544 };         // S6  (GF)
    IdSlice constexpr kSpellsDathrohan{ 206545, 206574 };       // S7  (DB / BZ)
    IdSlice constexpr kSpellsGrandLie{ 206575, 206604 };        // S8  (Balnazzar hard mode, relic use spells)
    IdSlice constexpr kSpellsBarthilas{ 206605, 206624 };       // S9  (BT)
    IdSlice constexpr kSpellsBaroness{ 206625, 206644 };        // S10 (BA)
    IdSlice constexpr kSpellsNerubenkan{ 206645, 206664 };      // S11 (NE)
    IdSlice constexpr kSpellsMaleki{ 206665, 206684 };          // S12 (MK)
    IdSlice constexpr kSpellsRamstein{ 206685, 206704 };        // S13 (RG)
    // The handoff's "BR and its hard mode 206705-206734", split so S14 and S15 never share an id. The boss Condemned
    // is its own id in kSpellsUltimatum, never the W1 item effect 205669 (handoff section 11 #1).
    IdSlice constexpr kSpellsBaron{ 206705, 206719 };           // S14 (BR)
    IdSlice constexpr kSpellsUltimatum{ 206720, 206734 };       // S15 (HM)
    IdSlice constexpr kSpellsSpare{ 206735, 206799 };

    inline std::array<IdSlice, 17> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsUnforgiven, kSpellsForresten, kSpellsTimmy, kSpellsMalor, kSpellsWilley, kSpellsGalford,
        kSpellsDathrohan, kSpellsGrandLie, kSpellsBarthilas, kSpellsBaroness, kSpellsNerubenkan, kSpellsMaleki,
        kSpellsRamstein, kSpellsBaron, kSpellsUltimatum, kSpellsSpare } };

    IdSlice constexpr kCreaturesReservation{ 300580, 300649 };
    IdSlice constexpr kCreaturesWave1{ 300580, 300599 };
    IdSlice constexpr kCreaturesWave2{ 300600, 300649 };
    IdSlice constexpr kGameObjectsReservation{ 301200, 301249 };
    IdSlice constexpr kRelicItems{ 70600, 70603 };

    // Stock spells the build specs keep or read (DD scales the kept ones on heroic; handoff section 3.6).
    enum StratholmeStockSpells : std::uint32_t
    {
        SPELL_BARON_ULTIMATUM       = 27861,    // the Baron Run's clock aura on players (stock)
        // kept kits
        SPELL_SHOOT_FORRESTEN       = 16100,
        SPELL_MULTI_SHOT            = 14443,
        SPELL_THRASH                = 12787,
        SPELL_RAVENOUS_CLAW         = 17470,
        SPELL_ENRAGE_TIMMY          = 8599,
        SPELL_KNOCK_AWAY            = 10101,
        SPELL_PUMMEL                = 15615,
        SPELL_SHOOT_RIFLEMAN        = 17353,
        SPELL_CRUSADER_STRIKE       = 17281,
        SPELL_HOLY_STRIKE           = 17284,
        SPELL_MIND_BLAST_BALNAZZAR  = 17287,
        SPELL_SHADOW_SHOCK_BALNAZZAR = 17288,
        SPELL_SLEEP_BALNAZZAR       = 17398,
        SPELL_MIGHTY_BLOW           = 14099,
        SPELL_DRAINING_BLOW         = 16793,
        SPELL_TRANSFORMATION        = 16794,    // Barthilas
        SPELL_BANSHEE_WAIL          = 16565,
        SPELL_PIERCE_ARMOR          = 6016,     // Nerub'enkan's stock Pierce Armor (handoff section 3.6)
        SPELL_POISON_PROC           = 13299,    // Undead Scarab
        SPELL_FROSTBOLT_MALEKI      = 17503,
        SPELL_FLURRY                = 15088,    // Ramstein's Flurry (handoff section 3.6)
        SPELL_SHADOW_BOLT_BARON     = 17393,
        SPELL_MORTAL_STRIKE         = 15708,
        SPELL_CLEAVE                = 15284,    // live at 10% weapon damage (ST note 4; not this build's to fix)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // creature_text groups (ST "Text" tables). Texts are inserted by each boss WP's own SQL rev; stock lines stay.
    // Mechanic emotes are type 41 (the Pilot lesson).
    // ----------------------------------------------------------------------------------------------------------------
    enum BarthilasTexts : std::uint8_t          // ST 2390-2400; group 0 stock
    {
        SAY_BARTHILAS_AGGRO         = 0,        // stock "Intruders at the Service Gate!", now on aggro
        EMOTE_BARTHILAS_COUGH       = 1,        // BT1
        YELL_BARTHILAS_QUARANTINE   = 2,        // BT6
        YELL_BARTHILAS_BEDLAM       = 3,        // heroic BT9
        YELL_BARTHILAS_GRAIN        = 4,        // BT4, now and then
        YELL_BARTHILAS_DEATH        = 5,
    };

    enum BaronessTexts : std::uint8_t           // ST 2660-2670
    {
        YELL_BARONESS_AGGRO         = 0,
        EMOTE_BARONESS_KEEN         = 1,        // BA1
        EMOTE_BARONESS_WAIL         = 2,        // BA4
        EMOTE_BARONESS_VEIL         = 3,        // BA6
        YELL_BARONESS_LAMENT        = 4,        // heroic BA7
        YELL_BARONESS_DEATH         = 5,
    };

    enum NerubenkanTexts : std::uint8_t         // ST 2893-2903
    {
        YELL_NERUBENKAN_AGGRO       = 0,
        EMOTE_NERUBENKAN_WEB        = 1,        // NE1
        EMOTE_NERUBENKAN_COCOON     = 2,        // NE4
        EMOTE_NERUBENKAN_SKITTER    = 3,        // NE6
        YELL_NERUBENKAN_BROOD_CALL  = 4,        // heroic NE7
        YELL_NERUBENKAN_DEATH       = 5,
    };

    enum MalekiTexts : std::uint8_t             // ST 3192-3202
    {
        YELL_MALEKI_AGGRO           = 0,
        EMOTE_MALEKI_CURSE          = 1,        // MK1
        EMOTE_MALEKI_STAFF          = 2,        // MK3
        YELL_MALEKI_COLD            = 3,        // MK5
        EMOTE_MALEKI_FROZEN         = 4,        // MK4
        YELL_MALEKI_DEATH           = 5,
    };

    enum RamsteinTexts : std::uint8_t           // ST 3464-3472; group 0 stock
    {
        YELL_RAMSTEIN_HUNGER        = 0,        // stock, the walk-in
        EMOTE_RAMSTEIN_GORGE        = 1,        // RG2
        EMOTE_RAMSTEIN_STITCHES     = 2,        // RG3
        YELL_RAMSTEIN_DEATH         = 3,
    };

    enum BaronTexts : std::uint8_t              // ST 3879-3897; groups 0-8 stock, kept
    {
        YELL_BARON_RUN_START        = 0,        // stock (the instance: the Baron Run starts)
        YELL_BARON_ZIGGURATS_FALL   = 1,        // stock (the instance: all three crystals broken)
        YELL_BARON_RUN_10M          = 2,        // stock (the instance)
        YELL_BARON_RUN_5M           = 3,        // stock (the instance)
        YELL_BARON_RUN_0M           = 4,        // stock (the instance)
        YELL_BARON_SUMMON_RAMSTEIN  = 5,        // stock (the instance)
        YELL_BARON_GUARDS_DEAD      = 6,        // stock (the instance)
        EMOTE_BARON_RAISE_DEAD      = 7,        // stock (BR1)
        EMOTE_BARON_DEATH_PACT      = 8,        // stock, unused (Death Pact removed)
        YELL_BARON_AGGRO            = 9,
        EMOTE_BARON_ROT             = 10,       // BR3
        YELL_BARON_HARD_MODE_PULL   = 11,       // S15
        EMOTE_BARON_EXECUTION       = 12,       // S15 HM1
        EMOTE_BARON_DEATHCHARGER    = 13,       // S15 HM3
        YELL_BARON_YSIDA_RISES      = 14,       // S15
        YELL_BARON_DEATH            = 15,
    };

    enum YsidaTexts : std::uint8_t              // 16031 groups 0-1 stock
    {
        SAY_YSIDA_OPT_IN            = 2,        // S15: "Don't wait on me. End him, whatever he does to me."
    };

    enum BlackGuardTexts : std::uint8_t
    {
        SAY_BLACK_GUARD_INIT        = 0,        // stock (the instance)
    };

    enum UnforgivenTexts : std::uint8_t         // ST 660-670
    {
        YELL_UNFORGIVEN_AGGRO       = 0,
        YELL_UNFORGIVEN_MARCH       = 1,
        YELL_UNFORGIVEN_ACCUSED     = 2,
        EMOTE_UNFORGIVEN_HOUSE_FIRE = 3,
        YELL_UNFORGIVEN_LAST_SOUL   = 4,
        YELL_UNFORGIVEN_DEATH       = 5,
    };

    enum ForrestenTexts : std::uint8_t          // ST 867-877
    {
        YELL_FORRESTEN_AGGRO        = 0,
        YELL_FORRESTEN_JIG          = 1,
        YELL_FORRESTEN_LULLABY      = 2,
        YELL_FORRESTEN_PIPER        = 3,
        EMOTE_FORRESTEN_CRESCENDO   = 4,
        YELL_FORRESTEN_DEATH        = 5,
    };

    enum TimmyTexts : std::uint8_t              // ST 1073-1085; group 0 stock
    {
        YELL_TIMMY_AGGRO            = 0,        // stock "TIMMY!"
        YELL_TIMMY_TAG              = 1,
        EMOTE_TIMMY_CLAP            = 2,
        YELL_TIMMY_TIMMIES          = 3,
        YELL_TIMMY_JUMP             = 4,
        EMOTE_TIMMY_JUMP_ROPE       = 5,
        YELL_TIMMY_DEATH            = 6,
        YELL_PLAYMATE_TIMMY         = 0,        // on the Playmate entry
    };

    enum MalorTexts : std::uint8_t              // ST 1275-1285
    {
        YELL_MALOR_AGGRO            = 0,
        EMOTE_MALOR_MEDALLION       = 1,
        YELL_MALOR_UNCLEAN          = 2,
        EMOTE_MALOR_WARHAMMER       = 3,
        YELL_MALOR_STRENGTH         = 4,
        YELL_MALOR_DEATH            = 5,
    };

    enum WilleyTexts : std::uint8_t             // ST 1483-1496 (the Barrage's order is a built boss emote)
    {
        YELL_WILLEY_AGGRO           = 0,
        YELL_WILLEY_READY           = 1,
        YELL_WILLEY_AIM             = 2,
        YELL_WILLEY_FIRE            = 3,
        YELL_WILLEY_MERCY_FIRE      = 4,
        YELL_WILLEY_ZEAL_FIRE       = 5,
        YELL_WILLEY_MY_GUNS         = 6,
        YELL_WILLEY_DEATH           = 7,
    };

    enum GalfordTexts : std::uint8_t            // ST 1747-1758
    {
        YELL_GALFORD_AGGRO          = 0,
        EMOTE_GALFORD_FIRE_NOVA     = 1,
        YELL_GALFORD_KINDLED        = 2,
        YELL_GALFORD_PYROBLAST      = 3,
        YELL_GALFORD_ARCHIVE        = 4,
        YELL_GALFORD_BURNING_WINDS  = 5,
        YELL_GALFORD_DEATH          = 6,
    };

    // ST 2135-2156 numbering; section 7 #14: the rows go on the entry that speaks (Dathrohan's on 10812, Balnazzar's
    // on 10813); S7 / S8 keep these numbers or renumber per entry in their own Logic header and say so.
    enum DathrohanBalnazzarTexts : std::uint8_t
    {
        YELL_DATHROHAN_AGGRO        = 0,        // stock
        YELL_DATHROHAN_GATHER_TRUE  = 1,
        YELL_DATHROHAN_BOW_LIE      = 2,
        YELL_DATHROHAN_JUDGMENT_TRUE = 3,
        YELL_DATHROHAN_JUDGMENT_LIE = 4,
        YELL_BALNAZZAR_TRANSFORM    = 5,
        YELL_BALNAZZAR_INFERNO      = 6,
        YELL_BALNAZZAR_DEATH        = 7,        // stock
        SAY_DATHROHAN_LETTER        = 8,        // S8
        YELL_DATHROHAN_MASK         = 9,        // S8
        YELL_BALNAZZAR_CLEAVE_TRUE  = 10,       // S8 HM1
        YELL_BALNAZZAR_CLEAVE_LIE   = 11,
        YELL_BALNAZZAR_RING_TRUE    = 12,       // S8 HM2
        YELL_BALNAZZAR_RING_LIE     = 13,
        YELL_BALNAZZAR_MARK_TRUE    = 14,       // S8 HM3
        YELL_BALNAZZAR_MARK_LIE     = 15,
        YELL_BALNAZZAR_DREAD_SLUMBER = 16,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (handoff section 3.8; stratholme-build.NAVMESH-REPORT.md). Axes: +x north, +y west.
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

    // Boss spawns [db] (creature rows; Ramstein's is the stock summon point).
    Point4 constexpr kUnforgivenSpawn{ 3706.78f, -3412.97f, 132.05f, 2.08f };
    Point4 constexpr kForrestenSpawn{ 3595.75f, -3509.93f, 137.501f, 5.74213f };
    Point4 constexpr kTimmySpawn{ 3624.6f, -3188.0f, 130.579f, 2.99341f };
    Point4 constexpr kMalorSpawn{ 3621.07f, -3126.82f, 135.748f, 2.18166f };
    Point4 constexpr kWilleySpawn{ 3573.57f, -2937.31f, 125.085f, 3.78736f };
    Point4 constexpr kGalfordSpawn{ 3455.96f, -3103.41f, 136.545f, 3.29655f };
    Point4 constexpr kDathrohanSpawn{ 3415.84f, -3044.54f, 136.814f, 5.42797f };
    Point4 constexpr kBarthilasSpawn{ 3663.23f, -3619.14f, 137.984f, 5.34071f };
    Point4 constexpr kBaronessSpawn{ 3855.34f, -3715.75f, 148.175f, 1.27409f };
    Point4 constexpr kNerubenkanSpawn{ 3854.98f, -3528.84f, 144.293f, 5.23599f };
    Point4 constexpr kMalekiSpawn{ 4035.81f, -3647.78f, 135.738f, 2.42601f };
    Point4 constexpr kBaronSpawn{ 4035.83f, -3336.31f, 115.144f, 4.67748f };
    Point4 constexpr kYsidaSpawn{ 4044.05f, -3334.55f, 115.54f, 4.12f };

    // The slaughter event (stock instance_stratholme.cpp, copied positions).
    Point4 constexpr kRamsteinSummon{ 4032.20f, -3378.06f, 119.75f, 4.67f };   // stock SlaughterPos
    Point3 constexpr kRamsteinStop{ 4032.63f, -3399.67f, 115.58f };             // end of his walk-in (report 12)
    Point4 constexpr kMindlessUndeadSpawn{ 3941.75f, -3393.06f, 119.70f, 0.f }; // the meat's spawn (S13 summons it)
    Point3 constexpr kSlaughterRecoveryCenter{ 4034.97f, -3402.13f, 0.f };      // a player this near restarts it
    float constexpr kSlaughterRecoveryRadius = 50.f;
    // Black Guard Sentries: 5 spawn points, then the 5 points they walk to (stock BlackGuardPos).
    inline std::array<Point4, 10> constexpr kBlackGuardPos{ {
        { 4032.73f, -3378.26f, 119.76f, 4.67f }, { 4034.73f, -3376.26f, 119.76f, 4.67f },
        { 4034.73f, -3380.26f, 119.76f, 4.67f }, { 4030.73f, -3376.26f, 119.76f, 4.67f },
        { 4030.73f, -3380.26f, 119.76f, 4.67f },
        { 4032.73f, -3407.38f, 115.56f, 0.f }, { 4034.73f, -3405.38f, 115.56f, 0.f },
        { 4034.73f, -3409.38f, 115.56f, 0.f }, { 4030.73f, -3405.38f, 115.56f, 0.f },
        { 4030.73f, -3409.38f, 115.56f, 0.f } } };
    // The two gate traps (stock aGateTrap): a player within kGateTrapRadius of a point springs it.
    inline std::array<Point4, 2> constexpr kGateTraps{ {
        { 3612.29f, -3335.39f, 124.077f, 3.14159f },    // scarlet side
        { 3919.88f, -3547.34f, 134.269f, 2.94961f } } };// undead side
    float constexpr kGateTrapRadius = 5.5f;

    // Gates and objects [db].
    Point3 constexpr kServiceEntranceGate{ 3624.91f, -3642.16f, 138.445f };
    Point3 constexpr kGauntletGate{ 3727.29f, -3599.08f, 142.22f };
    Point3 constexpr kBaronDoor{ 4032.69f, -3364.54f, 115.054f };
    Point3 constexpr kRamsteinDoor{ 4032.85f, -3388.84f, 119.667f };
    Point3 constexpr kSlaughterSideGate{ 3960.6f, -3392.89f, 119.662f };
    Point3 constexpr kExitGate{ 3929.59f, -3384.95f, 119.008f };
    Point3 constexpr kYsidaCage{ 4044.34f, -3334.22f, 115.06f };
    Point3 constexpr kScarletArchive{ 3456.98f, -3106.54f, 137.908f };
    Point3 constexpr kMalorsStrongbox{ 3617.53f, -3130.55f, 135.665f };
    Point3 constexpr kCrusadersSquareCrate{ 3666.63f, -3182.46f, 126.252f };   // Supply Crate (Holy Water) 176224

    // --- Magistrate Barthilas (S9) -----------------------------------------------------------------------------------
    // A ruin beside his spawn lets only a north-south ward line fit there; 12 yd west, every bearing fits.
    Point3 constexpr kBarthilasWardAnchor{ 3661.2f, -3607.1f, 137.5f };
    inline std::array<Point3, 2> constexpr kBarthilasSpawnWards{ {
        { 3672.2f, -3619.1f, 138.9f }, { 3654.2f, -3619.1f, 137.8f } } };
    float constexpr kBarthilasWardOffsetYd = 9.f;   // ward centers either side of him

    // --- Baroness Anastari (S10) -------------------------------------------------------------------------------------
    Point3 constexpr kBaronessDoor{ 3853.47f, -3722.94f, 148.094f };            // [db] 175380, 7.4 yd behind her

    // --- Nerub'enkan (S11) -------------------------------------------------------------------------------------------
    Point3 constexpr kNerubenkanDoor{ 3851.7f, -3522.96f, 144.213f };           // [db] 175379
    float constexpr kNerubenkanPlazaZ = 138.5f;

    // --- Maleki the Pallid (S12) -------------------------------------------------------------------------------------
    // The eye: an 8 yd circle 11 to 13 yd from him at bearing 130 to 150 deg (the walkway walls eat the rest).
    inline std::array<Point3, 2> constexpr kMalekiEyeCenters{ {
        { 4027.5f, -3640.8f, 134.6f }, { 4026.5f, -3640.2f, 133.9f } } };
    Point3 constexpr kMalekiDoor{ 4038.13f, -3649.91f, 135.658f };              // [db] 175381

    // --- Ramstein the Gorger (S13) -----------------------------------------------------------------------------------
    // The square: X north, Y west to y -3385 (about 105 x 80 yd of floor).
    FrameRect constexpr kRamsteinSquare{ { 3976.0f, -3470.0f }, 0.f, 104.0f, 85.0f };
    float constexpr kMeatPathYd = 91.1f;            // straight from the meat's spawn to his stop, bearing 356 deg

    // --- Baron Rivendare (S14, S15) ----------------------------------------------------------------------------------
    // The oval room: X north, Y west.
    FrameRect constexpr kBaronRoom{ { 4007.5f, -3370.5f }, 0.f, 50.0f, 44.0f };
    // The six stock Raise Dead points (spell_target_position 17475-17480): south row, then north row.
    inline std::array<Point3, 6> constexpr kRaiseDeadPoints{ {
        { 4012.92f, -3365.70f, 116.0f }, { 4009.10f, -3352.31f, 115.8f }, { 4013.96f, -3338.65f, 115.4f },
        { 4051.75f, -3339.05f, 116.0f }, { 4055.96f, -3351.46f, 116.1f }, { 4053.11f, -3364.98f, 116.2f } } };
    Point3 constexpr kMenethilsGift{ 4032.77f, -3350.60f, 115.2f };

    // --- The Unforgiven (S1, wave 2) ---------------------------------------------------------------------------------
    // Two march lanes (frames) and two cordon lines closing the plaza (handoff section 3.8 #1).
    FrameRect constexpr kUnforgivenLaneMarketRow{ { 3672.7f, -3379.3f }, 5.061f, 46.0f, 25.3f };   // L1
    FrameRect constexpr kUnforgivenLanePassage{ { 3721.6f, -3440.9f }, 2.007f, 50.0f, 12.0f };     // L2
    inline std::array<Vec2, 2> constexpr kUnforgivenCordonEast{ { { 3723.5f, -3440.6f }, { 3711.0f, -3442.1f } } };
    inline std::array<Vec2, 2> constexpr kUnforgivenCordonSouthWest{ { { 3697.5f, -3368.5f },
        { 3670.5f, -3380.5f } } };
    // Fire spots and shelters (the report's F1-F4 and F6; F5 was not kept).
    inline std::array<Vec2, 5> constexpr kUnforgivenFireSpots{ { { 3712.0f, -3401.5f }, { 3719.5f, -3426.5f },
        { 3676.0f, -3396.5f }, { 3684.0f, -3415.5f }, { 3709.5f, -3383.5f } } };
    // The plaza polygon (counterclockwise from the east cordon's north end; wall points 1-2 yd outside the mesh).
    inline std::array<Vec2, 13> constexpr kUnforgivenPlaza{ { { 3723.5f, -3440.6f }, { 3724.0f, -3425.0f },
        { 3719.0f, -3405.0f }, { 3719.0f, -3378.0f }, { 3700.0f, -3374.0f }, { 3697.5f, -3368.5f },
        { 3670.5f, -3380.5f }, { 3669.0f, -3392.0f }, { 3671.0f, -3405.0f }, { 3676.0f, -3419.0f },
        { 3704.0f, -3420.0f }, { 3706.0f, -3432.0f }, { 3711.0f, -3442.1f } } };

    // --- Hearthsinger Forresten (S2, wave 2) -------------------------------------------------------------------------
    inline std::array<Vec2, 3> constexpr kForrestenHearths{ { { 3608.0f, -3510.0f }, { 3602.0f, -3499.2f },
        { 3607.5f, -3505.5f } } };
    inline std::array<Vec2, 3> constexpr kForrestenMovedHearths{ { { 3614.5f, -3503.0f }, { 3606.0f, -3493.0f },
        { 3615.5f, -3509.0f } } };

    // --- Timmy the Cruel (S3, wave 2) --------------------------------------------------------------------------------
    inline std::array<Vec2, 3> constexpr kTimmyBursts{ { { 3655.0f, -3207.5f }, { 3642.0f, -3166.0f },
        { 3672.0f, -3140.0f } } };
    Vec2 constexpr kTimmyHeroicBurst{ 3697.0f, -3195.0f };

    // --- Malor the Zealous (S4, wave 2) ------------------------------------------------------------------------------
    Vec2 constexpr kMalorDaisTank{ 3618.0f, -3118.0f };
    Vec2 constexpr kMalorDaisMouth{ 3612.0f, -3112.0f };

    // --- Cannon Master Willey (S5, wave 2) ---------------------------------------------------------------------------
    // The hall: X from his back wall down the hall, Y across it (Y 0..10 west half in front of Zeal 176217, Y 10..20
    // east half in front of Mercy 176216).
    FrameRect constexpr kWilleyHall{ { 3568.98f, -2928.30f }, 3.761f, 58.0f, 20.0f };
    float constexpr kWilleyHalfSplitY = 10.f;
    inline std::array<Point3, 3> constexpr kWilleyRank3{ { { 3529.55f, -2962.57f, 125.3f },
        { 3532.45f, -2966.64f, 125.3f }, { 3535.36f, -2970.71f, 125.3f } } };
    inline std::array<Point3, 4> constexpr kWilleyRank4{ { { 3528.97f, -2961.75f, 125.3f },
        { 3531.68f, -2965.55f, 125.3f }, { 3533.61f, -2968.27f, 125.3f }, { 3535.94f, -2971.52f, 125.3f } } };

    // --- Archivist Galford (S6, wave 2) ------------------------------------------------------------------------------
    // The hall between the two seals: X north to the north wall, Y west.
    FrameRect constexpr kGalfordHall{ { 3446.0f, -3092.0f }, 0.f, 54.0f, 32.0f };
    inline std::array<Vec2, 2> constexpr kGalfordPyre{ { { 3446.0f, -3074.5f }, { 3446.0f, -3101.5f } } };
    inline std::array<Vec2, 2> constexpr kGalfordNorthWall{ { { 3500.0f, -3064.5f }, { 3500.0f, -3101.5f } } };

    // --- Grand Crusader Dathrohan (S7, S8, wave 2) -------------------------------------------------------------------
    // Halves: X from the entrance through the brazier to his spawn; the split line is Y = 20.
    FrameRect constexpr kDathrohanHalves{ { 3451.41f, -3060.15f }, 2.199f, 40.0f, 40.0f };
    float constexpr kDathrohanSplitY = 20.f;
    Point3 constexpr kDathrohanBrazier{ 3423.47f, -3055.73f, 136.8f };
    inline std::array<Vec2, 4> constexpr kDathrohanHalfASpots{ { { 3430.5f, -3062.1f }, { 3432.9f, -3054.4f },
        { 3428.5f, -3047.7f }, { 3420.5f, -3046.7f } } };
    inline std::array<Vec2, 4> constexpr kDathrohanHalfBSpots{ { { 3416.4f, -3049.4f }, { 3414.1f, -3057.1f },
        { 3418.4f, -3063.8f }, { 3426.4f, -3064.8f } } };

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (handoff section 3.8; user ruling on section 7 #16: the arena leash everywhere, the boss holds at the edge
    // and evades when dragged off it; the pull grip only for The Unforgiven and Galford, built by S1 / S6 with their
    // lethal walls). Each is a leash circle (or the report's polygon / frame) with its z band. StratholmeKit.h
    // LeashOptions() builds the guard's options.
    // ----------------------------------------------------------------------------------------------------------------
    inline Arena CircleArena(Vec2 center, float radius, float zMin, float zMax)
    {
        return Arena(ArenaRegion::Circle(center, radius, zMin, zMax));
    }

    inline Arena BarthilasArena() { return CircleArena({ 3661.0f, -3608.0f }, 30.f, 137.0f, 142.0f); }
    inline Arena BaronessArena() { return CircleArena({ 3857.0f, -3705.0f }, 30.f, 139.8f, 149.1f); }
    inline Arena NerubenkanArena() { return CircleArena({ 3858.0f, -3540.0f }, 30.f, 137.3f, 145.3f); }
    inline Arena MalekiArena() { return CircleArena({ 4028.0f, -3638.0f }, 25.f, 126.0f, 137.0f); }
    // He is summoned at kRamsteinSummon, 47.5 yd from the center (outside), in his pen; he walks in to kRamsteinStop.
    // S13 keeps him out of his own 5-6 yd passage.
    inline Arena RamsteinArena() { return CircleArena({ 4025.0f, -3425.0f }, 45.f, 115.0f, 124.0f); }
    // The stock leash (21 yd from 175405, 4 yd from his door) is S14's; this circle is the room.
    inline Arena BaronArena() { return CircleArena({ 4032.0f, -3348.0f }, 25.f, 115.0f, 117.5f); }

    inline Arena UnforgivenArena()
    {
        return Arena(ArenaRegion::Polygon(std::vector<Vec2>(kUnforgivenPlaza.begin(), kUnforgivenPlaza.end()),
            127.0f, 135.0f));
    }

    inline Arena ForrestenArena() { return CircleArena({ 3610.0f, -3500.0f }, 30.f, 135.5f, 140.0f); }
    inline Arena TimmyArena() { return CircleArena({ 3668.0f, -3176.0f }, 52.f, 126.0f, 136.0f); }
    inline Arena MalorArena() { return CircleArena({ 3612.0f, -3112.0f }, 22.f, 134.0f, 138.0f); }
    inline Arena WilleyArena()
    {
        return Arena(ArenaRegion::Frame(kWilleyHall, Box2{ 0.f, kWilleyHall.sizeX, 0.f, kWilleyHall.sizeY },
            124.0f, 127.0f));
    }
    // The hall between the seals. His spawn and the Scarlet Archive's corner lie 11 to 15 yd east of the frame's
    // Y = 0 edge, so the box reaches to Y -13 (y -3105) to hold his spawn; S6 checks the east wall in game.
    inline Arena GalfordArena()
    {
        return Arena(ArenaRegion::Frame(kGalfordHall, Box2{ 0.f, kGalfordHall.sizeX, -13.f, kGalfordHall.sizeY },
            135.0f, 139.0f));
    }
    inline Arena DathrohanArena() { return CircleArena({ 3423.47f, -3055.73f }, 22.f, 136.0f, 139.0f); }

    // The arena of a boss state (the hard mode slots: their boss's; the event bosses: none).
    inline Arena ArenaFor(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_UNFORGIVEN:   return UnforgivenArena();
            case BOSS_FORRESTEN:    return ForrestenArena();
            case BOSS_TIMMY:        return TimmyArena();
            case BOSS_WILLEY:       return WilleyArena();
            case BOSS_MALOR:        return MalorArena();
            case BOSS_GALFORD:      return GalfordArena();
            case BOSS_BALNAZZAR:
            case BOSS_GRAND_LIE:    return DathrohanArena();
            case BOSS_BARONESS:     return BaronessArena();
            case BOSS_NERUBENKAN:   return NerubenkanArena();
            case BOSS_MALEKI:       return MalekiArena();
            case BOSS_BARTHILAS:    return BarthilasArena();
            case BOSS_RAMSTEIN:     return RamsteinArena();
            case BOSS_BARON:
            case BOSS_ULTIMATUM:    return BaronArena();
            default:                return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The ziggurats (stock DATA_ZIGGURAT1-3): 0 = nothing, 1 = the boss is dead (its door opens), 2 = the Ash'ari
    // Crystal is shattered too. All three at 2 open the Gauntlet and Slaughter gates. Stock accepts only state + 1,
    // so a crystal (2) that breaks while the boss lives (0) was lost and the gates never opened (ST implementation
    // note 1, section 7 #12). The fix: that write is remembered (`pending`) and applied when the boss dies.
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kZigguratCount = 3;
    std::uint32_t constexpr kZigguratBossDead = 1;
    std::uint32_t constexpr kZigguratCrystalBroken = 2;

    struct Ziggurat
    {
        std::uint32_t state = 0;
        bool pending = false;       // the crystal broke while the boss lived

        bool operator==(Ziggurat const& o) const { return state == o.state && pending == o.pending; }
    };

    inline Ziggurat ZigguratAfterWrite(Ziggurat z, std::uint32_t data)
    {
        if (data == z.state + 1 && z.state < kZigguratCrystalBroken)
            ++z.state;
        else if (data == kZigguratCrystalBroken && z.state == 0)
            z.pending = true;
        if (z.state == kZigguratBossDead && z.pending)
            z.state = kZigguratCrystalBroken;
        if (z.state >= kZigguratCrystalBroken)
            z.pending = false;
        return z;
    }

    inline bool AllZigguratsBroken(std::array<Ziggurat, kZigguratCount> const& z)
    {
        for (Ziggurat const& one : z)
            if (one.state < kZigguratCrystalBroken)
                return false;
        return true;
    }

    // The ziggurat boss of each ziggurat (index 0..2), and back.
    inline std::array<std::uint32_t, kZigguratCount> constexpr kZigguratBosses{ {
        BOSS_BARONESS, BOSS_NERUBENKAN, BOSS_MALEKI } };

    constexpr std::optional<std::uint32_t> ZigguratOfBoss(std::uint32_t bossId)
    {
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
            if (kZigguratBosses[i] == bossId)
                return i;
        return std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The slaughter event (stock stages, same numbers so a stock save keeps its meaning). ST 3395-3400: Ramstein's
    // death goes straight to the Black Guards; the Mindless Undead stage is gone (his meat is S13's, never counted by
    // the instance). Retires ST implementation note 8.
    // ----------------------------------------------------------------------------------------------------------------
    enum SlaughterStage : std::uint32_t
    {
        SLAUGHTER_ABOMINATIONS      = 0,
        SLAUGHTER_RAMSTEIN          = 1,
        SLAUGHTER_MINDLESS_UNDEAD   = 2,    // retired: a stock save at this stage loads as SLAUGHTER_BLACK_GUARD
        SLAUGHTER_BLACK_GUARD       = 3,
        SLAUGHTER_COMPLETE          = 4,
    };
    std::uint32_t constexpr kBlackGuardCount = 5;
    std::uint32_t constexpr kBlackGuardDelayMs = 20000;

    inline std::uint32_t SanitizeSlaughterStage(std::uint32_t s)
    {
        if (s == SLAUGHTER_MINDLESS_UNDEAD)
            return SLAUGHTER_BLACK_GUARD;
        return s > SLAUGHTER_COMPLETE ? std::uint32_t(SLAUGHTER_COMPLETE) : s;
    }

    inline std::uint32_t NextSlaughterStage(std::uint32_t s)
    {
        s = SanitizeSlaughterStage(s);
        if (s == SLAUGHTER_COMPLETE)
            return SLAUGHTER_COMPLETE;
        return SanitizeSlaughterStage(s + 1);
    }

    // The Slaughter Square side gate: stock opened it for the Mindless stage; now from the Black Guards on (S13 may
    // open it earlier, at his first meat wave).
    inline bool SideGateOpen(std::uint32_t stage)
    {
        return SanitizeSlaughterStage(stage) >= SLAUGHTER_BLACK_GUARD;
    }

    // The Baron's door: open once the Black Guards are dead, closed while he fights.
    inline bool BaronDoorOpen(std::uint32_t stage, bool baronFighting)
    {
        return SanitizeSlaughterStage(stage) == SLAUGHTER_COMPLETE && !baronFighting;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Baron Run (stock: 45 minutes from the Gauntlet Gate, yells at 10 / 5 / 0, Ysida executed at 0 once the Baron
    // is out of combat) and the two hard modes (handoff section 3.7).
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBaronRunMinutes = 45;          // ruling 60: the stock clock

    // SetData(DATA_ULTIMATUM, data): 1 needs heroic, the clock running and the Baron neither fighting nor dead; 0 is
    // refused while he fights. The Ysida gossip's `conditions` show the option only when this would pass.
    inline bool UltimatumChangeAllowed(std::uint32_t data, bool heroic, std::uint32_t clockMinutes,
        std::uint32_t baronState)
    {
        if (baronState == DungeonKit::State::InProgress || baronState == DungeonKit::State::Done)
            return false;
        if (!data)
            return true;
        return heroic && clockMinutes > 0;
    }

    // SetData(DATA_GRAND_LIE, data): 1 needs heroic, wave 2 bound and Balnazzar neither fighting nor dead; it stays lit
    // through wipes (section 7 #10). 0 (a GM clear) is refused while he fights.
    inline bool GrandLieChangeAllowed(std::uint32_t data, bool heroic, bool wave2Bound, std::uint32_t balnazzarState)
    {
        if (balnazzarState == DungeonKit::State::InProgress || balnazzarState == DungeonKit::State::Done)
            return false;
        if (!data)
            return true;
        return heroic && wave2Bound;
    }

    // The exit gate 176424 opens through Ysida (her SmartAI) when she lives; when she is dead (executed by the clock,
    // or the Ultimatum killed her) the Baron's death opens it (ST implementation note 9, ruling 60).
    inline bool ExitGateOpensOnBaronDeath(bool ysidaAlive)
    {
        return !ysidaAlive;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The DBC encounter bits of map 329 (DungeonEncounter 472-484, Bit 0..12; the completed-encounter mask), read into
    // boss states when a stock save is loaded.
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<std::pair<std::uint32_t, std::uint32_t>, 13> constexpr kEncounterBits{ {
        { 0, BOSS_UNFORGIVEN }, { 1, BOSS_FORRESTEN }, { 2, BOSS_TIMMY }, { 3, BOSS_WILLEY }, { 4, BOSS_MALOR },
        { 5, BOSS_GALFORD }, { 6, BOSS_BALNAZZAR }, { 7, BOSS_BARONESS }, { 8, BOSS_NERUBENKAN }, { 9, BOSS_MALEKI },
        { 10, BOSS_BARTHILAS }, { 11, BOSS_RAMSTEIN }, { 12, BOSS_BARON } } };

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string: header "SR" (never "ST": a prefix of the stock "S T R" would hide a stock save from the
    // legacy reader), the 17 boss states, then the extras below. A stock save (instance_stratholme at 9ce0f3dcc:
    // "S T R", no boss states, then 8 integers and up to 3 time_t fields) is still read: its fields come over, the
    // completed-encounter mask (set before Load, from the DBC bits) and the ziggurat and slaughter fields fill in the
    // boss states they record, and a Mindless Undead stage moves on to the Black Guards.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "SR";
    char constexpr kStockSaveHeader[] = "STR";

    enum SaveExtra : std::size_t
    {
        EXTRA_BARON_RUN_PROGRESS    = 0,
        EXTRA_BARON_RUN_MINUTES     = 1,
        EXTRA_ZIGGURAT1             = 2,
        EXTRA_ZIGGURAT2             = 3,
        EXTRA_ZIGGURAT3             = 4,
        EXTRA_SLAUGHTER             = 5,
        EXTRA_POSTBOXES             = 6,
        EXTRA_BARTHILAS_RUN         = 7,
        EXTRA_SCARLET_THREADS       = 8,
        EXTRA_GATE_TRAP_SCARLET_END = 9,
        EXTRA_GATE_TRAP_UNDEAD_END  = 10,
        EXTRA_ZIGGURAT_PENDING      = 11,
        EXTRA_ULTIMATUM             = 12,
        EXTRA_GRAND_LIE             = 13,
    };
    std::size_t constexpr kSaveExtraCount = 14;

    std::uint32_t constexpr kScarletThreadLocations = 4;
    std::uint32_t constexpr kAllScarletThreads = (1u << kScarletThreadLocations) - 1;

    struct StratSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        std::uint32_t baronRunProgress = 0;     // 0 none, 1 the gate was opened
        std::uint32_t baronRunMinutes = 0;      // minutes left (0: none or out)
        std::array<Ziggurat, kZigguratCount> ziggurats{};
        std::uint32_t slaughter = SLAUGHTER_ABOMINATIONS;
        std::uint32_t postboxes = 0;
        std::uint32_t barthilasRun = 0;
        std::uint32_t scarletThreads = 0;       // used thread locations (bit per location)
        std::array<std::uint32_t, 2> gateTrapEnd{};     // unix time each trap's cooldown ends (0: ready)
        std::uint32_t ultimatum = 0;
        std::uint32_t grandLie = 0;
    };

    inline std::uint32_t ZigguratPendingMask(std::array<Ziggurat, kZigguratCount> const& z)
    {
        std::uint32_t mask = 0;
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
            if (z[i].pending)
                mask |= 1u << i;
        return mask;
    }

    inline std::string FormatStratSave(StratSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_BARON_RUN_PROGRESS] = s.baronRunProgress;
        extras[EXTRA_BARON_RUN_MINUTES] = s.baronRunMinutes;
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
            extras[EXTRA_ZIGGURAT1 + i] = s.ziggurats[i].state;
        extras[EXTRA_SLAUGHTER] = s.slaughter;
        extras[EXTRA_POSTBOXES] = s.postboxes;
        extras[EXTRA_BARTHILAS_RUN] = s.barthilasRun;
        extras[EXTRA_SCARLET_THREADS] = s.scarletThreads;
        extras[EXTRA_GATE_TRAP_SCARLET_END] = s.gateTrapEnd[0];
        extras[EXTRA_GATE_TRAP_UNDEAD_END] = s.gateTrapEnd[1];
        extras[EXTRA_ZIGGURAT_PENDING] = ZigguratPendingMask(s.ziggurats);
        extras[EXTRA_ULTIMATUM] = s.ultimatum;
        extras[EXTRA_GRAND_LIE] = s.grandLie;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The boss states a completed-encounter mask records (DONE), OR-ed into `states`.
    inline void ApplyEncounterMask(std::uint32_t mask, std::array<std::uint32_t, kBossCount>& states)
    {
        for (auto const& [bit, boss] : kEncounterBits)
            if (mask & (1u << bit))
                states[boss] = DungeonKit::State::Done;
    }

    // The stock "S T R <8 integers> [<thread mask>] [<trap end> <trap end>]" (instance_stratholme ReadSaveDataMore at
    // 9ce0f3dcc: 9 fields = the mask, 10 = the two trap cooldowns, 11 = all three). False without the 8 integers.
    inline bool ReadStockSave(std::string const& in, StratSave& out)
    {
        std::vector<std::uint32_t> f;
        if (!DungeonKit::ReadSaveFields(in, kStockSaveHeader, 8, 11, f))
            return false;
        out.baronRunProgress = f[0];
        out.baronRunMinutes = f[1];
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
            out.ziggurats[i].state = f[2 + i];
        out.slaughter = f[5];
        out.postboxes = f[6];
        out.barthilasRun = f[7];
        std::size_t const more = f.size() - 8;
        if (more == 2)
        {
            out.gateTrapEnd[0] = f[8];
            out.gateTrapEnd[1] = f[9];
        }
        else
        {
            if (more >= 1 && f[8] <= kAllScarletThreads)
                out.scarletThreads = f[8];
            if (more == 3)
            {
                out.gateTrapEnd[0] = f[9];
                out.gateTrapEnd[1] = f[10];
            }
        }
        return true;
    }

    // Loaded values that cannot be trusted are put back in range; a stock save also fills in the boss states its own
    // fields record (a ziggurat at 1 or 2 is its boss dead; the slaughter past Ramstein is Ramstein dead).
    inline void SanitizeStratSave(StratSave& s, bool fromStock)
    {
        s.baronRunProgress = s.baronRunProgress ? 1 : 0;
        if (s.baronRunMinutes > kBaronRunMinutes)
            s.baronRunMinutes = kBaronRunMinutes;
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
        {
            Ziggurat& z = s.ziggurats[i];
            if (z.state > kZigguratCrystalBroken)
                z.state = kZigguratCrystalBroken;
            if (z.state >= kZigguratCrystalBroken)
                z.pending = false;
            if (fromStock && z.state >= kZigguratBossDead)
                s.states[kZigguratBosses[i]] = DungeonKit::State::Done;
        }
        s.slaughter = SanitizeSlaughterStage(s.slaughter);
        if (fromStock && s.slaughter > SLAUGHTER_RAMSTEIN)
            s.states[BOSS_RAMSTEIN] = DungeonKit::State::Done;
        s.scarletThreads &= kAllScarletThreads;
        s.ultimatum = s.ultimatum ? 1 : 0;
        s.grandLie = s.grandLie ? 1 : 0;
        // No clock, no Ultimatum (the opt-in only exists while it runs); a dead boss has no lit hard mode.
        if (!s.baronRunMinutes || s.states[BOSS_BARON] == DungeonKit::State::Done)
            s.ultimatum = 0;
        if (s.states[BOSS_BALNAZZAR] == DungeonKit::State::Done)
            s.grandLie = 0;
    }

    // Reads this script's "S R" string, or a stock one; `encounterMask` is the instance's completed-encounter mask
    // (applied to a stock save only: an "S R" save carries its own states). False on anything else (ignored).
    inline bool ParseStratSave(std::string const& in, StratSave& out, std::uint32_t encounterMask = 0)
    {
        out = StratSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        StratSave stockSave;
        DungeonKit::LegacySaveReader const legacy = [&stock, &stockSave, encounterMask](std::string const& s,
            DungeonKit::StateSave& o)
        {
            if (!ReadStockSave(s, stockSave))
                return false;
            ApplyEncounterMask(encounterMask, stockSave.states);
            o.states.assign(stockSave.states.begin(), stockSave.states.end());
            stock = true;
            return true;
        };
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw, legacy))
            return false;
        if (stock)
        {
            out = stockSave;
            for (std::size_t i = 0; i < kBossCount; ++i)
                out.states[i] = raw.states[i];
            SanitizeStratSave(out, true);
            return true;
        }
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        out.baronRunProgress = raw.extras[EXTRA_BARON_RUN_PROGRESS];
        out.baronRunMinutes = raw.extras[EXTRA_BARON_RUN_MINUTES];
        std::uint32_t const pending = raw.extras[EXTRA_ZIGGURAT_PENDING];
        for (std::uint32_t i = 0; i < kZigguratCount; ++i)
        {
            out.ziggurats[i].state = raw.extras[EXTRA_ZIGGURAT1 + i];
            out.ziggurats[i].pending = (pending & (1u << i)) != 0;
        }
        out.slaughter = raw.extras[EXTRA_SLAUGHTER];
        out.postboxes = raw.extras[EXTRA_POSTBOXES];
        out.barthilasRun = raw.extras[EXTRA_BARTHILAS_RUN];
        out.scarletThreads = raw.extras[EXTRA_SCARLET_THREADS];
        out.gateTrapEnd[0] = raw.extras[EXTRA_GATE_TRAP_SCARLET_END];
        out.gateTrapEnd[1] = raw.extras[EXTRA_GATE_TRAP_UNDEAD_END];
        out.ultimatum = raw.extras[EXTRA_ULTIMATUM];
        out.grandLie = raw.extras[EXTRA_GRAND_LIE];
        SanitizeStratSave(out, false);
        return true;
    }
}

#endif
