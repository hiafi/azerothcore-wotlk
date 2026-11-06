/*
 * mod-dungeon-bosses, Deadmines: the shared kit's pure part (no engine headers; host-tested by tests/kit_test.cpp).
 *
 * - NH<T>: one tuning number per difficulty (normal, heroic). Boss WPs keep their own constants in their own
 *   <Boss>Logic.h as `inline constexpr NH<...>` values, so a retune is one line (handoff section 3.2 item 1, 3.6).
 * - RefFlatValue: percent of a reference-health row, rounded and clamped exactly like mod-boss-mechanics'
 *   FlatDamageFor / RefFlatFor (MechanicMath.h), so a script's own spell and a registry mechanic with the same percent
 *   deal the same number.
 * - 2D geometry on the map plane (x north, y west; orientation o points along (cos o, sin o)): point in polygon, the
 *   first wall a ray meets, a lane end clipped to the room. Used with the measured frames in DeadminesRework.h.
 * - Instance save string (Save / FormatSave / ParseSave): backward compatible with the stock instance_deadmines
 *   "D E <rhahkzor> <cannon>" string.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_KIT_MATH_H
#define MOD_DUNGEON_BOSSES_DEADMINES_KIT_MATH_H

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>

namespace DeadminesKit
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
        float constexpr twoPi = 6.28318530717958647692f;
        float o = std::atan2(to.y - from.y, to.x - from.x);
        if (o < 0.f)
            o += twoPi;
        return o;
    }

    // The tank hit of a TankExempt frontal (Sneed's SN2, Mr. Smite's SM2 / SM3): is `target` inside the frontal cone
    // of `angleDeg` and `length` (plus `reach`, the units' combat reach) in front of `source` facing `facing`?
    inline bool InFrontalCone(Vec2 source, float facing, Vec2 target, float angleDeg, float length, float reach = 0.f)
    {
        float constexpr pi = 3.14159265358979323846f;
        float const dist = Distance(source, target);
        if (dist > length + reach)
            return false;
        if (dist < 0.01f)
            return true;
        float diff = BearingTo(source, target) - facing;
        while (diff > pi)
            diff -= 2.f * pi;
        while (diff < -pi)
            diff += 2.f * pi;
        return std::fabs(diff) <= angleDeg * pi / 360.f;
    }

    inline Vec2 Advance(Vec2 from, float orientation, float distance)
    {
        return { from.x + std::cos(orientation) * distance, from.y + std::sin(orientation) * distance };
    }

    // Even-odd rule; a point exactly on an edge may land either way.
    template <std::size_t N>
    bool PointInPolygon(std::array<Vec2, N> const& poly, Vec2 p)
    {
        bool inside = false;
        for (std::size_t i = 0, j = N - 1; i < N; j = i++)
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

    // Axis-aligned box (a hole in a floor polygon, e.g. Gilnid's pot block).
    struct Box2
    {
        float minX = 0.f;
        float maxX = 0.f;
        float minY = 0.f;
        float maxY = 0.f;

        bool Contains(Vec2 p) const { return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY; }
        Vec2 Center() const { return { (minX + maxX) * 0.5f, (minY + maxY) * 0.5f }; }
    };

    // Distance along the ray from `origin` (looking along `orientation`) to the nearest polygon edge it crosses
    // (strictly ahead of the origin); nullopt when it meets none (an origin outside a polygon looking away from it).
    template <std::size_t N>
    std::optional<float> RayToPolygonEdge(std::array<Vec2, N> const& poly, Vec2 origin, float orientation)
    {
        float const dx = std::cos(orientation);
        float const dy = std::sin(orientation);
        std::optional<float> best;
        for (std::size_t i = 0, j = N - 1; i < N; j = i++)
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

    // A lane from `origin` through `through` to the room wall: the end point on the polygon edge, pulled back by
    // `inset` yards so the end stays inside the floor. nullopt when the ray meets no wall.
    template <std::size_t N>
    std::optional<Vec2> LaneEndAtWall(std::array<Vec2, N> const& poly, Vec2 origin, Vec2 through, float inset = 0.5f)
    {
        float const o = BearingTo(origin, through);
        std::optional<float> const hit = RayToPolygonEdge(poly, origin, o);
        if (!hit)
            return std::nullopt;
        return Advance(origin, o, std::max(0.f, *hit - inset));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Instance save string
    // ----------------------------------------------------------------------------------------------------------------

    // EncounterState values (InstanceScript.h); instance_deadmines_rework.cpp static_asserts they match the engine.
    namespace State
    {
        std::uint32_t constexpr NotStarted = 0;
        std::uint32_t constexpr InProgress = 1;
        std::uint32_t constexpr Fail = 2;
        std::uint32_t constexpr Done = 3;
        std::uint32_t constexpr Special = 4;
        std::uint32_t constexpr ToBeDecided = 5;
    }

    // Miner Johnson's spawn roll (handoff section 7 #15): rolled once per instance and saved.
    namespace JohnsonRoll
    {
        std::uint32_t constexpr Unrolled = 0;
        std::uint32_t constexpr Present = 1;
        std::uint32_t constexpr Absent = 2;
        std::uint32_t constexpr PresentChancePct = 40;  // stock SmartAI 3586: 60% despawn on AI init
    }

    // `roll` in [0, 100): Present below PresentChancePct.
    inline std::uint32_t ResolveJohnsonRoll(std::uint32_t roll)
    {
        return roll < JohnsonRoll::PresentChancePct ? JohnsonRoll::Present : JohnsonRoll::Absent;
    }

    std::size_t constexpr kSaveBossCount = 9;   // the instance's SetBossNumber, in DeadminesRework.h order

    struct Save
    {
        std::array<std::uint32_t, kSaveBossCount> bosses{};     // EncounterState per boss state id
        std::uint32_t cannon = State::NotStarted;               // the stock TYPE_CANNON field (Iron Clad Door event)
        std::uint32_t hardMode = 0;                             // DATA_HARD_MODE (1 while lit)
        std::uint32_t johnsonRoll = JohnsonRoll::Unrolled;
    };

    // A stored state that cannot survive a reload goes back to NOT_STARTED (InstanceScript::ReadSaveDataBossStates).
    inline std::uint32_t SanitizeLoadedState(std::uint32_t s)
    {
        if (s == State::InProgress || s == State::Fail || s == State::Special || s >= State::ToBeDecided)
            return State::NotStarted;
        return s;
    }

    // "D E <boss 0> <cannon> <boss 1> .. <boss 8> <hardMode> <johnsonRoll>". The first two numbers are the stock
    // instance_deadmines fields (TYPE_RHAHK_ZOR, TYPE_CANNON), and boss 0 is Rhahk'Zor, so a save written by the stock
    // script reads as Rhahk'Zor and the cannon with everything else unset.
    inline std::string FormatSave(Save const& s)
    {
        std::ostringstream out;
        out << "D E " << s.bosses[0] << ' ' << s.cannon;
        for (std::size_t i = 1; i < kSaveBossCount; ++i)
            out << ' ' << s.bosses[i];
        out << ' ' << s.hardMode << ' ' << s.johnsonRoll;
        return out.str();
    }

    // False on a missing or wrong header or a missing stock field (the save is then ignored, like the stock script).
    // A short tail (a stock save) leaves the rest at its defaults. Loaded states pass SanitizeLoadedState; the stock
    // script also reset an IN_PROGRESS cannon, so the cannon does too. A lit hard mode never survives a reload.
    inline bool ParseSave(std::string const& in, Save& out)
    {
        out = Save{};
        std::istringstream stream(in);
        char h1 = 0;
        char h2 = 0;
        if (!(stream >> h1 >> h2) || h1 != 'D' || h2 != 'E')
            return false;
        std::uint32_t first = 0;
        std::uint32_t cannon = 0;
        if (!(stream >> first >> cannon))
            return false;
        out.bosses[0] = SanitizeLoadedState(first);
        out.cannon = SanitizeLoadedState(cannon);
        for (std::size_t i = 1; i < kSaveBossCount; ++i)
        {
            std::uint32_t v = 0;
            if (!(stream >> v))
                return true;
            out.bosses[i] = SanitizeLoadedState(v);
        }
        std::uint32_t hardMode = 0;
        if (!(stream >> hardMode))
            return true;
        out.hardMode = 0;
        std::uint32_t roll = 0;
        if (!(stream >> roll))
            return true;
        out.johnsonRoll = roll <= JohnsonRoll::Absent ? roll : JohnsonRoll::Unrolled;
        return true;
    }
}

#endif
