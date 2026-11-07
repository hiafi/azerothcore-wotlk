// Host tests for Wolf Master Nandos (WP-S8): NandosLogic.h. STUB from WP-K: the slice and the arena; WP-S8 adds the
// suites of handoff section 5 for this boss.
#include "NandosLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Nandos::kSlice.first));
        CHECK(kSpellsReservation.Contains(Nandos::kSlice.last));
        CHECK(Nandos::kSlice.first <= Nandos::kSlice.last);
        CHECK(NandosArena().Contains(kNandosSpawn.XY(), kNandosSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_nandos_test");
}
