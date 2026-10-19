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

/*
 * Hunter rework - pet spell scripts (hunter-rework.SHARED.md §A4 / §C4).
 * Skeleton created by stage T2; H0-P1 adds Bloodthirsty (PET.md 7.5) and Web Pull (PET.md 8.3).
 */

#include "CharmInfo.h"
#include "Creature.h"
#include "HunterMechanics.h"
#include "Log.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

enum HunterPetSpells
{
    SPELL_HUN_DEATH_GRIP_JUMP = 57604, // stock Death Grip jump, not in the hunter DSL
    SPELL_HUN_PET_LEGGINGS_OF_BEAST_MASTERY = 38297 // Leggings of Beast Mastery (+52 Stamina, +70 AP, as stock)
};

// 53186, 53187 - Bloodthirsty (PET.md 7.5)
// Bound on both rank ids (no rank chain exists for pet spells). The aura's caster is the pet, so spell_proc applies
// no Proc Chance; the roll goes through Hunter::RollProcChance. Effect 0 still triggers the heal (54131).
class spell_hun_pet_bloodthirsty : public AuraScript
{
    PrepareAuraScript(spell_hun_pet_bloodthirsty);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_BLOODTHIRSTY_54131 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || damageInfo->GetDamage() == 0)
            return false;

        Unit* pet = GetUnitOwner();
        if (!pet || !pet->IsAlive() || eventInfo.GetActor() != pet)
            return false;

        // CR3: only a hunter's pet acts
        Player* owner = Hunter::GetOwningPlayer(pet);
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return false;

        // Effect 1 is a plain DUMMY (not an aura effect), so the aura has no AuraEffect for it: read the spell's value.
        float const chance = float(GetSpellInfo()->Effects[EFFECT_1].CalcValue(pet));
        return Hunter::RollProcChance(pet, chance);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_pet_bloodthirsty::CheckProc);
    }
};

// 201718 - Web Pull (PET.md 8.3)
class spell_hun_pet_web_pull : public SpellScript
{
    PrepareSpellScript(spell_hun_pet_web_pull);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_HUN_DEATH_GRIP_JUMP });
    }

    SpellCastResult CheckCast()
    {
        // CR3 / L6: gate here so a non-hunter pet pays no cooldown for a no-op
        Player* owner = Hunter::GetOwningPlayer(GetCaster());
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return SPELL_FAILED_DONT_REPORT;

        Unit* target = GetExplTargetUnit();
        if (!target)
            return SPELL_FAILED_BAD_TARGETS;

        // Death Grip's boss rule (spell_dk.cpp)
        if (Creature* creature = target->ToCreature())
            if (creature->isWorldBoss() || creature->IsDungeonBoss())
                return SPELL_FAILED_BAD_TARGETS;

        if (Player* player = target->ToPlayer())
            if (player->InArena() || player->InBattleground())
                return SPELL_FAILED_BAD_TARGETS;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* pet = GetCaster();
        Unit* target = GetHitUnit();
        if (!pet || !target || pet == target || !pet->IsAlive() || !target->IsAlive())
            return;

        // L6: the target may have died or turned friendly since the cast started
        if (!pet->IsValidAttackTarget(target))
            return;

        SpellInfo const* gripJump = sSpellMgr->GetSpellInfo(SPELL_HUN_DEATH_GRIP_JUMP);
        if (!gripJump)
            return;

        // Deterrence (deflect) stops the pull, as it does for Death Grip
        if (target->HasDetectSpellsAura() && !target->HasUnitState(UNIT_STATE_STUNNED))
            return;

        // Interrupt like Death Grip (immunity is checked against the Rogue Kick, as there)
        if (!target->IsImmunedToSpellEffect(sSpellMgr->GetSpellInfo(1766), EFFECT_0))
            target->InterruptNonMeleeSpells(false, 0, false);

        // Land just in front of the pet: its reach plus the target's, with a small margin
        float const dist = pet->GetCombatReach() + target->GetCombatReach() + 1.0f;
        Position const dest = pet->GetFirstCollisionPosition(dist, 0.0f);
        target->CastSpell(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), SPELL_HUN_DEATH_GRIP_JUMP, true);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_hun_pet_web_pull::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_hun_pet_web_pull::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 34902 - Hunter Pet Scaling 01 (PET.md 5.3, H0-P2 D3)
