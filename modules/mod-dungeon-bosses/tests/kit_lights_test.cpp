// Host tests for the shared dungeon kit's turning lights (Gnomeregan WP-KT-G, F23, F53; SP MA1, MA2, MA4, MT23):
// DungeonKitLightLogic.h (LightClock, SweptSector, InLight, TouchLatch).
#include "DungeonKitLightLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace DungeonKit;

namespace
{
    float Deg(float rad)
    {
        return rad * 180.f / kPi;
    }

    float Rad(float deg)
    {
        return deg * kPi / 180.f;
    }

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // Angular distance in degrees, [0, 180].
    float Gap(float aRad, float bRad)
    {
        float d = std::fmod(std::fabs(aRad - bRad), kTwoPi);
        if (d > kPi)
            d = kTwoPi - d;
        return Deg(d);
    }

    void TestClock()
    {
        LightClock c(0.f, 12.f, 2);
        CHECK(c.Count() == 2 && c.Direction() == 1 && c.Turning());
        CHECK(Near(Deg(c.BearingOf(1)), 180.f));                    // MA2: opposite each other
        c.Advance(1000);
        CHECK(Near(Deg(c.Bearing()), 12.f));
        CHECK(Near(Deg(c.BearingOf(1)), 192.f));

        // A hold runs down first; the rest of the tick turns.
        c.Hold(2000);
        CHECK(!c.Turning());
        c.Advance(1500);
        CHECK(Near(Deg(c.Bearing()), 12.f));
        c.Advance(1000);                                            // 500 held, 500 turning
        CHECK(Near(Deg(c.Bearing()), 18.f) && c.Turning());

        // MA4: stop 2 s, then the other way.
        c.Reverse(2000);
        CHECK(c.Direction() == -1 && c.HoldLeftMs() == 2000 && c.Reversals() == 1);
        c.Advance(3000);
        CHECK(Near(Deg(c.Bearing()), 6.f));
        c.Advance(1000);
        CHECK(Near(Deg(c.Bearing()), 354.f));                       // wraps below 0

        // +10% per Spotted (MA2): two touches = 14.4 deg/s.
        c.SetSpeed(12.f * 1.2f);
        c.Advance(1000);
        CHECK(Near(Deg(c.Bearing()), 339.6f, 0.02f));
        CHECK(Near(c.TurnedDeg(), 12.f + 6.f + 12.f + 12.f + 14.4f, 0.02f));
        c.SetSpeed(-5.f);
        CHECK(c.DegPerSec() == 0.f && !c.Turning());

        // A shorter hold never cuts a longer one.
        LightClock h(0.f, 10.f, 1);
        h.Hold(3000);
        h.Hold(1000);
        CHECK(h.HoldLeftMs() == 3000);
        // Clockwise from 10 degrees.
        LightClock cw(Rad(10.f), 20.f, 1, -1);
        cw.Advance(1000);
        CHECK(Near(Deg(cw.Bearing()), 350.f));
    }

    // The look ahead: the arc the middle sweeps over the horizon, the hold first, the direction it now turns.
    void TestAhead()
    {
        LightClock c(Rad(90.f), 12.f, 2);
        LightArc a = c.Ahead(0, 3000);
        CHECK(Near(Deg(a.from), 90.f) && Near(Deg(a.sweep), 36.f));
        a = c.Ahead(1, 3000);
        CHECK(Near(Deg(a.from), 270.f) && Near(Deg(a.sweep), 36.f));
        c.Reverse(2000);
        a = c.Ahead(0, 3000);                                       // 2 s still, 1 s back
        CHECK(Near(Deg(a.sweep), -12.f));
        a = c.Ahead(0, 1500);                                       // all inside the stop
        CHECK(a.sweep == 0.f);
        CHECK(c.Ahead(0, 0).sweep == 0.f);

        // MA1 (normal): 40 degrees, 2 s dim then 60 degrees clockwise at 20 deg/s; the swept floor is 100 degrees.
        LightClock n(Rad(30.f), 20.f, 1, -1);
        n.Hold(2000);
        LightArc const sweep = n.Ahead(0, 5000);
        CHECK(Near(Deg(sweep.sweep), -60.f));
        LightSector const floor = SweptSector(sweep, 40.f);
        CHECK(Near(floor.angleDeg, 100.f) && Near(Deg(floor.bearing), 0.f, 0.02f) && !floor.Full());
    }

