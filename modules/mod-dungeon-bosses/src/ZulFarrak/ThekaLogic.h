/*
 * mod-dungeon-bosses, Zul'Farrak D1: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D1 owns this file: its spell ids (inside kSpellsTheka of ZulFarrakRework.h, 213860-213889),
 * its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static constexpr, timers
 * with a static_assert on kWarningFloorMs), picks and geometry, tested by tests/zf_theka_test.cpp. Health is
 * ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_THEKA_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_THEKA_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfTheka
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsTheka;

    namespace Tune
    {
        // TODO(WP-D1): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D1): enum ThekaSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
