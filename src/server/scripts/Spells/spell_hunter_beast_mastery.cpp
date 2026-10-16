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
 * Hunter rework - Beast Mastery spell scripts (hunter-rework.SHARED.md §A4 / §C4, BEAST-MASTERY.md §4, S1a-HANDOFF
 * A1, A3-A7). Ids come from HunterData:: (long names where a short stem lost, L11) and the Hunter:: aliases in
 * HunterMechanics.h; stock ids the hunter DSL never declares stay hand literals.
 */

#include "HunterMechanics.h"
#include "Log.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <cmath>
#include <list>
#include <vector>

namespace
{
    // The hunter Player behind `unit` (the unit itself, or the owner of its pet/guardian), nullptr otherwise.
    Player* GetOwningHunter(Unit* unit)
    {
        Player* player = Hunter::GetOwningPlayer(unit);
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    // Gives every live Stampede beast the owner controls `spellId` with the given remaining duration. S1b summons
    // the beasts; until then GetPassthroughKind never returns StampedeBeast and this is a no-op.
    void ApplyToStampedeBeasts(Player* owner, uint32 spellId, int32 duration)
    {
        for (Unit* unit : owner->m_Controlled)
        {
            if (!unit || !unit->IsAlive() ||
                Hunter::GetPassthroughKind(owner, unit) != Hunter::PassthroughKind::StampedeBeast)
                continue;

            if (Aura* aura = owner->AddAura(spellId, unit))
                aura->SetDuration(duration);
        }
    }
}

// 201800 Command I, 201801 Command II - the hunter presses, the pet casts its family's commanded spell (A1)
class spell_hun_command : public SpellScript
{
    PrepareSpellScript(spell_hun_command);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_LUNGE_COMMAND, HunterData::SPELL_RIP_THROAT_COMMAND,
            HunterData::SPELL_RAKE_COMMAND, HunterData::SPELL_POUNCE_COMMAND, HunterData::SPELL_SAVAGE_REND_COMMAND,
            HunterData::SPELL_LEAPING_TEAR_COMMAND, HunterData::SPELL_SWIPE_COMMAND, HunterData::SPELL_MAUL_COMMAND,
            HunterData::SPELL_VENOM_BITE_COMMAND, HunterData::SPELL_VENOMOUS_CLOUD_COMMAND,
            HunterData::SPELL_SAVAGE_STRIKES_COMMAND, HunterData::SPELL_SAVAGE_POUNCE_COMMAND,
            HunterData::SPELL_THRASH_COMMAND, HunterData::SPELL_CRUSHING_BLOW_COMMAND,
            HunterData::SPELL_FEINT_STRIKE_COMMAND, HunterData::SPELL_AMBUSH_COMMAND });
    }

    uint8 GetSlot()
    {
        return GetSpellInfo()->Id == HunterData::SPELL_COMMAND_II ? 1 : 0;
    }

    SpellCastResult CheckCast()
    {
        // CR3: only a hunter Player acts
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return SPELL_CAST_OK;

        // B16: GetCommandSpell must never see a null pet
        Pet* pet = player->GetPet();
        if (!pet)
            return SPELL_FAILED_NO_PET;

        uint32 const cmd = Hunter::GetCommandSpell(pet, GetSlot());
        SpellInfo const* cmdInfo = cmd ? sSpellMgr->GetSpellInfo(cmd) : nullptr;
        if (!cmdInfo)
        {
            LOG_ERROR("scripts.hunter", "Command {}: no commanded spell for pet {} (slot {}, command id {})",
                GetSpellInfo()->Id, pet->GetEntry(), uint32(GetSlot()), cmd);
            return SPELL_FAILED_NO_PET;
        }

        return Hunter::CheckPetCanAct(player, GetExplTargetUnit(), cmdInfo);
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        Pet* pet = player->GetPet();
        Unit* target = GetHitUnit();
        if (!pet || !target || !pet->IsAlive() || !target->IsAlive())
            return;

        uint32 const cmd = Hunter::GetCommandSpell(pet, GetSlot());
        if (!cmd)
            return;

        // L6: the target may have died or turned friendly since the cast started
        if (!pet->IsValidAttackTarget(target))
            return;

        pet->CastSpell(target, cmd, TRIGGERED_FULL_MASK);
        Hunter::CommandPetAttack(pet, target);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_hun_command::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_hun_command::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 201726 Swipe (command), 201736 Venomous Cloud splash - the splash never re-hits the primary target (A3).
// The area target is eff1 on 201726 and eff0 on 201736, so the hook sits on EFFECT_ALL.
class spell_hun_command_splash : public SpellScript
{
    PrepareSpellScript(spell_hun_command_splash);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        if (!GetOwningHunter(GetCaster()))
            return;

        Unit* primary = GetExplTargetUnit();
        if (!primary)
            return;

        targets.remove_if([primary](WorldObject* obj)
        {
            return obj == primary;
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_command_splash::FilterTargets, EFFECT_ALL,
            TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 201726 Swipe (command), eff1 - the 8 yd splash takes a share of the primary's amount (eff0 is untouched)
class spell_hun_swipe_command_splash : public SpellScript
{
    PrepareSpellScript(spell_hun_swipe_command_splash);

    void HandleSplashDamage(SpellEffIndex /*effIndex*/)
    {
        if (!GetOwningHunter(GetCaster()))
            return;

        SetHitDamage(CalculatePct(GetHitDamage(), HunterData::SWIPE_SPLASH_PCT));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_hun_swipe_command_splash::HandleSplashDamage, EFFECT_1,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 34026 Kill Command (second class; PET's spell_hun_kill_command_rework stays) - Bestial Wrath cut, Spiked Collar
// extras, Beast Cleave copy (A4)
class spell_hun_kill_command_bm : public SpellScript
{
    PrepareSpellScript(spell_hun_kill_command_bm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_BESTIAL_WRATH, HunterData::SPELL_SPIKED_COLLAR_STRIKE,
            HunterData::SPELL_BEAST_CLEAVE_BUFF, HunterData::SPELL_BEAST_CLEAVE_STRIKE,
            HunterData::SPELL_SPIKED_COLLAR_201829 });
    }

    // Once per cast (L9)
    void HandleAfterCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        Hunter::ReduceSpellCooldown(player, Hunter::SPELL_BESTIAL_WRATH, HunterData::KILL_COMMAND_BW_REDUCTION_MS);
    }

    // Casts `strikeId` from the hunter at every enemy around `target`, each for `pct` percent of `damage`
    static void CopyHit(Player* player, Unit* target, uint32 strikeId, int32 damage, int32 pct, float radius,
        uint32 maxTargets)
    {
        std::vector<Unit*> targets;
        Hunter::CollectBmSplashTargets(player, player, target, radius, maxTargets, targets);
        for (Unit* extra : targets)
            player->CastCustomSpell(strikeId, SPELLVALUE_BASE_POINT0, CalculatePct(damage, pct), extra,
                TRIGGERED_FULL_MASK);
    }

    void HandleAfterHit()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        // the final amount (BM §0 contradiction 2)
        int32 const damage = GetHitDamage();
        Unit* target = GetHitUnit();
        if (damage <= 0 || !target)
            return;

        // Spiked Collar 3/3: the share is read from the rank spell (L10)
        if (player->HasAura(HunterData::SPELL_SPIKED_COLLAR_201829))
        {
            int32 const pct = sSpellMgr->AssertSpellInfo(HunterData::SPELL_SPIKED_COLLAR_201829)
                ->Effects[EFFECT_1].CalcValue(player);
            CopyHit(player, target, HunterData::SPELL_SPIKED_COLLAR_STRIKE, damage, pct,
                HunterData::SPIKED_COLLAR_RADIUS_YD, HunterData::SPIKED_COLLAR_MAX_TARGETS);
        }

        // Beast Cleave: the hunter's marker has no eff1, the share lives on the helper's SpellInfo (B5). The Spiked
        // Collar extras above are separate casts and are never copied.
        if (player->HasAura(HunterData::SPELL_BEAST_CLEAVE_BUFF))
        {
            int32 const pct = sSpellMgr->AssertSpellInfo(HunterData::SPELL_BEAST_CLEAVE_BUFF)
                ->Effects[EFFECT_1].CalcValue(player);
            CopyHit(player, target, HunterData::SPELL_BEAST_CLEAVE_STRIKE, damage, pct,
                HunterData::BEAST_CLEAVE_RADIUS_YD, 0);
        }
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_hun_kill_command_bm::HandleAfterCast);
        AfterHit += SpellHitFn(spell_hun_kill_command_bm::HandleAfterHit);
    }
};

// 201806 Beast Cleave - the pet's (and, from S1b, the beasts') copy splashes its hits (A5)
class spell_hun_beast_cleave : public AuraScript
{
    PrepareAuraScript(spell_hun_beast_cleave);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_BEAST_CLEAVE_STRIKE });
    }

    // A gate that decides "no copy" lives here, so no internal cooldown starts on a no-op (L6)
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || owner->IsPlayer() || !GetOwningHunter(owner))
            return false;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || damageInfo->GetDamage() == 0 || !eventInfo.GetActionTarget())
            return false;

        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC)
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return !spellInfo || !Hunter::IsBeastCleaveExcluded(spellInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* actor = eventInfo.GetActor();
        Unit* victim = eventInfo.GetActionTarget();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        Player* hunter = GetOwningHunter(actor);
        if (!actor || !victim || !damageInfo || !hunter)
            return;

        int32 const damage = int32(damageInfo->GetDamage());
        int32 const share = aurEff->GetAmount();
        if (damage <= 0 || share <= 0)
            return;

        std::vector<Unit*> targets;
        Hunter::CollectBmSplashTargets(hunter, actor, victim, HunterData::BEAST_CLEAVE_RADIUS_YD, 0, targets);
        for (Unit* extra : targets)
            actor->CastCustomSpell(HunterData::SPELL_BEAST_CLEAVE_STRIKE, SPELLVALUE_BASE_POINT0,
                CalculatePct(damage, share), extra, TRIGGERED_FULL_MASK);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // B5: AddAura gives a beast both effects; unguarded, every copy would re-add to every beast forever
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        Player* player = owner->ToPlayer();
        if (player->getClass() != CLASS_HUNTER)
            return;

        ApplyToStampedeBeasts(player, HunterData::SPELL_BEAST_CLEAVE_BUFF, GetAura()->GetDuration());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_beast_cleave::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_beast_cleave::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_hun_beast_cleave::HandleApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
    }
};

