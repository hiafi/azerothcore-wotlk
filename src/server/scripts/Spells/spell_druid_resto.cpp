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
 * Druid Restoration rework (docs/reworks/druid-resto.md,
 * .agents/plans/druid-rework/druid-rework.RESTO.md) - every genuinely new script class this pass
 * needs goes here, same "spell_dru_" naming convention as stock spell_druid.cpp and Balance's own
 * spell_druid_balance.cpp. A stock class that needs new behaviour is *replaced* by a same-named-idea
 * class here and rebound by SQL (the stock binding is DELETEd via a WP-A unbind_script, the stock
 * class itself is left in place, unbound) - see
 * .agents/plans/druid-rework/druid-rework.CORE-AUDIT.md §3 item 10 for why upstream-owned
 * spell_druid.cpp is never edited in place. Hooks that can't be a SpellScript/AuraScript at all
 * live in DruidMechanics.h/.cpp (core call sites, Resto section) or druid_hooks.cpp (ScriptMgr
 * handlers that run on every damage/heal event server-wide - CORE-AUDIT rows 11-21 for this pass).
 *
 * Six classes below (spell_dru_lifebloom_resto, spell_dru_living_seed_resto,
 * spell_dru_omen_of_clarity_resto, spell_dru_revitalize_resto, spell_dru_wild_growth_resto,
 * spell_dru_wild_growth_aura_resto) are new-name replacements for six stock spell_druid.cpp classes
 * (spell_dru_lifebloom, spell_dru_living_seed, spell_dru_omen_of_clarity, spell_dru_revitalize,
 * spell_dru_wild_growth, spell_dru_wild_growth_aura) - CORE-AUDIT §3 item 10 / WP-B brief "Critical
 * corrections" #4. The stock classes are untouched and left unbound; WP-A's DSL must
 * unbind_script(...) each stock binding and scripted_by(...) the matching name below - see the
 * table at the bottom of this comment.
 *
 * Stock ScriptName -> replacement (WP-A: unbind_script the left column, scripted_by the right):
 *   -33763 'spell_dru_lifebloom'         -> 'spell_dru_lifebloom_resto'
 *   -48496 'spell_dru_living_seed'       -> 'spell_dru_living_seed_resto'
 *    16864 'spell_dru_omen_of_clarity'   -> 'spell_dru_omen_of_clarity_resto' (also bind to the new
 *                                            200600/200601 ranks)
 *   -48539 'spell_dru_revitalize'        -> 'spell_dru_revitalize_resto'
 *   -48438 'spell_dru_wild_growth'       -> 'spell_dru_wild_growth_resto' (RegisterSpellAndAuraScriptPair
 *                                            registers spell_dru_wild_growth_aura_resto under the same
 *                                            ScriptName automatically - see AddSC below)
 */

#include "Cell.h"
#include "CellImpl.h"
#include "DruidMechanics.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "HealMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <list>

namespace
{
    // Stock ids this pass's replacement classes still need to reference, redeclared locally since
    // spell_druid.cpp's own anonymous enum isn't visible from this translation unit (same pattern
    // spell_druid_balance.cpp would use if it needed one).
    constexpr uint32 SPELL_DRUID_LIVING_SEED_PROC = 48504;
    constexpr uint32 SPELL_DRUID_BALANCE_T10_BONUS = 70718;
    constexpr uint32 SPELL_DRUID_BALANCE_T10_BONUS_PROC = 70721;
    constexpr uint32 SPELL_DRUID_REVITALIZE_ENERGIZE_MANA = 48542;
    constexpr uint32 SPELL_DRUID_REVITALIZE_ENERGIZE_RAGE = 48541;
    constexpr uint32 SPELL_DRUID_REVITALIZE_ENERGIZE_ENERGY = 48540;
    constexpr uint32 SPELL_DRUID_REVITALIZE_ENERGIZE_RP = 48543;
    constexpr uint32 SPELL_DRUID_GLYPH_OF_WILD_GROWTH = 62970;
    constexpr uint32 SPELL_DRUID_RESTORATION_T10_2P_BONUS = 70658;
}

// 5185, 8936, 18562, 200560, 200561, 44203, 200569 - Harmony / Nature's Mending / Waking Dream /
// Omen capstone direct-heal multiplier (CORE-AUDIT row 11). Lifebloom's bloom (33778) is NOT bound
// here - spell_dru_lifebloom_resto's TriggerLifebloomBloom call applies Harmony itself.
class spell_dru_harmony_direct : public SpellScript
{
    PrepareSpellScript(spell_dru_harmony_direct);

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        if (missInfo != SPELL_MISS_NONE)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Cached before any effect (including this cast's own new HoT, e.g. Regrowth's periodic
        // part) has applied, so a spell that both heals directly and applies a HoT doesn't count
        // its own brand-new HoT toward N.
        _harmonyCount = Druid::CountHarmonyHots(caster, target);
    }

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || GetHitHeal() <= 0)
            return;

        float const mult = Druid::GetDirectHealMultiplier(caster, target, GetSpellInfo(), _harmonyCount);
        if (mult != 1.0f)
            SetHitHeal(int32(float(GetHitHeal()) * mult));
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_dru_harmony_direct::HandleBeforeHit);
        OnHit += SpellHitFn(spell_dru_harmony_direct::HandleOnHit);
    }

