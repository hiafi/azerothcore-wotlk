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
 * Druid Feral rework (docs/reworks/druid-feral.md, .agents/plans/druid-rework/druid-rework.FERAL.md).
 * Every new script class this pass needs goes here; a stock spell_druid.cpp class that needs new
 * behaviour is replaced by a new-name class here and rebound through the DSL (scripted_by +
 * unbind_script), the stock class left in place, unbound (CORE-AUDIT §3 item 10). The class list,
 * bindings and effect-index contract are druid-rework.FERAL-WP-BRIEF.md §1/§3; the behaviour is §5.
 * Mechanics shared with druid_hooks.cpp (Swell, Barkskin floor, form checks, Heart of the Wild's
 * Mastery) live in DruidMechanics.h/.cpp; this file only calls them.
 *
 * Forms (FERAL §0.16): the everyday bear is FORM_DIREBEAR (8); Bestial Fury is FORM_BEAR (5).
 *
 * Stock ScriptName -> replacement (WP-A: unbind_script the left column, scripted_by the right):
 *    22842 'spell_dru_frenzied_regeneration' -> 'spell_dru_frenzied_regeneration_feral'
 *    -5217 'spell_dru_tiger_s_fury'          -> 'spell_dru_tiger_s_fury_feral' (bound to 5217)
 *    50334 'spell_dru_berserk'               -> 'spell_dru_berserk_feral'
 *    24932 'spell_dru_leader_of_the_pack'    -> 'spell_dru_leader_of_the_pack_feral'
 *    62606 'spell_dru_savage_defense'        -> none (a plain absorb; the pool is fed by
 *                                               spell_dru_savage_defense_talent)
 * The stock spell_dru_barkskin AuraScript stays bound to 22812 next to spell_dru_barkskin_floor.
 */

#include "DruidMechanics.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <initializer_list>
#include <list>
#include <utility>

namespace
{
    // Stock ids this file needs that DruidMechanics.h doesn't declare, redeclared locally (the
    // spell_druid_resto.cpp pattern).
    constexpr uint32 SPELL_DRUID_FERAL_CHARGE_BEAR = 16979;
    constexpr uint32 SPELL_DRUID_FERAL_CHARGE_CAT = 49376;
    constexpr uint32 SPELL_DRUID_LEADER_OF_THE_PACK_HEAL = 34299;

    // Swell sources and spenders (docs/reworks/druid-feral.md §2)
    constexpr uint8 SWELL_FROM_MAUL = 1;
    constexpr uint8 SWELL_FROM_THRASH = 1;
    constexpr uint32 THRASH_SWELL_MIN_TARGETS = 3;
    constexpr float SWELL_SPENDER_DAMAGE_PER_STACK = 0.25f;  // +25% damage per Swell consumed
    constexpr uint32 UPHEAVAL_SOFT_CAP_TARGETS = 5;          // sqrt(5 / N) past this
    constexpr uint32 UPHEAVAL_MAX_TARGETS = 10;

    constexpr int8 BERSERK_BONUS_COMBO_POINTS = 4;           // CORE-AUDIT row 33
    constexpr int32 SAVAGE_DEFENSE_BERSERK_MULTIPLIER = 2;
    constexpr int32 KING_OF_THE_JUNGLE_ENERGY_TICKS = 10;    // 200432: 1 s amplitude over 10 s

    // Internal cooldowns and fixed cooldown reductions (FERAL-WP-BRIEF §5)
    constexpr uint32 IRON_HIDE_ICD_MS = 1000;
    constexpr uint32 IRON_HIDE_BARKSKIN_REDUCTION_MS = 1000;
    constexpr uint32 BLOODLETTING_ICD_MS = 3000;
    constexpr uint32 IMPROVED_MANGLE_ICD_MS = 3000;
    constexpr uint32 IMPROVED_MANGLE_ENRAGE_REDUCTION_MS = 3000;
    constexpr uint32 LEADER_OF_THE_PACK_ICD_MS = 6000;
    constexpr Milliseconds BARKSKIN_FLOOR_DELAY{ 2 };        // after Cooldown Haste's own 1 ms correction

    constexpr float MASTERY_CHANGE_EPSILON = 0.001f;

    // PLAN §3 item 8: a chance the script rolls itself is scaled by the player's Proc Chance
    // (spell_proc-driven chances get it automatically; these don't).
    bool RollProcChance(Player const* player, float chancePct)
    {
        float const scaled = chancePct * (1.0f + player->GetProcChancePercentage() / 100.0f);
        return roll_chance_f(std::min(100.0f, scaled));
    }

    bool HasAnyAura(Unit const* unit, std::initializer_list<uint32> spellIds)
    {
        return std::any_of(spellIds.begin(), spellIds.end(), [unit](uint32 spellId)
        {
            return unit->HasAura(spellId);
        });
    }
}

// 200420 - Ironfur: Iron Hide (9,0) reduces Barkskin's cooldown on every cast, at most once a second.
class spell_dru_ironfur : public SpellScript
{
    PrepareSpellScript(spell_dru_ironfur);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BARKSKIN, Druid::SPELL_IRON_HIDE_R1, Druid::SPELL_IRON_HIDE_R2,
                                   Druid::SPELL_IRON_HIDE_R3 });
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        if (!HasAnyAura(caster, { Druid::SPELL_IRON_HIDE_R3, Druid::SPELL_IRON_HIDE_R2, Druid::SPELL_IRON_HIDE_R1 }))
            return;

        // The rank-1 id is every rank's 1 s internal cooldown marker.
        if (!Druid::TryStartInternalCooldown(caster, Druid::SPELL_IRON_HIDE_R1, IRON_HIDE_ICD_MS))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_BARKSKIN, IRON_HIDE_BARKSKIN_REDUCTION_MS);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_ironfur::HandleAfterCast);
    }
};

