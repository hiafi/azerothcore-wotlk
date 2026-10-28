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

#include "ObjectAccessor.h"
#include "Player.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
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

// 8676 - Ambush (RG0b): from Stealth it can be used at range and teleports the rogue behind the target before the
// strike (P0 variant A). Stealth is removed in Spell::prepare before BeforeCast, so the stealth state is latched in
// CheckCast, which runs in prepare before the removal (an instant spell's cast(true) skips the second check). Out of
// Stealth (Shadowed included) the strike needs melee range. The caster may be a creature.
class spell_rog_ambush : public SpellScript
{
    PrepareSpellScript(spell_rog_ambush);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_AMBUSH_TELEPORT });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        _wasStealthed |= caster->HasStealthAura();
        _inMelee = caster->IsWithinMeleeRange(target);
        if (!_wasStealthed && !_inMelee)
            return SPELL_FAILED_OUT_OF_RANGE;

        return SPELL_CAST_OK;
    }

    void HandleBeforeCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target || !_wasStealthed || _inMelee)
            return;

        // The helper's 50000 yd range keeps the script cast from being range-checked.
        caster->CastSpell(target, RogueData::SPELL_AMBUSH_TELEPORT, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_rog_ambush::CheckCast);
        BeforeCast += SpellCastFn(spell_rog_ambush::HandleBeforeCast);
    }

    bool _wasStealthed = false;
    bool _inMelee = false;
};

// 203725 - Shiv (RG0b): the strike applies every Lethal poison the rogue holds at 100% (Rogue::ApplyLethalPoisons).
// The strike's own Lethal roll is blocked by the guard (rule 3a''); the Non-lethal poison rolls as on any ability.
// S1 Toxic Blade: the extra combo points are data (SPELLMOD_EFFECT2 on Shiv); the capstone (rank 2) debuffs the hit
// target before the poisons land, so Shiv's own Instant Poison already takes the bonus.
class spell_rog_shiv_rework : public SpellScript
{
    PrepareSpellScript(spell_rog_shiv_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_INSTANT_POISON_8680, RogueData::SPELL_DEADLY_POISON,
            RogueData::SPELL_WOUND_POISON, RogueData::SPELL_TOXIC_BLADE_DEBUFF });
    }

    // AfterHit runs only for a unit the strike hit (a miss, dodge or parry applies nothing).
    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster)
            return;

        if (caster->HasAura(RogueData::SPELL_TOXIC_BLADE_203817))
            caster->CastSpell(target, RogueData::SPELL_TOXIC_BLADE_DEBUFF, true);

        Rogue::ApplyLethalPoisons(caster, target, Rogue::PoisonSource::Shiv);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_shiv_rework::HandleAfterHit);
    }
};

// 203723 - Ghostly Veil (RG0b): the dodge buff counts melee attacks taken from others. Ghostly Strike's own cast makes
// the rogue a hit target of its self-effect (and so do Eviscerate-style self dummies), which would raise a taken-melee
// event on the rogue's own aura and burn a charge, so an event the owner caused is not a proc. Friendly melee-type
// spells (a party pet's Furious Howl) raise it too, so only hostile actors count.
class spell_rog_ghostly_veil : public AuraScript
{
    PrepareAuraScript(spell_rog_ghostly_veil);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* actor = eventInfo.GetActor();
        return actor && actor != GetUnitOwner() && !actor->IsFriendlyTo(GetUnitOwner());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_ghostly_veil::CheckProc);
    }
};

// 51723 - Fan of Knives (RG0b): one combo point per cast, on the rogue's hostile selection. The combo effect hits every
// unit in the area and AddComboPointGain moves the gain to each new unit, so the point would land on whichever target
// was processed last, where a finisher on the selected target can't see it.
class spell_rog_fan_of_knives : public SpellScript
{
    PrepareSpellScript(spell_rog_fan_of_knives);

    void HandleComboPoint(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);
        // AddComboPointGain adds up when handed the same unit again: award once per cast
        if (_awarded)
            return;
        _awarded = true;

        Unit* caster = GetCaster();
        Unit* target = ObjectAccessor::GetUnit(*caster, caster->GetTarget());
        if (!target || !caster->IsValidAttackTarget(target))
            target = GetHitUnit();

        // S3 Anticipation (U54 (c), S3a-REVIEW L1): the native award caps at 5; a builder stamp banks what it loses,
        // one update later, so a Seal Fate point from this cast's own crit counts in the base first (no-op without
        // Restless Blades). Combo points follow the rogue to a new target, so the held count is the base.
        if (Player* player = caster->ToPlayer())
            Rogue::StampFanOfKnivesGain(player, GetEffectValue());

        GetSpell()->AddComboPointGain(target, int8(GetEffectValue()));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_rog_fan_of_knives::HandleComboPoint, EFFECT_1,
            SPELL_EFFECT_ADD_COMBO_POINTS);
    }

    bool _awarded = false;
};

void AddSC_rogue_shared_spell_scripts()
{
    RegisterSpellScript(spell_rog_energy_haste);
    RegisterSpellAndAuraScriptPair(spell_rog_poison, spell_rog_poison_aura);
    RegisterSpellScript(spell_rog_ambush);
    RegisterSpellScript(spell_rog_shiv_rework);
    RegisterSpellScript(spell_rog_ghostly_veil);
    RegisterSpellScript(spell_rog_fan_of_knives);
}
