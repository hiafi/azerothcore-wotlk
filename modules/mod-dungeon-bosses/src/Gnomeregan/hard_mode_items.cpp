/*
 * mod-dungeon-bosses, Gnomeregan: the hard mode item effects of Mekgineer Thermaplugg, the Whole Workshop (designer
 * text: docs/dungeons/gnomeregan-rework.md ## Loot, the hard mode list). The spells are
 * apps/dbc-tools/source/items/gnomeregan_hard_mode_effects.py; both damage numbers come from potency, so nothing here
 * sizes a hit. The scaled effects (scale="budget") carry their own copies on every tier above 71, bound to the same
 * scripts, so a script never casts a family spell by its base id: ItemSpellCopies::Resolve (the generated
 * ItemSpellCopies.h) gives the copy in the tier of the spell or aura it runs for, and the base id on the 71 tier.
 * Punched has no copies.
 *
 *   spell_gnomer_item_meltdown_pulse          214241 Radiation Pulse (Leaking Reactor Core's Meltdown, 214240, is pure
 *                                             data). Only enemies in combat.
 *   spell_gnomer_item_walking_bomb_launcher   214242 Walking Bomb Launcher (Equip). Each cast rolls once; on a proc
 *                                             the tier's mark 214243 lands on the target and a Launched Walking
 *                                             Bomb (301100, look only) runs at it from beside the wearer.
 *   spell_gnomer_item_walking_bomb            214243 Walking Bomb, the mark. Holds its bomb: within the fuse the wearer
 *                                             casts the tier's 214244 where the bomb stands; when the mark ends any
 *                                             other way the bomb falls apart.
 *   spell_gnomer_item_walking_bomb_blast      214244 Walking Bomb Blast. Only enemies in combat.
 *   spell_gnomer_item_master_punch_card       214245 Master Punch Card (Equip). Each different spell the wearer casts
 *                                             punches the card (214246, a stack); the last punch clears it and casts
 *                                             the tier's 214247, then the card is locked for effect 2's seconds.
 *
 * Every payout logs one DEBUG line, "gnomer-items <effect> ...", in module.dungeonbosses.
 */

#include "Creature.h"
#include "GameTime.h"
#include "GnomereganHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
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
#include <algorithm>
#include <list>

using namespace GnomereganHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    static_assert(kRangedHitFlags == (PROC_FLAG_DONE_RANGED_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS));
    static_assert(kOwnCastFlags == (PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
        | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
        | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG));

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

    // One roll per cast: true the first time a cast reaches the check, false for its later targets. An event without
    // a spell (an auto attack) always rolls. The engine runs the check before it rolls the spell_proc chance.
    bool FirstRollOfCast(CastStamp& rolled, ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return true;
        CastStamp const now{ spell, spell->GetSpellInfo()->Id, spell->m_cast_count,
            CastMoment(spell->GetDelayStart(), NowMs()) };
        if (SameCast(rolled, now))
            return false;
        rolled = now;
        return true;
    }

    // A spell's first rank: "a different spell" is a different first rank, so two ranks of one spell punch once.
    uint32 FirstRankOf(SpellInfo const* spellInfo)
    {
        SpellInfo const* first = spellInfo->GetFirstRankSpell();
        return first ? first->Id : spellInfo->Id;
    }

    // An area payout's in-combat filter: a bonus never pulls a pack.
    void KeepEnemiesInCombat(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject* object)
        {
            Unit const* unit = object->ToUnit();
            return !unit || !unit->IsInCombat();
        });
    }
}

// 214241 Radiation Pulse (Meltdown's tick): only enemies already in combat.
class spell_gnomer_item_meltdown_pulse : public SpellScript
{
    PrepareSpellScript(spell_gnomer_item_meltdown_pulse);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        KeepEnemiesInCombat(targets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_gnomer_item_meltdown_pulse::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
    }
};

