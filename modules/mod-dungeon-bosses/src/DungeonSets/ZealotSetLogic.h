/*
 * mod-dungeon-bosses, dungeon sets: the Zealot's set bonuses (docs/dungeons/scarlet-monastery-rework.md ## Loot, "The
 * Zealot's family: Martyrdom" and "3 piece bonuses", rulings 57 to 59). The ids mirror
 * apps/dbc-tools/source/items/zealot_set_bonuses.py (the `zealot_set` spell reservation 212100-212299) and the hound
 * look source/npcs/zealot_set/vendors.py (300894). The engine glue is zealot_set_bonuses.cpp.
 *
 * Pure: no engine headers, so the host test (tests/zealot_set_test.cpp) includes it.
 *
 * Every number a tooltip reads from the spell data stays there (the Fervor values, durations, the buff amounts, the
 * proc cooldown). What lives here are the script numbers: the Fervor slope's full-value line, the 35% trigger line,
 * search ranges, the hound count, and the percents a script applies itself (Arcanist's Ward, Blood Offering). Each one
 * a tooltip prints is a literal in zealot_set_bonuses.py too, and lib/test_zealot_set.py checks the two agree.
 */

#ifndef MOD_DUNGEON_BOSSES_ZEALOT_SET_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZEALOT_SET_LOGIC_H

#include <cstdint>

