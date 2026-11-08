/*
 * mod-dungeon-bosses, Scholomance S8:
 * The Ravenian (10507) and Master Corvane, the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S8 owns this file: its spell ids (inside kSpellsRavenian of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_ravenian_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAVENIAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAVENIAN_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoRavenian
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRavenian;

    // TODO(WP-S8): enum RavenianSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
