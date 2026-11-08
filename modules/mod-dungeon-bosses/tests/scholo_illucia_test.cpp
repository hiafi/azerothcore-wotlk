// Host tests for IlluciaLogic.h (S10: Lady Illucia Barov (10502)).
// STUB written by WP-KS: the slice and the arena; WP-S10 grows it with its mechanics' pure logic.
#include "IlluciaLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoIllucia::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoIllucia::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(IlluciaArena().Contains(kIlluciaSpawn.XY(), kIlluciaSpawn.z));
    CHECK(ArenaFor(BOSS_ILLUCIA).Contains(kIlluciaSpawn.XY(), kIlluciaSpawn.z));

    return Report("scholo_illucia_test");
}
