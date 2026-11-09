/*
 * mod-dungeon-bosses, Stratholme S5:
 * Cannon Master Willey (10997), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S5 owns this file: its spell ids (inside kSpellsWilley of StratholmeRework.h,
 * 206500-206519), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_willey_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_WILLEY_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_WILLEY_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratWilley
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsWilley;

    // TODO(WP-S5): enum WilleySpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
