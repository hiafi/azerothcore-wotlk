// Host tests for BeastLogic.h (B13: The Beast): the slice, the text range and the stock wake constants, the Heat clock
// and its retiming of the roar and Magma Split, the cast queue over a whole fight (one cast at a time), the pools (how
// many, how big, where, which look), the space math of the build spec, Molten Fury's clock, Dread's threshold, the
// 5 yd throw, the Eruption, the flex counts and the bots' crowd rule.
#include "BeastLogic.h"
#include "check.h"
#include <cmath>
#include <numbers>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsBeast;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndTexts()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { SPELL_BE_HEAT, SPELL_BE_MOLTEN_FURY, SPELL_BE_ROAR, SPELL_BE_DREAD, SPELL_BE_PANIC,
                 SPELL_BE_MAGMA_SPLIT_BAR, SPELL_BE_MAGMA_SPLIT, SPELL_BE_MAGMA_SPLIT_TARGET, SPELL_BE_MOLTEN_BLOOD,
                 SPELL_BE_ERUPTION, SPELL_BE_IMMOLATE, SPELL_BE_HEAT_FLASH, SPELL_BE_POOL_LOOK_4,
                 SPELL_BE_POOL_LOOK_10 })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_BE_HEAT == 210490u);
        CHECK(SPELL_BE_IMMOLATE == 210500u);
        CHECK(SPELL_BE_POOL_LOOK_4 == 210502u);
        CHECK(SPELL_BE_POOL_LOOK_10 == 210508u);
        // The pool trigger sits in the ids this WP was given, in wave 2's slice.
        CHECK(NPC_BRS_MOLTEN_BLOOD == 300735u);
        CHECK(kCreaturesWave2.Contains(NPC_BRS_MOLTEN_BLOOD));
        // He spawns kBeastSpawn, inside his arena; the two area triggers' centers too.
        CHECK(BeastArena().Contains(kBeastSpawn.XY(), kBeastSpawn.z));
        CHECK(ArenaFor(BOSS_BEAST).Contains(kBeastSpawn.XY(), kBeastSpawn.z));
        CHECK(BeastArena().Contains(kBeastTrigger2066.XY(), kBeastTrigger2066.z));
        CHECK(BeastArena().Contains(kBeastTrigger2067.XY(), kBeastTrigger2067.z));
        CHECK(NPC_BEAST == 10430u && BOSS_BEAST == 12u);
        // The creature text range is the build spec's three boss emotes, all new.
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_BEAST)
            {
                found = true;
                CHECK(r.first == 0 && r.last == 2 && r.firstNew == 0);
            }
        CHECK(found);
        CHECK(TEXT_ROAR == 0 && TEXT_HEAT == 1 && TEXT_ERUPTION == 2);
        // The stock wake protocol: the numbers the area triggers and the stock script share.
        CHECK(DATA_BEAST_REACHED == 1u && DATA_BEAST_ROOM == 2u && BEAST_MOVEMENT_ID == 1379690u);
        CHECK(NPC_BLACKHAND_ELITE == 10317u && SAY_BLACKHAND_DOOMED == 0);
        CHECK(Near(kEvadeLineY, -505.f));
        CHECK(kElitesMoveMs == 3000u && kElitesDieMs == 9000u);
        // No tank swap on the Beast (ruling 63's list does not hold him); the flex counts: 2 at 5, 4 at 6 or more.
        CHECK(kSplitTargets.At(5) == 2 && kSplitTargets.At(6) == 4 && kSplitTargets.At(10) == 4);
        CHECK(kSplitTargets.At(0) == 2);    // a count not held reads as 5
    }

    void TestHeatClock()
    {
        // A stack at 20 s (heroic 15 s) and then each period, no cap.
        CHECK(kHeatEveryMs(false) == 20000u && kHeatEveryMs(true) == 15000u);
        CHECK(HeatAt(false, 19999) == 0 && HeatAt(false, 20000) == 1 && HeatAt(false, 120000) == 6);
        CHECK(HeatAt(true, 14999) == 0 && HeatAt(true, 15000) == 1 && HeatAt(true, 100000) == 6);
        // 3 stacks: the roar every 15 s; 5 stacks: Magma Split every 15 s.
        CHECK(RoarEveryMs(0) == 20000u && RoarEveryMs(2) == 20000u && RoarEveryMs(3) == 15000u
            && RoarEveryMs(9) == 15000u);
        CHECK(SplitEveryMs(0) == 20000u && SplitEveryMs(4) == 20000u && SplitEveryMs(5) == 15000u
            && SplitEveryMs(9) == 15000u);
        // Damage: +10% a stack of Heat or Molten Fury.
        CHECK(Near(DamageMult(0, 0), 1.f) && Near(DamageMult(3, 0), 1.3f) && Near(DamageMult(3, 2), 1.5f));
        // Retiming: a beat that has fired moves up to last + the new cadence (never into the past, never later).
        CHECK(RetimeDue(70000, 50000, 15000, 60000) == 65000);
        CHECK(RetimeDue(70000, 50000, 15000, 68000) == 68000);      // already past the new time: now
        CHECK(RetimeDue(60000, 50000, 15000, 55000) == 60000);      // already earlier: unchanged
    }

    struct Cast
    {
        std::uint32_t id = 0;
        std::uint64_t at = 0;
    };

    // The AI's loop without the engine: the heat clock, the queue, the 100 ms tick. `blast` is the filler's roll.
    std::vector<Cast> SimulateFight(bool heroic, std::uint64_t untilMs, std::uint32_t blast = 6500)
    {
        std::vector<Cast> out;
        Beats beats;
        beats.Start(0, blast);
        std::uint32_t heat = 0;
        std::uint64_t nextHeat = kHeatEveryMs(heroic);
        for (std::uint64_t now = 0; now <= untilMs; now += 100)
        {
            while (now >= nextHeat)
            {
                nextHeat += kHeatEveryMs(heroic);
                ++heat;
                beats.OnHeat(heat, now);
            }
            beats.DropStale(now, blast);
            if (std::optional<std::uint32_t> const next = beats.Next(now))
            {
                out.push_back({ *next, now });
                beats.Started(*next, now, heat, blast);
            }
        }
        return out;
    }

    std::vector<std::uint64_t> TimesOf(std::vector<Cast> const& casts, std::uint32_t id)
    {
        std::vector<std::uint64_t> t;
        for (Cast const& c : casts)
            if (c.id == id)
                t.push_back(c.at);
        return t;
    }

    void TestBeatsNormal()
    {
        std::vector<Cast> const fight = SimulateFight(false, 150000);
        // First casts: Immolate at 3 s, the roar at 10 s, Magma Split at 20 s (the build spec's firsts).
        std::vector<std::uint64_t> const roars = TimesOf(fight, CAST_ROAR);
        std::vector<std::uint64_t> const splits = TimesOf(fight, CAST_SPLIT);
        std::vector<std::uint64_t> const immolates = TimesOf(fight, CAST_IMMOLATE);
        CHECK(!immolates.empty() && immolates[0] == kImmolateFirstMs);
        CHECK(roars.size() >= 5 && roars[0] == kRoarFirstMs);
        CHECK(splits.size() >= 4 && splits[0] == kSplitFirstMs);
        // The roar: 10, 30, 50, then Heat 3 (at 60 s) shortens it to 15 s from the last roar: 65.
        CHECK(roars[1] == 30000 && roars[2] == 50000);
        CHECK(roars[3] == 65000);
        // Magma Split: 20, 40, 60, then every 20 s until Heat 5 (100 s).
        CHECK(splits[1] == 40000 && splits[2] == 60000);
        // The two cadences meet at 80 s: the roar goes first and the split waits 5 s after it, and the pair settles
        // into an alternation (the split 5 s after each roar from then on).
        CHECK(roars[4] == 80000 && splits[3] == 85000);
        // The cast bars never overlap each other or any other cast: a roar or a split holds him 2 s plus the spacing.
        std::uint64_t barFree = 0;
        for (Cast const& c : fight)
        {
            CHECK(c.at >= barFree);
            if (c.id == CAST_ROAR || c.id == CAST_SPLIT)
                barFree = c.at + kRoarCastMs + kCastSpacingMs;
        }
        // Immolate every 8 s unless a bar holds it (then at the bar's end).
        for (std::size_t i = 1; i < immolates.size(); ++i)
            CHECK(immolates[i] - immolates[i - 1] >= kImmolateEveryMs);
        // The filler: a Fire Blast at the roll, then each roll on, never earlier than the roll.
        std::vector<std::uint64_t> const blasts = TimesOf(fight, CAST_FIRE_BLAST);
        CHECK(blasts.size() > 10);
        CHECK(blasts[0] == 6500);
        for (std::size_t i = 1; i < blasts.size(); ++i)
            CHECK(blasts[i] - blasts[i - 1] >= 6500);
        // The first thing he casts is the Immolate at 3 s.
        CHECK(fight.front().at == kImmolateFirstMs);
    }

    void TestBeatsHeroic()
    {
        std::vector<Cast> const fight = SimulateFight(true, 130000);
        std::vector<std::uint64_t> const roars = TimesOf(fight, CAST_ROAR);
        std::vector<std::uint64_t> const splits = TimesOf(fight, CAST_SPLIT);
        // Heat every 15 s: stack 3 at 45 s, so the roar after the one at 30 s (50 s) comes at 45 s: 10, 30, 45.
        CHECK(roars[0] == 10000 && roars[1] == 30000);
        CHECK(roars[2] == 45000);
        // The roar (60 s) and the split (60 s) meet: the roar goes first, the split 5 s after it. Heat 5 at 75 s then
        // brings the split to 80 s (65 + 15), 5 s after the roar at 75 s, and every 15 s on.
        CHECK(roars[3] == 60000);
        CHECK(splits[0] == 20000 && splits[1] == 40000 && splits[2] == 65000);
        CHECK(splits[3] == 80000);
        std::uint64_t barFree = 0;
        for (Cast const& c : fight)
        {
            CHECK(c.at >= barFree);
            if (c.id == CAST_ROAR || c.id == CAST_SPLIT)
                barFree = c.at + kRoarCastMs + kCastSpacingMs;
        }
        // From 75 s on, a roar and a split are never closer than 5 s.
        std::uint64_t lastBar = 0;
        std::uint32_t lastKind = 0;
        for (Cast const& c : fight)
        {
            if (c.id != CAST_ROAR && c.id != CAST_SPLIT)
                continue;
            if (lastKind && c.id != lastKind)
                CHECK(c.at - lastBar >= kBarGapMs);
            lastBar = c.at;
            lastKind = c.id;
        }
    }

    void TestDropStale()
    {
        // A filler that waited 3 s past its turn (a bar held it) is dropped and rolled again, never fired late in a
        // burst: Fire Blast due at 6.5 s, the caster held by a roar started at 5 s (busy until 7 s + spacing).
        Beats beats;
        beats.Start(0, 6500);
        beats.Started(CAST_ROAR, 5000, 0, 6500);
        CHECK(!beats.Next(6600).has_value());
        std::vector<std::uint32_t> const dropped = beats.DropStale(9600, 7000);
        CHECK(dropped.size() == 1 && dropped[0] == CAST_FIRE_BLAST);
        CHECK(beats.DueAt(CAST_FIRE_BLAST).value() == 16600);
    }

    void TestPools()
    {
        // One for every 4% lost, at most 25.
        CHECK(PoolsOwed(100.f, 0) == 0 && PoolsOwed(97.f, 0) == 0);
        CHECK(PoolsOwed(96.f, 0) == 1 && PoolsOwed(95.f, 0) == 1 && PoolsOwed(92.f, 0) == 2);
        CHECK(PoolsOwed(50.f, 0) == 12 && PoolsOwed(50.f, 12) == 0 && PoolsOwed(50.f, 10) == 2);
        CHECK(PoolsOwed(4.f, 0) == 24 && PoolsOwed(0.f, 0) == 25 && PoolsOwed(0.f, 25) == 0);
        CHECK(PoolsOwed(96.f, 5) == 0);     // healed back up: never negative
        // Radius: 5 yd (heroic 4.5) + half a yard a stack, no cap; its near edge stands 5 yd from him.
        CHECK(Near(PoolRadius(false, 0), 5.f) && Near(PoolRadius(true, 0), 4.5f));
        CHECK(Near(PoolRadius(false, 4), 7.f) && Near(PoolRadius(true, 6), 7.5f) && Near(PoolRadius(false, 20), 15.f));
        CHECK(Near(PoolRingYd(5.f), 10.f) && Near(PoolRingYd(7.5f), 12.5f));
        CHECK(Near(kSplitPoolRadiusYd, 4.f) && Near(kImmolatePoolRadiusYd, 4.f));
        // V-2's rungs: the smallest 1 yd rung at or above the radius, 4 at the bottom, 10 at the top.
        CHECK(PoolRung(4.f) == 4 && PoolRung(4.5f) == 5 && PoolRung(5.f) == 5 && PoolRung(5.5f) == 6);
        CHECK(PoolRung(6.5f) == 7 && PoolRung(9.5f) == 10 && PoolRung(10.f) == 10 && PoolRung(15.f) == 10);
        CHECK(PoolRung(3.f) == 4);
        CHECK(PoolLookSpell(4.f) == SPELL_BE_POOL_LOOK_4 && PoolLookSpell(7.f) == SPELL_BE_POOL_LOOK_4 + 3);
        CHECK(PoolLookSpell(12.f) == SPELL_BE_POOL_LOOK_10);
        for (float r = 3.f; r < 16.f; r += 0.25f)
            CHECK(kSpellSlice.Contains(PoolLookSpell(r)));
    }

    void TestPoolFloor()
    {
        // The hall: the rectangle x 17..83, y -561..-513 (a disc must lie wholly inside it).
        CHECK(PoolFits({ 50.f, -537.f }, 5.f));
        CHECK(PoolFits({ 22.f, -537.f }, 5.f));         // x - r = 17: on the edge
        CHECK(!PoolFits({ 21.f, -537.f }, 5.f));        // x - r = 16: into the wall
        CHECK(!PoolFits({ 50.f, -517.f }, 5.f));        // y + r = -512 past the hall's north edge
        CHECK(PoolFits({ 50.f, -518.f }, 5.f));
        CHECK(!PoolFits({ 50.f, -557.f }, 5.f));
        CHECK(PoolFits({ 78.f, -549.f }, 5.f));         // where the wake ends (78.8, -549.1)
        // The pit: a disc of radius 18 about (117.2, -561.2), wholly inside.
        CHECK(PoolFits({ 117.2f, -561.2f }, 6.f));
        CHECK(PoolFits({ 124.21f, -563.8f }, 5.f));     // at his spawn
        CHECK(PoolFits({ 117.2f, -561.2f }, 18.f));
        CHECK(!PoolFits({ 117.2f, -561.2f }, 18.5f));
        CHECK(!PoolFits({ 130.f, -561.f }, 6.f));
        // Neither the ramp's gap between the hall and the pit nor the corridors: no pool there.
        CHECK(!PoolFits({ 86.f, -550.f }, 5.f));
        CHECK(!PoolFits({ 50.f, -500.f }, 5.f));
        // The pool arena (the engine's candidate region) agrees with the rule on the floor height of each.
        Arena const arena = PoolArena(5.f);
        CHECK(arena.Contains({ 50.f, -537.f }, 111.2f));
        CHECK(!arena.Contains({ 20.f, -537.f }, 111.2f));
        CHECK(arena.Contains({ 117.2f, -561.2f }, 107.5f));
        CHECK(!arena.Contains({ 117.2f, -561.2f }, 120.f));
        CHECK(!arena.Contains({ 135.f, -561.2f }, 107.5f));
        // A huge pool has no floor at all (never a crash): the arena is empty.
        CHECK(PoolArena(40.f).Empty());
        // His spawn is floor a 5 yd pool can ring.
        CHECK(arena.Contains(kBeastSpawn.XY(), kBeastSpawn.z));
    }

    // The union of lava the build spec's space math counts: the sum of the pool discs (they avoid each other while the
    // floor lasts), pools laid at each 4% of a linear kill, the heroic Magma Split pools (4 yd, 2 per split at 5
    // players) on top.
    double LavaArea(bool heroic, double killSec)
    {
        double area = 0.0;
        for (std::uint32_t k = 1; k <= kPoolMax; ++k)
        {
            double const t = killSec * (kPoolEveryLostPct * k / 100.0);
            double const r = PoolRadius(heroic, HeatAt(heroic, static_cast<std::uint64_t>(t * 1000.0)));
            area += std::numbers::pi * r * r;
        }
        if (heroic)
            for (double t = kSplitFirstMs / 1000.0; t < killSec; t += 20.0)
                area += 2.0 * std::numbers::pi * kSplitPoolRadiusYd * kSplitPoolRadiusYd;
        return area;
    }

    void TestSpaceMath()
    {
        // SP: the room is about 4,100 sq yd, "about used up at three quarters covered". Normal: lava down at the 1:30
        // kill is about 2,790 sq yd (68%); at 2:00 it is used up (about 75%), which is the Eruption's time.
        double const n90 = LavaArea(false, 90.0);
        CHECK(n90 > 2790.0 * 0.96 && n90 < 2790.0 * 1.04);
        double const n120 = LavaArea(false, 120.0);
        CHECK(n120 > 3000.0 && n120 < 3300.0);
        CHECK(n120 / 4100.0 > 0.72 && n120 / 4100.0 < 0.80);
        // Heroic: at the 1:20 kill about 2,950 sq yd (72%) with the Magma Split pools.
        double const h80 = LavaArea(true, 80.0);
        CHECK(h80 > 2950.0 * 0.92 && h80 < 2950.0 * 1.08);
        // Heroic runs out sooner: about 1:30 (the Eruption at 1:40 is its hard stop).
        double const h90 = LavaArea(true, 90.0);
        CHECK(h90 > 3000.0);
        // Faster kills put less lava down (time adds Heat, so slower kills are bigger pools).
        CHECK(LavaArea(false, 75.0) < n90 && n90 < LavaArea(false, 100.0));
        CHECK(LavaArea(false, 60.0) < LavaArea(false, 75.0));
        // The Eruption: 2:00 normal, 1:40 heroic.
        CHECK(kEruptionAtMs(false) == 120000u && kEruptionAtMs(true) == 100000u);
        CHECK(!EruptionDue(false, 119999) && EruptionDue(false, 120000) && EruptionDue(true, 100000)
            && !EruptionDue(true, 99999));
        CHECK(Near(kEruptionPct, 10.f) && kEruptionTickMs == 1000u);
    }

    void TestFury()
    {
        // A stack for every 2 s of unbroken time in lava; leaving it resets the clock.
        FuryClock clock;
        std::uint32_t stacks = 0;
        for (int i = 0; i < 8; ++i)         // 2 s in 250 ms polls
            stacks += clock.Advance(true, kFuryPollMs);
        CHECK(stacks == 1 && clock.InsideMs() == 0);
        stacks = 0;
        for (int i = 0; i < 6; ++i)         // 1.5 s, out, 1.5 s: nothing
            stacks += clock.Advance(true, kFuryPollMs);
        stacks += clock.Advance(false, kFuryPollMs);
        for (int i = 0; i < 6; ++i)
            stacks += clock.Advance(true, kFuryPollMs);
        CHECK(stacks == 0 && clock.InsideMs() == 1500);
        // A long poll (a lagging tick) pays out every 2 s it covers.
        FuryClock lag;
        CHECK(lag.Advance(true, 5000) == 2 && lag.InsideMs() == 1000);
        CHECK(lag.Advance(true, 1000) == 1 && lag.InsideMs() == 0);
        CHECK(kFuryEveryMs == 2000u && Near(kFuryDamagePct, 10.f));
    }

    void TestDread()
    {
        // Normal panics at 3 stacks, heroic at 2 (one missed roar is a stack, two a panic).
        CHECK(!Panics(1, false) && !Panics(2, false) && Panics(3, false));
        CHECK(!Panics(1, true) && Panics(2, true) && Panics(3, true));
        CHECK(kDreadMinOthers == 2 && Near(kDreadRadiusYd, 6.f));
        CHECK(kDreadMs == 30000u && kPanicMs == 2000u);     // the 2 s limit on loss of control
        CHECK(kDreadPanicAt(false) <= kDreadMaxStacks && kDreadPanicAt(true) <= kDreadMaxStacks);
        CHECK(kRoarCastMs == 2000u && kRoarFirstMs == 10000u);
    }

    void TestSplitAndKnockback()
    {
        // The throw is 5 yd: the speeds invert Unit::KnockbackFrom's distance.
        float const speedXY = KnockbackSpeedXY(kSplitKnockYd, kSplitKnockSpeedZ);
        CHECK(Near(KnockbackDistance(speedXY, kSplitKnockSpeedZ), kSplitKnockYd, 0.001f));
        CHECK(KnockbackSpeedXY(5.f, 0.f) == 0.f);
        CHECK(Near(kSplitRadiusYd, 6.f) && Near(kSplitTargetPct, 15.f) && Near(kSplitOthersPct, 30.f));
        CHECK(kSplitCastMs == 2000u && kSplitFirstMs == 20000u);
        // The target's 15% and the others' 30% rise 10% a Heat stack and a Molten Fury stack.
        CHECK(Near(kSplitOthersPct * DamageMult(4, 1), 45.f) && Near(kSplitTargetPct * DamageMult(0, 0), 15.f));
    }

    void TestCrowd()
    {
        // The bots' tank rule: 4 pools with an edge within 8 yd of him send the tank to fresh floor.
        std::vector<PoolSpot> pools;
        Vec2 const boss{ 50.f, -537.f };
        CHECK(!ShouldPark(boss, pools));
        // Pools in the ring his own pools make (center 10 yd away, radius 5: edge 5 yd).
        for (int i = 0; i < 3; ++i)
            pools.push_back({ { 50.f + 10.f * std::cos(float(i) * 2.f), -537.f + 10.f * std::sin(float(i) * 2.f) },
                5.f });
        CHECK(CrowdCount(boss, pools) == 3 && !ShouldPark(boss, pools));
        pools.push_back({ { 50.f, -520.f }, 5.f });                 // edge 12 yd off: not crowding
        CHECK(CrowdCount(boss, pools) == 3);
        pools.push_back({ { 50.f, -548.f }, 5.f });                 // edge 6 yd off: the fourth
        CHECK(CrowdCount(boss, pools) == 4 && ShouldPark(boss, pools));
        // Far away from the lava: no park.
        CHECK(!ShouldPark({ 20.f, -520.f }, pools));
        CHECK(kParkMinYd < kParkMaxYd && kParkClearYd < kParkMaxYd);
    }

    void TestLavaDamage()
    {
        // Lava and Eruption tick 10% a second, Immolate (heroic) 3%: the DT test pins the same numbers in the spells.
        CHECK(Near(kPoolTickPct, 10.f) && kPoolTickMs == 1000u && Near(kImmolateTickPct, 3.f));
        CHECK(kImmolateMs == 21000u && kImmolateEveryMs == 8000u && kImmolateFirstMs == 3000u);
        CHECK(kPoolMarkMs == 1500u && kPoolMax == 25u && Near(kPoolNearEdgeYd, 5.f));
        // A burst of lost health lays its pools 250 ms apart, a retry waits a second.
        CHECK(kPoolStaggerMs < kPoolRetryMs);
        // Stock fillers: Fire Blast every 5 to 8 s.
        CHECK(kFireBlastMinMs == 5000u && kFireBlastMaxMs == 8000u);
    }
}

int main()
{
    TestSliceAndTexts();
    TestHeatClock();
    TestBeatsNormal();
    TestBeatsHeroic();
    TestDropStale();
    TestPools();
    TestPoolFloor();
    TestSpaceMath();
    TestFury();
    TestDread();
    TestSplitAndKnockback();
    TestCrowd();
    TestLavaDamage();
    return Report("brs_beast_test");
}
