// Host tests for RavenianLogic.h (S8: The Ravenian (10507) and Master Corvane).
// STUB written by WP-KS: the slice and the arena; WP-S8 grows it with its mechanics' pure logic.
#include "RavenianLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoRavenian::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoRavenian::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(RavenianArena().Contains(kRavenianSpawn.XY(), kRavenianSpawn.z));
    CHECK(ArenaFor(BOSS_RAVENIAN).Contains(kRavenianSpawn.XY(), kRavenianSpawn.z));

    return Report("scholo_ravenian_test");
}
