// Host tests for GilnidLogic.h (WP-B4): ids, timers, target picks, lanes against the measured foundry walls, Hot shot
// segments, ball sweeps and the land mine cap.
#include "GilnidLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

using namespace DeadminesKit;
using namespace DeadminesRework;
using namespace Gilnid;

namespace
{
    bool Near(float a, float b, float tolerance)
    {
        return std::fabs(a - b) <= tolerance;
    }

    void TestIds()
    {
        CHECK(kSlice.first == 205270u);
        CHECK(kSlice.Contains(kSlice.last));
        for (std::uint32_t id : { SPELL_ROLL_OUT_THE_SHOT, SPELL_BOWLED_OVER, SPELL_HOT_SHOT,
                 SPELL_LAND_MINE_DETONATION, SPELL_SHOT_POUR, SPELL_SHOT_LAUNCH, SPELL_RED_HOT, SPELL_LAND_MINE_ARMING,
                 SPELL_LAND_MINE_BLAST, SPELL_LAND_MINE_FIZZLE, SPELL_TOSS_LANDMINE, SPELL_HOT_SHOT_GROUND })
            CHECK(kSlice.Contains(id));
        CHECK(NPC_DM_IRON_SHOT == 300423u && NPC_DM_LAND_MINE == 300424u);
    }

    void TestTimers()
    {
        CHECK(ShotCooldownMs(false, false) == 18000u);
        CHECK(ShotCooldownMs(true, false) == 15000u);
        CHECK(ShotCooldownMs(true, true) == 10000u);
        CHECK(ShotCooldownMs(false, true) == 18000u);   // Double shift is heroic only
        CHECK(!kHotShot(false) && kHotShot(true));
        CHECK(!kLandmine(false) && kLandmine(true));
        CHECK(!kDoubleShift(false) && kDoubleShift(true));
        // Build spec: a ball reaches someone by Gilnid (about 28 yd from the pots) about 3 s after it leaves.
        CHECK(Near(Distance(kPotCenter, kGilnidSpawn) / kShotSpeed, 2.9f, 0.1f));
        // Hot shot: a batch's trails are gone about 11 s after its marker (2 s marker, at most 4 s of roll, 1 s
        // before the first tick, 6 s of fire), so Double shift's next marker (10 s) finds them almost gone.
        float const longest = 40.f / kShotSpeed;
        CHECK(kLaneWarnMs / 1000.f + longest + kHotShotDurationMs / 1000.f <= 12.5f);
    }

    std::uint32_t RollFirst(std::uint32_t)
    {
        return 0;
    }

    void TestTargets()
    {
        std::vector<Candidate<int>> const party{ { 1, true }, { 2, false }, { 3, false }, { 4, false }, { 5, false } };
        std::vector<int> const heroic = SelectShotTargets(party, true, RollFirst);
        CHECK(heroic.size() == 5);                      // every player, the tank included
        std::vector<int> const normal = SelectShotTargets(party, false, RollFirst);
        CHECK(normal.size() == 2);
        CHECK(normal[0] == 2 && normal[1] == 3);        // never the tank, never twice
        std::uint32_t seed = 7;
        auto roll = [&seed](std::uint32_t n)
        {
            seed = seed * 1103515245u + 12345u;
            return (seed >> 16) % n;
        };
        for (int i = 0; i < 200; ++i)
        {
            std::vector<int> const pick = SelectShotTargets(party, false, roll);
            CHECK(pick.size() == 2 && pick[0] != pick[1] && pick[0] != 1 && pick[1] != 1);
        }
        // only the tank there (a lone tester): the tank
        std::vector<Candidate<int>> const solo{ { 9, true } };
        CHECK(SelectShotTargets(solo, false, RollFirst) == std::vector<int>{ 9 });
        CHECK(SelectShotTargets(std::vector<Candidate<int>>{}, false, RollFirst).empty());
        // one non-tank: one lane
        std::vector<Candidate<int>> const duo{ { 1, true }, { 2, false } };
        CHECK(SelectShotTargets(duo, false, RollFirst) == std::vector<int>{ 2 });
        // mines: a random non-tank, none when only the tank is there
        CHECK(SelectMineTarget(party, RollFirst) == std::optional<int>(2));
        CHECK(!SelectMineTarget(solo, RollFirst));
        // a broken roll (out of range) still picks inside the pool
        CHECK(SelectMineTarget(party, [](std::uint32_t n) { return n + 3; }) == std::optional<int>(5));
    }

