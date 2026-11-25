// Host tests for JergoshLogic.h (D2: Jergosh the Invoker): the slice and the room, the clock (cadence, the Conflagrate
// window, lockouts), the picks, the fire's spread, the Tithe, the wisp's start.
#include "JergoshLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace RagefireChasmRework;
using namespace RfcJergosh;

namespace
{
    struct Fired
    {
        Act act;
        std::uint64_t at;
    };

    struct Run
    {
        std::vector<Fired> fired;
        std::uint32_t skipped = 0;

        std::vector<std::uint64_t> Times(Act act) const
        {
            std::vector<std::uint64_t> out;
            for (Fired const& f : fired)
                if (f.act == act)
                    out.push_back(f.at);
            return out;
        }
    };

    std::uint32_t CastMs(Act act)
    {
        switch (act)
        {
            case Act::Conflagrate:
                return Tune::kConflagrateCastMs;
            case Act::DrainSoul:
                return Tune::kDrainSoulChannelMs;
            case Act::Immolate:
                return Tune::kImmolateCastMs;
            default:
                return 0;
        }
    }

    // The AI's loop: one cast at a time, kicks (when `kick`) 1 s into every Immolate and Drain Soul, which refuse that
    // school for `lockMs` (a kick locks the school: section 3.5 rule 25).
    Run Simulate(bool heroic, std::uint64_t lengthMs, std::uint32_t tickMs, bool kick, std::uint32_t lockMs)
    {
        Run run;
        Timeline t;
        t.Start(heroic);
        std::uint64_t busyUntil = 0;
        std::uint64_t fireLock = 0;
        std::uint64_t shadowLock = 0;
        while (t.Now() < lengthMs)
        {
            if (t.Advance(tickMs))
                ++run.skipped;
            if (t.Now() < busyUntil)
                continue;
            Act const act = t.Next();
            if (act == Act::None)
                continue;
            // Conflagrate's bar is Arcane: no lockout of his reaches it. The curse is Shadow.
            if ((act == Act::Immolate && t.Now() < fireLock)
                || ((act == Act::DrainSoul || act == Act::Curse) && t.Now() < shadowLock))
            {
                t.Retry(act);
                continue;
            }
            t.Done(act);
            run.fired.push_back({ act, t.Now() });
            busyUntil = t.Now() + CastMs(act);
            if (kick && (act == Act::Immolate || act == Act::DrainSoul))
            {
                busyUntil = t.Now() + 1000;
                (act == Act::Immolate ? fireLock : shadowLock) = busyUntil + lockMs;
            }
        }
        return run;
    }

