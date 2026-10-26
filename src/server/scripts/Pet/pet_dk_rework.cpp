/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Death Knight rework minion AIs (death-knight-rework S3a): the Ebon Gargoyle fork (27829 ScriptName override, fixes
 * P0 9d), the Lesser Ghoul (300320) and the Abomination (300321). Owner via GetOwner() only; Attack() before MoveChase.
 * Rules: .agents/plans/death-knight-rework/death-knight-rework.S3a-WP-BRIEF.md.
 */

#include "CellImpl.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "DeathKnightMechanics.h"
#include "EngagementMechanics.h"
#include "EventMap.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"

namespace
{
    // Stock ids without a DeathKnightData:: name (brief D14).
    constexpr uint32 SPELL_DK_SANCTUARY = 54661;
    constexpr uint32 SPELL_DK_NIGHT_OF_THE_DEAD_AVOIDANCE = 62137;
    constexpr uint32 NIGHT_OF_THE_DEAD_ICON = 2718;

    // Stock Gargoyle timings (pet_dk.cpp): the fly-away takes ~4 s, the summon spell lasts 26 s (brief D13), the AI
    // despawns the Gargoyle by 24 s.
    constexpr uint32 GARGOYLE_DESPAWN_MS = 24000;
    constexpr uint32 GARGOYLE_LANDING_FALLBACK_MS = 4000; // fly-in is ~2.1 s; never wait longer for the landing
    constexpr uint32 GARGOYLE_POLL_MS = 100;
    constexpr float GARGOYLE_CAST_RANGE = 40.0f;
    constexpr uint32 GARGOYLE_FLY_POINT = 1;

    constexpr uint32 MINION_POLL_MS = 250;
    constexpr uint8 SUMMON_TARGET_RESOLVE_POLLS = 3;
    constexpr float MINION_TARGET_RANGE = 40.0f;

    // Any player owner (Freepick / Classless DKs included): GetOwner() only, never GetOwningPlayer.
    Player* GetDeathKnightOwner(Creature const* minion)
    {
        return DeathKnight::GetMinionOwner(minion);
    }

    enum GargoyleEvent : uint32
    {
        EVENT_GARGOYLE_MARK = 1,
        EVENT_GARGOYLE_POLL = 2,
        EVENT_GARGOYLE_FLY_AWAY = 3,
        EVENT_GARGOYLE_DESPAWN = 4
    };

    constexpr uint32 EVENT_MINION_POLL = 1;
}

/*
 * 27829 - Ebon Gargoyle (ScriptName override; every stock column and the Pet.cpp scaling auras stay). Fork of the stock
 * npc_pet_dk_ebon_gargoyle (pet_dk.cpp) with the target logic replaced (P0 9d: the stock AI only re-read the DK's
 * selection when its victim was gone, so it never followed a target switch) and the cadence reworked: 100 ms poll, no
 * 80% roll, first cast on landing, no strike that cannot finish before the fly-away.
 */
class npc_dk_ebon_gargoyle_rework : public ScriptedAI
{
public:
    explicit npc_dk_ebon_gargoyle_rework(Creature* creature) : ScriptedAI(creature) { }

    void MovementInform(uint32 type, uint32 point) override
    {
        if (type != POINT_MOTION_TYPE || point != GARGOYLE_FLY_POINT || _leaving)
            return;

        // The fly-in ended: land (the fly-away charge uses the same point id, hence the _leaving test above).
        me->SetCanFly(false);
        me->SetDisableGravity(false);
        _landed = true;
    }

    void JustExitedCombat() override
    {
        EngagementOver();
    }

    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        if (!_EnterEvadeMode())
            return;

        me->ClearUnitState(UNIT_STATE_EVADE);

