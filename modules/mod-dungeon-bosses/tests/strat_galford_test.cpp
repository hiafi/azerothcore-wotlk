// Host tests for GalfordLogic.h (S6: Archivist Galford).
// STUB written by WP-S0: the slice and the arena; WP-S6 grows it with its mechanics' pure logic.
#include "GalfordLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratGalford::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratGalford::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(GalfordArena().Contains(kGalfordSpawn.XY(), kGalfordSpawn.z));
    CHECK(ArenaFor(BOSS_GALFORD).Contains(kGalfordSpawn.XY(), kGalfordSpawn.z));

    return Report("strat_galford_test");
}
