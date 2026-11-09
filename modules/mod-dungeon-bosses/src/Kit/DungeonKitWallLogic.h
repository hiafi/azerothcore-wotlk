/*
 * mod-dungeon-bosses, the shared dungeon kit (Stratholme WP-KT-2, handoff section 3.11 #15 and #26): pure rules for
 * the lethal walls and the relic dispensers (no engine headers; host-tested by tests/kit_walls_test.cpp). The engine
 * halves are DungeonKitWalls.h (LethalWall, LethalWalls, RelicDispenserAI) and DungeonKitSpells.cpp
 * (spell_dungeon_lethal_strike).
 *
 *   WallLine           a wall: the centre line from `from` to `to` and its width (the registry Line's hitbox)
 *   WallClearance      how far a point stands from the wall's strip (negative inside it)
 *   KeepClear          a place a wall must keep clear of: a point with a radius (a shelter, a fire spot) or a path
 *                      with a half width (a March lane, a bot route)
 *   CheckPlacement     the closest keep-clear shape to a wall and its gap; KeepsClear: the handoff's placement rule
 *                      ("at least 5 yd outside every shelter, fire spot and march path", section 3.8)
 *   CrossesWall        a step from one poll to the next went across the wall's line (a blink, a charge, a sprint
 *                      faster than the strip is wide): the registry's tick sees only where a unit stands
 *   WallWatch          the last position of every unit near one wall; Observe reports a crossing
 *   StrikeBook         at most one strike per unit per kRestrikeMs (a shielded survivor is struck again, not spammed)
 *   PlanDispense       who gets a relic copy: the user's party members on the same map who lack it
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WALL_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WALL_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <unordered_map>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Walls (kit #15)
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kWallDefaultWidthYd = 2.f;      // a rank of footmen, a line of fire
    float constexpr kWallPlacementYd = 5.f;         // handoff section 3.8: 5 yd outside every shelter, fire, path
    float constexpr kWallMaxStepYd = 30.f;          // a longer step between two polls is a teleport, not a crossing
    std::uint32_t constexpr kWallTickMs = 250;      // the registry tick (X4's API)
    std::uint32_t constexpr kWallArmMs = 2000;      // section 10: the walls arm 2 s after the pull grip
    std::uint32_t constexpr kRestrikeMs = 500;      // a survivor (an absorb) is struck again after this long

    struct WallLine
    {
        Vec2 from;
        Vec2 to;
        float width = kWallDefaultWidthYd;

        float Length() const { return Distance(from, to); }
        float HalfWidth() const { return width * 0.5f; }
    };

    // Distance from `p` to the edge of the wall's strip (the capsule round the centre line): negative inside.
    inline float WallClearance(WallLine const& w, Vec2 p)
    {
        return SegmentDistance(w.from, w.to, p) - w.HalfWidth();
    }

    inline bool InsideWall(WallLine const& w, Vec2 p)
    {
        return WallClearance(w, p) <= 0.f;
    }

    // Signed distance of `p` from the infinite line through the wall (positive on the left of from -> to).
    inline float WallSide(WallLine const& w, Vec2 p)
    {
        float const len = w.Length();
        if (len < 1e-4f)
            return 0.f;
        return ((w.to.x - w.from.x) * (p.y - w.from.y) - (w.to.y - w.from.y) * (p.x - w.from.x)) / len;
    }

    // Shortest distance between the segments a-b and c-d (0 when they cross).
    inline float SegmentToSegment(Vec2 a, Vec2 b, Vec2 c, Vec2 d)
    {
        auto cross = [](Vec2 o, Vec2 p, Vec2 q) { return (p.x - o.x) * (q.y - o.y) - (p.y - o.y) * (q.x - o.x); };
        float const d1 = cross(c, d, a);
        float const d2 = cross(c, d, b);
        float const d3 = cross(a, b, c);
        float const d4 = cross(a, b, d);
        if (((d1 > 0.f && d2 < 0.f) || (d1 < 0.f && d2 > 0.f)) && ((d3 > 0.f && d4 < 0.f) || (d3 < 0.f && d4 > 0.f)))
            return 0.f;
        return std::min({ SegmentDistance(c, d, a), SegmentDistance(c, d, b), SegmentDistance(a, b, c),
            SegmentDistance(a, b, d) });
    }

    // A place the wall must keep clear of: a point (a == b) with `radius`, or the path a-b with half width `radius`.
    struct KeepClear
    {
        Vec2 a;
        Vec2 b;
        float radius = 0.f;

        static KeepClear Point(Vec2 p, float r) { return { p, p, r }; }
        static KeepClear Path(Vec2 from, Vec2 to, float halfWidth) { return { from, to, halfWidth }; }
    };

    // The gap between the wall's strip and the keep-clear shape's edge (negative: they overlap).
    inline float Clearance(WallLine const& w, KeepClear const& k)
    {
        return SegmentToSegment(w.from, w.to, k.a, k.b) - w.HalfWidth() - k.radius;
    }

    struct PlacementReport
    {
        float minYd = std::numeric_limits<float>::infinity();   // the smallest gap (infinity: nothing to keep clear)
        std::size_t worst = 0;                                  // the index of the shape with that gap
    };

    inline PlacementReport CheckPlacement(WallLine const& w, std::span<KeepClear const> keep)
    {
        PlacementReport r;
        for (std::size_t i = 0; i < keep.size(); ++i)
        {
            float const gap = Clearance(w, keep[i]);
            if (gap < r.minYd)
            {
                r.minYd = gap;
                r.worst = i;
            }
        }
        return r;
    }

    // The handoff's placement rule: every keep-clear shape at least `minYd` outside the wall's strip.
    inline bool KeepsClear(WallLine const& w, std::span<KeepClear const> keep, float minYd = kWallPlacementYd)
    {
        return CheckPlacement(w, keep).minYd >= minYd;
    }

    // A step from `prev` to `cur` that went across the wall's line within its length (its strip's ends included).
    // A step longer than `maxStepYd` is a teleport (a summon, a port), never a crossing. A step that ends or starts
    // inside the strip is the registry's (the unit stood inside at a tick); this catches the ones that never did.
    inline bool CrossesWall(WallLine const& w, Vec2 prev, Vec2 cur, float maxStepYd = kWallMaxStepYd)
    {
        if (Distance(prev, cur) > maxStepYd)
            return false;
        float const s1 = WallSide(w, prev);
        float const s2 = WallSide(w, cur);
        if (!((s1 > 0.f && s2 < 0.f) || (s1 < 0.f && s2 > 0.f)))
            return false;
        float const t = s1 / (s1 - s2);
        Vec2 const hit{ prev.x + t * (cur.x - prev.x), prev.y + t * (cur.y - prev.y) };
        float along = 0.f;
        float const off = SegmentDistance(w.from, w.to, hit, &along);
        return off <= w.HalfWidth() + 1e-3f;
    }

    // The last seen position of every unit one wall watches. Call Observe for each unit that counts this poll (alive,
    // in the wall's z band), then Sweep: a unit not observed in a poll (dead, gone, off the floor) is forgotten, so a
    // resurrection or a teleport never reads as a crossing.
    class WallWatch
    {
    public:
        explicit WallWatch(WallLine line, float maxStepYd = kWallMaxStepYd) : _line(line), _maxStep(maxStepYd) { }

        // True when `id` crossed the wall since the last poll it was seen in.
        bool Observe(std::uint64_t id, Vec2 p)
        {
            auto it = _seen.find(id);
            bool crossed = false;
            if (it == _seen.end())
                _seen.emplace(id, Seen{ p, _generation });
            else
            {
                crossed = CrossesWall(_line, it->second.at, p, _maxStep);
                it->second = Seen{ p, _generation };
            }
            return crossed;
        }

        void Sweep()
        {
            for (auto it = _seen.begin(); it != _seen.end();)
            {
                if (it->second.generation != _generation)
                    it = _seen.erase(it);
                else
                    ++it;
            }
            ++_generation;
        }

        std::size_t Size() const { return _seen.size(); }
        WallLine const& Line() const { return _line; }

    private:
        struct Seen
        {
            Vec2 at;
            std::uint64_t generation = 0;
        };

        WallLine _line;
        float _maxStep;
        std::unordered_map<std::uint64_t, Seen> _seen;
        std::uint64_t _generation = 0;
    };

    // At most one strike per unit per `restrikeMs`.
    class StrikeBook
    {
    public:
        explicit StrikeBook(std::uint32_t restrikeMs = kRestrikeMs) : _restrike(restrikeMs) { }

        // True (and booked) when `id` may be struck at `nowMs`.
        bool Due(std::uint64_t id, std::uint64_t nowMs)
        {
            auto it = _last.find(id);
            if (it != _last.end() && nowMs < it->second + _restrike)
                return false;
            _last[id] = nowMs;
            return true;
        }

        // Drops entries older than the restrike window (call now and then; a fight has a handful).
        void Prune(std::uint64_t nowMs)
        {
            for (auto it = _last.begin(); it != _last.end();)
            {
                if (nowMs >= it->second + _restrike)
                    it = _last.erase(it);
                else
                    ++it;
            }
        }

        std::size_t Size() const { return _last.size(); }

    private:
        std::uint32_t _restrike;
        std::unordered_map<std::uint64_t, std::uint64_t> _last;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Relic dispenser (kit #26)
    // ----------------------------------------------------------------------------------------------------------------

    // One candidate for a copy: the user and each member of the user's group.
    struct RelicCandidate
    {
        std::uint64_t id = 0;
        bool sameMap = false;       // in the world, on the dispenser's map (this instance)
        bool hasItem = false;       // carries a copy (bags or bank)
    };

    struct DispensePlan
    {
        std::vector<std::uint64_t> give;    // in candidate order, each once
        std::uint32_t had = 0;              // on the map, already carrying one
        std::uint32_t away = 0;             // not on the map
    };

    inline DispensePlan PlanDispense(std::span<RelicCandidate const> candidates)
    {
        DispensePlan plan;
        for (RelicCandidate const& c : candidates)
        {
            if (std::find(plan.give.begin(), plan.give.end(), c.id) != plan.give.end())
                continue;   // listed twice (the user is also a group member)
            if (!c.sameMap)
                ++plan.away;
            else if (c.hasItem)
                ++plan.had;
            else
                plan.give.push_back(c.id);
        }
        return plan;
    }
}

#endif
