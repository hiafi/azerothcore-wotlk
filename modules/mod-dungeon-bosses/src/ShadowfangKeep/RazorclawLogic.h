/*
 * mod-dungeon-bosses, Shadowfang Keep: Razorclaw the Butcher (WP-S2), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: SK 444-479 (build spec), SK
 * 357-443 (design), RC1-RC4; handoff section 3.5 rows RC.
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the
 * `RazorclawSpells` enum (apps/dbc-tools source/npcs/shadowfang_keep/razorclaw.py declares the same ids); tuning
 * numbers as `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the same on both
 * difficulties: the reference row (normal 1,300 / heroic 4,120) makes the difference.
 *
 * Meat Hook is shared with Silverlaine's Echo of Razorclaw (WP-S3, BS4: "as RC1, from the echo; no heroic bleed or twin
 * lines"). Its rules live here (HookTuning, HookFor, HookRule, HookVolleyMemory, DragSpeedXY) and its engine glue in
 * MeatHook.h; the echo calls MeatHook::Throw with HookFor(false) on both difficulties.
 *
 *   RC1  Meat Hook       registry line 3 yd wide from the thrower through a random non-tank at least 8 yd away, 5 yd
 *                        past it (clipped at the walls), the first 4 yd excluded; 2 s warning; 35% + Weakened, then a
 *                        drag to the thrower's front in under 1 s. First at 8 s, then every 15 s; never within 3 s
 *                        before a Butcher's Cut (Rhythm). Heroic: Twin Hooks (two lines, different players, once per
 *                        player per throw) and Hung to Bleed (20% over 8 s, no Weakened).
 *   RC2  Tenderize       each of his melee hits on the tank adds a stack: +10% of his melee per stack.
 *   RC3  Butcher's Cut   at 3 stacks: a 2 s cast, a 90 degree / 10 yd Frontal (tank exempt): non-tanks 40% + Weakened,
 *                        the tank a 250% weapon hit; then the stacks clear.
 *   RC4  Offal Slick     heroic: the Cut's cone stays on the floor 30 s, 5% a second and a slow, no Weakened.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_RAZORCLAW_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_RAZORCLAW_LOGIC_H

#include "DungeonKitLogic.h"
#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace Razorclaw
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsRazorclaw;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/razorclaw.py. The registry owns the line, the cone and
    // the slick (resolve copies); the script sets the bleed's ticks (base point 0 = DungeonKit::RefFlat) and casts the
    // tank's weapon hit.
    enum RazorclawSpells : std::uint32_t
    {
        SPELL_RC_MEAT_HOOK_CAST         = 205930,   // RC1 cast bar, 2 s (also the Echo of Razorclaw's)
        SPELL_RC_MEAT_HOOK_HIT          = 205931,   // RC1 the line's resolve copy + spell_sfk_meat_hook_once
        SPELL_RC_MEAT_HOOK_CHAIN        = 205932,   // RC1 the drag's look (SV 11055), also the arena grip's look
        SPELL_RC_HUNG_TO_BLEED          = 205933,   // RC1 heroic bleed, 4 ticks of 2 s
        SPELL_RC_TENDERIZED             = 205934,   // RC2 +10% melee damage taken per stack, 3 stacks
        SPELL_RC_BUTCHERS_CUT_CAST      = 205935,   // RC3 cast bar, 2 s
        SPELL_RC_BUTCHERS_CUT_HIT       = 205936,   // RC3 the cone's resolve copy (non-tanks)
        SPELL_RC_BUTCHERS_CUT_TANK      = 205937,   // RC3 the tank's 250% weapon hit
        SPELL_RC_OFFAL_SLICK            = 205938,   // RC4 heroic, the slick's tick (resolve copy)
    };
    static_assert(kSlice.Contains(SPELL_RC_MEAT_HOOK_CAST) && kSlice.Contains(SPELL_RC_OFFAL_SLICK),
        "Razorclaw's spells stay inside his slice");

    // RC4's blood pools: ShadowfangKeepRework::GO_SFK_OFFAL_SLICK (gameobject_template in WP-S2's SQL rev: GENERIC,
    // Blood of Heroes display 4211 at size 0.6, handoff section 3.10 gap 8 top pick).

    // Registry tags (the ledger and `.mech` read them; encounter-local).
    enum RazorclawTags : std::uint32_t
    {
        TAG_MEAT_HOOK       = 1,
        TAG_BUTCHERS_CUT    = 2,
        TAG_OFFAL_SLICK     = 3,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RC1 Meat Hook: the tuning a thrower uses (Razorclaw per difficulty; the echo HookFor(false) on both)
    // ----------------------------------------------------------------------------------------------------------------
    struct HookTuning
    {
        std::uint8_t lines = 1;             // lines per throw, each on a different non-tank (fewer if fewer qualify)
        float widthYd = 3.f;
        float overrunYd = 5.f;              // past the target, then clipped at the walls
        float excludeYd = 4.f;              // L4's excluded zone at the thrower's end (the tank and melee)
        std::uint32_t warnMs = 2000;        // the line marker and the cast bar
        float minRangeYd = 8.f;             // targets at least this far (melee never draw it); nobody: skipped
        float maxRangeYd = 40.f;            // the kitchen's longest line from him is 18.7 yd
        bool requireLos = true;
        float pct = 35.f;                   // % of reference non-tank health, + 1 Weakened
        float bleedPct = 0.f;               // heroic Hung to Bleed over bleedMs (0: none); no Weakened
        std::uint32_t bleedMs = 8000;
        std::uint32_t bleedTickMs = 2000;
        float frontYd = 3.f;                // the drag lands this far in front of the thrower (toward its victim)
        std::uint32_t dragMs = 750;         // the drag's flight ("the pull lasts under 1 sec")
        std::uint32_t tag = TAG_MEAT_HOOK;
    };

    inline constexpr NH<std::uint8_t> kHookLines{ 1, 2 };     // heroic Twin Hooks
    inline constexpr NH<float> kHookPct{ 35.f, 35.f };
    inline constexpr NH<float> kHookBleedPct{ 0.f, 20.f };    // heroic Hung to Bleed: 35 + 20 = 55 < 75 (cap)

    // Razorclaw's hook per difficulty. The Echo of Razorclaw (S3) throws HookFor(false) on both difficulties.
    constexpr HookTuning HookFor(bool heroic)
    {
        HookTuning t;
        t.lines = kHookLines(heroic);
        t.pct = kHookPct(heroic);
        t.bleedPct = kHookBleedPct(heroic);
        return t;
    }

    inline constexpr std::uint32_t kHookFirstMs = 8000;
    inline constexpr std::uint32_t kHookEveryMs = 15000;
    inline constexpr std::uint32_t kHookRetryMs = 250;          // held back (a Cut due or running, a cast): retry

    // The bleed's tick, % of the reference non-tank row (20% over 8 s in 2 s ticks: 5% a tick).
    constexpr float BleedTickPct(HookTuning const& t)
    {
        std::uint32_t const ticks = t.bleedTickMs ? t.bleedMs / t.bleedTickMs : 0;
        return ticks ? t.bleedPct / static_cast<float>(ticks) : 0.f;
    }

    // The pick rule of one throw: non-tanks only, at least minRangeYd away (nobody there: the throw is skipped), in
    // line of sight. `widen` (`.sfktest`): the tank (or a GM alone) may be picked when nobody else qualifies.
    inline DungeonKit::PickRule HookRule(HookTuning const& t, bool widen = false)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = widen;
        rule.minRange = t.minRangeYd;
        rule.maxRange = t.maxRangeYd;
        rule.requireLos = t.requireLos;
        return rule;
    }

    // Up to `t.lines` distinct targets (indices into `candidates`). `rand(n)` returns [0, n).
    template <class Rand>
    std::vector<std::size_t> PickHookTargets(std::vector<DungeonKit::PickCandidate> const& candidates,
        HookTuning const& t, bool widen, Rand&& rand)
    {
        return DungeonKit::PickDistinctFrom(candidates, HookRule(t, widen), t.lines, rand);
    }

    // The drag's horizontal speed: the distance in dragMs, never slower than kDragMinSpeedXY.
    inline constexpr float kDragMinSpeedXY = 20.f;
    inline constexpr float kDragMinSpeedZ = 3.f;                // a short drag still arcs a little
    inline constexpr float kGravity = 19.29110527038574f;       // Movement::gravity

    inline float DragSpeedXY(float distYd, HookTuning const& t)
    {
        float const byTime = t.dragMs ? distYd * 1000.f / static_cast<float>(t.dragMs) : kDragMinSpeedXY;
        return std::max(kDragMinSpeedXY, byTime);
    }

    // The flight time (ms) of DungeonKit::JumpTo's arc over `distYd` at `speedXY` (Spell::EffectPullTowards' speedZ).
    inline float JumpFlightMs(float distYd, float speedXY, float minSpeedZ)
    {
        if (speedXY <= 0.f)
            return 0.f;
        float const speedZ = std::max(minSpeedZ, distYd / speedXY * 0.5f * kGravity);
        return 2.f * speedZ / kGravity * 1000.f;
    }

    // Who one throw already hooked (Twin Hooks: "a player standing in both lines is hit once"). The registry casts
    // both lines of a throw on one tick, each hitting inside its CastSpell call, with the thrower as the original
    // caster; spell_sfk_meat_hook_once drops a unit an earlier line of the same throw hit. Keys are raw guids. A throw
    // lasts kVolleyWindowMs from its first hit (two throws of one thrower are at least 5 s apart: the echo's cadence).
    class HookVolleyMemory
    {
    public:
        static constexpr std::uint64_t kVolleyWindowMs = 1000;

        bool AlreadyHit(std::uint64_t thrower, std::uint64_t unit, std::uint64_t nowMs) const
        {
            auto const it = _byThrower.find(thrower);
            if (it == _byThrower.end() || nowMs - it->second.startMs > kVolleyWindowMs)
                return false;
            std::vector<std::uint64_t> const& hit = it->second.hit;
            return std::find(hit.begin(), hit.end(), unit) != hit.end();
        }

        void Record(std::uint64_t thrower, std::uint64_t unit, std::uint64_t nowMs)
        {
            Entry& e = _byThrower[thrower];
            if (e.hit.empty() || nowMs - e.startMs > kVolleyWindowMs)
            {
                e.startMs = nowMs;
                e.hit.clear();
            }
            if (std::find(e.hit.begin(), e.hit.end(), unit) == e.hit.end())
                e.hit.push_back(unit);
        }

        void Forget(std::uint64_t thrower)
        {
            _byThrower.erase(thrower);
        }

        std::size_t Throwers() const { return _byThrower.size(); }

    private:
        struct Entry
        {
            std::uint64_t startMs = 0;
            std::vector<std::uint64_t> hit;
        };

        std::unordered_map<std::uint64_t, Entry> _byThrower;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RC2 Tenderize / RC3 Butcher's Cut
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kCutStacks = 3;              // at 3 Tenderized stacks he casts the Cut
    inline constexpr std::uint32_t kTenderizeMaxStacks = 3;     // the DBC's CumulativeAura; held there until the Cut
    inline constexpr float kTenderizePctPerStack = 10.f;        // the DBC's base points (melee damage taken)
    inline constexpr std::uint32_t kCutWarnMs = 2000;
    inline constexpr float kCutAngleDeg = 90.f;
    inline constexpr float kCutLengthYd = 10.f;
    inline constexpr NH<float> kCutPct{ 40.f, 40.f };           // non-tanks in the cone, + 1 Weakened
    inline constexpr float kCutTankWeaponPct = 250.f;           // the tank: 2.5 x a swing (the DBC's 205937)

    // His melee on a target with `stacks` Tenderized stacks (the aura's amount x stacks): 1.0, 1.1, 1.2, 1.3.
    constexpr float TenderizedMultiplier(std::uint32_t stacks)
    {
        return 1.f + kTenderizePctPerStack * static_cast<float>(std::min(stacks, kTenderizeMaxStacks)) / 100.f;
    }

    // The Cut's tank hit lands when the tank stands in the cone (TankExempt skipped it in the registry).
    inline bool InCutCone(Vec2 boss, float facing, Vec2 target, float reachYd)
    {
        return DungeonKit::InFrontalCone(boss, facing, target, kCutAngleDeg, kCutLengthYd, reachYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hook / Cut rhythm: "never cast within 3 s before a Butcher's Cut, so a hooked player always lands with time
    // to leave the cone". The hook waits while a Cut is due (2+ stacks: one swing from it) or running; a Cut waits
    // until kHookCutGapMs after the last hook landed. Times are the AI's own clock (ms since the pull), which no cast
    // bar pauses.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kHookCutGapMs = 3000;
    inline constexpr std::uint32_t kHookDeferStacks = 2;
    // A Cut whose resolve never came back (cancelled, lost) stops holding the rhythm this long after its warning.
    inline constexpr std::uint32_t kCutResolveGraceMs = 2000;

    class Rhythm
    {
    public:
        void Reset()
        {
            _hookLandMs = 0;
            _hooked = false;
            _cutEndMs = 0;
            _cutPending = false;
        }

        bool HookMayStart(std::uint64_t nowMs, std::uint32_t tankStacks) const
        {
            return !CutBusy(nowMs) && tankStacks < kHookDeferStacks;
        }

        bool CutMayStart(std::uint64_t nowMs, std::uint32_t tankStacks) const
        {
            if (tankStacks < kCutStacks || CutBusy(nowMs))
                return false;
            return !_hooked || nowMs >= _hookLandMs + kHookCutGapMs;
        }

        // A hook was thrown at `nowMs`: it lands `warnMs` later.
        void HookThrown(std::uint64_t nowMs, std::uint32_t warnMs)
        {
            _hooked = true;
            _hookLandMs = nowMs + warnMs;
        }

        // A Cut started at `nowMs`: it resolves `warnMs` later (CutLanded).
        void CutStarted(std::uint64_t nowMs, std::uint32_t warnMs)
        {
            _cutEndMs = nowMs + warnMs;
            _cutPending = true;
        }

        // The Cut's cone resolved (the stacks are cleared).
        void CutLanded() { _cutPending = false; }

        // A Cut is casting, or its resolve has not come back yet (at most kCutResolveGraceMs past its warning).
        bool CutBusy(std::uint64_t nowMs) const
        {
            return nowMs < _cutEndMs || (_cutPending && nowMs < _cutEndMs + kCutResolveGraceMs);
        }

        // The earliest Cut start the last hook allows (0 before the first hook).
        std::uint64_t CutNotBeforeMs() const { return _hooked ? _hookLandMs + kHookCutGapMs : 0; }

    private:
        std::uint64_t _hookLandMs = 0;
        bool _hooked = false;
        std::uint64_t _cutEndMs = 0;
        bool _cutPending = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RC4 heroic Offal Slick
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<bool> kOffalSlick{ false, true };
    inline constexpr std::uint32_t kSlickMs = 30000;
    inline constexpr std::uint32_t kSlickTickMs = 1000;
    inline constexpr float kSlickPct = 5.f;                     // per tick; the kit's 205201 slow rides every tick

    // Three blood pools dressing the slick (GO 4211 at size 0.6 is about 2.9 x 3.2 yd): along the cone's axis and at
    // +-22 degrees, all inside the 90 degree / 10 yd cone.
    struct PoolSpot
    {
        float distYd;
        float offsetDeg;
    };
    inline constexpr std::array<PoolSpot, 3> kSlickPools{ { { 4.f, 0.f }, { 7.f, -22.f }, { 7.f, 22.f } } };

    inline std::array<Vec2, 3> SlickPoolPoints(Vec2 origin, float facing)
    {
        std::array<Vec2, 3> out{};
        for (std::size_t i = 0; i < kSlickPools.size(); ++i)
            out[i] = DungeonKit::Advance(origin, facing + kSlickPools[i].offsetDeg * DungeonKit::kPi / 180.f,
                kSlickPools[i].distYd);
        return out;
    }
}

#endif