        if (Unit* owner = me->GetOwner())
        {
            me->GetMotionMaster()->Clear(false);
            me->GetMotionMaster()->MoveFollow(owner, PET_FOLLOW_DIST, me->GetFollowAngle(), MOTION_SLOT_ACTIVE);
        }
    }

    void InitializeAI() override
    {
        ScriptedAI::InitializeAI();

        Player* owner = GetDeathKnightOwner(me);
        if (!owner)
        {
            _inert = true;
            return;
        }

        _summonMs = getMSTime();

        // Xinef: Night of the Dead avoidance (stock InitializeAI, unchanged).
        if (Aura* aur = me->GetAura(SPELL_DK_NIGHT_OF_THE_DEAD_AVOIDANCE))
            if (AuraEffect* aurEff = owner->GetAuraEffect(SPELL_AURA_ADD_FLAT_MODIFIER, SPELLFAMILY_DEATHKNIGHT,
                NIGHT_OF_THE_DEAD_ICON, EFFECT_0))
                if (aur->GetEffect(EFFECT_0))
                    aur->GetEffect(EFFECT_0)->SetAmount(-aurEff->GetSpellInfo()->Effects[EFFECT_2].CalcValue());

        // Area-damage ward (U39): applied by the AI, gone with the creature.
        if (!me->HasAura(DeathKnightData::SPELL_MINION_AREA_WARD))
            me->AddAura(DeathKnightData::SPELL_MINION_AREA_WARD, me);

        me->SetCanFly(true);
        me->SetDisableGravity(true);

        float const tz = me->GetMapHeight(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), true,
            MAX_FALL_DISTANCE);
        me->GetMotionMaster()->MoveCharge(me->GetPositionX(), me->GetPositionY(), tz, 7.0f, GARGOYLE_FLY_POINT);
        me->AddUnitState(UNIT_STATE_NO_ENVIRONMENT_UPD);

        _events.ScheduleEvent(EVENT_GARGOYLE_MARK, 0ms);
        _events.ScheduleEvent(EVENT_GARGOYLE_POLL, Milliseconds(GARGOYLE_POLL_MS));
        _events.ScheduleEvent(EVENT_GARGOYLE_FLY_AWAY, Milliseconds(DeathKnightData::GARGOYLE_WINDOW_MS));
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void UpdateAI(uint32 diff) override
    {
        if (_inert)
            return;

        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_GARGOYLE_MARK:
                    CaptureSummonTarget();
                    break;
                case EVENT_GARGOYLE_POLL:
                    Poll();
                    _events.ScheduleEvent(EVENT_GARGOYLE_POLL, Milliseconds(GARGOYLE_POLL_MS));
                    break;
                case EVENT_GARGOYLE_FLY_AWAY:
                    FlyAway();
                    break;
                case EVENT_GARGOYLE_DESPAWN:
                    me->DespawnOrUnsummon();
                    break;
                default:
                    break;
            }
        }
    }

