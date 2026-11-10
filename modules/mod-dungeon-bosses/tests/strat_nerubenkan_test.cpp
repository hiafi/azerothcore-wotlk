// Host tests for NerubenkanLogic.h (S11: Nerub'enkan, "The Web"; build spec ST 2859-2911): the slice and the arena,
// the merge rule on his webs, the web clock (slow, Stuck, immunity, the drop spot dwell), the farthest patch within
// 30 yd, the capped hatch and the Brood Call count, the glob missile's launch.
#include "DungeonKitFloor.h"
#include "NerubenkanLogic.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace StratholmeRework;
using namespace StratNerubenkan;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool OnArena(Vec2 p)
    {
        return NerubenkanArena().Contains(p, kNerubenkanPlazaZ);
    }
}

int main()
{
    // ---- the slice, the arena -----------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.Contains(SPELL_NE_WEB_SPRAY));
    CHECK(kSpellSlice.Contains(SPELL_NE_POISON_BURST));
    CHECK(SPELL_NE_WEB_SPRAY == 206645);
    CHECK(SPELL_NE_COCOON_SPLITS == 206659);
    CHECK(SPELL_NE_POISON_BURST == 206660);
    CHECK(NerubenkanArena().Contains(kNerubenkanSpawn.XY(), kNerubenkanSpawn.z));
    CHECK(ArenaFor(BOSS_NERUBENKAN).Contains(kNerubenkanSpawn.XY(), kNerubenkanSpawn.z));
    // The plaza floor (z 138.5) and his stoop (z 144.3) are both on the arena's z band.
    CHECK(NerubenkanArena().Contains({ 3858.f, -3545.f }, kNerubenkanPlazaZ));
    CHECK(!NerubenkanArena().Contains({ 3858.f, -3545.f }, 150.f));
    // His kit units are the header's.
    CHECK(NPC_ST_WEB_COCOON == 300582);
    CHECK(NPC_ST_WEB_PATCH == 300583);
    CHECK(NPC_UNDEAD_SCARAB == 10876);

    // ---- tuning (ST build spec) -----------------------------------------------------------------------------------
    CHECK(kGlobSplashPct(false) == 25.f && kGlobSplashPct(true) == 30.f);
    CHECK(kSkitterPct(false) == 30.f && kSkitterPct(true) == 40.f);
    CHECK(kWebRadius(false) == 5.f && kWebRadius(true) == 7.f);
    CHECK(kCocoonHoldMs(false) == 8000 && kCocoonHoldMs(true) == 6000);
    CHECK(kCocoonHealth(false) == 8000 && kCocoonHealth(true) == 12000);
    CHECK(kScarabHealth(false) == 2000 && kScarabHealth(true) == 2500);
    CHECK(kWebSprayFirstMs == 8000 && kWebSprayEveryMs == 15000 && kWebSprayWarnMs == 3000);
    CHECK(kCocoonFirstMs == 15000 && kCocoonEveryMs == 25000 && kCocoonCastMs == 2000);
    CHECK(kSkitterFirstMs == 22000 && kSkitterEveryMs == 30000 && kSkitterWarnMs == 2000);
    CHECK(kBroodFirstMs == 30000 && kBroodEveryMs == 30000 && kBroodCastMs == 2500);
    CHECK(kPriorityBrood > kPriorityCocoon && kPriorityCocoon > kPrioritySkitter);

    // ---- NE3 the merge rule (ruling 47; the kit's PuddleSet with merge = true) ----------------------------------
    {
        DungeonKit::PuddleSet webs;
        float const r = kWebRadius(false);
        auto const a = webs.Add(0, { 3860.f, -3540.f }, 138.5f, r, kWebArmMs, 0, true);
        CHECK(a.id != 0 && !a.merged);
        // A glob whose center lands inside the old patch merges: no new floor.
        auto const b = webs.Add(500, { 3863.f, -3542.f }, 138.5f, r, kWebArmMs, 0, true);
        CHECK(b.merged && b.id == a.id);
        CHECK(webs.Size() == 1);
        // Just past the edge: a new patch (overlapping, but its own).
        auto const c = webs.Add(600, { 3865.2f, -3540.f }, 138.5f, r, kWebArmMs, 0, true);
        CHECK(!c.merged && c.id != a.id);
        CHECK(webs.Size() == 2);
        // On the edge exactly: merges (center inside or on the rim).
        auto const d = webs.Add(700, { 3855.f, -3540.f }, 138.5f, r, kWebArmMs, 0, true);
        CHECK(d.merged && d.id == a.id);
        // Another floor (the stoop is 6 yd up): never merges into the plaza's web.
        auto const e = webs.Add(800, { 3860.f, -3540.f }, 144.6f, r, kWebArmMs, 0, true);
        CHECK(!e.merged);
        // Heroic webs are bigger, and the merge rule is the same.
        DungeonKit::PuddleSet heroic;
        auto const h1 = heroic.Add(0, { 3860.f, -3540.f }, 138.5f, kWebRadius(true), kWebArmMs, 0, true);
        auto const h2 = heroic.Add(0, { 3866.5f, -3540.f }, 138.5f, kWebRadius(true), kWebArmMs, 0, true);
        CHECK(!h1.merged && h2.merged);
        // A new patch only counts once armed (the 1 s grace after it lands); a web lasts the whole fight.
        CHECK(!webs.Contains(500, { 3860.f, -3540.f }, 138.5f));
        CHECK(webs.Contains(1000, { 3860.f, -3540.f }, 138.5f));
        CHECK(webs.Contains(3600000, { 3860.f, -3540.f }, 138.5f));
        CHECK(webs.Prune(3600000).empty());
    }

    // ---- NE3 the web clock ----------------------------------------------------------------------------------------
    CHECK(!SlowDue(0));
    CHECK(!SlowDue(750));
    CHECK(SlowDue(1000));
    CHECK(!StuckDue(1750, 10000, 0));
    CHECK(StuckDue(2000, 10000, 0));
    // Stuck at 10 s: rooted 2 s, then immune 3 s; still inside after that, Stuck again.
    {
        std::uint64_t const immune = StuckImmuneUntil(10000);
        CHECK(immune == 15000);
        CHECK(!StuckDue(4000, 12000, immune));
        CHECK(!StuckDue(6750, 14750, immune));
        CHECK(StuckDue(7000, 15000, immune));
    }
    // A player released from a Cocoon gets a fresh window (R-1-A m-1): held at 9.75 s after 8 s inside, the first
    // tick after the release counts 250 ms, not 8.25 s; slowed 1 s and Stuck 2 s after the release.
    {
        std::uint32_t const inside = 8250;
        CHECK(WebClockAfterHold(inside, 10000, kNeverHeld) == inside);
        CHECK(WebClockAfterHold(inside, 10000, 9750) == 250);
        CHECK(!SlowDue(WebClockAfterHold(inside, 10000, 9750)));
        CHECK(!StuckDue(WebClockAfterHold(inside, 10000, 9750), 10000, 0));
        CHECK(SlowDue(WebClockAfterHold(inside + 750, 10750, 9750)));
        CHECK(!StuckDue(WebClockAfterHold(inside + 1500, 11500, 9750), 11500, 0));
        CHECK(StuckDue(WebClockAfterHold(inside + 1750, 11750, 9750), 11750, 0));
        // Left the web and came back: the inside clock restarted and is the smaller one.
        CHECK(WebClockAfterHold(500, 30000, 9750) == 500);
        // A hold recorded ahead of the clock (never on one clock) changes nothing.
        CHECK(WebClockAfterHold(inside, 9000, 9750) == inside);
    }
    // A carrier bot that steps into an old web MaxDwell before its glob lands is out before Stuck.
    CHECK(kDropMaxDwellMs == 800);
    CHECK(!StuckDue(kDropMaxDwellMs + 1000, 50000, 0));

    // ---- NE1 the drop spot room: his arena's floor, not the circle (R-1-A m-2) -------------------------------------
    {
        Vec2 const center{ 3858.f, -3540.f };
        CHECK(DungeonKit::PointInPolygon(kDropRoom, center));
        for (Vec2 const& p : kDropRoom)
            CHECK(DungeonKit::Distance(center, p) <= 30.f && OnArena(p));
        // Behind him: his stoop, his door 175379 and the ziggurat west of the circle are out.
        CHECK(!DungeonKit::PointInPolygon(kDropRoom, kNerubenkanSpawn.XY()));
        CHECK(!DungeonKit::PointInPolygon(kDropRoom, { kNerubenkanDoor.x, kNerubenkanDoor.y }));
        CHECK(!DungeonKit::PointInPolygon(kDropRoom, { 3850.f, -3515.f }));
        CHECK(!DungeonKit::PointInPolygon(kDropRoom, { 3840.f, -3520.f }));
        // The plaza in front of him stays in, rim to rim.
        CHECK(DungeonKit::PointInPolygon(kDropRoom, { 3880.f, -3540.f }));
        CHECK(DungeonKit::PointInPolygon(kDropRoom, { 3858.f, -3565.f }));
        // A star outline: one point every 15 degrees round the center, in order.
        for (std::size_t i = 0; i < kDropRoom.size(); ++i)
        {
            float const want = DungeonKit::kTwoPi * float(i) / float(kDropRoom.size());
            float got = std::atan2(kDropRoom[i].y - center.y, kDropRoom[i].x - center.x);
            if (got < -0.01f)
                got += DungeonKit::kTwoPi;
            CHECK(Near(got, want, 0.05f));
        }
    }

    // ---- NE6 Skitter: the farthest patch within 30 yd, on his arena -----------------------------------------------
    {
        Vec2 const boss{ 3858.f, -3540.f };
        std::vector<Vec2> patches{
            { 3868.f, -3540.f },        // 10 yd
            { 3858.f, -3518.f },        // 22 yd
            { 3858.f, -3568.f },        // 28 yd
            { 3830.f, -3540.f },        // 28 yd, but past nothing
        };
        auto const pick = PickSkitterPatch(boss, patches, OnArena);
        CHECK(pick && (*pick == 2 || *pick == 3));
        // Beyond 30 yd: never.
        std::vector<Vec2> far{ { 3858.f, -3575.f }, { 3868.f, -3540.f } };
        auto const pickFar = PickSkitterPatch(boss, far, OnArena);
        CHECK(pickFar && *pickFar == 1);
        // Off his arena (within 30 yd of him, but he stands at its edge): never.
        Vec2 const atEdge{ 3858.f, -3515.f };
        std::vector<Vec2> outside{ { 3858.f, -3500.f }, { 3858.f, -3520.f } };
        CHECK(Near(DungeonKit::Distance(atEdge, outside[0]), 15.f));
        CHECK(!OnArena(outside[0]));
        auto const pickIn = PickSkitterPatch(atEdge, outside, OnArena);
        CHECK(pickIn && *pickIn == 1);
        // No patch, no leap.
        CHECK(!PickSkitterPatch(boss, {}, OnArena));
        CHECK(!PickSkitterPatch(boss, { { 3858.f, -3575.f } }, OnArena));
        // The leap lands after 1 s, at 10 yd/s at least.
        CHECK(Near(SkitterJumpSpeed(25.f), 25.f));
        CHECK(Near(SkitterJumpSpeed(3.f), kSkitterMinJumpSpeed));
    }

    // ---- NE5 the hatch: 3 scarabs, at most 6 alive on normal; heroic no cap ----------------------------------------
    CHECK(HatchSize(false, 0) == 3);
    CHECK(HatchSize(false, 3) == 3);
    CHECK(HatchSize(false, 4) == 2);
    CHECK(HatchSize(false, 6) == 0);
    CHECK(HatchSize(false, 9) == 0);
    CHECK(HatchSize(true, 0) == 3);
    CHECK(HatchSize(true, 12) == 3);

    // ---- NE7 Brood Call: 2 per patch, no cap (about 4 at 30 s, 8 at 60, 12 at 90) -------------------------------
    CHECK(BroodCallCount(0) == 0);
    CHECK(BroodCallCount(2) == 4);
    CHECK(BroodCallCount(4) == 8);
    CHECK(BroodCallCount(6) == 12);
    {
        Vec2 const c{ 3860.f, -3540.f };
        std::vector<Vec2> const spots = ScarabSpots(c, kBroodPerPatch);
        CHECK(spots.size() == 2);
        CHECK(Near(DungeonKit::Distance(c, spots[0]), 1.5f));
        CHECK(Near(DungeonKit::Distance(spots[0], spots[1]), 3.f));
        CHECK(ScarabSpots(c, kHatchCount).size() == 3);
        CHECK(ScarabSpots(c, 0).empty());
    }

    // ---- NE1 the glob missile arrives as the circle resolves ------------------------------------------------------
    CHECK(GlobLaunchAt(11000, 20.f) == 10000);         // 20 yd at 20 yd/s: launched 1 s before
    CHECK(GlobLaunchAt(11000, 0.f) == 11000);
    CHECK(GlobLaunchAt(500, 40.f) == 0);               // a flight longer than the clock: at once
    CHECK(GlobLaunchAt(11000, 10.f, 0.f) == 11000);

    return Report("strat_nerubenkan_test");
}
