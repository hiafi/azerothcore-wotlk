// Host tests for IlluciaLogic.h (S10: Lady Illucia Barov (10502)): the ids, the build spec numbers, the timeline, the
// Foresight chain schedule, the motion track's prediction (still = on the player), the Memory trail recorder, the
// Fear's run, the step out to the hall and the arena.
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

    // ---- motion track and prediction (handoff section 5: still = on the player) -------------------------------------
    {
        MotionTrack empty;
        Prediction const none = PredictSpot(empty, 1500);
        CHECK(none.still);

        // Standing: on the player.
        MotionTrack still = Walk({ 240.f, 0.f }, 0.f, 0.f, 5);
        Prediction const p0 = PredictSpot(still, 1500);
        CHECK(p0.still);
        CHECK(Near(p0.at, Vec2{ 240.f, 0.f }));

        // One sample: no heading yet, on the player.
        MotionTrack one;
        one.Add(1000, { 230.f, 2.f });
        CHECK(PredictSpot(one, 1500).still);

        // Running east at 7 yd/s: 10.5 yd ahead in 1.5 s.
        MotionTrack run = Walk({ 220.f, 0.f }, 0.f, 7.f, 6);
        Vec2 const now = run.Latest().p;
        Prediction const p1 = PredictSpot(run, 1500);
        CHECK(!p1.still);
        CHECK(Near(p1.speed, 7.f, 0.05f));
        CHECK(Near(p1.heading, 0.f, 0.01f));
        CHECK(Near(p1.at, Vec2{ now.x + 10.5f, now.y }, 0.05f));

        // Running north-west: the heading follows.
        float const nw = 3.f * DungeonKit::kPi / 4.f;
        MotionTrack diag = Walk({ 240.f, -5.f }, nw, 7.f, 4);
        Prediction const p2 = PredictSpot(diag, 1500);
        CHECK(!p2.still);
        CHECK(Near(p2.heading, nw, 0.01f));
        CHECK(Near(DungeonKit::Distance(diag.Latest().p, p2.at), 10.5f, 0.05f));

        // A turn shows within the 400 ms window: east for 1 s, then north for 0.4 s.
        MotionTrack turn = Walk({ 220.f, 0.f }, 0.f, 7.f, 6, 1000);
        Vec2 corner = turn.Latest().p;
        turn.Add(2200, { corner.x, corner.y + 1.4f });
        turn.Add(2400, { corner.x, corner.y + 2.8f });
        Prediction const p3 = PredictSpot(turn, 1500);
        CHECK(!p3.still);
        CHECK(Near(p3.heading, DungeonKit::kPi / 2.f, 0.01f));

        // Stopping: the newest 400 ms show no movement, so the next marker is on the player again.
        MotionTrack stop = Walk({ 220.f, 0.f }, 0.f, 7.f, 6, 1000);
        Vec2 const halt = stop.Latest().p;
        stop.Add(2200, halt);
        stop.Add(2400, halt);
        Prediction const p4 = PredictSpot(stop, 1500);
        CHECK(p4.still);
        CHECK(Near(p4.at, halt));

        // Walking slowly still counts as moving; creeping does not.
        CHECK(!PredictSpot(Walk({ 220.f, 0.f }, 0.f, 2.5f, 4), 1500).still);
        CHECK(PredictSpot(Walk({ 220.f, 0.f }, 0.f, 0.5f, 4), 1500).still);

        // A teleport or a knockback (40 yd/s) is not a heading: on the player.
        CHECK(PredictSpot(Walk({ 220.f, 0.f }, 0.f, 40.f, 4), 1500).still);

        // Samples closer than 50 ms replace the newest; a clock going back starts over.
        MotionTrack close;
        close.Add(1000, { 0.f, 0.f });
        close.Add(1200, { 1.f, 0.f });
        close.Add(1220, { 1.5f, 0.f });
        CHECK(close.Size() == 2);
        CHECK(Near(close.Latest().p, Vec2{ 1.5f, 0.f }));
        close.Add(500, { 9.f, 9.f });
        CHECK(close.Size() == 1);

        // The ring keeps its newest kSize samples.
        MotionTrack many = Walk({ 0.f, 0.f }, 0.f, 7.f, 20);
        CHECK(many.Size() == MotionTrack::kSize);
        CHECK(many.Latest().t == 1000 + 19 * kSampleEveryMs);
    }

    // ---- Memory trail recorder ------------------------------------------------------------------------------------
    {
        // A straight 7 yd/s run, sampled every 200 ms (1.4 yd a sample): 4 yd pieces, each released once the runner is
        // 2.5 yd past its end; pieces tile the path end to end.
        TrailRecorder trail;
        std::vector<TrailSegment> laid;
        for (int i = 0; i <= 30; ++i)
        {
            Vec2 const p{ 210.f + 1.4f * float(i), 0.f };
            for (TrailSegment const& s : trail.Feed(p))
            {
                // Never under the runner: the piece ends at least 2.5 yd behind it.
                CHECK(DungeonKit::Distance(p, s.to) >= kTrailClearYd - 0.001f);
                laid.push_back(s);
            }
        }
        CHECK(laid.size() >= 8);
        for (std::size_t i = 0; i < laid.size(); ++i)
        {
            float const len = DungeonKit::Distance(laid[i].from, laid[i].to);
            CHECK(len >= kTrailSegmentYd - 0.001f && len < kTrailSegmentYd + 1.4f);
            if (i)
                CHECK(Near(laid[i].from, laid[i - 1].to));
        }
        CHECK(Near(laid.front().from, Vec2{ 210.f, 0.f }));

        // Flush lays only what the runner has left behind.
        std::vector<TrailSegment> const tail = trail.Flush({ 252.f, 0.f });
        for (TrailSegment const& s : tail)
            CHECK(DungeonKit::Distance(Vec2{ 252.f, 0.f }, s.to) >= kTrailClearYd);
        CHECK(!trail.Started());

        // Standing still lays nothing.
        TrailRecorder idle;
        std::size_t idleLaid = 0;
        for (int i = 0; i < 10; ++i)
            idleLaid += idle.Feed({ 240.f, 1.f }).size();
        CHECK(idleLaid == 0);
        CHECK(idle.Flush({ 240.f, 1.f }).empty());

        // A teleport starts over: no piece across the jump.
        TrailRecorder jump;
        for (int i = 0; i <= 6; ++i)
            jump.Feed({ 210.f + 1.4f * float(i), 0.f });
        std::vector<TrailSegment> const after = jump.Feed({ 260.f, 5.f });
        CHECK(after.empty());
        CHECK(jump.Pending() == 0);
        bool crossed = false;
        for (int i = 1; i <= 10; ++i)
            for (TrailSegment const& s : jump.Feed({ 260.f + 1.4f * float(i), 5.f }))
                crossed = crossed || s.from.x < 259.f;
        CHECK(!crossed);

        // Budget: two heroic runners at 7 yd/s keep 7 pieces each.
        CHECK(PeakTrailPieces(7.f) == 7);
        CHECK(PeakTrailPieces(0.f) == 0);
    }

    // ---- Fear's run ---------------------------------------------------------------------------------------------
    {
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
