// Host tests for GraduateExamLogic.h (S13: Darkmaster Gandling's hard mode, the Graduate Exam).
// STUB written by WP-KS: the slice and the arena; WP-S13 grows it with its mechanics' pure logic.
#include "GraduateExamLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoGraduateExam::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoGraduateExam::kSpellSlice.last));
    CHECK(!PassingGrades().HonorsOpen());

    return Report("scholo_exam_test");
}
