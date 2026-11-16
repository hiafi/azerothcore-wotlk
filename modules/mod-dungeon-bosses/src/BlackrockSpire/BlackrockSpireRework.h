/*
 * mod-dungeon-bosses, Blackrock Spire (map 229): the shared ids, boss states, data fields, texts, measured points,
 * frames, arenas, the save string and the instance rules of the Blackrock Spire build
 * (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md sections 3.1-3.3, 3.7, 3.8, 3.12 and the user
 * rulings of section 10; build spec docs/dungeons/blackrock-spire-rework.md, "SP").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h /
 * DungeonKitFlexRules.h), so every <Boss>Logic.h and its host test can include it. Engine glue: the shared kit
 * (src/Kit/DungeonKit.h, DungeonKitFlex.h) and the Blackrock Spire glue (BlackrockSpireKit.h).
 *
 * Ownership: this file belongs to WP-S0 (the Blackrock Spire skeleton) until it reports, then to the orchestrator. A
 * boss WP keeps its own spell ids (inside its slice below), tuning constants, flex counts and script-local enums in its
 * own <Boss>Logic.h (convention: `enum <Boss>Spells : std::uint32_t { SPELL_<BOSS>_... = <id in its slice> }`,
 * `inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };` and `inline constexpr FlexAB k<Name>Targets{ a, b
 * };`), and asks the orchestrator, in its report, for any change here.
 *
 * Measured points, frames and arenas are [navmesh estimate] (blackrock-spire-build.NAVMESH-REPORT.md, folded into the
 * handoff's section 3.8: the mesh sits about 0.5 yd inside every wall) unless marked [db] (creature, gameobject or
 * areatrigger rows, exact). Axes: +x north, +y west. A boss WP tightens its own arena in its own file after the
 * playtest's `.gps` walk (section 7 #28); the arenas here are the leash frames of the stubs.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_REWORK_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_REWORK_H

#include "DungeonKitArena.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace BlackrockSpireRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Box2;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapBlackrockSpire = 229;
    // The stock instance name (handoff section 3.1, section 7 #2): the rework replaces the stock InstanceMapScript of
    // that name at load (same-named scripts registered later win; modules load after the core scripts), so
    // instance_template is untouched and every stock script that checks the name (GetBlackrockSpireAI: Valthalak, Mor
    // Grayhoof, npc_vaelastrasz_the_red, go_father_flame, the wave 2 bosses until they are bound) keeps working with
    // no copy.
    char constexpr kInstanceScriptName[] = "instance_blackrock_spire";
    // `.dbtest brs <boss> <mechanic>` (handoff section 3.2 item 4): the kit shell's command name; the chat command map
    // splits it at the space, so it nests under the shared `.dbtest` root (BlackrockSpireTestCommand.cpp).
    char constexpr kTestCommand[] = "dbtest brs";
    char constexpr kLogDungeon[] = "brs";           // DungeonKit::LogMechanic("brs", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. Every stock slot keeps its stock number and meaning (blackrock_spire.h DataTypes): the
    // stock scripts that stay (Valthalak's BossAI on 14, Mor Grayhoof's on 24, the wave 2 bosses until they are bound,
    // Solakar's BossAI on 23), the instance's own Dragonspire room check (15-22) and mod-dungeon-clear (9, 10) write
    // and read them. Stock had EncounterCount 23, so 23 and 24 never persisted (SP note 3); 28 slots keep them (section
    // 7 #2). 25 is DATA_VAELASTRASZ's number (still SetData, never a boss state: the slot stays NOT_STARTED). 26 and 27
    // are the two hard mode kills, written by the instance only.
    // ----------------------------------------------------------------------------------------------------------------
    enum BrsBosses : std::uint32_t
    {
        BOSS_OMOKK              = 0,    // B1, wave 1
        BOSS_VOSHGAJIN          = 1,    // B2, wave 1
        BOSS_VOONE              = 2,    // B3, wave 1
        BOSS_SMOLDERWEB         = 3,    // B4, wave 1
        BOSS_UROK               = 4,    // B5, wave 1
        BOSS_ZIGRIS             = 5,    // B6, wave 1
        BOSS_GIZRUL             = 6,    // B7, wave 1 (one encounter with Halycon; both slots written)
        BOSS_HALYCON            = 7,    // B7, wave 1
        BOSS_WYRMTHALAK         = 8,    // B8, wave 1 (the LBRS final)
        BOSS_EMBERSEER          = 9,    // B10, wave 2
        BOSS_REND               = 10,   // B12, wave 2
        BOSS_GYTH               = 11,   // B12, wave 2
        BOSS_BEAST              = 12,   // B13, wave 2
        BOSS_DRAKKISATH         = 13,   // B14, wave 2 (the UBRS final)
        BOSS_VALTHALAK          = 14,   // stock boss_lord_valthalak (BossAI, kept; out of scope)
        BOSS_DRAGONSPIRE_ROOM   = 15,   // the instance's room check: DONE when the seven hall runes are DONE
        BOSS_HALL_RUNE_1        = 16,   // the hall runes, DONE as their packs die (the instance's room check)
        BOSS_HALL_RUNE_2        = 17,
        BOSS_HALL_RUNE_3        = 18,
        BOSS_HALL_RUNE_4        = 19,
        BOSS_HALL_RUNE_5        = 20,
        BOSS_HALL_RUNE_6        = 21,
        BOSS_HALL_RUNE_7        = 22,
        BOSS_SOLAKAR            = 23,   // B11, wave 2 (stock BossAI(23); persists now)
        BOSS_MOR_GRAYHOOF       = 24,   // stock boss_mor_grayhoof (BossAI(24); persists now: harmless, section 6)
        BOSS_VAELASTRASZ_SLOT   = 25,   // reserved: DATA_VAELASTRASZ is SetData only, never a boss state
        BOSS_WAR_HORN           = 26,   // B9: Wyrmthalak killed with the war horn blown (set by the instance)
        BOSS_GENERALS_ARMY      = 27,   // B15: Drakkisath killed with the General's Army armed (set by the instance)
    };
    std::uint32_t constexpr kBossCount = 28;
    std::uint32_t constexpr kStockEncounterCount = 23;     // blackrock_spire.h EncounterCount (the stock save's length)
    std::uint32_t constexpr kHallRuneCount = 7;

    // The stock numbers (blackrock_spire.h DataTypes at 8eb009fdf), pinned: stock scripts write these slots.
    static_assert(BOSS_OMOKK == 0 && BOSS_VOSHGAJIN == 1 && BOSS_VOONE == 2 && BOSS_SMOLDERWEB == 3 && BOSS_UROK == 4
        && BOSS_ZIGRIS == 5 && BOSS_GIZRUL == 6 && BOSS_HALYCON == 7 && BOSS_WYRMTHALAK == 8, "stock LBRS slots");
    static_assert(BOSS_EMBERSEER == 9 && BOSS_REND == 10 && BOSS_GYTH == 11 && BOSS_BEAST == 12
        && BOSS_DRAKKISATH == 13 && BOSS_VALTHALAK == 14, "stock UBRS slots");
    static_assert(BOSS_DRAGONSPIRE_ROOM == 15 && BOSS_HALL_RUNE_1 == 16 && BOSS_HALL_RUNE_7 == 22,
        "stock DATA_DRAGONSPIRE_ROOM and DATA_HALL_RUNE_1..7");
    static_assert(BOSS_SOLAKAR == 23 && BOSS_MOR_GRAYHOOF == 24 && BOSS_VAELASTRASZ_SLOT == 25,
        "stock DATA_SOLAKAR_FLAMEWREATH, DATA_MOR_GRAYHOOF, DATA_VAELASTRASZ");
    static_assert(BOSS_HALL_RUNE_7 - BOSS_HALL_RUNE_1 + 1 == kHallRuneCount, "seven hall runes");
    static_assert(BOSS_GENERALS_ARMY + 1 == kBossCount, "every boss state has a slot");
    static_assert(kStockEncounterCount == BOSS_SOLAKAR, "the stock save stops before Solakar's slot");

    // Names by boss state id (`.dbtest brs state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Highlord Omokk", "Shadow Hunter Vosh'gajin", "War Master Voone", "Mother Smolderweb", "Urok Doomhowl",
        "Quartermaster Zigris", "Gizrul the Slavener", "Halycon", "Overlord Wyrmthalak", "Pyroguard Emberseer",
        "Warchief Rend Blackhand", "Gyth", "The Beast", "General Drakkisath", "Lord Valthalak (stock)",
        "Dragonspire Hall (room)", "Hall rune 1", "Hall rune 2", "Hall rune 3", "Hall rune 4", "Hall rune 5",
        "Hall rune 6", "Hall rune 7", "Solakar Flamewreath", "Mor Grayhoof (stock)", "(Vaelastrasz: data only)",
        "The War Horn (Wyrmthalak hard mode)", "The General's Army (Drakkisath hard mode)" } };

    // Slots no reworked boss writes: the stock event bosses, the room check, the reserved Vaelastrasz slot.
    constexpr bool IsStockBossSlot(std::uint32_t bossId)
    {
        return bossId == BOSS_VALTHALAK || bossId == BOSS_MOR_GRAYHOOF;
    }

    constexpr bool IsRoomSlot(std::uint32_t bossId)
    {
        return bossId >= BOSS_DRAGONSPIRE_ROOM && bossId <= BOSS_HALL_RUNE_7;
    }

    constexpr bool IsHallRuneSlot(std::uint32_t bossId)
    {
        return bossId >= BOSS_HALL_RUNE_1 && bossId <= BOSS_HALL_RUNE_7;
    }

    constexpr bool IsHardModeSlot(std::uint32_t bossId)
    {
        return bossId == BOSS_WAR_HORN || bossId == BOSS_GENERALS_ARMY;
    }

    // An encounter slot (a boss a player fights; the two hard mode slots are kills of their boss's encounter).
    constexpr bool IsEncounterSlot(std::uint32_t bossId)
    {
        return bossId <= BOSS_DRAKKISATH || bossId == BOSS_SOLAKAR;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Wave switch (handoff section 3.2, section 7 #32: wave 1 is Lower Blackrock Spire, wave 2 Upper Blackrock Spire;
    // the Scholomance and Stratholme pattern). Until wave 2 flips it, the UBRS bosses keep their stock ScriptName,
    // AIName, SmartAI and health (the DT twin BIND_WAVE_2 in apps/dbc-tools source/npcs/blackrock_spire/_common.py must
    // agree: lib/test_blackrock_spire_kit.py), their stub C++ registers no AI (an unbound registered name logs "not
    // assigned" at boot), and the instance keeps their stock event paths (the altar, the Solakar waves, Rend's
    // respawn); the wave 2 instance code (the insult, the herald's arming) stays off.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr bool kWave2Bound = true;

    constexpr bool IsWave2Boss(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_EMBERSEER:
            case BOSS_REND:
            case BOSS_GYTH:
            case BOSS_BEAST:
            case BOSS_DRAKKISATH:
            case BOSS_SOLAKAR:
            case BOSS_GENERALS_ARMY:
                return true;
            default:
                return false;
        }
    }

    // A reworked boss whose wave is bound (the stock event bosses and the room slots are never reworked).
    constexpr bool IsReworkBound(std::uint32_t bossId, bool wave2Bound = kWave2Bound)
    {
        if (bossId >= kBossCount || IsStockBossSlot(bossId) || IsRoomSlot(bossId) || bossId == BOSS_VAELASTRASZ_SLOT)
            return false;
        return !IsWave2Boss(bossId) || wave2Bound;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids above). The stock
    // ones keep their numbers and meanings; the new ones start at 30, clear of every stock type and of 2046.
    // ----------------------------------------------------------------------------------------------------------------
    enum BrsData : std::uint32_t
    {
        // Stock (blackrock_spire.h), kept:
        DATA_AREATRIGGER            = 1,    // SetData(1, 2046): at_dragonspire_hall starts the room check (STORE/CHECK)
        DATA_UROK_EVENT             = 4,    // SetData(4, FAIL): the Urok challenge failed: the pile resets (stock)
        DATA_VALTHALAK_DONE         = 14,   // stock boss_lord_valthalak's SetData(14, DONE): ignored, as stock
        DATA_SOLAKAR_EVENT          = 23,   // Get/SetData: the Solakar event (NOT_STARTED, IN_PROGRESS, DONE; a FAIL
                                            // resets it to NOT_STARTED so Father Flame starts it again, SP note 1)
        DATA_VAELASTRASZ            = 25,   // Get/SetData: the Call of Vaelastrasz state (stock, not saved)
        // New (30 on):
        DATA_NEF_INSULTED           = 30,   // SetData(30, 1): Nefarius's BRS copy was insulted (B12; refused while wave
                                            // 2 is unbound). Saved; kept through wipes for the lockout (SP 3838-3840)
        DATA_UROK_PILE              = 31,   // GetData: UrokPile; SetData(31, PILE_IN_USE) when B5's challenge starts,
                                            // SetData(31, PILE_READY) when it resets. Saved (derived again on load)
        DATA_SOLAKAR_FLAME          = 32,   // Get/SetData: SolakarFlame (B11, for the reset). Saved
        DATA_WAR_HORN               = 33,   // SetData(33, 1): the war horn was blown (B9's GO; heroic, Wyrmthalak
                                            // neither fighting nor dead). Per pull, not saved (SP WT17)
        DATA_GENERALS_ARMY          = 34,   // SetData(34, 1): the herald's "Let them come" (B15; heroic, wave 2 bound,
                                            // the insult saved, Drakkisath neither fighting nor dead). Per pull
        DATA_HALL_RUNES_DONE        = 35,   // GetData only: the mask of hall runes DONE (bit 0 = rune 1)
        DATA_ROOM_CHECK             = 36,   // GetData only: 1 while the room check runs; SetData(36, 1) (GM test)
                                            // starts it as the area trigger does
    };

    std::uint32_t constexpr kAreaTriggerDragonspireHall = 2046;     // [db] at_dragonspire_hall
    std::uint32_t constexpr kAreaTriggerBlackrockStadium = 2026;    // [db] at_blackrock_stadium (Rend; stock, kept)
    std::uint32_t constexpr kEventBlackrockAltar = 4884;            // ProcessEvent: Emberseer's cage (stock, kept)
    std::uint32_t constexpr kEventUrokPile = 4845;                  // ProcessEvent: Urok's tribute pile (stock path)

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum BrsCreatures : std::uint32_t
    {
        // bosses (stock entries; script names bound by apps/dbc-tools source/npcs/blackrock_spire/<boss>.py)
        NPC_OMOKK                   = 9196,     // boss_highlord_omokk_rework
        NPC_VOSHGAJIN               = 9236,     // boss_shadow_hunter_voshgajin_rework
        NPC_VOONE                   = 9237,     // boss_warmaster_voone_rework
        NPC_SMOLDERWEB              = 10596,    // boss_mother_smolderweb_rework
        NPC_UROK                    = 10584,    // boss_urok_doomhowl_rework (summoned by the pile's challenge)
        NPC_ZIGRIS                  = 9736,     // boss_quartermaster_zigris_rework
        NPC_GIZRUL                  = 10268,    // boss_halycon_gizrul_rework (summoned per pull, never ObjectData)
        NPC_HALYCON                 = 10220,    // boss_halycon_gizrul_rework
        NPC_WYRMTHALAK              = 9568,     // boss_overlord_wyrmthalak_rework
        NPC_EMBERSEER               = 9816,     // boss_pyroguard_emberseer_rework (wave 2)
        NPC_SOLAKAR                 = 10264,    // boss_solakar_flamewreath_rework (wave 2; summoned by the event)
        NPC_REND                    = 10429,    // boss_rend_blackhand_rework (wave 2)
        NPC_GYTH                    = 10339,    // boss_gyth_rework (wave 2; summoned)
        NPC_BEAST                   = 10430,    // boss_the_beast_rework (wave 2)
        NPC_DRAKKISATH              = 10363,    // boss_drakkisath_rework (wave 2)

        // stock units the instance or the kit uses
        NPC_VALTHALAK               = 16042,    // Lord Valthalak (stock boss_lord_valthalak, slot 14)
        NPC_MOR_GRAYHOOF            = 16080,    // Mor Grayhoof (stock boss_mor_grayhoof, slot 24)
        NPC_BLACKHAND_DREADWEAVER   = 9817,     // the hall rune packs
        NPC_BLACKHAND_SUMMONER      = 9818,
        NPC_BLACKHAND_VETERAN       = 9819,
        NPC_LORD_VICTOR_NEFARIUS    = 10162,    // shared with Blackwing Lair; BRS spawn 137967 until B12 rebinds it
        NPC_VAELASTRASZ_THE_RED     = 10340,
        NPC_VAELASTRASZ_UBRS        = 10538,
        NPC_SCARSHIELD_INFILTRATOR  = 10299,
        NPC_FINKLE_EINHORN          = 10776,    // the Beast's skinning surprise (stock, kept)
        // stock-id boss-kit adds (each boss's alone; handoff section 1 table)
        NPC_UROK_ENFORCER           = 10601,    // Urok's challenge (B5)
        NPC_UROK_MAGUS              = 10602,
        NPC_BLACKHAND_INCARCERATOR  = 10316,    // Emberseer (B10)
        NPC_ROOKERY_GUARDIAN        = 10258,    // Solakar (B11)
        NPC_ROOKERY_HATCHER         = 10683,
        NPC_ROOKERY_WHELP           = 10161,
        NPC_CHROMATIC_WHELP         = 10442,    // Rend's arena (B12)
        NPC_CHROMATIC_DRAGONSPAWN   = 10447,
        NPC_BLACKHAND_DRAGON_HANDLER = 10742,
        NPC_CHROMATIC_ELITE_GUARD   = 10814,    // Drakkisath's (B14; minion data)

        // new boss-kit creatures (ids.yaml reservation `blackrock_spire`, 300700-300779; declared by the boss WPs in
        // apps/dbc-tools source/npcs/blackrock_spire/). Wave 1 300700-300729, wave 2 300730-300779 (the heroic mint
        // order: every wave 1 add below every wave 2 add).
        NPC_BRS_BRAWL_FAN           = 300700,   // B1: crowd in the stands
        NPC_BRS_BRAWLER             = 300701,   // B1
        NPC_BRS_MOJO_MYSTIC         = 300702,   // B1: heroic, 12k, combat add
        NPC_BRS_VOODOO_DOLL         = 300703,   // B2: display 25017 (2 at 6+)
        NPC_BRS_CHAIN_ANCHOR        = 300704,   // B3: heroic Chained Axes anchor
        NPC_BRS_BROODLING           = 300705,   // B4: 2k / 3k, combat add
        NPC_BRS_STOLEN_MAGIC_SHARD  = 300706,   // B5 (reused by B9's Spirestone Champion)
        NPC_BRS_CLOCKWORK_SHEEP     = 300707,   // B6: heroic, 3k, combat add
        NPC_BRS_SPIRESTONE_CHAMPION = 300708,   // B8: 25k / 32k (hard mode 100k by script)
        NPC_BRS_SMOLDERTHORN_CHAMPION = 300709, // B8
        NPC_BRS_BLOODAXE_CHAMPION   = 300710,   // B8
        NPC_BRS_BLOODAXE_WORG_RIDER = 300711,   // B8 / B9
        NPC_BRS_TRIBE_THROWER       = 300712,   // B8
        NPC_BRS_STALKER             = 300713,   // shared generic stalker (ask the orchestrator)
        NPC_BRS_BINDING_POST        = 300730,   // B10 (x7 at the Incarcerators' spots)
        NPC_BRS_FLAME_WHELP         = 300731,   // B11
        NPC_BRS_NEFARIUS            = 300732,   // B12: Nefarius's BRS copy (spawn 137967 rebound; BWL's 10162 kept)
        NPC_BRS_BANNER              = 300733,   // B12: Banner of the Dark Horde
        NPC_BRS_FROST_WALL          = 300734,   // B12: frost wall trigger
        NPC_BRS_MOLTEN_BLOOD        = 300735,   // B13: Molten Blood pool trigger
        NPC_BRS_SQUAD_DRAGONSPAWN   = 300736,   // B15: Rage Talon squad copies
        NPC_BRS_SQUAD_CAPTAIN       = 300737,
        NPC_BRS_SQUAD_FIRE_TONGUE   = 300738,
        NPC_BRS_SQUAD_DRAGON_GUARD  = 300739,
        NPC_BRS_HERALD              = 300740,   // B15: the herald (gossip "Let them come")
        NPC_BRS_CHALLENGE_RING      = 300741,   // B15: the Champion's Challenge ring trigger
    };

    // Nefarius in BRS: the stock entry until B12 rebinds spawn 137967 to the copy.
    constexpr bool IsBrsNefarius(std::uint32_t entry)
    {
        return entry == NPC_LORD_VICTOR_NEFARIUS || entry == NPC_BRS_NEFARIUS;
    }

    // The boss state of a boss entry (a heroic copy's GetEntry() is its base entry); nullopt for anything else. The
    // stock event bosses (Valthalak, Mor Grayhoof) are BossAI and write their own slots, so they are not listed.
    constexpr std::optional<std::uint32_t> BossOfEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_OMOKK:         return BOSS_OMOKK;
            case NPC_VOSHGAJIN:     return BOSS_VOSHGAJIN;
            case NPC_VOONE:         return BOSS_VOONE;
            case NPC_SMOLDERWEB:    return BOSS_SMOLDERWEB;
            case NPC_UROK:          return BOSS_UROK;
            case NPC_ZIGRIS:        return BOSS_ZIGRIS;
            case NPC_GIZRUL:        return BOSS_GIZRUL;
            case NPC_HALYCON:       return BOSS_HALYCON;
            case NPC_WYRMTHALAK:    return BOSS_WYRMTHALAK;
            case NPC_EMBERSEER:     return BOSS_EMBERSEER;
            case NPC_REND:          return BOSS_REND;
            case NPC_GYTH:          return BOSS_GYTH;
            case NPC_BEAST:         return BOSS_BEAST;
            case NPC_DRAKKISATH:    return BOSS_DRAKKISATH;
            case NPC_SOLAKAR:       return BOSS_SOLAKAR;
            default:                return std::nullopt;
        }
    }

    // The entry of a boss state (the reverse of BossOfEntry; 0 for the other slots).
    constexpr std::uint32_t EntryOfBoss(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_OMOKK:        return NPC_OMOKK;
            case BOSS_VOSHGAJIN:    return NPC_VOSHGAJIN;
            case BOSS_VOONE:        return NPC_VOONE;
            case BOSS_SMOLDERWEB:   return NPC_SMOLDERWEB;
            case BOSS_UROK:         return NPC_UROK;
            case BOSS_ZIGRIS:       return NPC_ZIGRIS;
            case BOSS_GIZRUL:       return NPC_GIZRUL;
            case BOSS_HALYCON:      return NPC_HALYCON;
            case BOSS_WYRMTHALAK:   return NPC_WYRMTHALAK;
            case BOSS_EMBERSEER:    return NPC_EMBERSEER;
            case BOSS_REND:         return NPC_REND;
            case BOSS_GYTH:         return NPC_GYTH;
            case BOSS_BEAST:        return NPC_BEAST;
            case BOSS_DRAKKISATH:   return NPC_DRAKKISATH;
            case BOSS_SOLAKAR:      return NPC_SOLAKAR;
            case BOSS_VALTHALAK:    return NPC_VALTHALAK;
            case BOSS_MOR_GRAYHOOF: return NPC_MOR_GRAYHOOF;
            default:                return 0;
        }
    }

    constexpr bool IsBrsBossEntry(std::uint32_t entry)
    {
        return BossOfEntry(entry).has_value();
    }

    // Bosses that are summoned (no spawn row; never in ObjectData, cpp-scripts.md): tracked by hand by the instance.
    constexpr bool IsSummonedBoss(std::uint32_t entry)
    {
        return entry == NPC_UROK || entry == NPC_GIZRUL || entry == NPC_GYTH || entry == NPC_SOLAKAR;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum BrsGameObjects : std::uint32_t
    {
        // stock (blackrock_spire.h GameObjectsIds); the instance's GetGuidData keys are these entries (stock)
        GO_ROOKERY_EGG              = 175124,
        GO_EMBERSEER_IN             = 175244,   // [db] (216.44, -286.14, 76.94): the hall's door to Emberseer
        GO_EMBERSEER_DOORS          = 175705,   // [db] (175.13, -258.95, 91.56)
        GO_EMBERSEER_OUT            = 175153,   // [db] (113.75, -258.95, 91.56): door data, open once he is DONE
        GO_GYTH_ENTRY_DOOR          = 164726,   // [db] (108.04, -420.33): Rend's arena entry
        GO_GYTH_COMBAT_DOOR         = 175185,   // [db] (194.24, -420.23): the drake portcullis
        GO_GYTH_EXIT_DOOR           = 175186,   // [db] (92.96, -435.59): door data on Rend, passage
        GO_DRAKKISATH_DOOR_1        = 175946,   // [db] (45.19, -259.71, 106.53): door data on Drakkisath, passage
        GO_DRAKKISATH_DOOR_2        = 175947,   // [db] (45.19, -312.52, 106.53)
        GO_HALL_RUNE_1              = 175197,   // the hall runes, in stock rune order (DATA_HALL_RUNE_1..7)
        GO_HALL_RUNE_2              = 175199,
        GO_HALL_RUNE_3              = 175195,
        GO_HALL_RUNE_4              = 175200,
        GO_HALL_RUNE_5              = 175198,
        GO_HALL_RUNE_6              = 175196,
        GO_HALL_RUNE_7              = 175194,
        GO_EMBERSEER_RUNE_1         = 175266,
        GO_EMBERSEER_RUNE_2         = 175267,
        GO_EMBERSEER_RUNE_3         = 175268,
        GO_EMBERSEER_RUNE_4         = 175269,
        GO_EMBERSEER_RUNE_5         = 175270,
        GO_EMBERSEER_RUNE_6         = 175271,
        GO_EMBERSEER_RUNE_7         = 175272,
        GO_UROK_PILE                = 175621,   // [db] (-14.35, -395.83, 48.51) guid 99791
        GO_UROK_CHALLENGE           = 175584,   // summoned per attempt (tracked by hand)
        GO_UROK_CIRCLE              = 175571,   // summoned per attempt (tracked by hand)
        GO_BLACKROCK_ALTAR          = 175706,   // [db] (144.45, -280.94, 91.55) guid 87838
        GO_FATHER_FLAME             = 175245,   // [db] (76.00, -334.74, 91.51) guid 81163 (B11 rebinds)
        GO_DRAKKISATHS_BRAND        = 179880,   // untouched
        GO_SPIRE_SPIDER_EGG         = 175606,   // quest 4862 eggs, untouched

        // new (ids.yaml reservation `blackrock_spire`, 301250-301279; templates and spawns in the boss WPs' SQL revs)
        GO_BRS_STUCK_AXE            = 301250,   // B3 (display 8494)
        GO_BRS_SMOLDERWEB_EGG       = 301251,   // B4 (display 364)
        GO_BRS_SUPPLY_CRATE         = 301252,   // B6
        GO_BRS_NET_TRAP             = 301253,   // B6
        GO_BRS_POWDER_KEG           = 301254,   // B6
        GO_BRS_WAR_HORN             = 301255,   // B9: the Bloodaxe War Horn (heroic, before the pull)
    };

    // The hall runes in stock rune order (index i is boss state BOSS_HALL_RUNE_1 + i).
    inline std::array<std::uint32_t, kHallRuneCount> constexpr kHallRunes{ {
        GO_HALL_RUNE_1, GO_HALL_RUNE_2, GO_HALL_RUNE_3, GO_HALL_RUNE_4, GO_HALL_RUNE_5, GO_HALL_RUNE_6,
        GO_HALL_RUNE_7 } };

    inline std::array<std::uint32_t, 7> constexpr kEmberseerRunes{ {
        GO_EMBERSEER_RUNE_1, GO_EMBERSEER_RUNE_2, GO_EMBERSEER_RUNE_3, GO_EMBERSEER_RUNE_4, GO_EMBERSEER_RUNE_5,
        GO_EMBERSEER_RUNE_6, GO_EMBERSEER_RUNE_7 } };

    // The rune index of a hall rune entry; nullopt for anything else.
    constexpr std::optional<std::uint32_t> HallRuneIndex(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kHallRuneCount; ++i)
            if (kHallRunes[i] == entry)
                return i;
        return std::nullopt;
    }

    // The items the build touches. B11 (R-2 ruling 2026-11-15): Father Flame, the flame players toss, is a custom bag
    // item (70610, its on-use the toss; apps/dbc-tools source/world/blackrock_spire_father_flame.py, items.csv and the
    // Solakar SQL rev); the stock off-hand 13371 stays untouched as the keepsake (the holder at his death gets one).
    std::uint32_t constexpr kItemFatherFlame = 70610;
    std::uint32_t constexpr kItemFatherFlameKeepsake = 13371;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 210000-210699, ids.yaml reservation `blackrock_spire`; declared in apps/dbc-tools
    // source/npcs/blackrock_spire/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h. The
    // kit-wide 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h).
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 210000, 210699 };
    IdSlice constexpr kSpellsShared{ 210000, 210019 };          // kit cast bars, flex markers
    IdSlice constexpr kSpellsOmokk{ 210020, 210059 };           // B1  (OM)
    IdSlice constexpr kSpellsVoshgajin{ 210060, 210089 };       // B2  (VG)
    IdSlice constexpr kSpellsVoone{ 210090, 210119 };           // B3  (VO)
    IdSlice constexpr kSpellsSmolderweb{ 210120, 210149 };      // B4  (SW)
    IdSlice constexpr kSpellsUrok{ 210150, 210179 };            // B5  (UR; the shard and Stolen Power, reused by WT10)
    IdSlice constexpr kSpellsZigris{ 210180, 210209 };          // B6  (ZG)
    IdSlice constexpr kSpellsHalyconGizrul{ 210210, 210249 };   // B7  (HG)
    IdSlice constexpr kSpellsWyrmthalak{ 210250, 210289 };      // B8  (WT)
    IdSlice constexpr kSpellsWarHorn{ 210290, 210339 };         // B9  (WT hard mode)
    IdSlice constexpr kSpellsSpareWave1{ 210340, 210349 };
    IdSlice constexpr kSpellsEmberseer{ 210350, 210389 };       // B10 (EM)
    IdSlice constexpr kSpellsSolakar{ 210390, 210429 };         // B11 (SK; incl. the item 70610 toss)
    IdSlice constexpr kSpellsRendGyth{ 210430, 210489 };        // B12 (RG and the Nefarius copy)
    IdSlice constexpr kSpellsBeast{ 210490, 210519 };           // B13 (BE)
    IdSlice constexpr kSpellsDrakkisath{ 210520, 210559 };      // B14 (DR)
    IdSlice constexpr kSpellsGeneralsArmy{ 210560, 210619 };    // B15 (DR hard mode)
    IdSlice constexpr kSpellsSpare{ 210620, 210699 };

    inline std::array<IdSlice, 18> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsOmokk, kSpellsVoshgajin, kSpellsVoone, kSpellsSmolderweb, kSpellsUrok, kSpellsZigris,
        kSpellsHalyconGizrul, kSpellsWyrmthalak, kSpellsWarHorn, kSpellsSpareWave1, kSpellsEmberseer, kSpellsSolakar,
        kSpellsRendGyth, kSpellsBeast, kSpellsDrakkisath, kSpellsGeneralsArmy, kSpellsSpare } };

    IdSlice constexpr kCreaturesReservation{ 300700, 300779 };
    IdSlice constexpr kCreaturesWave1{ 300700, 300729 };
    IdSlice constexpr kCreaturesWave2{ 300730, 300779 };
    IdSlice constexpr kGameObjectsReservation{ 301250, 301279 };

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text groups per boss, SP's text tables). A boss WP names its groups in its own Logic header
    // (enum <Boss>Texts : std::uint8_t { SAY_..., EMOTE_... }) inside its range; groups below `firstNew` are stock rows
    // (kept, sometimes re-used for a new moment). The SQL rev of the boss WP writes the new rows.
    // ----------------------------------------------------------------------------------------------------------------
    struct TextRange
    {
        std::uint32_t entry;
        std::uint8_t first;
        std::uint8_t last;
        std::uint8_t firstNew;      // groups first..firstNew-1 are stock rows
    };

    inline std::array<TextRange, 15> constexpr kTextRanges{ {
        { NPC_OMOKK, 0, 7, 0 },             // B1 (no stock text)
        { NPC_VOSHGAJIN, 0, 3, 0 },         // B2
        { NPC_VOONE, 0, 5, 0 },             // B3
        { NPC_SMOLDERWEB, 0, 2, 0 },        // B4
        { NPC_UROK, 0, 5, 2 },              // B5: 0-1 stock
        { NPC_ZIGRIS, 0, 5, 0 },            // B6
        { NPC_HALYCON, 0, 4, 1 },           // B7: 0 stock (the death emote)
        { NPC_GIZRUL, 0, 3, 0 },            // B7
        { NPC_WYRMTHALAK, 0, 9, 1 },        // B8 / B9: 0 stock; 7 is the war horn line
        { NPC_EMBERSEER, 0, 7, 4 },         // B10: 0-3 stock (moved)
        { NPC_BRS_NEFARIUS, 0, 19, 12 },    // B12 / B15: 0-11 copied from 10162; 18-19 the insult
        { NPC_REND, 0, 4, 3 },              // B12: 0-2 stock
        { NPC_BEAST, 0, 2, 0 },             // B13
        { NPC_DRAKKISATH, 0, 9, 0 },        // B14 / B15: 9 is the hard mode line
        { NPC_BRS_HERALD, 0, 0, 0 },        // B15 (its gossip is SQL; its lines are B15's call)
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // Flex (handoff section 3.12; mod-dungeon-difficulties FlexScale.h through the kit wrapper DungeonKitFlex.h, the
    // pure rules DungeonKitFlexRules.h). The held count N (5..10) is read once at the pull (DungeonKit::Flex::OnPull in
    // JustEngagedWith: it holds the count, scales health and sets the flex loot bits); a boss's target counts are a
    // pair "a / b": a at 5 players, b at 6 or more. A boss WP keeps its pairs in its Logic header as FlexAB constants.
    // ----------------------------------------------------------------------------------------------------------------
    struct FlexAB
    {
        std::uint8_t a;     // at 5 players (a held count of 0, "not held", reads as 5)
        std::uint8_t b;     // at 6 or more

        constexpr std::uint8_t At(std::uint32_t players) const { return DungeonKit::Flex::TargetCount(players, a, b); }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (section 3.8 and the NAVMESH report's tables)
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

    // Boss spawns [db] (Urok, Gizrul, Gyth and Solakar have none: summoned).
    Point3 constexpr kOmokkSpawn{ -22.79f, -300.68f, 31.80f };
    Point3 constexpr kVoshgajinSpawn{ -121.19f, -482.18f, 24.71f };
    Point3 constexpr kVooneSpawn{ -16.98f, -459.15f, -18.64f };
    Point3 constexpr kSmolderwebSpawn{ -135.51f, -565.85f, 10.17f };
    Point3 constexpr kZigrisSpawn{ -190.46f, -475.58f, 87.39f };
    Point3 constexpr kHalyconSpawn{ -193.91f, -338.15f, 64.49f };
    Point3 constexpr kWyrmthalakSpawn{ -22.63f, -486.19f, 90.75f };
    Point3 constexpr kEmberseerSpawn{ 144.44f, -258.03f, 96.41f };
    Point3 constexpr kRendSpawn{ 159.28f, -443.62f, 122.06f };          // the balcony, 11 yd above the arena floor
    Point3 constexpr kNefariusSpawn{ 163.17f, -444.17f, 122.06f };      // spawn guid 137967
    Point3 constexpr kBeastSpawn{ 124.21f, -563.80f, 107.43f };
    Point3 constexpr kDrakkisathSpawn{ 36.45f, -285.99f, 111.04f };
    // The stock summon spots [db: smart_scripts 17558400 and the stock instance].
    Point4 constexpr kUrokSummon{ -28.57f, -395.78f, 48.78f, 1.41f };
    Point3 constexpr kGizrulSpawn{ -168.0f, -411.8f, 76.2f };           // path 402450 start (B7's run in)
    Point4 constexpr kGythSummon{ 211.8f, -397.6f, 111.2f, 0.f };       // 28.6 yd behind the drake portcullis
    Point4 constexpr kSolakarPosLeft{ 78.0f, -280.0f, 93.0f, 4.712389f };   // stock SolakarPosLeft
    Point4 constexpr kSolakarPosRight{ 84.0f, -280.0f, 93.0f, 4.712389f };  // stock SolakarPosRight
    Point4 constexpr kSolakarPosBoss{ 80.0f, -280.0f, 93.0f, 4.712389f };   // stock SolakarPosBoss

    // --- Highlord Omokk (B1, NM 1) -----------------------------------------------------------------------------------
    // The showdown on the bridge (heroic, 25%): his landing, the two haul-up spots at the doors, the five landings at
    // 5 players and the two more at 10 (the bay-wing spots and the platform wing's twin are too near the edge).
    Point3 constexpr kOmokkShowdownLanding{ -37.2f, -418.2f, 31.8f };
    Point3 constexpr kOmokkHaulUpWest{ -37.2f, -399.8f, 31.8f };
    Point3 constexpr kOmokkHaulUpEast{ -37.2f, -440.8f, 31.8f };
    inline std::array<Point3, 7> constexpr kOmokkLandings{ {
        { -37.8f, -405.8f, 31.8f }, { -37.8f, -410.2f, 31.8f }, { -37.8f, -426.2f, 31.8f }, { -37.2f, -434.8f, 31.8f },
        { -44.2f, -430.2f, 31.8f },     // the five at 5 players
        { -49.8f, -434.8f, 31.8f }, { -24.8f, -434.8f, 31.8f } } };     // plus these at 10
    float constexpr kOmokkBridgeDeckZ = 31.8f;
    float constexpr kOmokkPitFloorZ = -18.9f;           // 50.8 yd under the deck
    float constexpr kOmokkPitDropZ = 16.8f;             // the deck less 15 yd: the Pit Drop catch line

    // --- War Master Voone (B3, NM 3) ---------------------------------------------------------------------------------
    Point3 constexpr kVooneChargeSpot{ -26.2f, -481.2f, -18.6f };       // the troll hall, 23.6 yd from him (VO1 jump)
    Point3 constexpr kVooneGate{ -29.8f, -450.7f, -18.6f };             // his quarters' one opening (7 yd wide)

    // --- Mother Smolderweb (B4, NM 4): the eight proposed egg spots (z >= 7, clearance >= 5, >= 16 yd from her) ------
    inline std::array<Vec2, 8> constexpr kSmolderwebEggSpots{ {
        { -127.8f, -521.2f }, { -119.8f, -572.8f }, { -149.8f, -548.2f }, { -136.8f, -536.2f },
        { -116.8f, -561.2f }, { -137.2f, -547.2f }, { -146.8f, -535.8f }, { -143.8f, -543.2f } } };

    // --- Urok Doomhowl (B5, NM 5) ------------------------------------------------------------------------------------
    Point3 constexpr kUrokPile{ -14.35f, -395.83f, 48.51f };            // [db]

    // --- Quartermaster Zigris (B6, NM 6): the three crates (wall-side, >= 27.9 yd apart; crate 2 is the mortar's) ----
    inline std::array<Vec2, 3> constexpr kZigrisCrates{ { { -203.8f, -487.8f }, { -210.8f, -460.8f },
        { -184.8f, -450.8f } } };

    // --- Halycon and Gizrul (B7, NM 7) -------------------------------------------------------------------------------
    Vec2 constexpr kHalyconDenMouth{ -173.4f, -326.0f };

    // --- Overlord Wyrmthalak (B8 / B9, NM 8) -------------------------------------------------------------------------
    Point3 constexpr kWarHornSpot{ -52.5f, -503.0f, 89.1f };            // the ramp head (south-west shoulder)
    Vec2 constexpr kWyrmthalakEdgeA0{ -34.8f, -470.8f };                // the one open edge (chord 28.2 yd)
    Vec2 constexpr kWyrmthalakEdgeA1{ -47.8f, -495.8f };

    // --- Pyroguard Emberseer (B10, NM 9): the seven posts on a 36 yd square [db: the Incarcerators' spawns] ----------
    inline std::array<Vec2, 7> constexpr kEmberseerPosts{ {
        { 126.31f, -258.63f }, { 162.46f, -258.96f }, { 144.28f, -240.99f },        // axis posts
        { 126.45f, -276.60f }, { 126.51f, -240.90f }, { 162.22f, -240.97f }, { 162.33f, -276.76f } } };  // diagonals
    Point3 constexpr kBlackrockAltar{ 144.45f, -280.94f, 91.55f };      // [db]

    // --- Solakar (B11, NM 10) ----------------------------------------------------------------------------------------
    Point3 constexpr kFatherFlame{ 76.0f, -334.74f, 91.51f };           // [db]

    // --- Rend and Gyth (B12, NM 11) ----------------------------------------------------------------------------------
    Point3 constexpr kGythHoverGround{ 190.0f, -420.2f, 110.9f };       // 4.2 yd inside the portcullis
    Point3 constexpr kStadiumTrigger{ 153.76f, -419.83f, 110.47f };     // [db] areatrigger 2026, r 20

    // --- The Beast (B13, NM 12) --------------------------------------------------------------------------------------
    Point3 constexpr kBeastTrigger2066{ 75.26f, -547.68f, 110.93f };    // [db] r 30
    Point3 constexpr kBeastTrigger2067{ 26.46f, -522.47f, 110.94f };    // [db] r 15

    // --- General Drakkisath (B14 / B15, NM 13) -----------------------------------------------------------------------
    Point3 constexpr kDrakkisathGate1{ 45.19f, -259.71f, 106.53f };     // [db] 175946
    Point3 constexpr kDrakkisathGate2{ 45.19f, -312.52f, 106.53f };     // [db] 175947

    // ----------------------------------------------------------------------------------------------------------------
    // The Dragonspire Hall (the rune room, handoff section 10 "rune room hardening"). The seven hall runes stand at
    // x 124.8..228.8, y -353.0..-258.4, z 70.8 and 76.9 [db]; area trigger 2046 is at (102.43, -319.17, 65.46) r 10
    // [db], at the hall's west mouth. A living player (not a GM) inside kDragonspireHall starts the room check on its
    // own while the room is not DONE: on load, on a player's entry and on a periodic watch, so a reload or a Finder or
    // checkpoint start inside the hall no longer leaves the doors shut. The stock room check (a rune closes when the
    // Blackhand packs within 15 yd of it are dead) stays.
    // ----------------------------------------------------------------------------------------------------------------
    Box2 constexpr kDragonspireHall{ 98.f, 238.f, -362.f, -248.f };
    // The Upper Spire's Finder start (lfg_override(44) in DT source/world/lfg_classic_heroic.py) and its entrance
    // checkpoint (mod-dungeon-checkpoint u_dungeon_checkpoint_2026_11_15_00.sql) stand 0.25 yd inside the hall's west
    // edge: an arrival or a checkpoint respawn there starts the self-start about 1 s later, by design (the packs are
    // at rest, section 10 allows it). The stock area trigger 2046 is 19 yd further on. Pinned by
    // blackrock_spire_test (inside the box) and DT test_blackrock_spire_kit (the three copies agree), so a later
    // `.gps` nudge cannot silently flip it (R-1-KIT K-m3).
    Point3 constexpr kUbrsFinderStart{ 98.25f, -300.75f, 63.1f };
    float constexpr kDragonspireHallZMin = 62.f;
    float constexpr kDragonspireHallZMax = 86.f;
    float constexpr kHallRunePackRadius = 15.f;         // stock: the pack of a rune is within 15 yd of it
    std::uint32_t constexpr kRoomStoreDelayMs = 1000;   // stock: the trigger's STORE 1 s later
    std::uint32_t constexpr kRoomCheckMs = 3000;        // stock: CHECK every 3 s until the room is DONE
    std::uint32_t constexpr kRoomWatchMs = 5000;        // the self-start's watch

    constexpr bool InDragonspireHall(float x, float y, float z)
    {
        return x >= kDragonspireHall.minX && x <= kDragonspireHall.maxX && y >= kDragonspireHall.minY
            && y <= kDragonspireHall.maxY && z >= kDragonspireHallZMin && z <= kDragonspireHallZMax;
    }

    // STORE: a rune already DONE is never snapshotted again (ruling); a rune whose grid is not loaded is left for the
    // next STORE (its pack would read as dead).
    constexpr bool RuneShouldSnapshot(std::uint32_t runeState, bool gridLoaded)
    {
        return runeState != DungeonKit::State::Done && gridLoaded;
    }

    // CHECK: a rune closes (goes DONE) when it was snapshotted, is still lit, its grid is loaded and no creature of
    // its snapshot is alive.
    constexpr bool RuneShouldClose(std::uint32_t runeState, bool snapshotted, bool goActive, bool gridLoaded,
        bool anyAlive)
    {
        return runeState != DungeonKit::State::Done && snapshotted && goActive && gridLoaded && !anyAlive;
    }

    // The room check starts on its own when the room is not DONE, a player stands in the hall and some rune not DONE
    // still lacks a snapshot (the trigger's STORE or an earlier self-start took the rest).
    constexpr bool RoomNeedsSelfStart(std::uint32_t roomState, bool playerInHall, bool anyRuneUnsnapshotted)
    {
        return roomState != DungeonKit::State::Done && playerInHall && anyRuneUnsnapshotted;
    }

    constexpr bool AllRunesDone(std::array<std::uint32_t, kHallRuneCount> const& runeStates)
    {
        for (std::uint32_t const s : runeStates)
            if (s != DungeonKit::State::Done)
                return false;
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Urok's tribute pile (DATA_UROK_PILE; SP UR1, ruling 39): usable once Omokk is DONE, again after a wipe, spent
    // when Urok is DONE. The stock path (event 4845 from the pile's SmartGO, SetData(4, FAIL) on a failed challenge)
    // keeps working until B5 replaces it with its own GO script; B5's script uses the pile only while it is READY.
    // ----------------------------------------------------------------------------------------------------------------
    enum UrokPile : std::uint32_t
    {
        PILE_LOCKED     = 0,    // Omokk is alive
        PILE_READY      = 1,
        PILE_IN_USE     = 2,    // the challenge runs (not saved: a reload ends it)
        PILE_SPENT      = 3,    // Urok is dead
    };

    constexpr std::uint32_t UrokPileState(std::uint32_t omokkState, std::uint32_t urokState, bool inUse)
    {
        if (urokState == DungeonKit::State::Done)
            return PILE_SPENT;
        if (inUse)
            return PILE_IN_USE;
        return omokkState == DungeonKit::State::Done ? std::uint32_t(PILE_READY) : std::uint32_t(PILE_LOCKED);
    }

    constexpr bool UrokPileUsable(std::uint32_t pile) { return pile == PILE_READY; }

    // ----------------------------------------------------------------------------------------------------------------
    // The Solakar event (DATA_SOLAKAR_EVENT 23, the stock data id; SP notes 1 and 3). Stock wrote FAIL over its own
    // reset, so a failed event never started again (note 1): a FAIL now ends NOT_STARTED. DONE is final (his BossAI
    // slot 23 persists it); an IN_PROGRESS write starts it only from NOT_STARTED (stock).
    // ----------------------------------------------------------------------------------------------------------------
    constexpr std::uint32_t SolakarEventAfterWrite(std::uint32_t current, std::uint32_t data)
    {
        if (current == DungeonKit::State::Done)
            return current;
        switch (data)
        {
            case DungeonKit::State::InProgress:
                return current == DungeonKit::State::NotStarted ? data : current;
            case DungeonKit::State::Fail:
            case DungeonKit::State::NotStarted:
                return DungeonKit::State::NotStarted;
            case DungeonKit::State::Done:
                return data;
            default:
                return current;
        }
    }

    // Starts the event (the transition into IN_PROGRESS).
    constexpr bool SolakarEventStarts(std::uint32_t before, std::uint32_t after)
    {
        return before == DungeonKit::State::NotStarted && after == DungeonKit::State::InProgress;
    }

    // B11 (SK1, SP ruling 57): the event is one pair (a Rookery Guardian and a Rookery Hatcher at the stock spots) and
    // Solakar, summoned hidden with the pair (his AI owns Father Flame from the first second) and arriving 30 s later
    // whatever is left. The instance sends his AI these actions (CreatureAI::DoAction).
    std::uint32_t constexpr kSolakarArriveMs = 30000;
    enum SolakarActions : std::int32_t
    {
        ACTION_SOLAKAR_ARRIVE   = 0x534B0001,   // the 30 s mark: he shows himself and engages
        ACTION_SOLAKAR_RESET    = 0x534B0002,   // the event failed (a wipe, or a GM): flame, items, eggs and whelps go
    };

    // Father Flame's held flame (DATA_SOLAKAR_FLAME; B11 writes it, the reset reads it).
    enum SolakarFlame : std::uint32_t
    {
        FLAME_NONE      = 0,    // nobody took it (or the fight reset)
        FLAME_HOLDER    = 1,    // a player holds it
        FLAME_FLOOR     = 2,    // dropped on the floor
        FLAME_BRAZIER   = 3,    // back in Father Flame
    };
    std::uint32_t constexpr kSolakarFlameMax = FLAME_BRAZIER;

    // Is a flame write worth an instance save? A held or dropped flame is per attempt (SanitizeBrsSave drops it on
    // load), so tosses, snatches and drops never save (R-2 n-1).
    constexpr bool SolakarFlameSaved(std::uint32_t flame)
    {
        return flame != FLAME_HOLDER && flame != FLAME_FLOOR;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hard modes (section 3.7) and the insult
    // ----------------------------------------------------------------------------------------------------------------
    // B9: the war horn lights only on heroic, out of combat, before the kill; clearing it is refused mid-fight.
    constexpr bool WarHornChangeAllowed(std::uint32_t data, bool heroic, std::uint32_t wyrmthalakState)
    {
        if (wyrmthalakState == DungeonKit::State::InProgress)
            return false;
        if (!data)
            return true;
        return heroic && wyrmthalakState != DungeonKit::State::Done;
    }

    // B12: the insult is saved once given (wave 2 bound, Drakkisath not dead); a 0 clears it (GM test), never while
    // he fights.
    constexpr bool InsultChangeAllowed(std::uint32_t data, bool wave2Bound, std::uint32_t drakkisathState)
    {
        if (drakkisathState == DungeonKit::State::InProgress)
            return false;
        if (!data)
            return true;
        return wave2Bound && drakkisathState != DungeonKit::State::Done;
    }

    // B15: the herald arms the General's Army for the next pull: heroic, wave 2 bound, the insult saved, Drakkisath
    // neither fighting nor dead.
    constexpr bool GeneralsArmyChangeAllowed(std::uint32_t data, bool heroic, bool wave2Bound, bool insulted,
        std::uint32_t drakkisathState)
    {
        if (drakkisathState == DungeonKit::State::InProgress)
            return false;
        if (!data)
            return true;
        return heroic && wave2Bound && insulted && drakkisathState != DungeonKit::State::Done;
    }

    // A per-pull flag ends when its boss's attempt ends (the state leaves IN_PROGRESS for NOT_STARTED or FAIL).
    constexpr bool AttemptEnded(std::uint32_t before, std::uint32_t after)
    {
        return before == DungeonKit::State::InProgress
            && (after == DungeonKit::State::NotStarted || after == DungeonKit::State::Fail);
    }

    // A slot no Load and no boss AI wrote is still TO_BE_DECIDED at the first Update (the runes, the room, the hard
    // mode kill slots 26/27, a boss whose grid never loaded). InstanceScript::SetBossState treats TO_BE_DECIDED as
    // "loading": the first write is stored without SaveToDB and without this script's switch, so a rune, room or
    // hard mode kill DONE written first would be lost on a restart (R-1-KIT K-m1, R-1-B m3). The instance settles
    // them to NOT_STARTED once (a plain store, nothing else runs); every later write saves.
    constexpr std::uint32_t SettledSlotState(std::uint32_t state)
    {
        return state == DungeonKit::State::ToBeDecided ? std::uint32_t(DungeonKit::State::NotStarted) : state;
    }

    // B7's restart soft-lock: Halycon fell first, her spawn's respawn time was saved, then the server restarted (or
    // the den's grid reloaded) and Gizrul (a summon) is gone. A dead Halycon whose slot is not DONE with no living
    // Gizrul is respawned by the instance; her pull clears the stale 273/274 credits itself.
    constexpr bool HalyconNeedsRespawn(std::uint32_t halyconState, bool halyconAlive, bool gizrulAlive)
    {
        return halyconState != DungeonKit::State::Done && !halyconAlive && !gizrulAlive;
    }
    std::uint32_t constexpr kHalyconRespawnDelayMs = 1000;  // after her create: never Respawn inside AddToMap

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (the leash frames of the stubs; section 3.8). Each boss WP writes its final polygon from the NM hull after
    // the playtest's `.gps` walk. Boxes reach about 0.5 yd past the mesh (the agent shrink).
    // ----------------------------------------------------------------------------------------------------------------
    inline ArenaRegion BoxRegion(float minX, float maxX, float minY, float maxY, float zMin, float zMax)
    {
        return ArenaRegion::Polygon({ { minX, minY }, { maxX, minY }, { maxX, maxY }, { minX, maxY } }, zMin, zMax);
    }

    inline Arena PolygonArena(std::vector<Vec2> points, float zMin, float zMax)
    {
        return Arena(ArenaRegion::Polygon(std::move(points), zMin, zMax));
    }

    // Omokk: the hall with its north-wall alcoves, the rock pile and ledge south of it, and the bridge of the heroic
    // showdown.
    inline Arena OmokkArena()
    {
        return Arena(std::vector<ArenaRegion>{
            BoxRegion(-27.5f, -9.7f, -360.5f, -294.0f, 29.5f, 37.0f),     // hall x -26.8..-14.8 + alcoves to -10.2
            BoxRegion(-59.5f, -26.0f, -360.5f, -294.0f, 32.0f, 47.0f),    // rock pile and ledge
            BoxRegion(-51.0f, -23.0f, -442.0f, -397.0f, 29.0f, 35.0f) }); // the bridge
    }

    inline Arena VoshgajinArena() { return Arena(BoxRegion(-128.5f, -84.5f, -493.5f, -469.5f, 22.0f, 29.0f)); }

    // Voone: his quarters and the troll hall he charges into (VO1).
    inline Arena VooneArena()
    {
        return Arena(std::vector<ArenaRegion>{
            BoxRegion(-30.5f, -8.3f, -465.5f, -444.3f, -21.5f, -15.5f),
            BoxRegion(-57.7f, 1.7f, -546.3f, -472.3f, -22.5f, -14.0f) });
    }

    inline Arena SmolderwebArena()
    {
        return PolygonArena({ { -154.7f, -576.7f }, { -107.2f, -577.7f }, { -98.3f, -566.2f }, { -99.7f, -517.8f },
            { -123.8f, -499.7f }, { -130.2f, -499.7f }, { -152.3f, -523.8f }, { -154.7f, -531.2f } }, 4.0f, 16.0f);
    }

    inline Arena UrokArena() { return Arena(BoxRegion(-66.3f, -6.7f, -406.3f, -359.7f, 44.0f, 56.0f)); }

    inline Arena ZigrisArena()
    {
        return PolygonArena({ { -213.7f, -491.3f }, { -184.8f, -491.3f }, { -181.7f, -490.7f }, { -181.7f, -445.3f },
            { -213.7f, -445.3f }, { -214.3f, -472.2f } }, 85.0f, 92.0f);
    }

    // Halycon's den and the hall corridor Gizrul runs in through.
    inline Arena HalyconGizrulArena()
    {
        return Arena(std::vector<ArenaRegion>{
            ArenaRegion::Polygon({ { -204.3f, -319.8f }, { -193.2f, -356.3f }, { -187.8f, -355.7f },
                { -180.7f, -344.2f }, { -178.3f, -321.8f }, { -180.7f, -307.7f }, { -197.2f, -309.3f },
                { -203.3f, -314.8f } }, 62.0f, 70.0f),
            BoxRegion(-176.3f, -158.7f, -388.5f, -318.0f, 61.0f, 69.0f) });
    }

    inline Arena WyrmthalakArena()
    {
        return PolygonArena({ { -53.3f, -501.8f }, { -42.8f, -511.7f }, { -10.8f, -504.7f }, { -5.7f, -489.2f },
            { -6.7f, -477.2f }, { -20.2f, -461.7f }, { -29.2f, -461.7f }, { -41.7f, -479.2f }, { -47.7f, -488.8f } },
            87.0f, 95.0f);
    }

    // Wave 2. Emberseer's hall between the door lines, the dais (z 96) included.
    inline Arena EmberseerArena() { return Arena(BoxRegion(114.5f, 174.5f, -288.7f, -228.7f, 89.0f, 98.5f)); }
    inline Arena SolakarArena() { return Arena(BoxRegion(48.0f, 108.0f, -338.5f, -252.0f, 88.0f, 100.0f)); }
    // Rend's arena floor between the way-in door (x 108) and the portcullis (x 194.2); the balcony is not in it.
    inline Arena RendGythArena() { return Arena(BoxRegion(108.5f, 194.0f, -454.5f, -385.5f, 108.0f, 115.0f)); }

    // The Beast: the hall and the pit bowl.
    inline Arena BeastArena()
    {
        return Arena(std::vector<ArenaRegion>{
            BoxRegion(15.7f, 84.3f, -562.3f, -511.7f, 109.0f, 114.0f),
            BoxRegion(87.5f, 145.5f, -581.5f, -539.5f, 105.0f, 115.0f) });
    }

    // Drakkisath: the main hall and his alcove (the floor runs on south to y -380; walk it before widening).
    inline Arena DrakkisathArena()
    {
        return Arena(std::vector<ArenaRegion>{
            BoxRegion(-21.7f, 28.7f, -325.3f, -248.3f, 109.0f, 116.0f),
            BoxRegion(28.3f, 43.7f, -310.3f, -261.7f, 109.0f, 116.0f) });
    }

    // The arena of a boss state (the hard mode slots: their boss's; the stock and room slots: none).
    inline Arena ArenaFor(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_OMOKK:            return OmokkArena();
            case BOSS_VOSHGAJIN:        return VoshgajinArena();
            case BOSS_VOONE:            return VooneArena();
            case BOSS_SMOLDERWEB:       return SmolderwebArena();
            case BOSS_UROK:             return UrokArena();
            case BOSS_ZIGRIS:           return ZigrisArena();
            case BOSS_GIZRUL:
            case BOSS_HALYCON:          return HalyconGizrulArena();
            case BOSS_WYRMTHALAK:
            case BOSS_WAR_HORN:         return WyrmthalakArena();
            case BOSS_EMBERSEER:        return EmberseerArena();
            case BOSS_SOLAKAR:          return SolakarArena();
            case BOSS_REND:
            case BOSS_GYTH:             return RendGythArena();
            case BOSS_BEAST:            return BeastArena();
            case BOSS_DRAKKISATH:
            case BOSS_GENERALS_ARMY:    return DrakkisathArena();
            default:                    return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Completed-encounter bits (DungeonEncounter.dbc 267-280, verified 2026-11-15; mod-dungeon-clear keys its kills on
    // them): bit -> boss state. Used to fill in the boss states of a stock save (the SmartAI bosses Vosh'gajin,
    // Smolderweb and Gizrul never wrote theirs, Solakar's slot was never saved).
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<std::pair<std::uint32_t, std::uint32_t>, 14> constexpr kEncounterBits{ {
        { 0, BOSS_OMOKK }, { 1, BOSS_VOSHGAJIN }, { 2, BOSS_VOONE }, { 3, BOSS_SMOLDERWEB }, { 4, BOSS_UROK },
        { 5, BOSS_ZIGRIS }, { 6, BOSS_GIZRUL }, { 7, BOSS_HALYCON }, { 8, BOSS_WYRMTHALAK }, { 9, BOSS_EMBERSEER },
        { 10, BOSS_SOLAKAR }, { 11, BOSS_REND }, { 12, BOSS_BEAST }, { 13, BOSS_DRAKKISATH } } };

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string: header "BRW" (never "BR": a prefix of the stock "B R S" would hide a stock save from
    // the legacy reader), the 28 boss states, then the extras below. A stock save (instance_blackrock_spire at
    // 8eb009fdf: "B R S" and 23 boss states, no extras) is still read: its states come over, and the
    // completed-encounter mask (set before Load, from the DBC bits) fills in the ones stock never wrote. The war horn
    // and the General's Army are per pull and not saved (SP WT17, DR19); the insult is (SP 3838-3840).
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "BRW";
    char constexpr kStockSaveHeader[] = "BRS";

    enum SaveExtra : std::size_t
    {
        EXTRA_NEF_INSULTED      = 0,
        EXTRA_UROK_PILE         = 1,
        EXTRA_SOLAKAR_EVENT     = 2,
        EXTRA_SOLAKAR_FLAME     = 3,
    };
    std::size_t constexpr kSaveExtraCount = 4;

    struct BrsSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        std::uint32_t nefInsulted = 0;
        std::uint32_t urokPile = PILE_LOCKED;
        std::uint32_t solakarEvent = DungeonKit::State::NotStarted;
        std::uint32_t solakarFlame = FLAME_NONE;
    };

    inline std::string FormatBrsSave(BrsSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_NEF_INSULTED] = s.nefInsulted;
        extras[EXTRA_UROK_PILE] = s.urokPile;
        extras[EXTRA_SOLAKAR_EVENT] = s.solakarEvent;
        extras[EXTRA_SOLAKAR_FLAME] = s.solakarFlame;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The boss states a completed-encounter mask records (DONE), OR-ed into `states`.
    inline void ApplyEncounterMask(std::uint32_t mask, std::array<std::uint32_t, kBossCount>& states)
    {
        for (auto const& [bit, boss] : kEncounterBits)
            if (mask & (1u << bit))
                states[boss] = DungeonKit::State::Done;
    }

    // Loaded values that cannot be trusted are put back in range; the per-attempt ones end with the attempt (a reload
    // ends every fight): the pile is derived from Omokk and Urok again, the Solakar event keeps only DONE, a held or
    // dropped flame goes back to nobody. The insult is kept (wave 2 checks it again at the herald).
    inline void SanitizeBrsSave(BrsSave& s)
    {
        s.nefInsulted = s.nefInsulted ? 1 : 0;
        s.urokPile = UrokPileState(s.states[BOSS_OMOKK], s.states[BOSS_UROK], false);
        if (s.states[BOSS_SOLAKAR] == DungeonKit::State::Done)
            s.solakarEvent = DungeonKit::State::Done;
        else if (s.solakarEvent != DungeonKit::State::Done)
            s.solakarEvent = DungeonKit::State::NotStarted;
        if (s.solakarFlame > kSolakarFlameMax || s.solakarFlame == FLAME_HOLDER || s.solakarFlame == FLAME_FLOOR)
            s.solakarFlame = FLAME_NONE;
        s.states[BOSS_VAELASTRASZ_SLOT] = DungeonKit::State::NotStarted;
    }

    // The stock "B R S <23 boss states>" (instance_blackrock_spire at 8eb009fdf; the base InstanceScript save with
    // EncounterCount 23 and no extras). False without at least one state.
    inline bool ReadStockSave(std::string const& in, BrsSave& out)
    {
        std::vector<std::uint32_t> f;
        if (!DungeonKit::ReadSaveFields(in, kStockSaveHeader, 1, kStockEncounterCount, f))
            return false;
        for (std::size_t i = 0; i < f.size(); ++i)
            out.states[i] = DungeonKit::SanitizeLoadedState(f[i]);
        return true;
    }

    // Reads this script's "B R W" string, or a stock one; `encounterMask` is the instance's completed-encounter mask
    // (applied to a stock save only: a "B R W" save carries its own states). False on anything else (ignored).
    inline bool ParseBrsSave(std::string const& in, BrsSave& out, std::uint32_t encounterMask = 0)
    {
        out = BrsSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        BrsSave stockSave;
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
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        if (!stock)
        {
            out.nefInsulted = raw.extras[EXTRA_NEF_INSULTED];
            out.urokPile = raw.extras[EXTRA_UROK_PILE];
            out.solakarEvent = raw.extras[EXTRA_SOLAKAR_EVENT];
            out.solakarFlame = raw.extras[EXTRA_SOLAKAR_FLAME];
        }
        SanitizeBrsSave(out);
        return true;
    }

    inline char const* UrokPileName(std::uint32_t pile)
    {
        switch (pile)
        {
            case PILE_LOCKED:   return "locked (Omokk alive)";
            case PILE_READY:    return "ready";
            case PILE_IN_USE:   return "in use";
            case PILE_SPENT:    return "spent (Urok dead)";
            default:            return "?";
        }
    }

    inline char const* SolakarFlameName(std::uint32_t flame)
    {
        switch (flame)
        {
            case FLAME_NONE:    return "none";
            case FLAME_HOLDER:  return "held";
            case FLAME_FLOOR:   return "on the floor";
            case FLAME_BRAZIER: return "in the brazier";
            default:            return "?";
        }
    }
}

#endif
