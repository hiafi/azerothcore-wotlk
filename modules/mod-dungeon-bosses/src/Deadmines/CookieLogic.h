/*
 * mod-dungeon-bosses, Deadmines: Cookie (WP-B6), the pure, host-testable part (no engine headers): spell ids, per-
 * difficulty tuning numbers, timers, the dish order and the small formulas. Build spec: DM 'Cookie' Build spec CK1-CK6,
 * corrected by deadmines-pilot.HANDOFF.md section 3.4 (Fish Stew is a RunOut per drop plus a lingering puddle, not a
 * Bait: section 8 #7).
 *
 * Taste Test (CK3): every 15 s from 6 s, Cookie feeds a random non-tank a dish; on heroic two players at once, two
 * different dishes. The dish order rule ("never the same twice in a row") is PickCourse below:
 *   - normal: one dish, never the dish of the previous course;
 *   - heroic: two dishes, i.e. one dish left out, and never the same one left out twice in a row, so two courses in a
 *     row never serve the same pair (with three dishes and two per course, some dish always repeats).
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_COOKIE_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_COOKIE_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <utility>

namespace Cookie
{
    using DeadminesKit::NH;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsCookie;

    // apps/dbc-tools source/npcs/deadmines/cookie.py declares every one of these (205336-205339 spare).
    enum CookieSpells : std::uint32_t
    {
        SPELL_CHOWDER_DEBUFF            = 205320,   // the eater's dish debuff, 6 s
        SPELL_CHOWDER_BREATH_VISUAL     = 205321,   // the eater casts it on itself at each breath
        SPELL_CHOWDER_BREATH            = 205322,   // registry resolve copy, Fire
        SPELL_PEPPER_BURN               = 205323,   // heroic rider: 30% Fire over 6 s, Magic
        SPELL_STEW_DEBUFF               = 205324,   // the eater's dish debuff, 6 s
        SPELL_STEW_VOMIT_VISUAL         = 205325,   // the eater casts it on itself at each drop
        SPELL_STEW_PUDDLE               = 205326,   // registry resolve copy, Nature (puddle ticks)
        SPELL_STEW_PUDDLE_VISUAL_NORMAL = 205327,   // ground visual, 30 s (the eater's dynamic object)
        SPELL_STEW_PUDDLE_VISUAL_HEROIC = 205328,   // ground visual, 60 s
        SPELL_GUT_BOMB_DEBUFF           = 205329,   // the eater's dish debuff, 5 s (4 s on heroic)
        SPELL_GUT_BOMB_BELCH            = 205330,   // registry resolve copy, Nature (the others)
        SPELL_GUT_BOMB_EATER            = 205331,   // the eater's own 15%
        SPELL_GUT_BOMB_VISUAL           = 205332,   // the eater casts it on itself at the belch
        SPELL_COOKIES_COOKING_NORMAL    = 205333,   // CK2, 2 s cast, heals 5%
        SPELL_COOKIES_COOKING_HEROIC    = 205334,   // CK2, 2 s cast, heals 8%
        SPELL_SEASONED                  = 205335,   // +10% damage done per stack, for the fight
    };

    // creature_text groups of 645 (WP-B6's layout). Talk() picks a random line within a group, so the build spec's
    // "line 0" (one emote per dish) is one group per dish: group 0 keeps the kit's EMOTE_COOKIE_FEED for the chowder,
    // group 1 is the kit's aggro yell, and the stew and the gut bomb take 2 and 3.
    enum CookieTextGroups : std::uint8_t
    {
        EMOTE_FEED_CHOWDER  = DeadminesRework::EMOTE_COOKIE_FEED,   // 0
        YELL_AGGRO          = DeadminesRework::YELL_COOKIE_AGGRO,   // 1
        EMOTE_FEED_STEW     = DeadminesRework::EMOTE_COOKIE_FEED_STEW,     // 2
        EMOTE_FEED_GUT_BOMB = DeadminesRework::EMOTE_COOKIE_FEED_GUT_BOMB, // 3
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Dishes and the dish order (CK3)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Dish : std::uint8_t
    {
        Chowder = 0,    // CK4 Fire Pepper Chowder
        Stew    = 1,    // CK5 Week-Old Fish Stew
        GutBomb = 2,    // CK6 Gut Bomb
        None    = 3
    };

    inline constexpr std::uint32_t kDishCount = 3;

    inline constexpr Dish DishAt(std::uint32_t i)
    {
        return i < kDishCount ? static_cast<Dish>(i) : Dish::None;
    }

    // One course: one dish (normal) or two different dishes (heroic), dishes[i] for the i-th eater. `key` is what the
    // next course must not repeat: the dish served (normal) or the dish left out (heroic).
    struct Course
    {
        Dish dishes[2] = { Dish::None, Dish::None };
        std::uint8_t count = 0;
        Dish key = Dish::None;
    };

    // One of the two dishes that are not `excluded` (by roll parity); any of the three when `excluded` is None.
    inline Dish PickExcept(Dish excluded, std::uint32_t roll)
    {
        if (excluded == Dish::None || static_cast<std::uint32_t>(excluded) >= kDishCount)
            return DishAt(roll % kDishCount);
        std::uint32_t const n = roll % (kDishCount - 1);
        std::uint32_t const e = static_cast<std::uint32_t>(excluded);
        return DishAt(n < e ? n : n + 1);
    }

    // `previousKey`: the last course's key (None at the pull). `roll`: any random number (rand32()).
    inline Course PickCourse(bool heroic, Dish previousKey, std::uint32_t roll)
    {
        Course c;
        if (!heroic)
        {
            c.dishes[0] = PickExcept(previousKey, roll);
            c.count = 1;
            c.key = c.dishes[0];
            return c;
        }
        Dish const leftOut = PickExcept(previousKey, roll);
        std::uint8_t n = 0;
        for (std::uint32_t i = 0; i < kDishCount; ++i)
            if (DishAt(i) != leftOut)
                c.dishes[n++] = DishAt(i);
        if ((roll / 6u) % 2u)   // which eater gets which dish: another digit of the same roll
            std::swap(c.dishes[0], c.dishes[1]);
        c.count = 2;
        c.key = leftOut;
        return c;
    }

    // How many players a course feeds: 1 (normal) or 2 (heroic), never more than the candidates (the non-tanks).
    inline std::uint8_t EatersFor(bool heroic, std::size_t candidates)
    {
        std::size_t const want = heroic ? 2u : 1u;
        return static_cast<std::uint8_t>(std::min(want, candidates));
    }

    inline char const* DishName(Dish d)
    {
        switch (d)
        {
            case Dish::Chowder: return "chowder";
            case Dish::Stew:    return "stew";
            case Dish::GutBomb: return "gutbomb";
            default:            return "none";
        }
    }

    // `.dmtest cookie feed <dish>`: chowder, stew, gutbomb (None otherwise).
    inline Dish ParseDish(std::string_view s)
    {
        for (std::uint32_t i = 0; i < kDishCount; ++i)
            if (s == DishName(DishAt(i)))
                return DishAt(i);
        return Dish::None;
    }

    inline std::uint8_t FeedTextGroup(Dish d)
    {
        switch (d)
        {
            case Dish::Stew:    return EMOTE_FEED_STEW;
            case Dish::GutBomb: return EMOTE_FEED_GUT_BOMB;
            default:            return EMOTE_FEED_CHOWDER;
        }
    }

    inline std::uint32_t DishDebuffSpell(Dish d)
    {
        switch (d)
        {
            case Dish::Stew:    return SPELL_STEW_DEBUFF;
            case Dish::GutBomb: return SPELL_GUT_BOMB_DEBUFF;
            default:            return SPELL_CHOWDER_DEBUFF;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers and sizes (DM Build spec CK1-CK6; ms and yards)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kFeedFirstMs = 6000;             // CK3 first feed
    inline constexpr std::uint32_t kFeedEveryMs = 15000;            // CK3 cooldown
    inline constexpr std::uint32_t kDishLeadMs = 2000;              // feed -> first breath / first puddle

    inline constexpr std::uint32_t kAcidSplashFirstMinMs = 1000;    // CK1 (the stock SmartAI timers)
    inline constexpr std::uint32_t kAcidSplashFirstMaxMs = 7000;
    inline constexpr std::uint32_t kAcidSplashEveryMinMs = 20000;
    inline constexpr std::uint32_t kAcidSplashEveryMaxMs = 25000;
    inline constexpr std::uint32_t kCookingFirstMinMs = 10000;      // CK2 (the stock SmartAI timers)
    inline constexpr std::uint32_t kCookingFirstMaxMs = 12000;
    inline constexpr std::uint32_t kCookingEveryMinMs = 15000;
    inline constexpr std::uint32_t kCookingEveryMaxMs = 25000;
    inline constexpr std::uint32_t kCastRetryMs = 500;              // a cast event that finds him casting waits this

    // CK4: a 60 degree / 8 yd cone anchored on the eater, turning with them; 3 breaths, one every 2 s.
    inline constexpr float kChowderAngleDeg = 60.f;
    inline constexpr float kChowderLengthYd = 8.f;
    inline constexpr std::uint32_t kChowderBreaths = 3;
    inline constexpr std::uint32_t kChowderBreathEveryMs = 2000;
    inline constexpr NH<float> kChowderPct{ 25.f, 25.f };
    inline constexpr float kPepperBurnPctPerTick = 5.f;             // heroic: 30% over 6 s, 1 s ticks (the data)
    inline constexpr std::uint32_t kPepperBurnTicks = 6;
    inline constexpr std::uint32_t kChowderDebuffMs = 6000;

    // The registry's persistent passes land at the resolve and then every tick while the next tick is before the end
    // (Judge::TakePass): this many passes for Persistent(duration, tick).
    inline constexpr std::uint32_t PersistentPasses(std::uint32_t durationMs, std::uint32_t tickMs)
    {
        return tickMs == 0 ? 1u : std::max<std::uint32_t>(1u, (durationMs + tickMs - 1) / tickMs);
    }

    // The chowder cone's Persistent duration: kChowderBreaths passes, kChowderBreathEveryMs apart (the drill's 5000).
    inline constexpr std::uint32_t kChowderPersistMs = (kChowderBreaths - 1) * kChowderBreathEveryMs + 1000;

    // CK5: 3 drops 2 s apart from 2 s after the feed; a 4 yd RunOut on the eater before each, a 4 yd puddle at each.
    inline constexpr std::uint32_t kStewDrops = 3;
    inline constexpr std::uint32_t kStewDropEveryMs = 2000;
    inline constexpr float kStewRunOutYd = 4.f;
    inline constexpr float kStewPuddleYd = 4.f;
    inline constexpr NH<std::uint32_t> kStewPuddleMs{ 30000, 60000 };
    inline constexpr std::uint32_t kStewTickMs = 1000;
    inline constexpr NH<float> kStewPct{ 10.f, 15.f };              // per tick (per second), no Weakened
    inline constexpr std::uint32_t kStewDebuffMs = 6000;

    // CK6: the belch lands 5 s (normal) / 4 s (heroic) after the feed, 8 yd around the eater.
    inline constexpr NH<std::uint32_t> kGutBombDelayMs{ 5000, 4000 };
    inline constexpr float kGutBombYd = 8.f;
    inline constexpr float kGutBombPct = 30.f;                      // the others, + Weakened
    inline constexpr float kGutBombEaterPct = 15.f;                 // the eater, unavoidable
    inline constexpr float kGutBombKnockbackYd = 6.f;               // heroic, away from the eater
    inline constexpr float kGutBombKnockbackSpeedZ = 5.f;

    // CK2: heal 5% / 8% (in the spells' data); one Seasoned stack per completed cast, cap 3 / 10 (ruling 31).
    inline constexpr NH<std::uint32_t> kSeasonedCap{ 3, 10 };
    inline constexpr float kSeasonedPerStack = 0.10f;

    inline constexpr NH<std::uint32_t> kCookingSpell{ SPELL_COOKIES_COOKING_NORMAL, SPELL_COOKIES_COOKING_HEROIC };
    inline constexpr NH<std::uint32_t> kStewPuddleVisual{ SPELL_STEW_PUDDLE_VISUAL_NORMAL,
        SPELL_STEW_PUDDLE_VISUAL_HEROIC };

    // Failure-ledger tags, the same as mod-boss-mechanics' `cookie` drill (MechanicDrill.h), so sweep keys match.
    inline constexpr std::uint32_t kTagChowder = 4;
    inline constexpr std::uint32_t kTagStewRunOut = 5;
    inline constexpr std::uint32_t kTagGutBomb = 6;
    inline constexpr std::uint32_t kTagStewPuddle = 7;

    // How long the eater's dish debuff lasts: the dish's whole window.
    inline std::uint32_t DishDebuffMs(Dish d, bool heroic)
    {
        switch (d)
        {
            case Dish::Stew:    return kStewDebuffMs;
            case Dish::GutBomb: return kGutBombDelayMs(heroic);
            default:            return kChowderDebuffMs;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Seasoned and the knockback
    // ----------------------------------------------------------------------------------------------------------------

    // "Damage done +10% per stack, his dishes included" (CK2): the registry and script damage ignore caster modifiers,
    // so the script multiplies the percent itself. 3 stacks: a breath 25% -> 32.5%, a belch 30% -> 39% (DM Tuning).
    inline float SeasonedFactor(std::uint32_t stacks)
    {
        return 1.f + kSeasonedPerStack * static_cast<float>(stacks);
    }

    inline float SeasonedPct(float pct, std::uint32_t stacks)
    {
        return pct * SeasonedFactor(stacks);
    }

    // After a completed Cookie's Cooking: true when a stack is added (below the difficulty's cap); past the cap a
    // completed cast only heals (ruling 31).
    inline bool AddsSeasonedStack(std::uint32_t current, bool heroic)
    {
        return current < kSeasonedCap(heroic);
    }

    // Unit::KnockbackFrom's horizontal speed that carries a unit `distance` yards with vertical speed `speedZ`
    // (MotionMaster::MoveKnockbackFrom: distance = 2 * speedXY * speedZ / gravity).
    inline constexpr float kGravity = 19.29110527f;     // Movement::gravity

    inline float KnockbackSpeedXY(float distance, float speedZ)
    {
        return speedZ > 0.f ? distance * kGravity / (2.f * speedZ) : 0.f;
    }

    inline float KnockbackDistance(float speedXY, float speedZ)
    {
        return 2.f * speedXY * speedZ / kGravity;
    }
}

#endif
