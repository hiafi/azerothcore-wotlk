/*
 * mod-dungeon-bosses, Gnomeregan D5: Crowd Pummeler 9-60 (6229) in the glass window, the pure, host-testable part (no
 * engine headers). Build spec: SP 1226-1437 (CP1-CP8, Build spec 1388), rulings 31-36 and 65 under the window ruling
 * of handoff section 10 (he floats in the green glass window at kPummelerSpot, 4.8 yd under the pocket floor, scale
 * 5); handoff section 3.5 row D5 and rule 33, sections 3.6, 3.8 (the pocket, the frame), 3.9 row 7, section 7 #23 A,
 * #27 A (reach 10), #28 A (the frame), #29 A (death line), #36 A to #38 A. Tested by tests/gnomer_pummeler_test.cpp.
 * Health is GnomereganRework.h Health: never restated here.
 *
 *   PummelerSpells / Tags / Texts   the spell ids (kSpellsPummeler 214460-214489, declared in apps/dbc-tools
 *                   source/npcs/gnomeregan/crowd_pummeler.py), the registry tags (G1's gnomeregan-shapes row 7: BM
 *                   MechanicDrill.h kGnTagLeftHook 60 to kGnTagUppercut 64) and the creature_text groups
 *   The window      the script-set combat reach and bounding radius (section 7 #27 A), re-applied after every scale
 *                   or display change (Creature::SetObjectScale rewrites both from creature_model_info x scale,
 *                   Creature.cpp:3575-3591; Unit::RecalculateObjectScale runs it on every scale aura and SetDisplayId,
 *                   Unit.cpp:12978-12994), the 3D melee and the hunters' too-close line on the floor
 *   The frame       the punch shapes on the pocket frame (section 7 #28 A: origin (-887.0, 364.2), the center line due
 *                   south, the 12 yd near line from the origin) as the shared kit's ComboShapeDefs
 *   Combinations    the rounds (normal), the heroic growth, the chain roll with the One-Two (CP1-CP7)
 *   The machine     the pure half of ComboMachine (GnomereganMachines.h): the frame parameters any caller passes, the
 *                   shapes they make, the contract's timing as the kit's ComboTimeline
 *
 * Frame words: +x is north, +y is west. The frame faces south (o = pi): "left" is east (the Left Hook's half), "right"
 * west, "forward" south, away from the glass.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_CROWD_PUMMELER_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_CROWD_PUMMELER_LOGIC_H

#include "DungeonKitComboLogic.h"
#include "DungeonKitMath.h"
#include "GnomereganRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace GnomerPummeler
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsPummeler;

    // Declared in apps/dbc-tools source/npcs/gnomeregan/crowd_pummeler.py (same ids, same order).
    enum PummelerSpells : std::uint32_t
    {
        SPELL_LEFT_HOOK         = kSpellSlice.first + 0,    // CP2: resolve copy (Physical), the east half
        SPELL_RIGHT_HOOK        = kSpellSlice.first + 1,    // CP3: resolve copy (Physical), the west half
        SPELL_CROWD_PUMMEL      = kSpellSlice.first + 2,    // CP4: resolve copy (Physical), within 12 yd
        SPELL_UPPERCUT          = kSpellSlice.first + 3,    // CP5 heroic: resolve copy (Physical), the 8 yd lane
        SPELL_CLINCH            = kSpellSlice.first + 4,    // CP6 heroic: resolve copy (Physical), past 12 yd
        SPELL_TRAMPLE           = kSpellSlice.first + 5,    // CP8: resolve copy (Physical), the kit's RegistryHit
        SPELL_TRAMPLE_LOOK      = kSpellSlice.first + 6,    // CP8: the ground slam ring, cast by the frame stalker
        SPELL_PUNCH_BAR         = kSpellSlice.first + 7,    // the punch pose over a normal live marker (1.5 s bar)
        SPELL_PUNCH_BAR_H       = kSpellSlice.first + 8,    // the punch pose over a heroic live marker (0.8 s bar)
        SPELL_SEEING_STARS      = kSpellSlice.first + 9,    // a punch that landed: the stars (a 3 s look, the rider)
        // kSpellSlice.first + 10 .. kSpellSlice.last: spare
    };
    static_assert(kSpellSlice.Contains(SPELL_LEFT_HOOK) && kSpellSlice.Contains(SPELL_SEEING_STARS),
        "Crowd Pummeler's spells sit in his slice");

    // Registry tags: G1's gnomeregan-shapes row 7 uses the same numbers (BM MechanicDrill.h kGnTagLeftHook 60,
    // kGnTagRightHook 61, kGnTagPummel 62, kGnTagClinch 63, kGnTagUppercut 64); a change goes in both. Trample is not
    // drilled (a healer pulse): the next number of the Pummeler band (60-69).
    enum PummelerTags : std::uint32_t
    {
        TAG_LEFT_HOOK       = 60,   // CP2 the east half
        TAG_RIGHT_HOOK      = 61,   // CP3 the west half
        TAG_CROWD_PUMMEL    = 62,   // CP4 within 12 yd of the frame origin
        TAG_CLINCH          = 63,   // CP6 heroic: 12 to 40 yd
        TAG_UPPERCUT        = 64,   // CP5 heroic: the 8 yd lane
        TAG_TRAMPLE         = 65,   // CP8 (not drilled)
    };

    // The drill's tag table (LESSONS A.3 #4): diffed against BM MechanicDrill.h at the WP's close.
    struct DrillTag
    {
        std::uint32_t tag;
        char const* kind;
        char const* drillName;
    };
    inline constexpr std::array<DrillTag, 5> kDrillTags{ {
        { TAG_LEFT_HOOK, "Zone", "kGnTagLeftHook" },
        { TAG_RIGHT_HOOK, "Zone", "kGnTagRightHook" },
        { TAG_CROWD_PUMMEL, "Zone", "kGnTagPummel" },
        { TAG_CLINCH, "Zone", "kGnTagClinch" },
        { TAG_UPPERCUT, "Zone", "kGnTagUppercut" },
    } };

    // Texts (creature_text 6229, none stock: data/sql/updates/pending_db_world/rev_crowd_pummeler_gnomeregan.sql).
    enum PummelerTexts : std::uint8_t
    {
        EMOTE_COMBINATION   = 0,    // "%s winds up a combination!" (type 41), every call
        EMOTE_ROUND_TWO     = 1,    // "The bell rings. Round two!" (normal, at 66%)
        EMOTE_FINAL_ROUND   = 2,    // "The bell rings. Final round!" (normal, at 33%)
        EMOTE_DEATH         = 3,    // "%s shudders, sparks, and goes dark behind the glass." (section 7 #29 A)
    };

    // V's looks that the script plays by number (apps/dbc-tools source/npcs/gnomeregan/_visuals.py; the DT test pins
    // them): the bell (CP_BELL, SoundEntries) and the punch pose (CP_PUNCH_EMOTE_ANIM 16 = AttackUnarmed, played as
    // EMOTE_ONESHOT_ATTACK_UNARMED 35).
    std::uint32_t constexpr kBellSound = 6555;
    std::uint32_t constexpr kPunchEmote = 35;
    // Display 6774 is worn by 6229, 21426, 25752 and 25766: never edit its model info (the reach is the script's).
    std::uint32_t constexpr kDisplayPummeler = 6774;

    // A punch shape. The values are GnomereganMachines::PunchShape's (CrowdPummelerMachine.cpp static_asserts them):
    // this header stays engine-free.
    enum class Shape : std::uint8_t
    {
        LeftHalf    = 0,    // Left Hook: the half left of the center line (east)
        RightHalf   = 1,    // Right Hook: the west half
        Near        = 2,    // Crowd Pummel: within the near radius of the origin
        Far         = 3,    // Clinch: past the near radius
        Lane        = 4,    // Uppercut: the lane down the center line
    };
    std::size_t constexpr kShapeCount = 5;

    inline constexpr std::array<char const*, kShapeCount> kShapeNames{ {
        "left-hook", "right-hook", "pummel", "clinch", "uppercut",
    } };

    inline char const* ShapeName(Shape s)
    {
        std::size_t const i = static_cast<std::size_t>(s);
        return i < kShapeCount ? kShapeNames[i] : "?";
    }

    inline constexpr bool IsHook(Shape s)
    {
        return s == Shape::LeftHalf || s == Shape::RightHalf;
    }

    // One punch of a chain: a shape, or a One-Two (CP7: `paired` lands with it).
    struct PunchRoll
    {
        Shape shape = Shape::LeftHalf;
        std::optional<Shape> paired;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec CP1-CP8 and "Tuning starting points"; section 7 #27 A, #28 A, #37 A; rule 24)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // The window (section 10, rule 33). Scale 5 by SetDisplayId(6774, 5) in one call (rule 4); the combat reach
        // and the bounding radius are the script's: 10 at scale 5 (section 7 #27 A: melee to 11.9 yd out on the
        // floor, hunters too close inside 17.2 yd), never below 10 (melee must cross the glass at any scale), and
        // grown with the scale above 5.
        float constexpr kWindowScale = 5.f;
        float constexpr kCombatReachYd = 10.f;
        float constexpr kReachEpsilonYd = 0.01f;
        // A player's combat reach and the melee slack (Unit::GetMeleeRange: both reaches + 4/3), the hunters' Auto
        // Shot minimum range (Spell::CheckRange: TOO_CLOSE inside min range + the melee range, 3D).
        float constexpr kPlayerReachYd = 1.5f;
        float constexpr kMeleeSlackYd = 4.f / 3.f;
        float constexpr kHunterMinRangeYd = 5.f;
        // Kept on his spot: re-placed when he drifts farther than this (an evade's home move, a knockback), at most
        // once per kReplaceEveryMs (a spot the engine itself keeps adjusting must not teleport him every tick).
        float constexpr kSpotDriftYd = 0.5f;
        std::uint32_t constexpr kReplaceEveryMs = 5000;

        // The bots' ranged band (R-1-B M1): ranged damage dealers and healers hold 19 to 26 yd (2D) from his origin,
        // past the hunters' too-close line (17.2 yd of floor: between it and melee's 11.9 a hunter can neither melee
        // nor shoot, and no bot trigger fires there) and inside the pocket (the south wall 28.3 yd, the far corner
        // 33 yd; a ranged bot in a corridor deals nothing). A healer at 26 is within 38 yd of a tank in melee.
        float constexpr kRangedBandMinYd = 19.f;
        float constexpr kRangedBandMaxYd = 26.f;

        // R-1-B M2: a player's melee pet chases a creature to its back (PetAI::StartChase: ChaseAngle(pi)); his back
        // is the glass over the lower room, so the angled point has no path and the pet stops attacking. The script
        // drops the angle for each new chase, and again every kPetChaseRetryMs while the pet is out of his reach.
        std::uint32_t constexpr kPetChaseRetryMs = 2000;

        // The frame (section 7 #28 A, section 3.8): the near line 12 yd from the origin, the far donut to 40 yd, the
        // halves 30 yd forward and across (every pocket cell), the Uppercut lane 8 yd wide to the south wall (25.2
        // yd from the origin; 26 keeps the wall's foot inside). The halves and the lane start kBehindYd behind the
        // origin, so the strip between the origin and the glass (melee's) is in them.
        float constexpr kNearRadiusYd = 12.f;
        float constexpr kFarOuterYd = 40.f;
        float constexpr kHalfReachYd = 30.f;
        float constexpr kLaneWidthYd = 8.f;
        float constexpr kLaneLengthYd = 26.f;
        float constexpr kBehindYd = 5.f;

        // CP1 the Combo: a 1 s call flash per punch in order, then each punch's live marker (normal 1.5 s, heroic
        // 0.8 s), punches 2 s (heroic 1.2 s) apart. First at 10 s (guess), then 18 s after the last punch.
        std::uint32_t constexpr kCallMs = 1000;
        inline constexpr NH<std::uint32_t> kLiveMs{ 1500, 800 };
        inline constexpr NH<std::uint32_t> kApartMs{ 2000, 1200 };
        static_assert(kLiveMs.normal >= GnomereganRework::kWarningFloorMs, "a normal punch meets the warning floor");
        static_assert(kApartMs.normal >= kLiveMs.normal && kApartMs.heroic >= kLiveMs.heroic,
            "a punch's live marker never overlaps the one before it");
        std::uint32_t constexpr kComboFirstMs = 10000;
        std::uint32_t constexpr kComboAfterMs = 18000;

        // Normal rounds: 2, 3 and 4 punches; the bell at 66% and 33% (SP CP1).
        inline constexpr std::array<std::uint32_t, 3> kRoundLengths{ { 2, 3, 4 } };
        float constexpr kRoundTwoPct = 66.f;
        float constexpr kFinalRoundPct = 33.f;

        // Heroic: the first combination 3 punches, +1 each combination, +1 per punch that landed, no cap (rule 23).
        // kMaxPunches is the kit's limit (a punch index and its shapes fit uint8), not a design cap: 120 punches
        // take 120 s of calls and 143 s of strikes.
        std::uint32_t constexpr kHeroicFirstLength = 3;
        std::uint32_t constexpr kGrowthPerCombo = 1;
        std::uint32_t constexpr kGrowthPerLanded = 1;
        std::uint32_t constexpr kMaxPunches = 120;
        // CP7 One-Two (heroic): from the fourth punch of a combination on, half of the punches (section 7 #37 A) are a
        // hook with the Pummel or the Clinch.
        std::uint32_t constexpr kOneTwoFromPunch = 4;
        std::uint32_t constexpr kOneTwoChancePct = 50;

        // CP2-CP6: each punch 40% (heroic 60%) of the reference row, the tank's row on the tank, plus Weakened.
        inline constexpr NH<float> kPunchPct{ 40.f, 60.f };
        // CP4 Crowd Pummel's knockback, 7.5 yd due south (SP): 12 yd/s with a 6 yd/s lift flies 0.62 s.
        float constexpr kPummelKnockSpeedXY = 12.f;
        float constexpr kPummelKnockSpeedZ = 6.f;
        // CP5 Uppercut's knock up: straight up at 12 yd/s (3.7 yd high, no fall damage).
        float constexpr kUppercutKnockSpeedZ = 12.f;
        // The stars over a punched head (the rider's look).
        std::uint32_t constexpr kSeeingStarsMs = 3000;

        // CP8 Trample: 8% (heroic 12%) to everyone on the near side, every 10 s from 6 s, never during a combination;
        // at once when nobody has been in his melee reach for 1.5 s (guess), at most every 3 s (guess), and not in the
        // 2 s after a combination's last punch (guess). "Within 10 yd" of the stock spell reads as the 12 yd near line
        // of the frame here (designer question: a 10 yd circle on a unit sunk 4.8 yd under the floor reaches 8.8 yd of
        // floor, inside his own 11.9 yd melee reach, so "at once when nobody is in reach" would hit nobody).
        std::uint32_t constexpr kTrampleFirstMs = 6000;
        std::uint32_t constexpr kTrampleEveryMs = 10000;
        inline constexpr NH<float> kTramplePct{ 8.f, 12.f };
        float constexpr kTrampleRadiusYd = kNearRadiusYd;
        std::uint32_t constexpr kTrampleNoReachMs = 1500;
        std::uint32_t constexpr kTrampleMinGapMs = 3000;
        std::uint32_t constexpr kTrampleAfterComboMs = 2000;

        // The machine reports a punch's hits this long after its strike (the registry resolves it on its own tick).
        std::uint32_t constexpr kReportAfterMs = 400;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The window
    // ----------------------------------------------------------------------------------------------------------------

    // The pocket floor at the frame origin, and how far under it his origin floats (4.8 yd).
    float constexpr kPocketFloorZ = GnomereganRework::kPummelerFrameOrigin.z;
    float constexpr kSpotDepthYd = kPocketFloorZ - GnomereganRework::kPummelerSpot.z;

    // The combat reach (and bounding radius) for his current object scale: 10 at scale 5, never below 10, and in
    // proportion above it. Re-applied after every SetObjectScale (a SetDisplayId, a scale aura), rule 33.
    inline float WindowReach(float objectScale)
    {
        float const grown = Tune::kCombatReachYd * objectScale / Tune::kWindowScale;
        return std::max(Tune::kCombatReachYd, grown);
    }

    // True when the unit's field drifted from the reach the window wants (an engine rewrite).
    inline bool ReachNeedsReset(float current, float wanted)
    {
        return std::fabs(current - wanted) > Tune::kReachEpsilonYd;
    }

    // A 3D range from his origin as a floor distance, for a player standing `depthYd` above it (0 when the range does
    // not reach the floor).
    inline float FloorReach(float range3d, float depthYd)
    {
        float const r2 = range3d * range3d - depthYd * depthYd;
        return r2 > 0.f ? std::sqrt(r2) : 0.f;
    }

    // How far out on the floor (from the point above his origin) a player's melee reaches him.
    inline float MeleeFloorReach(float reach, float depthYd = kSpotDepthYd)
    {
        return FloorReach(reach + Tune::kPlayerReachYd + Tune::kMeleeSlackYd, depthYd);
    }

    // Inside this floor distance a hunter's Auto Shot (5 yd minimum range) is TOO_CLOSE.
    inline float HunterTooCloseFloor(float reach, float depthYd = kSpotDepthYd)
    {
        return FloorReach(Tune::kHunterMinRangeYd + reach + Tune::kPlayerReachYd + Tune::kMeleeSlackYd, depthYd);
    }

    // True when a player `floorYd` out on the floor is past the hunters' too-close line (HunterTooCloseFloor, compared
    // in squares: std::sqrt is not constexpr).
    constexpr bool PastHunterLine(float floorYd, float reach, float depthYd = kSpotDepthYd)
    {
        float const line = Tune::kHunterMinRangeYd + reach + Tune::kPlayerReachYd + Tune::kMeleeSlackYd;
        return floorYd * floorYd + depthYd * depthYd > line * line;
    }
    static_assert(PastHunterLine(Tune::kRangedBandMinYd, Tune::kCombatReachYd),
        "the ranged band starts past the hunters' too-close line");
    static_assert(Tune::kRangedBandMinYd < Tune::kRangedBandMaxYd, "the ranged band is a band");

    // R-1-B M2: re-issue a pet's chase without the angle when the chase is new (another generator than the one fixed
    // last), or when the pet is still out of his reach kPetChaseRetryMs after the last fix.
    constexpr bool PetChaseNeedsFix(bool newChase, bool inReach, std::uint32_t sinceFixMs)
    {
        return newChase || (!inReach && sinceFixMs >= Tune::kPetChaseRetryMs);
    }

    // Pull and damage only from the pocket (handoff section 3.5 row D5, section 3.8 the pocket box): an attacker
    // anywhere else (the lower room 44 yd down, the corridors) deals nothing and cannot pull him.
    inline bool FromThePocket(float x, float y, float z)
    {
        return GnomereganRework::InPocketBox(x, y, z);
    }

    // His victims (CanAIAttack, LESSONS A.2 #12): never one under the pocket floor (the lower room, 44 yd down, can
    // see him through the hit sphere but never reach his fight). The corridors stay valid: a hook's dodge may cross
    // the pocket box's edge for a moment, and the arena leash resets him when the group has left.
    inline bool VictimAllowed(float z)
    {
        return z >= GnomereganRework::kPocketBoxMinZ;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The frame and its shapes (the machine's pure half: the hard mode passes its own parameters)
    // ----------------------------------------------------------------------------------------------------------------
    struct FrameParams
    {
        float halfReachYd = Tune::kHalfReachYd;
        float nearRadiusYd = Tune::kNearRadiusYd;
        float farOuterYd = Tune::kFarOuterYd;
        float laneWidthYd = Tune::kLaneWidthYd;
        float laneLengthYd = Tune::kLaneLengthYd;
        float behindYd = Tune::kBehindYd;
    };

    // The pocket frame (section 7 #28 A): origin (-887.0, 364.2) on the floor, facing due south.
    inline DungeonKit::ComboFrame PocketFrame()
    {
        GnomereganRework::Point3 const& o = GnomereganRework::kPummelerFrameOrigin;
        return DungeonKit::ComboFrame{ o.XY(), o.z, o.o };
    }

    // A shape in frame terms. The halves and the lane start `behindYd` behind the origin; the near circle and the far
    // donut are centered on the origin (the 12 yd near line is the origin's, section 7 #28 A).
    inline DungeonKit::ComboShapeDef ShapeDef(Shape shape, FrameParams const& f)
    {
        using Def = DungeonKit::ComboShapeDef;
        switch (shape)
        {
            case Shape::LeftHalf:
                return Def::HalfLeft(-f.behindYd, f.halfReachYd, f.halfReachYd);
            case Shape::RightHalf:
                return Def::HalfRight(-f.behindYd, f.halfReachYd, f.halfReachYd);
            case Shape::Near:
                return Def::Circle(0.f, 0.f, f.nearRadiusYd);
            case Shape::Far:
                return Def::Donut(0.f, 0.f, f.nearRadiusYd, f.farOuterYd);
            case Shape::Lane:
                return Def::Lane(-f.behindYd, f.laneLengthYd, f.laneWidthYd);
        }
        return Def::Circle(0.f, 0.f, f.nearRadiusYd);
    }

    inline DungeonKit::PlacedShape PlaceShape(DungeonKit::ComboFrame const& frame, Shape shape, FrameParams const& f)
    {
        return DungeonKit::Place(frame, ShapeDef(shape, f));
    }

    // CP8 Trample's area: the near side of the pocket frame (Tune::kTrampleRadiusYd from the origin).
    inline bool InTrample(Vec2 p)
    {
        return DungeonKit::Distance(PocketFrame().origin, p) <= Tune::kTrampleRadiusYd;
    }

    // The machine contract's timing (GnomereganMachines.h ComboSpec) as the kit's: in order (Crowd Pummeler: a call
    // flash each, then the live markers) or all at once (the hard mode fist: the wind-up is the kit's call, every
    // shape drawn from the start).
    inline DungeonKit::ComboTiming KitTiming(std::uint32_t callFlashMs, std::uint32_t windUpMs, std::uint32_t markerMs,
        std::uint32_t gapMs, bool drawAllAtOnce)
    {
        DungeonKit::ComboTiming t;
        t.mode = drawAllAtOnce ? DungeonKit::ComboCallMode::AllAtOnce : DungeonKit::ComboCallMode::Sequential;
        t.callMs = drawAllAtOnce ? windUpMs : callFlashMs;
        t.liveMs = markerMs;
        t.spacingMs = gapMs;
        return t;
    }

    // Crowd Pummeler's own timing.
    inline DungeonKit::ComboTiming PummelerTiming(bool heroic)
    {
        return KitTiming(Tune::kCallMs, 0, Tune::kLiveMs.Get(heroic), Tune::kApartMs.Get(heroic), false);
    }

    // When the machine reports punch i's hits (its strike plus the registry's tick).
    inline bool PunchReportDue(std::uint32_t elapsedMs, std::uint32_t strikeAtMs)
    {
        return elapsedMs >= strikeAtMs + Tune::kReportAfterMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Combinations (CP1, CP7)
    // ----------------------------------------------------------------------------------------------------------------

    // Normal rounds: 1 above 66%, 2 from 66%, 3 from 33%.
    inline std::uint32_t RoundFor(float healthPct)
    {
        if (healthPct <= Tune::kFinalRoundPct)
            return 3;
        if (healthPct <= Tune::kRoundTwoPct)
            return 2;
        return 1;
    }

    inline std::uint32_t NormalLength(std::uint32_t round)
    {
        std::size_t const i = std::clamp<std::size_t>(round, 1, Tune::kRoundLengths.size()) - 1;
        return Tune::kRoundLengths[i];
    }

    // Heroic: 3 + one per combination already thrown + one per punch that landed so far (kMaxPunches is the kit's).
    inline std::uint32_t HeroicLength(std::uint32_t combosThrown, std::uint32_t landedSoFar)
    {
        std::uint64_t const n = std::uint64_t(Tune::kHeroicFirstLength)
            + std::uint64_t(Tune::kGrowthPerCombo) * combosThrown + std::uint64_t(Tune::kGrowthPerLanded) * landedSoFar;
        return static_cast<std::uint32_t>(std::min<std::uint64_t>(n, Tune::kMaxPunches));
    }

    inline constexpr std::array<Shape, 3> kNormalPool{ { Shape::LeftHalf, Shape::RightHalf, Shape::Near } };
    inline constexpr std::array<Shape, 5> kHeroicPool{ {
        Shape::LeftHalf, Shape::RightHalf, Shape::Near, Shape::Far, Shape::Lane,
    } };

    // Rolls a chain of `length` punches. `rng(n)` returns a number in [0, n). A single punch never repeats the single
    // punch right before it (a repeat is a free punch: nobody moves). Heroic: from the fourth punch on, each is a
    // One-Two with Tune::kOneTwoChancePct: a hook with the Pummel or the Clinch (one quarter safe).
    template <class Rng>
    std::vector<PunchRoll> RollChain(bool heroic, std::uint32_t length, Rng&& rng)
    {
        length = std::min(length, Tune::kMaxPunches);
        std::vector<PunchRoll> out;
        out.reserve(length);
        Shape const* pool = heroic ? kHeroicPool.data() : kNormalPool.data();
        std::size_t const poolSize = heroic ? kHeroicPool.size() : kNormalPool.size();
        for (std::uint32_t i = 0; i < length; ++i)
        {
            PunchRoll punch;
            if (heroic && i + 1 >= Tune::kOneTwoFromPunch && rng(100u) < Tune::kOneTwoChancePct)
            {
                punch.shape = rng(2u) == 0 ? Shape::LeftHalf : Shape::RightHalf;
                punch.paired = rng(2u) == 0 ? Shape::Near : Shape::Far;
                out.push_back(punch);
                continue;
            }
            std::optional<Shape> before;
            if (!out.empty() && !out.back().paired)
                before = out.back().shape;
            std::size_t const choices = poolSize - (before ? 1 : 0);
            std::size_t pick = static_cast<std::size_t>(rng(static_cast<std::uint32_t>(choices))) % choices;
            for (std::size_t k = 0; k < poolSize; ++k)
            {
                if (before && pool[k] == *before)
                    continue;
                if (pick == 0)
                {
                    punch.shape = pool[k];
                    break;
                }
                --pick;
            }
            out.push_back(punch);
        }
        return out;
    }

    // A One-Two leaves exactly one quarter: a hook (one side) with the near circle or the far donut.
    inline bool IsValidOneTwo(PunchRoll const& p)
    {
        return p.paired && IsHook(p.shape) && (*p.paired == Shape::Near || *p.paired == Shape::Far);
    }

    // The chain's last strike, in ms from the call (CP1: the next combination is due 18 s after it).
    inline std::uint32_t ChainLengthMs(bool heroic, std::size_t punches)
    {
        return DungeonKit::ComboLength(PummelerTiming(heroic), punches);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Test actions (`.dbtest gnomer pummeler ...`, through DoAction / SetData / GetData on the boss)
    // ----------------------------------------------------------------------------------------------------------------
    enum PummelerTestActions : std::int32_t
    {
        ACTION_TEST_COMBO       = 1,    // a combination now (DATA_TEST_COMBO_LENGTH first; 0: the fight's own length)
        ACTION_TEST_TRAMPLE     = 2,    // Trample now
        ACTION_TEST_ROUND_TWO   = 3,    // normal: the 66% bell now
        ACTION_TEST_FINAL_ROUND = 4,    // normal: the 33% bell now
    };

    enum PummelerTestData : std::uint32_t
    {
        DATA_TEST_ENGAGED       = 1,
        DATA_TEST_COMBO_LENGTH  = 2,    // Set: the next test combination's length; Get: the last chain's
        DATA_TEST_COMBOS        = 3,    // combinations thrown this pull
        DATA_TEST_LANDED        = 4,    // punches landed this pull
        DATA_TEST_ROUND         = 5,
    };
}

#endif
