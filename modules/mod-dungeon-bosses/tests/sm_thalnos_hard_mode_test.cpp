// Host tests for ThalnosHardModeLogic.h (D4H: Bloodmage Thalnos's hard mode, the Desecration): the slice and the
// spells, the heroes and the kill order, the stones and the rite (by entry, the refusals against the instance's rule,
// the looks), the TH7 landing on the lawn, the rising order, Blood Pact's ward rule, the banner's boost, the charge's
// run, the heal and shield picks, the spin.
#include "DungeonKitWingLogic.h"
#include "ThalnosHardModeLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace ScarletMonasteryRework;
using namespace SmDesecration;
using DungeonKit::Distance;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float AngleDiff(float a, float b)
    {
        float d = std::fmod(std::fabs(a - b), DungeonKit::kTwoPi);
        return d > DungeonKit::kPi ? DungeonKit::kTwoPi - d : d;
    }

    // On the lawn the bots and the arena hold (D4's bounds: 30 yd; the arena 40 yd, z 15-26).
    bool InLawnBounds(Vec2 p)
    {
        return Distance(p, SmThalnos::kLawnCenter) <= SmThalnos::kLawnBoundsYd;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 212480 && kSpellSlice.last == 212539);
        std::uint32_t const ids[] = { SPELL_DS_HARD_MODE_AURA, SPELL_DS_NO_REST, SPELL_DS_BLOOD_PACT,
            SPELL_DS_PACT_TETHER, SPELL_DS_RISE, SPELL_DS_STONE_STIR, SPELL_DS_STONE_BLOOD, SPELL_DS_DISTURB_THE_GRAVE,
            SPELL_DS_RALLIED, SPELL_DS_CHARGE_LOOK, SPELL_DS_CHARGE_HIT, SPELL_DS_REPENT, SPELL_DS_GREATER_HEAL,
            SPELL_DS_POWER_WORD_SHIELD, SPELL_DS_WHIRLWIND_WINDUP, SPELL_DS_WHIRLWIND, SPELL_DS_WHIRLWIND_HIT };
        std::set<std::uint32_t> seen;
        std::uint32_t expect = 212480;
        for (std::uint32_t id : ids)
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(id == expect++);
            CHECK(seen.insert(id).second);
        }
        // Never one of D4's.
        for (std::uint32_t id : ids)
            CHECK(!kSpellsThalnos.Contains(id));
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_DESECRATION));
        CHECK(!ArenaFor(BOSS_DESECRATION).Empty());
        CHECK(HardModeFlagData(BOSS_DESECRATION) == DATA_HARD_MODE_THALNOS);
        // Tags apart from D4's (2-4).
        for (std::uint32_t mine : { std::uint32_t(RH1), std::uint32_t(RH2), std::uint32_t(RH6) })
            for (std::uint32_t d4 : { std::uint32_t(SmThalnos::TH2), std::uint32_t(SmThalnos::TH3),
                std::uint32_t(SmThalnos::TH4) })
                CHECK(mine != d4);
        CHECK(RH2 != RH1 && RH6 != RH1 && RH6 != RH2);
    }

    void TestHeroes()
    {
        CHECK(EntryOf(Hero::Galvar) == 300903);
        CHECK(EntryOf(Hero::Fairbell) == 300904);
        CHECK(EntryOf(Hero::Voss) == 300905);
        CHECK(EntryOf(Hero::Goodchilde) == 300906);
        for (Hero h : kHeroes)
        {
            CHECK(HeroOfEntry(EntryOf(h)) == h);
            CHECK(std::string_view(NameOf(h)) != "?");
        }
        CHECK(!HeroOfEntry(NPC_SM_RALLYING_BANNER));
        CHECK(!HeroOfEntry(NPC_THALNOS));
        CHECK(!HeroOfEntry(NPC_HAUNTING_PHANTASM));
        // The kill order: Voss, Fairbell, Galvar, Goodchilde, then Thalnos (0).
        CHECK(KillPriority(Hero::Voss) > KillPriority(Hero::Fairbell));
        CHECK(KillPriority(Hero::Fairbell) > KillPriority(Hero::Galvar));
        CHECK(KillPriority(Hero::Galvar) > KillPriority(Hero::Goodchilde));
        CHECK(KillPriority(Hero::Goodchilde) > 0);
        // The stones' answer is the rising order and the instance's DATA_DESECRATION_TOUCH 0-3.
        for (std::size_t i = 0; i < kHeroCount; ++i)
            CHECK(IndexOf(kHeroes[i]) == i);
        CHECK(kHeroCount == kDesecrationStones);
    }

    void TestStones()
    {
        // By entry, never by spot (RB-3).
        CHECK(HeroOfStone(GO_SM_GRAVESTONE_GALVAR) == Hero::Galvar);
        CHECK(HeroOfStone(GO_SM_GRAVESTONE_FAIRBELL) == Hero::Fairbell);
        CHECK(HeroOfStone(GO_SM_GRAVESTONE_VOSS) == Hero::Voss);
        CHECK(HeroOfStone(GO_SM_GRAVESTONE_GOODCHILDE) == Hero::Goodchilde);
        CHECK(!HeroOfStone(GO_SM_BLOOD_RITE));
        CHECK(!HeroOfStone(0));
        // The epitaphs and the rite: npc_text ids = the objects' entries.
        for (Hero h : kHeroes)
            CHECK(EpitaphTextId(h) == 301310 + IndexOf(h));
        CHECK(kRiteTextId == 301314);

        // Section 7 #18 A: the disc (1796.5, 1369.5) r 16.1, NAVMESH's spots 11.4 yd apart, on the lawn.
        for (std::size_t i = 0; i < kHeroCount; ++i)
        {
            Vec2 const s = kStoneSpots[i].XY();
            CHECK(Distance(s, kStoneDisc) <= 16.1f);
            CHECK(Distance(s, kStoneDisc) > 6.f);
            CHECK(InLawnBounds(s));
            CHECK(ArenaFor(BOSS_DESECRATION).Contains(s, kStoneSpots[i].z));
            for (std::size_t j = i + 1; j < kHeroCount; ++j)
                CHECK(Distance(s, kStoneSpots[j].XY()) >= 11.f);
            // Each faces the disc's center.
            CHECK(AngleDiff(StoneFacing(kHeroes[i]), DungeonKit::BearingTo(s, kStoneDisc)) < 0.001f);
        }
        // The rite in the z 0 court, 30-40 yd from his spawn (the court: 37 yd of path), far from the stones.
        CHECK(Near(kRiteSpot.x, 1788.5f) && Near(kRiteSpot.y, 1417.f) && kRiteSpot.z < 2.f);
        CHECK(Distance(kRiteSpot.XY(), kStoneDisc) > 40.f);

        // The refusals agree with the instance's rule (the gossip never offers a touch it refuses).
        std::uint32_t const states[] = { DungeonKit::State::NotStarted, DungeonKit::State::InProgress,
            DungeonKit::State::Fail, DungeonKit::State::Done, DungeonKit::State::Special };
        for (bool heroic : { false, true })
            for (std::uint32_t thalnos : states)
                for (std::uint32_t council : states)
                    for (bool lit : { false, true })
                        CHECK((RefusalFor(heroic, thalnos, council, lit) == StoneRefusal::None)
                            == DesecrationTouchAllowed(heroic, thalnos, council, lit));
        // The reasons.
        CHECK(RefusalFor(false, 0, DungeonKit::State::Done, false) == StoneRefusal::NotHeroic);
        CHECK(RefusalFor(true, 0, DungeonKit::State::Done, true) == StoneRefusal::Lit);
        CHECK(RefusalFor(true, 0, DungeonKit::State::NotStarted, false) == StoneRefusal::CouncilAlive);
        CHECK(RefusalFor(true, 0, DungeonKit::State::InProgress, false) == StoneRefusal::CouncilAlive);
        CHECK(RefusalFor(true, DungeonKit::State::InProgress, DungeonKit::State::Done, false)
            == StoneRefusal::ThalnosFighting);
        CHECK(RefusalFor(true, DungeonKit::State::Done, DungeonKit::State::Done, false) == StoneRefusal::ThalnosDead);
        CHECK(RefusalFor(true, DungeonKit::State::Fail, DungeonKit::State::Done, false) == StoneRefusal::None);
        CHECK(std::string_view(RefusalText(StoneRefusal::CouncilAlive)) == "The dead are not yet at rest.");
        CHECK(std::string_view(RefusalText(StoneRefusal::None)).empty());
        for (StoneRefusal r : { StoneRefusal::NotHeroic, StoneRefusal::Lit, StoneRefusal::ThalnosFighting,
            StoneRefusal::ThalnosDead })
            CHECK(!std::string_view(RefusalText(r)).empty());

        // The looks: red once answered; a faint stir only while this attempt counts touches; dark after a judge.
        CHECK(LookFor(true, false, 0) == StoneLook::Blood);
        CHECK(LookFor(true, true, 3) == StoneLook::Blood);
        CHECK(LookFor(false, true, 2) == StoneLook::Stir);
        CHECK(LookFor(false, true, 0) == StoneLook::None);
        CHECK(LookFor(false, false, 3) == StoneLook::None);

        // The judge (the instance's pure rule): only Galvar, Fairbell, Voss, Goodchilde is right.
        CHECK(JudgeDesecration({ 0, 1, 2, 3 }) == DesecrationVerdict::Right);
        CHECK(JudgeDesecration({ 3, 2, 1, 0 }) == DesecrationVerdict::Wrong);
        CHECK(JudgeDesecration({ 1, 0, 2, 3 }) == DesecrationVerdict::Wrong);

        // The Phantasms of a wrong answer rise on the disc, apart, on the lawn.
        for (std::uint32_t i = 0; i < kPhantasmCount; ++i)
        {
            Vec2 const p = PhantasmSpot(i);
            CHECK(Near(Distance(p, kStoneDisc), kPhantasmRingYd, 0.01f));
            CHECK(InLawnBounds(p));
            for (std::uint32_t j = i + 1; j < kPhantasmCount; ++j)
                CHECK(Distance(p, PhantasmSpot(j)) > 5.f);
        }
        CHECK(kPhantasmCount == 3);
        CHECK(kDisturbCastMs == 2000);
    }

    void TestLanding()
    {
        // His landing is the council's disc (section 7 #18 A), facing away from the stones.
        CHECK(Near(kLawnLanding.x, 1798.5f) && Near(kLawnLanding.y, 1348.5f));
        float const facing = ThalnosLandingFacing();
        CHECK(AngleDiff(facing, DungeonKit::BearingTo(kLawnLanding, kStoneDisc)) > 3.f);
        for (std::uint32_t count = 1; count <= 10; ++count)
        {
            for (std::uint32_t i = 0; i < count; ++i)
            {
                Point4 const p = PlayerLanding(i, count);
                Vec2 const xy = p.XY();
                CHECK(Near(Distance(xy, kLawnLanding), kLandingRingYd, 0.01f));
                // On the clear disc (r 19.1), in the bots' bounds and the arena, clear of every stone.
                CHECK(Distance(xy, kLawnLanding) < 19.1f);
                CHECK(InLawnBounds(xy));
                CHECK(ArenaFor(BOSS_DESECRATION).Contains(xy, p.z));
                for (Point3 const& s : kStoneSpots)
                    CHECK(Distance(xy, s.XY()) > 5.f);
                // Facing him.
                CHECK(AngleDiff(p.o, DungeonKit::BearingTo(xy, kLawnLanding)) < 0.01f);
                CHECK(p.o >= 0.f && p.o < DungeonKit::kTwoPi);
                for (std::uint32_t j = i + 1; j < count; ++j)
                    CHECK(Distance(xy, PlayerLanding(j, count).XY()) >= 3.f);
            }
            // The arc is centered on his facing (in front of him).
            float sx = 0.f;
            float sy = 0.f;
            for (std::uint32_t i = 0; i < count; ++i)
            {
                sx += PlayerLanding(i, count).x - kLawnLanding.x;
                sy += PlayerLanding(i, count).y - kLawnLanding.y;
            }
            CHECK(AngleDiff(std::atan2(sy, sx), facing) < 0.01f);
        }
        // The gather reaches the crypt, its stair and the court from his spawn (the rite is in the court), never the
        // lawn (the council's disc is 76 yd away).
        auto dist3 = [](Point3 a, Point3 b)
        {
            return std::sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y) + (a.z - b.z) * (a.z - b.z));
        };
        CHECK(dist3(kThalnosSpawn, kRiteSpot.P3()) < kTeleportGatherYd);
        CHECK(dist3(kThalnosSpawn, kCouncilLawn) > kTeleportGatherYd);
        CHECK(kNoRestCastMs == 3000);
        CHECK(SmThalnos::kNoRestPct == 75.f);
    }

    void TestRising()
    {
        // Each rises at its own stone, in front of it toward the landing, on the lawn.
        for (Hero h : kHeroes)
        {
            Point4 const r = RiseSpot(h);
            Point3 const& s = kStoneSpots[IndexOf(h)];
            CHECK(Near(Distance(r.XY(), s.XY()), kRiseInYd, 0.01f));
            CHECK(Distance(r.XY(), kLawnLanding) < Distance(s.XY(), kLawnLanding));
            CHECK(InLawnBounds(r.XY()));
            CHECK(ArenaFor(BOSS_DESECRATION).Contains(r.XY(), r.z));
        }

        AliveMask none{};
        AliveMask all{ true, true, true, true };
        RiseClock clock;
        CHECK(!clock.Due(0, none));         // not started
        auto const first = clock.Start(1000);
        CHECK(first[0] == Hero::Galvar && first[1] == Hero::Fairbell);
        AliveMask alive{ true, true, false, false };
        CHECK(!clock.Due(20999, alive));
        CHECK(clock.Due(21000, alive) == Hero::Voss);       // Voss 20 s later
        alive[IndexOf(Hero::Voss)] = true;
        CHECK(!clock.Due(21000, alive));
        CHECK(clock.Due(41000, alive) == Hero::Goodchilde); // Goodchilde 20 s after that
        alive[IndexOf(Hero::Goodchilde)] = true;
        // Then every 20 s the first dead one; nobody while all four stand (at most four).
        CHECK(!clock.Due(61000, all));
        alive = { true, false, false, true };               // Fairbell and Voss dead: Fairbell first
        CHECK(clock.Due(81000, alive) == Hero::Fairbell);
        alive[IndexOf(Hero::Fairbell)] = true;
        CHECK(clock.Due(101000, alive) == Hero::Voss);
        alive = { false, true, true, true };
        CHECK(clock.Due(121000, alive) == Hero::Galvar);
        // A late tick does not burst: one rise, the next 20 s on.
        alive = { false, false, false, false };
        CHECK(clock.Due(500000, alive) == Hero::Galvar);
        CHECK(!clock.Due(500001, alive));
        CHECK(clock.DueMs() == 520000);
        clock.Stop();
        CHECK(!clock.Due(600000, alive));

        // Step 1 with Voss already standing (a GM rise): the first dead one instead.
        RiseClock c2;
        c2.Start(0);
        CHECK(c2.Due(20000, AliveMask{ false, true, true, false }) == Hero::Galvar);
        CHECK(RiseClock::FirstDead(all) == std::nullopt);
        CHECK(RiseClock::FirstDead(AliveMask{ true, true, true, false }) == Hero::Goodchilde);

        // The yard's length at the spec's group damage: two at the landing, one each 20 s, about 7 over 109 s.
        RiseClock c3;
        c3.Start(0);
        std::uint32_t risen = 2;
        AliveMask dead{};
        for (std::uint64_t t = 1000; t <= 109000; t += 1000)
            if (c3.Due(t, dead))
                ++risen;
        CHECK(risen == 7);
    }

    void TestPact()
    {
        DungeonKit::WardRule const rule{ kPactPctPerRisen, kPactCapPct };
        CHECK(Near(rule.ReductionPct(0), 0.f));
        CHECK(Near(rule.ReductionPct(1), 20.f));
        CHECK(Near(rule.ReductionPct(2), 40.f));
        CHECK(Near(rule.ReductionPct(4), 80.f));
        CHECK(Near(rule.ReductionPct(5), 80.f));
        CHECK(rule.Stacks(4) == 4 && rule.Stacks(9) == 4);
        CHECK(rule.Scale(1000, 0) == 1000);
        CHECK(rule.Scale(1000, 2) == 600);      // two thirds longer on him
        CHECK(rule.Scale(1000, 4) == 200);      // five times as long
        CHECK(rule.Scale(1, 4) >= 1);
    }

    void TestBanner()
    {
        CHECK(Near(Rallied(30.f, false), 30.f));
        CHECK(Near(Rallied(30.f, true), 37.5f));
        CHECK(RalliedDamage(1000) == 1250);
        CHECK(RalliedDamage(0) == 0);
        // No double boost: the hard mode's own hits are boosted at the registration, the hook skips them.
        for (std::uint32_t id = kSpellSlice.first; id <= kSpellSlice.last; ++id)
            CHECK(!HookBoosts(id));
        CHECK(HookBoosts(SmThalnos::SPELL_TH_BLOOD_LANCE_LINE));
        CHECK(HookBoosts(SmThalnos::SPELL_TH_BLOOD_BOLT));
        CHECK(kBannerRadius == 10.f && kBannerMs == 30000 && kBannerWarnMs == 3000);
        CHECK(kRalliedMs > kRallyRefreshMs);
        // Space math (GY): at most two banners up at once (25 s cadence, 30 s life), 630 sq yd of the yard.
        CHECK(kBannerMs / kBannerBeat.everyMs + 1 == 2);
    }

    void TestCharge()
    {
        CHECK(ChargeStartMs(0.f) == kChargeWarnMs - kChargeLandEarlyMs);
        // 42 yd/s: 30 yd takes ~714 ms, he starts ~1136 ms after the marker.
        std::uint32_t const at30 = ChargeStartMs(30.f);
        CHECK(at30 > 1100 && at30 < 1160);
        CHECK(ChargeStartMs(200.f) == 0);
        // He always lands before the resolve.
        for (float d : { 0.f, 5.f, 20.f, 40.f, 60.f })
        {
            float const land = static_cast<float>(ChargeStartMs(d)) + d / kChargeSpeed * 1000.f;
            CHECK(land <= static_cast<float>(kChargeWarnMs) || ChargeStartMs(d) == 0);
        }
        CHECK(kChargeRadius == 5.f && kChargePct == 30.f);
    }

    void TestVoss()
    {
        CHECK(HealAmount(360000) == 36000);
        CHECK(HealAmount(20000) == 2000);
        CHECK(HealAmount(0) == 1);
        std::array<Ally, kMaxAllies> allies{};
        allies[0] = { 1, 70.f, false };     // Thalnos
        allies[1] = { 2, 40.f, true };      // a risen, shielded
        allies[2] = { 3, 55.f, false };
        CHECK(MostWounded(allies, 3) == std::size_t(1));
        CHECK(MostWounded(allies, 3, true) == std::size_t(2));
        CHECK(MostWounded(allies, 0) == std::nullopt);
        // Ties go to the first given (Thalnos).
        allies[1] = { 2, 70.f, false };
        CHECK(MostWounded(allies, 2) == std::size_t(0));
        // Everyone shielded: no shield.
        for (std::size_t i = 0; i < 3; ++i)
            allies[i].shielded = true;
        CHECK(MostWounded(allies, 3, true) == std::nullopt);
        CHECK(kHealCastMs == 3000 && kRepentCastMs == 2000 && kRepentMs == 2000);
    }

    void TestWhirlwind()
    {
        CHECK(kWhirlwindHoldMs == kWhirlwindWindupMs + kWhirlwindSpinMs);
        // Staying in for the whole spin: four 30% ticks, 120%: lethal by design (hub ruling 54).
        CHECK(Near(static_cast<float>(kWhirlwindSpinMs / kWhirlwindTickMs) * kWhirlwindPct, 120.f));
        CHECK(kWhirlwindRadius == 8.f);
        CHECK(!kRisenMeleeFeedsRitual);
    }

    void TestNumbers()
    {
        CHECK(kThalnosHardModeHealth == 360000);
        CHECK(kRisenHealth == 20000);
        CHECK(kBannerBeat.firstMs == 5000 && kBannerBeat.everyMs == 25000);
        CHECK(kChargeBeat.firstMs == 8000 && kChargeBeat.everyMs == 15000);
        CHECK(kRepentBeat.firstMs == 6000 && kRepentBeat.everyMs == 12000);
        CHECK(kHealBeat.firstMs == 4000 && kHealBeat.everyMs == 12000);
        CHECK(kShieldBeat.firstMs == 10000 && kShieldBeat.everyMs == 20000);
        CHECK(kWhirlwindBeat.firstMs == 6000 && kWhirlwindBeat.everyMs == 20000);
        CHECK(kRiseEveryMs == 20000);
        CHECK(kRisenLeashYd > SmThalnos::kLawnArenaYd);
        // RF-1 m-4: a risen chased past the lawn's cut toward Ironspine walks back; the bots' bounds never trip it.
        CHECK(kRisenLeashSouthY < SmThalnos::kLawnSouthCutY);
        CHECK(!RisenOffLawn(SmThalnos::kLawnCenter));
        CHECK(!RisenOffLawn({ SmThalnos::kLawnCenter.x, SmThalnos::kLawnCenter.y - SmThalnos::kLawnBoundsYd }));
        CHECK(!RisenOffLawn({ SmThalnos::kLawnCenter.x, SmThalnos::kLawnSouthCutY - 4.f }));
        CHECK(RisenOffLawn({ SmThalnos::kLawnCenter.x, kRisenLeashSouthY - 1.f }));
        CHECK(RisenOffLawn({ SmThalnos::kLawnCenter.x + kRisenLeashYd + 1.f, SmThalnos::kLawnCenter.y }));
        CHECK(RisenOffLawn(kIronspineHome.XY()));
    }
}

int main()
{
    TestSlice();
    TestHeroes();
    TestStones();
    TestLanding();
    TestRising();
    TestPact();
    TestBanner();
    TestCharge();
    TestVoss();
    TestWhirlwind();
    TestNumbers();
    return Report("sm_thalnos_hard_mode_test");
}
