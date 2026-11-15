// Host tests for DrakkisathLogic.h (B14: General Drakkisath).
// STUB written by WP-S0: the slice and the arena; WP-B14 grows it with its mechanics' pure logic.
#include "DrakkisathLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsDrakkisath::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsDrakkisath::kSpellSlice.last));
    // He spawns kDrakkisathSpawn, inside his arena.
    CHECK(DrakkisathArena().Contains(kDrakkisathSpawn.XY(), kDrakkisathSpawn.z));
    CHECK(ArenaFor(BOSS_DRAKKISATH).Contains(kDrakkisathSpawn.XY(), kDrakkisathSpawn.z));

    return Report("brs_drakkisath_test");
}
