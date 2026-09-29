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
 * Warlock rework - Affliction pass (S1) spell/aura scripts
 * (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5, warlock-rework.AFFLICTION.md §6.1/§7).
 * Replacement classes for stock spell_warlock.cpp bindings the Affliction tree displaces - stock
 * spell_warlock.cpp stays unedited and every class it replaces is left unbound (unbind_script,
 * WP-A's job) rather than rewritten in place (.agents/docs/upstream-merge.md).
 *
 * One class (or SpellScript/AuraScript pair) per row in AFFLICTION.md §6.1's binding table; each
 * class's header comment cites the exact §7 subsection it implements. Script names below must
 * match WP-A's `scripted_by`/`unbind_script` calls byte for byte (case-sensitive) - see the
 * AFFLICTION-WP-BRIEF.md checklist.
 */

#include "WarlockMechanics.h"
#include "Cell.h"
#include "CellImpl.h"
#include "DBCStores.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <list>
#include <vector>

namespace
{
    // Stock ids/icons this file needs that are private to spell_warlock.cpp's own enum (kept as
    // plain warlock spells/icons by this pass, not owned by any Affliction talent) - duplicated
    // here rather than reaching into that file, which stays read-only (upstream-merge.md).
    constexpr uint32 SPELL_LIFE_TAP_ENERGIZE = 31818;
    constexpr uint32 SPELL_LIFE_TAP_ENERGIZE_2 = 32553;
    constexpr uint32 ICON_MANA_FEED = 1982;
    constexpr uint32 SPELL_GLYPH_OF_SIPHON_LIFE = 56216;
    constexpr uint32 FELHUNTER_ENTRY = 417;
    constexpr uint32 SPELL_IMMOLATE = 348;
    constexpr uint32 SPELL_SHADOW_WORD_PAIN = 589;
    constexpr uint32 SPELL_DEVOURING_PLAGUE = 2944;

    // Live amount of the highest-known rank of a talent, read from a given effect index (PLAN §2
    // "live talent reads by rank spell id" idiom - Priest's GetKnownRankEffect precedent,
    // PriestMechanics.cpp:178-191). Returns 0 (untalented) if none of the ranks are known.
    int32 GetKnownRankAmount(Unit const* unit, std::initializer_list<uint32> ranksHighestFirst,
                              uint8 effIndex = EFFECT_0)
    {
        if (!unit)
            return 0;
        for (uint32 rankId : ranksHighestFirst)
            if (AuraEffect const* eff = unit->GetAuraEffect(rankId, effIndex))
                return eff->GetAmount();
        return 0;
    }
}

// ===========================================================================================
// 172 - Corruption - AFFLICTION.md §7.1 (Contagion tick counter, Creeping Agony spread capstone)
// ===========================================================================================
class spell_warl_corruption_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_corruption_affliction);

    int32 _base = 0;
    uint32 _ticks = 0;

    void HandleApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        // REAL_OR_REAPPLY: a recast re-snapshots via ModStackAmount -> ChangeAmount, so the base
        // used for the empowered-tick math always matches the current roll (curse_of_agony
        // precedent, spell_warlock.cpp).
        _base = aurEff->GetAmount();
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        ++_ticks;

        Unit* caster = GetCaster();
        int32 const rankAmount = GetKnownRankAmount(caster,
            { Warlock::SPELL_CONTAGION_R3, Warlock::SPELL_CONTAGION_R2, Warlock::SPELL_CONTAGION_R1 });
        bool const empowered = rankAmount != 0 && (_ticks % 6 == 0);

        if (empowered)
        {
            int32 const boosted = int32(float(_base) * (1.0f + float(rankAmount) / 100.0f));
            const_cast<AuraEffect*>(aurEff)->SetAmount(boosted);

            // §12 mitigation: restore the resting amount one update after the empowered tick, so
            // a save/logout inside the ~2 s window before the next natural tick can't persist the
            // boosted amount as `_base` on the next login.
            Unit* target = GetTarget();
            int32 const base = _base;
            ObjectGuid const casterGuid = aurEff->GetCasterGUID();
            target->m_Events.AddEventAtOffset([target, casterGuid, base]()
            {
                if (Aura* current = target->GetAura(Warlock::SPELL_CORRUPTION, casterGuid))
                    if (AuraEffect* eff = current->GetEffect(EFFECT_0))
                        eff->SetAmount(base);
            }, Milliseconds(1));
        }
        else
            const_cast<AuraEffect*>(aurEff)->SetAmount(_base);

        if (!empowered || !caster)
            return;

        // Capstone (r3 30062): while the caster is draining this target's soul, spread a fresh
        // Corruption to nearby in-combat enemies (QA #4/#43a/#43b - a fresh apply, no inherited
        // snapshot, its own counter starts at 0).
        Unit* target = GetTarget();
        if (!caster->HasAura(Warlock::SPELL_CONTAGION_R3) ||
            !target->HasAura(Warlock::SPELL_DRAIN_SOUL, caster->GetGUID()))
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, caster, 10.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, 10.0f);

        for (Unit* unit : nearby)
        {
            if (unit == target || !unit->IsAlive() || !caster->IsValidAttackTarget(unit) ||
                !unit->IsInCombatWith(caster))
                continue;

            // §11 Q21: skip a unit that already carries the caster's Corruption - AddAura on an
            // existing same-caster aura re-snapshots it (SpellAuras.cpp ModStackAmount path).
            if (unit->HasAura(Warlock::SPELL_CORRUPTION, caster->GetGUID()))
                continue;

            caster->AddAura(Warlock::SPELL_CORRUPTION, unit);
        }
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_warl_corruption_affliction::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_corruption_affliction::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// ===========================================================================================
// 980 - Bane of Agony (renamed Curse of Agony) - AFFLICTION.md §7.2
// ===========================================================================================
class spell_warl_bane_of_agony : public SpellScript
{
    PrepareSpellScript(spell_warl_bane_of_agony);

