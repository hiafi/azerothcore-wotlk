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
 * Druid Balance rework (docs/reworks/druid-balance.md,
 * .agents/plans/druid-rework/druid-rework.BALANCE.md) - every genuinely new script class this pass
 * needs goes here, same "spell_dru_" naming convention as stock spell_druid.cpp. A stock class that
 * needs new behaviour is *replaced* by a same-named-idea class here and rebound by SQL (the stock
 * binding is DELETEd, the stock class itself is left in place, unbound) - see
 * .agents/plans/druid-rework/druid-rework.CORE-AUDIT.md §3 item 10 for why upstream-owned
 * spell_druid.cpp is never edited in place. Hooks that can't be a SpellScript/AuraScript at all
 * live in DruidMechanics.h/.cpp (core call sites) or druid_hooks.cpp (ScriptMgr handlers that run
 * on every damage/heal event server-wide).
 *
 * Four classes below (spell_dru_eclipse_balance, spell_dru_moonkin_form_proc_balance,
 * spell_dru_brambles_treant_balance, spell_dru_treant_scaling_balance) are the CORE-AUDIT/BALANCE
 * "corrections" replacements for the four stock spell_druid.cpp classes BALANCE.md §10 originally
 * said to rewrite in place (spell_dru_eclipse, spell_dru_moonkin_form_passive_proc,
 * spell_dru_brambles_treant, spell_dru_treant_scaling) - those stock classes are untouched and left
 * unbound; WP-A rebinds their spell ids to these new names instead. The names below match the
 * WP-B brief verbatim - WP-A's unbind_script/scripted_by calls must spell them the same way or the
 * binding silently registers nothing.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "DruidMechanics.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
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
#include <array>
#include <list>

// 2912 - Starfire - triggers the cleave (BALANCE.md §4 "Starfire cleave")
class spell_dru_starfire_cleave : public SpellScript
{
    PrepareSpellScript(spell_dru_starfire_cleave);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_STARFIRE_CLEAVE });
    }

    void HandleAfterHit()
    {
        GetCaster()->CastSpell(GetHitUnit(), Druid::SPELL_STARFIRE_CLEAVE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_starfire_cleave::HandleAfterHit);
    }
};

// 200333 - Starsurge - Starweaver r3 capstone (talent table 3,0) and Moonfury r3's Astral Surge
// capstone (talent table 5,1, BALANCE.md §7 "Astral Surge")
class spell_dru_starsurge : public SpellScript
{
    PrepareSpellScript(spell_dru_starsurge);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_STARFALL });
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return;

        if (caster->HasAura(Druid::TALENT_STARWEAVER_R3))
            Druid::ReduceSpellCooldown(caster, Druid::SPELL_STARFALL, 2000);

        if (caster->HasAura(Druid::TALENT_MOONFURY_R3))
            Druid::ApplyAstralSurge(caster);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_dru_starsurge::HandleAfterCast);
    }
};

// 200336 - Fury of Elune - casts Celestial Alignment and halves the running Starsurge cooldown
class spell_dru_fury_of_elune : public SpellScript
{
    PrepareSpellScript(spell_dru_fury_of_elune);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_CELESTIAL_ALIGNMENT, Druid::SPELL_STARSURGE });
    }

    void HandleOnCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return;

        // BALANCE.md §7 "Celestial Alignment": BP0 = the caster's Eclipse rank eff1 amount, or 30
        // (Eclipse's untalented base) if untalented.
        int32 amount = 30;
        static constexpr std::array<uint32, 3> eclipseRanks =
            { Druid::SPELL_ECLIPSE_R1, Druid::SPELL_ECLIPSE_R2, Druid::SPELL_ECLIPSE_R3 };
        for (uint32 rank : eclipseRanks)
        {
            if (AuraEffect const* eff = caster->GetAuraEffect(rank, EFFECT_0))
            {
                amount = eff->GetAmount();
                break;
            }
        }

        caster->CastCustomSpell(Druid::SPELL_CELESTIAL_ALIGNMENT, SPELLVALUE_BASE_POINT0, amount, caster,
                                 TRIGGERED_FULL_MASK);
    }

    void HandleAfterCast()
    {
        Player* caster = GetCaster()->ToPlayer();
        if (!caster)
            return;

        if (uint32 remaining = caster->GetSpellCooldownDelay(Druid::SPELL_STARSURGE))
            Druid::ReduceSpellCooldown(caster, Druid::SPELL_STARSURGE, remaining / 2);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dru_fury_of_elune::HandleOnCast);
        AfterCast += SpellCastFn(spell_dru_fury_of_elune::HandleAfterCast);
    }
};