// 200420 (aura half of the pair) - Ironfur: expiry drops one stack and restarts the shared timer.
class spell_dru_ironfur_aura : public AuraScript
{
    PrepareAuraScript(spell_dru_ironfur_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_IRONFUR });
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        uint8 const stacks = GetStackAmount();
        if (stacks > 1)
            Druid::RestartWithStacks(GetTarget(), Druid::SPELL_IRONFUR, uint8(stacks - 1), 0);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_ironfur_aura::HandleRemove, EFFECT_0,
                                                 SPELL_AURA_MOD_RESISTANCE_PCT, AURA_EFFECT_HANDLE_REAL);
    }
};

// 200421 - Pulverize: needs the caster's Lacerate at full stacks; +eff1% per Lacerate application and
// +25% per Swell consumed (separate multiplicative factors, FERAL §13 Q10). The crit roll and crit
// damage both happen before AfterHit, so they see Swell before it is consumed (spec §8.1).
class spell_dru_pulverize : public SpellScript
{
    PrepareSpellScript(spell_dru_pulverize);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_LACERATE });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        Aura const* lacerate = target->GetAura(Druid::SPELL_LACERATE, caster->GetGUID());
        if (!lacerate || lacerate->GetStackAmount() < lacerate->GetSpellInfo()->StackAmount)
            return SPELL_FAILED_TARGET_AURASTATE;

        return SPELL_CAST_OK;
    }

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        int32 const damage = GetHitDamage();
        if (!caster || !target || damage <= 0)
            return;

        uint8 lacerateStacks = 0;
        if (Aura const* lacerate = target->GetAura(Druid::SPELL_LACERATE, caster->GetGUID()))
            lacerateStacks = lacerate->GetStackAmount();

        float const perLacerate = float(GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster)) / 100.0f;
        float const swell = float(Druid::GetSwellStacksForDamage(caster));
        float const lacerateMult = 1.0f + perLacerate * float(lacerateStacks);
        float const swellMult = 1.0f + SWELL_SPENDER_DAMAGE_PER_STACK * swell;
        SetHitDamage(int32(float(damage) * lacerateMult * swellMult));
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Consumes every application, then reapplies Lacerate at one.
        if (Aura* lacerate = target->GetAura(Druid::SPELL_LACERATE, caster->GetGUID()))
        {
            lacerate->SetStackAmount(1);
            lacerate->RefreshDuration();
        }

        Druid::OnSwellSpent(caster, Druid::ConsumeSwell(caster, Druid::SWELL_MAX_CONSUMED));
        Druid::TryPrimalPrecisionBearReduction(caster, Druid::PRIMAL_PRECISION_PULVERIZE_REDUCTION_MS);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dru_pulverize::CheckCast);
        OnHit += SpellHitFn(spell_dru_pulverize::HandleOnHit);
        AfterHit += SpellHitFn(spell_dru_pulverize::HandleAfterHit);
    }
};

// 200422 - Upheaval: the 10 closest enemies, sqrt(5 / N) falloff past 5, +25% per Swell consumed.
class spell_dru_upheaval : public SpellScript
{
    PrepareSpellScript(spell_dru_upheaval);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (targets.size() > UPHEAVAL_MAX_TARGETS)
        {
            targets.sort(Acore::ObjectDistanceOrderPred(GetCaster()));
            targets.resize(UPHEAVAL_MAX_TARGETS);
        }

        _targetCount = uint32(targets.size());
    }

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        int32 const damage = GetHitDamage();
        if (!caster || damage <= 0)
            return;

        float mult = 1.0f + SWELL_SPENDER_DAMAGE_PER_STACK * float(Druid::GetSwellStacksForDamage(caster));
        if (_targetCount > UPHEAVAL_SOFT_CAP_TARGETS)
            mult *= std::sqrt(float(UPHEAVAL_SOFT_CAP_TARGETS) / float(_targetCount));

        SetHitDamage(int32(float(damage) * mult));
    }

    // Once per cast, after every target was hit. An Upheaval that hit nothing consumes nothing.
    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (_targetCount && caster)
            Druid::OnSwellSpent(caster, Druid::ConsumeSwell(caster, Druid::SWELL_MAX_CONSUMED));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dru_upheaval::FilterTargets, EFFECT_ALL,
                                                                    TARGET_UNIT_SRC_AREA_ENEMY);
        OnHit += SpellHitFn(spell_dru_upheaval::HandleOnHit);
        AfterCast += SpellCastFn(spell_dru_upheaval::HandleAfterCast);
    }

private:
    uint32 _targetCount = 0;
};

// 200423 - Thrash: grants 1 Swell when it hits 3 or more targets (AddSwell requires Bestial Fury).
class spell_dru_thrash : public SpellScript
{
    PrepareSpellScript(spell_dru_thrash);

    // EFFECT_ALL, not one hook per effect: Spell::CheckScriptEffectImplicitTargets only lets the three
    // effects share one target selection when the same hook covers all of them - single-effect hooks
    // would give each effect its own random target list.
    void CountTargets(std::list<WorldObject*>& targets)
    {
        _targetCount = uint32(targets.size());
    }

    void HandleAfterCast()
    {
        if (_targetCount >= THRASH_SWELL_MIN_TARGETS && GetCaster())
            Druid::AddSwell(GetCaster(), SWELL_FROM_THRASH);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dru_thrash::CountTargets, EFFECT_ALL,
                                                                    TARGET_UNIT_SRC_AREA_ENEMY);
        AfterCast += SpellCastFn(spell_dru_thrash::HandleAfterCast);
    }

