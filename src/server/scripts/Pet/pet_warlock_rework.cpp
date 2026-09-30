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
 * Warlock rework - Demonology pass (S3) guardian AIs
 * (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5, warlock-rework.DEMONOLOGY.md §2.7/§7.2-7.4).
 * Wild Imp / Imp Gang Boss (npc_warl_wild_imp, creatures 300150/300151), Dreadstalker
 * (npc_warl_dreadstalker, 300152), Doomguard (npc_warl_doomguard_guardian, 300153) and Infernal
 * (npc_warl_infernal_guardian, 300154) - all SummonProperties 1021 guardians (PLAN §2), declared
 * via stage T1's creature_template()/creature_model() DSL calls, never SummonProperties
 * 711/1161/1562 (those dismiss the warlock's main demon).
 *
 * Every AI here follows the tentacle/Mirror Image precedent (spell_priest_shadow.cpp's
 * npc_pri_tentacle_of_madness, pet_mage.cpp's npc_pet_mage_mirror_image): IsSummonedBy() issues no
 * MoveFollow/MoveChase of its own - Spell::SummonGuardian overwrites the motion master with
 * MoveFollow(caster) right after this hook returns (SpellEffects.cpp:6412-6417) - and every AI
 * calls SetReactState(REACT_PASSIVE) explicitly, since Guardian::InitStats defaults to
 * REACT_AGGRESSIVE (TemporarySummon.cpp:446) and these guardians are meant to be non-attackable,
 * fully custom-targeted helpers (DEMONOLOGY.md §5.0/§7.2-§7.4, §11 Q17's SPELL_ATTR1_NO_THREAT on
 * every guardian spell is WP-A's data half of the same rule).
 *
 * Separate from src/server/scripts/Spells/spell_warlock_demonology.cpp because pets_script_loader.cpp
 * is a distinct upstream-owned loader from spells_script_loader.cpp (cpp-scripts.md: "Creature
 * scripts: prefer RegisterCreatureAI for new code").
 */

#include "CreatureAI.h"
#include "CreatureScript.h"
#include "EventMap.h"
#include "Log.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "PetScript.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include "WarlockMechanics.h"
#include <algorithm>
#include <array>

namespace
{
    // Destruction talent (2,0) Demonic Power - not a Demonology id, so not part of the frozen
    // header; duplicated locally the same way spell_warlock_destruction.cpp/warlock_hooks.cpp
    // duplicate cross-spec ids rather than widening WarlockMechanics.h. §11 Q7 default (scripted):
    // only the plain Wild Imp's Fel Firebolt cast speed changes, read here at spawn.
    constexpr uint32 SPELL_DESTRO_DEMONIC_POWER_R1 = 18126;
    constexpr uint32 SPELL_DESTRO_DEMONIC_POWER_R2 = 18127;

    // Private copy of WarlockMechanics.cpp's own rank-amount helper (internal linkage - can't be
    // shared across translation units without a header change, and this is the only rank-value
    // read this file needs).
    template <std::size_t N>
    int32 GetHighestRankAmount(Unit const* unit, std::array<uint32, N> const& ranksLowToHigh, uint8 effIndex)
    {
        if (!unit)
            return 0;

        for (std::size_t i = ranksLowToHigh.size(); i-- > 0;)
            if (AuraEffect const* eff = unit->GetAuraEffect(ranksLowToHigh[i], effIndex))
                return eff->GetAmount();
        return 0;
    }

    // ---- Wild Imp / Imp Gang Boss (300150/300151) tuning + local ids ----
    constexpr float WILD_IMP_ATTACK_RANGE = 40.0f;
    constexpr float WILD_IMP_CHASE_RANGE = 30.0f;
    constexpr uint32 WILD_IMP_UPDATE_INTERVAL_MS = 250;
    constexpr uint32 WILD_IMP_EXPIRE_MS = 60000;
    constexpr uint32 WILD_IMP_ENERGY_DEATH_DESPAWN_MS = 2500;
    constexpr uint32 WILD_IMP_IMPLODE_FALLBACK_MS = 2000;
    constexpr float WILD_IMP_IMPLODE_JUMP_SPEED_XY = 40.0f;
    constexpr float WILD_IMP_IMPLODE_JUMP_SPEED_Z = 6.0f;
    // Death Grip's own jump (57604) is 50/3 (SpellEffects.cpp:1201-1205); tuned down to <= 40 yd
    // covering the AI's own 40 yd attack range in well under 1 s, per DEMONOLOGY.md §7.2's
    // "tune in playtest" note.
    constexpr uint32 POINT_WILD_IMP_IMPLODE = 1;

    enum WildImpAIEvent : uint32
    {
        EVENT_WILD_IMP_UPDATE = 1,
        EVENT_WILD_IMP_EXPIRE = 2,
        EVENT_WILD_IMP_IMPLODE_FALLBACK = 3
    };

    enum class ImpMovementState : uint8
    {
        None,
        Following,
        Chasing
    };

    // ---- Dreadstalker (300152) tuning + local ids ----
    constexpr float DREADSTALKER_BITE_RANGE = 5.0f;
    constexpr uint32 DREADSTALKER_BITE_INTERVAL_MS = 2000;
    constexpr uint32 DREADSTALKER_BITE_RETRY_MS = 250;
    constexpr uint32 DREADSTALKER_DEPART_MS = 12000;
    constexpr uint32 DREADSTALKER_RETARGET_INTERVAL_MS = 500;
    // Below this the stalker is already on the target - just chase instead of charging.
    constexpr float DREADSTALKER_MIN_CHARGE_DIST = 8.0f;
    constexpr float DREADSTALKER_CHARGE_SPEED = 30.0f;

    enum DreadstalkerAIEvent : uint32
    {
        EVENT_DREADSTALKER_CHASE = 1,
        EVENT_DREADSTALKER_BITE = 2,
        EVENT_DREADSTALKER_DEPART = 3
    };

    // ---- Doomguard (300153) tuning + local ids ----
    constexpr float DOOMGUARD_CHASE_RANGE = 30.0f;
    constexpr float DOOMGUARD_CAST_RANGE = 40.0f;
    constexpr uint32 DOOMGUARD_CAST_INTERVAL_MS = 2500;
    constexpr uint32 DOOMGUARD_CAST_RETRY_MS = 250;
    constexpr uint32 DOOMGUARD_RETARGET_INTERVAL_MS = 500;

    enum DoomguardAIEvent : uint32
    {
        EVENT_DOOMGUARD_CHASE = 1,
        EVENT_DOOMGUARD_CAST = 2
    };

    // ---- Infernal (300154) tuning + local ids ----
    constexpr uint32 INFERNAL_PULSE_INTERVAL_MS = 1000;
    constexpr uint32 INFERNAL_RETARGET_INTERVAL_MS = 500;
    // Melee swing (2 s, creature_template BaseAttackTime) = two Immolation ticks at level 80
    // (DEMONOLOGY.md §4.0: 83 + 0.1114 x SP per tick), +/- 10%.
    constexpr float INFERNAL_MELEE_BASE_DAMAGE = 166.0f;
    constexpr float INFERNAL_MELEE_SP_COEFFICIENT = 0.2228f;
    constexpr float INFERNAL_MELEE_SPREAD = 0.1f;

    enum InfernalAIEvent : uint32
    {
        EVENT_INFERNAL_CHASE = 1,
        EVENT_INFERNAL_PULSE = 2
    };

    // Doomguard/Infernal have no pending-summon target of their own: they take the owner's
    // in-combat target (§11 Q10's no-pulling rule), falling back to whatever the owner had
    // selected when summoning, so a guardian called onto a not-yet-pulled enemy engages at once.
    ObjectGuid GetOwnerSelectedEnemy(Player const* owner)
    {
        Unit* selected = owner ? ObjectAccessor::GetUnit(*owner, owner->GetTarget()) : nullptr;
        return selected && owner->IsValidAttackTarget(selected) ? selected->GetGUID() : ObjectGuid::Empty;
    }

    Unit* SelectOwnerOrSummonTarget(Creature* guardian, Player* owner, ObjectGuid summonTarget)
    {
        if (Unit* target = Warlock::SelectGuardianTarget(guardian, owner, ObjectGuid::Empty))
            return target;
        return Warlock::SelectGuardianTarget(guardian, owner, summonTarget);
    }
}

/*
 * 300150/300151 - Wild Imp / Imp Gang Boss - DEMONOLOGY.md §7.2 (spawn/update/expire/energy),
 * §7.3 (Implosion), §7.10 (Demonic Empowerment sacrifice). One class for both entries (entry-keyed
 * for the Gang Boss's extra aura/energy) - matches the WP brief's "same class, entry-keyed".
 */
class npc_warl_wild_imp : public CreatureAI
{
public:
    explicit npc_warl_wild_imp(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* summonerUnit = summoner ? summoner->ToUnit() : nullptr;
        Player* owner = summonerUnit ? summonerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        bool const gangBoss = me->GetEntry() == Warlock::NPC_IMP_GANG_BOSS;
        _energy = gangBoss ? Warlock::IMP_GANG_BOSS_ENERGY : Warlock::WILD_IMP_ENERGY;
        _targetGUID = Warlock::GetPendingSummon(owner).target;

        // Priest tentacle GetFirstCollisionPosition precedent - only matters for the lone first
        // imp of a summon (Spell::SummonGuardian already spreads a multi-summon around dest).
        float const angle = frand(0.0f, float(2 * M_PI));
        Position const pos = me->GetFirstCollisionPosition(frand(0.0f, 3.0f), angle);
        me->NearTeleportTo(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ(), me->GetOrientation());

        me->SetReactState(REACT_PASSIVE);

        Warlock::RefreshDemonAuras(owner, me);
        if (gangBoss)
            DoCastSelf(Warlock::SPELL_IMP_GANG_BOSS_AURA, true);
        else
        {
            int32 const bp = owner->HasAura(SPELL_DESTRO_DEMONIC_POWER_R2) ? 14 :
                              owner->HasAura(SPELL_DESTRO_DEMONIC_POWER_R1) ? 5 : 0;
            if (bp)
                me->CastCustomSpell(me, Warlock::SPELL_DEMONIC_POWER_IMP_HASTE, &bp, nullptr, nullptr, true);
        }

        // No MoveFollow/MoveChase here - Spell::SummonGuardian issues MoveFollow(owner) right after
        // this hook returns (SpellEffects.cpp:6412-6417), so track that as the starting state: the
        // first update (next AI tick) then clears it when the target is in range, instead of the
        // imp running back to the warlock between bolts.
        _moveState = ImpMovementState::Following;
        _events.ScheduleEvent(EVENT_WILD_IMP_UPDATE, 0ms);
        _events.ScheduleEvent(EVENT_WILD_IMP_EXPIRE, Milliseconds(WILD_IMP_EXPIRE_MS));
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_WILD_IMP_UPDATE:
                    DoUpdate();
                    if (!_departing)
                        _events.ScheduleEvent(EVENT_WILD_IMP_UPDATE, Milliseconds(WILD_IMP_UPDATE_INTERVAL_MS));
                    break;
                case EVENT_WILD_IMP_EXPIRE:
                    // Timeout: always counting, no Molten Core roll (DEMONOLOGY.md §7.2).
                    if (!_departing)
                    {
                        _departing = true;
                        me->DespawnOrUnsummon();
                    }
                    break;
                case EVENT_WILD_IMP_IMPLODE_FALLBACK:
                    if (!_exploded)
                        Explode();
                    break;
                default:
                    break;
            }
        }
    }

    // Death Grip precedent (SHARED/DEMONOLOGY §7.2, §11 Q13): the jump generator reports landing
    // here with EFFECT_MOTION_TYPE (PointMovementGenerator.cpp:386), which is when the imp explodes.
    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == EFFECT_MOTION_TYPE && id == POINT_WILD_IMP_IMPLODE && !_exploded)
            Explode();
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case Warlock::ACTION_WILD_IMP_IMPLODE:
                StartImplode();
                break;
            case Warlock::ACTION_WILD_IMP_SACRIFICE:
                // Demonic Empowerment sacrifice - no roll, no explosion (DEMONOLOGY.md §7.10).
                if (!_departing)
                {
                    _departing = true;
                    me->DespawnOrUnsummon();
                }
                break;
            default:
                break;
        }
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case Warlock::DATA_WILD_IMP_ENERGY:
                return uint32(std::max(0, _energy));
            case Warlock::DATA_WILD_IMP_DEPARTING:
                return _departing ? 1 : 0;
            default:
                return 0;
        }
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == Warlock::GUID_SLOT_IMPLODE_TARGET)
            _implodeTargetGUID = guid;
    }

