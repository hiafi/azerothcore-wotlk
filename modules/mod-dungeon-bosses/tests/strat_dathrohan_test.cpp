// Host tests for DathrohanLogic.h (S7: Grand Crusader Dathrohan and Balnazzar): the slice and the arena, the truth
// roll, the transform rule and the mask's damage clamp, the Sacred Ground and Judgment picks, the cone's carriers,
// the Infernal's stoking Immolation and cap, the Vampiric heal, the never-drifting cadence and the cast queue's order.
#include "DathrohanLogic.h"
#include "DungeonKitFlow.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>

using namespace StratholmeRework;
using namespace StratDathrohan;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation, never in S8's.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    for (std::uint32_t id = SPELL_DB_SACRED_GROUND_BAR; id <= SPELL_BZ_INFERNAL_STRIKE; ++id)
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsGrandLie.Contains(id));
    }
    CHECK(kHardModeCastBase > CAST_MIND_BLAST);
    CHECK(kHardModeTagBase > TAG_BZ_NIGHTMARE);

    // The boss spawns inside his arena; the bounds circle stays inside the leash circle and off the doorway (bearing
    // 306 degrees, 20-27 yd out); his spawn, the brazier and the half-disc spots lie inside the bounds.
    CHECK(DathrohanArena().Contains(kDathrohanSpawn.XY(), kDathrohanSpawn.z));
    CHECK(ArenaFor(BOSS_BALNAZZAR).Contains(kDathrohanSpawn.XY(), kDathrohanSpawn.z));
    CHECK(ArenaFor(BOSS_GRAND_LIE).Contains(kDathrohanSpawn.XY(), kDathrohanSpawn.z));
    CHECK(kBoundsRadius < 22.f);
    CHECK(InBounds(kDathrohanSpawn.XY()));
    CHECK(InBounds(kDathrohanBrazier.XY()));
    for (Vec2 const& p : kDathrohanHalfASpots)
        CHECK(InBounds(p));
    for (Vec2 const& p : kDathrohanHalfBSpots)
        CHECK(InBounds(p));
    CHECK(!InBounds({ 3438.0f, -3076.0f }));        // the entrance
    CHECK(kBoundsZMin <= kDathrohanSpawn.z && kDathrohanSpawn.z <= kBoundsZMax);

    // The truth roll: even odds over [0, 100).
    {
        int truths = 0;
        for (std::uint32_t roll = 0; roll < 100; ++roll)
            truths += RollTruth(roll) == Truth::True ? 1 : 0;
        CHECK(truths == 50);
        CHECK(RollTruth(0) == Truth::True);
        CHECK(RollTruth(99) == Truth::Lie);
    }

    // The transform: at or below 40% in stage 1 only; nothing kills him before Balnazzar.
    CHECK(!ShouldTransform(Stage::Dathrohan, 40.1f));
    CHECK(ShouldTransform(Stage::Dathrohan, 40.f));
    CHECK(!ShouldTransform(Stage::Transform, 10.f));
    CHECK(!ShouldTransform(Stage::Balnazzar, 10.f));
    CHECK(ClampMaskDamage(Stage::Dathrohan, 1000, 999) == 999);
    CHECK(ClampMaskDamage(Stage::Dathrohan, 1000, 1000) == 999);
    CHECK(ClampMaskDamage(Stage::Transform, 1000, 50000) == 999);
    CHECK(ClampMaskDamage(Stage::Dathrohan, 1, 5) == 0);
    CHECK(ClampMaskDamage(Stage::Balnazzar, 1000, 50000) == 50000);
    CHECK(kTransformEntryMs < kTransformStunMs);

    // Numbers (ST build spec): normal / heroic.
    CHECK(Near(kSacredGroundPct.normal, 40.f) && Near(kSacredGroundPct.heroic, 50.f));
    CHECK(kSacredGroundEveryMs.normal == 20000 && kSacredGroundEveryMs.heroic == 15000);
    CHECK(kJudgmentEveryMs.normal == 20000 && kJudgmentEveryMs.heroic == 12000);
    CHECK(Near(kJudgmentSharePct.normal, 90.f) && Near(kJudgmentSharePct.heroic, 120.f));
    CHECK(Near(kJudgmentBurstPct.normal, 40.f) && Near(kJudgmentBurstPct.heroic, 50.f));
    CHECK(kShelterRadius < kEruptionRadius);
    CHECK(kCarrionCones.normal == 1 && kCarrionCones.heroic == 2);
    CHECK(Near(kVampiricPct.normal, 1.f) && Near(kVampiricPct.heroic, 2.f));
    CHECK(Near(kNightmarePct, float(kNightmareMs / kNightmareTickMs) * 5.f));
    CHECK(kNightmarePulses * kNightmarePulseEveryMs == kNightmareMs);
    CHECK(kMeteorFallMs < kInfernoCastMs);

    // DB1 true: Holy Wrath strikes the living non-tanks outside the shelter, never the tank.
    {
        std::vector<Candidate> players{ { 1, true, true }, { 2, false, true }, { 3, false, true },
            { 4, false, false }, { 5, false, true } };
        std::vector<std::uint64_t> const struck = HolyWrathTargets(players, { 2, 5 });
        CHECK(struck.size() == 1 && struck[0] == 3);
        CHECK(HolyWrathTargets(players, { 2, 3, 5 }).empty());
        CHECK(HolyWrathTargets(players, {}).size() == 3);
    }

    // DB2 true: the marked player always shares (once).
    {
        CHECK(JudgmentTakers({ 7, 8 }, Candidate{ 9, false, true }).size() == 3);
        CHECK(JudgmentTakers({ 7, 9 }, Candidate{ 9, false, true }).size() == 2);
        CHECK(JudgmentTakers({ 7 }, Candidate{ 9, false, false }).size() == 1);
        CHECK(JudgmentTakers({}, Candidate{ 9, false, true }).size() == 1);
    }

    // BZ1: the cone's carriers are everyone but its target; alone, nobody.
    {
        std::vector<std::uint64_t> const carriers = ConeCarriers({ 1, 2, 3 }, 2);
        CHECK(carriers.size() == 2);
        CHECK(std::find(carriers.begin(), carriers.end(), std::uint64_t(2)) == carriers.end());
        CHECK(ConeCarriers({ 2 }, 2).empty());
        CarrionSpec const normal = DefaultCarrion(false);
        CarrionSpec const heroic = DefaultCarrion(true);
        CHECK(normal.cones == 1 && heroic.cones == 2);
        CHECK(heroic.secondDelayMs == 1500);
        CHECK(Near(normal.targetPct, 20.f) && Near(normal.othersPct, 40.f));
        CHECK(normal.wardAura == 0);
    }

    // BZ3: Immolation 5% flat on normal; heroic +1% every 5 s, 12% at 35 s and after.
    CHECK(Near(ImmolationPct(false, 40000), 5.f));
    CHECK(Near(ImmolationPct(true, 0), 5.f));
    CHECK(Near(ImmolationPct(true, 4999), 5.f));
    CHECK(Near(ImmolationPct(true, 5000), 6.f));
    CHECK(Near(ImmolationPct(true, 34999), 11.f));
    CHECK(Near(ImmolationPct(true, 35000), 12.f));
    CHECK(Near(ImmolationPct(true, 44000), 12.f));
    CHECK(StokeStacks(false, 30000) == 0);
    CHECK(StokeStacks(true, 35000) == 7);
    CHECK(StokeStacks(true, 44000) == 7);
    CHECK(Near(kImmolationBasePct + float(StokeStacks(true, 44000)) * kImmolationStokePct, kImmolationMaxPct));
    // The cap: two stand; a third rising takes the oldest's place.
    CHECK(InfernalsToCrumble(0) == 0);
    CHECK(InfernalsToCrumble(1) == 0);
    CHECK(InfernalsToCrumble(2) == 1);
    CHECK(InfernalsToCrumble(3) == 2);
    // The 45 s life against the 30 s cadence keeps at most two up without the cap.
    CHECK(kInfernalLifeMs < 2 * kInfernoEveryMs);
    CHECK(DefaultInferno(true).stokes && !DefaultInferno(false).stokes);
    CHECK(kInfernalHealth.normal == 12000 && kInfernalHealth.heroic == 18000);

    // BZ5: 1% of 220,000 is 2,200; 2% of 300,000 is 6,000; never 0.
    CHECK(VampiricHeal(220000, 1.f) == 2200);
    CHECK(VampiricHeal(300000, 2.f) == 6000);
    CHECK(VampiricHeal(600000, 3.f) == 18000);
    CHECK(VampiricHeal(10, 1.f) == 1);

    // The cadence counts from the due time (a waited cast never drifts the beat), never sooner than half a cadence.
    CHECK(NextDue(10000, 10000, 20000) == 30000);
    CHECK(NextDue(10000, 13000, 20000) == 30000);
    CHECK(NextDue(10000, 25000, 20000) == 35000);
    CHECK(FillerWaits(10000, 11000));
    CHECK(!FillerWaits(10000, 12000));

    // The beats: each cast beat has a queue id with its cast time.
    for (std::size_t i = 0; i < kBeatCount; ++i)
    {
        Beat const b = static_cast<Beat>(i);
        CHECK(EveryMs(b, false) >= EveryMs(b, true));
        CHECK(FirstAt(b) > 0);
        if (std::uint32_t const cast = CastOf(b))
        {
            CHECK(CastMsOf(cast) > 0);
            CHECK(BeatOfCast(cast) == b);
        }
    }
    CHECK(!IsStageTwoBeat(Beat::SacredGround) && !IsStageTwoBeat(Beat::Judgment));
    CHECK(IsStageTwoBeat(Beat::CarrionSwarm) && IsStageTwoBeat(Beat::MindBlast));
    CHECK(CastOf(Beat::Judgment) == 0);
    CHECK(PriorityOf(Beat::Inferno) > PriorityOf(Beat::CarrionSwarm));
    CHECK(PriorityOf(Beat::CarrionSwarm) > PriorityOf(Beat::Sleep));
    CHECK(PriorityOf(Beat::Sleep) > PriorityOf(Beat::MindBlast));

    // The queue: the meteor before the cones when both are due; the cast and the spacing then hold the cones.
    {
        DungeonKit::CastQueue queue(kCastSpacingMs);
        queue.Schedule(CAST_CARRION_SWARM, 8000, PriorityOf(Beat::CarrionSwarm));
        queue.Schedule(CAST_INFERNO, 8000, PriorityOf(Beat::Inferno));
        queue.Schedule(CAST_MIND_BLAST, 7000, 0);
        CHECK(queue.Next(8000) == std::optional<std::uint32_t>(CAST_INFERNO));
        queue.Started(CAST_INFERNO, 8000, CastMsOf(CAST_INFERNO));
        CHECK(!queue.Next(11000));
        CHECK(queue.Next(12000) == std::optional<std::uint32_t>(CAST_CARRION_SWARM));
    }

    // Stage 2's first beats come after the Unmasking marks resolve (they count from the stun's end).
    CHECK(kCarrionFirstMs > kUnmaskingMarkMs);
    CHECK(kSleepFirstMs > kCarrionFirstMs);

    return Report("strat_dathrohan_test");
}
