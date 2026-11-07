// Host tests for Odo the Blindwatcher (WP-S5): OdoLogic.h. STUB from WP-K: the slice and the arena; WP-S5 adds the
// suites of handoff section 5 for this boss.
#include "OdoLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Odo::kSlice.first));
        CHECK(kSpellsReservation.Contains(Odo::kSlice.last));
        CHECK(Odo::kSlice.first <= Odo::kSlice.last);
        CHECK(OdoArena().Contains(kOdoSpawn.XY(), kOdoSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_odo_test");
}
