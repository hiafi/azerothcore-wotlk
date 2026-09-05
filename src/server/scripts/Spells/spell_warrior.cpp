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

#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
/*
 * Scripts for spells with SPELLFAMILY_WARRIOR and SPELLFAMILY_GENERIC spells used by warrior players.
 * Ordered alphabetically using scriptname.
 * Scriptnames of files in this file should be prefixed with "spell_warr_".
 */

enum WarriorSpells
{
    SPELL_WARRIOR_INTERVENE_TRIGGER                 = 59667,
    SPELL_WARRIOR_SPELL_REFLECTION                  = 23920,
    SPELL_WARRIOR_IMPROVED_SPELL_REFLECTION_TRIGGER = 59725,
    SPELL_WARRIOR_BLOODTHIRST                       = 23885,
    SPELL_WARRIOR_BLOODTHIRST_DAMAGE                = 23881,
    SPELL_WARRIOR_CHARGE                            = 34846,
    SPELL_WARRIOR_DAMAGE_SHIELD_DAMAGE              = 59653,
    SPELL_WARRIOR_DEEP_WOUNDS_RANK_1                = 12162,
    SPELL_WARRIOR_DEEP_WOUNDS_RANK_2                = 12850,
    SPELL_WARRIOR_DEEP_WOUNDS_RANK_3                = 12868,
    SPELL_WARRIOR_DEEP_WOUNDS_RANK_PERIODIC         = 12721,
    SPELL_WARRIOR_EXECUTE                           = 20647,
    SPELL_WARRIOR_GLYPH_OF_EXECUTION                = 58367,
    SPELL_WARRIOR_GLYPH_OF_VIGILANCE                = 63326,
    SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_BUFF        = 65156,
    SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_TALENT      = 64976,
    SPELL_WARRIOR_LAST_STAND_TRIGGERED              = 12976,
    SPELL_WARRIOR_RETALIATION_DAMAGE                = 20240,
    SPELL_WARRIOR_SLAM                              = 50783,
    SPELL_WARRIOR_SUNDER_ARMOR                      = 58567,
    SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1   = 12723,
    SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_2   = 26654,
    SPELL_WARRIOR_TAUNT                             = 355,
    SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_1        = 46859,
    SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_2        = 46860,
    SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_1     = 64849,
    SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_2     = 64850,
    SPELL_WARRIOR_VIGILANCE_PROC                    = 50725,
    SPELL_WARRIOR_VIGILANCE_REDIRECT_THREAT         = 59665,
    SPELL_WARRIOR_WHIRLWIND_MAIN                    = 50622,
    SPELL_WARRIOR_WHIRLWIND_OFF                     = 44949,
    SPELL_WARRIOR_EXECUTE_R1                        = 5308,
    SPELL_WARRIOR_SECOND_WIND_HEAL_R1               = 29841,
    SPELL_WARRIOR_SECOND_WIND_HEAL_R2               = 29842,
    SPELL_WARRIOR_SECOND_WIND_UK                    = 42771,
    SPELL_WARRIOR_T10_PROT_4P_ABSORB                = 70845,
    SPELL_WARRIOR_GLYPH_OF_BLOCKING_BUFF            = 58374,
    SPELL_WARRIOR_T10_MELEE_4P_BONUS                = 70847,
    SPELL_WARRIOR_T10_MELEE_4P_EXTRA_CHARGE         = 70849,
    SPELL_WARRIOR_SLAM_GCD_REDUCED                  = 71072,
    SPELL_WARRIOR_EXECUTE_GCD_REDUCED               = 71069,
    SPELL_WARRIOR_WARRIORS_WRATH                    = 21887,
    // Protection Warrior rework (docs/prot_warrior_rework.md, New Spells/Auras), custom
    // (200000-209999 reserved block, apps/dbc-tools/source/spells/warrior.csv):
    SPELL_WARRIOR_STORMS_BULWARK                    = 200028,
    SPELL_WARRIOR_CONCUSSED                         = 200029,
    SPELL_WARRIOR_BLOODSTORM                        = 200030,
    // Protection Warrior rework phase 3 (docs/prot_warrior_rework.md) - real abilities these
    // talents hook into:
    SPELL_WARRIOR_THUNDER_CLAP                      = 6343,
    SPELL_WARRIOR_DEVASTATE                         = 20243,
    SPELL_WARRIOR_SHIELD_SLAM                       = 23922,
    SPELL_WARRIOR_SHIELD_BLOCK                      = 2565,
    SPELL_WARRIOR_REVENGE_R1                        = 6572,
    SPELL_WARRIOR_REVENGE_R6                        = 25288,
    SPELL_WARRIOR_LAST_STAND_ABILITY                = 12975,
    // 2236 is Unrelenting's *talent* id (talent_dbc), not a spell - the actual learned passive
    // aura HasAura() needs to check against is its single rank's real spell id, 200049.
    SPELL_WARRIOR_UNRELENTING                       = 200049,
    SPELL_WARRIOR_FOCUSED_RAGE_R3                   = 29792,
    SPELL_WARRIOR_INCITE_R3                         = 50687,
    SPELL_WARRIOR_SHOCKWAVE                         = 46968,
    SPELL_WARRIOR_SHIELD_COVER_R3                   = 200043,
    // Protection Warrior rework phase 3, new (200000-209999 reserved block,
    // apps/dbc-tools/source/spells/warrior_talents.csv):
    SPELL_WARRIOR_SHIELD_COVER_MAGIC_WARD           = 200061,
    SPELL_WARRIOR_SHIELD_DISCIPLINE_TC_BOOST        = 200064,
    SPELL_WARRIOR_THUNDER_CLAP_ECHO                 = 200065,
    SPELL_WARRIOR_THUNDERSTRUCK_ECHO_TRIGGER        = 200066,
    SPELL_WARRIOR_THUNDERSTRUCK_R3                  = 200053,
};

enum WarriorSpellIcons
{
    WARRIOR_ICON_ID_SUDDEN_DEATH                    = 1989,
    WARRIOR_ICON_ID_SECOND_WIND                     = 1697,
    // Protection Warrior rework phase 3: icons used to read a talent's passive marker aura live
    // (GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, icon, effIndex)), same idiom as
    // MageMechanics.cpp. Each is unique among this file's DUMMY-marker lookups by construction
    // (apps/dbc-tools/source/spells/warrior_talents.csv has no other SPELL_AURA_DUMMY effect to
    // collide with as of this rework).
    WARRIOR_ICON_ID_BLOOD_AND_THUNDER               = 245,
    WARRIOR_ICON_ID_REPRISAL                        = 1508,
    WARRIOR_ICON_ID_STORMS_BULWARK_TALENT           = 1941,
    WARRIOR_ICON_ID_SHIELD_DISCIPLINE               = 28,
    WARRIOR_ICON_ID_CRITICAL_BLOCK                  = 2778,
};

enum MiscSpells
{
    SPELL_PALADIN_BLESSING_OF_SANCTUARY             = 20911,
    SPELL_PALADIN_GREATER_BLESSING_OF_SANCTUARY     = 25899,
    SPELL_PRIEST_RENEWED_HOPE                       = 63944,
    SPELL_GEN_DAMAGE_REDUCTION_AURA                 = 68066,
    // custom (200000-209999 reserved block, apps/dbc-tools/source/spells/generic.csv):
    // grants baseline immunity to melee/ranged critical strikes; also applied by
    // Righteous Fury, Bear Form/Dire Bear Form, and Frost Presence
    SPELL_GEN_CRIT_IMMUNITY                         = 200000,
};

