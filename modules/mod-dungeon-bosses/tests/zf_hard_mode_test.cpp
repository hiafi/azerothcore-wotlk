// Host tests for GahzrillaCrewHardModeLogic.h (D7Ha, the crew at the pool): the slice, the package's clock, where the
// crew stand (their fight spots, the shore, the dry-spot search), the crew's rules (2 s late out of water, the
// Discharge on their own health, Murta's heal pick, their small hits), the five answers (the spring's spot, Storm's
// Chosen, Siphon Charge, Mass Dispel, Raven's kick) and a budget run of the crew through Storm Builds' Discharges.
#include "GahzrillaCrewHardModeLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfPoolCrew;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // The beats' firing times over `ms` (one tick a 100 ms), with the springs stopped at `stopSpringsAt` (0: never).
    struct ClockRun
    {
        std::vector<std::uint64_t> springs, chosen, overcharge;
    };

    ClockRun RunClock(std::uint64_t ms, std::uint64_t stopSpringsAt = 0)
    {
        ClockRun out;
        HardModeClock clock;
        clock.Start();
        for (std::uint64_t t = 0; t < ms; t += 100)
        {
            clock.Advance(100);
            if (stopSpringsAt && clock.Now() >= stopSpringsAt && clock.SpringsRunning())
                clock.StopSprings();
            for (HmAct act = clock.Next(); act != HmAct::None; act = clock.Next())
            {
                if (act == HmAct::Wellspring)
                    out.springs.push_back(clock.Now());
                else if (act == HmAct::StormsChosen)
                    out.chosen.push_back(clock.Now());
                else
                    out.overcharge.push_back(clock.Now());
                clock.Done(act);
            }
        }
        return out;
    }

    // The crew's budget through the hard mode's Discharges (section 3.7's table, from his arrival): each of the five
    // stays dry (no Charged) and Conductive is dispelled; Murta heals the lowest under 80% every 8.5 s (2.5 s cast + 6
    // s), never starting into a Discharge. Returns the Discharge at which the first member falls (0: none by `upTo`).
    std::uint32_t FirstCrewFall(std::uint32_t upTo, bool murtaHeals)
    {
        std::vector<float> health(kCrewCount, 100.f);
        std::uint64_t nextHeal = 0;
        std::uint64_t healLands = 0;
        std::uint32_t healTarget = 0;
        std::uint32_t landed = 0;
        std::uint64_t const end = ZfPool::DischargeLandsAt(true, upTo);
        for (std::uint64_t t = 0; t <= end; t += 100)
        {
            if (healLands && t >= healLands)
            {
                health[healTarget] = std::min(100.f, health[healTarget] + Tune::kGreaterHealPct);
                healLands = 0;
            }
            if (ZfPool::DischargeLandsAt(true, landed + 1) <= t)
            {
                ++landed;
                for (float& h : health)
                    h -= CrewDischargePct(0);
                for (float const h : health)
                    if (h <= 0.f)
                        return landed;
            }
            if (!murtaHeals || healLands || t < nextHeal)
                continue;
            std::uint64_t const nextIn = ZfPool::DischargeLandsAt(true, landed + 1) - t;
            if (!CastFitsBeforeDischarge(nextIn, Tune::kGreaterHealCastMs))
                continue;
            std::vector<HealCandidate> crew;
            for (std::uint32_t m = 0; m < kCrewCount; ++m)
                crew.push_back({ m, health[m], true, true });
            if (std::optional<std::uint32_t> pick = HealPick(crew))
            {
                healTarget = *pick;
                healLands = t + Tune::kGreaterHealCastMs;
                nextHeal = t + Tune::kGreaterHealCastMs + Tune::kGreaterHealEveryMs;
            }
        }
        return 0;
    }
}

