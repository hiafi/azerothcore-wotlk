/*
 * mod-dungeon-bosses, Blackrock Spire: the Overlord Wyrmthalak and General Drakkisath hard mode item effects (wave 2
 * dungeon items, after the Stratholme precedent StratholmeHardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/blackrock_spire_hard_mode_effects.py (the `blackrock_spire_items` reservation
 * 206800-206829). The engine glue is hard_mode_items.cpp.
 *
 * Pure: no engine headers, so the host test (tests/blackrock_spire_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the Ward's stack cap is 206802's amount and its
 * search radius 206802's radius, the damage per stack is 206803's amount. The helpers below only do the arithmetic on
 * them. None of the six effects scales by item level, so none has per-tier copies and no script resolves one
 * (ItemSpellCopies) here.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_HARD_MODE_ITEMS_LOGIC_H

#include <cstdint>

namespace BlackrockSpireHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `blackrock_spire_items` (wave 2 dungeon items); the creature reservation 300650-300654 is
    // unused (no summons).
    IdSlice constexpr kSpellsBlackrockSpireItems{ 206800, 206829 };
    IdSlice constexpr kSpellsDeclared{ 206800, 206811 };

    enum BlackrockSpireHardModeItemSpells : std::uint32_t
    {
        SPELL_BLOODAXE_WAR_HORN         = 206800,   // Bloodaxe War Horn, Use: the interrupt and 206801 (data only)
        SPELL_BLOODAXE_WAR_CRY          = 206801,   // the debuff: -10% damage done, 10 sec
        SPELL_WARD_OF_THE_THREE_TRIBES  = 206802,   // Ward of the Three Tribes, Equip: the 0.5 s watch
                                                    // (spell_brs_ward_of_the_three_tribes)
        SPELL_WARD_BUFF                 = 206803,   // the buff: -1% damage taken per stack, up to 5
        SPELL_SHARDSTAFF_OF_STOLEN_POWER = 206804,  // Shardstaff of Stolen Power, Equip: the crit proc (data only)
        SPELL_STOLEN_POWER              = 206805,   // +1% spell damage and healing, 10 sec, up to 5 stacks
        SPELL_TROPHY_OF_THE_CHAMPION    = 206806,   // Trophy of the Champion, Equip: the mark proc (data only)
        SPELL_CHAMPIONS_MARK            = 206807,   // "damaged in the last 5 sec" (spell_brs_champions_mark)
        SPELL_CHAMPIONS_TROPHY          = 206808,   // +1% damage and healing, 30 sec, up to 5 stacks
        SPELL_ORDERS_OF_THE_GENERAL     = 206809,   // Orders of the General, Use: -10% damage taken, 8 sec (data only)
        SPELL_THE_HUMBLER               = 206810,   // The Humbler, Equip: the melee proc (data only)
        SPELL_HUMBLED                   = 206811,   // the debuff: -5% damage done, 8 sec
        // 206812-206829 spare
    };

    // Ward of the Three Tribes: one stack per enemy attacking the wearer within the radius, at most `cap` (the aura's
    // amount). No attacker, or no cap, no stacks (the script then removes the buff). Never more than the cap, and the
    // result always fits the aura's 8-bit stack counter.
    constexpr std::uint32_t WardStacks(std::uint32_t attackers, std::int32_t cap)
    {
        if (cap <= 0)
            return 0;
        std::uint32_t const limit = cap > 255 ? 255u : std::uint32_t(cap);
        return attackers < limit ? attackers : limit;
    }

    // Trophy of the Champion: the wearer gets a Trophy only when the Champion's Mark ended because its target died
    // (not when it ran out, was removed or the target evaded), and only while the wearer is alive and still carries
    // the Trophy's equip aura.
    constexpr bool ChampionEarnsTrophy(bool markEndedByDeath, bool wearerAlive, bool wearerHasTrophy)
    {
        return markEndedByDeath && wearerAlive && wearerHasTrophy;
    }
}

#endif
