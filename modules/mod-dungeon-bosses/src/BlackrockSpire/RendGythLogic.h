/*
 * mod-dungeon-bosses, Blackrock Spire B12:
 * Warchief Rend Blackhand (10429), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B12 owns this file: its spell ids (inside kSpellsRendGyth of
 * BlackrockSpireRework.h, 210430-210489), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_rend_gyth_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_REND_GYTH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_REND_GYTH_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsRendGyth
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsRendGyth;

    // TODO(WP-B12): enum RendGythSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
