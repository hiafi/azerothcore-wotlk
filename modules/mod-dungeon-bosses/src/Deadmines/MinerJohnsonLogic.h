/*
 * mod-dungeon-bosses, Deadmines: Miner Johnson and the Working Miners (WP-B2), the pure, host-testable part (no engine
 * headers): spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: DM 'Miner Johnson'
 * Build spec MJ1-MJ5.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_MINER_JOHNSON_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_MINER_JOHNSON_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <vector>

namespace MinerJohnson
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsMinerJohnson;

    // Declared in apps/dbc-tools source/npcs/deadmines/miner_johnson.py.
    enum MinerJohnsonSpells : std::uint32_t
    {
        SPELL_PAY_POUCH         = kSlice.first + 0,     // 205230 MJ1 the pouch missile (cosmetic, to a point)
        SPELL_PAYDAY_GLINT      = kSlice.first + 1,     // 205231 MJ1 the gold glint on the miner whose pay it is
        SPELL_POCKETED          = kSlice.first + 2,     // 205232 MJ2 the catcher's buff (+15% damage done, 15 s)
        SPELL_GOLD_FEVER        = kSlice.first + 3,     // 205233 MJ5 heroic: attack speed +30%
        SPELL_GOLD_FEVER_TINT   = kSlice.first + 4,     // 205234 MJ5 the hidden gold tint aura
        // 205235-205239 spare
    };
    static_assert(kSlice.Contains(SPELL_GOLD_FEVER_TINT), "Miner Johnson's spells stay in his slice");

    // Registry tags (the build spec's MJ numbers).
    enum MinerJohnsonTags : std::uint32_t
    {
        TAG_PAYDAY = 1,     // MJ1
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (DM Build spec, Tuning starting points)
    // ----------------------------------------------------------------------------------------------------------------

    // MJ1 Payday: first at 8 s, then every 20 s; 1 pouch (2.5 s flight) normal, 2 pouches (2 s) heroic; Soak 2 yd,
    // 3 yd in front of the miner, 1 body.
    inline constexpr std::uint32_t kPaydayFirstMs = 8000;
    inline constexpr std::uint32_t kPaydayEveryMs = 20000;
    inline constexpr NH<std::uint32_t> kPouchFlightMs{ 2500, 2000 };
    inline constexpr NH<std::uint32_t> kPouchCount{ 1, 2 };
    inline constexpr float kSoakRadius = 2.f;
    inline constexpr std::uint8_t kSoakBodies = 1;
    inline constexpr float kSpotOffset = 3.f;
    // The pouch missile's Speed (yd/s); must equal Speed of spell 205230 in miner_johnson.py.
    inline constexpr float kPouchSpeed = 8.f;

    // MJ2 Pocketed: 15 s, +15% (both in the spell; listed here for the report and tests).
    inline constexpr std::uint32_t kPocketedMs = 15000;

    // MJ4 Pierce Armor (stock 12097 on the tank): 1 to 7 s, then every 20 to 25 s; the aura cut to 10 s (stock 20 s).
    inline constexpr std::uint32_t kPierceFirstMinMs = 1000;
    inline constexpr std::uint32_t kPierceFirstMaxMs = 7000;
    inline constexpr std::uint32_t kPierceEveryMinMs = 20000;
    inline constexpr std::uint32_t kPierceEveryMaxMs = 25000;
    inline constexpr std::uint32_t kPierceDurationMs = 10000;

    // MJ3 a paid miner's stock Pierce Armor 6016 (stock SmartAI 598: 2 to 10 s, then every 15 to 20 s; the spell's own
    // 45 s category cooldown still applies, as it did under SmartAI).
    inline constexpr std::uint32_t kMinerPierceFirstMinMs = 2000;
    inline constexpr std::uint32_t kMinerPierceFirstMaxMs = 10000;
    inline constexpr std::uint32_t kMinerPierceEveryMinMs = 15000;
    inline constexpr std::uint32_t kMinerPierceEveryMaxMs = 20000;

    // MJ5 Gold Fever: heroic only, below 30% health (0 = never).
    inline constexpr NH<std::uint32_t> kGoldFeverBelowPct{ 0, 30 };

    // The crew is summoned this long after Johnson's reset: the instance's 40% roll despawns an absent Johnson 500 ms
    // after his create, and his AI resets before that roll (AIM_Initialize runs before OnCreatureCreate).
    inline constexpr std::uint32_t kCrewSetupDelayMs = 1000;
    // A paid miner's corpse stays this long (loot), then the summon despawns.
    inline constexpr std::uint32_t kMinerCorpseMs = 300000;

    // ----------------------------------------------------------------------------------------------------------------
    // The room (live world DB, read-only 2026-11-06)
    // ----------------------------------------------------------------------------------------------------------------

    struct Pose
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        float o = 0.f;
    };

    // Johnson's spawn (guid 84079), stationary.
    inline constexpr std::uint32_t kJohnsonSpawnId = 84079;
    inline constexpr Pose kJohnsonHome{ -152.545f, -526.434f, 51.133f, 1.73877f };

    // The four Working Miners stand where the stock Defias Miners 79194, 79190, 79191 and 79185 stood (those spawns are
    // deleted by WP-B2's SQL), facing the walls they dig.
    inline constexpr std::size_t kCrewSize = 4;
    inline constexpr std::array<std::uint32_t, kCrewSize> kStockMinerSpawnIds{ { 79194, 79190, 79191, 79185 } };
    inline constexpr std::array<Pose, kCrewSize> kCrew{ {
        { -146.345f, -528.773f, 52.1728f, 0.366519f },  // 79194, 6.6 yd from Johnson
        { -159.594f, -529.266f, 52.2688f, 3.24631f },   // 79190, 7.6 yd
        { -149.5f, -519.485f, 53.0869f, 0.10472f },     // 79191, 7.6 yd
        { -158.652f, -513.984f, 52.7541f, 4.08407f },   // 79185, 13.9 yd
    } };

    // MJ1's spot: `kSpotOffset` yd from the miner toward `toward` (Johnson's spawn), on the room side: the miners face
    // the walls, so "in front of that miner" as the players see it is the side toward the room. A miner standing on
    // `toward` gives the miner's own spot.
    inline Vec2 PaydaySpot(Vec2 miner, Vec2 toward, float offset = kSpotOffset)
    {
        float const d = DeadminesKit::Distance(miner, toward);
        if (d < 1e-3f)
            return miner;
        float const step = std::min(offset, d);
        return { miner.x + (toward.x - miner.x) / d * step, miner.y + (toward.y - miner.y) / d * step };
    }

    // The fixed spot of crew slot `slot` (toward Johnson's spawn).
    inline Vec2 CrewSpot(std::size_t slot)
    {
        Pose const& m = kCrew[slot];
        return PaydaySpot({ m.x, m.y }, { kJohnsonHome.x, kJohnsonHome.y });
    }

    // The missile leaves this many ms after the Soak is registered, so it lands as the Soak resolves (flight
    // `distance / speed`). 0 when the flight is longer than the warning (it then lands late; never seen in this room:
    // the farthest spot is 10.9 yd, 1.4 s at 8 yd/s).
    inline std::uint32_t LaunchDelayMs(std::uint32_t warnMs, float distance, float speed = kPouchSpeed)
    {
        if (speed <= 0.f)
            return 0;
        double const flightMs = std::max(0.f, distance) / speed * 1000.0;
        if (flightMs >= warnMs)
            return 0;
        return static_cast<std::uint32_t>(std::lround(warnMs - flightMs));
    }

    // How many pouches a Payday throws: the difficulty's count, capped by the miners still digging.
    inline std::size_t PouchCount(bool heroic, std::size_t digging)
    {
        return std::min<std::size_t>(kPouchCount(heroic), digging);
    }

    // `want` distinct indices out of [0, available), each picked uniformly (a partial Fisher-Yates shuffle).
    // `rng(n)` returns a value in [0, n). Fewer than `want` when `available` is smaller.
    template <typename Rng>
    std::vector<std::size_t> PickDistinct(std::size_t available, std::size_t want, Rng&& rng)
    {
        std::vector<std::size_t> pool(available);
        std::iota(pool.begin(), pool.end(), std::size_t(0));
        std::size_t const n = std::min(available, want);
        for (std::size_t i = 0; i < n; ++i)
        {
            std::size_t const j = i + static_cast<std::size_t>(rng(static_cast<std::uint32_t>(available - i)));
            std::swap(pool[i], pool[std::min(j, available - 1)]);
        }
        pool.resize(n);
        return pool;
    }

    // MJ2: the catcher is the eligible player nearest the spot (several may stand in it; one pouch, one catcher).
    // Index into `distances`, or -1 for none.
    inline int PickCatcher(std::vector<float> const& distances)
    {
        if (distances.empty())
            return -1;
        return static_cast<int>(std::min_element(distances.begin(), distances.end()) - distances.begin());
    }

    // MJ5: Gold Fever is due (heroic only) once health is below the threshold.
    inline bool GoldFeverDue(bool heroic, float healthPct)
    {
        std::uint32_t const below = kGoldFeverBelowPct(heroic);
        return below > 0 && healthPct < static_cast<float>(below);
    }
}

#endif
