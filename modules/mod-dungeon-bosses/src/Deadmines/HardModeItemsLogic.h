/*
 * mod-dungeon-bosses, Deadmines: the Edwin VanCleef hard mode item effects (item variants plan section 7.2, stage
 * IV6). The ids mirror apps/dbc-tools/source/items/deadmines_hard_mode_effects.py (spells, the `items` reservation
 * 205400-205599) and source/npcs/deadmines/hard_mode_items.py (creature 300430, the `deadmines` creature spare). The
 * engine glue is hard_mode_items.cpp.
 *
 * Pure: no engine headers, so the host test (tests/hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the fuse is 205401's duration, the blast radius
 * 205402's, the zone's size, length and -10% are 205407's, the Signet's chance and internal cooldown are its spell_proc
 * row. Only the look-alike Blackguard's stay (how long it stands, how far behind the target) is a script number.
 */

#ifndef MOD_DUNGEON_BOSSES_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_HARD_MODE_ITEMS_LOGIC_H

#include "DeadminesRework.h"
#include <cstdint>

namespace HardModeItems
{
    using DeadminesRework::IdSlice;

    // ids.yaml reservation `items` (item variants); the Deadmines hard mode effects take its first ten ids.
    IdSlice constexpr kSpellsItems{ 205400, 205599 };
    IdSlice constexpr kSpellsDeadminesHardModeItems{ 205400, 205409 };

    enum HardModeItemSpells : std::uint32_t
    {
        SPELL_POWDER_KEG_FUSE           = 205400,   // Powder Keg Fuse, Use: the lobbed keg (spell_dm_powder_keg_fuse)
        SPELL_POWDER_KEG_FUSE_LOOK      = 205401,   // the lit keg on the ground; its duration is the fuse
        SPELL_POWDER_KEG_BLAST          = 205402,   // the 6 yd Fire blast (potency)
        SPELL_BLACKGUARDS_SIGNET        = 205403,   // Blackguard's Signet, Equip: the proc aura
                                                    // (spell_dm_blackguards_signet)
        SPELL_BLACKGUARD_STRIKE         = 205404,   // the strike, cast by the wearer (potency)
        SPELL_BLACKGUARD_AMBUSH_LOOK    = 205405,   // the Blackguard's look as it appears
        SPELL_LANTERN_OF_ROARING_FLAME  = 205406,   // Lantern of the Roaring Flame, Use: the one-charge heal buff
                                                    // (spell_dm_lantern_of_the_roaring_flame)
        SPELL_ROARING_FLAME_ZONE        = 205407,   // the warding flame, -10% damage taken
        // 205408-205409 spare
    };

    enum HardModeItemCreatures : std::uint32_t
    {
        NPC_SIGNET_BLACKGUARD           = 300430,   // the Signet's look-alike Blackguard, no script
    };

    // The Blackguard stands this long (the ambush look plays, then it is gone) and appears this far behind the edge of
    // the target's hit box.
    std::uint32_t constexpr kBlackguardStayMs = 2500;
    float constexpr kBlackguardGap = 1.0f;
    // Used only if 205401 is missing from the spell store (it never should be): the designer's 2 sec.
    std::uint32_t constexpr kKegFuseFallbackMs = 2000;

    // Where the wearer stood when the keg landed: the blast goes off only on the same map and instance.
    struct Place
    {
        std::uint32_t mapId;
        std::uint32_t instanceId;
    };

    // The blast goes off when the fuse runs out if the wearer is still in the world, on the map and in the instance
    // where the keg landed (a teleport, a zone change or a logout in the 2 sec defuses it; a death does not).
    constexpr bool KegStillLive(bool inWorld, Place lit, Place now)
    {
        return inWorld && lit.mapId == now.mapId && lit.instanceId == now.instanceId;
    }

    // How far behind the target's position the Blackguard appears.
    constexpr float BlackguardDistance(float targetCombatReach)
    {
        return (targetCombatReach > 0.0f ? targetCombatReach : 0.0f) + kBlackguardGap;
    }

    // How long the lobbed keg flies, the engine's own missile delay (Spell::AddUnitTarget: the distance counts as at
    // least 5 yd, the delay is floored to whole milliseconds). Needs a positive speed.
    constexpr std::uint32_t KegFlightMs(float distance, float speed)
    {
        if (speed <= 0.0f)
            return 0;
        float const dist = distance < 5.0f ? 5.0f : distance;
        return static_cast<std::uint32_t>(dist / speed * 1000.0f);
    }

    // The fuse in milliseconds: 205401's duration when it has one, the fallback otherwise.
    constexpr std::uint32_t KegFuseMs(std::int32_t lookDurationMs)
    {
        return lookDurationMs > 0 ? static_cast<std::uint32_t>(lookDurationMs) : kKegFuseFallbackMs;
    }
}

#endif
