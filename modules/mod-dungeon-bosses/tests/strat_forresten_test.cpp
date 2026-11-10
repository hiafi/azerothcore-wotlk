// Host tests for ForrestenLogic.h (S2: Hearthsinger Forresten).
// STUB written by WP-S0: the slice and the arena; WP-S2 grows it with its mechanics' pure logic.
#include "ForrestenLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratForresten::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratForresten::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(ForrestenArena().Contains(kForrestenSpawn.XY(), kForrestenSpawn.z));
    CHECK(ArenaFor(BOSS_FORRESTEN).Contains(kForrestenSpawn.XY(), kForrestenSpawn.z));

    return Report("strat_forresten_test");
}
