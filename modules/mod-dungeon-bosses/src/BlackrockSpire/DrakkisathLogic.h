/*
 * mod-dungeon-bosses, Blackrock Spire B14:
 * General Drakkisath (10363), the pure, host-testable part (no engine headers). WP-B14 owns this file: its spell ids
 * (inside kSpellsDrakkisath of BlackrockSpireRework.h, 210520-210559), tuning constants, flex target pairs, text
 * groups, timers, picks and geometry, tested by tests/brs_drakkisath_test.cpp. The engine side is
 * boss_drakkisath_rework.cpp; the hard mode hooks (WP-B15, the General's Army) are DrakkisathFight.h.
 *
 * Build spec: SP 3990-4082 (DR1-DR9; DR10-DR19 are the hard mode's, B15). Damage is a percent of the reference row
 * (N = level 60 normal, H = level 60 heroic; the build spec gives one percent for both rows); counts "a / b" are 5
 * players / 6 or more (FlexAB).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace BrsDrakkisath
{
    using DungeonKit::Vec2;
    using BlackrockSpireRework::FlexAB;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsDrakkisath;

    // apps/dbc-tools source/npcs/blackrock_spire/drakkisath.py declares every one of them.
    enum DrakkisathSpells : std::uint32_t
    {
        SPELL_DR_SEARING_BRAND      = 210520,   // DR2 the brand on its bearer: a 12 s DUMMY debuff (V-2's orange rune)
        SPELL_DR_COLLAPSING_BRAND   = 210521,   // DR3 the brand on its bearer: a 12 s DUMMY debuff (the yellow rune)
        SPELL_DR_SEARING_BURN       = 210522,   // DR2 the bearer's tick (the kit's percent spell, Fire, 2%)
        SPELL_DR_SEARING_FLARE      = 210523,   // DR2 the flare on each other player within 4 yd (Fire, 6%)
        SPELL_DR_COLLAPSING_BURN    = 210524,   // DR3 the bearer's tick with nobody within 4 yd (Fire, 8%)
        SPELL_DR_COLLAPSING_SHARED  = 210525,   // DR3 the bearer's tick with someone within 4 yd (Fire, 1.6%)
        SPELL_DR_THUNDERCLAP_CAST   = 210526,   // DR5 the 2 s wind-up bar (Physical, not interruptible)
        SPELL_DR_THUNDERCLAP        = 210527,   // DR5 the ring's hit (resolve copy, Physical)
        SPELL_DR_THUNDERCLAP_SLOW   = 210528,   // DR5 the 3 s slow rider
        SPELL_DR_THUNDERCLAP_LOOK   = 210529,   // DR5 the clap on him (Thunderclap 15548's SV 145)
        SPELL_DR_FLAMESTRIKE_CAST   = 210530,   // DR6 normal: the 2.5 s bar (Fire, not interruptible)
        SPELL_DR_FLAMESTRIKE_CAST_H = 210531,   // DR6 heroic: the 2.5 s bar (Fire, interruptible: the expected kick)
        SPELL_DR_FLAMESTRIKE        = 210532,   // DR6 a circle's hit (resolve copy, Fire)
        SPELL_DR_FLAMESTRIKE_BURN   = 210533,   // DR6 the burning patch's tick (resolve copy, Fire)
        SPELL_DR_FLAMESTRIKE_PATCH  = 210534,   // DR6 the patch's look: a 5 yd dynamic object for 15 s (SV 10383)
        SPELL_DR_SWEEP_CAST         = 210535,   // DR7 the 1.5 s bar, the sword drawn back (Physical)
        SPELL_DR_BLACKBLADE_SWEEP   = 210536,   // DR7 the sweep's hit (resolve copy, Physical)
        SPELL_DR_SWEEP_LOOK         = 210537,   // DR7 his swing (Wide Swipe 6749's SV 399)
        SPELL_DR_SEARED_FLESH       = 210538,   // DR9 10 players: a stack on his target (15 s, refreshed, no cap)
    };
    // 210539-210559 spare (ask B14 before taking one; B15 has its own slice, kSpellsGeneralsArmy).
    std::uint32_t constexpr kFirstSpell = SPELL_DR_SEARING_BRAND;
    std::uint32_t constexpr kLastSpell = SPELL_DR_SEARED_FLESH;

    std::uint32_t constexpr SPELL_DR_RAGE = 16789;              // DR8, stock: +50% attack speed for 15 s
    std::uint32_t constexpr SPELL_DR_GUARD_MORTAL_STRIKE = 15708;   // DR8, the Elite Guards' (stock)
    std::uint32_t constexpr SPELL_DR_GUARD_STRIKE = 15580;          // DR8, the Elite Guards' (stock)

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text 10363; the SQL rev rev_drakkisath_blackrock_spire.sql writes 0-8). Lines 3-7 and 9 are the
    // hard mode's (B15 says them); line 9 is B15's own row.
    // ----------------------------------------------------------------------------------------------------------------
    enum DrakkisathTexts : std::uint8_t
    {
        YELL_DR_AGGRO           = 0,    // "You stand before Nefarian's champion. Kneel, and take my mark!"
        EMOTE_DR_SEARING_BRAND  = 1,    // "%s burns a Searing Brand into $n!"
        EMOTE_DR_COLLAPSING     = 2,    // "%s burns a Collapsing Brand into $n!"
        YELL_DR_PHASE_TWO       = 3,    // B15 (DR16)
        YELL_DR_CHALLENGE       = 4,    // B15 (DR17)
        YELL_DR_COWARDS         = 5,    // B15 (DR17, unanswered)
        YELL_DR_CHALLENGE_WON   = 6,    // B15 (DR18, won)
        YELL_DR_CHALLENGE_LOST  = 7,    // B15 (DR18, lost)
        YELL_DR_DEATH           = 8,
        YELL_DR_ARMY_ARMED      = 9,    // B15 (DR11)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms since the pull, on the AI's own clock: a cast bar never pauses them)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBrandFirstMs = 15000;              // DR2 / DR3: 15 s, then every 20 s
    std::uint32_t constexpr kBrandEveryMs = 20000;
    std::uint32_t constexpr kThunderclapFirstMs = 8000;         // DR5: 8 s, then every 15 s
    std::uint32_t constexpr kThunderclapEveryMs = 15000;
    std::uint32_t constexpr kFlamestrikeFirstMs = 6000;         // DR6: 6 s, then every 15 s
    std::uint32_t constexpr kFlamestrikeEveryMs = 15000;
    std::uint32_t constexpr kSweepFirstMs = 5000;               // DR7: 5 s, then every 12 s
    std::uint32_t constexpr kSweepEveryMs = 12000;
    std::uint32_t constexpr kRageFirstMs = 1000;                // DR8: stock (1 s, every 35 s)
    std::uint32_t constexpr kRageEveryMs = 35000;
    std::uint32_t constexpr kRetryMs = 1000;                    // no target: try again in 1 s

    // The Elite Guards' stock SmartAI timers (smart_scripts 10814, Knockdown dropped): Mortal Strike 5-12.8 s, then
    // every 13 s; Strike 12-20.8 s, then every 9 s.
    std::uint32_t constexpr kGuardMortalFirstMinMs = 5000;
    std::uint32_t constexpr kGuardMortalFirstMaxMs = 12800;
    std::uint32_t constexpr kGuardMortalEveryMs = 13000;
    std::uint32_t constexpr kGuardStrikeFirstMinMs = 12000;
    std::uint32_t constexpr kGuardStrikeFirstMaxMs = 20800;
    std::uint32_t constexpr kGuardStrikeEveryMs = 9000;
    std::uint32_t constexpr kGuardHoldPickMs = 500;             // a held Guard re-picks its target this often

    // The cast queue (DungeonKit::CastQueue): his three wind-ups one at a time, 1 s apart, and B15's casts (ids from
    // kHardModeCastBase). Higher priority first: the two that hit the tank before the Flamestrike.
    enum DrakkisathCasts : std::uint32_t
    {
        CAST_SWEEP          = 1,
        CAST_THUNDERCLAP    = 2,
        CAST_FLAMESTRIKE    = 3,
    };
    std::uint8_t constexpr kSweepPriority = 3;
    std::uint8_t constexpr kThunderclapPriority = 2;
    std::uint8_t constexpr kFlamestrikePriority = 1;
    std::uint32_t constexpr kHardModeCastBase = 100;
    std::uint32_t constexpr kCastSpacingMs = 1000;
    // An id no cast uses: CastQueue::Started on it holds the queue without touching an entry.
    std::uint32_t constexpr kHeldCastId = 0;

    // A hard mode cast comes up (the B8 / B9 hand-over, R-1 F-1d): its entry is consumed BEFORE the hook runs, so a
    // next cast the hook schedules for the same id (DrakkisathFight::ScheduleCast inside OnCast) stays on the queue;
    // the hold then starts without cancelling anything. `onCast` answers the hold in ms (nullopt: it could not start).
    template <class OnCast>
    std::optional<std::uint32_t> StartHardModeCast(DungeonKit::CastQueue& queue, std::uint32_t id,
        DungeonKit::CastQueue::Ms now, OnCast&& onCast)
    {
        queue.Cancel(id);
        std::optional<std::uint32_t> const holdMs = onCast();
        if (holdMs)
            queue.Started(kHeldCastId, now, *holdMs);
        return holdMs;
    }

    // A cast bar of his ended early (kicked) at `now` while a hold runs to `holdUntil`: the hold ends now and the
    // queue's spacing counts from now (he does not stand idle for the rest of the bar). Returns the new hold end.
    inline DungeonKit::CastQueue::Ms EndHoldEarly(DungeonKit::CastQueue& queue, DungeonKit::CastQueue::Ms holdUntil,
        DungeonKit::CastQueue::Ms now)
    {
        if (now >= holdUntil)
            return holdUntil;
        queue.Interrupted(now);
        return now;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR2 / DR3 his two brands
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBrandMs = 12000;                   // the brand's life
    std::uint32_t constexpr kBrandMercyMs = 2000;               // nothing for its first 2 s
    std::uint32_t constexpr kBrandTickMs = 1000;
    std::uint32_t constexpr kBrandTicks = (kBrandMs - kBrandMercyMs) / kBrandTickMs;   // ticks at 3 s .. 12 s
    float constexpr kBrandRadius = 4.f;
    float constexpr kBrandZBand = 5.f;                          // "within 4 yd" ignores a player this far above/below
    float constexpr kSearingBearerPct = 2.f;                    // a second, to the bearer
    float constexpr kSearingOthersPct = 6.f;                    // a second, to each other player within 4 yd
    float constexpr kCollapsingAlonePct = 8.f;                  // a second, nobody within 4 yd
    float constexpr kCollapsingPairedPct = 1.6f;                // a second, someone within 4 yd (80% less)
    // Bearers per cast: normal, one kind at random, 1 / 2 of it; heroic, 1 / 2 of each kind.
    inline constexpr FlexAB kBrandTargets{ 1, 2 };

    enum class Brand : std::uint8_t
    {
        Searing = 0,
        Collapsing = 1,
    };

    constexpr char const* BrandName(Brand b)
    {
        return b == Brand::Searing ? "searing" : "collapsing";
    }

    // How many bearers of each kind one cast brands. `searingRoll`: the normal cast's coin (true: Searing).
    struct BrandCounts
    {
        std::uint8_t searing = 0;
        std::uint8_t collapsing = 0;
    };

    constexpr BrandCounts BrandsPerCast(bool heroic, std::uint32_t players, bool searingRoll)
    {
        std::uint8_t const n = kBrandTargets.At(players);
        if (heroic)
            return { n, n };
        return searingRoll ? BrandCounts{ n, 0 } : BrandCounts{ 0, n };
    }

    // The ms since the brand landed of its tick `k` (1..kBrandTicks); 0 for any other k.
    constexpr std::uint32_t BrandTickAtMs(std::uint32_t k)
    {
        return (k >= 1 && k <= kBrandTicks) ? kBrandMercyMs + k * kBrandTickMs : 0;
    }

    // The bearer's own tick, by kind and the number of OTHER players within kBrandRadius of the bearer.
    constexpr float BearerTickPct(Brand b, std::uint32_t othersWithin)
    {
        if (b == Brand::Searing)
            return kSearingBearerPct;
        return othersWithin ? kCollapsingPairedPct : kCollapsingAlonePct;
    }

    // Each other player within kBrandRadius of a bearer takes this a tick (Searing only).
    constexpr float NeighborTickPct(Brand b)
    {
        return b == Brand::Searing ? kSearingOthersPct : 0.f;
    }

    // A player of the fight as the partner pick sees it.
    struct BrandPlayer
    {
        std::uint64_t id = 0;
        Vec2 at;
        bool tank = false;              // his current victim (a partner only when nobody else is free)
    };

    // DR3's partners: who each Collapsing bearer stacks on. Two Collapsing bearers pair with each other first (in the
    // order given; SP: "at 6 or more the two Collapsing bearers can pair with each other"); a bearer left over takes
    // the nearest player who bears no brand of this cast, a non-tank before the tank. Returns (bearer, partner) pairs;
    // a mutual pair is listed once (the first bearer goes to the second). A bearer with no free player (a solo test)
    // gets no entry: it burns alone.
    inline std::vector<std::pair<std::uint64_t, std::uint64_t>> PairCollapsing(
        std::vector<std::uint64_t> const& collapsing, std::vector<std::uint64_t> const& searing,
        std::vector<BrandPlayer> const& players)
    {
        std::vector<std::pair<std::uint64_t, std::uint64_t>> out;
        auto findPlayer = [&players](std::uint64_t id) -> BrandPlayer const*
        {
            for (BrandPlayer const& p : players)
                if (p.id == id)
                    return &p;
            return nullptr;
        };
        auto isBearer = [&collapsing, &searing](std::uint64_t id)
        {
            return std::find(collapsing.begin(), collapsing.end(), id) != collapsing.end()
                || std::find(searing.begin(), searing.end(), id) != searing.end();
        };
        std::vector<std::uint64_t> present;
        for (std::uint64_t id : collapsing)
            if (findPlayer(id))
                present.push_back(id);
        std::size_t i = 0;
        for (; i + 1 < present.size(); i += 2)
            out.emplace_back(present[i], present[i + 1]);
        if (i < present.size())
        {
            BrandPlayer const* bearer = findPlayer(present[i]);
            BrandPlayer const* best = nullptr;
            float bestDist = 0.f;
            for (BrandPlayer const& p : players)
            {
                if (isBearer(p.id))
                    continue;
                float const d = DungeonKit::Distance(bearer->at, p.at);
                bool const better = !best || (best->tank && !p.tank) || (best->tank == p.tank && d < bestDist);
                if (better)
                {
                    best = &p;
                    bestDist = d;
                }
            }
            if (best)
                out.emplace_back(present[i], best->id);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR5 Thunderclap, DR6 Flamestrike, DR7 Blackblade Sweep
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kThunderclapCastMs = 2000;
    float constexpr kThunderclapRadius = 10.f;
    float constexpr kThunderclapPct = 25.f;                     // everyone, the tank too (its own row)
    std::uint32_t constexpr kThunderclapSlowMs = 3000;
    std::int32_t constexpr kThunderclapSlowPct = 50;            // movement (SP: "a 3 s slow"; the amount is ours)

    std::uint32_t constexpr kFlamestrikeCastMs = 2500;
    float constexpr kFlamestrikeRadius = 5.f;
    float constexpr kFlamestrikePct = 30.f;
    inline constexpr FlexAB kFlamestrikeTargets{ 2, 4 };        // random non-tanks (normal; heroic: every player)
    std::uint32_t constexpr kFlamestrikePatchMs = 15000;
    std::uint32_t constexpr kFlamestrikePatchTickMs = 1000;
    float constexpr kFlamestrikePatchPct = 5.f;                 // a second, the tank too
    std::uint8_t constexpr kFlamestrikeKickPriority = 3;        // heroic: the descriptor's interrupt entry

    std::uint32_t constexpr kSweepCastMs = 1500;
    float constexpr kSweepAngleDeg = 180.f;
    float constexpr kSweepLength = 10.f;
    float constexpr kSweepPct = 35.f;                           // the tank too (its own row): no tank exemption

    // How many Flamestrike circles a cast lands: normal 2 / 4 at random non-tanks; heroic one under every player
    // (uninterrupted; a kick stops them all).
    constexpr std::uint32_t FlamestrikeCircles(bool heroic, std::uint32_t players, std::uint32_t fightPlayers)
    {
        return heroic ? fightPlayers : std::min<std::uint32_t>(kFlamestrikeTargets.At(players), fightPlayers);
    }

    // Burning patches at once, at most: a cast's patches last 15 s against a 15 s cadence (the queue can push a cast
    // late, never early), so the next cast's set lands as the old one goes out; with a patch longer than the cadence
    // two sets overlap.
    constexpr std::uint32_t FlamestrikePatchesAtOnce(std::uint32_t circlesPerCast)
    {
        return kFlamestrikePatchMs > kFlamestrikeEveryMs ? 2 * circlesPerCast : circlesPerCast;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DR9 Seared Flesh (10 players only, rulings 63, 70, 71; the taunt swap at 3)
    //
    // Every 8 s his blade adds a stack to his target (15 s, each stack refreshing it, no cap): +10% damage taken from
    // him per stack. The bots swap at 3 and, by the user's ruling (2026-11-15), a tank taunts only once its own stacks
    // are gone. With interval I = 8 s and duration D = 15 s:
    //   - D > I: the stacks build to the swap count at all;
    //   - D < swapAt x I: the old holder's stacks are gone before the new holder reaches the count (the old holder's
    //     last stack is at L; the new holder's third lands at L + 3I at the earliest, downtime only pushes it later).
    // Downtime (the wave 2 addendum's lesson 1): his blade needs him free and his target in reach. His three wind-ups
    // (Sweep 1.5 s, Thunderclap 2 s, Flamestrike 2.5 s, 1 s apart on the queue) chain, and the tank runs out of the
    // 10 yd clap and back: the host model's worst real gap on his own kit is 12.5 s (under D), and B15's 12 s
    // Challenge hold pushes it to 18.5 s (past D). So the B7 hold (user-approved, R-1 ruling 2 / F-1d): his target's
    // Seared Flesh holds (does not run down) while he cannot strike it, and the gap counted in striking time is I
    // again. Only the current target's stacks hold: an old holder's run down at once, which only helps the rule.
    // tests/brs_drakkisath_test.cpp models the fight (SimulateSwaps).
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kSearedFleshFirstMs = 8000;
    std::uint32_t constexpr kSearedFleshEveryMs = 8000;
    std::uint32_t constexpr kSearedFleshMs = 15000;
    std::int32_t constexpr kSearedFleshDamagePct = 10;          // per stack, his damage on that player only
    std::uint8_t constexpr kSearedFleshSwapAt = 3;
    std::uint8_t constexpr kSearedFleshMax = 255;               // "no cap" (the aura's own limit)

    constexpr bool SearedFleshStacks(std::uint32_t everyMs, std::uint32_t durationMs)
    {
        return durationMs > everyMs;
    }

    constexpr bool SearedFleshFallsOffInTime(std::uint32_t everyMs, std::uint32_t durationMs, std::uint8_t swapAt)
    {
        return swapAt >= 1 && durationMs < static_cast<std::uint32_t>(swapAt) * everyMs;
    }

    static_assert(SearedFleshStacks(kSearedFleshEveryMs, kSearedFleshMs), "Seared Flesh must outlast the strike gap");
    static_assert(SearedFleshFallsOffInTime(kSearedFleshEveryMs, kSearedFleshMs, kSearedFleshSwapAt),
        "Seared Flesh must fall off the old tank before the new one reaches the swap count");
    // The three wind-ups back to back plus a strike interval would outlast the duration (an upper bound; the queue's
    // cadences keep the measured gap at 12.5 s): the hold covers it whatever the order.
    static_assert(kSweepCastMs + kThunderclapCastMs + kFlamestrikeCastMs + 2 * kCastSpacingMs + kSearedFleshEveryMs
        > kSearedFleshMs, "the chained wind-ups outlast Seared Flesh: the hold is needed");

    // The hold is applied to the aura in steps (one aura update a second, not one a frame), and at once when the aura
    // would run out before the next step.
    std::uint32_t constexpr kSearedFleshHoldStepMs = 1000;

    constexpr bool SearedFleshHoldDue(std::uint32_t heldMs, std::int32_t auraLeftMs)
    {
        return heldMs >= kSearedFleshHoldStepMs
            || auraLeftMs <= static_cast<std::int32_t>(heldMs + kSearedFleshHoldStepMs / 2u);
    }

    // The damage he deals a player who carries `stacks` of his Seared Flesh.
    constexpr std::uint32_t SearedFleshDamage(std::uint32_t damage, std::uint32_t stacks)
    {
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(damage)
            * static_cast<std::uint64_t>(100u + static_cast<std::uint32_t>(kSearedFleshDamagePct) * stacks) / 100u);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The room (handoff section 3.8, NM 13)
    // ----------------------------------------------------------------------------------------------------------------
    // The bots' spot bounds: the main hall and his alcove (DrakkisathArena's boxes, 0.5 yd in), z 109..116. The floor
    // runs on south of y -325 (NM 13: walk it before widening; the arena stops there too).
    inline constexpr std::array<Vec2, 4> kHallBox{ { { -21.2f, -324.8f }, { 28.2f, -324.8f }, { 28.2f, -248.8f },
        { -21.2f, -248.8f } } };
    inline constexpr std::array<Vec2, 4> kAlcoveBox{ { { 28.2f, -309.8f }, { 43.2f, -309.8f }, { 43.2f, -262.2f },
        { 28.2f, -262.2f } } };
    float constexpr kRoomZMin = 109.f;
    float constexpr kRoomZMax = 116.f;
    float constexpr kRoomZ = 111.04f;                           // his spawn height
}

#endif
