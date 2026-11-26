// Host tests for the shared dungeon kit's water sheets (Zul'Farrak WP-KT, F41): DungeonKitWaterLogic.h (WaterSheets,
// DiscFor). Spec rows SP GZ2-GZ8, GZ13, GZ15, GZ22, GZ23; handoff section 7 #36 A, #37 A, #43 f.
#include "DungeonKitWaterLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace DungeonKit;

namespace
{
    bool Near(float a, float b, float tolerance = 1e-3f)
    {
        return std::fabs(a - b) <= tolerance;
    }

    void TestShapes()
    {
        WaterSheets w;
        std::uint32_t const a = w.Add({ 0.f, 0.f }, 10.f, 8.f);
        CHECK(a == 1);
        CHECK(w.Add({ 0.f, 0.f }, 10.f, 0.f) == 0);                    // no radius: refused
        CHECK(w.IsWater({ 7.9f, 0.f }, 10.f));
        CHECK(w.IsWater({ 8.f, 0.f }, 10.f));                           // the rim counts
        CHECK(!w.IsWater({ 8.1f, 0.f }, 10.f));
        CHECK(w.IsWater({ 0.f, 0.f }, 15.9f));                          // the z band (6 yd)
        CHECK(!w.IsWater({ 0.f, 0.f }, 16.5f));
        CHECK(Near(w.Find(a)->EdgeDistance({ 11.f, 0.f }), 3.f));

        // A strip is the registry's rectangle: square ends, `radius` either side.
        std::uint32_t const pool = w.AddStrip({ 100.f, 0.f }, { 140.f, 0.f }, 10.f, 7.5f, { .canFreeze = false });
        WaterSheet const* p = w.Find(pool);
        CHECK(p && p->IsStrip());
        CHECK(w.IsWater({ 120.f, 7.4f }, 10.f));
        CHECK(!w.IsWater({ 120.f, 7.6f }, 10.f));
        CHECK(w.IsWater({ 100.f, 7.f }, 10.f));                         // the square corner
        CHECK(!w.IsWater({ 99.f, 0.f }, 10.f));
        CHECK(Near(p->EdgeDistance({ 143.f, 11.5f }), 5.f));            // 3 past the end, 4 past the side
        CHECK(Near(p->Middle().x, 120.f));
        CHECK(w.WaterSheetAt({ 120.f, 0.f }, 10.f) == pool);
    }

    void TestFreezeAndThaw()
    {
        WaterSheets w;
        SheetRules puddle;
        puddle.thawMs = 45000;
        std::uint32_t const a = w.Add({ 0.f, 0.f }, 10.f, 8.f, puddle);
        std::uint32_t const b = w.Add({ 10.f, 0.f }, 10.f, 8.f, puddle);    // overlaps a between x 2 and 8

        // Icicle: the puddle the target stands in, the nearest middle when two hold the point.
        FreezeResult r = w.FreezeAt({ 6.f, 0.f }, 10.f);
        CHECK(r.frozen.size() == 1 && r.frozen[0] == b);
        CHECK(!r.Meltwater());
        CHECK(w.Find(b)->state == SheetState::Ice);
        CHECK(w.CountIn(SheetState::Ice) == 1);
        // Ice wins: the overlap is dry, a's own side is still wet.
        CHECK(!w.IsWater({ 6.f, 0.f }, 10.f));
        CHECK(w.IsIce({ 6.f, 0.f }, 10.f));
        CHECK(w.IsWater({ -4.f, 0.f }, 10.f));
        CHECK(!w.InWaterSheet(a, { 6.f, 0.f }, 10.f));
        CHECK(w.InWaterSheet(a, { -4.f, 0.f }, 10.f));
        // Freezing ice again does nothing.
        CHECK(!w.Freeze(b));

        // Nothing to freeze: a Meltwater puddle (GZ13).
        r = w.FreezeAt({ 50.f, 50.f }, 10.f);
        CHECK(r.frozen.empty() && r.Meltwater());

        // The thaw: back to water at the radius it froze, on the clock (GZ8: 45 s normal).
        CHECK(w.ThawInMs(b) == 45000u);
        CHECK(w.Advance(44999).empty());
        std::vector<SheetChange> const thawed = w.Advance(1);
        CHECK(thawed.size() == 1 && thawed[0].id == b && thawed[0].kind == SheetChange::Kind::Thawed);
        CHECK(w.Find(b)->IsWater() && Near(w.Find(b)->radius, 8.f));
        CHECK(!w.ThawInMs(b));

        // thawMs 0: ice until Thaw by hand.
        SheetRules forever = puddle;
        forever.thawMs = 0;
        std::uint32_t const c = w.Add({ 40.f, 0.f }, 10.f, 8.f, forever);
        CHECK(w.Freeze(c));
        CHECK(w.Advance(600000).empty());
        CHECK(w.Thaw(c).has_value() && w.Find(c)->IsWater());
        CHECK(!w.Thaw(c).has_value());
    }

