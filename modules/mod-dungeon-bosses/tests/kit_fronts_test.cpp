// Host tests for the shared dungeon kit's wave 2 additions (Blackrock Spire WP-KT-B2): the rolling front plans
// (DungeonKitFrontLogic.h: timing, ring sequences, slices, pools, gaps, carriers) and the ring wall
// (DungeonKitRingLogic.h: geometry, crossings, the watch, the push-out, the grace). The BM parity of the mirrors is
// tests/kit_fronts_parity_test.cpp.
#include "DungeonKitFrontLogic.h"
#include "DungeonKitRingLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>

using namespace DungeonKit;

namespace
{
    bool Near(float a, float b, float tolerance = 1e-3f)
    {
        return std::fabs(a - b) <= tolerance;
    }

    bool AngleNear(float a, float b, float tolerance = 1e-3f)
    {
        return std::fabs(Fronts::WrapPi(a - b)) <= tolerance;
    }

    // ---- rolling fronts -------------------------------------------------------------------------------------------

    void TestTiming()
    {
        // Emberseer at 0 stacks: nova 7 yd, band 4, 8 yd/s.
        CHECK(Fronts::ReachMs(7.f, 4.f, 8.f, 15.f) == 500);     // outer edge 11 -> 15
        CHECK(Fronts::ReachMs(7.f, 4.f, 8.f, 9.f) == 0);        // already over it at the launch
        CHECK(Fronts::PassMs(7.f, 8.f, 21.f) == 1750);          // inner edge 7 -> 21 (EM6's flare)
        CHECK(Fronts::OverMs(7.f, 45.f, 8.f) == 4750);
        CHECK(Fronts::OverMs(7.f, 45.f, 0.f) == 0);
        // Rend: 86 yd at 8 yd/s, band 4.
        CHECK(Fronts::WallOverMs(86.f, 8.f) == 10750);
        CHECK(Fronts::WallReachMs(4.f, 8.f, 44.f) == 5000);
        CHECK(Fronts::WallPassMs(8.f, 44.f) == 5500);
    }

    void TestSlices()
    {
        CHECK(AngleNear(Fronts::SliceBearing(0.f, 0, 45.f), 0.f));
        CHECK(AngleNear(Fronts::SliceBearing(0.f, 1, 45.f), -kPi / 4.f));       // clockwise
        CHECK(AngleNear(Fronts::SliceBearing(0.f, 4, 45.f), kPi));
        CHECK(AngleNear(Fronts::SliceBearing(3.f, 3, 60.f), 3.f - kPi));
        CHECK(std::fabs(Fronts::SliceBearing(3.f, 7, 60.f)) <= kPi + 1e-4f);    // wrapped

        CHECK(AngleNear(Fronts::SliceAwayFrom({ 0.f, 0.f }, { -5.f, 0.f }), 0.f));   // tank west: slice east
        CHECK(AngleNear(Fronts::SliceAwayFrom({ 0.f, 0.f }, { 0.f, 5.f }), -kPi / 2.f));
        CHECK(Near(Fronts::SliceAwayFrom({ 1.f, 1.f }, { 1.f, 1.f }), 0.f));

        CHECK(Fronts::InSlice(0.4f, 0.f, 60.f));
        CHECK(!Fronts::InSlice(0.6f, 0.f, 60.f));
        CHECK(Fronts::InSlice(kPi - 0.1f, -kPi + 0.1f, 30.f));                      // across the wrap
    }

