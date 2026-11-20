// Host tests for ArgelmachLogic.h (D15: Golem Lord Argelmach): the slice, the spec's numbers, the golems and their
// pedestals, the wake order, the chamber, the Arcane Overcharge spot, the orb's fixed flight, Empowered, Beat.
#include "ArgelmachLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdArgelmach;

namespace
{
    // A deterministic [0, 1) sequence for the spot pick.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>(state >> 8) / static_cast<float>(1u << 24);
        }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // ---- The slice: every spell inside it, inside the dungeon's reservation; no stock id is reused (rule 15). ----
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 211330 && kSpellSlice.last == 211369);
    std::uint32_t const spells[] = { SPELL_AR_CHAIN_LIGHTNING, SPELL_AR_SHOCK, SPELL_AR_LIGHTNING_SHIELD,
        SPELL_AR_GOLEM_WAKES, SPELL_AR_CHEMICAL_BOMB, SPELL_AR_CHEMICAL_CLOUD, SPELL_AR_CHEMICAL_CLOUD_LOOK,
        SPELL_AR_POISON_MIST, SPELL_AR_LETHAL_ATTRACTION, SPELL_AR_LETHAL_JOLT, SPELL_AR_LIVEWIRE,
        SPELL_AR_LIVEWIRE_PULSE, SPELL_AR_LIVEWIRE_BURST, SPELL_AR_POWER_SURGE, SPELL_AR_OVERCHARGED,
        SPELL_AR_EMPOWERED, SPELL_AR_OVERCHARGE_BOMB, SPELL_AR_OVERCHARGE_CATCH, SPELL_AR_OVERCHARGE_BLAST,
        SPELL_AR_STATUE };
    std::set<std::uint32_t> unique;
    for (std::uint32_t id : spells)
    {
        CHECK(id >= kSpellSlice.first && id <= kSpellSlice.last);
        CHECK(id != kStockChainLightning && id != kStockShock && id != kStockLightningShield && id != kSpellStoned);
        unique.insert(id);
    }
    CHECK(unique.size() == sizeof(spells) / sizeof(spells[0]));
    CHECK(SPELL_AR_OVERCHARGE_BLAST == 211348);
    CHECK(SPELL_AR_STATUE == 211349);           // R-2-A MA-1: the statue look the golems' immunity set lets land

    // ---- The spawn and the arena (S0's stub checks). ----
    CHECK(ArgelmachArena().Contains(kArgelmachSpawn.XY(), kArgelmachSpawn.z));
    CHECK(ArenaFor(BOSS_ARGELMACH).Contains(kArgelmachSpawn.XY(), kArgelmachSpawn.z));

    // ---- Health (handoff 3.6): 150k / 220k; the golems 25k / 37k at level 55 (the DT rows). ----
    CHECK(kBossHealth.normal == 150000 && kBossHealth.heroic == 220000);
    CHECK(std::ceil(kPaladin55Base * 71.736) >= 149999 && std::ceil(kPaladin55Base * 71.736) <= 150001);
    CHECK(kGolemHealth.normal == 25000 && kGolemHealth.heroic == 37000);
    CHECK(static_cast<std::uint32_t>(std::ceil(kWarrior55Base * 9.56388)) == 25000);

    // ---- The spec's numbers (S3 Build spec AR1-AR10). ----
    CHECK(kChainFirstMs == 14000 && kChainEveryMs == 15000 && kChainCastMs == 3000 && kChainTargets == 5);
    CHECK(kShockFirstMs == 6000 && kShockEveryMs == 7000);
    CHECK(kShieldEveryMs == 45000);
    CHECK(kBombFirstMs == 5000 && kBombEveryMs.normal == 15000 && kBombEveryMs.heroic == 12000);
    CHECK(kBombMarks == 2 && kBombWarnMs == 4000 && Near(kCloudRadiusYd, 5.f) && kCloudLifeMs == 30000);
    CHECK(Near(kCloudPct.normal, 6.f) && Near(kCloudPct.heroic, 9.f) && kCloudTickMs == 1000);
    CHECK(kMistFirstMs == 8000 && kMistEveryMs == 20000 && kMistCastMs == 2000 && Near(kMistPct, 25.f));
    CHECK(Near(kMistTickPct, 2.f) && kMistTickMs == 2000 && kMistDotMs == 10000);
    CHECK(kTetherFirstMs == 5000 && kTetherEveryMs.normal == 20000 && kTetherEveryMs.heroic == 15000);
    CHECK(kTetherMs == 8000 && Near(kTetherRangeYd, 5.f));
    CHECK(Near(kTetherPct.normal, 40.f) && Near(kTetherPct.heroic, 60.f));
    CHECK(kLivewireFirstMs == 8000 && kLivewireEveryMs == 20000 && kLivewireMs == 12000 && kLivewirePulseMs == 2000);
    CHECK(Near(kLivewireRadiusYd, 8.f) && Near(kLivewirePulsePct, 4.f) && Near(kLivewireBurstPct, 30.f));
    CHECK(kOrbFirstMs == 5000 && kOrbEveryMs.normal == 20000 && kOrbEveryMs.heroic == 15000 && kOrbTravelMs == 10000);
    CHECK(Near(kOrbPopPct.normal, 10.f) && Near(kOrbPopPct.heroic, 15.f));
    CHECK(Near(kOverchargedPct, 10.f) && kOverchargedMaxStacks == 3 && kOverchargedMs == 30000);
    CHECK(Near(kEmpoweredPctPerStack, 15.f) && kEmpoweredMaxStacks == 5 && kEmpoweredMs == 30000);
    CHECK(kOverchargeFirstMs == 8000 && kOverchargeEveryMs == 20000 && kOverchargeWarnMs == 4000);
    CHECK(Near(kOverchargeCatchPct, 30.f) && Near(kOverchargeBlastPct, 40.f) && Near(kOverchargeRadiusYd, 3.f));
    CHECK(kSignatureDelayMs == 5000);

    // ---- Tether, Livewire. ----
    CHECK(TetherHolds(0.f) && TetherHolds(5.f) && !TetherHolds(5.01f));
    CHECK(InLivewire(8.f, 0.f) && InLivewire(0.f, -6.f) && !InLivewire(8.01f, 0.f) && !InLivewire(1.f, 6.5f));
    // The carrier is never the tank (orchestrator default 2026-11-17) unless the tank is alone in the fight.
    CHECK(!kLivewireMarksTank);
    {
        DungeonKit::PickRule const rule = LivewirePickRule();
        std::vector<DungeonKit::PickCandidate> group(2);
        group[0].id = 1;
        group[0].tank = true;
        group[1].id = 2;
        for (std::uint32_t roll = 0; roll < 2; ++roll)
        {
            auto const pick = DungeonKit::PickFrom(group, rule, [roll](std::uint32_t n) { return roll % n; });
            CHECK(pick && *pick == 1);
        }
        group.resize(1);
        auto const solo = DungeonKit::PickFrom(group, rule, [](std::uint32_t) { return 0u; });
        CHECK(solo && *solo == 0);
    }

    // ---- Empowered: +15% a stack, capped at 5; his hits read it. ----
    CHECK(Near(EmpoweredFactor(0), 1.f) && Near(EmpoweredFactor(1), 1.15f) && Near(EmpoweredFactor(5), 1.75f));
    CHECK(Near(EmpoweredFactor(9), 1.75f));
    CHECK(Near(ScaledPct(SPELL_AR_CHAIN_LIGHTNING, false, 0), kChainPct.normal));
    CHECK(Near(ScaledPct(SPELL_AR_CHAIN_LIGHTNING, true, 2), kChainPct.heroic * 1.3f));
    CHECK(Near(ScaledPct(SPELL_AR_SHOCK, true, 0), kShockPct.heroic));
    CHECK(Near(ScaledPct(SPELL_AR_SHOCK, false, 5), kShockPct.normal * 1.75f));

    // ---- The orb: a fixed 10 s flight whatever the distance (section 8 #20). ----
    CHECK(Near(OrbSpeed(20.f), 2.f) && Near(OrbSpeed(26.f), 2.6f) && Near(OrbSpeed(0.f), kOrbMinSpeed));
    for (Golem g : kGolems)
    {
        float const d = DungeonKit::Distance(PedestalOf(g).XY(), kArgelmachSpawn.XY());
        CHECK(Near(d / OrbSpeed(d) * 1000.f, static_cast<float>(kOrbTravelMs), 1.f));
    }
    CHECK(kOrbLifeMs > kOrbTravelMs);

    // ---- The golems: entries, names, yells, pedestals (NAVMESH 3.2), the wake order. ----
    CHECK(EntryOf(Golem::Toxitron) == 300833 && EntryOf(Golem::Electron) == 300834
        && EntryOf(Golem::Arcanoton) == 300835);
    CHECK(NPC_BRD_TOXITRON == 300833 && NPC_BRD_ARCANE_ORB == 300837);
    for (Golem g : kGolems)
    {
        CHECK(GolemOfEntry(EntryOf(g)) == g);
        CHECK(WakeYellOf(g) == YELL_AR_TOXITRON + IndexOf(g));
        CHECK(PedestalGoOf(g) == 301285 + IndexOf(g));
        // On the chamber's floor, near its rim (clearance 3.5-4.5 yd by the navmesh), off his spawn.
        CHECK(InChamber(PedestalOf(g).XY()));
        CHECK(ChamberClearance(PedestalOf(g).XY()) <= 4.5f);
        CHECK(DungeonKit::Distance(PedestalOf(g).XY(), kArgelmachSpawn.XY()) >= 13.f);
        // Facing the middle.
        float const o = PedestalFacing(g);
        CHECK(o >= 0.f && o < DungeonKit::kTwoPi);
    }
    CHECK(!GolemOfEntry(NPC_BRD_MAGMATRON) && !GolemOfEntry(NPC_ARGELMACH));
    CHECK(YELL_AR_AGGRO == 0 && YELL_AR_CONSOLE == 4 && YELL_AR_DEATH == 7);
    // Every pedestal (P4 too) at least 14 yd from every other (golems within 10 yd would buff each other in the
    // reference fight; NAVMESH: 14+).
    for (std::size_t i = 0; i < kPedestals.size(); ++i)
    {
        CHECK(InChamber(kPedestals[i].XY()));
        for (std::size_t j = i + 1; j < kPedestals.size(); ++j)
            CHECK(DungeonKit::Distance(kPedestals[i].XY(), kPedestals[j].XY()) >= 14.f);
    }
    CHECK(Near(kPedestal4.x, 841.2f) && Near(kPedestal4.y, 4.2f));

    // The wake order: 90 / 65 / 40, one at a time, a big hit wakes every threshold it passed.
    CHECK(Near(kWakePct[0], 90.f) && Near(kWakePct[1], 65.f) && Near(kWakePct[2], 40.f));
    std::array<bool, kGolemCount> none{};
    CHECK(GolemsToWake(100.f, kWakePct, none).empty());
    CHECK(GolemsToWake(90.5f, kWakePct, none).empty());
    {
        auto const w = GolemsToWake(90.f, kWakePct, none);
        CHECK(w.size() == 1 && w[0] == Golem::Toxitron);
    }
    {
        std::array<bool, kGolemCount> first{ true, false, false };
        CHECK(GolemsToWake(70.f, kWakePct, first).empty());
        auto const w = GolemsToWake(64.f, kWakePct, first);
        CHECK(w.size() == 1 && w[0] == Golem::Electron);
    }
    {
        auto const w = GolemsToWake(30.f, kWakePct, none);
        CHECK(w.size() == 3 && w[0] == Golem::Toxitron && w[1] == Golem::Electron && w[2] == Golem::Arcanoton);
    }
    {
        std::array<bool, kGolemCount> all{ true, true, true };
        CHECK(GolemsToWake(1.f, kWakePct, all).empty());
    }
    // The hard mode's thresholds (D16: 80 / 60 / 40) work the same way.
    {
        std::array<float, kGolemCount> const hard{ 80.f, 60.f, 40.f };
        CHECK(GolemsToWake(85.f, hard, none).empty());
        auto const w = GolemsToWake(59.f, hard, none);
        CHECK(w.size() == 2 && w[0] == Golem::Toxitron && w[1] == Golem::Electron);
    }

    // ---- The chamber: his spawn, the middle, the console's spot outside (the passage), its area. ----
    CHECK(InChamber(kArgelmachSpawn.XY()));
    CHECK(InChamber(kChamberMiddle));
    CHECK(ChamberClearance(kChamberMiddle) >= 8.f);
    CHECK(!InChamber({ 832.2f, 12.8f }));           // D16's console, by the passage mouth
    CHECK(!InChamber({ 809.1f, 22.0f }));           // the stock retreat point, in the hall
    CHECK(!InChamber({ 868.f, 40.f }));             // beyond the north-west diagonal wall
    CHECK(!InChamber({ 866.f, 5.f }));              // beyond the north-east wall
    float const area = ChamberArea();
    CHECK(area >= 1000.f && area <= 1110.f);         // the mesh north of x 836: 1,108
    // Every vertex inside the arena the leash uses (S0's chamber box).
    for (Vec2 const& v : kChamber)
        CHECK(ArgelmachArena().Contains(v, kChamberZ));
    CHECK(ChamberClearance({ 900.f, 0.f }) == 0.f);

    // ---- AR10's spot: on the open floor, off the walls and pedestals, 8-25 yd from him. ----
    Lcg rng;
    Vec2 const boss = kArgelmachSpawn.XY();
    std::uint32_t fits = 0;
    for (int i = 0; i < 200; ++i)
    {
        Vec2 const p = PickOverchargeSpot(boss, rng);
        if (!OverchargeSpotFits(p, boss))
            continue;
        ++fits;
        CHECK(InChamber(p));
        CHECK(ChamberClearance(p) >= kOverchargeEdgeYd);
        for (Point3 const& pedestal : kPedestals)
            CHECK(DungeonKit::Distance(p, pedestal.XY()) >= kOverchargePedestalYd);
        float const d = DungeonKit::Distance(p, boss);
        CHECK(d >= kOverchargeMinYd && d <= kOverchargeMaxYd);
    }
    CHECK(fits == 200);
    // From anywhere he can stand in the chamber a spot fits (the fallback is the middle).
    for (Vec2 const from : { Vec2{ 846.8f, 16.3f }, Vec2{ 851.f, 22.f }, Vec2{ 862.f, 25.f }, Vec2{ 840.f, 30.f } })
    {
        Vec2 const p = PickOverchargeSpot(from, rng);
        CHECK(OverchargeSpotFits(p, from) || (Near(p.x, kChamberMiddle.x) && Near(p.y, kChamberMiddle.y)));
    }
    // No draw fits: the middle.
    {
        auto zero = []() { return 0.f; };
        Vec2 const p = PickOverchargeSpot(boss, zero);
        CHECK(Near(p.x, kChamberMiddle.x) && Near(p.y, kChamberMiddle.y));
    }
    CHECK(!OverchargeSpotFits(kPedestal1.XY(), boss));
    CHECK(!OverchargeSpotFits(boss, boss));

    // ---- Beat. ----
    Beat beat;
    CHECK(!beat.On() && !beat.Due(100000));
    beat.Start(1000, 5000);
    CHECK(!beat.Due(5999) && beat.Due(6000));
    beat.Fired(6500, 15000);
    CHECK(beat.DueMs() == 21000);
    beat.Fired(60000, 15000);           // fell far behind: never in the past
    CHECK(beat.DueMs() == 75000);
    beat.Stop();
    CHECK(!beat.Due(100000));

    return Report("brd_argelmach_test");
}
