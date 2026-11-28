/*
 * mod-dungeon-bosses, dungeon sets: the Molten set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Molten set
 * bonuses", approved 2026-11-06). The ids mirror apps/dbc-tools/source/items/molten_set_bonuses.py (the `molten_set`
 * spell reservation 206900-206999, ten per set). The engine glue is molten_set_bonuses.cpp.
 *
 * Pure: no engine headers, so the host test (tests/molten_set_test.cpp) includes it.
 *
 * Heat, the family rule: a stacking buff whose stacks are the count; a critical strike or heal gives 2 instead of 1
 * (Darkmantle: 1 per combo point, 1 more on a crit); the gain that reaches the set's count erupts and resets Heat to 0.
 * Heat is a count, never a chance (no roll, no Proc Chance). Every number a tooltip reads from the spell data stays
 * there (durations, buff amounts); the counts, radii, target counts and the Mending Flame numbers live here and are
 * printed by the bonus tooltips as literals (molten_set_bonuses.py); lib/test_molten_set.py checks the two agree, and
 * that the Cooldown Haste rule below matches Player.cpp's.
 */

#ifndef MOD_DUNGEON_BOSSES_MOLTEN_SET_LOGIC_H
#define MOD_DUNGEON_BOSSES_MOLTEN_SET_LOGIC_H

#include <cstdint>

