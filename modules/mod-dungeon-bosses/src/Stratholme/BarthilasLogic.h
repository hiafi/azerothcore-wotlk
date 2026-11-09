/*
 * mod-dungeon-bosses, Stratholme S9:
 * Magistrate Barthilas (10435), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S9 owns this file: its spell ids (inside kSpellsBarthilas of StratholmeRework.h,
 * 206605-206624), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_barthilas_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARTHILAS_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARTHILAS_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratBarthilas
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBarthilas;

    // TODO(WP-S9): enum BarthilasSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