private:
    // The target Summon Gargoyle was cast at carries its marker aura (49206 eff1) from the spell's own hit; the first
    // tick finds it (as the stock AI did), keeps the guid as the last-resort target and removes the marker.
    void CaptureSummonTarget()
    {
        std::list<Unit*> targets;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(me, me, 50.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(me, targets, check);
        Cell::VisitObjects(me, searcher, 50.0f);
        for (Unit* target : targets)
            if (target->GetAura(DeathKnightData::SPELL_SUMMON_GARGOYLE, me->GetOwnerGUID()))
            {
                target->RemoveAura(DeathKnightData::SPELL_SUMMON_GARGOYLE, me->GetOwnerGUID());
                _summonTargetGUID = target->GetGUID();
                break;
            }
    }

    bool IsUsableTarget(Player const* owner, Unit* target, SpellInfo const* strike) const
    {
        return target && target->IsAlive() && target->IsInMap(me) && me->IsValidAttackTarget(target) &&
            owner->CanSeeOrDetect(target) && !target->IsImmunedToSpell(strike);
    }

    // U17 target order: the owner's current target if engaged (victim, else the selected unit) -> the current victim ->
    // the nearest engaged hostile -> the summon target. The current victim is never passed to SelectEngagedTarget as
    // the preferred one (it would be tried first and re-create P0 9d).
    Unit* SelectStrikeTarget(Player* owner, SpellInfo const* strike) const
    {
        if (Unit* ownerVictim = owner->GetVictim())
            if (IsUsableTarget(owner, ownerVictim, strike) && Engagement::IsEngagedWithOwnerOrGroup(ownerVictim, owner))
                return ownerVictim;

        if (Unit* selected = ObjectAccessor::GetUnit(*owner, owner->GetTarget()))
            if (IsUsableTarget(owner, selected, strike) && Engagement::IsEngagedWithOwnerOrGroup(selected, owner))
                return selected;

        if (Unit* victim = me->GetVictim())
            if (IsUsableTarget(owner, victim, strike) && Engagement::IsEngagedWithOwnerOrGroup(victim, owner))
                return victim;

        if (Unit* engaged = Engagement::SelectEngagedTarget(me, owner, ObjectGuid::Empty, GARGOYLE_CAST_RANGE))
            if (IsUsableTarget(owner, engaged, strike))
                return engaged;

        if (Unit* summonTarget = ObjectAccessor::GetUnit(*me, _summonTargetGUID))
            if (IsUsableTarget(owner, summonTarget, strike))
                return summonTarget;

        return nullptr;
    }

    void Poll()
    {
        if (_leaving)
            return;

        // First cast on landing.
        if (!_landed)
        {
            if (GetMSTimeDiffToNow(_summonMs) < GARGOYLE_LANDING_FALLBACK_MS)
                return;
            _landed = true;
        }

        // Never switch or recast in the middle of a strike.
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        Player* owner = GetDeathKnightOwner(me);
        SpellInfo const* strike = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_GARGOYLE_STRIKE);
        if (!owner || !strike)
            return;

        Unit* target = SelectStrikeTarget(owner, strike);
        if (!target)
        {
            if (me->GetVictim())
                me->CombatStop(true);

            if (!_following)
            {
                me->GetMotionMaster()->Clear(false);
                me->GetMotionMaster()->MoveFollow(owner, PET_FOLLOW_DIST, me->GetFollowAngle());
                _following = true;
            }
            return;
        }

        if (me->GetVictim() != target)
        {
            me->GetMotionMaster()->Clear(false);
            AttackStartCaster(target, GARGOYLE_CAST_RANGE);
            _following = false;
        }
        else if (me->GetMotionMaster()->GetMotionSlotType(MOTION_SLOT_ACTIVE) != CHASE_MOTION_TYPE)
            me->GetMotionMaster()->MoveChase(target, GARGOYLE_CAST_RANGE);

        if (me->HasUnitState(UNIT_STATE_LOST_CONTROL) ||
            me->GetMotionMaster()->GetMotionSlotType(MOTION_SLOT_CONTROLLED) != NULL_MOTION_TYPE)
            return;

        if (me->HasSilenceAura() || me->IsSpellProhibited(SPELL_SCHOOL_MASK_NATURE))
            return;

        if (!me->IsWithinDistInMap(target, strike->GetMaxRange(false, me)) || !me->IsWithinLOSInMap(target))
            return;

        // Only a strike that finishes before the fly-away (the cast time carries the spell-haste mirror).
        if (GetMSTimeDiffToNow(_summonMs) + strike->CalcCastTime(me) > uint32(DeathKnightData::GARGOYLE_WINDOW_MS))
            return;

        DoCast(target, DeathKnightData::SPELL_GARGOYLE_STRIKE);
    }

    void FlyAway()
    {
        if (_leaving)
            return;

        _leaving = true;

        // Stop fighting.
        me->InterruptNonMeleeSpells(false);
        me->CombatStop(true);
        me->ApplyModFlag(UNIT_FIELD_FLAGS, UNIT_FLAG_NON_ATTACKABLE, true);

        // Sanctuary.
        me->CastSpell(me, SPELL_DK_SANCTUARY, true);
        me->SetReactState(REACT_PASSIVE);

        me->SetSpeed(MOVE_FLIGHT, 1.0f, true);
        me->SetSpeed(MOVE_RUN, 1.0f, true);
        float const x = me->GetPositionX() + 20 * cos(me->GetOrientation());
        float const y = me->GetPositionY() + 20 * std::sin(me->GetOrientation());
        float const z = me->GetPositionZ() + 40;
        me->DisableSpline();
        me->GetMotionMaster()->Clear(false);

        me->GetMotionMaster()->MoveCharge(x, y, z, 7.0f, GARGOYLE_FLY_POINT);
        me->SetCanFly(true);
        me->SetDisableGravity(true);

        // It "leaves" now: the Necromancy stacks go with it (OnCreatureRemoveWorld covers every other path).
        if (Player* owner = GetDeathKnightOwner(me))
            DeathKnight::OnGargoyleLeave(owner);

        // The summon spell lasts 26 s and the fly-away takes ~4 s: despawn by 24 s.
        uint32 const elapsed = GetMSTimeDiffToNow(_summonMs);
        _events.ScheduleEvent(EVENT_GARGOYLE_DESPAWN,
            Milliseconds(elapsed < GARGOYLE_DESPAWN_MS ? GARGOYLE_DESPAWN_MS - elapsed : 0));
    }

    EventMap _events;
    ObjectGuid _summonTargetGUID;
    uint32 _summonMs = 0;
    bool _inert = false;
    bool _landed = false;
    bool _leaving = false;
    bool _following = false;
};

