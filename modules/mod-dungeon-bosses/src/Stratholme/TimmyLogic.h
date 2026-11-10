/*
 * mod-dungeon-bosses, Stratholme S3:
 * Timmy the Cruel (10808), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S3 owns this file: its spell ids (inside kSpellsTimmy of StratholmeRework.h,
 * 206460-206479), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_timmy_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_TIMMY_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_TIMMY_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratTimmy
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsTimmy;

    // TODO(WP-S3): enum TimmySpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
