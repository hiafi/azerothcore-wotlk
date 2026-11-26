/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F36): pure rules for a Soak that
 * must be held (Ukorz's rescue of a sunk player: someone stands within 3 yd of him for 2 s). No engine headers;
 * host-tested by tests/kit_soak_test.cpp. The engine half is DungeonKitSoaks.h (DwellSoaks).
 *
 *   SoakAt          one held Soak's clock: the first eligible player inside for `dwellMs` without a break takes it
 *                   (DwellTracker, the pickups' rule); it expires after `lifeMs` (0: never) when nobody did
 *   SoakAtTakers    who may count inside a held Soak: the players there minus the excluded ones (the anchors, the sunk)
 *   SoakRankAt, SoakPriorityOrder   the rank order of held Soaks (Gnomeregan WP-KT-G, F40: Thermaplugg's plates by
 *                   face priority). The registry serves an exclusive group earliest resolve first, then the lowest id,
 *                   so a ranked set is registered in rank order, and whenever one entry registers anew every entry
 *                   ranked after it does too
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAK_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAK_LOGIC_H

#include "DungeonKitLogic.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace DungeonKit
{
    enum class SoakAtStep : std::uint8_t
    {
        Wait,       // nobody has held it long enough yet
        Done,       // `taker` held it for the dwell
        Expire      // its life ran out first
    };

    struct SoakAtResult
    {
        SoakAtStep step = SoakAtStep::Wait;
        std::uint64_t taker = 0;
    };

    // Feed it the eligible players inside each poll (SoakAtTakers). A player's time counts from the poll that first
    // sees them inside (that poll's whole interval counts, as for the pickups); a poll without them starts them over.
    // A taker who completes the dwell on the poll the life runs out still takes it (the rescue at the buzzer). Once
    // Done or Expire it answers the same from then on.
    class SoakAt
    {
    public:
        SoakAt() = default;
        SoakAt(std::uint32_t dwellMs, std::uint32_t lifeMs) : _dwell(dwellMs), _lifeMs(lifeMs) { }

        SoakAtResult Update(std::vector<std::uint64_t> const& inside, std::uint32_t diffMs)
        {
            if (_over)
                return _last;
            _ageMs += diffMs;
            if (std::uint64_t const taker = _dwell.Update(inside, diffMs))
                return Finish({ SoakAtStep::Done, taker });
            if (_lifeMs && _ageMs >= _lifeMs)
                return Finish({ SoakAtStep::Expire, 0 });
            return {};
        }

        std::uint32_t AgeMs() const { return _ageMs; }
        // Milliseconds of life left (0 with no life, or once it is over).
        std::uint32_t LeftMs() const { return _lifeMs && !_over && _ageMs < _lifeMs ? _lifeMs - _ageMs : 0; }
        bool Over() const { return _over; }

    private:
        SoakAtResult Finish(SoakAtResult r)
        {
            _over = true;
            _last = r;
            return r;
        }

        DwellTracker _dwell{ 2000 };
        std::uint32_t _lifeMs = 0;
        std::uint32_t _ageMs = 0;
        bool _over = false;
        SoakAtResult _last;
    };

    // `present` minus every id in `excluded`, in `present`'s order.
    inline std::vector<std::uint64_t> SoakAtTakers(std::vector<std::uint64_t> const& present,
        std::vector<std::uint64_t> const& excluded)
    {
        std::vector<std::uint64_t> out;
        out.reserve(present.size());
        for (std::uint64_t const id : present)
            if (std::find(excluded.begin(), excluded.end(), id) == excluded.end())
                out.push_back(id);
        return out;
    }

    // Where an entry of `rank` goes among `ranks` (kept in order, lowest first): after every entry of the same or a
    // lower rank (equal ranks keep the order they came in).
    inline std::size_t SoakRankAt(std::vector<std::int32_t> const& ranks, std::int32_t rank)
    {
        return static_cast<std::size_t>(std::upper_bound(ranks.begin(), ranks.end(), rank) - ranks.begin());
    }

    // Which held Soaks register anew this pass. `changed[i]`: entry i's carriers set changed; `from`: an entry that
    // must register (a new or moved one; changed.size() for none). Unranked: the changed ones and `from`. Ranked: every
    // entry from the first of those on, so their registry ids follow the rank order.
    inline std::vector<bool> SoakRegisterMask(bool ranked, std::size_t from, std::vector<bool> const& changed)
    {
        std::vector<bool> out(changed.size(), false);
        std::size_t first = std::min(from, changed.size());
        for (std::size_t i = 0; i < changed.size(); ++i)
            if (changed[i])
                first = std::min(first, i);
        for (std::size_t i = 0; i < changed.size(); ++i)
            out[i] = ranked ? i >= first : (i == from || changed[i]);
        return out;
    }

    // `current` reordered: the ids of `order` first, in that order (ids not in `current` and repeats skipped), then
    // the rest of `current` in its own order.
    inline std::vector<std::uint32_t> SoakPriorityOrder(std::vector<std::uint32_t> const& current,
        std::vector<std::uint32_t> const& order)
    {
        std::vector<std::uint32_t> out;
        out.reserve(current.size());
        for (std::uint32_t const id : order)
            if (std::find(current.begin(), current.end(), id) != current.end()
                && std::find(out.begin(), out.end(), id) == out.end())
                out.push_back(id);
        for (std::uint32_t const id : current)
            if (std::find(out.begin(), out.end(), id) == out.end())
                out.push_back(id);
        return out;
    }
}

#endif