    // Floor points inside the measured polygon and off the pot block (1 yd grid).
    std::vector<Vec2> FloorPoints()
    {
        std::vector<Vec2> out;
        for (float x = -217.5f; x <= -168.f; x += 1.f)
            for (float y = -594.f; y <= -543.f; y += 1.f)
            {
                Vec2 const p{ x, y };
                if (PointInPolygon(kFoundryWalls, p) && !kPotBlock.Contains(p))
                    out.push_back(p);
            }
        return out;
    }

    void TestLanes()
    {
        std::vector<Vec2> const floor = FloorPoints();
        CHECK(floor.size() > 1000);     // about 1,100 sq yd of floor beside the pot block (NAVMESH-REPORT: 1,137)
        std::vector<Vec2> origins(kPots.begin(), kPots.end());
        origins.push_back(kPotCenter);
        std::size_t lanes = 0;
        float longest = 0.f;
        std::size_t maxSegments = 0;
        for (Vec2 const pot : origins)
        {
            for (Vec2 const target : floor)
            {
                std::optional<Lane> const lane = ComputeLane(pot, target, kGilnidSpawn);
                CHECK(lane.has_value());
                if (!lane)
                    continue;
                ++lanes;
                // the end point stays inside the measured floor polygon
                CHECK(PointInPolygon(kFoundryWalls, lane->to));
                // the lane reaches the target (a target on the floor is never beyond the wall it ends at; the
                // inset may stop it at most half a yard short of a target hugging the wall)
                CHECK(lane->length + kLaneWallInset + 1e-3f >= Distance(pot, target));
                // the target is on the lane's center line (unless it stands on the pot: then the lane aims at Gilnid)
                float const s = AlongLane(*lane, target);
                Vec2 const onLane = PointOnLane(*lane, s);
                CHECK(Distance(pot, target) < 0.5f || Distance(onLane, target) < 1e-2f);
                longest = std::max(longest, lane->length);
                float const skip = BlockExit(*lane, kPotBlock);
                CHECK(skip <= 12.8f);   // the pot block is 9 x 9 yd: no lane spends more than its diagonal in it
                maxSegments = std::max(maxSegments, HotShotSegments(lane->length, skip).size());
            }
        }
        CHECK(lanes == floor.size() * origins.size());
        CHECK(longest < 45.f);          // the room spans 40 yd at most, the far pot adds a little
        CHECK(maxSegments <= 11);

        // the measured lane through Gilnid: pot center -> wall at 36.0 yd (NAVMESH-REPORT), minus the inset
        std::optional<Lane> const throughGilnid = ComputeLane(kPotCenter, kGilnidSpawn, kGilnidSpawn);
        CHECK(throughGilnid && Near(throughGilnid->length, 36.0f - kLaneWallInset, 0.5f));
        CHECK(throughGilnid && Near(AlongLane(*throughGilnid, kGilnidSpawn), 28.7f, 0.2f));
        // a lane aimed east of the pots is short (8 to 17 yd)
        std::optional<Lane> const east = ComputeLane(kPotCenter, { -205.7f, -590.f }, kGilnidSpawn);
        CHECK(east && east->length < 17.f);
        // a target on the pot aims through the fallback (Gilnid)
        std::optional<Lane> const onPot = ComputeLane(kPots[0], kPots[0], kGilnidSpawn);
        CHECK(onPot && SweptWithin(onPot->from, onPot->to, kGilnidSpawn, 0.01f));
    }

    void TestSegments()
    {
        std::vector<Segment> const segs = HotShotSegments(30.f, 4.5f);
        CHECK(!segs.empty());
        CHECK(Near(segs.front().s0, 4.5f, 1e-4f));
        CHECK(Near(segs.back().s1, 30.f, 1e-4f));
        for (std::size_t i = 0; i < segs.size(); ++i)
        {
            CHECK(segs[i].s1 > segs[i].s0);
            CHECK(segs[i].s1 - segs[i].s0 <= kHotShotSegmentYd * 1.25f + 1e-4f);
            if (i > 0)
                CHECK(Near(segs[i].s0, segs[i - 1].s1, 1e-4f));     // contiguous: no gap in the trail
        }
        CHECK(segs.size() == 7);        // 25.5 yd: six pieces of 4, then 1.5 (at least a quarter piece: its own)
        CHECK(HotShotSegments(4.f, 4.5f).empty());
        CHECK(HotShotSegments(8.2f, 0.f).size() == 2);  // the 0.2 yd remainder joins the second piece

        // passing: a segment registers once the ball is past its far end; done releases the rest
        std::size_t next = 0;
        next = SegmentsPassed(segs, next, 3.f, false);
        CHECK(next == 0);
        next = SegmentsPassed(segs, next, 8.5f, false);
        CHECK(next == 1);
        next = SegmentsPassed(segs, next, 21.f, false);   // a slow update: three at once
        CHECK(next == 4);
        next = SegmentsPassed(segs, next, 22.f, true);
        CHECK(next == segs.size());
    }

