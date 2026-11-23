// Host tests for ThorneLogic.h (D12: Brother Aldous Thorne, the Gardener).
#include "ThorneLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>

using namespace ScarletMonasteryRework;
using namespace SmThorne;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Is a disc of `r` round `c` all on the dry floor (clear of the pond and the garden's walls)?
    bool DiscOnDry(Vec2 c, float r)
    {
        return c.x - r >= kDryFloor.minX && c.x + r <= kDryFloor.maxX && c.y - r >= kDryFloor.minY
            && c.y + r <= kDryFloor.maxY;
    }

    // Does a disc of `r` round `c` reach the pond?
    bool DiscInPond(Vec2 c, float r)
    {
        float const dx = std::max({ kPond.minX - c.x, 0.f, c.x - kPond.maxX });
        float const dy = std::max({ kPond.minY - c.y, 0.f, c.y - kPond.maxY });
        return std::hypot(dx, dy) < r;
    }
}

int main()
{
    // ---- the slice, the arena, the wave ---------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(SmThorne::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmThorne::kSpellSlice.last));
    CHECK(kSpellSlice.first == 213060 && kSpellSlice.last == 213099);
    CHECK(SPELL_GD_BLESSED_GRAIN == 213060);
    CHECK(SPELL_GD_BLESS_THE_HARVEST == 213077);
    CHECK(IsWave2Boss(BOSS_THORNE));
    CHECK(ThorneArena().Contains(kThorneSpot.XY(), kThorneSpot.z));
    CHECK(ArenaFor(BOSS_THORNE).Contains(kThorneSpot.XY(), kThorneSpot.z));
    CHECK(GardenArena().Contains(kThorneSpawn.XY(), kThorneSpawn.z));
    CHECK(GardenArena().Contains(kThorneSpawn.XY(), kGardenFloorZ));
    // The pond and the far corners of the garden count; the cloister walk (z 28-32) does not.
    CHECK(GardenArena().Contains({ 940.f, 1400.f }, 18.5f));
    CHECK(GardenArena().Contains({ 888.f, 1358.f }, 18.8f));
    CHECK(GardenArena().Contains({ 888.f, 1440.f }, 18.8f));
    CHECK(!GardenArena().Contains({ 908.f, 1399.f }, 30.f));
    CHECK(!GardenArena().Contains({ 1000.f, 1399.f }, 25.f));     // the upper garden past the stairs

    // ---- the spot: section 7 #32 A, on the dry floor, off the pond, where the mechanics fit (NAVMESH) --------------
    CHECK(Near(kThorneSpawn.x, 908.2f) && Near(kThorneSpawn.y, 1399.2f) && Near(kThorneSpawn.z, 19.0f));
    CHECK(kDryFloor.Contains(kThorneSpawn.XY()));
    CHECK(!kPond.Contains(kThorneSpawn.XY()));
    // The doc's spot is in the pond.
    CHECK(kPond.Contains({ 932.f, 1400.f }));
    // Holy Water 10 / 12 yd and the 8 yd blessed ground round him stay out of the pond and on the floor.
    CHECK(!DiscInPond(kThorneSpawn.XY(), kHolyWaterRadiusYd(false)));
    CHECK(!DiscInPond(kThorneSpawn.XY(), kHolyWaterRadiusYd(true)));
    CHECK(DiscOnDry(kThorneSpawn.XY(), kHolyWaterRadiusYd(true)));
    CHECK(DiscOnDry(kThorneSpawn.XY(), kBlessedGroundRadiusYd));
    // NAVMESH's clearance 14.9 yd: every mechanic round him is inside it.
    CHECK(kHolyWaterRadiusYd(true) < 14.9f);
    CHECK(kPruneLengthYd < 14.9f);
    CHECK(kFurrowAheadYd + kFurrowRadiusYd < 14.9f);
    // The furrow at his spawn facing (west): 5 yd ahead, its 3 yd circle on the floor and inside the 8 yd cone.
    Vec2 const furrow = FurrowSpot(kThorneSpawn.XY(), kThorneSpawnFacing);
    CHECK(Near(DungeonKit::Distance(furrow, kThorneSpawn.XY()), kFurrowAheadYd, 0.05f));
    CHECK(furrow.y > kThorneSpawn.y);                          // west is +y
    CHECK(DiscOnDry(furrow, kFurrowRadiusYd));
    CHECK(CutBy(kThorneSpawn.XY(), kThorneSpawnFacing, furrow, 0.f));
    // Every point of the furrow's circle is inside the sweep (the cone holds the whole 3 yd circle 5 yd out).
    for (int i = 0; i < 16; ++i)
    {
        float const a = static_cast<float>(i) * DungeonKit::kTwoPi / 16.f;
        Vec2 const edge{ furrow.x + std::cos(a) * kFurrowRadiusYd, furrow.y + std::sin(a) * kFurrowRadiusYd };
        CHECK(CutBy(kThorneSpawn.XY(), kThorneSpawnFacing, edge, 0.f));
    }
    // Facing every way from his spot the furrow stays on the dry floor (clamped at the pond's edge when he faces it).
    for (int i = 0; i < 36; ++i)
    {
        float const facing = static_cast<float>(i) * DungeonKit::kTwoPi / 36.f;
        Vec2 const f = FurrowSpot(kThorneSpawn.XY(), facing);
        CHECK(kDryFloor.Contains(f));
        CHECK(CutBy(kThorneSpawn.XY(), facing, f, 0.f));
    }
    // Dragged to the pond's edge and facing the water, the furrow is clamped onto the floor.
    Vec2 const clamped = FurrowSpot({ 920.f, 1400.f }, 0.f);
    CHECK(Near(clamped.x, kDryFloor.maxX) && Near(clamped.y, 1400.f));
    // Six normal briars of 4 yd: about 6% of the dry floor (the spec's space math against NAVMESH's 4,844 sq yd).
    float const briarArea = 6.f * DungeonKit::kPi * kBriarRadiusYd * kBriarRadiusYd;
    CHECK(briarArea / 4844.f < 0.07f);
    CHECK(briarArea / DryFloorAreaSqYd() < 0.11f);             // the south block alone: about 10%
    CHECK(DryFloorAreaSqYd() > 2900.f);
    // The moved Centurion: on the dry floor, out of every mechanic round his spot.
    CHECK(kDryFloor.Contains(kMovedCenturionSpot.XY()));
    CHECK(DungeonKit::Distance(kMovedCenturionSpot.XY(), kThorneSpawn.XY()) > 30.f);
    CHECK(kMovedCenturionGuid == 39953);

    // ---- the cycle (the spec's timeline) --------------------------------------------------------------------------
    CHECK(kPruneFirstMs == 5000 && kPruneEveryMs == 10000 && kPruneWarnMs == 2000);
    CHECK(kSowFirstMs == kPruneFirstMs + 1000);                // T+1
    CHECK(kBlessFirstMs == kPruneFirstMs + 4000);              // T+4
    CHECK(kHolyWaterFirstMs == kPruneFirstMs + 12000);         // T+12
    CHECK(kCycleMs == 2 * kPruneEveryMs);
    CHECK(PlantAtMs(0) == 11000);                              // T+6
    CHECK(PruneLandsAtMs(1) - kPruneWarnMs == PlantAtMs(0) + 2000);   // carriers clear in the wind-up (T+8)
    CHECK(SowAtMs(1) == 26000 && PlantAtMs(1) == 31000);
    // Bless the Harvest ends just after the seeds are planted, before the cutting sweep's wind-up.
    CHECK(kBlessFirstMs + kBlessCastMs > PlantAtMs(0));
    CHECK(kBlessFirstMs + kBlessCastMs < PruneLandsAtMs(1) - kPruneWarnMs);
    // Holy Water sits between the furrow's sweep and the next Prune's wind-up; the casts never overlap.
    CHECK(kHolyWaterFirstMs > PruneLandsAtMs(1));
    CHECK(kHolyWaterFirstMs + kHolyWaterCastMs <= PruneLandsAtMs(2) - kPruneWarnMs + 1000);
    CHECK(kBlessFirstMs + kBlessCastMs < kHolyWaterFirstMs);
    CHECK(kHolyWaterFirstMs + kHolyWaterCastMs < SowAtMs(1) + kBlessFirstMs - kSowFirstMs);
    // Sow and Holy Water never overlap (the spec's response count).
    CHECK(kHolyWaterFirstMs > PlantAtMs(0) && kHolyWaterFirstMs + kHolyWaterCastMs < SowAtMs(1));
    // Normal: two sweeps can cut a seed; heroic: one (every cycle).
    for (std::uint32_t n = 0; n < 6; ++n)
    {
        CHECK(SweepsBeforeBloom(n, false) == 2);
        CHECK(SweepsBeforeBloom(n, true) == 1);
    }
    CHECK(BloomMarkerAtMs(false) == 13000 && BloomMarkerAtMs(true) == 8000);
    CHECK(BudAtMs(false) == 7500 && BudAtMs(true) == 5000);
    // The heroic marker opens before the second sweep would land (age 14 s): that sweep is too late.
    CHECK(PruneLandsAtMs(2) - PlantAtMs(0) > kBloomAfterMs(true));
    // The normal second sweep (age 14 s) lands inside the bloom's marker (13-15 s) and still cuts it.
    CHECK(PruneLandsAtMs(2) - PlantAtMs(0) > BloomMarkerAtMs(false));
    CHECK(PruneLandsAtMs(2) - PlantAtMs(0) < kBloomAfterMs(false));
    CHECK(kSowDebuffMs == 5000 && kCarriers(false) == 2 && kCarriers(true) == 3);

    // ---- the build spec's numbers ---------------------------------------------------------------------------------
    CHECK(Near(kPrunePct(false), 30.f) && Near(kPrunePct(true), 45.f));
    CHECK(Near(kPruneTankPct(false), 15.f) && Near(kPruneTankPct(true), 25.f));
    CHECK(Near(kPruneAngleDeg, 120.f) && Near(kPruneLengthYd, 8.f));
    CHECK(Near(kBloomPct(false), 20.f) && Near(kBloomPct(true), 30.f) && Near(kBloomRadiusYd, 6.f));
    CHECK(Near(kBriarRadiusYd, 4.f) && Near(kBriarPct, 10.f) && kBriarCap == 6 && kBriarSlowPct == 50);
    CHECK(Near(kBrambleBriarRadiusYd, 5.f) && Near(kBrambleBriarPct, 15.f));
    CHECK(Near(kHolyWaterRadiusYd(false), 10.f) && Near(kHolyWaterRadiusYd(true), 12.f));
    CHECK(Near(kHolyWaterPct(false), 30.f) && Near(kHolyWaterPct(true), 45.f));
    CHECK(Near(kBlessedGroundRadiusYd, 8.f) && kBlessedGroundMs == 8000 && Near(kBlessedGroundHealPct, 1.f));
    CHECK(kThorneHealthNormal == 60000 && kThorneHealthHeroic == 300000 && kBrambleHealthHeroic == 8000);
    CHECK(std::lround(48.940 * 1226) == 60000);
    // Weakened only below 50% (every hit that applies it).
    CHECK(kPrunePct(true) < 50.f && kBloomPct(true) < 50.f && kHolyWaterPct(true) < 50.f);
    // No hit passes 75% (pollen tops at 20%).
    CHECK(PollenPct(1000) <= 75.f);

    // ---- picks ----------------------------------------------------------------------------------------------------
    // The sweep: 60 degrees either side, 8 yd plus his reach.
    Vec2 const boss{ 0.f, 0.f };
    CHECK(CutBy(boss, 0.f, { 7.9f, 0.f }, 0.f));
    CHECK(!CutBy(boss, 0.f, { 8.1f, 0.f }, 0.f));
    CHECK(CutBy(boss, 0.f, { 8.5f, 0.f }, 1.f));
    CHECK(CutBy(boss, 0.f, { 4.f * std::cos(1.04f), 4.f * std::sin(1.04f) }, 0.f));      // 59.6 degrees
    CHECK(!CutBy(boss, 0.f, { 4.f * std::cos(1.06f), 4.f * std::sin(1.06f) }, 0.f));     // 60.7 degrees
    CHECK(!CutBy(boss, 0.f, { -3.f, 0.f }, 0.f));             // behind him
    CHECK(CutBy(boss, DungeonKit::kPi, { -3.f, 0.f }, 0.f));  // he turned to it: cut
    // The pollen: 1, 2, 3 ... 20, then 20.
    CHECK(Near(PollenPct(0), 0.f) && Near(PollenPct(1), 1.f) && Near(PollenPct(2), 2.f));
    CHECK(Near(PollenPct(20), 20.f) && Near(PollenPct(21), 20.f) && Near(PollenPct(50), 20.f));
    // The spec's kill math: 4 pulses = 10% to everyone; left 20 s (10 pulses) 55%; 30 s (15 pulses) 120% and 15% a
    // pulse; the cap reached at 40 s (20 pulses).
    CHECK(Near(PollenTotalPct(4), 10.f));
    CHECK(Near(PollenTotalPct(10), 55.f));
    CHECK(Near(PollenPct(15), 15.f));
    CHECK(20u * kPollenEveryMs == 40000u);
    // The bramble at 8k (section 10 add sizing C, was 15k): two spec DPS (1,700) kill one in about 4.7 s, 2 pulses
    // (3% to everyone); the bots' 700 in about 11.4 s, 5 pulses (15%; at 15k it was 10 pulses, 55%: the one-mistake
    // wipe). The ramp still reads: every 2 s more of it, a bramble left alone 20 s still 55%.
    CHECK(PulsesBeforeKill(kSpecTwoDps) == 2);
    CHECK(Near(PollenTotalPct(PulsesBeforeKill(kSpecTwoDps)), 3.f));
    CHECK(PulsesBeforeKill(kBotAddDps) == 5);
    CHECK(Near(PollenTotalPct(PulsesBeforeKill(kBotAddDps)), 15.f));
    CHECK(PollenTotalPct(PulsesBeforeKill(kBotAddDps)) < 50.f);
    CHECK(PulsesBeforeKill(0.f) == 0);
    CHECK(PulsesBeforeKill(100000.f) == 0);
    // The briar cap: a seventh withers the oldest.
    CHECK(BriarsToWither(0) == 0 && BriarsToWither(5) == 0);
    CHECK(BriarsToWither(6) == 1 && BriarsToWither(7) == 2);
    // His heal: 1% of 300k = 3,000; of 60k = 600.
    CHECK(BlessedGroundHeal(300000) == 3000);
    CHECK(BlessedGroundHeal(60000) == 600);

    // ---- the clock ------------------------------------------------------------------------------------------------
    Clock clock;
    CHECK(!clock.Due(0));
    clock.Start(0, kPruneFirstMs - kPruneWarnMs);
    CHECK(!clock.Due(2999) && clock.Due(3000));
    clock.Fired(3000, kPruneEveryMs);
    CHECK(clock.DueMs() == 13000);
    clock.Fired(20000, kPruneEveryMs);                         // a little late: the beat holds
    CHECK(clock.DueMs() == 23000);
    clock.Fired(40000, kPruneEveryMs);                         // very late: never in the past
    CHECK(clock.DueMs() == 50000);
    clock.Stop();
    CHECK(!clock.Due(100000) && !clock.On());

    // ---- the texts (S0's range: 300946 0-6) -----------------------------------------------------------------------
    CHECK(SAY_PULL == 0 && SAY_SOW == 1 && SAY_BLESS == 2 && EMOTE_HOLY_WATER == 3 && EMOTE_BLOOM == 4
        && SAY_KILL == 5 && SAY_DEATH == 6);

    return Report("sm_thorne_test");
}
