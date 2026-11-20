/*
 * mod-dungeon-bosses, Blackrock Depths D20:
 * Ambassador Flamelash (9156), his Portal Anchors (300842) and the Burning Spirits (9178), the pure, host-testable
 * part (no engine headers). Build spec: docs/dungeons/blackrock-depths-4-imperial-seat.md "Ambassador Flamelash"
 * (S4 740-783, FL1-FL5; rulings 70-71, 88), handoff sections 3.4, 3.5 row D20, 3.6, 3.8 (NM: the chamber and the
 * seven rune spots), 3.10. Tested by tests/brd_flamelash_test.cpp.
 *
 *   Spells      the WP's ids, inside kSpellsFlamelash (211490-211519), declared in apps/dbc-tools
 *               source/npcs/blackrock_depths/flamelash.py
 *   Tuning      NH<> percents and cadences, straight from the build spec (percents of the reference row); the unset
 *               "stock rescaled" Fire Blast is this WP's default (report, designer questions)
 *   Runes       the seven rune objects [DB]: four at 34 yd and three at 24 yd from the chamber's center, the anchor
 *               spots; which rune opens next (never the same twice in a row, never one that is up)
 *   Spirits     the spill cadence and cap, the march speed per rune (the arrival time evened out), the arrival rule
 *   Stack       FL3 his Burning Spirit stack: +10% damage and +5% size each, 10 at most
 *   Kindling    FL4 the 8 s channel's ticks, who burns, the heroic trail steps (FL5)
 *   Beats       the fight's clock: first delay and cadence per mechanic and difficulty
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_FLAMELASH_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_FLAMELASH_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdFlamelash
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsFlamelash;

    enum FlamelashSpells : std::uint32_t
    {
        SPELL_FL_PORTAL             = kSpellSlice.first + 0,    // 211490 FL2 the anchor's portal look (a lasting state)
        SPELL_FL_BURNING_SPIRIT     = kSpellSlice.first + 1,    // 211491 FL3 his stack: +10% damage, +5% size, 30 s
        SPELL_FL_ARRIVAL_LOOK       = kSpellSlice.first + 2,    // 211492 FL3 look: the flash of an arrival
        SPELL_FL_FIRE_BLAST         = kSpellSlice.first + 3,    // 211493 FL1 the copy of 13342 (Fire, 20 yd)
        SPELL_FL_KINDLING           = kSpellSlice.first + 4,    // 211494 FL4 the 8 s channel (not interruptible)
        SPELL_FL_KINDLED            = kSpellSlice.first + 5,    // 211495 FL4 the mark on the channel's target (8 s)
        SPELL_FL_KINDLING_BURN      = kSpellSlice.first + 6,    // 211496 FL4 a tick on each other player in range
        SPELL_FL_KINDLING_SELF      = kSpellSlice.first + 7,    // 211497 FL4 a tick on the target
        SPELL_FL_TRAIL_LOOK         = kSpellSlice.first + 8,    // 211498 FL5 the patch's look on a stalker (heroic)
        SPELL_FL_TRAIL              = kSpellSlice.first + 9,    // 211499 FL5 the patch's hit (resolve copy, Fire)
        // 211500-211519 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_FL_TRAIL;
    static_assert(kLastSpell <= kSpellSlice.last, "Flamelash's spells must stay in his slice");

    // Stock spells of 9156 and 9178 the rework no longer casts: Fire Blast 13342 is kept and rescaled, so it is a copy
    // in the slice (rule 15: never an edit of the shared override); Burning Spirit 14744 becomes
    // SPELL_FL_BURNING_SPIRIT.
    inline constexpr std::uint32_t SPELL_STOCK_FIRE_BLAST = 13342;
    inline constexpr std::uint32_t SPELL_STOCK_BURNING_SPIRIT = 14744;

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them).
    enum FlamelashTags : std::uint32_t
    {
        TAG_FL_KINDLING     = 4,    // FL4 the bots' run-out from the channel's target (telegraph; the script ticks)
        TAG_FL_TRAIL        = 5,    // FL5 a Burning Trail patch (heroic)
        TAG_FL_TANK_SPOT    = 6,    // the tank's Spot in the chamber's center (bots only, no marker)
    };

    // creature_text groups of 9156 (data/sql/updates/pending_db_world/rev_flamelash_blackrock_depths.sql, S4 "Text").
    enum FlamelashTexts : std::uint8_t
    {
        SAY_PULL        = 0,    // stock yell: "Your reign of terror ends now! Face your doom mortals!"
        SAY_PORTAL      = 1,    // yell: "The Firelands answer their master's call!" (FL2)
        EMOTE_KINDLING  = 2,    // boss emote: "%s kindles $n!" (FL4)
        SAY_DEATH       = 3,    // yell: "Ragnaros... will hear of this..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The chamber and the seven runes [DB: gameobject guids 15547, 15550, 15552, 15577, 15629, 15642, 17124]
    // ----------------------------------------------------------------------------------------------------------------

    // The chamber's center: the middle of the four cardinal runes (the NM disc r 32.3 at (1012.2, -240.8)). Flamelash
    // spawns 3 yd off it, at kFlamelashSpawn; the tank holds him here.
    inline constexpr Vec2 kChamberCenter{ 1012.29f, -241.00f };
    inline constexpr float kChamberZ = -61.9f;

    struct Rune
    {
        std::uint32_t goEntry;      // the cosmetic Doodad_DarkIronDwarfRune object (170578-170584)
        float x;
        float y;
        float z;
        bool cardinal;              // 34 yd from the center; the diagonals are 24 yd
    };

    // Ordered by bearing from the center. The fourth diagonal (995.3, -224.1) has no rune: three diagonals, four
    // cardinals (handoff 3.8, correction 40).
    inline constexpr std::size_t kRuneCount = 7;
    inline constexpr std::array<Rune, kRuneCount> kRunes{ {
        { 170579, 1046.23f, -241.007f, -61.946f, true },    // 0 x +34
        { 170581, 1029.29f, -224.058f, -61.946f, false },   // 1 diagonal
        { 170583, 1012.31f, -207.095f, -61.946f, true },    // 2 y +34
        { 170584,  978.344f, -240.967f, -61.946f, true },   // 3 x -34
        { 170582,  995.262f, -257.966f, -61.946f, false },  // 4 diagonal
        { 170580, 1012.28f, -274.911f, -61.946f, true },    // 5 y -34
        { 170578, 1029.22f, -257.987f, -61.946f, false },   // 6 diagonal
    } };

    // Yards from the chamber's center to rune `i`.
    inline float RuneRange(std::size_t i)
    {
        return DungeonKit::Distance(kChamberCenter, { kRunes[i].x, kRunes[i].y });
    }

    inline constexpr std::uint32_t kAllRunes = (1u << kRuneCount) - 1;

    // The rune that opens next: never the one that opened last, never one with an anchor up (`busyMask`). `rand(n)`
    // returns [0, n). nullopt when nothing is free.
    template <class Rand>
    std::optional<std::size_t> PickRune(int last, std::uint32_t busyMask, Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < kRuneCount; ++i)
            if (static_cast<int>(i) != last && !(busyMask & (1u << i)))
                pool.push_back(i);
        if (pool.empty())
            return std::nullopt;
        std::size_t const n = pool.size();
        return pool[std::min<std::size_t>(rand(static_cast<std::uint32_t>(n)), n - 1)];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "Build spec": N level 55, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // FL1 Fire Blast: on the tank at 2 s, then every 7 s (stock). The spec says "stock rescaled" (gap 36): this WP's
    // default is 15% (heroic 20%) of the tank row, before his stack.
    inline constexpr std::uint32_t kFireBlastFirstMs = 2000;
    inline constexpr std::uint32_t kFireBlastEveryMs = 7000;
    inline constexpr std::uint32_t kFireBlastRetryMs = 1000;    // the victim is out of reach: try again shortly
    inline constexpr float kFireBlastRangeYd = 20.f;
    inline constexpr NH<float> kFireBlastPct{ 15.f, 20.f };

    // FL2 Firelands Portals: the first at 10 s, then every 30 s (heroic 20 s); each anchor spills a Burning Spirit
    // every 3 s (heroic 2 s) until it is destroyed.
    inline constexpr NH<std::uint32_t> kPortalFirstMs{ 10000, 10000 };
    inline constexpr NH<std::uint32_t> kPortalEveryMs{ 30000, 20000 };
    inline constexpr NH<std::uint32_t> kSpillEveryMs{ 3000, 2000 };
    // The spec sets no cap (the stack is the ceiling); the script bounds the worst case when a group ignores the
    // portals: at most this many Burning Spirits alive at once.
    inline constexpr NH<std::uint32_t> kSpiritCap{ 12, 16 };
    inline constexpr std::uint32_t kPortalRetryMs = 1000;       // every rune has an anchor up: try again shortly

    // The march: "about 6 yd per s (about 6 s from the ring)". The stock run speed is 0.857 x 7 = 6 yd/s; the 24 yd
    // runes would be 1.7 s sooner, so the speed is set per anchor to make every march take kSpiritTravelS.
    inline constexpr float kSpiritTravelS = 6.f;
    inline constexpr float kSpiritMinSpeed = 3.f;               // yd/s
    inline constexpr float kSpiritMaxSpeed = 6.f;
    inline constexpr std::uint32_t kSpiritReaimMs = 500;        // the march re-aims at him (a slow or a root shows)
    inline constexpr float kArriveYd = 1.5f;                    // a spirit this close to his reach has arrived
    // Bots: a ranged DPS skips a spirit within this of him (about 2 s from arriving at up to 6 yd/s; the 2026-11-19
    // brd-s4 smoke spent every post-anchor window on the oldest spirit, which arrived anyway). Melee still catch it.
    inline constexpr float kSpiritLateYd = 12.f;

    inline float SpiritSpeed(float distance)
    {
        return std::clamp(distance / kSpiritTravelS, kSpiritMinSpeed, kSpiritMaxSpeed);
    }

    constexpr bool CanSpill(std::uint32_t aliveSpirits, bool heroic)
    {
        return aliveSpirits < kSpiritCap(heroic);
    }

    constexpr bool Arrived(float dist2d, float bossReach)
    {
        return dist2d <= bossReach + kArriveYd;
    }

    // FL3 Burning Spirit: +10% damage and +5% size per stack, 30 s refreshed by every arrival, 10 at most.
    inline constexpr std::uint32_t kStackCap = 10;
    inline constexpr std::uint32_t kStackLifeMs = 30000;
    inline constexpr float kStackDamagePctPerStack = 10.f;
    inline constexpr float kStackSizePctPerStack = 5.f;

    constexpr std::uint32_t StacksAfterArrival(std::uint32_t stacks)
    {
        return stacks + 1 > kStackCap ? kStackCap : stacks + 1;
    }

    // His damage multiplier at `stacks`. The aura (+10% damage done) raises his melee; his own spells ignore caster
    // modifiers (rule 2), so the scripts multiply their percents by this (the spec: "the stack raises his damage").
    constexpr float DamageScale(std::uint32_t stacks)
    {
        return 1.f + kStackDamagePctPerStack / 100.f * static_cast<float>(std::min(stacks, kStackCap));
    }

    constexpr float SizeScale(std::uint32_t stacks)
    {
        return 1.f + kStackSizePctPerStack / 100.f * static_cast<float>(std::min(stacks, kStackCap));
    }

    // FL4 Kindling: at 15 s, then every 25 s (heroic 20 s): an 8 s channel on a random player other than the tank. A
    // tick every second: everyone else of the fight within 8 yd (heroic 10 yd) of the target burns 8% (12%) of their
    // row, the target 3% (5%). No Weakened (damage over time).
    inline constexpr std::uint32_t kKindlingFirstMs = 15000;
    inline constexpr NH<std::uint32_t> kKindlingEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kKindlingMs = 8000;
    inline constexpr std::uint32_t kKindlingTickMs = 1000;
    inline constexpr std::uint32_t kKindlingTicks = kKindlingMs / kKindlingTickMs;
    inline constexpr std::uint32_t kKindlingStartGraceMs = 1500;    // the channel has not taken yet
    inline constexpr std::uint32_t kKindlingRetryMs = 1000;         // a cast in progress, nobody to pick: try again
    inline constexpr NH<float> kKindlingRadius{ 8.f, 10.f };
    inline constexpr float kKindlingZBand = 8.f;                    // a player this far above or below is not near
    inline constexpr NH<float> kKindlingOthersPct{ 8.f, 12.f };
    inline constexpr NH<float> kKindlingSelfPct{ 3.f, 5.f };

    // FL5 Burning Trail (heroic): a 4 yd patch under the Kindled player every 2 s, up to 4 a channel, 15 s each, 8%
    // of the row a second. Placed under the registry's ring (a short warning) so the carrier, already running away,
    // is not hit as it forms.
    inline constexpr std::uint32_t kTrailEveryMs = 2000;
    inline constexpr std::uint32_t kTrailMax = 4;
    inline constexpr float kTrailRadius = 4.f;
    inline constexpr std::uint32_t kTrailLifeMs = 15000;            // the warning included
    inline constexpr std::uint32_t kTrailWarnMs = 1000;
    inline constexpr std::uint32_t kTrailTickMs = 1000;
    inline constexpr float kTrailPctPerTick = 8.f;

    // Kindling tick `tick` (1-based) lays a trail patch: heroic only, every second tick, `placed` of the channel's
    // patches so far.
    constexpr bool TrailOnTick(std::uint32_t tick, bool heroic, std::uint32_t placed)
    {
        return heroic && tick > 0 && tick <= kKindlingTicks && tick % (kTrailEveryMs / kKindlingTickMs) == 0
            && placed < kTrailMax;
    }

    constexpr std::uint32_t TrailsPerChannel(bool heroic)
    {
        std::uint32_t n = 0;
        for (std::uint32_t tick = 1; tick <= kKindlingTicks; ++tick)
            if (TrailOnTick(tick, heroic, n))
                ++n;
        return n;
    }
    static_assert(TrailsPerChannel(false) == 0, "normal: no trail");
    static_assert(TrailsPerChannel(true) == 4, "heroic: four patches a channel");

    // Another player `dist2d` yd from the target on the plane, `dz` yd above or below it, burns.
    constexpr bool InKindling(float dist2d, float dz, bool heroic)
    {
        return dist2d <= kKindlingRadius(heroic) && (dz < 0.f ? -dz : dz) <= kKindlingZBand;
    }

    // The tank's Spot in the chamber's center (the spirits arrive from every rune at equal range): bots only, 5 yd,
    // re-posted every 20 s.
    inline constexpr std::uint32_t kTankSpotMs = 20000;
    inline constexpr float kTankSpotRadius = 5.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Percent spells: the base percent of each of his own damage spells (before his stack)
    // ----------------------------------------------------------------------------------------------------------------

    // The per-hit percent of the reference row of `spellId`; 0 for a spell that deals none.
    constexpr float BasePct(std::uint32_t spellId, bool heroic)
    {
        switch (spellId)
        {
            case SPELL_FL_FIRE_BLAST:       return kFireBlastPct(heroic);
            case SPELL_FL_KINDLING_BURN:    return kKindlingOthersPct(heroic);
            case SPELL_FL_KINDLING_SELF:    return kKindlingSelfPct(heroic);
            case SPELL_FL_TRAIL:            return kTrailPctPerTick;
            default:                        return 0.f;
        }
    }

    // The percent with his stack on top.
    constexpr float ScaledPct(std::uint32_t spellId, bool heroic, std::uint32_t stacks)
    {
        return BasePct(spellId, heroic) * DamageScale(stacks);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The arena: the chamber out to the runes. The shared FlamelashArena() (r 33 at (1012.2, -240.8)) leaves the four
    // cardinal runes (34 yd) outside; players working an anchor there must still count as on the arena.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kArenaRadius = 38.f;

    inline BlackrockDepthsRework::Arena FightArena()
    {
        return BlackrockDepthsRework::Arena(BlackrockDepthsRework::CircleRegion(kChamberCenter, kArenaRadius, -64.f,
            -57.f));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats (S4 "Build spec" first / cooldown, normal / heroic)
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
}

#endif
