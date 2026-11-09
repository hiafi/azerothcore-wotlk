// Host tests for BaronessLogic.h (S10: Baroness Anastari).
// STUB written by WP-S0: the slice and the arena; WP-S10 grows it with its mechanics' pure logic.
#include "BaronessLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratBaroness::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratBaroness::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(BaronessArena().Contains(kBaronessSpawn.XY(), kBaronessSpawn.z));
    CHECK(ArenaFor(BOSS_BARONESS).Contains(kBaronessSpawn.XY(), kBaronessSpawn.z));

    return Report("strat_baroness_test");
}
