/*
 * mod-dungeon-bosses, Scholomance S10:
 * Lady Illucia Barov (10502), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S10 owns this file: its spell ids (inside kSpellsIllucia of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_illucia_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_ILLUCIA_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_ILLUCIA_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoIllucia
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsIllucia;

    // TODO(WP-S10): enum IlluciaSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
