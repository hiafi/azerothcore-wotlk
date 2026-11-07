/*
 * mod-dungeon-bosses, Deadmines: Sneed's Shredder and Sneed (WP-B3), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: DM 'Sneed's Shredder and
 * Sneed' Build spec SN1-SN12 (docs/dungeons/deadmines-rework.md), handoff section 3.4 rows SN.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below; tuning numbers as
 * `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`. Times are milliseconds; the script feeds the cast
 * queue GameTime milliseconds.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_SNEED_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_SNEED_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>

namespace Sneed
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;
    using Ms = std::int64_t;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsSneed;

    // Declared in apps/dbc-tools source/npcs/deadmines/sneed.py. The registry owns every SN mechanic's hit; these are
    // the cast bars, the channel, Tazer, the Splinter Spray tank hit and the visuals.
    enum SneedSpells : std::uint32_t
    {
        SPELL_SAW_SPIN_CAST             = 205240,   // SN1 / SN12: 2 s cast bar "Saw Spin" (Shredder, then Sneed)
        SPELL_SPLINTER_SPRAY_CAST       = 205241,   // SN2: 2 s cast bar
        SPELL_RUNAWAY_CAST              = 205242,   // SN3: 2 s cast bar
        SPELL_EMERGENCY_REPAIRS         = 205243,   // SN7: 6 s channel (normal); interruptible
        SPELL_EMERGENCY_REPAIRS_FAST    = 205244,   // SN7: 4 s channel (heroic)
        SPELL_OVERLOAD_SPARKS           = 205245,   // SN9: 3 s cast bar on the wreck (sparks)
        SPELL_OVERLOAD_BLAST            = 205246,   // SN9: the blast visual on the wreck (no damage)
        SPELL_TAZER                     = 205247,   // SN5: 2 s cast, chain of 3 (normal), damage set by its SpellScript
        SPELL_TAZER_HEROIC              = 205248,   // SN5: chain of 4 (heroic)
        SPELL_SAW_BOOMERANG_CAST        = 205249,   // SN6: 2 s cast bar
        SPELL_SAW_BOOMERANG_THROW       = 205250,   // SN6: the blade's missile to the line's far end (visual)
        SPELL_CLUSTER_BOMB_LOB          = 205251,   // SN10: the lobbed bomb (missile visual)
        SPELL_CLUSTER_BOMB_BLAST        = 205252,   // SN10 / SN11: the blast visual at a point
        SPELL_SPLINTER_SPRAY_TANK       = 205253,   // SN2: the tank's 30% of tank health (RefFlat in its SpellScript)
        SPELL_BROKEN_DOWN               = 205254,   // the wreck's smoke aura (also the descriptor's condition)
        SPELL_MALFUNCTION               = 205255,   // the visual with every Haywire emote
        // Copies of mod-boss-mechanics' resolve spell (Spell(id)), so the combat log names the mechanic:
        SPELL_SAW_SPIN_HIT              = 205256,   // SN1 / SN12, Physical
        SPELL_SPLINTER_SPRAY_HIT        = 205257,   // SN2, Physical
        SPELL_RUNAWAY_HIT               = 205258,   // SN3, Physical
        SPELL_SAW_BOOMERANG_HIT         = 205259,   // SN6, Physical
        SPELL_WRECK_OVERLOAD_HIT        = 205260,   // SN9, Fire
        SPELL_CLUSTER_BOMB_HIT          = 205261,   // SN10 / SN11, Fire
        // 205262-205269 spare
    };

    inline constexpr std::array<std::uint32_t, 22> kAllSpells{ {
        SPELL_SAW_SPIN_CAST, SPELL_SPLINTER_SPRAY_CAST, SPELL_RUNAWAY_CAST, SPELL_EMERGENCY_REPAIRS,
        SPELL_EMERGENCY_REPAIRS_FAST, SPELL_OVERLOAD_SPARKS, SPELL_OVERLOAD_BLAST, SPELL_TAZER, SPELL_TAZER_HEROIC,
        SPELL_SAW_BOOMERANG_CAST, SPELL_SAW_BOOMERANG_THROW, SPELL_CLUSTER_BOMB_LOB, SPELL_CLUSTER_BOMB_BLAST,
        SPELL_SPLINTER_SPRAY_TANK, SPELL_BROKEN_DOWN, SPELL_MALFUNCTION, SPELL_SAW_SPIN_HIT, SPELL_SPLINTER_SPRAY_HIT,
        SPELL_RUNAWAY_HIT, SPELL_SAW_BOOMERANG_HIT, SPELL_WRECK_OVERLOAD_HIT, SPELL_CLUSTER_BOMB_HIT,
    } };

    // Stock SpellVisual of Eject Sneed 5141 (the stock eject's dynamite puff), played when Sneed climbs out.
    inline constexpr std::uint32_t kEjectSpellVisual = 148;

    // Registry tags (the ledger's per-mechanic key): the build spec's SN numbers.
    enum SneedTags : std::uint32_t
    {
        TAG_SAW_SPIN        = 1,
        TAG_SPLINTER_SPRAY  = 2,
        TAG_RUNAWAY         = 3,
        TAG_SAW_BOOMERANG   = 6,
        TAG_WRECK_OVERLOAD  = 9,
        TAG_CLUSTER_BOMB    = 10,
        TAG_BOMBLET         = 11,
        TAG_SALVAGED_SAW    = 12,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec "Mechanics" table; damage in % of reference health)
    // ----------------------------------------------------------------------------------------------------------------

    // Haywire SN1-SN4
    inline constexpr NH<Ms> kHaywireFirstMs{ 8000, 8000 };          // after the pull and after each reboot
    inline constexpr NH<Ms> kHaywireEveryMs{ 15000, 15000 };
    inline constexpr NH<Ms> kHaywireWarnMs{ 2000, 2000 };           // emote + 2 s cast bar
    inline constexpr NH<bool> kChainedHaywire{ false, true };       // SN4
    inline constexpr NH<Ms> kChainWarnMs{ 1500, 1500 };             // SN4: lands 1.5 s after the first resolves
    inline constexpr NH<float> kSawSpinRadius{ 8.f, 8.f };
    inline constexpr NH<float> kSawSpinPct{ 40.f, 40.f };
    inline constexpr NH<float> kSprayAngleDeg{ 90.f, 90.f };
    inline constexpr NH<float> kSprayLength{ 10.f, 10.f };
    inline constexpr NH<float> kSprayPct{ 30.f, 30.f };             // non-tanks, + Weakened
    inline constexpr NH<float> kSprayTankPct{ 30.f, 30.f };         // the tank, % of tank reference, before armor
    inline constexpr NH<float> kRunawayWidth{ 4.f, 4.f };
    inline constexpr NH<float> kRunawayLength{ 30.f, 30.f };
    inline constexpr NH<float> kRunawayExclude{ 4.f, 4.f };
    inline constexpr NH<float> kRunawayPct{ 35.f, 35.f };
    inline constexpr NH<float> kRunawayChargeSpeed{ 24.f, 24.f };   // yd/s along the line after it resolves
    inline constexpr NH<Ms> kRunawayReturnMs{ 3000, 3000 };         // fail-safe: back to the tank after this

    // Back in the Saddle SN7, SN8
    inline constexpr NH<Ms> kRepairFirstMs{ 8000, 8000 };           // after each eject
    inline constexpr NH<Ms> kRepairEveryMs{ 20000, 20000 };
    inline constexpr NH<Ms> kRepairChannelMs{ 6000, 4000 };         // the DBC durations of 205243 / 205244
    inline constexpr NH<Ms> kRepairRunTimeoutMs{ 6000, 6000 };      // channel where he stands if the run takes longer
    inline constexpr NH<float> kRepairBreakPct{ 10.f, 10.f };       // of Sneed's health, dealt during the channel
    inline constexpr std::uint8_t kMaxReboots = 2;
    inline constexpr NH<std::array<float, kMaxReboots>> kRebootHealthPct{ { { 30.f, 15.f } }, { { 40.f, 20.f } } };

    // Wreck Overload SN9 (the third breakdown)
    inline constexpr NH<float> kOverloadRadius{ 10.f, 10.f };
    inline constexpr NH<Ms> kOverloadWarnMs{ 3000, 3000 };
    inline constexpr NH<float> kOverloadPct{ 60.f, 60.f };          // Fire, no Weakened (ruling 30)

    // Tazer SN5
    inline constexpr NH<Ms> kTazerAfterChannelMs{ 12000, 12000 };   // after each SN7 channel begins
    inline constexpr NH<Ms> kTazerSalvagedFirstMs{ 9000, 9000 };    // after the blast
    inline constexpr NH<Ms> kTazerSalvagedEveryMs{ 15000, 15000 };
    inline constexpr std::array<float, 3> kTazerPctNormal{ { 20.f, 14.f, 10.f } };
    inline constexpr std::array<float, 4> kTazerPctHeroic{ { 35.f, 25.f, 18.f, 12.f } };

    // Saw Boomerang SN6
    inline constexpr NH<Ms> kBoomerangFirstMs{ 3000, 3000 };        // after each eject
    inline constexpr NH<Ms> kBoomerangEveryMs{ 15000, 15000 };
    inline constexpr NH<Ms> kBoomerangWarnMs{ 2000, 2000 };
    inline constexpr NH<float> kBoomerangWidth{ 3.f, 3.f };
    inline constexpr NH<float> kBoomerangLength{ 25.f, 25.f };
    inline constexpr NH<float> kBoomerangExclude{ 4.f, 4.f };
    inline constexpr NH<float> kBoomerangPct{ 25.f, 25.f };         // per pass, + 1 Weakened per pass
    // The blade's speed: a player at about 10 yd sees the return pass 1.5 s after the out pass ((50 - 2 x 10) / 20).
    inline constexpr NH<float> kBoomerangSpeed{ 20.f, 20.f };

    // Cluster Bomb SN10, SN11 (heroic)
    inline constexpr NH<bool> kClusterBomb{ false, true };
    inline constexpr NH<Ms> kClusterFirstMs{ 10000, 10000 };        // after each eject
    inline constexpr NH<Ms> kClusterEveryMs{ 20000, 20000 };
    inline constexpr NH<Ms> kClusterWarnMs{ 2000, 2000 };
    inline constexpr NH<float> kClusterRadius{ 5.f, 5.f };
    inline constexpr NH<float> kClusterPct{ 30.f, 30.f };
    inline constexpr std::size_t kBombletCount = 3;
    inline constexpr NH<float> kBombletRadius{ 4.f, 4.f };
    inline constexpr NH<float> kBombletMinDist{ 6.f, 6.f };
    inline constexpr NH<float> kBombletMaxDist{ 10.f, 10.f };
    inline constexpr NH<Ms> kBombletWarnMs{ 2000, 2000 };
    inline constexpr NH<float> kBombletPct{ 30.f, 30.f };

    // Salvaged Saw SN12 (after the blast)
    inline constexpr NH<Ms> kSalvagedSawFirstMs{ 6000, 6000 };
    inline constexpr NH<Ms> kSalvagedSawEveryMs{ 15000, 15000 };

    // Sneed's cast queue: at least this long between the starts of any two of SN5, SN6, SN10, SN12 and a repair run.
    inline constexpr Ms kQueueSpacingMs = 3000;

    // ----------------------------------------------------------------------------------------------------------------
    // Haywire: which malfunction
    // ----------------------------------------------------------------------------------------------------------------

    enum class Malfunction : std::uint8_t
    {
        SawSpin,
        SplinterSpray,
        Runaway,
    };
    inline constexpr std::uint8_t kMalfunctionCount = 3;

    // Random, never the same as `last` (the last malfunction fired, a chained one included). `roll` is any random
    // number; no `last` (the first of the fight) picks among all three.
    inline Malfunction PickMalfunction(std::optional<Malfunction> last, std::uint32_t roll)
    {
        if (!last)
            return static_cast<Malfunction>(roll % kMalfunctionCount);
        std::uint32_t const offset = 1 + roll % (kMalfunctionCount - 1);
        return static_cast<Malfunction>((static_cast<std::uint32_t>(*last) + offset) % kMalfunctionCount);
    }

    // SN4: the chained follow-up, never the same as the first.
    inline Malfunction PickChained(Malfunction first, std::uint32_t roll)
    {
        return PickMalfunction(first, roll);
    }

    inline char const* MalfunctionName(Malfunction m)
    {
        switch (m)
        {
            case Malfunction::SawSpin:
                return "saw-spin";
            case Malfunction::SplinterSpray:
                return "splinter-spray";
            case Malfunction::Runaway:
                return "runaway";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The reboot ladder (SN7-SN9): breakdowns and reboots
    // ----------------------------------------------------------------------------------------------------------------

    enum class Breakdown : std::uint8_t
    {
        Eject,              // Sneed climbs out and will try to repair
        EjectAndOverload,   // the third breakdown: Sneed climbs out and the wreck overloads (SN9)
    };

    struct RebootLadder
    {
        std::uint8_t breakdowns = 0;
        std::uint8_t reboots = 0;

        // The Shredder reached 1 health.
        Breakdown OnBreakdown()
        {
            ++breakdowns;
            return reboots >= kMaxReboots ? Breakdown::EjectAndOverload : Breakdown::Eject;
        }

        // Sneed may run repairs while ejected (never after the overload).
        bool RepairsLeft() const { return reboots < kMaxReboots; }

        // A completed repair: the Shredder's new health in percent of its maximum (0: no reboot left).
        float OnReboot(bool heroic)
        {
            if (!RepairsLeft())
                return 0.f;
            float const pct = kRebootHealthPct(heroic)[reboots];
            ++reboots;
            return pct;
        }
    };

    // SN7 damage break: kRepairBreakPct of Sneed's maximum health, dealt during the channel.
    inline std::uint32_t RepairBreakThreshold(std::uint32_t maxHealth, bool heroic)
    {
        double const v = static_cast<double>(maxHealth) * kRepairBreakPct(heroic) / 100.0;
        return static_cast<std::uint32_t>(std::max(1.0, std::ceil(v)));
    }

    inline bool BreaksRepair(std::uint32_t damageDuringChannel, std::uint32_t maxHealth, bool heroic)
    {
        return damageDuringChannel >= RepairBreakThreshold(maxHealth, heroic);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tazer (SN5)
    // ----------------------------------------------------------------------------------------------------------------

    inline std::size_t TazerTargets(bool heroic)
    {
        return heroic ? kTazerPctHeroic.size() : kTazerPctNormal.size();
    }

    // The percent of reference health the `jump`-th target takes (0 = the first target); 0 past the last.
    inline float TazerJumpPct(bool heroic, std::size_t jump)
    {
        if (heroic)
            return jump < kTazerPctHeroic.size() ? kTazerPctHeroic[jump] : 0.f;
        return jump < kTazerPctNormal.size() ? kTazerPctNormal[jump] : 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Sneed's cast queue (build spec: "at least 3 s between any two of SN5, SN6, SN10 and the start of SN7; nothing
    // during SN7; SN5 goes first, anything due within 3 s of it waits"). SN12 (Salvaged Saw) joins it after the blast.
    // ----------------------------------------------------------------------------------------------------------------

    enum class Cast : std::uint8_t
    {
        None,
        Tazer,
        RepairRun,
        SawSpin,
        SawBoomerang,
        ClusterBomb,
    };
    inline constexpr std::size_t kCastKinds = 6;

    class CastQueue
    {
    public:
        static constexpr Ms kNever = std::numeric_limits<Ms>::max();

        void Reset()
        {
            _due.fill(kNever);
            _lastStart.reset();
            _busy = false;
        }

        // `c` is due at `at` (replaces any earlier due time).
        void Schedule(Cast c, Ms at) { _due[Index(c)] = at; }
        void Cancel(Cast c) { _due[Index(c)] = kNever; }
        Ms Due(Cast c) const { return _due[Index(c)]; }

        // A repair run, from its start to its channel's end: nothing starts meanwhile.
        void SetBusy(bool busy) { _busy = busy; }
        bool Busy() const { return _busy; }

        // What to start now (Cast::None: nothing, or wait).
        Cast Next(Ms now) const
        {
            if (_busy)
                return Cast::None;
            if (_lastStart && now < *_lastStart + kQueueSpacingMs)
                return Cast::None;
            Ms const tazer = Due(Cast::Tazer);
            if (tazer <= now)
                return Cast::Tazer;
            if (tazer != kNever && tazer - now < kQueueSpacingMs)
                return Cast::None;      // Tazer goes first: anything due within 3 s of it waits
            // Earliest due first; on a tie, the order below (the repair run is the fight's main mechanic).
            Cast best = Cast::None;
            Ms bestDue = kNever;
            for (Cast c : { Cast::RepairRun, Cast::SawSpin, Cast::SawBoomerang, Cast::ClusterBomb })
            {
                Ms const due = Due(c);
                if (due <= now && due < bestDue)
                {
                    best = c;
                    bestDue = due;
                }
            }
            return best;
        }

        // `c` started at `now`; it comes back `every` later (0: not by itself, e.g. Tazer before the blast).
        void Started(Cast c, Ms now, Ms every)
        {
            _lastStart = now;
            _due[Index(c)] = every > 0 ? now + every : kNever;
        }

        // SN7's channel began at `now`: Tazer is due `tazerDelay` later (12 s on both difficulties).
        void ChannelStarted(Ms now, Ms tazerDelay) { Schedule(Cast::Tazer, now + tazerDelay); }

        // A completed repair skips the Tazer its channel scheduled (Sneed is back in the Shredder).
        void RepairCompleted() { Cancel(Cast::Tazer); }

    private:
        static std::size_t Index(Cast c) { return static_cast<std::size_t>(c); }

        std::array<Ms, kCastKinds> _due{ { kNever, kNever, kNever, kNever, kNever, kNever } };
        std::optional<Ms> _lastStart;
        bool _busy = false;
    };

    inline char const* CastName(Cast c)
    {
        switch (c)
        {
            case Cast::None:
                return "none";
            case Cast::Tazer:
                return "tazer";
            case Cast::RepairRun:
                return "repairs";
            case Cast::SawSpin:
                return "salvaged-saw";
            case Cast::SawBoomerang:
                return "saw-boomerang";
            case Cast::ClusterBomb:
                return "cluster-bomb";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry
    // ----------------------------------------------------------------------------------------------------------------

    // A line from `from` through `through` to `length` yd (Runaway, Saw Boomerang). A `through` on top of `from`
    // uses `fallbackOrientation` (the caster's facing).
    inline Vec2 LineEnd(Vec2 from, Vec2 through, float length, float fallbackOrientation)
    {
        float const o = DeadminesKit::Distance(from, through) < 0.01f ? fallbackOrientation
            : DeadminesKit::BearingTo(from, through);
        return DeadminesKit::Advance(from, o, length);
    }

    // SN11: the bomblets' spots around the bomb at `center`. `angle01` and `dist01` are random numbers in [0, 1] per
    // bomblet: any direction, kBombletMinDist to kBombletMaxDist away.
    inline std::array<Vec2, kBombletCount> BombletSpots(Vec2 center, std::array<float, kBombletCount> const& angle01,
        std::array<float, kBombletCount> const& dist01, bool heroic)
    {
        float constexpr twoPi = 6.28318530717958647692f;
        float const lo = kBombletMinDist(heroic);
        float const hi = kBombletMaxDist(heroic);
        std::array<Vec2, kBombletCount> spots{};
        for (std::size_t i = 0; i < kBombletCount; ++i)
        {
            float const a = std::clamp(angle01[i], 0.f, 1.f) * twoPi;
            float const d = lo + std::clamp(dist01[i], 0.f, 1.f) * (hi - lo);
            spots[i] = DeadminesKit::Advance(center, a, d);
        }
        return spots;
    }

    // SN2's tank hit: DeadminesKit::InFrontalCone (DeadminesKitMath.h, shared with Mr. Smite's SM2 / SM3).
    using DeadminesKit::InFrontalCone;
}

#endif
