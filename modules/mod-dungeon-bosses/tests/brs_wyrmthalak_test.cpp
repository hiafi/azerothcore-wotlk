// Host tests for WyrmthalakLogic.h (B8: Overlord Wyrmthalak): the slice, the tribes and the orders, the flex counts,
// the timers and percents of the build spec, the Mortal Wounds taunt-swap timeline (the user ruling), the burn's
// patches, the riders' lanes and their knock-aside, the missiles' timing and the measured points on the ledge.
#include "WyrmthalakLogic.h"
#include "check.h"

#include <algorithm>
#include <cmath>
#include <optional>
#include <set>

using namespace BlackrockSpireRework;
using namespace BrsWyrmthalak;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        std::set<std::uint32_t> ids;
        for (std::uint32_t id = kFirstSpell; id <= kLastSpell; ++id)
        {
            CHECK(kSpellSlice.Contains(id));
            ids.insert(id);
        }
        CHECK(ids.size() == 16);
        CHECK(kFirstSpell == SPELL_WT_DRAGONFIRE_CAST);
        CHECK(kLastSpell == SPELL_WT_MORTAL_WOUNDS);
        CHECK(SPELL_WT_MORTAL_WOUNDS == 210265);
        CHECK(!kSpellSlice.Contains(SPELL_WT_CLEAVE));      // stock
    }

    void TestTribes()
    {
        CHECK(ChampionEntry(Tribe::Spirestone) == NPC_BRS_SPIRESTONE_CHAMPION);
        CHECK(ChampionEntry(Tribe::Smolderthorn) == NPC_BRS_SMOLDERTHORN_CHAMPION);
        CHECK(ChampionEntry(Tribe::Bloodaxe) == NPC_BRS_BLOODAXE_CHAMPION);
        for (Tribe t : kTribes)
        {
            CHECK(TribeOfEntry(ChampionEntry(t)) == t);
            CHECK(TribeByName(TribeName(t)) == t);
            CHECK(kCreaturesWave1.Contains(ChampionEntry(t)));
        }
        CHECK(!TribeOfEntry(NPC_WYRMTHALAK));
        CHECK(!TribeOfEntry(NPC_BRS_BLOODAXE_WORG_RIDER));
        CHECK(!TribeByName("bloodax"));
        CHECK(!TribeByName("bloodaxes"));
        CHECK(!TribeByName(nullptr));
        CHECK(OrderText(Tribe::Spirestone) == YELL_WT_SPIRESTONE);
        CHECK(OrderText(Tribe::Smolderthorn) == YELL_WT_SMOLDERTHORN);
        CHECK(OrderText(Tribe::Bloodaxe) == YELL_WT_BLOODAXE);
        CHECK(NextTribe(Tribe::Spirestone) == Tribe::Smolderthorn);
        CHECK(NextTribe(Tribe::Bloodaxe) == Tribe::Spirestone);

        // Normal and heroic: one tribe in turn. The hard mode: two (Spirestone + Smolderthorn, then Bloodaxe +
        // Spirestone ...). Never more than the three tribes.
        std::vector<Tribe> one = OrderTribes(Tribe::Bloodaxe, 1);
        CHECK(one.size() == 1 && one[0] == Tribe::Bloodaxe);
        std::vector<Tribe> two = OrderTribes(Tribe::Bloodaxe, 2);
        CHECK(two.size() == 2 && two[0] == Tribe::Bloodaxe && two[1] == Tribe::Spirestone);
        CHECK(OrderTribes(Tribe::Spirestone, 5).size() == kTribeCount);
        CHECK(OrderTribes(Tribe::Spirestone, 0).empty());

        // The texts: 0-9, inside B8's range of BlackrockSpireRework.h (7 the horn line, B9's).
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_WYRMTHALAK)
            {
                found = true;
                CHECK(r.first == YELL_WT_PULL && r.last == EMOTE_WT_SPEAR);
            }
        CHECK(found);
        CHECK(EMOTE_WT_HORN == 7);
    }

    void TestFlexAndNumbers()
    {
        // SP: 3 / 6 boulders, 2 / 4 marked, 2 / 4 riders; "a" at 5 players, "b" at 6 or more.
        CHECK(kBoulderTargets.At(5) == 3 && kBoulderTargets.At(6) == 6 && kBoulderTargets.At(10) == 6);
        CHECK(kAxeTargets.At(5) == 2 && kAxeTargets.At(7) == 4);
        CHECK(kRiderTargets.At(5) == 2 && kRiderTargets.At(10) == 4);
        CHECK(kBoulderTargets.At(0) == 3);      // not held reads as 5

        CHECK(kBreathFirstMs == 8000 && kBreathEveryMs == 15000 && kBreathCastMs == 2000);
        CHECK(kTailFirstMs == 5000 && kTailEveryMs == 12000);
        CHECK(kCleaveFirstMs == 6000 && kCleaveEveryMs == 7000);
        CHECK(kOrderFirstMs == 10000 && kOrderEveryMs(false) == 30000 && kOrderEveryMs(true) == 25000);
        CHECK(kMortalStrikeFirstMs == 8000 && kMortalStrikeEveryMs == 8000);

        CHECK(kBreathPct(false) == 35.f && kBreathPct(true) == 45.f);
        CHECK(kTailPct(false) == 20.f && kTailPct(true) == 25.f);
        CHECK(kBoulderPct(false) == 25.f && kBoulderPct(true) == 30.f);
        CHECK(kAxePct(false) == 25.f && kAxePct(true) == 30.f);
        CHECK(kRiderPct(false) == 30.f && kRiderPct(true) == 35.f);
        // Weakened rides every one of them: each hit stays at 50% or under (SYS).
        for (bool h : { false, true })
        {
            CHECK(kBreathPct(h) <= 50.f && kTailPct(h) <= 50.f && kBoulderPct(h) <= 50.f && kAxePct(h) <= 50.f
                && kRiderPct(h) <= 50.f);
        }
        CHECK(kBurnPct == 5.f && kBurnLifeMs == 8000 && kBurnGraceMs == 3000 && kBurnLength == 20.f);
        CHECK(kBreathAngleDeg == 60.f && kBreathLength == 25.f);
        CHECK(kTailAngleDeg == 120.f && kTailLength == 15.f);
        CHECK(kBoulderRadius == 4.f && kBoulderWarnMs == 2500);
        CHECK(kAxeRadius == 6.f && kAxeWarnMs == 4000);
        CHECK(kRiderLaneWidth == 4.f && kRiderWarnMs == 3000);
        CHECK(kFuryDamagePct == 15 && kFuryHastePct == 10 && kFuryMaxStacks == 3);

        // WT18: about 30% of tank reference health, 1,113 normal / 1,233 heroic (handoff section 3.6).
        CHECK(DungeonKit::RefFlatValue(3670, 3710, kMortalStrikeTankPct, true) == 1113);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kMortalStrikeTankPct, true) == 1233);
        CHECK(kMortalWoundsHealingPct == -10 && kMortalWoundsSwapAt == 3 && kMortalWoundsMs == 15000);
    }

    // The user ruling (2026-11-15): a tank taunts only once its own stacks are gone, and the holder is at or past 3.
    // With a strike every 8 s and a 15 s debuff the old tank is always clear by the new holder's third stack: no wait.
    void TestTauntSwapTimeline()
    {
        CHECK(DebuffFallsOffBeforeNextSwap(8000, 15000, 3));
        CHECK(!DebuffFallsOffBeforeNextSwap(8000, 16000, 3));
        CHECK(!DebuffFallsOffBeforeNextSwap(8000, 15000, 1));

        struct Tank
        {
            std::uint32_t stacks = 0;
            std::uint64_t expireAt = 0;
        };
        Tank tanks[2];
        int holder = 0;
        std::uint32_t peak = 0;
        std::uint32_t swaps = 0;
        std::uint32_t waits = 0;
        for (std::uint64_t t = kMortalStrikeFirstMs; t <= 300000; t += kMortalStrikeEveryMs)
        {
            for (Tank& k : tanks)
                if (k.stacks && t >= k.expireAt)
                    k.stacks = 0;
            Tank& h = tanks[holder];
            ++h.stacks;
            h.expireAt = t + kMortalWoundsMs;
            peak = std::max(peak, h.stacks);
            Tank& other = tanks[1 - holder];
            // The other tank taunts before the next strike, once its own stacks are gone.
            std::uint64_t const nextStrike = t + kMortalStrikeEveryMs - 1;
            bool const otherClear = !other.stacks || nextStrike >= other.expireAt;
            if (h.stacks >= kMortalWoundsSwapAt)
            {
                if (otherClear)
                {
                    other.stacks = 0;
                    holder = 1 - holder;
                    ++swaps;
                }
                else
                    ++waits;
            }
        }
        CHECK(peak == kMortalWoundsSwapAt);
        CHECK(waits == 0);
        CHECK(swaps >= 10);
    }

    void TestBurnPatches()
    {
        Vec2 const apex = kWyrmthalakSpawn.XY();
        for (float facing : { 0.f, 1.f, 3.5f, 5.9f })
            for (float length : { kBurnLength, kBreathLength })
            {
                auto const pts = BurnPatchPoints(apex, facing, length);
                for (Vec2 const& p : pts)
                {
                    CHECK(DungeonKit::InFrontalCone(apex, facing, p, kBreathAngleDeg, length));
                    CHECK(DungeonKit::Distance(apex, p) >= 0.2f * length);
                }
                // Spread: no two patches on one spot.
                for (std::size_t i = 0; i < pts.size(); ++i)
                    for (std::size_t j = i + 1; j < pts.size(); ++j)
                        CHECK(DungeonKit::Distance(pts[i], pts[j]) >= 4.f);
            }
    }

    void TestRiderLanes()
    {
        Vec2 const origin = kRiderOrigin.XY();
        CHECK(DungeonKit::PointInPolygon(kLedgeHull, origin));

        // Through his spot: the lane crosses the ledge to its far rim, inside the hull, past him.
        Lane const across = RiderLane(origin, kWyrmthalakSpawn.XY());
        CHECK(across.length > DungeonKit::Distance(origin, kWyrmthalakSpawn.XY()));
        CHECK(across.length < 50.f);
        CHECK(DungeonKit::PointInPolygon(kLedgeHull, across.to));
        CHECK(Near(DungeonKit::Distance(across.from, across.to), across.length));

        // Through a spot near the ramp head: pushed to the minimum length.
        Lane const shortLane = RiderLane(origin, { origin.x + 1.f, origin.y - 1.f });
        CHECK(shortLane.length >= kRiderMinLane - 0.01f);

        // Through a player off the ledge (knocked into the lower hall): 5 yd past them, never a wall hunt.
        Vec2 const below{ -49.2f, -467.8f };
        CHECK(!DungeonKit::PointInPolygon(kLedgeHull, below));
        Lane const off = RiderLane(origin, below);
        CHECK(Near(off.length, DungeonKit::Distance(origin, below) + 5.f, 0.1f));

        // Every lane through a ledge point ends inside the hull.
        for (float x = -45.f; x <= -10.f; x += 5.f)
            for (float y = -505.f; y <= -465.f; y += 5.f)
            {
                Vec2 const p{ x, y };
                if (!DungeonKit::PointInPolygon(kLedgeHull, p))
                    continue;
                Lane const lane = RiderLane(origin, p);
                CHECK(DungeonKit::PointInPolygon(kLedgeHull, lane.to));
                CHECK(lane.length >= kRiderMinLane - 0.01f);
            }

        // Knocked aside: from the nearest point on the line, so the push is sideways; on the line, 0.5 yd off it.
        Lane const lane{ { 0.f, 0.f }, { 20.f, 0.f }, 20.f };
        Vec2 const k1 = KnockAsideOrigin(lane, { 10.f, 1.5f });
        CHECK(Near(k1.x, 10.f) && Near(k1.y, 0.f));
        Vec2 const k2 = KnockAsideOrigin(lane, { 10.f, 0.f });
        CHECK(Near(DungeonKit::Distance(k2, { 10.f, 0.f }), 0.5f));
        CHECK(Near(k2.x, 10.f));
    }

    void TestMissiles()
    {
        CHECK(MissileDelayMs(30.f, 15.f, 2500) == 500);
        CHECK(MissileDelayMs(25.f, kBoulderMissileSpeed, kBoulderWarnMs) == 1500);
        CHECK(MissileDelayMs(60.f, 15.f, 2500) == 0);
        CHECK(MissileDelayMs(10.f, 0.f, 2500) == 0);
        CHECK(MissileDelayMs(20.f, 20.f, 4000) == 3000);
        // The throwers reach every ledge point within the warning (the missile lands with the marker).
        for (Vec2 const& p : kLedgeHull)
        {
            CHECK(DungeonKit::Distance(kBoulderThrowerSpot.XY(), p) / kBoulderMissileSpeed * 1000.f
                <= float(kBoulderWarnMs));
            CHECK(DungeonKit::Distance(kAxeThrowerSpot.XY(), p) / kAxeMissileSpeed * 1000.f <= float(kAxeWarnMs));
        }
    }

    void TestRoom()
    {
        // He spawns kWyrmthalakSpawn, inside his arena and on the ledge.
        CHECK(WyrmthalakArena().Contains(kWyrmthalakSpawn.XY(), kWyrmthalakSpawn.z));
        CHECK(ArenaFor(BOSS_WYRMTHALAK).Contains(kWyrmthalakSpawn.XY(), kWyrmthalakSpawn.z));
        CHECK(DungeonKit::PointInPolygon(kLedgeHull, kWyrmthalakSpawn.XY()));
        CHECK(kWyrmthalakSpawn.z >= kLedgeZMin && kWyrmthalakSpawn.z <= kLedgeZMax);

        // The champions' landing and the riders' origin are on the ledge (and in his arena); the ramp foot and the
        // boulder thrower are below it, off it.
        CHECK(DungeonKit::PointInPolygon(kLedgeHull, kChampionLanding.XY()));
        CHECK(WyrmthalakArena().Contains(kChampionLanding.XY(), kChampionLanding.z));
        CHECK(WyrmthalakArena().Contains(kRiderOrigin.XY(), kRiderOrigin.z));
        CHECK(!DungeonKit::PointInPolygon(kLedgeHull, kChampionStart.XY()));
        CHECK(kChampionStart.z < kLedgeZMin);
        CHECK(!DungeonKit::PointInPolygon(kLedgeHull, kBoulderThrowerSpot.XY()));
        CHECK(kBoulderThrowerSpot.z < kLedgeZMin);
        CHECK(!WyrmthalakArena().Contains(kChampionStart.XY(), kChampionStart.z));
        // The second and third champions start beside the first (the spread), still off the ledge.
        for (int i = -1; i <= 1; ++i)
            CHECK(!DungeonKit::PointInPolygon(kLedgeHull, Vec2{ kChampionStart.x + float(i) * kChampionStartSpread,
                kChampionStart.y }));

        // The riders burst off the ramp head, where the war horn stands (section 3.8).
        CHECK(DungeonKit::Distance(kRiderOrigin.XY(), kWarHornSpot.XY()) < 5.f);
        // The open edge (edge A, chord 28.2 yd) faces the lower hall.
        CHECK(DungeonKit::Distance(kWyrmthalakEdgeA0, kWyrmthalakEdgeA1) > 28.f);
    }

    // F-1d: the cast queue's hand-over to a hard mode cast (B9's request), a kicked bar's hold, the breath at 10.
    void TestCastQueueHandOver()
    {
        std::uint32_t constexpr kRoar = kHardModeCastBase + 1;
        std::uint32_t constexpr kSpear = kHardModeCastBase + 2;
        DungeonKit::CastQueue queue(kCastSpacingMs);
        queue.Schedule(kRoar, 1000, 1);
        queue.Schedule(kSpear, 1500, 1);
        CHECK(queue.Next(1000) == std::optional<std::uint32_t>(kRoar));
        // The hook schedules its own next cast 20 s on: it stays (CastQueue::Started used to cancel it after the hook,
        // which pushed the next cast to a later OnUpdate).
        bool inHook = false;
        std::optional<std::uint32_t> const hold = StartHardModeCast(queue, kRoar, 1000, [&]()
        {
            inHook = true;
            CHECK(!queue.Queued(kRoar));        // consumed before the hook
            queue.Schedule(kRoar, 21000, 1);
            return std::optional<std::uint32_t>(2500);
        });
        CHECK(inHook && hold == std::optional<std::uint32_t>(2500));
        CHECK(queue.DueAt(kRoar) == std::optional<DungeonKit::CastQueue::Ms>(21000));
        CHECK(queue.Queued(kSpear));            // nothing else touched
        // The hold: nothing starts until the bar's end plus the spacing.
        CHECK(queue.Waiting(3400) && !queue.Next(3400));
        CHECK(!queue.Waiting(1000 + 2500 + kCastSpacingMs));
        CHECK(queue.Next(4500) == std::optional<std::uint32_t>(kSpear));
        // A cast that could not start: its entry is gone (unless the hook queued a retry), no hold.
        std::optional<std::uint32_t> const refused = StartHardModeCast(queue, kSpear, 4500, []()
        {
            return std::optional<std::uint32_t>();
        });
        CHECK(!refused && !queue.Queued(kSpear) && !queue.Waiting(4500));
        StartHardModeCast(queue, kRoar, 21000, [&]()
        {
            queue.Schedule(kRoar, 22000, 1);    // a retry in a second
            return std::optional<std::uint32_t>();
        });
        CHECK(queue.DueAt(kRoar) == std::optional<DungeonKit::CastQueue::Ms>(22000));

        // A kicked bar: Caustic Roar (2.5 s hold) kicked 0.8 s in. The hold ends then; the spacing counts from the
        // kick, not from the bar's planned end.
        DungeonKit::CastQueue kicked(kCastSpacingMs);
        kicked.Schedule(kSpear, 0, 1);
        StartHardModeCast(kicked, kRoar, 10000, []() { return std::optional<std::uint32_t>(2500); });
        DungeonKit::CastQueue::Ms holdUntil = 12500;
        holdUntil = EndHoldEarly(kicked, holdUntil, 10800);
        CHECK(holdUntil == 10800);
        CHECK(!kicked.Waiting(10800 + kCastSpacingMs));
        CHECK(kicked.Next(11800) == std::optional<std::uint32_t>(kSpear));
        // After the bar's end nothing changes.
        CHECK(EndHoldEarly(kicked, 12500, 12600) == 12500);

        // WT1: both tanks spared at 10 players only (the taunt swap's count).
        CHECK(BreathSparesBothTanks(10));
        for (std::uint32_t n = 5; n <= 9; ++n)
            CHECK(!BreathSparesBothTanks(n));
    }
}

int main()
{
    TestSlice();
    TestTribes();
    TestFlexAndNumbers();
    TestTauntSwapTimeline();
    TestBurnPatches();
    TestRiderLanes();
    TestMissiles();
    TestRoom();
    TestCastQueueHandOver();
    return Report("brs_wyrmthalak_test");
}