private:
    uint32 _targetCount = 0;
};

// 200425 - Bestial Fury (FORM_BEAR): toggling it off - clicking it again or cancelling the buff -
// lands in Bear Form rather than caster form, keeping the rage (FERAL §0.16, WP-BRIEF §4 item 3).
// Shifting to another form by casting it removes the aura with another mode and does nothing here.
class spell_dru_bestial_fury : public AuraScript
{
    PrepareAuraScript(spell_dru_bestial_fury);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BEAR_FORM });
    }

    // Runs before the shapeshift handler switches the power type to mana, which empties rage.
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() == AURA_REMOVE_BY_CANCEL)
            _savedRage = GetTarget()->GetPower(POWER_RAGE);
    }

    void HandleAfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_CANCEL)
            return;

        Unit* target = GetTarget();
        if (target->CastSpell(target, Druid::SPELL_BEAR_FORM, TRIGGERED_FULL_MASK) != SPELL_CAST_OK)
            return;

        // Entering Bear Form switches the power type back to rage, which zeroes it (Unit::setPowerType).
        target->SetPower(POWER_RAGE, _savedRage);
    }

    void Register() override
    {
        OnEffectRemove += AuraEffectRemoveFn(spell_dru_bestial_fury::HandleRemove, EFFECT_0,
                                              SPELL_AURA_MOD_SHAPESHIFT, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_bestial_fury::HandleAfterRemove, EFFECT_0,
                                                 SPELL_AURA_MOD_SHAPESHIFT, AURA_EFFECT_HANDLE_REAL);
    }

private:
    uint32 _savedRage = 0;
};

// 200426 - Swell: expiry drops one stack and restarts the timer; every removal refreshes the
// Swell-scaled talents (Splintering Blows, Bonebreaker).
class spell_dru_swell : public AuraScript
{
    PrepareAuraScript(spell_dru_swell);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_SWELL });
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        uint8 const stacks = GetStackAmount();
        if (GetTargetApplication()->GetRemoveMode() == AURA_REMOVE_BY_EXPIRE && stacks > 1)
        {
            int32 const duration = target->IsInCombat() ? Druid::SWELL_DURATION_IN_COMBAT_MS
                                                        : Druid::SWELL_DURATION_OUT_OF_COMBAT_MS;
            Druid::RestartWithStacks(target, Druid::SPELL_SWELL, uint8(stacks - 1), duration);
        }

        Druid::OnSwellChanged(target);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_swell::HandleRemove, EFFECT_0,
                                                 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, AURA_EFFECT_HANDLE_REAL);
    }
};

// 200429 - Fury Swipe (Fury Swipes 4,1): the 20 rage only in Bear Form or Bestial Fury.
class spell_dru_fury_swipe : public SpellScript
{
    PrepareSpellScript(spell_dru_fury_swipe);

    void HandleEnergize(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        if (!caster || !Druid::IsInBearForm(caster))
            PreventHitDefaultEffect(effIndex);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dru_fury_swipe::HandleEnergize, EFFECT_1, SPELL_EFFECT_ENERGIZE);
    }
};

// 6807 - Maul: 1 Swell per cast (AddSwell is a no-op outside Bestial Fury).
class spell_dru_maul : public SpellScript
{
    PrepareSpellScript(spell_dru_maul);

    // FERAL-ADDENDUM decision 5: a cast that hit nothing (evade, immune) never rolls Tooth and Claw.
    void HandleHit()
    {
        _hitAny = true;
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        Druid::AddSwell(caster, SWELL_FROM_MAUL);

        if (_hitAny)
            Druid::TryGrantToothAndClaw(caster, Druid::TOOTH_AND_CLAW_MAUL_MANGLE_CHANCE_PCT);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dru_maul::HandleHit);
        AfterCast += SpellCastFn(spell_dru_maul::HandleAfterCast);
    }

private:
    bool _hitAny = false;
};

// 200439 - Savage Bite (docs/reworks/druid-feral-addition.md, FERAL-ADDENDUM.md): usable only with a
// Tooth and Claw charge, enforced by data (CasterAuraSpell 200438). Consumes 1 charge and triggers
// Nurturing Instinct exactly like a Predator's Swiftness Regrowth would. Sharing Pulverize's family
// bit (§3.3, user decision) already gives it Splintering Blows' crit chance and lets it both benefit
// from and spend an already-active Nurturing Instinct buff - no extra code for either. Never touches
// Swell and never rolls Tooth and Claw itself. Primal Precision's bear clause takes 3 sec off Berserk.
class spell_dru_savage_bite : public SpellScript
{
    PrepareSpellScript(spell_dru_savage_bite);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_TOOTH_AND_CLAW });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster || !GetHitUnit())
            return;

        if (Aura* toothAndClaw = caster->GetAura(Druid::SPELL_TOOTH_AND_CLAW, caster->GetGUID()))
            toothAndClaw->ModStackAmount(-1);

        Druid::ApplyNurturingInstinctEmpower(caster);
        Druid::TryPrimalPrecisionBearReduction(caster, Druid::PRIMAL_PRECISION_SAVAGE_BITE_REDUCTION_MS);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_savage_bite::HandleAfterHit);
    }
};

