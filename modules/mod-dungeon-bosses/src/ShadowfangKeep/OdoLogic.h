/*
 * mod-dungeon-bosses, Shadowfang Keep: Odo the Blindwatcher (WP-S5), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, the bell rules and geometry. Build spec: SK 904-952 (build spec),
 * SK 816-903 (design), OD1-OD8. The Hunt itself (OD1 / OD2) is shared with the Echo of Odo: HuntLogic.h / Hunt.h.
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below (apps/dbc-tools
 * source/npcs/shadowfang_keep/odo_the_blindwatcher.py declares the same ids); tuning numbers as `NH<T>{ normal,
 * heroic }`. The damage percents are the same on both difficulties: the reference row (normal 1,300 / heroic 4,120)
 * makes the difference.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_ODO_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_ODO_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "HuntLogic.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace Odo
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using Ms = std::chrono::milliseconds;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsOdo;

    // apps/dbc-tools source/npcs/shadowfang_keep/odo_the_blindwatcher.py declares every one of these.
    enum OdoSpells : std::uint32_t
    {
        SPELL_ODO_HUNT_HOWL         = 205990,   // OD1 the 2 s howl (cast bar, SV 754)
        SPELL_ODO_HUNTED            = 205991,   // OD1 the debuff on the hunted player
        SPELL_ODO_MAUL_HIT          = 205992,   // OD2 the catch: the hunt circle's resolve copy (SV 577), no damage
        SPELL_ODO_MAUL              = 205993,   // OD2 the rider: 3 s stun + 35% bleed (spell_sfk_hunt_maul)
        SPELL_ODO_BOUND             = 205994,   // OD4 the bound to the bell (self visual, SV 12083)
        SPELL_ODO_BELL_LANDING      = 205995,   // OD4 the landing's resolve copy (35% Physical + Weakened)
        SPELL_ODO_BELL_RING         = 205996,   // OD3 the ring flash on the ringer (self visual, SV 8124)
        SPELL_ODO_DEAFENED          = 205997,   // OD5 damage taken +25% for 5 s (SV 875)
        SPELL_ODO_BLOOD_FRENZY      = 205998,   // OD6 heroic, damage dealt +20% per stack, no cap (SV 870)
        SPELL_ODO_CRACKED_BELL      = 205999,   // the cracked bell's smoke (aura on a stalker at the bell, SV 9774)
    };
    inline constexpr std::array<std::uint32_t, 10> kAllSpells{ {
        SPELL_ODO_HUNT_HOWL, SPELL_ODO_HUNTED, SPELL_ODO_MAUL_HIT, SPELL_ODO_MAUL, SPELL_ODO_BOUND,
        SPELL_ODO_BELL_LANDING, SPELL_ODO_BELL_RING, SPELL_ODO_DEAFENED, SPELL_ODO_BLOOD_FRENZY,
        SPELL_ODO_CRACKED_BELL,
    } };

    // Registry tags, the drill's (mod-boss-mechanics MechanicDrill.h `sfk-hunt`), so the ledger reads the same in the
    // sweep and in the dungeon: 1 caught at 80%, 2 bell not rung (MissedSoak), 3 the landing, 5 caught at 95%. The
    // drill's 4 (the ringer in the landing) is not split out here: one landing circle for everyone.
    enum OdoTags : std::uint32_t
    {
        TAG_HUNT_NORMAL     = 1,
        TAG_BELL            = 2,
        TAG_LANDING         = 3,
        TAG_HUNT_HEROIC     = 5,
    };
    inline constexpr NH<std::uint32_t> kHuntTag{ TAG_HUNT_NORMAL, TAG_HUNT_HEROIC };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec OD1-OD8; approved 2026-10-27)
    // ----------------------------------------------------------------------------------------------------------------

    // OD1 The Hunt: first at 10 s, then every 25 s (both difficulties); a random non-tank, healer included.
    inline constexpr Ms kHuntFirst{ 10000 };
    inline constexpr Ms kHuntEvery{ 25000 };
    inline constexpr Ms kBusyRetry{ 500 };          // a Hunt due while he casts or bounds waits this long
    inline constexpr float kHuntPickRange = 60.f;   // the room is 42 yd long
    // The chase numbers (radius 3, howl 2 s, 10 s, 200 ms passes; 80% / 95%): SfkHunt::OdoHunt(heroic).

    // OD2 Maul (the data: the aura 205993, 3 s, 1 s ticks; the bleed's value is the total percent).
    inline constexpr float kMaulPct = 35.f;
    inline constexpr std::uint32_t kMaulMs = 3000;
    inline constexpr std::uint32_t kMaulTickMs = 1000;

    // OD3 Ring the bell: a 2 yd circle under a ready bell, 1 s to ring.
    inline constexpr float kBellRadius = 2.f;
    inline constexpr float kBellZBand = 3.f;
    inline constexpr std::uint32_t kBellDwellMs = 1000;
    inline constexpr std::uint32_t kBellPollMs = 250;
    // The bots' soak resolves this long before the chase ends: a hunt nobody belled leaves a MissedSoak (tag 2).
    inline constexpr std::uint32_t kBellSoakEarlyMs = 250;
    // A rung bell is cracked for 40 s on normal, for the rest of the fight on heroic (Silenced Bells).
    inline constexpr std::uint64_t kNever = std::numeric_limits<std::uint64_t>::max();
    inline constexpr NH<std::uint64_t> kBellCrackMs{ 40000, kNever };

    // OD4 Bell landing: he bounds to the bell and lands 2 s later; 6 yd, 35% Physical + 1 Weakened.
    inline constexpr Ms kLandingWarn{ 2000 };
    inline constexpr float kLandingRadius = 6.f;
    inline constexpr float kLandingPct = 35.f;
    inline constexpr float kBoundSpeedZ = 8.f;      // a low arc (about 1.7 yd high) under the room's ceiling

    // OD5 Deafened: 5 s, damage taken +25% (the data). OD6 Blood Frenzy: +20% damage dealt per stack (the data).
    inline constexpr std::uint32_t kDeafenedMs = 5000;
    inline constexpr float kDeafenedPct = 25.f;
    inline constexpr float kBloodFrenzyPct = 20.f;

    // OD7 Howling Rage: the stock spells at 70, 50 and 30% health, once each, interruptible.
    inline constexpr std::array<std::uint32_t, 3> kHowlThresholdPct{ { 70, 50, 30 } };
    inline constexpr std::array<std::uint32_t, 3> kHowlSpells{ {
        ShadowfangKeepRework::SPELL_HOWLING_RAGE_1, ShadowfangKeepRework::SPELL_HOWLING_RAGE_2,
        ShadowfangKeepRework::SPELL_HOWLING_RAGE_3,
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The bells (handoff section 7 #24: the navmesh report's three points, at least 19 yd apart)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kBellCount = ShadowfangKeepRework::kBellSpots.size();
    inline constexpr std::uint32_t kBellGuidBase = 3011010;    // the three spawns, S5's SQL rev: 3011010-3011012

    // The bell spot nearest to `p` within `maxYd` (the spawned gameobjects map to their spots), else nullopt.
    inline std::optional<std::size_t> NearestBellSpot(Vec2 p, float maxYd = 5.f)
    {
        std::optional<std::size_t> best;
        float bestYd = maxYd;
        for (std::size_t i = 0; i < kBellCount; ++i)
        {
            float const d = DungeonKit::Distance(p, ShadowfangKeepRework::kBellSpots[i].XY());
            if (d <= bestYd)
            {
                bestYd = d;
                best = i;
            }
        }
        return best;
    }

    // Who may ring: never the hunted player; the tank only by clicking the bell (the bots' rule: the nearest bot that
    // is neither hunted nor tank; a human tank who clicks has chosen to pull Odo off himself).
    constexpr bool CanRing(bool isHunted, bool isTank, bool byClick)
    {
        return !isHunted && (byClick || !isTank);
    }

    // The bell the bots are sent to (the boss data rule: the nearest eligible bot rings the nearest ready bell): the
    // ready bell with the smallest distance to any eligible ringer. Ties go to the lower index. nullopt: no ready bell
    // or no ringer.
    inline std::optional<std::size_t> ChooseBell(std::array<bool, kBellCount> const& ready,
        std::vector<Vec2> const& ringers)
    {
        std::optional<std::size_t> best;
        float bestYd = std::numeric_limits<float>::max();
        for (std::size_t i = 0; i < kBellCount; ++i)
        {
            if (!ready[i])
                continue;
            for (Vec2 const& r : ringers)
            {
                float const d = DungeonKit::Distance(r, ShadowfangKeepRework::kBellSpots[i].XY());
                if (d < bestYd)
                {
                    bestYd = d;
                    best = i;
                }
            }
        }
        return best;
    }

    // The three bells' cracked state on the fight's own clock (ms since the pull).
    class BellBoard
    {
    public:
        void Reset() { _readyAt.fill(0); }

        bool IsReady(std::size_t bell, std::uint64_t nowMs) const
        {
            return bell < kBellCount && nowMs >= _readyAt[bell] && _readyAt[bell] != kNever;
        }

        std::array<bool, kBellCount> Ready(std::uint64_t nowMs) const
        {
            std::array<bool, kBellCount> out{};
            for (std::size_t i = 0; i < kBellCount; ++i)
                out[i] = IsReady(i, nowMs);
            return out;
        }

        std::size_t ReadyCount(std::uint64_t nowMs) const
        {
            std::size_t n = 0;
            for (std::size_t i = 0; i < kBellCount; ++i)
                n += IsReady(i, nowMs) ? 1 : 0;
            return n;
        }

        // Rings `bell` at `nowMs`: cracked for `crackMs` (kNever: for good). False when it was not ready.
        bool Ring(std::size_t bell, std::uint64_t nowMs, std::uint64_t crackMs)
        {
            if (!IsReady(bell, nowMs))
                return false;
            _readyAt[bell] = crackMs == kNever || nowMs >= kNever - crackMs ? kNever : nowMs + crackMs;
            return true;
        }

        // The bells that were cracked at `beforeMs` and are ready at `nowMs` (the normal 40 s ran out between two
        // ticks): the script restores their look.
        std::vector<std::size_t> Recovered(std::uint64_t beforeMs, std::uint64_t nowMs) const
        {
            std::vector<std::size_t> out;
            for (std::size_t i = 0; i < kBellCount; ++i)
                if (!IsReady(i, beforeMs) && IsReady(i, nowMs))
                    out.push_back(i);
            return out;
        }

        bool CrackedForGood(std::size_t bell) const { return bell < kBellCount && _readyAt[bell] == kNever; }

    private:
        std::array<std::uint64_t, kBellCount> _readyAt{};
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Howling Rage (OD7): each threshold fires once, in order, when he is free to cast
    // ----------------------------------------------------------------------------------------------------------------

    class HowlTracker
    {
    public:
        void Reset()
        {
            _crossed.fill(false);
            _cast.fill(false);
        }

        // Health after a hit, in percent: marks every threshold at or above it as due.
        void OnHealth(float healthPct)
        {
            for (std::size_t i = 0; i < kHowlThresholdPct.size(); ++i)
                if (healthPct <= static_cast<float>(kHowlThresholdPct[i]))
                    _crossed[i] = true;
        }

        // The next due howl (the highest threshold first), or nullopt.
        std::optional<std::size_t> Next() const
        {
            for (std::size_t i = 0; i < kHowlThresholdPct.size(); ++i)
                if (_crossed[i] && !_cast[i])
                    return i;
            return std::nullopt;
        }

        void MarkCast(std::size_t i)
        {
            if (i < _cast.size())
                _cast[i] = true;
        }

    private:
        std::array<bool, 3> _crossed{};
        std::array<bool, 3> _cast{};
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry
    // ----------------------------------------------------------------------------------------------------------------

    // The room's middle (on the report's map: 20 yd ESE of Odo, 7 yd SSW), the fallback landing of a grip back.
    inline Vec2 RoomCenter()
    {
        return ShadowfangKeepRework::ReportPoint(ShadowfangKeepRework::kOdoSpawn.XY(), ShadowfangKeepRework::kKeepUp,
            20.f, -7.f);
    }

    // ArenaGuard's grip landing for a player who left the room (the playtest line "the hunted player who leaves the
    // room is gripped back"): 8 yd from Odo toward where the player was, when the room holds that point at Odo's
    // height; else the room's middle.
    inline Vec2 GripLanding(Vec2 odo, float odoZ, Vec2 from)
    {
        Vec2 const p = DungeonKit::Advance(odo, DungeonKit::BearingTo(odo, from), 8.f);
        return ShadowfangKeepRework::OdoArena().Contains(p, odoZ) ? p : RoomCenter();
    }

    // The bound's horizontal speed: he lands `warn` after leaving (OD4's 2 s), however far the bell is.
    inline float BoundSpeedXY(float distYd, Ms warn = kLandingWarn)
    {
        float const secs = std::max(static_cast<float>(warn.count()) / 1000.f, 0.1f);
        return std::max(distYd / secs, 1.f);
    }
}

#endif
