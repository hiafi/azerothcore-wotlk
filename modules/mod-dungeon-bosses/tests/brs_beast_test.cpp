// Host tests for BeastLogic.h (B13: The Beast).
// STUB written by WP-S0: the slice and the arena; WP-B13 grows it with its mechanics' pure logic.
#include "BeastLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsBeast::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsBeast::kSpellSlice.last));
    // He spawns kBeastSpawn, inside his arena.
    CHECK(BeastArena().Contains(kBeastSpawn.XY(), kBeastSpawn.z));
    CHECK(ArenaFor(BOSS_BEAST).Contains(kBeastSpawn.XY(), kBeastSpawn.z));

    return Report("brs_beast_test");
}