// 200336 - Fury of Elune - the periodic aura that fires the beam/splash each tick
class spell_dru_fury_of_elune_aura : public AuraScript
{
    PrepareAuraScript(spell_dru_fury_of_elune_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_FURY_OF_ELUNE_BEAM, Druid::SPELL_FURY_OF_ELUNE_SPLASH });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetTarget();
        if (!caster)
            return;

        caster->CastSpell(target, Druid::SPELL_FURY_OF_ELUNE_BEAM, TRIGGERED_FULL_MASK);
        caster->CastSpell(target, Druid::SPELL_FURY_OF_ELUNE_SPLASH, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_fury_of_elune_aura::HandlePeriodic, EFFECT_0,
                                                  SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 200323 - Improved Moonfire (rank 3) - Lunar Flare capstone (talent table 1,2)
class spell_dru_improved_moonfire_capstone : public AuraScript
{
    PrepareAuraScript(spell_dru_improved_moonfire_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_LUNAR_FLARE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return false;

        // "GetProcTarget() has a SPELL_AURA_PERIODIC_DAMAGE from the caster with family flag
        // 0x2" (Moonfire's dword 1 bit).
        return target->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_DRUID, 0x2, 0, 0,
                                      caster->GetGUID()) != nullptr;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        GetTarget()->CastSpell(eventInfo.GetProcTarget(), Druid::SPELL_LUNAR_FLARE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_improved_moonfire_capstone::CheckProc);
        OnProc += AuraProcFn(spell_dru_improved_moonfire_capstone::HandleProc);
    }
};

// 16820 - Nature's Reach (rank 2) - Moonfire spread capstone (talent table 2,3)
class spell_dru_natures_reach_moonfire_spread : public AuraScript
{
    PrepareAuraScript(spell_dru_natures_reach_moonfire_spread);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_MOONFIRE });
    }

    // Collects every hostile, attackable, living enemy within 5 yd of procTarget that lacks the
    // caster's Moonfire.
    static std::list<Unit*> FindSpreadTargets(Unit* caster, Unit* procTarget)
    {
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(procTarget, caster, 5.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(procTarget, nearby, check);
        Cell::VisitObjects(procTarget, searcher, 5.0f);

        nearby.remove_if([caster](Unit* unit)
        {
            return !caster->IsValidAttackTarget(unit) || unit->HasAura(Druid::SPELL_MOONFIRE, caster->GetGUID());
        });

        return nearby;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // The trigger spell must have a real base cast time.
        SpellInfo const* triggerSpell = eventInfo.GetSpellInfo();
        if (!triggerSpell || !triggerSpell->CastTimeEntry || triggerSpell->CastTimeEntry->CastTime <= 0)
            return false;

        Unit* caster = GetTarget();
        Unit* procTarget = eventInfo.GetProcTarget();
        if (!caster || !procTarget || !procTarget->HasAura(Druid::SPELL_MOONFIRE, caster->GetGUID()))
            return false;

        // The 6 s internal cooldown (spell_proc Cooldown) shouldn't be spent on nothing.
        return !FindSpreadTargets(caster, procTarget).empty();
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* procTarget = eventInfo.GetProcTarget();
        if (!caster || !procTarget)
            return;

        for (Unit* unit : FindSpreadTargets(caster, procTarget))
            caster->AddAura(Druid::SPELL_MOONFIRE, unit);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_natures_reach_moonfire_spread::CheckProc);
        OnProc += AuraProcFn(spell_dru_natures_reach_moonfire_spread::HandleProc);
    }
};

// 5570 - Insect Swarm - a real cast replaces a Swarming Rot copy rather than stacking with it
class spell_dru_insect_swarm_cast : public SpellScript
{
    PrepareSpellScript(spell_dru_insect_swarm_cast);

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        // BeforeHit runs for every target regardless of outcome - only remove the Swarming Rot
        // copy on an actual hit, or a miss/resist/immune on a target already carrying the copy
        // would strip it and leave nothing behind (code review caught this).
        if (missInfo != SPELL_MISS_NONE)
            return;

