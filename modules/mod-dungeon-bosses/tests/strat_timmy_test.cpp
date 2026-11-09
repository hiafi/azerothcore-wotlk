// Host tests for TimmyLogic.h (S3: Timmy the Cruel).
// STUB written by WP-S0: the slice and the arena; WP-S3 grows it with its mechanics' pure logic.
#include "TimmyLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratTimmy::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratTimmy::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(TimmyArena().Contains(kTimmySpawn.XY(), kTimmySpawn.z));
    CHECK(ArenaFor(BOSS_TIMMY).Contains(kTimmySpawn.XY(), kTimmySpawn.z));

    return Report("strat_timmy_test");
}