    void HandleAfterHit()
    {
        // Creeping Agony capstone (r3): non-triggered casts only (§7.2's "spreads only if that
        // unit is being drained" clause distinguishes real casts from the copy's own spread, which
        // never re-triggers since AddAura is not a cast).
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !caster->HasAura(Warlock::SPELL_CREEPING_AGONY_R3))
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, caster, 10.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, 10.0f);

        nearby.remove_if([caster, target](Unit* unit)
        {
            return unit == target || !unit->IsAlive() || !caster->IsValidAttackTarget(unit) ||
                   !unit->IsInCombatWith(caster) || unit->HasAura(Warlock::SPELL_BANE_OF_AGONY, caster->GetGUID());
        });

        if (nearby.empty())
            return;

        nearby.sort(Acore::ObjectDistanceOrderPred(target));
        caster->AddAura(Warlock::SPELL_BANE_OF_AGONY, nearby.front());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_bane_of_agony::HandleAfterHit);
    }
};

class spell_warl_bane_of_agony_aura : public AuraScript
{
    PrepareAuraScript(spell_warl_bane_of_agony_aura);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->HasAura(Warlock::SPELL_IMPROVED_BANE_OF_AGONY_R2))
            return;

        if (Player* player = caster->ToPlayer())
            AddPct(amount, player->GetMasteryPercentage());
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Unit* caster = GetCaster())
            Warlock::AddAgonyStacks(caster, GetTarget(), 1);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (caster && target)
            target->RemoveAura(Warlock::SPELL_BANE_OF_AGONY_STACKS, caster->GetGUID());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_bane_of_agony_aura::CalculateAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_bane_of_agony_aura::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_bane_of_agony_aura::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 30108 - Unstable Affliction - AFFLICTION.md §7.18 (Compounding Darkness, Pandemic capstone,
// Fatal Echoes)
// ===========================================================================================
class spell_warl_unstable_affliction_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_unstable_affliction_affliction);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        int32 const rankAmount = GetKnownRankAmount(caster,
            { Warlock::SPELL_COMPOUNDING_DARKNESS_R3, Warlock::SPELL_COMPOUNDING_DARKNESS_R2,
              Warlock::SPELL_COMPOUNDING_DARKNESS_R1 });
        if (rankAmount)
        {
            uint8 const n = Warlock::CountAfflictionDots(target, caster->GetGUID(), Warlock::SPELL_UNSTABLE_AFFLICTION);
            amount = int32(float(amount) * (1.0f + float(rankAmount) / 100.0f * float(n)));
        }

        if (caster->HasAura(Warlock::SPELL_PANDEMIC_R2))
            if (Player* player = caster->ToPlayer())
                AddPct(amount, player->GetMasteryPercentage());
    }

    void HandleExpire(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target || !caster->HasAura(Warlock::SPELL_FATAL_ECHOES_R3))
            return;

        Player* player = caster->ToPlayer();
        float const procMult = player ? (1.0f + player->GetProcChancePercentage() / 100.0f) : 1.0f;
        if (!roll_chance_f(15.0f * procMult))
            return;

        // The dying aura is still in the owner's map inside this handler - capture its snapshot
        // now, re-apply one update later (the haste/tick-interval part cannot be restored, no
        // amplitude setter - CORE-AUDIT C2, accepted).
        int32 const amount = aurEff->GetAmount();
        float const crit = aurEff->GetCritChance();
        float const pctMods = aurEff->GetPctMods();
        ObjectGuid const casterGuid = caster->GetGUID();

        target->m_Events.AddEventAtOffset([target, casterGuid, amount, crit, pctMods]()
        {
            Unit* caster2 = ObjectAccessor::GetUnit(*target, casterGuid);
            if (!caster2)
                return;

            Aura* aura = caster2->AddAura(Warlock::SPELL_UNSTABLE_AFFLICTION, target);
            if (!aura)
                return;

            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            {
                effect->SetAmount(amount);
                effect->SetCritChance(crit);
                effect->SetPctMods(pctMods);
            }
        }, Milliseconds(1));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_unstable_affliction_affliction::CalculateAmount,
            EFFECT_0, SPELL_AURA_PERIODIC_DAMAGE);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_unstable_affliction_affliction::HandleExpire, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 47422 - Everlasting Affliction (Corruption refresh) - AFFLICTION.md §7.3
// ===========================================================================================
class spell_warl_everlasting_affliction_refresh : public SpellScript
{
    PrepareSpellScript(spell_warl_everlasting_affliction_refresh);

    void HandleScriptEffect(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // Duration only - amount, crit, pctMods, amplitude and the tick counter are untouched
        // (unlike the stock class this replaces, which re-snapshotted SP and haste).
        if (Aura* aura = target->GetAura(Warlock::SPELL_CORRUPTION, caster->GetGUID()))
            aura->RefreshDuration();
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warl_everlasting_affliction_refresh::HandleScriptEffect, EFFECT_0,
            SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// ===========================================================================================
// 686 - Shadow Bolt (Affliction additive class) - AFFLICTION.md §7.5 (Nightfall's UA bonus tick)
// ===========================================================================================
class spell_warl_shadow_bolt_affliction : public SpellScript
{
    PrepareSpellScript(spell_warl_shadow_bolt_affliction);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !caster->HasAura(Warlock::SPELL_NIGHTFALL_R3))
            return;

        if (!target->HasAura(Warlock::SPELL_UNSTABLE_AFFLICTION, caster->GetGUID()))
            return;

        Warlock::FirePeriodicTickNow(target, caster->GetGUID(), Warlock::SPELL_UNSTABLE_AFFLICTION, EFFECT_0);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_shadow_bolt_affliction::HandleAfterHit);
    }
};

