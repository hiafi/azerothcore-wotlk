/*
 * mod-dungeon-bosses, Scholomance S3: Marduk Blackpool and Vectus, the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning, the syllabus (fixed order on normal, a shuffled bag on heroic, the double
 * period), the Group Exercise split, the quiz cap, the Drill floor picks, Marduk's move hold, the shared health rule
 * and the encounter arena. Build spec: SC 934-991 (docs/dungeons/scholomance-rework.md), MV1-MV7; handoff section 3.5
 * row S3, section 3.6. Tested by tests/scholo_marduk_test.cpp.
 *
 * Conventions (ScholomanceRework.h): spell ids only inside kSpellsMardukVectus (apps/dbc-tools
 * source/npcs/scholomance/marduk_and_vectus.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. Damage percents are of the reference row of the
 * difficulty (normal 3,670 / 3,710, heroic 4,120 / 4,110; MapLevels pin 289:60 289h:60).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_MARDUK_VECTUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_MARDUK_VECTUS_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <string_view>
#include <utility>
#include <vector>

namespace ScholoMardukVectus
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsMardukVectus;

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (marduk_and_vectus.py declares the same ids; 206167-206169 spare)
    // ----------------------------------------------------------------------------------------------------------------
    enum MardukVectusSpells : std::uint32_t
    {
        SPELL_MV_DRILL_CAST             = 206150,   // MV1 a student's 3 s Flamestrike at a floor point (2 s fire look)
        SPELL_MV_DRILL_CAST_HEROIC      = 206151,   // MV1 heroic: the same, the fire look burns 10 s
        SPELL_MV_DRILL                  = 206152,   // MV1 the registry's resolve copy, Fire
        SPELL_MV_DRILL_BURN             = 206153,   // MV1 heroic: the burning circle's tick (linger resolve copy), Fire
        SPELL_MV_GROUP_EXERCISE_MARK    = 206154,   // MV2 the marked player's 4 s marker
        SPELL_MV_GROUP_EXERCISE         = 206155,   // MV2 a student's Shadow Bolt: one split share (base point 0)
        SPELL_MV_GROUP_EXERCISE_LOOK    = 206156,   // MV2 a student's Shadow Bolt with no damage (the volley's look)
        SPELL_MV_ON_THE_SPOT            = 206157,   // MV3 the quiz student's aura (target priority, ignore list key)
        SPELL_MV_POP_QUIZ               = 206158,   // MV3 the quiz student's 5 s interruptible volley, Shadow
        SPELL_MV_EBON_SWEEP_BAR         = 206159,   // MV4 Marduk's 2 s wind-up
        SPELL_MV_EBON_SWEEP             = 206160,   // MV4 the registry's resolve copy, Shadow
        SPELL_MV_EBON_SWEEP_TANK        = 206161,   // MV4 the tank's own heavy hit, Shadow (R2 S-1)
        SPELL_MV_FIREBALL               = 206162,   // MV5 Vectus's filler, a real 3 s cast, Fire
        SPELL_MV_WHIRLWIND_BAR          = 206163,   // MV6 (heroic) Marduk's 2 s cast bar
        SPELL_MV_WHIRLWIND_SPIN         = 206164,   // MV6 (heroic) the 4 s spin aura on Marduk
        SPELL_MV_WHIRLWIND              = 206165,   // MV6 (heroic) the spin tick (resolve copy), Physical
        SPELL_MV_GRADUATE_BOLT          = 206166,   // the Graduate's Shadow Bolt, a real 2 s cast
    };

    inline constexpr std::array<std::uint32_t, 17> kAllSpells{ {
        SPELL_MV_DRILL_CAST, SPELL_MV_DRILL_CAST_HEROIC, SPELL_MV_DRILL, SPELL_MV_DRILL_BURN,
        SPELL_MV_GROUP_EXERCISE_MARK, SPELL_MV_GROUP_EXERCISE, SPELL_MV_GROUP_EXERCISE_LOOK, SPELL_MV_ON_THE_SPOT,
        SPELL_MV_POP_QUIZ, SPELL_MV_EBON_SWEEP_BAR, SPELL_MV_EBON_SWEEP, SPELL_MV_EBON_SWEEP_TANK, SPELL_MV_FIREBALL,
        SPELL_MV_WHIRLWIND_BAR, SPELL_MV_WHIRLWIND_SPIN, SPELL_MV_WHIRLWIND, SPELL_MV_GRADUATE_BOLT } };

    // Stock spells kept (DD scales them on heroic).
    using ScholomanceRework::SPELL_BLAST_WAVE;          // 17277 Vectus, MV7
    using ScholomanceRework::SPELL_DEFILING_AURA;       // 17695 Marduk, on the pull
    inline constexpr std::uint32_t SPELL_GAMBIT_RESURRECTION = 58854;  // Dawn's Gambit: the students fall (stock)
    inline constexpr std::uint32_t SPELL_GAMBIT_TRANSFORM = 18115;     // Dawn's Gambit: Viewing Room Student Transform

    // Dawn's Gambit (GO 176110's SmartAI, quest 4771) sends SetData(2, n): 1 and 2 to Marduk (his two "We are
    // betrayed!" lines), 3 and 4 to the students (they fall, then rise as skeletons), 4 to Vectus (his yell).
    inline constexpr std::uint32_t kGambitDataId = 2;
    inline constexpr std::uint32_t kGambitMardukFirst = 1;
    inline constexpr std::uint32_t kGambitMardukSecond = 2;
    inline constexpr std::uint32_t kGambitStudentsFall = 3;
    inline constexpr std::uint32_t kGambitStudentsRise = 4;
    inline constexpr std::uint32_t kGambitVectus = 4;

    // Registry tags (log and `.mech` ledger).
    enum MardukVectusTags : std::uint32_t
    {
        TAG_MV_DRILL            = 0x4D560101,   // MV1
        TAG_MV_DRILL_BURN       = 0x4D560102,   // MV1 heroic linger
        TAG_MV_GROUP_EXERCISE   = 0x4D560201,   // MV2
        TAG_MV_EBON_SWEEP       = 0x4D560401,   // MV4
        TAG_MV_WHIRLWIND        = 0x4D560601,   // MV6
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The syllabus (MV1-MV3): Vectus calls a lesson every 12 s (normal, the fixed order Drill, Group Exercise, Pop
    // Quiz) or 10 s (heroic, a shuffled order), first at 8 s. Heroic double period: below 50% of the shared health,
    // each call names two lessons at once.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Lesson : std::uint8_t
    {
        Drill = 0,
        GroupExercise = 1,
        PopQuiz = 2,
    };

    inline constexpr std::size_t kLessonCount = 3;
    inline constexpr std::uint32_t kLessonFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kLessonEveryMs{ 12000, 10000 };
    inline constexpr float kDoublePeriodBelowPct = 50.f;

    constexpr char const* LessonName(Lesson l)
    {
        switch (l)
        {
            case Lesson::Drill:
                return "drill";
            case Lesson::GroupExercise:
                return "exercise";
            case Lesson::PopQuiz:
                return "quiz";
        }
        return "?";
    }

    constexpr std::optional<Lesson> LessonByName(std::string_view name)
    {
        for (std::size_t i = 0; i < kLessonCount; ++i)
            if (name == LessonName(static_cast<Lesson>(i)))
                return static_cast<Lesson>(i);
        return std::nullopt;
    }

    // Vectus's yell group naming the lesson (ScholomanceRework.h VectusTexts).
    constexpr std::uint8_t LessonYell(Lesson l)
    {
        switch (l)
        {
            case Lesson::Drill:
                return ScholomanceRework::YELL_VECTUS_FLAMESTRIKE;
            case Lesson::GroupExercise:
                return ScholomanceRework::YELL_VECTUS_GROUP_EXERCISE;
            case Lesson::PopQuiz:
                return ScholomanceRework::YELL_VECTUS_POP_QUIZ;
        }
        return ScholomanceRework::YELL_VECTUS_FLAMESTRIKE;
    }

    // The heroic double period: below 50% of the shared health.
    constexpr bool DoublePeriod(bool heroic, float healthPct)
    {
        return heroic && healthPct < kDoublePeriodBelowPct;
    }

    // The order of the lessons. Normal: the fixed cycle Drill, Group Exercise, Pop Quiz. Heroic: a shuffled bag of the
    // three, refilled when empty, never the same lesson twice in a row across a refill. `rand(n)` returns [0, n).
    class Syllabus
    {
    public:
        explicit Syllabus(bool heroic = false) : _heroic(heroic) { }

        void Reset(bool heroic)
        {
            _heroic = heroic;
            _bagSize = 0;
            _next = 0;
            _last.reset();
        }

        bool Heroic() const { return _heroic; }

        template <class Rand>
        Lesson Next(Rand&& rand)
        {
            Lesson l;
            if (!_heroic)
            {
                l = static_cast<Lesson>(_next);
                _next = (_next + 1) % kLessonCount;
            }
            else
            {
                if (!_bagSize)
                    Refill(rand);
                l = _bag[--_bagSize];
            }
            _last = l;
            return l;
        }

        // Two different lessons (a double period call).
        template <class Rand>
        std::array<Lesson, 2> NextTwo(Rand&& rand)
        {
            Lesson const first = Next(rand);
            Lesson second = Next(rand);
            for (std::size_t guard = 0; second == first && guard < 8; ++guard)
                second = Next(rand);
            return { first, second };
        }

        // The lesson the next call names: the fixed cycle's on normal; on heroic the bag's top (none when the bag must
        // be refilled first).
        std::optional<Lesson> Peek() const
        {
            if (!_heroic)
                return static_cast<Lesson>(_next);
            if (_bagSize)
                return _bag[_bagSize - 1];
            return std::nullopt;
        }

        std::optional<Lesson> Last() const { return _last; }

    private:
        template <class Rand>
        void Refill(Rand&& rand)
        {
            _bag = { { Lesson::Drill, Lesson::GroupExercise, Lesson::PopQuiz } };
            // Fisher-Yates; the bag is drawn from the back.
            for (std::size_t i = kLessonCount - 1; i > 0; --i)
            {
                std::size_t const j = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(i + 1))) % (i + 1);
                std::swap(_bag[i], _bag[j]);
            }
            // Never the last lesson again at once: swap it away from the top.
            if (_last && _bag[kLessonCount - 1] == *_last)
                std::swap(_bag[kLessonCount - 1], _bag[0]);
            _bagSize = kLessonCount;
        }

        bool _heroic = false;
        std::array<Lesson, kLessonCount> _bag{ { Lesson::Drill, Lesson::GroupExercise, Lesson::PopQuiz } };
        std::size_t _bagSize = 0;
        std::size_t _next = 0;
        std::optional<Lesson> _last;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // MV1 Flamestrike Drill: 6 / 9 students cast at random floor points, never on a player: 6 yd circles, a 3 s cast
    // as the warning, 45% / 60% Fire, no Weakened. Heroic: the circles burn 10 s.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<std::uint32_t> kDrillCount{ 6, 9 };
    inline constexpr float kDrillRadiusYd = 6.f;
    inline constexpr std::uint32_t kDrillWarnMs = 3000;
    inline constexpr NH<float> kDrillPct{ 45.f, 60.f };
    // Heroic burn: 10 s, a tick every 1 s. The build spec gives no tick number: 10% a tick and the kit's slow, so a
    // player who crosses one loses a tick or two (WP-T tunes it).
    inline constexpr std::uint32_t kDrillBurnMs = 10000;
    inline constexpr std::uint32_t kDrillBurnTickMs = 1000;
    inline constexpr float kDrillBurnPct = 10.f;
    // "Never on a player": a circle's center at least its radius plus 1 yd from every player when it is placed.
    inline constexpr float kDrillClearYd = kDrillRadiusYd + 1.f;
    // Disjoint circles (the build spec's coverage math: six circles, about a fifth of the room).
    inline constexpr float kDrillSpacingYd = 2.f * kDrillRadiusYd;
    inline constexpr std::uint32_t kDrillTries = 80;

    // The Viewing Room's floor (NAVMESH-REPORT section 3): the whole room box, less the lectern block and the low
    // wall west of it (the two small hall holes are under 8 sq yd and need no rule). The box stops at y 63, short of
    // the east Iron Gate 175618 (136, 59).
    inline constexpr DungeonKit::Box2 kViewingFloorBox{ 88.0f, 156.0f, 63.0f, 123.0f };
    inline constexpr std::array<DungeonKit::Box2, 2> kViewingFloorHoles{ {
        { 136.0f, 149.0f, 90.0f, 111.0f },      // the lectern block (Vectus stands on its north edge)
        { 129.0f, 141.0f, 86.0f, 90.0f } } };   // the low wall west of it
    inline constexpr float kViewingFloorZMin = 95.0f;
    inline constexpr float kViewingFloorZMax = 106.0f;
    inline constexpr float kViewingFloorProbeZ = 107.0f;   // GetHeight from above the highest floor (105)

    inline bool OnViewingFloor(Vec2 p)
    {
        if (!kViewingFloorBox.Contains(p))
            return false;
        for (DungeonKit::Box2 const& hole : kViewingFloorHoles)
            if (hole.Contains(p))
                return false;
        return true;
    }

    // The fight's arena: the report's circle (128, 95) r 32 holds the student hall and Vectus's lectern, but Marduk's
    // stage (x 136-155, y 106-123) reaches past it (its corner is 38.9 yd out), so a box over the north part (x 131 to
    // 157, y 63 to 124, z 100 to 108) is added. Both gates (91.1, 100.7) and (136, 59) and the Viewing Room Door
    // (174.4, 77.9) stay outside (tests).
    inline DungeonKit::Arena MardukVectusArena()
    {
        DungeonKit::Arena arena = ScholomanceRework::ViewingRoomArena();
        arena.Add(DungeonKit::ArenaRegion::Polygon({ { 131.0f, 63.0f }, { 157.0f, 63.0f }, { 157.0f, 124.0f },
            { 131.0f, 124.0f } }, 100.0f, 108.0f));
        return arena;
    }

    // A candidate drill center: on the floor, clear of every player and of the circles picked so far.
    inline bool DrillPointFits(Vec2 p, std::vector<Vec2> const& players, std::vector<Vec2> const& picked)
    {
        if (!OnViewingFloor(p))
            return false;
        for (Vec2 const& pl : players)
            if (DungeonKit::Distance(p, pl) < kDrillClearYd)
                return false;
        for (Vec2 const& q : picked)
            if (DungeonKit::Distance(p, q) < kDrillSpacingYd)
                return false;
        return true;
    }

    // Up to `count` drill centers. `rand01()` returns [0, 1); `floorOk(p)` is the engine's height check (a floor under
    // the point inside the room's z band; none in the host tests). Random points in the floor box first (kDrillTries
    // tries per circle), then the measured set (ScholomanceRework::kViewingDrillCircles) for what is still missing.
    template <class Rand01>
    std::vector<Vec2> PickDrillPoints(std::uint32_t count, std::vector<Vec2> const& players, Rand01&& rand01,
        std::function<bool(Vec2)> const& floorOk = {})
    {
        std::vector<Vec2> picked;
        auto fits = [&](Vec2 p)
        {
            return DrillPointFits(p, players, picked) && (!floorOk || floorOk(p));
        };
        for (std::uint32_t tries = 0; picked.size() < count && tries < count * kDrillTries; ++tries)
        {
            float const fx = rand01();
            float const fy = rand01();
            Vec2 const p{ kViewingFloorBox.minX + fx * (kViewingFloorBox.maxX - kViewingFloorBox.minX),
                kViewingFloorBox.minY + fy * (kViewingFloorBox.maxY - kViewingFloorBox.minY) };
            if (fits(p))
                picked.push_back(p);
        }
        for (Vec2 const& p : ScholomanceRework::kViewingDrillCircles)
        {
            if (picked.size() >= count)
                break;
            if (fits(p))
                picked.push_back(p);
        }
        return picked;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MV2 Group Exercise: a 6 yd Stack on a marked non-tank (4 s); the students fire Shadow Bolts at the target:
    // 160% / 240% split among the players inside, at most 75% each. Shadow, no Weakened (a split hit).
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kExerciseRadiusYd = 6.f;
    inline constexpr std::uint32_t kExerciseWarnMs = 4000;
    inline constexpr NH<float> kExerciseTotalPct{ 160.f, 240.f };
    inline constexpr float kExerciseCapPct = 75.f;
    inline constexpr float kExercisePickRangeYd = 60.f;
    // Students that fire at the target (each share is one bolt; the others fire a bolt with no damage for the look).
    inline constexpr std::uint32_t kExerciseStudents = 6;

    // The pure form of DungeonKit::SplitShares(vectus, inside, kExerciseTotalPct, kExerciseCapPct), from the
    // reference non-tank row `refNonTank`.
    inline std::vector<std::uint32_t> ExerciseShares(std::uint32_t refNonTank, bool heroic, std::uint32_t inside)
    {
        std::uint32_t const total = DungeonKit::RefFlatValue(refNonTank, refNonTank, kExerciseTotalPct(heroic), false);
        std::uint32_t const cap = DungeonKit::RefFlatValue(refNonTank, refNonTank, kExerciseCapPct, false);
        return DungeonKit::SplitDamage(total, inside, cap);
    }

    // The student that deals share `share` (round robin over the `students` that fire).
    constexpr std::size_t ShareStudentFor(std::size_t share, std::size_t students)
    {
        return students ? share % students : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MV3 Pop Quiz: one student stands and casts a 5 s Shadow Bolt Volley (interruptible): 30% / 50% to everyone if it
    // finishes, and the student graduates (cap 3). Stop it by an interrupt or by killing the student (8k / 12k).
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kQuizCastMs = 5000;
    inline constexpr NH<float> kQuizPct{ 30.f, 50.f };
    inline constexpr std::uint32_t kGraduateCap = 3;

    enum class QuizEnd : std::uint8_t
    {
        Graduated,      // the volley finished, under the cap: a Graduate joins the fight
        Capped,         // the volley finished at the cap: the student sits back down
        Stopped,        // interrupted (or the cast failed): the student sits back down
        Killed,         // the student died
    };

    constexpr char const* QuizEndName(QuizEnd e)
    {
        switch (e)
        {
            case QuizEnd::Graduated:
                return "graduated";
            case QuizEnd::Capped:
                return "capped";
            case QuizEnd::Stopped:
                return "stopped";
            case QuizEnd::Killed:
                return "killed";
        }
        return "?";
    }

    // A finished volley with `graduates` already in the fight.
    constexpr QuizEnd FinishedQuiz(std::uint32_t graduates)
    {
        return graduates < kGraduateCap ? QuizEnd::Graduated : QuizEnd::Capped;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Graduate (300533): 15k / 22k, a caster add that stays at its desk and casts Shadow Bolt at random players.
    // The build spec gives no bolt number: 10% of the reference row, a 2 s cast every 3.5 to 5 s (WP-T tunes it).
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kGraduateBoltPct = 10.f;
    inline constexpr std::uint32_t kGraduateBoltFirstMs = 1500;
    inline constexpr std::uint32_t kGraduateBoltMinMs = 3500;
    inline constexpr std::uint32_t kGraduateBoltMaxMs = 5000;
    inline constexpr float kGraduateRangeYd = 45.f;

    // ----------------------------------------------------------------------------------------------------------------
    // MV4 Ebon Sweep: every 15 s from 10 s, a 2 s wind-up (emote), then a 10 yd cone in front of Marduk, 90 / 120
    // degrees: 60% / 70% Shadow to anyone in it but his target; the tank takes its own heavy hit. Held during MV6.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kSweepFirstMs = 10000;
    inline constexpr std::uint32_t kSweepEveryMs = 15000;
    inline constexpr std::uint32_t kSweepWarnMs = 2000;
    inline constexpr float kSweepLengthYd = 10.f;
    inline constexpr NH<float> kSweepAngleDeg{ 90.f, 120.f };
    inline constexpr NH<float> kSweepPct{ 60.f, 70.f };
    // "The tank takes it as a heavy hit": the build spec gives no number. 35% / 40% of the tank row (WP-T tunes it).
    inline constexpr NH<float> kSweepTankPct{ 35.f, 40.f };

    // ----------------------------------------------------------------------------------------------------------------
    // MV6 Whirlwind (heroic): every 30 s from 20 s, a 2 s cast and emote, then a 4 s rooted spin: 8 yd on Marduk,
    // a tick every 1 s for 20% Physical, one Weakened on a player's first tick per spin. Everyone steps out.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kWhirlwindFirstMs = 20000;
    inline constexpr std::uint32_t kWhirlwindEveryMs = 30000;
    inline constexpr std::uint32_t kWhirlwindCastMs = 2000;
    inline constexpr std::uint32_t kWhirlwindSpinMs = 4000;
    inline constexpr std::uint32_t kWhirlwindTickMs = 1000;
    inline constexpr float kWhirlwindRadiusYd = 8.f;
    inline constexpr float kWhirlwindPct = 20.f;

    // Marduk's two moves never overlap: Ebon Sweep waits while a Whirlwind winds up or spins, and a Whirlwind waits for
    // a sweep's wind-up. `busyUntilMs` is when the move in progress ends (0: none); the wait from `nowMs`.
    constexpr std::uint32_t MoveWaitMs(std::uint32_t nowMs, std::uint32_t busyUntilMs)
    {
        return busyUntilMs > nowMs ? busyUntilMs - nowMs : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MV5 Fireball (Vectus's filler) and MV7 Blast Wave (stock 17277)
    // ----------------------------------------------------------------------------------------------------------------
    // "Free casting: Fireball at random players between lessons, healer load": a real 3 s cast with a short gap. The
    // build spec gives no number: 10% of the reference row (WP-T tunes it).
    inline constexpr float kFireballPct = 10.f;
    inline constexpr std::uint32_t kFireballFirstMs = 3000;
    inline constexpr std::uint32_t kFireballGapMinMs = 1500;
    inline constexpr std::uint32_t kFireballGapMaxMs = 3500;
    inline constexpr float kFireballRangeYd = 45.f;
    // Blast Wave (the stock cadence: 3-12 s, then 11-22 s, only with someone within 10 yd).
    inline constexpr float kBlastWaveRadiusYd = 10.f;
    inline constexpr std::uint32_t kBlastWaveFirstMinMs = 3000;
    inline constexpr std::uint32_t kBlastWaveFirstMaxMs = 12000;
    inline constexpr std::uint32_t kBlastWaveMinMs = 11000;
    inline constexpr std::uint32_t kBlastWaveMaxMs = 22000;

    // Vectus's idle lecture out of combat (the stock SmartAI row: 6-20 s, then every 30-50 s).
    inline constexpr std::uint32_t kLectureFirstMinMs = 6000;
    inline constexpr std::uint32_t kLectureFirstMaxMs = 20000;
    inline constexpr std::uint32_t kLectureMinMs = 30000;
    inline constexpr std::uint32_t kLectureMaxMs = 50000;

    // ----------------------------------------------------------------------------------------------------------------
    // Shared health (the Twin Val'kyr pattern, boss_twin_valkyr.cpp UpdateSharedHealth): damage to either comes off
    // both, and they die together.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Mirror : std::uint8_t
    {
        None,           // nothing to do (no damage, or the partner is gone)
        Apply,          // take the same damage off the partner
        Clamp,          // the damage would kill the partner but not this one (out of sync): leave the partner at 1
        LetDie,         // the damage kills this one: its death kills the partner (JustDied), nothing now
    };

    // What a hit of `damage` on a unit at `health` does to its partner at `partnerHealth`.
    constexpr Mirror MirrorFor(std::uint32_t health, std::uint32_t partnerHealth, std::uint32_t damage)
    {
        if (!damage || !partnerHealth)
            return Mirror::None;
        if (damage >= health)
            return Mirror::LetDie;
        if (damage >= partnerHealth)
            return Mirror::Clamp;
        return Mirror::Apply;
    }

    // The two bars always match: both take the lower health (a heal, a regen tick or a GM command on one is undone).
    constexpr std::uint32_t SyncedHealth(std::uint32_t a, std::uint32_t b)
    {
        return a < b ? a : b;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (SC "Boss data"): target priority the quiz student, then graduates, then either boss; interrupt list
    // the Pop Quiz; Vectus's Fireball is do-not-kick (priority 0), so the bots keep their kicks for the quiz.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::int8_t kQuizStudentPriority = 3;
    inline constexpr std::int8_t kGraduatePriority = 2;
    inline constexpr std::uint8_t kQuizInterruptPriority = 3;

    // The students of the hall (32 spawns, all in the Viewing Room) within this of Vectus.
    inline constexpr float kStudentSearchYd = 80.f;
    // A timer that meets a cast (or a move in progress) tries again shortly.
    inline constexpr std::uint32_t kBusyRetryMs = 500;
}

#endif
