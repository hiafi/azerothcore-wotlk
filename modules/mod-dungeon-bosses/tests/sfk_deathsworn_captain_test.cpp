// Host tests for Deathsworn Captain (WP-S6): DeathswornCaptainLogic.h. Handoff section 5 for this boss: the chain
// targets are distinct, Sweeping Cleave's 4 s guard after a landing, the charge lines on the hall and the walkway
// (section 7 #25: along the walkway only, never off the arena), the grip landing, Last Stand, the numbers.
#include "DeathswornCaptainLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace DeathswornCaptain;

namespace
{
    bool Near(float a, float b, float eps)
    {
        return std::fabs(a - b) <= eps;
    }

    float NormalizeAngle(float o)
    {
        while (o < 0.f)
            o += DungeonKit::kTwoPi;
        while (o >= DungeonKit::kTwoPi)
            o -= DungeonKit::kTwoPi;
        return o;
    }

    float AngleGap(float a, float b)
    {
        float d = std::fabs(NormalizeAngle(a) - NormalizeAngle(b));
        return std::min(d, DungeonKit::kTwoPi - d);
    }

    // A point of the navmesh report's map (u right, v up; origin Odo, up = the keep grid).
    Vec2 MapPoint(float u, float v)
    {
        return ReportPoint(kOdoSpawn.XY(), kKeepUp, u, v);
    }

    bool OnPlan(Arena const& arena, Vec2 p)
    {
        for (DungeonKit::ArenaRegion const& r : arena.regions)
            if (r.ContainsPlane(p))
                return true;
        return false;
    }

    // On the hall or the walkway (plane only): the floor plan of a charge from either.
    bool OnHallOrWalkway(Arena const& arena, Vec2 p)
    {
        return arena.regions[kHallRegion].ContainsPlane(p) || arena.regions[kWalkwayRegion].ContainsPlane(p);
    }

    // A fixed pick sequence: returns `seq[i++ % size] % n`.
    struct SeqPick
    {
        std::vector<std::size_t> seq;
        std::size_t i = 0;

        std::size_t operator()(std::size_t n)
        {
            std::size_t const v = seq.empty() ? 0 : seq[i++ % seq.size()];
            return n ? v % n : 0;
        }
    };

    void TestSliceAndIds()
    {
        CHECK(kSpellsReservation.Contains(kSlice.first));
        CHECK(kSpellsReservation.Contains(kSlice.last));
        CHECK(kSlice.first <= kSlice.last);
        std::vector<std::uint32_t> const ids{ SPELL_CAPTAIN_CHARGE_BAR, SPELL_CAPTAIN_CHARGE_TRAIL,
            SPELL_CAPTAIN_CHARGE_HIT, SPELL_CAPTAIN_CLEAVE_BAR, SPELL_CAPTAIN_CLEAVE_HIT, SPELL_CAPTAIN_CLEAVE_TANK,
            SPELL_CAPTAIN_LAST_STAND };
        std::set<std::uint32_t> const unique(ids.begin(), ids.end());
        CHECK(unique.size() == ids.size());
        for (std::uint32_t id : ids)
            CHECK(kSlice.Contains(id));
        CHECK(TAG_DEATHSWORN_CHARGE == 1 && TAG_CHAIN_CHARGE == 2 && TAG_SWEEPING_CLEAVE == 3);
        CHECK(EMOTE_CAPTAIN_CHARGE == 0 && EMOTE_CAPTAIN_CLEAVE == 1);
    }

    void TestArenaAndPatrol()
    {
        Arena const arena = DeathswornCaptainArena();
        CHECK(arena.regions.size() == 3);
        CHECK(arena.Contains(kCaptainSpawn.XY(), kCaptainSpawn.z));
        // Every patrol point is on his arena (a pull anywhere on the path starts on it, he never leashes on a pull).
        for (Point3 const& p : kPatrol)
            CHECK(arena.Contains(p.XY(), p.z));
        // The hall points are not on the walkway; the walkway legs (points 3-6) are.
        for (std::size_t i : { 0u, 1u, 6u, 7u, 8u, 9u })
            CHECK(!OnWalkway(arena, kPatrol[i].XY()));
        for (std::size_t i : { 2u, 3u, 4u, 5u })
            CHECK(OnWalkway(arena, kPatrol[i].XY()));
        CHECK(!OnWalkway(arena, kCaptainSpawn.XY()));
        // The walkway runs along the keep grid's up axis.
        CHECK(Near(WalkwayAxis(arena), kKeepUp, 1e-4f));
        CHECK(AlongWalkway(arena, kPatrol[2].XY()) > AlongWalkway(arena, kPatrol[3].XY()));
    }

