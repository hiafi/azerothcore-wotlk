// Host tests for Arugal's hard mode "Face Him Alone" (WP-S10): FaceHimAloneLogic.h. STUB from WP-K: the slice; WP-S10
// adds its suites.
#include "FaceHimAloneLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"

using namespace ShadowfangKeepRework;

namespace
{
    void TestSlice()
    {
        CHECK(kSpellsArugal.Contains(FaceHimAlone::kSlice.first));
        CHECK(kSpellsArugal.Contains(FaceHimAlone::kSlice.last));
        CHECK(FaceHimAlone::kSlice.Size() == 5);
    }
}

int main()
{
    TestSlice();
    return Report("sfk_face_him_alone_test");
}