// 19574 Bestial Wrath (the stock spell_hun_bestial_wrath SpellScript stays bound) - The Beast Within and the
// Stampede beasts' copies (A6)
class spell_hun_bestial_wrath_bm : public AuraScript
{
    PrepareAuraScript(spell_hun_bestial_wrath_bm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_THE_BEAST_WITHIN, HunterData::SPELL_THE_BEAST_WITHIN_201855,
            HunterData::SPELL_THE_BEAST_WITHIN_201856, HunterData::SPELL_THE_BEAST_WITHIN_201857 });
    }

    // The hunter whose real pet carries this aura (a beast's copy is skipped, so no recursion), else nullptr
    Player* GetRealPetOwner() const
    {
        Unit* caster = GetCaster();
        Player* owner = caster ? caster->ToPlayer() : nullptr;
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return nullptr;

        Unit* target = GetUnitOwner();
        return target && owner->GetPet() == target ? owner : nullptr;
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* owner = GetRealPetOwner();
        if (!owner)
            return;

        // The Beast Within: the highest known rank (5/10/15), read from the rank spell (L10)
        for (uint32 rank : { HunterData::SPELL_THE_BEAST_WITHIN_201857, HunterData::SPELL_THE_BEAST_WITHIN_201856,
                 HunterData::SPELL_THE_BEAST_WITHIN_201855 })
        {
            if (!owner->HasAura(rank))
                continue;

            int32 const amount = sSpellMgr->AssertSpellInfo(rank)->Effects[EFFECT_0].CalcValue(owner);
            owner->CastCustomSpell(HunterData::SPELL_THE_BEAST_WITHIN, SPELLVALUE_BASE_POINT1, amount, owner,
                TRIGGERED_FULL_MASK);
            break;
        }

        ApplyToStampedeBeasts(owner, Hunter::SPELL_BESTIAL_WRATH, GetAura()->GetDuration());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* owner = GetRealPetOwner();
        if (!owner)
            return;

        // dispelled, cancelled or killed: The Beast Within goes with it; a natural expiry lets both end together
        AuraApplication const* application = GetTargetApplication();
        if (application && application->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            owner->RemoveAurasDueToSpell(HunterData::SPELL_THE_BEAST_WITHIN);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_hun_bestial_wrath_bm::HandleApply, EFFECT_1,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_bestial_wrath_bm::HandleRemove, EFFECT_1,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, AURA_EFFECT_HANDLE_REAL);
    }
};