// Storm's Bulwark (docs/prot_warrior_rework.md, New Spells/Auras): every source stacks
// additively into one absorb pool capped at 50% of max HP, refreshing duration by default.
// Callers are expected to have already applied their own mastery scaling to `amount` - which
// talents grant Storm's Bulwark (Incite, Reprisal, the Storm's Bulwark talent, Shockwave) is
// phase 2/3 work.
void GrantStormsBulwark(Unit* caster, int32 amount, bool refreshDuration = true)
{
    int32 const cap = caster->CountPctFromMaxHealth(50);
    if (Aura* aura = caster->GetAura(SPELL_WARRIOR_STORMS_BULWARK))
    {
        if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            effect->SetAmount(std::min(effect->GetAmount() + amount, cap));
        if (refreshDuration)
            aura->RefreshDuration();
    }
    else
    {
        int32 basepoints = std::min(amount, cap);
        caster->CastCustomSpell(caster, SPELL_WARRIOR_STORMS_BULWARK, &basepoints, nullptr, nullptr, true);
    }
}

// 71 - Defensive Stance
class spell_warr_defensive_stance : public AuraScript
{
    PrepareAuraScript(spell_warr_defensive_stance);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_GEN_CRIT_IMMUNITY });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->CastSpell(GetTarget(), SPELL_GEN_CRIT_IMMUNITY, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_GEN_CRIT_IMMUNITY);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warr_defensive_stance::HandleApply, EFFECT_0, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_defensive_stance::HandleRemove, EFFECT_0, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

class spell_warr_mocking_blow : public SpellScript
{
    PrepareSpellScript(spell_warr_mocking_blow);

    void HandleOnHit()
    {
        if (Unit* target = GetHitUnit())
            if (target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_1))
                SetHitDamage(0);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warr_mocking_blow::HandleOnHit);
    }
};

enum VictoryRushEnum
{
    SPELL_VICTORIOUS    = 32216
};

class spell_warr_victory_rush : public SpellScript
{
    PrepareSpellScript(spell_warr_victory_rush);

    void HandleCast()
    {
        if (Unit* caster = GetCaster())
            caster->RemoveAurasDueToSpell(SPELL_VICTORIOUS);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_victory_rush::HandleCast);
    }
};

class spell_warr_intervene : public SpellScript
{
    PrepareSpellScript(spell_warr_intervene);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_INTERVENE_TRIGGER });
    }

    void HandleApplyAura(SpellEffIndex /*effIndex*/)
    {
        if (Unit* target = GetHitUnit())
            target->CastSpell((Unit*)nullptr, SPELL_WARRIOR_INTERVENE_TRIGGER, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_intervene::HandleApplyAura, EFFECT_1, SPELL_EFFECT_APPLY_AURA);
    }
};

class spell_warr_improved_spell_reflection : public AuraScript
{
    PrepareAuraScript(spell_warr_improved_spell_reflection);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SPELL_REFLECTION, SPELL_WARRIOR_IMPROVED_SPELL_REFLECTION_TRIGGER });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return eventInfo.GetSpellInfo() && eventInfo.GetActor() && eventInfo.GetSpellInfo()->Id == SPELL_WARRIOR_SPELL_REFLECTION;
    }

    void OnProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_MAX_TARGETS, aurEff->GetAmount());
        values.AddSpellMod(SPELLVALUE_RADIUS_MOD, 2000); // Base range = 100, final range = 20 value / 10000.0f = 0.2f
        eventInfo.GetActor()->CastCustomSpell(SPELL_WARRIOR_IMPROVED_SPELL_REFLECTION_TRIGGER, values, eventInfo.GetActor(), TRIGGERED_FULL_MASK, nullptr);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_improved_spell_reflection::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_improved_spell_reflection::OnProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

class spell_warr_improved_spell_reflection_trigger : public SpellScript
{
    PrepareSpellScript(spell_warr_improved_spell_reflection_trigger);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SPELL_REFLECTION });
    }

    void FilterTargets(std::list<WorldObject*>& unitList)
    {
        GetCaster()->RemoveAurasDueToSpell(SPELL_WARRIOR_SPELL_REFLECTION);
        unitList.sort(Acore::ObjectDistanceOrderPred(GetCaster()));
        while (unitList.size() > GetSpellValue()->MaxAffectedTargets)
            unitList.pop_back();
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_improved_spell_reflection_trigger::FilterTargets, EFFECT_0, TARGET_UNIT_CASTER_AREA_PARTY);
    }
};

class spell_warr_improved_spell_reflection_trigger_aura : public AuraScript
{
    PrepareAuraScript(spell_warr_improved_spell_reflection_trigger_aura);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes  /*mode*/)
    {
        if (!IsExpired())
        {
            // aura remove - remove auras from all party members
            std::list<Unit*> PartyMembers;
            GetUnitOwner()->GetPartyMembers(PartyMembers);
            for (std::list<Unit*>::iterator itr = PartyMembers.begin(); itr != PartyMembers.end(); ++itr)
            {
                if ((*itr)->GetGUID() != GetOwner()->GetGUID())
                    if (Aura* aur = (*itr)->GetAura(59725, GetCasterGUID()))
                    {
                        aur->SetDuration(0);
                        aur->Remove();
                    }
            }
        }
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_improved_spell_reflection_trigger_aura::HandleRemove, EFFECT_0, SPELL_AURA_REFLECT_SPELLS, AURA_EFFECT_HANDLE_REAL);
    }
};

// 12975 - Last Stand
class spell_warr_last_stand : public SpellScript
{
    PrepareSpellScript(spell_warr_last_stand);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_LAST_STAND_TRIGGERED });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        int32 healthModSpellBasePoints0 = int32(caster->CountPctFromMaxHealth(GetEffectValue()));
        caster->CastCustomSpell(caster, SPELL_WARRIOR_LAST_STAND_TRIGGERED, &healthModSpellBasePoints0, nullptr, nullptr, true, nullptr);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_warr_last_stand::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -12162 - Deep Wounds
