// Host tests for StairLogic.h (D4b).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D4b grows it with its mechanics' pure logic.
#include "StairLogic.h"
#include "SezzzizLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfStair::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfStair::kSpellSlice.last));
    CHECK(kSpellsReservation.Contains(ZfAltar::kSpellSlice.first));
    CHECK(ZfAltar::kSpellSlice.first == ZfStair::kSpellSlice.first);
    // the stair foot
    CHECK(StairArena().Contains(kStairFoot.XY(), kStairFoot.z));
    // the lip (the landing's edge) and the landing beyond it
    CHECK(StairArena().Contains(kStairLip.XY(), kStairLip.z));
    CHECK(LandingArena().Contains(kLanding.XY(), kLanding.z));

    return Report("zf_stair_test");
}
