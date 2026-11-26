/*
 * mod-dungeon-bosses, Zul'Farrak: the hard mode item effects of Gahz'rilla, The Crew at the Pool (designer text:
 * docs/dungeons/zul-farrak-rework.md ## Loot, the hard mode list). The spells are
 * apps/dbc-tools/source/items/zul_farrak_hard_mode_effects.py; both damage numbers come from potency and the copied
 * heal is a share of a heal that already carries the wearer's bonuses, so nothing here sizes a hit. The scaled effects
 * (scale="budget") carry their own copies on every tier above 71, bound to the same scripts, so a script never casts a
 * family spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the tier of
 * the spell or aura it runs for, and the base id on the 71 tier. The charge buffs and The Crew's Aid have no copies.
 *
 *   spell_zf_scale_of_the_storm_god  213800 Scale of the Storm God (Equip). A direct hit that damages the wearer gives
 *                                    one 213801 (Static Charge); a melee ability that lands at full stacks takes them
 *                                    and casts the tier's 213802, at most once every effect 2's amount in seconds.
 *   spell_zf_static_discharge        213802 Static Discharge. Only enemies in combat.
 *   spell_zf_stormcharged_fang       213803 Stormcharged Fang (Equip). One action per cast: a critical damaging hit
 *                                    gives one 213804; at full charge a hit with other enemies in combat around its
 *                                    target takes the charges and casts the tier's 213805 on the nearest ones.
 *   spell_zf_sergeants_whistle       213806 Sergeant's Whistle (Use). Copies the wearer's single target heals (213807)
 *                                    to the injured group members lowest on health near the target, and shows the crew
 *                                    (301000-301004, look only) while it lasts.
 *
 * Every payout logs one DEBUG line, "zf-items <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "Creature.h"
#include "DruidMechanics.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ItemSpellCopies.h"
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
#include "ZulFarrakHardModeItemsLogic.h"
#include <algorithm>
#include <array>
#include <list>
#include <tuple>
#include <vector>

using namespace ZulFarrakHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    static_assert(kTakenHitFlags == (PROC_FLAG_TAKEN_MELEE_AUTO_ATTACK | PROC_FLAG_TAKEN_SPELL_MELEE_DMG_CLASS
        | PROC_FLAG_TAKEN_RANGED_AUTO_ATTACK | PROC_FLAG_TAKEN_SPELL_RANGED_DMG_CLASS
        | PROC_FLAG_TAKEN_SPELL_NONE_DMG_CLASS_NEG | PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG));
    static_assert(kMeleeAbilityFlag == PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS);
    static_assert(std::tuple_size_v<decltype(std::array<HealShape, 3>{})> == MAX_SPELL_EFFECTS);

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    uint64 NowMs()
    {
        return static_cast<uint64>(GameTime::GetGameTimeMS().count());
    }

    uint32 StacksOf(Unit const* wearer, uint32 spellId)
    {
        Aura const* aura = wearer->GetAura(spellId);
        return aura ? aura->GetStackAmount() : 0;
    }

    CastStamp StampOf(Spell const* spell)
    {
        if (!spell)
            return CastStamp{};
        return CastStamp{ spell, spell->GetSpellInfo()->Id, spell->m_cast_count,
            CastMoment(spell->GetDelayStart(), NowMs()) };
    }

    // The other enemies the Fang arcs to: alive, attackable, in combat (a bonus never pulls a pack), in the target's
    // sight, not under a crowd control that damage breaks (the engine's own chain spells skip those too), nearest
    // first, at most `count`.
    std::vector<Unit*> ArcTargets(Unit* victim, Unit* wearer, float radius, int32 count)
    {
        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(victim, wearer, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(victim, found, check);
        Cell::VisitObjects(victim, searcher, radius);

        std::vector<Unit*> picks;
        for (Unit* unit : found)
            if (unit != victim && unit->IsAlive() && unit->IsInCombat() && wearer->IsValidAttackTarget(unit)
                && !unit->HasBreakableByDamageCrowdControlAura(wearer) && victim->IsWithinLOSInMap(unit))
                picks.push_back(unit);
        std::sort(picks.begin(), picks.end(), [victim](Unit const* a, Unit const* b)
        {
            return victim->GetExactDistSq(a) < victim->GetExactDistSq(b);
        });
        if (picks.size() > static_cast<std::size_t>(std::max(count, 0)))
            picks.resize(static_cast<std::size_t>(std::max(count, 0)));
        return picks;
    }

    bool IsHealingEffect(SpellEffectInfo const& effect)
    {
        switch (effect.Effect)
        {
            case SPELL_EFFECT_HEAL:
            case SPELL_EFFECT_HEAL_MAX_HEALTH:
            case SPELL_EFFECT_HEAL_MECHANICAL:
            case SPELL_EFFECT_HEAL_PCT:
                return true;
            default:
                return effect.ApplyAuraName == SPELL_AURA_PERIODIC_HEAL;
        }
    }

    // Heals that a script spreads over several targets read as single heals in the data: Bloom jumps from target to
    // target (Druid::StartBloomJumps), the others are IsScriptSpreadHeal's.
    bool HealsOneTarget(SpellInfo const* spellInfo)
    {
        if (spellInfo->Id == Druid::SPELL_BLOOM || spellInfo->Id == Druid::SPELL_BLOOM_JUMP
            || IsScriptSpreadHeal(spellInfo->Id))
            return false;

        std::array<HealShape, 3> shapes;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            SpellEffectInfo const& effect = spellInfo->Effects[i];
            shapes[i].heals = IsHealingEffect(effect);
            shapes[i].area = effect.IsTargetingArea() || effect.IsAreaAuraEffect()
                || effect.IsEffect(SPELL_EFFECT_PERSISTENT_AREA_AURA);
            shapes[i].onCaster = effect.TargetA.GetTarget() == TARGET_UNIT_CASTER;
            shapes[i].chainTargets = effect.ChainTarget;
        }
        return IsSingleTargetHeal(shapes);
    }

    // The injured group members (the wearer included, alone without a group) within `radius` yards of `healed` and in
    // its sight, `healed` left out, lowest health fraction first, at most `count`.
    std::vector<Player*> LowestAllies(Player* healer, Unit* healed, float radius, int32 count)
    {
        std::vector<Player*> picks;
        auto consider = [&](Player* member)
        {
            if (!member || member == healed || !member->IsInWorld() || !member->IsAlive()
                || member->GetMap() != healed->GetMap() || !healed->IsWithinDistInMap(member, radius)
                || !IsInjured(member->GetHealth(), member->GetMaxHealth()) || !healed->IsWithinLOSInMap(member))
                return;
            picks.push_back(member);
        };
        if (Group* group = healer->GetGroup())
        {
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                consider(ref->GetSource());
        }
        else
            consider(healer);

        std::sort(picks.begin(), picks.end(), [](Player const* a, Player const* b)
        {
            return LowerHealthFraction(a->GetHealth(), a->GetMaxHealth(), b->GetHealth(), b->GetMaxHealth());
        });
        if (picks.size() > static_cast<std::size_t>(std::max(count, 0)))
            picks.resize(static_cast<std::size_t>(std::max(count, 0)));
        return picks;
    }
}

// 213800 Scale of the Storm God: hits taken build Static Charge, a melee ability at full stacks discharges it.
class spell_zf_scale_of_the_storm_god : public AuraScript
{
    PrepareAuraScript(spell_zf_scale_of_the_storm_god);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ SPELL_STATIC_CHARGE, TierSpell(spellInfo, SPELL_STATIC_DISCHARGE) });
    }

    bool Charges(ProcEventInfo& eventInfo)
    {
        DamageInfo const* damage = eventInfo.GetDamageInfo();
        return damage && HitCharges(eventInfo.GetTypeMask(), damage->GetDamage(), eventInfo.GetActor() == GetTarget());
    }

    bool Discharges(ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        AuraEffect const* needed = GetEffect(EFFECT_0);
        return spell && needed && AbilityDischarges(eventInfo.GetTypeMask(), spell->IsTriggered(),
            spell->GetSpellInfo()->HasAttribute(SPELL_ATTR3_NOT_A_PROC), StacksOf(GetTarget(), SPELL_STATIC_CHARGE),
            uint32(std::max(needed->GetAmount(), 0)), NowMs(), _readyAtMs);
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetTarget()->IsAlive() && (Charges(eventInfo) || Discharges(eventInfo));
    }

    // An area ability's later targets find no stacks left, so a cast discharges once.
    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        if (Charges(eventInfo))
        {
            wearer->CastSpell(wearer, SPELL_STATIC_CHARGE, true, nullptr, aurEff);
            return;
        }
        if (!Discharges(eventInfo))
            return;

        if (AuraEffect const* cooldown = GetEffect(EFFECT_1))
            _readyAtMs = NowMs() + uint64(std::max(cooldown->GetAmount(), 0)) * uint64(IN_MILLISECONDS);
        wearer->RemoveAurasDueToSpell(SPELL_STATIC_CHARGE);
        uint32 const dischargeId = TierSpell(GetSpellInfo(), SPELL_STATIC_DISCHARGE);
        wearer->CastSpell(wearer, dischargeId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zf-items scale {} discharged ({})", wearer->GetGUID().ToString(), dischargeId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zf_scale_of_the_storm_god::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zf_scale_of_the_storm_god::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    uint64 _readyAtMs = 0;
};

// 213802 Static Discharge: only enemies already in combat.
class spell_zf_static_discharge : public SpellScript
{
    PrepareSpellScript(spell_zf_static_discharge);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject* object)
        {
            Unit const* unit = object->ToUnit();
            return !unit || !unit->IsInCombat();
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_zf_static_discharge::FilterTargets, EFFECT_0,
            TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// 213803 Stormcharged Fang: critical spell hits charge it, a damaging spell at full charge arcs.
class spell_zf_stormcharged_fang : public AuraScript
{
    PrepareAuraScript(spell_zf_stormcharged_fang);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ SPELL_STORMCHARGED, TierSpell(spellInfo, SPELL_STORM_ARC) });
    }

    bool IsCharged() const
    {
        AuraEffect const* needed = GetEffect(EFFECT_0);
        return needed && needed->GetAmount() > 0
            && StacksOf(GetTarget(), SPELL_STORMCHARGED) >= uint32(needed->GetAmount());
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!victim || victim == wearer || !wearer->IsAlive()
            || SameCast(_acted, StampOf(eventInfo.GetProcSpell())))
            return false;
        return (eventInfo.GetHitMask() & PROC_HIT_CRITICAL) || IsCharged();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        AuraEffect const* arcs = GetEffect(EFFECT_1);
        if (!victim || !arcs)
            return;

        std::vector<Unit*> others;
        if (IsCharged())
            others = ArcTargets(victim, wearer, GetSpellInfo()->Effects[EFFECT_0].CalcRadius(wearer),
                arcs->GetAmount());

        FangAction const action = DecideFang(StacksOf(wearer, SPELL_STORMCHARGED),
            uint32(std::max(aurEff->GetAmount(), 0)), (eventInfo.GetHitMask() & PROC_HIT_CRITICAL) != 0,
            !others.empty());
        if (action == FangAction::None)
            return;

        _acted = StampOf(eventInfo.GetProcSpell());
        if (action == FangAction::Charge)
        {
            wearer->CastSpell(wearer, SPELL_STORMCHARGED, true, nullptr, aurEff);
            return;
        }

        wearer->RemoveAurasDueToSpell(SPELL_STORMCHARGED);
        uint32 const arcId = TierSpell(GetSpellInfo(), SPELL_STORM_ARC);
        for (Unit* other : others)
            wearer->CastSpell(other, arcId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "zf-items fang {} arced from {} to {} ({})", wearer->GetGUID().ToString(),
            victim->GetGUID().ToString(), others.size(), arcId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zf_stormcharged_fang::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zf_stormcharged_fang::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

    CastStamp _acted;
};

// 213806 Sergeant's Whistle: single target heals are shared with the two lowest allies near the target; the crew is
// look only.
class spell_zf_sergeants_whistle : public AuraScript
{
    PrepareAuraScript(spell_zf_sergeants_whistle);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_THE_CREWS_AID });
    }

    // A heal of the wearer on one target: direct or a tick. Not a copy (its own or another, e.g. Beacon of Light: sized
    // from a heal, so it ignores the caster's modifiers) and not an item's.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        SpellInfo const* healSpell = heal ? heal->GetSpellInfo() : nullptr;
        if (!healSpell || !heal->GetHeal() || !eventInfo.GetActionTarget() || !GetTarget()->IsPlayer())
            return false;
        if (healSpell->Id == SPELL_THE_CREWS_AID || healSpell->HasAttribute(SPELL_ATTR3_IGNORE_CASTER_MODIFIERS))
            return false;
        Spell const* spell = eventInfo.GetProcSpell();
        return !(spell && spell->m_CastItem) && HealsOneTarget(healSpell);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Player* healer = GetTarget()->ToPlayer();
        Unit* healed = eventInfo.GetActionTarget();
        HealInfo const* heal = eventInfo.GetHealInfo();
        AuraEffect const* allies = GetEffect(EFFECT_1);
        if (!healer || !healed || !heal || !allies)
            return;

        // The healed target's healing taken modifiers come off again: the copy takes its own target's.
        bool const tick = (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) != 0;
        uint32 const whole = HealBeforeTaken(heal->GetHeal(), heal->GetAbsorb(),
            healed->SpellHealingBonusTaken(healer, heal->GetSpellInfo(), kTakenProbe, tick ? DOT : HEAL));
        int32 const amount = ShareOfHeal(whole, aurEff->GetAmount());
        if (amount <= 0)
            return;

        std::vector<Player*> const picks = LowestAllies(healer, healed,
            GetSpellInfo()->Effects[EFFECT_0].CalcRadius(healer), allies->GetAmount());
        if (picks.empty())
            return;

        for (Player* ally : picks)
        {
            healer->CastCustomSpell(ally, SPELL_THE_CREWS_AID, &amount, nullptr, nullptr, true, nullptr, aurEff);
            LOG_DEBUG(kLog, "zf-items whistle {} healed {} for {} ({} before taken): {} to {}",
                healer->GetGUID().ToString(), healed->GetGUID().ToString(), heal->GetHeal(), whole, amount,
                ally->GetGUID().ToString());
        }
        for (ObjectGuid const& guid : _crew)
            if (Creature* member = ObjectAccessor::GetCreature(*healer, guid))
                if (member->GetEntry() == NPC_CREW_MURTA)
                    member->HandleEmoteCommand(EMOTE_ONESHOT_SPELL_CAST_OMNI);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsInWorld())
            return;

        for (CrewLook const& look : kCrew)
        {
            Position const spot = wearer->GetFirstCollisionPosition(kCrewDistance, look.angle);
            TempSummon* member = wearer->SummonCreature(look.entry, spot, TEMPSUMMON_TIMED_DESPAWN, kCrewStayMs);
            if (!member)
                continue;
            member->SetReactState(REACT_PASSIVE);
            member->AttackStop();
            member->SetVirtualItem(0, look.mainHand);
            member->SetVirtualItem(1, look.offHand);
            member->SetVirtualItem(2, look.ranged);
            member->SetSheath(SHEATH_STATE_MELEE);
            member->GetMotionMaster()->MoveFollow(wearer, kCrewDistance, look.angle);
            _crew.push_back(member->GetGUID());
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        for (ObjectGuid const& guid : _crew)
            if (Creature* member = ObjectAccessor::GetCreature(*GetTarget(), guid))
                member->DespawnOrUnsummon();
        _crew.clear();
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_zf_sergeants_whistle::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_zf_sergeants_whistle::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_zf_sergeants_whistle::HandleApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_zf_sergeants_whistle::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }

    std::vector<ObjectGuid> _crew;
};

void AddSC_zf_hard_mode_items()
{
    RegisterSpellScript(spell_zf_scale_of_the_storm_god);
    RegisterSpellScript(spell_zf_static_discharge);
    RegisterSpellScript(spell_zf_stormcharged_fang);
    RegisterSpellScript(spell_zf_sergeants_whistle);
}
