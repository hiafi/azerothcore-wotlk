// Host tests for Rethilgore (WP-S1): RethilgoreLogic.h. STUB from WP-K: the slice and the arena; WP-S1 adds the suites
// of handoff section 5 for this boss.
#include "RethilgoreLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSliceAndArena()
    {
        CHECK(kSpellsReservation.Contains(Rethilgore::kSlice.first));
        CHECK(kSpellsReservation.Contains(Rethilgore::kSlice.last));
        CHECK(Rethilgore::kSlice.first <= Rethilgore::kSlice.last);
        CHECK(RethilgoreArena().Contains(kRethilgoreSpawn.XY(), kRethilgoreSpawn.z));
    }
}

int main()
{
    TestSliceAndArena();
    return Report("sfk_rethilgore_test");
}
