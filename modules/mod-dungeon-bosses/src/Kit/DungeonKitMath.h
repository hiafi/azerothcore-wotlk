/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): the pure tuning and geometry part (no engine headers;
 * host-tested by tests/dungeon_kit_test.cpp and, through the Deadmines aliases, tests/kit_test.cpp).
 *
 * - NH<T>: one tuning number per difficulty (normal, heroic). A dungeon's <Boss>Logic.h keeps its constants as
 *   `inline constexpr DungeonKit::NH<...> kName{ normal, heroic };`, so a retune is one line.
 * - RefFlatValue: percent of a reference-health row, rounded and clamped exactly like mod-boss-mechanics'
 *   FlatDamageFor / RefFlatFor (MechanicMath.h), so a script's own spell and a registry mechanic with the same percent
 *   deal the same number.
 * - 2D geometry on the map plane (x north, y west; orientation o points along (cos o, sin o)): point in polygon, the
 *   first wall a ray meets, a lane end clipped to the room, distance to a segment, frontal cones. Every function
 *   here takes Vec2 (argument-dependent lookup finds it from any namespace): a dungeon helper taking Vec2 must not
 *   reuse one of these names with other parameters.
 * - Rectangle frames (FrameRect: a corner origin, X along `angle`, Y along angle + 90 degrees; mod-boss-mechanics'
 *   RoomFrame math) and the lanes laid on them.
 *
 * Polygons are std::array<Vec2, N> (measured constants) or any contiguous run of Vec2 (std::vector, std::span): the
 * array templates forward to the span versions, so both give the same answer.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MATH_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MATH_H

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Per-difficulty tuning numbers
    // ----------------------------------------------------------------------------------------------------------------

    // inline constexpr NH<float> kCaveInPct{ 20.f, 20.f };  ...  kCaveInPct(IsHeroicMap(me))
    template <typename T>
    struct NH
    {
        T normal;
        T heroic;

        constexpr T Get(bool isHeroic) const { return isHeroic ? heroic : normal; }
        constexpr T operator()(bool isHeroic) const { return Get(isHeroic); }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Reference health
    // ----------------------------------------------------------------------------------------------------------------

    // `pct` percent of the tank row (isTank) or the non-tank row; a negative percent is 0. Same rounding as
    // BossMechanics::FlatDamageFor (std::lround of pct / 100 * health, clamped at 0).
    inline std::uint32_t RefFlatValue(std::uint32_t nonTank, std::uint32_t tank, float pct, bool isTank)
    {
        double const health = isTank ? tank : nonTank;
        double const v = std::max(0.f, pct) / 100.0 * health;
        return static_cast<std::uint32_t>(std::max<long>(0, std::lround(v)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Map-plane geometry
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kPi = 3.14159265358979323846f;
    float constexpr kTwoPi = 6.28318530717958647692f;

    struct Vec2
    {
        float x = 0.f;
        float y = 0.f;
    };

    inline float Distance(Vec2 a, Vec2 b)
    {
        return std::hypot(a.x - b.x, a.y - b.y);
    }

    // The orientation (radians, [0, 2pi)) that looks from `from` to `to`.
    inline float BearingTo(Vec2 from, Vec2 to)
    {
        float o = std::atan2(to.y - from.y, to.x - from.x);
        if (o < 0.f)
            o += kTwoPi;
        return o;
    }

    // The tank hit of a TankExempt frontal: is `target` inside the frontal cone of `angleDeg` and `length` (plus
    // `reach`, the units' combat reach) in front of `source` facing `facing`?
    inline bool InFrontalCone(Vec2 source, float facing, Vec2 target, float angleDeg, float length, float reach = 0.f)
    {
        float const dist = Distance(source, target);
        if (dist > length + reach)
            return false;
        if (dist < 0.01f)
            return true;
        float diff = BearingTo(source, target) - facing;
        while (diff > kPi)
            diff -= 2.f * kPi;
        while (diff < -kPi)
            diff += 2.f * kPi;
        return std::fabs(diff) <= angleDeg * kPi / 360.f;
    }

    inline Vec2 Advance(Vec2 from, float orientation, float distance)
    {
        return { from.x + std::cos(orientation) * distance, from.y + std::sin(orientation) * distance };
    }

    // Even-odd rule; a point exactly on an edge may land either way.
    inline bool PointInPolygon(std::span<Vec2 const> poly, Vec2 p)
    {
        std::size_t const n = poly.size();
        if (n < 3)
            return false;
        bool inside = false;
        for (std::size_t i = 0, j = n - 1; i < n; j = i++)
        {
            Vec2 const a = poly[i];
            Vec2 const b = poly[j];
            if ((a.y > p.y) != (b.y > p.y))
            {
                float const xCross = (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x;
                if (p.x < xCross)
                    inside = !inside;
            }
        }
        return inside;
    }

    template <std::size_t N>
    bool PointInPolygon(std::array<Vec2, N> const& poly, Vec2 p)
    {
        return PointInPolygon(std::span<Vec2 const>(poly), p);
    }

    // Axis-aligned box (a hole in a floor polygon, a landing area, a cell).
    struct Box2
    {
        float minX = 0.f;
        float maxX = 0.f;
        float minY = 0.f;
        float maxY = 0.f;

        bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
        Vec2 Center() const { return { (minX + maxX) * 0.5f, (minY + maxY) * 0.5f }; }
        Vec2 Clamp(Vec2 p) const { return { std::clamp(p.x, minX, maxX), std::clamp(p.y, minY, maxY) }; }
    };

    // Distance along the ray from `origin` (looking along `orientation`) to the nearest polygon edge it crosses
    // (strictly ahead of the origin); nullopt when it meets none (an origin outside a polygon looking away from it).
    inline std::optional<float> RayToPolygonEdge(std::span<Vec2 const> poly, Vec2 origin, float orientation)
    {
        std::size_t const n = poly.size();
        if (n < 2)
            return std::nullopt;
        float const dx = std::cos(orientation);
        float const dy = std::sin(orientation);
        std::optional<float> best;
        for (std::size_t i = 0, j = n - 1; i < n; j = i++)
        {
            Vec2 const a = poly[j];
            Vec2 const b = poly[i];
            float const ex = b.x - a.x;
            float const ey = b.y - a.y;
            float const denom = dx * ey - dy * ex;
            if (std::fabs(denom) < 1e-6f)
                continue;   // parallel
            float const ox = a.x - origin.x;
            float const oy = a.y - origin.y;
            float const t = (ox * ey - oy * ex) / denom;    // along the ray
            float const s = (ox * dy - oy * dx) / denom;    // along the edge, 0..1
            if (t > 1e-4f && s >= 0.f && s <= 1.f && (!best || t < *best))
                best = t;
        }
        return best;
    }

    template <std::size_t N>
    std::optional<float> RayToPolygonEdge(std::array<Vec2, N> const& poly, Vec2 origin, float orientation)
    {
        return RayToPolygonEdge(std::span<Vec2 const>(poly), origin, orientation);
    }

    // Distance along the ray from `origin` to the circle's rim, for an origin inside it (or on it); nullopt outside.
    inline std::optional<float> RayToCircleEdge(Vec2 center, float radius, Vec2 origin, float orientation)
    {
        float const dx = std::cos(orientation);
        float const dy = std::sin(orientation);
        float const ox = origin.x - center.x;
        float const oy = origin.y - center.y;
        float const c = ox * ox + oy * oy - radius * radius;
        if (c > 1e-4f)
            return std::nullopt;
        float const b = ox * dx + oy * dy;
        float const disc = b * b - c;
        if (disc < 0.f)
            return std::nullopt;
        return std::max(0.f, -b + std::sqrt(disc));
    }

    // A lane from `origin` through `through` to the room wall: the end point on the polygon edge, pulled back by
    // `inset` yards so the end stays inside the floor. nullopt when the ray meets no wall.
    inline std::optional<Vec2> LaneEndAtWall(std::span<Vec2 const> poly, Vec2 origin, Vec2 through, float inset = 0.5f)
    {
        float const o = BearingTo(origin, through);
        std::optional<float> const hit = RayToPolygonEdge(poly, origin, o);
        if (!hit)
            return std::nullopt;
        return Advance(origin, o, std::max(0.f, *hit - inset));
    }

    template <std::size_t N>
    std::optional<Vec2> LaneEndAtWall(std::array<Vec2, N> const& poly, Vec2 origin, Vec2 through, float inset = 0.5f)
    {
        return LaneEndAtWall(std::span<Vec2 const>(poly), origin, through, inset);
    }

    // Distance from p to the segment a-b; `along` (optional) gets the distance from a to p's projection, clamped.
    // (Named apart from the dungeons' own DistanceToSegment helpers, whose argument orders differ: Vec2 lives here, so
    // argument-dependent lookup would offer this one to their calls too.)
    inline float SegmentDistance(Vec2 a, Vec2 b, Vec2 p, float* along = nullptr)
    {
        float const dx = b.x - a.x;
        float const dy = b.y - a.y;
        float const len2 = dx * dx + dy * dy;
        float t = 0.f;
        if (len2 > 1e-6f)
            t = std::clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / len2, 0.f, 1.f);
        if (along)
            *along = t * std::sqrt(len2);
        return Distance(p, { a.x + t * dx, a.y + t * dy });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rectangle frames (mod-boss-mechanics RoomFrame math: origin a corner, X along `angle` for sizeX, Y along
    // angle + 90 degrees for sizeY)
    // ----------------------------------------------------------------------------------------------------------------

    struct FrameRect
    {
        Vec2 origin;
        float angle = 0.f;
        float sizeX = 0.f;
        float sizeY = 0.f;
    };

    inline Vec2 FramePoint(FrameRect const& f, float fx, float fy)
    {
        float const c = std::cos(f.angle);
        float const s = std::sin(f.angle);
        return { f.origin.x + c * fx - s * fy, f.origin.y + s * fx + c * fy };
    }

    // A map point in frame coordinates (x along X, y along Y).
    inline Vec2 ToFrame(FrameRect const& f, Vec2 p)
    {
        float const c = std::cos(f.angle);
        float const s = std::sin(f.angle);
        float const dx = p.x - f.origin.x;
        float const dy = p.y - f.origin.y;
        return { c * dx + s * dy, -s * dx + c * dy };
    }

    inline bool InsideFrame(FrameRect const& f, Vec2 p, float eps = 0.01f)
    {
        Vec2 const q = ToFrame(f, p);
        return q.x >= -eps && q.x <= f.sizeX + eps && q.y >= -eps && q.y <= f.sizeY + eps;
    }

    enum class LaneAxis : std::uint8_t
    {
        Along,      // Axis::X (runs sizeX, offsets across sizeY)
        Across      // Axis::Y (runs sizeY, offsets across sizeX)
    };

    // The span the lane offsets of `axis` spread over.
    inline float SpanFor(FrameRect const& f, LaneAxis axis)
    {
        return axis == LaneAxis::Along ? f.sizeY : f.sizeX;
    }

    // `count` lanes of `width` with gaps >= minGap fit across `span` (else the registry spaces them evenly and warns).
    inline bool LanesFit(float span, std::uint32_t count, float width, float minGap)
    {
        if (count == 0)
            return true;
        return count * width + (count - 1) * minGap <= span + 1e-4f;
    }

    // A lane's centreline on the map (mod-boss-mechanics PlaceLane): `offset` is its low edge across the axis.
    struct LaneSegment
    {
        Vec2 from;
        Vec2 to;
        float width = 0.f;
    };

    inline LaneSegment LaneOnFrame(FrameRect const& f, LaneAxis axis, float offset, float width)
    {
        float const mid = offset + width * 0.5f;
        if (axis == LaneAxis::Along)
            return { FramePoint(f, 0.f, mid), FramePoint(f, f.sizeX, mid), width };
        return { FramePoint(f, mid, 0.f), FramePoint(f, mid, f.sizeY), width };
    }
}

#endif
