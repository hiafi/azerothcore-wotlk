// Host tests for KrastinovLogic.h (S6: Doctor Theolen Krastinov (11261)): the patient pick, the operation state
// machine (interrupt in the pause wasted, 3 or 4 to escape, 3 or 2 to succeed, the 25 s cap, the heroic claws), the
// graft order, the timing rules, the detention lesson's cuts and the room geometry.
#include "KrastinovLogic.h"
#include "check.h"
#include <cmath>

using namespace ScholomanceRework;
using namespace ScholoKrastinov;

namespace
{
    // Runs `op` for `ms` in 100 ms ticks; counts what the steps asked for.
    struct Run
    {
        std::uint32_t seats = 0;
        std::uint32_t cutsStarted = 0;
        std::uint32_t cutsLanded = 0;
        bool ended = false;
    };

    Run Advance(Operation& op, std::uint32_t ms, float r = 0.f, bool confirmSeat = true)
    {
        Run run;
        for (std::uint32_t t = 0; t < ms && !op.Done(); t += 100)
        {
            OpStep const step = op.Update(100, r);
            if (step.seat)
            {
                ++run.seats;
                if (confirmSeat)
                    op.Seated();
            }
            run.cutsStarted += step.startCut ? 1 : 0;
            run.cutsLanded += step.cutLanded ? 1 : 0;
            run.ended = run.ended || step.ended;
        }
        return run;
    }

    // Seats the patient and skips the walk: the operation is in its first pause.
    void ToFirstPause(Operation& op)
    {
        Advance(op, kHookMs);
        CHECK(op.Phase() == OpPhase::Approach);
        op.Arrived();
        CHECK(op.Phase() == OpPhase::Pause);
    }

    // Advances to the next cut's cast (from a pause).
    void ToCast(Operation& op)
    {
        for (int i = 0; i < 100 && op.Phase() == OpPhase::Pause; ++i)
            op.Update(100, 0.f);
    }

    // Advances `ms` (at most) and stops early on the end; returns the landed count of that stretch.
    std::uint32_t Ms(Operation& op, std::uint32_t ms)
    {
        return Advance(op, ms).cutsLanded;
    }
}

