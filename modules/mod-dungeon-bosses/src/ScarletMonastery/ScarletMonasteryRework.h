/*
 * mod-dungeon-bosses, Scarlet Monastery (map 189): the shared ids, boss states, data fields, texts, measured points,
 * wings, Finder sections, wing portals, arenas, the save string and the instance rules of the Scarlet Monastery build
 * (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md sections 3.1-3.3, 3.7, 3.8, 7 and the
 * user rulings of section 10: every section 7 decision as recommended; build spec docs/dungeons/
 * scarlet-monastery-rework.md, "HUB", and the four section docs scarlet-monastery-{1-graveyard,2-library,3-armory,
 * 4-cathedral}.md, "GY", "LIB", "ARM", "CATH").
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKitMath.h / DungeonKitState.h / DungeonKitArena.h), so
 * every <Boss>Logic.h and its host test can include it. Engine glue: the shared kit (src/Kit/DungeonKit.h) and the
 * Scarlet Monastery glue (ScarletMonasteryKit.h).
 *
 * Ownership: this file belongs to WP-S0 (the Scarlet Monastery skeleton) until it reports, then to the orchestrator.
 * A boss WP keeps its own spell ids (inside its slice below), tuning constants and script-local enums in its own
 * <Boss>Logic.h (convention: `enum <Boss>Spells : std::uint32_t { SPELL_<BOSS>_... = <id in its slice> }` and
 * `inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), and asks the orchestrator, in its report, for any
 * change here. Scarlet Monastery is not flex (HUB summary): 5 players on every difficulty.
 *
 * Measured points, frames and arenas are [navmesh estimate] (scarlet-monastery-build.NAVMESH-REPORT.md, folded into
 * the handoff's section 3.8) unless marked [db] (creature, gameobject or areatrigger rows, exact). Axes: +x north, +y
 * west. One map, four wings 600+ yd apart with no walkable link (FACTS-STOCK section 1). A boss WP tightens its own
 * arena in its own file after the playtest's `.gps` walk; the arenas here are the leash frames of the stubs.
 */

#ifndef MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_REWORK_H
#define MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_REWORK_H

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

