// Host tests for AntusulLogic.h (D2): the slice, the arena and its spots, the stone arithmetic, the rise pick, the gaze
// clock, the timeline and the bots' dispel rule.
#include "AntusulLogic.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfAntusul;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::vector<Vec2> RisePoints()
    {
        std::vector<Vec2> out;
        for (Point3 const& p : kServantRisePoints)
            out.push_back(p.XY());
        return out;
    }

    std::uint32_t First(std::uint32_t)
    {
        return 0;
    }

    std::uint32_t Last(std::uint32_t n)
    {
        return n - 1;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfAntusul::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfAntusul::kSpellSlice.last));
    CHECK(SPELL_AS_CALCIFY == 213890);
    CHECK(SPELL_AS_SERVANT_RISE == 213905);
    CHECK(kSpellSlice.Contains(SPELL_AS_SERVANT_RISE));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(DenArena().Contains(kAntusulSpawn.XY(), kAntusulSpawn.z));
    CHECK(ArenaFor(BOSS_ANTUSUL).Contains(kAntusulSpawn.XY(), kAntusulSpawn.z));
    // The chamber (section 7 #28 A: the fight's floor) and every rise point are on it.
    CHECK(DenArena().Contains(kAntusulChamber.XY(), kAntusulChamber.z));
    for (Point3 const& p : kServantRisePoints)
        CHECK(DenArena().Contains(p.XY(), p.z));
    // The area trigger's sphere reaches the chamber, not his spawn (he waits at the dead end until woken or pulled).
    CHECK(DungeonKit::Distance(kAntusulTrigger.XY(), kAntusulChamber.XY()) < kAntusulTriggerRadius);
    CHECK(DungeonKit::Distance(kAntusulTrigger.XY(), kAntusulSpawn.XY()) > kAntusulTriggerRadius);

    // ---- AS3 / AS7 / AS6 / AS8 stone arithmetic ----
    CHECK(Near(CalcifyTakenFactor(0), 1.f));
    CHECK(Near(CalcifyTakenFactor(5), 0.75f));
    CHECK(Near(CalcifyTakenFactor(9), 0.70f));      // clamped at 6 stacks
    // The shrapnel: 18% at 3, 30% at 5, 36% at 6 (normal); 54% at 6 (heroic).
    CHECK(Near(ShatterPct(3, false), 18.f));
    CHECK(Near(ShatterPct(5, false), 30.f));
    CHECK(Near(ShatterPct(6, false), 36.f));
    CHECK(Near(ShatterPct(6, true), 54.f));
    CHECK(Near(ShatterPct(5, true), 45.f));
    // No hit scales past 75% (SP approval check).
    CHECK(ShatterPct(99, true) <= 75.f);
    // Weakened up to 5 stacks, never at 6 (the crack), never for nothing.
    CHECK(ShatterWeakened(1));
    CHECK(ShatterWeakened(5));
    CHECK(!ShatterWeakened(6));
    CHECK(!ShatterWeakened(0));
    // Heroic shrapnel under 50% wherever it carries Weakened.
    for (std::uint32_t s = 1; s <= Tune::kShatterWeakenedMaxStacks; ++s)
        CHECK(ShatterPct(s, true) < 50.f);
    // The bolt on its target: 15% / 25%, cut by its own stone.
    CHECK(Near(BoltPct(0, false), 15.f));
    CHECK(Near(BoltPct(4, false), 12.f));
    CHECK(Near(BoltPct(0, true), 25.f));
    // The Shockwave: 50% at 0, 40% at 2, 25% at 5 (normal); 70% / 35% at 5 (heroic).
    CHECK(Near(ShockwaveNetPct(0, false), 50.f));
    CHECK(Near(ShockwaveNetPct(2, false), 40.f));
    CHECK(Near(ShockwaveNetPct(5, false), 25.f));
    CHECK(Near(ShockwaveNetPct(0, true), 70.f));
    CHECK(Near(ShockwaveNetPct(5, true), 35.f));
    // The registered percent times Calcify's own cut is the net (10% a stack in place of 5%).
    for (std::uint32_t s = 0; s <= 5; ++s)
        for (bool h : { false, true })
            CHECK(Near(ShockwaveScriptPct(s, h) * CalcifyTakenFactor(s), ShockwaveNetPct(s, h)));
    CHECK(Near(ShockwaveScriptPct(5, false), 25.f / 0.75f));
    // Never a full block: 6 stacks still take 40% of the hit.
    CHECK(ShockwaveNetPct(6, false) > 0.f);

    // AS9: 4% / 8% of his health.
    CHECK(PctOf(Health::kAntusul(false), Tune::kHealPct(false)) == 6398);
    CHECK(PctOf(Health::kAntusul(true), Tune::kHealPct(true)) == 21333);
    CHECK(kWakeDataId == 1 && kWakeDataValue == 1);

    // ---- AS10 ----
    CHECK(CrackReachesHim(6.f, 1.5f));
    CHECK(CrackReachesHim(7.4f, 1.5f));
    CHECK(!CrackReachesHim(7.6f, 1.5f));
    CHECK(Tune::kStonefleshStacks * std::uint32_t(Tune::kStonefleshTakenPctPerStack) == 30);

    // ---- section 7 #9 A: the bots' dispel rule ----
    CHECK(!BotsMayDispel(3, true, false, false, false));    // under 4 stacks
    CHECK(BotsMayDispel(4, true, false, false, false));     // a lone 4-stack carrier
    CHECK(!BotsMayDispel(5, false, false, false, false));   // someone within 6 yd
    CHECK(BotsMayDispel(5, true, false, true, true));       // normal: the tank too
    CHECK(!BotsMayDispel(5, true, true, true, true));       // heroic: never the tank while Stoneflesh is up
    CHECK(BotsMayDispel(5, true, true, true, false));       // heroic: the tank once Stoneflesh is gone
    CHECK(BotsMayDispel(5, true, true, false, true));       // heroic: a lone non-tank

    // ---- AS1 the rise pick ----
    {
        std::vector<Vec2> const points = RisePoints();
        // At his spawn: the throat's first point (1809.2, 682.8) is 13.9 yd away; all eight are clear of 12 yd.
        Vec2 const spawn = kAntusulSpawn.XY();
        std::optional<std::size_t> pick = PickRisePoint(points, {}, spawn, First);
        CHECK(pick && DungeonKit::Distance(points[*pick], spawn) >= Tune::kRiseClearOfBossYd);
        // Standing on a point (fought in the chamber): never that point, never one within 12 yd of him.
        Vec2 const onPoint = points[4];
        pick = PickRisePoint(points, {}, onPoint, First);
        CHECK(pick && *pick != 4 && DungeonKit::Distance(points[*pick], onPoint) >= Tune::kRiseClearOfBossYd);
        pick = PickRisePoint(points, {}, onPoint, Last);
        CHECK(pick && *pick != 4 && DungeonKit::Distance(points[*pick], onPoint) >= Tune::kRiseClearOfBossYd);
        // A living Servant takes its point.
        pick = PickRisePoint(points, { points[0] }, spawn, First);
        CHECK(pick && *pick != 0);
        // Every point taken: none.
        CHECK(!PickRisePoint(points, points, spawn, Last));
        // No point clear of him: the farthest free one.
        std::vector<Vec2> const two{ { 0.f, 0.f }, { 5.f, 0.f } };
        pick = PickRisePoint(two, {}, Vec2{ 1.f, 0.f }, First);
        CHECK(pick && *pick == 1);
    }

    // ---- AS2 the gaze clock ----
    {
        GazeClock g;
        CHECK(g.stage == GazeStage::Wait);
        CHECK(!g.Advance(500));
        CHECK(g.Advance(500));                              // the first gaze 1 s after the rise
        g.Start();
        bool ended = false;
        std::uint32_t laid = 0;
        for (int i = 0; i < 60; ++i)                        // 100 ms ticks for 6 s
        {
            laid += g.Tick(100, false, ended);
            if (ended)
                break;
        }
        CHECK(ended);
        CHECK(laid == 3);
        CHECK(laid == StacksPerGaze(false));
        g.Stop();
        CHECK(!g.Advance(1999));
        CHECK(g.Advance(1));                                // a new target 2 s later
        g.Start();
        laid = 0;
        for (int i = 0; i < 6; ++i)
            laid += g.Tick(1000, true, ended);              // heroic: 1.5, 3, 4.5, 6
        CHECK(laid == 4);
        CHECK(StacksPerGaze(true) == 4);
        CHECK(ended);
        // A big tick never lays more than the gaze's whole.
        g.Start();
        CHECK(g.Tick(60000, false, ended) == 3);
        // Held mid-gaze: stops, and the pause restarts while held.
        g.Start();
        CHECK(g.Tick(2000, false, ended) == 1);
        g.Held();
        CHECK(g.stage == GazeStage::Wait);
        CHECK(!g.Advance(1500));
        g.Held();                                           // still held: the pause starts over
        CHECK(!g.Advance(1500));
        CHECK(g.Advance(500));
    }

    // ---- the timeline ----
    {
        Timeline t;
        CHECK(t.RiseDue());                                 // a Servant on the pull
        t.RiseDone(false);
        CHECK(t.nextRise == 25000);
        CHECK(t.DueBar() == Bar::None);
        t.Advance(3000);
        CHECK(t.EarthShockDue());
        t.Advance(3000);
        CHECK(t.DueBar() == Bar::Bolt);                     // first bolt at 6 s
        t.BarDone(Bar::Bolt, 11000);
        CHECK(t.nextBolt == 17000);
        t.Advance(9000);                                    // 15 s: the heal
        CHECK(t.DueBar() == Bar::Heal);
        t.BarDone(Bar::Heal, 22000);
        t.Advance(3000);                                    // 18 s: the heal's bar ended; the bolt was due at 17
        CHECK(t.DueBar() == Bar::Bolt);
        t.BarDone(Bar::Bolt, 11000);
        CHECK(t.nextBolt == 28000);                         // max(17 + 11, 18 + 5.5)
        t.Advance(2000);                                    // 20 s: the Shockwave before everything
        CHECK(t.DueBar() == Bar::Shockwave);
        t.nextBolt = 20000;
        CHECK(t.DueBar() == Bar::Shockwave);
        t.BarDone(Bar::Shockwave, Tune::kShockwaveEveryMs(false));
        CHECK(t.nextShockwave == 40000);
        // A beat held far past its due keeps half a period from now (never starves the others).
        t.Advance(30000);                                   // 50 s
        t.BarDone(Bar::Shockwave, 20000);
        CHECK(t.nextShockwave == 60000);
        t.Advance(25000);                                   // 75 s, 15 s late
        t.BarDone(Bar::Shockwave, 20000);
        CHECK(t.nextShockwave == 85000);                    // max(60 + 20, 75 + 10)
        t.BarRetry(Bar::Heal);
        CHECK(t.nextHeal == t.now + Tune::kRetryMs);
        CHECK(t.InMs(Bar::Heal) == Tune::kRetryMs);
        // Heroic rises every 20 s.
        Timeline h;
        h.RiseDone(true);
        CHECK(h.nextRise == 20000);
    }

    // ---- the spec's numbers ----
    CHECK(Tune::kBoltCastMs(false) == 2500 && Tune::kBoltCastMs(true) == 2000);
    CHECK(Tune::kHealCastMs(false) == 3000 && Tune::kHealCastMs(true) == 2000);
    CHECK(Tune::kServantCap == 3);
    CHECK(Tune::kCalcifyMaxStacks == 6);
    // Health is the header's (section 3.6), never restated here.
    CHECK(Health::kAntusul(false) == 159947);
    CHECK(Health::kAntusul(true) == 266666);

    return Report("zf_antusul_test");
}