// 214243 Walking Bomb, the mark on the bomb's target: blows its bomb at the fuse, sends it away when the mark ends.
class spell_gnomer_item_walking_bomb : public AuraScript
{
    PrepareAuraScript(spell_gnomer_item_walking_bomb);

public:
    // Called by the Launcher right after it summoned the bomb this mark waits for.
    void SetBomb(ObjectGuid bomb)
    {
        _bomb = bomb;
    }

private:
    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_BOMB_LAUNCHER_BLAST) });
    }

    Creature* Bomb() const
    {
        return _bomb ? ObjectAccessor::GetCreature(*GetTarget(), _bomb) : nullptr;
    }

    void HandleTick(AuraEffect const* aurEff)
    {
        Unit* target = GetTarget();
        Unit* wearer = GetCaster();
        Creature* bomb = Bomb();
        bool const bombHere = bomb && bomb->IsAlive();
        bool const withinFuse = bombHere && bomb->IsWithinDist(target, float(std::max(aurEff->GetAmount(), 0)));
        // A dead wearer cannot cast the blast (SPELL_FAILED_CASTER_DEAD), so the bomb falls apart.
        bool const wearerHere = wearer && wearer->IsInWorld() && wearer->IsAlive();
        BombStep const step = StepBomb(target->IsAlive(), wearerHere, bombHere, withinFuse);
        if (step == BombStep::Walk)
            return;

        if (step == BombStep::Blast)
        {
            uint32 const blastId = TierSpell(GetSpellInfo(), SPELL_BOMB_LAUNCHER_BLAST);
            wearer->CastSpell(bomb->GetPositionX(), bomb->GetPositionY(), bomb->GetPositionZ(), blastId, true, nullptr,
                aurEff);
            LOG_DEBUG(kLog, "gnomer-items bomb {} blew at {} ({})", wearer->GetGUID().ToString(),
                target->GetGUID().ToString(), blastId);
        }
        else
            LOG_DEBUG(kLog, "gnomer-items bomb on {} fell apart", target->GetGUID().ToString());
        Remove();
    }

    // Any end of the mark (blown, the target died or evaded, it ran out, the wearer left): the bomb goes too.
    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Creature* bomb = Bomb())
            bomb->DespawnOrUnsummon();
        _bomb.Clear();
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_gnomer_item_walking_bomb::HandleTick, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_gnomer_item_walking_bomb::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    ObjectGuid _bomb;
};

// 214242 Walking Bomb Launcher: ranged critical strikes may launch a Walking Bomb at the target.
class spell_gnomer_item_walking_bomb_launcher : public AuraScript
{
    PrepareAuraScript(spell_gnomer_item_walking_bomb_launcher);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_BOMB_LAUNCHER_MARK) });
    }

    // A living enemy the wearer can attack, and the cast's first roll (Multi-Shot is one roll).
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!victim || victim == wearer || !wearer->IsAlive() || !victim->IsAlive()
            || !wearer->IsValidAttackTarget(victim))
            return false;
        return FirstRollOfCast(_rolled, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Unit* victim = eventInfo.GetActionTarget();
        if (!victim || !wearer->IsInWorld())
            return;

        // The mark first: a target that refuses it (immune, evading) gets no bomb.
        uint32 const markId = TierSpell(GetSpellInfo(), SPELL_BOMB_LAUNCHER_MARK);
        wearer->CastSpell(victim, markId, true, nullptr, aurEff);
        Aura* mark = victim->GetAura(markId, wearer->GetGUID());
        auto* holder = mark ? mark->GetScript<spell_gnomer_item_walking_bomb>("spell_gnomer_item_walking_bomb")
            : nullptr;
        if (!holder)
            return;

        Position const spot = wearer->GetFirstCollisionPosition(kBombLaunchDistance, wearer->GetRelativeAngle(victim));
        uint32 const stayMs = uint32(std::max(mark->GetMaxDuration(), 0)) + kBombTailMs;
        TempSummon* bomb = wearer->SummonCreature(NPC_LAUNCHER_WALKING_BOMB, spot, TEMPSUMMON_TIMED_DESPAWN, stayMs);
        if (!bomb)
        {
            mark->Remove();
            return;
        }
        bomb->SetLevel(wearer->GetLevel(), false);
        bomb->SetReactState(REACT_PASSIVE);
        bomb->SetFacingToObject(victim);
        // Follow, never chase: ChaseMovementGenerator stops while its owner's victim is not its target (HasLostTarget),
        // and this passive faction 35 bomb never has a victim (docs/bugs-and-fixes.md, the Infernal 300154).
        // FollowMovementGenerator has no victim check and ends at the bomb's own combat reach from the target's center,
        // inside the fuse. Its walk state and speed are not inherited (a creature following a creature takes the
        // target's speed), so the bomb runs at its own speed_run, 8 yd per sec.
        bomb->SetWalk(false);
        bomb->GetMotionMaster()->MoveFollow(victim, 0.0f, 0.0f, MOTION_SLOT_ACTIVE, false, false);
        holder->SetBomb(bomb->GetGUID());
        LOG_DEBUG(kLog, "gnomer-items launcher {} sent a bomb at {} ({})", wearer->GetGUID().ToString(),
            victim->GetGUID().ToString(), markId);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_gnomer_item_walking_bomb_launcher::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_gnomer_item_walking_bomb_launcher::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }

    CastStamp _rolled;
};

