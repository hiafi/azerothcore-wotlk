/*
 * mod-dungeon-bosses, Blackrock Spire B11:
 * Solakar Flamewreath (10264), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B11 owns this file: its spell ids (inside kSpellsSolakar of
 * BlackrockSpireRework.h, 210390-210429), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_solakar_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_SOLAKAR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_SOLAKAR_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsSolakar
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsSolakar;

    // TODO(WP-B11): enum SolakarSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
