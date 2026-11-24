// Host tests for CrellLogic.h (D9: Forgemaster Gideon Crell, the Armorer).
#include "CrellLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmCrell;

namespace
{
    // A fixed pseudo-random run in [0, 1) (a linear congruential generator): the tests never depend on luck.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>((state >> 8) & 0xFFFFFF) / static_cast<float>(0x1000000);
        }
    };

    bool InArena(Vec2 p)
    {
        return StoreroomArena().Contains(p, kFloorZ);
    }

    // The share of the floor cells' centers (sampled on a 1 yd grid inside each 2 yd cell) a set of circles covers.
    float CoveredShare(std::vector<Vec2> const& centers, float radius)
    {
        int inside = 0;
        int total = 0;
        for (std::size_t r = 0; r < kFloorRows; ++r)
            for (std::size_t c = 0; c < kFloorCols; ++c)
            {
                if (!IsFloorCell(r, c))
                    continue;
                Vec2 const center = CellCenter(r, c);
                for (float dx : { -0.5f, 0.5f })
                    for (float dy : { -0.5f, 0.5f })
                    {
                        Vec2 const p{ center.x + dx, center.y + dy };
                        ++total;
                        for (Vec2 const& q : centers)
                            if (DungeonKit::Distance(p, q) <= radius)
                            {
                                ++inside;
                                break;
                            }
                    }
            }
        return total ? static_cast<float>(inside) / static_cast<float>(total) : 0.f;
    }
}

