// Host tests for KrastinovLogic.h (S6: Doctor Theolen Krastinov (11261)).
// STUB written by WP-KS: the slice and the arena; WP-S6 grows it with its mechanics' pure logic.
#include "KrastinovLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoKrastinov::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoKrastinov::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(KrastinovArena().Contains(kKrastinovSpawn.XY(), kKrastinovSpawn.z));
    CHECK(ArenaFor(BOSS_KRASTINOV).Contains(kKrastinovSpawn.XY(), kKrastinovSpawn.z));

    return Report("scholo_krastinov_test");
}