    void TestRingPlan()
    {
        Fronts::RingSequenceSpec s;
        s.rings = 3;
        s.firstSlice = 1.f;
        s.turnDeg = 45.f;
        s.sliceDeg = 60.f;
        s.startYd = 7.f;
        std::vector<Fronts::RingStep> const plan = Fronts::PlanRings(s);
        CHECK(plan.size() == 3);
        if (plan.size() == 3)
        {
            CHECK(plan[0].registerMs == 0 && plan[0].launchMs == 2500 && plan[0].WarnMs() == 2500);
            CHECK(plan[1].registerMs == 2500 && plan[1].launchMs == 4500 && plan[1].WarnMs() == 2000);
            CHECK(plan[2].registerMs == 4500 && plan[2].launchMs == 6500);
            CHECK(plan[0].overMs == 2500 + 4750);
            CHECK(AngleNear(plan[1].sliceBearing, 1.f - kPi / 4.f));
            CHECK(AngleNear(plan[2].sliceBearing, 1.f - kPi / 2.f));
            for (Fronts::RingStep const& r : plan)
                CHECK(Near(r.startYd, 7.f));
            CHECK(Fronts::LastPassMs(plan, s, 21.f) == 6500 + 1750);
            CHECK(Fronts::FirstReachMs(plan, s, 15.f) == 3000);
            CHECK(Fronts::SequenceOverMs(plan) == 6500 + 4750);
        }

        // Heroic: 4 rings 1.5 s apart, slice 45, turn 60; every ring registered at once.
        s.rings = 4;
        s.turnDeg = 60.f;
        s.sliceDeg = 45.f;
        s.spacingMs = 1500;
        s.revealAtPreviousLaunch = false;
        std::vector<Fronts::RingStep> const h = Fronts::PlanRings(s);
        CHECK(h.size() == 4);
        for (Fronts::RingStep const& r : h)
        {
            CHECK(r.registerMs == 0);
            CHECK(r.launchMs == 2500 + r.index * 1500);
            CHECK(AngleNear(r.sliceBearing, Fronts::SliceBearing(1.f, r.index, 60.f)));
        }

        // RF question 2: later rings from the apex.
        s.laterStartYd = 0.f;
        std::vector<Fronts::RingStep> const a = Fronts::PlanRings(s);
        CHECK(a.size() == 4 && Near(a[0].startYd, 7.f) && Near(a[1].startYd, 0.f) && Near(a[3].startYd, 0.f));
        CHECK(a.size() == 4 && a[1].overMs == a[1].launchMs + Fronts::OverMs(0.f, 45.f, 8.f));
        CHECK(Fronts::LastPassMs(a, s, 21.f) == a[3].launchMs + Fronts::PassMs(0.f, 8.f, 21.f));

        // User rulings (HANDOFF section 10, rolling fronts): ring 0 shown 5 s ahead from the nova's edge, rings 1+
        // from the apex; the nova (2.5 s) is cued 2.5 s in, so it erupts as ring 0 launches.
        Fronts::RingSequenceSpec ru;
        ru.rings = 3;
        ru.firstSlice = -2.f;
        ru.startYd = 9.1f;
        ru.laterStartYd = 0.f;
        ru.firstWarnMs = 5000;
        std::vector<Fronts::RingStep> const rp = Fronts::PlanRings(ru);
        CHECK(rp.size() == 3);
        if (rp.size() == 3)
        {
            CHECK(rp[0].registerMs == 0 && rp[0].launchMs == 5000 && Near(rp[0].startYd, 9.1f));
            CHECK(rp[0].launchMs - 2500 == 2500);       // the nova's cue
            CHECK(rp[1].registerMs == 5000 && rp[1].launchMs == 7000 && Near(rp[1].startYd, 0.f));
            CHECK(rp[2].registerMs == 7000 && rp[2].launchMs == 9000 && Near(rp[2].startYd, 0.f));
            CHECK(Fronts::LastPassMs(rp, ru, 21.f) == 9000 + 2625);
        }

        // Refused plans.
        Fronts::RingSequenceSpec bad;
        bad.rings = 0;
        CHECK(Fronts::PlanRings(bad).empty());
        bad = {};
        bad.sliceDeg = 340.f;
        CHECK(Fronts::PlanRings(bad).empty());
        bad = {};
        bad.startYd = 50.f;
        CHECK(Fronts::PlanRings(bad).empty());
        bad = {};
        bad.speed = 0.f;
        CHECK(Fronts::PlanRings(bad).empty());
        bad = {};
        bad.bandYd = 0.2f;
        CHECK(Fronts::PlanRings(bad).empty());
        CHECK(Fronts::LastPassMs({}, bad, 21.f) == 0);
        CHECK(Fronts::FirstReachMs({}, bad, 15.f) == 0);
    }

