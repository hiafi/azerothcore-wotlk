// Host tests for BaronHardModeLogic.h (S15: Baron Rivendare's hard mode, the Ultimatum): the slice and the arena, the
// execution's line and percent, Ysida's misses, the Deathcharger lane (length, end, clamp, trail spots, travel) and the
// rot heal's once-a-second book.
#include "BaronHardModeLogic.h"
#include "check.h"

#include <cmath>
#include <vector>

using namespace StratholmeRework;
using namespace StratUltimatum;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool NearV(Vec2 a, Vec2 b, float eps = 0.01f)
    {
        return Near(a.x, b.x, eps) && Near(a.y, b.y, eps);
    }

    void SliceAndIds()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, apart from S14's.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (uint32_t id = SPELL_HM_EXECUTION; id <= SPELL_HM_RISEN_LOOK; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(!StratBaron::kSpellSlice.Contains(id));
        }
        CHECK_EQ(uint32_t(SPELL_HM_RISEN_LOOK - SPELL_HM_EXECUTION + 1), uint32_t(15));
        // Handoff 11 #1: the boss's Condemned is its own id, never the W1 item's 205669.
        CHECK(SPELL_HM_CONDEMNED != 205669u);
        CHECK(SPELL_HM_CONDEMNED_DOT != 205669u);
        // The hard mode's kill slot is its own and fights in its boss's arena.
        CHECK(IsHardModeSlot(BOSS_ULTIMATUM));
        CHECK(!ArenaFor(BOSS_ULTIMATUM).Empty());
        // Tags and casts sit above S14's.
        CHECK(uint32_t(TAG_EXECUTION) >= StratBaron::kHardModeTagBase);
        CHECK(uint32_t(TAG_EXECUTION) > uint32_t(StratBaron::TAG_PARK));
        CHECK(uint32_t(CAST_EXECUTION) >= StratBaron::kHardModeCastBase);
        CHECK(uint32_t(CAST_DEATHCHARGER) > uint32_t(StratBaron::CAST_SHADOW_BOLT));
        CHECK(kCastPriority > 0);       // above the Shadow Bolt filler
        // The entries.
        CHECK_EQ(uint32_t(NPC_ST_YSIDA_RISEN), uint32_t(300589));
        CHECK_EQ(uint32_t(NPC_YSIDA), uint32_t(16031));
    }

    void Tuning()
    {
        // ST: 500k, executions 15 s / 25 s with a 3 s cast, lanes 22 s / 30 s with a 3 s marker, the 45 s rot.
        CHECK_EQ(kHardModeHealth, uint32_t(500000));
        CHECK_EQ(kExecutionFirstMs, uint32_t(15000));
        CHECK_EQ(kExecutionEveryMs, uint32_t(25000));
        CHECK_EQ(kExecutionCastMs, uint32_t(3000));
        CHECK_EQ(kChargeFirstMs, uint32_t(22000));
        CHECK_EQ(kChargeEveryMs, uint32_t(30000));
        CHECK_EQ(kLaneWarnMs, uint32_t(3000));
        CHECK_EQ(kRotLifeMs, uint32_t(45000));
        CHECK_EQ(kTrailLifeMs, uint32_t(20000));
        CHECK_EQ(kRisenHealth, uint32_t(40000));
        CHECK(Near(kLaneWidth, 6.f));
        CHECK(Near(kExecutionLineWidth, 2.f));
        CHECK(Near(kPriceOfDefiancePct, 200.f));
        // A clean 3:30 sees 8 executions (ST HM2): 15 s, then every 25 s.
        uint32_t executions = 0;
        for (uint32_t t = kExecutionFirstMs; t <= 210000; t += kExecutionEveryMs)
            ++executions;
        CHECK_EQ(executions, uint32_t(8));
        // The rot heal: 1% of 500k a second is 5,000 (about 2 s of the fight's DPS on him, ST tuning note).
        CHECK_EQ(RotHealAmount(kHardModeHealth, kRotHealBossPct), uint32_t(5000));
        CHECK_EQ(RotHealAmount(7500, kRotHealServantPct), uint32_t(375));
        CHECK_EQ(RotHealAmount(kRisenHealth, kRotHealServantPct), uint32_t(2000));
        CHECK_EQ(RotHealAmount(10, 1.f), uint32_t(1));
        CHECK_EQ(RotHealAmount(0, 5.f), uint32_t(0));
    }

    void Execution()
    {
        // 30% times (1 + stacks): 30, 60, 90, 120.
        CHECK(Near(ExecutionPct(0), 30.f));
        CHECK(Near(ExecutionPct(1), 60.f));
        CHECK(Near(ExecutionPct(2), 90.f));
        CHECK(Near(ExecutionPct(3), 120.f));

        // The line from him (0, 0) to Ysida (10, 0), 2 yd wide.
        Vec2 const baron{ 0.f, 0.f };
        Vec2 const ysida{ 10.f, 0.f };
        std::vector<Vec2> players{ { 6.f, 0.5f }, { 3.f, -0.9f }, { 8.f, 2.f }, { -1.f, 0.f } };
        auto first = FirstOnLine(baron, ysida, kExecutionLineWidth, players);
        CHECK(first.has_value());
        CHECK_EQ(*first, std::size_t(1));       // the nearest on the line takes it
        // Off the side (1.1 yd), behind him, past her: nobody.
        std::vector<Vec2> off{ { 5.f, 1.1f }, { -0.5f, 0.f }, { 10.5f, 0.f } };
        CHECK(!FirstOnLine(baron, ysida, kExecutionLineWidth, off).has_value());
        // On her spot exactly still counts (the end is inside).
        std::vector<Vec2> atEnd{ { 10.f, 0.f } };
        CHECK(FirstOnLine(baron, ysida, kExecutionLineWidth, atEnd).has_value());
        // A diagonal line.
        std::vector<Vec2> diag{ { 5.f, 5.f }, { 2.f, 2.6f } };
        auto d = FirstOnLine(baron, { 10.f, 10.f }, kExecutionLineWidth, diag);
        CHECK(d.has_value());
        CHECK_EQ(*d, std::size_t(0));           // (2, 2.6) is 0.42 yd across... and nearer
        // (2, 2.6): along = 3.25, across = 0.42 -> on the line, and nearer than (5, 5): it takes it.
        std::vector<Vec2> diag2{ { 5.f, 5.f }, { 2.f, 2.6f } };
        auto d2 = FirstOnLine(baron, { 10.f, 10.f }, kExecutionLineWidth, { diag2[1], diag2[0] });
        CHECK(d2.has_value());
        CHECK_EQ(*d2, std::size_t(0));
        // Degenerate: Ysida on his spot.
        CHECK(!FirstOnLine(baron, baron, kExecutionLineWidth, players).has_value());
        // Empty group.
        CHECK(!FirstOnLine(baron, ysida, kExecutionLineWidth, {}).has_value());

        // Ysida: a third per miss, the third kills her.
        CHECK(Near(YsidaLifeShare(0), 1.f));
        CHECK(Near(YsidaLifeShare(1), 2.f / 3.f));
        CHECK(Near(YsidaLifeShare(2), 1.f / 3.f));
        CHECK(Near(YsidaLifeShare(3), 0.f));
        CHECK(!YsidaFalls(2));
        CHECK(YsidaFalls(3));
        CHECK(YsidaFalls(4));
    }

    void Lane()
    {
        // The drawn lane reaches 2 yd past the target, at least 5 and at most 50 yd.
        CHECK(Near(LaneLength(20.f), 22.f));
        CHECK(Near(LaneLength(1.f), 5.f));
        CHECK(Near(LaneLength(80.f), 50.f));

        // The charge stops 1 yd short of the target, never past the lane.
        Vec2 const start{ 0.f, 0.f };
        CHECK(NearV(ChargeEnd(start, { 20.f, 0.f }, 22.f), { 19.f, 0.f }));
        CHECK(NearV(ChargeEnd(start, { 30.f, 0.f }, 22.f), { 22.f, 0.f }));     // ran on: the lane's end
        CHECK(NearV(ChargeEnd(start, { 0.5f, 0.f }, 5.f), start));             // too close to move
        CHECK(NearV(ChargeEnd(start, start, 5.f), start));

        // Clamp: everything allowed -> the end; a wall at x > 12 -> 12; the first step refused -> the start.
        auto all = [](Vec2) { return true; };
        auto wall = [](Vec2 p) { return p.x <= 12.f; };
        auto none = [](Vec2) { return false; };
        CHECK(NearV(ClampCharge(start, { 19.f, 0.f }, all), { 19.f, 0.f }));
        CHECK(NearV(ClampCharge(start, { 19.f, 0.f }, wall), { 12.f, 0.f }));
        CHECK(NearV(ClampCharge(start, { 19.f, 0.f }, none), start));
        CHECK(NearV(ClampCharge(start, start, all), start));
        // A forbidden patch in the middle (the stock leash near his door) stops him before it, even if the end is fine.
        auto patch = [](Vec2 p) { return p.x < 5.f || p.x > 8.f; };
        CHECK(NearV(ClampCharge(start, { 19.f, 0.f }, patch), { 4.f, 0.f }));
        // A non-integer length ends exactly on the end.
        CHECK(NearV(ClampCharge(start, { 7.5f, 0.f }, all), { 7.5f, 0.f }));

        // Trail spots every 5 yd, the end added unless the last spot is within 2.5 yd of it.
        std::vector<Vec2> t = TrailSpots(start, { 20.f, 0.f });
        CHECK_EQ(t.size(), std::size_t(5));
        CHECK(NearV(t.front(), start));
        CHECK(NearV(t.back(), { 20.f, 0.f }));
        std::vector<Vec2> t2 = TrailSpots(start, { 13.f, 0.f });
        CHECK_EQ(t2.size(), std::size_t(4));    // 0, 5, 10, then 13 (3 yd from 10)
        CHECK(NearV(t2.back(), { 13.f, 0.f }));
        std::vector<Vec2> t3 = TrailSpots(start, { 12.f, 0.f });
        CHECK_EQ(t3.size(), std::size_t(3));    // 0, 5, 10 (12 is within 2.5 of 10)
        CHECK(TrailSpots(start, { 0.5f, 0.f }).empty());
        // Neighbouring spots' 3 yd circles touch (raise reach along the whole lane).
        for (std::size_t i = 1; i < t.size(); ++i)
            CHECK(DungeonKit::Distance(t[i - 1], t[i]) <= kTrailRadius * 2.f + 0.01f);

        // Travel at 42 yd/s.
        CHECK_EQ(ChargeTravelMs(42.f), uint32_t(1000));
        CHECK_EQ(ChargeTravelMs(21.f), uint32_t(500));
        CHECK_EQ(ChargeTravelMs(0.f), uint32_t(0));

        // The Baron's room: a lane clamped by his arena never ends outside it.
        Arena const arena = BaronArena();
        Vec2 const center{ 4032.f, -3348.f };
        auto inArena = [&arena](Vec2 p) { return arena.Contains(p, 115.5f); };
        Vec2 const far{ 4032.f + 40.f, -3348.f };
        Vec2 const clamped = ClampCharge(center, far, inArena);
        CHECK(inArena(clamped));
        CHECK(DungeonKit::Distance(center, clamped) <= 25.f + 0.01f);
        CHECK(DungeonKit::Distance(center, clamped) >= 23.f);
    }

    void HealBook()
    {
        RotHealBook book;
        CHECK(book.Take(1000, 7));
        CHECK(!book.Take(1000, 7));         // a second rot, the same second: once
        CHECK(book.Take(1000, 8));
        CHECK(!book.Take(1999, 7));         // still the same second
        CHECK(book.Take(2000, 7));          // a new second
        CHECK(book.Take(2000, 8));
        book.Reset();
        CHECK(book.Take(2000, 7));
    }
}

int main()
{
    SliceAndIds();
    Tuning();
    Execution();
    Lane();
    HealBook();
    return Report("strat_ultimatum_test");
}
