/*
 * mod-dungeon-bosses, Blackrock Spire B15:
 * General Drakkisath's hard mode, the General's Army, the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B15 owns this file: its spell ids (inside kSpellsGeneralsArmy of
 * BlackrockSpireRework.h, 210560-210619), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_drakkisath_hard_mode_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_DRAKKISATH_HARD_MODE_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsGeneralsArmy
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsGeneralsArmy;

    // TODO(WP-B15): enum DrakkisathHardModeSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