private:
    Player* GetOwnerPlayer() const
    {
        Unit* owner = me->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    void DoUpdate()
    {
        if (_departing || me->HasUnitState(UNIT_STATE_CASTING))
            return;

        Player* owner = GetOwnerPlayer();
        if (!owner)
            return;

        if (_energy < int32(Warlock::FEL_FIREBOLT_ENERGY_COST))
        {
            _departing = true;
            Warlock::OnWildImpDespawn(owner, Warlock::WildImpDespawnReason::Energy);
            // Keep the last bolt's missile alive (40 yd / Speed 20 = up to 2 s flight; the header's
            // own comment on OnWildImpDespawn/§7.2 calls out 1.5 s as too short).
            me->DespawnOrUnsummon(Milliseconds(WILD_IMP_ENERGY_DEATH_DESPAWN_MS));
            return;
        }

        Unit* target = Warlock::SelectGuardianTarget(me, owner, _targetGUID);
        if (!target)
        {
            _targetGUID.Clear();
            if (_moveState != ImpMovementState::Following)
            {
                me->GetMotionMaster()->MoveFollow(owner, PET_FOLLOW_DIST, me->GetFollowAngle());
                _moveState = ImpMovementState::Following;
            }
            return;
        }

        _targetGUID = target->GetGUID();

        bool const inRange = me->IsWithinDist(target, WILD_IMP_ATTACK_RANGE) && me->IsWithinLOSInMap(target);
        if (!inRange)
        {
            if (_moveState != ImpMovementState::Chasing)
            {
                me->GetMotionMaster()->MoveChase(target, WILD_IMP_CHASE_RANGE);
                _moveState = ImpMovementState::Chasing;
            }
            return;
        }

        if (_moveState != ImpMovementState::None)
        {
            me->GetMotionMaster()->Clear(false);
            me->StopMoving();
            _moveState = ImpMovementState::None;
        }

        // Demonic Power's +7/14% (§11 Q7 default) is applied to the hit in
        // spell_warl_guardian_hit_mods, never to bp0 here (§4.0 custom-BP rule). Real (non-
        // triggered) cast - Fel Firebolt has its own fixed 2000 ms cast time (§5.0) and
        // `triggered=true` would bypass it (TRIGGERED_CAST_DIRECTLY, part of TRIGGERED_FULL_MASK).
        int32 const bp0 = Warlock::ComputeGuardianBasePoints(me, Warlock::SPELL_FEL_FIREBOLT, 0.1028f);
        SpellCastResult const result =
            me->CastCustomSpell(target, Warlock::SPELL_FEL_FIREBOLT, &bp0, nullptr, nullptr, false);

        if (result == SPELL_CAST_OK)
        {
            int32 const freeChancePct = GetHighestRankAmount(owner, Warlock::RANKS_IMPROVED_IMP, EFFECT_2);
            bool const freeCast = freeChancePct > 0 &&
                roll_chance_f(float(freeChancePct) * Warlock::GetOwnerProcChanceMultiplier(me));
            if (!freeCast)
                _energy -= int32(Warlock::FEL_FIREBOLT_ENERGY_COST);
        }
        else
            LOG_DEBUG("scripts.ai", "npc_warl_wild_imp: {} Fel Firebolt on {} failed ({})",
                me->GetGUID().ToString(), target->GetGUID().ToString(), uint32(result));
    }

    void StartImplode()
    {
        if (_departing)
            return;

        _departing = true;
        me->InterruptNonMeleeSpells(false);

        if (Unit* target = ObjectAccessor::GetUnit(*me, _implodeTargetGUID))
            _implodeTargetPos.Relocate(*target);
        else
            _implodeTargetPos.Relocate(*me);

        me->GetMotionMaster()->MoveJump(_implodeTargetPos, WILD_IMP_IMPLODE_JUMP_SPEED_XY,
            WILD_IMP_IMPLODE_JUMP_SPEED_Z, POINT_WILD_IMP_IMPLODE);

        _events.CancelEvent(EVENT_WILD_IMP_UPDATE);
        _events.CancelEvent(EVENT_WILD_IMP_EXPIRE);
        _events.ScheduleEvent(EVENT_WILD_IMP_IMPLODE_FALLBACK, Milliseconds(WILD_IMP_IMPLODE_FALLBACK_MS));
    }

    void Explode()
    {
        if (_exploded)
            return;
        _exploded = true;

        if (SpellInfo const* explosionInfo = sSpellMgr->AssertSpellInfo(Warlock::SPELL_IMPLOSION_EXPLOSION))
        {
            int32 const bp0 = Warlock::ComputeGuardianBasePoints(me, Warlock::SPELL_IMPLOSION_EXPLOSION, 0.1543f);

            SpellCastTargets targets;
            targets.SetDst(_implodeTargetPos);

            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT0, bp0);

            me->CastSpell(targets, explosionInfo, &values, TRIGGERED_FULL_MASK);
        }

        Warlock::OnWildImpDespawn(GetOwnerPlayer(), Warlock::WildImpDespawnReason::Implosion);
        me->DespawnOrUnsummon();
    }

    ObjectGuid _targetGUID;
    ObjectGuid _implodeTargetGUID;
    Position _implodeTargetPos;
    int32 _energy = 0;
    bool _departing = false;
    bool _exploded = false;
    ImpMovementState _moveState = ImpMovementState::None;
    EventMap _events;
};

