/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff sections 3.11 and 3.4 F37, F54): pure rules
 * for a called combination, a chain of punches drawn on a room frame (Crowd Pummeler's pocket, the Whole Workshop's
 * fist from a Gnome Face). No engine headers; host-tested by tests/kit_combo_test.cpp. The engine half is
 * DungeonKitCombo.h (CalledCombination).
 *
 *   ComboFrame      a reference point, its floor height and a facing: "forward" runs along the facing, "left" 90
 *                   degrees counter-clockwise from it (the frame of the window looking south: forward = south,
 *                   left = east)
 *   ComboShapeDef   one punch's shape in frame terms: a circle, a donut, a cone or a rectangle (a half, a lane),
 *                   anchored `forwardYd` along and `leftYd` across the frame. Factories: Circle, Donut, Cone,
 *                   Rect, HalfLeft, HalfRight, Lane
 *   PlacedShape     the shape on the map (Place), with Contains (the registry's own test: circle, donut, cone,
 *                   line) and LabelPoint (where a numeral marker stands)
 *   ComboTimeline   when each punch of a chain calls, shows its live marker and strikes. Sequential: one call flash
 *                   per punch, in order, then the live markers; AllAtOnce: every call drawn from the start (the
 *                   fist's numbered shapes), each kept until its live marker
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_COMBO_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_COMBO_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitZoneLogic.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace DungeonKit
{
    enum class ComboShapeType : std::uint8_t
    {
        Circle,
        Donut,
        Cone,
        Rect        // a registry Line: from its anchor along its facing, `widthYd` across, centered on the axis
    };

    struct ComboFrame
    {
        Vec2 origin;
        float z = 0.f;
        float facing = 0.f;         // radians: "forward"

        Vec2 Point(float forwardYd, float leftYd) const
        {
            return Advance(Advance(origin, facing, forwardYd), facing + kPi * 0.5f, leftYd);
        }
    };

    struct ComboShapeDef
    {
        ComboShapeType type = ComboShapeType::Circle;
        float forwardYd = 0.f;      // the anchor, in frame terms
        float leftYd = 0.f;
        float turnDeg = 0.f;        // Cone, Rect: the shape's facing from the frame's (counter-clockwise)
        float radiusYd = 0.f;       // Circle; Donut: the outer edge
        float innerYd = 0.f;        // Donut
        float lengthYd = 0.f;       // Cone, Rect
        float widthYd = 0.f;        // Rect
        float angleDeg = 0.f;       // Cone

        static ComboShapeDef Circle(float forwardYd, float leftYd, float radiusYd)
        {
            ComboShapeDef d;
            d.type = ComboShapeType::Circle;
            d.forwardYd = forwardYd;
            d.leftYd = leftYd;
            d.radiusYd = radiusYd;
            return d;
        }

        static ComboShapeDef Donut(float forwardYd, float leftYd, float innerYd, float outerYd)
        {
            ComboShapeDef d;
            d.type = ComboShapeType::Donut;
            d.forwardYd = forwardYd;
            d.leftYd = leftYd;
            d.innerYd = innerYd;
            d.radiusYd = outerYd;
            return d;
        }

        static ComboShapeDef Cone(float forwardYd, float leftYd, float turnDeg, float angleDeg, float lengthYd)
        {
            ComboShapeDef d;
            d.type = ComboShapeType::Cone;
            d.forwardYd = forwardYd;
            d.leftYd = leftYd;
            d.turnDeg = turnDeg;
            d.angleDeg = angleDeg;
            d.lengthYd = lengthYd;
            return d;
        }

        // A rectangle from (forwardYd, leftYd) along the frame's facing turned by turnDeg, lengthYd long, widthYd
        // across (centered on that axis).
        static ComboShapeDef Rect(float forwardYd, float leftYd, float turnDeg, float lengthYd, float widthYd)
        {
            ComboShapeDef d;
            d.type = ComboShapeType::Rect;
            d.forwardYd = forwardYd;
            d.leftYd = leftYd;
            d.turnDeg = turnDeg;
            d.lengthYd = lengthYd;
            d.widthYd = widthYd;
            return d;
        }

        // The half of the room left of the center line (the line through the origin along the facing), from
        // `fromYd` forward to `toYd`, `acrossYd` wide from the line.
        static ComboShapeDef HalfLeft(float fromYd, float toYd, float acrossYd)
        {
            return Rect(fromYd, acrossYd * 0.5f, 0.f, toYd - fromYd, acrossYd);
        }

        static ComboShapeDef HalfRight(float fromYd, float toYd, float acrossYd)
        {
            return Rect(fromYd, -acrossYd * 0.5f, 0.f, toYd - fromYd, acrossYd);
        }

        // A lane `widthYd` wide down the center line, from `fromYd` forward to `toYd`.
        static ComboShapeDef Lane(float fromYd, float toYd, float widthYd)
        {
            return Rect(fromYd, 0.f, 0.f, toYd - fromYd, widthYd);
        }
    };

    struct PlacedShape
    {
        ComboShapeType type = ComboShapeType::Circle;
        Vec2 at;
        float z = 0.f;
        float facing = 0.f;
        float radiusYd = 0.f;
        float innerYd = 0.f;
        float lengthYd = 0.f;
        float widthYd = 0.f;
        float angleDeg = 0.f;

        // The registry's test (MechanicGeometry.h Contains), 2D: edges count.
        bool Contains(Vec2 p) const
        {
            float constexpr eps = 1e-3f;
            float const dx = p.x - at.x;
            float const dy = p.y - at.y;
            float const d2 = dx * dx + dy * dy;
            switch (type)
            {
                case ComboShapeType::Circle:
                    return d2 <= (radiusYd + eps) * (radiusYd + eps);
                case ComboShapeType::Donut:
                    return d2 > innerYd * innerYd && d2 <= (radiusYd + eps) * (radiusYd + eps);
                case ComboShapeType::Cone:
                    if (d2 > (lengthYd + eps) * (lengthYd + eps))
                        return false;
                    return angleDeg >= 360.f || d2 < 1e-8f || InFrontalCone(at, facing, p, angleDeg, lengthYd + eps);
                case ComboShapeType::Rect:
                {
                    float const c = std::cos(facing);
                    float const s = std::sin(facing);
                    float const along = dx * c + dy * s;
                    float const across = -dx * s + dy * c;
                    return along >= -eps && along <= lengthYd + eps && std::fabs(across) <= widthYd * 0.5f + eps;
                }
            }
            return false;
        }

        // Where a numeral marker stands: a circle's middle, a donut's ring halfway out along the facing, a cone's
        // and a rectangle's middle along their axis.
        Vec2 LabelPoint() const
        {
            switch (type)
            {
                case ComboShapeType::Circle:
                    return at;
                case ComboShapeType::Donut:
                    return Advance(at, facing, (innerYd + radiusYd) * 0.5f);
                case ComboShapeType::Cone:
                case ComboShapeType::Rect:
                    return Advance(at, facing, lengthYd * 0.5f);
            }
            return at;
        }
    };

    inline PlacedShape Place(ComboFrame const& frame, ComboShapeDef const& def)
    {
        PlacedShape p;
        p.type = def.type;
        p.at = frame.Point(def.forwardYd, def.leftYd);
        p.z = frame.z;
        p.facing = BeamClock::Wrap(frame.facing + def.turnDeg * kPi / 180.f);
        p.radiusYd = def.radiusYd;
        p.innerYd = def.innerYd;
        p.lengthYd = def.lengthYd;
        p.widthYd = def.widthYd;
        p.angleDeg = def.angleDeg;
        return p;
    }

    // A frame on the line from `from` (a Gnome Face) through `through` (the room's center): origin at `from`,
    // forward toward `through`.
    inline ComboFrame FrameFacing(Vec2 from, float z, Vec2 through)
    {
        ComboFrame f;
        f.origin = from;
        f.z = z;
        f.facing = BearingTo(from, through);
        return f;
    }

    enum class ComboCallMode : std::uint8_t
    {
        Sequential,     // punch i's call flashes for callMs from i x callMs (Crowd Pummeler: 1 s each, in order)
        AllAtOnce       // every call shows from the start until its own live marker (the fist's numbered shapes)
    };

    struct ComboTiming
    {
        ComboCallMode mode = ComboCallMode::Sequential;
        std::uint32_t callMs = 1000;        // Sequential: each call; AllAtOnce: the wind-up to the first live marker
        std::uint32_t liveMs = 1500;        // a punch's live marker before it strikes (0: the call stays to the strike)
        std::uint32_t spacingMs = 2000;     // strike to strike
    };

    // One punch's times, in ms from the combination's start.
    struct PunchTimes
    {
        std::uint32_t callFrom = 0;
        std::uint32_t callTo = 0;           // = liveFrom in AllAtOnce
        std::uint32_t liveFrom = 0;
        std::uint32_t strikeAt = 0;
    };

    // Sequential: calls back to back, then the first live marker right after the last call; AllAtOnce: the first
    // live marker after the wind-up (callMs). Strikes spacingMs apart.
    inline std::vector<PunchTimes> ComboTimeline(ComboTiming const& t, std::size_t punches)
    {
        std::vector<PunchTimes> out(punches);
        std::uint32_t const callsEnd = t.mode == ComboCallMode::Sequential
            ? t.callMs * static_cast<std::uint32_t>(punches) : t.callMs;
        for (std::size_t i = 0; i < punches; ++i)
        {
            PunchTimes& p = out[i];
            p.strikeAt = callsEnd + t.liveMs + t.spacingMs * static_cast<std::uint32_t>(i);
            p.liveFrom = p.strikeAt - t.liveMs;
            if (t.mode == ComboCallMode::Sequential)
            {
                p.callFrom = t.callMs * static_cast<std::uint32_t>(i);
                p.callTo = p.callFrom + t.callMs;
            }
            else
            {
                p.callFrom = 0;
                p.callTo = p.liveFrom;
            }
        }
        return out;
    }

    // The last strike (0 for no punch).
    inline std::uint32_t ComboLength(ComboTiming const& t, std::size_t punches)
    {
        std::vector<PunchTimes> const times = ComboTimeline(t, punches);
        return times.empty() ? 0 : times.back().strikeAt;
    }
}

#endif
