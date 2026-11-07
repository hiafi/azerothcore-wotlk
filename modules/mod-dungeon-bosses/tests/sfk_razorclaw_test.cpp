// Host tests for Razorclaw the Butcher (WP-S2): RazorclawLogic.h. STUB from WP-K: the slice and the arena; WP-S2 adds
// the suites of handoff section 5 for this boss.
#include "RazorclawLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Razorclaw::kSlice.first));
        CHECK(kSpellsReservation.Contains(Razorclaw::kSlice.last));
        CHECK(Razorclaw::kSlice.first <= Razorclaw::kSlice.last);
        CHECK(RazorclawArena().Contains(kRazorclawSpawn.XY(), kRazorclawSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_razorclaw_test");
}
