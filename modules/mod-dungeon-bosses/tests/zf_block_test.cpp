// Host tests for BlockLogic.h (D4a).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D4a grows it with its mechanics' pure logic.
#include "BlockLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfBlock::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfBlock::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(PyramidTopArena().Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
    CHECK(ArenaFor(BOSS_PYRAMID).Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
    // the landing
    CHECK(PyramidTopArena().Contains(kLanding.XY(), kLanding.z));
    // a cage
    CHECK(PyramidTopArena().Contains(kCages[0].XY(), kCages[0].z));

    return Report("zf_block_test");
}
