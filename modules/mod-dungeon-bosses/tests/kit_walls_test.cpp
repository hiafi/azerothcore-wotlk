// Host tests for the shared dungeon kit's lethal walls and relic dispensers (Stratholme WP-KT-2):
// DungeonKitWallLogic.h (wall geometry, the placement rule, crossings, the watch, the strike book, the dispense plan).
#include "DungeonKitWallLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <initializer_list>
#include <vector>

using namespace DungeonKit;

namespace
{
    bool Near(float a, float b, float tolerance = 1e-3f)
    {
        return std::fabs(a - b) <= tolerance;
    }

    // A 20 yd wall along x = 0, from y = -10 to y = 10, 2 yd wide.
    WallLine TestWall()
    {
        return { { 0.f, -10.f }, { 0.f, 10.f }, 2.f };
    }

    void TestGeometry()
    {
        WallLine const w = TestWall();
        CHECK(Near(w.Length(), 20.f));
        CHECK(Near(w.HalfWidth(), 1.f));
        CHECK(Near(WallClearance(w, { 5.f, 0.f }), 4.f));
        CHECK(Near(WallClearance(w, { 0.5f, 3.f }), -0.5f));
        CHECK(InsideWall(w, { 1.f, 0.f }));             // the strip's edge counts
        CHECK(!InsideWall(w, { 1.01f, 0.f }));
        CHECK(Near(WallClearance(w, { 0.f, 13.f }), 2.f));  // past an end: the capsule
        CHECK(WallSide(w, { -3.f, 0.f }) > 0.f);        // left of from -> to (north along +y)
        CHECK(WallSide(w, { 3.f, 0.f }) < 0.f);
        CHECK(Near(WallSide(w, { 3.f, 0.f }), -3.f));
        CHECK(Near(WallSide({ { 1.f, 1.f }, { 1.f, 1.f }, 2.f }, { 4.f, 4.f }), 0.f));     // degenerate wall

        CHECK(Near(SegmentToSegment({ -1.f, 0.f }, { 1.f, 0.f }, { 0.f, -1.f }, { 0.f, 1.f }), 0.f));   // crossing
        CHECK(Near(SegmentToSegment({ 0.f, 0.f }, { 10.f, 0.f }, { 0.f, 3.f }, { 10.f, 3.f }), 3.f));   // parallel
        CHECK(Near(SegmentToSegment({ 0.f, 0.f }, { 1.f, 0.f }, { 4.f, 4.f }, { 4.f, 4.f }), 5.f));     // to a point
        CHECK(Near(SegmentToSegment({ 0.f, 0.f }, { 10.f, 0.f }, { 5.f, 2.f }, { 5.f, 8.f }), 2.f));    // T, short
    }

    void TestPlacement()
    {
        WallLine const w = TestWall();
        std::array<KeepClear, 3> const keep{ {
            KeepClear::Point({ 8.f, 0.f }, 2.f),            // a shelter 8 yd off: gap 8 - 1 - 2 = 5
            KeepClear::Path({ 10.f, -20.f }, { 10.f, 20.f }, 3.f),  // a lane parallel 10 yd off: gap 6
            KeepClear::Point({ 0.f, 30.f }, 4.f),           // a fire spot past the north end: gap 20 - 1 - 4 = 15
        } };
        PlacementReport const r = CheckPlacement(w, keep);
        CHECK(Near(r.minYd, 5.f));
        CHECK(r.worst == 0);
        CHECK(KeepsClear(w, keep));                     // exactly 5 yd keeps the rule
        CHECK(!KeepsClear(w, keep, 5.5f));

        // A March path that runs into the wall's line fails it (the rank never marches through a cordon line).
        std::array<KeepClear, 1> const across{ { KeepClear::Path({ -20.f, 0.f }, { 20.f, 0.f }, 6.f) } };
        CHECK(CheckPlacement(w, across).minYd < 0.f);
        CHECK(!KeepsClear(w, across));

        CHECK(std::isinf(CheckPlacement(w, std::span<KeepClear const>()).minYd));
        CHECK(KeepsClear(w, std::span<KeepClear const>()));
    }

    void TestCrossings()
    {
        WallLine const w = TestWall();
        CHECK(CrossesWall(w, { -1.5f, 0.f }, { 1.5f, 0.f }));            // a walk across
        CHECK(CrossesWall(w, { 1.5f, 0.f }, { -1.5f, 0.f }));            // either way
        CHECK(CrossesWall(w, { -10.f, 2.f }, { 10.f, -2.f }));           // a 20 yd blink over it
        CHECK(CrossesWall(w, { -2.f, 9.f }, { 2.f, 10.9f }));            // inside the strip's rounded end
        CHECK(!CrossesWall(w, { -2.f, 12.f }, { 2.f, 12.f }));           // round the north end
        CHECK(!CrossesWall(w, { -3.f, -5.f }, { -3.f, 5.f }));           // along it, outside
        CHECK(!CrossesWall(w, { -3.f, 0.f }, { -0.5f, 0.f }));           // into the strip: the registry's
        CHECK(!CrossesWall(w, { 0.f, 0.f }, { 3.f, 0.f }));              // from the line itself: was inside
        CHECK(!CrossesWall(w, { -20.f, 0.f }, { 20.f, 0.f }));           // 40 yd: a teleport, not a crossing
        CHECK(CrossesWall(w, { -20.f, 0.f }, { 20.f, 0.f }, 50.f));      // unless the step limit allows it
        // A mounted sprint (14 yd/s) moves 3.5 yd in one 250 ms tick: wider than the 2 yd strip.
        float const step = 14.f * (static_cast<float>(kWallTickMs) / 1000.f);
        CHECK(step > w.width);
        CHECK(CrossesWall(w, { -1.75f, 0.f }, { -1.75f + step, 0.f }));

        // Galford's Pyre (handoff section 3.8: x 3446, y -3074.5..-3101.5): a step south across it.
        WallLine const pyre{ { 3446.f, -3074.5f }, { 3446.f, -3101.5f }, 3.f };
        CHECK(CrossesWall(pyre, { 3448.f, -3090.f }, { 3443.f, -3090.f }));
        CHECK(!CrossesWall(pyre, { 3448.f, -3090.f }, { 3448.f, -3060.f }));
    }