private:
    uint32 _harmonyCount = 0;
};

// 200560 - Bloom
class spell_dru_bloom : public SpellScript
{
    PrepareSpellScript(spell_dru_bloom);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BLOOM_JUMP });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        if (target->HasAura(Druid::SPELL_REJUVENATION, caster->GetGUID()) ||
            target->HasAura(Druid::SPELL_GERMINATION, caster->GetGUID()))
            return SPELL_CAST_OK;

        return SPELL_FAILED_BAD_TARGETS;
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (caster && target)
            Druid::StartBloomJumps(caster, target);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dru_bloom::CheckCast);
        AfterHit += SpellHitFn(spell_dru_bloom::HandleAfterHit);
    }
};

// 200562 - Cenarion Ward
class spell_dru_cenarion_ward : public AuraScript
{
    PrepareAuraScript(spell_dru_cenarion_ward);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_CENARION_WARD_HEAL });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        // Original caster = the druid, so the released heal counts toward Harmony and scales off
        // the druid's own spell power even if the ward's target isn't the caster.
        target->CastSpell(target, Druid::SPELL_CENARION_WARD_HEAL, TRIGGERED_FULL_MASK, nullptr, aurEff,
                           GetCasterGUID());
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dru_cenarion_ward::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 200564 - Flourish
class spell_dru_flourish : public SpellScript
{
    PrepareSpellScript(spell_dru_flourish);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        std::list<Unit*> nearby;
        Acore::AnyFriendlyUnitInObjectRangeCheck check(caster, caster, 60.0f);
        Acore::UnitListSearcher<Acore::AnyFriendlyUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, 60.0f);

        for (Unit* unit : nearby)
        {
            Druid::ForEachCasterHot(caster, unit, [](Aura* aura)
            {
                Druid::ExtendHot(aura, 8000);
                Druid::AccelerateHotTicks(aura, 8000);
            });
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dru_flourish::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 18562 - Swiftmend
class spell_dru_swiftmend : public SpellScript
{
    PrepareSpellScript(spell_dru_swiftmend);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        ObjectGuid const casterGuid = caster->GetGUID();
        if (target->HasAura(Druid::SPELL_REJUVENATION, casterGuid) ||
            target->HasAura(Druid::SPELL_GERMINATION, casterGuid) ||
            target->HasAura(Druid::SPELL_REGROWTH, casterGuid) ||
            target->HasAura(Druid::SPELL_LIFEBLOOM, casterGuid))
            return SPELL_CAST_OK;

        return SPELL_FAILED_TARGET_AURASTATE;
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        ObjectGuid const casterGuid = caster->GetGUID();
        static constexpr std::array<uint32, 4> extendable =
            { Druid::SPELL_REJUVENATION, Druid::SPELL_GERMINATION, Druid::SPELL_REGROWTH, Druid::SPELL_LIFEBLOOM };

        // Cenarion Ward (200562/200563) is deliberately excluded - not in this list.
        for (uint32 spellId : extendable)
            if (Aura* aura = target->GetAura(spellId, casterGuid))
                Druid::ExtendHot(aura, 6000);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dru_swiftmend::CheckCast);
        AfterHit += SpellHitFn(spell_dru_swiftmend::HandleAfterHit);
    }
};

