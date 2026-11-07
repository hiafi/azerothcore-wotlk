// Host tests for Deathsworn Captain (WP-S6): DeathswornCaptainLogic.h. STUB from WP-K: the slice and the arena; WP-S6
// adds the suites of handoff section 5 for this boss.
#include "DeathswornCaptainLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(DeathswornCaptain::kSlice.first));
        CHECK(kSpellsReservation.Contains(DeathswornCaptain::kSlice.last));
        CHECK(DeathswornCaptain::kSlice.first <= DeathswornCaptain::kSlice.last);
        CHECK(DeathswornCaptainArena().Contains(kCaptainSpawn.XY(), kCaptainSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_deathsworn_captain_test");
}
