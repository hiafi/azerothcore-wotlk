// Host tests for BarthilasLogic.h (S9: Magistrate Barthilas).
// STUB written by WP-S0: the slice and the arena; WP-S9 grows it with its mechanics' pure logic.
#include "BarthilasLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratBarthilas::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratBarthilas::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(BarthilasArena().Contains(kBarthilasSpawn.XY(), kBarthilasSpawn.z));
    CHECK(ArenaFor(BOSS_BARTHILAS).Contains(kBarthilasSpawn.XY(), kBarthilasSpawn.z));

    return Report("strat_barthilas_test");
}
