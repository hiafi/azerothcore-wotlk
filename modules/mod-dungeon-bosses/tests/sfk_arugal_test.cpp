// Host tests for Archmage Arugal (WP-S9): ArugalLogic.h. The slice and the arena; the Shadow Port spots and the wards
// on each spot's level; the never-paused timeline (normal and heroic casts never overlap, heroic's exact 5 s cycle);
// the Worgen's Curse arithmetic on the ruling 14 numbers (seep, wards, Thundershock, Void Bolt, Moonrise, Feral
// Power); the ward's dwell and life; the all-turned rule (handoff section 7 #22).
#include "ArugalLogic.h"
#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace Arugal;

namespace
{
    // The reference rows (normal level 20, heroic level 60; mod-boss-mechanics MapLevels 33:20 33h:60).
    std::uint32_t constexpr kRefNormal = 1300;
    std::uint32_t constexpr kRefNormalTank = 1290;
    std::uint32_t constexpr kRefHeroic = 4120;
    std::uint32_t constexpr kRefHeroicTank = 4110;

    bool InRoom(Point3 const& p)
    {
        return ArugalArena().Contains(p.XY(), p.z);
    }

    float Dist(Point3 const& a, Point3 const& b)
    {
        return DungeonKit::Distance(a.XY(), b.XY());
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(kSlice.first));
        CHECK(kSpellsReservation.Contains(kSlice.last));
        CHECK(kSlice.first <= kSlice.last);
        CHECK(ArugalArena().Contains(kArugalSpawn.XY(), kArugalSpawn.z));

