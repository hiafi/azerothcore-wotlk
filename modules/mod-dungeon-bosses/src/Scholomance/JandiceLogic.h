/*
 * mod-dungeon-bosses, Scholomance S1:
 * Jandice Barov (10503), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S1 owns this file: its spell ids (inside kSpellsJandice of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_jandice_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_JANDICE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_JANDICE_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoJandice
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsJandice;

    // TODO(WP-S1): enum JandiceSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
