/*
 * mod-dungeon-bosses, Blackrock Spire B4:
 * Mother Smolderweb (10596), the pure, host-testable part (no engine headers). Build spec: docs/dungeons/
 * blackrock-spire-rework.md "Mother Smolderweb" (SP 1231-1469, SW1-SW10, rulings 33-36, 63-64), handoff section 3.4
 * rows SW, 3.5 row B4, 3.6, 3.8 (her cave and its eight egg spots). Tested by tests/brs_smolderweb_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsSmolderweb (210120-210149), declared in apps/dbc-tools
 *                 source/npcs/blackrock_spire/smolderweb.py
 *   Tuning        NH<> percents, FlexAB counts and the cadences, straight from the build spec
 *   Eggs          SW1 / SW2 the eight starting spots (with their floor heights), the safety cap, the arm and grace
 *   BeatClock     a repeating beat on the AI's own ms clock (lay, milk, spray, brood call, bite)
 *   Broodlings    SW3 where the three spawn, whom they go for (the most Venom, else the hatcher)
 *   Brood Call    SW7 which eggs the call hatches, onto whom
 *   Tank hold     SW7 the park spot that keeps every egg out of the call's 15 yd
 *   Last Milk     SW8 who gets the stock quest aura
 *   Widow's Bite  SW10 the taunt swap numbers and the proof that the debuff falls off in time
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_SMOLDERWEB_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_SMOLDERWEB_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrsSmolderweb
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsSmolderweb;

    enum SmolderwebSpells : std::uint32_t
    {
        SPELL_SW_SPRAY_CAST     = kSpellSlice.first + 0,    // 210120 SW6 the 2 s rear-up (cast bar, Frost)
        SPELL_SW_SPRAY          = kSpellSlice.first + 1,    // 210121 SW6 the cone's hit (resolve copy, Frost)
        SPELL_SW_ENCASED        = kSpellSlice.first + 2,    // 210122 SW6 the 2 s stun of a cone hit (the rider)
        SPELL_SW_EGG_HATCH      = kSpellSlice.first + 3,    // 210123 SW1 / SW2 / SW3 a hatched egg's hit (resolve copy)
        SPELL_SW_MILK           = kSpellSlice.first + 4,    // 210124 SW4 the splash's hit (resolve copy, Nature)
        SPELL_SW_MILK_LOOK      = kSpellSlice.first + 5,    // 210125 SW4 / SW8 the spat missile to a point (look only)
        SPELL_SW_VENOM          = kSpellSlice.first + 6,    // 210126 SW5 Venom, up to 5 stacks (normal)
        SPELL_SW_VENOM_HEROIC   = kSpellSlice.first + 7,    // 210127 SW5 Venom, up to 8 stacks (heroic)
        SPELL_SW_WIDOWS_BITE    = kSpellSlice.first + 8,    // 210128 SW10 Widow's Bite (10 players), no stack cap
        SPELL_SW_BROOD_CALL     = kSpellSlice.first + 9,    // 210129 SW7 the 3 s chitter (cast bar, heroic)
        SPELL_SW_HATCH_LOOK     = kSpellSlice.first + 10,   // 210130 SW3 / SW7 the burst where an egg hatches (look)
        // 210131-210149 spare
    };
    static_assert(SPELL_SW_HATCH_LOOK <= kSpellSlice.last, "Smolderweb's spells must stay in her slice");

    // Stock spells and the quest, kept (SW8): Mother's Milk 16468 is only given at her death, to the quest 4866
    // holders; Summon Spire Spiderling 16103 is the stock death cast (the S0 SQL rev dropped its SmartAI row).
    inline constexpr std::uint32_t SPELL_SW_QUEST_MILK = 16468;
    inline constexpr std::uint32_t SPELL_SW_DEATH_SPIDERLINGS = 16103;
    inline constexpr std::uint32_t kQuestRaggedJohn = 4866;     // the gossip's QUESTTAKEN (menu 2061)

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum SmolderwebTags : std::uint32_t
    {
        TAG_SW_EGG      = 1,    // SW1 / SW2 an egg's Mine
        TAG_SW_LAY      = 2,    // SW2 the lay marker that follows its player (telegraph only)
        TAG_SW_MILK     = 4,    // SW4 the splash
        TAG_SW_SPRAY    = 6,    // SW6 the cone
        TAG_SW_CARRY    = 7,    // SW2 (heroic) the bots' carry-it-clear hint (never hurts)
        TAG_SW_PARK     = 10,   // SW7 the tank hold off the eggs (heroic, bots only)
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_mother_smolderweb_blackrock_spire.sql, SP "Text").
    enum SmolderwebTexts : std::uint8_t
    {
        TEXT_LAY_EGG    = 0,    // emote: "%s lays her eggs!"
        TEXT_BROOD_CALL = 1,    // emote (heroic): "%s calls to her brood!"
        TEXT_LAST_MILK  = 2,    // emote: "%s spits her last milk across the cave!"
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP "Build spec"; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // SW1 / SW2 The Clutch: every egg is a registry Mine, 4 yd, with a 0.5 s grace. A player who stays inside it
    // hatches it: 20% (heroic 25%) Nature + Weakened, and 3 Broodlings burst out onto them. Eggs stay (ruling 34): no
    // cap, no timer, they are only ever hatched by a step. DEVIATION: the SP says "armed at once"; a laid egg drops
    // where its player stands, and a Mine that is armed with anyone inside goes off at once, so the egg arms after
    // kEggArmMs (the telegraph shows its outline and growing fill meanwhile): time to step out, never to rest in it.
    inline constexpr float kEggRadius = 4.f;
    inline constexpr std::uint32_t kEggArmMs = 1500;
    inline constexpr std::uint32_t kEggGraceMs = 500;
    inline constexpr NH<float> kEggPct{ 20.f, 25.f };
    inline constexpr std::uint32_t kEggLifeSecs = 1800;         // the object's own timed despawn (a backstop)
    // The registry holds 256 mechanics per map (BossMechanics.MaxActivePerMap): with this many eggs alive on the floor
    // she lays no more until some hatch (about 40 minutes at 10 players), so the milk and the cone still register.
    inline constexpr std::size_t kEggSafetyCap = 150;

    // The eight starting spots (NM 4, z >= 7 floor, clearance >= 5, >= 16 yd from her): the xy are S0's
    // kSmolderwebEggSpots, the floor heights NM 4's table.
    inline constexpr std::size_t kClutchCount = 8;
    inline constexpr std::array<float, kClutchCount> kClutchZ{ { 11.5f, 12.1f, 8.3f, 7.8f, 8.9f, 8.6f, 7.5f, 8.1f } };
    static_assert(BlackrockSpireRework::kSmolderwebEggSpots.size() == kClutchCount, "the clutch is eight eggs");

    constexpr Point3 ClutchSpot(std::size_t index)
    {
        std::size_t const i = index % kClutchCount;
        return { BlackrockSpireRework::kSmolderwebEggSpots[i].x, BlackrockSpireRework::kSmolderwebEggSpots[i].y,
                 kClutchZ[i] };
    }

    // The floor under an egg: the map's height when it is a floor near the measured one, else the measured one.
    inline float EggZ(float measuredZ, float mapZ, bool mapValid)
    {
        constexpr float kMaxDriftYd = 3.f;
        if (!mapValid || std::fabs(mapZ - measuredZ) > kMaxDriftYd)
            return measuredZ;
        return mapZ;
    }

    // SW2 Lay Egg: first at 10 s, then every 20 s; an egg at the spot of each of 2 random non-tanks (4 at 6 or more),
    // dropped after the warning (2 s, heroic 3 s: the marker follows its player and lands where they stand).
    inline constexpr std::uint32_t kLayFirstMs = 10000;
    inline constexpr std::uint32_t kLayEveryMs = 20000;
    inline constexpr FlexAB kLayTargets{ 2, 4 };
    inline constexpr NH<std::uint32_t> kLayWarnMs{ 2000, 3000 };
    // Heroic: the marked player carries the egg out of the Brood Call's reach (a bots-only RunOut measured from her).
    inline constexpr float kCarryClearYd = 16.f;

    // SW3 Hatch: 3 Broodlings on the player who hatched it, in a ring around them.
    inline constexpr std::uint32_t kBroodlingsPerEgg = 3;
    inline constexpr float kBroodlingRingYd = 1.5f;
    inline constexpr std::uint32_t kBroodlingDespawnMs = 5000;  // after death (SummonWave's corpse timer)
    inline constexpr std::uint32_t kBroodlingRetargetMs = 1000;
    inline constexpr float kBroodlingSeekYd = 70.f;             // the cave, never the rest of the instance
    inline constexpr std::uint32_t kBroodlingHealth = 2000;     // 5 players, normal (the DT test pins it)
    inline constexpr std::uint32_t kBroodlingHealthHeroic = 3000;   // WP-H's heroic override

    // SW4 Mother's Milk: first at 5 s, then every 10 s; a 6 yd splash at the spot of a random non-tank (2 at 6 or more)
    // after a 2 s flight: 15% (heroic 20%) Nature + Weakened + a stack of Venom.
    inline constexpr std::uint32_t kMilkFirstMs = 5000;
    inline constexpr std::uint32_t kMilkEveryMs = 10000;
    inline constexpr FlexAB kMilkTargets{ 1, 2 };
    inline constexpr float kMilkRadius = 6.f;
    inline constexpr std::uint32_t kMilkFlightMs = 2000;
    inline constexpr NH<float> kMilkPct{ 15.f, 20.f };
    inline constexpr float kMilkMissileSpeed = 20.f;            // the look spell's Speed (the DT test pins it)

    // When the missile look must leave her, after the circle registers, so it lands as the splash resolves (a long spit
    // leaves at once and lands a little early, a short one waits). Clamped to the flight time.
    inline std::uint32_t MilkLaunchDelayMs(float distanceYd)
    {
        float const flight = std::max(0.f, distanceYd) / kMilkMissileSpeed * 1000.f;
        float const wait = static_cast<float>(kMilkFlightMs) - std::min(flight, static_cast<float>(kMilkFlightMs));
        return static_cast<std::uint32_t>(wait + 0.5f);
    }

    // SW5 Venom: Poison, 1% of the reference row a second per stack, 30 s (a new stack refreshes it), up to 5 stacks
    // (heroic 8). Two spells with their own stack limits (210126 / 210127). A Poison dispel clears every stack.
    inline constexpr float kVenomPctPerStack = 1.f;
    inline constexpr std::uint32_t kVenomMs = 30000;
    inline constexpr NH<std::uint32_t> kVenomMaxStacks{ 5, 8 };

    constexpr std::uint32_t VenomSpell(bool heroic)
    {
        return heroic ? SPELL_SW_VENOM_HEROIC : SPELL_SW_VENOM;
    }

    // SW6 Crystal Spray: first at 12 s, then every 15 s; she rears up for 2 s (cast bar), then a 60 degree cone 20 yd
    // in front of her hits the non-tanks: 25% (heroic 30%) Frost + Weakened + 2 s encased. The tank is exempt (at 10
    // players both tanks are).
    inline constexpr std::uint32_t kSprayFirstMs = 12000;
    inline constexpr std::uint32_t kSprayEveryMs = 15000;
    inline constexpr std::uint32_t kSprayCastMs = 2000;
    inline constexpr float kSprayAngleDeg = 60.f;
    inline constexpr float kSprayLengthYd = 20.f;
    inline constexpr NH<float> kSprayPct{ 25.f, 30.f };
    inline constexpr std::uint32_t kEncasedMs = 2000;           // the Encased spell's duration (the DT test pins it)

    // SW7 Brood Call (heroic): first at 25 s, then every 30 s; she rears back and chitters for 3 s (cast bar, not
    // interruptible, emote), and at the end every egg within 15 yd of her hatches at once: 3 Broodlings each, onto the
    // player nearest that egg. No damage: only the Broodlings.
    inline constexpr std::uint32_t kBroodCallFirstMs = 25000;
    inline constexpr std::uint32_t kBroodCallEveryMs = 30000;
    inline constexpr std::uint32_t kBroodCallCastMs = 3000;
    inline constexpr float kBroodCallRangeYd = 15.f;

    // SW7 for the bots (heroic): a tank-only hold circle (Park) that keeps her where every egg is out of the call's
    // reach. The circle is small (she is held inside it), renewed every kParkRenewMs, and its centre keeps clear of
    // every egg by the call's reach plus the circle plus a margin.
    inline constexpr float kParkRadiusYd = 2.5f;
    inline constexpr float kParkMarginYd = 0.5f;
    inline constexpr float kParkMaxMoveYd = 12.f;               // the hold never drags her further than this
    inline constexpr std::uint32_t kParkHoldMs = 8000;
    inline constexpr std::uint32_t kParkRenewMs = 5000;

    constexpr float ParkAvoidRadiusYd()
    {
        return kBroodCallRangeYd + kParkRadiusYd + kParkMarginYd;
    }

    // The eggs that are within the call's reach of a boss held somewhere in the circle at `spot` (0: clean).
    inline std::size_t ParkViolations(Vec2 spot, std::vector<Vec2> const& eggs)
    {
        std::size_t n = 0;
        for (Vec2 const& egg : eggs)
            if (DungeonKit::Distance(spot, egg) < ParkAvoidRadiusYd())
                ++n;
        return n;
    }

    // Every egg is out of the call's reach for a boss held anywhere in the circle at `spot`.
    inline bool ParkSpotClean(Vec2 spot, std::vector<Vec2> const& eggs)
    {
        return ParkViolations(spot, eggs) == 0;
    }

    // SW8 Last Milk: on her death every living player in the cave who has quest 4866 (incomplete) and lacks the aura
    // gets the stock Mother's Milk 16468 (the gossip's two conditions). "In the cave": within this of her.
    inline constexpr float kLastMilkRangeYd = 100.f;
    inline constexpr float kLastMilkZBandYd = 40.f;

    inline bool LastMilkWanted(bool alive, bool gameMaster, bool questIncomplete, bool hasAura, float distance2dYd,
        float dzYd)
    {
        if (!alive || gameMaster || !questIncomplete || hasAura)
            return false;
        return distance2dYd <= kLastMilkRangeYd && std::fabs(dzYd) <= kLastMilkZBandYd;
    }

    // SW10 Widow's Bite (10 players only): her bite on her target every 6 s adds a stack (Poison, 1% a second per
    // stack, 15 s, each stack refreshing it, no cap: CumulativeAura 255); the second tank taunts at 3 stacks, once
    // its own have fallen off (the user ruling of 2026-11-15); a Poison dispel removes one stack.
    inline constexpr std::uint32_t kBiteFirstMs = 6000;
    inline constexpr std::uint32_t kBiteEveryMs = 6000;
    inline constexpr std::uint32_t kBiteMs = 15000;
    inline constexpr float kBitePctPerStack = 1.f;
    inline constexpr std::uint8_t kBiteSwapAtStacks = 3;
    inline constexpr float kBiteReachYd = 8.f;                  // a bite needs her target this close (B7's reach)
    inline constexpr std::uint32_t kBiteRetryMs = 1000;         // ... else it is tried again this much later
    inline constexpr std::uint32_t kBiteStackCap = 255;         // CumulativeAura: the aura counter's limit

    // The debuff falls off before its holder is wanted again: the tank who takes her at the swap reaches the swap count
    // after SwapAtStacks bites, kBiteEveryMs apart, and the tank who gave her up had his last stack on the swap. So the
    // debuff must be gone by then: it lasts less than the new holder needs to reach the count.
    static_assert(kBiteMs < kBiteSwapAtStacks * kBiteEveryMs,
        "Widow's Bite must fall off the old tank before the new tank reaches the swap count");

    // The ms one tank holds her from a swap to the next (about 18 s) and the ms the old one spends clear of the
    // debuff by then (3 s: gone at 15, wanted again at 18).
    constexpr std::uint32_t BiteHoldMs()
    {
        return kBiteSwapAtStacks * kBiteEveryMs;
    }

    constexpr std::uint32_t BiteClearMs()
    {
        return BiteHoldMs() - kBiteMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Broodlings (SW3): where they burst, whom they go for
    // ----------------------------------------------------------------------------------------------------------------

    // The three spawn points: a ring of kBroodlingRingYd around `at`, the first at `startAngle` (radians).
    inline std::array<Vec2, kBroodlingsPerEgg> BroodlingSpots(Vec2 at, float startAngle)
    {
        std::array<Vec2, kBroodlingsPerEgg> spots{};
        for (std::size_t i = 0; i < kBroodlingsPerEgg; ++i)
            spots[i] = DungeonKit::Advance(at, startAngle + static_cast<float>(i) * DungeonKit::kTwoPi
                / static_cast<float>(kBroodlingsPerEgg), kBroodlingRingYd);
        return spots;
    }

    struct BroodlingCandidate
    {
        std::uint64_t guid = 0;
        std::uint32_t venom = 0;        // the player's Venom stacks (either spell)
        float distance = 0.f;           // from the Broodling
    };

    // "Goes for the player with the most Venom, else the player who hatched it" (SP). Ties on the most Venom go to the
    // hatcher when he is one of them, else the nearest, else the lower guid. Nobody with Venom and the hatcher gone
    // (dead, left): nullopt, the Broodling keeps the target it has.
    inline std::optional<std::uint64_t> PickBroodlingTarget(std::vector<BroodlingCandidate> const& players,
        std::uint64_t hatcher)
    {
        std::uint32_t most = 0;
        for (BroodlingCandidate const& c : players)
            most = std::max(most, c.venom);
        if (most == 0)
        {
            for (BroodlingCandidate const& c : players)
                if (hatcher && c.guid == hatcher)
                    return hatcher;
            return std::nullopt;
        }
        BroodlingCandidate const* best = nullptr;
        for (BroodlingCandidate const& c : players)
        {
            if (c.venom != most)
                continue;
            if (hatcher && c.guid == hatcher)
                return hatcher;
            if (!best || c.distance < best->distance || (c.distance == best->distance && c.guid < best->guid))
                best = &c;
        }
        return best ? std::optional<std::uint64_t>(best->guid) : std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Brood Call (SW7)
    // ----------------------------------------------------------------------------------------------------------------

    // The indices of the eggs within the call's reach of `boss` (2D, inclusive).
    inline std::vector<std::size_t> EggsInBroodRange(std::vector<Vec2> const& eggs, Vec2 boss)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < eggs.size(); ++i)
            if (DungeonKit::Distance(eggs[i], boss) <= kBroodCallRangeYd)
                out.push_back(i);
        return out;
    }

    // The index of the player nearest `egg` (the first on a tie); nullopt with nobody.
    inline std::optional<std::size_t> NearestTo(std::vector<Vec2> const& players, Vec2 egg)
    {
        std::optional<std::size_t> best;
        float bestDist = 0.f;
        for (std::size_t i = 0; i < players.size(); ++i)
        {
            float const d = DungeonKit::Distance(players[i], egg);
            if (!best || d < bestDist)
            {
                best = i;
                bestDist = d;
            }
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BeatClock: a repeating beat on the AI's own ms clock
    // ----------------------------------------------------------------------------------------------------------------

    class BeatClock
    {
    public:
        // Starts (or restarts) the beat: due `afterMs` from `nowMs`.
        void Start(std::uint64_t nowMs, std::uint32_t afterMs)
        {
            _on = true;
            _dueMs = nowMs + afterMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time (start to start), never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };

    // The beats the fight's clock starts at the pull: (first delay, cadence). The brood call (heroic only) and the
    // bite (10 players only) are started by the AI when they apply.
    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    inline constexpr Beat kLayBeat{ kLayFirstMs, kLayEveryMs };
    inline constexpr Beat kMilkBeat{ kMilkFirstMs, kMilkEveryMs };
    inline constexpr Beat kSprayBeat{ kSprayFirstMs, kSprayEveryMs };
    inline constexpr Beat kBroodCallBeat{ kBroodCallFirstMs, kBroodCallEveryMs };
    inline constexpr Beat kBiteBeat{ kBiteFirstMs, kBiteEveryMs };

    // Eggs on the floor after `rounds` lay rounds at `players` players, none hatched: the starting clutch plus what
    // each round laid (the space math of the SP: 8 + 4 x 2 = 16 at 5, 8 + 4 x 4 = 24 at 10).
    constexpr std::uint32_t EggsAfter(std::uint32_t rounds, std::uint32_t players)
    {
        return static_cast<std::uint32_t>(kClutchCount) + rounds * kLayTargets.At(players);
    }
}

#endif
