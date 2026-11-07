/*
 * mod-dungeon-bosses, dungeon sets: the Haunted set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Haunted set
 * bonuses", approved 2026-11-06). The ids mirror apps/dbc-tools/source/items/haunted_set_bonuses.py (the
 * `haunted_set` spell reservation 205700-205899). The engine glue is haunted_set_bonuses.cpp.
 *
 * Pure: no engine headers, so the host test (tests/haunted_set_test.cpp) includes it.
 *
 * Every number a tooltip reads from the spell data stays there (durations, the debuff and buff amounts, the
 * spell_proc chances and internal cooldowns of the data procs). What lives here are the script numbers: the rolls a
 * script makes itself (Wraith Volley's two chances, Wraith Venom's and Grave Rot's), search radii and target counts,
 * the Lingering Death, Gathering Chorus, Unbroken Faith, Bone Ward and Deathless numbers. Each one is also printed by
 * its bonus tooltip as a literal (haunted_set_bonuses.py), and lib/test_haunted_set.py checks the two agree.
 */

#ifndef MOD_DUNGEON_BOSSES_HAUNTED_SET_LOGIC_H
#define MOD_DUNGEON_BOSSES_HAUNTED_SET_LOGIC_H

#include <cstdint>

namespace HauntedSet
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const
        {
            return id >= first && id <= last;
        }
    };

    // ids.yaml reservation `haunted_set`: the set bonuses take 205700-205799 (ten per set), 205800-205899 spare.
    IdSlice constexpr kSpellsHauntedSet{ 205700, 205899 };
    IdSlice constexpr kSpellsHauntedSetBonuses{ 205700, 205799 };

    enum HauntedSetSpells : std::uint32_t
    {
        // Magister's (Cloth Intellect, ItemSet 181)
        SPELL_WRAITH_VOLLEY             = 205700,   // 3 piece, the proc aura (spell_haunted_wraith_volley)
        SPELL_WRAITH_VOLLEY_BOLT        = 205701,   // the bolt (spell_haunted_wraith_volley_bolt)
        SPELL_SOUL_REND                 = 205702,   // 5 piece, a marker
        SPELL_SOUL_REND_DEBUFF          = 205703,   // +5% damage from the caster's spells
        // Devout (Cloth Spirit, 182)
        SPELL_SOUL_SHROUD               = 205710,   // 3 piece, data only
        SPELL_SOUL_SHROUD_BUFF          = 205711,
        SPELL_WRAITH_OF_SOLACE          = 205712,   // 5 piece (spell_haunted_wraith_of_solace)
        SPELL_WRAITH_OF_SOLACE_HEAL     = 205713,
        // Wildheart (Leather Spirit, 185)
        SPELL_LINGERING_DEATH           = 205720,   // 3 piece, a marker (HauntedSetSpellHooks)
        SPELL_GRAVE_BLOOM               = 205721,   // 5 piece (spell_haunted_grave_bloom)
        SPELL_GRAVE_BLOOM_HEAL          = 205722,
        SPELL_GRAVE_BLOOM_DAMAGE        = 205723,
        // The Elements (Mail Intellect, 187)
        SPELL_FROZEN_CHORUS             = 205730,   // 3 piece (spell_haunted_frozen_chorus)
        SPELL_FROZEN_CHORUS_DAMAGE      = 205731,   // (spell_haunted_frozen_chorus_payout)
        SPELL_FROZEN_CHORUS_HEAL        = 205732,   // (spell_haunted_frozen_chorus_payout)
        SPELL_GATHERING_CHORUS          = 205733,   // 5 piece, data only
        SPELL_GATHERING_CHORUS_STACK    = 205734,
        // Lightforge (Plate Intellect, 188)
        SPELL_UNBROKEN_FAITH            = 205740,   // 3 piece (spell_haunted_unbroken_faith)
        SPELL_UNBROKEN_FAITH_BUFF       = 205741,
        SPELL_SOUL_RELEASED             = 205742,   // 5 piece (spell_haunted_soul_released)
        SPELL_SOUL_RELEASED_HEAL        = 205743,
        SPELL_SOUL_RELEASED_DAMAGE      = 205744,
        // Valor (Plate Strength, 189)
        SPELL_BONE_SHATTER              = 205750,   // 3 piece (spell_haunted_bone_shatter)
        SPELL_BONE_SHATTER_BURST        = 205751,
        SPELL_BROKEN_BONES              = 205752,   // 5 piece, a marker
        SPELL_BROKEN_BONES_BUFF         = 205753,
        // Beaststalker's (Mail Agility, 186)
        SPELL_HAUNTING_MARK             = 205760,   // 3 piece, data only
        SPELL_HAUNTING_MARK_DEBUFF      = 205761,   // consumed by HauntedSetUnitHooks
        SPELL_GRASP_OF_THE_DEAD         = 205762,   // 5 piece (spell_haunted_grasp_of_the_dead)
        SPELL_GRASP_OF_THE_DEAD_MELEE   = 205763,
        SPELL_GRASP_OF_THE_DEAD_RANGED  = 205764,
        // Shadowcraft (Leather Agility, 184)
        SPELL_WRAITH_VENOM              = 205770,   // 3 piece, a marker (HauntedSetUnitHooks)
        SPELL_WRAITH_VENOM_DOT          = 205771,
        SPELL_GRAVE_ROT                 = 205772,   // 5 piece, a marker (HauntedSetUnitHooks)
        SPELL_GRAVE_ROT_STRIKE          = 205773,
        // Protector's (Leather Tank, 1000)
        SPELL_GRAVE_HIDE                = 205780,   // 3 piece, data only
        SPELL_BONE_WARD                 = 205781,   // 5 piece, data only
        SPELL_BONE_WARD_ABSORB          = 205782,   // (spell_haunted_bone_ward)
        // Shadowguard (Plate Tank, 1001)
        SPELL_SPIRIT_BULWARK            = 205790,   // 3 piece, data only
        SPELL_SPIRIT_BULWARK_HEAL       = 205791,
        SPELL_DEATHLESS                 = 205792,   // 5 piece (spell_haunted_deathless)
        SPELL_DEATHLESS_HOT             = 205793,
    };

    // Wraith Volley: 10% on a damaging spell cast, 4% on a periodic damage tick; up to 2 more enemies within 10 yd of
    // the target.
    std::int32_t constexpr kWraithVolleyCastPct = 10;
    std::int32_t constexpr kWraithVolleyTickPct = 4;
    std::uint32_t constexpr kWraithVolleyExtraTargets = 2;
    float constexpr kWraithVolleyRadius = 10.0f;
    // Wraith of Solace: the most injured ally within 30 yd other than the heal's target.
    float constexpr kSolaceRange = 30.0f;
    // Lingering Death: periodic damage and healing auras last 10% longer.
    std::int32_t constexpr kLingeringDeathPct = 10;
    // Grave Bloom: the second target within 15 yd of the first.
    float constexpr kGraveBloomRadius = 15.0f;
    // Gathering Chorus: the stack aura's amount is the 20% per stack; at most 5 stacks count.
    std::uint32_t constexpr kGatheringChorusMaxStacks = 5;
    // Unbroken Faith: holds above 80% mana.
    std::int32_t constexpr kUnbrokenFaithManaPct = 80;
    // Soul Released: the heal within 30 yd, the strike within 20 yd.
    float constexpr kSoulReleasedHealRange = 30.0f;
    float constexpr kSoulReleasedEnemyRange = 20.0f;
    // Wraith Venom: 8%, 2 s internal cooldown; Grave Rot: 6%, 3 s internal cooldown, +2 s on the wounds.
    std::int32_t constexpr kWraithVenomPct = 8;
    std::uint32_t constexpr kWraithVenomCooldownMs = 2000;
    std::int32_t constexpr kGraveRotPct = 6;
    std::uint32_t constexpr kGraveRotCooldownMs = 3000;
    std::int32_t constexpr kGraveRotExtendMs = 2000;
    // Grave Rot's extensions add up to at most 6 s per application of a damage-over-time effect (user ruling
    // 2026-11-06); a refresh or a new application starts a fresh 6 s.
    std::int32_t constexpr kGraveRotExtendCapMs = 6000;
    // Bone Ward: 3% of maximum health per stack.
    std::int32_t constexpr kBoneWardPctPerStack = 3;
    // Deathless: a hit that takes the wearer below 35% health.
    std::int32_t constexpr kDeathlessHealthPct = 35;

    // A script roll's chance: the flat chance times (1 + Proc Chance / 100), at most 100 (docs/Systems.md section 5,
    // the Rogue/Shaman RollProcChance copies).
    constexpr float ProcChancePct(float basePct, float procChancePct)
    {
        float const scaled = basePct * (1.0f + (procChancePct > 0.0f ? procChancePct : 0.0f) / 100.0f);
        return scaled > 100.0f ? 100.0f : (scaled < 0.0f ? 0.0f : scaled);
    }

    // Wraith Volley's chance for one event: a periodic damage tick, or a damaging spell cast.
    constexpr std::int32_t WraithVolleyBasePct(bool periodicTick)
    {
        return periodicTick ? kWraithVolleyTickPct : kWraithVolleyCastPct;
    }

    // Lingering Death: the lengthened maximum duration of a periodic damage or heal aura. A permanent (-1) or empty
    // aura keeps its own.
    constexpr std::int32_t LingeringDeathDuration(std::int32_t maxDurationMs)
    {
        if (maxDurationMs <= 0)
            return maxDurationMs;
        std::int64_t const longer = static_cast<std::int64_t>(maxDurationMs) * (100 + kLingeringDeathPct) / 100;
        return longer > 0x7FFFFFFF ? 0x7FFFFFFF : static_cast<std::int32_t>(longer);
    }

    // Frozen Chorus: the payout's multiplier in percent for `stacks` Gathering Chorus stacks of `pctPerStack` each.
    constexpr std::int32_t GatheringChorusPct(std::uint32_t stacks, std::int32_t pctPerStack)
    {
        std::uint32_t const counted = stacks > kGatheringChorusMaxStacks ? kGatheringChorusMaxStacks : stacks;
        return 100 + static_cast<std::int32_t>(counted) * (pctPerStack > 0 ? pctPerStack : 0);
    }

    // `amount` scaled by `pct` percent, rounded down, never negative.
    constexpr std::int32_t ScalePct(std::int32_t amount, std::int32_t pct)
    {
        if (amount <= 0 || pct <= 0)
            return 0;
        std::int64_t const scaled = static_cast<std::int64_t>(amount) * pct / 100;
        return scaled > 0x7FFFFFFF ? 0x7FFFFFFF : static_cast<std::int32_t>(scaled);
    }

    // Unbroken Faith holds while mana is strictly above 80% of the maximum (no mana pool: never).
    constexpr bool UnbrokenFaithHolds(std::uint32_t mana, std::uint32_t maxMana)
    {
        return maxMana > 0 && static_cast<std::uint64_t>(mana) * 100 >
            static_cast<std::uint64_t>(maxMana) * kUnbrokenFaithManaPct;
    }

    // Bone Ward: the absorb of `stacks` stacks for a wearer with `maxHealth`.
    constexpr std::int32_t BoneWardAmount(std::uint32_t maxHealth, std::uint32_t stacks)
    {
        std::uint64_t const amount = static_cast<std::uint64_t>(maxHealth) * kBoneWardPctPerStack *
            (stacks > 0 ? stacks : 1) / 100;
        return amount > 0x7FFFFFFF ? 0x7FFFFFFF : static_cast<std::int32_t>(amount);
    }

    // Deathless: the hit of `damage` that left the wearer at `healthAfter` (alive) took them from 35% or more to below
    // 35% of `maxHealth`.
    constexpr bool DeathlessCrossed(std::uint32_t healthAfter, std::uint32_t damage, std::uint32_t maxHealth)
    {
        if (!maxHealth || !healthAfter || !damage)
            return false;
        std::uint64_t const threshold = static_cast<std::uint64_t>(maxHealth) * kDeathlessHealthPct;
        std::uint64_t const after = static_cast<std::uint64_t>(healthAfter) * 100;
        std::uint64_t const before = (static_cast<std::uint64_t>(healthAfter) + damage) * 100;
        return after < threshold && before >= threshold;
    }

    // Grave Rot: what one application of a damage-over-time effect has already been extended by, and the shape of
    // that application when it was last extended (its apply time, its maximum duration after the extension, the
    // tick count of its periodic effect). A refresh resets the maximum duration and the tick count, a new
    // application the apply time, so either one is a fresh application with the whole cap again.
    struct GraveRotRecord
    {
        std::int64_t applyTime = 0;
        std::int32_t maxDurationAfter = 0;
        std::uint32_t tickNumber = 0;
        std::int32_t extendedMs = 0;
    };

    // The application's own extension so far: the record's when it is the same application, else 0.
    constexpr std::int32_t GraveRotExtendedSoFar(GraveRotRecord const* record, std::int64_t applyTime,
        std::int32_t maxDuration, std::uint32_t tickNumber)
    {
        if (!record || record->applyTime != applyTime || record->maxDurationAfter != maxDuration ||
            tickNumber < record->tickNumber)
            return 0;
        return record->extendedMs;
    }

    // The extension Grave Rot grants now: 2 s, cut to what is left of the 6 s cap (0 once it is spent).
    constexpr std::int32_t GraveRotGrantMs(std::int32_t extendedSoFar)
    {
        std::int32_t const left = kGraveRotExtendCapMs - (extendedSoFar > 0 ? extendedSoFar : 0);
        if (left <= 0)
            return 0;
        return left < kGraveRotExtendMs ? left : kGraveRotExtendMs;
    }

    // Lower health fraction first (a / maxA < b / maxB, cross-multiplied): the "most injured" ally.
    constexpr bool MoreInjured(std::uint32_t healthA, std::uint32_t maxA, std::uint32_t healthB, std::uint32_t maxB)
    {
        return static_cast<std::uint64_t>(healthA) * maxB < static_cast<std::uint64_t>(healthB) * maxA;
    }
}

#endif
