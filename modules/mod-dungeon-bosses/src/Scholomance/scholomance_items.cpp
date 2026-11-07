/*
 * mod-dungeon-bosses, Scholomance: the scripted Scholomance item effects (wave 1 dungeon items; designer text:
 * docs/dungeons/scholomance-rework.md ## Loot, "Hard mode lists"). The spells are
 * apps/dbc-tools/source/items/scholomance_hard_mode_effects.py; every damage number comes from potency, so nothing here
 * sizes a hit. The other Scholomance item effects are spell data alone (proc triggers, periodic triggers, auras).
 *
 * The Portal Rod's barrage scales with the tier (stage IV10, scale="budget"): the 71 tier carries the declared spells,
 * every higher tier its own copies, bound to the same script. So the script never casts the barrage by its base id:
 * ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the tier of the aura it runs for. The
 * Phylactery Shard, the Bonechill Blade's proc check and the Transfer Papers have no copies (one spell per item).
 *
 *   spell_scholo_phylactery_shard        205631 Phylactery Shard (Use). While the ice is up, every hit taken
 *                                        (spell_proc: any damage taken) adds to a tally; when it ends any way but
 *                                        death the wearer heals for effect 2's percent of it (205632).
 *   spell_scholo_bonechill_blade         205635 Bonechill Blade (Equip). The proc check lets each cast reach the
 *                                        spell_proc roll once ("rolls once per cast"): an area spell's later targets
 *                                        are refused, so it is one 20% roll per cast, not one per target.
 *   spell_scholo_transfer_papers         205637 Transfer Papers (Use). Checks the target (another living player of the
 *                                        caster's group, neither side on a taxi or a vehicle) and swaps the two
 *                                        positions; each keeps its own facing.
 *   spell_scholo_darkmasters_portal_rod  205640 Darkmaster's Portal Rod (Equip). On a proc (spell_proc: landed
 *                                        damaging spells, 10%, 15 s internal cooldown) the portal (creature 300465,
 *                                        with the ground look 205642) opens behind the target and the wearer's
 *                                        triggered barrage 205641 (the tier's copy) hits.
 *
 * Every effect logs one DEBUG line, "scholo-items <effect> ...", in module.dungeonbosses.
 */

#include "ItemSpellCopies.h"
#include "Log.h"
#include "Player.h"
#include "ScholomanceItemsLogic.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"

using namespace ScholomanceItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";
}

// 205631 Phylactery Shard: armor for 10 sec, then a heal for a share of the damage taken meanwhile.
class spell_scholo_phylactery_shard : public AuraScript
{
    PrepareAuraScript(spell_scholo_phylactery_shard);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PHYLACTERY_MEND });
    }

    // Any damage taken while the ice is up (spell_proc: PROC_FLAG_TAKEN_DAMAGE), after absorbs.
    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        if (DamageInfo const* damage = eventInfo.GetDamageInfo())
            _taken = PhylacteryTally(_taken, damage->GetDamage());
    }

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        AuraApplication const* application = GetTargetApplication();
        if (!wearer || !wearer->IsAlive() || !application || application->GetRemoveMode() == AURA_REMOVE_BY_DEATH)
            return;

        int32 const heal = PhylacteryHeal(_taken, aurEff->GetAmount());
        LOG_DEBUG(kLog, "scholo-items phylactery {} ({}) took {} while iced: heals {}", wearer->GetGUID().ToString(),
            GetId(), _taken, heal);
        if (heal > 0)
            wearer->CastCustomSpell(wearer, SPELL_PHYLACTERY_MEND, &heal, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_scholo_phylactery_shard::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_scholo_phylactery_shard::HandleRemove, EFFECT_1,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    std::uint64_t _taken = 0;
};

// 205635 Bonechill Blade: one roll per cast. The engine runs this check before it rolls the spell_proc chance, so
// refusing a cast's later targets leaves exactly one roll per cast.
class spell_scholo_bonechill_blade : public AuraScript
{
    PrepareAuraScript(spell_scholo_bonechill_blade);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        Unit* target = eventInfo.GetActionTarget();
        if (!spell || !target || !target->IsAlive())
            return false;