// 774, 200568 - Rejuvenation / Germination: Proliferation's Germination copy + ally spread (7,1),
// Tree of Life's instant heal on every application (8,1).
class spell_dru_rejuvenation : public SpellScript
{
    PrepareSpellScript(spell_dru_rejuvenation);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_GERMINATION });
    }

    // Proliferation r3 capstone (Germination): a recast of Rejuvenation on a target that already
    // has the caster's Rejuvenation becomes (or refreshes) a Germination copy instead of just
    // refreshing 774 in place.
    void HandleGermination(SpellMissInfo missInfo)
    {
        if (missInfo != SPELL_MISS_NONE)
            return;

        if (GetSpellInfo()->Id != Druid::SPELL_REJUVENATION)
            return;

        Unit* casterUnit = GetCaster();
        Player* caster = casterUnit ? casterUnit->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        if (!caster->HasAura(Druid::SPELL_PROLIFERATION_R3))
            return;

        Aura* existingRejuv = target->GetAura(Druid::SPELL_REJUVENATION, caster->GetGUID());
        if (!existingRejuv)
            return; // a fresh application, not a recast - let it apply normally

        Aura* existingGermination = target->GetAura(Druid::SPELL_GERMINATION, caster->GetGUID());
        if (!existingGermination)
        {
            // Redirected into its own separate cast of 200568, which fires this same script's
            // AfterHit independently (including its own Tree of Life instant heal) - suppress this
            // cast's own ToL trigger below so it doesn't also fire for the untouched pre-existing
            // 774 aura (a double heal). Code-review fix: PreventHitAura() is a no-op in BeforeHit
            // (m_spellAura isn't populated until DoSpellHitOnUnit, well after BeforeHit runs), so
            // 774 was still silently refreshed by the normal hit; PreventHitDefaultEffect(EFFECT_0)
            // suppresses the aura-apply effect directly regardless of hook timing.
            _preventedHit = true;
            PreventHitDefaultEffect(EFFECT_0);
            caster->CastSpell(target, Druid::SPELL_GERMINATION, TRIGGERED_FULL_MASK);
            return;
        }

        // Both already present - refresh whichever has less time remaining, and prevent 774's own
        // reapplication so only one of the two actually gets extended. Not a new application, so no
        // extra Tree of Life heal either (same suppression as above).
        _preventedHit = true;
        PreventHitDefaultEffect(EFFECT_0);
        if (existingGermination->GetDuration() < existingRejuv->GetDuration())
            existingGermination->RefreshDuration();
        else
            existingRejuv->RefreshDuration();
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Tree of Life (8,1): every genuine application of this cast's own spell (774 or 200568)
        // instantly heals for a fraction of its total healing - including Proliferation spreads and
        // Germination itself, since this fires from any successful hit of this script's own spell.
        // Skipped when HandleGermination redirected/merged this hit above (see its comments).
        if (!_preventedHit)
            if (Aura* thisAura = target->GetAura(GetSpellInfo()->Id, caster->GetGUID()))
                Druid::OnRejuvenationApplied(caster, target, thisAura);

        // Proliferation (7,1) ally spread: only a real, non-triggered cast of Rejuvenation itself.
        if (GetSpellInfo()->Id != Druid::SPELL_REJUVENATION || GetSpell()->IsTriggered())
            return;

        Player* player = caster->ToPlayer();
        if (!player || !player->HasAura(Druid::SPELL_PROLIFERATION_BUFF))
            return;

        player->RemoveAurasDueToSpell(Druid::SPELL_PROLIFERATION_BUFF);

        std::list<Unit*> nearby;
        Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck check(target, caster, 30.0f, true);
        Acore::UnitListSearcher<Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, 30.0f);

        nearby.remove_if([caster](Unit* unit)
        {
            return unit->HasAura(Druid::SPELL_REJUVENATION, caster->GetGUID()) ||
                   unit->HasAura(Druid::SPELL_GERMINATION, caster->GetGUID());
        });

        if (nearby.empty())
            return;

        nearby.sort(Acore::HealthPctOrderPred());

        uint32 taken = 0;
        for (Unit* unit : nearby)
        {
            if (taken >= 2)
                break;

            caster->CastSpell(unit, Druid::SPELL_REJUVENATION, TRIGGERED_FULL_MASK);
            ++taken;
        }
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_dru_rejuvenation::HandleGermination);
        AfterHit += SpellHitFn(spell_dru_rejuvenation::HandleAfterHit);
    }

private:
    bool _preventedHit = false;
};

// 774, 200568 (aura half of the pair) - Perennial (1,3): a Rejuvenation tick on a full-health target
// extends the aura, up to a per-instance cap. Nature's Mending r3 capstone (1,0): a tick on a target
// below 50% health applies Cultivation.
class spell_dru_rejuvenation_aura : public AuraScript
{
    PrepareAuraScript(spell_dru_rejuvenation_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_CULTIVATION });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // A recast resets the per-cast cap (RESTO §8 (1,3): "independent... per cast").
        _perennialUsedMs = 0;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        Player* player = caster->ToPlayer();
        if (!player)
            return;

        // Nature's Mending r3 capstone (1,0): Cultivation - runs before the tick heals, like
        // Perennial below, so "below 50%" reads the target's health before this tick lands.
        if (player->HasAura(Druid::SPELL_NATURES_MENDING_R3) && target->HealthBelowPct(50))
            caster->CastSpell(target, Druid::SPELL_CULTIVATION, TRIGGERED_FULL_MASK);

        int32 const cap = Druid::GetRankAmount(player,
            { Druid::SPELL_PERENNIAL_R3, Druid::SPELL_PERENNIAL_R2, Druid::SPELL_PERENNIAL_R1 }, EFFECT_0);
        if (!cap || _perennialUsedMs >= cap)
            return;

        // "At full health" is checked before the tick heals - this handler runs before the periodic
        // heal is applied.
        if (!target->IsFullHealth())
            return;

        int32 const extension = std::min<int32>(2000, cap - _perennialUsedMs);
        Druid::ExtendHot(GetAura(), extension);
        _perennialUsedMs += extension;
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dru_rejuvenation_aura::HandleApply, EFFECT_0,
                                               SPELL_AURA_PERIODIC_HEAL, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_rejuvenation_aura::HandlePeriodic, EFFECT_0,
                                                  SPELL_AURA_PERIODIC_HEAL);
    }

private:
    int32 _perennialUsedMs = 0;
};

