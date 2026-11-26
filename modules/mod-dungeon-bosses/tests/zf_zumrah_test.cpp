// Host tests for ZumrahLogic.h (D3).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D3 grows it with its mechanics' pure logic.
#include "ZumrahLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfZumrah::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfZumrah::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(BowlArena().Contains(kZumrahSpawn.XY(), kZumrahSpawn.z));
    CHECK(ArenaFor(BOSS_ZUMRAH).Contains(kZumrahSpawn.XY(), kZumrahSpawn.z));
    // the cauldron
    CHECK(BowlArena().Contains(kCauldron.XY(), kCauldron.z));
    // the neck mouth
    CHECK(BowlArena().Contains(kBoundDeadOverflow.XY(), kBoundDeadOverflow.z));

    return Report("zf_zumrah_test");
}
