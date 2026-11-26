// Host tests for GahzrillaDelugeLogic.h (D7Hb).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D7Hb grows it with its mechanics' pure logic.
#include "GahzrillaDelugeLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfDeluge::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfDeluge::kSpellSlice.last));
    // a shore disc
    CHECK(PoolArena().Contains(kShoreDiscs[0].XY(), kShoreDiscs[0].z));

    return Report("zf_deluge_test");
}
