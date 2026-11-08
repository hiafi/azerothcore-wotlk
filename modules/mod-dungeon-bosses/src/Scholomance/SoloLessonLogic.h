/*
 * mod-dungeon-bosses, Scholomance: the pure half of the solo lesson interface (SoloLesson.h; handoff section 3.7).
 * Host-tested by tests/scholomance_test.cpp.
 *
 * A solo lesson is Gandling's detention room (GD1): one student, alone behind the room's shut gate, for 15 s, against
 * the room instructor's own mechanic ("Detention" notes at each instructor, SC 2960-2971). The lesson passes or fails
 * by its own rule (at most `allowedFailures` registry failures of the student), and it ends early, without a verdict,
 * when it is no longer safe to run (handoff section 3.7 "Safety").
 *
 *   LessonClock        the 15 s clock, the failure count and the verdict
 *   LessonEndCheck     why a running lesson must stop now (the student died, left, is the last one alive, a wipe)
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_SOLO_LESSON_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_SOLO_LESSON_LOGIC_H

#include <cstdint>

namespace ScholomanceRework
{
    std::uint32_t constexpr kLessonMs = 15000;              // SC GD1: 15 s in the room
    std::uint32_t constexpr kLessonFailurePctNormal = 15;   // any failure hit: 15% / 25% of the reference row,
    std::uint32_t constexpr kLessonFailurePctHeroic = 25;   // plus Weakened (ruling 21)

    // A lesson's failure hit, percent of the reference row (SC GD1): 15% normal, 25% heroic.
    constexpr float LessonFailurePct(bool heroic)
    {
        return float(heroic ? kLessonFailurePctHeroic : kLessonFailurePctNormal);
    }

    enum class LessonEnd : std::uint8_t
    {
        None,               // still running
        TimeUp,             // the clock ran out: Passed() / Failed() hold the verdict
        Finished,           // the lesson ended itself early (its last job resolved)
        StudentDied,        // safety: no verdict, the gate opens
        StudentLeft,        // safety: logged out, left the map, teleported away
        LastAlive,          // safety: nobody else in the study is alive
        Aborted,            // a wipe, Gandling's evade or death, a reset: no verdict
    };

    constexpr bool IsSafetyEnd(LessonEnd e)
    {
        return e == LessonEnd::StudentDied || e == LessonEnd::StudentLeft || e == LessonEnd::LastAlive
            || e == LessonEnd::Aborted;
    }

    class LessonClock
    {
    public:
        // `allowedFailures`: how many student failures still pass (Krastinov's normal lesson allows 1 Incision).
        void Start(std::uint32_t durationMs = kLessonMs, std::uint32_t allowedFailures = 0)
        {
            _durationMs = durationMs;
            _allowedFailures = allowedFailures;
            _elapsedMs = 0;
            _failures = 0;
            _end = LessonEnd::None;
            _started = true;
        }

        // True when this tick ran the clock out.
        bool Advance(std::uint32_t diff)
        {
            if (!Running())
                return false;
            _elapsedMs += diff;
            if (_elapsedMs < _durationMs)
                return false;
            _end = LessonEnd::TimeUp;
            return true;
        }

        void Fail()
        {
            if (Running())
                ++_failures;
        }

        // Ends the lesson now (`Finished`, or a safety end). A second end keeps the first.
        void End(LessonEnd why)
        {
            if (Running() && why != LessonEnd::None)
                _end = why;
        }

        bool Started() const { return _started; }
        bool Running() const { return _started && _end == LessonEnd::None; }
        bool Done() const { return _started && _end != LessonEnd::None; }
        LessonEnd EndReason() const { return _end; }
        // A verdict exists only when the lesson ran to its end (TimeUp or Finished).
        bool HasVerdict() const { return Done() && !IsSafetyEnd(_end); }
        bool Failed() const { return HasVerdict() && _failures > _allowedFailures; }
        bool Passed() const { return HasVerdict() && _failures <= _allowedFailures; }
        std::uint32_t Failures() const { return _failures; }
        std::uint32_t ElapsedMs() const { return _elapsedMs; }
        std::uint32_t RemainingMs() const { return _elapsedMs < _durationMs ? _durationMs - _elapsedMs : 0; }

    private:
        std::uint32_t _durationMs = kLessonMs;
        std::uint32_t _allowedFailures = 0;
        std::uint32_t _elapsedMs = 0;
        std::uint32_t _failures = 0;
        LessonEnd _end = LessonEnd::None;
        bool _started = false;
    };

    // Why a running lesson must stop now (handoff section 3.7 Safety), in priority order; None: carry on.
    constexpr LessonEnd LessonEndCheck(bool studentInMap, bool studentAlive, bool anyoneElseAlive, bool encounterOn)
    {
        if (!encounterOn)
            return LessonEnd::Aborted;
        if (!studentInMap)
            return LessonEnd::StudentLeft;
        if (!studentAlive)
            return LessonEnd::StudentDied;
        if (!anyoneElseAlive)
            return LessonEnd::LastAlive;
        return LessonEnd::None;
    }
}

#endif
