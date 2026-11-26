// Host tests for the shared dungeon kit's held Soaks (Zul'Farrak WP-KT, F36; SP UK6, the 2 s rescue):
// DungeonKitSoakLogic.h (SoakAt, SoakAtTakers), polled every 250 ms as DwellSoaks polls it.
#include "DungeonKitSoakLogic.h"
#include "check.h"
#include <cstdint>
#include <vector>

using namespace DungeonKit;

namespace
{
    std::uint32_t constexpr kPoll = 250;

    // Polls `inside` every 250 ms until the Soak is over or `maxMs` passed; the time it ended (0: not over).
    std::uint32_t RunUntilOver(SoakAt& s, std::vector<std::uint64_t> const& inside, std::uint32_t maxMs,
        SoakAtResult& last)
    {
        for (std::uint32_t t = kPoll; t <= maxMs; t += kPoll)
        {
            last = s.Update(inside, kPoll);
            if (last.step != SoakAtStep::Wait)
                return t;
        }
        return 0;
    }

    // UK6: a rescuer inside for 2 s frees the sunk player. The first poll that sees him counts its whole interval.
    void TestHeld()
    {
        SoakAt s(2000, 8000);
        SoakAtResult r;
        CHECK(RunUntilOver(s, { 7 }, 10000, r) == 2000);
        CHECK(r.step == SoakAtStep::Done && r.taker == 7);
        CHECK(s.Over() && s.LeftMs() == 0);
        // Over: the same answer from then on, whoever stands there.
        SoakAtResult const again = s.Update({ 9 }, kPoll);
        CHECK(again.step == SoakAtStep::Done && again.taker == 7);
    }

    // A step out starts him over; the clock is per player, and the longest holder takes it.
    void TestBreak()
    {
        SoakAt s(2000, 0);
        for (int i = 0; i < 7; ++i)                                     // 1.75 s
            CHECK(s.Update({ 1 }, kPoll).step == SoakAtStep::Wait);
        CHECK(s.Update({}, kPoll).step == SoakAtStep::Wait);            // out for one poll
        for (int i = 0; i < 7; ++i)
            CHECK(s.Update({ 1, 2 }, kPoll).step == SoakAtStep::Wait);
        SoakAtResult const r = s.Update({ 1, 2 }, kPoll);
        CHECK(r.step == SoakAtStep::Done);
        CHECK(r.taker == 1 || r.taker == 2);                            // a tie: either (both at 2 s)

        SoakAt t(2000, 0);
        for (int i = 0; i < 4; ++i)
            t.Update({ 1 }, kPoll);                                     // 1 s ahead
        for (int i = 0; i < 3; ++i)
            CHECK(t.Update({ 1, 2 }, kPoll).step == SoakAtStep::Wait);
        SoakAtResult const first = t.Update({ 1, 2 }, kPoll);
        CHECK(first.step == SoakAtStep::Done && first.taker == 1);
    }

    // Nobody comes in 8 s: it expires (Ruuzlu's Execute, UK7). Life 0: it never does.
    void TestExpire()
    {
        SoakAt s(2000, 8000);
        SoakAtResult r;
        CHECK(s.LeftMs() == 8000);
        CHECK(RunUntilOver(s, {}, 20000, r) == 8000);
        CHECK(r.step == SoakAtStep::Expire && r.taker == 0);

        // Someone arrives too late to finish.
        SoakAt late(2000, 8000);
        for (int i = 0; i < 28; ++i)                                    // 7 s empty
            late.Update({}, kPoll);
        CHECK(late.LeftMs() == 1000);
        RunUntilOver(late, { 3 }, 5000, r);
        CHECK(r.step == SoakAtStep::Expire);

        // The rescue at the buzzer: the dwell completes on the poll the life runs out.
        SoakAt buzzer(2000, 8000);
        for (int i = 0; i < 24; ++i)                                    // 6 s empty
            buzzer.Update({}, kPoll);
        CHECK(RunUntilOver(buzzer, { 4 }, 5000, r) == 2000);
        CHECK(r.step == SoakAtStep::Done && r.taker == 4);
        CHECK(buzzer.AgeMs() == 8000);

        SoakAt forever(2000, 0);
        CHECK(RunUntilOver(forever, {}, 600000, r) == 0);
        CHECK(forever.LeftMs() == 0 && !forever.Over());
    }

    // Dwell 0: on touch.
    void TestTouch()
    {
        SoakAt s(0, 8000);
        CHECK(s.Update({}, kPoll).step == SoakAtStep::Wait);
        SoakAtResult const r = s.Update({ 5 }, kPoll);
        CHECK(r.step == SoakAtStep::Done && r.taker == 5);
    }

    // Two sunk players never rescue each other (heroic UK11 sinks everyone): the anchors and the excluded drop out.
    void TestTakers()
    {
        std::vector<std::uint64_t> const present{ 1, 2, 3, 4 };
        std::vector<std::uint64_t> const takers = SoakAtTakers(present, { 2, 4, 9 });
        CHECK(takers == (std::vector<std::uint64_t>{ 1, 3 }));
        CHECK(SoakAtTakers(present, {}) == present);
        CHECK(SoakAtTakers({}, { 1 }).empty());

        // Everyone else sunk: nobody holds it, it expires.
        SoakAt s(2000, 8000);
        SoakAtResult r;
        CHECK(RunUntilOver(s, SoakAtTakers({ 1, 2 }, { 1, 2 }), 10000, r) == 8000);
        CHECK(r.step == SoakAtStep::Expire);
    }
}

int main()
{
    TestHeld();
    TestBreak();
    TestExpire();
    TestTouch();
    TestTakers();
    return Report("kit_soak_test");
}
