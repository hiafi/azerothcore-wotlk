// Host tests for DathrohanLogic.h (S7: Grand Crusader Dathrohan and Balnazzar).
// STUB written by WP-S0: the slice and the arena; WP-S7 grows it with its mechanics' pure logic.
#include "DathrohanLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratDathrohan::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratDathrohan::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(DathrohanArena().Contains(kDathrohanSpawn.XY(), kDathrohanSpawn.z));
    CHECK(ArenaFor(BOSS_BALNAZZAR).Contains(kDathrohanSpawn.XY(), kDathrohanSpawn.z));

    return Report("strat_dathrohan_test");
}
