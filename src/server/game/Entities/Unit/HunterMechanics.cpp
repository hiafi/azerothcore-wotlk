/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "HunterMechanics.h"
#include "CellImpl.h"
#include "CharmInfo.h"
#include "Config.h"
#include "Containers.h"
#include "Creature.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "UnitAI.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <list>
#include <mutex>
#include <unordered_map>
#include <vector>

/*
 * Hunter rework - shared mechanics (hunter-rework.SHARED.md §A5, §C4). Stage T2 holds the T2 block only.
 */
namespace Hunter
{
    bool StingsStack(SpellInfo const* a, SpellInfo const* b)
    {
        return a && b && a->GetSpellSpecific() == SPELL_SPECIFIC_STING && b->GetSpellSpecific() == SPELL_SPECIFIC_STING;
    }

    Player* GetOwningPlayer(Unit* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    Player const* GetOwningPlayer(Unit const* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    float GetProcChanceMultiplier(Unit const* unit)
    {
        Player const* owner = GetOwningPlayer(unit);
        return owner ? 1.0f + owner->GetProcChancePercentage() / 100.0f : 1.0f;
    }

    bool RollProcChance(Unit const* unit, float baseChancePct)
    {
        return roll_chance_f(baseChancePct * GetProcChanceMultiplier(unit));
    }

    void ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms)
    {
        if (!player || !ms)
            return;

        player->ModifySpellCooldown(spellId, -int32(ms));
    }

    bool IsClasslessRealm()
    {
        static bool const value = sConfigMgr->GetOption<bool>("Custom.Realm.Classless", false);
        return value;
    }

    void EnsureNoAmmoAura(Player* player)
    {
        if (!player || player->HasAura(SPELL_REQUIRES_NO_AMMO))
            return;

        // 46699 is passive and hidden, so addSpell applies the aura and nothing shows in the spellbook.
        if (!player->HasSpell(SPELL_REQUIRES_NO_AMMO))
            player->addSpell(SPELL_REQUIRES_NO_AMMO, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, SPELL_REQUIRES_NO_AMMO, true);
    }

    void ClearState(Player* player)
    {
        // Later sections add their Clear*State calls here; removal paths use find-only map access.
        ClearMarksmanshipState(player);

        if (!player)
            return;

        // S3 (A18): the Explosive Shot carry and the Burning Tar bank this hunter owns as caster.
        ClearExplosiveShotCarryForCaster(player->GetGUID());
        ClearBurningTarForCaster(player->GetGUID());
    }

    bool IsAspectRollSource(SpellInfo const* spellInfo)
    {
        // d1 b28: every pet-cast family-9 spell carries it (SHARED §A3).
        constexpr uint32 FAMILY_FLAG1_PET_ABILITY = 0x10000000;

        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_HUNTER ||
            spellInfo->DmgClass != SPELL_DAMAGE_CLASS_RANGED)
            return false;

        // SUPPRESS_CASTER_PROCS spells (Silencing Shot, proc damage) never roll (SHARED §B6.2); the CAST-phase proc
        // call does not honour the attribute, so it is checked here.
        if (spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS))
            return false;

        if (spellInfo->IsPassive() || (spellInfo->SpellFamilyFlags[1] & FAMILY_FLAG1_PET_ABILITY))
            return false;

