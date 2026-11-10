/*
 * mod-dungeon-bosses, Stratholme S13: Ramstein the Gorger (10439), the pure, host-testable part (no engine headers).
 * Build spec ST 3432-3483 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows RG and 3.5 row S13. Tested by
 * tests/strat_ramstein_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsRamstein (206685-206704), declared in apps/dbc-tools
 *                  source/npcs/stratholme/ramstein_the_gorger.py
 *   Tuning         NH<> constants and Cadence{first, every}: one number per difficulty, straight from the build spec
 *   MeatClock      RG1 the waves: 5 s, then every 15 s; 4 a wave, 33 in all on normal; 5 and no cap on heroic
 *   WavePoints     RG1 the spawn points across the gate passage
 *   GorgeReach     RG2 how close a walker must come to be eaten (3 yd; his reach once he is big)
 *   BiteQueue      RG2 the 1.5 s bites in flight (he fights on through them; several at once)
 *   BiteHealPct    RG2 the meal: a meat 3% / 4%, a heroic corpse half, a returning crawler none
 *   CrawlerBook    RG3 heroic: a crawler alive 15 s after the tear walks back to be eaten
 *   Spill*         RG3 the tear: 1 crawler + 1 per Gorged stack, on a ring around him
 *   TramplePct     RG4 the stomp: 10 yd + 1 per stack, 25% / 30% + 3% per stack
 *   MeatPriority   the bots' kill order: the meat nearest to him first
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_RAMSTEIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_RAMSTEIN_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace StratRamstein
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsRamstein;

    enum RamsteinSpells : std::uint32_t
    {
        SPELL_RG_GORGE_LOOK         = kSpellSlice.first + 0,    // 206685 RG2 the bite's look (self, triggered)
        SPELL_RG_GORGE_HEAL         = kSpellSlice.first + 1,    // 206686 RG2 the meal: heals him (base point 0)
        SPELL_RG_GORGED             = kSpellSlice.first + 2,    // 206687 RG2 +15% size, +10% damage per stack
        SPELL_RG_SEAMS_LOOK         = kSpellSlice.first + 3,    // 206688 RG3 the tear's look (self, triggered)
        SPELL_RG_EXPOSED            = kSpellSlice.first + 4,    // 206689 RG3 +50% damage taken, 8 s (heroic 6 s)
        SPELL_RG_GUT_PUDDLE         = kSpellSlice.first + 5,    // 206690 RG3 the puddle's tick (resolve copy, Nature)
        SPELL_RG_GUT_PUDDLE_LOOK    = kSpellSlice.first + 6,    // 206691 RG3 the puddle's look (aura on the stalker)
        SPELL_RG_TRAMPLE_HIT        = kSpellSlice.first + 7,    // 206692 RG4 the stomp's hit (resolve copy, Physical)
        SPELL_RG_TRAMPLE_LOOK       = kSpellSlice.first + 8,    // 206693 RG4 the stomp's look (self, triggered)
        SPELL_RG_TRAMPLE_TANK       = kSpellSlice.first + 9,    // 206694 RG4 the tank's share: the weapon hit
        SPELL_RG_KNOCKOUT           = kSpellSlice.first + 10,   // 206695 RG5 stock 17307 without the stun
        // 206696-206704 spare
    };
    static_assert(SPELL_RG_KNOCKOUT <= kSpellSlice.last, "Ramstein's spells must stay in his slice");

    // Stock: Flurry 15088 (+30% attack speed for 3 swings after a crit; kept, cast on himself at the pull; DD scales it
    // on heroic). StratholmeRework.h calls the same id SPELL_FLURRY.
    inline constexpr std::uint32_t SPELL_RG_FLURRY = 15088;

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum RamsteinTags : std::uint32_t
    {
        TAG_TRAMPLE     = 1,    // RG4
        TAG_GUT_PUDDLE  = 2,    // RG3
    };

    // DoAction on a Half-Digested Corpse: stop fighting and walk back to him (RG3 heroic).
    inline constexpr std::int32_t ACTION_RG_RETURN = 1;

    // MovePoint ids.
    inline constexpr std::uint32_t POINT_RG_WALK_IN = 1;    // the boss: summon point to his stop
    inline constexpr std::uint32_t POINT_RG_WALKER = 2;     // a meat or a returning crawler on its way to him

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 3315-3362, 3443-3455; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // First start and cadence of a beat, in ms since the pull (ST "First, cooldown"). Cadences count start to start.
    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    struct MsRange
    {
        std::uint32_t min;
        std::uint32_t max;
    };

    // `r` in [0, 1): a point of the range.
    constexpr std::uint32_t InRange(MsRange range, float r)
    {
        float const span = static_cast<float>(range.max - range.min);
        return range.min + static_cast<std::uint32_t>(std::clamp(r, 0.f, 1.f) * span);
    }

    // RG1 The Meat: the gate opens and a wave shambles out at 5 s, then every 15 s (about 26 s to walk to him).
    inline constexpr Cadence kMeatCadence{ 5000, 15000 };
    inline constexpr NH<std::uint32_t> kMeatPerWave{ 4, 5 };
    inline constexpr NH<std::uint32_t> kMeatCap{ 33, 0 };           // 33 in all on normal (the stock count); 0: no cap
    inline constexpr float kMeatSpeedYdPerSec = 3.5f;               // walk speed (1.4 on the 2.5 base)
    inline constexpr std::uint32_t kMeatRepathMs = 1000;            // re-path to him once a second (he moves)
    inline constexpr float kMeatSpacingYd = 1.5f;                   // across the gate passage (9-10 yd wide)
    inline constexpr float kWalkerZBandYd = 8.f;                    // a walker on another floor is not at him

    // RG2 Gorge: a meat within 3 yd of him is eaten in a 1.5 s bite. Once he is big (scale 4.4 at 8 stacks) 3 yd from
    // his center is inside his body, so the reach is never less than his combat reach + 1.5 yd.
    inline constexpr float kGorgeReachYd = 3.f;
    inline constexpr float kGorgeReachPastYd = 1.5f;
    inline constexpr std::uint32_t kBiteMs = 1500;
    inline constexpr std::uint32_t kEmoteGapMs = 1500;              // bites arriving together share one emote line
    inline constexpr NH<float> kGorgeHealPct{ 3.f, 4.f };           // of his maximum health
    inline constexpr float kCorpseHealFactor = 0.5f;                // heroic Cannibalize: half the heal, a full stack
    inline constexpr float kCorpseEatRadiusYd = 10.f;               // a heroic meat killed within this of him
    inline constexpr NH<std::uint32_t> kGorgedMaxStacks{ 8, 10 };

    // RG3 Bursting at the Seams: every 30 s, first at 30 s.
    inline constexpr Cadence kTearCadence{ 30000, 30000 };
    inline constexpr NH<std::uint32_t> kExposedMs{ 8000, 6000 };
    inline constexpr float kSpillRadiusMinYd = 4.f;                 // the ring around him: his combat reach + 2 yd
    inline constexpr float kSpillPastReachYd = 2.f;
    inline constexpr float kSpillNearPlayerYd = 40.f;               // a crawler's first target: any player this near
    inline constexpr std::uint32_t kCrawlerReturnAfterMs = 15000;   // heroic: a crawler still alive walks back

    // The gut puddle: a 6 yd registry zone under him, 4% of the reference row a second for 20 s after a 1 s grace.
    inline constexpr float kPuddleRadius = 6.f;
    inline constexpr std::uint32_t kPuddleMs = 20000;
    inline constexpr std::uint32_t kPuddleTickMs = 1000;
    inline constexpr float kPuddlePct = 4.f;                        // Weakened once per player per puddle

    // RG4 Trample: first 8 s, every 12 s; a 1.5 s rear-up, then a circle on him.
    inline constexpr Cadence kTrampleCadence{ 8000, 12000 };
    inline constexpr std::uint32_t kTrampleWarnMs = 1500;
    inline constexpr float kTrampleBaseRadiusYd = 10.f;
    inline constexpr float kTramplePerStackRadiusYd = 1.f;
    inline constexpr NH<float> kTramplePct{ 25.f, 30.f };
    inline constexpr float kTramplePerStackPct = 3.f;

    // RG5 Knockout (the stock timers of SmartAI 10439): first 4-9 s, then every 10-15 s, on his victim in melee range.
    inline constexpr MsRange kKnockoutFirst{ 4000, 9000 };
    inline constexpr MsRange kKnockoutEvery{ 10000, 15000 };

    // The walk-in (the stock action list 1043900): the door 175405 opens as he leaves his pen, he yells a second in and
    // walks to his stop, the door closes behind him, then he goes after the nearest player within 70 yd. A walk that
    // has not ended after 15 s ends where he stands. A GM-spawned Ramstein more than 5 yd from the summon point skips
    // the walk (he is where he is).
    inline constexpr std::uint32_t kWalkInYellMs = 1000;
    inline constexpr std::uint32_t kWalkInTimeoutMs = 15000;
    inline constexpr float kWalkInSkipRadiusYd = 5.f;
    inline constexpr float kWalkInAggroRangeYd = 70.f;
    inline constexpr float kWalkInDoorRangeYd = 30.f;

    // The Slaughter Square gate (the meat's passage) is found from his stop: it stands 72 yd away.
    inline constexpr float kSideGateSearchYd = 150.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Bots (ST "Bots"): the meat nearest to him first, then the crawlers, then him
    // ----------------------------------------------------------------------------------------------------------------

    struct MeatTier
    {
        float withinYd;             // the meat is within this of him
        std::int8_t priority;
    };
    inline constexpr std::array<MeatTier, 3> kMeatTiers{ { { 15.f, 4 }, { 30.f, 3 }, { 60.f, 2 } } };
    inline constexpr std::int8_t kCrawlerPriority = 1;          // below every meat tier, above him (the boss is 0)

    // The descriptor priority of a meat `distance` yd from him: the highest tier it falls in; 0 beyond the last (not
    // listed, the bots leave it until it walks in).
    constexpr std::int8_t MeatPriority(float distance)
    {
        std::int8_t best = 0;
        for (MeatTier const& tier : kMeatTiers)
            if (distance <= tier.withinYd && tier.priority > best)
                best = tier.priority;
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG1 The Meat
    // ----------------------------------------------------------------------------------------------------------------

    // How many to summon in a wave when `summoned` have come out already: the wave size, cut to the cap (0: no cap).
    constexpr std::uint32_t MeatWaveSize(bool heroic, std::uint32_t summoned)
    {
        std::uint32_t const want = kMeatPerWave(heroic);
        std::uint32_t const cap = kMeatCap(heroic);
        if (!cap)
            return want;
        return summoned >= cap ? 0 : std::min(want, cap - summoned);
    }

    // The waves' clock, on the AI's own clock (ms since the pull). Take() returns the size of the wave due now (0: none
    // due, or the cap is spent) and moves the next wave a cadence on; it counts what it hands out.
    class MeatClock
    {
    public:
        void Reset() { *this = MeatClock(); }

        std::uint32_t Take(std::uint64_t nowMs, bool heroic)
        {
            if (nowMs < _nextMs)
                return 0;
            _nextMs += kMeatCadence.every;
            std::uint32_t const n = MeatWaveSize(heroic, _summoned);
            _summoned += n;
            return n;
        }

        std::uint32_t Summoned() const { return _summoned; }
        std::uint64_t NextMs() const { return _nextMs; }

    private:
        std::uint64_t _nextMs = kMeatCadence.first;
        std::uint32_t _summoned = 0;
    };

    // The spawn points of a wave of `count`: across the passage (the +y axis, west), `kMeatSpacingYd` apart,
    // centered on the spawn point (a wave of 5 spans +-3 yd of a 9-10 yd passage).
    inline std::vector<Vec2> WavePoints(Vec2 spawn, std::uint32_t count)
    {
        std::vector<Vec2> points;
        for (std::uint32_t i = 0; i < count; ++i)
        {
            float const offset = (static_cast<float>(i) - static_cast<float>(count - 1) / 2.f) * kMeatSpacingYd;
            points.push_back({ spawn.x, spawn.y + offset });
        }
        return points;
    }

    // The pace of a walker under `slowPct` (the strongest slow aura on it, a negative percent; 0: none). The script
    // gives MovePoint an explicit speed, which the engine's own slow handling would not touch, so slows (a Frost
    // Nova's chill, Hamstring, Frostbolt) scale it here; the heroic copy of the meat's template is the stock row, so
    // the pace never rides on the template's speeds.
    constexpr float SlowedSpeed(float baseYdPerSec, std::int32_t slowPct)
    {
        return baseYdPerSec * std::max(0.f, 1.f + static_cast<float>(std::min(slowPct, 0)) / 100.f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RG2 Gorge
    // ----------------------------------------------------------------------------------------------------------------

    // How close a meat or a returning crawler must be (2D, from his center) to be eaten.
    constexpr float GorgeReach(float combatReach)
    {
        return std::max(kGorgeReachYd, combatReach + kGorgeReachPastYd);
    }

    constexpr bool InGorgeReach(float distance2d, float dz, float combatReach)
    {
        return distance2d <= GorgeReach(combatReach) && dz <= kWalkerZBandYd && dz >= -kWalkerZBandYd;
    }

    // A heroic meat killed within 10 yd of him leaves a corpse he eats.
    constexpr bool CorpseEdible(bool heroic, float distance2d)
    {
        return heroic && distance2d <= kCorpseEatRadiusYd;
    }

    enum class BiteKind : std::uint8_t
    {
        Meat,       // a walker that reached him
        Corpse,     // heroic: a meat killed within 10 yd of him
        Crawler,    // heroic: a Half-Digested Corpse that walked back
    };

    // The heal of one bite, in percent of his maximum health.
    constexpr float BiteHealPct(bool heroic, BiteKind kind)
    {
        switch (kind)
        {
            case BiteKind::Meat:    return kGorgeHealPct(heroic);
            case BiteKind::Corpse:  return kGorgeHealPct(heroic) * kCorpseHealFactor;
            case BiteKind::Crawler: return 0.f;
        }
        return 0.f;
    }

    // `pct` percent of `maxHealth`, rounded.
    inline std::uint32_t PctOfMax(std::uint32_t maxHealth, float pct)
    {
        return static_cast<std::uint32_t>(std::max<long>(0, std::lround(static_cast<double>(maxHealth) * pct / 100.0)));
    }

    // The stacks after one meal (every kind gives one; the cap is the difficulty's).
    constexpr std::uint32_t StacksAfterBite(std::uint32_t stacks, bool heroic)
    {
        return std::min(stacks + 1, kGorgedMaxStacks(heroic));
    }

    // The bites in flight. Add() books a bite that lands kBiteMs from `nowMs` (false: that unit is being eaten
    // already); Take() hands over the bites that have landed, oldest first.
    struct Bite
    {
        std::uint64_t id = 0;
        BiteKind kind = BiteKind::Meat;
        std::uint64_t dueMs = 0;
    };

    class BiteQueue
    {
    public:
        bool Add(std::uint64_t id, BiteKind kind, std::uint64_t nowMs)
        {
            if (Has(id))
                return false;
            _bites.push_back({ id, kind, nowMs + kBiteMs });
            return true;
        }

        std::vector<Bite> Take(std::uint64_t nowMs)
        {
            std::vector<Bite> due;
            for (auto it = _bites.begin(); it != _bites.end();)
            {
                if (it->dueMs <= nowMs)
                {
                    due.push_back(*it);
                    it = _bites.erase(it);
                }
                else
                    ++it;
            }
            std::stable_sort(due.begin(), due.end(), [](Bite const& a, Bite const& b) { return a.dueMs < b.dueMs; });
            return due;
        }

        bool Has(std::uint64_t id) const
        {
            return std::any_of(_bites.begin(), _bites.end(), [id](Bite const& b) { return b.id == id; });
        }

        // Drops a bite (the unit is gone and nothing is left to eat).
        void Forget(std::uint64_t id)
        {
            _bites.erase(std::remove_if(_bites.begin(), _bites.end(), [id](Bite const& b) { return b.id == id; }),
                _bites.end());
        }

        std::size_t Size() const { return _bites.size(); }
        void Clear() { _bites.clear(); }

    private:
        std::vector<Bite> _bites;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RG3 Bursting at the Seams
    // ----------------------------------------------------------------------------------------------------------------

    // The crawlers a tear spills: 1, plus 1 per Gorged stack (a lean group gets one).
    constexpr std::uint32_t SpillCount(std::uint32_t stacks)
    {
        return 1 + stacks;
    }

    // The ring they crawl out on: outside his body.
    constexpr float SpillRadius(float combatReach)
    {
        return std::max(kSpillRadiusMinYd, combatReach + kSpillPastReachYd);
    }

    // `count` bearings, evenly around the circle from `start`.
    inline std::vector<float> SpillAngles(std::uint32_t count, float start)
    {
        std::vector<float> angles;
        for (std::uint32_t i = 0; i < count; ++i)
            angles.push_back(std::fmod(start + static_cast<float>(i) * DungeonKit::kTwoPi / static_cast<float>(count),
                DungeonKit::kTwoPi));
        return angles;
    }

    // Heroic: the crawlers still alive 15 s after the tear walk back to him. Add() on a spill, TakeDue() each tick
    // (an id comes out once), Forget() when one dies or is eaten.
    class CrawlerBook
    {
    public:
        void Add(std::uint64_t id, std::uint64_t bornMs) { _crawlers.push_back({ id, bornMs, false }); }

        void Forget(std::uint64_t id)
        {
            _crawlers.erase(std::remove_if(_crawlers.begin(), _crawlers.end(),
                [id](Entry const& e) { return e.id == id; }), _crawlers.end());
        }

        std::vector<std::uint64_t> TakeDue(std::uint64_t nowMs)
        {
            std::vector<std::uint64_t> due;
            for (Entry& e : _crawlers)
                if (!e.returning && nowMs >= e.bornMs + kCrawlerReturnAfterMs)
                {
                    e.returning = true;
                    due.push_back(e.id);
                }
            return due;
        }

        bool Tracks(std::uint64_t id) const
        {
            return std::any_of(_crawlers.begin(), _crawlers.end(), [id](Entry const& e) { return e.id == id; });
        }

        std::size_t Size() const { return _crawlers.size(); }
        void Clear() { _crawlers.clear(); }

    private:
        struct Entry
        {
            std::uint64_t id;
            std::uint64_t bornMs;
            bool returning;
        };

        std::vector<Entry> _crawlers;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RG4 Trample
    // ----------------------------------------------------------------------------------------------------------------

    // The circle's radius, read as the rear-up begins: 10 yd + 1 yd per Gorged stack (18 yd at 8 stacks).
    constexpr float TrampleRadius(std::uint32_t stacks)
    {
        return kTrampleBaseRadiusYd + kTramplePerStackRadiusYd * static_cast<float>(stacks);
    }

    // Percent of the non-tank row: 25% (heroic 30%) + 3% per stack.
    constexpr float TramplePct(bool heroic, std::uint32_t stacks)
    {
        return kTramplePct(heroic) + kTramplePerStackPct * static_cast<float>(stacks);
    }
}

#endif
