/*
 * mod-dungeon-bosses, Scholomance S6:
 * Doctor Theolen Krastinov (11261), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S6 owns this file: its spell ids (inside kSpellsKrastinov of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_krastinov_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_KRASTINOV_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_KRASTINOV_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoKrastinov
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsKrastinov;

    // TODO(WP-S6): enum KrastinovSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
