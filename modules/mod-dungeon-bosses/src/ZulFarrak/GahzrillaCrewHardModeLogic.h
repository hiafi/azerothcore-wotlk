/*
 * mod-dungeon-bosses, Zul'Farrak D7Ha: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D7Ha owns this file: its spell ids (inside kSpellsPoolCrew of ZulFarrakRework.h,
 * 214150-214189), its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static
 * constexpr, timers with a static_assert on kWarningFloorMs), picks and geometry, tested by
 * tests/zf_hard_mode_test.cpp. Health is ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_CREW_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_CREW_HARD_MODE_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfPoolCrew
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsPoolCrew;

    namespace Tune
    {
        // TODO(WP-D7Ha): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D7Ha): enum PoolCrewSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
