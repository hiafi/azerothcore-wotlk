/*
 * mod-dungeon-bosses, Scholomance S2:
 * Rattlegore (11622), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S2 owns this file: its spell ids (inside kSpellsRattlegore of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_rattlegore_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RATTLEGORE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RATTLEGORE_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoRattlegore
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRattlegore;

    // TODO(WP-S2): enum RattlegoreSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
