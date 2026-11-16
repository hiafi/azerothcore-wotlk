// Host tests for DrakkisathLogic.h (B14: General Drakkisath): the slice, the texts, the flex counts, the brands (the
// cast plan, the ticks, the partner pick), Flamestrike's circles and patches, the cast queue's hand-over to the hard
// mode (B15), the Seared Flesh taunt-swap timeline against his real strike gaps (the user ruling, the wave 2 addendum's
// lesson 1: SimulateSwaps), and the room.
#include "DrakkisathLogic.h"
#include "check.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <set>

using namespace BlackrockSpireRework;
using namespace BrsDrakkisath;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id = kFirstSpell; id <= kLastSpell; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 19);
        CHECK(kFirstSpell == 210520 && kLastSpell == 210538);
        CHECK(!kSpellSlice.Contains(SPELL_DR_RAGE));                    // stock
        CHECK(!kSpellSlice.Contains(SPELL_DR_GUARD_MORTAL_STRIKE));
        CHECK(!kSpellsGeneralsArmy.Contains(kLastSpell));               // B15's slice is its own
    }

    void TestTexts()
    {
        TextRange const* range = nullptr;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_DRAKKISATH)
                range = &r;
        CHECK(range && range->first == 0 && range->last == 9);
        CHECK(YELL_DR_AGGRO == 0 && EMOTE_DR_SEARING_BRAND == 1 && EMOTE_DR_COLLAPSING == 2);
        CHECK(YELL_DR_DEATH == 8 && YELL_DR_ARMY_ARMED == 9);
        CHECK(range && YELL_DR_ARMY_ARMED == range->last);
    }

    void TestBrands()
    {
        // Normal: one kind at random, 1 / 2 of it; heroic: 1 / 2 of each.
        BrandCounts const n5s = BrandsPerCast(false, 5, true);
        CHECK(n5s.searing == 1 && n5s.collapsing == 0);
        BrandCounts const n10c = BrandsPerCast(false, 10, false);
        CHECK(n10c.searing == 0 && n10c.collapsing == 2);
        BrandCounts const n6s = BrandsPerCast(false, 6, true);
        CHECK(n6s.searing == 2 && n6s.collapsing == 0);
        BrandCounts const h5 = BrandsPerCast(true, 5, true);
        CHECK(h5.searing == 1 && h5.collapsing == 1);
        BrandCounts const h8 = BrandsPerCast(true, 8, false);
        CHECK(h8.searing == 2 && h8.collapsing == 2);
        CHECK(BrandsPerCast(false, 0, true).searing == 1);              // a count not held reads as 5

        // 12 s: nothing for 2 s, then a tick every second: 10 ticks at 3 .. 12 s.
        CHECK(kBrandTicks == 10);
        CHECK(BrandTickAtMs(1) == 3000 && BrandTickAtMs(10) == 12000);
        CHECK(BrandTickAtMs(0) == 0 && BrandTickAtMs(11) == 0);
        CHECK(BrandTickAtMs(1) > kBrandMercyMs);

        // SP numbers: Searing 2% bearer, 6% others; Collapsing 8%, 80% less (1.6%) with company.
        CHECK(Near(BearerTickPct(Brand::Searing, 0), 2.f) && Near(BearerTickPct(Brand::Searing, 3), 2.f));
        CHECK(Near(NeighborTickPct(Brand::Searing), 6.f) && Near(NeighborTickPct(Brand::Collapsing), 0.f));
        CHECK(Near(BearerTickPct(Brand::Collapsing, 0), 8.f));
        CHECK(Near(BearerTickPct(Brand::Collapsing, 1), 1.6f) && Near(BearerTickPct(Brand::Collapsing, 4), 1.6f));
        CHECK(Near(kCollapsingPairedPct, kCollapsingAlonePct * 0.2f));
        // A whole brand: a lone Searing bearer 20%, a neighbor 60% (the reason to spread); a lone Collapsing bearer
        // 80%, a paired one 16% (the reason to pair).
        CHECK(Near(kBrandTicks * kSearingBearerPct, 20.f) && Near(kBrandTicks * kSearingOthersPct, 60.f));
        CHECK(Near(kBrandTicks * kCollapsingAlonePct, 80.f) && Near(kBrandTicks * kCollapsingPairedPct, 16.f));
        CHECK(kBrandMs < kBrandEveryMs);                                // one cast's brands end before the next
        CHECK(BrandName(Brand::Searing)[0] == 's' && BrandName(Brand::Collapsing)[0] == 'c');
    }

    void TestPartners()
    {
        std::vector<BrandPlayer> players{
            { 1, { 0.f, 0.f }, false },     // Collapsing bearer
            { 2, { 3.f, 0.f }, false },     // Searing bearer: never the partner
            { 3, { 6.f, 0.f }, true },      // the tank: only when nobody else is free
            { 4, { 9.f, 0.f }, false },
            { 5, { 20.f, 0.f }, false },
        };
        // Heroic at 5: one of each; the partner is the nearest player with no brand, a non-tank before the tank.
        auto pairs = PairCollapsing({ 1 }, { 2 }, players);
        CHECK(pairs.size() == 1 && pairs[0].first == 1 && pairs[0].second == 4);
        // Nobody but the tank is free: the tank.
        std::vector<BrandPlayer> const fewer{ players[0], players[1], players[2] };
        pairs = PairCollapsing({ 1 }, { 2 }, fewer);
        CHECK(pairs.size() == 1 && pairs[0].second == 3);
        // Two Collapsing bearers pair with each other (heroic at 6+, normal at 6+), listed once.
        pairs = PairCollapsing({ 1, 5 }, { 2 }, players);
        CHECK(pairs.size() == 1 && pairs[0].first == 1 && pairs[0].second == 5);
        // Three: the first two pair, the third takes the nearest free player.
        std::vector<BrandPlayer> withSix = players;
        withSix.push_back({ 6, { 10.f, 0.f }, false });
        pairs = PairCollapsing({ 1, 5, 6 }, {}, withSix);
        CHECK(pairs.size() == 2 && pairs[1].first == 6 && pairs[1].second == 4);
        // A solo bearer has nobody: no partner, it burns alone.
        pairs = PairCollapsing({ 1 }, {}, { players[0] });
        CHECK(pairs.empty());
        // A bearer not among the players (gone) is skipped.
        pairs = PairCollapsing({ 42 }, {}, players);
        CHECK(pairs.empty());
    }

    void TestKit()
    {
        // DR5: 10 yd ring, 2 s wind-up, 25%, everyone; DR6: 2.5 s, 5 yd, 30%, 2 / 4; DR7: 1.5 s, 180 degrees, 10 yd,
        // 35%.
        CHECK(kThunderclapCastMs == 2000 && Near(kThunderclapRadius, 10.f) && Near(kThunderclapPct, 25.f));
        CHECK(kThunderclapSlowMs == 3000 && kThunderclapSlowPct > 0 && kThunderclapSlowPct < 100);
        CHECK(kFlamestrikeCastMs == 2500 && Near(kFlamestrikeRadius, 5.f) && Near(kFlamestrikePct, 30.f));
        CHECK(kFlamestrikeTargets.At(5) == 2 && kFlamestrikeTargets.At(6) == 4 && kFlamestrikeTargets.At(10) == 4);
        CHECK(kSweepCastMs == 1500 && Near(kSweepAngleDeg, 180.f) && Near(kSweepLength, 10.f) && Near(kSweepPct, 35.f));
        // Heroic: a circle under every player; normal never more circles than players.
        CHECK(FlamestrikeCircles(true, 10, 10) == 10 && FlamestrikeCircles(true, 5, 5) == 5);
        CHECK(FlamestrikeCircles(false, 5, 5) == 2 && FlamestrikeCircles(false, 8, 8) == 4);
        CHECK(FlamestrikeCircles(false, 5, 1) == 1);
        // Patches: 15 s against a 15 s cadence: one cast's set at a time. Space (SP: about 310 / 630 sq yd at most):
        // normal 2 / 4 patches, heroic up to 10, against the hall's 3,518 sq yd (NM 13).
        CHECK(FlamestrikePatchesAtOnce(2) == 2 && FlamestrikePatchesAtOnce(4) == 4);
        float const patch = DungeonKit::kPi * kFlamestrikeRadius * kFlamestrikeRadius;
        CHECK(FlamestrikePatchesAtOnce(4) * patch < 320.f);
        CHECK(FlamestrikePatchesAtOnce(FlamestrikeCircles(true, 10, 10)) * patch < 0.25f * 3518.f);
        // Timers (build spec "First, cooldown").
        CHECK(kBrandFirstMs == 15000 && kBrandEveryMs == 20000);
        CHECK(kThunderclapFirstMs == 8000 && kThunderclapEveryMs == 15000);
        CHECK(kFlamestrikeFirstMs == 6000 && kFlamestrikeEveryMs == 15000);
        CHECK(kSweepFirstMs == 5000 && kSweepEveryMs == 12000);
        // Priorities: the tank hits first; B15's casts are ids above his.
        CHECK(kSweepPriority > kThunderclapPriority && kThunderclapPriority > kFlamestrikePriority);
        CHECK(kHardModeCastBase > CAST_FLAMESTRIKE && kHeldCastId < CAST_SWEEP);
    }

    // The B8 / B9 hand-over (R-1 F-1d): a hard mode cast's entry goes before its hook runs, so the hook's own
    // reschedule of the same id stays; a kicked bar ends the hold at once.
    void TestHandOver()
    {
        DungeonKit::CastQueue queue(kCastSpacingMs);
        std::uint32_t constexpr kChallenge = kHardModeCastBase + 1;
        queue.Schedule(kChallenge, 1000, 4);
        queue.Schedule(CAST_SWEEP, 1000, kSweepPriority);
        CHECK(queue.Next(1000) == kChallenge);
        std::optional<std::uint32_t> const hold = StartHardModeCast(queue, kChallenge, 1000, [&queue]()
        {
            queue.Schedule(kChallenge, 46000, 4);      // the next one, from inside the hook
            return std::optional<std::uint32_t>(12000);
        });
        CHECK(hold && *hold == 12000);
        CHECK(queue.Queued(kChallenge) && queue.DueAt(kChallenge) == 46000u);
        CHECK(queue.Queued(CAST_SWEEP));
        CHECK(!queue.Next(5000));                                       // held: his Sweep waits
        CHECK(!queue.Next(13500));                                      // the hold, then the spacing
        CHECK(queue.Next(14000) == CAST_SWEEP);
        // A hook that cannot start holds nothing.
        DungeonKit::CastQueue other(kCastSpacingMs);
        other.Schedule(kChallenge, 0, 4);
        CHECK(!StartHardModeCast(other, kChallenge, 0, []() { return std::optional<std::uint32_t>(); }));
        CHECK(!other.Waiting(0));
        // Kicked at 3 s into a 12 s hold: the hold ends now, the next cast 1 s later.
        DungeonKit::CastQueue kicked(kCastSpacingMs);
        kicked.Schedule(CAST_SWEEP, 0, kSweepPriority);
        StartHardModeCast(kicked, kChallenge, 0, []() { return std::optional<std::uint32_t>(12000); });
        CHECK(EndHoldEarly(kicked, 12000, 3000) == 3000);
        CHECK(!kicked.Next(3500) && kicked.Next(4000) == CAST_SWEEP);
        CHECK(EndHoldEarly(kicked, 12000, 13000) == 12000);             // already over: unchanged
    }

    void TestSearedFleshRules()
    {
        CHECK(kSearedFleshFirstMs == 8000 && kSearedFleshEveryMs == 8000 && kSearedFleshMs == 15000);
        CHECK(kSearedFleshSwapAt == 3 && kSearedFleshDamagePct == 10);
        CHECK(SearedFleshStacks(kSearedFleshEveryMs, kSearedFleshMs));
        CHECK(SearedFleshFallsOffInTime(kSearedFleshEveryMs, kSearedFleshMs, kSearedFleshSwapAt));
        CHECK(!SearedFleshFallsOffInTime(kSearedFleshEveryMs, 24000, kSearedFleshSwapAt));
        CHECK(!SearedFleshStacks(kSearedFleshEveryMs, 8000));
        CHECK(SearedFleshDamage(1000, 0) == 1000 && SearedFleshDamage(1000, 3) == 1300);
        CHECK(SearedFleshDamage(1000, 10) == 2000);
        CHECK(!SearedFleshHoldDue(500, 10000) && SearedFleshHoldDue(1000, 10000));
        CHECK(SearedFleshHoldDue(200, 600));                            // about to run out: apply now
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Seared Flesh against the user's taunt rule: a model of the fight's own timers at 10 players with the downtime
    // that keeps his blade off his target: his three wind-ups on the cast queue (1 s apart; the heroic Flamestrike
    // uninterrupted, the worst case), the tank's run out of the 10 yd Thunderclap ring and back, B15's 12 s Challenge
    // hold every 45 s (optional), and the walk to a new tank after a taunt. The bots' rule (MechanicTauntSwap.h): the
    // holder at the count and the taker with none of his stacks. 100 ms ticks, 8 s taunt cooldowns.
    // ----------------------------------------------------------------------------------------------------------------
    struct SwapSetup
    {
        bool hold = true;                   // the fix: his target's stacks hold while he cannot strike it
        std::uint32_t clapRunMs = 2500;     // the tank leaves the ring in the wind-up and is back this long after it
        std::uint32_t tauntWalkMs = 1000;
        std::uint32_t challengeEveryMs = 0; // B15's phase 2: a 12 s hold every 45 s (0: none)
        std::uint32_t challengeMs = 12000;
        std::uint32_t durationMs = kSearedFleshMs;
        std::uint32_t totalMs = 240000;
    };

    struct SwapResult
    {
        std::uint32_t strikes = 0;
        std::uint32_t reached = 0;          // a holder reached the count
        std::uint32_t lost = 0;             // the holder's stacks fell off below the count
        std::uint32_t swaps = 0;
        std::uint32_t tauntsWithStacks = 0;
        std::uint32_t peak = 0;
        std::uint32_t waitMs = 0;           // a holder at or past the count with no legal taker
        std::uint32_t maxGapMs = 0;         // the longest real gap between two strikes
    };

    SwapResult SimulateSwaps(SwapSetup const& f)
    {
        std::uint32_t constexpr kStep = 100;
        std::uint32_t constexpr kTauntCdMs = 8000;
        SwapResult r;
        DungeonKit::CastQueue queue(kCastSpacingMs);
        queue.Schedule(CAST_SWEEP, kSweepFirstMs, kSweepPriority);
        queue.Schedule(CAST_THUNDERCLAP, kThunderclapFirstMs, kThunderclapPriority);
        queue.Schedule(CAST_FLAMESTRIKE, kFlamestrikeFirstMs, kFlamestrikePriority);
        std::array<std::uint32_t, 2> stacks{ { 0, 0 } };
        std::array<std::uint32_t, 2> expires{ { 0, 0 } };
        std::array<std::uint32_t, 2> tauntReady{ { 0, 0 } };
        int holder = 0;
        std::uint32_t castEnd = 0;
        std::uint32_t outOfReachUntil = 0;
        std::uint32_t reachAt = 0;
        std::uint32_t holdUntil = 0;
        std::uint32_t nextStrike = kSearedFleshFirstMs;
        std::uint32_t nextChallenge = f.challengeEveryMs;
        std::uint32_t lastStrike = 0;
        bool reachedNow = false;

        for (std::uint32_t t = 0; t <= f.totalMs; t += kStep)
        {
            bool const busy = t < castEnd || t < holdUntil;
            if (!busy && f.challengeEveryMs && t >= nextChallenge)
            {
                // B15's Challenge from the queue: he leaves his tank for 12 s.
                holdUntil = t + f.challengeMs;
                queue.Started(kHeldCastId, t, f.challengeMs);
                nextChallenge = t + f.challengeEveryMs;
            }
            else if (!busy)
            {
                if (std::optional<std::uint32_t> const next = queue.Next(t))
                {
                    std::uint32_t castMs = 0;
                    std::uint32_t everyMs = 0;
                    std::uint8_t priority = 0;
                    switch (*next)
                    {
                        case CAST_SWEEP:
                            castMs = kSweepCastMs;
                            everyMs = kSweepEveryMs;
                            priority = kSweepPriority;
                            break;
                        case CAST_THUNDERCLAP:
                            castMs = kThunderclapCastMs;
                            everyMs = kThunderclapEveryMs;
                            priority = kThunderclapPriority;
                            outOfReachUntil = t + castMs + f.clapRunMs;
                            break;
                        default:
                            castMs = kFlamestrikeCastMs;
                            everyMs = kFlamestrikeEveryMs;
                            priority = kFlamestrikePriority;
                            break;
                    }
                    queue.Started(*next, t, castMs);
                    queue.Schedule(*next, t + everyMs, priority);
                    castEnd = t + castMs;
                }
            }

            bool const canStrike = t >= castEnd && t >= holdUntil && t >= outOfReachUntil && t >= reachAt;
            if (f.hold && !canStrike && stacks[holder])
                expires[holder] += kStep;
            for (int k = 0; k < 2; ++k)
                if (stacks[k] && t >= expires[k])
                {
                    if (k == holder && stacks[k] < kSearedFleshSwapAt)
                        ++r.lost;
                    stacks[k] = 0;
                }

            if (t >= nextStrike && canStrike)
            {
                ++stacks[holder];
                expires[holder] = t + f.durationMs;
                if (r.strikes)
                    r.maxGapMs = std::max(r.maxGapMs, t - lastStrike);
                lastStrike = t;
                ++r.strikes;
                nextStrike = t + kSearedFleshEveryMs;
                r.peak = std::max(r.peak, stacks[holder]);
                if (stacks[holder] == kSearedFleshSwapAt && !reachedNow)
                {
                    ++r.reached;
                    reachedNow = true;
                }
            }

            if (stacks[holder] >= kSearedFleshSwapAt)
            {
                int const other = 1 - holder;
                if (stacks[other] == 0 && t >= tauntReady[other])
                {
                    if (stacks[other])
                        ++r.tauntsWithStacks;
                    holder = other;
                    reachAt = t + f.tauntWalkMs;
                    tauntReady[other] = t + kTauntCdMs;
                    ++r.swaps;
                    reachedNow = false;
                }
                else
                    r.waitMs += kStep;
            }
        }
        return r;
    }

    void TestSwapTimeline()
    {
        SwapSetup s;
        SwapResult const held = SimulateSwaps(s);
        s.hold = false;
        SwapResult const loose = SimulateSwaps(s);
        s.hold = true;
        s.challengeEveryMs = 45000;
        SwapResult const phase2 = SimulateSwaps(s);
        s.hold = false;
        SwapResult const phase2Loose = SimulateSwaps(s);
        std::printf("seared flesh, 4 min at 10: hold strikes=%u swaps=%u lost=%u peak=%u wait=%ums maxgap=%ums | "
            "no hold lost=%u swaps=%u maxgap=%ums\n", held.strikes, held.swaps, held.lost, held.peak, held.waitMs,
            held.maxGapMs, loose.lost, loose.swaps, loose.maxGapMs);
        std::printf("seared flesh, with B15's 12 s Challenge every 45 s: hold swaps=%u lost=%u peak=%u wait=%ums "
            "maxgap=%ums | no hold lost=%u maxgap=%ums\n", phase2.swaps, phase2.lost, phase2.peak, phase2.waitMs,
            phase2.maxGapMs, phase2Loose.lost, phase2Loose.maxGapMs);

        // With the hold: the stacks always build to the count, the bots swap, nobody taunts with stacks, and the
        // holder never waits at the count for a taker (the old holder's stacks are gone first).
        for (SwapResult const* r : { &held, &phase2 })
        {
            CHECK(r->lost == 0);
            CHECK(r->swaps >= 5);
            CHECK(r->tauntsWithStacks == 0);
            CHECK(r->peak == kSearedFleshSwapAt);
            CHECK(r->waitMs == 0);
        }
        // His own kit's gaps stay under the 15 s duration (12.5 s: the wind-ups chain and the clap run), but B15's
        // 12 s Challenge pushes a real gap past it: without the hold a holder drops its stacks there.
        CHECK(held.maxGapMs > kSearedFleshEveryMs && held.maxGapMs < kSearedFleshMs);
        CHECK(phase2.maxGapMs > kSearedFleshMs);
        CHECK(phase2Loose.lost > 0);
        CHECK(phase2Loose.swaps < phase2.swaps);
        // A debuff past the bound (3 x 8 s) breaks the taunt rule's timing: the holder waits at the count.
        s.hold = true;
        s.challengeEveryMs = 0;
        s.durationMs = 32000;
        CHECK(SimulateSwaps(s).waitMs > 0);
    }

    void TestRoom()
    {
        // He spawns inside his arena and his alcove box; the hall and alcove boxes sit inside the arena.
        CHECK(DrakkisathArena().Contains(kDrakkisathSpawn.XY(), kDrakkisathSpawn.z));
        CHECK(ArenaFor(BOSS_DRAKKISATH).Contains(kDrakkisathSpawn.XY(), kDrakkisathSpawn.z));
        CHECK(DungeonKit::PointInPolygon(kAlcoveBox, kDrakkisathSpawn.XY()));
        CHECK(!DungeonKit::PointInPolygon(kHallBox, kDrakkisathSpawn.XY()));
        for (auto const& box : { kHallBox, kAlcoveBox })
            for (Vec2 const& p : box)
                CHECK(DrakkisathArena().Contains(p, kRoomZ));
        CHECK(kDrakkisathSpawn.z > kRoomZMin && kDrakkisathSpawn.z < kRoomZMax);
        // His Sweep (10 yd) and Thunderclap ring (10 yd) fit his alcove's depth from his spot to the hall.
        CHECK(kHallBox[1].x - kHallBox[0].x > 2.f * kThunderclapRadius);
        // The side gates are outside the fight's floor (4.5 yd below, B15's squads come through them).
        CHECK(!DrakkisathArena().Contains(kDrakkisathGate1.XY(), kDrakkisathGate1.z));
        CHECK(!DrakkisathArena().Contains(kDrakkisathGate2.XY(), kDrakkisathGate2.z));
    }
}

int main()
{
    TestSlice();
    TestTexts();
    TestBrands();
    TestPartners();
    TestKit();
    TestHandOver();
    TestSearedFleshRules();
    TestSwapTimeline();
    TestRoom();
    return Report("brs_drakkisath_test");
}
