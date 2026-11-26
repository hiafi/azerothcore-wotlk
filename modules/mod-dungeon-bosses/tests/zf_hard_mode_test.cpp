// Host tests for GahzrillaCrewHardModeLogic.h (D7Ha).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D7Ha grows it with its mechanics' pure logic.
#include "GahzrillaCrewHardModeLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfPoolCrew::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfPoolCrew::kSpellSlice.last));
    // the gong
    CHECK(PoolArena().Contains(kGong.XY(), kGong.z));

    return Report("zf_hard_mode_test");
}