// 33745 - Lacerate: Flesh Render (1,2) - a chance to add an extra application, up to the stack cap.
class spell_dru_lacerate : public SpellScript
{
    PrepareSpellScript(spell_dru_lacerate);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_LACERATE, Druid::SPELL_FLESH_RENDER_R1, Druid::SPELL_FLESH_RENDER_R2,
                                   Druid::SPELL_FLESH_RENDER_R3 });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 const chance = Druid::GetRankAmount(caster,
            { Druid::SPELL_FLESH_RENDER_R3, Druid::SPELL_FLESH_RENDER_R2, Druid::SPELL_FLESH_RENDER_R1 }, EFFECT_2);
        if (chance <= 0 || !RollProcChance(caster, float(chance)))
            return;

        Aura* lacerate = target->GetAura(Druid::SPELL_LACERATE, caster->GetGUID());
        if (lacerate && lacerate->GetStackAmount() < lacerate->GetSpellInfo()->StackAmount)
            lacerate->ModStackAmount(1);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_lacerate::HandleAfterHit);
    }
};

// 22568 - Ferocious Bite: Sabertooth (6,3) extends the caster's Rip on the target, capped at 1.5x
// Rip's own duration (after the caster's duration mods) in total. MaxDuration moves first, so the
// pro-rated final tick is computed from the extended duration (spec §8.5).
class spell_dru_ferocious_bite : public SpellScript
{
    PrepareSpellScript(spell_dru_ferocious_bite);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_RIP, Druid::SPELL_SABERTOOTH_R1, Druid::SPELL_SABERTOOTH_R2,
                                   Druid::SPELL_SABERTOOTH_R3 });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 const extensionSec = Druid::GetRankAmount(caster,
            { Druid::SPELL_SABERTOOTH_R3, Druid::SPELL_SABERTOOTH_R2, Druid::SPELL_SABERTOOTH_R1 }, EFFECT_0);
        if (extensionSec <= 0)
            return;

        Aura* rip = target->GetAura(Druid::SPELL_RIP, caster->GetGUID());
        if (!rip)
            return;

        int32 baseDuration = rip->GetSpellInfo()->GetMaxDuration();
        caster->ApplySpellMod(rip->GetId(), SPELLMOD_DURATION, baseDuration);

        int32 const cap = baseDuration * 3 / 2;
        int32 const currentMax = rip->GetMaxDuration();
        int32 const newMax = std::min<int32>(cap, currentMax + extensionSec * IN_MILLISECONDS);
        if (newMax <= currentMax)
            return;

        rip->SetMaxDuration(newMax);
        rip->SetDuration(rip->GetDuration() + (newMax - currentMax));
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_ferocious_bite::HandleAfterHit);
    }
};

// 1079, 22568, 52610, 22570 - Rip / Ferocious Bite / Savage Roar / Maim: Primal Precision r2 capstone
// (3,3) - finishers reduce Berserk's cooldown, at most once every 5 sec (FERAL-ADDENDUM §3.7 - was
// 3 sec, now the same shared ICD as Druid::TryPrimalPrecisionBearReduction). Nothing happens, and no
// ICD is burned, while Berserk is active (decision: rule 9).
class spell_dru_primal_precision : public SpellScript
{
    PrepareSpellScript(spell_dru_primal_precision);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_PRIMAL_PRECISION_R2, Druid::SPELL_BERSERK });
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster || caster->HasAura(Druid::SPELL_BERSERK))
            return;

        AuraEffect const* capstone = caster->GetAuraEffect(Druid::SPELL_PRIMAL_PRECISION_R2, EFFECT_1);
        if (!capstone || capstone->GetAmount() <= 0)
            return;

        // 48410 doubles as its own internal cooldown marker.
        if (!Druid::TryStartInternalCooldown(caster, Druid::SPELL_PRIMAL_PRECISION_R2, Druid::PRIMAL_PRECISION_ICD_MS))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_BERSERK, uint32(capstone->GetAmount() * IN_MILLISECONDS));
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_primal_precision::HandleAfterCast);
    }
};

// 48409, 48410 - Primal Precision: while Bestial Fury is active, increases haste by 5/10%
// (FERAL-ADDENDUM §3.7). EFFECT_2 zeroed outside Bestial Fury; druid_hooks.cpp's shapeshift handler
// recalculates it on every form change (DruidMechanics.cpp's OnFeralFormChanged).
class spell_dru_primal_precision_haste : public AuraScript
{
    PrepareAuraScript(spell_dru_primal_precision_haste);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        if (!owner || !Druid::IsBestialFuryActive(owner))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_primal_precision_haste::CalculateAmount, EFFECT_2,
                                                      SPELL_AURA_MELEE_SLOW);
    }
};

// 1822 - Rake: Bloodletting r2 capstone (4,2) - reduces Tiger's Fury's cooldown, at most once every
// 3 sec.
class spell_dru_rake : public SpellScript
{
    PrepareSpellScript(spell_dru_rake);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BLOODLETTING_R2, Druid::SPELL_TIGERS_FURY });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        AuraEffect const* capstone = caster->GetAuraEffect(Druid::SPELL_BLOODLETTING_R2, EFFECT_2);
        if (!capstone || capstone->GetAmount() <= 0)
            return;

        // 200455 doubles as its own internal cooldown marker.
        if (!Druid::TryStartInternalCooldown(caster, Druid::SPELL_BLOODLETTING_R2, BLOODLETTING_ICD_MS))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_TIGERS_FURY, uint32(capstone->GetAmount() * IN_MILLISECONDS));
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_rake::HandleAfterHit);
    }
};

// 5221, 6785 - Shred / Ravage: Shredding Attacks r2 capstone (3,0) - from behind, applies a stack of
// Shredded Defense (the per-stack damage bonus itself is read in druid_hooks.cpp).
class spell_dru_shredding_attacks : public SpellScript
{
    PrepareSpellScript(spell_dru_shredding_attacks);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_SHREDDING_ATTACKS_R2, Druid::SPELL_SHREDDED_DEFENSE });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        if (!caster->HasAura(Druid::SPELL_SHREDDING_ATTACKS_R2))
            return;

        // WorldObject::isInBack(obj) is "obj is behind me", so this is "the caster is behind the target".
        if (!target->isInBack(caster))
            return;

        caster->CastSpell(target, Druid::SPELL_SHREDDED_DEFENSE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_shredding_attacks::HandleAfterHit);
    }
};