    void TestPatrolLanding()
    {
        Arena const arena = DeathswornCaptainArena();
        // A unit on the patrol line lands where it is.
        for (Point3 const& p : kPatrol)
        {
            Point3 const l = PatrolLanding(p.XY());
            CHECK(DungeonKit::Distance(l.XY(), p.XY()) < 0.01f);
            CHECK(Near(l.z, p.z, 0.01f));
        }
        // A fall into the inner yard (west of the walkway), a step into Odo's room, a unit on the bridge: each lands
        // on the arena, at walkway / hall height.
        for (Vec2 const p : { MapPoint(25.f, 25.f), MapPoint(28.f, 12.f), MapPoint(20.f, -5.f), MapPoint(10.f, 33.f),
                 MapPoint(50.f, 30.f), MapPoint(-40.f, 46.f) })
        {
            Point3 const l = PatrolLanding(p);
            CHECK(arena.Contains(l.XY(), l.z));
            CHECK(l.z >= 97.f && l.z <= 100.1f);
        }
        // The yard fall lands on the walkway, not the hall.
        CHECK(OnWalkway(arena, PatrolLanding(MapPoint(25.f, 25.f)).XY()));
    }

    void TestWalkwayCharges()
    {
        Arena const arena = DeathswornCaptainArena();
        Vec2 const bottom = kPatrol[3].XY();     // the walkway's low end (v 11)
        float const axis = NormalizeAngle(kKeepUp);

        // Toward the hall: along the walkway's axis, the lateral offset unchanged, not clipped (a 13+ yd run fits).
        ChargePath const up = ChargeLine(arena, bottom, kPatrol[0].XY(), 0.f);
        CHECK(up.alongWalkway);
        CHECK(AngleGap(up.facing, axis) < 1e-3f);
        CHECK(Near(DungeonKit::ToFrame(arena.regions[kWalkwayRegion].frame, up.end).y,
            DungeonKit::ToFrame(arena.regions[kWalkwayRegion].frame, bottom).y, 0.05f));
        CHECK(OnPlan(arena, up.end));
        CHECK(up.length >= kChargeMinDistance + kChargeOverrun);

        // A target beside him on the walkway (2 yd across, 9 yd up): still along the axis.
        Vec2 const side = MapPoint(38.5f, 20.f);
        ChargePath const sideways = ChargeLine(arena, bottom, side, 0.f);
        CHECK(sideways.alongWalkway);
        CHECK(AngleGap(sideways.facing, axis) < 1e-3f);
        CHECK(Near(sideways.length, 9.f + kChargeOverrun, 0.3f));

        // Toward Odo's door: down the axis, stopped short of the walkway's end (kChargeEdgeInset), not past it.
        ChargePath const down = ChargeLine(arena, bottom, kPatrol[4].XY(), 0.f);
        CHECK(down.alongWalkway);
        CHECK(AngleGap(down.facing, axis + DungeonKit::kPi) < 1e-3f);
        CHECK(down.clipped);
        CHECK(OnPlan(arena, down.end));
        CHECK(!OnHallOrWalkway(arena, DungeonKit::Advance(down.end, down.facing, kChargeEdgeInset + 0.3f)));
        CHECK(down.length < kChargeMinDistance + kChargeOverrun);

        // A target in Odo's room (off the arena) beyond the walkway's end: the same, the line never leaves the arena.
        ChargePath const room = ChargeLine(arena, kPatrol[5].XY(), MapPoint(10.f, -5.f), 0.f);
        CHECK(room.alongWalkway);
        CHECK(OnPlan(arena, room.end));

        // A target on top of him: the axis direction nearer to his facing.
        ChargePath const same = ChargeLine(arena, bottom, bottom, axis + 0.2f);
        CHECK(AngleGap(same.facing, axis) < 1e-3f);
        ChargePath const sameDown = ChargeLine(arena, bottom, bottom, axis + DungeonKit::kPi - 0.2f);
        CHECK(AngleGap(sameDown.facing, axis + DungeonKit::kPi) < 1e-3f);
    }

