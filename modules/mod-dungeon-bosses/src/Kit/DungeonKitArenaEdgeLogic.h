/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F57): pure rules for a boss who
 * fights at the edge of his arena. Promoted from Ragefire Chasm (RagefireChasmRework.h, Bazzalan and Taragaman) without
 * a change of rule or number; Ragefire keeps its own copy, and tests/kit_edge_test.cpp pins the two together. No engine
 * headers; the engine half is DungeonKitArenaEdge.h (ArenaEdge, SelfLeash, ReachLeash).
 *
 * Everything lives in the nested namespace DungeonKit::EdgeFight: Vec2 is DungeonKit's, so argument-dependent lookup
 * would offer a DungeonKit::InsideBy to Ragefire's own unqualified calls; the nested namespace is never searched that
 * way.
 *
 *   InsideBy          how far a point is inside a polygon (0 off it)
 *   ClampInto         a point, or its nearest boundary point moved a little inward (a landing that would leave it)
 *   StandSpot         where a boss may stand for a point: strictly inside, at least kStandMarginYd from the boundary
 *   BackSpot          back onto the arena straight toward the target, in melee range all the way
 *   BackstepStays     whether the engine's own step back from a target inside him ends strictly inside
 *   NextEdgeStep      chase, stand or walk (and where), from what he and his target are doing
 *   EdgeReachArena    the arena grown by the band he reaches past its edge (level floor, or in climbing bands)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_EDGE_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ARENA_EDGE_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitEdgeLogic.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <utility>

namespace DungeonKit::EdgeFight
{
    float constexpr kEdgeReachYd = 4.5f;            // the band's width: melee range is 5 yd or more, 3D
    float constexpr kStandInsetYd = 0.25f;          // where he stands is this far inside his arena ...
    float constexpr kStandMarginYd = 0.15f;         // ... and never nearer to its boundary than this
    float constexpr kStandSearchYd = 4.f;           // how far a corner's spot may be from its edge point

    // How far `p` is inside `polygon`; 0 off it.
    inline float InsideBy(std::span<Vec2 const> polygon, Vec2 p)
    {
        if (!PointInPolygon(polygon, p))
            return 0.f;
        auto const edge = NearestEdge(polygon, p);
        return edge ? edge->distance : 0.f;
    }

    // `p` itself when `polygon` holds it, else its nearest boundary point moved `insetYd` straight inward.
    inline Vec2 ClampInto(std::span<Vec2 const> polygon, Vec2 p, float insetYd = 0.25f)
    {
        if (PointInPolygon(polygon, p))
            return p;
        auto const edge = NearestEdge(polygon, p);
        if (!edge)
            return p;
        Vec2 const in = InwardNormal(polygon, edge->edge);
        Vec2 const moved{ edge->point.x + in.x * insetYd, edge->point.y + in.y * insetYd };
        return PointInPolygon(polygon, moved) ? moved : edge->point;
    }

    // Where a boss may stand for `p`: `p` itself when it is strictly inside, else the nearest edge point moved straight
    // in, else (a corner, a narrow end) the nearest point round it that is strictly inside. On the boundary itself, or
    // at a corner's bare edge point (ClampInto), the leash would count him as off it.
    inline Vec2 StandSpot(std::span<Vec2 const> polygon, Vec2 p)
    {
        if (InsideBy(polygon, p) >= kStandMarginYd)
            return p;
        auto const edge = NearestEdge(polygon, p);
        if (!edge)
            return p;
        Vec2 const in = InwardNormal(polygon, edge->edge);
        Vec2 const straight{ edge->point.x + in.x * kStandInsetYd, edge->point.y + in.y * kStandInsetYd };
        if (InsideBy(polygon, straight) >= kStandMarginYd)
            return straight;
        int constexpr bearings = 32;
        for (float r = kStandInsetYd; r <= kStandSearchYd; r += 0.125f)
        {
            Vec2 best{};
            float deepest = 0.f;
            for (int i = 0; i < bearings; ++i)
            {
                Vec2 const at = Advance(edge->point, 2.f * kPi * float(i) / float(bearings), r);
                float const inside = InsideBy(polygon, at);
                if (inside > deepest)
                {
                    best = at;
                    deepest = inside;
                }
            }
            if (deepest >= kStandMarginYd)
                return best;
        }
        return edge->point;
    }

    // Back onto the arena with the target in melee range, straight toward it: in range all the way.
    inline Vec2 BackSpot(std::span<Vec2 const> polygon, Vec2 self, Vec2 target)
    {
        float const distance = Distance(self, target);
        float const bearing = BearingTo(self, target);
        for (float d = kStandInsetYd; d < distance; d += kStandInsetYd)
        {
            Vec2 const at = Advance(self, bearing, d);
            if (InsideBy(polygon, at) >= kStandMarginYd)
                return at;
        }
        return StandSpot(polygon, self);
    }

