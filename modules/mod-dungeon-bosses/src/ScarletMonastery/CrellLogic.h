/*
 * mod-dungeon-bosses, Scarlet Monastery D9:
 * Forgemaster Gideon Crell, the Armorer (300940), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Forgemaster Gideon Crell, the Armorer" (AR1-AR8, Build spec), handoff
 * section 3.5 row D9, 3.6, 3.8 (the storeroom), 7 #28 A (16 heroic sparks), 7 #29 A (recruits from the Armor Crate).
 * Tested by tests/sm_crell_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsCrell (212900-212949), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/crell.py
 *   Storeroom  the floor (the NAVMESH map, 2 yd cells), its outline (the arena and the bots' bounds), the spots: the
 *              anvil, the trough, the forge, the Armor Crate, the counter, the recruits' way out
 *   Orders     AR1 the frame: the order clock, the steps' offsets, which piece an order issues, the heroic quality
 *   Tuning     NH<> percents, sizes and timers straight from the build spec (percents of the reference row: N level 37
 *              normal, H level 60 heroic)
 *   Picks      AR2 the sparks (random floor spots, spread apart), AR7 the dash's end, AR8 a rivet's spot and the
 *              plate's rivet thresholds
 */

#ifndef MOD_DUNGEON_BOSSES_SM_CRELL_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_CRELL_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace SmCrell
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsCrell;

    enum CrellSpells : std::uint32_t
    {
        SPELL_AR_SPARK = kSpellSlice.first + 0,  // 212900 AR2 a spark's hit (resolve copy, Fire)
        SPELL_AR_SPARK_LOOK = kSpellSlice.first + 1,  // 212901 AR2 the spark's burst at its spot (a look)
        SPELL_AR_SLAG = kSpellSlice.first + 2,  // 212902 AR2a a slag pool's tick (resolve copy, Fire; heroic)
        SPELL_AR_SLAG_LOOK = kSpellSlice.first + 3,  // 212903 AR2a the pool's look (an aura on a stalker)
        SPELL_AR_HAMMER_CAST = kSpellSlice.first + 4,  // 212904 AR3 the 2.5 s bar (Physical, not interruptible)
        SPELL_AR_HAMMER_RING = kSpellSlice.first + 5,  // 212905 AR3 the donut's hit (resolve copy, Physical)
        SPELL_AR_HAMMER_BURST = kSpellSlice.first + 6,  // 212906 AR3 the anvil circle's hit (resolve copy, Physical)
        SPELL_AR_ANVIL_STRIKE_LOOK = kSpellSlice.first + 7,  // 212907 AR3 the strike on the anvil (a look)
        SPELL_AR_STEAM = kSpellSlice.first + 8,  // 212908 AR4 the steam's tick (resolve copy, Fire)
        SPELL_AR_STEAM_LOOK = kSpellSlice.first + 9,  // 212909 AR4 the steam's look (an aura on a stalker)
        SPELL_AR_SLAG_BURST = kSpellSlice.first + 10,  // 212910 AR4a a pool's burst (resolve copy, Fire; heroic)
        SPELL_AR_SLAG_BURST_LOOK = kSpellSlice.first + 11,  // 212911 AR4a the burst at the pool (a look)
        SPELL_AR_TEMPER = kSpellSlice.first + 12,  // 212912 AR5 the 2.5 s interruptible cast (Fire; heroic)
        SPELL_AR_FLAWED = kSpellSlice.first + 13,  // 212913 AR5 the flawed piece's marker on Crell
        SPELL_AR_MASTERWORK = kSpellSlice.first + 14,  // 212914 AR5 the masterwork piece's marker on Crell
        SPELL_AR_FORGED_BLADE = kSpellSlice.first + 15,  // 212915 AR-Bl the holder aura (the Blade window)
        SPELL_AR_CLEAVE = kSpellSlice.first + 16,  // 212916 AR-Bl the cleave's hit on others (resolve copy)
        SPELL_AR_CLEAVE_TANK = kSpellSlice.first + 17,  // 212917 AR-Bl the cleave on the tank (kit percent script)
        SPELL_AR_PROVING_STRIKE = kSpellSlice.first + 18,  // 212918 AR7 a dash line's hit (resolve copy, Physical)
        SPELL_AR_DASH_LOOK = kSpellSlice.first + 19,  // 212919 AR7 the dash (Charge's look on Crell)
        SPELL_AR_RED_HOT_PLATE = kSpellSlice.first + 20,  // 212920 AR-Pl the absorb (spell_sm_crell_red_hot_plate)
        SPELL_AR_PLATE_BURN = kSpellSlice.first + 21,  // 212921 AR-Pl the burn-back on an attacker (Fire)
        SPELL_AR_RIVET = kSpellSlice.first + 22,  // 212922 AR8 a rivet's hit (resolve copy, Fire)
        SPELL_AR_RIVET_LOOK = kSpellSlice.first + 23,  // 212923 AR8 the rivet's flight to its spot (a look)
        // 212924-212949 spare
    };
    static_assert(SPELL_AR_RIVET_LOOK <= kSpellSlice.last, "Crell's spells must stay in his slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum CrellTags : std::uint32_t
    {
        TAG_AR_SPARK        = 2,    // AR2 a spark
        TAG_AR_SLAG         = 21,   // AR2a a slag pool (heroic)
        TAG_AR_HAMMER_RING  = 3,    // AR3 the donut
        TAG_AR_HAMMER_BURST = 31,   // AR3 the anvil circle
        TAG_AR_STEAM        = 4,    // AR4 the steam
        TAG_AR_SLAG_BURST   = 41,   // AR4a a pool's burst (heroic)
        TAG_AR_CLEAVE       = 10,   // AR-Bl the cleave
        TAG_AR_STRIKE       = 7,    // AR7 a dash line
        TAG_AR_BLADE_SPREAD = 70,   // AR7 the Blade window's 6 yd spread (no damage)
        TAG_AR_RIVET        = 8,    // AR8 a rivet
    };

    // creature_text groups of 300940 (data/sql/updates/pending_db_world/rev_crell_scarlet_monastery.sql, ARM "Text").
    enum CrellTexts : std::uint8_t
    {
        SAY_PULL            = 0,    // yell: "Out of uniform, are we? I'll fit you myself!"
        SAY_ORDER_BLADE     = 1,    // yell (AR1, a Blade order): "A blade for the Crusade!"
        SAY_ORDER_PLATE     = 2,    // yell (AR1, a Plate order; heroic orders yell 1 then 2)
        EMOTE_TEMPER        = 3,    // boss emote (AR5, heroic): "%s begins to temper the piece!"
        SAY_PROVING_STRIKE  = 4,    // yell (AR7): "Let's test the edge!"
        EMOTE_HAND_OVER     = 5,    // boss emote (AR6, heroic): "%s hands the finished piece to a Scarlet Recruit."
        SAY_KILL            = 6,    // yell: "Next!"
        SAY_DEATH           = 7,    // yell: "Who... will keep... the stores..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The storeroom (handoff 3.8, NAVMESH "Crell": floor z 8.0, two lobes joined by a 12 yd neck, plus the east strip
    // toward the upper hall). Compass follows the game's axes: +x north, +y west.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kFloorZ = 8.0f;
    inline constexpr std::uint32_t kKillLineCooldownMs = 5000;     // his "Next!" on a player kill, once per 5 s

    // The objects of the encounter (database spawns of the SQL rev; scenery, never touched by the script). The anvil is
    // the Hammer's anchor (ScarletMonasteryRework.h kCrellAnvil), the trough the steam's (NAVMESH: clearance 4.1,
    // inside the 8 yd anvil circle), the forge stands 9 yd north of the anvil, out of the circle.
    inline constexpr Point3 kAnvil = ScarletMonasteryRework::kCrellAnvil;
    inline constexpr Point3 kTrough{ 1776.0f, -394.0f, kFloorZ };
    inline constexpr Point3 kForge{ 1785.0f, -388.0f, kFloorZ };
    // Crell's spawn: beside the anvil, between it and the trough (NAVMESH's proposal), facing the stairs he is pulled
    // from (the south-west, about 141 degrees).
    inline constexpr Point3 kCrellSpawn{ 1776.0f, -390.5f, kFloorZ };
    inline constexpr float kCrellSpawnFacing = 2.46f;

    // AR6: the Armor Crate (GO 3703, guid 32254 [DB]) the recruits step out of (section 7 #29 A), his counter (3 yd off
    // the anvil toward the crate) and the strip's far end toward the upper hall, where they leave the room.
    inline constexpr Point3 kArmorCrate{ 1771.76f, -377.26f, kFloorZ };
    inline constexpr Point3 kCounter{ 1774.9f, -385.2f, kFloorZ };
    inline constexpr Point3 kRecruitExit{ 1808.0f, -410.0f, kFloorZ };

    // The floor: the NAVMESH storeroom map (navmesh/maps2.txt, 2 yd cells), row r at x = 1812 - 2r, column c at
    // y = -354 - 2c; '#' is walkable floor at z about 8. The east strip (x 1788-1812) leads on to the upper hall.
    inline constexpr std::size_t kFloorRows = 37;
    inline constexpr std::size_t kFloorCols = 35;
    inline constexpr float kFloorRowX0 = 1812.f;
    inline constexpr float kFloorColY0 = -354.f;
    inline constexpr float kFloorCellYd = 2.f;
    inline constexpr std::array<char const*, kFloorRows> kFloor{ {
        "..........................#.####...",   // x 1812
        "........................#######....",   // x 1810
        ".......................############",   // x 1808
        ".......................############",   // x 1806
        ".......................############",   // x 1804
        ".......................############",   // x 1802
        ".......................############",   // x 1800
        ".......................############",   // x 1798
        ".......................############",   // x 1796
        ".......................##########..",   // x 1794
        "........................########...",   // x 1792
        ".........................######....",   // x 1790
        ".........................######....",   // x 1788
        "............########....#######....",   // x 1786
        ".............########..#########...",   // x 1784
        "...........######################..",   // x 1782
        "...........######################..",   // x 1780
        "...........######################..",   // x 1778
        "...........######################..",   // x 1776
        "...........#####################...",   // x 1774
        "............####################...",   // x 1772
        "...........######################..",   // x 1770
        "...........##########..#########...",   // x 1768
        "............########....########...",   // x 1766
        ".............######................",   // x 1764
        ".............######................",   // x 1762
        "...#####....########....########...",   // x 1760
        "..#######..#########...##########..",   // x 1758
        "..###############################..",   // x 1756
        "...##############################..",   // x 1754
        "..###############################..",   // x 1752
        "...##############################..",   // x 1750
        "..###############################..",   // x 1748
        "...##############################..",   // x 1746
        "..#######..##########..##########..",   // x 1744
        "...######...#########...#######....",   // x 1742
        "....####...........................",   // x 1740
    } };

    // The cell holding a point (rounded to the nearest center); false off the map.
    constexpr bool CellOf(Vec2 p, std::size_t& row, std::size_t& col)
    {
        float const r = (kFloorRowX0 - p.x) / kFloorCellYd;
        float const c = (kFloorColY0 - p.y) / kFloorCellYd;
        if (r < -0.5f || c < -0.5f)
            return false;
        auto const ri = static_cast<std::size_t>(r + 0.5f);
        auto const ci = static_cast<std::size_t>(c + 0.5f);
        if (ri >= kFloorRows || ci >= kFloorCols)
            return false;
        row = ri;
        col = ci;
        return true;
    }

    constexpr Vec2 CellCenter(std::size_t row, std::size_t col)
    {
        return { kFloorRowX0 - kFloorCellYd * static_cast<float>(row),
            kFloorColY0 - kFloorCellYd * static_cast<float>(col) };
    }

    constexpr bool IsFloorCell(std::size_t row, std::size_t col)
    {
        return row < kFloorRows && col < kFloorCols && kFloor[row][col] == '#';
    }

    // Is `p` on the storeroom's floor (the cell holding it is walkable)?
    constexpr bool IsFloor(Vec2 p)
    {
        std::size_t row = 0;
        std::size_t col = 0;
        return CellOf(p, row, col) && IsFloorCell(row, col);
    }

    constexpr std::size_t FloorCellCount()
    {
        std::size_t n = 0;
        for (std::size_t r = 0; r < kFloorRows; ++r)
            for (std::size_t c = 0; c < kFloorCols; ++c)
                n += IsFloorCell(r, c) ? 1u : 0u;
        return n;
    }

    constexpr float FloorAreaSqYd()
    {
        return static_cast<float>(FloorCellCount()) * kFloorCellYd * kFloorCellYd;
    }

    // The outline (cell edges, about 1 yd outside the outer floor cells): the south lobe, the neck, the north lobe and
    // the east strip, one concave polygon. The arena guard and the bots' bounds use it.
    inline constexpr std::array<Vec2, 14> kOutline{ {
        { 1739.f, -357.f }, { 1761.f, -357.f }, { 1761.f, -378.f }, { 1765.f, -378.f }, { 1765.f, -375.f },
        { 1787.f, -375.f }, { 1787.f, -399.f }, { 1813.f, -399.f }, { 1813.f, -423.f }, { 1765.f, -423.f },
        { 1765.f, -392.f }, { 1761.f, -392.f }, { 1761.f, -419.f }, { 1739.f, -419.f },
    } };
    inline constexpr float kOutlineZMin = 5.f;
    inline constexpr float kOutlineZMax = 13.f;

    // His arena (the guard's frame): the outline at the storeroom's floor height (the stairs up to the entry hall and
    // the upper hall are off it).
    inline DungeonKit::Arena StoreroomArena()
    {
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Polygon(std::vector<Vec2>(kOutline.begin(), kOutline.end()),
            kOutlineZMin, kOutlineZMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR1 The Order: the frame
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint32_t firstMs;
        std::uint32_t everyMs;
    };

    // The first order 6 s after the pull, then every 30 s (heroic 25 s), start to start.
    inline constexpr NH<Beat> kOrderBeat{ { 6000, 30000 }, { 6000, 25000 } };

    // The steps from the order's yell (T): Heat at T, Hammer at T+5 (T+4), Quench at T+10 (T+8), Temper (heroic) at
    // T+10, the Issue at T+15 (T+12.5).
    inline constexpr NH<std::uint32_t> kHammerAtMs{ 5000, 4000 };
    inline constexpr NH<std::uint32_t> kQuenchAtMs{ 10000, 8000 };
    inline constexpr std::uint32_t kTemperAtMs = 10000;
    inline constexpr NH<std::uint32_t> kIssueAtMs{ 15000, 12500 };

    enum class Step : std::uint8_t
    {
        Heat,
        Hammer,
        Quench,
        Temper,     // heroic only
        Issue,
        Done,
    };

    // The step after `step` on this difficulty (normal skips the Temper).
    constexpr Step NextStep(Step step, bool heroic)
    {
        switch (step)
        {
            case Step::Heat:    return Step::Hammer;
            case Step::Hammer:  return Step::Quench;
            case Step::Quench:  return heroic ? Step::Temper : Step::Issue;
            case Step::Temper:  return Step::Issue;
            default:            return Step::Done;
        }
    }

    // A step's offset from the order's yell.
    constexpr std::uint32_t StepAtMs(Step step, bool heroic)
    {
        switch (step)
        {
            case Step::Heat:    return 0;
            case Step::Hammer:  return kHammerAtMs(heroic);
            case Step::Quench:  return kQuenchAtMs(heroic);
            case Step::Temper:  return kTemperAtMs;
            case Step::Issue:   return kIssueAtMs(heroic);
            default:            return kIssueAtMs(heroic);
        }
    }

    // A step that is a cast (it waits while he dashes or casts): the Hammer and the Temper.
    constexpr bool StepIsCast(Step step)
    {
        return step == Step::Hammer || step == Step::Temper;
    }

    // The piece an order issues: normal alternates, the first a Blade (orders counted from 1); heroic issues both.
    enum PieceMask : std::uint8_t
    {
        PIECE_BLADE = 1,
        PIECE_PLATE = 2,
    };

    constexpr std::uint8_t PiecesOf(std::uint32_t orderNumber, bool heroic)
    {
        if (heroic)
            return PIECE_BLADE | PIECE_PLATE;
        return (orderNumber % 2u) == 1u ? PIECE_BLADE : PIECE_PLATE;
    }

    // AR5 the heroic Temper decides the piece: kicked, flawed; let through, masterwork; never cast (he could not), the
    // standard piece. Normal is always standard.
    enum class Quality : std::uint8_t
    {
        Standard,
        Flawed,
        Masterwork,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 37 normal, H level 60 heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // AR2 Heat: 10 circles of 5 yd (heroic 16 of 4 yd: section 7 #28 A) at random floor spots, centers at least 4 yd
    // apart, never aimed at a player; a 2.5 s marker; 30% (45%) Fire and Weakened.
    inline constexpr NH<std::uint32_t> kSparkCount{ 10, 16 };
    inline constexpr NH<float> kSparkRadiusYd{ 5.f, 4.f };
    inline constexpr float kSparkMinApartYd = 4.f;
    inline constexpr std::uint32_t kSparkWarnMs = 2500;
    inline constexpr NH<float> kSparkPct{ 30.f, 45.f };
    // The picker's best-of-k: each spark takes the candidate farthest from the ones placed (the floor reads as an even
    // shower, not a cluster).
    inline constexpr std::uint32_t kSparkCandidates = 12;

    // AR2a Slag (heroic): a 3 yd pool where each spark lands, 10% Fire a second, until the Quench burst (or this long).
    inline constexpr float kSlagRadiusYd = 3.f;
    inline constexpr std::uint32_t kSlagTickMs = 1000;
    inline constexpr std::uint32_t kSlagMaxMs = 60000;
    inline constexpr float kSlagPct = 10.f;

    // AR3 Hammer: a 2.5 s cast, then the donut (8 yd from the anvil to the walls), then 2 s (heroic 1.5 s) later the
    // anvil circle; each 30% (45%) Physical and Weakened.
    inline constexpr std::uint32_t kHammerCastMs = 2500;
    inline constexpr float kAnvilCircleYd = 8.f;
    inline constexpr float kHammerOuterYd = 60.f;       // past every wall of the storeroom (its far corner: 51 yd)
    inline constexpr NH<std::uint32_t> kHammerFollowUpMs{ 2000, 1500 };
    inline constexpr NH<float> kHammerPct{ 30.f, 45.f };

    // AR4 Quench: steam 10 yd round the trough for 8 s, 8% (12%) Fire a second; lingering, no Weakened. The steam takes
    // a second to roll out (its first tick).
    inline constexpr float kSteamRadiusYd = 10.f;
    inline constexpr std::uint32_t kSteamWarnMs = 1000;
    inline constexpr std::uint32_t kSteamMs = 8000;
    inline constexpr std::uint32_t kSteamTickMs = 1000;
    inline constexpr NH<float> kSteamPct{ 8.f, 12.f };

    // AR4a Slag Burst (heroic): at the Quench every pool swells (a 2.5 s marker) and bursts, 5 yd, 45% Fire and
    // Weakened; the pool is gone.
    inline constexpr float kSlagBurstRadiusYd = 5.f;
    inline constexpr std::uint32_t kSlagBurstWarnMs = 2500;
    inline constexpr float kSlagBurstPct = 45.f;

    // AR5 Temper (heroic): a 2.5 s interruptible cast before the Issue.
    inline constexpr std::uint32_t kTemperCastMs = 2500;
    // The cast has not taken yet this long after the call (the AI waits before reading it as gone).
    inline constexpr std::uint32_t kCastStartGraceMs = 250;

    // AR-Bl Forged Blade: held 15 s (heroic flawed 8, masterwork 25); a 90 degree cleave 8 yd in front of him every
    // 6 s (the first at the Issue), a 1.5 s marker: the tank 15% (25%) of the tank row, anyone else 30% (45%) and
    // Weakened. No swing during a dash chain (a due cleave waits for its end).
    constexpr std::uint32_t BladeMs(bool heroic, Quality quality)
    {
        if (!heroic)
            return 15000;
        return quality == Quality::Flawed ? 8000 : quality == Quality::Masterwork ? 25000 : 15000;
    }
    inline constexpr std::uint32_t kCleaveEveryMs = 6000;
    inline constexpr std::uint32_t kCleaveWarnMs = 1500;
    inline constexpr float kCleaveAngleDeg = 90.f;
    inline constexpr float kCleaveLengthYd = 8.f;
    inline constexpr NH<float> kCleavePct{ 30.f, 45.f };
    inline constexpr NH<float> kCleaveTankPct{ 15.f, 25.f };

    // AR7 Proving Strike: 2 s after the Issue (heroic: then every 10 s while he holds the Blade) a chain of dashes,
    // one per player in a random order, never the same player twice: a 3 yd line from where he stands to 5 yd past the
    // player's spot, the first marked 2 s, every later one 1 s; 30% (45%), the follow-ups 20% (30%), Physical and
    // Weakened. He dashes along each line to its end, the next line starts there. A 6 yd spread lasts the Blade window.
    inline constexpr std::uint32_t kStrikeFirstMs = 2000;
    inline constexpr std::uint32_t kStrikeEveryMs = 10000;      // heroic, from the first chain's start
    inline constexpr float kStrikeWidthYd = 3.f;
    inline constexpr float kStrikeOverrunYd = 5.f;
    inline constexpr std::uint32_t kStrikeFirstWarnMs = 2000;
    inline constexpr std::uint32_t kStrikeNextWarnMs = 1000;
    inline constexpr NH<float> kStrikeFirstPct{ 30.f, 45.f };
    inline constexpr NH<float> kStrikeNextPct{ 20.f, 30.f };
    inline constexpr float kDashSpeed = 30.f;                   // yd/s along a line (Charge's look on him)
    inline constexpr float kBladeSpreadYd = 6.f;
    inline constexpr std::uint32_t kBladeSpreadWarnMs = 1000;
    inline constexpr std::uint32_t kBladeSpreadTickMs = 1000;

    constexpr std::uint32_t StrikeWarnMs(std::uint32_t link)
    {
        return link == 0 ? kStrikeFirstWarnMs : kStrikeNextWarnMs;
    }

    constexpr float StrikePct(std::uint32_t link, bool heroic)
    {
        return link == 0 ? kStrikeFirstPct(heroic) : kStrikeNextPct(heroic);
    }

    // AR7: a dash of `lengthYd` started at `nowMs` is over at this time (30 yd/s plus 200 ms for the spline's end). The
    // next line is marked only once he has landed, so a long dash is never cut by the next line's 1 s marker.
    inline constexpr std::uint32_t kDashLandSlackMs = 200;
    inline constexpr std::uint32_t kDashLandGraceMs = 1500;    // still moving after the plan: wait this much more

    constexpr std::uint64_t DashLandAtMs(std::uint64_t nowMs, float lengthYd)
    {
        float const yd = lengthYd > 0.f ? lengthYd : 0.f;
        return nowMs + static_cast<std::uint64_t>(yd / kDashSpeed * 1000.f) + kDashLandSlackMs;
    }

    // The chains a Blade of `bladeMs` holds: the first at the Issue + 2 s, then (heroic) every 10 s while he holds it.
    constexpr std::uint32_t ChainsIn(std::uint32_t bladeMs, bool heroic)
    {
        if (bladeMs <= kStrikeFirstMs)
            return 0;
        if (!heroic)
            return 1;
        return 1 + (bladeMs - kStrikeFirstMs - 1) / kStrikeEveryMs;
    }

    // AR-Pl Red-Hot Plate: absorbs 5k (heroic 25k; flawed 12.5k, masterwork 50k) until broken; 20% of each absorbed
    // hit burns its attacker back as Fire. Sunder Armor, Expose Armor and Faerie Fire tear off 500 more (no burn).
    constexpr std::uint32_t PlateAbsorb(bool heroic, Quality quality)
    {
        if (!heroic)
            return 5000;
        return quality == Quality::Flawed ? 12500 : quality == Quality::Masterwork ? 50000 : 25000;
    }
    inline constexpr float kBurnBackPct = 20.f;
    inline constexpr std::uint32_t kArmorTear = 500;

    constexpr std::uint32_t BurnBack(std::uint32_t absorbed)
    {
        return static_cast<std::uint32_t>(static_cast<float>(absorbed) * kBurnBackPct / 100.f + 0.5f);
    }

    // AR8 Popping Rivets: one per quarter of the normal plate (1,250), per eighth of the heroic one (3,125: a flawed
    // plate pops 4, a masterwork 16); a 4 yd circle at a random floor spot within 8 yd of a random player, the tank
    // included, a 2 s marker (the rivet's flight), 30% (45%) Fire and Weakened.
    inline constexpr NH<std::uint32_t> kRivetStep{ 1250, 3125 };
    inline constexpr float kRivetRadiusYd = 4.f;
    inline constexpr float kRivetScatterYd = 8.f;
    inline constexpr std::uint32_t kRivetWarnMs = 2000;
    inline constexpr NH<float> kRivetPct{ 30.f, 45.f };

    constexpr std::uint32_t RivetsFor(std::uint32_t plate, bool heroic)
    {
        return plate / kRivetStep(heroic);
    }

    // The rivets due once `broken` of the plate is gone (absorbed or torn), capped at the plate's own count.
    constexpr std::uint32_t RivetsDue(std::uint32_t broken, std::uint32_t plate, bool heroic)
    {
        return std::min(broken, plate) / kRivetStep(heroic);
    }

    // AR6 The Supply Line (heroic): a recruit walks from the crate to the counter (1.5 yd/s), takes the piece at the
    // Issue and walks out (at the run).
    inline constexpr float kRecruitWalkYdPerS = 1.5f;
    inline constexpr std::uint32_t kRecruitLifeMs = 60000;      // the safety net if nobody hands him a piece
    // The look of the issued piece on a recruit and on Crell (creature equipment, stock items): his smith's hammer, the
    // Blade's sword, the plate's shield.
    inline constexpr std::uint32_t kItemSmithHammer = 1903;     // Monster - Mace, Basic Metal Hammer (Godric's)
    inline constexpr std::uint32_t kItemBlade = 5305;           // Monster - Sword, Broadsword Silver Hilt
    inline constexpr std::uint32_t kItemPlateShield = 1984;     // Monster - Shield, Kite Metal

    // The armor tear (AR-Pl): the stock first ranks the spec names. The script also takes any player's spell that
    // lowers his armor (an armor resistance aura with a negative amount), so a reworked rank still tears.
    inline constexpr std::array<std::uint32_t, 4> kArmorTearFirstRanks{ {
        7386,   // Sunder Armor
        8647,   // Expose Armor
        770,    // Faerie Fire
        16857,  // Faerie Fire (Feral)
    } };

    constexpr bool IsNamedArmorTear(std::uint32_t firstRankId)
    {
        for (std::uint32_t const id : kArmorTearFirstRanks)
            if (id == firstRankId)
                return true;
        return false;
    }

    // The fight's length (Build spec "Tuning": effective group DPS 768 N / 3,145 H; the bots do about half).
    inline constexpr std::uint32_t kEffectiveDpsNormal = 768;
    inline constexpr std::uint32_t kEffectiveDpsHeroic = 3145;
    inline constexpr std::uint32_t kCrellHealthNormal = 54000;
    inline constexpr std::uint32_t kCrellHealthHeroic = 270000;

    // ----------------------------------------------------------------------------------------------------------------
    // Pure picks
    // ----------------------------------------------------------------------------------------------------------------

    // A uniformly random floor point: a random walkable cell, jittered inside it. `rand01()` returns [0, 1).
    template <class Rand>
    Vec2 RandomFloorPoint(Rand&& rand01)
    {
        std::size_t const total = FloorCellCount();
        auto pick = static_cast<std::size_t>(rand01() * static_cast<float>(total));
        if (pick >= total)
            pick = total - 1;
        for (std::size_t r = 0; r < kFloorRows; ++r)
            for (std::size_t c = 0; c < kFloorCols; ++c)
                if (IsFloorCell(r, c) && pick-- == 0)
                {
                    Vec2 const center = CellCenter(r, c);
                    float const half = kFloorCellYd * 0.5f;
                    return { center.x + (rand01() * 2.f - 1.f) * half * 0.9f,
                        center.y + (rand01() * 2.f - 1.f) * half * 0.9f };
                }
        return kAnvil.XY();
    }

    // AR2: `count` spark centers on the floor, at least kSparkMinApartYd apart; each the best of kSparkCandidates
    // random floor points (the farthest from those placed), so the shower covers the floor evenly. A candidate closer
    // than the minimum is never taken; after 64 refused rounds the spark is dropped (never in a normal room).
    template <class Rand>
    std::vector<Vec2> PickSparks(std::uint32_t count, Rand&& rand01)
    {
        std::vector<Vec2> out;
        out.reserve(count);
        for (std::uint32_t i = 0; i < count; ++i)
        {
            for (int round = 0; round < 64; ++round)
            {
                bool found = false;
                Vec2 best{};
                float bestNear = -1.f;
                for (std::uint32_t k = 0; k < kSparkCandidates; ++k)
                {
                    Vec2 const p = RandomFloorPoint(rand01);
                    float nearest = 1e9f;
                    for (Vec2 const& q : out)
                        nearest = std::min(nearest, DungeonKit::Distance(p, q));
                    if (nearest < kSparkMinApartYd)
                        continue;
                    if (nearest > bestNear)
                    {
                        bestNear = nearest;
                        best = p;
                        found = true;
                    }
                }
                if (found)
                {
                    out.push_back(best);
                    break;
                }
            }
        }
        return out;
    }

    // AR7: the dash's end: 5 yd past `target` on the line from `from`, walked back toward `from` until it stands on the
    // floor and every point between is floor too (the dash never crosses a wall: it stops at the first gap). A target
    // on `from` gives `from`.
    inline Vec2 DashEnd(Vec2 from, Vec2 target, float overrunYd = kStrikeOverrunYd)
    {
        float const dist = DungeonKit::Distance(from, target);
        if (dist < 0.1f)
            return from;
        float const dx = (target.x - from.x) / dist;
        float const dy = (target.y - from.y) / dist;
        float const length = dist + overrunYd;
        float const stepYd = 0.5f;
        Vec2 last = from;
        for (float s = stepYd; s <= length + 1e-3f; s += stepYd)
        {
            Vec2 const p{ from.x + dx * s, from.y + dy * s };
            if (!IsFloor(p))
                break;
            last = p;
        }
        return last;
    }

    // AR7: where the next line starts: where he really landed when that is on the floor, else the planned end (a
    // landing a hair off a floor cell's edge would otherwise lose the line: DashEnd's first step would be off the
    // floor).
    inline Vec2 ChainFrom(Vec2 landed, Vec2 planned)
    {
        return IsFloor(landed) ? landed : planned;
    }

    // AR8: a rivet's spot, a random floor point within kRivetScatterYd of `around` (16 tries, uniform over the disc),
    // else `around` itself.
    template <class Rand>
    Vec2 RivetSpot(Vec2 around, Rand&& rand01)
    {
        for (int i = 0; i < 16; ++i)
        {
            float const r = kRivetScatterYd * std::sqrt(rand01());
            float const o = rand01() * DungeonKit::kTwoPi;
            Vec2 const p = DungeonKit::Advance(around, o, r);
            if (IsFloor(p))
                return p;
        }
        return around;
    }

    // AR7: a random order of `n` players (Fisher-Yates over 0..n-1). `randBelow(k)` returns [0, k).
    template <class RandBelow>
    std::vector<std::size_t> ChainOrder(std::size_t n, RandBelow&& randBelow)
    {
        std::vector<std::size_t> order(n);
        for (std::size_t i = 0; i < n; ++i)
            order[i] = i;
        for (std::size_t i = n; i > 1; --i)
        {
            auto j = static_cast<std::size_t>(randBelow(static_cast<std::uint32_t>(i)));
            if (j >= i)
                j = i - 1;
            std::swap(order[i - 1], order[j]);
        }
        return order;
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

    // AR1: one order's steps on the AI's clock. Each step is due at T + its offset plus the delay the earlier steps
    // picked up (a cast step waits while he dashes or casts; the ones after it keep their spacing).
    class OrderRun
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t number, bool heroic)
        {
            _active = true;
            _heroic = heroic;
            _number = number;
            _startMs = nowMs;
            _delayMs = 0;
            _step = Step::Heat;
        }

        void Stop()
        {
            _active = false;
            _step = Step::Done;
        }

        bool Active() const { return _active; }
        Step Current() const { return _step; }
        std::uint32_t Number() const { return _number; }
        std::uint64_t StartMs() const { return _startMs; }
        std::uint64_t DelayMs() const { return _delayMs; }

        std::uint64_t DueMs() const { return _startMs + StepAtMs(_step, _heroic) + _delayMs; }
        bool Due(std::uint64_t nowMs) const { return _active && _step != Step::Done && nowMs >= DueMs(); }

        // The current step fired at `nowMs` (late: the later steps move by as much).
        void Fired(std::uint64_t nowMs)
        {
            if (nowMs > DueMs())
                _delayMs += nowMs - DueMs();
            _step = NextStep(_step, _heroic);
            if (_step == Step::Done)
                _active = false;
        }

    private:
        bool _active = false;
        bool _heroic = false;
        std::uint32_t _number = 0;
        std::uint64_t _startMs = 0;
        std::uint64_t _delayMs = 0;
        Step _step = Step::Done;
    };
}

#endif
