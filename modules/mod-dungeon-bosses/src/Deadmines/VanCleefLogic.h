/*
 * mod-dungeon-bosses, Deadmines: Edwin VanCleef, the Blackguards and the shadow image (WP-B8), the pure, host-testable
 * part (no engine headers): spell ids, per-difficulty tuning numbers, timers, the yard stages, the Ambush target pick
 * and the plan (which parts of the timeline run; B9's hard mode switches the guns off). Build spec: DM 'Edwin
 * VanCleef' Build spec VC1-VC9; handoff section 3.4 rows VC, section 7 #12 (DI-8).
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_VAN_CLEEF_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_VAN_CLEEF_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "GreenskinLogic.h"
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <vector>

namespace VanCleef
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsVanCleef;

    // Declared in apps/dbc-tools source/npcs/deadmines/edwin_vancleef.py. The guns reuse Greenskin's lane spells
    // (205340-205344: GreenskinLanes::Fire and Greenskin's cast bars); the stock spells kept are DeadminesRework.h's
    // (674, 3417 / 3391, 1833, 14903).
    enum VanCleefSpells : std::uint32_t
    {
        SPELL_AMBUSH_VANISH         = 205360,   // VC1 vanish look (SV 255, Vanish 1856), self, no effect
        SPELL_AMBUSH_HIT            = 205361,   // VC1 / VC2 circle hit: resolve copy, Physical (registry 40%)
        SPELL_SHADOW_IMAGE_VISUAL   = 205362,   // VC2 the image's look (SV 8262, Vanish 55964), self, no effect
        SPELL_FIRE_BOMB_TICK        = 205363,   // VC7 burning patch tick: resolve copy, Fire (registry 5%)
        SPELL_FIRE_BOMB_GROUND      = 205364,   // VC7 burning patch look (SV 9603, Fire Bomb 42629), 15 s dynobject
        SPELL_EXPOSE_ARMOR          = 205365,   // VC9 tank debuff: -6% armor per stack, 5 stacks, 20 s (SV 3441)
        SPELL_AMBUSH_STRIKE         = 205366,   // VC1 / VC2 landing look (SV 155, Ambush 8676), self, no effect
        // 205367-205379 spare
    };

    // DoAction ids of boss_edwin_vancleef_rework (the hooks B9's keg calls; section "Hard mode hooks" of the boss
    // file).
    enum VanCleefActions : std::int32_t
    {
        ACTION_HARD_MODE_LIT    = 1,    // B9: the fuse is lit (DATA_HARD_MODE set): re-read the plan (no guns)
        ACTION_HARD_MODE_RESET  = 2,    // B9: the hard mode ended without a kill (the ship blew): reset the plan
    };

    // Registry tags (the ledger's mechanic id: the build spec's VC number).
    enum VanCleefTags : std::uint32_t
    {
        TAG_AMBUSH          = 1,    // VC1 (VanCleef's own circle)
        TAG_SHADOW_IMAGE    = 2,    // VC2 (the image's circle)
        TAG_GUNS            = 3,    // VC3 (every lane and crossing of a volley)
        TAG_FIRE_BOMB       = 7,    // VC7
    };

    // ----------------------------------------------------------------------------------------------------------------
    // VC1 / VC2 Ambush from the Rigging
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kAmbushFirstMs = 12000;
    inline constexpr std::uint32_t kAmbushEveryMs = 20000;
    inline constexpr std::uint32_t kAmbushFastMs = 15000;           // below 33% (both difficulties)
    inline constexpr NH<std::uint32_t> kAmbushWarnMs{ 2000, 2000 }; // the marker; also how long he is untargetable
    inline constexpr float kAmbushRadius = 5.f;
    inline constexpr NH<float> kAmbushPct{ 40.f, 40.f };            // + 1 Weakened (ruling 15)
    inline constexpr std::uint32_t kShadowImageLifeMs = 2500;       // the image shows at the landing, then fades
    inline constexpr std::uint32_t kAmbushRetryMs = 2000;           // nobody to ambush: try again soon

    // ----------------------------------------------------------------------------------------------------------------
    // VC3 The guns: Greenskin's lanes on the same deck frame
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kGunsEveryMs = 25000;            // from 66%: at once, then every 25 s

    // Normal: 3 lanes rail to rail, 2 s. Heroic: Greenskin's Crossfire (4 across, 2 bow to stern, 2.5 s) with the
    // burning crossings (20 s, 10% Fire per second). Every part carries VC3's tag.
    inline Greenskin::LaneVolley GunsVolley(bool heroic)
    {
        Greenskin::LaneVolley guns = Greenskin::kFireOnMyMark(heroic);
        if (!heroic)
            guns.across = 3;
        guns.acrossTag = TAG_GUNS;
        guns.alongTag = TAG_GUNS;
        guns.cellTag = TAG_GUNS;
        return guns;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC4-VC7 The Brotherhood (boss-kit Blackguards)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kBlackguardCount = 2;
    inline constexpr std::uint32_t kBlackguardLifeMs = 300000;      // stock VanCleef's Allies 5200: 300 s
    inline constexpr float kBlackguardSideYd = 6.f;                 // they step out beside him
    inline constexpr std::uint32_t kCheapShotMs = 2000;             // VC5: stock 1833 (4 s) cut to 2 s
    inline constexpr float kCheapShotRangeYd = 5.f;                 // stock 1833 is a melee range spell
    inline constexpr std::uint32_t kCheapShotPollMs = 250;
    inline constexpr std::uint32_t kCheapShotGiveUpMs = 10000;      // never reached melee: no opener
    // VC6 Rupture 14903: the stock SmartAI timers (3-10 s, then 10-15 s), now on the victim (stock targeted itself).
    inline constexpr std::uint32_t kRuptureFirstMinMs = 3000;
    inline constexpr std::uint32_t kRuptureFirstMaxMs = 10000;
    inline constexpr std::uint32_t kRuptureMinMs = 10000;
    inline constexpr std::uint32_t kRuptureMaxMs = 15000;
    // VC7 Fire Bomb (heroic): a burning patch where a Blackguard dies.
    inline constexpr NH<bool> kFireBomb{ false, true };
    inline constexpr float kFireBombRadius = 6.f;
    inline constexpr std::uint32_t kFireBombMs = 15000;
    inline constexpr std::uint32_t kFireBombTickMs = 1000;
    inline constexpr float kFireBombPct = 5.f;                      // per tick, Fire, no slow, no Weakened

    // VC9 Expose Armor (heroic): a stack on the tank per Thrash proc (aura 3417 -> 3391).
    inline constexpr NH<bool> kExposeArmor{ false, true };
    inline constexpr std::uint32_t kExposeArmorMaxStacks = 5;       // also the spell's CumulativeAura

    // Two points beside `center`, `side` yd to its left and right (facing `orientation`): where the Blackguards step
    // out of the shadows.
    inline std::vector<Vec2> BlackguardSpots(Vec2 center, float orientation, float side = kBlackguardSideYd)
    {
        float const left = orientation + 1.57079633f;
        return { { center.x + std::cos(left) * side, center.y + std::sin(left) * side },
                 { center.x - std::cos(left) * side, center.y - std::sin(left) * side } };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The yard answers: the health stages (DM "The yard answers")
    // ----------------------------------------------------------------------------------------------------------------
    enum Stage : std::uint32_t
    {
        STAGE_GUNS          = 0x1,  // 66%: line 1, the guns start (unless the plan has none)
        STAGE_BROTHERHOOD   = 0x2,  // 50%: line 2 (emote), two Blackguards
        STAGE_RIGHTEOUS     = 0x4,  // 33%: line 3, Ambush every 15 s
        STAGE_IMAGE         = 0x8,  // the shadow image: 33% normal, 50% heroic
    };

    inline constexpr float kGunsPct = 66.f;
    inline constexpr float kBrotherhoodPct = 50.f;
    inline constexpr float kRighteousPct = 33.f;
    inline constexpr NH<float> kImagePct{ 33.f, 50.f };

    // Every stage reached at `healthPct` (the stock SmartAI's "between 0 and N%" checks: at or below N).
    inline std::uint32_t StagesReached(float healthPct, bool heroic)
    {
        std::uint32_t stages = 0;
        if (healthPct <= kGunsPct)
            stages |= STAGE_GUNS;
        if (healthPct <= kBrotherhoodPct)
            stages |= STAGE_BROTHERHOOD;
        if (healthPct <= kRighteousPct)
            stages |= STAGE_RIGHTEOUS;
        if (healthPct <= kImagePct(heroic))
            stages |= STAGE_IMAGE;
        return stages;
    }

    // The stages to run now, in order (a big hit can cross several at once): those reached and not yet done.
    inline std::vector<Stage> NewStages(std::uint32_t done, float healthPct, bool heroic)
    {
        std::uint32_t const fresh = StagesReached(healthPct, heroic) & ~done;
        std::vector<Stage> out;
        for (Stage s : { STAGE_GUNS, STAGE_BROTHERHOOD, STAGE_IMAGE, STAGE_RIGHTEOUS })
            if (fresh & s)
                out.push_back(s);
        return out;
    }

    // The next Ambush after one fires: 20 s, 15 s below 33% (STAGE_RIGHTEOUS done).
    inline std::uint32_t AmbushCooldownMs(std::uint32_t stagesDone)
    {
        return (stagesDone & STAGE_RIGHTEOUS) ? kAmbushFastMs : kAmbushEveryMs;
    }

    // Circles per Ambush: 1, then 2 once the shadow image is in (VC2 replaces VC1).
    inline std::uint32_t AmbushCircles(std::uint32_t stagesDone)
    {
        return (stagesDone & STAGE_IMAGE) ? 2u : 1u;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The plan: which parts of the timeline run. B9 (hard mode) switches the guns off ("the crews abandon the guns");
    // everything else is the heroic fight.
    // ----------------------------------------------------------------------------------------------------------------
    struct Plan
    {
        bool ambush = true;         // VC1 / VC2
        bool guns = true;           // VC3
        bool brotherhood = true;    // VC4-VC6 (VC7 with fireBomb)
        bool exposeArmor = false;   // VC9 (heroic)
        bool fireBomb = false;      // VC7 (heroic)
    };

    inline Plan PlanFor(bool heroic, bool hardMode)
    {
        Plan plan;
        plan.guns = !hardMode;
        plan.exposeArmor = kExposeArmor(heroic);
        plan.fireBomb = kFireBomb(heroic);
        return plan;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Ambush target pick
    // ----------------------------------------------------------------------------------------------------------------
    struct AmbushCandidate
    {
        std::size_t index = 0;      // the caller's index (its player list)
        bool tank = false;          // his current victim
    };

    // `count` distinct random non-tanks (fewer when there are fewer). With no non-tank at all (a solo test), the tank
    // alone, so the vanish still plays. `rng(n)` returns a value in [0, n).
    inline std::vector<std::size_t> PickAmbushTargets(std::vector<AmbushCandidate> const& candidates,
        std::uint32_t count, std::function<std::uint32_t(std::uint32_t)> const& rng)
    {
        std::vector<std::size_t> pool;
        for (AmbushCandidate const& c : candidates)
            if (!c.tank)
                pool.push_back(c.index);
        std::vector<std::size_t> out;
        if (pool.empty())
        {
            for (AmbushCandidate const& c : candidates)
            {
                if (c.tank)
                {
                    out.push_back(c.index);
                    break;
                }
            }
            return out;
        }
        while (out.size() < count && !pool.empty())
        {
            std::uint32_t const n = static_cast<std::uint32_t>(pool.size());
            std::uint32_t pick = rng(n);
            if (pick >= n)
                pick = n - 1;
            out.push_back(pool[pick]);
            pool.erase(pool.begin() + pick);
        }
        return out;
    }
}

#endif
