// Host tests for CookieLogic.h (WP-B6): the dish order (never the same twice in a row; two different dishes on
// heroic), the eater count, the timers against the registry's persistent passes, Seasoned and the knockback.
#include "CookieLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>

using namespace Cookie;

namespace
{
    bool Near(float a, float b, float eps = 1e-3f)
    {
        return std::fabs(a - b) <= eps;
    }

    // A small LCG so the walks are deterministic and cover many rolls.
    struct Lcg
    {
        std::uint32_t s = 12345u;
        std::uint32_t operator()()
        {
            s = s * 1664525u + 1013904223u;
            return s >> 8;  // an LCG's low bits cycle; the real rolls (rand32) do not
        }
    };

    void TestSlice()
    {
        CHECK(kSlice.first == 205320u);
        CHECK(kSlice.Contains(kSlice.last));
        std::uint32_t const ids[] = { SPELL_CHOWDER_DEBUFF, SPELL_CHOWDER_BREATH_VISUAL, SPELL_CHOWDER_BREATH,
            SPELL_PEPPER_BURN, SPELL_STEW_DEBUFF, SPELL_STEW_VOMIT_VISUAL, SPELL_STEW_PUDDLE,
            SPELL_STEW_PUDDLE_VISUAL_NORMAL, SPELL_STEW_PUDDLE_VISUAL_HEROIC, SPELL_GUT_BOMB_DEBUFF,
            SPELL_GUT_BOMB_BELCH, SPELL_GUT_BOMB_EATER, SPELL_GUT_BOMB_VISUAL, SPELL_COOKIES_COOKING_NORMAL,
            SPELL_COOKIES_COOKING_HEROIC, SPELL_SEASONED };
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : ids)
        {
            CHECK(kSlice.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(kCookingSpell(false) == SPELL_COOKIES_COOKING_NORMAL);
        CHECK(kCookingSpell(true) == SPELL_COOKIES_COOKING_HEROIC);
        CHECK(kStewPuddleVisual(true) == SPELL_STEW_PUDDLE_VISUAL_HEROIC);
    }

    void TestPickExcept()
    {
        for (std::uint32_t r = 0; r < 12; ++r)
        {
            CHECK(PickExcept(Dish::None, r) == DishAt(r % 3));
            for (std::uint32_t e = 0; e < kDishCount; ++e)
            {
                Dish const d = PickExcept(DishAt(e), r);
                CHECK(d != DishAt(e));
                CHECK(d != Dish::None);
            }
        }
        // Both of the other two dishes are reachable.
        for (std::uint32_t e = 0; e < kDishCount; ++e)
            CHECK(PickExcept(DishAt(e), 0) != PickExcept(DishAt(e), 1));
    }

    // Normal: one dish per course, never the same as the course before; every dish served over a long walk.
    void TestNormalOrder()
    {
        Lcg rng;
        Dish key = Dish::None;
        Dish last = Dish::None;
        std::uint32_t served[kDishCount] = {};
        for (int i = 0; i < 2000; ++i)
        {
            Course const c = PickCourse(false, key, rng());
            CHECK(c.count == 1);
            CHECK(c.dishes[0] != Dish::None);
            CHECK(c.dishes[1] == Dish::None);
            CHECK(c.dishes[0] != last);
            CHECK(c.key == c.dishes[0]);
            ++served[static_cast<std::uint32_t>(c.dishes[0])];
            last = c.dishes[0];
            key = c.key;
        }
        for (std::uint32_t d = 0; d < kDishCount; ++d)
            CHECK(served[d] > 500);     // about 667 each
        // The first course may be any dish.
        std::set<Dish> first;
        for (std::uint32_t r = 0; r < 3; ++r)
            first.insert(PickCourse(false, Dish::None, r).dishes[0]);
        CHECK(first.size() == 3);
    }

    // Heroic: two different dishes per course, never the same pair twice in a row (the left-out dish changes), and
    // each dish reaches both eater slots.
    void TestHeroicOrder()
    {
        Lcg rng;
        Dish key = Dish::None;
        Dish lastLeftOut = Dish::None;
        std::uint32_t slot[2][kDishCount] = {};
        for (int i = 0; i < 2000; ++i)
        {
            Course const c = PickCourse(true, key, rng());
            CHECK(c.count == 2);
            CHECK(c.dishes[0] != Dish::None);
            CHECK(c.dishes[1] != Dish::None);
            CHECK(c.dishes[0] != c.dishes[1]);
            CHECK(c.key != c.dishes[0] && c.key != c.dishes[1] && c.key != Dish::None);
            CHECK(c.key != lastLeftOut);
            ++slot[0][static_cast<std::uint32_t>(c.dishes[0])];
            ++slot[1][static_cast<std::uint32_t>(c.dishes[1])];
            lastLeftOut = c.key;
            key = c.key;
        }
        for (std::uint32_t s = 0; s < 2; ++s)
            for (std::uint32_t d = 0; d < kDishCount; ++d)
                CHECK(slot[s][d] > 400);    // about 667 each
    }

    void TestEaters()
    {
        CHECK(EatersFor(false, 0) == 0);
        CHECK(EatersFor(false, 1) == 1);
        CHECK(EatersFor(false, 4) == 1);
        CHECK(EatersFor(true, 0) == 0);
        CHECK(EatersFor(true, 1) == 1);
        CHECK(EatersFor(true, 2) == 2);
        CHECK(EatersFor(true, 4) == 2);
    }

    void TestNamesAndTexts()
    {
        for (std::uint32_t i = 0; i < kDishCount; ++i)
            CHECK(ParseDish(DishName(DishAt(i))) == DishAt(i));
        CHECK(ParseDish("soup") == Dish::None);
        CHECK(FeedTextGroup(Dish::Chowder) == 0);
        CHECK(FeedTextGroup(Dish::Stew) == 2);
        CHECK(FeedTextGroup(Dish::GutBomb) == 3);
        CHECK(YELL_AGGRO == 1);
        CHECK(DishDebuffSpell(Dish::Chowder) == SPELL_CHOWDER_DEBUFF);
        CHECK(DishDebuffSpell(Dish::Stew) == SPELL_STEW_DEBUFF);
        CHECK(DishDebuffSpell(Dish::GutBomb) == SPELL_GUT_BOMB_DEBUFF);
    }

    void TestTimers()
    {
        // 3 breaths at 2, 4, 6 s after the feed: one persistent cone, 2 s warning, a pass every 2 s.
        CHECK(kChowderPersistMs == 5000);
        CHECK(PersistentPasses(kChowderPersistMs, kChowderBreathEveryMs) == kChowderBreaths);
        CHECK(kDishLeadMs + (kChowderBreaths - 1) * kChowderBreathEveryMs == kChowderDebuffMs);
        // Puddles tick once a second for their whole life: 30 ticks normal, 60 heroic.
        CHECK(PersistentPasses(kStewPuddleMs(false), kStewTickMs) == 30);
        CHECK(PersistentPasses(kStewPuddleMs(true), kStewTickMs) == 60);
        CHECK(PersistentPasses(1000, 0) == 1);
        // The last drop is when the stew debuff ends.
        CHECK(kDishLeadMs + (kStewDrops - 1) * kStewDropEveryMs == kStewDebuffMs);
        // Gut Bomb: 5 s normal, 4 s heroic; the debuff is the countdown.
        CHECK(DishDebuffMs(Dish::GutBomb, false) == 5000);
        CHECK(DishDebuffMs(Dish::GutBomb, true) == 4000);
        CHECK(DishDebuffMs(Dish::Chowder, true) == 6000);
        CHECK(DishDebuffMs(Dish::Stew, false) == 6000);
        // A 60 s normal fight sees 4 feeds (6, 21, 36, 51 s); every dish is over before the next feed.
        std::uint32_t feeds = 0;
        for (std::uint32_t t = kFeedFirstMs; t < 60000; t += kFeedEveryMs)
            ++feeds;
        CHECK(feeds == 4);
        CHECK(kChowderDebuffMs < kFeedEveryMs);
        CHECK(kGutBombDelayMs(false) < kFeedEveryMs);
        // Warning floor (DM Tuning): at least 2 s before a breath or puddle, 4 to 5 s before the belch.
        CHECK(kDishLeadMs >= 2000);
        CHECK(kGutBombDelayMs(true) >= 4000);
    }

    void TestNumbers()
    {
        CHECK(Near(kChowderPct(false), 25.f) && Near(kChowderPct(true), 25.f));
        CHECK(Near(kStewPct(false), 10.f) && Near(kStewPct(true), 15.f));
        CHECK(Near(kPepperBurnPctPerTick * kPepperBurnTicks, 30.f));
        // Seasoned: +10% per stack on the dishes too; DM Tuning's capped normal numbers.
        CHECK(Near(SeasonedFactor(0), 1.f));
        CHECK(Near(SeasonedPct(25.f, 3), 32.5f));
        CHECK(Near(SeasonedPct(30.f, 3), 39.f));
        CHECK(Near(SeasonedPct(15.f, 10), 30.f));
        // Cap 3 normal, 10 heroic (ruling 31): past it a cast only heals.
        CHECK(AddsSeasonedStack(0, false));
        CHECK(AddsSeasonedStack(2, false));
        CHECK(!AddsSeasonedStack(3, false));
        CHECK(AddsSeasonedStack(3, true));
        CHECK(AddsSeasonedStack(9, true));
        CHECK(!AddsSeasonedStack(10, true));
        CHECK(!AddsSeasonedStack(11, true));
        // RefFlat on the reference rows (kit math): the eater's 15% normal 195, heroic 618.
        CHECK(DeadminesKit::RefFlatValue(1300, 1290, kGutBombEaterPct, false) == 195u);
        CHECK(DeadminesKit::RefFlatValue(4120, 4110, kGutBombEaterPct, false) == 618u);
        CHECK(DeadminesKit::RefFlatValue(4120, 4110, kPepperBurnPctPerTick, false) == 206u);
    }

    void TestKnockback()
    {
        float const v = KnockbackSpeedXY(kGutBombKnockbackYd, kGutBombKnockbackSpeedZ);
        CHECK(Near(v, 11.5747f, 1e-3f));
        CHECK(Near(KnockbackDistance(v, kGutBombKnockbackSpeedZ), kGutBombKnockbackYd));
        CHECK(KnockbackSpeedXY(6.f, 0.f) == 0.f);
    }
}

int main()
{
    TestSlice();
    TestPickExcept();
    TestNormalOrder();
    TestHeroicOrder();
    TestEaters();
    TestNamesAndTexts();
    TestTimers();
    TestNumbers();
    TestKnockback();
    return Report("cookie_test");
}
