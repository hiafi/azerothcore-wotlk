// Host tests for GandlingLogic.h (S11: Darkmaster Gandling): the room cycle, the never-tank / never-just-back rules,
// the lane picks, the 1.5 s lane gap after a swap, the Volley geometry and the fight modes.
#include "GandlingLogic.h"
#include "SoloLessonLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>

using namespace ScholomanceRework;
using namespace ScholoGandling;

namespace
{
    // A deterministic stand-in for urand: a small LCG, `rand(n)` in [0, n).
    struct Lcg
    {
        std::uint32_t s = 12345;
        std::size_t operator()(std::size_t n)
        {
            s = s * 1103515245u + 12345u;
            return n ? (s >> 8) % n : 0;
        }
    };

    Candidate Player(std::uint64_t id)
    {
        Candidate c;
        c.id = id;
        c.inRegion = true;
        c.alive = true;
        return c;
    }

    void TestSlicesAndArenas()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t const id : kGandlingSpells)
            CHECK(kSpellSlice.Contains(id));
        CHECK(GandlingArena().Contains(kGandlingSpawn.XY(), kGandlingSpawn.z));
        // Every classroom has a landing point in its own arena, and none in the study.
        for (std::size_t i = 0; i < kClassroomCount; ++i)
        {
            CHECK(ClassroomArena(Classroom(i)).Contains(kClassroomLandings[i].XY(), kClassroomLandings[i].z));
            CHECK(!GandlingArena().Contains(kClassroomLandings[i].XY(), kClassroomLandings[i].z));
        }
        // The study region: the spawn on its floor box, every portal point on it, no landing on it.
        GandlingRegion const study = StudyRegion();
        CHECK(study.clip.Contains(kGandlingSpawn.XY(), kGandlingSpawn.z));
        CHECK(study.portalPoints.size() == kStudyPortalPoints.size());
        for (Vec2 const& p : study.portalPoints)
            CHECK(study.clip.Contains(p, kStudyFloorZ));
        for (Point4 const& l : kClassroomLandings)
            CHECK(!study.clip.Contains(l.XY(), l.z));
    }

    void TestRoomCycle()
    {
        Lcg rand;
        RoomCycle cycle;
        auto const all = [](Classroom) { return true; };
        std::optional<Classroom> last;
        for (int round = 0; round < 20; ++round)
        {
            // Six detentions use six different rooms.
            std::set<int> seen;
            for (std::size_t k = 0; k < kClassroomCount; ++k)
            {
                std::optional<Classroom> const room = cycle.Next(all, rand);
                CHECK(room.has_value());
                if (!room)
                    continue;
                seen.insert(int(*room));
                // Never the same room twice in a row, across a cycle's boundary too.
                if (last)
                    CHECK(*room != *last);
                last = room;
            }
            CHECK(seen.size() == kClassroomCount);
            CHECK(cycle.Left().empty());
        }

        // A blocked room is passed over and comes later in the cycle once it opens.
        RoomCycle c2;
        bool coven = false;
        auto const noCoven = [&coven](Classroom r) { return r != Classroom::Coven || coven; };
        std::set<int> got;
        for (int k = 0; k < 5; ++k)
            if (std::optional<Classroom> const r = c2.Next(noCoven, rand))
                got.insert(int(*r));
        CHECK(got.size() == 5);
        CHECK(!got.count(int(Classroom::Coven)));
        coven = true;
        std::optional<Classroom> const sixth = c2.Next(noCoven, rand);
        CHECK(sixth && *sixth == Classroom::Coven);

        // Every room left blocked: the cycle restarts early instead of stalling.
        RoomCycle c3;
        auto const onlyShadow = [](Classroom r) { return r == Classroom::ShadowVault; };
        std::optional<Classroom> const a = c3.Next(onlyShadow, rand);
        CHECK(a && *a == Classroom::ShadowVault);
        auto const notShadow = [](Classroom r) { return r != Classroom::ShadowVault; };
        std::optional<Classroom> const b = c3.Next(notShadow, rand);
        CHECK(b && *b != Classroom::ShadowVault);
        // Nothing open: nullopt.
        auto const none = [](Classroom) { return false; };
        CHECK(!c3.Next(none, rand));
    }

    void TestRoomGate()
    {
        RoomState s;
        CHECK(!RoomOpenForDetention(s));    // no lesson
        s.hasLesson = true;
        CHECK(RoomOpenForDetention(s));
        RoomState f = s;
        f.instructorFighting = true;        // F-B1: never while Malicia (or any instructor) fights in the room
        CHECK(!RoomOpenForDetention(f));
        RoomState e = s;
        e.examinerFighting = true;
        CHECK(!RoomOpenForDetention(e));
        RoomState o = s;
        o.othersInside = true;
        CHECK(!RoomOpenForDetention(o));
        // Every room has its examiner(s); the Ravenian's vault two.
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            CHECK(!ExaminersOf(Classroom(i)).empty());
        CHECK(ExaminersOf(Classroom::RavenianVault).size() == 2);
        CHECK(ExaminersOf(Classroom::Coven).front() == NPC_SC_EXAMINER_MALICIA);
    }

    void TestDetentionPick()
    {
        Lcg rand;
        std::vector<Candidate> c{ Player(1), Player(2), Player(3), Player(4), Player(5) };
        c[0].tank = true;
        c[1].justBack = true;
        c[2].honorRoll = true;
        c[3].detained = true;
        for (int k = 0; k < 50; ++k)
        {
            std::optional<std::size_t> const i = PickDetentionStudent(c, rand);
            CHECK(i && *i == 4);    // never the tank, the one just back, Honor Roll or one in a room
        }
        c[4].inRegion = false;      // out of the study (on the ring above, in a room)
        CHECK(!PickDetentionStudent(c, rand));
        c[4].inRegion = true;
        c[4].alive = false;
        CHECK(!PickDetentionStudent(c, rand));
        // A tank alone never goes.
        std::vector<Candidate> solo{ Player(9) };
        solo[0].tank = true;
        CHECK(!PickDetentionStudent(solo, rand));
    }

    void TestLanePicks()
    {
        Lcg rand;
        std::vector<Candidate> c{ Player(1), Player(2), Player(3), Player(4), Player(5) };
        c[0].tank = true;
        c[4].detained = true;
        for (int k = 0; k < 50; ++k)
        {
            std::vector<std::size_t> const t = PickLaneTargets(c, 3, false, rand);
            CHECK(t.size() == 3);
            std::set<std::size_t> distinct(t.begin(), t.end());
            CHECK(distinct.size() == 3);        // three players for three lanes
            CHECK(!distinct.count(0));          // never the tank
            CHECK(!distinct.count(4));          // never the one in a room
        }
        // More lanes than players: repeats, still never the tank.
        std::vector<std::size_t> const many = PickLaneTargets(c, 5, false, rand);
        CHECK(many.size() == 5);
        for (std::size_t i : many)
            CHECK(i != 0 && i != 4);
        // HM final: every player in the study, the tank too.
        std::vector<std::size_t> const every = EveryLaneTarget(c);
        CHECK(every.size() == 4);
        // Nobody: no lanes.
        std::vector<Candidate> empty{ Player(1) };
        empty[0].tank = true;
        CHECK(PickLaneTargets(empty, 2, false, rand).empty());
        CHECK(PickLaneTargets(empty, 2, true, rand).size() == 2);

        // Portal points: distinct while they last.
        for (int k = 0; k < 50; ++k)
        {
            std::vector<std::size_t> const p = PickPortalPoints(kStudyPortalPoints.size(), 3, rand);
            CHECK(std::set<std::size_t>(p.begin(), p.end()).size() == 3);
            for (std::size_t i : p)
                CHECK(i < kStudyPortalPoints.size());
        }
        CHECK(PickPortalPoints(0, 3, rand).empty());
    }

    void TestTransferPair()
    {
        Lcg rand;
        std::vector<Candidate> c{ Player(1), Player(2), Player(3) };
        c[0].tank = true;
        for (int k = 0; k < 50; ++k)
        {
            auto const pair = PickTransferPair(c, true, rand);
            CHECK(pair && pair->first != pair->second);
        }
        bool tankSeen = false;
        for (int k = 0; k < 200; ++k)
            if (auto const pair = PickTransferPair(c, true, rand))
                tankSeen = tankSeen || pair->first == 0 || pair->second == 0;
        CHECK(tankSeen);                // heroic: the tank can be picked
        for (int k = 0; k < 50; ++k)
        {
            auto const pair = PickTransferPair(c, false, rand);
            CHECK(pair && pair->first != 0 && pair->second != 0);
        }
        c[2].detained = true;
        CHECK(!PickTransferPair(c, false, rand));       // one left: no swap
        CHECK(PickTransferPair(c, true, rand).has_value());
    }

    void TestSwapGap()
    {
        // A swap never lands within 1.5 s before a lane fires.
        CHECK(SwapHoldMs(10000, {}) == 0);
        CHECK(SwapHoldMs(10000, { 9000 }) == 0);            // the lane fired already
        CHECK(SwapHoldMs(10000, { 11600 }) == 0);           // 1.6 s later: fine
        CHECK(SwapHoldMs(10000, { 11500 }) == 1600);        // 1.5 s later: wait until past it
        CHECK(SwapHoldMs(10000, { 10000 }) == 100);
        CHECK(SwapHoldMs(10000, { 10400, 11200 }) == 1300); // the later of two
        // Held swaps then clear the rule.
        for (std::uint32_t fire : { 10000u, 10700u, 11500u })
        {
            std::uint32_t const hold = SwapHoldMs(10000, { fire });
            CHECK(hold > 0);
            CHECK(10000 + hold > fire);
            CHECK(SwapHoldMs(10000 + hold, { fire }) == 0);
        }
        // The Volley's own spacing: lanes fire 2 s after the portals open, so a swap before the portals is fine.
        CHECK(kVolleyWarnMs > kLaneGapAfterSwapMs);
    }

    void TestVolleyLane()
    {
        GandlingRegion const study = StudyRegion();
        // From the west edge point (163.5, -12) through the center: the lane reaches the east wall (x 200), never past.
        Vec2 const portal = kStudyPortalPoints[2];
        DungeonKit::LinePath const path = VolleyLane(study, portal, { 181.0f, -0.5f });
        CHECK(path.clipped);
        CHECK(path.length > 30.f);
        CHECK(study.clip.Contains(path.end, kStudyFloorZ) || path.end.x <= 200.5f);
        CHECK(path.end.x > 195.f && path.end.x <= 200.f);
        // A player on the portal: the lane still runs (along the fallback facing), clipped to the wall.
        DungeonKit::LinePath const onIt = VolleyLane(study, portal, portal);
        CHECK(onIt.length > 0.f);
        // Every portal through the spawn stays inside the room's box.
        for (Vec2 const& p : kStudyPortalPoints)
        {
            DungeonKit::LinePath const l = VolleyLane(study, p, kGandlingSpawn.XY());
            CHECK(l.clipped);
            CHECK(l.end.x >= 161.9f && l.end.x <= 200.1f && l.end.y >= -20.1f && l.end.y <= 19.1f);
        }
    }

    void TestModesAndNumbers()
    {
        GandlingMode const n = FightMode(false);
        GandlingMode const h = FightMode(true);
        CHECK(n.detention && h.detention);
        CHECK(n.volleyPortals == 2 && h.volleyPortals == 3);
        CHECK(!n.transfer && h.transfer);           // Transfer is heroic only
        CHECK(n.lingerMs == 0 && h.lingerMs == 4000);
        CHECK(n.detentionFirstMs == 15000 && n.detentionEveryMs == 25000);
        CHECK(n.volleyFirstMs == 10000 && n.volleyEveryMs == 20000);
        CHECK(h.transferFirstMs == 20000 && h.transferEveryMs == 30000);
        CHECK(h.transferTankEligible && !h.transferRaisesExpelled && !h.lanesThroughEveryone);
        GandlingMode const f = FinalExamMode();
        CHECK(!f.detention);                        // none in the final phase (approved answers)
        CHECK(f.lanesThroughEveryone);
        CHECK(f.transfer && f.transferEveryMs == 15000 && f.transferRaisesExpelled);
        CHECK(f.volleyEveryMs == 20000);
        CHECK(kVolleyPct(false) == 30.f && kVolleyPct(true) == 40.f);
        CHECK(std::fabs(LessonFailurePct(false) - 15.f) < 0.01f && std::fabs(LessonFailurePct(true) - 25.f) < 0.01f);
        CHECK(kHonorRollMs == 15000);
        // Expelled growth: +10% every 10 s alive.
        CHECK(ExpelledGrowthStacks(9999) == 0);
        CHECK(ExpelledGrowthStacks(10000) == 1);
        CHECK(ExpelledGrowthStacks(35000) == 3);
        CHECK(std::fabs(ExpelledDamageFactor(3) - 1.3f) < 0.001f);
        // A lesson ends (15 s) before the next detention is due (25 s), with the 1 s cast and the arrival allowance.
        CHECK(kDetentionCastMs + kArrivalTimeoutMs + kLessonMs + kArrivalTimeoutMs < kDetentionEveryMs);
    }
}

int main()
{
    TestSlicesAndArenas();
    TestRoomCycle();
    TestRoomGate();
    TestDetentionPick();
    TestLanePicks();
    TestTransferPair();
    TestSwapGap();
    TestVolleyLane();
    TestModesAndNumbers();
    return Report("scholo_gandling_test");
}
