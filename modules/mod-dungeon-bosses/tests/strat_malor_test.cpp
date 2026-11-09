// Host tests for MalorLogic.h (S4: Malor the Zealous).
// STUB written by WP-S0: the slice and the arena; WP-S4 grows it with its mechanics' pure logic.
#include "MalorLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratMalor::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratMalor::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(MalorArena().Contains(kMalorSpawn.XY(), kMalorSpawn.z));
    CHECK(ArenaFor(BOSS_MALOR).Contains(kMalorSpawn.XY(), kMalorSpawn.z));

    return Report("strat_malor_test");
}
