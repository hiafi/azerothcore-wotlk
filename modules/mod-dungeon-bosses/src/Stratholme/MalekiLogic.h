/*
 * mod-dungeon-bosses, Stratholme S12:
 * Maleki the Pallid (10438), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S12 owns this file: its spell ids (inside kSpellsMaleki of StratholmeRework.h,
 * 206665-206684), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_maleki_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_MALEKI_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_MALEKI_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratMaleki
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsMaleki;

    // TODO(WP-S12): enum MalekiSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
