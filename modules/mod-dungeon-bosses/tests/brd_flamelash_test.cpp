// Host tests for FlamelashLogic.h (D20: Ambassador Flamelash): the slice and the arenas (S0's), the seven runes (four
// at 34 yd, three at 24 yd from the chamber's center), the rune pick (never the same twice in a row, never one that is
// up), the march speed per rune, the spirit cap and the arrival rule, the stack (+10% damage, +5% size, ten at most),
// Kindling's ticks and reach, the heroic trail steps, the percents and the beats against the build spec (S4 740-783).
#include "FlamelashLogic.h"
#include "check.h"

#include <cmath>
#include <random>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdFlamelash;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return a - b < eps && b - a < eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation, in declaration order.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211490 && kSpellSlice.last == 211519);
        CHECK(SPELL_FL_PORTAL == 211490);
        CHECK(SPELL_FL_BURNING_SPIRIT == 211491);
        CHECK(SPELL_FL_FIRE_BLAST == 211493);
        CHECK(SPELL_FL_KINDLING == 211494);
        CHECK(SPELL_FL_TRAIL == 211499);
        for (std::uint32_t id = SPELL_FL_PORTAL; id <= SPELL_FL_TRAIL; ++id)
            CHECK(kSpellSlice.Contains(id));
        // The stock spells are never ids of the slice (rule 15: copies, never edits).
        CHECK(!kSpellSlice.Contains(SPELL_STOCK_FIRE_BLAST));
        CHECK(!kSpellSlice.Contains(SPELL_STOCK_BURNING_SPIRIT));
        CHECK(SPELL_STOCK_FIRE_BLAST == 13342 && SPELL_STOCK_BURNING_SPIRIT == 14744);
    }

    void TestArenas()
    {
        // Ambassador Flamelash spawns kFlamelashSpawn, inside the shared arena and the fight arena; every rune and the
        // march's ends (a rune, the chamber's center) are inside the fight arena, 4 yd or more from its edge.
        CHECK(FlamelashArena().Contains(kFlamelashSpawn.XY(), kFlamelashSpawn.z));
        CHECK(ArenaFor(BOSS_FLAMELASH).Contains(kFlamelashSpawn.XY(), kFlamelashSpawn.z));
        Arena const fight = FightArena();
        CHECK(fight.Contains(kFlamelashSpawn.XY(), kFlamelashSpawn.z));
        CHECK(fight.Contains(kChamberCenter, kChamberZ));
        for (Rune const& rune : kRunes)
        {
            CHECK(fight.Contains({ rune.x, rune.y }, rune.z));
            CHECK(DungeonKit::Distance(kChamberCenter, { rune.x, rune.y }) + 3.9f < kArenaRadius);
        }
        // F-1a widened the shared arena to the fight's circle (STAGE-D20 request 2): every rune is on it too.
        for (Rune const& rune : kRunes)
            CHECK(FlamelashArena().Contains({ rune.x, rune.y }, rune.z));
        // The floor band holds the runes and the spawn.
        CHECK(kChamberZ > -64.f && kChamberZ < -57.f);
        // The texts sit in his range (0-3: 0 stock).
        CHECK(SAY_PULL == 0 && SAY_DEATH == 3);
        bool found = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_FLAMELASH)
            {
                found = true;
                CHECK(range.first == SAY_PULL && range.last == SAY_DEATH && range.firstNew == 1);
            }
        CHECK(found);
        CHECK(NPC_FLAMELASH == 9156 && NPC_BURNING_SPIRIT == 9178 && NPC_BRD_PORTAL_ANCHOR == 300842);
    }

    void TestRunes()
    {
        // Seven runes: four cardinal at 34 yd, three diagonal at 24 yd from the chamber's center (the fourth diagonal
        // is missing, handoff correction 40).
        CHECK(kRuneCount == 7);
        int cardinals = 0;
        int diagonals = 0;
        std::set<std::uint32_t> entries;
        for (std::size_t i = 0; i < kRuneCount; ++i)
        {
            float const range = RuneRange(i);
            if (kRunes[i].cardinal)
            {
                ++cardinals;
                CHECK(Near(range, 34.f, 0.2f));
            }
            else
            {
                ++diagonals;
                CHECK(Near(range, 24.f, 0.2f));
            }
            entries.insert(kRunes[i].goEntry);
            CHECK(kRunes[i].goEntry >= 170578 && kRunes[i].goEntry <= 170584);
        }
        CHECK(cardinals == 4 && diagonals == 3);
        CHECK(entries.size() == kRuneCount);        // the seven stock objects, once each
        // Flamelash's own spawn is 3 yd off the center, the tank's spot.
        CHECK(DungeonKit::Distance(kChamberCenter, kFlamelashSpawn.XY()) < 4.f);
        // Every rune is closer than the fight arena's wall.
        for (std::size_t i = 0; i < kRuneCount; ++i)
            CHECK(RuneRange(i) < kArenaRadius);
    }

    void TestRunePick()
    {
        // Never the same twice in a row, never one that is up.
        for (int last = -1; last < static_cast<int>(kRuneCount); ++last)
            for (std::uint32_t n = 0; n < 40; ++n)
            {
                auto const pick = PickRune(last, 0, [n](std::uint32_t count) { return n % count; });
                CHECK(pick.has_value());
                CHECK(static_cast<int>(*pick) != last);
            }
        // A busy rune is skipped, whatever the roll.
        std::uint32_t const busy = 0b0101010;       // runes 1, 3, 5 up
        std::set<std::size_t> seen;
        for (std::uint32_t n = 0; n < 40; ++n)
        {
            auto const pick = PickRune(0, busy, [n](std::uint32_t count) { return n % count; });
            CHECK(pick.has_value());
            CHECK(!(busy & (1u << *pick)));
            CHECK(*pick != 0);
            seen.insert(*pick);
        }
        CHECK(seen == std::set<std::size_t>({ 2, 4, 6 }));
        // Everything up: nothing opens. Only the last one free: it is not repeated either.
        CHECK(!PickRune(-1, kAllRunes, [](std::uint32_t) { return 0u; }).has_value());
        CHECK(!PickRune(2, kAllRunes & ~(1u << 2), [](std::uint32_t) { return 0u; }).has_value());
        CHECK(PickRune(-1, kAllRunes & ~(1u << 2), [](std::uint32_t) { return 0u; }) == std::optional<std::size_t>(2));
        // A rand that overshoots is clamped, not out of range.
        auto const clamped = PickRune(-1, 0, [](std::uint32_t) { return 999u; });
        CHECK(clamped.has_value() && *clamped < kRuneCount);
        // Every rune opens given enough rolls (a long run covers all seven).
        std::set<std::size_t> all;
        int last = -1;
        std::mt19937 gen(20);
        for (std::uint32_t n = 0; n < 200; ++n)
        {
            auto const pick = PickRune(last, 0, [&gen](std::uint32_t count) { return gen() % count; });
            CHECK(pick.has_value());
            CHECK(static_cast<int>(*pick) != last);
            all.insert(*pick);
            last = static_cast<int>(*pick);
        }
        CHECK(all.size() == kRuneCount);
    }

    void TestSpirits()
    {
        // The march takes kSpiritTravelS from every rune: the 34 yd runes at 5.67 yd/s, the 24 yd ones at 4 yd/s (the
        // stock 6 yd/s would reach him 1.7 s sooner from a diagonal).
        for (std::size_t i = 0; i < kRuneCount; ++i)
        {
            float const range = RuneRange(i);
            float const speed = SpiritSpeed(range);
            CHECK(speed >= kSpiritMinSpeed && speed <= kSpiritMaxSpeed);
            CHECK(Near(range / speed, kSpiritTravelS, 0.01f));
        }
        CHECK(Near(SpiritSpeed(34.f), 34.f / 6.f));
        CHECK(Near(SpiritSpeed(24.f), 4.f));
        // Never faster than the stock walk, never crawling: a spirit that starts next to him or far off is clamped.
        CHECK(Near(SpiritSpeed(1.f), kSpiritMinSpeed));
        CHECK(Near(SpiritSpeed(80.f), kSpiritMaxSpeed));
        // About 6 s from the ring (S4: "about 6 yd per s").
        CHECK(kSpiritTravelS == 6.f);
        // The cap: below it a spirit spills, at it none.
        CHECK(CanSpill(0, false) && CanSpill(11, false) && !CanSpill(12, false));
        CHECK(CanSpill(15, true) && !CanSpill(16, true));
        CHECK(kSpiritCap(false) == 12 && kSpiritCap(true) == 16);
        // The cap never bites a group that kills its anchors: one anchor spills one spirit per 3 s and each is alive
        // about 6 s (two); five heroic anchors (2 s) keep about 15 alive, under 16.
        CHECK(2u * 1 <= kSpiritCap(false));
        CHECK(static_cast<std::uint32_t>(kSpiritTravelS / (kSpillEveryMs(true) / 1000.f)) * 5 <= kSpiritCap(true));
        // Arrival: within his reach plus the margin.
        CHECK(Arrived(2.f, 1.f) && Arrived(2.5f, 1.f) && !Arrived(2.6f, 1.f));
        CHECK(Arrived(0.f, 0.f) && !Arrived(10.f, 1.5f));
        // A larger reach is reached sooner.
        CHECK(Arrived(4.f, 2.6f) && !Arrived(4.f, 1.f));
    }

    void TestStack()
    {
        // +10% damage and +5% size per stack, ten at most.
        CHECK(kStackCap == 10);
        CHECK(StacksAfterArrival(0) == 1 && StacksAfterArrival(9) == 10 && StacksAfterArrival(10) == 10);
        CHECK(StacksAfterArrival(200) == 10);
        CHECK(Near(DamageScale(0), 1.f) && Near(DamageScale(1), 1.1f) && Near(DamageScale(10), 2.f));
        CHECK(Near(DamageScale(11), 2.f) && Near(DamageScale(255), 2.f));    // the cap is the ceiling: +100%
        CHECK(Near(SizeScale(0), 1.f) && Near(SizeScale(1), 1.05f) && Near(SizeScale(10), 1.5f));
        CHECK(Near(SizeScale(50), 1.5f));
        CHECK(kStackLifeMs == 30000);
        // Monotone.
        for (std::uint32_t s = 0; s < 12; ++s)
        {
            CHECK(DamageScale(s + 1) >= DamageScale(s));
            CHECK(SizeScale(s + 1) >= SizeScale(s));
        }
    }

    void TestKindling()
    {
        // An 8 s channel, a tick a second.
        CHECK(kKindlingMs == 8000 && kKindlingTickMs == 1000 && kKindlingTicks == 8);
        // Reach: 8 yd (heroic 10) on the plane, 8 yd of height at most.
        CHECK(InKindling(8.f, 0.f, false) && !InKindling(8.1f, 0.f, false));
        CHECK(InKindling(10.f, 0.f, true) && !InKindling(10.1f, 0.f, true));
        CHECK(InKindling(8.f, 8.f, false) && InKindling(8.f, -8.f, false) && !InKindling(8.f, 8.1f, false));
        CHECK(InKindling(0.f, 0.f, false));
        CHECK(!InKindling(9.f, 0.f, false) && InKindling(9.f, 0.f, true));
        // The percents of a tick (S4: others 8% / 12%, the target 3% / 5%), by spell.
        CHECK(Near(BasePct(SPELL_FL_KINDLING_BURN, false), 8.f) && Near(BasePct(SPELL_FL_KINDLING_BURN, true), 12.f));
        CHECK(Near(BasePct(SPELL_FL_KINDLING_SELF, false), 3.f) && Near(BasePct(SPELL_FL_KINDLING_SELF, true), 5.f));
        // The target burns less than the others, on both difficulties.
        CHECK(BasePct(SPELL_FL_KINDLING_SELF, false) < BasePct(SPELL_FL_KINDLING_BURN, false));
        CHECK(BasePct(SPELL_FL_KINDLING_SELF, true) < BasePct(SPELL_FL_KINDLING_BURN, true));
        // A whole channel next to the target: 8 ticks of 8% is 64% (heroic 96%).
        CHECK(Near(BasePct(SPELL_FL_KINDLING_BURN, false) * kKindlingTicks, 64.f));
        CHECK(Near(BasePct(SPELL_FL_KINDLING_BURN, true) * kKindlingTicks, 96.f));
        // Beats.
        CHECK(kKindlingFirstMs == 15000);
        CHECK(kKindlingEveryMs(false) == 25000 && kKindlingEveryMs(true) == 20000);
        // The channel always ends before the next one is due.
        CHECK(kKindlingMs < kKindlingEveryMs(false) && kKindlingMs < kKindlingEveryMs(true));
    }

    void TestTrail()
    {
        // FL5, heroic only: a patch every second tick (2, 4, 6, 8 s), up to four a channel.
        for (std::uint32_t tick = 1; tick <= kKindlingTicks; ++tick)
            CHECK(!TrailOnTick(tick, false, 0));
        std::vector<std::uint32_t> ticks;
        std::uint32_t placed = 0;
        for (std::uint32_t tick = 0; tick <= kKindlingTicks + 3; ++tick)
            if (TrailOnTick(tick, true, placed))
            {
                ticks.push_back(tick);
                ++placed;
            }
        CHECK((ticks == std::vector<std::uint32_t>{ 2, 4, 6, 8 }));
        CHECK(TrailsPerChannel(true) == 4 && TrailsPerChannel(false) == 0);
        // The cap holds even when the tick would qualify.
        CHECK(!TrailOnTick(8, true, 4));
        CHECK(!TrailOnTick(0, true, 0));
        CHECK(!TrailOnTick(10, true, 0));       // past the channel
        // 4 yd, 15 s with the warning, 8% a second.
        CHECK(Near(kTrailRadius, 4.f) && kTrailLifeMs == 15000 && kTrailWarnMs < kTrailLifeMs);
        CHECK(Near(BasePct(SPELL_FL_TRAIL, false), 8.f) && Near(BasePct(SPELL_FL_TRAIL, true), 8.f));
        // The spec's space math: "heroic trail patches peak at about 5, about 250 sq yd (5%)" of about 4,700 sq yd.
        float const patch = 3.14159265f * kTrailRadius * kTrailRadius;      // about 50 sq yd each
        CHECK(Near(patch * 5.f, 251.3f, 1.f));
        // At most two channels' patches overlap in time (a patch lives 15 s, a channel comes every 20 s and lays them
        // over its 8 s): never more than 8 standing.
        std::uint32_t const channelsOverlapping = (kTrailLifeMs + kKindlingMs) / kKindlingEveryMs(true) + 1;
        CHECK(channelsOverlapping * kTrailMax >= 4 && channelsOverlapping <= 2);
    }

    void TestPercents()
    {
        // Fire Blast: 15% (heroic 20%) of the tank row by default (the spec's "stock rescaled" cell is unset).
        CHECK(Near(BasePct(SPELL_FL_FIRE_BLAST, false), 15.f) && Near(BasePct(SPELL_FL_FIRE_BLAST, true), 20.f));
        CHECK(kFireBlastFirstMs == 2000 && kFireBlastEveryMs == 7000 && Near(kFireBlastRangeYd, 20.f));
        // A spell that deals no damage has no percent.
        CHECK(Near(BasePct(SPELL_FL_PORTAL, false), 0.f) && Near(BasePct(SPELL_FL_KINDLING, true), 0.f));
        CHECK(Near(BasePct(SPELL_FL_BURNING_SPIRIT, false), 0.f));
        // His stack on top: x1.0 at none, x2.0 at ten, never more.
        CHECK(Near(ScaledPct(SPELL_FL_FIRE_BLAST, false, 0), 15.f));
        CHECK(Near(ScaledPct(SPELL_FL_FIRE_BLAST, false, 10), 30.f));
        CHECK(Near(ScaledPct(SPELL_FL_FIRE_BLAST, true, 5), 30.f));
        CHECK(Near(ScaledPct(SPELL_FL_KINDLING_BURN, true, 10), 24.f));
        CHECK(Near(ScaledPct(SPELL_FL_KINDLING_BURN, true, 99), 24.f));
        CHECK(Near(ScaledPct(SPELL_FL_PORTAL, true, 10), 0.f));
        // The ceiling: a full stack on heroic Kindling kills a player who stays in it (the failing path's end).
        CHECK(ScaledPct(SPELL_FL_KINDLING_BURN, true, kStackCap) * kKindlingTicks > 100.f);
        // On normal at no stacks a whole channel does not kill (64%).
        CHECK(ScaledPct(SPELL_FL_KINDLING_BURN, false, 0) * kKindlingTicks < 100.f);
    }

    void TestBeats()
    {
        // Portals: the first at 10 s, then every 30 s (heroic 20 s); a spirit every 3 s (heroic 2 s).
        CHECK(kPortalFirstMs(false) == 10000 && kPortalFirstMs(true) == 10000);
        CHECK(kPortalEveryMs(false) == 30000 && kPortalEveryMs(true) == 20000);
        CHECK(kSpillEveryMs(false) == 3000 && kSpillEveryMs(true) == 2000);
        // About 3 portals in a 90 s normal fight (10, 40, 70), 4 to 5 in a 100 s heroic one (10, 30, 50, 70, 90).
        auto portalsIn = [](bool heroic, std::uint32_t fightMs)
        {
            std::uint32_t n = 0;
            for (std::uint64_t t = kPortalFirstMs(heroic); t <= fightMs; t += kPortalEveryMs(heroic))
                ++n;
            return n;
        };
        CHECK(portalsIn(false, 90000) == 3);
        CHECK(portalsIn(true, 100000) == 5);
        // The clock: due at its start time, again `every` after it, never in the past.
        BeatClock clock;
        CHECK(!clock.Due(100000));
        clock.Start(1000, 10000);
        CHECK(!clock.Due(10999) && clock.Due(11000));
        clock.Fired(11000, 30000);
        CHECK(clock.DueMs() == 41000 && !clock.Due(40999) && clock.Due(41000));
        clock.Fired(100000, 30000);     // late: the next one is 30 s after now
        CHECK(clock.DueMs() == 130000);
        clock.Stop();
        CHECK(!clock.On() && !clock.Due(999999));
        // The chain is Kindling at 15 s: after the first portal (10 s), before the second (40 s).
        CHECK(kKindlingFirstMs > kPortalFirstMs(false) && kKindlingFirstMs < kPortalFirstMs(false)
            + kPortalEveryMs(false));
        // The tank's Spot and its re-post.
        CHECK(kTankSpotMs == 20000 && Near(kTankSpotRadius, 5.f));
        CHECK(kSpiritReaimMs <= 1000);
    }
}

int main()
{
    TestSlice();
    TestArenas();
    TestRunes();
    TestRunePick();
    TestSpirits();
    TestStack();
    TestKindling();
    TestTrail();
    TestPercents();
    TestBeats();
    return Report("brd_flamelash_test");
}
