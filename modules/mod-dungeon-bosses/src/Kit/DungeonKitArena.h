/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): the pure part of the arena guard (no engine headers; host-tested
 * by tests/dungeon_kit_test.cpp and, through Greenskin's aliases, tests/greenskin_test.cpp).
 *
 * The Deadmines playtest 1 lesson (PT1 item 2): a boss is not kitable off its arena. An Arena is where a fight
 * happens: one or more regions (a polygon floor, a circle, or a box in a FrameRect's coordinates), each with its own
 * z band, so a multi-level room is a union of floors. ArenaGuard (ArenaGuard.h) is the engine half: grip at the pull,
 * grip back after a grace, hold the chase, evade off the arena, and confine units to (or out of) a cell.
 *
 *   GripTracker        per unit: how long it has been off the arena, and its post-grip cooldown
 *   LandingToward      where a gripped unit lands: `landYd` from the boss toward where it was, clamped into a box
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_H

#include "DungeonKitMath.h"
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <utility>
#include <vector>

namespace DungeonKit
{
    // One floor of an arena. Build it with the static helpers.
    struct ArenaRegion
    {
        enum class Kind : std::uint8_t
        {
            Polygon,    // `polygon` (map coordinates)
            Circle,     // `center`, `radius`
            FrameBox    // `frame` coordinates in [minX, maxX] x [minY, maxY] (may reach past the frame's own size)
        };

        Kind kind = Kind::Polygon;
        std::vector<Vec2> polygon;
        Vec2 center;
        float radius = 0.f;
        FrameRect frame;
        Box2 frameBox;              // in frame coordinates
        float zMin = -100000.f;
        float zMax = 100000.f;

        static ArenaRegion Polygon(std::vector<Vec2> points, float zMin, float zMax)
        {
            ArenaRegion r;
            r.kind = Kind::Polygon;
            r.polygon = std::move(points);
            r.zMin = zMin;
            r.zMax = zMax;
            return r;
        }

        static ArenaRegion Circle(Vec2 center, float radius, float zMin, float zMax)
        {
            ArenaRegion r;
            r.kind = Kind::Circle;
            r.center = center;
            r.radius = radius;
            r.zMin = zMin;
            r.zMax = zMax;
            return r;
        }

        static ArenaRegion Frame(FrameRect const& frame, Box2 const& inFrame, float zMin, float zMax)
        {
            ArenaRegion r;
            r.kind = Kind::FrameBox;
            r.frame = frame;
            r.frameBox = inFrame;
            r.zMin = zMin;
            r.zMax = zMax;
            return r;
        }

        bool InZBand(float z) const { return z >= zMin && z <= zMax; }

        // The plane test only (no z).
        bool ContainsPlane(Vec2 p) const
        {
            switch (kind)
            {
                case Kind::Polygon:
                    return PointInPolygon(std::span<Vec2 const>(polygon), p);
                case Kind::Circle:
                    return Distance(center, p) <= radius;
                case Kind::FrameBox:
                {
                    Vec2 const q = ToFrame(frame, p);
                    return q.x >= frameBox.minX && q.x <= frameBox.maxX && q.y >= frameBox.minY
                        && q.y <= frameBox.maxY;
                }
            }
            return false;
        }

        bool Contains(Vec2 p, float z) const
        {
            return InZBand(z) && ContainsPlane(p);
        }

        // Distance along the ray from `origin` (inside this region) to its edge; nullopt when it meets none.
        std::optional<float> RayToEdge(Vec2 origin, float orientation) const
        {
            switch (kind)
            {
                case Kind::Polygon:
                    return RayToPolygonEdge(std::span<Vec2 const>(polygon), origin, orientation);
                case Kind::Circle:
                    return RayToCircleEdge(center, radius, origin, orientation);
                case Kind::FrameBox:
                {
                    std::array<Vec2, 4> const corners{ {
                        FramePoint(frame, frameBox.minX, frameBox.minY),
                        FramePoint(frame, frameBox.maxX, frameBox.minY),
                        FramePoint(frame, frameBox.maxX, frameBox.maxY),
                        FramePoint(frame, frameBox.minX, frameBox.maxY),
                    } };
                    return RayToPolygonEdge(corners, origin, orientation);
                }
            }
            return std::nullopt;
        }
    };

    // Where a fight happens: the union of its regions. An empty arena contains nothing.
    struct Arena
    {
        std::vector<ArenaRegion> regions;

        Arena() = default;
        explicit Arena(ArenaRegion region) { regions.push_back(std::move(region)); }
        explicit Arena(std::vector<ArenaRegion> all) : regions(std::move(all)) { }

        Arena& Add(ArenaRegion region)
        {
            regions.push_back(std::move(region));
            return *this;
        }

        bool Empty() const { return regions.empty(); }

        bool Contains(Vec2 p, float z) const
        {
            for (ArenaRegion const& r : regions)
                if (r.Contains(p, z))
                    return true;
            return false;
        }

        // The first region holding (p, z), else nullptr.
        ArenaRegion const* RegionAt(Vec2 p, float z) const
        {
            for (ArenaRegion const& r : regions)
                if (r.Contains(p, z))
                    return &r;
            return nullptr;
        }

        // The lowest zMin / highest zMax over every region (a search band for the floor height).
        float ZMin() const
        {
            float z = regions.empty() ? 0.f : regions.front().zMin;
            for (ArenaRegion const& r : regions)
                z = std::min(z, r.zMin);
            return z;
        }

        float ZMax() const
        {
            float z = regions.empty() ? 0.f : regions.front().zMax;
            for (ArenaRegion const& r : regions)
                z = std::max(z, r.zMax);
            return z;
        }

        // Distance from `origin` along `orientation` to the edge of the region holding (origin, z); nullopt when no
        // region holds it or the ray meets no edge.
        std::optional<float> RayToEdge(Vec2 origin, float z, float orientation) const
        {
            ArenaRegion const* r = RegionAt(origin, z);
            if (!r)
                return std::nullopt;
            return r->RayToEdge(origin, orientation);
        }
    };

    // Per unit: how long it has been off the arena (continuously), and its post-grip cooldown. Keys are raw guids.
    class GripTracker
    {
    public:
        // Greenskin's numbers (Deadmines PT1): 1.5 s grace, 3 s cooldown.
        static std::uint32_t constexpr kDefaultGraceMs = 1500;
        static std::uint32_t constexpr kDefaultCooldownMs = 3000;

        explicit GripTracker(std::uint32_t graceMs = kDefaultGraceMs, std::uint32_t cooldownMs = kDefaultCooldownMs)
            : _graceMs(graceMs), _cooldownMs(cooldownMs) { }

        // `unit` was seen on (or off) the arena `diff` ms after its last update. True: grip it now (then Gripped).
        bool Update(std::uint64_t unit, bool onArena, std::uint32_t diff)
        {
            Entry& e = _units[unit];
            e.cooldownMs = e.cooldownMs > diff ? e.cooldownMs - diff : 0;
            if (onArena)
            {
                e.offMs = 0;
                return false;
            }
            e.offMs += diff;
            return !e.cooldownMs && e.offMs >= _graceMs;
        }

        // The pull: grip anyone off the arena at once (no grace), unless just gripped.
        bool PullNow(std::uint64_t unit, bool onArena) const
        {
            auto const it = _units.find(unit);
            return !onArena && (it == _units.end() || !it->second.cooldownMs);
        }

        void Gripped(std::uint64_t unit)
        {
            Entry& e = _units[unit];
            e.offMs = 0;
            e.cooldownMs = _cooldownMs;
        }

        void Forget(std::uint64_t unit) { _units.erase(unit); }
        void Clear() { _units.clear(); }
        std::size_t Size() const { return _units.size(); }
        std::uint32_t GraceMs() const { return _graceMs; }
        std::uint32_t CooldownMs() const { return _cooldownMs; }

    private:
        struct Entry
        {
            std::uint32_t offMs = 0;
            std::uint32_t cooldownMs = 0;
        };

        std::uint32_t _graceMs;
        std::uint32_t _cooldownMs;
        std::unordered_map<std::uint64_t, Entry> _units;
    };

    // Where a gripped unit lands: `landYd` from the boss toward where it was (the boss itself when they stand on each
    // other), clamped into `box` when given, so it always lands on a known-good floor.
    inline Vec2 LandingToward(Vec2 boss, Vec2 from, float landYd, std::optional<Box2> const& box = std::nullopt)
    {
        float const dx = from.x - boss.x;
        float const dy = from.y - boss.y;
        float const d = std::hypot(dx, dy);
        Vec2 p = d > 0.01f ? Vec2{ boss.x + dx / d * landYd, boss.y + dy / d * landYd } : boss;
        if (box)
            p = box->Clamp(p);
        return p;
    }
}

#endif
