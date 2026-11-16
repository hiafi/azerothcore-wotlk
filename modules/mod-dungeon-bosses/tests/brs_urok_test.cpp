// Host tests for UrokLogic.h (B5: Urok Doomhowl, "Stolen Magic"; SP 1630-1688).
#include "UrokLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace BlackrockSpireRework;
using namespace BrsUrok;

namespace
{
    bool Near(float a, float b)
    {
        return std::fabs(a - b) < 0.001f;
    }

    void TestSliceAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210150 && kSpellSlice.last == 210179);
        for (std::uint32_t id : { std::uint32_t(SPELL_UR_WAROSHS_POWER), std::uint32_t(SPELL_UR_STOLEN_POWER),
                 std::uint32_t(SPELL_UR_WILD_BOLT), std::uint32_t(SPELL_UR_DOOMHOWL),
                 std::uint32_t(SPELL_UR_OVERCHARGE), std::uint32_t(SPELL_UR_UNSTABLE_BURST) })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_UR_WAROSHS_POWER == 210150);
        CHECK(SPELL_UR_STOLEN_POWER == 210151);
        CHECK(SPELL_UR_UNSTABLE_BURST == 210165);
        // He is summoned at kUrokSummon, inside his arena; the pile and the circles are on the plateau too.
        CHECK(UrokArena().Contains(kUrokSummon.XY(), kUrokSummon.z));
        CHECK(ArenaFor(BOSS_UROK).Contains(kUrokSummon.XY(), kUrokSummon.z));
        CHECK(UrokArena().Contains(kUrokPile.XY(), kUrokPile.z));
        for (Point4 const& c : kCircles)
            CHECK(UrokArena().Contains(c.XY(), c.z));
        // Text groups inside the boss's range; the stock rows are 0 and 1.
        TextRange const* range = nullptr;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_UROK)
                range = &r;
        CHECK(range != nullptr);
        if (range)
        {
            CHECK(range->first <= SAY_UR_SUMMON && SAY_UR_DEATH <= range->last);
            CHECK(range->firstNew == EMOTE_UR_DOOMHOWL);
        }
        CHECK(NPC_BRS_STOLEN_MAGIC_SHARD == 300706);
    }

    void TestTuning()
    {
        CHECK(kShardWaitMs(false) == 10000 && kShardWaitMs(true) == 7000);
        CHECK(Near(kShardRadiusYd, 2.f) && Near(kShardCrawlYdPerSec, 3.f));
        CHECK(kWaroshMaxStacks == 3 && kWaroshMs == 20000);
        CHECK(kStolenPowerCap(false) == 8 && kStolenPowerCap(true) == 5);
        CHECK(kWildBoltCadence.first == 6000 && kWildBoltCadence.every == 10000);
        CHECK(kWildBoltTargets.At(5) == 1 && kWildBoltTargets.At(6) == 2 && kWildBoltTargets.At(10) == 2);
        CHECK(kWildBoltTargets.At(0) == 1);     // not held reads as 5
        CHECK(Near(kWildBoltPct(false), 25.f) && Near(kWildBoltPct(true), 30.f));
        CHECK(kDoomhowlCadence.first == 15000 && kDoomhowlCadence.every == 20000 && kDoomhowlCastMs == 2500);
        CHECK(Near(kDoomhowlPct(false), 20.f) && Near(kDoomhowlPct(true), 30.f));
        CHECK(Near(kDoomhowlRadiusYd, 12.f) && kDoomhowlFearMs == 2000);
        CHECK(kOverchargeCastMs == 3000 && Near(kOverchargePct, 40.f));
        CHECK(InRange(kTankHitEvery, 0.f) == 8000 && InRange(kTankHitEvery, 1.f) == 10000);
        CHECK(InRange(kRendFirst, 0.5f) == 18500);
    }

    void TestPrelude()
    {
        // 3 rounds of an Enforcer and a Magus at 2.5, 12.5 and 22.5 s, from six different circles.
        CHECK(kRounds.size() == 3 && kPreludeOgres == 6);
        CHECK(kRounds[0].atMs == 2500 && kRounds[1].atMs == 12500 && kRounds[2].atMs == 22500);
        bool used[6] = {};
        for (OgreRound const& r : kRounds)
        {
            CHECK(r.enforcerCircle < kCircles.size() && r.magusCircle < kCircles.size());
            CHECK(r.enforcerCircle != r.magusCircle);
            used[r.enforcerCircle] = true;
            used[r.magusCircle] = true;
        }
        for (bool u : used)
            CHECK(u);

        PreludeClock clock;
        CHECK(!clock.Running());
        CHECK(clock.Update(5000).empty());          // not started: nothing
        clock.Start();
        CHECK(clock.Update(2000).empty());
        auto due = clock.Update(500);
        CHECK(due.size() == 1 && due[0] == 0);
        due = clock.Update(30000);                  // a long tick: both later rounds at once, in order
        CHECK(due.size() == 2 && due[0] == 1 && due[1] == 2);
        CHECK(clock.Update(1000).empty() && clock.RoundsOut() == 3);
        CHECK(clock.ArrivalAt() == kArrivalCapMs && !clock.ArrivalDue());
        for (int i = 0; i < 5; ++i)
            clock.OgreDied();
        CHECK(clock.ArrivalAt() == kArrivalCapMs);  // 5 of 6: still the cap
        clock.OgreDied();                           // the sixth at 33.5 s: he comes at 38.5 s
        CHECK(clock.OgresDead() == 6);
        CHECK(clock.ArrivalAt() == 38500);
        CHECK(!clock.ArrivalDue());
        clock.Update(4999);
        CHECK(!clock.ArrivalDue());
        clock.Update(1);
        CHECK(clock.ArrivalDue());
        clock.OgreDied();                           // a stray extra death never counts past six
        CHECK(clock.OgresDead() == 6);

        // The cap: the last ogre at 48 s still means 50 s.
        CHECK(ArrivalAtMs(6, 48000) == 50000);
        CHECK(ArrivalAtMs(6, 10000) == 15000);
        CHECK(ArrivalAtMs(3, 10000) == 50000);
        clock.Stop();
        CHECK(!clock.ArrivalDue());
        clock.Start();
        CHECK(clock.Now() == 0 && clock.OgresDead() == 0 && clock.RoundsOut() == 0);
    }

    void TestStolenPower()
    {
        CHECK(StolenPowerAfterReach(0, false) == 1);
        CHECK(StolenPowerAfterReach(7, false) == 8);
        CHECK(StolenPowerAfterReach(8, false) == 8);     // the cap, +40%
        CHECK(StolenPowerAfterReach(4, true) == 5);
        CHECK(StolenPowerAfterReach(5, true) == 5);
        CHECK(StacksAtArrival(3, false) == 3 && StacksAtArrival(12, false) == 8 && StacksAtArrival(6, true) == 5);
        CHECK(kStolenPowerCap(false) * kStolenPowerPctPerStack == 40);
        CHECK(!OverchargeDue(5, false, false));          // never on normal
        CHECK(!OverchargeDue(4, true, false));
        CHECK(OverchargeDue(5, true, false));
        CHECK(!OverchargeDue(5, true, true));            // a cast holds him: it starts when he is free
    }

    void TestLaunchDelay()
    {
        // 30 yd/s: 15 yd flies 0.5 s, so it leaves 1.5 s into the 2 s warning.
        CHECK(LaunchDelayMs(2000, 15.f, 30.f) == 1500);
        CHECK(LaunchDelayMs(2000, 60.f, 30.f) == 0);
        CHECK(LaunchDelayMs(2000, 90.f, 30.f) == 0);
        CHECK(LaunchDelayMs(2000, 0.f, 30.f) == 2000);
        CHECK(LaunchDelayMs(2000, 10.f, 0.f) == 2000);
        CHECK(Near(kWildBoltMissileSpeed, 30.f));
    }

    void TestUnstable()
    {
        CHECK(Near(UnstableRadius(1), 8.f) && Near(UnstableRadius(2), 10.f) && Near(UnstableRadius(3), 12.f));
        CHECK(Near(UnstableRadius(0), 8.f));
        CHECK(Near(UnstableCarrierPct(1), 10.f) && Near(UnstableCarrierPct(3), 30.f));
        CHECK(Near(kUnstableOthersPct, 30.f) && kUnstableFuseMs == 6000);
        // SP UR10 (F-1a's bot-only claim order): anyone may grab at 0 to 2 stacks (Eligibility maxStacks 2, so a
        // third stack is the most), bots stop at 2 (Ordering capStacks 2: a bot at or above it never claims).
        CHECK(kUnstableGrabMaxStacks == 2 && kUnstableBotCapStacks == 2);
        for (std::uint32_t stacks = 0; stacks <= 3; ++stacks)
        {
            bool const anyone = stacks <= kUnstableGrabMaxStacks;
            bool const bot = anyone && stacks < kUnstableBotCapStacks;
            CHECK(anyone == (stacks <= 2));
            CHECK(bot == (stacks <= 1));
        }

        UnstableBook book;
        UnstableFuse f = book.Grab(7, 1000);
        CHECK(f.stacks == 1 && f.burstAtMs == 7000);
        f = book.Grab(7, 4000);                         // a second grab: one more stack, the fuse not reset
        CHECK(f.stacks == 2 && f.burstAtMs == 7000);
        CHECK(book.Remaining(7, 4000) == 3000);
        f = book.Grab(9, 5000);
        CHECK(f.stacks == 1 && f.burstAtMs == 11000);
        CHECK(book.Size() == 2 && book.Stacks(7) == 2 && book.Stacks(9) == 1 && book.Stacks(8) == 0);
        CHECK(book.TakeDue(6999).empty());
        auto due = book.TakeDue(7000);
        CHECK(due.size() == 1 && due[0].carrier == 7 && due[0].stacks == 2);
        CHECK(book.Size() == 1 && book.Stacks(7) == 0 && book.Remaining(7, 7000) == 0);
        f = book.Grab(7, 8000);                         // a new grab after the burst lights a new fuse
        CHECK(f.stacks == 1 && f.burstAtMs == 14000);
        due = book.TakeDue(20000);
        CHECK(due.size() == 2);
        book.Clear();
        CHECK(book.Size() == 0);
    }
}

int main()
{
    TestSliceAndArena();
    TestTuning();
    TestPrelude();
    TestStolenPower();
    TestLaunchDelay();
    TestUnstable();
    return Report("brs_urok_test");
}