        if (Unit* target = GetHitUnit())
            target->RemoveAura(Druid::SPELL_INSECT_SWARM_COPY, GetCaster()->GetGUID());
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_dru_insect_swarm_cast::HandleBeforeHit);
    }
};

// 200332 - Swarming Rot (rank 3) - Insect Swarm propagation capstone (talent table 3,1)
class spell_dru_swarming_rot : public AuraScript
{
    PrepareAuraScript(spell_dru_swarming_rot);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_INSECT_SWARM_COPY });
    }

    // Original 5570 ticks only - the Swarming Rot copy (200352) carries no script of its own, so
    // it never spreads and propagation stays linear (BALANCE.md §7 "Insect Swarm propagation").
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && spellInfo->Id == Druid::SPELL_INSECT_SWARM;
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* procTarget = eventInfo.GetProcTarget();
        if (!caster || !procTarget)
            return;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(procTarget, caster, 8.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(procTarget, nearby, check);
        Cell::VisitObjects(procTarget, searcher, 8.0f);

        nearby.remove_if([caster](Unit* unit)
        {
            return !unit->IsInCombatWith(caster) || !caster->IsValidAttackTarget(unit) ||
                unit->HasAura(Druid::SPELL_INSECT_SWARM, caster->GetGUID()) ||
                unit->HasAura(Druid::SPELL_INSECT_SWARM_COPY, caster->GetGUID());
        });

        if (nearby.empty())
            return;

        // At most one per tick - the nearest qualifying enemy.
        nearby.sort(Acore::ObjectDistanceOrderPred(procTarget));
        caster->CastSpell(nearby.front(), Druid::SPELL_INSECT_SWARM_COPY, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_swarming_rot::CheckProc);
        OnProc += AuraProcFn(spell_dru_swarming_rot::HandleProc);
    }
};

// 16840 - Brambles (rank 3) - Entangling Roots silence capstone (talent table 4,3)
class spell_dru_brambles_silence : public AuraScript
{
    PrepareAuraScript(spell_dru_brambles_silence);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_BRAMBLES_SILENCE });
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (caster && target)
            caster->CastSpell(target, Druid::SPELL_BRAMBLES_SILENCE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_dru_brambles_silence::HandleProc);
    }
};

// 33831 - Force of Nature
class spell_dru_force_of_nature : public SpellScript
{
    PrepareSpellScript(spell_dru_force_of_nature);

    SpellCastResult CheckCast()
    {
        if (GetCaster()->GetPetGUID())
            return SPELL_FAILED_ALREADY_HAVE_SUMMON;

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_dru_force_of_nature::CheckCast);
    }
};

// 33597, 33599, 33956 - Dreamstate
class spell_dru_dreamstate : public AuraScript
{
    PrepareAuraScript(spell_dru_dreamstate);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* target = GetTarget();
        uint32 const missing = target->GetMaxPower(POWER_MANA) - target->GetPower(POWER_MANA);
        if (!missing)
            return;

        target->EnergizeBySpell(target, GetId(), CalculatePct(missing, aurEff->GetAmount()), POWER_MANA);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_dru_dreamstate::HandlePeriodic, EFFECT_1,
                                                  SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 29166 - Innervate - Dreamstate r3's "casting Innervate on another player also grants yourself
// Innervate" bonus
class spell_dru_dreamstate_innervate : public SpellScript
{
    PrepareSpellScript(spell_dru_dreamstate_innervate);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        if (caster->HasAura(Druid::TALENT_DREAMSTATE_R3) && GetHitUnit() != caster)
            caster->CastSpell(caster, Druid::SPELL_INNERVATE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_dreamstate_innervate::HandleAfterHit);
    }
};

