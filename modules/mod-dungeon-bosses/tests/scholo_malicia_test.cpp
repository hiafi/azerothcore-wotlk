// Host tests for MaliciaLogic.h (S5: Instructor Malicia (10505)): the slice and the arena (WP-KS's stub), the Soul
// meter (floor, cap, the weight's percent, drains, pickups, blasts), Bound Soul, the fight timeline on both
// difficulties, the Soulstorm waves (counts, offset, falling souls, the normal floor rule), the Coven's floor picks,
// the detention lesson's numbers and the examiner's, against the build spec (SC 1431-1488).
#include "MaliciaLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace ScholomanceRework;
using namespace ScholoMalicia;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A deterministic [0, 1) generator (an LCG): the picks are tested over many draws.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return float(state >> 8) / float(1u << 24);
        }
    };

    // How many times `beat` fires in `ms` of a fight on one difficulty (every fire takes the fixed cooldown).
    std::uint32_t Fires(Beat beat, bool heroic, std::uint32_t ms)
    {
        Timeline t;
        std::uint32_t fires = 0;
        for (std::uint32_t now = 0; now < ms; now += 100)
        {
            t.Advance(100);
            if (t.Due(beat))
            {
                ++fires;
                t.Done(beat, EveryMs(beat, heroic));
            }
        }
        return fires;
    }
}

