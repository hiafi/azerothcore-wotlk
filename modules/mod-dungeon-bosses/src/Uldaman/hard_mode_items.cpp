/*
 * mod-dungeon-bosses, Uldaman: the hard mode item effects of Archaedas, The Makers' Lights (designer text:
 * docs/dungeons/uldaman-rework.md ## Loot, the hard mode list). The spells are
 * apps/dbc-tools/source/items/uldaman_hard_mode_effects.py; the trample's damage comes from potency and the Disk's
 * replay is a share of healing that already carried the wearer's bonuses, so nothing here sizes a hit. The scaled
 * effects (scale="budget") carry their own copies on every tier above 71, bound to the same scripts, so a script never
 * casts a family spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy in the
 * tier of the spell or aura it runs for, and the base id on the 71 tier. The Disk's replay and its heal have no copies.
 *
 *   spell_uldaman_item_waking_stone           214680 Waking Stone (Use). Sends a Waking Earthen (301200, look only)
 *                                             marching ahead of the wearer; each tick the tier's 214681 hits every
 *                                             enemy in combat its last step passed, once per enemy per march.
 *   spell_uldaman_item_earthen_trample        214681 Earthen Trample. Keeps the knockback off bosses.
 *   spell_uldaman_item_lightbound_choker      214682 Lightbound Choker (Equip). A damaging or healing spell of
 *                                             another school than the last casts the tier's 214683 (Two Lights).
 *   spell_uldaman_item_fragment_of_the_disks  214684 Fragment of the Disks (Use). Records the wearer's effective
 *                                             healing per target for 6 sec, then casts 214685 with the record.
 *   spell_uldaman_item_disk_replay            214685 Disk Replay. Heals each recorded target its share over 6 sec
 *                                             (214686).
 *
 * Every payout logs one DEBUG line, "uldaman-items <effect> ...", in module.dungeonbosses.
 */

#include "CellImpl.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ScriptedCreature.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include "UldamanHardModeItemsLogic.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <list>

using namespace UldamanHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    static_assert(kOwnCastFlags == (PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
        | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
        | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG));
    static_assert(kHealFlags == (PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
        | PROC_FLAG_DONE_PERIODIC));

    // The point id of the earthen's march (MovePoint).
    uint32 constexpr kMarchPointId = 1;

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    PathPoint ToPoint(Position const& pos)
    {
        return PathPoint{ pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ() };
    }

    // What the trample's knockback rule reads of a unit (UldamanHardModeItemsLogic.h CanKnockBack).
    KnockbackTarget KnockbackSignsOf(Unit const* unit)
    {
        KnockbackTarget signs;
        Creature const* creature = unit->ToCreature();
        if (!creature)
            return signs;
        signs.creature = true;
        signs.worldBoss = creature->isWorldBoss();
        signs.dungeonBoss = creature->IsDungeonBoss();
        signs.immune = creature->IsImmuneToKnockback();
        CreatureTemplate const* info = creature->GetCreatureTemplate();
        signs.bindsInstance = info && info->HasFlagsExtra(CREATURE_FLAG_EXTRA_INSTANCE_BIND);
        signs.bossScript = creature->IsAIEnabled && dynamic_cast<BossAI const*>(creature->AI()) != nullptr;
        return signs;
    }

    // One effect that deals damage or heals by its data: a damage, weapon damage, leech or heal effect, or a periodic
    // damage, leech or heal aura.
    bool DamagesOrHealsEffect(SpellEffectInfo const& effect)
    {
        switch (effect.Effect)
        {
            case SPELL_EFFECT_SCHOOL_DAMAGE:
            case SPELL_EFFECT_HEALTH_LEECH:
            case SPELL_EFFECT_HEAL:
            case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
            case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
            case SPELL_EFFECT_WEAPON_DAMAGE:
            case SPELL_EFFECT_HEAL_MECHANICAL:
            case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
            case SPELL_EFFECT_HEAL_PCT:
                return true;
            default:
                break;
        }
        if (!effect.IsAura())
            return false;
        switch (effect.ApplyAuraName)
        {
            case SPELL_AURA_PERIODIC_DAMAGE:
            case SPELL_AURA_PERIODIC_HEAL:
            case SPELL_AURA_OBS_MOD_HEALTH:
            case SPELL_AURA_PERIODIC_LEECH:
            case SPELL_AURA_PERIODIC_DAMAGE_PERCENT:
                return true;
            default:
                return false;
        }
    }

    bool TriggersASpell(SpellEffectInfo const& effect)
    {
        if (!effect.TriggerSpell)
            return false;
        if (effect.IsEffect(SPELL_EFFECT_TRIGGER_SPELL) || effect.IsEffect(SPELL_EFFECT_TRIGGER_MISSILE))
            return true;
        return effect.IsAura() && (effect.ApplyAuraName == SPELL_AURA_PERIODIC_TRIGGER_SPELL
            || effect.ApplyAuraName == SPELL_AURA_PERIODIC_TRIGGER_SPELL_WITH_VALUE);
    }

    // A damaging or healing spell (the Lightbound Choker's): one of its effects deals damage or heals, or one of them
    // triggers a spell that does, one level deep (a channel's bolts, a missile's impact).
    bool DamagesOrHeals(SpellInfo const* spellInfo, uint8 depth = 1)
    {
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            SpellEffectInfo const& effect = spellInfo->Effects[i];
            if (DamagesOrHealsEffect(effect))
                return true;
            if (depth == 0 || !TriggersASpell(effect))
                continue;
            SpellInfo const* triggered = sSpellMgr->GetSpellInfo(effect.TriggerSpell);
            if (triggered && triggered != spellInfo && DamagesOrHeals(triggered, depth - 1))
                return true;
        }
        return false;
    }
}

