// Host tests for UkorzLogic.h (D6): Chief Ukorz Sandscalp and Ruuzlu. Handoff section 5: Fury by percent and its fade,
// the roars, the hold at 30%, the transition; plus the kill order's pick, the executioners, the Lash's chain, Creeping
// Sands and the mesa's spots.
#include "UkorzLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <span>
#include <vector>

using namespace ZulFarrakRework;
using namespace ZfUkorz;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Drives a meter for `ms` in 100 ms ticks with the partner losing `pctPerSec` percent a second.
    FuryEvents Drive(FuryMeter& meter, std::uint64_t& now, std::uint32_t ms, float pctPerSec, bool partnerUp,
        bool heroic, bool vengeance, FuryEvents* sum = nullptr)
    {
        FuryEvents last;
        for (std::uint32_t t = 0; t < ms; t += 100)
        {
            now += 100;
            last = meter.Update(now, 100, pctPerSec / 10.f, partnerUp, heroic, vengeance);
            if (sum)
            {
                sum->gained += last.gained;
                sum->faded += last.faded;
            }
        }
        return last;
    }

    void TestSlice()
    {
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        for (std::uint32_t id : { uint32_t(SPELL_UK_FURY), uint32_t(SPELL_UK_ROAR), uint32_t(SPELL_UK_STORM),
            uint32_t(SPELL_UK_SUNK), uint32_t(SPELL_UK_EXECUTE), uint32_t(SPELL_UK_CALL), uint32_t(SPELL_UK_LASH),
            uint32_t(SPELL_UK_CREEPING), uint32_t(SPELL_UK_VENGEANCE) })
            CHECK(kSpellSlice.Contains(id));
        CHECK(SPELL_UK_VENGEANCE < kSpellSlice.last);
    }

    void TestMesa()
    {
        // The spawns are on the arena, and the slot's arena is the same one.
        CHECK(MesaArena().Contains(kUkorzSpawn.XY(), kUkorzSpawn.z));
        CHECK(ArenaFor(BOSS_UKORZ).Contains(kUkorzSpawn.XY(), kUkorzSpawn.z));
        CHECK(MesaArena().Contains(kRuuzluSpawn.XY(), kRuuzluSpawn.z));
        // Section 7 #34 A: the donut's center is the mesa's open middle, on the floor.
        CHECK(MesaArena().Contains(kMesaDonutCenter.XY(), kMesaDonutCenter.z));
        // The donut's outer edge lies past every corner of the mesa (no safe strip at the rim), and its 30 yd start
        // reaches both spawns (the fight starts inside it).
        float farthest = 0.f;
        for (Vec2 const& p : kMesaPolygon)
            farthest = std::max(farthest, DungeonKit::Distance(p, kMesaDonutCenter.XY()));
        CHECK(farthest < Tune::kCreepOuterYd);
        CHECK(farthest > 45.f);     // G1's 45 yd would leave the far corners outside
        CHECK(DungeonKit::Distance(kUkorzSpawn.XY(), kMesaDonutCenter.XY()) < Tune::kCreepStartYd);
        CHECK(DungeonKit::Distance(kRuuzluSpawn.XY(), kMesaDonutCenter.XY()) < Tune::kCreepStartYd);
    }

    void TestFuryFeed()
    {
        // Normal: a stack per 4% of the partner's health, carried across ticks.
        FuryMeter m;
        std::uint64_t now = 0;
        FuryEvents e = m.Update(now += 100, 100, 3.9f, true, false, true);
        CHECK(m.Stacks() == 0 && e.gained == 0);
        e = m.Update(now += 100, 100, 0.2f, true, false, true);
        CHECK(m.Stacks() == 1 && e.gained == 1);
        CHECK(Near(m.CarryPct(), 0.1f, 0.01f));
        // A big hit gives several stacks at once.
        e = m.Update(now += 100, 100, 12.f, true, false, true);
        CHECK(m.Stacks() == 4 && e.gained == 3);
        // The roar is due at 5, once per fill.
        e = m.Update(now += 100, 100, 4.f, true, false, true);
        CHECK(m.Stacks() == 5 && e.roarDue && !e.full);
        m.UseRoar();
        e = m.Update(now += 100, 100, 4.f, true, false, true);
        CHECK(m.Stacks() == 6 && !e.roarDue);
        // Full at 10, capped there.
        e = m.Update(now += 100, 100, 40.f, true, false, true);
        CHECK(m.Stacks() == Tune::kFuryMaxStacks && e.full && !e.roarDue && e.gained == 4);
        // The Bladestorm empties it and a new fill may roar again.
        m.Empty();
        CHECK(m.Stacks() == 0 && !m.RoarUsed());
        e = m.Update(now += 100, 100, 20.f, true, false, true);
        CHECK(m.Stacks() == 5 && e.roarDue);
        // A landed roar fills the meter.
        m.UseRoar();
        m.Fill();
        CHECK(m.Stacks() == Tune::kFuryMaxStacks);

        // Heroic: a stack per 3%.
        FuryMeter h;
        now = 0;
        e = h.Update(now += 100, 100, 9.f, true, true, false);
        CHECK(h.Stacks() == 3);
    }

    void TestFuryFade()
    {
        // Section 7 #41 A: it fades once the partner lost under 1% in the last 4 s, a stack every 4 s (heroic 5 s).
        FuryMeter m;
        std::uint64_t now = 0;
        m.Update(now += 100, 100, 24.f, true, false, true);
        CHECK(m.Stacks() == 6);
        // Under 1% in 4 s (a dot ticking 0.2% a second): once the big hit leaves the window (4 s), it fades on the
        // normal clock (4 s more).
        FuryEvents sum;
        Drive(m, now, 4000, 0.2f, true, false, true, &sum);
        CHECK(m.Stacks() == 6 && sum.faded == 0);
        Drive(m, now, 4200, 0.2f, true, false, true, &sum);
        CHECK(m.Stacks() == 5 && sum.faded == 1);
        // 1% a second keeps it from fading at all (the window holds 4% > 1%).
        sum = {};
        Drive(m, now, 20000, 1.f, true, false, true, &sum);
        CHECK(sum.faded == 0);
        CHECK(m.Stacks() == 10);        // 20% at 4% a stack: +5
        // Fully quiet: the window empties after 4 s, then a stack every 4 s.
        FuryMeter q;
        now = 0;
        q.Update(now += 100, 100, 20.f, true, false, true);     // 5 stacks, the loss in the window
        CHECK(q.Stacks() == 5);
        sum = {};
        Drive(q, now, 4000, 0.f, true, false, true, &sum);
        CHECK(sum.faded == 0);          // the 20% is still in the window until 4 s have passed
        Drive(q, now, 4100, 0.f, true, false, true, &sum);
        CHECK(sum.faded == 1 && q.Stacks() == 4);
        // Heroic fades every 5 s.
        FuryMeter hq;
        now = 0;
        hq.Update(now += 100, 100, 9.f, true, true, false);
        CHECK(hq.Stacks() == 3);
        sum = {};
        Drive(hq, now, 4000 + 5000, 0.f, true, true, false, &sum);
        CHECK(sum.faded == 1);
        Drive(hq, now, 5000, 0.f, true, true, false, &sum);
        CHECK(sum.faded == 2 && hq.Stacks() == 1);
        // Never below 0.
        Drive(hq, now, 30000, 0.f, true, true, false, &sum);
        CHECK(hq.Stacks() == 0);
    }

    void TestVengeance()
    {
        // Normal, the partner down: no fade, a stack every 3 s; a Bladestorm every 30 s at most.
        FuryMeter m;
        std::uint64_t now = 0;
        m.Update(now += 100, 100, 8.f, true, false, true);
        CHECK(m.Stacks() == 2);
        FuryEvents sum;
        Drive(m, now, 9000, 0.f, false, false, true, &sum);
        CHECK(m.Stacks() == 5 && sum.faded == 0 && sum.gained == 3);
        m.UseRoar();    // kicked
        FuryEvents last = Drive(m, now, 15000, 0.f, false, false, true);
        CHECK(m.Stacks() == 10 && last.full);
        m.Empty();
        Drive(m, now, 29900, 0.f, false, false, true);
        CHECK(m.Stacks() == 9);
        last = Drive(m, now, 100, 0.f, false, false, true);
        CHECK(last.full);
        // Heroic has no Vengeance (the hold replaces it): the meter stays where it is.
        FuryMeter h;
        now = 0;
        h.Update(now += 100, 100, 6.f, true, true, false);
        CHECK(h.Stacks() == 2);
        Drive(h, now, 30000, 0.f, false, true, false);
        CHECK(h.Stacks() == 2);
    }

    void TestFuryFactor()
    {
        CHECK(Near(FuryFactor(0, false), 1.f));
        CHECK(Near(FuryFactor(10, false), 1.3f));
        CHECK(Near(FuryFactor(10, true), 1.4f));
        CHECK(Near(FuryFactor(5, true), 1.2f));
    }

    void TestStackMath()
    {
        // Rule 26: re-run the spec's stack math against section 3.6's health. A meter fills in about 25 s of steady
        // damage on its partner at the normal target (1,431 on 170,000: 0.84% of the total a second); per boss, the
        // spec's 80,000 Ruuzlu loses 1.79% a second, 10 stacks of 4% in 22 s.
        float const specRuuzluPctPerSec = 1431.f / 80000.f * 100.f;
        float const fillSec = Tune::kFuryMaxStacks * Tune::kFuryPartnerPctPerStack.normal / specRuuzluPctPerSec;
        CHECK(fillSec > 20.f && fillSec < 26.f);
        // ...and drains in 40 s (10 stacks, one every 4 s).
        CHECK(Tune::kFuryMaxStacks * Tune::kFuryFadeMs.normal == 40000);
        // A bot group at 2,500 on the built 128,067 Ruuzlu: 1.95% a second, the roar at about 10 s, full at 21 s.
        float const botPctPerSec = 2500.f / static_cast<float>(Health::kRuuzlu.normal) * 100.f;
        float const botFillSec = Tune::kFuryMaxStacks * Tune::kFuryPartnerPctPerStack.normal / botPctPerSec;
        CHECK(botFillSec > 18.f && botFillSec < 24.f);
        // Heroic bots at 5,500 on 233,478: 2.36% a second, 3% a stack: full in about 13 s (switch every 8 s).
        float const hPctPerSec = 5500.f / static_cast<float>(Health::kRuuzlu.heroic) * 100.f;
        float const hFillSec = Tune::kFuryMaxStacks * Tune::kFuryPartnerPctPerStack.heroic / hPctPerSec;
        CHECK(hFillSec > 11.f && hFillSec < 15.f);
    }

    void TestFavored()
    {
        FavorView v;
        // No pick yet, both at 0: Ruuzlu (hitting him feeds Ukorz's empty meter).
        CHECK(PickFavored(std::nullopt, v) == Side::Ruuzlu);
        // Hysteresis: hitting Ruuzlu fed Ukorz to 2: stays; at 3 (margin): turns to Ukorz.
        v.fury[Index(Side::Ukorz)] = 2;
        CHECK(PickFavored(Side::Ruuzlu, v) == Side::Ruuzlu);
        v.fury[Index(Side::Ukorz)] = 3;
        CHECK(PickFavored(Side::Ruuzlu, v) == Side::Ukorz);
        // Back the other way only once Ruuzlu's meter leads by 3.
        v.fury[Index(Side::Ruuzlu)] = 5;
        CHECK(PickFavored(Side::Ukorz, v) == Side::Ukorz);
        v.fury[Index(Side::Ruuzlu)] = 6;
        CHECK(PickFavored(Side::Ukorz, v) == Side::Ruuzlu);
        // The health guard: never more than 8% below the other.
        FavorView g;
        g.healthPct[Index(Side::Ruuzlu)] = 60.f;
        g.healthPct[Index(Side::Ukorz)] = 69.f;
        CHECK(PickFavored(Side::Ruuzlu, g) == Side::Ukorz);
        g.healthPct[Index(Side::Ukorz)] = 67.f;
        CHECK(PickFavored(Side::Ruuzlu, g) == Side::Ruuzlu);
        // ...and a Fury switch never goes to a boss already 8% lower.
        g.healthPct[Index(Side::Ukorz)] = 50.f;
        g.fury[Index(Side::Ukorz)] = 9;
        CHECK(PickFavored(Side::Ruuzlu, g) == Side::Ruuzlu);
        // A held boss (heroic 30%) is never favored while the other is not.
        FavorView hold;
        hold.held[Index(Side::Ukorz)] = true;
        hold.fury[Index(Side::Ruuzlu)] = 10;
        CHECK(PickFavored(Side::Ukorz, hold) == Side::Ruuzlu);
        // One standing: that one; none: nothing.
        FavorView one;
        one.up[Index(Side::Ruuzlu)] = false;
        CHECK(PickFavored(Side::Ruuzlu, one) == Side::Ukorz);
        one.up[Index(Side::Ukorz)] = false;
        CHECK(!PickFavored(Side::Ukorz, one).has_value());
    }

    void TestExecutioners()
    {
        // Section 7 #42 A.
        ExecutionerView v;
        v.ruuzluStands = v.ruuzluFree = v.ukorzStands = v.ukorzFree = true;
        CHECK(ExecutionerFor(v) == Side::Ruuzlu);
        // Normal: Ruuzlu busy, Ukorz never steps in while Ruuzlu stands.
        v.ruuzluFree = false;
        CHECK(!ExecutionerFor(v).has_value());
        // Heroic phase 1: the two share.
        v.heroicPhaseOne = true;
        CHECK(ExecutionerFor(v) == Side::Ukorz);
        v.ukorzFree = false;
        CHECK(!ExecutionerFor(v).has_value());
        // Ruuzlu gone: Ukorz, on both difficulties, when free.
        ExecutionerView alone;
        alone.ukorzStands = true;
        alone.ukorzFree = true;
        CHECK(ExecutionerFor(alone) == Side::Ukorz);
        alone.ukorzFree = false;
        CHECK(!ExecutionerFor(alone).has_value());
        alone.ukorzStands = false;
        alone.ukorzFree = true;
        CHECK(!ExecutionerFor(alone).has_value());
    }

    void TestHold()
    {
        std::uint32_t const max = Health::kUkorz.heroic;
        std::uint32_t const line = HoldHealth(max, Tune::kHoldPct);
        CHECK(line == 80024);           // ceil(266,745 x 0.3)
        CHECK(static_cast<double>(line) >= max * 0.3);
        // A hit that would cross the line stops on it; once there, nothing gets through.
        CHECK(HoldDamage(100000, max, 50000, Tune::kHoldPct) == 100000 - line);
        CHECK(HoldDamage(100000, max, 5000, Tune::kHoldPct) == 5000);
        CHECK(HoldDamage(line, max, 5000, Tune::kHoldPct) == 0);
        CHECK(AtHold(line, max, Tune::kHoldPct));
        CHECK(!AtHold(line + 1, max, Tune::kHoldPct));
        CHECK(!AtHold(0, max, Tune::kHoldPct));
        // UK10: Ukorz takes Ruuzlu's remaining life: about 150k in all at the built heroic health (SP: about 112k on
        // its own numbers), never past his maximum.
        std::uint32_t const ruuzluLine = HoldHealth(Health::kRuuzlu.heroic, Tune::kHoldPct);
        std::uint32_t const called = CalledHealth(line, ruuzluLine, max);
        CHECK(called == line + ruuzluLine);
        CHECK(called > 145000 && called < 155000);
        CHECK(CalledHealth(max - 10, 1000, max) == max);
    }

    void TestLash()
    {
        // A chain: 0 struck, 1 within 8 of 0, 2 within 8 of 1 (not of 0), 3 far, 4 within 8 of 2.
        std::vector<Vec2> pts{ { 0.f, 0.f }, { 7.f, 0.f }, { 14.f, 0.f }, { 40.f, 40.f }, { 14.f, 7.f } };
        std::vector<std::size_t> chain = LashChain(pts, 0, Tune::kLashRadiusYd, Tune::kLashMaxJumps);
        CHECK(chain.size() == 4);
        CHECK(chain[0] == 0 && chain[1] == 1 && chain[2] == 2 && chain[3] == 4);
        // Spread players: only the first.
        std::vector<Vec2> spread{ { 0.f, 0.f }, { 9.f, 0.f }, { 0.f, 9.f }, { -9.f, 0.f }, { 0.f, -9.f } };
        CHECK(LashChain(spread, 2, Tune::kLashRadiusYd, Tune::kLashMaxJumps).size() == 1);
        // Stacked: up to 4 jumps (5 players), never more.
        std::vector<Vec2> stack(7, Vec2{ 1.f, 1.f });
        CHECK(LashChain(stack, 3, Tune::kLashRadiusYd, Tune::kLashMaxJumps).size() == 5);
        CHECK(LashChain(stack, 9, Tune::kLashRadiusYd, Tune::kLashMaxJumps).empty());
    }

    void TestCreep()
    {
        CHECK(CreepStep(0) == 0 && Near(CreepInnerYd(0), 30.f));
        CHECK(CreepStep(19999) == 0);
        CHECK(CreepStep(20000) == 1 && Near(CreepInnerYd(1), 25.f));
        CHECK(CreepStep(119999) == 5 && Near(CreepInnerYd(5), 5.f));
        // Ruling 45: no floor; it shuts at 120 s and stays shut.
        CHECK(CreepStep(120000) == 6 && Near(CreepInnerYd(6), 0.f));
        CHECK(CreepStep(600000) == 6);
        CHECK(Near(CreepBoundsYd(30.f), 29.f));
        CHECK(Near(CreepBoundsYd(0.f), 3.f));
        // SP's space check at 20 yd (about 45 s in at the target): 1,257 sq yd of safe circle.
        float const area20 = 3.14159265f * CreepInnerYd(2) * CreepInnerYd(2);
        CHECK(area20 > 1200.f && area20 < 1300.f);

        // F-1 MI-4: the bots' spots while the donut is up are the safe circle clipped to the mesa: no spot behind the
        // walls (the bare 29 yd circle has some), and every mesa point inside the circle kept (a 0.5 yd grid; the
        // 32-gon's rim band, 0.15 yd at 29 yd, is skipped).
        Vec2 const c = kMesaDonutCenter.XY();
        for (std::uint32_t step = 0; step <= 6; ++step)
        {
            float const r = CreepBoundsYd(CreepInnerYd(step));
            std::vector<Vec2> const safe = CreepSafeFloor(r);
            CHECK(safe.size() >= 3);
            std::uint32_t outside = 0;
            std::uint32_t lost = 0;
            std::uint32_t bareOutside = 0;
            for (float x = c.x - r; x <= c.x + r; x += 0.5f)
                for (float y = c.y - r; y <= c.y + r; y += 0.5f)
                {
                    Vec2 const p{ x + 0.13f, y + 0.07f };
                    float const d = DungeonKit::Distance(p, c);
                    bool const mesa = DungeonKit::PointInPolygon(kMesaPolygon, p);
                    bool const in = DungeonKit::PointInPolygon(std::span<Vec2 const>(safe), p);
                    bareOutside += d < r && !mesa ? 1 : 0;
                    outside += in && !mesa ? 1 : 0;
                    lost += !in && mesa && d < r - 0.2f ? 1 : 0;
                }
            CHECK(outside == 0);
            CHECK(lost == 0);
            if (step == 0)
                CHECK(bareOutside > 0);     // the defect the clip removes
            for (Vec2 const& v : safe)
                CHECK(DungeonKit::Distance(v, c) <= r + 0.01f);
        }
    }

    void TestTrailAndBeats()
    {
        CHECK(TrailDrops(1.9f) == 0);
        CHECK(TrailDrops(2.f) == 1);
        CHECK(TrailDrops(6.5f) == 3);
        // A spin's walk drops at most 23 circles (9 s at 5 yd/s), under the cap.
        CHECK(TrailDrops(Tune::kStormRoaredSpinMs / 1000.f * Tune::kStormWalkYdS) <= Tune::kTrailCap);
        // RB-17: a beat on time keeps its period; a late one waits at least half a period.
        CHECK(NextDue(20000, 20000, 20000) == 40000);
        CHECK(NextDue(20000, 20000, 35000) == 45000);
        CHECK(NextDue(20000, 20000, 21000) == 40000);
    }
}

int main()
{
    TestSlice();
    TestMesa();
    TestFuryFeed();
    TestFuryFade();
    TestVengeance();
    TestFuryFactor();
    TestStackMath();
    TestFavored();
    TestExecutioners();
    TestHold();
    TestLash();
    TestCreep();
    TestTrailAndBeats();
    return Report("zf_ukorz_test");
}
