// Host tests for IncendiusLogic.h (D11: Lord Incendius): the slice, the tuning, the causeway's geometry (the arena,
// the neck seals, the crumble steps, the bots' bounds, the surge strip, the Ember spots), the rebirth numbers and the
// beat clock.
#include "DungeonKitEdgeLogic.h"
#include "IncendiusLogic.h"
#include "check.h"
#include <cmath>
#include <span>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdIncendius;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool Inside(std::vector<Vec2> const& poly, Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(poly), p);
    }

    // Distance from `p` to the nearest edge of `poly`.
    float EdgeDistance(std::vector<Vec2> const& poly, Vec2 p)
    {
        return DungeonKit::NearestEdge(std::span<Vec2 const>(poly), p)->distance;
    }

    Vec2 Mid(Band const& b)
    {
        return { (b.from.x + b.to.x) * 0.5f, (b.from.y + b.to.y) * 0.5f };
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211140 && kSpellSlice.last == 211179);
        CHECK(SPELL_IN_CURSE == 211140);
        CHECK(SPELL_IN_CRUMBLING_GROUND == 211155);
        // Rule 15: the copies, never the stock ids.
        for (std::uint32_t id : { kStockCurse, kStockFieryBurst, kStockFireStorm, kStockMightyBlow })
            CHECK(!kSpellSlice.Contains(id));
    }

    void TestTuning()
    {
        // Section 3.6 / the build spec.
        CHECK(kBossHealth.normal == 100000 && kBossHealth.heroic == 160000);
        CHECK(kEmberHealth.normal == 6000 && kEmberHealth.heroic == 9000);
        CHECK(RebirthsFor(false) == 1 && RebirthsFor(true) == 2);
        CHECK(EmbersFor(false) == 4 && EmbersFor(true) == 5);
        CHECK(kCurseFirstMs == 16000 && kCurseEveryMs == 22000 && Near(kCurseFirePct, 10.f) && kCurseMs == 60000);
        CHECK(kBurstFirstMs == 9000 && kBurstMinMs == 9000 && kBurstMaxMs == 13000 && kBurstCastMs == 1500);
        CHECK(Near(kBurstRadiusYd, 10.f));
        CHECK(kFireStormFirstMs == 6000 && kFireStormEveryMs.normal == 10000 && kFireStormEveryMs.heroic == 8000);
        CHECK(kFireStormWarnMs == 2000 && kFireStormLifeMs == 30000 && Near(kFireStormRadiusYd, 5.f));
        CHECK(Near(kFireStormPct.normal, 4.f) && Near(kFireStormPct.heroic, 6.f));
        CHECK(kFistFirstMs == 12000 && kFistEveryMs == 20000 && kFistWarnMs == 2000 && Near(kFistThrowYd, 10.f));
        CHECK(Near(kFistPct.normal, 25.f) && Near(kFistPct.heroic, 40.f));
        CHECK(kSurgeFirstMs == 15000 && kSurgeEveryMs.normal == 25000 && kSurgeEveryMs.heroic == 20000);
        CHECK(kSurgeWarnMs == 3000 && Near(kSurgeWidthYd, 6.f));
        CHECK(Near(kSurgePct.normal, 30.f) && Near(kSurgePct.heroic, 45.f));
        CHECK(kReformMs == 12000 && kEmberRollMs == 10000 && kEmberRollMs < kReformMs);
        // The crumble lands as he stands up.
        CHECK(kBandWarnMs == 5000);
        CHECK(kBandRaiseAfterShatterMs + kBandWarnMs == kReformMs);
        // Under 50% the avoidable single hits carry Weakened (shared doc section 4); none of these is over 50%.
        CHECK(kFistPct.heroic < 50.f && kSurgePct.heroic < 50.f);
        // The drill's band tags (MechanicDrill.h kBrdTagEdgeBand / kBrdTagCrumble / kBrdTagSweep).
        CHECK(TAG_IN_NECK_SEAL == 13 && TAG_IN_CRUMBLE == 14 && TAG_IN_ARM_SWEEP == 15);
        CHECK(TAG_IN_FIRE_STORM != TAG_IN_MAGMA_FIST && TAG_IN_MAGMA_FIST != TAG_IN_LAVA_SURGE);
        // Text groups: 0-7 are D11's range (D12 owns 8-9).
        CHECK(YELL_IN_SHATTER == 0 && EMOTE_IN_BREATH == 7);
    }

    void TestRebirth()
    {
        CHECK(Near(RebornHealthPct(0), 40.f));
        CHECK(Near(RebornHealthPct(1), 50.f));
        CHECK(Near(RebornHealthPct(4), 80.f));
        CHECK(Near(RebornHealthPct(5), 90.f));
        CHECK(Near(RebornHealthPct(6), 100.f));
        CHECK(Near(RebornHealthPct(9), 100.f));
        CHECK(CrumbleStepsAfter(1) == 1 && CrumbleStepsAfter(2) == 2 && CrumbleStepsAfter(7) == kCrumbleMaxSteps);
        CHECK(Near(CrumbledDepth(0), 0.f) && Near(CrumbledDepth(1), 2.f) && Near(CrumbledDepth(2), 4.f));
        CHECK(Near(CrumbledDepth(3), 6.f) && Near(CrumbledDepth(9), 6.f));
        CHECK(Near(EmberSpeed(10.f), 1.f));
        CHECK(Near(EmberSpeed(0.f), kEmberMinSpeedYdS));
        CHECK(Near(FistLength(2.f), kFistMinLengthYd));
        CHECK(Near(FistLength(10.f), 18.f));
        CHECK(Near(FistLength(60.f), kFistMaxLengthYd));
        // R-1-B m3: from the near end, a far target still gets the whole overrun inside the line's 40 yd.
        CHECK(Near(FistStartOffset(10.f), 0.f));
        CHECK(Near(FistStartOffset(kFistMaxLengthYd - kFistOverrunYd), 0.f));
        for (float d : { 33.f, 36.f, 42.f, 48.f })
        {
            float const offset = FistStartOffset(d);
            CHECK(offset > 0.f);
            CHECK(Near(offset + FistLength(d - offset), d + kFistOverrunYd));
            CHECK(FistLength(d - offset) <= kFistMaxLengthYd + 0.01f);
        }
    }

    // R-1-B m4: past a sealed neck on the causeway, a player is put back onto the arena (never one in the lake, on the
    // arena or in the seal itself).
    void TestNeckGrip()
    {
        for (int side : { -1, 1 })
        {
            float const sign = float(side);
            for (float s : { 28.5f, 35.f, 50.f })
            {
                Vec2 const p = ToWorld(sign * s, MidlineAt(sign * s));
                CHECK(PastSealedNeck(p, kFloorZ) == side);
                CHECK(PastSealedNeck(p, kFloorZ + 1.f) == side);
                CHECK(PastSealedNeck(p, kFloorZ - 30.f) == 0);     // fallen: the FallWatch's
            }
            // On the arena or in the seal: no grip.
            for (float s : { 0.f, 20.f, 24.f, 26.f })
                CHECK(PastSealedNeck(ToWorld(sign * s, MidlineAt(sign * s)), kFloorZ) == 0);
            // Off the causeway's width (over the lake beside it): not this rule.
            CHECK(PastSealedNeck(ToWorld(sign * 35.f, ProfileAt(sign * 35.f).wHi + 5.f), kFloorZ) == 0);
            // Far down the corridor: not this fight's floor.
            CHECK(PastSealedNeck(ToWorld(sign * 70.f, MidlineAt(sign * 70.f)), kFloorZ) == 0);
            // The landing is on the arena, inside its neck's end, clear of the seal.
            Vec2 const land = NeckGripLanding(side);
            FramePoint const f = ToFrame(land);
            CHECK(f.s > kArenaSMin && f.s < kArenaSMax);
            CHECK(std::fabs(f.s) <= kArenaSMax - kNeckGripInsetYd + 0.01f);
            CHECK(Inside(ArenaFloor(), land));
            CHECK(PastSealedNeck(land, kFloorZ) == 0);
        }
        CHECK(kNeckGripGraceMs >= kNeckGripCheckMs);
    }

    void TestFrame()
    {
        // The frame: the spawn is s 0, w 0; the S0 tips are on the axis at s -8 and s 17.
        FramePoint const spawn = ToFrame(kIncendiusSpawn.XY());
        CHECK(Near(spawn.s, 0.f) && Near(spawn.w, 0.f));
        FramePoint const west = ToFrame(kIncendiusTipWest.XY());
        FramePoint const east = ToFrame(kIncendiusTipEast.XY());
        CHECK(Near(west.s, -8.f, 0.2f) && Near(west.w, 0.f, 0.3f));
        CHECK(Near(east.s, 17.f, 0.2f) && Near(east.w, 0.f, 0.3f));
        Vec2 const back = ToWorld(west.s, west.w);
        CHECK(Near(back.x, kIncendiusTipWest.x, 0.05f) && Near(back.y, kIncendiusTipWest.y, 0.05f));
        // The giant's spot (D12) is 28 yd off the axis over the lake, beside the Anvil.
        FramePoint const giant = ToFrame(kLakeLordSpot.XY());
        CHECK(Near(giant.s, 5.9f, 0.5f) && Near(giant.w, -28.f, 0.5f));
        FramePoint const anvil = ToFrame(kAnvil.XY());
        CHECK(Near(anvil.s, 5.9f, 0.3f) && Near(anvil.w, -3.2f, 0.3f));
    }

    void TestProfile()
    {
        for (std::size_t i = 0; i < kProfile.size(); ++i)
        {
            CHECK(kProfile[i].wLo < kProfile[i].wHi);
            if (i)
                CHECK(kProfile[i - 1].s < kProfile[i].s);
        }
        // NAVMESH 2.5: the bulge is about 22-25 yd at s 0-10, the necks 9-10 yd.
        CHECK(Near(ProfileAt(6.f).wHi - ProfileAt(6.f).wLo, 25.5f, 0.6f));
        CHECK(Near(ProfileAt(-15.f).wHi - ProfileAt(-15.f).wLo, 10.f, 1.2f));
        CHECK(Near(ProfileAt(24.f).wHi - ProfileAt(24.f).wLo, 10.f, 1.0f));
        CHECK(ProfileAt(-100.f).wLo == kProfile.front().wLo && ProfileAt(100.f).wHi == kProfile.back().wHi);

        std::vector<Vec2> const floor = CausewayFloor();
        CHECK(floor.size() == kProfile.size() * 2);
        std::vector<Vec2> const arena = ArenaFloor();
        // The spawn, the Anvil, the tips and the reform spot stand on the arena; the giant's spot does not.
        CHECK(Inside(arena, kIncendiusSpawn.XY()));
        CHECK(Inside(arena, kAnvil.XY()));
        CHECK(Inside(arena, kIncendiusTipWest.XY()));
        CHECK(Inside(arena, kIncendiusTipEast.XY()));
        CHECK(!Inside(floor, kLakeLordSpot.XY()));
        CHECK(Inside(arena, ReformSpot()));
        CHECK(Near(DungeonKit::Distance(ReformSpot(), kAnvil.XY()), kReformOffsetYd, 0.05f));
        // The S0 stub arena still holds the spawn and the tips (the leash now uses ArenaFloor: shared-file request).
        CHECK(IncendiusArena().Contains(kIncendiusSpawn.XY(), kIncendiusSpawn.z));
        CHECK(ArenaFor(BOSS_INCENDIUS).Contains(kIncendiusTipWest.XY(), kIncendiusTipWest.z));
        CHECK(ArenaFor(BOSS_INCENDIUS).Contains(kIncendiusTipEast.XY(), kIncendiusTipEast.z));
        // Every patrol point (waypoint_data 477330) is on the arena.
        for (Vec2 const p : { Vec2{ 888.783f, -266.98f }, Vec2{ 886.387f, -273.258f }, Vec2{ 888.873f, -279.984f },
                 Vec2{ 895.077f, -283.08f }, Vec2{ 903.96f, -276.264f }, Vec2{ 902.549f, -268.183f },
                 Vec2{ 893.001f, -264.676f } })
            CHECK(Inside(arena, p));
        // Section 7 #14 A: s -24 to +24 is about 685 sq yd on the mesh (this polygon adds the mesh's 0.5 yd shrink).
        float const area = PolygonArea(arena);
        CHECK(area > 660.f && area < 790.f);
    }

    void TestLongEdges()
    {
        std::vector<Vec2> const floor = CausewayFloor();
        for (std::size_t edge : kLongEdges)
        {
            CHECK(edge < floor.size());
            FramePoint const a = ToFrame(floor[edge]);
            FramePoint const b = ToFrame(floor[(edge + 1) % floor.size()]);
            CHECK(a.s >= kArenaSMin - 0.01f && a.s <= kArenaSMax + 0.01f);
            CHECK(b.s >= kArenaSMin - 0.01f && b.s <= kArenaSMax + 0.01f);
            CHECK(!Near(a.s, b.s, 0.5f));   // never a cap
        }
        // And every other edge leaves the arena (the two cap edges and the outer causeway).
        std::size_t outside = 0;
        for (std::size_t edge = 0; edge < floor.size(); ++edge)
        {
            bool listed = false;
            for (std::size_t e : kLongEdges)
                listed = listed || e == edge;
            if (listed)
                continue;
            FramePoint const a = ToFrame(floor[edge]);
            FramePoint const b = ToFrame(floor[(edge + 1) % floor.size()]);
            CHECK(std::fabs(a.s) > kArenaSMax + 1.f || std::fabs(b.s) > kArenaSMax + 1.f);
            ++outside;
        }
        CHECK(outside == 6);
    }

    void TestCrumbleBands()
    {
        std::vector<Vec2> const floor = CausewayFloor();
        for (std::uint32_t step = 1; step <= kCrumbleMaxSteps; ++step)
            for (std::size_t edge : kLongEdges)
            {
                Band const b = CrumbleBand(floor, edge, step);
                CHECK(Near(b.width, kCrumbleStepYd));
                // The band's middle sits (step - 0.5) * 2 yd inside its own edge, on the floor.
                Vec2 const m = Mid(b);
                CHECK(Inside(floor, m));
                float const along = DungeonKit::SegmentDistance(floor[edge], floor[(edge + 1) % floor.size()], m);
                CHECK(Near(along, CrumbledDepth(step) - kCrumbleStepYd * 0.5f, 0.05f));
                // Anyone in it is thrown over a real edge, never along the causeway.
                float const out = DungeonKit::OutwardBearing(std::span<Vec2 const>(floor), m);
                DungeonKit::EdgePush const push = DungeonKit::PlanOverEdge(std::span<Vec2 const>(floor), m, out);
                CHECK(push.overEdge);
                CHECK(!Inside(floor, push.landing));
                CHECK(push.distance < CrumbledDepth(step) + DungeonKit::kEdgeBeyondYd + 0.6f);
            }
    }

    void TestNeckSeals()
    {
        std::vector<Vec2> const floor = CausewayFloor();
        for (bool const east : { false, true })
        {
            Band const seal = NeckSeal(east);
            CHECK(Near(seal.width, kNeckSealWidthYd));
            FramePoint const a = ToFrame(seal.from);
            FramePoint const b = ToFrame(seal.to);
            float const s = east ? kArenaSMax + 2.f : kArenaSMin - 2.f;
            CHECK(Near(a.s, s, 0.05f) && Near(b.s, s, 0.05f));
            // Its inner edge is the arena's end; it reaches past both rims.
            CHECK(Near(std::fabs(s) - kNeckSealWidthYd * 0.5f, kArenaSMax, 0.01f));
            CHECK(!Inside(floor, seal.from) && !Inside(floor, seal.to));
            Vec2 const m = Mid(seal);
            CHECK(Inside(floor, m));
            // The way out of the neck is sideways (a fall), never along the causeway onto more floor.
            float const out = DungeonKit::OutwardBearing(std::span<Vec2 const>(floor), m);
            DungeonKit::EdgePush const push = DungeonKit::PlanOverEdge(std::span<Vec2 const>(floor), m, out);
            CHECK(push.overEdge);
            CHECK(std::fabs(ToFrame(push.landing).s - s) < 3.f);
            CHECK(push.distance < 10.f);
        }
    }

    void TestBounds()
    {
        std::vector<Vec2> const arena = ArenaFloor();
        float last = PolygonArea(arena);
        for (std::uint32_t steps = 0; steps <= kCrumbleMaxSteps; ++steps)
        {
            std::vector<Vec2> const safe = SafeFloor(steps);
            float const area = PolygonArea(safe);
            CHECK(area < last);
            last = area;
            // Every safe vertex keeps the margin from the crumbled edge (rule 5); a row whose two sides met sits on
            // one point (nothing safe there) and is skipped.
            std::vector<Vec2> const floor = CausewayFloor();
            std::size_t const rows = safe.size() / 2;
            for (std::size_t i = 0; i < rows; ++i)
            {
                Vec2 const lo = safe[i];
                Vec2 const hi = safe[safe.size() - 1 - i];
                FramePoint const f = ToFrame(lo);
                CHECK(f.s >= kArenaSMin + kBoundsMarginYd - 0.01f && f.s <= kArenaSMax - kBoundsMarginYd + 0.01f);
                CHECK(Near(ToFrame(hi).s, f.s, 0.01f));
                if (DungeonKit::Distance(lo, hi) < 0.01f)
                    continue;
                CHECK(EdgeDistance(floor, lo) >= CrumbledDepth(steps) + kBoundsMarginYd - 0.05f);
                CHECK(EdgeDistance(floor, hi) >= CrumbledDepth(steps) + kBoundsMarginYd - 0.05f);
            }
            // The Anvil's spot in the middle stays safe at every step.
            CHECK(Inside(safe, ToWorld(6.f, MidlineAt(6.f))));
            CHECK(Inside(safe, ReformSpot()));
        }
        // The bots' room (2 yd margin, slope-conservative inset): about 430 / 225 / 140 sq yd after 0 / 1 / 2 steps
        // (designer question 3: heroic's second rebirth with 30 s Fire Storms).
        CHECK(PolygonArea(SafeFloor(0)) > 400.f);
        CHECK(PolygonArea(SafeFloor(1)) > 200.f);
        CHECK(PolygonArea(SafeFloor(2)) > 120.f);
        // A point at the bulge's edge is never safe.
        CHECK(!Inside(SafeFloor(0), ToWorld(6.f, ProfileAt(6.f).wLo + 1.f)));
        CHECK(!Inside(SafeFloor(0), ToWorld(6.f, ProfileAt(6.f).wHi - 1.f)));
        // After two steps the west neck is closed to the bots (9.5 yd - 2 x 4 yd crumbled - margins).
        CHECK(!Inside(SafeFloor(2), ToWorld(-15.f, MidlineAt(-15.f))));
        CHECK(Inside(SafeFloor(0), ToWorld(-15.f, MidlineAt(-15.f))));
    }

    void TestSurge()
    {
        for (std::uint32_t steps = 0; steps <= 2; ++steps)
            for (Side const side : { Side::SouthEast, Side::NorthWest })
            {
                Band const strip = SurgeStrip(side, steps);
                CHECK(Near(strip.width, kSurgeWidthYd));
                FramePoint const a = ToFrame(strip.from);
                FramePoint const b = ToFrame(strip.to);
                CHECK(Near(a.s, kSurgeSMin, 0.05f) && Near(b.s, kSurgeSMax, 0.05f));
                CHECK(Near(a.w, b.w, 0.05f));
                ProfilePoint const widest = ProfileAt(kSurgeWidestS);
                float const depth = CrumbledDepth(steps);
                // Its outer side is the crumbled edge at the bulge's widest point; it never reaches the middle line.
                float const outer = side == Side::SouthEast ? a.w - kSurgeWidthYd * 0.5f : a.w + kSurgeWidthYd * 0.5f;
                float const edge = side == Side::SouthEast ? widest.wLo + depth : widest.wHi - depth;
                CHECK(Near(outer, edge, 0.05f));
                float const inner = side == Side::SouthEast ? a.w + kSurgeWidthYd * 0.5f : a.w - kSurgeWidthYd * 0.5f;
                float const mid = MidlineAt(kSurgeWidestS);
                CHECK(side == Side::SouthEast ? inner < mid : inner > mid);
                CHECK(SideOf(Mid(strip)) == side);
            }
        CHECK(PickSurgeSide(3, 1, 1) == Side::SouthEast);
        CHECK(PickSurgeSide(0, 2, 0) == Side::NorthWest);
        CHECK(PickSurgeSide(2, 2, 0) == Side::SouthEast);
        CHECK(PickSurgeSide(2, 2, 1) == Side::NorthWest);
    }

    void TestEmbers()
    {
        std::vector<Vec2> const floor = CausewayFloor();
        for (bool const heroic : { false, true })
            for (std::uint32_t steps = 0; steps <= 2; ++steps)
            {
                std::vector<Vec2> const spots = EmberSpots(EmbersFor(heroic), steps);
                CHECK(spots.size() == EmbersFor(heroic));
                for (std::size_t i = 0; i < spots.size(); ++i)
                {
                    Vec2 const p = spots[i];
                    CHECK(Inside(ArenaFloor(), p));
                    // Never in a band: the edge slots keep the inset past the crumbled edge, square to it; the neck's
                    // middle slot (heroic) stays clear of both sides' bands.
                    float const d = EdgeDistance(floor, p);
                    CHECK(d >= CrumbledDepth(steps) + (kEmberSlots[i].w != 0.f ? kEmberEdgeInsetYd - 0.05f : 0.5f));
                    float const toAnvil = DungeonKit::Distance(p, kAnvil.XY());
                    CHECK(toAnvil > 5.f && toAnvil < 25.f);
                    // Unslowed, it arrives within the roll's 10 s, before the reform.
                    float const seconds = toAnvil / EmberSpeed(toAnvil);
                    CHECK(seconds <= kEmberRollMs / 1000.f + 0.01f);
                }
            }
    }

    void TestClock()
    {
        FightClock c;
        CHECK(!c.On() && !c.Due(0));
        c.Start(0, kFistFirstMs);
        CHECK(!c.Due(kFistFirstMs - 1) && c.Due(kFistFirstMs));
        c.Fired(kFistFirstMs, kFistEveryMs);
        CHECK(c.DueMs() == kFistFirstMs + kFistEveryMs);
        c.NotBefore(kFistFirstMs + kFistEveryMs + 3000);
        CHECK(c.DueMs() == kFistFirstMs + kFistEveryMs + 3000);
        c.NotBefore(10);
        CHECK(c.DueMs() == kFistFirstMs + kFistEveryMs + 3000);
        c.Fired(100000, 1000);
        CHECK(c.DueMs() == 101000);
        c.Stop();
        CHECK(!c.Due(1000000));
    }
}

int main()
{
    TestSlice();
    TestTuning();
    TestRebirth();
    TestFrame();
    TestProfile();
    TestLongEdges();
    TestCrumbleBands();
    TestNeckSeals();
    TestNeckGrip();
    TestBounds();
    TestSurge();
    TestEmbers();
    TestClock();
    return Report("brd_incendius_test");
}
