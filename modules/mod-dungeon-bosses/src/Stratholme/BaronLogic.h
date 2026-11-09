/*
 * mod-dungeon-bosses, Stratholme S14:
 * Baron Rivendare (10440), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S14 owns this file: its spell ids (inside kSpellsBaron of StratholmeRework.h,
 * 206705-206719), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_baron_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARON_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARON_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratBaron
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBaron;

    // TODO(WP-S14): enum BaronSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
