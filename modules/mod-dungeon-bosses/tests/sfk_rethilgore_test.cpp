// Host tests for Rethilgore (WP-S1): RethilgoreLogic.h. Ids, the Lock-Up clock (waits while jailed), the keys, the
// fragment and tainted points against the measured cell block (3 to 6 yd from the door, at least 2 yd apart, in the
// corridor, never in the narrow WNW third for tainted ones), key landings 8 to 12 yd inside the corridor, landing
// points inside their cells, and the cell picks (handoff section 5, Rethilgore suites).
#include "RethilgoreLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace Rethilgore;

namespace
{
    std::uint32_t RollFirst(std::uint32_t)
    {
        return 0;
    }

    std::uint32_t RollLast(std::uint32_t n)
    {
        return n - 1;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(kSlice.first));
        CHECK(kSpellsReservation.Contains(kSlice.last));
        CHECK(kSlice.first <= kSlice.last);
        CHECK(RethilgoreArena().Contains(kRethilgoreSpawn.XY(), kRethilgoreSpawn.z));
        for (std::uint32_t id : { SPELL_LOCK_UP_LEAP, SPELL_LOCK_UP_CAST, SPELL_CELL_THROW_FLASH, SPELL_SOUL_DRAIN,
                 SPELL_SOUL_DRAIN_TICK, SPELL_SOUL_RETURN, SPELL_SOUL_STREAK, SPELL_SOUL_FEAST, SPELL_CELL_KEY,
                 SPELL_TAINTED_FRAGMENT })
            CHECK(kSlice.Contains(id));
        CHECK(kSlice.first == 205910u && kSlice.last == 205929u);
        CHECK(NPC_SFK_CELL_DOOR == 300500u && NPC_SFK_SOUL_FRAGMENT == 300501u && NPC_SFK_TAINTED_FRAGMENT == 300502u);
        CHECK(GO_SFK_CELL_KEY == 301100u);
    }

    void TestTuning()
    {
        // Build spec "Tuning starting points": door 720 / 12k, 5% ticks every 2 s, fragments 6 s, keys at 66 / 33%.
        CHECK(kDoorHealth(false) == 720u && kDoorHealth(true) == 12000u);
        CHECK(kDrainPct == 5.f && kDrainTickMs == 2000u && kDrainStartMs == 1000u);
        CHECK(kFragmentLifeMs == 6000u && kFragmentHealPct == 5.f && kFragmentFeastPct == 5.f);
        CHECK(kLockUpFirstMs == 10000u && kLockUpCooldownMs == 25000u && kLockUpWarnMs == 1500u);
        CHECK(!kTaintedSouls(false) && kTaintedSouls(true));
        CHECK(kTaintedPct == 25.f && kTaintedLifeMs == 40000u && kTaintedRadius == 1.5f);
        // The cap: about 3 fragments per Lock-Up at the door's break time (6 s), the channel starting 1 s in.
        std::uint32_t const breakMs = 6000;
        std::uint32_t const ticks = (breakMs + kDrainStartMs) / kDrainTickMs;
        CHECK(ticks == 3u);
        // Tainted: the second tick of a Lock-Up, heroic only.
        CHECK(!TaintedOnTick(false, 2));
        CHECK(TaintedOnTick(true, 2));
        CHECK(!TaintedOnTick(true, 1) && !TaintedOnTick(true, 3));
    }

    void TestLockUpClock()
    {
        LockUpClock clock;
        clock.Start();
        CHECK(clock.UntilDueMs() == kLockUpFirstMs);
        CHECK(!clock.Update(9999, false));
        CHECK(clock.Update(1, false));                  // 10 s
        clock.Fired();
        CHECK(clock.UntilDueMs() == kLockUpCooldownMs);

        // Due at 35 s while someone is still jailed: it waits.
        CHECK(!clock.Update(kLockUpCooldownMs, true));
        CHECK(clock.Waiting());
        CHECK(!clock.Update(5000, true));
        // Freed: it waits kLockUpAfterFreeMs more, then fires.
        CHECK(!clock.Update(1000, false));
        CHECK(!clock.Update(kLockUpAfterFreeMs - 1001, false));
        CHECK(clock.Update(1, false));
        clock.Fired();

        // A jail that ends long before the next one is due delays nothing.
        CHECK(!clock.Update(8000, true));
        CHECK(!clock.Update(16999, false));
        CHECK(clock.Update(1, false));

        // Retry: soon.
        clock.Retry();
        CHECK(clock.UntilDueMs() == kLockUpRetryMs);
        CHECK(!clock.Update(kLockUpRetryMs - 1, false));
        CHECK(clock.Update(1, false));
    }

    void TestKeys()
    {
        CHECK(NewKeys(100.f, 0) == 0u);
        CHECK(NewKeys(66.5f, 0) == 0u);
        CHECK(NewKeys(66.f, 0) == 1u);
        CHECK(NewKeys(50.f, 1) == 0u);
        CHECK(NewKeys(33.f, 1) == 1u);
        CHECK(NewKeys(20.f, 0) == 2u);                  // one big hit past both: both keys
        CHECK(NewKeys(10.f, 2) == 0u);                  // two per fight
        CHECK(KeyLanding(0).x != KeyLanding(1).x);      // the two keys land apart
        for (std::uint32_t i = 0; i < 2; ++i)
        {
            Point3 const k = KeyLanding(i);
            float const d = DungeonKit::Distance(k.XY(), kRethilgoreSpawn.XY());
            CHECK(d >= 7.9f && d <= 12.f);              // 8 to 12 yd from him (navmesh: 10.4 and 8.2)
            CHECK(CorridorArena().Contains(k.XY(), k.z));
            for (std::size_t c = 0; c < kCellCount; ++c)
                CHECK(!CellArena(CellId(c)).Contains(k.XY(), k.z));
        }
    }

    void TestFragmentPoints()
    {
        for (std::size_t c = 0; c < kCellCount; ++c)
        {
            CellId const cell = CellId(c);
            std::vector<Vec2> const points = FragmentPoints(cell);
            CHECK(!points.empty());
            for (std::size_t i = 0; i < points.size(); ++i)
            {
                float const d = DungeonKit::Distance(points[i], kCellDoors[cell].XY());
                CHECK(d >= 3.f && d <= 6.f);
                CHECK(CorridorArena().Contains(points[i], kCellBlockFloorZ));
                CHECK(DungeonKit::Distance(points[i], kRethilgoreSpawn.XY()) >= 3.4f);
                for (std::size_t j = i + 1; j < points.size(); ++j)
                    CHECK(DungeonKit::Distance(points[i], points[j]) >= kFragmentMinGap);
            }
        }
        CHECK(FragmentPoints(CELL_S).size() == 3u);
        CHECK(FragmentPoints(CELL_M).size() == 2u);
        CHECK(FragmentPoints(CELL_N).size() == 3u);
    }

    void TestTaintedPoints()
    {
        std::vector<Vec2> const narrow = FragmentPoints(CELL_N);
        for (std::size_t c = 0; c < kCellCount; ++c)
        {
            std::vector<Vec2> const points = TaintedPoints(CellId(c));
            CHECK(!points.empty());
            for (Vec2 const& p : points)
            {
                CHECK(CorridorArena().Contains(p, kCellBlockFloorZ));
                // Never in the narrow WNW third in front of the N door.
                CHECK(DungeonKit::Distance(p, kCellDoors[CELL_N].XY()) > 6.f);
                for (Vec2 const& n : narrow)
                    CHECK(DungeonKit::Distance(p, n) > 0.1f);
            }
        }
        CHECK(TaintedPoints(CELL_S).size() == FragmentPoints(CELL_S).size());
        CHECK(TaintedPoints(CELL_N).size() == FragmentPoints(CELL_M).size());
    }

    void TestPickFreePoint()
    {
        std::vector<Vec2> const points = FragmentPoints(CELL_S);
        std::optional<std::size_t> const first = PickFreePoint(points, {}, kFragmentMinGap, RollFirst);
        CHECK(first && *first == 0u);
        std::optional<std::size_t> const last = PickFreePoint(points, {}, kFragmentMinGap, RollLast);
        CHECK(last && *last == points.size() - 1);

        // Occupied points are skipped; three live fragments fill the S cell.
        std::vector<Vec2> occupied{ points[0] };
        std::set<std::size_t> picked;
        for (int i = 0; i < 2; ++i)
        {
            std::optional<std::size_t> const pick = PickFreePoint(points, occupied, kFragmentMinGap, RollFirst);
            CHECK(pick.has_value());
            if (!pick)
                return;
            CHECK(*pick != 0u);
            picked.insert(*pick);
            occupied.push_back(points[*pick]);
        }
        CHECK(picked.size() == 2u);
        CHECK(!PickFreePoint(points, occupied, kFragmentMinGap, RollFirst));

        // The M cell holds two at once: a third tick finds no point.
        std::vector<Vec2> const m = FragmentPoints(CELL_M);
        CHECK(!PickFreePoint(m, m, kFragmentMinGap, RollFirst));
        // A spot 1 yd off a point blocks it (closer than the gap); one 3 yd off does not.
        CHECK(!PickFreePoint({ m[0] }, { { m[0].x + 1.f, m[0].y } }, kFragmentMinGap, RollFirst));
        CHECK(PickFreePoint({ m[0] }, { { m[0].x + 3.f, m[0].y } }, kFragmentMinGap, RollFirst).has_value());
    }

    void TestCells()
    {
        std::set<int> cells;
        for (std::uint32_t roll = 0; roll < 6; ++roll)
            cells.insert(int(CellFromRoll(roll)));
        CHECK(cells.size() == kCellCount);
        CHECK(CellmateOf(CELL_S).entry == NPC_ADAMANT && CellmateOf(CELL_S).textGroup == 5);
        CHECK(CellmateOf(CELL_M).entry == NPC_ASHCROMBE && CellmateOf(CELL_M).textGroup == 5);
        CHECK(CellmateOf(CELL_N).entry == NPC_LANDEN_STILWELL && CellmateOf(CELL_N).textGroup == 0);
        for (std::size_t c = 0; c < kCellCount; ++c)
        {
            CellId const cell = CellId(c);
            Point3 const landing = kCellLandings[cell];
            // The throw lands inside its own cell and no other, and not in the corridor.
            CHECK(CellArena(cell).Contains(landing.XY(), landing.z));
            CHECK(!CorridorArena().Contains(landing.XY(), landing.z));
            for (std::size_t o = 0; o < kCellCount; ++o)
                if (o != c)
                    CHECK(!CellArena(CellId(o)).Contains(landing.XY(), landing.z));
            // A unit kept out of a closed cell is put in the corridor in front of it.
            Vec2 const out = InFrontOfCell(cell);
            CHECK(CorridorArena().Contains(out, kCellBlockFloorZ));
            CHECK(!CellArena(cell).Contains(out, kCellBlockFloorZ));
            // The carrier-only delivery ring reaches the corridor side of the door.
            CHECK(DungeonKit::Distance(out, kCellDoors[cell].XY()) < kDeliveryRadius + 0.01f);
        }
    }

    void TestThrowDelay()
    {
        CHECK(ThrowDelayMs(0.f) == kThrowMinDelayMs);
        CHECK(ThrowDelayMs(25.f) == 1000u + kThrowAfterLandingMs);
        CHECK(ThrowDelayMs(10.f) == 400u + kThrowAfterLandingMs);
    }
}

int main()
{
    TestSliceAndArena();
    TestTuning();
    TestLockUpClock();
    TestKeys();
    TestFragmentPoints();
    TestTaintedPoints();
    TestPickFreePoint();
    TestCells();
    TestThrowDelay();
    return Report("sfk_rethilgore_test");
}