    // Rend's arena: from the portcullis (x 194) west to the way-in door, 86 yd, 68 yd across at the end bays.
    Fronts::WallFrame RendFrame()
    {
        return { { 194.f, -420.f }, kPi, 86.f, 68.f };
    }

    void TestWallFrame()
    {
        Fronts::WallFrame const f = RendFrame();
        Fronts::WallCoords const c = Fronts::ToWallCoords(f, { 150.f, -410.f });
        CHECK(Near(c.s, 44.f));
        CHECK(Near(c.t, -10.f));                    // facing west, left is south (-y): north of the axis is negative
        Vec2 const back = Fronts::FromWallCoords(f, c.s, c.t);
        CHECK(Near(back.x, 150.f) && Near(back.y, -410.f));

        auto b = Fronts::PoolBlocks(f, { { 150.f, -410.f }, 3.f }, 1.f);
        CHECK(b && Near(b->first, -14.f) && Near(b->second, -6.f));
        CHECK(!Fronts::PoolBlocks(f, { { 200.f, -420.f }, 3.f }));             // behind the start line
        CHECK(!Fronts::PoolBlocks(f, { { 100.f, -420.f }, 3.f }));             // past the travel
        CHECK(Fronts::PoolBlocks(f, { { 106.f, -420.f }, 3.f }).has_value());   // reaches the last 3 yd
        std::vector<Fronts::PoolCircle> const pools{ { { 150.f, -410.f }, 3.f }, { { 200.f, -420.f }, 3.f },
            { { 170.f, -430.f }, 6.f } };
        CHECK(Fronts::PoolBlocksAll(f, pools).size() == 2);
    }

    void TestPlaceGap()
    {
        // 40 yd wall, 8 yd gap: centres in [-16, 16].
        for (float u : { 0.f, 0.25f, 0.5f, 0.99f })
        {
            auto g = Fronts::PlaceGap(40.f, 8.f, {}, u);
            CHECK(g && *g >= -16.f - 1e-3f && *g <= 16.f + 1e-3f);
        }
        CHECK(Near(*Fronts::PlaceGap(40.f, 8.f, {}, 0.f), -16.f));
        CHECK(Near(*Fronts::PlaceGap(40.f, 8.f, {}, 0.5f), 0.f, 0.01f));
        CHECK(*Fronts::PlaceGap(40.f, 8.f, {}, 0.3f, 1) >= 0.f);
        CHECK(*Fronts::PlaceGap(40.f, 8.f, {}, 0.7f, -1) <= 0.f);
        CHECK(!Fronts::PlaceGap(6.f, 8.f, {}, 0.5f));                         // does not fit
        // Edges: 1 yd inside the ends.
        CHECK(Near(*Fronts::PlaceGap(40.f, 8.f, {}, 0.f, 0, 1.f), -15.f));
        // Blocked [-20, 0]: centres from 4.
        auto g = Fronts::PlaceGap(40.f, 8.f, { { -20.f, 0.f } }, 0.f);
        CHECK(g && Near(*g, 4.f));
        CHECK(Fronts::GapClear(4.f, 8.f, { { -20.f, 0.f } }));
        // Fully blocked.
        CHECK(!Fronts::PlaceGap(40.f, 8.f, { { -20.f, 20.f } }, 0.5f));
        // Within 5 of 10.
        auto w = Fronts::PlaceGap(40.f, 8.f, {}, 0.99f, 0, 0.f, 10.f, 5.f);
        CHECK(w && *w <= 15.f + 1e-3f && *w >= 5.f - 1e-3f);
        CHECK(Fronts::SideOf(3.f) == 1 && Fronts::SideOf(-3.f) == -1 && Fronts::SideOf(0.f) == 0);
    }

