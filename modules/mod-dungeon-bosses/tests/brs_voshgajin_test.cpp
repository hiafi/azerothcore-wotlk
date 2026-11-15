// Host tests for VoshgajinLogic.h (B2: Shadow Hunter Vosh'gajin (9236)): the ids, the build spec numbers (SP 964-1021),
// the torment order and slots (normal, heroic, the twin form from 50%), the binding hold, the flex counts, the doll
// spots and the arena.
#include "VoshgajinLogic.h"
#include "check.h"
#include <array>
#include <set>

using namespace BlackrockSpireRework;
using namespace BrsVoshgajin;

namespace
{
    bool Contains(Schedule const& s, Torment t)
    {
        for (std::uint8_t i = 0; i < s.count; ++i)
            if (s.steps[i].Has(t))
                return true;
        return false;
    }

    std::uint32_t Total(Schedule const& s)
    {
        std::uint32_t n = 0;
        for (std::uint8_t i = 0; i < s.count; ++i)
            n += s.steps[i].count;
        return n;
    }

    // Every torment of a binding runs once.
    bool OncePerTorment(Schedule const& s)
    {
        std::array<int, 3> seen{ 0, 0, 0 };
        for (std::uint8_t i = 0; i < s.count; ++i)
            for (std::uint8_t j = 0; j < s.steps[i].count; ++j)
                ++seen[static_cast<std::size_t>(s.steps[i].torments[j])];
        return seen[0] == 1 && seen[1] == 1 && seen[2] == 1;
    }

