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
 * Warrior rework - Fury SpellScripts (warrior-rework S3; docs/reworks/warrior-fury-rework.md). Thin bindings: every
 * mechanic body lives in WarriorMechanics (Warrior::), the damage hooks and the dispatcher in warrior_hooks.cpp.
 *
 * spell_warr_bloodthirst_fury                 23881      D9-D11: fork of stock spell_warr_bloodthirst (unbound in
 *                                                        data): bleed bonus, landed main target once ->
 *                                                        Warrior::OnBloodthirstHit (23885 cast there), Fresh Meat
 *                                                        crit removed after the cast
 * spell_warr_execute_fury                     -5308      D16/D17: fork of stock spell_warr_execute (unbound in data):
 *                                                        Deathmaker consumed at OnCast, Execute's extra rage credited
 *                                                        to the meter, Improved Execute, Warrior::OnExecuteHit
 * spell_warr_rampage_fury                     204630     D7: OnCast snapshot -> Warrior::OnRampageCast; AfterCast ->
 *                                                        Warrior::StartRampage
 * spell_warr_enrage_fury                      204636     D4: damage / haste amounts, 1 s poll ->
 *                                                        Warrior::RefreshEnrageAmount
 * spell_warr_death_wish_fury                  12292      D5: Enrage on apply, held every 1 s, a full 12 s at the end
 * spell_warr_recklessness_fury                1719       D6/B-R1: Warrior::OnRecklessnessApply / OnRecklessnessRemove
 * spell_warr_hs_cleave_fury                   78, 845    D19/D21: Frenzied Blows' off-hand strike per landed target;
 *                                                        Cleave: Warrior::ReduceWhirlwindFromCleave
 * spell_warr_titans_grip_hardcode             49152      D31: the core's Titan's Grip hardcode forced to 0
 * spell_warr_two_handed_weapon_mastery_gate   -204524    D32: every effect 0 while an off-hand weapon is wielded
 * spell_warr_pummel_fury                      6552       D25: a real interrupt -> Warrior::OnPummelInterrupt
 * spell_warr_dance_of_death                   -204653    D26: crit buff on a kill; rank 3 heal (5 s ICD), Charge reset
 * spell_warr_commanding_presence              6673, 469  D30: the shouts' Strength / Stamina effect
 * spell_warr_deathmaker                       -204671    D16: only strike casts and white swings roll
 */

#include "GameTime.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SharedDefines.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellPotency.h"
#include "SpellScript.h"
#include "Unit.h"
#include "WarriorMechanics.h"
#include <algorithm>
#include <cmath>

namespace
{
    // Stock: the Sudden Death rows' SpellIconID (S2 keeps Arms' rows on family 0 / icon 1989 / effect 1 = the rage the
    // Execute script keeps; the stock enum is private to spell_warrior.cpp).
    constexpr uint32 WARRIOR_ICON_ID_SUDDEN_DEATH = 1989;

    // Stock Execute's rage ceiling, in power units (30 rage): the extra rage it spends is up to this minus the cost.
    constexpr int32 EXECUTE_MAX_RAGE_POWER = 300;

    // D26: Dance of Death rank 3's heal stamp (CustomData key <= 15 chars).
    constexpr char const* DANCE_OF_DEATH_HEAL_KEY = "war_dod_heal";

    struct DanceOfDeathHealStamp : DataMap::Base
    {
        uint32 lastMs = 0;
        bool used = false;
    };

    // A player's own, non-triggered cast (the rogue Kick precedent).
    Player* GetOwnCastWarrior(SpellScript& script)
    {
        Unit* caster = script.GetCaster();
        if (!caster || !caster->IsPlayer() || script.GetSpell()->IsTriggered())
            return nullptr;

        return caster->ToPlayer();
    }
}