    void TestWallGaps()
    {
        Fronts::WallFrame const f = RendFrame();
        Fronts::WallGapSpec g;          // 8 yd gap, 40 yd span in the 68 yd wall, 1 yd edge, other side within 20
        g.spanYd = 40.f;

        // One wall, no pools: inside the main strip.
        for (float u : { 0.f, 0.3f, 0.6f, 0.99f })
        {
            Fronts::GapPick const p = Fronts::PlaceWallGap(f, g, {}, std::nullopt, u);
            CHECK(std::fabs(p.centre) <= 15.f + 1e-3f);
            CHECK(p.offPools && p.keptSide && p.keptWithin);
        }

        // Heroic: two walls; the second on the other side, within 20.
        float const rolls[] = { 0.9f, 0.1f };
        std::vector<Fronts::GapPick> const two = Fronts::PlanWallGaps(f, g, 2, {}, rolls);
        CHECK(two.size() == 2);
        if (two.size() == 2)
        {
            CHECK(Fronts::SideOf(two[0].centre) == -Fronts::SideOf(two[1].centre) || Fronts::SideOf(two[0].centre)
                == 0);
            CHECK(std::fabs(two[0].centre - two[1].centre) <= 20.f + 1e-3f);
            CHECK(two[1].keptSide && two[1].keptWithin);
        }

        // Pools placed in the wall's frame (s along the travel, t across).
        auto pool = [&f](float sAt, float t, float r)
        {
            return Fronts::PoolCircle{ Fronts::FromWallCoords(f, sAt, t), r };
        };

        // One pool on the right: the first gap avoids it whatever the roll.
        std::vector<Fronts::PoolCircle> const one{ pool(40.f, -8.f, 6.f) };
        for (float u : { 0.f, 0.3f, 0.6f, 0.99f })
        {
            Fronts::GapPick const p = Fronts::PlaceWallGap(f, g, one, std::nullopt, u);
            CHECK(p.offPools && Near(p.poolAreaSqYd, 0.f));
            CHECK(p.centre >= -15.f - 1e-3f);
        }
        CHECK(Fronts::LanePoolArea(f, one, 0.f, -8.f, 8.f) > 80.f);    // the lane through its middle: most of it
        CHECK(Near(Fronts::LanePoolArea(f, one, 0.f, 10.f, 8.f), 0.f));
        CHECK(Fronts::LanePoolArea(f, one, 1.f, -8.f, 30.f) > 3.14f * 49.f * 0.95f);    // the whole disc (r 7)

        // The other side wholly under pools (centres -15..0 blocked): the side and the distance are kept, the lane
        // with the least pool floor is taken, and reported.
        std::vector<Fronts::PoolCircle> const right{ pool(40.f, -12.f, 6.f), pool(60.f, -2.f, 6.f) };
        Fronts::GapPick const second = Fronts::PlaceWallGap(f, g, right, 5.f, 0.5f);
        CHECK(!second.offPools && second.poolAreaSqYd > 0.f);
        CHECK(second.keptSide && second.keptWithin);
        CHECK(second.centre <= 0.f + 1e-3f && second.centre >= -15.f - 1e-3f);
        for (float x = -15.f; x <= 0.f; x += 0.5f)
            CHECK(second.poolAreaSqYd <= Fronts::LanePoolArea(f, right, g.poolMarginYd, x, g.gapYd) + 0.51f);

        // Everything under pools: still a gap, in the span, reported.
        std::vector<Fronts::PoolCircle> all;
        for (float t = -18.f; t <= 18.f; t += 6.f)
            all.push_back(pool(30.f + t, t, 6.f));
        Fronts::GapPick const forced = Fronts::PlaceWallGap(f, g, all, std::nullopt, 0.5f);
        CHECK(!forced.offPools);
        CHECK(std::fabs(forced.centre) <= 15.f + 1e-3f);

        // A span off the centreline (spanCentre 5): centres in [-10, 20].
        Fronts::WallGapSpec off = g;
        off.spanCentreYd = 5.f;
        CHECK(Near(Fronts::PlaceWallGap(f, off, {}, std::nullopt, 0.f).centre, -10.f));
        CHECK(Near(Fronts::PlaceWallGap(f, off, {}, std::nullopt, 0.9999f).centre, 20.f, 0.01f));
        // A span narrower than the gap: its middle.
        Fronts::WallGapSpec narrow = g;
        narrow.spanYd = 6.f;
        CHECK(Near(Fronts::PlaceWallGap(f, narrow, {}, std::nullopt, 0.3f).centre, 0.f));

        // Random layouts (0-9 pools of 6 yd over the arena): the gap is always in the span; off the pools whenever it
        // says so and whenever the strict rule could be kept; the second wall always keeps the side and the distance.
        std::mt19937 rng(7);
        std::uniform_real_distribution<float> U(0.f, 1.f);
        for (uint32_t i = 0; i < 3000; ++i)
        {
            std::vector<Fronts::PoolCircle> pools;
            uint32_t const n = static_cast<uint32_t>(U(rng) * 10.f);
            for (uint32_t k = 0; k < n; ++k)
                pools.push_back({ { 110.f + U(rng) * 80.f, -440.f + U(rng) * 40.f }, 6.f });
            std::vector<std::pair<float, float>> const blocked = Fronts::PoolBlocksAll(f, pools, g.poolMarginYd);
            float const r2[] = { U(rng), U(rng) };
            std::vector<Fronts::GapPick> const picks = Fronts::PlanWallGaps(f, g, 2, pools, r2);
            CHECK(picks.size() == 2);
            for (std::size_t k = 0; k < picks.size(); ++k)
            {
                Fronts::GapPick const& p = picks[k];
                CHECK(p.centre >= -15.f - 1e-3f && p.centre <= 15.f + 1e-3f);
                CHECK(p.offPools == Fronts::GapClear(p.centre, g.gapYd, blocked));
                CHECK(p.offPools == (p.poolAreaSqYd <= 1e-3f));
                std::optional<float> const prev = k ? std::optional<float>(picks[0].centre) : std::nullopt;
                int const side = (prev && Fronts::SideOf(*prev) != 0) ? -Fronts::SideOf(*prev) : 0;
                bool const strictFits = Fronts::PlaceGap(40.f, g.gapYd, blocked, 0.5f, side, g.edgeYd,
                    prev.value_or(0.f), prev ? g.withinYd : -1.f).has_value();
                if (strictFits)
                    CHECK(p.offPools);
                if (k == 1)
                {
                    CHECK(p.keptSide && p.keptWithin);
                    CHECK(std::fabs(p.centre - picks[0].centre) <= g.withinYd + 1e-3f);
                    if (Fronts::SideOf(picks[0].centre) != 0)
                        CHECK(Fronts::SideOf(p.centre) != Fronts::SideOf(picks[0].centre));
                }
            }
        }
    }

