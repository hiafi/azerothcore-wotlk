/*
 * mod-dungeon-bosses, Blackrock Spire B10:
 * Pyroguard Emberseer (9816), the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-B10 owns this file: its spell ids (inside kSpellsEmberseer of
 * BlackrockSpireRework.h, 210350-210389), tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal,
 * heroic };`), flex target pairs (`inline constexpr BlackrockSpireRework::FlexAB k<Name>Targets{ a, b };`), text
 * groups, timers, picks and geometry, tested by tests/brs_emberseer_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_EMBERSEER_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_EMBERSEER_LOGIC_H

#include "BlackrockSpireRework.h"
#include <cstdint>

namespace BrsEmberseer
{
    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsEmberseer;

    // TODO(WP-B10): enum EmberseerSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