/*
 * Shared melee-minion behaviour: REACT_PASSIVE, a 250 ms poll that picks the target, Attack(target, true) BEFORE
 * MoveChase (ChaseMovementGenerator pauses while GetVictim() != its target, bug log "A guardian given MoveChase never
 * leaves its owner"), and 2.0 s swings (creature_template BaseAttackTime) through DoMeleeAttackIfReady.
 */
class npc_dk_melee_minion_base : public CreatureAI
{
public:
    explicit npc_dk_melee_minion_base(Creature* creature) : CreatureAI(creature) { }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
            if (eventId == EVENT_MINION_POLL)
            {
                DoChase();
                _events.ScheduleEvent(EVENT_MINION_POLL, Milliseconds(MINION_POLL_MS));
            }

        DoMeleeAttackIfReady();
    }

protected:
    // The target to hit now, or nullptr to fall back to following the owner.
    virtual Unit* SelectMinionTarget(Player* owner) = 0;

    void StartMinion()
    {
        me->SetReactState(REACT_PASSIVE);
        _events.ScheduleEvent(EVENT_MINION_POLL, 0ms);
    }

    void DoChase()
    {
        Player* owner = GetDeathKnightOwner(me);
        if (!owner)
            return;

        Unit* target = SelectMinionTarget(owner);
        if (target)
        {
            if (target->GetGUID() != _chasingGUID || me->GetVictim() != target)
            {
                me->Attack(target, true);
                // A chase that starts already in range sends no spline of its own, so the follow spline still in
                // flight would carry the minion back to the owner.
                me->StopMoving();
                me->GetMotionMaster()->MoveChase(target);
                _chasingGUID = target->GetGUID();
            }
        }
        else if (!_chasingGUID.IsEmpty())
        {
            me->AttackStop();
            me->GetMotionMaster()->MoveFollow(owner, PET_FOLLOW_DIST, me->GetFollowAngle());
            _chasingGUID.Clear();
        }
    }

    // The owner's engaged target (its victim, else its selected unit, else the nearest engaged hostile).
    Unit* SelectOwnerEngagedTarget(Player* owner)
    {
        return Engagement::SelectEngagedTarget(me, owner, ObjectGuid::Empty, MINION_TARGET_RANGE);
    }

    ObjectGuid _chasingGUID;
    EventMap _events;
};