    void TestSweeps()
    {
        // the ball crosses Gilnid's spot between two updates: still counted
        CHECK(SweptWithin({ 0.f, 0.f }, { 4.f, 0.f }, { 2.f, 1.f }, kBowledOverRadius));
        CHECK(!SweptWithin({ 0.f, 0.f }, { 4.f, 0.f }, { 2.f, 3.f }, kBowledOverRadius));
        CHECK(!SweptWithin({ 0.f, 0.f }, { 4.f, 0.f }, { 8.f, 0.f }, kBowledOverRadius));  // not reached yet
        CHECK(Near(DistanceToSegment({ 0.f, 5.f }, { 0.f, 0.f }, { 0.f, 0.f }), 5.f, 1e-5f));
        // a mine 3.5 yd off the lane's center line is swept (within its 4 yd)
        CHECK(SweptWithin({ 0.f, 0.f }, { 10.f, 0.f }, { 5.f, 3.5f }, kBallMineRadius));
        // Bowled Over is reachable: a lane through Gilnid's spot passes within the radius of him
        std::optional<Lane> const lane = ComputeLane(kPots[1], kGilnidSpawn, kGilnidSpawn);
        CHECK(lane && SweptWithin(lane->from, lane->to, kGilnidSpawn, kBowledOverRadius));
    }

    struct MineEntry
    {
        int id = 0;
    };

    void TestMineCap()
    {
        MineLedger<MineEntry> ledger;
        for (int i = 1; i <= 6; ++i)
            CHECK(ledger.Add({ i }).empty());
        CHECK(ledger.Size() == kMineCap);
        std::vector<MineEntry> const out = ledger.Add({ 7 });     // a 7th makes the oldest fizzle
        CHECK(out.size() == 1 && out[0].id == 1);
        CHECK(ledger.Size() == 6 && ledger.Live().front().id == 2 && ledger.Live().back().id == 7);
        // a ball sweeps two mines: they leave, the next add evicts nothing
        std::vector<MineEntry> const swept = ledger.RemoveIf([](MineEntry const& e) { return e.id == 3 || e.id == 5; });
        CHECK(swept.size() == 2);
        CHECK(ledger.Size() == 4);
        CHECK(ledger.Add({ 8 }).empty());
        CHECK(ledger.Add({ 9 }).empty());
        std::vector<MineEntry> const next = ledger.Add({ 10 });
        CHECK(next.size() == 1 && next[0].id == 2);
        ledger.Clear();
        CHECK(ledger.Size() == 0);
        // an uncapped ledger never evicts
        MineLedger<MineEntry> open(0);
        for (int i = 0; i < 20; ++i)
            CHECK(open.Add({ i }).empty());
    }

    // Handoff section 6: the densest heroic moment (5 players, every lane a long one, Hot shot on, the mine cap
    // reached) stays lean: report the number.
    void TestPeak()
    {
        std::vector<float> const five(5, 36.f);
        std::size_t const peak = PeakRegistrations(five, 4.5f, true, kMineCap);
        CHECK(peak == 5 + 5 * 8 + 6);   // 36 - 4.5 = 31.5 yd: 7 pieces of 4 plus one of 3.5
        CHECK(PeakRegistrations(std::vector<float>(2, 36.f), 4.5f, false, 0) == 2);    // normal: two lanes
        std::printf("gilnid peak registrations (heroic, 5 long lanes, 6 mines): %zu\n", peak);
    }
}

int main()
{
    TestIds();
    TestTimers();
    TestTargets();
    TestLanes();
    TestSegments();
    TestSweeps();
    TestMineCap();
    TestPeak();
    return Report("gilnid_test");
}
