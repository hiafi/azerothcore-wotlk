// Host tests for RattlegoreLogic.h (S2: Rattlegore (11622)): the thresholds (once each, two at once), the landing
// points, the pile's crawl and grind, Frenzy, the ring timings out and back, and Salvage's gate.
#include "RattlegoreLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoRattlegore;

namespace
{
    // A small deterministic LCG in [0, 1).
    struct Lcg
    {
        std::uint32_t s;
        float operator()()
        {
            s = s * 1664525u + 1013904223u;
            return static_cast<float>(s >> 8) / 16777216.f;
        }
    };

    bool Near(float a, float b, float eps = 1e-3f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { SPELL_RG_PART_LANDS, SPELL_RG_PART_FLUNG, SPELL_RG_GRIND, SPELL_RG_BOLTED_BACK_ON,
            SPELL_RG_FRENZY, SPELL_RG_ERUPTION_CAST, SPELL_RG_ERUPTION_HIT, SPELL_RG_SALVAGE, SPELL_RG_SALVAGE_HEAL,
            SPELL_RG_REINFORCED, SPELL_RG_KNOCK_AWAY, SPELL_RG_GROUND_TO_DUST })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_RG_PART_LANDS == 206130);
        CHECK(SPELL_RG_GROUND_TO_DUST == 206141);
        // The boss spawns inside his arena.
        CHECK(RattlegoreArena().Contains(kRattlegoreSpawn.XY(), kRattlegoreSpawn.z));
        CHECK(ArenaFor(BOSS_RATTLEGORE).Contains(kRattlegoreSpawn.XY(), kRattlegoreSpawn.z));
        // Every construct spot is on his arena (he walks there for Salvage) and on the floor frame.
        for (Point3 const& c : kConstructSpots)
        {
            CHECK(RattlegoreArena().Contains(c.XY(), c.z));
            CHECK(DungeonKit::InsideFrame(kOssuaryFloor, c.XY()));
        }
        // The landing rules' arena is RattlegoreArena()'s circle.
        Arena const arena = RattlegoreArena();
        LandingRules const rules;
        CHECK(arena.regions.size() == 1);
        CHECK(Near(arena.regions[0].center.x, rules.arenaCenter.x));
        CHECK(Near(arena.regions[0].center.y, rules.arenaCenter.y));
        CHECK(Near(arena.regions[0].radius, rules.arenaRadius));
    }

    void TestThresholds()
    {
        BreakLadder ladder;
        CHECK(ladder.Take(100.f) == 0);
        CHECK(ladder.Take(85.5f) == 0);
        CHECK(ladder.Take(85.f) == 1);          // at 85: the first break
        CHECK(ladder.Take(84.f) == 0);          // once
        CHECK(ladder.Take(90.f) == 0);          // healed over it: not again
        CHECK(ladder.Take(84.f) == 0);
        CHECK(ladder.Take(54.f) == 2);          // a burst over 70 and 55: two at once
        CHECK(ladder.Breaks() == 3);
        CHECK(ladder.FiredCount() == 3);
        CHECK(ladder.Take(0.5f) == 3);          // 40, 25, 10
        CHECK(ladder.FiredCount() == 6);
        CHECK(ladder.Take(0.f) == 0);
        CHECK(ladder.Breaks() == 6);            // six breaks in all
        ladder.AddForced();
        CHECK(ladder.Breaks() == 7);
        CHECK(ladder.FiredCount() == 6);
        ladder.Reset();
        CHECK(ladder.Breaks() == 0 && ladder.FiredCount() == 0);
        CHECK(ladder.Take(9.f) == 6);           // a one-shot from full: all six (12 piles on heroic)
    }

    void TestLandings()
    {
        LandingRules const rules;
        auto anyFloor = [](Vec2) { return true; };
        Lcg rng{ 12345u };
        std::uint32_t far = 0;
        std::uint32_t total = 0;
        std::uint32_t opposite = 0;
        std::uint32_t pairs = 0;
        // Boss positions over his arena, on the floor.
        for (float x = 100.f; x <= 162.f; x += 4.f)
            for (float y = 152.f; y <= 196.f; y += 4.f)
            {
                Vec2 const boss{ x, y };
                if (!RattlegoreArena().Contains(boss, 94.f) || !DungeonKit::InsideFrame(kOssuaryFloor, boss))
                    continue;
                for (bool heroic : { false, true })
                {
                    std::vector<Vec2> const picks = PickLandings(rules, boss, kPilesPerBreak(heroic), {}, rng,
                        anyFloor);
                    CHECK(picks.size() == kPilesPerBreak(heroic));
                    for (Vec2 const& p : picks)
                    {
                        ++total;
                        CHECK(OnLandingFloor(rules, p));
                        CHECK(RattlegoreArena().Contains(p, 94.f));
                        // "a 20 yd point always exists" (NAVMESH): every landing is 20+ yd out (beyond the rings)
                        if (DungeonKit::Distance(boss, p) >= rules.minFromBoss)
                            ++far;
                    }
                    if (picks.size() == 2)
                    {
                        CHECK(DungeonKit::Distance(picks[0], picks[1]) >= rules.minApart);
                        // Opposite directions where the floor allows it: near the room's middle (the tank's spot)
                        // there is 20+ yd floor on both sides. Off-center, 20+ yd wins over the angle.
                        float const angle = AngleApartDeg(boss, picks[0], picks[1]);
                        if (DungeonKit::Distance(boss, rules.arenaCenter) <= 6.f)
                        {
                            ++pairs;
                            if (angle >= rules.oppositeDeg)
                                ++opposite;
                        }
                    }
                }
            }
        CHECK(total > 100);
        CHECK(far == total);
        CHECK(pairs >= 5);
        CHECK(opposite == pairs);

        // `avoid`: a live pile is never landed on.
        Vec2 const boss{ 130.5f, 173.5f };
        std::vector<Vec2> const first = PickLandings(rules, boss, 2, {}, rng, anyFloor);
        std::vector<Vec2> const second = PickLandings(rules, boss, 2, first, rng, anyFloor);
        CHECK(second.size() == 2);
        for (Vec2 const& a : first)
            for (Vec2 const& b : second)
                CHECK(DungeonKit::Distance(a, b) >= rules.minApart);

        // `valid` rejects everything: nothing to throw at.
        CHECK(PickLandings(rules, boss, 2, {}, rng, [](Vec2) { return false; }).empty());
        // `valid` keeps only the west half: still 20+ yd when the boss stands east.
        std::vector<Vec2> const west = PickLandings(rules, Vec2{ 155.f, 175.f }, 1, {}, rng,
            [](Vec2 p) { return p.x < 125.f; });
        CHECK(west.size() == 1 && west[0].x < 125.f);
        CHECK(!west.empty() && DungeonKit::Distance(Vec2{ 155.f, 175.f }, west[0]) >= rules.minFromBoss);

        // The missile lands on the resolve.
        CHECK(LaunchDelayMs(2000, 20.f) == 1000);
        CHECK(LaunchDelayMs(2000, 40.f) == 0);
        CHECK(LaunchDelayMs(2000, 50.f) == 0);
        CHECK(LaunchDelayMs(2000, 0.f) == 2000);
    }

    void TestPile()
    {
        // Normal: waits 3 s, crawls, 5 ticks over 5 s on it, progress kept when the soaker steps off.
        PileState pile(PileTuningFor(false));
        PileState::Step s = pile.Update(1000, false, false);
        CHECK(!s.move && pile.GetPhase() == PileState::Phase::Waiting);
        s = pile.Update(1999, false, false);
        CHECK(!s.move);
        s = pile.Update(1, false, false);
        CHECK(s.move && pile.GetPhase() == PileState::Phase::Crawling);
        s = pile.Update(100, false, false);
        CHECK(s.move);
        // A soaker steps on: held, no move, a tick at each full second.
        s = pile.Update(500, true, false);
        CHECK(s.held && !s.move && s.ticks == 0);
        s = pile.Update(500, true, false);
        CHECK(s.ticks == 1);
        s = pile.Update(1500, true, false);
        CHECK(s.ticks == 1 && pile.TicksDone() == 2);
        // Steps off at 2.5 s: it crawls again, the 2.5 s are kept.
        s = pile.Update(1000, false, false);
        CHECK(s.move && s.ticks == 0 && pile.GrindMs() == 2500 && pile.GrindPct() == 50);
        s = pile.Update(500, true, false);
        CHECK(s.ticks == 1);
        s = pile.Update(2000, true, false);
        CHECK(s.ground && s.ticks == 2 && pile.TicksDone() == 5);   // 5 ticks: 25% in all
        CHECK(pile.Done() && pile.GetPhase() == PileState::Phase::Ground);
        s = pile.Update(1000, true, true);
        CHECK(!s.ground && !s.home && !s.move && s.ticks == 0);

        // A big diff does not over-tick past the grind.
        PileState big(PileTuningFor(false));
        s = big.Update(60000, true, false);
        CHECK(s.ground && s.ticks == 5);

        // Heroic: waits 1 s, 6 ticks over 6 s.
        PileState heroic(PileTuningFor(true));
        s = heroic.Update(999, false, false);
        CHECK(!s.move);
        s = heroic.Update(1, false, false);
        CHECK(s.move);
        std::uint32_t ticks = 0;
        for (int i = 0; i < 100 && !heroic.Done(); ++i)
            ticks += heroic.Update(100, true, false).ticks;
        CHECK(heroic.GetPhase() == PileState::Phase::Ground && ticks == 6);

        // Home: only while crawling and nobody on it.
        PileState home(PileTuningFor(false));
        s = home.Update(1000, false, true);
        CHECK(!s.home);                          // still waiting: it has not crawled yet
        s = home.Update(2000, false, true);
        CHECK(s.home && home.GetPhase() == PileState::Phase::Home);
        PileState held(PileTuningFor(false));
        held.Update(3000, false, false);
        s = held.Update(100, true, true);
        CHECK(!s.home && s.held);                // a soaker at his feet still holds it

        // A soaker on it while it waits grinds it too.
        PileState early(PileTuningFor(false));
        s = early.Update(1000, true, false);
        CHECK(s.ticks == 1 && s.held);

        // Numbers: the build spec's.
        CHECK(kPileWaitMs(false) == 3000 && kPileWaitMs(true) == 1000);
        CHECK(Near(kPileCrawlYdPerSec(false), 3.f) && Near(kPileCrawlYdPerSec(true), 4.f));
        CHECK(Near(kPileTickPct(false) * kPileGrindMs(false) / 1000.f, 25.f));
        CHECK(Near(kPileTickPct(true) * kPileGrindMs(true) / 1000.f, 36.f));
        CHECK(Near(kPileHomeHealPct(false), 8.f) && Near(kPileHomeHealPct(true), 10.f));
    }

    void TestFrenzy()
    {
        CHECK(FrenzyAfterBreak(8) == 4);
        CHECK(FrenzyAfterBreak(9) == 4);
        CHECK(FrenzyAfterBreak(1) == 0);
        CHECK(FrenzyAfterBreak(FrenzyAfterBreak(20)) == 5);    // two breaks at once: halved twice
        CHECK(FrenzyAfterHome(0) == 5);
        CHECK(FrenzyAfterHome(97) == kFrenzyMaxStacks);
        CHECK(FrenzyAfterHome(100) == 100);
        CHECK(kFrenzyEveryMs(false) == 3000 && kFrenzyEveryMs(true) == 2000);
        // Normal pace (SC: a break about every 12 s): 4 stacks gained between breaks, so he peaks near 8.
        std::uint32_t stacks = 0;
        std::uint32_t peak = 0;
        for (int b = 0; b < 6; ++b)
        {
            stacks = std::min(kFrenzyMaxStacks, stacks + 12000 / kFrenzyEveryMs(false));
            peak = std::max(peak, stacks);
            stacks = FrenzyAfterBreak(stacks);
        }
        CHECK(peak <= 8);
    }

    void TestEruption()
    {
        std::vector<EruptionRing> const normal = EruptionRings(false);
        std::vector<EruptionRing> const heroic = EruptionRings(true);
        CHECK(normal.size() == 3 && heroic.size() == 6);
        // Out: 0-6, 6-12, 12-18 (the outer hole 12.06: the 0.67 marker step), 2 s then 1.5 s apart.
        std::vector<std::uint32_t> const n = EruptionResolveTimes(false);
        CHECK(n.size() == 3 && n[0] == 2000 && n[1] == 3500 && n[2] == 5000);
        // Heroic: back inward 1 s apart, outermost first.
        std::vector<std::uint32_t> const h = EruptionResolveTimes(true);
        CHECK(h.size() == 6 && h[3] == 6000 && h[4] == 7000 && h[5] == 8000);
        for (std::size_t i = 0; i < 3; ++i)
        {
            CHECK(!heroic[i].inward && heroic[i + 3].inward);
            CHECK(Near(heroic[i].inner, heroic[5 - i].inner) && Near(heroic[i].outer, heroic[5 - i].outer));
        }
        // The rings tile 0-18: each starts where the last ends (the 0.06 yd strip at 12 aside), never overlap.
        CHECK(Near(normal[0].inner, 0.f) && Near(normal[2].outer, 18.f));
        for (std::size_t i = 1; i < normal.size(); ++i)
        {
            CHECK(normal[i].inner >= normal[i - 1].outer);
            CHECK(normal[i].inner - normal[i - 1].outer <= 0.06f + 1e-4f);
        }
        // Marker steps (mod-boss-mechanics kDonutRatios, rounded down within 1e-4): 6/12 is the 0.50 step and
        // 12.06/18 the 0.67 step, so each drawn hole is the real one.
        CHECK(std::fabs(6.f / 12.f - 0.50f) <= 1e-4f);
        CHECK(kEruptionOuterInner / 18.f >= 0.67f - 1e-4f);
        CHECK(kEruptionOuterInner / 18.f <= 0.67f + 1e-4f);
        CHECK(12.f / 18.f < 0.67f - 1e-4f);     // why: 12 / 18 would round down to the 0.60 step
        // Piles land beyond the rings.
        CHECK(LandingRules{}.minFromBoss > normal.back().outer);
        CHECK(Near(kEruptionPct(false), 35.f) && Near(kEruptionPct(true), 50.f));
        CHECK(kEruptionFirstMs == 8000 && kEruptionEveryMs == 20000);
        // The whole heroic chain ends well before the next stomp.
        CHECK(h.back() < kEruptionEveryMs);
    }

    void TestSalvage()
    {
        CHECK(!SalvageMayStart(0, 4, 100000, 0));
        CHECK(!SalvageMayStart(1, 4, 100000, 0));
        CHECK(SalvageMayStart(2, 4, 100000, 0));
        CHECK(!SalvageMayStart(2, 0, 100000, 0));      // the cap is 4
        CHECK(!SalvageMayStart(3, 2, 29999, 30000));
        CHECK(SalvageMayStart(3, 2, 30000, 30000));
        // 5% of his health in the channel stops it: 9,250 normal (185k), 14,000 heroic (280k).
        CHECK(SalvageBreakDamage(185000) == 9250);
        CHECK(SalvageBreakDamage(280000) == 14000);
        CHECK(!BreaksSalvage(9249, 185000));
        CHECK(BreaksSalvage(9250, 185000));
        CHECK(SalvageBreakDamage(185001) == 9251);     // rounded up
        // The nearest construct still standing.
        std::array<bool, 4> standing{ { true, true, true, true } };
        CHECK(NearestConstruct({ 157.f, 191.f }, standing) == std::optional<std::size_t>(0));
        CHECK(NearestConstruct({ 104.f, 156.f }, standing) == std::optional<std::size_t>(3));
        standing[3] = false;
        CHECK(NearestConstruct({ 104.f, 156.f }, standing) == std::optional<std::size_t>(1));
        standing = { { false, false, false, false } };
        CHECK(!NearestConstruct({ 130.f, 170.f }, standing));
        // Heals.
        CHECK(PctOfMax(185000, kSalvageHealPct) == 18500);
        CHECK(PctOfMax(185000, kPileHomeHealPct(false)) == 14800);
        CHECK(PctOfMax(280000, kPileHomeHealPct(true)) == 28000);
        CHECK(kReinforcedMaxStacks == 4);
    }

    void TestTimers()
    {
        CHECK(InRange(kStrikeFirst, 0.f) == 3000);
        CHECK(InRange(kStrikeFirst, 0.999f) <= 6000);
        CHECK(InRange(kKnockEvery, 0.5f) == 20000);
        CHECK(InRange(kKnockFirst, 2.f) == 15000);
    }
}

int main()
{
    TestSlice();
    TestThresholds();
    TestLandings();
    TestPile();
    TestFrenzy();
    TestEruption();
    TestSalvage();
    TestTimers();
    return Report("scholo_rattlegore_test");
}
