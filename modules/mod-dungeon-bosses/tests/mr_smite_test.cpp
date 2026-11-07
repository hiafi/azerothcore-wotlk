// Host tests for MrSmiteLogic.h (WP-B5): the weapon order (never the same weapon twice), the swap thresholds, the
// dash chain's distinct targets, the leap and debris picks, and the dash geometry.
#include "MrSmiteLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace MrSmite;

namespace
{
    // A deterministic pick(n): a linear congruential sequence, so a seed sweep covers many orders.
    struct SeqPick
    {
        std::uint32_t state;

        std::size_t operator()(std::size_t n)
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<std::size_t>((state >> 8) % n);
        }
    };

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        CHECK(kSlice.first == 205290u);
        CHECK(kSlice.last == 205319u);
        for (std::uint32_t id = SPELL_SMITE_SWEEPING_SLASH; id <= SPELL_SMITE_SLASH_TANK; ++id)
            CHECK(kSlice.Contains(id));
    }

    void TestWeaponOrder()
    {
        bool sawHammerFirst = false;
        bool sawHarpoonFirst = false;
        for (bool hammerFirst : { true, false })
        {
            auto const order = WeaponOrder(hammerFirst);
            CHECK(order[0] == Weapon::Cutlasses);
            // never the same weapon twice: the three phases use three different weapons
            std::set<Weapon> seen(order.begin(), order.end());
            CHECK(seen.size() == kWeaponCount);
            for (std::size_t i = 1; i < order.size(); ++i)
                CHECK(order[i] != order[i - 1]);
            CHECK(order[1] != Weapon::Cutlasses && order[2] != Weapon::Cutlasses);
            sawHammerFirst = sawHammerFirst || order[1] == Weapon::Hammer;
            sawHarpoonFirst = sawHarpoonFirst || order[1] == Weapon::Harpoon;
            CHECK(WeaponForPhase(order, 0) == Weapon::Cutlasses);
            CHECK(WeaponForPhase(order, 1) == order[1]);
            CHECK(WeaponForPhase(order, 2) == order[2]);
            CHECK(WeaponForPhase(order, 7) == order[2]);
        }
        CHECK(sawHammerFirst && sawHarpoonFirst);

        // the equipment ids of creature_equip_template 646
        CHECK(static_cast<int>(Weapon::Cutlasses) == 2);
        CHECK(static_cast<int>(Weapon::Hammer) == 3);
        CHECK(static_cast<int>(Weapon::Harpoon) == 4);
    }

    void TestSwapDue()
    {
        CHECK(!SwapDue(100.f, 0));
        CHECK(!SwapDue(67.f, 0));
        CHECK(SwapDue(66.9f, 0) == std::size_t(0));
        CHECK(SwapDue(20.f, 0) == std::size_t(0));      // one swap at a time: the 34% swap waits for the first
        CHECK(!SwapDue(50.f, 1));
        CHECK(!SwapDue(34.f, 1));
        CHECK(SwapDue(33.9f, 1) == std::size_t(1));
        CHECK(!SwapDue(1.f, 2));                        // two swaps per fight, both difficulties
    }

    std::vector<Candidate> Party()
    {
        // four non-tanks around a boss at the origin (the tank is never a candidate)
        return {
            { 11, { 12.f, 0.f } },
            { 12, { -15.f, 3.f } },
            { 13, { 2.f, 20.f } },
            { 14, { 4.f, -3.f } },      // close to the boss: never a first dash unless nobody is far enough
        };
    }

    void TestDashChainDistinct()
    {
        std::vector<Candidate> const party = Party();
        for (std::uint32_t seed = 1; seed <= 200; ++seed)
        {
            SeqPick pick{ seed };
            Vec2 from{ 0.f, 0.f };
            std::vector<std::uint64_t> chain;
            for (int dash = 0; dash < 3; ++dash)
            {
                auto const i = PickDashTarget(party, from, chain, kDashMinDistance, pick);
                CHECK(i.has_value());
                if (!i)
                    break;
                Candidate const& c = party[*i];
                // a new target every dash
                CHECK(std::find(chain.begin(), chain.end(), c.id) == chain.end());
                // at least 8 yd from where the dash starts while such a target is left
                bool farLeft = false;
                for (Candidate const& o : party)
                    if (std::find(chain.begin(), chain.end(), o.id) == chain.end()
                        && DeadminesKit::Distance(from, o.pos) >= kDashMinDistance)
                        farLeft = true;
                if (farLeft)
                    CHECK(DeadminesKit::Distance(from, c.pos) >= kDashMinDistance);
                chain.push_back(c.id);
                // the next dash starts where this one ended
                Vec2 const end = DashEnd(from, c.pos, kDashMinDistance, 0.f);
                CHECK(DeadminesKit::Distance(from, end) >= kDashMinDistance - 0.01f);
                from = end;
            }
            std::set<std::uint64_t> distinct(chain.begin(), chain.end());
            CHECK(distinct.size() == 3u);
        }
    }

    void TestDashChainSmallGroups()
    {
        // two non-tanks: dashes 1 and 2 hit both, dash 3 goes to someone other than dash 2's target
        std::vector<Candidate> const two{ { 21, { 10.f, 0.f } }, { 22, { -10.f, 0.f } } };
        for (std::uint32_t seed = 1; seed <= 50; ++seed)
        {
            SeqPick pick{ seed };
            std::vector<std::uint64_t> chain;
            Vec2 from{ 0.f, 0.f };
            for (int dash = 0; dash < 3; ++dash)
            {
                auto const i = PickDashTarget(two, from, chain, kDashMinDistance, pick);
                CHECK(i.has_value());
                if (!i)
                    break;
                if (!chain.empty())
                    CHECK(two[*i].id != chain.back());
                from = DashEnd(from, two[*i].pos, kDashMinDistance, 0.f);
                chain.push_back(two[*i].id);
            }
            CHECK(chain.size() == 3u && chain[0] != chain[1] && chain[1] != chain[2]);
        }

        // one non-tank: every dash goes to them; nobody: no dash
        std::vector<Candidate> const one{ { 31, { 9.f, 0.f } } };
        SeqPick pick{ 7 };
        std::vector<std::uint64_t> chain{ 31 };
        auto const again = PickDashTarget(one, Vec2{ 9.f, 0.f }, chain, kDashMinDistance, pick);
        CHECK(again && *again == 0u);
        CHECK(!PickDashTarget(std::vector<Candidate>{}, Vec2{}, chain, kDashMinDistance, pick));

        // nobody 8 yd away: the farthest one not yet picked
        std::vector<Candidate> const close{ { 41, { 3.f, 0.f } }, { 42, { 0.f, 5.f } }, { 43, { -1.f, 1.f } } };
        auto const farthest = PickDashTarget(close, Vec2{}, {}, kDashMinDistance, pick);
        CHECK(farthest && close[*farthest].id == 42u);
        auto const next = PickDashTarget(close, Vec2{}, { 42 }, kDashMinDistance, pick);
        CHECK(next && close[*next].id == 41u);
    }

    void TestLeapAndDebris()
    {
        std::vector<Candidate> const party = Party();
        for (std::uint32_t seed = 1; seed <= 100; ++seed)
        {
            SeqPick pick{ seed };
            auto const leap = PickLeapTarget(party, Vec2{}, kHammerDropMinDistance, pick);
            CHECK(leap.has_value());
            if (!leap)
                continue;
            CHECK(DeadminesKit::Distance(Vec2{}, party[*leap].pos) >= kHammerDropMinDistance);

            std::uint64_t const target = party[*leap].id;
            auto const debris = PickOthers(party, target, kDebrisCount.heroic, pick);
            CHECK(debris.size() == 3u);
            std::set<std::uint64_t> ids;
            for (std::size_t i : debris)
            {
                CHECK(party[i].id != target);
                ids.insert(party[i].id);
            }
            CHECK(ids.size() == debris.size());
        }

        // fewer others than circles: one circle each, no repeats
        std::vector<Candidate> const two{ { 1, { 10.f, 0.f } }, { 2, { -10.f, 0.f } } };
        SeqPick pick{ 3 };
        auto const debris = PickOthers(two, 1, 3, pick);
        CHECK(debris.size() == 1u && two[debris[0]].id == 2u);
        CHECK(kDebrisCount.normal == 0u);
    }

    void TestGeometryAndTimers()
    {
        // a target 20 yd away: the dash ends on it
        Vec2 const end = DashEnd(Vec2{ 0.f, 0.f }, Vec2{ 20.f, 0.f }, kDashMinDistance, 0.f);
        CHECK(Near(end.x, 20.f) && Near(end.y, 0.f));
        // a target 2 yd away: an 8 yd dash through it
        Vec2 const shortEnd = DashEnd(Vec2{ 1.f, 1.f }, Vec2{ 1.f, 3.f }, kDashMinDistance, 0.f);
        CHECK(Near(shortEnd.x, 1.f) && Near(shortEnd.y, 9.f));
        // a target on the boss: along the facing
        Vec2 const onTop = DashEnd(Vec2{ 0.f, 0.f }, Vec2{ 0.f, 0.f }, kDashMinDistance, 0.f);
        CHECK(Near(onTop.x, 8.f) && Near(onTop.y, 0.f));

        CHECK(DashChainMs(kDashCount.normal) == 2000u);
        CHECK(DashChainMs(kDashCount.heroic) == 5000u);
        CHECK(DashChainMs(0) == 0u);
        CHECK(kDashFollowWarnMs == kFollowUpWarnMs);

        // the harpoon's two abilities alternate (5 and 10 s, both every 14 s): never at the same time
        for (std::uint32_t t = 0; t < 120000; t += 14000)
            CHECK(kSweepFirstMs + t + kSweepWarnMs + kFollowUpWarnMs <= kVolleyFirstMs + t
                || kVolleyFirstMs + t + kVolleyWarnMs <= kSweepFirstMs + t);
        CHECK(kVolleyRadius.normal == 6.f && kVolleyRadius.heroic == 8.f);
        CHECK(!kBackswing.normal && kBackswing.heroic);
        CHECK(!kAftershocks.normal && kAftershocks.heroic);
        CHECK(!kHaftSlam.normal && kHaftSlam.heroic);

        // Hammer Drop: the cast bar plus a 1 s leap fill the 2.5 s marker
        CHECK(kHammerDropCastMs + 1000u == kHammerDropWarnMs);
    }

    // SM2 / SM3 tank hit: in front for Sweeping Slash, behind for Backswing (90 degrees, 8 yd plus reach).
    void TestSlashArc()
    {
        float constexpr pi = 3.14159265358979323846f;
        Vec2 const smite{ 0.f, 0.f };
        CHECK(InSlashArc(smite, 0.f, Vec2{ 5.f, 0.f }, false, 0.f));
        CHECK(!InSlashArc(smite, 0.f, Vec2{ 5.f, 0.f }, true, 0.f));
        CHECK(InSlashArc(smite, 0.f, Vec2{ -5.f, 0.f }, true, 0.f));
        CHECK(!InSlashArc(smite, 0.f, Vec2{ -5.f, 0.f }, false, 0.f));
        CHECK(InSlashArc(smite, 0.f, Vec2{ -5.f, 4.9f }, true, 0.f));      // 44.4 degrees off the rear axis
        CHECK(!InSlashArc(smite, 0.f, Vec2{ -5.f, 5.2f }, true, 0.f));     // 46 degrees off
        CHECK(!InSlashArc(smite, 0.f, Vec2{ 0.f, 5.f }, true, 0.f));       // at his side: neither arc
        CHECK(!InSlashArc(smite, 0.f, Vec2{ 0.f, 5.f }, false, 0.f));
        CHECK(!InSlashArc(smite, 0.f, Vec2{ -9.f, 0.f }, true, 0.f));      // beyond 8 yd
        CHECK(InSlashArc(smite, 0.f, Vec2{ -9.f, 0.f }, true, 1.5f));      // within reach
        CHECK(InSlashArc(smite, pi, Vec2{ 5.f, 0.f }, true, 0.f));         // facing pi: the rear is +x
    }
}

int main()
{
    TestSlice();
    TestWeaponOrder();
    TestSwapDue();
    TestDashChainDistinct();
    TestDashChainSmallGroups();
    TestLeapAndDebris();
    TestGeometryAndTimers();
    TestSlashArc();
    return Report("mr_smite_test");
}
