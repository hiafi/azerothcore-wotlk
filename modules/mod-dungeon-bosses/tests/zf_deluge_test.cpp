// Host tests for GahzrillaDelugeLogic.h (D7Hb): the trigger, the rise, the cover over the whole shore, floes (ice wins
// over the flood), the flood's plan, the bots' floe bounds, the pin at the pool's edge, Storm Strikes, and the phase's
// pace on D7's clock (floes alive at a time, SP "about six or seven").
#include "GahzrillaDelugeLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfDeluge;
using DungeonKit::SheetState;
using DungeonKit::WaterSheets;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // The field as it stands once the rise is done: the pool, the risen look sheet and the cover.
    WaterSheets Flooded()
    {
        WaterSheets sheets;
        sheets.AddStrip(ZfPool::kPoolAxisFrom, ZfPool::kPoolAxisTo, ZfPool::kPoolSurfaceZ, ZfPool::kPoolHalfWidthYd,
            ZfPool::PoolRules());
        sheets.Add(kDelugeMiddle, ZfPool::kPoolSurfaceZ, DelugeRadiusAt(Tune::kRiseMs),
            DelugeRules(SHEET_DELUGE, kDelugeZBandYd));
        sheets.AddStrip(kCoverFrom, kCoverTo, kCoverZ, kCoverHalfWidthYd,
            DelugeRules(SHEET_DELUGE_COVER, kCoverZBandYd));
        return sheets;
    }

    // `p` is no further than `yd` from any point of the water polygon's outline (sampled).
    float DistanceToWater(Vec2 p)
    {
        float best = 1e9f;
        std::size_t const n = kPoolWaterPolygon.size();
        for (std::size_t i = 0; i < n; ++i)
        {
            Vec2 const a = kPoolWaterPolygon[i];
            Vec2 const b = kPoolWaterPolygon[(i + 1) % n];
            for (int k = 0; k <= 20; ++k)
            {
                float const t = float(k) / 20.f;
                best = std::min(best, DungeonKit::Distance(p, { a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t }));
            }
        }
        return best;
    }

    struct PaceRun
    {
        std::uint32_t icicles = 0;
        std::uint32_t freezes = 0;
        float meanAlive = 0.f;
        std::uint32_t maxAlive = 0;
        std::uint32_t minAlive = 0;
        std::uint32_t lateBars = 0;
    };

    // D7's heroic clock from his arrival, every cast its full time; the Deluge at `delugeMs` sets Icicle to 5 s; every
    // Icicle and Freeze Solid that lands after it is a floe living kFloeThawMs. Floes alive are sampled every second
    // from `delugeMs + kFloeThawMs` (steady state) to `endMs`.
    PaceRun RunDeluge(std::uint32_t delugeMs, std::uint32_t endMs)
    {
        ZfPool::GahzrillaClock clock;
        clock.Start(true);
        PaceRun run;
        std::vector<std::uint64_t> floeEnds;
        std::uint64_t busyUntil = 0;
        ZfPool::GAct casting = ZfPool::GAct::None;
        bool bar = false;
        std::uint32_t samples = 0;
        std::uint64_t aliveSum = 0;
        run.minAlive = 1000;
        for (std::uint32_t t = 0; t < endMs; t += 50)
        {
            clock.Advance(50);
            std::uint64_t const now = clock.Now();
            if (now == delugeMs)
                clock.SetIcicleEvery(Tune::kIcicleEveryMs);
            if (bar && now >= busyUntil)
            {
                clock.MarkLanded();
                bar = false;
            }
            if (casting != ZfPool::GAct::None && now >= busyUntil)
            {
                if (now > delugeMs)
                    floeEnds.push_back(now + Tune::kFloeThawMs);
                casting = ZfPool::GAct::None;
            }
            if (now % 1000 == 0 && now >= delugeMs + Tune::kFloeThawMs)
            {
                std::uint32_t const alive = std::uint32_t(std::count_if(floeEnds.begin(), floeEnds.end(),
                    [now](std::uint64_t end) { return end > now; }));
                aliveSum += alive;
                ++samples;
                run.maxAlive = std::max(run.maxAlive, alive);
                run.minAlive = std::min(run.minAlive, alive);
            }
            if (now < busyUntil)
                continue;
            ZfPool::GAct const act = clock.Next();
            std::uint32_t cast = 0;
            switch (act)
            {
                case ZfPool::GAct::Discharge:
                    if (now > clock.BarAt())
                        ++run.lateBars;
                    clock.BarStarted();
                    bar = true;
                    busyUntil = now + ZfPool::Tune::kDischargeCastMs;
                    continue;
                case ZfPool::GAct::CallTheWaters:
                    cast = ZfPool::Tune::kCallCastMs.heroic;
                    break;
                case ZfPool::GAct::Icicle:
                    cast = ZfPool::Tune::kIcicleCastMs;
                    casting = act;
                    if (now >= delugeMs)
                        ++run.icicles;
                    break;
                case ZfPool::GAct::FreezeSolid:
                    cast = ZfPool::Tune::kFreezeSolidCastMs;
                    casting = act;
                    if (now >= delugeMs)
                        ++run.freezes;
                    break;
                case ZfPool::GAct::Slam:
                case ZfPool::GAct::None:
                    if (act == ZfPool::GAct::Slam)
                        clock.Done(act, ZfPool::Tune::kSlamEveryMaxMs);
                    continue;
            }
            busyUntil = now + cast;
            clock.Done(act);
        }
        run.meanAlive = samples ? float(aliveSum) / float(samples) : 0.f;
        return run;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfDeluge::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfDeluge::kSpellSlice.last));
    CHECK(kSpellSlice.Contains(SPELL_DELUGE_STORM_STRIKE));
    CHECK(kSpellSlice.Contains(SPELL_DELUGE_STORM_STRIKE_LOOK));
    CHECK(SPELL_DELUGE_STORM_STRIKE == 214190 && SPELL_DELUGE_STORM_STRIKE_LOOK == 214191);
    // a shore disc
    CHECK(PoolArena().Contains(kShoreDiscs[0].XY(), kShoreDiscs[0].z));
    // G1's drill row 10 tags; the packages' sheet kinds start at 10, D7's stay under.
    CHECK(TAG_DELUGE_FLOE == 37 && TAG_DELUGE_STRIKE == 38);
    for (std::uint32_t const kind : { std::uint32_t(SHEET_DELUGE), std::uint32_t(SHEET_DELUGE_COVER),
        std::uint32_t(SHEET_FLOE) })
        CHECK(kind >= 30 && kind < 40 && !IsPoolPuddle(kind));
    CHECK(IsPoolPuddle(ZfPool::SHEET_SPILL) && IsPoolPuddle(ZfPool::SHEET_CALL));
    CHECK(IsPoolPuddle(ZfPool::SHEET_MELTWATER) && IsPoolPuddle(ZfPool::SHEET_GM));
    CHECK(!IsPoolPuddle(ZfPool::SHEET_POOL));

    // The trigger: at or under 40% after the hit, once.
    CHECK(!DelugeDue(40.01f, false));
    CHECK(DelugeDue(40.f, false));
    CHECK(DelugeDue(12.f, false));
    CHECK(!DelugeDue(30.f, true));

    // The rise: V's disc from scale 1 to 8 in ten 0.5 s steps over 5 s, never shrinking.
    CHECK(kRiseSteps == 10);
    CHECK(Near(DelugeRadiusAt(0), 4.8f));
    CHECK(Near(DelugeRadiusAt(Tune::kRiseMs), 38.4f));
    CHECK(Near(DelugeRadiusAt(Tune::kRiseMs * 3), 38.4f));
    CHECK(Near(DelugeRadiusAt(Tune::kRiseMs) / ZfPool::kDiscYdPerScale, Tune::kRiseEndScale));
    {
        float last = 0.f;
        bool grows = true;
        for (std::uint32_t t = 0; t <= Tune::kRiseMs; t += 100)
        {
            grows = grows && DelugeRadiusAt(t) >= last;
            last = DelugeRadiusAt(t);
        }
        CHECK(grows);
        CHECK(!RiseDone(Tune::kRiseMs - 1) && RiseDone(Tune::kRiseMs));
        CHECK(RiseStep(499) == 0 && RiseStep(500) == 1 && RiseStep(60000) == kRiseSteps);
    }

    // The cover: the whole shore and the pool are water once the rise is done, at every height of the arena.
    {
        WaterSheets const sheets = Flooded();
        bool all = true;
        for (Vec2 const& v : kShorePolygon)
            for (float const z : { kShoreZMin, 9.5f, 14.f, kShoreZMax })
                all = all && sheets.IsWater(v, z);
        for (Vec2 const& v : kPoolWaterPolygon)
            all = all && sheets.IsWater(v, ZfPool::kPoolSurfaceZ);
        for (auto const& d : kShoreDiscs)
            all = all && sheets.IsWater(d.XY(), d.z);
        CHECK(all);
        CHECK(sheets.IsWater(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
        CHECK(sheets.IsWater(kGong.XY(), kGong.z));
        // The flood never freezes: an Icicle on it freezes nothing and is no Meltwater (the Deluge adds the floe).
        WaterSheets probe = Flooded();
        DungeonKit::FreezeResult const r = probe.FreezeAt(kGahzrillaAshore.XY(), kGahzrillaAshore.z);
        CHECK(r.frozen.empty() && r.unfreezable && !r.Meltwater());
        DungeonKit::FreezeResult const r2 = probe.FreezeWithin(kShoreDiscs[0].XY(), kShoreDiscs[0].z, 8.f);
        CHECK(r2.frozen.empty() && !r2.Meltwater());
        // Rising Water never grows the flood.
        CHECK(probe.GrowWater(3.f).empty());
        // The look sheet's band covers the shore's floor; it starts on the pool's surface.
        CHECK(ZfPool::kPoolSurfaceZ - kDelugeZBandYd <= kShoreZMin);
        CHECK(ZfPool::kPoolSurfaceZ + kDelugeZBandYd >= kShoreZMax);
    }

    // Floes: ice wins over the flood; they thaw away after 30 s; a swimmer's floe forms at the nearest shore point.
    {
        WaterSheets sheets = Flooded();
        Vec2 const at = kGahzrillaAshore.XY();
        std::uint32_t const floe = sheets.Add(at, kGahzrillaAshore.z, FloeRadius(true),
            FloeRules(), SheetState::Ice);
        CHECK(floe != 0);
        CHECK(!sheets.IsWater(at, kGahzrillaAshore.z));
        CHECK(!sheets.IsWater({ at.x + 7.5f, at.y }, kGahzrillaAshore.z));
        CHECK(sheets.IsWater({ at.x + 8.5f, at.y }, kGahzrillaAshore.z));
        CHECK(sheets.ThawInMs(floe) && *sheets.ThawInMs(floe) == Tune::kFloeThawMs);
        std::vector<DungeonKit::SheetChange> const early = sheets.Advance(Tune::kFloeThawMs - 1);
        CHECK(early.empty() && sheets.Find(floe));
        std::vector<DungeonKit::SheetChange> const gone = sheets.Advance(1);
        CHECK(gone.size() == 1 && gone[0].kind == DungeonKit::SheetChange::Kind::Gone && !sheets.Find(floe));
        CHECK(sheets.IsWater(at, kGahzrillaAshore.z));
        CHECK(Near(FloeRadius(true), 8.f));
        CHECK(Near(FloeRadius(false), 12.f));
        // A swimmer in the pool's middle: the floe at D7's shore spill point, outside the water.
        Vec2 const swim = kDelugeMiddle;
        Vec2 const shore = FloeSpot(swim, true);
        CHECK(!PoolWater().Contains(shore, ZfPool::kPoolSurfaceZ));
        CHECK(PoolArena().Contains(shore, Tune::kShoreZ));
        CHECK(Near(FloeSpot(at, false).x, at.x) && Near(FloeSpot(at, false).y, at.y));
    }

    // The flood's plan: D7's water puddles are swallowed; a Call puddle landed after the flood floods the floe its
    // middle lies on (and only it); an older Call puddle and a Spill flood nothing; ice puddles stay (dry till thawed).
    {
        WaterSheets sheets = Flooded();
        Vec2 const a = kShoreDiscs[3].XY();
        Vec2 const b = kShoreDiscs[0].XY();
        float const z = 9.5f;
        std::uint32_t const spill = sheets.Add({ a.x + 20.f, a.y }, z, 8.f, ZfPool::PuddleRules(true,
            ZfPool::SHEET_SPILL));
        std::uint32_t const oldCall = sheets.Add(b, z, 8.f, ZfPool::PuddleRules(true, ZfPool::SHEET_CALL));
        std::uint32_t const icePuddle = sheets.Add({ a.x, a.y + 20.f }, z, 10.f, ZfPool::PuddleRules(true,
            ZfPool::SHEET_CALL));
        CHECK(sheets.Freeze(icePuddle));
        std::uint32_t const floeA = sheets.Add(a, z, 8.f, FloeRules(), SheetState::Ice);
        std::uint32_t const floeB = sheets.Add(b, z, 12.f, FloeRules(), SheetState::Ice);
        std::uint32_t const floodFrom = MaxSheetId(sheets) + 1;
        FloodPlan const first = PlanFlood(sheets, floodFrom);
        CHECK(first.swallowed.size() == 2 && first.flooded.empty());
        CHECK(std::find(first.swallowed.begin(), first.swallowed.end(), spill) != first.swallowed.end());
        CHECK(std::find(first.swallowed.begin(), first.swallowed.end(), oldCall) != first.swallowed.end());
        for (std::uint32_t const id : first.swallowed)
            sheets.Remove(id);
        std::uint32_t const newCall = sheets.Add({ a.x + 2.f, a.y }, z, 8.f, ZfPool::PuddleRules(true,
            ZfPool::SHEET_CALL));
        std::uint32_t const gm = sheets.Add(b, z, 8.f, ZfPool::PuddleRules(true, ZfPool::SHEET_GM));
        FloodPlan const second = PlanFlood(sheets, floodFrom);
        CHECK(second.swallowed.size() == 2);
        CHECK(second.flooded.size() == 1 && second.flooded[0] == floeA);
        CHECK(std::find(second.swallowed.begin(), second.swallowed.end(), newCall) != second.swallowed.end());
        CHECK(std::find(second.swallowed.begin(), second.swallowed.end(), gm) != second.swallowed.end());
        CHECK(sheets.Find(floeB) && sheets.Find(icePuddle));
        CHECK(MaxSheetId(sheets) == gm);
    }

    // The bots' bounds: every ice circle (floes and frozen puddles), inset 1 yd, never under 1.5 yd; no water, no
    // strip; the ids change when the set does.
    {
        WaterSheets sheets = Flooded();
        CHECK(FloeCircles(sheets).empty());
        std::uint32_t const f1 = sheets.Add(kShoreDiscs[1].XY(), 9.5f, 8.f, FloeRules(), SheetState::Ice);
        std::uint32_t const f2 = sheets.Add(kShoreDiscs[2].XY(), 9.5f, 2.f, FloeRules(), SheetState::Ice);
        std::uint32_t const water = sheets.Add(kShoreDiscs[4].XY(), 9.5f, 8.f, ZfPool::PuddleRules(true,
            ZfPool::SHEET_SPILL));
        std::vector<FloeCircle> const circles = FloeCircles(sheets);
        CHECK(circles.size() == 2);
        CHECK(circles[0].id == f1 && Near(circles[0].radius, 7.f) && Near(circles[0].zBand, Tune::kFloeZBandYd));
        CHECK(circles[1].id == f2 && Near(circles[1].radius, Tune::kFloeBoundsMinYd));
        std::vector<std::uint32_t> const before = IceIds(sheets);
        CHECK(sheets.Freeze(water));
        CHECK(IceIds(sheets) != before && IceIds(sheets).size() == 3);
        // A bot inside a bounds circle stands on dry ice (the inset circle lies inside the sheet).
        bool dry = true;
        for (FloeCircle const& c : FloeCircles(sheets))
            for (float a = 0.f; a < 6.28f; a += 0.5f)
                dry = dry && !sheets.IsWater({ c.center.x + c.radius * std::cos(a), c.center.y
                    + c.radius * std::sin(a) }, c.z);
        CHECK(dry);
    }

    // The pin: every spot on the shore, out of the water, at least 4 yd clear of it and within 6 yd of it (the pool's
    // edge: his 17.8 yd reach covers the first ring of the shore, section 7 #38 A); the spot nearest the fight.
    {
        std::vector<Vec2> const spots = PinSpots();
        CHECK(spots.size() == 24);
        bool ok = true;
        for (Vec2 const& s : spots)
        {
            float const d = DistanceToWater(s);
            ok = ok && PoolArena().Contains(s, Tune::kShoreZ) && !PoolWater().Contains(s, ZfPool::kPoolSurfaceZ)
                && d >= 3.f && d <= 6.5f;
            for (float a = 0.f; a < 6.28f; a += 0.4f)
                ok = ok && !PoolWater().Contains({ s.x + 2.5f * std::cos(a), s.y + 2.5f * std::sin(a) },
                    ZfPool::kPoolSurfaceZ);
        }
        CHECK(ok);
        Vec2 const ashore = PinSpotFor(kGahzrillaAshore.XY());
        CHECK(DungeonKit::Distance(ashore, kGahzrillaAshore.XY()) < 12.f);
        for (auto const& d : kShoreDiscs)
        {
            Vec2 const p = PinSpotFor(d.XY());
            bool nearest = true;
            for (Vec2 const& s : spots)
                nearest = nearest && DungeonKit::Distance(p, d.XY()) <= DungeonKit::Distance(s, d.XY()) + 1e-3f;
            CHECK(nearest);
        }
        std::printf("pin from (1677, 1167): (%.1f, %.1f)\n", ashore.x, ashore.y);
    }

    // Storm Strikes: three a second whatever the tick, 0 to 10 yd from the player.
    {
        StrikeClock clock;
        CHECK(clock.Advance(1000) == 0);
        clock.Start();
        std::uint32_t n = 0;
        for (std::uint32_t t = 0; t < 60000; t += 37)
            n += clock.Advance(37);
        CHECK(n >= 179 && n <= 180);
        StrikeClock fast;
        fast.Start();
        CHECK(fast.Advance(333) == 0 && fast.Advance(1) == 1 && fast.Advance(666) == 2);
        CHECK(fast.Advance(2000) == 6);
        bool within = true;
        Vec2 const p{ 1680.f, 1170.f };
        for (float d = 0.f; d <= 1.f; d += 0.1f)
            for (float a = 0.f; a <= 1.f; a += 0.05f)
                within = within && DungeonKit::Distance(StrikePoint(p, d, a), p) <= Tune::kStrikeScatterYd + 1e-3f;
        CHECK(within);
        CHECK(Near(DungeonKit::Distance(StrikePoint(p, 1.f, 0.25f), p), 10.f));
        CHECK(Near(StrikePoint(p, 0.f, 0.7f).x, p.x) && Near(StrikePoint(p, 0.f, 0.7f).y, p.y));
        // SP's space math: three 3 yd circles a second, each warned 1.5 s: about 130 sq yd under warning at a time.
        float const warned = float(Tune::kStrikesPerSecond) * Tune::kStrikeWarnMs / 1000.f * 3.14159f
            * Tune::kStrikeRadiusYd * Tune::kStrikeRadiusYd;
        CHECK(warned > 120.f && warned < 135.f);
    }

    // The pace on D7's heroic clock: the Deluge at 90 s after his arrival (SP: phase 2 ends near 95 s with Velratha's
    // last 30%), the kill near 150 s (section 3.7). Icicle twice as often; floes alive at a time near SP's 6 or 7.
    {
        PaceRun const run = RunDeluge(90000, 150000);
        CHECK(run.lateBars == 0);
        // Freezes that make floes: D7's clock checks Icicle before Freeze Solid, so at a 5 s Icicle Freeze Solid can
        // starve (the report's request to D7); either way the phase makes at least eight floes a minute.
        CHECK(run.icicles >= 6);
        CHECK(run.icicles + run.freezes >= 8);
        CHECK(run.meanAlive >= 4.f && run.meanAlive <= 9.f);
        std::printf("deluge pace 90-150 s: icicles %u, freeze solids %u, floes alive mean %.1f (min %u, max %u)\n",
            run.icicles, run.freezes, run.meanAlive, run.minAlive, run.maxAlive);
        PaceRun const early = RunDeluge(60000, 150000);
        std::printf("deluge pace 60-150 s: icicles %u, freeze solids %u, floes alive mean %.1f (min %u, max %u)\n",
            early.icicles, early.freezes, early.meanAlive, early.minAlive, early.maxAlive);
        CHECK(early.meanAlive >= 4.f);
    }

    return Report("zf_deluge_test");
}
