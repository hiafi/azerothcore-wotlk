// Host tests for JergoshLogic.h (D2: Jergosh the Invoker): the slice and the room, the clock (cadence, the Conflagrate
// window, the cap of three burns, kicks and their 2 s lock), the picks, the fire's spread, the Tithe, the wisp's start.
// `rfc_jergosh_test table` prints who burns at each Conflagrate and his swings per group of kickers.
#include "JergoshLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <set>
#include <string>
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

    // Deterministic on every compiler (xorshift).
    struct Dice
    {
        std::uint64_t state;

        explicit Dice(std::uint64_t seed) : state(seed * 0x9E3779B97F4A7C15ull + 1) { }
        std::uint32_t Below(std::uint32_t n)
        {
            state ^= state << 13;
            state ^= state >> 7;
            state ^= state << 17;
            return static_cast<std::uint32_t>((state >> 16) % n);
        }
    };

    struct Setup
    {
        bool heroic = false;
        std::uint64_t lengthMs = 300000;
        std::uint32_t tickMs = 100;
        std::uint32_t players = 5;
        std::uint32_t kickers = 0;
        std::uint32_t kickPct = 100;        // of the casts a ready kick answers
        std::uint32_t kickCooldownMs = 10000;
        std::uint32_t lockMs = Tune::kKickLockMs;
        std::uint64_t seed = 1;
    };

    struct Run
    {
        std::vector<Fired> fired;           // casts started
        std::vector<std::uint32_t> burning; // at each Conflagrate's start
        std::uint32_t skipped = 0;          // an Immolate that would run into Conflagrate
        std::uint32_t full = 0;             // an Immolate beat with three burning
        std::uint32_t kicked = 0;
        std::uint32_t swings = 0;
        std::uint32_t maxBurning = 0;

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

    // The AI's loop: one cast at a time, a burn at the end of a whole Immolate on someone who does not burn, all of
    // them gone at Conflagrate's end (a clean spread: nobody relit), a kick from the first ready kicker 0.1 to 1.8 s
    // into an Immolate (or a Drain Soul), which refuses that school for `lockMs` from the kick, a 2.0 s swing when he
    // is free (a completed Immolate resets it: Spell::IsAutoActionResetSpell).
    Run Simulate(Setup const& s)
    {
        Run run;
        Dice dice(s.seed);
        Timeline t;
        t.Start(s.heroic);
        std::vector<std::uint64_t> burnsUntil(s.players, 0);
        std::vector<std::uint64_t> ready(s.kickers, 0);
        std::uint64_t busyUntil = 0;
        std::uint64_t kickAt = 0;           // the kick on the cast that runs (0: none)
        std::uint64_t fireLock = 0;
        std::uint64_t shadowLock = 0;
        std::uint64_t swingAt = 0;
        Act casting = Act::None;
        auto const unlit = [&]
        {
            std::vector<std::size_t> out;
            for (std::size_t i = 0; i < burnsUntil.size(); ++i)
                if (burnsUntil[i] <= t.Now())
                    out.push_back(i);
            return out;
        };
        while (t.Now() < s.lengthMs)
        {
            if (t.Advance(s.tickMs))
                ++run.skipped;
            if (casting != Act::None && kickAt && t.Now() >= kickAt)
            {
                // The lock from the kick; the hook's 2 s is not the kick's own.
                (casting == Act::Immolate ? fireLock : shadowLock) = t.Now() + s.lockMs;
                busyUntil = t.Now();
                casting = Act::None;
                kickAt = 0;
                ++run.kicked;
            }
            if (t.Now() < busyUntil)
                continue;
            if (casting == Act::Immolate)
            {
                std::vector<std::size_t> const free = unlit();
                burnsUntil[free[dice.Below(static_cast<std::uint32_t>(free.size()))]] =
                    t.Now() + Tune::kImmolateDurationMs;
                run.maxBurning = std::max(run.maxBurning, static_cast<std::uint32_t>(s.players - unlit().size()));
                swingAt = t.Now() + 2000;
            }
            else if (casting == Act::Conflagrate)
                std::fill(burnsUntil.begin(), burnsUntil.end(), 0);
            casting = Act::None;

            Act const act = t.Next();
            std::size_t const burning = s.players - unlit().size();
            // Conflagrate's bar is Arcane: no lockout of his reaches it. The curse is Shadow. A locked school: refused.
            bool const locked = (act == Act::Immolate && t.Now() <= fireLock && fireLock)
                || ((act == Act::DrainSoul || act == Act::Curse) && t.Now() <= shadowLock && shadowLock);
            if (act == Act::Immolate && (ImmolateFull(burning) || burning == s.players))
            {
                ++run.full;
                t.Done(act);
            }
            else if (locked)
                t.Retry(act);
            else if (act != Act::None)
            {
                t.Done(act);
                run.fired.push_back({ act, t.Now() });
                if (act == Act::Conflagrate)
                    run.burning.push_back(static_cast<std::uint32_t>(burning));
                busyUntil = t.Now() + CastMs(act);
                casting = CastMs(act) ? act : Act::None;
                if (act == Act::Immolate || act == Act::DrainSoul)
                    for (std::uint64_t& kick : ready)
                        if (kick <= t.Now() && dice.Below(100) < s.kickPct)
                        {
                            kickAt = t.Now() + 100 + dice.Below(Tune::kImmolateCastMs - 300);
                            kick = kickAt + s.kickCooldownMs;
                            break;
                        }
            }
            if (casting == Act::None && t.Now() >= swingAt)
            {
                ++run.swings;
                swingAt = t.Now() + 2000;
            }
        }
        return run;
    }

    // The mean of who burns at the first three Conflagrates, and the swings a minute, over `trials` fights.
    struct Averages
    {
        double burning[3] = {};
        double swings = 0.0;
        double kicked = 0.0;
        double immolates = 0.0;
        std::uint32_t max = 0;
    };

    Averages Average(Setup s, std::uint32_t trials)
    {
        Averages out;
        s.lengthMs = 60000;
        for (std::uint32_t i = 0; i < trials; ++i)
        {
            s.seed = i + 1;
            Run const run = Simulate(s);
            CHECK(run.burning.size() == 3);
            for (std::size_t c = 0; c < 3 && c < run.burning.size(); ++c)
                out.burning[c] += double(run.burning[c]) / trials;
            out.swings += double(run.swings) / trials;
            out.kicked += double(run.kicked) / trials;
            out.immolates += double(run.Times(Act::Immolate).size()) / trials;
            out.max = std::max(out.max, run.maxBurning);
        }
        return out;
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
        CHECK(Tune::kHealth.normal == 70 * 307);
        CHECK(Tune::kHealth.heroic == 157 * 2136);
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
                Setup s;
                s.heroic = heroic;
                s.tickMs = tick;
                Run const run = Simulate(s);
                std::vector<std::uint64_t> const conflagrate = run.Times(Act::Conflagrate);
                CHECK(conflagrate.size() == 15);
                // On its grid to the tick, so the fire one Conflagrate lit is still burning at the next one's end.
                for (std::size_t i = 0; i < conflagrate.size(); ++i)
                    CHECK(conflagrate[i] >= 16000 + i * 20000 && conflagrate[i] < 16000 + i * 20000 + tick);
                // The curse: 1 s, then every 30 s (within a cast of its beat).
                std::vector<std::uint64_t> const curse = run.Times(Act::Curse);
                CHECK(curse.size() == 10);
                CHECK(curse[0] < 1000 + tick);
                for (std::size_t i = 0; i < curse.size(); ++i)
                    CHECK(curse[i] <= 1000 + i * 30000 + 5500);
                // Drain Soul: heroic only, every 20 s from 10 s, at most an Immolate late.
                std::vector<std::uint64_t> const drain = run.Times(Act::DrainSoul);
                CHECK(drain.size() == (heroic ? 15u : 0u));
                for (std::size_t i = 0; i < drain.size(); ++i)
                    CHECK(drain[i] >= 10000 + i * 20000 && drain[i] <= 12000 + i * 20000 + tick);
                // Nobody kicks: three burn at every Conflagrate, never four.
                CHECK(run.burning.size() == conflagrate.size());
                for (std::uint32_t const burning : run.burning)
                    CHECK(burning == Tune::kImmolateMaxBurning);
                CHECK(run.maxBurning == Tune::kImmolateMaxBurning);
                CHECK(run.full > 0 && run.Times(Act::Immolate).size() <= 3 * 16);
                // Nothing overlaps.
                for (std::size_t i = 1; i < run.fired.size(); ++i)
                    CHECK(run.fired[i].at >= run.fired[i - 1].at + CastMs(run.fired[i - 1].act));
            }
        }
        // First beats (the curse at 1 s, Immolate at 3 s, 6 s and 9 s; the 12 s one finds three burning).
        Setup s;
        s.lengthMs = 17000;
        Run const normal = Simulate(s);
        CHECK(normal.fired.size() == 5);
        CHECK(normal.fired[0].act == Act::Curse && normal.fired[0].at == 1000);
        for (std::size_t i = 1; i < 4; ++i)
            CHECK(normal.fired[i].act == Act::Immolate && normal.fired[i].at == i * 3000);
        CHECK(normal.fired[4].act == Act::Conflagrate && normal.fired[4].at == 16000);
        CHECK(normal.full == 1 && normal.skipped == 1);      // 12 s; 15 s would run into Conflagrate
        s.heroic = true;
        Run const heroic = Simulate(s);
        CHECK(heroic.Times(Act::Immolate).size() == 3);
        CHECK(heroic.Times(Act::DrainSoul).size() == 1);
        CHECK(heroic.Times(Act::DrainSoul)[0] == 11000);     // after the Immolate of 9 s
        // Fewer players than the cap: everyone burns, nothing stops.
        s.lengthMs = 60000;
        s.players = 2;
        Run const pair = Simulate(s);
        CHECK(pair.maxBurning == 2 && pair.burning.size() == 3 && pair.burning[2] == 2);

        // The cap counts everyone burning, whoever lit them (heroic's spread may exceed it).
        CHECK(!ImmolateFull(0) && !ImmolateFull(2) && ImmolateFull(3) && ImmolateFull(5));
    }

    void TestKicks()
    {
        // The worst case, a kick for every cast, and locks longer than his: Conflagrate stays on its grid (Arcane), no
        // Drain Soul is late or lost, and the curse still lands.
        for (bool const heroic : { false, true })
            for (std::uint32_t const lock : { Tune::kKickLockMs, 4000u, 8000u })
            {
                Setup s;
                s.heroic = heroic;
                s.kickers = 5;
                s.kickCooldownMs = 0;
                s.lockMs = lock;
                Run const run = Simulate(s);
                std::vector<std::uint64_t> const conflagrate = run.Times(Act::Conflagrate);
                CHECK(conflagrate.size() == 15);
                for (std::size_t i = 0; i < conflagrate.size(); ++i)
                    CHECK(conflagrate[i] == 16000 + i * 20000);
                CHECK(run.Times(Act::Curse).size() >= 9);
                // (The run's last cast may not be kicked yet.)
                CHECK(run.kicked + 1 >= run.Times(Act::Immolate).size() + run.Times(Act::DrainSoul).size());
                CHECK(run.maxBurning == 0);
                CHECK(run.Times(Act::Immolate).size() >= 15);
                std::vector<std::uint64_t> const drain = run.Times(Act::DrainSoul);
                CHECK(drain.size() == (heroic ? 15u : 0u));
                for (std::size_t i = 0; i < drain.size(); ++i)
                    CHECK(drain[i] >= 10000 + i * 20000 && drain[i] <= 12100 + i * 20000);
            }

        // His lock is a refusal of 2 s and no more: the cast after a kick comes 4.4 s after it started at the latest
        // (a kick at 1.8 s, the lock, a retry), but for the Conflagrate in between.
        Setup s;
        s.kickers = 5;
        s.kickCooldownMs = 0;
        Run const run = Simulate(s);
        std::vector<std::uint64_t> const immolate = run.Times(Act::Immolate);
        CHECK(immolate.size() >= 60);
        std::vector<std::uint64_t> const conflagrate = run.Times(Act::Conflagrate);
        for (std::size_t i = 1; i < immolate.size(); ++i)
        {
            bool const across = std::any_of(conflagrate.begin(), conflagrate.end(), [&](std::uint64_t at)
            {
                return at > immolate[i - 1] && at < immolate[i];
            });
            CHECK(immolate[i] - immolate[i - 1] <= (across ? 9100u : 4400u));
        }
    }

    // Kicks on a 10 s cooldown, answered 95% (bots) and 50% (people) of the time.
    void TestKickers(bool print)
    {
        for (bool const heroic : { false, true })
            for (std::uint32_t const pct : { 95u, 50u })
                for (std::uint32_t kickers = 0; kickers <= 3; ++kickers)
                {
                    Setup s;
                    s.heroic = heroic;
                    s.kickers = kickers;
                    s.kickPct = pct;
                    Averages const a = Average(s, 2000);
                    if (print)
                        std::printf("%s %u%% kickers=%u burning %.2f %.2f %.2f  immolates %.1f kicked %.1f swings %.1f "
                            "a minute\n", heroic ? "heroic" : "normal", pct, kickers, a.burning[0], a.burning[1],
                            a.burning[2], a.immolates, a.kicked, a.swings);
                    CHECK(a.max <= Tune::kImmolateMaxBurning);
                    // The fuel: three with nobody kicking, still two after the first Conflagrate with two kickers,
                    // and three cannot put it all out. The tank is hit all along.
                    for (std::size_t c = 0; c < 3; ++c)
                    {
                        CHECK(a.burning[c] <= 3.0 + 1e-6 && a.burning[c] >= 0.75);
                        if (kickers == 0)
                            CHECK(a.burning[c] >= 3.0 - 1e-6);
                        if (kickers <= 1)
                            CHECK(a.burning[c] >= (c || !heroic ? 2.95 : 1.95));
                        if (kickers == 2 && c)
                            CHECK(a.burning[c] >= 2.3);
                    }
                    CHECK(a.swings >= 9.0);
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

int main(int argc, char** argv)
{
    TestRoom();
    TestCadence();
    TestKicks();
    TestKickers(argc > 1 && std::string(argv[1]) == "table");
    TestGrid();
    TestPicks();
    TestFire();
    TestTithe();
    TestWisp();
    return Report("rfc_jergosh_test");
}
