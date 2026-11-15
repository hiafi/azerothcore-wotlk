/*
 * mod-dungeon-bosses, Blackrock Spire B14:
 * General Drakkisath (10363), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B14 owns this file: its spell ids (inside kSpellsDrakkisath of
 * BlackrockSpireRework.h, 210520-210559), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_drakkisath_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsDrakkisath
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsDrakkisath;

    // TODO(WP-B14): enum DrakkisathSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
