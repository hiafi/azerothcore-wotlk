/*
 * mod-dungeon-bosses, Scarlet Monastery: the hard mode item effects of Bloodmage Thalnos, Arcanist Doan, Herod and High
 * Inquisitor Whitemane (after the Blackrock Depths precedent BlackrockDepthsHardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/scarlet_monastery_hard_mode_effects.py (the `scarlet_monastery_items` reservation:
 * spells 212000-212099, creatures 300880-300889) and source/npcs/scarlet_monastery/hard_mode_items.py. The engine glue
 * is hard_mode_items.cpp.
 *
 * Pure: no engine headers (the generated ItemSpellCopies.h is pure too), so the host test
 * (tests/scarlet_monastery_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the banner's reach is 212000's radius, the Rallied
 * percent 212001's amount, the lockout 212002's duration, the Verdict's extra targets and reach 212018's amount and
 * radius, the Rosary's health threshold 212022's amount; the chances and internal cooldowns are spell_proc rows. Only
 * how long the banner stays, the Verdict's arc and the one-roll-per-cast bookkeeping are script numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_HARD_MODE_ITEMS_LOGIC_H

#include "ItemSpellCopies.h"
#include <cstdint>

namespace ScarletMonasteryHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `scarlet_monastery_items` (the Scarlet Monastery gear stage); the copies of the scaled
    // effects mint from the `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsScarletMonasteryItems{ 212000, 212099 };
    IdSlice constexpr kSpellsDeclared{ 212000, 212023 };
    IdSlice constexpr kCreaturesScarletMonasteryItems{ 300880, 300889 };

    // A Scarlet Monastery hard mode item spell: a declared one (the reservation) or one of their tier copies (minted in
    // the item spell copy block, so only ItemSpellCopies knows their base). The Haunted set's Haunting Mark skips them
    // (review m2: a Garrison Volley must never consume the mark meant for the hunter's next ranged ability).
    constexpr bool IsItemSpell(std::uint32_t id)
    {
        if (kSpellsScarletMonasteryItems.Contains(id))
            return true;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
            if (copy.copy == id)
                return kSpellsScarletMonasteryItems.Contains(copy.base);
        return false;
    }

    enum ScarletMonasteryHardModeItemSpells : std::uint32_t
    {
        // Bloodmage Thalnos, the Desecration
        SPELL_PUREBLOODS_RALLYING_STANDARD  = 212000,   // Pureblood's Rallying Standard, Use: the banner, every 1 sec
                                                        // (spell_sm_pureblood_rallying_standard; scaled per tier)
        SPELL_RALLIED                       = 212001,   // +5% damage near the banner (more on higher tiers), 2 sec
        SPELL_RECENTLY_RALLIED              = 212002,   // the 2 min lockout, one spell for every tier
        SPELL_FAIRBELLS_CENSER              = 212003,   // Fairbell's Censer, Equip: PROC_TRIGGER_SPELL into 212004
                                                        // (spell_sm_one_roll_per_cast)
        SPELL_PENITENT_FIRE                 = 212004,   // the 3 stack Fire DoT (potency, scaled per tier)
        SPELL_VOSSS_BLESSED_SIGNET          = 212005,   // Voss's Blessed Signet, Equip: PROC_TRIGGER_SPELL into 212006
                                                        // (spell_sm_one_roll_per_cast)
        SPELL_VOSSS_BLESSING                = 212006,   // the shield on the healed target (potency, scaled per tier)
        // Arcanist Doan, the Kel'Thuzad Heresy
        SPELL_SHARD_OF_THE_PHYLACTERY       = 212007,   // Shard of the Phylactery, Use: absorb + 10% (data only)
        SPELL_HERETICS_WAND                 = 212008,   // Heretic's Wand, Equip: PROC_TRIGGER_SPELL into 212009
                                                        // (spell_sm_one_roll_per_cast)
        SPELL_ICY_DEATH                     = 212009,   // Frost over time and a 30% slow (potency, scaled per tier)
        SPELL_FISSURE_TOUCHED_GRIPS         = 212010,   // Fissure-touched Grips, Equip: PROC_TRIGGER_SPELL into 212011
                                                        // (spell_sm_one_roll_per_cast)
        SPELL_SHADOW_FISSURE                = 212011,   // Shadow around the target (potency, scaled per tier)
        // Herod, Call to Arms
        SPELL_SCARLET_GARRISON_RIFLE        = 212012,   // Scarlet Garrison Rifle, Equip: PROC_TRIGGER_SPELL into 212013
                                                        // (spell_sm_one_roll_per_cast)
        SPELL_GARRISON_VOLLEY               = 212013,   // Physical around the target (potency, scaled per tier)
        SPELL_GARRISON_BULWARK              = 212014,   // Garrison Bulwark, Equip: PROC_TRIGGER_SPELL on a block
        SPELL_PILLAR_OF_LIGHT               = 212015,   // the heal on the wearer (potency, scaled per tier)
        SPELL_STAFF_OF_THE_CONSECRATED_HALL = 212016,   // Staff of the Consecrated Hall, Equip: PROC_TRIGGER_SPELL
                                                        // into 212017 (spell_sm_one_roll_per_cast)
        SPELL_CONSECRATED_PILLAR            = 212017,   // the party heal at the target (potency, scaled per tier)
        // High Inquisitor Whitemane, The Truth
        SPELL_FATHERS_VERDICT               = 212018,   // Father's Verdict, Equip: the melee proc aura
                                                        // (spell_sm_fathers_verdict)
        SPELL_VERDICT                       = 212019,   // one enemy's share of the cleave (potency, scaled per tier)
        SPELL_TREADS_OF_DENIAL              = 212020,   // Treads of Denial, Equip: PROC_TRIGGER_SPELL on a parry
        SPELL_DENIAL                        = 212021,   // 10% less damage taken (more on higher tiers), 6 sec
        SPELL_INQUISITORS_ROSARY            = 212022,   // Inquisitor's Rosary, Equip: the heal proc aura
                                                        // (spell_sm_inquisitors_rosary)
        SPELL_INQUISITORS_RESOLVE           = 212023,   // +3% Versatility, 8 sec, on the healer and the healed
        // 212024-212099 spare
    };

    enum ScarletMonasteryHardModeItemCreatures : std::uint32_t
    {
        NPC_RALLYING_STANDARD               = 300880,   // Galvar's banner (source/npcs/scarlet_monastery/)
        // 300881-300889 spare
    };

    // How long the banner stays: the Use's 15 sec plus a short tail, so the last pulse still finds it. The aura's
    // removal dismisses it first.
    std::uint32_t constexpr kStandardStayMs = 15500;
    // How far a script looks for the wearer's own banner (it stays where it was planted; the wearer may walk off).
    float constexpr kLookSearchRange = 100.0f;
    // The Verdict's cleave reaches enemies in the wearer's front half (Position::HasInArc takes the whole arc).
    float constexpr kVerdictArc = 3.14159265f;

    // A summoned look is the wearer's own when it was summoned by the wearer (raw guid values, 0 = none).
    constexpr bool IsOwnLook(std::uint64_t summonerGuid, std::uint64_t wearerGuid)
    {
        return summonerGuid != 0 && summonerGuid == wearerGuid;
    }

    // Pureblood's Rallying Standard: a player is rallied by `wearer`'s banner unless they carry another wearer's
    // Recently Rallied (raw guid values). A player with no lockout gets one from this wearer first; a player whose
    // lockout came from this wearer keeps being rallied by this banner (so a standard never locks out its own group).
    constexpr bool CanRally(bool hasLockout, std::uint64_t lockoutCaster, std::uint64_t wearer)
    {
        return !hasLockout || (lockoutCaster != 0 && lockoutCaster == wearer);
    }

    // Father's Verdict: how many other enemies the cleave takes (the aura's amount, never below 0) of those available.
    constexpr std::uint32_t VerdictExtraTargets(std::int32_t amount, std::uint32_t available)
    {
        if (amount <= 0)
            return 0;
        return std::uint32_t(amount) < available ? std::uint32_t(amount) : available;
    }

    // Inquisitor's Rosary: the healed player was strictly below `thresholdPct` percent of its maximum health before
    // the heal (the heal has landed when the proc runs: health now minus the effective heal). A unit at 0 before the
    // heal (dead) never qualifies.
    constexpr bool BelowThresholdBeforeHeal(std::uint32_t health, std::uint32_t effectiveHeal, std::uint32_t maxHealth,
        std::int32_t thresholdPct)
    {
        if (maxHealth == 0 || thresholdPct <= 0 || effectiveHeal >= health)
            return false;
        std::uint64_t const before = std::uint64_t(health - effectiveHeal);
        return before * 100u < std::uint64_t(maxHealth) * std::uint64_t(thresholdPct);
    }

    // One roll per cast (Systems.md section 5, "A cast rolls once"; the Scholomance Bonechill Blade's guard): an area
    // spell reaches a proc check once per target it hits, all with the same Spell object, so the object's address
    // groups the hits; it never identifies a cast alone, because the allocator reuses a freed Spell's address and
    // triggered spells all carry cast count 0. `moment` pins the cast in time: a delayed (travelling) spell's launch
    // moment (Spell::GetDelayStart, the same for every target it reaches later), else the game time of the update the
    // immediate spell hits in (all its targets land in that one update). A later cast that reuses the address has
    // another moment, so it rolls.
    struct CastStamp
    {
        void const* spell = nullptr;
        std::uint32_t spellId = 0;
        std::uint8_t castCount = 0;
        std::uint64_t moment = 0;
    };

    // The `moment` of a cast: the delayed spell's launch moment when it has one, else the current game time.
    constexpr std::uint64_t CastMoment(std::uint64_t delayStart, std::uint64_t nowMs)
    {
        return delayStart != 0 ? delayStart : nowMs;
    }

    // True when `now` is the cast that already rolled (so it does not roll again). An event without a spell (an auto
    // attack) has a null `spell` and always rolls.
    constexpr bool SameCast(CastStamp const& last, CastStamp const& now)
    {
        return now.spell != nullptr && last.spell == now.spell && last.spellId == now.spellId
            && last.castCount == now.castCount && last.moment == now.moment;
    }
}

#endif
