/*
 * mod-dungeon-bosses, Zul'Farrak D7Hb: the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-D7Hb owns this file: its spell ids (inside kSpellsDeluge of ZulFarrakRework.h,
 * 214190-214209), its script-local enums, its tuning (`namespace Tune`, section 3.5 rule 32: every percent a static
 * constexpr, timers with a static_assert on kWarningFloorMs), picks and geometry, tested by tests/zf_deluge_test.cpp.
 * Health is ZulFarrakRework.h Health: never restate it here.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_DELUGE_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_DELUGE_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfDeluge
{
    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsDeluge;

    namespace Tune
    {
        // TODO(WP-D7Hb): the Build spec's numbers, e.g.
        // inline constexpr DungeonKit::NH<float> kSomethingPct{ 40.f, 60.f };
    }

    // TODO(WP-D7Hb): enum DelugeSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
