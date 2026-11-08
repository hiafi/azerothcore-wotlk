// Host tests for RattlegoreLogic.h (S2: Rattlegore (11622)).
// STUB written by WP-KS: the slice and the arena; WP-S2 grows it with its mechanics' pure logic.
#include "RattlegoreLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoRattlegore::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoRattlegore::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(RattlegoreArena().Contains(kRattlegoreSpawn.XY(), kRattlegoreSpawn.z));
    CHECK(ArenaFor(BOSS_RATTLEGORE).Contains(kRattlegoreSpawn.XY(), kRattlegoreSpawn.z));

    return Report("scholo_rattlegore_test");
}
