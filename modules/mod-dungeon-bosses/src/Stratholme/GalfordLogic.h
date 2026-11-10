/*
 * mod-dungeon-bosses, Stratholme S6: Archivist Galford (10811), "the censor who burns the hall down around the
 * heretics", the pure, host-testable part (no engine headers). Build spec ST 1707-1765
 * (docs/dungeons/stratholme-rework.md, the whole "Archivist Galford" section), handoff sections 3.4 rows GF, 3.5 row
 * S6, 3.6 and 3.8 (the hall and its seals). Tested by tests/strat_galford_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsGalford (206520-206544), declared in apps/dbc-tools
 *                 source/npcs/stratholme/archivist_galford.py
 *   Tuning        NH<> constants: one number per difficulty, straight from the build spec
 *   Holy fire     GF7 the union tick (8% a second, x (1 + 0.25 per Scorched stack)), GF8 Scorched, GF9 Kindled
 *   Walls         GF10 the Pyre and the north wall (DungeonKit::LethalWall lines), what they keep clear (the archive,
 *                 the tank spots, the pull grip's landings), the stalkers that carry their look
 *   The hall      the floor outline the drop spot rule and the tank's Park pick use ([navmesh estimate])
 *   Burning Winds GF11 (heroic) the gust's per-player throw, cut short of the Pyre (KT-2: a wall strikes anyone whose
 *                 movement crosses it, knockbacks included)
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_GALFORD_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_GALFORD_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "DungeonKitWallLogic.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace StratGalford
{
    using DungeonKit::Box2;
    using DungeonKit::KeepClear;
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using DungeonKit::WallLine;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsGalford;

    enum GalfordSpells : std::uint32_t
    {
        SPELL_GF_HOLY_FIRE          = kSpellSlice.first + 0,    // 206520 GF1 the 6 s burn on the target (no dispel)
        SPELL_GF_HOLY_FIRE_LANDING  = kSpellSlice.first + 1,    // 206521 GF2 the landing on others (resolve copy)
        SPELL_GF_PYROBLAST          = kSpellSlice.first + 2,    // 206522 GF3 the 4 s cast at the tank (kickable)
        SPELL_GF_FIRE_NOVA_CAST     = kSpellSlice.first + 3,    // 206523 GF5 the 2 s cast bar
        SPELL_GF_FIRE_NOVA          = kSpellSlice.first + 4,    // 206524 GF5 the burst (resolve copy)
        SPELL_GF_FIRE_NOVA_LOOK     = kSpellSlice.first + 5,    // 206525 GF5 the burst's look on him (self visual)
        SPELL_GF_HOLY_FIRE_TICK     = kSpellSlice.first + 6,    // 206526 GF7 the holy fire tick (per Scorched stack)
        SPELL_GF_SCORCHED           = kSpellSlice.first + 7,    // 206527 GF8 Scorched, a stack a second in fire
        SPELL_GF_KINDLED            = kSpellSlice.first + 8,    // 206528 GF9 Kindled on him while he stands in fire
        SPELL_GF_BURNING_WINDS      = kSpellSlice.first + 9,    // 206529 GF11 heroic: the 2 s cast bar
        SPELL_GF_GUST               = kSpellSlice.first + 10,   // 206530 GF11 the gust's look on each player thrown
        SPELL_GF_PUDDLE_LOOK_4      = kSpellSlice.first + 11,   // 206531 GF7 a puddle's look, 4 yd (Holy Fire)
        SPELL_GF_PUDDLE_LOOK_5      = kSpellSlice.first + 12,   // 206532 GF7 5 yd (Fire Nova)
        SPELL_GF_PUDDLE_LOOK_6      = kSpellSlice.first + 13,   // 206533 GF7 6 yd (Pyroblast, normal)
        SPELL_GF_PUDDLE_LOOK_8      = kSpellSlice.first + 14,   // 206534 GF7 8 yd (Pyroblast, heroic)
        SPELL_GF_WALL_LOOK          = kSpellSlice.first + 15,   // 206535 GF10 the walls' fire (a stalker's state)
        // 206536-206544 spare
    };
    static_assert(SPELL_GF_WALL_LOOK <= kSpellSlice.last, "Galford's spells must stay in his slice");
    // The walls' strike is the shared StratholmeRework::SPELL_ST_CROSSED_THE_LINE (206400), never a copy here.

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum GalfordTags : std::uint32_t
    {
        TAG_HOLY_FIRE       = 1,    // GF1 / GF2 the circle on the target and its landing
        TAG_PYROBLAST       = 2,    // GF3 / GF4 the puddle-to-be on the tank (telegraph-only, the tank's drop spot)
        TAG_NOVA            = 3,    // GF5 the ring on him
        TAG_FIRE            = 4,    // GF7 a holy fire puddle (telegraph-only persistent zone of the PuddleField)
        TAG_WALL            = 5,    // GF10 the Pyre and the north wall (DungeonKit::LethalWall)
        TAG_WINDS           = 6,    // GF11 the puddles shifted north during the cast (telegraph-only)
        TAG_PARK            = 7,    // GF9 the tank's Park circle on clean floor (no marker, the tank only)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 1707-1765; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // GF1 Holy Fire / GF2 its landing
    inline constexpr std::uint32_t kHolyFireFirstMs = 5000;
    inline constexpr NH<std::uint32_t> kHolyFireEveryMs{ 8000, 12000 };
    inline constexpr NH<std::uint32_t> kHolyFireCount{ 1, 3 };      // different non-tanks
    inline constexpr std::uint32_t kHolyFireBurnMs = 6000;          // the burn, and the circle following the target
    inline constexpr float kHolyFireRadius = 4.f;
    inline constexpr float kHolyFireLandingPct = 30.f;              // others inside it + Weakened
    inline constexpr float kHolyFireBurnPct = 10.f;                 // the target, over the 6 s (206520's ticks)
    inline constexpr std::uint32_t kHolyFireTickMs = 1000;
    // 206520's tick in hundredths (spell_dungeon_refflat_periodic): 6 ticks of 167 = 10.02%.
    inline constexpr std::uint32_t kHolyFireTickHundredths = 167;
    static_assert(kHolyFireTickHundredths * (kHolyFireBurnMs / kHolyFireTickMs) >= 1000
        && kHolyFireTickHundredths * (kHolyFireBurnMs / kHolyFireTickMs) <= 1005, "the burn is 10% over 6 s");

    // GF3 Pyroblast / GF4 its puddle
    inline constexpr std::uint32_t kPyroFirstMs = 15000;
    inline constexpr std::uint32_t kPyroEveryMs = 20000;
    inline constexpr std::uint32_t kPyroCastMs = 4000;              // 206522's cast time (stock 6 s)
    inline constexpr NH<float> kPyroPct{ 35.f, 45.f };              // the tank row, not avoidable
    inline constexpr NH<float> kPyroPuddleRadius{ 6.f, 8.f };
    inline constexpr std::uint8_t kPyroKickPriority = 3;            // handoff 3.4: priority 3, every 20 s
    // The puddle-to-be follows the tank a little past the cast's end (the missile's flight); the hit places it.
    inline constexpr std::uint32_t kPyroMarkerTailMs = 500;
    // A hit that never came (the tank died, the missile missed): the marker and the turn are freed this long after.
    inline constexpr std::uint32_t kPyroLandGraceMs = 3000;

    // GF5 Fire Nova / GF6 its puddle
    inline constexpr std::uint32_t kNovaFirstMs = 12000;
    inline constexpr std::uint32_t kNovaEveryMs = 15000;
    inline constexpr std::uint32_t kNovaCastMs = 2000;              // 206523's cast time = the ring's warning
    inline constexpr float kNovaRadius = 10.f;
    inline constexpr float kNovaPct = 30.f;                         // + Weakened, the tank too
    inline constexpr float kNovaPuddleRadius = 5.f;

    // GF7 holy fire (the union of every puddle, until he dies or the group wipes)
    inline constexpr std::uint32_t kFireArmMs = 1000;               // a new puddle burns 1 s after it lands
    inline constexpr std::uint32_t kFireTickMs = 1000;              // once a second, however many overlap
    inline constexpr float kFireTickPct = 8.f;
    inline constexpr float kScorchedPerStack = 0.25f;               // GF8 +25% holy fire damage per stack
    inline constexpr std::uint32_t kScorchedFadeMs = 4000;          // 206527's duration: refreshed by each stack
    inline constexpr std::uint32_t kScorchedMaxStacks = 20;         // 206527's CumulativeAura (8 s in fire kills)

    // GF9 Kindled
    inline constexpr std::uint32_t kKindledPollMs = 250;
    inline constexpr std::uint32_t kKindledAuraMs = 1000;           // 206528's duration: gone 1 s after he leaves
    inline constexpr float kKindledDamageDonePct = 25.f;
    inline constexpr float kKindledDamageTakenPct = -50.f;
    // His custom hits ignore caster modifiers, so the +25% reaches Pyroblast through its own script.
    inline constexpr float kKindledPyroFactor = 1.f + kKindledDamageDonePct / 100.f;

    // GF9 the tank rule (the bots): keep him out of fire. Every kParkCheckMs, when he stands within kParkTriggerPadYd
    // of a puddle's edge (or in it), a tank-only Park circle on clean floor kParkMinYd..kParkMaxYd from him.
    inline constexpr std::uint32_t kParkCheckMs = 1000;
    inline constexpr std::uint32_t kParkHoldMs = 5000;
    inline constexpr std::uint32_t kParkCooldownMs = 1000;
    inline constexpr float kParkTriggerPadYd = 1.5f;
    inline constexpr float kParkRadius = 3.f;
    inline constexpr float kParkMinYd = 5.f;
    inline constexpr float kParkMaxYd = 15.f;
    inline constexpr float kParkClearYd = 2.5f;                     // the spot this far off every puddle's edge

    // GF11 Burning Winds (heroic)
    inline constexpr std::uint32_t kWindsFirstMs = 20000;
    inline constexpr std::uint32_t kWindsEveryMs = 25000;
    inline constexpr std::uint32_t kWindsCastMs = 2000;             // 206529's cast time = the offset shapes' warning
    inline constexpr std::uint32_t kGustLookMs = 1000;              // 206530's duration (the throw's flight)
    inline constexpr float kWindsPushYd = 8.f;                      // south, toward the Pyre
    inline constexpr float kWindsShiftFacing = 0.f;                 // the puddles' offset shapes reach north
    inline constexpr float kGustMarginYd = 2.f;                     // a throw stops this far short of the Pyre's strip
    inline constexpr float kGustMinYd = 1.f;                        // a shorter throw is skipped
    inline constexpr float kGustSpeedZ = 9.65f;                     // about a 1 s flight (the 1 s loss of control)
    inline constexpr float kGravity = 19.29110527038574f;           // Movement::gravity
    inline constexpr std::size_t kWindsMaxPuddles = 40;             // offset shapes for at most this many puddles

    // His casts never overlap (DungeonKit::CastQueue); Holy Fire is no cast and runs through them.
    enum GalfordCasts : std::uint32_t
    {
        CAST_PYROBLAST      = 1,
        CAST_NOVA           = 2,
        CAST_WINDS          = 3,
    };
    inline constexpr std::uint8_t kPriorityWinds = 3;
    inline constexpr std::uint8_t kPriorityPyro = 2;
    inline constexpr std::uint8_t kPriorityNova = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // GF7 / GF8 the holy fire tick
    // ----------------------------------------------------------------------------------------------------------------

    // The tick's percent for a player carrying `stacks` Scorched before this tick (the tick then adds one): 8, 10, 12,
    // ... Crossing one puddle (two ticks) costs 18%; eight seconds in fire, 120%.
    constexpr float FireTickPct(std::uint32_t stacks)
    {
        return kFireTickPct * (1.f + kScorchedPerStack * static_cast<float>(std::min(stacks, kScorchedMaxStacks)));
    }

    // The sum of `ticks` ticks from no stacks (a player who stays in the fire).
    constexpr float FireBurnPct(std::uint32_t ticks)
    {
        float sum = 0.f;
        for (std::uint32_t i = 0; i < ticks; ++i)
            sum += FireTickPct(i);
        return sum;
    }

    // Pyroblast's percent: the difficulty's, raised by Kindled.
    constexpr float PyroPct(bool heroic, bool kindled)
    {
        return kPyroPct(heroic) * (kindled ? kKindledPyroFactor : 1.f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hall (handoff 3.8 row Galford; stratholme-build.NAVMESH-REPORT.md section 6) [navmesh estimate]
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kHallFloorZ = 135.4f;
    inline constexpr float kPyreFloorZ = 135.2f;
    inline constexpr float kNorthFloorZ = 135.4f;
    inline constexpr float kHallZMin = 134.0f;                      // the hall 135.2..135.7, the archive to 138.7
    inline constexpr float kHallZMax = 140.0f;

    // GF10 the Pyre: the measured seal (StratholmeRework.h kGalfordPyre, x 3446) drawn 2 yd farther south, so its
    // strip keeps 5 yd off the archive's door (x 3448..3452; the placement rule) and the hall still closes: the
    // navmesh flood with the line at x 3444 holds 1,439 sq yd and reaches neither Dathrohan's chamber (its door at
    // x 3436..3441) nor the north (S6 seal check). The north wall is the measured line as it is.
    inline constexpr float kPyreSouthShiftYd = 2.f;
    inline constexpr float kWallWidthYd = DungeonKit::kWallDefaultWidthYd;

    inline WallLine PyreLine()
    {
        return { { StratholmeRework::kGalfordPyre[0].x - kPyreSouthShiftYd, StratholmeRework::kGalfordPyre[0].y },
            { StratholmeRework::kGalfordPyre[1].x - kPyreSouthShiftYd, StratholmeRework::kGalfordPyre[1].y },
            kWallWidthYd };
    }

    inline WallLine NorthLine()
    {
        return { StratholmeRework::kGalfordNorthWall[0], StratholmeRework::kGalfordNorthWall[1], kWallWidthYd };
    }

    // The arena the guard holds (the leash and the pull grip): the hall frame (StratholmeRework::GalfordArena's box,
    // Y to -13 for his spawn by the archive) cut kArenaWallGapYd (2 yd) short of both walls' strips (F-2 ruling): the
    // Pyre's strip x 3443..3445 (frame X -3..-1) and the north wall's x 3499..3501 (X 53..55), so the guard holds X
    // 1..51 and a player standing in a strip (or within 2 yd of it) at the pull is gripped clear before it arms; and
    // reaching Y 46 (y -3046): the sealed floor's west bay (x 3470..3494, y -3049..-3060,
    // the report's "closed side room") is hall too, so a tank who walks him there is not leashed.
    inline constexpr float kGuardMinX = 1.f;                        // frame X 1: x 3447, 2 yd off the Pyre's strip
    inline constexpr float kGuardMaxX = 51.f;                       // frame X 51: x 3497, 2 yd off the north strip
    inline constexpr float kGuardMaxY = 46.f;                       // frame Y 46: y -3046
    inline DungeonKit::Arena GuardArena()
    {
        using StratholmeRework::kGalfordHall;
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Frame(kGalfordHall,
            Box2{ kGuardMinX, kGuardMaxX, -13.f, kGuardMaxY }, 135.0f, 139.0f));
    }

    // The pull's reach (F-2 ruling): the pull puts in combat only the units its grip reaches (the guard's maxGripYd
    // is this too). BossAI's zone-in (250 yd, and its 5 s combat pulse) would leave a player 120-250 yd away in
    // combat, never gripped, and locked out by the north wall. It covers the whole guarded hall from anywhere in it.
    inline constexpr float kPullRadiusYd = 120.f;

    // The hall's floor outline (the navmesh flood between the seals, z 133..140, read every 2 yd of x), kept 2 yd off
    // both walls' strips: the drop spot rule's room (its edge is the hall's walls) and the tank's Park floor. It
    // leaves out the archive and the book alcove (their own areas below). East side from the Pyre north, then the
    // west side back south.
    inline constexpr std::array<Vec2, 33> kHallRoom{ {
        { 3447.0f, -3097.5f }, { 3450.5f, -3095.5f }, { 3454.0f, -3093.0f }, { 3456.5f, -3092.5f },
        { 3457.5f, -3084.0f }, { 3462.0f, -3083.0f }, { 3466.0f, -3086.0f }, { 3468.0f, -3083.0f },
        { 3472.0f, -3080.0f }, { 3474.5f, -3080.0f }, { 3476.0f, -3070.5f }, { 3480.5f, -3070.5f },
        { 3482.0f, -3086.0f }, { 3486.0f, -3089.5f }, { 3490.0f, -3087.0f }, { 3494.0f, -3086.0f },
        { 3497.0f, -3087.5f },
        { 3497.0f, -3070.5f }, { 3495.0f, -3071.0f }, { 3494.0f, -3058.5f }, { 3490.0f, -3055.0f },
        { 3488.0f, -3050.5f }, { 3484.0f, -3052.5f }, { 3478.0f, -3049.0f }, { 3476.0f, -3052.0f },
        { 3472.0f, -3054.5f }, { 3470.0f, -3053.5f }, { 3468.5f, -3063.5f }, { 3460.5f, -3061.0f },
        { 3458.0f, -3064.5f }, { 3452.0f, -3065.5f }, { 3451.0f, -3075.5f }, { 3447.0f, -3077.0f } } };

    // The Scarlet Archive (his room, x 3449..3465, y -3096..-3111; its door into the hall's south-east corner at x
    // 3448..3452) and the book alcove (x 3472..3478, y -3085..-3097): the best early places to drop fire (ST). The
    // drop areas stop at the arena's Y -13 (y -3105); kArchiveRoom is the whole room (the "Not the archive!" yell).
    inline constexpr Box2 kArchiveRoom{ 3448.0f, 3466.0f, -3112.0f, -3096.0f };
    inline constexpr Box2 kArchiveDrop{ 3451.5f, 3464.0f, -3104.5f, -3097.0f };
    inline constexpr Box2 kAlcoveDrop{ 3471.5f, 3478.0f, -3096.0f, -3087.0f };
    inline constexpr Vec2 kArchiveDoor{ 3450.0f, -3096.5f };

    // Where the pull grip lands a unit off the arena (the one nearest to where it was): each on hall floor and at
    // least 7 yd from either wall's strip (KT-2: the grip lands 5 yd inside the walls at least).
    inline constexpr std::array<Vec2, 4> kGripLandings{ {
        { 3452.5f, -3088.0f },      // the archive's mouth (a unit south of the Pyre, in Dathrohan's chamber)
        { 3465.0f, -3074.0f },      // mid hall
        { 3485.0f, -3068.0f },      // north hall, west of the pillar
        { 3492.0f, -3076.0f } } };  // the north stand (a unit north of the north wall)

    // Where a tank holds him through the fight as it marches north (the placement rule's "tank spots").
    inline constexpr std::array<Vec2, 5> kTankSpots{ {
        { 3455.96f, -3103.41f },    // his spawn, by the archive (the pull)
        { 3452.5f, -3088.0f }, { 3465.0f, -3074.0f }, { 3485.0f, -3068.0f }, { 3492.0f, -3076.0f } } };

    inline bool InHallRoom(Vec2 p)
    {
        return DungeonKit::PointInPolygon(std::span<Vec2 const>(kHallRoom), p);
    }

    // The fight's floor: the hall, the archive's drop area or the alcove's.
    inline bool OnFightFloor(Vec2 p)
    {
        return InHallRoom(p) || kArchiveDrop.Contains(p) || kAlcoveDrop.Contains(p);
    }

    // The nearest grip landing to where the unit was.
    inline Vec2 GripLanding(Vec2 from)
    {
        Vec2 best = kGripLandings[0];
        float bestD = DungeonKit::Distance(from, best);
        for (Vec2 const& p : kGripLandings)
        {
            float const d = DungeonKit::Distance(from, p);
            if (d < bestD)
            {
                bestD = d;
                best = p;
            }
        }
        return best;
    }

    // What the walls keep clear by the placement rule (5 yd off each strip): the archive (its door, the Scarlet
    // Archive), the tank spots (his spawn first) and the grip landings.
    inline std::vector<KeepClear> WallKeepClear()
    {
        std::vector<KeepClear> keep;
        keep.push_back(KeepClear::Point(kArchiveDoor, 0.f));
        keep.push_back(KeepClear::Point(StratholmeRework::kScarletArchive.XY(), 0.f));    // 176245
        for (Vec2 const& p : kTankSpots)
            keep.push_back(KeepClear::Point(p, 0.f));
        for (Vec2 const& p : kGripLandings)
            keep.push_back(KeepClear::Point(p, 0.f));
        return keep;
    }

    // The fire stalkers along a wall (one every `spacingYd` or less, at the centers of equal pieces): the look
    // (Fire Wall 43113's 6 yd wave) and the strike's casters.
    inline constexpr float kWallStalkerSpacingYd = 6.f;

    inline std::vector<Vec2> WallStalkerSpots(WallLine const& w, float spacingYd = kWallStalkerSpacingYd)
    {
        std::vector<Vec2> out;
        float const len = w.Length();
        if (len <= 0.f || spacingYd <= 0.f)
            return out;
        std::size_t const n = std::max<std::size_t>(1, static_cast<std::size_t>(std::ceil(len / spacingYd)));
        for (std::size_t i = 0; i < n; ++i)
        {
            float const t = (static_cast<float>(i) + 0.5f) / static_cast<float>(n);
            out.push_back({ w.from.x + (w.to.x - w.from.x) * t, w.from.y + (w.to.y - w.from.y) * t });
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF7 the puddles' looks
    // ----------------------------------------------------------------------------------------------------------------

    // The HolyZone look of a puddle of `radius` (the nearest of the four sizes V-2 minted).
    constexpr std::uint32_t PuddleLookFor(float radius)
    {
        if (radius < 4.5f)
            return SPELL_GF_PUDDLE_LOOK_4;
        if (radius < 5.5f)
            return SPELL_GF_PUDDLE_LOOK_5;
        if (radius < 7.f)
            return SPELL_GF_PUDDLE_LOOK_6;
        return SPELL_GF_PUDDLE_LOOK_8;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF9 the tank rule
    // ----------------------------------------------------------------------------------------------------------------

    struct PuddleSpot
    {
        Vec2 center;
        float radius = 0.f;
    };

    // He stands in a puddle or within kParkTriggerPadYd of its edge: time to walk him out.
    inline bool ShouldPark(Vec2 boss, std::span<PuddleSpot const> puddles)
    {
        for (PuddleSpot const& p : puddles)
            if (DungeonKit::Distance(boss, p.center) <= p.radius + kParkTriggerPadYd)
                return true;
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF11 Burning Winds: the gust
    // ----------------------------------------------------------------------------------------------------------------

    // How far the gust throws a player standing at `x` (south, toward the Pyre): the full 8 yd, cut so the landing
    // stays kGustMarginYd north of the Pyre's strip; 0 (no throw) when that leaves less than kGustMinYd. The cut uses
    // x alone, so a player past either end of the Pyre is cut too (the archive's south wall stops them anyway).
    inline float GustDistance(float x, WallLine const& pyre)
    {
        float const stripNorth = std::max(pyre.from.x, pyre.to.x) + pyre.HalfWidth();
        float const room = x - stripNorth - kGustMarginYd;
        float const d = std::min(kWindsPushYd, room);
        return d >= kGustMinYd ? d : 0.f;
    }

    inline float GustDistance(float x)
    {
        return GustDistance(x, PyreLine());
    }

    // Unit::KnockbackFrom's horizontal speed that throws a unit `distance` yards with vertical speed `speedZ`
    // (MotionMaster::MoveKnockbackFrom: distance = 2 * speedXY * speedZ / gravity).
    constexpr float KnockbackSpeedXY(float distance, float speedZ = kGustSpeedZ)
    {
        return speedZ > 0.f ? distance * kGravity / (2.f * speedZ) : 0.f;
    }

    constexpr float KnockbackDistance(float speedXY, float speedZ = kGustSpeedZ)
    {
        return 2.f * speedXY * speedZ / kGravity;
    }

    // The throw's flight (the loss of control), in seconds.
    constexpr float KnockbackFlightS(float speedZ = kGustSpeedZ)
    {
        return 2.f * speedZ / kGravity;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Pyroblast's yell: "Burn, heretic!" now and then (the first cast, then every other one)
    // ----------------------------------------------------------------------------------------------------------------

    constexpr bool PyroYells(std::uint32_t castNumber)
    {
        return castNumber % 2 == 1;
    }
}

#endif