    void TestFreezeWithin()
    {
        WaterSheets w;
        std::uint32_t const near = w.Add({ 10.f, 0.f }, 10.f, 3.f);         // edge 7 yd from the origin
        std::uint32_t const touching = w.Add({ 0.f, 11.f }, 10.f, 3.f);     // edge 8 yd
        std::uint32_t const far = w.Add({ -12.f, 0.f }, 10.f, 3.f);         // edge 9 yd
        std::uint32_t const high = w.Add({ 0.f, -5.f }, 30.f, 3.f);         // over the z band
        FreezeResult const r = w.FreezeWithin({ 0.f, 0.f }, 10.f, 8.f);    // Freeze Solid: 8 yd
        CHECK(r.frozen.size() == 2);
        CHECK(w.Find(near)->state == SheetState::Ice);
        CHECK(w.Find(touching)->state == SheetState::Ice);
        CHECK(w.Find(far)->IsWater());
        CHECK(w.Find(high)->IsWater());
        CHECK(!r.Meltwater());
        FreezeResult const none = w.FreezeWithin({ 100.f, 0.f }, 10.f, 8.f);
        CHECK(none.Meltwater());
    }

    // Section 7 #37 A: the pool always counts as water and never freezes.
    void TestPool()
    {
        WaterSheets w;
        SheetRules poolRules;
        poolRules.canFreeze = false;
        poolRules.grows = false;
        std::uint32_t const pool = w.AddStrip({ 0.f, 0.f }, { 40.f, 0.f }, 9.f, 8.f, poolRules);
        FreezeResult r = w.FreezeAt({ 20.f, 0.f }, 9.f);
        CHECK(r.frozen.empty() && r.unfreezable && !r.Meltwater());
        CHECK(w.IsWater({ 20.f, 0.f }, 9.f));
        r = w.FreezeWithin({ 20.f, 0.f }, 9.f, 8.f);
        CHECK(r.frozen.empty() && r.unfreezable);
        r = w.FreezeWithin({ 20.f, 12.f }, 9.f, 8.f);                       // on the shore beside it: Meltwater
        CHECK(r.frozen.empty() && !r.unfreezable && r.Meltwater());
        // A puddle in the pool's edge freezes; the pool does not.
        std::uint32_t const puddle = w.Add({ 20.f, 9.f }, 9.f, 4.f);
        r = w.FreezeAt({ 20.f, 7.f }, 9.f);
        CHECK(r.frozen.size() == 1 && r.frozen[0] == puddle && !r.unfreezable);
        CHECK(w.Find(pool)->IsWater());
        // The pool does not rise.
        w.GrowWater(2.f);
        CHECK(Near(w.Find(pool)->radius, 8.f));
    }

    // GZ4: every water sheet grows; frozen ones keep the size they froze at (section 7 #43 f); no cap (#36 A).
    void TestGrowth()
    {
        WaterSheets w;
        std::uint32_t const a = w.Add({ 0.f, 0.f }, 10.f, 8.f);
        std::uint32_t const b = w.Add({ 50.f, 0.f }, 10.f, 8.f);
        CHECK(w.Freeze(b));
        std::vector<std::uint32_t> grown = w.GrowWater(2.f);
        CHECK(grown.size() == 1 && grown[0] == a);
        CHECK(Near(w.Find(a)->radius, 10.f));
        CHECK(Near(w.Find(b)->radius, 8.f));
        for (int i = 0; i < 20; ++i)
            w.GrowWater(3.f);
        CHECK(Near(w.Find(a)->radius, 70.f));                              // no cap
        CHECK(w.Advance(45000).size() == 1);
        CHECK(Near(w.Find(b)->radius, 8.f));                               // thawed at its frozen size

        // A cap, and a hand step whatever the rules (a Wellspring's own 2 yd every 5 s).
        SheetRules capped;
        capped.maxRadiusYd = 16.f;
        std::uint32_t const c = w.Add({ 0.f, 100.f }, 10.f, 15.f, capped);
        w.GrowWater(3.f);
        CHECK(Near(w.Find(c)->radius, 16.f));
        CHECK(!w.Grow(c, 1.f));                                             // at the cap: no change
        SheetRules spring;
        spring.canFreeze = false;
        spring.grows = false;
        std::uint32_t const s = w.Add({ 100.f, 100.f }, 10.f, 6.f, spring);
        w.GrowWater(2.f);
        CHECK(Near(w.Find(s)->radius, 6.f));
        CHECK(w.Grow(s, 2.f) && Near(w.Find(s)->radius, 8.f));
        CHECK(w.SetRadius(s, 0.1f) && Near(w.Find(s)->radius, spring.minRadiusYd));
        CHECK(w.Remove(s) && !w.Find(s) && !w.Remove(s));
    }

