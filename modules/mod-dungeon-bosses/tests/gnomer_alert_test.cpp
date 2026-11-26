// Host tests for MobileAlertSystemLogic.h (Gnomeregan D4, the Mobile Alert System): the slice, the spots, the fight's
// floor, the timeline rules and the LightsMachine's pure half against KT-G's DungeonKit::LightClock.
#include "DungeonKitLightLogic.h"
#include "MobileAlertSystemLogic.h"
#include "check.h"
#include <cmath>

using namespace GnomereganRework;
using namespace GnomerAlert;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float Deg(float rad)
    {
        return rad * 180.f / DungeonKit::kPi;
    }

    // Signed smallest difference a - b in degrees.
    float DiffDeg(float a, float b)
    {
        float d = std::fmod(Deg(a) - Deg(b), 360.f);
        if (d > 180.f)
            d -= 360.f;
        if (d < -180.f)
            d += 360.f;
        return d;
    }

    Vec2 At(Vec2 from, float bearing, float yd)
    {
        return { from.x + yd * std::cos(bearing), from.y + yd * std::sin(bearing) };
    }

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214420 && kSpellSlice.last == 214459);
        for (std::uint32_t s : { SPELL_MA_SPOTTED, SPELL_MA_ALARM, SPELL_MA_ALARM_LOOK, SPELL_MA_LOCK_ON,
                 SPELL_MA_SPOTTED_BEAM, SPELL_MA_SELF_DESTRUCT, SPELL_MA_BLAST_LOOK, SPELL_MA_NET, SPELL_MA_NETTING })
            CHECK(kSpellSlice.Contains(s));
        CHECK(SPELL_MA_NETTING == 214428);
        // the drill's tags (mod-boss-mechanics MechanicDrill.h kGnTagSearchlight / kGnTagLights / kGnTagCameras)
        CHECK(TAG_MA_SEARCHLIGHT == 50 && TAG_MA_LIGHTS == 52 && TAG_MA_CAMERAS == 54);
        CHECK(FloorTag(LightTag(false)) == TAG_MA_SEARCHLIGHT_FLOOR);
        CHECK(FloorTag(LightTag(true)) == TAG_MA_LIGHTS_FLOOR);
        // the creatures (GnomereganRework.h, S0's row)
        CHECK(NPC_ALERT_SYSTEM == 301110 && NPC_SECURITY_ASSISTANT == 301111 && NPC_SECURITY_DEFENDER == 301112);
        CHECK(NPC_LIGHT_STALKER == 301113);
        // text groups 0-8, 0-based (rule 35)
        CHECK(YELL_MA_ALARM == 0 && YELL_MA_CANCELED == 7 && EMOTE_MA_CAMERAS == 8);
    }

    void TestSpots()
    {
        Arena const hall = ArenaFor(BOSS_ALERT_SYSTEM);
        CHECK(hall.Contains(kAlertSystemSpawn.XY(), kAlertSystemSpawn.z));
        // the corridor entry: on the hall, 5 to 6 yd from the door, past the light's reach, facing him
        CHECK(hall.Contains(kEntrySpot.XY(), kEntrySpot.z));
        float const toDoor = DungeonKit::Distance(kEntrySpot.XY(), kWorkshopDoorSpot.XY());
        CHECK(toDoor > 5.f && toDoor < 6.f);
        float const toHim = DungeonKit::Distance(kEntrySpot.XY(), kAlertSystemSpawn.XY());
        CHECK(toHim > Tune::kLightReachYd && toHim < 32.f);
        CHECK(std::fabs(DiffDeg(kEntrySpot.o, BearingTo(kEntrySpot.XY(), kAlertSystemSpawn.XY()))) < 4.f);
        for (std::uint32_t n : { 1u, 2u, 3u })
            for (std::uint32_t i = 0; i < n; ++i)
            {
                Vec2 const p = EntryPoint(i, n);
                CHECK(hall.Contains(p, kEntrySpot.z));
                CHECK(DungeonKit::Distance(p, kEntrySpot.XY()) <= kEntrySpacingYd * 1.01f);
            }
        // a pair stands kEntrySpacingYd apart, across the corridor (perpendicular to the walk in)
        Vec2 const a = EntryPoint(0, 2);
        Vec2 const b = EntryPoint(1, 2);
        CHECK(Near(DungeonKit::Distance(a, b), kEntrySpacingYd, 0.01f));
        float const across = BearingTo(a, b);
        CHECK(std::fabs(std::fabs(DiffDeg(across, kEntrySpot.o)) - 90.f) < 0.5f);
    }

    void TestFightFloor()
    {
        Vec2 const spot = kAlertSystemSpawn.XY();
        std::vector<Vec2> const floor = FightFloorPolygon(spot, Tune::kBotFloorYd);
        CHECK(floor.size() >= 3);
        for (Vec2 const& p : floor)
            CHECK(DungeonKit::Distance(p, spot) <= Tune::kBotFloorYd + 0.01f);
        float const area = PolygonArea(floor);
        // NAVMESH 4: 1,486 sq yd of floor within 30 yd, 1,202 within 25: 28 yd sits between
        CHECK(area > 1000.f && area < 1486.f);
        float const area30 = PolygonArea(FightFloorPolygon(spot, Tune::kLightReachYd));
        CHECK(area30 > area && area30 < 1800.f);
        float const hallArea = PolygonArea(std::vector<Vec2>(kHallPolygon.begin(), kHallPolygon.end()));
        CHECK(area30 < hallArea);
        Arena const arena = FightFloorArena(spot, Tune::kBotFloorYd);
        CHECK(arena.Contains(spot, kAlertSystemSpawn.z));
        CHECK(!arena.Contains(kEntrySpot.XY(), kEntrySpot.z));         // the corridor is 30 yd out
        CHECK(!arena.Contains(At(spot, 3.4f, 40.f), kAlertSystemSpawn.z));
        // a 10 yd ring round him is floor on most bearings (the pillar and the east wall cut the rest)
        std::uint32_t inside = 0;
        for (std::uint32_t i = 0; i < 36; ++i)
            if (arena.Contains(At(spot, DungeonKit::kTwoPi * i / 36.f, 8.f), kAlertSystemSpawn.z))
                ++inside;
        CHECK(inside >= 30);
        // clipping a square with a disc that holds it changes nothing; one that misses it leaves nothing
        std::vector<Vec2> const square{ { 0.f, 0.f }, { 1.f, 0.f }, { 1.f, 1.f }, { 0.f, 1.f } };
        CHECK(Near(PolygonArea(ClipToConvex(square, DiscPolygon({ 0.5f, 0.5f }, 5.f, 16))), 1.f, 0.001f));
        CHECK(ClipToConvex(square, DiscPolygon({ 50.f, 50.f }, 5.f, 16)).empty());
        CHECK(Near(PolygonArea(DiscPolygon({ 0.f, 0.f }, 10.f, 48)), 312.3f, 1.f));
    }

    void TestTimeline()
    {
        // rule 11: never sooner than half a period from now
        CHECK(NextDue(10000, 10000, 10000) == 20000);
        CHECK(NextDue(10000, 10000, 25000) == 30000);
        CHECK(NextDue(10000, 10000, 12000) == 20000);
        // the cameras (section 7 #21 A)
        CHECK(CameraSees(30.5f, true));
        CHECK(!CameraSees(30.f, true));
        CHECK(!CameraSees(45.f, false));
        // the Defender cap: 4 alive on normal, none on heroic
        CHECK(DefenderAllowed(false, 3));
        CHECK(!DefenderAllowed(false, 4));
        CHECK(DefenderAllowed(true, 40));
        CHECK(ResponseAssistants(false) == 0 && ResponseAssistants(true) == 1);
        // the Self-destruct clock
        CHECK(ClockAfterSpotted(120000) == 115000);
        CHECK(ClockAfterSpotted(3000) == 0);
        CHECK(WarnNow(20000, false));
        CHECK(!WarnNow(20001, false));
        CHECK(!WarnNow(15000, true));
        CHECK(WarnNow(18000, false));      // a Spotted jumped the mark
        CHECK(!WarnNow(0, false));         // it is already going off
        // the spec's numbers
        CHECK(Tune::kSpottedPct.normal == 20.f && Tune::kSpottedPct.heroic == 50.f);
        CHECK(Tune::kAlarmPct.normal == 5.f && Tune::kAlarmPct.heroic == 8.f);
        CHECK(Tune::kPatrolEveryMs.normal == 30000 && Tune::kPatrolEveryMs.heroic == 20000);
        CHECK(Tune::kSelfDestructMs == 120000);
        // heroic clock check (SP): five Spotted hits take 25 s, a clean 95 s kill's margin
        std::uint32_t left = Tune::kSelfDestructMs - 95000;
        for (int i = 0; i < 5; ++i)
            left = ClockAfterSpotted(left);
        CHECK(left == 0);
        CHECK(kSpottedWeakened.normal && !kSpottedWeakened.heroic);
    }

    void TestSweep()
    {
        LightPlan const plan = SweepPlan(Tune::kSearchSweepDeg, Tune::kSearchDimMs, Tune::kSearchSweepMs);
        CHECK(plan.count == 1);
        CHECK(Near(plan.degPerSec, 20.f));
        CHECK(plan.direction == -1);
        CHECK(plan.litAfterMs == 2000 && plan.lifeMs == 5000 && plan.lookAheadMs == 5000);
        CHECK(plan.lookAheadStepMs == 0 && plan.drawLookAhead);
        CHECK(Near(SweptDeg(Tune::kSearchConeDeg, Tune::kSearchSweepDeg), 100.f));

        // KT-G's clock run with the plan: the dim holds at the target, then 60 degrees clockwise in 3 s.
        Vec2 const boss = kAlertSystemSpawn.XY();
        Vec2 const target = At(boss, 1.0f, 20.f);
        float const start = BearingTo(boss, target);
        DungeonKit::LightClock clock(start, plan.degPerSec, 1, plan.direction);
        clock.Hold(plan.litAfterMs);
        DungeonKit::LightSector const swept = DungeonKit::SweptSector(clock.Ahead(0, plan.lookAheadMs),
            Tune::kSearchConeDeg);
        CHECK(Near(swept.angleDeg, 100.f, 0.1f));
        CHECK(Near(DiffDeg(swept.bearing, start), -30.f, 0.1f));
        clock.Advance(plan.litAfterMs);
        CHECK(Near(DiffDeg(clock.Bearing(), start), 0.f, 0.01f));      // lit on the target
        CHECK(DungeonKit::InLight(boss, clock.Bearing(), Tune::kSearchConeDeg, Tune::kLightReachYd, target));
        clock.Advance(plan.lifeMs - plan.litAfterMs);
        CHECK(Near(DiffDeg(clock.Bearing(), start), -60.f, 0.1f));     // clockwise

        // Out against the sweep: 25 degrees counter-clockwise of the start is never lit; 25 clockwise is crossed.
        Vec2 const against = At(boss, start + 25.f * DungeonKit::kPi / 180.f, 20.f);
        Vec2 const with = At(boss, start - 25.f * DungeonKit::kPi / 180.f, 20.f);
        DungeonKit::LightClock run(start, plan.degPerSec, 1, plan.direction);
        bool againstLit = false;
        bool withLit = false;
        for (std::uint32_t t = 0; t <= plan.lifeMs - plan.litAfterMs; t += 100)
        {
            againstLit = againstLit || DungeonKit::InLight(boss, run.Bearing(), Tune::kSearchConeDeg,
                Tune::kLightReachYd, against);
            withLit = withLit || DungeonKit::InLight(boss, run.Bearing(), Tune::kSearchConeDeg, Tune::kLightReachYd,
                with);
            run.Advance(100);
        }
        CHECK(!againstLit);
        CHECK(withLit);
        // a player past the light's reach is the cameras', never the cone's
        CHECK(!DungeonKit::InLight(boss, start, Tune::kSearchConeDeg, Tune::kLightReachYd, At(boss, start, 31.f)));
    }

    void TestTurning()
    {
        LightPlan const plan = TurningPlan(Tune::kLightsCount, Tune::kLightsDegPerSec, kLightsStartDirection,
            Tune::kLightsDarkMs);
        CHECK(plan.count == 2 && plan.lifeMs == 0 && plan.litAfterMs == 3000 && plan.direction == -1);
        CHECK(plan.lookAheadMs == 3000 && plan.lookAheadStepMs == 500 && !plan.drawLookAhead);
        CHECK(TurningPlan(0, 12.f, 5, 0).count == 1 && TurningPlan(0, 12.f, 5, 0).direction == 1);

        DungeonKit::LightClock clock(0.f, plan.degPerSec, static_cast<std::uint8_t>(plan.count), plan.direction);
        CHECK(Near(std::fabs(DiffDeg(clock.BearingOf(0), clock.BearingOf(1))), 180.f));   // opposite
        clock.Advance(30000);       // a full turn in 30 s
        CHECK(Near(DiffDeg(clock.Bearing(), 0.f), 0.f, 0.1f));
        // MA4: the reversal stops 2 s, then turns the other way
        clock.Reverse(Tune::kReverseStopMs);
        clock.Advance(Tune::kReverseStopMs);
        CHECK(Near(DiffDeg(clock.Bearing(), 0.f), 0.f, 0.1f));
        clock.Advance(5000);
        CHECK(Near(DiffDeg(clock.Bearing(), 0.f), 60.f, 0.1f));
        // MA2: +10% per Spotted, additive, no cap
        CHECK(Near(SpeedAfter(12.f, 0.f), 12.f));
        CHECK(Near(SpeedAfter(12.f, 30.f), 15.6f));
        CHECK(Near(SpeedAfter(12.f, 200.f), 36.f));
        CHECK(Near(SpeedAfter(12.f, -5.f), 12.f));
        // the reversal roll
        CHECK(ReversalInMs(Tune::kReverseMinMs, Tune::kReverseMaxMs, 0.f) == 15000);
        CHECK(ReversalInMs(Tune::kReverseMinMs, Tune::kReverseMaxMs, 1.f) == 25000);
        CHECK(ReversalInMs(Tune::kReverseMinMs, Tune::kReverseMaxMs, 0.5f) == 20000);
        CHECK(ReversalInMs(Tune::kReverseMinMs, Tune::kReverseMaxMs, 7.f) == 25000);
        CHECK(ReversalInMs(9000, 9000, 0.3f) == 9000);
        // the shared latch (KT-G Q2): one Spotted per player per 3 s across both lights
        DungeonKit::TouchLatch latch;
        CHECK(latch.Try(7, 1000, Tune::kSpottedLatchMs));
        CHECK(!latch.Try(7, 3999, Tune::kSpottedLatchMs));
        CHECK(latch.Try(7, 4000, Tune::kSpottedLatchMs));
        CHECK(latch.Try(8, 4000, Tune::kSpottedLatchMs));
    }

    void TestBearings()
    {
        CHECK(Near(BearingTo({ 0.f, 0.f }, { 1.f, 0.f }), 0.f));
        CHECK(Near(BearingTo({ 0.f, 0.f }, { 0.f, 1.f }), DungeonKit::kPi / 2.f));
        CHECK(Near(BearingTo({ 0.f, 0.f }, { 0.f, -1.f }), 3.f * DungeonKit::kPi / 2.f));
    }

    // R-1-B m1: the bots' band starts past a hunter's Auto Shot too-close line (5 + 2.4 + 1.5 + 4/3 = 10.23 yd).
    void TestBand()
    {
        CHECK(Near(Tune::kHunterTooCloseYd, 10.233f, 0.01f));
        CHECK(Tune::kBandMinYd > Tune::kHunterTooCloseYd);
        CHECK(Tune::kBandMaxYd < Tune::kBotFloorYd);
    }

    // R-1-B m4, rule 19: an arriving unit takes a tank first (the nearest to the door of two), else the nearest player.
    void TestArrival()
    {
        CHECK(PickArrival({}) == 0);
        CHECK(PickArrival({ { false, 9.f }, { true, 20.f }, { false, 3.f } }) == 1);
        CHECK(PickArrival({ { true, 20.f }, { false, 3.f }, { true, 12.f } }) == 2);
        CHECK(PickArrival({ { false, 9.f }, { false, 3.f }, { false, 5.f } }) == 1);
        CHECK(PickArrival({ { false, 9.f } }) == 0);
    }
}

int main()
{
    TestSliceAndIds();
    TestSpots();
    TestFightFloor();
    TestTimeline();
    TestSweep();
    TestTurning();
    TestBearings();
    TestBand();
    TestArrival();
    return Report("gnomer_alert_test");
}