int main()
{
    // ---- the slice and the wave -------------------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(SmCrell::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmCrell::kSpellSlice.last));
    CHECK(SPELL_AR_SPARK == 212900);
    CHECK(SPELL_AR_RIVET_LOOK == 212923);
    CHECK(SPELL_AR_RIVET_LOOK - SPELL_AR_SPARK == 23);      // twenty-four spells, contiguous from the slice start
    CHECK(IsWave2Boss(BOSS_CRELL));
    CHECK(!kWave2Bound || IsWave2Boss(BOSS_CRELL));

    // ---- the storeroom ----------------------------------------------------------------------------------------------
    // S0's arena and the stub's spot still hold the anvil; his own arena (the outline) holds every spot of the fight.
    CHECK(CrellArena().Contains(kCrellAnvil.XY(), kCrellAnvil.z));
    CHECK(ArenaFor(BOSS_CRELL).Contains(kCrellAnvil.XY(), kCrellAnvil.z));
    for (Point3 const& p : { kAnvil, kTrough, kForge, kCrellSpawn, kArmorCrate, kCounter, kRecruitExit })
    {
        CHECK(IsFloor(p.XY()));
        CHECK(InArena(p.XY()));
        CHECK(std::fabs(p.z - kFloorZ) < 0.01f);
    }
    // The stock crates [DB]: the Weapon Crate in the south lobe, the Armor Crate 11-12 yd from the anvil.
    CHECK(IsFloor({ 1744.f, -358.f }));     // the map's `w` cell (the crate stands on its north edge)
    CHECK(DungeonKit::Distance(kArmorCrate.XY(), kAnvil.XY()) < 12.f);
    // The floor matches the map: the anvil cell is the map's C, the crates' cells are floor, the neck is 6 cells wide.
    std::size_t row = 0;
    std::size_t col = 0;
    CHECK(CellOf(kAnvil.XY(), row, col) && row == 18 && col == 17);
    CHECK(FloorCellCount() == 639);
    CHECK(FloorAreaSqYd() > 2100.f && FloorAreaSqYd() < 2700.f);     // NAVMESH 2,116 for the room without the strip
    // Every floor cell is inside the outline (the arena never cuts the floor off).
    {
        int outside = 0;
        for (std::size_t r = 0; r < kFloorRows; ++r)
            for (std::size_t c = 0; c < kFloorCols; ++c)
                if (IsFloorCell(r, c) && !InArena(CellCenter(r, c)))
                    ++outside;
        CHECK(outside == 0);
    }
    // The stairs to the entry hall (z 19) and the upper hall are off the arena's height band.
    CHECK(!StoreroomArena().Contains(kAnvil.XY(), 19.f));
    // The anvil circle (8 yd) is floor all round (NAVMESH: 203 of 201 sq yd): every 1 yd point of it.
    {
        int points = 0;
        int floor = 0;
        for (float dx = -8.f; dx <= 8.f; dx += 1.f)
            for (float dy = -8.f; dy <= 8.f; dy += 1.f)
                if (dx * dx + dy * dy <= 64.f)
                {
                    ++points;
                    floor += IsFloor({ kAnvil.x + dx, kAnvil.y + dy }) ? 1 : 0;
                }
        CHECK(points > 190 && floor >= points - 2);
    }
    // The trough stands inside the anvil circle (beside the anvil), the forge outside it, the spawn beside the anvil.
    CHECK(DungeonKit::Distance(kTrough.XY(), kAnvil.XY()) <= kAnvilCircleYd);
    CHECK(DungeonKit::Distance(kForge.XY(), kAnvil.XY()) > kAnvilCircleYd);
    CHECK(DungeonKit::Distance(kCrellSpawn.XY(), kAnvil.XY()) < 3.f);
    // The counter is on the crate's side of the anvil, inside the circle; the recruits leave by the east strip.
    CHECK(DungeonKit::Distance(kCounter.XY(), kAnvil.XY()) < 4.f);
    CHECK(DungeonKit::Distance(kCounter.XY(), kArmorCrate.XY()) < DungeonKit::Distance(kAnvil.XY(),
        kArmorCrate.XY()));
    CHECK(kRecruitExit.x > 1800.f);
    // The Hammer's donut reaches every wall: the farthest floor cell is inside its outer edge.
    {
        float farthest = 0.f;
        for (std::size_t r = 0; r < kFloorRows; ++r)
            for (std::size_t c = 0; c < kFloorCols; ++c)
                if (IsFloorCell(r, c))
                    farthest = std::max(farthest, DungeonKit::Distance(CellCenter(r, c), kAnvil.XY()));
        CHECK(farthest + 2.f < kHammerOuterYd);
    }
    // The steam (10 yd round the trough) covers most of the anvil circle: the Quench's lesson is moving him out.
    CHECK(DungeonKit::Distance(kTrough.XY(), kAnvil.XY()) + kAnvilCircleYd > kSteamRadiusYd);

    // ---- AR1 the order ----------------------------------------------------------------------------------------------
    CHECK(kOrderBeat(false).firstMs == 6000 && kOrderBeat(false).everyMs == 30000);
    CHECK(kOrderBeat(true).firstMs == 6000 && kOrderBeat(true).everyMs == 25000);
    CHECK(StepAtMs(Step::Heat, false) == 0 && StepAtMs(Step::Hammer, false) == 5000);
    CHECK(StepAtMs(Step::Quench, false) == 10000 && StepAtMs(Step::Issue, false) == 15000);
    CHECK(StepAtMs(Step::Hammer, true) == 4000 && StepAtMs(Step::Quench, true) == 8000);
    CHECK(StepAtMs(Step::Temper, true) == 10000 && StepAtMs(Step::Issue, true) == 12500);
    CHECK(NextStep(Step::Quench, false) == Step::Issue);
    CHECK(NextStep(Step::Quench, true) == Step::Temper);
    CHECK(NextStep(Step::Temper, true) == Step::Issue);
    CHECK(NextStep(Step::Issue, true) == Step::Done);
    CHECK(StepIsCast(Step::Hammer) && StepIsCast(Step::Temper));
    CHECK(!StepIsCast(Step::Heat) && !StepIsCast(Step::Quench) && !StepIsCast(Step::Issue));
    // The Temper ends exactly at the heroic Issue.
    CHECK(kTemperAtMs + kTemperCastMs == kIssueAtMs(true));
    // The steps never overlap (normal): the Hammer's circle lands before the Quench; the sparks before the Hammer.
    CHECK(kSparkWarnMs <= kHammerAtMs(false));
    CHECK(kHammerAtMs(false) + kHammerCastMs + kHammerFollowUpMs(false) <= kQuenchAtMs(false));
    CHECK(kHammerAtMs(true) + kHammerCastMs + kHammerFollowUpMs(true) <= kQuenchAtMs(true));
    // The Blade ends as the next normal order starts (21 s + 15 s = 36 s).
    CHECK(kOrderBeat(false).firstMs + kIssueAtMs(false) + BladeMs(false, Quality::Standard)
        == kOrderBeat(false).firstMs + kOrderBeat(false).everyMs);
    // The pieces: normal alternates, a Blade first; heroic both every order.
    CHECK(PiecesOf(1, false) == PIECE_BLADE && PiecesOf(2, false) == PIECE_PLATE && PiecesOf(3, false) == PIECE_BLADE);
    CHECK(PiecesOf(1, true) == (PIECE_BLADE | PIECE_PLATE) && PiecesOf(2, true) == (PIECE_BLADE | PIECE_PLATE));
    // The order run: steps in turn, a late step moves the later ones.
    {
        OrderRun run;
        CHECK(!run.Active() && !run.Due(0));
        run.Start(1000, 1, false);
        CHECK(run.Due(1000) && run.Current() == Step::Heat);
        run.Fired(1000);
        CHECK(run.Current() == Step::Hammer && run.DueMs() == 6000 && !run.Due(5999));
        run.Fired(7000);        // the Hammer waited 1 s (he was dashing)
        CHECK(run.DelayMs() == 1000 && run.Current() == Step::Quench && run.DueMs() == 12000);
        run.Fired(12000);
        CHECK(run.Current() == Step::Issue && run.DueMs() == 17000);
        run.Fired(17000);
        CHECK(!run.Active() && run.Current() == Step::Done);
        OrderRun heroic;
        heroic.Start(0, 2, true);
        int steps = 0;
        while (heroic.Active())
        {
            heroic.Fired(heroic.DueMs());
            ++steps;
        }
        CHECK(steps == 5);      // Heat, Hammer, Quench, Temper, Issue
        heroic.Start(0, 3, true);
        heroic.Stop();
        CHECK(!heroic.Active() && !heroic.Due(100000));
    }

    // ---- AR2 Heat ---------------------------------------------------------------------------------------------------
    CHECK(kSparkCount(false) == 10 && kSparkCount(true) == 16);     // section 7 #28 A
    CHECK(kSparkRadiusYd(false) == 5.f && kSparkRadiusYd(true) == 4.f);
    CHECK(kSparkPct(false) == 30.f && kSparkPct(true) == 45.f);
    {
        float coverNormal = 0.f;
        float coverHeroicBurst = 0.f;
        int runs = 0;
        for (std::uint32_t seed : { 1u, 7u, 42u, 1234u, 99999u, 31337u })
        {
            for (bool const heroic : { false, true })
            {
                Lcg rng;
                rng.state = seed;
                std::vector<Vec2> const sparks = PickSparks(kSparkCount(heroic), rng);
                CHECK(sparks.size() == kSparkCount(heroic));
                for (std::size_t i = 0; i < sparks.size(); ++i)
                {
                    CHECK(IsFloor(sparks[i]));
                    for (std::size_t j = i + 1; j < sparks.size(); ++j)
                        CHECK(DungeonKit::Distance(sparks[i], sparks[j]) >= kSparkMinApartYd);
                }
                if (heroic)
                    coverHeroicBurst += CoveredShare(sparks, kSlagBurstRadiusYd);
                else
                    coverNormal += CoveredShare(sparks, kSparkRadiusYd(false));
            }
            ++runs;
        }
        coverNormal /= static_cast<float>(runs);
        coverHeroicBurst /= static_cast<float>(runs);
        // Normal: about a third of the floor marked (the spec's 33%; the floor here includes the east strip).
        CHECK(coverNormal > 0.20f && coverNormal < 0.40f);
        // Heroic: the 16 bursts leave well over a third of the floor (the steam aside) safe (section 7 #28 A, ~35%).
        CHECK(coverHeroicBurst > 0.30f && coverHeroicBurst < 0.65f);
    }
    CHECK(kSlagRadiusYd == 3.f && kSlagPct == 10.f && kSlagBurstRadiusYd == 5.f && kSlagBurstPct == 45.f);
    CHECK(kSlagBurstWarnMs == 2500 && kSlagMaxMs > kOrderBeat(true).everyMs);

    // ---- AR3 Hammer, AR4 Quench -------------------------------------------------------------------------------------
    CHECK(kHammerCastMs == 2500 && kAnvilCircleYd == 8.f);
    CHECK(kHammerFollowUpMs(false) == 2000 && kHammerFollowUpMs(true) == 1500);
    CHECK(kHammerPct(false) == 30.f && kHammerPct(true) == 45.f);
    CHECK(kSteamRadiusYd == 10.f && kSteamMs == 8000 && kSteamPct(false) == 8.f && kSteamPct(true) == 12.f);

    // ---- AR5 Temper, AR-Bl Blade, AR7 Proving Strike ----------------------------------------------------------------
    CHECK(kTemperCastMs == 2500);
    CHECK(BladeMs(false, Quality::Standard) == 15000 && BladeMs(false, Quality::Masterwork) == 15000);
    CHECK(BladeMs(true, Quality::Standard) == 15000);
    CHECK(BladeMs(true, Quality::Flawed) == 8000 && BladeMs(true, Quality::Masterwork) == 25000);
    CHECK(ChainsIn(BladeMs(false, Quality::Standard), false) == 1);
    CHECK(ChainsIn(BladeMs(true, Quality::Flawed), true) == 1);            // flawed: one chain
    CHECK(ChainsIn(BladeMs(true, Quality::Standard), true) == 2);
    CHECK(ChainsIn(BladeMs(true, Quality::Masterwork), true) == 3);        // masterwork: three
    CHECK(StrikeWarnMs(0) == 2000 && StrikeWarnMs(1) == 1000 && StrikeWarnMs(4) == 1000);
    CHECK(StrikePct(0, false) == 30.f && StrikePct(1, false) == 20.f);
    CHECK(StrikePct(0, true) == 45.f && StrikePct(3, true) == 30.f);
    // The normal chain of five: 2 s + 4 x 1 s of markers, about 7 s with the dashes (Build spec).
    CHECK(StrikeWarnMs(0) + 4 * StrikeWarnMs(1) == 6000);
    CHECK(kCleaveAngleDeg == 90.f && kCleaveLengthYd == 8.f && kCleaveEveryMs == 6000);
    CHECK(kCleavePct(false) == 30.f && kCleavePct(true) == 45.f);
    CHECK(kCleaveTankPct(false) == 15.f && kCleaveTankPct(true) == 25.f);
    CHECK(kStrikeWidthYd == 3.f && kStrikeOverrunYd == 5.f && kBladeSpreadYd == 6.f);
    // The dash's end: 5 yd past the target on open floor; stopped at a wall between the lobes.
    {
        Vec2 const from = kAnvil.XY();
        Vec2 const target{ 1776.f, -404.f };
        Vec2 const end = DashEnd(from, target);
        CHECK(IsFloor(end));
        CHECK(std::fabs(DungeonKit::Distance(from, end) - 21.f) < 0.6f);
        // From the south lobe straight north at y -410: the gap between the lobes (x 1762-1764) stops him.
        Vec2 const south{ 1750.f, -410.f };
        Vec2 const stopped = DashEnd(south, { 1780.f, -410.f });
        CHECK(IsFloor(stopped) && stopped.x < 1762.f && stopped.x > 1755.f);
        // Through the neck (y -385) he crosses.
        Vec2 const neck = DashEnd({ 1750.f, -385.f }, { 1775.f, -385.f });
        CHECK(IsFloor(neck) && neck.x > 1778.f);
        // A target on top of him: no line.
        Vec2 const same = DashEnd(from, from);
        CHECK(same.x == from.x && same.y == from.y);
        // Every end of a long random chain stays on the floor and in the arena.
        Lcg rng;
        Vec2 at = from;
        for (int i = 0; i < 200; ++i)
        {
            Vec2 const t = RandomFloorPoint(rng);
            at = DashEnd(at, t);
            CHECK(IsFloor(at));
            CHECK(InArena(at));
        }
    }
    // F-2c M-1: the next line waits for the landing (a 40 yd dash lands after 1,333 ms + 200, a 1 s marker could not
    // cut it), and it starts where he really landed when that is floor, else at the planned end.
    {
        CHECK(DashLandAtMs(10000, 40.f) == 11533);
        CHECK(DashLandAtMs(10000, 0.f) == 10000 + kDashLandSlackMs);
        CHECK(DashLandAtMs(10000, -3.f) == 10000 + kDashLandSlackMs);
        CHECK(DashLandAtMs(0, 60.f) > kStrikeNextWarnMs);
        Vec2 const planned{ 1776.f, -404.f };
        Vec2 const landed{ 1775.2f, -403.6f };
        CHECK(IsFloor(planned) && IsFloor(landed));
        Vec2 const from = ChainFrom(landed, planned);
        CHECK(from.x == landed.x && from.y == landed.y);
        Vec2 const offFloor{ 1763.f, -410.f };     // the gap between the lobes
        CHECK(!IsFloor(offFloor));
        Vec2 const back = ChainFrom(offFloor, planned);
        CHECK(back.x == planned.x && back.y == planned.y);
        // A chain of dashes from the real landings never leaves the floor between two links (no wall crossing):
        // every point along each line is floor.
        Lcg rng;
        Vec2 at = kAnvil.XY();
        for (int i = 0; i < 200; ++i)
        {
            Vec2 const end = DashEnd(at, RandomFloorPoint(rng));
            float const len = DungeonKit::Distance(at, end);
            for (float s = 0.5f; s < len; s += 0.5f)
                CHECK(IsFloor({ at.x + (end.x - at.x) * s / len, at.y + (end.y - at.y) * s / len }));
            at = ChainFrom({ end.x + 0.3f, end.y - 0.3f }, end);     // a landing a hair off the plan
        }
        CHECK(kKillLineCooldownMs == 5000);
    }
    // The chain's order: every player once.
    {
        std::uint32_t s = 7;
        auto below = [&s](std::uint32_t n)
        {
            s = s * 1664525u + 1013904223u;
            return (s >> 8) % n;
        };
        for (std::size_t n : { 0u, 1u, 2u, 5u })
        {
            std::vector<std::size_t> const order = ChainOrder(n, below);
            std::set<std::size_t> seen(order.begin(), order.end());
            CHECK(order.size() == n && seen.size() == n);
            for (std::size_t const i : order)
                CHECK(i < n);
        }
    }

    // ---- AR-Pl Red-Hot Plate, AR8 Popping Rivets --------------------------------------------------------------------
    CHECK(PlateAbsorb(false, Quality::Standard) == 5000 && PlateAbsorb(false, Quality::Flawed) == 5000);
    CHECK(PlateAbsorb(true, Quality::Standard) == 25000);
    CHECK(PlateAbsorb(true, Quality::Flawed) == 12500 && PlateAbsorb(true, Quality::Masterwork) == 50000);
    CHECK(BurnBack(5000) == 1000);          // the spec's "1k across the group"
    CHECK(BurnBack(PlateAbsorb(true, Quality::Masterwork)) == 10000);
    CHECK(BurnBack(1) == 0 && BurnBack(3) == 1);
    CHECK(kArmorTear == 500);
    CHECK(RivetsFor(PlateAbsorb(false, Quality::Standard), false) == 4);
    CHECK(RivetsFor(PlateAbsorb(true, Quality::Standard), true) == 8);
    CHECK(RivetsFor(PlateAbsorb(true, Quality::Flawed), true) == 4);
    CHECK(RivetsFor(PlateAbsorb(true, Quality::Masterwork), true) == 16);
    CHECK(RivetsDue(0, 5000, false) == 0 && RivetsDue(1249, 5000, false) == 0 && RivetsDue(1250, 5000, false) == 1);
    CHECK(RivetsDue(4999, 5000, false) == 3 && RivetsDue(5000, 5000, false) == 4);
    CHECK(RivetsDue(9000, 5000, false) == 4);       // never past the plate's own count
    CHECK(RivetsDue(3125, 25000, true) == 1 && RivetsDue(25000, 25000, true) == 8);
    CHECK(kRivetRadiusYd == 4.f && kRivetWarnMs == 2000 && kRivetPct(false) == 30.f && kRivetPct(true) == 45.f);
    {
        Lcg rng;
        for (int i = 0; i < 300; ++i)
        {
            Vec2 const near = RandomFloorPoint(rng);
            CHECK(IsFloor(near));
            Vec2 const spot = RivetSpot(near, rng);
            CHECK(IsFloor(spot));
            CHECK(DungeonKit::Distance(spot, near) <= kRivetScatterYd + 0.01f);
        }
    }
    // The armor tear's named stock ranks.
    CHECK(IsNamedArmorTear(7386) && IsNamedArmorTear(8647) && IsNamedArmorTear(770) && IsNamedArmorTear(16857));
    CHECK(!IsNamedArmorTear(0) && !IsNamedArmorTear(11597));

    // ---- the fight (Build spec "Tuning") ----------------------------------------------------------------------------
    // Normal: 54k + one plate (5k) at 768 = about 77 s; heroic: 270k + four flawed plates (50k) at 3,145 = about 102 s.
    {
        float const normal = static_cast<float>(kCrellHealthNormal + PlateAbsorb(false, Quality::Standard))
            / static_cast<float>(kEffectiveDpsNormal);
        float const heroic = static_cast<float>(kCrellHealthHeroic + 4 * PlateAbsorb(true, Quality::Flawed))
            / static_cast<float>(kEffectiveDpsHeroic);
        CHECK(normal > 75.f && normal < 79.f);
        CHECK(heroic > 100.f && heroic < 104.f);
    }
    // The beat clock.
    {
        BeatClock clock;
        CHECK(!clock.Due(0));
        clock.Start(0, 6000);
        CHECK(!clock.Due(5999) && clock.Due(6000));
        clock.Fired(6000, 30000);
        CHECK(clock.DueMs() == 36000);
        clock.Fired(100000, 30000);
        CHECK(clock.DueMs() == 130000);
        clock.Stop();
        CHECK(!clock.Due(200000));
    }

    return Report("sm_crell_test");
}
