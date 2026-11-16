/*
 * mod-dungeon-bosses, dungeon sets: the Molten set bonuses (docs/dungeons/dungeon-loot-vanilla.md "Molten set
 * bonuses", approved 2026-11-06). The spells are apps/dbc-tools/source/items/molten_set_bonuses.py; every damage and
 * heal number comes from potency or the spell data, so nothing here sizes a payout. Heat is a count, never a chance:
 * no script here rolls, and every Heat proc row is 100%. Heat builds only while the wearer is in combat (the buff's
 * LEAVE_COMBAT interrupt clears it on leaving), and an eruption's fallback enemy (victim, selection) must already be in
 * combat, so a bonus never pulls.
 *
 *   spell_molten_heat                  the ten 3 pieces (206900 + 10k): one Heat gain per event (MoltenSet::HeatGain,
 *                                      once per cast), the Heat buff's stacks (AddHeat), the set's eruption at its
 *                                      count (Erupt).
 *   spell_molten_cooldown_heat         206901 Flare-up, 206931 Thunderhead, 206951 Stoke the Forge, 206991 Banked
 *                                      Coals: a cast on the Cooldown Haste rule's list (no item cast) erupts at once
 *                                      (Flare-up) or adds Heat.
 *   spell_molten_eruption_in_combat    206903 / 206933 / 206973: the area reaches only enemies already in combat (and
 *                                      the eruption's own target).
 *   spell_molten_scorching_hide        206983: the same around the wearer.
 *   spell_molten_cauterize             206913: Mending Flame (206911) heals an ally below 50% health 50% more.
 *   spell_molten_ember_bloom           206923: the wearer's next periodic spell runs two real ticks at once, then
 *                                      Fanned Embers 206924 with the 5 piece 206921.
 *   spell_molten_hallowed_flame        206943 / 206944: each tick restores 1% mana (206945) with Tended Flame 206941.
 *   spell_molten_obsidian_shard        206963 / 206964: Burning Shards 206965 / 206966 with the 5 piece 206961.
 *   spell_molten_rekindle              206974: the next combo point generator grants 1 extra combo point.
 *
 * Every effect logs one DEBUG line, "molten-set <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "Log.h"
#include "MoltenSetLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
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
#include <vector>

using namespace MoltenSet;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // Once-per-cast guard (the Death Knight rework's DeathKnight::OncePerCastGuard shape), one per aura script
    // instance: a cast with an explicit unit target counts only its hit on that unit; a cast without one counts the
    // first event of the same spell object in the same game-time tick; periodic ticks always count.
    class OncePerCastGuard
    {
    public:
        bool First(ProcEventInfo& eventInfo)
        {
            Spell const* spell = eventInfo.GetProcSpell();
            if (!spell || (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC))
                return true;
            if (Unit const* castTarget = spell->m_targets.GetUnitTarget())
                return castTarget == eventInfo.GetActionTarget();
            uint32 const spellId = spell->GetSpellInfo() ? spell->GetSpellInfo()->Id : 0;
            int64 const now = int64(GameTime::GetGameTimeMS().count());
            if (_spell == spell && _spellId == spellId && _timeMs == now)
                return false;
            _spell = spell;
            _spellId = spellId;
            _timeMs = now;
            return true;
        }

    private:
        Spell const* _spell = nullptr;
        uint32 _spellId = 0;
        int64 _timeMs = 0;
    };

    bool HasDirectDamage(SpellInfo const* spellInfo)
    {
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
        }
        return false;
    }

    bool IsPeriodicDamageOrHeal(SpellEffectInfo const& effect)
    {
        return effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE) || effect.IsAura(SPELL_AURA_PERIODIC_LEECH) ||
            effect.IsAura(SPELL_AURA_PERIODIC_DAMAGE_PERCENT) || effect.IsAura(SPELL_AURA_PERIODIC_HEAL);
    }

    bool HasPeriodicDamageOrHeal(SpellInfo const* spellInfo)
    {
        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (IsPeriodicDamageOrHeal(effect))
                return true;
        return false;
    }

    // A direct heal or a heal over time: a two-sided eruption from it heals, the wearer too.
    bool IsHealingSpell(SpellInfo const* spellInfo)
    {
        if (spellInfo->HasEffect(SPELL_EFFECT_HEAL))
            return true;
        for (SpellEffectInfo const& effect : spellInfo->Effects)
            if (effect.IsAura(SPELL_AURA_PERIODIC_HEAL))
                return true;
        return false;
    }

    // The unit a proc event is about: the hit's target, or a cast-phase event's explicit unit target.
    Unit* EventTarget(ProcEventInfo& eventInfo)
    {
        if (Unit* target = eventInfo.GetActionTarget())
            return target;
        if (Spell const* spell = eventInfo.GetProcSpell())
            return spell->m_targets.GetUnitTarget();
        return nullptr;
    }

    // The event as MoltenSet::HeatGain reads it.
    HeatEvent BuildEvent(Unit const* owner, ProcEventInfo& eventInfo)
    {
        HeatEvent event;
        event.periodic = eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC;
        event.crit = eventInfo.GetHitMask() & PROC_HIT_CRITICAL;
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return event;
        event.spell = spellInfo->DmgClass == SPELL_DAMAGE_CLASS_MAGIC || spellInfo->DmgClass == SPELL_DAMAGE_CLASS_NONE;
        event.meleeAbility = spellInfo->DmgClass == SPELL_DAMAGE_CLASS_MELEE;
        event.rangedAbility = spellInfo->DmgClass == SPELL_DAMAGE_CLASS_RANGED;
        event.directDamage = HasDirectDamage(spellInfo);
        event.directHeal = spellInfo->HasEffect(SPELL_EFFECT_HEAL);
        event.damageOrHeal = event.directDamage || event.directHeal || HasPeriodicDamageOrHeal(spellInfo);
        DamageInfo const* damage = eventInfo.GetDamageInfo();
        event.periodicDamage = event.periodic && damage && damage->GetDamage() > 0;
        event.holy = spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_HOLY;
        event.finisher = spellInfo->NeedsComboPoints();
        // A finisher's points are taken only after its hits (Spell::_handle_finish_phase), so they are still held.
        if (event.finisher)
            event.comboPoints = owner->GetComboPoints();
        return event;
    }

    // `gain` Heat for `set` on `wearer`: the Heat buff's stacks, refreshed; true when it erupts (the buff goes).
    bool AddHeat(Unit* wearer, Archetype set, uint32 gain)
    {
        uint32 const heatSpell = HeatSpellOf(set);
        Aura* heat = wearer->GetAura(heatSpell);
        uint32 const current = heat ? heat->GetStackAmount() : 0;
        HeatStep const step = StepHeat(current, gain, HeatCountOf(set));
        if (step.erupts)
        {
            if (heat)
                heat->Remove();
            return true;
        }
        if (!step.stacks || step.stacks == current)
            return false;
        if (!heat)
            heat = wearer->AddAura(heatSpell, wearer);
        if (!heat)
            return false;
        if (heat->GetStackAmount() != step.stacks)
            heat->SetStackAmount(uint8(std::min<uint32>(step.stacks, 0xFF)));
        heat->RefreshDuration();
        return false;
    }

    bool IsEnemy(Unit const* wearer, Unit* unit)
    {
        return unit && unit != wearer && unit->IsAlive() && wearer->IsValidAttackTarget(unit);
    }

    bool IsAlly(Unit const* wearer, Unit* unit)
    {
        return unit && unit->IsAlive() && (unit == wearer || wearer->IsFriendlyTo(unit));
    }

    // The enemy an eruption hits: the event's own target when it is an enemy, else the wearer's victim, else its
    // hostile selection, those two only when already in combat (a bonus never pulls); nullptr when there is none.
    Unit* EnemyFor(Player* wearer, Unit* target)
    {
        if (IsEnemy(wearer, target))
            return target;
        if (Unit* victim = wearer->GetVictim(); IsEnemy(wearer, victim) && victim->IsInCombat())
            return victim;
        if (Unit* selected = wearer->GetSelectedUnit(); IsEnemy(wearer, selected) && selected->IsInCombat())
            return selected;
        return nullptr;
    }

    // Where a two-sided eruption lands (MoltenSet::ChoosePayoutSide): `enemy` is set for Enemy / Nearby, `ally` for
    // Ally / Wearer.
    void PayoutFor(Player* wearer, Unit* target, bool healing, Unit*& enemy, Unit*& ally)
    {
        bool const targetEnemy = IsEnemy(wearer, target);
        bool const targetOtherAlly = !targetEnemy && target != wearer && IsAlly(wearer, target);
        Unit* nearby = (targetEnemy || targetOtherAlly || healing) ? nullptr : EnemyFor(wearer, nullptr);
        PayoutSide const side = ChoosePayoutSide(targetEnemy, targetOtherAlly, healing, nearby != nullptr);
        enemy = side == PayoutSide::Enemy ? target : side == PayoutSide::Nearby ? nearby : nullptr;
        ally = side == PayoutSide::Ally ? target : side == PayoutSide::Wearer ? wearer : nullptr;
    }

    // Living enemies of `attacker` within `radius` yards of `center`, in combat (a bonus never pulls a pack).
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

    // Up to `count` living group members (or the player alone) within `range` yards of `center`, other than
    // `except`, most injured first.
    std::vector<Player*> AlliesNear(Player* player, WorldObject const* center, float range, Unit const* except,
        uint32 count)
    {
        std::vector<Player*> found;
        auto consider = [&](Player* member)
        {
            if (!member || member == except || !member->IsInWorld() || !member->IsAlive() ||
                member->GetMap() != player->GetMap() || !center->IsWithinDistInMap(member, range))
                return;
            found.push_back(member);
        };
        if (Group* group = player->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                consider(ref->GetSource());
        }
        else
            consider(player);
        std::sort(found.begin(), found.end(), [](Player const* a, Player const* b)
        {
            return MoreInjured(a->GetHealth(), a->GetMaxHealth(), b->GetHealth(), b->GetMaxHealth());
        });
        if (found.size() > count)
            found.resize(count);
        return found;
    }

    // An area payout's targets: living units already in combat; `keep` (the payout's own explicit target) stays.
    void RemoveIdleTargets(std::list<WorldObject*>& targets, Unit const* keep)
    {
        targets.remove_if([keep](WorldObject* object)
        {
            Unit const* unit = object->ToUnit();
            return !unit || (unit != keep && (!unit->IsAlive() || !unit->IsInCombat()));
        });
    }

    // A heal on `target` and up to `extra` other group members within `radius` yards of it, most injured first.
    void HealAround(Player* wearer, Unit* target, uint32 spellId, float radius, uint32 extra, AuraEffect const* by)
    {
        wearer->CastSpell(target, spellId, true, nullptr, by);
        for (Player* ally : AlliesNear(wearer, target, radius, target, extra))
            wearer->CastSpell(ally, spellId, true, nullptr, by);
    }

    // The set's eruption at its count. `target` is the event's unit (may be null or the wearer); `ranged` says the
    // event was a ranged ability (Beastmaster's shards off ranged attack power); `healing` that it healed (where Molten
    // Thunder and Hallowed Flame land when the target is the wearer or none).
    void Erupt(Player* wearer, Archetype set, Unit* target, bool ranged, bool healing, AuraEffect const* by)
    {
        Unit* payoutEnemy = nullptr;
        Unit* payoutAlly = nullptr;
        switch (set)
        {
            case Archetype::Sorcerers:
                if (Unit* enemy = EnemyFor(wearer, target))
                    wearer->CastSpell(enemy, SPELL_STOKED_FLAME_ERUPTION, true, nullptr, by);
                break;
            case Archetype::Virtuous:
                if (Unit* ally = IsAlly(wearer, target) ? target : wearer)
                    HealAround(wearer, ally, SPELL_CAUTERIZE_HEAL, kCauterizeRadius, kCauterizeExtraAllies, by);
                break;
            case Archetype::Feralheart:
                wearer->CastSpell(wearer, SPELL_EMBER_BLOOM_READY, true, nullptr, by);
                break;
            case Archetype::FiveThunders:
                PayoutFor(wearer, target, healing, payoutEnemy, payoutAlly);
                if (payoutEnemy)
                    wearer->CastSpell(payoutEnemy, SPELL_MOLTEN_THUNDER_DAMAGE, true, nullptr, by);
                else
                    HealAround(wearer, payoutAlly, SPELL_MOLTEN_THUNDER_HEAL, kMoltenThunderRadius,
                        kMoltenThunderExtraAllies, by);
                break;
            case Archetype::Soulforge:
                PayoutFor(wearer, target, healing, payoutEnemy, payoutAlly);
                wearer->CastSpell(payoutEnemy ? payoutEnemy : payoutAlly,
                    payoutEnemy ? SPELL_HALLOWED_FLAME_DOT : SPELL_HALLOWED_FLAME_HOT, true, nullptr, by);
                break;
            case Archetype::Heroism:
                if (Unit* enemy = EnemyFor(wearer, target))
                    wearer->CastSpell(enemy, SPELL_MOLTEN_EDGE_SEAR, true, nullptr, by);
                break;
            case Archetype::Beastmasters:
                if (Unit* enemy = EnemyFor(wearer, target))
                {
                    uint32 const shard = ranged ? SPELL_OBSIDIAN_SHARD_RANGED : SPELL_OBSIDIAN_SHARD_MELEE;
                    wearer->CastSpell(enemy, shard, true, nullptr, by);
                    if (Unit* bounce = NearestEnemy(enemy, wearer, kObsidianShardBounceRadius, enemy))
                        wearer->CastSpell(bounce, shard, true, nullptr, by);
                }
                break;
            case Archetype::Darkmantle:
                if (Unit* enemy = EnemyFor(wearer, target))
                    wearer->CastSpell(enemy, SPELL_SLAG_BURST_ERUPTION, true, nullptr, by);
                if (wearer->HasAura(SPELL_REKINDLE))
                    wearer->CastSpell(wearer, SPELL_REKINDLE_BUFF, true, nullptr, by);
                break;
            case Archetype::Guardians:
                wearer->CastSpell(wearer, SPELL_SCORCHING_HIDE_ERUPTION, true, nullptr, by);
                if (wearer->HasAura(SPELL_TEMPERED_HIDE))
                    wearer->CastSpell(wearer, SPELL_TEMPERED_HIDE_BUFF, true, nullptr, by);
                break;
            case Archetype::Impenetrable:
                wearer->CastSpell(wearer, SPELL_MOLTEN_PLATE_BUFF, true, nullptr, by);
                break;
            default:
                return;
        }
        LOG_DEBUG(kLog, "molten-set eruption {} set {} at {}", wearer->GetGUID().ToString(), uint32(set),
            target ? target->GetGUID().ToString() : "none");
    }
}

// The ten 3 pieces (206900 + 10k): every event the set counts gives Heat (1, or 2 on a crit; Darkmantle 1 per combo
// point and 1 more on a crit), once per cast; the gain that reaches the set's count erupts.
class spell_molten_heat : public AuraScript
{
    PrepareAuraScript(spell_molten_heat);

    bool Validate(SpellInfo const* spellInfo) override
    {
        Archetype const set = ArchetypeOf(spellInfo->Id);
        return set != Archetype::Count && ValidateSpellInfo({ HeatSpellOf(set) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        // Heat lives only in combat: its buff's LEAVE_COMBAT interrupt fires on leaving combat, never on a gain made
        // while already out of it (a heal between pulls), so such a gain must not start one.
        if (!spellInfo || eventInfo.GetActor() != wearer || !wearer->IsInCombat() ||
            kSpellsMoltenSet.Contains(spellInfo->Id))
            return false;
        _gain = HeatGain(ArchetypeOf(GetId()), BuildEvent(wearer, eventInfo));
        if (!_gain || !_guard.First(eventInfo))
            return false;
        Unit* target = EventTarget(eventInfo);
        _target = target ? target->GetGUID() : ObjectGuid::Empty;
        _ranged = spellInfo->DmgClass == SPELL_DAMAGE_CLASS_RANGED;
        _healing = IsHealingSpell(spellInfo);
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* wearer = GetTarget()->ToPlayer();
        if (!wearer || !wearer->IsAlive())
            return;
        Archetype const set = ArchetypeOf(GetId());
        if (!AddHeat(wearer, set, _gain))
            return;
        Unit* target = _target ? ObjectAccessor::GetUnit(*wearer, _target) : nullptr;
        Erupt(wearer, set, target, _ranged, _healing, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_molten_heat::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_molten_heat::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    OncePerCastGuard _guard;
    ObjectGuid _target;
    uint32 _gain = 0;
    bool _ranged = false;
    bool _healing = false;
};

// 206901 Flare-up, 206931 Thunderhead, 206951 Stoke the Forge, 206991 Banked Coals: a cast on the Cooldown Haste rule's
// list (base cooldown 30 s or more, the allow list, never the deny list; never an item cast), at its cast phase.
// Flare-up erupts at full strength whatever the Heat (no enemy: nothing happens); the others add Heat.
class spell_molten_cooldown_heat : public AuraScript
{
    PrepareAuraScript(spell_molten_cooldown_heat);

    bool Validate(SpellInfo const* spellInfo) override
    {
        Archetype const set = ArchetypeOf(spellInfo->Id);
        return CooldownHookHeat(set) > 0 && ValidateSpellInfo({ HeatSpellOf(set) });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        Spell const* spell = eventInfo.GetProcSpell();
        // In combat only, like the 3 pieces: a cooldown used before the pull neither starts Heat nor erupts at a pack.
        if (!spellInfo || !spell || eventInfo.GetActor() != wearer || !wearer->IsInCombat() ||
            !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST) || spell->m_CastItem || spellInfo->IsPassive() ||
            kSpellsMoltenSet.Contains(spellInfo->Id))
            return false;
        if (!IsCooldownHookSpell(spellInfo->Id, spellInfo->RecoveryTime, spellInfo->CategoryRecoveryTime))
            return false;
        Unit* target = EventTarget(eventInfo);
        _target = target ? target->GetGUID() : ObjectGuid::Empty;
        _ranged = spellInfo->DmgClass == SPELL_DAMAGE_CLASS_RANGED;
        _healing = IsHealingSpell(spellInfo);
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Player* wearer = GetTarget()->ToPlayer();
        if (!wearer || !wearer->IsAlive())
            return;
        Archetype const set = ArchetypeOf(GetId());
        Unit* target = _target ? ObjectAccessor::GetUnit(*wearer, _target) : nullptr;
        if (set == Archetype::Sorcerers)
        {
            // Flare-up: the eruption at full strength, whatever the Heat; with no enemy the Heat stays.
            if (!EnemyFor(wearer, target))
                return;
            wearer->RemoveAurasDueToSpell(HeatSpellOf(set));
            Erupt(wearer, set, target, _ranged, _healing, aurEff);
            return;
        }
        uint32 const gain = CooldownHookHeat(set);
        LOG_DEBUG(kLog, "molten-set cooldown hook {} set {} +{} heat", wearer->GetGUID().ToString(), uint32(set), gain);
        if (AddHeat(wearer, set, gain))
            Erupt(wearer, set, target, _ranged, _healing, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_molten_cooldown_heat::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_molten_cooldown_heat::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    ObjectGuid _target;
    bool _ranged = false;
    bool _healing = false;
};

// 206903 Stoked Flame, 206933 Molten Thunder, 206973 Slag Burst: the area around the target reaches only enemies
// already in combat (the target itself always), so an eruption never pulls a pack.
class spell_molten_eruption_in_combat : public SpellScript
{
    PrepareSpellScript(spell_molten_eruption_in_combat);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        RemoveIdleTargets(targets, GetExplTargetUnit());
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_molten_eruption_in_combat::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 206983 Scorching Hide: the area around the wearer reaches only enemies already in combat.
class spell_molten_scorching_hide : public SpellScript
{
    PrepareSpellScript(spell_molten_scorching_hide);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        RemoveIdleTargets(targets, nullptr);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_molten_scorching_hide::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// 206913 Cauterize: with Mending Flame (206911), an ally below 50% health (before this heal) is healed 50% more.
class spell_molten_cauterize : public SpellScript
{
    PrepareSpellScript(spell_molten_cauterize);

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !caster->HasAura(SPELL_MENDING_FLAME))
            return;
        int32 const pct = MendingFlamePct(target->GetHealth(), target->GetMaxHealth());
        if (pct == 100)
            return;
        SetHitHeal(ScalePct(GetHitHeal(), pct));
        LOG_DEBUG(kLog, "molten-set mending flame {} on {}: {}%", caster->GetGUID().ToString(),
            target->GetGUID().ToString(), pct);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_molten_cauterize::HandleHit);
    }
};

// 206923 Ember Bloom: the wearer's next cast of a periodic damage or heal spell (not a channel) blooms. The next
// update runs two real ticks of every periodic damage or heal effect that cast left on its target (spell power, crit
// and procs as a normal tick), then gives Fanned Embers 206924 with the 5 piece 206921. One charge (spell_proc).
class spell_molten_ember_bloom : public AuraScript
{
    PrepareAuraScript(spell_molten_ember_bloom);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_FANNED_EMBERS_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        Unit* target = eventInfo.GetActionTarget();
        if (!spellInfo || !target || eventInfo.GetActor() != wearer || spellInfo->IsChanneled() ||
            kSpellsMoltenSet.Contains(spellInfo->Id) || !HasPeriodicDamageOrHeal(spellInfo) || !_guard.First(eventInfo))
            return false;
        _target = target->GetGUID();
        _spellId = spellInfo->Id;
        return true;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        ObjectGuid const wearerGuid = wearer->GetGUID();
        ObjectGuid const targetGuid = _target;
        uint32 const spellId = _spellId;
        // Next update: the aura the cast applies is in place by then (never tick inside the proc of its own hit).
        wearer->m_Events.AddEventAtOffset([wearerGuid, targetGuid, spellId]()
        {
            Player* owner = ObjectAccessor::FindPlayer(wearerGuid);
            if (!owner || !owner->IsInWorld())
                return;
            Unit* victim = ObjectAccessor::GetUnit(*owner, targetGuid);
            Aura* aura = victim ? victim->GetAura(spellId, wearerGuid) : nullptr;
            AuraApplication* application = aura ? aura->GetApplicationOfTarget(targetGuid) : nullptr;
            if (!application || !victim->IsAlive())
                return;
            uint32 ticked = 0;
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            {
                AuraEffect* effect = aura->GetEffect(i);
                if (!effect || !IsPeriodicDamageOrHeal(aura->GetSpellInfo()->Effects[i]))
                    continue;
                for (uint32 tick = 0; tick < kEmberBloomTicks && victim->IsAlive(); ++tick)
                {
                    effect->PeriodicTick(application, owner);
                    ++ticked;
                }
            }
            if (ticked && owner->HasAura(SPELL_FANNED_EMBERS))
                owner->CastSpell(owner, SPELL_FANNED_EMBERS_BUFF, true);
            LOG_DEBUG(kLog, "molten-set ember bloom {} spell {} on {}: {} tick(s)", wearerGuid.ToString(), spellId,
                targetGuid.ToString(), ticked);
        }, Milliseconds(0));
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_molten_ember_bloom::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_molten_ember_bloom::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    OncePerCastGuard _guard;
    ObjectGuid _target;
    uint32 _spellId = 0;
};

// 206943 / 206944 Hallowed Flame: with Tended Flame (206941) each tick restores the caster 1% of maximum mana (206945).
class spell_molten_hallowed_flame : public AuraScript
{
    PrepareAuraScript(spell_molten_hallowed_flame);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_TENDED_FLAME_MANA });
    }

    void HandleTick(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (caster && caster->IsAlive() && caster->HasAura(SPELL_TENDED_FLAME))
            caster->CastSpell(caster, SPELL_TENDED_FLAME_MANA, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_molten_hallowed_flame::HandleTick, EFFECT_0, SPELL_AURA_ANY);
    }
};

// 206963 / 206964 Obsidian Shard: with Burning Shards (206961) the shard leaves its target burning, off the same attack
// power as the shard (206965 melee, 206966 ranged).
class spell_molten_obsidian_shard : public SpellScript
{
    PrepareSpellScript(spell_molten_obsidian_shard);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_BURNING_SHARDS_MELEE, SPELL_BURNING_SHARDS_RANGED });
    }

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || !target->IsAlive() || !caster->HasAura(SPELL_BURNING_SHARDS))
            return;
        bool const ranged = GetSpellInfo()->Id == SPELL_OBSIDIAN_SHARD_RANGED;
        caster->CastSpell(target, ranged ? SPELL_BURNING_SHARDS_RANGED : SPELL_BURNING_SHARDS_MELEE, true);
        LOG_DEBUG(kLog, "molten-set burning shards {} on {}", caster->GetGUID().ToString(),
            target->GetGUID().ToString());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_molten_obsidian_shard::HandleHit);
    }
};

// 206974 Rekindle: the next combo point generator (a spell with an ADD_COMBO_POINTS effect) grants 1 extra combo point
// (Rogue::GainComboPoints: onto the hit target, else the selection, else parked on the player). One charge.
class spell_molten_rekindle : public AuraScript
{
    PrepareAuraScript(spell_molten_rekindle);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && eventInfo.GetActor() == GetTarget() &&
            spellInfo->HasEffect(SPELL_EFFECT_ADD_COMBO_POINTS) && !kSpellsMoltenSet.Contains(spellInfo->Id);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Player* wearer = GetTarget()->ToPlayer();
        if (!wearer)
            return;
        Rogue::GainComboPoints(wearer, eventInfo.GetActionTarget(), int8(kRekindleComboPoints));
        LOG_DEBUG(kLog, "molten-set rekindle {} +{} combo point", wearer->GetGUID().ToString(), kRekindleComboPoints);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_molten_rekindle::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_molten_rekindle::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

void AddSC_molten_set_bonuses()
{
    RegisterSpellScript(spell_molten_heat);
    RegisterSpellScript(spell_molten_cooldown_heat);
    RegisterSpellScript(spell_molten_eruption_in_combat);
    RegisterSpellScript(spell_molten_scorching_hide);
    RegisterSpellScript(spell_molten_cauterize);
    RegisterSpellScript(spell_molten_ember_bloom);
    RegisterSpellScript(spell_molten_hallowed_flame);
    RegisterSpellScript(spell_molten_obsidian_shard);
    RegisterSpellScript(spell_molten_rekindle);
}
