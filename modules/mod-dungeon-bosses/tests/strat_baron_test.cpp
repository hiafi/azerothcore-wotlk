// Host tests for BaronLogic.h (S14: Baron Rivendare): the slice and the arena, wave alternation and the normal cap of
// 6, the Unholy Aura percent per servant, the piles a rot raises, the bot tank's reposition trigger, the stock leash
// and the never-paused timeline.
#include "BaronLogic.h"
#include "DungeonKitFlow.h"
#include "check.h"
#include <cmath>
#include <vector>

using namespace StratholmeRework;
using namespace StratBaron;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }
}

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation, never in S15's.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    for (std::uint32_t id : { SPELL_BR_UNHOLY_AURA, SPELL_BR_UNHOLY_PULSE, SPELL_BR_RISE, SPELL_BR_DEATH_AND_DECAY,
        SPELL_BR_ROT, SPELL_BR_ROT_LOOK, SPELL_BR_SKELETON_STRIKE })
    {
        CHECK(kSpellSlice.Contains(id));
        CHECK(!kSpellsUltimatum.Contains(id));
    }
    CHECK(kHardModeCastBase > CAST_SHADOW_BOLT);
    CHECK(kHardModeTagBase > TAG_PARK);

    // The boss spawns inside his arena (the r 25 leash circle); the six Raise Dead points and Menethil's Gift lie in
    // his room's frame (the drop spot rule's room). Two points (the south-east and north-east corners) lie 1-2 yd
    // outside the leash circle: the skeletons rise there, the boss is never held there.
    CHECK(BaronArena().Contains(kBaronSpawn.XY(), kBaronSpawn.z));
    CHECK(ArenaFor(BOSS_BARON).Contains(kBaronSpawn.XY(), kBaronSpawn.z));
    CHECK(DungeonKit::InsideFrame(kBaronRoom, kBaronSpawn.XY()));
    for (Point3 const& p : kRaiseDeadPoints)
        CHECK(DungeonKit::InsideFrame(kBaronRoom, p.XY()));
    CHECK(DungeonKit::InsideFrame(kBaronRoom, kMenethilsGift.XY()));
    CHECK(BaronArena().Contains(kMenethilsGift.XY(), kMenethilsGift.z));
    // The drop spot's room circle lies inside the room's frame and inside the leash circle.
    CHECK(DungeonKit::InsideFrame(kBaronRoom, { kDropRoomCenter.x - kDropRoomRadius, kDropRoomCenter.y }));
    CHECK(DungeonKit::InsideFrame(kBaronRoom, { kDropRoomCenter.x + kDropRoomRadius, kDropRoomCenter.y }));
    CHECK(DungeonKit::InsideFrame(kBaronRoom, { kDropRoomCenter.x, kDropRoomCenter.y - kDropRoomRadius }));
    CHECK(DungeonKit::InsideFrame(kBaronRoom, { kDropRoomCenter.x, kDropRoomCenter.y + kDropRoomRadius }));
    CHECK(BaronArena().Contains(kDropRoomCenter, 115.2f));

    // BR1: walls alternate; each wall's three points are its own row (south row x < 4020, north row x > 4045).
    CHECK(OtherWall(Wall::South) == Wall::North);
    CHECK(OtherWall(OtherWall(Wall::South)) == Wall::South);
    for (Point3 const& p : WallPoints(Wall::South))
        CHECK(p.x < 4020.f);
    for (Point3 const& p : WallPoints(Wall::North))
        CHECK(p.x > 4045.f);
    CHECK(WallPoints(Wall::South)[0].x == kRaiseDeadPoints[0].x);
    CHECK(WallPoints(Wall::North)[2].y == kRaiseDeadPoints[5].y);

    // BR1: the normal cap of 6 (a wave rises short), no cap on heroic.
    CHECK(WaveCount(0, false) == 3);
    CHECK(WaveCount(3, false) == 3);
    CHECK(WaveCount(4, false) == 2);
    CHECK(WaveCount(5, false) == 1);
    CHECK(WaveCount(6, false) == 0);
    CHECK(WaveCount(9, false) == 0);
    CHECK(WaveCount(0, true) == 3);
    CHECK(WaveCount(6, true) == 3);
    CHECK(WaveCount(30, true) == 3);
    // A pile-up on normal never passes 6 however the waves fall.
    {
        std::uint32_t alive = 0;
        for (int wave = 0; wave < 10; ++wave)
        {
            alive += WaveCount(alive, false);
            CHECK(alive <= kSkeletonCap.normal);
        }
        CHECK(alive == 6);
    }
    // The skeleton strike: 2 s at 2% / 2.5% is the build spec's 1% / 1.25% a second.
    CHECK(Near(kSkeletonStrikePct.normal * 1000.f / float(kSkeletonSwingMs), 1.f));
    CHECK(Near(kSkeletonStrikePct.heroic * 1000.f / float(kSkeletonSwingMs), 1.25f));
    CHECK(kSkeletonHealth.normal == 6000 && kSkeletonHealth.heroic == 7500);

    // BR4: 1% / 1.5% base, +0.5% per living servant; six adds on normal make it 4%.
    CHECK(Near(UnholyAuraPct(false, 0), 1.f));
    CHECK(Near(UnholyAuraPct(true, 0), 1.5f));
    CHECK(Near(UnholyAuraPct(false, 6), 4.f));
    CHECK(Near(UnholyAuraPct(true, 4), 3.5f));
    CHECK(kUnholyAuraRadius >= 100.f);
    CHECK(kUnholyAuraPeriodMs == 2000);

    // BR3: 10 s / 15 s, 4% / 5%, 6 yd, a 1 s grace, the 3 s following circle.
    CHECK(kRotLifeMs.normal == 10000 && kRotLifeMs.heroic == 15000);
    CHECK(Near(kRotPct.normal, 4.f) && Near(kRotPct.heroic, 5.f));
    CHECK(Near(kRotRadius, 6.f));
    CHECK(kRotGraceMs == 1000 && kDeathAndDecayWarnMs == 3000);
    CHECK(kRotLookMs >= 45000);     // the hard mode's 45 s rot (S15) still has its look

    // BR2 / BR3: the piles a rot raises: inside the radius, on the same floor.
    {
        Point3 const rot{ 4030.f, -3350.f, 115.2f };
        std::vector<Point3> const piles{ { 4030.f, -3350.f, 115.2f }, { 4035.9f, -3350.f, 115.4f },
            { 4036.1f, -3350.f, 115.4f }, { 4030.f, -3344.5f, 115.f }, { 4031.f, -3351.f, 125.f } };
        std::vector<std::size_t> const inside = PilesInRot(piles, rot, kRotRadius);
        CHECK(inside.size() == 3);
        CHECK(inside[0] == 0 && inside[1] == 1 && inside[2] == 3);
        // A lane spot's 3 yd reach (S15) takes fewer.
        CHECK(PilesInRot(piles, rot, 3.f).size() == 1);
        CHECK(PilesInRot({}, rot, kRotRadius).empty());
    }

    // BR2 for the bots: the tank walks him off a pile within 4 yd, not one farther out.
    {
        Vec2 const boss{ 4035.f, -3340.f };
        CHECK(!ShouldPark(boss, {}));
        CHECK(ShouldPark(boss, { { 4038.f, -3340.f, 115.2f } }));
        CHECK(!ShouldPark(boss, { { 4040.f, -3340.f, 115.2f } }));
        CHECK(Near(NearestPileYd(boss, { { 4040.f, -3340.f, 115.f }, { 4035.f, -3337.f, 115.f } }), 3.f));
        CHECK(kParkMinYd > kParkTriggerYd && kParkMaxYd > kParkMinYd);
    }

    // The stock leash: within 21 yd of Ramstein's door, or within 4 yd of his own door while more than 13 yd from
    // Menethil's Gift. His spawn and the room's middle never evade; the door's mouth does.
    CHECK(!StockLeashBreached(kBaronSpawn.XY()));
    CHECK(!StockLeashBreached(kMenethilsGift.XY()));
    for (Point3 const& p : kRaiseDeadPoints)
        CHECK(!StockLeashBreached(p.XY()));
    CHECK(StockLeashBreached(kBaronDoor.XY()));
    CHECK(StockLeashBreached(kRamsteinDoor.XY()));
    CHECK(StockLeashBreached(20.f, 50.f, 50.f));
    CHECK(!StockLeashBreached(22.f, 3.f, 12.f));       // at the door but near the Gift: stays
    CHECK(StockLeashBreached(22.f, 3.f, 14.f));
    CHECK(!StockLeashBreached(22.f, 5.f, 14.f));

    // The timeline: first Raise Dead at 6 s, Death and Decay at 12 s; fixed cooldowns 20 s / 15 s; a retry is 2 s.
    {
        Timeline t;
        CHECK(!t.Due(Beat::RaiseDead));
        t.Advance(5999);
        CHECK(!t.Due(Beat::RaiseDead));
        t.Advance(1);
        CHECK(t.Due(Beat::RaiseDead));
        CHECK(!t.Due(Beat::DeathAndDecay));
        t.Done(Beat::RaiseDead);
        CHECK(t.NextAt(Beat::RaiseDead) == 26000);
        t.Advance(6000);
        CHECK(t.Due(Beat::DeathAndDecay));
        t.Retry(Beat::DeathAndDecay);
        CHECK(t.NextAt(Beat::DeathAndDecay) == 14000);
        t.Advance(2000);
        t.Done(Beat::DeathAndDecay);
        CHECK(t.NextAt(Beat::DeathAndDecay) == 29000);
        t.Done(Beat::Cleave, 9000);
        CHECK(t.NextAt(Beat::Cleave) == 23000);
        // A 2 s Shadow Bolt never holds the clock: it only moves forward with the AI's diffs.
        t.Advance(20000);
        CHECK(t.Due(Beat::RaiseDead) && t.Due(Beat::DeathAndDecay));
    }

    // Raise Dead and Death and Decay over a 2:30 normal fight (no retries): 8 waves and 10 rots, as the build spec's
    // cadence gives (first 6 s / 12 s, then every 20 s / 15 s).
    {
        Timeline t;
        int waves = 0;
        int rots = 0;
        for (std::uint32_t ms = 0; ms < 150000; ms += 100)
        {
            t.Advance(100);
            if (t.Due(Beat::RaiseDead))
            {
                ++waves;
                t.Done(Beat::RaiseDead);
            }
            if (t.Due(Beat::DeathAndDecay))
            {
                ++rots;
                t.Done(Beat::DeathAndDecay);
            }
        }
        CHECK(waves == 8);
        CHECK(rots == 10);
    }

    // R-1-B N-1: the Shadow Bolt waits for a hard mode cast due within its 2 s cast time, so that cast starts on time.
    {
        CHECK(FillerWaits(10000, 12000));
        CHECK(FillerWaits(10000, 9000));
        CHECK(!FillerWaits(10000, 12001));
        DungeonKit::CastQueue queue(kCastSpacingMs);
        std::uint32_t constexpr kExecution = kHardModeCastBase;
        queue.Schedule(CAST_SHADOW_BOLT, 5000, 0);
        queue.Schedule(kExecution, 6500, 1);
        // At 5 s the bolt is the only due cast, but the execution falls due inside its cast time: it waits.
        CHECK((queue.Next(5000).value_or(0)) == (std::uint32_t(CAST_SHADOW_BOLT)));
        CHECK(FillerWaits(5000, queue.DueAt(kExecution).value_or(0)));
        // At 6.5 s the execution starts on time; the bolt follows its hold.
        CHECK((queue.Next(6500).value_or(0)) == (kExecution));
        queue.Started(kExecution, 6500, 3000);
        CHECK(!queue.Next(9000));
        CHECK((queue.Next(10000).value_or(0)) == (std::uint32_t(CAST_SHADOW_BOLT)));
        CHECK(!queue.DueAt(kExecution));
    }

    // The room's real shape (R-1-B B-1, for the room-shape drop spot rule): the spawn, the Gift, the cage and every
    // Raise Dead point are inside; the door 175796 and the corridor beyond the east wall are not.
    {
        CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, kBaronSpawn.XY()));
        CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, kMenethilsGift.XY()));
        CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, kYsidaCage.XY()));
        CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, kDropRoomCenter));
        for (Point3 const& p : kRaiseDeadPoints)
            CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, p.XY()));
        CHECK(!DungeonKit::PointInPolygon(kBaronRoomShape, kBaronDoor.XY()));
        CHECK(!DungeonKit::PointInPolygon(kBaronRoomShape, { 4032.f, -3368.f }));      // R-1-B's r 20 circle's reach
        CHECK(!DungeonKit::PointInPolygon(kBaronRoomShape, kRamsteinDoor.XY()));
        CHECK(DungeonKit::PointInPolygon(kBaronRoomShape, { 4032.f, -3361.f }));       // just inside the east wall
    }

    return Report("strat_baron_test");
}