// 214681 Earthen Trample: the knockback never lands on a boss.
class spell_uldaman_item_earthen_trample : public SpellScript
{
    PrepareSpellScript(spell_uldaman_item_earthen_trample);

    void HandleKnockBack(SpellEffIndex effIndex)
    {
        Unit* target = GetHitUnit();
        if (target && !CanKnockBack(KnockbackSignsOf(target)))
            PreventHitDefaultEffect(effIndex);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_uldaman_item_earthen_trample::HandleKnockBack, EFFECT_1,
            SPELL_EFFECT_KNOCK_BACK);
    }
};

// 214680 Waking Stone: an earthen marches ahead of the wearer and tramples the enemies in its path.
class spell_uldaman_item_waking_stone : public AuraScript
{
    PrepareAuraScript(spell_uldaman_item_waking_stone);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_WAKING_STONE_TRAMPLE) });
    }

    Creature* Earthen() const
    {
        return _earthen ? ObjectAccessor::GetCreature(*GetTarget(), _earthen) : nullptr;
    }

    // The earthen appears ahead of the wearer and runs to the first obstacle or effect 1's yards ahead.
    void HandleApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        Unit* wearer = GetTarget();
        if (!wearer->IsInWorld())
            return;

        Position const start = wearer->GetFirstCollisionPosition(kEarthenStartDistance, 0.0f);
        _end = wearer->GetFirstCollisionPosition(float(std::max(aurEff->GetAmount(), 0)), 0.0f);
        uint32 const stayMs = uint32(std::max(GetMaxDuration(), 0)) + kEarthenTailMs;
        TempSummon* earthen = wearer->SummonCreature(NPC_WAKING_STONE_EARTHEN, start, TEMPSUMMON_TIMED_DESPAWN,
            stayMs);
        if (!earthen)
            return;     // the first tick finds no earthen and ends the march
        earthen->SetReactState(REACT_PASSIVE);
        earthen->SetWalk(false);
        earthen->GetMotionMaster()->MovePoint(kMarchPointId, _end, FORCED_MOVEMENT_RUN);
        _earthen = earthen->GetGUID();
        _last = ToPoint(start);
        _trampled = TrampleList{};
        LOG_DEBUG(kLog, "uldaman-items waking stone {} sent an earthen {:.1f} yd", wearer->GetGUID().ToString(),
            wearer->GetExactDist2d(_end.GetPositionX(), _end.GetPositionY()));
    }

    // Every enemy in combat the step from `from` to `to` passed, not trampled yet this march.
    void Sweep(Unit* wearer, Creature* earthen, PathPoint const& from, PathPoint const& to, AuraEffect const* aurEff)
    {
        AuraEffect const* width = GetEffect(EFFECT_1);
        float const halfWidth = width ? float(std::max(width->GetAmount(), 0)) : 0.0f;
        float const step = std::sqrt((to.x - from.x) * (to.x - from.x) + (to.y - from.y) * (to.y - from.y));
        float const radius = step + halfWidth + kSearchMargin;

        std::list<Unit*> found;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(earthen, wearer, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(earthen, found, check);
        Cell::VisitObjects(earthen, searcher, radius);

        uint32 const trampleId = TierSpell(GetSpellInfo(), SPELL_WAKING_STONE_TRAMPLE);
        for (Unit* unit : found)
        {
            // In combat (a march never pulls a pack), attackable, not under a crowd control that damage breaks, in the
            // path and in the earthen's sight; once per march.
            if (!unit->IsAlive() || !unit->IsInCombat() || !wearer->IsValidAttackTarget(unit)
                || unit->HasBreakableByDamageCrowdControlAura(wearer)
                || !OnMarchPath(from, to, ToPoint(*unit), unit->GetCombatReach(), halfWidth)
                || !earthen->IsWithinLOSInMap(unit) || !MarkTrampled(_trampled, unit->GetGUID().GetRawValue()))
                continue;
            wearer->CastSpell(unit, trampleId, true, nullptr, aurEff);
            LOG_DEBUG(kLog, "uldaman-items waking stone {} trampled {} ({})", wearer->GetGUID().ToString(),
                unit->GetGUID().ToString(), trampleId);
        }
    }

    void HandleTick(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        Creature* earthen = Earthen();
        bool const earthenHere = earthen && earthen->IsInWorld() && earthen->IsAlive();
        bool const wearerHere = wearer->IsInWorld() && wearer->IsAlive();
        float const toEnd = earthenHere ? earthen->GetExactDist2d(_end.GetPositionX(), _end.GetPositionY()) : 0.0f;
        MarchStep const step = StepMarch(wearerHere, earthenHere, toEnd);
        if (step == MarchStep::Gone)
        {
            Remove();
            return;
        }

        PathPoint const now = ToPoint(*earthen);
        Sweep(wearer, earthen, _last, now, aurEff);
        _last = now;
        if (step == MarchStep::Arrived)
            Remove();
    }

    // Any end of the march (arrived, the 4 sec ran out, the wearer died or left): the earthen goes too.
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Creature* earthen = Earthen())
            earthen->DespawnOrUnsummon();
        _earthen.Clear();
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_uldaman_item_waking_stone::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_uldaman_item_waking_stone::HandleTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_uldaman_item_waking_stone::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    ObjectGuid _earthen;
    Position _end;
    PathPoint _last;
    TrampleList _trampled;
};

