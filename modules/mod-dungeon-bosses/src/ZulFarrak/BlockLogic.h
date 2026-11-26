/*
 * mod-dungeon-bosses, Zul'Farrak D4a: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D4a owns this file: its spell ids (inside kSpellsBlock of ZulFarrakRework.h,
 * 213960-213989), its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static
 * constexpr, timers with a static_assert on kWarningFloorMs), picks and geometry, tested by tests/zf_block_test.cpp.
 * Health is ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLOCK_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_BLOCK_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfBlock
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsBlock;

    namespace Tune
    {
        // TODO(WP-D4a): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D4a): enum BlockSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
