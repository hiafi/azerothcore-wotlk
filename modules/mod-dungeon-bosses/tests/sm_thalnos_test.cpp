// Host tests for ThalnosLogic.h (D4: Bloodmage Thalnos): the slice and the arena, Blood Ritual's stacks (thresholds,
// costs, the normal cap), the Blood Nova interrupt machine (the empowered nova's restart), Blood Brand's gate, the
// beats, the crypt's floor and Blood Lance's wall, the hard mode's threshold.
#include "ThalnosLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmThalnos;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation; twenty ids, all distinct, 212440-212459.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 212440 && kSpellSlice.last == 212479);
    std::set<std::uint32_t> const spells{ SPELL_TH_BLOOD_RITUAL, SPELL_TH_HANDS_RUN_RED, SPELL_TH_BLOOD_BOLT,
        SPELL_TH_BLOOD_LANCE, SPELL_TH_BLOOD_LANCE_LINE, SPELL_TH_FLAME_SPIKE_CAST, SPELL_TH_FLAME_SPIKE,
        SPELL_TH_FLAME_SPIKE_PILLAR, SPELL_TH_FLAME_SPIKE_POOL, SPELL_TH_FLAME_SPIKE_LOOK, SPELL_TH_BOILING_BLOOD,
        SPELL_TH_BOILING_BLOOD_SPLASH, SPELL_TH_BOILING_BLOOD_BURST, SPELL_TH_BLOOD_NOVA_CAST,
        SPELL_TH_EMPOWERED_NOVA_CAST, SPELL_TH_BLOOD_NOVA_RESTART, SPELL_TH_BLOOD_NOVA, SPELL_TH_EMPOWERED_NOVA,
        SPELL_TH_BLOOD_BRAND, SPELL_TH_FLAME_SPIKE_ERUPT };
    CHECK(spells.size() == 20);
    for (std::uint32_t id : spells)
        CHECK(kSpellSlice.Contains(id));
    CHECK(*spells.begin() == 212440);
    CHECK(*spells.rbegin() == 212459);
    // The retired stock spells are outside the slice (his versions are copies, rule 15).
    for (std::uint32_t stock : { SPELL_STOCK_SHADOW_BOLT, SPELL_STOCK_FLAME_SPIKE, SPELL_STOCK_FLAME_SHOCK,
        SPELL_STOCK_FIRE_NOVA })
        CHECK(!kSpellSlice.Contains(stock));

    // Bloodmage Thalnos spawns kThalnosSpawn, inside the arena and on the crypt's floor (his nook); wave 1; the hard
    // mode's kill slot; the Desecration's arena holds the crypt and the lawn.
    CHECK(ThalnosArena().Contains(kThalnosSpawn.XY(), kThalnosSpawn.z));
    CHECK(ArenaFor(BOSS_THALNOS).Contains(kThalnosSpawn.XY(), kThalnosSpawn.z));
    CHECK(OnCryptFloor(kThalnosSpawn.XY()));
    CHECK(kThalnosSpawn.z >= kCryptZMin && kThalnosSpawn.z <= kCryptZMax);
    CHECK(!IsWave2Boss(BOSS_THALNOS));
    CHECK(HardModeKillSlot(BOSS_THALNOS) == BOSS_DESECRATION);
    CHECK(DesecrationArena().Contains(kThalnosSpawn.XY(), kThalnosSpawn.z));
    CHECK(DesecrationArena().Contains(kLawnCenter, kCouncilLawn.z));
    CHECK(!ThalnosArena().Contains(kLawnCenter, kCouncilLawn.z));

    // Text groups: 0-2 stock, 3 new (his emote), 4 the Desecration's (D4H), inside S0's recorded range.
    bool rangeFound = false;
    for (TextRange const& r : kTextRanges)
        if (r.entry == NPC_THALNOS)
        {
            rangeFound = true;
            CHECK(r.first == SAY_AGGRO && r.last == SAY_WAKE_THEM_ALL);
            CHECK(r.firstNew == EMOTE_HANDS_RUN_RED);
        }
    CHECK(rangeFound);
    CHECK(SAY_NO_REST == 1 && SAY_KILL == 2);
    CHECK(kKillYellGapMs == 5000);

    // ---- TH1 Blood Ritual ----
    CHECK(CostOf(Empowered::Lance).needs == 3 && CostOf(Empowered::Lance).spends == 1);
    CHECK(CostOf(Empowered::Spike).needs == 3 && CostOf(Empowered::Spike).spends == 2);
    CHECK(CostOf(Empowered::Boil).needs == 4 && CostOf(Empowered::Boil).spends == 2);
    CHECK(CostOf(Empowered::Nova).needs == 5 && CostOf(Empowered::Nova).spends == 3);
    for (Empowered e : { Empowered::Lance, Empowered::Spike, Empowered::Boil, Empowered::Nova })
        CHECK(CostOf(e).spends < CostOf(e).needs);      // "needs a number held, spends fewer"
    CHECK(StackCap(false) == 10);
    CHECK(StackCap(true) == kAuraStackLimit);
    {
        Ritual r;
        r.Reset(false);
        CHECK(r.Stacks() == 0);
        CHECK(!r.Holds(Empowered::Lance));
        r.Add(1);                                       // a plain bolt on the tank
        r.Add(1);
        CHECK(r.Stacks() == 2 && !r.Holds(Empowered::Lance));
        r.Add(1);
        CHECK(r.Holds(Empowered::Lance) && r.Holds(Empowered::Spike));
        CHECK(!r.Holds(Empowered::Boil) && !r.Holds(Empowered::Nova));
        CHECK(r.Spend(Empowered::Lance) == 2);          // a Lance: 3 -> 2
        CHECK(!r.Holds(Empowered::Lance));
        r.Add(5);                                       // a missed nova: 5 players
        CHECK(r.Stacks() == 7 && r.Holds(Empowered::Nova));
        CHECK(r.Spend(Empowered::Nova) == 4);
        r.Add(20);                                      // capped at 10 on normal
        CHECK(r.Stacks() == 10);
        CHECK(r.Gained() == 3 + 5 + 6);
        CHECK(r.Spent() == 1 + 3);
        r.Set(50);
        CHECK(r.Stacks() == 10);
        r.Set(1);
        CHECK(r.Spend(Empowered::Boil) == 0);           // never below 0
    }
    {
        Ritual r;
        r.Reset(true);                                  // heroic: no cap
        r.Add(30);
        CHECK(r.Stacks() == 30);
        r.Add(1000);
        CHECK(r.Stacks() == kAuraStackLimit);
        r.Reset(true);
        CHECK(r.Stacks() == 0 && r.Gained() == 0 && r.Spent() == 0 && r.Heroic());
    }

    // ---- TH2 Blood Bolt / Lance numbers ----
    CHECK(kBoltCastMs == 2500);
    CHECK(Near(kBoltTankPct(false), 20.f) && Near(kBoltTankPct(true), 30.f));
    CHECK(Near(kLanceTankPct(false), 30.f) && Near(kLanceTankPct(true), 40.f));
    CHECK(Near(kLanceLinePct(false), 35.f) && Near(kLanceLinePct(true), 45.f));
    CHECK(Near(kLanceWidth, 4.f) && Near(kLanceMaxYd, 30.f));
    CHECK(kLanceResolveLagMs > 0 && kLanceResolveLagMs < 500);

    // ---- TH3 Flame Spike ----
    CHECK(kSpikeCastMs == 2000 && kSpikeMarkerMs == 1500);
    CHECK(Near(kSpikeRadius, 4.f));
    CHECK(Near(kSpikePillarPct(false), 35.f) && Near(kSpikePillarPct(true), 45.f));
    CHECK(Near(kSpikePoolPct(false), 5.f) && Near(kSpikePoolPct(true), 8.f));
    CHECK(kSpikePoolMs(false) == 20000 && kSpikePoolMs(true) == 30000);
    CHECK(SpikeTargets(false) == 1 && SpikeTargets(true) == 3);
    CHECK(kSpikeAvoidPoolYd > kSpikeRadius);
    // Space math (GY): two plain pools of 4 yd under 20% of the crypt, four under 40%.
    float const pool = 3.14159f * kSpikeRadius * kSpikeRadius;
    float const crypt = PolygonArea(kCryptFloor);
    CHECK(2.f * pool / crypt < 0.20f);
    CHECK(4.f * pool / crypt < 0.40f);

    // ---- TH4 Boiling Blood ----
    CHECK(kBoilMs == 5000);
    CHECK(Near(kBoilRadius(false), 8.f) && Near(kBoilRadius(true), 10.f));
    CHECK(Near(kBoilCarrierPct(false), 25.f) && Near(kBoilCarrierPct(true), 35.f));
    CHECK(Near(kBoilSplashPct(false), 35.f) && Near(kBoilSplashPct(true), 45.f));
    CHECK(BoilCarriers(false) == 1 && BoilCarriers(true) == 2);
    // NM: one carrier at an end of the crypt (y 1402 or 1432) leaves the middle band (y 1410-1424) clear on normal.
    CHECK(OnCryptFloor({ 1808.f, 1430.f }) && OnCryptFloor({ 1808.f, 1401.f }));
    CHECK(1430.f - kBoilRadius(false) >= 1410.f + 1.f);

    // ---- TH5 Blood Nova: the interrupt machine ----
    CHECK(kNovaCastMs == 3000 && kNovaRestartCastMs == 2000);
    CHECK(Near(kNovaPct(false), 15.f) && Near(kNovaPct(true), 20.f));
    CHECK(Near(kEmpoweredNovaPct(false), 25.f) && Near(kEmpoweredNovaPct(true), 35.f));
    CHECK(NovaStageOf(SPELL_TH_BLOOD_NOVA_CAST) == NovaStage::Plain);
    CHECK(NovaStageOf(SPELL_TH_EMPOWERED_NOVA_CAST) == NovaStage::Empowered);
    CHECK(NovaStageOf(SPELL_TH_BLOOD_NOVA_RESTART) == NovaStage::Restart);
    CHECK(NovaStageOf(SPELL_TH_BLOOD_BOLT) == NovaStage::Idle);
    CHECK(NovaStageOf(SPELL_TH_BLOOD_NOVA) == NovaStage::Idle);
    {
        NovaState n;                                    // a plain nova that lands
        CHECK(!n.Busy());
        n.StartPlain();
        CHECK(n.Busy());
        CHECK(n.Finished(NovaStage::Plain) == NovaOutcome::PlainLands);
        CHECK(!n.Busy());
        CHECK(n.Finished(NovaStage::Plain) == NovaOutcome::None);       // reported again: nothing
        CHECK(n.Kicked(NovaStage::Plain) == NovaOutcome::None);
    }
    {
        NovaState n;                                    // a plain nova kicked: nothing at all
        n.StartPlain();
        CHECK(n.Kicked(NovaStage::Plain) == NovaOutcome::Stopped);
        CHECK(!n.Busy());
        CHECK(n.Kicked(NovaStage::Plain) == NovaOutcome::None);
    }
    {
        NovaState n;                                    // the empowered nova lands: the big hit
        n.StartEmpowered();
        CHECK(n.Finished(NovaStage::Plain) == NovaOutcome::None);       // a stray id
        CHECK(n.Finished(NovaStage::Empowered) == NovaOutcome::EmpoweredLands);
        CHECK(!n.Busy());
    }
    {
        NovaState n;                                    // the double interrupt (hub ruling 54)
        n.StartEmpowered();
        CHECK(n.Kicked(NovaStage::Empowered) == NovaOutcome::Restart);  // the blood stripped
        CHECK(n.Stage() == NovaStage::RestartPending && n.Busy());
        CHECK(n.Kicked(NovaStage::Empowered) == NovaOutcome::None);     // the engine's repeat: no second restart
        CHECK(n.Finished(NovaStage::Empowered) == NovaOutcome::None);
        n.StartRestart();
        CHECK(n.Stage() == NovaStage::Restart);
        CHECK(n.Kicked(NovaStage::Restart) == NovaOutcome::Stopped);    // the second interrupt stops it
        CHECK(!n.Busy());
    }
    {
        NovaState n;                                    // one interrupt only: the plain restart lands
        n.StartEmpowered();
        CHECK(n.Kicked(NovaStage::Empowered) == NovaOutcome::Restart);
        n.StartRestart();
        CHECK(n.Finished(NovaStage::Restart) == NovaOutcome::PlainLands);
        CHECK(!n.Busy());
    }
    {
        NovaState n;                                    // the restart cannot start (silenced): over
        n.StartEmpowered();
        n.Kicked(NovaStage::Empowered);
        n.RestartFailed();
        CHECK(!n.Busy());
        n.RestartFailed();                              // harmless when idle
        CHECK(!n.Busy());
        n.StartPlain();
        n.RestartFailed();                              // only a pending restart is dropped
        CHECK(n.Stage() == NovaStage::Plain);
        n.Clear();
        CHECK(!n.Busy());
    }

    // ---- TH6 Blood Brand ----
    CHECK(kBrandMs == 12000);
    {
        BrandGate g;
        CHECK(g.Take(5000));
        CHECK(!g.Take(5000));
        CHECK(!g.Take(5999));
        CHECK(g.Take(6000));
        CHECK(!g.Take(6500));
        CHECK(g.Take(9000));
        // At most one a second over the 12 s brand: 12 or 13 stacks at the most (a hit at 0 and one each second).
        BrandGate h;
        std::uint32_t taken = 0;
        for (std::uint64_t t = 0; t <= kBrandMs; t += 100)
            taken += h.Take(t) ? 1 : 0;
        CHECK(taken == kBrandMs / kBrandStackGapMs + 1);
    }

    // ---- The beats (GY build spec first / cooldown) ----
    CHECK(kBoltBeat.firstMs == 2000 && kBoltBeat.everyMs(false) == 8000 && kBoltBeat.everyMs(true) == 6000);
    CHECK(kSpikeBeat.firstMs == 6000 && kSpikeBeat.everyMs(false) == 15000 && kSpikeBeat.everyMs(true) == 15000);
    CHECK(kBoilBeat.firstMs == 10000 && kBoilBeat.everyMs(false) == 15000);
    CHECK(kNovaBeat.firstMs == 15000 && kNovaBeat.everyMs(false) == 20000 && kNovaBeat.everyMs(true) == 20000);
    CHECK(kBrandBeat.firstMs == 12000 && kBrandBeat.everyMs(true) == 20000);
    // A bolt's 2.5 s bar fits between bolts on heroic (6 s).
    CHECK(kBoltCastMs < kBoltBeat.everyMs(true));
    {
        BeatClock c;
        CHECK(!c.Due(0));
        c.Start(0, 2000);
        CHECK(!c.Due(1999) && c.Due(2000));
        c.Fired(2500, 8000);                            // start to start: due at 10000
        CHECK(c.DueMs() == 10000);
        c.Fired(30000, 8000);                           // late: never in the past
        CHECK(c.DueMs() == 38000);
        c.Stop();
        CHECK(!c.Due(100000));
    }

    // ---- The crypt's floor and Blood Lance's wall ----
    // NM: 584 sq yd on the mesh; the polygon is drawn half a yard inside it.
    CHECK(crypt > 520.f && crypt < 640.f);
    // On the floor: portal P1's free disc (1807.2, 1417.8) and the two other measured discs; off it: the stair, the
    // court above, the lawn.
    CHECK(OnCryptFloor({ 1807.2f, 1417.8f }));
    CHECK(OnCryptFloor({ 1807.2f, 1425.8f }));
    CHECK(OnCryptFloor({ 1807.8f, 1405.8f }));
    CHECK(!OnCryptFloor({ 1795.f, 1415.f }));
    CHECK(!OnCryptFloor({ 1788.5f, 1417.f }));
    CHECK(!OnCryptFloor(kLawnCenter));
    CHECK(!OnCryptFloor({ 1822.f, 1425.f }));           // beside his nook: rock
    bool p1Found = false;
    for (WingPortal const& p : kPortals)
        if (p.id == 1)
        {
            p1Found = true;
            CHECK(OnCryptFloor(p.spot.XY()));
        }
    CHECK(p1Found);
    // The Lance from his spot through a tank south of him reaches the crypt's south wall (x 1800.5): about 20 yd, not
    // the spec's 30 (NM: "about 24 yd" at most).
    Vec2 const boss = kThalnosSpawn.XY();
    float const south = LanceLength(Ground::Crypt, boss, { 1812.f, boss.y });
    CHECK(Near(south, boss.x - 1800.5f, 0.2f));
    CHECK(south < kLanceMaxYd);
    // From the middle through a tank toward a corner: clipped by the wall, always past the tank.
    Vec2 const mid{ 1810.f, 1416.f };
    Vec2 const tank{ 1806.f, 1424.f };
    float const corner = LanceLength(Ground::Crypt, mid, tank);
    CHECK(corner >= DungeonKit::Distance(mid, tank) + kLanceMinBehindYd - 0.01f);
    CHECK(corner <= kLanceMaxYd);
    CHECK(OnCryptFloor(DungeonKit::Advance(mid, DungeonKit::BearingTo(mid, tank), corner - 0.5f)));
    // A tank in the nook's mouth, him deep in it: the line goes out into the room (the nook's walls never cut it).
    float const nook = LanceLength(Ground::Crypt, { 1823.f, 1415.8f }, { 1817.f, 1415.8f });
    CHECK(nook > 15.f);
    // The lawn, a tank on him, a tank off the floor: the spec's 30 yd.
    CHECK(Near(LanceLength(Ground::Lawn, kLawnCenter, { kLawnCenter.x + 3.f, kLawnCenter.y }), kLanceMaxYd));
    CHECK(Near(LanceLength(Ground::Crypt, boss, boss), kLanceMaxYd));
    CHECK(Near(LanceLength(Ground::Crypt, mid, { 1795.f, 1415.f }), kLanceMaxYd));
    // Every Lance stays within 30 yd, wherever the tank stands on the floor.
    for (float x = 1801.f; x <= 1818.f; x += 1.f)
        for (float y = 1400.f; y <= 1432.f; y += 1.f)
            if (OnCryptFloor({ x, y }))
                CHECK(LanceLength(Ground::Crypt, mid, { x, y }) <= kLanceMaxYd);

    // ---- The lawn and the hard mode's threshold ----
    CHECK(Near(kLawnCenter.x, 1798.5f) && Near(kLawnCenter.y, 1348.5f));
    CHECK(kLawnBoundsYd <= kLawnArenaYd);
    CHECK(kCouncilLawn.z >= kLawnZMin && kCouncilLawn.z <= kLawnZMax);
    // RF-1 m-4: the lawn is cut at Ironspine's yard edge (y 1317): the bounds stay inside, his side is off the lawn.
    CHECK(Near(kLawnSouthCutY, kIronspineYardNorthY));
    CHECK(kLawnCenter.y - kLawnSouthCutY > kLawnBoundsYd);
    CHECK(OnLawnFloor(kLawnCenter, kCouncilLawn.z));
    CHECK(OnLawnFloor({ kLawnCenter.x, kLawnSouthCutY + 1.f }, kCouncilLawn.z));
    CHECK(!OnLawnFloor({ kLawnCenter.x, kLawnSouthCutY - 1.f }, kCouncilLawn.z));
    CHECK(!OnLawnFloor(kIronspineHome.XY(), kIronspineHome.z));
    CHECK(OnLawnFloor({ kLawnCenter.x, kLawnCenter.y + kLawnArenaYd - 1.f }, kCouncilLawn.z));
    CHECK(!OnLawnFloor(kLawnCenter, kThalnosSpawn.z));
    CHECK(!DesecrationArena().Contains({ kLawnCenter.x, kLawnSouthCutY - 1.f }, kCouncilLawn.z));
    bool p1hFound = false;
    for (WingPortal const& p : kPortals)
        if (p.id == 2)
        {
            p1hFound = true;
            CHECK(DungeonKit::Distance(p.spot.XY(), kLawnCenter) <= kLawnBoundsYd);
        }
    CHECK(p1hFound);
    CHECK(Near(kNoRestPct, 75.f));

    // ---- The ground's mechanics (R-1-GY MJ-1): the 75% teleport cancels every crypt-bound one still live ----
    {
        GroundedHandles<int> grounded;
        grounded.Add(Ground::Crypt, 1);     // a pool (30 s heroic)
        grounded.Add(Ground::Crypt, 2);     // a pillar
        grounded.Add(Ground::Crypt, 3);     // a boil RunOut
        CHECK(grounded.Size() == 3 && grounded.CountOn(Ground::Crypt) == 3);
        // Nothing to cancel while the ground stays.
        CHECK(grounded.Leave(Ground::Crypt).empty());
        CHECK(grounded.Size() == 3);
        std::vector<int> const gone = grounded.Leave(Ground::Lawn);
        CHECK(gone.size() == 3 && gone[0] == 1 && gone[1] == 2 && gone[2] == 3);
        // After the move no live mechanic keeps the crypt's bounds: every bound left is the lawn's.
        CHECK(grounded.CountOn(Ground::Crypt) == 0 && grounded.Size() == 0);
        grounded.Add(Ground::Lawn, 4);      // a lawn spike: kept on the lawn
        grounded.Add(Ground::Lawn, 5);
        CHECK(grounded.Leave(Ground::Lawn).empty());
        CHECK(grounded.CountOn(Ground::Lawn) == 2);
        // Prune drops the resolved ones only (N-1: a trim never drops a live handle).
        grounded.Prune([](int h) { return h != 4; });
        CHECK(grounded.Size() == 1 && grounded.CountOn(Ground::Lawn) == 1);
        grounded.Clear();
        CHECK(grounded.Size() == 0);
    }

    return Report("sm_thalnos_test");
}
