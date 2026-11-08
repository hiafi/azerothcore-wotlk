/*
 * mod-dungeon-bosses, Scholomance S7:
 * Lorekeeper Polkelt (10901), the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S7 owns this file: its spell ids (inside kSpellsPolkelt of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_polkelt_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_POLKELT_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_POLKELT_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoPolkelt
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsPolkelt;

    // TODO(WP-S7): enum PolkeltSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
