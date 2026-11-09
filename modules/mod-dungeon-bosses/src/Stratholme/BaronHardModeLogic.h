/*
 * mod-dungeon-bosses, Stratholme S15: Baron Rivendare's hard mode, the Ultimatum (heroic only), the pure,
 * host-testable part (no engine headers): the spell ids, the tuning, the execution line, Ysida's misses, the
 * Deathcharger lane and its trail, the rot heal's once-a-second book and Ysida, Risen's numbers. Build spec: ST
 * 3709-3747 (Hard mode HM1-HM4), ST 3807-3828 (Implementation), ST 3868-3871 (the HM rows); handoff section 3.7,
 * section 3.5 row S15, section 3.6 (500k), section 11 #1 (the boss's Condemned is its own id, never the W1 item's
 * 205669). Tested by tests/strat_ultimatum_test.cpp. The engine side is baron_hard_mode.cpp, on S14's AI through
 * BaronFight.h.
 *
 * The hard mode is heroic only, so its percents are of the heroic reference row (4,120 non-tank / 4,110 tank at level
 * 60, the MapLevels pin 329h:60); there is no normal value.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARON_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARON_HARD_MODE_LOGIC_H

#include "BaronLogic.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <unordered_set>
#include <vector>

namespace StratUltimatum
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsUltimatum;

    // Declared in apps/dbc-tools source/npcs/stratholme/baron_hard_mode.py (same ids).
    enum BaronHardModeSpells : std::uint32_t
    {
        SPELL_HM_EXECUTION          = 206720,   // HM1 the 3 s channel at Ysida: the bar and the beam (Shadow Sear's SV)
        SPELL_HM_EXECUTION_HIT      = 206721,   // HM1 the blow on the taker: 30% x (1 + Condemned), set at launch
        SPELL_HM_EXECUTION_YSIDA    = 206722,   // HM1 no taker: the blow's look on Ysida (she loses a third)
        SPELL_HM_CONDEMNED          = 206723,   // HM2 the stack, the whole fight (+100% execution damage each)
        SPELL_HM_CONDEMNED_DOT      = 206724,   // HM2 1% Shadow a second for 10 s per execution taken
        SPELL_HM_PRICE_OF_DEFIANCE  = 206725,   // HM1 on him once Ysida falls: +200% damage done, the rest of the fight
        SPELL_HM_DEATHCHARGER_MARK  = 206726,   // HM3 the 3 s mark on the lane's target
        SPELL_HM_TRAMPLE            = 206727,   // HM3 the target's 20% (not avoidable), Charge's look, lands as he does
        SPELL_HM_LANE               = 206728,   // HM3 the lane's 50% on everyone else inside: resolve copy (Physical)
        SPELL_HM_TRAIL              = 206729,   // HM3 the trail's 1 s tick: resolve copy (Shadow)
        SPELL_HM_TRAIL_LOOK         = 206730,   // HM3 the trail's look on a rot stalker (3 yd, Death and Decay's SV)
        SPELL_HM_ROT_HEAL           = 206731,   // HM4 the rot's heal, a second: exact amount (base point 0)
        SPELL_HM_DEATH_COIL         = 206732,   // Ysida, Risen's Death Coil (a missile)
        SPELL_HM_RISEN_STRIKE       = 206733,   // Ysida, Risen's 2 s strike on her victim (percent spell)
        SPELL_HM_RISEN_LOOK         = 206734,   // Ysida, Risen's lasting look (Hysteria's SV)
    };
    static_assert(kSpellSlice.Contains(SPELL_HM_EXECUTION), "S15 spells sit in its slice");
    static_assert(kSpellSlice.Contains(SPELL_HM_RISEN_LOOK), "S15 spells sit in its slice");
    static_assert(SPELL_HM_CONDEMNED != 205669, "the boss's Condemned is never the W1 item's (handoff 11 #1)");

    // Registry tags (S14's tags stop below StratBaron::kHardModeTagBase).
    enum UltimatumTags : std::uint32_t
    {
        TAG_EXECUTION   = StratBaron::kHardModeTagBase,         // HM1 the line soak (telegraph only)
        TAG_LANE        = StratBaron::kHardModeTagBase + 1,     // HM3 the following lane (50% at the lock)
        TAG_TRAIL       = StratBaron::kHardModeTagBase + 2,     // HM3 the trail's persistent line (5% a second)
        TAG_TRAIL_ROT   = StratBaron::kHardModeTagBase + 3,     // HM3 the trail's rot stalkers (OnRotTick)
    };

    // S14's cast queue ids (StratBaron::kHardModeCastBase and up). Same priority: when both fall due together the
    // second waits for the first (ST "Casts never overlap"); the Shadow Bolt (priority 0) waits for both.
    enum UltimatumCasts : std::uint32_t
    {
        CAST_EXECUTION      = StratBaron::kHardModeCastBase,
        CAST_DEATHCHARGER   = StratBaron::kHardModeCastBase + 1,
    };
    std::uint8_t constexpr kCastPriority = 1;
    std::uint32_t constexpr kCastRetryMs = 2000;        // nobody to target, or Ysida not there: try again this soon

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Hard mode" and "Build spec", approved 2026-11-05, rulings 54-60)
    // ----------------------------------------------------------------------------------------------------------------

    // Health on a hard mode pull (ST: 500k, about 193 on base 2,590); the heroic template's 300k comes back on a wipe.
    std::uint32_t constexpr kHardModeHealth = 500000;
    // Mounted from the pull: Deathcharger 11195's display.
    std::uint32_t constexpr kDeathchargerDisplay = 10718;

    // HM1 Executions: a 3 s cast, first at 15 s, then every 25 s. At its end the first player on the 2 yd line from him
    // to Ysida takes 30% Shadow x (1 + their Condemned stacks); nobody on it: she loses a third of her life, and the
    // third miss kills her (Ysida, Risen and the Price of Defiance).
    std::uint32_t constexpr kExecutionFirstMs = 15000;
    std::uint32_t constexpr kExecutionEveryMs = 25000;
    std::uint32_t constexpr kExecutionCastMs = 3000;
    float constexpr kExecutionLineWidth = 2.f;
    float constexpr kExecutionPct = 30.f;
    std::uint32_t constexpr kYsidaMissesToFall = 3;

    // HM2 Condemned: each execution taken adds a stack (the whole fight, no cap) and a 10 s Shadow DoT of 1% a second.
    float constexpr kCondemnedPerStack = 1.f;           // +100% execution damage per stack
    float constexpr kCondemnedDotPct = 1.f;
    std::uint32_t constexpr kCondemnedDotMs = 10000;
    std::uint32_t constexpr kCondemnedMaxStacks = 255;  // the aura counter's limit (CumulativeAura 255): no real cap

    // The Price of Defiance: +200% damage done once Ysida falls (ruling 59).
    float constexpr kPriceOfDefiancePct = 200.f;

    // HM3 Deathcharger: first at 22 s, then every 30 s. The farthest non-tank is marked; a 6 yd lane from him to them
    // follows them for 3 s, then locks and he charges down it (a charge, not a teleport). The target takes 20%
    // (not avoidable), anyone else in the lane 50% Physical. The lane rots for 20 s: rot stalkers 5 yd apart, each
    // raising the piles within 3 yd and healing as Death and Decay does; the trail's line deals the rot's 5% a second.
    std::uint32_t constexpr kChargeFirstMs = 22000;
    std::uint32_t constexpr kChargeEveryMs = 30000;
    std::uint32_t constexpr kLaneWarnMs = 3000;
    float constexpr kLaneWidth = 6.f;
    float constexpr kLaneHitPct = 50.f;
    float constexpr kTargetHitPct = 20.f;
    float constexpr kLaneSlackYd = 2.f;                 // the drawn lane reaches this far past the target (its body)
    float constexpr kLaneMinYd = 5.f;
    float constexpr kLaneMaxYd = 50.f;                  // longer than the room's long axis (48 yd)
    float constexpr kChargeSpeed = 42.f;                // SPEED_CHARGE
    float constexpr kChargeStopShortYd = 1.f;           // he stops this short of the target (his reach does the rest)
    float constexpr kLaneProbeStepYd = 1.f;             // the clamp walks the charge path at this step
    std::uint32_t constexpr kChargeHoldExtraMs = 500;   // after the travel: he lands before he swings
    float constexpr kTrailSpacingYd = 5.f;
    float constexpr kTrailRadius = 3.f;
    std::uint32_t constexpr kTrailLifeMs = 20000;
    float constexpr kTrailPct = 5.f;                    // the heroic rot's tick (S14 kRotPct.heroic)
    std::uint32_t constexpr kTrailGraceMs = 1000;
    static_assert(kTrailPct == StratBaron::kRotPct.heroic, "the trail rots as heroic Death and Decay");
    static_assert(kTrailRadius * 2.f >= kTrailSpacingYd, "the trail's raise circles touch along the lane");

    // HM4 Death and Decay rots longer: 45 s, and every second it heals him 1% of his maximum health and every undead
    // of his (the skeletons, Ysida, Risen) 5% of theirs while they stand inside. The Deathcharger trail heals the same.
    std::uint32_t constexpr kRotLifeMs = 45000;
    float constexpr kRotHealBossPct = 1.f;
    float constexpr kRotHealServantPct = 5.f;
    static_assert(kRotLifeMs <= StratBaron::kRotLookMs, "S14's rot look covers the hard mode's 45 s");

    // Ysida, Risen (300589): 40,000 health (HealthModifier 13.106 on the level 60 warrior base 3,052, the DT file);
    // melee and a Death Coil (gap 22: the numbers are starting points), stun immune, attacks the nearest player.
    std::uint32_t constexpr kRisenHealth = 40000;
    std::uint32_t constexpr kRisenSwingMs = 2000;
    std::uint32_t constexpr kRisenFirstSwingMs = 1000;
    float constexpr kRisenStrikePct = 3.f;              // a swing: 1.5% of the row a second
    std::uint32_t constexpr kDeathCoilFirstMs = 4000;
    std::uint32_t constexpr kDeathCoilEveryMs = 10000;
    float constexpr kDeathCoilPct = 15.f;
    float constexpr kDeathCoilRangeYd = 30.f;
    std::uint32_t constexpr kRisenRetargetMs = 1000;
    std::int8_t constexpr kRisenTargetPriority = 3;     // above the skeletons (2): ST "kill order: Ysida, Risen first"

    // ----------------------------------------------------------------------------------------------------------------
    // HM1 / HM2 the execution
    // ----------------------------------------------------------------------------------------------------------------

    // The blow's percent of the reference row on a taker with `stacks` Condemned stacks: 30, 60, 90, 120...
    constexpr float ExecutionPct(std::uint32_t stacks)
    {
        return kExecutionPct * (1.f + kCondemnedPerStack * float(stacks));
    }

    // The first point (by distance from `from`) on the line from `from` to `to` of `width`: its projection lies on the
    // segment and it stands within width / 2 of it. nullopt: nobody on the line.
    inline std::optional<std::size_t> FirstOnLine(Vec2 from, Vec2 to, float width, std::vector<Vec2> const& points)
    {
        float const len = DungeonKit::Distance(from, to);
        if (len < 0.01f)
            return std::nullopt;
        float const dx = (to.x - from.x) / len;
        float const dy = (to.y - from.y) / len;
        std::optional<std::size_t> best;
        float bestAlong = 0.f;
        for (std::size_t i = 0; i < points.size(); ++i)
        {
            float const px = points[i].x - from.x;
            float const py = points[i].y - from.y;
            float const along = px * dx + py * dy;
            if (along < 0.f || along > len)
                continue;
            float const across = std::fabs(px * dy - py * dx);
            if (across > width * 0.5f)
                continue;
            if (!best || along < bestAlong)
            {
                best = i;
                bestAlong = along;
            }
        }
        return best;
    }

    // Ysida after `misses` missed executions: the share of her life left (a third per miss) and whether she fell.
    constexpr float YsidaLifeShare(std::uint32_t misses)
    {
        return misses >= kYsidaMissesToFall ? 0.f : float(kYsidaMissesToFall - misses) / float(kYsidaMissesToFall);
    }

    constexpr bool YsidaFalls(std::uint32_t misses)
    {
        return misses >= kYsidaMissesToFall;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM3 the Deathcharger lane
    // ----------------------------------------------------------------------------------------------------------------

    // The drawn lane's length for a target `dist` yards away (it reaches just past them).
    constexpr float LaneLength(float dist)
    {
        return std::clamp(dist + kLaneSlackYd, kLaneMinYd, kLaneMaxYd);
    }

    // Where the charge would end: toward the target, stopping short of them, never past the drawn lane.
    inline Vec2 ChargeEnd(Vec2 start, Vec2 target, float laneLength)
    {
        float const dist = DungeonKit::Distance(start, target);
        if (dist < 0.01f)
            return start;
        float const run = std::max(0.f, std::min(dist - kChargeStopShortYd, laneLength));
        return { start.x + (target.x - start.x) / dist * run, start.y + (target.y - start.y) / dist * run };
    }

    // The charge clamped to where he may stand (S14's BaronFight::CanStandAt: his arena, off the stock leash): walking
    // from `start` toward `end` every `step` yards, the last point before the first one he may not stand at; `start`
    // itself when the first step already fails.
    inline Vec2 ClampCharge(Vec2 start, Vec2 end, std::function<bool(Vec2)> const& canStand,
        float step = kLaneProbeStepYd)
    {
        float const len = DungeonKit::Distance(start, end);
        if (len < 0.01f || step <= 0.f)
            return start;
        Vec2 last = start;
        float d = 0.f;
        while (d < len)
        {
            d = std::min(d + step, len);
            Vec2 const p{ start.x + (end.x - start.x) / len * d, start.y + (end.y - start.y) / len * d };
            if (!canStand(p))
                return last;
            last = p;
        }
        return last;
    }

    // The trail's rot stalker spots: from `start` every `spacing` yards to `end`, the end itself added unless the last
    // spot is within half a spacing of it. Empty for a charge shorter than a yard.
    inline std::vector<Vec2> TrailSpots(Vec2 start, Vec2 end, float spacing = kTrailSpacingYd)
    {
        std::vector<Vec2> out;
        float const len = DungeonKit::Distance(start, end);
        if (len < 1.f || spacing <= 0.f)
            return out;
        for (float d = 0.f; d <= len + 0.001f; d += spacing)
            out.push_back({ start.x + (end.x - start.x) / len * d, start.y + (end.y - start.y) / len * d });
        if (DungeonKit::Distance(out.back(), end) > spacing * 0.5f)
            out.push_back(end);
        return out;
    }

    // The charge's travel time (ms) for `dist` yards.
    constexpr std::uint32_t ChargeTravelMs(float dist)
    {
        return dist <= 0.f ? 0u : std::uint32_t(dist / kChargeSpeed * 1000.f + 0.5f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM4 the rot heal
    // ----------------------------------------------------------------------------------------------------------------

    // S14 calls OnRotTick once a second for every live rot: a unit standing in two rots heals once that second. Keys
    // are raw guids; a new clock second clears the book.
    struct RotHealBook
    {
        std::uint64_t second = ~std::uint64_t(0);
        std::unordered_set<std::uint64_t> healed;

        // True the first time `guid` asks during the second of `clockMs` (S14's tick clock, BaronFight::ClockMs).
        bool Take(std::uint64_t clockMs, std::uint64_t guid)
        {
            std::uint64_t const s = clockMs / 1000;
            if (s != second)
            {
                second = s;
                healed.clear();
            }
            return healed.insert(guid).second;
        }

        void Reset()
        {
            second = ~std::uint64_t(0);
            healed.clear();
        }
    };

    // The heal (whole points) for a unit of `maxHealth` at `pct` percent; at least 1 for a living unit.
    constexpr std::uint32_t RotHealAmount(std::uint32_t maxHealth, float pct)
    {
        return maxHealth == 0 ? 0u : std::max<std::uint32_t>(1u, std::uint32_t(float(maxHealth) * pct / 100.f));
    }
}

#endif