// 6785 - Ravage: the stealth requirement moves from the ONLY_STEALTHED attribute (removed in data, the
// client checks it too) to here, so Stampede (Cat) can waive it.
class spell_dru_ravage : public SpellScript
{
    PrepareSpellScript(spell_dru_ravage);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_STAMPEDE_CAT });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster && (caster->HasStealthAura() || caster->HasAura(Druid::SPELL_STAMPEDE_CAT)))
            return SPELL_CAST_OK;

        return SPELL_FAILED_ONLY_STEALTHED;
    }

    void HandleAfterCast()
    {
        if (Unit* caster = GetCaster())
            caster->RemoveAurasDueToSpell(Druid::SPELL_STAMPEDE_CAT);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dru_ravage::CheckCast);
        AfterCast += SpellCastFn(spell_dru_ravage::HandleAfterCast);
    }
};

// 33876, 33878 - Mangle (Cat) / Mangle (Bear): Infected Wounds (7,3) attack-speed slow on both;
// Improved Mangle r2 capstone (8,2) on Mangle (Bear) only - a chance for 15 rage, and Enrage's
// cooldown reduced, at most once every 3 sec.
class spell_dru_mangle : public SpellScript
{
    PrepareSpellScript(spell_dru_mangle);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            Druid::SPELL_INFECTED_WOUNDS_R1, Druid::SPELL_INFECTED_WOUNDS_R2, Druid::SPELL_INFECTED_WOUNDS_R3,
            Druid::SPELL_INFECTED_WOUNDS_SLOW_R1, Druid::SPELL_INFECTED_WOUNDS_SLOW_R2,
            Druid::SPELL_INFECTED_WOUNDS_SLOW_R3, Druid::SPELL_MANGLE_BEAR, Druid::SPELL_IMPROVED_MANGLE_R2,
            Druid::SPELL_IMP_MANGLE_RAGE, Druid::SPELL_ENRAGE
        });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        _hitAny = true;

        static constexpr std::array<std::pair<uint32, uint32>, 3> infectedWounds =
        {{
            { Druid::SPELL_INFECTED_WOUNDS_R3, Druid::SPELL_INFECTED_WOUNDS_SLOW_R3 },
            { Druid::SPELL_INFECTED_WOUNDS_R2, Druid::SPELL_INFECTED_WOUNDS_SLOW_R2 },
            { Druid::SPELL_INFECTED_WOUNDS_R1, Druid::SPELL_INFECTED_WOUNDS_SLOW_R1 }
        }};

        for (auto const& [rank, slow] : infectedWounds)
        {
            if (!caster->HasAura(rank))
                continue;

            caster->CastSpell(target, slow, TRIGGERED_FULL_MASK);
            break;
        }

        if (GetSpellInfo()->Id != Druid::SPELL_MANGLE_BEAR)
            return;

        AuraEffect const* capstone = caster->GetAuraEffect(Druid::SPELL_IMPROVED_MANGLE_R2, EFFECT_2);
        if (!capstone)
            return;

        if (RollProcChance(caster, float(capstone->GetAmount())))
            caster->CastSpell(caster, Druid::SPELL_IMP_MANGLE_RAGE, TRIGGERED_FULL_MASK);

        // 48489 doubles as its own internal cooldown marker.
        if (!Druid::TryStartInternalCooldown(caster, Druid::SPELL_IMPROVED_MANGLE_R2, IMPROVED_MANGLE_ICD_MS))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_ENRAGE, IMPROVED_MANGLE_ENRAGE_REDUCTION_MS);
    }

    // FERAL-ADDENDUM §3.2: Mangle (Bear) rolls Tooth and Claw once per cast, only when it hit
    // something. Mangle (Cat) never rolls it (Tooth and Claw requires Bestial Fury, form 5, which
    // can't be in Cat Form anyway - the Id check is the belt-and-suspenders reason for both).
    void HandleAfterCast()
    {
        if (!_hitAny || GetSpellInfo()->Id != Druid::SPELL_MANGLE_BEAR)
            return;

        if (Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
            Druid::TryGrantToothAndClaw(caster, Druid::TOOTH_AND_CLAW_MAUL_MANGLE_CHANCE_PCT);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_mangle::HandleAfterHit);
        AfterCast += SpellCastFn(spell_dru_mangle::HandleAfterCast);
    }

private:
    bool _hitAny = false;
};

// 16979, 49376 - Feral Charge (Bear) / (Cat): Feral Swiftness r2 capstone (2,0), Stampede.
class spell_dru_feral_charge : public SpellScript
{
    PrepareSpellScript(spell_dru_feral_charge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DRUID_FERAL_CHARGE_BEAR, SPELL_DRUID_FERAL_CHARGE_CAT,
                                   Druid::SPELL_FERAL_SWIFTNESS_R2, Druid::SPELL_MANGLE_BEAR,
                                   Druid::SPELL_STAMPEDE_BEAR, Druid::SPELL_STAMPEDE_CAT });
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster || !caster->HasAura(Druid::SPELL_FERAL_SWIFTNESS_R2))
            return;

        uint32 const spellId = GetSpellInfo()->Id;
        if (spellId == SPELL_DRUID_FERAL_CHARGE_BEAR)
        {
            caster->RemoveSpellCooldown(Druid::SPELL_MANGLE_BEAR, true);
            caster->CastSpell(caster, Druid::SPELL_STAMPEDE_BEAR, TRIGGERED_FULL_MASK);
        }
        else if (spellId == SPELL_DRUID_FERAL_CHARGE_CAT)
            caster->CastSpell(caster, Druid::SPELL_STAMPEDE_CAT, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_feral_charge::HandleAfterCast);
    }
};