// 42231 - Hurricane (tick) - Gale Winds ramp (talent table 8,3)
class spell_dru_hurricane_tick : public SpellScript
{
    PrepareSpellScript(spell_dru_hurricane_tick);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_GALE_WINDS_STACK });
    }

    void HandleAfterHit()
    {
        if (GetHitDamage() > 0)
            _dealtDamage = true;
    }

    // Runs after every target of this tick has been processed - one stack per tick, not per
    // target, and a tick's own targets never see its own stack (BALANCE.md §7 "Hurricane ramp").
    void HandleAfterCast()
    {
        if (!_dealtDamage)
            return;

        Unit* caster = GetCaster();
        if (caster->HasAura(Druid::TALENT_GALE_WINDS_R2))
            caster->CastSpell(caster, Druid::SPELL_GALE_WINDS_STACK, true);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_hurricane_tick::HandleAfterHit);
        AfterCast += SpellCastFn(spell_dru_hurricane_tick::HandleAfterCast);
    }

private:
    bool _dealtDamage = false;
};

// 16914 - Hurricane (channel) - clears Gale Winds stacks when the channel starts or ends, so
// stacks never carry into a recast
class spell_dru_hurricane_channel : public AuraScript
{
    PrepareAuraScript(spell_dru_hurricane_channel);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_GALE_WINDS_STACK });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(Druid::SPELL_GALE_WINDS_STACK);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(Druid::SPELL_GALE_WINDS_STACK);
    }

    void Register() override
    {
        OnEffectApply += AuraEffectApplyFn(spell_dru_hurricane_channel::HandleApply, EFFECT_2,
                                            SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_hurricane_channel::HandleRemove, EFFECT_2,
                                                 SPELL_AURA_PERIODIC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }
};

// 48389, 48392, 48393 - Owlkin Frenzy (talent table 7,0). The native
// SPELL_AURA_PROC_TRIGGER_SPELL_WITH_VALUE effect (eff1) already handles casting 48391 with
// BP0 = this aura's own amount - this script only needs to gate CheckProc.
class spell_dru_owlkin_frenzy_proc : public AuraScript
{
    PrepareAuraScript(spell_dru_owlkin_frenzy_proc);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // GetTarget() (the aura's own owner), not eventInfo.GetActor() - on the melee-taken
        // branch below, GetActor() returns the *attacker*, not the Moonkin druid this aura is
        // on (Unit::TriggerAurasProcOnEvent always passes the instigator as "actor", even for
        // the target-side ProcEventInfo). Code review caught this: against an NPC attacker,
        // actor->ToPlayer() was null and the 30% melee proc never fired in PvE.
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return false;

        float const procChanceMult = 1.0f + player->GetProcChancePercentage() / 100.0f;

        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG)
        {
            // One roll per cast - reject the same DONE event seen again at the hit phase.
            if (!(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST))
                return false;

            SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
            if (!spellInfo || !(spellInfo->GetSchoolMask() & (SPELL_SCHOOL_MASK_ARCANE | SPELL_SCHOOL_MASK_NATURE)))
                return false;

            if (!Druid::IsDirectDamageCast(spellInfo))
                return false;

            return roll_chance_f(10.0f * procChanceMult);
        }

        // Melee-taken branch.
        return roll_chance_f(30.0f * procChanceMult);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_owlkin_frenzy_proc::CheckProc);
    }
};

// 200343 - Vengeful Soul (Vengeance r3 capstone buff, talent table 6,3)
class spell_dru_vengeful_soul : public AuraScript
{
    PrepareAuraScript(spell_dru_vengeful_soul);

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        // A refresh never fires this - only the buff's own 12 s expiry does.
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;

        Unit* target = GetTarget();
        uint32 const missing = target->GetMaxPower(POWER_MANA) - target->GetPower(POWER_MANA);
        if (!missing)
            return;

        target->EnergizeBySpell(target, aurEff->GetId(), CalculatePct(missing, 10), POWER_MANA);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_dru_vengeful_soul::HandleRemove, EFFECT_0,
                                                 SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, AURA_EFFECT_HANDLE_REAL);
    }
};

