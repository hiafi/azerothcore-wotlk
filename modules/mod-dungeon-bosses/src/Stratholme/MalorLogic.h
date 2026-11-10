/*
 * mod-dungeon-bosses, Stratholme S4:
 * Malor the Zealous (11032), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S4 owns this file: its spell ids (inside kSpellsMalor of StratholmeRework.h,
 * 206480-206499), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_malor_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_MALOR_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_MALOR_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratMalor
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsMalor;

    // TODO(WP-S4): enum MalorSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