// 214682 Lightbound Choker: a damaging or healing spell of another school than the last grants Two Lights.
class spell_uldaman_item_lightbound_choker : public AuraScript
{
    PrepareAuraScript(spell_uldaman_item_lightbound_choker);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_CHOKER_TWO_LIGHTS) });
    }

    // The wearer's own cast, at its cast phase (once per cast), that counts: not triggered, not an item's, not an auto
    // repeat, not passive, and damaging or healing by its data.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell || eventInfo.GetActor() != GetTarget() || !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST))
            return false;
        SpellInfo const* spellInfo = spell->GetSpellInfo();
        return CountsForLights(spell->IsTriggered(), spell->m_CastItem != nullptr, spellInfo->IsAutoRepeatRangedSpell(),
            spellInfo->IsPassive(), DamagesOrHeals(spellInfo));
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return;

        uint32 const school = uint32(spell->GetSpellInfo()->GetSchoolMask());
        if (NoteSchool(_memory, school) != LightsStep::Different)
            return;
        Unit* wearer = GetTarget();
        uint32 const lightsId = TierSpell(GetSpellInfo(), SPELL_CHOKER_TWO_LIGHTS);
        wearer->CastSpell(wearer, lightsId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "uldaman-items choker {} lit by {} (school {}, {})", wearer->GetGUID().ToString(),
            spell->GetSpellInfo()->Id, school, lightsId);
    }

    // Put on or taken off (a login, a swap): no last school.
    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        _memory = LightsMemory{};
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        _memory = LightsMemory{};
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_uldaman_item_lightbound_choker::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_uldaman_item_lightbound_choker::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_uldaman_item_lightbound_choker::HandleApply, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_uldaman_item_lightbound_choker::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    LightsMemory _memory;
};

// 214685 Disk Replay: heals each recorded target its share, a part per tick.
class spell_uldaman_item_disk_replay : public AuraScript
{
    PrepareAuraScript(spell_uldaman_item_disk_replay);

public:
    // Called by the recording right after it cast this replay: each target's share of what was recorded.
    void SetRecord(DiskRecord const& record, int32 sharePct)
    {
        _replay = record;
        for (uint32 i = 0; i < _replay.count && i < kMaxRecorded; ++i)
            _replay.entries[i].amount = ReplayShare(record.entries[i].amount, sharePct);
    }

private:
    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DISK_REPLAY_HEAL });
    }

    // A target alive, on the wearer's map and within the heal's range gets this tick's part; one out of reach misses
    // this tick only.
    void HandleTick(AuraEffect const* aurEff)
    {
        Unit* wearer = GetTarget();
        SpellInfo const* heal = sSpellMgr->GetSpellInfo(SPELL_DISK_REPLAY_HEAL);
        if (!heal || !wearer->IsInWorld() || !wearer->IsAlive())
            return;
        float const range = heal->GetMaxRange(true);
        uint32 const ticks = uint32(std::max(aurEff->GetTotalTicks(), 0));
        for (uint32 i = 0; i < _replay.count && i < kMaxRecorded; ++i)
        {
            DiskEntry const& entry = _replay.entries[i];
            int32 const amount = int32(ReplayTickAmount(entry.amount, ticks, aurEff->GetTickNumber()));
            if (amount <= 0)
                continue;
            Unit* target = ObjectAccessor::GetUnit(*wearer, ObjectGuid(entry.guid));
            if (!target || !target->IsInWorld() || !target->IsAlive() || !wearer->IsWithinDistInMap(target, range))
                continue;
            wearer->CastCustomSpell(target, SPELL_DISK_REPLAY_HEAL, &amount, nullptr, nullptr, true, nullptr, aurEff);
            LOG_DEBUG(kLog, "uldaman-items disk {} replayed {} on {} (tick {} of {})", wearer->GetGUID().ToString(),
                amount, target->GetGUID().ToString(), aurEff->GetTickNumber(), ticks);
        }
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_uldaman_item_disk_replay::HandleTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }

    DiskRecord _replay;
};

