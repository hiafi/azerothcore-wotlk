/*
 * mod-dungeon-bosses, Stratholme S8: Balnazzar's hard mode, the Grand Lie (heroic only), the pure, host-testable part
 * (no engine headers): the spell ids, the tuning, the acts, the calls and their twins, the room's halves, the moving
 * swarms' straight lines, the meteor and Dread Slumber timing, the relic spots and the Letter's refusals. Build spec:
 * ST 1920-1999 (Hard mode), ST 2107-2120 (the HM rows); handoff section 3.7, section 3.5 row S8, section 3.6 (600k),
 * section 3.8 (the chamber's halves). Tested by tests/strat_grand_lie_test.cpp. The engine side is
 * balnazzar_hard_mode.cpp, on S7's AI through DathrohanFight.h.
 *
 * The hard mode is heroic only, so its percents are of the heroic reference row (4,120 non-tank / 4,110 tank at level
 * 60, the MapLevels pin 329h:60); there is no normal value.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_GRAND_LIE_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_GRAND_LIE_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratGrandLie
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsGrandLie;

    // Declared in apps/dbc-tools source/npcs/stratholme/balnazzar_hard_mode.py (the relics' use spells too); same ids.
    enum GrandLieSpells : std::uint32_t
    {
        SPELL_GL_CLEAVE_LIGHT       = 206575,   // HM1 true: the claimed half is struck (resolve copy, Holy)
        SPELL_GL_CLEAVE_BLADE       = 206576,   // HM1 lie: the other half is struck (resolve copy, Shadow)
        SPELL_GL_RING_LIGHT         = 206577,   // HM2 true: the 10 yd circle on him is struck (resolve copy, Holy)
        SPELL_GL_RING_DARK          = 206578,   // HM2 lie: everything 10 to 40 yd from him is struck (Shadow)
        SPELL_GL_MARK               = 206579,   // HM3 the mark on the called non-tank until the call lands (DUMMY)
        SPELL_GL_MARK_SHARE         = 206580,   // HM3 true: one share of the 100% (Holy, base point from the script)
        SPELL_GL_MARK_BURST         = 206581,   // HM3 lie: each non-tank bursts on the others within 7 yd (Shadow)
        SPELL_GL_SWARM_CLOUD        = 206582,   // HM5 the swarm's cloud on its stalker (a look, STATE)
        SPELL_GL_SWARM_BITE         = 206583,   // HM5 the swarm's 1 s tick (resolve copy, Shadow)
        SPELL_GL_DREAD_SLUMBER      = 206584,   // HM8 the 3 s cast bar, not interruptible (yell 16)
        SPELL_GL_LETTER             = 206585,   // the Letter of Proof's use: read it to Dathrohan
        SPELL_GL_HOLY_WATER         = 206586,   // HM9 Blessed Holy Water: the throw (a spot within 10 yd, 5 yd splash)
        SPELL_GL_STANDARD           = 206587,   // HM9 the Scarlet Standard: a 6 yd ring for 5 s; its aura is the ward
        SPELL_GL_MEDALLION          = 206588,   // HM9 the Medallion's pulse: wakes sleepers, a 4 s sleep ward (30 yd)
        // 206589-206604 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_GL_CLEAVE_LIGHT), "S8 spells sit in its slice");
    static_assert(kSpellSlice.Contains(SPELL_GL_MEDALLION), "S8 spells sit in its slice");

    // Registry tags (S7's stop below StratDathrohan::kHardModeTagBase 20).
    enum GrandLieTags : std::uint32_t
    {
        TAG_GL_CLEAVE   = 20,   // HM1 the real half (NoTelegraph)
        TAG_GL_RING     = 21,   // HM2 the real circle or donut (NoTelegraph)
        TAG_GL_MARK     = 22,   // HM3 the real Stack or Spread (NoTelegraph)
        TAG_GL_CLAIM    = 23,   // the claimed marker of a call piece (a Decoy, drawn alike for truth and lie)
        TAG_GL_SWARM    = 24,   // HM5 a swarm's persistent circle
        TAG_GL_PARK     = 25,   // the tank rule: hold him on the brazier (hidden, tank-only Park)
        TAG_GL_STANDARD = 26,   // HM9 a raised Scarlet Standard: the bots' Stack on its ring (no damage)
    };

    // The cast queue id of Dread Slumber (StratDathrohan::kHardModeCastBase 100 on).
    std::uint32_t constexpr CAST_DREAD_SLUMBER = 101;
    std::uint8_t constexpr kSlumberPriority = 3;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Hard mode" and the HM rows, approved 2026-11-03, rulings 29-33)
    // ----------------------------------------------------------------------------------------------------------------

    // Health (section 3.6): 600k from the pull, set by the script (create health); a wipe's revert to Dathrohan
    // restores the template's.
    std::uint32_t constexpr kHardModeHealth = 600000;

    // The acts by health (100-70-40%). An act never goes back.
    enum class Act : std::uint8_t
    {
        Lies = 1,           // 100 to 70%: one twin every 10 s; moving swarms (cap 2)
        LiesUponLies = 2,   // 70 to 40%: pairs every 12 s; cap 3; the Carrion Swarm cones and the Infernals
        GrandLie = 3,       // 40 to 0%: all three every 15 s; cap 4; Dread Slumber replaces Sleep
    };
    float constexpr kActTwoPct = 70.f;
    float constexpr kActThreePct = 40.f;

    constexpr Act ActForHealth(float pct)
    {
        return pct > kActTwoPct ? Act::Lies : (pct > kActThreePct ? Act::LiesUponLies : Act::GrandLie);
    }

    // The act after a health check: the higher of the current one and the health's.
    constexpr Act NextAct(Act current, float pct)
    {
        Act const byHealth = ActForHealth(pct);
        return static_cast<std::uint8_t>(byHealth) > static_cast<std::uint8_t>(current) ? byHealth : current;
    }

    constexpr std::uint32_t ActIndex(Act act)
    {
        return static_cast<std::uint32_t>(act) - 1;
    }

    constexpr char const* ActName(Act act)
    {
        switch (act)
        {
            case Act::Lies: return "lies";
            case Act::LiesUponLies: return "lies-upon-lies";
            case Act::GrandLie: return "grand-lie";
        }
        return "?";
    }

    // ---- HM1-HM4 the twins and the calls ---------------------------------------------------------------------------

    enum class Twin : std::uint8_t
    {
        Cleave = 0,
        Ring = 1,
        Mark = 2,
    };

    constexpr char const* TwinName(Twin t)
    {
        switch (t)
        {
            case Twin::Cleave: return "cleave";
            case Twin::Ring: return "ring";
            case Twin::Mark: return "mark";
        }
        return "?";
    }

    // The truth roll (S7's rule): a call that says "the Light" is true, one that does not is a lie; even odds, every
    // piece on its own.
    std::uint32_t constexpr kTruthChancePct = 50;

    constexpr bool RollTrue(std::uint32_t roll)
    {
        return roll < kTruthChancePct;
    }

    // HM4: a call is one twin (act 1), a pair (act 2) or all three (act 3), taken in turn from this order; each piece
    // yells 1 s after the one before, and all of them land 4 s after the call's first yell.
    inline constexpr std::array<Twin, 3> kTwinOrder{ { Twin::Cleave, Twin::Ring, Twin::Mark } };
    inline constexpr std::array<std::uint32_t, 3> kCallEveryMs{ { 10000, 12000, 15000 } };
    std::uint32_t constexpr kFirstCallMs = 8000;        // from the pull (ST sets only the cadences)
    std::uint32_t constexpr kPieceGapMs = 1000;
    std::uint32_t constexpr kCallLandMs = 4000;

    constexpr std::uint32_t PiecesIn(Act act)
    {
        return static_cast<std::uint32_t>(act);
    }

    constexpr std::uint32_t CallEveryMs(Act act)
    {
        return kCallEveryMs[ActIndex(act)];
    }

    // The twins of call number `index` (0 on) in `act`, in yell order.
    inline std::vector<Twin> CallTwins(Act act, std::uint32_t index)
    {
        std::vector<Twin> out;
        for (std::uint32_t i = 0; i < PiecesIn(act); ++i)
            out.push_back(kTwinOrder[(index + i) % kTwinOrder.size()]);
        return out;
    }

    // Piece `i` of a call that started at `start`: its yell, and its warning (from its yell to the call's landing).
    constexpr std::uint64_t PieceYellAt(std::uint64_t start, std::uint32_t i)
    {
        return start + std::uint64_t(i) * kPieceGapMs;
    }

    constexpr std::uint32_t PieceWarnMs(std::uint32_t i)
    {
        return i * kPieceGapMs < kCallLandMs ? kCallLandMs - i * kPieceGapMs : 0;
    }

    // The texts (10813's groups, StratholmeRework.h DathrohanBalnazzarTexts): true lines say "the Light" (ruling 28).
    constexpr std::uint8_t YellOf(Twin t, bool isTrue)
    {
        using namespace StratholmeRework;
        switch (t)
        {
            case Twin::Cleave: return isTrue ? YELL_BALNAZZAR_CLEAVE_TRUE : YELL_BALNAZZAR_CLEAVE_LIE;
            case Twin::Ring: return isTrue ? YELL_BALNAZZAR_RING_TRUE : YELL_BALNAZZAR_RING_LIE;
            case Twin::Mark: return isTrue ? YELL_BALNAZZAR_MARK_TRUE : YELL_BALNAZZAR_MARK_LIE;
        }
        return YELL_BALNAZZAR_CLEAVE_TRUE;
    }

    // The hits: 50% to the non-tanks (the tank is exempt from all three), the true Mark 100% split. No Weakened (over
    // 30%, the Penalty column is empty).
    float constexpr kTwinPct = 50.f;
    float constexpr kMarkSplitPct = 100.f;

    // HM1 the Cleave: half the chamber, split through its center along the measured frame (StratholmeRework.h
    // kDathrohanHalves, the split line Y = 20 through the brazier): a 180 degree cone from the brazier that reaches
    // past the walls (the room is round, radius 19-20 on the mesh; the arena leash is 22).
    float constexpr kCleaveAngleDeg = 180.f;
    float constexpr kCleaveLengthYd = 25.f;

    // HM2 the Ring: true, the 10 yd circle on him; lie, the donut from 10 to 40 yd (past every wall).
    float constexpr kRingRadius = 10.f;
    float constexpr kRingOuter = 40.f;

    // HM3 the Mark: true, a 6 yd Stack on a random non-tank (100% split among the non-tanks within 6 yd and the
    // target); lie, a 7 yd Spread on every non-tank (50% to every other non-tank within 7 yd).
    float constexpr kMarkStackRadius = 6.f;
    float constexpr kMarkSpreadRadius = 7.f;

    // ---- The chamber's halves ---------------------------------------------------------------------------------------

    enum class Half : std::uint8_t
    {
        A = 0,      // frame Y below the split (the side of kDathrohanHalfASpots)
        B = 1,
    };

    constexpr Half Other(Half h)
    {
        return h == Half::A ? Half::B : Half::A;
    }

    constexpr char const* HalfName(Half h)
    {
        return h == Half::A ? "A" : "B";
    }

    inline Half HalfOf(Vec2 p)
    {
        Vec2 const local = DungeonKit::ToFrame(StratholmeRework::kDathrohanHalves, p);
        return local.y < StratholmeRework::kDathrohanSplitY ? Half::A : Half::B;
    }

    // The facing (radians, 0..2 pi) of a 180 degree cone from the brazier that covers `h`: the frame's -Y for A, its +Y
    // for B.
    inline float HalfFacing(Half h)
    {
        float const twoPi = 6.2831853f;
        float const quarter = 1.5707963f;
        float const a = StratholmeRework::kDathrohanHalves.angle;
        float f = h == Half::A ? a - quarter : a + quarter;
        while (f < 0.f)
            f += twoPi;
        while (f >= twoPi)
            f -= twoPi;
        return f;
    }

    // The struck half: the one with more swarms in it (ST space math: the safe half keeps the fewer); a tie goes to
    // `tieToA`.
    constexpr Half StruckHalf(std::uint32_t swarmsInA, std::uint32_t swarmsInB, bool tieToA)
    {
        if (swarmsInA != swarmsInB)
            return swarmsInA > swarmsInB ? Half::A : Half::B;
        return tieToA ? Half::A : Half::B;
    }

    // The struck half of a call (F-2 MAJ-1). The lie Ring's safe floor is the 10 yd disc on him (the donut strikes
    // the rest), and the Cleave strikes a half through the brazier: when he stands off the middle, a donut paired
    // with a Cleave on his half would leave almost nothing. So with a lie Ring in the call and him more than
    // kDonutSlackYd off the middle, the Cleave spares the half he stands in (the larger part of his disc); otherwise
    // the swarm rule. `bossSide` is his signed distance from the split line (SideOfMiddle, + on half B). A true Ring
    // (the 10 yd circle struck) leaves 220+ sq yd of a half wherever he stands, so it never needs the override.
    float constexpr kDonutSlackYd = 0.5f;

    inline Half StruckHalfFor(std::uint32_t swarmsInA, std::uint32_t swarmsInB, bool tieToA, bool lieRing,
        float bossSide)
    {
        if (lieRing && std::fabs(bossSide) > kDonutSlackYd)
            return bossSide > 0.f ? Half::A : Half::B;
        return StruckHalf(swarmsInA, swarmsInB, tieToA);
    }

    // The half the marker shows: the struck one when the call is true, the other when it lies.
    constexpr Half ClaimedHalf(Half struck, bool isTrue)
    {
        return isTrue ? struck : Other(struck);
    }

    // ---- HM5 the moving swarms --------------------------------------------------------------------------------------

    std::uint32_t constexpr kSwarmFirstMs = 15000;      // from the pull
    std::uint32_t constexpr kSwarmEveryMs = 20000;
    std::uint32_t constexpr kSwarmRetryMs = 1000;       // at the cap: the next one waits until one breaks up
    std::uint32_t constexpr kSwarmLifeMs = 30000;
    std::uint32_t constexpr kSwarmGraceMs = 1000;       // the first tick a second after it appears (Galford's grace)
    std::uint32_t constexpr kSwarmTickMs = 1000;
    float constexpr kSwarmSpeed = 3.f;                  // yd per second
    float constexpr kSwarmRadius = 2.5f;                // "5 yd across"
    float constexpr kSwarmTickPct = 10.f;               // per second, everyone inside, Weakened each second
    inline constexpr std::array<std::uint32_t, 3> kSwarmCap{ { 2, 3, 4 } };

    constexpr std::uint32_t SwarmCap(Act act)
    {
        return kSwarmCap[ActIndex(act)];
    }

    // The swarm's center keeps inside this circle around the brazier (the mesh's rim is 19-20 yd: its 2.5 yd cloud
    // brushes the wall) and comes out of the wall on it.
    float constexpr kSwarmPathRadius = 17.f;
    float constexpr kSwarmAimRadius = 6.f;              // it crawls toward a random point this near the brazier
    // No swarm comes out of the doorway (the only way in, north-east, about 20-27 yd out at (3438, -3076)).
    Vec2 constexpr kChamberEntrance{ 3438.0f, -3076.0f };
    float constexpr kEntranceAvoidRad = 0.6109f;        // 35 degrees either side of the doorway's bearing
    float constexpr kMiddleEpsYd = 0.3f;                // a swarm turning off the middle stops this short of it
    // The swarm's center keeps this far off the split line while the middle is closed: its whole 2.5 yd cloud stays
    // on its own side (F-2 MIN-2; ST 2115 "never crosses the middle in a call's last 4 s").
    float constexpr kMiddleClearYd = kSwarmRadius + kMiddleEpsYd;
    // A swarm already inside that band when the middle closes leaves it at least this fast across (cosine of its
    // heading to the split line's normal): out of the band within (kMiddleClearYd / kSwarmSpeed) / kLeaveMinCos.
    float constexpr kLeaveMinCos = 0.6f;

    inline Vec2 Brazier()
    {
        return StratholmeRework::kDathrohanBrazier.XY();
    }

    // The split line's unit normal (the frame's +Y axis).
    inline Vec2 MiddleNormal()
    {
        float const a = StratholmeRework::kDathrohanHalves.angle;
        return { -std::sin(a), std::cos(a) };
    }

    // A point's signed distance from the split line (through the brazier): + on half B, - on half A.
    inline float SideOfMiddle(Vec2 p)
    {
        Vec2 const c = Brazier();
        Vec2 const m = MiddleNormal();
        return (p.x - c.x) * m.x + (p.y - c.y) * m.y;
    }

    // ---- The tank rule (ST 1931, F-2 MAJ-1) ------------------------------------------------------------------------

    // The tank holds him on the brazier (Scholomance addition 7): while he stands more than kParkTriggerYd off it, a
    // hidden tank-only Park circle on it (checked every kParkCheckMs; each holds kParkHoldMs, under the bots' 8 s
    // hold cap a zone; a new one follows while he is still off it).
    std::uint32_t constexpr kParkCheckMs = 1000;
    std::uint32_t constexpr kParkHoldMs = 5000;
    float constexpr kParkRadius = 3.f;
    float constexpr kParkTriggerYd = 3.f;

    inline bool ShouldPark(Vec2 boss)
    {
        return DungeonKit::Distance(boss, Brazier()) > kParkTriggerYd;
    }

    inline float EntranceBearing()
    {
        Vec2 const c = Brazier();
        return std::atan2(kChamberEntrance.y - c.y, kChamberEntrance.x - c.x);
    }

    // The smallest angle between two bearings (0..pi).
    inline float BearingGap(float a, float b)
    {
        float const twoPi = 6.2831853f;
        float d = std::fmod(std::fabs(a - b), twoPi);
        return d > twoPi / 2.f ? twoPi - d : d;
    }

    // Where a new swarm comes out of the wall: `roll` in [0, 1) spread over the wall away from the doorway.
    inline float SpawnBearing(float roll)
    {
        float const twoPi = 6.2831853f;
        float const span = twoPi - 2.f * kEntranceAvoidRad;
        float b = EntranceBearing() + kEntranceAvoidRad + std::clamp(roll, 0.f, 1.f) * span;
        while (b >= twoPi)
            b -= twoPi;
        while (b < 0.f)
            b += twoPi;
        return b;
    }

    struct SwarmStart
    {
        Vec2 at;
        Vec2 dir;       // unit
    };

    // A swarm at `bearing` on the wall, crawling toward the point `aimDist` (0..kSwarmAimRadius) from the brazier at
    // `aimBearing`.
    inline SwarmStart SwarmSpawn(float bearing, float aimBearing, float aimDist)
    {
        Vec2 const c = Brazier();
        Vec2 const at{ c.x + kSwarmPathRadius * std::cos(bearing), c.y + kSwarmPathRadius * std::sin(bearing) };
        float const d = std::clamp(aimDist, 0.f, kSwarmAimRadius);
        Vec2 const aim{ c.x + d * std::cos(aimBearing), c.y + d * std::sin(aimBearing) };
        float const dx = aim.x - at.x;
        float const dy = aim.y - at.y;
        float const len = std::sqrt(dx * dx + dy * dy);
        if (len < 0.001f)
            return { at, { -std::cos(bearing), -std::sin(bearing) } };
        return { at, { dx / len, dy / len } };
    }

    // One straight leg of a swarm: from its spot along `dir` to the wall circle, or (with the middle closed, HM5: no
    // swarm crosses the middle in a call's last 4 s) to where its cloud's edge is just short of the split line when
    // that comes first. At the end it turns off what it met (a mirror bounce). A swarm whose cloud already reaches
    // over the line when the middle closes turns away at once (a zero-length leg), leaving at kLeaveMinCos or faster.
    struct SwarmLeg
    {
        Vec2 end;
        Vec2 dirAfter;
        float length = 0.f;
        bool offMiddle = false;
    };

    inline Vec2 Reflect(Vec2 d, Vec2 n)
    {
        float const dot = d.x * n.x + d.y * n.y;
        return { d.x - 2.f * dot * n.x, d.y - 2.f * dot * n.y };
    }

    inline SwarmLeg PlanLeg(Vec2 pos, Vec2 dir, bool middleClosed)
    {
        Vec2 const c = Brazier();
        float const R = kSwarmPathRadius;
        float const ox = pos.x - c.x;
        float const oy = pos.y - c.y;
        // A stray outside the circle comes back in: it aims at the brazier.
        if (ox * ox + oy * oy > R * R + 0.01f)
        {
            float const len = std::sqrt(ox * ox + oy * oy);
            dir = { -ox / len, -oy / len };
        }
        // Ray to the wall: |o + t d| = R, the far root.
        float const b = ox * dir.x + oy * dir.y;
        float const cc = ox * ox + oy * oy - R * R;
        float const disc = std::max(0.f, b * b - cc);
        float const tWall = std::max(0.f, -b + std::sqrt(disc));

        SwarmLeg leg;
        if (middleClosed)
        {
            Vec2 const m = MiddleNormal();
            float const side = ox * m.x + oy * m.y;
            // The side it is on (on the line itself: the side it heads for, else B), and its heading off the line.
            float const away = side > 0.f ? 1.f : (side < 0.f ? -1.f : (dir.x * m.x + dir.y * m.y < 0.f ? -1.f : 1.f));
            Vec2 const nAway{ m.x * away, m.y * away };
            float const leaving = dir.x * nAway.x + dir.y * nAway.y;
            if (std::fabs(side) <= kMiddleClearYd)
            {
                // Inside the band: turn away now (its cloud reaches over the line), back to the side it is on.
                if (leaving < kLeaveMinCos)
                {
                    Vec2 par{ dir.x - leaving * nAway.x, dir.y - leaving * nAway.y };
                    float const pl = std::sqrt(par.x * par.x + par.y * par.y);
                    float const along = std::sqrt(1.f - kLeaveMinCos * kLeaveMinCos);
                    par = pl > 0.001f ? Vec2{ par.x / pl * along, par.y / pl * along } : Vec2{ 0.f, 0.f };
                    Vec2 turned{ par.x + nAway.x * kLeaveMinCos, par.y + nAway.y * kLeaveMinCos };
                    float const tl = std::sqrt(turned.x * turned.x + turned.y * turned.y);
                    leg.end = pos;
                    leg.dirAfter = { turned.x / tl, turned.y / tl };
                    leg.length = 0.f;
                    leg.offMiddle = true;
                    return leg;
                }
            }
            else if (leaving < 0.f)
            {
                // Heading for the line: it stops with its cloud's edge just short of it and turns off it.
                float const tMid = (std::fabs(side) - kMiddleClearYd) / -leaving;
                if (tMid < tWall)
                {
                    leg.end = { pos.x + dir.x * tMid, pos.y + dir.y * tMid };
                    leg.dirAfter = Reflect(dir, m);
                    leg.length = tMid;
                    leg.offMiddle = true;
                    return leg;
                }
            }
        }
        leg.end = { pos.x + dir.x * tWall, pos.y + dir.y * tWall };
        Vec2 n{ leg.end.x - c.x, leg.end.y - c.y };
        float const nl = std::sqrt(n.x * n.x + n.y * n.y);
        if (nl > 0.001f)
            n = { n.x / nl, n.y / nl };
        leg.dirAfter = Reflect(dir, n);
        leg.length = tWall;
        return leg;
    }

    // ---- HM6 the cones, HM7 the Infernals, HM8 Sleep and Dread Slumber ---------------------------------------------

    // HM6 (act 2 on): S7's Carrion Swarm, two cones as on heroic (the second 1.5 s after the first, S7's default), 25%
    // to each target and 50% to anyone else inside; its own timer, every 20 s; the Standard's ward spares whoever
    // stands in its ring (the target too).
    std::uint32_t constexpr kConeCount = 2;
    float constexpr kConeTargetPct = 25.f;
    float constexpr kConeOthersPct = 50.f;
    std::uint32_t constexpr kConeEveryMs = 20000;
    std::uint32_t constexpr kConeFirstInActMs = 5000;       // after act 2 begins (ST sets only the cadence)

    // HM7 (act 2 on): S7's Inferno every 30 s; the meteor's 3.5 s, 50%; the Infernal 25k and stoking. It never lands
    // in a call's last 4 s.
    std::uint32_t constexpr kInfernalHealth = 25000;
    std::uint32_t constexpr kInfernoEveryMs = 30000;
    std::uint32_t constexpr kInfernoFirstInActMs = 12000;
    std::uint32_t constexpr kInfernoCastMs = 3500;          // S7's kInfernoCastMs (the meteor lands then)

    // A call's last 4 s: [its first yell, its landing].
    struct Window
    {
        std::uint64_t from = 0;
        std::uint64_t to = 0;

        constexpr bool Contains(std::uint64_t t) const { return t >= from && t <= to; }
    };

    constexpr Window CallWindow(std::uint64_t start)
    {
        return { start, start + kCallLandMs };
    }

    // HM7: a meteor started now lands at now + 3.5 s: never inside the running call's window or the next one's.
    inline bool MeteorBlocked(std::uint64_t now, std::optional<Window> running, std::optional<Window> next)
    {
        std::uint64_t const lands = now + kInfernoCastMs;
        return (running && running->Contains(lands)) || (next && next->Contains(lands));
    }

    // HM8 act 3: Dread Slumber every 30 s, a 3 s cast that cannot be interrupted; it lands 2 s after a call resolves
    // (so its cast starts 1 s before the call lands, 3 s after the call's first yell); every unwarded player sleeps
    // 5 s (S7's Sleep aura, Magic), then Nightmare. The next call's first yell comes 3 s after it lands.
    std::uint32_t constexpr kSlumberEveryMs = 30000;
    std::uint32_t constexpr kSlumberFirstInActMs = 8000;
    std::uint32_t constexpr kSlumberCastMs = 3000;
    std::uint32_t constexpr kSlumberAfterCallMs = 2000;
    std::uint32_t constexpr kCallAfterSlumberMs = 3000;

    // The cast's start, from the call's first yell.
    constexpr std::uint32_t SlumberCastInMs()
    {
        return kCallLandMs + kSlumberAfterCallMs - kSlumberCastMs;
    }

    // A call starting at `callStart` carries the slumber when it is due by the time the cast would start.
    constexpr bool CallCarriesSlumber(Act act, std::uint64_t slumberDueAt, std::uint64_t callStart)
    {
        return act == Act::GrandLie && slumberDueAt <= callStart + SlumberCastInMs();
    }

    // HM10 Vampiric Aura: 3% of his maximum health per hit landed (S7's hook).
    float constexpr kVampiricPct = 3.f;

    // ---- HM9 the relics ---------------------------------------------------------------------------------------------

    // Item use spells (each copy keeps its own cooldown, ruling 33).
    float constexpr kHolyWaterRangeYd = 10.f;
    float constexpr kHolyWaterSplashYd = 5.f;
    std::uint32_t constexpr kHolyWaterCooldownMs = 180000;
    float constexpr kStandardRadiusYd = 6.f;
    std::uint32_t constexpr kStandardMs = 5000;
    std::uint32_t constexpr kStandardCooldownMs = 20000;
    float constexpr kMedallionRadiusYd = 30.f;
    std::uint32_t constexpr kMedallionWardMs = 4000;
    std::uint32_t constexpr kMedallionCooldownMs = 25000;
    float constexpr kLetterRangeYd = 30.f;
    std::uint32_t constexpr kLetterSpeechMs = 2500;     // "What is this? A letter?" ... then the mask comes off

    // The relic and Letter spots (heroic only, spawnMask 2; the playtest checks them in game). The Letter in the ashes
    // of the Scarlet Archive 176245 (between Galford's spawn and the archive); the Standard on Willey's spot in his
    // yard; the Medallion's light beside Malor's Strongbox 176112 (1.5 yd toward his spawn, so the two clicks never
    // overlap); the blessed crate 2 yd from the stock Supply Crate (Holy Water) 176224 in Crusaders' Square.
    StratholmeRework::Point4 constexpr kLetterSpot{ 3456.3f, -3104.9f, 136.6f, 4.86f };
    StratholmeRework::Point4 constexpr kStandardSpot{ 3573.57f, -2937.31f, 125.09f, 3.79f };
    StratholmeRework::Point4 constexpr kMedallionLightSpot{ 3618.56f, -3129.46f, 135.7f, 0.81f };
    StratholmeRework::Point4 constexpr kBlessedCrateSpot{ 3664.63f, -3182.46f, 126.25f, 3.14f };

    // Which boss's death shows a spot (the crate: none, it stands from the instance's start).
    constexpr std::optional<std::uint32_t> RelicBoss(std::uint32_t goEntry)
    {
        switch (goEntry)
        {
            case StratholmeRework::GO_ST_LETTER_OF_PROOF: return StratholmeRework::BOSS_GALFORD;
            case StratholmeRework::GO_ST_SCARLET_STANDARD: return StratholmeRework::BOSS_WILLEY;
            case StratholmeRework::GO_ST_MEDALLION_LIGHT: return StratholmeRework::BOSS_MALOR;
            default: return std::nullopt;
        }
    }

    // The item a spot gives.
    constexpr std::uint32_t RelicItem(std::uint32_t goEntry)
    {
        switch (goEntry)
        {
            case StratholmeRework::GO_ST_LETTER_OF_PROOF: return StratholmeRework::ITEM_ST_LETTER_OF_PROOF;
            case StratholmeRework::GO_ST_SCARLET_STANDARD: return StratholmeRework::ITEM_ST_SCARLET_STANDARD;
            case StratholmeRework::GO_ST_BLESSED_CRATE: return StratholmeRework::ITEM_ST_BLESSED_HOLY_WATER;
            case StratholmeRework::GO_ST_MEDALLION_LIGHT: return StratholmeRework::ITEM_ST_RELIC_OF_THE_MEDALLION;
            default: return 0;
        }
    }

    // A spot shows (and gives) on heroic, with wave 2 bound, once its boss is dead (`bossState`: that boss's state;
    // ignored for the crate).
    constexpr bool RelicShown(std::uint32_t goEntry, bool heroic, bool wave2Bound, std::uint32_t bossState)
    {
        if (!heroic || !wave2Bound || !RelicItem(goEntry))
            return false;
        return !RelicBoss(goEntry) || bossState == DungeonKit::State::Done;
    }

    // ---- The Letter of Proof ----------------------------------------------------------------------------------------

    enum class LetterRefusal : std::uint8_t
    {
        None = 0,
        NotHeroic,          // the hard mode is heroic only
        NotBound,           // wave 2 is not bound (the Main Gate runs stock)
        Done,               // Balnazzar is dead
        NoDathrohan,        // he is not here (or already Balnazzar)
        Fighting,           // he is in combat
        TooFar,             // more than 30 yd, or out of sight
    };

    struct LetterCheck
    {
        bool heroic = false;
        bool wave2Bound = false;
        bool dathrohanHere = false;     // alive, entry 10812
        float distance = 0.f;
        bool inSight = true;
        bool inCombat = false;
        std::uint32_t balnazzarState = DungeonKit::State::NotStarted;
    };

    constexpr LetterRefusal CheckLetter(LetterCheck const& c)
    {
        if (!c.heroic)
            return LetterRefusal::NotHeroic;
        if (!c.wave2Bound)
            return LetterRefusal::NotBound;
        if (c.balnazzarState == DungeonKit::State::Done)
            return LetterRefusal::Done;
        if (!c.dathrohanHere)
            return LetterRefusal::NoDathrohan;
        if (c.inCombat || c.balnazzarState == DungeonKit::State::InProgress)
            return LetterRefusal::Fighting;
        if (c.distance > kLetterRangeYd || !c.inSight)
            return LetterRefusal::TooFar;
        return LetterRefusal::None;
    }

    constexpr char const* LetterRefusalText(LetterRefusal r)
    {
        switch (r)
        {
            case LetterRefusal::None: return "";
            case LetterRefusal::NotHeroic: return "The Grand Crusader pays no heed to letters here.";
            case LetterRefusal::NotBound: return "The Grand Crusader pays no heed to letters yet.";
            case LetterRefusal::Done: return "The dreadlord is already dead.";
            case LetterRefusal::NoDathrohan: return "The Grand Crusader is not here to read it.";
            case LetterRefusal::Fighting: return "Not while he fights.";
            case LetterRefusal::TooFar: return "Get closer to the Grand Crusader.";
        }
        return "";
    }
}

#endif
