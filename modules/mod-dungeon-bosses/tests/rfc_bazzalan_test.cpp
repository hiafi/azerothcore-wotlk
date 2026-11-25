// Host tests for BazzalanLogic.h (D3: Bazzalan): the slice and the arena, the cadence around a finisher, the normal bag
// and the heroic alternation, Envenom, the Shadowstep chain and its landings on the ridge, the reach from his edge.
#include "BazzalanLogic.h"
#include "check.h"
#include "rfc_edge_check.h"
#include <cmath>
#include <cstdio>
#include <iterator>
#include <map>
#include <random>
#include <set>

using namespace RagefireChasmRework;
using namespace RfcBazzalan;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    bool OnFloor(Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(kRidgeFloorPolygon), p);
    }

    bool OnArena(Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(kRidgeArenaPolygon), p);
    }

    struct FloorCell
    {
        float x, y, z;      // the floor (live navmesh of map 389)
        float spotZ;        // the floor at EdgeSpot of it
    };

    // The shelf past the notch: half-yard cells near his edge on the plane, 4.9 yd or more from his spot in 3D.
    constexpr FloorCell kShelfCells[] =
    {
        { -398.0f, 175.0f, 12.47f, 9.48f }, { -398.0f, 175.5f, 12.24f, 9.21f }, { -398.0f, 176.0f, 12.01f, 8.95f },
        { -398.0f, 176.5f, 11.79f, 8.31f }, { -397.5f, 174.0f, 12.23f, 8.85f }, { -397.5f, 175.0f, 13.15f, 9.51f },
        { -397.5f, 175.5f, 12.64f, 9.24f }, { -397.5f, 176.0f, 12.41f, 8.25f }, { -397.5f, 176.5f, 12.19f, 8.31f },
        { -397.5f, 177.0f, 11.96f, 8.31f }, { -397.5f, 177.5f, 11.74f, 8.31f }, { -397.5f, 178.0f, 11.51f, 8.31f },
        { -397.0f, 173.5f, 11.87f, 8.84f }, { -397.0f, 174.0f, 12.33f, 8.69f }, { -397.0f, 176.5f, 12.59f, 8.31f },
        { -397.0f, 177.0f, 12.36f, 8.31f }, { -397.0f, 177.5f, 12.14f, 8.31f }, { -397.0f, 178.0f, 11.91f, 8.31f },
        { -397.0f, 178.5f, 11.69f, 8.31f }, { -397.0f, 179.0f, 11.46f, 8.31f }, { -397.0f, 179.5f, 11.23f, 8.31f },
        { -397.0f, 180.0f, 11.01f, 8.31f }, { -397.0f, 180.5f, 10.78f, 8.31f }, { -396.5f, 173.5f, 11.98f, 8.87f },
        { -396.5f, 174.0f, 12.44f, 8.86f }, { -396.5f, 178.5f, 12.09f, 8.31f }, { -396.0f, 173.5f, 12.09f, 8.88f },
        { -396.0f, 174.0f, 12.55f, 8.88f }, { -395.5f, 173.5f, 12.19f, 8.89f }, { -395.5f, 174.0f, 12.66f, 8.89f },
        { -395.0f, 173.5f, 12.30f, 8.90f }, { -395.0f, 174.0f, 12.77f, 8.90f }, { -394.5f, 173.5f, 12.41f, 8.92f },
        { -394.5f, 174.0f, 12.88f, 8.92f }, { -394.0f, 173.5f, 12.52f, 8.93f }, { -393.5f, 173.0f, 12.16f, 8.93f },
        { -393.5f, 173.5f, 12.63f, 8.93f }, { -393.0f, 173.0f, 12.27f, 8.93f }, { -393.0f, 173.5f, 12.74f, 8.93f },
        { -392.5f, 173.0f, 12.38f, 8.93f }, { -392.5f, 173.5f, 12.84f, 8.93f }, { -392.0f, 172.5f, 12.03f, 8.93f },
        { -392.0f, 173.0f, 12.49f, 8.93f }, { -391.5f, 172.0f, 11.67f, 8.93f }, { -391.5f, 172.5f, 12.13f, 8.93f },
        { -391.0f, 172.0f, 11.78f, 8.93f }, { -390.5f, 171.5f, 11.42f, 8.92f }, { -382.0f, 162.5f, 9.63f, 8.06f },
        { -381.5f, 162.0f, 9.68f, 8.02f }, { -381.0f, 161.5f, 9.73f, 7.98f }, { -377.0f, 157.0f, 11.81f, 8.97f },
        { -376.5f, 157.0f, 11.64f, 9.10f }, { -376.0f, 157.0f, 11.46f, 9.24f },
    };

    // Cells of the same edges he does reach (4.9 yd at most in 3D).
    constexpr FloorCell kNearCells[] =
    {
        { -402.0f, 177.0f, 8.36f, 8.18f }, { -401.0f, 175.0f, 10.06f, 9.30f }, { -401.0f, 178.0f, 8.71f, 8.23f },
        { -400.0f, 174.0f, 11.32f, 9.89f }, { -400.0f, 177.0f, 9.96f, 8.21f }, { -399.0f, 171.0f, 9.12f, 8.84f },
        { -399.0f, 174.0f, 11.90f, 9.95f }, { -399.0f, 177.0f, 10.76f, 8.25f }, { -399.0f, 180.0f, 9.41f, 8.31f },
        { -398.0f, 172.0f, 10.26f, 8.83f }, { -398.0f, 177.0f, 11.56f, 8.31f }, { -398.0f, 180.0f, 10.21f, 8.31f },
        { -397.0f, 171.0f, 9.55f, 8.86f }, { -396.0f, 170.0f, 8.92f, 8.89f }, { -396.0f, 173.0f, 11.62f, 8.88f },
        { -395.0f, 172.0f, 10.91f, 8.91f }, { -394.0f, 170.0f, 8.99f, 8.93f }, { -394.0f, 173.0f, 12.06f, 8.93f },
        { -393.0f, 170.0f, 9.02f, 8.92f }, { -392.0f, 166.0f, 8.83f, 8.80f }, { -392.0f, 169.0f, 9.00f, 8.88f },
        { -392.0f, 172.0f, 11.56f, 8.93f }, { -391.0f, 167.0f, 8.92f, 8.81f }, { -391.0f, 170.0f, 9.09f, 8.89f },
        { -390.0f, 165.0f, 8.84f, 8.77f }, { -390.0f, 168.0f, 9.01f, 8.82f }, { -389.0f, 163.0f, 8.76f, 8.74f },
        { -389.0f, 166.0f, 8.93f, 8.76f }, { -389.0f, 169.0f, 9.10f, 8.83f }, { -388.0f, 164.0f, 8.85f, 8.74f },
        { -388.0f, 167.0f, 9.02f, 8.76f }, { -387.0f, 164.0f, 8.89f, 8.73f }, { -387.0f, 167.0f, 8.22f, 8.75f },
        { -386.0f, 163.0f, 8.14f, 8.71f }, { -386.0f, 166.0f, 8.14f, 8.74f }, { -385.0f, 162.0f, 8.05f, 8.69f },
        { -385.0f, 165.0f, 8.05f, 8.72f }, { -384.0f, 161.0f, 8.75f, 8.09f }, { -384.0f, 164.0f, 9.34f, 8.70f },
        { -383.0f, 160.0f, 8.85f, 8.01f }, { -383.0f, 163.0f, 9.44f, 8.68f }, { -382.0f, 159.0f, 8.95f, 8.23f },
        { -382.0f, 162.0f, 9.54f, 8.04f }, { -381.0f, 157.0f, 8.85f, 8.31f }, { -381.0f, 160.0f, 9.44f, 8.24f },
        { -380.0f, 154.0f, 8.55f, 8.28f }, { -380.0f, 157.0f, 9.14f, 8.30f }, { -380.0f, 160.0f, 9.73f, 8.31f },
        { -379.0f, 155.0f, 9.05f, 8.28f }, { -379.0f, 158.0f, 9.64f, 8.31f }, { -378.0f, 154.0f, 9.15f, 8.80f },
        { -378.0f, 157.0f, 9.74f, 8.29f }, { -377.0f, 154.0f, 9.44f, 9.07f }, { -376.0f, 148.0f, 8.09f, 8.09f },
        { -376.0f, 151.0f, 9.15f, 9.04f }, { -376.0f, 154.0f, 9.74f, 9.34f }, { -375.0f, 149.0f, 8.10f, 8.10f },
        { -375.0f, 152.0f, 9.64f, 9.29f }, { -375.0f, 155.0f, 11.01f, 9.35f }, { -374.0f, 150.0f, 9.54f, 8.86f },
        { -374.0f, 153.0f, 10.55f, 9.35f }, { -374.0f, 156.0f, 10.70f, 9.35f }, { -373.0f, 151.0f, 9.22f, 9.11f },
        { -373.0f, 154.0f, 10.25f, 9.35f }, { -372.0f, 151.0f, 9.74f, 9.13f }, { -372.0f, 154.0f, 9.89f, 9.35f },
    };

    // A whole fight on the script's own rules: strikes on StrikeClock, a finisher bar at 5 points, no tank movement.
    // The bars' start times; `chainAt` (an index) runs a Shadowstep chain after its bar.
    std::vector<std::uint64_t> BarStarts(bool heroic, std::uint32_t fightMs, int chainAt = -1)
    {
        std::vector<std::uint64_t> out;
        StrikeClock clock;
        clock.Start(Tune::kStrikeFirstMs);
        std::uint32_t points = 0;
        std::uint64_t busyUntil = 0;
        for (std::uint64_t now = 0; now < fightMs; now += 50)
        {
            if (now < busyUntil)
                continue;
            if (clock.Due(now))
            {
                clock.Fired(now, Tune::kStrikeEveryMs(heroic));
                points = std::min(points + 1, Tune::kComboMax);
            }
            if (points < Tune::kComboMax)
                continue;
            bool const chain = chainAt == static_cast<int>(out.size());
            out.push_back(now);
            busyUntil = now + Tune::kFinisherCastMs + (chain ? ShadowstepChainMs() : 0);
            points = 0;
            clock.Start(busyUntil + kStrikeAfterFinisherMs(heroic));
        }
        return out;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation; fifteen ids, all distinct.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    std::set<std::uint32_t> const spells{ SPELL_BZ_SINISTER_STRIKE, SPELL_BZ_COMBO_POINTS, SPELL_BZ_EVISCERATE,
        SPELL_BZ_RUPTURE_CAST, SPELL_BZ_RUPTURE_LOOK, SPELL_BZ_RUPTURE, SPELL_BZ_RUPTURE_HEROIC, SPELL_BZ_FAN_CAST,
        SPELL_BZ_FAN, SPELL_BZ_ENVENOM, SPELL_BZ_SHADOWSTEP_CAST, SPELL_BZ_SHADOWSTEP_LOOK, SPELL_BZ_DEADLY_POISON,
        SPELL_BZ_WOUND_POISON, SPELL_BZ_CRIPPLING_POISON };
    CHECK(spells.size() == 15);
    for (std::uint32_t id : spells)
        CHECK(kSpellSlice.Contains(id));
    CHECK(SPELL_BZ_SINISTER_STRIKE == 213610);
    CHECK(SPELL_BZ_CRIPPLING_POISON == 213624);
    CHECK(!kSpellsReservation.Contains(SPELL_STOCK_SINISTER_STRIKE));
    CHECK(!kSpellsReservation.Contains(SPELL_STOCK_DEADLY_POISON));
    // The drill's tags (BM MechanicDrill.h kRfcTagFan 8, kRfcTagStepFan 9).
    CHECK(TAG_BZ_FAN == 8 && TAG_BZ_STEP_FAN == 9);

    // His spawn is on his arena, and the slot's arena is the same one.
    CHECK(BazzalanArena().Contains(kBazzalanSpawn.XY(), kBazzalanSpawn.z));
    CHECK(ArenaFor(BOSS_BAZZALAN).Contains(kBazzalanSpawn.XY(), kBazzalanSpawn.z));
    CHECK(BazzalanArena().Contains(kRidgeSafeDisc.XY(), kRidgeSafeDisc.z));
    // The build spec's health and the numbers it names.
    CHECK(Tune::kHealth.normal == 65 * 356 && Tune::kHealth.heroic == 109 * 3052);
    CHECK(Near(Tune::kEvisceratePctTank(false), 35.f) && Near(Tune::kEvisceratePctTank(true), 50.f));
    CHECK(Near(Tune::kFanPct, 35.f) && Near(Tune::kShadowstepPct, 45.f));
    CHECK(Near(Tune::kFanRadius, 8.f) && Near(Tune::kShadowstepRadius, 6.f));
    // The drill's rows: 8 yd and 6 yd, 2 s each.
    CHECK(Tune::kFanWarnMs == 2000 && Tune::kShadowstepWarnMs == 2000 && Tune::kFinisherCastMs == 2000);
    // Rupture: 40% over six ticks; heroic 2% a tick.
    CHECK(Tune::kRuptureNormalMs / Tune::kRuptureTickMs == 6);
    CHECK(Near(Tune::RuptureTickPct(false) * 6.f, 40.f, 0.05f));
    CHECK(Near(Tune::RuptureTickPct(true), 2.f));

    // ---- Cadence (rule 24) ----
    // Normal: the first bar at 14 s (lands at 16, SP "about 15"), then every 17 s; heroic at 10 s, then every 10 s.
    CHECK(FirstFinisherMs(false) == 14000 && FinisherCycleMs(false) == 17000);
    CHECK(FirstFinisherMs(true) == 10000 && FinisherCycleMs(true) == 10000);
    std::vector<std::uint64_t> const normal = BarStarts(false, 66500);
    CHECK(normal.size() == 4);      // at most four in a 65 s kill (SP)
    CHECK(BarStarts(false, 62000).size() == 3);
    for (std::size_t i = 0; i < normal.size(); ++i)
        CHECK(normal[i] == FirstFinisherMs(false) + i * FinisherCycleMs(false));
    std::vector<std::uint64_t> const heroic = BarStarts(true, 80000);
    CHECK(heroic.size() == 7);      // "about 7 finishers in an 80 sec kill"
    for (std::size_t i = 0; i < heroic.size(); ++i)
        CHECK(heroic[i] == FirstFinisherMs(true) + i * FinisherCycleMs(true));
    // A chain stretches its own cycle only.
    std::vector<std::uint64_t> const chained = BarStarts(true, 80000, 1);
    CHECK(chained[1] == 20000 && chained[2] == 20000 + 10000 + ShadowstepChainMs());
    CHECK(chained[3] == chained[2] + 10000);
    // Two expected interrupts are never 10 s apart: the bag alternates, so they are 20 s apart or more, and never in
    // one interrupter's 10 s cooldown.
    CHECK(2 * FinisherCycleMs(true) == kKickEveryHeroicMs);
    // The bar of the next finisher, as the overload hold is told.
    CHECK(NextFinisherInMs(true, 0, 2000) == 10000);
    CHECK(NextFinisherInMs(true, 4, 1500) == 1500);
    CHECK(NextFinisherInMs(true, 5, 1500) == 0);
    CHECK(NextFinisherInMs(false, 0, Tune::kStrikeFirstMs) == FirstFinisherMs(false));
    // A due strike stays due while the tank is out, then the clock goes on from there (no burst).
    StrikeClock clock;
    CHECK(!clock.Due(100000));
    clock.Start(2000);
    CHECK(!clock.Due(1999) && clock.Due(2000) && clock.Due(9000));
    clock.Fired(9000, 2000);
    CHECK(!clock.Due(10999) && clock.Due(11000));
    CHECK(clock.InMs(10000) == 1000 && clock.InMs(12000) == 0);
    clock.Stop();
    CHECK(!clock.Due(20000) && clock.InMs(0) == 0);

    // ---- The bag ----
    std::mt19937 rng(389);
    auto rand = [&rng](std::uint32_t n) { return static_cast<std::uint32_t>(rng() % n); };
    FinisherBag bag;
    bag.Reset(false);
    std::set<std::vector<Finisher>> orders;
    for (int round = 0; round < 300; ++round)
    {
        std::vector<Finisher> three;
        for (int i = 0; i < 3; ++i)
            three.push_back(bag.Draw(rand));
        std::set<Finisher> const distinct(three.begin(), three.end());
        CHECK(distinct.size() == 3);        // each once before any repeats
        for (Finisher f : three)
            CHECK(UsedOn(f, false));
        orders.insert(three);
    }
    CHECK(orders.size() == 6);      // every order comes up
    bag.Reset(true);
    std::map<Finisher, int> seen;
    for (int i = 0; i < 400; ++i)
    {
        Finisher const f = bag.Draw(rand);
        CHECK(UsedOn(f, true));
        CHECK(Kickable(f) == (i % 2 == 0));     // alternating, the kickable half first (#34 A)
        ++seen[f];
    }
    CHECK(seen.size() == 4);
    for (auto const& [f, count] : seen)
        CHECK(count > 60);          // at random within each half
    // A reset starts with the kickable half again.
    bag.Draw(rand);
    bag.Reset(true);
    CHECK(Kickable(bag.Draw(rand)));
    CHECK(Kickable(Finisher::Eviscerate) && Kickable(Finisher::Envenom));
    CHECK(!Kickable(Finisher::Rupture) && !Kickable(Finisher::Fan) && !Kickable(Finisher::Shadowstep));
    CHECK(!UsedOn(Finisher::Fan, true) && !UsedOn(Finisher::Envenom, false) && !UsedOn(Finisher::Shadowstep, false));
    CHECK(!UsedOn(Finisher::None, false));
    // Refused finishers: a kickable one is tried again, never swapped; the others give way within their half first.
    CHECK((AttemptOrder(Finisher::Eviscerate, false) == std::vector<Finisher>{ Finisher::Eviscerate }));
    CHECK((AttemptOrder(Finisher::Envenom, true) == std::vector<Finisher>{ Finisher::Envenom }));
    CHECK((AttemptOrder(Finisher::Rupture, true) == std::vector<Finisher>{ Finisher::Rupture, Finisher::Shadowstep,
        Finisher::Eviscerate, Finisher::Envenom }));
    CHECK((AttemptOrder(Finisher::Shadowstep, true) == std::vector<Finisher>{ Finisher::Shadowstep, Finisher::Rupture,
        Finisher::Eviscerate, Finisher::Envenom }));
    for (bool const h : { false, true })
        for (Finisher f : { Finisher::Eviscerate, Finisher::Rupture, Finisher::Fan, Finisher::Envenom,
            Finisher::Shadowstep })
            if (UsedOn(f, h))
                for (Finisher tried : AttemptOrder(f, h))
                    CHECK(UsedOn(tried, h));

    // ---- Envenom ----
    CHECK(Near(EnvenomPctTank(0), 0.f) && Near(EnvenomPctTank(1), 10.f) && Near(EnvenomPctTank(5), 50.f));
    CHECK(Near(EnvenomPctTank(9), 50.f));       // tops out at 50%
    CHECK(Near(EnvenomPctTank(Tune::kDeadlyStacks), Tune::kEvisceratePctTank(true)));

    // ---- Shadowstep ----
    CHECK(Tune::kShadowstepCount == 3 && ShadowstepChainMs() == 7500);      // SP: "about 7.5 sec"
    CHECK(kShadowstepEveryMs >= 2000 && kShadowstepEveryMs <= 2500);        // STAGE-G1 Q4
    // A slowed player still clears the 6 yd ring in its 2 s.
    CHECK(SlowedReachYd(Tune::kShadowstepWarnMs) >= Tune::kShadowstepRadius);
    // Every landing, from every floor point and facing, is on the arena, near its player; a player within 2 yd of a rim
    // is never picked; and nearly everyone else can be.
    std::size_t safe = 0;
    std::size_t landed = 0;
    for (float x = -416.f; x <= -365.f; x += 1.f)
        for (float y = 127.f; y <= 196.f; y += 1.f)
        {
            Vec2 const player{ x, y };
            bool const rim = RimDistance(player) < Tune::kRimSkipYd;
            for (int i = 0; i < 16; ++i)
            {
                std::optional<Vec2> const at = ShadowstepLanding(player, float(i) * DungeonKit::kPi / 8.f);
                if (rim)
                {
                    CHECK(!at);
                    continue;
                }
                // South of the neck's cut: the neck itself is outside the arena.
                if (y <= 182.f)
                {
                    ++safe;
                    landed += at ? 1 : 0;
                }
                if (!at)
                    continue;
                CHECK(RfcEdgeCheck::StrictlyInside(BazzalanArena(), *at, kBazzalanSpawn.z));
                CHECK(OnFloor(*at));
                CHECK(DungeonKit::Distance(*at, player) <= kLandingMaxOffYd + 0.001f);
                CHECK(RimDistance(*at) >= 3.5f);        // 4 yd inside every edge, less the mesh cut's slack
            }
        }
    CHECK(safe > 10000);
    CHECK(float(landed) >= 0.9f * float(safe));
    // Open floor: 2 yd straight behind, unmoved.
    std::optional<Vec2> const open = ShadowstepLanding(kRidgeSafeDisc.XY(), 0.f);
    CHECK(open && Near(open->x, kRidgeSafeDisc.x - 2.f) && Near(open->y, kRidgeSafeDisc.y));
    // Off the ridge (Jergosh's hall): nobody.
    CHECK(!ShadowstepLanding(kJergoshSpawn.XY(), 0.f));
    CHECK(!ShadowstepLanding(kRidgeNeck.XY(), 0.f) || OnArena(*ShadowstepLanding(kRidgeNeck.XY(), 0.f)));
    // Back to the tank: 2 yd from it on the side he left from, on the arena whatever the tank's spot.
    Vec2 const tank = kRidgeSafeDisc.XY();
    Vec2 const back = ReturnSpot(tank, { tank.x + 10.f, tank.y });
    CHECK(Near(back.x, tank.x + 2.f) && Near(back.y, tank.y));
    CHECK(OnArena(ReturnSpot(tank, tank)));
    CHECK(OnArena(ReturnSpot({ -372.f, 138.f }, tank)));
    CHECK(OnArena(ReturnSpot(kRidgeNeck.XY(), tank)));

    // ---- His edge (R-1-BOSS M-1): a target he can reach from his arena never turns him ----
    DungeonKit::Arena const reach = ReachArena();
    CHECK(reach.Contains(kBazzalanSpawn.XY(), kBazzalanSpawn.z));
    CHECK(!reach.Contains(kBazzalanSpawn.XY(), kJergoshSpawn.z));      // the hall below
    CHECK(!reach.Contains(kRidgeNeck.XY(), kRidgeNeck.z));             // the neck: out of reach
    std::uint32_t floor = 0;
    std::uint32_t inReach = 0;
    std::uint32_t band = 0;
    for (float x = -417.f; x <= -364.f; x += 0.5f)
        for (float y = 126.f; y <= 184.f; y += 0.5f)
        {
            Vec2 const p{ x, y };
            if (OnArena(p))
                CHECK(reach.Contains(p, kBazzalanSpawn.z));
            if (!OnFloor(p))
                continue;
            ++floor;
            if (!reach.Contains(p, kBazzalanSpawn.z))
                continue;
            ++inReach;
            band += OnArena(p) ? 0 : 1;
            Vec2 const spot = EdgeSpot(p);
            CHECK(RfcEdgeCheck::StrictlyInside(BazzalanArena(), spot, kBazzalanSpawn.z));
            CHECK(DungeonKit::Distance(spot, p) <= 4.8f);               // melee range is 5 yd
        }
    CHECK(float(inReach) >= 0.9f * float(floor));
    CHECK(band > 0.3f * float(floor));                                  // the floor the old guard turned him on
    std::printf("reach: %.1f%% of the ridge south of y 184, %.1f%% outside his arena\n",
        100.f * float(inReach) / float(floor), 100.f * float(band) / float(floor));
    RfcEdgeCheck::CheckEdge("bazzalan", kRidgeArenaPolygon, BazzalanArena(), RidgeFloor(), reach, kBazzalanSpawn.z,
        { -417.f, -364.f, 126.f, 196.f }, 5.f, 1.4f);
    // RF-M3: high on the shelf he would stand at his edge out of melee range; it is not his reach, the guard turns him.
    auto spot3d = [](FloorCell const& c)
    {
        float const plane = DungeonKit::Distance(EdgeSpot({ c.x, c.y }), { c.x, c.y });
        return std::hypot(plane, c.z - c.spotZ);
    };
    std::uint32_t planeOnly = 0;
    std::uint32_t high = 0;
    for (FloorCell const& c : kShelfCells)
    {
        CHECK(spot3d(c) > 4.85f);
        if (spot3d(c) > 5.f)
        {
            ++high;
            CHECK(!reach.Contains({ c.x, c.y }, c.z));
        }
        planeOnly += reach.Contains({ c.x, c.y }, c.spotZ) ? 1 : 0;
    }
    CHECK(high >= 45);
    CHECK(planeOnly * 10 >= std::size(kShelfCells) * 9);                // on the plane nearly all of them were in reach
    // RF2-m1: on the level part of the east band a jump (apex 1.64 yd) leaves the height cap, the reason for JumpGrace.
    std::uint32_t east = 0;
    std::uint32_t jumpOut = 0;
    for (float x = -417.f; x <= -364.f; x += 0.5f)
        for (float y = 126.f; y <= 184.f; y += 0.5f)
            if (OnFloor({ x, y }) && !OnArena({ x, y }) && reach.Contains({ x, y }, 9.f))
            {
                ++east;
                jumpOut += reach.Contains({ x, y }, 9.f + 1.64f) ? 0 : 1;
            }
    CHECK(jumpOut > 0 && jumpOut < east / 4);
    // ... and how long the guard is not asked: a whole jump is, and the next one a second later.
    for (std::uint32_t const tick : { 50u, 100u, 250u })
    {
        JumpGrace grace;
        for (std::uint32_t jumps = 0; jumps < 3; ++jumps)
        {
            for (std::uint32_t ms = 0; ms + tick <= 830; ms += tick)
                CHECK(grace.Skip(true, tick));
            for (std::uint32_t ms = 0; ms < 1000; ms += tick)
                CHECK(!grace.Skip(false, tick));                        // on the ground: always asked
        }
        // Hopping without a pause (0.83 s up, one tick down), or falling on: judged most of the time.
        for (std::uint32_t const groundMs : { tick, 0u })
        {
            grace.Reset();
            std::uint32_t skipped = 0;
            for (std::uint32_t ms = 0; ms < 20000; ms += tick)
                if (grace.Skip(!groundMs || ms % 850 >= groundMs, tick))
                    skipped += tick;
            CHECK(skipped >= 800 && skipped <= (groundMs ? 8000u : kJumpAirMs));
        }
        grace.Skip(true, 60000);
        grace.Reset();
        CHECK(grace.Skip(true, tick));
    }
    std::uint32_t near = 0;
    for (FloorCell const& c : kNearCells)
    {
        bool const in = reach.Contains({ c.x, c.y }, c.z);
        near += in ? 1 : 0;
        if (in)
            CHECK(spot3d(c) <= 5.f);
    }
    CHECK(near * 100 >= std::size(kNearCells) * 80);
    std::printf("shelf: 0 of %u high cells in reach, %u of %zu near ones\n", high, near, std::size(kNearCells));

    // The tank's steps from him, as the finding measured them: he on his arena, the tank on the floor 3 to 9 yd away.
    for (float const step : { 3.f, 7.f, 9.f })
    {
        std::uint32_t spots = 0;
        std::uint32_t off = 0;
        std::uint32_t offArena = 0;
        for (float x = -411.f; x <= -372.f; x += 1.f)
            for (float y = 132.f; y <= 184.f; y += 1.f)
                for (int i = 0; OnArena({ x, y }) && i < 36; ++i)
                {
                    Vec2 const tank = DungeonKit::Advance({ x, y }, float(i) * DungeonKit::kPi / 18.f, step);
                    if (!OnFloor(tank))
                        continue;
                    ++spots;
                    off += reach.Contains(tank, kBazzalanSpawn.z) ? 0 : 1;
                    offArena += OnArena(tank) ? 0 : 1;
                }
        CHECK(off * 4 < offArena);
        std::printf("  %.0f yd: turns him on %.1f%% of the spots (was %.1f%%)\n", step,
            100.f * float(off) / float(spots), 100.f * float(offArena) / float(spots));
    }

    // ---- Outsiders ----
    CHECK((Outsiders({ { 1, true }, { 2, false }, { 3, true } }) == std::vector<std::uint64_t>{ 2 }));
    CHECK(Outsiders({ { 1, false }, { 2, false } }).empty());           // nobody on the ridge: anyone
    CHECK(Outsiders({}).empty());

    return Report("rfc_bazzalan_test");
}
