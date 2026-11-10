/*
 * mod-dungeon-bosses, Stratholme S1:
 * The Unforgiven (10516), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S1 owns this file: its spell ids (inside kSpellsUnforgiven of StratholmeRework.h,
 * 206420-206439), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_unforgiven_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_UNFORGIVEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_UNFORGIVEN_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratUnforgiven
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsUnforgiven;

    // TODO(WP-S1): enum UnforgivenSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
