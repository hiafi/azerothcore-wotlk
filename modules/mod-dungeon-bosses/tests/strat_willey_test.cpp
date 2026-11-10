// Host tests for WilleyLogic.h (S5: Cannon Master Willey).
// STUB written by WP-S0: the slice and the arena; WP-S5 grows it with its mechanics' pure logic.
#include "WilleyLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratWilley::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratWilley::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(WilleyArena().Contains(kWilleySpawn.XY(), kWilleySpawn.z));
    CHECK(ArenaFor(BOSS_WILLEY).Contains(kWilleySpawn.XY(), kWilleySpawn.z));

    return Report("strat_willey_test");
}
