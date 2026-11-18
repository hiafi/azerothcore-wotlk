// Host tests for PhalanxLogic.h (D19: Phalanx and the Rowdy Patrons): the slice, the text groups, the spec's numbers,
// the state machine against D17's BarModel (the three wake-ups, one walk, the door), the bar floor (the throw floor,
// the tables and their chairs, the tank's Spot, the fixed landings), the throw speed, the timeline (the first beats,
// the cadences, a throw and Last Call never at once, the Volley from 50%), and Property Damage (which table a knock
// smashes, each once, the Outrage scale and cap, the patrons' spots).
#include "PhalanxLogic.h"
#include "check.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdPhalanx;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    float MinTableDistance(Vec2 p)
    {
        float best = 1000.f;
        for (Vec2 const& t : kTables)
            best = std::min(best, DungeonKit::Distance(t, p));
        return best;
    }

    // One start of a beat as the engine's UpdateAI runs it, every 100 ms: a throw lasts kThrowWarnMs from its grab,
    // Last Call's bar kLastCallCastMs; the stock casts are instant. `volleyAtMs`: when he drops to 50%.
    struct Fire
    {
        std::uint64_t at = 0;
        Beat beat = Beat::ThrowOut;
    };

    std::vector<Fire> Run(bool heroic, std::uint64_t horizonMs, std::uint64_t volleyAtMs)
    {
        std::vector<Fire> fires;
        Timeline t;
        std::uint64_t const pull = 100;     // the AI's clock has run before the pull
        t.Start(heroic, pull);
        std::uint64_t throwEnd = 0;
        std::uint64_t castEnd = 0;
        for (std::uint64_t now = pull; now <= pull + horizonMs; now += 100)
        {
            if (now >= pull + volleyAtMs)
                t.ArmVolley(now);
            for (Beat beat : { Beat::ThrowOut, Beat::LastCall, Beat::Thunderclap, Beat::MightyBlow, Beat::Volley })
            {
                if (!t.Due(beat, now))
                    continue;
                if (!MayStart(beat, now < throwEnd, now < castEnd))
                {
                    t.Retry(beat, now);
                    continue;
                }
                t.Fired(beat, now);
                fires.push_back({ now - pull, beat });
                if (beat == Beat::ThrowOut)
                    throwEnd = now + kThrowWarnMs;
                else if (beat == Beat::LastCall)
                    castEnd = now + kLastCallCastMs;
            }
        }
        return fires;
    }

    std::vector<std::uint64_t> TimesOf(std::vector<Fire> const& fires, Beat beat)
    {
        std::vector<std::uint64_t> out;
        for (Fire const& f : fires)
            if (f.beat == beat)
                out.push_back(f.at);
        return out;
    }

    void TestIds()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211460 && kSpellSlice.last == 211489);
        CHECK(SPELL_PH_MIGHTY_BLOW == 211460);
        CHECK(SPELL_PH_THUNDERCLAP == 211461);
        CHECK(SPELL_PH_FIREBALL_VOLLEY == 211462);
        CHECK(SPELL_PH_GRAB == 211463);
        CHECK(SPELL_PH_THROW_LOOK == 211464);
        CHECK(SPELL_PH_THROW_OUT == 211465);
        CHECK(SPELL_PH_THROWN == 211466);
        CHECK(SPELL_PH_SLAM_LOOK == 211467);
        CHECK(SPELL_PH_LAST_CALL_CAST == 211468);
        CHECK(SPELL_PH_LAST_CALL == 211469);
        CHECK(SPELL_PH_OUTRAGE == 211470);
        CHECK(SPELL_PH_TABLE_SMASH == 211471);
        CHECK(SPELL_PH_TABLE_SPLINTERS == 211472);
        CHECK(kLastSpell == 211472 && kSpellSlice.Contains(kLastSpell));
        // the stock spells he keeps are copies (rule 15): no stock id is in the slice
        for (std::uint32_t stock : { 14099u, 15588u, 15285u })
            CHECK(!kSpellSlice.Contains(stock));

        // his entry, slot and the Rowdy Patron's id (section 3.3)
        CHECK(NPC_PHALANX == 9502);
        CHECK(BOSS_PHALANX == 12);
        CHECK(NPC_BRD_ROWDY_PATRON == 300841);
        CHECK(NPC_BRD_STALKER_WAVE_2 == 300845);
        CHECK(ACTION_PHALANX_START_ACTIVATION == 1);
        CHECK(DATA_PHALANX_ACTIVATED == 44);
        CHECK(DATA_PHALANX == 11);

        // the texts: 0 stock, 1-4 new
        CHECK(SAY_PH_DOOR == 0);
        CHECK(EMOTE_PH_GRAB == 1);
        CHECK(YELL_PH_LAST_CALL == 2);
        CHECK(YELL_PH_PROPERTY_DAMAGE == 3);
        CHECK(YELL_PH_DEATH == 4);

        // the tags are distinct
        std::set<std::uint32_t> const tags{ TAG_PH_THROW_OUT, TAG_PH_LAST_CALL, TAG_PH_THROWN, TAG_PH_SMASH,
            TAG_PH_PARK };
        CHECK(tags.size() == 5);
    }

    void TestNumbers()
    {
        // S4 "Build spec" / "New mechanics" / "Heroic"
        CHECK(kThrowFirstMs == 10000);
        CHECK(kThrowEveryMs(false) == 20000 && kThrowEveryMs(true) == 15000);
        CHECK(kLedgerWindowMs == 10000);
        CHECK(kGrabMs == 1000 && kFlightMs == 1000 && kThrowWarnMs == 2000);
        CHECK(kGrabAuraMs > kGrabMs);       // the hold never runs out before the throw removes it
        CHECK(Near(kThrowMinYd, 15.f) && Near(kThrowMaxYd, 25.f));
        CHECK(Near(kLandingRadiusYd, 6.f));
        CHECK(Near(kThrownPct(false), 15.f) && Near(kThrownPct(true), 25.f));
        CHECK(Near(kLandingPct(false), 30.f) && Near(kLandingPct(true), 45.f));
        CHECK(kLastCallFirstMs == 20000);
        CHECK(kLastCallEveryMs(false) == 30000 && kLastCallEveryMs(true) == 25000);
        CHECK(kLastCallCastMs == 3000);
        CHECK(Near(kLastCallRadiusYd(false), 10.f) && Near(kLastCallRadiusYd(true), 12.f));
        CHECK(Near(kLastCallPct(false), 25.f) && Near(kLastCallPct(true), 40.f));
        CHECK(Near(kSmashPct, 25.f));
        CHECK(kOutragePctPerStack == 15 && kOutrageCap == 5);
        CHECK(kPatronsPerTable == 2);
        CHECK(kPatronHealth(true) == 8000);
        // the stock timers kept
        CHECK(kThunderclapFirstMs == 12000 && kThunderclapEveryMs == 10000);
        CHECK(kMightyBlowFirstMs == 15000 && kMightyBlowEveryMs == 10000);
        CHECK(kVolleyEveryMs == 10000 && Near(kVolleyHealthPct, 51.f));
        CHECK(Near(kThunderclapRadiusYd, 10.f) && Near(kVolleyRadiusYd, 20.f));
        CHECK(kThunderclapSlowPct == -40 && kThunderclapAttackSpeedPct == -34 && kThunderclapMs == 10000);
        // the "stock rescaled" defaults are the BRS convention: tank swing 20-30%, group pulses 10-15%
        CHECK(kMightyBlowPct(false) >= 20.f && kMightyBlowPct(true) <= 30.f);
        CHECK(kThunderclapPct(false) >= 10.f && kThunderclapPct(true) <= 15.f);
        CHECK(kVolleyPct(false) >= 10.f && kVolleyPct(true) <= 15.f);
        CHECK(kMightyBlowPct(true) >= kMightyBlowPct(false));
        CHECK(kThunderclapPct(true) >= kThunderclapPct(false));
        CHECK(kVolleyPct(true) >= kVolleyPct(false));
        // no loss of control over 2 s (the hold is 1 s, removed at the throw)
        CHECK(kGrabMs + kFlightMs <= 2000);
        // the gossip menu is the stock one; the stock path and factions
        CHECK(kGossipMenu == 2283 && kGossipOption == 0);
        CHECK(kPathDoor == 95020);
        CHECK(kFactionAwake == 54 && kFactionPluggerDeath == 14);
        CHECK(kYellDelayMs == 200 && kWalkWatchdogMs == 15000);
    }

    void TestStateMachine()
    {
        using BrdGuzzler::BarModel;

        // Plugger's death is seen through his faction, only while dormant
        CHECK(PluggerDeathSeen(PhalanxState::Dormant, 14));
        CHECK(!PluggerDeathSeen(PhalanxState::Dormant, 35));
        CHECK(!PluggerDeathSeen(PhalanxState::MovingToDoor, 14));
        CHECK(!PluggerDeathSeen(PhalanxState::Active, 14));
        // damage on the walk wakes him (rule 10); not when dormant (friendly) or already active
        CHECK(WakesOnDamage(PhalanxState::MovingToDoor));
        CHECK(!WakesOnDamage(PhalanxState::Dormant));
        CHECK(!WakesOnDamage(PhalanxState::Active));

        // the gossip start is the third source: once, from dormant
        {
            BarModel bar;
            CHECK(bar.RequestPhalanxActivation(PhalanxRequest::Gossip));
            CHECK(bar.phalanx == PhalanxState::MovingToDoor);
            CHECK(bar.phalanxActivated);
            CHECK(!bar.RequestPhalanxActivation(PhalanxRequest::AleRun));    // one walk only
            CHECK(!bar.RequestPhalanxActivation(PhalanxRequest::PluggerDeath));
            bar.PhalanxArrived();
            CHECK(bar.phalanx == PhalanxState::Active);
            CHECK(bar.Door() == BarDoor::Closed);       // the gossip alone never opens the door
            bar.PhalanxDied();
            CHECK(bar.Door() == BarDoor::Open);         // ruling 66: his death opens it
        }
        // the love potion leaves him dormant (the stock quirk), and his gossip still works after it
        {
            BarModel bar;
            CHECK(bar.LovePotion());
            CHECK(bar.phalanx == PhalanxState::Dormant);
            CHECK(bar.Door() == BarDoor::Open);
            CHECK(bar.RequestPhalanxActivation(PhalanxRequest::Gossip));
        }
        // the ale run blasts the door; his death then opens it fully
        {
            BarModel bar;
            bar.AleTurnIn();
            bar.AleTurnIn();
            CHECK(bar.AleTurnIn());
            bar.AleEscortEnds();
            CHECK(bar.phalanx == PhalanxState::MovingToDoor);
            CHECK(bar.Door() == BarDoor::Blasted);
            bar.PhalanxArrived();
            bar.PhalanxDied();
            CHECK(bar.Door() == BarDoor::Open);
        }
        // Plugger's death wakes him
        {
            BarModel bar;
            bar.PluggerDied();
            CHECK(bar.phalanx == PhalanxState::MovingToDoor);
        }
        // a reload: dead wins, then the saved activation, else dormant
        CHECK(BrdGuzzler::PhalanxAfterReload(true, true) == PhalanxState::Dead);
        CHECK(BrdGuzzler::PhalanxAfterReload(true, false) == PhalanxState::Active);
        CHECK(BrdGuzzler::PhalanxAfterReload(false, false) == PhalanxState::Dormant);
        // the door rule is the instance's (Phalanx dead -> Open whatever else)
        CHECK(BarDoorState(false, DungeonKit::State::NotStarted, true) == BarDoor::Open);
        CHECK(BarDoorState(false, DungeonKit::State::Done, true) == BarDoor::Open);
    }

    void TestFloor()
    {
        DungeonKit::Arena const floor = ThrowFloor();
        Arena const leash = ArenaFor(BOSS_PHALANX);

        // Phalanx spawns kPhalanxSpawn, inside his leash arena (not on the throw floor: his corner)
        CHECK(BarUpperArena().Contains(kPhalanxSpawn.XY(), kPhalanxSpawn.z));
        CHECK(leash.Contains(kPhalanxSpawn.XY(), kPhalanxSpawn.z));
        CHECK(!floor.Contains(kPhalanxSpawn.XY(), kBarFloorZ));
        // the door node is his home: inside the leash, outside the throw floor (the door alcove)
        CHECK(Near(kDoorNode.x, 867.295f) && Near(kDoorNode.y, -222.645f));
        CHECK(leash.Contains(kDoorNode.XY(), kDoorNode.z));
        CHECK(!floor.Contains(kDoorNode.XY(), kDoorNode.z));
        // the tank's Spot: on the floor, 5.4 yd from the door node, 9+ yd from every table
        CHECK(floor.Contains(kTankSpot.XY(), kTankSpot.z));
        CHECK(leash.Contains(kTankSpot.XY(), kTankSpot.z));
        CHECK(Near(DungeonKit::Distance(kTankSpot.XY(), kDoorNode.XY()), 5.4f, 0.3f));
        CHECK(MinTableDistance(kTankSpot.XY()) >= 9.f);
        CHECK(kParkRadiusYd < MinTableDistance(kTankSpot.XY()) - kTableRadiusYd - kSmashReachYd);

        // the seven tables: on the floor and in the leash; apart from each other
        for (std::size_t i = 0; i < kTableCount; ++i)
        {
            CHECK(floor.Contains(kTables[i], kBarFloorZ));
            CHECK(leash.Contains(kTables[i], kBarFloorZ));
            for (std::size_t j = i + 1; j < kTableCount; ++j)
                CHECK(DungeonKit::Distance(kTables[i], kTables[j]) > 2.f * kTableRadiusYd);
        }
        // the floor's height band: the lower level (z -49.7) is never it, the floor itself is
        CHECK(floor.Contains({ 870.f, -200.f }, -43.65f));
        CHECK(floor.Contains({ 870.f, -200.f }, -43.0f));
        CHECK(!floor.Contains({ 870.f, -200.f }, -49.7f));
        // the drop's side (the rail and the lower level beyond it), the door alcove, his corner, the north end: off it
        CHECK(!floor.Contains({ 870.f, -175.f }, kBarFloorZ));
        CHECK(!floor.Contains({ 872.f, -230.f }, kBarFloorZ));
        CHECK(!floor.Contains({ 845.f, -210.f }, kBarFloorZ));
        CHECK(!floor.Contains({ 905.f, -195.f }, kBarFloorZ));

        // the fixed landings: on the floor, clear of every table (a landing never goes onto one) and the pillar
        for (Vec2 const& p : kFixedLandings)
        {
            CHECK(floor.Contains(p, kBarFloorZ));
            CHECK(MinTableDistance(p) >= kTableAvoidYd + 2.f);
            CHECK(DungeonKit::Distance(p, kPillar) > kPillarRadiusYd + 3.f);
        }
        // they are spread: no two within 9 yd
        for (std::size_t i = 0; i < kFixedLandings.size(); ++i)
            for (std::size_t j = i + 1; j < kFixedLandings.size(); ++j)
                CHECK(DungeonKit::Distance(kFixedLandings[i], kFixedLandings[j]) >= 9.f);

        // a throw has room: from the floor's middle, 20 yd reaches open floor in several directions
        std::uint32_t open = 0;
        for (int k = 0; k < 16; ++k)
        {
            Vec2 const p = DungeonKit::Advance({ 870.f, -205.f }, float(k) * DungeonKit::kTwoPi / 16.f, 20.f);
            if (floor.Contains(p, kBarFloorZ) && MinTableDistance(p) >= kTableAvoidYd)
                ++open;
        }
        CHECK(open >= 3);
    }

    void TestChairs()
    {
        std::set<std::uint32_t> entries;
        std::array<std::uint32_t, kTableCount> perTable{};
        for (Chair const& c : kChairs)
        {
            entries.insert(c.entry);
            CHECK(c.table < kTableCount);
            // each chair belongs to its nearest table, within 6.5 yd
            CHECK(NearestTable(c.at) == c.table);
            CHECK(DungeonKit::Distance(c.at, kTables[c.table]) <= 6.5f);
            ++perTable[c.table];
        }
        CHECK(entries.size() == kChairs.size());     // one spawn per entry [db]
        // the nearest-table split of the 31 chairs [db]
        CHECK(perTable[0] == 5 && perTable[1] == 8 && perTable[2] == 4 && perTable[3] == 4 && perTable[4] == 2
            && perTable[5] == 3 && perTable[6] == 5);
        std::size_t total = 0;
        for (std::size_t t = 0; t < kTableCount; ++t)
        {
            CHECK(ChairEntriesOf(t).size() == perTable[t]);
            total += ChairEntriesOf(t).size();
        }
        CHECK(total == AllChairEntries().size());
        CHECK(NearestTable(kTables[3]) == 3);
    }

    void TestThrow()
    {
        CHECK(Near(ThrowSpeedXY(20.f), 20.f));
        CHECK(Near(ThrowSpeedXY(15.f), 15.f));
        CHECK(Near(ThrowSpeedXY(25.f), 25.f));
        CHECK(Near(ThrowSpeedXY(3.f), kThrowMinSpeedXY));
        // the flight takes kFlightMs over the throw's range
        CHECK(Near(15.f / ThrowSpeedXY(15.f) * 1000.f, float(kFlightMs), 1.f));
        CHECK(Near(25.f / ThrowSpeedXY(25.f) * 1000.f, float(kFlightMs), 1.f));
        // never his victim, never the last one thrown, only on the floor
        CHECK(ThrowEligible(false, false, true));
        CHECK(!ThrowEligible(true, false, true));
        CHECK(!ThrowEligible(false, true, true));
        CHECK(!ThrowEligible(false, false, false));
    }

    void TestTimeline()
    {
        for (bool heroic : { false, true })
        {
            std::vector<Fire> const fires = Run(heroic, 300000, 150000);
            std::vector<std::uint64_t> const throws = TimesOf(fires, Beat::ThrowOut);
            std::vector<std::uint64_t> const calls = TimesOf(fires, Beat::LastCall);
            std::vector<std::uint64_t> const claps = TimesOf(fires, Beat::Thunderclap);
            std::vector<std::uint64_t> const blows = TimesOf(fires, Beat::MightyBlow);
            std::vector<std::uint64_t> const volleys = TimesOf(fires, Beat::Volley);

            // the first beats
            CHECK(!throws.empty() && throws.front() == 10000);
            CHECK(!calls.empty() && calls.front() == 20000);
            CHECK(!claps.empty() && claps.front() == 12000);
            CHECK(!blows.empty() && blows.front() == 15000);
            // the Volley waits for 50%, then fires at once and every 10 s (or a little later, after a bar)
            CHECK(!volleys.empty() && volleys.front() >= 150000 && volleys.front() <= 153000);
            for (std::size_t i = 1; i < volleys.size(); ++i)
                CHECK(volleys[i] - volleys[i - 1] >= kVolleyEveryMs && volleys[i] - volleys[i - 1] <= 13000);

            // a throw and Last Call never at once
            for (std::uint64_t c : calls)
                for (std::uint64_t t : throws)
                {
                    CHECK(!(t >= c && t < c + kLastCallCastMs));
                    CHECK(!(c >= t && c < t + kThrowWarnMs));
                }
            // nothing else starts during Last Call's bar
            for (std::uint64_t c : calls)
                for (Fire const& f : fires)
                    if (f.beat != Beat::LastCall)
                        CHECK(!(f.at > c && f.at < c + kLastCallCastMs));

            // the cadences: each gap at least the spec's, never more than a bar and a retry later
            std::uint32_t const throwEvery = kThrowEveryMs(heroic);
            for (std::size_t i = 1; i < throws.size(); ++i)
                CHECK(throws[i] - throws[i - 1] >= throwEvery && throws[i] - throws[i - 1] <= throwEvery + 3500);
            std::uint32_t const callEvery = kLastCallEveryMs(heroic);
            for (std::size_t i = 1; i < calls.size(); ++i)
                CHECK(calls[i] - calls[i - 1] >= callEvery && calls[i] - calls[i - 1] <= callEvery + 2500);
            // counts over 300 s
            CHECK(throws.size() >= (heroic ? 18u : 13u) && throws.size() <= (heroic ? 20u : 15u));
            CHECK(calls.size() >= (heroic ? 11u : 9u) && calls.size() <= (heroic ? 12u : 10u));
        }
        // ArmVolley once
        Timeline t;
        t.Start(false, 100);
        CHECK(t.At(Beat::Volley) == 0);
        CHECK(!t.Due(Beat::Volley, 1000000));
        CHECK(t.ArmVolley(5000));
        CHECK(!t.ArmVolley(6000));
        CHECK(t.Due(Beat::Volley, 5000));
        // MayStart
        CHECK(!MayStart(Beat::ThrowOut, true, false));
        CHECK(!MayStart(Beat::ThrowOut, false, true));
        CHECK(!MayStart(Beat::LastCall, true, false));
        CHECK(MayStart(Beat::Thunderclap, true, false));
        CHECK(!MayStart(Beat::Thunderclap, false, true));
        CHECK(MayStart(Beat::MightyBlow, false, false));
    }

    void TestPropertyDamage()
    {
        TableState tables;
        float const reach = kTableRadiusYd + kSmashReachYd;
        // within reach of T2's spot: T2
        Vec2 const t2 = kTables[1];
        CHECK(SmashedTable({ t2.x + reach - 0.1f, t2.y }, kBarFloorZ, tables) == std::optional<std::size_t>(1));
        CHECK(SmashedTable(t2, kBarFloorZ + 2.f, tables) == std::optional<std::size_t>(1));     // in the air
        // out of reach, or on the lower level: none
        CHECK(!SmashedTable({ t2.x + reach + 0.2f, t2.y }, kBarFloorZ, tables));
        CHECK(!SmashedTable(t2, -49.7f, tables));
        // the nearest of two in reach (T3 and T4 are 6.1 yd apart: a point between them nearer T4)
        Vec2 const between{ 887.5f, -207.5f };
        CHECK(SmashedTable(between, kBarFloorZ, tables) == std::optional<std::size_t>(3));
        // each table breaks once
        tables.Break(1);
        CHECK(tables.Broken(1) && tables.Count() == 1);
        CHECK(!SmashedTable(t2, kBarFloorZ, tables));
        tables.Break(1);
        CHECK(tables.Count() == 1);
        tables.Break(3);
        CHECK(SmashedTable(between, kBarFloorZ, tables) == std::optional<std::size_t>(2));
        for (std::size_t i = 0; i < kTableCount; ++i)
            tables.Break(i);
        CHECK(tables.Count() == kTableCount);
        tables.Break(9);
        CHECK(tables.Count() == kTableCount);
        // the tank's Spot and the fixed landings never smash a table
        TableState none;
        CHECK(!SmashedTable(kTankSpot.XY(), kTankSpot.z, none));
        for (Vec2 const& p : kFixedLandings)
            CHECK(!SmashedTable(p, kBarFloorZ, none));

        // the knock window
        CHECK(!KnockWatched(1100, 1000));
        CHECK(KnockWatched(1000 + kSmashGraceMs, 1000));
        CHECK(KnockWatched(1000 + kSmashWindowMs, 1000));
        CHECK(!KnockWatched(1000 + kSmashWindowMs + 1, 1000));
        CHECK(KnockExpired(1000 + kSmashWindowMs + 1, 1000));
        CHECK(!KnockExpired(1000 + kSmashWindowMs, 1000));

        // Outrage: +15% a stack, 5 at most
        CHECK(Near(OutrageScale(0), 1.f));
        CHECK(Near(OutrageScale(1), 1.15f));
        CHECK(Near(OutrageScale(5), 1.75f));
        CHECK(Near(OutrageScale(7), 1.75f));

        // the patrons appear at the table, two of them, on the floor
        for (std::size_t t = 0; t < kTableCount; ++t)
        {
            std::array<Vec2, kPatronsPerTable> const spots = PatronSpots(t);
            for (Vec2 const& p : spots)
            {
                CHECK(DungeonKit::Distance(p, kTables[t]) <= reach);
                CHECK(BarUpperArena().Contains(p, kBarFloorZ));
            }
            CHECK(DungeonKit::Distance(spots[0], spots[1]) > 1.f);
        }
    }
}

int main()
{
    TestIds();
    TestNumbers();
    TestStateMachine();
    TestFloor();
    TestChairs();
    TestThrow();
    TestTimeline();
    TestPropertyDamage();
    return Report("brd_phalanx_test");
}
