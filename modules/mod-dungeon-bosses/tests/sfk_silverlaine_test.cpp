// Host tests for Baron Silverlaine (WP-S3): SilverlaineLogic.h. STUB from WP-K: the slice and the arena; WP-S3 adds the
// suites of handoff section 5 for this boss.
#include "SilverlaineLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Silverlaine::kSlice.first));
        CHECK(kSpellsReservation.Contains(Silverlaine::kSlice.last));
        CHECK(Silverlaine::kSlice.first <= Silverlaine::kSlice.last);
        CHECK(SilverlaineArena().Contains(kSilverlaineSpawn.XY(), kSilverlaineSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_silverlaine_test");
}
