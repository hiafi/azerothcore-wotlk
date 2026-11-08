/*
 * mod-dungeon-bosses, Scholomance S3:
 * Marduk Blackpool and Vectus, the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S3 owns this file: its spell ids (inside kSpellsMardukVectus of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_marduk_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_MARDUK_VECTUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_MARDUK_VECTUS_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoMardukVectus
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsMardukVectus;

    // TODO(WP-S3): enum MardukVectusSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
