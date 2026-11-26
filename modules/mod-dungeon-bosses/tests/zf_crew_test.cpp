// Host tests for BlyCrewLogic.h (CR: Sergeant Bly's crew).
// STUB written by WP-S0: the slice, the factions by mode and the crew's points; WP-CR grows it (modes, Weegli's
// floor, restore after a wipe, reload and refill, the Test's key, the pool hand-off).
#include "BlyCrewLogic.h"
#include "check.h"

using namespace ZulFarrakRework;

int main()
{
    // CR's ally-kit spells sit in the shared slice, inside the dungeon's reservation.
    CHECK(kSpellsShared.Contains(ZfCrew::kSpellSlice.first));
    CHECK(kSpellsShared.Contains(ZfCrew::kSpellSlice.last));

    // Section 3.12: caged 35, ally 495, hostile 41, pool ally 35; only the fighting modes fight.
    CHECK(ZfCrew::FactionFor(CrewMode::Caged) == 35);
    CHECK(ZfCrew::FactionFor(CrewMode::Ally) == 495);
    CHECK(ZfCrew::FactionFor(CrewMode::Boss) == 41);
    CHECK(ZfCrew::FactionFor(CrewMode::PoolAlly) == 35);
    CHECK(ZfCrew::FightsIn(CrewMode::Ally) && ZfCrew::FightsIn(CrewMode::Boss) && ZfCrew::FightsIn(CrewMode::PoolAlly));
    CHECK(!ZfCrew::FightsIn(CrewMode::Caged) && !ZfCrew::FightsIn(CrewMode::Yielded));
    CHECK(!ZfCrew::FightsIn(CrewMode::Gone) && !ZfCrew::FightsIn(CrewMode::Prisoner));

    // Every crew point is on its room: the landing (the stair points), the plaza (the descent's foot and the gather).
    for (uint32_t m = 0; m < kCrewCount; ++m)
    {
        CHECK(PyramidTopArena().Contains(kCrewSpawns[m].XY(), kCrewSpawns[m].z));
        CHECK(PyramidTopArena().Contains(kCrewStairPoints[m].XY(), kCrewStairPoints[m].z));
        CHECK(PlazaArena().Contains(kCrewGatherPoints[m].XY(), kCrewGatherPoints[m].z));
        CHECK(InPyramidRegion(kCrewDescentPoints[m].XY()));
    }

    return Report("zf_crew_test");
}