// 5176 - Wrath - Wrath of Cenarius r3 capstone (talent table 7,2)
class spell_dru_wrath_of_cenarius_capstone : public SpellScript
{
    PrepareSpellScript(spell_dru_wrath_of_cenarius_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Druid::SPELL_SOLAR_BEAM });
    }

    void HandleAfterHit()
    {
        if (GetHitDamage() <= 0)
            return;

        Player* caster = GetCaster()->ToPlayer();
        if (!caster || !caster->HasAura(Druid::TALENT_WRATH_OF_CENARIUS_R3))
            return;

        Druid::ReduceSpellCooldown(caster, Druid::SPELL_SOLAR_BEAM, 1000);

        // Extends Nature's Grace's buff (16886) by 0.5 s, no cap (BALANCE.md §12.17: "each Wrath
        // adds 0.5 s and a Wrath takes at least 1 s of GCD, so it can't grow without bound").
        if (Aura* naturesGrace = caster->GetAura(Druid::SPELL_NATURES_GRACE_BUFF))
        {
            int32 const newDuration = naturesGrace->GetDuration() + 500;
            if (naturesGrace->GetMaxDuration() < newDuration)
                naturesGrace->SetMaxDuration(newDuration);
            naturesGrace->SetDuration(newDuration);
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_dru_wrath_of_cenarius_capstone::HandleAfterHit);
    }
};

// 200344-200347 - Astral Surge (3 stacking slots) and Balance of Power - CORE-AUDIT row 6 /
// BALANCE.md corrections item 2 (supersedes the dropped Druid::ApplySpellPowerMultipliers core
// hook talent table rows 5,1/5,2 originally called for). Each buff's flat spell-power/healing-
// power amount is computed once, at the moment the buff is cast, from "the configured percent"
// already stored on that effect (its own DBC base value, or - for 200347's damage effect - the
// BP0 the caster's Balance of Power rank passed in at cast time, spell_dru_eclipse_balance's
// HandleProc above) times caster->SpellBaseDamageBonusDone()/SpellBaseHealingBonusDone() for that
// effect's own school mask (72 Astral for the three Astral Surge slots, 126 all-magic for Balance
// of Power - read directly off each effect's MiscValue rather than hardcoded, so one class serves
// both). canBeRecalculated = false: PLAN's accepted deviation is that SP gained while the buff is
// already up isn't multiplied (CORE-AUDIT row 6's evidence column).
class spell_dru_astral_surge_sp : public AuraScript
{
    PrepareAuraScript(spell_dru_astral_surge_sp);

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
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_astral_surge_sp::CalculateDamageAmount, EFFECT_0,
                                                      SPELL_AURA_MOD_DAMAGE_DONE);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_astral_surge_sp::CalculateHealingAmount, EFFECT_1,
                                                      SPELL_AURA_MOD_HEALING_DONE);
    }
};

/*
 * Corrected class names (WP-B brief "Corrections to BALANCE.md" item 3) - new classes replacing
 * stock spell_druid.cpp behaviour, rebound by WP-A's SQL. spell_druid.cpp is never edited.
 */

