// Host tests for CrewFightLogic.h (D5).
// STUB written by WP-S0: the slice, the arena and its spots; WP-D5 grows it with its mechanics' pure logic.
#include "CrewFightLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ZfCrewFight::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ZfCrewFight::kSpellSlice.last));
    // Bly's gather spot
    CHECK(PlazaArena().Contains(kCrewGatherPoints[0].XY(), kCrewGatherPoints[0].z));

    return Report("zf_crewfight_test");
}
