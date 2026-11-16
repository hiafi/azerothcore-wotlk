/*
 * mod-dungeon-bosses, Blackrock Spire B13:
 * The Beast (10430), the pure, host-testable part (no engine headers). Build spec: docs/dungeons/
 * blackrock-spire-rework.md "The Beast" (SP 3465-3698, BE1-BE10, rulings 65-67), handoff section 3.4 rows BE, 3.5 row
 * B13, 3.6, 3.8 (the pit and the hall). Tested by tests/brs_beast_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsBeast (210490-210519), declared in apps/dbc-tools
 *                source/npcs/blackrock_spire/the_beast.py
 *   Tuning       NH<> percents, FlexAB counts and the cadences, straight from the build spec
 *   Heat         BE2 the stack clock and what each stack changes (the roar's and the split's cadence, the pools' size)
 *   Beats        the cast queue of the fight: Dread's roar, Magma Split, Immolate and the Fire Blast filler, with the
 *                retiming a new Heat stack asks for
 *   Pools        BE3 how many a loss of health owes, where one may lie (the hall's rectangle and the pit's disc), its
 *                radius, its look, the crowd that sends the bot tank to fresh floor
 *   Molten Fury  BE4 the 2 s clock while he stands in lava
 *   Dread        BE5 the stack count that panics
 *   Eruption     BE7 the enrage
 *   Knockback    BE6 the speeds of a 5 yd throw
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_BEAST_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_BEAST_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace BrsBeast
{
    using BlackrockSpireRework::Arena;
    using BlackrockSpireRework::FlexAB;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsBeast;

    enum BeastSpells : std::uint32_t
    {
        SPELL_BE_HEAT               = kSpellSlice.first + 0,    // 210490 BE2 +10% damage done a stack, no cap
        SPELL_BE_MOLTEN_FURY        = kSpellSlice.first + 1,    // 210491 BE4 +10% damage done a stack, no cap
        SPELL_BE_ROAR               = kSpellSlice.first + 2,    // 210492 BE5 the 2 s roar (a cast bar, no kick)
        SPELL_BE_DREAD              = kSpellSlice.first + 3,    // 210493 BE5 the stacking fear of standing alone
        SPELL_BE_PANIC              = kSpellSlice.first + 4,    // 210494 BE5 the 2 s flee
        SPELL_BE_MAGMA_SPLIT_BAR    = kSpellSlice.first + 5,    // 210495 BE6 the 2 s cast bar
        SPELL_BE_MAGMA_SPLIT        = kSpellSlice.first + 6,    // 210496 BE6 the others' hit (resolve copy, Fire)
        SPELL_BE_MAGMA_SPLIT_TARGET = kSpellSlice.first + 7,    // 210497 BE6 the target's own hit (resolve copy, Fire)
        SPELL_BE_MOLTEN_BLOOD       = kSpellSlice.first + 8,    // 210498 BE3 a second in lava: 10% Fire
        SPELL_BE_ERUPTION           = kSpellSlice.first + 9,    // 210499 BE7 a second on the erupted floor: 10% Fire
        SPELL_BE_IMMOLATE           = kSpellSlice.first + 10,   // 210500 BE8 heroic: Immolate at 3% a second
        SPELL_BE_HEAT_FLASH         = kSpellSlice.first + 11,   // 210501 BE2 the chest flash at each new stack (look)
        SPELL_BE_POOL_LOOK_4        = kSpellSlice.first + 12,   // 210502 BE3 a pool's look, 4 yd rung ... 10 yd (+18)
        SPELL_BE_POOL_LOOK_10       = kSpellSlice.first + 18,   // 210508
        // 210509-210519 spare
    };
    static_assert(SPELL_BE_POOL_LOOK_10 <= kSpellSlice.last, "The Beast's spells must stay in his slice");

    // The stock casts kept (BE8, BE9) and the Elites' end (BE1).
    inline constexpr std::uint32_t SPELL_BE_IMMOLATE_STOCK = 15570;
    inline constexpr std::uint32_t SPELL_BE_FIRE_BLAST = 16144;
    inline constexpr std::uint32_t SPELL_BE_SUICIDE = 8329;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum BeastTags : std::uint32_t
    {
        TAG_POOL        = 3,    // BE3 Molten Blood pools (the puddle field)
        TAG_DREAD       = 5,    // BE5 the roar's stack
        TAG_SPLIT       = 6,    // BE6 Magma Split (the circle and the target's own hit)
        TAG_PARK        = 9,    // the bots' tank rule (hidden, tank-only)
    };

    // creature_text groups (data/sql/updates/pending_db_world/rev_the_beast_blackrock_spire.sql, SP "Text"; all boss
    // emotes, type 41). The Elites' line 0 "We're doomed!" is stock (creature 10317).
    enum BeastTexts : std::uint8_t
    {
        TEXT_ROAR       = 0,    // emote: "%s rears back to roar!" (BE5)
        TEXT_HEAT       = 1,    // emote: "%s's blood boils!" (BE2)
        TEXT_ERUPTION   = 2,    // emote: "The lair floor erupts in magma!" (BE7)
    };
    inline constexpr std::uint8_t SAY_BLACKHAND_DOOMED = 0;         // creature 10317, stock

    // The stock wake protocol (boss_the_beast.cpp; the area triggers 2066 / 2067 call the AI's SetData).
    inline constexpr std::uint32_t DATA_BEAST_REACHED = 1;          // area trigger 2066: he walks out of the pit
    inline constexpr std::uint32_t DATA_BEAST_ROOM = 2;             // area trigger 2067: the Elites' panic
    inline constexpr std::uint32_t BEAST_MOVEMENT_ID = 1379690;     // waypoint path out of the pit (17 points)
    inline constexpr std::uint32_t NPC_BLACKHAND_ELITE = 10317;
    inline constexpr float kEvadeLineY = -505.f;                    // stock: past this he evades (the hall's far side)
    inline constexpr float kElitesFindYd = 50.f;
    inline constexpr std::uint32_t kElitesMoveMs = 3000;            // after the yell they run, 9 s after it they die
    inline constexpr std::uint32_t kElitesDieMs = 9000;
    inline constexpr float kElitesRunRadiusYd = 10.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP "Build spec"; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // BE2 Heat: a stack every 20 s (heroic 15 s) from the pull, no cap: +10% damage done (his melee, Fire Blast and
    // Immolate; Magma Split adds it to its own percents, DamageMult) and half a yard on every new Molten Blood pool.
    inline constexpr NH<std::uint32_t> kHeatEveryMs{ 20000, 15000 };
    inline constexpr float kHeatDamagePct = 10.f;
    inline constexpr float kHeatPoolGrowYd = 0.5f;
    inline constexpr std::uint32_t kRoarFasterAtHeat = 3;           // at 3 stacks the roar comes every 15 s
    inline constexpr std::uint32_t kSplitFasterAtHeat = 5;          // at 5 stacks Magma Split does too

    // BE4 Molten Fury: while he stands in his own lava, +10% damage done every 2 s, kept to the end of the fight.
    inline constexpr std::uint32_t kFuryEveryMs = 2000;
    inline constexpr float kFuryDamagePct = 10.f;
    inline constexpr std::uint32_t kFuryPollMs = 250;

    // BE5 Dread: the roar's 2 s cast; anyone with fewer than 2 other players within 6 yd gains a Dread stack (fades
    // 30 s after the last); at 3 stacks (heroic 2) they panic: a 2 s flee, the stacks clear.
    inline constexpr std::uint32_t kRoarFirstMs = 10000;
    inline constexpr std::uint32_t kRoarCastMs = 2000;
    inline constexpr std::uint32_t kRoarEveryMs = 20000;
    inline constexpr std::uint32_t kRoarEveryHotMs = 15000;
    inline constexpr float kDreadRadiusYd = 6.f;
    inline constexpr std::uint8_t kDreadMinOthers = 2;
    inline constexpr NH<std::uint8_t> kDreadPanicAt{ 3, 2 };
    inline constexpr std::uint32_t kDreadMs = 30000;                // the Dread spell's duration (the DT test pins it)
    inline constexpr std::uint32_t kPanicMs = 2000;                 // the Panic spell's duration (the DT test pins it)
    inline constexpr std::uint32_t kDreadMaxStacks = 3;             // the Dread aura's CumulativeAura

    // BE6 Magma Split: the 2 s cast and a 6 yd circle on 2 random non-tanks (4 at 6 or more); the target takes 15%
    // Fire, anyone else inside 30% + Weakened and a 5 yd throw away from the target; heroic leaves a 4 yd pool where
    // the target stands. First at 20 s, then every 20 s (15 s from Heat 5).
    inline constexpr std::uint32_t kSplitFirstMs = 20000;
    inline constexpr std::uint32_t kSplitCastMs = 2000;
    inline constexpr std::uint32_t kSplitEveryMs = 20000;
    inline constexpr std::uint32_t kSplitEveryHotMs = 15000;
    inline constexpr FlexAB kSplitTargets{ 2, 4 };
    inline constexpr float kSplitRadiusYd = 6.f;
    inline constexpr float kSplitTargetPct = 15.f;
    inline constexpr float kSplitOthersPct = 30.f;
    inline constexpr float kSplitKnockYd = 5.f;
    inline constexpr float kSplitKnockSpeedZ = 6.f;
    inline constexpr float kSplitPoolRadiusYd = 4.f;                // heroic, no Heat growth
    inline constexpr std::uint32_t kSplitPoolMarkMs = 1000;         // the splash pool arms 1 s after it lands
    inline constexpr std::size_t kSplitPreferMax = 8;               // old pools a heroic target's drop rule prefers

    // BE3 Molten Blood: a pool for every 4% of his health lost (25 in all), in a random direction with its near edge
    // 5 yd from him, on open floor; 5 yd (heroic 4.5) + half a yard a Heat stack; a 1.5 s marker, then 10% Fire a
    // second (once, however many overlap) to anyone inside, for the whole fight.
    inline constexpr float kPoolEveryLostPct = 4.f;
    inline constexpr std::uint32_t kPoolMax = 25;
    inline constexpr float kPoolNearEdgeYd = 5.f;
    inline constexpr NH<float> kPoolRadiusYd{ 5.f, 4.5f };
    inline constexpr std::uint32_t kPoolMarkMs = 1500;
    inline constexpr std::uint32_t kPoolTickMs = 1000;
    inline constexpr float kPoolTickPct = 10.f;                     // the spell's own percent (the DT test pins it)
    inline constexpr std::uint32_t kPoolStaggerMs = 250;            // a burst of lost health lays them this far apart
    inline constexpr std::uint32_t kPoolRetryMs = 1000;             // no floor found: try again
    inline constexpr float kPoolRungMinYd = 4.f;                    // V-2's looks: 4..10 yd in 1 yd rungs
    inline constexpr float kPoolRungMaxYd = 10.f;
    inline constexpr std::uint32_t kPoolLookDelayMs = kPoolMarkMs;  // the lava shows as the marker arms

    // BE7 Eruption: the enrage. The whole floor is lava: 10% Fire a second to everyone, until the wipe.
    inline constexpr NH<std::uint32_t> kEruptionAtMs{ 120000, 100000 };
    inline constexpr std::uint32_t kEruptionTickMs = 1000;
    inline constexpr float kEruptionPct = 10.f;                     // the spell's own percent (the DT test pins it)

    // BE8 Immolate: stock 15570 on a random player (any role) at 3 s, then every 8 s. Heroic casts its own copy: 3% a
    // second, 21 s (the stock duration), and when it runs out a 4 yd pool lies where the player stands. A dispel
    // (the priest's Magic cure) or a death leaves no pool.
    inline constexpr std::uint32_t kImmolateFirstMs = 3000;
    inline constexpr std::uint32_t kImmolateEveryMs = 8000;
    inline constexpr float kImmolateTickPct = 3.f;                  // the spell's own percent (the DT test pins it)
    inline constexpr std::uint32_t kImmolateMs = 21000;             // the heroic copy's duration (the DT test pins it)
    inline constexpr float kImmolatePoolRadiusYd = 4.f;
    inline constexpr std::uint32_t kImmolatePoolMarkMs = 1500;

    // BE9 Fire Blast, stock 16144 on his target every 5 to 8 s: a filler that never delays a mechanic.
    inline constexpr std::uint32_t kFireBlastMinMs = 5000;
    inline constexpr std::uint32_t kFireBlastMaxMs = 8000;
    inline constexpr std::uint32_t kFireBlastDropMs = 3000;        // a turn that waited this long is skipped

    // The bots' tank rule: when this many pools lie within kCrowdEdgeYd of his feet, a tank-only Park circle on clean
    // floor kParkMinYd..kParkMaxYd away draws the boss out (Galford's rule; no wall preference: PARTIAL).
    inline constexpr std::size_t kCrowdPools = 4;
    inline constexpr float kCrowdEdgeYd = 8.f;
    inline constexpr std::uint32_t kParkCheckMs = 1000;
    inline constexpr std::uint32_t kParkHoldMs = 6000;
    inline constexpr std::uint32_t kParkCooldownMs = 4000;
    inline constexpr float kParkRadiusYd = 3.f;
    inline constexpr float kParkMinYd = 10.f;
    inline constexpr float kParkMaxYd = 28.f;
    inline constexpr float kParkClearYd = 7.f;                      // the spot this far off every pool's edge

    // ----------------------------------------------------------------------------------------------------------------
    // The floor (NAVMESH 12): the pit is a bowl, the hall a flat rectangle
    // ----------------------------------------------------------------------------------------------------------------

    // A pool must lie wholly on open floor. The hall: the rectangle x 17..83, y -561..-513 (no pillar holes inside).
    // The pit: a disc of radius 18 about its centre (117.2, -561.2) (the z < 110.5 bowl). Nothing else is used: a pool
    // is never put on the ramp or in the corridors (the navmesh check the handoff allowed there is not needed).
    inline constexpr float kHallMinX = 17.f;
    inline constexpr float kHallMaxX = 83.f;
    inline constexpr float kHallMinY = -561.f;
    inline constexpr float kHallMaxY = -513.f;
    inline constexpr float kHallZMin = 109.5f;
    inline constexpr float kHallZMax = 113.5f;
    inline constexpr Vec2 kPitCenter{ 117.2f, -561.2f };
    inline constexpr float kPitRadiusYd = 18.f;
    inline constexpr float kPitZMin = 105.f;
    inline constexpr float kPitZMax = 113.f;

    // The disc (c, r) lies wholly on the hall or wholly on the pit's bowl.
    inline bool PoolFits(Vec2 c, float r)
    {
        bool const hall = c.x - r >= kHallMinX && c.x + r <= kHallMaxX && c.y - r >= kHallMinY && c.y + r <= kHallMaxY;
        bool const pit = DungeonKit::Distance(c, kPitCenter) + r <= kPitRadiusYd;
        return hall || pit;
    }

    // The arena a pool's centre may lie in: the hall rectangle and the pit disc, each shrunk by the pool's radius.
    inline Arena PoolArena(float r)
    {
        std::vector<DungeonKit::ArenaRegion> regions;
        if (kHallMaxX - kHallMinX > 2.f * r && kHallMaxY - kHallMinY > 2.f * r)
            regions.push_back(DungeonKit::ArenaRegion::Polygon({ { kHallMinX + r, kHallMinY + r },
                { kHallMaxX - r, kHallMinY + r }, { kHallMaxX - r, kHallMaxY - r }, { kHallMinX + r, kHallMaxY - r } },
                kHallZMin, kHallZMax));
        if (kPitRadiusYd > r)
            regions.push_back(DungeonKit::ArenaRegion::Circle(kPitCenter, kPitRadiusYd - r, kPitZMin, kPitZMax));
        return Arena(std::move(regions));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE2 Heat and what a stack changes
    // ----------------------------------------------------------------------------------------------------------------

    constexpr std::uint32_t RoarEveryMs(std::uint32_t heat)
    {
        return heat >= kRoarFasterAtHeat ? kRoarEveryHotMs : kRoarEveryMs;
    }

    constexpr std::uint32_t SplitEveryMs(std::uint32_t heat)
    {
        return heat >= kSplitFasterAtHeat ? kSplitEveryHotMs : kSplitEveryMs;
    }

    // The Heat stacks he has `elapsedMs` into the fight (the first at one period).
    constexpr std::uint32_t HeatAt(bool heroic, std::uint64_t elapsedMs)
    {
        return static_cast<std::uint32_t>(elapsedMs / kHeatEveryMs(heroic));
    }

    // His damage multiplier from `heat` and `fury` stacks (each +10%): applied to Magma Split's percents (the custom
    // hits ignore caster modifiers, so the aura alone would not raise them).
    constexpr float DamageMult(std::uint32_t heat, std::uint32_t fury)
    {
        return 1.f + (kHeatDamagePct * static_cast<float>(heat) + kFuryDamagePct * static_cast<float>(fury)) / 100.f;
    }

    // A beat that is due later than `lastFiredMs + newEveryMs` moves up to it (never into the past): a new Heat stack
    // that shortens a cadence takes effect at once for a beat that has fired before.
    constexpr std::uint64_t RetimeDue(std::uint64_t dueMs, std::uint64_t lastFiredMs, std::uint32_t newEveryMs,
        std::uint64_t nowMs)
    {
        std::uint64_t const target = std::max<std::uint64_t>(nowMs, lastFiredMs + newEveryMs);
        return std::min<std::uint64_t>(dueMs, target);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Beats: the fight's cast queue (the kit's CastQueue; one cast at a time)
    // ----------------------------------------------------------------------------------------------------------------

    enum BeastCast : std::uint32_t
    {
        CAST_ROAR       = 1,
        CAST_SPLIT      = 2,
        CAST_IMMOLATE   = 3,
        CAST_FIRE_BLAST = 4,
    };

    inline constexpr std::uint8_t kPriorityRoar = 3;
    inline constexpr std::uint8_t kPrioritySplit = 3;
    inline constexpr std::uint8_t kPriorityImmolate = 2;
    inline constexpr std::uint8_t kPriorityFireBlast = 0;
    inline constexpr std::uint32_t kCastSpacingMs = 500;            // after a cast bar ends, the next waits this long
    inline constexpr std::uint32_t kBarGapMs = 5000;                // a roar and a split start at least this far apart

    class Beats
    {
    public:
        static constexpr std::uint64_t kNever = ~std::uint64_t(0);

        Beats() : _queue(kCastSpacingMs) { }

        // The pull: roar, split and Immolate at their first times; the Fire Blast after `fireBlastFirstMs` (rolled
        // 5..8 s by the caller).
        void Start(std::uint64_t nowMs, std::uint32_t fireBlastFirstMs)
        {
            _queue.Reset();
            _lastRoar = _lastSplit = kNever;
            _queue.Schedule(CAST_ROAR, nowMs + kRoarFirstMs, kPriorityRoar);
            _queue.Schedule(CAST_SPLIT, nowMs + kSplitFirstMs, kPrioritySplit);
            _queue.Schedule(CAST_IMMOLATE, nowMs + kImmolateFirstMs, kPriorityImmolate);
            _queue.Schedule(CAST_FIRE_BLAST, nowMs + fireBlastFirstMs, kPriorityFireBlast, kFireBlastDropMs);
        }

        void Reset()
        {
            _queue.Reset();
            _lastRoar = _lastSplit = kNever;
        }

        // The cast to start now (nullopt: nothing due, or he is still in one). A filler that waited past its drop time
        // is dropped, and the script schedules its next turn through Dropped().
        std::optional<std::uint32_t> Next(std::uint64_t nowMs)
        {
            return _queue.Next(nowMs);
        }

        // The ids whose turn lapsed (only the Fire Blast filler has a drop time): rescheduled `fireBlastNextMs` on.
        std::vector<std::uint32_t> DropStale(std::uint64_t nowMs, std::uint32_t fireBlastNextMs)
        {
            std::vector<std::uint32_t> const dropped = _queue.DropStale(nowMs);
            for (std::uint32_t id : dropped)
                if (id == CAST_FIRE_BLAST)
                    _queue.Schedule(id, nowMs + fireBlastNextMs, kPriorityFireBlast, kFireBlastDropMs);
            return dropped;
        }

        // `id` started at `nowMs`; the next one is scheduled from now with `heat` stacks deciding the cadence.
        // `fireBlastNextMs`: the roll for the filler.
        void Started(std::uint32_t id, std::uint64_t nowMs, std::uint32_t heat, std::uint32_t fireBlastNextMs)
        {
            switch (id)
            {
                case CAST_ROAR:
                    _lastRoar = nowMs;
                    _queue.Started(id, nowMs, kRoarCastMs);
                    _queue.Schedule(id, nowMs + RoarEveryMs(heat), kPriorityRoar);
                    KeepApart(CAST_SPLIT, kPrioritySplit, nowMs);
                    break;
                case CAST_SPLIT:
                    _lastSplit = nowMs;
                    _queue.Started(id, nowMs, kSplitCastMs);
                    _queue.Schedule(id, nowMs + SplitEveryMs(heat), kPrioritySplit);
                    KeepApart(CAST_ROAR, kPriorityRoar, nowMs);
                    break;
                case CAST_IMMOLATE:
                    _queue.Started(id, nowMs, 0, false);
                    _queue.Schedule(id, nowMs + kImmolateEveryMs, kPriorityImmolate);
                    break;
                case CAST_FIRE_BLAST:
                    _queue.Started(id, nowMs, 0, false);
                    _queue.Schedule(id, nowMs + fireBlastNextMs, kPriorityFireBlast, kFireBlastDropMs);
                    break;
                default:
                    _queue.Started(id, nowMs, 0, false);
                    break;
            }
        }

        // A Heat stack landed: the cadences of the roar and the split may have changed.
        void OnHeat(std::uint32_t heat, std::uint64_t nowMs)
        {
            Retime(CAST_ROAR, kPriorityRoar, _lastRoar, RoarEveryMs(heat), nowMs);
            Retime(CAST_SPLIT, kPrioritySplit, _lastSplit, SplitEveryMs(heat), nowMs);
        }

        void Interrupted(std::uint64_t nowMs) { _queue.Interrupted(nowMs); }
        std::optional<std::uint64_t> DueAt(std::uint32_t id) const { return _queue.DueAt(id); }
        bool Waiting(std::uint64_t nowMs) const { return _queue.Waiting(nowMs); }

    private:
        // The roar packs the group and Magma Split spreads it: a bar of the other kind that would start within
        // kBarGapMs of this one waits until that long after it (a collision of the two cadences moves the later one
        // for good, so the two settle into an alternation instead of colliding again).
        void KeepApart(std::uint32_t other, std::uint8_t priority, std::uint64_t nowMs)
        {
            std::optional<std::uint64_t> const due = _queue.DueAt(other);
            if (due && *due < nowMs + kBarGapMs)
                _queue.Schedule(other, nowMs + kBarGapMs, priority);
        }

        void Retime(std::uint32_t id, std::uint8_t priority, std::uint64_t last, std::uint32_t every,
            std::uint64_t nowMs)
        {
            std::optional<std::uint64_t> const due = _queue.DueAt(id);
            if (!due || last == kNever)
                return;
            std::uint64_t const next = RetimeDue(*due, last, every, nowMs);
            if (next != *due)
                _queue.Schedule(id, next, priority);
        }

        DungeonKit::CastQueue _queue;
        std::uint64_t _lastRoar = kNever;
        std::uint64_t _lastSplit = kNever;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // BE3 Molten Blood: how many, how big, where, which look
    // ----------------------------------------------------------------------------------------------------------------

    // The pools owed for `healthPct` (0..100) with `placed` laid: one for every 4% lost, at most 25 in all.
    inline std::uint32_t PoolsOwed(float healthPct, std::uint32_t placed)
    {
        float const lost = std::clamp(100.f - healthPct, 0.f, 100.f);
        auto const due = static_cast<std::uint32_t>(std::floor(lost / kPoolEveryLostPct + 1e-4f));
        std::uint32_t const total = std::min(due, kPoolMax);
        return total > placed ? total - placed : 0;
    }

    constexpr float PoolRadius(bool heroic, std::uint32_t heat)
    {
        return kPoolRadiusYd(heroic) + kHeatPoolGrowYd * static_cast<float>(heat);
    }

    // The distance from him to a new pool's centre: its near edge is 5 yd from him.
    constexpr float PoolRingYd(float radius)
    {
        return kPoolNearEdgeYd + radius;
    }

    // V-2's look rung for a pool of `radius` yd: the smallest of the 1 yd rungs 4..10 at or above it, 10 the top.
    inline int PoolRung(float radius)
    {
        int const rung = static_cast<int>(std::ceil(radius - 1e-4f));
        return std::clamp(rung, static_cast<int>(kPoolRungMinYd), static_cast<int>(kPoolRungMaxYd));
    }

    inline std::uint32_t PoolLookSpell(float radius)
    {
        return SPELL_BE_POOL_LOOK_4 + static_cast<std::uint32_t>(PoolRung(radius) - static_cast<int>(kPoolRungMinYd));
    }

    struct PoolSpot
    {
        Vec2 center;
        float radius = 0.f;
    };

    // Pools whose edge lies within kCrowdEdgeYd of the boss: enough of them and the bot tank walks him to clean floor.
    inline std::size_t CrowdCount(Vec2 boss, std::span<PoolSpot const> pools)
    {
        std::size_t n = 0;
        for (PoolSpot const& p : pools)
            if (DungeonKit::Distance(boss, p.center) - p.radius <= kCrowdEdgeYd)
                ++n;
        return n;
    }

    inline bool ShouldPark(Vec2 boss, std::span<PoolSpot const> pools)
    {
        return CrowdCount(boss, pools) >= kCrowdPools;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE4 Molten Fury: a stack for every 2 s he stands in lava, counting only unbroken time
    // ----------------------------------------------------------------------------------------------------------------

    class FuryClock
    {
    public:
        // `inLava` for `dtMs`: the number of stacks to add now (0 or more).
        std::uint32_t Advance(bool inLava, std::uint32_t dtMs)
        {
            if (!inLava)
            {
                _insideMs = 0;
                return 0;
            }
            _insideMs += dtMs;
            std::uint32_t const stacks = _insideMs / kFuryEveryMs;
            _insideMs %= kFuryEveryMs;
            return stacks;
        }

        void Reset() { _insideMs = 0; }
        std::uint32_t InsideMs() const { return _insideMs; }

    private:
        std::uint32_t _insideMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // BE5 Dread
    // ----------------------------------------------------------------------------------------------------------------

    // Whether the stack count a missed roar leaves (`stacksNow`, after the new stack) panics.
    constexpr bool Panics(std::uint32_t stacksNow, bool heroic)
    {
        return stacksNow >= kDreadPanicAt(heroic);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE6 Magma Split: the throw (Unit::KnockbackFrom: distance = 2 x speedXY x speedZ / gravity)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kGravity = 19.29110527038574f;           // Movement::gravity

    constexpr float KnockbackSpeedXY(float distance, float speedZ)
    {
        return speedZ > 0.f ? distance * kGravity / (2.f * speedZ) : 0.f;
    }

    constexpr float KnockbackDistance(float speedXY, float speedZ)
    {
        return 2.f * speedXY * speedZ / kGravity;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE7 Eruption
    // ----------------------------------------------------------------------------------------------------------------

    constexpr bool EruptionDue(bool heroic, std::uint64_t elapsedMs)
    {
        return elapsedMs >= kEruptionAtMs(heroic);
    }
}

#endif