        std::uint32_t const ids[] = { SPELL_ARUGAL_WORGENS_CURSE, SPELL_ARUGAL_WORGENS_CURSE_HEROIC,
            SPELL_ARUGAL_FERAL_POWER, SPELL_ARUGAL_THUNDERSHOCK_CAST, SPELL_ARUGAL_THUNDERSHOCK,
            SPELL_ARUGAL_THUNDERSHOCK_STUN, SPELL_ARUGAL_VOID_BOLT, SPELL_ARUGAL_ARUGALS_CURSE,
            SPELL_ARUGAL_SHADOW_PORT, SPELL_ARUGAL_TURNED, SPELL_ARUGAL_TURNED_BURST, SPELL_ARUGAL_WARD_CAST_ASHCROMBE,
            SPELL_ARUGAL_WARD_CAST_ADAMANT, SPELL_ARUGAL_WARD_RUNE, SPELL_ARUGAL_WARD_SMOKE, SPELL_ARUGAL_WARD_PULSE,
            SPELL_ARUGAL_MOONRISE_CAST, SPELL_ARUGAL_MOONRISE, SPELL_ARUGAL_MOONLIGHT, SPELL_ARUGAL_CURSE_GLOW,
            SPELL_ARUGAL_CURSE_TINT };
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : ids)
        {
            CHECK(kSlice.Contains(id));
            CHECK(!kSpellsFaceHimAlone.Contains(id));      // S10's last five ids
            CHECK(seen.insert(id).second);
        }
        CHECK(CurseSpell(false) == SPELL_ARUGAL_WORGENS_CURSE);
        CHECK(CurseSpell(true) == SPELL_ARUGAL_WORGENS_CURSE_HEROIC);
    }

    // Handoff section 10: he keeps his ledge; every port spot is reachable (two stock spots, his spawn); 7587 is out.
    void TestSpots()
    {
        CHECK(kSpots[SPOT_SPAWN].pos.x == kArugalSpawn.x && kSpots[SPOT_SPAWN].pos.y == kArugalSpawn.y);
        CHECK(kSpots[SPOT_7586].pos.x == kShadowPortSpots[1].x && kSpots[SPOT_7586].stockSpell == 7586);
        CHECK(kSpots[SPOT_7136].pos.x == kShadowPortSpots[0].x && kSpots[SPOT_7136].stockSpell == 7136);
        for (Spot const& s : kSpots)
        {
            CHECK(InRoom(s.pos));
            CHECK(s.stockSpell != 7587);
            CHECK(s.pos.z > 153.5f);                        // all on the ledge level (the lower floor is z 145)
            CHECK(Dist(s.pos, kShadowPortSpots[2]) > 30.f); // nowhere near the unreachable 7587
            CHECK(NearestSpot(s.pos.XY()) == static_cast<SpotId>(&s - kSpots.data()));
            CHECK(InRoom(s.landing));
            CHECK(std::fabs(s.landing.z - s.pos.z) <= 1.6f);
            CHECK(Dist(s.landing, s.pos) >= kThundershockRadius && Dist(s.landing, s.pos) <= 13.f);
        }
        // The stock spacing: 8.3 yd on the platform, 21 to 29 yd to the antechamber.
        CHECK(Dist(kSpots[SPOT_SPAWN].pos, kSpots[SPOT_7586].pos) > 8.f);
        CHECK(Dist(kSpots[SPOT_SPAWN].pos, kSpots[SPOT_7136].pos) > 28.f);
        CHECK(Dist(kSpots[SPOT_7586].pos, kSpots[SPOT_7136].pos) > 20.f);
    }

    // The wards are placed for the level he is on (handoff section 10): same level, outside his Thundershock ring's
    // centre, inside the room.
    void TestWardPoints()
    {
        for (Spot const& s : kSpots)
        {
            CHECK(s.wardCount >= 1 && s.wardCount <= kMaxWardPoints);
            CHECK(s.moonWardCount >= 1 && s.moonWardCount <= kMaxWardPoints);
            for (std::size_t i = 0; i < s.wardCount; ++i)
            {
                Point3 const& w = s.wards[i];
                CHECK(InRoom(w));
                CHECK(std::fabs(w.z - s.pos.z) <= 1.6f);    // the registry's z band and the bots' probe (5 yd) agree
                CHECK(Dist(w, s.pos) >= 9.5f);              // the 5 yd ward overlaps his 8 yd ring by 3.5 yd at most
                CHECK(Dist(w, s.pos) <= 25.f);
                CHECK(Dist(w, kPrisonerPost) <= 30.f);      // within the prisoner's reach (Adamant's vial)
            }
            for (std::size_t i = 0; i < s.moonWardCount; ++i)
            {
                Point3 const& w = s.moonWards[i];
                CHECK(InRoom(w));
                CHECK(std::fabs(w.z - s.pos.z) <= 1.6f);
                CHECK(Dist(w, s.pos) >= 5.9f && Dist(w, s.pos) <= 12.f);
                CHECK(Dist(w, kPrisonerPost) <= 30.f);
            }
            for (std::uint32_t r = 0; r < 6; ++r)
            {
                auto fixed = [r](std::uint32_t n) { return r % n; };
                Point3 const full = PickWardPoint(static_cast<SpotId>(&s - kSpots.data()), WardKind::Normal, fixed);
                Point3 const small = PickWardPoint(static_cast<SpotId>(&s - kSpots.data()), WardKind::Moon, fixed);
                CHECK(full.x != 0.f && small.x != 0.f);     // never an unused (zero) slot
            }
            // Beside the group: the nearest full-ward point.
            SpotId const id = static_cast<SpotId>(&s - kSpots.data());
            CHECK(Dist(WardPointNearest(id, s.wards[s.wardCount - 1].XY()), s.wards[s.wardCount - 1]) < 0.01f);
        }
        // The prisoner's way in: the gap's edge and the gallery post are on the ledge level, a jump apart.
        CHECK(InRoom(kPrisonerJumpOff) && InRoom(kPrisonerPost));
        CHECK(kPrisonerJumpOff.z > 153.5f && kPrisonerPost.z > 153.5f);
        CHECK(Dist(kPrisonerJumpOff, kPrisonerPost) < 10.f);
        CHECK(Dist(kLairPrisonerWait, kPrisonerJumpOff) < 20.f);
    }

    void TestWardRules()
    {
        WardRule const normal = RuleFor(WardKind::Normal);
        CHECK(normal.radius == 5.f && normal.minStacks == 20 && normal.maxStacks == 99 && !normal.soak);
        WardRule const full = RuleFor(WardKind::FullMoon);
        CHECK(full.radius == 5.f && full.minStacks == 0 && full.maxStacks == 99 && !full.soak);
        WardRule const moon = RuleFor(WardKind::Moon);
        CHECK(moon.radius == 3.f && moon.soak && moon.bodies == 2 && moon.maxStacks == 99);
        // A turned player (100 stacks) is never eligible (F1 open item 2).
        CHECK(kTurnAt > normal.maxStacks && kTurnAt > moon.maxStacks);
        CHECK(InsideWard(4.9f, 1.f, 5.f));
        CHECK(!InsideWard(5.1f, 0.f, 5.f));
        CHECK(!InsideWard(1.f, 10.4f, 5.f));                // the lower floor under a ledge ward
        CHECK(!InsideWard(1.f, -10.4f, 5.f));
    }

    void TestPortPick()
    {
        for (std::size_t c = 0; c < kSpotCount; ++c)
        {
            std::set<SpotId> picked;
            for (std::uint32_t r = 0; r < 8; ++r)
            {
                SpotId const next = PickPortSpot(static_cast<SpotId>(c), [r](std::uint32_t n) { return r % n; });
                CHECK(next != c);
                CHECK(next < kSpotCount);
                picked.insert(next);
            }
            CHECK(picked.size() == kSpotCount - 1);         // both other spots come up
        }
    }

    struct Cast
    {
        Step step;
        Ms start;
        Ms end;
    };

    // Plays the AI's loop on a 100 ms tick: a free boss starts the due step (flicker 1 s, Thundershock 2 s, Void Bolt
    // 3 s). Returns every cast.
    std::vector<Cast> Play(bool heroic, Ms fight)
    {
        Timeline t;
        t.Start(heroic);
        std::vector<Cast> casts;
        Ms busyUntil{ 0 };
        for (Ms now{ 0 }; now <= fight; now += Ms(100))
        {
            if (now > Ms(0))
                t.Advance(Ms(100));
            if (t.Now() < busyUntil)
                continue;
            Step const s = NextStep(t);
            Ms length{ 0 };
            switch (s)
            {
                case Step::ShadowPort:
                    t.PortDone();
                    length = kPortFlicker;
                    break;
                case Step::Thundershock:
                    t.ThundershockDone();
                    length = kThundershockCast;
                    break;
                case Step::VoidBolt:
                    length = kVoidBoltCast;
                    break;
                case Step::None:
                default:
                    continue;
            }
            casts.push_back({ s, t.Now(), t.Now() + length });
            busyUntil = t.Now() + length;
        }
        return casts;
    }

    void TestTimelineNormal()
    {
        std::vector<Cast> const casts = Play(false, Ms(90000));
        std::vector<Ms> ts, ports;
        std::uint32_t bolts = 0;
        for (std::size_t i = 0; i < casts.size(); ++i)
        {
            Cast const& c = casts[i];
            if (c.step == Step::Thundershock)
                ts.push_back(c.start);
            else if (c.step == Step::ShadowPort)
                ports.push_back(c.start);
            else
                ++bolts;
            if (i)
                CHECK(casts[i - 1].end <= c.start);         // never two casts at once
        }
        // Thundershock on the dot every 10 s from 10; Shadow Port at 5, then every 20.
        CHECK(ts.size() == 9);
        for (std::size_t i = 0; i < ts.size(); ++i)
            CHECK(ts[i] == Ms(10000 + 10000 * static_cast<std::int64_t>(i)));
        CHECK(ports.size() == 5);
        for (std::size_t i = 0; i < ports.size(); ++i)
            CHECK(ports[i] == Ms(5000 + 20000 * static_cast<std::int64_t>(i)));
        // Back to back between the other casts: about 2 per 10 s.
        CHECK(bolts >= 14 && bolts <= 22);
    }

    void TestTimelineHeroic()
    {
        std::vector<Cast> const casts = Play(true, Ms(60000));
        std::uint32_t exactCycles = 0;
        for (std::size_t i = 0; i < casts.size(); ++i)
        {
            if (i)
                CHECK(casts[i - 1].end <= casts[i].start);
            // Heroic: a Thundershock, then exactly one Void Bolt, ending when the next Thundershock is due.
            if (casts[i].step == Step::Thundershock && i + 2 < casts.size() && casts[i + 1].step == Step::VoidBolt
                && casts[i + 2].step == Step::Thundershock)
            {
                CHECK(casts[i + 1].start == casts[i].end);
                CHECK(casts[i + 1].end == casts[i + 2].start);
                ++exactCycles;
            }
        }
        CHECK(exactCycles >= 7);
        std::uint32_t shocks = 0;
        for (Cast const& c : casts)
            if (c.step == Step::Thundershock)
            {
                CHECK((c.start.count() - 7000) % 5000 == 0);  // every 5 s from 7 s, never pushed back
                ++shocks;
            }
        CHECK(shocks == 11);
    }

    void TestCurseCastTimer()
    {
        for (bool heroic : { false, true })
        {
            Timeline t;
            t.Start(heroic);
            std::vector<Ms> curses;
            for (Ms now{ 0 }; now <= Ms(80000); now += Ms(100))
            {
                if (now > Ms(0))
                    t.Advance(Ms(100));
                if (t.CurseDue())
                {
                    curses.push_back(t.Now());
                    t.CurseDone();
                }
            }
            CHECK(!curses.empty() && curses.front() == Ms(15000));
            CHECK(curses.size() >= 2 && curses[1] - curses[0] == (heroic ? Ms(20000) : Ms(25000)));
        }
    }

    void TestSeepAndMoonrise()
    {
        // Normal: about 30 stacks over a 90 s fight (SK ruling 12).
        Timeline t;
        t.Start(false);
        std::uint32_t total = 0;
        for (int i = 0; i < 900; ++i)
        {
            t.Advance(Ms(100));
            total += t.TakeSeep();
        }
        CHECK(total == 30);

        // Heroic: Moonrise stops the casts at once; after the cast the seep is +2 every second.
        Timeline h;
        h.Start(true);
        h.Advance(Ms(60000));
        CHECK(h.TakeSeep() == 20);
        h.BeginMoonrise();
        CHECK(!h.ThundershockDue() && !h.PortDue() && !h.CurseDue());
        CHECK(NextStep(h) == Step::Thundershock || NextStep(h) == Step::None);
        h.Advance(Ms(3000));
        h.MoonRisen();
        CHECK(h.Moon());
        CHECK(!h.VoidBoltFits());
        CHECK(NextStep(h) == Step::None);
        CHECK(!h.WardDue());                                // the full ward restarted the ward grid (R2 S-1)
        CHECK(h.NextWard() == Ms(80000));
        h.Advance(Ms(10000));
        CHECK(h.TakeSeep() == 20);                          // 10 s at +2 per second

        CHECK(MoonriseDue(true, false, 30.f));
        CHECK(!MoonriseDue(true, false, 30.5f));
        CHECK(!MoonriseDue(true, true, 10.f));
        CHECK(!MoonriseDue(false, false, 10.f));
    }

    void TestCurseArithmetic()
    {
        CHECK(CurseAfter(0, -10) == 0);
        CHECK(CurseAfter(95, 15) == 100);
        CHECK(CurseAfter(35, kWardCleanse) == 25);
        CHECK(CurseAfter(20, kThundershockStacks) == 35);
        CHECK(Turns(100) && !Turns(99));
        // Feral Power: heroic only, +2% per full 10, capped at +18% (90+).
        CHECK(FeralPct(false, 90) == 0);
        CHECK(FeralPct(true, 9) == 0);
        CHECK(FeralPct(true, 10) == 2);
        CHECK(FeralPct(true, 59) == 10);
        CHECK(FeralPct(true, 90) == 18);
        CHECK(FeralPct(true, 100) == 18);
        CHECK(ShowsGlow(50) && !ShowsGlow(49) && ShowsTint(80) && !ShowsTint(79));

        // SK's balance: a clean group that takes every ward drifts down (seep about 6.7 per 20 s against -10).
        CHECK(static_cast<float>(kWardEvery.count()) / static_cast<float>(kSeepEvery.count()) * kSeepStacks
            < static_cast<float>(-kWardCleanse));
        // Ruling 14: a player entering the moon at 15 turns after about 42 s; at 60, after 20 s.
        float const at15 = SecondsToTurn(15, kMoonSeepStacks, kMoonSeepEvery);
        CHECK(at15 >= 42.f && at15 <= 43.f);
        CHECK(SecondsToTurn(60, kMoonSeepStacks, kMoonSeepEvery) == 20.f);
        // Hard mode: the seep alone puts everyone at about 25 after the first 70% (74 s).
        CHECK(74000 / kSeepEvery.count() == 24);
    }

    // The hits as numbers (acceptance #8: % x reference health).
    void TestNumbers()
    {
        CHECK(DungeonKit::RefFlatValue(kRefNormal, kRefNormalTank, kThundershockPct(false), false) == 390);
        CHECK(DungeonKit::RefFlatValue(kRefHeroic, kRefHeroicTank, kThundershockPct(true), false) == 1236);
        CHECK(DungeonKit::RefFlatValue(kRefNormal, kRefNormalTank, kVoidBoltPct(false), false) == 195);
        CHECK(DungeonKit::RefFlatValue(kRefHeroic, kRefHeroicTank, kVoidBoltPct(true), false) == 1030);
        CHECK(kThundershockRadius == 8.f && kThundershockCast == Ms(2000));
        CHECK(kVoidBoltCast == Ms(3000) && kVoidBoltStacks == 3 && kCurseCastStacks == 10);
        CHECK(kPortEvery == Ms(20000) && kPortFlicker == Ms(1000));
        CHECK(kWardEvery == Ms(20000) && kWardLife == Ms(10000) && kWardDwell == Ms(3000));
    }

    void TestWardLife()
    {
        // One player stands in it: it pulses after 3 s, once.
        WardLife w;
        w.Start();
        std::vector<std::uint64_t> const one{ 7 };
        WardLife::Event e = WardLife::Event::None;
        int ticks = 0;
        while (e == WardLife::Event::None && ticks < 100)
        {
            e = w.Update(one, kWardPoll);
            ++ticks;
        }
        CHECK(e == WardLife::Event::Pulse);
        CHECK(ticks == 12);                                 // 12 x 250 ms
        CHECK(!w.Live());
        CHECK(w.Update(one, kWardPoll) == WardLife::Event::None);

        // Stepping out resets the dwell; nobody stays 3 s: it fades at 10 s.
        WardLife f;
        f.Start();
        std::vector<std::uint64_t> const none;
        WardLife::Event last = WardLife::Event::None;
        for (int i = 0; i < 40 && f.Live(); ++i)
            last = f.Update((i % 8) < 6 ? one : none, kWardPoll);  // 1.5 s in, 0.5 s out
        CHECK(last == WardLife::Event::Expired);
        CHECK(f.Age() == kWardLife);

        // Two players: the one who stayed counts, the newcomer does not delay the pulse.
        WardLife g;
        g.Start();
        for (int i = 0; i < 8; ++i)
            CHECK(g.Update(one, kWardPoll) == WardLife::Event::None);
        std::vector<std::uint64_t> const both{ 7, 9 };
        for (int i = 0; i < 3; ++i)
            CHECK(g.Update(both, kWardPoll) == WardLife::Event::None);
        CHECK(g.Update(both, kWardPoll) == WardLife::Event::Pulse);
    }

    // R2 S-1: Moonrise starting 1 s or 4 s before a grid ward (or right on it): the full ward placed as the cast starts
    // keeps its whole 10 s life (no grid ward replaces it), and the next ward is a moon Soak kWardEvery after it.
    void TestMoonriseKeepsFullWard()
    {
        for (Ms const before : { Ms(1000), Ms(4000), Ms(0) })
        {
            Timeline t;
            t.Start(true);
            Ms const gridWard = kWardFirst + 3 * kWardEvery;     // 80 s
            Ms const moonAt = gridWard - before;
            std::vector<Ms> placed;                             // UpdateWard's grid placements
            while (t.Now() < moonAt)
            {
                t.Advance(Ms(100));
                if (t.Now() < moonAt && t.WardDue())
                {
                    t.WardDone();
                    placed.push_back(t.Now());
                }
            }
            CHECK(placed.size() == 3);                          // 20, 40, 60 s
            t.BeginMoonrise();                                  // StartMoonrise places the FullMoon ward now
            bool replaced = false;
            Ms nextPlaced = Timeline::kNever;
            while (t.Now() < moonAt + kWardEvery + Ms(1000))
            {
                t.Advance(Ms(100));
                if (t.Now() == moonAt + Ms(3000))
                    t.MoonRisen();
                if (t.WardDue())
                {
                    t.WardDone();
                    if (t.Now() < moonAt + kWardLife)
                        replaced = true;
                    if (nextPlaced == Timeline::kNever)
                        nextPlaced = t.Now();
                }
            }
            CHECK(!replaced);
            CHECK(nextPlaced == moonAt + kWardEvery);
            CHECK(t.Moon());                                    // that ward is a moon Soak
        }
    }

    void TestAllTurned()
    {
        CHECK(!AllTurned(0, 0));                            // a wipe is the core's evade, not this
        CHECK(!AllTurned(5, 4));
        CHECK(AllTurned(5, 5));
        CHECK(AllTurned(1, 1));
    }
}

int main()
{
    TestSliceAndArena();
    TestSpots();
    TestWardPoints();
    TestWardRules();
    TestPortPick();
    TestTimelineNormal();
    TestTimelineHeroic();
    TestCurseCastTimer();
    TestSeepAndMoonrise();
    TestCurseArithmetic();
    TestNumbers();
    TestWardLife();
    TestMoonriseKeepsFullWard();
    TestAllTurned();
    return Report("sfk_arugal_test");
}
