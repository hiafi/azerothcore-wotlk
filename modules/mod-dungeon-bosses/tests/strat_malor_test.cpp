// Host tests for MalorLogic.h (S4: Malor the Zealous (11032)): the ids, the build spec numbers (ST 1239-1289), the beam
// lane and its blockers, Faith and Searing Faith (gains, caps, fade clocks), Unclean and Judgment, the Faith-scaled
// heals, the Miracle trigger, the cast plan (cadences, no overlap, priorities) and the arena.
#include "MalorLogic.h"
#include "check.h"
#include <cmath>

using namespace StratholmeRework;
using namespace StratMalor;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    Candidate At(std::uint64_t id, Vec2 pos, bool tank = false)
    {
        Candidate c;
        c.id = id;
        c.pos = pos;
        c.tank = tank;
        return c;
    }

    struct Start
    {
        CastPlan::Cast cast;
        std::uint64_t at;
    };

    // Plays the plan for `endMs`: one decision every `stepMs`, a cast holds him for its cast time. `miracleAt`: the
    // time his health falls to 10% (0: never).
    std::vector<Start> Simulate(std::uint64_t endMs, std::uint64_t miracleAt = 0, std::uint64_t stepMs = 100)
    {
        CastPlan plan;
        plan.Reset();
        std::vector<Start> out;
        std::uint64_t busyUntil = 0;
        for (std::uint64_t now = 0; now <= endMs; now += stepMs)
        {
            if (miracleAt && now >= miracleAt)
                plan.ArmMiracle(now);
            if (now < busyUntil)
                continue;
            std::optional<CastPlan::Cast> const next = plan.Next(now);
            if (!next)
                continue;
            plan.Started(*next, now);
            out.push_back({ *next, now });
            busyUntil = now + CastPlan::CastMs(*next);
        }
        return out;
    }

    std::vector<std::uint64_t> StartsOf(std::vector<Start> const& all, CastPlan::Cast cast)
    {
        std::vector<std::uint64_t> out;
        for (Start const& s : all)
            if (s.cast == cast)
                out.push_back(s.at);
        return out;
    }

    void TestIds()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 206480);
        CHECK(SPELL_MZ_BLAZE == 206480);
        CHECK(SPELL_MZ_MIRACLE_HEAL == 206493);
        CHECK(kSpellSlice.Contains(SPELL_MZ_BLAZE));
        CHECK(kSpellSlice.Contains(SPELL_MZ_MIRACLE_HEAL));
        // No other WP's slice overlaps Malor's.
        CHECK(!kSpellsBaroness.Contains(SPELL_MZ_BLAZE));
        CHECK(!kSpellsWilley.Contains(SPELL_MZ_MIRACLE_HEAL));
        CHECK(NPC_ST_MEDALLION == 300605);
        CHECK(kCreaturesWave2.first <= NPC_ST_MEDALLION && NPC_ST_MEDALLION <= kCreaturesWave2.last);
        CHECK(BossOfEntry(NPC_MALOR).value() == BOSS_MALOR);
    }

    // The build spec's numbers, one line each (ST 1239-1289 and the Heroic block).
    void TestSpecNumbers()
    {
        CHECK(kBlaze.first == 10000 && kBlaze.every == 30000 && kBlazeMs == 12000);
        CHECK(kBlaze.every > kBlazeMs);                     // blazes never overlap
        CHECK(kFaithPerSecond(false) == 1 && kFaithPerSecond(true) == 2);
        CHECK(kFaithMax == 10 && kFaithFadeMs == 8000);
        CHECK(Near(kFaithDamagePct, 5.f));
        CHECK(Near(kSearingPct(false), 2.f) && Near(kSearingPct(true), 3.f));
        CHECK(kSearingFadeMs == 2000);
        CHECK(kUncleanCount(false) == 1 && kUncleanCount(true) == 2);
        CHECK(kUncleanMs == 8000 && kUncleanPurifySeconds == 2);
        CHECK(Near(kJudgmentPct(false), 40.f) && Near(kJudgmentPct(true), 50.f));
        CHECK(kSmash.first == 15000 && kSmash.every == 15000 && kSmashCastMs == 2000);
        CHECK(Near(kSmashRadius, 8.f) && Near(kSmashPct, 30.f) && kSmashStunMs == 1000);
        CHECK(Near(kAftershockInner, 8.f) && Near(kAftershockOuter, 14.f) && Near(kAftershockPct, 30.f));
        CHECK(kAftershockWarnMs == 1500);
        // The ring's hole: the marker draws a hole above an inner / outer ratio of 0.25 (F-1 ruling).
        CHECK(kAftershockInner / kAftershockOuter >= 0.25f);
        CHECK(kHolyLight.first == 20000 && kHolyLight.every == 15000 && kHolyLightCastMs == 2500);
        CHECK(Near(kHolyLightBasePct(false), 0.f) && Near(kHolyLightBasePct(true), 3.f));
        CHECK(Near(kHolyLightPerStackPct, 1.f));
        CHECK(kHolyLightKickPriority(false) == 1 && kHolyLightKickPriority(true) == 3);
        CHECK(Near(kMiracleHealthPct, 10.f) && kMiracleCastMs == 3000 && Near(kMiracleHealPerStackPct, 8.f));
        CHECK(Near(kBeamWidth, 3.f));
        // A bot waits out the warning before the lane is judged; the lane lives the blaze's length.
        CHECK(kBeamWarnMs < kBlazeMs);
        // The park circle is re-registered before the bots' hold cap (8 s) and before it ends.
        CHECK(kParkHoldMs < 8000 && kParkRefreshLeadMs < kParkHoldMs);
    }

    // The room (handoff section 3.8): the strongbox, the dais mouth and the spawn all sit on his arena; the beam is
    // long enough for a blocker to stand clear of the 8 yd Smash, and clear of the 14 yd Aftershock too.
    void TestGeometry()
    {
        Arena const arena = MalorArena();
        CHECK(arena.Contains(kBeamSource, kMalorsStrongbox.z));
        CHECK(arena.Contains(kFightSpot, kMalorsStrongbox.z));
        CHECK(arena.Contains(kMalorSpawn.XY(), kMalorSpawn.z));
        float const length = DungeonKit::Distance(kBeamSource, kFightSpot);
        CHECK(Near(length, 19.3f, 0.2f));
        CHECK(length >= 10.f);                              // ST: held at least about 10 yd from the box
        CHECK(length > kSmashRadius + 2.f);                 // a blocker clears the Smash
        CHECK(length > kAftershockOuter);                   // and, near the box, the heroic ring
        // The strongbox is 5 yd from his spawn: before the tank moves him the lane is short.
        CHECK(DungeonKit::Distance(kBeamSource, kMalorSpawn.XY()) < 6.f);
        CHECK(ArenaFor(BOSS_MALOR).Contains(kFightSpot, kMalorsStrongbox.z));
    }

    void TestBeamLane()
    {
        Vec2 const from{ 0.f, 0.f };
        Vec2 const to{ 20.f, 0.f };                         // 20 yd north
        CHECK(InBeam(from, to, 1.5f, { 10.f, 0.f }));       // on the line
        CHECK(InBeam(from, to, 1.5f, { 10.f, 1.5f }));      // the lane's edge
        CHECK(InBeam(from, to, 1.5f, { 10.f, -1.5f }));
        CHECK(!InBeam(from, to, 1.5f, { 10.f, 1.6f }));     // just outside
        CHECK(!InBeam(from, to, 1.5f, { -0.5f, 0.f }));     // behind the box: flat end
        CHECK(!InBeam(from, to, 1.5f, { 20.5f, 0.f }));     // behind him: flat end
        CHECK(InBeam(from, to, 1.5f, { 0.f, 0.f }));
        CHECK(InBeam(from, to, 1.5f, { 20.f, 0.f }));
        CHECK(!InBeam(from, from, 1.5f, { 0.f, 0.f }));     // no lane when he is on the box

        // A slanted lane: 3-4-5, 10 yd long.
        Vec2 const slantTo{ 6.f, 8.f };
        CHECK(InBeam(from, slantTo, 1.5f, { 3.f, 4.f }));
        CHECK(InBeam(from, slantTo, 1.5f, { 3.f + 0.8f, 4.f - 0.6f }));     // 1 yd across
        CHECK(!InBeam(from, slantTo, 1.5f, { 3.f + 1.6f, 4.f - 1.2f }));    // 2 yd across

        // Blockers: the non-tanks inside; the tank never blocks.
        std::vector<Candidate> const c{ At(1, { 5.f, 0.f }), At(2, { 5.f, 3.f }), At(3, { 15.f, -1.f }, true),
            At(4, { 19.f, 1.f }), At(5, { 30.f, 0.f }) };
        std::vector<std::size_t> const b = Blockers(from, to, kBeamHalfWidth, c);
        CHECK(b.size() == 2 && b[0] == 0 && b[1] == 3);
        CHECK(Blockers(from, to, kBeamHalfWidth, std::vector<Candidate>{}).empty());
        CHECK(Blockers(from, to, kBeamHalfWidth, std::vector<Candidate>{ At(9, { 10.f, 0.f }, true) }).empty());

        // The real lane: from the strongbox to the dais mouth. A non-tank on its midpoint blocks; a tank does not.
        Vec2 const mid{ (kBeamSource.x + kFightSpot.x) / 2.f, (kBeamSource.y + kFightSpot.y) / 2.f };
        CHECK(InBeam(kBeamSource, kFightSpot, kBeamHalfWidth, mid));
        CHECK(!Blockers(kBeamSource, kFightSpot, kBeamHalfWidth, std::vector<Candidate>{ At(1, mid) }).empty());
        CHECK(Blockers(kBeamSource, kFightSpot, kBeamHalfWidth, std::vector<Candidate>{ At(1, mid, true) }).empty());
    }

    void TestBeamRefresh()
    {
        CHECK(!BeamNeedsRefresh(19.3f, 19.3f));
        CHECK(!BeamNeedsRefresh(19.3f, 21.9f));             // under 3 yd of drift
        CHECK(BeamNeedsRefresh(19.3f, 22.4f));
        CHECK(BeamNeedsRefresh(19.3f, 15.0f));
        CHECK(kBeamRefreshMinLeftMs > kBeamRefreshWarnMs);
        // "Unclean first": the free lane opens when none is left, or 3 s into the blaze.
        CHECK(FreeBlockersDue(0, 0));
        CHECK(!FreeBlockersDue(0, 1));
        CHECK(!FreeBlockersDue(2999, 2));
        CHECK(FreeBlockersDue(3000, 2));
        CHECK(FreeBlockersDue(8000, 1));
    }

    void TestFaith()
    {
        // An unblocked blaze: 12 ticks. Normal: +1 a second to the cap of 10; heroic +2 and the cap in 5.
        std::uint32_t n = 0;
        for (int i = 0; i < 12; ++i)
            n = FaithAfter(n, kFaithPerSecond(false));
        CHECK(n == 10);
        std::uint32_t h = 0;
        int ticks = 0;
        while (h < kFaithMax)
        {
            h = FaithAfter(h, kFaithPerSecond(true));
            ++ticks;
        }
        CHECK(ticks == 5 && h == 10);
        CHECK(FaithAfter(9, 2) == 10);                      // the cap holds
        CHECK(FaithAfter(10, 2) == 10);
        // +5% damage done per stack: 10 stacks, +50%.
        CHECK(Near(kFaithDamagePct * static_cast<float>(kFaithMax), 50.f));
        // ST "Failing paths": never blocking leaves him at 6 to 10 stacks, +30 to +50%.
        CHECK(Near(kFaithDamagePct * 6, 30.f));
    }

    void TestSearing()
    {
        // Holding the beam 4 s costs about 20%: the damage ticks of stacks 1..4 at 2% each, ignoring the fade.
        float total = 0.f;
        std::uint32_t stacks = 0;
        for (int i = 0; i < 4; ++i)
        {
            stacks = SearingAfter(stacks);
            total += kSearingPct(false) * static_cast<float>(stacks);
        }
        CHECK(stacks == 4 && Near(total, 20.f));
        // The cap is the blaze's length; a fair rotation never reaches it.
        std::uint32_t capped = 0;
        for (int i = 0; i < 20; ++i)
            capped = SearingAfter(capped);
        CHECK(capped == kSearingMaxStacks && capped == kBlazeMs / kBlazeTickMs);
        // The bots' rotation cap sits well below it.
        CHECK(kSearingClaimCap < kSearingMaxStacks);
    }

    void TestFade()
    {
        // Faith: one stack per 8 s once seen; a new stack does not restart the clock.
        std::uint64_t next = 0;
        CHECK(FadeDue(0, 1000, next, 8000) == 0 && next == 0);
        CHECK(FadeDue(3, 1000, next, 8000) == 0 && next == 9000);       // first look starts the clock
        CHECK(FadeDue(3, 8999, next, 8000) == 0);
        CHECK(FadeDue(3, 9000, next, 8000) == 1 && next == 17000);
        CHECK(FadeDue(2, 10000, next, 8000) == 0);                      // a later look: not yet
        CHECK(FadeDue(2, 25000, next, 8000) == 2 && next == 0);         // both gone, the clock stops
        // A late look catches up on every fade due.
        next = 0;
        CHECK(FadeDue(5, 0, next, 2000) == 0);                          // the clock starts: first fade at 2000
        CHECK(FadeDue(5, 6500, next, 2000) == 3 && next == 8000);       // 2000, 4000 and 6000 passed
        // Searing Faith: still in the beam, the clock restarts; out of it, one per 2 s.
        std::uint64_t searing = 0;
        FadeDue(4, 0, searing, kSearingFadeMs);
        CHECK(searing == 2000);
        HoldFade(1000, searing, kSearingFadeMs);
        CHECK(searing == 3000);
        CHECK(FadeDue(4, 2500, searing, kSearingFadeMs) == 0);
        CHECK(FadeDue(4, 3000, searing, kSearingFadeMs) == 1 && searing == 5000);
        CHECK(FadeDue(3, 7000, searing, kSearingFadeMs) == 2 && searing == 9000);
    }

    void TestUnclean()
    {
        // Two seconds in the beam (cumulative) purify; running out is Judgment.
        UncleanTrack t;
        t.endMs = 18000;
        CHECK(!UncleanTick(t, false));
        CHECK(!UncleanTick(t, true));
        CHECK(!UncleanTick(t, false));
        CHECK(UncleanTick(t, true));                        // the second second in the beam
        UncleanTrack never;
        never.endMs = 18000;
        CHECK(!UncleanExpired(never, 17999));
        CHECK(UncleanExpired(never, 18000));
        // 8 s inside a 12 s blaze: the bearer has time to walk to the beam.
        CHECK(kUncleanMs < kBlazeMs);
        CHECK(kUncleanMs / kBlazeTickMs >= kUncleanPurifySeconds + 3);
        // Judgment: 40% of 3,670 = 1,468; heroic 50% of 4,120 = 2,060.
        CHECK(DungeonKit::RefFlatValue(3670, 3710, kJudgmentPct(false), false) == 1468);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kJudgmentPct(true), false) == 2060);
    }

    void TestHits()
    {
        // Ground Smash 30%: 1,101 normal non-tank, 1,113 tank; heroic 1,236 / 1,233.
        CHECK(DungeonKit::RefFlatValue(3670, 3710, kSmashPct, false) == 1101);
        CHECK(DungeonKit::RefFlatValue(3670, 3710, kSmashPct, true) == 1113);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kAftershockPct, false) == 1236);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kAftershockPct, true) == 1233);
        // Searing Faith: 2% = 73 a stack and second; heroic 3% = 124.
        CHECK(DungeonKit::RefFlatValue(3670, 3710, kSearingPct(false), false) == 73);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kSearingPct(true), false) == 124);
    }

    void TestHeals()
    {
        // Holy Light: normal 1% a stack; heroic 3% plus 1% a stack.
        CHECK(Near(HolyLightHealPct(false, 0), 0.f));
        CHECK(Near(HolyLightHealPct(false, 10), 10.f));
        CHECK(Near(HolyLightHealPct(true, 0), 3.f));
        CHECK(Near(HolyLightHealPct(true, 10), 13.f));
        CHECK(HealAmount(175000, HolyLightHealPct(false, 6)) == 10500);
        CHECK(HealAmount(230000, HolyLightHealPct(true, 0)) == 6900);
        CHECK(HealAmount(230000, HolyLightHealPct(true, 10)) == 29900);
        // Miracle: 8% a stack: nothing at 0, 80% at 10.
        CHECK(Near(MiracleHealPct(0), 0.f));
        CHECK(Near(MiracleHealPct(10), 80.f));
        CHECK(HealAmount(175000, MiracleHealPct(10)) == 140000);
        CHECK(HealAmount(175000, MiracleHealPct(0)) == 0);
        CHECK(HealAmount(175000, -5.f) == 0);
        // The trigger: 10% health or lower, once.
        CHECK(!MiracleDue(10.5f, false));
        CHECK(MiracleDue(10.f, false));
        CHECK(MiracleDue(3.f, false));
        CHECK(!MiracleDue(3.f, true));
        CHECK(NextOnCadence(10000, 10500, 30000) == 40000);
        CHECK(NextOnCadence(10000, 45000, 30000) == 45001);     // a start that ran very late
    }

    void TestCastPlan()
    {
        std::vector<Start> const all = Simulate(94000);
        std::vector<std::uint64_t> const smash = StartsOf(all, CastPlan::Smash);
        std::vector<std::uint64_t> const holy = StartsOf(all, CastPlan::HolyLight);
        // Smash from 15 s every 15 s; Holy Light from 20 s every 15 s (the plan checks every 100 ms).
        CHECK(smash.size() == 6);
        CHECK(smash[0] == 15000 && smash[1] == 30000 && smash[5] == 90000);
        CHECK(holy.size() == 5);
        CHECK(holy[0] == 20000 && holy[1] == 35000 && holy[4] == 80000);
        // No two casts overlap, and each waits the spacing after the last.
        for (std::size_t i = 1; i < all.size(); ++i)
            CHECK(all[i].at >= all[i - 1].at + CastPlan::CastMs(all[i - 1].cast) + kCastSpacingMs);
        CHECK(StartsOf(all, CastPlan::Miracle).empty());

        // The Miracle: due when his health falls, goes before a due Holy Light and Smash, once.
        std::vector<Start> const withMiracle = Simulate(94000, 20000);
        std::vector<std::uint64_t> const miracle = StartsOf(withMiracle, CastPlan::Miracle);
        CHECK(miracle.size() == 1);
        CHECK(miracle[0] == 20000);                                 // the Holy Light due at 20 s waits for it
        std::vector<std::uint64_t> const holy2 = StartsOf(withMiracle, CastPlan::HolyLight);
        CHECK(!holy2.empty() && holy2[0] >= 20000 + kMiracleCastMs + kCastSpacingMs);
        // A Holy Light due with a Smash: the interruptible cast first.
        CastPlan plan;
        plan.Reset();
        CHECK(!plan.Next(14999).has_value());
        CHECK(plan.Next(15000).value() == CastPlan::Smash);
        CHECK(plan.Next(20000).value() == CastPlan::HolyLight);     // both due at 20 s: the Holy Light first
        // Refused: tried again in a second, the cadence unchanged.
        plan.Started(CastPlan::Smash, 15000);
        CHECK(plan.DueAt(CastPlan::Smash).value() == 30000);
        plan.Refused(CastPlan::HolyLight, 20000);
        CHECK(plan.DueAt(CastPlan::HolyLight).value() == 21000);
        // An interrupted Holy Light frees him at once.
        plan.Reset();
        plan.Started(CastPlan::HolyLight, 20000);
        CHECK(!plan.Next(20100).has_value());                       // busy and spaced
        plan.Interrupted(20400);
        CHECK(plan.DueAt(CastPlan::HolyLight).value() == 35000);
        // The Miracle is armed once.
        plan.Reset();
        plan.ArmMiracle(1000);
        plan.Started(CastPlan::Miracle, 1000);
        CHECK(plan.MiracleUsed());
        plan.ArmMiracle(9000);
        CHECK(!plan.DueAt(CastPlan::Miracle).has_value());
        CHECK(CastPlan::Every(CastPlan::Smash) == kSmash.every);
        CHECK(CastPlan::CastMs(CastPlan::HolyLight) == kHolyLightCastMs);
    }
}

int main()
{
    TestIds();
    TestSpecNumbers();
    TestGeometry();
    TestBeamLane();
    TestBeamRefresh();
    TestFaith();
    TestSearing();
    TestFade();
    TestUnclean();
    TestHits();
    TestHeals();
    TestCastPlan();

    return Report("strat_malor_test");
}