    void TestIdsAndArena()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 210060 && kSpellSlice.last == 210089);
        CHECK(SPELL_VG_BIND == 210060);
        CHECK(SPELL_VG_HEX_SKULL == 210075);
        CHECK(SPELL_VG_BOUND == SPELL_VG_BIND + 1);
        CHECK(SPELL_VG_HEXED == 210070);
        CHECK(SPELL_VG_HEX_OF_AGONY == 210071);
        CHECK(SPELL_VG_PIN == 210073);
        CHECK(kSpellSlice.Contains(SPELL_VG_HEX_SKULL));
        // The creature texts of 9236 are groups 0-3.
        CHECK(YELL_VG_PULL == 0 && EMOTE_VG_BIND == 1 && YELL_VG_TWIN == 2 && YELL_VG_DEATH == 3);
        bool textsSeen = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_VOSHGAJIN)
            {
                textsSeen = true;
                CHECK(range.first == 0 && range.last == YELL_VG_DEATH && range.firstNew == 0);
            }
        CHECK(textsSeen);
        // She spawns kVoshgajinSpawn, inside her arena; so do both dolls (the dais).
        CHECK(VoshgajinArena().Contains(kVoshgajinSpawn.XY(), kVoshgajinSpawn.z));
        CHECK(ArenaFor(BOSS_VOSHGAJIN).Contains(kVoshgajinSpawn.XY(), kVoshgajinSpawn.z));
        for (Point4 const& spot : kDollSpots)
            CHECK(VoshgajinArena().Contains(spot.XY(), spot.z));
        CHECK(kCreaturesWave1.Contains(NPC_BRS_VOODOO_DOLL));
        CHECK(NPC_BRS_VOODOO_DOLL == 300703);
    }

    void TestNumbers()
    {
        CHECK(kBindFirstMs == 8000);
        CHECK(kBindEveryMs(false) == 25000 && kBindEveryMs(true) == 20000);
        CHECK(kBoundMs == 18000 && kPinEveryMs == 2000 && kPinPct == 5.f);
        CHECK(kTellMs == 3000);
        CHECK((kSlotsNormal == std::array<std::uint32_t, 3>{ 4000, 10000, 16000 }));
        CHECK((kSlotsHeroic == std::array<std::uint32_t, 3>{ 3000, 8000, 13000 }));
        CHECK(kFlamesPct(false) == 30.f && kFlamesPct(true) == 35.f);
        CHECK(kNeedlePct(false) == 40.f && kNeedlePct(true) == 50.f);
        CHECK(kSqueezePct(false) == 25.f && kSqueezePct(true) == 30.f);
        CHECK(kFlamesBoundPct == 10.f && kNeedleBoundPct == 10.f);
        CHECK(kFlamesRadius == 8.f && kNeedleWidth == 4.f);
        // The Needle skips whoever is on the strings (Puppet Strings), never keyed on the dispellable Bound curse.
        CHECK(kNeedleSkipAura == SPELL_VG_BIND && kNeedleSkipAura != SPELL_VG_BOUND);
        CHECK(kSqueezeInner == 5.f && kSqueezeOuter == 25.f);
        CHECK(kPatchRadius == 5.f && kPatchMs == 20000 && kPatchTickMs == 1000 && kPatchPct == 10.f);
        CHECK(kHexedMs == 2000);
        CHECK(kHexOfAgony.first == 15000 && kHexOfAgony.every == 20000);
        CHECK(kHexOfAgonyMs == 8000 && kHexOfAgonyPct == 4.f && kHexBurstRadius == 8.f && kHexBurstPct == 40.f);
        CHECK(kTwinFromHealthPct == 50.f);
        // The Squeeze donut keeps a hole big enough for the Bound player's circle to be drawn as a donut.
        CHECK(kSqueezeInner / kSqueezeOuter >= 0.2f);
    }

    void TestFlex()
    {
        // One doll and Bound player at 5 players, two at 6 or more; a held count of 0 reads as 5.
        CHECK(kBindCount.At(0) == 1 && kBindCount.At(5) == 1);
        for (std::uint32_t n = 6; n <= 10; ++n)
        {
            CHECK(kBindCount.At(n) == 2);
            CHECK(kHexOfAgonyCount.At(n) == 2);
        }
        CHECK(kHexOfAgonyCount.At(5) == 1);
        // Never more dolls than spots.
        CHECK(kBindCount.At(10) <= kDollSpots.size());
        CHECK(kDollSpots[0].x != kDollSpots[1].x || kDollSpots[0].y != kDollSpots[1].y);
    }

    void TestTormentOrder()
    {
        // The six orders are the six permutations, each torment once.
        std::set<std::array<Torment, 3>> orders(kOrders.begin(), kOrders.end());
        CHECK(orders.size() == kOrderCount);
        for (auto const& order : kOrders)
            CHECK(order[0] != order[1] && order[1] != order[2] && order[0] != order[2]);

        for (bool heroic : { false, true })
            for (std::uint32_t roll = 0; roll < kOrderCount; ++roll)
            {
                Schedule const s = BuildSchedule(heroic, false, roll, 0);
                CHECK(s.count == 3);
                CHECK(Total(s) == 3);
                CHECK(OncePerTorment(s));
                for (std::uint8_t i = 0; i < 3; ++i)
                {
                    CHECK(s.steps[i].count == 1);
                    CHECK(s.steps[i].atMs == Slots(heroic)[i]);
                }
                // The order of the roll.
                CHECK(s.steps[0].torments[0] == kOrders[roll][0]);
                CHECK(s.steps[2].torments[0] == kOrders[roll][2]);
            }
        // A roll past the table wraps (the engine rolls 0..5; any value is safe).
        CHECK(BuildSchedule(false, false, 6, 0).steps[0].torments[0] == kOrders[0][0]);
        CHECK(BuildSchedule(false, false, 13, 0).steps[0].torments[0] == kOrders[1][0]);
        // Slots: normal 4 / 10 / 16 s, heroic 3 / 8 / 13 s.
        Schedule const n = BuildSchedule(false, false, 0, 0);
        CHECK(n.steps[0].atMs == 4000 && n.steps[1].atMs == 10000 && n.steps[2].atMs == 16000);
        Schedule const h = BuildSchedule(true, false, 0, 0);
        CHECK(h.steps[0].atMs == 3000 && h.steps[1].atMs == 8000 && h.steps[2].atMs == 13000);
        // The tells never overlap in a plain binding (a slot is at least a tell apart).
        for (std::uint8_t i = 1; i < 3; ++i)
        {
            CHECK(n.steps[i].atMs >= n.steps[i - 1].atMs + kTellMs);
            CHECK(h.steps[i].atMs >= h.steps[i - 1].atMs + kTellMs);
        }
    }

    void TestTwinTorments()
    {
        CHECK(!TwinOn(false, 10.f));        // never on normal
        CHECK(!TwinOn(true, 51.f));
        CHECK(TwinOn(true, 50.f));
        CHECK(TwinOn(true, 12.f));

        std::set<int> mates;
        for (std::uint32_t pair = 0; pair < 2; ++pair)
            for (std::uint32_t order = 0; order < kOrderCount; ++order)
            {
                Schedule const s = BuildSchedule(true, true, order, pair);
                CHECK(s.count == 2);
                CHECK(Total(s) == 3);
                CHECK(OncePerTorment(s));
                // The pair is the Needle with Flames or with Squeeze; never Flames with Squeeze.
                CHECK(s.steps[0].count == 2);
                CHECK(s.steps[0].Has(Torment::Needle));
                CHECK(!(s.steps[0].Has(Torment::Flames) && s.steps[0].Has(Torment::Squeeze)));
                CHECK(s.steps[1].count == 1);
                CHECK(!s.steps[1].Has(Torment::Needle));
                // The pair at the first slot, the third alone at the second (heroic 3 s and 8 s).
                CHECK(s.steps[0].atMs == 3000 && s.steps[1].atMs == 8000);
                mates.insert(s.steps[0].Has(Torment::Flames) ? 0 : 1);
                // The one alone is the one the pair left out.
                CHECK(s.steps[0].Has(Torment::Flames) != s.steps[1].Has(Torment::Flames));
                CHECK(s.steps[0].Has(Torment::Squeeze) != s.steps[1].Has(Torment::Squeeze));
            }
        CHECK(mates.size() == 2);       // both mates are reachable
        CHECK(BuildSchedule(true, true, 0, 0).steps[0].Has(Torment::Flames));
        CHECK(BuildSchedule(true, true, 0, 1).steps[0].Has(Torment::Squeeze));
        CHECK(BuildSchedule(true, true, 0, 0).steps[1].Has(Torment::Squeeze));
        CHECK(BuildSchedule(true, true, 0, 1).steps[1].Has(Torment::Flames));
        // The single starts after the pair has landed.
        Schedule const t = BuildSchedule(true, true, 0, 0);
        CHECK(t.steps[1].atMs >= t.steps[0].atMs + kTellMs);
        CHECK(Contains(t, Torment::Flames) && Contains(t, Torment::Needle) && Contains(t, Torment::Squeeze));
    }

    void TestBindingHold()
    {
        // Normal: the third slot lands at 19 s, past the 18 s of Bound, so the hold runs to 19.5 s.
        Schedule const n = BuildSchedule(false, false, 0, 0);
        CHECK(LastLandsMs(n) == 19000);
        CHECK(BindHoldMs(n) == 19000 + kBoundTailMs);
        CHECK(BindHoldMs(n) > kBoundMs);
        // Heroic: the third lands at 16 s, inside 18 s, so the hold is the build spec's 18 s.
        Schedule const h = BuildSchedule(true, false, 0, 0);
        CHECK(LastLandsMs(h) == 16000);
        CHECK(BindHoldMs(h) == kBoundMs);
        // Twin: the last lands at 11 s, the hold is 18 s.
        Schedule const t = BuildSchedule(true, true, 0, 0);
        CHECK(LastLandsMs(t) == 11000);
        CHECK(BindHoldMs(t) == kBoundMs);
        // No hold ever ends before a torment has landed, in any form, and a binding is over before the next starts.
        for (bool heroic : { false, true })
            for (bool twin : { false, true })
            {
                if (twin && !heroic)
                    continue;
                for (std::uint32_t order = 0; order < kOrderCount; ++order)
                {
                    Schedule const s = BuildSchedule(heroic, twin, order, order % 2);
                    CHECK(BindHoldMs(s) >= LastLandsMs(s) + kBoundTailMs);
                    CHECK(BindHoldMs(s) >= kBoundMs);
                }
                CHECK(BindingFitsCadence(heroic, twin));
            }
        // The pins: a tick every 2 s, nine of them in 18 s.
        CHECK(kBoundMs / kPinEveryMs == 9);
    }

    void TestCadences()
    {
        // 8 s, then every 25 s (heroic 20 s); a late start does not pull the next one back.
        CHECK(NextBindMs(8000, false, 8000) == 33000);
        CHECK(NextBindMs(8000, true, 8000) == 28000);
        CHECK(NextBindMs(8000, true, 40000) == 40001);
        // Two skull re-casts inside the 8 s of a Hex of Agony (3 s and 6 s), none near its end.
        std::uint32_t skulls = 0;
        for (std::uint32_t at = kHexSkullEveryMs; at + 500 < kHexOfAgonyMs; at += kHexSkullEveryMs)
            ++skulls;
        CHECK(skulls == 2);
        // A gone aura more than 400 ms before its end counts as dispelled, well inside the 8 s.
        CHECK(kHexDispelledBeforeMs < 1000);
        // 4% a second for 8 s is 32% of the row: the wait costs.
        CHECK(kHexOfAgonyMs / 1000 * kHexOfAgonyPct == 32.f);
    }
}

int main()
{
    TestIdsAndArena();
    TestNumbers();
    TestFlex();
    TestTormentOrder();
    TestTwinTorments();
    TestBindingHold();
    TestCadences();
    return Report("brs_voshgajin_test");
}
