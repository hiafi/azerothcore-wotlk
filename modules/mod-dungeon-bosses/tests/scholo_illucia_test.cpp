// Host tests for IlluciaLogic.h (S10: Lady Illucia Barov (10502)): the ids, the build spec numbers, the timeline, the
// Foresight chain schedule, her tuning of the kit's motion track and trail recorder (their rules are in
// dungeon_kit_test.cpp), the Fear's run, the Passing Grade exemption, the step out to the hall and the arena.
#include "IlluciaLogic.h"
#include "check.h"
#include <cmath>

using namespace ScholomanceRework;
using namespace ScholoIllucia;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool Near(Vec2 a, Vec2 b, float eps = 0.01f)
    {
        return Near(a.x, b.x, eps) && Near(a.y, b.y, eps);
    }

    // A mover sampled every 200 ms for `samples` samples from `start` at `speed` yd/s along `heading`.
    MotionTrack Walk(Vec2 start, float heading, float speed, int samples, std::uint32_t t0 = 1000)
    {
        MotionTrack track;
        for (int i = 0; i < samples; ++i)
        {
            float const d = speed * 0.2f * float(i);
            track.Add(t0 + std::uint32_t(i) * kSampleEveryMs, DungeonKit::Advance(start, heading, d));
        }
        return track;
    }
}

