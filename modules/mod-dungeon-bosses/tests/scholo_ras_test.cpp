// Host tests for RasLogic.h (S4: Ras Frostwhisper (10508)).
// STUB written by WP-KS: the slice and the arena; WP-S4 grows it with its mechanics' pure logic.
#include "RasLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoRas::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoRas::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(RasArena().Contains(kRasSpawn.XY(), kRasSpawn.z));
    CHECK(ArenaFor(BOSS_RAS).Contains(kRasSpawn.XY(), kRasSpawn.z));

    return Report("scholo_ras_test");
}
