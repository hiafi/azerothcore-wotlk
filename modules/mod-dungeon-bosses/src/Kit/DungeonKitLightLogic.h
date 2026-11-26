/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff sections 3.11 and 3.4 F23, F53): pure rules
 * for turning lights, cones that turn without stopping around an anchor (the Mobile Alert System's searchlights, the
 * Whole Workshop's lights on Thermaplugg). No engine headers; host-tested by tests/kit_lights_test.cpp. The engine half
 * is DungeonKitLights.h (TurningLights).
 *
 *   LightClock     `count` lights evenly spaced, turning at degPerSec (+1 counter-clockwise, -1 clockwise); Hold
 *                  stops them for a while, Reverse stops them and turns them the other way after the stop, SetSpeed
 *                  changes the rate (the heroic +10% per Spotted). Continuous, not stepped (TurningBeams steps)
 *   LightArc       the bearings one light's middle sweeps over the next N ms (the stop first, then the turn): the bot
 *                  look ahead knows the direction and the reversal
 *   SweptSector    the one cone that covers a light of `coneDeg` over its arc (full circle past 360 degrees)
 *   InLight        is a point inside a light (2D cone from the apex, InFrontalCone's rule, optional inner radius)
 *   TouchLatch     one touch per player per latch (the Spotted 3 s latch), shared by every light of a set
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LIGHT_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LIGHT_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitZoneLogic.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <unordered_map>

namespace DungeonKit
{
    // The arc a light's middle sweeps: from `from` (radians, [0, 2pi)) by `sweep` (signed radians: + is
    // counter-clockwise). sweep 0: the light stands still for the whole horizon.
    struct LightArc
    {
        float from = 0.f;
        float sweep = 0.f;
    };

    // A cone covering a light over its arc: `bearing` is the cone's middle, `angleDeg` its full opening (360: the
    // whole circle).
    struct LightSector
    {
        float bearing = 0.f;
        float angleDeg = 0.f;

        bool Full() const { return angleDeg >= 360.f; }
    };

    // Turning lights. Bearings in radians on the map plane (0 = +x, north; growing counter-clockwise, toward +y west).
    class LightClock
    {
    public:
        LightClock() = default;
        LightClock(float startBearing, float degPerSec, std::uint8_t count, int direction = 1)
            : _bearing(BeamClock::Wrap(startBearing)), _degPerSec(std::max(0.f, degPerSec)),
              _count(std::max<std::uint8_t>(1, count)), _direction(direction < 0 ? -1 : 1) { }

        float Bearing() const { return _bearing; }
        float DegPerSec() const { return _degPerSec; }
        int Direction() const { return _direction; }
        std::uint8_t Count() const { return _count; }
        std::uint32_t HoldLeftMs() const { return _holdLeftMs; }
        bool Turning() const { return _holdLeftMs == 0 && _degPerSec > 0.f; }
        std::uint32_t Reversals() const { return _reversals; }
        float TurnedDeg() const { return _turnedDeg; }     // total turned, both ways (a log number)

        // Light `i`'s bearing now (light 0 is Bearing(); the others 360 / count apart, counter-clockwise).
        float BearingOf(std::uint8_t i) const
        {
            return BeamClock::Wrap(_bearing + kTwoPi * static_cast<float>(i % _count) / static_cast<float>(_count));
        }

        // `diffMs` passes: the hold runs down first, the rest of the time turns the lights.
        void Advance(std::uint32_t diffMs)
        {
            std::uint32_t const held = std::min(diffMs, _holdLeftMs);
            _holdLeftMs -= held;
            std::uint32_t const turning = diffMs - held;
            if (turning == 0 || _degPerSec <= 0.f)
                return;
            float const deg = _degPerSec * static_cast<float>(turning) / 1000.f;
            _bearing = BeamClock::Wrap(_bearing + static_cast<float>(_direction) * deg * kPi / 180.f);
            _turnedDeg += deg;
        }

        // The lights stand still for `ms` from now (a longer hold already running is kept).
        void Hold(std::uint32_t ms) { _holdLeftMs = std::max(_holdLeftMs, ms); }

        // MA4: the lights stop for `stopMs`, then turn the other way.
        void Reverse(std::uint32_t stopMs)
        {
            _direction = -_direction;
            _holdLeftMs = stopMs;
            ++_reversals;
        }

        void SetSpeed(float degPerSec) { _degPerSec = std::max(0.f, degPerSec); }

        // The arc light `i`'s middle sweeps over the next `horizonMs`: the hold first, then the turn in the current
        // direction (a Reverse has already flipped it, so the arc after a reversal runs the new way).
        LightArc Ahead(std::uint8_t i, std::uint32_t horizonMs) const
        {
            LightArc arc;
            arc.from = BearingOf(i);
            std::uint32_t const turning = horizonMs > _holdLeftMs ? horizonMs - _holdLeftMs : 0;
            float const deg = _degPerSec * static_cast<float>(turning) / 1000.f;
            arc.sweep = static_cast<float>(_direction) * deg * kPi / 180.f;
            return arc;
        }

    private:
        float _bearing = 0.f;
        float _degPerSec = 0.f;
        std::uint8_t _count = 1;
        int _direction = 1;
        std::uint32_t _holdLeftMs = 0;
        std::uint32_t _reversals = 0;
        float _turnedDeg = 0.f;
    };

    // The cone of `coneDeg` swept along `arc`: its middle halfway along the arc, its opening the cone plus the arc
    // (360 or more: the whole circle).
    inline LightSector SweptSector(LightArc const& arc, float coneDeg)
    {
        LightSector s;
        float const sweepDeg = std::fabs(arc.sweep) * 180.f / kPi;
        s.angleDeg = std::min(360.f, std::max(0.f, coneDeg) + sweepDeg);
        s.bearing = BeamClock::Wrap(arc.from + arc.sweep * 0.5f);
        return s;
    }

    // Is `p` inside a light from `apex` along `bearing`, `angleDeg` wide and `lengthYd` long, and at least `innerYd`
    // from the apex? 2D (the caller checks the height band), edges count as inside (InFrontalCone).
    inline bool InLight(Vec2 apex, float bearing, float angleDeg, float lengthYd, Vec2 p, float innerYd = 0.f)
    {
        if (innerYd > 0.f && Distance(apex, p) < innerYd)
            return false;
        if (angleDeg >= 360.f)
            return Distance(apex, p) <= lengthYd;
        return InFrontalCone(apex, bearing, p, angleDeg, lengthYd);
    }

    // One touch per key per latch: Try answers true (and starts the latch) when `key` has not touched within the
    // last `latchMs`. Times are one clock's milliseconds (the owner's fight time).
    class TouchLatch
    {
    public:
        bool Try(std::uint64_t key, std::uint32_t nowMs, std::uint32_t latchMs)
        {
            auto it = _last.find(key);
            if (it != _last.end() && nowMs - it->second < latchMs)
                return false;
            _last[key] = nowMs;
            return true;
        }

        // Milliseconds until `key` may touch again (0: now).
        std::uint32_t LeftMs(std::uint64_t key, std::uint32_t nowMs, std::uint32_t latchMs) const
        {
            auto it = _last.find(key);
            if (it == _last.end() || nowMs - it->second >= latchMs)
                return 0;
            return latchMs - (nowMs - it->second);
        }

        void Clear() { _last.clear(); }
        std::size_t Size() const { return _last.size(); }

    private:
        std::unordered_map<std::uint64_t, std::uint32_t> _last;
    };
}

#endif