class spell_warr_deep_wounds : public SpellScript
{
    PrepareSpellScript(spell_warr_deep_wounds);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_DEEP_WOUNDS_RANK_PERIODIC });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        int32 damage = std::max(GetEffectValue(), 0);
        Unit* caster = GetCaster();
        if (Unit* target = GetHitUnit())
        {
            // include target dependant auras
            damage = target->MeleeDamageBonusTaken(caster, damage, BASE_ATTACK, GetSpellInfo());
            // apply percent damage mods
            ApplyPct(damage, 16.0f * GetSpellInfo()->GetRank() / 6.0f);
            target->CastDelayedSpellWithPeriodicAmount(caster, SPELL_WARRIOR_DEEP_WOUNDS_RANK_PERIODIC, SPELL_AURA_PERIODIC_DAMAGE, damage, EFFECT_0);

            //caster->CastCustomSpell(target, SPELL_WARRIOR_DEEP_WOUNDS_RANK_PERIODIC, &damage, nullptr, nullptr, true);
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_deep_wounds::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -100 - Charge
class spell_warr_charge : public SpellScript
{
    PrepareSpellScript(spell_warr_charge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_TALENT,
                SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_BUFF,
                SPELL_WARRIOR_CHARGE
            });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        int32 chargeBasePoints0 = GetEffectValue();
        Unit* caster = GetCaster();
        caster->CastCustomSpell(caster, SPELL_WARRIOR_CHARGE, &chargeBasePoints0, nullptr, nullptr, true);

        // Juggernaut crit bonus
        if (caster->HasAura(SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_TALENT))
            caster->CastSpell(caster, SPELL_WARRIOR_JUGGERNAUT_CRIT_BONUS_BUFF, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_charge::HandleDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

// -1464 - Slam
class spell_warr_slam : public SpellScript
{
    PrepareSpellScript(spell_warr_slam);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SLAM });
    }

    void SendMiss(SpellMissInfo missInfo)
    {
        if (missInfo != SPELL_MISS_NONE)
        {
            if (Unit* caster = GetCaster())
            {
                if (Unit* target = GetHitUnit())
                {
                    caster->SendSpellMiss(target, SPELL_WARRIOR_SLAM, missInfo);
                }
            }
        }
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (GetHitUnit())
            GetCaster()->CastCustomSpell(SPELL_WARRIOR_SLAM, SPELLVALUE_BASE_POINT0, GetEffectValue(), GetHitUnit(), TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_warr_slam::SendMiss);
        OnEffectHitTarget += SpellEffectFn(spell_warr_slam::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// -58872 - Damage Shield
class spell_warr_damage_shield : public AuraScript
{
    PrepareAuraScript(spell_warr_damage_shield);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_DAMAGE_SHIELD_DAMAGE });
    }

    void OnProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        // % of amount blocked
        int32 damage = CalculatePct(int32(GetTarget()->GetShieldBlockValue()), aurEff->GetAmount());
        GetTarget()->CastCustomSpell(SPELL_WARRIOR_DAMAGE_SHIELD_DAMAGE, SPELLVALUE_BASE_POINT0, damage, eventInfo.GetProcTarget(), true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_damage_shield::OnProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -5308 - Execute
class spell_warr_execute : public SpellScript
{
    PrepareSpellScript(spell_warr_execute);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_EXECUTE, SPELL_WARRIOR_GLYPH_OF_EXECUTION });
    }

    void SendMiss(SpellMissInfo missInfo)
    {
        if (missInfo != SPELL_MISS_NONE)
        {
            if (Unit* caster = GetCaster())
            {
                if (Unit* target = GetHitUnit())
                {
                    caster->SendSpellMiss(target, SPELL_WARRIOR_EXECUTE, missInfo);
                }
            }
        }
    }

    void HandleEffect(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        if (Unit* target = GetHitUnit())
        {
            SpellInfo const* spellInfo = GetSpellInfo();
            int32 rageUsed = std::min<int32>(300 - spellInfo->CalcPowerCost(caster, SpellSchoolMask(spellInfo->SchoolMask)), caster->GetPower(POWER_RAGE));
            int32 newRage = std::max<int32>(0, caster->GetPower(POWER_RAGE) - rageUsed);

            // Sudden Death rage save
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_PROC_TRIGGER_SPELL, SPELLFAMILY_GENERIC, WARRIOR_ICON_ID_SUDDEN_DEATH, EFFECT_0))
            {
                int32 ragesave = aurEff->GetSpellInfo()->Effects[EFFECT_1].CalcValue() * 10;
                newRage = std::max(newRage, ragesave);
            }

            caster->SetPower(POWER_RAGE, uint32(newRage));
            // Glyph of Execution bonus
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_WARRIOR_GLYPH_OF_EXECUTION, EFFECT_0))
                rageUsed += aurEff->GetAmount() * 10;

            int32 bp = GetEffectValue() + int32(rageUsed * spellInfo->Effects[effIndex].DamageMultiplier + caster->GetTotalAttackPowerValue(BASE_ATTACK) * 0.2f);
            caster->CastCustomSpell(target, SPELL_WARRIOR_EXECUTE, &bp, nullptr, nullptr, true, nullptr, nullptr, GetOriginalCaster()->GetGUID());
        }
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_warr_execute::SendMiss);
        OnEffectHitTarget += SpellEffectFn(spell_warr_execute::HandleEffect, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 12809 - Concussion Blow
class spell_warr_concussion_blow : public SpellScript
{
    PrepareSpellScript(spell_warr_concussion_blow);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_CONCUSSED });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        SetHitDamage(CalculatePct(GetCaster()->GetTotalAttackPowerValue(BASE_ATTACK), GetEffectValue()));
    }

    // Protection Warrior rework phase 3: "Targets that cannot be stunned are instead Concussed"
    // (docs/prot_warrior_rework.md Row 5) - same IsImmunedToSpellEffect idiom as
    // spell_warr_mocking_blow. EFFECT_0 is the stun (SPELL_AURA_MOD_STUN); the engine already
    // silently skips applying it to an immune target, so this only needs to add the substitute.
    void HandleConcussed()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (target && target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_0))
            caster->CastSpell(target, SPELL_WARRIOR_CONCUSSED, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_concussion_blow::HandleDummy, EFFECT_2, SPELL_EFFECT_DUMMY);
        OnHit += SpellHitFn(spell_warr_concussion_blow::HandleConcussed);
    }
};

// 23881 - Bloodthirst
class spell_warr_bloodthirst : public SpellScript
{
    PrepareSpellScript(spell_warr_bloodthirst);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_BLOODTHIRST });
    }

    void HandleDamage(SpellEffIndex effIndex)
    {
        int32 damage = GetEffectValue();
        ApplyPct(damage, GetCaster()->GetTotalAttackPowerValue(BASE_ATTACK));

        if (Unit* target = GetHitUnit())
        {
            damage = GetCaster()->SpellDamageBonusDone(target, GetSpellInfo(), uint32(damage), SPELL_DIRECT_DAMAGE, effIndex);
            damage = target->SpellDamageBonusTaken(GetCaster(), GetSpellInfo(), uint32(damage), SPELL_DIRECT_DAMAGE);
        }
        SetHitDamage(damage);
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        int32 damage = GetEffectValue();
        GetCaster()->CastCustomSpell(GetCaster(), SPELL_WARRIOR_BLOODTHIRST, &damage, nullptr, nullptr, true, nullptr);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_bloodthirst::HandleDamage, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        OnEffectHit += SpellEffectFn(spell_warr_bloodthirst::HandleDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

// 23880 - Bloodthirst (Heal)
class spell_warr_bloodthirst_heal : public SpellScript
{
    PrepareSpellScript(spell_warr_bloodthirst_heal);

    void HandleHeal(SpellEffIndex /*effIndex*/)
    {
        if (SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(SPELL_WARRIOR_BLOODTHIRST_DAMAGE))
            SetEffectValue(GetCaster()->CountPctFromMaxHealth(spellInfo->Effects[EFFECT_1].CalcValue(GetCaster())));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_warr_bloodthirst_heal::HandleHeal, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

// 7384, 7887, 11584, 11585 - Overpower
class spell_warr_overpower : public SpellScript
{
    PrepareSpellScript(spell_warr_overpower);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_1,
            SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_1,
            SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_2,
            SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_2
            });
    }

    void HandleEffect(SpellEffIndex /*effIndex*/)
    {
        uint32 spellId = 0;
        if (GetCaster()->HasAura(SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_1))
            spellId = SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_1;
        else if (GetCaster()->HasAura(SPELL_WARRIOR_UNRELENTING_ASSAULT_RANK_2))
            spellId = SPELL_WARRIOR_UNRELENTING_ASSAULT_TRIGGER_2;

        if (!spellId)
            return;

        if (Player* target = GetHitPlayer())
            if (target->HasUnitState(UNIT_STATE_CASTING))
                target->CastSpell(target, spellId, true, 0, 0, GetCaster()->GetGUID());
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_overpower::HandleEffect, EFFECT_0, SPELL_EFFECT_ANY);
    }
};