// ===========================================================================================
// 18094, 18095, 200766 - Nightfall - AFFLICTION.md §7.5
// ===========================================================================================
class spell_warl_nightfall_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_nightfall_affliction);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_SHADOW_TRANCE });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        int32 const bp2 = aurEff->GetAmount();
        caster->CastCustomSpell(caster, Warlock::SPELL_SHADOW_TRANCE, nullptr, nullptr, &bp2, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warl_nightfall_affliction::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 1454 - Life Tap - AFFLICTION.md §7.7 (full rewrite: level-scaled base, Improved Life Tap,
// Siphon Power's capstone SP buff)
// ===========================================================================================
namespace
{
    // §4.1 item 7 / §11 Q16: SpellInfoCorrections.cpp zeroes the runtime SpellInfo's
    // RealPointsPerLevel for 1454 every boot, so the *loaded* SpellInfo can't be used to compute
    // the level-scaled base. sSpellStore is the raw spell_dbc row, loaded once and never touched
    // by that correction.
    int32 CalculateLifeTapBase(uint8 level)
    {
        SpellEntry const* raw = sSpellStore.LookupEntry(Warlock::SPELL_LIFE_TAP);
        if (!raw)
            return 0;

        uint8 const baseLevel = uint8(raw->BaseLevel);
        uint8 const maxLevel = raw->MaxLevel ? uint8(raw->MaxLevel) : 80;
        uint8 const effectiveLevel = std::min(std::max(level, baseLevel), maxLevel);

        // SpellEffectInfo::CalcValue: basePoints (already +1 from die_sides) plus ppl per level
        // above BaseLevel, truncated toward zero.
        return raw->EffectBasePoints[EFFECT_0] + 1 +
               int32(raw->EffectRealPointsPerLevel[EFFECT_0] * float(effectiveLevel - baseLevel));
    }
}

class spell_warl_life_tap_affliction : public SpellScript
{
    PrepareSpellScript(spell_warl_life_tap_affliction);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_LIFE_TAP_ENERGIZE, SPELL_LIFE_TAP_ENERGIZE_2,
            Warlock::SPELL_IMPROVED_LIFE_TAP_BUFF });
    }

    SpellCastResult CheckCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return SPELL_CAST_OK;

        int32 const base = CalculateLifeTapBase(caster->GetLevel());
        return int32(caster->GetHealth()) > base ? SPELL_CAST_OK : SPELL_FAILED_FIZZLE;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 const base = CalculateLifeTapBase(caster->GetLevel());
        int32 mana = base + int32(caster->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_SHADOW) * 0.5f);

        // Shouldn't appear in the combat log (stock comment kept).
        target->ModifyHealth(-base);

        int32 const rankAmount = GetKnownRankAmount(caster,
            { Warlock::SPELL_IMPROVED_LIFE_TAP_R3, Warlock::SPELL_IMPROVED_LIFE_TAP_R2,
              Warlock::SPELL_IMPROVED_LIFE_TAP_R1 });
        if (rankAmount)
            AddPct(mana, rankAmount);

        if (caster->GetPower(POWER_MANA) < caster->GetMaxPower(POWER_MANA) / 2)
            mana = int32(float(mana) * 1.5f);

        caster->CastCustomSpell(target, SPELL_LIFE_TAP_ENERGIZE, &mana, nullptr, nullptr, false);

        // Mana Feed - kept verbatim (icon 1982) for Demonology's Fel Vitality (CORE-AUDIT C20).
        if (AuraEffect const* aurEff = caster->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_WARLOCK,
                ICON_MANA_FEED, EFFECT_0))
        {
            int32 manaFeedVal = aurEff->GetAmount();
            if (manaFeedVal > 0)
            {
                ApplyPct(manaFeedVal, mana);
                caster->CastCustomSpell(caster, SPELL_LIFE_TAP_ENERGIZE_2, &manaFeedVal, nullptr, nullptr, true);
            }
        }

        // Capstone (200765): using Life Tap grants a flat-SP buff worth 10% of SP for 15 sec.
        if (caster->HasAura(Warlock::SPELL_IMPROVED_LIFE_TAP_R3))
        {
            caster->RemoveAurasDueToSpell(Warlock::SPELL_IMPROVED_LIFE_TAP_BUFF);
            caster->CastSpell(caster, Warlock::SPELL_IMPROVED_LIFE_TAP_BUFF, true);
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warl_life_tap_affliction::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
        OnCheckCast += SpellCheckCastFn(spell_warl_life_tap_affliction::CheckCast);
    }
};

// ===========================================================================================
// 200726, 200727 - Improved Life Tap / Siphon Power flat-SP buffs - AFFLICTION.md §7.8
// ===========================================================================================
class spell_warl_spell_power_pct_buff : public AuraScript
{
    PrepareAuraScript(spell_warl_spell_power_pct_buff);

    void CalculateDamageAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Unit* caster = GetCaster();
        if (!caster)
        {
            amount = 0;
            return;
        }

        int32 const benefit = caster->SpellBaseDamageBonusDone(SpellSchoolMask(aurEff->GetMiscValue()));
        amount = CalculatePct(std::max<int32>(0, benefit), amount);
    }

    void CalculateHealingAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Unit* caster = GetCaster();
        if (!caster)
        {
            amount = 0;
            return;
        }

        int32 const benefit = caster->SpellBaseHealingBonusDone(SpellSchoolMask(aurEff->GetMiscValue()));
        amount = CalculatePct(std::max<int32>(0, benefit), amount);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_spell_power_pct_buff::CalculateDamageAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_DONE);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_spell_power_pct_buff::CalculateHealingAmount, EFFECT_1,
            SPELL_AURA_MOD_HEALING_DONE);
    }
};

