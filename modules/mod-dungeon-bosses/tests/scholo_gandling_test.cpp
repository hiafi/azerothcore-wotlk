// Host tests for GandlingLogic.h (S11: Darkmaster Gandling).
// STUB written by WP-KS: the slice and the arena; WP-S11 grows it with its mechanics' pure logic.
#include "GandlingLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoGandling::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoGandling::kSpellSlice.last));
    CHECK(GandlingArena().Contains(kGandlingSpawn.XY(), kGandlingSpawn.z));
    // Every classroom has a landing point in its own arena.
    for (std::size_t i = 0; i < kClassroomCount; ++i)
        CHECK(ClassroomArena(Classroom(i)).Contains(kClassroomLandings[i].XY(), kClassroomLandings[i].z));

    return Report("scholo_gandling_test");
}
