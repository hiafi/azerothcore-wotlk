/*
 * mod-dungeon-bosses, Zul'Farrak D7: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D7 owns this file: its spell ids (inside kSpellsPool of ZulFarrakRework.h, 214110-214149),
 * its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static constexpr, timers
 * with a static_assert on kWarningFloorMs), picks and geometry, tested by tests/zf_gahzrilla_test.cpp. Health is
 * ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfPool
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsPool;

    namespace Tune
    {
        // TODO(WP-D7): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D7): enum PoolSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
