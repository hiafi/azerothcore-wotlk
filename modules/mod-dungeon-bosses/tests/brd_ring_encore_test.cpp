// Host tests for RingEncoreLogic.h (D6: the Ring of Law's hard mode, the Encore).
#include "RingEncoreLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string_view>

using namespace BlackrockDepthsRework;
using namespace BrdEncore;
using DungeonKit::BodyState;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210960 && kSpellSlice.last == 211019);
        CHECK(SPELL_TH_CHARGE_BAR == 210960);
        CHECK(SPELL_KO_CHAIN_HEAL == 210969);
        CHECK(SPELL_LE_SHADOWSTEP_LOOK == 210978);
        CHECK(SPELL_VL_BLIZZARD == 210983);
        CHECK(SPELL_MA_PIERCING_SHOT_CAST == 210991);
        CHECK(SPELL_EN_BANNER_BURN == 210999);
        CHECK(kLastSpell == 210999);
        CHECK(kLastSpell <= kSpellSlice.last);
        // Never the champions' or the Ring's ids.
        CHECK(kSpellSlice.first > kSpellsRingChampions.last);
        // The hard mode's kill slot is its own and fights in the Ring's arena.
        CHECK(IsHardModeSlot(BOSS_ENCORE));
        CHECK(!ArenaFor(BOSS_ENCORE).Empty());
        // Tags never collide with the Ring (11-17), the champions (18-28) or G1's rows (6-10).
        std::set<std::uint32_t> const tags{ TAG_TH_ROAR, TAG_VL_BLIZZARD, TAG_VL_FROST_NOVA, TAG_MA_PIERCING_SHOT,
            TAG_MA_SNAP_TRAP, TAG_MA_MULTI_SHOT };
        CHECK(tags.size() == 6);
        for (std::uint32_t t : tags)
            CHECK(t > 28);
        // Theldren's lines: 0 stock (the leap), 1 new (his death); the header's text range says 0-1.
        CHECK(SAY_TH_LEAP == 0 && SAY_TH_DEATH == 1);
    }

    void TestTeam()
    {
        CHECK(kTeamEntries[0] == 16059 && kTeamEntries[1] == 16053 && kTeamEntries[2] == 16049);
        CHECK(kTeamEntries[3] == 16058 && kTeamEntries[4] == 16052);
        for (std::size_t i = 0; i < kTeamSize; ++i)
        {
            Member const m = static_cast<Member>(i);
            CHECK(MemberOf(EntryOf(m)) == m);
            CHECK(std::string_view(MemberKey(m)) != "?");
        }
        CHECK(!MemberOf(16050).has_value());     // the unused stock members
        CHECK(!MemberOf(16051).has_value());
        CHECK(!MemberOf(16054).has_value());
        CHECK(!MemberOf(16055).has_value());
        // Ruling 30: 160k / 80k / 100k x3 = 540k.
        CHECK(HealthOf(Member::Theldren) == 160000);
        CHECK(HealthOf(Member::Korv) == 80000);
        CHECK(HealthOf(Member::Lefty) == 100000 && HealthOf(Member::Volida) == 100000);
        CHECK(HealthOf(Member::Malgen) == 100000);
        CHECK(TeamHealth() == 540000);
        // Korv is never held (nobody brings him back); the others once.
        CHECK(HoldsOf(Member::Korv) == 0);
        CHECK(HoldsOf(Member::Theldren) == 1 && HoldsOf(Member::Malgen) == 1);
        CHECK(Near(kRevivePct, 50.f));
        // The totems.
        CHECK(kTotemEntries[0] == 300789 && kTotemEntries[1] == 300790 && kTotemEntries[2] == 300791);
        CHECK(TotemOf(300790) == TotemKind::Searing);
        CHECK(!TotemOf(300792).has_value());
        CHECK(kTotemLifeMs[0] == 0 && kTotemLifeMs[1] == 20000 && kTotemLifeMs[2] == 20000);
        CHECK(kTotemEveryMs[0] == 25000 && kTotemEveryMs[1] == 20000 && kTotemEveryMs[2] == 25000);
        CHECK(kTotemHealth == 1);
        // The corpses outlast the stock Arena Spoils chest (300 s).
        CHECK(kCorpseMs > BrdRingOfLaw::kArenaSpoilsDespawnSec * 1000);
    }

    void TestLeap()
    {
        Vec2 const center = kRingCenter.XY();
        std::set<std::pair<int, int>> spots;
        for (std::size_t i = 0; i < kTeamSize; ++i)
        {
            Point3 const g = kGallery[i];
            // On the gallery: 17-20 yd above the floor, beyond the floor's wall, over the east side.
            CHECK(g.z > -40.f && g.z < -33.f);
            CHECK(!BrdRingOfLaw::OnFloorPlane(g.XY()));
            float const d = DungeonKit::Distance(center, g.XY());
            CHECK(d > 45.f && d < 60.f);
            Vec2 const land = LandingOf(i);
            CHECK(Near(DungeonKit::Distance(center, land), kLandingRadius, 0.05f));
            CHECK(BrdRingOfLaw::WellInside(land, 2.f));
            spots.insert({ int(land.x * 10.f), int(land.y * 10.f) });
            // The leap is a long jump down, not a teleport.
            CHECK(DungeonKit::Distance(g.XY(), land) > 15.f);
        }
        CHECK(spots.size() == kTeamSize);
    }

    void TestTheldren()
    {
        CHECK(kChargeEveryMs == 12000 && kChargeWarnMs == 1500);
        CHECK(Near(kChargePct, 25.f) && Near(kExecutePct, 40.f));
        CHECK(ExecuteFollows(29.f) && !ExecuteFollows(30.f) && !ExecuteFollows(80.f));
        CHECK(kRoarEveryMs == 18000 && kRoarPrideEveryMs == 12000 && kRoarWarnMs == 2500);
        CHECK(RoarEveryMs(false) == 18000 && RoarEveryMs(true) == 12000);
        CHECK(Near(kRoarRadius, 8.f) && Near(kRoarPct, 35.f) && kRoarFearMs == 2000);
        CHECK(PrideActive(29.9f) && !PrideActive(30.f));
        CHECK(kPrideHastePct == 25);
        CHECK(FirstOf(12000) == 6000);
        // EN2: the lowest health, the tank too; ties to the nearer.
        std::vector<Candidate> c{ { 1, 80.f, 5.f }, { 2, 35.f, 20.f }, { 3, 35.f, 10.f }, { 4, 90.f, 1.f } };
        CHECK(LowestHealth(c) == std::optional<std::size_t>(2));
        CHECK(!LowestHealth({}).has_value());
    }

    void TestKorv()
    {
        CHECK(kChainHealEveryMs == 8000 && kChainHealCastMs == 2000 && kChainHealTargets == 3);
        CHECK(Near(kChainHealPct, 12.f));
        CHECK(kSpiritCastMs == 5000);
        CHECK(kEarthShieldEveryMs == 30000 && kEarthShieldCharges == 6 && Near(kEarthShieldPct, 2.f));
        CHECK(Near(kHealingStreamPct, 2.f) && Near(kSearingPct, 3.f) && kEarthbindSlowPct == 50);
        CHECK(Near(kHealingStreamRangeYd, 20.f) && Near(kSearingRangeYd, 20.f) && Near(kEarthbindRangeYd, 10.f));
        // EN4: the three lowest standing teammates, never a body, never one at full health or out of range.
        std::vector<Mate> m{
            { 1, 40.f, false, false, 5.f },
            { 2, 10.f, true, false, 5.f },      // a body
            { 3, 70.f, false, false, 5.f },
            { 4, 100.f, false, false, 5.f },    // full
            { 5, 55.f, false, false, 5.f },
            { 6, 20.f, false, false, 60.f },    // out of range
            { 7, 90.f, false, false, 5.f },
        };
        std::vector<std::size_t> const picks = ChainHealPicks(m);
        CHECK(picks.size() == 3);
        CHECK(picks[0] == 0 && picks[1] == 4 && picks[2] == 2);
        CHECK(ChainHealPicks({ { 1, 100.f, false, false, 1.f } }).empty());
        // EN5: a body never brought back, the nearest.
        std::vector<Mate> b{
            { 1, 1.f, true, true, 2.f },        // revived once already
            { 2, 1.f, true, false, 12.f },
            { 3, 1.f, true, false, 8.f },
            { 4, 50.f, false, false, 1.f },
        };
        CHECK(SpiritPick(b) == std::optional<std::size_t>(2));
        CHECK(!SpiritPick({ { 1, 1.f, true, true, 1.f } }).has_value());
    }

    void TestLefty()
    {
        CHECK(kShadowstepEveryMs == 15000 && kKidneyShotMs == 2000);
        CHECK(NextWound(0) == 1 && NextWound(4) == 5 && NextWound(5) == 5);
        CHECK(Near(WoundTickPct(3), 3.f) && Near(WoundTickPct(5), 5.f));
        CHECK(WoundEnds(90.5f) && !WoundEnds(90.f) && !WoundEnds(40.f));
        CHECK(EvasionsDue(80.f, 0) == 0);
        CHECK(EvasionsDue(50.f, 0) == 1);
        CHECK(EvasionsDue(40.f, 1) == 0);
        CHECK(EvasionsDue(25.f, 1) == 1);
        CHECK(EvasionsDue(10.f, 0) == 2);       // a burst through both thresholds
        CHECK(EvasionsDue(10.f, 2) == 0);
        CHECK(kEvasionMs == 8000);
    }

    void TestVolida()
    {
        CHECK(kBlizzardEveryMs == 12000 && kBlizzardWarnMs == 2000 && kBlizzardMs == 6000);
        CHECK(Near(kBlizzardRadius, 8.f) && Near(kBlizzardPct, 4.f));
        CHECK(kNovaCastMs == 1500 && Near(kNovaRadius, 10.f) && Near(kNovaPct, 20.f) && kNovaRootMs == 2000);
        CHECK(!NovaWanted(1) && NovaWanted(2) && NovaWanted(5));
        CHECK(kIceBarrierEveryMs == 30000 && Near(kIceBarrierPct, 10.f));
        CHECK(Near(kBlinkYd, 15.f));
    }

    void TestMalgen()
    {
        CHECK(kPiercingEveryMs == 15000 && kPiercingCastMs == 3000 && Near(kPiercingWidth, 3.f));
        CHECK(Near(kPiercingPct, 40.f));
        CHECK(kTrapMeleeMs == 3000 && Near(kTrapRadius, 3.f) && kTrapLifeMs == 60000 && kTrapCap == 3);
        CHECK(Near(kTrapPct, 20.f) && kTrapFreezeMs == 2000 && Near(kDisengageYd, 15.f));
        CHECK(kMultiShotEveryMs == 10000 && kMultiShotWarnMs == 2000 && Near(kMultiShotLength, 30.f));
        CHECK(Near(kMultiShotPct, 25.f));
        // The melee clock and the trap's gap.
        CHECK(MeleeClock(0, 1000, true) == 1000);
        CHECK(MeleeClock(2500, 1000, true) == 3500);
        CHECK(MeleeClock(2500, 1000, false) == 0);
        CHECK(!TrapDue(2999, 10000, 0));
        CHECK(TrapDue(3000, 10000, 0));
        CHECK(!TrapDue(3000, 10000, 5000));
        CHECK(TrapDue(3000, 11000, 5000));
    }

    void TestFloorSteps()
    {
        Vec2 const center = kRingCenter.XY();
        // From the center every bearing has room for 15 yd.
        for (int i = 0; i < 8; ++i)
        {
            std::optional<Vec2> const to = FloorStep(center, float(i) * DungeonKit::kPi / 4.f, 15.f);
            CHECK(to.has_value());
            if (to)
                CHECK(BrdRingOfLaw::WellInside(*to, 2.f));
        }
        // Next to the east wall, a step outward turns along it (or is refused), never off the floor.
        Vec2 const nearWall = DungeonKit::Advance(center, 0.f, 30.f);
        if (std::optional<Vec2> const to = FloorStep(nearWall, 0.f, 15.f))
            CHECK(BrdRingOfLaw::WellInside(*to, 2.f));
        // Away from a threat: the step grows the distance when it goes straight.
        Vec2 const threat{ center.x - 3.f, center.y };
        std::optional<Vec2> const away = AwayFrom(center, threat, kBlinkYd);
        CHECK(away.has_value());
        if (away)
            CHECK(DungeonKit::Distance(*away, threat) > 15.f);
    }

    void TestVerdict()
    {
        using T = std::array<BodyState, kTeamSize>;
        BodyState const U = BodyState::Up;
        BodyState const F = BodyState::Fallen;
        BodyState const D = BodyState::Dead;
        CHECK(Judge(T{ U, U, U, U, U }) == Verdict::Fight);
        CHECK(Judge(T{ F, U, U, U, U }) == Verdict::Fight);           // Korv can bring Theldren back
        CHECK(Judge(T{ F, D, U, U, U }) == Verdict::FinishBodies);    // Korv dead: nobody can
        CHECK(Judge(T{ U, D, D, U, U }) == Verdict::Fight);           // no body lying
        CHECK(Judge(T{ F, U, F, F, F }) == Verdict::Fight);           // Korv stands
        CHECK(Judge(T{ F, D, F, F, F }) == Verdict::FinishBodies);    // every member down
        CHECK(Judge(T{ D, D, D, D, D }) == Verdict::Won);
        CHECK(Judge(T{ D, D, D, D, F }) == Verdict::FinishBodies);
        // Theldren is finished last; every member once.
        CHECK(kFinishOrder.back() == Member::Theldren);
        std::set<Member> const once(kFinishOrder.begin(), kFinishOrder.end());
        CHECK(once.size() == kTeamSize);
    }

    void TestBanner()
    {
        // The stock banner's spot, on the floor.
        CHECK(BrdRingOfLaw::WellInside(kBannerSpot.XY(), 2.f));
        CHECK(kBannerBackstopSec >= 3600);
        CHECK(GO_BRD_ENCORE_BANNER == 301280);
        CHECK(kGameObjectsReservation.Contains(GO_BRD_ENCORE_BANNER));
        // The flags' gates (the instance's): heroic only, burned needs thrown, never once the Ring is done.
        CHECK(BannerBurnAllowed(1, true, true, DungeonKit::State::NotStarted));
        CHECK(!BannerBurnAllowed(1, false, true, DungeonKit::State::NotStarted));
        CHECK(!BannerBurnAllowed(1, true, false, DungeonKit::State::NotStarted));
        CHECK(!BannerBurnAllowed(1, true, true, DungeonKit::State::Done));
    }
}

int main()
{
    TestSliceAndIds();
    TestTeam();
    TestLeap();
    TestTheldren();
    TestKorv();
    TestLefty();
    TestVolida();
    TestMalgen();
    TestFloorSteps();
    TestVerdict();
    TestBanner();
    return Report("brd_ring_encore_test");
}
