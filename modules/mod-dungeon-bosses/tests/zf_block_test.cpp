// Host tests for BlockLogic.h (D4a): the slice, the arena and its spots, the Block's clock and gaps, the prisoner and
// soaker picks, the Behead's percent, the chain spot candidates, the Sandfury entries, the wound's end and the Blood
// Price arithmetic and bleed meter (PyramidFight.h's pure half).
#include "BlockLogic.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfBlock;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfBlock::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfBlock::kSpellSlice.last));
    CHECK(SPELL_PY_BEHEAD_BAR == 213960);
    CHECK(SPELL_PY_GRIEVOUS_WOUND == 213963);
    CHECK(SPELL_PY_CHAIN == 213967);
    CHECK(kSpellSlice.Contains(SPELL_PY_CHAIN));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(PyramidTopArena().Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
    CHECK(ArenaFor(BOSS_PYRAMID).Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
    // the landing
    CHECK(PyramidTopArena().Contains(kLanding.XY(), kLanding.z));
    // a cage
    CHECK(PyramidTopArena().Contains(kCages[0].XY(), kCages[0].z));
    // Every crew spawn (the cages the prisoners come from and go back to) is on the top.
    for (Point3 const& p : kCrewSpawns)
        CHECK(PyramidTopArena().Contains(p.XY(), p.z));

    // ---- PY1 the Block's gaps (SP: 10 s, then 20 s; heroic 18 s and 2 s shorter each, floor cast + 1 s) ----
    CHECK(Tune::kBlockGapFloorMs == 5000);
    CHECK(BlockGapMs(0, false) == 20000);
    CHECK(BlockGapMs(9, false) == 20000);
    CHECK(BlockGapMs(0, true) == 18000);
    CHECK(BlockGapMs(1, true) == 16000);
    CHECK(BlockGapMs(5, true) == 8000);
    CHECK(BlockGapMs(6, true) == 6000);
    CHECK(BlockGapMs(7, true) == 5000);      // 4 s would be under the floor
    CHECK(BlockGapMs(8, true) == 5000);
    CHECK(BlockGapMs(4000000000u, true) == 5000);    // no unsigned wrap in a long fight
    // The heroic starts: 10, 28, 44, 58, 70, 80, 88, 94, 99, 104 s.
    {
        std::vector<std::uint32_t> starts;
        std::uint32_t at = Tune::kBlockFirstMs;
        for (std::uint32_t i = 0; i < 10; ++i)
        {
            starts.push_back(at / 1000);
            at += BlockGapMs(i, true);
        }
        CHECK((starts == std::vector<std::uint32_t>{ 10, 28, 44, 58, 70, 80, 88, 94, 99, 104 }));
    }
    // Handoff 3.6's timelines: normal 136,058 at 2,500 bot DPS dies near 54 s (3 Blocks); heroic 226,764 at 5,500 near
    // 41 s (2 Blocks; the third at 44 s for a slower group).
    CHECK(BlocksBy(9999, false) == 0);
    CHECK(BlocksBy(10000, false) == 1);
    CHECK(BlocksBy(54000, false) == 3);
    CHECK(BlocksBy(41000, true) == 2);
    CHECK(BlocksBy(44000, true) == 3);
    // The spec's own target (1,431 normal): 85,000 / 1,431 = 59 s: three Blocks, as SP says ("about 60 s, so three").
    CHECK(BlocksBy(59000, false) == 3);

    // ---- the clock ----
    {
        BlockClock c;
        CHECK(!c.Due());
        c.Advance(9999);
        CHECK(!c.Due());
        c.Advance(1);
        CHECK(c.Due());
        c.Start(true);
        CHECK(c.busy && !c.Due() && c.started == 1);
        CHECK(c.nextDue == 28000);
        c.Advance(30000);       // the Block ran long: the next one waits for it to end
        CHECK(!c.Due());
        c.End();
        CHECK(c.Due());
        c.Retry();              // nobody free
        CHECK(!c.Due());
        c.Advance(Tune::kBlockRetryMs);
        CHECK(c.Due());
        c.Start(true);
        CHECK(c.nextDue == c.now + 16000);
        c.End();
        c.Exhaust();            // every fighter lost
        c.Advance(100000);
        CHECK(!c.Due());
    }
    {
        BlockClock c;
        c.Advance(10000);
        c.Start(false);
        CHECK(c.nextDue == 30000);
    }

    // ---- the prisoner (never Weegli; the roll picks among the free fighters) ----
    CHECK(!PickPrisoner(0, 0));
    CHECK(!PickPrisoner(kCrewWeegliBit, 0));
    CHECK(PickPrisoner(CrewBit(CREW_RAVEN), 7) == CREW_RAVEN);
    CHECK(PickPrisoner(kCrewAll, 0) == CREW_BLY);
    CHECK(PickPrisoner(kCrewAll, 1) == CREW_RAVEN);
    CHECK(PickPrisoner(kCrewAll, 2) == CREW_ORO);
    CHECK(PickPrisoner(kCrewAll, 3) == CREW_MURTA);     // Weegli's bit skipped
    CHECK(PickPrisoner(kCrewAll, 4) == CREW_BLY);       // modulo the four
    CHECK(PickPrisoner(CrewBit(CREW_ORO) | CrewBit(CREW_MURTA), 1) == CREW_MURTA);

    // ---- the soaker: inside 2 yd and 3 yd of height, wound-free first, then the nearest ----
    CHECK(!PickSoaker({}));
    CHECK(!PickSoaker({ { 2.1f, 0.f, false } }));
    CHECK(!PickSoaker({ { 1.f, 3.5f, false } }));
    CHECK(PickSoaker({ { 2.f, -3.f, false } }).has_value());
    {
        std::vector<SoakerCandidate> const c{ { 0.5f, 0.f, true }, { 1.5f, 0.f, false }, { 1.0f, 0.f, false } };
        std::optional<SoakerPick> const p = PickSoaker(c);
        CHECK(p && p->index == 2 && !p->wounded);
    }
    {
        std::vector<SoakerCandidate> const c{ { 9.f, 0.f, false }, { 1.5f, 0.f, true } };
        std::optional<SoakerPick> const p = PickSoaker(c);
        CHECK(p && p->index == 1 && p->wounded);      // only a wounded one inside: the 150% (a human's choice)
    }
    CHECK(Near(BeheadPct(false, false), 40.f));
    CHECK(Near(BeheadPct(false, true), 40.f));      // no wound on normal
    CHECK(Near(BeheadPct(true, false), 60.f));
    CHECK(Near(BeheadPct(true, true), 150.f));

    // ---- the chain spot: 2.5 yd, behind him first, the victim's side last ----
    {
        Vec2 const boss = kExecutionerSpawn.XY();
        Vec2 const victim = kLanding.XY();
        float const away = DungeonKit::BearingTo(victim, boss);
        auto const spots = ChainSpotCandidates(boss, away);
        for (Vec2 const& p : spots)
            CHECK(Near(DungeonKit::Distance(p, boss), Tune::kChainDistYd));
        // the first is farther from the victim than he is, the last nearer
        CHECK(DungeonKit::Distance(spots.front(), victim) > DungeonKit::Distance(boss, victim));
        CHECK(DungeonKit::Distance(spots.back(), victim) < DungeonKit::Distance(boss, victim));
        // all of them are on the top around his spawn, at his height (the engine checks the real floor height too)
        std::uint32_t inside = 0;
        for (Vec2 const& p : spots)
            if (PyramidTopArena().Contains(p, kExecutionerSpawn.z))
                ++inside;
        CHECK(inside == spots.size());
        // the soak circle fits beside him: a prisoner 2.5 yd out keeps the 2 yd circle off his own spot's center
        CHECK(Tune::kChainDistYd > Tune::kSoakRadiusYd);
    }

    // ---- the Pyramid-wide pieces ----
    for (std::uint32_t entry : { 7274u, 7275u, 7796u, 7787u, 7788u, 301015u, 301016u, 301017u })
        CHECK(IsPyramidSandfury(entry));
    for (std::uint32_t entry : { 301018u, 301019u, 7604u, 7607u, 7267u })
        CHECK(!IsPyramidSandfury(entry));
    CHECK(!WoundClears(94.9f));
    CHECK(WoundClears(95.f));
    CHECK(WoundClears(100.f));
    CHECK(OfferingsStacks(0) == 0);
    CHECK(OfferingsStacks(3) == 3);
    CHECK(OfferingsStacks(9) == kOfferingsCap);
    CHECK(Tune::kOfferingsPctPerStack * std::int32_t(kOfferingsCap) == 40);     // 40% at the normal cap
    CHECK(BloodPriceDamagePct(0) == 0);
    CHECK(BloodPriceDamagePct(1) == 0);
    CHECK(BloodPriceDamagePct(2) == 1);
    CHECK(BloodPriceDamagePct(kBloodPricePerCrew) == 15);      // a crew member lost on the Block: 30 stacks, +15%
    CHECK(BloodPriceDamagePct(90) == 45);                      // SP: a clean run ends near 90 stacks (45%)
    CHECK(BloodPriceDamagePct(600) == 300);                    // no cap past the counter
    CHECK(BloodPriceShownStacks(90) == 90);
    CHECK(BloodPriceShownStacks(600) == 255);
    {
        BleedMeter m;
        CHECK(m.Advance(250, true) == 0);
        CHECK(m.Advance(250, true) == 0);
        CHECK(m.Advance(250, false) == 0);     // a gap keeps the partial second
        CHECK(m.Advance(250, true) == 0);
        CHECK(m.Advance(250, true) == 1);      // four bleeding polls: one stack
        CHECK(m.Advance(2000, true) == 2);
        m.Reset();
        CHECK(m.Advance(750, true) == 0);
    }
    // SP: one Block wound cleared in about 5 s is 5 stacks; a minute of bleeding is 60.
    {
        BleedMeter m;
        std::uint32_t stacks = 0;
        for (std::uint32_t t = 0; t < 5000; t += Tune::kWoundPollMs)
            stacks += m.Advance(Tune::kWoundPollMs, true);
        CHECK(stacks == 5);
    }
    CHECK(BloodPriceLogs(9, 10));
    CHECK(!BloodPriceLogs(10, 19));
    CHECK(BloodPriceLogs(19, 31));

    return Report("zf_block_test");
}
