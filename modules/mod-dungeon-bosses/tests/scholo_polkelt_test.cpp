// Host tests for PolkeltLogic.h (S7: Lorekeeper Polkelt (10901)).
// STUB written by WP-KS: the slice and the arena; WP-S7 grows it with its mechanics' pure logic.
#include "PolkeltLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoPolkelt::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoPolkelt::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(PolkeltArena().Contains(kPolkeltSpawn.XY(), kPolkeltSpawn.z));
    CHECK(ArenaFor(BOSS_POLKELT).Contains(kPolkeltSpawn.XY(), kPolkeltSpawn.z));

    return Report("scholo_polkelt_test");
}
