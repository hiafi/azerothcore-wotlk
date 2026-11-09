/*
 * mod-dungeon-bosses, Stratholme S15:
 * Baron Rivendare's hard mode, the Ultimatum, the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S15 owns this file: its spell ids (inside kSpellsUltimatum of StratholmeRework.h,
 * 206720-206734), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_ultimatum_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARON_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARON_HARD_MODE_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratUltimatum
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsUltimatum;

    // TODO(WP-S15): enum BaronHardModeSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