    void TestHallCharges()
    {
        Arena const arena = DeathswornCaptainArena();
        Vec2 const spawn = kCaptainSpawn.XY();

        // Along the hall: straight at the target, 5 yd past it, not clipped.
        Vec2 const along = MapPoint(13.5f, 49.5f);
        ChargePath const a = ChargeLine(arena, spawn, along, 0.f);
        CHECK(!a.alongWalkway);
        CHECK(!a.clipped);
        CHECK(Near(a.length, DungeonKit::Distance(spawn, along) + kChargeOverrun, 0.01f));
        CHECK(Near(a.facing, DungeonKit::BearingTo(spawn, along), 1e-4f));

        // A target 3 yd away still gets the full line through it (8 + 5 yd).
        Vec2 const close = MapPoint(6.5f, 49.5f);
        ChargePath const c = ChargeLine(arena, spawn, close, 0.f);
        CHECK(Near(c.length, kChargeMinDistance + kChargeOverrun, 0.01f));

        // Across the hall (12 yd wide): stopped short of the wall.
        Vec2 const across = MapPoint(3.5f, 41.f);
        ChargePath const x = ChargeLine(arena, spawn, across, 0.f);
        CHECK(x.clipped);
        CHECK(x.length < DungeonKit::Distance(spawn, across) + kChargeOverrun);
        CHECK(OnPlan(arena, x.end));

        // Every direction from every hall point of the patrol and the spawn: the line ends on the arena, at least the
        // inset (less one march step) short of its edge, and is never longer than wanted.
        std::vector<Vec2> starts{ spawn };
        for (std::size_t i : { 0u, 1u, 7u, 8u, 9u })
            starts.push_back(kPatrol[i].XY());
        for (Vec2 const s : starts)
            for (int k = 0; k < 72; ++k)
            {
                float const o = k * DungeonKit::kTwoPi / 72.f;
                Vec2 const t = DungeonKit::Advance(s, o, 12.f);
                ChargePath const p = ChargeLine(arena, s, t, 0.f);
                CHECK(p.length >= 0.f && p.length <= 12.f + kChargeOverrun + 0.01f);
                CHECK(OnPlan(arena, p.end));
                CHECK(OnPlan(arena, DungeonKit::Advance(p.end, p.facing, kChargeEdgeInset - 0.3f)));
            }
    }

    void TestChainedCharge()
    {
        Arena const arena = DeathswornCaptainArena();
        // DC1 from the hall to a player at the walkway's top, then DC2 from that landing to another player.
        Vec2 const spawn = kCaptainSpawn.XY();
        std::vector<ChargeCandidate> const group{
            { 11, MapPoint(28.f, 48.f) },       // in the hall, ~25 yd
            { 12, MapPoint(-15.f, 48.f) },      // in the hall, the other way
            { 13, MapPoint(3.f, 46.f) },        // 3.5 yd from him
        };
        SeqPick pick{ { 0, 1, 0 } };
        std::vector<std::uint64_t> chain;
        std::optional<std::size_t> const first = PickChargeTarget(group, spawn, chain, kChargeMinDistance, pick);
        CHECK(first.has_value());
        CHECK(group[*first].id != 13);           // the near player is never the first pick while others are 8+ yd
        chain.push_back(group[*first].id);
        ChargePath const leg1 = ChargeLine(arena, spawn, group[*first].pos, 0.f);
        std::optional<std::size_t> const second = PickChargeTarget(group, leg1.end, chain, kChargeMinDistance, pick);
        CHECK(second.has_value());
        CHECK(group[*second].id != group[*first].id);
        ChargePath const leg2 = ChargeLine(arena, leg1.end, group[*second].pos, leg1.facing);
        CHECK(OnPlan(arena, leg2.end));

        // Distinct for every pick sequence while two or more players stand.
        for (std::size_t s = 0; s < 6; ++s)
        {
            SeqPick p{ { s, s + 1 } };
            std::vector<std::uint64_t> c;
            std::optional<std::size_t> const a = PickChargeTarget(group, spawn, c, kChargeMinDistance, p);
            CHECK(a.has_value());
            c.push_back(group[*a].id);
            std::optional<std::size_t> const b = PickChargeTarget(group, group[*a].pos, c, kChargeMinDistance, p);
            CHECK(b.has_value() && group[*b].id != group[*a].id);
        }
    }

