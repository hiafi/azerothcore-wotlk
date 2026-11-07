/*
 * mod-dungeon-bosses, Shadowfang Keep: the Archmage Arugal hard mode item effects that need a script (item variants,
 * wave 1; designer text: docs/dungeons/shadowfang-keep-rework.md "Hard mode bonus list: Archmage Arugal, Face Him
 * Alone"). The spells are apps/dbc-tools/source/items/shadowfang_keep_hard_mode_effects.py; every damage number comes
 * from potency, so nothing here sizes a hit. The 71 tier of the Tome carries the declared spells; every higher tier
 * carries its own copies (stage IV10, scale="budget"), bound to the same scripts here, so a script never casts a family
 * spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the tier of the
 * spell or aura it runs for, and the base id on the 71 tier.
 *
 *   spell_sfk_arugals_shadow_tome      205601 Arugal's Shadow Tome (Equip). On a proc (spell_proc: landed direct
 *                                      damaging spells, 10%, 30 s internal cooldown) an Arugal's Voidwalker (300460)
 *                                      appears at the target, on the wearer's side, and chases it; the wearer's
 *                                      triggered 205602 lands on the target. Item auras get no Proc Chance
 *                                      (docs/Systems.md section 5), so nothing extra is rolled here.
 *   spell_sfk_arugals_voidwalker       205602 Arugal's Voidwalker (the damage over time). On every tick the wearer's
 *                                      own Voidwalker swings at the target; when the debuff ends (it ran out, the
 *                                      target died) the Voidwalker leaves.
 *
 * The Vial of the Worgen's Curse (205600), Ashcrombe's Locket (205603) and the Meteor Shard's Firebolt (205604) are
 * pure spell data.
 *
 * Every effect logs one DEBUG line, "sfk-items <effect> ...", in module.dungeonbosses.
 */

#include "Creature.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "SfkHardModeItemsLogic.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <list>

using namespace SfkHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    // The Voidwalkers around `target` that `casterGuid` summoned (normally one: the Tome's cooldown outlasts it).
    std::list<Creature*> OwnVoidwalkers(Unit* target, ObjectGuid casterGuid)
    {
        std::list<Creature*> found;
        target->GetCreatureListWithEntryInGrid(found, NPC_TOME_VOIDWALKER, kVoidwalkerSearchRange);
        found.remove_if([casterGuid](Creature* creature)
        {
            TempSummon const* summon = creature->ToTempSummon();
            return !summon || !IsOwnVoidwalker(summon->GetSummonerGUID().GetRawValue(), casterGuid.GetRawValue());
        });
        return found;
    }
}

// 205601 Arugal's Shadow Tome: a Voidwalker appears at the target and the wearer's 205602 lands.
class spell_sfk_arugals_shadow_tome : public AuraScript
{
    PrepareAuraScript(spell_sfk_arugals_shadow_tome);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_ARUGALS_VOIDWALKER) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        return wearer && victim && victim != wearer && victim->IsAlive() && wearer->IsValidAttackTarget(victim);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!wearer || !victim)
            return;

        Position const beside = victim->GetFirstCollisionPosition(VoidwalkerDistance(victim->GetCombatReach()),
            victim->GetRelativeAngle(wearer));
        if (TempSummon* voidwalker = wearer->SummonCreature(NPC_TOME_VOIDWALKER, beside, TEMPSUMMON_TIMED_DESPAWN,
            kVoidwalkerStayMs))
        {
            voidwalker->SetLevel(wearer->GetLevel(), false);
            voidwalker->SetReactState(REACT_PASSIVE);
            voidwalker->SetFacingToObject(victim);
            voidwalker->GetMotionMaster()->MoveChase(victim);
        }

        // Triggered by this aura: the debuff can never proc the Tome again. The tier's own debuff (a copy above the
        // 71 tier).
        uint32 const attackId = TierSpell(GetSpellInfo(), SPELL_ARUGALS_VOIDWALKER);
        wearer->CastSpell(victim, attackId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "sfk-items tome {} ({}) called a Voidwalker on {}: attacks {}", wearer->GetGUID().ToString(),
            GetId(), victim->GetGUID().ToString(), attackId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sfk_arugals_shadow_tome::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sfk_arugals_shadow_tome::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 205602 Arugal's Voidwalker: the wearer's own Voidwalker swings on every tick and leaves when the debuff ends. The
// damage itself is the aura's periodic tick (potency), untouched here.
class spell_sfk_arugals_voidwalker : public AuraScript
{
    PrepareAuraScript(spell_sfk_arugals_voidwalker);

    void HandleTick(AuraEffect const* /*aurEff*/)
    {
        Unit* target = GetTarget();
        if (!target)
            return;

        for (Creature* voidwalker : OwnVoidwalkers(target, GetCasterGUID()))
        {
            voidwalker->SetFacingToObject(target);
            voidwalker->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target)
            return;

        for (Creature* voidwalker : OwnVoidwalkers(target, GetCasterGUID()))
            voidwalker->DespawnOrUnsummon();
        LOG_DEBUG(kLog, "sfk-items voidwalker ({}) on {} ended", GetId(), target->GetGUID().ToString());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_sfk_arugals_voidwalker::HandleTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sfk_arugals_voidwalker::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_sfk_hard_mode_items()
{
    RegisterSpellScript(spell_sfk_arugals_shadow_tome);
    RegisterSpellScript(spell_sfk_arugals_voidwalker);
}