// 201812 The Beast Within (Mastery) - Kill Command gains Mastery % damage, refreshed every second (A7)
class spell_hun_tbw_mastery : public AuraScript
{
    PrepareAuraScript(spell_hun_tbw_mastery);

    static int32 GetMasteryAmount(Unit const* owner)
    {
        Player const* player = owner ? owner->ToPlayer() : nullptr;
        return player ? int32(std::lround(player->GetMasteryPercentage())) : 0;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        amount = GetMasteryAmount(owner);
        canBeRecalculated = true;
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        AuraEffect* modEffect = GetEffect(EFFECT_0);
        if (!modEffect || modEffect->GetAuraType() != SPELL_AURA_ADD_PCT_MODIFIER)
            return;

        // Changing the amount re-sends the spell mod to the client, so only do it when the rounded value moved
        int32 const amount = GetMasteryAmount(owner);
        if (amount != modEffect->GetAmount())
            modEffect->ChangeAmount(amount, false);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_hun_tbw_mastery::CalculateAmount, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_tbw_mastery::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

void AddSC_hunter_beast_mastery_spell_scripts()
{
    RegisterSpellScript(spell_hun_command);
    RegisterSpellScript(spell_hun_command_splash);
    RegisterSpellScript(spell_hun_swipe_command_splash);
    RegisterSpellScript(spell_hun_kill_command_bm);
    RegisterSpellScript(spell_hun_beast_cleave);
    RegisterSpellScript(spell_hun_bestial_wrath_bm);
    RegisterSpellScript(spell_hun_tbw_mastery);
}