    void TestPicks()
    {
        Vec2 const o{ 0.f, 0.f };
        std::vector<ChargeCandidate> const c{ { 1, { 5.f, 0.f } }, { 2, { 10.f, 0.f } }, { 3, { 0.f, 12.f } } };
        SeqPick zero{ { 0 } };
        SeqPick one{ { 1 } };
        // 1. random among the 8+ yd ones
        CHECK(PickChargeTarget(c, o, {}, kChargeMinDistance, zero) == std::optional<std::size_t>(1));
        CHECK(PickChargeTarget(c, o, {}, kChargeMinDistance, one) == std::optional<std::size_t>(2));
        CHECK(PickChargeTarget(c, o, { 2 }, kChargeMinDistance, zero) == std::optional<std::size_t>(2));
        // 2. else the farthest not yet picked
        CHECK(PickChargeTarget(c, o, { 2, 3 }, kChargeMinDistance, zero) == std::optional<std::size_t>(0));
        std::vector<ChargeCandidate> const near{ { 1, { 3.f, 0.f } }, { 2, { 0.f, 6.f } } };
        CHECK(PickChargeTarget(near, o, {}, kChargeMinDistance, zero) == std::optional<std::size_t>(1));
        // 3. everyone picked: anyone but the last pick
        std::optional<std::size_t> const again = PickChargeTarget(c, o, { 1, 2, 3 }, kChargeMinDistance, zero);
        CHECK(again.has_value() && c[*again].id != 3);
        // 4. a lone non-tank already picked: picked again (the G8 drill's fallback); nobody: none
        std::vector<ChargeCandidate> const lone{ { 7, { 9.f, 0.f } } };
        CHECK(PickChargeTarget(lone, o, { 7 }, kChargeMinDistance, zero) == std::optional<std::size_t>(0));
        CHECK(!PickChargeTarget({}, o, {}, kChargeMinDistance, zero).has_value());
    }

    void TestReach()
    {
        Arena const arena = DeathswornCaptainArena();
        // From the hall's ESE end (patrol point 2), a player at the walkway's foot is cut off by the hall wall (the
        // line leaves the hall beside the walkway), a player along the hall is reached.
        Vec2 const from = kPatrol[1].XY();
        Vec2 const walkway = kPatrol[3].XY();
        Vec2 const hall = MapPoint(5.f, 46.f);
        ChargePath const toWalkway = ChargeLine(arena, from, walkway, 0.f);
        ChargePath const toHall = ChargeLine(arena, from, hall, 0.f);
        CHECK(toWalkway.clipped);
        CHECK(!ChargeReaches(toWalkway, walkway));
        CHECK(ChargeReaches(toHall, hall));
        // On the walkway a player beside the line still counts (the line runs level with them).
        ChargePath const along = ChargeLine(arena, kPatrol[3].XY(), MapPoint(38.5f, 20.f), 0.f);
        CHECK(ChargeReaches(along, MapPoint(38.5f, 20.f)));
        // Inside the excluded first 4 yd: not reached.
        CHECK(!ChargeReaches(toHall, DungeonKit::Advance(from, toHall.facing, kChargeExclude - 0.5f)));

        std::vector<ChargeCandidate> const c{ { 1, walkway }, { 2, hall } };
        std::vector<bool> const reaches{ ChargeReaches(ChargeLine(arena, from, walkway, 0.f), walkway),
            ChargeReaches(ChargeLine(arena, from, hall, 0.f), hall) };
        for (std::size_t s = 0; s < 4; ++s)
        {
            SeqPick p{ { s } };
            CHECK(PickReachableChargeTarget(c, from, {}, kChargeMinDistance, reaches, p)
                == std::optional<std::size_t>(1));
        }
        // Nobody reachable: the plain rule (random among the 8+ yd ones).
        SeqPick zero{ { 0 } };
        CHECK(PickReachableChargeTarget(c, from, {}, kChargeMinDistance, { false, false }, zero)
            == std::optional<std::size_t>(0));
        // The reachable one already charged at: the plain rule picks the other.
        CHECK(PickReachableChargeTarget(c, from, { 2 }, kChargeMinDistance, reaches, zero)
            == std::optional<std::size_t>(0));
    }

