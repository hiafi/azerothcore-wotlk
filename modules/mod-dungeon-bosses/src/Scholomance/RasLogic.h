/*
 * mod-dungeon-bosses, Scholomance S4:
 * Ras Frostwhisper (10508), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S4 owns this file: its spell ids (inside kSpellsRas of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_ras_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoRas
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRas;

    // TODO(WP-S4): enum RasSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
