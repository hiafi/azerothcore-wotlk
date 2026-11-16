/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Spire WP-KT-B2, handoff section 3.11 #6): pure rules for the
 * ring wall, the circle form of the lethal wall (DungeonKitWallLogic.h) with a push-out of everyone but the pair it
 * closes round (Drakkisath's Champion's Challenge, SP DR17). No engine headers; host-tested by
 * tests/kit_fronts_test.cpp. The engine half is DungeonKitRing.h (LethalRing, LethalRings).
 *
 *   RingWall         the ring: a centre, the band's middle radius and its width (the registry Donut's hitbox)
 *   RingClearance    how far a point stands from the band (negative inside it); InsideRingBand, InsideRing (the
 *                    disc the band closes, band excluded)
 *   CrossesRing      a step from one poll to the next that went across the band's middle circle (a blink, a charge,
 *                    a knockback the kit did not give): the registry's tick sees only where a unit stands
 *   RingWatch        the last position of every unit near one ring; Observe reports a crossing
 *   PushOutNeeded    whether a unit is pushed out: not kept in, and inside the band's outer edge (at the close) or
 *                    inside the disc (later ticks)
 *   PlanPushOut      where a pushed unit lands (straight out from the centre, `clearYd` past the band) and the point
 *                    Unit::KnockbackFrom pushes it away from; PushSpeedXY, PushFlightMs: the knockback's numbers
 *   GraceBook        a pushed unit is neither struck nor read as crossing while it flies over the band
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_RING_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_RING_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <unordered_map>

namespace DungeonKit
{
    float constexpr kRingDefaultRadiusYd = 12.f;        // SP DR17: a 12 yd ring
    float constexpr kRingDefaultWidthYd = 2.f;
    float constexpr kRingPushClearYd = 3.f;             // a pushed unit lands this far outside the band
    float constexpr kRingPushSpeedZ = 7.f;              // the knockback's vertical speed (yd/s)
    float constexpr kRingGravity = 19.29110527038574f;  // Movement::gravity
    std::uint32_t constexpr kRingPushGraceExtraMs = 600;    // past the flight time, for the landing and the next poll
    std::uint32_t constexpr kRingArmMs = 1500;          // the push lands before the ring kills (flight about 0.7 s)
    std::uint32_t constexpr kRingLifeMs = 12000;        // SP DR17: a lethal wall for 12 s

    struct RingWall
    {
        Vec2 center;
        float radius = kRingDefaultRadiusYd;    // the band's middle
        float width = kRingDefaultWidthYd;

        float HalfWidth() const { return width * 0.5f; }
        float Inner() const { return std::max(0.f, radius - HalfWidth()); }
        float Outer() const { return radius + HalfWidth(); }
    };

    // Distance from `p` to the band's edge: negative inside the band.
    inline float RingClearance(RingWall const& w, Vec2 p)
    {
        return std::fabs(Distance(w.center, p) - w.radius) - w.HalfWidth();
    }

    inline bool InsideRingBand(RingWall const& w, Vec2 p)
    {
        return RingClearance(w, p) <= 0.f;
    }

    // Inside the disc the ring closes (band excluded).
    inline bool InsideRing(RingWall const& w, Vec2 p)
    {
        return Distance(w.center, p) < w.Inner();
    }

    // A step from `prev` to `cur` that went across the band's middle circle (in, out, or through and out again). A
    // step longer than `maxStepYd` is a teleport, never a crossing.
    inline bool CrossesRing(RingWall const& w, Vec2 prev, Vec2 cur, float maxStepYd = 30.f)
    {
        if (Distance(prev, cur) > maxStepYd)
            return false;
        float const d0 = Distance(w.center, prev);
        float const d1 = Distance(w.center, cur);
        if ((d0 < w.radius) != (d1 < w.radius))
            return true;
        if (d0 < w.radius)
            return false;       // both inside the circle: a chord of a disc stays inside it
        // Both outside: crossed only when the step passed through the disc (in and out again).
        return SegmentDistance(prev, cur, w.center) < w.radius;
    }