    // Whether the engine's own step back (MotionMaster::MoveBackwards: `distance` from the target on his side of it)
    // ends strictly inside.
    inline bool BackstepStays(std::span<Vec2 const> polygon, Vec2 self, Vec2 target, float distance)
    {
        return InsideBy(polygon, Advance(target, BearingTo(target, self), distance)) >= kStandMarginYd;
    }

    enum class EdgeAct : std::uint8_t
    {
        Chase,          // the engine's own chase
        Stand,          // where he is
        Walk,           // to `spot`
    };

    struct EdgeView
    {
        Vec2 self;
        Vec2 target;
        bool selfInside = true;     // he is on his arena
        bool targetInside = true;   // his target is on it
        bool targetInReach = true;  // his target is on the reach arena
        bool inMelee = false;
    };

    struct EdgeStep
    {
        EdgeAct act = EdgeAct::Chase;
        Vec2 spot;
    };

    // Off his arena he walks back first, whatever else holds (the leash counts; only a chase of a target inside, which
    // brings him back by itself, goes on until he is in range). Then: a target inside is chased, one out of reach is
    // the reach guard's, one on the band in melee range is fought from where he is, else he walks to its stand spot.
    inline EdgeStep NextEdgeStep(std::span<Vec2 const> polygon, EdgeView const& v)
    {
        if (!v.selfInside && !v.targetInside)
            return { EdgeAct::Walk, StandSpot(polygon, v.self) };
        if (!v.selfInside && v.inMelee)
            return { EdgeAct::Walk, BackSpot(polygon, v.self, v.target) };
        if (v.targetInside)
            return { EdgeAct::Chase, v.self };
        if (!v.targetInReach || v.inMelee)
            return { EdgeAct::Stand, v.self };
        return { EdgeAct::Walk, StandSpot(polygon, v.target) };
    }

    // Where the floor past an edge climbs, how far over the edge's own floor a target may stand: a target `band` yd off
    // the edge is in melee range (3D) of the spot inside it up to here.
    inline float constexpr kReachMelee3dYd = 5.f;
    inline std::array<float, 4> constexpr kReachBandsYd{ 1.5f, 2.5f, 3.5f, kEdgeReachYd };

    inline float ReachRiseYd(float bandYd)
    {
        float const plane = bandYd + kStandInsetYd + 0.1f;      // 0.1: a corner's spot is a little farther in
        return std::sqrt(kReachMelee3dYd * kReachMelee3dYd - plane * plane);
    }

    // `own` grown by kEdgeReachYd: a quad beside every edge, a circle at every corner, in the z band [zMin, zMax]. An
    // edge whose floor `climbFloorOf(edge)` gives (its lowest height; nullopt: level floor) grows in kReachBandsYd
    // steps, each up to its own ReachRiseYd over that floor; a corner takes the lower of its two edges.
    template <typename ClimbFloorOf>
    inline Arena EdgeReachArena(Arena own, std::span<Vec2 const> polygon, float zMin, float zMax,
        ClimbFloorOf&& climbFloorOf)
    {
        std::size_t const n = polygon.size();
        for (std::size_t i = 0; i < n; ++i)
        {
            Vec2 const a = polygon[i];
            Vec2 const b = polygon[(i + 1) % n];
            Vec2 const in = InwardNormal(polygon, i);
            std::optional<float> const climb = climbFloorOf(i);
            std::optional<float> corner = climbFloorOf((i + n - 1) % n);
            if (climb)
                corner = corner ? std::min(*corner, *climb) : *climb;
            auto grow = [&](float yd, float quadZ, float circleZ)
            {
                Vec2 const off{ -in.x * yd, -in.y * yd };
                own.regions.push_back(ArenaRegion::Polygon({ a, b, { b.x + off.x, b.y + off.y },
                    { a.x + off.x, a.y + off.y } }, zMin, quadZ));
                own.regions.push_back(ArenaRegion::Circle(a, yd, zMin, circleZ));
            };
            if (!climb && !corner)
            {
                grow(kEdgeReachYd, zMax, zMax);
                continue;
            }
            for (float const yd : kReachBandsYd)
                grow(yd, climb ? *climb + ReachRiseYd(yd) : zMax, *corner + ReachRiseYd(yd));
        }
        return own;
    }

    // A level floor all round: `own` grown by kEdgeReachYd at its own z band.
    inline Arena EdgeReachArena(Arena own, std::span<Vec2 const> polygon, float zMin, float zMax)
    {
        return EdgeReachArena(std::move(own), polygon, zMin, zMax, [](std::size_t) { return std::optional<float>{}; });
    }
}

#endif
