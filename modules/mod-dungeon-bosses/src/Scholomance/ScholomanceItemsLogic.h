/*
 * mod-dungeon-bosses, Scholomance: the item effects of the Scholomance loot (wave 1 dungeon items; designer text:
 * docs/dungeons/scholomance-rework.md ## Loot). The ids mirror apps/dbc-tools/source/items/
 * scholomance_hard_mode_effects.py (the `scholomance_items` spell reservation 205620-205659). The engine glue is
 * scholomance_items.cpp; only four effects need a script (Phylactery Shard, Bonechill Blade, Transfer Papers,
 * Darkmaster's Portal Rod), the rest are spell data.
 *
 * Pure: no engine headers, so the host test (tests/scholomance_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the Phylactery's armor, length and 30% are 205631's
 * effects, the chances and internal cooldowns are spell_proc rows, the barrage's length and ticks are 205641's. Only
 * how far behind the target the portal opens is a script number.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_ITEMS_LOGIC_H

#include <cstdint>
#include <limits>

namespace ScholomanceItems
{
    // An inclusive id range of an ids.yaml reservation.
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const
        {
            return id >= first && id <= last;
        }
    };

    // ids.yaml reservation `scholomance_items`; the declared effects take 205620-205642, 205643-205659 are spare.
    IdSlice constexpr kSpellsScholomanceItems{ 205620, 205659 };

    enum ScholomanceItemSpells : std::uint32_t
    {
        // Normal list (data only, no script)
        SPELL_SPARE_RIB                 = 205620,   // Spare Rib, Use: +armor
        SPELL_JAR_OF_TORN_SOULS         = 205621,   // Jar of Torn Souls, Equip: the proc aura
        SPELL_TORN_SOUL                 = 205622,   // the stacking Intellect buff
        SPELL_RIB_SPREADER              = 205623,   // Rib Spreader, Equip: the proc aura
        SPELL_OPEN_WOUND                = 205624,   // the bleed (potency)
        SPELL_SPECIMEN_LAUNCHER         = 205625,   // Polkelt's Specimen Launcher, Equip: the proc aura
        SPELL_SPECIMEN_ACID             = 205626,   // the acid pool (potency)
        SPELL_THE_DEANS_ROD             = 205627,   // The Dean's Rod, Equip: the parry proc aura
        SPELL_DEMERIT                   = 205628,   // the attacker's -1% damage done, stacks to 5
        SPELL_SUTURE_KIT                = 205629,   // Krastinov's Suture Kit, Use: three charges
        SPELL_STITCHES                  = 205630,   // the heal over time (potency)
        // Ras Frostwhisper hard mode
        SPELL_PHYLACTERY_SHARD          = 205631,   // Phylactery Shard, Use: armor + the damage tally
                                                    // (spell_scholo_phylactery_shard)
        SPELL_PHYLACTERY_MEND           = 205632,   // the heal when it ends, sized by the script
        SPELL_FROSTWHISPERS_CHILLBAND   = 205633,   // Frostwhisper's Chillband, Equip: the proc aura
        SPELL_CHILL                     = 205634,   // -10% attack and casting speed
        SPELL_BONECHILL_BLADE           = 205635,   // Bonechill Blade, Equip: the proc aura
                                                    // (spell_scholo_bonechill_blade, once per cast)
        SPELL_BONECHILL_FROST_BLAST     = 205636,   // the blast (potency)
        // Darkmaster Gandling hard mode
        SPELL_TRANSFER_PAPERS           = 205637,   // Transfer Papers, Use: swap places
                                                    // (spell_scholo_transfer_papers)
        SPELL_HONOR_ROLL_RIBBON         = 205638,   // Honor Roll Ribbon, Equip: the 30 sec periodic trigger
        SPELL_HONOR_ROLL                = 205639,   // the absorb (potency) + 1% damage and healing
        SPELL_DARKMASTERS_PORTAL_ROD    = 205640,   // Darkmaster's Portal Rod, Equip: the proc aura
                                                    // (spell_scholo_darkmasters_portal_rod)
        SPELL_PORTAL_BARRAGE            = 205641,   // the stream of arcane missiles (potency)
        SPELL_DARKMASTERS_PORTAL_LOOK   = 205642,   // the portal's ground look, visual only
        // 205643-205659 spare
    };

    // ids.yaml `scholomance_items` creature slice 300465-300469 (source/npcs/scholomance/hard_mode_items.py).
    enum ScholomanceItemCreatures : std::uint32_t
    {
        NPC_DARKMASTERS_PORTAL          = 300465,   // the Portal Rod's look-alike portal, no script
    };

    // The portal stays for the barrage (3 sec, 205641's duration) plus a short tail, then despawns.
    std::uint32_t constexpr kPortalStayMs = 3500;

    // The portal opens this far behind the edge of the target's hit box.
    float constexpr kPortalGap = 2.0f;

    // How far behind the target's position the portal opens.
    constexpr float PortalDistance(float targetCombatReach)
    {
        return (targetCombatReach > 0.0f ? targetCombatReach : 0.0f) + kPortalGap;
    }

    // Phylactery Shard: the damage taken while the ice is up, added hit by hit (never wraps).
    constexpr std::uint64_t PhylacteryTally(std::uint64_t sum, std::uint32_t damage)
    {
        return sum > std::numeric_limits<std::uint64_t>::max() - damage ? std::numeric_limits<std::uint64_t>::max()
                                                                         : sum + damage;
    }

    // Phylactery Shard: the heal when the ice ends, `pct` percent of the tally (205631 effect 2's amount), rounded
    // down and capped to what a spell value holds. Nothing for a non-positive percent or an empty tally.
    constexpr std::int32_t PhylacteryHeal(std::uint64_t taken, std::int32_t pct)
    {
        if (pct <= 0 || taken == 0)
            return 0;
        std::uint64_t constexpr cap = static_cast<std::uint64_t>(std::numeric_limits<std::int32_t>::max());
        // taken * pct / 100 without overflowing: the tally is capped first
        std::uint64_t const capped = taken > cap ? cap : taken;
        std::uint64_t const heal = capped * static_cast<std::uint64_t>(pct) / 100;
        return static_cast<std::int32_t>(heal > cap ? cap : heal);
    }

    // Bonechill Blade: one cast, as the proc check sees it. An area spell reaches the check once per target it hits,
    // all with the same Spell object; its id and the caster's cast counter tell a later cast that reuses the address
    // apart from it.
    struct CastStamp
    {
        void const* spell = nullptr;
        std::uint32_t spellId = 0;
        std::uint8_t castCount = 0;
    };

    // True when `now` is the cast the Blade already rolled for (so it does not roll again).
    constexpr bool SameCast(CastStamp const& last, CastStamp const& now)
    {
        return now.spell != nullptr && last.spell == now.spell && last.spellId == now.spellId
            && last.castCount == now.castCount;
    }

    // Transfer Papers: what the swap needs to know about the two sides.
    struct SwapCheck
    {
        bool targetIsPlayer;
        bool targetIsCaster;
        bool targetAlive;
        bool sameGroup;
        bool casterInFlight;
        bool targetInFlight;
        bool casterOnVehicle;
        bool targetOnVehicle;
    };

    // The swap goes ahead only with another living player of the caster's group, neither side on a taxi or a vehicle.
    constexpr bool CanSwap(SwapCheck const& c)
    {
        return c.targetIsPlayer && !c.targetIsCaster && c.targetAlive && c.sameGroup && !c.casterInFlight
            && !c.targetInFlight && !c.casterOnVehicle && !c.targetOnVehicle;
    }
}

#endif
