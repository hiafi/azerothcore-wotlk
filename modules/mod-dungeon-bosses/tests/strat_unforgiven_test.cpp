// Host tests for UnforgivenLogic.h (S1: The Unforgiven): the street lanes inside their frames, the cordon placement
// rule (5 yd from every shelter, fire spot and march path, handoff section 3.8), the freed / bound rule, the Last Soul
// count, the fire picks and cap, the nova's gate.
#include "DungeonKitArena.h"
#include "UnforgivenLogic.h"
#include "check.h"
#include <cmath>
#include <cstdio>
#include <set>
#include <vector>

using namespace StratholmeRework;
using namespace StratUnforgiven;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // ----- Ids -------------------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206420 && kSpellSlice.last == 206439);
    for (std::uint32_t id : { SPELL_UF_MARCH_HIT, SPELL_UF_HOUSE_FIRE, SPELL_UF_BURNING_HOUSE, SPELL_UF_FIRELIGHT,
             SPELL_UF_ACCUSED, SPELL_UF_ACCUSED_FLASH, SPELL_UF_GRIEF, SPELL_UF_GRUDGE, SPELL_UF_FREED,
             SPELL_UF_SOUL_FREED, SPELL_UF_BOUND, SPELL_UF_FROST_NOVA, SPELL_UF_HAUNTING_MEMORY,
             SPELL_UF_IN_FIRELIGHT })
        CHECK(kSpellSlice.Contains(id));
    // The walls' strike is the shared one, never one of his.
    CHECK(!kSpellSlice.Contains(SPELL_ST_CROSSED_THE_LINE));
    CHECK(kCreaturesWave2.Contains(NPC_ST_SPECTRAL_FOOTMAN) && kCreaturesWave2.Contains(NPC_ST_HOUSE_FIRE));

    // ----- The arena -------------------------------------------------------------------------------------------------
    CHECK(UnforgivenArena().Contains(kUnforgivenSpawn.XY(), kUnforgivenSpawn.z));
    CHECK(ArenaFor(BOSS_UNFORGIVEN).Contains(kUnforgivenSpawn.XY(), kUnforgivenSpawn.z));
    CHECK(UnforgivenArena().Contains(kPlazaCenter, 132.f));
    // Every fire spot is on the plaza (inside the arena, on its floor band).
    for (std::size_t i = 0; i < kFireSpotCount; ++i)
        CHECK(UnforgivenArena().Contains(FireSpot(i), kFireSpotZ[i]));

    // ----- UF1 The March: the lanes inside their frames --------------------------------------------------------------
    for (MarchLane const& lane : kLanes)
    {
        HitLine const hit = MarchHitLine(lane);
        CHECK(DungeonKit::InsideFrame(lane.frame, hit.from));
        CHECK(DungeonKit::InsideFrame(lane.frame, hit.to));
        // The street's full width (never narrowed by a drawing limit: the R-1 lesson).
        CHECK(Near(hit.width, lane.frame.sizeY));
        CHECK(Near(hit.Length(), lane.frame.sizeX - lane.startX));
        // The march takes kMarchPassMs.
        CHECK(Near(hit.Length() / MarchSpeed(lane), kMarchPassMs / 1000.f, 0.001f));
        // The rank forms just inside its cordon, steps out to the hit line's start, then marches.
        CHECK(lane.formX >= 0.f && lane.formX < lane.startX);
        CHECK(lane.footmen >= 2 && RankLeader(lane) < lane.footmen);
        for (std::uint32_t i = 0; i < lane.footmen; ++i)
        {
            CHECK(DungeonKit::InsideFrame(lane.frame, RankPoint(lane, i, lane.formX)));
            CHECK(DungeonKit::InsideFrame(lane.frame, RankPoint(lane, i, lane.frame.sizeX)));
            CHECK(InMarchPath(lane, RankPoint(lane, i, lane.startX + 0.01f)));
        }
        // Footmen about 3.5 yd apart: a rank, not a crowd or a gap.
        float const spacing = DungeonKit::Distance(RankPoint(lane, 0, lane.startX), RankPoint(lane, 1, lane.startX));
        CHECK(spacing >= 2.5f && spacing <= 4.f);
        // The leader marches down the hit line's middle (ProjectileUnit tracks its projection on that line).
        Vec2 const leader = RankPoint(lane, RankLeader(lane), lane.startX);
        CHECK(DungeonKit::SegmentDistance(hit.from, hit.to, leader) <= lane.frame.sizeY / (2.f * lane.footmen) + 0.01f);
    }
    // The two lanes and the crossing (handoff section 3.8 #1: "the two lanes cross on the plaza's middle").
    CHECK(OtherLane(kLaneMarketRow) == kLanePassage && OtherLane(kLanePassage) == kLaneMarketRow);
    CHECK(InMarchPath(kLanes[kLaneMarketRow], kPlazaCenter));
    CHECK(InMarchPath(kLanes[kLanePassage], kPlazaCenter));
    // His spawn lies in both lanes (the report: inside L1, 4.8 yd from its edge): the tank moves him out.
    CHECK(InMarchPath(kLanes[kLaneMarketRow], kUnforgivenSpawn.XY()));
    // Heroic follow-up timing as the drill (section 3.9 row t 0): 3 s marker, 1.5 s chained marker, 40 / 45%.
    CHECK(kMarchWarnMs == 3000 && kMarchChainWarnMs == 1500);
    CHECK(kMarchPct(false) == 40.f && kMarchPct(true) == 45.f);
    CHECK(kMarchPct(true) < 50.f);      // under 50%, so it keeps Weakened (ST Heroic)
    CHECK(kMarch.first == 20000 && kMarch.every == 40000);

    // ----- UF2-UF4 The bays: fire spots and shelters -----------------------------------------------------------------
    for (std::size_t i = 0; i < kFireSpotCount; ++i)
    {
        // Each bay is a shelter: outside both marched lanes.
        for (MarchLane const& lane : kLanes)
            CHECK(!InMarchPath(lane, FireSpot(i)));
        CHECK(kBayKeepClearYd[i] >= kFireRadius);
    }
    CHECK(kFireMaxBurning == 3 && kFireBurnMs == 60000 && kFireEveryMs(false) == 25000 && kFireEveryMs(true) == 20000);
    CHECK(FireCanLight(0) && FireCanLight(2) && !FireCanLight(3) && !FireCanLight(4));
    {
        std::array<bool, kFireSpotCount> burning{};
        std::set<std::size_t> seen;
        for (std::uint32_t r = 0; r < 5; ++r)
        {
            auto const pick = PickFireSpot(burning, [r](std::uint32_t n) { return r % n; });
            CHECK(pick.has_value());
            if (pick)
                seen.insert(*pick);
        }
        CHECK(seen.size() == kFireSpotCount);
        burning = { true, true, false, true, true };
        auto const only = PickFireSpot(burning, [](std::uint32_t n) { return n - 1; });
        CHECK(only && *only == 2);
        burning.fill(true);
        CHECK(!PickFireSpot(burning, [](std::uint32_t) { return 0u; }));
    }
    // Firelight: within 10 yd of a burning house (the patch included), nowhere else.
    {
        std::vector<Vec2> lit{ FireSpot(0) };
        CHECK(InFirelight(FireSpot(0), lit));
        CHECK(InFirelight(DungeonKit::Advance(FireSpot(0), 1.f, 7.f), lit));
        CHECK(InFirelight(DungeonKit::Advance(FireSpot(0), 1.f, 9.99f), lit));
        CHECK(!InFirelight(DungeonKit::Advance(FireSpot(0), 1.f, 10.1f), lit));
        CHECK(!InFirelight(FireSpot(0), {}));
        CHECK(kFirelightInner == kFireRadius && kFirelightOuter == 10.f);
    }

    // ----- UF12 The Cordon: the placement rule -----------------------------------------------------------------------
    std::vector<KeepClear> const keep = CordonKeepClear();
    CHECK(keep.size() > kFireSpotCount + 2);
    for (std::size_t c = 0; c < kCordonCount; ++c)
    {
        WallLine const wall = CordonWall(c);
        CHECK(Near(wall.width, 2.f));
        DungeonKit::PlacementReport const report = DungeonKit::CheckPlacement(wall, keep);
        std::printf("strat_unforgiven_test: cordon %zu keeps %.2f yd clear (shape %zu)\n", c, report.minYd,
            report.worst);
        CHECK(DungeonKit::KeepsClear(wall, keep));
        // Each bay on its own, and each lane on its own.
        for (std::size_t i = 0; i < kFireSpotCount; ++i)
        {
            std::array<KeepClear, 1> const bay{ KeepClear::Point(FireSpot(i), kBayKeepClearYd[i]) };
            CHECK(DungeonKit::KeepsClear(wall, bay));
        }
        for (MarchLane const& lane : kLanes)
            CHECK(DungeonKit::KeepsClear(wall, MarchPathKeepClear(lane)));
        // His spawn and the plaza's middle are well inside.
        CHECK(DungeonKit::WallClearance(wall, kUnforgivenSpawn.XY()) > 5.f);
        CHECK(DungeonKit::WallClearance(wall, kPlazaCenter) > 5.f);
        // The cordon footmen stand on the line, about 2.5 yd apart.
        for (std::uint32_t k = 0; k < kCordonFootmen[c]; ++k)
            CHECK(DungeonKit::InsideWall(wall, CordonPoint(c, k)));
        float const gap = wall.Length() / static_cast<float>(kCordonFootmen[c]);
        CHECK(gap >= 2.f && gap <= 3.f);
    }
    // F-2 ruling (R-2-A question 1): every firelight ring, where the accused stands, keeps 5 yd from both strips (F2
    // moved 2 yd north along its bay for the east cordon), and F2 is still a shelter on the plaza.
    for (std::size_t c = 0; c < kCordonCount; ++c)
        for (std::size_t i = 0; i < kFireSpotCount; ++i)
        {
            std::array<KeepClear, 1> const ring{ FirelightKeepClear(i) };
            CHECK(DungeonKit::KeepsClear(CordonWall(c), ring));
        }
    {
        std::array<KeepClear, 1> const f2{ FirelightKeepClear(1) };
        float const gap = DungeonKit::CheckPlacement(CordonWall(kCordonEast), f2).minYd;
        std::printf("strat_unforgiven_test: F2's firelight ring keeps %.2f yd from the east cordon\n", gap);
        CHECK(gap >= 5.f && gap < 6.f);
        // Still inside the measured bay (x 3716..3722, y -3421..-3432).
        CHECK(FireSpot(1).x >= 3716.f && FireSpot(1).x <= 3722.f);
        CHECK(FireSpot(1).y >= -3432.f && FireSpot(1).y <= -3421.f);
        // The other four are the report's spots.
        for (std::size_t i : { 0u, 2u, 3u, 4u })
            CHECK(FireSpot(i).x == kUnforgivenFireSpots[i].x && FireSpot(i).y == kUnforgivenFireSpots[i].y);
    }

    // R-2-A A-1 (acceptance #8): a unit standing in a strip or within 1 yd of it at the pull is gripped onto the plaza
    // (off the polygon: the guard's own pull grip; on it: GripOffTheCordon's safety net), and the grip lands it well
    // clear of both strips.
    for (std::size_t c = 0; c < kCordonCount; ++c)
    {
        WallLine const wall = CordonWall(c);
        float const len = wall.Length();
        Vec2 const dir{ (wall.to.x - wall.from.x) / len, (wall.to.y - wall.from.y) / len };
        // The plaza side of the line: the side his spawn is on.
        float const side = DungeonKit::WallSide(wall, kUnforgivenSpawn.XY()) > 0.f ? 1.f : -1.f;
        Vec2 const normal{ -dir.y * side, dir.x * side };
        for (float t : { 0.1f, 0.3f, 0.5f, 0.7f, 0.9f })
        {
            Vec2 const on{ wall.from.x + (wall.to.x - wall.from.x) * t, wall.from.y + (wall.to.y - wall.from.y) * t };
            for (float in : { 0.f, 0.5f, 0.9f, 1.5f, 1.9f })
            {
                Vec2 const p{ on.x + normal.x * in, on.y + normal.y * in };
                CHECK(DungeonKit::WallSide(wall, p) * side >= -1e-3f);
                bool const offArena = !UnforgivenArena().Contains(p, kCordonZ[c]);
                CHECK(NeedsCordonGrip(p) || offArena);
                // The grip's default landing (8 yd from him toward the unit) is clear of both strips.
                Vec2 const land = DungeonKit::LandingToward(kUnforgivenSpawn.XY(), p, 8.f);
                CHECK(!NeedsCordonGrip(land));
                CHECK(UnforgivenArena().Contains(land, kUnforgivenSpawn.z));
            }
        }
    }
    // 0.5 yd plaza side of each line is a grip (the R-2-A scenario), 3 yd in is not.
    CHECK(NeedsCordonGrip(DungeonKit::Advance(CordonPoint(kCordonEast, 2), DungeonKit::BearingTo(
        CordonPoint(kCordonEast, 2), kPlazaCenter), 0.5f)));
    CHECK(NeedsCordonGrip(DungeonKit::Advance(CordonPoint(kCordonSouthWest, 5), DungeonKit::BearingTo(
        CordonPoint(kCordonSouthWest, 5), kPlazaCenter), 0.5f)));
    CHECK(!NeedsCordonGrip(DungeonKit::Advance(CordonPoint(kCordonEast, 2), DungeonKit::BearingTo(
        CordonPoint(kCordonEast, 2), kPlazaCenter), 3.f)));
    CHECK(!NeedsCordonGrip(kUnforgivenSpawn.XY()) && !NeedsCordonGrip(kPlazaCenter));
    for (std::size_t i = 0; i < kFireSpotCount; ++i)
        CHECK(!NeedsCordonGrip(FireSpot(i)));
    CHECK(kCordonGripClearanceYd == 1.f);

    // The strips really cover the street: a point in the middle of each marched lane is inside one of them.
    for (MarchLane const& lane : kLanes)
    {
        std::vector<KeepClear> const strips = MarchPathKeepClear(lane);
        CHECK(!strips.empty());
        Vec2 const mid = DungeonKit::FramePoint(lane.frame, (lane.startX + lane.frame.sizeX) * 0.5f,
            lane.frame.sizeY * 0.37f);
        bool covered = false;
        for (KeepClear const& k : strips)
            covered = covered || DungeonKit::SegmentDistance(k.a, k.b, mid) <= k.radius + 1e-3f;
        CHECK(covered);
        CHECK(strips.front().radius <= 1.f + 1e-3f);
    }
    // The cordon cuts the lane's mouth: a lane's frame origin sits on (or by) its cordon.
    CHECK(DungeonKit::WallClearance(CordonWall(kCordonSouthWest), kLanes[kLaneMarketRow].frame.origin) <= 1.f);
    CHECK(DungeonKit::WallClearance(CordonWall(kCordonEast), kLanes[kLanePassage].frame.origin) <= 1.f);
    // A crossing from inside to outside is seen; a walk along the plaza is not.
    CHECK(DungeonKit::CrossesWall(CordonWall(kCordonEast), { 3717.f, -3437.f }, { 3717.f, -3446.f }));
    CHECK(!DungeonKit::CrossesWall(CordonWall(kCordonEast), { 3717.f, -3430.f }, { 3710.f, -3425.f }));

    // ----- UF5-UF9 The phantoms --------------------------------------------------------------------------------------
    {
        PhantomOutcome o = Outcome(PhantomEnd::DiedInLight, false);
        CHECK(o.freed && !o.grief && o.grudgeDelta == 0);
        o = Outcome(PhantomEnd::DiedInDark, false);
        CHECK(!o.freed && !o.grief && o.grudgeDelta == 1);
        o = Outcome(PhantomEnd::Expired, false);
        CHECK(!o.freed && !o.grief && o.grudgeDelta == 1);
        o = Outcome(PhantomEnd::Reached, false);
        CHECK(!o.freed && o.grief && o.grudgeDelta == 1);
        // The Last Soul's returning phantoms: freeing one removes its stack; binding it again changes nothing.
        o = Outcome(PhantomEnd::DiedInLight, true);
        CHECK(o.freed && o.grudgeDelta == -1);
        o = Outcome(PhantomEnd::DiedInDark, true);
        CHECK(!o.freed && o.grudgeDelta == 0);
        o = Outcome(PhantomEnd::Reached, true);
        CHECK(o.grief && o.grudgeDelta == 0);
        o = Outcome(PhantomEnd::Expired, true);
        CHECK(o.grudgeDelta == 0);
    }
    // Freed tears 2% of his maximum health: 3,700 of 185k, 5,000 of 250k; never his last point.
    CHECK(FreedAmount(185000, 185000) == 3700);
    CHECK(FreedAmount(250000, 100000) == 5000);
    CHECK(FreedAmount(185000, 1000) == 999);
    CHECK(FreedAmount(185000, 1) == 0);
    // The Last Soul: once, at 25% or lower; one phantom per Grudge stack (a clean group gets none).
    CHECK(!LastSoulDue(25.1f, false));
    CHECK(LastSoulDue(25.f, false));
    CHECK(LastSoulDue(3.f, false));
    CHECK(!LastSoulDue(20.f, true));
    CHECK(LastSoulPhantoms(0) == 0 && LastSoulPhantoms(9) == 9);
    // Counts and health per difficulty (ST: 3 x 6,000 / 4 x 9,000), a 20 s life, a 60% walk.
    CHECK(kPhantomCount(false) == 3 && kPhantomCount(true) == 4);
    CHECK(kPhantomHealth(false) == 6000 && kPhantomHealth(true) == 9000);
    CHECK(kPhantomLifeMs == 20000 && Near(kPhantomSpeedYd, 0.6f * 2.5f, 0.001f));
    CHECK(kGriefPct == 30.f && kGrudgeDamagePct == 10.f && kFreedPct == 2.f);
    // They rise on a ring around him.
    for (std::uint32_t i = 0; i < 4; ++i)
        CHECK(Near(DungeonKit::Distance(PhantomRisePoint(kUnforgivenSpawn.XY(), i, 4), kUnforgivenSpawn.XY()),
            kPhantomSpawnYd));
    CHECK(DungeonKit::Distance(PhantomRisePoint(kUnforgivenSpawn.XY(), 0, 4),
        PhantomRisePoint(kUnforgivenSpawn.XY(), 2, 4)) > 5.f);
    // A Haunting Memory phantom rises 6 yd toward the middle (never past it), on the plaza.
    {
        Vec2 const carrier = FireSpot(1);
        Vec2 const rise = HauntingRisePoint(carrier);
        CHECK(Near(DungeonKit::Distance(carrier, rise), kHauntingRiseYd));
        CHECK(DungeonKit::Distance(rise, kPlazaCenter) < DungeonKit::Distance(carrier, kPlazaCenter));
        CHECK(UnforgivenArena().Contains(rise, 132.f));
        Vec2 const close = DungeonKit::Advance(kPlazaCenter, 0.5f, 2.f);
        CHECK(Near(DungeonKit::Distance(HauntingRisePoint(close), kPlazaCenter), 0.f));
    }
    CHECK(kHauntingCount == 2 && kHauntingMs == 8000 && kHauntingPct == 3.f && kHaunting.every == 30000);

    // ----- UF10 The nova's gate --------------------------------------------------------------------------------------
    // The next March lands at 23 s (20 s + the 3 s marker): no nova from 17 s on.
    CHECK(NovaAllowed(16000, 23000, 0));
    CHECK(!NovaAllowed(17000, 23000, 0));
    CHECK(!NovaAllowed(22999, 23000, 0));
    // A rank on the floor (heroic: through the chained rank's pass) blocks it too.
    CHECK(!NovaAllowed(25000, 63000, 29000));
    CHECK(NovaAllowed(29000, 63000, 29000));
    CHECK(NovaAllowed(5000, 0, 0));
    CHECK(kNovaMinMs == 15000 && kNovaMaxMs == 20000 && kNovaRootMs == 1500 && kNovaPct == 8.f);

    // ----- Cadence ---------------------------------------------------------------------------------------------------
    CHECK(NextOnCadence(20000, 20500, 40000) == 60000);
    CHECK(NextOnCadence(20000, 70000, 40000) == 70001);
    // The first Accusation (15 s) finds a fire: the first lands at 10 s (8 s + 2 s) and burns 60 s.
    CHECK(kFireFirstMs + kFireWarnMs < kAccusation.first);
    CHECK(kAccusation.first == 15000 && kAccusation.every == 35000);

    return Report("strat_unforgiven_test");
}