// 8936 - Regrowth: undoes Nature's Bounty/Tree of Life's direct-only crit bonus bleeding into the
// periodic tick's snapshotted crit chance (CORE-AUDIT row 13), and adds Empowered Rejuvenation's
// coefficient bump to the HoT (row 14, excluded from the general BONUS_MULTIPLIER classmask so it
// doesn't also scale the direct heal).
class spell_dru_regrowth : public AuraScript
{
    PrepareAuraScript(spell_dru_regrowth);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_TREE_OF_LIFE_PASSIVE });
    }

    void CalculateTickAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetUnitOwner();
        if (!caster || !target)
            return;

        Player* player = caster->ToPlayer();
        if (!player)
            return;

        int32 const rank = Druid::GetRankAmount(player,
            { Druid::SPELL_EMPOWERED_REJUVENATION_R3, Druid::SPELL_EMPOWERED_REJUVENATION_R2,
              Druid::SPELL_EMPOWERED_REJUVENATION_R1 }, EFFECT_0);
        if (rank)
        {
            uint32 const bonus = caster->SpellHealingBonusDone(target, GetSpellInfo(), 0, DOT, EFFECT_1,
                                                                aurEff->GetPctMods(), 1);
            amount += CalculatePct(int32(bonus), rank);
        }

        int32 bleed = Druid::GetRankAmount(player,
            { Druid::SPELL_NATURES_BOUNTY_R3, Druid::SPELL_NATURES_BOUNTY_R2, Druid::SPELL_NATURES_BOUNTY_R1 },
            EFFECT_0);

        // Tree of Life is a SPELL_AURA_TRANSFORM buff, not a real shapeshift (CORE-AUDIT row 38) -
        // GetShapeshiftForm() never returns FORM_TREE, so gate on 5420 itself being applied (code-
        // review fix: a stale GetShapeshiftForm() == FORM_TREE check here was permanently dead, so
        // Regrowth's periodic tick kept 5420's +25% crit rider instead of having it bled back out).
        if (AuraEffect const* tol = player->GetAuraEffect(Druid::SPELL_TREE_OF_LIFE_PASSIVE, EFFECT_2))
            bleed += tol->GetAmount();

        if (bleed)
        {
            // `aurEff` IS effect index 1 here (we registered for EFFECT_1 below), so it is always
            // valid even on the very first calculation (Aura::_InitEffects only stores the pointer
            // into the effect array *after* this constructor call returns) - the warlock precedent
            // for this exact const_cast pattern is spell_warlock.cpp.
            const_cast<AuraEffect*>(aurEff)->SetCritChance(std::max(0.0f, aurEff->GetCritChance() - float(bleed)));
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_regrowth::CalculateTickAmount, EFFECT_1,
                                                      SPELL_AURA_PERIODIC_HEAL);
    }
};

// -33763 - Lifebloom - replaces stock spell_dru_lifebloom (see header comment): no mana return, the
// bloom is routed through the shared Druid::TriggerLifebloomBloom (also used by Photosynthesis).
class spell_dru_lifebloom_resto : public AuraScript
{
    PrepareAuraScript(spell_dru_lifebloom_resto);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_LIFEBLOOM_BLOOM });
    }

    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // Final heal only on duration end - a dispel is handled separately below.
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        Druid::TriggerLifebloomBloom(GetCaster(), GetTarget(), GetAura(), false);
    }

    void HandleDispel(DispelInfo* dispelInfo)
    {
        Unit* target = GetUnitOwner();
        if (!target || !GetEffect(EFFECT_1))
            return;

        Unit* caster = GetCaster();
        int32 healAmount = GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster ? caster : target, nullptr, target) *
                            dispelInfo->GetRemovedCharges();
        SpellInfo const* finalHeal = sSpellMgr->GetSpellInfo(Druid::SPELL_LIFEBLOOM_BLOOM);

        if (caster && finalHeal)
        {
            healAmount = int32(caster->SpellHealingBonusDone(target, finalHeal, healAmount, HEAL, EFFECT_1, 0.0f,
                                                               dispelInfo->GetRemovedCharges()));
            healAmount = int32(target->SpellHealingBonusTaken(caster, finalHeal, healAmount, HEAL,
                                                                dispelInfo->GetRemovedCharges()));
        }

        target->CastCustomSpell(target, Druid::SPELL_LIFEBLOOM_BLOOM, &healAmount, nullptr, nullptr, true, nullptr,
                                 nullptr, GetCasterGUID());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_lifebloom_resto::AfterRemove, EFFECT_1, SPELL_AURA_DUMMY,
                                                 AURA_EFFECT_HANDLE_REAL);
        AfterDispel += AuraDispelFn(spell_dru_lifebloom_resto::HandleDispel);
    }
};

// 33763 - Lifebloom: one-target limit, two with Gift of the Earthmother's r3 capstone (9,2).
class spell_dru_lifebloom_target_limit : public SpellScript
{
    PrepareSpellScript(spell_dru_lifebloom_target_limit);

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        Druid::OnLifebloomApplied(caster, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_lifebloom_target_limit::HandleAfterHit);
    }
};