    void TestRoom()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.Contains(SPELL_JR_IMMOLATE));
        CHECK(kSpellSlice.Contains(SPELL_JR_FEED_LOOK));
        // His spawn is on his arena, and the slot's arena is the same one.
        CHECK(JergoshArena().Contains(kJergoshSpawn.XY(), kJergoshSpawn.z));
        CHECK(ArenaFor(BOSS_JERGOSH).Contains(kJergoshSpawn.XY(), kJergoshSpawn.z));
        CHECK(JergoshArena().Contains(kOfferingSpot.XY(), kOfferingSpot.z));
        CHECK(JergoshArena().Contains(kHallDisc.XY(), kHallDisc.z));
        // The build spec's health and the wisp's walk (50 yd, 16.5 s: section 7 #21 A).
        CHECK(Tune::kHealth.normal == 28 * 307);
        CHECK(Tune::kHealth.heroic == 118 * 2136);
        float const walk = DungeonKit::Distance(kJergoshSpawn.XY(), kOfferingSpot.XY());
        CHECK(std::fabs(walk - 50.f) < 1.f);
        CHECK(std::fabs(walk / Tune::kWispSpeed - 16.5f) < 0.3f);
        CHECK(kImmolateTicks == 7);
    }

    void TestCadence()
    {
        for (bool const heroic : { false, true })
        {
            for (std::uint32_t const tick : { 50u, 100u, 200u })
            {
                Run const run = Simulate(heroic, 300000, tick, false, 0);
                std::vector<std::uint64_t> const conflagrate = run.Times(Act::Conflagrate);
                CHECK(conflagrate.size() == 15);
                // On its grid to the tick, so the fire one Conflagrate lit is still burning at the next one's end.
                for (std::size_t i = 0; i < conflagrate.size(); ++i)
                    CHECK(conflagrate[i] >= 16000 + i * 20000 && conflagrate[i] < 16000 + i * 20000 + tick);
                // The curse: 1 s, then every 30 s (within a cast of its beat).
                std::vector<std::uint64_t> const curse = run.Times(Act::Curse);
                CHECK(curse.size() == 10);
                CHECK(curse[0] < 1000 + tick);
                // Drain Soul: heroic only, every 20 s from 10 s, at most an Immolate late.
                std::vector<std::uint64_t> const drain = run.Times(Act::DrainSoul);
                CHECK(drain.size() == (heroic ? 15u : 0u));
                for (std::size_t i = 0; i < drain.size(); ++i)
                    CHECK(drain[i] >= 10000 + i * 20000 && drain[i] <= 12000 + i * 20000 + tick);
                // Every burn landed since the last Conflagrate's end is there at the next: 2 on normal, 2 or 3 heroic.
                std::vector<std::uint64_t> const immolate = run.Times(Act::Immolate);
                for (std::size_t i = 0; i < conflagrate.size(); ++i)
                {
                    std::uint64_t const from = i ? conflagrate[i - 1] : 0;
                    std::uint64_t const resolve = conflagrate[i] + Tune::kConflagrateCastMs;
                    std::uint32_t burning = 0;
                    for (std::uint64_t const at : immolate)
                    {
                        std::uint64_t const lands = at + Tune::kImmolateCastMs;
                        if (at >= from && lands <= resolve && lands + Tune::kImmolateDurationMs > resolve)
                            ++burning;
                    }
                    CHECK(burning >= 2 && burning <= (heroic ? 3u : 2u));
                }
                // Nothing overlaps.
                for (std::size_t i = 1; i < run.fired.size(); ++i)
                    CHECK(run.fired[i].at >= run.fired[i - 1].at + CastMs(run.fired[i - 1].act));
            }
        }
        // First beats (the curse at 1 s, Immolate at 3 s).
        Run const normal = Simulate(false, 17000, 100, false, 0);
        CHECK(normal.fired.size() == 4);
        CHECK(normal.fired[0].act == Act::Curse && normal.fired[0].at == 1000);
        CHECK(normal.fired[1].act == Act::Immolate && normal.fired[1].at == 3000);
        CHECK(normal.fired[2].act == Act::Immolate && normal.fired[2].at == 11000);
        CHECK(normal.fired[3].act == Act::Conflagrate && normal.fired[3].at == 16000);
        // Heroic: the 15 s Immolate would run into Conflagrate and is skipped.
        Run const heroic = Simulate(true, 17000, 100, false, 0);
        CHECK(heroic.Times(Act::Immolate).size() == 2);
        CHECK(heroic.skipped == 1);
        CHECK(heroic.Times(Act::DrainSoul).size() == 1);
        CHECK(heroic.Times(Act::DrainSoul)[0] == 11000);     // after the Immolate of 9 s
    }

    void TestLockouts()
    {
        // Every kickable cast kicked, up to the longest lockout: Conflagrate stays on its grid (Arcane) and no cast
        // starves.
        for (bool const heroic : { false, true })
            for (std::uint32_t const lock : { 4000u, 8000u })
            {
                Run const run = Simulate(heroic, 300000, 100, true, lock);
                std::vector<std::uint64_t> const conflagrate = run.Times(Act::Conflagrate);
                CHECK(conflagrate.size() == 15);
                for (std::size_t i = 0; i < conflagrate.size(); ++i)
                    CHECK(conflagrate[i] == 16000 + i * 20000);
                CHECK(run.Times(Act::Curse).size() >= 9);
                CHECK(run.Times(Act::Immolate).size() >= 15);
                CHECK(run.Times(Act::DrainSoul).size() == (heroic ? 15u : 0u));
            }
    }

    void TestGrid()
    {
        Grid g;
        CHECK(!g.Running() && !g.Due(1000000));
        g.Done(1000);       // not running: nothing
        CHECK(!g.Due(1000000));
        g.Start(3000, 6000);
        CHECK(!g.Due(2999) && g.Due(3000));
        g.Retry(3000);
        CHECK(!g.Due(3000 + kRetryMs - 1) && g.Due(3000 + kRetryMs));
        g.Done(4000);
        CHECK(g.due == 9000 && !g.Due(8999) && g.Due(9000));
        g.Done(22000);      // late by two beats: the next one ahead
        CHECK(g.due == 27000);

        Timeline t;
        CHECK(t.Next() == Act::None);
        t.Start(true);
        CHECK(t.In(Act::DrainSoul) == 10000 && t.In(Act::Immolate) == 3000 && t.In(Act::Curse) == 1000);
        CHECK(t.In(Act::None) == 0);
        t.Start(false);
        CHECK(t.In(Act::DrainSoul) == 0);
    }

    void TestPicks()
    {
        auto const first = [](std::uint32_t) { return 0u; };
        // The tank alone is left unburned: he is the pick (tank included); everyone burning: nobody.
        std::vector<DungeonKit::PickCandidate> const c{ { 1, 5.f, true, true, false }, { 2, 9.f, false, true, true },
            { 3, 9.f, false, true, false } };
        CHECK(DungeonKit::PickFrom(c, ImmolatePick({ 2, 3 }), first) == 0u);
        CHECK(DungeonKit::PickFrom(c, ImmolatePick({ 1, 3 }), first) == 1u);
        CHECK(!DungeonKit::PickFrom(c, ImmolatePick({ 1, 2, 3 }), first));
        std::set<std::size_t> seen;
        for (std::uint32_t i = 0; i < 3; ++i)
            seen.insert(*DungeonKit::PickFrom(c, DrainSoulPick({}), [i](std::uint32_t n) { return i % n; }));
        CHECK(seen.size() == 3);
        // Whoever is off the hall is skipped, unless nobody is in it.
        std::vector<std::uint64_t> const off = Outsiders({ { 1, false }, { 2, true }, { 3, false } });
        CHECK((off == std::vector<std::uint64_t>{ 1, 3 }));
        for (std::uint32_t i = 0; i < 3; ++i)
            CHECK(DungeonKit::PickFrom(c, DrainSoulPick(off), [i](std::uint32_t n) { return i % n; }) == 1u);
        CHECK(!DungeonKit::PickFrom(c, ImmolatePick({ 1, 3, 2 }), first));  // the one in the hall burns: nobody
        CHECK(Outsiders({ { 1, false }, { 2, false } }).empty());
        CHECK(Outsiders({}).empty());
    }

    void TestFire()
    {
        // Lost rings: never on the tick that jumps past the bar's end (the registry resolves after the AI).
        CHECK(!RingsLost(10000, 10000) && !RingsLost(10000 + kRetryMs, 10000));
        CHECK(RingsLost(10001 + kRetryMs, 10000));
        std::uint64_t const before = 9900;      // a 4 s lag tick: the clock after it is 13,900
        CHECK(!RingsLost(before, 10000) && RingsLost(before + 4000, 10000));

        // Normal: consumed, nobody lit. Heroic: each distinct hit player, once, whoever burned before.
        CHECK(BurningAfter({ 4, 5 }, false).empty());
        CHECK(BurningAfter({}, true).empty());
        CHECK((BurningAfter({ 4, 5, 4 }, true) == std::vector<std::uint64_t>{ 4, 5 }));
        // Two bearers (1 and 2) standing together light each other.
        CHECK((BurningAfter({ 2, 1 }, true) == std::vector<std::uint64_t>{ 2, 1 }));
    }

    void TestTithe()
    {
        CHECK(TitheFactor(0) == 1.f);
        CHECK(std::fabs(TitheFactor(1) - 1.15f) < 1e-5f);
        CHECK(std::fabs(TitheFactor(10) - 2.5f) < 1e-5f);      // no cap
        CHECK(TitheScale(0) == 1.f);
        CHECK(std::fabs(TitheScale(5) - 1.2f) < 1e-5f);
        CHECK(TitheScale(12) == TitheScale(5));
        // A clean ring hit stays under 75% up to four souls (the ceiling is the group's to keep).
        CHECK(Tune::kConflagrateOthersPct.heroic * TitheFactor(4) < 75.f);
    }

    void TestWisp()
    {
        Vec2 const goal = kOfferingSpot.XY();
        auto const arena = JergoshArena();
        // From his spawn: 4 yd along the straight line to the spot.
        Vec2 const spawn = kJergoshSpawn.XY();
        Vec2 const p = WispStart(spawn, goal);
        CHECK(std::fabs(DungeonKit::Distance(spawn, p) - Tune::kWispSpawnAheadYd) < 0.01f);
        CHECK(std::fabs(DungeonKit::Distance(spawn, goal) - DungeonKit::Distance(p, goal) - Tune::kWispSpawnAheadYd)
            < 0.01f);
        // Every owner's spot on the hall floor: on the floor, off the owner's touch, never on the offering spot.
        std::uint32_t owners = 0;
        for (float x = -393.f; x <= -317.f; x += 1.f)
            for (float y = 155.f; y <= 245.f; y += 1.f)
            {
                Vec2 const owner{ x, y };
                if (!arena.Contains(owner, kJergoshSpawn.z))
                    continue;
                ++owners;
                Vec2 const start = WispStart(owner, goal);
                CHECK(arena.Contains(start, kJergoshSpawn.z));
                CHECK(DungeonKit::Distance(owner, start) > Tune::kWispTouchYd);
                CHECK(DungeonKit::Distance(start, goal) >= kWispGoalClearYd - 0.01f);
            }
        CHECK(owners > 2500);
        // An owner off the hall (the ridge above, the tunnels): the wisp still starts in it, at its height.
        for (Vec2 const owner : { kRidgeSafeDisc.XY(), kBazzalanSpawn.XY(), kRidgeNeck.XY(), Vec2{ -306.5f, 218.5f } })
            CHECK(DungeonKit::Distance(WispStart(owner, goal),
                ClampInto(kHallArenaPolygon, WispStart(owner, goal))) < 0.3f);
        // An owner on the spot itself.
        CHECK(DungeonKit::Distance(WispStart(goal, goal), goal) >= kWispGoalClearYd);
    }
}

int main()
{
    TestRoom();
    TestCadence();
    TestLockouts();
    TestGrid();
    TestPicks();
    TestFire();
    TestTithe();
    TestWisp();
    return Report("rfc_jergosh_test");
}
