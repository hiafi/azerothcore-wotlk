// Host tests for OggleflintLogic.h (D1: Oggleflint): the slice and the arena, the timeline (the cadence of every beat,
// the 3 s between a hunt and a swing, the swing and the Beating apart, no beat starving), the Borer count over time and
// against the player count, the picks, the Beating's chain, the space and speed facts the build leans on.
#include "OggleflintLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <set>

using namespace RagefireChasmRework;
using namespace RfcOggleflint;

namespace
{
    struct Sim
    {
        std::vector<std::uint64_t> swings;
        std::vector<std::uint64_t> hunts;
        std::vector<std::uint64_t> beatings;
        std::vector<std::uint64_t> beatingEnds;
        std::uint32_t skipped = 0;
        std::uint32_t borers = 1;
        std::vector<std::uint64_t> joins;
        std::vector<std::size_t> sent;
    };

    // The AI's loop on its own timeline, `players` in the den, `tick` ms an update.
    Sim Run(bool heroic, std::uint64_t ms, std::uint32_t players, std::uint32_t tick)
    {
        Sim s;
        Timeline t;
        t.Start(heroic);
        BeatingChain chain;
        std::uint32_t beaten = 0;
        std::uint32_t seed = 12345;
        auto rand = [&seed](std::uint32_t n)
        {
            seed = seed * 1103515245u + 12345u;
            return (seed >> 16) % n;
        };
        std::vector<std::uint32_t> ids;
        for (std::uint32_t i = 1; i <= players; ++i)
            ids.push_back(i);
        std::vector<std::pair<std::uint32_t, std::uint64_t>> hunted;    // player, until
        for (std::uint64_t now = 0; now <= ms; now += tick)
        {
            std::erase_if(hunted, [now](auto const& h) { return now >= h.second; });
            std::vector<std::uint32_t> out;
            for (auto const& h : hunted)
                out.push_back(h.first);
            if (chain.active && now >= chain.LandMs())
            {
                if (chain.Last())
                {
                    chain.Stop();
                    beaten = 0;
                    t.BeatingEnded(now);
                    s.beatingEnds.push_back(now);
                }
                else
                    chain.Marked(now);
            }
            if (t.BorerMark(now))
            {
                t.BorerMarkPassed(now);
                if (BorerMayJoin(s.borers, players, chain.active))
                {
                    ++s.borers;
                    s.joins.push_back(now);
                }
            }
            if (t.BeatingMayStart(now))
            {
                t.BeatingBeat(now);
                auto const pick = PickDistinctIds(ids, out, 1, rand);
                if (pick.empty())
                    ++s.skipped;
                else
                {
                    CHECK(std::find(out.begin(), out.end(), pick[0]) == out.end());
                    beaten = pick[0];
                    chain.Start();
                    t.BeatingStarted();
                    chain.Marked(now);
                    s.beatings.push_back(now);
                }
            }
            if (t.HuntMayStart(now))
            {
                t.HuntStarted(now);
                s.hunts.push_back(now);
                std::vector<std::uint32_t> excluded = out;
                if (chain.active)
                    excluded.push_back(beaten);
                auto const picks = PickDistinctIds(ids, excluded, s.borers, rand);
                CHECK(std::set<std::uint32_t>(picks.begin(), picks.end()).size() == picks.size());
                if (chain.active)
                    CHECK(std::find(picks.begin(), picks.end(), beaten) == picks.end());
                s.sent.push_back(picks.size());
                for (std::uint32_t p : picks)
                    hunted.emplace_back(p, now + Tune::kChaseMs + Tune::kEruptionWarnMs);
            }
            if (t.SwingMayStart(now))
            {
                CHECK(!chain.active);
                t.SwingStarted(now);
                s.swings.push_back(now);
            }
        }
        return s;
    }

    std::uint64_t MaxGap(std::vector<std::uint64_t> const& v)
    {
        std::uint64_t gap = 0;
        for (std::size_t i = 1; i < v.size(); ++i)
            gap = std::max(gap, v[i] - v[i - 1]);
        return gap;
    }

