/*
 * mod-dungeon-bosses, Ragefire Chasm D2: Jergosh the Invoker, the pure, host-testable part (no engine headers). Build
 * spec: docs/dungeons/ragefire-chasm-rework.md "Jergosh the Invoker" (JR1-JR5, ruling 15); handoff sections 3.5 row D2,
 * 3.6, 3.8, 3.12, 7 #21, #29, #35, #36. Tested by tests/rfc_jergosh_test.cpp; apps/dbc-tools
 * lib/test_ragefire_chasm_jergosh.py pins the data against this file and RagefireChasmRework.h.
 *
 *   JergoshSpells / JergoshTags     the spells (kSpellsJergosh) and the registry tags (the drill's: 6 and 7)
 *   Timeline                        the fight's clock: Conflagrate first and always on its grid, then Drain Soul, then
 *                                   Immolate, then the curse; an Immolate that would run into Conflagrate is skipped
 *   ImmolateFull                    he lights nobody while three burn (the fire's spread may still exceed it)
 *   Outsiders                       who the random picks skip: whoever is off his hall
 *   ImmolatePick                    any player, the tank included, never one already burning
 *   BurningAfter                    Conflagrate's fire: every burn consumed, then (heroic) whoever another's ring hit
 *   TitheFactor / TitheScale        +15% damage dealt per eaten soul, no cap; the look grows five steps
 *   WispStart                       4 yd off its owner, toward the offering spot (no catch on spawn)
 *
 * The numbers are RagefireChasmRework::Jergosh (`Tune` below): never restate one here.
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_JERGOSH_LOGIC_H
#define MOD_DUNGEON_BOSSES_RFC_JERGOSH_LOGIC_H

#include "DungeonKitLogic.h"
#include "RagefireChasmRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <utility>
#include <vector>

namespace RfcJergosh
{
    namespace Tune = RagefireChasmRework::Jergosh;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (RagefireChasmRework.h; ids.yaml reservation `ragefire_chasm`).
    inline constexpr RagefireChasmRework::IdSlice kSpellSlice = RagefireChasmRework::kSpellsJergosh;

    // apps/dbc-tools source/npcs/ragefire_chasm/jergosh.py declares them.
    enum JergoshSpells : std::uint32_t
    {
        SPELL_JR_IMMOLATE           = kSpellSlice.first + 0,    // JR1: the kickable 2 s cast; effect 0 the hit, effect
                                                                // 1 the Magic DoT (both script base points)
        SPELL_JR_CONFLAGRATE_CAST   = kSpellSlice.first + 1,    // JR2: the 2.5 s bar (Arcane: rule 25)
        SPELL_JR_CONFLAGRATE        = kSpellSlice.first + 2,    // JR2: the rings' hit (resolve copy, Fire)
        SPELL_JR_CONFLAGRATE_BEARER = kSpellSlice.first + 3,    // JR2: the bearer's own hit (script base point)
        SPELL_JR_DRAIN_SOUL         = kSpellSlice.first + 4,    // JR4: the kickable 3 s channel (heroic)
        SPELL_JR_SOUL_TEAR          = kSpellSlice.first + 5,    // JR4: the completed channel's hit (script base point)
        SPELL_JR_SOUL_SICK          = kSpellSlice.first + 6,    // JR5: an eaten soul's owner
        SPELL_JR_TITHE              = kSpellSlice.first + 7,    // JR5: his stacks
        SPELL_JR_OFFERING_SPOT      = kSpellSlice.first + 8,    // JR5: the shadow patch on the stalker
        SPELL_JR_FEED_LOOK          = kSpellSlice.first + 9,    // JR5: the look on him as a soul arrives
    };

    // Registry tags (G1's ragefire-chasm-shapes rows burn-spread and wisp-soak use the same two).
    enum JergoshTags : std::uint32_t
    {
        TAG_JR_CONFLAGRATE  = 6,
        TAG_JR_WISP         = 7,
    };

    // The descriptor: Drain Soul before Immolate; nothing to dispel (Immolate is DispelType none, user 2026-11-25).
    inline constexpr std::uint8_t kDrainSoulKickPriority = 2;
    inline constexpr std::uint8_t kImmolateKickPriority = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's clock
    // ----------------------------------------------------------------------------------------------------------------

    enum class Act : std::uint8_t
    {
        None,
        Conflagrate,
        DrainSoul,      // heroic
        Immolate,
        Curse,
    };

    // A cast the engine refused (a school lockout after a kick) is tried again this soon; its grid stays.
    inline constexpr std::uint32_t kRetryMs = 500;
    // A cast that would end later than this before Conflagrate's beat does not start (update ticks).
    inline constexpr std::uint32_t kBeatMarginMs = 250;

    // A beat on a fixed grid: a late cast never moves the ones after it.
    struct Grid
    {
        std::uint64_t due = std::numeric_limits<std::uint64_t>::max();
        std::uint64_t heldUntil = 0;
        std::uint32_t every = 0;

        void Start(std::uint32_t firstMs, std::uint32_t everyMs)
        {
            due = firstMs;
            heldUntil = 0;
            every = everyMs;
        }
        bool Running() const { return every != 0; }
        bool Due(std::uint64_t now) const { return Running() && now >= due && now >= heldUntil; }
        // The next beat still ahead.
        void Done(std::uint64_t now)
        {
            heldUntil = 0;
            if (!Running())
                return;
            do
                due += every;
            while (due <= now);
        }
        void Retry(std::uint64_t now) { heldUntil = now + kRetryMs; }
    };

    // Conflagrate is never late: nothing starts that would still run at its beat (ruling 15's re-lit burns last 21 s,
    // one second more than its period, so a beat a second late would let them lapse). An Immolate that does not fit is
    // skipped, not delayed (the next is 3 s away). A Drain Soul that does not fit waits.
    class Timeline
    {
    public:
        void Start(bool heroic)
        {
            *this = Timeline();
            _conflagrate.Start(Tune::kConflagrateFirstMs(heroic), Tune::kConflagrateEveryMs(heroic));
            _immolate.Start(Tune::kImmolateFirstMs(heroic), Tune::kImmolateEveryMs(heroic));
            _curse.Start(Tune::kCurseFirstMs, Tune::kCurseEveryMs);
            if (heroic)
                _drain.Start(Tune::kDrainSoulFirstMs, Tune::kDrainSoulEveryMs);
        }

        std::uint64_t Now() const { return _now; }

        // True when an Immolate beat was skipped for Conflagrate.
        bool Advance(std::uint32_t diff)
        {
            _now += diff;
            if (!_immolate.Running() || _now < _immolate.due || Fits(Tune::kImmolateCastMs))
                return false;
            _immolate.Done(_now);
            return true;
        }

        // What he casts now when he is free (the caller reports Done or Retry).
        Act Next() const
        {
            if (_conflagrate.Due(_now))
                return Act::Conflagrate;
            if (_drain.Due(_now) && Fits(Tune::kDrainSoulChannelMs))
                return Act::DrainSoul;
            if (_immolate.Due(_now) && Fits(Tune::kImmolateCastMs))
                return Act::Immolate;
            if (_curse.Due(_now))
                return Act::Curse;
            return Act::None;
        }

        void Done(Act act)
        {
            if (Grid* g = Of(act))
                g->Done(_now);
        }
        void Retry(Act act)
        {
            if (Grid* g = Of(act))
                g->Retry(_now);
        }
        // Milliseconds to the act's next beat (0: due or not running).
        std::uint32_t In(Act act)
        {
            Grid const* g = Of(act);
            return g && g->Running() && g->due > _now ? static_cast<std::uint32_t>(g->due - _now) : 0;
        }

    private:
        bool Fits(std::uint32_t castMs) const
        {
            return !_conflagrate.Running() || _now + castMs + kBeatMarginMs <= _conflagrate.due;
        }

        Grid* Of(Act act)
        {
            switch (act)
            {
                case Act::Conflagrate:
                    return &_conflagrate;
                case Act::DrainSoul:
                    return &_drain;
                case Act::Immolate:
                    return &_immolate;
                case Act::Curse:
                    return &_curse;
                case Act::None:
                    break;
            }
            return nullptr;
        }

        std::uint64_t _now = 0;
        Grid _conflagrate;
        Grid _drain;
        Grid _immolate;
        Grid _curse;
    };

    // A burn lit by one Conflagrate is still there for the next (the cascade of ruling 15).
    static_assert(Tune::kImmolateDurationMs >= Tune::kConflagrateEveryMs.heroic + 2 * kBeatMarginMs);
    static_assert(Tune::kImmolateDurationMs % Tune::kImmolateTickMs == 0);
    static_assert(Tune::kImmolateEveryMs.normal > Tune::kImmolateCastMs
        && Tune::kImmolateEveryMs.heroic > Tune::kImmolateCastMs);
    inline constexpr std::uint32_t kImmolateTicks = Tune::kImmolateDurationMs / Tune::kImmolateTickMs;

    // ----------------------------------------------------------------------------------------------------------------
    // JR1 and JR4 picks (section 7 #33 A: the tank and the healer are in every pool)
    // ----------------------------------------------------------------------------------------------------------------

    // The players a random pick skips, from (guid, in the hall): whoever is off it, unless nobody is on it.
    inline std::vector<std::uint64_t> Outsiders(std::vector<std::pair<std::uint64_t, bool>> const& players)
    {
        std::vector<std::uint64_t> out;
        for (auto const& [guid, inside] : players)
            if (!inside)
                out.push_back(guid);
        return out.size() == players.size() ? std::vector<std::uint64_t>() : out;
    }

    // He lights nobody while this many burn already, whoever lit them. One cast at a time: he never makes it a fourth.
    constexpr bool ImmolateFull(std::size_t burning)
    {
        return burning >= Tune::kImmolateMaxBurning;
    }

    // `skip`: everyone burning, and the Outsiders.
    inline DungeonKit::PickRule ImmolatePick(std::vector<std::uint64_t> skip)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.exclude = std::move(skip);
        return rule;
    }

    inline DungeonKit::PickRule DrainSoulPick(std::vector<std::uint64_t> outsiders)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.exclude = std::move(outsiders);
        return rule;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR2 Conflagrate
    // ----------------------------------------------------------------------------------------------------------------

    // The registry never reported the rings (the stale handle is dropped). Judged by the clock before this tick's: the
    // registry resolves at the end of the map tick, after the AI, so a lag tick past the bar's end is not a lost one.
    constexpr bool RingsLost(std::uint64_t clockBeforeTickMs, std::uint64_t endsAtMs)
    {
        return clockBeforeTickMs > endsAtMs + kRetryMs;
    }

    // Who burns once Conflagrate has resolved: every burn is consumed first; on heroic each distinct player another's
    // ring hit catches fire (a player in two rings is listed twice in `hits`, and is lit once; a bearer hit by another
    // bearer's ring ends burning). Normal: nobody.
    inline std::vector<std::uint64_t> BurningAfter(std::vector<std::uint64_t> const& hits, bool heroic)
    {
        std::vector<std::uint64_t> out;
        if (!heroic)
            return out;
        for (std::uint64_t const id : hits)
            if (std::find(out.begin(), out.end(), id) == out.end())
                out.push_back(id);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // JR5 the Tithe and the wisp
    // ----------------------------------------------------------------------------------------------------------------

    // The aura's stack ceiling: out of reach (a soul every 20 s; no cap by ruling 15).
    inline constexpr std::uint32_t kTitheMaxStacks = 99;
    static_assert(std::uint64_t(kTitheMaxStacks) * Tune::kDrainSoulEveryMs > 30ull * 60 * 1000);

    // What his own percent hits are multiplied by (they ignore the aura: SPELL_ATTR3_IGNORE_CASTER_MODIFIERS; the aura
    // itself raises his melee).
    constexpr float TitheFactor(std::uint32_t stacks)
    {
        return 1.f + static_cast<float>(stacks) * Tune::kTithePct / 100.f;
    }

    // His size, times his own scale.
    constexpr float TitheScale(std::uint32_t stacks)
    {
        return 1.f + static_cast<float>(std::min(stacks, Tune::kTitheScaleSteps)) * Tune::kTitheScaleStep;
    }

    inline constexpr float kWispReachYd = 1.5f;         // from the offering spot: eaten
    // A wisp never starts this close to the offering spot.
    inline constexpr float kWispGoalClearYd = Tune::kWispTouchYd + kWispReachYd;

    // Where an owner's wisp appears: 4 yd off them toward the offering spot; with a wall there, or an owner standing on
    // the spot, the nearest bearing to that line which keeps it on the hall floor and off the spot.
    inline Vec2 WispStart(Vec2 owner, Vec2 goal)
    {
        auto const at = [owner](float bearing)
        {
            return Vec2{ owner.x + std::cos(bearing) * Tune::kWispSpawnAheadYd,
                owner.y + std::sin(bearing) * Tune::kWispSpawnAheadYd };
        };
        float const toGoal = DungeonKit::Distance(owner, goal) > 0.1f ? DungeonKit::BearingTo(owner, goal)
            : DungeonKit::BearingTo(goal, RagefireChasmRework::kJergoshSpawn.XY());
        float constexpr kStep = DungeonKit::kTwoPi / 12.f;
        std::array<float, 12> constexpr kTurns{ 0.f, 1.f, -1.f, 2.f, -2.f, 3.f, -3.f, 4.f, -4.f, 5.f, -5.f, 6.f };
        for (float const turn : kTurns)
        {
            Vec2 const p = at(toGoal + turn * kStep);
            if (DungeonKit::PointInPolygon(RagefireChasmRework::kHallArenaPolygon, p)
                && DungeonKit::Distance(p, goal) >= kWispGoalClearYd)
                return p;
        }
        return RagefireChasmRework::ClampInto(RagefireChasmRework::kHallArenaPolygon, at(toGoal));
    }
}

#endif
