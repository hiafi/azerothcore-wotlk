// Host tests for Odo the Blindwatcher (WP-S5): OdoLogic.h and the shared Hunt rules (HuntLogic.h, also the Echo of
// Odo's). Handoff section 5: Hunt speed rates, bell cooldowns (40 s normal, spent heroic), the bell rule; plus the
// build spec's numbers, the bell points against the room and the `sfk-hunt` drill's model.
#include "HuntLogic.h"
#include "OdoLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace ShadowfangKeepRework;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Odo::kSlice.first));
        CHECK(kSpellsReservation.Contains(Odo::kSlice.last));
        CHECK(Odo::kSlice.first <= Odo::kSlice.last);
        CHECK(OdoArena().Contains(kOdoSpawn.XY(), kOdoSpawn.z));
    }

    // Every spell id sits in Odo's slice, once.
    void TestSpellIds()
    {
        std::set<std::uint32_t> seen;
        for (std::uint32_t const id : Odo::kAllSpells)
        {
            CHECK(Odo::kSlice.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(seen.size() == Odo::kAllSpells.size());
        CHECK(Odo::kAllSpells.size() <= Odo::kSlice.Size());
    }

    // OD1: the Hunt's numbers (build spec; handoff section 8 #11: speed_run 0.8 / 0.95) and the drill's line
    // (`hunt 3 2000 speed=0.8 persist=10000 tick=200` and the 95% step).
    void TestHuntNumbers()
    {
        SfkHunt::HuntTuning const n = SfkHunt::OdoHunt(false);
        SfkHunt::HuntTuning const h = SfkHunt::OdoHunt(true);
        CHECK(Near(SfkHunt::RunRate(n.ratePct), 0.8f));
        CHECK(Near(SfkHunt::RunRate(h.ratePct), 0.95f));
        CHECK(Near(SfkHunt::ChaserYdS(n.ratePct), 5.6f));
        CHECK(Near(SfkHunt::ChaserYdS(h.ratePct), 6.65f));
        for (SfkHunt::HuntTuning const& t : { n, h })
        {
            CHECK(Near(t.radius, 3.f));
            CHECK(t.warnMs == 2000);
            CHECK(t.chaseMs == 10000);
            CHECK(t.tickMs == 200);
            CHECK(SfkHunt::TotalMs(t) == 12000);
            CHECK(SfkHunt::Passes(t) == 50);
        }
        // The navmesh report: 14 yd gained in 10 s at 80%, 3.5 yd at 95%.
        CHECK(Near(SfkHunt::GainYd(n), 14.f));
        CHECK(Near(SfkHunt::GainYd(h), 3.5f));
        // Both are slower than a player (the hunted can always walk away), and faster than nothing.
        CHECK(SfkHunt::ChaserYdS(h.ratePct) < SfkHunt::kPlayerRunYdS);
        // The stock run rate (1.14) is faster than a player: the hunt rate replaces it while hunting.
        CHECK(SfkHunt::RunRate(h.ratePct) < 1.14286f);
        // Tags: the drill's 1 (80%) and 5 (95%).
        CHECK(Odo::kHuntTag(false) == 1);
        CHECK(Odo::kHuntTag(true) == 5);
        CHECK(Odo::TAG_BELL == 2);
        CHECK(Odo::TAG_LANDING == 3);
        // First at 10 s, then 25 s.
        CHECK(Odo::kHuntFirst.count() == 10000);
        CHECK(Odo::kHuntEvery.count() == 25000);
        // A hunt (12 s) ends well before the next (25 s).
        CHECK(SfkHunt::TotalMs(h) < static_cast<std::uint32_t>(Odo::kHuntEvery.count()));
    }

    // The Echo of Odo (BS5): 8 s at 80%, the same circle and howl.
    void TestEchoHunt()
    {
        SfkHunt::HuntTuning const e = SfkHunt::kEchoHunt;
        CHECK(Near(SfkHunt::RunRate(e.ratePct), 0.8f));
        CHECK(e.chaseMs == 8000);
        CHECK(e.warnMs == 2000);
        CHECK(Near(e.radius, 3.f));
        // The navmesh report: the player gains 11.2 yd in 8 s.
        CHECK(Near(SfkHunt::GainYd(e), 11.2f));
    }

    // The slack to start walking (the drill's desk model): (gap - 3) / chaser speed.
    void TestCatchSlack()
    {
        SfkHunt::HuntTuning const n = SfkHunt::OdoHunt(false);
        SfkHunt::HuntTuning const h = SfkHunt::OdoHunt(true);
        CHECK(SfkHunt::CatchSlackMs(n, 8.f) == 892);      // 5 / 5.6
        CHECK(SfkHunt::CatchSlackMs(h, 8.f) == 751);      // 5 / 6.65
        CHECK(SfkHunt::CatchSlackMs(n, 3.f) == 0);
        CHECK(SfkHunt::CatchSlackMs(n, 1.f) == 0);
        CHECK(SfkHunt::CatchSlackMs(n, 20.f) > SfkHunt::CatchSlackMs(h, 20.f));
    }

    // OD2: Maul 35% over 3 s (1 s ticks); the echo's 20% over 1.5 s (0.5 s ticks). Reference rows 1,300 / 4,120.
    void TestMaul()
    {
        CHECK(SfkHunt::MaulTicks(Odo::kMaulMs, Odo::kMaulTickMs) == 3);
        CHECK(Near(SfkHunt::MaulTickPct(Odo::kMaulPct, Odo::kMaulMs, Odo::kMaulTickMs), 35.f / 3.f));
        float const tick = SfkHunt::MaulTickPct(Odo::kMaulPct, Odo::kMaulMs, Odo::kMaulTickMs);
        // Three ticks of RefFlatValue add up to 35% (+- rounding).
        std::uint32_t const normal = 3 * DungeonKit::RefFlatValue(1300, 1290, tick, false);
        std::uint32_t const heroic = 3 * DungeonKit::RefFlatValue(4120, 4110, tick, false);
        CHECK(normal >= 454 && normal <= 456);           // 35% of 1,300 = 455
        CHECK(heroic >= 1441 && heroic <= 1443);         // 35% of 4,120 = 1,442
        CHECK(SfkHunt::MaulTicks(1500, 500) == 3);
        CHECK(Near(SfkHunt::MaulTickPct(20.f, 1500, 500), 20.f / 3.f));
        CHECK(SfkHunt::MaulTicks(3000, 0) == 0);
        CHECK(Near(SfkHunt::MaulTickPct(35.f, 3000, 0), 0.f));
    }

    // OD3 / OD4: the bell points (handoff section 7 #24) in the room, at least 19 yd apart; the landing numbers.
    void TestBellPoints()
    {
        Arena const room = OdoArena();
        for (std::size_t i = 0; i < Odo::kBellCount; ++i)
        {
            Point3 const& p = kBellSpots[i];
            CHECK(room.Contains(p.XY(), p.z));
            CHECK(Odo::NearestBellSpot(p.XY()) == std::optional<std::size_t>(i));
            for (std::size_t j = i + 1; j < Odo::kBellCount; ++j)
                CHECK(DungeonKit::Distance(p.XY(), kBellSpots[j].XY()) >= 19.f);
        }
        CHECK(Odo::kBellCount == 3);
        // The navmesh report's distances from Odo: 12.2, 19.1, 37.6 yd.
        CHECK(Near(DungeonKit::Distance(kOdoSpawn.XY(), kBellSpots[0].XY()), 12.2f, 0.1f));
        CHECK(Near(DungeonKit::Distance(kOdoSpawn.XY(), kBellSpots[1].XY()), 19.1f, 0.1f));
        CHECK(Near(DungeonKit::Distance(kOdoSpawn.XY(), kBellSpots[2].XY()), 37.6f, 0.1f));
        // A spawned bell maps to its spot within 5 yd, a far point to none.
        CHECK(Odo::NearestBellSpot({ kBellSpots[1].x + 1.f, kBellSpots[1].y - 1.f }) == std::optional<std::size_t>(1));
        CHECK(!Odo::NearestBellSpot(kOdoSpawn.XY()).has_value());
        // OD3 / OD4 numbers.
        CHECK(Near(Odo::kBellRadius, 2.f));
        CHECK(Odo::kBellDwellMs == 1000);
        CHECK(Near(Odo::kLandingRadius, 6.f));
        CHECK(Near(Odo::kLandingPct, 35.f));
        CHECK(Odo::kLandingWarn.count() == 2000);
        // 35% is under the 40% cap and under the Weakened line (ruling 17: heroic hit < 50%).
        CHECK(Odo::kLandingPct < 40.f);
        // The bound lands 2 s after leaving, from any bell distance.
        CHECK(Near(Odo::BoundSpeedXY(37.6f), 18.8f));
        CHECK(Near(Odo::BoundSpeedXY(0.f), 1.f));
        // A bell soak (2 yd) never overlaps another bell's landing (6 yd): the bells are 19 yd apart.
        CHECK(Odo::kLandingRadius + Odo::kBellRadius < 19.f);
        // The bots' soak resolves just inside the hunt.
        CHECK(Odo::kBellSoakEarlyMs < SfkHunt::OdoHunt(false).tickMs * 2);
    }

    // The bell rule: never the hunted player; the tank only by a click.
    void TestCanRing()
    {
        CHECK(Odo::CanRing(false, false, false));
        CHECK(Odo::CanRing(false, false, true));
        CHECK(!Odo::CanRing(true, false, false));
        CHECK(!Odo::CanRing(true, false, true));
        CHECK(!Odo::CanRing(false, true, false));
        CHECK(Odo::CanRing(false, true, true));
        CHECK(!Odo::CanRing(true, true, true));
    }

    // The boss data bell rule: the nearest eligible ringer's nearest ready bell.
    void TestChooseBell()
    {
        std::array<bool, 3> all{ { true, true, true } };
        // A ringer by bell 3 picks bell 3, one by bell 1 picks bell 1.
        CHECK(Odo::ChooseBell(all, { kBellSpots[2].XY() }) == std::optional<std::size_t>(2));
        CHECK(Odo::ChooseBell(all, { kBellSpots[0].XY() }) == std::optional<std::size_t>(0));
        // Two ringers: the pair with the smallest distance wins (the one 1 yd from bell 2).
        Vec2 const nearTwo{ kBellSpots[1].x + 1.f, kBellSpots[1].y };
        Vec2 const farFromAll = kOdoSpawn.XY();
        CHECK(Odo::ChooseBell(all, { farFromAll, nearTwo }) == std::optional<std::size_t>(1));
        // A cracked bell is skipped: bell 3's ringer then takes the nearest ready one.
        std::array<bool, 3> noThree{ { true, true, false } };
        CHECK(Odo::ChooseBell(noThree, { kBellSpots[2].XY() }) == std::optional<std::size_t>(1));
        // Nothing ready, or nobody to ring.
        std::array<bool, 3> none{ { false, false, false } };
        CHECK(!Odo::ChooseBell(none, { kBellSpots[0].XY() }).has_value());
        CHECK(!Odo::ChooseBell(all, {}).has_value());
    }

    // Cracked 40 s on normal (with a Hunt every 25 s and three bells, one is always ready); spent on heroic.
    void TestBellBoard()
    {
        // Normal.
        Odo::BellBoard b;
        b.Reset();
        CHECK(b.ReadyCount(0) == 3);
        CHECK(b.Ring(1, 10000, Odo::kBellCrackMs(false)));
        CHECK(!b.IsReady(1, 10000));
        CHECK(!b.Ring(1, 20000, Odo::kBellCrackMs(false)));    // still cracked
        CHECK(!b.IsReady(1, 49999));
        CHECK(b.IsReady(1, 50000));
        CHECK(!b.CrackedForGood(1));
        CHECK(b.Recovered(49999, 50000) == std::vector<std::size_t>{ 1 });
        CHECK(b.Recovered(50000, 60000).empty());
        // A Hunt every 25 s from 10 s, each belled at the nearest ready bell: a ready bell at every Hunt.
        Odo::BellBoard r;
        r.Reset();
        for (std::uint64_t t = 10000; t <= 300000; t += 25000)
        {
            CHECK(r.ReadyCount(t) >= 1);
            std::array<bool, 3> const ready = r.Ready(t);
            std::size_t pick = 0;
            while (!ready[pick])
                ++pick;
            CHECK(r.Ring(pick, t, Odo::kBellCrackMs(false)));
        }

        // Heroic: three saves, then none for the fight (the 4th Hunt at about 85 s has no bell).
        Odo::BellBoard h;
        h.Reset();
        std::uint64_t t = 10000;
        for (std::size_t i = 0; i < 3; ++i, t += 25000)
            CHECK(h.Ring(i, t, Odo::kBellCrackMs(true)));
        CHECK(h.ReadyCount(t) == 0);
        CHECK(h.ReadyCount(10000000) == 0);
        CHECK(h.CrackedForGood(0) && h.CrackedForGood(1) && h.CrackedForGood(2));
        CHECK(h.Recovered(0, 100000000).empty());
        CHECK(!h.Ring(0, 99999999, Odo::kBellCrackMs(true)));
        // A wipe brings them back.
        h.Reset();
        CHECK(h.ReadyCount(0) == 3);
        // Out of range.
        CHECK(!h.IsReady(3, 0));
        CHECK(!h.Ring(7, 0, 1));
    }

    // OD7: 70, 50, 30% once each, in order; a big hit that skips two queues both.
    void TestHowls()
    {
        Odo::HowlTracker t;
        t.Reset();
        t.OnHealth(90.f);
        CHECK(!t.Next().has_value());
        t.OnHealth(70.f);
        CHECK(t.Next() == std::optional<std::size_t>(0));
        t.MarkCast(0);
        CHECK(!t.Next().has_value());
        t.OnHealth(69.f);
        CHECK(!t.Next().has_value());       // never twice
        t.OnHealth(29.f);                   // skips 50 and 30 in one hit
        CHECK(t.Next() == std::optional<std::size_t>(1));
        t.MarkCast(1);
        CHECK(t.Next() == std::optional<std::size_t>(2));
        t.MarkCast(2);
        CHECK(!t.Next().has_value());
        t.Reset();
        t.OnHealth(10.f);
        CHECK(t.Next() == std::optional<std::size_t>(0));
        CHECK(Odo::kHowlSpells[0] == SPELL_HOWLING_RAGE_1);
        CHECK(Odo::kHowlSpells[1] == SPELL_HOWLING_RAGE_2);
        CHECK(Odo::kHowlSpells[2] == SPELL_HOWLING_RAGE_3);
    }

    // The grip landing: 8 yd toward the player when the room holds it, else the room's middle; always in the room.
    void TestGripLanding()
    {
        Arena const room = OdoArena();
        Vec2 const center = Odo::RoomCenter();
        CHECK(room.Contains(center, kOdoSpawn.z));
        // From the door (42 yd from him), the landing is 8 yd toward the door, in the room.
        Vec2 const towardDoor = Odo::GripLanding(kOdoSpawn.XY(), kOdoSpawn.z, kOdoDoor.XY());
        CHECK(Near(DungeonKit::Distance(towardDoor, kOdoSpawn.XY()), 8.f, 0.05f));
        CHECK(room.Contains(towardDoor, kOdoSpawn.z));
        // From behind his back wall (WNW, the Courtyard Door landing), 8 yd would be outside: the middle.
        Vec2 const behind = ReportPoint(kOdoSpawn.XY(), kKeepUp, -12.f, 0.f);
        CHECK(!room.Contains(DungeonKit::Advance(kOdoSpawn.XY(), DungeonKit::BearingTo(kOdoSpawn.XY(), behind), 8.f),
            kOdoSpawn.z));
        Vec2 const fromBehind = Odo::GripLanding(kOdoSpawn.XY(), kOdoSpawn.z, behind);
        CHECK(Near(fromBehind.x, center.x) && Near(fromBehind.y, center.y));
        // The hunted player is never landed on him: at least 8 yd away either way.
        CHECK(DungeonKit::Distance(fromBehind, kOdoSpawn.XY()) >= 8.f);
    }

    // The fight shape on heroic: Hunts at 10, 35, 60, 85 s (about 87 s): 4 Hunts against 3 bells.
    // Stratholme SWEEP-2 D5: a pass that hit only the hunted player's pet is not the catch; one that hit the player
    // is.
    void TestCatchIsTheHuntedPlayer()
    {
        using Id = std::uint64_t;
        Id const hunted = 11;
        Id const pet = 12;
        CHECK(!SfkHunt::IsCatch(std::vector<Id>{}, hunted));
        CHECK(!SfkHunt::IsCatch(std::vector<Id>{ pet }, hunted));
        CHECK(SfkHunt::IsCatch(std::vector<Id>{ hunted }, hunted));
        CHECK(SfkHunt::IsCatch(std::vector<Id>{ pet, hunted }, hunted));
    }

    void TestHeroicShape()
    {
        std::uint32_t hunts = 0;
        for (std::int64_t t = Odo::kHuntFirst.count(); t <= 87000; t += Odo::kHuntEvery.count())
            ++hunts;
        CHECK(hunts == 4);
        CHECK(hunts > Odo::kBellCount);
        CHECK(Near(Odo::kBloodFrenzyPct, 20.f));
        CHECK(Near(Odo::kDeafenedPct, 25.f));
        CHECK(Odo::kDeafenedMs == 5000);
    }
}

int main()
{
    TestSliceAndArena();
    TestSpellIds();
    TestHuntNumbers();
    TestEchoHunt();
    TestCatchSlack();
    TestMaul();
    TestBellPoints();
    TestCanRing();
    TestChooseBell();
    TestCatchIsTheHuntedPlayer();
    TestBellBoard();
    TestHowls();
    TestGripLanding();
    TestHeroicShape();
    return Report("sfk_odo_test");
}
