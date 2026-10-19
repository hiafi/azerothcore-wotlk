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
 * A1, A3-A7, S1b-HANDOFF B1-B4, B6). Ids come from HunterData:: (long names where a short stem lost, L11) and the
 * Hunter:: aliases in HunterMechanics.h; stock ids the hunter DSL never declares stay named constants below.
 */

#include "CreatureAI.h"
#include "DBCStores.h"
#include "GridDefines.h"
#include "HunterMechanics.h"
#include "Log.h"
#include "Map.h"
#include "ObjectMgr.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "WorldPacket.h"
#include <array>
#include <cmath>
#include <initializer_list>
#include <list>
#include <vector>

namespace
{
    // Stock ids the hunter DSL never declares (no HunterData:: name)
    constexpr uint32 SPELL_REPLENISHMENT = 57669;              // stock Replenishment (spell_gen_replenishment)

    // _masks.py PET_BASIC_ATTACK: d2 b23, every pet basic attack (Culling the Herd reads it)
    constexpr uint32 FAMILY_FLAG2_PET_BASIC_ATTACK = 0x800000;

    // Stampede guardians (BEAST-MASTERY §4.6), the generated creature_template names (review m6)
    constexpr std::array<uint32, 8> STAMPEDE_BEAST_ENTRIES = { HunterData::NPC_STAMPEDING_WOLF,
        HunterData::NPC_STAMPEDING_CAT, HunterData::NPC_STAMPEDING_RAPTOR, HunterData::NPC_STAMPEDING_BEAR,
        HunterData::NPC_STAMPEDING_SPIDER, HunterData::NPC_STAMPEDING_BEAST_FEROCITY,
        HunterData::NPC_STAMPEDING_BEAST_TENACITY, HunterData::NPC_STAMPEDING_BEAST_CUNNING };

    // The rank of `ranks` (listed highest first) that `player` knows, else 0. Every BM rank is a passive with aura
    // effects, so ownership is HasAura (L10).
    uint32 GetKnownRank(Player const* player, std::initializer_list<uint32> ranks)
    {
        for (uint32 rank : ranks)
            if (player->HasAura(rank))
                return rank;

        return 0;
    }

    // EFFECT_0 of the known rank of `ranks`, read from its SpellInfo (L10); 0 when no rank is known
    int32 GetKnownRankValue(Player const* player, std::initializer_list<uint32> ranks)
    {
        uint32 const rank = GetKnownRank(player, ranks);
        return rank ? sSpellMgr->AssertSpellInfo(rank)->Effects[EFFECT_0].CalcValue(player) : 0;
    }