    // Bot clear 2026-11-08: he turns in Odo's door, so a pull there fights in Odo's ESE alcove behind it; units there
    // (x -250 to -257, y 2110 to 2117, z 100) were gripped 38 times in 77 s. The alcove is on the arena now.
    void TestOdoAlcove()
    {
        Arena const arena = DeathswornCaptainArena();
        for (float x : { -250.f, -253.5f, -257.f })
            for (float y : { 2110.f, 2113.5f, 2117.f })
            {
                Vec2 const p{ x, y };
                CHECK(arena.Contains(p, 100.f));
                CHECK(arena.Contains(p, 101.2f));
                CHECK(InOdoAlcove(arena, p));
                CHECK(!OnWalkway(arena, p));
                CHECK(!arena.Contains(p, 87.f));            // the jail's upper level under it
            }
        // The navmesh floor of the alcove (u 33 to 39.75, v -16 to 3), its corners.
        for (Vec2 const p : { MapPoint(33.f, -15.5f), MapPoint(39.75f, -15.5f), MapPoint(33.f, 3.f),
                 MapPoint(39.75f, 3.f), MapPoint(36.5f, -8.f) })
            CHECK(arena.Contains(p, 100.6f));
        // The door strip counts as walkway (his patrol point 5 is in it).
        CHECK(OnWalkway(arena, kPatrol[4].XY()));
        CHECK(!InOdoAlcove(arena, kPatrol[4].XY()));
        // Odo's end of the room stays off: his spawn, the middle bell, the room 10 yd short of the partition.
        CHECK(!arena.Contains(kOdoSpawn.XY(), kOdoSpawn.z));
        CHECK(!arena.Contains(kBellSpots[1].XY(), kBellSpots[1].z));
        CHECK(!arena.Contains(MapPoint(21.f, -5.f), 100.6f));
        // The walkway floor (navmesh u 33.75 to 38.5) and its east niches (u 40, z up to 99.5) are on it.
        for (Vec2 const p : { MapPoint(33.75f, 8.f), MapPoint(38.5f, 8.f), MapPoint(33.75f, 30.f),
                 MapPoint(38.5f, 37.f), MapPoint(33.f, 17.5f), MapPoint(40.f, 17.5f), MapPoint(40.f, 23.5f) })
        {
            CHECK(arena.Contains(p, 98.8f));
            CHECK(OnWalkway(arena, p));
        }
        // The inner yard below the walkway (z 77 to 81), under it and beside it, is off.
        for (Vec2 const p : { MapPoint(36.f, 20.f), MapPoint(25.f, 20.f), MapPoint(30.f, 15.f), MapPoint(36.f, 11.f) })
        {
            CHECK(!arena.Contains(p, 79.f));
            CHECK(!arena.Contains(p, 81.f));
        }

        // A charge from the alcove stays in it, along the room (straight at the target) and toward the walkway (cut
        // at the alcove's door line, never through the wall beside the door).
        Vec2 const in = MapPoint(36.5f, -2.f);
        ChargePath const along = ChargeLine(arena, in, MapPoint(36.5f, -14.f), 0.f);
        CHECK(!along.alongWalkway);
        CHECK(InOdoAlcove(arena, along.end));
        CHECK(Near(along.length, 12.f + kChargeOverrun, 0.01f) || along.clipped);
        ChargePath const out = ChargeLine(arena, MapPoint(34.f, -2.f), MapPoint(34.f, 20.f), 0.f);
        CHECK(out.clipped);
        CHECK(InOdoAlcove(arena, out.end));
        for (int k = 0; k < 72; ++k)
        {
            float const o = k * DungeonKit::kTwoPi / 72.f;
            ChargePath const p = ChargeLine(arena, in, DungeonKit::Advance(in, o, 12.f), 0.f);
            CHECK(InOdoAlcove(arena, p.end));
            CHECK(arena.regions[kOdoAlcoveRegion].ContainsPlane(
                DungeonKit::Advance(p.end, p.facing, kChargeEdgeInset - 0.3f)));
        }
        // A charge from the walkway toward a player in the alcove stops short of the walkway's end, as before.
        ChargePath const down = ChargeLine(arena, kPatrol[3].XY(), MapPoint(36.5f, -8.f), 0.f);
        CHECK(down.alongWalkway);
        CHECK(down.clipped);
        CHECK(!InOdoAlcove(arena, down.end));
        CHECK(OnHallOrWalkway(arena, down.end));
    }

