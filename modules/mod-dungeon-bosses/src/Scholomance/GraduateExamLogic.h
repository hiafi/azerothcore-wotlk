/*
 * mod-dungeon-bosses, Scholomance S13:
 * Darkmaster Gandling's hard mode, the Graduate Exam, the pure, host-testable part (no engine headers).
 * STUB written by WP-KS; WP-S13 owns this file: its spell ids (inside kSpellsGandlingHardMode of ScholomanceRework.h),
 * tuning constants (`inline constexpr DungeonKit::NH<...> k<Name>{ normal, heroic };`), timers, picks and geometry,
 * tested by tests/scholo_exam_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GRADUATE_EXAM_LOGIC_H

#include "ScholomanceRework.h"
#include <cstdint>

namespace ScholoGraduateExam
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsGandlingHardMode;

    // TODO(WP-S13): enum GraduateExamSpells : std::uint32_t { SPELL_..._... = <id in kSpellSlice>, };
}

#endif