// ===========================================================================================
// 1120 - Drain Soul - AFFLICTION.md §7.10 (Soul Shard grant, Siphon Power SP buff, Soul Siphon)
// ===========================================================================================
class spell_warl_drain_soul_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_drain_soul_affliction);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (!caster || !target || !caster->isHonorOrXPTarget(target))
            return;

        Warlock::GrantSoulShard(caster);

        if (caster->HasAura(Warlock::SPELL_SIPHON_POWER_R1) || caster->HasAura(Warlock::SPELL_SIPHON_POWER_R2))
        {
            caster->RemoveAurasDueToSpell(Warlock::SPELL_SIPHON_POWER_BUFF);
            caster->CastSpell(caster, Warlock::SPELL_SIPHON_POWER_BUFF, true);
        }
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        // Stops the stock KILL proc (eff3) from double-granting Improved Drain Soul's mana
        // alongside -18213's own script - that row now carries the sole grant (§8).
        return false;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (caster && target)
            amount = int32(float(amount) * Warlock::GetSoulSiphonMultiplier(caster, target));
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_drain_soul_affliction::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        DoCheckProc += AuraCheckProcFn(spell_warl_drain_soul_affliction::CheckProc);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_drain_soul_affliction::CalculateAmount, EFFECT_1,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// ===========================================================================================
// 689 - Drain Life - AFFLICTION.md §7.19 (Soul Siphon, Inevitable Demise consumption)
// ===========================================================================================
class spell_warl_drain_life_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_drain_life_affliction);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        amount = int32(float(amount) * Warlock::GetSoulSiphonMultiplier(caster, target));

        if (Aura const* inevitableDemise = caster->GetAura(Warlock::SPELL_INEVITABLE_DEMISE))
            amount = int32(float(amount) * (1.0f + 0.05f * float(inevitableDemise->GetStackAmount())));
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // Drain Life consumes every stack on cast; Drain Soul neither consumes nor gains (QA #10).
        if (Unit* caster = GetCaster())
            caster->RemoveAurasDueToSpell(Warlock::SPELL_INEVITABLE_DEMISE);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_warl_drain_life_affliction::CalculateAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_LEECH);
        AfterEffectApply += AuraEffectApplyFn(spell_warl_drain_life_affliction::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_LEECH, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 29341 - Shadowburn (shard grant only) - AFFLICTION.md §7.10
// ===========================================================================================
class spell_warl_shadowburn_shard : public AuraScript
{
    PrepareAuraScript(spell_warl_shadowburn_shard);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetTarget();
        if (caster && target && caster->isHonorOrXPTarget(target))
            Warlock::GrantSoulShard(caster);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_shadowburn_shard::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 200709 - Soul Shard buff - AFFLICTION.md §7.10
// ===========================================================================================
class spell_warl_soul_shard_buff : public AuraScript
{
    PrepareAuraScript(spell_warl_soul_shard_buff);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        // Resyncs the stack/duration against the deque as a side effect.
        if (Player* player = GetTarget()->ToPlayer())
            Warlock::GetSoulShardCount(player);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        if (Player* player = GetTarget()->ToPlayer())
            Warlock::ClearSoulShards(player);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_soul_shard_buff::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_soul_shard_buff::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 200710 - Soulburn - AFFLICTION.md §7.11
// ===========================================================================================
class spell_warl_soulburn : public SpellScript
{
    PrepareSpellScript(spell_warl_soulburn);

    SpellCastResult CheckCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return SPELL_CAST_OK;

        if (Warlock::GetSoulShardCount(caster) < 1)
            return SPELL_FAILED_REAGENTS;

        // §11 Q19: refused while already primed, so a shard isn't wasted.
        if (caster->HasAura(Warlock::SPELL_SOULBURN_MARKER))
            return SPELL_FAILED_AURA_BOUNCED;

        return SPELL_CAST_OK;
    }

    void HandleOnCast()
    {
        if (Player* caster = GetCaster()->ToPlayer())
            Warlock::ConsumeSoulShards(caster, 1);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_soulburn::CheckCast);
        OnCast += SpellCastFn(spell_warl_soulburn::HandleOnCast);
    }
};

// ===========================================================================================
// 27243 - Seed of Corruption (Soulburn) - AFFLICTION.md §7.6
// ===========================================================================================
class spell_warl_seed_of_corruption_soulburn : public SpellScript
{
    PrepareSpellScript(spell_warl_seed_of_corruption_soulburn);

    bool _empowered = false;

    // Consumed in OnCast, not AfterCast: 27243 has Speed > 0 (missile), so an AfterCast/AfterHit
    // pair happens to work too, but OnCast is order-proof regardless of a spell's Speed (§7.6).
    void HandleOnCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        _empowered = caster && Warlock::TryConsumeSoulburnMarker(caster);
    }

    void HandleAfterHit()
    {
        if (!_empowered)
            return;

        Unit* caster = GetCaster();
        Unit* primary = GetHitUnit();
        if (!caster || !primary)
            return;

        std::list<Unit*> candidates;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(caster, caster, 30.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(caster, candidates, check);
        Cell::VisitObjects(caster, searcher, 30.0f);

        candidates.remove_if([&](Unit* unit)
        {
            return unit == primary || !unit->IsAlive() || !caster->IsValidAttackTarget(unit) ||
                   !unit->IsInCombatWith(caster) || !caster->IsWithinLOSInMap(unit) ||
                   unit->HasAura(Warlock::SPELL_SEED_OF_CORRUPTION_DOT, caster->GetGUID());
        });

        if (candidates.empty())
            return;

        // "2 closest enemies" - closest to the primary target (§11 Q4).
        candidates.sort(Acore::ObjectDistanceOrderPred(primary));

        uint8 placed = 0;
        for (Unit* unit : candidates)
        {
            if (placed >= 2)
                break;

            // AddAura, not a cast - no proc rolls, no mana, no Nightfall charge (G15).
            caster->AddAura(Warlock::SPELL_SEED_OF_CORRUPTION_DOT, unit);
            ++placed;
        }
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warl_seed_of_corruption_soulburn::HandleOnCast);
        AfterHit += SpellHitFn(spell_warl_seed_of_corruption_soulburn::HandleAfterHit);
    }
};

// ===========================================================================================
// 27285 - Seed of Corruption (detonation) - AFFLICTION.md §7.6 (chain-detonation fix, Virulence)
// ===========================================================================================
class spell_warl_seed_of_corruption_detonation_affliction : public SpellScript
{
    PrepareSpellScript(spell_warl_seed_of_corruption_detonation_affliction);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        int32 const dealt = GetHitDamage();
        if (!caster || !target)
            return;

        // Chain-detonation fix: the stock TAKEN proc never fires between two Seeds (both are the
        // same SpellInfo - SpellAuras.cpp's "no proc from itself" check compares SpellInfo, not
        // aura instance). Subtract the dealt damage from every 27243 on the hit unit (any caster)
        // and detonate whichever reaches zero, deferred by one update to avoid casting inside a hit.
        std::vector<Aura*> seeds;
        auto const range = target->GetAppliedAuras().equal_range(Warlock::SPELL_SEED_OF_CORRUPTION_DOT);
        for (auto itr = range.first; itr != range.second; ++itr)
            seeds.push_back(itr->second->GetBase());

