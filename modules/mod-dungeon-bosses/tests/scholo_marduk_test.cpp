// Host tests for MardukVectusLogic.h (S3: Marduk Blackpool and Vectus): the slice, the arena, the syllabus (fixed
// order on normal, a shuffled bag on heroic, the double period), the Drill picks, the Group Exercise split, the quiz
// cap, Marduk's move hold and the shared health rule.
#include "MardukVectusLogic.h"
#include "check.h"
#include <algorithm>
#include <cstdint>
#include <set>
#include <string_view>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoMardukVectus;

namespace
{
    // A deterministic LCG for the shuffles and picks.
    struct Lcg
    {
        std::uint32_t state = 12345;

        std::uint32_t Next()
        {
            state = state * 1664525u + 1013904223u;
            return state >> 8;
        }

        std::uint32_t operator()(std::uint32_t n) { return n ? Next() % n : 0; }
        float Unit() { return static_cast<float>(Next() % 1000000u) / 1000000.f; }
    };

    std::uint32_t constexpr kRefNormal = 3670;
    std::uint32_t constexpr kRefHeroic = 4120;
}

int main()
{
    // ---- Ids ----------------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    {
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(seen.size() == kAllSpells.size());
    }

    // ---- Arena --------------------------------------------------------------------------------------------------
    CHECK(ViewingRoomArena().Contains(kMardukSpawn.XY(), kMardukSpawn.z));
    CHECK(ViewingRoomArena().Contains(kVectusSpawn.XY(), kVectusSpawn.z));
    {
        DungeonKit::Arena const arena = MardukVectusArena();
        CHECK(arena.Contains(kMardukSpawn.XY(), kMardukSpawn.z));
        CHECK(arena.Contains(kVectusSpawn.XY(), kVectusSpawn.z));
        // Marduk's stage corner (outside the report's circle) is in; `.dbtest scholo where` (ArenaFor) agrees with
        // the leash (S3 request, R-A N-13).
        CHECK(ViewingRoomArena().Contains({ 154.5f, 122.5f }, 104.3f));
        CHECK(arena.Contains({ 154.5f, 122.5f }, 104.3f));
        CHECK(ArenaFor(BOSS_MARDUK_VECTUS).Contains({ 154.5f, 122.5f }, 104.3f));
        // R-A N-9: the south-west desks (spawns 48460, 91320, 48465, 48463, 48468, 32 to 39.5 yd from the circle's
        // centre) and the hall's north-west corner are in.
        for (Point3 const p : { Point3{ 94.90f, 73.51f, 97.78f }, Point3{ 95.29f, 76.51f, 97.79f },
            Point3{ 97.92f, 75.09f, 97.96f }, Point3{ 111.24f, 64.84f, 99.04f }, Point3{ 109.25f, 68.80f, 98.94f },
            Point3{ 90.0f, 120.0f, 100.0f } })
            CHECK(arena.Contains(p.XY(), p.z));
        // Every drill floor point is on the arena (a melee player killing a quiz student is never off it).
        for (float x = kViewingFloorBox.minX; x <= kViewingFloorBox.maxX; x += 1.f)
            for (float y = kViewingFloorBox.minY; y <= kViewingFloorBox.maxY; y += 1.f)
                if (OnViewingFloor({ x, y }))
                    CHECK(arena.Contains({ x, y }, 101.0f));
        // The hall's far corners are in; both Iron Gates and the Viewing Room Door are out.
        CHECK(arena.Contains({ 110.0f, 70.0f }, 98.0f));
        CHECK(!arena.Contains({ 91.1f, 100.7f }, 99.0f));     // Iron Gate 175617 (south)
        CHECK(!arena.Contains({ 136.0f, 59.0f }, 102.8f));    // Iron Gate 175618 (east)
        CHECK(!arena.Contains({ 174.4f, 77.9f }, 104.8f));    // Viewing Room Door 175167
        CHECK(!arena.Contains({ 165.0f, 75.0f }, 104.0f));    // the corridor behind the door
        // Every student spawn and the measured drill set are in.
        for (Vec2 p : kViewingDrillCircles)
            CHECK(arena.Contains(p, 100.0f));
        // No other boss's spawn is in this arena.
        CHECK(!arena.Contains(kJandiceSpawn.XY(), kJandiceSpawn.z));
        CHECK(!arena.Contains(kRattlegoreSpawn.XY(), kRattlegoreSpawn.z));
        CHECK(!arena.Contains(kRasSpawn.XY(), kRasSpawn.z));
        CHECK(!arena.Contains(kGandlingSpawn.XY(), kGandlingSpawn.z));
    }

    // ---- The floor ----------------------------------------------------------------------------------------------
    CHECK(OnViewingFloor({ 110.0f, 90.0f }));
    CHECK(!OnViewingFloor({ 143.0f, 100.0f }));     // the lectern block
    CHECK(!OnViewingFloor({ 135.0f, 88.0f }));      // the low wall
    CHECK(!OnViewingFloor({ 80.0f, 90.0f }));       // past the south wall
    for (Vec2 p : kViewingDrillCircles)
        CHECK(OnViewingFloor(p));

    // ---- Syllabus: normal, the fixed order ----------------------------------------------------------------------
    {
        Lcg rng;
        Syllabus s(false);
        CHECK(s.Peek() == Lesson::Drill);
        Lesson const expect[] = { Lesson::Drill, Lesson::GroupExercise, Lesson::PopQuiz, Lesson::Drill,
            Lesson::GroupExercise, Lesson::PopQuiz, Lesson::Drill };
        for (Lesson e : expect)
            CHECK(s.Next(rng) == e);
        s.Reset(false);
        CHECK(s.Next(rng) == Lesson::Drill);
        CHECK(!s.Heroic());
    }

    // ---- Syllabus: heroic, shuffled; each bag holds all three; never twice in a row ------------------------------
    {
        Lcg rng;
        Syllabus s(true);
        CHECK(!s.Peek().has_value());
        std::vector<Lesson> drawn;
        for (int i = 0; i < 300; ++i)
            drawn.push_back(s.Next(rng));
        bool allBags = true;
        for (std::size_t b = 0; b + 3 <= drawn.size(); b += 3)
        {
            std::set<Lesson> bag(drawn.begin() + static_cast<std::ptrdiff_t>(b),
                drawn.begin() + static_cast<std::ptrdiff_t>(b + 3));
            allBags = allBags && bag.size() == 3;
        }
        CHECK(allBags);
        bool noRepeat = true;
        for (std::size_t i = 1; i < drawn.size(); ++i)
            noRepeat = noRepeat && drawn[i] != drawn[i - 1];
        CHECK(noRepeat);
        // Shuffled: the heroic order is not the fixed cycle every time.
        bool differs = false;
        for (std::size_t b = 0; b + 3 <= drawn.size(); b += 3)
            differs = differs || drawn[b] != Lesson::Drill || drawn[b + 1] != Lesson::GroupExercise;
        CHECK(differs);
        // Every lesson opens a bag at some point.
        std::set<Lesson> openers;
        for (std::size_t b = 0; b + 3 <= drawn.size(); b += 3)
            openers.insert(drawn[b]);
        CHECK(openers.size() == 3);
    }

    // ---- Double period: two different lessons per call, heroic below 50% only -----------------------------------
    CHECK(!DoublePeriod(false, 10.f));
    CHECK(!DoublePeriod(true, 50.f));
    CHECK(DoublePeriod(true, 49.9f));
    {
        Lcg rng;
        Syllabus s(true);
        bool distinct = true;
        for (int i = 0; i < 200; ++i)
        {
            std::array<Lesson, 2> const two = s.NextTwo(rng);
            distinct = distinct && two[0] != two[1];
        }
        CHECK(distinct);
    }
    CHECK(LessonYell(Lesson::Drill) == YELL_VECTUS_FLAMESTRIKE);
    CHECK(LessonYell(Lesson::GroupExercise) == YELL_VECTUS_GROUP_EXERCISE);
    CHECK(LessonYell(Lesson::PopQuiz) == YELL_VECTUS_POP_QUIZ);
    CHECK(LessonByName("quiz") == Lesson::PopQuiz);
    CHECK(!LessonByName("recess").has_value());
    CHECK(kLessonEveryMs(false) == 12000 && kLessonEveryMs(true) == 10000 && kLessonFirstMs == 8000);

    // ---- MV1 Drill picks: on the floor, clear of players, disjoint ----------------------------------------------
    {
        Lcg rng;
        std::vector<Vec2> const players{ { 128.0f, 100.0f }, { 126.0f, 98.0f }, { 130.0f, 102.0f }, { 125.0f, 103.0f },
            { 150.0f, 116.0f } };
        for (bool heroic : { false, true })
        {
            std::vector<Vec2> const points = PickDrillPoints(kDrillCount(heroic), players,
                [&rng]() { return rng.Unit(); });
            CHECK(points.size() == kDrillCount(heroic));
            bool ok = true;
            for (std::size_t i = 0; i < points.size(); ++i)
            {
                ok = ok && OnViewingFloor(points[i]);
                for (Vec2 pl : players)
                    ok = ok && DungeonKit::Distance(points[i], pl) >= kDrillClearYd;
                for (std::size_t j = i + 1; j < points.size(); ++j)
                    ok = ok && DungeonKit::Distance(points[i], points[j]) >= kDrillSpacingYd;
            }
            CHECK(ok);
        }
        // A floor check that refuses everything leaves nothing.
        CHECK(PickDrillPoints(6, players, [&rng]() { return rng.Unit(); }, [](Vec2) { return false; }).empty());
        // The random draw always lands outside the floor: the measured set fills in.
        std::vector<Vec2> const fallback = PickDrillPoints(6, { { 128.0f, 100.0f } }, []() { return 0.999f; });
        CHECK(fallback.size() == 6);
    }
    CHECK(kDrillCount(false) == 6 && kDrillCount(true) == 9);
    CHECK(kDrillPct(false) == 45.f && kDrillPct(true) == 60.f);

    // ---- MV2 Group Exercise split ---------------------------------------------------------------------------------
    {
        // Four together on normal: 40% each; alone: the 75% cap; heroic four: 60% each.
        std::vector<std::uint32_t> four = ExerciseShares(kRefNormal, false, 4);
        CHECK(four.size() == 4);
        CHECK(four[0] == 1468 && four[3] == 1468);    // 40% of 3,670
        std::uint32_t sum = 0;
        for (std::uint32_t s : four)
            sum += s;
        CHECK(sum == DungeonKit::RefFlatValue(kRefNormal, kRefNormal, 160.f, false));
        std::vector<std::uint32_t> const alone = ExerciseShares(kRefNormal, false, 1);
        CHECK(alone.size() == 1 && alone[0] == DungeonKit::RefFlatValue(kRefNormal, kRefNormal, 75.f, false));
        std::vector<std::uint32_t> const aloneH = ExerciseShares(kRefHeroic, true, 1);
        CHECK(aloneH.size() == 1 && aloneH[0] == DungeonKit::RefFlatValue(kRefHeroic, kRefHeroic, 75.f, false));
        std::vector<std::uint32_t> const fourH = ExerciseShares(kRefHeroic, true, 4);
        CHECK(fourH.size() == 4 && fourH[0] == DungeonKit::RefFlatValue(kRefHeroic, kRefHeroic, 60.f, false));
        // Two on heroic: 120% each, capped at 75%.
        std::vector<std::uint32_t> const twoH = ExerciseShares(kRefHeroic, true, 2);
        CHECK(twoH.size() == 2 && twoH[1] == DungeonKit::RefFlatValue(kRefHeroic, kRefHeroic, 75.f, false));
        CHECK(ExerciseShares(kRefNormal, false, 0).empty());
        CHECK(ShareStudentFor(0, 6) == 0 && ShareStudentFor(7, 6) == 1 && ShareStudentFor(3, 0) == 0);
    }

    // ---- MV3 Pop Quiz: the cap of 3 graduates ---------------------------------------------------------------------
    CHECK(FinishedQuiz(0) == QuizEnd::Graduated);
    CHECK(FinishedQuiz(2) == QuizEnd::Graduated);
    CHECK(FinishedQuiz(3) == QuizEnd::Capped);
    CHECK(FinishedQuiz(9) == QuizEnd::Capped);
    CHECK(kQuizPct(false) == 30.f && kQuizPct(true) == 50.f && kQuizCastMs == 5000);
    CHECK(std::string_view(QuizEndName(QuizEnd::Stopped)) == "stopped");

    // ---- MV4 / MV6: Marduk's moves never overlap -----------------------------------------------------------------
    CHECK(MoveWaitMs(1000, 0) == 0);
    CHECK(MoveWaitMs(1000, 4000) == 3000);
    CHECK(MoveWaitMs(5000, 4000) == 0);
    CHECK(kSweepAngleDeg(false) == 90.f && kSweepAngleDeg(true) == 120.f);
    CHECK(kSweepPct(false) == 60.f && kSweepPct(true) == 70.f);
    CHECK(kWhirlwindCastMs + kWhirlwindSpinMs == 6000);

    // ---- Shared health ---------------------------------------------------------------------------------------------
    CHECK(MirrorFor(1000, 1000, 0) == Mirror::None);
    CHECK(MirrorFor(1000, 0, 100) == Mirror::None);
    CHECK(MirrorFor(1000, 1000, 100) == Mirror::Apply);
    CHECK(MirrorFor(1000, 1000, 1000) == Mirror::LetDie);
    CHECK(MirrorFor(1000, 50, 100) == Mirror::Clamp);
    CHECK(MirrorFor(50, 1000, 100) == Mirror::LetDie);
    CHECK(SyncedHealth(500, 700) == 500);
    CHECK(SyncedHealth(700, 500) == 500);

    // ---- Boss data ------------------------------------------------------------------------------------------------
    CHECK(kQuizStudentPriority > kGraduatePriority && kGraduatePriority > 0);

    return Report("scholo_marduk_test");
}
