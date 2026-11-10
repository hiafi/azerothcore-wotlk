// Host tests for UnforgivenLogic.h (S1: The Unforgiven).
// STUB written by WP-S0: the slice and the arena; WP-S1 grows it with its mechanics' pure logic.
#include "UnforgivenLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratUnforgiven::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratUnforgiven::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(UnforgivenArena().Contains(kUnforgivenSpawn.XY(), kUnforgivenSpawn.z));
    CHECK(ArenaFor(BOSS_UNFORGIVEN).Contains(kUnforgivenSpawn.XY(), kUnforgivenSpawn.z));

    return Report("strat_unforgiven_test");
}
