/*
 * mod-dungeon-bosses, Deadmines: the Edwin VanCleef hard mode item effects (item variants plan section 7.2, stage
 * IV6; designer text: docs/dungeons/deadmines-rework.md "Hard mode bonus list: Edwin VanCleef"). The spells are
 * apps/dbc-tools/source/items/deadmines_hard_mode_effects.py; every damage number comes from potency, so nothing here
 * sizes a hit. The 71 tier of each item carries the declared spells; every higher tier carries its own copies (stage
 * IV10, scale="budget": damage and healing scaled by the tier's stat budget), bound to the same scripts here. So a
 * script never casts a family spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives
 * the copy in the tier of the spell or aura it runs for, and the base id on the 71 tier.
 *
 *   spell_dm_powder_keg_fuse           205400 Powder Keg Fuse (Use). The keg is aimed at the target's position at
 *                                      throw time and lands there whatever becomes of the target in flight: the
 *                                      lit keg 205401 marks the spot, and when its duration (the fuse) runs out
 *                                      the wearer sets off the blast 205402 there, if still on the same map and
 *                                      instance.
 *   spell_dm_blackguards_signet        205403 Blackguard's Signet (Equip). On a proc (spell_proc: landed melee hits,
 *                                      10%, 10 s internal cooldown) a Defias Blackguard (300430) appears behind the
 *                                      target, plays the ambush 205405 and the wearer's triggered 205404 strikes.
 *                                      Item auras get no Proc Chance (docs/Systems.md section 5), so nothing extra
 *                                      is rolled here.
 *   spell_dm_lantern_of_the_roaring_flame  205406 Lantern of the Roaring Flame (Use). The next direct heal (spell_proc:
 *                                      heal type, hit phase, one charge) drops the warding flame 205407 at the healed
 *                                      target's feet.
 *
 * Every effect logs one DEBUG line, "dm-items <effect> ...", in module.dungeonbosses.
 */

#include "Creature.h"
#include "HardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"

using namespace HardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }
}

// 205400 Powder Keg Fuse: the keg is aimed at the target's position at the moment of the throw. It lands there, the
// fuse burns for 205401's duration, then the blast goes off at the spot. Nothing waits for the missile to hit the
// target, so a target that dies or evades in flight still gets the blast at that spot and the cooldown is never wasted.
class spell_dm_powder_keg_fuse : public SpellScript
{
    PrepareSpellScript(spell_dm_powder_keg_fuse);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_POWDER_KEG_FUSE_LOOK),
            TierSpell(spellInfo, SPELL_POWDER_KEG_BLAST) });
    }

    void HandleThrown()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return;

        // This tier's lit keg and blast (the declared ones on the 71 tier, the tier's copies above it).
        uint32 const lookId = TierSpell(GetSpellInfo(), SPELL_POWDER_KEG_FUSE_LOOK);
        uint32 const blastId = TierSpell(GetSpellInfo(), SPELL_POWDER_KEG_BLAST);
        Position const spot = target->GetPosition();
        uint32 const flightMs = KegFlightMs(caster->GetDistance(spot), GetSpellInfo()->Speed);
        SpellInfo const* look = sSpellMgr->GetSpellInfo(lookId);
        uint32 const fuseMs = KegFuseMs(look ? look->GetDuration() : 0);
        Place const lit{ caster->GetMapId(), caster->GetInstanceId() };
        LOG_DEBUG(kLog, "dm-items keg {} ({}) thrown at ({:.1f}, {:.1f}, {:.1f}): lands in {} ms, blast {} {} ms later",
            caster->GetGUID().ToString(), GetSpellInfo()->Id, spot.GetPositionX(), spot.GetPositionY(),
            spot.GetPositionZ(), flightMs, blastId, fuseMs);

        // The events live in the caster's own EventProcessor, so they die with the caster (logout, removal) and the
        // captured pointer never outlives it.
        caster->m_Events.AddEventAtOffset([caster, spot, lit, lookId]()
        {
            if (!KegStillLive(caster->IsInWorld(), lit, Place{ caster->GetMapId(), caster->GetInstanceId() }))
                return;
            caster->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), lookId, true);
        }, Milliseconds(flightMs));
        caster->m_Events.AddEventAtOffset([caster, spot, lit, blastId]()
        {
            if (!KegStillLive(caster->IsInWorld(), lit, Place{ caster->GetMapId(), caster->GetInstanceId() }))
                return;
            caster->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), blastId, true);
        }, Milliseconds(flightMs + fuseMs));
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_dm_powder_keg_fuse::HandleThrown);
    }
};

// 205403 Blackguard's Signet: a Blackguard appears behind the target and the wearer's 205404 strikes.
class spell_dm_blackguards_signet : public AuraScript
{
    PrepareAuraScript(spell_dm_blackguards_signet);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_BLACKGUARD_STRIKE), SPELL_BLACKGUARD_AMBUSH_LOOK });
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

        Position const behind = victim->GetFirstCollisionPosition(BlackguardDistance(victim->GetCombatReach()),
            float(M_PI));
        if (TempSummon* blackguard = wearer->SummonCreature(NPC_SIGNET_BLACKGUARD, behind,
            TEMPSUMMON_TIMED_DESPAWN, kBlackguardStayMs))
        {
            blackguard->SetLevel(wearer->GetLevel(), false);
            blackguard->SetReactState(REACT_PASSIVE);
            blackguard->SetFacingToObject(victim);
            blackguard->CastSpell(blackguard, SPELL_BLACKGUARD_AMBUSH_LOOK, true);
        }

        // Triggered by this aura: the strike can never proc the Signet again. The tier's own strike (a copy above
        // the 71 tier). The ambush look is the Blackguard's, the same on every tier.
        uint32 const strikeId = TierSpell(GetSpellInfo(), SPELL_BLACKGUARD_STRIKE);
        wearer->CastSpell(victim, strikeId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "dm-items signet {} ({}) called a Blackguard on {}: strike {}", wearer->GetGUID().ToString(),
            GetId(), victim->GetGUID().ToString(), strikeId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dm_blackguards_signet::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dm_blackguards_signet::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 205406 Lantern of the Roaring Flame: the next direct heal drops the warding flame 205407 at the healed target.
class spell_dm_lantern_of_the_roaring_flame : public AuraScript
{
    PrepareAuraScript(spell_dm_lantern_of_the_roaring_flame);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_ROARING_FLAME_ZONE) });
    }

    // A direct heal that landed (spell_proc: heal type, hit phase). A heal over time's cast heals nothing then, and
    // its ticks are periodic events, which the proc flags leave out.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        return heal && heal->GetSpellInfo() && eventInfo.GetActionTarget();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* healed = eventInfo.GetActionTarget();
        if (!healer || !healed)
            return;

        // The tier's own zone (a copy above the 71 tier; its -10% is the same on every tier).
        uint32 const zoneId = TierSpell(GetSpellInfo(), SPELL_ROARING_FLAME_ZONE);
        healer->CastSpell(healed->GetPositionX(), healed->GetPositionY(), healed->GetPositionZ(), zoneId, true);
        LOG_DEBUG(kLog, "dm-items lantern {} ({}) healed {}: warding flame {}", healer->GetGUID().ToString(), GetId(),
            healed->GetGUID().ToString(), zoneId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_dm_lantern_of_the_roaring_flame::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_dm_lantern_of_the_roaring_flame::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }
};

void AddSC_dm_hard_mode_items()
{
    RegisterSpellScript(spell_dm_powder_keg_fuse);
    RegisterSpellScript(spell_dm_blackguards_signet);
    RegisterSpellScript(spell_dm_lantern_of_the_roaring_flame);
}