    void TestTimings()
    {
        CHECK(ChargeTravelMs(21.f) == 500);
        CHECK(ChargeTravelMs(0.f) == 0);
        CHECK(ChargeTravelMs(0.01f) >= 1);
        CHECK(ChargeChainMs(kChargeLegs(false)) == 2000);
        CHECK(ChargeChainMs(kChargeLegs(true)) == 3500);
        CHECK(kChargeLegs(false) == 1 && kChargeLegs(true) == 2);

        // DC3's guard: never while charging, never within 4 s after the last landing.
        CHECK(CleaveWaitMs(5000, true, std::nullopt) == kBusyRetryMs);
        CHECK(CleaveWaitMs(5000, false, std::nullopt) == 0);
        CHECK(CleaveWaitMs(12000, false, 10000u) == 2000);
        CHECK(CleaveWaitMs(13999, false, 10000u) == 1);
        CHECK(CleaveWaitMs(14000, false, 10000u) == 0);
        CHECK(CleaveWaitMs(30000, false, 10000u) == 0);
        // A cleave delayed by the guard lands outside the window: now + wait == landing + 4 s.
        for (std::uint32_t now = 10000; now < 14000; now += 250)
            CHECK(now + CleaveWaitMs(now, false, 10000u) == 10000 + kCleaveAfterChargeMs);

        // The opening: the first cleave's cast ends before the first charge's marker starts.
        CHECK(kCleaveFirstMs + kCleaveWarnMs <= kChargeFirstMs);
        CHECK(kCleaveEveryMs == 12000 && kChargeEveryMs == 15000);
    }

    void TestLastStand()
    {
        CHECK(!LastStandDue(false, 10.f, false));
        CHECK(LastStandDue(true, 29.9f, false));
        CHECK(!LastStandDue(true, 30.f, false));
        CHECK(!LastStandDue(true, 10.f, true));
        CHECK(kLastStandHastePct == 30);
    }

    // R2 S-2: he holds only while Odo is IN_PROGRESS, short of the doorway; the bells stay out of his reach.
    void TestOdoHold()
    {
        CHECK(HoldForOdo(DungeonKit::State::InProgress));
        CHECK(!HoldForOdo(DungeonKit::State::NotStarted));
        CHECK(!HoldForOdo(DungeonKit::State::Fail));
        CHECK(!HoldForOdo(DungeonKit::State::Done));
        CHECK(!HoldForOdo(DungeonKit::State::ToBeDecided));

        Point3 const hold = OdoHoldPoint();
        CHECK(std::fabs(hold.x - -239.866f) < 0.01f && std::fabs(hold.y - 2108.05f) < 0.01f);
        float const door = DungeonKit::Distance(hold.XY(), kOdoDoor.XY());
        CHECK(door > 7.f && door < 9.f);
        CHECK(HoldWalksBack(kPatrol[4].XY()));                  // point 5, in the doorway
        CHECK(!HoldWalksBack(hold.XY()));
        for (std::size_t i : { 0u, 1u, 2u, 5u, 6u, 7u, 8u, 9u })
            CHECK(!HoldWalksBack(kPatrol[i].XY()));
    }

    void TestNumbers()
    {
        // Reference rows (handoff section 3.7): normal 1,300 / 1,290, heroic 4,120 / 4,110.
        CHECK(DungeonKit::RefFlatValue(1300, 1290, kChargePct, false) == 455);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kChargePct, false) == 1442);
        CHECK(DungeonKit::RefFlatValue(1300, 1290, kCleavePct, false) == 520);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kCleavePct, false) == 1648);
        CHECK(kChargeWidth == 3.f && kChargeOverrun == 5.f && kChargeExclude == 4.f);
        CHECK(kCleaveAngle == 90.f && kCleaveLength == 10.f && kCleaveTankSwings == 2);
        CHECK(kChargeMinLength > kChargeExclude);
    }
}

int main()
{
    TestOdoHold();
    TestSliceAndIds();
    TestArenaAndPatrol();
    TestPatrolLanding();
    TestWalkwayCharges();
    TestOdoAlcove();
    TestHallCharges();
    TestChainedCharge();
    TestPicks();
    TestReach();
    TestTimings();
    TestLastStand();
    TestNumbers();
    return Report("sfk_deathsworn_captain_test");
}
