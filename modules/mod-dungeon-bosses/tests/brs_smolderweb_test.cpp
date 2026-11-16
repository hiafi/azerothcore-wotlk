// Host tests for SmolderwebLogic.h (B4: Mother Smolderweb): the slice and the arena, the clutch's spots and floor, the
// eggs' numbers and the space math, the milk's launch delay, the Venom spells, the Broodlings' ring and their pick, the
// Brood Call's reach and the tank hold, Last Milk's rule, the Widow's Bite timeline against the taunt swap rule, and
// the beat clock.
#include "SmolderwebLogic.h"
#include "check.h"
#include <algorithm>
#include <cmath>
#include <set>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsSmolderweb;

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
        std::set<std::uint32_t> const ids{ SPELL_SW_SPRAY_CAST, SPELL_SW_SPRAY, SPELL_SW_ENCASED, SPELL_SW_EGG_HATCH,
            SPELL_SW_MILK, SPELL_SW_MILK_LOOK, SPELL_SW_VENOM, SPELL_SW_VENOM_HEROIC, SPELL_SW_WIDOWS_BITE,
            SPELL_SW_BROOD_CALL, SPELL_SW_HATCH_LOOK };
        for (std::uint32_t id : ids)
            CHECK(kSpellSlice.Contains(id));
        CHECK(ids.size() == 11);        // no two share an id
        CHECK(SPELL_SW_SPRAY_CAST == 210120u);
        CHECK(SPELL_SW_HATCH_LOOK == 210130u);
        // She spawns kSmolderwebSpawn, inside her arena.
        CHECK(SmolderwebArena().Contains(kSmolderwebSpawn.XY(), kSmolderwebSpawn.z));
        CHECK(ArenaFor(BOSS_SMOLDERWEB).Contains(kSmolderwebSpawn.XY(), kSmolderwebSpawn.z));
        // The new units sit in the ids this WP was given.
        CHECK(NPC_BRS_BROODLING == 300705u);
        CHECK(GO_BRS_SMOLDERWEB_EGG == 301251u);
        // The stock spells and the quest the fight touches.
        CHECK(SPELL_SW_QUEST_MILK == 16468u);
        CHECK(SPELL_SW_DEATH_SPIDERLINGS == 16103u);
        CHECK(kQuestRaggedJohn == 4866u);
        // Her three texts: the SP's range (groups 0-2, none stock).
        CHECK(TEXT_LAY_EGG == 0 && TEXT_BROOD_CALL == 1 && TEXT_LAST_MILK == 2);
        std::size_t found = 0;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_SMOLDERWEB)
            {
                ++found;
                CHECK(r.first == 0 && r.last == TEXT_LAST_MILK && r.firstNew == 0);
            }
        CHECK(found == 1);
    }

    void TestClutch()
    {
        CHECK(kClutchCount == 8);
        for (std::size_t i = 0; i < kClutchCount; ++i)
        {
            Point3 const p = ClutchSpot(i);
            // On the cave floor (her arena), the xy S0's, the z from NM 4 (all z >= 7, the flat-ish floor).
            CHECK(SmolderwebArena().Contains(p.XY(), p.z));
            CHECK(p.z >= 7.f);
            CHECK(Near(p.x, kSmolderwebEggSpots[i].x) && Near(p.y, kSmolderwebEggSpots[i].y));
            // At least 16 yd from her spawn (NM 4: the tank holds her there).
            CHECK(DungeonKit::Distance(p.XY(), kSmolderwebSpawn.XY()) >= 16.f);
            // No two start in each other's 4 yd (the closest pair, 6 and 8, are 7.6 yd apart).
            for (std::size_t j = i + 1; j < kClutchCount; ++j)
                CHECK(DungeonKit::Distance(p.XY(), ClutchSpot(j).XY()) >= 7.5f);
        }
        // The spots wrap (a test asking for a ninth reads the first).
        CHECK(ClutchSpot(8).x == ClutchSpot(0).x);
        // The NM table's heights.
        CHECK(Near(ClutchSpot(0).z, 11.5f) && Near(ClutchSpot(1).z, 12.1f) && Near(ClutchSpot(6).z, 7.5f));
        // The map's floor when it is near the measured one, else the measured one.
        CHECK(Near(EggZ(8.f, 8.4f, true), 8.4f));
        CHECK(Near(EggZ(8.f, 11.5f, true), 8.f));       // 3.5 yd off: a ledge over or a pit under, not this floor
        CHECK(Near(EggZ(8.f, -50000.f, false), 8.f));
        CHECK(Near(EggZ(8.f, 4.9f, true), 8.f));
        CHECK(Near(EggZ(8.f, 5.1f, true), 5.1f));       // 2.9 yd off is still this floor
    }

    void TestEggs()
    {
        // The Mine: 4 yd, 0.5 s grace, arms after 1.5 s (the deviation from "armed at once", the SP's drop under a
        // player), 20% (heroic 25%) Weakened.
        CHECK(Near(kEggRadius, 4.f));
        CHECK(kEggGraceMs == 500 && kEggArmMs == 1500);
        CHECK(Near(kEggPct(false), 20.f) && Near(kEggPct(true), 25.f));
        // The egg arms after a step's time, but not so late it is a free rest.
        CHECK(kEggArmMs > 1000 && kEggArmMs <= 2000);
        // The lay: 10 s then every 20 s, 2 targets (4 at 6 or more), 2 s warning (heroic 3 s).
        CHECK(kLayFirstMs == 10000 && kLayEveryMs == 20000);
        CHECK(kLayTargets.At(5) == 2 && kLayTargets.At(6) == 4 && kLayTargets.At(10) == 4);
        CHECK(kLayTargets.At(0) == 2);      // not held reads as 5
        CHECK(kLayWarnMs(false) == 2000 && kLayWarnMs(true) == 3000);
        CHECK(kLayBeat.firstMs == 10000 && kLayBeat.everyMs == 20000);
        // Heroic: the carry hint is wider than the call's reach.
        CHECK(kCarryClearYd > kBroodCallRangeYd);
        // The space math of the SP: 4 lay rounds (10, 30, 50, 70 s) over a 71 s (5) or 80 s (10) kill.
        CHECK(EggsAfter(4, 5) == 16);
        CHECK(EggsAfter(4, 10) == 24);
        CHECK(EggsAfter(0, 5) == 8);
        // 40 s slower at 10 adds two rounds of four: 8 eggs (the soft enrage).
        CHECK(EggsAfter(6, 10) - EggsAfter(4, 10) == 8);
        // The safety cap sits above the longest fight the SP's space math considers, and under the registry's 256
        // mechanics (BossMechanics.MaxActivePerMap) with room left for the milk, the cone and the markers.
        CHECK(kEggSafetyCap > EggsAfter(6, 10));
        CHECK(kEggSafetyCap + 100 < 256);
        // An hour at 10 players would lay more than the registry holds: the cap is what keeps the milk alive.
        CHECK(EggsAfter(180, 10) > 256);
    }

    void TestMilkAndVenom()
    {
        CHECK(kMilkFirstMs == 5000 && kMilkEveryMs == 10000);
        CHECK(kMilkTargets.At(5) == 1 && kMilkTargets.At(6) == 2 && kMilkTargets.At(10) == 2);
        CHECK(Near(kMilkRadius, 6.f) && kMilkFlightMs == 2000);
        CHECK(Near(kMilkPct(false), 15.f) && Near(kMilkPct(true), 20.f));
        // The launch delay: a missile that flies for the whole 2 s leaves at once, a short one waits.
        CHECK(MilkLaunchDelayMs(0.f) == 2000);
        CHECK(MilkLaunchDelayMs(-5.f) == 2000);
        CHECK(MilkLaunchDelayMs(20.f) == 1000);     // 20 yd at 20 yd/s is a 1 s flight
        CHECK(MilkLaunchDelayMs(40.f) == 0);
        CHECK(MilkLaunchDelayMs(60.f) == 0);
        // Venom: 1% a second a stack, 30 s, up to 5 (heroic 8), two spells.
        CHECK(Near(kVenomPctPerStack, 1.f) && kVenomMs == 30000);
        CHECK(kVenomMaxStacks(false) == 5 && kVenomMaxStacks(true) == 8);
        CHECK(VenomSpell(false) == SPELL_SW_VENOM && VenomSpell(true) == SPELL_SW_VENOM_HEROIC);
        CHECK(VenomSpell(false) != VenomSpell(true));
        // A full dose: 5% a second normal, 8% heroic.
        CHECK(Near(kVenomPctPerStack * static_cast<float>(kVenomMaxStacks(false)), 5.f));
        CHECK(Near(kVenomPctPerStack * static_cast<float>(kVenomMaxStacks(true)), 8.f));
    }

    void TestSpray()
    {
        CHECK(kSprayFirstMs == 12000 && kSprayEveryMs == 15000 && kSprayCastMs == 2000);
        CHECK(Near(kSprayAngleDeg, 60.f) && Near(kSprayLengthYd, 20.f));
        CHECK(Near(kSprayPct(false), 25.f) && Near(kSprayPct(true), 30.f));
        CHECK(kEncasedMs == 2000);
    }

    void TestBroodlings()
    {
        // The ring: three spots, each 1.5 yd from the centre, 120 degrees apart.
        std::array<Vec2, 3> const ring = BroodlingSpots({ 10.f, 20.f }, 0.5f);
        for (Vec2 const& p : ring)
            CHECK(Near(DungeonKit::Distance(p, { 10.f, 20.f }), kBroodlingRingYd));
        CHECK(Near(DungeonKit::Distance(ring[0], ring[1]), DungeonKit::Distance(ring[1], ring[2])));
        CHECK(Near(DungeonKit::Distance(ring[0], ring[1]), DungeonKit::Distance(ring[0], ring[2])));
        CHECK(kBroodlingsPerEgg == 3);
        // 2,000 health (heroic 3,000): three of them are 6,000 and 9,000 (the SP's failing path checks).
        CHECK(kBroodlingHealth * kBroodlingsPerEgg == 6000);
        CHECK(kBroodlingHealthHeroic * kBroodlingsPerEgg == 9000);

        // The pick: the most Venom; a tie goes to the hatcher, else the nearest, else the lower guid.
        std::vector<BroodlingCandidate> players{ { 1, 0, 10.f }, { 2, 3, 30.f }, { 3, 5, 25.f }, { 4, 5, 8.f } };
        CHECK(PickBroodlingTarget(players, 1).value() == 4);        // 3 and 4 tie on 5 stacks: 4 is nearer
        CHECK(PickBroodlingTarget(players, 3).value() == 3);        // the hatcher is one of the tied
        CHECK(PickBroodlingTarget(players, 2).value() == 4);        // the hatcher has less: the milkiest wins
        CHECK(PickBroodlingTarget(players, 0).value() == 4);        // no hatcher recorded
        players[3].distance = 25.f;
        CHECK(PickBroodlingTarget(players, 0).value() == 3);        // equal distance: the lower guid
        // Nobody with Venom: the hatcher, if he is still there; else nobody (it keeps its victim).
        std::vector<BroodlingCandidate> const clean{ { 7, 0, 5.f }, { 8, 0, 9.f } };
        CHECK(PickBroodlingTarget(clean, 8).value() == 8);
        CHECK(!PickBroodlingTarget(clean, 9).has_value());
        CHECK(!PickBroodlingTarget(clean, 0).has_value());
        CHECK(!PickBroodlingTarget({}, 8).has_value());
        // Anyone with Venom beats a clean hatcher.
        std::vector<BroodlingCandidate> const milky{ { 5, 1, 50.f }, { 8, 0, 1.f } };
        CHECK(PickBroodlingTarget(milky, 8).value() == 5);
        CHECK(kBroodlingRetargetMs == 1000);
    }

    void TestBroodCall()
    {
        // The call's reach and its timing (heroic: 25 s then every 30 s, a 3 s cast).
        CHECK(Near(kBroodCallRangeYd, 15.f));
        CHECK(kBroodCallFirstMs == 25000 && kBroodCallEveryMs == 30000 && kBroodCallCastMs == 3000);
        CHECK(kBroodCallBeat.firstMs == 25000 && kBroodCallBeat.everyMs == 30000);
        Vec2 const boss{ 0.f, 0.f };
        std::vector<Vec2> const eggs{ { 10.f, 0.f }, { 15.f, 0.f }, { 15.1f, 0.f }, { 0.f, -14.9f }, { 30.f, 30.f } };
        std::vector<std::size_t> const in = EggsInBroodRange(eggs, boss);
        CHECK(in.size() == 3 && in[0] == 0 && in[1] == 1 && in[2] == 3);    // 15 yd is inside, 15.1 is not
        CHECK(EggsInBroodRange({}, boss).empty());

        // The clutch is out of the call's reach of her spawn: the tank can hold her where she is on the pull.
        std::vector<Vec2> clutch;
        for (std::size_t i = 0; i < kClutchCount; ++i)
            clutch.push_back(ClutchSpot(i).XY());
        CHECK(EggsInBroodRange(clutch, kSmolderwebSpawn.XY()).empty());

        // Nearest player to an egg.
        std::vector<Vec2> const players{ { 5.f, 5.f }, { 1.f, 0.f }, { -3.f, 0.f } };
        CHECK(NearestTo(players, { 0.f, 0.f }).value() == 1);
        CHECK(NearestTo(players, { -5.f, 0.f }).value() == 2);
        CHECK(!NearestTo({}, { 0.f, 0.f }).has_value());
        CHECK(NearestTo({ { 2.f, 0.f }, { 0.f, 2.f } }, { 0.f, 0.f }).value() == 0);    // the first on a tie
    }

    void TestParkHold()
    {
        // The hold circle keeps every egg out of the call's reach: the call's 15 yd, the circle, a margin.
        CHECK(Near(ParkAvoidRadiusYd(), kBroodCallRangeYd + kParkRadiusYd + kParkMarginYd));
        CHECK(Near(ParkAvoidRadiusYd(), 18.f));
        CHECK(kParkRenewMs < kParkHoldMs);              // renewed before it ends: no gap for the bots
        CHECK(kParkMaxMoveYd >= 10.f && kParkMaxMoveYd <= 15.f);
        std::vector<Vec2> const eggs{ { 20.f, 0.f }, { 0.f, 30.f } };
        CHECK(ParkSpotClean({ 0.f, 0.f }, eggs));
        CHECK(ParkViolations({ 0.f, 0.f }, eggs) == 0);
        CHECK(!ParkSpotClean({ 3.f, 0.f }, eggs));      // 17 yd from the first
        CHECK(ParkViolations({ 3.f, 0.f }, eggs) == 1);
        CHECK(ParkViolations({ 5.f, 0.f }, { { 20.f, 0.f }, { 20.f, 2.f } }) == 2);
        CHECK(ParkSpotClean({ 0.f, 0.f }, {}));
        // From her spawn the first clutch has exactly one egg inside the strict ring (spot 2, 17.2 yd): the hold may
        // shift her a few yd, never more than kParkMaxMoveYd.
        std::vector<Vec2> clutch;
        for (std::size_t i = 0; i < kClutchCount; ++i)
            clutch.push_back(ClutchSpot(i).XY());
        CHECK(ParkViolations(kSmolderwebSpawn.XY(), clutch) == 1);
    }

    void TestLastMilk()
    {
        // The gossip: quest 4866 incomplete and the aura missing; alive, in the cave, not a game master.
        CHECK(LastMilkWanted(true, false, true, false, 30.f, 2.f));
        CHECK(!LastMilkWanted(false, false, true, false, 30.f, 2.f));       // dead: it would be stripped
        CHECK(!LastMilkWanted(true, true, true, false, 30.f, 2.f));         // a game master
        CHECK(!LastMilkWanted(true, false, false, false, 30.f, 2.f));       // no quest (or done, or not taken)
        CHECK(!LastMilkWanted(true, false, true, true, 30.f, 2.f));         // already has it
        CHECK(LastMilkWanted(true, false, true, false, kLastMilkRangeYd, 0.f));
        CHECK(!LastMilkWanted(true, false, true, false, kLastMilkRangeYd + 1.f, 0.f));      // another wing
        CHECK(!LastMilkWanted(true, false, true, false, 30.f, kLastMilkZBandYd + 1.f));     // another floor
        CHECK(!LastMilkWanted(true, false, true, false, 30.f, -(kLastMilkZBandYd + 1.f)));
        CHECK(LastMilkWanted(true, false, true, false, 30.f, -kLastMilkZBandYd));
        // The cave (about 77 yd long) is inside the range from her spawn.
        CHECK(kLastMilkRangeYd > 77.f);
    }

    // Widow's Bite (10 players): the debuff must fall off the old tank before the new tank reaches the swap count.
    void TestWidowsBite()
    {
        CHECK(kBiteFirstMs == 6000 && kBiteEveryMs == 6000 && kBiteMs == 15000);
        CHECK(kBiteSwapAtStacks == 3);
        CHECK(kBiteStackCap == 255);
        CHECK(Near(kBitePctPerStack, 1.f));
        CHECK(BiteHoldMs() == 18000);
        CHECK(BiteClearMs() == 3000);
        CHECK(kBiteMs < BiteHoldMs());

        // The timeline: two tanks, 100 ms ticks, bites every 6 s on the holder (from 6 s), each bite one stack and
        // the 15 s refreshed, a taunt (8 s cooldown) by the other tank when the holder is at 3 stacks and its own are
        // gone (the user ruling of 2026-11-15). Three minutes: ten swaps, never a fourth stack, never a wait.
        struct Tank
        {
            std::uint32_t stacks = 0;
            std::int64_t fallsAt = 0;
        };
        Tank tanks[2];
        int holder = 0;
        std::int64_t tauntReadyAt = 0;
        std::uint32_t swaps = 0;
        std::uint32_t peak = 0;
        std::uint32_t ticksAtCount = 0;
        std::int64_t nextBite = kBiteFirstMs;
        for (std::int64_t t = 0; t <= 180000; t += 100)
        {
            for (Tank& tank : tanks)
                if (tank.stacks && t >= tank.fallsAt)
                    tank.stacks = 0;
            if (t >= nextBite)
            {
                ++tanks[holder].stacks;
                tanks[holder].fallsAt = t + kBiteMs;
                nextBite += kBiteEveryMs;
            }
            peak = std::max(peak, tanks[holder].stacks);
            if (tanks[holder].stacks >= kBiteSwapAtStacks)
            {
                ++ticksAtCount;
                int const other = 1 - holder;
                if (tanks[other].stacks == 0 && t >= tauntReadyAt)
                {
                    holder = other;
                    tauntReadyAt = t + 8000;
                    ++swaps;
                }
            }
        }
        CHECK(swaps == 10);
        CHECK(peak == kBiteSwapAtStacks);
        CHECK(ticksAtCount == swaps);       // the swap is the same tick as the third stack: nobody waits

        // R-1-B n1: a bite needs her target within kBiteReachYd, else it is tried again 1 s later. A tank who taunts
        // from range (she walks 2.5 s, or 7 s: a bite comes due on the way and waits): the bites on the new holder
        // only come later, so the swaps still flow, the old holder is still clear first, nobody waits at the count.
        CHECK(kBiteReachYd == 8.f && kBiteRetryMs == 1000 && kBiteRetryMs < kBiteEveryMs);
        for (std::int64_t const walkMs : { 2500, 7000 })
        {
            Tank walk[2];
            int h = 0;
            std::int64_t ready = 0;
            std::int64_t inReachAt = 0;
            std::uint32_t walkSwaps = 0;
            std::uint32_t walkPeak = 0;
            std::uint32_t early = 0;
            std::uint32_t retries = 0;
            std::uint32_t waitTicks = 0;
            BeatClock bite;
            bite.Start(0, kBiteFirstMs);
            for (std::int64_t t = 0; t <= 180000; t += 100)
            {
                for (Tank& tank : walk)
                    if (tank.stacks && t >= tank.fallsAt)
                        tank.stacks = 0;
                if (bite.Due(std::uint64_t(t)))
                {
                    if (t >= inReachAt)
                    {
                        bite.Fired(std::uint64_t(t), kBiteEveryMs);
                        ++walk[h].stacks;
                        walk[h].fallsAt = t + kBiteMs;
                        if (walk[h].stacks == kBiteSwapAtStacks && walk[1 - h].stacks)
                            ++early;
                    }
                    else
                    {
                        bite.Start(std::uint64_t(t), kBiteRetryMs);
                        ++retries;
                    }
                }
                walkPeak = std::max(walkPeak, walk[h].stacks);
                if (walk[h].stacks >= kBiteSwapAtStacks)
                {
                    ++waitTicks;
                    if (!walk[1 - h].stacks && t >= ready)
                    {
                        h = 1 - h;
                        ready = t + 8000;
                        inReachAt = t + walkMs;
                        ++walkSwaps;
                    }
                }
            }
            CHECK(walkSwaps >= 7);
            CHECK(walkPeak == kBiteSwapAtStacks);
            CHECK(early == 0);
            CHECK(waitTicks == walkSwaps);
            CHECK((retries > 0) == (walkMs > kBiteEveryMs));
        }

        // A solo tank (no swap): a bite every 6 s with the 15 s refreshed, no cap: 10 stacks at 60 s.
        std::uint32_t solo = 0;
        for (std::uint32_t t = kBiteFirstMs; t <= 60000; t += kBiteEveryMs)
            ++solo;
        CHECK(solo == 10);
    }

    void TestBeatClock()
    {
        BeatClock clock;
        CHECK(!clock.On() && !clock.Due(100000));
        clock.Start(1000, 5000);
        CHECK(clock.On() && clock.DueMs() == 6000);
        CHECK(!clock.Due(5999) && clock.Due(6000) && clock.Due(9000));
        // It stays due until fired (a cast beat waits for her to be free).
        CHECK(clock.Due(7000) && clock.Due(7500));
        clock.Fired(6000, 10000);
        CHECK(clock.DueMs() == 16000 && !clock.Due(15999) && clock.Due(16000));
        // Fired late: the next is still start to start, never in the past.
        clock.Fired(16000, 10000);
        CHECK(clock.DueMs() == 26000);
        clock.Fired(40000, 10000);
        CHECK(clock.DueMs() == 50000);
        clock.Stop();
        CHECK(!clock.On() && !clock.Due(1000000));
        clock.Start(0, 0);
        CHECK(clock.Due(0));

        // The fight's beats: lay 10 / 20, milk 5 / 10, spray 12 / 15, call 25 / 30, bite 6 / 6.
        CHECK(kMilkBeat.firstMs == 5000 && kMilkBeat.everyMs == 10000);
        CHECK(kSprayBeat.firstMs == 12000 && kSprayBeat.everyMs == 15000);
        CHECK(kBiteBeat.firstMs == 6000 && kBiteBeat.everyMs == 6000);
        // Her two casts (a 2 s spray, a 3 s call) do not overlap on the first rounds: the spray at 12 ends at 14, the
        // call at 25; the spray due at 27 waits for the call to end at 28.
        CHECK(kSprayBeat.firstMs + kSprayCastMs < kBroodCallBeat.firstMs);
        CHECK(kSprayBeat.firstMs + kSprayBeat.everyMs > kBroodCallBeat.firstMs);
    }
}

int main()
{
    TestSliceAndArena();
    TestClutch();
    TestEggs();
    TestMilkAndVenom();
    TestSpray();
    TestBroodlings();
    TestBroodCall();
    TestParkHold();
    TestLastMilk();
    TestWidowsBite();
    TestBeatClock();
    return Report("brs_smolderweb_test");
}