// 23881 - Bloodthirst (D9-D11). The stock damage body (potency gate included) times the bleed bonus. 23885 is cast
// from AfterHit (landed, main target, once), never from OnEffectHit: Bloodthirst's own HIT proc would eat its one
// charge. Fresh Meat's +100 crit (added by the dispatcher) is removed after every cast: only one +100 crit mod applies
// per cast, so with Recklessness up Fresh Meat's would otherwise survive to the next Bloodthirst.
class spell_warr_bloodthirst_fury : public SpellScript
{
    PrepareSpellScript(spell_warr_bloodthirst_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_BLOODTHIRST_HEAL_BUFF, WarriorData::SPELL_BLOOD_CRAZE_HEAL,
            WarriorData::SPELL_FRESH_MEAT_CRIT });
    }

    void HandleDamage(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        int32 damage = GetEffectValue();
        // Custom: potency-system (stock body): with a potency row GetEffectValue() already holds the AP part.
        if (!SpellPotency::HasRow(GetSpellInfo()->Id, effIndex))
            ApplyPct(damage, caster->GetTotalAttackPowerValue(BASE_ATTACK));

        if (Unit* target = GetHitUnit())
        {
            damage = caster->SpellDamageBonusDone(target, GetSpellInfo(), uint32(damage), SPELL_DIRECT_DAMAGE,
                effIndex);
            damage = target->SpellDamageBonusTaken(caster, GetSpellInfo(), uint32(damage), SPELL_DIRECT_DAMAGE);

            if (Player* player = caster->ToPlayer())
                damage = int32(std::lround(damage * Warrior::GetBloodthirstBleedMultiplier(player, target)));
        }

        SetHitDamage(damage);
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (_done || !player || !target || target != GetExplTargetUnit())
            return;

        _done = true;
        Warrior::OnBloodthirstHit(player, target);
    }

    void HandleAfterCast()
    {
        GetCaster()->RemoveAurasDueToSpell(WarriorData::SPELL_FRESH_MEAT_CRIT);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_bloodthirst_fury::HandleDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_warr_bloodthirst_fury::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warr_bloodthirst_fury::HandleAfterCast);
    }

private:
    bool _done = false;
};

// -5308 - Execute (D16/D17, R4). The stock body (miss packet, extra rage up to 30, Sudden Death's kept-rage floor, the
// damage formula with rageUsed) minus the retired Glyph of Execution. Deathmaker is spent at AfterCast: 20647 is cast
// on the hit and needs Deathmaker's aura 262 to pass its below-20% target check above 20%. OnCast notes the buff's
// duration so a Deathmaker this same Execute grants (a refresh resets the duration) survives. The rage this script
// removes (the cost was already paid and credited by the dispatcher) feeds the meter before 20647 is cast, so a fill
// Enrages the damage.
class spell_warr_execute_fury : public SpellScript
{
    PrepareSpellScript(spell_warr_execute_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_EXECUTE_20647, WarriorData::SPELL_DEATHMAKER_BUFF,
            WarriorData::SPELL_IMPROVED_EXECUTE_BUFF });
    }

    void SendMiss(SpellMissInfo missInfo)
    {
        if (missInfo == SPELL_MISS_NONE)
            return;

        if (Unit* target = GetHitUnit())
            GetCaster()->SendSpellMiss(target, WarriorData::SPELL_EXECUTE_20647, missInfo);
    }

    void HandleOnCast()
    {
        if (Aura const* deathmaker = GetCaster()->GetAura(WarriorData::SPELL_DEATHMAKER_BUFF))
            _deathmakerDuration = deathmaker->GetDuration();
    }

    void HandleAfterCast()
    {
        if (!_deathmakerDuration)
            return;

        // Not refreshed by this Execute's own roll: spend it.
        Aura* deathmaker = GetCaster()->GetAura(WarriorData::SPELL_DEATHMAKER_BUFF);
        if (deathmaker && deathmaker->GetDuration() <= *_deathmakerDuration)
            deathmaker->Remove();
    }

    void HandleEffect(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target)
            return;

        SpellInfo const* spellInfo = GetSpellInfo();
        int32 const rageBefore = int32(caster->GetPower(POWER_RAGE));
        int32 rageUsed = std::min<int32>(EXECUTE_MAX_RAGE_POWER -
            spellInfo->CalcPowerCost(caster, SpellSchoolMask(spellInfo->SchoolMask)), rageBefore);
        int32 newRage = std::max<int32>(0, rageBefore - rageUsed);

        // Sudden Death rage save (stock).
        if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_PROC_TRIGGER_SPELL, SPELLFAMILY_GENERIC,
            WARRIOR_ICON_ID_SUDDEN_DEATH, EFFECT_0))
        {
            int32 const rageSave = aurEff->GetSpellInfo()->Effects[EFFECT_1].CalcValue() * 10;
            newRage = std::max(newRage, rageSave);
        }

        caster->SetPower(POWER_RAGE, uint32(newRage));

        int32 bp = GetEffectValue() + int32(rageUsed * spellInfo->Effects[effIndex].DamageMultiplier +
            caster->GetTotalAttackPowerValue(BASE_ATTACK) * 0.2f);

        Player* player = caster->ToPlayer();
        if (player)
        {
            // GetPower is already in power units (tenths of a rage point), the unit AddRagePaid takes.
            Warrior::AddRagePaid(player, std::max(0, rageBefore - newRage));
            bp = int32(std::lround(bp * Warrior::GetImprovedExecuteMultiplier(player, target)));
        }

        Unit* originalCaster = GetOriginalCaster();
        caster->CastCustomSpell(target, WarriorData::SPELL_EXECUTE_20647, &bp, nullptr, nullptr, true, nullptr,
            nullptr, originalCaster ? originalCaster->GetGUID() : caster->GetGUID());

        if (player)
            Warrior::OnExecuteHit(player, target);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_warr_execute_fury::SendMiss);
        OnCast += SpellCastFn(spell_warr_execute_fury::HandleOnCast);
        OnEffectHitTarget += SpellEffectFn(spell_warr_execute_fury::HandleEffect, EFFECT_0, SPELL_EFFECT_DUMMY);
        AfterCast += SpellCastFn(spell_warr_execute_fury::HandleAfterCast);
    }

