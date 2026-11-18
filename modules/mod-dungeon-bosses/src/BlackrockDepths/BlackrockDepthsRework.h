/*
 * mod-dungeon-bosses, Blackrock Depths (map 230): the shared ids, boss states, data fields, texts, measured points,
 * frames, arenas, the Finder sections, the save string and the instance rules of the Blackrock Depths build
 * (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md sections 3.1-3.3, 3.7, 3.8 and the user
 * rulings of section 10; build spec docs/dungeons/blackrock-depths-rework.md, "HUB", and the four section docs
 * blackrock-depths-{1-detention-block,2-shadowforge-city,3-manufactory,4-imperial-seat}.md, "S1"-"S4").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h), so
 * every <Boss>Logic.h and its host test can include it. Engine glue: the shared kit (src/Kit/DungeonKit.h) and the
 * Blackrock Depths glue (BlackrockDepthsKit.h).
 *
 * Ownership: this file belongs to WP-S0 (the Blackrock Depths skeleton) until it reports, then to the orchestrator. A
 * boss WP keeps its own spell ids (inside its slice below), tuning constants and script-local enums in its own
 * <Boss>Logic.h (convention: `enum <Boss>Spells : std::uint32_t { SPELL_<BOSS>_... = <id in its slice> }` and
 * `inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), and asks the orchestrator, in its report, for any
 * change here. Blackrock Depths is not flex (HUB ruling 3): 5 players on every difficulty.
 *
 * Measured points, frames and arenas are [navmesh estimate] (blackrock-depths-build.NAVMESH-REPORT.md, folded into the
 * handoff's section 3.8: the mesh sits about 0.5 yd inside every wall) unless marked [db] (creature, gameobject or
 * areatrigger rows, exact). Axes: +x north, +y west. A boss WP tightens its own arena in its own file after the
 * playtest's `.gps` walk; the arenas here are the leash frames of the stubs.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_REWORK_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_REWORK_H

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

namespace BlackrockDepthsRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Box2;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapBlackrockDepths = 230;
    // The stock instance name (handoff section 3.1, section 7 #1): the rework replaces the stock InstanceMapScript of
    // that name at load (same-named scripts registered later win; modules load after the core scripts), so
    // instance_template is untouched and every stock script that checks the name (GetBlackrockDepthsAI: Rocknot,
    // Nagmara, the braziers, the Ironhand Guardians, at_ring_of_law, Grimstone, Phalanx and the stock bosses until
    // their wave binds) keeps working with no copy.
    char constexpr kInstanceScriptName[] = "instance_blackrock_depths";
    // `.dbtest brd <boss> <mechanic>` (handoff section 3.2 item 5): the kit shell's command name; the chat command map
    // splits it at the space, so it nests under the shared `.dbtest` root (BlackrockDepthsTestCommand.cpp).
    char constexpr kTestCommand[] = "dbtest brd";
    char constexpr kLogDungeon[] = "brd";           // DungeonKit::LogMechanic("brd", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The stock instance had no boss states at all (handoff section 2.2): slots 0-18 follow
    // the DungeonEncounter.dbc bits (227-245, read 2026-11-17: Bit = OrderIndex / 1000 = the id order here), 19 is the
    // Vault (no credit row), 20-23 the four hard mode kills (written by the instance only). Fineous, Ribbly and Plugger
    // keep tracking slots (doors, save, `.dbtest`) although their credit rows go (BD5, section 7 #4).
    // ----------------------------------------------------------------------------------------------------------------
    enum BrdBosses : std::uint32_t
    {
        BOSS_GERSTAHN           = 0,    // D1, wave 1
        BOSS_ROCCOR             = 1,    // D2, wave 1
        BOSS_GREBMAR            = 2,    // D3, wave 1
        BOSS_RING_OF_LAW        = 3,    // D4/D5, wave 1 (the event; mirrors TYPE_RING_OF_LAW)
        BOSS_LOREGRAIN          = 4,    // D7, wave 1
        BOSS_INCENDIUS          = 5,    // D11, wave 1
        BOSS_STILGISS_VEREK     = 6,    // D8, wave 1 (one encounter; DONE once both are dead)
        BOSS_FINEOUS            = 7,    // D10, wave 1 (tracking only: no credit)
        BOSS_BAELGAR            = 8,    // D13, wave 1 (section 2's end)
        BOSS_ANGERFORGE         = 9,    // D14, wave 2
        BOSS_ARGELMACH          = 10,   // D15, wave 2 (section 3's end)
        BOSS_HURLEY             = 11,   // D18, wave 2
        BOSS_PHALANX            = 12,   // D19, wave 2
        BOSS_RIBBLY             = 13,   // D17, wave 2 (tracking only: SmartAI, no credit)
        BOSS_PLUGGER            = 14,   // D17, wave 2 (tracking only: SmartAI, no credit)
        BOSS_FLAMELASH          = 15,   // D20, wave 2
        BOSS_THE_SEVEN          = 16,   // D21, wave 2 (mirrors TYPE_TOMB_OF_SEVEN)
        BOSS_MAGMUS             = 17,   // D22, wave 2 (mirrors TYPE_IRON_HALL)
        BOSS_EMPEROR            = 18,   // D23, wave 2 (section 4's end)
        BOSS_VAULT              = 19,   // D9, wave 1 (mirrors TYPE_VAULT; no credit row)
        BOSS_ENCORE             = 20,   // D6: the Ring won with the banner burned (set by the instance)
        BOSS_LORD_OF_THE_LAKE   = 21,   // D12: Incendius killed with the Cinder used (set by the instance)
        BOSS_PROTOTYPE          = 22,   // D16: Argelmach killed with the console armed (set by the instance)
        BOSS_AVATAR             = 23,   // D24: Dagran killed as the Avatar of Ragnaros (set by the instance)
    };
    std::uint32_t constexpr kBossCount = 24;
    std::uint32_t constexpr kEncounterCount = 19;   // the DungeonEncounter rows 227-245 (bits 0-18)

    static_assert(BOSS_EMPEROR + 1 == kEncounterCount, "slots 0-18 are the DungeonEncounter bits");
    static_assert(BOSS_VAULT == 19 && BOSS_ENCORE == 20 && BOSS_AVATAR == 23, "section 3.2 item 2");
    static_assert(BOSS_AVATAR + 1 == kBossCount, "every boss state has a slot");

    // Names by boss state id (`.dbtest brd state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "High Interrogator Gerstahn", "Lord Roccor", "Houndmaster Grebmar", "Ring of Law", "Pyromancer Loregrain",
        "Lord Incendius", "Warder Stilgiss and Verek", "Fineous Darkvire (no credit)", "Bael'Gar",
        "General Angerforge", "Golem Lord Argelmach", "Hurley Blackbreath", "Phalanx",
        "Ribbly Screwspigot (no credit)", "Plugger Spazzring (no credit)", "Ambassador Flamelash", "The Seven",
        "Magmus", "Emperor Dagran Thaurissan", "The Vault (Watchman Doomgrip)", "The Encore (Ring hard mode)",
        "Lord of the Lake (Incendius hard mode)", "The Prototype (Argelmach hard mode)",
        "The Avatar of Ragnaros (Emperor hard mode)" } };

    // A DungeonEncounter slot (bits 0-18; Fineous, Ribbly and Plugger included: they keep their client row).
    constexpr bool IsEncounterSlot(std::uint32_t bossId)
    {
        return bossId < kEncounterCount;
    }

    // The three mini-bosses whose instance_encounters credit rows go (BD5; WP-H deletes 234, 240, 241).
    constexpr bool IsTrackingOnlySlot(std::uint32_t bossId)
    {
        return bossId == BOSS_FINEOUS || bossId == BOSS_RIBBLY || bossId == BOSS_PLUGGER;
    }

    constexpr bool IsHardModeSlot(std::uint32_t bossId)
    {
        return bossId >= BOSS_ENCORE && bossId <= BOSS_AVATAR;
    }

    // The boss slot a hard mode kill belongs to.
    constexpr std::uint32_t HardModeBoss(std::uint32_t hardModeSlot)
    {
        switch (hardModeSlot)
        {
            case BOSS_ENCORE:           return BOSS_RING_OF_LAW;
            case BOSS_LORD_OF_THE_LAKE: return BOSS_INCENDIUS;
            case BOSS_PROTOTYPE:        return BOSS_ARGELMACH;
            case BOSS_AVATAR:           return BOSS_EMPEROR;
            default:                    return kBossCount;
        }
    }

    // The section of a slot (the Finder sections, handoff section 3.8): 1 Detention Block, 2 Shadowforge City, 3
    // Manufactory, 4 Imperial Seat.
    constexpr std::uint32_t SectionOf(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_GERSTAHN:
            case BOSS_ROCCOR:
            case BOSS_GREBMAR:
            case BOSS_RING_OF_LAW:
            case BOSS_ENCORE:
                return 1;
            case BOSS_LOREGRAIN:
            case BOSS_INCENDIUS:
            case BOSS_STILGISS_VEREK:
            case BOSS_FINEOUS:
            case BOSS_BAELGAR:
            case BOSS_VAULT:
            case BOSS_LORD_OF_THE_LAKE:
                return 2;
            case BOSS_ANGERFORGE:
            case BOSS_ARGELMACH:
            case BOSS_PROTOTYPE:
                return 3;
            default:
                return bossId < kBossCount ? 4 : 0;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Wave switch (handoff section 3.2 item 3, section 7 #23; the user rules both waves are built before one deploy,
    // section 10 #24, but the gate stays so wave 1 can be checked alone). Wave 1 is sections 1 and 2, wave 2 sections 3
    // and 4. Until wave 2 flips it, the section 3-4 bosses keep their stock ScriptName, AIName, SmartAI and health (the
    // DT twin BIND_WAVE_2 in apps/dbc-tools source/npcs/blackrock_depths/_common.py must agree:
    // lib/test_blackrock_depths_kit.py), their stub C++ registers no AI (an unbound registered name logs "not assigned"
    // at boot), and the instance keeps their stock event paths (Argelmach's hall release, the Tomb's 30 s release, the
    // Ironhand Gout timer). Orchestrator WP 0-2 flips both in one commit.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr bool kWave2Bound = true;

    constexpr bool IsWave2Boss(std::uint32_t bossId)
    {
        return (bossId >= BOSS_ANGERFORGE && bossId <= BOSS_EMPEROR) || bossId == BOSS_PROTOTYPE
            || bossId == BOSS_AVATAR;
    }

    // A slot whose state the boss's own script writes (a reworked BossAI, its wave bound). Everything else is written
    // by the instance: the Ring (the event, TYPE_RING_OF_LAW), Stilgiss and Verek (DONE once both are dead), the Vault
    // (TYPE_VAULT), Ribbly and Plugger (SmartAI), the Seven while stock (TYPE_TOMB_OF_SEVEN), the stock wave 2 bosses
    // (their deaths, OnUnitDeath) and the hard mode kills.
    constexpr bool SlotWrittenByScript(std::uint32_t bossId, bool wave2Bound = kWave2Bound)
    {
        switch (bossId)
        {
            case BOSS_RING_OF_LAW:
            case BOSS_STILGISS_VEREK:
            case BOSS_RIBBLY:
            case BOSS_PLUGGER:
            case BOSS_VAULT:
                return false;
            default:
                if (bossId >= kEncounterCount)
                    return false;
                return !IsWave2Boss(bossId) || wave2Bound;
        }
    }

    // A reworked boss whose wave is bound.
    constexpr bool IsReworkBound(std::uint32_t bossId, bool wave2Bound = kWave2Bound)
    {
        if (bossId >= kBossCount || bossId == BOSS_RIBBLY || bossId == BOSS_PLUGGER)
            return false;
        return !IsWave2Boss(bossId) || wave2Bound;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // InstanceScript::SetData / GetData ids. Every stock one keeps its number and meaning (blackrock_depths.h
    // DataTypes at 60bac7405: the stock scripts that stay and mod-dungeon-clear read them); the TYPE_* ones are now
    // mirrors of boss slots where an encounter has one. The new ones start at 50, clear of every stock id.
    // ----------------------------------------------------------------------------------------------------------------
    enum BrdData : std::uint32_t
    {
        // Stock (blackrock_depths.h), kept:
        TYPE_RING_OF_LAW            = 1,    // mirror of BOSS_RING_OF_LAW (DONE 3); at_ring_of_law sets IN_PROGRESS
        TYPE_VAULT                  = 2,    // mirror of BOSS_VAULT
        TYPE_BAR                    = 3,    // the Grim Guzzler bar (no slot): SetData(3, SPECIAL) counts an ale run;
                                            // GetData returns SPECIAL at three while IN_PROGRESS (stock)
        TYPE_TOMB_OF_SEVEN          = 4,    // mirror of BOSS_THE_SEVEN
        TYPE_LYCEUM                 = 5,    // the braziers (no slot): IN_PROGRESS, then DONE opens the Golem Room doors
        TYPE_IRON_HALL              = 6,    // mirror of BOSS_MAGMUS (stock Magmus sets IN_PROGRESS / NOT_STARTED)
        DATA_EMPEROR                = 10,   // GetGuidData: Dagran
        DATA_PHALANX                = 11,   // GetGuidData: Phalanx (Rocknot reads it)
        DATA_ARENA1                 = 12,   // GetGuidData: the Ring's gates (Grimstone opens and closes them)
        DATA_ARENA2                 = 13,
        DATA_ARENA3                 = 14,   // the north gate 161524 (opens when the Ring is DONE)
        DATA_ARENA4                 = 15,
        DATA_GO_BAR_KEG             = 16,   // GetGuidData: Keg Shotgun 170607
        DATA_GO_BAR_KEG_TRAP        = 17,   // GetGuidData: Keg Trap 171941
        DATA_GO_BAR_DOOR            = 18,   // GetGuidData: Bar Door 170571
        DATA_GO_CHALICE             = 19,   // GetGuidData: Spectral Chalice 164869 (Gloom'rel respawns it)
        DATA_GOLEM_DOOR_N           = 22,
        DATA_GOLEM_DOOR_S           = 23,
        DATA_THRONE_DOOR            = 24,
        DATA_SF_BRAZIER_N           = 25,
        DATA_SF_BRAZIER_S           = 26,
        DATA_MOIRA                  = 27,   // GetGuidData: the princess on the dais (Moira, or the High Priestess when
                                            // she replaced Moira: the stock MoiraGUID bug fixed)
        DATA_PRIESTESS              = 28,   // GetGuidData: the High Priestess while she stands in
        DATA_OPEN_COFFER_DOORS      = 30,   // SetData: a Relic Coffer Door opened (the doors' SmartAI). Counted only:
                                            // the Vault no longer starts at 12 (section 7 #17, the trigger moved)
        DATA_GOLEM_LORD_ARGELMACH_INIT = 31,    // stock Argelmach SmartAI: the hall release (wave 1 only; ruling 56
        DATA_GOLEM_LORD_ARGELMACH_ADDS = 32,    // retires it once wave 2 binds D15)
        DATA_MAGMUS                 = 33,   // GetGuidData: Magmus
        DATA_COREN                  = 34,   // GetGuidData: Coren Direbrew (Brewfest)
        DATA_ANUBSHIAH              = 35,   // stock champion BossAI ids (beyond the 24 slots: no-ops, as stock)
        DATA_EVISCERATOR            = 36,
        DATA_GOROSH                 = 37,
        DATA_GRIZZLE                = 38,
        DATA_HEDRUM                 = 39,
        DATA_OKTHOR                 = 40,
        DATA_TIME_RING_FAIL         = 41,   // GetData: the game time of the last Ring FAIL (the AT's 2 min block)
        DATA_ARENA_MOBS             = 42,   // GetData: the Ring's wave type 0-5 (stock RingMobs index; the saved roll)
        DATA_ARENA_BOSS             = 43,   // GetData: the Ring's champion 0-5 (stock RingBoss index; the pair's first)
        DATA_PHALANX_ACTIVATED      = 44,   // Get/SetData: Phalanx walked to the Bar Door (saved)
        DATA_LOVE_POTION_EVENT      = 45,   // Get/SetData: Nagmara's love potion event (DONE opens the Bar Door; saved)

        // New (50 on):
        DATA_RING_SENTENCE          = 50,   // GetData: the saved Sentence roll, 0-2 (D4)
        DATA_RING_WAVE              = 51,   // GetData: the saved wave type roll, 0-5 (= DATA_ARENA_MOBS)
        DATA_RING_FIRST             = 52,   // GetData: the saved first champion, 0-5 (= DATA_ARENA_BOSS)
        DATA_RING_SECOND            = 53,   // GetData: the saved second champion, 0-5, never the first
        DATA_RING_FAVOR             = 54,   // Get/SetData: Crowd Favor 0-10 (D4; per attempt, not saved; starts at 5)
        DATA_BANNER_THROWN          = 55,   // Get/SetData(55, 1): the crowd threw the banner (D4, heroic, the Ring not
                                            // DONE). Saved: it stays for the run
        DATA_BANNER_BURNED          = 56,   // Get/SetData(56, 1): a player burned it (D6; heroic, thrown, the Ring not
                                            // DONE): the Encore is armed. Saved
        DATA_VAULT_TRIGGER          = 57,   // SetData(57, 1): the Dark Coffer 174565 opened (its SmartAI row); starts
                                            // the Vault once Stilgiss and Verek are DONE (section 7 #17)
        DATA_VAULT_CLOCK            = 58,   // Get/SetData: the Vault's finishing time in s (D9 sets it at the end; 0
                                            // until then). Saved; VaultSafe() reads the Safe's contents from it
        DATA_GUZZLER_ROPE           = 59,   // Get/SetData: RopeState (D10: dropped, then placed). Saved
        DATA_CINDER_USED            = 60,   // Get/SetData(60, 1): the Cinder of the Firelord was used (D12; heroic,
                                            // Incendius neither fighting nor dead). Saved until the reset
        DATA_MOIRA_SAVED            = 61,   // GetData: Moira was saved by the Avatar kill (D24). Saved
        DATA_CONSOLE_ARMED          = 62,   // Get/SetData(62, 1): the Activation Console (D16; heroic, wave 2 bound,
                                            // Argelmach not engaged nor dead). Per pull
        DATA_AVATAR                 = 63,   // Get/SetData(63, 1): Ragnaros Awakens started (D24; heroic, wave 2 bound,
                                            // Dagran fighting). Per pull
        DATA_COFFER_DOORS_OPENED    = 64,   // GetData: how many Relic Coffer Doors were opened this load (debug)
        DATA_GM_SLOT_WRITE          = 65,   // SetData(65, 1): the next SetBossState passes the stock-collision guard
                                            // (`.dbtest brd instance boss`)
        DATA_VAULT_RESET            = 66,   // SetData(66, 1): the Vault attempt is over (D9's wipe; also the
                                            // instance's own idle watch): sentinels re-stone, Doomgrip despawns
        DATA_VAULT_DOOMGRIP_ITEM    = 67,   // Get/SetData: the gear item Doomgrip dropped (D9; the Safe never gives
                                            // it). Saved while the Vault is DONE; cleared by a Vault reset
        DATA_ENCORE_WON             = 68,   // SetData(68, 1): the Encore's five are dead (D6, right before the Ring's
                                            // credit). Only then does the Ring's DONE record BOSS_ENCORE
        DATA_ENCORE_RUNNING         = 69,   // Get/SetData(69, 0|1): the Encore is on (Grimstone). A Ring FAIL while
                                            // it is on puts the banner out (section 10: unlit after an Encore wipe)
        DATA_GALLERY_STOOD_DOWN     = 70,   // Get: the Ring gallery stood down for a section 2 start (saved);
                                            // SetData(70, 1) stands it down now (section 10)
        DATA_STILGISS_VEREK_FIGHT   = 71,   // SetData(71, 1|0): D8's pull / reset: slot 6 IN_PROGRESS / NOT_STARTED
                                            // (never DONE: that is both deaths)
        DATA_VAULT_OPENER           = 72,   // SetGuidData(72, player): who opened the Dark Coffer (its SmartAI row,
                                            // SMART_ACTION_SET_INST_DATA64 on the invoker); the Vault's end takes
                                            // that player's Dark Keeper Key (section 10, orchestrator ruling)
    };

    // Stock numbers (blackrock_depths.h at 60bac7405), pinned: stock scripts and mod-dungeon-clear use them raw.
    static_assert(TYPE_RING_OF_LAW == 1 && TYPE_VAULT == 2 && TYPE_BAR == 3 && TYPE_TOMB_OF_SEVEN == 4
        && TYPE_LYCEUM == 5 && TYPE_IRON_HALL == 6, "stock TYPE_* (1-based)");
    static_assert(DATA_EMPEROR == 10 && DATA_PHALANX == 11 && DATA_ARENA1 == 12 && DATA_ARENA4 == 15
        && DATA_GO_BAR_KEG == 16 && DATA_GO_BAR_KEG_TRAP == 17 && DATA_GO_BAR_DOOR == 18 && DATA_GO_CHALICE == 19,
        "stock DATA_EMPEROR..DATA_GO_CHALICE");
    static_assert(DATA_GOLEM_DOOR_N == 22 && DATA_GOLEM_DOOR_S == 23 && DATA_THRONE_DOOR == 24
        && DATA_SF_BRAZIER_N == 25 && DATA_SF_BRAZIER_S == 26 && DATA_MOIRA == 27 && DATA_PRIESTESS == 28,
        "stock DATA_GOLEM_DOOR_N..DATA_PRIESTESS");
    static_assert(DATA_OPEN_COFFER_DOORS == 30 && DATA_GOLEM_LORD_ARGELMACH_INIT == 31
        && DATA_GOLEM_LORD_ARGELMACH_ADDS == 32 && DATA_MAGMUS == 33 && DATA_COREN == 34, "stock 30-34");
    static_assert(DATA_ANUBSHIAH == 35 && DATA_EVISCERATOR == 36 && DATA_GOROSH == 37 && DATA_GRIZZLE == 38
        && DATA_HEDRUM == 39 && DATA_OKTHOR == 40 && DATA_TIME_RING_FAIL == 41 && DATA_ARENA_MOBS == 42
        && DATA_ARENA_BOSS == 43 && DATA_PHALANX_ACTIVATED == 44 && DATA_LOVE_POTION_EVENT == 45,
        "stock auto-numbered 35-45 (computed by enumeration order)");
    static_assert(DATA_RING_SENTENCE > DATA_LOVE_POTION_EVENT, "new data ids clear the stock ones");
    // The stock champion BossAI ids fall beyond the slots (their SetBossState stays a no-op, as stock).
    static_assert(DATA_ANUBSHIAH >= kBossCount && DATA_MOIRA >= kBossCount && DATA_PRIESTESS >= kBossCount,
        "stock BossAI ids that are no slot");

    // The mirror slot of a stock TYPE_* (none for the bar and the Lyceum).
    constexpr std::optional<std::uint32_t> SlotOfType(std::uint32_t type)
    {
        switch (type)
        {
            case TYPE_RING_OF_LAW:      return BOSS_RING_OF_LAW;
            case TYPE_VAULT:            return BOSS_VAULT;
            case TYPE_TOMB_OF_SEVEN:    return BOSS_THE_SEVEN;
            case TYPE_IRON_HALL:        return BOSS_MAGMUS;
            default:                    return std::nullopt;
        }
    }

    // Stock protocols the instance keeps for the scripts that stay (blackrock_depths.cpp / instance file at 60bac7405)
    // and that the reworked scripts must keep accepting.
    enum BrdStockProtocol : std::uint32_t
    {
        ACTION_PHALANX_START_ACTIVATION = 1,    // Rocknot -> Phalanx's AI DoAction (D19 keeps it)
        DATA_EMPEROR_SENATORS_DEAD      = 0,    // instance -> Dagran's AI SetData(0, % of the room's senators dead)
        DATA_IRONHAND_FLAMES            = 0,    // instance -> Ironhand Guardian AI SetData(0, 0|1) (wave 1 only)
        // Dark Iron Ale (the patrons' SmartAI and the instance, stock d05ad7f82)
        DATA_DARK_IRON_ALE              = 1,    // SmartAI data id on the patron
        DATA_DARK_IRON_ALE_DRINK        = 4,
        DATA_DARK_IRON_ALE_HOME         = 100,  // SetGuidData keys from the patrons' SmartAI
        DATA_DARK_IRON_ALE_REFORM       = 101,
        DATA_DARK_IRON_ALE_DISBAND      = 102,
        DATA_DARK_IRON_ALE_EMOTE        = 103,
    };

    std::uint32_t constexpr kAreaTriggerRingOfLaw = 1526;   // [db] at_ring_of_law, sphere r 8 at (596.4, -188.5, -50)

    // ----------------------------------------------------------------------------------------------------------------
    // Factions and quests
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kFactionNeutral = 674;          // stock FACTION_NEUTRAL (spectators after the Ring)
    std::uint32_t constexpr kFactionHostile = 754;          // stock FACTION_HOSTILE
    std::uint32_t constexpr kFactionFriend = 35;            // stock FACTION_FRIEND (Moira standing down)
    std::uint32_t constexpr kFactionDarkIronDwarves = 54;   // the Seven's release (stock FACTION_DARK_IRON_DWARVES)

    std::uint32_t constexpr kQuestPrincessHorde = 4004;     // Moira / Priestess swap (stock)
    std::uint32_t constexpr kQuestPrincessAlliance = 4363;
    std::uint32_t constexpr kQuestTheChallenge = 9015;      // the Encore's credit 16166 (heroic only, section 7 #16)
    std::uint32_t constexpr kQuestDarkIronAle = 4295;       // Rocknot's ale run
    std::uint32_t constexpr kQuestLovePotion = 4201;        // Nagmara's branch
    std::uint32_t constexpr kKillCreditTheldren = 16166;    // KilledMonsterCredit of the Encore

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum BrdCreatures : std::uint32_t
    {
        // encounter bosses (stock entries; script names bound by apps/dbc-tools source/npcs/blackrock_depths/<boss>.py)
        NPC_GERSTAHN                = 9018,     // boss_high_interrogator_gerstahn_rework
        NPC_ROCCOR                  = 9025,     // boss_lord_roccor_rework
        NPC_GREBMAR                 = 9319,     // boss_houndmaster_grebmar_rework
        NPC_GRIMSTONE               = 10096,    // npc_grimstone_rework (D4; summoned per attempt, never ObjectData)
        NPC_GOROSH                  = 9027,     // the six champions (D5; summoned, never ObjectData)
        NPC_GRIZZLE                 = 9028,
        NPC_EVISCERATOR             = 9029,
        NPC_OKTHOR                  = 9030,
        NPC_ANUBSHIAH               = 9031,
        NPC_HEDRUM                  = 9032,
        NPC_THELDREN                = 16059,    // the Encore (D6; summoned)
        NPC_KORV                    = 16053,
        NPC_LEFTY                   = 16049,
        NPC_VOLIDA                  = 16058,
        NPC_MALGEN_LONGSPEAR        = 16052,
        NPC_LOREGRAIN               = 9024,     // boss_pyromancer_loregrain_rework
        NPC_FRANCLORNS_SPIRIT       = 9542,     // D7 summons it at the pull (D10 a short-lived copy at Fineous)
        NPC_STILGISS                = 9041,     // boss_warder_stilgiss_rework
        NPC_VEREK                   = 9042,     // npc_verek_rework
        NPC_DOOMGRIP                = 9476,     // boss_watchman_doomgrip_rework (summoned by the Vault, by hand)
        NPC_WARBRINGER_CONSTRUCT    = 8905,     // the four in the Relic Coffer room are the Vault's (until D9 re-enters
                                                // spawns 46608, 46610, 46611, 46612 to the Vault Sentinel)
        NPC_FINEOUS                 = 9056,     // npc_fineous_darkvire_rework
        NPC_INCENDIUS               = 9017,     // boss_lord_incendius_rework
        NPC_BAELGAR                 = 9016,     // boss_baelgar_rework
        NPC_ANGERFORGE              = 9033,     // boss_general_angerforge_rework (wave 2)
        NPC_ARGELMACH               = 8983,     // boss_golem_lord_argelmach_rework (wave 2)
        NPC_HURLEY                  = 9537,     // boss_hurley_blackbreath_rework (wave 2)
        NPC_BLACKBREATH_CRONY       = 9541,     // npc_blackbreath_crony_rework (wave 2)
        NPC_PHALANX                 = 9502,     // npc_phalanx_rework (wave 2)
        NPC_RIBBLY                  = 9543,     // SmartAI (D17 edits rows)
        NPC_RIBBLYS_CRONY           = 10043,
        NPC_PLUGGER                 = 9499,     // SmartAI (D17 edits rows)
        NPC_FLAMELASH               = 9156,     // boss_ambassador_flamelash_rework (wave 2)
        NPC_BURNING_SPIRIT          = 9178,     // npc_burning_spirit_rework (wave 2; summoned)
        NPC_HATEREL                 = 9034,     // the Seven: boss_the_seven_rework on all seven (wave 2)
        NPC_ANGERREL                = 9035,
        NPC_VILEREL                 = 9036,
        NPC_GLOOMREL                = 9037,
        NPC_SEETHREL                = 9038,
        NPC_DOOMREL                 = 9039,
        NPC_DOPEREL                 = 9040,
        NPC_MAGMUS                  = 9938,     // boss_magmus_rework (wave 2)
        NPC_IRONHAND_GUARDIAN       = 8982,     // npc_ironhand_guardian_rework (wave 2; stock brd_ironhand_guardian)
        NPC_EMPEROR                 = 9019,     // boss_emperor_dagran_thaurissan_rework (wave 2)
        NPC_MOIRA                   = 8929,     // boss_moira_bronzebeard_rework (wave 2; may be summoned by the swap)
        NPC_PRIESTESS               = 10076,    // boss_moira_bronzebeard_rework (wave 2; summoned by the swap)

        // stock units the instance or the kit uses
        NPC_ROCKNOT                 = 9503,     // stock npc_rocknot (kept)
        NPC_NAGMARA                 = 9500,     // stock npc_mistress_nagmara (kept)
        NPC_COREN_DIREBREW          = 23872,
        NPC_ARENA_SPECTATOR         = 8916,
        NPC_SHADOWFORGE_PEASANT     = 8896,
        NPC_SHADOWFORGE_CITIZEN     = 8902,
        NPC_SHADOWFORGE_SENATOR     = 8904,
        NPC_WEAPON_TECHNICIAN       = 8920,     // the Argelmach hall (wave 1 stock release)
        NPC_DOOMFORGE_ARCANASMITH   = 8900,
        NPC_RAGEREAVER_GOLEM        = 8906,
        NPC_WRATH_HAMMER_CONSTRUCT  = 8907,
        NPC_GRIM_PATRON             = 9545,
        NPC_GUZZLING_PATRON         = 9547,
        NPC_HAMMERED_PATRON         = 9554,
        NPC_ANVILRAGE_RESERVIST     = 8901,     // Angerforge's four at his side (D14 kill order)
        NPC_DREDGE_WORM             = 8925,     // the Ring's wave mobs (D4: npc_ring_beast_rework)
        NPC_DEEP_STINGER            = 8926,
        NPC_DARK_SCREECHER          = 8927,
        NPC_THUNDERSNOUT            = 8928,
        NPC_BORER_BEETLE            = 8932,
        NPC_CAVE_CREEPER            = 8933,

        // new boss-kit creatures (ids.yaml reservation `blackrock_depths`, 300780-300879; declared by the boss WPs in
        // apps/dbc-tools source/npcs/blackrock_depths/). Wave 1 300780-300829, wave 2 300830-300879 (the heroic mint
        // order: every wave 1 add below every wave 2 add).
        NPC_BRD_LOOSED_EARTH        = 300780,   // D2
        NPC_BRD_KENNEL_HOUND        = 300781,   // D3
        NPC_BRD_RISEN_WORM          = 300782,   // D5: Risen beasts, one per wave type (stock RingMobs order)
        NPC_BRD_RISEN_STINGER       = 300783,
        NPC_BRD_RISEN_SCREECHER     = 300784,
        NPC_BRD_RISEN_THUNDERSNOUT  = 300785,
        NPC_BRD_RISEN_CREEPER       = 300786,
        NPC_BRD_RISEN_BEETLE        = 300787,
        NPC_BRD_RISEN_CHAMPION      = 300788,   // D5: heroic
        NPC_BRD_KORV_TOTEM_1        = 300789,   // D6: Korv's three totems
        NPC_BRD_KORV_TOTEM_2        = 300790,
        NPC_BRD_KORV_TOTEM_3        = 300791,
        NPC_BRD_DEFILING_TOTEM      = 300792,   // D7
        NPC_BRD_VAULT_SENTINEL      = 300793,   // D9: the four event constructs re-entered
        NPC_BRD_EMBER_OF_INCENDIUS  = 300794,   // D11
        NPC_BRD_LAVA_SPAWN          = 300795,   // D12 (the items' 300655 is another unit)
        NPC_BRD_STALKER             = 300796,   // shared generic stalker, wave 1 (ask the orchestrator)
        NPC_BRD_SQUAD_OFFICER       = 300830,   // D14
        NPC_BRD_SQUAD_RESERVIST     = 300831,
        NPC_BRD_SQUAD_MEDIC         = 300832,
        NPC_BRD_TOXITRON            = 300833,   // D15
        NPC_BRD_ELECTRON            = 300834,
        NPC_BRD_ARCANOTON           = 300835,
        NPC_BRD_MAGMATRON           = 300836,   // D16
        NPC_BRD_ARCANE_ORB          = 300837,   // D15
        NPC_BRD_SALVAGED_CORE       = 300838,   // D16
        NPC_BRD_LAGER_KEG           = 300839,   // D18
        NPC_BRD_LAGER_PUDDLE        = 300840,
        NPC_BRD_ROWDY_PATRON        = 300841,   // D19: heroic
        NPC_BRD_PORTAL_ANCHOR       = 300842,   // D20
        NPC_BRD_IMPERIAL_GUARD      = 300843,   // D23
        NPC_BRD_TWILIGHT_AMBASSADOR = 300844,   // D23: heroic
        NPC_BRD_STALKER_WAVE_2      = 300845,   // shared generic stalker, wave 2
    };

    // The Seven in the stock release order (instance TombBossGUIDs[0..6]: Anger'rel first, Doom'rel last).
    inline std::array<std::uint32_t, 7> constexpr kTheSeven{ { NPC_ANGERREL, NPC_SEETHREL, NPC_DOPEREL, NPC_GLOOMREL,
        NPC_VILEREL, NPC_HATEREL, NPC_DOOMREL } };

    constexpr std::optional<std::uint32_t> SevenIndex(std::uint32_t entry)
    {
        for (std::uint32_t i = 0; i < kTheSeven.size(); ++i)
            if (kTheSeven[i] == entry)
                return i;
        return std::nullopt;
    }

    // The Ring's champions and wave mobs in stock order (blackrock_depths.cpp RingBoss / RingMobs): the saved rolls
    // index these.
    inline std::array<std::uint32_t, 6> constexpr kRingChampions{ { NPC_GOROSH, NPC_GRIZZLE, NPC_EVISCERATOR,
        NPC_OKTHOR, NPC_ANUBSHIAH, NPC_HEDRUM } };
    inline std::array<std::uint32_t, 6> constexpr kRingWaveMobs{ { NPC_DREDGE_WORM, NPC_DEEP_STINGER,
        NPC_DARK_SCREECHER, NPC_THUNDERSNOUT, NPC_CAVE_CREEPER, NPC_BORER_BEETLE } };
    inline std::array<std::uint32_t, 6> constexpr kRingWaveCounts{ { 3, 3, 3, 2, 3, 6 } };     // stock amounts

    // The boss state of a boss entry (a heroic copy's GetEntry() is its base entry); nullopt for anything else. The
    // Ring's units (Grimstone, champions, the Encore) belong to the Ring's event, not to a slot by death.
    constexpr std::optional<std::uint32_t> BossOfEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_GERSTAHN:      return BOSS_GERSTAHN;
            case NPC_ROCCOR:        return BOSS_ROCCOR;
            case NPC_GREBMAR:       return BOSS_GREBMAR;
            case NPC_LOREGRAIN:     return BOSS_LOREGRAIN;
            case NPC_INCENDIUS:     return BOSS_INCENDIUS;
            case NPC_STILGISS:
            case NPC_VEREK:         return BOSS_STILGISS_VEREK;
            case NPC_FINEOUS:       return BOSS_FINEOUS;
            case NPC_BAELGAR:       return BOSS_BAELGAR;
            case NPC_ANGERFORGE:    return BOSS_ANGERFORGE;
            case NPC_ARGELMACH:     return BOSS_ARGELMACH;
            case NPC_HURLEY:        return BOSS_HURLEY;
            case NPC_PHALANX:       return BOSS_PHALANX;
            case NPC_RIBBLY:        return BOSS_RIBBLY;
            case NPC_PLUGGER:       return BOSS_PLUGGER;
            case NPC_FLAMELASH:     return BOSS_FLAMELASH;
            case NPC_HATEREL:
            case NPC_ANGERREL:
            case NPC_VILEREL:
            case NPC_GLOOMREL:
            case NPC_SEETHREL:
            case NPC_DOOMREL:
            case NPC_DOPEREL:       return BOSS_THE_SEVEN;
            case NPC_MAGMUS:        return BOSS_MAGMUS;
            case NPC_EMPEROR:       return BOSS_EMPEROR;
            case NPC_DOOMGRIP:      return BOSS_VAULT;
            default:                return std::nullopt;
        }
    }

    // The entry `.dbtest brd` and the guard look a slot's boss up by (the first of a pair; 0 for the others).
    constexpr std::uint32_t EntryOfBoss(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_GERSTAHN:         return NPC_GERSTAHN;
            case BOSS_ROCCOR:           return NPC_ROCCOR;
            case BOSS_GREBMAR:          return NPC_GREBMAR;
            case BOSS_RING_OF_LAW:      return NPC_GRIMSTONE;
            case BOSS_LOREGRAIN:        return NPC_LOREGRAIN;
            case BOSS_INCENDIUS:
            case BOSS_LORD_OF_THE_LAKE: return NPC_INCENDIUS;
            case BOSS_STILGISS_VEREK:   return NPC_STILGISS;
            case BOSS_FINEOUS:          return NPC_FINEOUS;
            case BOSS_BAELGAR:          return NPC_BAELGAR;
            case BOSS_ANGERFORGE:       return NPC_ANGERFORGE;
            case BOSS_ARGELMACH:
            case BOSS_PROTOTYPE:        return NPC_ARGELMACH;
            case BOSS_HURLEY:           return NPC_HURLEY;
            case BOSS_PHALANX:          return NPC_PHALANX;
            case BOSS_RIBBLY:           return NPC_RIBBLY;
            case BOSS_PLUGGER:          return NPC_PLUGGER;
            case BOSS_FLAMELASH:        return NPC_FLAMELASH;
            case BOSS_THE_SEVEN:        return NPC_DOOMREL;
            case BOSS_MAGMUS:           return NPC_MAGMUS;
            case BOSS_EMPEROR:
            case BOSS_AVATAR:           return NPC_EMPEROR;
            case BOSS_VAULT:            return NPC_DOOMGRIP;
            case BOSS_ENCORE:           return NPC_THELDREN;
            default:                    return 0;
        }
    }

    // Spawned, never summoned twice: these go into the instance's ObjectData under GetGuidData(kGuidBossBase + slot)
    // (cpp-scripts.md, the ObjectData pitfall). Dagran, Phalanx and Magmus are ObjectData under their stock keys
    // (DATA_EMPEROR, DATA_PHALANX, DATA_MAGMUS). Grimstone, the champions, the Encore, Doomgrip, Moira and the
    // Priestess (the swap summons either), Verek, the Seven, Coren and every add are tracked by hand.
    constexpr bool IsObjectDataBoss(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_GERSTAHN:
            case NPC_ROCCOR:
            case NPC_GREBMAR:
            case NPC_LOREGRAIN:
            case NPC_INCENDIUS:
            case NPC_STILGISS:
            case NPC_FINEOUS:
            case NPC_BAELGAR:
            case NPC_ANGERFORGE:
            case NPC_ARGELMACH:
            case NPC_HURLEY:
            case NPC_RIBBLY:
            case NPC_PLUGGER:
            case NPC_FLAMELASH:
                return true;
            default:
                return false;
        }
    }

    // GetGuidData keys of the boss units (a namespace apart from the stock keys 10-34, which overlap the slot ids:
    // GetGuidData(10) is still Dagran, as stock).
    std::uint32_t constexpr kGuidBossBase = 200;
    std::uint32_t constexpr kGuidVerek = 230;           // GetGuidData: Verek (by hand)
    std::uint32_t constexpr kGuidDoomgrip = 231;        // GetGuidData: Watchman Doomgrip (summoned, by hand)
    std::uint32_t constexpr kGuidGrimstone = 232;       // GetGuidData: the summoned Grimstone (by hand)

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum BrdGameObjects : std::uint32_t
    {
        // stock (instance_blackrock_depths.cpp GameObjects); the stock GetGuidData keys are the DATA_* ids above, the
        // others are their entries (GetGuidData(<entry>))
        GO_ARENA1                   = 161525,   // [db] (607.7, -229.7) DATA_ARENA1
        GO_ARENA2                   = 161522,   // [db] (637.6, -177.8) DATA_ARENA2
        GO_ARENA3                   = 161524,   // [db] (585.7, -147.8) DATA_ARENA3: the north gate
        GO_ARENA4                   = 161523,   // [db] (555.8, -199.7) DATA_ARENA4: spawns open
        GO_SHADOW_LOCK              = 161460,   // [db] (615.6, -49.8, -60.1): the Shadowforge Lock lever (SmartAI)
        GO_SHADOW_MECHANISM         = 161461,
        GO_SHADOW_GIANT_DOOR        = 157923,   // [db] (723.1, -105.9, -71.5)
        GO_SHADOW_DUMMY             = 161516,   // [db] (702.1, -125.7, -45.7): the bridge choke (section 3.8)
        GO_BAR_KEG_SHOT             = 170607,
        GO_BAR_KEG_TRAP             = 171941,
        GO_BAR_DOOR                 = 170571,   // [db] (870.7, -228.9, -43.8)
        GO_TOMB_ENTER               = 170576,   // [db] (1230.3, -205.2, -85.7)
        GO_TOMB_EXIT                = 170577,   // [db] (1262.8, -293.8, -78.2)
        GO_LYCEUM                   = 170558,   // [db] (1311.5, -343.1, -92.0)
        GO_SF_BRAZIER_N             = 174745,
        GO_SF_BRAZIER_S             = 174744,
        GO_GOLEM_ROOM_N             = 170573,
        GO_GOLEM_ROOM_S             = 170574,
        GO_THRONE_ROOM              = 170575,   // [db] (1380.1, -710.5, -92.0)
        GO_SPECTRAL_CHALICE         = 164869,
        GO_CHEST_SEVEN              = 169243,
        GO_SECRET_DOOR              = 174553,   // [db] (804.2, -356.1, -49.0): opens when the Vault is DONE
        GO_SECRET_SAFE              = 161495,   // [db] (803.5, -357.4, -48.9): selectable when the Vault is DONE
        GO_DARK_IRON_ALE_MUG        = 165578,
        GO_DARK_COFFER_DOOR         = 174565,   // [db] (804.3, -356.1, -49.4): the Vault's trigger (section 7 #17)
        GO_DARK_COFFER              = 160845,   // [db] (803.9, -356.4, -47.5)
        GO_RELIC_COFFER_DOOR_FIRST  = 174554,   // 174554-174564 and 174566: the twelve Relic Coffer Doors
        GO_RELIC_COFFER_DOOR_LAST   = 174566,
        GO_BLACK_ANVIL              = 172911,   // [db] (895.1, -273.6, -71.9)
        GO_BANNER_OF_PROVOCATION    = 181058,   // template only (D6 checks its click; else 301280)
        GO_ARENA_SPOILS             = 181074,   // template only (Grimstone summons it after the Encore)
        GO_THUNDERBREW_LAGER_KEG    = 164911,   // [db] guids 265712-265714 (mod-dungeon-clear reads them)

        // new (ids.yaml reservation `blackrock_depths`, 301280-301309; templates and spawns in the boss WPs' SQL revs)
        GO_BRD_ENCORE_BANNER        = 301280,   // D6 (only if 181058 cannot be clicked)
        GO_BRD_FALLEN_BOULDER       = 301281,   // D13 (GODI 3711)
        GO_BRD_HANGING_ROPE         = 301282,   // D10 (the rope's climb)
        GO_BRD_SHODDY_PILLAR        = 301283,   // D10
        GO_BRD_ACTIVATION_CONSOLE   = 301284,   // D16 (display 6424)
        GO_BRD_PEDESTAL_1           = 301285,   // D15 / D16 (the fourth is the hard mode's)
        GO_BRD_PEDESTAL_2           = 301286,
        GO_BRD_PEDESTAL_3           = 301287,
        GO_BRD_PEDESTAL_4           = 301288,
        GO_BRD_MOLE_MACHINE         = 301289,   // D14 (display 7510 at 0.6)
    };

    constexpr bool IsRelicCofferDoor(std::uint32_t entry)
    {
        return (entry >= GO_RELIC_COFFER_DOOR_FIRST && entry <= 174564) || entry == GO_RELIC_COFFER_DOOR_LAST;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Items (ids.yaml reservation `blackrock_depths`, 70620-70629; declared by WP-IT) and the stock keys
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kItemVaultTreasureBag = 70620;
    std::uint32_t constexpr kItemVaultTreasureBagHeroic = 70623;        // two rare cuts (heroic Safe)
    std::uint32_t constexpr kItemCinderOfTheFirelord = 70621;
    std::uint32_t constexpr kItemGuzzlerRope = 70622;
    std::uint32_t constexpr kItemRelicCofferKey = 11078;
    std::uint32_t constexpr kItemDarkKeeperKey = 11197;
    std::uint32_t constexpr kItemBannerOfProvocation = 21986;   // the stock banner path, ignored (section 7 #16)

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 210700-211999, ids.yaml reservation `blackrock_depths`; declared in apps/dbc-tools
    // source/npcs/blackrock_depths/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h. The
    // kit-wide 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h).
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 210700, 211999 };
    IdSlice constexpr kSpellsShared{ 210700, 210719 };              // kit cast bars, markers
    IdSlice constexpr kSpellsGerstahn{ 210720, 210749 };            // D1  (GE)
    IdSlice constexpr kSpellsRoccor{ 210750, 210779 };              // D2  (RO)
    IdSlice constexpr kSpellsGrebmar{ 210780, 210809 };             // D3  (GR)
    IdSlice constexpr kSpellsRingOfLaw{ 210810, 210869 };           // D4  (RL, RW: the frame and the waves)
    IdSlice constexpr kSpellsRingChampions{ 210870, 210959 };       // D5  (GO, GZ, EV, OK, AN, HE, CH)
    IdSlice constexpr kSpellsEncore{ 210960, 211019 };              // D6  (EN)
    IdSlice constexpr kSpellsLoregrain{ 211020, 211049 };           // D7  (LG)
    IdSlice constexpr kSpellsStilgissVerek{ 211050, 211089 };       // D8  (SV)
    IdSlice constexpr kSpellsVault{ 211090, 211119 };               // D9  (VA)
    IdSlice constexpr kSpellsFineous{ 211120, 211139 };             // D10 (FD and the rope)
    IdSlice constexpr kSpellsIncendius{ 211140, 211179 };           // D11 (IN)
    IdSlice constexpr kSpellsLordOfTheLake{ 211180, 211229 };       // D12 (IN hard mode)
    IdSlice constexpr kSpellsBaelgar{ 211230, 211259 };             // D13 (BG)
    IdSlice constexpr kSpellsEventItems{ 211260, 211269 };          // IT  (Cinder use, rope use, bag)
    IdSlice constexpr kSpellsSpareWave1{ 211270, 211299 };
    IdSlice constexpr kSpellsAngerforge{ 211300, 211329 };          // D14 (AF)
    IdSlice constexpr kSpellsArgelmach{ 211330, 211369 };           // D15 (AR)
    IdSlice constexpr kSpellsPrototype{ 211370, 211409 };           // D16 (AR hard mode)
    IdSlice constexpr kSpellsGuzzler{ 211410, 211429 };             // D17 (Gouge and Kick copies; DD swaps the patrons'
                                                                    // Shadow Bolt on heroic)
    IdSlice constexpr kSpellsHurley{ 211430, 211459 };              // D18 (HU)
    IdSlice constexpr kSpellsPhalanx{ 211460, 211489 };             // D19 (PH)
    IdSlice constexpr kSpellsFlamelash{ 211490, 211519 };           // D20 (FL)
    IdSlice constexpr kSpellsTheSeven{ 211520, 211579 };            // D21 (TS)
    IdSlice constexpr kSpellsMagmus{ 211580, 211609 };              // D22 (MG)
    IdSlice constexpr kSpellsEmperor{ 211610, 211659 };             // D23 (EM)
    IdSlice constexpr kSpellsAvatar{ 211660, 211709 };              // D24 (EM hard mode)
    IdSlice constexpr kSpellsSpare{ 211710, 211999 };

    // Warder Stilgiss and Verek's encounter credit (D8 Q1, F-1a): instance_encounters 233 is a spell credit
    // (creditType 1) on this id, sent by the instance once both are dead (Map::UpdateEncounterState; never cast).
    std::uint32_t constexpr kSpellStilgissVerekCredit = 211066;
    static_assert(kSpellsStilgissVerek.Contains(kSpellStilgissVerekCredit), "D8's slice");

    // The Vault Sentinels' dormant look (R-2-A MA-2): D9's copy of Stoned 10255 (NO_IMMUNITIES, no mechanic; the stock
    // aura's FREEZE mechanic is dropped by the sentinel's immunity set 1972). The instance's freeze casts it on 300793.
    std::uint32_t constexpr kSpellVaultStoned = 211103;
    static_assert(kSpellsVault.Contains(kSpellVaultStoned), "D9's slice");

    inline std::array<IdSlice, 28> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsGerstahn, kSpellsRoccor, kSpellsGrebmar, kSpellsRingOfLaw, kSpellsRingChampions,
        kSpellsEncore, kSpellsLoregrain, kSpellsStilgissVerek, kSpellsVault, kSpellsFineous, kSpellsIncendius,
        kSpellsLordOfTheLake, kSpellsBaelgar, kSpellsEventItems, kSpellsSpareWave1, kSpellsAngerforge,
        kSpellsArgelmach, kSpellsPrototype, kSpellsGuzzler, kSpellsHurley, kSpellsPhalanx, kSpellsFlamelash,
        kSpellsTheSeven, kSpellsMagmus, kSpellsEmperor, kSpellsAvatar, kSpellsSpare } };

    IdSlice constexpr kCreaturesReservation{ 300780, 300879 };
    IdSlice constexpr kCreaturesWave1{ 300780, 300829 };
    IdSlice constexpr kCreaturesWave2{ 300830, 300879 };
    IdSlice constexpr kGameObjectsReservation{ 301280, 301309 };
    IdSlice constexpr kItemsReservation{ 70620, 70629 };

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text groups per boss, the section docs' text tables). A boss WP names its groups in its own Logic
    // header (enum <Boss>Texts : std::uint8_t { SAY_..., EMOTE_... }) inside its range; groups below `firstNew` are
    // stock rows (kept, sometimes moved to a new moment). The boss WP's SQL rev writes the new rows. A hard mode WP
    // (D6, D12, D16, D24) uses its boss's range.
    // ----------------------------------------------------------------------------------------------------------------
    struct TextRange
    {
        std::uint32_t entry;
        std::uint8_t first;
        std::uint8_t last;
        std::uint8_t firstNew;      // groups first..firstNew-1 are stock rows
    };

    inline std::array<TextRange, 31> constexpr kTextRanges{ {
        { NPC_GERSTAHN, 0, 4, 0 },              // D1
        { NPC_ROCCOR, 0, 3, 0 },                // D2
        { NPC_GREBMAR, 0, 6, 0 },               // D3
        { NPC_GRIMSTONE, 0, 14, 6 },            // D4: 0-5 stock (3 "Good riddance!" moved to the end), 11 the banner
        { NPC_GRIZZLE, 0, 0, 1 },               // D5: 0 stock
        { NPC_THELDREN, 0, 1, 1 },              // D6: 0 stock (the leap)
        { NPC_LOREGRAIN, 0, 4, 0 },             // D7
        { NPC_FRANCLORNS_SPIRIT, 0, 1, 0 },     // D7 (0) and D10's copy (1)
        { NPC_STILGISS, 0, 6, 0 },              // D8
        { NPC_VEREK, 0, 0, 1 },                 // D8: 0 stock
        { NPC_DOOMGRIP, 0, 5, 1 },              // D9: 0 stock
        { NPC_FINEOUS, 0, 0, 0 },               // D10
        { NPC_INCENDIUS, 0, 9, 1 },             // D11 0-7 (0 stock, the shatter yell); D12 8-9
        { NPC_BAELGAR, 0, 3, 0 },               // D13 (3 the Falling Boulder line, gap 38)
        { NPC_ANGERFORGE, 0, 3, 0 },            // D14
        { NPC_ARGELMACH, 0, 7, 1 },             // D15 (0 stock moved); 4 the console (D16)
        { NPC_HURLEY, 0, 5, 2 },                // D18: 0-1 stock
        { NPC_PHALANX, 0, 4, 1 },               // D19: 0 stock
        { NPC_FLAMELASH, 0, 3, 1 },             // D20: 0 stock
        { NPC_ANGERREL, 0, 1, 0 },              // D21: a rise and a mood line per ghost (section 8 #24)
        { NPC_SEETHREL, 0, 1, 0 },
        { NPC_DOPEREL, 0, 1, 0 },
        { NPC_GLOOMREL, 0, 1, 0 },
        { NPC_VILEREL, 0, 1, 0 },
        { NPC_HATEREL, 0, 1, 0 },
        { NPC_DOOMREL, 0, 2, 1 },               // D21: 0 stock
        { NPC_MAGMUS, 0, 3, 1 },                // D22: 0 stock (the braziers yell, sent by the instance)
        { NPC_EMPEROR, 0, 13, 8 },              // D23 0-10, 13 (0-7 stock); D24 says 11-12
        { NPC_MOIRA, 0, 1, 1 },                 // D23: 0 stock (the stand-down)
        { NPC_PRIESTESS, 0, 1, 1 },             // D23: 0 stock (her aggro yell), 1 the Nemesis emote
        { NPC_PLUGGER, 0, 3, 4 },               // D17: 0-3 stock, kept (Ribbly's one stock line too)
    } };

    // Stock text groups the instance itself says.
    std::uint8_t constexpr kSayMagmusBraziersLit = 0;

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

    // Boss spawns [db] (Grimstone, the champions, the Encore, Doomgrip and the Priestess have none: summoned).
    Point3 constexpr kGerstahnSpawn{ 310.6f, -146.3f, -70.3f };
    Point3 constexpr kRoccorSpawn{ 615.5f, -267.4f, -83.6f };          // patrol 473040 (D2 replaces it)
    Point3 constexpr kGrebmarSpawn{ 607.7f, -174.8f, -84.5f };
    Point3 constexpr kLoregrainSpawn{ 530.2f, -243.9f, -43.0f };
    Point3 constexpr kStilgissSpawn{ 823.4f, -342.3f, -50.1f };
    Point3 constexpr kVerekSpawn{ 821.7f, -340.4f, -50.1f };
    Point3 constexpr kFineousSpawn{ 963.3f, -343.7f, -71.7f };         // patrol 476310 (kept)
    Point3 constexpr kIncendiusSpawn{ 893.5f, -267.1f, -71.9f };       // patrol 477330 (kept out of combat)
    Point3 constexpr kBaelgarSpawn{ 702.4f, 184.5f, -72.0f };
    Point3 constexpr kAngerforgeSpawn{ 652.4f, 21.4f, -60.0f };
    Point3 constexpr kArgelmachSpawn{ 846.8f, 16.3f, -53.6f };
    Point3 constexpr kHurleySpawn{ 878.1f, -153.1f, -49.8f };          // guid 72000
    Point3 constexpr kRibblySpawn{ 878.5f, -167.7f, -49.7f };
    Point3 constexpr kPluggerSpawn{ 888.5f, -177.9f, -43.0f };
    Point3 constexpr kPhalanxSpawn{ 847.8f, -230.1f, -43.6f };
    Point3 constexpr kFlamelashSpawn{ 1009.8f, -239.0f, -61.3f };
    Point3 constexpr kAngerrelSpawn{ 1215.1f, -220.7f, -85.6f };
    Point3 constexpr kDoomrelSpawn{ 1281.1f, -282.2f, -78.1f };
    Point3 constexpr kMagmusSpawn{ 1380.7f, -659.3f, -91.9f };
    Point3 constexpr kEmperorSpawn{ 1380.2f, -831.6f, -87.6f };
    Point3 constexpr kMoiraSpawn{ 1384.6f, -831.5f, -87.6f };

    // The stock summon spots [db: the stock instance and blackrock_depths.cpp].
    Point4 constexpr kGrimstoneSummon{ 625.559f, -205.618f, -52.735f, 2.609f };
    Point4 constexpr kRingChampionSummon{ 644.3f, -175.989f, -53.739f, 3.418f };
    Point3 constexpr kRingWaveSummon{ 608.96f, -235.322f, -53.907f };
    Point4 constexpr kDoomgripSummon{ 821.905f, -338.382f, -50.134f, 3.78736f };     // the room entrance (cmangos)

    // The Ring of Law [db: the stock instance's CenterOfRingOfLaw; z NM].
    Point3 constexpr kRingCenter{ 595.289f, -186.56f, -54.0f };
    float constexpr kRingSpectatorRadius = 80.f;            // stock RADIUS_RING_OF_LAW (peasants and citizens)
    Point3 constexpr kRingAreaTrigger{ 596.432f, -188.498f, -50.0f };  // [db] AT 1526
    float constexpr kRingAreaTriggerRadius = 8.f;

    // The Black Vault [db: the stock instance's VaultWarderCenter].
    Vec2 constexpr kVaultCenter{ 813.5f, -348.0f };
    float constexpr kVaultWarderRadius = 15.f;              // stock DISTANCE_VAULT_WARDER
    inline std::array<Point3, 4> constexpr kVaultSentinelPosts{ {
        { 813.6f, -341.8f, -50.5f }, { 819.5f, -349.0f, -50.5f }, { 813.6f, -353.7f, -50.5f },
        { 808.0f, -345.9f, -50.5f } } };                    // [db] the four construct spots

    // Lord Incendius's causeway (section 3.8, NM 2.5): the axis through his spawn toward Fineous, the Anvil bulge's
    // tips, the giant's spot (section 7 #14 A), the rope (D10).
    Vec2 constexpr kIncendiusAxis{ 0.672f, -0.740f };       // unit-ish (0.9996): s along it from kIncendiusSpawn
    Point3 constexpr kIncendiusTipWest{ 888.1f, -261.2f, -71.9f };     // s -8
    Point3 constexpr kIncendiusTipEast{ 904.9f, -279.7f, -71.9f };     // s +17
    Point3 constexpr kLakeLordSpot{ 876.8f, -290.3f, -72.0f };          // south-east, hovering near causeway height
    Point3 constexpr kRopeClimbSpot{ 893.5f, -267.1f, -71.9f };         // the rope's use spot behind Incendius
    Point3 constexpr kRopeTop{ 878.5f, -222.5f, -49.8f };               // past the Bar Door (22 yd up, 47 yd across)

    // Bael'Gar: the fight spot the tank pulls him to (NM 2.6).
    Point3 constexpr kBaelgarFightSpot{ 689.8f, 162.8f, -72.4f };

    // The Emperor's room: senators counted within 125 yd of here (stock EmperorSpawnPos, DISTANCE_EMPEROR_ROOM).
    Vec2 constexpr kEmperorRoomCenter{ 1380.52f, -831.0f };
    float constexpr kEmperorRoomRadius = 125.f;

    // The Argelmach hall adds the stock release wakes (wave 1 only): alive, z between these.
    float constexpr kArgelmachHallZMin = -55.f;
    float constexpr kArgelmachHallZMax = -51.5f;
    float constexpr kArgelmachNearRange = 10.f;             // Ragereavers within this of him wake at the pull
    float constexpr kDarkIronAleRange = 20.f;               // stock DISTANCE_DARK_IRON_ALE

    // ----------------------------------------------------------------------------------------------------------------
    // The Finder sections (handoff section 3.8, section 7 #3 / #12): the LFG ids, the start points (the
    // lfg_dungeon_template rows WP-H / FD write and the checkpoint rows), the end slot whose kill completes the section
    // (lastEncounterDungeon), and the doors a teleported group meets on its path.
    // ----------------------------------------------------------------------------------------------------------------
    struct FinderSection
    {
        std::uint32_t number;           // 1-4
        char const* name;
        std::uint32_t lfgNormal;
        std::uint32_t lfgHeroic;
        Point4 start;
        std::uint32_t endSlot;
        std::array<std::uint32_t, 7> doors;     // GO entries on the path (0 = none)
    };

    inline std::array<FinderSection, 4> constexpr kSections{ {
        { 1, "Detention Block", 30, 310, { 458.32f, 26.52f, -70.67f, 4.95f }, BOSS_RING_OF_LAW,
            { { GO_ARENA4, GO_ARENA3, 0, 0, 0, 0, 0 } } },
        { 2, "Shadowforge City", 308, 311, { 595.0f, -92.0f, -45.0f, 1.89f }, BOSS_BAELGAR,
            { { 0, 0, 0, 0, 0, 0, 0 } } },
        { 3, "Manufactory", 309, 312, { 607.2f, -47.8f, -59.8f, 6.05f }, BOSS_ARGELMACH,
            { { GO_SHADOW_LOCK, GO_SHADOW_DUMMY, GO_SHADOW_GIANT_DOOR, 0, 0, 0, 0 } } },
        { 4, "Imperial Seat", 276, 313, { 843.8f, -167.8f, -49.7f, 4.64f }, BOSS_EMPEROR,
            { { GO_BAR_DOOR, GO_TOMB_ENTER, GO_TOMB_EXIT, GO_LYCEUM, GO_GOLEM_ROOM_N, GO_GOLEM_ROOM_S,
                GO_THRONE_ROOM } } },
    } };

    constexpr FinderSection const* SectionByNumber(std::uint32_t number)
    {
        for (FinderSection const& s : kSections)
            if (s.number == number)
                return &s;
        return nullptr;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Completed-encounter bits (DungeonEncounter.dbc 227-245, verified 2026-11-17 against
    // var/extractors/dbc/DungeonEncounter.dbc: Bit 0-18 in id order; mod-dungeon-clear keys its kills on them): bit ->
    // boss state. Used to fill the boss states of a stock save (stock never wrote any).
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<std::pair<std::uint32_t, std::uint32_t>, kEncounterCount> constexpr kEncounterBits{ {
        { 0, BOSS_GERSTAHN }, { 1, BOSS_ROCCOR }, { 2, BOSS_GREBMAR }, { 3, BOSS_RING_OF_LAW },
        { 4, BOSS_LOREGRAIN }, { 5, BOSS_INCENDIUS }, { 6, BOSS_STILGISS_VEREK }, { 7, BOSS_FINEOUS },
        { 8, BOSS_BAELGAR }, { 9, BOSS_ANGERFORGE }, { 10, BOSS_ARGELMACH }, { 11, BOSS_HURLEY },
        { 12, BOSS_PHALANX }, { 13, BOSS_RIBBLY }, { 14, BOSS_PLUGGER }, { 15, BOSS_FLAMELASH },
        { 16, BOSS_THE_SEVEN }, { 17, BOSS_MAGMUS }, { 18, BOSS_EMPEROR } } };
    std::uint32_t constexpr kDungeonEncounterFirstId = 227;     // 227 + bit = the stock DungeonEncounter id

    // ----------------------------------------------------------------------------------------------------------------
    // The stock BossAI collisions (handoff section 3.2 left them unnamed; S0 finding). Three stock boss scripts write a
    // BossAI id that is now a wave 1 slot: boss_ambassador_flamelash BossAI(0) = Gerstahn's, boss_magmus
    // BossAI(TYPE_IRON_HALL = 6) = Stilgiss and Verek's, boss_emperor_dagran_thaurissan BossAI(DATA_EMPEROR = 10) =
    // Argelmach's. While wave 2 is unbound those stock scripts run; the instance only lets a write on these three slots
    // through when it fits the slot's own bosses (DONE: all of them dead; IN_PROGRESS: one of them fighting;
    // NOT_STARTED: none fighting and the slot not DONE). Once wave 2 binds, the stock scripts are unbound and the guard
    // is off.
    // ----------------------------------------------------------------------------------------------------------------
    constexpr bool IsStockCollisionSlot(std::uint32_t bossId)
    {
        return bossId == BOSS_GERSTAHN || bossId == BOSS_STILGISS_VEREK || bossId == BOSS_ARGELMACH;
    }

    // The slot's own units, as the instance found them on the map.
    struct SlotOwners
    {
        bool anyFound = false;
        bool allDead = false;       // every found one is dead (or dying)
        bool anyInCombat = false;
    };

    constexpr bool SlotWriteAccepted(std::uint32_t bossId, std::uint32_t state, std::uint32_t current,
        SlotOwners const& owners, bool wave2Bound = kWave2Bound)
    {
        if (wave2Bound || !IsStockCollisionSlot(bossId))
            return true;
        switch (state)
        {
            case DungeonKit::State::Done:
                return owners.anyFound && owners.allDead;
            case DungeonKit::State::NotStarted:
                return current != DungeonKit::State::Done && !owners.anyInCombat;
            default:
                return owners.anyInCombat;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Ring of Law's saved rolls (section 7 #16, S1 613 / 633: once per instance, saved; stock re-rolled per load).
    // Sentence 1 of 3, wave type 1 of 6, an ordered champion pair 1 of 30. Stored 1-based (0 = not rolled yet).
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kRingSentences = 3;
    std::uint32_t constexpr kRingWaveTypes = 6;
    std::uint32_t constexpr kRingChampionCount = 6;

    struct RingRolls
    {
        std::uint32_t sentence = 0;     // 1..3
        std::uint32_t wave = 0;         // 1..6 (stock RingMobs index + 1)
        std::uint32_t first = 0;        // 1..6 (stock RingBoss index + 1)
        std::uint32_t second = 0;       // 1..6, never `first`

        constexpr bool Rolled() const { return sentence && wave && first && second; }
    };

    // The rolls from four random numbers (urand(0, 0xFFFF) each); every one of the 30 ordered pairs is reachable.
    constexpr RingRolls RollRing(std::uint32_t r1, std::uint32_t r2, std::uint32_t r3, std::uint32_t r4)
    {
        RingRolls r;
        r.sentence = r1 % kRingSentences + 1;
        r.wave = r2 % kRingWaveTypes + 1;
        std::uint32_t const first = r3 % kRingChampionCount;
        r.first = first + 1;
        r.second = (first + 1 + r4 % (kRingChampionCount - 1)) % kRingChampionCount + 1;
        return r;
    }

    // A loaded roll set that is not whole and valid is rolled again (all four together).
    constexpr RingRolls SanitizeRingRolls(RingRolls r)
    {
        bool const valid = r.sentence >= 1 && r.sentence <= kRingSentences && r.wave >= 1 && r.wave <= kRingWaveTypes
            && r.first >= 1 && r.first <= kRingChampionCount && r.second >= 1 && r.second <= kRingChampionCount
            && r.first != r.second;
        return valid ? r : RingRolls{};
    }

    std::uint32_t constexpr kRingFavorStart = 5;
    std::uint32_t constexpr kRingFavorMax = 10;

    // ----------------------------------------------------------------------------------------------------------------
    // The Vault (D9; section 3.7, section 7 #17). The Dark Coffer starts it once Stilgiss and Verek are DONE; a wipe
    // resets it (sentinels re-stone, Doomgrip despawns) and the opened Dark Coffer's gossip starts it again. The
    // instance also ends an attempt nobody fights: kVaultIdleMs with no warder in combat after kVaultGraceMs.
    // ----------------------------------------------------------------------------------------------------------------
    constexpr bool VaultTriggerAccepted(std::uint32_t vaultState, std::uint32_t stilgissState)
    {
        return vaultState == DungeonKit::State::NotStarted && stilgissState == DungeonKit::State::Done;
    }

    std::uint32_t constexpr kVaultGraceMs = 15000;
    std::uint32_t constexpr kVaultIdleMs = 10000;
    std::uint32_t constexpr kVaultWatchMs = 1000;

    constexpr bool VaultAttemptLost(std::uint32_t sinceStartMs, std::uint32_t idleMs, bool anyWarderAlive)
    {
        return anyWarderAlive && sinceStartMs >= kVaultGraceMs && idleMs >= kVaultIdleMs;
    }

    // The idle watch's verdict each second of an attempt (R-1-KIT B1 / R-1-B B1): every warder dead finishes the Vault
    // even when no death reached OnVaultWarderDeath (the fallback); else an idle attempt is lost.
    enum class VaultWatchVerdict : std::uint8_t
    {
        Continue,
        Done,
        Lost,
    };

    constexpr VaultWatchVerdict VaultWatchFor(std::uint32_t sinceStartMs, std::uint32_t idleMs, bool anyWarderAlive)
    {
        if (!anyWarderAlive)
            return VaultWatchVerdict::Done;
        return VaultAttemptLost(sinceStartMs, idleMs, anyWarderAlive) ? VaultWatchVerdict::Lost
            : VaultWatchVerdict::Continue;
    }

    // A death that counts for the Vault (by entry and by the instance's list, never by where it died: a sentinel
    // gripped, feared or knocked out of the 15 yd circle still counts). The Vault Sentinel 300793 is the event's own
    // entry; a Warbringer Construct 8905 counts only when it is one of the four the instance listed at create.
    constexpr bool CountsAsVaultWarder(std::uint32_t entry, bool listed)
    {
        return entry == NPC_DOOMGRIP || entry == NPC_BRD_VAULT_SENTINEL || listed;
    }

    // A construct of the Vault at create: every Vault Sentinel (D9 re-entered the four), or an 8905 inside the room.
    constexpr bool IsVaultConstructAt(std::uint32_t entry, float distanceFromCenter)
    {
        return entry == NPC_BRD_VAULT_SENTINEL
            || (entry == NPC_WARBRINGER_CONSTRUCT && distanceFromCenter <= kVaultWarderRadius);
    }

    // The Dark Coffer 174565 can be opened only once Stilgiss and Verek are DONE (section 10: the key is never spent
    // on a refused trigger): the instance keeps it unselectable until then.
    float constexpr kDarkCofferReachYd = 10.f;      // a player this close when the coffer fires: its opener (fallback)

    constexpr bool DarkCofferSelectable(std::uint32_t stilgissState)
    {
        return stilgissState == DungeonKit::State::Done;
    }

    // The loot clock (section 3.7): a bag seals at 75 s, the gear at 90 s, the last bag at 110 s. D9 owns the tuning;
    // the instance stores the finishing time (DATA_VAULT_CLOCK, s) and this reads the Safe's contents from it.
    std::uint32_t constexpr kVaultSealFirstBagS = 75;
    std::uint32_t constexpr kVaultSealGearS = 90;
    std::uint32_t constexpr kVaultSealLastBagS = 110;

    struct VaultSafe
    {
        bool cinder = false;        // the Cinder of the Firelord, always (never sealed)
        bool gear = false;          // one gear item, never Doomgrip's
        std::uint32_t bags = 0;     // Vault Treasure Bags
    };

    constexpr VaultSafe VaultSafeFor(std::uint32_t finishedS)
    {
        VaultSafe s;
        if (!finishedS)
            return s;
        s.cinder = true;
        s.gear = finishedS < kVaultSealGearS;
        s.bags = (finishedS < kVaultSealFirstBagS ? 1u : 0u) + (finishedS < kVaultSealLastBagS ? 1u : 0u);
        return s;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Guzzler rope (D10; section 3.7): one per instance; dropped by Fineous, placed at kRopeClimbSpot (the hanging
    // rope GO stays for the rest of the instance, respawned on load).
    // ----------------------------------------------------------------------------------------------------------------
    enum RopeState : std::uint32_t
    {
        ROPE_NONE       = 0,
        ROPE_DROPPED    = 1,    // Fineous dropped it (never again this instance)
        ROPE_PLACED     = 2,    // the hanging rope is up
    };

    constexpr bool RopeChangeAllowed(std::uint32_t current, std::uint32_t next)
    {
        return next > current && next <= ROPE_PLACED;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Grim Guzzler's Bar Door 170571 (stock + section 3.2 item 3): the love potion or Phalanx's death opens it
    // (ACTIVE); the ale run's end (TYPE_BAR DONE) blasts it (ACTIVE_ALTERNATIVE). Phalanx's death opens a blasted
    // door fully too (D17 / D19's BarModel pins it; R-1-KIT m1 left as designed). Restored on every load.
    // ----------------------------------------------------------------------------------------------------------------
    enum class BarDoor : std::uint8_t
    {
        Closed,
        Open,               // GO_STATE_ACTIVE
        Blasted,            // GO_STATE_ACTIVE_ALTERNATIVE
    };

    constexpr BarDoor BarDoorState(bool lovePotionDone, std::uint32_t barState, bool phalanxDead)
    {
        if (lovePotionDone || phalanxDead)
            return BarDoor::Open;
        if (barState == DungeonKit::State::Done)
            return BarDoor::Blasted;
        return BarDoor::Closed;
    }

    // The Tomb of the Seven's doors by its state (stock: IN_PROGRESS shuts both, DONE opens both, a reset opens the
    // entrance and shuts the exit).
    struct TombDoors
    {
        bool enterOpen;
        bool exitOpen;
    };

    constexpr TombDoors TombDoorsFor(std::uint32_t tombState)
    {
        switch (tombState)
        {
            case DungeonKit::State::InProgress: return { false, false };
            case DungeonKit::State::Done:       return { true, true };
            default:                            return { true, false };
        }
    }

    // The Seven's stock release cadence (wave 1 only: wave 2's D21 rotation replaces it).
    std::uint32_t constexpr kTombReleaseMs = 30000;
    std::uint32_t constexpr kTombFirstReleaseMs = 1000;
    std::uint32_t constexpr kTombResetMs = 15000;

    // Moira on the dais (section 7 #19): she stands down (friendly) once Dagran is DONE or after the Avatar kill saved
    // her (DATA_MOIRA_SAVED), on every load too.
    constexpr bool MoiraStandsDown(std::uint32_t emperorState, bool moiraSaved)
    {
        return moiraSaved || emperorState == DungeonKit::State::Done;
    }

    // The stock Moira / Priestess swap (quests 4004 / 4363 rewarded by everyone on the map) never runs mid-fight
    // (R-2-C m2): while Dagran's slot is IN_PROGRESS it waits; the attempt's end runs it again.
    constexpr bool MoiraSwapAllowed(std::uint32_t emperorState)
    {
        return emperorState != DungeonKit::State::InProgress;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hard modes (section 3.7, section 7 #15): all heroic only. The Encore's banner flags and the Cinder are saved
    // (a wipe keeps them); the console and the Avatar are per pull. A hard mode kill slot is recorded by the instance
    // when its boss slot goes DONE while lit; the hard mode loot bit rides the boss while lit (Encore: D6 sets it on
    // Theldren at his summon, the instance cannot reach a summon it never saw).
    // ----------------------------------------------------------------------------------------------------------------
    constexpr bool BannerThrowAllowed(std::uint32_t data, bool heroic, std::uint32_t ringState)
    {
        return data == 0 || (heroic && ringState != DungeonKit::State::Done);
    }

    constexpr bool BannerBurnAllowed(std::uint32_t data, bool heroic, bool thrown, std::uint32_t ringState)
    {
        return data == 0 || (heroic && thrown && ringState != DungeonKit::State::Done);
    }

    constexpr bool CinderAllowed(std::uint32_t data, bool heroic, std::uint32_t incendiusState)
    {
        return data == 0 || (heroic && incendiusState != DungeonKit::State::Done
            && incendiusState != DungeonKit::State::InProgress);
    }

    constexpr bool ConsoleAllowed(std::uint32_t data, bool heroic, bool wave2Bound, std::uint32_t argelmachState)
    {
        return data == 0 || (heroic && wave2Bound && argelmachState != DungeonKit::State::Done
            && argelmachState != DungeonKit::State::InProgress);
    }

    constexpr bool AvatarAllowed(std::uint32_t data, bool heroic, bool wave2Bound, std::uint32_t emperorState)
    {
        return data == 0 || (heroic && wave2Bound && emperorState == DungeonKit::State::InProgress);
    }

    // The Encore's kill (D4 request 2, D6): DATA_ENCORE_WON is accepted on heroic, with the banner burned, while the
    // Ring runs; the Ring's DONE then records BOSS_ENCORE. A burn in the seconds after the title holder died, or a Ring
    // won without an Encore, records nothing.
    constexpr bool EncoreWonAccepted(std::uint32_t data, bool heroic, bool burned, std::uint32_t ringState)
    {
        return data != 0 && heroic && burned && ringState == DungeonKit::State::InProgress;
    }

    // Section 10 (user, after R-1): a wipe during the Encore puts the banner out; the thrown banner stays (it can be
    // burned again before a later attempt).
    constexpr bool EncoreWipeUnlights(bool encoreRunning, bool burned)
    {
        return encoreRunning && burned;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Ring gallery stand-down for a section 2 start (section 10, R-1-RING MJ-1): every gallery unit (the
    // spectators, peasants and citizens, the armed Anvilrage soldiers, medics, officers and footmen, the two senators)
    // turns neutral for a group whose instance starts at S2a: its Finder dungeon is section 2's (308 / 311), or the
    // instance's first entry lands at the S2a start (a headless `.dc test brd-s2` run has no LFG group). Saved; the
    // Ring's slot, gates and credit are untouched (the Ring stays startable). [db] the gallery: 69 units at z -37 to
    // -34, 50-67 yd from kRingCenter, and two footmen at z -46, 71-72 yd.
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr NPC_ANVILRAGE_FOOTMAN = 8892;
    std::uint32_t constexpr NPC_ANVILRAGE_SOLDIER = 8893;
    std::uint32_t constexpr NPC_ANVILRAGE_MEDIC = 8894;
    std::uint32_t constexpr NPC_ANVILRAGE_OFFICER = 8895;
    float constexpr kGalleryRadius = 75.f;
    float constexpr kGalleryZMin = -48.f;               // above the Ring's floor (z -54) and the depths (z -83)
    float constexpr kGalleryStartEntryYd = 25.f;        // a first entry this close to the S2a start counts

    constexpr bool IsGalleryEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_ARENA_SPECTATOR:
            case NPC_SHADOWFORGE_PEASANT:
            case NPC_SHADOWFORGE_CITIZEN:
            case NPC_SHADOWFORGE_SENATOR:
            case NPC_ANVILRAGE_FOOTMAN:
            case NPC_ANVILRAGE_SOLDIER:
            case NPC_ANVILRAGE_MEDIC:
            case NPC_ANVILRAGE_OFFICER:
                return true;
            default:
                return false;
        }
    }

    constexpr bool IsGalleryUnit(std::uint32_t entry, float distanceFromRingCenter, float z)
    {
        return IsGalleryEntry(entry) && distanceFromRingCenter < kGalleryRadius && z > kGalleryZMin;
    }

    // `lfgDungeon`: the entering player's LFG group's dungeon (0 without one); `firstEntry`: no player entered this
    // instance before and no slot is IN_PROGRESS or DONE; `yardsFromS2Start`: the player's 2D distance to S2a.
    constexpr bool GalleryStandsDownOnEntry(bool alreadyStoodDown, std::uint32_t ringState, std::uint32_t lfgDungeon,
        std::uint32_t lfgSection2Normal, std::uint32_t lfgSection2Heroic, bool firstEntry, float yardsFromS2Start)
    {
        if (alreadyStoodDown || ringState == DungeonKit::State::Done)
            return false;
        if (lfgDungeon && (lfgDungeon == lfgSection2Normal || lfgDungeon == lfgSection2Heroic))
            return true;
        return firstEntry && yardsFromS2Start <= kGalleryStartEntryYd;
    }

    // An attempt ended: IN_PROGRESS went back to NOT_STARTED or FAIL (a wipe or an evade).
    constexpr bool AttemptEnded(std::uint32_t before, std::uint32_t after)
    {
        return before == DungeonKit::State::InProgress
            && (after == DungeonKit::State::NotStarted || after == DungeonKit::State::Fail);
    }

    // A slot no Load and no boss AI wrote is still TO_BE_DECIDED at the first Update (a boss whose grid never loaded,
    // the Vault, the hard mode kills). InstanceScript::SetBossState treats TO_BE_DECIDED as "loading": the first write
    // is stored without SaveToDB and without this script's switch. The instance settles them to NOT_STARTED once
    // (BRS R-1-KIT K-m1, F-1a).
    constexpr std::uint32_t SettledSlotState(std::uint32_t state)
    {
        return state == DungeonKit::State::ToBeDecided ? std::uint32_t(DungeonKit::State::NotStarted) : state;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (the leash frames of the stubs; section 3.8). Each boss WP writes its final polygon from the NM hull after
    // the playtest's `.gps` walk (an arena stops 2 yd short of a lethal edge: Incendius's causeway, Angerforge's drop,
    // Phalanx's floor edge).
    // ----------------------------------------------------------------------------------------------------------------
    inline ArenaRegion BoxRegion(float minX, float maxX, float minY, float maxY, float zMin, float zMax)
    {
        return ArenaRegion::Polygon({ { minX, minY }, { maxX, minY }, { maxX, maxY }, { minX, maxY } }, zMin, zMax);
    }

    inline ArenaRegion CircleRegion(Vec2 center, float radius, float zMin, float zMax)
    {
        return ArenaRegion::Circle(center, radius, zMin, zMax);
    }

    // A strip along a unit direction `axis` from `origin`: s in [sMin, sMax], |offset| <= halfWidth.
    inline ArenaRegion StripRegion(Vec2 origin, Vec2 axis, float sMin, float sMax, float halfWidth, float zMin,
        float zMax)
    {
        Vec2 const n{ -axis.y, axis.x };
        auto at = [&](float s, float w)
        {
            return Vec2{ origin.x + axis.x * s + n.x * w, origin.y + axis.y * s + n.y * w };
        };
        return ArenaRegion::Polygon({ at(sMin, -halfWidth), at(sMax, -halfWidth), at(sMax, halfWidth),
            at(sMin, halfWidth) }, zMin, zMax);
    }

    // Section 1.
    inline Arena GerstahnArena() { return Arena(CircleRegion(kGerstahnSpawn.XY(), 22.f, -74.f, -64.f)); }
    // Roccor's road from (580, -273) to (637, -249) and the plaza at its east end.
    inline Arena RoccorArena() { return Arena(BoxRegion(566.f, 652.f, -292.f, -232.f, -87.f, -75.f)); }
    // Grebmar's round cavern with the kennel row (hound entries x 581) and the Fetch exit (574.7, -196.6).
    inline Arena GrebmarArena() { return Arena(CircleRegion({ 600.f, -188.f }, 32.f, -88.f, -79.f)); }
    // The Ring's measured floor (D4's BrdRingOfLaw::RingFloorArena, NAVMESH 1.4; F-1a): the wall's distance from
    // kRingCenter by bearing (degrees, 0 = north +x, 90 = west +y, every 10 degrees plus the four gate alcoves), 0.5 yd
    // added (the mesh sits inside the wall); z -60..-46, so the gallery (z -37 to -34) is not in it. The floor is not
    // round: 38-43 yd on the cardinals, 23-26 yd on the diagonals. BrdRingOfLaw::kRingWall must stay equal (host test).
    struct RingWallSample
    {
        float bearingDeg;
        float distance;
    };

    inline std::array<RingWallSample, 36> constexpr kRingFloorWall{ {
        { 0.f, 38.5f }, { 11.7f, 43.2f }, { 20.f, 38.f }, { 30.f, 35.f }, { 40.f, 24.8f }, { 50.f, 24.2f },
        { 60.f, 26.f }, { 70.f, 29.f }, { 80.f, 33.f }, { 90.f, 35.f }, { 103.9f, 39.9f }, { 110.f, 36.f },
        { 120.f, 33.5f }, { 130.f, 31.f }, { 140.f, 29.5f }, { 150.f, 29.f }, { 160.f, 28.5f }, { 170.f, 27.5f },
        { 180.f, 32.f }, { 190.f, 36.f }, { 198.4f, 41.6f }, { 210.f, 37.f }, { 220.f, 23.f }, { 230.f, 23.f },
        { 240.f, 23.f }, { 250.f, 25.f }, { 260.f, 29.f }, { 270.f, 33.f }, { 280.f, 39.5f }, { 286.f, 44.9f },
        { 300.f, 40.f }, { 310.f, 41.f }, { 320.f, 42.f }, { 330.f, 38.f }, { 340.f, 37.f }, { 350.f, 37.f },
    } };
    float constexpr kRingFloorWallPad = 0.5f;
    float constexpr kRingFloorArenaZMin = -60.f;
    float constexpr kRingFloorArenaZMax = -46.f;

    inline std::vector<Vec2> RingFloorPolygon()
    {
        std::vector<Vec2> p;
        p.reserve(kRingFloorWall.size());
        for (RingWallSample const& s : kRingFloorWall)
            p.push_back(DungeonKit::Advance(kRingCenter.XY(), s.bearingDeg * DungeonKit::kPi / 180.f,
                s.distance + kRingFloorWallPad));
        return p;
    }

    inline Arena RingOfLawArena()
    {
        return Arena(ArenaRegion::Polygon(RingFloorPolygon(), kRingFloorArenaZMin, kRingFloorArenaZMax));
    }

    // Section 2.
    // Loregrain's 16 yd corridor north-east from the statue (ward spots (530, -243.5), (541, -254), (552, -264)).
    inline Arena LoregrainArena()
    {
        return Arena(StripRegion({ 530.0f, -243.5f }, { 0.7316f, -0.6817f }, -6.f, 50.f, 8.5f, -48.f, -37.f));
    }
    // The Black Vault (rim 12-18 yd): Stilgiss and Verek, and the Vault event.
    inline Arena BlackVaultArena() { return Arena(CircleRegion(kVaultCenter, 19.f, -53.f, -45.f)); }
    // Fineous's ramp (the patrol's 146 yd; corners (978, -370) and (938, -408)).
    inline Arena FineousArena() { return Arena(BoxRegion(888.f, 1012.f, -424.f, -322.f, -80.f, -44.f)); }
    // Incendius's Anvil bulge on the causeway: D11's measured floor (STAGE-D11 request 2, NM 2.5; F-1a), the bulge
    // and both necks (s about -26 to +24 along kIncendiusAxis). D11 leashes on its own BrdIncendius::ArenaFloor().
    inline Arena IncendiusArena()
    {
        return Arena(ArenaRegion::Polygon({ { 870.0f, -256.1f }, { 883.2f, -268.4f }, { 883.1f, -276.5f },
            { 885.7f, -282.3f }, { 889.1f, -284.6f }, { 900.2f, -285.3f }, { 904.3f, -289.7f }, { 911.7f, -283.0f },
            { 907.1f, -279.1f }, { 906.5f, -268.8f }, { 904.6f, -265.2f }, { 899.2f, -261.9f }, { 890.4f, -261.8f },
            { 877.9f, -248.8f } }, -76.f, -66.f));
    }
    // Bael'Gar: the cavern centre (disc r 33.7) and his spawn against the north wall.
    inline Arena BaelgarArena() { return Arena(CircleRegion(kBaelgarFightSpot.XY(), 36.f, -78.f, -60.f)); }

    // Section 3.
    // Angerforge's hall (the hall is about 74-77 yd wide; the drop behind him at x < 651 is out to its lip at 650:
    // STAGE-D14 request 1, F-1a).
    inline Arena AngerforgeArena() { return Arena(BoxRegion(650.f, 689.f, -16.f, 62.f, -62.f, -52.f)); }
    // Argelmach's chamber and its passage south.
    inline Arena ArgelmachArena()
    {
        return Arena(std::vector<ArenaRegion>{
            BoxRegion(834.f, 871.f, -2.f, 46.f, -56.f, -50.f),
            BoxRegion(808.f, 836.f, 2.f, 28.f, -56.f, -50.f) });
    }

    // Section 4.
    // The Guzzler's lower floor (Hurley; the six keg spots).
    inline Arena GuzzlerLowerArena() { return Arena(BoxRegion(862.f, 924.f, -180.f, -122.f, -54.f, -45.f)); }
    // The bar's upper floor (Phalanx; tables T1-T7 and the tank spot by the door).
    inline Arena BarUpperArena() { return Arena(CircleRegion({ 870.f, -210.f }, 32.f, -47.f, -40.f)); }
    // Flamelash's chamber out to the seven runes (the cardinal runes sit 34 yd out): D20's FightArena circle
    // (STAGE-D20 request 2, F-1a).
    inline Arena FlamelashArena() { return Arena(CircleRegion({ 1012.29f, -241.0f }, 38.f, -64.f, -57.f)); }
    // The Tomb: the lower floor (z -85.6) and the raised tier (z -78).
    inline Arena TheSevenArena() { return Arena(BoxRegion(1205.f, 1300.f, -300.f, -180.f, -88.f, -75.f)); }
    // The Iron Hall's open floor (x 1361-1400; the statue alcoves are out).
    inline Arena MagmusArena() { return Arena(BoxRegion(1360.f, 1401.f, -720.f, -550.f, -95.f, -88.f)); }
    // The throne room (the cross, the dais at z -87.6).
    inline Arena EmperorArena() { return Arena(BoxRegion(1333.f, 1429.f, -847.f, -715.f, -95.f, -83.f)); }

    // The arena of a boss state (a hard mode slot: its boss's; Ribbly and Plugger stay on SmartAI with no leash).
    inline Arena ArenaFor(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_GERSTAHN:         return GerstahnArena();
            case BOSS_ROCCOR:           return RoccorArena();
            case BOSS_GREBMAR:          return GrebmarArena();
            case BOSS_RING_OF_LAW:
            case BOSS_ENCORE:           return RingOfLawArena();
            case BOSS_LOREGRAIN:        return LoregrainArena();
            case BOSS_INCENDIUS:
            case BOSS_LORD_OF_THE_LAKE: return IncendiusArena();
            case BOSS_STILGISS_VEREK:
            case BOSS_VAULT:            return BlackVaultArena();
            case BOSS_FINEOUS:          return FineousArena();
            case BOSS_BAELGAR:          return BaelgarArena();
            case BOSS_ANGERFORGE:       return AngerforgeArena();
            case BOSS_ARGELMACH:
            case BOSS_PROTOTYPE:        return ArgelmachArena();
            case BOSS_HURLEY:           return GuzzlerLowerArena();
            case BOSS_PHALANX:          return BarUpperArena();
            case BOSS_FLAMELASH:        return FlamelashArena();
            case BOSS_THE_SEVEN:        return TheSevenArena();
            case BOSS_MAGMUS:           return MagmusArena();
            case BOSS_EMPEROR:
            case BOSS_AVATAR:           return EmperorArena();
            default:                    return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string: header "BDW" (no prefix of a stock save: stock wrote no header at all, only numbers),
    // the 24 boss states, then the extras below. A stock save (instance_blackrock_depths at 60bac7405: "e0 e1 e2 e3 e4
    // e5 GhostKillCount PhalanxActivationState LovePotionEventState", no header) is still read: its six encounter
    // fields go to their mirrors (the Ring, the Vault, the bar, the Tomb, the Lyceum, the Iron Hall), seven ghosts
    // kill the Tomb, and the completed-encounter mask (set before Load, from the DBC bits) fills the slots stock never
    // wrote.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "BDW";
    std::size_t constexpr kStockSaveMinFields = 6;
    std::size_t constexpr kStockSaveFields = 9;

    enum SaveExtra : std::size_t
    {
        EXTRA_RING_SENTENCE     = 0,
        EXTRA_RING_WAVE         = 1,
        EXTRA_RING_FIRST        = 2,
        EXTRA_RING_SECOND       = 3,
        EXTRA_BANNER_THROWN     = 4,
        EXTRA_BANNER_BURNED     = 5,
        EXTRA_ROPE              = 6,
        EXTRA_CINDER_USED       = 7,
        EXTRA_VAULT_CLOCK       = 8,
        EXTRA_MOIRA_SAVED       = 9,
        EXTRA_BAR               = 10,   // TYPE_BAR (stock encounter[2])
        EXTRA_PHALANX_ACTIVATED = 11,
        EXTRA_LOVE_POTION       = 12,
        EXTRA_LYCEUM            = 13,   // TYPE_LYCEUM (stock encounter[4])
        EXTRA_GALLERY_STOOD_DOWN = 14,  // F-1a: a short (older) save leaves it 0
        EXTRA_DOOMGRIP_ITEM     = 15,   // F-1a: DATA_VAULT_DOOMGRIP_ITEM
    };
    std::size_t constexpr kSaveExtraCount = 16;

    struct BrdSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        RingRolls ring;
        std::uint32_t bannerThrown = 0;
        std::uint32_t bannerBurned = 0;
        std::uint32_t rope = ROPE_NONE;
        std::uint32_t cinderUsed = 0;
        std::uint32_t vaultClock = 0;
        std::uint32_t moiraSaved = 0;
        std::uint32_t bar = DungeonKit::State::NotStarted;
        std::uint32_t phalanxActivated = DungeonKit::State::NotStarted;
        std::uint32_t lovePotion = DungeonKit::State::NotStarted;
        std::uint32_t lyceum = DungeonKit::State::NotStarted;
        std::uint32_t galleryStoodDown = 0;
        std::uint32_t doomgripItem = 0;
    };

    inline std::string FormatBrdSave(BrdSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_RING_SENTENCE] = s.ring.sentence;
        extras[EXTRA_RING_WAVE] = s.ring.wave;
        extras[EXTRA_RING_FIRST] = s.ring.first;
        extras[EXTRA_RING_SECOND] = s.ring.second;
        extras[EXTRA_BANNER_THROWN] = s.bannerThrown;
        extras[EXTRA_BANNER_BURNED] = s.bannerBurned;
        extras[EXTRA_ROPE] = s.rope;
        extras[EXTRA_CINDER_USED] = s.cinderUsed;
        extras[EXTRA_VAULT_CLOCK] = s.vaultClock;
        extras[EXTRA_MOIRA_SAVED] = s.moiraSaved;
        extras[EXTRA_BAR] = s.bar;
        extras[EXTRA_PHALANX_ACTIVATED] = s.phalanxActivated;
        extras[EXTRA_LOVE_POTION] = s.lovePotion;
        extras[EXTRA_LYCEUM] = s.lyceum;
        extras[EXTRA_GALLERY_STOOD_DOWN] = s.galleryStoodDown;
        extras[EXTRA_DOOMGRIP_ITEM] = s.doomgripItem;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The boss states a completed-encounter mask records (DONE), OR-ed into `states`.
    inline void ApplyEncounterMask(std::uint32_t mask, std::array<std::uint32_t, kBossCount>& states)
    {
        for (auto const& [bit, boss] : kEncounterBits)
            if (mask & (1u << bit))
                states[boss] = DungeonKit::State::Done;
    }

    // Only DONE survives a reload for the event fields (the stock Load turned IN_PROGRESS back; a SPECIAL bar is an
    // ale run in progress). The flags go back to 0 / 1; the hard mode kill slots need their boss DONE.
    inline std::uint32_t SanitizeEventField(std::uint32_t v)
    {
        return v == DungeonKit::State::Done ? v : std::uint32_t(DungeonKit::State::NotStarted);
    }

    inline void SanitizeBrdSave(BrdSave& s)
    {
        s.ring = SanitizeRingRolls(s.ring);
        s.bannerThrown = s.bannerThrown ? 1 : 0;
        s.bannerBurned = s.bannerBurned && s.bannerThrown ? 1 : 0;
        s.rope = s.rope <= ROPE_PLACED ? s.rope : std::uint32_t(ROPE_NONE);
        s.cinderUsed = s.cinderUsed ? 1 : 0;
        s.moiraSaved = s.moiraSaved ? 1 : 0;
        s.bar = SanitizeEventField(s.bar);
        s.phalanxActivated = SanitizeEventField(s.phalanxActivated);
        s.lovePotion = SanitizeEventField(s.lovePotion);
        s.lyceum = SanitizeEventField(s.lyceum);
        s.galleryStoodDown = s.galleryStoodDown ? 1 : 0;
        if (s.states[BOSS_VAULT] != DungeonKit::State::Done)
        {
            s.vaultClock = 0;
            s.doomgripItem = 0;
        }
        for (std::uint32_t slot = BOSS_ENCORE; slot <= BOSS_AVATAR; ++slot)
            if (s.states[HardModeBoss(slot)] != DungeonKit::State::Done)
                s.states[slot] = DungeonKit::State::NotStarted;
    }

    // The stock save (no header: "e0 .. e5 GhostKillCount PhalanxActivationState LovePotionEventState"; the last three
    // may be missing in an old one). False without the six encounter fields.
    inline bool ReadStockSave(std::string const& in, BrdSave& out)
    {
        std::vector<std::uint32_t> f;
        if (!DungeonKit::ReadSaveFields(in, "", kStockSaveMinFields, kStockSaveFields, f))
            return false;
        out.states[BOSS_RING_OF_LAW] = DungeonKit::SanitizeLoadedState(f[0]);
        out.states[BOSS_VAULT] = DungeonKit::SanitizeLoadedState(f[1]);
        out.bar = SanitizeEventField(f[2]);
        out.states[BOSS_THE_SEVEN] = DungeonKit::SanitizeLoadedState(f[3]);
        out.lyceum = SanitizeEventField(f[4]);
        out.states[BOSS_MAGMUS] = DungeonKit::SanitizeLoadedState(f[5]);
        if (f.size() > 6 && f[6] >= 7)
            out.states[BOSS_THE_SEVEN] = DungeonKit::State::Done;
        if (f.size() > 7)
            out.phalanxActivated = SanitizeEventField(f[7]);
        if (f.size() > 8)
            out.lovePotion = SanitizeEventField(f[8]);
        return true;
    }

    // Reads this script's "B D W" string, or a stock one; `encounterMask` is the instance's completed-encounter mask
    // (applied to a stock save only: a "B D W" save carries its own states). False on anything else (ignored).
    inline bool ParseBrdSave(std::string const& in, BrdSave& out, std::uint32_t encounterMask = 0)
    {
        out = BrdSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        BrdSave stockSave;
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
        if (stock)
        {
            out.bar = stockSave.bar;
            out.lyceum = stockSave.lyceum;
            out.phalanxActivated = stockSave.phalanxActivated;
            out.lovePotion = stockSave.lovePotion;
        }
        else
        {
            out.ring = { raw.extras[EXTRA_RING_SENTENCE], raw.extras[EXTRA_RING_WAVE], raw.extras[EXTRA_RING_FIRST],
                raw.extras[EXTRA_RING_SECOND] };
            out.bannerThrown = raw.extras[EXTRA_BANNER_THROWN];
            out.bannerBurned = raw.extras[EXTRA_BANNER_BURNED];
            out.rope = raw.extras[EXTRA_ROPE];
            out.cinderUsed = raw.extras[EXTRA_CINDER_USED];
            out.vaultClock = raw.extras[EXTRA_VAULT_CLOCK];
            out.moiraSaved = raw.extras[EXTRA_MOIRA_SAVED];
            out.bar = raw.extras[EXTRA_BAR];
            out.phalanxActivated = raw.extras[EXTRA_PHALANX_ACTIVATED];
            out.lovePotion = raw.extras[EXTRA_LOVE_POTION];
            out.lyceum = raw.extras[EXTRA_LYCEUM];
            out.galleryStoodDown = raw.extras[EXTRA_GALLERY_STOOD_DOWN];
            out.doomgripItem = raw.extras[EXTRA_DOOMGRIP_ITEM];
        }
        SanitizeBrdSave(out);
        return true;
    }

    inline char const* RopeStateName(std::uint32_t rope)
    {
        switch (rope)
        {
            case ROPE_NONE:     return "none";
            case ROPE_DROPPED:  return "dropped";
            case ROPE_PLACED:   return "placed";
            default:            return "?";
        }
    }
}

#endif
