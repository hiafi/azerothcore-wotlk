/*
 * mod-dungeon-bosses, Shadowfang Keep: the Archmage Arugal hard mode item effects (item variants, wave 1). The ids
 * mirror apps/dbc-tools/source/items/shadowfang_keep_hard_mode_effects.py (spells, the `shadowfang_items`
 * reservation 205600-205619) and source/npcs/shadowfang_keep/hard_mode_items.py (creature 300460, the
 * shadowfang_items creature slice 300460-300464).
 * The engine glue is sfk_hard_mode_items.cpp.
 *
 * Pure: no engine headers, so the host test (tests/shadowfang_keep_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the Tome's chance and internal cooldown are its
 * spell_proc row, the Voidwalker's damage, tick and length are 205602's. Only the look-alike Voidwalker's stay and
 * where it appears are script numbers. The Vial (205600) and the Locket (205603) are pure data, with no script.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_HARD_MODE_ITEMS_LOGIC_H

#include <cstdint>

namespace SfkHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `shadowfang_items`; the declared effects take its first five ids.
    IdSlice constexpr kSpellsShadowfangItems{ 205600, 205619 };
    IdSlice constexpr kSpellsDeclared{ 205600, 205604 };

    enum SfkHardModeItemSpells : std::uint32_t
    {
        SPELL_VIAL_OF_THE_WORGENS_CURSE = 205600,   // Vial of the Worgen's Curse, Use: Haste rating and speed (data)
        SPELL_ARUGALS_SHADOW_TOME       = 205601,   // Arugal's Shadow Tome, Equip: the proc aura
                                                    // (spell_sfk_arugals_shadow_tome)
        SPELL_ARUGALS_VOIDWALKER        = 205602,   // the Voidwalker's attacks, a damage over time (potency)
                                                    // (spell_sfk_arugals_voidwalker)
        SPELL_ASHCROMBES_LOCKET         = 205603,   // Ashcrombe's Locket, Use: Curse dispel and ward (data)
        SPELL_METEOR_SHARD_FIREBOLT     = 205604,   // the Meteor Shard's Chance on hit (data)
        // 205605-205619 spare
    };

    enum SfkHardModeItemCreatures : std::uint32_t
    {
        NPC_TOME_VOIDWALKER             = 300460,   // the Tome's look-alike Voidwalker, no script
    };

    // The Voidwalker stays as long as the Voidwalker debuff (205602's 10 sec) plus a little, so a debuff that runs its
    // full length still sees it on the last tick; the debuff's removal sends it away first.
    std::uint32_t constexpr kVoidwalkerStayMs = 10500;
    // It appears this far beyond the edge of the target's hit box, on the wearer's side.
    float constexpr kVoidwalkerGap = 1.0f;
    // The script looks for its own Voidwalker this far around the target (it chases the target, so it stays close).
    float constexpr kVoidwalkerSearchRange = 30.0f;

    // How far from the target's position the Voidwalker appears.
    constexpr float VoidwalkerDistance(float targetCombatReach)
    {
        return (targetCombatReach > 0.0f ? targetCombatReach : 0.0f) + kVoidwalkerGap;
    }

    // Whether a Voidwalker belongs to this debuff: summoned by the debuff's caster (the wearer). Two wearers attacking
    // the same target each keep their own.
    constexpr bool IsOwnVoidwalker(std::uint64_t summonerRawGuid, std::uint64_t casterRawGuid)
    {
        return summonerRawGuid != 0 && summonerRawGuid == casterRawGuid;
    }
}

#endif