namespace ZealotSet
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

    // ids.yaml reservation `zealot_set`: 212100-212103 the Fervor lines, 212110-212209 ten per set, the rest spare.
    IdSlice constexpr kSpellsZealotSet{ 212100, 212299 };

    enum ZealotSetSpells : std::uint32_t
    {
        // Zealot's Fervor, the 2 piece role line
        SPELL_FERVOR_DAMAGE             = 212100,   // +6% damage on own health (ZealotSetUnitHooks)
        SPELL_FERVOR_HEALING            = 212101,   // +8% healing on the target's health
        SPELL_FERVOR_TANK               = 212102,   // -6% damage taken on own health
        SPELL_FERVOR_HYBRID             = 212103,   // effect 1 damage, effect 2 healing
        // Battlegear of the Scarlet Champion (Plate Strength, ItemSet 1004)
        SPELL_UNBROKEN_ZEAL             = 212110,   // 3 piece (spell_zealot_martyr)
        SPELL_UNBROKEN_ZEAL_BUFF        = 212111,   // (spell_zealot_unbroken_zeal)
        SPELL_UNBROKEN_ZEAL_HEAL        = 212112,
        // Bulwark of the Last Stand (Plate Tank, 1005)
        SPELL_HOLD_THE_LINE             = 212120,   // 3 piece
        SPELL_HOLD_THE_LINE_BUFF        = 212121,   // data only
        // Vigil of the Fallen Champion (Plate Intellect, 1006)
        SPELL_KINDLED_VIGIL             = 212130,   // 3 piece
        SPELL_KINDLED_VIGIL_AURA        = 212131,   // (spell_zealot_kindled_vigil)
        SPELL_KINDLED_VIGIL_BURN        = 212132,   // every enemy within 5 yd (ruling B8: no in-combat filter)
        // Houndmaster's Harness (Mail Agility, 1007)
        SPELL_KENNEL_CALL               = 212140,   // 3 piece
        SPELL_KENNEL_CALL_BUFF          = 212141,   // (spell_zealot_kennel_call)
        SPELL_KENNEL_CALL_BITE          = 212142,
        SPELL_KENNEL_CALL_BITE_RANGED   = 212143,
        // Curator's Regalia (Mail Intellect, 1008)
        SPELL_LAST_PAGE                 = 212150,   // 3 piece
        SPELL_LAST_PAGE_BUFF            = 212151,   // (spell_zealot_last_page)
        // Interrogator's Garb (Leather Agility, 1009)
        SPELL_EXTRACT_CONFESSION        = 212160,   // 3 piece
        SPELL_EXTRACT_CONFESSION_DEBUFF = 212161,   // read by ZealotSetUnitHooks
        SPELL_EXTRACT_CONFESSION_HEAL   = 212162,
        // Ironspine's Bones (Leather Tank, 1010)
        SPELL_BONE_CAGE                 = 212170,   // 3 piece
        SPELL_BONE_CAGE_BUFF            = 212171,   // data only (PROC_TRIGGER_SPELL)
        SPELL_BONE_CAGE_SPIKE           = 212172,
        // Gardener's Vestments (Leather Spirit, 1011)
        SPELL_HALLOWED_THORNS           = 212180,   // 3 piece
        SPELL_HALLOWED_THORNS_BUFF      = 212181,   // (spell_zealot_hallowed_thorns)
        SPELL_HALLOWED_THORNS_STRIKE    = 212182,
        // Regalia of the Arcanist (Cloth Intellect, 1012)
        SPELL_ARCANISTS_WARD            = 212190,   // 3 piece
        SPELL_ARCANISTS_WARD_ABSORB     = 212191,   // (spell_zealot_arcanists_ward)
        SPELL_ARCANISTS_WARD_DETONATION = 212192,   // every enemy within 10 yd (ruling B8: no in-combat filter)
        // Vestments of the High Inquisitor (Cloth Spirit, 1013)
        SPELL_BLOOD_OFFERING            = 212200,   // 3 piece
        SPELL_BLOOD_OFFERING_HEAL       = 212201,   // (spell_zealot_blood_offering)
    };

    enum ZealotSetCreatures : std::uint32_t
    {
        NPC_SCARLET_TRACKING_HOUND      = 300894,   // the Kennel Call look
    };

    // Zealot's Fervor: the full value at 40% health or below, nothing at full health, a straight slope between.
    std::uint32_t constexpr kFervorFullAtHealthPct = 40;
    // The 3 piece trigger line: a hit that takes the wearer below 35%, a heal on any target at or below 35%.
    std::uint32_t constexpr kMartyrHealthPct = 35;
    // Kennel Call: two hounds, a bite target within 40 yd.
    std::uint32_t constexpr kKennelCallHounds = 2;
    float constexpr kKennelCallRange = 40.0f;
    float constexpr kHoundFollowDistance = 2.0f;
    float constexpr kLookSearchRange = 60.0f;
    // Extract Confession: the wearer's target within 40 yd, else the enemy whose hit crossed the line.
    float constexpr kConfessionRange = 40.0f;
    // Arcanist's Ward: absorbs 15% of maximum health.
    std::uint32_t constexpr kArcanistsWardHealthPct = 15;
    // Blood Offering: the wearer gives 10% of current health.
    std::uint32_t constexpr kBloodOfferingCostPct = 10;

    // The ten 3 piece bonuses and how each is triggered: by the wearer's own 35% crossing, by the wearer's heal on an
    // ally at or below 35%, or both (ruling 59: Plate Intellect, Mail Intellect, Leather Spirit both; Cloth Spirit
    // the ally alone).
    enum class Trigger : std::uint8_t
    {
        Self,
        Ally,
        SelfOrAlly,
    };

    struct Martyr
    {
        std::uint32_t bonus;    // the 3 piece aura
        Trigger trigger;
    };

    Martyr constexpr kMartyrs[] = {
        { SPELL_UNBROKEN_ZEAL, Trigger::Self },
        { SPELL_HOLD_THE_LINE, Trigger::Self },
        { SPELL_KINDLED_VIGIL, Trigger::SelfOrAlly },
        { SPELL_KENNEL_CALL, Trigger::Self },
        { SPELL_LAST_PAGE, Trigger::SelfOrAlly },
        { SPELL_EXTRACT_CONFESSION, Trigger::Self },
        { SPELL_BONE_CAGE, Trigger::Self },
        { SPELL_HALLOWED_THORNS, Trigger::SelfOrAlly },
        { SPELL_ARCANISTS_WARD, Trigger::Self },
        { SPELL_BLOOD_OFFERING, Trigger::Ally },
    };

    // The trigger kind of a 3 piece aura (Self for an id that is none of them).
    constexpr Trigger TriggerOf(std::uint32_t bonus)
    {
        for (Martyr const& martyr : kMartyrs)
            if (martyr.bonus == bonus)
                return martyr.trigger;
        return Trigger::Self;
    }

    constexpr bool TriggersOnSelf(Trigger trigger)
    {
        return trigger != Trigger::Ally;
    }

    constexpr bool TriggersOnAlly(Trigger trigger)
    {
        return trigger != Trigger::Self;
    }

    // Zealot's Fervor's share of the full value, in basis points (10000 = the full value): (missing health) / 60% of
    // maximum health, capped at 10000; 0 at full health or with no maximum.
    constexpr std::uint32_t FervorShareBp(std::uint32_t health, std::uint32_t maxHealth)
    {
        if (!maxHealth || health >= maxHealth)
            return 0;
        std::uint64_t const missing = static_cast<std::uint64_t>(maxHealth - health);
        std::uint64_t const span = static_cast<std::uint64_t>(maxHealth) * (100 - kFervorFullAtHealthPct);
        std::uint64_t const share = missing * 100 * 10000 / span;
        return share >= 10000 ? 10000 : static_cast<std::uint32_t>(share);
    }

    // The Fervor bonus in basis points of the amount (fullPct 6: up to 600) for a unit at `health` of `maxHealth`.
    constexpr std::uint32_t FervorBonusBp(std::int32_t fullPct, std::uint32_t health, std::uint32_t maxHealth)
    {
        if (fullPct <= 0)
            return 0;
        return static_cast<std::uint32_t>(static_cast<std::uint64_t>(fullPct) * FervorShareBp(health, maxHealth) /
            100);
    }

    // `amount` raised (`raise`) or lowered by `bonusBp` basis points, rounded down, never negative, at most INT32_MAX.
    constexpr std::uint32_t ApplyBp(std::uint32_t amount, std::uint32_t bonusBp, bool raise)
    {
        if (!amount || !bonusBp)
            return amount;
        std::uint64_t const factor = raise ? 10000u + bonusBp : (bonusBp >= 10000 ? 0u : 10000u - bonusBp);
        std::uint64_t const scaled = static_cast<std::uint64_t>(amount) * factor / 10000;
        return scaled > 0x7FFFFFFF ? 0x7FFFFFFFu : static_cast<std::uint32_t>(scaled);
    }

    // `pct` percent of `amount`, rounded down (a heal of a hit, a share of health).
    constexpr std::uint32_t PctOf(std::uint32_t amount, std::uint32_t pct)
    {
        std::uint64_t const part = static_cast<std::uint64_t>(amount) * pct / 100;
        return part > 0x7FFFFFFF ? 0x7FFFFFFFu : static_cast<std::uint32_t>(part);
    }

    // The 3 piece's own line: the hit of `damage` that left the wearer at `healthAfter` (alive) took them from 35% or
    // more to below 35% of `maxHealth` (the Haunted Deathless shape).
    constexpr bool CrossedMartyrLine(std::uint32_t healthAfter, std::uint32_t damage, std::uint32_t maxHealth)
    {
        if (!maxHealth || !healthAfter || !damage)
            return false;
        std::uint64_t const line = static_cast<std::uint64_t>(maxHealth) * kMartyrHealthPct;
        std::uint64_t const after = static_cast<std::uint64_t>(healthAfter) * 100;
        std::uint64_t const before = (static_cast<std::uint64_t>(healthAfter) + damage) * 100;
        return after < line && before >= line;
    }

    // The heal line (designer ruling C4, 2026-11-20): any target the wearer's heal hits, the wearer included, was at or
    // below 35% of `maxHealth` at the moment the heal landed, before its amount was added (its health now minus the
    // effective heal; a dead target never counts). The name is historical: the target need not be an ally.
    constexpr bool AllyAtMartyrLine(std::uint32_t healthNow, std::uint32_t effectiveHeal, std::uint32_t maxHealth)
    {
        if (!maxHealth || !healthNow)
            return false;
        std::uint64_t const before = healthNow > effectiveHeal ? healthNow - effectiveHeal : 0;
        if (!before)
            return false;
        return before * 100 <= static_cast<std::uint64_t>(maxHealth) * kMartyrHealthPct;
    }

    // Kennel Call: hound `index` (0, 1) stands at +90 / -90 degrees from the wearer's facing, at summon and whenever it
    // falls back to following (a TempSummon has no follow angle of its own: review n3).
    constexpr float HoundAngle(std::uint32_t index)
    {
        return index ? -1.57079633f : 1.57079633f;
    }

    // Zealot's Fervor on periodic ticks. A heal tick calls ModifyPeriodicDamageAurasTick(target, caster) and then,
    // right after it on the same thread, ModifyHealReceived(target, caster); a direct heal calls only
    // ModifyHealReceived, with the healer first. So a tick of a spell that can heal over time (SPELL_AURA_PERIODIC_HEAL 8, OBS_MOD_HEALTH 20) is
    // not scaled as damage: it is marked, and the ModifyHealReceived call that matches the mark scales it as the
    // caster's heal on the target (review m1 and n6). A tick of a spell with no heal aura is damage.
    std::uint32_t constexpr kAuraPeriodicHeal = 8;
    std::uint32_t constexpr kAuraObsModHealth = 20;

    constexpr bool IsPeriodicHealAura(std::uint32_t auraType)
    {
        return auraType == kAuraPeriodicHeal || auraType == kAuraObsModHealth;
    }

    struct PeriodicTick
    {
        std::uint64_t target = 0;   // raw guid values
        std::uint64_t caster = 0;
        std::uint32_t spellId = 0;
        bool set = false;
    };

    // True when ModifyHealReceived(first, second, spellId) is the heal half of the marked tick.
    constexpr bool IsHealTickOf(PeriodicTick const& tick, std::uint64_t first, std::uint64_t second,
        std::uint32_t spellId)
    {
        return tick.set && tick.target == first && tick.caster == second && tick.spellId == spellId;
    }

    // Blood Offering's price: 10% of the current health, never the last point.
    constexpr std::uint32_t BloodOfferingCost(std::uint32_t health)
    {
        std::uint32_t const cost = PctOf(health, kBloodOfferingCostPct);
        return health > 1 && cost >= health ? health - 1 : cost;
    }
}

#endif
