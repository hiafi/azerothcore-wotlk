// Host tests for MardukVectusLogic.h (S3: Marduk Blackpool and Vectus).
// STUB written by WP-KS: the slice and the arena; WP-S3 grows it with its mechanics' pure logic.
#include "MardukVectusLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoMardukVectus::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoMardukVectus::kSpellSlice.last));
    // Both spawn inside the Viewing Room arena.
    CHECK(ViewingRoomArena().Contains(kMardukSpawn.XY(), kMardukSpawn.z));
    CHECK(ViewingRoomArena().Contains(kVectusSpawn.XY(), kVectusSpawn.z));

    return Report("scholo_marduk_test");
}
