/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Depths WP-KT-D1, handoff section 3.11 #1): pure rules for
 * death spots and held bodies. No engine headers; host-tested by tests/dungeon_kit_test.cpp. The engine half is
 * DungeonKitBodies.h (DeathSpots, HeldBody).
 *
 *   DeathSpot       where a unit died: its id, entry, position, time and a caller tag; `used` once raised
 *   DeathSpotBook   the spots one fight stored: Record (a unit dying again replaces its spot), Find, Nearest, Take
 *                   (oldest first or by a random pick, marked used: Raise Dead), a cap (the oldest go first), Clear
 *   BodyState       Up, Fallen (held at 1 health as a body), Dead
 *   HeldBodyLatch   the held body's state: a lethal hit while Up and holds left makes it Fallen (clamped to 1 health);
 *                   every hit while Fallen is absorbed; Revive (back Up), Finish (the real death follows), an optional
 *                   hold limit (Update says when it ran out), Reset for the next pull
 *   AllDown         every member of a team is Fallen or Dead (the Encore ends: finish the held bodies)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_BODY_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_BODY_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Death spots
    // ----------------------------------------------------------------------------------------------------------------

    std::size_t constexpr kDeathSpotCap = 32;   // a fight's worth (a Ring of Law wave is at most 6 beasts)

    struct DeathSpot
    {
        std::uint64_t id = 0;           // the dead unit's raw guid
        std::uint32_t entry = 0;        // its creature entry (0: a player)
        Vec2 at;
        float z = 0.f;
        float o = 0.f;
        std::uint64_t atMs = 0;         // the caller's clock at the death
        std::uint32_t tag = 0;          // the caller's own kind (a wave, a member)
        bool used = false;              // raised, burst or otherwise spent
    };

    // Which spots a query takes: `entry` / `tag` 0 match any; `unusedOnly` skips spent spots.
    struct DeathSpotFilter
    {
        std::uint32_t entry = 0;
        std::uint32_t tag = 0;
        bool unusedOnly = true;

        bool Matches(DeathSpot const& s) const
        {
            return (!entry || s.entry == entry) && (!tag || s.tag == tag) && (!unusedOnly || !s.used);
        }
    };

    class DeathSpotBook
    {
    public:
        explicit DeathSpotBook(std::size_t cap = kDeathSpotCap) : _cap(std::max<std::size_t>(1, cap)) { }

        // Stores a death. The same id again replaces its old spot (a revived unit that dies again); past the cap the
        // oldest spot is dropped. Returns the stored spot.
        DeathSpot const& Record(DeathSpot spot)
        {
            spot.used = false;
            auto it = std::find_if(_spots.begin(), _spots.end(), [&spot](DeathSpot const& s)
            {
                return s.id == spot.id;
            });
            if (it != _spots.end())
                _spots.erase(it);
            if (_spots.size() >= _cap)
                _spots.erase(_spots.begin());       // kept in death order: the front is the oldest
            _spots.push_back(spot);
            return _spots.back();
        }

        std::optional<DeathSpot> Find(std::uint64_t id) const
        {
            for (DeathSpot const& s : _spots)
                if (s.id == id)
                    return s;
            return std::nullopt;
        }

        // The matching spot nearest `p` within `maxYd` (2D; maxYd <= 0: any distance).
        std::optional<DeathSpot> Nearest(Vec2 p, float maxYd = 0.f, DeathSpotFilter const& filter = {}) const
        {
            std::optional<DeathSpot> best;
            float bestDist = 0.f;
            for (DeathSpot const& s : _spots)
            {
                if (!filter.Matches(s))
                    continue;
                float const d = Distance(p, s.at);
                if (maxYd > 0.f && d > maxYd)
                    continue;
                if (!best || d < bestDist)
                {
                    best = s;
                    bestDist = d;
                }
            }
            return best;
        }

        std::size_t Count(DeathSpotFilter const& filter = { 0, 0, false }) const
        {
            return static_cast<std::size_t>(std::count_if(_spots.begin(), _spots.end(), [&filter](DeathSpot const& s)
            {
                return filter.Matches(s);
            }));
        }

        // Up to `n` matching spots, oldest death first, each marked used.
        std::vector<DeathSpot> TakeOldest(std::size_t n, DeathSpotFilter const& filter = {})
        {
            std::vector<DeathSpot> out;
            for (DeathSpot& s : _spots)
            {
                if (out.size() >= n)
                    break;
                if (!filter.Matches(s))
                    continue;
                s.used = true;
                out.push_back(s);
            }
            return out;
        }

        // Up to `n` distinct matching spots picked by `rand(k)` (an index in [0, k), urand's role), each marked used.
        template <class Rand>
        std::vector<DeathSpot> TakeRandom(std::size_t n, Rand&& rand, DeathSpotFilter const& filter = {})
        {
            std::vector<DeathSpot> out;
            while (out.size() < n)
            {
                std::vector<std::size_t> pool;
                for (std::size_t i = 0; i < _spots.size(); ++i)
                    if (filter.Matches(_spots[i]) && !_spots[i].used)
                        pool.push_back(i);
                if (pool.empty())
                    break;
                std::size_t const k = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())));
                DeathSpot& s = _spots[pool[std::min(k, pool.size() - 1)]];
                s.used = true;
                out.push_back(s);
            }
            return out;
        }

        // Marks one spot used (or unused again). False when the id has no spot.
        bool Mark(std::uint64_t id, bool used = true)
        {
            for (DeathSpot& s : _spots)
                if (s.id == id)
                {
                    s.used = used;
                    return true;
                }
            return false;
        }

        bool Forget(std::uint64_t id)
        {
            auto it = std::find_if(_spots.begin(), _spots.end(), [id](DeathSpot const& s) { return s.id == id; });
            if (it == _spots.end())
                return false;
            _spots.erase(it);
            return true;
        }

        // Drops spots older than `maxAgeMs` at `nowMs`.
        void Expire(std::uint64_t nowMs, std::uint64_t maxAgeMs)
        {
            _spots.erase(std::remove_if(_spots.begin(), _spots.end(), [nowMs, maxAgeMs](DeathSpot const& s)
            {
                return nowMs >= s.atMs + maxAgeMs;
            }), _spots.end());
        }

        void Clear() { _spots.clear(); }
        std::size_t Size() const { return _spots.size(); }
        std::span<DeathSpot const> All() const { return _spots; }

    private:
        std::size_t _cap;
        std::vector<DeathSpot> _spots;      // death order
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Held bodies
    // ----------------------------------------------------------------------------------------------------------------

    enum class BodyState : std::uint8_t
    {
        Up,         // standing and fighting
        Fallen,     // held at 1 health as a body: untargetable by attacks, every hit absorbed
        Dead        // Finish was called (or a lethal hit with no hold left went through)
    };

    // `holds`: how many lethal hits are held as a fall (Korv's Ancestral Spirit: 1, a revived member dies for real;
    // Acid Burst's swell: 1 with a 2 s hold limit). `holdLimitMs`: a fall ends by itself after this long (0: only by
    // Revive or Finish).
    class HeldBodyLatch
    {
    public:
        struct Result
        {
            bool clamped = false;           // the damage was cut (to 1 health, or to 0 while Fallen)
            bool fell = false;              // this hit made it Fallen: run the fall (onFall)
            std::uint32_t damage = 0;       // the damage to deal
        };

        explicit HeldBodyLatch(std::uint8_t holds = 1, std::uint32_t holdLimitMs = 0)
            : _holds(holds), _holdLimitMs(holdLimitMs)
        {
        }

        Result Apply(std::uint32_t health, std::uint32_t damage)
        {
            if (_state == BodyState::Fallen)
                return { damage > 0, false, 0 };
            if (_state == BodyState::Dead || damage < health)
                return { false, false, damage };
            if (_falls >= _holds)
            {
                // No hold left: the hit goes through and kills (R-1-FW MIN-4: State() reads Dead from here on, so a
                // caller of AllDown on raw latch states sees the team down).
                if (health > 0)
                    _state = BodyState::Dead;
                return { false, false, damage };
            }
            _state = BodyState::Fallen;
            ++_falls;
            _fallenMs = 0;
            return { true, true, ClampLethal(health, damage) };
        }

        // Back Up from Fallen. False in any other state.
        bool Revive()
        {
            if (_state != BodyState::Fallen)
                return false;
            _state = BodyState::Up;
            ++_revives;
            _fallenMs = 0;
            return true;
        }

        // Fallen (or Up) -> Dead: the engine kills it next. False when already Dead.
        bool Finish()
        {
            if (_state == BodyState::Dead)
                return false;
            _state = BodyState::Dead;
            return true;
        }

        // Time while Fallen; true once (the update that crosses the hold limit): Finish it now.
        bool Update(std::uint32_t diffMs)
        {
            if (_state != BodyState::Fallen || !_holdLimitMs)
                return false;
            bool const before = _fallenMs < _holdLimitMs;
            _fallenMs += diffMs;
            return before && _fallenMs >= _holdLimitMs;
        }

        // The next pull: Up, no falls, no revives.
        void Reset()
        {
            _state = BodyState::Up;
            _falls = 0;
            _revives = 0;
            _fallenMs = 0;
        }

        BodyState State() const { return _state; }
        bool Fallen() const { return _state == BodyState::Fallen; }
        std::uint8_t Falls() const { return _falls; }
        std::uint8_t Revives() const { return _revives; }
        std::uint32_t FallenMs() const { return _fallenMs; }
        // A lethal hit now would be held.
        bool HoldsLeft() const { return _state == BodyState::Up && _falls < _holds; }

    private:
        std::uint8_t _holds;
        std::uint32_t _holdLimitMs;
        BodyState _state = BodyState::Up;
        std::uint8_t _falls = 0;
        std::uint8_t _revives = 0;
        std::uint32_t _fallenMs = 0;
    };

    // Every member is Fallen or Dead (an empty team is not down).
    inline bool AllDown(std::span<BodyState const> team)
    {
        return !team.empty() && std::all_of(team.begin(), team.end(), [](BodyState s) { return s != BodyState::Up; });
    }
}

#endif