// -48516 - Eclipse (rewrite of stock spell_dru_eclipse; CORE-AUDIT §3 item 10, BALANCE.md §7
// "Eclipse")
class spell_dru_eclipse_balance : public AuraScript
{
    PrepareAuraScript(spell_dru_eclipse_balance);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            { Druid::SPELL_ECLIPSE_SOLAR, Druid::SPELL_ECLIPSE_LUNAR, Druid::SPELL_BALANCE_OF_POWER_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = GetTarget();
        if (!target->IsPlayer())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        // Checked by id, not family flag - the Starfire cleave (200337) deliberately shares
        // Starfire's bit and must not proc this.
        bool const isStarfire = spellInfo->Id == Druid::SPELL_STARFIRE;
        bool const isWrath = spellInfo->Id == Druid::SPELL_WRATH;
        if (!isStarfire && !isWrath)
            return false;

        uint32 const now = GameTime::GetGameTimeMS().count();
        if (isStarfire && _solarIcdEnd > now)
            return false;
        if (isWrath && _lunarIcdEnd > now)
            return false;

        // Fail if either Eclipse side is already up. Celestial Alignment is not checked.
        if (target->HasAura(Druid::SPELL_ECLIPSE_SOLAR) || target->HasAura(Druid::SPELL_ECLIPSE_LUNAR))
            return false;

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        bool const isStarfire = spellInfo->Id == Druid::SPELL_STARFIRE;
        uint32 const triggeredSpell = isStarfire ? Druid::SPELL_ECLIPSE_SOLAR : Druid::SPELL_ECLIPSE_LUNAR;

        Unit* target = GetTarget();
        target->CastCustomSpell(triggeredSpell, SPELLVALUE_BASE_POINT0, aurEff->GetAmount(), target,
                                 TRIGGERED_FULL_MASK);

        uint32 const now = GameTime::GetGameTimeMS().count();
        if (isStarfire)
            _solarIcdEnd = now + 30000;
        else
            _lunarIcdEnd = now + 30000;

        // Balance of Power capstone (talent table 5,2): both effects (EFFECT_0 damage,
        // EFFECT_1 healing) get the talent rank's own amount - a single-mod CastCustomSpell
        // call only overrides EFFECT_0 and leaves EFFECT_1 at its static DBC value, so this
        // needs both SPELLVALUE_BASE_POINT0 and _BASE_POINT1 set together (code review caught
        // the healing side silently never scaling). Only one rank is ever active at a time.
        Player* player = target->ToPlayer();
        AuraEffect const* bop = player->GetAuraEffect(Druid::TALENT_BALANCE_OF_POWER_R2, EFFECT_0);
        if (!bop)
            bop = player->GetAuraEffect(Druid::TALENT_BALANCE_OF_POWER_R1, EFFECT_0);

        if (bop)
        {
            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT0, bop->GetAmount());
            values.AddSpellMod(SPELLVALUE_BASE_POINT1, bop->GetAmount());
            target->CastCustomSpell(Druid::SPELL_BALANCE_OF_POWER_BUFF, values, target, TRIGGERED_FULL_MASK);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_eclipse_balance::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dru_eclipse_balance::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

private:
    uint32 _solarIcdEnd = 0;
    uint32 _lunarIcdEnd = 0;
};

// 24905 - Moonkin Form (mana-on-cast proc) - rewrite of stock spell_dru_moonkin_form_passive_proc
class spell_dru_moonkin_form_proc_balance : public AuraScript
{
    PrepareAuraScript(spell_dru_moonkin_form_proc_balance);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return Druid::IsDirectDamageCast(eventInfo.GetSpellInfo());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dru_moonkin_form_proc_balance::CheckProc);
    }
};

// 50419 - Brambles (summoned treant's damage bonus) - rewrite of stock spell_dru_brambles_treant.
// Brambles' old "steal Barkskin's chance-of-success amount" hack is gone now that eff3 no longer
// reuses CHANCE_OF_SUCCESS (talent table 4,3); the treant's bonus is read directly off Brambles'
// own eff2 (EFFECT_1), which is now a plain DUMMY value (BALANCE.md corrections item 3).
class spell_dru_brambles_treant_balance : public AuraScript
{
    PrepareAuraScript(spell_dru_brambles_treant_balance);

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        // Always fails - removes the stock daze proc entirely (BALANCE.md §10).
        return false;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // Mirrors stock spell_dru_brambles_treant's own comment: GetOwner() (and
        // GetSpellModOwner()) return null at this point - the addon aura applies during early
        // summoning, before TempSummon::InitStats has set the generic owner field. The
        // TempSummon-specific summoner field is set earlier and is what's actually valid here
        // (code review caught the regression to the plain GetOwner() call).
        if (!GetUnitOwner()->IsSummon())
            return;

        Unit* owner = GetUnitOwner()->ToTempSummon()->GetSummonerUnit();
        if (!owner)
            return;

        static constexpr std::array<uint32, 3> bramblesRanks = { 16836, 16839, 16840 };
        for (uint32 rank : bramblesRanks)
        {
            if (AuraEffect const* brambles = owner->GetAuraEffect(rank, EFFECT_1))
            {
                amount = brambles->GetAmount();
                break;
            }
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_brambles_treant_balance::CalculateAmount, EFFECT_0,
                                                      SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        DoCheckProc += AuraCheckProcFn(spell_dru_brambles_treant_balance::CheckProc);
    }
};

/* 35669 - Serverside - Druid Pet Scaling 01
   35670 - Serverside - Druid Pet Scaling 02
   35671 - Serverside - Druid Pet Scaling 03
   35672 - Serverside - Druid Pet Scaling 04
   Rewrite of stock spell_dru_treant_scaling minus the Brambles AP clause that read icon 53 eff 2
   (BALANCE.md §10/corrections item 3) - everything else ported verbatim from the stock class. */
class spell_dru_treant_scaling_balance : public AuraScript
{
    PrepareAuraScript(spell_dru_treant_scaling_balance);