private:
    Optional<int32> _deathmakerDuration;
};

// 204630 - Rampage (D7). OnCast runs after the dispatcher credited the 60 rage (a fill by this press is part of the
// snapshot) and before the CAST-phase roll: the snapshot, the one Recklessness charge and Blood Rush's removal live in
// Warrior::OnRampageCast. AfterCast starts the four strikes on the explicit target (each strike rolls its own hit, so
// the press's own avoidance does not cancel them, the P0 shape) and applies Will of the Berserker's cut.
class spell_warr_rampage_fury : public SpellScript
{
    PrepareSpellScript(spell_warr_rampage_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_RAMPAGE_STRIKE_MH, WarriorData::SPELL_RAMPAGE_STRIKE_OH,
            WarriorData::SPELL_RAMPAGE_SNAPSHOT, WarriorData::SPELL_BLOOD_RUSH_BUFF });
    }

    void HandleOnCast()
    {
        if (Player* player = GetOwnCastWarrior(*this))
            Warrior::OnRampageCast(player);
    }

    void HandleAfterCast()
    {
        Player* player = GetOwnCastWarrior(*this);
        Unit* target = GetExplTargetUnit();
        if (player && target)
            Warrior::StartRampage(player, target);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_rampage_fury::HandleOnCast);
        AfterCast += SpellCastFn(spell_warr_rampage_fury::HandleAfterCast);
    }
};

// 204636 - Enrage (D4). Effect 0 (aura 79 physical) = Warrior::GetEnrageBonusPct, effect 1 (aura 138, attack speed
// only) = the talent rank's haste. Effect 2's 1 s tick re-reads the sum (Mastery from gear or buffs); the refresh
// only recalculates when the rounded value changed, so the buff never flickers. Every "Enraged" reads this aura.
class spell_warr_enrage_fury : public AuraScript
{
    PrepareAuraScript(spell_warr_enrage_fury);

    void CalcDamageAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        if (Player* player = GetUnitOwner()->ToPlayer())
            amount = int32(std::lround(Warrior::GetEnrageBonusPct(player)));
    }

    void CalcHasteAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        if (Player* player = GetUnitOwner()->ToPlayer())
            amount = int32(std::lround(Warrior::GetEnrageHastePct(player)));
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Warrior::RefreshEnrageAmount(player);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_enrage_fury::CalcDamageAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_enrage_fury::CalcHasteAmount, EFFECT_1,
            SPELL_AURA_MOD_MELEE_HASTE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_enrage_fury::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 12292 - Death Wish (D5, the P0 shape). Effect 1 is the 1 s PERIODIC_DUMMY. On apply it Enrages (with an Enrage rank)
