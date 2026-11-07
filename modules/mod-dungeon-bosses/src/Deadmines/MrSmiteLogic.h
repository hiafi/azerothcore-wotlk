/*
 * mod-dungeon-bosses, Deadmines: Mr. Smite (WP-B5), the pure, host-testable part (no engine headers): spell ids, per-
 * difficulty tuning numbers, timers, target picks and geometry. Build spec: DM 'Mr. Smite' Build spec SM1-SM13.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`.
 *
 * Random picks take a `pick(n)` callable that returns a uniform index in [0, n) (the script passes urand, the tests a
 * fixed sequence), so every rule here runs on the host.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_MR_SMITE_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_MR_SMITE_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace MrSmite
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsMrSmite;

    // Declared in apps/dbc-tools source/npcs/deadmines/mr_smite.py. Cast bars are no-effect casts (the registry owns
    // every hit); Smite Slam and the harpoon impact deal the damage the script sets (DeadminesKit::RefFlat as base
    // point 0 at cast), so DD never scales them and they read the heroic reference row instead.
    enum MrSmiteSpells : std::uint32_t
    {
        SPELL_SMITE_SWEEPING_SLASH      = 205290,   // SM2 cast bar, 2 s
        SPELL_SMITE_BACKSWING           = 205291,   // SM3 cast bar, 1.5 s (heroic)
        SPELL_SMITE_RECKLESS_CHARGE     = 205292,   // SM4 cast bar, 2 s (the first dash)
        SPELL_SMITE_HAMMER_DROP         = 205293,   // SM5 cast bar, 1.5 s, then the 1 s leap
        SPELL_SMITE_HAMMER_LANDING      = 205294,   // SM5 landing visual (instant, no effect)
        SPELL_SMITE_DEBRIS              = 205295,   // SM6 rockfall visual at a point (instant, no effect)
        SPELL_SMITE_SHOCKWAVE           = 205296,   // SM7 cast bar, 2 s
        SPELL_SMITE_AFTERSHOCKS         = 205297,   // SM8 cast bar, 1.5 s (heroic)
        SPELL_SMITE_SLAM_NO_STUN        = 205298,   // SM9 1.5 s cast on the tank, physical, no stun (6435 copy)
        SPELL_SMITE_HARPOON_SWEEP       = 205299,   // SM10 cast bar, 2 s
        SPELL_SMITE_HAFT_SLAM           = 205300,   // SM11 cast bar, 1.5 s (heroic)
        SPELL_SMITE_HARPOON_VOLLEY      = 205301,   // SM12 cast bar, 2.5 s
        SPELL_SMITE_HARPOON_IMPACT      = 205302,   // SM12 the carrier's own hit (unavoidable, no Weakened)
        SPELL_SMITE_SLASH_TANK          = 205303,   // SM2 / SM3 the tank's own 30% of the tank row (the cones skip it)
        SPELL_SMITE_HARPOON_LANDING     = 205304,   // SM12 the impact look at each carrier's feet (instant, no effect)
    };
    static_assert(kSlice.Contains(SPELL_SMITE_SWEEPING_SLASH) && kSlice.Contains(SPELL_SMITE_HARPOON_LANDING),
        "Mr. Smite's spells stay inside his slice");

    // ----------------------------------------------------------------------------------------------------------------
    // Weapons: creature_equip_template 646 ids. Phase 1 is the dual cutlasses (2); the swaps at 67% and 34% bring the
    // hammer (3) and the harpoon (4) in a random order, never the same weapon twice (Improvise). Id 1 (the stock single
    // scimitar) is unused.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Weapon : std::uint8_t
    {
        Cutlasses   = 2,
        Hammer      = 3,
        Harpoon     = 4,
    };

    inline constexpr std::size_t kWeaponCount = 3;
    inline constexpr std::array<std::uint8_t, 2> kSwapHealthPct{ { 67, 34 } };

    // The fight's weapon order from one coin flip: cutlasses, then the hammer and the harpoon in either order.
    inline std::array<Weapon, kWeaponCount> WeaponOrder(bool hammerFirst)
    {
        if (hammerFirst)
            return { { Weapon::Cutlasses, Weapon::Hammer, Weapon::Harpoon } };
        return { { Weapon::Cutlasses, Weapon::Harpoon, Weapon::Hammer } };
    }

    // The weapon of phase `phase` (0 = the pull, 1 = after the first swap, 2 = after the second).
    inline Weapon WeaponForPhase(std::array<Weapon, kWeaponCount> const& order, std::size_t phase)
    {
        return order[std::min(phase, kWeaponCount - 1)];
    }

    // The swap due at `healthPct` after `swapsDone` swaps: its index (0 at 67%, 1 at 34%), or none.
    inline std::optional<std::size_t> SwapDue(float healthPct, std::size_t swapsDone)
    {
        if (swapsDone >= kSwapHealthPct.size())
            return std::nullopt;
        if (healthPct < static_cast<float>(kSwapHealthPct[swapsDone]))
            return swapsDone;
        return std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec SM1-SM12; damage in % of the reference row, times in ms)
    // ----------------------------------------------------------------------------------------------------------------

    // SM1 Smite Stomp: stock 6432 (a 10 s stun within 45 yd), cut to 2 s per target (handoff section 7 #3).
    inline constexpr std::uint32_t kStompStunMs = 2000;
    // The swap: kneel at the chest, the new weapon 1.5 s later, back in the fight 3 s after the kneel (stock timings).
    inline constexpr std::uint32_t kSwapWeaponMs = 1500;
    inline constexpr std::uint32_t kSwapResumeMs = 3000;
    // If the chest is never reached (a blocked path), kneel where he stands after this long.
    inline constexpr std::uint32_t kSwapFallbackMs = 8000;
    inline constexpr std::uint32_t kHealthCheckMs = 500;
    inline constexpr float kChestFacing = 5.558f;       // stock: he kneels facing the chest

    // SM2 / SM3 Sweeping Slash and Backswing: cone 90 degrees, 8 yd; 30% non-tank, 30% of the tank row for a tank.
    inline constexpr float kSlashAngle = 90.f;
    inline constexpr float kSlashLength = 8.f;
    inline constexpr float kSlashPct = 30.f;
    inline constexpr std::uint32_t kSlashWarnMs = 2000;
    inline constexpr std::uint32_t kSlashFirstMs = 6000;
    inline constexpr std::uint32_t kSlashEveryMs = 12000;
    inline constexpr NH<bool> kBackswing{ false, true };

    // SM2 / SM3's tank hit: the cones are TankExempt (bots read them as a Frontal, the tank gets no Weakened), so the
    // script hits the victim itself if it stands in the arc when the cone resolves: in front (Sweeping Slash) or
    // behind (Backswing). `reach` is both units' combat reach.
    inline bool InSlashArc(Vec2 smite, float facing, Vec2 tank, bool rear, float reach)
    {
        float constexpr pi = 3.14159265358979323846f;
        return DeadminesKit::InFrontalCone(smite, facing + (rear ? pi : 0.f), tank, kSlashAngle, kSlashLength, reach);
    }

    // SM4 Reckless Charge: a 3 yd line from Smite to a random non-tank at least 8 yd away, 4 yd at his end excluded;
    // heroic chains 3 dashes, each from the last one's end to a different non-tank (2 s marker, then 1.5 s each).
    inline constexpr float kDashWidth = 3.f;
    inline constexpr float kDashExclude = 4.f;
    inline constexpr float kDashMinDistance = 8.f;
    inline constexpr float kDashPct = 35.f;
    inline constexpr std::uint32_t kDashWarnMs = 2000;
    inline constexpr std::uint32_t kDashFollowWarnMs = 1500;
    inline constexpr std::uint32_t kDashFirstMs = 10000;
    inline constexpr std::uint32_t kDashEveryMs = 15000;
    inline constexpr NH<std::uint8_t> kDashCount{ 1, 3 };
    inline constexpr float kDashSpeed = 42.f;           // SPEED_CHARGE
    inline constexpr std::uint32_t kReturnDelayMs = 1000;   // after the last dash or the landing: back to the tank

    // SM5 / SM6 Hammer Drop and its debris.
    inline constexpr float kHammerDropRadius = 6.f;
    inline constexpr float kHammerDropMinDistance = 10.f;
    inline constexpr float kHammerDropPct = 40.f;
    inline constexpr std::uint32_t kHammerDropWarnMs = 2500;
    inline constexpr std::uint32_t kHammerDropCastMs = 1500;    // the cast bar; the leap fills the last second
    inline constexpr float kHammerLeapSpeedZ = 10.f;
    inline constexpr float kHammerLeapMinSpeed = 8.f;
    inline constexpr std::uint32_t kHammerDropFirstMs = 5000;   // after he resumes
    inline constexpr std::uint32_t kHammerDropEveryMs = 15000;
    inline constexpr NH<std::uint8_t> kDebrisCount{ 0, 3 };
    inline constexpr float kDebrisRadius = 4.f;
    inline constexpr float kDebrisPct = 20.f;
    inline constexpr std::uint32_t kDebrisWarnMs = 2000;

    // SM7 / SM8 Shockwave and the aftershocks.
    inline constexpr float kShockwaveLength = 25.f;
    inline constexpr float kShockwaveWidth = 4.f;
    inline constexpr float kShockwavePct = 35.f;
    inline constexpr std::uint32_t kShockwaveWarnMs = 2000;
    inline constexpr std::uint32_t kShockwaveFirstMs = 10000;
    inline constexpr std::uint32_t kShockwaveEveryMs = 15000;
    inline constexpr NH<bool> kAftershocks{ false, true };
    inline constexpr float kAftershockOffsetDeg = 30.f;

    // SM9 Smite Slam: stock 6435 deals 50 Physical at level 20 (BasePoints 49 + DieSides 1); 3.9% of the tank row is
    // 50 on normal (1,290) and 160 on heroic (4,110), the same share DD would keep for the stock spell.
    inline constexpr float kSlamTankPct = 3.9f;
    inline constexpr std::uint32_t kSlamFirstMs = 3000;
    inline constexpr std::uint32_t kSlamEveryMs = 10000;

    // SM10 / SM11 Harpoon Sweep and Haft Slam.
    inline constexpr float kSweepInner = 5.f;
    inline constexpr float kSweepOuter = 14.f;
    inline constexpr float kSweepPct = 35.f;
    inline constexpr std::uint32_t kSweepWarnMs = 2000;
    inline constexpr std::uint32_t kSweepFirstMs = 5000;
    inline constexpr std::uint32_t kSweepEveryMs = 14000;
    inline constexpr NH<bool> kHaftSlam{ false, true };
    inline constexpr float kHaftSlamRadius = 6.f;
    inline constexpr float kHaftSlamPct = 35.f;

    // SM12 Harpoon Volley: a Spread on every non-tank; the carrier takes 15% (unavoidable), anyone else in its
    // splash 25% plus Weakened.
    inline constexpr NH<float> kVolleyRadius{ 6.f, 8.f };
    inline constexpr float kVolleySplashPct = 25.f;
    inline constexpr float kVolleyCarrierPct = 15.f;
    inline constexpr std::uint32_t kVolleyWarnMs = 2500;
    inline constexpr std::uint32_t kVolleyFirstMs = 10000;
    inline constexpr std::uint32_t kVolleyEveryMs = 14000;

    // Every heroic follow-up lands 1.5 s after the shape before it resolves (gap 8, handoff section 3.9).
    inline constexpr std::uint32_t kFollowUpWarnMs = 1500;

    // An ability that comes due while Smite is busy (a dash chain, a leap) waits this long and tries again.
    inline constexpr std::uint32_t kBusyRetryMs = 1000;

    // Registry tags (the failure ledger): the build spec ids.
    enum MrSmiteTags : std::uint32_t
    {
        TAG_SWEEPING_SLASH  = 2,
        TAG_BACKSWING       = 3,
        TAG_RECKLESS_CHARGE = 4,
        TAG_HAMMER_DROP     = 5,
        TAG_DEBRIS          = 6,
        TAG_SHOCKWAVE       = 7,
        TAG_AFTERSHOCKS     = 8,
        TAG_HARPOON_SWEEP   = 10,
        TAG_HAFT_SLAM       = 11,
        TAG_HARPOON_VOLLEY  = 12,
    };

    // How long a dash chain of `dashes` keeps Smite busy, from the first marker to the last dash's resolve.
    inline constexpr std::uint32_t DashChainMs(std::uint8_t dashes)
    {
        return dashes == 0 ? 0 : kDashWarnMs + (dashes - 1u) * kDashFollowWarnMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Target picks
    // ----------------------------------------------------------------------------------------------------------------

    // A non-tank player a pick may choose: an opaque id (the raw guid) and where it stands.
    struct Candidate
    {
        std::uint64_t id = 0;
        Vec2 pos;
    };

    // One dash's target (handoff section 3.4 SM4; the `deadmines-followups` drill's pick=other rule):
    //   1. a candidate not yet in `chain`, at least `minDistance` from `from`, at random;
    //   2. else the farthest candidate not yet in `chain`;
    //   3. else (everyone is in the chain) a candidate other than the chain's last pick, at random;
    //   4. else the only candidate; none when there are no candidates.
    // Returns the index into `candidates`.
    template <typename Pick>
    std::optional<std::size_t> PickDashTarget(std::vector<Candidate> const& candidates, Vec2 from,
        std::vector<std::uint64_t> const& chain, float minDistance, Pick&& pick)
    {
        if (candidates.empty())
            return std::nullopt;

        auto inChain = [&chain](std::uint64_t id)
        {
            return std::find(chain.begin(), chain.end(), id) != chain.end();
        };

        std::vector<std::size_t> far;
        std::optional<std::size_t> farthest;
        float farthestDist = -1.f;
        for (std::size_t i = 0; i < candidates.size(); ++i)
        {
            if (inChain(candidates[i].id))
                continue;
            float const d = DeadminesKit::Distance(from, candidates[i].pos);
            if (d >= minDistance)
                far.push_back(i);
            if (d > farthestDist)
            {
                farthestDist = d;
                farthest = i;
            }
        }
        if (!far.empty())
            return far[pick(far.size()) % far.size()];
        if (farthest)
            return farthest;

        std::vector<std::size_t> others;
        std::uint64_t const last = chain.empty() ? 0 : chain.back();
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].id != last)
                others.push_back(i);
        if (!others.empty())
            return others[pick(others.size()) % others.size()];
        return std::size_t(0);
    }

    // Hammer Drop's target: a random candidate at least `minDistance` away, else the farthest one.
    template <typename Pick>
    std::optional<std::size_t> PickLeapTarget(std::vector<Candidate> const& candidates, Vec2 from, float minDistance,
        Pick&& pick)
    {
        return PickDashTarget(candidates, from, {}, minDistance, pick);
    }

    // Up to `count` different candidates other than `exclude`, at random (the debris targets).
    template <typename Pick>
    std::vector<std::size_t> PickOthers(std::vector<Candidate> const& candidates, std::uint64_t exclude,
        std::size_t count, Pick&& pick)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].id != exclude)
                pool.push_back(i);
        std::vector<std::size_t> out;
        while (out.size() < count && !pool.empty())
        {
            std::size_t const j = pick(pool.size()) % pool.size();
            out.push_back(pool[j]);
            pool.erase(pool.begin() + static_cast<std::ptrdiff_t>(j));
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry
    // ----------------------------------------------------------------------------------------------------------------

    // Where a dash from `from` toward `target` ends: on the target, but never shorter than `minLength` (a target
    // closer than that still gets a dash of `minLength` through it). A target on `from` dashes along `facing`.
    inline Vec2 DashEnd(Vec2 from, Vec2 target, float minLength, float facing)
    {
        float const d = DeadminesKit::Distance(from, target);
        if (d >= minLength)
            return target;
        float const o = d > 0.01f ? DeadminesKit::BearingTo(from, target) : facing;
        return { from.x + std::cos(o) * minLength, from.y + std::sin(o) * minLength };
    }
}

#endif
