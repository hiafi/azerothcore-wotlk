// Host tests for RasLogic.h (S4: Ras Frostwhisper (10508)): the slice and the arena (WP-KS's stub), the Chill meter
// and warmth rules (normal and heroic), the fight timeline, the heroic Blizzard drift and the build spec's numbers.
#include "RasLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace ScholomanceRework;
using namespace ScholoRas;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Chill a player builds over `seconds` beats at one warmth.
    std::uint32_t Build(bool warm, bool heroic, std::uint32_t seconds)
    {
        ChillClock clock;
        std::uint32_t stacks = 0;
        for (std::uint32_t i = 0; i < seconds; ++i)
            stacks = ChillAfter(stacks, std::int32_t(clock.Beat(warm, heroic)));
        return stacks;
    }
}

int main()
{
    // ---- KS's stub checks: the slice and the arena ----------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(RasArena().Contains(kRasSpawn.XY(), kRasSpawn.z));
    CHECK(ArenaFor(BOSS_RAS).Contains(kRasSpawn.XY(), kRasSpawn.z));

    // ---- Ids: every spell in the slice, none in S12's ---------------------------------------------------------------
    for (std::uint32_t id : { std::uint32_t(SPELL_RF_CHILL), std::uint32_t(SPELL_RF_DEEP_CHILL),
        std::uint32_t(SPELL_RF_WARMTH), std::uint32_t(SPELL_RF_ENTOMBED), std::uint32_t(SPELL_RF_THAW),
        std::uint32_t(SPELL_RF_FROST_MARK), std::uint32_t(SPELL_RF_CHILL_NOVA),
        std::uint32_t(SPELL_RF_CHILL_NOVA_KNOCK),
        std::uint32_t(SPELL_RF_BLIZZARD_CAST), std::uint32_t(SPELL_RF_BLIZZARD), std::uint32_t(SPELL_RF_BLIZZARD_LOOK),
        std::uint32_t(SPELL_RF_BLIZZARD_DRIFT), std::uint32_t(SPELL_RF_FROSTBOLT_VOLLEY) })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsRasHardMode.Contains(id));
    }
    CHECK(NPC_SC_BLIZZARD_ANCHOR == 300534u);

    // ---- RF2 warmth: two or more allies -----------------------------------------------------------------------------
    CHECK(!IsWarm(0));
    CHECK(!IsWarm(1));
    CHECK(IsWarm(2));
    CHECK(IsWarm(4));
    CHECK(kWarmStackRadius < kWarmRadius);      // a bot inside the Stack is warm by the 8 yd rule

    // ---- RF1 Chill rates (SC tuning: 20 to freeze, 1 a second cold, heroic warm 1 per 3 s) --------------------------
    CHECK(Build(false, false, 20) == 20);       // 20 s alone freezes, normal and heroic
    CHECK(Build(false, true, 20) == 20);
    CHECK(Build(false, false, 19) == 19);
    CHECK(Build(true, false, 600) == 0);        // normal: a warm player builds nothing
    CHECK(Build(true, true, 3) == 1);           // heroic: a third of the cold rate
    CHECK(Build(true, true, 2) == 0);
    CHECK(Build(true, true, 30) == 10);
    CHECK(Build(true, true, 60) == 20);         // a minute warm on heroic freezes: everyone freezes in turn
    {
        // A cold beat between warm ones does not reset the heroic warm count.
        ChillClock clock;
        CHECK(clock.Beat(true, true) == 0);
        CHECK(clock.Beat(false, true) == 1);
        CHECK(clock.Beat(true, true) == 0);
        CHECK(clock.Beat(true, true) == 1);
    }
    CHECK(ChillAfter(0, -5) == 0);
    CHECK(ChillAfter(18, 5) == kChillMax);      // a Nova near the top freezes
    CHECK(ChillAfter(10, 2) == 12);
    CHECK(Freezes(20));
    CHECK(!Freezes(19));
    CHECK(DeepChill(12));
    CHECK(!DeepChill(11));
    CHECK(kChillRunOutAt > kDeepChillAt && kChillRunOutAt < kChillMax);
    CHECK(kChillRunOutRadius > kThawRadius);    // a bot stepping out clears the thaw

    // ---- Numbers against the build spec (N / H, % of the reference row) ---------------------------------------------
    CHECK(kThawPct(false) == 30.f && kThawPct(true) == 45.f);
    CHECK(kThawChill(false) == 0 && kThawChill(true) == 3);
    CHECK(kFrostMarkPct(false) == 40.f && kFrostMarkPct(true) == 55.f);
    CHECK(kFrostMarkChill == 5);
    CHECK(kFrostMarkRadius == 10.f && kFrostMarkWarnMs == 5000);
    CHECK(kBlizzardPct(false) == 8.f && kBlizzardPct(true) == 12.f);
    CHECK(kBlizzardChill == 2 && kBlizzardRadius == 6.f && kBlizzardLifeMs == 12000 && kBlizzardCastMs == 1500);
    CHECK(kBlizzardCount(false) == 1 && kBlizzardCount(true) == 3);
    CHECK(kVolleyPct(false) == 15.f && kVolleyPct(true) == 40.f);
    CHECK(kVolleyChill(false) == 0 && kVolleyChill(true) == 3);
    CHECK(kVolleyCastMs == 3000);
    CHECK(kTombMs == 2000);
    // Normal 1% = 36.7, heroic 41.2 (handoff s3.6): the Volley 551 / 1,648, the Nova 1,468 / 2,266.
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kVolleyPct(false), false) == 551);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kVolleyPct(true), false) == 1648);
    CHECK(DungeonKit::RefFlatValue(3670, 3710, kFrostMarkPct(false), false) == 1468);
    CHECK(DungeonKit::RefFlatValue(4120, 4110, kFrostMarkPct(true), false) == 2266);

    // ---- The timeline: first casts and cooldowns (SC timers) --------------------------------------------------------
    {
        Timeline t;
        CHECK(!t.Due(Beat::Blizzard));
        t.Advance(5999, false);
        CHECK(!t.Due(Beat::Blizzard));
        t.Advance(1, false);
        CHECK(t.Due(Beat::Blizzard));           // Blizzard at 6 s
        CHECK(!t.Due(Beat::FrostMark));
        t.Done(Beat::Blizzard);
        CHECK(t.next[std::size_t(Beat::Blizzard)] == 21000);
        t.Advance(4000, false);
        CHECK(t.Due(Beat::FrostMark));          // Frost Mark at 10 s
        t.Done(Beat::FrostMark);
        CHECK(t.next[std::size_t(Beat::FrostMark)] == 25000);
        t.Advance(5000, false);
        CHECK(t.Due(Beat::Volley));             // the Volley at 15 s
        t.Done(Beat::Volley);
        CHECK(t.next[std::size_t(Beat::Volley)] == 35000);
        CHECK(t.TakeChillBeats() == 15);        // one beat a second
        CHECK(t.TakeChillBeats() == 0);
        t.Advance(1500, false);
        CHECK(t.TakeChillBeats() == 1);
        t.Advance(500, false);
        CHECK(t.TakeChillBeats() == 1);         // the half second carried over

        // A hold (S12's transition) stops the clock: nothing comes due, no Chill beat.
        std::uint32_t const before = t.now;
        t.Advance(10000, true);
        CHECK(t.now == before);
        CHECK(t.TakeChillBeats() == 0);

        // Nobody to target: a short retry, not a full cooldown.
        t.Retry(Beat::FrostMark);
        CHECK(t.next[std::size_t(Beat::FrostMark)] == t.now + kRetryMs);
    }
    CHECK(Timeline::Every(Beat::FrostMark) == 15000);
    CHECK(Timeline::Every(Beat::Blizzard) == 15000);
    CHECK(Timeline::Every(Beat::Volley) == 20000);
    CHECK(kRunOutRefreshMs < kRunOutWarnMs);    // the rolling RunOut never resolves

    // ---- RF6 heroic drift: 18 yd at 1.5 yd/s, inside the arena less the storm's radius ------------------------------
    CHECK(Near(kBlizzardDriftYd, 18.f));
    CHECK(kBlizzardAnchorLifeMs > kBlizzardCastMs + kBlizzardLifeMs);
    // The drift circle is RasArena()'s: its center inside, a point just past its radius outside.
    CHECK(RasArena().Contains(kDriftCenter, 84.f));
    CHECK(!RasArena().Contains({ kDriftCenter.x + kDriftRadius + 0.5f, kDriftCenter.y }, 84.f));
    CHECK(RasArena().Contains({ kDriftCenter.x + kDriftRadius - 0.5f, kDriftCenter.y }, 84.f));
    {
        // From the center, the full 18 yd (inside 28 - 6 = 22).
        Vec2 const end = DriftEnd(kDriftCenter, 0.f, kBlizzardDriftYd, kDriftCenter, kDriftRadius, kDriftMargin);
        CHECK(Near(end.x, kDriftCenter.x + 18.f) && Near(end.y, kDriftCenter.y));
    }
    {
        // From 10 yd east heading east: stops at 22 yd from the center (12 yd of drift).
        Vec2 const start{ kDriftCenter.x + 10.f, kDriftCenter.y };
        Vec2 const end = DriftEnd(start, 0.f, kBlizzardDriftYd, kDriftCenter, kDriftRadius, kDriftMargin);
        CHECK(Near(DungeonKit::Distance(end, kDriftCenter), kDriftRadius - kDriftMargin));
        CHECK(Near(DungeonKit::Distance(end, start), 12.f));
    }
    {
        // Heading west from 10 yd east: crosses the center, the full 18 yd.
        Vec2 const start{ kDriftCenter.x + 10.f, kDriftCenter.y };
        Vec2 const end = DriftEnd(start, DungeonKit::kPi, kBlizzardDriftYd, kDriftCenter, kDriftRadius, kDriftMargin);
        CHECK(Near(end.x, kDriftCenter.x - 8.f) && Near(end.y, kDriftCenter.y));
    }
    {
        // A start outside the inner circle drifts toward the center instead.
        Vec2 const start{ kDriftCenter.x, kDriftCenter.y + 25.f };
        Vec2 const end = DriftEnd(start, DungeonKit::kPi / 2.f, kBlizzardDriftYd, kDriftCenter, kDriftRadius,
            kDriftMargin);
        CHECK(DungeonKit::Distance(end, kDriftCenter) < DungeonKit::Distance(start, kDriftCenter));
        CHECK(Near(end.y, kDriftCenter.y + 7.f));
    }
    // Every heading from points across the study stays inside the inner circle.
    for (float sx = -12.f; sx <= 12.f; sx += 6.f)
        for (float sy = -12.f; sy <= 12.f; sy += 6.f)
            for (int k = 0; k < 16; ++k)
            {
                Vec2 const start{ kDriftCenter.x + sx, kDriftCenter.y + sy };
                Vec2 const end = DriftEnd(start, float(k) * DungeonKit::kTwoPi / 16.f, kBlizzardDriftYd, kDriftCenter,
                    kDriftRadius, kDriftMargin);
                CHECK(DungeonKit::Distance(end, kDriftCenter) <= kDriftRadius - kDriftMargin + 0.01f);
                CHECK(DungeonKit::Distance(end, start) <= kBlizzardDriftYd + 0.01f);
            }

    // The knockback rider's numbers (the DT declaration mirrors them).
    CHECK(kNovaKnockMisc == 120 && kNovaKnockBasePoints == 60);

    return Report("scholo_ras_test");
}
