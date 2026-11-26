/*
 * mod-dungeon-bosses, Zul'Farrak: the hard mode item effects of Gahz'rilla, The Crew at the Pool (after the Ragefire
 * Chasm precedent RagefireChasmHardModeItemsLogic.h). The ids mirror
 * apps/dbc-tools/source/items/zul_farrak_hard_mode_effects.py and source/npcs/zul_farrak/hard_mode_items.py (the
 * `zul_farrak_items` reservation: spells 213800-213839, creatures 301000-301004). The engine glue is
 * hard_mode_items.cpp.
 *
 * Pure: no engine headers (the generated ItemSpellCopies.h is pure too), so the host test
 * (tests/zul_farrak_hard_mode_items_test.cpp) includes it.
 *
 * Every number a tooltip shows lives in the spell data, not here: the discharge's and the arc's damage are potency, the
 * stacks, the discharge's cooldown, the arc's targets and reach, the Whistle's share, allies and reach are aura
 * amounts and radii. Only the event rules, the one-action-per-cast bookkeeping and the crew's look are script numbers.
 */

#ifndef MOD_DUNGEON_BOSSES_ZUL_FARRAK_HARD_MODE_ITEMS_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZUL_FARRAK_HARD_MODE_ITEMS_LOGIC_H

#include "ItemSpellCopies.h"
#include <array>
#include <cstdint>

namespace ZulFarrakHardModeItems
{
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // ids.yaml reservation `zul_farrak_items` (the Zul'Farrak gear stage); the copies of the scaled effects mint from
    // the `item_spell_copy` block, never from here.
    IdSlice constexpr kSpellsZulFarrakItems{ 213800, 213839 };
    IdSlice constexpr kSpellsDeclared{ 213800, 213807 };
    IdSlice constexpr kCreaturesZulFarrakItems{ 301000, 301004 };

    enum ZulFarrakHardModeItemSpells : std::uint32_t
    {
        SPELL_SCALE_OF_THE_STORM_GOD    = 213800,   // Scale of the Storm God, Equip: the proc aura
                                                    // (spell_zf_scale_of_the_storm_god; its discharge grows per tier)
        SPELL_STATIC_CHARGE             = 213801,   // the stacks on the wearer (one spell for every tier)
        SPELL_STATIC_DISCHARGE          = 213802,   // the discharge (potency, scaled per tier;
                                                    // spell_zf_static_discharge)
        SPELL_STORMCHARGED_FANG         = 213803,   // Stormcharged Fang, Equip: the proc aura
                                                    // (spell_zf_stormcharged_fang; its arc grows per tier)
        SPELL_STORMCHARGED              = 213804,   // the charges on the wearer (one spell for every tier)
        SPELL_STORM_ARC                 = 213805,   // one arc (potency, scaled per tier; data only)
        SPELL_SERGEANTS_WHISTLE         = 213806,   // Sergeant's Whistle, Use: the 12 sec aura
                                                    // (spell_zf_sergeants_whistle; its share grows per tier)
        SPELL_THE_CREWS_AID             = 213807,   // the copied heal (one spell for every tier)
        // 213808 Call of Sul'thraze (SulthrazeJoinLogic.h); 213809-213839 spare
    };

    enum ZulFarrakHardModeItemCreatures : std::uint32_t
    {
        NPC_CREW_BLY    = 301000,
        NPC_CREW_RAVEN  = 301001,
        NPC_CREW_ORO    = 301002,
        NPC_CREW_WEEGLI = 301003,
        NPC_CREW_MURTA  = 301004,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Scale of the Storm God

    // SpellMgr.h ProcFlags, the two kinds of event 213800's spell_proc row passes (the host test keeps this header
    // free of SpellMgr.h; the .cpp asserts the values).
    std::uint32_t constexpr kTakenHitFlags = 0x8u | 0x20u | 0x80u | 0x200u | 0x2000u | 0x20000u;
    std::uint32_t constexpr kMeleeAbilityFlag = 0x10u;

    // A hit the wearer took: it charges the Scale when it dealt damage (after absorbs; a fully absorbed hit took
    // nothing) and came from somebody else. The wearer's own event never has a taken flag for a hit on another unit.
    constexpr bool HitCharges(std::uint32_t typeMask, std::uint32_t damage, bool fromWearer)
    {
        return (typeMask & kTakenHitFlags) != 0 && damage > 0 && !fromWearer;
    }