// 5246 - Intimidating Shout
class spell_warr_intimidating_shout : public SpellScript
{
    PrepareSpellScript(spell_warr_intimidating_shout);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove(GetExplTargetWorldObject());
        uint32 maxTargets = GetSpellInfo()->MaxAffectedTargets;
        if (targets.size() > maxTargets)
            targets.resize(maxTargets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_intimidating_shout::FilterTargets, EFFECT_1, TARGET_UNIT_SRC_AREA_ENEMY);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_intimidating_shout::FilterTargets, EFFECT_2, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// -772 - Rend
class spell_warr_rend : public AuraScript
{
    PrepareAuraScript(spell_warr_rend);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        if (Unit* caster = GetCaster())
        {
            canBeRecalculated = false;

            // $0.2 * (($MWB + $mwb) / 2 + $AP / 14 * $MWS) bonus per tick
            float ap = caster->GetTotalAttackPowerValue(BASE_ATTACK);
            int32 mws = caster->GetAttackTime(BASE_ATTACK);
            float mwbMin = 0.f;
            float mwbMax = 0.f;
            for (uint8 i = 0; i < MAX_ITEM_PROTO_DAMAGES; ++i)
            {
                mwbMin += caster->GetWeaponDamageRange(BASE_ATTACK, MINDAMAGE, i);
                mwbMax += caster->GetWeaponDamageRange(BASE_ATTACK, MAXDAMAGE, i);
            }

            float mwb = ((mwbMin + mwbMax) / 2 + ap * mws / 14000) * 0.2f;
            amount += int32(caster->ApplyEffectModifiers(GetSpellInfo(), aurEff->GetEffIndex(), mwb));

            // "If used while your target is above 75% health, Rend does 35% more damage."
            // as for 3.1.3 only ranks above 9 (wrong tooltip?)
            if (GetSpellInfo()->GetRank() >= 9)
            {
                if (GetUnitOwner()->HasAuraState(AURA_STATE_HEALTH_ABOVE_75_PERCENT, GetSpellInfo(), caster))
                    AddPct(amount, GetSpellInfo()->Effects[EFFECT_2].CalcValue(caster));
            }
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_rend::CalculateAmount, EFFECT_0, SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// 64380, 65941 - Shattering Throw
class spell_warr_shattering_throw : public SpellScript
{
    PrepareSpellScript(spell_warr_shattering_throw);

    void HandleScript(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);

        // remove shields, will still display immune to damage part
        if (Unit* target = GetHitUnit())
            target->RemoveAurasWithMechanic(1ULL << MECHANIC_IMMUNE_SHIELD, AURA_REMOVE_BY_ENEMY_SPELL);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_shattering_throw::HandleScript, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// 12328, 18765, 35429 - Sweeping Strikes
class spell_warr_sweeping_strikes : public AuraScript
{
    PrepareAuraScript(spell_warr_sweeping_strikes);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1, SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_2 });
    }

    bool Load() override
    {
        _procTargetGUID.Clear();
        return true;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* actor = eventInfo.GetActor();
        if (!actor)
            return false;

        if (SpellInfo const* spellInfo = eventInfo.GetSpellInfo())
        {
            switch (spellInfo->Id)
            {
                case SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1:
                case SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_2:
                case SPELL_WARRIOR_WHIRLWIND_OFF:
                    return false;
                case SPELL_WARRIOR_WHIRLWIND_MAIN:
                {
                    if (actor->HasSpellCooldown(SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1))
                        return false;

                    break;
                }
                default:
                    break;
            }
        }

        Unit* procTarget = actor->SelectNearbyNoTotemTarget(eventInfo.GetProcTarget());
        if (procTarget)
            _procTargetGUID = procTarget->GetGUID();

        return procTarget != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* procTarget = ObjectAccessor::GetUnit(*GetTarget(), _procTargetGUID);
        if (!procTarget)
            return;

        if (DamageInfo* damageInfo = eventInfo.GetDamageInfo())
        {
            SpellInfo const* spellInfo = damageInfo->GetSpellInfo();
            if (spellInfo && spellInfo->Id == SPELL_WARRIOR_EXECUTE
                && !procTarget->HasAuraState(AURA_STATE_HEALTHLESS_20_PERCENT))
            {
                // If triggered by Execute (while target is not under 20% hp) deals normalized weapon damage
                GetTarget()->CastSpell(procTarget, SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_2, aurEff);
            }
            else
            {
                if (spellInfo && spellInfo->Id == SPELL_WARRIOR_WHIRLWIND_MAIN)
                    eventInfo.GetActor()->AddSpellCooldown(SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1, 0, 500);

                auto damage = static_cast<int32>(damageInfo->GetUnmitigatedDamage());
                GetTarget()->CastCustomSpell(procTarget, SPELL_WARRIOR_SWEEPING_STRIKES_EXTRA_ATTACK_1,
                    &damage, nullptr, nullptr, true, nullptr, aurEff);
            }
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_sweeping_strikes::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_sweeping_strikes::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

private:
    ObjectGuid _procTargetGUID;
};

// 50720 - Vigilance
class spell_warr_vigilance : public AuraScript
{
    PrepareAuraScript(spell_warr_vigilance);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_WARRIOR_GLYPH_OF_VIGILANCE,
                SPELL_WARRIOR_VIGILANCE_PROC,
                SPELL_WARRIOR_VIGILANCE_REDIRECT_THREAT,
                SPELL_GEN_DAMAGE_REDUCTION_AURA,
                SPELL_PALADIN_BLESSING_OF_SANCTUARY,
                SPELL_PALADIN_GREATER_BLESSING_OF_SANCTUARY,
                SPELL_PRIEST_RENEWED_HOPE,
                SPELL_WARRIOR_FOCUSED_RAGE_R3
            });
    }

