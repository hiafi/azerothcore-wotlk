// Host tests for VishasLogic.h (D1: Interrogator Vishas): the slice, the arena and the floor, the phases, the
// Interrogation's pulses, the Branding Iron's facing, the Torment split, the beats.
#include "VishasLogic.h"
#include "check.h"
#include <cmath>
#include <optional>
#include <set>

using namespace ScarletMonasteryRework;
using namespace SmVishas;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation; eight ids, all distinct.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    std::set<std::uint32_t> const spells{ SPELL_VI_INTERROGATION_CAST, SPELL_VI_INTERROGATION, SPELL_VI_ACCOMPLICE,
        SPELL_VI_BRANDING_IRON_CAST, SPELL_VI_BRANDING_IRON, SPELL_VI_PAIN, SPELL_VI_TORMENT,
        SPELL_VI_TORMENT_SHARE };
    CHECK(spells.size() == 8);
    for (std::uint32_t id : spells)
        CHECK(kSpellSlice.Contains(id));
    CHECK(SPELL_VI_INTERROGATION_CAST == 212320);
    CHECK(SPELL_VI_TORMENT_SHARE == 212327);
    // The stock Shadow Word: Pain is outside the slice (a copy is cast, rule 15).
    CHECK(!kSpellSlice.Contains(SPELL_STOCK_SHADOW_WORD_PAIN));

    // Interrogator Vishas spawns kVishasSpawn, inside the arena and on the floor; wave 1.
    CHECK(VishasArena().Contains(kVishasSpawn.XY(), kVishasSpawn.z));
    CHECK(ArenaFor(BOSS_VISHAS).Contains(kVishasSpawn.XY(), kVishasSpawn.z));
    CHECK(OnFloor(kVishasSpawn.XY()));
    CHECK(kVishasSpawn.z >= kFloorZMin && kVishasSpawn.z <= kFloorZMax);
    CHECK(!IsWave2Boss(BOSS_VISHAS));
    // Vorrel stands beside him (his death line reaches him).
    CHECK(DungeonKit::Distance(kVishasSpawn.XY(), kVorrelSpawn.XY()) < kVorrelRange);

    // The floor rectangles sit inside the arena (the bots never plan a spot the leash would call off it).
    for (FloorRect const& r : kFloor)
    {
        CHECK(r.minX < r.maxX && r.minY < r.maxY);
        for (Vec2 corner : { Vec2{ r.minX, r.minY }, Vec2{ r.maxX, r.minY }, Vec2{ r.maxX, r.maxY },
            Vec2{ r.minX, r.maxY } })
            CHECK(VishasArena().Contains(corner, 8.f));
    }
    // The two heroic carrier discs (NM): each 8 yd disc fits one chamber, they are 16+ yd apart (8 yd from each other
    // with room to spare: NM 33 yd), and each has its measured clearance of at least the accomplice radius.
    for (std::size_t i = 0; i < kCarrierDiscs.size(); ++i)
    {
        CHECK(kCarrierDiscRadii[i] >= kAccompliceRadius);
        bool fits = false;
        for (FloorRect const& r : kFloor)
            fits = fits || r.ContainsDisc(kCarrierDiscs[i], kAccompliceRadius);
        CHECK(fits);
    }
    float const apart = DungeonKit::Distance(kCarrierDiscs[0], kCarrierDiscs[1]);
    CHECK(apart >= 2.f * kAccompliceRadius);
    CHECK(Near(apart, 33.f, 0.5f));
    // Torment's beam fits the hall: the back-off end is well inside the longest free line.
    CHECK(kTormentBackOffYd < kLongestFreeLine);

    // Phases: exactly at 70% and 30%, one step at a time, never back.
    CHECK(PhaseFor(100.f) == 1);
    CHECK(PhaseFor(70.01f) == 1);
    CHECK(PhaseFor(70.f) == 2);
    CHECK(PhaseFor(30.01f) == 2);
    CHECK(PhaseFor(30.f) == 3);
    CHECK(PhaseFor(0.f) == 3);
    CHECK(NextPhase(1, 80.f) == 1);
    CHECK(NextPhase(1, 69.f) == 2);
    CHECK(NextPhase(1, 10.f) == 2);     // phase 2's yell and iron first
    CHECK(NextPhase(2, 10.f) == 3);
    CHECK(NextPhase(2, 90.f) == 2);     // a heal never takes a phase back
    CHECK(NextPhase(3, 10.f) == 3);

    // VI1 Interrogation: one target; two in heroic phase 3 only.
    CHECK(InterrogationCount(false, 1) == 1);
    CHECK(InterrogationCount(false, 3) == 1);
    CHECK(InterrogationCount(true, 2) == 1);
    CHECK(InterrogationCount(true, 3) == 2);
    // The target's own damage: 4% a second for 6 s (24%), both difficulties.
    CHECK(Near(kInterrogationPct(false), 4.f) && Near(kInterrogationPct(true), 4.f));
    CHECK(kInterrogationMs / kInterrogationTickMs == 6);
    // Accomplices: 12% / 20% a pulse, a pulse every 2 s, three of them; the first 2 s after the bar.
    CHECK(Near(kAccomplicePct(false), 12.f) && Near(kAccomplicePct(true), 20.f));
    CHECK(AccompliceWarnMs() == 3500);
    CHECK(PassesIn(AccomplicePersistMs(), kAccomplicePulseMs) == 3);
    // The pulses land at 3.5, 5.5 and 7.5 s from the bar's start: the last as the debuff (1.5 + 6 s) ends.
    CHECK(AccompliceWarnMs() + 2 * kAccomplicePulseMs == kInterrogationCastMs + kInterrogationMs);
    CHECK(AccomplicePersistMs() > 2 * kAccomplicePulseMs);
    CHECK(AccomplicePersistMs() <= 2 * kAccomplicePulseMs + 1);
    // The pass clock model: a window of exactly n ticks takes n passes, one more ms takes n + 1.
    CHECK(PassesIn(4000, 2000) == 2);
    CHECK(PassesIn(4001, 2000) == 3);
    CHECK(PassesIn(0, 0) == 1);

    // VI2 Branding Iron: 35% / 45%, 90 degrees, 15 yd, a 2 s bar.
    CHECK(Near(kBrandPct(false), 35.f) && Near(kBrandPct(true), 45.f));
    CHECK(Near(kBrandAngleDeg, 90.f) && Near(kBrandLength, 15.f) && kBrandCastMs == 2000);
    // The facing points at the player's spot (+x north, +y west); a player on top of him keeps his facing.
    CHECK(Near(BrandFacing({ 0.f, 0.f }, { 10.f, 0.f }, 1.f), 0.f));
    CHECK(Near(BrandFacing({ 0.f, 0.f }, { 0.f, 10.f }, 1.f), DungeonKit::kPi / 2.f));
    CHECK(Near(BrandFacing({ 0.f, 0.f }, { -10.f, 0.f }, 1.f), DungeonKit::kPi));
    CHECK(Near(BrandFacing({ 0.f, 0.f }, { 0.f, -10.f }, 1.f), 3.f * DungeonKit::kPi / 2.f));
    CHECK(Near(BrandFacing({ 5.f, 5.f }, { 5.1f, 5.1f }, 1.25f), 1.25f));
    // The cone's facing sends its edge 45 degrees off the target line: the target is in it, a player 46 degrees off
    // the line is not.
    {
        Vec2 const boss{ 0.f, 0.f };
        float const facing = BrandFacing(boss, { 10.f, 0.f }, 0.f);
        CHECK(DungeonKit::InFrontalCone(boss, facing, { 10.f, 0.f }, kBrandAngleDeg, kBrandLength));
        float const off = 46.f * DungeonKit::kPi / 180.f;
        CHECK(!DungeonKit::InFrontalCone(boss, facing, { 10.f * std::cos(off), 10.f * std::sin(off) },
            kBrandAngleDeg, kBrandLength));
        CHECK(!DungeonKit::InFrontalCone(boss, facing, { 16.f, 0.f }, kBrandAngleDeg, kBrandLength));
    }

    // VI3 Pain: 2% / 4% every 3 s for 18 s; first 3-7 s, then 10-14 s.
    CHECK(Near(kPainPct(false), 2.f) && Near(kPainPct(true), 4.f));
    CHECK(kPainMs / kPainTickMs == 6);
    CHECK(kPainFirstMinMs == 3000 && kPainFirstMaxMs == 7000);
    CHECK(kPainEveryMinMs == 10000 && kPainEveryMaxMs == 14000);

    // VI4 Torment: 20% a second split; alone the target dies (160%); with the tank and one more about 6.7% a second
    // (53% over the beam).
    CHECK(Near(TormentTotalPct(1, true), 160.f));
    CHECK(Near(TormentSharePct(3, true), 20.f / 3.f));
    CHECK(Near(TormentTotalPct(3, true), 160.f / 3.f, 0.05f));
    CHECK(Near(TormentTotalPct(5, true), 32.f));
    CHECK(Near(TormentSharePct(0, true), 0.f));
    CHECK(kTormentTicks == 8);
    CHECK(TormentChannelMs() == kTormentWarnMs + kTormentMs);
    // SM-BM's F2 example (G1's torment drill row): 3 yd wide, 1.5 s, 8 s of 1 s passes, back-off 10, tank near 4.
    CHECK(Near(kTormentWidth, 3.f) && kTormentWarnMs == 1500 && kTormentMs == 8000 && kTormentTickMs == 1000);
    CHECK(Near(kTormentBackOffYd, 10.f) && Near(kTormentTankNearYd, 4.f));
    CHECK(kTormentTankNearYd < kTormentBackOffYd);

    // The beats (GY build spec).
    CHECK(kInterrogationBeat.firstMs == 6000 && Cadence(kInterrogationBeat, 1) == 18000);
    CHECK(Cadence(kInterrogationBeat, 2) == 18000 && Cadence(kInterrogationBeat, 3) == 14000);
    CHECK(kBrandBeat.firstMs == 3000 && Cadence(kBrandBeat, 2) == 12000 && Cadence(kBrandBeat, 3) == 10000);
    CHECK(kTormentBeat.firstMs == 10000 && Cadence(kTormentBeat, 1) == 25000 && Cadence(kTormentBeat, 3) == 25000);
    // A Torment channel (9.5 s) never outlasts its cadence: the tools it holds get their turn.
    CHECK(TormentChannelMs() < kTormentBeat.everyMs);

    // BeatClock: due at its time, a fired beat is start to start, never in the past; a stalled beat stays due; a
    // shorter cadence pulls a later beat in but never pushes an earlier one out.
    {
        BeatClock clock;
        CHECK(!clock.Due(0));
        clock.Start(0, 6000);
        CHECK(!clock.Due(5999));
        CHECK(clock.Due(6000));
        CHECK(clock.Due(9000));             // held by a cast: still due
        clock.Fired(9000, 18000);
        CHECK(clock.DueMs() == 24000);      // start to start
        clock.Fired(50000, 18000);
        CHECK(clock.DueMs() == 68000);      // never in the past
        clock.Shorten(60000, 14000);
        CHECK(clock.DueMs() == 68000);      // 8 s away: already sooner than 14 s
        clock.Shorten(50000, 14000);
        CHECK(clock.DueMs() == 64000);      // 18 s away: pulled to 14 s
        clock.Stop();
        CHECK(!clock.Due(100000));
        clock.Shorten(100000, 1000);
        CHECK(!clock.On());
    }

    // A modeled normal kill (GY tuning: 40k at 541 effective group DPS, about 75 s): phase 1 to 70% takes about
    // 22 s, enough for the first Interrogation (6 s) and the second (24 s) to be close; the first Brand comes 3 s
    // after the 70% yell.
    {
        float const effectiveDps = 541.f;
        float const health = 40000.f;
        float const phase2At = health * (1.f - kPhase2Pct / 100.f) / effectiveDps;
        float const phase3At = health * (1.f - kPhase3Pct / 100.f) / effectiveDps;
        CHECK(phase2At > kInterrogationBeat.firstMs / 1000.f);
        CHECK(Near(phase2At, 22.2f, 0.5f));
        CHECK(Near(phase3At, 51.8f, 0.5f));
    }

    // Texts: groups 0-6 on 3983, inside the shared text range; Vorrel's line 0.
    {
        bool vishasRange = false;
        bool vorrelRange = false;
        for (TextRange const& r : kTextRanges)
        {
            if (r.entry == NPC_VISHAS)
                vishasRange = r.first == SAY_PULL && r.last == EMOTE_TORMENT && r.firstNew == EMOTE_CONFESSION;
            if (r.entry == NPC_VORREL)
                vorrelRange = r.first == SAY_VORREL_DEATH && r.last == SAY_VORREL_DEATH;
        }
        CHECK(vishasRange);
        CHECK(vorrelRange);
    }

    // Torment's pick (R-1-GY MN-4): never a live Interrogation carrier while anyone else qualifies, the tank included;
    // with every player a carrier the excluding pick finds nobody and the fallback rule takes one.
    {
        std::vector<DungeonKit::PickCandidate> const group{ { 1, 5.f, true }, { 2, 10.f }, { 3, 12.f }, { 4, 15.f },
            { 5, 20.f } };
        DungeonKit::PickRule const rule = TormentRule({ 2, 4 });
        CHECK(!rule.nonTank);
        std::set<std::uint64_t> picked;
        for (std::uint32_t seed = 0; seed < 50; ++seed)
        {
            std::optional<std::size_t> const at = DungeonKit::PickFrom(group, rule,
                [seed](std::uint32_t n) { return seed % n; });
            CHECK(at.has_value());
            if (at)
                picked.insert(group[*at].id);
        }
        CHECK((picked == std::set<std::uint64_t>{ 1, 3, 5 }));      // the tank can be picked, carriers never
        DungeonKit::PickRule const all = TormentRule({ 1, 2, 3, 4, 5 });
        CHECK(!DungeonKit::PickFrom(group, all, [](std::uint32_t) { return 0u; }).has_value());
        CHECK(DungeonKit::PickFrom(group, TormentRule({}), [](std::uint32_t) { return 0u; }).has_value());
    }

    return Report("sm_vishas_test");
}