    void TestCarriers()
    {
        std::vector<std::pair<float, float>> const gap{ { 0.f, 8.f } };
        std::vector<float> const slots = Fronts::WallCarrierSlots(40.f, 6.f, gap);
        CHECK(slots.size() == 6);                   // two 16 yd segments, 3 each
        for (float t : slots)
        {
            CHECK(std::fabs(t) >= 4.f);
            CHECK(std::fabs(t) <= 20.f);
        }
        CHECK(Fronts::WallCarrierSlots(40.f, 6.f, gap, 4).size() == 4);
        CHECK(Fronts::WallCarrierSlots(40.f, 6.f, {}).size() == 7);
        CHECK(Fronts::WallCarrierSlots(0.f, 6.f, {}).empty());
        // A gap at the wall's end: one segment.
        std::vector<std::pair<float, float>> const endGap{ { 18.f, 8.f } };
        for (float t : Fronts::WallCarrierSlots(40.f, 5.f, endGap))
            CHECK(t <= 14.f);

        std::vector<float> const ring = Fronts::RingCarrierBearings(0.5f, 60.f, 9.f, 6.f);
        CHECK(ring.size() == static_cast<std::size_t>(std::ceil(Fronts::DegToRad(300.f) * 9.f / 6.f)));
        for (float b : ring)
            CHECK(!Fronts::InSlice(b, 0.5f, 60.f));
        CHECK(Fronts::RingCarrierBearings(0.5f, 60.f, 40.f, 6.f, 12).size() == 12);
        CHECK(Fronts::RingCarrierBearings(0.f, 0.f, 10.f, 6.f).size() == 11);   // full ring
    }

