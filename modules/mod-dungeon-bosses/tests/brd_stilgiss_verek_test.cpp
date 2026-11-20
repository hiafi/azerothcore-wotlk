// Host tests for StilgissVerekLogic.h (D8: Warder Stilgiss and Verek): the ids and texts, the build spec numbers (SP
// 353-407), the coffer engine (no repeats till five, caps 2 / 3, the oldest dropped), the rim (the twelve doors and
// where he stands), the Wand's chords, the Bindings and Black Blood rules and Verek's two beats.
#include "StilgissVerekLogic.h"
#include "DungeonKitFlow.h"
#include "check.h"
#include <array>
#include <cmath>
#include <set>

using namespace BlackrockDepthsRework;
using namespace BrdStilgissVerek;

namespace
{
    void TestIdsAndTexts()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211050 && kSpellSlice.last == 211089);
        CHECK(SPELL_SV_OPEN_COFFER == 211050);
        CHECK(SPELL_SV_CURSE_OF_BLOOD == 211064);
        CHECK(kSpellSlice.Contains(SPELL_SV_CURSE_OF_BLOOD));
        CHECK(SPELL_SV_BINDINGS_TICK == SPELL_SV_BINDINGS + 1 && SPELL_SV_BINDINGS_CHAIN == SPELL_SV_BINDINGS + 2);
        CHECK(SPELL_SV_FROSTBOLT == 211063);
        CHECK(SPELL_SV_BLOOD_LOOK == 211065 && kSpellSlice.Contains(SPELL_SV_BLOOD_LOOK));
        // The creature texts of 9041 are groups 0-6 (all new), Verek's group 0 is stock.
        CHECK(YELL_ST_PULL == 0 && EMOTE_ST_EYE == 1 && EMOTE_ST_BLOOD == 5 && YELL_ST_DEATH == 6);
        CHECK(EMOTE_VK_ENRAGE == 0);
        bool stilgiss = false;
        bool verek = false;
        for (TextRange const& range : kTextRanges)
        {
            if (range.entry == NPC_STILGISS)
            {
                stilgiss = true;
                CHECK(range.first == 0 && range.last == YELL_ST_DEATH && range.firstNew == 0);
            }
            if (range.entry == NPC_VEREK)
            {
                verek = true;
                CHECK(range.first == 0 && range.last == EMOTE_VK_ENRAGE && range.firstNew == 1);
            }
        }
        CHECK(stilgiss && verek);
        // Each artifact's emote is the line of its draw.
        CHECK(EmoteOf(Artifact::Eye) == 1 && EmoteOf(Artifact::Bindings) == 2 && EmoteOf(Artifact::Magma) == 3);
        CHECK(EmoteOf(Artifact::Wand) == 4 && EmoteOf(Artifact::BlackBlood) == 5);
        // The stock spells kept.
        CHECK(SPELL_STOCK_FROST_ARMOR == 12544 && SPELL_STOCK_ENRAGE == 8599);
        // Slot 6 holds both: the spawn points of both sit in the arena, as does every stand point.
        CHECK(BOSS_STILGISS_VEREK == 6);
        CHECK(NPC_STILGISS == 9041 && NPC_VEREK == 9042);
        CHECK(ArenaFor(BOSS_STILGISS_VEREK).Contains(kStilgissSpawn.XY(), kStilgissSpawn.z));
        CHECK(ArenaFor(BOSS_STILGISS_VEREK).Contains(kVerekSpawn.XY(), kVerekSpawn.z));
        CHECK(BlackVaultArena().Contains(kStilgissSpawn.XY(), kStilgissSpawn.z));
        CHECK(BlackVaultArena().Contains(kVerekSpawn.XY(), kVerekSpawn.z));
    }

    void TestSpecNumbers()
    {
        // SV1: 8 s, then 25 s (heroic 20 s); 2 active (heroic 3); 2 s to open; an artifact's first use 3 s after.
        CHECK(kCofferFirstMs == 8000);
        CHECK(kCofferEveryMs.Get(false) == 25000 && kCofferEveryMs.Get(true) == 20000);
        CHECK(kMaxActive.Get(false) == 2 && kMaxActive.Get(true) == 3);
        CHECK(kOpenMs == 2000 && kFirstAfterDrawMs == 3000);
        // SV2-SV6: the cadences and the percents N / H.
        CHECK(ArtifactEveryMs(Artifact::Eye) == 10000 && ArtifactEveryMs(Artifact::Bindings) == 15000);
        CHECK(ArtifactEveryMs(Artifact::Magma) == 15000 && ArtifactEveryMs(Artifact::Wand) == 12000);
        CHECK(ArtifactEveryMs(Artifact::BlackBlood) == 15000);
        CHECK(kEyePct.Get(false) == 25.f && kEyePct.Get(true) == 40.f && kEyeWidth == 4.f && kEyeWarnMs == 2000);
        CHECK(kBindingsPct.Get(false) == 4.f && kBindingsPct.Get(true) == 6.f);
        CHECK(kBindingsRangeYd == 8.f && kBindingsMs == 8000 && kBindingsTickMs == 1000);
        CHECK(kMagmaPct.Get(false) == 30.f && kMagmaPct.Get(true) == 45.f);
        CHECK(kMagmaInnerYd == 4.f && kMagmaOuterYd == 9.f && kMagmaCastMs == 2500);
        CHECK(kWandPct.Get(false) == 20.f && kWandPct.Get(true) == 35.f);
        CHECK(kWandLines == 3 && kWandWidth == 3.f && kWandWarnMs == 2000);
        CHECK(kBloodPct.Get(false) == 4.f && kBloodPct.Get(true) == 6.f);
        CHECK(kBloodRadiusYd == 3.f && kBloodWarnMs == 2000 && kBloodLifeMs == 30000 && kBloodHealPct == 2.f);
        // SV7 / SV8: Frost Nova 1.5 s, 10 yd, 2 players, 2 s root; Frostbolt 3 s, the stock 2.4 to 3.8 s.
        CHECK(kNovaCastMs == 1500 && kNovaRadiusYd == 10.f && kNovaMinPlayers == 2 && kNovaRootMs == 2000);
        CHECK(kNovaEveryMs == 15000);
        CHECK(kFrostboltCastMs == 3000 && kFrostboltGapMinMs == 2400 && kFrostboltGapMaxMs == 3800);
        CHECK(kFrostboltSlowMs == 4000);
        // SV9 / SV10: Curse of Blood 3-5 s in then 30-45 s (stock), 30 s, +10%; Enrage below 30%.
        CHECK(kCurseFirstMinMs == 3000 && kCurseFirstMaxMs == 5000);
        CHECK(kCurseEveryMinMs == 30000 && kCurseEveryMaxMs == 45000 && kCurseMs == 30000);
        CHECK(kCursePhysicalPct == 10.f && kEnrageBelowPct == 30.f);
        // Heroic never lowers a percent (it is the same fight, harder).
        CHECK(kEyePct.heroic > kEyePct.normal && kMagmaPct.heroic > kMagmaPct.normal);
        CHECK(kWandPct.heroic > kWandPct.normal && kNovaPct.heroic > kNovaPct.normal);
        CHECK(kFrostboltPct.heroic > kFrostboltPct.normal);
    }

    void TestNextDue()
    {
        // Start to start: a late beat does not push the cadence back, but never lands in the past.
        CHECK(NextDue(8000, 25000, 9000) == 33000);
        CHECK(NextDue(8000, 25000, 40000) == 40001);
        CHECK(NextDue(0, 15000, 0) == 15000);
    }

    void TestEnrage()
    {
        CHECK(!EnrageDue(30.f, false));
        CHECK(EnrageDue(29.9f, false));
        CHECK(!EnrageDue(10.f, true));
        CHECK(EnrageDue(0.5f, false));
    }

    // SV1: no repeats until all five are out, every cycle, whatever the rolls and the cap.
    void TestDrawCycles()
    {
        for (std::uint8_t cap : { std::uint8_t(2), std::uint8_t(3) })
        {
            for (std::uint32_t salt = 0; salt < 40; ++salt)
            {
                Collection held;
                std::uint32_t seed = salt * 2654435761u + 1;
                for (int cycle = 0; cycle < 4; ++cycle)
                {
                    std::set<int> seen;
                    for (int i = 0; i < kArtifactCount; ++i)
                    {
                        seed = seed * 1664525u + 1013904223u;
                        Draw const d = DrawNext(held.drawnMask, held.ActiveMask(), seed >> 8);
                        // Never one already drawn in this cycle.
                        CHECK(seen.insert(static_cast<int>(d.artifact)).second);
                        held.drawnMask = d.drawnMask;
                        // Never a copy of one he still holds.
                        CHECK(!held.Has(d.artifact));
                        held.Add(d.artifact, cap);
                        CHECK(held.count <= cap);
                    }
                    CHECK(seen.size() == kArtifactCount);
                    CHECK(held.drawnMask == kAllDrawnMask);
                }
            }
        }
    }

    void TestDrawEdges()
    {
        // The first draw: any of the five by the roll.
        std::set<int> first;
        for (std::uint32_t roll = 0; roll < 5; ++roll)
            first.insert(static_cast<int>(DrawNext(0, 0, roll).artifact));
        CHECK(first.size() == 5);
        // One left: that one, and the cycle mask fills.
        std::uint8_t const fourDrawn = static_cast<std::uint8_t>(kAllDrawnMask & ~BitOf(Artifact::Wand));
        Draw const last = DrawNext(fourDrawn, 0, 17);
        CHECK(last.artifact == Artifact::Wand && last.drawnMask == kAllDrawnMask);
        // A full cycle restarts, skipping the two he holds.
        std::uint8_t const held = static_cast<std::uint8_t>(BitOf(Artifact::Eye) | BitOf(Artifact::Wand));
        for (std::uint32_t roll = 0; roll < 10; ++roll)
        {
            Draw const d = DrawNext(kAllDrawnMask, held, roll);
            CHECK(d.artifact != Artifact::Eye && d.artifact != Artifact::Wand);
            CHECK(d.drawnMask == BitOf(d.artifact));
        }
        // Holding all that is left does not stall the draw.
        std::uint8_t const onlyEyeLeft = static_cast<std::uint8_t>(kAllDrawnMask & ~BitOf(Artifact::Eye));
        CHECK(DrawNext(onlyEyeLeft, BitOf(Artifact::Eye), 3).artifact == Artifact::Eye);
    }

    void TestCollection()
    {
        Collection c;
        CHECK(c.count == 0 && c.ActiveMask() == 0);
        CHECK(!c.Add(Artifact::Eye, 2));
        CHECK(!c.Add(Artifact::Wand, 2));
        CHECK(c.count == 2 && c.Has(Artifact::Eye) && c.Has(Artifact::Wand));
        // The third drops the oldest (normal: 2 active).
        std::optional<Artifact> const dropped = c.Add(Artifact::Magma, 2);
        CHECK(dropped && *dropped == Artifact::Eye);
        CHECK(c.count == 2 && !c.Has(Artifact::Eye) && c.kinds[0] == Artifact::Wand && c.kinds[1] == Artifact::Magma);
        // Heroic holds 3, then drops the oldest again.
        Collection h;
        h.Add(Artifact::Eye, 3);
        h.Add(Artifact::Bindings, 3);
        CHECK(!h.Add(Artifact::Magma, 3));
        CHECK(h.count == 3);
        std::optional<Artifact> const droppedH = h.Add(Artifact::Wand, 3);
        CHECK(droppedH && *droppedH == Artifact::Eye);
        CHECK(h.kinds[0] == Artifact::Bindings && h.kinds[1] == Artifact::Magma && h.kinds[2] == Artifact::Wand);
        // The cap never exceeds the storage or drops below one.
        Collection w;
        w.Add(Artifact::Eye, 9);
        w.Add(Artifact::Bindings, 9);
        w.Add(Artifact::Magma, 9);
        w.Add(Artifact::Wand, 9);
        CHECK(w.count == kMaxCollection);
        Collection z;
        z.Add(Artifact::Eye, 0);
        z.Add(Artifact::Wand, 0);
        CHECK(z.count == 1 && z.kinds[0] == Artifact::Wand);
        c.Clear();
        CHECK(c.count == 0 && c.drawnMask == 0);
    }

    void TestRim()
    {
        // Twelve doors, one per entry 174554-174564 and 174566, each 12.6 to 16.8 yd from kVaultCenter (12.8 to 16.6
        // from the navmesh report's center) [db].
        CHECK(kCofferDoors.size() == 12 && kCofferDoorEntries.size() == 12);
        std::set<std::uint32_t> entries(kCofferDoorEntries.begin(), kCofferDoorEntries.end());
        CHECK(entries.size() == 12);
        for (std::uint32_t entry : kCofferDoorEntries)
            CHECK(IsRelicCofferDoor(entry));
        for (std::size_t i = 0; i < kCofferDoors.size(); ++i)
        {
            Point3 const& door = kCofferDoors[i];
            float const r = DungeonKit::Distance(door.XY(), kVaultCenter);
            CHECK(r > 12.5f && r < 16.9f);
            // The spot he stands on: 3 yd in from the door, on the floor, inside the arena, on the hall's rim band.
            Point3 const stand = StandPointFor(door);
            float const sr = DungeonKit::Distance(stand.XY(), kVaultCenter);
            CHECK(std::fabs((r - sr) - kStandInsetYd) < 0.01f);
            CHECK(sr > 9.f && sr < 14.f);
            CHECK(std::fabs(stand.z - (door.z - kStandDropYd)) < 0.001f);
            CHECK(BlackVaultArena().Contains(stand.XY(), stand.z));
            CHECK(ArenaFor(BOSS_STILGISS_VEREK).Contains(stand.XY(), stand.z));
        }
        // The Dark Coffer's door 174565 is not one of them (that one is the Vault's trigger).
        CHECK(!entries.contains(174565));
        // The door picked next is never the one used last, and every door is reachable.
        std::set<std::size_t> reached;
        for (int previous = -1; previous < 12; ++previous)
            for (std::uint32_t roll = 0; roll < 40; ++roll)
            {
                std::size_t const next = NextDoor(previous, roll);
                CHECK(next < 12);
                if (previous >= 0)
                    CHECK(next != static_cast<std::size_t>(previous));
                if (previous == 0)
                    reached.insert(next);
            }
        CHECK(reached.size() == 11);
    }

    // SV5: three chords, 60 degrees apart, every end on the ring.
    void TestWandChords()
    {
        for (float base : { 0.f, 0.7f, 1.4f, 2.9f })
            for (float offset : { -8.f, -3.f, 0.f, 2.5f, 6.f })
            {
                std::array<Chord, kWandLines> const chords = WandChords(base, { offset, -offset, offset * 0.5f });
                for (std::size_t i = 0; i < kWandLines; ++i)
                {
                    Chord const& c = chords[i];
                    CHECK(std::fabs(DungeonKit::Distance(c.from, kVaultCenter) - kWandRingYd) < 0.02f);
                    CHECK(std::fabs(DungeonKit::Distance(c.to, kVaultCenter) - kWandRingYd) < 0.02f);
                    // Across the hall: far longer than the room's smallest radius.
                    CHECK(DungeonKit::Distance(c.from, c.to) > 2.f * std::sqrt(kWandRingYd * kWandRingYd
                        - kWandMaxOffsetYd * kWandMaxOffsetYd) - 0.1f);
                    // The line runs at most kWandMaxOffsetYd from the middle.
                    float along = 0.f;
                    float const d = DungeonKit::SegmentDistance(c.from, c.to, kVaultCenter, &along);
                    CHECK(d <= kWandMaxOffsetYd + 0.02f);
                    // Both ends inside the arena (which reaches 19 yd).
                    CHECK(BlackVaultArena().Contains(c.from, -50.1f) && BlackVaultArena().Contains(c.to, -50.1f));
                }
                // 60 degrees apart: the directions' dot product is cos(60).
                auto dir = [](Chord const& c)
                {
                    float const len = DungeonKit::Distance(c.from, c.to);
                    return Vec2{ (c.to.x - c.from.x) / len, (c.to.y - c.from.y) / len };
                };
                Vec2 const d0 = dir(chords[0]);
                Vec2 const d1 = dir(chords[1]);
                Vec2 const d2 = dir(chords[2]);
                CHECK(std::fabs(d0.x * d1.x + d0.y * d1.y - 0.5f) < 0.01f);
                CHECK(std::fabs(d1.x * d2.x + d1.y * d2.y - 0.5f) < 0.01f);
            }
        // Zero offsets: all three pass through the middle (the star).
        std::array<Chord, kWandLines> const star = WandChords(0.3f, { 0.f, 0.f, 0.f });
        for (Chord const& c : star)
            CHECK(DungeonKit::SegmentDistance(c.from, c.to, kVaultCenter) < 0.02f);
    }

    void TestBindings()
    {
        Vec2 const a{ 810.f, -348.f };
        CHECK(!BindingsApart(a, -50.f, { 817.9f, -348.f }, -50.f));     // 7.9 yd: together
        CHECK(!BindingsApart(a, -50.f, { 818.0f, -348.f }, -50.f));     // exactly 8: still together
        CHECK(BindingsApart(a, -50.f, { 818.2f, -348.f }, -50.f));      // 8.2 yd: apart
        CHECK(BindingsApart(a, -50.f, { 812.f, -348.f }, -40.f));       // another floor
        CHECK(!BindingsApart(a, -50.f, { 812.f, -348.f }, -45.f));      // a 5 yd step is the same floor
    }

    void TestBlackBlood()
    {
        // The marker lasts 2 s, the pool 30 s after it.
        CHECK(!BloodLive(10000, 10000));
        CHECK(!BloodLive(10000, 11999));
        CHECK(BloodLive(10000, 12000));
        CHECK(BloodLive(10000, 41999));
        CHECK(!BloodLive(10000, 42000));
        // Verek counts inside by his center within 3 yd and one floor.
        Vec2 const pool{ 813.f, -348.f };
        CHECK(InBloodPool(pool, -50.f, { 815.9f, -348.f }, -50.f));
        CHECK(InBloodPool(pool, -50.f, { 816.0f, -348.f }, -50.f));
        CHECK(!InBloodPool(pool, -50.f, { 816.2f, -348.f }, -50.f));
        CHECK(!InBloodPool(pool, -50.f, { 813.f, -348.f }, -40.f));
        // Verek's heal is the registry-sized 2% of his own health a second: 50,000 -> 1,000 a tick.
        CHECK(static_cast<int>(50000.f * kBloodHealPct / 100.f) == 1000);
    }

    // R-1-A n6: the Bindings Stacks resolve before the pair ends (the end cancels them).
    void TestBindingsStackLength()
    {
        CHECK(kBindingsStackMs < kBindingsMs);
        CHECK(kBindingsStackMs + 250 <= kBindingsMs);      // one AI tick of margin at least
        CHECK(kBindingsStackMs >= kBindingsMs - 1000);      // still the pair's length to the bots
    }

    // R-1-A m6: the script's filler flow on its kit CastQueue. A refused bolt (school lock after a kick) is not
    // Started: the coffer walk due a moment later starts at once; the old flow held the queue for the bar's 3 s.
    void TestRefusedFrostbolt()
    {
        enum : std::uint32_t { Q_COFFER = 1, Q_FROSTBOLT = 3 };
        auto run = [](bool refused)
        {
            DungeonKit::CastQueue queue;
            queue.Schedule(Q_FROSTBOLT, 0, 0);
            queue.Schedule(Q_COFFER, 500, 2);
            std::optional<std::uint32_t> const first = queue.Next(0);
            CHECK(first && *first == Q_FROSTBOLT);
            if (refused)
                queue.Schedule(Q_FROSTBOLT, 1000, 0);         // RunFrostbolt: retried in a second, nothing held
            else
            {
                queue.Started(Q_FROSTBOLT, 0, kFrostboltCastMs, false);
                queue.Schedule(Q_FROSTBOLT, kFrostboltGapMinMs, 0);
            }
            return queue.Next(500);
        };
        std::optional<std::uint32_t> const afterRefusal = run(true);
        CHECK(afterRefusal && *afterRefusal == Q_COFFER);
        CHECK(!run(false));                                     // a real bolt holds the caster its 3 s
    }

    // R-1-A m7: slot 6 IN_PROGRESS while either one fights. The instance's stock-collision guard takes the AIs'
    // writes: IN_PROGRESS while one is in combat; NOT_STARTED only once neither is (the second Reset); never over DONE.
    void TestSlotInProgress()
    {
        using DungeonKit::State::Done;
        using DungeonKit::State::InProgress;
        using DungeonKit::State::NotStarted;
        CHECK(IsStockCollisionSlot(BOSS_STILGISS_VEREK));
        CHECK(!SlotWrittenByScript(BOSS_STILGISS_VEREK));       // DONE stays the instance's (both dead)
        SlotOwners fighting;
        fighting.anyFound = true;
        fighting.anyInCombat = true;
        SlotOwners idle;
        idle.anyFound = true;
        CHECK(SlotWriteAccepted(BOSS_STILGISS_VEREK, InProgress, NotStarted, fighting, false));
        CHECK(!SlotWriteAccepted(BOSS_STILGISS_VEREK, InProgress, NotStarted, idle, false));
        CHECK(!SlotWriteAccepted(BOSS_STILGISS_VEREK, NotStarted, InProgress, fighting, false));
        CHECK(SlotWriteAccepted(BOSS_STILGISS_VEREK, NotStarted, InProgress, idle, false));
        CHECK(!SlotWriteAccepted(BOSS_STILGISS_VEREK, NotStarted, Done, idle, false));
    }

    void TestNova()
    {
        CHECK(!NovaWanted(0));
        CHECK(!NovaWanted(1));
        CHECK(NovaWanted(2));
        CHECK(NovaWanted(5));
    }
}

int main()
{
    TestIdsAndTexts();
    TestSpecNumbers();
    TestNextDue();
    TestEnrage();
    TestDrawCycles();
    TestDrawEdges();
    TestCollection();
    TestRim();
    TestWandChords();
    TestBindings();
    TestBindingsStackLength();
    TestRefusedFrostbolt();
    TestSlotInProgress();
    TestBlackBlood();
    TestNova();
    return Report("brd_stilgiss_verek_test");
}
