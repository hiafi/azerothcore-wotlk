// Host tests for HerodHardModeLogic.h (D11H: Herod's hard mode, Call to Arms): the slice and the ids, the trigger's
// answers, the tuning as ratios of D11's heroic values against the build spec's numbers, the prayer's heal, the
// garrison's squads and march (section 7 #31 A), Zeal, the beams round the planted axe (clipped at the pit), the
// hall's ticks, the halves, the rack's spot and the rule 20 numbers.
#include "HerodHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <cstdio>
#include <set>

using namespace ScarletMonasteryRework;
using namespace SmCallToArms;
using DungeonKit::Distance;
using DungeonKit::State::Done;
using DungeonKit::State::Fail;
using DungeonKit::State::InProgress;
using DungeonKit::State::NotStarted;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    Vec2 PitCenter()
    {
        return { SmHerod::kPitCenter.x, SmHerod::kPitCenter.y };
    }

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 213020u);
        CHECK(kSpellSlice.last == 213059u);
        std::set<std::uint32_t> const ids{ SPELL_CTA_AURA, SPELL_CTA_PRAYER, SPELL_CTA_PILLAR, SPELL_CTA_ZEAL,
            SPELL_CTA_FADE, SPELL_CTA_GLOW, SPELL_CTA_BEAM_LOOK, SPELL_CTA_BEAM, SPELL_CTA_HALL, SPELL_CTA_HALL_LOOK };
        CHECK(ids.size() == 10u);
        for (std::uint32_t id : ids)
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_CTA_AURA == 213020u);
        CHECK(SPELL_CTA_HALL_LOOK == 213029u);
        // never one of D11's (its slice ends at 213019)
        CHECK(!SmHerod::kSpellSlice.Contains(SPELL_CTA_AURA));
        // the hard mode's kill slot, its flag, its arena (S0)
        CHECK(IsHardModeSlot(BOSS_CALL_TO_ARMS));
        CHECK(!ArenaFor(BOSS_CALL_TO_ARMS).Empty());
        CHECK(HardModeFlagData(BOSS_CALL_TO_ARMS) == DATA_HARD_MODE_HEROD);
        // the units and objects are S0's ids
        CHECK(NPC_SM_GARRISON_TRAINEE == 300944u);
        CHECK(NPC_SM_PLANTED_RAVAGER == 300945u);
        CHECK(GO_SM_WALL_RACK == 301328u);
        CHECK(GO_SM_PLANTED_AXE == 301329u);
        // tags never meet D11's (2, 3, 11-15, 21, 22)
        for (std::uint32_t tag : { 2u, 3u, 11u, 12u, 13u, 14u, 15u, 21u, 22u })
            CHECK(TAG_HM_BEAM != tag);
        // the items (V's ITEM_HEROD_BLADE, ITEM_TRAINEE_MACE)
        CHECK(kItemCrusaderBlade == 39802u);
        CHECK(kItemTraineeMace == 2813u);
        // the texts D11 names for D11H (groups 5-8, inside S0's range for 3975)
        CHECK(SmHerod::SAY_TAUNT_ANSWERED == 5);
        CHECK(SmHerod::SAY_TAUNT_WORDS == 6);
        CHECK(SmHerod::SAY_RISING == 7);
        CHECK(SmHerod::EMOTE_GARRISON == 8);
        CHECK(SmHerod::kTextEmoteTaunt == 136u);
    }

    void TestTaunt()
    {
        // heroic, out of combat, not lit, Herod idle, wave 2 bound: the challenge
        CHECK(TauntAnswerFor(true, true, false, false, NotStarted, true) == TauntAnswer::Challenge);
        CHECK(TauntAnswerFor(true, true, false, false, Fail, true) == TauntAnswer::Challenge);
        // normal, in combat, already lit, killed or fighting: words
        CHECK(TauntAnswerFor(true, false, false, false, NotStarted, true) == TauntAnswer::Words);
        CHECK(TauntAnswerFor(true, true, true, false, InProgress, true) == TauntAnswer::Words);
        CHECK(TauntAnswerFor(true, true, true, false, NotStarted, true) == TauntAnswer::Words);
        CHECK(TauntAnswerFor(true, true, false, true, NotStarted, true) == TauntAnswer::Words);
        CHECK(TauntAnswerFor(true, true, false, false, Done, true) == TauntAnswer::Words);
        // wave 2 unbound: the instance refuses it (D11's AI does not run then anyway)
        CHECK(TauntAnswerFor(true, true, false, false, NotStarted, false) == TauntAnswer::Words);
        CHECK(TauntAnswerFor(true, true, false, false, NotStarted) ==
            (kWave2Bound ? TauntAnswer::Challenge : TauntAnswer::Words));
        // dead: nothing
        CHECK(TauntAnswerFor(false, true, false, false, NotStarted, true) == TauntAnswer::None);
        // the words' cooldown
        CHECK(kWordsCooldownMs == 30000u);
        CHECK(WordsReady(0, 0));
        CHECK(!WordsReady(1000, 30000));
        CHECK(WordsReady(30000, 30000));
    }

    void TestTuning()
    {
        // the build spec's hard mode numbers, reached as ratios of D11's heroic values
        CHECK(kHerodHealth == 400000u);
        CHECK(SmHerod::kHerodHealth.heroic == 320000u);
        CHECK(HardModeHealth(400000) == 500000u);                  // a retune of D11's heroic carries over
        CHECK(kSpinEveryMs == 28160u);                          // D11's heroic 32 s (F-2c) x 0.88
        CHECK(kThrowEveryMs == 28160u);
        CHECK(HardModeEveryMs(30000) == 26400u);
        CHECK(Near(kLapSpeedYd, 14.f, 0.001f));
        CHECK(kBlades.everyMs == 1500u);
        CHECK(kBlades.count == 2u);
        CHECK(kWhirlMs == 6000u);
        CHECK(Near(kHitPct, 60.f, 0.001f));
        CHECK(Near(kBeamPct, 45.f, 0.001f));
        CHECK(Near(kThresholdPct, 50.f, 0.001f));
        // harder than heroic everywhere
        CHECK(kSpinEveryMs < SmHerod::kSpinBeat.heroic.everyMs);
        CHECK(kLapSpeedYd > SmHerod::kLapSpeedYd.heroic);
        CHECK(kWhirlMs > SmHerod::kWhirlMs.heroic);
        CHECK(kHitPct > SmHerod::kHitPct.heroic);
        // the lap at 14 yd/s: about 8.6 s (NAVMESH)
        std::uint32_t const lapMs = SmHerod::LapMs(kLapSpeedYd);
        CHECK(lapMs > 8000u && lapMs < 9200u);
        // blades through the lap: one pair every 1.5 s, the last resolving before the lap ends
        std::uint32_t const waves = SmHerod::BladeWaves(lapMs, kBlades.everyMs);
        CHECK(waves >= 4u && waves <= 5u);
    }

    // R-2-ARM M-2: D11's tick order (threshold, spin end, axe home, threshold again, then a beat may start unless the
    // threshold is pending) on the hard mode's first half: a spin of `spinMs`, a throw of `throwMs`, both every
    // `everyMs` from D11's heroic firsts. Returns the ms from the crossing to the prayer (or ~0 when never).
    std::uint64_t PrayerDelayMs(std::uint64_t crossMs, std::uint32_t everyMs, std::uint32_t spinMs,
        std::uint32_t throwMs, bool fixed)
    {
        SmHerod::BeatClock spinClock;
        SmHerod::BeatClock throwClock;
        spinClock.Start(0, SmHerod::kSpinBeat.heroic.firstMs);
        throwClock.Start(0, SmHerod::kThrowBeat.heroic.firstMs);
        bool spinning = false;
        bool axeOut = false;
        bool done = false;
        std::uint64_t spinEnd = 0;
        std::uint64_t axeEnd = 0;
        for (std::uint64_t t = 0; t < crossMs + 120000; t += 100)
        {
            float const health = t >= crossMs ? 49.f : 80.f;
            auto threshold = [&]
            {
                if (!done && SmHerod::ThresholdReady(health, kThresholdPct, spinning, axeOut))
                    done = true;
            };
            threshold();
            if (done)
                return t - crossMs;
            if (spinning && t >= spinEnd)
                spinning = false;
            if (axeOut && t >= axeEnd)
                axeOut = false;
            if (fixed)
            {
                threshold();
                if (done)
                    return t - crossMs;
            }
            bool const gate = !fixed || SmHerod::BeatMayStart(SmHerod::ThresholdPending(health, kThresholdPct, done));
            if (gate && !spinning && SmHerod::SpinAllowed(axeOut, false) && spinClock.Due(t))
            {
                spinClock.Fired(t, everyMs);
                spinning = true;
                spinEnd = t + spinMs;
            }
            else if (gate && !axeOut && SmHerod::ThrowAllowed(spinning, false, true) && throwClock.Due(t))
            {
                throwClock.Fired(t, everyMs);
                axeOut = true;
                axeEnd = t + throwMs;
            }
        }
        return ~std::uint64_t(0);
    }

    void TestThresholdCadence()
    {
        // The hard mode's spin (2.5 s marker, two ~0.8 s dashes, the 8.6 s lap, 1.5 s home) and throw (2 s + the 6 s
        // whirl + 1.5 s return), as R-2-ARM measured them.
        std::uint32_t const spinMs = SmHerod::kOutWarnMs + 800 + SmHerod::LapMs(kLapSpeedYd) + SmHerod::kHomeWarnMs
            + 800;
        std::uint32_t const throwMs = SmHerod::kThrowWarnMs + kWhirlMs + SmHerod::kReturnWarnMs;
        CHECK(spinMs > 13000u && spinMs < 15000u);
        CHECK(throwMs == 9500u);
        // The old order on the old 22 s cadence: back to back, the prayer starves (the bug).
        CHECK(PrayerDelayMs(40000, 22000, spinMs, throwMs, false) > 100000u);
        // The fixed order: the prayer fires as soon as the running beat ends, on the old and the new cadence, for a
        // crossing at any moment of the fight.
        std::uint64_t worst = 0;
        for (std::uint32_t const every : { 22000u, kSpinEveryMs })
            for (std::uint64_t cross = 0; cross < 120000; cross += 700)
            {
                std::uint64_t const delay = PrayerDelayMs(cross, every, spinMs, throwMs, true);
                CHECK(delay <= std::max(spinMs, throwMs));
                worst = std::max(worst, delay);
            }
        std::printf("threshold: the prayer at most %.1f s after the 50%% crossing\n",
            static_cast<double>(worst) / 1000.0);
        // The new cadence leaves the tank a melee window every cycle (F-2c: D11 Q1's ~1 s on heroic).
        CHECK(kSpinEveryMs > spinMs + throwMs + 4000u);
    }

    void TestPrayer()
    {
        CHECK(kPrayerMs == 20000u);
        CHECK(PrayerHealth(200000, 400000, 0) == 200000u);
        CHECK(PrayerHealth(200000, 400000, 10000) == 300000u);
        CHECK(PrayerHealth(200000, 400000, 19999) < 400000u);
        CHECK(PrayerHealth(200000, 400000, 20000) == 400000u);
        CHECK(PrayerHealth(200000, 400000, 90000) == 400000u);
        CHECK(PrayerHealth(150000, 400000, 10000) == 275000u);     // a burst past 50%: still full at 20 s
        CHECK(PrayerHealth(400000, 400000, 0) == 400000u);
        CHECK(PrayerHealth(500000, 400000, 0) == 400000u);
        // monotone, never above full
        std::uint32_t last = 0;
        for (std::uint64_t t = 0; t <= kPrayerMs; t += kPrayerTickMs)
        {
            std::uint32_t const h = PrayerHealth(123456, 400000, t);
            CHECK(h >= last);
            CHECK(h <= 400000u);
            last = h;
        }
        // the kneel: the pillar 3 yd short of the pit's center, facing the planted axe at the center
        CHECK(Near(Distance(kKneelSpot.XY(), PitCenter()), 3.f, 0.01f));
        CHECK(Near(Distance(kAxeSpot.XY(), PitCenter()), 0.f, 0.001f));
        CHECK(Near(DungeonKit::BearingTo(kKneelSpot.XY(), kAxeSpot.XY()), kKneelFacing, 0.01f));
        CHECK(kKneelSpot.z >= SmHerod::kPitZMin && kKneelSpot.z <= SmHerod::kPitZMax);
        CHECK(kKneelWalkMaxMs < kSquadEveryMs);
    }

    void TestSquads()
    {
        CHECK(kSquadCount == 3u);
        CHECK(kSquadSize == 4u);
        CHECK(kGarrisonCount == 12u);
        CHECK(SquadsDue(0) == 1u);
        CHECK(SquadsDue(4999) == 1u);
        CHECK(SquadsDue(5000) == 2u);
        CHECK(SquadsDue(10000) == 3u);
        CHECK(SquadsDue(60000) == 3u);
        // the door: sealed again after the last squad stepped in, shut about 15 s in, inside the prayer
        std::uint32_t const lastSquadMs = (kSquadCount - 1) * kSquadEveryMs;
        CHECK(kResealAtMs > lastSquadMs);
        CHECK(kResealAtMs + kDoorShutDelayMs == 15000u);
        CHECK(kResealAtMs + kDoorShutDelayMs < kPrayerMs);
    }

    void TestMarch()
    {
        CHECK(kRoutePoints == 5u);
        CHECK(kJumpFromIndex == 2u);
        CHECK(kJumpToIndex == 3u);
        CHECK(kLastIndex == 4u);
        std::set<int> ys;
        for (std::size_t lane = 0; lane < kSquadSize; ++lane)
        {
            auto const route = MarchRoute(lane);
            // behind the door line (x 1933.69), at most 3 yd back: they march through the opened door
            CHECK(route[0].x < kHerodsDoor.x);
            CHECK(kHerodsDoor.x - route[0].x < 3.f);
            // the line of section 7 #31 A, shifted across by the lane's offset
            for (std::size_t i = 1; i < kRoutePoints - 1; ++i)
            {
                CHECK(Near(route[i].x, SmHerod::kGarrisonMarch[i - 1].x, 0.001f));
                CHECK(Near(route[i].y, SmHerod::kGarrisonMarch[i - 1].y + SmHerod::kGarrisonLaneOffsetsYd[lane],
                    0.001f));
            }
            // northward all the way (x grows)
            for (std::size_t i = 1; i < kRoutePoints; ++i)
                CHECK(route[i].x > route[i - 1].x);
            // the lip is above the pit, the landing on its floor (the jump), the halt in the pit
            CHECK(route[kJumpFromIndex].z > SmHerod::kPitZMax);
            CHECK(route[kJumpToIndex].z <= SmHerod::kPitZMax);
            Vec2 const halt{ route[kLastIndex].x, route[kLastIndex].y };
            CHECK(Distance(halt, PitCenter()) <= SmHerod::kPitSafeRadiusYd);
            // the halt: kPillarShortYd south of the pillar on its lane (Herod kneels on the pillar itself)
            CHECK(Near(route[kLastIndex].x, kKneelSpot.x - kPillarShortYd, 0.001f));
            CHECK(Distance(halt, kKneelSpot.XY()) >= kPillarShortYd - 0.001f);
            CHECK(Distance(halt, kKneelSpot.XY()) < 2.6f);
            // every point inside Herod's hall (pit, ledge, door spur) but the spawn behind the door
            for (std::size_t i = 1; i < kRoutePoints; ++i)
                CHECK(HerodArena().Contains({ route[i].x, route[i].y }, route[i].z));
            ys.insert(static_cast<int>(std::lround(route[kLastIndex].y * 10.f)));
        }
        CHECK(ys.size() == kSquadSize);                         // four abreast
        // the lanes are 1.2 yd apart and fit the 5 yd spur (y -429 to -434.2)
        auto const west = MarchRoute(0);
        auto const east = MarchRoute(3);
        CHECK(Near(std::fabs(west[1].y - east[1].y), 3.6f, 0.01f));
        for (std::size_t lane = 0; lane < kSquadSize; ++lane)
        {
            float const y = MarchRoute(lane)[1].y;
            CHECK(y < -429.f && y > -434.2f);
        }
        // spawn to halt: about 12 s at 2.5 yd/s (section 7 #31 A; D11 said about 11 s)
        std::uint32_t const marchMs = MarchMs();
        std::printf("march: %.1f yd walked, %u ms\n", static_cast<double>(WalkedYd(MarchRoute(0))), marchMs);
        CHECK(marchMs >= 8000u && marchMs <= 13000u);
        CHECK(Near(kMarchPaceYd, 2.5f, 0.001f));
        // the last squad arrives before the prayer ends (its 10 s + the march)
        CHECK((kSquadCount - 1) * kSquadEveryMs + marchMs < kPrayerMs + 1000u);
        // the knockback rule: in the pit before the jump: straight to the halt; on the spur or the ledge: on its leg
        CHECK(NextLeg(1, 6.5f) == kLastIndex);
        CHECK(NextLeg(2, 7.f) == kLastIndex);
        CHECK(NextLeg(3, 6.6f) == kLastIndex);
        CHECK(NextLeg(1, 18.f) == 1u);
        CHECK(NextLeg(2, 12.f) == 2u);
        CHECK(NextLeg(kLastIndex, 6.4f) == kLastIndex);
        // arrival
        CHECK(Arrived(0.f));
        CHECK(Arrived(kArriveYd));
        CHECK(!Arrived(kArriveYd + 0.1f));
        CHECK(kLegReachYd <= kArriveYd);
        CHECK(kMarchLifeMs > kPrayerMs * 3);
    }

    void TestZeal()
    {
        CHECK(kZealPct == 5u);
        CHECK(kZealMax == 6u);                                   // HANDOFF section 10 add sizing C
        CHECK(kZealMax < kGarrisonCount);
        CHECK(ZealAfterArrival(0) == 1u);
        CHECK(ZealAfterArrival(5) == 6u);
        CHECK(ZealAfterArrival(6) == 6u);                        // capped at six
        CHECK(ZealAfterArrival(11) == 6u);
        CHECK(Near(MeleeLoad(0, false), 1.f, 0.001f));
        CHECK(Near(MeleeLoad(0, true), 1.3f * 1.2f, 0.001f));    // D11's Frenzy alone
        CHECK(Near(MeleeLoad(12, true), 1.6f * 1.6f * 1.3f * 1.2f, 0.01f));
        CHECK(Near(MeleeLoad(kZealMax, true), 1.3f * 1.3f * 1.3f * 1.2f, 0.01f));    // the most he can reach
        std::printf("melee load: 0 stacks %.2fx, 6 stacks %.2fx, 12 stacks %.2fx (frenzied, against plain heroic)\n",
            static_cast<double>(MeleeLoad(0, true)), static_cast<double>(MeleeLoad(6, true)),
            static_cast<double>(MeleeLoad(12, true)));
    }

    void TestBeams()
    {
        CHECK(kBeamCount == 2);
        CHECK(Near(kBeamStepDeg, 30.f, 0.001f));
        CHECK(kBeamStepMs == 1500u);
        CHECK(kBeamTurnMs == 18000u);                            // "a full turn about 18 s"
        CHECK(Near(kBeamWidthYd, 4.f, 0.001f));
        CHECK(Near(kBeamInnerYd, 3.f, 0.001f));
        // every step's lane: from 3 yd off the axe to 0.5 yd short of the pit's edge (G2's turning-beams row: 3 to
        // 13 yd, a 10 yd line)
        DungeonKit::Arena const pit = SmHerod::PitArena();
        for (int step = 0; step < 12; ++step)
        {
            float const bearing = static_cast<float>(step) * kBeamStepDeg * DungeonKit::kPi / 180.f;
            std::optional<DungeonKit::BeamLane> const lane = BeamLaneAt(bearing);
            CHECK(lane.has_value());
            if (!lane)
                continue;
            CHECK(lane->clipped);
            CHECK(Near(Distance(lane->from, kAxeSpot.XY()), kBeamInnerYd, 0.01f));
            CHECK(Near(Distance(lane->to, PitCenter()), SmHerod::kPitRadiusYd - kBeamInsetYd, 0.02f));
            CHECK(lane->length > 9.f && lane->length < 10.5f);
            CHECK(pit.Contains(lane->to, kAxeSpot.z));
            // the kit's own clip (TurningBeams `clip` = PitArena) agrees
            std::optional<float> const wall = pit.RayToEdge(kAxeSpot.XY(), kAxeSpot.z, bearing);
            CHECK(wall.has_value() && Near(*wall, SmHerod::kPitRadiusYd, 0.02f));
        }
        // the halt and the kneel are inside the beams' 3 yd hole? The kneel is on its edge (3 yd), the halt beyond
        CHECK(Distance(kKneelSpot.XY(), kAxeSpot.XY()) <= kBeamInnerYd + 0.01f);
        CHECK(kGlowEveryMs == 4000u);
        // the space math: two beams and their marked next steps, about 4 x 9.6 yd each: about 150-180 sq yd
        float const strips = 4.f * kBeamWidthYd * BeamLaneAt(0.f)->length;
        CHECK(strips > 140.f && strips < 190.f);
    }

    void TestHall()
    {
        CHECK(kHallTickMs == 2000u);
        CHECK(kHallHundredths == 400u);                          // 2% a second, 4% a tick
        CHECK(HallHundredthsPerTick(2.f, 1000) == 200u);
        CHECK(HallHundredthsPerTick(1.f, 2000) == 200u);
    }

    void TestHalves()
    {
        CHECK(ThrowsAllowed(Half::First));
        CHECK(!ThrowsAllowed(Half::Prayer));
        CHECK(!ThrowsAllowed(Half::Second));
        CHECK(!BeamsFlipOnSpin(Half::First));
        CHECK(!BeamsFlipOnSpin(Half::Prayer));
        CHECK(BeamsFlipOnSpin(Half::Second));
        CHECK(kSpinAfterRisingMs == SmHerod::kSpinBeat.heroic.firstMs);
        CHECK(kGarrisonPriority > 0);                            // above Herod (0)
    }

    void TestRack()
    {
        // on the pit floor at its east wall, facing the center
        CHECK(kRackSpot.z >= SmHerod::kPitZMin && kRackSpot.z <= SmHerod::kPitZMax);
        float const r = Distance(kRackSpot.XY(), PitCenter());
        CHECK(r > 11.f && r < 13.6f);
        CHECK(Near(DungeonKit::BearingTo(kRackSpot.XY(), PitCenter()), kRackFacing, 0.01f));
        // clear of the march's halt and the Fine Chairs (97801 (1951.79, -436.72), 97802 (1972.01, -437.26))
        for (std::size_t lane = 0; lane < kSquadSize; ++lane)
        {
            auto const halt = MarchRoute(lane)[kLastIndex];
            CHECK(Distance(kRackSpot.XY(), { halt.x, halt.y }) > 8.f);
        }
        CHECK(Distance(kRackSpot.XY(), { 1951.79f, -436.72f }) > 5.f);
        CHECK(Distance(kRackSpot.XY(), { 1972.01f, -437.26f }) > 5.f);
    }

    // Rule 20 (LESSONS 4.2): spec groups kill the march; a bot group single-target does not.
    void TestRule20()
    {
        std::uint32_t const marchMs = MarchMs();
        std::uint32_t const human = TraineesKilled(3774.f, 1, 5000, marchMs);
        std::uint32_t const botsSingle = TraineesKilled(700.f, 1, 5000, marchMs);
        std::uint32_t const botsAoe = TraineesKilled(700.f, 4, 5000, marchMs);
        std::printf("rule 20: march window %.1f s; killed of 12: spec group %u, bots single target %u, "
            "bots AoE on 4 %u\n",
            static_cast<double>((kSquadCount - 1) * kSquadEveryMs + marchMs) / 1000.0, human, botsSingle, botsAoe);
        CHECK(human == kGarrisonCount);
        CHECK(botsSingle < human);
        CHECK(botsAoe >= botsSingle);
        CHECK(TraineesKilled(1000.f, 1, 0, marchMs) == kGarrisonCount);
    }
}

int main()
{
    TestSliceAndIds();
    TestTaunt();
    TestTuning();
    TestThresholdCadence();
    TestPrayer();
    TestSquads();
    TestMarch();
    TestZeal();
    TestBeams();
    TestHall();
    TestHalves();
    TestRack();
    TestRule20();
    return Report("sm_herod_hard_mode_test");
}