// Replaces spell_hun_generic_scaling on 34902 only (34903/34904 keep the stock class). Stamina 45% (Tenacity x1.20),
// AP = 100% RAP + 100% SP, spell power 0; no Hunter vs. Wild and no Wild Hunt term. The 2 s tick also drives the
// kit swap, the Focus pin, the default bar and the mirror refresh (the tame paths run before OnPetAddToWorld).
class spell_hun_pet_scaling_rework : public AuraScript
{
    PrepareAuraScript(spell_hun_pet_scaling_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
        {
            Hunter::SPELL_HUNTER_PET_VERSATILITY,
            Hunter::SPELL_HUNTER_PET_CRIT_HASTE,
            Hunter::SPELL_HUNTER_PET_DAMAGE_HOOK
        });
    }

    // The owner is null on the first calculation of a fresh tame (34902 is cast before SetMinion): amounts are 0
    Player* GetHunterOwner() const
    {
        Unit* pet = GetUnitOwner();
        if (!pet)
            return nullptr;

        Unit* owner = pet->GetOwner();
        if (!owner)
            return nullptr;

        Player* player = owner->ToPlayer();
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    void CalculateStatAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Player* owner = GetHunterOwner();
        if (!owner)
            return;

        float modifier = float(HunterData::PET_STAMINA_PCT) / 100.0f;
        if (Hunter::GetPetType(GetUnitOwner()) == Hunter::PetType::Tenacity)
            modifier *= 1.0f + float(HunterData::PET_TENACITY_STAMINA_BONUS_PCT) / 100.0f;

        Stats const stat = Stats(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
        amount = int32(std::max<int32>(0, owner->GetStat(stat)) * modifier);
        if (owner->HasAura(SPELL_HUN_PET_LEGGINGS_OF_BEAST_MASTERY))
            amount += 52;
    }

    void CalculateAPAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Player* owner = GetHunterOwner();
        if (!owner)
            return;

        float const rap = std::max<float>(0.0f, owner->GetTotalAttackPowerValue(RANGED_ATTACK));
        float const sp = std::max<int32>(0, owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_MAGIC));
        amount = int32(rap * float(HunterData::PET_AP_FROM_RAP_PCT) / 100.0f +
            sp * float(HunterData::PET_AP_FROM_SP_PCT) / 100.0f);
        if (owner->HasAura(SPELL_HUN_PET_LEGGINGS_OF_BEAST_MASTERY))
            amount += 70;
    }

    void CalculateSPAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        amount = 0;
        if (Player* owner = GetHunterOwner())
            owner->SetUInt32Value(PLAYER_PET_SPELL_POWER, 0);
    }

    void CalcPeriodic(AuraEffect const* /*aurEff*/, bool& isPeriodic, int32& amplitude)
    {
        isPeriodic = true;
        amplitude = 2 * IN_MILLISECONDS;
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        PreventDefaultAction();
        if (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT && aurEff->GetMiscValue() == STAT_STAMINA)
        {
            int32 currentAmount = aurEff->GetAmount();
            int32 newAmount = GetEffect(aurEff->GetEffIndex())->CalculateAmount(GetCaster());
            if (newAmount != currentAmount)
            {
                // keep health proportional when Stamina changes
                uint32 actStat = GetUnitOwner()->GetHealth();
                GetEffect(aurEff->GetEffIndex())->ChangeAmount(newAmount, false);
                GetUnitOwner()->SetHealth(std::min<uint32>(GetUnitOwner()->GetMaxHealth(), actStat));
            }
        }
        else
            GetEffect(aurEff->GetEffIndex())->RecalculateAmount();

        // The periodic fires once per effect: run the pet work once per tick. All of it is idempotent (C1).
        if (aurEff->GetEffIndex() != EFFECT_0)
            return;

        Pet* pet = GetUnitOwner() ? GetUnitOwner()->ToPet() : nullptr;
        if (!pet || pet->getPetType() != HUNTER_PET)
            return;

        Player* owner = GetHunterOwner();
        if (!owner)
            return;

        Hunter::ApplyPetKit(owner, pet);
        Hunter::PinPetPowers(pet);
        Hunter::SeatDefaultPetBar(pet);
        Hunter::RefreshAllPassthrough(owner);
        Hunter::ReapplyPetMonkeyAura(owner, pet);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(
            spell_hun_pet_scaling_rework::CalculateStatAmount, EFFECT_ALL, SPELL_AURA_MOD_STAT);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(
            spell_hun_pet_scaling_rework::CalculateAPAmount, EFFECT_ALL, SPELL_AURA_MOD_ATTACK_POWER);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(
            spell_hun_pet_scaling_rework::CalculateSPAmount, EFFECT_ALL, SPELL_AURA_MOD_DAMAGE_DONE);
        DoEffectCalcPeriodic += AuraEffectCalcPeriodicFn(
            spell_hun_pet_scaling_rework::CalcPeriodic, EFFECT_ALL, SPELL_AURA_ANY);
        OnEffectPeriodic += AuraEffectPeriodicFn(
            spell_hun_pet_scaling_rework::HandlePeriodic, EFFECT_ALL, SPELL_AURA_ANY);
    }
};