        for (Aura* seed : seeds)
        {
            AuraEffect* effect = seed->GetEffect(EFFECT_1);
            if (!effect)
                continue;

            int32 const remaining = effect->GetAmount() - dealt;
            if (remaining > 0)
            {
                effect->SetAmount(remaining);
                continue;
            }

            ObjectGuid const seedCasterGuid = seed->GetCasterGUID();
            target->m_Events.AddEventAtOffset([target, seedCasterGuid]()
            {
                if (Aura* current = target->GetAura(Warlock::SPELL_SEED_OF_CORRUPTION_DOT, seedCasterGuid))
                    Warlock::DetonateSeed(current);
            }, Milliseconds(1));
        }

        if (dealt > 0 && caster->HasAura(Warlock::SPELL_VIRULENCE_R3))
            caster->AddAura(Warlock::SPELL_CORRUPTION, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_seed_of_corruption_detonation_affliction::HandleAfterHit);
    }
};

// ===========================================================================================
// 48181 - Haunt (Soulburn) - AFFLICTION.md §7.13
// ===========================================================================================
class spell_warl_haunt_soulburn : public SpellScript
{
    PrepareSpellScript(spell_warl_haunt_soulburn);

    bool _empowered = false;

    void HandleOnCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        _empowered = caster && Warlock::TryConsumeSoulburnMarker(caster);
    }

    void HandleAfterHit()
    {
        if (!_empowered)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (caster && target)
            caster->CastSpell(target, Warlock::SPELL_SOULBURN_HAUNT_DEBUFF, true);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_warl_haunt_soulburn::HandleOnCast);
        AfterHit += SpellHitFn(spell_warl_haunt_soulburn::HandleAfterHit);
    }
};

class spell_warl_haunt_soulburn_aura : public AuraScript
{
    PrepareAuraScript(spell_warl_haunt_soulburn_aura);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (caster && target)
            target->RemoveAura(Warlock::SPELL_SOULBURN_HAUNT_DEBUFF, caster->GetGUID());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_haunt_soulburn_aura::HandleRemove, EFFECT_2,
            SPELL_AURA_MOD_DAMAGE_FROM_CASTER, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 63108, 200767 - Siphon Life - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_siphon_life_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_siphon_life_affliction);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Warlock::SPELL_SIPHON_LIFE_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || !damageInfo->GetDamage())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->Id != Warlock::SPELL_CORRUPTION)
            return false;

        Player* player = GetTarget()->ToPlayer();
        return player && Warlock::GetActiveLeechTalent(player) == Warlock::LeechTalent::SiphonLife;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        int32 amount = CalculatePct(int32(eventInfo.GetDamageInfo()->GetDamage()), aurEff->GetAmount());
        int32 const cap = int32(CalculatePct(caster->GetMaxHealth(), 5));
        if (amount > cap)
            amount = cap;

        if (AuraEffect const* glyph = caster->GetAuraEffect(SPELL_GLYPH_OF_SIPHON_LIFE, EFFECT_0))
            AddPct(amount, glyph->GetAmount());

        caster->CastCustomSpell(Warlock::SPELL_SIPHON_LIFE_HEAL, SPELLVALUE_BASE_POINT0, amount, caster, true,
            nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_siphon_life_affliction::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_warl_siphon_life_affliction::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 18219 - Grim Reach r2 capstone - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_grim_reach_capstone : public AuraScript
{
    PrepareAuraScript(spell_warl_grim_reach_capstone);

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        caster->CastSpell(target, Warlock::SPELL_GRIM_REACH_BOLT, true, nullptr, aurEff);
        caster->CastSpell(target, Warlock::SPELL_GRIM_REACH_DEBUFF, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_warl_grim_reach_capstone::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 200741 - Shadow Pact r3 - AFFLICTION.md §7.15 (Tainted Soul generation)
// ===========================================================================================
class spell_warl_shadow_pact_tainted_soul : public AuraScript
{
    PrepareAuraScript(spell_warl_shadow_pact_tainted_soul);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        switch (spellInfo->Id)
        {
            case Warlock::SPELL_CORRUPTION:
            case Warlock::SPELL_BANE_OF_AGONY:
            case Warlock::SPELL_UNSTABLE_AFFLICTION:
                return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) != 0;
            case Warlock::SPELL_PHANTOM_SINGULARITY_DAMAGE:
                // QA #41: PS non-crits never reach this proc (HitMask = CRITICAL on the row).
                return true;
            default:
                return false;
        }
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        uint8 const stacks = (spellInfo && spellInfo->Id != Warlock::SPELL_CORRUPTION &&
                               spellInfo->Id != Warlock::SPELL_PHANTOM_SINGULARITY_DAMAGE) ? 2 : 1;

        Warlock::AddTaintedSoul(caster, target, stacks);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_shadow_pact_tainted_soul::CheckProc);
        OnProc += AuraProcFn(spell_warl_shadow_pact_tainted_soul::HandleProc);
    }
};

// ===========================================================================================
// 200721 - Tainted Soul - AFFLICTION.md §7.15
// ===========================================================================================
class spell_warl_tainted_soul : public AuraScript
{
    PrepareAuraScript(spell_warl_tainted_soul);

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_DEATH)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        uint32 const stacks = aurEff->GetBase()->GetStackAmount();
        Warlock::EruptTaintedSoul(caster, target, uint8(std::min<uint32>(100u, 10u * stacks)));
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_tainted_soul::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 200722 - Tainted Soul (eruption) - AFFLICTION.md §7.15
// ===========================================================================================
class spell_warl_tainted_soul_eruption : public SpellScript
{
    PrepareSpellScript(spell_warl_tainted_soul_eruption);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        WorldLocation const* dest = GetExplTargetDest();
        if (!dest || targets.size() <= 5)
            return;

