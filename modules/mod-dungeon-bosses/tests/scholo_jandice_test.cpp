// Host tests for JandiceLogic.h (S1: Jandice Barov (10503)).
// STUB written by WP-KS: the slice and the arena; WP-S1 grows it with its mechanics' pure logic.
#include "JandiceLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoJandice::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoJandice::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(JandiceArena().Contains(kJandiceSpawn.XY(), kJandiceSpawn.z));
    CHECK(ArenaFor(BOSS_JANDICE).Contains(kJandiceSpawn.XY(), kJandiceSpawn.z));

    return Report("scholo_jandice_test");
}
