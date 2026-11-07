/*
 * mod-dungeon-bosses, Stratholme: the Balnazzar and Baron Rivendare hard mode item effects (wave 1 dungeon items;
 * designer text: docs/dungeons/stratholme-rework.md "Hard mode lists"). The spells are
 * apps/dbc-tools/source/items/stratholme_hard_mode_effects.py; every damage and absorb number comes from potency or
 * from the spell data, so nothing here sizes a hit. The Carrion Signet, Ysida's Locket and the Deathcharger's Spur
 * scale by item level (scale="budget"): their tiers above 71 carry their own copies, bound to the same scripts, so a
 * script never casts a family spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives
 * the copy in the tier of the spell or aura it runs for, and the base id on the 71 tier. The Carrion Signet is data
 * only (a PROC_TRIGGER_SPELL aura) and has no script.
 *
 *   spell_strat_dust_of_the_nathrezim     205662 Dust of the Nathrezim (Use). Refuses a player, anything a player
 *                                         controls, and a boss; the sleep itself is the spell data.
 *   spell_strat_two_faced_tome            205663 Two-Faced Tome (Equip). On a landed direct heal (spell_proc: 20%) the
 *                                         enemy nearest the healed target within the aura's radius, in combat, takes
 *                                         205664 for the aura's amount in percent of the heal.
 *   spell_strat_ysidas_locket             205665 Ysida's Locket (Equip). Every 0.5 s, unless the lockout 205667 is up:
 *                                         the lowest group member within the radius under the threshold (the
 *                                         aura's amount) gets the ward 205666, the wearer the lockout.
 *   spell_strat_blade_of_the_condemned    205668 Blade of the Condemned (Equip). Every landed melee hit adds a stack
 *                                         of 205669 to the target; a hit on another target first removes the
 *                                         wearer's Condemned from the last one.
 *   StratholmeCondemnedDamage (UnitScript) melee, spell and periodic damage from a Condemned target's condemner
 *                                         grows by the aura's amount (1% x stacks).
 *   spell_strat_deathchargers_spur        205670 Deathcharger's Spur (Use). Puts the mount look 205672 under the
 *                                         wearer for the Spur's duration and, every 0.25 s, tramples (205671) every
 *                                         enemy within the radius it has not trampled yet this use.
 *
 * Every effect logs one DEBUG line, "strat-items <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeHardModeItemsLogic.h"
#include "Unit.h"
#include <list>
#include <unordered_set>

using namespace StratholmeHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    // Every living enemy of `attacker` within `radius` yards of `center`.
    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, attacker, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, found, check);
        Cell::VisitObjects(center, searcher, radius);
        found.remove_if([attacker](Unit* unit) { return !unit->IsAlive() || !attacker->IsValidAttackTarget(unit); });
        return found;
    }
}

// 205662 Dust of the Nathrezim: a non-boss enemy creature only. The sleep, its length and "damage wakes it" are the
// spell data (MOD_STUN, Mechanic SLEEP, AuraInterruptFlags TAKE_DAMAGE).
class spell_strat_dust_of_the_nathrezim : public SpellScript
{
    PrepareSpellScript(spell_strat_dust_of_the_nathrezim);

    SpellCastResult CheckTarget()
    {
        Unit* target = GetExplTargetUnit();
        if (!target || target->IsControlledByPlayer())
            return SPELL_FAILED_BAD_TARGETS;
        Creature* creature = target->ToCreature();
        if (!creature || creature->IsDungeonBoss() || creature->isWorldBoss())
            return SPELL_FAILED_BAD_TARGETS;
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_strat_dust_of_the_nathrezim::CheckTarget);
    }
};

// 205663 Two-Faced Tome: a landed direct heal tells a lie to the enemy nearest the healed target.
class spell_strat_two_faced_tome : public AuraScript
{
    PrepareAuraScript(spell_strat_two_faced_tome);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_THE_LIE });
    }

    // A direct heal that landed (spell_proc: heal type, hit phase). A heal over time's cast heals nothing then, and
    // its ticks are periodic events, which the proc flags leave out.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        return heal && heal->GetSpellInfo() && heal->GetHeal() > 0 && eventInfo.GetActionTarget();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* healed = eventInfo.GetActionTarget();
        HealInfo const* heal = eventInfo.GetHealInfo();
        if (!healer || !healed || !heal)
            return;

        int32 const damage = LieDamage(heal->GetHeal(), aurEff->GetAmount());
        if (damage <= 0)
            return;

        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(healer);
        Unit* liar = nullptr;
        for (Unit* enemy : EnemiesNear(healed, healer, radius))
        {
            if (!enemy->IsInCombat())
                continue;
            if (!liar || healed->GetExactDist(enemy) < healed->GetExactDist(liar))
                liar = enemy;
        }
        if (!liar)
            return;

        // Triggered by this aura: the lie can never proc the Tome again (it is damage, and SUPPRESS_CASTER_PROCS).
        healer->CastCustomSpell(liar, SPELL_THE_LIE, &damage, nullptr, nullptr, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "strat-items tome {} healed {} for {}: lie of {} on {}", healer->GetGUID().ToString(),
            healed->GetGUID().ToString(), heal->GetHeal(), damage, liar->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_strat_two_faced_tome::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_strat_two_faced_tome::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 205665 Ysida's Locket: wards the group member in the most danger, once per lockout.
class spell_strat_ysidas_locket : public AuraScript
{
    PrepareAuraScript(spell_strat_ysidas_locket);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_YSIDAS_WARD),
            TierSpell(spellInfo, SPELL_YSIDAS_LOCKET_LOCKOUT) });
    }

    void HandleWatch(AuraEffect const* aurEff)
    {
        Player* wearer = GetTarget()->ToPlayer();
        if (!wearer || !wearer->IsAlive() || !wearer->IsInWorld())
            return;

        // This tier's ward and lockout (the declared ones on the 71 tier, the tier's copies above it).
        uint32 const lockoutId = TierSpell(GetSpellInfo(), SPELL_YSIDAS_LOCKET_LOCKOUT);
        if (wearer->HasAura(lockoutId))
            return;

        int32 const thresholdPct = aurEff->GetAmount();
        float const radius = GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer);
        Player* ward = nullptr;
        auto consider = [&](Player* member)
        {
            if (!member || !member->IsInWorld() || !member->IsAlive() || member->GetMap() != wearer->GetMap())
                return;
            if (member != wearer && !wearer->IsWithinDistInMap(member, radius))
                return;
            if (!BelowHealthPct(member->GetHealth(), member->GetMaxHealth(), thresholdPct))
                return;
            if (!ward || LowerHealthFraction(member->GetHealth(), member->GetMaxHealth(), ward->GetHealth(),
                    ward->GetMaxHealth()))
                ward = member;
        };
        if (Group* group = wearer->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                consider(ref->GetSource());
        }
        else
            consider(wearer);
        if (!ward)
            return;

        uint32 const wardId = TierSpell(GetSpellInfo(), SPELL_YSIDAS_WARD);
        wearer->CastSpell(ward, wardId, true, nullptr, aurEff);
        wearer->CastSpell(wearer, lockoutId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "strat-items locket {} ({}) warded {} at {}/{}: ward {}", wearer->GetGUID().ToString(), GetId(),
            ward->GetGUID().ToString(), ward->GetHealth(), ward->GetMaxHealth(), wardId);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_strat_ysidas_locket::HandleWatch, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 205668 Blade of the Condemned: every landed melee hit Condemns the target; a new target resets the old one.
class spell_strat_blade_of_the_condemned : public AuraScript
{
    PrepareAuraScript(spell_strat_blade_of_the_condemned);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_CONDEMNED });
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

        if (CondemnResets(_lastTarget.GetRawValue(), victim->GetGUID().GetRawValue()))
            if (Unit* last = ObjectAccessor::GetUnit(*wearer, _lastTarget))
                last->RemoveAurasDueToSpell(SPELL_CONDEMNED, wearer->GetGUID());
        _lastTarget = victim->GetGUID();

        // One more stack (the spell data caps it at 5) and a fresh duration.
        wearer->CastSpell(victim, SPELL_CONDEMNED, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "strat-items blade {} condemned {}", wearer->GetGUID().ToString(),
            victim->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_strat_blade_of_the_condemned::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_strat_blade_of_the_condemned::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }

    ObjectGuid _lastTarget;
};

// 205669 Condemned: damage from the condemner grows by the aura's amount (1% per stack; the engine multiplies the
// amount by the stacks). SPELL_AURA_MOD_DAMAGE_FROM_CASTER cannot do this: it needs a spell class mask and skips auto
// attacks.
class StratholmeCondemnedDamage : public UnitScript
{
public:
    StratholmeCondemnedDamage() : UnitScript("StratholmeCondemnedDamage", true, { UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK }) { }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        damage = Condemned(target, attacker, damage);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* /*spellInfo*/) override
    {
        if (damage > 0)
            damage = int32(std::min<uint32>(Condemned(target, attacker, uint32(damage)), 0x7FFFFFFFu));
    }

    // The engine also calls this hook for periodic heals: a positive spell is never Condemned damage.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
        SpellInfo const* spellInfo) override
    {
        if (spellInfo && spellInfo->IsPositive())
            return;
        damage = Condemned(target, attacker, damage);
    }

