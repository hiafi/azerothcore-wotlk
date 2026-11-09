// Host tests for NerubenkanLogic.h (S11: Nerub'enkan).
// STUB written by WP-S0: the slice and the arena; WP-S11 grows it with its mechanics' pure logic.
#include "NerubenkanLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratNerubenkan::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratNerubenkan::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(NerubenkanArena().Contains(kNerubenkanSpawn.XY(), kNerubenkanSpawn.z));
    CHECK(ArenaFor(BOSS_NERUBENKAN).Contains(kNerubenkanSpawn.XY(), kNerubenkanSpawn.z));

    return Report("strat_nerubenkan_test");
}