// 214684 Fragment of the Disks: records the wearer's healing, then hands it to the replay.
class spell_uldaman_item_fragment_of_the_disks : public AuraScript
{
    PrepareAuraScript(spell_uldaman_item_fragment_of_the_disks);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DISK_REPLAY, SPELL_DISK_REPLAY_HEAL });
    }

    // A heal of the wearer's, direct or a tick, that healed something. Not an item's Use (a cast with m_CastItem; a
    // tick has no Spell, so an item's heal over time, a bandage, is recorded), not a heal sized from another heal
    // (IGNORE_CASTER_MODIFIERS: Beacon of Light, the Sergeant's Whistle's copy, the Disk's own replay). The actor is
    // the wearer: a pet's or a totem's heal (Healing Stream Totem, a Lightwell) is not recorded.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        SpellInfo const* healSpell = heal ? heal->GetSpellInfo() : nullptr;
        if (!healSpell || !heal->GetEffectiveHeal() || !eventInfo.GetActionTarget()
            || eventInfo.GetActor() != GetTarget())
            return false;
        if (healSpell->Id == SPELL_DISK_REPLAY_HEAL || healSpell->HasAttribute(SPELL_ATTR3_IGNORE_CASTER_MODIFIERS))
            return false;
        Spell const* spell = eventInfo.GetProcSpell();
        return !(spell && spell->m_CastItem);
    }

    // The effective healing (no overhealing), before the healed target's own healing taken modifiers: the replay is a
    // heal of its own and takes them once.
    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        HealInfo const* heal = eventInfo.GetHealInfo();
        Unit* healed = eventInfo.GetActionTarget();
        if (!heal || !healed)
            return;

        bool const tick = (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) != 0;
        uint32 const probe = healed->SpellHealingBonusTaken(GetTarget(), heal->GetSpellInfo(), kTakenProbe,
            tick ? DOT : HEAL);
        uint32 const amount = UndoTakenMods(heal->GetEffectiveHeal(), probe);
        if (Record(_record, healed->GetGUID().GetRawValue(), amount))
            LOG_DEBUG(kLog, "uldaman-items disk {} recorded {} ({} landed) on {}", GetTarget()->GetGUID().ToString(),
                amount, heal->GetEffectiveHeal(), healed->GetGUID().ToString());
    }

    // The recording ran out: the replay starts with the record (any other end, death included, replays nothing).
    void HandleRemove(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        DiskRecord const record = _record;
        _record = DiskRecord{};
        Unit* wearer = GetTarget();
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE || record.count == 0
            || !wearer->IsInWorld() || !wearer->IsAlive())
            return;

        int32 const share = aurEff->GetAmount();
        wearer->CastSpell(wearer, SPELL_DISK_REPLAY, true);
        Aura* replay = wearer->GetAura(SPELL_DISK_REPLAY, wearer->GetGUID());
        auto* holder = replay ? replay->GetScript<spell_uldaman_item_disk_replay>("spell_uldaman_item_disk_replay")
            : nullptr;
        if (!holder)
        {
            if (replay)
                replay->Remove();
            return;
        }
        holder->SetRecord(record, share);
        LOG_DEBUG(kLog, "uldaman-items disk {} replays {} target(s) at {}%", wearer->GetGUID().ToString(), record.count,
            share);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_uldaman_item_fragment_of_the_disks::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_uldaman_item_fragment_of_the_disks::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_uldaman_item_fragment_of_the_disks::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    DiskRecord _record;
};

void AddSC_uldaman_hard_mode_items()
{
    RegisterSpellScript(spell_uldaman_item_waking_stone);
    RegisterSpellScript(spell_uldaman_item_earthen_trample);
    RegisterSpellScript(spell_uldaman_item_lightbound_choker);
    RegisterSpellScript(spell_uldaman_item_fragment_of_the_disks);
    RegisterSpellScript(spell_uldaman_item_disk_replay);
}
