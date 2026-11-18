/*
 * mod-dungeon-bosses, Blackrock Depths D7:
 * Pyromancer Loregrain (9024), "Franclorn's last stand": the pure, host-testable part (no engine headers). Build spec
 * S2 165-219 (docs/dungeons/blackrock-depths-2-shadowforge-city.md, rulings 37-39 and 91), the moving ward S2 147-156,
 * handoff sections 3.4 / 3.5 / 3.6 / 3.8 rows D7, section 7 #21 and section 8 #18 / #36 (defaults built). Tested by
 * tests/brd_loregrain_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsLoregrain (211020-211049), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/loregrain.py
 *   Tuning         NH<> constants: one number per difficulty, straight from the build spec (5 players, not flex)
 *   The corridor   16 yd wide (NAVMESH, not the spec's 10-12), north-east from the statue; three ward spots, the
 *                  statue's moved onto the floor: (530.0, -243.5), (541, -254), (552, -264)
 *   The ward       LG3: 6 yd (heroic 5), -1 yd per living Defiling Totem (min 2); heroic, -1 yd per Wrath of
 *                  Ragnaros for the rest of the fight (base min 3). Locked at each tide's warning start (section 8
 *                  #18): the donut and the Stack of that tide never change radius
 *   The move       LG2: at each Fire Tide (never a Wrath, section 7 #21) the spirit appears at a neighboring spot:
 *                  from the middle either way, from an end to the middle (never end to end)
 *   Fury           LG6: a meter 0-100: +10 per Molten Blast landed, +3 a second while Fire Ward holds, +2 a second per
 *                  living totem; -15 per interrupted Molten Blast, -10 per totem killed, -20 when Fire Ward breaks or
 *                  is purged. At 100 Wrath of Ragnaros (LG7) fires and the meter drops to 30
 *   Fire Tide      LG1: 30% (heroic 45%) x (1 + Fury / 100), at most 75% (ruling 91); the Wrath uses the same rule at
 *                  the Fury it fired on (100: 60% / 75%)
 *   Patches        LG5: a tide washes away every Molten Splash patch whose center lies outside its (locked) ward
 *   The repel      the spirit keeps Loregrain out of the ward: inside it he is thrown clear (a computed landing in the
 *                  corridor); at its edge, with his victim inside, he holds there (and answers with Searing Bolt when
 *                  his victim is out of his reach, rule 10)
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_LOREGRAIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_LOREGRAIN_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace BrdLoregrain
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsLoregrain;

    enum LoregrainSpells : std::uint32_t
    {
        SPELL_LG_TIDE_HIT           = kSpellSlice.first + 0,    // 211020 LG1 Fire Tide (resolve copy, Fire)
        SPELL_LG_TIDE_CAST          = kSpellSlice.first + 1,    // 211021 LG1 the 4 s cast bar (Physical, no kick)
        SPELL_LG_WRATH_CAST_N       = kSpellSlice.first + 2,    // 211022 LG7 the Wrath's 4 s cast bar (normal)
        SPELL_LG_WRATH_CAST_H       = kSpellSlice.first + 3,    // 211023 LG7 the Wrath's 2 s cast bar (heroic)
        SPELL_LG_WRATH_HIT          = kSpellSlice.first + 4,    // 211024 LG7 Wrath of Ragnaros (resolve copy, Fire)
        SPELL_LG_WARD_REPEL         = kSpellSlice.first + 5,    // 211025 LG3 the spirit throws him clear (look)
        SPELL_LG_DEFILING_PRESENCE  = kSpellSlice.first + 6,    // 211026 LG4 the totem's tooltip aura (DUMMY)
        SPELL_LG_SPLASH_LOB         = kSpellSlice.first + 7,    // 211027 LG5 the lob to the marked spot (look)
        SPELL_LG_SPLASH_HIT         = kSpellSlice.first + 8,    // 211028 LG5 Molten Splash (resolve copy, Fire)
        SPELL_LG_PATCH_HIT          = kSpellSlice.first + 9,    // 211029 LG5 the patch's tick (resolve copy, Fire)
        SPELL_LG_PATCH_LOOK         = kSpellSlice.first + 10,   // 211030 LG5 the 4 yd lava pool on a stalker
        SPELL_LG_FURY               = kSpellSlice.first + 11,   // 211031 LG6 the meter (stacks 1-100 on him)
        SPELL_LG_FIRE_WARD          = kSpellSlice.first + 12,   // 211032 LG9 the absorb (any school, Magic)
        SPELL_LG_MOLTEN_BLAST       = kSpellSlice.first + 13,   // 211033 LG8 the 2 s kick (Fire, a copy of 15095)
        SPELL_LG_FLAME_SHOCK        = kSpellSlice.first + 14,   // 211034 LG10 the Magic DoT (a copy of 15616)
        SPELL_LG_SEARING_BOLT       = kSpellSlice.first + 15,   // 211035 his answer while he holds out of reach
        // 211036-211049 spare
    };
    static_assert(SPELL_LG_SEARING_BOLT <= kSpellSlice.last, "Loregrain's spells must stay in his slice");

    // creature_text groups (S2 "Text"; kTextRanges: 9024 0-4, 9542 0 (D10's copy uses 1)).
    enum LoregrainTexts : std::uint8_t
    {
        YELL_LG_PULL        = 0,    // "This shrine belongs to the Firelord now!"
        YELL_LG_TIDE        = 1,    // LG1 "Drown in Ragnaros's fire!"
        YELL_LG_WRATH       = 2,    // LG7 "The Firelord's fury overflows!"
        YELL_LG_DEATH       = 3,    // "The flame... gutters..."
        EMOTE_LG_WARD_MOVE  = 4,    // LG2 "Franclorn's spirit moves to new ground!" (boss emote, 41)
    };
    enum FranclornTexts : std::uint8_t
    {
        SAY_FRANCLORN_THANKS = 0,   // on Loregrain's death, at the statue
    };

    // Registry tags (the failure ledger, the logs and the G1 drill `ward` row: Stack/11 reported, Zone/12 gated).
    enum LoregrainTags : std::uint32_t
    {
        TAG_LG_SPLASH   = 1,    // LG5 the 2 s circle
        TAG_LG_PATCH    = 2,    // LG5 the lingering patch
        TAG_LG_WARD     = 11,   // LG1 / LG7 the ward's Stack (= G1 kBrdTagWard)
        TAG_LG_TIDE     = 12,   // LG1 / LG7 the donut (= G1 kBrdTagTide)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The corridor and the ward spots (handoff section 3.8 D7, NAVMESH 2.1: 15.5-16.5 yd wide from 5 to 40 yd)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kCorridorOrigin{ 530.0f, -243.5f };       // the statue spot (s = 0)
    inline constexpr Vec2 kCorridorAxis{ 0.7316f, -0.6817f };       // unit vector toward the far spot (north-east)
    inline constexpr float kCorridorHalfWidthYd = 8.f;
    inline constexpr float kCorridorUsableHalfYd = 6.5f;            // a landing stays 1.5 yd off the walls
    inline constexpr float kCorridorMinS = -4.f;                    // the statue end
    inline constexpr float kCorridorMaxS = 48.f;
    inline constexpr float kFloorZ = -43.f;                         // the spots' floor (the script snaps to the mesh)

    inline constexpr std::size_t kWardSpotCount = 3;
    inline constexpr std::array<Point3, kWardSpotCount> kWardSpots{ {
        { 530.0f, -243.5f, kFloorZ },   // 0 the statue (moved onto the floor; the statue spot is on the wall line)
        { 541.0f, -254.0f, kFloorZ },   // 1 the middle (19.1 yd from the statue spot)
        { 552.0f, -264.0f, kFloorZ },   // 2 the far end (14.9 yd from the middle)
    } };
    inline constexpr std::uint8_t kWardSpotAtPull = 0;              // the statue: the spirit's thanks, the reset
    // The ward forms at the first Fire Tide, not on the pull (orchestrator default after R-1, review Q1: a ward
    // formed on his spawn threw him toward the group on every pull). It forms at the middle spot (the move from the
    // statue); a totem planted before it stands where it will form.
    inline constexpr std::uint8_t kWardSpotFirst = 1;

    // Corridor coordinates of a point: s along the axis from the statue spot, w across it.
    struct CorridorPoint
    {
        float s = 0.f;
        float w = 0.f;
    };

    inline CorridorPoint ToCorridor(Vec2 p)
    {
        float const dx = p.x - kCorridorOrigin.x;
        float const dy = p.y - kCorridorOrigin.y;
        return { dx * kCorridorAxis.x + dy * kCorridorAxis.y, -dx * kCorridorAxis.y + dy * kCorridorAxis.x };
    }

    inline Vec2 FromCorridor(CorridorPoint c)
    {
        return { kCorridorOrigin.x + kCorridorAxis.x * c.s - kCorridorAxis.y * c.w,
            kCorridorOrigin.y + kCorridorAxis.y * c.s + kCorridorAxis.x * c.w };
    }

    // `p` clamped into the corridor's usable floor (1.5 yd off the walls, the statue end and the far end).
    inline Vec2 ClampToCorridor(Vec2 p)
    {
        CorridorPoint c = ToCorridor(p);
        c.s = std::clamp(c.s, kCorridorMinS, kCorridorMaxS);
        c.w = std::clamp(c.w, -kCorridorUsableHalfYd, kCorridorUsableHalfYd);
        return FromCorridor(c);
    }

    inline bool InCorridor(Vec2 p)
    {
        CorridorPoint const c = ToCorridor(p);
        return c.s >= kCorridorMinS - 1.f && c.s <= kCorridorMaxS + 1.f && std::fabs(c.w) <= kCorridorHalfWidthYd;
    }

    // LG2: the spot the spirit appears at for the next Fire Tide. From the middle either way (`towardFar` picks the
    // far end), from an end to the middle; never the same spot, never end to end (34 yd).
    constexpr std::uint8_t NextWardSpot(std::uint8_t current, bool towardFar)
    {
        if (current == 1)
            return towardFar ? 2 : 0;
        return 1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG3 Franclorn's Ward
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kWardBaseYd{ 6.f, 5.f };
    inline constexpr float kWardMinYd = 2.f;                        // the totems never shrink it below this
    inline constexpr float kWardPerTotemYd = 1.f;
    inline constexpr float kWardPerCrackYd = 1.f;                   // heroic, per Wrath of Ragnaros
    inline constexpr float kWardCrackFloorYd = 3.f;                 // heroic: the cracks stop the base here

    // The ward's radius now: the base (heroic: less the cracks, never below 3 yd), less 1 yd per living totem, never
    // below 2 yd. Normal never cracks (`cracks` is ignored).
    constexpr float WardRadius(bool heroic, std::uint32_t livingTotems, std::uint32_t cracks)
    {
        float base = kWardBaseYd(heroic);
        if (heroic)
            base = std::max(kWardCrackFloorYd, base - kWardPerCrackYd * float(cracks));
        return std::max(kWardMinYd, base - kWardPerTotemYd * float(livingTotems));
    }

    // The repel: he is inside the ward (less a 0.25 yd slack, so a boss standing on the edge is not thrown).
    inline constexpr float kRepelSlackYd = 0.25f;
    inline constexpr float kRepelLandYd = 3.f;                      // he lands this far outside the edge
    inline constexpr float kRepelJumpSpeedXY = 18.f;
    inline constexpr float kRepelJumpMinSpeedZ = 6.f;
    // A second throw waits this long after the first (the guard also skips him while he is in the jump; after the
    // landing it walks him to the ward's edge instead of chasing a victim inside it: R-1-A M2).
    inline constexpr std::uint32_t kRepelCooldownMs = 1000;

    constexpr bool RepelDue(float bossDistYd, float wardYd)
    {
        return bossDistYd < wardYd - kRepelSlackYd;
    }

    // Where he lands: straight out from the ward's center through him, `radius + kRepelLandYd` from the center,
    // clamped into the corridor. When the clamp pulls the landing back near the ward (a push toward a wall) or he
    // stands on the center, he goes along the corridor instead: toward the far end from the statue half, toward the
    // statue from the far half. The landing is at least radius + 1 yd from the center.
    inline Vec2 RepelLanding(Vec2 center, Vec2 boss, float radius)
    {
        float const reach = radius + kRepelLandYd;
        auto clear = [&](Vec2 p) { return DungeonKit::Distance(p, center) >= radius + 1.f; };
        float const dx = boss.x - center.x;
        float const dy = boss.y - center.y;
        float const len = std::sqrt(dx * dx + dy * dy);
        if (len > 0.1f)
        {
            Vec2 const out = ClampToCorridor({ center.x + dx / len * reach, center.y + dy / len * reach });
            if (clear(out))
                return out;
        }
        float const sCenter = ToCorridor(center).s;
        float const toFar = sCenter < (kCorridorMinS + kCorridorMaxS) * 0.5f ? 1.f : -1.f;
        for (float const sign : { toFar, -toFar })
        {
            Vec2 const along = ClampToCorridor({ center.x + kCorridorAxis.x * reach * sign,
                center.y + kCorridorAxis.y * reach * sign });
            if (clear(along))
                return along;
        }
        // Unreachable with the measured corridor (52 yd long, wards of 6 yd at most); kept for safety.
        return FromCorridor({ kCorridorMaxS, 0.f });
    }

    // The hold: his victim stands in the ward and he is at its edge (within this of it): he stops there.
    inline constexpr float kHoldEdgeYd = 1.5f;

    constexpr bool HoldAtEdge(float bossDistYd, float victimDistYd, float wardYd)
    {
        return victimDistYd < wardYd && bossDistYd <= wardYd + kHoldEdgeYd;
    }

    // His victim inside the ward and he farther out than the hold band: he walks to this spot (never a chase, which
    // would take him into the ward): on his own side of the ward, kHoldStandYd past the edge, on the corridor floor.
    inline constexpr float kHoldStandYd = 0.75f;
    inline Vec2 HoldSpot(Vec2 center, Vec2 boss, float radius)
    {
        float const dx = boss.x - center.x;
        float const dy = boss.y - center.y;
        float const len = std::sqrt(dx * dx + dy * dy);
        float const reach = radius + kHoldStandYd;
        if (len > 0.1f)
        {
            Vec2 const out = ClampToCorridor({ center.x + dx / len * reach, center.y + dy / len * reach });
            if (DungeonKit::Distance(out, center) >= radius)
                return out;
        }
        // Beside a wall (or on the center): the edge along the corridor, his side first (the statue end leaves no
        // room past a ward at the statue spot: then the far side).
        float const toBoss = ToCorridor(boss).s < ToCorridor(center).s ? -1.f : 1.f;
        Vec2 along{};
        for (float const sign : { toBoss, -toBoss })
        {
            along = ClampToCorridor({ center.x + kCorridorAxis.x * reach * sign,
                center.y + kCorridorAxis.y * reach * sign });
            if (DungeonKit::Distance(along, center) >= radius)
                return along;
        }
        return along;
    }

    // Rule 10: holding with his victim out of his melee reach, he answers with Searing Bolt on it.
    inline constexpr std::uint32_t kSearingBoltEveryMs = 2000;
    inline constexpr NH<float> kSearingBoltPct{ 10.f, 15.f };       // of the target's row (the tank's, usually)

    // ----------------------------------------------------------------------------------------------------------------
    // LG1 Fire Tide and LG7 Wrath of Ragnaros
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kTideFirstMs = 20000;
    inline constexpr NH<std::uint32_t> kTideEveryMs{ 30000, 25000 };
    inline constexpr std::uint32_t kTideWarnMs = 4000;              // the yell, the glow (cast bar) and the markers
    // Section 7 #21 (designer default): the Wrath keeps a 4 s warning on normal (the normal ladder), 2 s on heroic.
    inline constexpr NH<std::uint32_t> kWrathWarnMs{ 4000, 2000 };
    inline constexpr NH<float> kTideBasePct{ 30.f, 45.f };
    inline constexpr float kTideCapPct = 75.f;
    inline constexpr float kTideOuterYd = 45.f;                     // section 7 #21 default (the spec leaves it unset)
    // A tide never starts within this of the previous one's landing (a Wrath against a Fire Tide, either way).
    inline constexpr std::uint32_t kTideGapMs = 3000;

    // The tide's percent of the reference row at Fury `fury` (0-100).
    constexpr float TidePct(bool heroic, std::uint32_t fury)
    {
        float const scaled = kTideBasePct(heroic) * (1.f + float(std::min<std::uint32_t>(fury, 100)) / 100.f);
        return std::min(kTideCapPct, scaled);
    }

    // The start of a tide due at `dueMs` when the last one landed at `lastResolveMs` (0: none yet).
    constexpr std::uint64_t TideStartAfter(std::uint64_t dueMs, std::uint64_t lastResolveMs)
    {
        return lastResolveMs ? std::max<std::uint64_t>(dueMs, lastResolveMs + kTideGapMs) : dueMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG6 Fury of Ragnaros
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kFuryMax = 100;
    inline constexpr std::uint32_t kFuryAfterWrath = 30;
    inline constexpr std::int32_t kFuryBlastLanded = 10;
    inline constexpr std::int32_t kFuryBlastInterrupted = -15;
    inline constexpr std::int32_t kFuryTotemKilled = -10;
    inline constexpr std::int32_t kFuryWardBroken = -20;
    inline constexpr std::int32_t kFuryPerSecondWard = 3;
    inline constexpr std::int32_t kFuryPerSecondTotem = 2;
    inline constexpr std::uint32_t kFuryTickMs = 1000;

    constexpr std::uint32_t FuryAdd(std::uint32_t fury, std::int32_t delta)
    {
        std::int64_t const v = std::int64_t(fury) + delta;
        return std::uint32_t(std::clamp<std::int64_t>(v, 0, kFuryMax));
    }

    // One second of the meter: +3 while Fire Ward holds, +2 per living totem.
    constexpr std::uint32_t FuryAfterSecond(std::uint32_t fury, bool fireWardUp, std::uint32_t livingTotems)
    {
        return FuryAdd(fury, (fireWardUp ? kFuryPerSecondWard : 0)
            + kFuryPerSecondTotem * std::int32_t(livingTotems));
    }

    constexpr bool WrathDue(std::uint32_t fury)
    {
        return fury >= kFuryMax;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG4 Defiling Totem
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kTotemFirstMs = 10000;
    inline constexpr NH<std::uint32_t> kTotemEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kTotemCap = 3;
    inline constexpr float kTotemInsetYd = 0.75f;                   // planted at least this far inside the edge

    // A spot inside the ward of `radius` around `center`, from two uniform numbers in [0, 1]: uniform over the disc
    // shrunk by the inset (at least 0.5 yd of disc).
    inline Vec2 TotemSpot(Vec2 center, float radius, float u, float v)
    {
        float const r = std::max(0.5f, radius - kTotemInsetYd) * std::sqrt(std::clamp(u, 0.f, 1.f));
        float const a = DungeonKit::kTwoPi * std::clamp(v, 0.f, 1.f);
        return { center.x + r * std::cos(a), center.y + r * std::sin(a) };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG5 Molten Splash
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kSplashFirstMs = 6000;
    inline constexpr NH<std::uint32_t> kSplashEveryMs{ 10000, 8000 };
    inline constexpr NH<std::uint32_t> kSplashCount{ 2, 3 };
    inline constexpr std::uint32_t kSplashWarnMs = 2000;
    inline constexpr float kSplashRadiusYd = 4.f;
    inline constexpr NH<float> kSplashPct{ 20.f, 35.f };
    // Gap 20 (section 7 #21 default): the patch's damage a second. No Weakened (a lingering patch never applies it).
    inline constexpr NH<float> kPatchPct{ 4.f, 6.f };
    inline constexpr std::uint32_t kPatchTickMs = 1000;
    inline constexpr std::uint32_t kPatchLifeMs = 900000;           // "for the fight": a ceiling; a tide or the end
                                                                    // of the fight removes it first
    inline constexpr float kPatchRadiusYd = 4.f;

    // A patch survives a tide when its center lies inside that tide's ward (S2 147-156: "sheltered").
    inline bool Sheltered(Vec2 patch, Vec2 wardCenter, float wardYd)
    {
        return DungeonKit::Distance(patch, wardCenter) <= wardYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LG8 Molten Blast, LG9 Fire Ward, LG10 Flame Shock (gap 36 "stock rescaled": the BRS convention, designer Qs)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kMoltenBlastFirstMs = 6000;
    inline constexpr std::uint32_t kMoltenBlastEveryMs = 12000;     // both difficulties (ruling 91)
    inline constexpr std::uint32_t kMoltenBlastCastMs = 2000;
    inline constexpr float kMoltenBlastRangeYd = 30.f;
    inline constexpr NH<float> kMoltenBlastPct{ 15.f, 25.f };       // of the target's row (RefFlatOn)

    inline constexpr std::uint32_t kFireWardFirstMs = 5000;
    inline constexpr std::uint32_t kFireWardEveryMs = 30000;
    inline constexpr std::uint32_t kFireWardMs = 30000;             // the aura's length (the next cast replaces it)
    inline constexpr float kFireWardHealthPct = 8.f;                // of his maximum health, any school
    // A Fire Ward gone with more than this left was broken or purged (-20 Fury); less is a natural expiry.
    inline constexpr std::uint32_t kFireWardExpirySlackMs = 750;

    constexpr std::int32_t FireWardAbsorb(std::uint32_t maxHealth)
    {
        return std::int32_t(double(maxHealth) * double(kFireWardHealthPct) / 100.0 + 0.5);
    }

    inline constexpr std::uint32_t kFlameShockFirstMs = 9000;
    inline constexpr std::uint32_t kFlameShockMinMs = 8000;         // stock repeat 8-21 s
    inline constexpr std::uint32_t kFlameShockMaxMs = 21000;
    inline constexpr float kFlameShockRangeYd = 20.f;
    inline constexpr NH<float> kFlameShockPct{ 6.f, 10.f };         // the hit
    inline constexpr NH<float> kFlameShockTickPct{ 3.f, 5.f };      // each 3 s tick, 12 s (4 ticks)
    inline constexpr std::uint32_t kFlameShockTickMs = 3000;
    inline constexpr std::uint32_t kFlameShockMs = 12000;

    // A cast of `castMs` started at `nowMs` would still run (+ 500 ms of margin) when the next tide is due at
    // `tideMs`: the tide's cast bar must not wait on it, so the cast waits instead (it starts after the tide's).
    constexpr bool CastBlocksTide(std::uint64_t nowMs, std::uint32_t castMs, std::uint64_t tideMs)
    {
        return nowMs + castMs + 500 > tideMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Cadence
    // ----------------------------------------------------------------------------------------------------------------

    // The next start of a beat planned at `plannedMs` with cadence `everyMs`, after `nowMs` (a missed beat is skipped,
    // the cadence keeps its phase).
    constexpr std::uint64_t NextPlanned(std::uint64_t plannedMs, std::uint32_t everyMs, std::uint64_t nowMs)
    {
        std::uint64_t next = plannedMs + everyMs;
        while (everyMs && next <= nowMs)
            next += everyMs;
        return next;
    }
}

#endif