        // The erupting unit sits at this exact position (Warlock::EruptTaintedSoul's SetDst), so
        // sorting by distance to it and trimming to 5 keeps it in (QA #13/#14).
        float const x = dest->GetPositionX();
        float const y = dest->GetPositionY();
        targets.sort([x, y](WorldObject const* a, WorldObject const* b)
        {
            return a->GetExactDist2dSq(x, y) < b->GetExactDist2dSq(x, y);
        });
        targets.resize(5);
    }

    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        int32 const pct = GetSpellValue()->EffectBasePoints[EFFECT_1];
        SetHitDamage(GetHitDamage() * pct / 100);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warl_tainted_soul_eruption::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_warl_tainted_soul_eruption::HandleDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// ===========================================================================================
// 200754, 200755 - Agonizing Pain - AFFLICTION.md §7.16
// ===========================================================================================
class spell_warl_agonizing_pain : public AuraScript
{
    PrepareAuraScript(spell_warl_agonizing_pain);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && spellInfo->Id == Warlock::SPELL_BANE_OF_AGONY;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        uint8 const cap = Warlock::GetAgonyStackCap(caster);
        uint8 const stacks = Warlock::GetAgonyStacks(target, caster->GetGUID());

        if (stacks < cap)
            Warlock::AddAgonyStacks(caster, target, 1);
        else
            caster->CastSpell(target, Warlock::SPELL_AGONIZING_PAIN_BOLT, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_agonizing_pain::CheckProc);
        OnProc += AuraProcFn(spell_warl_agonizing_pain::HandleProc);
    }
};

// ===========================================================================================
// 32385, 32387, 32392 - Shadow Embrace - AFFLICTION.md §7.12
// ===========================================================================================
class spell_warl_shadow_embrace_affliction : public AuraScript
{
    PrepareAuraScript(spell_warl_shadow_embrace_affliction);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || !(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_SHADOW))
            return false;

        uint32 const typeMask = eventInfo.GetTypeMask();
        if (!(typeMask & PROC_FLAG_DONE_PERIODIC))
        {
            // Non-periodic hit: any direct Shadow damage effect, incl. Death Coil's HEALTH_LEECH
            // (type 9, not SCHOOL_DAMAGE - missing this silently drops Death Coil).
            return spellInfo->HasEffect(SPELL_EFFECT_SCHOOL_DAMAGE) || spellInfo->HasEffect(SPELL_EFFECT_HEALTH_LEECH);
        }

        // Periodic tick: only Drain Life and Drain Soul (not every Shadow DoT).
        return spellInfo->Id == Warlock::SPELL_DRAIN_LIFE || spellInfo->Id == Warlock::SPELL_DRAIN_SOUL;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_shadow_embrace_affliction::CheckProc);
    }
};

// ===========================================================================================
// 17785 - Fel Concentration r3 capstone - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_fel_concentration_capstone : public AuraScript
{
    PrepareAuraScript(spell_warl_fel_concentration_capstone);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || Warlock::GetActiveLeechTalent(player) != Warlock::LeechTalent::FelConcentration)
            return false;

        if (eventInfo.GetProcTarget() == caster)
            return false;

        Spell* current = caster->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        if (!current)
            current = caster->GetCurrentSpell(CURRENT_CHANNELED_SPELL);
        if (!current || !current->m_spellInfo)
            return false;

        SpellInfo const* castInfo = current->m_spellInfo;
        return castInfo->HasEffect(SPELL_EFFECT_SCHOOL_DAMAGE) || castInfo->HasAura(SPELL_AURA_PERIODIC_DAMAGE) ||
               castInfo->HasAura(SPELL_AURA_PERIODIC_LEECH);
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        if (!caster || !damageInfo || !damageInfo->GetDamage())
            return;

        int32 amount = CalculatePct(int32(damageInfo->GetDamage()), 20);
        int32 const cap = int32(CalculatePct(caster->GetMaxHealth(), 5));
        if (amount > cap)
            amount = cap;

        caster->CastCustomSpell(Warlock::SPELL_FEL_CONCENTRATION_HEAL, SPELLVALUE_BASE_POINT0, amount, caster, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_warl_fel_concentration_capstone::CheckProc);
        OnProc += AuraProcFn(spell_warl_fel_concentration_capstone::HandleProc);
    }
};

// ===========================================================================================
// 200729 - Phantom Singularity - AFFLICTION.md §7.17
// ===========================================================================================
class spell_warl_phantom_singularity : public AuraScript
{
    PrepareAuraScript(spell_warl_phantom_singularity);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (caster && target)
            caster->CastSpell(target, Warlock::SPELL_PHANTOM_SINGULARITY_DAMAGE, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_phantom_singularity::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// ===========================================================================================
// 200730 - Phantom Singularity (damage) - AFFLICTION.md §7.17
// ===========================================================================================
class spell_warl_phantom_singularity_damage : public SpellScript
{
    PrepareSpellScript(spell_warl_phantom_singularity_damage);

    int32 _totalDamage = 0;

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Unit* explicitTarget = GetExplTargetUnit();
        if (!caster)
            return;

        targets.remove_if([caster, explicitTarget](WorldObject const* obj)
        {
            if (obj == explicitTarget)
                return false;

            Unit const* unit = obj->ToUnit();
            return !unit || !unit->IsInCombatWith(caster);
        });
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        float const mult = Warlock::GetSoulSiphonMultiplier(caster, target);
        SetHitDamage(int32(float(GetHitDamage()) * mult));
    }

    void HandleAfterHit()
    {
        if (GetHitDamage() > 0)
            _totalDamage += GetHitDamage();
    }

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        if (!caster || _totalDamage <= 0)
            return;

        int32 const heal = CalculatePct(_totalDamage, 20);
        caster->CastCustomSpell(caster, Warlock::SPELL_PHANTOM_SINGULARITY_HEAL, &heal, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warl_phantom_singularity_damage::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_warl_phantom_singularity_damage::HandleHit, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_warl_phantom_singularity_damage::HandleAfterHit);
        AfterCast += SpellCastFn(spell_warl_phantom_singularity_damage::HandleAfterCast);
    }
};