// at the x1.5 amount; every tick holds Enrage at its full duration whatever the meter does; at the end Enrage is held
// once more (a full 12 s) and drops to the plain amount (Death Wish has already left the applied list). Logout / map
// removal unapplies auras outside the world and death clears IsAlive first: nothing is granted then.
class spell_warr_death_wish_fury : public AuraScript
{
    PrepareAuraScript(spell_warr_death_wish_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_ENRAGE_BUFF });
    }

    void AfterApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->IsInWorld())
            return;

        Warrior::GrantEnrage(player);
        Warrior::RefreshEnrageAmount(player);
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Warrior::HoldEnrage(player);
    }

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->IsInWorld() || !player->IsAlive())
            return;

        Warrior::HoldEnrage(player);
        Warrior::RefreshEnrageAmount(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warr_death_wish_fury::AfterApply, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warr_death_wish_fury::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_death_wish_fury::AfterRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 1719 - Recklessness (D6, B-R1). No spell_proc row: Player::RemoveSpellMods spends one charge per Spell at its finish
// (remove mode EXPIRE); Rampage's DropCharge removes with DEFAULT. Will of the Berserker only follows those two modes,
// which Warrior::OnRecklessnessRemove checks. Outside the world (logout / map change) or dead, the removal is reported
// as a cancel: the Merciless free-Rampage mod still goes, no buff is granted. Player guard: no NPC uses 1719.
class spell_warr_recklessness_fury : public AuraScript
{
    PrepareAuraScript(spell_warr_recklessness_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_ENRAGE_BUFF, WarriorData::SPELL_MERCILESS_FREE_RAMPAGE,
            WarriorData::SPELL_WILL_OF_THE_BERSERKER_BUFF });
    }

    void AfterApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (player && player->IsInWorld())
            Warrior::OnRecklessnessApply(player);
    }

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        AuraRemoveMode removeMode = GetTargetApplication()->GetRemoveMode();
        if (!player->IsInWorld() || !player->IsAlive())
            removeMode = AURA_REMOVE_BY_CANCEL;

        Warrior::OnRecklessnessRemove(player, uint8(removeMode));
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warr_recklessness_fury::AfterApply, EFFECT_0,
            SPELL_AURA_ADD_FLAT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warr_recklessness_fury::AfterRemove, EFFECT_0,
            SPELL_AURA_ADD_FLAT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
    }
};

// 78 - Heroic Strike, 845 - Cleave (D19, D21, R6). Frenzied Blows' capstone: OnCast snapshots the capstone, Enraged
// (the dispatcher's meter credit for this cast has already run) and an off-hand weapon (a shield, held item or empty
// hand gives nothing; a Titan's Grip two-hander counts). Each landed target then takes the matching off-hand strike,
// cast triggered and synchronously inside Warrior::PressChargeGuard, so it reads this cast's charged mods (Bloodsurge's
// +20% on every Frenzied Cleave strike, Recklessness' crit) without spending a charge; this cast's finish spends the
// one charge per press. Never deferred (the charged mods drop at this cast's finish). Cleave only: Unending Fury's
// Whirlwind cut, once per cast. Player guard: NPC Znort (2765) casts Cleave.
class spell_warr_hs_cleave_fury : public SpellScript
{
    PrepareSpellScript(spell_warr_hs_cleave_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_FRENZIED_BLOWS_HEROIC_STRIKE,
            WarriorData::SPELL_FRENZIED_BLOWS_CLEAVE });
    }

    void HandleOnCast()
    {
        Player* player = GetCaster()->ToPlayer();
        _offhandStrike = player && Warrior::HasFrenziedBlowsCapstone(player) && Warrior::IsEnraged(player)
            && player->HasOffhandWeaponForAttack();
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!_offhandStrike || !player || !target || !target->IsAlive())
            return;

        uint32 const strikeId = GetSpellInfo()->Id == WarriorData::SPELL_CLEAVE ?
            WarriorData::SPELL_FRENZIED_BLOWS_CLEAVE : WarriorData::SPELL_FRENZIED_BLOWS_HEROIC_STRIKE;
        Warrior::PressChargeGuard const chargeGuard(player);
        player->CastSpell(target, strikeId, true);
    }

    void HandleAfterCast()
    {
        if (GetSpellInfo()->Id != WarriorData::SPELL_CLEAVE)
            return;

        if (Player* player = GetCaster()->ToPlayer())
            Warrior::ReduceWhirlwindFromCleave(player);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warr_hs_cleave_fury::HandleOnCast);
        AfterHit += SpellHitFn(spell_warr_hs_cleave_fury::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warr_hs_cleave_fury::HandleAfterCast);
    }

private:
    bool _offhandStrike = false;
};