/*
 * 300152 - Dreadstalker - DEMONOLOGY.md §7.4. Guardian; no movement order in IsSummonedBy (same
 * Spell::SummonGuardian timing note as the Wild Imp above) - the first engage (charge + melee) is
 * issued from the first AI tick instead. Melees its target on top of the scripted Bite.
 */
class npc_warl_dreadstalker : public CreatureAI
{
public:
    explicit npc_warl_dreadstalker(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* summonerUnit = summoner ? summoner->ToUnit() : nullptr;
        Player* owner = summonerUnit ? summonerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        Warlock::PendingSummon const pending = Warlock::GetPendingSummon(owner);
        _targetGUID = pending.target;
        _pairToken = pending.pairToken;

        me->SetReactState(REACT_PASSIVE);
        Warlock::RefreshDemonAuras(owner, me);

        _events.ScheduleEvent(EVENT_DREADSTALKER_CHASE, 0ms);
        _events.ScheduleEvent(EVENT_DREADSTALKER_BITE, 0ms);
        _events.ScheduleEvent(EVENT_DREADSTALKER_DEPART, Milliseconds(DREADSTALKER_DEPART_MS));
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_DREADSTALKER_CHASE:
                    DoChase();
                    _events.ScheduleEvent(EVENT_DREADSTALKER_CHASE, Milliseconds(DREADSTALKER_RETARGET_INTERVAL_MS));
                    break;
                case EVENT_DREADSTALKER_BITE:
                    _events.ScheduleEvent(EVENT_DREADSTALKER_BITE, Milliseconds(DoBite() ?
                        DREADSTALKER_BITE_INTERVAL_MS : DREADSTALKER_BITE_RETRY_MS));
                    break;
                case EVENT_DREADSTALKER_DEPART:
                    if (Player* owner = GetOwnerPlayer())
                        Warlock::OnDreadstalkerDeparted(owner, _pairToken);
                    me->DespawnOrUnsummon();
                    break;
                default:
                    break;
            }
        }

        DoMeleeAttackIfReady();
    }

