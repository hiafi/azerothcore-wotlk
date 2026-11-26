/*
 * mod-dungeon-bosses, Zul'Farrak D7: Hydromancer Velratha (7795) and Gahz'rilla (7273), the pure, host-testable part
 * (no engine headers). Build spec: docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha and Gahz'rilla" (GZ1-GZ14,
 * rulings 36-40); handoff sections 3.5 row D7, 3.6, 3.8 (the pool), 3.9 row 11, 7 #35-#40 and section 10 (#40 B: Spill
 * the Pool 4 s normal / 3 s heroic, Icicle 2.5 s). Tested by tests/zf_gahzrilla_test.cpp; apps/dbc-tools
 * lib/test_zul_farrak_gahzrilla.py pins the spell rows against this file.
 *
 *   PoolSpells / PoolTags   the spells (kSpellsPool 214110-214149) and the registry tags (G1's drill row 11: 31-34)
 *   Tune                    every number of the fight (rule 32), normal / heroic as NH<>
 *   Storm Builds            CycleMs / DischargeLandsAt / StaticChargeStacks: the Discharge clock (normal every 30 s;
 *                           heroic 20 s, 20 s, then 1.5 s shorter, never under the 3 s cast: section 7 #43 b A)
 *   Charged                 ChargedFactor / DischargePct: 40% plus 10% per stack on heroic, 50% in water on normal
 *   MeltFor                 what an Icicle or Freeze Solid that froze nothing does (Meltwater, the pool's shore spill)
 *   VelrathaClock           her beats: Spill the Pool on its grid (a must-land Arcane bar), the kickable heal, the
 *                           Frostbolt filler; nothing starts that would still run at the next Spill
 *   GahzrillaClock          his beats: the Discharge on Storm Builds' fixed clock (nothing a player does moves it),
 *                           then Call the Waters, Icicle, Freeze Solid; nothing starts that would run into the
 *                           Discharge's bar; the Slam (instant) and the hard mode's Icicle pace (GZ23)
 *   The pool strip          the sacred pool as a water strip (section 7 #37 A: never freezes, the bank counted),
 *                           ShoreSpotFor (a swimmer's Meltwater on heroic spills at the nearest shore point)
 *
 * Health is ZulFarrakRework.h Health (never restated here).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitWaterLogic.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace ZfPool
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsPool;

    // apps/dbc-tools source/npcs/zul_farrak/gahzrilla.py declares them (its test pins these ids and cast times).
    enum PoolSpells : std::uint32_t
    {
        SPELL_GZ_SPILL                  = kSpellSlice.first + 0,    // GZ1 normal: the 4 s Arcane bar (section 10)
        SPELL_GZ_SPILL_HEROIC           = kSpellSlice.first + 1,    // GZ1 heroic: the 3 s bar
        SPELL_GZ_SPILL_MARK             = kSpellSlice.first + 2,    // GZ1: the marked player's debuff (the look)
        SPELL_GZ_STATIC_CHARGE          = kSpellSlice.first + 3,    // GZ3: his meter, 10 stacks at the bar
        SPELL_GZ_DISCHARGE_BAR          = kSpellSlice.first + 4,    // GZ3: the 3 s Nature bar (not kickable)
        SPELL_GZ_DISCHARGE              = kSpellSlice.first + 5,    // GZ3: the hit (script base point, Nature)
        SPELL_GZ_STATIC_SHOCK           = kSpellSlice.first + 6,    // GZ3: the 2 s stun of anyone in water
        SPELL_GZ_CALL_THE_WATERS        = kSpellSlice.first + 7,    // GZ5 normal: the kickable 2.5 s Arcane cast
        SPELL_GZ_CALL_THE_WATERS_HEROIC = kSpellSlice.first + 8,    // GZ5 heroic: 2 s
        SPELL_GZ_ICICLE                 = kSpellSlice.first + 9,    // GZ6: copy of 11131, 2.5 s, no interrupt flags
        SPELL_GZ_FREEZE_SOLID           = kSpellSlice.first + 10,   // GZ7: copy of 11836, a 2 s Magic stun
        SPELL_GZ_FREEZE_LOOK            = kSpellSlice.first + 11,   // GZ8: the burst on a frozen puddle's disc
        SPELL_GZ_SLAM                   = kSpellSlice.first + 12,   // GZ11: copy of 11902 without the knock up
        SPELL_GZ_HEALING_WAVE           = kSpellSlice.first + 13,   // GZ9 normal: Velratha's 3 s self-heal, kickable
        SPELL_GZ_HEALING_WAVE_HEROIC    = kSpellSlice.first + 14,   // GZ9 heroic: 2 s
        SPELL_GZ_ACID_SPIT              = kSpellSlice.first + 15,   // GZ11: his swing at a target out of reach
        SPELL_GZ_CHARGED                = kSpellSlice.first + 16,   // GZ12 heroic: the personal stacks, no cap
        SPELL_GZ_CONDUCTIVE             = kSpellSlice.first + 17,   // GZ14 heroic: the Magic debuff, 10 s
        SPELL_GZ_CONDUCTIVE_ARC         = kSpellSlice.first + 18,   // GZ14: its arcs (script base point, Nature)
        SPELL_GZ_GONG_STRIKE            = kSpellSlice.first + 19,   // GZ10: the look of her strike on the gong
    };
    // The first id D7 leaves free (214130-214149: spare).
    inline constexpr std::uint32_t kFirstSpareSpell = kSpellSlice.first + 20;
    static_assert(kFirstSpareSpell <= kSpellSlice.last + 1);

    // Stock spells kept as cast (SP Build spec "Kept as cast").
    inline constexpr std::uint32_t SPELL_FROSTBOLT = 10180;     // Velratha's filler (live overlay: 30 yd, 9 s slow)

    // Registry tags: G1's zul-farrak-shapes row 11 uses 31 to 34 for the same shapes (the gate map reads 32, 34).
    enum PoolTags : std::uint32_t
    {
        TAG_GZ_WATER        = 31,   // GZ2 the puddles' avoid zones and the pool
        TAG_GZ_DISCHARGE    = 32,   // GZ3 the water under the Discharge's bar
        TAG_GZ_ICICLE       = 33,   // GZ6 / GZ7 the target's circle
        TAG_GZ_ICICLE_DROP  = 34,   // GZ6 the target's carry into a puddle (the drill judges it as its own tag)
        TAG_GZ_SPILL        = 41,   // GZ1 the marked player's 8 yd circle (35-40 are the hard mode's)
        TAG_GZ_CONDUCTIVE   = 42,   // GZ14 the carriers' 6 yd rings
    };

    // The water field's discs (WP-V's _visuals.py GZ_WATER_DISC / GZ_ICE_DISC / GZ_STORM_DISC and DISC_QUAD_RADIUS,
    // patch-M creature displays; lib/test_zul_farrak_gahzrilla.py pins them against _visuals.py).
    inline constexpr std::uint32_t kDisplayWaterDisc = 90830;
    inline constexpr std::uint32_t kDisplayIceDisc = 90831;
    inline constexpr std::uint32_t kDisplayStormDisc = 90832;
    inline constexpr float kDiscYdPerScale = 4.8f;

    // WaterField SheetRules::kind of D7's sheets (the hard mode packages use 10 and up).
    enum SheetKind : std::uint32_t
    {
        SHEET_SPILL     = 1,
        SHEET_CALL      = 2,
        SHEET_MELTWATER = 3,
        SHEET_POOL      = 4,
        SHEET_GM        = 5,
    };

    // The descriptor's priorities: the self-heal before Call the Waters (both on the interrupt list); Conductive is
    // the answer (dispel first), Freeze Solid's stun and Frostbolt's slow are rewards.
    inline constexpr std::uint8_t kHealKickPriority = 2;
    inline constexpr std::uint8_t kCallKickPriority = 1;
    inline constexpr std::uint8_t kConductiveDispelPriority = 3;
    inline constexpr std::uint8_t kFreezeSolidDispelPriority = 2;
    inline constexpr std::uint8_t kFrostboltDispelPriority = 1;

    // Text groups (0-based, rule 34). Velratha 7795 and Gahz'rilla 7273 have no stock lines.
    enum PoolTexts : std::uint8_t
    {
        YELL_VELRATHA_AGGRO     = 0,    // "The sacred pool is not for outlanders!"
        YELL_VELRATHA_GONG      = 1,    // "Rise, Gahz'rilla! The waters are yours!" (GZ10)
        EMOTE_GAHZRILLA_CHARGE  = 0,    // "%s's scales crackle with building charge!" (GZ3, each bar)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (rule 32): every percent and timer of the fight. Damage percents are of the reference row (RefFlatOn: the
    // tank row on the tank); normal flat values are the stock spells' at level 46 (handoff section 3.6).
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // GZ1 Spill the Pool (section 10, #40 B: 4 s normal, 3 s heroic).
        inline constexpr NH<std::uint32_t> kSpillCastMs{ 4000, 3000 };
        inline constexpr NH<std::uint32_t> kSpillFirstMs{ 5000, 5000 };
        inline constexpr NH<std::uint32_t> kSpillEveryMs{ 10000, 8000 };
        inline constexpr float kPuddleRadiusYd = 8.f;           // GZ1, GZ5, GZ13: every new puddle

        // GZ9 Healing Wave (her self-heal, the interrupt).
        inline constexpr NH<std::uint32_t> kHealCastMs{ 3000, 2000 };
        inline constexpr NH<float> kHealPct{ 10.f, 20.f };      // of her maximum health
        inline constexpr std::uint32_t kHealFirstMs = 12000;
        inline constexpr std::uint32_t kHealEveryMs = 15000;

        // GZ11 Frostbolt 10180 (stock, kept): her filler, 3 to 4 s apart.
        inline constexpr std::uint32_t kFrostboltCastMs = 3000;
        inline constexpr std::uint32_t kFrostboltFirstMs = 1000;
        inline constexpr std::uint32_t kFrostboltEveryMinMs = 3000;
        inline constexpr std::uint32_t kFrostboltEveryMaxMs = 4000;
        inline constexpr float kFrostboltRangeYd = 30.f;        // the live overlay's range

        // GZ10 the gong: at her 30% she runs to it (about 61 yd), strikes it, and fights on from its water patch.
        inline constexpr float kGongHealthPct = 30.f;
        inline constexpr float kGongStandOffYd = 2.5f;          // her strike spot, toward the shore from the gong
        inline constexpr std::uint32_t kGongRunTimeoutMs = 15000;   // a run that never arrives strikes from there

        // Gahz'rilla's rise (section 7 #35 A): from the stock summon point to (1677, 1167), untargetable until there.
        inline constexpr std::uint32_t kRiseTimeoutMs = 15000;  // not ashore by then: put there, and he fights

        // GZ3 Static Discharge and Storm Builds.
        inline constexpr std::uint32_t kDischargeCastMs = 3000;
        inline constexpr std::uint32_t kNormalCycleMs = 30000;
        inline constexpr std::uint32_t kHeroicFirstCyclesMs = 20000;
        inline constexpr std::uint32_t kHeroicCycleStepMs = 1500;
        inline constexpr std::uint32_t kStaticChargeMax = 10;
        inline constexpr float kDischargeWaterPct = 50.f;       // normal, in water only
        inline constexpr float kDischargeHeroicPct = 40.f;      // heroic, everyone, raised by Charged
        inline constexpr std::uint32_t kStaticShockMs = 2000;   // the stun of anyone in water

        // GZ4 Rising Water: every water puddle at each Discharge; no cap (heroic: ruling 38).
        inline constexpr NH<float> kRisingWaterYd{ 2.f, 3.f };

        // GZ5 Call the Waters.
        inline constexpr NH<std::uint32_t> kCallCastMs{ 2500, 2000 };
        inline constexpr NH<std::uint32_t> kCallFirstMs{ 10000, 10000 };
        inline constexpr NH<std::uint32_t> kCallEveryMs{ 15000, 12000 };
        inline constexpr NH<std::uint32_t> kCallPuddles{ 2, 3 };
        inline constexpr float kCallHeroicGrowYd = 2.f;         // heroic: every water puddle when it lands

        // GZ6 Icicle (section 10: 2.5 s on both difficulties).
        inline constexpr std::uint32_t kIcicleCastMs = 2500;
        inline constexpr std::uint32_t kIcicleFirstMs = 6000;
        inline constexpr std::uint32_t kIcicleEveryMs = 10000;
        inline constexpr std::uint32_t kIcicleMinDamage = 355; // stock 11131 at 46 (section 3.6), normal
        inline constexpr std::uint32_t kIcicleMaxDamage = 405;
        inline constexpr float kIcicleHeroicPct = 14.f;         // the stock hit's share of the normal row, at 60
        inline constexpr float kIcicleRangeYd = 40.f;           // stock: a random player within 40 yd

        // GZ7 Freeze Solid.
        inline constexpr std::uint32_t kFreezeSolidCastMs = 2500;
        inline constexpr std::uint32_t kFreezeSolidFirstMs = 15000;
        inline constexpr std::uint32_t kFreezeSolidEveryMs = 22000;
        inline constexpr std::uint32_t kFreezeSolidStunMs = 2000;
        inline constexpr std::uint32_t kFreezeSolidDamage = 115;   // the stock tick (108-122) once, normal
        inline constexpr float kFreezeSolidHeroicPct = 4.5f;
        inline constexpr float kFreezeSolidReachYd = 8.f;      // to a puddle's edge (KT Q3, ruled as built)
        inline constexpr float kFreezeSolidRangeYd = 30.f;

        // GZ8 Ice: thaws back to water at the size it froze.
        inline constexpr NH<std::uint32_t> kThawMs{ 45000, 30000 };

        // GZ11 Slam: everyone within 20 yd, 50% weapon damage (the spell), no knock up.
        inline constexpr std::uint32_t kSlamFirstMs = 15000;
        inline constexpr std::uint32_t kSlamEveryMinMs = 25000;
        inline constexpr std::uint32_t kSlamEveryMaxMs = 35000;
        // GZ11 Acid Spit: his swing at a target out of his melee reach, as Nature (armor does not help).
        inline constexpr float kAcidSpitMeleePct = 150.f;
        inline constexpr float kAcidSpitRangeYd = 40.f;

        // GZ12 Charged (heroic): one stack a second in water, no cap, +10% Discharge damage a stack.
        inline constexpr std::uint32_t kChargedTickMs = 1000;
        inline constexpr float kChargedPerStackPct = 10.f;
        inline constexpr std::uint32_t kChargedMaxStacks = 999;     // the spell's CumulativeAura: out of reach

        // GZ13 Meltwater (heroic): a freeze that froze no water spills a puddle of kPuddleRadiusYd.
        // GZ14 Conductive (heroic).
        inline constexpr std::uint32_t kConductiveMs = 10000;
        inline constexpr std::uint32_t kConductiveTickMs = 2000;
        inline constexpr float kConductivePct = 25.f;
        inline constexpr float kConductiveArcYd = 6.f;

        // Bots: the Icicle target may stand in the water it baits this long before the landing (FF B GZ6).
        inline constexpr std::uint32_t kBaitMaxDwellMs = 800;

        // A cast that would still run this close to a must-land bar does not start (update ticks).
        inline constexpr std::uint32_t kBeatMarginMs = 250;
        // A cast the engine refused (a school lockout after a kick) is tried again this soon.
        inline constexpr std::uint32_t kRetryMs = 500;

        // The warning floor (section 3.5 rule 32, SYS 4): every hit's warning is at least 1.5 s.
        static_assert(kSpillCastMs.normal >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kSpillCastMs.heroic >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kDischargeCastMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kCallCastMs.heroic >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kIcicleCastMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kFreezeSolidCastMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kHealCastMs.heroic >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kConductiveTickMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kStaticShockMs <= 2000, "SYS 4: a stun of 2 s at most");
        static_assert(kFreezeSolidStunMs <= 2000, "SYS 4: a stun of 2 s at most");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Storm Builds (GZ3): the Discharge clock, from Gahz'rilla's arrival
    // ----------------------------------------------------------------------------------------------------------------

    // The `n`-th charge cycle (1-based), from the last landing (or his arrival) to the next landing.
    constexpr std::uint32_t CycleMs(bool heroic, std::uint32_t n)
    {
        if (!heroic)
            return Tune::kNormalCycleMs;
        if (n <= 2)
            return Tune::kHeroicFirstCyclesMs;
        std::int64_t const v = std::int64_t(Tune::kHeroicFirstCyclesMs)
            - std::int64_t(Tune::kHeroicCycleStepMs) * std::int64_t(n - 2);
        return std::uint32_t(std::max<std::int64_t>(v, Tune::kDischargeCastMs));     // section 7 #43 b A
    }

    // When the `n`-th Discharge lands (ms after his arrival).
    constexpr std::uint64_t DischargeLandsAt(bool heroic, std::uint32_t n)
    {
        std::uint64_t at = 0;
        for (std::uint32_t i = 1; i <= n; ++i)
            at += CycleMs(heroic, i);
        return at;
    }

    // SP's heroic table and section 3.7's tail, pinned.
    static_assert(DischargeLandsAt(true, 1) == 20000 && DischargeLandsAt(true, 2) == 40000);
    static_assert(DischargeLandsAt(true, 3) == 58500 && DischargeLandsAt(true, 4) == 75500);
    static_assert(DischargeLandsAt(true, 5) == 91000 && DischargeLandsAt(true, 10) == 146000);
    static_assert(DischargeLandsAt(true, 13) == 161000 && DischargeLandsAt(true, 14) == 164000);
    static_assert(DischargeLandsAt(false, 3) == 90000);

    // The meter on him `elapsed` ms into a cycle of `cycle` ms: full (10) when the bar starts.
    constexpr std::uint32_t StaticChargeStacks(std::uint64_t elapsed, std::uint32_t cycle)
    {
        if (cycle <= Tune::kDischargeCastMs)
            return Tune::kStaticChargeMax;
        std::uint64_t const charge = cycle - Tune::kDischargeCastMs;
        std::uint64_t const stacks = elapsed * Tune::kStaticChargeMax / charge;
        return std::uint32_t(std::min<std::uint64_t>(stacks, Tune::kStaticChargeMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Charged (GZ12) and the Discharge's damage (GZ3)
    // ----------------------------------------------------------------------------------------------------------------

    constexpr float ChargedFactor(std::uint32_t stacks)
    {
        return 1.f + Tune::kChargedPerStackPct / 100.f * float(stacks);
    }

    // The percent of the reference row a Discharge deals to one target; 0: none (normal, dry ground).
    constexpr float DischargePct(bool heroic, bool inWater, std::uint32_t charged)
    {
        if (!heroic)
            return inWater ? Tune::kDischargeWaterPct : 0.f;
        return Tune::kDischargeHeroicPct * ChargedFactor(charged);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // What a freeze does when it froze nothing (GZ13, section 7 #37 A)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Melt : std::uint8_t
    {
        None,           // something froze, or normal
        AtTarget,       // heroic Meltwater: a puddle under the target
        AtShore,        // heroic, the target swims in the pool: the puddle at the nearest shore point
    };

    inline Melt MeltFor(bool heroic, DungeonKit::FreezeResult const& r)
    {
        if (!heroic || !r.frozen.empty())
            return Melt::None;
        return r.unfreezable ? Melt::AtShore : Melt::AtTarget;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The sacred pool as a water strip (section 7 #37 A; [navmesh estimate], fitted to kPoolWaterPolygon: its long
    // axis at 43.7 degrees, 51 yd, 8.2 to 10.0 yd either side). The strip's half width counts the 60 degree bank
    // (the dry floor starts a median 3.5 yd from the water): 7.5 + 4 (KT's default). Its ends run 3 yd past the
    // water. Never freezes, never grows; a swimmer's Icicle freezes nothing.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kPoolAxisFrom{ 1646.9f, 1169.9f };
    inline constexpr Vec2 kPoolAxisTo{ 1688.2f, 1209.3f };
    inline constexpr float kPoolHalfWidthYd = 11.5f;
    inline constexpr float kPoolSurfaceZ = 9.0f;
    inline constexpr float kPoolZBandYd = 12.f;         // the surface to the bed (-2.9) and the shore above it
    inline constexpr float kShoreSpillOutYd = 3.f;      // a shore spill lands this far past the strip's edge

    // The pool's sheet rules (the host test and the engine build it the same way).
    inline DungeonKit::SheetRules PoolRules()
    {
        DungeonKit::SheetRules rules;
        rules.canFreeze = false;
        rules.grows = false;
        rules.thawMs = 0;
        rules.zBand = kPoolZBandYd;
        rules.kind = SHEET_POOL;
        return rules;
    }

    // A puddle's rules (GZ1, GZ5, GZ13): freezes, grows with no cap, thaws back to water.
    inline DungeonKit::SheetRules PuddleRules(bool heroic, std::uint32_t kind)
    {
        DungeonKit::SheetRules rules;
        rules.thawMs = Tune::kThawMs(heroic);
        rules.kind = kind;
        return rules;
    }

    // The nearest shore point to `p` (a swimmer): straight across the strip's long side `p` is on, kShoreSpillOutYd
    // past its edge.
    inline Vec2 ShoreSpotFor(Vec2 p)
    {
        float const len = DungeonKit::Distance(kPoolAxisFrom, kPoolAxisTo);
        float const ux = (kPoolAxisTo.x - kPoolAxisFrom.x) / len;
        float const uy = (kPoolAxisTo.y - kPoolAxisFrom.y) / len;
        float const along = std::clamp((p.x - kPoolAxisFrom.x) * ux + (p.y - kPoolAxisFrom.y) * uy, 0.f, len);
        float const side = -(p.x - kPoolAxisFrom.x) * uy + (p.y - kPoolAxisFrom.y) * ux;
        float const sign = side >= 0.f ? 1.f : -1.f;
        float const out = kPoolHalfWidthYd + kShoreSpillOutYd;
        Vec2 const onAxis{ kPoolAxisFrom.x + ux * along, kPoolAxisFrom.y + uy * along };
        return { onAxis.x - uy * out * sign, onAxis.y + ux * out * sign };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats. A grid beat keeps its pace after a late cast: the next is max(due + every, now + every / 2) (LESSONS
    // L8), so one long hold never makes two casts back to back nor drifts the grid.
    // ----------------------------------------------------------------------------------------------------------------

    struct Beat
    {
        std::uint64_t due = std::numeric_limits<std::uint64_t>::max();
        std::uint64_t heldUntil = 0;
        std::uint32_t every = 0;

        void Start(std::uint32_t firstMs, std::uint32_t everyMs, std::uint64_t now = 0)
        {
            due = now + firstMs;
            heldUntil = 0;
            every = everyMs;
        }
        bool Running() const { return every != 0; }
        bool Due(std::uint64_t now) const { return Running() && now >= due && now >= heldUntil; }
        std::uint64_t In(std::uint64_t now) const { return !Running() ? 0 : (due > now ? due - now : 0); }
        // Done now; `everyMs` (0: keep the last) for a beat with a random pace (Frostbolt, the Slam).
        void Done(std::uint64_t now, std::uint32_t everyMs = 0)
        {
            if (everyMs)
                every = everyMs;
            heldUntil = 0;
            if (!Running())
                return;
            due = std::max(due + every, now + every / 2);
        }
        void Retry(std::uint64_t now) { heldUntil = now + Tune::kRetryMs; }
    };

    // ---- Velratha (GZ1, GZ9, GZ11) ----------------------------------------------------------------------------------

    enum class VAct : std::uint8_t
    {
        None,
        Spill,
        Heal,
        Frostbolt,
    };

    // Spill the Pool is never late (its puddles are phase 2's stage): nothing starts that would still be casting at
    // its beat. The heal waits for room; the Frostbolt is a filler that waits too.
    class VelrathaClock
    {
    public:
        void Start(bool heroic)
        {
            *this = VelrathaClock();
            _heroic = heroic;
            _spill.Start(Tune::kSpillFirstMs(heroic), Tune::kSpillEveryMs(heroic));
            _heal.Start(Tune::kHealFirstMs, Tune::kHealEveryMs);
            _frostbolt.Start(Tune::kFrostboltFirstMs, Tune::kFrostboltEveryMinMs);
        }
        void Stop() { *this = VelrathaClock(); }

        std::uint64_t Now() const { return _now; }
        void Advance(std::uint32_t diff) { _now += diff; }
        bool Running() const { return _spill.Running(); }

        // The act to start now, if any (she is not casting).
        VAct Next() const
        {
            if (_spill.Due(_now))
                return VAct::Spill;
            if (_heal.Due(_now) && Fits(Tune::kHealCastMs(_heroic)))
                return VAct::Heal;
            if (_frostbolt.Due(_now) && Fits(Tune::kFrostboltCastMs))
                return VAct::Frostbolt;
            return VAct::None;
        }

        // `everyMs` for the Frostbolt's random 3 to 4 s.
        void Done(VAct act, std::uint32_t everyMs = 0)
        {
            if (Beat* b = Of(act))
                b->Done(_now, everyMs);
        }
        void Retry(VAct act)
        {
            if (Beat* b = Of(act))
                b->Retry(_now);
        }
        std::uint64_t In(VAct act) const
        {
            Beat const* b = Of(act);
            return b ? b->In(_now) : 0;
        }

        // A cast of `castMs` started now ends before the next Spill's beat (with the margin).
        bool Fits(std::uint32_t castMs) const
        {
            return _now + castMs + Tune::kBeatMarginMs <= _spill.due;
        }

    private:
        Beat const* Of(VAct act) const
        {
            switch (act)
            {
                case VAct::Spill:
                    return &_spill;
                case VAct::Heal:
                    return &_heal;
                case VAct::Frostbolt:
                    return &_frostbolt;
                case VAct::None:
                    break;
            }
            return nullptr;
        }
        Beat* Of(VAct act) { return const_cast<Beat*>(static_cast<VelrathaClock const*>(this)->Of(act)); }

        std::uint64_t _now = 0;
        bool _heroic = false;
        Beat _spill;
        Beat _heal;
        Beat _frostbolt;
    };

    // GZ10: she strikes the gong at her 30% (once a pull).
    constexpr bool GongDue(float healthPct, bool struck)
    {
        return !struck && healthPct <= Tune::kGongHealthPct;
    }

    // ---- Gahz'rilla (GZ3, GZ5, GZ6, GZ7, GZ11) ----------------------------------------------------------------------

    enum class GAct : std::uint8_t
    {
        None,
        Discharge,
        CallTheWaters,
        Icicle,
        FreezeSolid,
        Slam,
    };

    // The Discharge's bar starts exactly kDischargeCastMs before its landing (Storm Builds: nothing moves it); every
    // other cast starts only when it ends before that bar (with the margin), else it waits until after it. The Slam is
    // instant and fires between casts.
    class GahzrillaClock
    {
    public:
        void Start(bool heroic)
        {
            *this = GahzrillaClock();
            _heroic = heroic;
            _running = true;
            _call.Start(Tune::kCallFirstMs(heroic), Tune::kCallEveryMs(heroic));
            _icicle.Start(Tune::kIcicleFirstMs, Tune::kIcicleEveryMs);
            _freeze.Start(Tune::kFreezeSolidFirstMs, Tune::kFreezeSolidEveryMs);
            _slam.Start(Tune::kSlamFirstMs, Tune::kSlamEveryMinMs);
        }
        void Stop() { *this = GahzrillaClock(); }

        bool Running() const { return _running; }
        bool Heroic() const { return _heroic; }
        std::uint64_t Now() const { return _now; }
        void Advance(std::uint32_t diff) { _now += diff; }

        // The cycle in play (1-based) and the Discharges landed so far.
        std::uint32_t Cycle() const { return _cycle; }
        std::uint32_t Landed() const { return _cycle - 1; }
        std::uint64_t LandsAt() const { return _cycleStart + CycleMs(_heroic, _cycle); }
        std::uint64_t BarAt() const { return LandsAt() - Tune::kDischargeCastMs; }
        std::uint32_t Stacks() const
        {
            return StaticChargeStacks(_now > _cycleStart ? _now - _cycleStart : 0, CycleMs(_heroic, _cycle));
        }

        // The act to start now (he is not casting). The Discharge is due from its bar's moment on, whatever else.
        GAct Next() const
        {
            if (!_running || _barStarted)
                return GAct::None;
            if (_now >= BarAt())
                return GAct::Discharge;
            if (_call.Due(_now) && Fits(Tune::kCallCastMs(_heroic)))
                return GAct::CallTheWaters;
            // Freeze Solid before Icicle: the Deluge's 5 s Icicle is always due, so the other order never froze (D7Hb)
            if (_freeze.Due(_now) && Fits(Tune::kFreezeSolidCastMs))
                return GAct::FreezeSolid;
            if (_icicle.Due(_now) && Fits(Tune::kIcicleCastMs))
                return GAct::Icicle;
            if (_slam.Due(_now))
                return GAct::Slam;
            return GAct::None;
        }

        bool Fits(std::uint32_t castMs) const
        {
            return _now + castMs + Tune::kBeatMarginMs <= BarAt();
        }

        // The Discharge's bar started (at BarAt or later); it lands at the bar's end.
        void BarStarted() { _barStarted = true; }
        bool BarRunning() const { return _barStarted; }
        // The bar's landing: the next cycle runs from the planned landing (the clock never drifts).
        void MarkLanded()
        {
            _cycleStart = LandsAt();
            ++_cycle;
            _barStarted = false;
        }

        void Done(GAct act, std::uint32_t everyMs = 0)
        {
            if (Beat* b = Of(act))
                b->Done(_now, everyMs);
        }
        void Retry(GAct act)
        {
            if (Beat* b = Of(act))
                b->Retry(_now);
        }
        std::uint64_t In(GAct act) const
        {
            if (act == GAct::Discharge)
                return BarAt() > _now ? BarAt() - _now : 0;
            Beat const* b = Of(act);
            return b ? b->In(_now) : 0;
        }

        // The hard mode's Deluge (GZ23): Icicle every `everyMs` from now (0: back to the normal pace).
        void SetIcicleEvery(std::uint32_t everyMs)
        {
            std::uint32_t const every = everyMs ? everyMs : Tune::kIcicleEveryMs;
            _icicle.every = every;
            _icicle.due = std::min(_icicle.due, _now + every);
        }
        std::uint32_t IcicleEvery() const { return _icicle.every; }

    private:
        Beat const* Of(GAct act) const
        {
            switch (act)
            {
                case GAct::CallTheWaters:
                    return &_call;
                case GAct::Icicle:
                    return &_icicle;
                case GAct::FreezeSolid:
                    return &_freeze;
                case GAct::Slam:
                    return &_slam;
                case GAct::Discharge:
                case GAct::None:
                    break;
            }
            return nullptr;
        }
        Beat* Of(GAct act) { return const_cast<Beat*>(static_cast<GahzrillaClock const*>(this)->Of(act)); }

        std::uint64_t _now = 0;
        std::uint64_t _cycleStart = 0;
        std::uint32_t _cycle = 1;
        bool _heroic = false;
        bool _running = false;
        bool _barStarted = false;
        Beat _call;
        Beat _icicle;
        Beat _freeze;
        Beat _slam;
    };
}

#endif