    bool Load() override
    {
        _procTargetGUID.Clear();
        return true;
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        target->CastSpell(target, SPELL_GEN_DAMAGE_REDUCTION_AURA, true);

        if (Unit* caster = GetCaster())
            target->CastSpell(caster, SPELL_WARRIOR_VIGILANCE_REDIRECT_THREAT, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (target->HasAura(SPELL_GEN_DAMAGE_REDUCTION_AURA) &&
                !(target->HasAura(SPELL_PALADIN_BLESSING_OF_SANCTUARY) ||
                    target->HasAura(SPELL_PALADIN_GREATER_BLESSING_OF_SANCTUARY) ||
                    target->HasAura(SPELL_PRIEST_RENEWED_HOPE)))
        {
            target->RemoveAurasDueToSpell(SPELL_GEN_DAMAGE_REDUCTION_AURA);
        }

        target->GetThreatMgr().UnregisterRedirectThreat(SPELL_WARRIOR_VIGILANCE_REDIRECT_THREAT, GetCasterGUID());
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        if (Unit* caster = GetCaster())
        {
            _procTargetGUID = caster->GetGUID();
            return true;
        }
        return false;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* procTarget = ObjectAccessor::GetUnit(*GetTarget(), _procTargetGUID);
        if (!procTarget)
            return;

        GetTarget()->CastSpell(procTarget, SPELL_WARRIOR_VIGILANCE_PROC, true, nullptr, aurEff);

        // Focused Rage capstone (Protection Warrior rework phase 3, docs/prot_warrior_rework.md
        // Row 7): "You gain 5 rage every time the target of your Vigilance takes damage. This
        // effect can only occur once every second." procTarget is already the warrior here (see
        // CheckProc: _procTargetGUID is set to the aura's *caster*, i.e. the warrior who cast
        // Vigilance) - reuse it instead of a second GetCaster() lookup. The 1s internal cooldown
        // reuses SPELL_WARRIOR_FOCUSED_RAGE_R3's own id purely as a gate key (it's a passive-only
        // marker, never actually cast), same HasSpellCooldown-as-gate idiom as
        // spell_warr_sweeping_strikes.
        if (procTarget->HasAura(SPELL_WARRIOR_FOCUSED_RAGE_R3) && !procTarget->HasSpellCooldown(SPELL_WARRIOR_FOCUSED_RAGE_R3))
        {
            procTarget->EnergizeBySpell(procTarget, SPELL_WARRIOR_FOCUSED_RAGE_R3, 5, POWER_RAGE);
            procTarget->AddSpellCooldown(SPELL_WARRIOR_FOCUSED_RAGE_R3, 0, 1000);
        }
    }

    void Register() override
    {
        OnEffectApply += AuraEffectApplyFn(spell_warr_vigilance::HandleApply, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        OnEffectRemove += AuraEffectRemoveFn(spell_warr_vigilance::HandleRemove, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        DoCheckProc += AuraCheckProcFn(spell_warr_vigilance::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_vigilance::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }

private:
    ObjectGuid _procTargetGUID;
};

// 59665 - Vigilance (Redirect Threat)
class spell_warr_vigilance_redirect_threat : public SpellScript
{
    PrepareSpellScript(spell_warr_vigilance_redirect_threat);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_GLYPH_OF_VIGILANCE });
    }

    void HandleGlyph(SpellEffIndex /*effIndex*/)
    {
        if (Unit* warrior = GetHitUnit())
            if (AuraEffect const* glyph = warrior->GetAuraEffect(SPELL_WARRIOR_GLYPH_OF_VIGILANCE, EFFECT_0))
                SetEffectValue(GetEffectValue() + glyph->GetAmount());
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_vigilance_redirect_threat::HandleGlyph, EFFECT_0, SPELL_EFFECT_REDIRECT_THREAT);
    }
};

