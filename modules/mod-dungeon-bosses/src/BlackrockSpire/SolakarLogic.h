/*
 * mod-dungeon-bosses, Blackrock Spire B11:
 * Solakar Flamewreath (10264), the pure, host-testable part (no engine headers). Build spec: docs/dungeons/
 * blackrock-spire-rework.md "Solakar Flamewreath" (SP 2791-3111, SK1-SK12, rulings 55-58), handoff section 3.4 rows SK,
 * 3.5 row B11, 3.6, 3.8 (the Rookery). Tested by tests/brs_solakar_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsSolakar (210390-210429), declared in apps/dbc-tools
 *                source/npcs/blackrock_spire/solakar.py (the toss item 70610:
 *                source/world/blackrock_spire_father_flame.py)
 *   Heat         SK4 Searing Heat by size and difficulty (the heat table), Scorched Hands, the bots' hold times
 *   Flamewreath  SK8 the stack meter shared by a Reclaim and a torn wound, its cap and the enrage
 *   Catch        SK5 who may catch (not Scorched; heroic: the wounded may), SK11 the 2 s sear
 *   FightClock   the Hunt (SK9), War Stomp (SK10, never during a Hunt) and Spear Wound (SK11, halfway between Hunts)
 *   Eggs         the clutches (the stock eggs chained within 3 yd, split at 4 yd), the hatch picks, the whelp cap
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_SOLAKAR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_SOLAKAR_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <vector>

namespace BrsSolakar
{
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsSolakar;

    enum SolakarSpells : std::uint32_t
    {
        SPELL_SK_FATHER_FLAME       = kSpellSlice.first + 0,    // 210390 SK4 the holder aura (the flame in hand)
        SPELL_SK_TOSS               = kSpellSlice.first + 1,    // 210391 SK5 item 70610's on-use toss (0.75 s flight)
        SPELL_SK_SEARING_HEAT       = kSpellSlice.first + 2,    // 210392 SK4 the holder's burn (a self tick, flat)
        SPELL_SK_SCORCHED_HANDS     = kSpellSlice.first + 3,    // 210393 SK5 the thrower cannot catch
        SPELL_SK_CATCH_FLARE        = kSpellSlice.first + 4,    // 210394 SK6 the catch's flare (look)
        SPELL_SK_HATCH_BURST        = kSpellSlice.first + 5,    // 210395 SK6 a hatching egg's burst (look)
        SPELL_SK_HATCHER_HATCH      = kSpellSlice.first + 6,    // 210396 SK2 the Hatcher at its clutch (look)
        SPELL_SK_STOLEN_FLAME       = kSpellSlice.first + 7,    // 210397 SK2 the flame the Hatcher carries
        SPELL_SK_FLAMEWREATH        = kSpellSlice.first + 8,    // 210398 SK8 normal: +20% damage done a stack
        SPELL_SK_FLAMEWREATH_H      = kSpellSlice.first + 9,    // 210399 SK8 heroic: +25% a stack
        SPELL_SK_WREATHED           = kSpellSlice.first + 10,   // 210400 SK8 the enrage (on him)
        SPELL_SK_WREATHED_TICK      = kSpellSlice.first + 11,   // 210401 SK8 the enrage's 10% every 2 s
        SPELL_SK_HUNT_ROAR          = kSpellSlice.first + 12,   // 210402 SK9 the 1.5 s roar (a cast bar)
        SPELL_SK_HUNT               = kSpellSlice.first + 13,   // 210403 SK9 the 8 s Hunt (on him: the bots' tell)
        SPELL_SK_HUNTED             = kSpellSlice.first + 14,   // 210404 SK9 the hunted holder (debuff)
        SPELL_SK_WAR_STOMP_BAR      = kSpellSlice.first + 15,   // 210405 SK10 the 2 s bar
        SPELL_SK_WAR_STOMP          = kSpellSlice.first + 16,   // 210406 SK10 the hit (resolve copy, Physical)
        SPELL_SK_STOMP_LOOK         = kSpellSlice.first + 17,   // 210407 SK3 / SK10 the stomp (look)
        SPELL_SK_WAR_STOMP_STUN     = kSpellSlice.first + 18,   // 210408 SK10 the 2 s stun rider
        SPELL_SK_GROUND_STOMP_BAR   = kSpellSlice.first + 19,   // 210409 SK3 the Guardian's 2 s bar
        SPELL_SK_GROUND_STOMP       = kSpellSlice.first + 20,   // 210410 SK3 the hit (resolve copy, Physical)
        SPELL_SK_SPEAR_THROW        = kSpellSlice.first + 21,   // 210411 SK11 heroic: the spear in flight
        SPELL_SK_SPEAR_WOUND        = kSpellSlice.first + 22,   // 210412 SK11 heroic: the bleed (12 s, then it tears)
        SPELL_SK_SPEAR_TEAR         = kSpellSlice.first + 23,   // 210413 SK11 heroic: the torn wound's 40%
        SPELL_SK_CAUTERIZE          = kSpellSlice.first + 24,   // 210414 SK11 heroic: the wound seared shut (look)
        // 210415-210429 spare
    };
    static_assert(SPELL_SK_CAUTERIZE <= kSpellSlice.last, "Solakar's spells must stay in his slice");

    // The stock casts the pair keeps (SmartAI timers, moved into C++).
    inline constexpr std::uint32_t SPELL_STRIKE = 15580;
    inline constexpr std::uint32_t SPELL_SUNDER_ARMOR = 15572;

    // The one flame is BlackrockSpireRework::kItemFatherFlame (70610, a bag item; the toss is its on-use spell). The
    // stock off-hand 13371 is only the keepsake (kItemFatherFlameKeepsake).
    // "Flame Circle" 185555 (type 5, display 410: _visuals.py GODI_FLAME_CIRCLE, 5.5 yd across): the floor flame's
    // look.
    inline constexpr std::uint32_t GO_FLOOR_FLAME = 185555;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum SolakarTags : std::uint32_t
    {
        TAG_GROUND_STOMP    = 3,    // SK3
        TAG_EGG_CLUTCH      = 6,    // SK6 a clutch's zone (no damage, no marker; the pass counts them)
        TAG_FLOOR_FLAME     = 7,    // SK7 the floor and brazier pickups
        TAG_HUNT_RING       = 9,    // SK9 the red ring on the hunted holder (a decoy: bots never see it)
        TAG_WAR_STOMP       = 10,   // SK10
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_solakar_flamewreath_blackrock_spire.sql).
    enum SolakarTexts : std::uint8_t
    {
        TEXT_ARRIVAL        = 0,    // yell "Thieves in the Rookery! ..." (SK1)
        TEXT_HUNT           = 1,    // emote "%s hunts the flame!" (SK9)
        TEXT_RECLAIM        = 2,    // boss emote "%s reclaims Father Flame!" (SK8)
        TEXT_WREATHED       = 3,    // boss emote "%s is wreathed in flame!" (SK8 enrage)
        TEXT_SPEAR_RETURNS  = 4,    // emote "%s's spear returns to him, bloodied." (SK11 tear)
    };
    enum HatcherTexts : std::uint8_t
    {
        TEXT_HATCHER_INTRUDERS  = 0,    // stock yell (the instance says it at the summon)
        TEXT_HATCHER_SNATCH     = 1,    // emote "%s snatches Father Flame!" (SK2)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Size and difficulty
    // ----------------------------------------------------------------------------------------------------------------

    // "6 or more players" (ruling 56; the flex count held at the pull, a preview before it).
    constexpr bool IsBig(std::uint32_t players)
    {
        return players >= 6;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK4 Searing Heat and SK5 Scorched Hands: the heat table (ruling 56)
    // ----------------------------------------------------------------------------------------------------------------

    struct HeatRamp
    {
        float firstPct;     // the first second's burn
        float risePct;      // added every further second held
    };

    // | | First | Rise | Over 6 s | Scorched |
    // | Normal, 5 | 1% | 0.5% | 13.5% | 15 s |    | Normal, 6+ | 2% | 1% | 27% | 25 s |
    // | Heroic, 5 | 1% | 1% | 21% | 10 s |        | Heroic, 6+ | 2% | 1.5% | 34.5% | 25 s |
    constexpr HeatRamp HeatFor(bool heroic, bool big)
    {
        if (heroic)
            return big ? HeatRamp{ 2.f, 1.5f } : HeatRamp{ 1.f, 1.f };
        return big ? HeatRamp{ 2.f, 1.f } : HeatRamp{ 1.f, 0.5f };
    }

    // The burn of the `tick`-th second held (1-based), in percent of the holder's reference row. It never stops
    // rising (ruling 57): only a toss or the holder's death ends it.
    constexpr float SearingHeatPct(bool heroic, bool big, std::uint32_t tick)
    {
        HeatRamp const r = HeatFor(heroic, big);
        return tick == 0 ? 0.f : r.firstPct + r.risePct * static_cast<float>(tick - 1);
    }

    // The sum of the first `seconds` ticks (the table's "over a 6 sec hold").
    constexpr float SearingHeatTotalPct(bool heroic, bool big, std::uint32_t seconds)
    {
        float total = 0.f;
        for (std::uint32_t t = 1; t <= seconds; ++t)
            total += SearingHeatPct(heroic, big, t);
        return total;
    }

    // Seconds an unhealed holder at full health lives through (the table's "unhealed death").
    constexpr std::uint32_t SecondsToBurnOut(bool heroic, bool big)
    {
        std::uint32_t s = 0;
        while (SearingHeatTotalPct(heroic, big, s) < 100.f && s < 600)
            ++s;
        return s;
    }

    constexpr std::uint32_t ScorchedHandsMs(bool heroic, bool big)
    {
        if (big)
            return 25000;
        return heroic ? 10000 : 15000;
    }

    inline constexpr std::uint32_t kSearingHeatTickMs = 1000;

    // The bots' throw by hold time (SP Bots: "after holding 6 / 4 sec (normal at 5 / 6 or more) and 4 / 3 sec
    // (heroic)"), and the catch's flight (0.75 s at about 25 yd: PassEntry::Flight with a margin).
    constexpr std::uint32_t ThrowHoldMs(bool heroic, bool big)
    {
        if (heroic)
            return big ? 3000 : 4000;
        return big ? 4000 : 6000;
    }
    inline constexpr float kTossRangeYd = 30.f;
    inline constexpr float kTossSpeed = 33.f;               // yd/s: 0.75 s at 25 yd (SP "about 0.75 sec")
    inline constexpr std::uint32_t kTossFlightMs = 1000;    // the pass's Flight (30 yd: 0.91 s)
    inline constexpr float kThrowTriggerYd = 15.f;          // SP: he (or the Hatcher) within 15 yd
    inline constexpr float kUrgentThrowYd = 5.f;            // a hunting Solakar this close beats the wound's sear
    inline constexpr float kCatcherKeepFromYd = 15.f;
    inline constexpr float kCatchEggYd = 4.f;               // SK6: eggs within 4 yd of the catcher hatch
    inline constexpr FlexAB kReadyCatchers{ 1, 2 };

    // ----------------------------------------------------------------------------------------------------------------
    // SK5 who may catch; SK11 the sear
    // ----------------------------------------------------------------------------------------------------------------

    // Not Scorched; on heroic a wounded player catches even while Scorched.
    constexpr bool CanCatch(bool scorched, bool wounded, bool heroic)
    {
        return !scorched || (heroic && wounded);
    }

    inline constexpr std::uint32_t kSearMs = 2000;          // holding 2 s in total sears a Spear Wound shut
    inline constexpr std::uint32_t kSpearWoundMs = 12000;   // then it tears
    inline constexpr float kSpearBleedPct = 1.f;            // a second
    inline constexpr float kSpearTearPct = 40.f;
    inline constexpr FlexAB kSpearTargets{ 1, 2 };

    // ----------------------------------------------------------------------------------------------------------------
    // SK8 Flamewreath, Reclaim, Wreathed in Flame
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kFlamewreathPctPerStack{ 20.f, 25.f };
    inline constexpr std::uint32_t kFlamewreathCap = 3;
    inline constexpr float kWreathedPct = 10.f;             // the enrage: everyone, every 2 s, unavoidable
    inline constexpr std::uint32_t kWreathedTickMs = 2000;

    // Every hit he deals is raised by his stacks (SP: "+20% damage on everything he does"; the custom spells ignore
    // caster modifiers, so the script multiplies their percents; his melee takes the aura).
    constexpr float WreathMult(bool heroic, std::uint32_t stacks)
    {
        return 1.f + kFlamewreathPctPerStack(heroic) / 100.f * static_cast<float>(std::min(stacks, kFlamewreathCap));
    }

    struct WreathStep
    {
        std::uint32_t stacks;   // after the step
        bool enrage;            // this step lit Wreathed in Flame
    };

    // A Reclaim or a torn wound: +1 stack up to 3; one more at 3 is the enrage (once).
    constexpr WreathStep AddWreath(std::uint32_t stacks, bool enraged)
    {
        if (stacks < kFlamewreathCap)
            return { stacks + 1, false };
        return { kFlamewreathCap, !enraged };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK7 / SK8 the flame off a hand
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kPickupRadiusYd = 4.f;
    inline constexpr std::uint32_t kFloorFlameMs = 6000;    // then he leaves the tank for it
    inline constexpr std::uint32_t kBrazierFlameMs = 10000;
    inline constexpr std::uint32_t kRunPickupMs = 60000;    // while he runs for it, it can still be taken
    inline constexpr float kFloorEggYd = 6.f;               // SK7: eggs within 6 yd of a dropped flame hatch
    inline constexpr float kReclaimReachYd = 2.5f;          // he takes it this close
    // R-2 m-5: a run that has not reached the flame in its budget (a spot off his path: a ledge, a pillar's edge)
    // takes it in place, a Reclaim, so an unreachable flame never leaves him a free target. The budget is the straight
    // run at his speed with half again for the path, plus a grace (the Rookery's 105 yd diagonal at his 10 yd/s:
    // about 20 s; a flame 5 yd off: about 4.8 s).
    inline constexpr std::uint32_t kRunGraceMs = 4000;

    constexpr std::uint64_t RunBudgetMs(float startYd, float speedYdS)
    {
        float const speed = speedYdS > 1.f ? speedYdS : 1.f;
        float const yd = startYd > 0.f ? startYd : 0.f;
        return static_cast<std::uint64_t>(yd / speed * 1500.f) + kRunGraceMs;
    }

    constexpr bool RunGivesUp(std::uint64_t startedMs, std::uint64_t budgetMs, std::uint64_t nowMs)
    {
        return nowMs >= startedMs + budgetMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SK1 / SK2 / SK3 the opening
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kGroundStompFirstMs = 6000;
    inline constexpr std::uint32_t kGroundStompEveryMs = 12000;
    inline constexpr std::uint32_t kStompCastMs = 2000;
    inline constexpr float kStompRadiusYd = 8.f;
    inline constexpr float kGroundStompPct = 20.f;
    inline constexpr std::uint32_t kStrikeFirstMinMs = 5000;
    inline constexpr std::uint32_t kStrikeFirstMaxMs = 7000;
    inline constexpr std::uint32_t kStrikeMinMs = 4000;
    inline constexpr std::uint32_t kStrikeMaxMs = 6000;
    inline constexpr std::uint32_t kSunderFirstMinMs = 10000;
    inline constexpr std::uint32_t kSunderFirstMaxMs = 12000;
    inline constexpr std::uint32_t kSunderMinMs = 10000;
    inline constexpr std::uint32_t kSunderMaxMs = 15000;
    inline constexpr std::uint32_t kTossPauseMs = 1000;     // each toss stops the Hatcher (and the Hunt) 1 s
    inline constexpr float kSnatchReachYd = 2.5f;
    inline constexpr float kHatcherClutchYd = 6.f;          // SK2: every egg within 6 yd of its clutch hatches
    inline constexpr std::uint32_t kHatcherClutchMinEggs = 3;
    inline constexpr float kClutchArriveYd = 1.5f;
    inline constexpr std::uint32_t kOpeningWipeMs = 10000;  // nobody alive in the Rookery this long: the event fails

    // ----------------------------------------------------------------------------------------------------------------
    // SK9 the Hunt, SK10 War Stomp, SK11 Spear Wound: the fight's clock
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kHuntFirstMs = 10000;
    inline constexpr NH<std::uint32_t> kHuntEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kHuntRoarMs = 1500;
    inline constexpr std::uint32_t kHuntChaseMs = 8000;
    inline constexpr std::uint32_t kStompFirstMs = 15000;
    inline constexpr std::uint32_t kStompEveryMs = 20000;
    inline constexpr std::uint32_t kStompAfterHuntMs = 1000;    // a stomp due in a Hunt waits for its end + 1 s
    inline constexpr float kWarStompPct = 25.f;
    inline constexpr std::uint32_t kWarStompStunMs = 2000;
    inline constexpr std::uint32_t kSpearAfterHuntMs = 10000;   // heroic: halfway between Hunts (SK11)
    inline constexpr std::uint32_t kRetryMs = 1000;             // a Hunt with nobody holding the flame waits

    enum class Beat : std::uint8_t
    {
        None,
        Hunt,
        Stomp,
        Spear,
    };

    // The fight's three beats after his arrival. The Hunt runs from its roar to the end of its chase; a War Stomp
    // never starts inside it (nor a Hunt inside a stomp's bar); a heroic Spear Wound comes 10 s after each Hunt
    // starts (halfway between Hunts, so a late Hunt moves it too).
    class FightClock
    {
    public:
        static constexpr std::uint64_t kNever = std::numeric_limits<std::uint64_t>::max() / 2;

        void Start(bool heroic)
        {
            _heroic = heroic;
            _nextHunt = kHuntFirstMs;
            _nextStomp = kStompFirstMs;
            _nextSpear = kNever;
            _huntUntil = 0;
            _stompUntil = 0;
        }

        // The beat due at `now` (ms since his arrival), if any; `free`: he is on his tank (not running for a dropped
        // flame), `holder`: someone holds the flame (a Hunt needs one).
        Beat Next(std::uint64_t now, bool free, bool holder) const
        {
            if (_heroic && now >= _nextSpear)
                return Beat::Spear;
            bool const inHunt = now < _huntUntil;
            bool const inStomp = now < _stompUntil;
            if (now >= _nextHunt && !inHunt && !inStomp && free && holder)
                return Beat::Hunt;
            if (now >= _nextStomp && !inHunt && !inStomp && free && now >= _huntUntil + StompGap())
                return Beat::Stomp;
            return Beat::None;
        }

        // Book the beat started at `now`.
        void Started(Beat beat, std::uint64_t now)
        {
            switch (beat)
            {
                case Beat::Hunt:
                    _huntUntil = now + kHuntRoarMs + kHuntChaseMs;
                    _nextHunt = now + kHuntEveryMs(_heroic);
                    if (_heroic)
                        _nextSpear = now + kSpearAfterHuntMs;
                    break;
                case Beat::Stomp:
                    _stompUntil = now + kStompCastMs;
                    _nextStomp = now + kStompEveryMs;
                    break;
                case Beat::Spear:
                    _nextSpear = kNever;    // the next Hunt books the next one
                    break;
                case Beat::None:
                    break;
            }
        }

        // The Hunt ended early (a Reclaim, the holder gone).
        void HuntEnded(std::uint64_t now)
        {
            _huntUntil = std::min(_huntUntil, now);
        }

        // A Hunt due with nobody holding: try again in a second.
        void HuntWaits(std::uint64_t now)
        {
            _nextHunt = std::max(_nextHunt, now + kRetryMs);
        }

        bool InHunt(std::uint64_t now) const { return now < _huntUntil; }
        std::uint64_t NextHunt() const { return _nextHunt; }
        std::uint64_t NextStomp() const { return _nextStomp; }
        std::uint64_t NextSpear() const { return _nextSpear; }
        std::uint64_t HuntUntil() const { return _huntUntil; }

    private:
        // A stomp waits for the Hunt's end plus a second (only once a Hunt has run).
        std::uint64_t StompGap() const { return _huntUntil ? kStompAfterHuntMs : 0; }

        bool _heroic = false;
        std::uint64_t _nextHunt = kHuntFirstMs;
        std::uint64_t _nextStomp = kStompFirstMs;
        std::uint64_t _nextSpear = kNever;
        std::uint64_t _huntUntil = 0;
        std::uint64_t _stompUntil = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // SK6 the eggs: clutches, hatch picks, the whelp cap
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kEggLinkYd = 3.f;        // eggs within 3 yd chain into one clutch (NM 10: 33 clutches)
    inline constexpr float kClutchMaxYd = 4.f;      // a chain wider than this (about its centroid) is split
    inline constexpr float kEggTrapYd = 1.5f;       // the stock egg trap's radius (diameter 3, spell 15745)
    inline constexpr float kEggSearchYd = 75.f;     // the egg search about the Rookery's middle
    inline constexpr FlexAB kWhelpCap{ 6, 12 };     // flame whelps alive at once (SK6)
    inline constexpr std::uint32_t kEggPollMs = 1000;
    inline constexpr std::uint32_t kEggHatchedRespawnSec = 7200;    // a hatched egg stays gone (the reset brings it
                                                                    // back)
    inline constexpr std::uint32_t kClutchZoneMinutes = 60;         // a clutch zone outlasts any fight

    struct Clutch
    {
        Vec2 center;
        float radius = 0.f;                 // the farthest egg from the center (0 for a lone egg)
        std::vector<std::size_t> eggs;      // indices into the egg list
    };

    // The registry zone of a clutch: its spread plus the trap's own radius.
    constexpr float ClutchZoneRadius(float spread)
    {
        return spread + kEggTrapYd;
    }

    namespace Detail
    {
        inline Vec2 Centroid(std::span<Vec2 const> eggs, std::vector<std::size_t> const& members)
        {
            Vec2 c;
            for (std::size_t i : members)
            {
                c.x += eggs[i].x;
                c.y += eggs[i].y;
            }
            float const n = static_cast<float>(std::max<std::size_t>(members.size(), 1));
            return { c.x / n, c.y / n };
        }

        inline float Spread(std::span<Vec2 const> eggs, std::vector<std::size_t> const& members, Vec2 c)
        {
            float r = 0.f;
            for (std::size_t i : members)
                r = std::max(r, DungeonKit::Distance(eggs[i], c));
            return r;
        }

        // A chain too wide is cut at the median of its longer axis until every part fits.
        inline void Emit(std::span<Vec2 const> eggs, std::vector<std::size_t> members, float maxYd,
            std::vector<Clutch>& out)
        {
            Vec2 const c = Centroid(eggs, members);
            float const spread = Spread(eggs, members, c);
            if (members.size() <= 1 || spread <= maxYd)
            {
                out.push_back({ c, spread, std::move(members) });
                return;
            }
            float minX = eggs[members[0]].x;
            float maxX = minX;
            float minY = eggs[members[0]].y;
            float maxY = minY;
            for (std::size_t i : members)
            {
                minX = std::min(minX, eggs[i].x);
                maxX = std::max(maxX, eggs[i].x);
                minY = std::min(minY, eggs[i].y);
                maxY = std::max(maxY, eggs[i].y);
            }
            bool const alongX = maxX - minX >= maxY - minY;
            std::sort(members.begin(), members.end(), [&](std::size_t a, std::size_t b)
            {
                float const ka = alongX ? eggs[a].x : eggs[a].y;
                float const kb = alongX ? eggs[b].x : eggs[b].y;
                return ka != kb ? ka < kb : a < b;
            });
            std::size_t const half = members.size() / 2;
            Emit(eggs, std::vector<std::size_t>(members.begin(), members.begin() + half), maxYd, out);
            Emit(eggs, std::vector<std::size_t>(members.begin() + half, members.end()), maxYd, out);
        }
    }

    // The clutches of `eggs`: chained within `linkYd` (union-find), each chain split until it spreads at most `maxYd`
    // about its centroid. Deterministic (by egg index).
    inline std::vector<Clutch> BuildClutches(std::span<Vec2 const> eggs, float linkYd = kEggLinkYd,
        float maxYd = kClutchMaxYd)
    {
        std::vector<std::size_t> parent(eggs.size());
        for (std::size_t i = 0; i < eggs.size(); ++i)
            parent[i] = i;
        auto find = [&parent](std::size_t i)
        {
            while (parent[i] != i)
            {
                parent[i] = parent[parent[i]];
                i = parent[i];
            }
            return i;
        };
        for (std::size_t i = 0; i < eggs.size(); ++i)
            for (std::size_t j = i + 1; j < eggs.size(); ++j)
                if (DungeonKit::Distance(eggs[i], eggs[j]) <= linkYd)
                    parent[find(j)] = find(i);

        std::size_t constexpr kNone = std::numeric_limits<std::size_t>::max();
        std::vector<std::vector<std::size_t>> chains;
        std::vector<std::size_t> chainOf(eggs.size(), kNone);
        for (std::size_t i = 0; i < eggs.size(); ++i)
        {
            std::size_t const root = find(i);
            if (chainOf[root] == kNone)
            {
                chainOf[root] = chains.size();
                chains.emplace_back();
            }
            chains[chainOf[root]].push_back(i);
        }
        std::vector<Clutch> out;
        for (std::vector<std::size_t>& chain : chains)
            Detail::Emit(eggs, std::move(chain), maxYd, out);
        return out;
    }

    // A clutch's live part: its center and spread over the live eggs (`live[i]`); no live egg: nullopt.
    inline std::optional<Clutch> LivePart(std::span<Vec2 const> eggs, std::vector<bool> const& live, Clutch const& c)
    {
        std::vector<std::size_t> members;
        for (std::size_t i : c.eggs)
            if (live[i])
                members.push_back(i);
        if (members.empty())
            return std::nullopt;
        Vec2 const center = Detail::Centroid(eggs, members);
        return Clutch{ center, Detail::Spread(eggs, members, center), std::move(members) };
    }

    // The live eggs within `r` yd of `p`, nearest first.
    inline std::vector<std::size_t> EggsWithin(std::span<Vec2 const> eggs, std::vector<bool> const& live, Vec2 p,
        float r)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < eggs.size(); ++i)
            if (live[i] && DungeonKit::Distance(eggs[i], p) <= r)
                out.push_back(i);
        std::sort(out.begin(), out.end(), [&](std::size_t a, std::size_t b)
        {
            float const da = DungeonKit::Distance(eggs[a], p);
            float const db = DungeonKit::Distance(eggs[b], p);
            return da != db ? da < db : a < b;
        });
        return out;
    }

    // The live egg nearest `p` (the Reclaim's stir: one per player).
    inline std::optional<std::size_t> NearestEgg(std::span<Vec2 const> eggs, std::vector<bool> const& live, Vec2 p)
    {
        std::optional<std::size_t> best;
        float bestD = 0.f;
        for (std::size_t i = 0; i < eggs.size(); ++i)
        {
            if (!live[i])
                continue;
            float const d = DungeonKit::Distance(eggs[i], p);
            if (!best || d < bestD)
            {
                best = i;
                bestD = d;
            }
        }
        return best;
    }

    // The Hatcher's run (SK2): the clutch with at least `minEggs` live eggs nearest `p` (by its live center).
    inline std::optional<Vec2> NearestClutch(std::span<Vec2 const> eggs, std::vector<bool> const& live,
        std::span<Clutch const> clutches, Vec2 p, std::uint32_t minEggs = kHatcherClutchMinEggs)
    {
        std::optional<Vec2> best;
        float bestD = 0.f;
        for (Clutch const& c : clutches)
        {
            std::optional<Clutch> const part = LivePart(eggs, live, c);
            if (!part || part->eggs.size() < minEggs)
                continue;
            float const d = DungeonKit::Distance(part->center, p);
            if (!best || d < bestD)
            {
                best = part->center;
                bestD = d;
            }
        }
        return best;
    }
}

#endif