int main()
{
    // ---- KS's stub checks: the slice and the arena ----------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(MaliciaArena().Contains(kMaliciaSpawn.XY(), kMaliciaSpawn.z));
    CHECK(ArenaFor(BOSS_MALICIA).Contains(kMaliciaSpawn.XY(), kMaliciaSpawn.z));

    // ---- Ids: 206205-206217, all in her slice, none in another WP's -------------------------------------------------
    std::uint32_t const ids[] = { SPELL_MA_SOUL, SPELL_MA_SOUL_WEIGHT, SPELL_MA_SOUL_DRAIN_CAST, SPELL_MA_SOUL_DRAIN,
        SPELL_MA_BOUND_SOUL, SPELL_MA_SHADE_VOLLEY, SPELL_MA_SOULSTORM_CAST, SPELL_MA_SOULSTORM_FALL,
        SPELL_MA_SOULSTORM_BLAST, SPELL_MA_SOULSTORM_BURST, SPELL_MA_SHADOW_HEAL, SPELL_MA_SHADOW_NOVA,
        SPELL_MA_SOUL_LOST };
    for (std::size_t i = 0; i < std::size(ids); ++i)
    {
        CHECK(ids[i] == 206205u + i);
        CHECK(kSpellSlice.Contains(ids[i]));
        CHECK(!kSpellsKrastinov.Contains(ids[i]));
        CHECK(!kSpellsRasHardMode.Contains(ids[i]));
    }
    CHECK(kSpellSlice.first == 206205u && kSpellSlice.last == 206224u);
    CHECK(SPELL_MA_SLOW == 13747u && SPELL_MA_CORRUPTION == 18376u && SPELL_MA_STOCK_SHADOW_BOLT_VOLLEY == 17228u);
    CHECK(SPELL_MA_CORRUPTION == SPELL_CORRUPTION);
    CHECK(SPELL_EXAMINER_GHOST_VISUAL == 9617u);
    CHECK(NPC_SC_MALICIAS_SHADE == 300536u && NPC_SC_LOOSE_SOUL == 300537u && NPC_SC_EXAMINER_MALICIA == 300548u);

    // ---- MA1 Soul: 20 at the pull, 5% a stack both ways, floor 10, cap 40 ------------------------------------------
    CHECK(kSoulStart == 20 && kSoulFloor == 10 && kSoulCap == 40 && kSoulPctPerStack == 5);
    CHECK(SoulModPct(20) == 0);
    CHECK(SoulModPct(10) == -50);       // half damage, healing and health: no player under half health
    CHECK(SoulModPct(40) == 100);       // double
    CHECK(SoulModPct(16) == -20);
    CHECK(SoulModPct(24) == 20);
    CHECK(SoulModPct(0) == 0);          // no meter, no weight
    CHECK(SoulModPct(5) == -50);        // clamped to the floor
    CHECK(SoulModPct(45) == 100);       // clamped to the cap
    CHECK(SoulAfter(20, -4) == 16);
    CHECK(SoulAfter(12, -4) == 10);
    CHECK(SoulAfter(10, -1) == 10);
    CHECK(SoulAfter(39, 1) == 40);
    CHECK(SoulAfter(40, 1) == 40);
    CHECK(SoulAfter(5, -1) == 5);       // under the floor already: never lower
    CHECK(SoulAfter(5, 1) == 6);

    // MA2: a drain takes 4, never under the floor; one soul per stack taken (zero-sum).
    CHECK(kDrainStacks == 4);
    CHECK(DrainLoss(20) == 4);
    CHECK(DrainLoss(14) == 4);
    CHECK(DrainLoss(12) == 2);
    CHECK(DrainLoss(10) == 0);
    CHECK(DrainLoss(9) == 0);
    CHECK(DrainLoss(40) == 4);
    // Zero-sum: the meter plus the souls spilled stays the same.
    for (std::uint32_t s = 10; s <= 40; ++s)
        CHECK(SoulAfter(s, -std::int32_t(DrainLoss(s))) + DrainLoss(s) == s);

    // MA3: a soul gives one stack; at the cap (or with no meter) it stays on the floor.
    CHECK(!CanTakeSoul(0));
    CHECK(CanTakeSoul(1));
    CHECK(CanTakeSoul(10));
    CHECK(CanTakeSoul(39));
    CHECK(!CanTakeSoul(40));
    CHECK(Near(kSoulRadius, 2.f));
    CHECK(kSoulFadeMs(false) == 8000 && kSoulFadeMs(true) == 5000);
    CHECK(Near(kSoulSpillMinYd, 10.f) && Near(kSoulSpillMaxYd, 15.f));
    CHECK(kSoulSoakSlackMs > kSoulPollMs);      // the Soak's warning runs past the fade: it never resolves
    CHECK(kSoulSoakSlackMs <= 1000);            // but not long past it: no bot plans an arrival at a gone soul

    // MA6: a blast destroys one stack (in place of Weakened), never under the floor.
    CHECK(BlastLoss(20) == 1);
    CHECK(BlastLoss(11) == 1);
    CHECK(BlastLoss(10) == 0);

    // ---- MA5 Bound Soul: a faded soul 1, a shade 4; +2% a stack, cap 20 --------------------------------------------
    CHECK(kBoundPerSoul == 1 && kBoundPerShade == 4 && kBoundCap == 20 && kBoundPctPerStack == 2);
    CHECK(BoundAfter(0, 1) == 1);
    CHECK(BoundAfter(16, 4) == 20);
    CHECK(BoundAfter(19, 4) == 20);
    CHECK(BoundAfter(20, 1) == 20);
    CHECK(Near(BoundDamageScale(0), 1.f));
    CHECK(Near(BoundDamageScale(10), 1.2f));
    CHECK(Near(BoundDamageScale(20), 1.4f));    // +40% at the cap
    CHECK(Near(BoundDamageScale(30), 1.4f));

    // ---- The build spec's numbers ----------------------------------------------------------------------------------
    CHECK(kDrainFirstMs == 10000 && kDrainEveryMs(false) == 20000 && kDrainEveryMs(true) == 30000);
    CHECK(kDrainCastMs == 2000);
    CHECK(NormalDrainTargets(100.f) == 1);
    CHECK(NormalDrainTargets(50.f) == 1);
    CHECK(NormalDrainTargets(49.9f) == 2);
    CHECK(kCallFirstMs == 15000 && kCallEveryMs == 25000);
    CHECK(kShadeCount(false) == 1 && kShadeCount(true) == 2);
    CHECK(Near(kShadeMinYd, 15.f) && Near(kShadeMaxYd, 25.f));
    CHECK(kShadeSouls == 4 && kShadeWalkInMs == 20000);
    CHECK(kShadeHealth(false) == 12000 && kShadeHealth(true) == 18000);
    CHECK(kShadeVolleyCastMs == 2000 && kShadeVolleyFirstMs < kShadeWalkInMs);
    CHECK(kStormFirstMs == 20000 && kStormEveryMs == 30000);
    CHECK(kStormWaves == 3 && kStormWaveGapMs == 1000 && kStormWarnMs == 1500);
    CHECK(kStormCastMs == 3500);    // the bar covers the last wave's landing (2 s + 1.5 s)
    CHECK(Near(kStormRadius, 4.f) && Near(kStormOffsetYd, 2.f));
    CHECK(Near(kStormRadius - kStormOffsetYd, 2.f));    // the way out of your own marker is 2 yd
    CHECK(kStormRandomSpots(false) == 2 && kStormRandomSpots(true) == 1);
    CHECK(Near(kStormSpotMinFromPlayerYd, 6.f));
    CHECK(Near(kStormPct(false), 20.f) && Near(kStormPct(true), 30.f));
    CHECK(Near(kHealBelowPct, 50.f) && kHealEveryMs == 20000 && kHealCastMs == 3500);
    CHECK(Near(kHealSelfPct(false), 5.f) && Near(kHealSelfPct(true), 10.f));
    CHECK(Near(kHealBurstPct(false), 15.f) && Near(kHealBurstPct(true), 40.f));
    CHECK(kSlowFirstMinMs == 13000 && kSlowFirstMaxMs == 15000 && kSlowEveryMinMs == 20000
        && kSlowEveryMaxMs == 35000);
    CHECK(kCorruptionFirstMinMs == 3000 && kCorruptionFirstMaxMs == 12000 && kCorruptionEveryMinMs == 17000
        && kCorruptionEveryMaxMs == 22000);
    CHECK(Near(kSlowRadius, 20.f) && Near(kCorruptionRadius, 10.f));
    CHECK(kExaminerHealth == 80000);

    // ---- MA6 waves: normal 1 non-tank + 2 spots (3 markers), heroic every player + 1 (6 for five) ------------------
    CHECK(StormPlayersPerWave(false, 5, 4) + kStormRandomSpots(false) == 3);
    CHECK(StormPlayersPerWave(true, 5, 4) + kStormRandomSpots(true) == 6);
    CHECK(StormPlayersPerWave(false, 1, 0) == 0);       // a tank alone: the AI marks the tank (a test)
    CHECK(StormPlayersPerWave(true, 1, 0) == 1);
    // Normal never starts while a drain's souls are down; heroic always may.
    CHECK(!StormMayStart(false, 1));
    CHECK(StormMayStart(false, 0));
    CHECK(StormMayStart(true, 8));
    // The offset marker sits exactly 2 yd from its player, at any bearing.
    for (int i = 0; i < 16; ++i)
    {
        Vec2 const player{ 112.f, -1.f };
        Vec2 const m = OffsetMarker(player, float(i) * 0.39f);
        CHECK(Near(DungeonKit::Distance(player, m), kStormOffsetYd));
    }
    // A falling soul lands as its marker resolves: the launch waits warn - flight.
    CHECK(FallLaunchDelayMs(0.f) == 1500);
    CHECK(FallLaunchDelayMs(10.f) == 1000);
    CHECK(FallLaunchDelayMs(20.f) == 500);
    CHECK(FallLaunchDelayMs(30.f) == 0);
    CHECK(FallLaunchDelayMs(45.f) == 0);

    // ---- The timeline -----------------------------------------------------------------------------------------------
    {
        Timeline t;
        CHECK(t.In(Beat::Drain) == kDrainFirstMs);
        CHECK(t.In(Beat::Call) == kCallFirstMs);
        CHECK(t.In(Beat::Soulstorm) == kStormFirstMs);
        CHECK(!t.Armed(Beat::ShadowHeal) && t.In(Beat::ShadowHeal) == kNever);
        CHECK(!t.Armed(Beat::Slow) && !t.Armed(Beat::Corruption));
        t.Start(14000, 5000);
        CHECK(t.In(Beat::Slow) == 14000 && t.In(Beat::Corruption) == 5000);
        t.Advance(9999);
        CHECK(!t.Due(Beat::Drain));
        t.Advance(1);
        CHECK(t.Due(Beat::Drain));
        t.Done(Beat::Drain, EveryMs(Beat::Drain, false));
        CHECK(t.In(Beat::Drain) == 20000);
        // Shadow Heal: armed at 50%, due at once, then every 20 s; a second Arm keeps the schedule.
        t.Arm(Beat::ShadowHeal);
        CHECK(t.Due(Beat::ShadowHeal));
        t.Done(Beat::ShadowHeal, EveryMs(Beat::ShadowHeal, false));
        t.Arm(Beat::ShadowHeal);
        CHECK(t.In(Beat::ShadowHeal) == kHealEveryMs);
        // A retry comes soon; a disabled beat never comes.
        t.Retry(Beat::Soulstorm, kStormWaitRetryMs);
        CHECK(t.In(Beat::Soulstorm) == kStormWaitRetryMs);
        t.Disable(Beat::Call);
        t.Advance(100000);
        CHECK(!t.Due(Beat::Call) && !t.Armed(Beat::Call));
    }
    // Two minutes: drains at 10, 30, 50, 70, 90, 110 (normal) and 10, 40, 70, 100 (heroic); shades at 15, 40, 65, 90,
    // 115; storms at 20, 50, 80, 110.
    CHECK(Fires(Beat::Drain, false, 120000) == 6);
    CHECK(Fires(Beat::Drain, true, 120000) == 4);
    CHECK(Fires(Beat::Call, false, 120000) == 5);
    CHECK(Fires(Beat::Soulstorm, true, 120000) == 4);
    CHECK(EveryMs(Beat::Slow, false) == kSlowEveryMinMs && EveryMs(Beat::Corruption, true) == kCorruptionEveryMinMs);

    // ---- The Coven's floor ------------------------------------------------------------------------------------------
    CHECK(OnCovenFloor(kMaliciaSpawn.XY()));                    // her apse
    CHECK(OnCovenFloor(kClassroomLandings[std::size_t(Classroom::Coven)].XY()));   // detention lands here
    CHECK(OnCovenFloor({ 112.f, -1.f }));
    CHECK(OnCovenFloor({ 130.f, 6.f }));
    CHECK(!OnCovenFloor({ 140.f, 0.f }));                       // the step to the gate
    CHECK(!OnCovenFloor(kClassroomGatePoints[std::size_t(Classroom::Coven)].XY()));
    CHECK(!OnCovenFloor({ 112.f, 8.f }));                       // against the north wall (inset)
    CHECK(!OnCovenFloor({ 84.f, 3.f }));                        // beside the apse
    CHECK(OnCovenFloor(ClampToCovenFloor({ 150.f, 0.f })));
    CHECK(OnCovenFloor(ClampToCovenFloor({ 112.f, 30.f })));
    CHECK(Near(DungeonKit::Distance(ClampToCovenFloor({ 112.f, -1.f }), { 112.f, -1.f }), 0.f));
    // Every floor point is inside her arena (souls, shades and markers never leave it).
    for (float x = 80.f; x <= 140.f; x += 0.5f)
        for (float y = -11.f; y <= 9.f; y += 0.5f)
            if (OnCovenFloor({ x, y }))
                CHECK(MaliciaArena().Contains({ x, y }, 85.f));

    // ---- Picks ------------------------------------------------------------------------------------------------------
    {
        Lcg rng;
        // Shades: 15-25 yd from her spawn (the apse): the ring reaches the room, and two heroic shades rise apart.
        std::uint32_t found = 0;
        for (int i = 0; i < 200; ++i)
        {
            std::vector<Vec2> picked;
            for (int k = 0; k < 2; ++k)
            {
                std::optional<Vec2> p = PickRingPoint(kMaliciaSpawn.XY(), kShadeMinYd, kShadeMaxYd, picked,
                    kShadeApartYd, rng);
                if (!p)
                    continue;
                ++found;
                float const d = DungeonKit::Distance(*p, kMaliciaSpawn.XY());
                CHECK(d >= kShadeMinYd - 0.01f && d <= kShadeMaxYd + 0.01f);
                CHECK(OnCovenFloor(*p));
                CHECK(FarFromAll(*p, picked, kShadeApartYd));
                picked.push_back(*p);
            }
        }
        CHECK(found == 400);    // never the fallback band from her spot
        // From the room's middle (the tank dragged her) too.
        for (int i = 0; i < 100; ++i)
            CHECK(PickRingPoint({ 112.f, -1.f }, kShadeMinYd, kShadeMaxYd, {}, 0.f, rng).has_value());

        // Souls: 10-15 yd around a drained player, on the floor.
        std::uint32_t souls = 0;
        for (int i = 0; i < 100; ++i)
        {
            std::vector<Vec2> taken;
            for (std::uint32_t k = 0; k < kDrainStacks; ++k)
                if (std::optional<Vec2> p = PickRingPoint({ 112.f, -1.f }, kSoulSpillMinYd, kSoulSpillMaxYd, taken,
                    kSoulsApartYd, rng))
                {
                    ++souls;
                    float const d = DungeonKit::Distance(*p, { 112.f, -1.f });
                    CHECK(d >= kSoulSpillMinYd - 0.01f && d <= kSoulSpillMaxYd + 0.01f);
                    CHECK(OnCovenFloor(*p));
                    taken.push_back(*p);
                }
        }
        CHECK(souls == 400);

        // Soulstorm's random spots: on the floor, 6 yd or more from every player.
        std::vector<Vec2> const players{ { 100.f, -2.f }, { 110.f, 3.f }, { 118.f, -6.f }, { 125.f, 0.f },
            { 95.f, 5.f } };
        for (int i = 0; i < 200; ++i)
        {
            std::optional<Vec2> p = PickRoomPoint(players, kStormSpotMinFromPlayerYd, rng);
            CHECK(p.has_value());
            if (p)
            {
                CHECK(OnCovenFloor(*p));
                CHECK(FarFromAll(*p, players, kStormSpotMinFromPlayerYd));
            }
        }
    }

    // ---- Detention: the Coven (SC 2965) -----------------------------------------------------------------------------
    CHECK(kLessonSouls(false) == 3 && kLessonSouls(true) == 4);
    CHECK(kLessonFadeMs(false) == 10000 && kLessonFadeMs(true) == 6000);
    CHECK(DrainLoss(kSoulStart, kLessonSouls(true)) == 4);       // the student, given 20, loses exactly the lesson's
    CHECK(DrainLoss(kSoulStart, kLessonSouls(false)) == 3);
    CHECK(kLessonSpillMaxYd < kSoulSpillMinYd);
    // User ruling 4: one hit per miss, staggered. The fades come 1.5-2 s apart, the first at the lesson's fade time,
    // and the last inside the 15 s lesson.
    CHECK(kLessonFadeStaggerMs >= 1500 && kLessonFadeStaggerMs <= 2000);
    for (bool const heroic : { false, true })
    {
        CHECK(LessonSoulFadeMs(heroic, 0) == kLessonFadeMs(heroic));
        for (std::uint32_t i = 1; i < kLessonSouls(heroic); ++i)
            CHECK(LessonSoulFadeMs(heroic, i) - LessonSoulFadeMs(heroic, i - 1) >= 1500);
        CHECK(LessonSoulFadeMs(heroic, kLessonSouls(heroic) - 1) + kSoulPollMs < kLessonMs);
    }
    CHECK(LessonSoulFadeMs(false, 2) == 13500 && LessonSoulFadeMs(true, 3) == 11250);
    // Soul Lost follows the lesson's own flag (base point 0 = percent x 100; the engine may take 1 off).
    CHECK(SoulLostBasePoints(false) == 1500 && SoulLostBasePoints(true) == 2500);
    CHECK(Near(SoulLostPctFromBasePoints(2500), 25.f) && Near(SoulLostPctFromBasePoints(2499), 25.f));
    CHECK(Near(SoulLostPctFromBasePoints(1499), 15.f) && Near(SoulLostPctFromBasePoints(1500), 15.f));
    CHECK(Near(SoulLostPctFromBasePoints(0), 0.f) && Near(SoulLostPctFromBasePoints(-1), 0.f));
    {
        // The student lands in her apse: the souls spill around the apse's mouth, in the room.
        Vec2 const landing = kClassroomLandings[std::size_t(Classroom::Coven)].XY();
        Vec2 const center = LessonSpillCenter(landing);
        CHECK(Near(DungeonKit::Distance(center, kApseMouth), 0.f));
        CHECK(OnCovenFloor(center));
        Vec2 const inRoom{ 115.f, 2.f };
        CHECK(Near(DungeonKit::Distance(LessonSpillCenter(inRoom), inRoom), 0.f));
        // The heroic lesson's wide spread (a quarter turn apart at the outer radius) is walkable inside the fade: from
        // the landing to the nearest soul, then the nearest each time, each leg shortened by the 2 yd reach, 7 yd/s.
        float const r = kLessonSpillMaxYd;
        float const chord = r * std::sqrt(2.f);
        float const first = DungeonKit::Distance(landing, center) + r - kSoulRadius;
        float const path = first + 3.f * (chord - kSoulRadius);
        CHECK(path / 7.f * 1000.f < float(kLessonFadeMs(true)) * 0.85f);
        // The souls land on the floor, apart, around that point.
        Lcg rng;
        std::uint32_t ok = 0;
        for (int i = 0; i < 100; ++i)
        {
            std::vector<Vec2> taken;
            for (std::uint32_t k = 0; k < kLessonSouls(true); ++k)
                if (std::optional<Vec2> p = PickRingPoint(center, kLessonSpillMinYd, kLessonSpillMaxYd, taken,
                    kLessonSoulsApartYd, rng))
                {
                    ++ok;
                    CHECK(OnCovenFloor(*p));
                    taken.push_back(*p);
                }
        }
        CHECK(ok == 400);
    }

    return Report("scholo_malicia_test");
}
