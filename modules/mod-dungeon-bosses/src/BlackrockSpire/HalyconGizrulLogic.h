/*
 * mod-dungeon-bosses, Blackrock Spire B7:
 * Halycon and Gizrul (10220, 10268), the pure, host-testable part (no engine headers). Build spec SP "Halycon and
 * Gizrul" (docs/dungeons/blackrock-spire-rework.md, HG1-HG11; rulings 44-46, tank swap at 10 rulings 62-64), handoff
 * sections 3.4 (rows HG), 3.5 (row B7), 3.6, 3.8 (NM 7: the den is 758 sq yd). Tested by
 * tests/brs_halycon_gizrul_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsHalyconGizrul (210210-210249), declared in apps/dbc-tools
 *                  source/npcs/blackrock_spire/halycon_gizrul.py
 *   Tuning         NH<> constants and FlexAB pairs, straight from the build spec
 *   Cooldown       a timer that runs 1.5 times as fast under Pack Fury (HG7)
 *   ChargePlan     HG2 / HG3: when each line resolves, when its pounce lands, how long the charger holds at the end
 *   ChargeReach    HG2: a line's length, 30 yd or to the wall of the den-and-hall arena (both regions: a line from the
 *                  den runs on into the hall)
 *   Torn Hide      HG11 at 10 players: the debuff duration sized against the bite rate (the user's taunt rule)
 *   Trail          HG9 heroic: the goo puddles along a trail, and the den's space math
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_HALYCON_GIZRUL_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_HALYCON_GIZRUL_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <vector>

namespace BrsHalyconGizrul
{
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::Arena;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsHalyconGizrul;

    enum HalyconGizrulSpells : std::uint32_t
    {
        SPELL_HG_SAVAGE_CHARGE      = kSpellSlice.first + 0,    // 210210 HG2 a line's hit (resolve copy, Physical)
        SPELL_HG_PACK_POUNCE        = kSpellSlice.first + 1,    // 210211 HG3 the pounce's hit (resolve copy)
        SPELL_HG_THRASH             = kSpellSlice.first + 2,    // 210212 HG4 the ring's hit (resolve copy)
        SPELL_HG_RABID_FROTH        = kSpellSlice.first + 3,    // 210213 HG5 the ring's hit (resolve copy, Nature)
        SPELL_HG_RABID_TRAIL        = kSpellSlice.first + 4,    // 210214 HG9 a trail's tick (resolve copy, no damage)
        SPELL_HG_RABIES             = kSpellSlice.first + 5,    // 210215 HG6 the Disease (periodic, up to 5 stacks)
        SPELL_HG_CALL_OF_THE_PACK   = kSpellSlice.first + 6,    // 210216 HG7 the 3 s interruptible howl
        SPELL_HG_PACK_FURY          = kSpellSlice.first + 7,    // 210217 HG7 +25% damage, 15 s
        SPELL_HG_BLOODIED_PACK      = kSpellSlice.first + 8,    // 210218 HG7 heroic: +10% damage a stack, up to 5
        SPELL_HG_GRIEF              = kSpellSlice.first + 9,    // 210219 HG8 +25% (heroic 40%) damage on the survivor
        SPELL_HG_TORN_HIDE          = kSpellSlice.first + 10,   // 210220 HG11 the tank debuff (10 players)
        SPELL_HG_CHARGE_BAR         = kSpellSlice.first + 11,   // 210221 HG2 the 3 s paw (cast bar, not a kick)
        SPELL_HG_THRASH_BAR         = kSpellSlice.first + 12,   // 210222 HG4 the 2 s crouch (cast bar)
        SPELL_HG_FROTH_BAR          = kSpellSlice.first + 13,   // 210223 HG5 the 2 s head shake (cast bar)
        SPELL_HG_CHARGE_LOOK        = kSpellSlice.first + 14,   // 210224 look: Feral Charge - Bear's trail
        SPELL_HG_LEAP_LOOK          = kSpellSlice.first + 15,   // 210225 look: Leap, on the pounce
        SPELL_HG_MAUL_LOOK          = kSpellSlice.first + 16,   // 210226 look: Maul, on the landing
        SPELL_HG_WHIRL_LOOK         = kSpellSlice.first + 17,   // 210227 look: Whirlwind, on Thrash
        SPELL_HG_FROTH_LOOK         = kSpellSlice.first + 18,   // 210228 look: Disease Cloud, on Rabid Froth
        SPELL_HG_SPRINT             = kSpellSlice.first + 19,   // 210229 HG1 Gizrul's run in: +100% speed, 10 s
        SPELL_HG_TRAIL_PUDDLE       = kSpellSlice.first + 20,   // 210230 HG9 look: a goo puddle (area aura, 4 yd)
        // 210231-210249 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_HG_TRAIL_PUDDLE;
    static_assert(kLastSpell <= kSpellSlice.last, "Halycon and Gizrul's spells must stay in their slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum HalyconGizrulTags : std::uint32_t
    {
        TAG_HG_CHARGE   = 2,
        TAG_HG_POUNCE   = 3,
        TAG_HG_THRASH   = 4,
        TAG_HG_FROTH    = 5,
        TAG_HG_TRAIL    = 9,
    };

    // creature_text group ids (the SQL rev writes them; SP "Text"). Every line is a boss emote (type 41).
    enum HalyconTexts : std::uint8_t
    {
        EMOTE_HALYCON_GRIEF     = 0,    // HG8 "%s collapses. Gizrul howls in grief!" (her death while he lives)
        EMOTE_HALYCON_PULL      = 1,    // HG1
        EMOTE_HALYCON_THRASH    = 2,    // HG4
        EMOTE_HALYCON_CALL      = 3,    // HG7
        EMOTE_HALYCON_CHARGE    = 4,    // HG8 her charge under Grief ($n)
    };

    enum GizrulTexts : std::uint8_t
    {
        EMOTE_GIZRUL_CHARGE     = 0,    // HG2 ($n)
        EMOTE_GIZRUL_FROTH      = 1,    // HG5
        EMOTE_GIZRUL_GRIEF      = 2,    // HG8 "%s falls. Halycon's howl turns to a scream!" (his death while she lives)
        EMOTE_GIZRUL_CALL       = 3,    // HG7 under Grief
    };

    // The stock waypoint path Gizrul runs from the foot of his ramp to the den's mouth [db: waypoint_data 402450].
    inline constexpr std::uint32_t kGizrulPath = 402450;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kChargePct{ 30.f, 40.f };        // HG2
    inline constexpr NH<float> kPouncePct{ 25.f, 30.f };        // HG3
    inline constexpr NH<float> kThrashPct{ 25.f, 30.f };        // HG4
    inline constexpr NH<float> kFrothPct{ 20.f, 25.f };         // HG5
    inline constexpr NH<float> kRabiesPctPerStack{ 1.f, 1.5f }; // HG6, every 3 s (every 1.5 s under Pack Fury)
    inline constexpr NH<std::int32_t> kGriefDamagePct{ 25, 40 };    // HG8

    inline constexpr std::int32_t kPackFuryDamagePct = 25;      // HG7
    inline constexpr std::int32_t kBloodiedPackDamagePct = 10;  // HG7 heroic, per stack
    inline constexpr std::uint8_t kBloodiedPackMax = 5;
    inline constexpr std::uint8_t kRabiesMaxStacks = 5;

    // The counts, "a / b" at 5 players / 6 or more (ruling 8).
    inline constexpr FlexAB kChargeLines{ 1, 2 };       // HG2: the farthest non-tanks, charged 1 s apart

    // HG3: a pounce at the end of the first line only on normal, at the end of every line on heroic.
    inline constexpr bool PounceOn(std::uint32_t lineIndex, bool heroic)
    {
        return heroic || lineIndex == 0;
    }

    // Shapes (yd).
    inline constexpr float kChargeWidth = 5.f;
    inline constexpr float kChargeLength = 30.f;
    inline constexpr float kChargeInsetYd = 1.f;        // a line stops this far short of the arena's edge
    inline constexpr float kChargeMinYd = 6.f;          // never shorter (a target at his feet still gets a line)
    inline constexpr float kPounceRadius = 8.f;
    inline constexpr float kThrashRadius = 8.f;
    inline constexpr float kFrothRadius = 10.f;
    inline constexpr float kTrailWidth = 5.f;           // HG9: the line itself
    inline constexpr float kPuddleRadius = 4.f;         // HG9 look: the Deadmines goo (SV 90342)
    inline constexpr float kPuddleSpacing = 8.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms). The pull is t = 0; Gizrul arrives at about 4 s (ruling 45).
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kGizrulArriveMs = 4000;      // HG1 (81 yd at his 10 yd/s doubled by the sprint)
    inline constexpr std::uint32_t kGizrulRunTimeoutMs = 9000;  // still not at the mouth: he is placed there
    inline constexpr std::uint32_t kSprintMs = 10000;
    inline constexpr std::int32_t kSprintSpeedPct = 100;
    inline constexpr float kArriveYd = 3.f;                     // at the den's mouth

    inline constexpr std::uint32_t kChargeEveryMs = 18000;      // HG2, first on his arrival
    inline constexpr std::uint32_t kPawMs = 3000;               // HG2 the warning (the paw)
    inline constexpr std::uint32_t kChargeGapMs = 1000;         // HG2 at 6+: the second line 1 s after the first
    inline constexpr std::uint32_t kChargeTravelMs = 750;       // HG2 the dash along a line (any length)
    inline constexpr std::uint32_t kPounceDelayMs = 1500;       // HG3 after the charge ends
    inline constexpr std::uint32_t kLeapMs = 1000;              // HG3 her leap's flight (she takes off 1 s early)
    inline constexpr std::uint32_t kHoldNoPounceMs = 1500;      // the charger's hold at the end with no pounce
    inline constexpr std::uint32_t kPounceRecoverMs = 500;      // HG3 she stands on the spot this long after landing

    inline constexpr std::uint32_t kThrashFirstMs = 10000;      // HG4
    inline constexpr std::uint32_t kThrashEveryMs = 20000;
    inline constexpr std::uint32_t kThrashWarnMs = 2000;
    inline constexpr std::uint32_t kFrothFirstMs = 20000;       // HG5 (from the pull: the rings alternate every 10 s)
    inline constexpr std::uint32_t kFrothEveryMs = 20000;
    inline constexpr std::uint32_t kFrothWarnMs = 2000;
    inline constexpr std::uint32_t kFrothMinFirstMs = 2000;     // a late arrival still gets 2 s before the first ring
    inline constexpr std::uint32_t kRabiesBiteFirstMs = 8000;   // HG6 after his arrival
    inline constexpr std::uint32_t kRabiesBiteEveryMs = 8000;
    inline constexpr std::uint32_t kRabiesMs = 30000;
    inline constexpr std::uint32_t kRabiesTickMs = 3000;        // 1.5 s under Pack Fury: the aura ticks every 1.5 s
    inline constexpr std::uint32_t kRabiesAmplitudeMs = 1500;   // and skips every other tick without it
    inline constexpr std::uint32_t kCallFirstMs = 15000;        // HG7
    inline constexpr std::uint32_t kCallEveryMs = 25000;        // from the cast's start; not sped up by Pack Fury
    inline constexpr std::uint32_t kCallCastMs = 3000;
    inline constexpr std::uint32_t kPackFuryMs = 15000;
    inline constexpr std::uint8_t kCallKickPriorityNormal = 2;  // a reward
    inline constexpr std::uint8_t kCallKickPriorityHeroic = 3;  // expected
    inline constexpr std::uint32_t kTrailMs = 12000;            // HG9 heroic
    inline constexpr std::uint32_t kTrailTickMs = 2000;
    inline constexpr float kKillTogetherPct = 5.f;              // the bots keep the two within 5%
    inline constexpr std::uint32_t kRetryMs = 500;              // a due move that cannot start yet

    // Halycon's cast bars (Thrash 2 s, Call 3 s) wait while one of her pounces takes off within the cast plus this
    // margin, so a leap never breaks her cast. A pounce queued during a cast takes off after it ends (the earliest
    // take-off is LeapStartMs(0) = 4.25 s after the charge starts, longer than either cast).
    inline constexpr std::uint32_t kPounceClearMs = 250;

    // Rabies: the aura ticks every kRabiesAmplitudeMs; without Pack Fury on its caster every odd tick is skipped.
    inline constexpr bool RabiesTickDeals(std::uint32_t tickNumber, bool fury)
    {
        return fury || tickNumber % 2u == 0u;
    }
    static_assert(kRabiesAmplitudeMs * 2u == kRabiesTickMs, "Rabies ticks twice as fast under Pack Fury");

    // The skipper's own tick count (one per aura, kept by the aura script). The engine's tick number cannot be used:
    // a new stack restarts it at 0 without moving the periodic timer (Aura::RefreshTimers), so the first tick after
    // every refresh would read as tick 1 and be skipped (R-1-B M2).
    class RabiesTicker
    {
    public:
        // The next tick: true when it deals.
        constexpr bool Next(bool fury)
        {
            ++_ticks;
            return RabiesTickDeals(_ticks, fury);
        }

    private:
        std::uint32_t _ticks = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Pack Fury: "their timers run 50% faster" (every cooldown below runs 1.5 times as fast; 18 s becomes 12 s)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t FuryStep(std::uint32_t diff, bool fury)
    {
        return fury ? diff * 3u / 2u : diff;
    }

    // A repeating timer in ms of "fight time": Advance with the frame's diff and whether the owner wears Pack Fury.
    class Cooldown
    {
    public:
        static constexpr std::int64_t kNever = std::numeric_limits<std::int64_t>::max() / 4;

        constexpr void Arm(std::uint32_t inMs) { _left = static_cast<std::int64_t>(inMs); }
        constexpr void Disarm() { _left = kNever; }
        constexpr bool Armed() const { return _left != kNever; }
        constexpr void Advance(std::uint32_t diff, bool fury)
        {
            if (Armed())
                _left -= static_cast<std::int64_t>(FuryStep(diff, fury));
        }
        constexpr bool Due() const { return Armed() && _left <= 0; }
        // Fight time left (0 when due; kNever when disarmed).
        constexpr std::int64_t Left() const { return Armed() ? std::max<std::int64_t>(_left, 0) : kNever; }

    private:
        std::int64_t _left = kNever;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // HG2 / HG3: one Savage Charge (one line at 5 players, two lines 1 s apart at 6+)
    // ----------------------------------------------------------------------------------------------------------------
    struct ChargePlan
    {
        // Line i registers (and its emote names its target) this long after the charge starts.
        static constexpr std::uint32_t RegisterMs(std::uint32_t line) { return line * kChargeGapMs; }
        // Line i resolves (the charger leaves along it) after its 3 s paw.
        static constexpr std::uint32_t ResolveMs(std::uint32_t line) { return RegisterMs(line) + kPawMs; }
        // The charger reaches line i's end.
        static constexpr std::uint32_t ArriveMs(std::uint32_t line) { return ResolveMs(line) + kChargeTravelMs; }
        // Line i's pounce lands 1.5 s after the charge along it ends. The circle is drawn with the line (SP's
        // reading), so its warning runs from the line's registration to the landing.
        static constexpr std::uint32_t PounceLandMs(std::uint32_t line) { return ArriveMs(line) + kPounceDelayMs; }
        static constexpr std::uint32_t PounceWarnMs() { return kPawMs + kChargeTravelMs + kPounceDelayMs; }
        // Halycon takes off this long before the landing.
        static constexpr std::uint32_t LeapStartMs(std::uint32_t line) { return PounceLandMs(line) - kLeapMs; }

        // The charger stays at the last line's end until its pounce lands (or kHoldNoPounceMs), then runs back.
        static constexpr std::uint32_t ReturnMs(std::uint32_t lines, bool lastPounce)
        {
            std::uint32_t const last = lines ? lines - 1 : 0;
            return lastPounce ? PounceLandMs(last) : ArriveMs(last) + kHoldNoPounceMs;
        }
    };
    static_assert(ChargePlan::PounceWarnMs() == 5250, "3 s paw + the dash + 1.5 s");
    static_assert(ChargePlan::LeapStartMs(0) > kCallCastMs + kPounceClearMs, "a pounce queued in a cast waits for it");

    // The floor along `facing` from `from`: kChargeLength, or less where the arena (any of its regions: the den runs
    // into the hall at the mouth) ends, kept kChargeInsetYd inside (0 when the edge is closer than that). Sampled
    // every `step` yd.
    inline float ArenaReach(Arena const& arena, Vec2 from, float z, float facing, float step = 0.5f)
    {
        float reach = 0.f;
        for (float d = step; d <= kChargeLength + kChargeInsetYd + 0.001f; d += step)
        {
            if (!arena.Contains(DungeonKit::Advance(from, facing, d), z))
                break;
            reach = d;
        }
        return std::clamp(reach - kChargeInsetYd, 0.f, kChargeLength);
    }

    struct ChargeAim
    {
        float facing = 0.f;
        float length = 0.f;
    };

    // A charge line from `from` aimed along `facing` (at its target): kChargeLength or to the arena's edge. A line is
    // never shorter than kChargeMinYd (a target at his feet still gets one); when the edge is closer than that the
    // way he faces, the line turns toward open floor instead of running through the wall (R-1-B m5): the nearest
    // turn first, in 15 degree steps either way. With no such floor anywhere (off the arena) it keeps the old
    // minimum along `facing`.
    inline ChargeAim AimCharge(Arena const& arena, Vec2 from, float z, float facing, float step = 0.5f)
    {
        float const ahead = ArenaReach(arena, from, z, facing, step);
        if (ahead >= kChargeMinYd)
            return { facing, ahead };
        float constexpr kTurn = DungeonKit::kPi / 12.f;
        for (int i = 1; i <= 12; ++i)
            for (float const sign : { 1.f, -1.f })
            {
                float turned = facing + sign * kTurn * static_cast<float>(i);
                while (turned < 0.f)
                    turned += 2.f * DungeonKit::kPi;
                while (turned >= 2.f * DungeonKit::kPi)
                    turned -= 2.f * DungeonKit::kPi;
                float const reach = ArenaReach(arena, from, z, turned, step);
                if (reach >= kChargeMinYd)
                    return { turned, reach };
            }
        return { facing, kChargeMinYd };
    }

    // The length of a line aimed along `facing` (after AimCharge's turn, if any).
    inline float ChargeReach(Arena const& arena, Vec2 from, float z, float facing, float step = 0.5f)
    {
        return AimCharge(arena, from, z, facing, step).length;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG11 Torn Hide (10 players). The user's taunt rule (2026-11-15): a tank taunts a wolf only once that wolf's Torn
    // Hide has fallen off it. R-1 ruling 2 (2026-11-15): SP's 15 s at the normal 6 s bite, about 10-11 s under Pack
    // Fury's 4 s bite. Two conditions on the debuff duration D against the bite interval I:
    //   - D > I: the stacks build to the swap count at all (each bite lands before the last one ran out);
    //   - D < swapAt x I: the old holder's stacks are gone before the new holder reaches the count. The old holder's
    //     last bite is at L; the new holder's third stack lands at L + 3I at the earliest (its bites follow the same
    //     timer), and downtime only pushes it later.
    // Downtime: a wolf away on a charge or a pounce, running back, or under a cast bar cannot bite, and Gizrul's
    // charge cycle under Pack Fury (12 s, 6.25 s away plus the run back) leaves room for one bite: his real gap was
    // 12-13 s, more than any D < 3I (R-1-B M1). So the debuff on the wolf's current target holds (does not run
    // down) while its wolf cannot bite it: measured in biting time the gap is I again, and both conditions hold. Only
    // the current target's stacks hold: an old holder's run down at once, which only helps the rule.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kTornHideBiteFirstMs = 6000;     // after each wolf engages
    inline constexpr std::uint32_t kTornHideBiteEveryMs = 6000;     // 4 s under Pack Fury (the 1.5x rule)
    inline constexpr std::uint32_t kTornHideMs = 15000;             // SP
    inline constexpr std::uint32_t kTornHideFuryMs = 10000;         // ruling 2: about 10-11 s (bounds 6 s and 12 s)
    inline constexpr std::int32_t kTornHideDamagePct = 10;          // per stack, from that wolf only
    inline constexpr std::uint8_t kTornHideSwapAt = 3;
    inline constexpr std::uint8_t kTornHideMax = 255;               // "no cap" (the aura's own limit)
    inline constexpr float kTornHideBiteYd = 8.f;                   // a bite needs the target in reach

    inline constexpr std::uint32_t TornHideBiteMs(bool fury)
    {
        return fury ? kTornHideBiteEveryMs * 2u / 3u : kTornHideBiteEveryMs;
    }

    inline constexpr std::uint32_t TornHideMs(bool fury)
    {
        return fury ? kTornHideFuryMs : kTornHideMs;
    }

    inline constexpr bool TornHideStacks(std::uint32_t biteMs, std::uint32_t durationMs)
    {
        return durationMs > biteMs;
    }

    inline constexpr bool TornHideFallsOffInTime(std::uint32_t biteMs, std::uint32_t durationMs, std::uint8_t swapAt)
    {
        return swapAt >= 1 && durationMs < static_cast<std::uint32_t>(swapAt) * biteMs;
    }

    // The hold is applied to the aura in steps (one aura update a second, not one a frame), and at once when the
    // aura would run out before the next step.
    inline constexpr std::uint32_t kTornHideHoldStepMs = 1000;

    inline constexpr bool TornHideHoldDue(std::uint32_t heldMs, std::int32_t auraLeftMs)
    {
        return heldMs >= kTornHideHoldStepMs
            || auraLeftMs <= static_cast<std::int32_t>(heldMs + kTornHideHoldStepMs / 2u);
    }

    static_assert(TornHideBiteMs(true) == 4000, "SP HG11: 4 s bites under Pack Fury");
    static_assert(TornHideStacks(TornHideBiteMs(false), TornHideMs(false))
        && TornHideStacks(TornHideBiteMs(true), TornHideMs(true)), "Torn Hide must outlast the bite interval");
    static_assert(TornHideFallsOffInTime(TornHideBiteMs(false), TornHideMs(false), kTornHideSwapAt)
        && TornHideFallsOffInTime(TornHideBiteMs(true), TornHideMs(true), kTornHideSwapAt),
        "Torn Hide must fall off the old holder before the new one reaches the swap count");
    // Pack Fury ending between two bites: a fury stack still bridges the next normal 6 s bite.
    static_assert(TornHideStacks(TornHideBiteMs(false), TornHideMs(true)), "a fury stack bridges a normal bite");
    // A normal 15 s stack against a fury-rate new holder fails the bound (15 > 12): Pack Fury landing right after a
    // swap can keep the new holder at 3 up to 3 s (the host model measures it).
    static_assert(!TornHideFallsOffInTime(TornHideBiteMs(true), TornHideMs(false), kTornHideSwapAt),
        "the mixed case is bounded, not excluded");

    // The damage a wolf deals its target with `stacks` of its own Torn Hide on it.
    inline constexpr std::uint32_t TornHideDamage(std::uint32_t damage, std::uint32_t stacks)
    {
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(damage)
            * static_cast<std::uint64_t>(100u + static_cast<std::uint32_t>(kTornHideDamagePct) * stacks) / 100u);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HG9 Rabid Trail (heroic): the puddles along a trail, and the space math
    // ----------------------------------------------------------------------------------------------------------------

    // Puddle centres from `a` to `b`: the first kPuddleSpacing / 2 in, then every kPuddleSpacing (a 30 yd trail gets
    // 4 puddles, a 6 yd one 1).
    inline std::vector<Vec2> TrailPuddles(Vec2 a, Vec2 b)
    {
        std::vector<Vec2> out;
        float const length = DungeonKit::Distance(a, b);
        if (length <= 0.f)
        {
            out.push_back(a);
            return out;
        }
        float const facing = DungeonKit::BearingTo(a, b);
        for (float d = kPuddleSpacing * 0.5f; d < length + 0.001f; d += kPuddleSpacing)
            out.push_back(DungeonKit::Advance(a, facing, d));
        return out;
    }

    // NM 7: the den floor, and the den plus the hall's west half (handoff section 3.8; SP said about 1,000 / 1,700).
    inline constexpr float kDenSqYd = 758.f;
    inline constexpr float kDenAndHallSqYd = 1405.f;

    // Trails on the floor at once, at most: one charge cycle (18 s, 12 s under Pack Fury) against a 12 s trail. A
    // charge lays `lines` trails; when the cycle is no longer than the trail plus the second line's 1 s, the next
    // charge's trails land while the last ones still lie (SP: "4 at 6 or more for under 3 sec").
    inline constexpr std::uint32_t TrailsAtOnce(std::uint32_t lines, bool fury)
    {
        std::uint32_t const cycle = fury ? kChargeEveryMs * 2u / 3u : kChargeEveryMs;
        return kTrailMs + kChargeGapMs > cycle ? lines * 2u : lines;
    }

    inline constexpr float TrailSqYd(float length)
    {
        return length * kTrailWidth;
    }
}

#endif
