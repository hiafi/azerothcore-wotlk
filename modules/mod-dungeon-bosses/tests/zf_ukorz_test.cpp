// Host tests for UkorzLogic.h (D6).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D6 grows it with its mechanics' pure logic.
#include "UkorzLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfUkorz::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfUkorz::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(MesaArena().Contains(kUkorzSpawn.XY(), kUkorzSpawn.z));
    CHECK(ArenaFor(BOSS_UKORZ).Contains(kUkorzSpawn.XY(), kUkorzSpawn.z));
    // the donut center
    CHECK(MesaArena().Contains(kMesaDonutCenter.XY(), kMesaDonutCenter.z));
    // Ruuzlu
    CHECK(MesaArena().Contains(kRuuzluSpawn.XY(), kRuuzluSpawn.z));

    return Report("zf_ukorz_test");
}
