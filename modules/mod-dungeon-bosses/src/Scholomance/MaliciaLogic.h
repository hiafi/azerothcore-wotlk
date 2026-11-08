/*
 * mod-dungeon-bosses, Scholomance S5: Instructor Malicia (10505), the pure, host-testable part (no engine headers): the
 * spell ids, the per-difficulty tuning, the Soul meter's rules, the never-paused fight timeline, the Soulstorm waves,
 * the floor picks of the Coven and the numbers of her detention lesson and her examiner mode. Build spec: SC 1431-1488
 * (build spec), SC 1250-1430 (design: pitch B "Soul stacks", approved 2026-10-31), MA1-MA9; handoff section 3.4 rows
 * MA, section 3.5 row S5, section 3.6 (normal 160k, heroic 250k, examiner 80k), section 3.7 (the Coven's lesson).
 *
 * Damage percentages are of the reference health row (normal 3,670 / heroic 4,120 non-tank at level 60).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_MALICIA_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_MALICIA_LOGIC_H

#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>

namespace ScholoMalicia
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsMalicia;

    // Declared in apps/dbc-tools source/npcs/scholomance/instructor_malicia.py (same ids).
    enum MaliciaSpells : std::uint32_t
    {
        SPELL_MA_SOUL               = 206205,   // MA1 the visible meter: 20 at the pull, floor 10, cap 40 (stacks only)
        SPELL_MA_SOUL_WEIGHT        = 206206,   // MA1 the hidden weight: damage, healing, max health (stacks-20) x 5%
        SPELL_MA_SOUL_DRAIN_CAST    = 206207,   // MA2 the 2 s cast bar (not interruptible)
        SPELL_MA_SOUL_DRAIN         = 206208,   // MA2 the drain's impact on each drained player (Drain Soul's look)
        SPELL_MA_BOUND_SOUL         = 206209,   // MA5 her buff: +2% damage a stack, cap 20
        SPELL_MA_SHADE_VOLLEY       = 206210,   // MA4 the shade's 2 s kickable cast; on completion the stock 17228
        SPELL_MA_SOULSTORM_CAST     = 206211,   // MA6 the 3.5 s cast bar (the three waves land inside it)
        SPELL_MA_SOULSTORM_FALL     = 206212,   // MA6 a falling soul: a missile from her to a marker
        SPELL_MA_SOULSTORM_BLAST    = 206213,   // MA6 the 4 yd blast: resolve copy (Shadow)
        SPELL_MA_SOULSTORM_BURST    = 206214,   // MA6 the burst's look at the marker as it lands (every marker)
        SPELL_MA_SHADOW_HEAL        = 206215,   // MA7 the 3.5 s kickable cast: heals her, then triggers the nova
        SPELL_MA_SHADOW_NOVA        = 206216,   // MA7 the burst on every player (RefFlat at launch)
        SPELL_MA_SOUL_LOST          = 206217,   // detention: a soul faded: the lesson's failure hit (RefFlat, Weakened)
        // 206218-206224 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_MA_SOUL), "Malicia's spells sit in her slice");
    static_assert(kSpellSlice.Contains(SPELL_MA_SOUL_LOST), "Malicia's spells sit in her slice");

    // Stock spells she and her shades keep (SC "Stock kit"): Slow 13747 and Corruption 18376 (ScholomanceRework.h
    // SPELL_CORRUPTION), the shades' Shadow Bolt Volley 17228 (the custom kickable cast triggers it).
    std::uint32_t constexpr SPELL_MA_SLOW = 13747;
    std::uint32_t constexpr SPELL_MA_CORRUPTION = 18376;
    std::uint32_t constexpr SPELL_MA_STOCK_SHADOW_BOLT_VOLLEY = 17228;
    // Her examiner's tint (source/npcs/scholomance/_visuals.py AURA_GHOST_VISUAL: Ghost Visual 9617, SV 886).
    std::uint32_t constexpr SPELL_EXAMINER_GHOST_VISUAL = 9617;

    // Registry tags (the build spec's MA numbers).
    enum MaliciaTags : std::uint32_t
    {
        TAG_LOOSE_SOUL      = 3,    // MA3 a soul's Soak (never resolves: the pickup takes it or it fades)
        TAG_SOULSTORM       = 6,    // MA6 one marker of a wave
    };

    // ----------------------------------------------------------------------------------------------------------------
    // MA1 Soul: every player of the fight, 20 at the pull; each stack is 5% of damage, healing and max health both ways
    // (20 = 100%); floor 10 (50%), cap 40 (200%).
    // ----------------------------------------------------------------------------------------------------------------

    std::uint32_t constexpr kSoulStart = 20;
    std::uint32_t constexpr kSoulFloor = 10;
    std::uint32_t constexpr kSoulCap = 40;
    std::int32_t constexpr kSoulPctPerStack = 5;

    // The weight's percent for `stacks` (damage done, healing done, max health): 0 at 20, -50 at 10, +100 at 40. No
    // aura (0 stacks) is no weight.
    constexpr std::int32_t SoulModPct(std::uint32_t stacks)
    {
        if (stacks == 0)
            return 0;
        std::uint32_t const s = std::clamp(stacks, kSoulFloor, kSoulCap);
        return (static_cast<std::int32_t>(s) - static_cast<std::int32_t>(kSoulStart)) * kSoulPctPerStack;
    }

    // The meter after `delta`, held in [floor, cap] (a meter already under the floor never drops further).
    constexpr std::uint32_t SoulAfter(std::uint32_t current, std::int32_t delta)
    {
        std::int64_t const v = static_cast<std::int64_t>(current) + delta;
        std::int64_t const lo = std::min<std::int64_t>(current, kSoulFloor);
        return static_cast<std::uint32_t>(std::clamp<std::int64_t>(v, lo, kSoulCap));
    }

    // MA2: a drain takes up to 4 stacks, never below the floor; each stack taken lands as one Loose Soul (zero-sum).
    std::uint32_t constexpr kDrainStacks = 4;
    constexpr std::uint32_t DrainLoss(std::uint32_t stacks, std::uint32_t want = kDrainStacks)
    {
        return stacks > kSoulFloor ? std::min(want, stacks - kSoulFloor) : 0u;
    }

    // MA3: walking through a soul gives one stack; a player at the cap (or with no meter: not in the fight) leaves it.
    constexpr bool CanTakeSoul(std::uint32_t stacks)
    {
        return stacks > 0 && stacks < kSoulCap;
    }

    // MA6: a blast destroys one stack (nothing spills), never below the floor.
    constexpr std::uint32_t BlastLoss(std::uint32_t stacks)
    {
        return stacks > kSoulFloor ? 1u : 0u;
    }

    // MA3 Loose Soul: 2 yd walk-in pickup; fades after 8 s (normal) / 5 s (heroic) and goes to her (MA5). Souls land at
    // random floor spots 10 to 15 yd around their drained player; a shade's 4 land where it dies.
    float constexpr kSoulRadius = 2.f;
    float constexpr kSoulZBand = 4.f;
    inline constexpr NH<std::uint32_t> kSoulFadeMs{ 8000, 5000 };
    float constexpr kSoulSpillMinYd = 10.f;
    float constexpr kSoulSpillMaxYd = 15.f;
    float constexpr kShadeSpillMaxYd = 3.f;             // a dead shade's souls: around its body
    float constexpr kSoulsApartYd = 2.5f;               // souls of one spill land at least this far apart (if they can)
    std::uint32_t constexpr kSoulPollMs = 250;
    float constexpr kSoulHoverZ = 1.0f;                 // the wisp floats this high over its spot
    float constexpr kSoulFlySpeed = 14.f;               // a faded soul flies to her (yd/s), then is gone
    std::uint32_t constexpr kSoulFlyMs = 2500;
    // The bots' Soak per soul (BM Soak + Order): lowest Soul first, nobody at the cap; it never resolves (cancelled at
    // the pickup or the fade; its warning runs this long past the fade).
    std::uint32_t constexpr kSoulSoakSlackMs = 5000;

    // ----------------------------------------------------------------------------------------------------------------
    // MA5 Bound Soul: a faded soul is 1, a shade that walks in is 4; +2% damage a stack, cap 20 (+40%).
    // ----------------------------------------------------------------------------------------------------------------

    std::uint32_t constexpr kBoundPctPerStack = 2;
    std::uint32_t constexpr kBoundCap = 20;
    std::uint32_t constexpr kBoundPerSoul = 1;
    std::uint32_t constexpr kBoundPerShade = 4;

    constexpr std::uint32_t BoundAfter(std::uint32_t current, std::uint32_t add)
    {
        return std::min(kBoundCap, current + add);
    }

    // The aura raises her melee and stock spells; her own spells (Soulstorm, Shadow Nova) ignore caster modifiers (the
    // reference row is the number), so the AI scales their percent by the same factor.
    constexpr float BoundDamageScale(std::uint32_t stacks)
    {
        return 1.f + float(std::min(stacks, kBoundCap) * kBoundPctPerStack) / 100.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers and numbers (SC "Timers", the build spec table)
    // ----------------------------------------------------------------------------------------------------------------

    // MA2 Soul Drain: 10 s, then every 20 s (normal) / 30 s (heroic); a 2 s cast. Normal: one random non-tank, two
    // below 50% of her health, never the tank. Heroic: every player, the tank included.
    std::uint32_t constexpr kDrainFirstMs = 10000;
    inline constexpr NH<std::uint32_t> kDrainEveryMs{ 20000, 30000 };
    std::uint32_t constexpr kDrainCastMs = 2000;
    float constexpr kDrainTwoBelowPct = 50.f;

    constexpr std::uint32_t NormalDrainTargets(float healthPct)
    {
        return healthPct < kDrainTwoBelowPct ? 2u : 1u;
    }

    // MA4 Call a Student: 15 s, then every 25 s; 1 shade (normal) / 2 (heroic), 15 to 25 yd from her. Killed: 4 souls
    // where it dies. Alive 20 s: it walks into her (+4 Bound Soul). 12k / 18k health (the template, WP-H's override).
    std::uint32_t constexpr kCallFirstMs = 15000;
    std::uint32_t constexpr kCallEveryMs = 25000;
    inline constexpr NH<std::uint32_t> kShadeCount{ 1, 2 };
    float constexpr kShadeMinYd = 15.f;
    float constexpr kShadeMaxYd = 25.f;
    float constexpr kShadeApartYd = 6.f;                // two heroic shades rise at least this far apart
    std::uint32_t constexpr kShadeSouls = 4;
    std::uint32_t constexpr kShadeWalkInMs = 20000;
    float constexpr kShadeBindYd = 3.f;                 // this close to her, the shade is bound (+4)
    std::uint32_t constexpr kShadeRepathMs = 1000;
    inline constexpr NH<std::uint32_t> kShadeHealth{ 12000, 18000 };
    // The shades' Volley (the stock 17228 behind a 2 s kickable cast): first after 4 s, then every 8 s while it stands.
    std::uint32_t constexpr kShadeVolleyFirstMs = 4000;
    std::uint32_t constexpr kShadeVolleyEveryMs = 8000;
    std::uint32_t constexpr kShadeVolleyCastMs = 2000;

    // MA6 Soulstorm: 20 s, then every 30 s. 3 waves 1 s apart, 4 yd markers, 1.5 s each. Normal: each wave one random
    // non-tank plus 2 random spots, and it waits while a drain's souls lie on the floor. Heroic: each wave every player
    // plus 1 random spot. A player's marker is centered 2 yd from them at a random bearing; random spots never within
    // 6 yd of a player. 20% / 30% Shadow, and the hit destroys one Soul stack (in place of Weakened); souls under a
    // blast are destroyed.
    std::uint32_t constexpr kStormFirstMs = 20000;
    std::uint32_t constexpr kStormEveryMs = 30000;
    std::uint32_t constexpr kStormWaves = 3;
    std::uint32_t constexpr kStormWaveGapMs = 1000;
    std::uint32_t constexpr kStormWarnMs = 1500;
    std::uint32_t constexpr kStormCastMs = (kStormWaves - 1) * kStormWaveGapMs + kStormWarnMs;    // 3.5 s
    float constexpr kStormRadius = 4.f;
    float constexpr kStormOffsetYd = 2.f;
    inline constexpr NH<std::uint32_t> kStormRandomSpots{ 2, 1 };
    float constexpr kStormSpotMinFromPlayerYd = 6.f;
    inline constexpr NH<float> kStormPct{ 20.f, 30.f };
    std::uint32_t constexpr kStormWaitRetryMs = 1000;   // normal: a drain's souls still down, look again this soon
    float constexpr kStormFallSpeed = 20.f;             // the falling soul's missile (instructor_malicia.py Speed)

    // Normal Soulstorm never starts while a drain's souls are on the floor (SC Timers); heroic always may.
    constexpr bool StormMayStart(bool heroic, std::size_t drainSoulsOnFloor)
    {
        return heroic || drainSoulsOnFloor == 0;
    }

    // Players marked in one wave: normal 1 non-tank (when one exists), heroic everyone.
    constexpr std::size_t StormPlayersPerWave(bool heroic, std::size_t players, std::size_t nonTanks)
    {
        return heroic ? players : std::min<std::size_t>(1, nonTanks);
    }

    // The ms after the marker's registration to launch the falling soul so it lands as the marker resolves (a far
    // marker launches at once and lands a little late).
    constexpr std::uint32_t FallLaunchDelayMs(float distance, std::uint32_t warnMs = kStormWarnMs,
        float speed = kStormFallSpeed)
    {
        float const flightMs = speed > 0.f ? distance / speed * 1000.f : 0.f;
        return flightMs >= float(warnMs) ? 0u : static_cast<std::uint32_t>(float(warnMs) - flightMs);
    }

    // MA7 Shadow Heal: below 50%, every 20 s (the first as she crosses 50%); 3.5 s kickable cast; heals her 5% / 10% of
    // her max health and bursts on every player for 15% / 40% Shadow.
    float constexpr kHealBelowPct = 50.f;
    std::uint32_t constexpr kHealEveryMs = 20000;
    std::uint32_t constexpr kHealCastMs = 3500;
    inline constexpr NH<float> kHealSelfPct{ 5.f, 10.f };
    inline constexpr NH<float> kHealBurstPct{ 15.f, 40.f };
    float constexpr kHealBurstRadius = 60.f;            // every player in the Coven (the room is 57 yd long)

    // MA8 Slow (stock 13747): 13 to 15 s, then 20 to 35 s. MA9 Corruption (stock 18376): 3 to 12 s, then 17 to 22 s.
    std::uint32_t constexpr kSlowFirstMinMs = 13000;
    std::uint32_t constexpr kSlowFirstMaxMs = 15000;
    std::uint32_t constexpr kSlowEveryMinMs = 20000;
    std::uint32_t constexpr kSlowEveryMaxMs = 35000;
    std::uint32_t constexpr kCorruptionFirstMinMs = 3000;
    std::uint32_t constexpr kCorruptionFirstMaxMs = 12000;
    std::uint32_t constexpr kCorruptionEveryMinMs = 17000;
    std::uint32_t constexpr kCorruptionEveryMaxMs = 22000;
    float constexpr kSlowRadius = 20.f;                 // the stock spell's area (cast only with a player inside)
    float constexpr kCorruptionRadius = 10.f;

    // Melee: DamageModifier 3.5 (the AC base value; live 5 was mod-progression's), set by the DT file; heroic is the
    // heroic template's tier (WP-T).

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). A beat that comes due
    // while she casts stays due until the cast ends.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        Drain = 0,
        Call = 1,
        Soulstorm = 2,
        ShadowHeal = 3,
        Slow = 4,
        Corruption = 5,
    };
    std::size_t constexpr kBeatCount = 6;
    std::uint32_t constexpr kRetryMs = 2000;            // nobody to target: try again this soon
    std::uint32_t constexpr kNever = std::numeric_limits<std::uint32_t>::max();

    struct Timeline
    {
        std::uint32_t now = 0;      // ms since the pull
        // Shadow Heal waits for 50% (Arm); Slow and Corruption take their first roll at the pull (Start).
        std::array<std::uint32_t, kBeatCount> next{ { kDrainFirstMs, kCallFirstMs, kStormFirstMs, kNever, kNever,
            kNever } };

        // The pull: the stock spells' first casts, rolled by the caller in their ranges.
        void Start(std::uint32_t slowFirstMs, std::uint32_t corruptionFirstMs)
        {
            next[static_cast<std::size_t>(Beat::Slow)] = slowFirstMs;
            next[static_cast<std::size_t>(Beat::Corruption)] = corruptionFirstMs;
        }

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        bool Due(Beat b) const
        {
            std::uint32_t const at = next[static_cast<std::size_t>(b)];
            return at != kNever && now >= at;
        }

        bool Armed(Beat b) const
        {
            return next[static_cast<std::size_t>(b)] != kNever;
        }

        // MA7: she fell below 50%: the heal is due now (once; later calls keep the schedule).
        void Arm(Beat b)
        {
            if (!Armed(b))
                next[static_cast<std::size_t>(b)] = now;
        }

        // Switched off (the examiner leaves out a mechanic).
        void Disable(Beat b)
        {
            next[static_cast<std::size_t>(b)] = kNever;
        }

        // Fired: the next one `everyMs` from now.
        void Done(Beat b, std::uint32_t everyMs)
        {
            next[static_cast<std::size_t>(b)] = now + everyMs;
        }

        // Not now (nobody to target, a normal Soulstorm waiting for the floor): try again `ms` from now.
        void Retry(Beat b, std::uint32_t ms = kRetryMs)
        {
            next[static_cast<std::size_t>(b)] = now + ms;
        }

        std::uint32_t In(Beat b) const
        {
            std::uint32_t const at = next[static_cast<std::size_t>(b)];
            return at == kNever ? kNever : (at > now ? at - now : 0u);
        }
    };

    // The cooldown after a fire of the fixed beats (Slow and Corruption roll theirs in [min, max] in the AI).
    constexpr std::uint32_t EveryMs(Beat b, bool heroic)
    {
        switch (b)
        {
            case Beat::Drain:       return kDrainEveryMs(heroic);
            case Beat::Call:        return kCallEveryMs;
            case Beat::Soulstorm:   return kStormEveryMs;
            case Beat::ShadowHeal:  return kHealEveryMs;
            case Beat::Slow:        return kSlowEveryMinMs;
            case Beat::Corruption:  return kCorruptionEveryMinMs;
        }
        return kRetryMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Coven's floor (ScholomanceRework.h kCovenFloor, NAVMESH-REPORT section 5): the main room x 90-137 (19 yd
    // wide) plus her apse (x 80-89.5, y -4..1). The gate step (x 137 on) is not floor for souls, shades or markers.
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kApseMinX = 80.0f;
    float constexpr kApseMaxX = 90.0f;
    float constexpr kApseMinY = -4.0f;
    float constexpr kApseMaxY = 1.0f;
    float constexpr kFloorInset = 1.0f;                 // stay this far off the walls

    inline bool OnCovenFloor(Vec2 p, float inset = kFloorInset)
    {
        DungeonKit::FrameRect const& f = ScholomanceRework::kCovenFloor;
        Vec2 const q = DungeonKit::ToFrame(f, p);
        bool const room = q.x >= inset && q.x <= f.sizeX - inset && q.y >= inset && q.y <= f.sizeY - inset;
        bool const apse = p.x >= kApseMinX + inset && p.x <= kApseMaxX && p.y >= kApseMinY + inset * 0.5f
            && p.y <= kApseMaxY - inset * 0.5f;
        return room || apse;
    }

    // The nearest point of the main room (less the inset): the fallback when no random pick lands on the floor.
    inline Vec2 ClampToCovenFloor(Vec2 p, float inset = kFloorInset)
    {
        if (OnCovenFloor(p, inset))
            return p;
        DungeonKit::FrameRect const& f = ScholomanceRework::kCovenFloor;
        Vec2 const q = DungeonKit::ToFrame(f, p);
        float const fx = std::clamp(q.x, inset, f.sizeX - inset);
        float const fy = std::clamp(q.y, inset, f.sizeY - inset);
        return DungeonKit::FramePoint(f, fx, fy);
    }

    // True when `p` is at least `minYd` from every point of `others`.
    inline bool FarFromAll(Vec2 p, std::span<Vec2 const> others, float minYd)
    {
        for (Vec2 const& o : others)
            if (DungeonKit::Distance(p, o) < minYd)
                return false;
        return true;
    }

    // A random floor point `minYd` to `maxYd` from `center` and at least `apartYd` from every point of `avoid`, after
    // up to `tries` draws; nullopt when none landed. `rand01()` returns a float in [0, 1).
    template <class Rand01>
    std::optional<Vec2> PickRingPoint(Vec2 center, float minYd, float maxYd, std::span<Vec2 const> avoid, float apartYd,
        Rand01&& rand01, std::uint32_t tries = 64)
    {
        for (std::uint32_t i = 0; i < tries; ++i)
        {
            float const bearing = rand01() * DungeonKit::kTwoPi;
            float const dist = minYd + rand01() * (maxYd - minYd);
            Vec2 const p = DungeonKit::Advance(center, bearing, dist);
            if (OnCovenFloor(p) && FarFromAll(p, avoid, apartYd))
                return p;
        }
        return std::nullopt;
    }

    // A random floor point of the main room at least `apartYd` from every point of `avoid` (Soulstorm's random spots);
    // nullopt after `tries` misses.
    template <class Rand01>
    std::optional<Vec2> PickRoomPoint(std::span<Vec2 const> avoid, float apartYd, Rand01&& rand01,
        std::uint32_t tries = 64)
    {
        DungeonKit::FrameRect const& f = ScholomanceRework::kCovenFloor;
        for (std::uint32_t i = 0; i < tries; ++i)
        {
            float const fx = kFloorInset + rand01() * (f.sizeX - 2.f * kFloorInset);
            float const fy = kFloorInset + rand01() * (f.sizeY - 2.f * kFloorInset);
            Vec2 const p = DungeonKit::FramePoint(f, fx, fy);
            if (FarFromAll(p, avoid, apartYd))
                return p;
        }
        return std::nullopt;
    }

    // MA6: a player's marker, centered kStormOffsetYd from them at `bearing` (the marker is the exact blast circle).
    inline Vec2 OffsetMarker(Vec2 player, float bearing)
    {
        return DungeonKit::Advance(player, bearing, kStormOffsetYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Detention: the Coven's solo lesson (SC 2965; handoff section 3.7): drained on landing, 3 / 4 souls spill around
    // the student and fade in 10 / 6 s; the student passes by picking up all of them. A fade is a failure: the lesson's
    // failure hit (15% / 25% + Weakened, SoloLesson.h LessonFailurePct). It works with or without her.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<std::uint32_t> kLessonSouls{ 3, 4 };
    inline constexpr NH<std::uint32_t> kLessonFadeMs{ 10000, 6000 };
    // The lesson's souls land closer than the fight's (10-15 yd): four souls in 6 s must be a walk, not a sprint. The
    // student lands in her apse (17943's point, 5 yd wide), so the souls spill around the apse's mouth, in the room.
    float constexpr kLessonSpillMinYd = 3.f;
    float constexpr kLessonSpillMaxYd = 6.f;
    float constexpr kLessonSoulsApartYd = 3.f;
    inline constexpr Vec2 kApseMouth{ 92.0f, -1.5f };

    // Where the lesson's souls spill around: the student, or the apse's mouth when the student stands in the apse (or
    // off the floor).
    inline Vec2 LessonSpillCenter(Vec2 student)
    {
        DungeonKit::FrameRect const& f = ScholomanceRework::kCovenFloor;
        Vec2 const q = DungeonKit::ToFrame(f, student);
        bool const inRoom = q.x >= kFloorInset && q.x <= f.sizeX - kFloorInset && q.y >= kFloorInset
            && q.y <= f.sizeY - kFloorInset;
        return inRoom ? student : kApseMouth;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Examiner mode (S13, the Graduate Exam; SC 3046): the same fight at heroic values on the examiner entry
    // (NPC_SC_EXAMINER_MALICIA 300548), 80k, with no boss state, gates or grades.
    // ----------------------------------------------------------------------------------------------------------------

    std::uint32_t constexpr kExaminerHealth = 80000;
}

#endif
