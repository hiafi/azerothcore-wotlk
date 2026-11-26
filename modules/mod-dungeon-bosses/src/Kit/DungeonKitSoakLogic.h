/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F36): pure rules for a Soak that
 * must be held (Ukorz's rescue of a sunk player: someone stands within 3 yd of him for 2 s). No engine headers;
 * host-tested by tests/kit_soak_test.cpp. The engine half is DungeonKitSoaks.h (DwellSoaks).
 *
 *   SoakAt          one held Soak's clock: the first eligible player inside for `dwellMs` without a break takes it
 *                   (DwellTracker, the pickups' rule); it expires after `lifeMs` (0: never) when nobody did
 *   SoakAtTakers    who may count inside a held Soak: the players there minus the excluded ones (the anchors, the sunk)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAK_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_SOAK_LOGIC_H

#include "DungeonKitLogic.h"
#include <algorithm>
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
}

#endif
