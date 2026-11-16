// Host tests for DrakkisathHardModeLogic.h (B15: General Drakkisath's hard mode, the General's Army): the slice, the
// herald's rule (against the instance's), the hard mode health x the flex ladder, the Muster's drill and timeline
// (SP DR12-DR16 squad table and the phase 1 total), the kit's phase gate, the phase 1 answer, the Champion's Call and
// Challenge (ring centre, blow timing and plan, Fire Blast spots inside the ring, Finesse, the win rule, Trophies),
// the squads' moves (command, shield front, the Shield Charge's knockback side) and the room's points.
#include "DrakkisathHardModeLogic.h"
#include "check.h"

#include <cmath>
#include <cstdint>
#include <random>
#include <set>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsGeneralsArmy;

namespace
{
    bool Near(double a, double b, double eps = 0.01)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, and never in B14's.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210560 && kSpellSlice.last == 210619);
        for (std::uint32_t id = kFirstSpell; id <= kLastSpell; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(!BrsDrakkisath::kSpellSlice.Contains(id));
        }
        CHECK(kFirstSpell == 210560 && kLastSpell == 210586);
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_GENERALS_ARMY));
        CHECK(!ArenaFor(BOSS_GENERALS_ARMY).Empty());
        // S0's creature ids (the squads first: their heroic copies are predicted in this order).
        CHECK(NPC_BRS_SQUAD_DRAGONSPAWN == 300736 && NPC_BRS_SQUAD_CAPTAIN == 300737);
        CHECK(NPC_BRS_SQUAD_FIRE_TONGUE == 300738 && NPC_BRS_SQUAD_DRAGON_GUARD == 300739);
        CHECK(NPC_BRS_HERALD == 300740 && NPC_BRS_CHALLENGE_RING == 300741);
        // Tags clear of B14's (1-6); the Challenge's cast id is a hard mode id, above his three wind-ups.
        CHECK(TAG_GA_CALL > 6);
        CHECK(CAST_GA_CHALLENGE >= BrsDrakkisath::kHardModeCastBase);
        CHECK(kChallengePriority > BrsDrakkisath::kSweepPriority);
        // Kit mirrors BrsDrakkisath::Ability (the .cpp asserts it too).
        CHECK(std::uint8_t(Kit::Melee) == 6 && std::uint8_t(Kit::Brands) == 0);
    }

    void TestHerald()
    {
        using DungeonKit::State::Done;
        using DungeonKit::State::InProgress;
        using DungeonKit::State::NotStarted;
        std::uint32_t const fail = DungeonKit::State::Fail;
        CHECK(HeraldRefusalFor(true, true, NotStarted, false) == HeraldRefusal::None);
        CHECK(HeraldRefusalFor(true, true, fail, false) == HeraldRefusal::None);           // again after a wipe
        CHECK(HeraldRefusalFor(false, true, NotStarted, false) == HeraldRefusal::NotHeroic);
        CHECK(HeraldRefusalFor(true, false, NotStarted, false) == HeraldRefusal::NotInsulted);
        CHECK(HeraldRefusalFor(true, true, InProgress, false) == HeraldRefusal::Fighting);
        CHECK(HeraldRefusalFor(true, true, Done, false) == HeraldRefusal::Dead);
        CHECK(HeraldRefusalFor(true, true, NotStarted, true) == HeraldRefusal::AlreadyArmed);
        // The herald's answer agrees with the instance's rule wherever it would arm.
        for (bool heroic : { false, true })
            for (bool insulted : { false, true })
                for (std::uint32_t state : { NotStarted, InProgress, fail, Done })
                {
                    bool const herald = HeraldRefusalFor(heroic, insulted, state, false) == HeraldRefusal::None;
                    CHECK(herald == GeneralsArmyChangeAllowed(1, heroic, true, insulted, state));
                }
        // Shown at the entrance only with the insult on heroic while he waits; at the alcove once armed (DR19: back
        // at the entrance when the attempt ends and the instance clears the flag).
        CHECK(HeraldPlaceFor(true, true, NotStarted, false) == HeraldPlace::Entrance);
        CHECK(HeraldPlaceFor(true, true, fail, false) == HeraldPlace::Entrance);
        CHECK(HeraldPlaceFor(true, true, NotStarted, true) == HeraldPlace::Alcove);
        CHECK(HeraldPlaceFor(true, false, NotStarted, false) == HeraldPlace::Hidden);
        CHECK(HeraldPlaceFor(false, true, NotStarted, false) == HeraldPlace::Hidden);
        CHECK(HeraldPlaceFor(true, true, InProgress, true) == HeraldPlace::Hidden);
        CHECK(HeraldPlaceFor(true, true, Done, false) == HeraldPlace::Hidden);
        CHECK(HeraldRefusalText(HeraldRefusal::None)[0] == '\0');
        CHECK(HeraldRefusalText(HeraldRefusal::Fighting)[0] != '\0');
        // S0's text range for the herald holds its line.
        CHECK(SAY_HERALD_ARMED == 0);
    }

    void TestHealth()
    {
        CHECK(DungeonKit::Flex::HealthAt(5, kBossHealthAt5) == 240000);
        CHECK(DungeonKit::Flex::HealthAt(10, kBossHealthAt5) == 540000);        // SP DR build spec
        CHECK(DungeonKit::Flex::HealthAt(10, kEliteGuardHealthAt5) == 67500);
        // The heroic base comes back exactly from a held max health.
        for (std::uint32_t n = 5; n <= 10; ++n)
            CHECK(BaseBeforeHardMode(DungeonKit::Flex::HealthAt(n, 310000), n) == 310000);
    }

    void TestMuster()
    {
        // SP's squad table (DR12-DR16).
        struct Row { SquadKind kind; std::uint32_t health; std::uint32_t soldiers; std::uint64_t at; };
        std::vector<Row> const sp{
            { SquadKind::Vanguard, 57000, 3, 0 },
            { SquadKind::FireLine, 47000, 3, 20000 },
            { SquadKind::ShieldWall, 63000, 3, 40000 },
            { SquadKind::Vanguard, 74000, 4, 60000 },
            { SquadKind::FireLine, 60000, 4, 80000 },
            { SquadKind::ShieldWall, 84000, 4, 135000 },
            { SquadKind::Vanguard, 91000, 5, 180000 },
        };
        std::uint32_t phase1 = 0;
        for (std::uint32_t i = 0; i < sp.size(); ++i)
        {
            SquadPlan const p = PlanSquad(i);
            CHECK(p.kind == sp[i].kind);
            CHECK(p.HealthAt5() == sp[i].health);
            CHECK(p.Soldiers() == sp[i].soldiers);
            CHECK(SquadArrivalMs(i) == sp[i].at);
            CHECK(SquadCallsChallenge(i) == (i >= 5));
            CHECK(PhaseAt(SquadArrivalMs(i)) == (i < 5 ? Phase::Muster : Phase::Field));
            if (i < 5)
                phase1 += p.HealthAt5();
        }
        CHECK(phase1 == 301000);    // SP: "squads 1 to 5, 301,000"
        // Vanguard 4 DS + Captain and Shield Wall 4 (phase 2 squads 6 and 7), and a capped later drill.
        CHECK(PlanSquad(6).dragonspawn == 4 && PlanSquad(6).captains == 1);
        CHECK(PlanSquad(7).fireTongues == 4 && PlanSquad(7).dragonGuards == 1);
        CHECK(PlanSquad(30).Soldiers() == PlanSquad(9).Soldiers());
        CHECK(PlanSquad(9).dragonspawn == 2 + kMaxSquadStep);
        // The gates alternate.
        CHECK(SquadGate(0) == 0 && SquadGate(1) == 1 && SquadGate(2) == 0);
        // Phase 2 at 1:30; the first field squad at 2:15.
        CHECK(PhaseAt(89999) == Phase::Muster && PhaseAt(90000) == Phase::Field);
        // A squad's soldiers stand side by side across the gate's axis, centred on it.
        Vec2 const a = SquadSpot(0, 0, 3);
        Vec2 const c = SquadSpot(0, 2, 3);
        CHECK(Near(a.x, kSquadSpawn[0].x) && Near((a.y + c.y) * 0.5, kSquadSpawn[0].y));
        CHECK(Near(std::fabs(c.y - a.y), 2.0 * kSquadSpreadYd));
        // The spawn spots sit on the lower floor behind the gates (x 38.8..65.2, z 104.8..109), out of the hall.
        for (Point3 const& s : kSquadSpawn)
        {
            CHECK(s.x > 45.2f && s.x < 65.2f && s.z > 104.8f && s.z < 109.f);
            CHECK(!InRoom(s.XY(), s.z));
        }
    }

    void TestGate()
    {
        // Phase 1: his brands and his blade only.
        for (std::uint8_t k = 0; k <= 6; ++k)
        {
            Kit const kit = static_cast<Kit>(k);
            CHECK(UsesKit(Phase::Muster, false, false, kit) == (kit == Kit::Brands || kit == Kit::Melee));
            CHECK(UsesKit(Phase::Field, false, false, kit));
        }
        // The Call: his wind-ups wait (the queue stays free for the Challenge), the rest runs.
        CHECK(!UsesKit(Phase::Field, true, false, Kit::BlackbladeSweep));
        CHECK(!UsesKit(Phase::Field, true, false, Kit::Thunderclap));
        CHECK(!UsesKit(Phase::Field, true, false, Kit::Flamestrike));
        CHECK(UsesKit(Phase::Field, true, false, Kit::Melee) && UsesKit(Phase::Field, true, false, Kit::Brands));
        CHECK(UsesKit(Phase::Field, true, false, Kit::SearedFlesh));
        // The Challenge: no brands.
        CHECK(!UsesKit(Phase::Field, false, true, Kit::Brands));
        CHECK(UsesKit(Phase::Field, false, true, Kit::SearedFlesh));
        // B14's note: Melee and Seared Flesh go off together (never Seared Flesh on with his blade off).
        for (Phase ph : { Phase::Muster, Phase::Field })
            for (bool calling : { false, true })
                for (bool challenging : { false, true })
                    CHECK(!UsesKit(ph, calling, challenging, Kit::SearedFlesh)
                        || UsesKit(ph, calling, challenging, Kit::Melee));
        // The phase 1 answer: beyond 10 yd, phase 1 only.
        CHECK(AnswersAttacker(Phase::Muster, 25.f));
        CHECK(!AnswersAttacker(Phase::Muster, 5.f));
        CHECK(!AnswersAttacker(Phase::Field, 25.f));
    }

    void TestChallenge()
    {
        // The ring: 12 s in all, armed after the push (1.5 s).
        CHECK(kRingArmMs + kRingLifeMs == kChallengeMs);
        CHECK(Near(kRingRadius, 12.f) && Near(kRingWidth, 2.f));
        CHECK(!kRingStrikesPets && !kRingSparesChallenger);
        // Its centre: on him for a challenger close in; shifted for one far out, both well inside the band.
        Vec2 const boss{ 10.f, -290.f };
        CHECK(Near(RingCentre(boss, { 18.f, -290.f }).x, 10.f));
        for (float d : { 0.f, 4.f, 8.f, 9.5f, 12.f, 14.f, 20.f })
        {
            Vec2 const ch{ boss.x + d, boss.y };
            Vec2 const c = RingCentre(boss, ch);
            float const inner = kRingRadius - kRingWidth * 0.5f;
            CHECK(DungeonKit::Distance(c, ch) <= kChallengerMaxFromCentreYd + 0.01f);
            CHECK(DungeonKit::Distance(c, boss) < inner);
        }
        // The Call's circle 8 yd ahead: a challenger anywhere in it ends up inside the ring.
        Vec2 const call = CallSpot(boss, 0.f);
        CHECK(Near(call.x, boss.x + kCallAheadYd) && Near(call.y, boss.y));
        CHECK(kCallAheadYd + kCallRadius <= kChallengerMaxFromCentreYd + kCallAheadYd);
        CHECK(kCallBotDelayMs < kCallMs);

        // Blows: six, 2 s apart, 1.5 s telegraphs, all judged before the ring ends.
        CHECK(BlowStartMs(0) == 0 && BlowLandMs(0) == 1500 && BlowLandMs(5) == 11500);
        for (std::uint32_t k = 0; k + 1 < kBlows; ++k)
            CHECK(BlowStartMs(k + 1) - BlowStartMs(k) == 2000);
        // Penalties: Weakened from the 40% and 30% blows, none from the 50% Overhead Cleave.
        CHECK(NumbersOf(Blow::OverheadCleave).pct == 50.f && !NumbersOf(Blow::OverheadCleave).weakened);
        for (Blow b : { Blow::Sweep, Blow::FireBlast, Blow::RingOfFlame, Blow::Thunderclap })
            CHECK(NumbersOf(b).weakened && NumbersOf(b).pct < 50.f);
        CHECK(NumbersOf(Blow::FireBlast).pct == 30.f && NumbersOf(Blow::Sweep).pct == 40.f);
        // The plan: the five kinds once each, then one of the first four (never the fifth twice running).
        std::mt19937 rng(7);
        auto rand = [&rng](std::uint32_t n) { return n ? std::uint32_t(rng() % n) : 0u; };
        for (int i = 0; i < 2000; ++i)
        {
            auto const plan = PlanBlows(rand);
            std::set<Blow> firstFive(plan.begin(), plan.begin() + kBlowKinds);
            CHECK(firstFive.size() == kBlowKinds);
            CHECK(plan[kBlows - 1] != plan[kBlowKinds - 1]);
            // R-2 ruling: never a Sweep right after a Thunderclap.
            for (std::size_t k = 0; k + 1 < kBlows; ++k)
                CHECK(BlowFollowsOk(plan[k], plan[k + 1]));
        }
        CHECK(!BlowFollowsOk(Blow::Thunderclap, Blow::Sweep) && BlowFollowsOk(Blow::Sweep, Blow::Thunderclap));
        // Every rand stream (each shuffle index, each sixth pick) keeps the rule: a fixed roll of every value.
        for (std::uint32_t roll = 0; roll < 5; ++roll)
        {
            auto fixed = [roll](std::uint32_t n) { return n ? roll % n : 0u; };
            auto const plan = PlanBlows(fixed);
            for (std::size_t k = 0; k + 1 < kBlows; ++k)
                CHECK(BlowFollowsOk(plan[k], plan[k + 1]));
        }
        // The Fire Blast circles: one on the challenger, the two beside it wholly inside the ring.
        std::uniform_real_distribution<float> angle(0.f, 2.f * kPi);
        std::uniform_real_distribution<float> radius(0.f, kChallengerMaxFromCentreYd);
        for (int i = 0; i < 2000; ++i)
        {
            Vec2 const centre{ 0.f, 0.f };
            float const r = radius(rng);
            float const a = angle(rng);
            Vec2 const ch{ r * std::cos(a), r * std::sin(a) };
            auto const spots = FireBlastSpots(ch, angle(rng), centre);
            CHECK(Near(spots[0].x, ch.x) && Near(spots[0].y, ch.y));
            for (std::size_t k = 1; k < spots.size(); ++k)     // the two beside the challenger stay in the ring
                CHECK(DungeonKit::Distance(centre, spots[k]) + kFireBlastRadius
                    <= kRingRadius - kRingWidth * 0.5f + 0.01f);
        }
        // The donut reaches the band; the clap stops short of it.
        CHECK(kRingOfFlameOuter <= kRingRadius && kThunderclapRadius < kRingRadius);

        // Win: 18,000 at every size; x the empowered multiplier.
        CHECK(WinDamage() == 18000 && WinDamage(1.5) == 27000 && WinDamage(0.) == 18000);
        // SP: 1,200 a second for 12 s is 14,400: Finesse makes the difference (2-3 early dodges).
        double base = 1200.0 * 12.0;
        CHECK(base < kWinDamage);
        double withFinesse = 0.0;
        for (std::uint32_t s = 0; s < 12; ++s)  // a dodge each blow from the first: stacks grow every 2 s
        {
            std::uint32_t const stacks = std::min<std::uint32_t>(s >= 1 ? (s + 1) / 2 : 0, kFinesseMax);
            withFinesse += 1200.0 * (1.0 + kFinessePctPerStack * stacks / 100.0);
        }
        CHECK(withFinesse >= kWinDamage);
        CHECK(kFinesseMs > kChallengeMs);
        // Outcomes.
        CHECK(JudgeChallenge(18000, 18000, true, false) == ChallengeEnd::Won);
        CHECK(JudgeChallenge(18000, 18000, false, true) == ChallengeEnd::Won);
        CHECK(JudgeChallenge(100, 18000, false, false) == ChallengeEnd::ChallengerDied);
        CHECK(JudgeChallenge(100, 18000, true, true) == ChallengeEnd::Lost);
        CHECK(!JudgeChallenge(100, 18000, true, false));
        CHECK(GivesTrophy(ChallengeEnd::Lost) && GivesTrophy(ChallengeEnd::ChallengerDied));
        CHECK(GivesTrophy(ChallengeEnd::Unanswered) && !GivesTrophy(ChallengeEnd::Won));
        CHECK(!GivesTrophy(ChallengeEnd::Aborted));
        // Trophies scale his blows: +10% each.
        CHECK(Near(TrophyScale(0), 1.0) && Near(TrophyScale(3), 1.3));
        // R-2: the Trophy raises his non-melee hits through OnDamageDealt (B14's kit and the blows); melee is the
        // aura's.
        CHECK(TrophyDamage(1000, 0, false) == 1000 && TrophyDamage(1000, 3, false) == 1300);
        CHECK(TrophyDamage(1000, 3, true) == 1000);
        // R-2 M-3: the challenger (active, else the Call's pick) is kept out of the squads; a 5 yd knock from the
        // clap's safe annulus (8-11 yd) would cross the ring's band, so the knock skips them.
        CHECK(DuelChallengerOf(true, 7, 9) == 7 && DuelChallengerOf(false, 7, 9) == 9);
        CHECK(DuelChallengerOf(false, 7, 0) == 0);
        CHECK(kThunderclapRadius + kShieldChargeKnockYd > kRingRadius - kRingWidth * 0.5f);
        CHECK(kHumbledPct == 30 && kHumbledMs == 10000);
    }

    void TestSquadMoves()
    {
        CHECK(Near(CommandScale(true), 1.25) && Near(CommandScale(false), 1.0));
        CHECK(kCommandAuraMs > kCommandRefreshMs);
        // Scattering Flame: 2 / 4 marks per Fire Tongue.
        CHECK(kScatteringTargets.At(5) == 2 && kScatteringTargets.At(6) == 4 && kScatteringTargets.At(10) == 4);
        CHECK(kVolleyKickPriority < BrsDrakkisath::kFlamestrikeKickPriority);
        // Shield front: half from the front 180 degrees, full from behind.
        float const facing = 0.f;
        CHECK(ShieldFrontDamage(1000, facing, 0.f) == 500);
        CHECK(ShieldFrontDamage(1000, facing, 1.5f) == 500);
        CHECK(ShieldFrontDamage(1000, facing, -1.5f) == 500);
        CHECK(ShieldFrontDamage(1000, facing, kPi) == 1000);
        CHECK(ShieldFrontDamage(1000, 2.f * kPi - 0.1f, 0.2f) == 500);     // wraps
        CHECK(ShieldFrontDamage(1000, facing, 1.7f) == 1000);
        // Shield Charge: the knockback pushes a player out of the lane to its own side; on the axis, to the left.
        Vec2 const start{ 0.f, 0.f };
        for (float side : { 1.f, -1.f })
        {
            Vec2 const p{ 10.f, 1.f * side };
            CHECK(LaneSide(start, 0.f, p) == int(side));
            Vec2 const src = KnockSource(start, 0.f, p);
            CHECK(Near(src.x, 10.f));
            CHECK((p.y - src.y) * side > 0.f);             // pushed away from the source: outward
        }
        Vec2 const onAxis = KnockSource(start, 0.f, { 10.f, 0.f });
        CHECK(onAxis.y < 0.f);                              // the source to the right: pushed left
        // Timers fit the drill: each move first comes before the next squad (20 s).
        CHECK(kCleavingChargeFirstMs < kMusterEveryMs && kScatteringFirstMs < kMusterEveryMs);
        CHECK(kShieldChargeFirstMs < kMusterEveryMs && kVolleyFirstMs < kMusterEveryMs);
        CHECK(kCleavingChargeEveryMs > kCleavingChargeCastMs && kShieldChargeEveryMs > kShieldChargeCastMs);
    }

    void TestRoom()
    {
        // The hold spots sit at the alcove's mouth, on the floor, one on each flank of him, in front of him.
        for (Point3 const& s : kGuardHoldSpots)
            CHECK(InRoom(s.XY(), s.z) && s.x < kDrakkisathSpawn.x - 5.f);
        CHECK(kGuardHoldSpots[0].y < kDrakkisathSpawn.y && kGuardHoldSpots[1].y > kDrakkisathSpawn.y);
        // The herald stands on the floor, well out of his reach (his blade, the Sweep's 10 yd); the alcove spot too.
        CHECK(InRoom(kHeraldEntrance.XY(), kHeraldEntrance.z));
        CHECK(DungeonKit::Distance(kHeraldEntrance.XY(), kDrakkisathSpawn.XY()) > 40.f);
        CHECK(InRoom(kHeraldAlcove.XY(), kHeraldAlcove.z));
        CHECK(DungeonKit::Distance(kHeraldAlcove.XY(), kDrakkisathSpawn.XY()) > 15.f);
        // His Call circle from his spot facing south (the hall) lands on the hall floor.
        Vec2 const call = CallSpot(kDrakkisathSpawn.XY(), kPi);
        CHECK(InRoom(call, kDrakkisathSpawn.z));
    }
}

int main()
{
    TestSlice();
    TestHerald();
    TestHealth();
    TestMuster();
    TestGate();
    TestChallenge();
    TestSquadMoves();
    TestRoom();
    return Report("brs_drakkisath_hard_mode_test");
}