// 50725 - Vigilance
class spell_warr_vigilance_trigger : public SpellScript
{
    PrepareSpellScript(spell_warr_vigilance_trigger);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_TAUNT });
    }

    void HandleScript(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);

        // Remove Taunt cooldown
        if (Player* target = GetHitPlayer())
            target->RemoveSpellCooldown(SPELL_WARRIOR_TAUNT, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_vigilance_trigger::HandleScript, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// 58387 - Glyph of Sunder Armor
class spell_warr_glyph_of_sunder_armor : public AuraScript
{
    PrepareAuraScript(spell_warr_glyph_of_sunder_armor);

    void HandleEffectCalcSpellMod(AuraEffect const* aurEff, SpellModifier*& spellMod)
    {
        if (!spellMod)
        {
            spellMod = new SpellModifier(aurEff->GetBase());
            spellMod->op = SpellModOp(aurEff->GetMiscValue());
            spellMod->type = SPELLMOD_FLAT;
            spellMod->spellId = GetId();
            spellMod->mask = GetSpellInfo()->Effects[aurEff->GetEffIndex()].SpellClassMask;
        }

        spellMod->value = aurEff->GetAmount();
    }

    void Register() override
    {
        DoEffectCalcSpellMod += AuraEffectCalcSpellModFn(spell_warr_glyph_of_sunder_armor::HandleEffectCalcSpellMod, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 28845 - Cheat Death
class spell_warr_t3_prot_8p_bonus : public AuraScript
{
    PrepareAuraScript(spell_warr_t3_prot_8p_bonus);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (eventInfo.GetActionTarget()->HealthBelowPct(20))
            return true;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (damageInfo && damageInfo->GetDamage())
            if (GetTarget()->HealthBelowPctDamaged(20, damageInfo->GetDamage()))
                return true;

        return false;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_t3_prot_8p_bonus::CheckProc);
    }
};

// 20230 - Retaliation
class spell_warr_retaliation : public AuraScript
{
    PrepareAuraScript(spell_warr_retaliation);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_RETALIATION_DAMAGE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Prevent counterattacking yourself on activation
        if (eventInfo.GetActor() == eventInfo.GetActionTarget())
            return false;

        // check attack comes not from behind and warrior is not stunned
        return eventInfo.GetActionTarget()->isInFront(eventInfo.GetActor(), float(M_PI)) && !GetTarget()->HasUnitState(UNIT_STATE_STUNNED);
    }

    void HandleEffectProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        eventInfo.GetActionTarget()->CastSpell(eventInfo.GetActor(), SPELL_WARRIOR_RETALIATION_DAMAGE, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_retaliation::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_retaliation::HandleEffectProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 29707 - Heroic Strike (Rank 10)
// 30324 - Heroic Strike (Rank 11)
// 47449 - Heroic Strike (Rank 12)
// 47450 - Heroic Strike (Rank 13)
enum DazeSpells
{
    ICON_GENERIC_DAZE                   = 15,
    SPELL_GENERIC_AFTERMATH             = 18118,
};

class spell_warr_heroic_strike : public SpellScript
{
    PrepareSpellScript(spell_warr_heroic_strike);

    void HandleOnHit()
    {
        Unit* target = GetHitUnit();
        if (!target)
            return;
        Unit::AuraEffectList const& AuraEffectList = target->GetAuraEffectsByType(SPELL_AURA_MOD_DECREASE_SPEED);
        bool bonusDamage = false;
        for (AuraEffect* eff : AuraEffectList)
        {
            SpellInfo const* spellInfo = eff->GetSpellInfo();
            if (!spellInfo)
                continue;

            // Warrior Spells: Piercing Howl or Dazed (29703)
            if (spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR && (spellInfo->SpellFamilyFlags[1] & (0x20 | 0x200000)))
            {
                bonusDamage = true;
                break;
            }

            // Generic Daze: icon 15 with mechanic daze or snare
            if ((spellInfo->SpellIconID == ICON_GENERIC_DAZE)
                && ((spellInfo->Mechanic == MECHANIC_DAZE || spellInfo->HasEffectMechanic(MECHANIC_DAZE))
                    || (spellInfo->Mechanic == MECHANIC_SNARE || spellInfo->HasEffectMechanic(MECHANIC_SNARE))
                    )
            )
            {
                bonusDamage = true;
                break;
            }

            if ((spellInfo->Id == SPELL_GENERIC_AFTERMATH)
                || (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE && (spellInfo->SpellFamilyFlags[1] & 0x40)) // Blast Wave
                || (spellInfo->SpellFamilyName == SPELLFAMILY_PALADIN && (spellInfo->SpellFamilyFlags[2] & 0x4000)) // Avenger's Shield
            )
            {
                bonusDamage = true;
                break;
            }
        }
        if (bonusDamage)
        {
            int32 damage = GetHitDamage();
            AddPct(damage, 35); // "Causes ${0.35*$m1} additional damage against Dazed targets."
            SetHitDamage(damage);
        }
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warr_heroic_strike::HandleOnHit);
    }
};

class spell_war_sudden_death_aura : public AuraScript
{   PrepareAuraScript(spell_war_sudden_death_aura);

    bool AfterCheckProc(ProcEventInfo& eventInfo, bool isTriggeredAtSpellProcEvent)
    {
        // Check PROC_SPELL_PHASE_FINISH only for Execute
        if (eventInfo.GetSpellPhaseMask() != PROC_SPELL_PHASE_FINISH)
            return isTriggeredAtSpellProcEvent;
        if (Spell const* procSpell = eventInfo.GetProcSpell())
            if (procSpell->GetSpellInfo()->GetFirstRankSpell()->Id == SPELL_WARRIOR_EXECUTE_R1)
                return isTriggeredAtSpellProcEvent;
        return false;
    }

    void Register() override
    {
        DoAfterCheckProc += AuraAfterCheckProcFn(spell_war_sudden_death_aura::AfterCheckProc);
    }
};

// Second Wind - triggers health regen when stunned or immobilized
class spell_warr_second_wind : public AuraScript
{
    PrepareAuraScript(spell_warr_second_wind);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            SPELL_WARRIOR_SECOND_WIND_HEAL_R1,
            SPELL_WARRIOR_SECOND_WIND_HEAL_R2,
            SPELL_WARRIOR_SECOND_WIND_UK
        });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return false;

        // Must be from stun or root mechanic
        if (!(procSpell->GetAllEffectsMechanicMask() & ((1ULL << MECHANIC_ROOT) | (1ULL << MECHANIC_STUN))))
            return false;

        // Not from self
        if (eventInfo.GetActionTarget() == eventInfo.GetActor())
            return false;

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        uint32 triggeredSpellId = 0;
        switch (GetId())
        {
            case 29838: triggeredSpellId = SPELL_WARRIOR_SECOND_WIND_HEAL_R2; break;
            case 29834: triggeredSpellId = SPELL_WARRIOR_SECOND_WIND_HEAL_R1; break;
            case 42770: triggeredSpellId = SPELL_WARRIOR_SECOND_WIND_UK; break;
            default:
                return;
        }

        GetTarget()->CastSpell(GetTarget(), triggeredSpellId, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_second_wind::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_second_wind::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Deep Wounds - calculates bleed damage based on weapon damage
class spell_warr_deep_wounds_aura : public AuraScript
{
    PrepareAuraScript(spell_warr_deep_wounds_aura);

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        if (!caster->IsPlayer())
            return;

        int32 basepoints;
        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_OFFHAND_ATTACK)
            basepoints = int32((caster->GetFloatValue(UNIT_FIELD_MAXOFFHANDDAMAGE) + caster->GetFloatValue(UNIT_FIELD_MINOFFHANDDAMAGE)) / 2.0f);
        else
            basepoints = int32((caster->GetFloatValue(UNIT_FIELD_MAXDAMAGE) + caster->GetFloatValue(UNIT_FIELD_MINDAMAGE)) / 2.0f);

        uint32 triggeredSpellId = GetSpellInfo()->Effects[EFFECT_0].TriggerSpell;
        if (Unit* target = eventInfo.GetActionTarget())
            caster->CastCustomSpell(target, triggeredSpellId, &basepoints, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_deep_wounds_aura::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// Warrior T10 Melee 4P Bonus - extra effects for Sudden Death/Bloodsurge procs
class spell_warr_extra_proc : public AuraScript
{
    PrepareAuraScript(spell_warr_extra_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            SPELL_WARRIOR_T10_MELEE_4P_BONUS,
            SPELL_WARRIOR_T10_MELEE_4P_EXTRA_CHARGE,
            SPELL_WARRIOR_SLAM_GCD_REDUCED,
            SPELL_WARRIOR_EXECUTE_GCD_REDUCED
        });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        Unit* caster = GetTarget();
        uint32 triggeredSpellId = GetSpellInfo()->Effects[EFFECT_0].TriggerSpell;

        // Triggered spell IDs: 46916 = Slam!, 52437 = Sudden Death
        bool isBloodsurge = (triggeredSpellId == 46916);

        // Item - Warrior T10 Melee 4P Bonus
        if (AuraEffect const* t10Bonus = caster->GetAuraEffect(SPELL_WARRIOR_T10_MELEE_4P_BONUS, EFFECT_0))
        {
            if (!roll_chance_i(t10Bonus->GetAmount()))
            {
                // Don't allow normal proc to override set one
                if (caster->GetAura(isBloodsurge ? SPELL_WARRIOR_SLAM_GCD_REDUCED : SPELL_WARRIOR_EXECUTE_GCD_REDUCED))
                {
                    PreventDefaultAction();
                    return;
                }
                // Just to be sure
                caster->RemoveAurasDueToSpell(SPELL_WARRIOR_T10_MELEE_4P_EXTRA_CHARGE);
                return;
            }

            PreventDefaultAction();

            // Fully remove all auras and reapply once more
            caster->RemoveAurasDueToSpell(SPELL_WARRIOR_T10_MELEE_4P_EXTRA_CHARGE);
            caster->RemoveAurasDueToSpell(SPELL_WARRIOR_SLAM_GCD_REDUCED);
            caster->RemoveAurasDueToSpell(SPELL_WARRIOR_EXECUTE_GCD_REDUCED);

            caster->CastSpell(caster, SPELL_WARRIOR_T10_MELEE_4P_EXTRA_CHARGE, true, nullptr, aurEff);
            caster->CastSpell(caster, triggeredSpellId, true, nullptr, aurEff);
            caster->CastSpell(caster, isBloodsurge ? SPELL_WARRIOR_SLAM_GCD_REDUCED : SPELL_WARRIOR_EXECUTE_GCD_REDUCED, true, nullptr, aurEff);
        }
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_extra_proc::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// Sword and Board proc - remove Shield Slam cooldown
class spell_warr_sword_and_board : public AuraScript
{
    PrepareAuraScript(spell_warr_sword_and_board);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        Unit* caster = GetTarget();
        if (caster->IsPlayer())
            caster->ToPlayer()->RemoveCategoryCooldown(1209); // Shield Slam category
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_sword_and_board::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// Glyph of Blocking - triggers block value buff
class spell_warr_glyph_of_blocking : public AuraScript
{
    PrepareAuraScript(spell_warr_glyph_of_blocking);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_GLYPH_OF_BLOCKING_BUFF });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->CastSpell(GetTarget(), SPELL_WARRIOR_GLYPH_OF_BLOCKING_BUFF, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_glyph_of_blocking::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Item - Warrior T10 Protection 4P Bonus
class spell_warr_item_t10_prot_4p_bonus : public AuraScript
{
    PrepareAuraScript(spell_warr_item_t10_prot_4p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_T10_PROT_4P_ABSORB });
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        int32 basepoints = CalculatePct(static_cast<int32>(caster->GetMaxHealth()), GetSpellInfo()->Effects[EFFECT_1].CalcValue());
        caster->CastCustomSpell(caster, SPELL_WARRIOR_T10_PROT_4P_ABSORB, &basepoints, nullptr, nullptr, true, nullptr, GetEffect(EFFECT_0));
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_warr_item_t10_prot_4p_bonus::HandleProc);
    }
};

// 21977 - Warrior's Wrath (T3 8P Bonus)
class spell_warr_warriors_wrath : public SpellScript
{
    PrepareSpellScript(spell_warr_warriors_wrath);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_WARRIORS_WRATH });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        GetCaster()->CastSpell(GetCaster(), SPELL_WARRIOR_WARRIORS_WRATH, true);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_warr_warriors_wrath::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 50687 - Incite (rank 3 capstone: critical strikes with Revenge grant Storm's Bulwark)
class spell_warr_incite : public AuraScript
{
    PrepareAuraScript(spell_warr_incite);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        // Revenge's own classmask (SpellFamilyFlags[0] & 0x400) rather than a literal spell id
        // list, so this keeps working across every Revenge rank without needing to enumerate
        // them here. ProcTypeMask (16, PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS - set on this spell's
        // own row) already narrows procs to melee-class ability damage the caster deals; this
        // narrows further to Revenge specifically and to a critical hit.
        return spellInfo && spellInfo->SpellFamilyName == SPELLFAMILY_WARRIOR
            && (spellInfo->SpellFamilyFlags[0] & 0x400)
            && (eventInfo.GetHitMask() & PROC_HIT_CRITICAL);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        // "add an amount equal to 1.5% of your maximum health ... increased by your mastery, up
        // to its maximum" - GrantStormsBulwark itself enforces the 50%-max-HP cap.
        // "This does not extend the shield's duration" -> refreshDuration=false.
        int32 amount = int32(CalculatePct(player->GetMaxHealth(), 1.5f));
        AddPct(amount, player->GetMasteryPercentage());
        GrantStormsBulwark(player, amount, false);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_incite::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warr_incite::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 6343 - Thunder Clap: Blood and Thunder, the Storm's Bulwark talent, Shield Discipline's
// consumption, and Thunderstruck's delayed echo all hook the caster's own real Thunder Clap cast.
class spell_warr_thunder_clap : public SpellScript
{
    PrepareSpellScript(spell_warr_thunder_clap);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_BLOODSTORM, SPELL_WARRIOR_THUNDERSTRUCK_ECHO_TRIGGER,
                                    SPELL_WARRIOR_SHIELD_DISCIPLINE_TC_BOOST });
    }

    bool Load() override
    {
        _targetsHit = 0;
        return true;
    }

    // EFFECT_0 is Thunder Clap's real damage effect (SPELL_EFFECT_SCHOOL_DAMAGE); EFFECT_1 is its
    // separate attack-speed-slow debuff, untouched here.
    void HandleDamageEffect(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target)
            return;

        ++_targetsHit;

        // Blood and Thunder (docs/prot_warrior_rework.md Row 2): "Your Thunder Clap causes
        // targets to bleed for 15/30% of the damage dealt over 9 sec" - Bloodstorm (200030,
        // Phase 1) ticks every 3s over 9s, so split the total 3 ways; per-tick amount goes
        // through CastCustomSpell's own "+1" convention like every other custom-cast amount.
        if (AuraEffect const* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, WARRIOR_ICON_ID_BLOOD_AND_THUNDER, EFFECT_0))
        {
            int32 total = CalculatePct(GetHitDamage(), aurEff->GetAmount());
            int32 perTick = total / 3 - 1;
            caster->CastCustomSpell(target, SPELL_WARRIOR_BLOODSTORM, &perTick, nullptr, nullptr, true);
        }
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return;

        // Storm's Bulwark talent (Row 6): "absorb shield equal to 2/4/6% of your maximum health
        // increased by your mastery, plus an additional 1% for each target struck." Percentages
        // combine before converting to a health value, then mastery multiplies the combined total
        // (confirmed by the user - see docs/prot_warrior_rework.md phase 3 plan).
        if (AuraEffect const* aurEff = player->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, WARRIOR_ICON_ID_STORMS_BULWARK_TALENT, EFFECT_0))
        {
            int32 totalPct = aurEff->GetAmount() + _targetsHit;
            int32 amount = int32(CalculatePct(player->GetMaxHealth(), totalPct));

            // Shield Discipline (Row 9): "Your Shield Slam increases the absorb granted by your
            // next Thunder Clap by 25/50%" - charge applied by spell_warr_shield_slam, consumed
            // here regardless of which Thunder Clap effect fed the base amount.
            if (Aura* boost = player->GetAura(SPELL_WARRIOR_SHIELD_DISCIPLINE_TC_BOOST))
            {
                if (AuraEffect* boostEff = boost->GetEffect(EFFECT_0))
                    AddPct(amount, boostEff->GetAmount());
                boost->Remove();
            }

            AddPct(amount, player->GetMasteryPercentage());
            GrantStormsBulwark(player, amount, true);
        }

        // Thunderstruck capstone (Row 10): schedule the 50%-effectiveness echo 3s later. 200066
        // is a pure data-driven PERIODIC_TRIGGER_SPELL holder (no script) that fires 200065 once;
        // re-casting it on repeated Thunder Claps within 3s just refreshes rather than stacking.
        if (player->HasAura(SPELL_WARRIOR_THUNDERSTRUCK_R3))
            player->CastSpell(player, SPELL_WARRIOR_THUNDERSTRUCK_ECHO_TRIGGER, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_thunder_clap::HandleDamageEffect, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterCast += SpellCastFn(spell_warr_thunder_clap::HandleAfterCast);
    }

