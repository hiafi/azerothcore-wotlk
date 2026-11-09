/*
 * mod-dungeon-bosses, Stratholme S10:
 * Baroness Anastari (10436), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S10 owns this file: its spell ids (inside kSpellsBaroness of StratholmeRework.h,
 * 206625-206644), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_baroness_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARONESS_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARONESS_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratBaroness
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsBaroness;

    // TODO(WP-S10): enum BaronessSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