    void CalculateResistanceAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: treant inherits 40% of resistance from owner and 35% of armor (guessed)
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            SpellSchoolMask schoolMask =
                SpellSchoolMask(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            int32 modifier = schoolMask == SPELL_SCHOOL_MASK_NORMAL ? 35 : 40;
            amount = CalculatePct(std::max<int32>(0, owner->GetResistance(schoolMask)), modifier);
        }
    }

    void CalculateStatAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: treant inherits 30% of intellect / stamina (guessed)
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            Stats stat = Stats(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            amount = CalculatePct(std::max<int32>(0, owner->GetStat(stat)), 30);
        }
    }

    void CalculateAPAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: treant inherits 105% of SP as AP - 15% of damage increase per hit
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            int32 nature = owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_NATURE);
            amount = CalculatePct(std::max<int32>(0, nature), 105);
        }
    }

    void CalculateSPAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: treant inherits 15% of SP
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            int32 nature = owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_NATURE);
            amount = CalculatePct(std::max<int32>(0, nature), 15);

            // xinef: Update appropriate player field
            if (owner->IsPlayer())
                owner->SetUInt32Value(PLAYER_PET_SPELL_POWER, (uint32)amount);
        }
    }

    void HandleEffectApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, aurEff->GetAuraType(), true, SPELL_BLOCK_TYPE_POSITIVE);
        if (aurEff->GetAuraType() == SPELL_AURA_MOD_ATTACK_POWER)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_ATTACK_POWER_PCT, true,
                                              SPELL_BLOCK_TYPE_POSITIVE);
        else if (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE, true,
                                              SPELL_BLOCK_TYPE_POSITIVE);
    }

    void Register() override
    {
        if (m_scriptSpellId != 35669)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_treant_scaling_balance::CalculateResistanceAmount,
                                                          EFFECT_ALL, SPELL_AURA_MOD_RESISTANCE);

        if (m_scriptSpellId == 35669 || m_scriptSpellId == 35670)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_treant_scaling_balance::CalculateStatAmount,
                                                          EFFECT_ALL, SPELL_AURA_MOD_STAT);

        if (m_scriptSpellId == 35669)
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_treant_scaling_balance::CalculateAPAmount,
                                                          EFFECT_ALL, SPELL_AURA_MOD_ATTACK_POWER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dru_treant_scaling_balance::CalculateSPAmount,
                                                          EFFECT_ALL, SPELL_AURA_MOD_DAMAGE_DONE);
        }

        OnEffectApply += AuraEffectApplyFn(spell_dru_treant_scaling_balance::HandleEffectApply, EFFECT_ALL,
                                            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_druid_balance_spell_scripts()
{
    RegisterSpellScript(spell_dru_starfire_cleave);
    RegisterSpellScript(spell_dru_starsurge);
    RegisterSpellAndAuraScriptPair(spell_dru_fury_of_elune, spell_dru_fury_of_elune_aura);
    RegisterSpellScript(spell_dru_improved_moonfire_capstone);
    RegisterSpellScript(spell_dru_natures_reach_moonfire_spread);
    RegisterSpellScript(spell_dru_insect_swarm_cast);
    RegisterSpellScript(spell_dru_swarming_rot);
    RegisterSpellScript(spell_dru_brambles_silence);
    RegisterSpellScript(spell_dru_force_of_nature);
    RegisterSpellScript(spell_dru_dreamstate);
    RegisterSpellScript(spell_dru_dreamstate_innervate);
    RegisterSpellScript(spell_dru_hurricane_tick);
    RegisterSpellScript(spell_dru_hurricane_channel);
    RegisterSpellScript(spell_dru_owlkin_frenzy_proc);
    RegisterSpellScript(spell_dru_vengeful_soul);
    RegisterSpellScript(spell_dru_wrath_of_cenarius_capstone);
    RegisterSpellScript(spell_dru_astral_surge_sp);

    // Corrected-name rewrites of stock spell_druid.cpp classes (see the header comment above).
    RegisterSpellScript(spell_dru_eclipse_balance);
    RegisterSpellScript(spell_dru_moonkin_form_proc_balance);
    RegisterSpellScript(spell_dru_brambles_treant_balance);
    RegisterSpellScript(spell_dru_treant_scaling_balance);
}
