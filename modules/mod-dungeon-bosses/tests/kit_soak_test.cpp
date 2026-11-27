// Host tests for the shared dungeon kit's held Soaks (Zul'Farrak WP-KT, F36; SP UK6, the 2 s rescue):
// DungeonKitSoakLogic.h (SoakAt, SoakAtTakers), polled every 250 ms as DwellSoaks polls it; Gnomeregan WP-KT-G (F40):
// the rank order of held Soaks (SoakRankAt, SoakPriorityOrder, SoakRegisterMask).
#include "DungeonKitSoakLogic.h"
#include "check.h"
#include <algorithm>
#include <cstddef>
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

    // Gnomeregan WP-KT-G (F40): where a ranked Soak goes, and the Reprioritize order.
    void TestRankAt()
    {
        CHECK(SoakRankAt({}, 3) == 0);
        CHECK(SoakRankAt({ 0, 1, 1, 4 }, 1) == 3);      // after the equal ones (they came first)
        CHECK(SoakRankAt({ 0, 1, 1, 4 }, 0) == 1);
        CHECK(SoakRankAt({ 0, 1, 1, 4 }, 5) == 4);
        CHECK(SoakRankAt({ 2, 3 }, -1) == 0);

        CHECK(SoakPriorityOrder({ 1, 2, 3, 4 }, { 3, 1 }) == (std::vector<std::uint32_t>{ 3, 1, 2, 4 }));
        CHECK(SoakPriorityOrder({ 1, 2, 3 }, { 9, 2, 2 }) == (std::vector<std::uint32_t>{ 2, 1, 3 }));
        CHECK(SoakPriorityOrder({ 1, 2 }, {}) == (std::vector<std::uint32_t>{ 1, 2 }));
        CHECK(SoakPriorityOrder({}, { 1 }).empty());
    }

    // Unranked: exactly the old rule (the changed ones and the new one). Ranked: everything from the first on.
    void TestRegisterMask()
    {
        std::vector<bool> const changed{ false, true, false, true, false };
        CHECK(SoakRegisterMask(false, 5, changed) == (std::vector<bool>{ false, true, false, true, false }));
        CHECK(SoakRegisterMask(false, 4, changed) == (std::vector<bool>{ false, true, false, true, true }));
        CHECK(SoakRegisterMask(true, 5, changed) == (std::vector<bool>{ false, true, true, true, true }));
        CHECK(SoakRegisterMask(true, 0, std::vector<bool>(3, false)) == (std::vector<bool>{ true, true, true }));
        CHECK(SoakRegisterMask(true, 3, std::vector<bool>(3, false)) == (std::vector<bool>{ false, false, false }));
        CHECK(SoakRegisterMask(true, 2, std::vector<bool>(3, false)) == (std::vector<bool>{ false, false, true }));
    }

    // The registry serves an exclusive group earliest resolve (registration time + the same whole-fight warning)
    // first, then the lowest id. A ranked set kept in rank order and re-registered by SoakRegisterMask is served in
    // rank order after any run of adds, carrier changes, cancels and reprioritizations (Thermaplugg's plates: six
    // faces, Locked Out changing the carriers of every plate at each touch).
    void TestRankedServeOrder()
    {
        struct Sim
        {
            std::uint32_t id = 0;
            std::int32_t rank = 0;
            std::uint32_t regTime = 0;
            std::uint32_t regId = 0;
        };
        std::uint32_t seed = 12345;
        auto rnd = [&seed](std::uint32_t n) { seed = seed * 1103515245u + 12345u; return (seed >> 16) % n; };

        std::vector<Sim> set;
        std::uint32_t nextId = 1;
        std::uint32_t nextReg = 1;
        int bad = 0;
        for (std::uint32_t t = 1; t <= 4000; ++t)
        {
            std::vector<bool> changed(set.size(), false);
            std::size_t from = set.size();
            std::uint32_t const op = rnd(10);
            if (op < 3 && set.size() < 6)
            {
                Sim s;
                s.id = nextId++;
                s.rank = static_cast<std::int32_t>(rnd(6));       // the face priority
                std::vector<std::int32_t> ranks;
                for (Sim const& x : set)
                    ranks.push_back(x.rank);
                from = SoakRankAt(ranks, s.rank);
                set.insert(set.begin() + static_cast<std::ptrdiff_t>(from), s);
                changed.insert(changed.begin() + static_cast<std::ptrdiff_t>(from), true);
            }
            else if (op < 5 && !set.empty())
            {
                set.erase(set.begin() + static_cast<std::ptrdiff_t>(rnd(static_cast<std::uint32_t>(set.size()))));
                changed.assign(set.size(), false);
                from = set.size();
            }
            else if (op < 8)
            {
                for (std::size_t i = 0; i < changed.size(); ++i)
                    changed[i] = rnd(2) == 0;                    // a touch locks one player out of some plates
            }
            else if (!set.empty())
            {
                std::vector<std::uint32_t> ids;
                for (Sim const& x : set)
                    ids.push_back(x.id);
                std::vector<std::uint32_t> order{ ids[rnd(static_cast<std::uint32_t>(ids.size()))] };
                std::vector<std::uint32_t> const sorted = SoakPriorityOrder(ids, order);
                std::vector<Sim> next;
                for (std::size_t i = 0; i < sorted.size(); ++i)
                    for (Sim x : set)
                        if (x.id == sorted[i])
                        {
                            x.rank = static_cast<std::int32_t>(std::min<std::size_t>(i, 1));
                            next.push_back(x);
                        }
                set = next;
                changed.assign(set.size(), false);
                from = 0;
            }
            std::vector<bool> const mask = SoakRegisterMask(true, from, changed);
            for (std::size_t i = 0; i < set.size(); ++i)
                if (mask[i])
                {
                    set[i].regTime = t;
                    set[i].regId = nextReg++;
                }
            // Served order == the set's order, and the set is in rank order.
            for (std::size_t i = 1; i < set.size(); ++i)
            {
                Sim const& a = set[i - 1];
                Sim const& b = set[i];
                bool const servedFirst = a.regTime < b.regTime || (a.regTime == b.regTime && a.regId < b.regId);
                if (!servedFirst || a.rank > b.rank)
                    ++bad;
            }
        }
        CHECK(bad == 0);
    }
}

int main()
{
    TestHeld();
    TestBreak();
    TestExpire();
    TestTouch();
    TestTakers();
    TestRankAt();
    TestRegisterMask();
    TestRankedServeOrder();
    return Report("kit_soak_test");
}
