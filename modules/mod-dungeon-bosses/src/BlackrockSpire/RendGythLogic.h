/*
 * mod-dungeon-bosses, Blackrock Spire B12:
 * Warchief Rend Blackhand (10429), Gyth (10339) and Lord Victor Nefarius's Blackrock Spire copy (300732), the pure,
 * host-testable part (no engine headers). WP-B12 owns this file: its spell ids (inside kSpellsRendGyth of
 * BlackrockSpireRework.h, 210430-210489), tuning constants, flex target pairs, text groups, timers, picks and geometry,
 * tested by tests/brs_rend_gyth_test.cpp. The engine side is boss_rend_blackhand_rework.cpp (the event runner, Rend,
 * the Nefarius copy, the Dress Hunt whelps, the Banner, the frost wall carrier) and boss_gyth_rework.cpp (Gyth).
 *
 * Build spec: SP "Warchief Rend Blackhand and Gyth" (RG1-RG17, "Tank swap at 10"), handoff section 3.4 rows RG,
 * section 3.5 row B12, the user's rolling front ruling 3 (the heroic second gap within 20 yd of the first). Damage is
 * a percent of the reference row (N = level 60 normal, H = level 60 heroic); counts "a / b" are 5 players / 6 or more
 * (FlexAB).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_REND_GYTH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_REND_GYTH_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>

namespace BrsRendGyth
{
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsRendGyth;

    // apps/dbc-tools source/npcs/blackrock_spire/rend_gyth.py declares every one of them.
    enum RendGythSpells : std::uint32_t
    {
        SPELL_RG_MARK               = 210430,   // RG9 the 4 s tell on the marked player (DUMMY debuff)
        SPELL_RG_FLAME_BREATH       = 210431,   // RG9 / RG10 a breath's hit (resolve copy, Fire)
        SPELL_RG_FLAME_BREATH_LOOK  = 210432,   // RG9 Gyth's breath at the marked player (Flame Breath 16390's SV)
        SPELL_RG_FLAME_BREATH_BAR   = 210433,   // RG10 the riderless breath's 2 s bar (Fire, not interruptible)
        SPELL_RG_FREEZING_SWEEP     = 210434,   // RG6 the wall's hit (resolve copy, Frost)
        SPELL_RG_FROZEN             = 210435,   // RG6 the wall's rider: a 2 s stun
        SPELL_RG_FREEZING_BREATH    = 210436,   // RG6 the breath that sends a wall (Freezing Breath 47415's SV)
        SPELL_RG_SHADOWFLAME        = 210437,   // RG7 the circle's hit (resolve copy, Shadow)
        SPELL_RG_SHADOWFLAME_BURN   = 210438,   // RG7 a pool's burn (the kit's percent spell, Shadow)
        SPELL_RG_SHADOWFLAME_POOL   = 210439,   // RG7 a pool's look, normal: a 6 yd dynamic object for 20 s
        SPELL_RG_SHADOWFLAME_POOL_H = 210440,   // RG7 a pool's look, heroic: 25 s
        SPELL_RG_WHELP_BITE         = 210441,   // RG5 a hunting whelp's bite, normal (the kit's percent spell)
        SPELL_RG_WHELP_BITE_H       = 210442,   // RG5 the same, heroic
        SPELL_RG_HUNTING            = 210443,   // RG5 the hunting whelp's marker (the descriptor's kill priority)
        SPELL_RG_THUMBS_DOWN        = 210444,   // RG8 the skull over the condemned (5 s)
        SPELL_RG_SHADOW_CRASH       = 210445,   // RG8 a share of the split hit (Shadow, the value set by the script)
        SPELL_RG_WHIRLWIND_BAR      = 210446,   // RG11 the 2 s wind-up (Physical)
        SPELL_RG_WHIRLWIND          = 210447,   // RG11 the whirl's tick (resolve copy, Physical)
        SPELL_RG_WHIRLWIND_LOOK     = 210448,   // RG11 the 6 s whirl on Rend (Whirlwind 13736's SV)
        SPELL_RG_BANNER_EMPOWER     = 210449,   // RG12 Rend's buff while a live banner is within 10 yd (DUMMY)
        SPELL_RG_MORTAL_WOUNDS      = 210450,   // RG17 10 players: -10% healing taken per stack
        SPELL_RG_IMPATIENT_HOST     = 210451,   // RG4 the bored host, step 1 (on Nefarius; DUMMY)
        SPELL_RG_BORED_HOST         = 210452,   // RG4 the bored host, step 2
    };
    // 210453-210489 spare.
    std::uint32_t constexpr kFirstSpell = SPELL_RG_MARK;
    std::uint32_t constexpr kLastSpell = SPELL_RG_BORED_HOST;

    // Stock spells kept (SP "Stock kit"; DD scales them on heroic).
    std::uint32_t constexpr SPELL_RG_CORROSIVE_ACID = 16359;    // RG14 / RG16 Gyth's tank breath (armor, Nature)
    std::uint32_t constexpr SPELL_RG_KNOCK_AWAY = 10101;        // RG14
    std::uint32_t constexpr SPELL_RG_REND_MOUNTS = 16167;       // Rend in the saddle (the model swap on Gyth)
    std::uint32_t constexpr SPELL_RG_PROTECTION_FIRE = 16373;   // Chromatic Protection after a breath of that school
    std::uint32_t constexpr SPELL_RG_PROTECTION_NATURE = 16391;
    std::uint32_t constexpr SPELL_RG_PROTECTION_FROST = 16392;
    std::uint32_t constexpr SPELL_RG_MORTAL_STRIKE = 16856;     // RG14 / RG17 Rend's
    std::uint32_t constexpr SPELL_RG_CLEAVE = 15284;            // RG14 Rend's (SP note 9)

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text; the SQL rev rev_rend_gyth_blackrock_spire.sql writes them)
    // ----------------------------------------------------------------------------------------------------------------
    // Nefarius's copy 300732: 0-11 copied from 10162 (3 unused), 12-17 the rounds, 18-19 the insult (DR10, for B15).
    enum NefariusTexts : std::uint8_t
    {
        YELL_NEF_WELCOME        = 0,    // RG1 on the trigger
        YELL_NEF_FEAST          = 1,    // RG1 group 1
        YELL_NEF_DRESS          = 2,    // RG5 "Kill the one in the dress!" (fixed: never fired in stock)
        YELL_NEF_FRUITLESS      = 4,    // RG4 the bored host, step 2
        YELL_NEF_FORCE_MY_HAND  = 5,    // RG4 the bored host, step 1
        YELL_NEF_FREEZING       = 6,    // RG6
        YELL_NEF_CANNOT_BE      = 7,    // RG3 act 3 on the timer
        YELL_NEF_WARCHIEF       = 8,    // RG2
        YELL_NEF_TASTE          = 9,    // RG7
        YELL_NEF_SHORT_LIVED    = 10,   // RG3 Rend's death
        YELL_NEF_MORTALS_FALLEN = 11,   // RG15 a wipe (the instance says it, as stock)
        YELL_NEF_MYSELF         = 12,   // RG6 with Gyth dead
        YELL_NEF_BORES_ME       = 13,   // RG8
        EMOTE_NEF_HUNT          = 14,   // RG5 "Whelps hunt $n!"
        EMOTE_NEF_SWEEP         = 15,   // RG6
        EMOTE_NEF_SHADOWFLAME   = 16,   // RG7
        EMOTE_NEF_THUMBS_DOWN   = 17,   // RG8 "Nefarius turns his thumb down on $n!"
        YELL_NEF_INSULTED       = 18,   // DR10 the first insult (saved)
        SAY_NEF_INSULTED_AGAIN  = 19,   // DR10 later insults
    };
    // Rend 10429: 0-2 stock, 3-4 new.
    enum RendTexts : std::uint8_t
    {
        YELL_REND_IMPOSSIBLE    = 0,    // stock, unused (SP)
        YELL_REND_PLEASURE      = 1,    // RG2
        EMOTE_REND_KNOCKED_OFF  = 2,    // RG3 on Gyth's death
        EMOTE_REND_MARK         = 3,    // RG9 "%s points his polearm at $n!"
        EMOTE_REND_BANNER       = 4,    // RG12
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RG1-RG3 the Program (ms; the act clocks run on the event runner's own clock)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kGroupOneDelayMs = 3000;            // line 0 on the trigger, line 1 + group 1 3 s later
    std::uint32_t constexpr kGroupTwoMs = 15000;                // from group 1 ("0 s")
    std::uint32_t constexpr kActTwoMs = 30000;                  // from group 1, whatever is left
    std::uint32_t constexpr kActTwoLengthMs = 75000;            // RG2 normal (from Gyth's arrival)
    std::uint32_t constexpr kActTwoLengthHeroicMs = 60000;      // RG2 heroic
    inline constexpr FlexAB kGroupWhelps{ 2, 3 };               // RG1 whelps per group (plus 1 Dragonspawn, 1 Handler)
    std::uint32_t constexpr kPortcullisOpenS = 8;               // the drake portcullis stays open this long per call

    constexpr std::uint32_t ActTwoLengthMs(bool heroic)
    {
        return heroic ? kActTwoLengthHeroicMs : kActTwoLengthMs;
    }

    // The event's acts (the runner's state).
    enum class Act : std::uint8_t
    {
        Idle = 0,       // Rend waits on his balcony
        Beasts = 1,     // RG1
        Drake = 2,      // RG2: Gyth with Rend in the saddle
        Warchief = 3,   // RG3: Rend on foot (Gyth beside him on the failing path)
        Over = 4,       // Rend is dead
    };

    constexpr char const* ActName(Act a)
    {
        switch (a)
        {
            case Act::Idle:     return "idle";
            case Act::Beasts:   return "beasts";
            case Act::Drake:    return "drake";
            case Act::Warchief: return "warchief";
            default:            return "over";
        }
    }

    // A wipe: nobody alive (players only, not a GM) on the arena floor for this long while the event runs.
    std::uint32_t constexpr kWipePollMs = 1000;
    std::uint32_t constexpr kWipeGraceMs = 3000;

    // ----------------------------------------------------------------------------------------------------------------
    // RG4 the Rounds and the bored host
    // ----------------------------------------------------------------------------------------------------------------
    enum class Round : std::uint8_t
    {
        DressHunt = 0,      // RG5
        FreezingSweep = 1,  // RG6
        Shadowflame = 2,    // RG7
        ThumbsDown = 3,     // RG8 (heroic)
    };

    constexpr char const* RoundName(Round r)
    {
        switch (r)
        {
            case Round::DressHunt:      return "dress-hunt";
            case Round::FreezingSweep:  return "freezing-sweep";
            case Round::Shadowflame:    return "shadowflame";
            default:                    return "thumbs-down";
        }
    }

    std::uint32_t constexpr kRoundsFirstMs = 10000;             // 10 s into act 2
    std::uint32_t constexpr kRoundMs = 15000;                   // every round lasts 15 s
    std::uint32_t constexpr kRoundEveryMs = 30000;              // normal
    std::uint32_t constexpr kRoundEveryHeroicMs = 10000;        // heroic (the last 5 s of a round overlap the next)
    // The bored host (act 3 only, from Rend's landing): normal past 1:30 every 20 s, past 2:30 two rounds per call;
    // heroic past 1:15 every 7 s, past 2:00 every 5 s.
    std::uint32_t constexpr kBoredOneMs = 90000;
    std::uint32_t constexpr kBoredTwoMs = 150000;
    std::uint32_t constexpr kBoredOneHeroicMs = 75000;
    std::uint32_t constexpr kBoredTwoHeroicMs = 120000;
    std::uint32_t constexpr kBoredEveryMs = 20000;
    std::uint32_t constexpr kBoredOneEveryHeroicMs = 7000;
    std::uint32_t constexpr kBoredTwoEveryHeroicMs = 5000;

    // The rounds in their fixed order: normal RG5, RG6, RG7; heroic RG5, RG6, RG7, RG8.
    constexpr std::uint32_t RoundCount(bool heroic)
    {
        return heroic ? 4u : 3u;
    }

    constexpr Round RoundAt(std::uint32_t index, bool heroic)
    {
        return static_cast<Round>(index % RoundCount(heroic));
    }

    // 0: not bored; 1: the first step (line 5); 2: the second (line 4). `act3Ms`: ms since Rend landed (0 before).
    constexpr std::uint8_t BoredStep(bool heroic, std::uint32_t act3Ms)
    {
        std::uint32_t const one = heroic ? kBoredOneHeroicMs : kBoredOneMs;
        std::uint32_t const two = heroic ? kBoredTwoHeroicMs : kBoredTwoMs;
        return act3Ms >= two ? 2 : act3Ms >= one ? 1 : 0;
    }

    // The gap from one call to the next at `step`.
    constexpr std::uint32_t CallEveryMs(bool heroic, std::uint8_t step)
    {
        if (heroic)
            return step >= 2 ? kBoredTwoEveryHeroicMs : step == 1 ? kBoredOneEveryHeroicMs : kRoundEveryHeroicMs;
        return step >= 1 ? kBoredEveryMs : kRoundEveryMs;
    }

    // Rounds per call: normal past the second step, two at once; otherwise one.
    constexpr std::uint32_t RoundsPerCall(bool heroic, std::uint8_t step)
    {
        return (!heroic && step >= 2) ? 2u : 1u;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG5 Kill the one in the dress
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr FlexAB kHuntWhelps{ 3, 6 };                // normal
    inline constexpr FlexAB kHuntWhelpsHeroic{ 4, 8 };          // heroic
    float constexpr kHuntSpeed = 8.f;                           // yd/s
    float constexpr kHuntReach = 2.5f;                          // yd (2D): at the target, it bites
    std::uint32_t constexpr kBiteEveryMs = 1000;
    float constexpr kBitePct = 3.f;                             // a second, Physical
    float constexpr kBiteHeroicPct = 5.f;

    constexpr std::uint8_t HuntWhelps(bool heroic, std::uint32_t players)
    {
        return heroic ? kHuntWhelpsHeroic.At(players) : kHuntWhelps.At(players);
    }

    // The whelps' targets: split over the healers in turn (each healer at 10); with no healer, all on `fallback` (the
    // player with the least armor). Returns one target id per whelp (empty when nobody qualifies).
    inline std::vector<std::uint64_t> HuntTargets(std::uint32_t whelps, std::vector<std::uint64_t> const& healers,
        std::uint64_t fallback)
    {
        std::vector<std::uint64_t> out;
        if (healers.empty() && !fallback)
            return out;
        for (std::uint32_t i = 0; i < whelps; ++i)
            out.push_back(healers.empty() ? fallback : healers[i % healers.size()]);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG6 Freezing Sweep (the rolling line front: KT-B2's FrontDirector WallSequence)
    // ----------------------------------------------------------------------------------------------------------------
    // The wall starts on the portcullis line (x 194) across the arena's axis (y -420.2) and travels west to the way-in
    // door (x 108): 86 yd. It spans the end bays (68 yd); its gap stays in the 40 yd main strip (handoff section 3.8,
    // NM 11). Heroic: a second wall 3 s later, its gap on the other side and within 20 yd of the first (rolling front
    // ruling 3).
    float constexpr kSweepStartX = 194.f;
    float constexpr kSweepStartY = -420.2f;
    float constexpr kSweepStartZ = 111.f;
    float constexpr kSweepTravelYd = 86.f;
    float constexpr kSweepWidthYd = 68.f;
    float constexpr kSweepSpanYd = 40.f;
    float constexpr kSweepGapYd = 8.f;
    float constexpr kSweepWithinYd = 20.f;
    float constexpr kSweepBandYd = 4.f;
    float constexpr kSweepSpeed = 8.f;
    std::uint32_t constexpr kSweepWarnMs = 3000;                // the wall starts 3 s after the call
    std::uint32_t constexpr kSweepSpacingMs = 3000;             // heroic: 3 s apart
    float constexpr kSweepPct = 25.f;
    std::uint32_t constexpr kFrozenMs = 2000;
    float constexpr kSweepCarrierSpacingYd = 8.f;               // one ice wall piece (scale 0.5: about 8 yd) per 8 yd
    std::uint32_t constexpr kSweepCarrierMax = 10;

    constexpr std::uint32_t SweepWalls(bool heroic)
    {
        return heroic ? 2u : 1u;
    }

    // ms from the call until the last wall is over (KT-B2 Fronts::WallOverMs per wall: the travel at the speed).
    constexpr std::uint32_t SweepOverMs(bool heroic)
    {
        return kSweepWarnMs + (SweepWalls(heroic) - 1) * kSweepSpacingMs
            + static_cast<std::uint32_t>(kSweepTravelYd * 1000.f / kSweepSpeed + 0.999f);
    }

    // Gyth hovers over the portcullis end while the walls roll: up for the warning, down once the last one is past.
    float constexpr kHoverHeightYd = 6.f;
    std::uint32_t constexpr kHoverTailMs = 500;

    constexpr std::uint32_t HoverMs(bool heroic)
    {
        return SweepOverMs(heroic) + kHoverTailMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG7 Taste in my power
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kShadowflameRadius = 6.f;
    std::uint32_t constexpr kShadowflameWarnMs = 3000;
    float constexpr kShadowflamePct = 30.f;                     // in someone else's circle (Weakened)
    std::uint32_t constexpr kPoolMs = 20000;
    std::uint32_t constexpr kPoolHeroicMs = 25000;
    float constexpr kPoolPct = 30.f;                            // on entering and every 2 s inside (no Weakened)
    std::uint32_t constexpr kPoolTickMs = 2000;
    std::uint32_t constexpr kPoolArmMs = 500;

    constexpr std::uint32_t PoolMs(bool heroic)
    {
        return heroic ? kPoolHeroicMs : kPoolMs;
    }

    // A player inside a pool burns now: on entering (no burn yet in this stay), then every kPoolTickMs.
    constexpr bool PoolBurnDue(bool burnedBefore, std::uint64_t sinceLastBurnMs)
    {
        return !burnedBefore || sinceLastBurnMs >= kPoolTickMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG8 Thumbs Down (heroic)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr FlexAB kCondemned{ 1, 2 };
    std::uint32_t constexpr kThumbsWarnMs = 5000;
    float constexpr kThumbsRadius = 8.f;
    float constexpr kThumbsTotalPct = 150.f;                    // split evenly among everyone within 8 yd

    float constexpr kCondemnedApartYd = 16.f;                   // SP RG8: the two condemned (6 or more) 16 yd apart

    struct CondemnCandidate
    {
        std::uint64_t id = 0;
        float healthPct = 100.f;
        std::uint32_t health = 0;
        bool victim = false;                                    // a boss's current target: never condemned
        Vec2 at{};                                              // where they stand (the 16 yd rule)
    };

    // The non-tanks (any boss's current victim excluded; the second tank stays eligible) with the lowest health percent
    // (ties: lower health, then lower id), `count` of them. Each later pick is the lowest one standing at least
    // kCondemnedApartYd from every earlier pick (RG8: two overlapping stacks would charge everyone between twice); when
    // nobody that far is left, the next lowest.
    inline std::vector<std::uint64_t> PickCondemned(std::vector<CondemnCandidate> players, std::uint32_t count)
    {
        std::erase_if(players, [](CondemnCandidate const& c) { return c.victim; });
        std::sort(players.begin(), players.end(), [](CondemnCandidate const& a, CondemnCandidate const& b)
        {
            if (a.healthPct != b.healthPct)
                return a.healthPct < b.healthPct;
            if (a.health != b.health)
                return a.health < b.health;
            return a.id < b.id;
        });
        std::vector<std::uint64_t> out;
        std::vector<Vec2> picked;
        std::vector<bool> used(players.size(), false);
        while (out.size() < count)
        {
            std::size_t pick = players.size();
            for (std::size_t i = 0; i < players.size() && pick == players.size(); ++i)
            {
                if (used[i])
                    continue;
                bool apart = true;
                for (Vec2 const& p : picked)
                    if (DungeonKit::Distance(p, players[i].at) < kCondemnedApartYd)
                        apart = false;
                if (apart)
                    pick = i;
            }
            for (std::size_t i = 0; i < players.size() && pick == players.size(); ++i)
                if (!used[i])
                    pick = i;
            if (pick == players.size())
                break;
            used[pick] = true;
            picked.push_back(players[pick].at);
            out.push_back(players[pick].id);
        }
        return out;
    }

    // Each player's share of one crash (percent of the reference row): 150% / inside. A lone player takes it all.
    constexpr float ThumbsSharePct(std::uint32_t inside)
    {
        return inside ? kThumbsTotalPct / static_cast<float>(inside) : 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG9 Rend's Mark, RG10 the riderless Gyth
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kMarkFirstMs = 5000;                // after Gyth lands (engages)
    std::uint32_t constexpr kMarkEveryMs = 15000;
    std::uint32_t constexpr kMarkWarnMs = 4000;
    float constexpr kMarkRunOutYd = 20.f;                       // the marked player runs out past 20 yd from Gyth
    float constexpr kBreathAngleDeg = 60.f;
    float constexpr kBreathLengthYd = 20.f;
    float constexpr kBreathPct = 40.f;
    std::uint32_t constexpr kRiderlessFirstMs = 5000;           // after Rend lands
    std::uint32_t constexpr kRiderlessEveryMs = 15000;
    std::uint32_t constexpr kRiderlessCastMs = 2000;

    // ----------------------------------------------------------------------------------------------------------------
    // RG11 Whirlwind, RG12 Banner of the Dark Horde, the stock kit
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kWhirlFirstMs = 15000;              // after landing
    std::uint32_t constexpr kWhirlEveryMs = 20000;
    std::uint32_t constexpr kWhirlWindupMs = 2000;
    std::uint32_t constexpr kWhirlMs = 6000;
    std::uint32_t constexpr kWhirlTickMs = 1000;
    float constexpr kWhirlRadius = 8.f;
    float constexpr kWhirlPct = 10.f;                           // a second, everyone, the tank too (ruling 51)

    std::uint32_t constexpr kBannerFirstMs = 10000;             // after landing
    std::uint32_t constexpr kBannerEveryMs = 30000;
    std::uint32_t constexpr kBannerMax = 3;
    float constexpr kBannerRadius = 10.f;
    std::uint32_t constexpr kBannerDamagePct = 25;
    std::uint32_t constexpr kBannerPollMs = 500;

    constexpr std::uint32_t BannerDamage(std::uint32_t damage, bool empowered)
    {
        return empowered ? static_cast<std::uint32_t>(static_cast<std::uint64_t>(damage)
            * (100u + kBannerDamagePct) / 100u) : damage;
    }

    // Stock timers (boss_rend_blackhand.cpp / boss_gyth.cpp): Rend's Cleave 15-17 s then 10-14 s, Mortal Strike
    // 17-19 s then 14-18 s; Gyth's Corrosive Acid 8-16 s then 10-16 s, Knock Away 12-18 s then 14-20 s.
    std::uint32_t constexpr kCleaveFirstMinMs = 15000;
    std::uint32_t constexpr kCleaveFirstMaxMs = 17000;
    std::uint32_t constexpr kCleaveEveryMinMs = 10000;
    std::uint32_t constexpr kCleaveEveryMaxMs = 14000;
    std::uint32_t constexpr kStrikeFirstMinMs = 17000;
    std::uint32_t constexpr kStrikeFirstMaxMs = 19000;
    std::uint32_t constexpr kStrikeEveryMinMs = 14000;
    std::uint32_t constexpr kStrikeEveryMaxMs = 18000;
    std::uint32_t constexpr kAcidFirstMinMs = 8000;
    std::uint32_t constexpr kAcidFirstMaxMs = 16000;
    std::uint32_t constexpr kAcidEveryMinMs = 10000;
    std::uint32_t constexpr kAcidEveryMaxMs = 16000;
    std::uint32_t constexpr kKnockFirstMinMs = 12000;
    std::uint32_t constexpr kKnockFirstMaxMs = 18000;
    std::uint32_t constexpr kKnockEveryMinMs = 14000;
    std::uint32_t constexpr kKnockEveryMaxMs = 20000;
    std::uint32_t constexpr kRetryMs = 1000;

    // ----------------------------------------------------------------------------------------------------------------
    // RG16 Corrosive Acid Breath, RG17 Mortal Wounds (10 players only, rulings 63, 64; the taunt swap at 3)
    //
    // At 10: Gyth breathes Corrosive Acid on his tank every 8 s (stock 16359: armor loss stacking, a Nature tick), each
    // stack 15 s (stock 30) and +10% of Gyth's damage on that player; Rend's Mortal Strike every 8 s adds a Mortal
    // Wounds stack (-10% healing taken, 15 s). The bots swap at 3; by the user's ruling a tank taunts only once its own
    // stacks of that boss's debuff are gone (heroic: the tanks trade Gyth and Rend). With I = 8 s and D = 15 s: D > I
    // (the stacks build) and D < 3 x I (the old holder is clear before the new holder's third).
    //
    // The real gaps (wave 2 lesson 1): Gyth leaves his tank for the whole Freezing Sweep (he hovers over the
    // portcullis: about 15 s normal, 18 s heroic with the second wall) and Knock Away throws his tank out of reach;
    // Rend's Whirlwind (2 s wind-up + 6 s whirl, everyone steps out) and the run back keep his strike off for 8-10 s.
    // A Sweep gap is past D, so the B7 hold (user-approved): the current target's stacks hold while its boss cannot
    // strike it (hovering, a wind-up or whirl, out of reach). tests/brs_rend_gyth_test.cpp models both bosses and the
    // heroic trade (SimulateSwaps).
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kAcidSwapEveryMs = 8000;
    std::uint32_t constexpr kAcidMs = 15000;
    std::int32_t constexpr kAcidDamagePct = 10;                 // Gyth's damage on that player, per stack
    std::uint32_t constexpr kWoundsFirstMs = 5000;              // after landing
    std::uint32_t constexpr kWoundsEveryMs = 8000;
    std::uint32_t constexpr kWoundsMs = 15000;
    std::uint8_t constexpr kSwapAt = 3;
    std::uint8_t constexpr kWoundsMax = 255;                    // "no cap" (the aura's own limit)

    constexpr bool StacksBuild(std::uint32_t everyMs, std::uint32_t durationMs)
    {
        return durationMs > everyMs;
    }

    constexpr bool FallsOffInTime(std::uint32_t everyMs, std::uint32_t durationMs, std::uint8_t swapAt)
    {
        return swapAt >= 1 && durationMs < static_cast<std::uint32_t>(swapAt) * everyMs;
    }

    static_assert(StacksBuild(kAcidSwapEveryMs, kAcidMs) && StacksBuild(kWoundsEveryMs, kWoundsMs),
        "the swap debuffs must outlast the strike gap");
    static_assert(FallsOffInTime(kAcidSwapEveryMs, kAcidMs, kSwapAt) && FallsOffInTime(kWoundsEveryMs, kWoundsMs,
        kSwapAt), "the swap debuffs must fall off the old tank before the new one reaches the swap count");
    // A Sweep keeps Gyth off his tank longer than the acid lasts: the hold is required (not a nicety), and it must hold
    // on the tank he left while he has no victim aloft (AcidHoldFor).
    static_assert(HoverMs(false) + kAcidSwapEveryMs > kAcidMs && HoverMs(true) + kAcidSwapEveryMs > kAcidMs,
        "the hover outlasts Corrosive Acid: the hold is needed");

    // The hold is applied to the aura in steps (one aura update a second), and at once when the aura would run out
    // before the next step (B7 / B14).
    std::uint32_t constexpr kHoldStepMs = 1000;

    constexpr bool HoldDue(std::uint32_t heldMs, std::int32_t auraLeftMs)
    {
        return heldMs >= kHoldStepMs || auraLeftMs <= static_cast<std::int32_t>(heldMs + kHoldStepMs / 2u);
    }

    // Whose Corrosive Acid holds, and whether it holds now (R-2 M-1). On the ground: his victim's, while he cannot
    // breathe on it. Aloft (the Sweep hover, from the takeoff to the landing) he has no victim: Hover() stops his
    // attack and makes him passive, and CreatureAI::UpdateVictim keeps a passive creature's victim empty. So the tank
    // he left (remembered at the takeoff) holds for the whole hover, and he takes that tank back when he lands.
    struct AcidHold
    {
        std::uint64_t on = 0;
        bool holding = false;
    };

    constexpr AcidHold AcidHoldFor(bool aloft, std::uint64_t victim, std::uint64_t hoverTank, bool canBreathe)
    {
        if (aloft)
            return { hoverTank, hoverTank != 0 };
        return { victim, victim != 0 && !canBreathe };
    }

    // A landing that never reports (the land motion cleared) ends the hover this long after it was due (R-2 m-4).
    std::uint32_t constexpr kLandFallbackMs = 3000;

    // Gyth's damage on a player carrying `stacks` of his Corrosive Acid (10 players).
    constexpr std::uint32_t AcidDamage(std::uint32_t damage, std::uint32_t stacks)
    {
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(damage)
            * static_cast<std::uint64_t>(100u + static_cast<std::uint32_t>(kAcidDamagePct) * stacks) / 100u);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The room (handoff section 3.8, NM 11)
    // ----------------------------------------------------------------------------------------------------------------
    // The bots' spot bounds: the two end bays (68 yd across) and the 40 yd main strip between them, z 109..115 (0.5 yd
    // inside the floor's measured edges; no lethal wall). The balcony (z 119..124) is not in it.
    inline constexpr std::array<Vec2, 4> kWestBay{ { { 109.3f, -453.8f }, { 124.f, -453.8f }, { 124.f, -386.2f },
        { 109.3f, -386.2f } } };
    inline constexpr std::array<Vec2, 4> kMainStrip{ { { 124.f, -439.7f }, { 180.f, -439.7f }, { 180.f, -400.3f },
        { 124.f, -400.3f } } };
    inline constexpr std::array<Vec2, 4> kEastBay{ { { 180.f, -453.8f }, { 193.6f, -453.8f }, { 193.6f, -386.2f },
        { 180.f, -386.2f } } };
    float constexpr kFloorZ = 110.9f;
    float constexpr kRoomZMin = 109.f;
    float constexpr kRoomZMax = 115.f;

    // The stock summon spots behind the portcullis (creature_summon_groups 10429, groups 0-5) [db].
    inline constexpr std::array<Vec2, 8> kWaveSpots{ { { 202.5f, -421.3f }, { 204.0f, -418.4f }, { 203.1f, -424.0f },
        { 201.0f, -416.6f }, { 209.9f, -428.3f }, { 209.3f, -430.9f }, { 211.3f, -425.9f }, { 208.6f, -424.6f } } };
    float constexpr kWaveZ = 110.99f;
    float constexpr kStaticSearchYd = 15.f;                     // the 4 static adds stand within this of kWaveSpots[0]
    // Where Rend lands: kRendLeapYd from Gyth toward the arena's middle, or this spot when Gyth is gone.
    inline constexpr Vec2 kRendLanding{ 172.f, -420.2f };
    float constexpr kRendLeapYd = 6.f;
    float constexpr kInsultRangeYd = 40.f;                      // DR10: a player this close to Nefarius may insult him

    // Inside the bots' room (the two bays and the strip).
    inline bool InRoom(Vec2 p)
    {
        return DungeonKit::PointInPolygon(kWestBay, p) || DungeonKit::PointInPolygon(kMainStrip, p)
            || DungeonKit::PointInPolygon(kEastBay, p);
    }

    // Who owns a round's registry shapes (R-2 M-2). BM applies a mechanic's Within(...) room bounds to a bot only
    // while the mechanic's owner is in combat with that bot (MechanicBotView BoundsOf), and the Nefarius copy drops all
    // combat every second: so the rounds belong to a boss that fights the group, Gyth while he fights (hovering too: he
    // keeps his combat), else Rend once he is on the floor; Nefarius only when neither fights (a gap of a few seconds:
    // Gyth's walk in, Rend's leap). Nefarius still speaks, casts the looks and burns the pools.
    enum class RoundOwner : std::uint8_t
    {
        Gyth = 0,
        Rend = 1,
        Nefarius = 2,
    };

    constexpr RoundOwner RoundOwnerFor(bool gythFighting, bool rendFighting)
    {
        return gythFighting ? RoundOwner::Gyth : rendFighting ? RoundOwner::Rend : RoundOwner::Nefarius;
    }

    // The arena entry door 164726 (R-2 B-1): shut only while the show runs (Rend's boss state IN_PROGRESS, 1); open on
    // NOT_STARTED (0), FAIL (2) and DONE (3). It is the arena's only way out (stock boss_rend_blackhand::JustDied
    // opens it); the way-out door 175186 lies behind it.
    std::uint32_t constexpr kRendStateInProgress = 1;

    constexpr bool EntryDoorOpen(std::uint32_t rendState)
    {
        return rendState != kRendStateInProgress;
    }

    // The heroic second gap's rule (rolling front ruling 3): on the other side of the strip's middle (a first gap on
    // the middle has no side: any), within 20 yd.
    constexpr int GapSide(float centre)
    {
        return centre > 0.01f ? 1 : centre < -0.01f ? -1 : 0;
    }

    constexpr bool SecondGapOk(float first, float second)
    {
        bool const otherSide = GapSide(first) == 0 || GapSide(second) != GapSide(first);
        float const apart = first > second ? first - second : second - first;
        return otherSide && apart <= kSweepWithinYd;
    }
}

#endif
