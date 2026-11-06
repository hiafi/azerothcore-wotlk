/*
 * mod-dungeon-bosses, Deadmines: Rhahk'Zor, the Watchman and the Evoker (WP-B1), the pure, host-testable part (no
 * engine headers): spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: DM
 * 'Rhahk'Zor' Build spec RZ1-RZ10; handoff section 3.4 rows RZ, section 3.5 row B1.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`. Cooldowns are the same on normal and
 * heroic (DM "Cooldowns and first casts"); the damage percents are the same too, the reference row (normal 1,300 /
 * heroic 4,120) makes the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_RHAHK_ZOR_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_RHAHK_ZOR_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iterator>
#include <optional>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace RhahkZor
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;
    using Ms = std::chrono::milliseconds;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsRhahkZor;

    // apps/dbc-tools source/npcs/deadmines/rhahk_zor.py declares every one of these.
    enum RhahkZorSpells : std::uint32_t
    {
        SPELL_RZ_CAVE_IN                = 205210,   // RZ1/RZ10 registry resolve copy (+ spell_dm_rhahkzor_cave_in)
        SPELL_RZ_CAVE_IN_TREMOR         = 205211,   // RZ2 every player, RefFlat (spell_dm_rhahkzor_ref_flat)
        SPELL_RZ_CAVE_IN_ROCKS          = 205212,   // RZ1 falling rocks look (dynamic object, SV 8455)
        SPELL_RZ_RUBBLE                 = 205213,   // RZ3 registry resolve copy (lingering tick)
        SPELL_RZ_WHIRLWIND_CAST         = 205214,   // RZ4 2 s cast bar
        SPELL_RZ_WHIRLWIND_SPIN         = 205215,   // RZ4 4 s spin aura on the boss (SV 10704)
        SPELL_RZ_WHIRLWIND              = 205216,   // RZ4 registry resolve copy (tick)
        SPELL_RZ_WHIRLWIND_KNOCKBACK    = 205217,   // RZ4 heroic rider
        SPELL_RZ_SPOTTED                = 205218,   // RZ10 heroic mark (SV 3239)
        SPELL_RZ_FIREBALL_VOLLEY        = 205219,   // RZ8 heroic Evoker cast, RefFlat (spell_dm_rhahkzor_ref_flat)
    };

    // Registry tags (bookkeeping in `.mech` listings and the failure ledger).
    enum RhahkZorTags : std::uint32_t
    {
        TAG_CAVE_IN         = 1,
        TAG_LOOKOUT         = 2,
        TAG_RUBBLE          = 3,
        TAG_WHIRLWIND       = 4,
        TAG_FLAMESTRIKE     = 5,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Damage (percent of the reference row for the difficulty; DM Build spec "Damage N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kCaveInPct{ 20.f, 20.f };        // RZ1, RZ10
    inline constexpr NH<float> kTremorPct{ 5.f, 5.f };          // RZ2
    inline constexpr NH<float> kRubblePct{ 5.f, 5.f };          // RZ3, per tick (heroic only)
    inline constexpr NH<float> kWhirlwindPct{ 15.f, 15.f };     // RZ4, per tick
    inline constexpr NH<float> kVolleyPct{ 40.f, 40.f };        // RZ8 (heroic only)

    // ----------------------------------------------------------------------------------------------------------------
    // Shapes
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kCaveInRadius = 5.f;
    inline constexpr float kWhirlwindRadius = 8.f;
    inline constexpr float kFlamestrikeRadius = 5.f;            // stock 11829, radius index 8
    // Heroic random circles: count, the build spec's distance from every player at cast, and (our choice, not the
    // spec's) a minimum distance between two random circles so the five spread over the room.
    inline constexpr NH<std::uint32_t> kRandomCircles{ 0, 5 };
    inline constexpr float kRandomMinFromPlayer = 6.f;
    inline constexpr float kRandomMinApart = 4.f;
    // The engine samples a random spot this far from the boss (the first collision along the ray) for each try.
    inline constexpr float kRandomRingMin = 4.f;
    inline constexpr float kRandomRingMax = 20.f;
    inline constexpr std::uint32_t kRandomTries = 60;
    // Every player within this range of the boss is "every player" (heroic circles, Lookout).
    inline constexpr float kRoomRange = 80.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (DM "Cooldowns and first casts"; same on both difficulties)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr Ms kCaveInFirst{ 8000 };
    inline constexpr Ms kCaveInEvery{ 15000 };
    inline constexpr Ms kCaveInWarn{ 2000 };
    inline constexpr Ms kLookoutWarn{ 1500 };                   // RZ10: lands 1.5 s after the first wave
    inline constexpr Ms kRubbleDuration{ 10000 };
    inline constexpr Ms kRubbleTick{ 1000 };
    inline constexpr Ms kRocksLook{ 2000 };                     // 205212's duration

    inline constexpr Ms kWhirlwindFirst{ 20000 };
    inline constexpr Ms kWhirlwindEvery{ 40000 };
    inline constexpr Ms kWhirlwindCast{ 2000 };
    inline constexpr Ms kWhirlwindSpin{ 4000 };
    inline constexpr Ms kWhirlwindTick{ 1000 };

    inline constexpr Ms kSlamFirst{ 10000 };
    inline constexpr Ms kSlamEvery{ 50000 };
    inline constexpr Ms kSlamStun{ 1500 };                      // stock 6304 is 3 s (handoff section 7 #3)

    inline constexpr Ms kFlamestrikeFirst{ 5000 };
    inline constexpr Ms kFlamestrikeEvery{ 12000 };
    inline constexpr Ms kFlamestrikeGround{ 8000 };             // stock 11829, duration index 31
    inline constexpr Ms kFireballFirst{ 2000 };
    inline constexpr Ms kVolleyFirst{ 8000 };
    inline constexpr Ms kVolleyEvery{ 14000 };
    // Quick Flame Ward 4979 keeps the stock SmartAI timing (1729: 1.1-21.1 s, then 42.6-63.5 s).
    inline constexpr Ms kWardFirstMin{ 1100 };
    inline constexpr Ms kWardFirstMax{ 21100 };
    inline constexpr Ms kWardEveryMin{ 42600 };
    inline constexpr Ms kWardEveryMax{ 63500 };
    // An Evoker cast that comes due while he is casting waits this long and tries again.
    inline constexpr Ms kBusyRetry{ 250 };

    // Watchman Shoot 6660: stock SmartAI 1725, at 5 to 30 yd every 2 s.
    inline constexpr Ms kShootEvery{ 2000 };
    inline constexpr float kShootMin = 5.f;
    inline constexpr float kShootMax = 30.f;

    inline constexpr bool ShootInRange(float distance)
    {
        return distance >= kShootMin && distance <= kShootMax;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Cave In waves
    // ----------------------------------------------------------------------------------------------------------------

    // Player circles of a first wave: one random non-tank on normal, every player on heroic.
    inline constexpr std::size_t PlayerCircleCount(bool heroic, std::size_t players)
    {
        return heroic ? players : (players ? 1 : 0);
    }

    // Rubble patches a first wave leaves: every heroic circle (players and random spots), none on normal; the second
    // wave (Lookout) never leaves any.
    inline constexpr std::size_t RubbleCount(bool heroic, std::size_t playerCircles, std::size_t randomCircles,
        bool lookoutWave)
    {
        return heroic && !lookoutWave ? playerCircles + randomCircles : 0;
    }

    // The Lookout wave comes only on heroic, from a living Watchman, after a first wave.
    inline constexpr bool LookoutFollows(bool heroic, bool watchmanAlive)
    {
        return heroic && watchmanAlive;
    }

    // True when `p` is at least `minDist` from every point in `points`.
    inline bool FarFromAll(Vec2 p, std::vector<Vec2> const& points, float minDist)
    {
        for (Vec2 const& q : points)
            if (DeadminesKit::Distance(p, q) < minDist)
                return false;
        return true;
    }

    // Up to `count` random spots for the heroic circles: each try asks `sample()` for a candidate (the engine: a
    // random bearing and distance from the boss, cut at the first collision; nullopt = no usable spot) and keeps it
    // when it is at least `minFromPlayer` from every player (DM RZ1: no player starts inside two circles) and
    // `minApart` from the spots already kept. Stops after `tries` samples; may return fewer than `count`.
    template <class Sampler>
    std::vector<Vec2> PickRandomSpots(std::size_t count, std::uint32_t tries, Sampler&& sample,
        std::vector<Vec2> const& players, float minFromPlayer, float minApart)
    {
        std::vector<Vec2> spots;
        for (std::uint32_t i = 0; i < tries && spots.size() < count; ++i)
        {
            std::optional<Vec2> const c = sample();
            if (!c || !FarFromAll(*c, players, minFromPlayer) || !FarFromAll(*c, spots, minApart))
                continue;
            spots.push_back(*c);
        }
        return spots;
    }

    // "Once per player per wave" (DM RZ1): every circle of a wave is its own registry mechanic, so a player standing
    // in two circles of one wave would be hit twice. The boss maps each circle's mechanic id to its wave; the Cave In
    // resolve copy's filter drops a player the wave already hit. Keeps the last kKeptWaves waves.
    class WaveLedger
    {
    public:
        static constexpr std::uint32_t kKeptWaves = 4;

        // Starts a new wave and returns its id (never 0).
        std::uint32_t BeginWave()
        {
            ++_lastWave;
            if (_lastWave > kKeptWaves)
            {
                std::uint32_t const old = _lastWave - kKeptWaves;
                _hits.erase(old);
                for (auto it = _waveOf.begin(); it != _waveOf.end();)
                    it = it->second <= old ? _waveOf.erase(it) : std::next(it);
            }
            return _lastWave;
        }

        void Assign(std::uint32_t mechanicId, std::uint32_t wave)
        {
            if (mechanicId && wave)
                _waveOf[mechanicId] = wave;
        }

        // 0 when the mechanic is not a known circle.
        std::uint32_t WaveOf(std::uint32_t mechanicId) const
        {
            auto const it = _waveOf.find(mechanicId);
            return it == _waveOf.end() ? 0 : it->second;
        }

        // The circle `mechanicId` may hit `who`: not yet hit by any circle of its wave (an unknown circle: always).
        bool MayHit(std::uint32_t mechanicId, std::uint64_t who) const
        {
            std::uint32_t const wave = WaveOf(mechanicId);
            if (!wave)
                return true;
            auto const it = _hits.find(wave);
            return it == _hits.end() || !it->second.count(who);
        }

        void NoteHit(std::uint32_t mechanicId, std::uint64_t who)
        {
            if (std::uint32_t const wave = WaveOf(mechanicId))
                _hits[wave].insert(who);
        }

        void Clear()
        {
            _waveOf.clear();
            _hits.clear();
            _lastWave = 0;
        }

    private:
        std::uint32_t _lastWave = 0;
        std::unordered_map<std::uint32_t, std::uint32_t> _waveOf;
        std::unordered_map<std::uint32_t, std::unordered_set<std::uint64_t>> _hits;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The Evoker's cast choice when several are due: Fireball Volley (heroic) > Flamestrike > Fireball (filler).
    // ----------------------------------------------------------------------------------------------------------------
    enum class EvokerCast : std::uint8_t
    {
        None,
        Volley,
        Flamestrike,
        Fireball,
    };

    inline constexpr EvokerCast NextEvokerCast(bool volleyDue, bool flamestrikeDue, bool fireballDue)
    {
        if (volleyDue)
            return EvokerCast::Volley;
        if (flamestrikeDue)
            return EvokerCast::Flamestrike;
        if (fireballDue)
            return EvokerCast::Fireball;
        return EvokerCast::None;
    }
}

#endif
