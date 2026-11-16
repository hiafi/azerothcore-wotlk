// Host tests for VooneLogic.h (B3: War Master Voone). The slice and arena checks are WP-S0's; the rest is WP-B3's:
// the spells, the stance clock and the throw beat, the counts and the cap, the stuck axes' book and a long simulation
// of it, the lanes' geometry (and their parity with the G1 follow-up drill's lines), Berserking, the hold and the
// arena.
#include "VooneLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <optional>
#include <set>
#include <vector>

using namespace BlackrockSpireRework;
using namespace BrsVoone;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210090 && kSpellSlice.last == 210119);

        std::set<std::uint32_t> ids;
        for (std::uint32_t id : { SPELL_VO_AXE_THROW, SPELL_VO_AXE_FAN, SPELL_VO_AXE_RAIN, SPELL_VO_RECALL_HIT,
            SPELL_VO_CHAIN_HIT, SPELL_VO_AXE_FLIGHT, SPELL_VO_AXE_RETURN, SPELL_VO_CHAINED_AXE, SPELL_VO_WAR_CRY,
            SPELL_VO_BERSERKING, SPELL_VO_CHARGE, SPELL_VO_RECALL_BAR })
        {
            CHECK(id >= kSpellSlice.first && id <= kSpellSlice.last);
            ids.insert(id);
        }
        CHECK(ids.size() == 12);
        // The stock spells that stay are stock ids, outside the custom block.
        CHECK(SPELL_VO_THRASH == 3391 && SPELL_VO_CLEAVE == 15284 && SPELL_VO_MORTAL_STRIKE == 16856);

        // Boss, anchor and axe ids of the shared header (S0's table).
        CHECK(NPC_VOONE == 9237 && NPC_BRS_CHAIN_ANCHOR == 300704 && GO_BRS_STUCK_AXE == 301250);
        CHECK(BossOfEntry(NPC_VOONE) == BOSS_VOONE && BOSS_VOONE == 2);

        // creature_text groups 0 to 5 (the text range of the shared header: 9237 0-5, no stock group).
        CHECK(YELL_VOONE_PULL == 0 && YELL_VOONE_DEATH == 5 && EMOTE_VOONE_RECALL == 4);
        CHECK(YELL_VOONE_BRAWLER == 1 && YELL_VOONE_THRASHER == 2 && YELL_VOONE_WAR_MASTER == 3);
        bool found = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_VOONE)
            {
                found = true;
                CHECK(range.first == 0 && range.last == YELL_VOONE_DEATH && range.firstNew == 0);
            }
        CHECK(found);

        // The tags are the build spec's mechanic numbers.
        CHECK(TAG_VO_AXE_THROW == 3 && TAG_VO_AXE_FAN == 4 && TAG_VO_RECALL == 7);
        CHECK(TAG_VO_CHAINS == 11);
        // Rain is off 5 (the G1 drill's chain tag, R-1-A n2); every tag is distinct.
        std::array<std::uint32_t, 8> const tags{ TAG_VO_AXE_THROW, TAG_VO_AXE_FAN, TAG_VO_AXE_RAIN, TAG_VO_RECALL,
            TAG_VO_CLEAVE, TAG_VO_CHAINS, TAG_VO_PARK, TAG_VO_HOLD_THROW };
        CHECK(TAG_VO_AXE_RAIN != 5);
        for (std::size_t i = 0; i < tags.size(); ++i)
            for (std::size_t j = i + 1; j < tags.size(); ++j)
                CHECK(tags[i] != tags[j]);
    }

    void TestArena()
    {
        // He spawns kVooneSpawn, inside his arena.
        CHECK(VooneArena().Contains(kVooneSpawn.XY(), kVooneSpawn.z));
        CHECK(ArenaFor(BOSS_VOONE).Contains(kVooneSpawn.XY(), kVooneSpawn.z));

        // The fight's leash adds the walk from his gate to the hall: every point of the walk is inside it.
        DungeonKit::Arena const arena = FightArena();
        CHECK(arena.Contains(kVooneSpawn.XY(), kVooneSpawn.z));
        CHECK(arena.Contains(kVooneChargeSpot.XY(), kVooneChargeSpot.z));
        CHECK(arena.Contains(kVooneGate.XY(), kVooneGate.z));
        CHECK(arena.Contains({ -45.f, -450.f }, -18.6f));       // out of the gate, south
        CHECK(arena.Contains({ -58.f, -466.f }, -18.6f));       // around to the hall's west edge
        CHECK(arena.Contains({ -50.f, -480.f }, -18.6f));       // the hall
        // ... but not the Firebrand camp (north, the pit's other half), nor the floor above.
        CHECK(!arena.Contains({ -20.f, -420.f }, -18.6f));
        CHECK(!arena.Contains(kVooneSpawn.XY(), 31.8f));
        // His own arena did not hold the route (the shared leash would have evaded him on the walk).
        CHECK(!VooneArena().Contains({ -45.f, -450.f }, -18.6f));

        // The charge spot is about 24 yd from his spawn (SP: about 25 yd; the NM report's 23.6 is from its own centre).
        CHECK(Near(DungeonKit::Distance(kVooneSpawn.XY(), kVooneChargeSpot.XY()), 23.9f, 0.5f));
        CHECK(arena.RayToEdge(kVooneChargeSpot.XY(), kVooneChargeSpot.z, 0.f).value_or(0.f) > 9.f);
    }

    void TestStanceCycle()
    {
        CHECK(NextStance(0) == 1 && NextStance(1) == 2 && NextStance(2) == 0);
        CHECK(kStanceMs(false) == 30000 && kStanceMs(true) == 25000);
        CHECK(std::string(StanceName(Stance::Brawler)) == "brawler");
        CHECK(std::string(StanceName(Stance::WarMaster)) == "war-master");

        for (bool heroic : { false, true })
        {
            StanceClock clock;
            clock.Start(1000, heroic);
            std::uint32_t const len = kStanceMs(heroic);
            CHECK(clock.Current() == Stance::Brawler && clock.StartMs() == 1000 && clock.EndMs() == 1000 + len);
            CHECK(!clock.Advance(1000 + len - 1));
            CHECK(clock.Advance(1000 + len));
            CHECK(clock.Current() == Stance::Thrasher && clock.StartMs() == 1000 + len && clock.Changes() == 1);
            CHECK(!clock.Advance(1000 + len + 5));
            CHECK(clock.Advance(1000 + 2 * len));
            CHECK(clock.Current() == Stance::WarMaster);
            CHECK(clock.Advance(1000 + 3 * len));
            CHECK(clock.Current() == Stance::Brawler && clock.Changes() == 3);
            // A tick that is late by more than a stance stays on the grid and reports one change.
            CHECK(clock.Advance(1000 + 5 * len + 10));
            CHECK(clock.Current() == Stance::WarMaster && clock.StartMs() == 1000 + 5 * len);
        }
    }

    void TestThrowBeat()
    {
        // Normal, 30 s: the first throw 3 s in, then every 6 / 10 / 8 s while the throw lands (2 s) inside the stance.
        StanceClock normal;
        normal.Start(0, false);
        CHECK(normal.ThrowsPerStance(Stance::Brawler) == 5);        // 3 9 15 21 27
        CHECK(normal.ThrowsPerStance(Stance::Thrasher) == 3);       // 3 13 23
        CHECK(normal.ThrowsPerStance(Stance::WarMaster) == 4);      // 3 11 19 27
        StanceClock heroic;
        heroic.Start(0, true);
        CHECK(heroic.ThrowsPerStance(Stance::Brawler) == 4);        // 3 9 15 21 (27 would land at 29 > 25)
        CHECK(heroic.ThrowsPerStance(Stance::Thrasher) == 3);       // 3 13 23 (lands at 25 = the change)
        CHECK(heroic.ThrowsPerStance(Stance::WarMaster) == 3);      // 3 11 19

        // The live clock fires exactly those.
        std::vector<std::uint64_t> fired;
        StanceClock clock;
        clock.Start(0, false);
        for (std::uint64_t t = 0; t <= 29900; t += 100)
        {
            clock.Advance(t);
            if (clock.ThrowDue(t))
            {
                fired.push_back(t);
                clock.ThrowFired();
            }
        }
        CHECK((fired == std::vector<std::uint64_t>{ 3000, 9000, 15000, 21000, 27000 }));

        // Nothing is thrown before 3 s into a new stance, and the beat re-arms with the stance.
        CHECK(!clock.ThrowDue(30000));
        CHECK(clock.Advance(30000));
        CHECK(clock.NextThrowMs() == 33000);
        CHECK(!clock.ThrowDue(32900) && clock.ThrowDue(33000));
        CHECK(ThrowEveryMs(Stance::Brawler) == 6000 && ThrowEveryMs(Stance::Thrasher) == 10000
            && ThrowEveryMs(Stance::WarMaster) == 8000);
        CHECK(kThrowFirstMs == 3000 && kThrowWarnMs == 2000);
    }

    void TestCounts()
    {
        // 5 players / 6 or more (the flex pairs of the build spec).
        CHECK(kThrowLanes.At(5) == 1 && kThrowLanes.At(6) == 2 && kThrowLanes.At(10) == 2);
        CHECK(kFanCount.At(5) == 1 && kFanCount.At(6) == 2);
        CHECK(kRainCount.At(5) == 2 && kRainCount.At(6) == 4 && kRainCount.At(10) == 4);
        CHECK(kRainCount.At(0) == 2);       // not held reads as 5
        CHECK(AxesPerThrow(Stance::Brawler, 5) == 1 && AxesPerThrow(Stance::Brawler, 10) == 2);
        CHECK(AxesPerThrow(Stance::Thrasher, 5) == 3 && AxesPerThrow(Stance::Thrasher, 10) == 6);
        CHECK(AxesPerThrow(Stance::WarMaster, 5) == 2 && AxesPerThrow(Stance::WarMaster, 10) == 4);
        // VO6: the cap, normal 6 / 8, heroic 8 / 10.
        CHECK(StuckCap(false, 5) == 6 && StuckCap(false, 6) == 8 && StuckCap(false, 10) == 8);
        CHECK(StuckCap(true, 5) == 8 && StuckCap(true, 6) == 10 && StuckCap(true, 10) == 10);
        // One throw always fits under the cap (the cap can always make room).
        for (std::uint32_t n : { 5u, 6u, 10u })
            for (bool heroic : { false, true })
                for (Stance s : { Stance::Brawler, Stance::Thrasher, Stance::WarMaster })
                    CHECK(AxesPerThrow(s, n) <= StuckCap(heroic, n));

        // Damage: 30% normal, 40% heroic; the chain 10%.
        CHECK(kAxePct(false) == 30.f && kAxePct(true) == 40.f && kRecallPct(false) == 30.f && kRecallPct(true) == 40.f);
        CHECK(kChainPct == 10.f);
    }

    void TestCapRecalls()
    {
        CHECK(CapRecalls(0, 0, 1, 6) == 0);
        CHECK(CapRecalls(5, 0, 1, 6) == 0);         // lands on the cap exactly
        CHECK(CapRecalls(6, 0, 1, 6) == 1);         // one more would land: the oldest goes
        CHECK(CapRecalls(6, 0, 3, 6) == 3);
        CHECK(CapRecalls(4, 2, 1, 6) == 1);         // the throws in flight count
        CHECK(CapRecalls(2, 6, 3, 6) == 2);         // only axes still stuck can be sent
        CHECK(CapRecalls(0, 6, 3, 6) == 0);
        CHECK(CapRecalls(8, 0, 6, 8) == 6);         // a full fan at 10 players over a full floor
    }

    void TestAxeBook()
    {
        AxeBook book;
        CHECK(book.Count() == 0 && book.StuckCount() == 0 && book.StuckIds().empty());
        std::uint32_t const a = book.Add({ 1.f, 2.f }, -18.6f, 100);
        std::uint32_t const b = book.Add({ 3.f, 4.f }, -18.6f, 200);
        std::uint32_t const c = book.Add({ 5.f, 6.f }, -18.6f, 300);
        CHECK(a != b && b != c && a != 0);
        CHECK(book.Count() == 3 && book.StuckCount() == 3);
        CHECK((book.StuckIds() == std::vector<std::uint32_t>{ a, b, c }));      // the oldest first
        CHECK(book.Find(b) && book.Find(b)->landedMs == 200 && Near(book.Find(b)->at.y, 4.f));
        CHECK(!book.Find(999));

        // Sending an axe home takes it off the stuck list at once; it is gone when its lane arrives.
        CHECK(book.MarkRecall(a, 2100));
        CHECK(!book.MarkRecall(a, 2200));           // not twice
        CHECK(!book.MarkRecall(999, 1));
        CHECK(book.StuckCount() == 2 && book.Count() == 3);
        CHECK((book.StuckIds() == std::vector<std::uint32_t>{ b, c }));
        CHECK(book.TakeArrived(2099).empty());
        std::vector<StuckAxe> const arrived = book.TakeArrived(2100);
        CHECK(arrived.size() == 1 && arrived[0].id == a);
        CHECK(book.Count() == 2 && !book.Find(a));
        // A stuck axe never "arrives".
        CHECK(book.TakeArrived(999999).empty());
        book.Clear();
        CHECK(book.Count() == 0);
        // Ids keep counting after a clear (a late lane of an old pull never matches a new axe).
        CHECK(book.Add({ 0.f, 0.f }, 0.f, 1) > c);
    }

    // A fight of the stance clock, the throws, the cap and the Recall at every stance change, 100 ms steps: the floor
    // (stuck axes plus throws in flight) never passes the cap, every stance change empties the floor 3 s later, and
    // an axe is never sent home twice.
    void TestFightSimulation()
    {
        for (bool heroic : { false, true })
        {
            for (std::uint32_t players : { 5u, 6u, 8u, 10u })
            {
                std::uint32_t const cap = StuckCap(heroic, players);
                StanceClock clock;
                AxeBook book;
                std::vector<std::uint64_t> pending;
                clock.Start(0, heroic);
                std::uint32_t maxFloor = 0;
                std::uint32_t capRecalls = 0;
                std::uint32_t stanceRecalls = 0;
                bool floorEmptyAfterRecall = true;
                std::uint64_t recallDone = 0;
                for (std::uint64_t t = 0; t <= 400000; t += 100)
                {
                    // arrivals and landings
                    book.TakeArrived(t);
                    for (auto it = pending.begin(); it != pending.end();)
                    {
                        if (t >= *it)
                        {
                            book.Add({ 0.f, 0.f }, 0.f, t);
                            it = pending.erase(it);
                        }
                        else
                            ++it;
                    }
                    if (recallDone && t == recallDone + 100)
                    {
                        // Only axes that landed during the warning may remain.
                        for (StuckAxe const& axe : book.All())
                            if (axe.landedMs < recallDone - kRecallWarnMs)
                                floorEmptyAfterRecall = false;
                        recallDone = 0;
                    }

                    if (clock.Advance(t))
                    {
                        std::vector<std::uint32_t> const ids = book.StuckIds();
                        for (std::uint32_t id : ids)
                            CHECK(book.MarkRecall(id, t + kRecallWarnMs));
                        stanceRecalls += static_cast<std::uint32_t>(ids.size());
                        recallDone = t + kRecallWarnMs;
                    }
                    if (clock.ThrowDue(t))
                    {
                        std::uint32_t const incoming = AxesPerThrow(clock.Current(), players);
                        std::uint32_t const n = CapRecalls(book.StuckCount(),
                            static_cast<std::uint32_t>(pending.size()), incoming, cap);
                        std::vector<std::uint32_t> ids = book.StuckIds();
                        for (std::uint32_t i = 0; i < n; ++i)
                            CHECK(book.MarkRecall(ids[i], t + kCapRecallWarnMs));
                        capRecalls += n;
                        for (std::uint32_t i = 0; i < incoming; ++i)
                            pending.push_back(t + kThrowWarnMs);
                        clock.ThrowFired();
                    }
                    std::uint32_t const floor = book.StuckCount() + static_cast<std::uint32_t>(pending.size());
                    maxFloor = std::max(maxFloor, floor);
                }
                CHECK(maxFloor <= cap);
                CHECK(maxFloor >= AxesPerThrow(Stance::WarMaster, players));    // the fight does use the floor
                CHECK(stanceRecalls > 0);
                CHECK(floorEmptyAfterRecall);
                // Thrasher's fans (9 axes at 5 players, 3 fans) outrun the normal cap of 6: the cap works there.
                if (!heroic && players == 5)
                    CHECK(capRecalls > 0);
            }
        }
    }

    void TestGeometry()
    {
        // Facings: toward the aim point, or the fallback when he stands on it.
        CHECK(Near(LaneFacing({ 0.f, 0.f }, { 10.f, 0.f }, 1.f), 0.f));
        CHECK(Near(LaneFacing({ 0.f, 0.f }, { 0.f, 10.f }, 1.f), DungeonKit::kPi / 2.f));
        CHECK(Near(LaneFacing({ 5.f, 5.f }, { 5.2f, 5.1f }, 1.25f), 1.25f));

        // The fan: three lanes 30 degrees apart, the middle one on the base.
        std::array<float, 3> const fan = FanFacings(1.0f);
        float const step = 30.f * DungeonKit::kPi / 180.f;
        CHECK(Near(fan[1], 1.0f) && Near(fan[0], 1.0f - step) && Near(fan[2], 1.0f + step));
        std::array<float, 3> const wrap = FanFacings(0.1f);     // wraps below zero
        CHECK(wrap[0] >= 0.f && wrap[0] < DungeonKit::kTwoPi && Near(wrap[0], DungeonKit::kTwoPi + 0.1f - step));
        CHECK(Near(NormalizeFacing(-0.5f), DungeonKit::kTwoPi - 0.5f));
        CHECK(Near(NormalizeFacing(DungeonKit::kTwoPi + 0.25f), 0.25f));

        // Lane length: 30 yd, cut 1 yd inside an edge, never under 6.
        CHECK(LaneLength(std::nullopt) == 30.f);
        CHECK(LaneLength(60.f) == 30.f);
        CHECK(Near(LaneLength(20.f), 19.f));
        CHECK(LaneLength(3.f) == kMinLaneYd);
        CHECK(kLaneWidth == 4.f && kLaneLength == 30.f && kRainRadius == 4.f && kFanSpreadDeg == 30.f);

        // A lane from the charge spot along the hall stays on the hall region of the arena.
        DungeonKit::Arena const arena = FightArena();
        for (int deg = 0; deg < 360; deg += 15)
        {
            float const facing = DungeonKit::kPi * static_cast<float>(deg) / 180.f;
            float const length = LaneLength(arena.RayToEdge(kVooneChargeSpot.XY(), kVooneChargeSpot.z, facing));
            CHECK(length >= kMinLaneYd && length <= kLaneLength);
            Vec2 const end = DungeonKit::Advance(kVooneChargeSpot.XY(), facing, length);
            if (length < kLaneLength)
                CHECK(arena.Contains(end, kVooneChargeSpot.z));
        }
    }

    // The G1 drill (blackrock-spire-followups, STAGE-G1-REPORT) models these lines: the numbers must not drift.
    void TestDrillParity()
    {
        // Tag 7, VO12 War Cry -> VO7 recall: `line 5 1500 width=4 exclude=5 ... pct=40 weak=1`.
        CHECK(kEarlyRecallWarnMs == 1500 && kRecallWidth == 4.f && kRecallExcludeSourceEnd == 5.f);
        CHECK(kRecallPct(true) == 40.f);
        CHECK(TAG_VO_RECALL == 7);
        // Tag 5, VO11 chains: `line 5 2000 width=2 ... persist tick=2000 pct=10 weak=1`.
        CHECK(kChainWidth == 2.f && kChainTickMs == 2000 && kChainWarnMs == 2000 && kChainPct == 10.f);
        // The recall lane is wider than the chain, and a lane stops short of him (the 5 yd at his side are safe).
        CHECK(kRecallWidth > kChainWidth);
        // The warnings: 3 s at a stance change, 2 s for the cap's one lane, 1.5 s after a landed War Cry.
        CHECK(kRecallWarnMs == 3000 && kCapRecallWarnMs == 2000);
        // The missile looks arrive with their warnings (30 yd lane).
        CHECK(Near(kLaneLength / kThrowMissileSpeed * 1000.f, static_cast<float>(kThrowWarnMs), 1.f));
        CHECK(Near(kLaneLength / kReturnMissileSpeed * 1000.f, static_cast<float>(kRecallWarnMs), 1.f));
    }

    void TestStockBeats()
    {
        // The stock phase offsets (Thrash 3 s / 10 s; Mortal Strike 12 s / 10 s; Cleave 14 s / 12 s).
        CHECK(kThrashBeat.first == 3000 && kThrashBeat.every == 10000);
        CHECK(kMortalStrikeBeat.first == 12000 && kMortalStrikeBeat.every == 10000);
        CHECK(kCleaveBeat.first == 14000 && kCleaveBeat.every == 12000);
        BeatClock beat;
        CHECK(!beat.Due(1000000));          // unarmed: never
        beat.Arm(5000);
        CHECK(!beat.Due(4999) && beat.Due(5000));
        beat.Fired(5100, 10000);
        CHECK(beat.DueMs() == 15100 && !beat.Due(15099) && beat.Due(15100));
        beat.Disarm();
        CHECK(!beat.Due(1000000));
        // Every stock cast of the stance fits the stance.
        CHECK(kCleaveBeat.first + kCleaveWarnMs < kStanceMs(true));
        CHECK(kCleaveConeDeg > 0.f && kCleaveConeYd > 0.f);
    }

    void TestBerserk()
    {
        BerserkClock b;
        CHECK(!b.Active(0) && b.RemainingMs(0) == 0 && b.Until() == 0);
        // War Master's stance: until the stance ends.
        b.SetStance(30000);
        CHECK(b.Active(1000) && b.RemainingMs(1000) == 29000);
        // A War Cry landing in another stance: 10 s; in War Master, it does not shorten the stance's share.
        b.SetCry(5000 + kWarCryBerserkMs);
        CHECK(b.Until() == 30000);
        b.ClearStance();
        CHECK(b.Until() == 15000 && b.RemainingMs(5000) == 10000);
        CHECK(!b.Active(15000));
        // Two cries: the later one wins.
        b.SetCry(40000);
        b.SetCry(20000);
        CHECK(b.Until() == 40000);
        b.Clear();
        CHECK(b.Until() == 0);
        CHECK(kBerserkingPct == 30 && kWarCryBerserkMs == 10000);
    }

    void TestWarCry()
    {
        CHECK(kWarCryFirstMs == 15000 && kWarCryEveryMs == 25000 && kWarCryCastMs == 2500);
        CHECK(kWarCryKickPriority == 3);
        // The first cry falls inside the first heroic stance, and the cry never overlaps a stance change's Recall cast.
        CHECK(kWarCryFirstMs + kWarCryCastMs < kStanceMs(true));
        for (std::uint64_t k = 0; k < 20; ++k)
        {
            std::uint64_t const cry = kWarCryFirstMs + k * kWarCryEveryMs;
            std::uint64_t const change = (k + 1) * kStanceMs(true);
            // Cries land 15 s into each 25 s stance: well clear of the change (the Recall cast bar).
            CHECK(cry + kWarCryCastMs + 1000 < change || cry > change + kRecallWarnMs);
        }
    }

    void TestHold()
    {
        CHECK(!HoldReleased(97.f, 0));
        CHECK(!HoldReleased(30.f, 20000));
        CHECK(HoldReleased(kHoldReleaseYd, 1000));
        CHECK(HoldReleased(5.f, 0));
        CHECK(HoldReleased(97.f, kHoldMaxMs));
        // The walk takes about 14 s at run speed (97 yd at 7 yd/s): well inside the cap.
        CHECK(kHoldMaxMs > 4u * static_cast<std::uint32_t>(97.f / 7.f * 1000.f));
        CHECK(kChargeLandMs < kHoldMaxMs);

        // R-1 ruling 1: damage from beyond 12 yd while he holds is answered; from inside it the hold ends anyway.
        CHECK(!HoldThrowAnswers(kHoldReleaseYd));
        CHECK(!HoldThrowAnswers(5.f));
        CHECK(HoldThrowAnswers(kHoldReleaseYd + 0.1f));
        CHECK(HoldThrowAnswers(40.f));
        // One axe per attacker every 2 s.
        CHECK(HoldThrowReady(0, std::nullopt));
        CHECK(!HoldThrowReady(1000, std::optional<std::uint64_t>(0)));
        CHECK(!HoldThrowReady(1999, std::optional<std::uint64_t>(0)));
        CHECK(HoldThrowReady(kHoldThrowEveryMs, std::optional<std::uint64_t>(0)));
        // The hit lands with the flight look (15 yd/s), capped at 3 s.
        CHECK(kHoldThrowFlightYdPerSec == kThrowMissileSpeed);
        CHECK(HoldThrowFlightMs(30.f) == 2000);
        CHECK(HoldThrowFlightMs(0.f) == 0);
        CHECK(HoldThrowFlightMs(100.f) == kHoldThrowMaxFlightMs);
        // Survivable as plain single-target damage: no Weakened, below one lane throw, and a healer has 2 s between.
        CHECK(kHoldThrowPct(false) == 20.f && kHoldThrowPct(true) == 25.f);
        CHECK(kHoldThrowPct(false) < kAxePct(false) && kHoldThrowPct(true) < kAxePct(true));
        // Uninterrupted for the whole walk (about 14 s): 6 axes, 120% / 150% unhealed: the group walks in instead.
        std::uint32_t const axes = static_cast<std::uint32_t>(97.f / 7.f * 1000.f) / kHoldThrowEveryMs;
        CHECK(axes == 6);
    }
}

int main()
{
    TestSlice();
    TestArena();
    TestStanceCycle();
    TestThrowBeat();
    TestCounts();
    TestCapRecalls();
    TestAxeBook();
    TestFightSimulation();
    TestGeometry();
    TestDrillParity();
    TestStockBeats();
    TestBerserk();
    TestWarCry();
    TestHold();

    return Report("brs_voone_test");
}