        // Kill Command and its cosmetic pet strike (201705, PET 6.3) never roll aspect procs.
        if (spellInfo->Id == SPELL_KILL_COMMAND || spellInfo->Id == SPELL_KILL_COMMAND_STRIKE)
            return false;

        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    return true;
                case SPELL_EFFECT_APPLY_AURA:
                    if (effect.ApplyAuraName == SPELL_AURA_PERIODIC_DAMAGE)
                        return true;
                    break;
                default:
                    break;
            }
        }

        return false;
    }

    Unit* GetProcTarget(ProcEventInfo& eventInfo)
    {
        if (Unit* target = eventInfo.GetActionTarget())
            return target;

        // CAST phase: no action target yet, fall back to the proc spell's explicit unit target.
        if (Spell const* spell = eventInfo.GetProcSpell())
            return spell->m_targets.GetUnitTarget();

        return nullptr;
    }

    void OnDirectFireHit(Unit* attacker, Unit* target, SpellInfo const* spellInfo)
    {
        // S3b body (contract in HunterMechanics.h, SURVIVAL §0.23, S3b-HANDOFF B1).
        // Never twice for one hit: a source either raises Tarred's proc itself (no SUPPRESS_CASTER_PROCS) or calls
        // this from its AfterHit (it carries the attribute), never both (S3b 0-verify 4a checked every source).
        //  - Raise Tarred 202048's proc themselves (its OnEffectProc calls this): the 53301 hit, the 202045 impact,
        //    the 202051 first blast, the 13812 blast.
        //  - Call this from their AfterHit (suppressed, GetHitDamage() > 0 only): 201601 (H0's Dragonhawk
        //    explosion), 202052 (Cluster Bombs follow-up), 202053 (Shrapnel), 202054 (Explosive Shot hit splash).
        //  - Exclusion list (the body returns for them): 53352 (Explosive Shot blasts), 202055 (blast splash),
        //    202057 (Explosive Trap ground fire), 202050 (Burning Tar itself).
        // No class check (contract verbatim): the bank is erased by 202050's own AfterEffectRemove for any caster.
        Player* hunter = GetOwningPlayer(attacker);
        if (!hunter || !target || !spellInfo || !target->IsAlive())
            return;

        switch (spellInfo->Id)
        {
            case SPELL_EXPLOSIVE_SHOT_BLAST:
            case SPELL_EXPLOSIVE_SHOT_BLAST_SPLASH:
            case SPELL_EXPLOSIVE_TRAP_FIRE:
            case SPELL_BURNING_TAR:
                return;
            default:
                break;
        }

        if (!(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_FIRE))
            return;

        // At least one non-periodic damage effect (a periodic-only spell never counts).
        bool directDamage = false;
        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    directDamage = true;
                    break;
                default:
                    break;
            }
        }

        if (!directDamage || !target->GetAura(SPELL_TARRED, hunter->GetGUID()))
            return;

        AddBurningTar(hunter, target);
    }

    float GetShotManaPct(Unit const* caster, SpellInfo const* shot)
    {
        if (!shot)
            return 0.0f;

        // User ruling 6 (S3a brief resolution 5): Raptor Strike 2973 has no EFFECT_1 and is never read there. It
        // restores the percent of base mana in Deadly Focus rank 2's marker (202081 eff2 DUMMY, live 5, already a
        // whole percent) while the hunter knows that rank, and nothing otherwise.
        if (shot->GetFirstRankSpell()->Id == SPELL_RAPTOR_STRIKE)
        {
            Player const* player = caster ? caster->ToPlayer() : nullptr;
            if (!player || !player->HasSpell(SPELL_DEADLY_FOCUS_R2))
                return 0.0f;

            SpellInfo const* deadlyFocus = sSpellMgr->GetSpellInfo(SPELL_DEADLY_FOCUS_R2);
            return deadlyFocus ? float(deadlyFocus->Effects[EFFECT_2].CalcValue(player)) : 0.0f;
        }

        // Tenths of a percent of base mana (Arcane Shot 3044: bp 199 -> 20.0%).
        return shot->Effects[EFFECT_1].CalcValue(caster) / 10.0f;
    }

    void RestoreShotMana(Player* player, SpellInfo const* shot, float multiplier)
    {
        if (!player || !shot)
            return;

        // S1b PT-6 (user ruling 2026-10-15): the percent is of BASE mana (UNIT_FIELD_BASE_MANA, the class/level base),
        // not of maximum mana, for every caller.
        float const pct = GetShotManaPct(player, shot);
        uint32 const amount = uint32(std::max(0.0f, player->GetCreateMana() * pct / 100.0f * multiplier));
        if (!amount)
            return;

        player->EnergizeBySpell(player, shot->Id, amount, POWER_MANA);
    }

    // ---- H0-P: pet section (PET.md 4.2, 4.5, 4.7, 5, 6; HunterMechanics.h has the contract) ----
    namespace
    {
        // Stock Leggings of Beast Mastery (spell_hunter.cpp:71): +70 pet attack power, mirrored by the beast copy.
        constexpr uint32 SPELL_PET_LEGGINGS_OF_BEAST_MASTERY = 38297;
        constexpr int32 LEGGINGS_PET_AP_BONUS = 70;

        // CreatureFamily.dbc petTalentType values.
        constexpr int32 PET_TALENT_TYPE_FEROCITY = 0;
        constexpr int32 PET_TALENT_TYPE_TENACITY = 1;
        constexpr int32 PET_TALENT_TYPE_CUNNING = 2;

        // Commanded spells (PET 4.9), declared by the BM DSL rows.
        constexpr uint32 SPELL_LUNGE_COMMAND = HunterData::SPELL_LUNGE_COMMAND;
        constexpr uint32 SPELL_RIP_THROAT_COMMAND = HunterData::SPELL_RIP_THROAT_COMMAND;
        constexpr uint32 SPELL_RAKE_COMMAND = HunterData::SPELL_RAKE_COMMAND;
        constexpr uint32 SPELL_POUNCE_COMMAND = HunterData::SPELL_POUNCE_COMMAND;
        constexpr uint32 SPELL_SAVAGE_REND_COMMAND = HunterData::SPELL_SAVAGE_REND_COMMAND;
        constexpr uint32 SPELL_LEAPING_TEAR_COMMAND = HunterData::SPELL_LEAPING_TEAR_COMMAND;
        constexpr uint32 SPELL_SWIPE_COMMAND = HunterData::SPELL_SWIPE_COMMAND;
        constexpr uint32 SPELL_MAUL_COMMAND = HunterData::SPELL_MAUL_COMMAND;
        constexpr uint32 SPELL_VENOM_BITE_COMMAND = HunterData::SPELL_VENOM_BITE_COMMAND;
        constexpr uint32 SPELL_VENOMOUS_CLOUD_COMMAND = HunterData::SPELL_VENOMOUS_CLOUD_COMMAND;
        constexpr uint32 SPELL_SAVAGE_STRIKES_COMMAND = HunterData::SPELL_SAVAGE_STRIKES_COMMAND;
        constexpr uint32 SPELL_SAVAGE_POUNCE_COMMAND = HunterData::SPELL_SAVAGE_POUNCE_COMMAND;
        constexpr uint32 SPELL_THRASH_COMMAND = HunterData::SPELL_THRASH_COMMAND;
        constexpr uint32 SPELL_CRUSHING_BLOW_COMMAND = HunterData::SPELL_CRUSHING_BLOW_COMMAND;
        constexpr uint32 SPELL_FEINT_STRIKE_COMMAND = HunterData::SPELL_FEINT_STRIKE_COMMAND;
        constexpr uint32 SPELL_AMBUSH_COMMAND = HunterData::SPELL_AMBUSH_COMMAND;

        // PET 4.2: the type defaults, then one row per family (32 hunter families).
        constexpr PetKit KIT_FEROCITY_DEFAULT =
            { SPELL_BITE, SPELL_DASH, SPELL_SAVAGE_STRIKES_COMMAND, SPELL_SAVAGE_POUNCE_COMMAND };
        constexpr PetKit KIT_TENACITY_DEFAULT =
            { SPELL_BITE, SPELL_LAST_STAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND };
        constexpr PetKit KIT_CUNNING_DEFAULT =
            { SPELL_CUNNING_SPIT, SPELL_BULLHEADED, SPELL_FEINT_STRIKE_COMMAND, SPELL_AMBUSH_COMMAND };
        constexpr PetKit KIT_NONE = { 0, 0, 0, 0 };

        PetKit const& GetTypeDefaultKit(PetType type)
        {
            switch (type)
            {
                case PetType::Ferocity:
                    return KIT_FEROCITY_DEFAULT;
                case PetType::Tenacity:
                    return KIT_TENACITY_DEFAULT;
                case PetType::Cunning:
                    return KIT_CUNNING_DEFAULT;
                default:
                    return KIT_NONE;
            }
        }

        PetType GetFamilyPetType(uint32 creatureFamily)
        {
            CreatureFamilyEntry const* family = sCreatureFamilyStore.LookupEntry(creatureFamily);
            if (!family)
                return PetType::None;

            switch (family->petTalentType)
            {
                case PET_TALENT_TYPE_FEROCITY:
                    return PetType::Ferocity;
                case PET_TALENT_TYPE_TENACITY:
                    return PetType::Tenacity;
                case PET_TALENT_TYPE_CUNNING:
                    return PetType::Cunning;
                default:
                    return PetType::None;
            }
        }

        // Families that differ from their type's default (PET 4.2; family id in the comment).
        std::unordered_map<uint32, PetKit> const& GetFamilyKits()
        {
            static std::unordered_map<uint32, PetKit> const kits =
            {
                // Ferocity
                // Wolf
                { 1, { SPELL_BITE, SPELL_FURIOUS_HOWL, SPELL_LUNGE_COMMAND, SPELL_RIP_THROAT_COMMAND } },
                // Cat
                { 2, { SPELL_CLAW, SPELL_ROAR_OF_COURAGE, SPELL_RAKE_COMMAND, SPELL_POUNCE_COMMAND } },
                // Raptor
                { 11, { SPELL_CLAW, SPELL_TEAR_ARMOR, SPELL_SAVAGE_REND_COMMAND, SPELL_LEAPING_TEAR_COMMAND } },
                // Carrion Bird
                { 7, KIT_FEROCITY_DEFAULT },
                // Hyena
                { 25, KIT_FEROCITY_DEFAULT },
                // Devilsaur
                { 39, KIT_FEROCITY_DEFAULT },
                // Core Hound
                { 45, KIT_FEROCITY_DEFAULT },
                // Tallstrider
                { 12, { SPELL_CLAW, SPELL_DASH, SPELL_SAVAGE_STRIKES_COMMAND, SPELL_SAVAGE_POUNCE_COMMAND } },
                // Spirit Beast
                { 46, { SPELL_CLAW, SPELL_DASH, SPELL_SAVAGE_STRIKES_COMMAND, SPELL_SAVAGE_POUNCE_COMMAND } },
                // Moth
                { 37, { SPELL_SMACK, SPELL_DASH, SPELL_SAVAGE_STRIKES_COMMAND, SPELL_SAVAGE_POUNCE_COMMAND } },
                // Wasp
                { 44, { SPELL_SMACK, SPELL_DASH, SPELL_SAVAGE_STRIKES_COMMAND, SPELL_SAVAGE_POUNCE_COMMAND } },
                // Tenacity
                // Bear
                { 4, { SPELL_CLAW, SPELL_MENACING_ROAR, SPELL_SWIPE_COMMAND, SPELL_MAUL_COMMAND } },
                // Boar
                { 5, KIT_TENACITY_DEFAULT },
                // Crocolisk
                { 6, KIT_TENACITY_DEFAULT },
                // Turtle
                { 21, KIT_TENACITY_DEFAULT },
                // Warp Stalker
                { 32, KIT_TENACITY_DEFAULT },
                // Worm
                { 42, KIT_TENACITY_DEFAULT },
                // Crab
                { 8, { SPELL_CLAW, SPELL_LAST_STAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND } },
                // Scorpid
                { 20, { SPELL_CLAW, SPELL_LAST_STAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND } },
                // Gorilla
                { 9, { SPELL_SMACK, SPELL_LAST_STAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND } },
                // Rhino
                { 43, { SPELL_SMACK, SPELL_LAST_STAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND } },
                // Cunning
                // Spider
                { 3, { SPELL_VENOM_SPIT, SPELL_WEB_PULL, SPELL_VENOM_BITE_COMMAND, SPELL_VENOMOUS_CLOUD_COMMAND } },
                // Bat
                { 24, KIT_CUNNING_DEFAULT },
                // Bird of Prey
                { 26, KIT_CUNNING_DEFAULT },
                // Wind Serpent
                { 27, KIT_CUNNING_DEFAULT },
                // Dragonhawk
                { 30, KIT_CUNNING_DEFAULT },
                // Ravager
                { 31, KIT_CUNNING_DEFAULT },
                // Sporebat
                { 33, KIT_CUNNING_DEFAULT },
                // Nether Ray
                { 34, KIT_CUNNING_DEFAULT },
                // Serpent
                { 35, KIT_CUNNING_DEFAULT },
                // Chimaera
                { 38, KIT_CUNNING_DEFAULT },
                // Silithid
                { 41, KIT_CUNNING_DEFAULT },
            };
            return kits;
        }

        // S1: The Beast Within 3/3 Mastery (live GetMasteryPercentage()), PET 9.1, BM A7. Kinds Pet and
        // StampedeBeast both get it; the caller has already resolved the kind.
        float S1Term(Player* owner, Unit* /*unit*/)
        {
            return GetBeastMasteryPetMasteryPct(owner);
        }

        // Recalculates every effect of an already-applied aura (RecalculateAmount() routes back through
        // ComputePetPassthroughAmount). Add-if-missing alone goes stale (warlock fix of 2026-09-28,
        // WarlockMechanics.cpp RecalculateAllEffects).
        void RecalculateAllEffects(Aura* aura)
        {
            if (!aura)
                return;

            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (AuraEffect* effect = aura->GetEffect(i))
                    effect->RecalculateAmount();
        }

        // The pet's own spell for a wanted id: the id itself, else the rank of the same chain it learned.
        uint32 FindKnownPetSpell(Pet const* pet, uint32 spellId)
        {
            if (pet->HasSpell(spellId))
                return spellId;

            uint32 const first = sSpellMgr->GetFirstSpellInChain(spellId);
            uint32 best = 0;
            uint8 bestRank = 0;
            for (auto const& [knownId, petSpell] : pet->m_spells)
            {
                if (petSpell.state == PETSPELL_REMOVED || sSpellMgr->GetFirstSpellInChain(knownId) != first)
                    continue;

                uint8 const rank = sSpellMgr->GetSpellRank(knownId);
                if (!best || rank > bestRank)
                {
                    best = knownId;
                    bestRank = rank;
                }
            }

            return best;
        }

        // Crit effects (aura 52 / 290) of `unit` whose spell the owner carries as well: raid buffs such as Furious
        // Howl, Leader of the Pack or Rampage land on both, and the owner's ranged crit already contains them.
        float GetSharedCritBonus(Player const* owner, Unit const* unit)
        {
            // Group-aware like the engine's own crit total (Unit::GetTotalAuraModifier): Furious Howl and Leader of the
            // Pack share an exclusive same-effect group, so both on one unit count once, not twice.
            auto const shared = [owner](AuraEffect const* auraEffect)
            {
                return auraEffect->GetId() != SPELL_HUNTER_PET_CRIT_HASTE && owner->HasAura(auraEffect->GetId());
            };

            return float(unit->GetTotalAuraModifier(SPELL_AURA_MOD_WEAPON_CRIT_PERCENT, shared) +
                unit->GetTotalAuraModifier(SPELL_AURA_MOD_CRIT_PCT, shared));
        }

        bool IsAutocastUtility(uint32 spellId)
        {
            return spellId == SPELL_FURIOUS_HOWL || spellId == SPELL_ROAR_OF_COURAGE || spellId == SPELL_TEAR_ARMOR ||
                spellId == SPELL_MENACING_ROAR;
        }

        // Owner attack power the pet inherits: 100% RAP + 100% SP (PET 5.3, same formula as the 34902 eff1 rebind).
        int32 ComputeOwnerAttackPowerShare(Player* owner)
        {
            float const rangedAp = std::max(0.0f, owner->GetTotalAttackPowerValue(RANGED_ATTACK));
            float const spellPower = std::max(0, owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_MAGIC));
            int32 amount = int32(rangedAp * HunterData::PET_AP_FROM_RAP_PCT / 100.0f +
                spellPower * HunterData::PET_AP_FROM_SP_PCT / 100.0f);
            if (owner->HasAura(SPELL_PET_LEGGINGS_OF_BEAST_MASTERY))
                amount += LEGGINGS_PET_AP_BONUS;

            return amount;
        }

        // S1b PT-5: every commanded spell (one kit slot each, 201720-201735) has one passive display spell at
        // id + COMMAND_DISPLAY_OFFSET (201858-201873). 201736 (Venomous Cloud's splash) is in no slot and has none.
        constexpr uint32 COMMANDED_SPELLS[] =
        {
            SPELL_LUNGE_COMMAND, SPELL_RIP_THROAT_COMMAND, SPELL_RAKE_COMMAND, SPELL_POUNCE_COMMAND,
            SPELL_SAVAGE_REND_COMMAND, SPELL_LEAPING_TEAR_COMMAND, SPELL_SWIPE_COMMAND, SPELL_MAUL_COMMAND,
            SPELL_VENOM_BITE_COMMAND, SPELL_VENOMOUS_CLOUD_COMMAND, SPELL_SAVAGE_STRIKES_COMMAND,
            SPELL_SAVAGE_POUNCE_COMMAND, SPELL_THRASH_COMMAND, SPELL_CRUSHING_BLOW_COMMAND, SPELL_FEINT_STRIKE_COMMAND,
            SPELL_AMBUSH_COMMAND,
        };

        // Learns the kit's two display spells and removes the other 14; true when the spellbook changed. Idempotent.
        // addSpell, not learnSpell: the caller sends the single PetSpellInitialize. The display spells are passive
        // (attributes 0x150), so addSpell casts their DUMMY self-aura and never puts them on the bar
        // (Pet.cpp addSpell), and they can't be cast; nothing here ever casts the real commanded spell.
        bool SyncCommandDisplaySpells(Pet* pet, PetKit const& kit)
        {
            bool changed = false;
            for (uint32 command : COMMANDED_SPELLS)
            {
                uint32 const display = command + uint32(HunterData::COMMAND_DISPLAY_OFFSET);
                bool const wanted = command == kit.commandI || command == kit.commandII;
                if (wanted)
                {
                    // The SpellInfo check keeps addSpell's "Non-existed in SpellStore" error off the 2 s tick when the
                    // data is not deployed.
                    if (!pet->HasSpell(display) && sSpellMgr->GetSpellInfo(display) &&
                        pet->addSpell(display, ACT_PASSIVE))
                        changed = true;
                }
                else if (pet->HasSpell(display) && pet->removeSpell(display, false))
                    changed = true;
            }

            return changed;
        }

        // S1b B6: the Stampede guardians (creature_template, hunter_bm_spells.py) must sit inside PET's
        // STAMPEDE_ENTRY_MIN/MAX, which GetPassthroughKind reads.
        constexpr bool IsStampedeEntry(uint32 entry)
        {
            return entry >= uint32(HunterData::STAMPEDE_ENTRY_MIN) && entry <= uint32(HunterData::STAMPEDE_ENTRY_MAX);
        }
        static_assert(IsStampedeEntry(HunterData::NPC_STAMPEDING_WOLF) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_CAT) && IsStampedeEntry(HunterData::NPC_STAMPEDING_RAPTOR) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_BEAR) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_SPIDER) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_BEAST_FEROCITY) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_BEAST_TENACITY) &&
            IsStampedeEntry(HunterData::NPC_STAMPEDING_BEAST_CUNNING),
            "Stampede guardians must sit inside STAMPEDE_ENTRY_MIN/MAX (GetPassthroughKind)");

        // S1b B5: Phoenix's Plume. 54114 is the stock Heart of the Phoenix revive (no HunterData:: name).
        constexpr uint32 SPELL_HEART_OF_THE_PHOENIX_REVIVE = 54114;
        constexpr uint32 SPELL_PHOENIX_S_PLUME_RANK3 = HunterData::SPELL_PHOENIX_S_PLUME;           // 201826
        constexpr uint32 SPELL_PHOENIX_S_PLUME_LOCKOUT = HunterData::SPELL_PHOENIX_S_PLUME_LOCKOUT; // 201810
    }

    PetType GetPetType(Unit const* petOrGuardian)
    {
        Creature const* creature = petOrGuardian ? petOrGuardian->ToCreature() : nullptr;
        CreatureTemplate const* creatureTemplate = creature ? creature->GetCreatureTemplate() : nullptr;
        return creatureTemplate ? GetFamilyPetType(creatureTemplate->family) : PetType::None;
    }

    PetKit const& GetPetKit(uint32 creatureFamily)
    {
        auto const& kits = GetFamilyKits();
        auto const itr = kits.find(creatureFamily);
        if (itr != kits.end())
            return itr->second;

        // Unknown family: its type's default (None gives an all-zero kit).
        return GetTypeDefaultKit(GetFamilyPetType(creatureFamily));
    }

    uint32 GetCommandSpell(Unit const* pet, uint8 slot)
    {
        Creature const* creature = pet ? pet->ToCreature() : nullptr;
        CreatureTemplate const* creatureTemplate = creature ? creature->GetCreatureTemplate() : nullptr;
        if (!creatureTemplate)
            return 0;

        PetKit const& kit = GetPetKit(creatureTemplate->family);
        return slot == 0 ? kit.commandI : slot == 1 ? kit.commandII : 0;
    }

    bool HasActivePet(Player const* owner)
    {
        Pet const* pet = owner ? owner->GetPet() : nullptr;
        return pet && pet->IsAlive() && pet->IsInWorld();
    }

    SpellCastResult CheckPetCanAct(Player* owner, Unit* target, SpellInfo const* petSpell)
    {
        Pet* pet = owner ? owner->GetPet() : nullptr;
        // Only a real hunter pet obeys (a warlock demon or a charmed beast does not).
        if (!pet || !pet->IsAlive() || pet->getPetType() != HUNTER_PET)
            return SPELL_FAILED_NO_PET;

        // Mini Spell::CheckCasterAuras on the pet, as spell_hun_masters_call does (spell_hunter.cpp:625-637). Roots do
        // not block: Kill Command and the commands teleport or cast from where the pet stands.
        uint32 const unitFlags = pet->GetUnitFlags();
        if (pet->GetCharmerGUID())
            return SPELL_FAILED_CHARMED;
        if (unitFlags & UNIT_FLAG_STUNNED)
            return SPELL_FAILED_STUNNED;
        if (unitFlags & UNIT_FLAG_FLEEING)
            return SPELL_FAILED_FLEEING;
        if (unitFlags & UNIT_FLAG_CONFUSED)
            return SPELL_FAILED_CONFUSED;

        // Kill Command: no pet reach (the pet teleports to the target).
        if (!petSpell)
            return SPELL_CAST_OK;

        if (!target)
            return SPELL_FAILED_BAD_TARGETS;

        float const range = petSpell->GetMaxRange(false, pet);
        if (petSpell->RangeEntry && (petSpell->RangeEntry->Flags & SPELL_RANGE_MELEE))
        {
            // S1a-5: the pet casts the command triggered, and Spell::CheckRange (strict) measures a melee-range spell
            // centre to centre with IsWithinMeleeRange, less 2 x MIN_MELEE_REACH (one with leeway). The plain
            // IsWithinDist below adds both object sizes, so it let through presses the pet's cast then refused, and
            // the Command's cooldown was spent on nothing. Same arithmetic here.
            float const margin = pet->GetLeewayBonusRange(target) > 0.0f ? MIN_MELEE_REACH : 2 * MIN_MELEE_REACH;
            if (!pet->IsWithinMeleeRange(target, std::max(range - margin, 0.0f)))
                return SPELL_FAILED_OUT_OF_RANGE;
        }
        else if (range > 0.0f && !pet->IsWithinDist(target, range))
            return SPELL_FAILED_OUT_OF_RANGE;

        if (!pet->IsWithinLOSInMap(target))
            return SPELL_FAILED_LINE_OF_SIGHT;

        return SPELL_CAST_OK;
    }

    void ApplyPetKit(Player* owner, Pet* pet)
    {
        if (!owner || !pet)
            return;

        uint32 wanted = 0;
        switch (GetPetType(pet))
        {
            case PetType::Ferocity:
                wanted = SPELL_FEROCITY_KIT;
                break;
            case PetType::Tenacity:
                wanted = SPELL_TENACITY_KIT;
                break;
            case PetType::Cunning:
                wanted = SPELL_CUNNING_KIT;
                break;
            default:
                break;
        }

        // Idempotent: the kits are passive owner auras, so a kit already on the owner is left alone.
        for (uint32 kit : { SPELL_FEROCITY_KIT, SPELL_TENACITY_KIT, SPELL_CUNNING_KIT })
            if (kit != wanted && owner->HasAura(kit))
                owner->RemoveAurasDueToSpell(kit);

        if (wanted && !owner->HasAura(wanted))
            owner->AddAura(wanted, owner);
    }

    void ApplyPetTypeStats(Guardian* guardian)
    {
        if (!guardian)
            return;

        uint32 swing = 0;
        switch (GetPetType(guardian))
        {
            case PetType::Ferocity:
                swing = HunterData::PET_SWING_MS_FEROCITY;
                break;
            case PetType::Tenacity:
                swing = HunterData::PET_SWING_MS_TENACITY;
                break;
            case PetType::Cunning:
                swing = HunterData::PET_SWING_MS_CUNNING;
                break;
            default:
                return;
        }

        // Stock forces a 2 s swing and level -/+ level/4 at that speed (Pet.cpp:1103, :1178); keep the DPS the same
        // for every type by scaling the base damage with the swing. UpdateAllStats() runs right after this hook
        // (Pet.cpp:1434-1436), so no stat update here.
        uint8 const level = guardian->GetLevel();
        guardian->SetAttackTime(BASE_ATTACK, swing);
        guardian->SetBaseWeaponDamage(BASE_ATTACK, MINDAMAGE, float(level - level / 4) * swing / 2000.0f);
        guardian->SetBaseWeaponDamage(BASE_ATTACK, MAXDAMAGE, float(level + level / 4) * swing / 2000.0f);
        guardian->SetStatPctModifier(UNIT_MOD_DAMAGE_MAINHAND, BASE_PCT, HunterData::PET_WHITE_SCALE_PCT / 100.0f);

        // A pet level-up: the pet is already in the world and the mirrors carry the old amounts. The load and summon
        // paths are covered by OnPetAddToWorld, Stampede beasts by S1's summon script.
        if (guardian->IsInWorld())
        {
            Unit* ownerUnit = guardian->GetOwner();
            if (Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr)
                RefreshPetPassthrough(owner, guardian);
        }
    }

    PassthroughKind GetPassthroughKind(Player const* owner, Unit const* unit)
    {
        if (!owner || !unit || !unit->HasUnitTypeMask(UNIT_MASK_MINION))
            return PassthroughKind::None;

        // Minion::GetOwner reads the GUID stored at construction. GetOwnerGUID is set only in SetMinion, which runs
        // after InitStatsForLevel and, on the taming paths, after AddToMap.
        Unit const* minionOwner = static_cast<Minion const*>(unit)->GetOwner();
        if (minionOwner != owner)
            return PassthroughKind::None;

        if (unit->IsPet())
        {
            bool const hunterPet = static_cast<Pet const*>(unit)->getPetType() == HUNTER_PET;
            return hunterPet ? PassthroughKind::Pet : PassthroughKind::None;
        }

        uint32 const entry = unit->GetEntry();
        if (entry >= uint32(HunterData::STAMPEDE_ENTRY_MIN) && entry <= uint32(HunterData::STAMPEDE_ENTRY_MAX))
            return PassthroughKind::StampedeBeast;

        return PassthroughKind::None;
    }

    void RefreshPetPassthrough(Player* owner, Unit* unit)
    {
        if (!owner || !unit)
            return;

        PassthroughKind const kind = GetPassthroughKind(owner, unit);
        if (kind == PassthroughKind::None)
            return;

        for (uint32 spellId :
            { SPELL_HUNTER_PET_VERSATILITY, SPELL_HUNTER_PET_CRIT_HASTE, SPELL_HUNTER_PET_DAMAGE_HOOK })
        {
            // The owner applies the aura (never the pet: a pet-cast copy would be saved to pet_aura), and every
            // effect is recalculated: an aura that is already present keeps whatever amount it had.
            Aura* aura = unit->GetAura(spellId, owner->GetGUID());
            if (!aura)
                aura = owner->AddAura(spellId, unit);

            RecalculateAllEffects(aura);
        }

        // S1b B4: the BM pet proc carrier, on the hunter pet only (Stampede beasts get none, BEAST-MASTERY §8.3).
        if (kind == PassthroughKind::Pet)
            ApplyBmPetAuras(owner, unit->ToPet());
    }

    void RefreshAllPassthrough(Player* owner)
    {
        if (!owner)
            return;

        // Copy first: the refresh applies auras, which can run stat updates that touch the control set.
        std::vector<Unit*> const controlled(owner->m_Controlled.begin(), owner->m_Controlled.end());
        for (Unit* unit : controlled)
            if (unit)
                RefreshPetPassthrough(owner, unit);
    }

    int32 ComputePetPassthroughAmount(Player* owner, Unit* target, uint32 spellId, uint8 effIndex)
    {
        if (!owner || !target)
            return 0;

        PassthroughKind const kind = GetPassthroughKind(owner, target);
        if (kind == PassthroughKind::None)
            return 0;

        switch (spellId)
        {
            case SPELL_HUNTER_PET_VERSATILITY:
            {
                float const versatility =
                    owner->GetVersatilityPercentage() * HunterData::PET_VERSATILITY_SHARE_PCT / 100.0f;
                switch (effIndex)
                {
                    case EFFECT_0:
                        return int32(std::lround(versatility));
                    case EFFECT_1:
                        return -int32(std::lround(versatility / 2.0f));
                    case EFFECT_2:
                        return int32(std::lround(versatility));
                    default:
                        return 0;
                }
            }
            case SPELL_HUNTER_PET_CRIT_HASTE:
            {
                if (effIndex == EFFECT_0)
                {
                    // A creature's crit is 5 + aura 52 + aura 290 (Unit.cpp:3743): the pet's total equals the owner's.
                    float const ownerCrit = owner->GetFloatValue(PLAYER_RANGED_CRIT_PERCENTAGE);
                    // Minus the crit auras both carry (raid buffs): the target has them itself.
                    float const shared =
                        (ownerCrit - 5.0f - GetSharedCritBonus(owner, target)) *
                        HunterData::PET_CRIT_SHARE_PCT / 100.0f;
                    int32 crit = std::max<int32>(0, int32(std::lround(shared)));
                    if (kind == PassthroughKind::StampedeBeast)
                        crit += int32(std::lround(GetPetCritBonusPct(owner->GetPet())));
                    return crit;
                }

                if (effIndex == EFFECT_1)
                {
                    float haste = 1.0f + owner->GetRatingBonusValue(CR_HASTE_RANGED) / 100.0f;
                    // Skip the auras the target carries itself (Bloodlust, Heroism): they already speed it up once.
                    auto const notOnTarget = [target](AuraEffect const* auraEffect)
                    {
                        return !target->HasAura(auraEffect->GetId());
                    };

                    // 192 has no stack-group check in its handler, so a plain product is right. 193 honours
                    // same-effect groups (HandleModCombatSpeedPct), and so does the group-aware multiplier: the
                    // owner's group-aware total over the pet's shared group-aware total (the crit mirror's shape),
                    // so a shared member never drops out before its group's maximum is taken.
                    for (AuraEffect const* auraEffect : owner->GetAuraEffectsByType(SPELL_AURA_MOD_MELEE_RANGED_HASTE))
                        if (notOnTarget(auraEffect))
                            haste *= 1.0f + auraEffect->GetAmount() / 100.0f;

                    float const petShared = target->GetTotalAuraMultiplier(SPELL_AURA_MELEE_SLOW,
                        [owner](AuraEffect const* auraEffect)
                        {
                            uint32 const spellId = auraEffect->GetId();
                            return spellId != SPELL_HUNTER_PET_CRIT_HASTE && owner->HasAura(spellId);
                        });
                    if (petShared > 0.0f)
                        haste *= owner->GetTotalAuraMultiplier(SPELL_AURA_MELEE_SLOW) / petShared;

                    return int32(std::lround((haste - 1.0f) * 100.0f * HunterData::PET_HASTE_SHARE_PCT / 100.0f));
                }

                return 0;
            }
            case SPELL_HUNTER_PET_DAMAGE_HOOK:
            {
                if (effIndex == EFFECT_0)
                {
                    float const s1Term = S1Term(owner, target);
                    if (kind == PassthroughKind::Pet)
                        return int32(std::lround(s1Term));

                    float const petPct = GetPetDamageDonePct(owner->GetPet());
                    return int32(std::lround(((1.0f + petPct / 100.0f) * (1.0f + s1Term / 100.0f) - 1.0f) * 100.0f));
                }

                if (effIndex == EFFECT_1 && kind == PassthroughKind::StampedeBeast)
                {
                    // Animal Handler and the other pet attack power percents ([R2-11 RESOLVED]); 1 without a pet.
                    Pet const* pet = owner->GetPet();
                    float const multiplier = pet ? pet->GetTotalAuraMultiplier(SPELL_AURA_MOD_ATTACK_POWER_PCT) : 1.0f;
                    return int32(std::lround(ComputeOwnerAttackPowerShare(owner) * multiplier));
                }

                return 0;
            }
            default:
                return 0;
        }
    }

    float GetPetDamageDonePct(Pet const* pet)
    {
        if (!pet)
            return 0.0f;

        float const multiplier = pet->GetTotalAuraMultiplier(SPELL_AURA_MOD_DAMAGE_PERCENT_DONE,
            [](AuraEffect const* auraEffect)
            {
                uint32 const spellId = auraEffect->GetId();
                return (auraEffect->GetMiscValue() & SPELL_SCHOOL_MASK_NORMAL) != 0 &&
                    spellId != SPELL_BESTIAL_WRATH && spellId != SPELL_HUNTER_PET_VERSATILITY &&
                    spellId != SPELL_HUNTER_PET_DAMAGE_HOOK;
            });
        return (multiplier - 1.0f) * 100.0f;
    }

    float GetPetCritBonusPct(Pet const* pet)
    {
        if (!pet)
            return 0.0f;

        // Leaves out 201701 itself and every crit aura the owner carries too (raid buffs): the owner's crit, which a
        // beast copies, already contains those.
        Player const* owner = pet->GetOwner();
        auto const own = [owner](AuraEffect const* auraEffect)
        {
            uint32 const spellId = auraEffect->GetId();
            return spellId != SPELL_HUNTER_PET_CRIT_HASTE && !(owner && owner->HasAura(spellId));
        };

        int32 const bonus = pet->GetTotalAuraModifier(SPELL_AURA_MOD_WEAPON_CRIT_PERCENT, own) +
            pet->GetTotalAuraModifier(SPELL_AURA_MOD_CRIT_PCT, own);
        return float(bonus);
    }

    void PinPetPowers(Pet* pet)
    {
        if (!pet || pet->getPetType() != HUNTER_PET)
            return;

        // Happy pets deal x1.25 white damage (StatSystem.cpp:1379), folded into PET_WHITE_SCALE_PCT; drain and the
        // death penalty are undone here (PET 4.7).
        HappinessState const before = pet->GetHappinessState();
        pet->SetPower(POWER_HAPPINESS, pet->GetMaxPower(POWER_HAPPINESS));
        pet->SetPower(POWER_FOCUS, pet->GetMaxPower(POWER_FOCUS));
        if (pet->GetHappinessState() != before)
            pet->UpdateDamagePhysical(BASE_ATTACK);
    }

    void SeatDefaultPetBar(Pet* pet)
    {
        // The load path adds the pet to the world before its spells load (Pet.cpp:410 vs the async callback), so the
        // 34902 tick does the real work there; this returns at once while the pet has no spells. learnSpell/addSpell
        // must never run on a pet that is still loading.
        if (!pet || pet->getPetType() != HUNTER_PET || !pet->IsInWorld() || !pet->IsAlive() ||
            pet->isBeingLoaded())
            return;

        Player* owner = pet->GetOwner();
        CharmInfo* charmInfo = pet->GetCharmInfo();
        CreatureTemplate const* creatureTemplate = pet->GetCreatureTemplate();
        if (!owner || owner->getClass() != CLASS_HUNTER || !charmInfo || !creatureTemplate)
            return;

        PetKit const& kit = GetPetKit(creatureTemplate->family);

        // S1b PT-5: the kit's Command I/II display spells, before the basic check (they don't depend on it). This is
        // the 34902 tick's path, so a tame or a family change is picked up within 2 s.
        bool changed = SyncCommandDisplaySpells(pet, kit);

        uint32 const basic = kit.basic ? FindKnownPetSpell(pet, kit.basic) : 0;
        if (!basic)
        {
            if (changed && owner->GetPet() == pet)
                owner->PetSpellInitialize();
            return;
        }

        // Stranded rule, the only re-seat trigger: the basic is on no spell slot of the bar (the engine learns the
        // lines in reverse order, so with five active spells for four slots the basic is the one left out). A basic
        // that is on the bar, in any of the 10 slots, means the player's own arrangement stands. Only while the pet
        // lacks 201703: once the bar has been seated (same pass), a basic the player removes stays removed.
        uint32 const firstBasic = sSpellMgr->GetFirstSpellInChain(basic);
        bool basicOnBar = false;
        for (uint8 slot = ACTION_BAR_INDEX_START; slot < ACTION_BAR_INDEX_END; ++slot)
        {
            UnitActionBarEntry const* entry = charmInfo->GetActionBarEntry(slot);
            if (entry && entry->IsActionBarForSpell() && entry->GetAction() &&
                sSpellMgr->GetFirstSpellInChain(entry->GetAction()) == firstBasic)
            {
                basicOnBar = true;
                break;
            }
        }

        // Once per pet: the marker is learned in the pass that seats the bar, so a later removal is the player's choice.
        if (!basicOnBar && !pet->HasSpell(SPELL_HUNTER_PET_AUTOCAST_MARKER))
        {
            // Wanted bar (PET 4.2): basic, utility, Growl, then Cower for Ferocity or Dash for the others. A spell
            // the pet does not know is skipped and the gap closed.
            uint32 const slotFour = GetPetType(pet) == PetType::Ferocity ? SPELL_COWER : SPELL_DASH;
            std::vector<uint32> wanted = { basic };
            for (uint32 spellId : { kit.utility, uint32(SPELL_GROWL), slotFour })
            {
                uint32 const known = spellId ? FindKnownPetSpell(pet, spellId) : 0;
                if (known && std::find(wanted.begin(), wanted.end(), known) == wanted.end())
                    wanted.push_back(known);
            }

            // Only slots that already hold a spell (or nothing) are written; command and reaction slots are never
            // touched. The spell slots 3-6 come first, then any other spell-type slot, so the basic is always seated
            // first and as many as fit are seated.
            std::vector<uint8> slots;
            for (uint8 slot = ACTION_BAR_INDEX_PET_SPELL_START; slot < ACTION_BAR_INDEX_PET_SPELL_END; ++slot)
                slots.push_back(slot);
            for (uint8 slot = ACTION_BAR_INDEX_START; slot < ACTION_BAR_INDEX_END; ++slot)
                if (slot < ACTION_BAR_INDEX_PET_SPELL_START || slot >= ACTION_BAR_INDEX_PET_SPELL_END)
                    slots.push_back(slot);

            size_t seated = 0;
            for (uint8 slot : slots)
            {
                UnitActionBarEntry const* entry = charmInfo->GetActionBarEntry(slot);
                bool const inSpellRange =
                    slot >= ACTION_BAR_INDEX_PET_SPELL_START && slot < ACTION_BAR_INDEX_PET_SPELL_END;
                if (!entry || !entry->IsActionBarForSpell())
                    continue;

                if (seated >= wanted.size())
                {
                    // Spell slots 3-6 beyond the wanted bar are emptied. A spell parked elsewhere is left alone unless
                    // it is one of the wanted spells (it would otherwise show twice).
                    bool const duplicate = entry->GetAction() &&
                        std::find(wanted.begin(), wanted.end(), entry->GetAction()) != wanted.end();
                    if (inSpellRange || duplicate)
                        charmInfo->SetActionBar(slot, 0, ACT_PASSIVE);
                    continue;
                }

                uint32 const spellId = wanted[seated++];
                SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
                auto const petSpell = pet->m_spells.find(spellId);
                ActiveStates type = ACT_PASSIVE;
                if (spellInfo && spellInfo->IsAutocastable())
                {
                    bool const autocast = petSpell != pet->m_spells.end() && petSpell->second.active == ACT_ENABLED;
                    type = autocast ? ACT_ENABLED : ACT_DISABLED;
                }

                charmInfo->SetActionBar(slot, spellId, type);
            }

            // A spell displaced from the bar keeps its autocast state on purpose: an autocast spell that is no longer
            // on the bar keeps casting until the player turns it off from the spellbook.
            changed = true;
        }

        // Autocast once per spell group, tracked by two persistent hidden passives (pet_spell), so tames, existing pets
        // and rank-ups are all covered and a player who later turns autocast off is respected:
        //  - 201703 marks the basic. A pet that lacks it and knows the basic gets autocast on the basic, then the
        //    marker.
        //  - 201752 marks the buff or debuff utility (Furious Howl, Roar of Courage, Tear Armor, Menacing Roar). The
        //    utilities are learned later than the basic (pet level 10 and 14), so they have their own marker, added
        //    only in the pass that handled the utility. Placeholder utilities and Web Pull never get it.
        // Web Pull, Dash, Last Stand, Bullheaded, Growl and Cower stay manual.
        // addSpell, not learnSpell: a marker is hidden, so no "learned" packet and no extra PetSpellInitialize (the
        // single resend below covers it). Passive, so addSpell casts it on the pet; type NORMAL, so _SaveSpells writes
        // it.
        auto const enableAutocastOnce = [&](uint32 spellId, uint32 marker)
        {
            if (!spellId || pet->HasSpell(marker) || !sSpellMgr->GetSpellInfo(marker))
                return;

            auto const petSpell = pet->m_spells.find(spellId);
            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
            if (petSpell == pet->m_spells.end() || !spellInfo || !spellInfo->IsAutocastable())
                return;

            if (petSpell->second.active != ACT_ENABLED)
            {
                pet->ToggleAutocast(spellInfo, true);
                charmInfo->SetSpellAutocast(spellInfo, true);
            }

            if (pet->addSpell(marker, ACT_PASSIVE))
                changed = true;
        };

        enableAutocastOnce(basic, SPELL_HUNTER_PET_AUTOCAST_MARKER);
        if (IsAutocastUtility(kit.utility))
            enableAutocastOnce(FindKnownPetSpell(pet, kit.utility), SPELL_HUNTER_PET_UTILITY_MARKER);

        if (changed && owner->GetPet() == pet)
            owner->PetSpellInitialize();
    }

    void ReapplyPetMonkeyAura(Player* owner, Pet* pet)
    {
        if (!owner || !pet || !owner->HasAura(SPELL_ASPECT_OF_THE_MONKEY) ||
            pet->HasAura(SPELL_ASPECT_OF_THE_MONKEY_PET))
            return;

        // 201605's implicit target 5 resolves through the owner's guardian-pet slot, which Pet::LoadFromDB and
        // Player::SummonPet fill (SetMinion) before AddToMap. The taming paths (Spell::EffectTameCreature,
        // EffectCreateTamedPet, Player::CreatePet) call AddToMap before SetMinion, so there the slot
        // is still empty and the aura goes on the pet directly. The owner is the caster either way: a
        // pet-cast copy would be saved to pet_aura and Pet::_LoadAuras (async, after AddToMap) would add a
        // second aura next to the owner-cast one on the next summon.
        if (owner->GetGuardianPet() == pet)
            owner->CastSpell(pet, SPELL_ASPECT_OF_THE_MONKEY_PET, true);
        else
            owner->AddAura(SPELL_ASPECT_OF_THE_MONKEY_PET, pet);
    }

    // ---- S1a: Beast Mastery (BEAST-MASTERY.md §8.4; S1a-HANDOFF A7, A8, A13) ----
    float GetBeastMasteryPetMasteryPct(Player const* owner)
    {
        if (!owner || !owner->HasAura(HunterData::SPELL_THE_BEAST_WITHIN_201857))
            return 0.0f;

        return owner->GetMasteryPercentage();
    }

    bool IsBeastCleaveExcluded(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;

        // The AoE commands and their splash, Stomp, Spiked Collar and Beast Cleave's own strike never feed it.
        switch (spellInfo->Id)
        {
            case HunterData::SPELL_LEAPING_TEAR_COMMAND:
            case HunterData::SPELL_SWIPE_COMMAND:
            case HunterData::SPELL_VENOMOUS_CLOUD_COMMAND:
            case HunterData::SPELL_VENOMOUS_CLOUD_SPLASH:
            case HunterData::SPELL_STOMP_PET:
            case HunterData::SPELL_SPIKED_COLLAR_STRIKE:
            case HunterData::SPELL_BEAST_CLEAVE_STRIKE:
                return true;
            default:
                return false;
        }
    }

    void RefreshSteadyShotTransforms(Player* player)
    {
        // An evicted transform aura never comes back by itself (C6); removal is automatic through the type-2 link.
        if (!player || !player->HasAura(SPELL_COBRA_SHOT_RANK3) || player->HasAura(SPELL_COBRA_SHOT_TRANSFORM))
            return;

        player->AddAura(SPELL_COBRA_SHOT_TRANSFORM, player);
    }

    void RecalculatePetTalentChannels(Player* player)
    {
        // The pet may not exist (hooks fire for every hunter, summon and load paths): nothing to do then.
        Pet* pet = player ? player->GetPet() : nullptr;
        if (!pet)
            return;

        for (uint32 spellId : { SPELL_TAMED_PET_PASSIVE_8875, SPELL_TAMED_PET_PASSIVE_19581,
            SPELL_TAMED_PET_PASSIVE_19591, SPELL_TAMED_PET_PASSIVE_34667 })
            if (Aura* aura = pet->GetAura(spellId))
                aura->RecalculateAmountOfEffects();
    }

    void OnBeastMasteryTalentsChanged(Player* player)
    {
        if (!player)
            return;

        // Channels before the passthrough: the beasts' copy reads the pet's damage auras.
        RefreshSteadyShotTransforms(player);
        RecalculatePetTalentChannels(player);
        RefreshAllPassthrough(player);
    }

    void CommandPetAttack(Pet* pet, Unit* target)
    {
        if (!pet || !target || pet->GetVictim() == target)
            return;

        // as the pet-action "attack" handler (PetHandler.cpp COMMAND_ATTACK); same sequence as
        // spell_hun_kill_command_rework
        CharmInfo* charmInfo = pet->GetCharmInfo();
        if (!charmInfo || !pet->IsAIEnabled || !pet->AI())
            return;

        pet->ClearUnitState(UNIT_STATE_FOLLOW);
        pet->AttackStop();
        charmInfo->SetIsCommandAttack(true);
        charmInfo->SetIsAtStay(false);
        charmInfo->SetIsFollowing(false);
        charmInfo->SetIsCommandFollow(false);
        charmInfo->SetIsReturning(false);
        pet->AI()->AttackStart(target);
    }

    void CollectBmSplashTargets(Player* hunter, Unit* source, Unit* center, float radius, uint32 maxTargets,
        std::vector<Unit*>& out)
    {
        if (!hunter || !source || !center)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, source, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, nearby, check);
        Cell::VisitObjects(center, searcher, radius);

        Pet* pet = hunter->GetPet();
        std::vector<Unit*> candidates;
        for (Unit* unit : nearby)
        {
            if (unit == center || !unit->IsAlive() || !source->IsValidAttackTarget(unit))
                continue;

            // BM §0.4: only enemies the hunter or its pet are fighting.
            if (!unit->IsInCombatWith(hunter) && !(pet && unit->IsInCombatWith(pet)))
                continue;

            candidates.push_back(unit);
        }

        std::sort(candidates.begin(), candidates.end(), [center](Unit const* a, Unit const* b)
        {
            return center->GetExactDistSq(a) < center->GetExactDistSq(b);
        });

        if (maxTargets && candidates.size() > maxTargets)
            candidates.resize(maxTargets);

        out.insert(out.end(), candidates.begin(), candidates.end());
    }

    // ---- S1b: Beast Mastery (S1b-HANDOFF B4-B7) ----
    uint32 GetStampedeEntry(uint32 creatureFamily)
    {
        switch (creatureFamily)
        {
            case CREATURE_FAMILY_WOLF:
                return HunterData::NPC_STAMPEDING_WOLF;
            case CREATURE_FAMILY_CAT:
                return HunterData::NPC_STAMPEDING_CAT;
            case CREATURE_FAMILY_RAPTOR:
                return HunterData::NPC_STAMPEDING_RAPTOR;
            case CREATURE_FAMILY_BEAR:
                return HunterData::NPC_STAMPEDING_BEAR;
            case CREATURE_FAMILY_SPIDER:
                return HunterData::NPC_STAMPEDING_SPIDER;
            default:
                break;
        }

        // Any other family: its type's beast (CreatureFamilyEntry::petTalentType 0 / 1 / 2); unknown -> Ferocity's.
        switch (GetFamilyPetType(creatureFamily))
        {
            case PetType::Tenacity:
                return HunterData::NPC_STAMPEDING_BEAST_TENACITY;
            case PetType::Cunning:
                return HunterData::NPC_STAMPEDING_BEAST_CUNNING;
            default:
                return HunterData::NPC_STAMPEDING_BEAST_FEROCITY;
        }
    }

    void ApplyBmPetAuras(Player* owner, Pet* pet)
    {
        // 201809 carries Culling the Herd and the Improved Aspect of the Viper capstone; its script checks the talents
        // at proc time, so every hunter pet carries it. The owner is the caster (L5): a pet-cast copy would be saved
        // to pet_aura and doubled on reload. Passive, so it is never saved and the 34902 tick re-adds it.
        if (!owner || !pet || pet->HasAura(HunterData::SPELL_BM_PET_PROCS))
            return;

        owner->AddAura(HunterData::SPELL_BM_PET_PROCS, pet);
    }

    void OnPhoenixPlumePetDeath(Unit* unit)
    {
        // Runs for every death in the world (HunterUnitScript): cheapest guard first, nothing allocated before the
        // owner qualifies.
        if (!unit || !unit->IsPet())
            return;

        Pet* pet = unit->ToPet();
        if (pet->getPetType() != HUNTER_PET)
            return;

        // Pet::GetOwner reads the stored Player*.
        Player* owner = pet->GetOwner();
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return;

        // A UnitScript has no Validate(): the three spells are checked once, on the first hunter-pet death, before
        // the aura checks (a missing 201826 would otherwise just never match). LOG_ERROR so it reaches the log (L17).
        static bool const spellsValid = []()
        {
            bool valid = true;
            for (uint32 spellId :
                { SPELL_HEART_OF_THE_PHOENIX_REVIVE, SPELL_PHOENIX_S_PLUME_LOCKOUT, SPELL_PHOENIX_S_PLUME_RANK3 })
            {
                if (!sSpellMgr->GetSpellInfo(spellId))
                {
                    LOG_ERROR("scripts.hunter",
                        "Hunter::OnPhoenixPlumePetDeath: spell {} does not exist, Phoenix's Plume revive disabled.",
                        spellId);
                    valid = false;
                }
            }

            return valid;
        }();
        if (!spellsValid)
            return;

        // Rank 3 (the capstone), in combat, and the 10-minute lockout aura is not up. The lockout is an aura, not a
        // cooldown: no Cooldown Haste, and Readiness can't reset it.
        if (!owner->HasAura(SPELL_PHOENIX_S_PLUME_RANK3) || !owner->IsInCombat() ||
            owner->HasAura(SPELL_PHOENIX_S_PLUME_LOCKOUT))
            return;

        // The event lives on the owner's own event list, so capturing the owner is safe (the list dies with it); the
        // pet is re-resolved by GUID inside, so a pet dismissed, stabled or replaced in that second is skipped.
        ObjectGuid const petGuid = pet->GetGUID();
        owner->m_Events.AddEventAtOffset([owner, petGuid]()
        {
            // A hunter who died or left the world in that second gets no revive (R-cpp m1).
            if (!owner->IsAlive() || !owner->IsInWorld())
                return;

            Pet* deadPet = owner->GetPet();
            if (!deadPet || deadPet->GetGUID() != petGuid || deadPet->IsAlive() ||
                owner->HasAura(SPELL_PHOENIX_S_PLUME_LOCKOUT))
                return;

            // The owner casts the stock revive on the dead pet, as spell_hun_pet_heart_of_the_phoenix does
            // (spell_hunter.cpp); EffectResurrectPet brings it back at the owner's side. The lockout starts only when
            // the revive cast went through, so a failed cast leaves the next death free to try again.
            if (owner->CastCustomSpell(SPELL_HEART_OF_THE_PHOENIX_REVIVE, SPELLVALUE_BASE_POINT0,
                HunterData::PHOENIX_PLUME_REVIVE_PCT, deadPet, TRIGGERED_FULL_MASK) == SPELL_CAST_OK)
                owner->CastSpell(owner, SPELL_PHOENIX_S_PLUME_LOCKOUT, true);
        }, Milliseconds(HunterData::PHOENIX_PLUME_REVIVE_DELAY_MS));
    }

    // ---- S2: Marksmanship (MARKSMANSHIP.md §4.2-§4.8, §5.10, §7; S2a-HANDOFF A2-A5, A11, A16, A20) ----
    /*
     * Mark state is per player, keyed by the player GUID (S2a A2). Map structure changes (find / emplace / erase) of
     * the outer map go through `markStateLock` because maps update on several threads (PaladinMechanics.cpp
     * precedent); a player's entry, and its per-target map, is only touched from that player's own map update, and
     * unordered_map entries keep their address across other keys' insertions. Removal paths (OnMarkRemoved,
     * RefreshFalconHaste, every read) are find-only (R5). The counter is the authority; the visible aura stack is
     * max(1, n) and is never read back (SetStackAmount returns early without a client update when the aura's
     * caster is null, SpellAuras.cpp:1033). Reads return 0 once the aura (by caster GUID) is gone, even if an entry
     * lingers (an aura removed while its caster was off the map never reaches OnMarkRemoved).
     */
    namespace
    {
        constexpr uint32 SPELL_SNIPERS_MARK = HunterData::SPELL_SNIPERS_MARK;           // 201920
        constexpr uint32 SPELL_VIPERS_MARK = HunterData::SPELL_VIPERS_MARK;             // 201921
        constexpr uint32 SPELL_FALCONS_MARK = HunterData::SPELL_FALCONS_MARK;           // 201922
        constexpr uint32 SPELL_FALCONS_HASTE = HunterData::SPELL_FALCONS_HASTE;         // 201942

        // Talent chains the mechanics read, highest rank first (each rank is a passive aura on the hunter).
        constexpr std::array<uint32, 3> KEEN_EYE_RANKS =
            { HunterData::SPELL_KEEN_EYE_201974, HunterData::SPELL_KEEN_EYE_201973, HunterData::SPELL_KEEN_EYE };
        constexpr std::array<uint32, 3> TRIANGULATION_RANKS = { HunterData::SPELL_TRIANGULATION_201978,
            HunterData::SPELL_TRIANGULATION_201977, HunterData::SPELL_TRIANGULATION };
        constexpr std::array<uint32, 3> MARKED_FOR_DEATH_RANKS = { HunterData::SPELL_MARKED_FOR_DEATH_53244,
            HunterData::SPELL_MARKED_FOR_DEATH_53243, HunterData::SPELL_MARKED_FOR_DEATH };
        constexpr std::array<uint32, 3> RAPID_KILLING_RANKS = { HunterData::SPELL_RAPID_KILLING_201981,
            HunterData::SPELL_RAPID_KILLING_34949, HunterData::SPELL_RAPID_KILLING };
        constexpr std::array<uint32, 2> LONE_SURVIVOR_RANKS =
            { HunterData::SPELL_LONE_SURVIVOR_19412, HunterData::SPELL_LONE_SURVIVOR };
        constexpr uint32 SPELL_LONE_SURVIVOR_BUFF = HunterData::SPELL_LONE_SURVIVOR_BUFF;   // 201950

        constexpr std::array<Mark, 3> ALL_MARKS = { Mark::Sniper, Mark::Viper, Mark::Falcon };

        struct MarkState
        {
            std::unordered_map<ObjectGuid, std::array<uint8, 3>> stacks;   // target GUID -> counter per Mark
            uint32 lastTripleConsumeMs = 0;                                 // GameTime ms of the last triple consume
            ObjectGuid convergenceCentre;                                   // S2b: Convergence's centre, per cast
            bool inStackWrite = false;                                      // M13 re-entrancy guard
        };

        std::mutex markStateLock;
        std::unordered_map<ObjectGuid, MarkState> markStates;

        MarkState* FindMarkState(ObjectGuid const& playerGuid)
        {
            std::lock_guard<std::mutex> lock(markStateLock);
            auto const itr = markStates.find(playerGuid);
            return itr != markStates.end() ? &itr->second : nullptr;
        }

        MarkState& GetOrCreateMarkState(ObjectGuid const& playerGuid)
        {
            std::lock_guard<std::mutex> lock(markStateLock);
            return markStates[playerGuid];
        }

        bool IsValidMark(Mark mark)
        {
            return mark < Mark::Max;
        }

        uint8 MarkIndex(Mark mark)
        {
            return static_cast<uint8>(mark);
        }

        // The player's own mark aura on the target (one per caster), nullptr when absent.
        Aura* GetMarkAura(Player const* player, Unit const* target, Mark mark)
        {
            uint32 const spellId = GetMarkSpellId(mark);
            return spellId ? target->GetAura(spellId, player->GetGUID()) : nullptr;
        }

        // The highest rank of a talent chain the player carries, nullptr without one.
        template <std::size_t N>
        SpellInfo const* GetKnownRank(Player const* player, std::array<uint32, N> const& ranksHighestFirst)
        {
            for (uint32 spellId : ranksHighestFirst)
                if (player->HasAura(spellId))
                    return sSpellMgr->GetSpellInfo(spellId);

            return nullptr;
        }

        // §4.1 favored actions (MARK_FAVORED_GAIN in total): Sniper's - Arcane Shot, Chimera Shot, Kill Shot;
        // Viper's - Serpent Sting; Falcon's - none. Keyed by the chain's first rank.
        bool IsFavoredAction(uint32 firstRankId, Mark mark)
        {
            switch (mark)
            {
                case Mark::Sniper:
                    return firstRankId == HunterData::SPELL_ARCANE_SHOT ||
                        firstRankId == HunterData::SPELL_CHIMERA_SHOT || firstRankId == HunterData::SPELL_KILL_SHOT;
                case Mark::Viper:
                    return firstRankId == HunterData::SPELL_SERPENT_STING;
                default:
                    return false;
            }
        }

        // The one stack writer (S2a A2, M13): counter first, then the visible stack inside the guard. The mark hooks
        // are AURA_EFFECT_HANDLE_REAL only, so SetStackAmount (REAPPLY | CHANGE_AMOUNT) never re-enters them; the
        // ASSERT turns a hook re-registered with REAPPLY into a crash on the first mark instead of a recursion.
        void WriteMarkStacks(Player* player, Unit* target, Mark mark, uint32 wanted)
        {
            if (!player || !target || !IsValidMark(mark))
                return;

            // No stacks without the aura (R5): a writer never creates state for a mark that is not up.
            Aura* aura = GetMarkAura(player, target, mark);
            if (!aura)
                return;

            uint8 const stacks = uint8(std::min<uint32>(wanted, MARK_MAX_STACKS));
            MarkState& state = GetOrCreateMarkState(player->GetGUID());
            ASSERT(!state.inStackWrite, "Hunter::WriteMarkStacks re-entered (mark hook registered with REAPPLY?)");
            state.stacks[target->GetGUID()][MarkIndex(mark)] = stacks;

            // The 3.3.5 client draws no number at 1, so 0 and 1 look the same (accepted, §9). Never ModStackAmount:
            // it refreshes the duration.
            uint8 const display = std::max<uint8>(1, stacks);
            if (aura->GetStackAmount() != display)
            {
                state.inStackWrite = true;
                aura->SetStackAmount(display);
                state.inStackWrite = false;
            }

            RefreshFalconHaste(player);
        }

        // Effect amount write that re-registers the spell mod only when the value moved (ChangeAmount marks the
        // amount as set by script, so a later recalculation does not reset it to the DBC 0).
        void SetEffectAmount(Aura* aura, uint8 effIndex, int32 amount)
        {
            if (AuraEffect* effect = aura->GetEffect(effIndex))
                if (effect->GetAmount() != amount)
                    effect->ChangeAmount(amount);
        }

        // §2.4 HUNTER_SHOTS (_masks.py, one HunterData const per dword): the hunter's shots, pet abilities excluded.
        // A stack-built flag96 and three ANDs: no allocation (B8 runs for every direct spell hit).
        bool IsHunterShot(SpellInfo const* spellInfo)
        {
            flag96 const shots(HunterData::HUNTER_SHOTS_MASK_0, HunterData::HUNTER_SHOTS_MASK_1,
                HunterData::HUNTER_SHOTS_MASK_2);
            return spellInfo->SpellFamilyName == SPELLFAMILY_HUNTER && (spellInfo->SpellFamilyFlags & shots);
        }
    }

    uint32 GetMarkSpellId(Mark mark)
    {
        switch (mark)
        {
            case Mark::Sniper:
                return SPELL_SNIPERS_MARK;
            case Mark::Viper:
                return SPELL_VIPERS_MARK;
            case Mark::Falcon:
                return SPELL_FALCONS_MARK;
            default:
                return 0;
        }
    }

    bool GetMarkForSpell(uint32 spellId, Mark& out)
    {
        switch (spellId)
        {
            case SPELL_SNIPERS_MARK:
                out = Mark::Sniper;
                return true;
            case SPELL_VIPERS_MARK:
                out = Mark::Viper;
                return true;
            case SPELL_FALCONS_MARK:
                out = Mark::Falcon;
                return true;
            default:
                return false;
        }
    }

    bool HasMark(Player const* player, Unit const* target, Mark mark)
    {
        return player && target && IsValidMark(mark) && GetMarkAura(player, target, mark);
    }

    uint8 GetMarkStacks(Player const* player, Unit const* target, Mark mark)
    {
        if (!HasMark(player, target, mark))
            return 0;

        MarkState const* state = FindMarkState(player->GetGUID());
        if (!state)
            return 0;

        auto const itr = state->stacks.find(target->GetGUID());
        return itr != state->stacks.end() ? itr->second[MarkIndex(mark)] : 0;
    }

    void AddMarkStacks(Player* player, Unit* target, Mark mark, uint8 amount)
    {
        if (!amount)
            return;

        WriteMarkStacks(player, target, mark, uint32(GetMarkStacks(player, target, mark)) + amount);
    }

    void SetMarkStacks(Player* player, Unit* target, Mark mark, uint8 stacks)
    {
        WriteMarkStacks(player, target, mark, stacks);
    }

    void OnMarkApplied(Player* player, Unit* target, Mark mark)
    {
        if (!player || !target || !IsValidMark(mark))
            return;

        // A fresh aura (a press, a Trick Shots copy) starts at counter 0; its visible stack is already 1, so the
        // stack is not written here (§4.2).
        MarkState& state = GetOrCreateMarkState(player->GetGUID());
        ASSERT(!state.inStackWrite, "Hunter::OnMarkApplied ran inside a stack write (hook registered with REAPPLY?)");
        state.stacks[target->GetGUID()][MarkIndex(mark)] = 0;

        RefreshFalconHaste(player);
    }

    void OnMarkRemoved(Player* player, Unit* target, Mark mark)
    {
        if (!player || !target || !IsValidMark(mark))
            return;

        // Find-only (paladin CR5): logout erased the state before the auras go.
        if (MarkState* state = FindMarkState(player->GetGUID()))
        {
            ASSERT(!state->inStackWrite, "Hunter::OnMarkRemoved ran inside a stack write (REAPPLY hook?)");

            auto const itr = state->stacks.find(target->GetGUID());
            if (itr != state->stacks.end())
            {
                itr->second[MarkIndex(mark)] = 0;

                // The removed aura has already left the target's applied list (Unit::_UnapplyAura erases it before
                // the effect handlers run), so this sees only the player's other marks.
                bool otherMarkUp = false;
                for (Mark other : ALL_MARKS)
                    if (other != mark && GetMarkAura(player, target, other))
                        otherMarkUp = true;

                if (!otherMarkUp)
                    state->stacks.erase(itr);
            }
        }

        RefreshFalconHaste(player);
    }

    void SetConvergenceCentre(Player* player, ObjectGuid centre)
    {
        if (!player)
            return;

        if (centre)
            GetOrCreateMarkState(player->GetGUID()).convergenceCentre = centre;
        else if (MarkState* state = FindMarkState(player->GetGUID()))
            state->convergenceCentre.Clear();
    }

    ObjectGuid GetConvergenceCentre(Player const* player)
    {
        MarkState const* state = player ? FindMarkState(player->GetGUID()) : nullptr;
        return state ? state->convergenceCentre : ObjectGuid::Empty;
    }

    uint8 MarkSnapshot::Count() const
    {
        return uint8(std::count(present.begin(), present.end(), true));
    }

    bool MarkSnapshot::Has(Mark mark) const
    {
        return IsValidMark(mark) && present[MarkIndex(mark)];
    }

    uint8 MarkSnapshot::Stacks(Mark mark) const
    {
        return Has(mark) ? stacks[MarkIndex(mark)] : 0;
    }

    MarkSnapshot ReadMarks(Player const* player, Unit const* target)
    {
        MarkSnapshot snapshot;
        if (!player || !target)
            return snapshot;

        for (Mark mark : ALL_MARKS)
        {
            uint8 const index = MarkIndex(mark);
            snapshot.present[index] = HasMark(player, target, mark);
            snapshot.stacks[index] = snapshot.present[index] ? GetMarkStacks(player, target, mark) : 0;
        }

        return snapshot;
    }

    void ConsumeMarks(Player* player, Unit* target, MarkSnapshot const& snapshot)
    {
        if (!player || !target)
            return;

        // AURA_REMOVE_BY_DEFAULT; each removal reaches OnMarkRemoved through spell_hun_mark's REAL remove hook.
        for (Mark mark : ALL_MARKS)
            if (snapshot.Has(mark))
                target->RemoveAurasDueToSpell(GetMarkSpellId(mark), player->GetGUID());
    }

    void OnHunterSpellCast(Player* player, Spell* spell)
    {
        // §4.3 / S2a A3, in this order: class, not triggered, not auto-repeat, hunter family, not a mark press (C9),
        // not Aimed Shot (Q18), then the primary unit target only.
        if (!player || !spell || player->getClass() != CLASS_HUNTER)
            return;

        if (spell->IsTriggered())
            return;

        if (spell->IsAutoRepeat())
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_HUNTER)
            return;

        Mark pressed = Mark::Max;
        if (GetMarkForSpell(spellInfo->Id, pressed))
            return;

        if (spellInfo->Id == HunterData::SPELL_AIMED_SHOT)
            return;

        // Fires at Spell.cpp:3956, before the completion CheckCast (R7, accepted). Ground-targeted casts have none.
        Unit* target = spell->m_targets.GetUnitTarget();
        if (!target || target == player || !player->IsValidAttackTarget(target))
            return;

        uint32 const firstRankId = spellInfo->GetFirstRankSpell()->Id;
        for (Mark mark : ALL_MARKS)
            if (HasMark(player, target, mark))
                AddMarkStacks(player, target, mark, IsFavoredAction(firstRankId, mark) ? MARK_FAVORED_GAIN : MARK_GAIN);
    }

    void RollKeenEye(Player* player, Unit* target)
    {
        if (!player || !target)
            return;

        // §5.10: the known rank's eff0 (10/20/30) is the chance; once per cast, no ICD.
        SpellInfo const* rank = GetKnownRank(player, KEEN_EYE_RANKS);
        if (!rank)
            return;

        MarkSnapshot const marks = ReadMarks(player, target);
        if (!marks.Count())
            return;

        if (!RollProcChance(player, float(rank->Effects[EFFECT_0].CalcValue(player))))
            return;

        for (Mark mark : ALL_MARKS)
            if (marks.Has(mark))
                AddMarkStacks(player, target, mark, KEEN_EYE_GAIN);
    }

    void RefreshFalconHaste(Player* player)
    {
        if (!player)
            return;

        // §4.5: the highest Falcon's stack among the player's live Falcon's Marks. Find-only.
        bool falconMarkUp = false;
        uint8 highest = 0;
        if (MarkState const* state = FindMarkState(player->GetGUID()))
        {
            for (auto const& [targetGuid, counters] : state->stacks)
            {
                Unit* target = ObjectAccessor::GetUnit(*player, targetGuid);
                if (!target || !GetMarkAura(player, target, Mark::Falcon))
                    continue;

                falconMarkUp = true;
                highest = std::max(highest, counters[MarkIndex(Mark::Falcon)]);
            }
        }

        if (!falconMarkUp)
        {
            player->RemoveAurasDueToSpell(SPELL_FALCONS_HASTE);
            return;
        }

        Aura* haste = player->GetAura(SPELL_FALCONS_HASTE, player->GetGUID());
        if (!haste)
        {
            // A player leaving the world gets no new aura.
            if (!player->IsInWorld())
                return;

            haste = player->AddAura(SPELL_FALCONS_HASTE, player);
            if (!haste)
                return;
        }

        // A 0-stack mark gives 0% (the buff stays up while a Falcon's Mark is).
        SetEffectAmount(haste, EFFECT_0, MARK_FALCON_HASTE_PER_STACK * highest);
    }

    void SetSniperCritHelper(Player* player, uint32 helperId, int32 critChance, int32 critDamagePct)
    {
        if (!player || !helperId)
            return;

        // §4.6 / S2a A5: hidden helper on the hunter (201948 Aimed Shot, 201949 Chimera Shot). A missing helper
        // already means 0 / 0, so a reset never adds it.
        Aura* helper = player->GetAura(helperId, player->GetGUID());
        if (!helper)
        {
            if (!critChance && !critDamagePct)
                return;

            helper = player->AddAura(helperId, player);
            if (!helper)
                return;
        }

        // eff0 ADD_FLAT_MODIFIER SPELLMOD_CRITICAL_CHANCE, eff1 ADD_PCT_MODIFIER SPELLMOD_CRIT_DAMAGE_BONUS.
        SetEffectAmount(helper, EFFECT_0, critChance);
        SetEffectAmount(helper, EFFECT_1, critDamagePct);
    }

    float GetSniperPayoffMultiplier(Player const* player)
    {
        if (!player)
            return 1.0f;

        // §4.7 / S2a A16: (1 + MfD eff0 / 100) x (1 + Mastery / 100, rank 3 only), two separate factors (L10: the
        // percent comes from the rank's SpellInfo).
        SpellInfo const* rank = GetKnownRank(player, MARKED_FOR_DEATH_RANKS);
        if (!rank)
            return 1.0f;

        float multiplier = 1.0f + rank->Effects[EFFECT_0].CalcValue(player) / 100.0f;
        if (rank->Id == HunterData::SPELL_MARKED_FOR_DEATH_53244)
            multiplier *= 1.0f + player->GetMasteryPercentage() / 100.0f;

        return multiplier;
    }

    float GetTriangulationMultiplier(Player const* player, uint8 marksConsumed)
    {
        if (!player || !marksConsumed)
            return 1.0f;

        // +3/6/9% (the rank's eff0) per mark consumed, a separate multiplier (§4.7).
        SpellInfo const* rank = GetKnownRank(player, TRIANGULATION_RANKS);
        if (!rank)
            return 1.0f;

        return 1.0f + rank->Effects[EFFECT_0].CalcValue(player) * marksConsumed / 100.0f;
    }

    float GetRapidKillingExecutePct(Player const* player)
    {
        // §6 row (2,3): the known rank's eff0 DUMMY (4/8/12). S2b's UnitScript is the only reader.
        SpellInfo const* rank = player ? GetKnownRank(player, RAPID_KILLING_RANKS) : nullptr;
        return rank ? float(rank->Effects[EFFECT_0].CalcValue(player)) : 0.0f;
    }

    void ApplyMarksmanshipTakenMods(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo)
    {
        // §10.4 / S2b B8, Rapid Killing's execute clause. Unit::CalculateSpellDamageTaken calls this for every direct
        // spell hit in the world, before armor and crit, so the cheapest checks come first and nothing allocates.
        // Shots only: a pet's hit has the pet as attacker (not a Player) and periodic ticks never reach the hook.
        if (damage <= 0 || !target || !attacker || !attacker->IsPlayer() || attacker->getClass() != CLASS_HUNTER)
            return;

        if (!spellInfo || !IsHunterShot(spellInfo))
            return;

        // The hook honours IGNORE_CASTER_MODIFIERS itself (druid_hooks.cpp precedent).
        if (spellInfo->HasAttribute(SPELL_ATTR3_IGNORE_CASTER_MODIFIERS))
            return;

        // RAPID_KILLING_HEALTH_PCT is a float: GetHealthPct, not HealthBelowPct(int32) (S2b 0-verify finding 7).
        if (target->GetHealthPct() >= RAPID_KILLING_HEALTH_PCT)
            return;

        // The known rank's eff0 (4/8/12), live through its SpellInfo; 0 without a rank.
        float const pct = GetRapidKillingExecutePct(attacker->ToPlayer());
        if (pct > 0.0f)
            AddPct(damage, pct);
    }

    void RefreshLoneSurvivor(Player* player)
    {
        // §10.3 / §10.4 / S2b B7. Callers: spell_hun_lone_survivor's 500 ms tick (19407 / 19412 eff2),
        // HunterPetScript::OnPetAddToWorld and HunterUnitScript::OnUnitDeath (hunter pet death).
        if (!player)
            return;

        SpellInfo const* rank = GetKnownRank(player, LONE_SURVIVOR_RANKS);
        if (!rank)
        {
            player->RemoveAurasDueToSpell(SPELL_LONE_SURVIVOR_BUFF);
            return;
        }

        // Only a live hunter pet counts (user ruling 3): HasActivePet checks alive and in world but not the type, so
        // a Classless player's warlock demon or a charmed pet leaves the buff up.
        Pet const* pet = player->GetPet();
        if (HasActivePet(player) && pet && pet->getPetType() == HUNTER_PET)
        {
            player->RemoveAurasDueToSpell(SPELL_LONE_SURVIVOR_BUFF);
            return;
        }

        // M12: the Classless value (eff1, 1/2%) on a Classless realm, else the Classic value (eff0, 5/10%).
        int32 const amount = rank->Effects[IsClasslessRealm() ? EFFECT_1 : EFFECT_0].CalcValue(player);

        Aura* buff = player->GetAura(SPELL_LONE_SURVIVOR_BUFF, player->GetGUID());
        if (!buff)
        {
            // A player leaving the world gets no new aura; AddAura refuses a dead player (non-passive buff).
            if (!player->IsInWorld())
                return;

            buff = player->AddAura(SPELL_LONE_SURVIVOR_BUFF, player);
            if (!buff)
                return;
        }

        // eff0 MOD_DAMAGE_PERCENT_DONE; rewritten only when the value moved (rank or realm change, a loaded aura).
        SetEffectAmount(buff, EFFECT_0, amount);
    }

    void NoteTripleConsume(Player* player)
    {
        if (player)
            GetOrCreateMarkState(player->GetGUID()).lastTripleConsumeMs = uint32(GameTime::GetGameTimeMS().count());
    }

    uint32 GetLastTripleConsumeMs(Player const* player)
    {
        MarkState const* state = player ? FindMarkState(player->GetGUID()) : nullptr;
        return state ? state->lastTripleConsumeMs : 0;
    }

    void ClearMarksmanshipState(Player* player)
    {
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(markStateLock);
        markStates.erase(player->GetGUID());
    }

    // ---- S3: Survival (SURVIVAL.md §0.19, §5.6, §5.7, §7.2, §10; S3a-HANDOFF A6, A7, A11, A12, A17, A18) ----
    /*
     * Explosive Shot recast carry (V3, N15): caster GUID -> target GUID -> the done-final amount each remaining blast
     * adds. Every access holds `explosiveCarryLock` for its whole duration (maps update on several threads, the
     * markStates precedent), no pointer into the map leaves the lock, and removal paths are find-only. No Unit* is
     * stored; the owning aura's AfterEffectRemove and ClearState (logout) remove the entries.
     */
    namespace
    {
        // Talent chains the S3 mechanics read, highest rank first (each rank is a passive aura on the hunter).
        constexpr std::array<uint32, 2> SHRAPNEL_RANKS = { SPELL_SHRAPNEL_R2, SPELL_SHRAPNEL_R1 };
        constexpr std::array<uint32, 3> POINT_OF_NO_ESCAPE_RANKS =
            { SPELL_POINT_OF_NO_ESCAPE_R3, SPELL_POINT_OF_NO_ESCAPE_R2, SPELL_POINT_OF_NO_ESCAPE_R1 };

        std::mutex explosiveCarryLock;
        std::unordered_map<ObjectGuid, std::unordered_map<ObjectGuid, uint32>> explosiveCarries;

        // Find-only erase of one (caster, target) entry; drops the caster's map once empty. Caller holds the lock.
        void EraseExplosiveShotCarryLocked(ObjectGuid const& casterGuid, ObjectGuid const& targetGuid)
        {
            auto const itr = explosiveCarries.find(casterGuid);
            if (itr == explosiveCarries.end())
                return;

            itr->second.erase(targetGuid);
            if (itr->second.empty())
                explosiveCarries.erase(itr);
        }

        // Stock Frost Trap Aura (the dynobj aura, eff0 MOD_DECREASE_SPEED): no HunterData:: name (S3b brief 10).
        constexpr uint32 SPELL_FROST_TRAP_AURA = 13810;

        /*
         * Burning Tar bank (C18, S3b B2; the Mage::AddIgniteDamage shape with a lock, stale line 10, N15): caster
         * GUID -> target GUID -> { damage still to pay, stacks shown }. Same rules as the carry above: every access
         * holds `burningTarLock` for its whole duration, no pointer into the map leaves the lock, removal is
         * find-only, no Unit* is stored. 202050's AfterEffectRemove and ClearState (logout) remove the entries.
         */
        struct BurningTarBank
        {
            uint32 remaining = 0;
            uint32 stacks = 0;
        };

        std::mutex burningTarLock;
        std::unordered_map<ObjectGuid, std::unordered_map<ObjectGuid, BurningTarBank>> burningTarBanks;

        // Find-only erase of one (caster, target) bank; drops the caster's map once empty. Caller holds the lock.
        void EraseBurningTarLocked(ObjectGuid const& casterGuid, ObjectGuid const& targetGuid)
        {
            auto const itr = burningTarBanks.find(casterGuid);
            if (itr == burningTarBanks.end())
                return;

            itr->second.erase(targetGuid);
            if (itr->second.empty())
                burningTarBanks.erase(itr);
        }

        // Find-only lookup; nullptr when there is no bank. Caller holds the lock and drops the pointer with it.
        BurningTarBank* FindBurningTarLocked(ObjectGuid const& casterGuid, ObjectGuid const& targetGuid)
        {
            auto const casterItr = burningTarBanks.find(casterGuid);
            if (casterItr == burningTarBanks.end())
                return nullptr;

            auto const targetItr = casterItr->second.find(targetGuid);
            return targetItr != casterItr->second.end() ? &targetItr->second : nullptr;
        }
    }

    void AddBurningTar(Player* hunter, Unit* target)
    {
        // §5.10 / S3b B2. Caller: OnDirectFireHit (target alive, Tarred by this hunter, a counted direct Fire hit).
        if (!hunter || !target || !hunter->IsInWorld() || !target->IsInWorld() || !target->IsAlive())
            return;

        SpellInfo const* burningTar = sSpellMgr->GetSpellInfo(SPELL_BURNING_TAR);
        if (!burningTar)
            return;

        // (1) The chunk: 202050's own eff0 (potency) through the done path as a DOT (RAP coefficient, Dark Hunting,
        // T.N.T., Mastery's SPELLMOD_DOT on d1 b27, Fire %, Versatility, Favored Prey), then Point of No Escape by
        // hand while this hunter's marker is up (§0.3: 202058's aura 271 mask skips d1 b27).
        int32 const base = burningTar->Effects[EFFECT_0].CalcValue(hunter);
        uint32 chunk = hunter->SpellDamageBonusDone(target, burningTar, uint32(std::max(base, 0)), DOT, EFFECT_0);
        if (target->GetAura(SPELL_POINT_OF_NO_ESCAPE_MARKER, hunter->GetGUID()))
            chunk = uint32(float(chunk) * (1.0f + GetPointOfNoEscapePct(hunter) / 100.0f));

        ObjectGuid const hunterGuid = hunter->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();

        // (2) Apply or refresh. The lock is never held across CastSpell / RefreshTimers / SetStackAmount (they can
        // run aura hooks, and 202050's remove hook takes the lock).
        Aura* aura = target->GetAura(SPELL_BURNING_TAR, hunterGuid);
        if (!aura)
        {
            // A new Burning Tar starts from an empty bank (a stale entry would otherwise be paid out again).
            {
                std::lock_guard<std::mutex> lock(burningTarLock);
                EraseBurningTarLocked(hunterGuid, targetGuid);
            }

            // 202050 has AttributesEx2 0x4 (stale line 12): the counted hit may come from a trap or splash the
            // hunter can't see.
            hunter->CastSpell(target, SPELL_BURNING_TAR, TRIGGERED_FULL_MASK);
            aura = target->GetAura(SPELL_BURNING_TAR, hunterGuid);
            if (!aura)
            {
                // Immune (or the target died in the cast): nothing banks.
                std::lock_guard<std::mutex> lock(burningTarLock);
                EraseBurningTarLocked(hunterGuid, targetGuid);
                return;
            }
        }
        else
        {
            // S3b 0-verify 4c: max duration (with mods) and duration back to 6 s, amplitude from current haste, tick
            // number 0, periodic timer kept (PERIODIC_DAMAGE), crit chance re-snapshotted; amount and stacks untouched.
            aura->RefreshTimers(false);
        }

        // (3) Bank the chunk. No damage cap; the sum saturates at uint32 max instead of wrapping.
        uint32 stacks = 0;
        uint32 remaining = 0;
        {
            std::lock_guard<std::mutex> lock(burningTarLock);
            BurningTarBank& bank = burningTarBanks[hunterGuid][targetGuid];
            bank.remaining = uint32(std::min<uint64>(uint64(bank.remaining) + chunk,
                uint64(std::numeric_limits<uint32>::max())));
            ++bank.stacks;
            stacks = bank.stacks;
            remaining = bank.remaining;
        }

        // Display only (0-verify 4e): SetStackAmount recalculates the amount (CalcValue x done x stacks), and the
        // next tick's SetAmount overwrites it with the bank's payout, so the stack never feeds the damage dealt.
        // Stale line 21: the engine's taken path still multiplies FLAT damage-taken auras by stack² (accepted).
        uint8 const display = uint8(std::min<uint32>(stacks, 255));
        if (aura->GetStackAmount() != display)
            aura->SetStackAmount(display);

        LOG_DEBUG("scripts.hunter", "Burning Tar: {} -> {} banked {} (stack {}), bank now {}",
            hunterGuid.ToString(), targetGuid.ToString(), chunk, stacks, remaining);
    }

    uint32 TakeBurningTarTick(Unit* caster, Unit* target, AuraEffect const* eff)
    {
        // §5.10 / S3b B2: called from 202050's OnEffectPeriodic, before the default tick reads GetAmount()
        // (SpellAuraEffects.cpp PeriodicTick runs the scripts first). The return becomes the tick's amount; the
        // engine then applies GetFinalTickBonusMultiplier() (1 + f on tick N, 1 otherwise) and the taken path.
        if (!caster || !target || !eff || !eff->GetBase())
            return 0;

        int32 const amplitude = eff->GetAmplitude();
        int32 const totalTicks = eff->GetTotalTicks();
        int32 const tickNumber = int32(eff->GetTickNumber());   // already incremented (0-verify 4d): 1..N

        // f exactly as GetFinalTickBonusMultiplier (SpellAuraEffects.cpp:7136-7144): the same integer
        // GetMaxDuration() - N * amplitude and the same float division. It is copied, not called, because the
        // function returns 1.0 on every tick but the last and the non-final payouts need f too.
        float f = 0.0f;
        if (totalTicks > 0 && amplitude > 0)
        {
            int32 const leftover = eff->GetBase()->GetMaxDuration() - totalTicks * amplitude;
            f = leftover > 0 ? float(leftover) / float(amplitude) : 0.0f;
        }

        ObjectGuid const casterGuid = caster->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();

        uint32 payout = 0;
        uint32 left = 0;
        bool finalTick = false;
        {
            std::lock_guard<std::mutex> lock(burningTarLock);
            BurningTarBank* bank = FindBurningTarLocked(casterGuid, targetGuid);
            if (!bank || !bank->remaining)
                return 0;

            // Tick N (or a tick past a shrunk N, or broken periodic data): the engine multiplies this by 1 + f, so
            // pay remaining / (1 + f) and empty the bank.
            finalTick = totalTicks <= 0 || amplitude <= 0 || tickNumber >= totalTicks;

            // Stranding guard (Gate+ race "haste change between refreshes"): RefreshTimers keeps the periodic timer
            // while it shortens the amplitude, so after a refresh with more haste the timer can exceed the new
            // amplitude and tick N can fall after expiry. When the next tick is not due before the aura runs out,
            // this tick (n < N, engine multiplier 1.0) pays the whole bank.
            bool const lastToFire = !finalTick && eff->GetPeriodicTimer() > eff->GetBase()->GetDuration();

            if (finalTick)
                payout = uint32(double(bank->remaining) / (1.0 + double(f)));
            else if (lastToFire)
                payout = bank->remaining;
            else
                payout = uint32(double(bank->remaining) / (double(totalTicks - tickNumber + 1) + double(f)));

            // SetAmount takes an int32.
            payout = std::min<uint32>(payout, uint32(std::numeric_limits<int32>::max()));

            if (finalTick || lastToFire)
                bank->remaining = 0;
            else
                bank->remaining -= std::min(payout, bank->remaining);

            left = bank->remaining;
        }

        // Bank side of the playtest's bank-vs-dealt check: `paid` is the amount before the engine's final-tick
        // multiplier, the taken path, crit and absorb (the combat log shows what was dealt).
        LOG_DEBUG("scripts.hunter", "Burning Tar: {} -> {} tick {}/{} (amp {}, f {:.3f}) paid {}{}, bank left {}",
            casterGuid.ToString(), targetGuid.ToString(), tickNumber, totalTicks, amplitude, f, payout,
            finalTick ? " (final, x(1+f) by the engine)" : "", left);

        return payout;
    }

    uint32 GetBurningTarRemaining(Unit const* caster, Unit const* target)
    {
        if (!caster || !target)
            return 0;

        std::lock_guard<std::mutex> lock(burningTarLock);
        BurningTarBank const* bank = FindBurningTarLocked(caster->GetGUID(), target->GetGUID());
        return bank ? bank->remaining : 0;
    }

    uint32 GetBurningTarStacks(Unit const* caster, Unit const* target)
    {
        if (!caster || !target)
            return 0;

        std::lock_guard<std::mutex> lock(burningTarLock);
        BurningTarBank const* bank = FindBurningTarLocked(caster->GetGUID(), target->GetGUID());
        return bank ? bank->stacks : 0;
    }

    void ClearBurningTar(ObjectGuid casterGuid, ObjectGuid targetGuid)
    {
        // 202050's AfterEffectRemove (REAL: expiry, death, dispel, despawn). Whatever is left is dropped.
        std::lock_guard<std::mutex> lock(burningTarLock);
        if (BurningTarBank const* bank = FindBurningTarLocked(casterGuid, targetGuid))
            if (bank->remaining)
                LOG_DEBUG("scripts.hunter", "Burning Tar: {} -> {} removed with {} unpaid",
                    casterGuid.ToString(), targetGuid.ToString(), bank->remaining);

        EraseBurningTarLocked(casterGuid, targetGuid);
    }

    void ClearBurningTarForCaster(ObjectGuid casterGuid)
    {
        // ClearState (logout). The caster's auras left behind tick for 0 and their remove hook finds nothing.
        std::lock_guard<std::mutex> lock(burningTarLock);
        auto const itr = burningTarBanks.find(casterGuid);
        if (itr != burningTarBanks.end())
            burningTarBanks.erase(itr);
    }

    bool TryLockAndLoad(Player* hunter, float baseChancePct)
    {
        // C49 / S3b B4: the periodic path's one roll (the ground-fire tick; the talent script rolls its own row).
        // 67544 is the shared 5 s ICD.
        if (!hunter || hunter->HasAura(SPELL_LOCK_AND_LOAD_MARKER))
            return false;

        if (!RollProcChance(hunter, baseChancePct))
            return false;

        TriggerLockAndLoad(hunter);
        return true;
    }

    void TriggerLockAndLoad(Player* hunter)
    {
        // C49 / S3b B4: one charge (56453, consumed by its own CAST row), the ICD marker, and Arcane Shot +
        // Explosive Shot (category 1173) off cooldown; Chain Reaction (rank 3) cuts Cluster Bombs by its eff2.
        if (!hunter || !hunter->IsInWorld())
            return;

        hunter->CastSpell(hunter, SPELL_LOCK_AND_LOAD_BUFF, TRIGGERED_FULL_MASK);
        hunter->CastSpell(hunter, SPELL_LOCK_AND_LOAD_MARKER, TRIGGERED_FULL_MASK);
        hunter->RemoveCategoryCooldown(CATEGORY_ARCANE_EXPLOSIVE);

        // "Known" = the rank's passive aura (GetKnownRank's rule). eff2 DUMMY bp 1999, live 2000 ms (V-m15).
        if (hunter->HasAura(SPELL_LOCK_AND_LOAD_R3))
            if (SpellInfo const* rank = sSpellMgr->GetSpellInfo(SPELL_LOCK_AND_LOAD_R3))
                ReduceSpellCooldown(hunter, SPELL_CLUSTER_BOMBS,
                    uint32(std::max(rank->Effects[EFFECT_2].CalcValue(hunter), 0)));
    }

    void TryShrapnel(Player* hunter, Unit* primary)
    {
        // §5.7 / A7. Called from the AfterHit of the 53301 hit and of each 53352 blast, after the splash.
        if (!hunter || !primary || !hunter->IsInWorld() || !primary->IsInWorld())
            return;

        // The known rank's eff0 (10 / 20%), live through its SpellInfo, scaled by Proc Chance.
        SpellInfo const* rank = GetKnownRank(hunter, SHRAPNEL_RANKS);
        if (!rank || !RollProcChance(hunter, float(rank->Effects[EFFECT_0].CalcValue(hunter))))
            return;

        // Candidates: alive enemies within SHRAPNEL_RADIUS_YD of the primary (its corpse on a killing blow, the same
        // tick) that are in combat with the hunter and in the primary's line of sight (202053 ignores LoS itself,
        // AttributesEx2 0x4, so the filter is from the primary, stale line 12), plus the primary while it lives
        // (brief resolution 2). Uniform pick; no candidate, no shrapnel.
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(primary, hunter, SHRAPNEL_RADIUS_YD);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(primary, nearby, check);
        Cell::VisitObjects(primary, searcher, SHRAPNEL_RADIUS_YD);

        std::vector<Unit*> candidates;
        if (primary->IsAlive() && hunter->IsValidAttackTarget(primary))
            candidates.push_back(primary);

        for (Unit* unit : nearby)
        {
            if (unit == primary || !unit->IsAlive() || !hunter->IsValidAttackTarget(unit))
                continue;

            if (!unit->IsInCombatWith(hunter) || !primary->IsWithinLOSInMap(unit))
                continue;

            candidates.push_back(unit);
        }

        if (candidates.empty())
            return;

        Unit* victim = Acore::Containers::SelectRandomContainerElement(candidates);
        hunter->CastSpell(victim, SPELL_SHRAPNEL_HIT, TRIGGERED_FULL_MASK);
    }

    void SetExplosiveShotCarry(Unit* caster, Unit* target, uint32 perBlast)
    {
        // A6: the 53301 AfterHit stores the per-blast carry of a recast (replaces any previous value); 0 stores
        // nothing and drops a stale entry.
        if (!caster || !target)
            return;

        std::lock_guard<std::mutex> lock(explosiveCarryLock);
        if (!perBlast)
        {
            EraseExplosiveShotCarryLocked(caster->GetGUID(), target->GetGUID());
            return;
        }

        explosiveCarries[caster->GetGUID()][target->GetGUID()] = perBlast;
    }

    uint32 GetExplosiveShotCarry(Unit const* caster, Unit const* target)
    {
        if (!caster || !target)
            return 0;

        std::lock_guard<std::mutex> lock(explosiveCarryLock);
        auto const casterItr = explosiveCarries.find(caster->GetGUID());
        if (casterItr == explosiveCarries.end())
            return 0;

        auto const targetItr = casterItr->second.find(target->GetGUID());
        return targetItr != casterItr->second.end() ? targetItr->second : 0;
    }

    void ClearExplosiveShotCarry(Unit const* caster, Unit const* target)
    {
        // The 53301 aura's AfterEffectRemove (REAL). A caster already gone was cleared by ClearState.
        if (!caster || !target)
            return;

        std::lock_guard<std::mutex> lock(explosiveCarryLock);
        EraseExplosiveShotCarryLocked(caster->GetGUID(), target->GetGUID());
    }

    void ClearExplosiveShotCarryForCaster(ObjectGuid casterGuid)
    {
        std::lock_guard<std::mutex> lock(explosiveCarryLock);
        auto const itr = explosiveCarries.find(casterGuid);
        if (itr != explosiveCarries.end())
            explosiveCarries.erase(itr);
    }

    float GetCreatureTypeDoneFactor(Unit const* caster, Unit const* target, SpellInfo const* spellInfo)
    {
        // §5.9 / S3b B5 (V-m4): the SPELL_AURA_MOD_DAMAGE_DONE_VERSUS term of Unit::SpellPctDamageModsDone
        // (Unit.cpp ~8313-8317), read the same way: the product of (100 + amount) / 100 over the caster's aura-168
        // effects whose misc mask has the target's creature-type bit, filtered by the spell's Attributes6 rule. The
        // signature carries no damage type, so the rule is evaluated as non-DOT; it only matters for a spell with
        // SPELL_ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS, which neither 13812 nor 202057 has.
        if (!caster || !target)
            return 1.0f;

        uint32 const creatureTypeMask = target->GetCreatureTypeMask();
        if (!creatureTypeMask)
            return 1.0f;

        return caster->GetTotalAuraMultiplier(SPELL_AURA_MOD_DAMAGE_DONE_VERSUS,
            [creatureTypeMask, spellInfo, caster](AuraEffect const* aurEff)
            {
                return (creatureTypeMask & aurEff->GetMiscValue()) &&
                    (!spellInfo || spellInfo->ValidateAttribute6SpellDamageMods(caster, aurEff, false));
            });
    }

    float GetPointOfNoEscapePct(Player const* hunter)
    {
        // The known rank's eff0 DUMMY (53298 / 53299 / 202106: 2 / 4 / 6), live through its SpellInfo; 0 without the
        // talent. S3a's only reader is Shrapnel's OnHit, behind the 202058 marker, which never exists before S3b.
        SpellInfo const* rank = hunter ? GetKnownRank(hunter, POINT_OF_NO_ESCAPE_RANKS) : nullptr;
        return rank ? float(rank->Effects[EFFECT_0].CalcValue(hunter)) : 0.0f;
    }

    void UpdatePointOfNoEscape(Unit* caster, Unit* target)
    {
        // §0.3 / §9.2 #18 / S3b B3. Callers: Tarred 202048's apply (REAL | REAPPLY: a Tar Bomb refresh is REAPPLY,
        // brief 4) and remove hooks, Frost Trap Aura 13810's apply and remove hooks. A removal hook runs after the
        // aura left the target's applied list (Unit.cpp _UnapplyAura), so the other source is read correctly.
        Player* hunter = GetOwningPlayer(caster);
        if (!hunter || !target)
            return;

        ObjectGuid const hunterGuid = hunter->GetGUID();

        if (!GetKnownRank(hunter, POINT_OF_NO_ESCAPE_RANKS))
        {
            target->RemoveAurasDueToSpell(SPELL_POINT_OF_NO_ESCAPE_MARKER, hunterGuid);
            return;
        }

        // The longer remaining time of this hunter's Tarred and Frost Trap Aura on the target (a permanent -1 never
        // occurs for either and counts as 0).
        int32 longest = 0;
        if (Aura const* tarred = target->GetAura(SPELL_TARRED, hunterGuid))
            longest = std::max(longest, tarred->GetDuration());

        if (Aura const* frostTrap = target->GetAura(SPELL_FROST_TRAP_AURA, hunterGuid))
            longest = std::max(longest, frostTrap->GetDuration());

        Aura* marker = target->GetAura(SPELL_POINT_OF_NO_ESCAPE_MARKER, hunterGuid);
        if (longest <= 0)
        {
            if (marker)
                target->RemoveAurasDueToSpell(SPELL_POINT_OF_NO_ESCAPE_MARKER, hunterGuid);
            return;
        }

        if (!marker)
        {
            // AddAura: no CheckCast, no LoS, no DR (stale line 12); it refuses a dead or immune target itself.
            if (!hunter->IsInWorld() || !target->IsInWorld() || !target->IsAlive())
                return;

            marker = hunter->AddAura(SPELL_POINT_OF_NO_ESCAPE_MARKER, target);
            if (!marker)
                return;
        }

        marker->SetMaxDuration(longest);
        marker->SetDuration(longest);
    }

    bool IsOncePerRangedCast(ProcEventInfo& eventInfo)
    {
        // §7.2 / A11, the aspect rule of SHARED §B6.2: Auto Shot is triggered, so it has no CAST phase and counts at
        // HIT; every other HIT event (one per Multi-Shot target) is rejected. The CAST phase never runs for a
        // triggered cast, so IsAspectRollSource decides there.
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        if (eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_HIT)
            return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_RANGED_AUTO_ATTACK) && spellInfo->Id == SPELL_AUTO_SHOT;

        if (eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST)
            return IsAspectRollSource(spellInfo);

        return false;
    }

    uint32 GetFavoredPreyBuff(uint32 creatureType)
    {
        // A11: CREATURE_TYPE 1-10 -> 202063-202072 (one spell_group 1242, exclusive); totem, non-combat pet and gas
        // cloud get none.
        switch (creatureType)
        {
            case CREATURE_TYPE_BEAST:
                return SPELL_FAVORED_PREY_BEAST;
            case CREATURE_TYPE_DRAGONKIN:
                return SPELL_FAVORED_PREY_DRAGONKIN;
            case CREATURE_TYPE_DEMON:
                return SPELL_FAVORED_PREY_DEMON;
            case CREATURE_TYPE_ELEMENTAL:
                return SPELL_FAVORED_PREY_ELEMENTAL;
            case CREATURE_TYPE_GIANT:
                return SPELL_FAVORED_PREY_GIANT;
            case CREATURE_TYPE_UNDEAD:
                return SPELL_FAVORED_PREY_UNDEAD;
            case CREATURE_TYPE_HUMANOID:
                return SPELL_FAVORED_PREY_HUMANOID;
            case CREATURE_TYPE_CRITTER:
                return SPELL_FAVORED_PREY_CRITTER;
            case CREATURE_TYPE_MECHANICAL:
                return SPELL_FAVORED_PREY_MECHANICAL;
            case CREATURE_TYPE_NOT_SPECIFIED:
                return SPELL_FAVORED_PREY_NOT_SPECIFIED;
            default:
                return 0;
        }
    }

    void ReduceCategoryCooldown(Player* player, uint32 category, uint32 ms)
    {
        // §0.19 / A12. Only spells the player knows (brief resolution 6: item and other stray entries share the map)
        // whose category matches. ReduceSpellCooldown re-sends the entry (Player::ResendSpellCooldown erases and
        // re-inserts it), so the ids are collected first and the map is never changed while it is iterated.
        if (!player || !category || !ms)
            return;

        std::vector<uint32> spellIds;
        for (auto const& entry : player->GetSpellCooldownMap())
        {
            if (!player->HasSpell(entry.first))
                continue;

            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(entry.first);
            if (spellInfo && spellInfo->GetCategory() == category)
                spellIds.push_back(entry.first);
        }

        for (uint32 spellId : spellIds)
            ReduceSpellCooldown(player, spellId, ms);
    }
}
