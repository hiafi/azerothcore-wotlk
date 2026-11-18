// Host tests for MagmusLogic.h (D22: Magmus and the Ironhand Guardians): the slice, the text groups, the spec's
// numbers, the hall geometry (the lane wall to wall at his y, the strips over the alcoves, the side choice), the
// timeline (the first beats, the cadences, "nothing holds the group in a lane"), the Crossfire plan and the breath
// schedule, and the Dripping Magma walk tracker with its cap.
#include "MagmusLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdMagmus;
using DungeonKit::Vec2;

namespace
{
    bool Near(float a, float b, float eps = 0.05f)
    {
        return std::fabs(a - b) <= eps;
    }

    // One start of a beat, as the engine's UpdateAI runs it: the Crossfire first (it waits for a cast in progress and
    // retries a second later), then the Flame Wall, the stomp and the Fiery Burst (neither while a cast is going on),
    // every 100 ms. The Fiery Burst is a 2 s cast.
    struct Fire
    {
        std::uint64_t at = 0;
        Beat beat = Beat::Stomp;
    };

    std::vector<Fire> Run(bool heroic, std::uint64_t horizonMs, std::uint32_t stompGapMs = 10000)
    {
        std::vector<Fire> fires;
        Timeline t;
        t.Start(heroic, 0, stompGapMs);
        std::uint64_t castEnd = 0;
        for (std::uint64_t now = 0; now <= horizonMs; now += 100)
        {
            bool const casting = now < castEnd;
            if (t.Due(Beat::Crossfire, now))
            {
                if (!casting)
                {
                    t.Fired(Beat::Crossfire, now);
                    fires.push_back({ now, Beat::Crossfire });
                }
                else
                    t.Retry(Beat::Crossfire, now);
            }
            if (t.Due(Beat::FlameWall, now))
            {
                t.Fired(Beat::FlameWall, now);
                fires.push_back({ now, Beat::FlameWall });
            }
            if (t.Due(Beat::Stomp, now) && now >= castEnd)
            {
                t.Fired(Beat::Stomp, now, stompGapMs);
                fires.push_back({ now, Beat::Stomp });
            }
            if (t.Due(Beat::Burst, now) && now >= castEnd)
            {
                t.Fired(Beat::Burst, now);
                fires.push_back({ now, Beat::Burst });
                castEnd = now + kBurstCastMs;
            }
        }
        return fires;
    }

    std::vector<std::uint64_t> Times(std::vector<Fire> const& fires, Beat beat)
    {
        std::vector<std::uint64_t> out;
        for (Fire const& f : fires)
            if (f.beat == beat)
                out.push_back(f.at);
        return out;
    }

    // The lane's glow windows of a replay: [start, start + kGlowMs).
    bool InGlow(std::vector<std::uint64_t> const& crossfires, std::uint64_t at, std::uint32_t leadMs = 0)
    {
        for (std::uint64_t const start : crossfires)
            if (at + leadMs > start && at < start + kGlowMs)
                return true;
        return false;
    }
}