    // The last seen position of every unit one ring watches (WallWatch's rules: Observe each unit that counts this
    // poll, then Sweep; a unit not observed in a poll is forgotten).
    class RingWatch
    {
    public:
        explicit RingWatch(RingWall ring, float maxStepYd = 30.f) : _ring(ring), _maxStep(maxStepYd) { }

        bool Observe(std::uint64_t id, Vec2 p)
        {
            auto it = _seen.find(id);
            bool crossed = false;
            if (it == _seen.end())
                _seen.emplace(id, Seen{ p, _generation });
            else
            {
                crossed = CrossesRing(_ring, it->second.at, p, _maxStep);
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
        RingWall const& Ring() const { return _ring; }

    private:
        struct Seen
        {
            Vec2 at;
            std::uint64_t generation = 0;
        };

        RingWall _ring;
        float _maxStep;
        std::unordered_map<std::uint64_t, Seen> _seen;
        std::uint64_t _generation = 0;
    };

    // At the close (`closing`): everyone not kept in and inside the band's outer edge (plus `marginYd`) is pushed. On
    // later ticks: only those inside the disc (someone in the band is the wall's; someone outside is fine).
    inline bool PushOutNeeded(RingWall const& w, Vec2 p, bool keptIn, bool closing, float marginYd = 0.5f)
    {
        if (keptIn)
            return false;
        float const d = Distance(w.center, p);
        return closing ? d < w.Outer() + marginYd : d < w.Inner();
    }

    struct PushOut
    {
        Vec2 landing;       // where it lands
        Vec2 source;        // Unit::KnockbackFrom's point (1 yd behind the unit, on the centre's side)
        float distance = 0.f;
    };

    // Straight out from the centre to `clearYd` past the band. A unit on the centre goes along `fallbackBearing`.
    inline PushOut PlanPushOut(RingWall const& w, Vec2 p, float clearYd = kRingPushClearYd,
        float fallbackBearing = 0.f)
    {
        float const d = Distance(w.center, p);
        float const o = d < 0.05f ? fallbackBearing : BearingTo(w.center, p);
        PushOut r;
        r.landing = Advance(w.center, o, w.Outer() + std::max(0.f, clearYd));
        r.distance = std::max(0.f, w.Outer() + std::max(0.f, clearYd) - d);
        r.source = Advance(p, o, -1.f);
        return r;
    }

    // Unit::KnockbackFrom's horizontal speed for a throw of `distance` yd (distance = 2 x speedXY x speedZ / g).
    inline float PushSpeedXY(float distance, float speedZ = kRingPushSpeedZ)
    {
        return speedZ > 0.f ? distance * kRingGravity / (2.f * speedZ) : 0.f;
    }

    inline std::uint32_t PushFlightMs(float speedZ = kRingPushSpeedZ)
    {
        return speedZ > 0.f ? static_cast<std::uint32_t>(std::lround(2000.f * speedZ / kRingGravity)) : 0u;
    }

    // A unit pushed out holds a grace until its landing: no strike, no crossing.
    class GraceBook
    {
    public:
        void Grant(std::uint64_t id, std::uint64_t untilMs) { _until[id] = std::max(_until[id], untilMs); }

        bool Has(std::uint64_t id, std::uint64_t nowMs) const
        {
            auto it = _until.find(id);
            return it != _until.end() && nowMs < it->second;
        }

        void Prune(std::uint64_t nowMs)
        {
            for (auto it = _until.begin(); it != _until.end();)
            {
                if (nowMs >= it->second)
                    it = _until.erase(it);
                else
                    ++it;
            }
        }

        std::size_t Size() const { return _until.size(); }

    private:
        std::unordered_map<std::uint64_t, std::uint64_t> _until;
    };
}

#endif
