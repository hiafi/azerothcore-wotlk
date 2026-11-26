// Host tests for TechbotLogic.h (D1): the slice, the dish, the bug rise points, the Duplicator's clock (normal once,
// heroic repeating, the cap with bars in flight, the heroic ceiling, a copy's clock, a stopped cast, a refused start,
// completion), the Patch heal and Version, the Rubber Band's steps, the timeline's no-starve rule, and every timed
// beat over a simulated fight.
#include "TechbotLogic.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace GnomereganRework;
using namespace GnomerTechbot;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Runs a unit's clock for `ms` in steps of `step`, starting a due cast and completing it after the cast time.
    struct Sim
    {
        DupRule rule;
        DupClock clock;
        std::uint32_t castLeft = 0;

        explicit Sim(DupRule r) : rule(r), clock(StartClock(r)) { }

        void Run(std::uint32_t ms, std::uint32_t alive, bool stopEachCast = false, std::uint32_t step = 100)
        {
            for (std::uint32_t t = 0; t < ms; t += step)
            {
                clock.lifeMs += step;
                if (clock.casting)
                {
                    if (stopEachCast)
                    {
                        OnCastEnded(clock, rule, false);
                        continue;
                    }
                    castLeft = castLeft > step ? castLeft - step : 0;
                    if (!castLeft)
                        OnCastEnded(clock, rule, true);
                }
                else if (DueToStart(clock, rule, alive))
                {
                    OnCastStarted(clock);
                    castLeft = rule.castMs;
                }
            }
        }
    };
}

