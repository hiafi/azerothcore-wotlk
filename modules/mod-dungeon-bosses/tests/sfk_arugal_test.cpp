// Host tests for Archmage Arugal (WP-S9): ArugalLogic.h. STUB from WP-K: the slice and the arena; WP-S9 adds the suites
// of handoff section 5 for this boss.
#include "ArugalLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Arugal::kSlice.first));
        CHECK(kSpellsReservation.Contains(Arugal::kSlice.last));
        CHECK(Arugal::kSlice.first <= Arugal::kSlice.last);
        CHECK(ArugalArena().Contains(kArugalSpawn.XY(), kArugalSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_arugal_test");
}
