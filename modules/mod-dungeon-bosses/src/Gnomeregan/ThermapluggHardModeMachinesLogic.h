/*
 * mod-dungeon-bosses, Gnomeregan D6Hb: the Whole Workshop, part b (Mekgineer Thermaplugg's heroic hard mode), the pure,
 * host-testable part (no engine headers) of the package SchematicsB (thermaplugg_hard_mode_machines.cpp): the spell
 * ids of kSpellsHardModeB (214580-214619), the registry tags (G1's drill row 10, LESSONS A.3 #4), the text groups
 * (7800 groups 10 and 11), every number of the three schematics (`namespace Tune`, handoff section 3.5 rule 24) and
 * the rules a host test pins: the load thresholds (MT15, ruling 45), the console's load line, the Voltage rules on
 * him (MT21, MT22), the lights (MT23), and the fist's frame from a Gnome Face, its shapes, numerals, timing and roll
 * (MT24, rulings 68 and 69, section 7 #33 A). Build spec: SP 1738-1864 "Hard mode: the Whole Workshop", rulings
 * 43-53, 68, 69; handoff sections 3.5 row D6Hb, 3.6, 3.7, 3.8 (the room), 3.9 row 10, 7 #33 A, #35 A, 10. Tested by
 * tests/gnomer_hard_mode_machines_test.cpp. Health is GnomereganRework.h Health (the Whole Workshop's 800,000 is D6's
 * to set): never restated here.
 *
 * The machines are D3's, D4's and D5's (GnomereganMachines.h); this header only gives them the hard mode's numbers.
 * Their pure halves (ElectrocutionerLogic.h VoltageClock, MobileAlertSystemLogic.h FloorTag, CrowdPummelerLogic.h
 * ShapeDef and KitTiming) are reused, never restated. No stock code is mirrored.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_HARD_MODE_MACHINES_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_THERMAPLUGG_HARD_MODE_MACHINES_LOGIC_H

#include "CrowdPummelerLogic.h"
#include "DungeonKitComboLogic.h"
#include "DungeonKitMath.h"
#include "ElectrocutionerLogic.h"
#include "GnomereganRework.h"
#include "MobileAlertSystemLogic.h"
#include "ThermapluggLogic.h"
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace GnomerSchematics
{
    using DungeonKit::Vec2;
    using GnomereganRework::kWarningFloorMs;
    using Shape = GnomerPummeler::Shape;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsHardModeB;

    // Declared in apps/dbc-tools source/npcs/gnomeregan/thermaplugg_hard_mode_machines.py (same ids, same order;
    // lib/test_gnomeregan_hard_mode_machines.py pins each name to its offset). The machines bring their own looks and
    // hits too (D3's VoltageMeter: Electrocutioner's Electric Justice hit 214383, his brighter crackle 214381 and the
    // blast look 214384 on blast stalkers 301132; D4's lights: the light stalker 301113 and the BM cones).
    enum SchematicsSpells : std::uint32_t
    {
        SPELL_HMB_VOLTAGE       = kSpellSlice.first + 0,    // MT21 the meter on him: stacks, +3% damage done a stack
        SPELL_HMB_JUSTICE_BAR   = kSpellSlice.first + 1,    // MT22 the 4 s bar: Physical, InterruptFlags 0
        SPELL_HMB_SPOTTED       = kSpellSlice.first + 2,    // MT23 the Spotted hit: resolve copy (Arcane)
        SPELL_HMB_SPOTTED_BEAM  = kSpellSlice.first + 3,    // MT23 the red beam from him to the Spotted player (a look)
        SPELL_HMB_FIST_HIT      = kSpellSlice.first + 4,    // MT24 every punch: resolve copy (Physical)
        SPELL_HMB_FIST_WIND_UP  = kSpellSlice.first + 5,    // MT24 the fist's wind-up (the punch pose, a bar)
        SPELL_HMB_FACE_LIGHT    = kSpellSlice.first + 6,    // MT24 the Gnome Face lights up (a look on its stalker)
        // kSpellSlice.first + 7 .. kSpellSlice.last (214587-214619): spare
    };
    std::uint32_t constexpr kSpellCount = 7;
    static_assert(kSpellSlice.Contains(SPELL_HMB_VOLTAGE) && kSpellSlice.Contains(SPELL_HMB_FACE_LIGHT),
        "D6Hb's spells sit in the slice");

    // Registry tags: G1's gnomeregan-shapes drill row 10 (BM MechanicDrill.h kGnTagHm*, 80-85; reported, not gated;
    // change both together, LESSONS A.3 #4). 80 (the hard mode's mines) and 81 (the Wandering Puddles) are the drill's
    // names for D6's and D6Ha's units: this package registers nothing under them. 85 is the Justice donut, live and in
    // the drill (JusticeSpec::tag; the machine's default is Electrocutioner's 40).
    enum SchematicsTags : std::uint32_t
    {
        TAG_HMB_MINES           = 80,   // drill only (D6's mines live as TAG_MT_MINE 75)
        TAG_HMB_PUDDLES         = 81,   // drill only (D6Ha's Wandering Puddles)
        TAG_HMB_LIGHTS          = 82,   // MT23: the two lit cones and every Spotted hit
        TAG_HMB_LIGHTS_FLOOR    = 83,   // MT23: the lights' look ahead (D4's FloorTag: the light's tag + 1)
        TAG_HMB_FIST            = 84,   // MT24: the fist's punches (every shape)
        TAG_HMB_JUSTICE         = 85,   // MT22: the Justice donut (JusticeSpec::tag)
    };
    static_assert(GnomerAlert::FloorTag(TAG_HMB_LIGHTS) == TAG_HMB_LIGHTS_FLOOR,
        "the look ahead is the light's tag + 1 (MobileAlertSystemLogic.h FloorTag)");
    static_assert(TAG_HMB_MINES == GnomerThermaplugg::kFirstPackageTag, "the packages' tags start at 80");

    struct DrillTag
    {
        std::uint32_t tag;
        char const* drillName;
    };
    // The tag table the drill shares (lib/test_gnomeregan_hard_mode_machines.py diffs it against MechanicDrill.h when
    // BM_SRC is set). 83 has no name of its own in the drill (LightsFloorTag(82)).
    inline constexpr std::array<DrillTag, 5> kDrillTags{ {
        { TAG_HMB_MINES, "kGnTagHmMines" },
        { TAG_HMB_PUDDLES, "kGnTagHmPuddles" },
        { TAG_HMB_LIGHTS, "kGnTagHmLights" },
        { TAG_HMB_FIST, "kGnTagHmFist" },
        { TAG_HMB_JUSTICE, "kGnTagHmJustice" },
    } };

    // creature_text 7800 (D6's ThermapluggLogic.h: groups 9 to 11 are the packages'; 9 is D6Ha's yell). Type 41
    // (rule 2), rev_thermaplugg_hard_mode_machines_gnomeregan.sql. The machines say them (the Justice's and the
    // combination's call emote) through their owner's Talk.
    enum SchematicsTexts : std::uint8_t
    {
        EMOTE_HMB_JUSTICE   = 10,   // SP line 10: "%s overloads the room. Get to him!" (MT22)
        EMOTE_HMB_FIST      = 11,   // SP line 11: "A giant fist winds up inside a Gnome Face!" (MT24)
    };
    static_assert(EMOTE_HMB_JUSTICE > GnomerThermaplugg::kFirstPackageTextGroup
        && EMOTE_HMB_FIST > EMOTE_HMB_JUSTICE, "D6Hb's groups are 10 and 11 (9 is D6Ha's)");

    // The three schematics of this package (MT15, ruling 45: Electrocutioner at 60%, the Alert System at 45%, Crowd
    // Pummeler at 30%; D6Ha loads Techbot at 90% and Viscous Fallout at 75%). Each stays to the end of the fight.
    enum class Schematic : std::uint8_t
    {
        Electrocutioner = 0,
        AlertSystem = 1,
        Pummeler = 2,
    };
    std::size_t constexpr kSchematicCount = 3;

    inline constexpr std::array<char const*, kSchematicCount> kSchematicKeys{ { "electro", "alert", "pummeler" } };
    // The console's names (SP: "Loading schematic: TECHBOT" and so on).
    inline constexpr std::array<char const*, kSchematicCount> kSchematicNames{ {
        "ELECTROCUTIONER 6000", "THE MOBILE ALERT SYSTEM", "CROWD PUMMELER 9-60" } };

    constexpr std::size_t SchematicIndex(Schematic s)
    {
        return static_cast<std::size_t>(s);
    }

    // `.dbtest gnomer schematics load <key>`.
    inline std::optional<Schematic> SchematicOfKey(std::string const& key)
    {
        for (std::size_t i = 0; i < kSchematicCount; ++i)
            if (key == kSchematicKeys[i])
                return static_cast<Schematic>(i);
        return std::nullopt;
    }

    // MT24: three punches from four shapes, all read from the face (ruling 68). The lane is Crowd Pummeler's only.
    std::uint32_t constexpr kFistShapeCount = 4;
    inline constexpr std::array<Shape, kFistShapeCount> kFistShapes{ {
        Shape::LeftHalf, Shape::RightHalf, Shape::Near, Shape::Far } };
    // The log and the combat log's names, by PunchShape (GnomereganMachines.h; the lane never comes).
    inline constexpr std::array<char const*, GnomerPummeler::kShapeCount> kFistShapeNames{ {
        "left", "right", "near", "far", "lane" } };

    // V's numeral quads (source/npcs/gnomeregan/_visuals.py MT_NUMERAL_1..3, CDI 90853-90855; the DT test pins them).
    inline constexpr std::array<std::uint32_t, 3> kNumeralDisplays{ { 90853, 90854, 90855 } };
    // Emotes.dbc 35: AttackUnarmed (anim 16), the one punch the Pummeler's model has (V: CP_PUNCH_EMOTE_ANIM).
    std::uint32_t constexpr kFistEmote = 35;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP 1738-1864 and the MT21-MT24 rows; rulings 45, 49, 68, 69; section 7 #33 A, #37 A: the guesses as
    // written; rule 24: every percent a named constant, every warning at least the 1.5 s floor)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // MT15: the load thresholds of this package, highest first (D6 calls OnHealthPct once each).
        inline constexpr std::array<float, kSchematicCount> kLoadPct{ { 60.f, 45.f, 30.f } };
        // The console's load line reaches the whole room (SP: "the console shows ..."; s7 #35 A: the bowl).
        float constexpr kConsoleLineYd = 120.f;

        // MT21 Voltage: +1 stack (1,000 volts) every 5 s and +1 for every player a mine or a bomb hits; 3% to all his
        // damage a stack, never resets (heroic Electrocutioner's rules). His melee and Knock Away through the aura's
        // damage done; D6's percent hits through DamageFactor; this package's own hits times the same factor.
        std::uint32_t constexpr kVoltageTickMs = 5000;
        std::uint32_t constexpr kVoltsPerPlayerHit = 1;
        float constexpr kVoltagePctPerStack = 3.f;
        // Which blasts charge him (SP: "a mine or bomb"): walking bombs and mines, and (switches) the Sticky Bomb and
        // The Big One.
        bool constexpr kStickyCharges = true;
        bool constexpr kBigOneCharges = true;

        // MT22 Electric Justice: at every 6,000 volts a 4 s bar (Physical, not interruptible), emote line 10, the
        // room outside 8 yd of him (the donut only, no circle in turn), 75% of the reference row times the factor;
        // no Weakened (Penalty: none). Ruling 49: with the dose it can kill (a named exception).
        std::uint32_t constexpr kJusticeEvery = 6;
        std::uint32_t constexpr kJusticeCastMs = 4000;
        float constexpr kJusticeSafeYd = 8.f;
        float constexpr kJusticePct = 75.f;

        // MT23 Searchlights: two 30 degree cones from him to the wall, opposite each other, 12 degrees a second
        // (guess: the Alert System's heroic speed), always lit after a dim opening; Spotted: 50% of the reference row
        // (times the factor) and a closed face opens; no Weakened (Penalty: none). One Spotted per player per 3 s
        // (D4's latch, KT-G Q2). The range reaches the room's farthest floor from anywhere in the bowl.
        std::uint32_t constexpr kLightsCones = 2;
        float constexpr kLightsConeDeg = 30.f;
        float constexpr kLightsDegPerSec = 12.f;
        float constexpr kLightsRangeYd = 110.f;
        float constexpr kLightsZBandYd = 6.f;
        std::uint32_t constexpr kLightsDarkMs = 3000;        // the dim opening (the Alert System's heroic 3 s)
        std::uint32_t constexpr kLightsLatchMs = 3000;
        int constexpr kLightsDirection = -1;                 // clockwise first (D4's default)
        // Light 0 starts this far from his facing (90: across his tank's line, so the opening lights no tank).
        float constexpr kLightsStartOffsetDeg = 90.f;
        // SP's MT23 row names no speed-up and no reversal (the Alert System's heroic has both). Switches, off.
        float constexpr kLightsSpeedUpPct = 0.f;
        std::uint32_t constexpr kLightsReverseMinMs = 0;     // 0: never reverses
        std::uint32_t constexpr kLightsReverseMaxMs = 0;
        std::uint32_t constexpr kLightsReverseStopMs = 2000;
        float constexpr kSpottedPct = 50.f;
        bool constexpr kSpottedWeakened = false;
        bool constexpr kSpottedOpensFace = true;

        // MT24 Fist Combination (rulings 68, 69): every 18 s from a random Gnome Face, open or shut; the face lights
        // and the fist winds up 4 s before the first punch; three punches 2.5 s apart; all three shapes drawn at once,
        // numbered; each shape filled for its last second (its live marker, inside the 4 s: punch 1 still lands at
        // 4 s); 60% each (guess, Pummeler's heroic) times the factor; Weakened.
        std::uint32_t constexpr kFistFirstMs = 3000;         // (guess) after the 30% load
        std::uint32_t constexpr kFistEveryMs = 18000;        // start to start (SP: "every 18 sec")
        std::uint32_t constexpr kFistWarnMs = 4000;          // ruling 69: the wind-up to the first punch
        std::uint32_t constexpr kFistLiveMs = 1000;          // the fill before each strike (guess)
        std::uint32_t constexpr kFistWindUpMs = kFistWarnMs - kFistLiveMs;     // the machine's windUpMs
        std::uint32_t constexpr kFistApartMs = 2500;         // ruling 69
        std::uint32_t constexpr kFistPunches = 3;
        float constexpr kFistPct = 60.f;
        bool constexpr kFistWeakened = true;
        // The frame from the face (section 7 #33 A): near = within 50 yd of the face, far = past it; the halves split
        // on the face-to-center line. The halves' reach and the far donut's outer edge cover the whole room from every
        // face (host-tested); the halves start 5 yd behind the face (D5's kBehindYd).
        float constexpr kFistNearYd = 50.f;
        float constexpr kFistFarOuterYd = 110.f;
        float constexpr kFistHalfReachYd = 110.f;
        float constexpr kFistBehindYd = 5.f;
        // The machine (CrowdPummelerMachine.cpp ParamsOf) passes no behindYd: it builds with D5's own.
        static_assert(kFistBehindYd == GnomerPummeler::Tune::kBehindYd, "the machine's halves start where ours do");
        // The fist (V: the Pummeler's display 6774, no hands-only model) stands this far behind the face's plane,
        // facing the center, so only its front shows through the face (V gap 12). Its scale is the template's 5.
        float constexpr kFistBodyBehindYd = 4.f;
        std::uint32_t constexpr kFistLingerMs = 1500;        // after the last punch, then it goes
        std::uint32_t constexpr kFaceLightMs = 10000;        // the face's glow: the wind-up and the three punches
        // Numerals (V: numeral_scale(4) = 2.5, a 4 yd glyph) on each shape's floor, this far from the room's center
        // on its own side (the four label spots of a face are inside the bowl, each in its own shape only).
        float constexpr kNumeralScale = 2.5f;
        float constexpr kNumeralOffsetYd = 19.f;

        static_assert(kLoadPct[0] > kLoadPct[1] && kLoadPct[1] > kLoadPct[2], "MT15: highest first");
        static_assert(kJusticeCastMs >= kWarningFloorMs, "Electric Justice's bar is no less than 1.5 s");
        static_assert(kLightsDarkMs >= kWarningFloorMs, "the lights' dim opening is no less than 1.5 s");
        static_assert(kFistWarnMs >= kWarningFloorMs, "the fist winds up for no less than 1.5 s");
        static_assert(kFistLiveMs < kFistWarnMs, "the live marker sits inside the wind-up");
        static_assert(kFistApartMs >= kWarningFloorMs, "punches no closer than the warning floor");
        static_assert(kFistLiveMs <= kFistApartMs, "a live marker never starts before the punch ahead lands");
        // RB-29: the cadence is at least the warning plus 0.5 s, and a combination ends before the next is called.
        static_assert(kFistEveryMs >= kFistWarnMs + (kFistPunches - 1) * kFistApartMs + kFistLingerMs + 500,
            "a combination ends before the next one");
        static_assert(kFaceLightMs >= kFistWarnMs + (kFistPunches - 1) * kFistApartMs, "the face glows to the end");
        static_assert(kFistFarOuterYd > kFistNearYd, "the far donut lies past the near circle");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT15: the loads
    // ----------------------------------------------------------------------------------------------------------------

    // The thresholds this package hands D6 (ThermapluggHardMode::HealthThresholds).
    inline std::vector<float> Thresholds()
    {
        return std::vector<float>(Tune::kLoadPct.begin(), Tune::kLoadPct.end());
    }

    // The schematic a threshold loads (nullopt: not one of this package's).
    constexpr std::optional<Schematic> SchematicAt(float pct)
    {
        for (std::size_t i = 0; i < kSchematicCount; ++i)
            if (pct == Tune::kLoadPct[i])
                return static_cast<Schematic>(i);
        return std::nullopt;
    }

    // The console's line (SP MT15: "Loading schematic: TECHBOT" and so on).
    inline std::string LoadLine(Schematic s)
    {
        return std::string("Loading schematic: ") + kSchematicNames[SchematicIndex(s)];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT21, MT22: Voltage on him (the VoltageMeter machine's rules: heroic Electrocutioner's, the donut only)
    // ----------------------------------------------------------------------------------------------------------------
    inline GnomerElectro::VoltageRules VoltageRules()
    {
        GnomerElectro::VoltageRules r;
        r.tickMs = Tune::kVoltageTickMs;
        r.every = Tune::kJusticeEvery;
        r.resetAfterJustice = false;
        r.pauseAfterMs = 0;
        r.minGapMs = 0;
        return r;
    }

    // +1,000 volts for every player a blast reached (MT21).
    constexpr std::uint32_t VoltsForHit(std::size_t playersHit)
    {
        return static_cast<std::uint32_t>(playersHit) * Tune::kVoltsPerPlayerHit;
    }

    // Does a blast of this source charge him? `hitSource` is ThermapluggFight.h HitSource's value: 0 a walking bomb,
    // 1 a mine, 2 the Sticky Bomb, 3 The Big One.
    constexpr bool SourceCharges(std::uint8_t hitSource)
    {
        switch (hitSource)
        {
            case 0:
            case 1:
                return true;
            case 2:
                return Tune::kStickyCharges;
            case 3:
                return Tune::kBigOneCharges;
            default:
                return false;
        }
    }

    // A percent of his own (Spotted, the fist) times the Voltage factor; never below 0.
    constexpr float Scaled(float pct, float factor)
    {
        return pct * (factor > 0.f ? factor : 0.f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT23: the lights
    // ----------------------------------------------------------------------------------------------------------------

    // Light 0's first bearing from his facing (radians, [0, 2pi)).
    inline float LightsStartBearing(float facing)
    {
        float o = std::fmod(facing + Tune::kLightsStartOffsetDeg * DungeonKit::kPi / 180.f, DungeonKit::kTwoPi);
        if (o < 0.f)
            o += DungeonKit::kTwoPi;
        return o;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MT24: the fist (a frame from a Gnome Face, ruling 68; section 7 #33 A)
    // ----------------------------------------------------------------------------------------------------------------

    // The frame of face `face` (0 to 5 = face 01 to 06): the face's DB spot, facing the room's center (the halves
    // split on that line; near and far measured from the face).
    inline DungeonKit::ComboFrame FistFrame(std::uint32_t face)
    {
        GnomereganRework::Point3 const& f = GnomereganRework::kFaceSpots[face % GnomereganRework::kFaceCount];
        return DungeonKit::FrameFacing(f.XY(), f.z, GnomereganRework::kRoomCenter.XY());
    }

    // The machine's frame parameters (GnomereganMachines.h ComboFrame; D5's pure FrameParams). The lane is unused.
    inline GnomerPummeler::FrameParams FistParams()
    {
        GnomerPummeler::FrameParams p;
        p.halfReachYd = Tune::kFistHalfReachYd;
        p.nearRadiusYd = Tune::kFistNearYd;
        p.farOuterYd = Tune::kFistFarOuterYd;
        p.behindYd = Tune::kFistBehindYd;
        return p;
    }

    // A shape of the fist from `face`, as the machine places it (D5's ShapeDef on this frame).
    inline DungeonKit::PlacedShape FistShape(std::uint32_t face, Shape shape)
    {
        return GnomerPummeler::PlaceShape(FistFrame(face), shape, FistParams());
    }

    // Where a shape's numeral stands: on the bowl's floor, kNumeralOffsetYd from the center on the shape's own side
    // (the near side toward the face, the far side past the center, the halves across the line).
    inline Vec2 FistLabel(std::uint32_t face, Shape shape)
    {
        DungeonKit::ComboFrame const frame = FistFrame(face);
        float const center = DungeonKit::Distance(frame.origin, GnomereganRework::kRoomCenter.XY());
        float const o = Tune::kNumeralOffsetYd;
        switch (shape)
        {
            case Shape::LeftHalf:
                return frame.Point(center, o);
            case Shape::RightHalf:
                return frame.Point(center, -o);
            case Shape::Near:
                return frame.Point(center - o, 0.f);
            case Shape::Far:
            case Shape::Lane:
                break;
        }
        return frame.Point(center + o, 0.f);
    }

    // The fist's body: behind face `face`'s plane, facing the center (the orientation in `o`).
    inline GnomereganRework::Point3 FistSpot(std::uint32_t face)
    {
        DungeonKit::ComboFrame const frame = FistFrame(face);
        Vec2 const p = frame.Point(-Tune::kFistBodyBehindYd, 0.f);
        return { p.x, p.y, frame.z, frame.facing };
    }

    // The machine's timing (the contract's windUpMs, markerMs and gapMs, drawn all at once) as the kit's: strikes at
    // 4.0, 6.5 and 9.0 s from the call.
    inline DungeonKit::ComboTiming FistTiming()
    {
        return GnomerPummeler::KitTiming(0, Tune::kFistWindUpMs, Tune::kFistLiveMs, Tune::kFistApartMs, true);
    }

    // When punch `index` (0-based) strikes, from the call.
    inline std::uint32_t FistStrikeMs(std::size_t index)
    {
        std::vector<DungeonKit::PunchTimes> const times = DungeonKit::ComboTimeline(FistTiming(), index + 1);
        return times.back().strikeAt;
    }

    // MT24: three distinct shapes of the four, in a random order (`rand(n)` returns [0, n)). Distinct, so a punch
    // never repeats the one before it (D5's rule) and every chain leaves a way out (host-tested from every face).
    template <class Rand>
    std::vector<Shape> RollFistChain(Rand&& rand)
    {
        std::vector<Shape> pool(kFistShapes.begin(), kFistShapes.end());
        std::vector<Shape> out;
        while (out.size() < Tune::kFistPunches && !pool.empty())
        {
            std::size_t const at = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())))
                % pool.size();
            out.push_back(pool[at]);
            pool.erase(pool.begin() + static_cast<std::ptrdiff_t>(at));
        }
        return out;
    }

    // MT24 (ruling 68): any face, open or shut.
    template <class Rand>
    std::uint32_t RollFace(Rand&& rand)
    {
        return static_cast<std::uint32_t>(rand(GnomereganRework::kFaceCount)) % GnomereganRework::kFaceCount;
    }
}

#endif
