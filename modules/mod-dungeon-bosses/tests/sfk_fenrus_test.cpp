// Host tests for Fenrus the Devourer (WP-S7): FenrusLogic.h. STUB from WP-K: the slice and the arena; WP-S7 adds the
// suites of handoff section 5 for this boss.
#include "FenrusLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Fenrus::kSlice.first));
        CHECK(kSpellsReservation.Contains(Fenrus::kSlice.last));
        CHECK(Fenrus::kSlice.first <= Fenrus::kSlice.last);
        CHECK(FenrusArena().Contains(kFenrusSpawn.XY(), kFenrusSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_fenrus_test");
}