    // A melee ability of the wearer that landed. spell_proc passes triggered casts (boss hits often are), so a
    // triggered strike of the wearer that the engine would refuse (no "not a proc" attribute) is refused here.
    constexpr bool AbilityDischarges(std::uint32_t typeMask, bool triggered, bool notAProc, std::uint32_t stacks,
        std::uint32_t stacksNeeded, std::uint64_t nowMs, std::uint64_t readyAtMs)
    {
        return (typeMask & kTakenHitFlags) == 0 && (typeMask & kMeleeAbilityFlag) != 0 && (!triggered || notAProc)
            && stacksNeeded > 0 && stacks >= stacksNeeded && nowMs >= readyAtMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Stormcharged Fang

    enum class FangAction : std::uint8_t
    {
        None,
        Charge,
        Arc,
    };

    // A landed damaging hit of a cast that has not acted yet: at full charge it arcs when somebody is there to arc to
    // (else the charges are kept, and a critical hit renews them); below it a critical hit charges.
    constexpr FangAction DecideFang(std::uint32_t charges, std::uint32_t chargesNeeded, bool critical, bool anyOther)
    {
        if (chargesNeeded > 0 && charges >= chargesNeeded && anyOther)
            return FangAction::Arc;
        return critical ? FangAction::Charge : FangAction::None;
    }

    // One action per cast (Systems.md section 5, "A cast rolls once"; the Scholomance Bonechill Blade's guard): an area
    // spell reaches a proc check once per target it hits, all with the same Spell object, so the object's address
    // groups the hits; it never identifies a cast alone, because the allocator reuses a freed Spell's address and
    // triggered spells all carry cast count 0. `moment` pins the cast in time: a delayed (traveling) spell's launch
    // moment (Spell::GetDelayStart, the same for every target it reaches later), else the game time of the update the
    // immediate spell hits in (all its targets land in that one update). A later cast that reuses the address has
    // another moment, so it acts.
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

    // True when `now` is the cast that already acted. An event without a spell has a null `spell` and never matches.
    constexpr bool SameCast(CastStamp const& last, CastStamp const& now)
    {
        return now.spell != nullptr && last.spell == now.spell && last.spellId == now.spellId
            && last.castCount == now.castCount && last.moment == now.moment;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Sergeant's Whistle

    // One effect of a healing spell, as IsSingleTargetHeal reads it.
    struct HealShape
    {
        bool heals = false;             // a direct heal or a heal over time
        bool area = false;              // an area target, an area aura or a ground aura
        bool onCaster = false;          // aimed at the caster by the data (TARGET_UNIT_CASTER)
        std::uint32_t chainTargets = 0; // above 1: a chain heal
    };

    // A single target heal: every healing effect goes to one unit, and to the same one (Binding Heal's target and
    // caster are two).
    constexpr bool IsSingleTargetHeal(std::array<HealShape, 3> const& effects)
    {
        bool any = false;
        bool onCaster = false;
        for (HealShape const& effect : effects)
        {
            if (!effect.heals)
                continue;
            if (effect.area || effect.chainTargets > 1 || (any && effect.onCaster != onCaster))
                return false;
            any = true;
            onCaster = effect.onCaster;
        }
        return any;
    }

    // Priest heals that read as one single target heal in the data, but that a script casts on several targets at once:
    // Empowered Penance's extra bolts (spell_priest.cpp) and Glyph of Prayer of Healing's heal over time, one on each
    // ally the area heal reached. Their enum lives in spell_priest.cpp; the lib test pins the ids to it.
    std::uint32_t constexpr kEmpoweredPenanceBolt = 200160;
    std::uint32_t constexpr kPrayerOfHealingGlyph = 56161;

    constexpr bool IsScriptSpreadHeal(std::uint32_t spellId)
    {
        return spellId == kEmpoweredPenanceBolt || spellId == kPrayerOfHealingGlyph;
    }

    // The heal the wearer gave, before the healed target's own healing taken modifiers and heal absorbs: the copy is a
    // heal of its own, so the ally's modifiers apply to it, once. `probeTaken` is what kTakenProbe points of the same
    // heal become on the healed target (Unit::SpellHealingBonusTaken; the Tidal Force echo's precedent). HealInfo's
    // own GetHealBeforeTakenMods() does not serve: a tick leaves it 0 and it misses what a script added to the heal
    // (SetHitHeal: Harmony, Glimmer, set bonuses). A probe of 0 cannot be undone: the heal as it landed.
    std::uint32_t constexpr kTakenProbe = 1000000;

    constexpr std::uint32_t HealBeforeTaken(std::uint32_t landed, std::uint32_t absorbed, std::uint32_t probeTaken)
    {
        std::uint64_t amount = std::uint64_t(landed) + absorbed;
        if (probeTaken != 0)
            amount = (amount * kTakenProbe + probeTaken / 2) / probeTaken;
        return amount > 0xFFFFFFFFu ? 0xFFFFFFFFu : std::uint32_t(amount);
    }

    // The copied heal: `sharePct` percent of the heal's amount.
    constexpr std::int32_t ShareOfHeal(std::uint32_t heal, std::int32_t sharePct)
    {
        if (sharePct <= 0)
            return 0;
        std::uint64_t const amount = std::uint64_t(heal) * std::uint64_t(sharePct) / 100u;
        return amount > 0x7FFFFFFFu ? 0x7FFFFFFF : std::int32_t(amount);
    }

    constexpr bool IsInjured(std::uint32_t health, std::uint32_t maxHealth)
    {
        return health > 0 && health < maxHealth;
    }

    // A's health fraction is below B's (cross-multiplied: no rounding).
    constexpr bool LowerHealthFraction(std::uint32_t healthA, std::uint32_t maxA, std::uint32_t healthB,
        std::uint32_t maxB)
    {
        return std::uint64_t(healthA) * maxB < std::uint64_t(healthB) * maxA;
    }

    // The crew around the wearer, look only: where each one stands (an angle from the wearer's facing, behind it) and
    // the stock crew's weapons (creature_equip_template 7604-7608).
    struct CrewLook
    {
        std::uint32_t entry;
        float angle;
        std::uint32_t mainHand;
        std::uint32_t offHand;
        std::uint32_t ranged;
    };

    std::array<CrewLook, 5> constexpr kCrew
    { {
        { NPC_CREW_BLY,    1.6f, 2180, 1984, 0 },
        { NPC_CREW_RAVEN,  2.4f, 5281, 5281, 0 },
        { NPC_CREW_MURTA,  3.1f, 5291, 0,    0 },
        { NPC_CREW_WEEGLI, 3.9f, 5278, 0,    2552 },
        { NPC_CREW_ORO,    4.7f, 2559, 0,    0 },
    } };
    float constexpr kCrewDistance = 3.0f;
    // The Use's 12 sec and a short tail: the script dismisses them, this only catches a wearer that left the map.
    std::uint32_t constexpr kCrewStayMs = 13000;
}

#endif
