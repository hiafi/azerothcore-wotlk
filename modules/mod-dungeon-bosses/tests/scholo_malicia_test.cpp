// Host tests for MaliciaLogic.h (S5: Instructor Malicia (10505)).
// STUB written by WP-KS: the slice and the arena; WP-S5 grows it with its mechanics' pure logic.
#include "MaliciaLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoMalicia::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoMalicia::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(MaliciaArena().Contains(kMaliciaSpawn.XY(), kMaliciaSpawn.z));
    CHECK(ArenaFor(BOSS_MALICIA).Contains(kMaliciaSpawn.XY(), kMaliciaSpawn.z));

    return Report("scholo_malicia_test");
}
