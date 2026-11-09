/*
 * mod-dungeon-bosses, Stratholme S2:
 * Hearthsinger Forresten (10558), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S2 owns this file: its spell ids (inside kSpellsForresten of StratholmeRework.h,
 * 206440-206459), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_forresten_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_FORRESTEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_FORRESTEN_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratForresten
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsForresten;

    // TODO(WP-S2): enum ForrestenSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
