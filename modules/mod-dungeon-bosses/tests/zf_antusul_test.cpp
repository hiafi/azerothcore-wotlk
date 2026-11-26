// Host tests for AntusulLogic.h (D2).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D2 grows it with its mechanics' pure logic.
#include "AntusulLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfAntusul::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfAntusul::kSpellSlice.last));
    // The spawn is on the arena, and the slot's arena is the same one.
    CHECK(DenArena().Contains(kAntusulSpawn.XY(), kAntusulSpawn.z));
    CHECK(ArenaFor(BOSS_ANTUSUL).Contains(kAntusulSpawn.XY(), kAntusulSpawn.z));
    // the chamber
    CHECK(DenArena().Contains(kAntusulChamber.XY(), kAntusulChamber.z));
    // a throat rise point
    CHECK(DenArena().Contains(kServantRisePoints[0].XY(), kServantRisePoints[0].z));

    return Report("zf_antusul_test");
}
