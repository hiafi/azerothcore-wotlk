/*
 * mod-dungeon-bosses, Scholomance S9: Lord Alexei Barov (10504), "the Code of Conduct", the pure, host-testable part
 * (no engine headers). Build spec SC 2460-2533 (design SC 2275-2459), AB1-AB12; handoff section 3.4 rows AB, 3.5 row
 * S9, 3.6 (normal 160k, heroic 250k, examiner 80k), 3.7 (the Barov Family Vault's solo lesson), 3.8 (the vault's
 * thirds, lane and desks, every number [navmesh estimate]). Tested by tests/scholo_alexei_test.cpp.
 *
 *   Rules              AB1 the rule pool (normal singles; heroic: a single first, then the approved pairs, AB8), never
 *                      the same rule set twice in a row; Assembly only with three or more players
 *   Rod ladder         AB9 the Dean's Rod per Demerit already held (ruling 19): N 20-60%, H 30-90%
 *   Thirds             AB5 the forbidden third: the one most of the group stands in
 *   Lane               AB6 the 4 yd lane along the north side of the vault, cut short to stay out of a forbidden third
 *   Desks              AB7 the desk grid, 8 yd apart, and the assignment (nearest free desk)
 *   Fortune            AB10 where a fortune may lie: 8-12 yd from the nearest player, where taking it breaks the rule
 *   Lesson             the Barov Family Vault's detention lesson (SC 2960-2971): Out of bounds, then No running
 *   Examiner           S13's Graduate Examiner (300553): heroic rules and fortunes at 80k health
 *
 * Axes (ScholomanceRework.h): +x north, +y west. The vault is 29 x 58 yd, x 168-197, y -35 to -93: the gate third
 * (y -34 to -53.5, z 75), the middle third (the ramps and the pit's north end) and Alexei's third (y -73.5 to -94,
 * z 72, a U around the pit).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_ALEXEI_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_ALEXEI_LOGIC_H

#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace ScholoAlexei
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsAlexei;

    // Declared in apps/dbc-tools source/npcs/scholomance/lord_alexei_barov.py (same ids).
    enum AlexeiSpells : std::uint32_t
    {
        SPELL_AX_RULE_NO_RUNNING    = kSpellSlice.first + 0,    // 206290 AB2 the rule's icon on everyone (DUMMY)
        SPELL_AX_RULE_ASSEMBLY      = kSpellSlice.first + 1,    // 206291 AB3
        SPELL_AX_RULE_KEEP_DISTANCE = kSpellSlice.first + 2,    // 206292 AB4
        SPELL_AX_RULE_OUT_OF_BOUNDS = kSpellSlice.first + 3,    // 206293 AB5
        SPELL_AX_RULE_LINE_UP       = kSpellSlice.first + 4,    // 206294 AB6 (heroic)
        SPELL_AX_RULE_DESKS         = kSpellSlice.first + 5,    // 206295 AB7 (heroic)
        SPELL_AX_ANNOUNCE           = kSpellSlice.first + 6,    // 206296 AB1 the announcement's look on him
        SPELL_AX_OUT_OF_BOUNDS      = kSpellSlice.first + 7,    // 206297 AB5 the zone's tick (resolve copy, 0 damage)
        SPELL_AX_KEEP_DISTANCE      = kSpellSlice.first + 8,    // 206298 AB4 the Spread's hit (resolve copy, 0)
        SPELL_AX_DEMERIT            = kSpellSlice.first + 9,    // 206299 AB9 the stacking debuff, 5 stacks
        SPELL_AX_DEANS_ROD          = kSpellSlice.first + 10,   // 206300 AB9 the punishment (damage by base point)
        SPELL_AX_ILL_GOTTEN_GAINS   = kSpellSlice.first + 11,   // 206301 AB10 +40% damage and healing, 15 s
        SPELL_AX_VEIL_OF_SHADOW     = kSpellSlice.first + 12,   // 206302 AB11 the tank-only copy of 17820
        // 206303-206314 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_AX_RULE_NO_RUNNING), "Alexei spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_AX_VEIL_OF_SHADOW), "Alexei spells sit in his slice");

    // The fortune's look: the stock "Gold Coins" chest 186634 (GODI 2614 GoldPilesmall01, 1.85 yd), summoned as a
    // temporary object with GO_FLAG_NOT_SELECTABLE so nobody (and no bot: LootObjectStack skips it) can open it. No new
    // gameobject entry.
    std::uint32_t constexpr GO_GOLD_COINS = 186634;

    // Registry tags (the build spec's AB numbers; mod-boss-mechanics' `alexei` drill uses the same).
    enum AlexeiTags : std::uint32_t
    {
        TAG_NO_RUNNING      = 2,
        TAG_ASSEMBLY        = 3,
        TAG_KEEP_DISTANCE   = 4,
        TAG_OUT_OF_BOUNDS   = 5,
        TAG_LINE_UP         = 6,
        TAG_DESKS           = 7,
        TAG_FORTUNE         = 10,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // AB1-AB8 the rules
    // ----------------------------------------------------------------------------------------------------------------

    // One bit per rule; a rule set is one rule or a heroic pair.
    enum RuleBit : std::uint8_t
    {
        RULE_NONE           = 0x00,
        RULE_NO_RUNNING     = 0x01,     // AB2 hold still in the window (moving more than 1 yd breaks it)
        RULE_ASSEMBLY       = 0x02,     // AB3 within 6 yd of two other players at the close
        RULE_KEEP_DISTANCE  = 0x04,     // AB4 nobody within 8 yd of another player at the close
        RULE_OUT_OF_BOUNDS  = 0x08,     // AB5 a third of the vault forbidden for the window
        RULE_LINE_UP        = 0x10,     // AB6 heroic: inside the 4 yd lane at the close
        RULE_DESKS          = 0x20,     // AB7 heroic: on your own 3 yd desk at the close
    };
    using RuleSet = std::uint8_t;
    std::size_t constexpr kRuleCount = 6;

    inline std::array<RuleBit, kRuleCount> constexpr kRules{ { RULE_NO_RUNNING, RULE_ASSEMBLY, RULE_KEEP_DISTANCE,
        RULE_OUT_OF_BOUNDS, RULE_LINE_UP, RULE_DESKS } };
    // `.dbtest scholo alexei rule <key> [<key>]`.
    inline std::array<char const*, kRuleCount> constexpr kRuleKeys{ { "norunning", "assembly", "distance", "bounds",
        "lineup", "desks" } };

    constexpr bool Has(RuleSet set, RuleBit rule) { return (set & rule) != 0; }

    constexpr std::uint32_t RuleCountOf(RuleSet set)
    {
        std::uint32_t n = 0;
        for (RuleBit r : kRules)
            if (Has(set, r))
                ++n;
        return n;
    }

    // The rule's icon aura, its yell (creature_text group of 10504) and its registry tag.
    constexpr std::uint32_t RuleAura(RuleBit rule)
    {
        switch (rule)
        {
            case RULE_NO_RUNNING:    return SPELL_AX_RULE_NO_RUNNING;
            case RULE_ASSEMBLY:      return SPELL_AX_RULE_ASSEMBLY;
            case RULE_KEEP_DISTANCE: return SPELL_AX_RULE_KEEP_DISTANCE;
            case RULE_OUT_OF_BOUNDS: return SPELL_AX_RULE_OUT_OF_BOUNDS;
            case RULE_LINE_UP:       return SPELL_AX_RULE_LINE_UP;
            case RULE_DESKS:         return SPELL_AX_RULE_DESKS;
            default:                 return 0;
        }
    }

    constexpr std::uint8_t RuleYell(RuleBit rule)
    {
        switch (rule)
        {
            case RULE_NO_RUNNING:    return ScholomanceRework::YELL_ALEXEI_NO_RUNNING;
            case RULE_ASSEMBLY:      return ScholomanceRework::YELL_ALEXEI_ASSEMBLY;
            case RULE_KEEP_DISTANCE: return ScholomanceRework::YELL_ALEXEI_KEEP_DISTANCE;
            case RULE_OUT_OF_BOUNDS: return ScholomanceRework::YELL_ALEXEI_CORNER;
            case RULE_LINE_UP:       return ScholomanceRework::YELL_ALEXEI_LINE_UP;
            case RULE_DESKS:         return ScholomanceRework::YELL_ALEXEI_DESKS;
            default:                 return ScholomanceRework::YELL_ALEXEI_AGGRO;
        }
    }

    constexpr std::uint32_t RuleTag(RuleBit rule)
    {
        switch (rule)
        {
            case RULE_NO_RUNNING:    return TAG_NO_RUNNING;
            case RULE_ASSEMBLY:      return TAG_ASSEMBLY;
            case RULE_KEEP_DISTANCE: return TAG_KEEP_DISTANCE;
            case RULE_OUT_OF_BOUNDS: return TAG_OUT_OF_BOUNDS;
            case RULE_LINE_UP:       return TAG_LINE_UP;
            case RULE_DESKS:         return TAG_DESKS;
            default:                 return 0;
        }
    }

    // The words the vault reads out in the solo lesson (no creature_text: the lesson's stalker belongs to S11); the
    // same words as his yells (SC "Text").
    constexpr char const* RuleWords(RuleBit rule)
    {
        switch (rule)
        {
            case RULE_NO_RUNNING:    return "No running in the halls!";
            case RULE_ASSEMBLY:      return "Assembly!";
            case RULE_KEEP_DISTANCE: return "Keep your distance!";
            case RULE_OUT_OF_BOUNDS: return "Go to the corner!";
            case RULE_LINE_UP:       return "Line up!";
            case RULE_DESKS:         return "To your desks!";
            default:                 return "";
        }
    }

    // AB1 timing: first at 10 s, every 25 s (announcement to announcement); 3 s (heroic 4 s) to get ready, then a
    // 6 s window. Out of bounds and No running are judged through the window; the rest when the window closes.
    std::uint32_t constexpr kRuleFirstMs = 10000;
    std::uint32_t constexpr kRuleEveryMs = 25000;
    inline constexpr NH<std::uint32_t> kRuleWarnMs{ 3000, 4000 };
    std::uint32_t constexpr kRuleWindowMs = 6000;
    std::uint32_t constexpr kOutOfBoundsTickMs = 1000;  // the forbidden third is judged every second of the window

    // AB2-AB7 sizes.
    float constexpr kNoRunningToleranceYd = 1.f;        // AB2 moving more than 1 yd breaks it; turning is fine
    float constexpr kAssemblyRadius = 6.f;              // AB3 within 6 yd ...
    std::uint8_t constexpr kAssemblyMinOthers = 2;      // ... of at least two other players
    std::uint32_t constexpr kAssemblyMinPlayers = 3;    // so it is in the pool only with three or more players
    float constexpr kKeepDistanceRadius = 8.f;          // AB4
    float constexpr kLaneWidth = 4.f;                   // AB6
    float constexpr kDeskRadius = 3.f;                  // AB7
    float constexpr kDeskMinApart = 8.f;                // AB7 desks at least 8 yd apart

    // AB8 the approved heroic pairs (build spec AB8; side questions, rounds 2 and 3): Out of bounds with any other
    // rule; No running only with Out of bounds (leave in the warning, then freeze); Assembly with Out of bounds or Line
    // up; Line up with Keep your distance. Never Assembly with Keep your distance or desks.
    inline std::array<RuleSet, 7> constexpr kHeroicPairs{ {
        RuleSet(RULE_OUT_OF_BOUNDS | RULE_NO_RUNNING),
        RuleSet(RULE_OUT_OF_BOUNDS | RULE_ASSEMBLY),
        RuleSet(RULE_OUT_OF_BOUNDS | RULE_KEEP_DISTANCE),
        RuleSet(RULE_OUT_OF_BOUNDS | RULE_LINE_UP),
        RuleSet(RULE_OUT_OF_BOUNDS | RULE_DESKS),
        RuleSet(RULE_ASSEMBLY | RULE_LINE_UP),
        RuleSet(RULE_LINE_UP | RULE_KEEP_DISTANCE),
    } };

    inline std::array<RuleBit, 4> constexpr kNormalRules{ { RULE_NO_RUNNING, RULE_ASSEMBLY, RULE_KEEP_DISTANCE,
        RULE_OUT_OF_BOUNDS } };

    // True when the set is one rule of the difficulty's pool or one of the approved pairs (heroic).
    constexpr bool IsAllowedSet(RuleSet set, bool heroic)
    {
        if (RuleCountOf(set) == 1)
        {
            if (heroic)
                return true;
            for (RuleBit r : kNormalRules)
                if (set == r)
                    return true;
            return false;
        }
        if (!heroic)
            return false;
        for (RuleSet p : kHeroicPairs)
            if (p == set)
                return true;
        return false;
    }

    // The sets the next announcement draws from: normal, one of the four rules; heroic, any of the six for the first
    // announcement of the fight, then the approved pairs only (AB1, AB8). Never the previous set again (AB1), and no
    // Assembly with fewer than three players (nobody could pass it).
    inline std::vector<RuleSet> RulePool(bool heroic, std::uint32_t announcedSoFar, std::uint32_t players,
        RuleSet previous)
    {
        std::vector<RuleSet> pool;
        auto add = [&](RuleSet set)
        {
            if (set == previous)
                return;
            if (Has(set, RULE_ASSEMBLY) && players < kAssemblyMinPlayers)
                return;
            pool.push_back(set);
        };
        if (!heroic)
            for (RuleBit r : kNormalRules)
                add(r);
        else if (announcedSoFar == 0)
            for (RuleBit r : kRules)
                add(r);
        else
            for (RuleSet p : kHeroicPairs)
                add(p);
        return pool;
    }

    // A uniform pick from the pool; `rand01` in [0, 1). RULE_NONE for an empty pool.
    inline RuleSet PickRuleSet(std::vector<RuleSet> const& pool, float rand01)
    {
        if (pool.empty())
            return RULE_NONE;
        std::size_t const i = std::min(pool.size() - 1, static_cast<std::size_t>(rand01 * float(pool.size())));
        return pool[i];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AB9 Demerits and the Dean's Rod; AB10 the fortune; AB11 Veil of Shadow; the boss
    // ----------------------------------------------------------------------------------------------------------------

    // Demerits last the fight and stack to 5 (round 3). The Rod lands at once for its base plus 50% of the base per
    // Demerit already held, capped at the 5th value: N 20, 30, 40, 50, 60%; H 30, 45, 60, 75, 90% (ruling 19). Every
    // Rod hit adds a Weakened stack (ruling 21). One Demerit per player per announcement (a broken rule, either rule of
    // a pair, or a fortune taken; S9's reading, STAGE-S9 report).
    std::uint32_t constexpr kDemeritCap = 5;
    inline constexpr NH<float> kRodBasePct{ 20.f, 30.f };
    float constexpr kRodStepOfBase = 0.5f;

    constexpr float RodPct(bool heroic, std::uint32_t demeritsHeld)
    {
        std::uint32_t const steps = std::min<std::uint32_t>(demeritsHeld, kDemeritCap - 1);
        return kRodBasePct(heroic) * (1.f + kRodStepOfBase * float(steps));
    }

    // AB10 the Barov fortune: 1 (heroic 2) per announcement, from the window's opening to its close, 8-12 yd from the
    // nearest player, where taking it breaks the rule. Walked over (2 yd), one player each; Ill-Gotten Gains (+40%
    // damage and healing done, 15 s) and the Demerit. A player takes at most one per announcement.
    inline constexpr NH<std::uint32_t> kFortunesPerRule{ 1, 2 };
    float constexpr kFortuneMinYd = 8.f;
    float constexpr kFortuneMaxYd = 12.f;
    float constexpr kFortunePickupYd = 2.f;
    float constexpr kFortuneZBand = 4.f;
    float constexpr kFortunesApartYd = 6.f;
    std::uint32_t constexpr kFortunePollMs = 250;
    std::uint32_t constexpr kIllGottenGainsPct = 40;
    std::uint32_t constexpr kIllGottenGainsMs = 15000;

    // AB11 Veil of Shadow: the tank only, a 1.5 s cast, healing taken -50% for 10 s, Curse; stock timers 5-12 s, then
    // 15-25 s; never during a rule (from the announcement to the close, with the cast clear of both ends).
    std::uint32_t constexpr kVeilCastMs = 1500;
    std::uint32_t constexpr kVeilFirstMinMs = 5000;
    std::uint32_t constexpr kVeilFirstMaxMs = 12000;
    std::uint32_t constexpr kVeilEveryMinMs = 15000;
    std::uint32_t constexpr kVeilEveryMaxMs = 25000;
    std::uint32_t constexpr kVeilClearMs = 500;         // slack past the cast before an announcement
    std::uint32_t constexpr kVeilAfterCloseMs = 1000;   // a blocked Veil waits this long past the close

    // A Veil may start at `nowMs` when no rule runs and its cast ends kVeilClearMs before the next announcement.
    constexpr bool VeilMayStart(std::uint64_t nowMs, bool ruleRunning, std::uint64_t nextAnnounceMs)
    {
        return !ruleRunning && nowMs + kVeilCastMs + kVeilClearMs <= nextAnnounceMs;
    }

    // His own melee (the live 6 was a mod-progression leftover; set explicitly, WP-T tunes it). Heroic is WP-H's.
    float constexpr kDamageModifier = 6.f;

    // Health (handoff section 3.6): normal 160k (the dbc-tools HealthModifier), heroic 250k (WP-H).
    std::uint32_t constexpr kNormalHealth = 160000;
    std::uint32_t constexpr kHeroicHealth = 250000;

    // ----------------------------------------------------------------------------------------------------------------
    // The vault [navmesh estimate] (ScholomanceRework.h kBarovVault, kBarovThirdsY, kBarovLane*, kBarovDesks)
    // ----------------------------------------------------------------------------------------------------------------

    float constexpr kVaultMinX = 168.0f;
    float constexpr kVaultMaxX = 197.0f;
    float constexpr kVaultMinY = -93.0f;
    float constexpr kVaultMaxY = -35.0f;
    float constexpr kVaultFloorZ = 72.0f;               // the east tier; the gate tier is z 75, the pit about 66
    float constexpr kVaultZTolerance = 8.f;             // a zone on a third holds both tiers and the pit (64-80)
    float constexpr kFortuneFloorMinZ = 70.5f;          // a fortune never lies in the pit
    float constexpr kFortuneFloorMaxZ = 76.5f;

    // A third: [yMin, yMax] of ScholomanceRework::kBarovThirdsY (0 the gate third, 1 the middle, 2 Alexei's).
    std::size_t constexpr kThirdCount = 3;

    constexpr float ThirdMinY(std::size_t third) { return ScholomanceRework::kBarovThirdsY[third][0]; }
    constexpr float ThirdMaxY(std::size_t third) { return ScholomanceRework::kBarovThirdsY[third][1]; }

    constexpr bool InThird(std::size_t third, Vec2 p, float margin = 0.f)
    {
        return p.y >= ThirdMinY(third) - margin && p.y <= ThirdMaxY(third) + margin;
    }

    // The third that holds `p` (by y), or kThirdCount when none does.
    constexpr std::size_t ThirdOf(Vec2 p)
    {
        for (std::size_t i = 0; i < kThirdCount; ++i)
            if (InThird(i, p))
                return i;
        return kThirdCount;
    }

    // AB5 the forbidden third, "the part the group stands in or next to": the third that holds the most players, ties
    // broken by `rand01`; nobody in any third (all outside the vault's y range): the third nearest the group's
    // center. No players: Alexei's third.
    inline std::size_t PickForbiddenThird(std::vector<Vec2> const& players, float rand01)
    {
        if (players.empty())
            return 2;
        std::array<std::uint32_t, kThirdCount> counts{};
        float sumY = 0.f;
        for (Vec2 const& p : players)
        {
            sumY += p.y;
            std::size_t const t = ThirdOf(p);
            if (t < kThirdCount)
                ++counts[t];
        }
        std::uint32_t const best = *std::max_element(counts.begin(), counts.end());
        if (best == 0)
        {
            float const cy = sumY / float(players.size());
            std::size_t nearest = 0;
            float nearestD = std::numeric_limits<float>::max();
            for (std::size_t i = 0; i < kThirdCount; ++i)
            {
                float const d = std::fabs(cy - 0.5f * (ThirdMinY(i) + ThirdMaxY(i)));
                if (d < nearestD)
                {
                    nearestD = d;
                    nearest = i;
                }
            }
            return nearest;
        }
        std::vector<std::size_t> ties;
        for (std::size_t i = 0; i < kThirdCount; ++i)
            if (counts[i] == best)
                ties.push_back(i);
        return ties[std::min(ties.size() - 1, static_cast<std::size_t>(rand01 * float(ties.size())))];
    }

    // A rectangle on the floor: from the center of its start edge, `length` along `facing` (radians), `width` across
    // (mod-boss-mechanics Shapes::LineFacing).
    struct Strip
    {
        Vec2 from;
        float facing = 0.f;
        float length = 0.f;
        float width = 0.f;
    };

    // The Out of bounds zone on a third: across the whole vault (30 yd; the room is 29), from the third's gate-side
    // edge toward Alexei's end (facing -y).
    float constexpr kThirdZoneWidth = 30.f;
    float constexpr kFacingMinusY = 4.71238898f;        // 3/2 pi

    inline Strip ThirdZone(std::size_t third)
    {
        return { { 0.5f * (kVaultMinX + kVaultMaxX), ThirdMaxY(third) }, kFacingMinusY,
            ThirdMaxY(third) - ThirdMinY(third), kThirdZoneWidth };
    }

    // AB6 the lane: 4 yd wide along the vault's north side (ScholomanceRework.h kBarovLaneMinX/MaxX, x 186-197, the
    // only side that runs the full length; at y -61 to -74 the pit reaches x 192), so its center is x 194.5
    // (192.5-196.5: clear of the pit, 0.5 yd off the wall). The full lane runs y -35 to -93. With Out of bounds the
    // lane stops kLaneZoneGap yd short of the forbidden third, on the side nearer the group (a tie: the longer piece).
    float constexpr kLaneCenterX = 194.5f;
    float constexpr kLaneZoneGap = 1.f;
    float constexpr kLaneMinLength = 8.f;
    static_assert(kLaneCenterX - 0.5f * kLaneWidth >= ScholomanceRework::kBarovLaneMinX, "the lane sits in the strip");
    static_assert(kLaneCenterX + 0.5f * kLaneWidth <= ScholomanceRework::kBarovLaneMaxX, "the lane sits in the strip");

    struct LaneSpan
    {
        float yMin = kVaultMinY;
        float yMax = kVaultMaxY;

        constexpr float Length() const { return yMax - yMin; }
        constexpr float DistanceTo(float y) const { return y > yMax ? y - yMax : (y < yMin ? yMin - y : 0.f); }
    };

    inline LaneSpan LaneFor(std::optional<std::size_t> forbidden, float groupY)
    {
        LaneSpan const full;
        if (!forbidden || *forbidden >= kThirdCount)
            return full;
        LaneSpan const gateSide{ ThirdMaxY(*forbidden) + kLaneZoneGap, full.yMax };
        LaneSpan const alexeiSide{ full.yMin, ThirdMinY(*forbidden) - kLaneZoneGap };
        bool const gateOk = gateSide.Length() >= kLaneMinLength;
        bool const alexeiOk = alexeiSide.Length() >= kLaneMinLength;
        if (gateOk != alexeiOk)
            return gateOk ? gateSide : alexeiSide;
        float const dGate = gateSide.DistanceTo(groupY);
        float const dAlexei = alexeiSide.DistanceTo(groupY);
        if (std::fabs(dGate - dAlexei) < 0.01f)
            return gateSide.Length() >= alexeiSide.Length() ? gateSide : alexeiSide;
        return dGate < dAlexei ? gateSide : alexeiSide;
    }

    inline Strip LaneStrip(LaneSpan span)
    {
        return { { kLaneCenterX, span.yMax }, kFacingMinusY, span.Length(), kLaneWidth };
    }

    inline bool InLane(LaneSpan span, Vec2 p, float margin = 0.f)
    {
        return std::fabs(p.x - kLaneCenterX) <= 0.5f * kLaneWidth + margin && p.y >= span.yMin - margin
            && p.y <= span.yMax + margin;
    }

    // AB7 the desks. Without Out of bounds: the build spec's five down the north lane (ScholomanceRework.h
    // kBarovDesks). With it, the desks outside the forbidden third (a desk radius clear of its edges) from the whole
    // grid: the five, one more down the lane, three on the gate tier, one before the pit and three down the south lane
    // (x 168-172). Every pair is at least 8 yd apart; leaving out any third still leaves 7 or more.
    inline std::array<Vec2, 13> constexpr kDeskGrid{ {
        { 192.5f, -45.0f }, { 192.5f, -53.0f }, { 192.5f, -61.0f }, { 192.5f, -69.0f }, { 192.5f, -77.0f },
        { 192.5f, -85.0f },
        { 176.0f, -40.0f }, { 176.0f, -48.0f }, { 184.0f, -44.0f },
        { 176.0f, -56.0f },
        { 170.0f, -70.0f }, { 170.0f, -78.0f }, { 170.0f, -86.0f },
    } };
    std::size_t constexpr kCanonicalDesks = 5;      // the first five are kBarovDesks

    constexpr bool DeskClearOf(Vec2 desk, std::size_t forbidden)
    {
        return desk.y < ThirdMinY(forbidden) - kDeskRadius || desk.y > ThirdMaxY(forbidden) + kDeskRadius;
    }

    // The desks the assignment may use.
    inline std::vector<Vec2> DeskCandidates(std::optional<std::size_t> forbidden, std::size_t players)
    {
        std::vector<Vec2> out;
        if (!forbidden && players <= kCanonicalDesks)
        {
            out.assign(kDeskGrid.begin(), kDeskGrid.begin() + kCanonicalDesks);
            return out;
        }
        for (Vec2 d : kDeskGrid)
            if (!forbidden || *forbidden >= kThirdCount || DeskClearOf(d, *forbidden))
                out.push_back(d);
        return out;
    }

    std::size_t constexpr kNoDesk = std::numeric_limits<std::size_t>::max();

    // Each player its own desk: repeatedly the closest (player, free desk) pair. Returns an index into `candidates`
    // per player (the order of `players`); kNoDesk when the desks ran out.
    inline std::vector<std::size_t> AssignDesks(std::vector<Vec2> const& players, std::vector<Vec2> const& candidates)
    {
        std::vector<std::size_t> out(players.size(), kNoDesk);
        std::vector<bool> used(candidates.size(), false);
        for (std::size_t round = 0; round < players.size(); ++round)
        {
            float best = std::numeric_limits<float>::max();
            std::size_t bp = kNoDesk;
            std::size_t bd = kNoDesk;
            for (std::size_t p = 0; p < players.size(); ++p)
            {
                if (out[p] != kNoDesk)
                    continue;
                for (std::size_t d = 0; d < candidates.size(); ++d)
                {
                    if (used[d])
                        continue;
                    float const dist = DungeonKit::Distance(players[p], candidates[d]);
                    if (dist < best)
                    {
                        best = dist;
                        bp = p;
                        bd = d;
                    }
                }
            }
            if (bp == kNoDesk)
                break;
            out[bp] = bd;
            used[bd] = true;
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AB10 where a fortune may lie
    // ----------------------------------------------------------------------------------------------------------------

    struct FortuneRules
    {
        RuleSet set = RULE_NONE;
        std::vector<Vec2> players;                  // every player of the fight
        std::optional<std::size_t> forbidden;       // Out of bounds: the third
        std::optional<LaneSpan> lane;               // Line up
        std::vector<Vec2> desks;                    // To your desks: the assigned desks
        std::vector<Vec2> taken;                    // fortunes already placed this announcement
        float minYd = kFortuneMinYd;
        float maxYd = kFortuneMaxYd;
        std::uint32_t tries = 60;
    };

    // The 2D distance from `p` to the nearest player (max float with none).
    inline float NearestPlayerYd(Vec2 p, std::vector<Vec2> const& players)
    {
        float best = std::numeric_limits<float>::max();
        for (Vec2 const& q : players)
            best = std::min(best, DungeonKit::Distance(p, q));
        return best;
    }

    constexpr bool InVault(Vec2 p, float inset = 1.f)
    {
        return p.x >= kVaultMinX + inset && p.x <= kVaultMaxX - inset && p.y >= kVaultMinY + inset
            && p.y <= kVaultMaxY - inset;
    }

    // Taking a fortune at `p` breaks the rule: inside the forbidden third (Out of bounds), off the lane (Line up), off
    // every desk (desks); for No running, Assembly and Keep your distance any spot 8-12 yd from the group is a walk
    // away from where the rule wants you (and the fortune's Demerit stands even if the taker walks back, round 3).
    inline bool FortuneFits(Vec2 p, FortuneRules const& rules)
    {
        if (!InVault(p))
            return false;
        float const nearest = NearestPlayerYd(p, rules.players);
        if (!rules.players.empty() && (nearest < rules.minYd || nearest > rules.maxYd))
            return false;
        if (Has(rules.set, RULE_OUT_OF_BOUNDS) && rules.forbidden && !InThird(*rules.forbidden, p, -1.f))
            return false;
        if (Has(rules.set, RULE_LINE_UP) && rules.lane && InLane(*rules.lane, p, 1.5f))
            return false;
        for (Vec2 const& d : rules.desks)
            if (DungeonKit::Distance(p, d) < kDeskRadius + 1.f)
                return false;
        for (Vec2 const& f : rules.taken)
            if (DungeonKit::Distance(p, f) < kFortunesApartYd)
                return false;
        return true;
    }

    // Up to `count` spots: random points in the vault that fit and stand on its floor (`floorOk`, the engine's map
    // height check). When none fits, the distance band widens once (2 yd nearer, 4 yd farther).
    template <typename Rand01, typename FloorOk>
    std::vector<Vec2> PickFortuneSpots(FortuneRules rules, std::uint32_t count, Rand01&& rand01, FloorOk&& floorOk)
    {
        std::vector<Vec2> out;
        for (std::uint32_t i = 0; i < count; ++i)
        {
            std::optional<Vec2> found;
            for (std::uint32_t pass = 0; pass < 2 && !found; ++pass)
            {
                FortuneRules r = rules;
                if (pass == 1)
                {
                    r.minYd = std::max(0.f, rules.minYd - 2.f);
                    r.maxYd = rules.maxYd + 4.f;
                }
                for (std::uint32_t t = 0; t < r.tries; ++t)
                {
                    Vec2 const p{ kVaultMinX + 1.f + rand01() * (kVaultMaxX - kVaultMinX - 2.f),
                        kVaultMinY + 1.f + rand01() * (kVaultMaxY - kVaultMinY - 2.f) };
                    if (FortuneFits(p, r) && floorOk(p))
                    {
                        found = p;
                        break;
                    }
                }
            }
            if (!found)
                break;
            out.push_back(*found);
            rules.taken.push_back(*found);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // One announcement's clock
    // ----------------------------------------------------------------------------------------------------------------

    enum class RulePhase : std::uint8_t
    {
        Idle,           // no rule
        Warning,        // announced: get ready
        Window,         // judged (Out of bounds, No running); the fortunes lie
    };

    struct RuleTimes
    {
        std::uint64_t announceMs = 0;
        std::uint32_t warnMs = 0;
        std::uint32_t windowMs = kRuleWindowMs;

        constexpr std::uint64_t OpenMs() const { return announceMs + warnMs; }
        constexpr std::uint64_t CloseMs() const { return announceMs + warnMs + windowMs; }

        constexpr RulePhase PhaseAt(std::uint64_t nowMs) const
        {
            if (nowMs < announceMs || nowMs >= CloseMs())
                return RulePhase::Idle;
            return nowMs < OpenMs() ? RulePhase::Warning : RulePhase::Window;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The Barov Family Vault's solo lesson (detention, SC 2960-2971; handoff section 3.7)
    // ----------------------------------------------------------------------------------------------------------------

    // "The vault reads 2 rules that work alone (No running, Out of bounds); a fortune lies in reach. Pass: no rule
    // broken, fortune left." 15 s: Out of bounds on the third the student stands in (4 s to get out: they land on
    // Alexei's spot, 17.6 yd inside his third), then No running announced while that window still runs (the student
    // is already out, then freezes). A fortune lies in reach in each window: inside the forbidden third, then a few
    // steps away. A broken rule or a fortune taken is one 15% (heroic 25%) hit plus Weakened, once per rule; the lesson
    // fails on any (SoloLesson.h). Both difficulties read the same two rules; only the hit differs.
    struct LessonRule
    {
        RuleBit rule = RULE_NONE;
        RuleTimes times;
        float fortuneMinYd = 0.f;
        float fortuneMaxYd = 0.f;
    };

    inline std::array<LessonRule, 2> constexpr kLessonRules{ {
        { RULE_OUT_OF_BOUNDS, { 500, 4000, 5000 }, 4.f, 8.f },      // window 4.5-9.5 s
        { RULE_NO_RUNNING, { 7000, 3000, 4500 }, 3.f, 6.f },        // window 10-14.5 s
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The Graduate Examiner (S13's hard mode gauntlet, SC 3046; handoff section 3.6): "both mechanics at H values"
    // ----------------------------------------------------------------------------------------------------------------

    // The examiner (NPC_SC_EXAMINER_ALEXEI 300553, declared by S13, ScriptName kExaminerScriptName: its own AI,
    // registered once wave C binds, kWaveCBound) runs the Code of Conduct and the Bargain on the heroic numbers
    // whatever the map: rules (a single first, then pairs), 4 s warnings, two fortunes, the heroic Rod ladder, at 80k
    // health. No Veil, no Unholy Aura, no boss state, no Passing Grade. A gauntlet room lasts about 22 s (SC), so the
    // first rule comes at 6 s and the next 18 s later (S9's reading).
    char constexpr kExaminerScriptName[] = "npc_sc_examiner_alexei";
    std::uint32_t constexpr kExaminerHealth = 80000;
    std::uint32_t constexpr kExaminerFirstRuleMs = 6000;
    std::uint32_t constexpr kExaminerRuleEveryMs = 18000;
    bool constexpr kExaminerHeroic = true;
}

#endif
