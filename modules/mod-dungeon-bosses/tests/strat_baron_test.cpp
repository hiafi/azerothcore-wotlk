// Host tests for BaronLogic.h (S14: Baron Rivendare).
// STUB written by WP-S0: the slice and the arena; WP-S14 grows it with its mechanics' pure logic.
#include "BaronLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratBaron::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratBaron::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(BaronArena().Contains(kBaronSpawn.XY(), kBaronSpawn.z));
    CHECK(ArenaFor(BOSS_BARON).Contains(kBaronSpawn.XY(), kBaronSpawn.z));

    return Report("strat_baron_test");
}