int main()
{
    // ---- the slice and the room --------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 214300 && kSpellSlice.last == 214339);
    CHECK(kSpellSlice.Contains(kFirstSpell) && kSpellSlice.Contains(kLastSpell));
    CHECK(kLastSpell - kFirstSpell + 1 == 23);
    // His spot (ruling 61) is on the dish, and the dish is his arena.
    CHECK(ArenaFor(BOSS_TECHBOT).Contains(kTechbotSpawn.XY(), kTechbotSpawn.z));
    CHECK(DishArena().Contains(kTechbotSpawn.XY(), kTechbotSpawn.z));

    // ---- difficulty switches and spells ---------------------------------------------------------------------------
    CHECK(LagSpikeOn(false) && !LagSpikeOn(true));
    CHECK(!RubberBandOn(false) && RubberBandOn(true));
    CHECK(!BattleNetOn(false) && BattleNetOn(true));
    CHECK(!VersionOn(false) && VersionOn(true));
    CHECK(DuplicationSpell(false) == SPELL_DUPLICATION && DuplicationSpell(true) == SPELL_DUPLICATION_H);
    CHECK(PatchSpell(false) == SPELL_PATCH && PatchSpell(true) == SPELL_PATCH_H);
    // The text groups SP prints (rule 35) and the drill's tags (BM MechanicDrill.h kGnTag*).
    CHECK(SAY_CHATTER == 0 && EMOTE_LAG == 1 && YELL_PATCH == 2 && YELL_PATCH_FIXED == 3 && YELL_PATCH_CLEAN == 4);
    CHECK(YELL_SHUTDOWN == 5 && EMOTE_RUBBER_BAND == 6 && EMOTE_DUPLICATE == 0);
    CHECK(TAG_LAG_SPIKE == 1 && TAG_RUBBER_RUN_OUT == 2 && TAG_SAVE_POINT == 3 && TAG_RUBBER_SPIKE == 4);
    CHECK(TAG_BUG_ECHO == 5 && TAG_BATTLE_NET == 6);
    // Kick priorities: Duplication over Patch, Patch's never-kick entry 0.
    CHECK(kKickDuplication > kKickPatch && kKickPatch > kNeverKick && kNeverKick == 0);
    CHECK(kKillCastingBug > kKillBug && kKillBug > 0);

    // ---- damage: Version ------------------------------------------------------------------------------------------
    CHECK(Near(VersionMultiplier(0), 1.f));
    CHECK(Near(VersionMultiplier(4), 1.2f));
    CHECK(Near(ScaledPct(60.f, 10), 90.f));
    CHECK(VersionAuraAmount(7) == 35);
    CHECK(VersionShownStacks(300) == 255 && VersionShownStacks(12) == 12);

    // ---- TB4: the Patch heal --------------------------------------------------------------------------------------
    CHECK(PatchHeal(60001, 0, false) == 0);
    CHECK(PatchHeal(60001, 8, false) == 14400);         // 24% at the cap (SP)
    CHECK(PatchHeal(333333, 5, true) == 66667);         // 4% per bug on heroic
    CHECK(PatchHeal(1000, 1, false) == 30);

    // ---- TB2: the cap and the rise points -------------------------------------------------------------------------
    CHECK(BugMayRise(7, false) && !BugMayRise(8, false));
    // R-1-A m1: a Duplication bar in flight is a bug on its way (7 alive and one bar: no rise).
    CHECK(!BugMayRise(7, false, 1) && BugMayRise(6, false, 1));
    // DQ3: heroic has no design cap, only the technical ceiling of 64.
    CHECK(Tune::kBugSafetyCeiling == 64 && BugLimit(true) == 64 && BugLimit(false) == 8);
    CHECK(BugMayRise(63, true) && !BugMayRise(64, true) && !BugMayRise(60, true, 4));
    {
        Vec2 const boss{ kTechbotSpawn.x, kTechbotSpawn.y };
        auto onDish = [](Vec2 p) { return DishArena().Contains(p, kTechbotSpawn.z); };
        std::vector<Vec2> bugs;
        for (int i = 0; i < 6; ++i)
        {
            Vec2 const p = RisePoint(boss, kTechbotSpawn.o, bugs, onDish);
            CHECK(Near(DungeonKit::Distance(p, boss), Tune::kBugRiseYd, 0.05f));    // 3 yd from him
            CHECK(onDish(p));
            for (Vec2 const& b : bugs)
                CHECK(DungeonKit::Distance(p, b) >= Tune::kBugApartYd - 0.05f);    // 3 yd from each other
            bugs.push_back(p);
        }
        // A full ring: the 3 yd circle has room for 6 (60 degrees apart); the next one falls back to his spot.
        Vec2 const seventh = RisePoint(boss, kTechbotSpawn.o, bugs, onDish);
        CHECK(Near(seventh.x, boss.x) && Near(seventh.y, boss.y));
        // Nothing on the floor: his spot.
        Vec2 const none = RisePoint(boss, 0.f, {}, [](Vec2) { return false; });
        CHECK(Near(none.x, boss.x) && Near(none.y, boss.y));
    }

    // ---- TB3: the Duplicator's clock ------------------------------------------------------------------------------
    {
        DupRule const normal = BugRule(false);
        DupRule const heroic = BugRule(true);
        CHECK(normal.castMs == 3000 && normal.firstAfterMs == 9000 && normal.repeatMs == 0 && normal.capAlive == 8);
        CHECK(heroic.castMs == 2000 && heroic.firstAfterMs == 7000 && heroic.repeatMs == 7000);
        CHECK(heroic.capAlive == Tune::kBugSafetyCeiling);

        // Normal: one cast at 9 s, done at 12 s, never again.
        Sim n(normal);
        n.Run(8900, 1);
        CHECK(n.clock.starts == 0);
        n.Run(200, 1);
        CHECK(n.clock.starts == 1 && n.clock.casting);
        n.Run(3000, 1);
        CHECK(n.clock.copies == 1 && !n.clock.casting && n.clock.spent);
        n.Run(60000, 1);
        CHECK(n.clock.starts == 1 && n.clock.copies == 1);

        // Normal at the cap: the due cast waits, then starts once there is room.
        Sim c(normal);
        c.Run(20000, 8);
        CHECK(c.clock.starts == 0);
        c.Run(200, 7);
        CHECK(c.clock.starts == 1);

        // A stopped normal cast (a kick, a stun) is lost: spent, no copy, no retry.
        Sim s(normal);
        s.Run(9100, 1, true);
        s.Run(200, 1, true);
        CHECK(s.clock.starts == 1 && s.clock.copies == 0 && s.clock.spent);
        s.Run(30000, 1);
        CHECK(s.clock.starts == 1);

        // Heroic: every 7 s of life, 2 s bars: starts at 7, 14, 21, 28 s.
        Sim h(heroic);
        h.Run(30100, 1);
        CHECK(h.clock.starts == 4 && h.clock.copies == 4);
        // Heroic, every cast stopped: the next comes at the next due time (no faster than half a period).
        Sim hs(heroic);
        hs.Run(29000, 1, true);
        CHECK(hs.clock.starts == 4 && hs.clock.copies == 0);
        // Heroic has no design cap: 63 alive still duplicates; only the technical ceiling (DQ3) holds a due cast.
        Sim hc(heroic);
        hc.Run(8000, 63);
        CHECK(hc.clock.starts == 1);
        Sim hceil(heroic);
        hceil.Run(8000, 64);
        CHECK(hceil.clock.starts == 0);

        // R-1-A m1: the cap counts the bars in flight: 7 alive and another bug casting, a due cast waits.
        DupClock w = StartClock(normal);
        w.lifeMs = 9000;
        CHECK(DueToStart(w, normal, 7) && !DueToStart(w, normal, 7, 1) && DueToStart(w, normal, 6, 1));
        // And a completed bar at the cap makes no copy (the last guard).
        CHECK(CopyFits(normal, 7) && !CopyFits(normal, 8) && CopyFits(DupRule{}, 500));

        // DQ1: a normal copy never duplicates; a heroic copy (and the hard mode's repeating bombs) runs its own clock.
        DupClock const nCopy = CopyClock(normal);
        CHECK(nCopy.spent && nCopy.lifeMs == 0);
        Sim nc(normal);
        nc.clock = nCopy;
        nc.Run(60000, 1);
        CHECK(nc.clock.starts == 0 && nc.clock.copies == 0);
        DupClock const hCopy = CopyClock(heroic);
        CHECK(!hCopy.spent && hCopy.nextDueMs == heroic.firstAfterMs);
        DupRule bombs;
        bombs.castMs = 2000;
        bombs.firstAfterMs = 10000;
        bombs.repeatMs = 10000;
        CHECK(!CopyClock(bombs).spent);

        // A refused start retries in a second, the cast is not lost.
        DupClock r = StartClock(normal);
        r.lifeMs = 9000;
        CHECK(DueToStart(r, normal, 1));
        OnCastRefused(r);
        CHECK(!DueToStart(r, normal, 1) && r.nextDueMs == 10000);
        r.lifeMs = 10000;
        CHECK(DueToStart(r, normal, 1));

        // RB-17 on a late repeat: the next due time is at least half a period away.
        DupClock late = StartClock(heroic);
        late.lifeMs = 30000;        // started 23 s late (stunned a long time)
        OnCastStarted(late);
        OnCastEnded(late, heroic, true);
        CHECK(late.nextDueMs == 30000 + heroic.repeatMs / 2);

        // Completion: the bar's own aura, or the remaining time fitting the time since it was last seen.
        CHECK(CastCompleted(true, 3000, 0));
        CHECK(CastCompleted(false, 100, 0));
        CHECK(CastCompleted(false, 200, 50));
        CHECK(!CastCompleted(false, 1500, 100));        // a kick halfway
        CHECK(!CastCompleted(false, 400, 100));
        // R-1-A m2: a bar that applies its own aura is judged by the aura alone: a kick 0.2 s before the end (no
        // aura) is a stop, not a copy; the aura still means done.
        CHECK(CastCompleted(false, 200, 50) && !CastCompleted(false, 200, 50, true));
        CHECK(!CastCompleted(false, 0, 500, true) && CastCompleted(true, 3000, 0, true));
    }

    // ---- the timeline: no beat starves another (RB-17) ------------------------------------------------------------
    CHECK(NextDue(15000, 15000, 15000) == 30000);
    CHECK(NextDue(15000, 15000, 40000) == 47500);       // far behind: half a period from now
    CHECK(NextDue(0, 45000, 2000) == 45000);

    // ---- TB6: the Rubber Band's steps -----------------------------------------------------------------------------
    {
        BandProgress p;
        CHECK(DueBandStep(p, 1999) == BandStep::None);
        CHECK(DueBandStep(p, 2000) == BandStep::Save);
        MarkBandStep(p, BandStep::Save);
        CHECK(DueBandStep(p, 3499) == BandStep::None);
        CHECK(DueBandStep(p, 3500) == BandStep::SpikeTwo);
        MarkBandStep(p, BandStep::SpikeTwo);
        // The second spike lands at 5 s; the snap waits until after it (RB-29).
        CHECK(DueBandStep(p, 5000) == BandStep::None);
        CHECK(DueBandStep(p, Tune::kBandSnapAtMs) == BandStep::Snap);
        MarkBandStep(p, BandStep::Snap);
        CHECK(DueBandStep(p, 99999) == BandStep::Done);
        // One step per call even when late: a tick of 10 s still walks every step in order.
        BandProgress late;
        std::vector<BandStep> seen;
        for (int i = 0; i < 4; ++i)
        {
            BandStep const s = DueBandStep(late, 10000);
            seen.push_back(s);
            MarkBandStep(late, s);
        }
        CHECK(seen.size() == 4 && seen[0] == BandStep::Save && seen[1] == BandStep::SpikeTwo
            && seen[2] == BandStep::Snap && seen[3] == BandStep::Done);
        // The save point's burst lands at the snap; the spikes are 1.5 s apart and both resolve before it.
        CHECK(Tune::kBandSaveMs + Tune::kBandBurstWarnMs == Tune::kBandSnapAtMs);
        CHECK(Tune::kBandSpikeOneMs + Tune::kBandSpikeWarnMs == Tune::kBandSpikeTwoMs);
    }

    // ---- every timed beat fires over a simulated fight (normal 120 s, heroic 120 s) -------------------------------
    for (bool heroic : { false, true })
    {
        std::uint32_t lagAt = heroic ? Tune::kBandFirstMs : Tune::kLagFirstMs;
        std::uint32_t bugAt = Tune::kBugFirstMs.Get(heroic);
        std::uint32_t patchAt = Tune::kPatchFirstMs.Get(heroic);
        std::uint32_t netAt = Tune::kNetFirstMs;
        std::uint32_t lags = 0;
        std::uint32_t bugs = 0;
        std::uint32_t patches = 0;
        std::uint32_t nets = 0;
        std::uint32_t castLeft = 0;
        for (std::uint32_t now = 0; now <= 120000; now += 100)
        {
            if (now >= lagAt)
            {
                lagAt = NextDue(lagAt, heroic ? Tune::kBandEveryMs : Tune::kLagEveryMs, now);
                ++lags;
            }
            if (now >= bugAt)
            {
                bugAt = NextDue(bugAt, Tune::kBugEveryMs.Get(heroic), now);
                ++bugs;
            }
            if (heroic && now >= netAt)
            {
                netAt = NextDue(netAt, Tune::kNetEveryMs, now);
                ++nets;
            }
            castLeft = castLeft > 100 ? castLeft - 100 : 0;
            if (!castLeft && now >= patchAt)
            {
                patchAt = NextDue(patchAt, Tune::kPatchEveryMs.Get(heroic), now);
                castLeft = Tune::kPatchCastMs.Get(heroic);
                ++patches;
            }
        }
        CHECK(lags == 8);                       // 8, 23, ..., 113 s
        CHECK(bugs == (heroic ? 15u : 12u));    // every 10 s from 10 s / every 8 s from 8 s
        CHECK(patches == (heroic ? 3u : 2u));   // 45, 90 / 35, 70, 105
        CHECK(nets == (heroic ? 5u : 0u));      // 20, 45, 70, 95, 120
    }

    return Report("gnomer_techbot_test");
}
