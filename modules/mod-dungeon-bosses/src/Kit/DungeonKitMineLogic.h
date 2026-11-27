/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff section 3.11, F42; SP MT5): pure rules for
 * two-ring mines, a small ring that sets the mine off and a larger ring the blast hits. No engine headers;
 * host-tested by tests/kit_mines_test.cpp. The engine half is DungeonKitMines.h (TwoRingMines).
 *
 *   MineRings    the trigger and blast radii (blast >= trigger)
 *   InBlast      is a point inside a blast ring (2D radius, a height band)
 *   MineBook     the field's clocks: each mine's arm time and life, which are armed, which ran out, and which a
 *                detonator sets off (armed only, or every one)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MINE_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_MINE_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace DungeonKit
{
    struct MineRings
    {
        float triggerYd = 3.f;      // a player inside for the grace sets it off (the registry's mine)
        float blastYd = 6.f;        // the blast hits every player inside (the script's hit)

        bool Valid() const { return triggerYd > 0.f && blastYd >= triggerYd; }
    };

    // Inside the blast: within `blastYd` on the map plane and `zBand` above or below the mine. Edges count.
    inline bool InBlast(Vec2 mine, float mineZ, Vec2 p, float pZ, float blastYd, float zBand)
    {
        return Distance(mine, p) <= blastYd + 1e-3f && std::fabs(pZ - mineZ) <= zBand;
    }

    // The clocks of a field of mines. Times are one clock's milliseconds (the owner's fight time).
    class MineBook
    {
    public:
        // lifeMs 0: until removed. A mine already in the book is replaced.
        void Add(std::uint32_t id, std::uint32_t nowMs, std::uint32_t armMs, std::uint32_t lifeMs)
        {
            Remove(id);
            _mines.push_back({ id, nowMs + armMs, lifeMs ? nowMs + lifeMs : 0 });
        }

        bool Remove(std::uint32_t id)
        {
            auto it = std::find_if(_mines.begin(), _mines.end(), [id](Mine const& m) { return m.id == id; });
            if (it == _mines.end())
                return false;
            _mines.erase(it);
            return true;
        }

        bool Has(std::uint32_t id) const
        {
            return std::any_of(_mines.begin(), _mines.end(), [id](Mine const& m) { return m.id == id; });
        }

        bool Armed(std::uint32_t id, std::uint32_t nowMs) const
        {
            for (Mine const& m : _mines)
                if (m.id == id)
                    return nowMs >= m.armAt;
            return false;
        }

        // The mines whose life has run out by `nowMs` (oldest first).
        std::vector<std::uint32_t> Expired(std::uint32_t nowMs) const
        {
            std::vector<std::uint32_t> out;
            for (Mine const& m : _mines)
                if (m.endAt && nowMs >= m.endAt)
                    out.push_back(m.id);
            return out;
        }

        // What a detonator sets off now: the armed mines, or every one (armedOnly false). Oldest first.
        std::vector<std::uint32_t> Detonations(std::uint32_t nowMs, bool armedOnly) const
        {
            std::vector<std::uint32_t> out;
            for (Mine const& m : _mines)
                if (!armedOnly || nowMs >= m.armAt)
                    out.push_back(m.id);
            return out;
        }

        std::vector<std::uint32_t> Ids() const
        {
            std::vector<std::uint32_t> out;
            out.reserve(_mines.size());
            for (Mine const& m : _mines)
                out.push_back(m.id);
            return out;
        }

        std::size_t ArmedCount(std::uint32_t nowMs) const
        {
            return static_cast<std::size_t>(std::count_if(_mines.begin(), _mines.end(),
                [nowMs](Mine const& m) { return nowMs >= m.armAt; }));
        }

        std::size_t Count() const { return _mines.size(); }
        void Clear() { _mines.clear(); }

    private:
        struct Mine
        {
            std::uint32_t id = 0;
            std::uint32_t armAt = 0;
            std::uint32_t endAt = 0;    // 0: no life
        };

        std::vector<Mine> _mines;
    };
}

#endif