namespace ScarletMonasteryRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapScarletMonastery = 189;
    // The stock instance name (handoff section 3.1, section 7 #1): the rework replaces the stock InstanceMapScript of
    // that name at load (same-named scripts registered later win; modules load after the core scripts), so
    // instance_template is untouched, and the two stock spell scripts registered in the same stock AddSC
    // (spell_forgiveness_dummy_visual, spell_transform_ghost_visual) keep working.
    char constexpr kInstanceScriptName[] = "instance_scarlet_monastery";
    // `.dbtest sm <boss> <mechanic>` (handoff section 3.2 item 5): the kit shell's command name, nested under the
    // shared `.dbtest` root (ScarletMonasteryTestCommand.cpp).
    char constexpr kTestCommand[] = "dbtest sm";
    char constexpr kLogDungeon[] = "sm";            // DungeonKit::LogMechanic("sm", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The stock instance had no boss states at all (handoff section 2.2). Slots 0-13 follow
    // the DungeonEncounter bits: 0-6 the stock rows 444-450 (read from var/extractors/dbc/DungeonEncounter.dbc
    // 2026-11-20: Bit = OrderIndex / 1000 = id - 444), with Fairbanks's bit 5 re-pointed to the Last Stand
    // (section 7 #3 A, FD-SM); 7-13 the seven new normal rows 1074-1080 FD-SM declares. 14-17 are the four hard mode
    // kills (written by the instance only).
    // ----------------------------------------------------------------------------------------------------------------
    enum SmBosses : std::uint32_t
    {
        BOSS_VISHAS         = 0,    // D1, wave 1 (section 1)
        BOSS_THALNOS        = 1,    // D4, wave 1 (section 1's end)
        BOSS_LOKSEY         = 2,    // D5, wave 1 (section 2)
        BOSS_DOAN           = 3,    // D8, wave 1 (section 2's end)
        BOSS_HEROD          = 4,    // D11, wave 2 (section 3's end)
        BOSS_LAST_STAND     = 5,    // D13, wave 2 (the instance writes it: the Chapel Door, Mograine's fall at 1%)
        BOSS_WHITEMANE      = 6,    // D14, wave 2 (section 4's end; opens only after the Last Stand is DONE)
        BOSS_IRONSPINE      = 7,    // D2, wave 1
        BOSS_COUNCIL        = 8,    // D3, wave 1 (Azshir and the Fallen Champion; DONE once both are dead)
        BOSS_KELL           = 9,    // D6, wave 1
        BOSS_HOLLIS_GREY    = 10,   // D7, wave 1
        BOSS_CRELL          = 11,   // D9, wave 2
        BOSS_HALDEN         = 12,   // D10, wave 2
        BOSS_THORNE         = 13,   // D12, wave 2
        BOSS_DESECRATION    = 14,   // D4H: Thalnos killed with the Desecration answered (set by the instance)
        BOSS_HERESY         = 15,   // D8H: Doan killed with the Heresy read (set by the instance)
        BOSS_CALL_TO_ARMS   = 16,   // D11H: Herod killed after the /taunt (set by the instance)
        BOSS_THE_TRUTH      = 17,   // D14H: Whitemane killed after the Torch (set by the instance)
    };
    std::uint32_t constexpr kBossCount = 18;
    std::uint32_t constexpr kEncounterCount = 14;       // DungeonEncounter bits 0-13
    std::uint32_t constexpr kStockEncounterCount = 7;   // the stock rows 444-450 (bits 0-6)

    static_assert(BOSS_THORNE + 1 == kEncounterCount, "slots 0-13 are the DungeonEncounter bits");
    static_assert(BOSS_WHITEMANE + 1 == kStockEncounterCount, "slots 0-6 are the stock rows 444-450");
    static_assert(BOSS_DESECRATION == 14 && BOSS_THE_TRUTH == 17, "section 3.2 item 2: 14-17 the hard mode kills");
    static_assert(BOSS_THE_TRUTH + 1 == kBossCount, "every boss state has a slot");

    // Names by boss state id (`.dbtest sm state`, logs).
    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Interrogator Vishas", "Bloodmage Thalnos", "Houndmaster Loksey", "Arcanist Doan", "Herod",
        "The Last Stand (Scarlet Commander Mograine)", "High Inquisitor Whitemane (with Mograine risen)", "Ironspine",
        "Azshir the Sleepless and the Fallen Champion", "Ambrose Kell, the Antiquarian",
        "Lector Hollis Grey, the Librarian", "Forgemaster Gideon Crell", "Drillmaster Corin Halden",
        "Brother Aldous Thorne, the Gardener", "The Desecration (Thalnos hard mode)",
        "The Kel'Thuzad Heresy (Doan hard mode)", "Call to Arms (Herod hard mode)",
        "The Truth (Whitemane hard mode)" } };

    constexpr bool IsEncounterSlot(std::uint32_t bossId)
    {
        return bossId < kEncounterCount;
    }

    constexpr bool IsHardModeSlot(std::uint32_t bossId)
    {
        return bossId >= BOSS_DESECRATION && bossId <= BOSS_THE_TRUTH;
    }

    // The boss slot a hard mode kill belongs to (kBossCount for anything else).
    constexpr std::uint32_t HardModeBoss(std::uint32_t hardModeSlot)
    {
        switch (hardModeSlot)
        {
            case BOSS_DESECRATION:  return BOSS_THALNOS;
            case BOSS_HERESY:       return BOSS_DOAN;
            case BOSS_CALL_TO_ARMS: return BOSS_HEROD;
            case BOSS_THE_TRUTH:    return BOSS_WHITEMANE;
            default:                return kBossCount;
        }
    }

    // The hard mode kill slot of an end boss (kBossCount for anything else).
    constexpr std::uint32_t HardModeKillSlot(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_THALNOS:      return BOSS_DESECRATION;
            case BOSS_DOAN:         return BOSS_HERESY;
            case BOSS_HEROD:        return BOSS_CALL_TO_ARMS;
            case BOSS_WHITEMANE:    return BOSS_THE_TRUTH;
            default:                return kBossCount;
        }
    }

    // The Finder section (= the wing) of a slot: 1 Graveyard, 2 Library, 3 Armory, 4 Cathedral (HUB ruling 2).
    constexpr std::uint32_t SectionOf(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_VISHAS:
            case BOSS_IRONSPINE:
            case BOSS_COUNCIL:
            case BOSS_THALNOS:
            case BOSS_DESECRATION:
                return 1;
            case BOSS_LOKSEY:
            case BOSS_KELL:
            case BOSS_HOLLIS_GREY:
            case BOSS_DOAN:
            case BOSS_HERESY:
                return 2;
            case BOSS_CRELL:
            case BOSS_HALDEN:
            case BOSS_HEROD:
            case BOSS_CALL_TO_ARMS:
                return 3;
            default:
                return bossId < kBossCount ? 4 : 0;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Wave switch (handoff section 3.2 item 3; the user rules both waves are built before one deploy, so the flag never
    // ships false, but it keeps the wave 1 checkpoint coherent). Wave 1 is sections 1-2 (the Graveyard and the
    // Library), wave 2 sections 3-4 (the Armory and the Cathedral). Until wave 2 flips it, the Armory and Cathedral
    // bosses keep their stock ScriptName, AIName, SmartAI and health (the DT twin BIND_WAVE_2 in apps/dbc-tools
    // source/npcs/scarlet_monastery/_common.py must agree: lib/test_scarlet_monastery_kit.py), their stub C++ registers
    // no AI, and the instance keeps the stock Cathedral path (the 80 yd pull on SetData(1, IN_PROGRESS), the stock
    // FAIL block, `_encounter` behind GetData(1) / GetData(6)). W2-SETUP flipped both in one commit.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr bool kWave2Bound = true;

    constexpr bool IsWave2Boss(std::uint32_t bossId)
    {
        return SectionOf(bossId) == 3 || SectionOf(bossId) == 4;
    }

    // A slot whose state a reworked BossAI writes (its wave bound). The instance writes the council (DONE once both
    // are dead), the Last Stand (the Chapel Door, the crossing restart, D13's DATA_LAST_STAND), the hard mode kills,
    // and, while wave 2 is unbound, the stock Herod / Mograine / Whitemane deaths (OnUnitDeath).
    constexpr bool SlotWrittenByScript(std::uint32_t bossId, bool wave2Bound = kWave2Bound)
    {
        if (bossId >= kEncounterCount || bossId == BOSS_COUNCIL || bossId == BOSS_LAST_STAND)
            return false;
        return !IsWave2Boss(bossId) || wave2Bound;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Instance data ids. 1-10 are the stock ids of instance_scarlet_monastery.cpp at their stock numbers (handoff
    // section 2.2; FACTS-STOCK section 4), kept for every reader: the stock SmartAI (action 34 on data 1 while wave 2
    // is unbound; AT 4089's SmartTrigger writes 2 and its condition type 13 reads it), hallows_end.cpp (data 5, see
    // below), mod-dungeon-clear (none of these; it reads the completed-encounter mask). New ids start at 20.
    // ----------------------------------------------------------------------------------------------------------------
    enum SmData : std::uint32_t
    {
        TYPE_MOGRAINE_AND_WHITE_EVENT   = 1,    // Get: the Cathedral pair (stock `_encounter`, or the slots 5-6 mirror)
        TYPE_ASHBRINGER_EVENT           = 2,    // Get/Set: the Ashbringer event (AT 4089; section 7 #16 A)
        DATA_MOGRAINE                   = 3,    // GetGuidData: Scarlet Commander Mograine (ObjectData)
        DATA_WHITEMANE                  = 4,    // GetGuidData: High Inquisitor Whitemane (ObjectData)
        DATA_DOOR_WHITEMANE             = 5,    // GetGuidData: the High Inquisitor's Door; Get/SetData: the Horseman
        DATA_HORSEMAN_EVENT             = 6,    // the stock instance's own Horseman id (unused by hallows_end.cpp)
        DATA_VORREL                     = 7,    // GetGuidData: Vorrel Sengutz (stock: unused; now ObjectData)
        DATA_ARCANIST_DOAN              = 8,    // GetGuidData: Arcanist Doan (stock: unused; now ObjectData)
        DATA_DOOR_CHAPEL                = 9,    // GetGuidData: the Chapel Door
        GAMEOBJECT_PUMPKIN_SHRINE       = 10,   // stock: unused (its OnGameObjectCreate case is commented out)

        // New (S0).
        DATA_HORSEMAN_PRIVATE           = 20,   // Get: the private Horseman state SetData(5, x) wrote (never a slot)
        DATA_LAST_STAND                 = 21,   // Get: slot 5. Set (D13): DONE at Mograine's fall, FAIL on a wipe
        DATA_CATHEDRAL_STAGE            = 22,   // Get: CathedralStage (D13 / D14 read it on Reset: a cold load)
        DATA_CHAPEL_DOOR_OPENED         = 23,   // Set (go_sm_chapel_door): the door was used (1 by a unit, 0 not)
        DATA_DESECRATION_TOUCH          = 24,   // Set (D4H's stones): stone 0-3 touched. Get: touches this attempt
        DATA_DESECRATION_RESULT         = 25,   // Get: the last judge (DesecrationVerdict)
        DATA_HARD_MODE_THALNOS          = 26,   // Get: the Desecration answered (saved)
        DATA_DOAN_PAGE_READ             = 27,   // Set (D8H's pages): page 0-3 read. Get: pages read (0-4)
        DATA_HARD_MODE_DOAN             = 28,   // Get: the Heresy read (all four pages; saved)
        DATA_HARD_MODE_HEROD            = 29,   // Get/Set(1) (D11H's /taunt): Herod taunted (saved)
        DATA_HARD_MODE_WHITEMANE        = 30,   // Get/Set(1) (D14H's Torch): the Torch pulled (saved)
        DATA_PORTALS                    = 31,   // Get: the bitmask of the wing portals that stand (PortalBit)
        DATA_DOAN_PAGES_MASK            = 32,   // Get: which pages were read (bit = page)
        DATA_ASHBRINGER_REFUSED         = 33,   // Get: how often the Ashbringer trigger was refused (debug)
        DATA_GM_SLOT_WRITE              = 34,   // Set: the next SetBossState passes the slot 6 guard (`.dbtest sm`)
        DATA_GM_PORTAL                  = 35,   // Set(1-4): stand portal n now (GM; in memory, not saved)
        DATA_GM_HARD_MODE               = 36,   // Set(kill slot 14-17): arm its flag past the trigger rules (GM)
    };

    static_assert(TYPE_MOGRAINE_AND_WHITE_EVENT == 1 && TYPE_ASHBRINGER_EVENT == 2 && DATA_MOGRAINE == 3
        && DATA_WHITEMANE == 4 && DATA_DOOR_WHITEMANE == 5 && DATA_HORSEMAN_EVENT == 6 && DATA_VORREL == 7
        && DATA_ARCANIST_DOAN == 8 && DATA_DOOR_CHAPEL == 9 && GAMEOBJECT_PUMPKIN_SHRINE == 10,
        "every stock data id keeps its stock number (instance_scarlet_monastery.cpp DataTypes)");
    static_assert(DATA_HORSEMAN_PRIVATE > GAMEOBJECT_PUMPKIN_SHRINE, "new data ids clear the stock ones");

    // The Headless Horseman's data id (src/server/scripts/Events/hallows_end.cpp: DATA_HORSEMAN_EVENT = 5; the stock
    // instance maps 5 to DATA_DOOR_WHITEMANE with no SetData case, so live GetData(5) is always 0 and
    // go_pumpkin_shrine's only real guard is its 100 yd FindNearestCreature). HUB ruling 9 keeps the Horseman as
    // live: GetData(5) answers 0 whatever SetData(5) received; SetData(5, x) writes a private field (never a slot,
    // never saved), readable as DATA_HORSEMAN_PRIVATE (section 7 #17 A).
    std::uint32_t constexpr kHallowsEndHorsemanData = 5;
    static_assert(kHallowsEndHorsemanData == DATA_DOOR_WHITEMANE, "the stock data id mismatch the rework keeps");

    constexpr std::uint32_t HorsemanGetData(std::uint32_t /*privateState*/)
    {
        return 0;       // live behavior: the shrine's "already running / done" guard never fires
    }

    // The GetData id of a hard mode kill slot's flag (0 for anything else).
    constexpr std::uint32_t HardModeFlagData(std::uint32_t killSlot)
    {
        switch (killSlot)
        {
            case BOSS_DESECRATION:  return DATA_HARD_MODE_THALNOS;
            case BOSS_HERESY:       return DATA_HARD_MODE_DOAN;
            case BOSS_CALL_TO_ARMS: return DATA_HARD_MODE_HEROD;
            case BOSS_THE_TRUTH:    return DATA_HARD_MODE_WHITEMANE;
            default:                return 0;
        }
    }

    // AI actions the instance sends (DoAction) to the Cathedral units once wave 2 binds (D13 / D14 implement them; a
    // stub AI ignores them).
    enum SmActions : std::int32_t
    {
        ACTION_SM_LAST_STAND_START  = 18901,    // to Mograine: the Chapel Door opened or the crossing was crossed
        ACTION_SM_MOGRAINE_FALLEN   = 18902,    // to Mograine: the Last Stand is DONE (sent at the DONE write only;
                                                // on a cold load D13 reads DATA_CATHEDRAL_STAGE in Reset)
        ACTION_SM_WHITEMANE_VIGIL   = 18903,    // to Whitemane: walk out to the vigil and kneel (slot 5 DONE)
        ACTION_SM_ASHBRINGER        = 18904,    // to Mograine: the instance accepted the Ashbringer (AT 4089)
    };

    // The Ashbringer cameo (HANDOFF section 10, STAGE-R-1-KIT m-1 default c): moved from the stock SmartAI (3976 rows
    // 0, 25-27 and list 397602; AT 4089 rows 2-3, AzerothCore DB data) into D13's AI, so a refused Ashbringer plays
    // nothing. The instance sends ACTION_SM_ASHBRINGER on accepting it: he yells line 6; the item's periodic effect
    // hitting him then makes him kneel to its bearer (line 3) and summons Highlord Mograine, whose stock SmartAI
    // (16062, list 1606200) plays the rest (the Forgiveness kills him).
    std::uint32_t constexpr kSpellAshbringerEffect = 28441;     // "AB Effect 000", the item aura's periodic dummy
    std::uint8_t constexpr kSayMograineAshbringerKneel = 3;     // stock "You hold my father's blade, $n..."
    std::uint8_t constexpr kSayMograineAshbringerYell = 6;      // stock "Bow down! Kneel BEFORE the Ashbringer!..."

    // ----------------------------------------------------------------------------------------------------------------
    // Factions, game events, items
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kFactionFriendly = 35;          // stock FACTION_FRIENDLY (the Ashbringer sweep)
    std::uint32_t constexpr kGameEventScourgeBossInInstance = 120;  // Thalnos's Scorn summon condition (stock)
    std::uint32_t constexpr kGameEventHallowsEnd = 12;      // the Horseman's objects on the Graveyard lawn
    std::uint32_t constexpr kItemCorruptedAshbringer = 22691;   // AT 4089's condition (no source on this server)
    std::uint32_t constexpr kItemScarletKey = 7146;         // lock 299 (the interior doors go keyless, section 7 #14)
    std::uint32_t constexpr kAreaTriggerAshbringer = 4089;  // [db] (864.62, 1321.6, 18.07), r 5, SmartTrigger

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures: stock entries [db] and the new ones (ids.yaml reservation `scarlet_monastery`, creature 300900-300979;
    // handoff section 3.3; wave 1 300900-300939 below every wave 2 id, the heroic mint order).
    // ----------------------------------------------------------------------------------------------------------------
    enum SmCreatures : std::uint32_t
    {
        // Bosses (stock)
        NPC_VISHAS                  = 3983,
        NPC_IRONSPINE               = 6489,
        NPC_AZSHIR                  = 6490,
        NPC_FALLEN_CHAMPION         = 6488,
        NPC_THALNOS                 = 4543,
        NPC_LOKSEY                  = 3974,
        NPC_DOAN                    = 6487,
        NPC_HEROD                   = 3975,
        NPC_MOGRAINE                = 3976,
        NPC_WHITEMANE               = 3977,
        NPC_FAIRBANKS               = 4542,     // D14H's trigger (ruling 44: no encounter of his own)
        // Stock units the rework touches
        NPC_VORREL                  = 3981,     // Vishas's death line goes to him (stock SmartAI 3983 row 5)
        NPC_SCORN                   = 14693,    // Thalnos's death summon while game event 120 runs (stock row 7)
        NPC_HEADLESS_HORSEMAN       = 23682,
        NPC_HIGHLORD_MOGRAINE       = 16062,    // the Ashbringer cameo
        NPC_HAUNTING_PHANTASM       = 6427,     // D4H's wrong answer
        NPC_SCARLET_TRAINEE         = 6575,     // Herod's summon group 1 on death
        NPC_TRACKING_HOUND          = 4304,
        // The stock Cathedral pull (instance_scarlet_monastery.cpp SetData(1, IN_PROGRESS), wave 2 unbound only)
        NPC_SCARLET_MONK            = 4540,
        NPC_SCARLET_ABBOT           = 4303,
        NPC_SCARLET_CHAMPION        = 4302,
        NPC_SCARLET_CENTURION       = 4301,
        NPC_SCARLET_WIZARD          = 4300,
        NPC_SCARLET_CHAPLAIN        = 4299,
        // The stock Ashbringer exclusions (the Graveyard list and the rabbit)
        NPC_RABBIT                  = 721,
        NPC_RAT                     = 4075,
        NPC_SCARLET_SENTRY          = 4283,
        NPC_SCARLET_SCRYER          = 4293,
        NPC_UNFETTERED_SPIRIT       = 4308,
        NPC_SCARLET_TORTURER        = 4306,
        NPC_ANGUISHED_DEAD          = 6426,
        NPC_SUFFERING_VICTIM        = 6547,

        // New, wave 1 (300900-300939)
        NPC_SM_IRONSPINE_FIST       = 300900,   // D2
        NPC_SM_IRONSPINE_RIBCAGE    = 300901,
        NPC_SM_IRONSPINE_EYE        = 300902,
        NPC_SM_GALVAR               = 300903,   // D4H, the risen heroes
        NPC_SM_FAIRBELL             = 300904,
        NPC_SM_VOSS                 = 300905,
        NPC_SM_GOODCHILDE           = 300906,
        NPC_SM_RALLYING_BANNER      = 300907,
        NPC_SM_TRACKING_HOUND       = 300908,   // D5
        NPC_SM_KENNEL_PUP           = 300909,
        NPC_SM_KELL                 = 300910,   // D6
        NPC_SM_RELIC_TRIGGER        = 300911,
        NPC_SM_GALLERY_SKELETON     = 300912,
        NPC_SM_HOLLIS_GREY          = 300913,   // D7
        NPC_SM_CURSED_BOOK          = 300914,
        NPC_SM_INFERNAL             = 300915,
        NPC_SM_SPIDERLING           = 300916,
        NPC_SM_SPECTRAL_TROLL       = 300917,
        NPC_SM_PHANTOM_GRUNT        = 300918,
        NPC_SM_ARCANE_ANCHOR        = 300919,   // D8
        NPC_SM_PHYLACTERY_SHARD     = 300920,   // D8H
        NPC_SM_RISEN_PURGED         = 300921,
        NPC_SM_STALKER              = 300922,   // the generic stalker, wave 1 (the orchestrator's template)
        // New, wave 2 (300940-300979)
        NPC_SM_CRELL                = 300940,   // D9
        NPC_SM_SCARLET_RECRUIT      = 300941,
        NPC_SM_HALDEN               = 300942,   // D10
        NPC_SM_DRILL_RECRUIT        = 300943,
        NPC_SM_GARRISON_TRAINEE     = 300944,   // D11H
        NPC_SM_PLANTED_RAVAGER      = 300945,
        NPC_SM_THORNE               = 300946,   // D12
        NPC_SM_SEEDLING             = 300947,
        NPC_SM_BRIAR                = 300948,
        NPC_SM_BLESSED_BRAMBLE      = 300949,
        NPC_SM_CHAPEL_GUARD_CHAMPION = 300950,  // D13, the companies
        NPC_SM_CAPTAIN_OF_THE_GUARD = 300951,
        NPC_SM_COMPANY_CHAPLAIN     = 300952,
        NPC_SM_COMPANY_MONK         = 300953,
        NPC_SM_COMPANY_WIZARD       = 300954,
        NPC_SM_COMPANY_ABBOT        = 300955,
        NPC_SM_VIGIL_FAIRBANKS      = 300956,   // D14H
        NPC_SM_ALEXANDROS_SPIRIT    = 300957,
        NPC_SM_STALKER_WAVE2        = 300958,   // the generic stalker, wave 2
    };

    std::uint32_t constexpr kCreaturesFirst = 300900;
    std::uint32_t constexpr kCreaturesLast = 300979;
    std::uint32_t constexpr kCreaturesWave2First = 300940;
    // The gear stage's look (300880 Rallying Standard) and the Zealot's vendors (300890-300893) sit just below.
    std::uint32_t constexpr kGearCreaturesFirst = 300880;

    // The Ashbringer sweep (section 7 #16 A): every creature created in the map turns friendly except the stock
    // Graveyard list (instance_scarlet_monastery.cpp OnCreatureCreate, upstream b70b14ed6) and every rework entry (the
    // gear's look, the companies, the vigil Fairbanks, the spirit, Thorne's units and every other new unit).
    constexpr bool AshbringerSweeps(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_RABBIT:
            case NPC_VISHAS:
            case NPC_RAT:
            case NPC_SCARLET_SENTRY:
            case NPC_SCARLET_SCRYER:
            case NPC_UNFETTERED_SPIRIT:
            case NPC_SCARLET_TORTURER:
            case NPC_ANGUISHED_DEAD:
            case NPC_HAUNTING_PHANTASM:
            case NPC_FALLEN_CHAMPION:
            case NPC_THALNOS:
            case NPC_SUFFERING_VICTIM:
                return false;
            default:
                return !(entry >= kGearCreaturesFirst && entry <= kCreaturesLast);
        }
    }

    // Which creatures the sweep reaches (STAGE-RF-1 m-1): the Cathedral's own spawns only (`spawned`: a database
    // spawn, not a summon; `wing`: WingOf its position, 4 the Cathedral). Stock swept every creature in the map, so a
    // grid of another wing loaded later (Loksey, Doan, Herod and his trainees) could come up friendly and its section
    // never complete; the item holder walks into the Cathedral, and only its nave and gardens turn.
    std::uint32_t constexpr kAshbringerWing = 4;

    constexpr bool AshbringerSweepsUnit(std::uint32_t entry, bool spawned, std::uint32_t wing)
    {
        return spawned && wing == kAshbringerWing && AshbringerSweeps(entry);
    }

    // A reload after the Ashbringer event (R-1-KIT m-2): a swept creature created again turns friendly at once (stock
    // lost the whole state on a reload; the save keeps the flag, so the nave stays friendly).
    constexpr bool AshbringerKeepsFriendly(bool ashbringerRan, std::uint32_t entry, bool alive, bool spawned,
        std::uint32_t wing)
    {
        return ashbringerRan && alive && AshbringerSweepsUnit(entry, spawned, wing);
    }

    // The boss slot of a spawned boss entry (stock or new); std::nullopt for anything else.
    constexpr std::optional<std::uint32_t> BossOfEntry(std::uint32_t entry)
    {
        switch (entry)
        {
            case NPC_VISHAS:            return BOSS_VISHAS;
            case NPC_THALNOS:           return BOSS_THALNOS;
            case NPC_LOKSEY:            return BOSS_LOKSEY;
            case NPC_DOAN:              return BOSS_DOAN;
            case NPC_HEROD:             return BOSS_HEROD;
            case NPC_MOGRAINE:          return BOSS_LAST_STAND;
            case NPC_WHITEMANE:         return BOSS_WHITEMANE;
            case NPC_IRONSPINE:         return BOSS_IRONSPINE;
            case NPC_AZSHIR:
            case NPC_FALLEN_CHAMPION:   return BOSS_COUNCIL;
            case NPC_SM_KELL:           return BOSS_KELL;
            case NPC_SM_HOLLIS_GREY:    return BOSS_HOLLIS_GREY;
            case NPC_SM_CRELL:          return BOSS_CRELL;
            case NPC_SM_HALDEN:         return BOSS_HALDEN;
            case NPC_SM_THORNE:         return BOSS_THORNE;
            default:                    return std::nullopt;
        }
    }

    // GetGuidData keys besides the stock ones: the boss unit of a slot (kGuidBossBase + slot), Azshir and the stock
    // Fairbanks by hand.
    std::uint32_t constexpr kGuidBossBase = 200;
    std::uint32_t constexpr kGuidAzshir = 230;
    std::uint32_t constexpr kGuidFairbanks = 231;
    static_assert(kGuidBossBase + kBossCount <= kGuidAzshir, "the boss keys stay below the hand keys");

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects: stock [db] and the new ones (ids.yaml reservation `scarlet_monastery`, gameobject 301310-301339)
    // ----------------------------------------------------------------------------------------------------------------
    enum SmGameObjects : std::uint32_t
    {
        GO_CHAPEL_DOOR              = 104591,   // guid 11875, lock 299 (keyless: section 7 #14 A), the Last Stand start
        GO_CHAPEL_LEVER             = 104589,   // guid 11881, 4 yd inside, SmartGameObjectAI "activate 11875"
        GO_HIGH_INQUISITOR_DOOR     = 104600,   // guid 11877, lock 85; opens when the Last Stand is DONE
        GO_SECRET_DOOR              = 97700,    // guid 11876, Fairbanks's room; follows the Torch (D14H)
        GO_TORCH                    = 97701,    // guid 11894, SmartGameObjectAI "activate 11876" (D14H replaces it)
        GO_HERODS_DOOR              = 101854,   // guid 32250, lock 299 (keyless); shut while Herod fights
        GO_HERODS_LEVER             = 101855,   // guid 32260, 6 yd inside; not selectable while Herod fights
        GO_DOANS_STRONGBOX          = 103821,   // the Scarlet Key
        GO_PUMPKIN_SHRINE           = 186267,   // Hallow's End (go_pumpkin_shrine)
        GO_ARMOR_CRATE              = 3703,     // Crell's recruits (section 7 #29 A)
        GO_WEAPON_CRATE             = 3704,

        GO_SM_GRAVESTONE_GALVAR     = 301310,   // D4H (the stone order: Galvar, Fairbell, Voss, Goodchilde)
        GO_SM_GRAVESTONE_FAIRBELL   = 301311,
        GO_SM_GRAVESTONE_VOSS       = 301312,
        GO_SM_GRAVESTONE_GOODCHILDE = 301313,
        GO_SM_BLOOD_RITE            = 301314,
        GO_SM_RELIC_PEDESTAL        = 301315,   // D6
        GO_SM_RELIC_CASK            = 301316,
        GO_SM_RELIC_STAFF           = 301317,
        GO_SM_RELIC_SKULL           = 301318,
        GO_SM_CHAMBER_SEAL          = 301319,   // D8 (KT-SM SealedArena)
        GO_SM_EVIDENCE_PAGE_1       = 301320,   // D8H
        GO_SM_EVIDENCE_PAGE_2       = 301321,
        GO_SM_EVIDENCE_PAGE_3       = 301322,
        GO_SM_EVIDENCE_PAGE_4       = 301323,
        GO_SM_WING_PORTAL           = 301324,   // S0 (go_sm_wing_portal; section 7 #15 A)
        GO_SM_FORGE                 = 301325,   // D9
        GO_SM_ANVIL                 = 301326,
        GO_SM_QUENCH_TROUGH         = 301327,
        GO_SM_WALL_RACK             = 301328,   // D11H
        GO_SM_PLANTED_AXE           = 301329,   // D11H, only if the creature stand-in fails (VR)
        GO_SM_LAST_STAND_CHEST      = 301330,   // D13 (section 7 #20 A), normal
        GO_SM_LAST_STAND_CHEST_H    = 301331,   // D13, heroic
    };

    std::uint32_t constexpr kGameObjectsFirst = 301310;
    std::uint32_t constexpr kGameObjectsLast = 301339;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 212300-213499, ids.yaml reservation `scarlet_monastery`; declared in apps/dbc-tools
    // source/npcs/scarlet_monastery/). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h. The
    // kit-wide 205200 (cast bar) and 205201 ("Standing in It" slow) are used by id (DungeonKitIds.h). The gear's
    // item-copy pool starts at 219000: the build stays below it.
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 212300, 213499 };
    IdSlice constexpr kSpellsShared{ 212300, 212319 };              // S0: credit spells, portal, cast bars
    IdSlice constexpr kSpellsVishas{ 212320, 212349 };              // D1  (VI)
    IdSlice constexpr kSpellsIronspine{ 212350, 212389 };           // D2  (IR)
    IdSlice constexpr kSpellsCouncil{ 212390, 212439 };             // D3  (CV)
    IdSlice constexpr kSpellsThalnos{ 212440, 212479 };             // D4  (TH)
    IdSlice constexpr kSpellsDesecration{ 212480, 212539 };         // D4H (TH hard mode)
    IdSlice constexpr kSpellsLoksey{ 212540, 212569 };              // D5  (LK)
    IdSlice constexpr kSpellsKell{ 212570, 212609 };                // D6  (AN)
    IdSlice constexpr kSpellsHollisGrey{ 212610, 212669 };          // D7  (LB)
    IdSlice constexpr kSpellsDoan{ 212670, 212709 };                // D8  (DN)
    IdSlice constexpr kSpellsHeresy{ 212710, 212749 };              // D8H (DN hard mode)
    IdSlice constexpr kSpellsSpareWave1{ 212750, 212899 };
    IdSlice constexpr kSpellsCrell{ 212900, 212949 };               // D9  (AR)
    IdSlice constexpr kSpellsHalden{ 212950, 212979 };              // D10 (MA)
    IdSlice constexpr kSpellsHerod{ 212980, 213019 };               // D11 (HB)
    IdSlice constexpr kSpellsCallToArms{ 213020, 213059 };          // D11H (HB hard mode)
    IdSlice constexpr kSpellsThorne{ 213060, 213099 };              // D12 (GD)
    IdSlice constexpr kSpellsLastStand{ 213100, 213149 };           // D13 (LS)
    IdSlice constexpr kSpellsWhitemane{ 213150, 213189 };           // D14 (WM)
    IdSlice constexpr kSpellsTheTruth{ 213190, 213239 };            // D14H (WM hard mode)
    IdSlice constexpr kSpellsSpare{ 213240, 213499 };

    inline std::array<IdSlice, 21> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsVishas, kSpellsIronspine, kSpellsCouncil, kSpellsThalnos, kSpellsDesecration,
        kSpellsLoksey, kSpellsKell, kSpellsHollisGrey, kSpellsDoan, kSpellsHeresy, kSpellsSpareWave1, kSpellsCrell,
        kSpellsHalden, kSpellsHerod, kSpellsCallToArms, kSpellsThorne, kSpellsLastStand, kSpellsWhitemane,
        kSpellsTheTruth, kSpellsSpare } };

    // The encounter credits the instance sends (handoff section 3.11 #3, the BRD 211066 precedent): server-side DUMMY
    // spells never cast; FD-SM's instance_encounters rows name them (creditType 1). The council's when both Azshir and
    // the Fallen Champion are dead; the Last Stand's when Mograine falls at 1% (D13 sends DATA_LAST_STAND = DONE).
    std::uint32_t constexpr kSpellCouncilCredit = 212300;
    std::uint32_t constexpr kSpellLastStandCredit = 212301;
    static_assert(kSpellsShared.Contains(kSpellCouncilCredit) && kSpellsShared.Contains(kSpellLastStandCredit),
        "S0's shared slice");

    IdSlice constexpr kCreaturesReservation{ kCreaturesFirst, kCreaturesLast };
    IdSlice constexpr kCreaturesWave1{ 300900, 300939 };
    IdSlice constexpr kCreaturesWave2{ 300940, 300979 };
    IdSlice constexpr kGameObjectsReservation{ kGameObjectsFirst, kGameObjectsLast };

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text groups per unit, the section docs' text tables). A boss WP names its groups in its own Logic
    // header (enum <Boss>Texts : std::uint8_t { SAY_..., EMOTE_... }) inside its range; groups below `firstNew` are
    // stock rows (kept, some moved to a new moment). The boss WP's SQL rev writes the new rows. A hard mode WP uses its
    // boss's range where its boss speaks (the comments below name the owner).
    // ----------------------------------------------------------------------------------------------------------------
    struct TextRange
    {
        std::uint32_t entry;
        std::uint8_t first;
        std::uint8_t last;
        std::uint8_t firstNew;      // groups first..firstNew-1 are stock rows
    };

    inline std::array<TextRange, 25> constexpr kTextRanges{ {
        { NPC_VISHAS, 0, 6, 4 },                // D1: 0-3 stock (1 / 2 moved to 70 / 30%), 4-6 new
        { NPC_VORREL, 0, 0, 1 },                // D1: his stock line 0 on Vishas's death
        { NPC_IRONSPINE, 0, 3, 0 },             // D2
        { NPC_SM_IRONSPINE_EYE, 0, 0, 0 },      // D2: the Glare (heroic)
        { NPC_AZSHIR, 0, 2, 0 },                // D3
        { NPC_FALLEN_CHAMPION, 0, 3, 0 },       // D3
        { NPC_THALNOS, 0, 4, 3 },               // D4: 0-2 stock, 3 new; 4 the Desecration's yell (D4H)
        { NPC_SM_GOODCHILDE, 0, 0, 0 },         // D4H
        { NPC_SM_GALVAR, 0, 0, 0 },             // D4H
        { NPC_LOKSEY, 0, 4, 1 },                // D5: 0 stock
        { NPC_SM_KELL, 0, 6, 0 },               // D6
        { NPC_SM_HOLLIS_GREY, 0, 7, 0 },        // D7
        { NPC_DOAN, 0, 5, 2 },                  // D8: 0-1 stock; 2 the Heresy's zone yell (D8H), 3 (D8H, HM5); 4-5 D8
        { NPC_SM_CRELL, 0, 7, 0 },              // D9
        { NPC_SM_HALDEN, 0, 9, 0 },             // D10
        { NPC_HEROD, 0, 9, 5 },                 // D11: 0-4 stock; 5-8 the hard mode's (D11H); 9 the seal (F-2c)
        { NPC_SCARLET_TRAINEE, 0, 0, 1 },       // D11: 0 stock (his death)
        { NPC_SM_THORNE, 0, 6, 0 },             // D12
        { NPC_MOGRAINE, 0, 13, 7 },             // D13 7-11; D14 12-13. 0-6 stock (3 and 6 the Ashbringer; 4-5
                                                // shared by the cameo and D14H's SAY_MOGRAINE_FATHER / FORGIVE)
        { NPC_WHITEMANE, 0, 7, 3 },             // D14 3-5, 7 (0-2 stock; 0 split into 3 + 2); D14H 6
        { NPC_SM_VIGIL_FAIRBANKS, 0, 0, 0 },    // D14H
        { NPC_SM_ALEXANDROS_SPIRIT, 0, 2, 0 },  // D14H: 0-1 copies of Highlord Mograine 16062's lines 0 and 2;
                                                // 2 the Verdict's raid emote
        { NPC_SM_IRONSPINE_RIBCAGE, 0, 0, 1 },  // D2: no lines (the range keeps the entry known)
        { NPC_SM_KENNEL_PUP, 0, 0, 1 },         // D5: no lines
        { NPC_SM_ARCANE_ANCHOR, 0, 0, 1 },      // D8: no lines
    } };

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

    // Boss spawns [db] (and the new bosses' spots: section 3.8, NM).
    Point3 constexpr kVishasSpawn{ 1786.55f, 1124.44f, 7.57f };
    Point3 constexpr kVorrelSpawn{ 1786.22f, 1119.48f, 8.76f };
    Point3 constexpr kIronspineStockSpawn{ 1749.61f, 1247.4f, 18.16f };     // guid 12164 (D2 moves it, section 7 #24)
    Point3 constexpr kIronspineHome{ 1796.5f, 1285.5f, 18.8f };            // the lawn (section 7 #24 A)
    Point3 constexpr kFallenChampionSpawn{ 1756.17f, 1345.45f, 19.37f };   // guid 39894
    Point3 constexpr kAzshirSpawn{ 1850.97f, 1392.82f, 20.48f };           // guid 1975841 (respawn 300 -> 86400, S0)
    Point3 constexpr kCouncilLawn{ 1798.5f, 1348.5f, 18.6f };              // the council fights here (section 7 #18 A)
    Point3 constexpr kThalnosSpawn{ 1820.34f, 1416.71f, -7.92f };
    Point4 constexpr kScornSummon{ 1797.84f, 1233.68f, 18.3153f, 1.58286f };   // [db] stock SmartAI 4543 row 7
    Point3 constexpr kLokseySpawn{ 119.94f, -260.87f, 18.63f };
    Point3 constexpr kKellSpot{ 242.8f, -329.2f, 18.9f };
    Point3 constexpr kHollisGreySpot{ 254.8f, -389.2f, 20.49f };           // the pocket (section 7 #26 A; D7's floor)
    Point3 constexpr kDoanSpawn{ 148.32f, -428.69f, 18.49f };              // patrol path 401240 (kept out of combat)
    Point3 constexpr kCrellAnvil{ 1776.f, -388.f, 8.0f };
    Point3 constexpr kHaldenSpot{ 1875.f, -400.f, 18.7f };
    Point3 constexpr kHerodSpawn{ 1965.09f, -431.61f, 6.26f };
    Point3 constexpr kThorneSpot{ 908.2f, 1399.2f, 19.0f };                 // section 7 #32 A
    Point3 constexpr kMograineSpawn{ 1153.87f, 1398.39f, 32.61f };         // guid 40029
    Point4 constexpr kHighlordMograineSummon{ 1033.46f, 1399.1f, 27.34f, 6.258f };  // the cameo (stock 3976 row 27)
    Point3 constexpr kWhitemaneSpawn{ 1202.13f, 1399.07f, 29.09f };        // guid 39946
    Point3 constexpr kFairbanksSpawn{ 1158.86f, 1354.27f, 30.39f };        // guid 40039
    Point3 constexpr kWhitemaneVigil{ 1146.f, 1398.f, 32.1f };              // section 7 #33 A
    Point3 constexpr kMograineBody{ 1154.f, 1398.4f, 33.0f };

    // Doors [db].
    Point3 constexpr kChapelDoor{ 1069.95f, 1399.14f, 30.80f };
    Point3 constexpr kHighInquisitorDoor{ 1173.01f, 1398.91f, 31.97f };
    Point3 constexpr kHerodsDoor{ 1933.69f, -431.65f, 18.67f };
    Point3 constexpr kHerodsLever{ 1939.48f, -428.0f, 17.08f };

    // ----------------------------------------------------------------------------------------------------------------
    // The wings (FACTS-STOCK section 1: spawn bounding boxes, padded to the starts and exits) and the Finder sections
    // (handoff section 3.8): the starts stay the stock spots [db] (the areatrigger_teleport targets = the
    // lfg_dungeon_template rows = the checkpoint rows), the end slot whose kill completes the section
    // (lastEncounterDungeon 18 / 165 / 163 / 164; heroic 314-317, WP-H), and the doors a teleported group meets.
    // ----------------------------------------------------------------------------------------------------------------
    struct WingBox
    {
        float minX;
        float maxX;
        float minY;
        float maxY;

        constexpr bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
    };

    struct FinderSection
    {
        std::uint32_t number;           // 1-4
        char const* name;
        std::uint32_t lfgNormal;        // the stock LFGDungeons rows
        std::uint32_t lfgHeroic;        // WP-H's heroic rows (section 3.3)
        Point4 start;                   // [db]
        std::uint32_t endSlot;
        WingBox wing;
        Point3 exitTrigger;             // [db] the in-map exit areatrigger (r 8) near the start
        std::array<std::uint32_t, 3> doors;     // GO entries on the path (0 = none)
    };

    float constexpr kExitTriggerRadius = 8.f;

    inline std::array<FinderSection, 4> constexpr kSections{ {
        { 1, "Graveyard", 18, 314, { 1688.99f, 1053.48f, 18.6775f, 0.00117f }, BOSS_THALNOS,
            { 1670.f, 1880.f, 1020.f, 1460.f }, { 1687.57f, 1040.09f, 20.98f }, { { 0, 0, 0 } } },
        { 2, "Library", 165, 315, { 255.346f, -209.09f, 18.6773f, 6.26656f }, BOSS_DOAN,
            { 100.f, 300.f, -470.f, -180.f }, { 253.601f, -196.804f, 21.04f }, { { GO_SM_CHAMBER_SEAL, 0, 0 } } },
        { 3, "Armory", 163, 316, { 1610.83f, -323.433f, 18.6738f, 6.28022f }, BOSS_HEROD,
            { 1595.f, 1995.f, -470.f, -295.f }, { 1608.65f, -308.97f, 20.78f }, { { GO_HERODS_DOOR, 0, 0 } } },
        { 4, "Cathedral", 164, 317, { 855.683f, 1321.5f, 18.6709f, 0.001747f }, BOSS_WHITEMANE,
            { 830.f, 1230.f, 1290.f, 1480.f }, { 853.679f, 1308.1f, 19.67f },
            { { GO_CHAPEL_DOOR, GO_HIGH_INQUISITOR_DOOR, 0 } } },
    } };

    constexpr FinderSection const* SectionByNumber(std::uint32_t number)
    {
        for (FinderSection const& s : kSections)
            if (s.number == number)
                return &s;
        return nullptr;
    }

    // The wing (section number 1-4) a position belongs to, 0 when in none of them.
    constexpr std::uint32_t WingOf(Vec2 p)
    {
        for (FinderSection const& s : kSections)
            if (s.wing.Contains(p))
                return s.number;
        return 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The wing portals (HUB ruling 2, section 7 #15 A; section 3.8): a clickable GO (301324, GODI 4711) spawned by the
    // instance when the end boss's slot is DONE (and restored from the slots on a reload); a use moves the user plus
    // every living group member within kPortalGroupRange who is out of combat to the next section's start. P1 stands in
    // the crypt, P1h on the lawn when Thalnos died in his hard mode (he dies on the lawn); no portal after Whitemane.
    // ----------------------------------------------------------------------------------------------------------------
    struct WingPortal
    {
        std::uint32_t id;           // 1 P1, 2 P1h, 3 P2, 4 P3 (DATA_GM_PORTAL's argument)
        char const* name;
        Point4 spot;
        std::uint32_t openSlot;     // the slot whose DONE opens it
        bool hardMode;              // P1h: only when the hard mode kill slot is DONE (P1 only when it is not)
        std::uint32_t toSection;
    };

    float constexpr kPortalGroupRange = 20.f;
    float constexpr kPortalScale = 0.45f;           // VR: GODI 4711 InstancePortal_Red at about 0.45 (S0's SQL)

    inline std::array<WingPortal, 4> constexpr kPortals{ {
        { 1, "P1", { 1807.2f, 1417.8f, -8.9f, 0.f }, BOSS_THALNOS, false, 2 },
        { 2, "P1h", { 1798.5f, 1348.5f, 18.6f, 0.f }, BOSS_THALNOS, true, 2 },
        { 3, "P2", { 138.0f, -429.2f, 18.6f, 0.f }, BOSS_DOAN, false, 3 },        // 10 yd off Doan's spawn
        { 4, "P3", { 1955.0f, -431.8f, 6.4f, 0.f }, BOSS_HEROD, false, 4 },      // 10 yd off Herod's spawn
    } };
    // A misclick while looting moves the group a wing away (no walk back): P2 / P3 stand at least this far from the
    // end boss's spawn (R-1-KIT m-3; NM: chamber floor at x 138, pit floor at x 1955).
    float constexpr kPortalBossClearance = 9.f;

    constexpr std::uint32_t PortalBit(std::uint32_t portalId)
    {
        return portalId >= 1 && portalId <= kPortals.size() ? 1u << (portalId - 1) : 0u;
    }

    constexpr WingPortal const* PortalById(std::uint32_t portalId)
    {
        for (WingPortal const& p : kPortals)
            if (p.id == portalId)
                return &p;
        return nullptr;
    }

    // Does another portal open on the same slot with the opposite hard mode flag (P1 / P1h)?
    constexpr bool PortalHasVariant(WingPortal const& portal)
    {
        for (WingPortal const& p : kPortals)
            if (p.id != portal.id && p.openSlot == portal.openSlot && p.hardMode != portal.hardMode)
                return true;
        return false;
    }

    // Which portals stand for these boss states (DATA_PORTALS). A portal with a hard mode variant stands only on its
    // side of the hard mode kill (P1 / P1h); a portal without one (P2 after the Heresy, P3 after the Call to Arms)
    // stands whenever its end boss is DONE.
    inline std::uint32_t PortalsOpenMask(std::array<std::uint32_t, kBossCount> const& states)
    {
        std::uint32_t mask = 0;
        for (WingPortal const& p : kPortals)
        {
            if (states[p.openSlot] != DungeonKit::State::Done)
                continue;
            std::uint32_t const killSlot = HardModeKillSlot(p.openSlot);
            bool const lit = killSlot < kBossCount && states[killSlot] == DungeonKit::State::Done;
            if (!PortalHasVariant(p) || p.hardMode == lit)
                mask |= PortalBit(p.id);
        }
        return mask;
    }

    // The portal standing nearest to a position (the portal GO finds its own role by where it stands).
    inline WingPortal const* PortalNear(Vec2 at, float within = 5.f)
    {
        WingPortal const* best = nullptr;
        float bestD = within;
        for (WingPortal const& p : kPortals)
        {
            float const d = DungeonKit::Distance(at, p.spot.XY());
            if (d <= bestD)
            {
                best = &p;
                bestD = d;
            }
        }
        return best;
    }

    // Who a portal use takes along (section 7 #15 A): the user and every group member within 20 yd, alive and out of
    // combat. ScarletMonasteryKit.cpp uses the kit's PortalTravel; this copy mirrors its rule for the host test.
    constexpr bool PortalTakesAlong(float distance, bool alive, bool inCombat)
    {
        return alive && !inCombat && distance <= kPortalGroupRange;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Completed-encounter bits (DungeonEncounter.dbc 444-450 verified 2026-11-20 for bits 0-6; FD-SM's new normal rows
    // 1074-1080 for bits 7-13, section 7 #3 A): bit -> boss state. Used to fill the slots of a stock save (stock never
    // wrote any) and by mod-dungeon-clear's wing masks.
    // ----------------------------------------------------------------------------------------------------------------
    inline std::array<std::pair<std::uint32_t, std::uint32_t>, kEncounterCount> constexpr kEncounterBits{ {
        { 0, BOSS_VISHAS }, { 1, BOSS_THALNOS }, { 2, BOSS_LOKSEY }, { 3, BOSS_DOAN }, { 4, BOSS_HEROD },
        { 5, BOSS_LAST_STAND }, { 6, BOSS_WHITEMANE }, { 7, BOSS_IRONSPINE }, { 8, BOSS_COUNCIL }, { 9, BOSS_KELL },
        { 10, BOSS_HOLLIS_GREY }, { 11, BOSS_CRELL }, { 12, BOSS_HALDEN }, { 13, BOSS_THORNE } } };
    std::uint32_t constexpr kStockDungeonEncounterFirstId = 444;    // 444 + bit for bits 0-6
    std::uint32_t constexpr kNewDungeonEncounterFirstId = 1074;     // 1074 + (bit - 7) for bits 7-13 (FD-SM)

    constexpr std::uint32_t DungeonEncounterIdOfBit(std::uint32_t bit)
    {
        return bit < kStockEncounterCount ? kStockDungeonEncounterFirstId + bit
            : kNewDungeonEncounterFirstId + (bit - kStockEncounterCount);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Instance rules (pure; the instance calls them, scarlet_monastery_test.cpp pins them)
    // ----------------------------------------------------------------------------------------------------------------

    // A slot no Load and no boss AI wrote is still TO_BE_DECIDED at the first Update. InstanceScript::SetBossState
    // treats TO_BE_DECIDED as "loading" (the first write is stored without SaveToDB and without the switch), so the
    // instance settles them to NOT_STARTED once (the BRS R-1-KIT K-m1 lesson).
    constexpr std::uint32_t SettledSlotState(std::uint32_t state)
    {
        return state == DungeonKit::State::ToBeDecided ? std::uint32_t(DungeonKit::State::NotStarted) : state;
    }

    // An attempt ended: IN_PROGRESS went back to NOT_STARTED or FAIL (a wipe or an evade).
    constexpr bool AttemptEnded(std::uint32_t before, std::uint32_t after)
    {
        return before == DungeonKit::State::InProgress
            && (after == DungeonKit::State::NotStarted || after == DungeonKit::State::Fail);
    }

    // GetData(1) / GetData(6) once wave 2 binds: the Cathedral pair as one stock value (IN_PROGRESS while the Last
    // Stand or Whitemane is; DONE when Whitemane is; else NOT_STARTED).
    constexpr std::uint32_t CathedralMirror(std::uint32_t lastStand, std::uint32_t whitemane)
    {
        if (whitemane == DungeonKit::State::Done)
            return DungeonKit::State::Done;
        if (lastStand == DungeonKit::State::InProgress || whitemane == DungeonKit::State::InProgress)
            return DungeonKit::State::InProgress;
        return DungeonKit::State::NotStarted;
    }

    // DATA_CATHEDRAL_STAGE: where the Cathedral pair stands (what a cold-loaded Mograine and Whitemane restore to).
    enum class CathedralStage : std::uint32_t
    {
        BeforeStand     = 0,    // Mograine at the altar, Whitemane behind her door
        StandRunning    = 1,    // the Last Stand is IN_PROGRESS
        Vigil           = 2,    // the Last Stand is DONE: Mograine fallen at the altar, Whitemane at her vigil
        Done            = 3,    // Whitemane is DONE
    };

    constexpr CathedralStage CathedralStageFor(std::uint32_t lastStand, std::uint32_t whitemane)
    {
        if (whitemane == DungeonKit::State::Done)
            return CathedralStage::Done;
        if (lastStand == DungeonKit::State::Done)
            return CathedralStage::Vigil;
        if (lastStand == DungeonKit::State::InProgress)
            return CathedralStage::StandRunning;
        return CathedralStage::BeforeStand;
    }

    // The Chapel Door starts the Last Stand (section 7 #14 A, #19 A): only once wave 2 binds, never after the
    // Ashbringer event, and only from NOT_STARTED / FAIL.
    constexpr bool LastStandStartAllowed(std::uint32_t lastStand, bool ashbringer, bool wave2Bound = kWave2Bound)
    {
        return wave2Bound && !ashbringer
            && (lastStand == DungeonKit::State::NotStarted || lastStand == DungeonKit::State::Fail);
    }

    // The crossing restart (section 7 #19 A): after a wipe the door stays open; a living player crossing the door line
    // starts the stand again. Armed only with the door open and slot 5 NOT_STARTED.
    constexpr bool CrossingRestartArmed(std::uint32_t lastStand, bool doorOpen, bool ashbringer,
        bool wave2Bound = kWave2Bound)
    {
        return wave2Bound && doorOpen && !ashbringer && lastStand == DungeonKit::State::NotStarted;
    }

    // The crossing line: a strip just inside the Chapel Door (x 1069.95 [db]; the nave starts at x 1073, the opening
    // is 9-10 yd: NM), 4 to 12 yd in, across the doorway. Somebody walking in passes it; somebody standing deeper in
    // the nave does not.
    float constexpr kCrossingMinX = 1074.f;
    float constexpr kCrossingMaxX = 1082.f;
    float constexpr kCrossingMinY = 1392.f;
    float constexpr kCrossingMaxY = 1406.f;
    float constexpr kCrossingMinZ = 28.f;
    float constexpr kCrossingMaxZ = 36.f;
    std::uint32_t constexpr kCrossingCheckMs = 1000;

    constexpr bool InCrossingLine(Vec2 p, float z)
    {
        return p.x >= kCrossingMinX && p.x <= kCrossingMaxX && p.y >= kCrossingMinY && p.y <= kCrossingMaxY
            && z >= kCrossingMinZ && z <= kCrossingMaxZ;
    }

    // Whitemane's slot opens only after the Last Stand is DONE (section 3.2 item 3): with wave 2 bound an IN_PROGRESS
    // or DONE write on slot 6 is refused while slot 5 is not DONE.
    constexpr bool WhitemaneWriteAccepted(std::uint32_t state, std::uint32_t lastStand, bool wave2Bound = kWave2Bound)
    {
        if (!wave2Bound)
            return true;
        if (state == DungeonKit::State::InProgress || state == DungeonKit::State::Done)
            return lastStand == DungeonKit::State::Done;
        return true;
    }

    // The Ashbringer event (section 7 #16 A): refused while any Cathedral slot fights (the Last Stand, Whitemane,
    // Thorne) or, while wave 2 is unbound, while the stock pair fights; once fired it plays as stock. Also refused
    // once the Last Stand is DONE while Whitemane lives (R-2-FW MN-3): the event would despawn her at her vigil and
    // slot 6 could never be earned.
    constexpr bool AshbringerAllowed(std::uint32_t lastStand, std::uint32_t whitemane, std::uint32_t thorne,
        std::uint32_t stockEncounter, bool wave2Bound = kWave2Bound)
    {
        if (lastStand == DungeonKit::State::InProgress || whitemane == DungeonKit::State::InProgress
            || thorne == DungeonKit::State::InProgress)
            return false;
        if (lastStand == DungeonKit::State::Done && whitemane != DungeonKit::State::Done)
            return false;
        return wave2Bound || stockEncounter != DungeonKit::State::InProgress;
    }

    // Herod's Door (section 7 #14 A, HB0): shut while Herod fights; open again on his death or a reset. The instance
    // acts on Open only: the close is D11's SealedArena (3 s after the pull with the stragglers pulled in, section 7
    // #22 A; the kit wants the door out of the instance's DoorData), which also reopens it on its Release.
    enum class DoorMove : std::uint8_t
    {
        None,
        Open,
        Close,
    };

    constexpr DoorMove HerodsDoorMoveFor(std::uint32_t before, std::uint32_t after)
    {
        if (after == DungeonKit::State::InProgress)
            return DoorMove::Close;
        if (after == DungeonKit::State::Done || AttemptEnded(before, after))
            return DoorMove::Open;
        return DoorMove::None;
    }

    // The lever does nothing (not selectable) while Herod fights.
    constexpr bool HerodsLeverUsable(std::uint32_t herod)
    {
        return herod != DungeonKit::State::InProgress;
    }

    // --- The hard mode triggers (section 3.7; bots never set one: SM1) ---------------------------------------------

    // The Desecration (D4H): four gravestones touched in the order Galvar, Fairbell, Voss, Goodchilde (0-3). Heroic,
    // out of combat (Thalnos neither fighting nor dead), not lit yet, and the council dead (section 7 #18 A: "the dead
    // are not yet at rest" while the council lives).
    std::uint32_t constexpr kDesecrationStones = 4;

    constexpr bool DesecrationTouchAllowed(bool heroic, std::uint32_t thalnos, std::uint32_t council, bool lit)
    {
        return heroic && !lit && thalnos != DungeonKit::State::InProgress && thalnos != DungeonKit::State::Done
            && council == DungeonKit::State::Done;
    }

    enum class DesecrationVerdict : std::uint32_t
    {
        None        = 0,    // fewer than four touches so far
        Right       = 1,    // the flag is set (saved): the stones glow red, Thalnos yells line 4 (D4H)
        Wrong       = 2,    // the order clears: three Haunting Phantasms rise (D4H); no try limit
        Refused     = 3,    // DesecrationTouchAllowed said no (D4H shows "the dead are not yet at rest")
        Repeat      = 4,    // a stone already touched this attempt (ignored)
    };

    constexpr DesecrationVerdict JudgeDesecration(std::array<std::uint32_t, kDesecrationStones> const& order)
    {
        for (std::uint32_t i = 0; i < kDesecrationStones; ++i)
            if (order[i] != i)
                return DesecrationVerdict::Wrong;
        return DesecrationVerdict::Right;
    }

    // The Heresy (D8H): four evidence pages read in any order, each once per instance. Heroic, Doan neither fighting
    // nor dead.
    std::uint32_t constexpr kDoanPages = 4;
    std::uint32_t constexpr kDoanPagesAll = (1u << kDoanPages) - 1;

    constexpr bool DoanPageAllowed(bool heroic, std::uint32_t doan, std::uint32_t mask, std::uint32_t page)
    {
        return heroic && page < kDoanPages && !(mask & (1u << page)) && doan != DungeonKit::State::InProgress
            && doan != DungeonKit::State::Done;
    }

    constexpr std::uint32_t DoanPagesRead(std::uint32_t mask)
    {
        std::uint32_t n = 0;
        for (std::uint32_t i = 0; i < kDoanPages; ++i)
            if (mask & (1u << i))
                ++n;
        return n;
    }

    // Call to Arms (D11H): a /taunt on Herod out of combat, heroic, wave 2 bound, Herod neither fighting nor dead.
    constexpr bool HerodTauntAllowed(bool heroic, std::uint32_t herod, bool lit, bool wave2Bound = kWave2Bound)
    {
        return heroic && wave2Bound && !lit && herod != DungeonKit::State::InProgress
            && herod != DungeonKit::State::Done;
    }

    // The Truth (D14H, section 7 #21 A): the Torch works on heroic only once the Last Stand is DONE and before
    // Whitemane is pulled.
    constexpr bool TorchAllowed(bool heroic, std::uint32_t lastStand, std::uint32_t whitemane, bool lit,
        bool wave2Bound = kWave2Bound)
    {
        return heroic && wave2Bound && !lit && lastStand == DungeonKit::State::Done
            && (whitemane == DungeonKit::State::NotStarted || whitemane == DungeonKit::State::Fail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas (the leash frames of the stubs; section 3.8). Each boss WP writes its final polygon from the NM hull after
    // the playtest's `.gps` walk (an arena stops 2 yd short of any drop: Herod's ledge, the altar steps).
    // ----------------------------------------------------------------------------------------------------------------
    inline ArenaRegion BoxRegion(float minX, float maxX, float minY, float maxY, float zMin, float zMax)
    {
        return ArenaRegion::Polygon({ { minX, minY }, { maxX, minY }, { maxX, maxY }, { minX, maxY } }, zMin, zMax);
    }

    inline ArenaRegion CircleRegion(Vec2 center, float radius, float zMin, float zMax)
    {
        return ArenaRegion::Circle(center, radius, zMin, zMax);
    }

    // Section 1. Vishas's H-shaped hall (box x 1740-1800, y 1098-1162, z 7-9.6: NM).
    inline Arena VishasArena() { return Arena(BoxRegion(1738.f, 1802.f, 1096.f, 1164.f, 4.f, 13.f)); }
    // Ironspine: the lawn home (40 yd disc, section 7 #24 A; D2's rev moved his spawn there), cut at y 1317 short of
    // the council (R-1-GY MN-3): the same 32-corner polygon as SmIronspine::FightArena() (IronspineLogic.h YardPolygon;
    // the host test keeps the two in step).
    float constexpr kIronspineYardNorthY = 1317.f;
    inline Arena IronspineArena()
    {
        std::uint32_t constexpr kCorners = 32;
        std::vector<Vec2> yard;
        yard.reserve(kCorners);
        for (std::uint32_t i = 0; i < kCorners; ++i)
        {
            float const bearing = DungeonKit::kTwoPi * static_cast<float>(i) / kCorners;
            Vec2 p = DungeonKit::Advance(kIronspineHome.XY(), bearing, 40.f);
            p.y = std::min(p.y, kIronspineYardNorthY);
            yard.push_back(p);
        }
        return Arena(ArenaRegion::Polygon(yard, 14.f, 26.f));
    }
    // The council's lawn: the 40 yd disc (section 7 #18 A) cut at y 1317, the yard's north edge, so a fight on the lawn
    // stays 31.5 yd from a living Ironspine's home (RF-1 m-4, the reverse half of R-1-GY MN-3). The bots' bounds
    // (30 yd round, y 1318.5 and up) stay inside the cut.
    float constexpr kCouncilLawnSouthY = kIronspineYardNorthY;
    inline ArenaRegion CouncilLawnRegion()
    {
        std::uint32_t constexpr kCorners = 32;
        std::vector<Vec2> lawn;
        lawn.reserve(kCorners);
        for (std::uint32_t i = 0; i < kCorners; ++i)
        {
            float const bearing = DungeonKit::kTwoPi * static_cast<float>(i) / kCorners;
            Vec2 p = DungeonKit::Advance(kCouncilLawn.XY(), bearing, 40.f);
            p.y = std::max(p.y, kCouncilLawnSouthY);
            lawn.push_back(p);
        }
        return ArenaRegion::Polygon(lawn, 15.f, 26.f);
    }
    // The council: the cut lawn (D3's rev moved both spawns there: SmCouncil::FightArena()).
    inline Arena CouncilArena() { return Arena(CouncilLawnRegion()); }
    // Thalnos's crypt (x 1801-1819, y 1400-1433 plus his nook, z -9.3 to -8: NM).
    inline Arena ThalnosArena() { return Arena(BoxRegion(1799.f, 1824.f, 1398.f, 1435.f, -12.f, -3.f)); }
    // The Desecration: the crypt and the lawn landing (section 7 #18 A: the council's cut lawn).
    inline Arena DesecrationArena()
    {
        return Arena(std::vector<ArenaRegion>{ BoxRegion(1799.f, 1824.f, 1398.f, 1435.f, -12.f, -3.f),
            CouncilLawnRegion() });
    }

    // Section 2. Loksey's alcove and its neck (x 119-152) and the kennel hall (x 155-208, y -240 to -310).
    inline Arena LokseyArena()
    {
        return Arena(std::vector<ArenaRegion>{ BoxRegion(117.f, 153.f, -267.f, -247.f, 15.f, 23.f),
            BoxRegion(153.f, 210.f, -312.f, -238.f, 15.f, 24.f) });
    }
    // Kell's long hall (x 212-278, y -300 to -349).
    inline Arena KellArena() { return Arena(BoxRegion(210.f, 280.f, -351.f, -298.f, 15.f, 25.f)); }
    // The reading hall (x 248-282, y -346 to -417).
    inline Arena HollisGreyArena() { return Arena(BoxRegion(246.f, 284.f, -419.f, -344.f, 15.f, 25.f)); }
    // Doan's chamber (x 129-167, y -409 to -449).
    inline Arena DoanArena() { return Arena(BoxRegion(127.f, 169.f, -451.f, -407.f, 15.f, 24.f)); }

    // Section 3. Crell's storeroom (two lobes and the neck, x 1742-1808, z 8; the south lobe reaches y -419: D9).
    inline Arena CrellArena() { return Arena(BoxRegion(1738.f, 1814.f, -424.f, -354.f, 5.f, 13.f)); }
    // Halden's three rooms and the two necks between them: the mesh boxes 1 yd wider, z 16-23 (D10's
    // SmHalden::RoomsArena(), HaldenLogic.h kWalkable; the host test keeps the two in step).
    inline Arena HaldenArena()
    {
        return Arena(std::vector<ArenaRegion>{ BoxRegion(1842.f, 1860.f, -438.f, -374.f, 16.f, 23.f),
            BoxRegion(1858.f, 1867.f, -392.f, -378.f, 16.f, 23.f),
            BoxRegion(1864.f, 1886.5f, -420.f, -374.f, 16.f, 23.f),
            BoxRegion(1884.f, 1893.f, -416.f, -402.f, 16.f, 23.f),
            BoxRegion(1891.f, 1912.f, -418.f, -356.f, 16.f, 23.f) });
    }
    // Herod's pit and ledge ring (radius 25.5 around the pit centroid) and the door spur. The spur starts 0.5 yd inside
    // Herod's Door (x 1933.69), so a straggler in the doorway or the cross hall counts as outside and the seal pulls
    // them in (R-2-ARM M-3, section 7 #22 A).
    float constexpr kHerodSpurMinX = 1934.2f;
    inline Arena HerodArena()
    {
        return Arena(std::vector<ArenaRegion>{ CircleRegion({ 1961.9f, -431.6f }, 27.f, 4.f, 20.f),
            BoxRegion(kHerodSpurMinX, 1953.f, -438.f, -425.f, 14.f, 21.f) });
    }

    // Section 4. Thorne's dry disc (section 7 #32 A).
    inline Arena ThorneArena() { return Arena(CircleRegion(kThorneSpot.XY(), 20.f, 15.f, 25.f)); }
    // The nave, the crossing and the altar platform (x 1073-1172, y 1333-1465, z 30-34).
    inline Arena LastStandArena() { return Arena(BoxRegion(1072.f, 1173.f, 1330.f, 1468.f, 28.f, 38.f)); }
    // Whitemane: the crossing and the platform (her vigil, section 7 #33 A) plus her chamber and its corridor.
    inline Arena WhitemaneArena()
    {
        return Arena(std::vector<ArenaRegion>{ BoxRegion(1072.f, 1173.f, 1330.f, 1468.f, 28.f, 38.f),
            BoxRegion(1172.f, 1218.f, 1382.f, 1416.f, 27.f, 34.f) });
    }

    // The arena of a boss state (a hard mode slot: its boss's, the Desecration's includes the lawn).
    inline Arena ArenaFor(std::uint32_t bossId)
    {
        switch (bossId)
        {
            case BOSS_VISHAS:           return VishasArena();
            case BOSS_IRONSPINE:        return IronspineArena();
            case BOSS_COUNCIL:          return CouncilArena();
            case BOSS_THALNOS:          return ThalnosArena();
            case BOSS_DESECRATION:      return DesecrationArena();
            case BOSS_LOKSEY:           return LokseyArena();
            case BOSS_KELL:             return KellArena();
            case BOSS_HOLLIS_GREY:      return HollisGreyArena();
            case BOSS_DOAN:
            case BOSS_HERESY:           return DoanArena();
            case BOSS_CRELL:            return CrellArena();
            case BOSS_HALDEN:           return HaldenArena();
            case BOSS_HEROD:
            case BOSS_CALL_TO_ARMS:     return HerodArena();
            case BOSS_THORNE:           return ThorneArena();
            case BOSS_LAST_STAND:       return LastStandArena();
            case BOSS_WHITEMANE:
            case BOSS_THE_TRUTH:        return WhitemaneArena();
            default:                    return Arena();
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string: header "SCR" (neither a prefix of the stock "SM" nor prefixed by it: the Stratholme
    // "SR" lesson), the 18 boss states, then the extras below. The stock save (instance_scarlet_monastery.cpp at
    // b70b14ed6: SetHeaders("SM"), no boss states, no data: "S M") reads as an empty run; the completed-encounter mask
    // (set before Load, from the DBC bits) fills the slots stock never wrote. Not saved (per attempt): the Desecration
    // touch order, the Last Stand's progress, the private Horseman field, the GM portals.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "SCR";
    char constexpr kStockSaveHeader[] = "SM";

    enum SaveExtra : std::size_t
    {
        EXTRA_DESECRATION       = 0,    // Thalnos's hard mode answered
        EXTRA_DOAN_PAGES        = 1,    // the pages read (bit = page)
        EXTRA_HERESY            = 2,    // all four read: Doan's hard mode lit
        EXTRA_HEROD_TAUNTED     = 3,
        EXTRA_TORCH_PULLED      = 4,
        EXTRA_ASHBRINGER        = 5,    // the Ashbringer event ran (GetData(2) stays non-zero, the door stays open)
    };
    std::size_t constexpr kSaveExtraCount = 6;

    struct SmSave
    {
        std::array<std::uint32_t, kBossCount> states{};
        std::uint32_t desecration = 0;
        std::uint32_t doanPages = 0;
        std::uint32_t heresy = 0;
        std::uint32_t herodTaunted = 0;
        std::uint32_t torchPulled = 0;
        std::uint32_t ashbringer = 0;
    };

    inline std::string FormatSmSave(SmSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_DESECRATION] = s.desecration;
        extras[EXTRA_DOAN_PAGES] = s.doanPages;
        extras[EXTRA_HERESY] = s.heresy;
        extras[EXTRA_HEROD_TAUNTED] = s.herodTaunted;
        extras[EXTRA_TORCH_PULLED] = s.torchPulled;
        extras[EXTRA_ASHBRINGER] = s.ashbringer;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // The boss states a completed-encounter mask records (DONE), OR-ed into `states`.
    inline void ApplyEncounterMask(std::uint32_t mask, std::array<std::uint32_t, kBossCount>& states)
    {
        for (auto const& [bit, boss] : kEncounterBits)
            if (mask & (1u << bit))
                states[boss] = DungeonKit::State::Done;
    }

    // The flags go back to 0 / 1, the pages to their four bits, the Heresy to "all four read", and a hard mode kill
    // slot needs its boss DONE.
    inline void SanitizeSmSave(SmSave& s)
    {
        s.desecration = s.desecration ? 1 : 0;
        s.doanPages &= kDoanPagesAll;
        s.heresy = s.doanPages == kDoanPagesAll ? 1 : 0;
        s.herodTaunted = s.herodTaunted ? 1 : 0;
        s.torchPulled = s.torchPulled ? 1 : 0;
        s.ashbringer = s.ashbringer ? 1 : 0;
        for (std::uint32_t slot = BOSS_DESECRATION; slot <= BOSS_THE_TRUTH; ++slot)
            if (s.states[HardModeBoss(slot)] != DungeonKit::State::Done)
                s.states[slot] = DungeonKit::State::NotStarted;
    }

    // The stock save: "S M" and nothing after it (no boss states, no data). False on anything else.
    inline bool ReadStockSave(std::string const& in)
    {
        std::vector<std::uint32_t> fields;
        return DungeonKit::ReadSaveFields(in, kStockSaveHeader, 0, 0, fields);
    }

    // Reads this script's "S C R" string, or the stock "S M"; `encounterMask` is the instance's completed-encounter
    // mask (applied to a stock save only: an "S C R" save carries its own states). False on anything else (ignored).
    inline bool ParseSmSave(std::string const& in, SmSave& out, std::uint32_t encounterMask = 0)
    {
        out = SmSave{};
        DungeonKit::StateSave raw;
        bool stock = false;
        DungeonKit::LegacySaveReader const legacy = [&stock, encounterMask](std::string const& s,
            DungeonKit::StateSave& o)
        {
            if (!ReadStockSave(s))
                return false;
            std::array<std::uint32_t, kBossCount> states{};
            ApplyEncounterMask(encounterMask, states);
            o.states.assign(states.begin(), states.end());
            stock = true;
            return true;
        };
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw, legacy))
            return false;
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        if (!stock)
        {
            out.desecration = raw.extras[EXTRA_DESECRATION];
            out.doanPages = raw.extras[EXTRA_DOAN_PAGES];
            out.heresy = raw.extras[EXTRA_HERESY];
            out.herodTaunted = raw.extras[EXTRA_HEROD_TAUNTED];
            out.torchPulled = raw.extras[EXTRA_TORCH_PULLED];
            out.ashbringer = raw.extras[EXTRA_ASHBRINGER];
        }
        SanitizeSmSave(out);
        return true;
    }
}

#endif
