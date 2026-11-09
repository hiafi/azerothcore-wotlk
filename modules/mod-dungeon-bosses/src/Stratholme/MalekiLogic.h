/*
 * mod-dungeon-bosses, Stratholme S12: Maleki the Pallid (10438), the pure, host-testable part (no engine headers): the
 * spell ids, the per-difficulty tuning, the target picks, the never-paused fight timeline, the Icy Death growth clock,
 * the Siphon's snap and eat rules, the eye spot and the heroic drift. Build spec: ST 3160-3211 (build spec), ST
 * 2915-3159 (design, rulings 48-50), MK1-MK6; handoff section 3.4 rows MK, section 3.5 row S12, section 3.6 (normal
 * 170k, heroic 210k), section 3.8 (his arena and eye centres).
 *
 * Damage percentages are of the reference health row (normal 3,670 / heroic 4,120 non-tank at level 60, the 329:60
 * pins): the build spec gives N / H percents, and the row makes the rest of the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_MALEKI_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_MALEKI_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratMaleki
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsMaleki;

    // Declared in apps/dbc-tools source/npcs/stratholme/maleki_the_pallid.py (same ids).
    enum MalekiSpells : std::uint32_t
    {
        SPELL_MK_ICY_DEATH          = 206665,   // MK1 the frost corruption: Magic, 5 stacks, DoT and slow per stack
        SPELL_MK_ICY_DEATH_LOOK     = 206666,   // MK1 the landing look (Chains of Ice 45524's SV 12328)
        SPELL_MK_SHATTER            = 206667,   // MK2 the nova: resolve copy (Frost), Frost Nova 122's SV 17
        SPELL_MK_SHATTER_ROOT       = 206668,   // MK2 the rider: a 2 s root
        SPELL_MK_SIPHON_CAST        = 206669,   // MK3 the 2 s cast at the carrier (kickable)
        SPELL_MK_SIPHON_CHANNEL     = 206670,   // MK3 the 5 s channel, the tether (kickable; Drain Life's SV 12655)
        SPELL_MK_SIPHON_DRAIN       = 206671,   // MK3 a stack eaten: Shadow on the carrier (refflat damage spell)
        SPELL_MK_SIPHON_HEAL        = 206672,   // MK3 a stack eaten: his heal (base point 0 = the amount)
        SPELL_MK_ICE_TOMB_HOLD      = 206673,   // MK4 the prisoner's hold (stun, CHANGE_MAP; HoldInUnit)
        SPELL_MK_ICE_TOMB_DRAIN     = 206674,   // MK4 the drain on the prisoner, a second (refflat damage spell)
        SPELL_MK_ICE_TOMB_HEAL      = 206675,   // MK4 his heal from the tomb (base point 0 = the amount)
        SPELL_MK_EYE_STORM          = 206676,   // MK5 the storm's 1 s tick: resolve copy (Frost)
        SPELL_MK_EYE_CHANNEL        = 206677,   // MK5 the 6 s channel bar (not kickable)
        SPELL_MK_EYE_STORM_LOOK     = 206678,   // MK5 the falling ice on a storm stalker (Blizzard 26607's SV 8787)
        SPELL_MK_ICE_TOMB_LOOK      = 206679,   // MK4 the freeze's look on the prisoner (Ice Tomb 16869's SV 4340)
        SPELL_MK_FROSTBITE_LOOK     = 206680,   // MK2 heroic: a Frostbite stack's look (Seed of Corruption's SV 8339)
        // 206681-206684 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_MK_ICY_DEATH), "Maleki's spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_MK_FROSTBITE_LOOK), "Maleki's spells sit in his slice");

    // Registry tags (the build spec's MK numbers; 10+ for the helpers).
    enum MalekiTags : std::uint32_t
    {
        TAG_ICY_DEATH       = 1,    // MK1 the rolling self-keyed RunOut (carriers at 2+ stacks keep 8 yd)
        TAG_SHATTER         = 2,
        TAG_SIPHON          = 3,    // MK3 the carrier's spot (bots: get out 12 yd)
        TAG_EYE             = 5,    // MK5 the storm outside the eye (hidden: the real hit)
        TAG_EYE_DRAWN       = 15,   // MK5 the eye's drawn donut (a Decoy: humans read it, bots never see it)
        TAG_EYE_CARRIER     = 16,   // MK5 the Siphon carrier's storm ticks (RegistryHit)
    };

    // The descriptor phase while the Eye is marked or storming: no bot dispels Icy Death then (ST MK1 "Bots").
    std::uint32_t constexpr kPhaseEye = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Build spec" and "Heroic", approved 2026-11-05)
    // ----------------------------------------------------------------------------------------------------------------

    // MK1 Icy Death: every 12 s, first at 5 s, on a random non-tank without it (else the fewest stacks); it starts at
    // 1 stack and grows 1 every 6 s (heroic 4 s). Each stack: 1% Frost every 2 s and a 10% slow (the aura's own
    // effects, multiplied by its stack count). 5 stacks: the Ice Tomb.
    std::uint32_t constexpr kCurseFirstMs = 5000;
    std::uint32_t constexpr kCurseEveryMs = 12000;
    inline constexpr NH<std::uint32_t> kCurseGrowMs{ 6000, 4000 };
    std::uint32_t constexpr kCurseMaxStacks = 5;
    float constexpr kCurseTickPct = 1.f;            // per stack, every kCurseTickMs (the aura's periodic effect)
    std::uint32_t constexpr kCurseTickMs = 2000;
    std::int32_t constexpr kCurseSlowPct = 10;      // per stack
    // Bots: a carrier at 2+ stacks keeps 8 yd from allies outside the Eye (a rolling self-keyed RunOut, never
    // resolved: replaced every kRunOutRefreshMs with a kRunOutWarnMs warning, the Ras precedent).
    std::uint8_t constexpr kCurseSpreadAt = 2;
    float constexpr kCurseSpreadRadius = 8.f;
    std::uint32_t constexpr kRunOutWarnMs = 4000;
    std::uint32_t constexpr kRunOutRefreshMs = 2000;
    static_assert(kRunOutRefreshMs < kRunOutWarnMs, "the rolling RunOut is replaced before it resolves");
    // Bots: dispel only when no ally is within this range of the carrier (X1's DispelEntry `when`), never during the
    // Eye. Normal: a reward (priority 2); heroic: expected (priority 3).
    float constexpr kDispelSpacingYd = 8.f;
    inline constexpr NH<std::uint8_t> kDispelPriority{ 2, 3 };

    // MK2 Shatter: a dispel or a snapped Siphon bursts the carrier's stacks in an 8 yd nova around them (the carrier
    // is spared): 7% / 8% Frost per stack to everyone else and a 2 s root, no Weakened (ruling 50). Heroic: each ally
    // hit gains a stack of Icy Death (Frostbite; never the tank: Icy Death never lands on the tank).
    float constexpr kShatterRadius = 8.f;
    inline constexpr NH<float> kShatterPctPerStack{ 7.f, 8.f };
    std::uint32_t constexpr kShatterWarnMs = 250;   // "short": the nova is at the carrier the moment it bursts
    std::uint32_t constexpr kShatterRootMs = 2000;
    inline constexpr NH<std::uint32_t> kFrostbiteStacks{ 0, 1 };

    // MK3 The Siphon: every 20 s, first at 15 s (a fixed grid: a Siphon that waits for a cast keeps the next one on
    // time), on the carrier with the most stacks (ties random); no carrier, no Siphon. A 2 s cast, then a 5 s channel
    // eating one stack a second: 6% / 8% Shadow to the carrier and 2% / 3% of his maximum health to him per stack. The
    // tether snaps once the carrier is 12 yd from where they stood at the cast's start (checked every 250 ms), and the
    // stacks left shatter there (MK2). A kick ends it with the stacks kept (priority 1: a reward).
    std::uint32_t constexpr kSiphonFirstMs = 15000;
    std::uint32_t constexpr kSiphonEveryMs = 20000;
    std::uint32_t constexpr kSiphonCastMs = 2000;
    std::uint32_t constexpr kSiphonChannelMs = 5000;
    std::uint32_t constexpr kSiphonEatMs = 1000;
    std::uint32_t constexpr kSiphonSnapCheckMs = 250;
    float constexpr kSiphonSnapYd = 12.f;
    inline constexpr NH<float> kSiphonDrainPct{ 6.f, 8.f };     // per stack eaten, to the carrier
    inline constexpr NH<float> kSiphonHealPct{ 2.f, 3.f };      // per stack eaten, of his maximum health
    std::uint8_t constexpr kSiphonKickPriority = 1;

    // MK4 Ice Tomb: Icy Death at 5 stacks freezes the carrier (the stacks are gone) in an Ice Tomb, 8,000 / 12,000
    // health, for at most 8 s. Each second: 3% / 4% Shadow to the prisoner, 1% / 1.5% of his maximum health to him.
    // Kill order: the tomb first (BreakOut).
    inline constexpr NH<std::uint32_t> kTombHealth{ 8000, 12000 };
    std::uint32_t constexpr kTombMaxMs = 8000;
    std::uint32_t constexpr kTombTickMs = 1000;
    inline constexpr NH<float> kTombDrainPct{ 3.f, 4.f };
    inline constexpr NH<float> kTombHealPct{ 1.f, 1.5f };
    std::int8_t constexpr kTombTargetPriority = 3;

    // MK5 The Eye of the Blizzard: every 30 s, first at 27 s: yell line 3 and a 3 s marker on the eye, an 8 yd / 6 yd
    // circle 10 to 14 yd from him toward the plaza; then a 6 s storm: everyone outside the eye takes 10% / 15% Frost a
    // second, Weakened once per player. Heroic: the eye drifts 1.5 yd/s in one direction, turning back at the floor's
    // edge.
    std::uint32_t constexpr kEyeFirstMs = 27000;
    std::uint32_t constexpr kEyeEveryMs = 30000;
    std::uint32_t constexpr kEyeMarkerMs = 3000;
    std::uint32_t constexpr kEyeStormMs = 6000;
    std::uint32_t constexpr kEyeTickMs = 1000;
    inline constexpr NH<float> kEyeRadius{ 8.f, 6.f };
    inline constexpr NH<float> kEyeStormPct{ 10.f, 15.f };
    float constexpr kEyeMinFromBossYd = 10.f;
    float constexpr kEyeMaxFromBossYd = 14.f;
    float constexpr kEyeAimYd = 12.f;               // the pick's centre: 12 yd from him toward the plaza
    float constexpr kEyeAimSlackYd = 2.f;
    // The storm reaches the whole plaza: the real hit is a hidden donut out to kEyeStormReachYd; the drawn donut (a
    // Decoy) keeps the inner / outer ratio at 0.25, the smallest the marker draws with a hole (BM README "Donut
    // ratios"; orchestrator ruling: Donut(8, 32), heroic 6 / 24 the same way).
    float constexpr kEyeStormReachYd = 60.f;
    float constexpr kEyeDrawnRatio = 0.25f;
    constexpr float EyeDrawnOuter(float inner) { return inner / kEyeDrawnRatio; }
    // Heroic drift: 1.5 yd/s for the 6 s storm (9 yd).
    float constexpr kEyeDriftSpeed = 1.5f;
    float constexpr kEyeDriftYd = kEyeDriftSpeed * float(kEyeStormMs) / 1000.f;
    float constexpr kEyeDriftMinLegYd = 0.5f;       // a shorter free run turns back at once
    // The falling ice (looks only, no hit of their own): storm stalkers in a ring around the eye, outside every spot
    // the eye can cover: the eye's radius, its drift and the look's own 3 yd half width.
    std::uint32_t constexpr kStormLookCount = 6;
    float constexpr kStormLookHalfWidthYd = 3.f;
    inline constexpr NH<float> kStormLookRingYd{ 8.f + kStormLookHalfWidthYd + 1.f,
        6.f + kEyeDriftYd + kStormLookHalfWidthYd };

    // MK6: Frostbolt 17503 (stock, DD-scaled on heroic) on the tank every 2.9 to 3.7 s; it waits for his mechanic
    // casts and never starts in the kFrostboltClearMs before one (a 2 s cast and a margin).
    std::uint32_t constexpr kFrostboltMinMs = 2900;
    std::uint32_t constexpr kFrostboltMaxMs = 3700;
    std::uint32_t constexpr kFrostboltClearMs = 2200;

    // Melee: DamageModifier 3.5 on normal (the stock value, kept); heroic is the heroic template's tier (WP-T).

    std::uint32_t constexpr kRetryMs = 2000;        // nobody to target: try again this soon

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    struct Candidate
    {
        std::uint64_t id = 0;
        std::uint32_t stacks = 0;       // Icy Death on them
        bool tank = false;              // his victim
        bool held = false;              // in an Ice Tomb
    };

    // MK1: a random non-tank without Icy Death; if all have it, the one with the fewest stacks (ties random). Never
    // the tank, never a prisoner, never a player at the cap (the next stack is the tomb's, not the curse's). `rand(n)`
    // returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickCurseTarget(std::vector<Candidate> const& c, Rand&& rand)
    {
        std::vector<std::size_t> fresh;
        std::vector<std::size_t> fewest;
        std::uint32_t low = kCurseMaxStacks;
        for (std::size_t i = 0; i < c.size(); ++i)
        {
            if (c[i].tank || c[i].held || c[i].stacks >= kCurseMaxStacks)
                continue;
            if (!c[i].stacks)
            {
                fresh.push_back(i);
                continue;
            }
            if (c[i].stacks < low)
            {
                low = c[i].stacks;
                fewest.clear();
            }
            if (c[i].stacks == low)
                fewest.push_back(i);
        }
        std::vector<std::size_t> const& pool = fresh.empty() ? fewest : fresh;
        if (pool.empty())
            return std::nullopt;
        return pool[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())))];
    }

    // MK3: the carrier with the most stacks (ties random); nobody with stacks: nullopt (no Siphon).
    template <class Rand>
    std::optional<std::size_t> PickSiphonCarrier(std::vector<Candidate> const& c, Rand&& rand)
    {
        std::vector<std::size_t> best;
        std::uint32_t high = 0;
        for (std::size_t i = 0; i < c.size(); ++i)
        {
            if (c[i].tank || c[i].held || !c[i].stacks)
                continue;
            if (c[i].stacks > high)
            {
                high = c[i].stacks;
                best.clear();
            }
            if (c[i].stacks == high)
                best.push_back(i);
        }
        if (best.empty())
            return std::nullopt;
        return best[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(best.size())))];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MK1 growth, MK2 / MK3 / MK4 numbers
    // ----------------------------------------------------------------------------------------------------------------

    // One carrier's growth clock: the stacks `diff` ms adds.
    struct CurseClock
    {
        std::uint32_t ms = 0;

        std::uint32_t Advance(std::uint32_t diff, bool heroic)
        {
            std::uint32_t const every = kCurseGrowMs(heroic);
            ms += diff;
            std::uint32_t const grown = ms / every;
            ms -= grown * every;
            return grown;
        }
    };

    constexpr bool Freezes(std::uint32_t stacks)
    {
        return stacks >= kCurseMaxStacks;
    }

    // The time from landing to the tomb with nothing done (ST: 24 s normal, 16 s heroic).
    constexpr std::uint32_t MsToTomb(bool heroic)
    {
        return (kCurseMaxStacks - 1) * kCurseGrowMs(heroic);
    }

    // The nova's percent for the stacks the carrier had (at most 4: the fifth is the tomb's).
    constexpr float ShatterPct(std::uint32_t stacks, bool heroic)
    {
        return float(std::min(stacks, kCurseMaxStacks - 1)) * kShatterPctPerStack(heroic);
    }

    // The tether snaps once the carrier is this far from their spot at the cast's start (on the map plane).
    inline bool SiphonSnaps(Vec2 spot, Vec2 carrier)
    {
        return DungeonKit::Distance(spot, carrier) >= kSiphonSnapYd;
    }

    // Whole stacks eaten after `channelMs` of the channel (one a second, the first at 1 s), at most `had`.
    constexpr std::uint32_t StacksEaten(std::uint32_t channelMs, std::uint32_t had)
    {
        std::uint32_t const eaten = std::min(channelMs, kSiphonChannelMs) / kSiphonEatMs;
        return eaten < had ? eaten : had;
    }

    // `pct` percent of `maxHealth`, rounded.
    constexpr std::uint32_t PctOf(std::uint32_t maxHealth, float pct)
    {
        return static_cast<std::uint32_t>(double(maxHealth) * double(pct) / 100.0 + 0.5);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). A beat that comes due
    // while he casts stays due until he is free (the Eye's marker excepted: it is not a cast).
    // ----------------------------------------------------------------------------------------------------------------

    enum class EyeStage : std::uint8_t
    {
        Idle,
        Marker,     // the 3 s marker (phase kPhaseEye)
        Storm,      // the 6 s storm (phase kPhaseEye)
    };

    struct Timeline
    {
        std::uint32_t now = 0;                          // ms since the pull
        std::uint32_t nextCurse = kCurseFirstMs;
        std::uint32_t nextSiphon = kSiphonFirstMs;      // the 15 / 35 / 55 ... grid
        std::uint32_t nextEye = kEyeFirstMs;            // the marker's start
        std::uint32_t nextFrostbolt = kFrostboltMinMs;
        EyeStage eye = EyeStage::Idle;
        std::uint32_t eyeAt = 0;                        // the current stage's start

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        bool CurseDue() const { return now >= nextCurse; }
        void CurseDone() { nextCurse = now + kCurseEveryMs; }
        void CurseRetry() { nextCurse = now + kRetryMs; }

        bool SiphonDue() const { return now >= nextSiphon; }
        // Fired or skipped (no carrier): the next one stays on the grid; one held past a whole period skips it.
        void SiphonDone()
        {
            nextSiphon += kSiphonEveryMs;
            while (nextSiphon <= now)
                nextSiphon += kSiphonEveryMs;
        }

        bool EyeDue() const { return eye == EyeStage::Idle && now >= nextEye; }
        void EyeMarked()
        {
            eye = EyeStage::Marker;
            eyeAt = now;
            nextEye += kEyeEveryMs;
            while (nextEye <= now)
                nextEye += kEyeEveryMs;
        }
        // The marker's end: the storm starts now.
        bool StormDue() const { return eye == EyeStage::Marker && now >= eyeAt + kEyeMarkerMs; }
        void StormStarted()
        {
            eye = EyeStage::Storm;
            eyeAt = now;
        }
        bool StormOver() const { return eye == EyeStage::Storm && now >= eyeAt + kEyeStormMs; }
        void EyeOver() { eye = EyeStage::Idle; }
        // The ms left of the marker (Marker) or the storm (Storm); 0 when idle.
        std::uint32_t EyeLeftMs() const
        {
            std::uint32_t const len = eye == EyeStage::Marker ? kEyeMarkerMs : eye == EyeStage::Storm ? kEyeStormMs : 0;
            std::uint32_t const gone = now - eyeAt;
            return gone >= len ? 0 : len - gone;
        }

        // The next storm's start (marked: its known start; storming: now; idle: the next marker's plus the marker).
        std::uint32_t NextStormAt() const
        {
            if (eye == EyeStage::Marker)
                return eyeAt + kEyeMarkerMs;
            if (eye == EyeStage::Storm)
                return now;
            return nextEye + kEyeMarkerMs;
        }

        // Frostbolt waits for his mechanic casts: never during the Siphon or the storm, never within
        // kFrostboltClearMs of a due Siphon or a storm's start.
        bool FrostboltDue() const { return now >= nextFrostbolt; }
        bool FrostboltClear(bool siphonBusy) const
        {
            if (siphonBusy || eye == EyeStage::Storm)
                return false;
            if (nextSiphon <= now + kFrostboltClearMs)
                return false;
            return NextStormAt() > now + kFrostboltClearMs;
        }
        void FrostboltDone(std::uint32_t every) { nextFrostbolt = now + every; }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // MK5 the eye
    // ----------------------------------------------------------------------------------------------------------------

    // The eye's aim: kEyeAimYd from him toward his plaza (his arena's centre), or along his spawn facing when he stands
    // on the centre itself. The pick (PickFloorSpot) takes a floor point within kEyeAimSlackYd of it.
    inline Vec2 EyeAim(Vec2 boss, Vec2 plaza, float spawnFacing)
    {
        float const bearing = DungeonKit::Distance(boss, plaza) > 1.f ? DungeonKit::BearingTo(boss, plaza)
            : spawnFacing;
        return DungeonKit::Advance(boss, bearing, kEyeAimYd);
    }

    inline bool EyeSpotFits(Vec2 boss, Vec2 eye)
    {
        float const d = DungeonKit::Distance(boss, eye);
        return d >= kEyeMinFromBossYd - 0.01f && d <= kEyeMaxFromBossYd + 0.01f;
    }

    // The heroic drift: `freeYd` of floor ahead in the chosen direction (the raycast's first wall, or the arena's
    // edge, whichever is nearer). Legs as distances along the direction: forward `freeYd` (at most the whole drift),
    // then back for what is left. A wall closer than kEyeDriftMinLegYd turns it at once: the whole drift runs back.
    struct DriftLegs
    {
        float forward = 0.f;    // yd along the direction
        float back = 0.f;       // then yd back along it
    };

    inline DriftLegs EyeDriftLegs(float freeYd, float total = kEyeDriftYd)
    {
        DriftLegs legs;
        float const free = std::max(0.f, freeYd);
        if (free < kEyeDriftMinLegYd)
        {
            legs.back = total;
            return legs;
        }
        legs.forward = std::min(free, total);
        legs.back = total - legs.forward;
        return legs;
    }

    // Where a ray from `start` along `bearing` leaves the circle (`center`, `radius`): the distance; 0 when `start`
    // is outside it.
    inline float RayLeavesCircle(Vec2 start, float bearing, Vec2 center, float radius)
    {
        float const dx = std::cos(bearing);
        float const dy = std::sin(bearing);
        float const px = start.x - center.x;
        float const py = start.y - center.y;
        float const c = px * px + py * py - radius * radius;
        if (c > 0.f)
            return 0.f;
        float const b = px * dx + py * dy;
        return -b + std::sqrt(std::max(0.f, b * b - c));
    }

    // The storm stalkers' ring: `count` points `ring` yd from the eye's start, evenly spaced from `phase`.
    inline std::vector<Vec2> StormLookRing(Vec2 eye, float ring, std::uint32_t count = kStormLookCount,
        float phase = 0.f)
    {
        std::vector<Vec2> out;
        out.reserve(count);
        for (std::uint32_t i = 0; i < count; ++i)
            out.push_back(DungeonKit::Advance(eye, phase + DungeonKit::kTwoPi * float(i) / float(count), ring));
        return out;
    }
}

#endif