namespace MoltenSet
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

    // ids.yaml reservation `molten_set`: spells 206900-206999, ten per set.
    IdSlice constexpr kSpellsMoltenSet{ 206900, 206999 };

    // The ten sets in id order: set k owns 206900 + 10k .. 206909 + 10k.
    enum class Archetype : std::uint8_t
    {
        Sorcerers = 0,      // Cloth Intellect, ItemSet 517
        Virtuous,           // Cloth Spirit, 514
        Feralheart,         // Leather Spirit, 513
        FiveThunders,       // Mail Intellect, 519
        Soulforge,          // Plate Intellect, 516
        Heroism,            // Plate Strength, 511
        Beastmasters,       // Mail Agility, 515
        Darkmantle,         // Leather Agility, 512
        Guardians,          // Leather Tank, 1002
        Impenetrable,       // Plate Tank, 1003
        Count
    };

    std::uint32_t constexpr kArchetypeCount = static_cast<std::uint32_t>(Archetype::Count);
    std::uint32_t constexpr kIdsPerSet = 10;
    // Within a set's ten ids.
    std::uint32_t constexpr kOffsetThreePiece = 0;
    std::uint32_t constexpr kOffsetFivePiece = 1;
    std::uint32_t constexpr kOffsetHeat = 2;

    enum MoltenSetSpells : std::uint32_t
    {
        // Sorcerer's (Cloth Intellect, ItemSet 517), Heat 10
        SPELL_STOKED_FLAME              = 206900,   // 3 piece (spell_molten_heat)
        SPELL_FLARE_UP                  = 206901,   // 5 piece (spell_molten_cooldown_heat)
        SPELL_STOKED_FLAME_HEAT         = 206902,
        SPELL_STOKED_FLAME_ERUPTION     = 206903,   // (spell_molten_eruption_in_combat)
        // Virtuous (Cloth Spirit, 514), Heat 8
        SPELL_CAUTERIZE                 = 206910,   // 3 piece (spell_molten_heat)
        SPELL_MENDING_FLAME             = 206911,   // 5 piece, a marker
        SPELL_CAUTERIZE_HEAT            = 206912,
        SPELL_CAUTERIZE_HEAL            = 206913,   // (spell_molten_cauterize)
        // Feralheart (Leather Spirit, 513), Heat 8
        SPELL_EMBER_BLOOM               = 206920,   // 3 piece (spell_molten_heat)
        SPELL_FANNED_EMBERS             = 206921,   // 5 piece, a marker
        SPELL_EMBER_BLOOM_HEAT          = 206922,
        SPELL_EMBER_BLOOM_READY         = 206923,   // (spell_molten_ember_bloom)
        SPELL_FANNED_EMBERS_BUFF        = 206924,   // data only (one charge)
        // The Five Thunders (Mail Intellect, 519), Heat 10
        SPELL_MOLTEN_THUNDER            = 206930,   // 3 piece (spell_molten_heat)
        SPELL_THUNDERHEAD               = 206931,   // 5 piece (spell_molten_cooldown_heat)
        SPELL_MOLTEN_THUNDER_HEAT       = 206932,
        SPELL_MOLTEN_THUNDER_DAMAGE     = 206933,   // (spell_molten_eruption_in_combat)
        SPELL_MOLTEN_THUNDER_HEAL       = 206934,
        // Soulforge (Plate Intellect, 516), Heat 8
        SPELL_HALLOWED_FLAME            = 206940,   // 3 piece (spell_molten_heat)
        SPELL_TENDED_FLAME              = 206941,   // 5 piece, a marker
        SPELL_HALLOWED_FLAME_HEAT       = 206942,
        SPELL_HALLOWED_FLAME_HOT        = 206943,   // (spell_molten_hallowed_flame)
        SPELL_HALLOWED_FLAME_DOT        = 206944,   // (spell_molten_hallowed_flame)
        SPELL_TENDED_FLAME_MANA         = 206945,
        // Heroism (Plate Strength, 511), Heat 10
        SPELL_MOLTEN_EDGE               = 206950,   // 3 piece (spell_molten_heat)
        SPELL_STOKE_THE_FORGE           = 206951,   // 5 piece (spell_molten_cooldown_heat)
        SPELL_MOLTEN_EDGE_HEAT          = 206952,
        SPELL_MOLTEN_EDGE_SEAR          = 206953,
        // Beastmaster's (Mail Agility, 515), Heat 8
        SPELL_OBSIDIAN_SHARD            = 206960,   // 3 piece (spell_molten_heat)
        SPELL_BURNING_SHARDS            = 206961,   // 5 piece, a marker
        SPELL_OBSIDIAN_SHARD_HEAT       = 206962,
        SPELL_OBSIDIAN_SHARD_MELEE      = 206963,   // (spell_molten_obsidian_shard)
        SPELL_OBSIDIAN_SHARD_RANGED     = 206964,   // (spell_molten_obsidian_shard)
        SPELL_BURNING_SHARDS_MELEE      = 206965,
        SPELL_BURNING_SHARDS_RANGED     = 206966,
        // Darkmantle (Leather Agility, 512), Heat 10
        SPELL_SLAG_BURST                = 206970,   // 3 piece (spell_molten_heat)
        SPELL_REKINDLE                  = 206971,   // 5 piece, a marker
        SPELL_SLAG_BURST_HEAT           = 206972,
        SPELL_SLAG_BURST_ERUPTION       = 206973,   // (spell_molten_eruption_in_combat)
        SPELL_REKINDLE_BUFF             = 206974,   // (spell_molten_rekindle)
        // Guardian's (Leather Tank, 1002), Heat 10
        SPELL_SCORCHING_HIDE            = 206980,   // 3 piece (spell_molten_heat)
        SPELL_TEMPERED_HIDE             = 206981,   // 5 piece, a marker
        SPELL_SCORCHING_HIDE_HEAT       = 206982,
        SPELL_SCORCHING_HIDE_ERUPTION   = 206983,   // (spell_molten_scorching_hide)
        SPELL_TEMPERED_HIDE_BUFF        = 206984,
        // Impenetrable (Plate Tank, 1003), Heat 10
        SPELL_MOLTEN_PLATE              = 206990,   // 3 piece (spell_molten_heat)
        SPELL_BANKED_COALS              = 206991,   // 5 piece (spell_molten_cooldown_heat)
        SPELL_MOLTEN_PLATE_HEAT         = 206992,
        SPELL_MOLTEN_PLATE_BUFF         = 206993,
    };

    // The Heat count of each set, in Archetype order.
    std::uint32_t constexpr kHeatCount[kArchetypeCount] = { 10, 8, 8, 10, 8, 10, 8, 10, 10, 10 };
    // A critical strike or heal gives this much (Darkmantle: 1 more than its combo points).
    std::uint32_t constexpr kCritHeat = 2;

    // Cauterize: the healed target and up to 3 more allies within 10 yd of it. Mending Flame: +50% below 50% health.
    std::uint32_t constexpr kCauterizeExtraAllies = 3;
    float constexpr kCauterizeRadius = 10.0f;
    std::int32_t constexpr kMendingFlameHealthPct = 50;
    std::int32_t constexpr kMendingFlameBonusPct = 50;
    // Ember Bloom: two ticks of the bloomed spell.
    std::uint32_t constexpr kEmberBloomTicks = 2;
    // Molten Thunder: within 8 yd of the target; the heal reaches the target and up to 4 more allies.
    float constexpr kMoltenThunderRadius = 8.0f;
    std::uint32_t constexpr kMoltenThunderExtraAllies = 4;
    // The cooldown hooks' Heat: Thunderhead 5, Stoke the Forge 10, Banked Coals 10 (Flare-up erupts outright).
    std::uint32_t constexpr kThunderheadHeat = 5;
    std::uint32_t constexpr kStokeTheForgeHeat = 10;
    std::uint32_t constexpr kBankedCoalsHeat = 10;
    // Obsidian Shard: the bounce reaches the nearest other enemy within 10 yd of the target.
    float constexpr kObsidianShardBounceRadius = 10.0f;
    // Rekindle: the extra combo point.
    std::int32_t constexpr kRekindleComboPoints = 1;

    // The cooldown hooks' trigger rule: an unmodified base RecoveryTime or CategoryRecoveryTime of 30 s or more, or
    // the Molten trigger allow list, never the deny list. The floor and the deny list mirror Player.cpp's Cooldown
    // Haste rule (CUSTOM_COOLDOWN_HASTE_MIN_BASE_COOLDOWN_MS, _DENY_LIST; lib/test_molten_set.py checks they agree).
    // kMoltenCooldownTriggerAllowList is deliberately NOT the Cooldown Haste allow list: the short damage cooldowns
    // gear-scaling GS2 put on that list (Holy Shock, Exorcism, Hand of Gul'dan, ...) must not fire the hooks (user
    // ruling 2026-11-27). Its source is COOLDOWN_TRIGGER_ALLOW_LIST in dbc-tools molten_set_bonuses.py.
    std::uint32_t constexpr kCooldownHookMinMs = 30000;
    std::uint32_t constexpr kMoltenCooldownTriggerAllowList[] = { 200333, 200829, 204148 };
    std::uint32_t constexpr kCooldownHasteDenyList[] = { 20154, 20164, 20165, 20166, 20375, 21084, 31801, 21169 };

    constexpr bool InList(std::uint32_t id, std::uint32_t const* list, std::uint32_t size)
    {
        for (std::uint32_t i = 0; i < size; ++i)
            if (list[i] == id)
                return true;
        return false;
    }

    constexpr bool IsCooldownHookSpell(std::uint32_t spellId, std::uint32_t recoveryMs,
        std::uint32_t categoryRecoveryMs)
    {
        if (InList(spellId, kCooldownHasteDenyList, sizeof(kCooldownHasteDenyList) / sizeof(kCooldownHasteDenyList[0])))
            return false;
        if (InList(spellId, kMoltenCooldownTriggerAllowList,
                sizeof(kMoltenCooldownTriggerAllowList) / sizeof(kMoltenCooldownTriggerAllowList[0])))
            return true;
        return recoveryMs >= kCooldownHookMinMs || categoryRecoveryMs >= kCooldownHookMinMs;
    }

    // The set of a Molten spell id (any of its ten), or Count outside the reservation.
    constexpr Archetype ArchetypeOf(std::uint32_t spellId)
    {
        if (!kSpellsMoltenSet.Contains(spellId))
            return Archetype::Count;
        std::uint32_t const index = (spellId - kSpellsMoltenSet.first) / kIdsPerSet;
        return index < kArchetypeCount ? static_cast<Archetype>(index) : Archetype::Count;
    }

    constexpr std::uint32_t SpellOf(Archetype set, std::uint32_t offset)
    {
        return kSpellsMoltenSet.first + static_cast<std::uint32_t>(set) * kIdsPerSet + offset;
    }

    constexpr std::uint32_t HeatSpellOf(Archetype set)
    {
        return SpellOf(set, kOffsetHeat);
    }

    constexpr std::uint32_t HeatCountOf(Archetype set)
    {
        return set < Archetype::Count ? kHeatCount[static_cast<std::uint32_t>(set)] : 0;
    }

    // One Heat event, as the proc saw it.
    struct HeatEvent
    {
        bool periodic = false;          // a periodic tick (not a cast)
        bool crit = false;              // a critical strike or heal
        bool spell = false;             // a spell: damage class magic or none
        bool meleeAbility = false;      // damage class melee
        bool rangedAbility = false;     // damage class ranged
        bool directDamage = false;      // the cast has a direct damage effect
        bool directHeal = false;        // the cast has a direct heal effect
        bool damageOrHeal = false;      // the cast has a damage or heal effect, direct or periodic
        bool periodicDamage = false;    // the tick dealt damage (a periodic event)
        bool holy = false;              // the spell's school includes Holy
        bool finisher = false;          // the spell needs combo points
        std::uint32_t comboPoints = 0;  // the points held at the hit (a finisher's, before they are taken)
    };

    // The Heat one event gives a set's 3 piece (0: not the set's event).
    constexpr std::uint32_t HeatGain(Archetype set, HeatEvent const& e)
    {
        std::uint32_t const castHeat = e.crit ? kCritHeat : 1;
        switch (set)
        {
            case Archetype::Sorcerers:
                if (e.periodic)
                    return (e.periodicDamage && e.crit) ? 1 : 0;
                return (e.spell && e.directDamage) ? castHeat : 0;
            case Archetype::Virtuous:
                return (!e.periodic && e.spell && e.directHeal) ? castHeat : 0;
            case Archetype::Feralheart:
            case Archetype::FiveThunders:
                return (!e.periodic && e.spell && e.damageOrHeal) ? castHeat : 0;
            case Archetype::Soulforge:
                // Any Holy spell or ability: Judgement and Avenger's Shield are ranged class in the 3.3.5 data.
                return (!e.periodic && (e.spell || e.meleeAbility || e.rangedAbility) && e.holy) ? castHeat : 0;
            case Archetype::Heroism:
            case Archetype::Guardians:
            case Archetype::Impenetrable:
                // "Abilities": melee or ranged class (Thunder Clap, Avenger's Shield, Judgement are ranged class),
                // never an auto attack (the proc rows carry no auto attack flag).
            case Archetype::Beastmasters:
                return (!e.periodic && (e.meleeAbility || e.rangedAbility)) ? castHeat : 0;
            case Archetype::Darkmantle:
                // Any finisher, whatever its damage class: Slice and Dice and Savage Roar are class NONE.
                if (e.periodic || !e.finisher || !e.comboPoints)
                    return 0;
                return e.comboPoints + (e.crit ? 1 : 0);
            default:
                return 0;
        }
    }

    // Where a two-sided eruption (Molten Thunder, Hallowed Flame) lands.
    enum class PayoutSide : std::uint8_t
    {
        Enemy,   // the damage half on the event's enemy target
        Ally,    // the heal half on the event's ally target
        Wearer,  // the heal half on the wearer
        Nearby,  // the damage half on the wearer's in-combat victim or selection
    };

    // The event's target is an enemy, an ally other than the wearer, or neither (none, or the wearer itself, as a
    // self-cast cooldown has); `healing` says the cast heals; `enemyInCombat` that the wearer has an in-combat victim
    // or hostile selection. A heal (on the wearer too) heals; a self-cast that does not heal (Elemental Mastery, a
    // seal) strikes the wearer's enemy, the heal on the wearer only when there is none.
    constexpr PayoutSide ChoosePayoutSide(bool targetEnemy, bool targetOtherAlly, bool healing, bool enemyInCombat)
    {
        if (targetEnemy)
            return PayoutSide::Enemy;
        if (targetOtherAlly)
            return PayoutSide::Ally;
        if (!healing && enemyInCombat)
            return PayoutSide::Nearby;
        return PayoutSide::Wearer;
    }

    // A Heat gain's result: the stacks left on the buff (0: the buff goes) and whether it erupted.
    struct HeatStep
    {
        std::uint32_t stacks = 0;
        bool erupts = false;
    };

    // `current` Heat plus `gain` against the set's `count`: reaching the count erupts and resets to 0 (the overflow is
    // lost); a zero count never erupts.
    constexpr HeatStep StepHeat(std::uint32_t current, std::uint32_t gain, std::uint32_t count)
    {
        HeatStep step;
        if (!count)
            return step;
        std::uint64_t const total = static_cast<std::uint64_t>(current) + gain;
        if (total >= count)
        {
            step.erupts = gain > 0;
            step.stacks = step.erupts ? 0 : current;
            return step;
        }
        step.stacks = static_cast<std::uint32_t>(total);
        return step;
    }

    // The Heat a 5 piece cooldown hook adds (Flare-up erupts at full strength whatever the Heat: the set's count).
    constexpr std::uint32_t CooldownHookHeat(Archetype set)
    {
        switch (set)
        {
            case Archetype::Sorcerers:
                return HeatCountOf(Archetype::Sorcerers);
            case Archetype::FiveThunders:
                return kThunderheadHeat;
            case Archetype::Heroism:
                return kStokeTheForgeHeat;
            case Archetype::Impenetrable:
                return kBankedCoalsHeat;
            default:
                return 0;
        }
    }

    // `amount` scaled by `pct` percent, rounded down, never negative.
    constexpr std::int32_t ScalePct(std::int32_t amount, std::int32_t pct)
    {
        if (amount <= 0 || pct <= 0)
            return 0;
        std::int64_t const scaled = static_cast<std::int64_t>(amount) * pct / 100;
        return scaled > 0x7FFFFFFF ? 0x7FFFFFFF : static_cast<std::int32_t>(scaled);
    }

    // Mending Flame: the Cauterize heal on an ally at `health` of `maxHealth` (before the heal), in percent.
    constexpr std::int32_t MendingFlamePct(std::uint32_t health, std::uint32_t maxHealth)
    {
        bool const below = maxHealth > 0 && static_cast<std::uint64_t>(health) * 100 <
            static_cast<std::uint64_t>(maxHealth) * kMendingFlameHealthPct;
        return below ? 100 + kMendingFlameBonusPct : 100;
    }

    // Lower health fraction first (a / maxA < b / maxB, cross-multiplied): the "most injured" ally.
    constexpr bool MoreInjured(std::uint32_t healthA, std::uint32_t maxA, std::uint32_t healthB, std::uint32_t maxB)
    {
        return static_cast<std::uint64_t>(healthA) * maxB < static_cast<std::uint64_t>(healthB) * maxA;
    }
}

#endif
