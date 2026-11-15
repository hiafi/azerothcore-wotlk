/*
 * mod-dungeon-bosses, Blackrock Spire B13:
 * The Beast (10430), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B13 owns this file: its spell ids (inside kSpellsBeast of
 * BlackrockSpireRework.h, 210490-210519), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_beast_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_BEAST_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_BEAST_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsBeast
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsBeast;

    // TODO(WP-B13): enum BeastSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