// 5221, 1822, 33876, 6785, 9005 - Shred / Rake / Mangle (Cat) / Ravage / Pounce: Berserk
// makes combo point generators grant 4 more (CORE-AUDIT row 33). The builder's own gain is already on
// the Spell by OnHit (its combo point effect runs in DoSpellHitOnUnit) and is applied in
// Spell::_handle_finish_phase.
class spell_dru_berserk_combo_points : public SpellScript
{
    PrepareSpellScript(spell_dru_berserk_combo_points);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BERSERK });
    }

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        Spell* spell = GetSpell();
        if (!caster || spell->IsTriggered() || !caster->HasAura(Druid::SPELL_BERSERK))
            return;

        // AddComboPointGain resets the gain when handed a different unit, so pass the spell's own
        // combo target rather than the hit unit.
        if (spell->m_comboTarget && spell->m_comboPointGain > 0)
            spell->AddComboPointGain(spell->m_comboTarget, BERSERK_BONUS_COMBO_POINTS);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dru_berserk_combo_points::HandleOnHit);
    }
};

// 200459, 200460 - Savage Defense (6,0): a direct crit in Bear Form adds a share of current armor to
// the 62606 absorb pool (doubled under Berserk). Crit-only, direct-only and the 3 s cooldown are the
// spell_proc row; the pool itself is a plain absorb with no script.
class spell_dru_savage_defense_talent : public AuraScript
{
    PrepareAuraScript(spell_dru_savage_defense_talent);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_SAVAGE_DEFENSE_ABSORB, Druid::SPELL_BERSERK });
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        Unit* target = GetTarget();
        return Druid::IsInBearForm(target) && !Druid::IsBestialFuryActive(target);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        int32 gain = CalculatePct(int32(target->GetArmor()), aurEff->GetAmount());
        if (target->HasAura(Druid::SPELL_BERSERK))
            gain *= SAVAGE_DEFENSE_BERSERK_MULTIPLIER;

        if (gain <= 0)
            return;

        // Recasting refreshes the existing pool with the new base points, so carry what is left of it.
        int32 pool = gain;
        if (AuraEffect const* existing =
                target->GetAuraEffect(Druid::SPELL_SAVAGE_DEFENSE_ABSORB, EFFECT_0, target->GetGUID()))
            pool += existing->GetAmount();

        target->CastCustomSpell(Druid::SPELL_SAVAGE_DEFENSE_ABSORB, SPELLVALUE_BASE_POINT0, pool, target, true,
                                 nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_savage_defense_talent::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dru_savage_defense_talent::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 8936, 5185 - Regrowth / Healing Touch: Nurturing Instinct (4,3) - a cast made instant by Predatory
// Strikes (Predator's Swiftness) empowers the next 2 melee abilities.
class spell_dru_nurturing_instinct_empower : public SpellScript
{
    PrepareSpellScript(spell_dru_nurturing_instinct_empower);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_PREDATORS_SWIFTNESS, Druid::SPELL_NURTURING_INSTINCT_R1,
                                   Druid::SPELL_NURTURING_INSTINCT_R2, Druid::SPELL_NI_EMPOWER });
    }

    // Predator's Swiftness is still on the caster here: its charge drops when the cast's spell mods
    // are removed, after BeforeCast.
    void HandleBeforeCast()
    {
        Unit* caster = GetCaster();
        Spell const* spell = GetSpell();
        _madeInstant = caster && !spell->IsTriggered() && spell->GetCastTime() == 0 &&
                       caster->HasAura(Druid::SPELL_PREDATORS_SWIFTNESS);
    }

    // FERAL-ADDENDUM §3.3/§3.8: this class is bound only to Regrowth (unbind_script dropped the
    // Healing Touch binding - user override, Predator's Swiftness/Nurturing Instinct are Regrowth
    // only). The shared body also fires from Savage Bite.
    void HandleAfterCast()
    {
        if (!_madeInstant)
            return;

        if (Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
            Druid::ApplyNurturingInstinctEmpower(caster);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_dru_nurturing_instinct_empower::HandleBeforeCast);
        AfterCast += SpellCastFn(spell_dru_nurturing_instinct_empower::HandleAfterCast);
    }

private:
    bool _madeInstant = false;
};

// 57873, 57876, 57877 - Protector of the Pack (7,0): the physical damage reduction is suppressed while
// Bestial Fury is active. druid_hooks.cpp's shapeshift handler recalculates it on every form change.
class spell_dru_protector_of_the_pack : public AuraScript
{
    PrepareAuraScript(spell_dru_protector_of_the_pack);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        if (owner && Druid::IsBestialFuryActive(owner))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_protector_of_the_pack::CalculateAmount, EFFECT_1,
                                                      SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// 33853, 33855, 33856 - Survival of the Fittest (5,2): the attack power bonus only while Bestial Fury
// is active. Recalculated on every form change by druid_hooks.cpp.
class spell_dru_survival_of_the_fittest : public AuraScript
{
    PrepareAuraScript(spell_dru_survival_of_the_fittest);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        if (!owner || !Druid::IsBestialFuryActive(owner))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_survival_of_the_fittest::CalculateAmount, EFFECT_1,
                                                      SPELL_AURA_MOD_ATTACK_POWER_PCT);
    }
};