private:
    static uint32 Condemned(Unit* target, Unit* attacker, uint32 damage)
    {
        if (!target || !attacker || !damage)
            return damage;
        Aura const* aura = target->GetAura(SPELL_CONDEMNED, attacker->GetGUID());
        if (!aura)
            return damage;
        AuraEffect const* effect = aura->GetEffect(EFFECT_0);
        return CondemnedDamage(damage, effect ? effect->GetAmount() : 0);
    }
};

// 205670 Deathcharger's Spur: the mount look, and a trample on every enemy the wearer passes through, once each.
class spell_strat_deathchargers_spur : public AuraScript
{
    PrepareAuraScript(spell_strat_deathchargers_spur);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_DEATHCHARGER_TRAMPLE), SPELL_SPECTRAL_DEATHCHARGER });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        _trampled.clear();
        Unit* wearer = GetTarget();
        // The look only: a mount spell cast would fail Spell::CheckCast's no-mounts-in-dungeons rule, so it is added
        // as an aura. Skipped in a form that cannot mount, on a mount already or in a vehicle.
        if (!wearer->IsInDisallowedMountForm() && !wearer->IsMounted() && !wearer->GetVehicle())
            wearer->AddAura(SPELL_SPECTRAL_DEATHCHARGER, wearer);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_SPECTRAL_DEATHCHARGER);
        _trampled.clear();
    }

    void HandleTrample(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;

        uint32 const trampleId = TierSpell(GetSpellInfo(), SPELL_DEATHCHARGER_TRAMPLE);
        float const radius = GetSpellInfo()->Effects[EFFECT_2].CalcRadius(wearer);
        for (Unit* enemy : EnemiesNear(wearer, wearer, radius))
        {
            if (!_trampled.insert(enemy->GetGUID()).second)
                continue;
            wearer->CastSpell(enemy, trampleId, true, nullptr, aurEff);
            LOG_DEBUG(kLog, "strat-items spur {} ({}) trampled {}: {}", wearer->GetGUID().ToString(), GetId(),
                enemy->GetGUID().ToString(), trampleId);
        }
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_strat_deathchargers_spur::HandleApply, EFFECT_0,
            SPELL_AURA_MOD_INCREASE_SPEED, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_strat_deathchargers_spur::HandleRemove, EFFECT_0,
            SPELL_AURA_MOD_INCREASE_SPEED, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_strat_deathchargers_spur::HandleTrample, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }

    std::unordered_set<ObjectGuid> _trampled;
};

void AddSC_strat_hard_mode_items()
{
    RegisterSpellScript(spell_strat_dust_of_the_nathrezim);
    RegisterSpellScript(spell_strat_two_faced_tome);
    RegisterSpellScript(spell_strat_ysidas_locket);
    RegisterSpellScript(spell_strat_blade_of_the_condemned);
    RegisterSpellScript(spell_strat_deathchargers_spur);
    new StratholmeCondemnedDamage();
}