// -48496 - Living Seed - replaces stock spell_dru_living_seed: adds DoCheckProc restricting the
// trigger to a direct Nature healing spell (RESTO §8 (7,2)); the proc handler itself is unchanged.
class spell_dru_living_seed_resto : public AuraScript
{
    PrepareAuraScript(spell_dru_living_seed_resto);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DRUID_LIVING_SEED_PROC });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return Heal::IsDirectNatureHeal(eventInfo.GetSpellInfo());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        if (!eventInfo.GetHealInfo() || !eventInfo.GetProcTarget())
            return;

        int32 amount = CalculatePct(eventInfo.GetHealInfo()->GetHeal(), aurEff->GetAmount());
        GetTarget()->CastCustomSpell(SPELL_DRUID_LIVING_SEED_PROC, SPELLVALUE_BASE_POINT0, amount,
                                      eventInfo.GetProcTarget(), true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_living_seed_resto::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dru_living_seed_resto::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 16864, 200600, 200601 - Omen of Clarity - replaces stock spell_dru_omen_of_clarity: narrows
// CheckProc to the three RESTO §8 (2,1) cases; keeps the T10 Balance 4-piece handling verbatim.
class spell_dru_omen_of_clarity_resto : public AuraScript
{
    PrepareAuraScript(spell_dru_omen_of_clarity_resto);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DRUID_BALANCE_T10_BONUS, SPELL_DRUID_BALANCE_T10_BONUS_PROC });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        bool const isPeriodic =
            (eventInfo.GetTypeMask() & (PROC_FLAG_DONE_PERIODIC | PROC_FLAG_TAKEN_PERIODIC)) != 0;

        // (a) Lifebloom's periodic heal tick is the sole periodic exception (also covers Tranquility
        // ticks being rejected, since 44203 is neither Lifebloom nor a periodic aura tick at all).
        if (isPeriodic)
            return spellInfo->Id == Druid::SPELL_LIFEBLOOM && eventInfo.GetHealInfo() != nullptr;

        // (b) direct Nature healing spells.
        if (eventInfo.GetHealInfo())
            return Heal::IsDirectNatureHeal(spellInfo);

        // (c) direct damage, including auto attacks.
        if (DamageInfo const* damageInfo = eventInfo.GetDamageInfo())
            return damageInfo->GetDamage() > 0;

        return false;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        Unit* target = GetTarget();
        if (target->HasAura(SPELL_DRUID_BALANCE_T10_BONUS))
            target->CastSpell(nullptr, SPELL_DRUID_BALANCE_T10_BONUS_PROC, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_omen_of_clarity_resto::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dru_omen_of_clarity_resto::HandleProc, EFFECT_0,
                                          SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// -48539 - Revitalize - replaces stock spell_dru_revitalize (RESTO §8 (8,0)): fixes the missing Proc
// Chance multiplier, adds the caster's own 1% base mana return, and rolls the tick/cast-percentage
// pair off the right effect for the right spell.
class spell_dru_revitalize_resto : public AuraScript
{
    PrepareAuraScript(spell_dru_revitalize_resto);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            SPELL_DRUID_REVITALIZE_ENERGIZE_MANA, SPELL_DRUID_REVITALIZE_ENERGIZE_RAGE,
            SPELL_DRUID_REVITALIZE_ENERGIZE_ENERGY, SPELL_DRUID_REVITALIZE_ENERGIZE_RP,
            Druid::SPELL_REVITALIZE_MANA
        });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return;

        bool const isPeriodic = (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) != 0;
        uint32 const id = spellInfo->Id;
        int32 chance;

        if (isPeriodic)
        {
            // Rejuvenation, Germination, Wild Growth ticks - Regrowth's own tick is rejected.
            if (id != Druid::SPELL_REJUVENATION && id != Druid::SPELL_GERMINATION && id != Druid::SPELL_WILD_GROWTH)
                return;

            chance = aurEff->GetAmount();
        }
        else
        {
            // Healing Touch and Regrowth's direct heal only - Nature's Bounty's spread never fires
            // this (AddAura has no HIT event).
            if (id != Druid::SPELL_HEALING_TOUCH && id != Druid::SPELL_REGROWTH)
                return;

            AuraEffect const* castEffect = GetEffect(EFFECT_1);
            if (!castEffect)
                return;

            chance = castEffect->GetAmount();
        }

        Player* caster = GetTarget()->ToPlayer();
        if (!caster)
            return;

        float const chanceMult = 1.0f + caster->GetProcChancePercentage() / 100.0f;
        if (!roll_chance_f(std::min(100.0f, float(chance) * chanceMult)))
            return;

        Unit* target = eventInfo.GetActionTarget();
        if (!target)
            return;

        uint32 energizeSpell;
        switch (target->getPowerType())
        {
            case POWER_MANA:
                energizeSpell = SPELL_DRUID_REVITALIZE_ENERGIZE_MANA;
                break;
            case POWER_RAGE:
                energizeSpell = SPELL_DRUID_REVITALIZE_ENERGIZE_RAGE;
                break;
            case POWER_ENERGY:
                energizeSpell = SPELL_DRUID_REVITALIZE_ENERGIZE_ENERGY;
                break;
            case POWER_RUNIC_POWER:
                energizeSpell = SPELL_DRUID_REVITALIZE_ENERGIZE_RP;
                break;
            default:
                return;
        }

        eventInfo.GetActor()->CastSpell(target, energizeSpell, true, nullptr, aurEff);

        // "Each time Revitalize triggers, you also restore 1% of your base mana."
        int32 const casterReturn = int32(CalculatePct(caster->GetCreateMana(), 1));
        caster->CastCustomSpell(Druid::SPELL_REVITALIZE_MANA, SPELLVALUE_BASE_POINT0, casterReturn, caster, true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dru_revitalize_resto::HandleProc, EFFECT_0,
                                          SPELL_AURA_OVERRIDE_CLASS_SCRIPTS);
    }
};