// 33859, 33866, 33867 - Predatory Instincts (7,2): the crit damage bonus only in Cat Form (the talent
// carries no ShapeshiftMask so its AoE reduction works in every form). Recalculated on every form
// change by druid_hooks.cpp.
class spell_dru_predatory_instincts : public AuraScript
{
    PrepareAuraScript(spell_dru_predatory_instincts);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        if (!owner || owner->GetShapeshiftForm() != FORM_CAT)
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_predatory_instincts::CalculateAmount, EFFECT_0,
                                                      SPELL_AURA_MOD_CRIT_DAMAGE_BONUS);
    }
};

// 200464, 200465, 200466 - Splintering Blows (8,3): Pulverize crit chance per Swell stack (CORE-AUDIT
// row 23). Recalculated by Druid::OnSwellChanged whenever the stack count changes.
class spell_dru_splintering_blows : public AuraScript
{
    PrepareAuraScript(spell_dru_splintering_blows);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        amount = owner ? amount * int32(Druid::GetSwellStacks(owner)) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_splintering_blows::CalculateAmount, EFFECT_0,
                                                      SPELL_AURA_ADD_FLAT_MODIFIER);
    }
};

// 200456, 200457, 200458 - Bonebreaker (5,3): +P crit damage points per Swell stack on the 200% base,
// scaled by 150% of Mastery at rank 3 (CORE-AUDIT row 25, FERAL §0.16). Aura 163 multiplies the whole
// crit, so P points on the total are P / 2 on the aura: rank 3, 5 stacks, no Mastery -> 100 -> 400%.
// Recalculated by Druid::OnSwellChanged whenever the stack count changes.
class spell_dru_bonebreaker : public AuraScript
{
    PrepareAuraScript(spell_dru_bonebreaker);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BONEBREAKER_R3 });
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Unit* owner = GetUnitOwner();
        uint8 const stacks = owner ? Druid::GetSwellStacks(owner) : 0;
        if (!stacks)
        {
            amount = 0;
            return;
        }

        float value = float(amount) / 2.0f * float(stacks);

        // EFFECT_1's AuraEffect isn't built yet while EFFECT_0 is being created, so read the spell data.
        Player const* player = owner->ToPlayer();
        if (player && GetId() == Druid::SPELL_BONEBREAKER_R3)
        {
            float const masteryShare = float(GetSpellInfo()->Effects[EFFECT_1].CalcValue(owner));
            value *= 1.0f + masteryShare / 100.0f * player->GetMasteryPercentage() / 100.0f;
        }

        amount = int32(std::lround(value));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_bonebreaker::CalculateAmount, EFFECT_0,
                                                      SPELL_AURA_MOD_CRIT_DAMAGE_BONUS);
    }
};

// 17005 - Heart of the Wild r3 (5,1): its Mastery-scaled max health only refreshes on UpdateMaxHealth,
// so a 5 s check picks up Mastery-only gear/buff changes (CORE-AUDIT row 29, PLAN C4).
class spell_dru_heart_of_the_wild_mastery : public AuraScript
{
    PrepareAuraScript(spell_dru_heart_of_the_wild_mastery);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        float const mastery = player->GetMasteryPercentage();
        if (std::fabs(mastery - _lastMastery) < MASTERY_CHANGE_EPSILON)
            return;

        _lastMastery = mastery;
        player->UpdateMaxHealth();
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_heart_of_the_wild_mastery::HandlePeriodic, EFFECT_2,
                                                  SPELL_AURA_PERIODIC_DUMMY);
    }

private:
    float _lastMastery = -1.0f;
};

// 22842 - Frenzied Regeneration - replaces stock spell_dru_frenzied_regeneration (a rage-to-health
// AuraScript): now a flat HEAL_PCT, plus Heart of the Wild's Mastery capstone.
class spell_dru_frenzied_regeneration_feral : public SpellScript
{
    PrepareSpellScript(spell_dru_frenzied_regeneration_feral);

    void HandleOnHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        int32 heal = GetHitHeal();
        if (!caster || heal <= 0)
            return;

        float const pct = Druid::GetHeartOfTheWildMasteryPct(caster);
        if (pct <= 0.0f)
            return;

        AddPct(heal, pct);
        SetHitHeal(heal);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dru_frenzied_regeneration_feral::HandleOnHit);
    }
};

// 5217 - Tiger's Fury - replaces stock spell_dru_tiger_s_fury: Feral Instinct (1,0) damage buff for
// Tiger's Fury's duration, and King of the Jungle (8,0) energy over 10 sec instead of instantly.
class spell_dru_tiger_s_fury_feral : public SpellScript
{
    PrepareSpellScript(spell_dru_tiger_s_fury_feral);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            Druid::SPELL_TIGERS_FURY, Druid::SPELL_FERAL_INSTINCT_R1, Druid::SPELL_FERAL_INSTINCT_R2,
            Druid::SPELL_FERAL_INSTINCT_R3, Druid::SPELL_FERAL_INSTINCT_BUFF, Druid::SPELL_KING_OF_THE_JUNGLE_R1,
            Druid::SPELL_KING_OF_THE_JUNGLE_R2, Druid::SPELL_KING_OF_THE_JUNGLE_R3, Druid::SPELL_KOTJ_ENERGY
        });
    }

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster)
            return;

        int32 const damageBonus = Druid::GetRankAmount(caster,
            { Druid::SPELL_FERAL_INSTINCT_R3, Druid::SPELL_FERAL_INSTINCT_R2, Druid::SPELL_FERAL_INSTINCT_R1 },
            EFFECT_0);
        if (damageBonus > 0)
        {
            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT0, damageBonus);
            if (Aura const* tigersFury = caster->GetAura(Druid::SPELL_TIGERS_FURY))
                values.AddSpellMod(SPELLVALUE_AURA_DURATION, tigersFury->GetDuration());

            caster->CastCustomSpell(Druid::SPELL_FERAL_INSTINCT_BUFF, values, caster, TRIGGERED_FULL_MASK);
        }

        int32 const energy = Druid::GetRankAmount(caster,
            { Druid::SPELL_KING_OF_THE_JUNGLE_R3, Druid::SPELL_KING_OF_THE_JUNGLE_R2,
              Druid::SPELL_KING_OF_THE_JUNGLE_R1 }, EFFECT_1);
        if (energy > 0)
            caster->CastCustomSpell(Druid::SPELL_KOTJ_ENERGY, SPELLVALUE_BASE_POINT0,
                                     energy / KING_OF_THE_JUNGLE_ENERGY_TICKS, caster, true);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_tiger_s_fury_feral::HandleAfterHit);
    }
};