    // The hunter Player behind `unit` (the unit itself, or the owner of its pet/guardian), nullptr otherwise.
    Player* GetOwningHunter(Unit* unit)
    {
        Player* player = Hunter::GetOwningPlayer(unit);
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    // Gives every live Stampede beast the owner controls `spellId` with the given remaining duration. Walks a copy
    // of m_Controlled, because AddAura runs aura hooks that may touch the owner's controlled set (S1b decision 8).
    void ApplyToStampedeBeasts(Player* owner, uint32 spellId, int32 duration)
    {
        std::vector<Unit*> const controlled(owner->m_Controlled.begin(), owner->m_Controlled.end());
        for (Unit* unit : controlled)
        {
            // an unsummoned beast stays a valid pointer until its deferred delete, so check it is still in world
            if (!unit || !unit->IsInWorld() || !unit->IsAlive() ||
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

        // S1a-5: the press passed CheckPetCanAct, but the triggered pet cast re-checks range strictly (melee reach),
        // so it can still fail at the edge of melee range; log it where the playtest can see it (L17)
        SpellCastResult const result = pet->CastSpell(target, cmd, TRIGGERED_FULL_MASK);
        if (result != SPELL_CAST_OK)
            LOG_ERROR("scripts.hunter", "Command {}: pet {} failed to cast commanded spell {} on {} (result {})",
                GetSpellInfo()->Id, pet->GetEntry(), cmd, target->GetGUID().ToString(), uint32(result));

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

        // The Beast Within: the highest known rank (5/10/15), read from the rank spell (L10). S1a-4: it lasts as long
        // as Bestial Wrath has left, so a pet_aura reload on resummon doesn't restart it at full duration.
        // An AuraDuration of 0 means "the DBC duration" (Spell.cpp), so a spent Bestial Wrath casts nothing.
        int32 const duration = GetAura()->GetDuration();
        for (uint32 rank : { HunterData::SPELL_THE_BEAST_WITHIN_201857, HunterData::SPELL_THE_BEAST_WITHIN_201856,
                 HunterData::SPELL_THE_BEAST_WITHIN_201855 })
        {
            if (duration == 0)
                break;

            if (!owner->HasAura(rank))
                continue;

            int32 const amount = sSpellMgr->AssertSpellInfo(rank)->Effects[EFFECT_0].CalcValue(owner);
            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT1, amount);
            values.AddSpellMod(SPELLVALUE_AURA_DURATION, duration);
            owner->CastCustomSpell(HunterData::SPELL_THE_BEAST_WITHIN, values, owner, TRIGGERED_FULL_MASK);
            break;
        }

        if (duration != 0)
            ApplyToStampedeBeasts(owner, Hunter::SPELL_BESTIAL_WRATH, duration);
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

// 34466/34467/34468 Serpent's Swiftness - Steady Shot's Nature hit, and at
// Serpent's Swiftness 3/3 a Kill Command cut per Steady Shot cast (S1b B1, BEAST-MASTERY §4.2, §7.1). Every bound
// rank has eff0 aura DUMMY. 34468's spell_proc row has phase 0x3 (CAST + HIT), the others 0x2 (HIT), so the two
// branches are told apart by the event's phase in both hooks (L9).
class spell_hun_steady_shot_nature : public AuraScript
{
    PrepareAuraScript(spell_hun_steady_shot_nature);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_STEADY_SHOT, HunterData::SPELL_KILL_COMMAND,
            HunterData::SPELL_STEADY_SHOT_NATURE, HunterData::SPELL_SERPENT_S_SWIFTNESS,
            HunterData::SPELL_SERPENT_S_SWIFTNESS_34467, HunterData::SPELL_SERPENT_S_SWIFTNESS_34468 });
    }

    Player* GetHunter() const
    {
        Unit* owner = GetUnitOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        return player && player->getClass() == CLASS_HUNTER ? player : nullptr;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->Id != HunterData::SPELL_STEADY_SHOT)
            return false;

        Player* player = GetHunter();
        if (!player)
            return false;

        uint32 const phase = eventInfo.GetSpellPhaseMask();

        // CAST (34468's row only): the Kill Command cut, once per Steady Shot cast; there is no DamageInfo here
        if (phase & PROC_SPELL_PHASE_CAST)
            return GetId() == HunterData::SPELL_SERPENT_S_SWIFTNESS_34468;

        if (phase & PROC_SPELL_PHASE_HIT)
        {
            DamageInfo* damageInfo = eventInfo.GetDamageInfo();
            if (!damageInfo || damageInfo->GetDamage() == 0)
                return false;

            // L6: the "does this proc act" gate lives here, not in the handler (review m4)
            Unit* victim = damageInfo->GetVictim();
            if (!victim || !victim->IsAlive() || !player->IsValidAttackTarget(victim))
                return false;

            return true;
        }

        return false;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetHunter();
        if (!player)
            return;

        uint32 const phase = eventInfo.GetSpellPhaseMask();
        if (phase & PROC_SPELL_PHASE_CAST)
        {
            // 1000 ms, real seconds (34468 eff2, L10)
            int32 const cut = sSpellMgr->AssertSpellInfo(HunterData::SPELL_SERPENT_S_SWIFTNESS_34468)
                ->Effects[EFFECT_2].CalcValue(player);
            if (cut > 0)
                Hunter::ReduceSpellCooldown(player, HunterData::SPELL_KILL_COMMAND, uint32(cut));
            return;
        }

        if (!(phase & PROC_SPELL_PHASE_HIT))
            return;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        Unit* victim = damageInfo ? damageInfo->GetVictim() : nullptr;
        if (!victim || !victim->IsAlive())
            return;

        int32 const pct = GetKnownRankValue(player, { HunterData::SPELL_SERPENT_S_SWIFTNESS_34468,
            HunterData::SPELL_SERPENT_S_SWIFTNESS_34467, HunterData::SPELL_SERPENT_S_SWIFTNESS });
        if (pct <= 0)
            return;

        // The pre-armor figure: damage + cleanDamage (armor loss, block, resilience) + absorb + resist. On a crit the
        // armor came off before the crit doubling (Unit.cpp CalculateSpellDamageTaken), so the armor loss is added
        // once more (B10; exact for a x2 crit, 0-verify 4.3). The block is taken out of that second term, so a
        // blocked crit doesn't count its block twice (review m3); resilience (PvP only) still does.
        uint32 pre = damageInfo->GetUnmitigatedDamage();
        if (eventInfo.GetHitMask() & PROC_HIT_CRITICAL)
        {
            uint32 const notArmor = damageInfo->GetDamage() + damageInfo->GetAbsorb() + damageInfo->GetResist() +
                damageInfo->GetBlock();
            if (pre > notArmor)
                pre += pre - notArmor;
        }

        int32 const damage = CalculatePct(int32(pre), pct);
        if (damage <= 0)
            return;

        player->CastCustomSpell(HunterData::SPELL_STEADY_SHOT_NATURE, SPELLVALUE_BASE_POINT0, damage, victim,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_steady_shot_nature::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_steady_shot_nature::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 53256/53259/53260 Cobra Strikes - a Steady Shot cast (CAST row, 5/10/15% x Proc Chance) resets Arcane Shot only;
// Explosive Shot keeps its shared category entry (S1b B2, BEAST-MASTERY §0.11, §7.1)
class spell_hun_cobra_strikes_bm : public AuraScript
{
    PrepareAuraScript(spell_hun_cobra_strikes_bm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_ARCANE_SHOT });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* owner = GetUnitOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        player->RemoveSpellCooldown(HunterData::SPELL_ARCANE_SHOT, true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_hun_cobra_strikes_bm::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 3044 Arcane Shot (second class; SHARED's spell_hun_shot_mana stays) - Stomp: the pet stomps at the target once per
// Arcane Shot cast, Cobra Strikes resets included, from any pet distance (S1b B3, BEAST-MASTERY §4.7)
class spell_hun_arcane_shot_bm : public SpellScript
{
    PrepareSpellScript(spell_hun_arcane_shot_bm);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_STOMP_PET, HunterData::SPELL_STOMP_TALENT });
    }

    void HandleAfterCast()
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player || player->getClass() != CLASS_HUNTER || !player->HasAura(HunterData::SPELL_STOMP_TALENT))
            return;

        Pet* pet = player->GetPet();
        Unit* target = GetExplTargetUnit();
        if (!pet || !target || !target->IsAlive())
            return;

        // Kill Command's rule: no pet range, the stomp lands at the target. CheckPetCanAct ignores the target when
        // petSpell is null, so the hostility check is our own (L6)
        if (Hunter::CheckPetCanAct(player, target, nullptr) != SPELL_CAST_OK || !pet->IsValidAttackTarget(target))
            return;

        pet->CastSpell(target, HunterData::SPELL_STOMP_PET, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_hun_arcane_shot_bm::HandleAfterCast);
    }
};