// 201700, 201701, 201702 - Pet Versatility, Pet Crit and Haste, Pet Damage Hook (PET.md 5.2-5.4, H0-P2 D4)
// Mirrors of the hunter's stats on the pet; the owner applies them, so the caster is the hunter.
class spell_hun_pet_passthrough : public AuraScript
{
    PrepareAuraScript(spell_hun_pet_passthrough);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
        {
            Hunter::SPELL_HUNTER_PET_VERSATILITY,
            Hunter::SPELL_HUNTER_PET_CRIT_HASTE,
            Hunter::SPELL_HUNTER_PET_DAMAGE_HOOK
        });
    }

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        amount = 0;

        Unit* caster = GetCaster();
        Player* owner = caster ? caster->ToPlayer() : nullptr;
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return;

        amount = Hunter::ComputePetPassthroughAmount(owner, GetUnitOwner(), GetId(), aurEff->GetEffIndex());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(
            spell_hun_pet_passthrough::CalculateAmount, EFFECT_ALL, SPELL_AURA_ANY);
    }
};

// 34026 - Kill Command (PET.md 6.3, H0-P2 D10)
// 34026 has no aura: effect 0 is the hunter's own damage, effect 1 (dummy) sends the pet in. Replaces
// spell_hun_kill_command on 34026 only.
class spell_hun_kill_command_rework : public SpellScript
{
    PrepareSpellScript(spell_hun_kill_command_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_KILL_COMMAND_TELEPORT, Hunter::SPELL_KILL_COMMAND_STRIKE });
    }

    SpellCastResult CheckCast()
    {
        // CR3: only a player acts
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return SPELL_CAST_OK;

        return Hunter::CheckPetCanAct(player, GetExplTargetUnit(), nullptr);
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        Unit* target = GetHitUnit();
        Pet* pet = player->GetPet();
        if (!target || !pet || pet->getPetType() != HUNTER_PET || !target->IsAlive() || !pet->IsAlive())
            return;

        // L6: the target may have died or turned friendly since the cast started
        if (!pet->IsValidAttackTarget(target))
            return;

        // CastSpell returns the SpellCastResult; on a failed cast, jump behind the target by hand
        if (pet->CastSpell(target, Hunter::SPELL_KILL_COMMAND_TELEPORT, TRIGGERED_FULL_MASK) != SPELL_CAST_OK)
        {
            LOG_ERROR("scripts.hunter", "Kill Command: teleport spell {} failed for pet {}, using NearTeleportTo",
                Hunter::SPELL_KILL_COMMAND_TELEPORT, pet->GetEntry());
            Position pos = target->GetNearPosition(pet->GetCombatReach() + target->GetCombatReach(), M_PI);
            pet->NearTeleportTo(pos);
        }

        // cosmetic strike
        pet->CastSpell(target, Hunter::SPELL_KILL_COMMAND_STRIKE, TRIGGERED_FULL_MASK);

        if (pet->GetVictim() == target)
            return;

        // as the pet-action "attack" handler (PetHandler.cpp COMMAND_ATTACK)
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

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_hun_kill_command_rework::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_hun_kill_command_rework::HandleDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

void AddSC_hunter_pet_spell_scripts()
{
    RegisterSpellScript(spell_hun_pet_bloodthirsty);
    RegisterSpellScript(spell_hun_pet_web_pull);
    RegisterSpellScript(spell_hun_pet_scaling_rework);
    RegisterSpellScript(spell_hun_pet_passthrough);
    RegisterSpellScript(spell_hun_kill_command_rework);
}
