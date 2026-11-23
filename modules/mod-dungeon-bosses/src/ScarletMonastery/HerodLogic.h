/*
 * mod-dungeon-bosses, Scarlet Monastery D11:
 * Herod (3975), "Blades of Light", the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Herod" (HB0-HB5, Heroic, Build spec), handoff section 3.5 row D11, 3.6,
 * 3.8 (the hall, NAVMESH), 7 #31 A (the garrison's march; the lap drilled by G2's herod-lap row). Tested by
 * tests/sm_herod_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsHerod (212980-213019), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/herod.py
 *   Hall       the pit (543 sq yd, equivalent radius 13.1 round the centroid), the ledge ring (12.3 to 25.5 yd out),
 *              the door spur (the hall's only entrance, south), the lap's route along the ledge's middle (121 yd,
 *              through the landing at the door spur), the stragglers' entry spot inside the door, the garrison's
 *              march for the hard mode (section 7 #31 A)
 *   Tuning     NH<> percents, sizes and timers straight from the build spec (percents of the reference row: N level 37
 *              normal, H level 60 heroic; the hard mode's own numbers are D11H's, through HerodFight.h)
 *   Picks      HB1c a blade's lane (from him across the pit to its far edge), HB2w the whirling axe's path
 *   Beats      the fight's clock: first delay and cadence per mechanic and difficulty
 *
 * Compass (NAVMESH): +x is north, +y is west; a bearing is measured from +x toward +y (radians, as WoW's orientation).
 */

