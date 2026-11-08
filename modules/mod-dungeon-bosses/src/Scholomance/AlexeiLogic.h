/*
 * mod-dungeon-bosses, Scholomance S9:
 * Lord Alexei Barov (10504), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S9 owns this file: its spell ids (inside kSpellsAlexei of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_alexei_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_ALEXEI_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_ALEXEI_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoAlexei
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsAlexei;

    // TODO(WP-S9): enum AlexeiSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
