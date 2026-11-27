// Host tests for the shared dungeon kit's called combination (Gnomeregan WP-KT-G, F37, F54; SP CP1-CP7, MT24):
// DungeonKitComboLogic.h (ComboFrame, ComboShapeDef, PlacedShape, ComboTimeline). The pocket numbers are the
// handoff's section 3.8 and section 7 #28 A (frame origin (-887.0, 364.2), center line due south), the room's
// section 3.8 (Thermaplugg's faces 50 yd out).
#include "DungeonKitComboLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <vector>

using namespace DungeonKit;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    ComboFrame const kPocket{ { -887.0f, 364.2f }, -272.6f, kPi };     // facing south (-x)

    void TestFrame()
    {
        // Forward is along the facing, left 90 degrees counter-clockwise: facing south, left is east (-y).
        Vec2 const p = kPocket.Point(10.f, 5.f);
        CHECK(Near(p.x, -897.f) && Near(p.y, 359.2f));
        ComboFrame const north{ { 0.f, 0.f }, 0.f, 0.f };
        Vec2 const q = north.Point(3.f, 4.f);
        CHECK(Near(q.x, 3.f) && Near(q.y, 4.f));                     // facing north, left is west (+y)

        ComboFrame const f = FrameFacing({ 10.f, 0.f }, 1.f, { 0.f, 0.f });
        CHECK(Near(f.facing, kPi) && f.z == 1.f);
    }

    // CP2, CP3: the two halves of the pocket to 30 yd; together they cover every pocket point south of the origin
    // (bbox x -912.2 to -884.8, y 342.8 to 389.8), and a point off the line is in exactly one.
    void TestHalves()
    {
        PlacedShape const left = Place(kPocket, ComboShapeDef::HalfLeft(0.f, 30.f, 30.f));
        PlacedShape const right = Place(kPocket, ComboShapeDef::HalfRight(0.f, 30.f, 30.f));
        CHECK(left.type == ComboShapeType::Rect && Near(left.lengthYd, 30.f) && Near(left.widthYd, 30.f));
        CHECK(left.Contains(kPocket.Point(10.f, 5.f)) && !right.Contains(kPocket.Point(10.f, 5.f)));
        CHECK(right.Contains(kPocket.Point(10.f, -5.f)) && !left.Contains(kPocket.Point(10.f, -5.f)));
        CHECK(left.Contains(kPocket.Point(10.f, 0.f)) && right.Contains(kPocket.Point(10.f, 0.f)));     // the line
        CHECK(!left.Contains(kPocket.Point(-1.f, 5.f)));                                                // behind
        CHECK(!left.Contains(kPocket.Point(31.f, 5.f)));

        int uncovered = 0;
        int both = 0;
        for (float x = -912.2f; x <= -887.0f; x += 0.5f)
            for (float y = 342.8f; y <= 389.8f; y += 0.5f)
            {
                bool const l = left.Contains({ x, y });
                bool const r = right.Contains({ x, y });
                if (!l && !r)
                    ++uncovered;
                if (l && r && std::fabs(y - 364.2f) > 0.01f)
                    ++both;
            }
        CHECK(uncovered == 0);
        CHECK(both == 0);
        // The east half is the one left of a frame facing south.
        CHECK(left.Contains({ -900.f, 350.f }) && right.Contains({ -900.f, 380.f }));
    }

    // CP4, CP6: Crowd Pummel within 12 yd of the boss and the Clinch past 12 yd to 40 never overlap off the edge.
    void TestCircleDonut()
    {
        Vec2 const boss{ -883.5655f, 363.25467f };
        // Facing south, forward = -dx and left = -dy: the boss is 3.43 yd north of the origin (forward -3.43) and
        // 0.95 yd east of the center line (left +0.95).
        ComboShapeDef const atBoss = ComboShapeDef::Circle(-(boss.x - kPocket.origin.x), -(boss.y - kPocket.origin.y),
            12.f);
        CHECK(Near(atBoss.forwardYd, -3.43f) && Near(atBoss.leftYd, 0.95f));
        PlacedShape const c = Place(kPocket, atBoss);
        CHECK(Near(c.at.x, boss.x, 0.001f) && Near(c.at.y, boss.y, 0.001f));
        PlacedShape const d = Place(kPocket, ComboShapeDef::Donut(atBoss.forwardYd, atBoss.leftYd, 12.f, 40.f));
        int overlap = 0;
        int gap = 0;
        for (float r = 0.5f; r < 40.f; r += 0.5f)
            for (float a = 0.f; a < 360.f; a += 15.f)
            {
                if (std::fabs(r - 12.f) < 0.01f)
                    continue;
                Vec2 const p{ boss.x + r * std::cos(a * kPi / 180.f), boss.y + r * std::sin(a * kPi / 180.f) };
                bool const in = c.Contains(p);
                bool const out = d.Contains(p);
                overlap += in && out;
                gap += !in && !out;
            }
        CHECK(overlap == 0 && gap == 0);
        CHECK(Near(Distance(d.LabelPoint(), boss), 26.f));          // the numeral halfway round the ring
    }

    // CP5: the Uppercut lane, 8 yd wide down the center line to the south wall.
    void TestLane()
    {
        PlacedShape const lane = Place(kPocket, ComboShapeDef::Lane(0.f, 25.f, 8.f));
        CHECK(lane.Contains(kPocket.Point(10.f, 3.9f)) && !lane.Contains(kPocket.Point(10.f, 4.1f)));
        CHECK(lane.Contains(kPocket.Point(24.9f, -3.9f)) && !lane.Contains(kPocket.Point(25.1f, 0.f)));
        Vec2 const mid = lane.LabelPoint();
        CHECK(Near(mid.x, -899.5f) && Near(mid.y, 364.2f));
    }

    // A cone and a turned rectangle: the facing turns with turnDeg (counter-clockwise).
    void TestTurned()
    {
        ComboFrame const f{ { 0.f, 0.f }, 0.f, 0.f };
        PlacedShape const cone = Place(f, ComboShapeDef::Cone(0.f, 0.f, 90.f, 60.f, 20.f));
        CHECK(Near(cone.facing, kPi * 0.5f));
        CHECK(cone.Contains({ 0.f, 10.f }) && !cone.Contains({ 10.f, 0.f }) && !cone.Contains({ 0.f, 21.f }));
        CHECK(Near(cone.LabelPoint().y, 10.f));
        PlacedShape const rect = Place(f, ComboShapeDef::Rect(2.f, 0.f, -90.f, 10.f, 4.f));
        CHECK(rect.Contains({ 2.f, -5.f }) && !rect.Contains({ 2.f, 5.f }) && !rect.Contains({ 4.5f, -5.f }));
    }

    // MT24 (ruling 68, section 7 #33 A): from a face 50 yd out, the halves split on the face-to-center line, near =
    // within 50 yd of the face, far beyond it.
    void TestFist()
    {
        Vec2 const center{ -531.32f, 670.16f };
        float const bearing = 127.f * kPi / 180.f;                 // face 01
        Vec2 const face{ center.x + 50.f * std::cos(bearing), center.y + 50.f * std::sin(bearing) };
        ComboFrame const f = FrameFacing(face, -326.5f, center);
        PlacedShape const near = Place(f, ComboShapeDef::Circle(0.f, 0.f, 50.f));
        PlacedShape const far = Place(f, ComboShapeDef::Donut(0.f, 0.f, 50.f, 150.f));
        PlacedShape const left = Place(f, ComboShapeDef::HalfLeft(-5.f, 140.f, 140.f));
        PlacedShape const right = Place(f, ComboShapeDef::HalfRight(-5.f, 140.f, 140.f));
        CHECK(near.Contains(center) && !far.Contains(center));      // the center is 50 yd out: near's edge
        Vec2 const beyond = Advance(center, f.facing, 10.f);
        CHECK(far.Contains(beyond) && !near.Contains(beyond));
        // Every point of the bowl (r 41 around the center) is in exactly one half, off the line.
        int bad = 0;
        for (float r = 1.f; r <= 41.f; r += 2.f)
            for (float a = 0.f; a < 360.f; a += 10.f)
            {
                Vec2 const p{ center.x + r * std::cos(a * kPi / 180.f), center.y + r * std::sin(a * kPi / 180.f) };
                bool const l = left.Contains(p);
                bool const rr = right.Contains(p);
                if (l == rr)
                    ++bad;
            }
        CHECK(bad == 0);
    }

    // CP1: the call flashes in order, the live marker 1.5 s, punches 2 s apart (normal); 0.8 s and 1.2 s (heroic).
    void TestTimeline()
    {
        ComboTiming const normal{ ComboCallMode::Sequential, 1000, 1500, 2000 };
        std::vector<PunchTimes> const t = ComboTimeline(normal, 3);
        CHECK(t.size() == 3);
        CHECK(t[0].callFrom == 0 && t[0].callTo == 1000 && t[1].callFrom == 1000 && t[2].callTo == 3000);
        CHECK(t[0].liveFrom == 3000 && t[0].strikeAt == 4500);
        CHECK(t[1].liveFrom == 5000 && t[1].strikeAt == 6500 && t[2].strikeAt == 8500);
        CHECK(t[0].strikeAt - t[0].callTo >= 1500);                 // SP: the first punch has the call plus 1.5 s
        CHECK(ComboLength(normal, 3) == 8500 && ComboLength(normal, 0) == 0);

        ComboTiming const heroic{ ComboCallMode::Sequential, 1000, 800, 1200 };
        std::vector<PunchTimes> const h = ComboTimeline(heroic, 5);
        CHECK(h[0].strikeAt == 5800 && h[4].strikeAt == 5800 + 4 * 1200 && h[4].liveFrom == h[4].strikeAt - 800);

        // MT24: the wind-up 4 s, every shape drawn at once and kept to its strike, punches 2.5 s apart.
        ComboTiming const fist{ ComboCallMode::AllAtOnce, 4000, 0, 2500 };
        std::vector<PunchTimes> const m = ComboTimeline(fist, 3);
        CHECK(m[0].strikeAt == 4000 && m[1].strikeAt == 6500 && m[2].strikeAt == 9000);
        for (PunchTimes const& p : m)
            CHECK(p.callFrom == 0 && p.callTo == p.strikeAt && p.liveFrom == p.strikeAt);
        ComboTiming const fistLive{ ComboCallMode::AllAtOnce, 4000, 1000, 2500 };
        std::vector<PunchTimes> const ml = ComboTimeline(fistLive, 2);
        CHECK(ml[0].callTo == 4000 && ml[0].strikeAt == 5000 && ml[1].callTo == 6500);
    }
}

int main()
{
    TestFrame();
    TestHalves();
    TestCircleDonut();
    TestLane();
    TestTurned();
    TestFist();
    TestTimeline();
    return Report("kit_combo_test");
}