#ifndef MOD_DUNGEON_BOSSES_SM_HEROD_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_HEROD_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace SmHerod
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    // The hard mode (Call to Arms, D11H) has its own slice, kSpellsCallToArms (213020-213059).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsHerod;

    enum HerodSpells : std::uint32_t
    {
        SPELL_HB_CYCLONE = kSpellSlice.first + 0,  // 212980 HB1 the cyclone on him from the yell to his return (look)
        SPELL_HB_OUT = kSpellSlice.first + 1,  // 212981 HB1a the out lane's hit (resolve copy, Physical)
        SPELL_HB_LAP = kSpellSlice.first + 2,  // 212982 HB1b his spin passing a player on the lap (Physical)
        SPELL_HB_BLADE = kSpellSlice.first + 3,  // 212983 HB1c a blade of light's hit (resolve copy, Holy)
        SPELL_HB_BLADE_LOOK = kSpellSlice.first + 4,  // 212984 HB1c the blade's flight (a missile to a point)
        SPELL_HB_HOME = kSpellSlice.first + 5,  // 212985 HB1d the home lane's hit (resolve copy, Physical)
        SPELL_HB_THROW = kSpellSlice.first + 6,  // 212986 HB2 Ravager's Throw's hit (resolve copy, Physical)
        SPELL_HB_THROW_LOOK = kSpellSlice.first + 7,  // 212987 HB2 the axe's flight (a missile to a point)
        SPELL_HB_AXE_SPIN = kSpellSlice.first + 8,  // 212988 HB2 the axe spinning on the floor (a stalker's aura)
        SPELL_HB_RETURN = kSpellSlice.first + 9,  // 212989 HB2a the return line's hit (resolve copy, Physical)
        SPELL_HB_WHIRL = kSpellSlice.first + 10,  // 212990 HB2w the whirling axe passing a player (Physical; heroic)
        SPELL_HB_CLEAVE = kSpellSlice.first + 11,  // 212991 HB3 the cleave on others (resolve copy, Physical)
        SPELL_HB_CLEAVE_TANK = kSpellSlice.first + 12,  // 212992 HB3 the cleave on the tank (kit percent script)
        SPELL_HB_FRENZY = kSpellSlice.first + 13,  // 212993 HB4 Frenzy (+30% attack speed, +20% Physical damage)
        // 212994-213019 spare
    };
    static_assert(SPELL_HB_FRENZY <= kSpellSlice.last, "Herod's spells must stay in his slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum HerodTags : std::uint32_t
    {
        TAG_HB_THROW        = 2,    // HB2 Ravager's Throw
        TAG_HB_CLEAVE       = 3,    // HB3 Champion's Cleave (others)
        TAG_HB_OUT          = 11,   // HB1a the out lane
        TAG_HB_LAP          = 12,   // HB1b the ledge band (telegraph) and his spin passing a player
        TAG_HB_BLADE        = 13,   // HB1c a blade of light
        TAG_HB_HOME         = 14,   // HB1d the home lane
        TAG_HB_SPIN         = 15,   // HB1 the circle following him while he spins (telegraph)
        TAG_HB_RETURN       = 21,   // HB2a the axe's return line
        TAG_HB_WHIRL        = 22,   // HB2w the whirling axe (heroic)
    };

    // creature_text groups of 3975. 0-4 are the stock rows (kept as the build spec's telegraphs); 5-8 are the hard
    // mode's (D11H's rev). The Scarlet Trainee's (6575) line 0 is stock.
    enum HerodTexts : std::uint8_t
    {
        SAY_AGGRO           = 0,    // yell (stock): "Ah - I've been waiting for a real challenge!"
        SAY_BLADES          = 1,    // yell (stock, every HB1): "Blades of light!"
        SAY_STRENGTH        = 2,    // yell (stock, HB4; HM2 the prayer): "Light, give me strength!"
        SAY_KILL            = 3,    // yell (stock): "Is that all?"
        EMOTE_ENRAGED       = 4,    // emote (stock, HB4): "%s becomes enraged!"
        SAY_TAUNT_ANSWERED  = 5,    // D11H: HM0 on heroic
        SAY_TAUNT_WORDS     = 6,    // D11H: HM0 on normal or in combat
        SAY_RISING          = 7,    // D11H: rising from HM2
        EMOTE_GARRISON      = 8,    // D11H: HM2 the door bursts open
        EMOTE_SEAL          = 9,    // HB0: Herod's Door slams shut (section 7 #22 A "with an emote"; F-2c)
    };
    inline constexpr std::uint8_t SAY_TRAINEE_AVENGE = 0;  // 6575 (stock): "The master has fallen! Avenge him, ..."
    // His kill line waits this long before it can come again (stock SmartAI 3975 row 7).
    inline constexpr std::uint32_t kKillLineCooldownMs = 5000;

    // The /taunt text emote (SharedDefines.h TEXT_EMOTE_TAUNT): HM0's trigger, routed by D11's ReceiveEmote to D11H.
    inline constexpr std::uint32_t kTextEmoteTaunt = 136;

    // Ravager in his hand: his stock equipment (creature_equip_template 3975 id 1, item 7612 "Monster - Axe, 2H
    // Special NPC (Herod)" [DB]). Gone from his hand while it is thrown (HB2).
    inline constexpr std::uint32_t kItemRavager = 7612;

    // ----------------------------------------------------------------------------------------------------------------
    // The Hall of Champions (section 3.8, NAVMESH "Herod" and navmesh/maps3.txt; [navmesh estimate] unless [DB])
    // ----------------------------------------------------------------------------------------------------------------

    // The pit: z 6.4 to 7.6, 543 sq yd, a rounded hexagon 25 x 30 yd round this centroid, equivalent radius 13.1. He
    // fights in its middle; the home lane ends here; portal P3 stands here after his death (the instance's).
    inline constexpr Point3 kPitCenter{ 1961.9f, -431.6f, 6.4f };
    inline constexpr float kPitRadiusYd = 13.1f;
    // The disc that is pit floor at every bearing (the pit's edge is 11.1 yd out at its nearest): the bots' spots
    // while the ledge band is up stay inside it.
    inline constexpr float kPitSafeRadiusYd = 11.f;
    inline constexpr float kPitZMin = 4.f;
    inline constexpr float kPitZMax = 9.5f;

    // The ledge ring round the pit, 12.3 to 25.5 yd out (6-12 yd wide, z 7.6 to 15.5; the pit is walkable only by two
    // north ramps), and the door spur (z 15.5 to 18.2, 5 yd wide from Herod's Door at x 1933.7 north to the landing).
    inline constexpr float kHallRadiusYd = 25.5f;
    inline constexpr float kHallZMin = 4.f;
    inline constexpr float kHallZMax = 21.f;
    // The spur's polygon starts 0.5 yd inside the door (S0's HerodArena() spur box, kHerodSpurMinX: R-2-ARM M-3), so
    // no bot spot is planned in the doorway or the cross hall.
    inline constexpr std::array<Vec2, 4> kDoorSpur{ { { 1934.2f, -429.f }, { 1944.f, -429.f }, { 1944.f, -434.2f },
        { 1934.2f, -434.2f } } };

    // HB1b the ledge band: from the pit's edge out past the walls and the door spur (Herod's Door is 28.2 yd out).
    // G2's herod-lap row drills it as this donut round the pit's center (inner 13).
    inline constexpr float kBandInnerYd = 13.f;
    inline constexpr float kBandOuterYd = 30.f;

    // HB1b the lap's route: the ledge's middle every 15 degrees from north (bearing 0) toward the west, so the spin
    // keeps to the ledge where it narrows over the south (16-17 yd out) and dips into the door spur at 180 degrees
    // (22 yd out: his 5 yd spin sweeps the spur to the door). 121 yd round (NAVMESH: about 121 yd).
    inline constexpr std::size_t kLapPointCount = 24;
    inline constexpr std::array<float, kLapPointCount> kLapRadiiYd{ {
        20.1f, 19.75f, 19.55f, 18.5f, 18.2f, 19.25f, 19.15f, 18.75f, 17.8f, 16.6f, 16.55f, 16.3f,
        22.f, 15.95f, 15.5f, 16.5f, 17.15f, 18.15f, 18.85f, 19.05f, 18.35f, 18.25f, 19.35f, 19.75f,
    } };
    inline constexpr float kLapStepDeg = 15.f;
    // The floor heights along the route are probed once at run time, each point in its own band (R-2-ARM m-3): the
    // ledge (NAVMESH z 7.6-15.5, open above) and the door spur's dip (z 15.5-18.2, a corridor through the wall with a
    // roof over it). A probe starts 2 yd over the band's top (under the spur's roof) and a hit outside the band (1 yd
    // slack) falls back to the band's estimate, so he never spins on the roof or under the spur's floor.
    struct LapZBand
    {
        float minZ;
        float maxZ;
        float estimateZ;

        constexpr float ProbeZ() const { return maxZ + 2.f; }
        constexpr float Pick(float hitZ) const
        {
            return (hitZ < minZ - 1.f || hitZ > maxZ + 1.f) ? estimateZ : hitZ;
        }
    };
    inline constexpr LapZBand kLedgeZBand{ 7.6f, 15.5f, 12.f };
    inline constexpr LapZBand kSpurZBand{ 15.5f, 18.2f, 17.5f };
    inline constexpr float kSpurMaxX = 1944.f;          // the spur's inner end (kDoorSpur), the ledge north of it

    // Section 7 #22 A (KT-SM SealedArena): the stragglers' entry spot just inside Herod's Door (on the spur, beside
    // the Lever at (1939.48, -428.0, 17.08) [DB]), facing north into the hall.
    inline constexpr Point3 kHallEntry{ 1941.f, -431.6f, 17.5f };
    inline constexpr float kHallEntryFacing = 0.f;

    // HB5 the trainees' stock spots (creature_summon_groups 3975 group 1 [DB]): the cross hall behind the door.
    inline constexpr std::uint32_t kTraineeSummonGroup = 1;
    inline constexpr std::uint32_t kTraineeCount = 20;
    inline constexpr float kTraineeSayRangeYd = 100.f;     // stock SmartAI 3975 row 9: the closest trainee speaks

    // The hard mode (D11H, section 7 #31 A): the garrison marches a scripted straight line from the door down the
    // south side: along the spur to the landing's lip, a short jump down into the pit, on to the pillar 3 yd short of
    // the pit's center. About 28 yd: 11 s at the drill pace of 2.5 yd/s. Squads march four abreast on the lane
    // offsets (yd across the line, + to the west). Heights are [navmesh estimate]; D11H probes the floor.
    inline constexpr std::array<Point3, 4> kGarrisonMarch{ {
        { 1935.5f, -431.6f, 18.2f },    // just inside the door
        { 1947.5f, -431.6f, 16.f },     // the landing's lip over the pit (the jump starts here)
        { 1951.5f, -431.6f, 6.6f },     // the pit floor below (the jump lands here)
        { 1958.9f, -431.6f, 6.4f },     // the pillar: 3 yd short of the pit's center
    } };
    inline constexpr std::size_t kGarrisonJumpFrom = 1;
    inline constexpr std::array<float, 4> kGarrisonLaneOffsetsYd{ { -1.8f, -0.6f, 0.6f, 1.8f } };
    inline constexpr float kGarrisonPaceYd = 2.5f;

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (Build spec "First, cooldown", normal / heroic; the hard mode's are D11H's overrides)
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    // Heroic every 32 s, not the spec's 25 s (F-2c, orchestrator default from the D11 Q1 tanking gap): a heroic spin
    // (~15.7 s) plus a throw with its whirl (~8.5 s) left ~1 s of a 25 s cycle for plain melee; at 32 s the tank gets
    // a ~7 s window each cycle (normal: ~9 s of 30 s). The hard mode's 0.88 ratio follows (28.2 s, ~4.7 s window).
    inline constexpr NH<Beat> kSpinBeat{ { 15000, 30000 }, { 15000, 32000 } };      // HB1
    inline constexpr NH<Beat> kThrowBeat{ { 6000, 30000 }, { 6000, 32000 } };       // HB2 (between the spins)
    inline constexpr Beat kCleaveBeat{ 3000, 6000 };                                 // HB3 (stock first: 3-7 s)
    // After a hold (a spin, a throw, the hard mode's prayer) the next cleave comes this long after he is free again:
    // the tank picks him up and turns him first.
    inline constexpr std::uint32_t kCleaveAfterHoldMs = 3000;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 37, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    // Every hit of his kit on a player who failed it (the lanes, the lap, the blades, the throw, the return, the
    // whirl, the cleave on others): 30% (heroic 45%; the hard mode's 60% is D11H's) and Weakened. The tank takes the
    // tank row's percent (rule 16), the cleave aside.
    inline constexpr NH<float> kHitPct{ 30.f, 45.f };

    // HB1 Blades of Light. The yell, the cyclone on him (a 5 yd spin), the ledge band marked from the yell; the out
    // lane (10 yd wide, 2.5 s marker) to a random point of the lap; the lap round the ledge in a random direction at 10
    // yd/s (heroic 12); then the home lane (10 yd, 1.5 s) to the pit's center. He dashes each lane once its marker
    // resolves ("instant: he travels it"), faster than the lap.
    inline constexpr std::uint32_t kOutWarnMs = 2500;
    inline constexpr std::uint32_t kHomeWarnMs = 1500;
    inline constexpr float kLaneWidthYd = 10.f;
    inline constexpr float kSpinRadiusYd = 5.f;
    inline constexpr NH<float> kLapSpeedYd{ 10.f, 12.f };
    inline constexpr float kDashSpeedYd = 25.f;
    // The spin passing a player: checked this often; a player within the spin (2D, and this close in height) is hit
    // once per lap.
    inline constexpr std::uint32_t kLapScanMs = 250;
    inline constexpr float kSpinZBandYd = 5.f;
    // A spline that never reports its end is cut this long after its planned end.
    inline constexpr std::uint32_t kMoveGraceMs = 2000;

    // HB1c blades of light: a lane 4 yd wide from him across the pit to its far edge toward a random player (the tank
    // included), a 1.5 s marker, Holy. Normal one every 2 s (after Frenzy every 1.5 s); heroic one every 1.5 s (after
    // Frenzy two at once every 1 s). The first one interval into the lap, the last one resolving before the lap ends:
    // 5 a lap (7 after Frenzy) on normal.
    inline constexpr std::uint32_t kBladeWarnMs = 1500;
    inline constexpr float kBladeWidthYd = 4.f;
    inline constexpr float kBladeMinYd = 6.f;
    inline constexpr float kBladeMaxYd = 40.f;
    inline constexpr float kBladePastTargetYd = 4.f;       // a target off the pit: the lane ends this far past them

    struct BladePlan
    {
        std::uint32_t everyMs;
        std::uint32_t count;            // blades at once (each at a different player)
    };

    constexpr BladePlan BladePlanFor(bool heroic, bool frenzied)
    {
        if (heroic)
            return frenzied ? BladePlan{ 1000, 2 } : BladePlan{ 1500, 1 };
        return frenzied ? BladePlan{ 1500, 1 } : BladePlan{ 2000, 1 };
    }

    // HB2 Ravager's Throw: a 5 yd circle at a random player's spot (the tank included), a 2 s marker. Normal: the axe
    // spins where it lands while its way home shows as a 3 yd line to his hand (1.5 s), then flies home along it.
    // Heroic (HB2w): it first whirls on its own toward a random player for 5 s (a 4 yd spin at 5 yd/s, its path
    // shown 1.5 s ahead; once per player per whirl), then the line home. While the axe is out he punches the tank and
    // never cleaves.
    inline constexpr std::uint32_t kThrowWarnMs = 2000;
    inline constexpr float kThrowRadiusYd = 5.f;
    inline constexpr std::uint32_t kReturnWarnMs = 1500;
    inline constexpr float kReturnWidthYd = 3.f;
    inline constexpr NH<std::uint32_t> kWhirlMs{ 0, 5000 };
    inline constexpr float kWhirlSpeedYd = 5.f;
    inline constexpr float kWhirlRadiusYd = 4.f;
    inline constexpr std::uint32_t kWhirlAheadMs = 1500;
    inline constexpr float kWhirlPathWidthYd = 8.f;
    // The whirl keeps to the hall: its path ends inside this disc round the pit's center.
    inline constexpr float kWhirlRoomYd = 22.f;
    // The axe's flight home (the stalker's look) before it is in his hand again.
    inline constexpr std::uint32_t kAxeFlightMs = 600;

    // HB3 Champion's Cleave: every 6 s while he holds a weapon in melee, a 90 degree cone 8 yd ahead (a 1.5 s marker,
    // the Armory's cleave): the tank takes 15% (heroic 25%) of the tank row, anyone else inside 30% (45%) and Weakened.
    inline constexpr std::uint32_t kCleaveWarnMs = 1500;
    inline constexpr float kCleaveAngleDeg = 90.f;
    inline constexpr float kCleaveLengthYd = 8.f;
    inline constexpr NH<float> kCleaveTankPct{ 15.f, 25.f };

    // HB4 Frenzy, once at 50% (the hard mode replaces it with HM2): +30% attack speed and +20% Physical damage for the
    // rest of the fight; the blades quicken (BladePlanFor).
    inline constexpr float kFrenzyAtPct = 50.f;
    inline constexpr float kFrenzyHastePct = 30.f;
    inline constexpr float kFrenzyDamagePct = 20.f;

    // HB5 the trainees: 20 x 400 on normal (level 30 mage, HealthModifier 0.5427 on the base 737), 20 x 2.5k on
    // heroic (WP-H's override).
    inline constexpr NH<std::uint32_t> kTraineeHealth{ 400, 2500 };
    inline constexpr std::uint32_t kTraineeBaseHealthL30Mage = 737;

    // Health (section 3.6): 66k normal (49.401 on the level 37 warrior base 1,336), 320k heroic (WP-H), the hard mode
    // 400k from the pull (D11H).
    inline constexpr NH<std::uint32_t> kHerodHealth{ 66000, 320000 };
    inline constexpr std::uint32_t kHerodBaseHealthL37Warrior = 1336;

    // ----------------------------------------------------------------------------------------------------------------
    // The lap
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kDegToRad = DungeonKit::kPi / 180.f;

    // Lap point `i` (0 = north, then every 15 degrees toward the west).
    inline Vec2 LapPoint(std::size_t i)
    {
        i %= kLapPointCount;
        float const bearing = static_cast<float>(i) * kLapStepDeg * kDegToRad;
        float const r = kLapRadiiYd[i];
        return Vec2{ kPitCenter.x + r * std::cos(bearing), kPitCenter.y + r * std::sin(bearing) };
    }

    // The floor band of lap point `i`: the spur's for the dip into the door spur, else the ledge's.
    inline LapZBand LapZBandOf(std::size_t i)
    {
        Vec2 const p = LapPoint(i);
        bool const spur = p.x <= kSpurMaxX && p.y <= kDoorSpur[0].y && p.y >= kDoorSpur[2].y;
        return spur ? kSpurZBand : kLedgeZBand;
    }

    // The whole lap's length (yd).
    inline float LapLengthYd()
    {
        float total = 0.f;
        for (std::size_t i = 0; i < kLapPointCount; ++i)
            total += DungeonKit::Distance(LapPoint(i), LapPoint(i + 1));
        return total;
    }

    // Milliseconds to cover `yd` at `speedYd` yd/s.
    inline std::uint32_t TravelMs(float yd, float speedYd)
    {
        return speedYd > 0.f ? static_cast<std::uint32_t>(std::lround(yd / speedYd * 1000.f)) : 0u;
    }

    // The lap's time at `speedYd` yd/s.
    inline std::uint32_t LapMs(float speedYd)
    {
        return TravelMs(LapLengthYd(), speedYd);
    }

    // The lap point nearest `p`.
    inline std::size_t NearestLapIndex(Vec2 p)
    {
        std::size_t best = 0;
        float bestYd = DungeonKit::Distance(p, LapPoint(0));
        for (std::size_t i = 1; i < kLapPointCount; ++i)
        {
            float const d = DungeonKit::Distance(p, LapPoint(i));
            if (d < bestYd)
            {
                best = i;
                bestYd = d;
            }
        }
        return best;
    }

    // The route of one lap from point `start`: every point once in the given direction, then `start` again
    // (kLapPointCount + 1 points). `clockwise` as seen from above with north up (+x up, +y to the left): toward the
    // east first, the bearing falling.
    inline std::vector<Vec2> LapRoute(std::size_t start, bool clockwise)
    {
        std::vector<Vec2> route;
        route.reserve(kLapPointCount + 1);
        for (std::size_t k = 0; k <= kLapPointCount; ++k)
        {
            std::size_t const step = k % kLapPointCount;
            std::size_t const i = clockwise ? (start + kLapPointCount - step) % kLapPointCount
                : (start + step) % kLapPointCount;
            route.push_back(LapPoint(i));
        }
        return route;
    }

    // HB1c: the blade waves registered during a lap of `lapMs`: the first one interval into it, then every `everyMs`,
    // each resolving (registration + kBladeWarnMs) no later than the lap's end.
    constexpr std::uint32_t BladeWaves(std::uint32_t lapMs, std::uint32_t everyMs)
    {
        if (!everyMs)
            return 0;
        std::uint32_t n = 0;
        for (std::uint32_t at = everyMs; at + kBladeWarnMs <= lapMs; at += everyMs)
            ++n;
        return n;
    }

    // Distance along a ray from `origin` (anywhere) at `facing` to where it leaves the circle (center, radius) on its
    // far side; nullopt when the ray misses the circle or the circle is behind it.
    inline std::optional<float> RayFarCircleExit(Vec2 center, float radius, Vec2 origin, float facing)
    {
        float const dx = std::cos(facing);
        float const dy = std::sin(facing);
        float const ox = origin.x - center.x;
        float const oy = origin.y - center.y;
        float const b = ox * dx + oy * dy;
        float const c = ox * ox + oy * oy - radius * radius;
        float const disc = b * b - c;
        if (disc < 0.f)
            return std::nullopt;
        float const far = -b + std::sqrt(disc);
        if (far <= 0.f)
            return std::nullopt;
        return far;
    }

    // HB1c a blade's lane from `from` (Herod on the lap) toward `target`: across the pit to its far edge; a target the
    // ray never takes across the pit gets a lane kBladePastTargetYd past them. Held to [kBladeMinYd, kBladeMaxYd].
    inline float BladeLengthYd(Vec2 from, Vec2 target)
    {
        float const facing = DungeonKit::BearingTo(from, target);
        float length = DungeonKit::Distance(from, target) + kBladePastTargetYd;
        if (std::optional<float> const exit = RayFarCircleExit({ kPitCenter.x, kPitCenter.y }, kPitRadiusYd, from,
            facing))
            length = std::max(*exit, DungeonKit::Distance(from, target));
        return std::clamp(length, kBladeMinYd, kBladeMaxYd);
    }

    // HB2w the whirling axe's path end: from `from` toward `target`, `lengthYd` long, cut where it would leave the
    // disc of kWhirlRoomYd round the pit's center (a landing spot outside that disc whirls its full length).
    inline Vec2 WhirlEnd(Vec2 from, Vec2 target, float lengthYd, float roomYd = kWhirlRoomYd)
    {
        Vec2 const center{ kPitCenter.x, kPitCenter.y };
        float const facing = DungeonKit::Distance(from, target) < 0.01f ? DungeonKit::BearingTo(from, center)
            : DungeonKit::BearingTo(from, target);
        float length = lengthYd;
        if (DungeonKit::Distance(from, center) <= roomYd)
            if (std::optional<float> const exit = RayFarCircleExit(center, roomYd, from, facing))
                length = std::min(length, *exit);
        return DungeonKit::Advance(from, facing, length);
    }

    // HB2w the whirl's room (R-2-ARM m-4): an axe that landed in the pit whirls inside the pit's disc (it never slides
    // up the steps onto the ledge, where its hits would miss the players under its telegraph); one that landed on the
    // ledge keeps kWhirlRoomYd. A pit landing past the disc (a corner of the hexagon) gets a disc 0.5 yd past its spot
    // (aimed outward it barely moves).
    inline bool LandedInPit(float spotZ)
    {
        return spotZ <= kPitZMax;
    }

    inline float WhirlRoomYd(Vec2 from, bool landedInPit)
    {
        if (!landedInPit)
            return kWhirlRoomYd;
        return std::max(kPitRadiusYd, DungeonKit::Distance(from, { kPitCenter.x, kPitCenter.y }) + 0.5f);
    }

    // HB2w the whirling axe's height at `at` on its path: from the landing's to the end's, along the path (a ledge
    // throw whirling down into the pit hits the pit players under its telegraph).
    inline float WhirlZAt(Vec2 from, float fromZ, Vec2 end, float endZ, Vec2 at)
    {
        float const length = DungeonKit::Distance(from, end);
        if (length < 0.01f)
            return fromZ;
        float const t = std::clamp(DungeonKit::Distance(from, at) / length, 0.f, 1.f);
        return fromZ + (endZ - fromZ) * t;
    }

    // The probed floor at the whirl's end, when it is a hall height; else the landing's (no hit, a roof).
    inline float WhirlEndZ(float probedZ, float spotZ)
    {
        return (probedZ < kHallZMin || probedZ > kHallZMax) ? spotZ : probedZ;
    }

    // HB2w where the whirling axe is `elapsedMs` into its whirl: along the straight path from `from` to `end` at
    // `speedYd` yd/s, holding at `end` once there.
    inline Vec2 WhirlPosAt(Vec2 from, Vec2 end, float speedYd, std::uint64_t elapsedMs)
    {
        float const length = DungeonKit::Distance(from, end);
        if (length < 0.01f)
            return from;
        float const along = std::min(length, speedYd * static_cast<float>(elapsedMs) / 1000.f);
        return Vec2{ from.x + (end.x - from.x) * along / length, from.y + (end.y - from.y) * along / length };
    }

    // The pit floor as an arena (the hard mode's beams clip to it: KT-SM TurningBeams `clip`).
    inline DungeonKit::Arena PitArena()
    {
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Circle({ kPitCenter.x, kPitCenter.y }, kPitRadiusYd,
            kPitZMin, kPitZMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rules
    // ----------------------------------------------------------------------------------------------------------------

    // HB3: he cleaves only with a weapon in hand, in melee: never while he spins, while the axe is out or while the
    // hard mode holds his kit (the prayer).
    constexpr bool CleaveAllowed(bool spinning, bool axeOut, bool held)
    {
        return !spinning && !axeOut && !held;
    }

    // HB1 / HB2: spins and throws never overlap (a due one waits for the other's end); neither runs while the kit is
    // held; the throw also waits for the hard mode's leave (its second half plants the axe).
    constexpr bool SpinAllowed(bool axeOut, bool held)
    {
        return !axeOut && !held;
    }

    constexpr bool ThrowAllowed(bool spinning, bool held, bool hardModeAllows)
    {
        return !spinning && !held && hardModeAllows;
    }

    // HB4 / HM2: the 50% point (or the hard mode's) is acted on once he is home and holds his axe.
    constexpr bool ThresholdReady(float healthPct, float atPct, bool spinning, bool axeOut)
    {
        return healthPct <= atPct && !spinning && !axeOut;
    }

    // HB4 / HM2: the point is crossed and not acted on yet. While it is, no new spin or throw starts (the one running
    // finishes), so a spin ending into an overdue throw (or a throw into an overdue spin) can never starve it
    // (R-2-ARM M-2: on the hard mode's back-to-back first half the prayer never fired).
    constexpr bool ThresholdPending(float healthPct, float atPct, bool done)
    {
        return !done && healthPct <= atPct;
    }

    constexpr bool BeatMayStart(bool thresholdPending)
    {
        return !thresholdPending;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The AI's own clock
    // ----------------------------------------------------------------------------------------------------------------

    // A repeating beat on the AI's own ms clock (start to start); a beat that cannot fire yet stays due.
    class BeatClock
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t inMs)
        {
            _on = true;
            _dueMs = nowMs + inMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time, never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