int main()
{
    // ---- ids, tags, texts ----------------------------------------------------------------------------------------

    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(kSpellSlice.last));
    CHECK(kSpellSlice.first == 211580 && kSpellSlice.last == 211609);
    CHECK(SPELL_MG_WAR_STOMP == 211580 && SPELL_MG_POOL_LOOK == 211591 && kLastSpell == 211591);
    CHECK(kLastSpell <= kSpellSlice.last);
    // G2's drill tags (BM MechanicDrill.h kBrd2BarTags = 22, 25, 26, 27): the bots' follow-ups are tuned on them.
    CHECK(TAG_MG_CROSSFIRE_IGNITION == 25 && TAG_MG_CROSSFIRE_BURN == 26 && TAG_MG_FLAME_WALL == 27);
    CHECK(TAG_MG_FIERY_BURST != 22 && TAG_MG_DRIPPING_MAGMA != 22);     // 22 is the Seven's loner
    // Texts: group 0 stock (the instance's), 1-3 new, inside the header's range of 9938 (0-3, 1 stock).
    CHECK(SAY_MAGMUS_BRAZIERS_LIT == kSayMagmusBraziersLit);
    CHECK(EMOTE_MAGMUS_FIST == 1 && YELL_MAGMUS_WALL == 2 && YELL_MAGMUS_DEATH == 3);
    {
        bool found = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_MAGMUS)
            {
                found = true;
                CHECK(range.first == 0 && range.last == YELL_MAGMUS_DEATH && range.firstNew == 1);
            }
        CHECK(found);
    }

    // ---- the spec's numbers --------------------------------------------------------------------------------------

    CHECK(kBurstPct(false) == 25.f && kBurstPct(true) == 40.f);
    CHECK(kCrossfireIgnitionPct(false) == 30.f && kCrossfireIgnitionPct(true) == 45.f);
    CHECK(kCrossfireBurnPct(false) == 10.f && kCrossfireBurnPct(true) == 15.f);
    CHECK(kWallPct(false) == 10.f && kWallPct(true) == 15.f);
    CHECK(kPoolPct == 8.f && kPoolRadiusYd == 4.f && kPoolLifeMs == 30000 && kPoolEveryMs == 3000);
    CHECK(kStompStunMs == 2000);                // ruling 76: the stun drops from 8 s to 2 s
    CHECK(kStompRadiusYd == 5.f && kBurstRadiusYd == 8.f && kBurstCastMs == 2000);
    CHECK(kLaneWidthYd == 10.f && kWallStripYd == 12.f && kGlowMs == 3000);
    CHECK(kCrossfireFirstMs == 8000 && kCrossfireEveryMs(false) == 15000 && kCrossfireEveryMs(true) == 12000);
    CHECK(kWallFirstMs == 20000 && kWallEveryMs(false) == 30000 && kWallEveryMs(true) == 25000);
    CHECK(kBurstFirstMs == 6000 && kBurstEveryMs == 10000);
    CHECK(kStompEveryMinMs == 8000 && kStompEveryMaxMs == 12000);
    // G2's drill rows: the burn's first tick is 1 s after the ignition, 5 s of ticks, a tick a second; the Flame Wall
    // is 8 s a second after its 3 s warning.
    CHECK(kBurnWarnMs == kGlowMs + 1000 && kBurnLifeMs == 5000 && kBurnTickMs == 1000);
    CHECK(kWallLifeMs == 8000 && kWallTickMs == 1000 && kWallEndMs == 11000 && kCrossfireEndMs == 9000);
    // A pool's persistence is its life after the 1.5 s warning.
    CHECK(PoolLifeAfterWarnMs() == 28500);

    // ---- the arena and the hall ----------------------------------------------------------------------------------

    CHECK(MagmusArena().Contains(kMagmusSpawn.XY(), kMagmusSpawn.z));
    CHECK(ArenaFor(BOSS_MAGMUS).Contains(kMagmusSpawn.XY(), kMagmusSpawn.z));
    // The hall (NM 4.5: 39 yd) is inside the leash box; the statues stand in the alcoves, outside it.
    CHECK(Near(kHallHighX - kHallLowX, 39.f));
    CHECK(MagmusArena().Contains({ kHallLowX + 0.5f, -640.f }, -92.f));
    CHECK(MagmusArena().Contains({ kHallHighX - 0.5f, -640.f }, -92.f));
    CHECK(!MagmusArena().Contains({ kStatueLowX, kStatueRowY[0] }, kStatueZ));
    CHECK(!MagmusArena().Contains({ kStatueHighX, kStatueRowY[0] }, kStatueZ));
    // The hall's ends are the arena's (the entrance end and the throne end).
    CHECK(kHallYMax == -550.f && kHallYMin == -720.f);
    CHECK(kMagmusSpawn.y < kHallYMax && kMagmusSpawn.y > kHallYMin);
    CHECK(Near(kHallCenterX, 1380.7f));

    // ---- the statue rows -----------------------------------------------------------------------------------------

    CHECK(NearestStatueRow(-587.3f) == 0 && NearestStatueRow(-632.8f) == 1 && NearestStatueRow(-677.4f) == 2);
    CHECK(NearestStatueRow(-560.f) == 0 && NearestStatueRow(-715.f) == 2);
    CHECK(NearestStatueRow(kMagmusSpawn.y) == 2);       // 18 yd from the third row, 27 from the second
    CHECK(StatueSideOf(1353.43f) == Side::LowX && StatueSideOf(1353.92f) == Side::LowX
        && StatueSideOf(1353.16f) == Side::LowX);
    CHECK(StatueSideOf(1407.29f) == Side::HighX && StatueSideOf(1406.88f) == Side::HighX
        && StatueSideOf(1407.67f) == Side::HighX);
    CHECK(StatueX(Side::LowX) == kStatueLowX && StatueX(Side::HighX) == kStatueHighX);

    // ---- MG3 the lane: wall to wall at his y ---------------------------------------------------------------------

    {
        Lane const lane = LaneAt(kMagmusSpawn.y);
        CHECK(Near(lane.center.y, kMagmusSpawn.y) && lane.from.y == lane.to.y);
        CHECK(lane.facing == 0.f && lane.width == 10.f);
        // statue to statue plus the overrun: it reaches both columns and the floor between
        CHECK(Near(lane.from.x, kStatueLowX - kLaneOverrunYd) && Near(lane.to.x, kStatueHighX + kLaneOverrunYd));
        CHECK(Near(lane.length, lane.to.x - lane.from.x));
        CHECK(lane.length > kHallHighX - kHallLowX);
        CHECK(lane.row == 2);
        // every point of the floor across the hall at his y is in it; 5.1 yd either side is not; the rest of the hall
        // beside the lane (the group's flank) is clear
        for (float x = kHallLowX; x <= kHallHighX + 0.01f; x += 1.f)
        {
            CHECK(InLane(lane, { x, kMagmusSpawn.y }));
            CHECK(InLane(lane, { x, kMagmusSpawn.y + 4.9f }));
            CHECK(!InLane(lane, { x, kMagmusSpawn.y + 5.1f }));
            CHECK(!InLane(lane, { x, kMagmusSpawn.y - 5.1f }));
        }
        // the alcoves with their statues are in it too (nobody hides there when he stands at a row)
        Lane const row = LaneAt(kStatueRowY[1]);
        CHECK(InLane(row, { kStatueLowX, kStatueRowY[1] }) && InLane(row, { kStatueHighX, kStatueRowY[1] }));
        CHECK(row.row == 1);
        // the lane's center is between the pair
        CHECK(lane.center.x > kStatueLowX && lane.center.x < kStatueHighX);
        CHECK(Near(lane.center.x, kHallCenterX, 0.5f));
    }
    // A lane stays on the hall: y is clamped so its 10 yd does not leave the ends.
    CHECK(Near(ClampLaneY(-549.f), kHallYMax - 5.f) && Near(ClampLaneY(-721.f), kHallYMin + 5.f));
    CHECK(Near(ClampLaneY(-650.f), -650.f));
    CHECK(LaneAt(-100.f).center.y == kHallYMax - 5.f && LaneAt(-100.f).row == 0);

    // The plan of one Crossfire: the glow, the ignition 3 s after the fist, the last burn tick at 9 s.
    {
        CrossfirePlan const plan = PlanCrossfire(10000);
        CHECK(plan.startMs == 10000 && plan.ignitionMs == 13000 && plan.endMs == 19000);
        CHECK(plan.Glowing(10000) && plan.Glowing(12999) && !plan.Glowing(13000) && !plan.Glowing(9999));
        CHECK(!plan.Burning(12999) && plan.Burning(13000) && plan.Burning(19000) && !plan.Burning(19001));
        // the breath schedule: the ignition, then every 2 s while the burn lasts (3, 5, 7, 9 s after the fist)
        std::vector<std::uint64_t> breaths;
        std::uint64_t last = 0;
        for (int i = 0; i < 20; ++i)
        {
            std::uint64_t const due = NextBreathMs(plan.ignitionMs, last, plan.endMs);
            if (!due)
                break;
            breaths.push_back(due);
            last = due;
        }
        CHECK((breaths == std::vector<std::uint64_t>{ 13000, 15000, 17000, 19000 }));
        CHECK(NextBreathMs(plan.ignitionMs, 19000, plan.endMs) == 0);
        // the Flame Wall's: from the glow's end, 8 s of strip
        CHECK(NextBreathMs(kGlowMs, 0, kWallEndMs) == kGlowMs && NextBreathMs(kGlowMs, 9000, kWallEndMs) == 11000
            && NextBreathMs(kGlowMs, 11000, kWallEndMs) == 0);
    }

    // ---- MG4 the strips ------------------------------------------------------------------------------------------

    for (Side const side : { Side::LowX, Side::HighX })
    {
        Strip const strip = StripOf(side);
        CHECK(Near(strip.width, 20.f) && Near(std::fabs(strip.innerX - strip.outerX), strip.width));
        CHECK(Near(strip.length, 170.f) && strip.facing == kFacingToThrone);
        CHECK(Near(strip.from.y, kHallYMax) && Near(strip.from.x, strip.centerX));
        // 12 yd of floor from the wall, and the alcove behind it (8 yd past the wall)
        if (side == Side::LowX)
        {
            CHECK(Near(strip.innerX, kHallLowX + 12.f) && Near(strip.outerX, kHallLowX - 8.f));
            CHECK(InStrip(strip, { kHallLowX, -640.f }) && InStrip(strip, { kHallLowX + 11.9f, -640.f }));
            CHECK(!InStrip(strip, { kHallLowX + 12.1f, -640.f }));
            CHECK(InStrip(strip, { kStatueLowX, kStatueRowY[0] }));     // the statues' alcoves are in it
            CHECK(InStrip(strip, { kStatueLowX, kStatueRowY[2] }));
        }
        else
        {
            CHECK(Near(strip.innerX, kHallHighX - 12.f) && Near(strip.outerX, kHallHighX + 8.f));
            CHECK(InStrip(strip, { kHallHighX, -640.f }) && InStrip(strip, { kHallHighX - 11.9f, -640.f }));
            CHECK(!InStrip(strip, { kHallHighX - 12.1f, -640.f }));
            CHECK(InStrip(strip, { kStatueHighX, kStatueRowY[0] }));
            CHECK(InStrip(strip, { kStatueHighX, kStatueRowY[2] }));
        }
        // the whole hall's length: the entrance end and the throne end
        CHECK(InStrip(strip, { strip.centerX, kHallYMax }) && InStrip(strip, { strip.centerX, kHallYMin }));
        CHECK(!InStrip(strip, { strip.centerX, kHallYMax + 1.f }));
        CHECK(!InStrip(strip, { strip.centerX, kHallYMin - 1.f }));
        // his own spot is never in the strip chosen for him (the side choice below), and the middle is clear
        CHECK(!InStrip(strip, { kHallCenterX, -640.f }));
        // the far walls' statues are not in this side's strip
        CHECK(!InStrip(strip, { side == Side::LowX ? kStatueHighX : kStatueLowX, kStatueRowY[1] }));
    }
    CHECK(Near(FloorLeftYd(), 27.f));                   // 39 - 12 (G2's drill: 27 yd of floor left)
    // The breath points: down the hall from each statue's row, on the strip's line, inside the hall's length.
    for (std::size_t row = 0; row < kStatueRows; ++row)
        for (Side const side : { Side::LowX, Side::HighX })
        {
            Vec2 const p = WallBreathPoint(side, row);
            CHECK(Near(p.x, StripOf(side).centerX) && Near(p.y, kStatueRowY[row] - kWallBreathReachYd));
            CHECK(p.y > kHallYMin);
        }

    // The side: never the one whose floor strip he stands on; otherwise the sides alternate.
    CHECK(ChooseWallSide(kMagmusSpawn.x, std::nullopt, 0) == Side::LowX);
    CHECK(ChooseWallSide(kMagmusSpawn.x, std::nullopt, 1) == Side::HighX);
    CHECK(ChooseWallSide(kMagmusSpawn.x, Side::LowX, 0) == Side::HighX);
    CHECK(ChooseWallSide(kMagmusSpawn.x, Side::HighX, 1) == Side::LowX);
    CHECK(ChooseWallSide(1365.f, Side::LowX, 0) == Side::HighX);        // on the low-x floor strip: the other side
    CHECK(ChooseWallSide(1365.f, std::nullopt, 0) == Side::HighX);
    CHECK(ChooseWallSide(1397.f, Side::HighX, 1) == Side::LowX);
    CHECK(ChooseWallSide(1397.f, std::nullopt, 1) == Side::LowX);
    CHECK(ChooseWallSide(1377.f, std::nullopt, 0) == Side::HighX);      // 16 yd in: still counted (body margin)
    CHECK(ChooseWallSide(1378.f, std::nullopt, 0) == Side::LowX);       // 16.8 yd in: free of both
    for (float x = kHallLowX; x <= kHallHighX; x += 0.5f)
    {
        Side const side = ChooseWallSide(x, std::nullopt, 0);
        CHECK(!InStrip(StripOf(side), { x, -640.f }));
    }

    // ---- the timeline --------------------------------------------------------------------------------------------

    for (bool const heroic : { false, true })
    {
        std::vector<Fire> const fires = Run(heroic, 300000);
        std::vector<std::uint64_t> const crossfire = Times(fires, Beat::Crossfire);
        std::vector<std::uint64_t> const wall = Times(fires, Beat::FlameWall);
        std::vector<std::uint64_t> const stomp = Times(fires, Beat::Stomp);
        std::vector<std::uint64_t> const burst = Times(fires, Beat::Burst);

        // The first beats: the Fiery Burst at 6 s, the Crossfire at 8 s, the Flame Wall at 20 s.
        CHECK(!burst.empty() && burst.front() == 6000);
        CHECK(!crossfire.empty() && crossfire.front() == 8000);
        CHECK(!wall.empty() && wall.front() == 20000);
        // the replay's stomp gap is 10 s: due at 10 s, inside the first Crossfire's glow (8-11 s), so it waits
        CHECK(!stomp.empty() && stomp.front() == 11000);

        // The cadences: every 15 s (12 heroic) and every 30 s (25 heroic), on the grid.
        std::uint32_t const crossEvery = kCrossfireEveryMs(heroic);
        std::uint32_t const wallEvery = kWallEveryMs(heroic);
        for (std::size_t i = 1; i < wall.size(); ++i)
            CHECK(wall[i] - wall[i - 1] == wallEvery);
        CHECK(crossfire.size() == (300000 - 8000) / crossEvery + 1);

        // "Nothing holds the group in a lane": no Fiery Burst cast starts in a glow, no stomp starts in one or
        // within the stun's length of one.
        for (std::uint64_t const at : burst)
            CHECK(!InGlow(crossfire, at));
        for (std::uint64_t const at : stomp)
            CHECK(!InGlow(crossfire, at, kStompStunMs));
        // ... and a Fiery Burst cast in progress never stops a Crossfire for more than the cast: nothing is starved.
        for (std::size_t i = 0; i < crossfire.size(); ++i)
        {
            std::uint64_t const planned = 8000 + i * crossEvery;
            CHECK(crossfire[i] >= planned && crossfire[i] - planned <= kBurstCastMs + 100);
        }
        // The stomp and the burst are never starved either: a stomp at least every 20 s, a burst at least every 15 s.
        for (std::size_t i = 1; i < stomp.size(); ++i)
            CHECK(stomp[i] - stomp[i - 1] <= 20000);
        for (std::size_t i = 1; i < burst.size(); ++i)
            CHECK(burst[i] - burst[i - 1] <= 15000);
        CHECK(stomp.size() > 15 && burst.size() > 18);
    }

    // The stomp's gap rolls 8-12 s (the engine passes it to Fired): a stomp never starts early.
    for (std::uint32_t gap = kStompEveryMinMs; gap <= kStompEveryMaxMs; gap += 1000)
    {
        std::vector<Fire> const fires = Run(false, 120000, gap);
        std::vector<std::uint64_t> const stomp = Times(fires, Beat::Stomp);
        CHECK(!stomp.empty() && stomp.front() >= gap && stomp.front() <= 12000);   // 8-11 s wait for the glow
        for (std::size_t i = 1; i < stomp.size(); ++i)
            CHECK(stomp[i] - stomp[i - 1] >= gap);
    }

    // A beat that cannot start tries again a second later; the grid does not move.
    {
        Timeline t;
        t.Start(false, 0, 10000);
        CHECK(!t.Due(Beat::Crossfire, 7900) && t.Due(Beat::Crossfire, 8000));
        t.Retry(Beat::Crossfire, 8000);
        CHECK(!t.Due(Beat::Crossfire, 8900) && t.Due(Beat::Crossfire, 9000));
        t.Fired(Beat::Crossfire, 9000);
        CHECK(t.crossfireAt == 23000);              // the grid (8, 23, 38, ...), not 9 + 15
        CHECK(t.glowUntil == 12000);
        // the stomp and the burst hold during the glow, then go at once
        t.stompAt = 9500;
        t.burstAt = 9500;
        CHECK(!t.Due(Beat::Stomp, 10000) && !t.Due(Beat::Burst, 10000));
        CHECK(!t.Due(Beat::Stomp, 11900) && !t.Due(Beat::Burst, 11900));
        CHECK(t.Due(Beat::Stomp, 12000) && t.Due(Beat::Burst, 12000));
        // ... and a stomp within 2 s of the next Crossfire waits, a Fiery Burst does not (it only needs the glow over)
        t.stompAt = 20000;
        t.burstAt = 20000;
        CHECK(t.Due(Beat::Stomp, 21000) && !t.Due(Beat::Stomp, 21100));     // 21.1 s + 2 s > 23 s
        CHECK(t.Due(Beat::Burst, 22900));
        CHECK(!t.Due(Beat::Burst, 23100));                                  // the Crossfire is due: it goes first
    }

    // ---- MG5 Dripping Magma ---------------------------------------------------------------------------------------

    CHECK(PoolsToRetire(0) == 0 && PoolsToRetire(5) == 0 && PoolsToRetire(6) == 1 && PoolsToRetire(7) == 2);
    CHECK(kPoolCap == 6);
    {
        // Standing still for a minute: no pool (they fall only while he walks).
        DripTracker drip;
        Vec2 at{ 1380.7f, -659.3f };
        drip.Start(0, at);
        int pools = 0;
        for (std::uint64_t now = 100; now <= 60000; now += 100)
            if (drip.Step(now, at, 100))
                ++pools;
        CHECK(pools == 0);
        // Micro adjustments (0.05 yd a tick = 0.5 yd/s) never add up to a step.
        for (std::uint64_t now = 60100; now <= 120000; now += 100)
        {
            at.y += (now / 100) % 2 ? 0.05f : -0.05f;
            if (drip.Step(now, at, 100))
                ++pools;
        }
        CHECK(pools == 0);
    }
    {
        // Walking 2 yd/s for 10 s from the pull: a pool each 3 s, the first at 3 s.
        DripTracker drip;
        Vec2 at{ 1380.7f, -600.f };
        drip.Start(0, at);
        std::vector<std::uint64_t> drops;
        for (std::uint64_t now = 100; now <= 10000; now += 100)
        {
            at.y -= 0.2f;
            if (drip.Step(now, at, 100))
                drops.push_back(now);
        }
        CHECK(drops.size() == 3);
        CHECK(!drops.empty() && drops[0] >= 3000 && drops[0] <= 3100);
        for (std::size_t i = 1; i < drops.size(); ++i)
            CHECK(drops[i] - drops[i - 1] >= kPoolEveryMs && drops[i] - drops[i - 1] <= kPoolEveryMs + 100);
    }
    {
        // A Crossfire move: he stands 20 s, walks 3 s at 4 yd/s (one pool when he starts, since a pool is long due),
        // stands again. 1 or 2 pools per move (the spec).
        DripTracker drip;
        Vec2 at{ 1380.7f, -659.3f };
        drip.Start(0, at);
        std::uint64_t now = 0;
        int pools = 0;
        for (now = 100; now <= 20000; now += 100)
            drip.Step(now, at, 100);
        for (int i = 0; i < 30; ++i)
        {
            now += 100;
            at.y += 0.4f;
            if (drip.Step(now, at, 100))
                ++pools;
        }
        CHECK(pools >= 1 && pools <= 2);
        // the walk stops: nothing more
        for (int i = 0; i < 100; ++i)
        {
            now += 100;
            if (drip.Step(now, at, 100))
                ++pools;
        }
        CHECK(pools >= 1 && pools <= 2);
    }
    {
        // No pool with the first call (it only starts the tracker), and none without a measured step.
        DripTracker drip;
        CHECK(!drip.Step(5000, { 0.f, 0.f }, 100));
        CHECK(drip.haveLast && drip.nextAt == 5000 + kPoolEveryMs);
        CHECK(!drip.Step(9000, { 100.f, 0.f }, 0));         // diff 0: not a speed
    }

    return Report("brd_magmus_test");
}