// 214244 Walking Bomb Blast: only enemies already in combat.
class spell_gnomer_item_walking_bomb_blast : public SpellScript
{
    PrepareSpellScript(spell_gnomer_item_walking_bomb_blast);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        KeepEnemiesInCombat(targets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_gnomer_item_walking_bomb_blast::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 214245 Master Punch Card: each different spell punches the card; the last punch gives Clearance: PRISMATIC.
class spell_gnomer_item_master_punch_card : public AuraScript
{
    PrepareAuraScript(spell_gnomer_item_master_punch_card);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ SPELL_PUNCH_CARD_PUNCHED, TierSpell(spellInfo, SPELL_PUNCH_CARD_CLEARANCE) });
    }

    // The wearer's own cast, at its cast phase, that can punch, while the card is not locked, of a spell that has not
    // punched it yet. The visible stacks are read first: a card whose stacks went (death, a cancel) is a cleared card.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* wearer = GetTarget();
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell || eventInfo.GetActor() != wearer || !(eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST))
            return false;
        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!CountsAsPunch(spell->IsTriggered(), spell->m_CastItem != nullptr, spellInfo->IsAutoRepeatRangedSpell(),
            spellInfo->IsPassive()))
            return false;
        SyncCard(_card, StacksOf(wearer, SPELL_PUNCH_CARD_PUNCHED));
        return NowMs() >= _readyAtMs && !IsPunched(_card, FirstRankOf(spellInfo));
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* wearer = GetTarget();
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return;

        uint32 const firstRank = FirstRankOf(spell->GetSpellInfo());
        uint64 const now = NowMs();
        PunchResult const result = Punch(_card, firstRank, uint32(std::max(aurEff->GetAmount(), 0)), now, _readyAtMs);
        if (result == PunchResult::None)
            return;
        if (result == PunchResult::Punched)
        {
            wearer->CastSpell(wearer, SPELL_PUNCH_CARD_PUNCHED, true, nullptr, aurEff);
            return;
        }

        if (AuraEffect const* lock = GetEffect(EFFECT_1))
            _readyAtMs = now + uint64(std::max(lock->GetAmount(), 0)) * uint64(IN_MILLISECONDS);
        wearer->RemoveAurasDueToSpell(SPELL_PUNCH_CARD_PUNCHED);
        uint32 const clearanceId = TierSpell(GetSpellInfo(), SPELL_PUNCH_CARD_CLEARANCE);
        wearer->CastSpell(wearer, clearanceId, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "gnomer-items punch card {} cleared by {} ({})", wearer->GetGUID().ToString(), firstRank,
            clearanceId);
    }

    // Put on or taken off (a login, a swap): a blank card. A login reloads the stacks but not which spells made them.
    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        ClearCard(_card);
        GetTarget()->RemoveAurasDueToSpell(SPELL_PUNCH_CARD_PUNCHED);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        ClearCard(_card);
        GetTarget()->RemoveAurasDueToSpell(SPELL_PUNCH_CARD_PUNCHED);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_gnomer_item_master_punch_card::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_gnomer_item_master_punch_card::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_gnomer_item_master_punch_card::HandleApply, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_gnomer_item_master_punch_card::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }

    PunchCard _card;
    uint64 _readyAtMs = 0;
};

void AddSC_gnomer_hard_mode_items()
{
    RegisterSpellScript(spell_gnomer_item_meltdown_pulse);
    RegisterSpellScript(spell_gnomer_item_walking_bomb);
    RegisterSpellScript(spell_gnomer_item_walking_bomb_launcher);
    RegisterSpellScript(spell_gnomer_item_walking_bomb_blast);
    RegisterSpellScript(spell_gnomer_item_master_punch_card);
}