private:
    int32 _targetsHit = 0;
};

// 20243 - Devastate: Reprisal (Row 4)
class spell_warr_devastate : public SpellScript
{
    PrepareSpellScript(spell_warr_devastate);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SUNDER_ARMOR });
    }

    void HandleOnHit()
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // "adds an amount equal to 0.5/1% of your maximum health ... increased by your mastery.
        // This amount is increased by 20% for each application of Sunder Armor on the target."
        // Marker stores tenths of a percent (see apps/dbc-tools/source/spells/warrior_talents.csv).
        AuraEffect const* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, WARRIOR_ICON_ID_REPRISAL, EFFECT_0);
        if (!aurEff)
            return;

        float pct = aurEff->GetAmount() / 10.0f;
        int32 amount = int32(CalculatePct(caster->GetMaxHealth(), pct));

        // Devastate always (re)applies Sunder Armor before this OnHit runs (native
        // SPELLFAMILY_WARRIOR handling in SpellEffects.cpp), so there's always >=1 stack -
        // confirmed multiplicative by the user: at 5 stacks, 0.5%/1% becomes 1%/2%.
        int32 stacks = 1;
        if (Aura const* sunder = target->GetAura(SPELL_WARRIOR_SUNDER_ARMOR, caster->GetGUID()))
            stacks = sunder->GetStackAmount();
        amount = int32(amount * (1.0f + 0.2f * stacks));

        AddPct(amount, caster->GetMasteryPercentage());
        GrantStormsBulwark(caster, amount, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warr_devastate::HandleOnHit);
    }
};

