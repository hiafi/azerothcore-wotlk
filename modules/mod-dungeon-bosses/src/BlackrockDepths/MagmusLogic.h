/*
 * mod-dungeon-bosses, Blackrock Depths D22:
 * Magmus (9938) and the six Ironhand Guardians (8982), the pure, host-testable part (no engine headers). Build spec S4
 * "Magmus" (docs/dungeons/blackrock-depths-4-imperial-seat.md, MG1-MG5; rulings 75, 76, 88), handoff sections 3.4
 * (row D22), 3.5, 3.8 (NM: the Iron Hall), 3.9 (the `crossfire` row of `blackrock-depths-shapes-2`, tags 25-27),
 * section 8 #26. Tested by tests/brd_magmus_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsMagmus (211580-211609), declared in apps/dbc-tools
 *                source/npcs/blackrock_depths/magmus.py
 *   Tuning       NH<> constants straight from the build spec (normal / heroic); the unset "stock rescaled" cells
 *                (War Stomp) are this WP's defaults (report, designer questions)
 *   Geometry     the hall (NM x 1361.2-1400.2, 39 yd), the six statues, the Crossfire lane (one lane wall to wall at
 *                his y at the fist raise: section 8 #26), the Flame Wall strips (12 yd of floor along a wall, plus the
 *                alcoves behind it so nobody hides in one)
 *   Timeline     the four clocks (War Stomp, Fiery Burst, Crossfire, Flame Wall) and the rule "nothing holds the
 *                group in a lane": a stomp or a Fiery Burst cast waits while a Crossfire's glow is up or about to
 *                start. The engine runs this very struct; the test replays 300 s of it
 *   Dripping Magma (heroic) the walk tracker and the pool cap
 *
 * Axes: x north, y west (NAVMESH-REPORT). The spec's "west column" of statues is the low-x one (x about 1353), the
 * "east column" the high-x one (x about 1407); this file says low-x and high-x. Orientation 0 looks along +x, pi / 2
 * along +y, so the hall's long axis from the entrance (y -550) to the throne door (y -720) is orientation 3 pi / 2.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_MAGMUS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_MAGMUS_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace BrdMagmus
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsMagmus;

    enum MagmusSpells : std::uint32_t
    {
        SPELL_MG_WAR_STOMP          = kSpellSlice.first + 0,    // 211580 MG1 the stomp: a hit and a 2 s stun (15593)
        SPELL_MG_FIERY_BURST_CAST   = kSpellSlice.first + 1,    // 211581 MG2 the 2 s interruptible bar on the target
        SPELL_MG_FIERY_BURST        = kSpellSlice.first + 2,    // 211582 MG2 the circle's hit (resolve copy, Fire)
        SPELL_MG_FIERY_BURST_LOOK   = kSpellSlice.first + 3,    // 211583 look: Fiery Burst's blast at the circle
        SPELL_MG_CROSSFIRE_IGNITION = kSpellSlice.first + 4,    // 211584 MG3 the lane's ignition (resolve copy, Fire)
        SPELL_MG_CROSSFIRE_BURN     = kSpellSlice.first + 5,    // 211585 MG3 the lane's burn tick (resolve copy, Fire)
        SPELL_MG_FLAME_WALL         = kSpellSlice.first + 6,    // 211586 MG4 the strip's tick (resolve copy, Fire)
        SPELL_MG_DRIPPING_MAGMA     = kSpellSlice.first + 7,    // 211587 MG5 a pool's tick (resolve copy, Fire)
        SPELL_MG_STATUE_GLOW        = kSpellSlice.first + 8,    // 211588 look: a statue glows (an aura on the statue)
        SPELL_MG_STATUE_BREATH      = kSpellSlice.first + 9,    // 211589 look: a statue's breath at a point
        SPELL_MG_CROSSFIRE_END_LOOK = kSpellSlice.first + 10,   // 211590 look: the burst at a lane's end
        SPELL_MG_POOL_LOOK          = kSpellSlice.first + 11,   // 211591 look: a pool (an aura on a stalker)
        // 211592-211609 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_MG_POOL_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "Magmus's spells must stay in his slice");

    // Registry tags. 25, 26 and 27 are the G2 drill's `crossfire` and Flame Wall rows (BM MechanicDrill.h
    // kBrd2BarTags, gated at 1: the bots' follow-ups are tuned on exactly these shapes); the others are this fight's.
    enum MagmusTags : std::uint32_t
    {
        TAG_MG_FIERY_BURST        = 1,      // MG2
        TAG_MG_DRIPPING_MAGMA     = 2,      // MG5
        TAG_MG_CROSSFIRE_IGNITION = 25,     // MG3 the ignition (drill row `crossfire`, Zone/25)
        TAG_MG_CROSSFIRE_BURN     = 26,     // MG3 the burn (Zone/26)
        TAG_MG_FLAME_WALL         = 27,     // MG4 (drill row Flame Wall, Zone/27)
    };

    // creature_text groups of 9938 (S4 "Text"): 0 is the stock braziers yell (the instance says it), 1-3 are new. 1 is
    // a boss emote (type 41, rule 2), 2 and 3 yells; all map-wide (TextRange 3), the hall being 170 yd long.
    enum MagmusTexts : std::uint8_t
    {
        SAY_MAGMUS_BRAZIERS_LIT = 0,    // stock (the instance sends it)
        EMOTE_MAGMUS_FIST       = 1,    // MG3 "Magmus raises his fist, and the Ironhand Guardians turn!"
        YELL_MAGMUS_WALL        = 2,    // MG4 "Burn in the Emperor's hall!"
        YELL_MAGMUS_DEATH       = 3,    // "The Emperor... will not... be disturbed..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    // MG1 War Stomp: stock 15593 (5 yd round him, a hit and a stun), rescaled: the stun drops from 8 s to 2 s (ruling
    // 76, the 2 s rule). Stock timers: first at 8-12 s, then every 8-12 s. The hit is "stock rescaled" in the spec
    // (gap 36): this WP's default is a group pulse of the BRS convention (designer question 1). Everyone within 5 yd,
    // the tank too (stock).
    inline constexpr NH<float> kStompPct{ 12.f, 15.f };
    inline constexpr float kStompRadiusYd = 5.f;
    inline constexpr std::uint32_t kStompStunMs = 2000;
    inline constexpr std::uint32_t kStompEveryMinMs = 8000;
    inline constexpr std::uint32_t kStompEveryMaxMs = 12000;

    // MG2 Fiery Burst: a 2 s interruptible cast on a random player, the tank included (ruling 88 over 76), an 8 yd
    // circle fixed where that player stands when the cast starts, 25% / 40% + Weakened. First at 6 s, then every 10 s.
    inline constexpr NH<float> kBurstPct{ 25.f, 40.f };
    inline constexpr float kBurstRadiusYd = 8.f;
    inline constexpr std::uint32_t kBurstCastMs = 2000;
    inline constexpr std::uint32_t kBurstFirstMs = 6000;
    inline constexpr std::uint32_t kBurstEveryMs = 10000;
    inline constexpr float kBurstRangeYd = 40.f;

    // MG3 Crossfire: first at 8 s, then every 15 s (heroic 12 s). He raises a fist (emote line 1); the statue pair
    // nearest his y turns to the lane and glows for 3 s; then a 10 yd lane wall to wall at his y (locked when the fist
    // goes up) ignites (30% / 45% + Weakened) and burns 10% / 15% a second. G2's drill row: the ignition at 3 s
    // (warn 3000), the burn's first tick 1 s later (warn 4000) for 5 s (persist 5000, tick 1000): 6 hits of the burn
    // with the ignition. The statues breathe from the ignition on, a fresh breath every kBreathEveryMs.
    inline constexpr NH<float> kCrossfireIgnitionPct{ 30.f, 45.f };
    inline constexpr NH<float> kCrossfireBurnPct{ 10.f, 15.f };
    inline constexpr float kLaneWidthYd = 10.f;
    inline constexpr float kLaneOverrunYd = 1.5f;       // the lane runs statue to statue plus this at each end
    inline constexpr std::uint32_t kCrossfireFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kCrossfireEveryMs{ 15000, 12000 };
    inline constexpr std::uint32_t kGlowMs = 3000;              // the warning: the ignition lands this long after
    inline constexpr std::uint32_t kBurnWarnMs = 4000;          // the burn's first tick
    inline constexpr std::uint32_t kBurnLifeMs = 5000;          // ... and the 5 s it ticks
    inline constexpr std::uint32_t kBurnTickMs = 1000;
    inline constexpr std::uint32_t kCrossfireEndMs = kBurnWarnMs + kBurnLifeMs;   // 9 s: the last tick
    inline constexpr std::uint32_t kBreathEveryMs = 2000;       // a one-shot breath look is cast again every 2 s

    // MG4 Flame Wall: first at 20 s, then every 30 s (heroic 25 s); yell line 2. One whole statue row glows 3 s, then
    // breathes along the hall: the 12 yd strip of floor along that wall burns 8 s, 10% / 15% a second, no ignition
    // hit. The strip is drawn 8 yd wider on the wall side so the alcoves behind the row are no hiding place.
    inline constexpr NH<float> kWallPct{ 10.f, 15.f };
    inline constexpr float kWallStripYd = 12.f;
    inline constexpr float kWallOutsetYd = 8.f;                 // the alcoves are 7.6 yd deep (NM 4.5)
    inline constexpr std::uint32_t kWallFirstMs = 20000;
    inline constexpr NH<std::uint32_t> kWallEveryMs{ 30000, 25000 };
    inline constexpr std::uint32_t kWallLifeMs = 8000;
    inline constexpr std::uint32_t kWallTickMs = 1000;
    inline constexpr std::uint32_t kWallEndMs = kGlowMs + kWallLifeMs;      // 11 s from the glow to the last tick
    inline constexpr float kWallBreathReachYd = 20.f;           // each statue breathes this far down the row
    // The strip is never laid on the side whose floor he stands on (plus his body), so the tank is not asked to move
    // him before the strip lands.
    inline constexpr float kWallBodyMarginYd = 4.f;

    // MG5 Dripping Magma (heroic only): while he walks, every 3 s of walking a 4 yd lava pool under him, 30 s, 8% a
    // second. At most 6 stand at once (the spec's "about 6, about 300 sq yd"): a seventh retires the oldest. The first
    // tick lands kPoolWarnMs after the drop (the outline shows meanwhile), so melee at his feet can step out.
    inline constexpr float kPoolPct = 8.f;
    inline constexpr float kPoolRadiusYd = 4.f;
    inline constexpr std::uint32_t kPoolEveryMs = 3000;
    inline constexpr std::uint32_t kPoolLifeMs = 30000;
    inline constexpr std::uint32_t kPoolWarnMs = 1500;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr std::size_t kPoolCap = 6;
    inline constexpr float kWalkSpeedYdPerS = 1.0f;             // moving faster than this counts as walking
    inline constexpr float kWalkedMinYd = 2.5f;                 // and he must have covered this since the last pool
    inline constexpr std::uint32_t kStandStillResetMs = 1500;   // standing this long forgets the distance walked

    inline constexpr std::uint32_t kRetryMs = 1000;             // a refused start tries again this soon

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry (NM 4.5, handoff section 3.8): the Iron Hall
    // ----------------------------------------------------------------------------------------------------------------

    // The open floor, 39 yd across (the spec said 34; NM measured x 1361.2 to 1400.2). MagmusArena() (the leash box)
    // is x 1360-1401, y -720 to -550.
    inline constexpr float kHallLowX = 1361.2f;
    inline constexpr float kHallHighX = 1400.2f;
    inline constexpr float kHallCenterX = (kHallLowX + kHallHighX) / 2.f;
    inline constexpr float kHallYMax = -550.f;      // the entrance end
    inline constexpr float kHallYMin = -720.f;      // the throne end (the throne door stands at -710.5)
    inline constexpr float kFacingAlongX = 0.f;
    inline constexpr float kFacingToThrone = 3.f * DungeonKit::kPi / 2.f;   // along -y, the hall's long axis

    // The six statues [DB], two columns of three. Rows by y (the two columns differ by 0.4 yd; the mean).
    inline constexpr float kStatueLowX = 1353.4f;
    inline constexpr float kStatueHighX = 1407.3f;
    inline constexpr std::size_t kStatueRows = 3;
    inline constexpr std::array<float, kStatueRows> kStatueRowY{ { -587.3f, -632.6f, -677.55f } };
    inline constexpr float kStatueZ = -91.97f;

    enum class Side : std::uint8_t
    {
        LowX,       // the spec's "west" column (o about 0.1: it faces +x)
        HighX,      // the spec's "east" column (o about 3.15)
    };

    inline constexpr float StatueX(Side side)
    {
        return side == Side::LowX ? kStatueLowX : kStatueHighX;
    }

    // The statue row nearest `y`.
    inline std::size_t NearestStatueRow(float y)
    {
        std::size_t best = 0;
        for (std::size_t i = 1; i < kStatueRows; ++i)
            if (std::fabs(kStatueRowY[i] - y) < std::fabs(kStatueRowY[best] - y))
                best = i;
        return best;
    }

    // The side a statue creature at `x` belongs to (its row is NearestStatueRow of its y).
    inline Side StatueSideOf(float x)
    {
        return x < kHallCenterX ? Side::LowX : Side::HighX;
    }

    // The hall's long coordinate a lane may be laid at: its 10 yd stays on the hall.
    inline float ClampLaneY(float y)
    {
        float const half = kLaneWidthYd / 2.f;
        return std::clamp(y, kHallYMin + half, kHallYMax - half);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG3 Crossfire: the lane
    // ----------------------------------------------------------------------------------------------------------------

    // One lane wall to wall at his y (section 8 #26: two statues aimed at his spot would make a V, not a lane): it runs
    // along +x from the low-x statue column to the high-x one (and a little beyond), `width` wide, centered on `y`.
    struct Lane
    {
        Vec2 from;              // the start of the line (the low-x end), on the lane's axis
        Vec2 to;
        Vec2 center;
        float facing = kFacingAlongX;
        float length = 0.f;
        float width = kLaneWidthYd;
        std::size_t row = 0;    // the statue row nearest the lane: the pair that turns and glows
    };

    inline Lane LaneAt(float y)
    {
        Lane lane;
        float const laneY = ClampLaneY(y);
        lane.from = { kStatueLowX - kLaneOverrunYd, laneY };
        lane.to = { kStatueHighX + kLaneOverrunYd, laneY };
        lane.center = { (lane.from.x + lane.to.x) / 2.f, laneY };
        lane.length = lane.to.x - lane.from.x;
        lane.row = NearestStatueRow(laneY);
        return lane;
    }

    // `p` on the lane's ground (the rectangle of the line and its width).
    inline bool InLane(Lane const& lane, Vec2 p)
    {
        return p.x >= lane.from.x && p.x <= lane.to.x && std::fabs(p.y - lane.center.y) <= lane.width / 2.f;
    }

    // The timeline of one Crossfire, in ms from the fist: the glow, the ignition, the burn and the end (the last tick).
    struct CrossfirePlan
    {
        std::uint64_t startMs = 0;      // the fist goes up, the lane's markers are down
        std::uint64_t ignitionMs = 0;   // glow over, the ignition and the first breath
        std::uint64_t endMs = 0;        // the last burn tick

        constexpr bool Glowing(std::uint64_t now) const { return now >= startMs && now < ignitionMs; }
        constexpr bool Burning(std::uint64_t now) const { return now >= ignitionMs && now <= endMs; }
    };

    inline constexpr CrossfirePlan PlanCrossfire(std::uint64_t startMs)
    {
        return { startMs, startMs + kGlowMs, startMs + kCrossfireEndMs };
    }

    // The next breath look of a window whose breath starts at `firstMs` and ends at `endMs`: `lastMs` (0: none cast
    // yet) -> the next due, or 0 when the window is over.
    inline constexpr std::uint64_t NextBreathMs(std::uint64_t firstMs, std::uint64_t lastMs, std::uint64_t endMs)
    {
        std::uint64_t const next = lastMs == 0 ? firstMs : lastMs + kBreathEveryMs;
        return next <= endMs ? next : 0;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG4 Flame Wall: the strips
    // ----------------------------------------------------------------------------------------------------------------

    // The strip along one wall: 12 yd of floor from the wall inward, drawn kWallOutsetYd wider on the wall side (the
    // alcoves), the whole length of the hall, running from the entrance end toward the throne.
    struct Strip
    {
        Vec2 from;              // the middle of the entrance end
        float facing = kFacingToThrone;
        float length = 0.f;
        float width = 0.f;
        float centerX = 0.f;
        float innerX = 0.f;     // the edge on the floor: the 12 yd of floor end here
        float outerX = 0.f;
    };

    inline Strip StripOf(Side side)
    {
        Strip strip;
        strip.width = kWallStripYd + kWallOutsetYd;
        if (side == Side::LowX)
        {
            strip.outerX = kHallLowX - kWallOutsetYd;
            strip.innerX = kHallLowX + kWallStripYd;
        }
        else
        {
            strip.innerX = kHallHighX - kWallStripYd;
            strip.outerX = kHallHighX + kWallOutsetYd;
        }
        strip.centerX = (strip.innerX + strip.outerX) / 2.f;
        strip.from = { strip.centerX, kHallYMax };
        strip.length = kHallYMax - kHallYMin;
        return strip;
    }

    inline bool InStrip(Strip const& strip, Vec2 p)
    {
        return std::fabs(p.x - strip.centerX) <= strip.width / 2.f && p.y <= kHallYMax && p.y >= kHallYMin;
    }

    // The floor a strip leaves clear, across the hall (39 - 12 = 27 yd).
    inline constexpr float FloorLeftYd()
    {
        return (kHallHighX - kHallLowX) - kWallStripYd;
    }

    // The strip is laid on the side he does not stand on: a side whose floor strip (plus his body margin) holds his x
    // is skipped; with both or neither, the sides alternate (the first is `roll` odd or even).
    inline Side ChooseWallSide(float magmusX, std::optional<Side> last, std::uint32_t roll)
    {
        bool const lowHoldsHim = magmusX <= kHallLowX + kWallStripYd + kWallBodyMarginYd;
        bool const highHoldsHim = magmusX >= kHallHighX - kWallStripYd - kWallBodyMarginYd;
        if (lowHoldsHim && !highHoldsHim)
            return Side::HighX;
        if (highHoldsHim && !lowHoldsHim)
            return Side::LowX;
        if (last)
            return *last == Side::LowX ? Side::HighX : Side::LowX;
        return (roll & 1u) ? Side::HighX : Side::LowX;
    }

    // Where the statue of row `row` breathes at: down the hall (toward the throne), on the strip's own line.
    inline Vec2 WallBreathPoint(Side side, std::size_t row)
    {
        return { StripOf(side).centerX, kStatueRowY[row < kStatueRows ? row : 0] - kWallBreathReachYd };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The clocks
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

    enum class Beat : std::uint8_t
    {
        Stomp,      // MG1
        Burst,      // MG2
        Crossfire,  // MG3
        FlameWall,  // MG4
    };

    // The four clocks, in the AI's own milliseconds (the pull is `Start`'s `now`). "Nothing holds the group in a lane":
    // a stomp (a 2 s stun on everyone within 5 yd, the tank too) never starts while a Crossfire's glow is up or would
    // still be up when the stun ends, and a Fiery Burst cast (he cannot walk while casting) never starts while a glow
    // is up, so the tank can always walk him out of the lane during the 3 s warning (designer question 2). A due
    // Crossfire itself waits for a cast in progress (the script retries). Held beats wait; their clock does not move.
    struct Timeline
    {
        bool heroic = false;
        std::uint64_t stompAt = 0;          // the next planned start of each beat (the grid)
        std::uint64_t burstAt = 0;
        std::uint64_t crossfireAt = 0;
        std::uint64_t wallAt = 0;
        std::uint64_t glowUntil = 0;        // the live Crossfire's glow ends (0: none)
        std::array<std::uint64_t, 4> holdUntil{};   // a refused start holds the beat until then (Retry)

        void Start(bool heroicForm, std::uint64_t now, std::uint32_t firstStompMs)
        {
            *this = Timeline{};
            heroic = heroicForm;
            stompAt = now + firstStompMs;
            burstAt = now + kBurstFirstMs;
            crossfireAt = now + kCrossfireFirstMs;
            wallAt = now + kWallFirstMs;
        }

        std::uint64_t PlannedAt(Beat beat) const
        {
            switch (beat)
            {
                case Beat::Stomp:     return stompAt;
                case Beat::Burst:     return burstAt;
                case Beat::Crossfire: return crossfireAt;
                case Beat::FlameWall: return wallAt;
            }
            return 0;
        }

        // A Crossfire's glow is up at `now`, or one that is due now (or starts within `leadMs`) would be.
        bool LaneGlowBlocks(std::uint64_t now, std::uint32_t leadMs) const
        {
            return now < glowUntil || now + leadMs > crossfireAt;
        }

        // Planned time reached, not held by a refused start, and not held by a Crossfire's glow (the stomp and the
        // Fiery Burst cast only).
        bool Due(Beat beat, std::uint64_t now) const
        {
            if (now < PlannedAt(beat) || now < holdUntil[static_cast<std::size_t>(beat)])
                return false;
            switch (beat)
            {
                case Beat::Stomp:     return !LaneGlowBlocks(now, kStompStunMs);
                case Beat::Burst:     return !LaneGlowBlocks(now, 0);
                case Beat::Crossfire: return true;
                case Beat::FlameWall: return true;
            }
            return false;
        }

        // The beat started at `now`: its clock moves on. `nextStompMs` is the roll of the stomp's next gap.
        void Fired(Beat beat, std::uint64_t now, std::uint32_t nextStompMs = kStompEveryMinMs)
        {
            holdUntil[static_cast<std::size_t>(beat)] = 0;
            switch (beat)
            {
                case Beat::Stomp:
                    stompAt = now + nextStompMs;
                    break;
                case Beat::Burst:
                    burstAt = now + kBurstEveryMs;
                    break;
                case Beat::Crossfire:
                    crossfireAt = NextPlanned(crossfireAt, kCrossfireEveryMs(heroic), now);
                    glowUntil = now + kGlowMs;
                    break;
                case Beat::FlameWall:
                    wallAt = NextPlanned(wallAt, kWallEveryMs(heroic), now);
                    break;
            }
        }

        // A refused start tries again `afterMs` from now (the grid does not move).
        void Retry(Beat beat, std::uint64_t now, std::uint32_t afterMs = kRetryMs)
        {
            holdUntil[static_cast<std::size_t>(beat)] = now + afterMs;
        }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // MG5 Dripping Magma (heroic): the walk tracker and the pool cap
    // ----------------------------------------------------------------------------------------------------------------

    // "Every 3 s while he walks": one pool when kPoolEveryMs have passed since the last and he has covered
    // kWalkedMinYd walking since then. Standing still for kStandStillResetMs forgets the distance (a creature's small
    // adjustments never add up to a step), so pools fall only while he moves. Step it every AI update.
    struct DripTracker
    {
        std::uint64_t nextAt = 0;
        float walkedYd = 0.f;
        std::uint64_t lastMovingMs = 0;
        Vec2 last;
        bool haveLast = false;

        void Start(std::uint64_t now, Vec2 position)
        {
            nextAt = now + kPoolEveryMs;
            walkedYd = 0.f;
            lastMovingMs = now;
            last = position;
            haveLast = true;
        }

        // True when a pool drops now (at `position`).
        bool Step(std::uint64_t now, Vec2 position, std::uint32_t diffMs)
        {
            if (!haveLast)
            {
                Start(now, position);
                return false;
            }
            float const moved = DungeonKit::Distance(last, position);
            last = position;
            bool const walking = diffMs > 0 && moved * 1000.f / static_cast<float>(diffMs) >= kWalkSpeedYdPerS;
            if (walking)
            {
                walkedYd += moved;
                lastMovingMs = now;
            }
            else if (now > lastMovingMs && now - lastMovingMs > kStandStillResetMs)
                walkedYd = 0.f;
            if (now >= nextAt && walkedYd >= kWalkedMinYd)
            {
                nextAt = now + kPoolEveryMs;
                walkedYd = 0.f;
                return true;
            }
            return false;
        }
    };

    // How many of the oldest pools retire so that one more can stand (the cap).
    inline constexpr std::size_t PoolsToRetire(std::size_t standing)
    {
        return standing >= kPoolCap ? standing - kPoolCap + 1 : 0;
    }

    // The registry persistence of one pool: its life after the first tick (the warning is not part of it).
    inline constexpr std::uint32_t PoolLifeAfterWarnMs()
    {
        return kPoolLifeMs - kPoolWarnMs;
    }
}

#endif
