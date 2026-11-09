// Host tests for RamsteinLogic.h (S13: Ramstein the Gorger).
// STUB written by WP-S0: the slice and the arena; WP-S13 grows it with its mechanics' pure logic.
#include "RamsteinLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratRamstein::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratRamstein::kSpellSlice.last));
    // He is summoned in his pen and walks in to his stop, inside his arena.
    CHECK(RamsteinArena().Contains(kRamsteinStop.XY(), kRamsteinStop.z));
    CHECK(ArenaFor(BOSS_RAMSTEIN).Contains(kRamsteinStop.XY(), kRamsteinStop.z));

    return Report("strat_ramstein_test");
}
