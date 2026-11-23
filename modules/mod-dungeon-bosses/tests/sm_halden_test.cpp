// Host tests for HaldenLogic.h (D10: Drillmaster Corin Halden, the Master-at-Arms).
#include "HaldenLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>
#include <vector>

using namespace ScarletMonasteryRework;
using namespace SmHalden;

namespace
{
    // A fixed pseudo-random run in [0, 1) (a linear congruential generator): the tests never depend on luck.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>((state >> 8) & 0xFFFFFF) / static_cast<float>(0x1000000);
        }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    Vec2 const kSpawn{ kHaldenSpot.x, kHaldenSpot.y };

    // The spacing between neighbors of a rank (west to east).
    std::vector<float> Gaps(std::vector<Vec2> const& rank)
    {
        std::vector<float> out;
        for (std::size_t i = 1; i < rank.size(); ++i)
            out.push_back(rank[i - 1].y - rank[i].y);
        return out;
    }
}

int main()
{
    // ---- the slice, the arena, the wave ----------------------------------------------------------------------------
    CHECK(kSpellsReservation.Contains(SmHalden::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmHalden::kSpellSlice.last));
    CHECK(SPELL_MA_CHARGE == 212950);
    CHECK(SPELL_MA_CLOSE_RANKS_LOOK == 212958);
    CHECK(SPELL_MA_CLOSE_RANKS_LOOK <= kSpellSlice.last);
    CHECK(HaldenArena().Contains(kHaldenSpot.XY(), kHaldenSpot.z));
    CHECK(ArenaFor(BOSS_HALDEN).Contains(kHaldenSpot.XY(), kHaldenSpot.z));
    CHECK(RoomsArena().Contains(kHaldenSpot.XY(), kHaldenSpot.z));
    CHECK(IsWave2Boss(BOSS_HALDEN));
    CHECK(NPC_SM_HALDEN == 300942 && NPC_SM_DRILL_RECRUIT == 300943);
    // His texts are groups 0-9 of 300942 (S0's text table).
    {
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_SM_HALDEN)
                found = r.first == 0 && r.last == 9 && r.firstNew == 0;
        CHECK(found);
        CHECK(SAY_PAIR_JAVELINS == 9 && SAY_DEATH == 7 && EMOTE_FUMBLE == 5);
    }
    // The drill row `close-ranks` (scarlet-monastery-shapes-2) keys the band 27; the fight keys MA numbers.
    CHECK(TAG_MA_CHARGE == 1 && TAG_MA_SPEARS == 2 && TAG_MA_JAVELIN == 3 && TAG_MA_CLOSE_RANKS == 4);
    CHECK(TAG_MA_SECOND_VOLLEY == 31);

    // ---- MA0 the Drill: normal --------------------------------------------------------------------------------------
    {
        // 8 s, then every 10 s, in the fixed order.
        Command const order[] = { Command::Charge, Command::Spears, Command::Javelins, Command::CloseRanks };
        for (std::uint32_t i = 0; i < 12; ++i)
        {
            DrillCall const c = CallAt(i, false);
            CHECK(c.yellMs == 8000 + 10000 * i);
            CHECK(c.command == order[i % 4]);
            CHECK(!c.pairFirst && !c.pairSecond);
        }
        CHECK(DrillLengthMs(false) == 40000);
        // A full 78 s fight (60k at 768): about 7 commands, almost two drills (the spec's tuning table: the eighth
        // is yelled at 78 s, as he dies).
        std::uint32_t const normalCommands =
            CommandsBy(static_cast<std::uint32_t>(FightSeconds(false) * 1000.f), false);
        CHECK(normalCommands >= 7 && normalCommands <= 8);
        // Nothing is left of a command when the next one is yelled: the ring (2.5 s + 6 s from its yell) ends 1.5 s
        // before the next Charge; the recruits jog back in the 2 s after it (the next lanes' marker covers the rest).
        for (std::uint32_t i = 0; i < 12; ++i)
        {
            DrillCall const c = CallAt(i, false);
            CHECK(c.yellMs + EndMs(c.command, false) < CallAt(i + 1, false).yellMs);
        }
        CHECK(EndMs(Command::CloseRanks, false) == 8500);
    }

    // ---- MA0 the Drill: heroic pairs --------------------------------------------------------------------------------
    {
        std::uint32_t const expect[] = { 8000, 12500, 20000, 26500, 39000, 43500, 51000, 57500, 70000, 74500 };
        Command const order[] = { Command::Charge, Command::Spears, Command::Javelins, Command::CloseRanks };
        for (std::uint32_t i = 0; i < 10; ++i)
        {
            DrillCall const c = CallAt(i, true);
            CHECK(c.yellMs == expect[i]);
            CHECK(c.command == order[i % 4]);
            CHECK(c.pairFirst == (i % 2 == 0));
            CHECK(c.pairSecond == (i % 2 == 1));
        }
        CHECK(DrillLengthMs(true) == 31000);
        // The second yell 2 s after the first lands; the next pair 12 s after a Charge pair, 2 s after a ring.
        for (std::uint32_t p = 0; p < 6; ++p)
        {
            DrillCall const a = CallAt(2 * p, true);
            DrillCall const b = CallAt(2 * p + 1, true);
            DrillCall const next = CallAt(2 * p + 2, true);
            CHECK(b.yellMs == a.yellMs + LandMs(a.command) + 2000);
            if (a.command == Command::Charge)
                CHECK(next.yellMs == a.yellMs + 12000);
            else
                CHECK(next.yellMs == b.yellMs + EndMs(Command::CloseRanks, true) + 2000);
            CHECK(PairText(a.command) == (a.command == Command::Charge ? SAY_PAIR_CHARGE : SAY_PAIR_JAVELINS));
        }
        // The second volley (1.5 s after the first lands) is in before the ring's yell.
        DrillCall const jav = CallAt(2, true);
        CHECK(jav.yellMs + LandMs(Command::Javelins) + kSecondVolleyWarnMs < CallAt(3, true).yellMs);
        // About 6 pairs in the 95 s fight (300k at 3,145).
        std::uint32_t const commands = CommandsBy(static_cast<std::uint32_t>(FightSeconds(true) * 1000.f), true);
        CHECK(commands >= 11 && commands <= 13);
        CHECK(LandMs(Command::Javelins) == 4500 && LandMs(Command::Charge) == 2500);
        CHECK(EndMs(Command::CloseRanks, true) == 10500);
    }

    // ---- the rooms ------------------------------------------------------------------------------------------------
    {
        // NAVMESH: the middle chamber 21 N-S x 38-42 E-W (666 sq yd); his spawn in it with 6.2 yd of clearance.
        CHECK(kMiddleChamber.Contains(kSpawn));
        CHECK(kMiddleChamber.xMax - kMiddleChamber.xMin >= 19.f && kMiddleChamber.xMax - kMiddleChamber.xMin <= 22.f);
        CHECK(kMiddleChamber.yMax - kMiddleChamber.yMin >= 38.f && kMiddleChamber.yMax - kMiddleChamber.yMin <= 45.f);
        // Free runs from the spawn (NAVMESH: north 9.5, south 8.0; the boxes hold the neck-less edge, 2 yd grid).
        CHECK(kMiddleChamber.xMax - kSpawn.x >= 9.5f && kMiddleChamber.xMax - kSpawn.x <= 11.f);
        CHECK(kSpawn.x - kMiddleChamber.xMin >= 8.f && kSpawn.x - kMiddleChamber.xMin <= 11.f);
        CHECK(RoomAt(kSpawn).xMin == kMiddleChamber.xMin);
        CHECK(RoomAt({ 1850.f, -400.f }).xMax == kSouthBand.xMax);
        CHECK(RoomAt({ 1900.f, -390.f }).xMin == kNorthRoom.xMin);
        // The Red Rockets (GO 103820, x 1895.6-1906.1, y -414.6 to -416.5) stand on the north room's south edge.
        CHECK(kNorthRoom.Contains({ 1898.f, -416.f }));
        // The necks join the rooms (each overlaps its two rooms).
        CHECK(kSouthNeck.xMin <= kSouthBand.xMax && kSouthNeck.xMax >= kMiddleChamber.xMin);
        CHECK(kNorthNeck.xMin <= kMiddleChamber.xMax && kNorthNeck.xMax >= kNorthRoom.xMin);
        CHECK(OnFloor(kSpawn) && !OnFloor({ 1875.f, -425.f }) && !OnFloor({ 1888.f, -390.f }));
        // The leash frame holds every floor box and his spawn.
        for (Room const& r : kWalkable)
            CHECK(RoomsArena().Contains({ (r.xMin + r.xMax) * 0.5f, (r.yMin + r.yMax) * 0.5f }, 18.7f));
        CHECK(!RoomsArena().Contains(kSpawn, 30.f));
    }

    // ---- the rank ---------------------------------------------------------------------------------------------------
    {
        // At his spawn facing north: x 1867, y -384 to -416 (NAVMESH), 8 yd apart, all on the floor.
        std::vector<Vec2> const rank = RankSpots(kSpawn, Facing::North, 5, 8.f);
        CHECK(rank.size() == 5);
        for (Vec2 const& p : rank)
        {
            CHECK(Near(p.x, 1867.f));
            CHECK(OnFloor(p));
        }
        CHECK(Near(rank.front().y, -384.f) && Near(rank.back().y, -416.f));
        for (float g : Gaps(rank))
            CHECK(Near(g, 8.f));
        // The middle recruit stands 8 yd straight behind him.
        CHECK(Near(rank[2].y, kSpawn.y) && Near(kSpawn.x - rank[2].x, kRankBehindYd));
        // Facing south: 8 yd north of him.
        std::vector<Vec2> const south = RankSpots(kSpawn, Facing::South, 5, 8.f);
        CHECK(Near(south[2].x, 1883.f));
        // His spawn faces south (the group comes up from the storeroom): out of combat the rank stands north of him.
        CHECK(SnapFacing(3.14159f) == Facing::South);
        for (Vec2 const& p : south)
            CHECK(OnFloor(p) && kMiddleChamber.Contains(p));
        // Heroic seven, 7 yd apart: 42 yd, wall to wall, so the eastern end closes in (the chamber's east wall at
        // -419, 1 yd margin: -418), the western end keeps 7 yd.
        std::vector<Vec2> const heroic = RankSpots(kSpawn, Facing::North, 7, 7.f);
        CHECK(heroic.size() == 7);
        CHECK(Near(heroic.front().y, -379.f));
        CHECK(heroic.back().y >= kMiddleChamber.yMin + kWallMarginYd - 0.01f);
        std::vector<float> const gaps = Gaps(heroic);
        CHECK(Near(gaps[0], 7.f) && Near(gaps[2], 7.f));
        CHECK(gaps[5] < 7.f && gaps[5] > 5.f);
        for (Vec2 const& p : heroic)
            CHECK(OnFloor(p));
        // Pulled toward the west wall: the west side closes in, the east keeps 8 yd, nobody leaves the room.
        std::vector<Vec2> const west = RankSpots({ 1875.f, -380.f }, Facing::North, 5, 8.f);
        CHECK(Near(west[2].y, -380.f));
        CHECK(west.front().y <= kMiddleChamber.yMax - kWallMarginYd + 0.01f);
        CHECK(Near(Gaps(west)[3], 8.f) && Gaps(west)[0] < 8.f);
        // Near the south wall facing north: the rank cannot stand 8 yd behind; it stops 1 yd off the wall.
        std::vector<Vec2> const tight = RankSpots({ 1869.f, -400.f }, Facing::North, 5, 8.f);
        CHECK(Near(tight[0].x, kMiddleChamber.xMin + kWallMarginYd));
        // Out of the middle chamber the rank stays in his room (the north room, facing south).
        std::vector<Vec2> const north = RankSpots({ 1897.f, -390.f }, Facing::South, 5, 8.f);
        for (Vec2 const& p : north)
            CHECK(kNorthRoom.Contains(p));
        CHECK(RankSpots(kSpawn, Facing::North, 0, 8.f).empty());
        CHECK(RankSpots(kSpawn, Facing::North, 1, 8.f).size() == 1);
    }

    // ---- facing -----------------------------------------------------------------------------------------------------
    {
        CHECK(ChooseFacing(kSpawn, { 1878.f, -400.f }, Facing::South) == Facing::North);
        CHECK(ChooseFacing(kSpawn, { 1872.f, -400.f }, Facing::North) == Facing::South);
        // Beside him (the hysteresis): the drill keeps its facing.
        CHECK(ChooseFacing(kSpawn, { 1876.f, -395.f }, Facing::South) == Facing::South);
        CHECK(ChooseFacing(kSpawn, { 1874.f, -405.f }, Facing::North) == Facing::North);
        CHECK(SnapFacing(0.f) == Facing::North && SnapFacing(3.1f) == Facing::South);
        CHECK(SnapFacing(1.5f) == Facing::North && SnapFacing(4.8f) == Facing::North);
        CHECK(Near(FacingAngle(Facing::South), DungeonKit::kPi));
    }

    // ---- MA1 lanes ----------------------------------------------------------------------------------------------
    {
        std::vector<Vec2> const rank = RankSpots(kSpawn, Facing::North, 5, 8.f);
        for (Vec2 const& spot : rank)
        {
            Lane const lane = ChargeLane(spot, Facing::North, kMiddleChamber);
            // Clipped at the north wall: from the rank 18 yd, i.e. 10 yd past him (section 7 #30 A: 8-10 yd free).
            CHECK(Near(lane.from.x, spot.x) && Near(lane.to.y, spot.y));
            CHECK(lane.to.x <= kMiddleChamber.xMax);
            CHECK(lane.to.x - kSpawn.x >= 8.f && lane.to.x - kSpawn.x <= 10.5f);
            CHECK(lane.to.x - lane.from.x <= kChargeLengthYd);
        }
        // 4 yd lanes at 8 yd: 4 yd gaps (heroic 7 yd: 3 yd gaps).
        CHECK(Near(kRankSpacingYd(false) - kChargeWidthYd, 4.f));
        CHECK(Near(kRankSpacingYd(true) - kChargeWidthYd, 3.f));
        // The middle lane runs through him (and the tank in front of him).
        Lane const middle = ChargeLane(rank[2], Facing::North, kMiddleChamber);
        CHECK(middle.from.x < kSpawn.x && middle.to.x > kSpawn.x + 3.f && Near(middle.from.y, kSpawn.y));
        // Facing south from the north side of the chamber: clipped at the south wall.
        Lane const back = ChargeLane({ 1883.f, -400.f }, Facing::South, kMiddleChamber);
        CHECK(back.to.x >= kMiddleChamber.xMin && back.to.x < 1866.f);
        // In the long south band a lane may run its full length only where the room allows (16 yd deep: clipped).
        Lane const band = ChargeLane({ 1845.f, -400.f }, Facing::North, kSouthBand);
        CHECK(band.to.x <= kSouthBand.xMax);
        // Never shorter than the minimum, even against the wall.
        Lane const wall = ChargeLane({ 1885.f, -400.f }, Facing::North, kMiddleChamber);
        CHECK(wall.to.x - wall.from.x >= kChargeMinLengthYd - 0.01f);
        // Space math (normal): five 4 x 18 lanes in the 666 sq yd chamber: 360 sq yd, about half the floor for 2.5 s
        // (the spec's 24% of its estimated hall; the lanes stop at the wall, the room is smaller).
        float area = 0.f;
        for (Vec2 const& spot : rank)
        {
            Lane const lane = ChargeLane(spot, Facing::North, kMiddleChamber);
            area += kChargeWidthYd * (lane.to.x - lane.from.x);
        }
        CHECK(area > 300.f && area < 400.f);
    }

    // ---- MA2 cones ----------------------------------------------------------------------------------------------
    {
        // From the rank 8 yd behind him, 10 yd ahead: 2 yd past him (his back and flanks; his front corners clear).
        CHECK(Near(kSpearsLengthYd - kRankBehindYd, 2.f));
        CHECK(Near(kSpearsAngleDeg, 60.f));
        // R-2-ARM m-6: tanked 4 yd off the wall at his back (middle chamber, facing north at x 1870: the rank is
        // clamped to x 1866), every cone still ends 2 yd past him, never over his front corners.
        {
            Vec2 const boss{ 1870.f, -400.f };
            std::vector<Vec2> const rank = RankSpots(boss, Facing::North, 7, 7.f);
            CHECK(Near(rank.front().x, 1866.f));
            float const length = SpearsLengthYd(rank.front().x, boss.x, Facing::North);
            CHECK(Near(length, 6.f));
            CHECK(Near(rank.front().x + length, boss.x + kSpearsPastBossYd));
            // In the open: the full 10 yd. Facing south mirrors it. Never under the floor or over the cap.
            std::vector<Vec2> const open = RankSpots(kSpawn, Facing::North, 5, 8.f);
            CHECK(Near(SpearsLengthYd(open.front().x, kSpawn.x, Facing::North), kSpearsLengthYd));
            CHECK(Near(SpearsLengthYd(1884.f, 1880.f, Facing::South), 6.f));
            CHECK(Near(SpearsLengthYd(1880.f, 1880.f, Facing::North), kSpearsPastBossYd));
            CHECK(Near(SpearsLengthYd(1890.f, 1880.f, Facing::North), kSpearsMinLengthYd));
            CHECK(Near(SpearsLengthYd(1850.f, 1880.f, Facing::North), kSpearsLengthYd));
        }
        CHECK(kKillLineCooldownMs == 5000);
        // Neighboring cones overlap before they reach him: a 60 degree cone is 8 yd wide (2 x 8 x tan 30 = 9.2) at
        // 8 yd, wider than the 8 yd spacing.
        float const halfWidthAtBoss = kRankBehindYd * std::tan(kSpearsAngleDeg * 0.5f * DungeonKit::kPi / 180.f);
        CHECK(2.f * halfWidthAtBoss > kRankSpacingYd(false));
        CHECK(2.f * halfWidthAtBoss > kRankSpacingYd(true));
    }

    // ---- MA3 javelins -------------------------------------------------------------------------------------------
    {
        Lcg rng;
        // Normal: five recruits, five players: a different player each.
        std::vector<std::uint32_t> picks = JavelinPicks(5, 5, false, rng);
        CHECK(picks.size() == 5);
        CHECK(std::set<std::uint32_t>(picks.begin(), picks.end()).size() == 5);
        // Normal with three players: three throws (a recruit with nobody left does not throw).
        CHECK(JavelinPicks(3, 5, false, rng).size() == 3);
        // Heroic: seven, the five different, then two at random players.
        for (int run = 0; run < 50; ++run)
        {
            std::vector<std::uint32_t> const h = JavelinPicks(5, 7, true, rng);
            CHECK(h.size() == 7);
            CHECK(std::set<std::uint32_t>(h.begin(), h.begin() + 5).size() == 5);
            for (std::uint32_t idx : h)
                CHECK(idx < 5);
        }
        // Heroic with two players: seven throws on the two.
        CHECK(JavelinPicks(2, 7, true, rng).size() == 7);
        CHECK(JavelinPicks(0, 7, true, rng).empty());
        // Normal lands on the player; heroic within 5 yd of them, on the floor.
        Vec2 const p{ 1878.f, -395.f };
        Vec2 const n = JavelinSpot(p, false, rng);
        CHECK(Near(n.x, p.x) && Near(n.y, p.y));
        float maxSeen = 0.f;
        for (int run = 0; run < 500; ++run)
        {
            Vec2 const s = JavelinSpot(p, true, rng);
            float const d = DungeonKit::Distance(s, p);
            CHECK(d <= kJavelinOffsetYd + 0.01f);
            CHECK(OnFloor(s));
            maxSeen = std::max(maxSeen, d);
        }
        CHECK(maxSeen > 3.f);
        // At a wall the spot stays on the floor.
        for (int run = 0; run < 200; ++run)
            CHECK(OnFloor(JavelinSpot({ 1875.f, -418.f }, true, rng)));
        // The look leaves the recruit so that it lands with the hit (2.5 s flight).
        CHECK(LookDelayMs(18.f, 2500) == 1500);
        CHECK(Near(kJavelinSpeed, 18.f));
        CHECK(LookDelayMs(60.f, 2500) == 0);
        CHECK(LookDelayMs(0.f, 2500) == 2500);
        // Five 5 yd circles: 79 sq yd each (the spec's space math).
        CHECK(Near(DungeonKit::kPi * kJavelinRadiusYd * kJavelinRadiusYd, 78.54f, 0.1f));
    }

    // ---- MA4 the ring -------------------------------------------------------------------------------------------
    {
        // Section 7 #30 A: 5 to 11 yd (the drill row's band); 6 s (heroic 8 s), a tick a second.
        CHECK(Near(kRingInnerYd, 5.f) && Near(kRingOuterYd, 11.f));
        CHECK(kRingMs(false) == 6000 && kRingMs(true) == 8000 && kRingTickMs == 1000);
        CHECK(kRingPathYd > kRingInnerYd && kRingPathYd < kRingOuterYd);
        // One lap in the ring's time.
        CHECK(Near(RingStepRad(false) * 6.f, 2.f * DungeonKit::kPi, 0.001f));
        CHECK(Near(RingStepRad(true) * 8.f, 2.f * DungeonKit::kPi, 0.001f));
        // The recruits start behind him, evenly spread, on the band, in the room.
        Vec2 const first = RingSpot(kSpawn, Facing::North, 0, 5, 0.f);
        CHECK(Near(first.x, kSpawn.x - kRingPathYd) && Near(first.y, kSpawn.y));
        for (std::uint32_t i = 0; i < 7; ++i)
            for (int step = 0; step < 8; ++step)
            {
                Vec2 const s = RingSpot(kSpawn, Facing::North, i, 7, RingStepRad(true) * static_cast<float>(step));
                CHECK(kMiddleChamber.Contains(s));
                float const d = DungeonKit::Distance(s, kSpawn);
                CHECK(d >= kRingInnerYd && d <= kRingOuterYd);
            }
        // Space math: the 5-11 yd band is 302 sq yd of circle; the chamber is only 21 yd deep, so it covers about a
        // third of its floor (section 7 #30 A).
        float const band = DungeonKit::kPi * (kRingOuterYd * kRingOuterYd - kRingInnerYd * kRingInnerYd);
        CHECK(band > 300.f && band < 305.f);
    }

    // ---- tuning -----------------------------------------------------------------------------------------------------
    {
        CHECK(Near(kHitPct(false), 30.f) && Near(kHitPct(true), 45.f));
        CHECK(Near(kRingPct(false), 10.f) && Near(kRingPct(true), 12.f));
        CHECK(kRecruits(false) == 5 && kRecruits(true) == 7 && kMaxRecruits == 7);
        CHECK(Near(kRankSpacingYd(false) * 4.f, 32.f) && Near(kRankSpacingYd(true) * 6.f, 42.f));
        // 60k / 768 = 78 s; 300k / 3,145 = 95 s; the bots at half: 156 s and 191 s.
        CHECK(std::fabs(FightSeconds(false) - 78.1f) < 0.5f);
        CHECK(std::fabs(FightSeconds(true) - 95.4f) < 0.5f);
        CHECK(std::fabs(FightSeconds(false, 0.5f) - 156.3f) < 0.5f);
        CHECK(kJavelinCastMs == 2000 && kJavelinFlightMs == 2500 && kSecondVolleyWarnMs == 1500 && kReadyMs == 2500);
    }

    // ---- the clock ----------------------------------------------------------------------------------------------
    {
        Timer t;
        CHECK(!t.Due(0) && !t.On());
        t.Start(100, 400);
        CHECK(!t.Due(499) && t.Due(500) && t.DueMs() == 500);
        t.Stop();
        CHECK(!t.Due(1000));
    }

    return Report("sm_halden_test");
}