int main()
{
    // ---- ids ----------------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(SPELL_KR_HOOK == 206225u);
    CHECK(SPELL_KR_WRENCH_FREE == 206227u);
    CHECK(SPELL_KR_INCISION == 206229u);
    CHECK(SPELL_KR_SAW_DESCENDING == 206231u);
    CHECK(SPELL_KR_CLAW_AT_STRAPS == 206241u);
    CHECK(kSpellSlice.Contains(SPELL_KR_CLAW_AT_STRAPS));
    CHECK(NPC_SC_WORK_BENCH == 300538u);
    CHECK(NPC_SC_FAILED_PATIENT == 300539u);
    CHECK(NPC_SC_EXAMINER_KRASTINOV == 300549u);

    // ---- the room -------------------------------------------------------------------------------------------------
    CHECK(KrastinovArena().Contains(kKrastinovSpawn.XY(), kKrastinovSpawn.z));
    CHECK(ArenaFor(BOSS_KRASTINOV).Contains(kKrastinovSpawn.XY(), kKrastinovSpawn.z));
    // The bench sits 30.1 yd from the leash circle's center: off the circle, on the fight arena (the apse box).
    CHECK(!KrastinovArena().Contains(kWorkBenchGo.XY(), kWorkBenchGo.z));
    CHECK(KrastinovFightArena().Contains(kWorkBenchGo.XY(), kWorkBenchGo.z));
    CHECK(KrastinovFightArena().Contains(kOperatingSpot.XY(), kOperatingSpot.z));
    CHECK(KrastinovFightArena().Contains(kKrastinovSpawn.XY(), kKrastinovSpawn.z));
    CHECK(KrastinovFightArena().Contains(kFailedPatientRise.XY(), kFailedPatientRise.z));
    // The operating spot is in his apse (x 179-186, y -100 to -93), 2-3 yd in front of the bench.
    CHECK(kOperatingSpot.x > 179.f && kOperatingSpot.x < 186.f);
    CHECK(kOperatingSpot.y > -100.f && kOperatingSpot.y < -93.f);
    float const benchToSpot = DungeonKit::Distance(kWorkBenchGo.XY(), kOperatingSpot.XY());
    CHECK(benchToSpot > 2.f && benchToSpot < 3.f);
    // The Failed Patients rise about 20 yd from the bench (the south alcove).
    float const riseToBench = DungeonKit::Distance(kWorkBenchGo.XY(), kFailedPatientRise.XY());
    CHECK(riseToBench > 19.f && riseToBench < 24.f);
    // The fight arena stays clear of the gate (the room's gate is the instance's, outside the arena).
    CHECK(!KrastinovFightArena().Contains(Vec2{ 181.2f, -29.1f }, 88.9f));
    // The eject spot (2 yd forward and 2 yd left of the bench facing +y, i.e. toward -x) is on the arena and in the
    // apse.
    {
        float const o = kWorkBenchGo.o;
        Vec2 const exitAt{ kWorkBenchGo.x + kBenchExitForward * std::cos(o) - kBenchExitLeft * std::sin(o),
            kWorkBenchGo.y + kBenchExitForward * std::sin(o) + kBenchExitLeft * std::cos(o) };
        CHECK(KrastinovFightArena().Contains(exitAt, 85.3f));
        CHECK(exitAt.x > 179.f && exitAt.x < 186.f && exitAt.y > -100.f && exitAt.y < -93.f);
    }

    // ---- KR1 the patient pick ---------------------------------------------------------------------------------------
    {
        std::vector<PatientCandidate> group = {
            { 1, true, true, true, false, false },      // the tank (his victim)
            { 2, true, false, false, true, false },     // the healer
            { 3, true, false, false, false, false },    // a DPS
            { 4, true, false, false, false, false },    // a DPS
        };
        // Normal: only DPS.
        for (float r : { 0.f, 0.3f, 0.6f, 0.99f })
        {
            std::optional<std::uint64_t> const p = PickPatient(group, false, r);
            CHECK(p && (*p == 3 || *p == 4));
        }
        CHECK(*PickPatient(group, false, 0.f) == 3);
        CHECK(*PickPatient(group, false, 0.99f) == 4);
        // Heroic: anyone but the tank, the healer included.
        bool healerSeen = false;
        for (float r : { 0.f, 0.34f, 0.67f, 0.99f })
        {
            std::optional<std::uint64_t> const p = PickPatient(group, true, r);
            CHECK(p && *p != 1);
            healerSeen = healerSeen || (p && *p == 2);
        }
        CHECK(healerSeen);
        // Dead or unavailable players are never picked.
        group[2].alive = false;
        group[3].unavailable = true;
        CHECK(*PickPatient(group, false, 0.5f) == 2);       // normal fallback: the healer
        // A tank-spec off-tank who is not his victim is never picked on heroic while someone else is there.
        std::vector<PatientCandidate> offTank = { { 1, true, true, true }, { 5, true, false, true }, { 6, true } };
        for (float r : { 0.f, 0.99f })
            CHECK(*PickPatient(offTank, true, r) == 6);
        // Only the tank: nobody.
        std::vector<PatientCandidate> solo = { { 1, true, true, true } };
        CHECK(!PickPatient(solo, false, 0.5f));
        CHECK(!PickPatient(solo, true, 0.5f));
        // Only the tank and an off-tank: the off-tank as the last fallback.
        std::vector<PatientCandidate> const tanks = { offTank[0], offTank[1] };
        CHECK(*PickPatient(tanks, false, 0.5f) == 5);
        CHECK(*PickPatient(tanks, true, 0.5f) == 5);
    }

    // ---- KR1-KR5 the boss operation ---------------------------------------------------------------------------------
    // Rules.
    {
        OperationRules const n = BossOperationRules(false, false);
        OperationRules const h = BossOperationRules(true, false);
        OperationRules const eyes = BossOperationRules(false, true);
        CHECK(n.interruptsToEscape == 3 && n.cutsToSucceed == 3 && n.capMs == 25000 && n.maxCuts == 0);
        CHECK(h.interruptsToEscape == 3 && h.cutsToSucceed == 2);
        CHECK(eyes.interruptsToEscape == 4);
        CHECK(n.castMs == 1500 && n.pauseMinMs == 2000 && n.pauseMaxMs == 3000 && n.wrenchCooldownMs == 3000);
        // The design check (SC KR3): even after an interrupt at the very start of a cast, the next cast's window ends
        // at least 0.5 s after the cooldown is back.
        CHECK(n.pauseMinMs + n.castMs >= n.wrenchCooldownMs + 500);
    }
    // The hook: not seated, Wrench Free does nothing; the seat comes after 1 s.
    {
        Operation op;
        CHECK(!op.Active());
        CHECK(op.WrenchFree(0.f) == WrenchResult::NotSeated);
        op.Start(BossOperationRules(false, false));
        CHECK(op.Phase() == OpPhase::Seating);
        CHECK(op.WrenchFree(0.f) == WrenchResult::NotSeated);
        Run const r = Advance(op, 900, 0.f, false);
        CHECK(r.seats == 0);
        CHECK(op.Update(100, 0.f).seat);
        CHECK(op.Phase() == OpPhase::Seating);                  // until the glue confirms
        CHECK(op.Update(100, 0.f).seat);                        // asked again each tick
        op.Seated();
        CHECK(op.Phase() == OpPhase::Approach);
        CHECK(op.IsSeated());
        // Wrench Free while he walks: wasted, and on cooldown.
        CHECK(op.WrenchFree(0.f) == WrenchResult::Wasted);
        CHECK(op.WrenchFree(0.f) == WrenchResult::OnCooldown);
        CHECK(op.WastedPresses() == 1);
        // The walk times out after 6 s: the first pause, then the first cut.
        Advance(op, kApproachTimeoutMs);
        CHECK(op.Phase() == OpPhase::Pause || op.Phase() == OpPhase::Casting);
    }
    // A perfect escape on normal: 3 interrupts, each in a cast.
    {
        Operation op;
        op.Start(BossOperationRules(false, false));
        ToFirstPause(op);
        CHECK(op.StrapsLeft() == 3);
        for (std::uint32_t i = 0; i < 3; ++i)
        {
            ToCast(op);
            CHECK(op.Cutting());
            // The perfect press: the first moment the cooldown allows (0.5 s into this bar after a 2.5 s pause).
            while (op.Cutting() && op.WrenchCooldownMs() > 0)
                op.Update(100, 0.5f);
            CHECK(op.Cutting());
            CHECK(op.PhaseLeftMs() >= 500);                     // still at least 0.5 s of the bar left
            WrenchResult const res = op.WrenchFree(0.5f);
            CHECK(res == (i < 2 ? WrenchResult::Interrupted : WrenchResult::Escaped));
            if (i < 2)
            {
                CHECK(op.Phase() == OpPhase::Pause);
                CHECK(op.PhaseLeftMs() == 2500);                // r 0.5: the middle of 2-3 s
                CHECK(op.StrapsLeft() == 2 - i);
            }
        }
        CHECK(op.Done());
        CHECK(op.Outcome() == OpOutcome::Escape);
        CHECK(op.Landed() == 0);
        CHECK(op.TotalInterrupts() == 3);
    }
    // Wrench Free in the pause is wasted and costs the next cut: the cooldown is still running when it comes down.
    {
        Operation op;
        op.Start(BossOperationRules(false, false));
        ToFirstPause(op);
        CHECK(op.WrenchFree(0.f) == WrenchResult::Wasted);      // in the 0.5 s first-cut delay
        ToCast(op);
        CHECK(op.Cutting());
        CHECK(op.WrenchFree(0.f) == WrenchResult::OnCooldown);  // 0.5 s later: still 2.5 s to go
        CHECK(Ms(op, kIncisionCastMs) == 1);                    // the cut lands
        CHECK(op.Landed() == 1);
        CHECK(op.Phase() == OpPhase::Pause);
    }
    // Normal success at 3 landed cuts; heroic at 2.
    {
        Operation op;
        op.Start(BossOperationRules(false, false));
        ToFirstPause(op);
        Run const r = Advance(op, 20000);
        CHECK(r.cutsLanded == 3);
        CHECK(r.cutsStarted == 3);
        CHECK(op.Outcome() == OpOutcome::Success);
        CHECK(r.ended);

        Operation hop;
        hop.Start(BossOperationRules(true, false));
        ToFirstPause(hop);
        Run const hr = Advance(hop, 20000);
        CHECK(hr.cutsLanded == 2);
        CHECK(hop.Outcome() == OpOutcome::Success);
    }
    // Mixed: 2 interrupts and 3 landed on normal is a success (the cuts finish first).
    {
        Operation op;
        op.Start(BossOperationRules(false, false));
        ToFirstPause(op);
        ToCast(op);
        CHECK(op.WrenchFree(0.f) == WrenchResult::Interrupted);
        ToCast(op);
        Ms(op, kIncisionCastMs);                                 // cooldown 3 s > pause 2 s: this one lands
        CHECK(op.Landed() == 1);
        ToCast(op);
        CHECK(op.WrenchFree(0.f) == WrenchResult::Interrupted);
        Advance(op, 20000);
        CHECK(op.Outcome() == OpOutcome::Success);
        CHECK(op.Landed() == 3);
        CHECK(op.TotalInterrupts() == 2);
    }
    // After the eyes: 4 interrupts to escape.
    {
        Operation op;
        op.Start(BossOperationRules(false, true));
        ToFirstPause(op);
        WrenchResult last = WrenchResult::NotSeated;
        for (int i = 0; i < 4; ++i)
        {
            ToCast(op);
            Advance(op, 1000);                                  // let the cooldown run out before each cast
            if (!op.Cutting())
                ToCast(op);
            last = op.WrenchFree(0.99f);
            Advance(op, 100);
        }
        CHECK(last == WrenchResult::Escaped);
        CHECK(op.Outcome() == OpOutcome::Escape);
    }
    // The 25 s cap: a success even with no cut landed (nothing interrupts, nothing lands: he never got there).
    {
        Operation op;
        OperationRules rules = BossOperationRules(false, false);
        rules.firstCutDelayMs = 60000;                          // he never cuts (a stuck walk, a test)
        op.Start(rules);
        Advance(op, kHookMs);
        op.Arrived();
        Run const r = Advance(op, 24900);
        CHECK(!r.ended);
        CHECK(op.Active());
        Run const r2 = Advance(op, 200);
        CHECK(r2.ended);
        CHECK(op.Outcome() == OpOutcome::Success);
        CHECK(op.SeatedMs() >= kOperationCapMs);
    }
    // KR7 heroic claws: an interrupt undone; none to undo is a no-op.
    {
        Operation op;
        op.Start(BossOperationRules(true, false));
        ToFirstPause(op);
        CHECK(!op.Claw());
        ToCast(op);
        CHECK(op.WrenchFree(0.f) == WrenchResult::Interrupted);
        CHECK(op.Interrupts() == 1);
        CHECK(op.StrapsLeft() == 2);
        CHECK(op.Claw());
        CHECK(op.Interrupts() == 0);
        CHECK(op.StrapsLeft() == 3);
        CHECK(op.TotalInterrupts() == 1);
        CHECK(op.Claws() == 1);
        // Clawed back, the escape needs 3 more.
        for (int i = 0; i < 2; ++i)
        {
            ToCast(op);
            Advance(op, 1000);
            if (!op.Cutting())
                ToCast(op);
            CHECK(op.WrenchFree(0.f) == WrenchResult::Interrupted);
        }
        CHECK(op.Active());
    }
    // ClawTicker: one claw per 3 s at the bench; stepping away restarts it.
    {
        ClawTicker t;
        CHECK(t.Update(2900, true) == 0);
        CHECK(t.Update(100, true) == 1);
        CHECK(t.Update(2000, true) == 0);
        CHECK(t.Update(500, false) == 0);
        CHECK(t.Update(2999, true) == 0);
        CHECK(t.Update(1, true) == 1);
    }
    // Abort: any active phase ends with Aborted; a second abort or an idle one does nothing.
    {
        Operation op;
        op.Abort();
        CHECK(op.Outcome() == OpOutcome::None);
        op.Start(BossOperationRules(false, false));
        op.Abort();
        CHECK(op.Outcome() == OpOutcome::Aborted);
        CHECK(op.Done());
        CHECK(op.WrenchFree(0.f) == WrenchResult::NotSeated);
    }

    // ---- KR6 the graft order -------------------------------------------------------------------------------------
    CHECK(GraftFor(1) == Graft::Hands);
    CHECK(GraftFor(2) == Graft::Eyes);
    CHECK(GraftFor(3) == Graft::Heart);
    CHECK(GraftFor(4) == Graft::Heart);
    CHECK(GraftFor(9) == Graft::Heart);

    // ---- numbers (SC KR rows) ------------------------------------------------------------------------------------
    CHECK(kIncisionPct(false) == 20.f && kIncisionPct(true) == 30.f);
    CHECK(kBackhandPct(false) == 40.f && kBackhandPct(true) == 55.f);
    CHECK(kKillingFrenzyPct(false) == 25 && kKillingFrenzyPct(true) == 40);
    CHECK(kHeartHealPct(false) == 10.f && kHeartHealPct(true) == 15.f);
    CHECK(kFailedPatientsPerOperation(false) == 2 && kFailedPatientsPerOperation(true) == 3);
    CHECK(kFailedPatientHealth(false) == 6000 && kFailedPatientHealth(true) == 9000);
    CHECK(kScalpelStabPct == 5.f && kStitchedWoundPct == 15);
    CHECK(kExaminerHealth == 80000);

    // ---- KR1 / KR8 timing -------------------------------------------------------------------------------------------
    CHECK(NextOperationAt(15000, 30000) == 45000);              // operations at 15, 45, 75 s
    CHECK(NextOperationAt(15000, 42000) == 47000);              // a long one: 5 s after it ended
    CHECK(BackhandMayStart(10000, 10000, false, 15000));        // the first at 10 s, 5 s before the hook
    CHECK(!BackhandMayStart(13000, 10000, false, 15000));       // too close to the operation: it waits
    CHECK(!BackhandMayStart(20000, 10000, true, 45000));        // never during an operation
    CHECK(!BackhandMayStart(9999, 10000, false, 45000));

    // ---- detention (SC 2966) ---------------------------------------------------------------------------------------
    {
        OperationRules const rules = LessonOperationRules();
        CHECK(rules.interruptsToEscape == 0 && rules.cutsToSucceed == 0 && rules.maxCuts == 3 && rules.capMs == 0);
        CHECK(rules.approachTimeoutMs == 0);
        // Nobody interrupts: 3 cuts land, then Finished, well inside the 15 s lesson.
        Operation op;
        op.Start(rules);
        Run const r = Advance(op, kLessonMs, 0.99f);
        CHECK(r.seats == 1);
        CHECK(r.cutsLanded == 3);
        CHECK(op.Outcome() == OpOutcome::Finished);
        CHECK(op.ElapsedMs() < kLessonMs);
        CHECK(!LessonPassed(3, false));
        // Interrupts do not free the student: they count as cuts; 2 interrupts and 1 landed is a normal pass, a
        // heroic fail.
        Operation op2;
        op2.Start(rules);
        Advance(op2, kLessonSeatDelayMs);
        CHECK(op2.Phase() == OpPhase::Pause);
        CHECK(op2.StrapsLeft() == 3);
        ToCast(op2);
        CHECK(op2.WrenchFree(0.f) == WrenchResult::Interrupted);
        CHECK(op2.StrapsLeft() == 2);
        ToCast(op2);
        Ms(op2, kIncisionCastMs);                                // cooldown: this one lands
        ToCast(op2);
        CHECK(op2.WrenchFree(0.f) == WrenchResult::Interrupted);
        CHECK(op2.Outcome() == OpOutcome::Finished);
        CHECK(op2.Landed() == 1);
        CHECK(LessonPassed(op2.Landed(), false));
        CHECK(!LessonPassed(op2.Landed(), true));
        CHECK(LessonPassed(0, true));
        // The worst case (every pause at its longest) still ends inside 15 s.
        Operation op3;
        op3.Start(rules);
        Advance(op3, kLessonMs, 0.9999f);
        CHECK(op3.Done());
    }

    return Report("scholo_krastinov_test");
}
