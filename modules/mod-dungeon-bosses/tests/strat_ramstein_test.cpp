// Host tests for RamsteinLogic.h (S13: Ramstein the Gorger (10439)): the spell ids, the meat's clock and its cap, the
// spawn points, the bots' kill tiers, the bite (reach, heal, queue, stacks), the tear (the crawlers, the ring, the
// heroic crawl-back) and Trample.
#include "RamsteinLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace StratholmeRework;
using namespace StratRamstein;

namespace
{
    bool Near(float a, float b, float eps = 1e-3f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { SPELL_RG_GORGE_LOOK, SPELL_RG_GORGE_HEAL, SPELL_RG_GORGED, SPELL_RG_SEAMS_LOOK,
            SPELL_RG_EXPOSED, SPELL_RG_GUT_PUDDLE, SPELL_RG_GUT_PUDDLE_LOOK, SPELL_RG_TRAMPLE_HIT,
            SPELL_RG_TRAMPLE_LOOK, SPELL_RG_TRAMPLE_TANK, SPELL_RG_KNOCKOUT })
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 11);
        // The ids the DT file declares (apps/dbc-tools source/npcs/stratholme/ramstein_the_gorger.py).
        CHECK(SPELL_RG_GORGE_LOOK == 206685);
        CHECK(SPELL_RG_GORGE_HEAL == 206686);
        CHECK(SPELL_RG_GORGED == 206687);
        CHECK(SPELL_RG_SEAMS_LOOK == 206688);
        CHECK(SPELL_RG_EXPOSED == 206689);
        CHECK(SPELL_RG_GUT_PUDDLE == 206690);
        CHECK(SPELL_RG_GUT_PUDDLE_LOOK == 206691);
        CHECK(SPELL_RG_TRAMPLE_HIT == 206692);
        CHECK(SPELL_RG_TRAMPLE_LOOK == 206693);
        CHECK(SPELL_RG_TRAMPLE_TANK == 206694);
        CHECK(SPELL_RG_KNOCKOUT == 206695);
        CHECK(kSpellSlice.first == 206685 && kSpellSlice.last == 206704);
        // The two kit creatures sit in wave 1's creature slice, the meat is a stock id.
        CHECK(NPC_ST_HALF_DIGESTED_CORPSE == 300586);
        CHECK(NPC_ST_GUT_PUDDLE == 300587);
        CHECK(kCreaturesWave1.Contains(NPC_ST_HALF_DIGESTED_CORPSE));
        CHECK(kCreaturesWave1.Contains(NPC_ST_GUT_PUDDLE));
        CHECK(NPC_MINDLESS_UNDEAD == 11030);
        CHECK(NPC_RAMSTEIN == 10439);
    }

    void TestRoom()
    {
        // He is summoned in his pen, outside his arena (47.5 yd from its center), and walks in to his stop, inside it.
        Arena const arena = RamsteinArena();
        CHECK(arena.Contains(kRamsteinStop.XY(), kRamsteinStop.z));
        CHECK(!arena.Contains(kRamsteinSummon.XY(), kRamsteinSummon.z));
        // The meat's walk is the 91 yd straight line of the navmesh report, about 26 s at 3.5 yd/s.
        float const walk = DungeonKit::Distance(kMindlessUndeadSpawn.XY(), kRamsteinStop.XY());
        CHECK(Near(walk, kMeatPathYd, 0.5f));
        float const walkSeconds = kMeatPathYd / kMeatSpeedYdPerSec;
        CHECK(walkSeconds > 25.f && walkSeconds < 27.f);
        // The first meat reaches him at 5 s + 26 s = 31 s, after the first tear (30 s): a lean group gets one crawler.
        CHECK(static_cast<float>(kMeatCadence.first) / 1000.f + walkSeconds > static_cast<float>(kTearCadence.first)
            / 1000.f);
        // The meat spawns 19 yd short of the Slaughter Square gate, on the line to his stop.
        float const toGate = DungeonKit::Distance(kMindlessUndeadSpawn.XY(), kSlaughterSideGate.XY());
        CHECK(Near(toGate, 19.f, 0.5f));
        // The gate is found from his stop (72 yd) well within the search range.
        CHECK(DungeonKit::Distance(kRamsteinStop.XY(), kSlaughterSideGate.XY()) < kSideGateSearchYd);
        // His pen door is within the door search range of the summon point.
        CHECK(DungeonKit::Distance(kRamsteinSummon.XY(), kRamsteinDoor.XY()) < kWalkInDoorRangeYd);
        // The walk-in skip rule: the summon point itself is on the walk-in, a point 20 yd off is a GM spawn.
        CHECK(DungeonKit::Distance(kRamsteinSummon.XY(), kRamsteinSummon.XY()) <= kWalkInSkipRadiusYd);
        // Text groups: 0 the stock yell (the walk-in), 1 the bite, 2 the tear, 3 the death yell.
        CHECK(YELL_RAMSTEIN_HUNGER == 0 && EMOTE_RAMSTEIN_GORGE == 1 && EMOTE_RAMSTEIN_STITCHES == 2
            && YELL_RAMSTEIN_DEATH == 3);
    }

    void TestMeatClock()
    {
        // Normal: waves of 4 at 5, 20, 35 ... s; 33 in all (eight waves of 4 and one of 1: about 2 min 5 s).
        MeatClock normal;
        CHECK(normal.NextMs() == 5000);
        CHECK(normal.Take(0, false) == 0);
        CHECK(normal.Take(4999, false) == 0);
        CHECK(normal.Take(5000, false) == 4);
        CHECK(normal.NextMs() == 20000);
        CHECK(normal.Take(19999, false) == 0);
        std::vector<std::uint32_t> waves{ 4 };
        std::uint64_t at = 20000;
        while (waves.size() < 12)
        {
            std::uint32_t const n = normal.Take(at, false);
            waves.push_back(n);
            at += 15000;
        }
        CHECK(waves[0] == 4 && waves[7] == 4);
        CHECK(waves[8] == 1);                        // the ninth wave (125 s) is the last meat
        CHECK(waves[9] == 0 && waves[10] == 0 && waves[11] == 0);
        CHECK(normal.Summoned() == 33);
        CHECK(5000 + 8 * 15000 == 125000);

        // Heroic: 5 a wave, no cap (the soft enrage): 100 after twenty waves.
        MeatClock heroic;
        std::uint32_t total = 0;
        for (std::uint64_t t = 5000; t < 5000 + 20 * 15000ull; t += 15000)
        {
            std::uint32_t const n = heroic.Take(t, true);
            CHECK(n == 5);
            total += n;
        }
        CHECK(total == 100);
        CHECK(heroic.Summoned() == 100);

        // A late tick takes one wave per call and keeps the cadence (no wave is lost, none doubled).
        MeatClock late;
        CHECK(late.Take(50000, false) == 4);
        CHECK(late.NextMs() == 20000);
        CHECK(late.Take(50000, false) == 4);
        CHECK(late.NextMs() == 35000);
        CHECK(late.Take(50000, false) == 4);
        CHECK(late.NextMs() == 50000);
        CHECK(late.Take(50000, false) == 4);
        CHECK(late.NextMs() == 65000);
        CHECK(late.Take(50000, false) == 0);

        // Reset starts the next pull clean.
        late.Reset();
        CHECK(late.Summoned() == 0 && late.NextMs() == 5000);

        // The cap arithmetic.
        CHECK(MeatWaveSize(false, 0) == 4);
        CHECK(MeatWaveSize(false, 29) == 4);
        CHECK(MeatWaveSize(false, 30) == 3);
        CHECK(MeatWaveSize(false, 32) == 1);
        CHECK(MeatWaveSize(false, 33) == 0);
        CHECK(MeatWaveSize(false, 99) == 0);
        CHECK(MeatWaveSize(true, 0) == 5);
        CHECK(MeatWaveSize(true, 10000) == 5);
    }

    void TestWavePoints()
    {
        Vec2 const spawn = kMindlessUndeadSpawn.XY();
        for (std::uint32_t count : { 1u, 4u, 5u })
        {
            std::vector<Vec2> const points = WavePoints(spawn, count);
            CHECK(points.size() == count);
            float sum = 0.f;
            for (Vec2 const& p : points)
            {
                CHECK(Near(p.x, spawn.x));
                CHECK(std::fabs(p.y - spawn.y) <= 3.001f);      // inside the 9-10 yd passage with a wall margin
                sum += p.y - spawn.y;
            }
            CHECK(Near(sum, 0.f));                              // centered on the spawn point
        }
        std::vector<Vec2> const five = WavePoints(spawn, 5);
        CHECK(Near(five[0].y, spawn.y - 3.f) && Near(five[4].y, spawn.y + 3.f));
        CHECK(Near(five[1].y - five[0].y, kMeatSpacingYd));
        CHECK(WavePoints(spawn, 0).empty());
    }

    void TestTiers()
    {
        // The bots' kill order: the meat nearest to him first (15 / 30 / 60 yd), then the crawlers, then him.
        CHECK(MeatPriority(0.f) == 4);
        CHECK(MeatPriority(15.f) == 4);
        CHECK(MeatPriority(15.01f) == 3);
        CHECK(MeatPriority(30.f) == 3);
        CHECK(MeatPriority(30.01f) == 2);
        CHECK(MeatPriority(60.f) == 2);
        CHECK(MeatPriority(60.01f) == 0);
        CHECK(MeatPriority(91.f) == 0);
        for (float d = 0.f; d < 59.f; d += 0.5f)
            CHECK(MeatPriority(d) >= MeatPriority(d + 0.5f));   // never ranks a farther meat above a nearer one
        CHECK(kCrawlerPriority == 1);
        CHECK(kCrawlerPriority < MeatPriority(60.f));
        CHECK(kCrawlerPriority > 0);
    }

    void TestSlowedSpeed()
    {
        // Slows scale the meat's 3.5 yd/s walk; a speed-up never does; a root-like slow stops it.
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, 0), 3.5f));
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, -50), 1.75f));
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, -30), 2.45f));
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, 40), 3.5f));
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, -100), 0.f));
        CHECK(Near(SlowedSpeed(kMeatSpeedYdPerSec, -150), 0.f));
    }

    void TestGorge()
    {
        // Reach: 3 yd, but never less than his combat reach + 1.5 yd (he is big at 8 stacks).
        CHECK(Near(GorgeReach(0.f), 3.f));
        CHECK(Near(GorgeReach(1.5f), 3.f));
        CHECK(Near(GorgeReach(2.f), 3.5f));
        CHECK(Near(GorgeReach(9.f), 10.5f));
        CHECK(InGorgeReach(3.f, 0.f, 0.f));
        CHECK(!InGorgeReach(3.01f, 0.f, 0.f));
        CHECK(InGorgeReach(10.5f, 0.f, 9.f));
        CHECK(!InGorgeReach(2.f, 8.01f, 0.f));                  // another floor
        CHECK(!InGorgeReach(2.f, -8.01f, 0.f));
        CHECK(InGorgeReach(2.f, -8.f, 0.f));

        // The meal: 3% (heroic 4%) of his health; a heroic corpse half; a returning crawler none.
        CHECK(Near(BiteHealPct(false, BiteKind::Meat), 3.f));
        CHECK(Near(BiteHealPct(true, BiteKind::Meat), 4.f));
        CHECK(Near(BiteHealPct(true, BiteKind::Corpse), 2.f));
        CHECK(Near(BiteHealPct(false, BiteKind::Crawler), 0.f));
        CHECK(Near(BiteHealPct(true, BiteKind::Crawler), 0.f));
        CHECK(PctOfMax(210000, 3.f) == 6300);                   // "about 6,300" (ST 3345)
        CHECK(PctOfMax(230000, 4.f) == 9200);
        CHECK(PctOfMax(230000, 2.f) == 4600);
        CHECK(PctOfMax(210000, 0.f) == 0);
        CHECK(PctOfMax(0, 3.f) == 0);

        // A meal gives one stack, up to 8 (heroic 10); a meal at the cap still heals.
        CHECK(StacksAfterBite(0, false) == 1);
        CHECK(StacksAfterBite(7, false) == 8);
        CHECK(StacksAfterBite(8, false) == 8);
        CHECK(StacksAfterBite(8, true) == 9);
        CHECK(StacksAfterBite(9, true) == 10);
        CHECK(StacksAfterBite(10, true) == 10);

        // Cannibalize: heroic only, within 10 yd of him.
        CHECK(!CorpseEdible(false, 1.f));
        CHECK(CorpseEdible(true, 0.f));
        CHECK(CorpseEdible(true, 10.f));
        CHECK(!CorpseEdible(true, 10.01f));
        CHECK(!CorpseEdible(true, 40.f));

        // The failing-path check of ST 3344: a meal heals 6,300 and comes back as a 3,000 crawler against 4,000 to
        // kill the meat: feeding him never pays (9,300 instead of 4,000).
        CHECK(PctOfMax(210000, kGorgeHealPct(false)) + 3000 > 4000);
    }

    void TestBiteQueue()
    {
        BiteQueue bites;
        CHECK(bites.Size() == 0);
        CHECK(bites.Add(7, BiteKind::Meat, 1000));
        CHECK(!bites.Add(7, BiteKind::Corpse, 1200));           // being eaten already
        CHECK(bites.Has(7));
        CHECK(bites.Add(8, BiteKind::Crawler, 1500));
        CHECK(bites.Add(9, BiteKind::Corpse, 1100));
        CHECK(bites.Size() == 3);
        CHECK(bites.Take(2499).empty());                        // 7 lands at 2500
        std::vector<Bite> due = bites.Take(2500);
        CHECK(due.size() == 1 && due[0].id == 7 && due[0].kind == BiteKind::Meat);
        CHECK(!bites.Has(7));
        // Two at once come out oldest first, and only once.
        due = bites.Take(5000);
        CHECK(due.size() == 2 && due[0].id == 9 && due[1].id == 8);
        CHECK(bites.Take(9000).empty());
        CHECK(bites.Size() == 0);
        // Forget and Clear.
        bites.Add(1, BiteKind::Meat, 0);
        bites.Add(2, BiteKind::Meat, 0);
        bites.Forget(1);
        CHECK(!bites.Has(1) && bites.Has(2));
        bites.Clear();
        CHECK(bites.Size() == 0);
        CHECK(kBiteMs == 1500);
    }

    void TestSpill()
    {
        // 1 crawler + 1 per Gorged stack: a lean group gets one, a fat Ramstein 9 (heroic 11).
        CHECK(SpillCount(0) == 1);
        CHECK(SpillCount(4) == 5);
        CHECK(SpillCount(kGorgedMaxStacks(false)) == 9);
        CHECK(SpillCount(kGorgedMaxStacks(true)) == 11);

        // The ring: outside his body, never under 4 yd.
        CHECK(Near(SpillRadius(0.f), 4.f));
        CHECK(Near(SpillRadius(1.9f), 4.f));
        CHECK(Near(SpillRadius(5.f), 7.f));

        // Evenly spaced bearings from the start angle, all in [0, 2 pi).
        std::vector<float> const angles = SpillAngles(9, 1.f);
        CHECK(angles.size() == 9);
        for (std::size_t i = 0; i < angles.size(); ++i)
        {
            CHECK(angles[i] >= 0.f && angles[i] < DungeonKit::kTwoPi);
            float const next = angles[(i + 1) % angles.size()];
            float gap = next - angles[i];
            if (gap < 0.f)
                gap += DungeonKit::kTwoPi;
            CHECK(Near(gap, DungeonKit::kTwoPi / 9.f, 1e-3f));
        }
        CHECK(Near(angles[0], 1.f));
        CHECK(SpillAngles(1, 2.f).size() == 1);
        CHECK(SpillAngles(0, 2.f).empty());

        // Exposed: 8 s (heroic 6 s), the same however fat he was.
        CHECK(kExposedMs(false) == 8000 && kExposedMs(true) == 6000);
        // The tear: first at 30 s, every 30 s; the puddle 6 yd, 4% a second for 20 s (so it ends before the next tear).
        CHECK(kTearCadence.first == 30000 && kTearCadence.every == 30000);
        CHECK(kPuddleRadius == 6.f && kPuddleMs == 20000 && kPuddleTickMs == 1000 && kPuddlePct == 4.f);
        CHECK(kPuddleMs < kTearCadence.every);
        CHECK(kSpillNearPlayerYd == 40.f);
    }

    void TestCrawlerBook()
    {
        // Heroic: a crawler alive 15 s after the tear walks back, once.
        CrawlerBook book;
        book.Add(1, 30000);
        book.Add(2, 30000);
        book.Add(3, 60000);
        CHECK(book.Size() == 3 && book.Tracks(2));
        CHECK(book.TakeDue(44999).empty());
        std::vector<std::uint64_t> due = book.TakeDue(45000);
        CHECK(due.size() == 2 && due[0] == 1 && due[1] == 2);
        CHECK(book.TakeDue(46000).empty());                     // an id comes out once
        book.Forget(2);                                         // killed on the way back
        CHECK(!book.Tracks(2) && book.Size() == 2);
        due = book.TakeDue(75000);
        CHECK(due.size() == 1 && due[0] == 3);
        book.Clear();
        CHECK(book.Size() == 0);
        // The next tear (30 s on) spills while the last one's survivors are still walking: 15 s < 30 s.
        CHECK(kCrawlerReturnAfterMs < kTearCadence.every);
        CHECK(kCrawlerReturnAfterMs == 15000);
    }

    void TestTrample()
    {
        // 10 yd + 1 yd per stack; 25% (heroic 30%) + 3% per stack (ST 3336-3338, 3349).
        CHECK(Near(TrampleRadius(0), 10.f));
        CHECK(Near(TrampleRadius(8), 18.f));
        CHECK(Near(TrampleRadius(10), 20.f));
        CHECK(Near(TramplePct(false, 0), 25.f));
        CHECK(Near(TramplePct(false, 8), 49.f));
        CHECK(Near(TramplePct(true, 0), 30.f));
        CHECK(Near(TramplePct(true, 10), 60.f));
        // "Trample at 8 stacks is 18 yd (about 1,000 sq yd), which empties melee range."
        float const area = DungeonKit::kPi * TrampleRadius(8) * TrampleRadius(8);
        CHECK(area > 1000.f && area < 1030.f);
        // The cadence: first at 8 s, every 12 s, a 1.5 s warning.
        CHECK(kTrampleCadence.first == 8000 && kTrampleCadence.every == 12000 && kTrampleWarnMs == 1500);
        CHECK(kTrampleWarnMs < kTrampleCadence.every);
        // Knockout: the stock timers.
        CHECK(InRange(kKnockoutFirst, 0.f) == 4000 && InRange(kKnockoutFirst, 1.f) == 9000);
        CHECK(InRange(kKnockoutEvery, 0.f) == 10000 && InRange(kKnockoutEvery, 1.f) == 15000);
        CHECK(InRange(kKnockoutEvery, 0.5f) == 12500);
        CHECK(InRange(kKnockoutEvery, -3.f) == 10000);
    }

    void TestWalkIn()
    {
        CHECK(kWalkInYellMs == 1000);
        CHECK(kWalkInYellMs < kWalkInTimeoutMs);
        CHECK(kWalkInAggroRangeYd == 70.f);
        // The summon point is 21.6 yd from his stop (the stock walk).
        CHECK(Near(DungeonKit::Distance(kRamsteinSummon.XY(), kRamsteinStop.XY()), 21.6f, 0.3f));
        CHECK(POINT_RG_WALK_IN != POINT_RG_WALKER);
        CHECK(ACTION_RG_RETURN == 1);
    }
}

int main()
{
    TestSlice();
    TestRoom();
    TestMeatClock();
    TestWavePoints();
    TestTiers();
    TestSlowedSpeed();
    TestGorge();
    TestBiteQueue();
    TestSpill();
    TestCrawlerBook();
    TestTrample();
    TestWalkIn();

    return Report("strat_ramstein_test");
}