int main()
{
    // ---- ids and slice --------------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 206315 && kSpellSlice.last == 206329);
    for (std::uint32_t id : { std::uint32_t(SPELL_IB_FORESIGHT_CAST), std::uint32_t(SPELL_IB_READ),
        std::uint32_t(SPELL_IB_FORESIGHT), std::uint32_t(SPELL_IB_MEMORY), std::uint32_t(SPELL_IB_FEAR),
        std::uint32_t(SPELL_IB_FEAR_END) })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsAlexei.Contains(id));
        CHECK(!kSpellsGandling.Contains(id));
    }

    // ---- build spec numbers (SC 2695-2741) ------------------------------------------------------------------------
    CHECK(kForesightReads(false) == 1 && kForesightReads(true) == 2);
    CHECK(kForesightMarkers(false) == 3 && kForesightMarkers(true) == 5);
    CHECK(kForesightPct(false) == 30.f && kForesightPct(true) == 40.f);
    CHECK(kForesightRadius == 4.f && kForesightMarkerMs == 1500 && kForesightCastMs == 1500);
    CHECK(kForesightFirstMs == 8000 && kForesightEveryMs == 20000);
    CHECK(!kMemoryTrail(false) && kMemoryTrail(true));
    CHECK(kTrailWidth == 3.f && kTrailLingerMs == 4000 && kTrailTickMs == 1000 && kTrailPct == 10.f);
    CHECK(kFearCastMs == 1500 && kFearMs == 2000 && kFearRadius == 4.f);
    CHECK(kFearEndPct(false) == 15.f && kFearEndPct(true) == 50.f);
    CHECK(kFearFirstMs == 18000 && kFearEveryMs == 20000);
    CHECK(kShadowShockEveryMs == 10000 && kShadowShockFirstMinMs == 1000 && kShadowShockFirstMaxMs == 2000);
    CHECK(kCurseFirstMinMs == 1000 && kCurseFirstMaxMs == 10000);
    CHECK(kCurseEveryMinMs == 14000 && kCurseEveryMaxMs == 24000);
    // Normal chain about 4.5 s, heroic about 7.5 s (SC); the heroic chains end before the first Fear.
    CHECK(std::uint32_t(kForesightMarkers(false)) * kForesightMarkerMs == 4500);
    CHECK(std::uint32_t(kForesightMarkers(true)) * kForesightMarkerMs == 7500);
    CHECK(kForesightFirstMs + kForesightCastMs + std::uint32_t(kForesightMarkers(true)) * kForesightMarkerMs
        < kFearFirstMs);
    CHECK(ReadAuraMs(kForesightMarkers(true)) == 9000);
    // Examiner: 80k, heroic values on any map.
    CHECK(kExaminerHealth == 80000);
    CHECK(HeroicValues(false, true) && HeroicValues(true, false) && !HeroicValues(false, false));
    // The lesson: 3 / 5 markers, 15% / 25%, the chain inside the 15 s.
    CHECK(kLessonMarkers(false) == 3 && kLessonMarkers(true) == 5);
    CHECK(LessonMarkerPct(false) == 15.f && LessonMarkerPct(true) == 25.f);
    CHECK(kLessonReadAtMs + std::uint32_t(kLessonMarkers(true)) * kForesightMarkerMs < kLessonMs);

    // ---- timeline -------------------------------------------------------------------------------------------------
    {
        Timeline t;
        t.Start(1500, 7000);
        CHECK(!t.Due(Beat::Foresight) && !t.Due(Beat::Fear));
        t.Advance(1500);
        CHECK(t.Due(Beat::ShadowShock) && !t.Due(Beat::Curse));
        t.Done(Beat::ShadowShock, kShadowShockEveryMs);
        CHECK(!t.Due(Beat::ShadowShock));
        t.Advance(6500);
        CHECK(t.Due(Beat::Foresight) && t.Due(Beat::Curse) && !t.Due(Beat::Fear));
        t.Done(Beat::Foresight, kForesightEveryMs);
        CHECK(t.next[std::size_t(Beat::Foresight)] == 28000);
        t.Retry(Beat::Curse);
        CHECK(t.next[std::size_t(Beat::Curse)] == 8000 + kRetryMs);
        t.Advance(10000);
        CHECK(t.Due(Beat::Fear));
    }

    // ---- chain schedule: markers at 0, 1.5, 3 s; each lands as the next is placed; ends at 4.5 s --------------------
    {
        ChainSchedule c;
        c.start = 1000;
        c.total = 3;
        CHECK(!c.PlaceDue(999));
        CHECK(c.PlaceDue(1000));
        CHECK(!c.NextIsPredicted());
        c.placed = 1;
        CHECK(c.NextIsPredicted());
        CHECK(!c.PlaceDue(2499) && c.PlaceDue(2500));
        c.placed = 2;
        CHECK(c.PlaceDue(4000));
        c.placed = 3;
        CHECK(!c.PlaceDue(10000));
        CHECK(c.EndAt() == 5500);
        CHECK(!c.Ended(5499) && c.Ended(5500));
    }

    // ---- motion track and Memory trail: her tuning of the kit pieces (their rules: dungeon_kit_test.cpp) ------------
    {
        CHECK(kSampleEveryMs == 200);
        // A 7 yd/s runner: 10.5 yd ahead after one marker's warning.
        MotionTrack run = Walk({ 220.f, 0.f }, 0.f, 7.f, 6);
        Prediction const p = PredictSpot(run, kForesightMarkerMs);
        CHECK(!p.still);
        CHECK(Near(p.at, Vec2{ run.Latest().p.x + 10.5f, 0.f }, 0.05f));

        // The Memory trail's recorder: 4 yd pieces, never under the runner (2.5 yd behind > half its 3 yd width).
        TrailRecorder trail = MemoryTrailRecorder();
        std::size_t laid = 0;
        for (int i = 0; i <= 30; ++i)
        {
            Vec2 const at{ 210.f + 1.4f * float(i), 0.f };
            for (TrailSegment const& s : trail.Feed(at))
            {
                CHECK(DungeonKit::Distance(at, s.to) >= kTrailClearYd - 0.001f);
                CHECK(DungeonKit::Distance(s.from, s.to) >= kTrailSegmentYd - 0.001f);
                ++laid;
            }
        }
        CHECK(laid >= 8);
        CHECK(kTrailClearYd > kTrailWidth / 2.f);

        // Budget: two heroic runners at 7 yd/s keep 7 pieces each.
        CHECK(PeakTrailPieces(7.f) == 7);
        CHECK(PeakTrailPieces(0.f) == 0);
    }

    // ---- Fear's run ---------------------------------------------------------------------------------------------
    {
        // Ranges: the Fear 40 yd (the hall), the Curse its stock 30 yd.
        CHECK(kFearRange == 40.f && kCurseRange == 30.f);
        // The end marker costs the feared player no Passing Grade; a bystander in it still fails (F-B ruling).
        GradeLedger grades;
        std::uint32_t const marker = 42;
        grades.Exempt(marker, 1001);
        CHECK(!grades.Record(marker, 1001) && !grades.HasFailed(1001));
        CHECK(grades.Record(marker, 1002) && grades.HasFailed(1002));

        CHECK(Near(FearRunYd(7.f), 14.f));
        CHECK(Near(FearRunYd(14.f), kFearMaxRunYd));
        CHECK(Near(FearRunYd(0.f), 0.f));
        // Straight away from her.
        CHECK(Near(FearRunBearing({ 243.f, 0.5f }, { 233.f, 0.5f }, 0.f), DungeonKit::kPi, 0.001f));
        CHECK(Near(FearRunBearing({ 243.f, 0.5f }, { 243.f, 8.f }, 0.f), DungeonKit::kPi / 2.f, 0.001f));
        // On top of her: along her facing.
        CHECK(Near(FearRunBearing({ 243.f, 0.5f }, { 243.05f, 0.5f }, 1.25f), 1.25f));
    }

    // ---- the Shadow Vault: step out, arena ------------------------------------------------------------------------
    {
        CHECK(InInnerRoom(kIlluciaSpawn.XY()));
        CHECK(!InInnerRoom({ kIlluciaHallPoint.x, kIlluciaHallPoint.y }));
        CHECK(!InInnerRoom({ 230.f, 0.f }));
        // The boss spawns in her arena, and the hall point, the hall and the inner room are in it.
        CHECK(IlluciaArena().Contains(kIlluciaSpawn.XY(), kIlluciaSpawn.z));
        CHECK(ArenaFor(BOSS_ILLUCIA).Contains(kIlluciaSpawn.XY(), kIlluciaSpawn.z));
        CHECK(IlluciaArena().Contains({ kIlluciaHallPoint.x, kIlluciaHallPoint.y }, kIlluciaHallPoint.z));
        CHECK(IlluciaArena().Contains({ 212.f, 0.f }, 74.6f));
        CHECK(IlluciaArena().Contains({ 270.f, 0.f }, 75.3f));
        // The detention landing (17944) is in her arena: the lesson runs where the fight does.
        CHECK(IlluciaArena().Contains(kClassroomLandings[std::size_t(Classroom::ShadowVault)].XY(),
            kClassroomLandings[std::size_t(Classroom::ShadowVault)].z));
        // The gate (204.3, 0.0) stays out.
        CHECK(!IlluciaArena().Contains({ 204.3f, 0.0f }, 76.2f));
        // A Fear from the hall point runs at most 20 yd: still in the arena both ways along the hall.
        CHECK(IlluciaArena().Contains({ kIlluciaHallPoint.x - kFearMaxRunYd, kIlluciaHallPoint.y }, 74.6f));
    }

    return Report("scholo_illucia_test");
}