// ===========================================================================================
// 6789 - Death Coil - AFFLICTION.md §7.19 (Harvester of Death capstone)
// ===========================================================================================
class spell_warl_harvester_death_coil : public SpellScript
{
    PrepareSpellScript(spell_warl_harvester_death_coil);

    void HandleLeech(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->HasAura(Warlock::SPELL_HARVESTER_OF_DEATH_CAPSTONE))
            return;

        if (!caster->HealthBelowPct(80))
            return;

        // Not SetHitDamage here: SPELL_EFFECT_HEALTH_LEECH's own handler runs after this hook and
        // is what adds this effect's damage into m_damage, so GetHitDamage() is still 0 inside it.
        SetEffectValue(GetEffectValue() * 2);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warl_harvester_death_coil::HandleLeech, EFFECT_0,
            SPELL_EFFECT_HEALTH_LEECH);
    }
};

// ===========================================================================================
// 54037, 54038 - Improved Felhunter - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_improved_felhunter : public AuraScript
{
    PrepareAuraScript(spell_warl_improved_felhunter);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        Pet* pet = player->GetPet();
        if (!pet || pet->GetEntry() != FELHUNTER_ENTRY)
            return;

        int32 const amount = aurEff->GetAmount();
        AuraEffect const* existing = pet->GetAuraEffect(Warlock::SPELL_IMPROVED_FELHUNTER_PET_BUFF, EFFECT_0);
        if (existing && existing->GetAmount() == amount)
            return;

        player->CastCustomSpell(pet, Warlock::SPELL_IMPROVED_FELHUNTER_PET_BUFF, &amount, nullptr, nullptr, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (Pet* pet = player ? player->GetPet() : nullptr)
            pet->RemoveAurasDueToSpell(Warlock::SPELL_IMPROVED_FELHUNTER_PET_BUFF);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_warl_improved_felhunter::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_warl_improved_felhunter::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 54049-54053 - Shadow Bite (Felhunter pet ability, all ranks) - AFFLICTION.md §7.19 (B17c)
// ===========================================================================================
class spell_warl_shadow_bite_improved_felhunter : public SpellScript
{
    PrepareSpellScript(spell_warl_shadow_bite_improved_felhunter);

    void HandleAfterHit()
    {
        Unit* pet = GetCaster();
        if (!pet || GetHitDamage() <= 0)
            return;

        Unit* owner = pet->GetOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player || !player->HasAura(Warlock::SPELL_IMPROVED_FELHUNTER_R2))
            return;

        int32 const energize = CalculatePct(int32(pet->GetMaxPower(POWER_MANA)), 10);
        if (energize > 0)
            pet->EnergizeBySpell(pet, GetSpellInfo()->Id, energize, POWER_MANA);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_warl_shadow_bite_improved_felhunter::HandleAfterHit);
    }
};

// ===========================================================================================
// 200733 - Soul Swap (inhale) - AFFLICTION.md §7.9
// ===========================================================================================
class spell_warl_soul_swap : public SpellScript
{
    PrepareSpellScript(spell_warl_soul_swap);

    SpellCastResult CheckCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        bool const hasDot = target->HasAura(Warlock::SPELL_CORRUPTION, caster->GetGUID()) ||
                             target->HasAura(Warlock::SPELL_BANE_OF_AGONY, caster->GetGUID()) ||
                             target->HasAura(Warlock::SPELL_UNSTABLE_AFFLICTION, caster->GetGUID());

        return hasDot ? SPELL_CAST_OK : SPELL_FAILED_BAD_TARGETS;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        std::vector<Warlock::SoulSwapEntry> entries;

        if (target->HasAura(Warlock::SPELL_CORRUPTION, caster->GetGUID()))
        {
            Warlock::SoulSwapEntry entry;
            entry.spellId = Warlock::SPELL_CORRUPTION;
            entries.push_back(entry);
        }

        if (Aura const* bane = target->GetAura(Warlock::SPELL_BANE_OF_AGONY, caster->GetGUID()))
        {
            AuraEffect const* effect = bane->GetEffect(EFFECT_0);
            Warlock::SoulSwapEntry entry;
            entry.spellId = Warlock::SPELL_BANE_OF_AGONY;
            entry.amount = effect ? effect->GetAmount() : 0;
            entry.crit = effect ? effect->GetCritChance() : 0.0f;
            entry.pctMods = effect ? effect->GetPctMods() : 0.0f;
            entry.duration = bane->GetDuration();
            entry.maxDuration = bane->GetMaxDuration();
            entry.agonyStacks = Warlock::GetAgonyStacks(target, caster->GetGUID());
            entries.push_back(entry);
        }

        if (Aura const* ua = target->GetAura(Warlock::SPELL_UNSTABLE_AFFLICTION, caster->GetGUID()))
        {
            AuraEffect const* effect = ua->GetEffect(EFFECT_0);
            Warlock::SoulSwapEntry entry;
            entry.spellId = Warlock::SPELL_UNSTABLE_AFFLICTION;
            entry.amount = effect ? effect->GetAmount() : 0;
            entry.crit = effect ? effect->GetCritChance() : 0.0f;
            entry.pctMods = effect ? effect->GetPctMods() : 0.0f;
            entry.duration = ua->GetDuration();
            entry.maxDuration = ua->GetMaxDuration();
            entries.push_back(entry);
        }

        Warlock::StoreSoulSwap(caster, target->GetGUID(), std::move(entries));
        caster->CastSpell(caster, Warlock::SPELL_SOUL_SWAP_COPIED_MARKER, true);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_soul_swap::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_warl_soul_swap::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// ===========================================================================================
// 200734 - Soul Swap: Exhale - AFFLICTION.md §7.9
// ===========================================================================================
class spell_warl_soul_swap_exhale : public SpellScript
{
    PrepareSpellScript(spell_warl_soul_swap_exhale);

    SpellCastResult CheckCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        ObjectGuid source;
        if (!Warlock::HasSoulSwapCopy(caster, &source))
            return SPELL_FAILED_CANT_DO_THAT_RIGHT_NOW;

