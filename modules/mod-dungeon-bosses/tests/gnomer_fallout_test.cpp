// Host tests for ViscousFalloutLogic.h (Gnomeregan D2: Viscous Fallout and the DoseField machine's pure half).
// WP-S0 wrote the stub (the slice, the arena, the spot); WP-D2: the halving rule (STAGE-S0 Q10), the dose ledger on
// both difficulties (the cap, the drain, Leaking, Meltdown, the emote latches), the percents, the beats, the pools
// and the drill tags.
#include "ViscousFalloutLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace GnomereganRework;
using namespace GnomerFallout;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::uint64_t constexpr kA = 0x10001;
    std::uint64_t constexpr kB = 0x10002;
    std::uint64_t constexpr kC = 0x10003;

    void TestSliceAndSpot()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214340 && kSpellSlice.last == 214379);
        CHECK(SPELL_VF_IRRADIATED == 214340);
        CHECK(SPELL_VF_VOLLEY_LOOK == 214356);
        CHECK(kSpellSlice.Contains(SPELL_VF_VOLLEY_LOOK));
        // The spawn is on the slot's arena: area C (section 7 #19 A), facing 3.95 (STAGE-S0 Q8).
        CHECK(ArenaFor(BOSS_VISCOUS_FALLOUT).Contains(kFalloutSpawn.XY(), kFalloutSpawn.z));
        CHECK(Near(kFalloutSpawn.x, -391.f) && Near(kFalloutSpawn.y, 132.f) && Near(kFalloutSpawn.o, 3.95f));
        // The 30 yd fight area round C stays on the cave floor in eight directions (picks and pools land there).
        Arena const cave = CaveArena();
        for (int i = 0; i < 8; ++i)
        {
            float const a = float(i) * DungeonKit::kTwoPi / 8.f;
            Vec2 const p{ kFalloutSpawn.x + 10.f * std::cos(a), kFalloutSpawn.y + 10.f * std::sin(a) };
            CHECK(cave.Contains(p, kFalloutSpawn.z));
        }
    }

    void TestHalvingRule()
    {
        // STAGE-S0 Q10: loses half rounded up, keeps half rounded down; one rule for Half-Life and the plates.
        CHECK(Halve(0) == 0 && Shed(0) == 0);
        CHECK(Halve(1) == 0 && Shed(1) == 1);
        CHECK(Halve(2) == 1 && Shed(2) == 1);
        CHECK(Halve(9) == 4 && Shed(9) == 5);
        CHECK(Halve(10) == 5 && Shed(10) == 5);
        CHECK(Halve(21) == 10 && Shed(21) == 11);
        for (std::uint32_t d = 0; d < 300; ++d)
        {
            CHECK(Halve(d) + Shed(d) == d);
            CHECK(Shed(d) >= Halve(d));             // the rounding favors the player
            CHECK(Shed(d) == (d + 1) / 2);
        }
    }

    void TestArithmetic()
    {
        CHECK(ApplyDelta(0, -3, 0) == 0);
        CHECK(ApplyDelta(5, 2, 0) == 7);
        CHECK(ApplyDelta(9, 3, 10) == 10);
        CHECK(ApplyDelta(9, -12, 10) == 0);
        CHECK(ApplyDelta(40, 5, 0) == 45);          // heroic: no cap
        CHECK(Crossing(9, 10, 10) == 1);
        CHECK(Crossing(10, 12, 10) == 0);
        CHECK(Crossing(12, 9, 10) == -1);
        CHECK(Crossing(3, 30, 0) == 0);             // off
        CHECK(ShownStacks(0) == 0 && ShownStacks(12) == 12 && ShownStacks(300) == 255);
        CHECK(GeigerEveryMs(0) == 0);
        CHECK(GeigerEveryMs(1) == Tune::kGeigerSlowMs);
        CHECK(GeigerEveryMs(100) == Tune::kGeigerFastMs);
        for (std::uint32_t d = 1; d < 40; ++d)
            CHECK(GeigerEveryMs(d + 1) <= GeigerEveryMs(d));
        // 3% a dose: 9 is 27% (the edge of the cliff, SP VF1).
        CHECK(Tune::kDosePctPerStack * 9 == 27);
    }

    void TestNormalLedger()
    {
        DoseLedger ledger(FalloutDoseRules(false));
        CHECK(ledger.Rules().capAt == 10 && ledger.Rules().drainEveryMs == 3000);
        CHECK(!ledger.Rules().leakAt && !ledger.Rules().meltdownAt);

        // Two Volleys and a glob: 2 + 2 + 3 = 7.
        CHECK(!ledger.Add(kA, Tune::kVolleyDose).Any());
        ledger.Add(kA, Tune::kVolleyDose);
        ledger.Add(kA, Tune::kOozeDose.normal);
        CHECK(ledger.Dose(kA) == 7);
        // A third Volley tips over: the cap fires once, the dose waits at 10, nothing more is taken.
        DoseEvents e = ledger.Add(kA, Tune::kVolleyDose + Tune::kSaturatedVolleyDose);
        CHECK(e.cap);
        CHECK(ledger.Dose(kA) == 10 && ledger.CapPending(kA));
        CHECK(!ledger.Add(kA, 1).Any());
        CHECK(ledger.Dose(kA) == 10);
        CHECK(!ledger.Tick(kA, 5000, true).Any());   // no drain while the Sickness waits
        e = ledger.ResolveCap(kA);
        CHECK(!e.Any());
        CHECK(ledger.Dose(kA) == 0 && !ledger.CapPending(kA));
        CHECK(ledger.Size() == 0);                  // pruned: no latch on normal

        // The drain: 1 per 3 s out of every pool; standing in one restarts the clock.
        ledger.Add(kB, 5);
        CHECK(!ledger.Tick(kB, 2000, true).drained);
        CHECK(ledger.Tick(kB, 1000, true).drained);
        CHECK(ledger.Dose(kB) == 4);
        ledger.Tick(kB, 2500, true);
        CHECK(!ledger.Tick(kB, 250, false).drained);     // stepped into a pool: the clock resets
        CHECK(!ledger.Tick(kB, 2750, true).drained);
        CHECK(ledger.Tick(kB, 250, true).drained);
        CHECK(ledger.Dose(kB) == 3);
        // 3 left drains to 0 in 9 s, and the entry goes.
        for (int i = 0; i < 36; ++i)
            ledger.Tick(kB, 250, true);
        CHECK(ledger.Dose(kB) == 0 && ledger.Size() == 0);

        // A GM set at the cap is Sickness too (the cap fires as an Add would); below it nothing fires.
        CHECK(!ledger.Set(kC, 6).Any());
        CHECK(ledger.Set(kC, 12).cap);
        CHECK(ledger.Dose(kC) == 10);
        ledger.ResolveCap(kC);
        CHECK(ledger.Dose(kC) == 0);

        // The failing path (SP "Left in a pool"): Volleys alone (2 per 15 s against 5 drained) never tip a player.
        DoseLedger calm(FalloutDoseRules(false));
        bool tipped = false;
        for (std::uint32_t t = 0; t <= 120000; t += 250)
        {
            if (t && t % 15000 == 0)
                tipped |= calm.Add(kA, Tune::kVolleyDose).cap;
            calm.Tick(kA, 250, true);
        }
        CHECK(!tipped);
        CHECK(calm.Dose(kA) <= 2);
        // Saturated left on (+4 per Volley) plus a second a beat in a pool tips a greedy player within four beats.
        DoseLedger greedy(FalloutDoseRules(false));
        bool cap = false;
        for (std::uint32_t beat = 1; beat <= 4 && !cap; ++beat)
        {
            cap |= greedy.Add(kA, VolleyDose(true)).cap;
            cap |= greedy.Add(kA, Tune::kPoolDose).cap;
        }
        CHECK(cap);
    }

    void TestHeroicLedger()
    {
        DoseLedger ledger(FalloutDoseRules(true));
        CHECK(!ledger.Rules().capAt && !ledger.Rules().drainEveryMs);
        CHECK(ledger.Rules().leakAt == 10 && ledger.Rules().meltdownAt == 20);

        // No drain on heroic.
        ledger.Add(kA, 4);
        for (int i = 0; i < 100; ++i)
            CHECK(!ledger.Tick(kA, 250, true).drained);
        CHECK(ledger.Dose(kA) == 4);

        // Leaking at 10: the emote once; the first drop a full 10 s after the crossing, then every 10 s.
        DoseEvents e = ledger.Add(kA, 6);
        CHECK(e.leakEmote && !e.meltdown && !e.cap);
        std::uint32_t drops = 0;
        for (std::uint32_t t = 250; t < 30000; t += 250)
            drops += ledger.Tick(kA, 250, false).leakDrop ? 1 : 0;
        CHECK(drops == 2);                          // at 10 s and 20 s (29.75 s so far)
        drops += ledger.Tick(kA, 250, false).leakDrop ? 1 : 0;
        CHECK(drops == 3);

        // Meltdown at 20: on, the emote once.
        e = ledger.Add(kA, 10);
        CHECK(e.meltdown == 1 && e.meltdownEmote && !e.leakEmote);
        CHECK(ledger.Dose(kA) == 20);
        // Half-Life: 21 -> 10 (11 shed): Meltdown off, still Leaking (10 is the line).
        ledger.Add(kA, 1);
        std::uint32_t shed = 0;
        e = ledger.Halve(kA, shed);
        CHECK(shed == 11 && ledger.Dose(kA) == 10 && e.meltdown == -1 && !e.leakEmote);
        // 10 -> 5: no longer Leaking; drops stop.
        e = ledger.Halve(kA, shed);
        CHECK(shed == 5 && ledger.Dose(kA) == 5);
        for (int i = 0; i < 80; ++i)
            CHECK(!ledger.Tick(kA, 250, false).leakDrop);
        // Back over both lines: no second emote this pull (the latches), Meltdown on again.
        e = ledger.Add(kA, 15);
        CHECK(e.meltdown == 1 && !e.meltdownEmote && !e.leakEmote);
        // Halving down to 0 keeps the latches (the entry stays while it holds one).
        ledger.Halve(kA, shed);
        ledger.Halve(kA, shed);
        ledger.Halve(kA, shed);
        ledger.Halve(kA, shed);
        ledger.Halve(kA, shed);
        CHECK(ledger.Dose(kA) == 0);
        CHECK(ledger.Find(kA) && ledger.Find(kA)->leakEmoted);
        CHECK(!ledger.Add(kA, 12).leakEmote);

        // No cap: 30 is a Volley that kills from full (ruling 18).
        ledger.Set(kB, 30);
        CHECK(ledger.Dose(kB) == 30);
        CHECK(Near(VolleyPct(true, ledger.Dose(kB), false), 100.f));

        // Carriers: the highest dose first.
        ledger.Set(kC, 30);
        auto const carriers = ledger.Carriers();
        CHECK(carriers.size() == 3);
        CHECK(carriers[0].second == 30 && carriers[1].second == 30 && carriers[2].second == 12);
        CHECK(carriers[0].first == kB && carriers[1].first == kC);
        ledger.Forget(kB);
        CHECK(ledger.Dose(kB) == 0);
        ledger.Clear();
        CHECK(ledger.Size() == 0 && ledger.Carriers().empty());
    }

    void TestPercents()
    {
        CHECK(Near(VolleyPct(false, 9, false), 10.f));
        CHECK(Near(VolleyPct(true, 0, false), 10.f));
        CHECK(Near(VolleyPct(true, 20, false), 70.f));     // SP: at 20 dose a Volley is 70%
        CHECK(Near(VolleyPct(false, 0, true), 15.f));
        CHECK(VolleyDose(false) == 2 && VolleyDose(true) == 4);
        CHECK(Near(OozePct(false, false), 40.f) && Near(OozePct(true, false), 60.f));
        CHECK(Near(OozePct(false, true), 60.f));
        CHECK(Near(SaturatedFactor(false), 1.f) && Near(SaturatedFactor(true), 1.5f));
        // Half-Life: 0.5% of his maximum health per dose shed.
        CHECK(HalfLifeHeal(Health::kViscousFallout.heroic, 0) == 0);
        CHECK(HalfLifeHeal(Health::kViscousFallout.heroic, 10) == 23333);
        CHECK(HalfLifeHeal(Health::kViscousFallout.normal, 1) == 330);
        // RF-1 Minor-2: the bots' shapes warn for the bar's real length (a slowed 3 s bar runs about 4.8 s).
        CHECK(HalfLifeBarMs(4800) == 4800);
        CHECK(HalfLifeBarMs(3000) == Tune::kHalfLifeCastMs);
        CHECK(HalfLifeBarMs(0) == Tune::kHalfLifeCastMs);
        CHECK(HalfLifeBarMs(-1) == Tune::kHalfLifeCastMs);
        // Hits on the reference rows (section 3.6): the glob 40% on normal is 678 (the tank row 683); the pool 8%.
        CHECK(DungeonKit::RefFlatValue(kReferenceNormal.nonTank, kReferenceNormal.tank, Tune::kOozePct.normal, false)
            == 678);
        CHECK(DungeonKit::RefFlatValue(kReferenceNormal.nonTank, kReferenceNormal.tank, Tune::kOozePct.normal, true)
            == 683);
        CHECK(DungeonKit::RefFlatValue(kReferenceHeroic.nonTank, kReferenceHeroic.tank, Tune::kPoolPct, false) == 330);
        // Normal hits fit the ladder (40% at a 2 s warning).
        CHECK(Tune::kOozePct.normal <= 40.f && Tune::kOozeWarnMs >= 2000);
        CHECK(Near(DiscScale(4.8f), 1.f));
        CHECK(Near(DiscScale(7.f), 7.f / 4.8f));
        CHECK(GlobLaunchDelayMs(0.f) == 2000);
        CHECK(GlobLaunchDelayMs(20.f) == 1000);
        CHECK(GlobLaunchDelayMs(40.f) == 0);
        CHECK(GlobLaunchDelayMs(60.f) == 0);
    }

    void TestBeats()
    {
        // Normal, about 84 s (SP "Failing path math"): Volleys at 15, 30, 45, 60, 75; globs from 5 s every 10 s.
        BeatCounts n = SimulateBeats(false, 84000);
        CHECK(n.volleys == 5);
        CHECK(n.oozes == 8);
        CHECK(n.halfLifes == 0);
        // Heroic, 90 s: Volleys every 12 s (7), Half-Life at 30, 60, 90 (3).
        BeatCounts h = SimulateBeats(true, 90000);
        CHECK(h.volleys == 7);
        CHECK(h.halfLifes == 3);
        CHECK(h.oozes == 9);
        // A beat that fired late never starves the next (RB-17).
        Beat b;
        b.Start(0, 1000, 10000);
        CHECK(!b.Due(999) && b.Due(1000));
        b.Fired(9000);                  // fired 8 s late
        CHECK(b.due == 14000);          // max(11000, 9000 + 5000)
        b.Fired(14000);
        CHECK(b.due == 24000);
        b.Retry(24000, Tune::kHalfLifeRetryMs);
        CHECK(b.due == 25000);
        CHECK(b.InMs(20000) == 5000);
        b.Stop();
        CHECK(!b.Due(99999) && b.InMs(0) == 0);
    }

    void TestPools()
    {
        PoolSet pools;
        Vec2 const c{ -391.f, 132.f };
        float const z = -209.1f;
        std::uint32_t const volley = pools.Add(0, PoolKind::Volley, c, z, Tune::kVolleyPoolYd, Tune::kVolleyPoolArmMs,
            Tune::kVolleyPoolLifeMs.normal);
        // Arms after 1.5 s: stepping out at once costs nothing.
        CHECK(!pools.Contains(1499, c, z));
        CHECK(pools.Contains(1500, c, z));
        CHECK(pools.Contains(1500, { c.x + 3.9f, c.y }, z));
        CHECK(!pools.Contains(1500, { c.x + 4.1f, c.y }, z));
        CHECK(!pools.Contains(1500, c, z + 5.f));       // another floor
        // Lasts 20 s after arming, then it is pruned.
        CHECK(pools.Contains(21499, c, z));
        CHECK(pools.Prune(21500).size() == 1);
        CHECK(!pools.Find(volley) && pools.Size() == 0);

        // A heroic Slough grows by hand: the step is due 10 s after arming, the radius counts when the ring is live.
        std::uint32_t const slough = pools.Add(0, PoolKind::Slough, c, z, Tune::kSloughYd, Tune::kSloughSwellMs, 0,
            Tune::kSloughGrowEveryMsH);
        CHECK(pools.GrowthDue(11999).empty());
        CHECK(pools.GrowthDue(12000).size() == 1);
        CHECK(pools.Grew(slough, 12000, Tune::kSloughGrowEveryMsH));
        CHECK(pools.GrowthDue(12000).empty());
        CHECK(!pools.Contains(13000, { c.x + 7.5f, c.y }, z));
        CHECK(pools.SetRadius(slough, Tune::kSloughYd + Tune::kSloughGrowYdH));
        CHECK(pools.Contains(13000, { c.x + 7.5f, c.y }, z));
        CHECK(pools.GrowthDue(22000).size() == 1);
        CHECK(!pools.SetRadius(slough, 3.f) || pools.Find(slough)->radius >= 8.f);     // never shrinks
        // Fight-long: never pruned.
        CHECK(pools.Prune(10000000).empty());
        // A normal Slough does not grow.
        std::uint32_t const plain = pools.Add(0, PoolKind::Slough, { c.x + 30.f, c.y }, z, Tune::kSloughYd,
            Tune::kSloughSwellMs, 0, 0);
        CHECK(pools.Find(plain) && !pools.Find(plain)->grows);
        CHECK(pools.Count(PoolKind::Slough) == 2 && pools.Count(PoolKind::Volley) == 0);
        CHECK(PoolTag(PoolKind::Volley) == TAG_VF_VOLLEY_POOL && PoolTag(PoolKind::Leak) == TAG_VF_LEAKING);
        CHECK(PoolTag(PoolKind::Slough) == TAG_VF_SLOUGH && PoolTag(PoolKind::Ooze) == TAG_VF_SLOUGH);
        pools.Clear();
        CHECK(pools.Size() == 0);

        // Space math (SP): heroic, a Slough every 12 s growing 1 yd per 10 s; at 90 s the seven Sloughs sum to about
        // 2,900 sq yd (the spec's figure; overlaps counted twice).
        PoolSet heroic;
        float sum = 0.f;
        for (std::uint32_t t = 12000; t <= 84000; t += 12000)
        {
            std::uint32_t const grownSteps = (90000 - (t + Tune::kSloughSwellMs)) / Tune::kSloughGrowEveryMsH;
            float const r = Tune::kSloughYd + Tune::kSloughGrowYdH * float(grownSteps);
            heroic.Add(t, PoolKind::Slough, { float(t) / 1000.f, 0.f }, z, r, Tune::kSloughSwellMs, 0, 0);
            sum += PoolArea(r);
        }
        CHECK(heroic.Count(PoolKind::Slough) == 7);
        CHECK(Near(heroic.AreaSum(), sum, 1.f));
        CHECK(sum > 2500.f && sum < 3300.f);
    }

    void TestDrillTags()
    {
        // MechanicDrill.h kGnTagSlough .. kGnTagHalfLifeOut (WP-G1's table, LESSONS A.3 #4).
        CHECK(TAG_VF_SLOUGH == 20 && TAG_VF_SATURATED == 21 && TAG_VF_VOLLEY_POOL == 22 && TAG_VF_OOZE == 23);
        CHECK(TAG_VF_LEAKING == 24 && TAG_VF_MELTDOWN == 25 && TAG_VF_HALF_LIFE == 26 && TAG_VF_HALF_LIFE_OUT == 27);
        for (std::uint32_t tag : kDrillTags)
            CHECK(tag >= 20 && tag < 40);           // Fallout's block of the drill table
        // The drill's numbers (MechanicDrill.h kGnSloughYd, kGnVolleyPoolYd, kGnOozeYd, kGnHalfLifeStacks,
        // kGnHalfLifeYd, kGnMeltdownYd).
        CHECK(Near(Tune::kSloughYd, 7.f) && Near(Tune::kVolleyPoolYd, 4.f) && Near(Tune::kOozeYd, 5.f));
        CHECK(Tune::kHalfLifeBotStacks == 8 && Near(Tune::kHalfLifeYd, 10.f) && Near(Tune::kMeltdownYd, 6.f));
        // Texts: groups 0-4 as SP prints them (rule 35).
        CHECK(EMOTE_SLOUGH == 0 && EMOTE_SICKNESS == 1 && EMOTE_HALF_LIFE == 2 && EMOTE_LEAKING == 3
            && EMOTE_MELTDOWN == 4);
    }
}

int main()
{
    TestSliceAndSpot();
    TestHalvingRule();
    TestArithmetic();
    TestNormalLedger();
    TestHeroicLedger();
    TestPercents();
    TestBeats();
    TestPools();
    TestDrillTags();
    return Report("gnomer_fallout_test");
}