// 46968 - Shockwave (Row 11): real base-game ability, already correctly scoped/tuned in the DBC
// data (0.75*AP via effect3's carried value, 4s stun, 10yd frontal cone) - just needs the
// AP-based damage calc, the stun-immunity double-damage fallback, and its own Storm's Bulwark
// grant (unconditional - not gated by the separate Storm's Bulwark talent, it's baked into the
// ability itself per docs/prot_warrior_rework.md Row 11).
class spell_warr_shockwave : public SpellScript
{
    PrepareSpellScript(spell_warr_shockwave);

    bool Load() override
    {
        _targetsHit = 0;
        return true;
    }

    // EFFECT_0 is the stun (SPELL_AURA_MOD_STUN); EFFECT_1 is the school-damage effect this
    // computes. EFFECT_2 just carries the 74 (->0.75) coefficient value referenced by the DBC
    // tooltip's $m3 - not itself an active effect.
    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target)
            return;

        ++_targetsHit;

        int32 damage = CalculatePct(caster->GetTotalAttackPowerValue(BASE_ATTACK), 75);
        // "Targets that cannot be stunned take double damage instead."
        if (target->IsImmunedToSpellEffect(GetSpellInfo(), EFFECT_0))
            damage *= 2;
        SetHitDamage(damage);
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || !_targetsHit)
            return;

        // "adds an amount equal to 20% of your maximum health ... plus an additional 1% for each
        // target struck increased by your mastery."
        int32 totalPct = 20 + _targetsHit;
        int32 amount = int32(CalculatePct(player->GetMaxHealth(), totalPct));
        AddPct(amount, player->GetMasteryPercentage());
        GrantStormsBulwark(player, amount, true);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_shockwave::HandleDamage, EFFECT_1, SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterCast += SpellCastFn(spell_warr_shockwave::HandleAfterCast);
    }

private:
    int32 _targetsHit = 0;
};

// Shield Cover capstone (Row 4): bound to both Spell Reflection (23920) and Shield Block (2565)
// via spell_script_names - "Using Spell Reflection or Shield Block also reduces all Magic damage
// taken by 30% for 3 sec" when Shield Cover rank 3 (200043) is talented.
class spell_warr_shield_cover_capstone : public SpellScript
{
    PrepareSpellScript(spell_warr_shield_cover_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SHIELD_COVER_MAGIC_WARD });
    }

    void HandleCast()
    {
        Unit* caster = GetCaster();
        if (caster->HasAura(SPELL_WARRIOR_SHIELD_COVER_R3))
            caster->CastSpell(caster, SPELL_WARRIOR_SHIELD_COVER_MAGIC_WARD, true);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_shield_cover_capstone::HandleCast);
    }
};

// Revenge (6572, 25288): Unrelenting's cooldown clause - "Each cast of Revenge reduces the
// remaining cooldown of your Last Stand by 1 sec."
class spell_warr_revenge : public SpellScript
{
    PrepareSpellScript(spell_warr_revenge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_LAST_STAND_ABILITY, SPELL_WARRIOR_UNRELENTING });
    }

    void HandleCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (player && player->HasAura(SPELL_WARRIOR_UNRELENTING))
            player->ModifySpellCooldown(SPELL_WARRIOR_LAST_STAND_ABILITY, -1000);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_revenge::HandleCast);
    }
};

// 23922 - Shield Slam: Shield Discipline (Row 9) applies its "next Thunder Clap" charge,
// consumed by spell_warr_thunder_clap's AfterCast.
class spell_warr_shield_slam : public SpellScript
{
    PrepareSpellScript(spell_warr_shield_slam);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WARRIOR_SHIELD_DISCIPLINE_TC_BOOST });
    }

    void HandleOnHit()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return;

        if (AuraEffect const* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, WARRIOR_ICON_ID_SHIELD_DISCIPLINE, EFFECT_0))
        {
            // aurEff->GetAmount() is already "+1"-adjusted (25 or 50); subtract 1 back out since
            // this custom cast will apply that same convention again when the charge buff is read.
            int32 bp = aurEff->GetAmount() - 1;
            caster->CastCustomSpell(caster, SPELL_WARRIOR_SHIELD_DISCIPLINE_TC_BOOST, &bp, nullptr, nullptr, true, nullptr);
        }
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_warr_shield_slam::HandleOnHit);
    }
};

void AddSC_warrior_spell_scripts()
{
    RegisterSpellScript(spell_warr_mocking_blow);
    RegisterSpellScript(spell_warr_intervene);
    RegisterSpellScript(spell_warr_improved_spell_reflection);
    RegisterSpellAndAuraScriptPair(spell_warr_improved_spell_reflection_trigger, spell_warr_improved_spell_reflection_trigger_aura);
    RegisterSpellScript(spell_warr_victory_rush);
    RegisterSpellScript(spell_warr_bloodthirst);
    RegisterSpellScript(spell_warr_bloodthirst_heal);
    RegisterSpellScript(spell_warr_charge);
    RegisterSpellScript(spell_warr_concussion_blow);
    RegisterSpellScript(spell_warr_damage_shield);
    RegisterSpellScript(spell_warr_deep_wounds);
    RegisterSpellScript(spell_warr_execute);
    RegisterSpellScript(spell_warr_glyph_of_sunder_armor);
    RegisterSpellScript(spell_warr_intimidating_shout);
    RegisterSpellScript(spell_warr_last_stand);
    RegisterSpellScript(spell_warr_overpower);
    RegisterSpellScript(spell_warr_rend);
    RegisterSpellScript(spell_warr_retaliation);
    RegisterSpellScript(spell_warr_shattering_throw);
    RegisterSpellScript(spell_warr_slam);
    RegisterSpellScript(spell_warr_sweeping_strikes);
    RegisterSpellScript(spell_warr_vigilance);
    RegisterSpellScript(spell_warr_vigilance_redirect_threat);
    RegisterSpellScript(spell_warr_vigilance_trigger);
    RegisterSpellScript(spell_warr_warriors_wrath);
    RegisterSpellScript(spell_warr_t3_prot_8p_bonus);
    RegisterSpellScript(spell_warr_heroic_strike);
    RegisterSpellScript(spell_war_sudden_death_aura);
    RegisterSpellScript(spell_warr_second_wind);
    RegisterSpellScript(spell_warr_deep_wounds_aura);
    RegisterSpellScript(spell_warr_extra_proc);
    RegisterSpellScript(spell_warr_sword_and_board);
    RegisterSpellScript(spell_warr_glyph_of_blocking);
    RegisterSpellScript(spell_warr_item_t10_prot_4p_bonus);
    RegisterSpellScript(spell_warr_defensive_stance);
    // Protection Warrior rework phase 3 (docs/prot_warrior_rework.md):
    RegisterSpellScript(spell_warr_incite);
    RegisterSpellScript(spell_warr_thunder_clap);
    RegisterSpellScript(spell_warr_devastate);
    RegisterSpellScript(spell_warr_shockwave);
    RegisterSpellScript(spell_warr_shield_cover_capstone);
    RegisterSpellScript(spell_warr_revenge);
    RegisterSpellScript(spell_warr_shield_slam);
}
