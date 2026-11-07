/*
 * mod-dungeon-bosses, Deadmines: Gilnid, the iron shot and the land mine (WP-B4), the pure, host-testable part (no
 * engine headers): spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: DM 'Gilnid'
 * Build spec GI1-GI7; handoff section 3.4 rows GI, section 3.8 (the foundry frame), section 7 #6 (Hot shot segments).
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`. Tested by tests/gilnid_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_GILNID_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_GILNID_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <utility>
#include <vector>

namespace Gilnid
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsGilnid;

    // Declared in apps/dbc-tools source/npcs/deadmines/gilnid.py. The three resolve copies are bound to
    // spell_boss_mechanics_resolve (the registry sets their damage); the rest carry visuals copied from the build
    // spec's stock sources (never cast the stock spells themselves: DM "Implementation notes", copy the visual).
    enum GilnidSpells : std::uint32_t
    {
        SPELL_ROLL_OUT_THE_SHOT     = 205270,   // GI2 ball hit: resolve copy, Physical, impact SV 1564 (Cannon Ball)
        SPELL_BOWLED_OVER           = 205271,   // GI3 2 s stun on Gilnid, mechanic 0 (passes immunity set 1972)
        SPELL_HOT_SHOT              = 205272,   // GI4 trail tick: resolve copy, Fire
        SPELL_LAND_MINE_DETONATION  = 205273,   // GI6/GI7 blast: resolve copy, Fire
        SPELL_SHOT_POUR             = 205274,   // the pot pours: on the ball at the pot (SV 380, Molten Metal 5213)
        SPELL_SHOT_LAUNCH           = 205275,   // the ball leaves the pot (SV 8030, Flaming Cannonball 29639)
        SPELL_RED_HOT               = 205276,   // the ball's glow, a DUMMY aura (SV 4101, the look of Lava 16455)
        SPELL_LAND_MINE_ARMING      = 205277,   // the mine's arming look, a DUMMY aura (SV 34, Land Mine Arming)
        SPELL_LAND_MINE_BLAST       = 205278,   // the mine's blast look (SV 148, Detonation 4043)
        SPELL_LAND_MINE_FIZZLE      = 205279,   // the oldest mine fizzles at the cap (SV 1931, Spawn Smoke 10389)
        SPELL_TOSS_LANDMINE         = 205280,   // Gilnid tosses a mine (SV 74, Goblin Land Mine 4100)
        SPELL_HOT_SHOT_GROUND       = 205281,   // GI4 a trail segment's slag look: 6 s dynamic object (SV 90340)
        SPELL_SHOT_FLAME_BLAST      = 205282,   // GI2 the rolling shot's look: Flame Blast 7101's SV 33 at a point
        // 205283-205289 spare
    };
    static_assert(kSlice.Contains(SPELL_ROLL_OUT_THE_SHOT) && kSlice.Contains(SPELL_SHOT_FLAME_BLAST),
        "Gilnid's spells stay inside his slice");

    // Registry tags (ledger and failure listing): the build spec's mechanic numbers.
    inline constexpr std::uint32_t kTagRollOut = 2;     // GI2
    inline constexpr std::uint32_t kTagHotShot = 4;     // GI4
    inline constexpr std::uint32_t kTagLandmine = 6;    // GI6 / GI7 (one mechanic: arming, then armed)
    inline constexpr std::uint32_t kMineCapGroup = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec GI1-GI7, Tuning starting points). Times in ms, damage in % of the reference row.
    // ----------------------------------------------------------------------------------------------------------------

    // GI1 Molten Metal (stock 5213; DD scales it on heroic): 1 to 6 s, then every 15 to 25 s.
    inline constexpr std::uint32_t kMoltenMetalFirstMinMs = 1000;
    inline constexpr std::uint32_t kMoltenMetalFirstMaxMs = 6000;
    inline constexpr std::uint32_t kMoltenMetalRepeatMinMs = 15000;
    inline constexpr std::uint32_t kMoltenMetalRepeatMaxMs = 25000;
    inline constexpr std::uint32_t kMoltenMetalEveryMs = 20000;         // the descriptor's cadence (the mean)

    // GI2 Roll Out the Shot.
    inline constexpr std::uint32_t kShotFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kShotCooldownMs{ 18000, 15000 };
    inline constexpr std::uint32_t kDoubleShiftCooldownMs = 10000;      // GI5, heroic below 50%
    inline constexpr NH<bool> kDoubleShift{ false, true };
    inline constexpr float kDoubleShiftHealthPct = 50.f;
    inline constexpr std::uint32_t kShotTargetsNormal = 2;              // random non-tanks; heroic: every player
    inline constexpr std::uint32_t kLaneWarnMs = 2000;
    inline constexpr float kLaneWidth = 4.f;
    inline constexpr float kShotSpeed = 10.f;                           // yd per s
    inline constexpr float kShotPct = 30.f;
    inline constexpr float kLaneWallInset = 0.5f;                       // the wall point: this far inside the wall
    // Playtest 1: every lane runs this much further than the wall point (marker, roll and hitbox alike). The measured
    // room ends 34 to 37.5 yd from the pots on the north and west (8 to 17 yd east and south), so the extra length
    // lies past the navmesh wall except through the Foundry Door; NAVMESH-REPORT section 1.
    inline constexpr float kLaneExtraYd = 30.f;
    inline constexpr float kShotTargetRange = 60.f;                     // players this close to Gilnid are targets
    inline constexpr std::uint32_t kShotLingerMs = 1000;                // the ball rests at the lane end, then goes
    // The shot's look (playtest 1): a Flame Blast burst at its feet this often while it rolls (4 yd apart at 10 yd
    // per s), along a path that follows the floor (a point every kFloorPathStepYd at the floor height, so it never
    // floats off the dais edge). A floor probe further than kFloorPathMaxStepZ from the last point is ignored.
    inline constexpr std::uint32_t kFlameBlastPulseMs = 400;
    inline constexpr float kFloorPathStepYd = 2.f;
    inline constexpr float kFloorPathMaxStepZ = 2.5f;

    // GI3 Bowled Over: a ball whose center passes this close to Gilnid's center (half a lane plus a little of his
    // body) knocks him down for 2 s (the spell's duration) and takes 5% of his health. Once per ball.
    inline constexpr float kBowledOverRadius = 2.5f;
    inline constexpr float kBowledOverHealthPct = 5.f;
    inline constexpr std::uint32_t kBowledOverYellCooldownMs = 30000;   // text line 5, at most once per 30 s

    // GI4 Hot shot (heroic): 4 yd persistent segments of the lane, registered as the ball passes each one (handoff
    // section 7 #6), 6 s, ticks 1 s, 5% Fire, the shared slow rider.
    inline constexpr NH<bool> kHotShot{ false, true };
    inline constexpr float kHotShotSegmentYd = 4.f;
    inline constexpr std::uint32_t kHotShotDurationMs = 6000;
    inline constexpr std::uint32_t kHotShotTickMs = 1000;
    inline constexpr float kHotShotPct = 5.f;

    // GI6/GI7 Landmine (heroic): a 4 yd mine at a random non-tank's feet, arms after 3 s, 0.5 s grace once armed,
    // 35% Fire + Weakened, at most 6 live (a 7th makes the oldest fizzle); first at 12 s, then every 20 s (Double
    // shift does not speed it up).
    inline constexpr NH<bool> kLandmine{ false, true };
    inline constexpr float kMineRadius = 4.f;
    inline constexpr std::uint32_t kMineArmMs = 3000;
    inline constexpr std::uint32_t kMineGraceMs = 500;
    inline constexpr std::uint8_t kMineCap = 6;
    inline constexpr float kMinePct = 35.f;
    inline constexpr std::uint32_t kMineFirstMs = 12000;
    inline constexpr std::uint32_t kMineCooldownMs = 20000;
    // A ball sets off an armed mine when its center passes within the mine's radius.
    inline constexpr float kBallMineRadius = kMineRadius;

    // The out of combat say (stock SmartAI 1763 event 1: every 120 s).
    inline constexpr std::uint32_t kOutOfCombatSayMs = 120000;

    // GI2's cooldown after this batch: 18 s normal, 15 s heroic, 10 s once Double shift is on (heroic only).
    inline std::uint32_t ShotCooldownMs(bool heroic, bool doubleShift)
    {
        if (heroic && doubleShift)
            return kDoubleShiftCooldownMs;
        return kShotCooldownMs(heroic);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Targets
    // ----------------------------------------------------------------------------------------------------------------

    template <typename Id>
    struct Candidate
    {
        Id id{};
        bool tank = false;
    };

    // GI2's targets: heroic, every candidate (the tank included); normal, up to kShotTargetsNormal random non-tanks
    // (when nobody but the tank is there, the tank, so a lone tester still sees a lane). `roll(n)` returns a value in
    // [0, n).
    template <typename Id, typename Roll>
    std::vector<Id> SelectShotTargets(std::vector<Candidate<Id>> const& candidates, bool heroic, Roll&& roll)
    {
        std::vector<Id> out;
        if (heroic)
        {
            for (Candidate<Id> const& c : candidates)
                out.push_back(c.id);
            return out;
        }
        std::vector<Id> pool;
        for (Candidate<Id> const& c : candidates)
            if (!c.tank)
                pool.push_back(c.id);
        if (pool.empty())
            for (Candidate<Id> const& c : candidates)
                pool.push_back(c.id);
        while (!pool.empty() && out.size() < kShotTargetsNormal)
        {
            std::size_t const i = static_cast<std::size_t>(roll(static_cast<std::uint32_t>(pool.size())));
            std::size_t const pick = i < pool.size() ? i : pool.size() - 1;
            out.push_back(pool[pick]);
            pool.erase(pool.begin() + static_cast<std::ptrdiff_t>(pick));
        }
        return out;
    }

    // GI6's target: a random non-tank (nullopt when there is none).
    template <typename Id, typename Roll>
    std::optional<Id> SelectMineTarget(std::vector<Candidate<Id>> const& candidates, Roll&& roll)
    {
        std::vector<Id> pool;
        for (Candidate<Id> const& c : candidates)
            if (!c.tank)
                pool.push_back(c.id);
        if (pool.empty())
            return std::nullopt;
        std::size_t const i = static_cast<std::size_t>(roll(static_cast<std::uint32_t>(pool.size())));
        return pool[i < pool.size() ? i : pool.size() - 1];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Lanes (handoff section 3.8: from the pot through the target to the measured wall polygon)
    // ----------------------------------------------------------------------------------------------------------------

    struct Lane
    {
        Vec2 from;
        Vec2 to;
        float length = 0.f;
        float wallLength = 0.f;     // from the pot to the wall point (kLaneWallInset inside kFoundryWalls)
    };

    // The lane from `pot` through `target` to the wall point on kFoundryWalls (kLaneWallInset inside it), then
    // `extra` yd further on the same bearing (kLaneExtraYd: the playtest 1 length). A target on top of the pot
    // (closer than 0.5 yd) aims through `fallback` instead (Gilnid). nullopt when the ray meets no wall (a pot outside
    // the polygon: never with the measured frame) or the in-room part would be shorter than 1 yd.
    inline std::optional<Lane> ComputeLane(Vec2 pot, Vec2 target, Vec2 fallback, float extra = kLaneExtraYd)
    {
        Vec2 const through = DeadminesKit::Distance(pot, target) < 0.5f ? fallback : target;
        std::optional<Vec2> const wall =
            DeadminesKit::LaneEndAtWall(DeadminesRework::kFoundryWalls, pot, through, kLaneWallInset);
        if (!wall)
            return std::nullopt;
        float const wallLength = DeadminesKit::Distance(pot, *wall);
        if (wallLength < 1.f)
            return std::nullopt;
        float const length = wallLength + std::max(0.f, extra);
        Vec2 const end = DeadminesKit::Advance(pot, DeadminesKit::BearingTo(pot, through), length);
        return Lane{ pot, end, length, wallLength };
    }

    // Distance along `lane` of the point `p` projected on it (negative before the start, past `length` beyond it).
    inline float AlongLane(Lane const& lane, Vec2 p)
    {
        if (lane.length <= 0.f)
            return 0.f;
        float const dx = (lane.to.x - lane.from.x) / lane.length;
        float const dy = (lane.to.y - lane.from.y) / lane.length;
        return (p.x - lane.from.x) * dx + (p.y - lane.from.y) * dy;
    }

    inline Vec2 PointOnLane(Lane const& lane, float s)
    {
        if (lane.length <= 0.f)
            return lane.from;
        float const t = s / lane.length;
        return { lane.from.x + (lane.to.x - lane.from.x) * t, lane.from.y + (lane.to.y - lane.from.y) * t };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The rolling path: the lane's points every `step` yd (both ends included) at the floor height. `probe(x, y, z)`
    // returns the floor at or below about z (nullopt: none); a probe more than `maxStepZ` from the last point's z (a
    // wall's top, another level, nothing) keeps the last z. The first point is at `startZ` (the pot dais).
    // ----------------------------------------------------------------------------------------------------------------

    struct PathPoint
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
    };

    template <typename Probe>
    std::vector<PathPoint> FloorPath(Lane const& lane, float startZ, Probe&& probe, float step = kFloorPathStepYd,
        float maxStepZ = kFloorPathMaxStepZ)
    {
        std::vector<PathPoint> out;
        out.push_back({ lane.from.x, lane.from.y, startZ });
        if (lane.length <= 0.f || step <= 0.f)
            return out;
        float z = startZ;
        float s = 0.f;
        while (s < lane.length - 1e-3f)
        {
            s = std::min(lane.length, s + step);
            Vec2 const p = PointOnLane(lane, s);
            std::optional<float> const floor = probe(p.x, p.y, z);
            if (floor && std::fabs(*floor - z) <= maxStepZ)
                z = *floor;
            out.push_back({ p.x, p.y, z });
        }
        return out;
    }

    // How far along the lane it leaves `block` (the pot block, a hole nobody stands in): 0 when it starts outside.
    inline float BlockExit(Lane const& lane, DeadminesKit::Box2 const& block)
    {
        float constexpr step = 0.25f;
        float s = 0.f;
        while (s < lane.length && block.Contains(PointOnLane(lane, s)))
            s += step;
        return std::min(s, lane.length);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Hot shot segments
    // ----------------------------------------------------------------------------------------------------------------

    struct Segment
    {
        float s0 = 0.f;
        float s1 = 0.f;
    };

    // The lane cut into `segment`-yd pieces from `skip` (the pot block's exit: nobody stands in the hole) to its end;
    // a remainder under a quarter of a segment joins the piece before it, so no sliver gets its own zone.
    inline std::vector<Segment> HotShotSegments(float laneLength, float skip, float segment = kHotShotSegmentYd)
    {
        std::vector<Segment> out;
        if (segment <= 0.f || laneLength <= skip)
            return out;
        float s = std::max(0.f, skip);
        while (s < laneLength - 1e-3f)
        {
            float end = std::min(laneLength, s + segment);
            if (laneLength - end < segment * 0.25f)
                end = laneLength;
            out.push_back({ s, end });
            s = end;
        }
        return out;
    }

    // The ball has reached `nowS` along the lane: returns the index after the last segment it has fully passed
    // (the segments [next, return value) are newly passed). `done` (the ball reached the wall or is gone) releases
    // every remaining segment.
    inline std::size_t SegmentsPassed(std::vector<Segment> const& segments, std::size_t next, float nowS, bool done)
    {
        if (done)
            return segments.size();
        while (next < segments.size() && nowS >= segments[next].s1)
            ++next;
        return next;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Ball sweeps (Bowled Over, the mine sweep): the ball moved from `from` to `to` since the last update, so a fast
    // ball on a slow map update still meets everything on its path.
    // ----------------------------------------------------------------------------------------------------------------

    inline float DistanceToSegment(Vec2 p, Vec2 a, Vec2 b)
    {
        float const vx = b.x - a.x;
        float const vy = b.y - a.y;
        float const len2 = vx * vx + vy * vy;
        float t = 0.f;
        if (len2 > 1e-8f)
            t = std::clamp(((p.x - a.x) * vx + (p.y - a.y) * vy) / len2, 0.f, 1.f);
        return std::hypot(p.x - (a.x + vx * t), p.y - (a.y + vy * t));
    }

    inline bool SweptWithin(Vec2 from, Vec2 to, Vec2 target, float radius)
    {
        return DistanceToSegment(target, from, to) <= radius;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The land mine ledger: the script's own record of live mines in registration order, capped like the registry's
    // Mine(...).Cap(group, n) (the oldest goes first), so the script knows which mine unit fizzles (the registry's
    // cap fizzles its mechanic without a resolve callback).
    // ----------------------------------------------------------------------------------------------------------------

    template <typename Entry>
    class MineLedger
    {
    public:
        explicit MineLedger(std::size_t cap = kMineCap) : _cap(cap) { }

        // Adds `e`; returns the entries the cap pushes out (the oldest first).
        std::vector<Entry> Add(Entry e)
        {
            _live.push_back(std::move(e));
            std::vector<Entry> evicted;
            while (_cap > 0 && _live.size() > _cap)
            {
                evicted.push_back(std::move(_live.front()));
                _live.pop_front();
            }
            return evicted;
        }

        // Removes every entry `pred` accepts; returns them.
        template <typename Pred>
        std::vector<Entry> RemoveIf(Pred&& pred)
        {
            std::vector<Entry> removed;
            for (auto it = _live.begin(); it != _live.end();)
            {
                if (pred(*it))
                {
                    removed.push_back(std::move(*it));
                    it = _live.erase(it);
                }
                else
                    ++it;
            }
            return removed;
        }

        void Clear() { _live.clear(); }
        std::size_t Size() const { return _live.size(); }
        std::deque<Entry> const& Live() const { return _live; }

    private:
        std::size_t _cap;
        std::deque<Entry> _live;
    };

    // The peak number of registry mechanics one batch keeps alive at once (handoff section 6, solver cost): one
    // projectile lane per target, every Hot shot segment of every lane (a lane's segments overlap for a while: the
    // ball crosses a lane in at most 4 s, a segment lives 1 s of warning plus 6 s), plus the live mines.
    inline std::size_t PeakRegistrations(std::vector<float> const& laneLengths, float skip, bool hotShot,
        std::size_t mines)
    {
        std::size_t n = laneLengths.size() + mines;
        if (hotShot)
            for (float length : laneLengths)
                n += HotShotSegments(length, skip).size();
        return n;
    }
}

#endif
