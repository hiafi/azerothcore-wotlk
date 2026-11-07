/*
 * mod-dungeon-bosses, dungeon sets: the Haunted set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Haunted set
 * bonuses", approved 2026-11-06). The spells are apps/dbc-tools/source/items/haunted_set_bonuses.py; every damage and
 * heal number comes from potency or a percent of health, so nothing here sizes a payout. Set bonuses are applied by
 * the item set (AddItemsSetItem), with no cast item, so `Aura::CalcProcChance` already multiplies a spell_proc chance
 * by Proc Chance; a roll a script makes itself multiplies it here (`RollSetChance`).
 *
 *   spell_haunted_wraith_volley        205700 Magister's 3 piece: a damaging cast 10%, a periodic damage tick 4%;
 *                                      bolts 205701 at the target and up to 2 other enemies within 10 yd.
 *   spell_haunted_wraith_volley_bolt   205701: with the 5 piece 205702, Soul Rend 205703 on every enemy it hits.
 *   spell_haunted_wraith_of_solace     205712 Devout 5 piece: a direct heal cast heals the most injured ally within
 *                                      30 yd other than its target (205713).
 *   spell_haunted_grave_bloom          205721 Wildheart 5 piece: a periodic tick repeats on a second target within
 *                                      15 yd (205722 heal, 205723 damage, the tick's amount).
 *   spell_haunted_frozen_chorus        205730 The Elements 3 piece: a damaging cast or a direct heal arcs 205731 or
 *                                      205732.
 *   spell_haunted_frozen_chorus_payout 205731 / 205732: Gathering Chorus 205734 stacks make it stronger, then go.
 *   spell_haunted_unbroken_faith       205740 Lightforge 3 piece: 205741 while above 80% mana.
 *   spell_haunted_soul_released        205742 Lightforge 5 piece: heals the most injured ally (205743) and strikes the
 *                                      nearest enemy (205744).
 *   spell_haunted_bone_shatter         205750 Valor 3 piece: shards 205751 around the ability's target; Broken Bones
 *                                      205753 with the 5 piece 205752.
 *   spell_haunted_grasp_of_the_dead    205762 Beaststalker's 5 piece: 205763 after a melee ability, 205764 (ranged
 *                                      attack power) after a ranged one.
 *   spell_haunted_bone_ward            205782 Protector's 5 piece: the ward absorbs 3% of maximum health per stack.
 *   spell_haunted_deathless            205792 Shadowguard 5 piece: only the hit that crosses 35% health.
 *   HauntedSetSpellHooks               205720 Wildheart 3 piece (Lingering Death): periodic damage and heal auras of
 *                                      the wearer last 10% longer (OnCalcMaxDuration).
 *   HauntedSetUnitHooks                205761 Haunting Mark (Beaststalker's 3 piece): the next ability of the marker
 *                                      deals 15% more and consumes it. 205770 / 205772 Shadowcraft: Wraith Venom and
 *                                      Grave Rot roll on the wearer's poison hits and bleed ticks.
 *
 * Every effect logs one DEBUG line, "haunted-set <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "HauntedSetLogic.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <mutex>
#include <unordered_map>

using namespace HauntedSet;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    float ProcChanceOf(Unit const* unit)
    {
        Player const* player = unit ? unit->ToPlayer() : nullptr;
        return player ? player->GetProcChancePercentage() : 0.0f;
    }

    // A script's own roll: the flat chance times Proc Chance.
    bool RollSetChance(Unit const* unit, int32 basePct)
    {
        return roll_chance_f(ProcChancePct(float(basePct), ProcChanceOf(unit)));
    }

    bool IsDamagingSpell(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;
        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_HEALTH_LEECH:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    return true;
                default:
                    break;
            }
            if (effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE) || effect.IsAura(SPELL_AURA_PERIODIC_LEECH) ||
                effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE_PERCENT))
                return true;
        }
        return false;
    }

    bool IsDirectHeal(SpellInfo const* spellInfo)
    {
        return spellInfo && spellInfo->HasEffect(SPELL_EFFECT_HEAL);
    }

    bool HasPeriodicDamageOrHeal(SpellInfo const* spellInfo)
    {
        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE) || effect.IsAura(SPELL_AURA_PERIODIC_LEECH) ||
                effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE_PERCENT) || effect.IsAura(SPELL_AURA_PERIODIC_HEAL))
                return true;
        return false;
    }

    // A bleed: the bleed mechanic (rogue Garrote and Rupture, cat Rake and Rip) or one of the rogue rework's bleeds
    // (Rogue::IsRogueBleed, Hemorrhage's included).
    bool IsBleed(SpellInfo const* spellInfo)
    {
        return spellInfo && ((spellInfo->GetAllEffectsMechanicMask() & (1ULL << MECHANIC_BLEED)) ||
            Rogue::IsRogueBleed(spellInfo));
    }

    // The unit a proc event is about: the hit's target, or a cast-phase event's explicit unit target (the cast phase
    // runs before any hit, so it has no action target).
    Unit* EventTarget(ProcEventInfo& eventInfo)
    {
        if (Unit* target = eventInfo.GetActionTarget())
            return target;
        if (Spell const* spell = eventInfo.GetProcSpell())
            return spell->m_targets.GetUnitTarget();
        return nullptr;
    }

    // Living enemies of `attacker` within `radius` yards of `center`, in combat (a bonus never pulls a pack) and valid
    // attack targets.
    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* attacker, float radius)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, attacker, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, found, check);
        Cell::VisitObjects(center, searcher, radius);
        found.remove_if([attacker](Unit* unit)
        {
            return !unit->IsAlive() || !unit->IsInCombat() || !attacker->IsValidAttackTarget(unit);
        });
        return found;
    }

    Unit* NearestEnemy(WorldObject* center, Unit* attacker, float radius, Unit const* except)
    {
        Unit* best = nullptr;
        for (Unit* enemy : EnemiesNear(center, attacker, radius))
        {
            if (enemy == except)
                continue;
            if (!best || center->GetExactDist(enemy) < center->GetExactDist(best))
                best = enemy;
        }
        return best;
    }

    // The most injured (lowest health fraction) living group member, or the player alone, within `range` yards of
    // `center`, other than `except`; nullptr when nobody is hurt.
    Player* MostInjuredAlly(Player* player, WorldObject const* center, float range, Unit const* except)
    {
        Player* best = nullptr;
        auto consider = [&](Player* member)
        {
            if (!member || member == except || !member->IsInWorld() || !member->IsAlive() ||
                member->GetMap() != player->GetMap() || !center->IsWithinDistInMap(member, range))
                return;
            if (member->GetHealth() >= member->GetMaxHealth())
                return;
            if (!best || MoreInjured(member->GetHealth(), member->GetMaxHealth(), best->GetHealth(),
                    best->GetMaxHealth()))
                best = member;
        };
        if (Group* group = player->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                consider(ref->GetSource());
        }
        else
            consider(player);
        return best;
    }
}

// 205700 Wraith Volley (Magister's 3 piece): a damaging spell cast rolls 10%, a periodic damage tick 4%, both times
// Proc Chance. The spell_proc row is 100% with the 4 s internal cooldown, so the cooldown starts only on a success.
class spell_haunted_wraith_volley : public AuraScript
{
    PrepareAuraScript(spell_haunted_wraith_volley);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WRAITH_VOLLEY_BOLT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        bool const periodic = eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC;
        // One roll per cast: a cast counts in its cast phase only (its hits are the same cast again).
        if (!periodic && (!(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST) ||
            !IsDamagingSpell(eventInfo.GetSpellInfo())))
            return false;
        Unit* target = EventTarget(eventInfo);
        if (!target || target == caster || !target->IsAlive() || !caster->IsValidAttackTarget(target))
            return false;
        _target = target->GetGUID();
        return RollSetChance(caster, WraithVolleyBasePct(periodic));
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* caster = GetTarget();
        Unit* target = ObjectAccessor::GetUnit(*caster, _target);
        if (!target || !target->IsAlive())
            return;

        caster->CastSpell(target, SPELL_WRAITH_VOLLEY_BOLT, true, nullptr, aurEff);
        std::list<Unit*> others = EnemiesNear(target, caster, kWraithVolleyRadius);
        others.remove(target);
        others.sort([target](Unit const* a, Unit const* b)
        {
            return target->GetExactDist(a) < target->GetExactDist(b);
        });
        uint32 count = 0;
        for (Unit* other : others)
        {
            if (count++ >= kWraithVolleyExtraTargets)
                break;
            caster->CastSpell(other, SPELL_WRAITH_VOLLEY_BOLT, true, nullptr, aurEff);
        }
        LOG_DEBUG(kLog, "haunted-set wraith volley {} at {} (+{} more)", caster->GetGUID().ToString(),
            target->GetGUID().ToString(), std::min<uint32>(count, kWraithVolleyExtraTargets));
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_wraith_volley::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_wraith_volley::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _target;
};

// 205701 Wraith Volley bolt: with the Magister's 5 piece (Soul Rend 205702), every enemy it hits is vulnerable to the
// caster's spells (205703, refreshed by the next bolt).
class spell_haunted_wraith_volley_bolt : public SpellScript
{
    PrepareSpellScript(spell_haunted_wraith_volley_bolt);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_SOUL_REND_DEBUFF });
    }

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !target->IsAlive() || !caster->HasAura(SPELL_SOUL_REND))
            return;
        caster->CastSpell(target, SPELL_SOUL_REND_DEBUFF, true);
        LOG_DEBUG(kLog, "haunted-set soul rend {} on {}", caster->GetGUID().ToString(), target->GetGUID().ToString());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_haunted_wraith_volley_bolt::HandleHit);
    }
};

// 205712 Wraith of Solace (Devout 5 piece): a direct heal cast (cast phase, one roll a cast) heals the most injured
// ally within 30 yd other than the heal's target. The ally is picked before the roll: no hurt ally, no cooldown.
class spell_haunted_wraith_of_solace : public AuraScript
{
    PrepareAuraScript(spell_haunted_wraith_of_solace);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_WRAITH_OF_SOLACE_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* healer = GetTarget()->ToPlayer();
        if (!healer || !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST) ||
            !IsDirectHeal(eventInfo.GetSpellInfo()))
            return false;
        Unit* healed = EventTarget(eventInfo);
        Player* ally = MostInjuredAlly(healer, healer, kSolaceRange, healed ? healed : healer);
        if (!ally)
            return false;
        _ally = ally->GetGUID();
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* ally = ObjectAccessor::GetUnit(*healer, _ally);
        if (!ally || !ally->IsAlive())
            return;
        healer->CastSpell(ally, SPELL_WRAITH_OF_SOLACE_HEAL, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set wraith of solace {} healed {}", healer->GetGUID().ToString(),
            ally->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_wraith_of_solace::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_wraith_of_solace::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _ally;
};

// 205721 Grave Bloom (Wildheart 5 piece): a periodic tick repeats on a second target within 15 yd of the first, the
// most injured ally for a heal tick, the nearest other enemy in combat for a damage tick. The repeat carries the tick's
// amount (205722 / 205723 are DefenseType NONE: no second spell power or done bonus).
class spell_haunted_grave_bloom : public AuraScript
{
    PrepareAuraScript(spell_haunted_grave_bloom);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_GRAVE_BLOOM_HEAL, SPELL_GRAVE_BLOOM_DAMAGE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* wearer = GetTarget()->ToPlayer();
        Unit* first = eventInfo.GetActionTarget();
        if (!wearer || !first)
            return false;
        Unit* second = nullptr;
        if (HealInfo const* heal = eventInfo.GetHealInfo(); heal && heal->GetHeal() > 0)
        {
            second = MostInjuredAlly(wearer, first, kGraveBloomRadius, first);
            _heal = true;
            _amount = int32(std::min<uint32>(heal->GetHeal(), 0x7FFFFFFFu));
        }
        else if (DamageInfo const* damage = eventInfo.GetDamageInfo(); damage && damage->GetDamage() > 0)
        {
            second = NearestEnemy(first, wearer, kGraveBloomRadius, first);
            _heal = false;
            _amount = int32(std::min<uint32>(damage->GetDamage(), 0x7FFFFFFFu));
        }
        if (!second)
            return false;
        _second = second->GetGUID();
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* second = ObjectAccessor::GetUnit(*wearer, _second);
        if (!second || !second->IsAlive() || _amount <= 0)
            return;
        int32 const amount = _amount;
        uint32 const spellId = _heal ? SPELL_GRAVE_BLOOM_HEAL : SPELL_GRAVE_BLOOM_DAMAGE;
        wearer->CastCustomSpell(second, spellId, &amount, nullptr, nullptr, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set grave bloom {} repeated a {} tick of {} on {}", wearer->GetGUID().ToString(),
            _heal ? "heal" : "damage", amount, second->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_grave_bloom::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_grave_bloom::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _second;
    int32 _amount = 0;
    bool _heal = false;
};

// 205730 Frozen Chorus (The Elements 3 piece): a damaging spell cast arcs 205731 from its enemy target, a direct heal
// cast arcs 205732 from its ally target (spell_proc: cast phase, 10%, 6 s internal cooldown).
class spell_haunted_frozen_chorus : public AuraScript
{
    PrepareAuraScript(spell_haunted_frozen_chorus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_FROZEN_CHORUS_DAMAGE, SPELL_FROZEN_CHORUS_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST) || !spellInfo)
            return false;
        Unit* target = EventTarget(eventInfo);
        if (!target)
            target = caster;  // a self-cast heal names no unit target
        if (!target->IsAlive())
            return false;
        if (IsDirectHeal(spellInfo) && caster->IsFriendlyTo(target))
            _heal = true;
        else if (IsDamagingSpell(spellInfo) && caster->IsValidAttackTarget(target))
            _heal = false;
        else
            return false;
        _target = target->GetGUID();
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* caster = GetTarget();
        Unit* target = ObjectAccessor::GetUnit(*caster, _target);
        if (!target || !target->IsAlive())
            return;
        caster->CastSpell(target, _heal ? SPELL_FROZEN_CHORUS_HEAL : SPELL_FROZEN_CHORUS_DAMAGE, true, nullptr,
            aurEff);
        LOG_DEBUG(kLog, "haunted-set frozen chorus {} {} from {}", caster->GetGUID().ToString(),
            _heal ? "heal" : "damage", target->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_frozen_chorus::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_frozen_chorus::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _target;
    bool _heal = false;
};

// 205731 / 205732 Frozen Chorus payout: the Gathering Chorus stacks (205734, The Elements 5 piece) make every target
// of this chorus 20% stronger per stack, and the chorus consumes them all as it is cast.
class spell_haunted_frozen_chorus_payout : public SpellScript
{
    PrepareSpellScript(spell_haunted_frozen_chorus_payout);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_GATHERING_CHORUS_STACK });
    }

    void HandleCast()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        Aura* stacks = caster->GetAura(SPELL_GATHERING_CHORUS_STACK);
        if (!stacks)
            return;
        SpellInfo const* stackInfo = sSpellMgr->GetSpellInfo(SPELL_GATHERING_CHORUS_STACK);
        int32 const perStack = stackInfo ? stackInfo->Effects[EFFECT_0].CalcValue() : 0;
        _pct = GatheringChorusPct(stacks->GetStackAmount(), perStack);
        LOG_DEBUG(kLog, "haunted-set gathering chorus {} spent {} stack(s): {}%", caster->GetGUID().ToString(),
            stacks->GetStackAmount(), _pct);
        stacks->Remove();
    }

    void HandleHit()
    {
        if (_pct == 100)
            return;
        if (GetSpellInfo()->Id == SPELL_FROZEN_CHORUS_HEAL)
            SetHitHeal(ScalePct(GetHitHeal(), _pct));
        else
            SetHitDamage(ScalePct(GetHitDamage(), _pct));
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_haunted_frozen_chorus_payout::HandleCast);
        OnHit += SpellHitFn(spell_haunted_frozen_chorus_payout::HandleHit);
    }

    int32 _pct = 100;
};

// 205740 Unbroken Faith (Lightforge 3 piece): every second, 205741 is on the wearer while mana is above 80% and gone
// otherwise; it goes with the bonus.
class spell_haunted_unbroken_faith : public AuraScript
{
    PrepareAuraScript(spell_haunted_unbroken_faith);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_UNBROKEN_FAITH_BUFF });
    }

    void HandleCheck(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        bool const holds = wearer->IsAlive() &&
            UnbrokenFaithHolds(wearer->GetPower(POWER_MANA), wearer->GetMaxPower(POWER_MANA));
        bool const has = wearer->HasAura(SPELL_UNBROKEN_FAITH_BUFF);
        if (holds && !has)
            wearer->CastSpell(wearer, SPELL_UNBROKEN_FAITH_BUFF, true, nullptr, aurEff);
        else if (!holds && has)
            wearer->RemoveAurasDueToSpell(SPELL_UNBROKEN_FAITH_BUFF);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(SPELL_UNBROKEN_FAITH_BUFF);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_haunted_unbroken_faith::HandleCheck, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_haunted_unbroken_faith::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 205742 Soul Released (Lightforge 5 piece): a direct heal or Holy damage spell cast frees a soul that heals the most
// injured ally within 30 yd (205743) and strikes the nearest enemy in combat within 20 yd (205744). Either half alone
// when the other has no target; neither, no roll.
class spell_haunted_soul_released : public AuraScript
{
    PrepareAuraScript(spell_haunted_soul_released);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_SOUL_RELEASED_HEAL, SPELL_SOUL_RELEASED_DAMAGE });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* wearer = GetTarget()->ToPlayer();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!wearer || !spellInfo || !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST))
            return false;
        bool const holyDamage = (spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_HOLY) && IsDamagingSpell(spellInfo);
        if (!IsDirectHeal(spellInfo) && !holyDamage)
            return false;
        Player* ally = MostInjuredAlly(wearer, wearer, kSoulReleasedHealRange, nullptr);
        Unit* enemy = NearestEnemy(wearer, wearer, kSoulReleasedEnemyRange, nullptr);
        _ally = ally ? ally->GetGUID() : ObjectGuid::Empty;
        _enemy = enemy ? enemy->GetGUID() : ObjectGuid::Empty;
        return ally || enemy;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        if (Unit* ally = ObjectAccessor::GetUnit(*wearer, _ally); ally && ally->IsAlive())
            wearer->CastSpell(ally, SPELL_SOUL_RELEASED_HEAL, true, nullptr, aurEff);
        if (Unit* enemy = ObjectAccessor::GetUnit(*wearer, _enemy); enemy && enemy->IsAlive())
            wearer->CastSpell(enemy, SPELL_SOUL_RELEASED_DAMAGE, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set soul released {}: ally {} enemy {}", wearer->GetGUID().ToString(),
            _ally.ToString(), _enemy.ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_soul_released::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_soul_released::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _ally;
    ObjectGuid _enemy;
};

// 205750 Bone Shatter (Valor 3 piece): a melee ability cast (cast phase: one roll per ability, a cleave included)
// bursts 205751 around its target; with the 5 piece (Broken Bones 205752) the wearer also gains 205753.
class spell_haunted_bone_shatter : public AuraScript
{
    PrepareAuraScript(spell_haunted_bone_shatter);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_BONE_SHATTER_BURST, SPELL_BROKEN_BONES_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        if (!(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST))
            return false;
        Unit* target = EventTarget(eventInfo);
        if (!target || target == wearer)
            target = wearer->GetVictim();  // a self-targeted ability (Whirlwind, Thunder Clap)
        if (!target || !target->IsAlive() || !wearer->IsValidAttackTarget(target))
            return false;
        _target = target->GetGUID();
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* target = ObjectAccessor::GetUnit(*wearer, _target);
        if (!target || !target->IsAlive())
            return;
        wearer->CastSpell(target, SPELL_BONE_SHATTER_BURST, true, nullptr, aurEff);
        bool const brokenBones = wearer->HasAura(SPELL_BROKEN_BONES);
        if (brokenBones)
            wearer->CastSpell(wearer, SPELL_BROKEN_BONES_BUFF, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set bone shatter {} at {}{}", wearer->GetGUID().ToString(),
            target->GetGUID().ToString(), brokenBones ? " + broken bones" : "");
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_bone_shatter::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_bone_shatter::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _target;
};

// 205762 Grasp of the Dead (Beaststalker's 5 piece): the claw after a ranged ability is 205764 (ranged attack power),
// after a melee one 205763.
class spell_haunted_grasp_of_the_dead : public AuraScript
{
    PrepareAuraScript(spell_haunted_grasp_of_the_dead);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_GRASP_OF_THE_DEAD_MELEE, SPELL_GRASP_OF_THE_DEAD_RANGED });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = eventInfo.GetActionTarget();
        return target && target->IsAlive() && GetTarget()->IsValidAttackTarget(target);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        if (!target)
            return;
        SpellInfo const* ability = eventInfo.GetSpellInfo();
        bool const ranged = ability && ability->DmgClass == SPELL_DAMAGE_CLASS_RANGED;
        wearer->CastSpell(target, ranged ? SPELL_GRASP_OF_THE_DEAD_RANGED : SPELL_GRASP_OF_THE_DEAD_MELEE, true,
            nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set grasp of the dead {} ({}) on {}", wearer->GetGUID().ToString(),
            ranged ? "ranged" : "melee", target->GetGUID().ToString());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_grasp_of_the_dead::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_grasp_of_the_dead::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 205782 Bone Ward (Protector's 5 piece): each stack absorbs 3% of the wearer's maximum health (the engine multiplies
// the amount by the stacks and recalculates it on a restack, so the ward is full again).
class spell_haunted_bone_ward : public AuraScript
{
    PrepareAuraScript(spell_haunted_bone_ward);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;
        if (Unit* owner = GetUnitOwner())
            amount = BoneWardAmount(owner->GetMaxHealth(), 1);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_haunted_bone_ward::CalcAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// 205792 Deathless (Shadowguard 5 piece): only the hit that takes the wearer from 35% health or more to below 35%
// (alive) passes, so the 60 s internal cooldown starts only then.
class spell_haunted_deathless : public AuraScript
{
    PrepareAuraScript(spell_haunted_deathless);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DEATHLESS_HOT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        DamageInfo const* damage = eventInfo.GetDamageInfo();
        return damage && wearer->IsAlive() &&
            DeathlessCrossed(wearer->GetHealth(), damage->GetDamage(), wearer->GetMaxHealth());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        wearer->CastSpell(wearer, SPELL_DEATHLESS_HOT, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "haunted-set deathless {} at {}/{}", wearer->GetGUID().ToString(), wearer->GetHealth(),
            wearer->GetMaxHealth());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_haunted_deathless::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_haunted_deathless::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 205720 Lingering Death (Wildheart 3 piece): every periodic damage, leech or heal aura the wearer casts (not a
// channel, not a passive) lasts 10% longer, on creation and on every refresh. The engine folds the part of a tick
// that does not fit into the last tick (AuraEffect::GetFinalTickBonusMultiplier), so 10% longer is 10% more.
class HauntedSetSpellHooks : public AllSpellScript
{
public:
    HauntedSetSpellHooks() : AllSpellScript("HauntedSetSpellHooks", { ALLSPELLHOOK_ON_CALC_MAX_DURATION }) { }

    void OnCalcMaxDuration(Aura const* aura, int32& maxDuration) override
    {
        if (maxDuration <= 0 || !aura)
            return;
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (spellInfo->IsPassive() || spellInfo->IsChanneled() || !HasPeriodicDamageOrHeal(spellInfo))
            return;
        Unit* caster = aura->GetCaster();
        if (!caster || !caster->IsPlayer() || !caster->HasAura(SPELL_LINGERING_DEATH))
            return;
        maxDuration = LingeringDeathDuration(maxDuration);
    }
};

// 205761 Haunting Mark (Beaststalker's 3 piece): the marker's next melee or ranged ability against the marked target
// deals the mark's amount (15%) more and consumes the mark. The ability that marked gains nothing: the mark lands
// after its damage. The set's own payouts never consume it.
// 205770 Wraith Venom / 205772 Grave Rot (Shadowcraft 3 and 5 piece): poisons roll nothing by the shared rogue rule,
// so the rolls happen here, on every rogue poison damage hit (direct and periodic, Instant Poison included) and every
// bleed tick the wearer deals, times Proc Chance, with an internal cooldown kept as a spell cooldown on the bonus id.
// The casts wait for the wearer's next update (never inside a damage calculation).
class HauntedSetUnitHooks : public UnitScript
{
public:
    HauntedSetUnitHooks() : UnitScript("HauntedSetUnitHooks", true, { UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
        UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_PERIODIC_DAMAGE_FINAL }) { }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage <= 0 || !target || !attacker || !spellInfo || !attacker->IsPlayer() ||
            kSpellsHauntedSet.Contains(spellInfo->Id))
            return;
        if (spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE && spellInfo->DmgClass != SPELL_DAMAGE_CLASS_RANGED)
            return;
        Aura* mark = target->GetAura(SPELL_HAUNTING_MARK_DEBUFF, attacker->GetGUID());
        if (!mark)
            return;
        AuraEffect const* effect = mark->GetEffect(EFFECT_0);
        int32 const pct = 100 + (effect ? effect->GetAmount() : 0);
        damage = ScalePct(damage, pct);
        mark->Remove();
        LOG_DEBUG(kLog, "haunted-set haunting mark {} consumed on {}: {} ({}%)", attacker->GetGUID().ToString(),
            target->GetGUID().ToString(), damage, pct);
    }

    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/) override
    {
        if (damage > 0 && Rogue::IsRoguePoisonDamage(spellInfo))
            Wound(target, attacker);
    }

    void OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo,
        bool /*isCrit*/) override
    {
        if (damage > 0 && spellInfo && (IsBleed(spellInfo) || Rogue::IsRoguePoisonDamage(spellInfo)))
            Wound(target, attacker);
    }