// 5185 - Healing Touch - Revitalize r3 capstone: healing a target to full restores 30% of the
// spell's mana cost.
class spell_dru_revitalize_capstone : public SpellScript
{
    PrepareSpellScript(spell_dru_revitalize_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_REVITALIZE_MANA });
    }

    void HandleHit()
    {
        Unit* target = GetHitUnit();
        _wasFull = target && target->IsFullHealth();
    }

    void HandleAfterHit()
    {
        if (_wasFull)
            return;

        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target || !target->IsFullHealth())
            return;

        if (!caster->HasAura(Druid::SPELL_REVITALIZE_R3))
            return;

        // IsFullHealth() rather than GetHitHeal() - GetHitHeal() in AfterHit is post-overheal
        // (docs/bugs-and-fixes.md).
        int32 const amount = int32(CalculatePct(GetSpell()->GetPowerCost(), 30));
        caster->CastCustomSpell(Druid::SPELL_REVITALIZE_MANA, SPELLVALUE_BASE_POINT0, amount, caster, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_dru_revitalize_capstone::HandleHit);
        AfterHit += SpellHitFn(spell_dru_revitalize_capstone::HandleAfterHit);
    }

private:
    bool _wasFull = false;
};

// -48438 - Wild Growth - replaces stock spell_dru_wild_growth: Tree of Life (8,1) heals one
// additional target.
class spell_dru_wild_growth_resto : public SpellScript
{
    PrepareSpellScript(spell_dru_wild_growth_resto);

    bool Validate(SpellInfo const* spellInfo) override
    {
        if (spellInfo->Effects[EFFECT_2].IsEffect() || spellInfo->Effects[EFFECT_2].CalcValue() <= 0)
            return false;
        return true;
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if(Acore::RaidCheck(GetCaster(), false));

        uint32 maxTargets = GetCaster()->HasAura(SPELL_DRUID_GLYPH_OF_WILD_GROWTH) ? 6 : 5;

        // Tree of Life is a SPELL_AURA_TRANSFORM buff, not a real shapeshift (CORE-AUDIT row 38) -
        // GetShapeshiftForm() never returns FORM_TREE, so gate on the buff aura directly (code-
        // review fix: a stale GetShapeshiftForm() == FORM_TREE check here was permanently dead, so
        // Wild Growth never healed the extra target while in Tree of Life).
        if (Player* player = GetCaster()->ToPlayer())
            if (player->HasAura(Druid::SPELL_TREE_OF_LIFE_FORM))
                ++maxTargets;

        if (targets.size() > maxTargets)
        {
            targets.sort(Acore::HealthPctOrderPred());
            targets.resize(maxTargets);
        }

        _targets = targets;
    }

    void SetTargets(std::list<WorldObject*>& targets)
    {
        targets = _targets;
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dru_wild_growth_resto::FilterTargets,
                                                                    EFFECT_0, TARGET_UNIT_DEST_AREA_ALLY);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dru_wild_growth_resto::SetTargets,
                                                                    EFFECT_1, TARGET_UNIT_DEST_AREA_ALLY);
    }

private:
    std::list<WorldObject*> _targets;
};

// -48438 (aura half of the pair) - Wild Growth: Unstoppable Growth (9,0) falloff reduction, on top
// of the stock T10 2-piece reduction; falloff step scales with the aura's actual tick count (RESTO
// §13 Q18) and is floored at -100%.
class spell_dru_wild_growth_aura_resto : public AuraScript
{
    PrepareAuraScript(spell_dru_wild_growth_aura_resto);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DRUID_RESTORATION_T10_2P_BONUS });
    }

    void SetTickHeal(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        _baseTick = amount;

        // Rescale the stock step (2 points of the base tick at 7 ticks) by the aura's actual total
        // tick count, so the same +6%/-6% spread always spans the whole duration. This does not
        // account for Flourish's injected extra ticks (CORE-AUDIT row 21 deliberately keeps those
        // out of GetTotalTicks() to avoid a core edit) - a known, documented simplification.
        int32 const totalTicks = std::max(1, aurEff->GetTotalTicks());
        _baseReduction = 2.0f * 7.0f / float(totalTicks);

        Unit* caster = GetCaster();
        if (!caster)
            return;

        if (AuraEffect const* bonus = caster->GetAuraEffect(SPELL_DRUID_RESTORATION_T10_2P_BONUS, EFFECT_0))
            AddPct(_baseReduction, -bonus->GetAmount());

        if (Player* player = caster->ToPlayer())
            if (int32 rank = Druid::GetRankAmount(player,
                    { Druid::SPELL_UNSTOPPABLE_GROWTH_R2, Druid::SPELL_UNSTOPPABLE_GROWTH_R1 }, EFFECT_0))
                AddPct(_baseReduction, -rank);
    }

    void HandleTickUpdate(AuraEffect* aurEff)
    {
        float reduction = _baseReduction;
        reduction *= float(aurEff->GetTickNumber() - 1);

        float const bonus = std::max(-100.0f, 6.0f - reduction);
        int32 const amount = int32(_baseTick + CalculatePct(_baseTick, bonus));
        aurEff->SetAmount(amount);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_wild_growth_aura_resto::SetTickHeal, EFFECT_0,
                                                      SPELL_AURA_PERIODIC_HEAL);
        OnEffectUpdatePeriodic += AuraEffectUpdatePeriodicFn(spell_dru_wild_growth_aura_resto::HandleTickUpdate,
                                                              EFFECT_0, SPELL_AURA_PERIODIC_HEAL);
    }

