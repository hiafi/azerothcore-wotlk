/*
 * mod-dungeon-bosses, Stratholme: the Balnazzar and Baron Rivendare hard mode item effects (wave 1 dungeon items,
 * after the Deadmines precedent HardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/stratholme_hard_mode_effects.py (the `stratholme_items` reservation 205660-205699). The
 * engine glue is hard_mode_items.cpp.
 *
 * Pure: no engine headers, so the host test (tests/stratholme_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the Tome's share is 205663's amount and its search
 * radius 205663's radius, the Locket's threshold and radius are 205665's, its lockout 205667's duration, the Condemned
 * percent and stack cap 205669's, the trample radius 205670's. The helpers below only do the arithmetic on them.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_HARD_MODE_ITEMS_LOGIC_H

#include <cstdint>

namespace StratholmeHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `stratholme_items` (wave 1 dungeon items); the copies of the scaled effects mint from the
    // `item_spell_copy` block (205410-205599), never from here.
    IdSlice constexpr kSpellsStratholmeItems{ 205660, 205699 };
    IdSlice constexpr kSpellsDeclared{ 205660, 205672 };

    enum StratholmeHardModeItemSpells : std::uint32_t
    {
        SPELL_CARRION_SIGNET            = 205660,   // Carrion Signet, Equip: PROC_TRIGGER_SPELL into 205661 (no script)
        SPELL_CARRION_SWARM             = 205661,   // the Shadow cone (potency, scaled per tier)
        SPELL_DUST_OF_THE_NATHREZIM     = 205662,   // Dust of the Nathrezim, Use: the sleep
                                                    // (spell_strat_dust_of_the_nathrezim)
        SPELL_TWO_FACED_TOME            = 205663,   // Two-Faced Tome, Equip: the heal proc aura
                                                    // (spell_strat_two_faced_tome)
        SPELL_THE_LIE                   = 205664,   // the lie: Shadow damage, a share of the heal
        SPELL_YSIDAS_LOCKET             = 205665,   // Ysida's Locket, Equip: the 0.5 s watch
                                                    // (spell_strat_ysidas_locket)
        SPELL_YSIDAS_WARD               = 205666,   // the ward (absorb potency, scaled per tier)
        SPELL_YSIDAS_LOCKET_LOCKOUT     = 205667,   // the 60 s lockout on the wearer
        SPELL_BLADE_OF_THE_CONDEMNED    = 205668,   // Blade of the Condemned, Equip: the melee proc aura
                                                    // (spell_strat_blade_of_the_condemned)
        SPELL_CONDEMNED                 = 205669,   // the stacking debuff (StratholmeCondemnedDamage applies it)
        SPELL_DEATHCHARGERS_SPUR        = 205670,   // Deathcharger's Spur, Use: speed and the trample watch
                                                    // (spell_strat_deathchargers_spur)
        SPELL_DEATHCHARGER_TRAMPLE      = 205671,   // the trample (potency, scaled per tier)
        SPELL_SPECTRAL_DEATHCHARGER     = 205672,   // the mount look, added and removed by the Spur's script
        // 205673-205699 spare
    };

    // Ysida's Locket: a group member qualifies below `thresholdPct` percent of its maximum health (strictly below, as
    // "falls below 20%" reads). A dead or empty unit never does.
    constexpr bool BelowHealthPct(std::uint32_t health, std::uint32_t maxHealth, std::int32_t thresholdPct)
    {
        if (health == 0 || maxHealth == 0 || thresholdPct <= 0)
            return false;
        return std::uint64_t(health) * 100u < std::uint64_t(maxHealth) * std::uint64_t(thresholdPct);
    }

    // Of two qualifying members the one with the lower health fraction gets the ward (cross-multiplied, no floats).
    constexpr bool LowerHealthFraction(std::uint32_t healthA, std::uint32_t maxA, std::uint32_t healthB,
        std::uint32_t maxB)
    {
        return std::uint64_t(healthA) * maxB < std::uint64_t(healthB) * maxA;
    }

    // The Two-Faced Tome's lie: `sharePct` percent of the heal, rounded down. Nothing for a zero heal or share.
    constexpr std::int32_t LieDamage(std::uint32_t heal, std::int32_t sharePct)
    {
        if (sharePct <= 0)
            return 0;
        std::uint64_t const damage = std::uint64_t(heal) * std::uint64_t(sharePct) / 100u;
        return damage > 0x7FFFFFFFu ? 0x7FFFFFFF : std::int32_t(damage);
    }

    // Condemned: `totalPct` is the aura's amount, which the engine already multiplies by its stacks (1% x stacks).
    // Damage from the aura's caster grows by that percent, rounded down; a zero or negative amount changes nothing.
    constexpr std::uint32_t CondemnedDamage(std::uint32_t damage, std::int32_t totalPct)
    {
        if (totalPct <= 0)
            return damage;
        std::uint64_t const grown = std::uint64_t(damage) * (100u + std::uint64_t(totalPct)) / 100u;
        return grown > 0xFFFFFFFFu ? 0xFFFFFFFFu : std::uint32_t(grown);
    }

    // Blade of the Condemned: a hit on another target than the last one first takes the wearer's Condemned off the
    // last one ("attacking another target resets it"). 0 = no last target yet.
    constexpr bool CondemnResets(std::uint64_t lastTarget, std::uint64_t newTarget)
    {
        return lastTarget != 0 && lastTarget != newTarget;
    }
}

#endif