    // The Deluge (GZ22, GZ23): a room-wide water sheet; floes are ice sheets on it that melt away.
    void TestDeluge()
    {
        WaterSheets w;
        SheetRules flood;
        flood.canFreeze = false;
        flood.grows = false;
        flood.avoid = false;
        flood.discharge = false;
        w.Add({ 0.f, 0.f }, 9.f, 40.f, flood);
        CHECK(w.IsWater({ 30.f, 0.f }, 9.f));
        SheetRules floe;
        floe.thawMs = 30000;
        floe.thawTo = ThawTo::Gone;
        std::uint32_t const f = w.Add({ 30.f, 0.f }, 9.f, 8.f, floe, SheetState::Ice);
        CHECK(!w.IsWater({ 30.f, 0.f }, 9.f));                             // on the floe: dry
        CHECK(w.IsWater({ 30.f, 9.f }, 9.f));                              // off it: the flood
        CHECK(w.ThawInMs(f) == 30000u);
        std::vector<SheetChange> const gone = w.Advance(30000);
        CHECK(gone.size() == 1 && gone[0].kind == SheetChange::Kind::Gone && !w.Find(f));
        CHECK(w.IsWater({ 30.f, 0.f }, 9.f));
        // Freeze Solid on the flood freezes nothing (the flood cannot freeze): the caller adds a 12 yd floe.
        FreezeResult const r = w.FreezeWithin({ 10.f, 0.f }, 9.f, 8.f);
        CHECK(r.frozen.empty() && r.unfreezable);
    }

    void TestNearest()
    {
        WaterSheets w;
        std::uint32_t const a = w.Add({ 0.f, 0.f }, 10.f, 4.f);
        std::uint32_t const b = w.Add({ 20.f, 0.f }, 10.f, 8.f);
        CHECK(w.NearestSheet({ 9.f, 0.f }, 10.f) == b);                    // edge 3 yd against 5
        CHECK(w.Freeze(b));
        CHECK(w.NearestSheet({ 9.f, 0.f }, 10.f, SheetState::Water) == a);
        CHECK(!w.NearestSheet({ 9.f, 0.f }, 40.f).has_value());
    }

    // Appendix C: the disc's display by state, the storm disc in a Discharge tell, scale = radius / 4.8.
    void TestDiscs()
    {
        DiscLooks const looks{ 90830, 90831, 90832, 4.8f, 0.05f };
        WaterSheets w;
        std::uint32_t const a = w.Add({ 0.f, 0.f }, 10.f, 9.6f);
        std::optional<DiscLook> d = DiscFor(*w.Find(a), false, looks);
        CHECK(d && d->display == 90830 && Near(d->scale, 2.f));
        d = DiscFor(*w.Find(a), true, looks);
        CHECK(d && d->display == 90832);
        w.Freeze(a);
        d = DiscFor(*w.Find(a), true, looks);                               // ice never storms
        CHECK(d && d->display == 90831 && Near(d->scale, 2.f));
        w.Thaw(a);
        w.GrowWater(2.4f);
        d = DiscFor(*w.Find(a), false, looks);
        CHECK(d && Near(d->scale, 2.5f));

        // No ice display: the water one; no storm display: no tell; no water display: no disc; a strip: no disc.
        DiscLooks const plain{ 90830, 0, 0, 4.8f, 0.05f };
        w.Freeze(a);
        CHECK(DiscFor(*w.Find(a), false, plain)->display == 90830);
        w.Thaw(a);
        CHECK(DiscFor(*w.Find(a), true, plain)->display == 90830);
        CHECK(!DiscFor(*w.Find(a), false, DiscLooks{}));
        std::uint32_t const pool = w.AddStrip({ 50.f, 0.f }, { 90.f, 0.f }, 10.f, 7.5f);
        CHECK(!DiscFor(*w.Find(pool), false, looks));
        // A tiny sheet keeps a visible floor of scale.
        std::uint32_t const tiny = w.Add({ 0.f, 50.f }, 10.f, 0.1f);
        CHECK(Near(DiscFor(*w.Find(tiny), false, looks)->scale, 0.5f / 4.8f));     // minRadiusYd 0.5
        DiscLook const one{ 1, 1.f };
        DiscLook const almost{ 1, 1.0001f };
        DiscLook const other{ 2, 1.f };
        CHECK(one == almost);
        CHECK(!(one == other));
    }
}

int main()
{
    TestShapes();
    TestFreezeAndThaw();
    TestFreezeWithin();
    TestPool();
    TestGrowth();
    TestDeluge();
    TestNearest();
    TestDiscs();
    return Report("kit_water_test");
}
