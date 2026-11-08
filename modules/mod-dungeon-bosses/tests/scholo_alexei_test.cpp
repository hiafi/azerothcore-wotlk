// Host tests for AlexeiLogic.h (S9: Lord Alexei Barov (10504)).
// STUB written by WP-KS: the slice and the arena; WP-S9 grows it with its mechanics' pure logic.
#include "AlexeiLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoAlexei::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoAlexei::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(AlexeiArena().Contains(kAlexeiSpawn.XY(), kAlexeiSpawn.z));
    CHECK(ArenaFor(BOSS_ALEXEI).Contains(kAlexeiSpawn.XY(), kAlexeiSpawn.z));

    return Report("scholo_alexei_test");
}