int main()
{
    // ---- the slice ------------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 214150 && kSpellSlice.last == 214189);
    CHECK(SPELL_HM_WELLSPRING == 214150 && SPELL_HM_TWIN_CALL == 214162);
    CHECK(kFirstSpareSpell == 214163 && kSpellSlice.Contains(kFirstSpareSpell - 1));
    // The tags sit in the hard mode's band, apart from D7Hb's 37 and 38 and D7's 31-34, 41, 42.
    for (std::uint32_t tag : { std::uint32_t(TAG_HM_GATHER), std::uint32_t(TAG_HM_OVERCHARGE),
        std::uint32_t(TAG_HM_CHOSEN), std::uint32_t(TAG_HM_BLAST) })
    {
        CHECK(tag >= 35 && tag <= 40);
        CHECK(tag != 37 && tag != 38);
    }
    CHECK(SHEET_WELLSPRING >= 10 && SHEET_WELLSPRING < 30);
    CHECK(kPointCrewFight >= 100 && kPointWeegliSpring >= 100 && kPointCrewHome >= 100);
    CHECK(EMOTE_GAHZRILLA_DEVOURS == 2);
    // the gong (S0's stub check)
    CHECK(PoolArena().Contains(kGong.XY(), kGong.z));

    // ---- the numbers (SP GZ15-GZ21, section 10) ------------------------------------------------------------------
    CHECK(Tune::kWellspringFirstMs == 20000 && Tune::kWellspringEveryMs == 40000);
    CHECK(Near(Tune::kWellspringRadiusYd, 6.f) && Near(Tune::kWellspringGrowYd, 2.f));
    CHECK(Tune::kWellspringGrowEveryMs == 5000 && Near(Tune::kWellspringMinFromPlayerYd, 15.f));
    CHECK(Tune::kPlantMs == 5000 && Tune::kFuseMs == 3000 && Near(Tune::kBlastRadiusYd, 10.f));
    CHECK(Near(Tune::kBlastPct, 60.f));
    CHECK(Tune::kChosenFirstMs == 15000 && Tune::kChosenEveryMs == 30000 && Tune::kChosenMarkMs == 4000);
    CHECK(Near(Tune::kChosenPct, 150.f) && Near(Tune::kBodyguardYd, 5.f) && Tune::kBodyguardCharged == 2);
    CHECK(Tune::kChosenSplitCharged == 1);
    CHECK(Tune::kOverchargeFirstMs == 25000 && Tune::kOverchargeEveryMs == 25000 && Tune::kOverchargeMs == 8000);
    CHECK(Tune::kOverchargeStacks == 5 && Near(Tune::kSiphonRangeYd, 10.f) && Tune::kSiphonMs == 3000);
    CHECK(Tune::kSiphonOroCharged == 1);
    CHECK(Tune::kMassDispelCastMs == 2000 && Near(Tune::kMassDispelRangeYd, 15.f));
    CHECK(Tune::kTwinCallCastMs == 2000);
    CHECK(Tune::kWaterExitLateMs == 2000 && Near(Tune::kDevourHealPct, 5.f));
    // The crew's damage: about 15% of the hard mode's target group DPS (3,774, section 3.6), within a point.
    std::uint32_t dps = 0;
    for (std::uint32_t d : Tune::kCrewDps)
        dps += d;
    CHECK(dps >= 528 && dps <= 604);
    CHECK(CrewHitAmount(CREW_BLY) == 300 && CrewHitAmount(CREW_MURTA) == 92 && CrewHitAmount(9) == 0);
    CHECK(CrewHitCapped(300, 1000) == 300 && CrewHitCapped(300, 120) == 119 && CrewHitCapped(300, 1) == 0);

    // ---- the clock ------------------------------------------------------------------------------------------------
    {
        ClockRun const r = RunClock(180000);
        CHECK(r.springs.size() == 5 && r.springs.front() == 20000 && r.springs[1] == 60000 && r.springs[4] == 180000);
        CHECK(r.chosen.size() == 6 && r.chosen.front() == 15000 && r.chosen[1] == 45000);
        CHECK(r.overcharge.size() == 7 && r.overcharge.front() == 25000 && r.overcharge[1] == 50000);
        // The Deluge stops the springs (SP: phases 1 and 2 only); the marks go on.
        ClockRun const d = RunClock(180000, 70000);
        CHECK(d.springs.size() == 2);
        CHECK(d.chosen.size() == r.chosen.size() && d.overcharge.size() == r.overcharge.size());
        // A retried beat (no boss to own it) comes back half a second later, then keeps its grid.
        HardModeClock clock;
        clock.Start();
        clock.Advance(15000);
        CHECK(clock.Next() == HmAct::StormsChosen);
        clock.Retry(HmAct::StormsChosen);
        CHECK(clock.Next() == HmAct::None);
        clock.Advance(ZfPool::Tune::kRetryMs);
        CHECK(clock.Next() == HmAct::StormsChosen);
        clock.Done(HmAct::StormsChosen);
        CHECK(clock.In(HmAct::StormsChosen) == 30000 - ZfPool::Tune::kRetryMs);
        clock.Stop();
        CHECK(!clock.Running() && clock.Next() == HmAct::None);
    }

    // ---- where the crew stand ------------------------------------------------------------------------------------
    {
        Vec2 const ashore = kGahzrillaAshore.XY();
        Vec2 const group{ 1706.f, 1235.f };     // CR's waiting disc (BlyCrewLogic.h kPoolWaitCenter)
        float const toGroup = DungeonKit::BearingTo(ashore, group);
        std::vector<Vec2> spots;
        for (std::uint32_t m = 0; m < kCrewCount; ++m)
        {
            Vec2 const p = CrewFightSpot(m, ashore, toGroup, 15.f);
            spots.push_back(p);
            CHECK(Near(DungeonKit::Distance(ashore, p), IsMeleeCrew(m) ? 14.f : Tune::kCrewRangedYd, 0.05f));
        }
        // No two crew within a Conductive arc of each other (6 yd) at his reach of 15.
        for (std::size_t i = 0; i < spots.size(); ++i)
            for (std::size_t j = i + 1; j < spots.size(); ++j)
                CHECK(DungeonKit::Distance(spots[i], spots[j]) > ZfPool::Tune::kConductiveArcYd);
        // Murta stands on the line to the group (the gather, GZ19).
        CHECK(Near(DungeonKit::BearingTo(ashore, spots[CREW_MURTA]), toGroup, 0.01f));
        // Velratha's reach is small: the melee pair stands at the 2 yd floor.
        CHECK(Near(CrewFightDistance(CREW_BLY, 1.5f), Tune::kCrewMinMeleeYd));
        CHECK(Near(CrewFightDistance(CREW_ORO, 1.5f), Tune::kCrewRangedYd));
        CHECK(Near(CrewFightSpot(9, ashore, 0.f, 15.f).x, ashore.x));
        // BearingToMiddle: the fallback with nobody, and the middle's bearing otherwise.
        CHECK(Near(BearingToMiddle(ashore, {}, 1.25f), 1.25f));
        std::vector<Vec2> const two{ { ashore.x + 10.f, ashore.y + 2.f }, { ashore.x + 10.f, ashore.y - 2.f } };
        CHECK(Near(BearingToMiddle(ashore, two, 3.f), 0.f));
    }
    {
        // The shore: Velratha's spawn and the crew's pool spots are dry shore; the pool's middle and its bank are not.
        CHECK(OnShore(kVelrathaSpawn.XY()));
        CHECK(OnShore({ 1706.f, 1235.f }));
        CHECK(!OnShore(kPoolMiddle));
        CHECK(!OnShore({ 1667.f, 1189.f }));
        CHECK(!OnShore({ 1500.f, 1100.f }));
        CHECK(InPoolStrip(kPoolMiddle) && !InPoolStrip(kVelrathaSpawn.XY()));
        // The search: nearest first, the extras (ice) last; NearestOf keeps the nearest accepted.
        Vec2 const want{ 1700.f, 1220.f };
        std::vector<Vec2> const ice{ { 1690.f, 1230.f } };
        std::vector<Vec2> const c = SearchCandidates(want, ice);
        CHECK(c.size() == (Tune::kSearchRingsYd.size() - 1) * Tune::kSearchAngles + 1 + ice.size());
        CHECK(Near(c.front().x, want.x) && Near(c.back().x, 1690.f));
        std::optional<Vec2> const any = NearestOf(want, c, [](Vec2) { return true; });
        CHECK(any && Near(any->x, want.x) && Near(any->y, want.y));
        std::optional<Vec2> const onlyIce = NearestOf(want, c, [](Vec2 p) { return Near(p.x, 1690.f) &&
            Near(p.y, 1230.f); });
        CHECK(onlyIce && Near(onlyIce->y, 1230.f));
        std::optional<Vec2> const far = NearestOf(want, c, [&](Vec2 p) { return DungeonKit::Distance(p, want) > 5.f; });
        CHECK(far && Near(DungeonKit::Distance(*far, want), 6.f, 0.05f));
        CHECK(!NearestOf(want, c, [](Vec2) { return false; }));
        // From the pool's middle the nearest dry shore is found within the search (a swimmer gets out).
        std::vector<Vec2> const out = SearchCandidates(kPoolMiddle);
        std::optional<Vec2> const shore = NearestOf(kPoolMiddle, out, [](Vec2 p) { return OnShore(p); });
        CHECK(shore.has_value());
        CHECK(shore && DungeonKit::Distance(*shore, kPoolMiddle) <= 20.f);
    }

    // ---- the crew's rules ----------------------------------------------------------------------------------------
    CHECK(!WaterExitDue(1000, 0) && !WaterExitDue(2999, 1000) && WaterExitDue(3000, 1000));
    CHECK(Near(CrewDischargePct(0), 40.f) && Near(CrewDischargePct(3), 52.f) && Near(CrewDischargePct(15), 100.f));
    CHECK(PctOfHealth(113229, 40.f) == 45291 && PctOfHealth(55000, 0.f) == 0 && PctOfHealth(0, 40.f) == 0);
    CHECK(PctOfHealth(10, 1.f) == 1 && PctOfHealth(100, 250.f) == 100);
    {
        std::vector<HealCandidate> crew{ { 0, 90.f, true, true }, { 1, 60.f, true, true }, { 2, 40.f, false, true },
            { 3, 30.f, true, false }, { 4, 79.f, true, true } };
        CHECK(HealPick(crew) == std::optional<std::uint32_t>(1));
        crew[1].healthPct = 85.f;
        CHECK(HealPick(crew) == std::optional<std::uint32_t>(4));
        crew[4].healthPct = 80.f;
        CHECK(!HealPick(crew));
    }
    // A player's heal on the crew: the share of a player's health it would fill (never scaled down).
    CHECK(ScaledCrewHeal(1000, 113229, 4120) == 27482 && ScaledCrewHeal(1000, 3000, 4120) == 1000);
    CHECK(ScaledCrewHeal(1000, 55000, 0) == 1000);
    CHECK(CastFitsBeforeDischarge(0, 2500) && CastFitsBeforeDischarge(3001, 2500));
    CHECK(!CastFitsBeforeDischarge(3000, 2500) && !CastFitsBeforeDischarge(1000, 2500));

    // ---- the five answers ----------------------------------------------------------------------------------------
    {
        // GZ15: the spring's spots: on the shore, within 40 yd of the pool, 15 yd from every player.
        std::vector<Vec2> const none = SpringCandidates({});
        CHECK(none.size() > 100);
        for (Vec2 const& p : none)
        {
            CHECK(OnShore(p));
            CHECK(DungeonKit::Distance(p, kPoolMiddle) <= Tune::kWellspringMaxFromPoolYd);
        }
        // The group at the waiting spots and Gahz'rilla's tank ashore: springs still have room, never near them.
        std::vector<Vec2> players;
        for (Point3 const& s : { Point3{ 1702.f, 1235.f, 9.5f }, Point3{ 1706.f, 1239.f, 9.5f },
            Point3{ 1710.f, 1235.f, 9.5f } })
            players.push_back(s.XY());
        players.push_back(kGahzrillaAshore.XY());
        players.push_back(kVelrathaSpawn.XY());
        std::vector<Vec2> const some = SpringCandidates(players);
        CHECK(!some.empty());
        for (Vec2 const& p : some)
            for (Vec2 const& q : players)
                CHECK(DungeonKit::Distance(p, q) >= Tune::kWellspringMinFromPlayerYd);
        CHECK(!SpringSpotOk(kPoolMiddle, {}));
        std::printf("springs: %zu spots with nobody, %zu with five players spread on the shore\n", none.size(),
            some.size());
    }
    // GZ17: Bly takes it (alive, able, within 5 yd); else the mark alone; Bly dead: the split.
    CHECK(ChosenFor(true, true, 4.9f) == Chosen::Bodyguard);
    CHECK(ChosenFor(true, true, 5.f) == Chosen::Bodyguard);
    CHECK(ChosenFor(true, true, 5.1f) == Chosen::Alone);
    CHECK(ChosenFor(true, false, 1.f) == Chosen::Alone);
    CHECK(ChosenFor(false, false, 1.f) == Chosen::Split);
    // GZ18: Oro starts only if able, within 10 yd and with the whole channel left.
    CHECK(SiphonCanStart(true, 9.f, 3000));
    CHECK(!SiphonCanStart(true, 10.5f, 8000));
    CHECK(!SiphonCanStart(true, 5.f, 2999));
    CHECK(!SiphonCanStart(false, 5.f, 8000));
    // GZ19 and GZ20.
    CHECK(InMassDispel(15.f) && !InMassDispel(15.1f));
    CHECK(RavenCanKick(true, true, Tune::kRavenKickDelayMs));
    CHECK(!RavenCanKick(true, true, Tune::kRavenKickDelayMs - 1));
    CHECK(!RavenCanKick(true, false, 1500) && !RavenCanKick(false, true, 1500));

    // ---- the crew's budget -----------------------------------------------------------------------------------------
    {
        // Dry and dispelled, the crew outlast two Discharges on their own; Murta's heals carry them further. Past
        // that they need the group's healer (section 7 #17 A): the budget SP names. Reported, not gated past 3.
        std::uint32_t const bare = FirstCrewFall(13, false);
        std::uint32_t const healed = FirstCrewFall(13, true);
        CHECK(bare == 3);
        CHECK(healed == 0 || healed >= bare);
        std::printf("crew budget: first fall at Discharge %u unhealed, %u with Murta alone (0: none by 13)\n", bare,
            healed);
    }

    return Report("zf_hard_mode_test");
}
