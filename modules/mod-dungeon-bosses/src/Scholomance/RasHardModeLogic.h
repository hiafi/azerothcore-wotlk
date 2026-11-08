/*
 * mod-dungeon-bosses, Scholomance S12:
 * Ras Frostwhisper's hard mode, the Torn Keepsake, the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S12 owns this file: its spell ids (inside kSpellsRasHardMode of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_keepsake_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_HARD_MODE_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoRasHardMode
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRasHardMode;

    // TODO(WP-S12): enum RasHardModeSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