    std::uint64_t Apart(std::vector<std::uint64_t> const& a, std::vector<std::uint64_t> const& b)
    {
        std::uint64_t least = ~std::uint64_t(0);
        for (std::uint64_t x : a)
            for (std::uint64_t y : b)
                least = std::min(least, x > y ? x - y : y - x);
        return least;
    }

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSkeleton()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(OggleflintArena().Contains(kOggleflintSpawn.XY(), kOggleflintSpawn.z));
        CHECK(ArenaFor(BOSS_OGGLEFLINT).Contains(kOggleflintSpawn.XY(), kOggleflintSpawn.z));
        CHECK(OggleflintArena().Contains(kDenTankSpot.XY(), kDenTankSpot.z));
        CHECK(OggleflintArena().Contains(kDenNeck.XY(), kDenNeck.z));
        // The jump-in ledges are not the fight's (section 7 #13 A).
        CHECK(!OggleflintArena().Contains({ -157.f, 24.f }, -21.3f));
        CHECK(!OggleflintArena().Contains({ -145.f, 20.f }, -18.f));
        CHECK(Tune::kHealth.normal == 60 * 356);
        CHECK(Tune::kHealth.heroic == 104 * 3052);
    }

    void TestNumbers()
    {
        // Build spec OG1 to OG4.
        CHECK(Tune::kHuntEveryMs.normal == 15000 && Tune::kHuntEveryMs.heroic == 12000);
        CHECK(Tune::kEruptionPct.normal == 30.f && Tune::kEruptionPct.heroic == 45.f);
        CHECK(Tune::kSwingPct.normal == 30.f && Tune::kSwingPct.heroic == 40.f);
        CHECK(Tune::kSwingTankPct == 10.f && Tune::kBeatingPct == 35.f && Tune::kBeatingBlows == 3);
        // The drill's rows borer-den and beating-chain (mod-boss-mechanics MechanicDrill.h): kRfcTagChase,
        // kRfcTagErupt, kRfcTagBlow, kMoundYd, kMoundLifeMs, kMoundArmMs, kMoundSpeed*, kEruptYd, kEruptMs, kBlowYd,
        // kBlowMs.
        CHECK(TAG_OG_CHASE == 1 && TAG_OG_ERUPTION == 2 && TAG_OG_BLOW == 3 && TAG_OG_SWING > 17);
        CHECK(Tune::kChaseRadius == 3.f && Tune::kChaseMs == 4000 && kChaseArmMs == 500 && kChaseStandsMs == 3500);
        CHECK(Tune::kChaseSpeed.normal == 4.f && Tune::kChaseSpeed.heroic == 5.f);
        CHECK(Tune::kEruptionRadius == 4.f && Tune::kEruptionWarnMs == 2000);
        CHECK(Tune::kBeatingRadius == 3.f && Tune::kBeatingBlowMs == 1500);
        // The mound is slower than a run; a runner clears the 4 yd ring in its 2 s, the 3 yd blow in its 1.5 s.
        CHECK(Tune::kChaseSpeed.heroic < 7.f);
        CHECK(7.f * 2.f > Tune::kEruptionRadius && 7.f * 1.5f > Tune::kBeatingRadius);
        // The throw is straight up, peaks under 3 yd (inside the arena's band) and never hurts on landing.
        CHECK(Near(KnockUpPeakYd(kKnockUpSpeedZ), 2.592f, 0.01f));
        CHECK(KnockUpAirSec(kKnockUpSpeedZ) < 1.1f);
        CHECK(kDenFloorZ + KnockUpPeakYd(kKnockUpSpeedZ) < kDenZMax);
        CHECK(kWormScale >= 0.5f && kWormScale <= 0.7f);
    }

    void TestNormalTimeline()
    {
        for (std::uint32_t tick : { 50u, 100u, 400u })
        {
            Sim const s = Run(false, 180000, 5, tick);
            CHECK(s.beatings.empty() && s.joins.empty() && s.borers == 1);
            CHECK(s.swings.front() >= 6000 && s.swings.front() < 6000 + tick);
            CHECK(s.hunts.front() >= 10000 && s.hunts.front() < 10000 + tick);
            CHECK(Apart(s.swings, s.hunts) >= Tune::kHuntSwingGapMs);
            CHECK(MaxGap(s.swings) <= 12000 + Tune::kHuntSwingGapMs + 2 * tick);
            CHECK(MaxGap(s.hunts) <= 15000 + Tune::kHuntSwingGapMs + 2 * tick);
            CHECK(s.swings.size() >= 14 && s.hunts.size() >= 11);
        }
        // The kill at the target (60 s): four hunts and five swings.
        Sim const kill = Run(false, 60000, 5, 100);
        CHECK(kill.hunts.size() == 4 && kill.swings.size() == 5);
    }

    void TestHeroicTimeline()
    {
        for (std::uint32_t tick : { 50u, 100u, 400u })
            for (std::uint32_t players : { 1u, 2u, 3u, 5u })
            {
                Sim const s = Run(true, 400000, players, tick);
                CHECK(Apart(s.swings, s.hunts) >= Tune::kHuntSwingGapMs);
                // Rule 24: nothing starves. A swing waits at most for a Beating, its tail and a hunt's gap.
                CHECK(MaxGap(s.swings) <= 12000 + kBeatingMs + kSwingAfterBeatingMs + Tune::kHuntSwingGapMs + 4 * tick);
                CHECK(MaxGap(s.hunts) <= 12000 + Tune::kHuntSwingGapMs + 2 * tick);
                CHECK(s.swings.size() >= 30 && s.hunts.size() >= 32);
                // The Beating's beats: every 20 s from 15 s, run or skipped.
                CHECK(s.beatings.size() + s.skipped >= 19 && s.beatings.size() + s.skipped <= 20);
                // Alone and hunted half the time, two of three are skipped (LCM of 12 and 20 s).
                CHECK(s.beatings.size() >= 6 && (players == 1 || s.beatings.size() >= 8));
                // The swing's 2 s and the Beating never overlap.
                for (std::uint64_t swing : s.swings)
                    for (std::size_t i = 0; i < s.beatings.size(); ++i)
                    {
                        std::uint64_t const end = i < s.beatingEnds.size() ? s.beatingEnds[i] : ~std::uint64_t(0);
                        CHECK(swing >= end + kSwingAfterBeatingMs || swing + Tune::kSwingWarnMs <= s.beatings[i]);
                    }
            }
        Sim const s = Run(true, 76000, 5, 100);
        CHECK(s.beatings.front() == 15000);
        CHECK(s.borers == 2);       // a kill at the target sees two
    }

    void TestBorers()
    {
        Sim const s = Run(true, 400000, 5, 100);
        // 40, 80, 120 s, then the fifth while nobody is being beaten (the 160 s mark lies past the 155 s Beating).
        CHECK(s.joins.size() == 4);
        CHECK(s.joins[0] == 40000 && s.joins[1] == 80000 && s.joins[2] == 120000 && s.joins[3] >= 160000);
        CHECK(s.borers == 5);
        for (std::size_t n : s.sent)
            CHECK(n <= 5);
        CHECK(*std::max_element(s.sent.begin(), s.sent.end()) == 5);
        CHECK(s.skipped > 0);       // all five hunted: the Beating is skipped
        // The player-count rule.
        CHECK(Run(true, 400000, 1, 100).borers == 1);
        CHECK(Run(true, 400000, 2, 100).borers == 2);
        CHECK(BorerMayJoin(1, 5, false) && BorerMayJoin(4, 5, false) && !BorerMayJoin(5, 5, false));
        CHECK(BorerMayJoin(3, 5, true) && !BorerMayJoin(4, 5, true));
        CHECK(!BorerMayJoin(1, 1, false) && !BorerMayJoin(1, 0, false));
    }

    void TestPicks()
    {
        std::vector<int> const ids{ 1, 2, 3, 4, 5 };
        auto first = [](std::uint32_t) { return 0u; };
        auto last = [](std::uint32_t n) { return n - 1; };
        CHECK((PickDistinctIds(ids, {}, 2, first) == std::vector<int>{ 1, 2 }));
        CHECK((PickDistinctIds(ids, {}, 2, last) == std::vector<int>{ 5, 1 }));
        CHECK((PickDistinctIds(ids, { 1, 2, 3 }, 9, first) == std::vector<int>{ 4, 5 }));
        CHECK(PickDistinctIds(ids, ids, 1, first).empty());
        CHECK(PickDistinctIds(ids, {}, 0, first).empty());
        CHECK(PickDistinctIds(std::vector<int>{}, std::vector<int>{}, 1, first).empty());
    }

    void TestChain()
    {
        BeatingChain c;
        CHECK(!c.LeapDue(99999) && !c.Overdue(99999));
        c.Start();
        CHECK(!c.LeapDue(99999));       // nothing marked
        c.Marked(1000);
        CHECK(c.blow == 1 && c.LandMs() == 2500);
        CHECK(!c.LeapDue(1699) && c.LeapDue(1700));
        CHECK(c.FlightMs(1700) == 800 && c.FlightMs(2500) == 1 && c.FlightMs(9000) == 1);
        c.leapt = true;
        CHECK(!c.LeapDue(1800));
        CHECK(!c.Overdue(3499) && c.Overdue(3500));
        c.Marked(2500);
        CHECK(!c.leapt && !c.Last());
        c.Marked(4000);
        CHECK(c.Last() && c.LandMs() == 1000 + kBeatingMs);
        c.Stop();
        CHECK(!c.active && c.blow == 0);
        // The leap lands on time from anywhere in the den (26 yd: 33 yd/s), and never at a crawl the engine refuses.
        CHECK(Near(LeapSpeedXY(24.f, 800), 30.f));
        CHECK(LeapSpeedXY(0.5f, 800) >= 1.f);
        CHECK(LeapSpeedXY(0.f, 0) >= 1.f);
    }

    void TestLandings()
    {
        // A blow marked in the neck or past it lands on the den's floor (section 7 #24 A).
        for (Vec2 p : { Vec2{ -149.f, 10.f }, Vec2{ -149.f, 2.f }, Vec2{ -165.f, 36.f }, Vec2{ -130.f, 40.f },
            Vec2{ -150.f, 60.f }, Vec2{ -157.f, 24.f }, kOggleflintSpawn.XY(), kDenTankSpot.XY() })
        {
            Vec2 const in = ClampInto(kDenFloorPolygon, p);
            CHECK(DenFloor().Contains(in, kDenFloorZ));
            CHECK(OggleflintArena().Contains(in, kDenFloorZ));
        }
        Vec2 const stays = ClampInto(kDenFloorPolygon, kDenDisc.XY());
        CHECK(stays.x == kDenDisc.x && stays.y == kDenDisc.y);
    }
}

int main()
{
    TestSkeleton();
    TestNumbers();
    TestNormalTimeline();
    TestHeroicTimeline();
    TestBorers();
    TestPicks();
    TestChain();
    TestLandings();
    return Report("rfc_oggleflint_test");
}
