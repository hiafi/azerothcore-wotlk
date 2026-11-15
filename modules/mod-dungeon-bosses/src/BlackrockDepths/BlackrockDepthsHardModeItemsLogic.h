/*
 * mod-dungeon-bosses, Blackrock Depths: the hard mode item effects of the Ring of Law Encore, Lord Incendius, Golem
 * Lord Argelmach and Emperor Dagran Thaurissan (wave 2 dungeon items, after the Stratholme precedent
 * StratholmeHardModeItemsLogic.h). The ids mirror apps/dbc-tools/source/items/blackrock_depths_hard_mode_effects.py
 * (the `blackrock_depths_items` reservation: spells 206830-206899, creatures 300655-300669) and
 * source/npcs/blackrock_depths/hard_mode_items.py. The engine glue is hard_mode_items.cpp.
 *
 * Pure: no engine headers, so the host test (tests/blackrock_depths_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: Theldren's percent and threshold are 206830's two
 * amounts, Korv's share and search radius 206833's, the orb count and reach 206842's, the Servo's reach 206845's, the
 * Coil's charge chance and arc radius 206847's, the beam's half width 206852's; the chances and internal cooldowns are
 * spell_proc rows. Only how long a summoned look stays, where it stands and how far a script looks for it are script
 * numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_HARD_MODE_ITEMS_LOGIC_H

#include <cstdint>

namespace BlackrockDepthsHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `blackrock_depths_items` (wave 2 dungeon items); the copies of the scaled effects mint from
    // the `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsBlackrockDepthsItems{ 206830, 206899 };
    IdSlice constexpr kSpellsDeclared{ 206830, 206853 };
    IdSlice constexpr kCreaturesBlackrockDepthsItems{ 300655, 300669 };

    enum BlackrockDepthsHardModeItemSpells : std::uint32_t
    {
        // The Ring of Law, the Encore
        SPELL_THELDRENS_EXECUTIONER     = 206830,   // Theldren's Executioner, Equip: the marker aura
                                                    // (BrdExecutionerDamage reads its two amounts)
        SPELL_LEFTYS_SHIV               = 206831,   // Lefty's Shiv, Equip: PROC_TRIGGER_SPELL into 206832 (no script)
        SPELL_VICIOUS_WOUND             = 206832,   // the stacking bleed (potency, scaled per tier)
        SPELL_KORVS_SPIRIT_FETISH       = 206833,   // Korv's Spirit Fetish, Equip: the heal proc aura
                                                    // (spell_brd_korvs_spirit_fetish)
        SPELL_SPIRIT_CHAIN              = 206834,   // the chained heal, half the heal (set by the script)
        // Lord Incendius, Lord of the Lake
        SPELL_BLACK_ANVIL_BULWARK       = 206835,   // Black Anvil Bulwark, Equip: PROC_TRIGGER_SPELL on a block
        SPELL_ANVIL_ERUPTION            = 206836,   // the Fire burst around the wearer (potency, scaled per tier)
        SPELL_FIST_OF_THE_LAKE_LORD     = 206837,   // Fist of the Lake Lord, Equip: PROC_TRIGGER_SPELL on melee hits
        SPELL_LAKE_LORDS_SLAM           = 206838,   // the Fire slam under the target (potency, scaled per tier)
        SPELL_SCEPTER_OF_THE_MOLTEN_LAKE = 206839,  // Scepter of the Molten Lake, Equip: the spell proc aura
                                                    // (spell_brd_scepter_of_the_molten_lake)
        SPELL_LAVA_SPAWN                = 206840,   // the wearer's 10 sec buff, every 2 sec (spell_brd_lava_spawn)
        SPELL_MOLTEN_HURL               = 206841,   // the Spawn's hurl, cast by the wearer (potency, scaled per tier)
        // Golem Lord Argelmach, the Prototype
        SPELL_PROTOTYPE_POWER_CORE      = 206842,   // Prototype Power Core, Use: the orbs, every 2 sec
                                                    // (spell_brd_prototype_power_core)
        SPELL_ARCANE_ORB_STRIKE         = 206843,   // one orb's strike (potency, scaled per tier)
        SPELL_GOLEMWRIGHTS_MENDING_ROD  = 206844,   // Golemwright's Mending Rod, Equip: the heal proc aura
                                                    // (spell_brd_golemwrights_mending_rod)
        SPELL_MENDING_SERVO             = 206845,   // the healer's 10 sec buff, every 2 sec (spell_brd_mending_servo)
        SPELL_SERVO_MEND                = 206846,   // the Servo's heal, cast by the healer (potency, scaled per tier)
        SPELL_ELECTRONS_LETHAL_COIL     = 206847,   // Electron's Lethal Coil, Equip: the hit watch
                                                    // (spell_brd_electrons_lethal_coil)
        SPELL_LETHAL_ATTRACTION         = 206848,   // the 8 sec charge on the target
        SPELL_LETHAL_ARC                = 206849,   // the arc (potency, scaled per tier)
        // Emperor Dagran Thaurissan, the Avatar of Ragnaros
        SPELL_VOLCANIC_HEARTSTONE       = 206850,   // Volcanic Heartstone, Use: -20% damage taken
                                                    // (spell_brd_volcanic_heartstone)
        SPELL_HEARTSTONE_ERUPTION       = 206851,   // the burst when it ends (potency, scaled per tier)
        SPELL_ORB_OF_THE_SORCERER_THANE = 206852,   // Orb of the Sorcerer-Thane, Equip: the spell proc aura
                                                    // (spell_brd_orb_of_the_sorcerer_thane)
        SPELL_SHADOW_BEAM               = 206853,   // the beam (potency, scaled per tier)
        // 206854-206899 spare
    };

    enum BlackrockDepthsHardModeItemCreatures : std::uint32_t
    {
        NPC_LAVA_SPAWN                  = 300655,   // the Scepter's look (source/npcs/blackrock_depths/)
        NPC_MENDING_SERVO               = 300656,   // the Mending Rod's look
        // 300657-300669 spare
    };

    // How long a summoned look stays: the buff it fights under (206840 / 206845, 10 sec) plus a short tail, so the
    // last tick still finds it. The buff's removal dismisses it first.
    std::uint32_t constexpr kLookStayMs = 11500;
    // How far a script looks for the wearer's own look (the Servo stays where it was deployed; the wearer may walk).
    float constexpr kLookSearchRange = 100.0f;
    // The Lava Spawn follows the wearer at this distance, to the wearer's left.
    float constexpr kSpawnFollowDistance = 2.5f;
    float constexpr kSpawnFollowAngle = 1.5707964f;
    // The Lava Spawn only hurls at an enemy within this distance of the wearer.
    float constexpr kHurlRange = 40.0f;

    // A summoned look is the wearer's own when it was summoned by the wearer (raw guid values, 0 = none).
    constexpr bool IsOwnLook(std::uint64_t summonerGuid, std::uint64_t wearerGuid)
    {
        return summonerGuid != 0 && summonerGuid == wearerGuid;
    }

    // Theldren's Executioner: the target qualifies strictly below `thresholdPct` percent of its maximum health ("below
    // 30% health"). A dead or empty unit never does.
    constexpr bool BelowHealthPct(std::uint32_t health, std::uint32_t maxHealth, std::int32_t thresholdPct)
    {
        if (health == 0 || maxHealth == 0 || thresholdPct <= 0)
            return false;
        return std::uint64_t(health) * 100u < std::uint64_t(maxHealth) * std::uint64_t(thresholdPct);
    }

    // Theldren's Executioner: the hit grows by `bonusPct` percent, rounded down; a zero or negative bonus changes
    // nothing.
    constexpr std::uint32_t GrownDamage(std::uint32_t damage, std::int32_t bonusPct)
    {
        if (bonusPct <= 0)
            return damage;
        std::uint64_t const grown = std::uint64_t(damage) * (100u + std::uint64_t(bonusPct)) / 100u;
        return grown > 0xFFFFFFFFu ? 0xFFFFFFFFu : std::uint32_t(grown);
    }

    // Korv's Spirit Fetish: `sharePct` percent of the heal, rounded down, clamped to an int32 spell value.
    constexpr std::int32_t ShareOfHeal(std::uint32_t heal, std::int32_t sharePct)
    {
        if (sharePct <= 0)
            return 0;
        std::uint64_t const amount = std::uint64_t(heal) * std::uint64_t(sharePct) / 100u;
        return amount > 0x7FFFFFFFu ? 0x7FFFFFFF : std::int32_t(amount);
    }

    // Korv's Spirit Fetish and the Mending Servo heal the injured only: alive and below full health.
    constexpr bool IsInjured(std::uint32_t health, std::uint32_t maxHealth)
    {
        return health > 0 && health < maxHealth;
    }

    // Of two injured members, the one with the lower health fraction is "the most injured" (cross-multiplied, no
    // floats). A tie keeps the first pick.
    constexpr bool LowerHealthFraction(std::uint32_t healthA, std::uint32_t maxA, std::uint32_t healthB,
        std::uint32_t maxB)
    {
        return std::uint64_t(healthA) * maxB < std::uint64_t(healthB) * maxA;
    }

    // Prototype Power Core: orb `orb` (0-based) strikes enemy number `orb % enemies` of the shuffled list, so the
    // orbs pick different enemies while there are enough and share them when there are fewer. -1 with no enemy.
    constexpr std::int32_t OrbTargetIndex(std::uint32_t orb, std::uint32_t enemies)
    {
        return enemies == 0 ? -1 : std::int32_t(orb % enemies);
    }

    // Orb of the Sorcerer-Thane: is the point (px, py) on the beam from (ax, ay) to (bx, by)? Its projection must fall
    // between the two ends and its distance from the line be at most `halfWidth` (all on the ground plane, yards).
    // A zero-length beam holds only its own end.
    constexpr bool OnBeam(float px, float py, float ax, float ay, float bx, float by, float halfWidth)
    {
        float const dx = bx - ax;
        float const dy = by - ay;
        float const lengthSq = dx * dx + dy * dy;
        float const wx = px - ax;
        float const wy = py - ay;
        if (lengthSq <= 0.0f)
            return wx * wx + wy * wy <= halfWidth * halfWidth;
        float const along = wx * dx + wy * dy;
        if (along < 0.0f || along > lengthSq)
            return false;
        float const cross = wx * dy - wy * dx;
        // distance from the line = |cross| / length; compared squared to stay exact without a square root
        return cross * cross <= halfWidth * halfWidth * lengthSq;
    }
}

#endif