// 201809 Hunter Pet Talent Procs, on the real pet (owner-added, ApplyBmPetAuras) - Culling the Herd on a basic
// attack crit, the Improved Aspect of the Viper capstone on a basic or command crit (S1b B4, BEAST-MASTERY §4.9).
// The spell_proc row already limits it to crits of d2 b22 | b23 spells; neither effect rolls (deterministic).
class spell_hun_bm_pet_procs : public AuraScript
{
    PrepareAuraScript(spell_hun_bm_pet_procs);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ HunterData::SPELL_CULLING_THE_HERD_BUFF, SPELL_REPLENISHMENT,
            HunterData::SPELL_IMPROVED_ASPECT_OF_THE_VIPER_201831, HunterData::SPELL_CULLING_THE_HERD,
            HunterData::SPELL_CULLING_THE_HERD_201842, HunterData::SPELL_CULLING_THE_HERD_201843 });
    }

    static bool IsBasicAttack(SpellInfo const* spellInfo)
    {
        return spellInfo->SpellFamilyName == SPELLFAMILY_HUNTER &&
            (spellInfo->SpellFamilyFlags[2] & FAMILY_FLAG2_PET_BASIC_ATTACK);
    }

    static uint32 GetCullingTheHerdRank(Player const* owner)
    {
        return GetKnownRank(owner, { HunterData::SPELL_CULLING_THE_HERD_201843,
            HunterData::SPELL_CULLING_THE_HERD_201842, HunterData::SPELL_CULLING_THE_HERD });
    }

    // The hunter who added 201809 (the aura's caster, L5), while the aura's pet is still his and nobody else charms it
    // (review m2: a mind-controlled pet must not feed its charmer, nor its owner). The owner's own possession (Eyes
    // of the Beast) still counts.
    Player* GetRealOwner() const
    {
        Unit* caster = GetCaster();
        Player* owner = caster ? caster->ToPlayer() : nullptr;
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return nullptr;

        Unit* unit = GetUnitOwner();
        Pet* pet = unit ? unit->ToPet() : nullptr;
        if (!pet || pet->GetOwner() != owner)
            return nullptr;

        ObjectGuid const charmer = pet->GetCharmerGUID();
        return charmer.IsEmpty() || charmer == owner->GetGUID() ? owner : nullptr;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return false;

        Player* owner = GetRealOwner();
        if (!owner)
            return false;

        return (IsBasicAttack(spellInfo) && GetCullingTheHerdRank(owner)) ||
            owner->HasAura(HunterData::SPELL_IMPROVED_ASPECT_OF_THE_VIPER_201831);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* pet = GetUnitOwner();
        Player* owner = GetRealOwner();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!pet || !owner || !spellInfo)
            return;

        // Culling the Herd (basic attacks only): 201808 is target 1, so it always lands on its caster; the hunter
        // and the pet each cast their own copy (B4)
        if (IsBasicAttack(spellInfo))
        {
            if (uint32 const rank = GetCullingTheHerdRank(owner))
            {
                int32 const amount = sSpellMgr->AssertSpellInfo(rank)->Effects[EFFECT_0].CalcValue(owner);
                if (amount > 0)
                {
                    owner->CastCustomSpell(HunterData::SPELL_CULLING_THE_HERD_BUFF, SPELLVALUE_BASE_POINT0, amount,
                        owner, TRIGGERED_FULL_MASK);
                    pet->CastCustomSpell(HunterData::SPELL_CULLING_THE_HERD_BUFF, SPELLVALUE_BASE_POINT0, amount, pet,
                        TRIGGERED_FULL_MASK);
                }
            }
        }

        // Improved Aspect of the Viper 2/2 capstone (basic or command crit, per target on area commands, F23)
        if (owner->HasAura(HunterData::SPELL_IMPROVED_ASPECT_OF_THE_VIPER_201831))
        {
            owner->EnergizeBySpell(owner, HunterData::SPELL_IMPROVED_ASPECT_OF_THE_VIPER_201831,
                CalculatePct(owner->GetMaxPower(POWER_MANA), HunterData::IAOTV_CAPSTONE_MANA_PCT), POWER_MANA);
            owner->CastSpell(owner, SPELL_REPLENISHMENT, true);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_bm_pet_procs::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_bm_pet_procs::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201802 Stampede - three guardians of the pet's family attack the target for 15 s (S1b B6, BEAST-MASTERY §4.4,
// PET §9.1). The warlock spell_warl_summon_infernal shape, summoned inline (no meteor delay). No follow motion and
// no AttackStart here: npc_hun_stampede_beast starts its own chase from the GUID it is given (S1b decision 7).
class spell_hun_stampede : public SpellScript
{
    PrepareSpellScript(spell_hun_stampede);

    bool Validate(SpellInfo const* spellInfo) override
    {
        if (!ValidateSpellInfo({ HunterData::SPELL_BESTIAL_WRATH, HunterData::SPELL_BEAST_CLEAVE_BUFF }))
            return false;

        if (!sSummonPropertiesStore.LookupEntry(spellInfo->Effects[EFFECT_0].MiscValueB))
        {
            LOG_ERROR("scripts.hunter", "spell_hun_stampede: spell {} has no SummonProperties {}", spellInfo->Id,
                spellInfo->Effects[EFFECT_0].MiscValueB);
            return false;
        }

        for (uint32 entry : STAMPEDE_BEAST_ENTRIES)
        {
            if (!sObjectMgr->GetCreatureTemplate(entry))
            {
                LOG_ERROR("scripts.hunter", "spell_hun_stampede: creature_template {} does not exist", entry);
                return false;
            }
        }

        return true;
    }

    SpellCastResult CheckCast()
    {
        // CR3: only a hunter Player acts
        Player* player = GetCaster()->ToPlayer();
        if (!player || player->getClass() != CLASS_HUNTER)
            return SPELL_CAST_OK;

        Pet* pet = player->GetPet();
        if (!pet || !pet->IsAlive())
            return SPELL_FAILED_NO_PET;

        Unit* target = GetExplTargetUnit();
        if (!target || !target->IsAlive() || !player->IsValidAttackTarget(target))
            return SPELL_FAILED_BAD_TARGETS;

        return SPELL_CAST_OK;
    }

    // Copies the player's `spellId` aura on the pet to `beast` with the pet's remaining duration. S1a's recursion
    // guards make this safe: Bestial Wrath's apply hook skips a non-pet, Beast Cleave's returns on a non-Player.
    static void CopyPetAura(Player* player, Pet* pet, Unit* beast, uint32 spellId)
    {
        // a spent aura (0 ms left) is not copied: the copy would expire on the next update (review m5)
        Aura const* petAura = pet->GetAura(spellId, player->GetGUID());
        if (!petAura || petAura->GetDuration() == 0)
            return;

        if (Aura* copy = player->AddAura(spellId, beast))
            copy->SetDuration(petAura->GetDuration());
    }

    void HandleSummon(SpellEffIndex effIndex)
    {
        PreventHitDefaultEffect(effIndex);

        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        Pet* pet = player->GetPet();
        WorldLocation const* dest = GetHitDest();
        if (!pet || !dest || !pet->GetCreatureTemplate())
            return;

        SpellInfo const* spellInfo = GetSpellInfo();
        uint32 const spellId = spellInfo->Id;
        uint32 const entry = Hunter::GetStampedeEntry(pet->GetCreatureTemplate()->family);
        SummonPropertiesEntry const* properties =
            sSummonPropertiesStore.LookupEntry(spellInfo->Effects[effIndex].MiscValueB);
        if (!properties)
            return;

        int32 duration = spellInfo->GetDuration();
        player->ApplySpellMod(spellId, SPELLMOD_DURATION, duration);

        // The spell's dest only carries coordinates (its map id stays invalid, bugs log "Summon Infernal summons
        // nothing"), so the map is the player's
        Map* map = player->GetMap();
        Position const center = *dest;
        Unit* target = GetExplTargetUnit();

        std::vector<TempSummon*> beasts;
        for (int32 i = 0; i < HunterData::STAMPEDE_BEAST_COUNT; ++i)
        {
            // evenly on a STAMPEDE_SPREAD_YD ring around the dest, ground height from the player's map
            float const angle = player->GetOrientation() + 2.0f * float(M_PI) * float(i) /
                float(HunterData::STAMPEDE_BEAST_COUNT);
            float x = center.GetPositionX() + HunterData::STAMPEDE_SPREAD_YD * std::cos(angle);
            float y = center.GetPositionY() + HunterData::STAMPEDE_SPREAD_YD * std::sin(angle);
            float z = center.GetPositionZ();
            Acore::NormalizeMapCoord(x);
            Acore::NormalizeMapCoord(y);
            player->UpdateGroundPositionZ(x, y, z);

            // each beast faces the target (else the ring's center), not outward along its ring angle (review MN-4)
            Position spot(x, y, z);
            spot.SetOrientation(target ? spot.GetAbsoluteAngle(target) : spot.GetAbsoluteAngle(center));

            TempSummon* beast = map->SummonCreature(entry, spot, properties, duration, player, spellId);
            if (!beast)
                continue;

            if (properties->Category == SUMMON_CATEGORY_ALLY)
                beast->SetFaction(player->GetFaction());

            // The beast is in m_Controlled once SummonCreature has returned (L4)
            Hunter::RefreshPetPassthrough(player, beast);
            CopyPetAura(player, pet, beast, HunterData::SPELL_BESTIAL_WRATH);
            CopyPetAura(player, pet, beast, HunterData::SPELL_BEAST_CLEAVE_BUFF);

            if (target && target->IsAlive() && beast->AI())
                beast->AI()->SetGUID(target->GetGUID());

            beasts.push_back(beast);
        }

        if (beasts.empty())
            return;

        // The spell's own SPELL_SUMMON combat-log line (Spell::ExecuteLogEffectSummonObject) was skipped along with
        // the default effect; damage meters need it to credit the beasts' damage to the hunter. Same layout as
        // Spell::SendLogExecute.
        WorldPacket data(SMSG_SPELLLOGEXECUTE, 8 + 4 + 4 + 4 + 4 + 8 * beasts.size());
        data << player->GetPackGUID();
        data << uint32(spellId);
        data << uint32(1);                              // effect count
        data << uint32(SPELL_EFFECT_SUMMON);
        data << uint32(beasts.size());                  // target count
        for (TempSummon* beast : beasts)
            data << beast->GetPackGUID();
        player->SendMessageToSet(&data, true);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_hun_stampede::CheckCast);
        OnEffectHit += SpellEffectFn(spell_hun_stampede::HandleSummon, EFFECT_0, SPELL_EFFECT_SUMMON);
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
    // S1b
    RegisterSpellScript(spell_hun_steady_shot_nature);
    RegisterSpellScript(spell_hun_cobra_strikes_bm);
    RegisterSpellScript(spell_hun_arcane_shot_bm);
    RegisterSpellScript(spell_hun_bm_pet_procs);
    RegisterSpellScript(spell_hun_stampede);
}