        // "Cannot Soul Swap to the same target."
        if (source == target->GetGUID())
            return SPELL_FAILED_BAD_TARGETS;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetCaster()->ToPlayer();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        ObjectGuid sourceGuid;
        std::vector<Warlock::SoulSwapEntry> entries;
        if (!Warlock::TakeSoulSwap(caster, sourceGuid, entries))
            return;

        if (sourceGuid == target->GetGUID())
            return;

        for (Warlock::SoulSwapEntry const& entry : entries)
        {
            Aura* aura = caster->AddAura(entry.spellId, target);
            if (!aura)
                continue;

            // Corruption is presence-only - a fresh application using current stats (spec).
            if (entry.spellId == Warlock::SPELL_CORRUPTION)
                continue;

            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            {
                effect->SetAmount(entry.amount);
                effect->SetCritChance(entry.crit);
                effect->SetPctMods(entry.pctMods);
            }

            aura->SetMaxDuration(entry.maxDuration);
            aura->SetDuration(entry.duration);

            if (entry.spellId == Warlock::SPELL_BANE_OF_AGONY)
                Warlock::AddAgonyStacks(caster, target, entry.agonyStacks);
        }

        caster->RemoveAurasDueToSpell(Warlock::SPELL_SOUL_SWAP_COPIED_MARKER);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_soul_swap_exhale::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_warl_soul_swap_exhale::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// ===========================================================================================
// 200736 - Soul Harvest - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_soul_harvest : public SpellScript
{
    PrepareSpellScript(spell_warl_soul_harvest);

    void HandleAfterCast()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(caster, caster, 40.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, 40.0f);

        uint32 n = 0;
        for (Unit* unit : nearby)
        {
            if (!unit->IsInCombatWith(caster))
                continue;

            // B4: cheap Classless clause - counts a Classless character's Shadow Word: Pain /
            // Devouring Plague too, alongside the warlock's own Corruption / Bane of Agony.
            if (unit->HasAura(Warlock::SPELL_CORRUPTION, caster->GetGUID()) ||
                unit->HasAura(Warlock::SPELL_BANE_OF_AGONY, caster->GetGUID()) ||
                unit->HasAura(SPELL_IMMOLATE, caster->GetGUID()) ||
                unit->HasAura(SPELL_SHADOW_WORD_PAIN, caster->GetGUID()) ||
                unit->HasAura(SPELL_DEVOURING_PLAGUE, caster->GetGUID()))
                ++n;
        }

        int32 const duration = std::min<int32>(24000, 10000 + 3000 * int32(n));

        if (Aura* self = caster->GetAura(Warlock::SPELL_SOUL_HARVEST))
        {
            self->SetMaxDuration(duration);
            self->SetDuration(duration);
        }

        if (Pet* pet = player->GetPet())
            if (Aura* petAura = pet->GetAura(Warlock::SPELL_SOUL_HARVEST, caster->GetGUID()))
            {
                petAura->SetMaxDuration(duration);
                petAura->SetDuration(duration);
            }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_warl_soul_harvest::HandleAfterCast);
    }
};

// ===========================================================================================
// 200738 - Burning Rush (toggle) - AFFLICTION.md §7.19
// ===========================================================================================
class spell_warl_burning_rush : public SpellScript
{
    PrepareSpellScript(spell_warl_burning_rush);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster->HasAura(Warlock::SPELL_BURNING_RUSH))
        {
            caster->RemoveAurasDueToSpell(Warlock::SPELL_BURNING_RUSH);
            return SPELL_FAILED_DONT_REPORT;
        }
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warl_burning_rush::CheckCast);
    }
};

void AddSC_warlock_affliction_spell_scripts()
{
    RegisterSpellScript(spell_warl_corruption_affliction);
    RegisterSpellAndAuraScriptPair(spell_warl_bane_of_agony, spell_warl_bane_of_agony_aura);
    RegisterSpellScript(spell_warl_unstable_affliction_affliction);
    RegisterSpellScript(spell_warl_everlasting_affliction_refresh);
    RegisterSpellScript(spell_warl_shadow_bolt_affliction);
    RegisterSpellScript(spell_warl_nightfall_affliction);
    RegisterSpellScript(spell_warl_life_tap_affliction);
    RegisterSpellScript(spell_warl_spell_power_pct_buff);
    RegisterSpellScript(spell_warl_drain_soul_affliction);
    RegisterSpellScript(spell_warl_drain_life_affliction);
    RegisterSpellScript(spell_warl_shadowburn_shard);
    RegisterSpellScript(spell_warl_soul_shard_buff);
    RegisterSpellScript(spell_warl_soulburn);
    RegisterSpellScript(spell_warl_seed_of_corruption_soulburn);
    RegisterSpellScript(spell_warl_seed_of_corruption_detonation_affliction);
    RegisterSpellAndAuraScriptPair(spell_warl_haunt_soulburn, spell_warl_haunt_soulburn_aura);
    RegisterSpellScript(spell_warl_siphon_life_affliction);
    RegisterSpellScript(spell_warl_grim_reach_capstone);
    RegisterSpellScript(spell_warl_shadow_pact_tainted_soul);
    RegisterSpellScript(spell_warl_tainted_soul);
    RegisterSpellScript(spell_warl_tainted_soul_eruption);
    RegisterSpellScript(spell_warl_agonizing_pain);
    RegisterSpellScript(spell_warl_shadow_embrace_affliction);
    RegisterSpellScript(spell_warl_fel_concentration_capstone);
    RegisterSpellScript(spell_warl_phantom_singularity);
    RegisterSpellScript(spell_warl_phantom_singularity_damage);
    RegisterSpellScript(spell_warl_harvester_death_coil);
    RegisterSpellScript(spell_warl_improved_felhunter);
    RegisterSpellScript(spell_warl_shadow_bite_improved_felhunter);
    RegisterSpellScript(spell_warl_soul_swap);
    RegisterSpellScript(spell_warl_soul_swap_exhale);
    RegisterSpellScript(spell_warl_soul_harvest);
    RegisterSpellScript(spell_warl_burning_rush);
}
