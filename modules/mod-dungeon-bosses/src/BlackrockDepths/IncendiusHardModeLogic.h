/*
 * mod-dungeon-bosses, Blackrock Depths D12:
 * Lord Incendius's hard mode, Lord of the Lake, the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/blackrock-depths-2-shadowforge-city.md "Hard mode" and "Build spec" (IN9-IN14; rulings 81-84, 90),
 * handoff sections 3.5 row D12, 3.6, 3.7, 7 #14 A (the user's ruling: the arena is the Anvil bulge s -24 to +24, both
 * necks sealed at the pull, the crumble eats 2 yd of the long edges per step for three steps, the giant hovers near
 * causeway height at kLakeLordSpot), 7 #15 (heroic only; the Cinder stays lit until the hard mode kill or a reset).
 * Tested by tests/brd_incendius_hard_mode_test.cpp; apps/dbc-tools source/npcs/blackrock_depths/incendius_hard_mode.py
 * declares the same ids.
 *
 *   Spells      the WP's ids, inside kSpellsLordOfTheLake (211180-211229)
 *   Tuning      the hard mode's numbers and cadences, straight from the build spec (gap 36 picks marked)
 *   The giant   his spot in the lake (kLakeLordSpot), his scale, and the combat reach that lets the reach band hit
 *               him (melee range is 3D: he hovers at causeway height)
 *   Reach       IN14's reach band: the 6 yd band along the current near (south-east) edge of the bulge; a player in it
 *               keeps Firelord's Breath off; the tank bot's soak line inside it
 *   Arm Sweep   IN11's three 10 yd bands across the floor and the throw's bearing (toward the far edge)
 *   Lava Spawn  IN12's climb spots on the current edges, the walk's speed, Firelord's Will
 *   Crumble     IN13's timer (the three steps of section 7 #14 A)
 *   Cinder      IN9: the use spell's refusals (heroic, out of combat, Incendius alive and idle, on the island)
 *   Intro       the Cinder's toss: the yell, his jump off the edge, the giant rising in the lake
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_INCENDIUS_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_INCENDIUS_HARD_MODE_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "IncendiusLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace BrdLordOfTheLake
{
    using BlackrockDepthsRework::Point3;
    using BrdIncendius::Band;
    using BrdIncendius::FramePoint;
    using BrdIncendius::ProfilePoint;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsLordOfTheLake;

    enum IncendiusHardModeSpells : std::uint32_t
    {
        SPELL_LAKE_CRUSHING_FIST        = kSpellSlice.first + 0,    // 211180 IN10 the circle's hit (resolve copy)
        SPELL_LAKE_CRUSHING_FIST_TANK   = kSpellSlice.first + 1,    // 211181 IN10 the tank's own hit (scaled hit)
        SPELL_LAKE_CRUSHING_FIST_LOOK   = kSpellSlice.first + 2,    // 211182 IN10 the crack where it lands (look)
        SPELL_LAKE_ARM_SWEEP_CAST       = kSpellSlice.first + 3,    // 211183 IN11 the 4 s cast bar (Physical)
        SPELL_LAKE_ARM_SWEEP            = kSpellSlice.first + 4,    // 211184 IN11 the band's hit (resolve copy)
        SPELL_LAKE_FIRELORDS_BREATH     = kSpellSlice.first + 5,    // 211185 IN14 a second of the breath (scaled hit)
        SPELL_LAKE_FIRELORDS_WILL       = kSpellSlice.first + 6,    // 211186 IN12 +10% damage done a stack, 10
        SPELL_LAKE_LAVA_SPAWN_CLIMB     = kSpellSlice.first + 7,    // 211187 IN12 a spawn climbs out (look)
        SPELL_LAKE_ERUPTION             = kSpellSlice.first + 8,    // 211188 IN12 / IN9 a lava burst at a point (look)
        SPELL_LAKE_LAVA_SPAWN_ARRIVES   = kSpellSlice.first + 9,    // 211189 IN12 a spawn sinks into the Anvil (look)
        SPELL_LAKE_LORD_RISES           = kSpellSlice.first + 10,   // 211190 IN9 the giant rises in the lake (look)
        SPELL_LAKE_CINDER_TOSS          = kSpellSlice.first + 11,   // 211191 IN9 the Cinder arcs into the lava (look)
        // 211192-211229 spare
    };
    static_assert(SPELL_LAKE_CINDER_TOSS <= kSpellSlice.last, "Lord of the Lake's spells must stay in its slice");

    // The Cinder of the Firelord (IT): item 70621, its use spell 211260 (the first of kSpellsEventItems), bound to
    // spell_brd_cinder_of_the_firelord (this WP's SpellScript).
    inline constexpr std::uint32_t kItemCinder = BlackrockDepthsRework::kItemCinderOfTheFirelord;
    inline constexpr std::uint32_t kSpellCinderUse = BlackrockDepthsRework::kSpellsEventItems.first;

    // Registry tags (the failure ledger and the playtest greps). 15 is the BM drill's kBrdTagSweep (MechanicDrill.h),
    // reserved by D11 (BrdIncendius::TAG_IN_ARM_SWEEP); D11's own are 3-5, 13 and 14.
    enum LakeTags : std::uint32_t
    {
        TAG_LAKE_ARM_SWEEP      = BrdIncendius::TAG_IN_ARM_SWEEP,   // IN11 (15)
        TAG_LAKE_CRUSHING_FIST  = 17,                               // IN10
        TAG_LAKE_REACH          = 18,                               // IN14 the tank bot's soak line (no failures)
        TAG_LAKE_NO_BEHIND      = 19,                               // the melee and tank bounds carrier
    };

    // creature_text 9017: D11's groups 4, 6 and 7 are this WP's lines (in D11's rev); this WP owns 8 and 9
    // (rev_incendius_hard_mode_blackrock_depths.sql).
    enum LakeTexts : std::uint8_t
    {
        YELL_LAKE_CINDER            = BrdIncendius::YELL_IN_LORD_OF_THE_LAKE,   // 4 IN9
        EMOTE_LAKE_ARM_RAISED       = BrdIncendius::EMOTE_IN_ARM_RAISED,        // 6 IN11
        EMOTE_LAKE_BREATH           = BrdIncendius::EMOTE_IN_BREATH,            // 7 IN14
        EMOTE_LAKE_RISES            = 8,    // IN9 the giant rises in the lake (the intro, a reload, a wipe)
        EMOTE_LAKE_SPAWNS           = 9,    // IN12 the Lava Spawn climb out
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Hard mode"; damage = % of the level 60 reference row)
    // ----------------------------------------------------------------------------------------------------------------

    // Health (section 3.6): about 340,000, one kill (no rebirth), set by the script at the pull, his heroic 160k back
    // on the evade. Lava Spawn 6,000 (its heroic template is WP-H's: 300795 -> 310406).
    inline constexpr std::uint32_t kLakeHealth = 340000;
    inline constexpr std::uint32_t kLavaSpawnHealth = 6000;
    inline constexpr std::uint32_t kRebirths = 0;

    // The kit in the hard mode (S2 "Kit in the hard mode", ruling 84): Fire Storm every 10 s, its patch 20 s (not 30);
    // Magma Fist never on the tank (ruling 90); Lava Surge off (the Arm Sweep takes its place).
    inline constexpr std::uint32_t kFireStormEveryMs = 10000;
    inline constexpr std::uint32_t kFireStormLifeMs = 20000;
    inline constexpr bool kMagmaFistOnTank = false;
    inline constexpr bool kLavaSurge = false;

    // IN10 Crushing Fist: from 10 s, every 15 s, a 3 s marker, a 6 yd circle on the tank's spot; the tank takes 35%
    // (his hit to take: the circle spares him and the script hits him), anyone else inside 45% + Weakened.
    inline constexpr std::uint32_t kCrushingFirstMs = 10000;
    inline constexpr std::uint32_t kCrushingEveryMs = 15000;
    inline constexpr std::uint32_t kCrushingWarnMs = 3000;
    inline constexpr float kCrushingRadiusYd = 6.f;
    inline constexpr float kCrushingTankPct = 35.f;
    inline constexpr float kCrushingOthersPct = 45.f;

    // IN11 Arm Sweep: from 20 s, every 30 s, a 4 s cast (emote line 6): a 10 yd band across the floor at one of three
    // spots; 30% and a throw over the far edge (a fall: lethal, ruling 84). The tank is included and slides along the
    // edge.
    inline constexpr std::uint32_t kSweepFirstMs = 20000;
    inline constexpr std::uint32_t kSweepEveryMs = 30000;
    inline constexpr std::uint32_t kSweepCastMs = 4000;
    inline constexpr float kSweepWidthYd = 10.f;
    inline constexpr float kSweepPct = 30.f;
    // The band runs this far past both real edges (the whole width, whatever the profile does inside it).
    inline constexpr float kSweepOverhangYd = 3.f;
    // "Nothing lands during the Sweep": Fire Storm and Magma Fist (2 s markers) and Crushing Fist (3 s) are held from
    // this long before the cast starts until it ends, so nothing registered then lands inside the cast.
    inline constexpr std::uint32_t kSweepPreHoldMs = 3000;

    // The three spots (frame s): south-west (toward the entrance), the middle (in front of the giant, the Anvil's s)
    // and north-east (toward Fineous). 10 yd bands: s -11..-1, 1..11, 13..23 (2 yd of safe ground between them).
    inline constexpr std::array<float, 3> kSweepSpots{ { -6.f, 6.f, 18.f } };

    enum class SweepSpot : std::uint8_t
    {
        SouthWest = 0,
        Middle = 1,
        NorthEast = 2,
    };

    constexpr char const* SweepSpotName(SweepSpot spot)
    {
        switch (spot)
        {
            case SweepSpot::SouthWest:
                return "south-west";
            case SweepSpot::Middle:
                return "middle";
            default:
                return "north-east";
        }
    }

    // A random spot, never the last one (`roll` picks between the other two; the first sweep: `last` = kNoSpot, any
    // of the three).
    inline constexpr std::uint8_t kNoSpot = 0xFF;

    constexpr SweepSpot PickSweepSpot(std::uint8_t last, std::uint32_t roll)
    {
        std::uint8_t const n = static_cast<std::uint8_t>(kSweepSpots.size());
        if (last >= n)
            return static_cast<SweepSpot>(roll % n);
        return static_cast<SweepSpot>((last + 1 + roll % 2) % n);
    }

    // IN12 Lava Spawn: from 15 s, every 20 s, 2 climb over the edges (one on each long edge, at a random s along the
    // bulge) and walk to The Black Anvil over about 10 s. Each that arrives heals him 5% and gives Firelord's Will
    // (+10% damage, cap 10). Slows, roots and stuns hold them (a reward).
    inline constexpr std::uint32_t kSpawnFirstMs = 15000;
    inline constexpr std::uint32_t kSpawnEveryMs = 20000;
    inline constexpr std::uint32_t kSpawnCount = 2;
    inline constexpr std::uint32_t kSpawnWalkMs = 10000;
    inline constexpr float kSpawnArriveYd = 3.f;                // 2D, to the Anvil's centre
    inline constexpr float kSpawnMinSpeedYdS = 0.5f;
    inline constexpr std::uint32_t kSpawnReaimMs = 1000;
    inline constexpr std::uint32_t kSpawnCorpseMs = 5000;
    inline constexpr float kSpawnEdgeInsetYd = 1.5f;            // this far inside the current (crumbled) edge
    inline constexpr float kSpawnSMin = -4.f;                   // the bulge, 2 yd inside its tips
    inline constexpr float kSpawnSMax = 16.f;
    inline constexpr std::uint32_t kSpawnHealPct = 5;
    inline constexpr float kWillPctPerStack = 10.f;
    inline constexpr std::uint32_t kWillMaxStacks = 10;

    // IN13 The island crumbles (section 7 #14 A): the next 2 yd of both long edges crumble at 40 s, 80 s and 120 s
    // (each after D11's 5 s edge marker, raised kBandWarnMs earlier), three steps, then it stops.
    inline constexpr std::array<std::uint32_t, 3> kCrumbleAtMs{ { 40000, 80000, 120000 } };
    static_assert(kCrumbleAtMs.size() == BrdIncendius::kCrumbleMaxSteps, "one timer step per crumble step");

    constexpr std::uint32_t CrumbleRaiseMs(std::size_t step)
    {
        return kCrumbleAtMs[step] - BrdIncendius::kBandWarnMs;
    }

    // IN14 Firelord's Breath: checked every 1 s; when no player has stood in his reach for 3 s he breathes over the
    // whole island, 8% a second to everyone (no Weakened, no cap) until a player is back.
    inline constexpr std::uint32_t kBreathCheckMs = 1000;
    inline constexpr std::uint32_t kBreathGraceMs = 3000;
    inline constexpr float kBreathPct = 8.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Firelord's Will: +10% a stack on everything he deals. His melee reads the aura; the reference-sized hits ignore
    // caster modifiers, so the script multiplies its own (Crushing Fist, the Arm Sweep, the Breath) by this.
    // ----------------------------------------------------------------------------------------------------------------

    constexpr float WillFactor(std::uint32_t stacks)
    {
        return 1.f + kWillPctPerStack / 100.f * static_cast<float>(stacks < kWillMaxStacks ? stacks : kWillMaxStacks);
    }

    // His health after an arrival: + kSpawnHealPct of his maximum, never past it.
    constexpr std::uint32_t HealedHealth(std::uint32_t health, std::uint32_t maxHealth)
    {
        std::uint64_t const after = static_cast<std::uint64_t>(health)
            + static_cast<std::uint64_t>(maxHealth) * kSpawnHealPct / 100u;
        return static_cast<std::uint32_t>(after > maxHealth ? maxHealth : after);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The giant (section 7 #14 A; VISUALS INCENDIUS_GIANT_SCALE_RANGE 8-10)
    // ----------------------------------------------------------------------------------------------------------------

    // His own display (creature_template_model 9017 is 1204, live 2026-11-17; _visuals DISPLAY_INCENDIUS_GIANT) at a
    // creature scale of 9 (the model is about 3 yd tall at 1.0: a 27 yd giant). He stands in the air over the lava at
    // kLakeLordSpot (causeway height, so melee reach and line of sight work; the lava is 37-40 yd below).
    inline constexpr std::uint32_t kGiantDisplay = 1204;
    inline constexpr float kGiantScale = 9.f;
    inline constexpr Point3 kGiantSpot = BlackrockDepthsRework::kLakeLordSpot;
    // The lava's surface under the spot (NAVMESH 2.5: -108.9 to -112.4): his intro jump ends here.
    inline constexpr float kLakeSurfaceZ = -108.f;

    // The near edge is the south-east one (wLo): the giant stands at s ~6, w ~-28 in D11's frame.
    constexpr bool GiantOnSouthEast()
    {
        return BrdIncendius::ToFrame(kGiantSpot.XY()).w < 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Reach (IN14, ruling 90): the 6 yd band along the current near edge, over the bulge (s -4 to +16). A player in it
    // (or between it and the edge) is in reach; the band moves in with every crumble step.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kReachDepthYd = 6.f;
    inline constexpr float kReachSMin = -4.f;
    inline constexpr float kReachSMax = 16.f;
    inline constexpr float kReachRimSlackYd = 1.f;              // a player on the rim, just past the polygon, counts
    inline constexpr float kReachZToleranceYd = 5.f;            // on the causeway (the C++ checks the height)
    // The tank bot's soak line: a short straight line in front of him (s 3.5 to 7.5, where the bots' safe floor reaches
    // deepest into the band at every step), kSoakWidthYd wide, inside both the band and the bots' safe floor.
    inline constexpr float kSoakSMin = 3.5f;
    inline constexpr float kSoakSMax = 7.5f;
    inline constexpr float kSoakWidthYd = 2.f;
    // The melee range the giant gets past the band's farthest point (a player's combat reach 1.5 and the engine's 4/3
    // are added by Unit::GetMeleeRange).
    inline constexpr float kPlayerCombatReach = 1.5f;
    inline constexpr float kMeleeMarginYd = 1.f;

    // The near edge's w at `s` after `steps` crumble steps (the real edge moved in by the crumbled depth, square to
    // it).
    inline float NearEdgeW(float s, std::uint32_t steps)
    {
        ProfilePoint const p = BrdIncendius::ProfileAt(s);
        float const depth = BrdIncendius::CrumbledDepth(steps);
        return GiantOnSouthEast() ? p.wLo + BrdIncendius::LateralShiftAt(s, true, depth)
            : p.wHi - BrdIncendius::LateralShiftAt(s, false, depth);
    }

    // The inner side of the reach band at `s`.
    inline float ReachInnerW(float s, std::uint32_t steps)
    {
        return GiantOnSouthEast() ? NearEdgeW(s, steps) + kReachDepthYd : NearEdgeW(s, steps) - kReachDepthYd;
    }

    // Is a point on the causeway (map plane) in reach after `steps`? Between the near edge (kReachRimSlackYd past it)
    // and the band's inner side, over the bulge.
    inline bool InReach(Vec2 p, std::uint32_t steps)
    {
        FramePoint const f = BrdIncendius::ToFrame(p);
        if (f.s < kReachSMin || f.s > kReachSMax)
            return false;
        float const edge = NearEdgeW(f.s, steps);
        float const inner = ReachInnerW(f.s, steps);
        return GiantOnSouthEast() ? (f.w >= edge - kReachRimSlackYd && f.w <= inner)
            : (f.w <= edge + kReachRimSlackYd && f.w >= inner);
    }

    // The band's edge and inner points every yd of s (the tests and the giant's reach below).
    inline std::vector<Vec2> ReachSamples(std::uint32_t steps)
    {
        std::vector<Vec2> out;
        for (int i = 0; i <= static_cast<int>(kReachSMax - kReachSMin); ++i)
        {
            float const s = kReachSMin + static_cast<float>(i);
            out.push_back(BrdIncendius::ToWorld(s, NearEdgeW(s, steps)));
            out.push_back(BrdIncendius::ToWorld(s, ReachInnerW(s, steps)));
        }
        return out;
    }

    // The farthest point of the band from the giant (2D; he hovers at causeway height).
    inline float ReachFarthestYd(std::uint32_t steps)
    {
        float far = 0.f;
        for (Vec2 const& p : ReachSamples(steps))
            far = std::max(far, DungeonKit::Distance(p, kGiantSpot.XY()));
        return far;
    }

    // The giant's combat reach after `steps`: a player anywhere in the band is within melee range of him (and he of
    // the tank there).
    inline float GiantCombatReach(std::uint32_t steps)
    {
        return ReachFarthestYd(steps) + kMeleeMarginYd - kPlayerCombatReach - 4.f / 3.f;
    }

    // The engine's melee range between the giant (combat reach `giantReach`) and a player (Unit::GetMeleeRange).
    constexpr float MeleeRangeYd(float giantReach)
    {
        return giantReach + kPlayerCombatReach + 4.f / 3.f;
    }

    // The tank bot's soak line after `steps`: constant w over s kSoakSMin..kSoakSMax, midway between the first w whose
    // outer side is on the bots' safe floor (BrdIncendius::SafeFloor: 2 yd inside the lethal edge, conservative at the
    // profile's corners) all along, and the band's inner side less half its width.
    inline Band SoakLine(std::uint32_t steps)
    {
        bool const se = GiantOnSouthEast();
        float const sign = se ? 1.f : -1.f;
        float const half = kSoakWidthYd * 0.5f;
        int const samples = static_cast<int>((kSoakSMax - kSoakSMin) * 2.f);
        auto sAt = [](int i) { return kSoakSMin + 0.5f * static_cast<float>(i); };
        float hi = se ? 1000.f : -1000.f;
        float outermost = se ? 1000.f : -1000.f;
        for (int i = 0; i <= samples; ++i)
        {
            hi = se ? std::min(hi, ReachInnerW(sAt(i), steps) - half) : std::max(hi, ReachInnerW(sAt(i), steps) + half);
            outermost = se ? std::min(outermost, NearEdgeW(sAt(i), steps))
                : std::max(outermost, NearEdgeW(sAt(i), steps));
        }
        std::vector<Vec2> const safe = BrdIncendius::SafeFloor(steps);
        float lo = hi;
        for (int k = 0; k <= static_cast<int>(kReachDepthYd * 20.f); ++k)
        {
            float const w = outermost + sign * 0.05f * static_cast<float>(k);
            if (se ? w > hi : w < hi)
                break;
            bool inside = true;
            for (int i = 0; i <= samples && inside; ++i)
                inside = DungeonKit::PointInPolygon(std::span<Vec2 const>(safe),
                    BrdIncendius::ToWorld(sAt(i), w - sign * half));
            if (inside)
            {
                lo = w;
                break;
            }
        }
        float const w = (lo + hi) * 0.5f;
        return { BrdIncendius::ToWorld(kSoakSMin, w), BrdIncendius::ToWorld(kSoakSMax, w), kSoakWidthYd };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The giant's own reach and his Hand (R-1-B M2, orchestrator default after R-1)
    // ----------------------------------------------------------------------------------------------------------------

    // GiantCombatReach made every ranged shot (Auto Shot, wands: Spell.cpp's TOO_CLOSE inside min range + the melee
    // range, which counts both combat reaches) fail on nearly the whole island. The giant keeps a small reach of his
    // own: no point of the floor is inside his melee range, so no hunter or wand is ever too close, and his spells and
    // the players' taunts still reach the near half. The melee hit his Hand instead, a stand-in on the near rim that
    // shares his health (every hit on it lands on him, its threat goes to him); his swings on the tank in the reach
    // band are the script's (no range check: AttackerStateUpdate). GiantCombatReach above stays the band's geometry.
    // The nearest rim point is 12.6 yd from him (s 8, the bulge's tip), so his melee range (4.3 yd) plus Auto Shot's
    // 5 yd minimum stays short of every floor point; his Fiery Burst (40 yd) and a 30 yd taunt reach the soak line.
    inline constexpr float kGiantReachYd = 1.5f;
    inline constexpr float kRangedMinYd = 6.f;              // the longest stock ranged minimum (Auto Shot 5) + margin
    inline constexpr std::uint32_t NPC_LAKE_HAND = 300828;  // a spare wave 1 kit creature (incendius_hard_mode.py)
    static_assert(BlackrockDepthsRework::kCreaturesWave1.Contains(NPC_LAKE_HAND), "a wave 1 kit creature id");
    inline constexpr float kHandEdgeInsetYd = 1.5f;         // inside the current (crumbled) near edge
    inline constexpr float kHandScale = 1.5f;
    inline constexpr std::uint32_t kHandSyncMs = 250;       // its health back on his, its threat moved to him

    // The Hand's spot after `steps`: by the tank's soak line (its s middle), kHandEdgeInsetYd inside the near edge.
    // It moves in with every crumble step (raised: the step counts from its warning).
    inline Vec2 HandSpot(std::uint32_t steps)
    {
        float const s = (kSoakSMin + kSoakSMax) * 0.5f;
        float const sign = GiantOnSouthEast() ? 1.f : -1.f;
        return BrdIncendius::ToWorld(s, NearEdgeW(s, steps) + sign * kHandEdgeInsetYd);
    }

    // The giant's corpse (R-1-B M1): the lethal hit puts him on the near rim at the Hand's spot (clear of gravity, so
    // the death does not drop him into the lava), where the group can loot him.
    inline Vec2 CorpseSpot(std::uint32_t steps)
    {
        return HandSpot(steps);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arm Sweep (IN11)
    // ----------------------------------------------------------------------------------------------------------------

    // The 10 yd band across the floor at `spot`: from past the near edge to past the far edge (the widest the real
    // profile gets within the band, plus kSweepOverhangYd on both sides).
    inline Band SweepBand(SweepSpot spot)
    {
        float const s = kSweepSpots[static_cast<std::size_t>(spot)];
        float lo = 1000.f;
        float hi = -1000.f;
        for (int i = 0; i <= static_cast<int>(kSweepWidthYd * 2.f); ++i)
        {
            ProfilePoint const p = BrdIncendius::ProfileAt(s - kSweepWidthYd * 0.5f + 0.5f * static_cast<float>(i));
            lo = std::min(lo, p.wLo);
            hi = std::max(hi, p.wHi);
        }
        return { BrdIncendius::ToWorld(s, lo - kSweepOverhangYd), BrdIncendius::ToWorld(s, hi + kSweepOverhangYd),
            kSweepWidthYd };
    }

    // The throw's bearing: across the causeway away from the giant (toward the far edge), radians [0, 2pi).
    inline float SweepThrowBearing()
    {
        Vec2 const away = GiantOnSouthEast() ? BrdIncendius::kAcross
            : Vec2{ -BrdIncendius::kAcross.x, -BrdIncendius::kAcross.y };
        float const o = std::atan2(away.y, away.x);
        return o < 0.f ? o + 2.f * 3.14159265358979f : o;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Lava Spawn (IN12)
    // ----------------------------------------------------------------------------------------------------------------

    // Where a spawn climbs out: at `s` (clamped to the bulge) on one long edge, kSpawnEdgeInsetYd inside the current
    // crumbled edge (never past the floor's middle line). `southEast`: that edge, else the north-west one.
    inline Vec2 SpawnSpot(float s, bool southEast, std::uint32_t steps)
    {
        s = std::clamp(s, kSpawnSMin, kSpawnSMax);
        ProfilePoint const p = BrdIncendius::ProfileAt(s);
        float const depth = BrdIncendius::CrumbledDepth(steps) + kSpawnEdgeInsetYd;
        float const mid = BrdIncendius::MidlineAt(s);
        float const w = southEast ? std::min(p.wLo + BrdIncendius::LateralShiftAt(s, true, depth), mid)
            : std::max(p.wHi - BrdIncendius::LateralShiftAt(s, false, depth), mid);
        return BrdIncendius::ToWorld(s, w);
    }

    // `roll` in [0, 1]: the s along the bulge.
    constexpr float SpawnS(float roll)
    {
        return kSpawnSMin + (kSpawnSMax - kSpawnSMin) * (roll < 0.f ? 0.f : (roll > 1.f ? 1.f : roll));
    }

    // A spawn's walk speed over `distanceYd` (it arrives in kSpawnWalkMs when nothing slows it).
    inline float SpawnSpeed(float distanceYd)
    {
        return std::max(kSpawnMinSpeedYdS, distanceYd * 1000.f / static_cast<float>(kSpawnWalkMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Cinder of the Firelord (IN9): the use spell's refusals (a refused cast keeps the item)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kCinderZToleranceYd = 5.f;
    inline constexpr float kCinderBossRangeYd = 60.f;           // he patrols round the Anvil: anywhere on the bulge

    // On the island: inside the arena's real floor (s -24 to +24, D11's ArenaFloor) at the causeway's height.
    inline bool OnTheIsland(Vec2 p, float z)
    {
        std::vector<Vec2> const floor = BrdIncendius::ArenaFloor();
        return std::fabs(z - BrdIncendius::kFloorZ) <= kCinderZToleranceYd
            && DungeonKit::PointInPolygon(std::span<Vec2 const>(floor), p);
    }

    enum class CinderRefusal : std::uint8_t
    {
        None,
        NotInDungeon,       // not in a Blackrock Depths instance
        NotHeroic,          // heroic only (section 7 #15)
        AlreadyLit,         // the Cinder already burns (until the hard mode kill or a reset; a wipe never burns it)
        IncendiusGone,      // he is dead (or not near)
        IncendiusFighting,  // he is in combat (or his encounter is in progress)
        InCombat,           // the user is in combat
        NotOnTheIsland,     // not on the island near him
    };

    struct CinderCheck
    {
        std::uint32_t mapId = 0;
        bool hasInstance = false;
        bool heroic = false;
        bool lit = false;
        bool incendiusAlive = false;        // found within kCinderBossRangeYd and alive
        bool incendiusEngaged = false;
        std::uint32_t incendiusState = 0;   // his boss slot (BOSS_INCENDIUS)
        bool casterInCombat = false;
        bool onTheIsland = false;
    };

    constexpr CinderRefusal CinderUseRefusal(CinderCheck const& c)
    {
        if (c.mapId != BlackrockDepthsRework::kMapBlackrockDepths || !c.hasInstance)
            return CinderRefusal::NotInDungeon;
        if (!c.heroic)
            return CinderRefusal::NotHeroic;
        if (c.lit)
            return CinderRefusal::AlreadyLit;
        if (!c.incendiusAlive || c.incendiusState == DungeonKit::State::Done)
            return CinderRefusal::IncendiusGone;
        if (c.incendiusEngaged || c.incendiusState == DungeonKit::State::InProgress)
            return CinderRefusal::IncendiusFighting;
        if (c.casterInCombat)
            return CinderRefusal::InCombat;
        if (!c.onTheIsland)
            return CinderRefusal::NotOnTheIsland;
        return CinderRefusal::None;
    }

    constexpr char const* CinderRefusalText(CinderRefusal why)
    {
        switch (why)
        {
            case CinderRefusal::NotInDungeon:
                return "The Cinder of the Firelord stirs only in Blackrock Depths.";
            case CinderRefusal::NotHeroic:
                return "The Cinder of the Firelord stirs only in the heroic Depths.";
            case CinderRefusal::AlreadyLit:
                return "The lake already burns with the Firelord's flame.";
            case CinderRefusal::IncendiusGone:
                return "Lord Incendius is not here to answer the Cinder.";
            case CinderRefusal::IncendiusFighting:
                return "Lord Incendius is already fighting.";
            case CinderRefusal::InCombat:
                return "You cannot toss the Cinder while in combat.";
            case CinderRefusal::NotOnTheIsland:
                return "Toss the Cinder from Lord Incendius's island.";
            default:
                return "";
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The intro (IN9: "the toss, his yell, a scripted jump off the long side, then he reappears in the lake at the
    // giant's spot at the scaled size")
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kIntroJumpMs = 2500;         // after the yell
    inline constexpr std::uint32_t kIntroRiseMs = 4500;         // he stands in the lake as the giant
    inline constexpr float kIntroJumpSpeedXY = 20.f;
    inline constexpr float kIntroJumpMinSpeedZ = 10.f;
    inline constexpr std::uint32_t kIdleCheckMs = 500;          // the idle hook's pose check
    inline constexpr float kCinderTossSpeed = 20.f;             // the look's flight, yd/s

    enum class IntroStep : std::uint8_t
    {
        Yell = 0,       // he stops his patrol, turns to the lake and yells (line 4)
        Jump = 1,       // he jumps off the near edge into the lava
        Rise = 2,       // the giant rises at kGiantSpot (line 8)
    };

    // The step the intro is at `ms` after the Cinder.
    constexpr IntroStep IntroStepAt(std::uint32_t ms)
    {
        if (ms >= kIntroRiseMs)
            return IntroStep::Rise;
        if (ms >= kIntroJumpMs)
            return IntroStep::Jump;
        return IntroStep::Yell;
    }
}

#endif
