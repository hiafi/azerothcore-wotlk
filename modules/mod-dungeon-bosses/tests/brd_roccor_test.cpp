// Host tests for RoccorLogic.h (D2: Lord Roccor): the slice, the road and its arena, the walk timing, Rampage's
// lane plan (clipped at the road's end, turned round near it), the lane test, Underfoot, the merge heal, the wave cap,
// the shock cadence and G1's leash numbers.
#include "RoccorLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace BlackrockDepthsRework;
using namespace BrdRoccor;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210750 && kSpellSlice.last == 210779);
        CHECK(SPELL_RO_RAMPAGE_CAST == 210750);
        CHECK(SPELL_RO_HURL_STONE == 210763);
        CHECK(kSpellSlice.Contains(SPELL_RO_HURL_STONE));
        CHECK(NPC_BRD_LOOSED_EARTH == 300780);
        CHECK(IsDarkIron(8891) && IsDarkIron(8892) && IsDarkIron(8909) && IsDarkIron(8921));
        CHECK(!IsDarkIron(NPC_ROCCOR) && !IsDarkIron(NPC_BRD_LOOSED_EARTH) && !IsDarkIron(9319));
    }

    // RO1: the road is the spec's 62-65 yd stretch through his spawn, the stub's spawn sits on it, both ends and the
    // whole line are in the leash frame, and a leg takes about 41 s at 1.5 yd/s.
    void TestRoad()
    {
        CHECK(Near(RoadLength(), 61.8f, 0.2f));
        CHECK(RoadOffset(kRoccorSpawn.XY()) < 0.5f);
        CHECK(RoadS(kRoccorSpawn.XY()) > 30.f && RoadS(kRoccorSpawn.XY()) < 45.f);
        // The spec's line (580, -273) to (637, -249) runs parallel, 8-10 yd away (onto the wall side).
        Vec2 const a = RoadAxis();
        Vec2 const specAxis{ 57.f / std::hypot(57.f, 24.f), 24.f / std::hypot(57.f, 24.f) };
        CHECK(a.x * specAxis.x + a.y * specAxis.y > 0.9995f);
        CHECK(RoadOffset({ 580.f, -273.f }) > 7.f && RoadOffset({ 580.f, -273.f }) < 10.f);
        CHECK(RoadOffset({ 637.f, -249.f }) > 7.f && RoadOffset({ 637.f, -249.f }) < 10.f);
        // The NAVMESH widest discs (588.2, -277.8) r 13.0 and (626.2, -262.8) r 14.6 sit on the line.
        CHECK(RoadOffset({ 588.2f, -277.8f }) < 1.f);
        CHECK(RoadOffset({ 626.2f, -262.8f }) < 1.f);
        CHECK(Near(RoadS(kRoadWest.XY()), 0.f) && Near(RoadS(kRoadEast.XY()), RoadLength()));
        CHECK(Near(RoadPoint(0.f).x, kRoadWest.x) && Near(RoadPoint(RoadLength()).y, kRoadEast.y));
        CHECK(Near(RoadPoint(-5.f).x, kRoadWest.x) && Near(RoadPoint(999.f).x, kRoadEast.x));
        Point3 const mid = RoadPoint(RoadLength() / 2.f);
        CHECK(Near(mid.z, (kRoadWest.z + kRoadEast.z) / 2.f));
        CHECK(LegEnd(1).x == kRoadEast.x && LegEnd(-1).x == kRoadWest.x);
        CHECK(Near(RoadAhead(10.f, 1), RoadLength() - 10.f) && Near(RoadAhead(10.f, -1), 10.f));
        // facings
        CHECK(DirectionOf(RoadFacing(1)) == 1 && DirectionOf(RoadFacing(-1)) == -1);
        CHECK(Near(std::fabs(RoadFacing(1) - RoadFacing(-1)), DungeonKit::kPi, 0.001f));
        CHECK(Near(std::cos(RoadFacing(1)), a.x, 0.001f) && Near(std::sin(RoadFacing(1)), a.y, 0.001f));
        // walk timing: 61.8 / 1.5 = 41.2 s a leg; G1 walks 30 yd in 20 s at the same speed
        CHECK(LegMs() > 41000 && LegMs() < 41400);
        CHECK(Near(kWalkYdS, 30.f / 20.f));
        CHECK(Near(kSpeedWalkRate * 2.5f, kWalkYdS));
        // the arena: the road and everything 39 yd off it, not 45 yd off, not the Ring above
        Arena const arena = RoadArena();
        for (float s = 0.f; s <= RoadLength(); s += 2.f)
        {
            Point3 const p = RoadPoint(s);
            CHECK(arena.Contains(p.XY(), p.z));
            Vec2 const n{ -a.y, a.x };
            CHECK(arena.Contains({ p.x + n.x * 39.f, p.y + n.y * 39.f }, p.z));
            CHECK(arena.Contains({ p.x - n.x * 39.f, p.y - n.y * 39.f }, p.z));
            CHECK(!arena.Contains({ p.x + n.x * 45.f, p.y + n.y * 45.f }, p.z));
            CHECK(!arena.Contains(p.XY(), -54.f));      // the Ring of Law's floor
        }
        CHECK(arena.Contains(kRoccorSpawn.XY(), kRoccorSpawn.z));
        CHECK(!arena.Contains(kGrebmarSpawn.XY(), kGrebmarSpawn.z));
        // the stub's frame check (S0) still holds for the spawn
        CHECK(RoccorArena().Contains(kRoccorSpawn.XY(), kRoccorSpawn.z));
        CHECK(ArenaFor(BOSS_ROCCOR).Contains(kRoccorSpawn.XY(), kRoccorSpawn.z));
        // the boulder floor holds the road and 8 yd round any point of it
        Arena const floor = BoulderFloor();
        for (float s = 0.f; s <= RoadLength(); s += 4.f)
        {
            Point3 const p = RoadPoint(s);
            CHECK(floor.Contains(p.XY(), p.z));
            CHECK(floor.Contains({ p.x + a.y * 8.f, p.y - a.x * 8.f }, p.z));
        }
    }

    // RO3: 20 yd ahead, clipped at the road's end; turned round with less than 10 yd ahead; the lane test.
    void TestRampage()
    {
        float const l = RoadLength();
        // mid road: a full lane either way
        RampagePlan p = PlanRampage(20.f, 1);
        CHECK(p.dir == 1 && !p.turned && Near(p.length, 20.f) && Near(p.toS, 40.f));
        p = PlanRampage(30.f, -1);
        CHECK(p.dir == -1 && !p.turned && Near(p.length, 20.f) && Near(p.toS, 10.f));
        // near the east end: clipped (15 yd left)
        p = PlanRampage(l - 15.f, 1);
        CHECK(p.dir == 1 && !p.turned && Near(p.length, 15.f) && Near(p.toS, l));
        // 10 yd left exactly: still forward, a 10 yd lane
        p = PlanRampage(l - 10.f, 1);
        CHECK(p.dir == 1 && Near(p.length, 10.f));
        // less than 10 left: turned round, a full lane back
        p = PlanRampage(l - 4.f, 1);
        CHECK(p.dir == -1 && p.turned && Near(p.length, 20.f) && Near(p.toS, l - 24.f));
        p = PlanRampage(3.f, -1);
        CHECK(p.dir == 1 && p.turned && Near(p.length, 20.f) && Near(p.toS, 23.f));
        // at the ends and beyond them
        p = PlanRampage(-5.f, -1);
        CHECK(p.dir == 1 && Near(p.fromS, 0.f) && Near(p.length, 20.f));
        p = PlanRampage(l + 5.f, 1);
        CHECK(p.dir == -1 && Near(p.fromS, l) && Near(p.toS, l - 20.f));
        // every plan stays on the road and never leaves a stub
        for (float s = 0.f; s <= l; s += 0.5f)
            for (int dir : { 1, -1 })
            {
                RampagePlan const q = PlanRampage(s, dir);
                CHECK(q.toS >= -0.01f && q.toS <= l + 0.01f);
                CHECK(q.length >= kRampageMinLaneYd - 0.01f && q.length <= kRampageLengthYd + 0.01f);
                CHECK(Near(std::fabs(q.toS - q.fromS), q.length, 0.01f));
            }
        // the lane: 20 x 8 ahead of him along the road
        Vec2 const o = RoadPoint(10.f).XY();
        float const f = RoadFacing(1);
        Vec2 const a = RoadAxis();
        Vec2 const n{ -a.y, a.x };
        auto at = [&](float along, float across)
        {
            return Vec2{ o.x + a.x * along + n.x * across, o.y + a.y * along + n.y * across };
        };
        CHECK(InLane(o, f, 20.f, 8.f, at(1.f, 0.f)));
        CHECK(InLane(o, f, 20.f, 8.f, at(19.5f, 3.9f)));
        CHECK(InLane(o, f, 20.f, 8.f, at(10.f, -3.9f)));
        CHECK(!InLane(o, f, 20.f, 8.f, at(10.f, 4.2f)));
        CHECK(!InLane(o, f, 20.f, 8.f, at(20.5f, 0.f)));
        CHECK(!InLane(o, f, 20.f, 8.f, at(-1.f, 0.f)));      // behind him
        CHECK(InLane(o, f, 20.f, 8.f, at(-1.f, 0.f), 1.5f)); // a body's margin
        CHECK(InLane(o, f, 20.f, 8.f, at(10.f, 5.f), 1.5f));
        // the lane fits the road: 8 yd against a road at least 21.5 yd wide (NAVMESH 1.2), G1's 20 x 8 x 2.5 s
        CHECK(kRampageWidthYd <= 21.5f / 2.f);
        CHECK(Near(kRampageLengthYd, 20.f) && Near(kRampageWidthYd, 8.f) && kRampageWarnMs == 2500);
        CHECK(Near(kRampagePct(false), 40.f) && Near(kRampagePct(true), 60.f));
        CHECK(kRampageEveryMs(false) == 20000 && kRampageEveryMs(true) == 15000 && kRampageFirstMs == 12000);
        // the surge: 20 yd in under a second, done well inside the tank's grace
        CHECK(kRampageLengthYd / kSurgeYdS < 1.f);
        CHECK(kSurgeLeashGraceMs >= static_cast<std::uint32_t>((kRampageLengthYd / 7.f) * 1000.f));
    }

    // RO2 / heroic merge / RO4 cap / RO6 cadence / RO5.
    void TestNumbers()
    {
        // Underfoot: 10% a second, dead in 10 ticks; 6 yd and a height band
        CHECK(UnderfootDamage(6645) == 665);
        CHECK(UnderfootDamage(5) == 1);
        CHECK(UnderfootDamage(0) == 1);
        uint32_t hp = 6645;
        uint32_t ticks = 0;
        while (hp > 0 && ticks < 20)
        {
            uint32_t const d = UnderfootDamage(6645);
            hp = d >= hp ? 0 : hp - d;
            ++ticks;
        }
        CHECK(ticks == 10);
        Vec2 const b{ 600.f, -270.f };
        CHECK(InUnderfoot(b, -83.f, { 605.9f, -270.f }, -83.f));
        CHECK(!InUnderfoot(b, -83.f, { 606.1f, -270.f }, -83.f));
        CHECK(!InUnderfoot(b, -83.f, { 601.f, -270.f }, -70.f));
        CHECK(kUnderfootTickMs == 1000 && kUnderfootLookEveryMs >= 2 * kUnderfootTickMs);
        // heroic merge: 3% of his health (190k: 5,700)
        CHECK(MergeHeal(190000) == 5700);
        CHECK(MergeHeal(110000) == 3300);
        // the waves: 2 / 3, at most two waves alive
        CHECK(LoosedToRaise(false, 0) == 2 && LoosedToRaise(false, 2) == 2 && LoosedToRaise(false, 3) == 1);
        CHECK(LoosedToRaise(false, 4) == 0 && LoosedToRaise(false, 9) == 0);
        CHECK(LoosedToRaise(true, 0) == 3 && LoosedToRaise(true, 3) == 3 && LoosedToRaise(true, 5) == 1);
        CHECK(LoosedToRaise(true, 6) == 0);
        CHECK(kLoosedCap(false) == 2 * kLoosedPerWave(false) && kLoosedCap(true) == 2 * kLoosedPerWave(true));
        // normal: 45 s life over a 25 s cadence: two waves, the cap never bites
        CHECK(kLoosedLifeMs / kLoosedEveryMs(false) + 1 == 2);
        // heroic: 45 s over 20 s would be three waves; the cap holds two
        CHECK(kLoosedLifeMs / kLoosedEveryMs(true) + 1 == 3);
        CHECK(kLoosedFirstMs == 18000 && kTremorCastMs == 2000);
        CHECK(kLoosedHealth(false) == 7000 && kLoosedHealth(true) == 12000);
        // Flame Shock 8-18 s
        CHECK(FlameShockDelay(0.f) == 8000 && FlameShockDelay(1.f) == 18000 && FlameShockDelay(0.5f) == 13000);
        CHECK(FlameShockDelay(-1.f) == 8000 && FlameShockDelay(7.f) == 18000);
        CHECK(kFlameShockMs / kFlameShockTickMs == 4);
        // Flame Shock in total: 6% + 4 x 2% = 14% (heroic 8% + 4 x 3% = 20%)
        CHECK(Near(kFlameShockPct(false) + 4 * kFlameShockTickPct(false), 14.f));
        CHECK(Near(kFlameShockPct(true) + 4 * kFlameShockTickPct(true), 20.f));
        CHECK(Near(kEarthShockPct(false), 10.f) && Near(kEarthShockPct(true), 15.f) && kEarthShockLockoutMs == 2000);
        // Flung Boulders: 3 x 3 yd within 8 yd every 5 s, 2 s warning; the look lands before the hit
        CHECK(kBouldersCount == 3 && Near(kBoulderRadiusYd, 3.f) && Near(kBoulderSpreadYd, 8.f));
        CHECK(kBouldersEveryMs == 5000 && kBouldersFirstMs == 10000 && kBoulderWarnMs == 2000);
        CHECK(kBoulderLookLeadMs < kBoulderWarnMs);
        CHECK(kBoulderPct < 50.f);      // a Weakened hit (shared doc section 4: under 50%)
        // the space math (S1 RO5): 3 circles are 42% of the 8 yd disc
        float const share = 3.f * DungeonKit::kPi * 9.f / (DungeonKit::kPi * 64.f);
        CHECK(share > 0.40f && share < 0.45f);
        // rule 10's stone: only after the grace, not faster than his swing
        CHECK(kHurlGraceMs >= 2000 && kHurlEveryMs >= 2000);
        CHECK(Near(kHurlPct(false), 15.f) && Near(kHurlPct(true), 20.f));
        // R-1-A m1: out of reach past the grace, but the tank is still catching up after a surge: no stone
        CHECK(!HurlReady(kHurlGraceMs - 1, 10000, 0, 0));
        CHECK(HurlReady(kHurlGraceMs, 10000, 0, 0));
        CHECK(!HurlReady(kHurlGraceMs, 10000, 10001, 0));
        CHECK(!HurlReady(kHurlGraceMs + 500, 10000, 0, 10000 + kSurgeLeashGraceMs));
        CHECK(!HurlReady(kHurlGraceMs + 500, 13999, 0, 14000));
        CHECK(HurlReady(kHurlGraceMs + 500, 14000, 0, 14000));
        // a 20 yd run after the surge takes about 3 s: the stone's own grace alone would not cover it
        CHECK(kSurgeLeashGraceMs > kHurlGraceMs);
    }

    // G1's walk row: the tank 8 yd, everyone 40 yd, tags 2 and 3, 1 s ticks, the Rampage tag 1.
    void TestLeash()
    {
        CHECK(TAG_RAMPAGE == 1 && TAG_TANK_LEASH == 2 && TAG_RANGE_LEASH == 3);
        CHECK(Near(kTankLeashYd, 8.f) && Near(kRangeLeashYd, 40.f) && kLeashTickMs == 1000);
        CHECK(LeashTag(5.f, true, false) == 0);
        CHECK(LeashTag(8.f, true, false) == 0);
        CHECK(LeashTag(8.5f, true, false) == TAG_TANK_LEASH);
        CHECK(LeashTag(8.5f, true, true) == 0);              // the surge's grace
        CHECK(LeashTag(30.f, false, false) == 0);
        CHECK(LeashTag(40.5f, false, false) == TAG_RANGE_LEASH);
        CHECK(LeashTag(40.5f, true, false) == TAG_RANGE_LEASH);
        CHECK(LeashTag(40.5f, true, true) == TAG_RANGE_LEASH);
        CHECK(Near(kRoadLeashYd, 40.f));
    }
}

int main()
{
    TestSlice();
    TestRoad();
    TestRampage();
    TestNumbers();
    TestLeash();
    return Report("brd_roccor_test");
}
