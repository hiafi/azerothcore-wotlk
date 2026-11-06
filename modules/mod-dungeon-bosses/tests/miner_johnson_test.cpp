// Host tests for MinerJohnsonLogic.h (WP-B2): Payday's spot, pick and cap, the pouch's launch timing, the catcher pick
// and Gold Fever's threshold.
#include "MinerJohnsonLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace MinerJohnson;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A scripted random source: returns the queued values in order (each taken modulo n, as urand(0, n - 1) would
    // bound it), then 0.
    struct Scripted
    {
        std::vector<std::uint32_t> values;
        std::size_t next = 0;

        std::uint32_t operator()(std::uint32_t n)
        {
            std::uint32_t const v = next < values.size() ? values[next++] : 0;
            return n ? v % n : 0;
        }
    };

    void TestSlice()
    {
        CHECK(kSlice.first == 205230u);
        CHECK(kSlice.Contains(kSlice.last));
        CHECK(SPELL_PAY_POUCH == 205230u);
        CHECK(SPELL_PAYDAY_GLINT == 205231u);
        CHECK(SPELL_POCKETED == 205232u);
        CHECK(SPELL_GOLD_FEVER == 205233u);
        CHECK(SPELL_GOLD_FEVER_TINT == 205234u);
        CHECK(kSlice.Contains(SPELL_GOLD_FEVER_TINT));
    }

    void TestTuning()
    {
        // DM Build spec MJ1: 1 / 2 pouches, 2.5 / 2 s flight, first 8 s, every 20 s, Soak 2 yd, 1 body, 3 yd out.
        CHECK(kPouchCount(false) == 1u && kPouchCount(true) == 2u);
        CHECK(kPouchFlightMs(false) == 2500u && kPouchFlightMs(true) == 2000u);
        CHECK(kPaydayFirstMs == 8000u && kPaydayEveryMs == 20000u);
        CHECK(Near(kSoakRadius, 2.f) && kSoakBodies == 1 && Near(kSpotOffset, 3.f));
        // MJ4: 10 s Pierce Armor window, timers 1-7 s then 20-25 s.
        CHECK(kPierceDurationMs == 10000u);
        CHECK(kPierceFirstMinMs == 1000u && kPierceFirstMaxMs == 7000u);
        CHECK(kPierceEveryMinMs == 20000u && kPierceEveryMaxMs == 25000u);
        // MJ2 15 s; MJ5 heroic only at 30%.
        CHECK(kPocketedMs == 15000u);
        CHECK(kGoldFeverBelowPct(false) == 0u && kGoldFeverBelowPct(true) == 30u);
        // The crew is set up after the instance's 500 ms despawn of an absent Johnson.
        CHECK(kCrewSetupDelayMs > 500u);
    }

    void TestSpot()
    {
        // 3 yd from the miner toward the target.
        Vec2 const s = PaydaySpot({ 0.f, 0.f }, { 10.f, 0.f });
        CHECK(Near(s.x, 3.f) && Near(s.y, 0.f));
        Vec2 const d = PaydaySpot({ 1.f, 1.f }, { 1.f, -9.f });
        CHECK(Near(d.x, 1.f) && Near(d.y, -2.f));
        // Never past the target, and a miner on the target keeps his own spot.
        Vec2 const close = PaydaySpot({ 0.f, 0.f }, { 2.f, 0.f });
        CHECK(Near(close.x, 2.f) && Near(close.y, 0.f));
        Vec2 const same = PaydaySpot({ 4.f, 5.f }, { 4.f, 5.f });
        CHECK(Near(same.x, 4.f) && Near(same.y, 5.f));

        // The crew spots: 3 yd from each miner, on Johnson's side, and every Soak circle inside the room's reach of
        // Johnson (closer to him than its miner by exactly 3 yd).
        Vec2 const home{ kJohnsonHome.x, kJohnsonHome.y };
        for (std::size_t i = 0; i < kCrewSize; ++i)
        {
            Vec2 const miner{ kCrew[i].x, kCrew[i].y };
            Vec2 const spot = CrewSpot(i);
            CHECK(Near(DeadminesKit::Distance(miner, spot), kSpotOffset));
            CHECK(Near(DeadminesKit::Distance(home, spot), DeadminesKit::Distance(home, miner) - kSpotOffset));
            // Two spots never overlap (one pouch, one circle to read).
            for (std::size_t j = i + 1; j < kCrewSize; ++j)
                CHECK(DeadminesKit::Distance(spot, CrewSpot(j)) > 2.f * kSoakRadius);
        }
        // The crew stands where the stock miners stood (DM: 6.6, 7.6, 7.6, 13.9 yd from Johnson).
        CHECK(Near(DeadminesKit::Distance(home, { kCrew[0].x, kCrew[0].y }), 6.63f, 0.05f));
        CHECK(Near(DeadminesKit::Distance(home, { kCrew[3].x, kCrew[3].y }), 13.87f, 0.05f));
        CHECK(kStockMinerSpawnIds[0] == 79194u && kStockMinerSpawnIds[3] == 79185u);
    }

    void TestLaunchDelay()
    {
        // 8 yd at 8 yd/s is a 1 s flight: a 2.5 s warning launches it after 1.5 s.
        CHECK(LaunchDelayMs(2500, 8.f) == 1500u);
        CHECK(LaunchDelayMs(2000, 8.f) == 1000u);
        CHECK(LaunchDelayMs(2500, 0.f) == 2500u);
        // A flight longer than the warning leaves at once.
        CHECK(LaunchDelayMs(2000, 20.f) == 0u);
        CHECK(LaunchDelayMs(2000, 16.f) == 0u);
        CHECK(LaunchDelayMs(2000, 8.f, 0.f) == 0u);
        // Every crew spot is reachable within the heroic 2 s from Johnson's spawn, so the pouch always lands on time.
        Vec2 const home{ kJohnsonHome.x, kJohnsonHome.y };
        for (std::size_t i = 0; i < kCrewSize; ++i)
        {
            float const d = DeadminesKit::Distance(home, CrewSpot(i));
            CHECK(d / kPouchSpeed * 1000.f < static_cast<float>(kPouchFlightMs(true)));
            CHECK(LaunchDelayMs(kPouchFlightMs(true), d) > 0u);
        }
    }

    void TestPouchCount()
    {
        CHECK(PouchCount(false, 4) == 1u);
        CHECK(PouchCount(true, 4) == 2u);
        CHECK(PouchCount(true, 1) == 1u);     // the last digging miner takes the only pouch
        CHECK(PouchCount(true, 0) == 0u);     // nobody left: Payday stops
        CHECK(PouchCount(false, 0) == 0u);
    }

    void TestPickDistinct()
    {
        // Scripted picks map through the shrinking pool.
        Scripted a{ { 2, 0 } };
        std::vector<std::size_t> p = PickDistinct(4, 2, a);
        CHECK(p.size() == 2u && p[0] == 2u && p[1] == 1u);

        // Two picks are always different miners, for every random sequence.
        for (std::uint32_t x = 0; x < 8; ++x)
            for (std::uint32_t y = 0; y < 8; ++y)
            {
                Scripted r{ { x, y } };
                std::vector<std::size_t> const q = PickDistinct(4, 2, r);
                CHECK(q.size() == 2u && q[0] != q[1] && q[0] < 4u && q[1] < 4u);
            }

        // Capped by the miners available; none when nobody digs.
        Scripted b{ { 5, 5, 5 } };
        std::vector<std::size_t> const one = PickDistinct(1, 2, b);
        CHECK(one.size() == 1u && one[0] == 0u);
        Scripted c{};
        CHECK(PickDistinct(0, 2, c).empty());

        // Every miner can be picked (uniform over the pool).
        std::set<std::size_t> seen;
        for (std::uint32_t x = 0; x < 4; ++x)
        {
            Scripted r{ { x } };
            seen.insert(PickDistinct(4, 1, r)[0]);
        }
        CHECK(seen.size() == 4u);
    }

    void TestCatcher()
    {
        CHECK(PickCatcher({}) == -1);
        CHECK(PickCatcher({ 1.5f }) == 0);
        CHECK(PickCatcher({ 1.5f, 0.2f, 1.9f }) == 1);
        CHECK(PickCatcher({ 0.5f, 0.5f }) == 0);    // a tie goes to the first listed
    }

    void TestGoldFever()
    {
        CHECK(!GoldFeverDue(false, 10.f));          // normal: never
        CHECK(!GoldFeverDue(true, 30.f));
        CHECK(GoldFeverDue(true, 29.9f));
        CHECK(!GoldFeverDue(true, 80.f));
    }
}

int main()
{
    TestSlice();
    TestTuning();
    TestSpot();
    TestLaunchDelay();
    TestPouchCount();
    TestPickDistinct();
    TestCatcher();
    TestGoldFever();
    return Report("miner_johnson_test");
}
