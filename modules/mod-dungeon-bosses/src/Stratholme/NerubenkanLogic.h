/*
 * mod-dungeon-bosses, Stratholme S11:
 * Nerub'enkan (10437), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S11 owns this file: its spell ids (inside kSpellsNerubenkan of StratholmeRework.h,
 * 206645-206664), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_nerubenkan_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_NERUBENKAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_NERUBENKAN_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratNerubenkan
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsNerubenkan;

    // TODO(WP-S11): enum NerubenkanSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
