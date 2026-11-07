// Host tests for Commander Springvale (WP-S4): SpringvaleLogic.h. STUB from WP-K: the slice and the arena; WP-S4 adds
// the suites of handoff section 5 for this boss.
#include "SpringvaleLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Springvale::kSlice.first));
        CHECK(kSpellsReservation.Contains(Springvale::kSlice.last));
        CHECK(Springvale::kSlice.first <= Springvale::kSlice.last);
        CHECK(SpringvaleArena().Contains(kSpringvaleSpawn.XY(), kSpringvaleSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_springvale_test");
}