// 50334 - Berserk - replaces stock spell_dru_berserk: still ends Tiger's Fury, no longer resets Mangle
// (Bear), and grants maximum Swell while Bestial Fury is active (AddSwell's own check).
class spell_dru_berserk_feral : public SpellScript
{
    PrepareSpellScript(spell_dru_berserk_feral);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_TIGERS_FURY, Druid::SPELL_FERAL_INSTINCT_BUFF });
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->RemoveAurasDueToSpell(Druid::SPELL_TIGERS_FURY);
        // Feral Instinct's buff is "while Tiger's Fury is active", so it ends with it.
        caster->RemoveAurasDueToSpell(Druid::SPELL_FERAL_INSTINCT_BUFF);
        Druid::AddSwell(caster, Druid::SWELL_MAX_STACKS);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_berserk_feral::HandleAfterCast);
    }
};

// 24932 - Leader of the Pack - replaces stock spell_dru_leader_of_the_pack: heals 4% of base health
// (FERAL §0.16) instead of max health, and drops Improved Leader of the Pack's mana clause.
class spell_dru_leader_of_the_pack_feral : public AuraScript
{
    PrepareAuraScript(spell_dru_leader_of_the_pack_feral);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DRUID_LEADER_OF_THE_PACK_HEAL });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        int32 const healPct = aurEff->GetAmount();
        if (healPct <= 0)
            return;

        // 6 second internal cooldown - only trackable when the target is a player; a non-player
        // target (no spell cooldown map) always heals, same as before this helper existed.
        Player* player = target->ToPlayer();
        if (player && !Druid::TryStartInternalCooldown(player, SPELL_DRUID_LEADER_OF_THE_PACK_HEAL, LEADER_OF_THE_PACK_ICD_MS))
            return;

        int32 const heal = CalculatePct(int32(target->GetCreateHealth()), healPct);
        target->CastCustomSpell(SPELL_DRUID_LEADER_OF_THE_PACK_HEAL, SPELLVALUE_BASE_POINT0, heal, target, true,
                                 nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dru_leader_of_the_pack_feral::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 22812 - Barkskin: the 30 s cooldown floor (B7, CORE-AUDIT row 34). Records the cast time, then
// clamps the cooldown 2 ms later - after Cooldown Haste's own 1 ms deferred correction.
class spell_dru_barkskin_floor : public SpellScript
{
    PrepareSpellScript(spell_dru_barkskin_floor);

    void HandleAfterCast()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player)
            return;

        Druid::OnBarkskinCast(player);

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            if (Player* target = ObjectAccessor::FindPlayer(guid))
                Druid::ApplyBarkskinFloor(target);
        }, BARKSKIN_FLOOR_DELAY);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_barkskin_floor::HandleAfterCast);
    }
};

void AddSC_druid_feral_spell_scripts()
{
    RegisterSpellAndAuraScriptPair(spell_dru_ironfur, spell_dru_ironfur_aura);
    RegisterSpellScript(spell_dru_pulverize);
    RegisterSpellScript(spell_dru_upheaval);
    RegisterSpellScript(spell_dru_thrash);
    RegisterSpellScript(spell_dru_bestial_fury);
    RegisterSpellScript(spell_dru_swell);
    RegisterSpellScript(spell_dru_fury_swipe);
    RegisterSpellScript(spell_dru_maul);
    RegisterSpellScript(spell_dru_savage_bite);
    RegisterSpellScript(spell_dru_lacerate);
    RegisterSpellScript(spell_dru_ferocious_bite);
    RegisterSpellScript(spell_dru_primal_precision);
    RegisterSpellScript(spell_dru_primal_precision_haste);
    RegisterSpellScript(spell_dru_rake);
    RegisterSpellScript(spell_dru_shredding_attacks);
    RegisterSpellScript(spell_dru_ravage);
    RegisterSpellScript(spell_dru_mangle);
    RegisterSpellScript(spell_dru_feral_charge);
    RegisterSpellScript(spell_dru_berserk_combo_points);
    RegisterSpellScript(spell_dru_savage_defense_talent);
    RegisterSpellScript(spell_dru_nurturing_instinct_empower);
    RegisterSpellScript(spell_dru_protector_of_the_pack);
    RegisterSpellScript(spell_dru_survival_of_the_fittest);
    RegisterSpellScript(spell_dru_predatory_instincts);
    RegisterSpellScript(spell_dru_splintering_blows);
    RegisterSpellScript(spell_dru_bonebreaker);
    RegisterSpellScript(spell_dru_heart_of_the_wild_mastery);
    RegisterSpellScript(spell_dru_frenzied_regeneration_feral);
    RegisterSpellScript(spell_dru_tiger_s_fury_feral);
    RegisterSpellScript(spell_dru_berserk_feral);
    RegisterSpellScript(spell_dru_leader_of_the_pack_feral);
    RegisterSpellScript(spell_dru_barkskin_floor);
}