    void TestSector()
    {
        LightSector s = SweptSector({ 0.f, Rad(36.f) }, 30.f);
        CHECK(Near(s.angleDeg, 66.f) && Near(Deg(s.bearing), 18.f));
        s = SweptSector({ Rad(10.f), Rad(-40.f) }, 30.f);
        CHECK(Near(s.angleDeg, 70.f) && Near(Deg(s.bearing), 350.f, 0.02f));
        s = SweptSector({ 0.f, Rad(400.f) }, 30.f);
        CHECK(s.Full() && s.angleDeg == 360.f);
        s = SweptSector({ Rad(45.f), 0.f }, 30.f);                  // standing still: the cone itself
        CHECK(Near(s.angleDeg, 30.f) && Near(Deg(s.bearing), 45.f));
    }

    void TestInLight()
    {
        Vec2 const apex{ 0.f, 0.f };
        float const b = Rad(90.f);                                  // toward +y
        CHECK(InLight(apex, b, 30.f, 30.f, { 0.f, 10.f }));
        CHECK(InLight(apex, b, 30.f, 30.f, { 0.f, 30.f }));         // the edge counts
        CHECK(!InLight(apex, b, 30.f, 30.f, { 0.f, 30.5f }));
        CHECK(!InLight(apex, b, 30.f, 30.f, { 0.f, -10.f }));       // behind
        // 14 degrees off the middle is inside a 30 degree cone, 16 is not.
        CHECK(InLight(apex, b, 30.f, 30.f, { 20.f * std::cos(Rad(104.f)), 20.f * std::sin(Rad(104.f)) }));
        CHECK(!InLight(apex, b, 30.f, 30.f, { 20.f * std::cos(Rad(106.f)), 20.f * std::sin(Rad(106.f)) }));
        CHECK(!InLight(apex, b, 30.f, 30.f, { 0.f, 2.f }, 3.f));    // inside the inner radius
        CHECK(InLight(apex, b, 360.f, 30.f, { 0.f, -10.f }));
        CHECK(InLight(apex, b, 30.f, 30.f, apex));                  // the apex itself
    }

    // The look ahead covers every point a light touches over its horizon (sampled every 50 ms, 11 bearings across the
    // cone, out to its length), and the sector has the cone's own width on each side, no more.
    void TestSectorCovers()
    {
        int misses = 0;
        for (int dir : { 1, -1 })
            for (std::uint32_t hold : { 0u, 1000u, 2000u })
            {
                LightClock c(Rad(200.f), 12.f, 2, dir);
                c.Hold(hold);
                std::uint32_t const horizon = 3000;
                for (std::uint8_t i = 0; i < 2; ++i)
                {
                    LightSector const s = SweptSector(c.Ahead(i, horizon), 30.f);
                    LightClock walk = c;
                    for (std::uint32_t t = 0; t <= horizon; t += 50)
                    {
                        float const mid = walk.BearingOf(i);
                        for (float off = -14.9f; off <= 14.95f; off += 2.98f)    // the edges, inside by 0.1
                            for (float r = 1.f; r <= 29.95f; r += 7.225f)    // to 29.9
                            {
                                Vec2 const p{ r * std::cos(mid + Rad(off)), r * std::sin(mid + Rad(off)) };
                                if (!InLight({ 0.f, 0.f }, s.bearing, s.angleDeg, 30.f, p))
                                    ++misses;
                            }
                        walk.Advance(50);
                    }
                    // Tight: the sector's edges are the cone's at the arc's two ends.
                    LightArc const a = c.Ahead(i, horizon);
                    CHECK(Near(Gap(s.bearing, a.from) + 15.f, s.angleDeg * 0.5f, 0.05f));
                }
            }
        CHECK(misses == 0);
    }

    void TestLatch()
    {
        TouchLatch l;
        CHECK(l.Try(7, 0, 3000));
        CHECK(!l.Try(7, 2999, 3000));
        CHECK(l.LeftMs(7, 2000, 3000) == 1000);
        CHECK(l.Try(8, 100, 3000));                                 // per player
        CHECK(l.Try(7, 3000, 3000));
        CHECK(l.LeftMs(7, 3000, 3000) == 3000 && l.LeftMs(9, 0, 3000) == 0);
        CHECK(l.Size() == 2);
        l.Clear();
        CHECK(l.Try(7, 3001, 3000) && l.Size() == 1);
    }
}

int main()
{
    TestClock();
    TestAhead();
    TestSector();
    TestInLight();
    TestSectorCovers();
    TestLatch();
    return Report("kit_lights_test");
}
