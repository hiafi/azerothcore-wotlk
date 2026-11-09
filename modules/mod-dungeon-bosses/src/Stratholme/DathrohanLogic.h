/*
 * mod-dungeon-bosses, Stratholme S7:
 * Grand Crusader Dathrohan and Balnazzar (10812), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S7 owns this file: its spell ids (inside kSpellsDathrohan of StratholmeRework.h,
 * 206545-206574), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_dathrohan_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratDathrohan
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsDathrohan;

    // TODO(WP-S7): enum DathrohanSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
