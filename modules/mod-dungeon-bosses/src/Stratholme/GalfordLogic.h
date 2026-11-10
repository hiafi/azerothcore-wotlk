/*
 * mod-dungeon-bosses, Stratholme S6:
 * Archivist Galford (10811), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-S6 owns this file: its spell ids (inside kSpellsGalford of StratholmeRework.h,
 * 206520-206544), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers,
 * picks and geometry, tested by tests/strat_galford_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_GALFORD_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_GALFORD_LOGIC_H

#include "StratholmeRework.h"
#include <cstdint>

namespace StratGalford
{
    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsGalford;

    // TODO(WP-S6): enum GalfordSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