// 49152 - Titan's Grip penalty (D31, stock row). AuraEffect::CalculateAmount sets -10% whenever either hand holds a
// two-hander and only then calls this hook: always 0. The real penalty is the visible 204651, kept by
// Warrior::UpdateTitansGripPenalty from the equip / talent hooks.
class spell_warr_titans_grip_hardcode : public AuraScript
{
    PrepareAuraScript(spell_warr_titans_grip_hardcode);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_titans_grip_hardcode::CalcAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
    }
};

// 204524, 204525 - Two-Handed Weapon Mastery (D32, Q10): "only while wielding a single two-handed weapon". The item
// gate passes on any slot, so every effect (rage, damage, Colossus Smash's duration mod) reads 0 while the off hand
// holds a weapon. Warrior::UpdateTwoHandedWeaponMastery recalculates from the equip / talent hooks.
class spell_warr_two_handed_weapon_mastery_gate : public AuraScript
{
    PrepareAuraScript(spell_warr_two_handed_weapon_mastery_gate);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        Player* player = GetUnitOwner()->ToPlayer();
        if (player && player->GetWeaponForAttack(OFF_ATTACK, true))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_two_handed_weapon_mastery_gate::CalcAmount, EFFECT_0,
            SPELL_AURA_MOD_RAGE_FROM_DAMAGE_DEALT);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_two_handed_weapon_mastery_gate::CalcAmount, EFFECT_1,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_two_handed_weapon_mastery_gate::CalcAmount, EFFECT_2,
            SPELL_AURA_ADD_FLAT_MODIFIER);
    }
};

// 6552 - Pummel (D25): Intensify Rage's capstone needs to know whether Pummel really interrupted a cast (the rogue
// Kick shape). The interrupt effect runs at launch, before any hit hook, so the effect hook (ahead of the default
// handler) records the target's interruptible spells under the core's own conditions, and AfterHit checks which are
// gone.
class spell_warr_pummel_fury : public SpellScript
{
    PrepareSpellScript(spell_warr_pummel_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_INTENSIFY_RAGE_SILENCE,
            WarriorData::SPELL_INTENSIFY_RAGE_BLOODRAGE });
    }

    void RecordInterruptible(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetOwnCastWarrior(*this);
        Unit* target = GetHitUnit();
        if (!player || !target || !target->IsAlive() || !player->HasAura(WarriorData::SPELL_INTENSIFY_RAGE_56924))
            return;

        // The conditions of Spell::EffectInterruptCast.
        for (uint32 type : { uint32(CURRENT_GENERIC_SPELL), uint32(CURRENT_CHANNELED_SPELL) })
        {
            Spell* spell = target->GetCurrentSpell(type);
            if (!spell)
                continue;

            SpellInfo const* current = spell->GetSpellInfo();
            bool const running = spell->getState() == SPELL_STATE_CASTING ||
                (spell->getState() == SPELL_STATE_PREPARING && spell->GetCastTime() > 0);
            bool const interruptible = type == CURRENT_GENERIC_SPELL ?
                (current->InterruptFlags & SPELL_INTERRUPT_FLAG_INTERRUPT) != 0 :
                (current->ChannelInterruptFlags & CHANNEL_INTERRUPT_FLAG_INTERRUPT) != 0;
            if (running && interruptible && current->PreventionType == SPELL_PREVENTION_TYPE_SILENCE)
                _recorded[type == CURRENT_GENERIC_SPELL ? 0 : 1] = current->Id;
        }
    }

    void HandleAfterHit()
    {
        Player* player = GetOwnCastWarrior(*this);
        Unit* target = GetHitUnit();
        if (!player || !target || (!_recorded[0] && !_recorded[1]))
            return;

        bool interrupted = false;
        for (uint32 index : { 0u, 1u })
        {
            if (!_recorded[index])
                continue;

            Spell* spell = target->GetCurrentSpell(index == 0 ? uint32(CURRENT_GENERIC_SPELL) :
                uint32(CURRENT_CHANNELED_SPELL));
            if (!spell || spell->GetSpellInfo()->Id != _recorded[index])
                interrupted = true;
        }

        if (interrupted)
            Warrior::OnPummelInterrupt(player, target);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_warr_pummel_fury::RecordInterruptible, EFFECT_0,
            SPELL_EFFECT_INTERRUPT_CAST);
        AfterHit += SpellHitFn(spell_warr_pummel_fury::HandleAfterHit);
    }

private:
    uint32 _recorded[2] = { 0, 0 };
};

