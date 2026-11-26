// Host tests for GahzrillaLogic.h (D7): the arena and its spots, Storm Builds, Charged, the freeze outcomes, the pool
// strip and the two clocks (Velratha's must-land Spill, Gahz'rilla's fixed Discharge).
#include "GahzrillaLogic.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfPool;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    DungeonKit::WaterSheets PoolOnly()
    {
        DungeonKit::WaterSheets sheets;
        sheets.AddStrip(kPoolAxisFrom, kPoolAxisTo, kPoolSurfaceZ, kPoolHalfWidthYd, PoolRules());
        return sheets;
    }

    // Velratha's clock run for `ms` with every cast taking its full time: the Spill start times.
    std::vector<std::uint64_t> RunVelratha(bool heroic, std::uint32_t ms, std::uint32_t& overlaps)
    {
        VelrathaClock clock;
        clock.Start(heroic);
        std::vector<std::uint64_t> spills;
        std::uint64_t busyUntil = 0;
        overlaps = 0;
        for (std::uint32_t t = 0; t < ms; t += 50)
        {
            clock.Advance(50);
            if (clock.Now() < busyUntil)
                continue;
            VAct const act = clock.Next();
            std::uint32_t cast = 0;
            switch (act)
            {
                case VAct::Spill:
                    cast = Tune::kSpillCastMs(heroic);
                    spills.push_back(clock.Now());
                    break;
                case VAct::Heal:
                    cast = Tune::kHealCastMs(heroic);
                    break;
                case VAct::Frostbolt:
                    cast = Tune::kFrostboltCastMs;
                    break;
                case VAct::None:
                    continue;
            }
            // A cast that is not the Spill never runs past the next Spill's beat.
            if (act != VAct::Spill && clock.Now() + cast > clock.Now() + clock.In(VAct::Spill))
                ++overlaps;
            busyUntil = clock.Now() + cast;
            clock.Done(act, act == VAct::Frostbolt ? Tune::kFrostboltEveryMaxMs : 0);
        }
        return spills;
    }

    struct GRun
    {
        std::vector<std::uint64_t> lands;
        std::uint32_t icicles = 0;
        std::uint32_t freezes = 0;
        std::uint32_t calls = 0;
        std::uint32_t slams = 0;
        std::uint32_t lateBars = 0;
        std::uint32_t intoBar = 0;
    };

    // Gahz'rilla's clock from his arrival, every cast its full time; `icicleEvery` set at `deluge` (0: never).
    GRun RunGahzrilla(bool heroic, std::uint32_t ms, std::uint64_t deluge = 0, std::uint32_t icicleEvery = 0)
    {
        GahzrillaClock clock;
        clock.Start(heroic);
        GRun run;
        std::uint64_t busyUntil = 0;
        bool bar = false;
        for (std::uint32_t t = 0; t < ms; t += 50)
        {
            clock.Advance(50);
            if (deluge && clock.Now() == deluge)
                clock.SetIcicleEvery(icicleEvery);
            if (bar && clock.Now() >= busyUntil)
            {
                run.lands.push_back(clock.Now());
                clock.MarkLanded();
                bar = false;
            }
            if (clock.Now() < busyUntil)
                continue;
            GAct const act = clock.Next();
            std::uint32_t cast = 0;
            switch (act)
            {
                case GAct::Discharge:
                    if (clock.Now() > clock.BarAt())
                        ++run.lateBars;
                    clock.BarStarted();
                    bar = true;
                    busyUntil = clock.Now() + Tune::kDischargeCastMs;
                    continue;
                case GAct::CallTheWaters:
                    cast = Tune::kCallCastMs(heroic);
                    ++run.calls;
                    break;
                case GAct::Icicle:
                    cast = Tune::kIcicleCastMs;
                    ++run.icicles;
                    break;
                case GAct::FreezeSolid:
                    cast = Tune::kFreezeSolidCastMs;
                    ++run.freezes;
                    break;
                case GAct::Slam:
                    ++run.slams;
                    break;
                case GAct::None:
                    continue;
            }
            if (clock.Now() + cast > clock.BarAt())
                ++run.intoBar;
            busyUntil = clock.Now() + cast;
            clock.Done(act, act == GAct::Slam ? Tune::kSlamEveryMaxMs : 0);
        }
        return run;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfPool::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfPool::kSpellSlice.last));
    CHECK(kSpellSlice.Contains(SPELL_GZ_SPILL) && kSpellSlice.Contains(SPELL_GZ_GONG_STRIKE));
    CHECK(SPELL_GZ_SPILL == 214110 && SPELL_GZ_GONG_STRIKE == 214129);

    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(PoolArena().Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
    CHECK(ArenaFor(BOSS_VELRATHA).Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
    CHECK(ArenaFor(BOSS_GAHZRILLA).Contains(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
    CHECK(PoolArena().Contains(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
    CHECK(PoolArena().Contains(kGong.XY(), kGong.z));
    CHECK(PoolArena().Contains(kGahzrillaSummon.XY(), kGahzrillaSummon.z));
    for (Point3 const& disc : kShoreDiscs)
        CHECK(PoolArena().Contains(disc.XY(), disc.z));

    // Storm Builds: SP's heroic table (lands after his arrival) and the normal 30 s.
    std::uint64_t const table[] = { 20000, 40000, 58500, 75500, 91000, 105000, 117500, 128500, 138000, 146000 };
    for (std::uint32_t n = 1; n <= 10; ++n)
        CHECK(DischargeLandsAt(true, n) == table[n - 1]);
    CHECK(DischargeLandsAt(false, 1) == 30000 && DischargeLandsAt(false, 4) == 120000);
    // Section 3.7: back to back from 164 s, never shorter than the bar (section 7 #43 b A).
    CHECK(CycleMs(true, 14) == Tune::kDischargeCastMs && CycleMs(true, 40) == Tune::kDischargeCastMs);
    CHECK(CycleMs(true, 13) == 3500);
    // The meter: empty at the cycle's start, full when the bar starts.
    CHECK(StaticChargeStacks(0, 30000) == 0);
    CHECK(StaticChargeStacks(13500, 30000) == 5);
    CHECK(StaticChargeStacks(27000, 30000) == 10 && StaticChargeStacks(29000, 30000) == 10);
    CHECK(StaticChargeStacks(0, 3000) == 10);

    // Charged: 40% at none, 52% at 3, 80% at 10, 100% at 15, 120% at 20 (SP); normal 50% in water, 0 dry.
    CHECK(Near(DischargePct(true, false, 0), 40.f) && Near(DischargePct(true, true, 3), 52.f));
    CHECK(Near(DischargePct(true, false, 10), 80.f) && Near(DischargePct(true, false, 15), 100.f));
    CHECK(Near(DischargePct(true, false, 20), 120.f));
    CHECK(Near(DischargePct(false, true, 7), 50.f) && Near(DischargePct(false, false, 7), 0.f));

    // Freeze outcomes (GZ13, section 7 #37 A).
    DungeonKit::FreezeResult froze;
    froze.frozen.push_back(3);
    DungeonKit::FreezeResult dry;
    DungeonKit::FreezeResult swim;
    swim.unfreezable = true;
    CHECK(MeltFor(true, froze) == Melt::None && MeltFor(false, dry) == Melt::None);
    CHECK(MeltFor(true, dry) == Melt::AtTarget && MeltFor(true, swim) == Melt::AtShore);
    CHECK(MeltFor(false, swim) == Melt::None);

    // The pool strip: the water and the summon point are in it, it never freezes; the shore spots are dry.
    {
        DungeonKit::WaterSheets sheets = PoolOnly();
        CHECK(sheets.IsWater(kGahzrillaSummon.XY(), kGahzrillaSummon.z));
        CHECK(sheets.IsWater(kGong.XY(), kGong.z));
        CHECK(sheets.IsWater({ 1668.0f, 1190.0f }, kPoolSurfaceZ));       // the water's centroid
        CHECK(!sheets.IsWater(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
        CHECK(!sheets.IsWater(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
        for (Point3 const& disc : kShoreDiscs)
            CHECK(!sheets.IsWater(disc.XY(), disc.z));
        // Every vertex of the water polygon is in the strip.
        for (Vec2 const& v : kPoolWaterPolygon)
            CHECK(sheets.IsWater(v, kPoolSurfaceZ));
        DungeonKit::FreezeResult const r = sheets.FreezeAt({ 1668.0f, 1190.0f }, kPoolSurfaceZ);
        CHECK(r.unfreezable && r.frozen.empty() && MeltFor(true, r) == Melt::AtShore);
        CHECK(sheets.GrowWater(3.f).empty());
        // A swimmer's shore spot is out of the pool, on the shore, on the swimmer's side.
        Vec2 const swimmers[] = { { 1668.0f, 1190.0f }, { 1655.0f, 1180.0f }, { 1683.0f, 1200.0f },
            { 1660.0f, 1186.0f }, { 1675.0f, 1188.0f } };
        for (Vec2 const& p : swimmers)
        {
            Vec2 const shore = ShoreSpotFor(p);
            CHECK(!sheets.IsWater(shore, kPoolSurfaceZ));
            CHECK(PoolArena().Contains(shore, 10.f));
            CHECK(DungeonKit::Distance(p, shore) <= kPoolHalfWidthYd * 2.f + kShoreSpillOutYd + 1.f);
        }
        // A puddle on the shore beside the pool: Icicle freezes it, not the pool (ice wins, the puddle is nearer).
        std::uint32_t const puddle = sheets.Add(kGahzrillaAshore.XY(), kGahzrillaAshore.z, Tune::kPuddleRadiusYd,
            PuddleRules(true, SHEET_SPILL));
        DungeonKit::FreezeResult const p = sheets.FreezeAt(kGahzrillaAshore.XY(), kGahzrillaAshore.z);
        CHECK(p.frozen.size() == 1 && p.frozen[0] == puddle && MeltFor(true, p) == Melt::None);
        CHECK(sheets.ThawInMs(puddle) && *sheets.ThawInMs(puddle) == Tune::kThawMs.heroic);
        // Rising Water skips the frozen puddle and the pool.
        CHECK(sheets.GrowWater(Tune::kRisingWaterYd.heroic).empty());
        sheets.Advance(Tune::kThawMs.heroic);
        CHECK(sheets.Find(puddle)->IsWater() && Near(sheets.Find(puddle)->radius, Tune::kPuddleRadiusYd));
        CHECK(sheets.GrowWater(Tune::kRisingWaterYd.heroic).size() == 1);
        CHECK(Near(sheets.Find(puddle)->radius, Tune::kPuddleRadiusYd + Tune::kRisingWaterYd.heroic));
        // Freeze Solid reaches a puddle whose edge is within 8 yd.
        Vec2 const off{ kGahzrillaAshore.x + 11.f + 7.5f, kGahzrillaAshore.y };
        DungeonKit::FreezeResult const fs = sheets.FreezeWithin(off, kGahzrillaAshore.z, Tune::kFreezeSolidReachYd);
        CHECK(fs.frozen.size() == 1);
    }

    // Velratha: the Spill never late, nothing runs into it.
    for (bool const heroic : { false, true })
    {
        std::uint32_t overlaps = 0;
        std::vector<std::uint64_t> const spills = RunVelratha(heroic, 60000, overlaps);
        CHECK(overlaps == 0);
        CHECK(!spills.empty());
        CHECK(spills.front() == Tune::kSpillFirstMs(heroic));
        for (std::size_t i = 1; i < spills.size(); ++i)
            CHECK(spills[i] - spills[i - 1] == Tune::kSpillEveryMs(heroic));
        CHECK(spills.size() == (heroic ? 7u : 6u));
    }
    // The gong at 30%, once.
    CHECK(!GongDue(30.1f, false) && GongDue(30.f, false) && GongDue(2.f, false) && !GongDue(10.f, true));

    // Gahz'rilla: the Discharge lands on Storm Builds' table, no bar late, nothing runs into a bar.
    {
        GRun const run = RunGahzrilla(true, 150000);
        CHECK(run.lateBars == 0 && run.intoBar == 0);
        CHECK(run.lands.size() == 10);
        for (std::size_t i = 0; i < run.lands.size() && i < 10; ++i)
            CHECK(run.lands[i] == table[i]);
        // About 9 Icicles and 4 Freeze Solids to the kill at about 92 s (SP's space math), more past it.
        CHECK(run.icicles >= 9 && run.freezes >= 4);
        CHECK(run.calls >= 7 && run.slams >= 4);
    }
    {
        GRun const run = RunGahzrilla(false, 120000);
        CHECK(run.lateBars == 0 && run.intoBar == 0);
        CHECK(run.lands.size() == 4 && run.lands[0] == 30000 && run.lands[3] == 120000);
        CHECK(run.calls >= 6);
    }
    // The hard mode's Deluge (GZ23): Icicle every 5 s from the call on.
    {
        GRun const slow = RunGahzrilla(true, 100000);
        GRun const fast = RunGahzrilla(true, 100000, 50000, 5000);
        CHECK(fast.icicles > slow.icicles);
        CHECK(fast.lateBars == 0 && fast.intoBar == 0);
        GahzrillaClock clock;
        clock.Start(true);
        clock.SetIcicleEvery(5000);
        CHECK(clock.IcicleEvery() == 5000);
        clock.SetIcicleEvery(0);
        CHECK(clock.IcicleEvery() == Tune::kIcicleEveryMs);
    }

    // A late beat keeps its grid: max(due + every, now + every / 2).
    {
        Beat b;
        b.Start(1000, 10000);
        b.Done(1000);
        CHECK(b.due == 11000);
        b.Done(30000);
        CHECK(b.due == 35000);
        b.Retry(35000);
        CHECK(!b.Due(35200) && b.Due(35500));
    }

    return Report("zf_gahzrilla_test");
}
