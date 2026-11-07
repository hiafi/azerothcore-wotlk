/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): pure rules behind the engine helpers of DungeonKit.h (no engine
 * headers; host-tested by tests/dungeon_kit_test.cpp).
 *
 *   SplitDamage        a shared hit split among the players inside, capped per player (Mark the Prey, Group Exercise)
 *   PickFrom           one random (or the farthest) candidate with the common filters (PickPlayer's rule)
 *   SpeedFor           a run-speed rate from a percent of a player's run speed (7 yd/s)
 *   ClampStacks        a stacking meter's new count after +/- delta, clamped to [0, max]
 *   StackCap           AddStacks' cap: the caller's max, else the spell's own StackAmount
 *   ClampLethal        the damage that leaves a unit at 1 health (InterceptLethal)
 *   LethalLatch        LethalGuard's state: armed / fired, Reset for the next pull
 *   QuietTimer         time in combat with no hit taken (BreakableDoorAI's evade path)
 *   InPickupRange      a pickup's reach: 2D radius plus a z band
 *   LineStrikePath     a line from the source through the target, `overrun` past it, clipped to the arena walls
 *   DwellTracker       who has stood in a pickup for how long (Pickups: the first eligible player inside for `dwell`)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Split damage
    // ----------------------------------------------------------------------------------------------------------------

    // `total` split evenly among `count` players (the remainder goes one point each to the first shares, so the shares
    // add up to `total`), each share capped at `capEach` (0 = no cap). Empty for count 0.
    inline std::vector<std::uint32_t> SplitDamage(std::uint32_t total, std::uint32_t count, std::uint32_t capEach)
    {
        std::vector<std::uint32_t> shares;
        if (!count)
            return shares;
        std::uint32_t const base = total / count;
        std::uint32_t const rest = total % count;
        shares.reserve(count);
        for (std::uint32_t i = 0; i < count; ++i)
        {
            std::uint32_t share = base + (i < rest ? 1 : 0);
            if (capEach && share > capEach)
                share = capEach;
            shares.push_back(share);
        }
        return shares;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Target picks
    // ----------------------------------------------------------------------------------------------------------------

    struct PickCandidate
    {
        std::uint64_t id = 0;       // raw guid
        float distance = 0.f;       // from the picker
        bool tank = false;          // the picker's current victim
        bool inLos = true;
    };

    struct PickRule
    {
        bool nonTank = true;        // never the tank (unless nobody else qualifies and `tankIfAlone`)
        bool tankIfAlone = false;   // a solo tank (or a tank-only group) may still be picked
        float minRange = 0.f;
        float maxRange = 100.f;
        bool requireLos = false;
        bool farthest = false;      // the farthest qualifying candidate instead of a random one
        std::vector<std::uint64_t> exclude;
    };

    // The index of the picked candidate, nullopt when none qualifies. `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickFrom(std::vector<PickCandidate> const& candidates, PickRule const& rule, Rand&& rand)
    {
        auto qualifies = [&rule](PickCandidate const& c, bool allowTank)
        {
            if (c.tank && rule.nonTank && !allowTank)
                return false;
            if (c.distance < rule.minRange || c.distance > rule.maxRange)
                return false;
            if (rule.requireLos && !c.inLos)
                return false;
            return std::find(rule.exclude.begin(), rule.exclude.end(), c.id) == rule.exclude.end();
        };
        for (bool const allowTank : { false, true })
        {
            if (allowTank && !(rule.nonTank && rule.tankIfAlone))
                break;
            std::vector<std::size_t> pool;
            for (std::size_t i = 0; i < candidates.size(); ++i)
                if (qualifies(candidates[i], allowTank))
                    pool.push_back(i);
            if (pool.empty())
                continue;
            if (rule.farthest)
                return *std::max_element(pool.begin(), pool.end(), [&candidates](std::size_t a, std::size_t b)
                {
                    return candidates[a].distance < candidates[b].distance;
                });
            std::size_t const n = pool.size();
            return pool[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(n))) % n];
        }
        return std::nullopt;
    }

    // Up to `count` distinct picks (PickFrom repeated, each pick excluded from the next).
    template <class Rand>
    std::vector<std::size_t> PickDistinctFrom(std::vector<PickCandidate> const& candidates, PickRule rule,
        std::uint32_t count, Rand&& rand)
    {
        std::vector<std::size_t> out;
        while (out.size() < count)
        {
            std::optional<std::size_t> const pick = PickFrom(candidates, rule, rand);
            if (!pick)
                break;
            out.push_back(*pick);
            rule.exclude.push_back(candidates[*pick].id);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Speed, stacks, lethal damage
    // ----------------------------------------------------------------------------------------------------------------

    // A player runs 7 yd/s; a creature's MOVE_RUN rate 1.0 is the same 7 yd/s (baseMoveSpeed). SpeedFor(80) = 0.8.
    float constexpr kPlayerRunYdPerSec = 7.f;

    constexpr float SpeedFor(float pctOfPlayerRun)
    {
        return pctOfPlayerRun > 0.f ? pctOfPlayerRun / 100.f : 0.f;
    }

    // The stack count after adding `delta` (negative removes) to `current`, clamped to [0, max] (max 0 = no cap).
    constexpr std::uint32_t ClampStacks(std::uint32_t current, std::int32_t delta, std::uint32_t max)
    {
        std::int64_t v = static_cast<std::int64_t>(current) + delta;
        if (v < 0)
            v = 0;
        if (max && v > static_cast<std::int64_t>(max))
            v = max;
        return static_cast<std::uint32_t>(v);
    }

    // AddStacks' cap: `max` when given, else the spell's own StackAmount (0 there too: no cap).
    constexpr std::uint32_t StackCap(std::uint32_t max, std::uint32_t spellStackAmount)
    {
        return max ? max : spellStackAmount;
    }

    // The damage a unit at `health` may take and keep 1 health: `damage` itself when it is not lethal.
    constexpr std::uint32_t ClampLethal(std::uint32_t health, std::uint32_t damage)
    {
        if (damage < health)
            return damage;
        return health > 1 ? health - 1 : 0;
    }

    // LethalGuard's state (DungeonKit.h). Armed: every lethal hit is clamped to leave 1 health; the first one after
    // Arm / Reset also fires (the phase change). It stays armed after firing (every later lethal hit is still clamped)
    // until Disarm. Reset re-arms and clears `fired`: call it from the boss's Reset, or a wipe leaves him unkillable.
    class LethalLatch
    {
    public:
        struct Result
        {
            bool clamped = false;
            bool fire = false;              // the first lethal hit since Arm / Reset: call onZero
            std::uint32_t damage = 0;       // the damage to deal
        };

        void Arm()
        {
            _armed = true;
            _fired = false;
        }

        void Reset() { Arm(); }
        void Disarm() { _armed = false; }
        bool Armed() const { return _armed; }
        bool Fired() const { return _fired; }

        Result Apply(std::uint32_t health, std::uint32_t damage)
        {
            if (!_armed || damage < health)
                return { false, false, damage };
            bool const fire = !_fired;
            _fired = true;
            return { true, fire, ClampLethal(health, damage) };
        }

    private:
        bool _armed = true;
        bool _fired = false;
    };

    // Time in combat without taking a hit: true once `quietMs` passed since the last Hit (or since combat began).
    // Out of combat it rests at 0.
    class QuietTimer
    {
    public:
        explicit QuietTimer(std::uint32_t quietMs = 10000) : _quietMs(quietMs) { }

        void Hit() { _ms = 0; }

        bool Update(bool inCombat, std::uint32_t diff)
        {
            if (!inCombat)
            {
                _ms = 0;
                return false;
            }
            _ms += diff;
            return _ms >= _quietMs;
        }

        void Reset() { _ms = 0; }

    private:
        std::uint32_t _quietMs;
        std::uint32_t _ms = 0;
    };

    // A pickup's reach: within `radius` on the plane and `zBand` yd above or below the spot.
    constexpr bool InPickupRange(float dist2d, float dz, float radius, float zBand)
    {
        return dist2d <= radius && (dz < 0.f ? -dz : dz) <= zBand;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Line strikes (L4)
    // ----------------------------------------------------------------------------------------------------------------

    struct LinePath
    {
        Vec2 from;
        Vec2 end;
        float facing = 0.f;
        float length = 0.f;
        bool clipped = false;       // the wall stopped it short of target + overrun
    };

    // From `from` through `target`, `overrun` yd past it; when `arena` is given and holds `from` at height `z`, the
    // line stops `inset` yd short of the wall it meets first. A target on top of the source keeps `facing`.
    inline LinePath LineStrikePath(Vec2 from, Vec2 target, float overrun, float fallbackFacing = 0.f,
        Arena const* arena = nullptr, float z = 0.f, float inset = 0.5f)
    {
        LinePath path;
        path.from = from;
        float const dist = Distance(from, target);
        path.facing = dist > 0.01f ? BearingTo(from, target) : fallbackFacing;
        path.length = std::max(0.f, dist + overrun);
        if (arena)
            if (std::optional<float> const wall = arena->RayToEdge(from, z, path.facing))
            {
                float const limit = std::max(0.f, *wall - inset);
                if (limit < path.length)
                {
                    path.length = limit;
                    path.clipped = true;
                }
            }
        path.end = Advance(from, path.facing, path.length);
        return path;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Pickups
    // ----------------------------------------------------------------------------------------------------------------

    // Who has stood inside one pickup for how long, without a break. Feed every eligible player each poll; the first to
    // reach `dwellMs` takes it.
    class DwellTracker
    {
    public:
        explicit DwellTracker(std::uint32_t dwellMs = 0) : _dwellMs(dwellMs) { }

        // `ids` are the eligible players inside now. Returns the one who takes it this poll (0: nobody). With dwell 0
        // the first id inside takes it at once.
        std::uint64_t Update(std::vector<std::uint64_t> const& ids, std::uint32_t diffMs)
        {
            std::vector<std::pair<std::uint64_t, std::uint32_t>> next;
            std::uint64_t taker = 0;
            std::uint32_t best = 0;
            for (std::uint64_t const id : ids)
            {
                std::uint32_t ms = diffMs;
                for (auto const& [prev, prevMs] : _inside)
                    if (prev == id)
                        ms = prevMs + diffMs;
                if (!_dwellMs)
                    ms = 0;
                next.emplace_back(id, ms);
                if (ms >= _dwellMs && (!taker || ms > best))
                {
                    taker = id;
                    best = ms;
                }
            }
            _inside = std::move(next);
            return taker;
        }

        void Clear() { _inside.clear(); }

    private:
        std::uint32_t _dwellMs;
        std::vector<std::pair<std::uint64_t, std::uint32_t>> _inside;
    };
}

#endif
