/*
 * mod-dungeon-bosses, Scholomance S6: Doctor Theolen Krastinov (11261), the pure, host-testable part (no engine
 * headers). Build spec SC 1703-1764 (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows KR and 3.5 row S6.
 * Tested by tests/scholo_krastinov_test.cpp.
 *
 *   Spells             the WP's ids, inside kSpellsKrastinov (206225-206249), declared in apps/dbc-tools
 *                      source/npcs/scholomance/doctor_theolen_krastinov.py
 *   Tuning             NH<> constants: one number per difficulty, straight from the build spec (and section 7 #24)
 *   PickPatient        KR1 who goes on the bench: normal a random DPS, heroic anyone but the tank (healer included)
 *   Operation          KR1-KR5 the operation on the Work Bench: the hook, his walk, the cuts (1.5 s cast, 2-3 s pause),
 *                      Wrench Free (interrupts a cut in its cast, wasted in a pause, 3 s cooldown), the escape (3, 4
 *                      after the eyes), the success (3 landed, heroic 2, or the 25 s cap) and the heroic claws; the
 *                      same machine runs the detention lesson (three cuts, no escape, no success)
 *   GraftFor           KR6 the graft order: hands, eyes, then a heart for every later success
 *   ClawTicker         KR7 heroic: a Failed Patient at the bench undoes one interrupt every 3 s (ClawsWork: not
 *                      while crowd-controlled)
 *   NextOperationAt    KR1 first at 15 s, every 30 s start to start, never sooner than 5 s after the last one ended
 *                      (a refused seat: he picks another patient at once)
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_KRASTINOV_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_KRASTINOV_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include "SoloLessonLogic.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ScholoKrastinov
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsKrastinov;

    enum KrastinovSpells : std::uint32_t
    {
        SPELL_KR_HOOK               = kSpellSlice.first + 0,    // 206225 KR1 the 1 s hook cast on the patient (chain)
        SPELL_KR_STRAPPED_DOWN      = kSpellSlice.first + 1,    // 206226 KR1 the bench's aura: stacks = straps left
        SPELL_KR_WRENCH_FREE        = kSpellSlice.first + 2,    // 206227 KR2 the bench's button (vehicle spell)
        SPELL_KR_WRENCH_IMPACT      = kSpellSlice.first + 3,    // 206228 KR2 the jolt on the operator (look only)
        SPELL_KR_INCISION           = kSpellSlice.first + 4,    // 206229 KR3 his 1.5 s cast bar on the patient
        SPELL_KR_INCISION_HIT       = kSpellSlice.first + 5,    // 206230 KR3 a landed cut (the damage)
        SPELL_KR_SAW_DESCENDING     = kSpellSlice.first + 6,    // 206231 KR3 the bench's 1.5 s aura: the cut window
        SPELL_KR_SCALPEL_STAB       = kSpellSlice.first + 7,    // 206232 KR4 the escape: 5% of his health
        SPELL_KR_STITCHED_WOUND     = kSpellSlice.first + 8,    // 206233 KR5 the patient: max health -15% per stack
        SPELL_KR_KILLING_FRENZY     = kSpellSlice.first + 9,    // 206234 KR6 hands: attack speed +25% / +40%
        SPELL_KR_GRAFTED_EYES       = kSpellSlice.first + 10,   // 206235 KR6 eyes: the look (escapes need 4)
        SPELL_KR_GRAFTED_HEART_HEAL = kSpellSlice.first + 11,   // 206236 KR6 heart: heals 10% / 15% of his health
        SPELL_KR_GRAFTED_HEART      = kSpellSlice.first + 12,   // 206237 KR6 heart: the look, a stack per heart
        SPELL_KR_BACKHAND           = kSpellSlice.first + 13,   // 206238 KR8 the 2 s tank buster
        SPELL_KR_BUTCHERS_REND      = kSpellSlice.first + 14,   // 206239 KR9 the stacking bleed on the tank
        SPELL_KR_INFECTED_CLAWS     = kSpellSlice.first + 15,   // 206240 KR7 the Failed Patients' light bleed
        SPELL_KR_CLAW_AT_STRAPS     = kSpellSlice.first + 16,   // 206241 KR7 heroic: a claw undoes an interrupt (look)
        // 206242-206249 spare
    };
    static_assert(SPELL_KR_CLAW_AT_STRAPS <= kSpellSlice.last, "Krastinov's spells must stay in his slice");

    // The Work Bench (VehicleId 6): one seat, seat index 0 (VehicleSeat 441: control and cast, no exit by the player).
    inline constexpr std::int8_t kBenchSeat = 0;
    inline constexpr std::uint32_t kBenchVehicleId = 6;
    inline constexpr std::uint32_t kBenchVehicleSeatEntry = 441;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC 1712-1736; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // KR1 Operation
    inline constexpr std::uint32_t kOperationFirstMs = 15000;
    inline constexpr std::uint32_t kOperationEveryMs = 30000;          // start to start
    inline constexpr std::uint32_t kOperationMinGapMs = 5000;          // after the last one ended
    inline constexpr std::uint32_t kHookMs = 1000;                     // the hook's cast bar, then the seat
    inline constexpr std::uint32_t kApproachTimeoutMs = 6000;          // a blocked walk: he cuts from where he is
    inline constexpr std::uint32_t kFirstCutDelayMs = 500;             // after he reached the bench
    inline constexpr std::uint32_t kOperationCapMs = 25000;            // from the seat: then a success
    inline constexpr std::uint32_t kSeatGiveUpMs = 3000;               // a seat refused this long after it was due

    // KR2 Wrench Free / KR3 Incision
    inline constexpr std::uint32_t kWrenchFreeCooldownMs = 3000;
    inline constexpr std::uint32_t kIncisionCastMs = 1500;
    inline constexpr std::uint32_t kIncisionPauseMinMs = 2000;
    inline constexpr std::uint32_t kIncisionPauseMaxMs = 3000;
    inline constexpr NH<float> kIncisionPct{ 20.f, 30.f };             // Physical (a bleed cut: no armor), no Weakened
    inline constexpr std::uint32_t kInterruptsToEscape = 3;
    inline constexpr std::uint32_t kInterruptsToEscapeWithEyes = 4;    // KR6 the eyes graft
    inline constexpr NH<std::uint32_t> kCutsToSucceed{ 3, 2 };

    // KR4 Escape
    inline constexpr float kScalpelStabPct = 5.f;                      // of his maximum health

    // KR5 Success / KR6 Grafts
    inline constexpr std::int32_t kStitchedWoundPct = 15;              // max health -15% per stack, the fight
    inline constexpr NH<std::int32_t> kKillingFrenzyPct{ 25, 40 };     // attack speed
    inline constexpr NH<float> kHeartHealPct{ 10.f, 15.f };            // of his maximum health

    // KR7 Failed Patients (the waiting room)
    inline constexpr NH<std::uint32_t> kFailedPatientsPerOperation{ 2, 3 };
    inline constexpr NH<std::uint32_t> kFailedPatientHealth{ 6000, 9000 };
    inline constexpr float kFailedPatientSpread = 2.5f;                // yd around the rise spot
    inline constexpr std::uint32_t kClawEveryMs = 3000;                // heroic, at the bench
    inline constexpr float kClawReach = 5.f;                           // yd from the bench
    inline constexpr float kInfectedClawsPct = 1.f;                    // per 2 s tick, 10 s (section 7 #24)
    inline constexpr std::uint32_t kInfectedClawsEveryMinMs = 6000;
    inline constexpr std::uint32_t kInfectedClawsEveryMaxMs = 9000;
    // They shamble: about 6 s from the rise spot to the bench (21.7 yd at 3.6 yd/s). Their chase runs, so the speed
    // is creature_template speed_run (0.514286 x 7 yd/s), not a walk (apps/dbc-tools doctor_theolen_krastinov.py).
    inline constexpr float kFailedPatientYdPerSec = 3.6f;
    // Orphan check: a Failed Patient whose summoner (him or his examiner) is gone despawns.
    inline constexpr std::uint32_t kFailedPatientOwnerCheckMs = 1000;

    // KR8 Backhand (tank buster): first at 10 s, then every 15 s; never during an operation
    inline constexpr std::uint32_t kBackhandFirstMs = 10000;
    inline constexpr std::uint32_t kBackhandEveryMs = 15000;
    inline constexpr std::uint32_t kBackhandCastMs = 2000;
    inline constexpr NH<float> kBackhandPct{ 40.f, 55.f };             // of the tank row, Physical (armor applies)
    inline constexpr std::uint32_t kBackhandAfterOperationMs = 3000;   // a due one waits this long after an operation
    inline constexpr std::uint32_t kBackhandOperationGuardMs = 2500;   // no Backhand this close before an operation
    inline constexpr std::uint32_t kBackhandRetryMs = 1000;            // a cast that did not start: try again
    // The spell's range (DT backhand_206238): far past melee, so a step back during the bar never dodges it.
    inline constexpr float kBackhandRangeYd = 40.f;

    // KR9 Butcher's Rend: stock timer 3-7 s, then 14-18 s; 2% of the tank row per stack per 3 s, 5 stacks, 15 s
    inline constexpr std::uint32_t kRendFirstMinMs = 3000;
    inline constexpr std::uint32_t kRendFirstMaxMs = 7000;
    inline constexpr std::uint32_t kRendEveryMinMs = 14000;
    inline constexpr std::uint32_t kRendEveryMaxMs = 18000;
    inline constexpr float kRendPctPerStack = 2.f;
    inline constexpr std::uint32_t kRendMaxStacks = 5;

    // Detention (SC 2966): the empty bench straps the student in and its saw makes 3 cuts; pass when at most 1 lands
    // (normal) or none (heroic). A landed cut is the lesson's failure hit (15% / 25% + Weakened).
    inline constexpr std::uint32_t kLessonCuts = 3;
    inline constexpr NH<std::uint32_t> kLessonAllowedLanded{ 1, 0 };
    inline constexpr std::uint32_t kLessonSeatDelayMs = 1000;          // after the landing (the teleport settles)
    inline constexpr std::uint32_t kLessonFirstCutDelayMs = 1000;
    // A student the bench could not seat (kSeatGiveUpMs after it was due) fails the lesson: one more failure than the
    // lesson allows (no hits: no cut came down).
    constexpr std::uint32_t RefusedSeatFailures(bool heroic) { return kLessonAllowedLanded(heroic) + 1; }
    // The three cuts with every pause at its longest end inside the 15 s lesson (12.5 s).
    static_assert(kLessonSeatDelayMs + kLessonFirstCutDelayMs + kLessonCuts * kIncisionCastMs
        + (kLessonCuts - 1) * kIncisionPauseMaxMs < ScholomanceRework::kLessonMs, "the saw must finish in the lesson");

    // Hard mode examiner (S13): the Graduate Examiner Krastinov, both mechanics at heroic values, 80,000 health.
    inline constexpr std::uint32_t kExaminerHealth = 80000;

    // `r` in [0, 1): a point of [min, max].
    constexpr std::uint32_t InRange(std::uint32_t min, std::uint32_t max, float r)
    {
        float const span = static_cast<float>(max - min);
        return min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 0.9999f) * span);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The room (handoff section 3.8, NAVMESH-REPORT section 6). His apse: x 179-186, y -100 to -93; the bench at its
    // back, facing the hall (+y).
    // ----------------------------------------------------------------------------------------------------------------

    // Where he stands to operate: in front of the bench, between it and the hall (2.7 yd from the bench).
    inline constexpr ScholomanceRework::Point3 kOperatingSpot{ 182.4f, -97.4f, 85.3f };
    // Where the patient lands on an eject: vehicle_seat_addon 441 with ExitParamValue 2 (an absolute spot; the engine
    // lifts it to the floor), 2 yd in front of the bench and 2 yd to its left. Not an offset (ExitParamValue 1): the
    // offset keeps the bench's z 85.2, under the 85.31 floor there, and the engine then drops the patient on the
    // bench's own spot; it also turns with the bench.
    inline constexpr ScholomanceRework::Point3 kBenchExit{ 180.5f, -98.1f, 85.4f };

    // His fight arena: ScholomanceRework::KrastinovArena(), the room's leash circle plus his apse (the bench, 30.1 yd
    // from the circle's center, his operating spot and the eject spot).
    inline DungeonKit::Arena KrastinovFightArena()
    {
        return ScholomanceRework::KrastinovArena();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // KR1 Who goes on the bench
    // ----------------------------------------------------------------------------------------------------------------

    struct PatientCandidate
    {
        std::uint64_t id = 0;
        bool alive = true;
        bool isVictim = false;      // his current victim: the tank
        bool tankSpec = false;
        bool healSpec = false;
        bool unavailable = false;   // already on a vehicle, being teleported, a game master
    };

    // Normal: a random DPS (never the tank; a healer, then anyone but his victim, only as fallbacks). Heroic: anyone
    // but the tank (the healer included). `r` in [0, 1). Nobody: nullopt (he skips the operation).
    inline std::optional<std::uint64_t> PickPatient(std::vector<PatientCandidate> const& all, bool heroic, float r)
    {
        auto pick = [r](std::vector<std::uint64_t> const& pool) -> std::optional<std::uint64_t>
        {
            if (pool.empty())
                return std::nullopt;
            std::size_t const i = std::min(pool.size() - 1,
                static_cast<std::size_t>(std::clamp(r, 0.f, 0.9999f) * static_cast<float>(pool.size())));
            return pool[i];
        };
        std::vector<std::uint64_t> dps;
        std::vector<std::uint64_t> healers;
        std::vector<std::uint64_t> notTank;
        std::vector<std::uint64_t> anyButVictim;
        for (PatientCandidate const& c : all)
        {
            if (!c.alive || c.unavailable || c.isVictim)
                continue;
            anyButVictim.push_back(c.id);
            if (c.tankSpec)
                continue;
            notTank.push_back(c.id);
            if (c.healSpec)
                healers.push_back(c.id);
            else
                dps.push_back(c.id);
        }
        if (heroic)
            return notTank.empty() ? pick(anyButVictim) : pick(notTank);
        if (!dps.empty())
            return pick(dps);
        if (!healers.empty())
            return pick(healers);
        return pick(anyButVictim);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // KR1-KR5 the operation (and the detention lesson)
    // ----------------------------------------------------------------------------------------------------------------

    struct OperationRules
    {
        std::uint32_t interruptsToEscape = kInterruptsToEscape;    // 0: interrupts never free the patient
        std::uint32_t cutsToSucceed = 3;                            // 0: no success by landed cuts
        std::uint32_t maxCuts = 0;                                  // > 0: ends (Finished) after this many cuts
        std::uint32_t capMs = kOperationCapMs;                      // 0: no cap; else a success at the cap
        std::uint32_t seatDelayMs = kHookMs;                        // the hook (boss) or the settle (lesson)
        std::uint32_t approachTimeoutMs = kApproachTimeoutMs;       // 0: no walk (the bench operates itself)
        std::uint32_t firstCutDelayMs = kFirstCutDelayMs;
        std::uint32_t castMs = kIncisionCastMs;
        std::uint32_t pauseMinMs = kIncisionPauseMinMs;
        std::uint32_t pauseMaxMs = kIncisionPauseMaxMs;
        std::uint32_t wrenchCooldownMs = kWrenchFreeCooldownMs;
    };

    // The boss's operation: 3 interrupts to escape (4 after the eyes graft), 3 landed cuts (heroic 2) to succeed, the
    // 25 s cap.
    inline OperationRules BossOperationRules(bool heroic, bool eyes)
    {
        OperationRules rules;
        rules.interruptsToEscape = eyes ? kInterruptsToEscapeWithEyes : kInterruptsToEscape;
        rules.cutsToSucceed = kCutsToSucceed(heroic);
        return rules;
    }

    // The detention lesson: the bench's saw makes 3 cuts, interrupted or landed; no escape, no success, no cap (the
    // lesson's own 15 s clock is the backstop). The verdict is the lesson's (kLessonAllowedLanded).
    inline OperationRules LessonOperationRules()
    {
        OperationRules rules;
        rules.interruptsToEscape = 0;
        rules.cutsToSucceed = 0;
        rules.maxCuts = kLessonCuts;
        rules.capMs = 0;
        rules.seatDelayMs = kLessonSeatDelayMs;
        rules.approachTimeoutMs = 0;
        rules.firstCutDelayMs = kLessonFirstCutDelayMs;
        return rules;
    }

    enum class OpPhase : std::uint8_t
    {
        Idle,       // never started
        Seating,    // the hook (boss) or the settle (lesson): the patient is not on the bench yet
        Approach,   // seated; he walks to the bench
        Pause,      // seated; between cuts (Wrench Free is wasted here)
        Casting,    // seated; a cut is coming down (Wrench Free interrupts it)
        Done,
    };

    enum class OpOutcome : std::uint8_t
    {
        None,
        Escape,     // KR4 enough interrupts
        Success,    // KR5 enough landed cuts, or the cap
        Finished,   // the lesson's cuts are all resolved
        Aborted,    // the patient was lost (died, left, ejected), a wipe, his death, a test
    };

    enum class WrenchResult : std::uint8_t
    {
        NotSeated,      // no operation on the bench (ignored)
        OnCooldown,     // pressed again inside the 3 s (ignored, the cooldown is not restarted)
        Wasted,         // a pause (or his walk): nothing to interrupt; the cooldown runs, so the next cut lands
        Interrupted,    // a cut stopped in its cast
        Escaped,        // the interrupt that broke the last strap
    };

    // What one Update asks of the engine glue.
    struct OpStep
    {
        bool seat = false;          // put the patient in the bench seat now, then call Seated() (or Abort())
        bool startCut = false;      // a cut starts: his cast bar, the bench's window aura
        bool cutLanded = false;     // the cut landed: the hit
        bool ended = false;         // the operation just ended (Outcome() says how)
    };

    class Operation
    {
    public:
        void Start(OperationRules const& rules)
        {
            *this = Operation();
            _rules = rules;
            _phase = OpPhase::Seating;
            _leftMs = rules.seatDelayMs;
        }

        // `r` in [0, 1): the next pause, when one starts this tick.
        OpStep Update(std::uint32_t diff, float r)
        {
            OpStep step;
            if (_phase == OpPhase::Idle || _phase == OpPhase::Done)
                return step;
            _elapsedMs += diff;
            _wrenchCooldownMs = _wrenchCooldownMs > diff ? _wrenchCooldownMs - diff : 0;

            if (_phase == OpPhase::Seating)
            {
                _leftMs = _leftMs > diff ? _leftMs - diff : 0;
                step.seat = _leftMs == 0;   // every tick until the glue confirms with Seated() (or aborts)
                return step;
            }

            _seatedMs += diff;
            if (_rules.capMs && _seatedMs >= _rules.capMs)
            {
                End(OpOutcome::Success);
                step.ended = true;
                return step;
            }

            switch (_phase)
            {
                case OpPhase::Approach:
                    if (_leftMs > diff)
                        _leftMs -= diff;
                    else
                        StartPause(_rules.firstCutDelayMs);     // the walk timed out: cut from where he is
                    break;
                case OpPhase::Pause:
                    if (_leftMs > diff)
                        _leftMs -= diff;
                    else
                    {
                        _phase = OpPhase::Casting;
                        _leftMs = _rules.castMs;
                        step.startCut = true;
                    }
                    break;
                case OpPhase::Casting:
                    if (_leftMs > diff)
                        _leftMs -= diff;
                    else
                    {
                        ++_landed;
                        ++_cuts;
                        step.cutLanded = true;
                        if (_rules.cutsToSucceed && _landed >= _rules.cutsToSucceed)
                        {
                            End(OpOutcome::Success);
                            step.ended = true;
                        }
                        else if (_rules.maxCuts && _cuts >= _rules.maxCuts)
                        {
                            End(OpOutcome::Finished);
                            step.ended = true;
                        }
                        else
                            StartPause(InRange(_rules.pauseMinMs, _rules.pauseMaxMs, r));
                    }
                    break;
                default:
                    break;
            }
            return step;
        }

        // The glue put the patient in the seat (after a `seat` step): the walk (boss) or the first pause (lesson).
        void Seated()
        {
            if (_phase != OpPhase::Seating)
                return;
            _seatedMs = 0;
            _wasSeated = true;
            if (_rules.approachTimeoutMs)
            {
                _phase = OpPhase::Approach;
                _leftMs = _rules.approachTimeoutMs;
            }
            else
                StartPause(_rules.firstCutDelayMs);
        }

        // He reached the bench (the boss's walk).
        void Arrived()
        {
            if (_phase == OpPhase::Approach)
                StartPause(_rules.firstCutDelayMs);
        }

        // KR2: the patient pressed Wrench Free. `r` in [0, 1): the pause after an interrupt.
        WrenchResult WrenchFree(float r)
        {
            if (!IsSeated())
                return WrenchResult::NotSeated;
            if (_wrenchCooldownMs)
                return WrenchResult::OnCooldown;
            _wrenchCooldownMs = _rules.wrenchCooldownMs;
            if (_phase != OpPhase::Casting)
            {
                ++_wasted;
                return WrenchResult::Wasted;
            }
            ++_interrupts;
            ++_totalInterrupts;
            ++_cuts;
            if (_rules.interruptsToEscape && _interrupts >= _rules.interruptsToEscape)
            {
                End(OpOutcome::Escape);
                return WrenchResult::Escaped;
            }
            if (_rules.maxCuts && _cuts >= _rules.maxCuts)
            {
                End(OpOutcome::Finished);
                return WrenchResult::Interrupted;
            }
            StartPause(InRange(_rules.pauseMinMs, _rules.pauseMaxMs, r));
            return WrenchResult::Interrupted;
        }

        // KR7 heroic: a Failed Patient at the bench pulls the straps tight again (one interrupt undone). False when
        // there was none to undo.
        bool Claw()
        {
            if (!IsSeated() || !_interrupts)
                return false;
            --_interrupts;
            ++_claws;
            return true;
        }

        void Abort()
        {
            if (Active())
                End(OpOutcome::Aborted);
        }

        OpPhase Phase() const { return _phase; }
        OpOutcome Outcome() const { return _outcome; }
        bool Active() const { return _phase != OpPhase::Idle && _phase != OpPhase::Done; }
        bool Done() const { return _phase == OpPhase::Done; }
        bool IsSeated() const
        {
            return _phase == OpPhase::Approach || _phase == OpPhase::Pause || _phase == OpPhase::Casting;
        }
        bool Cutting() const { return _phase == OpPhase::Casting; }
        bool WasSeated() const { return _wasSeated; }                     // the patient made it onto the bench
        std::uint32_t Interrupts() const { return _interrupts; }          // standing (claws take them back)
        std::uint32_t TotalInterrupts() const { return _totalInterrupts; }
        std::uint32_t Landed() const { return _landed; }
        std::uint32_t Cuts() const { return _cuts; }                      // landed + interrupted
        std::uint32_t WastedPresses() const { return _wasted; }
        std::uint32_t Claws() const { return _claws; }
        std::uint32_t ElapsedMs() const { return _elapsedMs; }
        std::uint32_t SeatedMs() const { return _seatedMs; }
        std::uint32_t PhaseLeftMs() const { return _leftMs; }
        std::uint32_t WrenchCooldownMs() const { return _wrenchCooldownMs; }
        OperationRules const& Rules() const { return _rules; }

        // The bench's Strapped Down stacks: straps left (boss) or cuts left (lesson).
        std::uint32_t StrapsLeft() const
        {
            if (_rules.interruptsToEscape)
                return _rules.interruptsToEscape > _interrupts ? _rules.interruptsToEscape - _interrupts : 0;
            if (_rules.maxCuts)
                return _rules.maxCuts > _cuts ? _rules.maxCuts - _cuts : 0;
            return 0;
        }

    private:
        void StartPause(std::uint32_t ms)
        {
            _phase = OpPhase::Pause;
            _leftMs = ms;
        }

        void End(OpOutcome outcome)
        {
            _phase = OpPhase::Done;
            _outcome = outcome;
            _leftMs = 0;
        }

        OperationRules _rules;
        OpPhase _phase = OpPhase::Idle;
        OpOutcome _outcome = OpOutcome::None;
        std::uint32_t _leftMs = 0;
        std::uint32_t _elapsedMs = 0;
        std::uint32_t _seatedMs = 0;
        std::uint32_t _wrenchCooldownMs = 0;
        std::uint32_t _interrupts = 0;
        std::uint32_t _totalInterrupts = 0;
        std::uint32_t _landed = 0;
        std::uint32_t _cuts = 0;
        std::uint32_t _wasted = 0;
        std::uint32_t _claws = 0;
        bool _wasSeated = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // KR6 Grafts
    // ----------------------------------------------------------------------------------------------------------------

    enum class Graft : std::uint8_t
    {
        Hands = 1,  // Killing Frenzy, emote line 4
        Eyes = 2,   // later escapes need 4 interrupts, emote line 6
        Heart = 3,  // heals 10% / 15%, emote line 7; every success after the third is another heart
    };

    // The graft of the `success`-th successful operation (1-based).
    constexpr Graft GraftFor(std::uint32_t success)
    {
        if (success <= 1)
            return Graft::Hands;
        if (success == 2)
            return Graft::Eyes;
        return Graft::Heart;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // KR7 heroic claws
    // ----------------------------------------------------------------------------------------------------------------

    // A Failed Patient's claws work only at the bench and only while it is free to act: stunned, incapacitated
    // (polymorph, Shackle Undead), feared or pacified, it stops (SC KR7 "slows, roots and stops work"); the count
    // starts over (ClawTicker::Update with false).
    constexpr bool ClawsWork(bool atBench, bool crowdControlled)
    {
        return atBench && !crowdControlled;
    }

    // One Failed Patient's claws: every 3 s spent at the bench, one claw. Leaving the bench restarts the count.
    class ClawTicker
    {
    public:
        // How many claws land this tick (0 or 1 at a server tick).
        std::uint32_t Update(std::uint32_t diff, bool atBench)
        {
            if (!atBench)
            {
                _ms = 0;
                return 0;
            }
            _ms += diff;
            std::uint32_t claws = 0;
            while (_ms >= kClawEveryMs)
            {
                _ms -= kClawEveryMs;
                ++claws;
            }
            return claws;
        }

        void Reset() { _ms = 0; }

    private:
        std::uint32_t _ms = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // KR1 / KR8 timing
    // ----------------------------------------------------------------------------------------------------------------

    // The next operation: 30 s after the last one started, never sooner than 5 s after it ended.
    constexpr std::uint64_t NextOperationAt(std::uint64_t lastStartMs, std::uint64_t lastEndMs)
    {
        return std::max<std::uint64_t>(lastStartMs + kOperationEveryMs, lastEndMs + kOperationMinGapMs);
    }

    // KR8: a Backhand may start now: due, no operation running, and not so close to the next operation that its 2 s
    // cast would hold the hook back.
    constexpr bool BackhandMayStart(std::uint64_t nowMs, std::uint64_t dueMs, bool operationActive,
        std::uint64_t nextOperationMs)
    {
        return nowMs >= dueMs && !operationActive && nowMs + kBackhandOperationGuardMs < nextOperationMs;
    }

    // Detention verdict (SC 2966): pass when at most 1 cut landed (normal) or none (heroic).
    constexpr bool LessonPassed(std::uint32_t landed, bool heroic)
    {
        return landed <= kLessonAllowedLanded(heroic);
    }
}

#endif