    // ---- ring wall ------------------------------------------------------------------------------------------------

    RingWall TestRing()
    {
        return { { 0.f, 0.f }, 12.f, 2.f };
    }

    void TestRingGeometry()
    {
        RingWall const w = TestRing();
        CHECK(Near(w.Inner(), 11.f) && Near(w.Outer(), 13.f));
        CHECK(Near(RingClearance(w, { 12.f, 0.f }), -1.f));
        CHECK(Near(RingClearance(w, { 0.f, 5.f }), 6.f));
        CHECK(Near(RingClearance(w, { 0.f, -20.f }), 7.f));
        CHECK(InsideRingBand(w, { 11.f, 0.f }) && InsideRingBand(w, { 0.f, 13.f }));
        CHECK(!InsideRingBand(w, { 10.9f, 0.f }));
        CHECK(InsideRing(w, { 10.9f, 0.f }) && !InsideRing(w, { 11.f, 0.f }));
        RingWall const thin{ { 0.f, 0.f }, 1.f, 4.f };
        CHECK(Near(thin.Inner(), 0.f));
    }

    void TestRingCrossings()
    {
        RingWall const w = TestRing();
        CHECK(CrossesRing(w, { 5.f, 0.f }, { 15.f, 0.f }));       // out
        CHECK(CrossesRing(w, { 15.f, 0.f }, { 5.f, 0.f }));       // in
        CHECK(CrossesRing(w, { -15.f, 1.f }, { 15.f, 1.f }));     // straight through
        CHECK(!CrossesRing(w, { -5.f, 0.f }, { 5.f, 3.f }));      // a chord inside
        CHECK(!CrossesRing(w, { -15.f, 14.f }, { 15.f, 14.f }));  // outside, never in
        CHECK(!CrossesRing(w, { 0.f, 0.f }, { 50.f, 0.f }));      // a teleport
        CHECK(CrossesRing(w, { 14.f, 0.f }, { 0.f, 14.f }));       // a corner cut through the disc (9.9 yd in)
        CHECK(!CrossesRing(w, { 14.f, 0.f }, { 10.f, 10.f }));     // outside all the way (14.1 yd at the end)

        RingWatch watch(w);
        CHECK(!watch.Observe(1, { 5.f, 0.f }));
        CHECK(!watch.Observe(2, { 20.f, 0.f }));
        watch.Sweep();
        CHECK(watch.Observe(1, { 16.f, 0.f }));                  // walked out
        CHECK(!watch.Observe(2, { 21.f, 0.f }));
        watch.Sweep();
        CHECK(watch.Size() == 2);
        CHECK(!watch.Observe(2, { 22.f, 0.f }));
        watch.Sweep();                                          // 1 not seen: forgotten
        CHECK(watch.Size() == 1);
        CHECK(!watch.Observe(1, { 0.f, 0.f }));                  // back (a res): no crossing
    }

