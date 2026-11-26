// Host tests for ElectrocutionerLogic.h (Gnomeregan D3, Electrocutioner 6000): the slice and the tags, the Voltage
// meter's cadence on both difficulties (SP "Failing path math": executions at 30 and 74 s on a clean normal, 30 / 60 /
// 90 s on heroic, at least 25 s apart on normal however badly it goes), the multiplier, the Justice shape in turn,
// the donut's reach over the platform, the Chain Bolt's jumps and percents, Static and its discharge partner, the
// picks' disc and the platform's spots.
#include "ElectrocutionerLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace GnomereganRework;
using namespace GnomerElectro;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A fight on `rules`: every `stepMs` the clock advances; a due Justice starts (the bar) and lands castMs later;
    // `mistakes(nowMs)` adds charge. Returns the start times of every Justice up to `untilMs`.
    template <class Mistakes>
    std::vector<std::uint32_t> Run(VoltageRules rules, std::uint32_t untilMs, Mistakes&& mistakes,
        std::uint32_t stepMs = 100, VoltageClock* out = nullptr)
    {
        VoltageClock clock(rules);
        std::vector<std::uint32_t> starts;
        std::uint32_t landAt = 0;
        for (std::uint32_t now = stepMs; now <= untilMs; now += stepMs)
        {
            clock.Advance(stepMs);
            if (clock.Running() && now >= landAt)
                clock.LandJustice();
            clock.Add(mistakes(now));
            if (clock.JusticeDue())
            {
                clock.StartJustice(Tune::kJusticeCastMs);
                starts.push_back(now);
                landAt = now + Tune::kJusticeCastMs;
            }
        }
        if (out)
            *out = clock;
        return starts;
    }

    std::uint32_t NoMistakes(std::uint32_t)
    {
        return 0;
    }

    void TestSliceAndTags()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 214380 && kSpellSlice.last == 214419);
        CHECK(SPELL_VOLTAGE == 214380);
        CHECK(SPELL_DISCHARGE_LOOK == kSpellSlice.first + kSpellCount - 1);
        CHECK(kSpellSlice.Contains(kSpellSlice.first + kSpellCount - 1));
        // The drill's block 40-49 (BM MechanicDrill.h kGnTag*), each tag once.
        for (std::size_t i = 0; i < kDrillTags.size(); ++i)
        {
            CHECK(kDrillTags[i].tag >= 40 && kDrillTags[i].tag <= 49);
            for (std::size_t j = i + 1; j < kDrillTags.size(); ++j)
                CHECK(kDrillTags[i].tag != kDrillTags[j].tag);
        }
        CHECK(TAG_JUSTICE_DONUT == 40 && TAG_JUSTICE_CIRCLE == 41 && TAG_MEGAVOLT == 42);
        CHECK(TAG_CHAIN_BOLT == 44 && TAG_CHAIN_BOLT_NORMAL == 45 && TAG_DISCHARGE == 46);
        // Texts: the stock row stays group 0 (rule 35).
        CHECK(SAY_JUSTICE == 0 && SAY_AGGRO == 1 && EMOTE_JUSTICE_DONUT == 2 && EMOTE_JUSTICE_CIRCLE == 3);
    }

    void TestTuneAgainstTheSpec()
    {
        // The warning floor (SYS 4) on every bar.
        CHECK(Tune::kJusticeCastMs >= kWarningFloorMs);
        CHECK(Tune::kMegavoltCastMs >= kWarningFloorMs);
        CHECK(Tune::kChainCastMs >= kWarningFloorMs);
        // Normal: 40% Megavolt at 2 s, 75% Justice at 4 s (the ladder); heroic 60%.
        CHECK(Near(Tune::kMegavoltPct(false), 40.f) && Near(Tune::kMegavoltPct(true), 60.f));
        CHECK(Near(Tune::kJusticePct, 75.f));
        CHECK(Tune::kMegavoltTargets(false) == 1 && Tune::kMegavoltTargets(true) == 2);
        CHECK(Tune::kMegavoltVoltsPerHit(false) == 1 && Tune::kMegavoltVoltsPerHit(true) == 2);
        CHECK(Near(Tune::kChainJumpYd(false), 6.f) && Near(Tune::kChainJumpYd(true), 10.f));
        CHECK(Tune::kChainMaxJumps(false) == 2 && Tune::kChainMaxJumps(true) == 0);
        CHECK(Near(Tune::kShockPct(false), 10.f) && Near(Tune::kShockPct(true), 15.f));
        CHECK(Near(Tune::kLightningPctPerStack(false), 0.f) && Near(Tune::kLightningPctPerStack(true), 3.f));
        // Static: the bot threshold sits under the discharge; the band between the donut's hole and the circle.
        CHECK(float(Tune::kStaticBotStandAbove) < Tune::kStaticDischargeAt);
        CHECK(Tune::kStaticGraceMs == 5000);                               // STAGE-R-1-A DQ2
        CHECK(Tune::kRangedBandMinYd > Tune::kJusticeSafeYd && Tune::kRangedBandMaxYd < Tune::kJusticeCircleYd);
        CHECK(Tune::kRangedBandMaxYd < kPlatformPickRadius);
        // Rule 17: no beat starves another.
        CHECK(NextDue(10000, 10000, 12000) == 22000);
        CHECK(NextDue(10000, 30000, 12000) == 36000);
    }

    void TestNormalCadence()
    {
        // Clean: the meter climbs by itself only. Executions at 30 and 74 s (SP), two in an 89 s fight.
        std::vector<std::uint32_t> const clean = Run(BossVoltageRules(false), 89000, NoMistakes);
        CHECK(clean.size() == 2);
        CHECK(clean.size() >= 1 && clean[0] == 30000);
        CHECK(clean.size() >= 2 && clean[1] == 74000);

        // Sloppy (SP: one player per Megavolt, two jumps per Chain Bolt): about one every 30 s, three in the fight.
        auto sloppy = [](std::uint32_t now)
        {
            std::uint32_t add = 0;
            if (now >= Tune::kMegavoltFirstMs && (now - Tune::kMegavoltFirstMs) % Tune::kMegavoltEveryMs == 0)
                add += 1;
            if (now >= Tune::kChainFirstMs + Tune::kChainCastMs
                && (now - Tune::kChainFirstMs - Tune::kChainCastMs) % Tune::kChainEveryMs == 0)
                add += 2;
            return add;
        };
        std::vector<std::uint32_t> const s = Run(BossVoltageRules(false), 93000, sloppy);
        CHECK(s.size() == 3);
        for (std::size_t i = 1; i < s.size(); ++i)
            CHECK(s[i] - s[i - 1] >= 25000);

        // Worst case: five players in every Megavolt the moment the pause lifts. Still 25 s apart (the floor).
        auto worst = [](std::uint32_t now) { return now % 1000 == 0 ? 5u : 0u; };
        std::vector<std::uint32_t> const w = Run(BossVoltageRules(false), 120000, worst);
        CHECK(w.size() >= 3);
        for (std::size_t i = 1; i < w.size(); ++i)
            CHECK(w[i] - w[i - 1] >= 25000);
        // Without the floor the pause alone would allow less (the reason for kJusticeMinGapMs).
        VoltageRules noFloor = BossVoltageRules(false);
        noFloor.minGapMs = 0;
        std::vector<std::uint32_t> const nf = Run(noFloor, 120000, worst);
        bool shorter = false;
        for (std::size_t i = 1; i < nf.size(); ++i)
            shorter = shorter || nf[i] - nf[i - 1] < 25000;
        CHECK(shorter);
    }

    void TestNormalMeterRules()
    {
        VoltageClock c(BossVoltageRules(false));
        CHECK(c.Stacks() == 0 && c.NextAt() == 6);
        CHECK(c.Advance(4999) == 0);
        CHECK(c.Advance(1) == 1 && c.Stacks() == 1);
        CHECK(c.Add(10) == 5 && c.Stacks() == 6);       // capped at the threshold on normal
        CHECK(c.JusticeDue());
        CHECK(c.ToNext() == 0);
        c.StartJustice(Tune::kJusticeCastMs);
        CHECK(c.Running() && !c.JusticeDue());
        CHECK(c.PauseLeft() == Tune::kJusticeCastMs + 10000);
        CHECK(c.GapLeft() == 25000);
        CHECK(c.Add(1) == 0);                           // no climb during the bar
        c.LandJustice();
        CHECK(!c.Running() && c.Stacks() == 0 && c.Justices() == 1);
        CHECK(c.Add(1) == 0);                           // ... or for 10 s after it
        CHECK(c.Advance(13999) == 0 && c.Paused());
        CHECK(c.Advance(1) == 0 && !c.Paused());
        CHECK(c.TickLeft() == Tune::kVoltageTickMs);    // the tick restarts when the pause ends
        CHECK(c.Add(2) == 2 && c.ToNext() == 4);
        c.Add(4);
        CHECK(c.Stacks() == 6 && !c.JusticeDue());      // 14 s after the start: the 25 s floor holds it
        c.Advance(11000);
        CHECK(c.GapLeft() == 0 && c.JusticeDue());
        c.LandJustice();                                // a landing with no bar running is ignored
        CHECK(c.Justices() == 1);
        c.Reset();
        CHECK(c.Stacks() == 0 && c.Justices() == 0 && !c.Paused() && c.NextAt() == 6 && c.GapLeft() == 0);
    }

    void TestHeroicCadence()
    {
        VoltageClock end;
        std::vector<std::uint32_t> const clean = Run(BossVoltageRules(true), 95000, NoMistakes, 100, &end);
        CHECK(clean.size() == 3);
        CHECK(clean.size() == 3 && clean[0] == 30000 && clean[1] == 60000 && clean[2] == 90000);
        CHECK(end.Stacks() == 19);                      // SP: about 19,000 volts by 95 s
        CHECK(Near(DamageMultiplier(end.Stacks(), Tune::kLightningPctPerStack(true)), 1.57f));
        CHECK(Near(DamageMultiplier(19, Tune::kLightningPctPerStack(false)), 1.f));

        // Never resets, no pause: a mistake during the bar counts; a threshold crossed during it folds into it.
        VoltageClock c(BossVoltageRules(true));
        CHECK(c.Add(6) == 6 && c.JusticeDue());
        c.StartJustice(Tune::kJusticeCastMs);
        CHECK(!c.Paused() && c.NextAt() == 12 && c.GapLeft() == 0);
        CHECK(c.Add(7) == 7 && c.Stacks() == 13);
        CHECK(!c.JusticeDue());
        c.LandJustice();
        CHECK(c.Stacks() == 13 && c.NextAt() == 18 && !c.JusticeDue());
        // Without the fold the next execution is due at once.
        VoltageRules rules = BossVoltageRules(true);
        rules.foldDuringBar = false;
        VoltageClock f(rules);
        f.Add(6);
        f.StartJustice(Tune::kJusticeCastMs);
        f.Add(7);
        f.LandJustice();
        CHECK(f.NextAt() == 12 && f.JusticeDue());
        // The client counter caps at 255.
        VoltageClock big(BossVoltageRules(true));
        big.Add(300);
        CHECK(big.Stacks() == Tune::kVoltageStackLimit);
        CHECK(NextJusticeAt(0, 6) == 6 && NextJusticeAt(6, 6) == 12 && NextJusticeAt(11, 6) == 12);
        CHECK(NextJusticeAt(5, 0) == 0);
        // The hard mode's rules (no floor set): the floor is the boss's own.
        VoltageClock hm{ VoltageRules{} };
        hm.Add(6);
        hm.StartJustice(4000);
        CHECK(hm.GapLeft() == 0);
        hm.SetMinGap(5000);
        hm.LandJustice();
        hm.Add(6);
        hm.StartJustice(4000);
        CHECK(hm.GapLeft() == 5000);
    }

    void TestShapesAndTiers()
    {
        for (std::uint32_t i = 0; i < 6; ++i)
            CHECK(JusticeShapeFor(i, false) == JusticeShape::Donut);
        CHECK(JusticeShapeFor(0, true) == JusticeShape::Donut);
        CHECK(JusticeShapeFor(1, true) == JusticeShape::Circle);
        CHECK(JusticeShapeFor(2, true) == JusticeShape::Donut);
        CHECK(JusticeShapeFor(3, true) == JusticeShape::Circle);
        CHECK(VoltageTier(0) == 0 && VoltageTier(1) == 1 && VoltageTier(2) == 1 && VoltageTier(3) == 2);
        CHECK(VoltageTier(19) == 2);
    }

    void TestPlatformReach()
    {
        Arena const floor = PlatformArena();
        Vec2 const center = kPlatformCenter.XY();
        float const outer = JusticeOuterYd(floor, center, Tune::kJusticeSafeYd);
        // LESSONS A.4 #5: the donut reaches the farthest corner of the platform (the walkway mouth, about 30 yd).
        for (Vec2 const& p : kPlatformPolygon)
            CHECK(DungeonKit::Distance(center, p) < outer);
        CHECK(outer > 30.f && outer < 34.f);
        // From his stock spawn (a walk that never arrived) too.
        float const fromSpawn = JusticeOuterYd(floor, kElectrocutionerSpawn.XY(), Tune::kJusticeSafeYd);
        for (Vec2 const& p : kPlatformPolygon)
            CHECK(DungeonKit::Distance(kElectrocutionerSpawn.XY(), p) < fromSpawn);
        // An empty floor: a wide reach; a tiny one: still past the hole.
        CHECK(Near(JusticeOuterYd(Arena(), center, 8.f), 60.f));
        Arena tiny(ArenaRegion::Circle(center, 2.f, -300.f, 300.f));
        CHECK(JusticeOuterYd(tiny, center, 8.f) >= 9.f);
        CHECK(Near(FarthestReach(tiny, center), 2.f));
        // R-1-A M1: the Justice's floor is the platform plus the walkway, so the donut reaches the walkway's far end
        // (NAVMESH 3: the walkway's "continues" samples, about 44 yd out); the platform alone stopped at about 31 yd.
        Arena const justice = JusticeFloor();
        float const reach = JusticeOuterYd(justice, center, Tune::kJusticeSafeYd);
        float const reachFromSpawn = JusticeOuterYd(justice, kElectrocutionerSpawn.XY(), Tune::kJusticeSafeYd);
        CHECK(reach > 45.f && reach < 52.f);
        std::vector<Vec2> const walkway{ { -548.f, 546.f }, { -545.f, 548.f }, { -542.f, 547.f }, { -539.f, 547.f },
            { -537.f, 545.f }, { -535.f, 542.f }, { -542.f, 540.f } };
        for (Vec2 const& p : walkway)
        {
            CHECK(justice.Contains(p, -218.f));
            CHECK(DungeonKit::Distance(center, p) < reach);
            CHECK(DungeonKit::Distance(kElectrocutionerSpawn.XY(), p) < reachFromSpawn);
        }
        for (Vec2 const& p : kPlatformPolygon)
            CHECK(justice.Contains({ center.x + 0.95f * (p.x - center.x), center.y + 0.95f * (p.y - center.y) },
                kPlatformCenter.z));
        CHECK(!justice.Contains(center, kPlatformCenter.z - 56.f));        // a fallen player is under it, not on it
        // The blast ring stands on the platform.
        std::uint32_t onFloor = 0;
        for (Vec2 const& p : RingPoints(center, Tune::kBlastRingYd, Tune::kBlastPoints))
        {
            CHECK(Near(DungeonKit::Distance(center, p), Tune::kBlastRingYd, 0.01f));
            if (floor.Contains(p, kPlatformCenter.z))
                ++onFloor;
        }
        CHECK(onFloor == Tune::kBlastPoints);
        CHECK(RingPoints(center, 5.f, 0).empty());
    }

    void TestPicksAndSpots()
    {
        // Rule 5, section 3.8 (R-1-A M1): a pick stands on the platform arena: the center, his spawn, the rim band
        // past the 21 yd bot disc (the ranged at 22 yd) and the walkway mouth; a fallen player never.
        CHECK(OnPickFloor(kPlatformCenter.XY(), kPlatformCenter.z));
        CHECK(OnPickFloor(kElectrocutionerSpawn.XY(), kElectrocutionerSpawn.z));
        CHECK(Near(DungeonKit::Distance(kPlatformCenter.XY(), kElectrocutionerSpawn.XY()), 2.3f, 0.1f));
        CHECK(OnPickFloor(DungeonKit::Advance(kPlatformCenter.XY(), 1.f, 22.f), kPlatformCenter.z));
        CHECK(OnPickFloor(kEndNpc1Spot.XY(), kEndNpc1Spot.z));
        CHECK(!PlatformPickArena().Contains(DungeonKit::Advance(kPlatformCenter.XY(), 1.f, 22.f), kPlatformCenter.z));
        CHECK(!OnPickFloor(kPlatformCenter.XY(), kPlatformCenter.z - 56.f));    // fell off: never picked
        // The heroic circle's safe ring fits on the bots' disc.
        CHECK(PlatformPickArena().Contains(DungeonKit::Advance(kPlatformCenter.XY(), 2.f, Tune::kJusticeCircleYd + 1.f),
            kPlatformCenter.z));
        CHECK(ArenaFor(BOSS_ELECTROCUTIONER).Contains(kEndNpc1Spot.XY(), kEndNpc1Spot.z));
        CHECK(ArenaFor(BOSS_ELECTROCUTIONER).Contains(kElectrocutionerSpawn.XY(), kElectrocutionerSpawn.z));
    }

    void TestChain()
    {
        // Five players in a row 5 yd apart, the target at one end.
        std::vector<ChainNode> row;
        for (std::uint64_t i = 0; i < 5; ++i)
            row.push_back({ i + 1, { -550.f + 5.f * float(i), 505.f } });
        std::vector<std::size_t> n = ChainOrder(row, 0, Tune::kChainJumpYd(false), Tune::kChainMaxJumps(false));
        CHECK(n.size() == 3 && n[0] == 0 && n[1] == 1 && n[2] == 2);       // two jumps on normal
        std::vector<std::size_t> h = ChainOrder(row, 0, Tune::kChainJumpYd(true), Tune::kChainMaxJumps(true));
        CHECK(h.size() == 5);                                               // no limit on heroic
        // Spread 6.5 yd apart: nobody is reached on normal; the heroic 10 yd still jumps.
        std::vector<ChainNode> spread;
        for (std::uint64_t i = 0; i < 5; ++i)
            spread.push_back({ i + 1, { -550.f + 6.5f * float(i), 505.f } });
        CHECK(ChainOrder(spread, 2, 6.f, 2).size() == 1);
        CHECK(ChainOrder(spread, 0, 10.f, 0).size() == 5);
        // From the middle: the nearest first, ties to the lower index; the chain runs from the last one struck, so
        // it never comes back across the target (index 3 is 15 yd from the end it reached).
        std::vector<std::size_t> mid = ChainOrder(row, 2, 6.f, 0);
        CHECK(mid.size() == 3 && mid[1] == 1 && mid[2] == 0);
        CHECK(ChainOrder(row, 9, 6.f, 0).empty());
        CHECK(ChainOrder({}, 0, 6.f, 0).empty());
        // Percents: normal 20 each; heroic 40, then each jump 25% more than the last.
        CHECK(Near(ChainHitPct(0, 20.f, 1.f), 20.f) && Near(ChainHitPct(2, 20.f, 1.f), 20.f));
        CHECK(Near(ChainHitPct(0, 40.f, 1.25f), 40.f));
        CHECK(Near(ChainHitPct(1, 40.f, 1.25f), 50.f));
        CHECK(Near(ChainHitPct(2, 40.f, 1.25f), 62.5f));
        CHECK(Near(ChainHitPct(3, 40.f, 1.25f), 78.125f));
    }

    void TestStatic()
    {
        StaticCharge c;
        Vec2 at{ -550.f, 505.f };
        CHECK(!c.Step(at, 250) && c.Shown() == 0);      // the first sample only remembers the spot
        // 1 yd a sample: 19 shown after 19 yards, the discharge at 20 (then 0).
        bool fired = false;
        std::uint32_t samples = 0;
        while (!fired && samples < 40)
        {
            at.x += 1.f;
            fired = c.Step(at, 250);
            ++samples;
            if (samples == 19)
                CHECK(c.Shown() == 19);
        }
        CHECK(fired && samples == 20 && c.Shown() == 0);
        // Standing still drains 2 a second.
        c.Set(10.f);
        for (int i = 0; i < 4; ++i)
            CHECK(!c.Step(at, 250));
        CHECK(Near(c.Value(), 8.f));
        // A teleport adds nothing and drains nothing.
        Vec2 const far{ at.x + 40.f, at.y };
        CHECK(!c.Step(far, 250));
        CHECK(Near(c.Value(), 8.f));
        // Never below 0.
        c.Set(0.4f);
        CHECK(!c.Step(far, 250));
        CHECK(Near(c.Value(), 0.f));
        // A 15 yd run to the middle is most of a discharge (SP): 15 shown.
        StaticCharge run;
        Vec2 p{ 0.f, 0.f };
        run.Step(p, 250);
        for (int i = 0; i < 6; ++i)
        {
            p.x += 2.5f;
            run.Step(p, 250);
        }
        CHECK(run.Shown() == 15);
        // Forget: the next sample starts again.
        run.Forget();
        CHECK(!run.Step({ 100.f, 100.f }, 250) && run.Shown() == 15);

        // The partner: the nearest other player within 10 yd.
        std::vector<ChainNode> nodes{ { 1, { 0.f, 0.f } }, { 2, { 9.f, 0.f } }, { 3, { 0.f, 4.f } },
            { 4, { 30.f, 0.f } } };
        std::optional<std::size_t> ally = NearestWithin(nodes, 0, Tune::kDischargeAllyYd);
        CHECK(ally && *ally == 2);
        CHECK(!NearestWithin(nodes, 3, Tune::kDischargeAllyYd));
        CHECK(!NearestWithin(nodes, 7, Tune::kDischargeAllyYd));
    }
}

int main()
{
    TestSliceAndTags();
    TestTuneAgainstTheSpec();
    TestNormalCadence();
    TestNormalMeterRules();
    TestHeroicCadence();
    TestShapesAndTiers();
    TestPlatformReach();
    TestPicksAndSpots();
    TestChain();
    TestStatic();
    return Report("gnomer_electro_test");
}
