/*
 * mod-dungeon-bosses, Stratholme S13:
 * Ramstein the Gorger (10439), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S13 owns this file: its spell ids (inside kSpellsRamstein of StratholmeRework.h,
 * 206685-206704), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_ramstein_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_RAMSTEIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_RAMSTEIN_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratRamstein
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsRamstein;

    // TODO(WP-S13): enum RamsteinSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
