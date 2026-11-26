/*
 * mod-dungeon-bosses, Zul'Farrak D4b: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D4b owns this file: its spell ids (inside kSpellsStair of ZulFarrakRework.h,
 * 213990-214029), its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static
 * constexpr, timers with a static_assert on kWarningFloorMs), picks and geometry, tested by tests/zf_stair_test.cpp.
 * Health is ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_STAIR_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_STAIR_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfStair
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsStair;

    namespace Tune
    {
        // TODO(WP-D4b): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D4b): enum StairSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
