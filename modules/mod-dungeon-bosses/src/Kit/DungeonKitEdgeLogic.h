/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Depths WP-KT-D1, handoff section 3.11 #2 and #3): pure rules
 * for pushing a unit over a floor's real edge and for the lethal bands along it (Lord Incendius's crumbled edge, Arm
 * Sweep's throw, Magma Fist's knockback near the edge; SP S2 900-918, plan section 8 #42). No engine headers;
 * host-tested by tests/dungeon_kit_test.cpp. The engine half is DungeonKitEdges.h (PushOverEdge, LethalBand).
 *
 * The floor is a polygon of the real walkable edge (the causeway's top, not the arena): beyond it is the drop.
 *
 *   NearestEdge       the nearest point of the polygon's boundary to a point, its distance and edge index
 *   InwardNormal      the unit normal of one edge pointing into the polygon (either winding)
 *   OutwardBearing    the shortest way out from a point: towards its nearest edge point (on the edge: the normal)
 *   AwayFromLine      perpendicular away from a centre line (SP: "pushed outward from the island's center line")
 *   PlanOverEdge      along a bearing to where the ray leaves the floor for good, then `beyondYd` past it
 *   PlanKnockback     a fixed-length throw (Magma Fist's 10 yd) that, when it crosses the edge, lands at least
 *                     `beyondYd` past it: never a landing on the rim
 *   EdgeJumpSpeedXY   the jump's horizontal speed for a set flight time (JumpTo's arc: flight = distance / speedXY)
 *   EdgeBand          the band along one edge between two depths (a crumble step), as a two-point line and width
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_EDGE_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_EDGE_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitWallLogic.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace DungeonKit
{
    float constexpr kEdgeBeyondYd = 4.f;            // a push lands this far past the real edge (clear of the rim)
    float constexpr kEdgeDropYd = 1.f;              // a player's jump ends this far under the floor (then falls)
    std::uint32_t constexpr kEdgeFlightMs = 800;    // the push's flight (the jump's duration)
    float constexpr kEdgeMinSpeedXY = 8.f;          // yd/s: a short push still flies, never crawls
    std::uint32_t constexpr kBandWarnMs = 5000;     // SP S2 909: the crumble's 5 s edge marker
    std::uint32_t constexpr kBandGraceExtraMs = 600;    // past the flight, before a pushed unit counts again
    std::uint32_t constexpr kEdgeMaxExits = 16;     // PlanOverEdge's walk through a concave floor's re-entries

    struct EdgePoint
    {
        Vec2 point;
        float distance = 0.f;
        std::size_t edge = 0;       // the edge from vertex `edge` to vertex `edge + 1` (wrapping)
    };

    // The nearest boundary point of `poly` to `p` (any side). Needs at least 2 vertices; nullopt otherwise.
    inline std::optional<EdgePoint> NearestEdge(std::span<Vec2 const> poly, Vec2 p)
    {
        std::size_t const n = poly.size();
        if (n < 2)
            return std::nullopt;
        std::optional<EdgePoint> best;
        for (std::size_t i = 0; i < n; ++i)
        {
            Vec2 const a = poly[i];
            Vec2 const b = poly[(i + 1) % n];
            float along = 0.f;
            float const d = SegmentDistance(a, b, p, &along);
            if (best && d >= best->distance)
                continue;
            float const len = Distance(a, b);
            float const t = len > 1e-6f ? along / len : 0.f;
            best = EdgePoint{ { a.x + t * (b.x - a.x), a.y + t * (b.y - a.y) }, d, i };
        }
        return best;
    }

    // The unit normal of edge `edge` that points into `poly` (tested 0.05 yd off the edge's middle, so either winding
    // works). A degenerate edge gives {0, 0}.
    inline Vec2 InwardNormal(std::span<Vec2 const> poly, std::size_t edge)
    {
        std::size_t const n = poly.size();
        if (n < 3)
            return {};
        Vec2 const a = poly[edge % n];
        Vec2 const b = poly[(edge + 1) % n];
        float const len = Distance(a, b);
        if (len < 1e-6f)
            return {};
        Vec2 nrm{ -(b.y - a.y) / len, (b.x - a.x) / len };       // the left normal of a -> b
        Vec2 const mid{ (a.x + b.x) * 0.5f, (a.y + b.y) * 0.5f };
        if (!PointInPolygon(poly, { mid.x + nrm.x * 0.05f, mid.y + nrm.y * 0.05f }))
            nrm = { -nrm.x, -nrm.y };
        return nrm;
    }

    // The shortest way out of `poly` from `p`: the bearing to its nearest boundary point; on the boundary (within 0.05
    // yd) the edge's outward normal. `fallback` when the polygon is degenerate.
    inline float OutwardBearing(std::span<Vec2 const> poly, Vec2 p, float fallback = 0.f)
    {
        std::optional<EdgePoint> const e = NearestEdge(poly, p);
        if (!e)
            return fallback;
        bool const inside = PointInPolygon(poly, p);
        if (e->distance > 0.05f)
        {
            // Outside the floor already: keep going away from it.
            return inside ? BearingTo(p, e->point) : BearingTo(e->point, p);
        }
        Vec2 const in = InwardNormal(poly, e->edge);
        if (std::fabs(in.x) < 1e-6f && std::fabs(in.y) < 1e-6f)
            return fallback;
        return BearingTo({ 0.f, 0.f }, { -in.x, -in.y });
    }

    // Perpendicular away from the centre line a-b (the side `p` is on); on the line, `fallback`.
    inline float AwayFromLine(Vec2 a, Vec2 b, Vec2 p, float fallback = 0.f)
    {
        float along = 0.f;
        float const d = SegmentDistance(a, b, p, &along);
        if (d < 0.05f)
            return fallback;
        float const len = Distance(a, b);
        float const t = len > 1e-6f ? along / len : 0.f;
        return BearingTo({ a.x + t * (b.x - a.x), a.y + t * (b.y - a.y) }, p);
    }

    struct EdgePush
    {
        Vec2 landing;               // where the throw ends (past the edge, or on the floor for a short knockback)
        Vec2 exit;                  // where the path leaves the floor for good (= landing when it stays on it)
        float bearing = 0.f;
        float distance = 0.f;       // from the start to the landing (2D)
        float exitYd = 0.f;         // from the start to the exit (0: it started off the floor)
        bool overEdge = false;      // the landing is off the floor: a fall
    };

    // Along `bearing` from `p` to the point where the ray leaves `poly` for good (a concave floor's notch it crosses
    // and re-enters is walked through), then `beyondYd` past it. A start already off the floor lands `beyondYd` on.
    inline EdgePush PlanOverEdge(std::span<Vec2 const> poly, Vec2 p, float bearing, float beyondYd = kEdgeBeyondYd)
    {
        float const beyond = std::max(0.f, beyondYd);
        EdgePush r;
        r.bearing = bearing;
        r.overEdge = true;
        if (!PointInPolygon(poly, p))
        {
            r.exit = p;
            r.landing = Advance(p, bearing, beyond);
            r.distance = beyond;
            return r;
        }
        float travelled = 0.f;
        for (std::uint32_t i = 0; i < kEdgeMaxExits; ++i)
        {
            std::optional<float> const hit = RayToPolygonEdge(poly, Advance(p, bearing, travelled), bearing);
            if (!hit)
                break;
            travelled += *hit;
            // Past this edge: off the floor? (0.05 yd in, so a vertex graze is not read as a re-entry.)
            if (!PointInPolygon(poly, Advance(p, bearing, travelled + 0.05f)))
            {
                // The landing must be off the floor too (a notch narrower than beyondYd re-enters before it).
                Vec2 const land = Advance(p, bearing, travelled + beyond);
                if (!PointInPolygon(poly, land))
                {
                    r.exitYd = travelled;
                    r.exit = Advance(p, bearing, travelled);
                    r.landing = land;
                    r.distance = travelled + beyond;
                    return r;
                }
            }
            travelled += 0.05f;
        }
        // No way out found (cannot happen for a closed polygon and an inside start): straight on by beyondYd.
        r.exit = Advance(p, bearing, travelled);
        r.exitYd = travelled;
        r.landing = Advance(p, bearing, travelled + beyond);
        r.distance = travelled + beyond;
        return r;
    }

    // A throw of `distanceYd` along `bearing`: on the floor when it stays on it (overEdge false; exit = landing), else
    // over the edge, at least `beyondYd` past the exit (PlanOverEdge's landing when that is farther).
    inline EdgePush PlanKnockback(std::span<Vec2 const> poly, Vec2 p, float bearing, float distanceYd,
        float beyondYd = kEdgeBeyondYd)
    {
        float const dist = std::max(0.f, distanceYd);
        Vec2 const end = Advance(p, bearing, dist);
        if (PointInPolygon(poly, p))
        {
            std::optional<float> const hit = RayToPolygonEdge(poly, p, bearing);
            if (!hit || *hit >= dist)
            {
                // The first wall is past the throw: it stays on the floor.
                EdgePush r;
                r.bearing = bearing;
                r.landing = end;
                r.exit = end;
                r.exitYd = dist;
                r.distance = dist;
                r.overEdge = false;
                return r;
            }
        }
        EdgePush r = PlanOverEdge(poly, p, bearing, beyondYd);
        if (r.distance < dist && !PointInPolygon(poly, end))
        {
            r.landing = end;
            r.distance = dist;
        }
        return r;
    }

    // JumpTo's horizontal speed for a flight of `flightMs` over `distance` yd, at least `minSpeed`.
    inline float EdgeJumpSpeedXY(float distance, std::uint32_t flightMs = kEdgeFlightMs,
        float minSpeed = kEdgeMinSpeedXY)
    {
        if (flightMs == 0)
            return std::max(minSpeed, 1.f);
        return std::max(minSpeed, distance * 1000.f / static_cast<float>(flightMs));
    }

    // The flight time of that jump (ms, rounded).
    inline std::uint32_t EdgeFlightMs(float distance, float speedXY)
    {
        return speedXY > 0.f ? static_cast<std::uint32_t>(std::lround(distance * 1000.f / speedXY)) : 0u;
    }

    // The band along edge `edge` from `fromDepthYd` to `toDepthYd` inside the floor (a crumble: 0 to 4, then 4 to 8;
    // Lord of the Lake's long edges: 0 to 2, 2 to 4, 4 to 6), as the centre line and width a registry Line takes. The
    // line runs the edge's full length (shifted in); `extendYd` stretches both ends (to close the corners). A
    // degenerate edge or depths gives width 0.
    inline WallLine EdgeBand(std::span<Vec2 const> poly, std::size_t edge, float fromDepthYd, float toDepthYd,
        float extendYd = 0.f)
    {
        WallLine band;
        std::size_t const n = poly.size();
        if (n < 3 || toDepthYd <= fromDepthYd)
        {
            band.width = 0.f;
            return band;
        }
        Vec2 const a = poly[edge % n];
        Vec2 const b = poly[(edge + 1) % n];
        Vec2 const in = InwardNormal(poly, edge);
        float const len = Distance(a, b);
        if (len < 1e-6f)
        {
            band.width = 0.f;
            return band;
        }
        float const mid = (std::max(0.f, fromDepthYd) + toDepthYd) * 0.5f;
        Vec2 const dir{ (b.x - a.x) / len, (b.y - a.y) / len };
        band.from = { a.x + in.x * mid - dir.x * extendYd, a.y + in.y * mid - dir.y * extendYd };
        band.to = { b.x + in.x * mid + dir.x * extendYd, b.y + in.y * mid + dir.y * extendYd };
        band.width = toDepthYd - std::max(0.f, fromDepthYd);
        return band;
    }

    // One band per listed edge (all edges when `edges` is empty).
    inline std::vector<WallLine> EdgeBands(std::span<Vec2 const> poly, std::span<std::size_t const> edges,
        float fromDepthYd, float toDepthYd, float extendYd = 0.f)
    {
        std::vector<WallLine> out;
        if (edges.empty())
        {
            for (std::size_t i = 0; i < poly.size(); ++i)
                out.push_back(EdgeBand(poly, i, fromDepthYd, toDepthYd, extendYd));
        }
        else
            for (std::size_t i : edges)
                out.push_back(EdgeBand(poly, i, fromDepthYd, toDepthYd, extendYd));
        out.erase(std::remove_if(out.begin(), out.end(), [](WallLine const& w) { return w.width <= 0.f; }),
            out.end());
        return out;
    }
}

#endif
