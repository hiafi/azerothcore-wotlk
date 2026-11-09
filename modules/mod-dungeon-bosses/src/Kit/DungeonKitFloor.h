/*
 * mod-dungeon-bosses, the shared dungeon kit (Stratholme WP-KT-1, handoff section 3.11 #12, #16, #21): the pure floor
 * rules (no engine headers; host-tested by tests/dungeon_kit_test.cpp). The engine halves are in DungeonKitFields.h.
 *
 *   FloorPath          points every `step` yd along a straight lane at the floor height (Gilnid's rolling path, lifted
 *                      from GilnidLogic.h unchanged; kit #12): walkers, charges and stalker rows that hug the floor
 *   PickFloorSpotFrom  a random floor point near a point (min / max range) outside avoid circles and away from units,
 *                      with fixed fallbacks and a best-effort pick (kit #21; Polkelt's and Malicia's pickers, general)
 *   PuddleSet          a union of round puddles (arming, life, the merge rule, z band, area); PuddleField's state
 *                      (kit #16)
 *   InsideClock        how long each unit has stood inside a union without a break (PuddleField's dwell)
 *
 * Names: every function here takes Vec2, so argument-dependent lookup offers it to any call with kit types; a dungeon
 * helper taking Vec2 must not reuse these names with other parameters (.agents/docs/cpp-scripts.md).
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLOOR_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLOOR_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // FloorPath (kit #12; GilnidLogic.h FloorPath, the same rule on a from / to lane): the lane's points every `step`
    // yd (both ends included) at the floor height. `probe(x, y, z)` returns the floor at or below about z (nullopt:
    // none); a probe more than `maxStepZ` from the last point's z (a wall's top, another level, nothing) keeps the last
    // z. The first point is at `startZ`.
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kFloorPathStepYd = 2.f;
    float constexpr kFloorPathMaxStepZ = 2.5f;

    struct FloorPathPoint
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
    };

    template <typename Probe>
    std::vector<FloorPathPoint> FloorPath(Vec2 from, Vec2 to, float startZ, Probe&& probe,
        float step = kFloorPathStepYd, float maxStepZ = kFloorPathMaxStepZ)
    {
        std::vector<FloorPathPoint> out;
        out.push_back({ from.x, from.y, startZ });
        float const length = Distance(from, to);
        if (length <= 0.f || step <= 0.f)
            return out;
        float z = startZ;
        float s = 0.f;
        while (s < length - 1e-3f)
        {
            s = std::min(length, s + step);
            float const t = s / length;
            Vec2 const p{ from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t };
            std::optional<float> const floor = probe(p.x, p.y, z);
            if (floor && std::fabs(*floor - z) <= maxStepZ)
                z = *floor;
            out.push_back({ p.x, p.y, z });
        }
        return out;
    }

    // The path's length on the map plane.
    inline float FloorPathLength(std::vector<FloorPathPoint> const& path)
    {
        float length = 0.f;
        for (std::size_t i = 1; i < path.size(); ++i)
            length += Distance(Vec2{ path[i - 1].x, path[i - 1].y }, Vec2{ path[i].x, path[i].y });
        return length;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Floor spots (kit #21)
    // ----------------------------------------------------------------------------------------------------------------

    struct AvoidCircle
    {
        Vec2 center;
        float radius = 0.f;
    };

    struct FloorSpotRules
    {
        Vec2 near;                          // candidates lie minRange..maxRange from here (uniform over the ring)
        float minRange = 0.f;
        float maxRange = 10.f;
        std::vector<AvoidCircle> avoid;     // a spot never inside one (plus avoidMargin): piles, puddles, wards
        float avoidMargin = 0.f;
        std::vector<Vec2> awayFrom;         // a spot at least minFromAway from each (players, other spots)
        float minFromAway = 0.f;
        std::uint32_t tries = 32;           // random candidates per pick
        bool bestEffort = true;             // nothing keeps every rule: the best scored floor candidate (else none)
    };

    struct FloorSpot
    {
        Vec2 p;
        float z = 0.f;
        bool full = false;                  // keeps every rule
    };

    // How well a candidate keeps the rules, worst first: fewer avoid circles entered, then the away rule, then the
    // most room (the distance to the nearest avoid edge or away point, capped at 50 yd).
    struct FloorSpotScore
    {
        std::uint32_t avoidHits = 0;
        bool away = true;
        float room = 50.f;

        bool Full() const { return avoidHits == 0 && away; }
        float Value() const
        {
            return -1000.f * float(avoidHits) + (away ? 100.f : 0.f) + std::min(room, 50.f);
        }
    };

    inline FloorSpotScore ScoreFloorSpot(FloorSpotRules const& rules, Vec2 p)
    {
        FloorSpotScore s;
        for (AvoidCircle const& c : rules.avoid)
        {
            float const edge = Distance(c.center, p) - c.radius - rules.avoidMargin;
            if (edge < 0.f)
                ++s.avoidHits;
            s.room = std::min(s.room, std::max(0.f, edge));
        }
        for (Vec2 const& q : rules.awayFrom)
        {
            float const d = Distance(q, p);
            if (d < rules.minFromAway)
                s.away = false;
            s.room = std::min(s.room, std::max(0.f, d - rules.minFromAway));
        }
        return s;
    }

    // A point minRange..maxRange from `near`, uniform over the ring's area; `u`, `v` in [0, 1).
    inline Vec2 RingPoint(Vec2 near, float minRange, float maxRange, float u, float v)
    {
        float const lo = std::max(0.f, std::min(minRange, maxRange));
        float const hi = std::max(lo, maxRange);
        float const r = std::sqrt(lo * lo + std::clamp(u, 0.f, 1.f) * (hi * hi - lo * lo));
        return Advance(near, std::clamp(v, 0.f, 1.f) * kTwoPi, r);
    }

    // One floor spot. Each of `rules.tries` candidates is RingPoint(near, ...) with two rand01() draws in [0, 1);
    // `floor(p)` returns the floor height there (nullopt: not floor, off the arena, off the navmesh). The first
    // candidate that keeps every rule wins; else the first of `fixed` that is floor and keeps every rule; else, with
    // bestEffort, the best scored floor candidate (fixed ones included); else nullopt.
    template <class Rand01, class Floor>
    std::optional<FloorSpot> PickFloorSpotFrom(FloorSpotRules const& rules, Rand01&& rand01, Floor&& floor,
        std::vector<Vec2> const& fixed = {})
    {
        std::optional<FloorSpot> best;
        float bestValue = 0.f;
        auto consider = [&](Vec2 p) -> bool
        {
            std::optional<float> const z = floor(p);
            if (!z)
                return false;
            FloorSpotScore const s = ScoreFloorSpot(rules, p);
            if (s.Full())
            {
                best = FloorSpot{ p, *z, true };
                return true;
            }
            if (!best || s.Value() > bestValue)
            {
                best = FloorSpot{ p, *z, false };
                bestValue = s.Value();
            }
            return false;
        };
        for (std::uint32_t t = 0; t < rules.tries; ++t)
        {
            float const u = rand01();
            float const v = rand01();
            if (consider(RingPoint(rules.near, rules.minRange, rules.maxRange, u, v)))
                return best;
        }
        for (Vec2 const& p : fixed)
            if (consider(p))
                return best;
        if (best && !best->full && !rules.bestEffort)
            return std::nullopt;
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Puddles (kit #16): a union of round puddles. Each arms `armAfterMs` after it lands and lives `lifeMs` (0: until
    // removed). With `merge`, a puddle whose center lands inside a live one (within the z band) makes no new puddle and
    // returns the old one's id (Nerub'enkan's webs, ruling 47). Times are the caller's clock in ms.
    // ----------------------------------------------------------------------------------------------------------------

    struct Puddle
    {
        std::uint32_t id = 0;
        Vec2 center;
        float z = 0.f;
        float radius = 0.f;
        std::uint64_t armAt = 0;
        std::uint64_t expireAt = 0;         // 0: never

        bool Armed(std::uint64_t now) const { return now >= armAt; }
        bool Expired(std::uint64_t now) const { return expireAt && now >= expireAt; }
    };

    class PuddleSet
    {
    public:
        static float constexpr kDefaultZBand = 4.f;

        struct AddResult
        {
            std::uint32_t id = 0;
            bool merged = false;
        };

        explicit PuddleSet(float zBand = kDefaultZBand) : _zBand(zBand) { }

        AddResult Add(std::uint64_t now, Vec2 center, float z, float radius, std::uint32_t armAfterMs,
            std::uint32_t lifeMs, bool merge)
        {
            if (merge)
                for (Puddle const& p : _puddles)
                    if (!p.Expired(now) && InBand(p, z) && Distance(p.center, center) <= p.radius)
                        return { p.id, true };
            Puddle p;
            p.id = _nextId++;
            p.center = center;
            p.z = z;
            p.radius = std::max(0.f, radius);
            p.armAt = now + armAfterMs;
            p.expireAt = lifeMs ? now + lifeMs : 0;
            _puddles.push_back(p);
            return { p.id, false };
        }

        // The puddle holding (p, z) now (armed only unless `arming`), the first added wins; nullopt: none.
        std::optional<std::uint32_t> PuddleAt(std::uint64_t now, Vec2 p, float z, bool arming = false) const
        {
            for (Puddle const& q : _puddles)
                if (!q.Expired(now) && (arming || q.Armed(now)) && InBand(q, z) && Distance(q.center, p) <= q.radius)
                    return q.id;
            return std::nullopt;
        }

        bool Contains(std::uint64_t now, Vec2 p, float z, bool arming = false) const
        {
            return PuddleAt(now, p, z, arming).has_value();
        }

        // Removes the expired puddles; returns their ids.
        std::vector<std::uint32_t> Prune(std::uint64_t now)
        {
            std::vector<std::uint32_t> gone;
            std::erase_if(_puddles, [now, &gone](Puddle const& p)
            {
                if (!p.Expired(now))
                    return false;
                gone.push_back(p.id);
                return true;
            });
            return gone;
        }

        bool Remove(std::uint32_t id)
        {
            return std::erase_if(_puddles, [id](Puddle const& p) { return p.id == id; }) > 0;
        }

        void Clear() { _puddles.clear(); }

        Puddle const* Find(std::uint32_t id) const
        {
            for (Puddle const& p : _puddles)
                if (p.id == id)
                    return &p;
            return nullptr;
        }

        std::vector<Puddle> const& All() const { return _puddles; }
        std::size_t Size() const { return _puddles.size(); }
        float ZBand() const { return _zBand; }

        // The floor the union covers (live puddles, armed or arming), in square yd, by sampling a `cell`-yd grid over
        // the puddles' bounding box: overlapping puddles count once (the space math of Galford's hall and
        // Nerub'enkan's webs). Accurate to a few percent at cell 0.25.
        float CoveredArea(std::uint64_t now, float cell = 0.25f) const
        {
            if (_puddles.empty() || cell <= 0.f)
                return 0.f;
            float minX = 1e9f;
            float maxX = -1e9f;
            float minY = 1e9f;
            float maxY = -1e9f;
            bool any = false;
            for (Puddle const& p : _puddles)
            {
                if (p.Expired(now))
                    continue;
                any = true;
                minX = std::min(minX, p.center.x - p.radius);
                maxX = std::max(maxX, p.center.x + p.radius);
                minY = std::min(minY, p.center.y - p.radius);
                maxY = std::max(maxY, p.center.y + p.radius);
            }
            if (!any)
                return 0.f;
            std::uint64_t cells = 0;
            for (float x = minX + cell * 0.5f; x < maxX; x += cell)
                for (float y = minY + cell * 0.5f; y < maxY; y += cell)
                    for (Puddle const& p : _puddles)
                        if (!p.Expired(now) && Distance(p.center, Vec2{ x, y }) <= p.radius)
                        {
                            ++cells;
                            break;
                        }
            return float(cells) * cell * cell;
        }

    private:
        bool InBand(Puddle const& p, float z) const { return std::fabs(p.z - z) <= _zBand; }

        float _zBand;
        std::vector<Puddle> _puddles;
        std::uint32_t _nextId = 1;
    };

    // How long each unit (raw guid) has stood inside without a break. Feed the units inside now with the time since
    // the last update; a unit not fed is outside (its time resets).
    class InsideClock
    {
    public:
        // Returns each inside unit with its time inside, this update included.
        std::vector<std::pair<std::uint64_t, std::uint32_t>> Update(std::vector<std::uint64_t> const& inside,
            std::uint32_t diffMs)
        {
            std::vector<std::pair<std::uint64_t, std::uint32_t>> next;
            next.reserve(inside.size());
            for (std::uint64_t const id : inside)
            {
                std::uint32_t ms = diffMs;
                for (auto const& [prev, prevMs] : _inside)
                    if (prev == id)
                        ms = prevMs + diffMs;
                next.emplace_back(id, ms);
            }
            _inside = next;
            return next;
        }

        std::uint32_t Of(std::uint64_t id) const
        {
            for (auto const& [prev, ms] : _inside)
                if (prev == id)
                    return ms;
            return 0;
        }

        void Clear() { _inside.clear(); }

    private:
        std::vector<std::pair<std::uint64_t, std::uint32_t>> _inside;
    };
}

#endif
