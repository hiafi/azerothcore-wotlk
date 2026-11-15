// Host tests for ZigrisLogic.h (B6: Quartermaster Zigris): the slice and the arena, the crates and the order of the
// restocks, the flex counts and caps, the shells' picks and launch delay, the leap, the trap spots, the sheep's trap
// contact and the gadget clock.
#include "ZigrisLogic.h"
#include "check.h"
#include <cmath>
#include <set>

using namespace BlackrockSpireRework;
using namespace BrsZigris;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { SPELL_ZG_NET_TRAP, SPELL_ZG_NETTED, SPELL_ZG_KEG_BLAST, SPELL_ZG_KEG_STUN,
                 SPELL_ZG_FUSE, SPELL_ZG_BLAST_LOOK, SPELL_ZG_MORTAR_SHELL, SPELL_ZG_MORTAR_LOOK, SPELL_ZG_SMOKE_BOMB,
                 SPELL_ZG_LEAP, SPELL_ZG_SHEEP_BLAST, SPELL_ZG_SHEEP_WINDUP })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_ZG_NET_TRAP == 210180u);
        CHECK(SPELL_ZG_SHEEP_WINDUP == 210191u);
        // He spawns kZigrisSpawn, inside his arena.
        CHECK(ZigrisArena().Contains(kZigrisSpawn.XY(), kZigrisSpawn.z));
        CHECK(ArenaFor(BOSS_ZIGRIS).Contains(kZigrisSpawn.XY(), kZigrisSpawn.z));
        // The new units sit in the ids this WP was given.
        CHECK(NPC_BRS_CLOCKWORK_SHEEP == 300707u);
        CHECK(GO_BRS_SUPPLY_CRATE == 301252u);
        CHECK(GO_BRS_NET_TRAP == 301253u);
        CHECK(GO_BRS_POWDER_KEG == 301254u);
    }

    void TestCrates()
    {
        // The three crates stand on the ledge (inside his arena) and at least 27.9 yd apart (NM 6).
        for (std::size_t i = 0; i < kCrateCount; ++i)
        {
            Point3 const p = CrateSpot(i);
            CHECK(ZigrisArena().Contains(p.XY(), p.z));
            for (std::size_t j = i + 1; j < kCrateCount; ++j)
                CHECK(DungeonKit::Distance(p.XY(), CrateSpot(j).XY()) >= 27.8f);
        }
        // Crate 2 is the mortar's, at (-210.8, -460.8).
        CHECK(kMortarCrate == 1);
        CHECK(Near(CrateSpot(kMortarCrate).x, -210.8f) && Near(CrateSpot(kMortarCrate).y, -460.8f));
        // In turn, then round again.
        CHECK(CrateFor(0) == 0 && CrateFor(1) == 1 && CrateFor(2) == 2);
        CHECK(CrateFor(3) == 0 && CrateFor(7) == 1);
        CHECK(CrateSpot(3).x == CrateSpot(0).x);
    }

    void TestRestocks()
    {
        // Normal: the keg, the Mortar, then nothing new (and no emote at the third crate).
        CHECK(RestockFor(1, false).gadget == Gadget::PowderKeg && RestockFor(1, false).text == TEXT_KEG);
        CHECK(RestockFor(2, false).gadget == Gadget::Mortar && RestockFor(2, false).text == TEXT_MORTAR);
        CHECK(RestockFor(3, false).gadget == Gadget::None && RestockFor(3, false).text == -1);
        // Heroic: the same order, the sheep at the third crate, which names it.
        CHECK(RestockFor(1, true).gadget == Gadget::PowderKeg);
        CHECK(RestockFor(2, true).gadget == Gadget::Mortar);
        CHECK(RestockFor(3, true).gadget == Gadget::Sheep && RestockFor(3, true).text == TEXT_SHEEP);
        // Later leaps and the pull itself add nothing.
        for (std::uint32_t landing : { 0u, 4u, 5u, 9u })
            for (bool heroic : { false, true })
                CHECK(RestockFor(landing, heroic).gadget == Gadget::None && RestockFor(landing, heroic).text == -1);
        // The emote groups are the build spec's lines 2 to 4.
        CHECK(TEXT_PULL == 0 && TEXT_FALL_BACK == 1 && TEXT_KEG == 2 && TEXT_MORTAR == 3 && TEXT_SHEEP == 4
            && TEXT_DEATH == 5);
        // The creature text range covers all six.
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_ZIGRIS)
            {
                found = true;
                CHECK(r.first == 0 && r.last == TEXT_DEATH && r.firstNew == 0);
            }
        CHECK(found);
    }

    void TestFlexCounts()
    {
        // Traps: 2 at 5 players, 4 at 6 or more (the doubling of ruling 8); the held count 0 reads as 5.
        CHECK(kTossTargets.At(0) == 2 && kTossTargets.At(5) == 2);
        CHECK(kTossTargets.At(6) == 4 && kTossTargets.At(10) == 4);
        // Caps: normal 8 / 12, heroic 10 / 14.
        CHECK(TrapCap(false, 5) == 8 && TrapCap(false, 6) == 12 && TrapCap(false, 10) == 12);
        CHECK(TrapCap(true, 5) == 10 && TrapCap(true, 6) == 14 && TrapCap(true, 10) == 14);
        // Shells: 3 at 5, 6 at 6 or more; sheep: 1, then 2.
        CHECK(kShells.At(5) == 3 && kShells.At(6) == 6 && kShells.At(10) == 6);
        CHECK(kSheepCount.At(5) == 1 && kSheepCount.At(6) == 2 && kSheepCount.At(10) == 2);
        // Damage: traps 20 / 25, keg 30 / 40, Mortar 25 / 30, sheep 35 (the build spec's Damage column).
        CHECK(Near(kTrapPct(false), 20.f) && Near(kTrapPct(true), 25.f));
        CHECK(Near(kKegPct(false), 30.f) && Near(kKegPct(true), 40.f));
        CHECK(Near(kMortarPct(false), 25.f) && Near(kMortarPct(true), 30.f));
        CHECK(Near(kSheepBlastPct, 35.f));
    }

    void TestCadences()
    {
        // Traps at 8 s then every 15 s; Fall Back 20 / 20 (heroic 15 / 15).
        CHECK(kTrapsFirstMs == 8000 && kTrapsEveryMs == 15000);
        CHECK(kFallBackFirstMs(false) == 20000 && kFallBackEveryMs(false) == 20000);
        CHECK(kFallBackFirstMs(true) == 15000 && kFallBackEveryMs(true) == 15000);
        // Keg 4 s after the first restock, then 20 s; Mortar 3 s after the second, then 7 s; sheep 3 s after the third,
        // then 20 s.
        CHECK(kKegFirstAfterMs == 4000 && kKegEveryMs == 20000);
        CHECK(kMortarFirstAfterMs == 3000 && kMortarEveryMs == 7000);
        CHECK(kSheepFirstAfterMs == 3000 && kSheepEveryMs == 20000);
        // Heroic kit builds at 15, 30 and 45 s of Fall Backs (SP "Heroic").
        CHECK(kFallBackFirstMs(true) + 2 * kFallBackEveryMs(true) == 45000);
        // The shells: 1 s apart, 2 s flight, 5 yd; the keg 10 yd after a 4 s fuse; the sheep 8 yd.
        CHECK(kShellGapMs == 1000 && kShellFlightMs == 2000 && Near(kShellRadius, 5.f));
        CHECK(Near(kKegRadius, 10.f) && kKegFuseMs == 4000);
        CHECK(Near(kSheepBlastRadius, 8.f) && Near(kSheepSpeed, 5.f) && kSheepLifeMs == 10000);
        // The trap: 3 yd, armed after 1 s, grace 0.5 s, 60 s.
        CHECK(Near(kTrapRadius, 3.f) && kTrapArmMs == 1000 && kTrapGraceMs == 500 && kTrapLifeMs == 60000);
    }

    void TestGadgetClock()
    {
        GadgetClock c;
        CHECK(!c.On() && !c.Due(1000000));
        c.Start(1000, 4000);
        CHECK(c.On() && !c.Due(4999) && c.Due(5000));
        c.Fired(5000, 20000);
        CHECK(c.DueMs() == 25000 && !c.Due(24999) && c.Due(25000));
        // A late firing keeps the beat (start to start), never a burst.
        c.Fired(25200, 20000);
        CHECK(c.DueMs() == 45000);
        // A beat that fell far behind does not fire in a row.
        c.Fired(100000, 20000);
        CHECK(c.DueMs() == 120000);
        c.Stop();
        CHECK(!c.Due(1000000));
        c.Start(0, 3000);
        CHECK(c.Due(3000));
    }

    void TestShells()
    {
        // A different player each while there are enough, then round again.
        std::set<std::uint32_t> three;
        for (std::uint32_t s = 0; s < 3; ++s)
            three.insert(ShellTarget(s, 3));
        CHECK(three.size() == 3);
        // 6 shells over the 5 non-tanks of a 6-player group: every one is hit, one twice.
        std::uint32_t hits[5] = {};
        for (std::uint32_t s = 0; s < 6; ++s)
            ++hits[ShellTarget(s, 5)];
        std::uint32_t total = 0;
        for (std::uint32_t h : hits)
        {
            CHECK(h >= 1 && h <= 2);
            total += h;
        }
        CHECK(total == 6);
        CHECK(ShellTarget(4, 0) == 0);
        // The missile leaves so that it lands as the circle resolves: nothing waits for a 44 yd throw, an 11 yd throw
        // (0.5 s of flight at 22 yd/s) waits 1.5 s, a point blank one waits the whole 2 s.
        CHECK(ShellLaunchDelayMs(44.f) == 0);
        CHECK(ShellLaunchDelayMs(60.f) == 0);
        CHECK(ShellLaunchDelayMs(11.f) == 1500);
        CHECK(ShellLaunchDelayMs(0.f) == 2000);
        CHECK(ShellLaunchDelayMs(-3.f) == 2000);
        // The farthest spot of the ledge from the mortar flies for less than the circle's 2 s (the look can keep up).
        Point3 const mortar = CrateSpot(kMortarCrate);
        float far = 0.f;
        for (Vec2 corner : { Vec2{ -213.2f, -490.8f }, Vec2{ -184.8f, -490.8f }, Vec2{ -182.2f, -490.2f },
                 Vec2{ -182.2f, -445.8f }, Vec2{ -213.2f, -445.8f } })
            far = std::max(far, DungeonKit::Distance(mortar.XY(), corner));
        CHECK(far / kShellMissileSpeed * 1000.f <= static_cast<float>(kShellFlightMs) + 1.f);
    }

    void TestLeapAndTraps()
    {
        // The leap from his spawn to crate 1 (18 yd) takes under a second and a half.
        float const d = DungeonKit::Distance(kZigrisSpawn.XY(), CrateSpot(0).XY());
        CHECK(LeapMs(d) > kLeapPadMs && LeapMs(d) < 1500);
        CHECK(LeapMs(-1.f) == kLeapPadMs);
        // The longest leap of the ledge (crate 1 to crate 3, about 41 yd) is over in about 2.1 s.
        float const longest = DungeonKit::Distance(CrateSpot(0).XY(), CrateSpot(2).XY());
        CHECK(LeapMs(longest) < 2200);

        // The two traps of a Fall Back sit 2 yd either side of where he stood, across the leap.
        Vec2 const at{ -190.f, -475.f };
        std::array<Vec2, 2> const spots = FallBackTrapSpots(at, 0.f);
        CHECK(Near(DungeonKit::Distance(spots[0], at), kFallBackTrapOffsetYd));
        CHECK(Near(DungeonKit::Distance(spots[1], at), kFallBackTrapOffsetYd));
        CHECK(Near(DungeonKit::Distance(spots[0], spots[1]), 2.f * kFallBackTrapOffsetYd));
        // Across the leap: facing along +x puts them on the y axis.
        CHECK(Near(spots[0].x, at.x, 0.05f) && Near(spots[1].x, at.x, 0.05f));
        CHECK(kFallBackTraps == 2);
        // Two traps 4 yd apart do not overlap their 3 yd hitboxes more than a trap's own width.
        CHECK(DungeonKit::Distance(spots[0], spots[1]) > kTrapRadius);
    }

    void TestSheepTouch()
    {
        Vec2 const trap{ -200.f, -470.f };
        CHECK(SheepSpringsTrap({ -200.f, -470.f }, trap));
        CHECK(SheepSpringsTrap({ -198.f, -470.f }, trap));
        CHECK(SheepSpringsTrap({ -197.1f, -470.f }, trap));
        CHECK(!SheepSpringsTrap({ -196.5f, -470.f }, trap));
        // The chase is 5 yd/s: it covers the trap's 6 yd diameter in 1.2 s, so a 250 ms poll never skips one.
        CHECK(kSheepSpeed * 0.25f < 2.f * kTrapRadius);
        // 3,000 health at 5 players (the template's).
        CHECK(kSheepHealth == 3000);
        // The keep-away registration outlives the sheep, so it never resolves on its own.
        CHECK(kSheepRunOutWarnMs > kSheepLifeMs);
    }

    void TestSpace()
    {
        // The space math of SP "Space math, 10 players", normal: 12 traps (28 sq yd each) + the keg (314) + the shells
        // in flight (2 to 3 marked at once, 79 each) stays inside the ledge's 1,100 to 1,300 sq yd; the NM measure is
        // 1,349.
        float const pi = DungeonKit::kPi;
        float const trapArea = pi * kTrapRadius * kTrapRadius;
        float const kegArea = pi * kKegRadius * kKegRadius;
        float const shellArea = pi * kShellRadius * kShellRadius;
        float const normal10 = TrapCap(false, 10) * trapArea + kegArea + 3.f * shellArea;
        float const heroic10 = TrapCap(true, 10) * trapArea + kegArea + 3.f * shellArea;
        CHECK(normal10 > 800.f && normal10 < 950.f);
        CHECK(heroic10 > 900.f && heroic10 < 1000.f);
        CHECK(heroic10 < 1349.f);
    }
}

int main()
{
    TestSliceAndArena();
    TestCrates();
    TestRestocks();
    TestFlexCounts();
    TestCadences();
    TestGadgetClock();
    TestShells();
    TestLeapAndTraps();
    TestSheepTouch();
    TestSpace();

    return Report("brs_zigris_test");
}
