// Host tests for ThekaLogic.h (D1).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D1 grows it with its mechanics' pure logic.
#include "ThekaLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfTheka::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfTheka::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(CourtyardArena().Contains(kThekaSpawn.XY(), kThekaSpawn.z));
    CHECK(ArenaFor(BOSS_THEKA).Contains(kThekaSpawn.XY(), kThekaSpawn.z));
    // rise A
    CHECK(CourtyardArena().Contains(kThekaRisePoints[0].XY(), kThekaRisePoints[0].z));
    // rise D
    CHECK(CourtyardArena().Contains(kThekaRisePoints[3].XY(), kThekaRisePoints[3].z));

    return Report("zf_theka_test");
}