        CastStamp const now{ spell, spell->GetSpellInfo()->Id, spell->m_cast_count };
        if (SameCast(_rolled, now))
            return false;
        _rolled = now;
        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_scholo_bonechill_blade::CheckProc);
    }

    CastStamp _rolled;
};

// 205637 Transfer Papers: swap places with a friendly party member within 30 yd.
class spell_scholo_transfer_papers : public SpellScript
{
    PrepareSpellScript(spell_scholo_transfer_papers);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return SPELL_FAILED_BAD_TARGETS;

        Player const* casterPlayer = caster->ToPlayer();
        Player const* targetPlayer = target->ToPlayer();
        SwapCheck const check{ targetPlayer != nullptr, target == caster, target->IsAlive(),
            casterPlayer && targetPlayer && casterPlayer->IsInSameGroupWith(targetPlayer), caster->IsInFlight(),
            target->IsInFlight(), caster->GetVehicle() != nullptr, target->GetVehicle() != nullptr };
        return CanSwap(check) ? SPELL_CAST_OK : SPELL_FAILED_BAD_TARGETS;
    }

    void HandleSwap(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || caster == target)
            return;

        Position const from = caster->GetPosition();
        Position const to = target->GetPosition();
        caster->NearTeleportTo(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), caster->GetOrientation(),
            true);
        target->NearTeleportTo(from.GetPositionX(), from.GetPositionY(), from.GetPositionZ(),
            target->GetOrientation(), true);
        LOG_DEBUG(kLog, "scholo-items transfer papers {} swapped places with {}", caster->GetGUID().ToString(),
            target->GetGUID().ToString());
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_scholo_transfer_papers::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_scholo_transfer_papers::HandleSwap, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 205640 Darkmaster's Portal Rod: a portal opens behind the target and the wearer's barrage hits it.
class spell_scholo_darkmasters_portal_rod : public AuraScript
{
    PrepareAuraScript(spell_scholo_darkmasters_portal_rod);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ ItemSpellCopies::Resolve(spellInfo->Id, SPELL_PORTAL_BARRAGE),
            SPELL_DARKMASTERS_PORTAL_LOOK });
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

        // The portal look is the same on every tier; the barrage is the tier's own (a copy above the 71 tier).
        Position const behind = victim->GetFirstCollisionPosition(PortalDistance(victim->GetCombatReach()),
            float(M_PI));
        if (TempSummon* portal = wearer->SummonCreature(NPC_DARKMASTERS_PORTAL, behind, TEMPSUMMON_TIMED_DESPAWN,
            kPortalStayMs))
        {
            portal->SetReactState(REACT_PASSIVE);
            portal->SetControlled(true, UNIT_STATE_ROOT);
            portal->SetFacingToObject(victim);
            portal->CastSpell(portal->GetPositionX(), portal->GetPositionY(), portal->GetPositionZ(),
                SPELL_DARKMASTERS_PORTAL_LOOK, true);
        }
        else
        {
            wearer->CastSpell(behind.GetPositionX(), behind.GetPositionY(), behind.GetPositionZ(),
                SPELL_DARKMASTERS_PORTAL_LOOK, true);
        }
        uint32 const barrageId = ItemSpellCopies::Resolve(GetId(), SPELL_PORTAL_BARRAGE);
        wearer->CastSpell(victim, barrageId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "scholo-items portal rod {} ({}) opened a portal on {}: barrage {}",
            wearer->GetGUID().ToString(), GetId(), victim->GetGUID().ToString(), barrageId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_scholo_darkmasters_portal_rod::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_scholo_darkmasters_portal_rod::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }
};

void AddSC_scholo_items()
{
    RegisterSpellScript(spell_scholo_phylactery_shard);
    RegisterSpellScript(spell_scholo_bonechill_blade);
    RegisterSpellScript(spell_scholo_transfer_papers);
    RegisterSpellScript(spell_scholo_darkmasters_portal_rod);
}