    void TestWatch()
    {
        WallWatch watch(TestWall());
        CHECK(!watch.Observe(1, { -3.f, 0.f }));        // first sight: nothing to compare
        CHECK(!watch.Observe(2, { 5.f, 0.f }));
        watch.Sweep();
        CHECK(watch.Size() == 2);
        CHECK(watch.Observe(1, { 3.f, 0.f }));          // 1 crossed since the last poll
        CHECK(!watch.Observe(2, { 6.f, 0.f }));
        watch.Sweep();
        CHECK(!watch.Observe(1, { 3.5f, 0.f }));        // on the far side now: no second crossing
        watch.Sweep();                                  // 2 not seen this poll (dead, gone): forgotten
        CHECK(watch.Size() == 1);
        CHECK(!watch.Observe(2, { -6.f, 0.f }));        // seen again on the other side: a fresh start (a teleport)
        CHECK(!watch.Observe(1, { 3.5f, 0.f }));
        watch.Sweep();
        CHECK(watch.Size() == 2);
        CHECK(Near(watch.Line().width, 2.f));
    }

    void TestStrikeBook()
    {
        StrikeBook book;
        CHECK(book.Due(7, 1000));
        CHECK(!book.Due(7, 1000 + kRestrikeMs - 1));    // a second tick inside the window
        CHECK(book.Due(8, 1100));                       // another unit is its own
        CHECK(book.Due(7, 1000 + kRestrikeMs));
        CHECK(book.Size() == 2);
        book.Prune(1100 + kRestrikeMs + kRestrikeMs);
        CHECK(book.Size() == 0);
        StrikeBook every(0);
        CHECK(every.Due(1, 5) && every.Due(1, 5));
        CHECK(kRestrikeMs > kWallTickMs);               // a survivor is struck every other tick, not every one
        CHECK(kWallArmMs == 2000);                      // section 10
    }

    // User ruling (F-2): a strike is an outright kill; no absorb, shield, reduction or immunity leaves a survivor.
    void TestOutrightKill()
    {
        LethalStrikeTarget plain;
        CHECK(LethalStrikeKills(plain));
        for (std::uint32_t absorb : { 0u, 1u, 5000u, 1000000u })
            for (bool immune : { false, true })
                for (float taken : { 100.f, 60.f, 10.f, 0.f })
                {
                    LethalStrikeTarget t;
                    t.absorbLeft = absorb;
                    t.immunityAura = immune;
                    t.damageTakenPct = taken;
                    CHECK(LethalStrikeKills(t));
                }
        LethalStrikeTarget dead;
        dead.alive = false;
        CHECK(!LethalStrikeKills(dead));                // never killed twice
        LethalStrikeTarget god;
        god.godMode = true;
        god.absorbLeft = 5000;
        CHECK(!LethalStrikeKills(god));                 // .cheat god (a GM tool) is spared, like the engine's INSTAKILL
        LethalStrikeTarget redemption;
        redemption.spiritOfRedemption = true;
        CHECK(!LethalStrikeKills(redemption));          // the form already ends in death
    }

    void TestDispense()
    {
        std::vector<RelicCandidate> const party{
            { 10, true, false },        // the user
            { 11, true, true },         // already carries one
            { 12, false, false },       // outside the instance
            { 13, true, false },        // a bot in the group
            { 10, true, false },        // the user listed again as a group member
        };
        DispensePlan const plan = PlanDispense(party);
        CHECK(plan.give.size() == 2);
        CHECK(plan.give.size() == 2 && plan.give[0] == 10 && plan.give[1] == 13);
        CHECK(plan.had == 1);
        CHECK(plan.away == 1);

        std::vector<RelicCandidate> const solo{ { 1, true, true } };
        DispensePlan const again = PlanDispense(solo);
        CHECK(again.give.empty() && again.had == 1 && again.away == 0);
        CHECK(PlanDispense(std::span<RelicCandidate const>()).give.empty());

        // R-2-FW m-3: a click calls GossipHello from the use and again from the report-use; only the use dispenses.
        CHECK(DispensesOnClick(true, false));
        CHECK(!DispensesOnClick(true, true));
        CHECK(!DispensesOnClick(false, false));
        CHECK(!DispensesOnClick(false, true));
    }
}

int main()
{
    TestGeometry();
    TestPlacement();
    TestCrossings();
    TestWatch();
    TestStrikeBook();
    TestOutrightKill();
    TestDispense();
    return Report("kit_walls_test");
}