    void TestPushOut()
    {
        RingWall const w = TestRing();
        // At the close: inside the outer edge (plus 0.5) unless kept in.
        CHECK(PushOutNeeded(w, { 3.f, 0.f }, false, true));
        CHECK(PushOutNeeded(w, { 13.4f, 0.f }, false, true));
        CHECK(!PushOutNeeded(w, { 13.6f, 0.f }, false, true));
        CHECK(!PushOutNeeded(w, { 3.f, 0.f }, true, true));
        // Later: only inside the disc.
        CHECK(PushOutNeeded(w, { 3.f, 0.f }, false, false));
        CHECK(!PushOutNeeded(w, { 12.f, 0.f }, false, false));

        PushOut const p = PlanPushOut(w, { 6.f, 0.f });
        CHECK(Near(p.landing.x, 16.f) && Near(p.landing.y, 0.f));
        CHECK(Near(p.distance, 10.f));
        CHECK(Near(p.source.x, 5.f) && Near(p.source.y, 0.f));     // behind it, on the centre's side
        PushOut const c = PlanPushOut(w, { 0.f, 0.f }, 3.f, kPi / 2.f);
        CHECK(Near(c.landing.x, 0.f) && Near(c.landing.y, 16.f) && Near(c.distance, 16.f));
        PushOut const out = PlanPushOut(w, { 0.f, 20.f });
        CHECK(Near(out.distance, 0.f));                            // already clear

        float const xy = PushSpeedXY(10.f, 7.f);
        CHECK(Near(2.f * xy * 7.f / kRingGravity, 10.f));
        CHECK(Near(PushSpeedXY(10.f, 0.f), 0.f));
        CHECK(PushFlightMs(7.f) == 726);
        CHECK(PushFlightMs(7.f) + kRingPushGraceExtraMs < kRingArmMs);  // the close's pushes land before the arm

        GraceBook g;
        g.Grant(5, 1000);
        CHECK(g.Has(5, 999) && !g.Has(5, 1000) && !g.Has(6, 0));
        g.Grant(5, 800);                                        // never shortens
        CHECK(g.Has(5, 900));
        g.Prune(1000);
        CHECK(g.Size() == 0);
    }

    // The engine's tick order (DungeonKitRing.cpp TickRing) on a pushed unit flying over the band at 100 ms polls:
    // observed every poll, under grace no strike and no crossing; after the grace no crossing either.
    void TestPushFlightNoStrike()
    {
        RingWall const w = TestRing();
        RingWatch watch(w);
        GraceBook grace;
        Vec2 const from{ 4.f, 0.f };
        PushOut const p = PlanPushOut(w, from);
        uint32_t const flight = PushFlightMs();
        uint64_t const pushAt = 1000;
        grace.Grant(9, pushAt + flight + kRingPushGraceExtraMs);
        watch.Observe(9, from);
        watch.Sweep();
        uint32_t strikes = 0;
        for (uint64_t now = pushAt + 100; now <= pushAt + 3000; now += 100)
        {
            float const k = std::min(1.f, static_cast<float>(now - pushAt) / static_cast<float>(flight));
            Vec2 const at{ from.x + (p.landing.x - from.x) * k, from.y + (p.landing.y - from.y) * k };
            bool const crossed = watch.Observe(9, at);
            watch.Sweep();
            if (grace.Has(9, now))
                continue;
            if (crossed || InsideRingBand(w, at))
                ++strikes;
        }
        CHECK(strikes == 0);

        // Without the grace the same flight would be struck (the rule the grace exists for).
        RingWatch bare(w);
        bare.Observe(9, from);
        bare.Sweep();
        bool struck = false;
        for (uint64_t now = pushAt + 100; now <= pushAt + 1000; now += 100)
        {
            float const k = std::min(1.f, static_cast<float>(now - pushAt) / static_cast<float>(flight));
            Vec2 const at{ from.x + (p.landing.x - from.x) * k, from.y + (p.landing.y - from.y) * k };
            struck = struck || bare.Observe(9, at) || InsideRingBand(w, at);
            bare.Sweep();
        }
        CHECK(struck);
    }
}

int main()
{
    TestTiming();
    TestSlices();
    TestRingPlan();
    TestWallFrame();
    TestPlaceGap();
    TestWallGaps();
    TestCarriers();
    TestRingGeometry();
    TestRingCrossings();
    TestPushOut();
    TestPushFlightNoStrike();
    return Report("kit_fronts_test");
}
