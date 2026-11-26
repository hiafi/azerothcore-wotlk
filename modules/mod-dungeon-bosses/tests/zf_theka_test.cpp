// Host tests for ThekaLogic.h (D1: Theka the Martyr): the slice and the courtyard, the rise points and their sectors,
// the swarm's closing and turning rules, the stacks and their caps, the Penitent Hunt's stagger, the plague's ticks and
// cadence, the timeline through the rising, and the stack math of the design against section 3.6's health.
#include "ThekaLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace ZulFarrakRework;
using namespace ZfTheka;

namespace
{
    std::uint32_t g_seed = 4242;

    std::uint32_t Rand(std::uint32_t n)
    {
        g_seed = g_seed * 1103515245u + 12345u;
        return (g_seed >> 16) % n;
    }

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndTexts()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 213860 && kSpellSlice.last == 213889);
        CHECK(SPELL_TK_BITE == 213860);
        CHECK(SPELL_TK_HUNT_TRAIL == 213874);
        CHECK(kSpellSlice.Contains(SPELL_TK_HUNT_TRAIL));
        // SP's text groups 0-4 (rule 34)
        CHECK(YELL_THEKA_AGGRO == 0 && EMOTE_THEKA_SWARM == 1 && EMOTE_THEKA_DEVOUR == 2 && YELL_THEKA_RISING == 3
            && EMOTE_THEKA_HUNT == 4);
        // the drill's tags (MechanicDrill.h kZfTagSwarm 1, kZfTagReaim 2, kZfTagDevour 3, kZfTagSwarmNormal 4,
        // kZfTagDevourNormal 5); the undrilled ones past its last tag (40)
        CHECK(SwarmTag(true) == 1 && SwarmTag(false) == 4);
        CHECK(DevourTag(true) == 3 && DevourTag(false) == 5);
        CHECK(TAG_TK_REAIM == 2);
        CHECK(TAG_TK_CHASE > 40 && TAG_TK_ERUPTION > 40 && TAG_TK_SPREAD > 40);
    }

    void TestCourtyard()
    {
        Arena const courtyard = CourtyardArena();
        CHECK(courtyard.Contains(kThekaSpawn.XY(), kThekaSpawn.z));
        CHECK(ArenaFor(BOSS_THEKA).Contains(kThekaSpawn.XY(), kThekaSpawn.z));
        for (Point3 const& p : kThekaRisePoints)
        {
            CHECK(courtyard.Contains(p.XY(), p.z));
            // 30 yd out (section 3.8): the lines run about 7.5 s at 4 yd/s, 6 s at 5
            float const d = DungeonKit::Distance(p.XY(), kThekaSpawn.XY());
            CHECK(d > 28.f && d < 32.f);
            // the line to him stays on the courtyard (sampled every yard)
            for (float t = 0.f; t <= 1.f; t += 1.f / 30.f)
            {
                Vec2 const q{ p.x + (kThekaSpawn.x - p.x) * t, p.y + (kThekaSpawn.y - p.y) * t };
                CHECK(courtyard.Contains(q, 10.f));
            }
        }
        for (Point3 const& p : kThekaRiseAlternates)
            CHECK(courtyard.Contains(p.XY(), p.z));
        CHECK(courtyard.Contains(kCourtyardDisc.XY(), kCourtyardDisc.z));
        // sectors (+x north, +y west): A and B north-west, C and D north-east
        for (std::size_t i : kNorthWest)
            CHECK(kThekaRisePoints[i].x > kThekaSpawn.x && kThekaRisePoints[i].y > kThekaSpawn.y);
        for (std::size_t i : kNorthEast)
            CHECK(kThekaRisePoints[i].x > kThekaSpawn.x && kThekaRisePoints[i].y < kThekaSpawn.y);
    }

    void TestRisePicks()
    {
        std::set<std::size_t> normalSeen;
        for (int i = 0; i < 400; ++i)
        {
            std::vector<std::size_t> const n = RisePicks(false, Rand);
            CHECK(n.size() == 1 && n[0] < 4);
            normalSeen.insert(n[0]);
            std::vector<std::size_t> const h = RisePicks(true, Rand);
            CHECK(h.size() == 2);
            // one of each sector: the heroic lines cross only at Theka (section 7 #27 A)
            CHECK(h[0] == kNorthWest[0] || h[0] == kNorthWest[1]);
            CHECK(h[1] == kNorthEast[0] || h[1] == kNorthEast[1]);
        }
        CHECK(normalSeen.size() == 4);
        CHECK(Tune::kSwarmsPerRise(false) == 1 && Tune::kSwarmsPerRise(true) == 2);
    }

    void TestClosingAndTurning()
    {
        // TK2 drawn 2.5 s out: 10 yd at 4 yd/s, 12.5 at 5 (plus his hit box)
        CHECK(Near(ClosingYd(false), 10.f + kArriveReachYd));
        CHECK(Near(ClosingYd(true), 12.5f + kArriveReachYd));
        Vec2 const theka{ 0.f, 0.f };
        Vec2 const end = theka;
        // on the line, inside the distance
        CHECK(Closing({ 11.f, 0.f }, end, theka, false));
        CHECK(!Closing({ 12.f, 0.f }, end, theka, false));
        CHECK(Closing({ 13.f, 0.f }, end, theka, true));
        // walked 5 yd off the line's way: no circle, the body crawls to the end and turns
        Vec2 const moved{ 0.f, 5.f };
        CHECK(!Closing({ 8.f, 0.f }, end, moved, false));
        CHECK(!AtLineEnd({ 8.f, 0.f }, end));
        CHECK(AtLineEnd({ 0.5f, 0.f }, end));
        // walked along the line toward the body (2 yd off it): he still stands on its way, the circle comes early
        CHECK(Closing({ 8.f, 0.f }, end, Vec2{ 4.f, 2.f }, false));
        // the closing walk lands with the circle
        CHECK(Near(ClosingSpeed(ClosingYd(false)), Tune::kSwarmSpeed(false)));
        CHECK(Near(ClosingSpeed(ClosingYd(true)), Tune::kSwarmSpeed(true)));
        CHECK(ClosingSpeed(0.f) >= 1.f);
        // a turn's new line is a fresh warning on the floor (rule 32)
        CHECK(kReaimMs >= kWarningFloorMs);
    }

    void TestStacksAndHunts()
    {
        std::uint32_t s = 0;
        for (int i = 0; i < 9; ++i)
            s = AddStack(s, false);
        CHECK(s == 5);                                  // normal cap 5 (rule 23)
        s = 0;
        for (int i = 0; i < 9; ++i)
            s = AddStack(s, true);
        CHECK(s == 9);                                  // heroic: no cap (ruling 45)
        CHECK(AddStack(98, true) == 99 && AddStack(99, true) == 99);
        // the stagger: two swarms on normal hunt 7.5 s apart, three on heroic 4 s apart
        CHECK(HuntFirstDueMs(1000, 0, 2, false) == 1000 + kHuntFirstMs);
        CHECK(HuntFirstDueMs(1000, 1, 2, false) == 1000 + kHuntFirstMs + 7500);
        CHECK(HuntFirstDueMs(0, 2, 3, true) == kHuntFirstMs + 8000);
        // stack math's phase 2 on normal (SP): about 23 s gives about 3 hunts at 2 stacks, about 5 at 3 (4 here: the
        // first comes 3 s after the 2 s rising)
        auto huntsIn = [](std::uint32_t stacks, std::uint64_t phase2Ms)
        {
            std::uint32_t n = 0;
            for (std::uint32_t i = 0; i < stacks; ++i)
                for (std::uint64_t t = HuntFirstDueMs(Tune::kRisingMs, i, stacks, false); t < phase2Ms;
                     t += Tune::kHuntEveryMs(false))
                    ++n;
            return n;
        };
        CHECK(huntsIn(2, 23000) == 3);
        CHECK(huntsIn(3, 23000) == 4);
        // the Lament: 1.5% a stack, 6% at 4, 7.5% at 5 (SP)
        CHECK(Near(LamentPct(4), 6.f) && Near(LamentPct(5), 7.5f));
        // a hunt never waits: the hunted fill up when nobody else is free
        std::vector<int> const ids{ 1, 2, 3 };
        std::vector<int> const picked = PickPreferring(ids, std::vector<int>{ 1, 2 }, 1, Rand);
        CHECK(picked.size() == 1 && picked[0] == 3);
        std::vector<int> const all = PickPreferring(ids, std::vector<int>{ 1, 2, 3 }, 2, Rand);
        CHECK(all.size() == 2 && all[0] != all[1]);
        CHECK(PickPreferring(ids, std::vector<int>{}, 5, Rand).size() == 3);
    }

    void TestPlague()
    {
        // 15% over 12 s in 3 s ticks; 40% over 10 s in 2 s ticks (the copies too)
        CHECK(PlagueTickHundredths(false) == 375);
        CHECK(PlagueTickHundredths(true) == 800);
        CHECK(PlagueTickHundredths(false) * 4 == 1500);
        CHECK(PlagueTickHundredths(true) * 5 == 4000);
        CHECK(PlagueHitHundredths(false) == 1000 && PlagueHitHundredths(true) == 2000);
        CHECK(PlagueGapMs(0) == 12000 && PlagueGapMs(99999) == 16000 && PlagueGapMs(14000) == 14000);
        // one 10 s interrupter keeps up (SP): the shortest gap is longer than a kick's cooldown
        CHECK(Tune::kPlagueEveryMinMs >= 10000);
    }

    void TestTimeline()
    {
        for (bool heroic : { false, true })
        {
            Timeline t;
            t.Start(heroic);
            std::vector<std::uint64_t> swarms;
            std::vector<std::uint64_t> plagues;
            for (std::uint64_t now = 0; now <= 70000; now += 100)
            {
                if (t.SwarmDue(now))
                {
                    swarms.push_back(now);
                    t.SwarmRose(now);
                }
                if (t.PlagueDue(now))
                {
                    plagues.push_back(now);
                    t.PlagueCast(now, 12000 + Rand(4001));
                }
            }
            std::uint64_t const first = heroic ? 20000 : 12000;
            CHECK(swarms.size() >= 3);
            CHECK(swarms[0] == first && swarms[1] == first + 20000 && swarms[2] == first + 40000);
            CHECK(plagues.size() >= 4 && plagues[0] == 8000);
            for (std::size_t i = 1; i < plagues.size(); ++i)
                CHECK(plagues[i] - plagues[i - 1] >= 12000 && plagues[i] - plagues[i - 1] <= 16000);
        }
        // the rising: no more swarms; a plague due inside it waits for its end
        Timeline t;
        t.Start(false);
        t.SwarmRose(12000);
        t.Rising(9000);
        CHECK(!t.SwarmDue(100000));
        CHECK(!t.PlagueDue(8500) && t.PlagueDue(9000));
        // a refused cast tries again a second later
        t.PlagueRetry(9000);
        CHECK(!t.PlagueDue(9500) && t.PlagueDue(10000));
    }

    void TestStackMath()
    {
        // SP's own numbers: 110k (77k phase 1) at 1,431 group DPS rises him at 2 stacks; below about 1,250 at 3
        CHECK(StacksAtRising(Phase1Ms(110000, 1431.f), 30.f, false) == 2);
        CHECK(StacksAtRising(Phase1Ms(110000, 1200.f), 30.f, false) == 3);
        // arrivals 21.5, 41.5, 61.5 s (normal), 28, 48, 68 s (heroic)
        CHECK(ArrivalMs(0, 30.f, false) == 21500 && ArrivalMs(2, 30.f, false) == 61500);
        CHECK(ArrivalMs(0, 30.f, true) == 28000 && ArrivalMs(1, 30.f, true) == 48000);
        // section 3.6 at the built health: a bot group (2,500) still rises him at 2 on normal, the design's own target
        // (1,431) at 4; heroic at 5,000 bot DPS at 4, the target (3,145) at 6
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(false), 2500.f), 30.f, false) == 2);
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(false), 1431.f), 30.f, false) == 4);
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(true), 5000.f), 30.f, true) == 4);
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(true), 3145.f), 30.f, true) == 6);
        // the edge the report names: at 5,500 phase 1 ends at 47.5 s, half a second before the second pair (48 s)
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(true), 5500.f), 30.f, true) == 2);
        // normal's cap holds a slow group at 5
        CHECK(StacksAtRising(Phase1Ms(Health::kTheka(false), 600.f), 30.f, false) == 5);
    }
}

int main()
{
    TestSliceAndTexts();
    TestCourtyard();
    TestRisePicks();
    TestClosingAndTurning();
    TestStacksAndHunts();
    TestPlague();
    TestTimeline();
    TestStackMath();
    return Report("zf_theka_test");
}