private:
    Player* GetOwnerPlayer() const
    {
        Unit* owner = me->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    void DoChase()
    {
        Player* owner = GetOwnerPlayer();
        if (!owner)
            return;

        Unit* target = Warlock::SelectGuardianTarget(me, owner, _targetGUID);
        if (target)
        {
            _targetGUID = target->GetGUID();
            if (target->GetGUID() != _chasingGUID)
            {
                me->Attack(target, true);
                // Chase sits in the active slot under the charge (controlled slot), so it takes
                // over the moment the charge lands - replacing SummonGuardian's MoveFollow(owner).
                me->GetMotionMaster()->MoveChase(target);
                if (!_charged)
                {
                    _charged = true;
                    if (!me->IsWithinDist(target, DREADSTALKER_MIN_CHARGE_DIST))
                    {
                        float x, y, z;
                        target->GetContactPoint(me, x, y, z);
                        me->GetMotionMaster()->MoveCharge(x, y, z, DREADSTALKER_CHARGE_SPEED, EVENT_CHARGE,
                            nullptr, true, 0.0f, target->GetGUID());
                    }
                }
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

    // Returns whether Bite went out, so a stalker still closing in retries shortly instead of
    // waiting a full bite interval after landing.
    bool DoBite()
    {
        Player* owner = GetOwnerPlayer();
        if (!owner)
            return false;

        Unit* target = Warlock::SelectGuardianTarget(me, owner, _targetGUID);
        if (!target || !me->IsWithinDist(target, DREADSTALKER_BITE_RANGE))
            return false;

        _targetGUID = target->GetGUID();
        int32 const bp0 = Warlock::ComputeGuardianBasePoints(me, Warlock::SPELL_DREADSTALKER_BITE, 0.1568f);
        me->CastCustomSpell(target, Warlock::SPELL_DREADSTALKER_BITE, &bp0, nullptr, nullptr, true);
        return true;
    }

    ObjectGuid _targetGUID;
    ObjectGuid _chasingGUID;
    uint32 _pairToken = 0;
    bool _charged = false;
    EventMap _events;
};

/*
 * 300153 - Doomguard - DEMONOLOGY.md §7.4. Ranged caster guardian; casts Doom Bolt at
 * Warlock::SelectGuardianTarget.
 */
class npc_warl_doomguard_guardian : public CreatureAI
{
public:
    explicit npc_warl_doomguard_guardian(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* summonerUnit = summoner ? summoner->ToUnit() : nullptr;
        Player* owner = summonerUnit ? summonerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        _summonTargetGUID = GetOwnerSelectedEnemy(owner);

        me->SetReactState(REACT_PASSIVE);
        Warlock::RefreshDemonAuras(owner, me);

        _events.ScheduleEvent(EVENT_DOOMGUARD_CHASE, 0ms);
        _events.ScheduleEvent(EVENT_DOOMGUARD_CAST, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_DOOMGUARD_CHASE:
                    DoChase();
                    _events.ScheduleEvent(EVENT_DOOMGUARD_CHASE, Milliseconds(DOOMGUARD_RETARGET_INTERVAL_MS));
                    break;
                case EVENT_DOOMGUARD_CAST:
                    _events.ScheduleEvent(EVENT_DOOMGUARD_CAST, Milliseconds(DoCastDoomBolt() ?
                        DOOMGUARD_CAST_INTERVAL_MS : DOOMGUARD_CAST_RETRY_MS));
                    break;
                default:
                    break;
            }
        }
    }

private:
    Player* GetOwnerPlayer() const
    {
        Unit* owner = me->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    void DoChase()
    {
        Player* owner = GetOwnerPlayer();
        if (!owner)
            return;

        Unit* target = SelectOwnerOrSummonTarget(me, owner, _summonTargetGUID);
        if (target)
        {
            if (target->GetGUID() != _chasingGUID)
            {
                me->GetMotionMaster()->MoveChase(target, DOOMGUARD_CHASE_RANGE);
                _chasingGUID = target->GetGUID();
            }
        }
        else if (!_chasingGUID.IsEmpty())
        {
            me->GetMotionMaster()->MoveFollow(owner, PET_FOLLOW_DIST, me->GetFollowAngle());
            _chasingGUID.Clear();
        }
    }

    // Returns whether the event should wait out a full cast (a bolt is in progress or just went
    // out) rather than retry shortly (no target in range yet).
    bool DoCastDoomBolt()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return true;

        Player* owner = GetOwnerPlayer();
        if (!owner)
            return false;

        Unit* target = SelectOwnerOrSummonTarget(me, owner, _summonTargetGUID);
        if (!target || !me->IsWithinDist(target, DOOMGUARD_CAST_RANGE) || !me->IsWithinLOSInMap(target))
            return false;

        int32 const bp0 = Warlock::ComputeGuardianBasePoints(me, Warlock::SPELL_DOOM_BOLT, 0.857f);
        return me->CastCustomSpell(target, Warlock::SPELL_DOOM_BOLT, &bp0, nullptr, nullptr, false) == SPELL_CAST_OK;
    }

    ObjectGuid _summonTargetGUID;
    ObjectGuid _chasingGUID;
    EventMap _events;
};

/*
 * 300154 - Infernal - DEMONOLOGY.md §7.4. Melees its target and pulses a self-centred Immolation
 * AoE every second, multiplied by the owner's Cataclysm rank in spell_warl_guardian_hit_mods
 * (spell_warlock_demonology.cpp), never here. Its weapon damage follows the owner's spell power,
 * refreshed with every pulse.
 */
class npc_warl_infernal_guardian : public CreatureAI
{
public:
    explicit npc_warl_infernal_guardian(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        Unit* summonerUnit = summoner ? summoner->ToUnit() : nullptr;
        Player* owner = summonerUnit ? summonerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        _summonTargetGUID = GetOwnerSelectedEnemy(owner);

        me->SetReactState(REACT_PASSIVE);
        Warlock::RefreshDemonAuras(owner, me);
        UpdateMeleeDamage();

        _events.ScheduleEvent(EVENT_INFERNAL_CHASE, 0ms);
        _events.ScheduleEvent(EVENT_INFERNAL_PULSE, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_INFERNAL_CHASE:
                    DoChase();
                    _events.ScheduleEvent(EVENT_INFERNAL_CHASE, Milliseconds(INFERNAL_RETARGET_INTERVAL_MS));
                    break;
                case EVENT_INFERNAL_PULSE:
                    DoPulse();
                    _events.ScheduleEvent(EVENT_INFERNAL_PULSE, Milliseconds(INFERNAL_PULSE_INTERVAL_MS));
                    break;
                default:
                    break;
            }
        }

        DoMeleeAttackIfReady();
    }

private:
    Player* GetOwnerPlayer() const
    {
        Unit* owner = me->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    void DoChase()
    {
        Player* owner = GetOwnerPlayer();
        if (!owner)
            return;

        Unit* target = SelectOwnerOrSummonTarget(me, owner, _summonTargetGUID);
        if (target)
        {
            // ChaseMovementGenerator pauses while GetVictim() != its target, so Attack() also has
            // to (re)set the victim whenever something cleared it.
            if (target->GetGUID() != _chasingGUID || me->GetVictim() != target)
            {
                me->Attack(target, true);
                // A chase that starts already in range sends no spline of its own, so the follow
                // spline still in flight would carry the Infernal back to the owner, and the chase
                // only re-paths once the target moves (never, for a training dummy).
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

    void DoPulse()
    {
        UpdateMeleeDamage();

        int32 const bp0 = Warlock::ComputeGuardianBasePoints(me, Warlock::SPELL_INFERNAL_IMMOLATION, 0.1114f);
        me->CastCustomSpell(me, Warlock::SPELL_INFERNAL_IMMOLATION, &bp0, nullptr, nullptr, true);
    }

    void UpdateMeleeDamage()
    {
        Player* owner = GetOwnerPlayer();
        if (!owner)
            return;

        int32 const sp = std::max(0, owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_FIRE));
        float const damage = INFERNAL_MELEE_BASE_DAMAGE + INFERNAL_MELEE_SP_COEFFICIENT * float(sp);
        me->SetBaseWeaponDamage(BASE_ATTACK, MINDAMAGE, damage * (1.0f - INFERNAL_MELEE_SPREAD));
        me->SetBaseWeaponDamage(BASE_ATTACK, MAXDAMAGE, damage * (1.0f + INFERNAL_MELEE_SPREAD));
        me->UpdateDamagePhysical(BASE_ATTACK);
    }

    ObjectGuid _summonTargetGUID;
    ObjectGuid _chasingGUID;
    EventMap _events;
};

/*
 * PetScript::OnPetAddToWorld - DEMONOLOGY.md §7.1: a freshly summoned/resummoned main pet (Imp,
 * Voidwalker, Succubus, Felhunter, Felguard) needs its Demonic Potency (and the other conditional
 * hidden auras) applied the moment it enters the world, same as every guardian's own
 * Warlock::RefreshDemonAuras call in IsSummonedBy above.
 */
class warlock_demonology_pet_script : public PetScript
{
public:
    warlock_demonology_pet_script() : PetScript("warlock_demonology_pet_script", { PETHOOK_ON_PET_ADD_TO_WORLD }) { }

    void OnPetAddToWorld(Pet* pet) override
    {
        if (!pet)
            return;

        Unit* ownerUnit = pet->GetOwner();
        Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr;
        if (owner && owner->getClass() == CLASS_WARLOCK)
            Warlock::RefreshDemonAuras(owner, pet);
    }
};

void AddSC_warlock_rework_pet_scripts()
{
    RegisterCreatureAI(npc_warl_wild_imp);
    RegisterCreatureAI(npc_warl_dreadstalker);
    RegisterCreatureAI(npc_warl_doomguard_guardian);
    RegisterCreatureAI(npc_warl_infernal_guardian);
    new warlock_demonology_pet_script();
}
