/*
 * mod-dungeon-bosses, Stratholme S11: Nerub'enkan (10437), "The Web", the pure, host-testable part (no engine
 * headers). Build spec ST 2859-2911 (docs/dungeons/stratholme-rework.md, the whole "Nerub'enkan" section), handoff
 * section 3.4 rows NE, 3.5 row S11, 3.6 and 3.8. Tested by tests/strat_nerubenkan_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsNerubenkan (206645-206664), declared in apps/dbc-tools
 *                 source/npcs/stratholme/nerubenkan.py
 *   Tuning        NH<> constants: one number per difficulty, straight from the build spec
 *   Webs          NE3 the patch rules: the merge rule is the kit's PuddleSet (merge = true); the per-player inside
 *                 clock decides the slow (after the 1 s entry grace) and Stuck (after 2 s, then 3 s immune)
 *   Skitter       NE6 the patch farthest from him within 30 yd (and on his arena)
 *   Hatch, Brood  NE5 the capped hatch (6 alive on normal), NE7 two scarabs per patch, no cap
 *   Glob missile  NE1 when to launch the look-only glob so it arrives as the circle resolves
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_NERUBENKAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_NERUBENKAN_LOGIC_H

#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratNerubenkan
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsNerubenkan;

    enum NerubenkanSpells : std::uint32_t
    {
        SPELL_NE_WEB_SPRAY          = kSpellSlice.first + 0,    // 206645 NE1 the 3 s mark on the carrier (a debuff)
        SPELL_NE_GLOB_MISSILE       = kSpellSlice.first + 1,    // 206646 NE1 the glob missile (look only)
        SPELL_NE_GLOB_HIT           = kSpellSlice.first + 2,    // 206647 NE2 the carrier's 15% (kit percent spell)
        SPELL_NE_GLOB_SPLASH        = kSpellSlice.first + 3,    // 206648 NE2 the splash on others (resolve copy)
        SPELL_NE_STICKY_WEB         = kSpellSlice.first + 4,    // 206649 NE3 the 50% slow inside a web
        SPELL_NE_STUCK              = kSpellSlice.first + 5,    // 206650 NE3 the 2 s root (registry rider)
        SPELL_NE_WEB_LOOK_5         = kSpellSlice.first + 6,    // 206651 NE3 the patch stalker's look, 5 yd
        SPELL_NE_WEB_LOOK_7         = kSpellSlice.first + 7,    // 206652 NE3 the patch stalker's look, 7 yd (heroic)
        SPELL_NE_COCOON_CAST        = kSpellSlice.first + 8,    // 206653 NE4 the 2 s cast bar
        SPELL_NE_COCOON_HOLD        = kSpellSlice.first + 9,    // 206654 NE4 the hold on the wrapped player (stun)
        SPELL_NE_COCOONED           = kSpellSlice.first + 10,   // 206655 NE4 the wrapped player's damage immunity
        SPELL_NE_SKITTER_BURST      = kSpellSlice.first + 11,   // 206656 NE6 the landing burst (resolve copy)
        SPELL_NE_SKITTER_LANDING    = kSpellSlice.first + 12,   // 206657 NE6 the landing look (self visual)
        SPELL_NE_BROOD_CALL         = kSpellSlice.first + 13,   // 206658 NE7 heroic: the 2.5 s cast bar
        SPELL_NE_COCOON_SPLITS      = kSpellSlice.first + 14,   // 206659 NE5 the cocoon splits open (self visual)
        SPELL_NE_POISON_BURST       = kSpellSlice.first + 15,   // 206660 NE6 the landing's poison fog (self visual)
        // 206661-206664 spare
    };
    static_assert(SPELL_NE_POISON_BURST <= kSpellSlice.last, "Nerub'enkan's spells must stay in his slice");

    // Stock spells kept: Pierce Armor 6016 on the tank (NE8; DD scales it on heroic; StratholmeRework.h's
    // SPELL_PIERCE_ARMOR), the scarab's Poison Proc 13299 (its own SmartAI reset row).

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum NerubenkanTags : std::uint32_t
    {
        TAG_GLOB            = 1,    // NE1 / NE2 the glob landing
        TAG_WEB             = 2,    // NE3 a web patch (telegraph-only persistent zone of the PuddleField)
        TAG_STUCK           = 3,    // NE3 Stuck (a RegistryHit: Weakened + the root)
        TAG_SKITTER         = 4,    // NE6 the landing circle
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 2859-2911; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // NE1 Web Spray / NE2 the glob
    inline constexpr std::uint32_t kWebSprayFirstMs = 8000;
    inline constexpr std::uint32_t kWebSprayEveryMs = 15000;
    inline constexpr std::uint32_t kWebSprayWarnMs = 3000;          // the circle follows the carrier this long
    inline constexpr float kGlobRadius = 5.f;                       // the splash: anyone else within 5 yd
    inline constexpr NH<float> kGlobSplashPct{ 25.f, 30.f };        // + Weakened (others)
    inline constexpr float kGlobTargetPct = 15.f;                   // the carrier, not avoidable (206647's value)
    inline constexpr float kGlobMissileSpeed = 20.f;                // yd/s: 206646's Speed in nerubenkan.py

    // NE3 web patches (the whole fight; nothing destroys them)
    inline constexpr NH<float> kWebRadius{ 5.f, 7.f };
    inline constexpr std::uint32_t kWebArmMs = 1000;                // a new patch counts 1 s after it lands
    inline constexpr std::uint32_t kWebTickMs = 250;                // the PuddleField tick (= its poll)
    inline constexpr std::uint32_t kWebGraceMs = 1000;              // the entry grace: slowed from 1 s inside
    inline constexpr std::uint32_t kStuckAfterMs = 2000;            // Stuck after 2 s inside
    inline constexpr std::uint32_t kStuckRootMs = 2000;             // 206650's duration
    inline constexpr std::uint32_t kStuckImmuneMs = 3000;           // then immune to Stuck for 3 s
    inline constexpr std::uint32_t kSlowRefreshBelowMs = 500;       // re-cast the slow when it has less left
    // X2's drop spot rule: a carrier bot may step into an old web this long before its glob lands (MaxDwell), so it
    // stands in it about this long plus its way out (the landing center needs to be only 0.5 yd inside the old web).
    // Kept under the Stuck timer (orchestrator note on X2).
    inline constexpr std::uint32_t kDropMaxDwellMs = 800;
    static_assert(kDropMaxDwellMs + 1000 < kStuckAfterMs, "a carrier dropping onto an old web must never get Stuck");

    // X2's drop spot room (DropSpotRule::Room, the polygon form): the floor of his arena circle, not the circle (R-1-A
    // m-2: the circle's west rim runs past his door into the ziggurat, so a carrier's edge candidates sat on walls).
    // A star outline from the arena center (3858, -3540), one point every 15 degrees from bearing 0: the farthest
    // navmesh floor along that ray reachable from the center (z 137.3 to 145.3, at most 30 yd), 1.5 yd in; the stoop
    // rays (90 to 120 degrees) stop at his spawn, so the outline never wraps behind him to his door. [navmesh estimate,
    // F-1c: 1,552 sq yd, 95% of it floor; the circle is 2,827, 67% floor]
    inline constexpr std::array<Vec2, 24> kDropRoom{ {
        { 3886.5f, -3540.0f }, { 3885.0f, -3532.8f }, { 3881.8f, -3526.2f }, { 3878.2f, -3519.8f },
        { 3870.0f, -3519.2f }, { 3860.6f, -3530.3f }, { 3858.0f, -3529.0f }, { 3855.0f, -3528.9f },
        { 3852.2f, -3530.0f }, { 3852.7f, -3534.7f }, { 3844.6f, -3532.2f }, { 3831.0f, -3532.8f },
        { 3837.0f, -3540.0f }, { 3843.0f, -3544.0f }, { 3842.0f, -3549.2f }, { 3842.8f, -3555.2f },
        { 3848.2f, -3556.9f }, { 3852.7f, -3559.8f }, { 3858.0f, -3568.5f }, { 3865.2f, -3567.0f },
        { 3871.8f, -3563.8f }, { 3878.2f, -3560.2f }, { 3881.8f, -3553.8f }, { 3885.0f, -3547.2f } } };
    static_assert(kWebGraceMs < kStuckAfterMs, "the slow comes before Stuck");

    // NE4 Cocoon / NE5 hatch
    inline constexpr std::uint32_t kCocoonFirstMs = 15000;
    inline constexpr std::uint32_t kCocoonEveryMs = 25000;
    inline constexpr std::uint32_t kCocoonCastMs = 2000;            // 206653's cast time
    inline constexpr NH<std::uint32_t> kCocoonHoldMs{ 8000, 6000 }; // unbroken this long: it hatches
    inline constexpr NH<std::uint32_t> kCocoonHealth{ 8000, 12000 };    // data: 300582's normal row / heroic template
    inline constexpr std::uint32_t kHatchCount = 3;
    inline constexpr NH<std::uint32_t> kHatchCap{ 6, 0 };           // live scarabs on normal; heroic: no cap
    inline constexpr NH<std::uint32_t> kScarabHealth{ 2000, 2500 }; // data: 10876's normal row / heroic template

    // NE6 Skitter
    inline constexpr std::uint32_t kSkitterFirstMs = 22000;
    inline constexpr std::uint32_t kSkitterEveryMs = 30000;
    inline constexpr std::uint32_t kSkitterRetryMs = 1000;          // due with no patch yet: look again
    inline constexpr std::uint32_t kSkitterWarnMs = 2000;
    inline constexpr std::uint32_t kSkitterFlightMs = 1000;         // he leaps 1 s before the burst
    inline constexpr float kSkitterRadius = 8.f;
    inline constexpr float kSkitterRange = 30.f;                    // the farthest patch within 30 yd of him
    inline constexpr NH<float> kSkitterPct{ 30.f, 40.f };           // + Weakened
    inline constexpr float kSkitterMinJumpSpeed = 10.f;             // yd/s
    static_assert(kSkitterFlightMs < kSkitterWarnMs, "he leaves after the marker shows");

    // NE7 Brood Call (heroic)
    inline constexpr std::uint32_t kBroodFirstMs = 30000;
    inline constexpr std::uint32_t kBroodEveryMs = 30000;
    inline constexpr std::uint32_t kBroodCastMs = 2500;             // 206658's cast time
    inline constexpr std::uint32_t kBroodPerPatch = 2;

    // NE8 stock tank kit: Pierce Armor 6016 at 1 s, then every 12 to 15 s (stock row 1)
    inline constexpr std::uint32_t kPierceFirstMs = 1000;
    inline constexpr std::uint32_t kPierceEveryMinMs = 12000;
    inline constexpr std::uint32_t kPierceEveryMaxMs = 15000;
    inline constexpr std::uint32_t kPierceRetryMs = 1000;

    // The cast queue (DungeonKit::CastQueue): his casts never overlap; the second waits for the first (ST
    // Implementation). Skitter holds him for its marker (he must not start a cast he would break by leaping).
    enum NerubenkanCasts : std::uint32_t
    {
        CAST_COCOON         = 1,
        CAST_SKITTER        = 2,
        CAST_BROOD_CALL     = 3,
    };
    inline constexpr std::uint8_t kPriorityBrood = 3;
    inline constexpr std::uint8_t kPriorityCocoon = 2;
    inline constexpr std::uint8_t kPrioritySkitter = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // NE3 the per-player web clock
    // ----------------------------------------------------------------------------------------------------------------

    // `msInside`: the time the player has stood in the union of armed webs without a break (PuddleField::Inside).
    constexpr bool SlowDue(std::uint32_t msInside)
    {
        return msInside >= kWebGraceMs;
    }

    // Stuck when 2 s inside and not immune (immuneUntil: the end of the last Stuck's 3 s immunity, on the AI clock).
    constexpr bool StuckDue(std::uint32_t msInside, std::uint64_t now, std::uint64_t immuneUntil)
    {
        return msInside >= kStuckAfterMs && now >= immuneUntil;
    }

    // The immunity a Stuck at `now` grants: the 2 s root, then 3 s.
    constexpr std::uint64_t StuckImmuneUntil(std::uint64_t now)
    {
        return now + kStuckRootMs + kStuckImmuneMs;
    }

    // A player released from a Cocoon gets a fresh web window (R-1-A m-1): their web clock counts from the last tick
    // they were held (`lastHeldAt`, on the AI clock; kNeverHeld: never), not from when they stepped in, so the slow
    // comes 1 s and Stuck 2 s after the release, never at once. Leaving the web resets `msInside` as before.
    inline constexpr std::uint64_t kNeverHeld = ~std::uint64_t(0);

    constexpr std::uint32_t WebClockAfterHold(std::uint32_t msInside, std::uint64_t now, std::uint64_t lastHeldAt)
    {
        if (lastHeldAt == kNeverHeld || now < lastHeldAt)
            return msInside;
        std::uint64_t const sinceRelease = now - lastHeldAt;
        return sinceRelease < msInside ? static_cast<std::uint32_t>(sinceRelease) : msInside;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE6 Skitter: the patch farthest from him within 30 yd, on his arena (he never leaps off it: the leash would
    // evade him). nullopt: no patch qualifies (no leap).
    // ----------------------------------------------------------------------------------------------------------------

    template <class OnArena>
    std::optional<std::size_t> PickSkitterPatch(Vec2 boss, std::vector<Vec2> const& patches, OnArena&& onArena,
        float range = kSkitterRange)
    {
        std::optional<std::size_t> best;
        float bestDist = -1.f;
        for (std::size_t i = 0; i < patches.size(); ++i)
        {
            float const d = DungeonKit::Distance(boss, patches[i]);
            if (d > range || !onArena(patches[i]))
                continue;
            if (d > bestDist)
            {
                bestDist = d;
                best = i;
            }
        }
        return best;
    }

    // The jump's horizontal speed: lands after kSkitterFlightMs, never slower than kSkitterMinJumpSpeed.
    inline float SkitterJumpSpeed(float distance)
    {
        float const v = distance * 1000.f / float(kSkitterFlightMs);
        return std::max(v, kSkitterMinJumpSpeed);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE5 / NE7 the scarabs
    // ----------------------------------------------------------------------------------------------------------------

    // An unbroken cocoon's hatch: 3 scarabs, at most 6 alive on normal (heroic: no cap).
    constexpr std::uint32_t HatchSize(bool heroic, std::uint32_t alive)
    {
        return DungeonKit::CappedWaveSize(kHatchCount, alive, kHatchCap(heroic));
    }

    // Brood Call: two scarabs on every patch, no cap (the heroic's soft enrage).
    constexpr std::uint32_t BroodCallCount(std::size_t patches)
    {
        return static_cast<std::uint32_t>(patches) * kBroodPerPatch;
    }

    // Where the scarabs of one patch (or one cocoon) appear: `n` points round `center`, 1.5 yd out, evenly spaced.
    inline std::vector<Vec2> ScarabSpots(Vec2 center, std::uint32_t n, float startAngle = 0.f)
    {
        std::vector<Vec2> out;
        out.reserve(n);
        float constexpr kRingYd = 1.5f;
        for (std::uint32_t i = 0; i < n; ++i)
            out.push_back(DungeonKit::Advance(center, startAngle + DungeonKit::kTwoPi * float(i) / float(n), kRingYd));
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // NE1 the glob missile: a homing missile on the carrier, launched so it arrives as the circle resolves
    // ----------------------------------------------------------------------------------------------------------------

    // The clock time to launch at: `landAt` minus the flight over `distance` (0 when the flight is longer).
    inline std::uint64_t GlobLaunchAt(std::uint64_t landAt, float distance, float speed = kGlobMissileSpeed)
    {
        if (speed <= 0.f)
            return landAt;
        std::uint64_t const flight =
            static_cast<std::uint64_t>(std::lround(std::max(0.f, distance) / speed * 1000.f));
        return flight >= landAt ? 0 : landAt - flight;
    }
}

#endif