/*
 * 300320 - Lesser Ghoul. Attacks the target the owner had when it was summoned, then follows the owner's engaged
 * target. The 15 s lifetime is the summon spell's duration.
 */
class npc_dk_lesser_ghoul : public npc_dk_melee_minion_base
{
public:
    explicit npc_dk_lesser_ghoul(Creature* creature) : npc_dk_melee_minion_base(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        // The summon target (copied to the ghoul in OnMinionAddWorld) is read lazily on the first polls.
        if (GetDeathKnightOwner(me))
            StartMinion();
    }

    // The counter (203470) drops at once instead of waiting for the corpse to despawn.
    void JustDied(Unit* /*killer*/) override
    {
        if (TempSummon* summon = me->ToTempSummon())
            summon->UnSummon();
    }

protected:
    Unit* SelectMinionTarget(Player* owner) override
    {
        if (!_summonTargetResolved)
            ResolveSummonTarget(owner);

        if (!_summonTargetGUID.IsEmpty())
        {
            Unit* summonTarget = ObjectAccessor::GetUnit(*me, _summonTargetGUID);
            if (summonTarget && summonTarget->IsAlive() && summonTarget->IsInMap(me) &&
                me->IsValidAttackTarget(summonTarget))
                return summonTarget;

            // The summon target is gone: from now on follow the owner.
            _summonTargetGUID.Clear();
        }

        return SelectOwnerEngagedTarget(owner);
    }

private:
    // The target SummonLesserGhoul was given (stored on the ghoul), if alive, attackable and engaged; else the owner's
    // selected unit under the same test. Retried for a few polls in case the store is not there yet.
    void ResolveSummonTarget(Player* owner)
    {
        auto isGood = [&](Unit* unit)
        {
            return unit && unit->IsAlive() && me->IsValidAttackTarget(unit) &&
                Engagement::IsEngagedWithOwnerOrGroup(unit, owner);
        };

        ObjectGuid const stored = DeathKnight::GetLesserGhoulSummonTarget(me);
        if (!stored.IsEmpty())
        {
            _summonTargetResolved = true;
            if (isGood(ObjectAccessor::GetUnit(*me, stored)))
                _summonTargetGUID = stored;
            return;
        }

        if (++_resolveAttempts < SUMMON_TARGET_RESOLVE_POLLS)
            return;

        _summonTargetResolved = true;
        if (Unit* selected = ObjectAccessor::GetUnit(*owner, owner->GetTarget()))
            if (isGood(selected))
                _summonTargetGUID = selected->GetGUID();
    }

    ObjectGuid _summonTargetGUID;
    uint8 _resolveAttempts = 0;
    bool _summonTargetResolved = false;
};

/*
 * 300321 - Abomination. Melees the owner's engaged target; the putrid cloud (203472, an aura on the Abomination, which
 * is therefore its caster: the cloud's AuraScript casts the ticks from it) and the area-damage ward (203474).
 */
class npc_dk_abomination : public npc_dk_melee_minion_base
{
public:
    explicit npc_dk_abomination(Creature* creature) : npc_dk_melee_minion_base(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        if (!GetDeathKnightOwner(me))
            return;

        if (!me->HasAura(DeathKnightData::SPELL_PUTRID_CLOUD))
            me->AddAura(DeathKnightData::SPELL_PUTRID_CLOUD, me);
        if (!me->HasAura(DeathKnightData::SPELL_MINION_AREA_WARD))
            me->AddAura(DeathKnightData::SPELL_MINION_AREA_WARD, me);

        StartMinion();
    }

protected:
    Unit* SelectMinionTarget(Player* owner) override
    {
        return SelectOwnerEngagedTarget(owner);
    }
};

void AddSC_deathknight_rework_pet_scripts()
{
    RegisterCreatureAI(npc_dk_ebon_gargoyle_rework);
    RegisterCreatureAI(npc_dk_lesser_ghoul);
    RegisterCreatureAI(npc_dk_abomination);
}