// 204653, 204654, 204655 - Dance of Death (D26). The KILL row (experience or honor; KillCredit pays assisters through
// the same proc flag) fires the rank's DUMMY carrier: the crit buff 204639 with the carrier as its final value
// (refresh, never stacks). Rank 3: the heal 204640 at most once per DANCE_OF_DEATH_HEAL_ICD_MS (a CustomData stamp:
// the aura's proc cooldown would throttle the crit too) and Charge's cooldown reset on every kill (Charge has no GCD
// sweep).
class spell_warr_dance_of_death : public AuraScript
{
    PrepareAuraScript(spell_warr_dance_of_death);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_DANCE_OF_DEATH_BUFF, WarriorData::SPELL_DANCE_OF_DEATH_HEAL,
            WarriorData::SPELL_CHARGE });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetTarget()->ToPlayer();
        if (!player || !player->IsAlive())
            return;

        int32 critPct = aurEff->GetAmount();
        player->CastCustomSpell(player, WarriorData::SPELL_DANCE_OF_DEATH_BUFF, &critPct, nullptr, nullptr, true,
            nullptr, aurEff);

        if (GetId() != WarriorData::SPELL_DANCE_OF_DEATH_204655)
            return;

        uint32 const now = uint32(GameTime::GetGameTimeMS().count());
        DanceOfDeathHealStamp* stamp = player->CustomData.GetDefault<DanceOfDeathHealStamp>(DANCE_OF_DEATH_HEAL_KEY);
        if (!stamp->used || now - stamp->lastMs >= uint32(WarriorData::DANCE_OF_DEATH_HEAL_ICD_MS))
        {
            stamp->used = true;
            stamp->lastMs = now;
            player->CastSpell(player, WarriorData::SPELL_DANCE_OF_DEATH_HEAL, true, nullptr, aurEff);
        }

        for (SpellInfo const* charge = sSpellMgr->GetSpellInfo(WarriorData::SPELL_CHARGE); charge;
            charge = charge->GetNextRankSpell())
        {
            if (player->HasSpell(charge->Id))
                player->RemoveSpellCooldown(charge->Id, true);
        }
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warr_dance_of_death::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 6673 - Battle Shout, 469 - Commanding Shout (D30). The new MOD_STAT effect (Battle Shout effect 2 Strength,
// Commanding Shout effect 1 Stamina) is the caster's Commanding Presence amount, level-scaled; 0 without the talent.
// Each raid member's aura has the warrior as caster.
class spell_warr_commanding_presence : public AuraScript
{
    PrepareAuraScript(spell_warr_commanding_presence);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        amount = caster ? Warrior::GetCommandingPresenceAmount(caster) : 0;
    }

    void Register() override
    {
        SpellEffIndex const statEffect = m_scriptSpellId == WarriorData::SPELL_BATTLE_SHOUT ? EFFECT_2 : EFFECT_1;
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warr_commanding_presence::CalcAmount, statEffect,
            SPELL_AURA_MOD_STAT);
    }
};

// 204671, 204672 - Deathmaker (D16). The CAST-phase row sees every non-triggered melee-class cast (stances and Pummel
// included): only a strike cast rolls; white swings (no spell) always do. The default trigger casts 204638.
class spell_warr_deathmaker : public AuraScript
{
    PrepareAuraScript(spell_warr_deathmaker);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetTarget()->IsPlayer())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return !spellInfo || Warrior::IsStrikeCast(spellInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warr_deathmaker::CheckProc);
    }
};

void AddSC_warrior_fury_spell_scripts()
{
    RegisterSpellScript(spell_warr_bloodthirst_fury);
    RegisterSpellScript(spell_warr_execute_fury);
    RegisterSpellScript(spell_warr_rampage_fury);
    RegisterSpellScript(spell_warr_enrage_fury);
    RegisterSpellScript(spell_warr_death_wish_fury);
    RegisterSpellScript(spell_warr_recklessness_fury);
    RegisterSpellScript(spell_warr_hs_cleave_fury);
    RegisterSpellScript(spell_warr_titans_grip_hardcode);
    RegisterSpellScript(spell_warr_two_handed_weapon_mastery_gate);
    RegisterSpellScript(spell_warr_pummel_fury);
    RegisterSpellScript(spell_warr_dance_of_death);
    RegisterSpellScript(spell_warr_commanding_presence);
    RegisterSpellScript(spell_warr_deathmaker);
}
