// Host tests for GahzrillaLogic.h (D7).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D7 grows it with its mechanics' pure logic.
#include "GahzrillaLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfPool::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfPool::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(PoolArena().Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
    CHECK(ArenaFor(BOSS_VELRATHA).Contains(kVelrathaSpawn.XY(), kVelrathaSpawn.z));
    // the ashore point
    CHECK(PoolArena().Contains(kGahzrillaAshore.XY(), kGahzrillaAshore.z));
    // the gong
    CHECK(PoolArena().Contains(kGong.XY(), kGong.z));

    return Report("zf_gahzrilla_test");
}
