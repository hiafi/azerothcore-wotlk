/*
 * mod-dungeon-bosses, Scholomance S2: Rattlegore (11622), the pure, host-testable part (no engine headers). Build spec
 * SC 733-778 (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows RG and 3.5 row S2. Tested by
 * tests/scholo_rattlegore_test.cpp.
 *
 *   Spells             the WP's ids, inside kSpellsRattlegore (206130-206149), declared in apps/dbc-tools
 *                      source/npcs/scholomance/rattlegore.py
 *   Tuning             NH<> constants: one number per difficulty, straight from the build spec
 *   BreakLadder        RG1 the six health thresholds (85 .. 10%), each fires once; a burst may cross two
 *   PickLandings       RG1 landing points: on the Ossuary floor, inside his arena, 20+ yd from him; heroic's second
 *                      pile on the far side of him
 *   PileState          RG2 / RG3 one bone pile: wait, crawl, ground down by whoever stands on it (progress kept),
 *                      or home
 *   Frenzy             RG8 stacks: halved by each break, +5 per pile home, cap 100
 *   EruptionRings      RG4 the chained rings, out (and heroic back in)
 *   Salvage            RG5 the gate (second break on, 30 s apart, 4 constructs), the damage break, the nearest pick
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RATTLEGORE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RATTLEGORE_LOGIC_H

#include "DungeonKitMath.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ScholoRattlegore
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRattlegore;

    enum RattlegoreSpells : std::uint32_t
    {
        SPELL_RG_PART_LANDS         = kSpellSlice.first + 0,    // 206130 RG1 the landing circle's hit (resolve copy)
        SPELL_RG_PART_FLUNG         = kSpellSlice.first + 1,    // 206131 RG1 the bone missile to the landing point
        SPELL_RG_GRIND              = kSpellSlice.first + 2,    // 206132 RG2 the soaker's tick
        SPELL_RG_BOLTED_BACK_ON     = kSpellSlice.first + 3,    // 206133 RG3 a pile home: the heal (bp by script)
        SPELL_RG_FRENZY             = kSpellSlice.first + 4,    // 206134 RG8 the stacking buff
        SPELL_RG_ERUPTION_CAST      = kSpellSlice.first + 5,    // 206135 RG4 the 2 s cast bar
        SPELL_RG_ERUPTION_HIT       = kSpellSlice.first + 6,    // 206136 RG4 a ring's hit (resolve copy)
        SPELL_RG_SALVAGE            = kSpellSlice.first + 7,    // 206137 RG5 the 5 s self channel (interruptible)
        SPELL_RG_SALVAGE_HEAL       = kSpellSlice.first + 8,    // 206138 RG5 an unbroken channel: the heal
        SPELL_RG_REINFORCED         = kSpellSlice.first + 9,    // 206139 RG5 heroic: +15% damage dealt, 4 stacks
        SPELL_RG_KNOCK_AWAY         = kSpellSlice.first + 10,   // 206140 RG7 stock 10101 without the threat cut
        SPELL_RG_GROUND_TO_DUST     = kSpellSlice.first + 11,   // 206141 RG2 a pile ground down / a construct spent
        // 206142-206149 spare
    };
    static_assert(SPELL_RG_GROUND_TO_DUST <= kSpellSlice.last, "Rattlegore's spells must stay in his slice");

    // Stock spells kept: Strike 18368 (RG6) is ScholomanceRework::SPELL_STRIKE (DD scales it on heroic).
    inline constexpr std::uint32_t SPELL_PERMANENT_FEIGN_DEATH = 29266;   // the constructs' collapsed pose (SQL addon)

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum RattlegoreTags : std::uint32_t
    {
        TAG_PART_LANDS      = 1,
        TAG_LOOSE_PART      = 2,
        TAG_ERUPTION_OUT    = 3,
        TAG_ERUPTION_IN     = 4,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC 742-771; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // RG1 Part lands
    inline constexpr NH<std::uint32_t> kPilesPerBreak{ 1, 2 };
    inline constexpr NH<float> kLandingRadius{ 4.f, 6.f };
    inline constexpr std::uint32_t kLandingWarnMs = 2000;
    inline constexpr NH<float> kLandingPct{ 30.f, 40.f };            // + 1 Weakened (ruling 21, both difficulties)
    inline constexpr float kPartFlungSpeed = 20.f;                    // yd/s: the missile's Speed in rattlegore.py

    // RG2 / RG3 Loose part
    inline constexpr float kPileSoakRadius = 3.f;
    inline constexpr float kPileSoakZBand = 4.f;                      // yd above or below the pile that still count
    inline constexpr NH<std::uint32_t> kPileWaitMs{ 3000, 1000 };
    inline constexpr NH<float> kPileCrawlYdPerSec{ 3.f, 4.f };
    inline constexpr NH<std::uint32_t> kPileGrindMs{ 5000, 6000 };
    inline constexpr std::uint32_t kPileTickMs = 1000;
    inline constexpr NH<float> kPileTickPct{ 5.f, 6.f };              // per tick to each player on it; no Weakened
    inline constexpr NH<float> kPileHomeHealPct{ 8.f, 10.f };         // of his maximum health
    inline constexpr std::uint32_t kPileHomeFrenzy = 5;
    inline constexpr float kPileHomeReach = 1.5f;                     // yd past his combat reach: bolted back on
    inline constexpr std::uint32_t kPileRepathMs = 500;
    // The Soak lasts as long as the pile can live; the script cancels it when the pile is ground down or home.
    inline constexpr std::uint32_t kPileSoakLifeMs = 180000;

    // RG4 Ossuary Eruption
    inline constexpr std::uint32_t kEruptionCastMs = 2000;
    inline constexpr std::uint32_t kEruptionFirstMs = 8000;
    inline constexpr std::uint32_t kEruptionEveryMs = 20000;
    inline constexpr std::uint32_t kEruptionOutStepMs = 1500;
    inline constexpr std::uint32_t kEruptionInStepMs = 1000;
    inline constexpr NH<float> kEruptionPct{ 35.f, 50.f };            // per ring, no Weakened
    // The outer ring's hole: 12 / 18 = 0.6667 sits just under mod-boss-mechanics' 0.67 donut texture step, which the
    // marker would round down to 0.60 (a drawn hole of 10.8 yd that overlaps the 6-12 ring). 12.06 / 18 is exactly the
    // 0.67 step, so the drawn hole is the real one; the 0.06 yd strip between the rings is hit by neither.
    inline constexpr float kEruptionOuterInner = 12.06f;

    // RG5 Salvage
    inline constexpr std::uint32_t kSalvageFromBreak = 2;
    inline constexpr std::uint32_t kSalvageAfterBreakMs = 3000;       // the first one, after the second break
    inline constexpr std::uint32_t kSalvageEveryMs = 30000;           // at most every 30 s (start to start)
    inline constexpr std::uint32_t kSalvageChannelMs = 5000;
    inline constexpr std::uint32_t kSalvageWalkTimeoutMs = 8000;      // a blocked path: channel where he stands
    inline constexpr float kSalvageBreakPct = 5.f;                    // of his maximum health, during the channel
    inline constexpr float kSalvageHealPct = 10.f;                    // both difficulties
    inline constexpr std::uint32_t kReinforcedMaxStacks = 4;          // heroic, one per missed Salvage

    // RG6 Strike / RG7 Knock Away: first in [min, max], then every [min, max]
    struct MsRange
    {
        std::uint32_t min;
        std::uint32_t max;
    };
    inline constexpr MsRange kStrikeFirst{ 3000, 6000 };
    inline constexpr MsRange kStrikeEvery{ 7000, 12000 };
    inline constexpr MsRange kKnockFirst{ 7000, 15000 };
    inline constexpr MsRange kKnockEvery{ 15000, 25000 };

    // `r` in [0, 1): a point of the range.
    constexpr std::uint32_t InRange(MsRange range, float r)
    {
        float const span = static_cast<float>(range.max - range.min);
        return range.min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 1.f) * span);
    }

    // RG8 Frenzy
    inline constexpr NH<std::uint32_t> kFrenzyEveryMs{ 3000, 2000 };
    inline constexpr std::uint32_t kFrenzyMaxStacks = 100;

    // ----------------------------------------------------------------------------------------------------------------
    // RG1 Break thresholds: each fires once, so healing him over one never fires it again; a burst over two fires two
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::array<float, 6> kBreakAtPct{ { 85.f, 70.f, 55.f, 40.f, 25.f, 10.f } };

    class BreakLadder
    {
    public:
        // The thresholds newly crossed at `healthPct` (at or below), marked fired.
        std::uint32_t Take(float healthPct)
        {
            std::uint32_t crossed = 0;
            for (std::size_t i = 0; i < kBreakAtPct.size(); ++i)
            {
                if (_fired & (1u << i))
                    continue;
                if (healthPct <= kBreakAtPct[i])
                {
                    _fired |= 1u << i;
                    ++crossed;
                }
            }
            _breaks += crossed;
            return crossed;
        }

        // A break that is not a threshold (`.dbtest scholo rattlegore break`): counted for Salvage's gate only.
        void AddForced() { ++_breaks; }

        std::uint32_t FiredCount() const
        {
            std::uint32_t n = 0;
            for (std::size_t i = 0; i < kBreakAtPct.size(); ++i)
                n += (_fired >> i) & 1u;
            return n;
        }

        std::uint32_t Breaks() const { return _breaks; }
        void Reset() { _fired = 0; _breaks = 0; }

    private:
        std::uint32_t _fired = 0;
        std::uint32_t _breaks = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RG1 Landing points
    // ----------------------------------------------------------------------------------------------------------------
    struct LandingRules
    {
        DungeonKit::FrameRect floor = ScholomanceRework::kOssuaryFloor;
        float inset = 2.f;                      // yd inside the floor frame
        Vec2 arenaCenter{ 130.5f, 173.5f };     // RattlegoreArena()
        float arenaRadius = 35.f;
        float arenaMargin = 2.f;                // yd inside the arena circle
        float minFromBoss = 20.f;               // SC: at least 20 yd from him (beyond the 18 yd rings)
        float minApart = 10.f;                  // from every other live landing and pile
        float oppositeDeg = 135.f;              // heroic: the second pile at least this far around him from the first
        std::uint32_t tries = 48;
    };

    // The angle (degrees, 0-180) between the bearings from `center` to `a` and to `b`.
    inline float AngleApartDeg(Vec2 center, Vec2 a, Vec2 b)
    {
        float d = DungeonKit::BearingTo(center, a) - DungeonKit::BearingTo(center, b);
        while (d > DungeonKit::kPi)
            d -= DungeonKit::kTwoPi;
        while (d < -DungeonKit::kPi)
            d += DungeonKit::kTwoPi;
        return std::fabs(d) * 180.f / DungeonKit::kPi;
    }

    inline bool OnLandingFloor(LandingRules const& rules, Vec2 p)
    {
        DungeonKit::FrameRect inner = rules.floor;
        inner.origin = DungeonKit::FramePoint(rules.floor, rules.inset, rules.inset);
        inner.sizeX = std::max(0.f, rules.floor.sizeX - 2.f * rules.inset);
        inner.sizeY = std::max(0.f, rules.floor.sizeY - 2.f * rules.inset);
        return DungeonKit::InsideFrame(inner, p, 0.f)
            && DungeonKit::Distance(rules.arenaCenter, p) <= rules.arenaRadius - rules.arenaMargin;
    }

    // `count` landing points for one break. Each candidate is uniform on the inset floor frame (rand01() in [0, 1)),
    // inside the arena, and accepted by `valid(p)` (the engine's floor height check). The first candidate that is
    // 20+ yd from him, `minApart` from every point in `avoid` and the break's earlier picks and (for a second pile)
    // `oppositeDeg` around him from the first is taken; when none is in `tries`, the best scored one is (far first,
    // then apart, then the angle, then the distance), so a break always throws its parts when the floor has any point.
    template <class Rand01, class Valid>
    std::vector<Vec2> PickLandings(LandingRules const& rules, Vec2 boss, std::uint32_t count,
        std::vector<Vec2> const& avoid, Rand01&& rand01, Valid&& valid)
    {
        std::vector<Vec2> picks;
        for (std::uint32_t i = 0; i < count; ++i)
        {
            std::optional<Vec2> best;
            float bestScore = -1.f;
            for (std::uint32_t t = 0; t < rules.tries; ++t)
            {
                float const fx = rand01();
                float const fy = rand01();
                Vec2 const p = DungeonKit::FramePoint(rules.floor,
                    rules.inset + fx * std::max(0.f, rules.floor.sizeX - 2.f * rules.inset),
                    rules.inset + fy * std::max(0.f, rules.floor.sizeY - 2.f * rules.inset));
                if (!OnLandingFloor(rules, p) || !valid(p))
                    continue;
                float const d = DungeonKit::Distance(boss, p);
                bool const far = d >= rules.minFromBoss;
                bool apart = true;
                for (Vec2 const& q : avoid)
                    apart = apart && DungeonKit::Distance(p, q) >= rules.minApart;
                for (Vec2 const& q : picks)
                    apart = apart && DungeonKit::Distance(p, q) >= rules.minApart;
                float const angle = picks.empty() ? 180.f : AngleApartDeg(boss, picks.front(), p);
                bool const opposite = angle >= rules.oppositeDeg;
                if (far && apart && opposite)
                {
                    best = p;
                    break;
                }
                float const score = (far ? 10000.f : 0.f) + (apart ? 1000.f : 0.f) + angle + d;
                if (score > bestScore)
                {
                    bestScore = score;
                    best = p;
                }
            }
            if (!best)
                break;
            picks.push_back(*best);
        }
        return picks;
    }

    // The missile's launch delay so it lands as the landing circle resolves (0 when the flight is longer).
    constexpr std::uint32_t LaunchDelayMs(std::uint32_t warnMs, float distance, float speed = kPartFlungSpeed)
    {
        float const flight = speed > 0.f ? distance / speed * 1000.f : 0.f;
        return flight >= static_cast<float>(warnMs) ? 0u : static_cast<std::uint32_t>(static_cast<float>(warnMs)
            - flight);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG2 / RG3 One bone pile
    // ----------------------------------------------------------------------------------------------------------------
    struct PileTuning
    {
        std::uint32_t waitMs = 3000;
        std::uint32_t grindMs = 5000;
        std::uint32_t tickMs = kPileTickMs;
    };

    constexpr PileTuning PileTuningFor(bool heroic)
    {
        return { kPileWaitMs(heroic), kPileGrindMs(heroic), kPileTickMs };
    }

    class PileState
    {
    public:
        enum class Phase : std::uint8_t
        {
            Waiting,        // just landed: still for waitMs
            Crawling,       // toward him
            Ground,         // ground down (done)
            Home,           // reached him (done)
        };

        struct Step
        {
            std::uint32_t ticks = 0;        // grind ticks due now (one per tickMs on it): damage each player on it
            bool ground = false;            // ground down this step
            bool home = false;              // reached him this step
            bool move = false;              // crawling: keep moving toward him
            bool held = false;              // a player is on it: it does not move
        };

        explicit PileState(PileTuning tuning = {}) : _t(tuning), _waitLeft(tuning.waitMs) { }

        // One update: `soakerOn` = an eligible player stands on it now; `atBoss` = it touches him now.
        Step Update(std::uint32_t diff, bool soakerOn, bool atBoss)
        {
            Step step;
            if (Done())
                return step;

            if (_phase == Phase::Waiting)
            {
                _waitLeft = diff >= _waitLeft ? 0 : _waitLeft - diff;
                if (!_waitLeft)
                    _phase = Phase::Crawling;
            }

            if (soakerOn)
            {
                step.held = true;
                _grindMs = std::min(_t.grindMs, _grindMs + diff);
                std::uint32_t const due = _t.tickMs ? _grindMs / _t.tickMs : 0;
                step.ticks = due > _ticksDone ? due - _ticksDone : 0;
                _ticksDone = due;
                if (_grindMs >= _t.grindMs)
                {
                    _phase = Phase::Ground;
                    step.ground = true;
                }
                return step;
            }

            if (_phase == Phase::Crawling)
            {
                if (atBoss)
                {
                    _phase = Phase::Home;
                    step.home = true;
                    return step;
                }
                step.move = true;
            }
            return step;
        }

        Phase GetPhase() const { return _phase; }
        bool Done() const { return _phase == Phase::Ground || _phase == Phase::Home; }
        std::uint32_t GrindMs() const { return _grindMs; }
        std::uint32_t TicksDone() const { return _ticksDone; }
        // 0-100: how far it is ground down (kept when the soaker steps off).
        std::uint32_t GrindPct() const { return _t.grindMs ? _grindMs * 100 / _t.grindMs : 100; }

    private:
        PileTuning _t;
        Phase _phase = Phase::Waiting;
        std::uint32_t _waitLeft = 0;
        std::uint32_t _grindMs = 0;
        std::uint32_t _ticksDone = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RG8 Frenzy stacks
    // ----------------------------------------------------------------------------------------------------------------
    // A break halves them (rounded down): the stacks left.
    constexpr std::uint32_t FrenzyAfterBreak(std::uint32_t stacks) { return stacks / 2; }
    // A pile home: +5, capped.
    constexpr std::uint32_t FrenzyAfterHome(std::uint32_t stacks)
    {
        return std::min(kFrenzyMaxStacks, stacks + kPileHomeFrenzy);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG4 Ossuary Eruption: the rings in order, each registered when the last resolves (its warning is the gap)
    // ----------------------------------------------------------------------------------------------------------------
    struct EruptionRing
    {
        float inner = 0.f;          // 0: a circle
        float outer = 0.f;
        std::uint32_t warnMs = 0;   // from the previous ring's resolve (the first: from the stomp)
        bool inward = false;        // heroic's way back
    };

    inline std::vector<EruptionRing> EruptionRings(bool heroic)
    {
        std::vector<EruptionRing> rings{
            { 0.f, 6.f, kEruptionCastMs, false },
            { 6.f, 12.f, kEruptionOutStepMs, false },
            { kEruptionOuterInner, 18.f, kEruptionOutStepMs, false },
        };
        if (heroic)
        {
            // Back inward, 1 s apart (handoff section 3.4: three more rings, outermost first).
            rings.push_back({ kEruptionOuterInner, 18.f, kEruptionInStepMs, true });
            rings.push_back({ 6.f, 12.f, kEruptionInStepMs, true });
            rings.push_back({ 0.f, 6.f, kEruptionInStepMs, true });
        }
        return rings;
    }

    // Each ring's resolve time from the stomp.
    inline std::vector<std::uint32_t> EruptionResolveTimes(bool heroic)
    {
        std::vector<std::uint32_t> at;
        std::uint32_t t = 0;
        for (EruptionRing const& ring : EruptionRings(heroic))
        {
            t += ring.warnMs;
            at.push_back(t);
        }
        return at;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG5 Salvage
    // ----------------------------------------------------------------------------------------------------------------
    // He may start one now: the second break has happened, a construct is left, and `now` is past `notBefore` (30 s
    // after the last start; kSalvageAfterBreakMs after the second break for the first).
    constexpr bool SalvageMayStart(std::uint32_t breaks, std::uint32_t constructsLeft, std::uint64_t now,
        std::uint64_t notBefore)
    {
        return breaks >= kSalvageFromBreak && constructsLeft > 0 && now >= notBefore;
    }

    // The damage taken during the channel that stops it: 5% of his maximum health (rounded up).
    constexpr std::uint64_t SalvageBreakDamage(std::uint64_t maxHealth)
    {
        return (maxHealth * static_cast<std::uint64_t>(kSalvageBreakPct * 100.f) + 9999) / 10000;
    }

    constexpr bool BreaksSalvage(std::uint64_t damageInChannel, std::uint64_t maxHealth)
    {
        return damageInChannel >= SalvageBreakDamage(maxHealth);
    }

    // The nearest construct still standing (index into kConstructSpots), nullopt when all are spent.
    inline std::optional<std::size_t> NearestConstruct(Vec2 from, std::array<bool, 4> const& standing)
    {
        std::optional<std::size_t> best;
        float bestDist = 0.f;
        for (std::size_t i = 0; i < ScholomanceRework::kConstructSpots.size(); ++i)
        {
            if (!standing[i])
                continue;
            float const d = DungeonKit::Distance(from, ScholomanceRework::kConstructSpots[i].XY());
            if (!best || d < bestDist)
            {
                best = i;
                bestDist = d;
            }
        }
        return best;
    }

    // A percent of his maximum health (the heals' base points).
    constexpr std::int32_t PctOfMax(std::uint64_t maxHealth, float pct)
    {
        return static_cast<std::int32_t>(static_cast<double>(maxHealth) * pct / 100.0 + 0.5);
    }
}

#endif
