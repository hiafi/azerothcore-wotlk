// Host tests for MalekiLogic.h (S12: Maleki the Pallid): the slice and the arena, the picks, Icy Death's growth, the
// Shatter, Siphon and tomb numbers, the never-paused timeline (the Siphon's grid, the Eye, the 60 s collision,
// Frostbolt's wait), the eye spot and the heroic drift.
#include "MalekiLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace StratholmeRework;
using namespace StratMaleki;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A deterministic "random": always the first, or always the last of n.
    std::uint32_t First(std::uint32_t /*n*/) { return 0; }
    std::uint32_t Last(std::uint32_t n) { return n ? n - 1 : 0; }

    void TestSliceAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { std::uint32_t(SPELL_MK_ICY_DEATH), std::uint32_t(SPELL_MK_ICY_DEATH_LOOK),
            std::uint32_t(SPELL_MK_SHATTER), std::uint32_t(SPELL_MK_SHATTER_ROOT), std::uint32_t(SPELL_MK_SIPHON_CAST),
            std::uint32_t(SPELL_MK_SIPHON_CHANNEL), std::uint32_t(SPELL_MK_SIPHON_DRAIN),
            std::uint32_t(SPELL_MK_SIPHON_HEAL), std::uint32_t(SPELL_MK_ICE_TOMB_HOLD),
            std::uint32_t(SPELL_MK_ICE_TOMB_DRAIN), std::uint32_t(SPELL_MK_ICE_TOMB_HEAL),
            std::uint32_t(SPELL_MK_EYE_STORM), std::uint32_t(SPELL_MK_EYE_CHANNEL),
            std::uint32_t(SPELL_MK_EYE_STORM_LOOK), std::uint32_t(SPELL_MK_ICE_TOMB_LOOK),
            std::uint32_t(SPELL_MK_FROSTBITE_LOOK) })
        {
            CHECK(kSpellSlice.Contains(id));
            CHECK(ids.insert(id).second);
        }
        CHECK(ids.size() == 16);
        // His own creatures are wave 1 ids.
        CHECK(kCreaturesWave1.Contains(NPC_ST_ICE_TOMB));
        CHECK(kCreaturesWave1.Contains(NPC_ST_EYE));
        // The boss spawns inside his arena; the C++ reads its one circle (25 yd) for the eye's aim and drift.
        CHECK(MalekiArena().Contains(kMalekiSpawn.XY(), kMalekiSpawn.z));
        CHECK(ArenaFor(BOSS_MALEKI).Contains(kMalekiSpawn.XY(), kMalekiSpawn.z));
        CHECK(MalekiArena().regions.size() == 1);
        CHECK(Near(MalekiArena().regions.front().radius, 25.f));
    }

    void TestCursePick()
    {
        // A fresh non-tank first.
        std::vector<Candidate> c{ { 1, 0, true, false }, { 2, 2, false, false }, { 3, 0, false, false },
            { 4, 0, false, true } };
        auto pick = PickCurseTarget(c, First);
        CHECK(pick && *pick == 2);
        // Everyone has it: the fewest stacks (ties by rand), never the tank, a prisoner or a capped player.
        c = { { 1, 0, true, false }, { 2, 3, false, false }, { 3, 1, false, false }, { 4, 1, false, false },
            { 5, 0, false, true }, { 6, 5, false, false } };
        pick = PickCurseTarget(c, First);
        CHECK(pick && *pick == 2);
        pick = PickCurseTarget(c, Last);
        CHECK(pick && *pick == 3);
        // Only the tank: nobody.
        c = { { 1, 0, true, false } };
        CHECK(!PickCurseTarget(c, First));
        CHECK(!PickCurseTarget(std::vector<Candidate>{}, First));
    }

    void TestSiphonPick()
    {
        std::vector<Candidate> c{ { 1, 4, true, false }, { 2, 2, false, false }, { 3, 3, false, false },
            { 4, 3, false, false }, { 5, 0, false, true } };
        auto pick = PickSiphonCarrier(c, First);
        CHECK(pick && *pick == 2);
        pick = PickSiphonCarrier(c, Last);
        CHECK(pick && *pick == 3);
        // Nobody with stacks: no Siphon.
        c = { { 1, 0, false, false }, { 2, 0, true, false } };
        CHECK(!PickSiphonCarrier(c, First));
    }

    void TestGrowthAndNumbers()
    {
        CurseClock clock;
        CHECK(clock.Advance(5999, false) == 0);
        CHECK(clock.Advance(1, false) == 1);
        CHECK(clock.Advance(12000, false) == 2);
        CurseClock heroic;
        CHECK(heroic.Advance(4000, true) == 1);
        CHECK(heroic.Advance(3999, true) == 0);
        CHECK(MsToTomb(false) == 24000);    // ST: "reaches 5 stacks 24 sec after it lands"
        CHECK(MsToTomb(true) == 16000);     // ST heroic: 16 sec
        CHECK(!Freezes(4));
        CHECK(Freezes(5));
        CHECK(kCurseMaxStacks * std::uint32_t(kCurseSlowPct) == 50);    // 50% slow at 5

        CHECK(Near(ShatterPct(1, false), 7.f));
        CHECK(Near(ShatterPct(4, false), 28.f));    // ST: "up to 28%"
        CHECK(Near(ShatterPct(4, true), 32.f));
        CHECK(Near(ShatterPct(5, false), 28.f));    // the fifth stack is the tomb's
        CHECK(Near(ShatterPct(0, false), 0.f));
        CHECK(kFrostbiteStacks(false) == 0 && kFrostbiteStacks(true) == 1);

        CHECK(!SiphonSnaps({ 0.f, 0.f }, { 11.9f, 0.f }));
        CHECK(SiphonSnaps({ 0.f, 0.f }, { 12.f, 0.f }));
        CHECK(SiphonSnaps({ 0.f, 0.f }, { 9.f, 9.f }));
        CHECK(StacksEaten(999, 4) == 0);
        CHECK(StacksEaten(1000, 4) == 1);
        CHECK(StacksEaten(5000, 4) == 4);
        CHECK(StacksEaten(9000, 9) == 5);
        // ST failing path check: a finished Siphon on 4 stacks heals him 8% (normal) and costs the carrier 24%.
        CHECK(Near(4.f * kSiphonHealPct(false), 8.f));
        CHECK(Near(4.f * kSiphonDrainPct(false), 24.f));
        CHECK(PctOf(170000, kSiphonHealPct(false)) == 3400);
        CHECK(PctOf(210000, kTombHealPct(true)) == 3150);
        CHECK(kTombHealth(false) == 8000 && kTombHealth(true) == 12000);
        CHECK(kTombMaxMs == 8000);
    }

    void TestTimeline()
    {
        // Ticks of 100 ms for 125 s: the beats fire on their grids, nothing in the way.
        Timeline t;
        std::vector<std::uint32_t> curses;
        std::vector<std::uint32_t> siphons;
        std::vector<std::uint32_t> marks;
        std::vector<std::uint32_t> storms;
        for (std::uint32_t ms = 0; ms < 125000; ms += 100)
        {
            t.Advance(100);
            if (t.CurseDue())
            {
                curses.push_back(t.now);
                t.CurseDone();
            }
            if (t.SiphonDue())
            {
                siphons.push_back(t.now);
                t.SiphonDone();
            }
            if (t.EyeDue())
            {
                marks.push_back(t.now);
                t.EyeMarked();
            }
            if (t.StormDue())
            {
                storms.push_back(t.now);
                t.StormStarted();
            }
            if (t.StormOver())
                t.EyeOver();
        }
        CHECK((curses == std::vector<std::uint32_t>{ 5000, 17000, 29000, 41000, 53000, 65000, 77000, 89000, 101000,
            113000, 125000 }));
        CHECK((siphons == std::vector<std::uint32_t>{ 15000, 35000, 55000, 75000, 95000, 115000 }));
        CHECK((marks == std::vector<std::uint32_t>{ 27000, 57000, 87000, 117000 }));
        CHECK((storms == std::vector<std::uint32_t>{ 30000, 60000, 90000, 120000 }));

        // The 60 s collision (ST "The collisions"): the 55 s Siphon's channel (57-62 s) runs into the 60 s storm.
        CHECK(55000 + kSiphonCastMs == 57000 && 57000 + kSiphonChannelMs > 60000);

        // A Siphon held 1 s by the storm's channel (35 s -> 36 s) keeps the next one on the grid.
        Timeline held;
        held.now = 36000;
        held.nextSiphon = 35000;
        held.SiphonDone();
        CHECK(held.nextSiphon == 55000);
        // Held past a whole period: that one is skipped.
        held.now = 80000;
        held.nextSiphon = 55000;
        held.SiphonDone();
        CHECK(held.nextSiphon == 95000);

        // The eye's stages and what is left of them.
        Timeline e;
        e.now = 27000;
        CHECK(e.EyeDue());
        e.EyeMarked();
        CHECK(e.eye == EyeStage::Marker && e.EyeLeftMs() == 3000 && e.nextEye == 57000);
        CHECK(!e.EyeDue());
        e.now = 29000;
        CHECK(e.EyeLeftMs() == 1000 && !e.StormDue() && e.NextStormAt() == 30000);
        e.now = 30000;
        CHECK(e.StormDue());
        e.StormStarted();
        CHECK(e.eye == EyeStage::Storm && e.EyeLeftMs() == 6000);
        e.now = 35500;
        CHECK(e.EyeLeftMs() == 500 && !e.StormOver());
        e.now = 36000;
        CHECK(e.StormOver());
        e.EyeOver();
        CHECK(e.eye == EyeStage::Idle && e.EyeLeftMs() == 0 && e.NextStormAt() == 60000);
    }

    void TestFrostboltWait()
    {
        Timeline t;
        t.now = 10000;
        t.nextFrostbolt = 10000;
        CHECK(t.FrostboltDue());
        CHECK(t.FrostboltClear(false));     // Siphon at 15 s, storm at 30 s
        CHECK(!t.FrostboltClear(true));     // a Siphon in progress
        t.now = 12900;
        CHECK(!t.FrostboltClear(false));    // the Siphon is 2.1 s away
        t.now = 25000;
        t.nextSiphon = 35000;
        CHECK(t.FrostboltClear(false));
        t.now = 27900;
        CHECK(!t.FrostboltClear(false));    // the storm starts 2.1 s from now
        t.now = 27000;
        t.EyeMarked();
        t.now = 27500;
        CHECK(t.FrostboltClear(false));     // marked: the storm is 2.5 s away, a 2 s bolt still fits
        t.now = 27900;
        CHECK(!t.FrostboltClear(false));    // 2.1 s away: it waits
        t.now = 30000;
        t.StormStarted();
        CHECK(!t.FrostboltClear(false));    // he channels the storm
        t.FrostboltDone(3000);
        CHECK(t.nextFrostbolt == 33000);
    }

    void TestEye()
    {
        // The aim from his spawn: toward his arena's center, 12 yd; the measured eye centers fit 10-14 yd.
        Vec2 const spawn = kMalekiSpawn.XY();
        Vec2 const plaza = MalekiArena().regions.front().center;
        Vec2 const aim = EyeAim(spawn, plaza, kMalekiSpawn.o);
        CHECK(Near(DungeonKit::Distance(spawn, aim), kEyeAimYd));
        CHECK(EyeSpotFits(spawn, aim));
        // The aim's slack never leaves the 10-14 yd band.
        CHECK(kEyeAimYd - kEyeAimSlackYd >= kEyeMinFromBossYd && kEyeAimYd + kEyeAimSlackYd <= kEyeMaxFromBossYd);
        for (Point3 const& c : kMalekiEyeCenters)
        {
            CHECK(EyeSpotFits(spawn, c.XY()));
            CHECK(MalekiArena().Contains(c.XY(), c.z));
        }
        // Standing on the plaza's center: along his spawn facing.
        Vec2 const onCenter = EyeAim(plaza, plaza, kMalekiSpawn.o);
        CHECK(Near(DungeonKit::Distance(plaza, onCenter), kEyeAimYd));
        // The aim lies toward the plaza (south-west of the stoop: x down, y up).
        CHECK(aim.x < spawn.x && aim.y > spawn.y);

        // The drawn donut keeps a hole: 8 / 32 and 6 / 24 (ratio 0.25).
        CHECK(Near(EyeDrawnOuter(kEyeRadius(false)), 32.f));
        CHECK(Near(EyeDrawnOuter(kEyeRadius(true)), 24.f));
        CHECK(kEyeRadius(false) / EyeDrawnOuter(kEyeRadius(false)) >= 0.25f - 1e-4f);
        // The hidden hit reaches past every corner of his arena from any eye in it.
        CHECK(kEyeStormReachYd >= 2.f * MalekiArena().regions.front().radius);

        // The heroic drift: 9 yd; a wall turns it back.
        CHECK(Near(kEyeDriftYd, 9.f));
        DriftLegs legs = EyeDriftLegs(20.f);
        CHECK(Near(legs.forward, 9.f) && Near(legs.back, 0.f));
        legs = EyeDriftLegs(4.f);
        CHECK(Near(legs.forward, 4.f) && Near(legs.back, 5.f));
        legs = EyeDriftLegs(0.2f);
        CHECK(Near(legs.forward, 0.f) && Near(legs.back, 9.f));
        legs = EyeDriftLegs(-3.f);
        CHECK(Near(legs.forward, 0.f) && Near(legs.back, 9.f));

        CHECK(Near(RayLeavesCircle({ 0.f, 0.f }, 0.f, { 0.f, 0.f }, 25.f), 25.f));
        CHECK(Near(RayLeavesCircle({ 10.f, 0.f }, 0.f, { 0.f, 0.f }, 25.f), 15.f));
        CHECK(Near(RayLeavesCircle({ 10.f, 0.f }, DungeonKit::kPi, { 0.f, 0.f }, 25.f), 35.f));
        CHECK(Near(RayLeavesCircle({ 30.f, 0.f }, 0.f, { 0.f, 0.f }, 25.f), 0.f));

        // The falling ice stays outside every spot the eye covers: the eye, its drift and the look's half width.
        CHECK(kStormLookRingYd(false) >= kEyeRadius(false) + kStormLookHalfWidthYd);
        CHECK(kStormLookRingYd(true) >= kEyeRadius(true) + kEyeDriftYd + kStormLookHalfWidthYd);
        std::vector<Vec2> const ring = StormLookRing({ 1.f, 2.f }, 12.f, 6, 0.3f);
        CHECK(ring.size() == 6);
        for (Vec2 const& p : ring)
            CHECK(Near(DungeonKit::Distance({ 1.f, 2.f }, p), 12.f));
        CHECK(Near(DungeonKit::Distance(ring[0], ring[1]), 12.f));     // a hexagon: side = radius
    }

    // R-1-B B-3: Weakened once per player per storm. The registry's hit gives it (once per player, registered once
    // per Eye); a Siphon carrier who took the storm only through the script's ticks owes one at the storm's end.
    void TestStormWeakened()
    {
        StormWeakenedBook book;
        CHECK(book.Owed().empty());
        book.RegistryHit(1);                // hit by the registry before the Siphon picked them
        book.CarrierTick(1);                // then the carrier, ticked by the script
        book.CarrierTick(2);                // a carrier the registry never hit
        book.CarrierTick(2);
        book.RegistryHit(3);                // never a carrier
        std::vector<std::uint64_t> owed = book.Owed();
        CHECK((owed.size()) == (std::size_t(1)));
        CHECK(!owed.empty() && owed.front() == 2u);
        book.RegistryHit(2);                // the Siphon ended mid-storm, the registry hit them: nothing owed
        CHECK(book.Owed().empty());
        book.Clear();
        book.CarrierTick(4);
        CHECK((book.Owed().size()) == (std::size_t(1)));

        // The marker and the drawn outline outlast the Siphon (cast + channel), so neither lapses nor fills mid-Siphon.
        CHECK(kSiphonMarkMs > kSiphonCastMs + kSiphonChannelMs);
        CHECK(kSiphonDrawnMs > kSiphonCastMs + kSiphonChannelMs);
        CHECK(kSpellSlice.Contains(SPELL_MK_SIPHON_MARK));
        CHECK(TAG_SIPHON_DRAWN != TAG_SIPHON && TAG_SIPHON_DRAWN != TAG_EYE_DRAWN && TAG_SIPHON_DRAWN != TAG_EYE);
    }
}

int main()
{
    TestSliceAndArena();
    TestCursePick();
    TestSiphonPick();
    TestGrowthAndNumbers();
    TestTimeline();
    TestFrostboltWait();
    TestEye();
    TestStormWeakened();
    return Report("strat_maleki_test");
}
