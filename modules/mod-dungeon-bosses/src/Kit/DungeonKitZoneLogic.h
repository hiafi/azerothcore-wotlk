/*
 * mod-dungeon-bosses, the shared dungeon kit (Scarlet Monastery WP-KT-SM, handoff section 3.11 #1 and #5): pure rules
 * for zones that change over time. No engine headers; host-tested by tests/dungeon_kit_test.cpp. The engine half is
 * DungeonKitZones.h (GrowingZone, GrowingZones, TurningBeams).
 *
 *   GrowthPlan      a radius that grows in steps: fromYd at the start, toYd after overMs, one step every stepMs
 *                   (Ironspine's heroic Grave Rot, 7 to 10 yd over 30 s); RadiusAt, StepCount, NextStepInMs
 *   NearestRung     the visual rung (a ground look per radius) closest to a radius; a tie goes to the larger rung
 *   BeamClock       turning beams (L43, Herod's Ravager's Beacon): `count` beams evenly spaced around an anchor,
 *                   turning `stepDeg` each step, the direction flipped on demand
 *   BeamSegment     one beam's lane: from `innerYd` off the anchor to `innerYd + lengthYd`, or short of a wall
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ZONE_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ZONE_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Growing zone
    // ----------------------------------------------------------------------------------------------------------------

    // A radius that grows (or shrinks: toYd < fromYd) in equal steps. overMs or stepMs 0: no timed growth (the radius
    // stays fromYd; GrowingZone::GrowTo still steps it by hand, the Librarian's mist "+3 yd per page").
    struct GrowthPlan
    {
        float fromYd = 0.f;
        float toYd = 0.f;
        std::uint32_t overMs = 0;
        std::uint32_t stepMs = 0;

        bool Timed() const { return overMs > 0 && stepMs > 0 && fromYd != toYd; }

        // Steps from fromYd to toYd: ceil(overMs / stepMs) (0 when not timed). 7 to 10 yd over 30 s at 10 s: 3.
        std::uint32_t StepCount() const
        {
            if (!Timed())
                return 0;
            return (overMs + stepMs - 1) / stepMs;
        }

        // The radius `elapsedMs` after the start: fromYd until the first step, toYd from the last step on.
        float RadiusAt(std::uint32_t elapsedMs) const
        {
            std::uint32_t const total = StepCount();
            if (total == 0)
                return fromYd;
            std::uint32_t const done = std::min<std::uint32_t>(elapsedMs / stepMs, total);
            return fromYd + (toYd - fromYd) * static_cast<float>(done) / static_cast<float>(total);
        }

        // Milliseconds from `elapsedMs` to the next step; nullopt once the last step is done (or not timed).
        std::optional<std::uint32_t> NextStepInMs(std::uint32_t elapsedMs) const
        {
            std::uint32_t const total = StepCount();
            if (total == 0)
                return std::nullopt;
            std::uint32_t const done = elapsedMs / stepMs;
            if (done >= total)
                return std::nullopt;
            return (done + 1) * stepMs - elapsedMs;
        }
    };

    // The index of the rung radius closest to `radius` (a tie goes to the larger rung); nullopt for no rungs.
    inline std::optional<std::size_t> NearestRung(std::span<float const> rungRadii, float radius)
    {
        std::optional<std::size_t> best;
        float bestGap = 0.f;
        for (std::size_t i = 0; i < rungRadii.size(); ++i)
        {
            float const gap = std::fabs(rungRadii[i] - radius);
            if (!best || gap < bestGap - 1e-4f
                || (std::fabs(gap - bestGap) <= 1e-4f && rungRadii[i] > rungRadii[*best]))
            {
                best = i;
                bestGap = gap;
            }
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Turning beams
    // ----------------------------------------------------------------------------------------------------------------

    // Bearings of `count` beams spaced 360 / count apart, the first on `Bearing()`. Step() turns them all by stepDeg
    // in the current direction (+1: counter-clockwise, the map's growing orientation; -1: clockwise); Flip() reverses
    // the direction for the next steps.
    class BeamClock
    {
    public:
        BeamClock() = default;
        BeamClock(float startBearing, float stepDeg, std::uint8_t count, int direction = 1)
            : _bearing(Wrap(startBearing)), _stepRad(stepDeg * kPi / 180.f), _count(std::max<std::uint8_t>(1, count)),
              _direction(direction < 0 ? -1 : 1) { }

        float Bearing() const { return _bearing; }
        int Direction() const { return _direction; }
        std::uint8_t Count() const { return _count; }
        std::uint32_t Steps() const { return _steps; }

        // Beam `i`'s bearing now.
        float BearingOf(std::uint8_t i) const
        {
            return Wrap(_bearing + kTwoPi * static_cast<float>(i % _count) / static_cast<float>(_count));
        }

        // The bearing of beam `i` after one more step (the step the next marker shows).
        float NextBearingOf(std::uint8_t i) const
        {
            return Wrap(BearingOf(i) + static_cast<float>(_direction) * _stepRad);
        }

        void Step()
        {
            _bearing = Wrap(_bearing + static_cast<float>(_direction) * _stepRad);
            ++_steps;
        }

        void Flip() { _direction = -_direction; }

        static float Wrap(float o)
        {
            o = std::fmod(o, kTwoPi);
            if (o < 0.f)
                o += kTwoPi;
            return o;
        }

    private:
        float _bearing = 0.f;
        float _stepRad = 0.f;
        std::uint8_t _count = 1;
        int _direction = 1;
        std::uint32_t _steps = 0;
    };

    struct BeamLane
    {
        Vec2 from;
        Vec2 to;
        float length = 0.f;     // from -> to
        bool clipped = false;   // a wall stopped it short of innerYd + lengthYd
    };

    // One beam's lane along `bearing`: from `innerYd` off `anchor` to `innerYd + lengthYd`. With `wallYd` (the
    // distance from the anchor to the wall along the bearing: Arena::RayToEdge), it stops `inset` short of the wall;
    // nullopt when that leaves nothing (the wall is inside innerYd).
    inline std::optional<BeamLane> BeamSegment(Vec2 anchor, float bearing, float innerYd, float lengthYd,
        std::optional<float> wallYd = std::nullopt, float inset = 0.5f)
    {
        float outer = innerYd + lengthYd;
        bool clipped = false;
        if (wallYd && *wallYd - inset < outer)
        {
            outer = *wallYd - inset;
            clipped = true;
        }
        if (outer <= innerYd + 0.01f)
            return std::nullopt;
        BeamLane lane;
        lane.from = Advance(anchor, bearing, innerYd);
        lane.to = Advance(anchor, bearing, outer);
        lane.length = outer - innerYd;
        lane.clipped = clipped;
        return lane;
    }
}

#endif
