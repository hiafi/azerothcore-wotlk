/*
 * mod-dungeon-bosses, Blackrock Depths D17:
 * The Grim Guzzler room: the patrons, Ribbly Screwspigot and Plugger Spazzring, the pure, host-testable part (no engine
 * headers). Build spec SP 66-216, 428-435, 635-641 (docs/dungeons/blackrock-depths-4-imperial-seat.md, rulings 61-69),
 * handoff section 3.5 row D17 and section 3.6. Tested by tests/brd_guzzler_test.cpp.
 *
 * The room has no C++ script: Ribbly (9543), his Cronies (10043), Plugger (9499) and the 68 patrons (9545, 9547, 9554)
 * stay on stock SmartAI, edited by data (rev_guzzler_blackrock_depths.sql: five rows; guzzler.py: two spell copies and
 * the creature columns). This header is the one place their numbers live, and the bar state machine D18 (Hurley) and
 * D19 (Phalanx) build on:
 *
 *   Spells         211410 Gouge (2 s incapacitate), 211411 Kick (3 s lockout): copies of the stock spells, rule 15
 *   Tuning         health, DamageModifier and the SmartAI repeat windows of the room (ruling 65, 62, 69)
 *   Predicates     who joins which trigger, by entry and distance (the SmartAI target rows, re-implemented)
 *   BarModel       the bar event as a state machine: the six triggers, what each one makes hostile, wakes or opens,
 *                  and how Plugger, the patrons, Hurley, Ribbly, Rocknot's ale run, the love potion and Phalanx fit
 *                  together. D18 keeps `KegUsed` -> Hurley, D19 keeps `RequestPhalanxActivation` and the door rule.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_GUZZLER_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_GUZZLER_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <cmath>
#include <cstdint>

namespace BrdGuzzler
{
    using BlackrockDepthsRework::BarDoor;
    using DungeonKit::NH;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsGuzzler;

    enum GuzzlerSpells : std::uint32_t
    {
        SPELL_GZ_GOUGE      = kSpellSlice.first + 0,    // 211410 Ribbly's Gouge: 20 Physical + the 2 s incapacitate
        SPELL_GZ_KICK       = kSpellSlice.first + 1,    // 211411 the Grim Patron's Kick: Physical + the 3 s lockout
        // 211412-211429 spare
    };
    static_assert(SPELL_GZ_KICK <= kSpellSlice.last, "the D17 spells must stay in their slice");

    // The stock spells the room's SmartAI keeps casting (no copy: the spec changes only their repeat windows, and
    // Plugger's Shadow Bolt takes the heroic version through DD's SpellDifficulty swap 12739 -> 15472).
    inline constexpr std::uint32_t SPELL_STOCK_GOUGE = 12540;               // swapped for SPELL_GZ_GOUGE on 9543
    inline constexpr std::uint32_t SPELL_STOCK_KICK = 15610;                // swapped for SPELL_GZ_KICK on 9545
    inline constexpr std::uint32_t SPELL_STOCK_HAMSTRING = 9080;            // Ribbly, kept
    inline constexpr std::uint32_t SPELL_STOCK_EVISCERATE = 15692;          // the Cronies, kept
    inline constexpr std::uint32_t SPELL_STOCK_SINISTER_STRIKE = 15581;     // the Cronies, kept
    inline constexpr std::uint32_t SPELL_STOCK_CURSE_OF_TONGUES = 13338;    // Plugger, kept
    inline constexpr std::uint32_t SPELL_STOCK_IMMOLATE = 12742;            // Plugger, kept
    inline constexpr std::uint32_t SPELL_STOCK_PLUGGER_SHADOW_BOLT = 12739; // Plugger, repeat 8-10 s
    inline constexpr std::uint32_t SPELL_STOCK_DEMON_ARMOR = 13787;         // Plugger, kept
    inline constexpr std::uint32_t SPELL_STOCK_CURSE_OF_AGONY = 14868;      // the Guzzling Patron, kept
    inline constexpr std::uint32_t SPELL_STOCK_PATRON_SHADOW_BOLT = 20825;  // the Guzzling Patron, repeat 8-10 s
    inline constexpr std::uint32_t SPELL_STOCK_BACKHAND = 6253;             // the Hammered Patron, repeat 10-12 s
    inline constexpr std::uint32_t SPELL_STOCK_DRUNKEN_RAGE = 14822;        // the three patrons, kept

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (every number of the room; the build spec's tables and the stock rows they change)
    // ----------------------------------------------------------------------------------------------------------------

    // Class bases at 5 players (creature_classlevelstats basehp0, live 2026-11-17): health = base x HealthModifier.
    inline constexpr std::uint32_t kBaseWarrior50 = 2215;   // the patrons' and the Cronies' middle level (48-52)
    inline constexpr std::uint32_t kBaseMage50 = 1551;      // the Guzzling Patron (class 8)
    inline constexpr std::uint32_t kBaseWarrior53 = 2453;   // Ribbly
    inline constexpr std::uint32_t kBasePaladin55 = 2091;   // Plugger (class 2)

    inline constexpr std::uint32_t HealthOf(std::uint32_t classBase, float healthModifier)
    {
        return static_cast<std::uint32_t>(std::lround(static_cast<double>(classBase) * healthModifier));
    }

    // Ribbly 9543, his Cronies 10043 and Plugger 9499: the health at 5 players, normal and heroic (SP 417-420, 624-628;
    // the heroic numbers are WP-H's `_boss` / `dict(health=...)` overrides in
    // source/world/dungeons/blackrock_depths.py).
    inline constexpr NH<std::uint32_t> kRibblyHealth{ 40000, 60000 };
    inline constexpr NH<std::uint32_t> kRibblyCronyHealth{ 6000, 9000 };
    inline constexpr NH<std::uint32_t> kPluggerHealth{ 40000, 60000 };
    // The normal rows' HealthModifier (guzzler.py GUZZLER_CREATURE_COLUMNS): 40,000 / 2,453, 6,000 / 2,215 (the Cronies
    // are level 48-52: 5,586 to 6,423 at the ends), 40,000 / 2,091.
    inline constexpr float kRibblyHealthModifier = 16.307f;
    inline constexpr float kRibblyCronyHealthModifier = 2.709f;
    inline constexpr float kPluggerHealthModifier = 19.13f;

    // The patrons (ruling 65, both difficulties: they run their normal rows on heroic, no heroic template).
    inline constexpr float kPatronDamageModifier = 1.5f;            // stock 3.5, all three
    inline constexpr float kStockPatronDamageModifier = 3.5f;
    inline constexpr float kGrimPatronHealthModifier = 0.6f;        // stock 1: about 2,200 -> 1,300
    inline constexpr float kGuzzlingPatronHealthModifier = 0.6f;    // stock 1: about 1,550 -> 930
    inline constexpr float kHammeredPatronHealthModifier = 1.5f;    // stock 3: about 6,650 -> 3,300
    inline constexpr float kStockGrimPatronHealthModifier = 1.0f;
    inline constexpr float kStockGuzzlingPatronHealthModifier = 1.0f;
    inline constexpr float kStockHammeredPatronHealthModifier = 3.0f;

    // The room's crowd (live 2026-11-17, creature rows of map 230).
    inline constexpr std::uint32_t kGrimPatrons = 28;
    inline constexpr std::uint32_t kGuzzlingPatrons = 28;
    inline constexpr std::uint32_t kHammeredPatrons = 12;
    inline constexpr std::uint32_t kPatronCount = kGrimPatrons + kGuzzlingPatrons + kHammeredPatrons;
    static_assert(kPatronCount == 68, "the spec's 68 patrons");

    // A SmartAI repeat window (event_param3 / event_param4, ms).
    struct Window
    {
        std::uint32_t min;
        std::uint32_t max;
        constexpr bool operator==(Window const&) const = default;
    };
    // Plugger's and the Guzzling Patron's Shadow Bolt (ruling 65 / 69): 3-4 s -> 8-10 s.
    inline constexpr Window kShadowBoltRepeat{ 8000, 10000 };
    inline constexpr Window kStockShadowBoltRepeat{ 3000, 4000 };
    // The Hammered Patron's Backhand (ruling 65): 5-8 s -> 10-12 s.
    inline constexpr Window kBackhandRepeat{ 10000, 12000 };
    inline constexpr Window kStockBackhandRepeat{ 5000, 8000 };
    // The Grim Patron's Kick fires from an AREA_CASTING event, 25% a fire, first 3-5 s, repeat 5-8 s: unchanged.
    inline constexpr Window kKickRepeat{ 5000, 8000 };
    // Ribbly's Gouge: first at 3 s, repeat 10 s: unchanged (the 2 s rule is the incapacitate, below).
    inline constexpr std::uint32_t kGougeRepeatMs = 10000;

    // The two copied spells' durations (ruling 62 / 65): the incapacitate 4 s -> 2 s, the Kick lockout 6 s -> 3 s.
    inline constexpr std::uint32_t kGougeIncapacitateMs = 2000;
    inline constexpr std::uint32_t kStockGougeIncapacitateMs = 4000;
    inline constexpr std::uint32_t kKickLockoutMs = 3000;
    inline constexpr std::uint32_t kStockKickLockoutMs = 6000;

    // Immunity sets (creature_immunities): stock -251 (Ribbly) and -324 (Plugger: every CC mechanic AND the interrupt)
    // become the kit's 1972 on both normal rows (STAGE-H report 7 item 3): stun immune, interruptible.
    inline constexpr std::int32_t kStockRibblyImmunity = -251;
    inline constexpr std::int32_t kStockPluggerImmunity = -324;
    inline constexpr std::uint32_t kBossImmunity = 1972;

    // ----------------------------------------------------------------------------------------------------------------
    // Triggers, by entry and distance (the stock SmartAI target rows)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kTheftThreshold = 3;         // Plugger's counter1 at 3 runs actionlist 949900
    inline constexpr float kTheftJoinRange = 7.f;               // patrons within this of Plugger attack with him
    inline constexpr float kDeathHostileRange = 100.f;          // his death: faction 14 on the crowd and Phalanx
    inline constexpr float kRibblyGossipRange = 30.f;           // the gossip: faction 14 on his Cronies
    inline constexpr std::uint32_t kRibblyGossipMenu = 1970;
    inline constexpr std::uint32_t kFactionAllHostile = 14;     // the stock rows' faction (monster)
    inline constexpr std::uint32_t kKegsToWakeHurley = 3;       // the third Thunderbrew Lager Keg wakes Hurley
    inline constexpr std::uint32_t kAleTurnInsForTheRun = 3;    // Rocknot's quest 4295: the third turn-in starts it
    // Live counts of the theft sources (re-queried 2026-11-17, handoff section 8 #27; the spec says 8 and 3, FS 6
    // and 2).
    inline constexpr std::uint32_t kLiveMugSpawns = 6;          // Dark Iron Ale Mug 165738
    inline constexpr std::uint32_t kLiveBoarSpawns = 2;         // Grim Guzzler Boar 165739
    static_assert(kLiveMugSpawns + kLiveBoarSpawns >= kTheftThreshold, "the counter must be reachable");

    // Plugger's actionlist 949900: the patrons within kTheftJoinRange that join (not the Hammered ones).
    constexpr bool JoinsTheft(std::uint32_t entry, float distanceToPlugger)
    {
        return (entry == BlackrockDepthsRework::NPC_GRIM_PATRON || entry == BlackrockDepthsRework::NPC_GUZZLING_PATRON)
            && distanceToPlugger <= kTheftJoinRange;
    }

    // Plugger's death (SmartAI 9499 ids 9-12): faction 14 on all three patrons and on Phalanx within 100 yd.
    constexpr bool TurnsHostileOnPluggerDeath(std::uint32_t entry, float distanceToPlugger)
    {
        return (entry == BlackrockDepthsRework::NPC_GRIM_PATRON || entry == BlackrockDepthsRework::NPC_GUZZLING_PATRON
                || entry == BlackrockDepthsRework::NPC_HAMMERED_PATRON || entry == BlackrockDepthsRework::NPC_PHALANX)
            && distanceToPlugger <= kDeathHostileRange;
    }

    // Ribbly's gossip (SmartAI 9543 ids 0-3): Ribbly and the Cronies within 30 yd of him turn hostile.
    constexpr bool JoinsRibblyGossip(std::uint32_t entry, float distanceToRibbly)
    {
        return entry == BlackrockDepthsRework::NPC_RIBBLYS_CRONY && distanceToRibbly <= kRibblyGossipRange;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bar event as a state machine (spec "The bar event as a state machine", SP 109-216)
    //
    // One model of the room's state; every method is one trigger. The real units keep their own rules (SmartAI rows,
    // Rocknot's and Nagmara's stock scripts, the instance's TYPE_BAR / love potion fields); this model says what the
    // whole must do, so D18 (Hurley) and D19 (Phalanx) can test their half against the others.
    //
    //   Theft          3 loots of a Dark Iron Ale Mug / Grim Guzzler Boar: Plugger fights, JoinsTheft patrons attack
    //   PluggerDied    faction 14 on every TurnsHostileOnPluggerDeath unit: the room is hostile, Phalanx is requested
    //   KegUsed        the third Thunderbrew Lager Keg wakes Hurley (SetData 1,1; he and the Cronies walk out)
    //   RibblyGossip   menu 1970 option 0: Ribbly and the JoinsRibblyGossip Cronies hostile
    //   AleTurnIn      quest 4295 at Rocknot: the third starts the escort; AleEscortEnds: bar DONE, Phalanx requested
    //   LovePotion     Nagmara's event: bar DONE, the door opens, Phalanx stays dormant (the stock quirk)
    //   Phalanx        Dormant -> MovingToDoor (once; three sources, the gossip one new in D19) -> Active -> Dead
    //   Door           BarDoorState(love potion DONE, bar, Phalanx dead): Phalanx's death opens it (ruling 66)
    // ----------------------------------------------------------------------------------------------------------------

    enum class PluggerState : std::uint8_t
    {
        Idle,           // behind the counter, vendor and questgiver flags on
        Fighting,       // the theft counter reached 3 (flags off while in combat)
        Dead,
    };

    enum class PatronMood : std::uint8_t
    {
        Calm,           // faction 674, ambient emotes
        NearPlugger,    // the Grim and Guzzling patrons within 7 yd of him attack (theft)
        WholeRoom,      // all 68 patrons within 100 yd faction 14 (his death)
    };

    enum class HurleyState : std::uint8_t
    {
        Hidden,         // invisible, passive, unit flags 320 (the stock rest state)
        Awake,          // the third keg: visible, walks out, passive until struck
    };

    enum class PhalanxState : std::uint8_t
    {
        Dormant,        // faction 35 in his corner
        MovingToDoor,   // activation requested: the 2-node walk (path 95020), 15 s watchdog
        Active,         // faction 54, at the door, fights
        Dead,
    };

    // The three requests that wake Phalanx: Rocknot's ale run (DoAction ACTION_PHALANX_START_ACTIVATION), Plugger's
    // death (his faction 14, seen in Phalanx's UpdateAI) and, new in D19, the gossip option.
    enum class PhalanxRequest : std::uint8_t
    {
        AleRun,
        PluggerDeath,
        Gossip,
    };

    struct BarModel
    {
        // The state, all of it (what the instance saves is bar, lovePotion and phalanxActivated).
        std::uint32_t theftCount = 0;                   // Plugger's counter1, 0-2 (3 runs the actionlist and resets it)
        PluggerState plugger = PluggerState::Idle;
        PatronMood patrons = PatronMood::Calm;
        std::uint32_t kegsUsed = 0;
        HurleyState hurley = HurleyState::Hidden;
        bool ribblyHostile = false;                     // Ribbly and the Cronies near him
        std::uint32_t bar = DungeonKit::State::NotStarted;      // TYPE_BAR: NOT_STARTED, IN_PROGRESS, DONE
        std::uint32_t aleTurnIns = 0;                   // BarAleCount, 0-3
        bool aleEscortRunning = false;                  // Rocknot walking to the kegs
        std::uint32_t lovePotion = DungeonKit::State::NotStarted;   // DATA_LOVE_POTION_EVENT
        PhalanxState phalanx = PhalanxState::Dormant;
        bool phalanxActivated = false;                  // DATA_PHALANX_ACTIVATED (saved: a reload skips the walk)

        // Third Dark Iron Ale Mug / Grim Guzzler Boar loot (SmartAI 165738 / 165739 -> Plugger event 6-8).
        // Returns true when this loot was the third one (Plugger attacks, the near patrons join).
        constexpr bool Theft()
        {
            if (plugger == PluggerState::Dead)
                return false;
            if (++theftCount < kTheftThreshold)
                return false;
            theftCount = 0;
            plugger = PluggerState::Fighting;
            if (patrons == PatronMood::Calm)
                patrons = PatronMood::NearPlugger;
            return true;
        }

        // Plugger dies (SmartAI 9499 ids 9-12): the whole room, and Phalanx through his faction.
        constexpr void PluggerDied()
        {
            plugger = PluggerState::Dead;
            patrons = PatronMood::WholeRoom;
            RequestPhalanxActivation(PhalanxRequest::PluggerDeath);
        }

        // A Thunderbrew Lager Keg is used (SmartAI 164911 id 0 / 1): the third wakes Hurley. Returns true on that one.
        constexpr bool KegUsed()
        {
            if (hurley == HurleyState::Awake)
                return false;
            if (++kegsUsed < kKegsToWakeHurley)
                return false;
            hurley = HurleyState::Awake;
            return true;
        }

        // Gossip menu 1970 option 0 on Ribbly.
        constexpr void RibblyGossip() { ribblyHostile = true; }

        // A turn-in of quest 4295 at Rocknot. It counts only while nothing else owns the bar: not after the love
        // potion, not once the run is DONE, not while he is walking (the stock sQuestReward guards). Returns true when
        // this turn-in starts the escort (the third).
        constexpr bool AleTurnIn()
        {
            if (lovePotion == DungeonKit::State::Done || bar == DungeonKit::State::Done || aleEscortRunning)
                return false;
            if (bar == DungeonKit::State::NotStarted)
                bar = DungeonKit::State::InProgress;
            if (++aleTurnIns < kAleTurnInsForTheRun)
                return false;
            aleEscortRunning = true;
            return true;
        }

        // The escort's last keg breaks and, 7 s later, the trap lands on Rocknot: TYPE_BAR DONE, Phalanx requested.
        // (The Bar Door itself is blasted at the keg, 7 s earlier: BarDoorState follows the saved DONE.)
        constexpr void AleEscortEnds()
        {
            if (!aleEscortRunning)
                return;
            aleEscortRunning = false;
            bar = DungeonKit::State::Done;
            RequestPhalanxActivation(PhalanxRequest::AleRun);
        }

        // Nagmara's love potion event completes. Needs the bar NOT_STARTED or IN_PROGRESS and Rocknot free (stock
        // DATA_CAN_START_LOVE_POTION); returns whether it ran. It never wakes Phalanx.
        constexpr bool LovePotion()
        {
            if ((bar != DungeonKit::State::NotStarted && bar != DungeonKit::State::InProgress) || aleEscortRunning)
                return false;
            lovePotion = DungeonKit::State::Done;
            bar = DungeonKit::State::Done;
            return true;
        }

        // Phalanx wakes: once, from Dormant (the saved flag is set at the request). Returns whether it started.
        constexpr bool RequestPhalanxActivation(PhalanxRequest)
        {
            if (phalanx != PhalanxState::Dormant)
                return false;
            phalanx = PhalanxState::MovingToDoor;
            phalanxActivated = true;
            return true;
        }

        // His walk ends (or the 15 s watchdog): faction 54, aggressive, home at the door.
        constexpr void PhalanxArrived()
        {
            if (phalanx == PhalanxState::MovingToDoor)
                phalanx = PhalanxState::Active;
        }

        constexpr void PhalanxDied() { phalanx = PhalanxState::Dead; }

        constexpr BarDoor Door() const
        {
            return BlackrockDepthsRework::BarDoorState(
                lovePotion == DungeonKit::State::Done, bar, phalanx == PhalanxState::Dead);
        }
    };

    // Phalanx's state after a reload (stock Reset: DONE goes straight to Active at the door; the instance opens the
    // Bar Door on load from the same fields): dead wins, then the saved activation, else dormant.
    constexpr PhalanxState PhalanxAfterReload(bool phalanxActivated, bool phalanxDead)
    {
        if (phalanxDead)
            return PhalanxState::Dead;
        return phalanxActivated ? PhalanxState::Active : PhalanxState::Dormant;
    }
}

#endif
