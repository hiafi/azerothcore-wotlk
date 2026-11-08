/*
 * mod-dungeon-bosses, Shadowfang Keep: Rethilgore (WP-S1), the pure, host-testable part (no engine headers): spell ids,
 * per-difficulty tuning numbers, timers, target picks and geometry. Build spec: SK 310-353 (normal and heroic), SK
 * 191-309 (design), RG1-RG6; handoff section 3.5 rows RG, section 3.6 row S1, section 3.8 (the cell block).
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum
 * (apps/dbc-tools source/npcs/shadowfang_keep/rethilgore.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the same on both difficulties:
 * the reference row (normal 1,300 / heroic 4,120) makes the difference. Tested by tests/sfk_rethilgore_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_RETHILGORE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_RETHILGORE_LOGIC_H

#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace Rethilgore
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ShadowfangKeepRework::CellId;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsRethilgore;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/rethilgore.py. Visuals are copied from stock spells (the
    // stock spells themselves are never cast); the ids come from WP-V's source/npcs/shadowfang_keep/_visuals.py.
    enum RethilgoreSpells : std::uint32_t
    {
        SPELL_LOCK_UP_LEAP          = 205910,   // RG1: the leap's look on the grabbed player (Charge SV 11546), DUMMY
        SPELL_LOCK_UP_CAST          = 205911,   // RG1: the 1.5 s "Lock-Up" cast bar (no effect, not interruptible)
        SPELL_CELL_THROW_FLASH      = 205912,   // RG1: a flash at both ends of the throw (Shadow Port SV 3303)
        SPELL_SOUL_DRAIN            = 205913,   // RG4: the channel on the prisoner (SV 680, the soul beam), a look
                                                // only; not interruptible, not dispellable, he keeps meleeing
        SPELL_SOUL_DRAIN_TICK       = 205914,   // RG4: 5% Shadow per 2 s tick (spell_sfk_rethilgore_soul_drain RefFlat)
        SPELL_SOUL_RETURN           = 205915,   // RG5: a caught fragment heals the prisoner (value from the script)
        SPELL_SOUL_STREAK           = 205916,   // RG5: a fragment streaks to its owner or to him (SV 9253), visual
        SPELL_SOUL_FEAST            = 205917,   // RG5: a missed fragment heals him 5% of his max health
        SPELL_CELL_KEY              = 205918,   // RG3: the Cell Key carrier buff (one at most)
        SPELL_TAINTED_FRAGMENT      = 205919,   // RG6 heroic: the registry Mine's resolve copy, Shadow
        // 205920-205929 spare
    };
    static_assert(kSlice.Contains(SPELL_LOCK_UP_LEAP) && kSlice.Contains(SPELL_TAINTED_FRAGMENT),
        "Rethilgore's spells stay inside his slice");

    // Registry tags (ledger and failure listing): the build spec's mechanic numbers.
    inline constexpr std::uint32_t kTagCellKey = 3;         // RG3: key pickups and the carrier-only door delivery
    inline constexpr std::uint32_t kTagSoulFragment = 5;    // RG5
    inline constexpr std::uint32_t kTagTaintedFragment = 6; // RG6

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec RG1-RG6, "Tuning starting points"). Times in ms, damage in % of the reference row.
    // ----------------------------------------------------------------------------------------------------------------

    // RG1 Lock-Up: at 10 s, then every 25 s; a Lock-Up due while someone is jailed waits until the cell block is empty
    // (and has been for kLockUpAfterFreeMs, so a freed player is not thrown straight back in). The emote and the
    // 1.5 s cast bar come first; then he leaps onto the target and throws it into a random cell.
    inline constexpr std::uint32_t kLockUpFirstMs = 10000;
    inline constexpr std::uint32_t kLockUpCooldownMs = 25000;
    inline constexpr std::uint32_t kLockUpWarnMs = 1500;
    inline constexpr std::uint32_t kLockUpAfterFreeMs = 2000;
    inline constexpr std::uint32_t kLockUpRetryMs = 1000;       // nobody to grab (or the grab failed): try again soon
    inline constexpr float kLockUpRange = 40.f;                 // targets within this many yd of him
    inline constexpr float kLeapSpeedXY = 25.f;
    inline constexpr float kLeapMinSpeedZ = 6.f;
    inline constexpr std::uint32_t kThrowAfterLandingMs = 250;  // the throw follows his landing by this much
    inline constexpr std::uint32_t kThrowMinDelayMs = 400;

    // RG2 Cell Door stand-in: about 6 s of two DPS players (60 / 1,000 DPS each).
    inline constexpr NH<std::uint32_t> kDoorHealth{ 720, 12000 };

    // RG3 Cell Key: he fumbles one at 66% and one at 33% (two per fight); it lies on the floor until picked up.
    inline constexpr std::array<float, 2> kKeyThresholdsPct{ { 66.f, 33.f } };
    inline constexpr float kKeyRadius = 1.5f;
    inline constexpr std::uint32_t kKeyLifeMs = 600000;         // the fight's length, in practice "until picked up"
    inline constexpr float kDeliveryRadius = 3.f;               // a carrier this close to the jailed door opens it

    // RG4 Soul Drain: the channel starts 1 s after the throw; a tick every 2 s, 5% Shadow of the non-tank row.
    inline constexpr std::uint32_t kDrainStartMs = 1000;
    inline constexpr std::uint32_t kDrainTickMs = 2000;
    inline constexpr float kDrainPct = 5.f;

    // RG5 Soul Fragment: one per tick at a free fragment point of the cell; 6 s, then it streaks to him. Caught: heals
    // the prisoner 5% of the non-tank row. Missed: heals him 5% of his max health.
    inline constexpr std::uint32_t kFragmentLifeMs = 6000;
    inline constexpr float kFragmentRadius = 1.5f;
    inline constexpr float kFragmentHealPct = 5.f;
    inline constexpr float kFragmentFeastPct = 5.f;
    inline constexpr float kFragmentMinGap = 2.f;               // live fragments and tainted ones stay this far apart

    // RG6 Tainted Fragment (heroic): the second fragment of every Lock-Up comes out tainted, a registry Mine: 1.5 yd,
    // arms in 0.5 s, no grace (a touch pops it), 40 s, 25% Shadow + 1 Weakened on the toucher.
    inline constexpr NH<bool> kTaintedSouls{ false, true };
    inline constexpr std::uint32_t kTaintedTick = 2;
    inline constexpr float kTaintedRadius = 1.5f;
    inline constexpr std::uint32_t kTaintedArmMs = 500;
    inline constexpr std::uint32_t kTaintedGraceMs = 0;
    inline constexpr std::uint32_t kTaintedLifeMs = 40000;
    inline constexpr float kTaintedPct = 25.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Rules
    // ----------------------------------------------------------------------------------------------------------------

    // RG1's clock: due at kLockUpFirstMs, then kLockUpCooldownMs after each Lock-Up; a due Lock-Up waits while someone
    // is jailed, then fires once the cell block has been empty for kLockUpAfterFreeMs.
    class LockUpClock
    {
    public:
        void Start()
        {
            _untilMs = kLockUpFirstMs;
            _emptyMs = kLockUpAfterFreeMs;
        }

        // True when Lock-Up should start now (then call Fired, or Retry when it could not).
        bool Update(std::uint32_t diff, bool jailed)
        {
            _untilMs = diff >= _untilMs ? 0 : _untilMs - diff;
            if (jailed)
                _emptyMs = 0;
            else
                _emptyMs = diff >= kLockUpAfterFreeMs - _emptyMs ? kLockUpAfterFreeMs : _emptyMs + diff;
            return !_untilMs && !jailed && _emptyMs >= kLockUpAfterFreeMs;
        }

        void Fired() { _untilMs = kLockUpCooldownMs; }
        void Retry() { _untilMs = kLockUpRetryMs; }
        std::uint32_t UntilDueMs() const { return _untilMs; }
        bool Waiting() const { return !_untilMs; }

    private:
        std::uint32_t _untilMs = kLockUpFirstMs;
        std::uint32_t _emptyMs = kLockUpAfterFreeMs;    // never above kLockUpAfterFreeMs
    };

    // RG3's keys: how many new keys a health drop to `pctAfter` releases, given `dropped` keys so far.
    constexpr std::uint32_t NewKeys(float pctAfter, std::uint32_t dropped)
    {
        std::uint32_t due = 0;
        for (float const t : kKeyThresholdsPct)
            if (pctAfter <= t)
                ++due;
        return due > dropped ? due - dropped : 0;
    }

    // Where key `index` (0 = the 66% key) lands: along the corridor, 8 to 12 yd from him (handoff section 3.8; a
    // throw across the 7 yd corridor would hit the wall).
    inline ShadowfangKeepRework::Point3 KeyLanding(std::uint32_t index)
    {
        return ShadowfangKeepRework::kKeyLandings[index % ShadowfangKeepRework::kKeyLandings.size()];
    }

    // RG5 fragment points of a cell (corridor side, 3 to 6 yd from its door).
    inline std::vector<Vec2> FragmentPoints(CellId cell)
    {
        using namespace ShadowfangKeepRework;
        switch (cell)
        {
            case CELL_S:
                return { kFragmentPointsS.begin(), kFragmentPointsS.end() };
            case CELL_M:
                return { kFragmentPointsM.begin(), kFragmentPointsM.end() };
            default:
                return { kFragmentPointsN.begin(), kFragmentPointsN.end() };
        }
    }

    // RG6 tainted points of a cell: its own fragment points, except the N cell, whose points lie in the corridor's
    // narrow WNW third, where one 1.5 yd circle nearly walls the cell off (handoff section 7 #17): an N Lock-Up's
    // tainted fragment takes an M point (the wide corridor's WNW end, 7.7 yd from the N door) instead.
    inline std::vector<Vec2> TaintedPoints(CellId cell)
    {
        return FragmentPoints(cell == ShadowfangKeepRework::CELL_N ? ShadowfangKeepRework::CELL_M : cell);
    }

    // A random point of `points` at least `minGap` yd from every `occupied` spot; nullopt when every point is taken (no
    // fragment that tick: the M cell has two points for up to three live fragments). `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickFreePoint(std::vector<Vec2> const& points, std::vector<Vec2> const& occupied,
        float minGap, Rand&& rand)
    {
        std::vector<std::size_t> free;
        for (std::size_t i = 0; i < points.size(); ++i)
        {
            bool clear = true;
            for (Vec2 const& o : occupied)
                if (DungeonKit::Distance(points[i], o) < minGap)
                    clear = false;
            if (clear)
                free.push_back(i);
        }
        if (free.empty())
            return std::nullopt;
        std::size_t const n = free.size();
        return free[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(n))) % n];
    }

    // RG6: drain tick `tick` (1 = the first of this Lock-Up) comes out tainted.
    constexpr bool TaintedOnTick(bool heroic, std::uint32_t tick)
    {
        return kTaintedSouls(heroic) && tick == kTaintedTick;
    }

    // The cell occupant who speaks when a player lands in their cell, and the text group (SK "Text").
    struct Cellmate
    {
        std::uint32_t entry = 0;
        std::uint8_t textGroup = 0;
    };

    constexpr Cellmate CellmateOf(CellId cell)
    {
        using namespace ShadowfangKeepRework;
        return cell == CELL_S ? Cellmate{ NPC_ADAMANT, SAY_ADAMANT_CELLMATE }
            : cell == CELL_M ? Cellmate{ NPC_ASHCROMBE, SAY_ASHCROMBE_CELLMATE }
            : Cellmate{ NPC_LANDEN_STILWELL, SAY_LANDEN_CELLMATE };
    }

    // A cell from a random number (any value: taken modulo the cell count).
    constexpr CellId CellFromRoll(std::uint32_t roll)
    {
        return CellId(roll % ShadowfangKeepRework::kCellCount);
    }

    // The throw's delay after the leap starts: his flight time over `distYd` plus kThrowAfterLandingMs.
    constexpr std::uint32_t ThrowDelayMs(float distYd)
    {
        float const flight = distYd > 0.f ? distYd / kLeapSpeedXY * 1000.f : 0.f;
        std::uint32_t const ms = static_cast<std::uint32_t>(flight) + kThrowAfterLandingMs;
        return ms < kThrowMinDelayMs ? kThrowMinDelayMs : ms;
    }
}

#endif
