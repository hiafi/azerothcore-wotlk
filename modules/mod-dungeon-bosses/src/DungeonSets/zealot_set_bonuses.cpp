/*
 * mod-dungeon-bosses, dungeon sets: the Zealot's set bonuses (docs/dungeons/scarlet-monastery-rework.md ## Loot, "The
 * Zealot's family: Martyrdom" and "3 piece bonuses", rulings 57 to 59). The spells are
 * apps/dbc-tools/source/items/zealot_set_bonuses.py; every damage number comes from potency and every heal from a
 * percent of health or of a hit, so nothing here sizes a payout. The trigger is a health line, never a chance: every
 * proc row is 100%, the 3 piece rows carry the 60 s internal cooldown (a proc cooldown, which Cooldown Haste never
 * touches), and no script here rolls.
 *
 *   spell_zealot_martyr            the ten 3 pieces (212110 + 10k): the hit that takes the wearer from 35% health or
 *                                  more to below 35%, or (the heal sets) the wearer's heal on any target it hits, the
 *                                  wearer included, at or below 35% as it lands (ruling C4); then the set's payout
 *                                  (ZealotSet::kMartyrs).
 *   spell_zealot_unbroken_zeal     212111: each melee ability hit heals the wearer 30% of its damage (212112).
 *   spell_zealot_kindled_vigil     212131: every 2 s the wearer's burn 212132 at the vigil owner's spot.
 *   spell_zealot_kennel_call       212141: every 2 s each hound look (300894) chases the wearer's target and the
 *                                  wearer bites it (212142, or 212143 off ranged attack power); the hounds leave
 *                                  with the buff.
 *   spell_zealot_last_page         212151: only the wearer's own spells with a cast time spend a charge.
 *   spell_zealot_hallowed_thorns   212181: an attacker of the protected unit takes the wearer's 212182.
 *   spell_zealot_arcanists_ward    212191: absorbs 15% of maximum health; detonates (212192) when it breaks, expires
 *                                  or is cancelled.
 *
 * The two areas (212132 Kindled Vigil's burn, 5 yd; 212192 Arcanist's Ward's detonation, 10 yd) hit every enemy in
 * reach, in combat or not (designer ruling B8, 2026-11-20: only a long reach of about 30 yd keeps an in-combat filter);
 * Kennel Call's and Extract Confession's single target (40 yd) is still an enemy already in combat.
 *   spell_zealot_blood_offering    212201: the caster gives 10% of current health.
 *   ZealotSetUnitHooks             212100-212103 Zealot's Fervor (the slope on missing health: damage done, damage
 *                                  taken, healing done) and 212161 Extract Confession (the confessor's hits on the
 *                                  wearer, the wearer's finishing moves and their heal 212162).
 *
 * Every effect logs one DEBUG line, "zealot-set <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "ZealotSetLogic.h"
#include <algorithm>
#include <list>

using namespace ZealotSet;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";
    // A hound look outlives its 12 s buff by this much, so the buff's removal (which dismisses it) always comes first.
    constexpr uint32 kHoundTailMs = 1000;

    bool IsHittableEnemy(Unit* wearer, Unit* victim)
    {
        return wearer && victim && victim != wearer && victim->IsAlive() && wearer->IsValidAttackTarget(victim);
    }

    // The wearer's target: the selected enemy, else the one it attacks; in combat (a bonus never pulls) and within
    // `range` yards. nullptr when neither fits.
    Unit* WearerTarget(Unit* wearer, float range)
    {
        auto usable = [wearer, range](Unit* unit)
        {
            return IsHittableEnemy(wearer, unit) && unit->IsInCombat() && wearer->IsWithinDistInMap(unit, range);
        };
        if (Player* player = wearer->ToPlayer())
            if (Unit* selected = player->GetSelectedUnit(); usable(selected))
                return selected;
        Unit* victim = wearer->GetVictim();
        return usable(victim) ? victim : nullptr;
    }

    // The hound looks `wearer` summoned that are still around.
    std::list<Creature*> OwnHounds(Unit* wearer)
    {
        std::list<Creature*> found;
        wearer->GetCreatureListWithEntryInGrid(found, NPC_SCARLET_TRACKING_HOUND, kLookSearchRange);
        ObjectGuid const wearerGuid = wearer->GetGUID();
        found.remove_if([wearerGuid](Creature* creature)
        {
            TempSummon const* summon = creature->ToTempSummon();
            return !creature->IsAlive() || !summon || summon->GetSummonerGUID() != wearerGuid;
        });
        return found;
    }

    void DismissOwnHounds(Unit* wearer)
    {
        for (Creature* hound : OwnHounds(wearer))
            hound->DespawnOrUnsummon();
    }

    static_assert(uint32(SPELL_AURA_PERIODIC_HEAL) == kAuraPeriodicHeal);
    static_assert(uint32(SPELL_AURA_OBS_MOD_HEALTH) == kAuraObsModHealth);

    // A spell that can heal over time (a periodic heal or OBS_MOD_HEALTH aura, Kindled Vigil's tick): its tick is a
    // heal tick (ZealotSet::IsPeriodicHealAura). A spell with both a heal and a damage over time has its damage ticks left
    // unscaled by Fervor; its heal ticks scale as heals (review n6: they used to be scaled twice, the second time with
    // the roles swapped).
    bool CanHealOverTime(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;
        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (effect.IsAura() && IsPeriodicHealAura(uint32(effect.ApplyAuraName)))
                return true;
        return false;
    }

    uint64 RawGuid(Unit const* unit)
    {
        return unit ? unit->GetGUID().GetRawValue() : 0;
    }

    // Map threads tick different maps at once; the two calls of one heal tick run back to back on one thread.
    thread_local PeriodicTick _periodicTick;

    // The amount of effect `index` of `unit`'s aura `spellId` (0 without it).
    int32 AuraAmount(Unit const* unit, uint32 spellId, uint8 index, ObjectGuid caster = ObjectGuid::Empty)
    {
        AuraEffect const* effect = unit ? unit->GetAuraEffect(spellId, index, caster) : nullptr;
        return effect ? effect->GetAmount() : 0;
    }
}

// The ten 3 pieces (212110 + 10k): the trigger line, then the set's payout.
class spell_zealot_martyr : public AuraScript
{
    PrepareAuraScript(spell_zealot_martyr);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_UNBROKEN_ZEAL_BUFF, SPELL_HOLD_THE_LINE_BUFF, SPELL_KINDLED_VIGIL_AURA,
            SPELL_KENNEL_CALL_BUFF, SPELL_LAST_PAGE_BUFF, SPELL_EXTRACT_CONFESSION_DEBUFF, SPELL_BONE_CAGE_BUFF,
            SPELL_HALLOWED_THORNS_BUFF, SPELL_ARCANISTS_WARD_ABSORB, SPELL_BLOOD_OFFERING_HEAL });
    }

    // Extract Confession's target: the wearer's (selected, else attacked), else the enemy whose hit crossed the line.
    static Unit* ConfessionTarget(Unit* wearer, Unit* attacker)
    {
        if (Unit* target = WearerTarget(wearer, kConfessionRange))
            return target;
        return IsHittableEnemy(wearer, attacker) ? attacker : nullptr;
    }

    // The unit the payout is for: the wearer after its own crossing, the healed target after a heal (the wearer too,
    // after a self-heal); nullptr when the event is neither (the proc cooldown starts only on a pass).
    Unit* Subject(ProcEventInfo& eventInfo) const
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return nullptr;
        Trigger const trigger = TriggerOf(GetId());
        if (eventInfo.GetTypeMask() & PROC_FLAG_TAKEN_DAMAGE)
        {
            DamageInfo const* damage = eventInfo.GetDamageInfo();
            if (!TriggersOnSelf(trigger) || !damage ||
                !CrossedMartyrLine(wearer->GetHealth(), damage->GetDamage(), wearer->GetMaxHealth()))
                return nullptr;
            return wearer;
        }
        if (!TriggersOnAlly(trigger) || eventInfo.GetActor() != wearer)
            return nullptr;
        // Ruling C4: any target the heal hits (the proc runs once per target, so every target of a multi-target heal
        // is checked), the wearer included, at or below 35% as the heal lands; direct heals and heal over time ticks.
        HealInfo const* heal = eventInfo.GetHealInfo();
        Unit* healed = heal ? heal->GetTarget() : nullptr;
        if (!healed || !healed->IsAlive())
            return nullptr;
        return AllyAtMartyrLine(healed->GetHealth(), heal->GetEffectiveHeal(), healed->GetMaxHealth()) ? healed :
            nullptr;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!Subject(eventInfo))
            return false;
        // A confession needs someone to confess: no enemy, no cooldown.
        return GetId() != SPELL_EXTRACT_CONFESSION || ConfessionTarget(GetTarget(), eventInfo.GetActor());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* subject = Subject(eventInfo);
        if (!subject)
            return;

        switch (GetId())
        {
            case SPELL_UNBROKEN_ZEAL:
                wearer->CastSpell(wearer, SPELL_UNBROKEN_ZEAL_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_HOLD_THE_LINE:
                wearer->CastSpell(wearer, SPELL_HOLD_THE_LINE_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_KINDLED_VIGIL:
                wearer->CastSpell(subject, SPELL_KINDLED_VIGIL_AURA, true, nullptr, aurEff);
                break;
            case SPELL_KENNEL_CALL:
                CallHounds(wearer);
                wearer->CastSpell(wearer, SPELL_KENNEL_CALL_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_LAST_PAGE:
                wearer->CastSpell(wearer, SPELL_LAST_PAGE_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_EXTRACT_CONFESSION:
                if (Unit* target = ConfessionTarget(wearer, eventInfo.GetActor()))
                    wearer->CastSpell(target, SPELL_EXTRACT_CONFESSION_DEBUFF, true, nullptr, aurEff);
                break;
            case SPELL_BONE_CAGE:
                wearer->CastSpell(wearer, SPELL_BONE_CAGE_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_HALLOWED_THORNS:
                wearer->CastSpell(subject, SPELL_HALLOWED_THORNS_BUFF, true, nullptr, aurEff);
                break;
            case SPELL_ARCANISTS_WARD:
                wearer->CastSpell(wearer, SPELL_ARCANISTS_WARD_ABSORB, true, nullptr, aurEff);
                break;
            case SPELL_BLOOD_OFFERING:
                wearer->CastSpell(subject, SPELL_BLOOD_OFFERING_HEAL, true, nullptr, aurEff);
                break;
            default:
                return;
        }
        LOG_DEBUG(kLog, "zealot-set martyr {} ({}) for {} at {}/{}", wearer->GetGUID().ToString(), GetId(),
            subject->GetGUID().ToString(), subject->GetHealth(), subject->GetMaxHealth());
    }

    // Kennel Call: two hound looks beside the wearer (a leftover pair is dismissed first).
    static void CallHounds(Unit* wearer)
    {
        DismissOwnHounds(wearer);
        SpellInfo const* buff = sSpellMgr->GetSpellInfo(SPELL_KENNEL_CALL_BUFF);
        uint32 const stayMs = uint32(buff ? buff->GetMaxDuration() : 12000) + kHoundTailMs;
        for (uint32 n = 0; n < kKennelCallHounds; ++n)
        {
            float const angle = HoundAngle(n);
            Position const beside = wearer->GetFirstCollisionPosition(kHoundFollowDistance, angle);
            if (TempSummon* hound = wearer->SummonCreature(NPC_SCARLET_TRACKING_HOUND, beside,
                TEMPSUMMON_TIMED_DESPAWN, stayMs))
            {
                hound->SetReactState(REACT_PASSIVE);
                hound->GetMotionMaster()->MoveFollow(wearer, kHoundFollowDistance, angle);
            }
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zealot_martyr::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zealot_martyr::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 212111 Unbroken Zeal: each melee ability hit heals the wearer for the aura's percent (effect 2) of its damage.
class spell_zealot_unbroken_zeal : public AuraScript
{
    PrepareAuraScript(spell_zealot_unbroken_zeal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_UNBROKEN_ZEAL_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo const* damage = eventInfo.GetDamageInfo();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return damage && damage->GetDamage() && spellInfo && !kSpellsZealotSet.Contains(spellInfo->Id) &&
            GetTarget()->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        uint32 const pct = uint32(std::max(0, aurEff->GetAmount()));
        int32 const heal = int32(PctOf(eventInfo.GetDamageInfo()->GetDamage(), pct));
        if (heal <= 0)
            return;
        wearer->CastCustomSpell(wearer, SPELL_UNBROKEN_ZEAL_HEAL, &heal, nullptr, nullptr, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zealot-set unbroken zeal {} healed {}", wearer->GetGUID().ToString(), heal);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zealot_unbroken_zeal::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zealot_unbroken_zeal::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 212131 Kindled Vigil: every 2 s the wearer (the aura's caster) burns enemies around the vigil's owner.
class spell_zealot_kindled_vigil : public AuraScript
{
    PrepareAuraScript(spell_zealot_kindled_vigil);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_KINDLED_VIGIL_BURN });
    }

    void HandleBurn(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        Unit* owner = GetTarget();
        if (!caster || !caster->IsAlive() || !owner->IsAlive() || caster->GetMap() != owner->GetMap())
            return;
        caster->CastSpell(owner->GetPositionX(), owner->GetPositionY(), owner->GetPositionZ(),
            SPELL_KINDLED_VIGIL_BURN, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zealot-set kindled vigil {} burned around {}", caster->GetGUID().ToString(),
            owner->GetGUID().ToString());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_zealot_kindled_vigil::HandleBurn, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 212141 Kennel Call: every 2 s each hound chases the wearer's target and the wearer bites it once per hound.
class spell_zealot_kennel_call : public AuraScript
{
    PrepareAuraScript(spell_zealot_kennel_call);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_KENNEL_CALL_BITE, SPELL_KENNEL_CALL_BITE_RANGED });
    }

    // The ranged bite when the wearer's ranged attack power is the higher (hunters), else the melee one.
    static uint32 BiteFor(Unit* wearer)
    {
        return wearer->GetTotalAttackPowerValue(RANGED_ATTACK) > wearer->GetTotalAttackPowerValue(BASE_ATTACK) ?
            SPELL_KENNEL_CALL_BITE_RANGED : SPELL_KENNEL_CALL_BITE;
    }

    void HandleBites(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsAlive())
            return;
        std::list<Creature*> const hounds = OwnHounds(wearer);
        Unit* target = WearerTarget(wearer, kKennelCallRange);
        if (hounds.empty())
            return;
        if (!target)
        {
            // Each hound back to its own side (review n3: a TempSummon's GetFollowAngle is Unit's 90 degrees for
            // both, so the pair would stack on one side).
            uint32 index = 0;
            for (Creature* hound : hounds)
            {
                if (hound->GetMotionMaster()->GetCurrentMovementGeneratorType() != FOLLOW_MOTION_TYPE)
                    hound->GetMotionMaster()->MoveFollow(wearer, kHoundFollowDistance, HoundAngle(index));
                ++index;
            }
            return;
        }

        uint32 const biteId = BiteFor(wearer);
        for (Creature* hound : hounds)
        {
            hound->GetMotionMaster()->MoveChase(target);
            hound->SetFacingToObject(target);
            hound->HandleEmoteCommand(EMOTE_ONESHOT_ATTACK1H);
            wearer->CastSpell(target, biteId, true, nullptr, aurEff);
        }
        LOG_DEBUG(kLog, "zealot-set kennel call {} : {} bites ({}) on {}", wearer->GetGUID().ToString(),
            hounds.size(), biteId, target->GetGUID().ToString());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        DismissOwnHounds(GetTarget());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_zealot_kennel_call::HandleBites, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_zealot_kennel_call::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 212151 Last Page: only the wearer's own spells with a cast time spend a charge (an instant keeps it).
class spell_zealot_last_page : public AuraScript
{
    PrepareAuraScript(spell_zealot_last_page);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || eventInfo.GetActor() != GetTarget() || kSpellsZealotSet.Contains(spellInfo->Id))
            return false;
        if (Spell const* spell = eventInfo.GetProcSpell(); spell && spell->IsTriggered())
            return false;
        return spellInfo->CastTimeEntry && spellInfo->CastTimeEntry->CastTime > 0;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zealot_last_page::CheckProc);
    }
};

// 212181 Hallowed Thorns: an attacker of the protected unit takes the wearer's Holy strike (the wearer's spell power,
// wherever the thorns sit).
class spell_zealot_hallowed_thorns : public AuraScript
{
    PrepareAuraScript(spell_zealot_hallowed_thorns);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_HALLOWED_THORNS_STRIKE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetCaster();
        return caster && caster->IsAlive() && IsHittableEnemy(caster, eventInfo.GetActor());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* caster = GetCaster();
        Unit* attacker = eventInfo.GetActor();
        if (!caster || !IsHittableEnemy(caster, attacker))
            return;
        caster->CastSpell(attacker, SPELL_HALLOWED_THORNS_STRIKE, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zealot-set hallowed thorns {} struck {} for {}", caster->GetGUID().ToString(),
            attacker->GetGUID().ToString(), GetTarget()->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zealot_hallowed_thorns::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zealot_hallowed_thorns::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 212191 Arcanist's Ward: absorbs 15% of maximum health; when it breaks (depleted or dispelled), expires or is
// cancelled it detonates at the wearer's spot. Never on death, nor on any other removal (logout and cleanup remove
// with AURA_REMOVE_BY_DEFAULT: review m6).
class spell_zealot_arcanists_ward : public AuraScript
{
    PrepareAuraScript(spell_zealot_arcanists_ward);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_ARCANISTS_WARD_DETONATION });
    }

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* owner = GetUnitOwner())
            amount = int32(PctOf(owner->GetMaxHealth(), kArcanistsWardHealthPct));
    }

    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        AuraRemoveMode const mode = GetTargetApplication()->GetRemoveMode();
        if ((mode != AURA_REMOVE_BY_ENEMY_SPELL && mode != AURA_REMOVE_BY_EXPIRE && mode != AURA_REMOVE_BY_CANCEL) ||
            !wearer->IsAlive() || !wearer->IsInWorld())
            return;
        wearer->CastSpell(wearer->GetPositionX(), wearer->GetPositionY(), wearer->GetPositionZ(),
            SPELL_ARCANISTS_WARD_DETONATION, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zealot-set arcanist's ward {} detonated (remove mode {})", wearer->GetGUID().ToString(),
            uint32(GetTargetApplication()->GetRemoveMode()));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_zealot_arcanists_ward::CalcAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
        AfterEffectRemove += AuraEffectRemoveFn(spell_zealot_arcanists_ward::HandleRemove, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB, AURA_EFFECT_HANDLE_REAL);
    }
};

// 212201 Blood Offering: the caster gives 10% of current health (never the last point) as the heal lands.
class spell_zealot_blood_offering : public SpellScript
{
    PrepareSpellScript(spell_zealot_blood_offering);

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsAlive())
            return;
        uint32 const cost = BloodOfferingCost(caster->GetHealth());
        if (cost)
            caster->ModifyHealth(-int32(cost));
        LOG_DEBUG(kLog, "zealot-set blood offering {} gave {} health", caster->GetGUID().ToString(), cost);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_zealot_blood_offering::HandleAfterHit);
    }
};

// Zealot's Fervor (212100-212103) and Extract Confession (212161). Fervor scales the wearer's damage done and the
// damage it takes by its own health, and its healing by the healed target's, at every hit, tick or heal (the slope:
// ZealotSet::FervorBonusBp). Extract Confession lowers the confessor's hits and ticks on the wearer, raises the
// wearer's finishing moves (and their ticks) against it, and heals the wearer for a share of them (cast on the
// wearer's next update, never inside a damage calculation).
class ZealotSetUnitHooks : public UnitScript
{
public:
    ZealotSetUnitHooks() : UnitScript("ZealotSetUnitHooks", true, { UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK, UNITHOOK_MODIFY_HEAL_RECEIVED,
        UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_PERIODIC_DAMAGE_FINAL }) { }

    // Auto attacks.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        damage = Damage(target, attacker, damage, nullptr);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage > 0)
            damage = int32(Damage(target, attacker, uint32(damage), spellInfo));
    }

    // Damage and heal ticks alike come through here (a heal tick then also calls ModifyHealReceived with the target
    // first, the reverse of a direct heal's order). A tick of a spell that can heal over time is only marked here and
    // scaled as a heal by the ModifyHealReceived call that follows it (ZealotSet::IsHealTickOf); every other tick is
    // damage.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& amount,
        SpellInfo const* spellInfo) override
    {
        _periodicTick = PeriodicTick{};
        if (CanHealOverTime(spellInfo))
        {
            _periodicTick = PeriodicTick{ RawGuid(target), RawGuid(attacker), spellInfo->Id, true };
            return;
        }
        amount = Damage(target, attacker, amount, spellInfo);
    }

    // A direct heal: HealBySpell passes the healer first (`this`), then the target. A heal tick: the target first, then
    // the caster, right after the marked ModifyPeriodicDamageAurasTick call.
    void ModifyHealReceived(Unit* first, Unit* second, uint32& heal, SpellInfo const* spellInfo) override
    {
        PeriodicTick const tick = _periodicTick;
        _periodicTick = PeriodicTick{};
        if (spellInfo && IsHealTickOf(tick, RawGuid(first), RawGuid(second), spellInfo->Id))
            heal = Heal(second, first, heal);
        else
            heal = Heal(first, second, heal);
    }

    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/) override
    {
        if (damage > 0)
            ConfessionHeal(target, attacker, uint32(damage), spellInfo);
    }

    void OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/) override
    {
        ConfessionHeal(target, attacker, damage, spellInfo);
    }

private:
    static bool IsFinisher(SpellInfo const* spellInfo)
    {
        return spellInfo && spellInfo->NeedsComboPoints() && !kSpellsZealotSet.Contains(spellInfo->Id);
    }

    static uint32 Damage(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo)
    {
        if (!damage || !target || !attacker || target == attacker)
            return damage;

        // The attacker's side: Fervor on its own health, a finishing move against its confessor.
        if (Player const* player = attacker->ToPlayer())
        {
            int32 const fervor = std::max(AuraAmount(player, SPELL_FERVOR_DAMAGE, EFFECT_0),
                AuraAmount(player, SPELL_FERVOR_HYBRID, EFFECT_0));
            damage = ApplyBp(damage, FervorBonusBp(fervor, player->GetHealth(), player->GetMaxHealth()), true);
            if (IsFinisher(spellInfo))
            {
                int32 const more = AuraAmount(target, SPELL_EXTRACT_CONFESSION_DEBUFF, EFFECT_1, player->GetGUID());
                if (more > 0)
                    damage = ApplyBp(damage, uint32(more) * 100, true);
            }
        }

        // The target's side: a tank's Fervor on its own health, its confessor's hits.
        if (Player const* player = target->ToPlayer())
        {
            int32 const fervor = AuraAmount(player, SPELL_FERVOR_TANK, EFFECT_0);
            damage = ApplyBp(damage, FervorBonusBp(fervor, player->GetHealth(), player->GetMaxHealth()), false);
            int32 const less = AuraAmount(attacker, SPELL_EXTRACT_CONFESSION_DEBUFF, EFFECT_0, player->GetGUID());
            if (less > 0)
                damage = ApplyBp(damage, uint32(less) * 100, false);
        }
        return damage;
    }

    static uint32 Heal(Unit* healer, Unit* target, uint32 heal)
    {
        Player const* player = healer ? healer->ToPlayer() : nullptr;
        if (!heal || !player || !target)
            return heal;
        int32 const fervor = std::max(AuraAmount(player, SPELL_FERVOR_HEALING, EFFECT_0),
            AuraAmount(player, SPELL_FERVOR_HYBRID, EFFECT_1));
        return ApplyBp(heal, FervorBonusBp(fervor, target->GetHealth(), target->GetMaxHealth()), true);
    }

    // Extract Confession: the wearer's finishing move (or its tick) on its confessor heals the wearer for a share.
    static void ConfessionHeal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo)
    {
        Player* player = attacker ? attacker->ToPlayer() : nullptr;
        if (!damage || !player || !target || !IsFinisher(spellInfo))
            return;
        int32 const pct = AuraAmount(target, SPELL_EXTRACT_CONFESSION_DEBUFF, EFFECT_2, player->GetGUID());
        if (pct <= 0)
            return;
        int32 const heal = int32(PctOf(damage, uint32(pct)));
        if (heal <= 0)
            return;
        ObjectGuid const playerGuid = player->GetGUID();
        player->m_Events.AddEventAtOffset([playerGuid, heal]()
        {
            Player* wearer = ObjectAccessor::FindPlayer(playerGuid);
            if (!wearer || !wearer->IsInWorld() || !wearer->IsAlive())
                return;
            wearer->CastCustomSpell(wearer, SPELL_EXTRACT_CONFESSION_HEAL, &heal, nullptr, nullptr, true);
            LOG_DEBUG(kLog, "zealot-set extract confession {} healed {}", wearer->GetGUID().ToString(), heal);
        }, Milliseconds(0));
    }
};

void AddSC_zealot_set_bonuses()
{
    RegisterSpellScript(spell_zealot_martyr);
    RegisterSpellScript(spell_zealot_unbroken_zeal);
    RegisterSpellScript(spell_zealot_kindled_vigil);
    RegisterSpellScript(spell_zealot_kennel_call);
    RegisterSpellScript(spell_zealot_last_page);
    RegisterSpellScript(spell_zealot_hallowed_thorns);
    RegisterSpellScript(spell_zealot_arcanists_ward);
    RegisterSpellScript(spell_zealot_blood_offering);
    new ZealotSetUnitHooks();
}