private:
    float _baseTick = 0.0f;
    float _baseReduction = 2.0f;
};

// 5185, 8936 - Healing Touch / Regrowth - Photosynthesis r3 capstone (8,2): a 20% chance to force
// Lifebloom to bloom without ending it.
class spell_dru_photosynthesis_capstone : public SpellScript
{
    PrepareSpellScript(spell_dru_photosynthesis_capstone);

    void HandleAfterHit()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        AuraEffect const* capstone = caster->GetAuraEffect(Druid::SPELL_PHOTOSYNTHESIS_R3, EFFECT_1);
        if (!capstone)
            return;

        Aura* lifebloom = target->GetAura(Druid::SPELL_LIFEBLOOM, caster->GetGUID());
        if (!lifebloom)
            return;

        float const chance = float(capstone->GetAmount()) * (1.0f + caster->GetProcChancePercentage() / 100.0f);
        if (!roll_chance_f(std::min(100.0f, chance)))
            return;

        Druid::TriggerLifebloomBloom(caster, target, lifebloom, true);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_photosynthesis_capstone::HandleAfterHit);
    }
};

// 5185, 200564 - Healing Touch / Flourish - Empowered Touch r2 capstone (5,0): reduces Natural
// Alacrity's and Tranquility's remaining cooldowns by 2 sec per cast, after Cooldown Haste.
class spell_dru_empowered_touch_capstone : public SpellScript
{
    PrepareSpellScript(spell_dru_empowered_touch_capstone);

    void HandleAfterCast()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster || GetSpell()->IsTriggered())
            return;

        if (!caster->HasAura(Druid::SPELL_EMPOWERED_TOUCH_R2))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_NATURAL_ALACRITY, 2000);
        Druid::ReduceSpellCooldown(caster, Druid::SPELL_TRANQUILITY, 2000);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_empowered_touch_capstone::HandleAfterCast);
    }
};

// 17076 - Nature's Bounty r3 - capstone: a critical Regrowth direct heal spreads Regrowth's HoT to
// one additional target.
class spell_dru_natures_bounty_capstone : public AuraScript
{
    PrepareAuraScript(spell_dru_natures_bounty_capstone);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* procTarget = eventInfo.GetProcTarget();
        if (!caster || !procTarget)
            return;

        std::list<Unit*> nearby;
        Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck check(procTarget, caster, 30.0f, true);
        Acore::UnitListSearcher<Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck> searcher(procTarget, nearby, check);
        Cell::VisitObjects(procTarget, searcher, 30.0f);

        nearby.remove_if([caster](Unit* unit)
        {
            return unit->HasAura(Druid::SPELL_REGROWTH, caster->GetGUID());
        });

        if (nearby.empty())
            return;

        nearby.sort(Acore::HealthPctOrderPred());

        // Aura effects only - no direct heal, no cast, no procs (Photosynthesis/Revitalize/Living
        // Seed/Omen don't trigger), and caster SpellMods (Deep Roots, Nature's Mending, Empowered
        // Rejuvenation) still apply through AddAura's own coefficient path.
        caster->AddAura(Druid::SPELL_REGROWTH, nearby.front());
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_dru_natures_bounty_capstone::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 33883 - Natural Perfection r3 - capstone: a critical heal from a direct Nature healing spell
// reduces Cenarion Ward's remaining cooldown by 2 sec, after Cooldown Haste.
class spell_dru_natural_perfection_capstone : public AuraScript
{
    PrepareAuraScript(spell_dru_natural_perfection_capstone);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return Heal::IsDirectNatureHeal(eventInfo.GetSpellInfo());
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Druid::ReduceSpellCooldown(player, Druid::SPELL_CENARION_WARD, 2000);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_natural_perfection_capstone::CheckProc);
        OnProc += AuraProcFn(spell_dru_natural_perfection_capstone::HandleProc);
    }
};

