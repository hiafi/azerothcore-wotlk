// Host tests for HerodLogic.h (D11: Herod, "Blades of Light"): the slice and the ids, the hall (the pit, the ledge
// band, the lap's route against the NAVMESH numbers, the door's entry spot, the garrison's march), the beats and the
// tuning against the build spec, the blades' lanes and waves, the whirling axe's path, the rules and the clock.
#include "HerodLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace ScarletMonasteryRework;
using namespace SmHerod;
using DungeonKit::Distance;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    Vec2 Center()
    {
        return { kPitCenter.x, kPitCenter.y };
    }

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 212980u);
        CHECK(kSpellSlice.last == 213019u);
        CHECK(SPELL_HB_CYCLONE == 212980u);
        CHECK(SPELL_HB_FRENZY == 212993u);
        CHECK(SPELL_HB_FRENZY <= kSpellSlice.last);
        // Every id distinct and in order (DT pins the same offsets).
        std::set<std::uint32_t> ids{ SPELL_HB_CYCLONE, SPELL_HB_OUT, SPELL_HB_LAP, SPELL_HB_BLADE, SPELL_HB_BLADE_LOOK,
            SPELL_HB_HOME, SPELL_HB_THROW, SPELL_HB_THROW_LOOK, SPELL_HB_AXE_SPIN, SPELL_HB_RETURN, SPELL_HB_WHIRL,
            SPELL_HB_CLEAVE, SPELL_HB_CLEAVE_TANK, SPELL_HB_FRENZY };
        CHECK(ids.size() == 14u);
        CHECK(*ids.begin() == kSpellSlice.first && *ids.rbegin() == kSpellSlice.first + 13);
        // The hard mode's slice is apart (D11H's ids never collide with D11's).
        CHECK(kSpellsCallToArms.first == kSpellSlice.last + 1);
        // Texts: 0-4 stock, 5-8 the hard mode's, 9 the seal's emote (F-2c); the shared header's range covers them.
        CHECK(SAY_AGGRO == 0 && EMOTE_ENRAGED == 4 && SAY_TAUNT_ANSWERED == 5 && EMOTE_GARRISON == 8);
        CHECK(EMOTE_SEAL == 9);
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_HEROD)
            {
                found = true;
                CHECK(r.first == 0 && r.last == EMOTE_SEAL && r.firstNew == 5);
            }
        CHECK(found);
        CHECK(kTextEmoteTaunt == 136u);             // TEXT_EMOTE_TAUNT (SharedDefines.h)
        CHECK(kItemRavager == 7612u);               // creature_equip_template 3975 [DB]
    }

    void TestTheHall()
    {
        // Herod spawns in the pit, inside his arena; the pit's center inside the pit; P3 on the pit floor.
        CHECK(HerodArena().Contains(kHerodSpawn.XY(), kHerodSpawn.z));
        CHECK(ArenaFor(BOSS_HEROD).Contains(kHerodSpawn.XY(), kHerodSpawn.z));
        CHECK(Distance(kHerodSpawn.XY(), Center()) < 4.f);
        CHECK(PitArena().Contains(kHerodSpawn.XY(), kHerodSpawn.z));
        CHECK(PitArena().Contains(Center(), kPitCenter.z));
        CHECK(!PitArena().Contains(LapPoint(0), 12.f));
        CHECK(Distance(Center(), { 1961.2f, -431.8f }) < 1.f);         // P3 (section 3.8)
        // NAVMESH: pit r 13.1, ledge out to 25.5, the safe disc inside the pit's nearest edge (11.1).
        CHECK(Near(kPitRadiusYd, 13.1f) && Near(kHallRadiusYd, 25.5f));
        CHECK(kPitSafeRadiusYd <= 11.1f);
        // The band (G2's herod-lap row: inner 13) covers the ledge and reaches the door (28.2 yd out).
        CHECK(Near(kBandInnerYd, 13.f));
        CHECK(kBandOuterYd >= Distance(Center(), kHerodsDoor.XY()));
        CHECK(kBandOuterYd < Distance(Center(), kHerodsDoor.XY()) + 3.f);
        // The entry spot is inside the arena, on the spur, between the door and the hall, 3 yd from the Lever.
        CHECK(HerodArena().Contains(kHallEntry.XY(), kHallEntry.z));
        CHECK(kHallEntry.x > kHerodsDoor.x && kHallEntry.x < 1945.f);
        CHECK(Distance(kHallEntry.XY(), kHerodsLever.XY()) < 4.5f);
        CHECK(DungeonKit::PointInPolygon(std::span<Vec2 const>(kDoorSpur), kHallEntry.XY()));
        // R-2-ARM M-3: a straggler at the door (x 1932, the cross hall side) is outside the seal's arena (pulled in),
        // and the bots' spur polygon starts where S0's arena spur box does (inside the door).
        CHECK(!HerodArena().Contains({ 1932.f, -431.6f }, 18.7f));
        CHECK(!HerodArena().Contains({ 1933.6f, -431.6f }, 18.f));
        CHECK(HerodArena().Contains({ 1935.f, -431.6f }, 17.5f));
        CHECK(Near(kDoorSpur[0].x, kHerodSpurMinX) && Near(kDoorSpur[3].x, kHerodSpurMinX));
        CHECK(kDoorSpur[0].x > kHerodsDoor.x);
        CHECK(!DungeonKit::PointInPolygon(std::span<Vec2 const>(kDoorSpur), Vec2{ 1933.f, -431.6f }));
    }

    void TestTheLap()
    {
        // 24 points every 15 degrees, each on the ledge band (out of the pit, inside the walls or the door spur).
        for (std::size_t i = 0; i < kLapPointCount; ++i)
        {
            Vec2 const p = LapPoint(i);
            float const r = Distance(p, Center());
            CHECK(r >= 15.f);
            CHECK(r > kBandInnerYd && r < kBandOuterYd);
            CHECK(HerodArena().Contains(p, 12.f) || HerodArena().Contains(p, 16.f));
            float const bearing = DungeonKit::BearingTo(Center(), p);
            CHECK(Near(std::fmod(bearing / kDegToRad + 360.f, 360.f), std::fmod(15.f * i, 360.f), 0.2f));
        }
        // R-2-ARM m-3: the dip probes in the spur's band (under its roof), every other point in the ledge's; a hit
        // on the roof or under the floor falls back to the band's estimate.
        for (std::size_t i = 0; i < kLapPointCount; ++i)
        {
            LapZBand const band = LapZBandOf(i);
            CHECK((i == 12) == (band.estimateZ == kSpurZBand.estimateZ));
            CHECK(band.ProbeZ() <= kHallZMax);
        }
        CHECK(Near(kSpurZBand.ProbeZ(), 20.2f) && Near(kLedgeZBand.ProbeZ(), 17.5f));
        CHECK(Near(kSpurZBand.Pick(17.4f), 17.4f));
        CHECK(Near(kSpurZBand.Pick(23.f), 17.5f));                  // the roof
        CHECK(Near(kSpurZBand.Pick(12.f), 17.5f));                  // under the floor
        CHECK(Near(kSpurZBand.Pick(-200000.f), 17.5f));             // no hit (INVALID_HEIGHT)
        CHECK(Near(kLedgeZBand.Pick(9.3f), 9.3f));
        CHECK(Near(kLedgeZBand.Pick(6.8f), 6.8f));                  // the lowest step, inside the 1 yd slack
        CHECK(Near(kLedgeZBand.Pick(4.f), 12.f));
        CHECK(Near(kLedgeZBand.Pick(18.f), 12.f));
        // Point 0 north, point 6 west (+y), point 12 south in the door spur, point 18 east.
        CHECK(LapPoint(0).x > kPitCenter.x + 19.f);
        CHECK(LapPoint(6).y > kPitCenter.y + 18.f);
        CHECK(LapPoint(12).x < kPitCenter.x - 21.f);
        CHECK(DungeonKit::PointInPolygon(std::span<Vec2 const>(kDoorSpur), LapPoint(12)));
        CHECK(LapPoint(18).y < kPitCenter.y - 18.f);
        // His 5 yd spin at the dip sweeps the spur to within 1.5 yd of the door.
        CHECK(LapPoint(12).x - kSpinRadiusYd <= kHerodsDoor.x + 1.5f);
        // The south half narrows (16-17 yd out), the north is wider (19-20).
        CHECK(Distance(LapPoint(14), Center()) < Distance(LapPoint(0), Center()));
        // NAVMESH: a lap of about 121 yd: 12 s at 10 yd/s, 10 s at 12, 8.6 s at 14.
        float const length = LapLengthYd();
        CHECK(length > 118.f && length < 124.f);
        CHECK(LapMs(10.f) > 11800 && LapMs(10.f) < 12400);
        CHECK(LapMs(12.f) > 9800 && LapMs(12.f) < 10400);
        CHECK(LapMs(14.f) > 8400 && LapMs(14.f) < 8900);
        CHECK(LapMs(0.f) == 0u);
        CHECK(TravelMs(25.f, kDashSpeedYd) == 1000u);
        // A route: 25 points, back to its start, every point once, each step 15 degrees the chosen way.
        for (bool const clockwise : { false, true })
            for (std::size_t start : { std::size_t(0), std::size_t(7), std::size_t(23) })
            {
                std::vector<Vec2> const route = LapRoute(start, clockwise);
                CHECK(route.size() == kLapPointCount + 1);
                CHECK(Near(route.front().x, route.back().x) && Near(route.front().y, route.back().y));
                CHECK(Near(route.front().x, LapPoint(start).x) && Near(route.front().y, LapPoint(start).y));
                Vec2 const second = LapPoint(clockwise ? (start + kLapPointCount - 1) % kLapPointCount
                    : (start + 1) % kLapPointCount);
                CHECK(Near(route[1].x, second.x) && Near(route[1].y, second.y));
                float sum = 0.f;
                for (std::size_t k = 1; k < route.size(); ++k)
                    sum += Distance(route[k - 1], route[k]);
                CHECK(Near(sum, length, 0.1f));
            }
        // The nearest lap point.
        CHECK(NearestLapIndex(LapPoint(5)) == 5u);
        CHECK(NearestLapIndex({ kPitCenter.x - 30.f, kPitCenter.y }) == 12u);
        CHECK(NearestLapIndex({ kPitCenter.x + 30.f, kPitCenter.y + 0.5f }) == 0u);
    }

    void TestBeatsAndTuning()
    {
        // HB1 15 s then 30 s (heroic 25 s); HB2 6 s then 30 s (heroic 25 s); HB3 every 6 s.
        CHECK(kSpinBeat(false).firstMs == 15000u && kSpinBeat(false).everyMs == 30000u);
        CHECK(kSpinBeat(true).firstMs == 15000u && kSpinBeat(true).everyMs == 32000u);    // F-2c: spec 25 s
        CHECK(kThrowBeat(false).firstMs == 6000u && kThrowBeat(false).everyMs == 30000u);
        CHECK(kThrowBeat(true).everyMs == 32000u);
        CHECK(kCleaveBeat.everyMs == 6000u);
        // Hits 30% / 45%; the cleave on the tank 15% / 25%.
        CHECK(Near(kHitPct(false), 30.f) && Near(kHitPct(true), 45.f));
        CHECK(Near(kCleaveTankPct(false), 15.f) && Near(kCleaveTankPct(true), 25.f));
        // Shapes: lanes 10 yd (2.5 s out, 1.5 s home), spin 5 yd, blades 4 yd 1.5 s, throw 5 yd 2 s, return 3 yd 1.5 s,
        // whirl 4 yd at 5 yd/s for 5 s (heroic only) shown 1.5 s ahead, cleave 90 degrees 8 yd 1.5 s.
        CHECK(kOutWarnMs == 2500u && kHomeWarnMs == 1500u && Near(kLaneWidthYd, 10.f) && Near(kSpinRadiusYd, 5.f));
        CHECK(kBladeWarnMs == 1500u && Near(kBladeWidthYd, 4.f));
        CHECK(kThrowWarnMs == 2000u && Near(kThrowRadiusYd, 5.f));
        CHECK(kReturnWarnMs == 1500u && Near(kReturnWidthYd, 3.f));
        CHECK(kWhirlMs(false) == 0u && kWhirlMs(true) == 5000u);
        CHECK(Near(kWhirlSpeedYd, 5.f) && Near(kWhirlRadiusYd, 4.f) && kWhirlAheadMs == 1500u);
        CHECK(Near(kCleaveAngleDeg, 90.f) && Near(kCleaveLengthYd, 8.f) && kCleaveWarnMs == 1500u);
        // The lap at 10 / 12 yd/s; the dashes faster than the lap.
        CHECK(Near(kLapSpeedYd(false), 10.f) && Near(kLapSpeedYd(true), 12.f));
        CHECK(kDashSpeedYd > kLapSpeedYd(true));
        // Frenzy at 50%: +30% speed, +20% Physical damage.
        CHECK(Near(kFrenzyAtPct, 50.f) && Near(kFrenzyHastePct, 30.f) && Near(kFrenzyDamagePct, 20.f));
        // Health: 66k = 49.401 x 1,336; the trainees 400 = 0.5427 x 737.
        CHECK(std::lround(49.401 * kHerodBaseHealthL37Warrior) == 65999 || std::lround(49.401 * 1336) == 66000);
        CHECK(std::abs(std::lround(0.5427 * kTraineeBaseHealthL30Mage) - long(kTraineeHealth(false))) <= 1);
        CHECK(kTraineeHealth(true) == 2500u && kHerodHealth(true) == 320000u);
        CHECK(kTraineeCount == 20u && kTraineeSummonGroup == 1u);
        // A spin from the yell to his return, normal: about 2.5 + 0.7 + 12.1 + 1.5 + 0.7 s (spec "about 16 s").
        std::uint32_t const spinMs = kOutWarnMs + TravelMs(17.f, kDashSpeedYd) + LapMs(kLapSpeedYd(false)) + kHomeWarnMs
            + TravelMs(17.f, kDashSpeedYd);
        CHECK(spinMs > 15000u && spinMs < 19000u);
        // Heroic: a spin plus a throw (2 s, 5 s whirl, 1.5 s return) leave the tank a real melee window in the 32 s
        // cadence (F-2c, D11 Q1: the spec's 25 s left ~1 s); about normal's window (30 s less a spin and a throw).
        std::uint32_t const heroicSpinMs = kOutWarnMs + TravelMs(17.f, kDashSpeedYd) + LapMs(kLapSpeedYd(true))
            + kHomeWarnMs + TravelMs(17.f, kDashSpeedYd);
        std::uint32_t const heroicBusyMs = heroicSpinMs + kThrowWarnMs + kWhirlMs(true) + kReturnWarnMs;
        CHECK(heroicBusyMs + 6000u < kSpinBeat(true).everyMs);
        CHECK(heroicBusyMs + 2000u > 25000u);       // the old cadence's gap, for the record
    }

    void TestBlades()
    {
        // Normal: one every 2 s, after Frenzy every 1.5 s; heroic one every 1.5 s, after Frenzy two every 1 s.
        CHECK(BladePlanFor(false, false).everyMs == 2000u && BladePlanFor(false, false).count == 1u);
        CHECK(BladePlanFor(false, true).everyMs == 1500u && BladePlanFor(false, true).count == 1u);
        CHECK(BladePlanFor(true, false).everyMs == 1500u && BladePlanFor(true, false).count == 1u);
        CHECK(BladePlanFor(true, true).everyMs == 1000u && BladePlanFor(true, true).count == 2u);
        // Waves a lap: normal 5 (spec "five a lap"), after Frenzy 7 (spec "seven"); heroic 5, after Frenzy 8 pairs;
        // the hard mode's 1.5 s pairs at 14 yd/s: 4.
        std::uint32_t const normalLap = LapMs(kLapSpeedYd(false));
        std::uint32_t const heroicLap = LapMs(kLapSpeedYd(true));
        CHECK(BladeWaves(normalLap, BladePlanFor(false, false).everyMs) == 5u);
        CHECK(BladeWaves(normalLap, BladePlanFor(false, true).everyMs) == 7u);
        CHECK(BladeWaves(heroicLap, BladePlanFor(true, false).everyMs) == 5u);
        CHECK(BladeWaves(heroicLap, BladePlanFor(true, true).everyMs) == 8u);
        CHECK(BladeWaves(LapMs(14.f), 1500) == 4u);
        CHECK(BladeWaves(normalLap, 0) == 0u);
        CHECK(BladeWaves(1000, 2000) == 0u);
        // Each wave resolves inside the lap.
        CHECK(5u * 2000u + kBladeWarnMs <= normalLap);
        // A blade from the north lap point toward the pit's center crosses the pit to its far edge: 20.1 + 13.1.
        Vec2 const north = LapPoint(0);
        CHECK(Near(BladeLengthYd(north, Center()), Distance(north, Center()) + kPitRadiusYd, 0.05f));
        // Toward a player in the pit off the center: still to the far edge (longer than the distance to them).
        Vec2 const inPit{ kPitCenter.x - 4.f, kPitCenter.y + 5.f };
        float const len = BladeLengthYd(north, inPit);
        CHECK(len > Distance(north, inPit));
        Vec2 const end = DungeonKit::Advance(north, DungeonKit::BearingTo(north, inPit), len);
        CHECK(Near(Distance(end, Center()), kPitRadiusYd, 0.05f));
        // A target the lane never takes across the pit (beside him on the ledge): the lane ends 4 yd past them.
        Vec2 const beside = LapPoint(1);
        CHECK(Near(BladeLengthYd(north, beside), std::max(kBladeMinYd, Distance(north, beside) + kBladePastTargetYd)));
        // Held to its bounds.
        CHECK(BladeLengthYd(north, north) >= kBladeMinYd);
        CHECK(BladeLengthYd(LapPoint(12), LapPoint(0)) <= kBladeMaxYd);
        // The ray helper: a ray away from the circle misses; through the center from outside it exits far side.
        CHECK(!RayFarCircleExit(Center(), 5.f, { kPitCenter.x + 20.f, kPitCenter.y }, 0.f).has_value());
        CHECK(Near(*RayFarCircleExit(Center(), 5.f, { kPitCenter.x + 20.f, kPitCenter.y }, DungeonKit::kPi), 25.f));
        CHECK(!RayFarCircleExit(Center(), 5.f, { kPitCenter.x + 20.f, kPitCenter.y + 20.f }, DungeonKit::kPi)
            .has_value());
    }

    void TestTheWhirl()
    {
        // From the pit toward a player: 25 yd (5 s at 5 yd/s), cut at 22 yd from the pit's center.
        Vec2 const from = Center();
        Vec2 const aim{ kPitCenter.x + 5.f, kPitCenter.y };
        Vec2 const end = WhirlEnd(from, aim, kWhirlSpeedYd * 5.f);
        CHECK(Near(Distance(end, Center()), kWhirlRoomYd, 0.05f));
        CHECK(end.x > from.x);
        // A short path stays its length.
        Vec2 const shortEnd = WhirlEnd(from, aim, 6.f);
        CHECK(Near(Distance(shortEnd, from), 6.f));
        // A landing spot outside the room whirls its full length.
        Vec2 const outside{ kPitCenter.x + 24.f, kPitCenter.y };
        CHECK(Near(Distance(WhirlEnd(outside, Center(), 10.f), outside), 10.f));
        // On the target itself: it whirls toward the center.
        Vec2 const onIt = WhirlEnd(aim, aim, 4.f);
        CHECK(Distance(onIt, Center()) < Distance(aim, Center()));
        // Its position on the clock: 5 yd/s along the path, holding at the end.
        Vec2 const at2s = WhirlPosAt(from, end, kWhirlSpeedYd, 2000);
        CHECK(Near(Distance(at2s, from), 10.f));
        CHECK(Near(Distance(WhirlPosAt(from, end, kWhirlSpeedYd, 60000), end), 0.f));
        CHECK(Near(Distance(WhirlPosAt(from, end, kWhirlSpeedYd, 0), from), 0.f));
        CHECK(Near(Distance(WhirlPosAt(from, from, kWhirlSpeedYd, 3000), from), 0.f));
        // The whirl's path stays in the hall's arena.
        CHECK(HerodArena().Contains(end, 12.f) || HerodArena().Contains(end, 7.f));
        // R-2-ARM m-4: a pit landing whirls inside the pit's disc (never up the steps), aimed at a ledge player.
        CHECK(LandedInPit(kPitCenter.z) && LandedInPit(7.6f) && !LandedInPit(12.f));
        Vec2 const pitSpot{ kPitCenter.x + 5.f, kPitCenter.y };
        Vec2 const ledgeAim{ kPitCenter.x + 20.f, kPitCenter.y };
        Vec2 const pitEnd = WhirlEnd(pitSpot, ledgeAim, kWhirlSpeedYd * 6.f, WhirlRoomYd(pitSpot, true));
        CHECK(Distance(pitEnd, Center()) <= kPitRadiusYd + 0.01f);
        CHECK(Distance(WhirlEnd(pitSpot, ledgeAim, kWhirlSpeedYd * 6.f), Center()) > kPitRadiusYd);   // the old room
        Vec2 const corner{ kPitCenter.x + 14.f, kPitCenter.y };     // past the disc, in a corner of the hexagon
        CHECK(Near(WhirlRoomYd(corner, true), 14.5f));
        CHECK(Distance(WhirlEnd(corner, ledgeAim, 10.f, WhirlRoomYd(corner, true)), Center()) <= 14.51f);
        CHECK(Near(WhirlRoomYd(pitSpot, true), kPitRadiusYd));
        CHECK(Near(WhirlRoomYd(ledgeAim, false), kWhirlRoomYd));
        // Its height follows the path: a ledge throw (z 12) whirling down to the pit floor (6.4) is at pit height
        // at its end and halfway between at the middle.
        Vec2 const ledgeFrom{ kPitCenter.x + 18.f, kPitCenter.y };
        Vec2 const pitTo{ kPitCenter.x + 2.f, kPitCenter.y };
        CHECK(Near(WhirlZAt(ledgeFrom, 12.f, pitTo, 6.4f, pitTo), 6.4f));
        CHECK(Near(WhirlZAt(ledgeFrom, 12.f, pitTo, 6.4f, ledgeFrom), 12.f));
        CHECK(Near(WhirlZAt(ledgeFrom, 12.f, pitTo, 6.4f, { kPitCenter.x + 10.f, kPitCenter.y }), 9.2f));
        CHECK(Near(WhirlZAt(ledgeFrom, 12.f, ledgeFrom, 6.4f, ledgeFrom), 12.f));      // no path
        // The end's probe: a hall height, else the landing's.
        CHECK(Near(WhirlEndZ(6.5f, 12.f), 6.5f));
        CHECK(Near(WhirlEndZ(-200000.f, 12.f), 12.f));
        CHECK(Near(WhirlEndZ(25.f, 12.f), 12.f));
    }

    void TestRules()
    {
        CHECK(CleaveAllowed(false, false, false));
        CHECK(!CleaveAllowed(true, false, false));
        CHECK(!CleaveAllowed(false, true, false));
        CHECK(!CleaveAllowed(false, false, true));
        CHECK(SpinAllowed(false, false));
        CHECK(!SpinAllowed(true, false));
        CHECK(!SpinAllowed(false, true));
        CHECK(ThrowAllowed(false, false, true));
        CHECK(!ThrowAllowed(true, false, true));
        CHECK(!ThrowAllowed(false, true, true));
        CHECK(!ThrowAllowed(false, false, false));      // the hard mode's second half: the axe planted
        CHECK(ThresholdReady(50.f, 50.f, false, false));
        CHECK(ThresholdReady(12.f, 50.f, false, false));
        CHECK(!ThresholdReady(50.1f, 50.f, false, false));
        CHECK(!ThresholdReady(40.f, 50.f, true, false));    // mid-spin: waits for his return
        CHECK(!ThresholdReady(40.f, 50.f, false, true));    // the axe out: waits for it
        // R-2-ARM M-2: crossed and not acted on, no new spin or throw starts.
        CHECK(ThresholdPending(50.f, 50.f, false) && !BeatMayStart(true));
        CHECK(!ThresholdPending(50.1f, 50.f, false) && BeatMayStart(false));
        CHECK(!ThresholdPending(10.f, 50.f, true));
    }

    void TestGarrisonMarch()
    {
        // Section 7 #31 A: a straight line from the door down the south side, a jump off the landing's lip into the
        // pit, on to the pillar 3 yd short of the center; about 12 s at 2.5 yd/s.
        float length = 0.f;
        for (std::size_t i = 1; i < kGarrisonMarch.size(); ++i)
            length += Distance(kGarrisonMarch[i - 1].XY(), kGarrisonMarch[i].XY());
        float const seconds = length / kGarrisonPaceYd;
        CHECK(seconds > 9.f && seconds < 13.5f);
        CHECK(Distance(kGarrisonMarch.front().XY(), kHerodsDoor.XY()) < 3.f);
        CHECK(Near(Distance(kGarrisonMarch.back().XY(), Center()), 3.f, 0.1f));
        CHECK(kGarrisonMarch[kGarrisonJumpFrom].z > kGarrisonMarch[kGarrisonJumpFrom + 1].z + 5.f);
        CHECK(PitArena().Contains(kGarrisonMarch[kGarrisonJumpFrom + 1].XY(), kGarrisonMarch[kGarrisonJumpFrom + 1].z));
        for (Point3 const& p : kGarrisonMarch)
            CHECK(HerodArena().Contains(p.XY(), p.z));
        // Four abreast inside the 5 yd spur.
        CHECK(kGarrisonLaneOffsetsYd.front() >= -2.5f && kGarrisonLaneOffsetsYd.back() <= 2.5f);
    }

    void TestBeatClock()
    {
        BeatClock clock;
        CHECK(!clock.Due(100000));
        clock.Start(0, 15000);
        CHECK(!clock.Due(14999));
        CHECK(clock.Due(15000));
        // A spin that waited 3 s for the axe keeps the next one on schedule.
        clock.Fired(18000, 30000);
        CHECK(clock.DueMs() == 45000u);
        // A long hold: never in the past.
        clock.Fired(90000, 30000);
        CHECK(clock.DueMs() == 120000u);
        clock.Stop();
        CHECK(!clock.Due(200000));
    }

    void TestSkeleton()
    {
        // Wave 2; the end boss's hard mode kill slot; the instance's flag for the taunt.
        CHECK(IsWave2Boss(BOSS_HEROD));
        CHECK(HardModeKillSlot(BOSS_HEROD) == BOSS_CALL_TO_ARMS);
        CHECK(HardModeFlagData(BOSS_CALL_TO_ARMS) == DATA_HARD_MODE_HEROD);
        // The taunt is judged by the shared rule (D11H): heroic, out of combat, wave 2 bound.
        CHECK(HerodTauntAllowed(true, DungeonKit::State::NotStarted, false, true));
        CHECK(!HerodTauntAllowed(false, DungeonKit::State::NotStarted, false, true));
        CHECK(!HerodTauntAllowed(true, DungeonKit::State::InProgress, false, true));
        // The Lever is inert while he fights; the door opens on his death or a wipe.
        CHECK(!HerodsLeverUsable(DungeonKit::State::InProgress));
        CHECK(HerodsDoorMoveFor(DungeonKit::State::InProgress, DungeonKit::State::Done) == DoorMove::Open);
    }
}

int main()
{
    TestSliceAndIds();
    TestTheHall();
    TestTheLap();
    TestBeatsAndTuning();
    TestBlades();
    TestTheWhirl();
    TestRules();
    TestGarrisonMarch();
    TestBeatClock();
    TestSkeleton();

    return Report("sm_herod_test");
}