private:
    // A poison hit or bleed tick of `attacker` on `target`.
    static void Wound(Unit* target, Unit* attacker)
    {
        Player* player = attacker ? attacker->ToPlayer() : nullptr;
        if (!player || !target || !target->IsAlive())
            return;
        bool const venom = player->HasAura(SPELL_WRAITH_VENOM) && !player->HasSpellCooldown(SPELL_WRAITH_VENOM) &&
            RollSetChance(player, kWraithVenomPct);
        bool const rot = player->HasAura(SPELL_GRAVE_ROT) && !player->HasSpellCooldown(SPELL_GRAVE_ROT) &&
            RollSetChance(player, kGraveRotPct);
        if (!venom && !rot)
            return;
        if (venom)
            player->AddSpellCooldown(SPELL_WRAITH_VENOM, 0, kWraithVenomCooldownMs);
        if (rot)
            player->AddSpellCooldown(SPELL_GRAVE_ROT, 0, kGraveRotCooldownMs);

        ObjectGuid const playerGuid = player->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        player->m_Events.AddEventAtOffset([playerGuid, targetGuid, venom, rot]()
        {
            Player* wearer = ObjectAccessor::FindPlayer(playerGuid);
            if (!wearer || !wearer->IsInWorld())
                return;
            Unit* victim = ObjectAccessor::GetUnit(*wearer, targetGuid);
            if (!victim || !victim->IsAlive())
                return;
            if (venom)
                wearer->CastSpell(victim, SPELL_WRAITH_VENOM_DOT, true);
            if (rot)
            {
                wearer->CastSpell(victim, SPELL_GRAVE_ROT_STRIKE, true);
                ExtendWounds(wearer, victim);
            }
            LOG_DEBUG(kLog, "haunted-set shadowcraft {} on {}:{}{}", wearer->GetGUID().ToString(),
                victim->GetGUID().ToString(), venom ? " wraith venom" : "", rot ? " grave rot" : "");
        }, Milliseconds(0));
    }

    // Grave Rot: the wearer's bleeds, damage-over-time poisons and Wraith Venom on `victim` last 2 s longer (the
    // maximum duration too, so the engine's last-tick fold stays right), at most 6 s per application (user ruling
    // 2026-11-06): a refresh or a reapplication starts a fresh 6 s.
    static void ExtendWounds(Player* wearer, Unit* victim)
    {
        for (auto const& [spellId, application] : victim->GetAppliedAuras())
        {
            Aura* aura = application->GetBase();
            if (aura->GetCasterGUID() != wearer->GetGUID() || aura->IsPermanent())
                continue;
            SpellInfo const* spellInfo = aura->GetSpellInfo();
            bool const wound = spellId == SPELL_WRAITH_VENOM_DOT || (HasPeriodicDamageOrHeal(spellInfo) &&
                (IsBleed(spellInfo) || Rogue::IsRoguePoisonDamage(spellInfo)));
            if (!wound)
                continue;
            ExtendOne(aura, victim->GetGUID(), wearer->GetGUID(), spellId);
        }
    }

    static uint32 TickNumberOf(Aura const* aura)
    {
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i); effect && effect->GetAmplitude())
                return effect->GetTickNumber();
        return 0;
    }

    static void ExtendOne(Aura* aura, ObjectGuid victim, ObjectGuid caster, uint32 spellId)
    {
        WoundKey const key{ victim.GetRawValue(), caster.GetRawValue(), spellId };
        int64 const applyTime = int64(aura->GetApplyTime());
        uint32 const tick = TickNumberOf(aura);
        std::lock_guard<std::mutex> guard(_woundsLock);
        if (_wounds.size() > kMaxTrackedWounds)
            _wounds.clear();  // stale records of auras long gone; a cleared record only resets a budget early
        auto found = _wounds.find(key);
        int32 const soFar = GraveRotExtendedSoFar(found != _wounds.end() ? &found->second : nullptr, applyTime,
            aura->GetMaxDuration(), tick);
        int32 const grant = GraveRotGrantMs(soFar);
        if (grant <= 0)
            return;
        aura->SetMaxDuration(aura->GetMaxDuration() + grant);
        aura->SetDuration(aura->GetDuration() + grant);
        _wounds[key] = GraveRotRecord{ applyTime, aura->GetMaxDuration(), tick, soFar + grant };
    }

    struct WoundKey
    {
        uint64 victim;
        uint64 caster;
        uint32 spellId;

        bool operator==(WoundKey const& other) const
        {
            return victim == other.victim && caster == other.caster && spellId == other.spellId;
        }
    };

    struct WoundKeyHash
    {
        std::size_t operator()(WoundKey const& key) const
        {
            return std::hash<uint64>()(key.victim) ^ (std::hash<uint64>()(key.caster) << 1) ^
                (std::hash<uint32>()(key.spellId) << 2);
        }
    };

    static constexpr std::size_t kMaxTrackedWounds = 4096;
    // Map threads may update different maps at once, so the records sit behind a lock.
    static inline std::mutex _woundsLock;
    static inline std::unordered_map<WoundKey, GraveRotRecord, WoundKeyHash> _wounds;
};

void AddSC_haunted_set_bonuses()
{
    RegisterSpellScript(spell_haunted_wraith_volley);
    RegisterSpellScript(spell_haunted_wraith_volley_bolt);
    RegisterSpellScript(spell_haunted_wraith_of_solace);
    RegisterSpellScript(spell_haunted_grave_bloom);
    RegisterSpellScript(spell_haunted_frozen_chorus);
    RegisterSpellScript(spell_haunted_frozen_chorus_payout);
    RegisterSpellScript(spell_haunted_unbroken_faith);
    RegisterSpellScript(spell_haunted_soul_released);
    RegisterSpellScript(spell_haunted_bone_shatter);
    RegisterSpellScript(spell_haunted_grasp_of_the_dead);
    RegisterSpellScript(spell_haunted_bone_ward);
    RegisterSpellScript(spell_haunted_deathless);
    new HauntedSetSpellHooks();
    new HauntedSetUnitHooks();
}
