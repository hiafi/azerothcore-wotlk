/*
 * mod-dungeon-bosses, Stratholme S8:
 * Balnazzar's hard mode, the Grand Lie, the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S8 owns this file: its spell ids (inside kSpellsGrandLie of StratholmeRework.h,
 * 206575-206604), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_grand_lie_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_GRAND_LIE_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_GRAND_LIE_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratGrandLie
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsGrandLie;

    // TODO(WP-S8): enum GrandLieSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