// 200586, 200587, 200588 - Ysera's Gift: every 5 sec, heals the druid (or the lowest-HP% nearby
// ally if the druid is at full health) for a percent of the druid's max health.
class spell_dru_yseras_gift : public AuraScript
{
    PrepareAuraScript(spell_dru_yseras_gift);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_YSERAS_GIFT_HEAL });
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Player* druid = GetTarget()->ToPlayer();
        if (!druid || !druid->IsAlive())
            return;

        int32 const amount = CalculatePct(int32(druid->GetMaxHealth()), aurEff->GetAmount());
        if (amount <= 0)
            return;

        Unit* target = nullptr;
        if (!druid->IsFullHealth())
        {
            target = druid;
        }
        else
        {
            std::list<Unit*> nearby;
            Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck check(druid, druid, 40.0f, true);
            Acore::UnitListSearcher<Acore::AnyFriendlyNotSelfUnitInObjectRangeCheck> searcher(druid, nearby, check);
            Cell::VisitObjects(druid, searcher, 40.0f);

            nearby.remove_if([druid](Unit* unit)
            {
                return unit->IsFullHealth() || !druid->IsWithinLOSInMap(unit);
            });

            if (!nearby.empty())
            {
                nearby.sort(Acore::HealthPctOrderPred());
                target = nearby.front();
            }
        }

        if (!target)
            return;

        druid->CastCustomSpell(target, Druid::SPELL_YSERAS_GIFT_HEAL, &amount, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_yseras_gift::HandlePeriodic, EFFECT_0,
                                                  SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 34153 - Living Spirit r3 - capstone: Spirit scales with the number of active Rejuvenations.
class spell_dru_living_spirit_capstone : public AuraScript
{
    PrepareAuraScript(spell_dru_living_spirit_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_LIVING_SPIRIT_STAT });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        uint32 const n = std::min<uint32>(10, Druid::CountActiveRejuvenations(player));
        if (!n)
        {
            player->RemoveAurasDueToSpell(Druid::SPELL_LIVING_SPIRIT_STAT);
            return;
        }

        if (Aura* aura = player->GetAura(Druid::SPELL_LIVING_SPIRIT_STAT))
        {
            // Code-review fix: SetStackAmount unconditionally re-applies aura-specific mods and
            // forces a client update, so only call it when the stack count actually changed.
            if (aura->GetStackAmount() != n)
                aura->SetStackAmount(uint8(n));
        }
        else if (Aura* newAura = player->AddAura(Druid::SPELL_LIVING_SPIRIT_STAT, player))
            newAura->SetStackAmount(uint8(n));
    }

    // Code-review fix: 200571 was never cleaned up when 34153 itself is removed (respec, death,
    // etc.) - the periodic that maintains its stack count stops with 34153, leaving the Spirit
    // buff stuck at whatever stack count it last had.
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            player->RemoveAurasDueToSpell(Druid::SPELL_LIVING_SPIRIT_STAT);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_living_spirit_capstone::HandlePeriodic, EFFECT_1,
                                                  SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_living_spirit_capstone::HandleRemove, EFFECT_1,
                                                 SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 740 - Tranquility - Nature's Focus r2 capstone: while channeling, 50% less damage taken and no
// knockback.
class spell_dru_natures_focus_capstone : public AuraScript
{
    PrepareAuraScript(spell_dru_natures_focus_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_TRANQUIL_FOCUS });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* caster = GetTarget()->ToPlayer();
        if (caster && caster->HasAura(Druid::SPELL_NATURES_FOCUS_R2))
            caster->CastSpell(caster, Druid::SPELL_TRANQUIL_FOCUS, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(Druid::SPELL_TRANQUIL_FOCUS);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dru_natures_focus_capstone::HandleApply, EFFECT_1,
                                               SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_natures_focus_capstone::HandleRemove, EFFECT_1,
                                                 SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }
};

// 16833, 16834, 16835 - Natural Shapeshifter - re-evaluates form bonuses on learn/login/unlearn (the
// druid_hooks.cpp UnitScript covers the "already know it, then shapeshift" direction).
class spell_dru_natural_shapeshifter : public AuraScript
{
    PrepareAuraScript(spell_dru_natural_shapeshifter);

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Druid::ApplyShapeshiftFormBonuses(player, player->GetShapeshiftForm());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetTarget()->ToPlayer())
            Druid::ApplyShapeshiftFormBonuses(player, player->GetShapeshiftForm());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_dru_natural_shapeshifter::HandleApply, EFFECT_0,
                                               SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_natural_shapeshifter::HandleRemove, EFFECT_0,
                                                 SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_druid_resto_spell_scripts()
{
    RegisterSpellScript(spell_dru_harmony_direct);
    RegisterSpellScript(spell_dru_bloom);
    RegisterSpellScript(spell_dru_cenarion_ward);
    RegisterSpellScript(spell_dru_flourish);
    RegisterSpellScript(spell_dru_swiftmend);
    RegisterSpellAndAuraScriptPair(spell_dru_rejuvenation, spell_dru_rejuvenation_aura);
    RegisterSpellScript(spell_dru_regrowth);
    RegisterSpellScript(spell_dru_lifebloom_resto);
    RegisterSpellScript(spell_dru_lifebloom_target_limit);
    RegisterSpellScript(spell_dru_living_seed_resto);
    RegisterSpellScript(spell_dru_omen_of_clarity_resto);
    RegisterSpellScript(spell_dru_revitalize_resto);
    RegisterSpellScript(spell_dru_revitalize_capstone);
    RegisterSpellAndAuraScriptPair(spell_dru_wild_growth_resto, spell_dru_wild_growth_aura_resto);
    RegisterSpellScript(spell_dru_photosynthesis_capstone);
    RegisterSpellScript(spell_dru_empowered_touch_capstone);
    RegisterSpellScript(spell_dru_natures_bounty_capstone);
    RegisterSpellScript(spell_dru_natural_perfection_capstone);
    RegisterSpellScript(spell_dru_yseras_gift);
    RegisterSpellScript(spell_dru_living_spirit_capstone);
    RegisterSpellScript(spell_dru_natures_focus_capstone);
    RegisterSpellScript(spell_dru_natural_shapeshifter);
}
