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
 * Rogue rework - shared SpellScripts and AuraScripts (rogue-rework RG0a, RG0b). Bodies: RogueMechanics.
 */

#include "Player.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "Unit.h"

// 203700 - Energy Haste (hidden passive, granted by RoguePlayerScript).
// Effect 0 is SPELL_AURA_MOD_POWER_REGEN_PERCENT on POWER_ENERGY: its amount is the owner's spell haste in percent, so
// energy regenerates 10 x (1 + haste). The amount is computed on apply (a login starts right) and re-synced every
// 500 ms by effect 1 (SPELL_AURA_PERIODIC_DUMMY): changing it re-runs HandleModPowerRegen -> UpdateEnergyRegen, which
// writes the regen modifier the client predicts its bar from.
class spell_rog_energy_haste : public AuraScript
{
    PrepareAuraScript(spell_rog_energy_haste);

    void CalcRegenAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        amount = Rogue::GetEnergyHastePct(GetUnitOwner());
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (AuraEffect* regen = GetEffect(EFFECT_0))
            Rogue::SyncEnergyHaste(GetUnitOwner(), regen);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_energy_haste::CalcRegenAmount, EFFECT_0,
            SPELL_AURA_MOD_POWER_REGEN_PERCENT);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_energy_haste::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 203701-203706 - Instant / Deadly / Wound / Crippling / Mind-numbing / Anesthetic Poison, the self auras.
// Registered as a SpellScript + AuraScript pair under one name (the SpellScript class name, which is what
// spell_script_names binds). The cast half enforces the Lethal slot limit, the aura half rolls the poison on a
// qualifying hit (Rogue::PoisonRollAllowed + Rogue::RollPoison; the native proc roll always passes, spell_proc chance
// 100) and draws the weapon glow.
class spell_rog_poison : public SpellScript
{
    PrepareSpellScript(spell_rog_poison);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_INSTANT_POISON_8680, RogueData::SPELL_DEADLY_POISON,
            RogueData::SPELL_WOUND_POISON, RogueData::SPELL_CRIPPLING_POISON,
            RogueData::SPELL_MIND_NUMBING_POISON, RogueData::SPELL_ANESTHETIC_POISON });
    }

    // AfterHit: the new aura is already on the caster, so the slot count includes it; the kept aura is excluded from
    // the eviction.
    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        uint32 const auraId = GetSpellInfo()->Id;
        if (Rogue::GetPoisonSlot(auraId) == Rogue::PoisonSlot::Lethal)
            Rogue::EnforceLethalSlots(caster, auraId);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_poison::HandleAfterHit);
    }
};

class spell_rog_poison_aura : public AuraScript
{
    PrepareAuraScript(spell_rog_poison_aura);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* rogue = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        if (!rogue)
            return false;

        uint32 const auraId = GetId();
        return Rogue::PoisonRollAllowed(rogue, eventInfo, auraId) && Rogue::RollPoison(rogue, auraId, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* rogue = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Unit* target = eventInfo.GetActionTarget();
        if (!rogue || !target)
            return;

        // The payload id is stored in the aura row (effect 0's TriggerSpell); the default trigger is suppressed above
        // so that every application goes through the one helper.
        Rogue::ApplyPoison(rogue, target, aurEff->GetSpellInfo()->Effects[EFFECT_0].TriggerSpell, aurEff,
            Rogue::PoisonSource::Roll);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* rogue = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
            Rogue::ApplyPoisonGlow(rogue);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // The aura is already gone from the unit here, so the restore redraws the real values or the remaining glow
        if (Player* rogue = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
            Rogue::RestorePoisonGlow(rogue);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_poison_aura::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_rog_poison_aura::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
        AfterEffectApply += AuraEffectApplyFn(spell_rog_poison_aura::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_rog_poison_aura::HandleRemove, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_rogue_shared_spell_scripts()
{
    RegisterSpellScript(spell_rog_energy_haste);
    RegisterSpellAndAuraScriptPair(spell_rog_poison, spell_rog_poison_aura);
}
