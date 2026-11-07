/*
 * mod-dungeon-bosses, Shadowfang Keep: Commander Springvale (WP-S4), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: SK 754-812 (build spec), SK
 * 625-753 (design), SP1-SP8.
 *
 * STUB from WP-K. Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries
 * of a `SpringvaleSpells` enum (apps/dbc-tools source/npcs/shadowfang_keep/commander_springvale.py declares the same
 * ids); tuning numbers as `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the
 * same on both difficulties: the reference row (normal 1,300 / heroic 4,120) makes the difference.
 *
 * TODO(WP-S4): the spell enum, registry tags, tuning, timers and the pure logic its host test covers
 * (tests/sfk_springvale_test.cpp).
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_SPRINGVALE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_SPRINGVALE_LOGIC_H

#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <cstdint>

namespace Springvale
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsSpringvale;
}

#endif
