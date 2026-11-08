/*
 * mod-dungeon-bosses, Scholomance S11:
 * Darkmaster Gandling, the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S11 owns this file: its spell ids (inside kSpellsGandling of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_gandling_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoGandling
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsGandling;

    // TODO(WP-S11): enum GandlingSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
