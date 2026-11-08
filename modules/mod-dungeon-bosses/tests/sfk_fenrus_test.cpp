// Host tests for Fenrus the Devourer (WP-S7): FenrusLogic.h (handoff section 5: voidwalker strike points on the room
// edge, Rising Pulse cap 10%, the Shadow Scar multiplier) plus the phase rules, the pulse clock and the arena.
#include "FenrusLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <optional>
#include <set>

using namespace ShadowfangKeepRework;
using namespace Fenrus;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Fenrus::kSlice.first));
        CHECK(kSpellsReservation.Contains(Fenrus::kSlice.last));
        CHECK(Fenrus::kSlice.first <= Fenrus::kSlice.last);
        CHECK(FenrusArena().Contains(kFenrusSpawn.XY(), kFenrusSpawn.z));
        for (std::uint32_t id : { SPELL_FENRUS_ARUGALS_LIGHTNING, SPELL_FENRUS_LIGHTNING_ARRIVAL,
                 SPELL_FENRUS_VOID_PULSE, SPELL_FENRUS_SHADOW_FENRUS, SPELL_FENRUS_SHADOW_LEAP_CAST,
                 SPELL_FENRUS_SHADOW_LEAP, SPELL_FENRUS_SHADOW_SCAR, SPELL_FENRUS_SHADOW_LIGHTNING,
                 SPELL_FENRUS_SHADOW_LIGHTNING_LOOK })
            CHECK(Fenrus::kSlice.Contains(id));
        // the bait point (the farthest spot with clearance) is inside his arena
        CHECK(FenrusArena().Contains(kFenrusBaitPoint.XY(), kFenrusBaitPoint.z));
        // the farthest the leap can go stays inside the arena circle: the bait point is about 26 yd from him
        CHECK(DungeonKit::Distance(kFenrusSpawn.XY(), kFenrusBaitPoint.XY()) > kLeapOthersRange + kLeapRadius);
    }

    // FN1: every strike point is on the room's edge (9-17 yd from the center: the room is not quite round), inside the
    // arena on the floor, clear of Fenrus's spawn (the 0 degree point 4.6 yd from him was dropped) and at least 4 yd
    // from its neighbours.
    void TestStrikePoints()
    {
        auto const& points = kFenrusStrikePoints;
        for (std::size_t i = 0; i < points.size(); ++i)
        {
            float const fromCenter = DungeonKit::Distance(points[i], kFenrusRoomCenter);
            CHECK(fromCenter >= 9.f);
            CHECK(fromCenter <= kFenrusRoomRadius);
            CHECK(FenrusArena().Contains(points[i], kFenrusFloorZ));
            CHECK(DungeonKit::Distance(points[i], kFenrusSpawn.XY()) >= 5.f);
            for (std::size_t j = i + 1; j < points.size(); ++j)
                CHECK(DungeonKit::Distance(points[i], points[j]) >= 4.f);
        }
        // a 3 yd circle on any point never reaches the room center: the middle stays safe
        for (Vec2 const p : points)
            CHECK(DungeonKit::Distance(p, kFenrusRoomCenter) > kLightningRadius + 5.f);
    }

    // FN1: never the same point twice in a row; every other point reachable.
    void TestStrikePick()
    {
        std::size_t const n = kFenrusStrikePoints.size();
        std::uint32_t seed = 12345;
        auto rand = [&seed](std::uint32_t m)
        {
            seed = seed * 1103515245u + 12345u;
            return m ? (seed >> 16) % m : 0u;
        };
        std::optional<std::size_t> last;
        std::set<std::size_t> seen;
        for (int i = 0; i < 200; ++i)
        {
            std::size_t const pick = PickStrikeIndex(n, last, rand);
            CHECK(pick < n);
            if (last)
                CHECK(pick != *last);
            seen.insert(pick);
            last = pick;
        }
        CHECK(seen.size() == n);
        // a stale or missing last index still picks in range
        CHECK(PickStrikeIndex(n, std::optional<std::size_t>(99), rand) < n);
        CHECK(PickStrikeIndex(1, std::optional<std::size_t>(0), rand) == 0);
        CHECK(PickStrikeIndex(0, std::nullopt, rand) == 0);
        // with two points the pick always alternates
        CHECK(PickStrikeIndex(2, std::optional<std::size_t>(0), rand) == 1);
        CHECK(PickStrikeIndex(2, std::optional<std::size_t>(1), rand) == 0);
        // the nearest point to each point is itself
        for (std::size_t i = 0; i < n; ++i)
            CHECK(NearestStrikeIndex(kFenrusStrikePoints[i]) == i);
    }

    // FN1 cadence: 10 s, then every 20 s; about 3 voidwalkers in the 62 s normal fight (SK tuning).
    void TestStrikeCadence()
    {
        CHECK(StrikesBy(Ms(9999)) == 0);
        CHECK(StrikesBy(Ms(10000)) == 1);
        CHECK(StrikesBy(Ms(29999)) == 1);
        CHECK(StrikesBy(Ms(30000)) == 2);
        CHECK(StrikesBy(Ms(62000)) == 3);
        CHECK(kLightningPct(false) == 20.f && kLightningPct(true) == 20.f);
        CHECK(kLightningWarn == Ms(2000));
        CHECK(Near(kLightningRadius, 3.f));
    }

    // FN3 + Rising Pulse: 4% flat on normal; heroic +1% per landed pulse, capped at 10%.
    void TestVoidPulse()
    {
        for (std::uint32_t landed = 0; landed < 20; ++landed)
            CHECK(Near(VoidPulsePct(false, landed), 4.f));
        CHECK(Near(VoidPulsePct(true, 0), 4.f));
        CHECK(Near(VoidPulsePct(true, 1), 5.f));
        CHECK(Near(VoidPulsePct(true, 5), 9.f));
        CHECK(Near(VoidPulsePct(true, 6), 10.f));
        CHECK(Near(VoidPulsePct(true, 7), 10.f));
        CHECK(Near(VoidPulsePct(true, 1000), 10.f));
        for (std::uint32_t landed = 0; landed < 50; ++landed)
            CHECK(VoidPulsePct(true, landed) <= kRisingPulseCapPct);
        CHECK(kVoidPulseEvery == Ms(3000));
    }

    // The pulse clock: first cast 1.5 s after the voidwalker steps out, then cast + pause; interrupts do not count.
    void TestPulseClock()
    {
        PulseClock c;
        c.Start(Ms(0));
        CHECK(!c.Due(Ms(1499)));
        CHECK(c.Due(Ms(1500)));
        // cast 1.5-3.0 s, lands at 3.0 s
        c.Landed(Ms(3000));
        CHECK(c.LandedCount() == 1);
        CHECK(!c.Due(Ms(4499)));
        CHECK(c.Due(Ms(4500)));
        CHECK(Near(c.Pct(true), 5.f));
        CHECK(Near(c.Pct(false), 4.f));
        // interrupted at 5.0 s: not counted, the pause follows
        c.Interrupted(Ms(5000));
        CHECK(c.LandedCount() == 1);
        CHECK(c.Next() == Ms(6500));
        CHECK(Near(c.Pct(true), 5.f));
        // stunned at 6.5 s: retried 250 ms later
        c.Blocked(Ms(6500));
        CHECK(c.Next() == Ms(6750));
        for (int i = 0; i < 10; ++i)
            c.Landed(Ms(10000 + i * 3000));
        CHECK(c.LandedCount() == 11);
        CHECK(Near(c.Pct(true), 10.f));
        // a restart (a new voidwalker) starts from 4% again
        c.Start(Ms(90000));
        CHECK(c.LandedCount() == 0);
        CHECK(Near(c.Pct(true), 4.f));
        CHECK(c.Next() == Ms(91500));
    }

    // FN6 + FN7: 25% of the reference row; each Shadow Scar adds +200% Shadow Leap damage taken.
    void TestShadowScar()
    {
        CHECK(Near(ScarFactor(0), 1.f));
        CHECK(Near(ScarFactor(1), 3.f));
        CHECK(Near(ScarFactor(2), 5.f));
        CHECK(Near(ScarFactor(5), 11.f));
        // heroic: 25% of 4,120 = 1,030; normal: 25% of 1,300 = 325
        std::uint32_t const heroicHit = DungeonKit::RefFlatValue(4120, 4110, kLeapPct(true), false);
        std::uint32_t const normalHit = DungeonKit::RefFlatValue(1300, 1290, kLeapPct(false), false);
        CHECK(heroicHit == 1030);
        CHECK(normalHit == 325);
        CHECK(ScarredDamage(heroicHit, 0) == 1030);
        CHECK(ScarredDamage(heroicHit, 1) == 3090);
        CHECK(ScarredDamage(heroicHit, 2) == 5150);
        CHECK(ScarredDamage(0, 3) == 0);
        CHECK(ScarredDamage(1, 1) == 3);
        // the rotation: whoever has the fewest stacks takes the next leap at 1x, a second leap on the same player
        // would be 3x (a failed bait costs the group, not just the baiter)
        CHECK(ScarredDamage(heroicHit, 1) > heroicHit * 2);
        CHECK(kLeapRadius == 6.f && kLeapOthersRange == 12.f);
        CHECK(kLeapFirst == Ms(5000) && kLeapEvery == Ms(10000) && kLeapWarn == Ms(2000));
    }

    // FN8: 15%, 1 s, 3 yd, every 3 s from 2 s into phase two.
    void TestShadowLightning()
    {
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kShadowLightningPct(true), false) == 618);
        CHECK(DungeonKit::RefFlatValue(1300, 1290, kShadowLightningPct(false), false) == 195);
        CHECK(kShadowLightningFirst == Ms(2000) && kShadowLightningEvery == Ms(3000));
        CHECK(kShadowLightningWarn == Ms(1000) && Near(kShadowLightningRadius, 3.f));
    }

    // FN5: the fake death on heroic only, until phase two; strikes summon in phase one only.
    void TestPhases()
    {
        CHECK(!InterceptsLethal(false, Phase::One));
        CHECK(!InterceptsLethal(false, Phase::Rising));
        CHECK(!InterceptsLethal(false, Phase::Two));
        CHECK(InterceptsLethal(true, Phase::One));
        CHECK(InterceptsLethal(true, Phase::Rising));
        CHECK(!InterceptsLethal(true, Phase::Two));

        CHECK(StrikeSummons(Phase::One));
        CHECK(!StrikeSummons(Phase::Rising));
        CHECK(!StrikeSummons(Phase::Two));

        CHECK(MayAct(Phase::One));
        CHECK(!MayAct(Phase::Rising));
        CHECK(MayAct(Phase::Two));

        // heroic 259,420 rises with 103,768 (SK tuning, handoff s3.7)
        CHECK(PhaseTwoHealth(259420) == 103768);
        CHECK(PhaseTwoHealth(11462) == 4584);
        CHECK(PhaseTwoHealth(1) == 1);
        CHECK(PhaseTwoHealth(0) == 1);
        CHECK(kStillness == Ms(1000));
    }

    // The arena guard's landing: a unit in a doorway is put just inside the room, a unit inside stays where it is.
    void TestGripLanding()
    {
        Vec2 const inside{ kFenrusRoomCenter.x + 3.f, kFenrusRoomCenter.y - 2.f };
        Vec2 const landedInside = GripLanding(kFenrusRoomCenter, inside, kGripLandRadius);
        CHECK(Near(landedInside.x, inside.x) && Near(landedInside.y, inside.y));

        // the Sorcerer's Gate (NNE exit) and a point 30 yd out to the SSW
        for (Vec2 const from : { kSorcerersGate.XY(), Vec2{ kFenrusRoomCenter.x - 30.f, kFenrusRoomCenter.y + 5.f } })
        {
            Vec2 const landed = GripLanding(kFenrusRoomCenter, from, kGripLandRadius);
            CHECK(DungeonKit::Distance(landed, kFenrusRoomCenter) <= kGripLandRadius + 0.01f);
            CHECK(FenrusArena().Contains(landed, kFenrusFloorZ));
            // on the line toward the unit: closer to it than the center is
            CHECK(DungeonKit::Distance(landed, from) < DungeonKit::Distance(kFenrusRoomCenter, from));
        }
        Vec2 const atCenter = GripLanding(kFenrusRoomCenter, kFenrusRoomCenter, kGripLandRadius);
        CHECK(Near(atCenter.x, kFenrusRoomCenter.x) && Near(atCenter.y, kFenrusRoomCenter.y));
    }

    // Numbers against the build spec: the strike and pulse at the reference rows (acceptance #8 spot checks).
    void TestNumbers()
    {
        CHECK(DungeonKit::RefFlatValue(1300, 1290, kLightningPct(false), false) == 260);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, kLightningPct(true), false) == 824);
        CHECK(DungeonKit::RefFlatValue(1300, 1290, VoidPulsePct(false, 0), false) == 52);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, VoidPulsePct(true, 0), false) == 165);
        CHECK(DungeonKit::RefFlatValue(4120, 4110, VoidPulsePct(true, 6), false) == 412);
    }
}

int main()
{
    TestSliceAndArena();
    TestStrikePoints();
    TestStrikePick();
    TestStrikeCadence();
    TestVoidPulse();
    TestPulseClock();
    TestShadowScar();
    TestShadowLightning();
    TestPhases();
    TestGripLanding();
    TestNumbers();
    return Report("sfk_fenrus_test");
}
