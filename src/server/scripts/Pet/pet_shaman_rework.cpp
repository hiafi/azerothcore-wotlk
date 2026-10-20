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
 * Shaman rework - totem and guardian AIs (shaman-rework SH0b; docs/reworks/shaman-shared-rework.md).
 *
 * Totems (TotemAI subclasses; every entry is summoned with SummonProperties 63/81/82/83, so it is a real Totem and
 * TotemAI's IsTotem() assert holds):
 *  - npc_sha_elemental_totem (300270-300273): hides the totem model; its index-0 passive summons the guardian
 *    (CORE-AUDIT-A A5), so the totem leaving the world takes the elemental with it.
 *  - npc_sha_searing_totem (300278): empty m_spells[0] (TOTEM_PASSIVE, stock TotemAI does nothing); fires the
 *    instant Searing bolt every SEARING_BOLT_PERIOD_MS from placement, SEARING_BOLT_COUNT bolts, only at enemies
 *    engaged with the shaman or the group (A35, T0b section 5).
 *  - npc_sha_earthen_wall_totem (300274): empty m_spells[0]; EARTHEN_WALL_PULSES pulses from placement, every
 *    EARTHEN_WALL_PERIOD_MS (A32).
 *
 * Guardians (owner = the shaman: Spell::SummonGuardian remaps the totem caster to its owner):
 *  - npc_sha_fire_elemental_rework (15438), npc_sha_earth_elemental_rework (15352): the stock pet_shaman.cpp AIs,
 *    except that targets come from Engagement::SelectEngagedTarget (no _initAttack pull of an idle unit, no
 *    proximity aggro) and death empties the totem slot.
 *  - npc_sha_water_elemental (300260), npc_sha_storm_elemental (300261): ranged casters, Doomguard shape
 *    (pet_warlock_rework.cpp): back-to-back 2 sec bolts, chase to ELEMENTAL_CHASE_RANGE_YD.
 *
 * Every damage/heal here is cast by the totem or guardian itself with no original-caster GUID, so none of the
 * shaman's procs roll (A11). A missing or non-player owner never crashes: the AI just stays idle.
 */

#include "CreatureAI.h"
#include "CreatureScript.h"
#include "EngagementMechanics.h"
#include "EventMap.h"
#include "HealMechanics.h"
#include "Log.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PetDefines.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "ShamanMechanics.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "TaskScheduler.h"
#include "Totem.h"
#include "TotemAI.h"
#include "Unit.h"
#include <algorithm>
#include <vector>

namespace
{
    // How often an idle guardian looks for an engaged target, and how soon a totem/caster retries when it found
    // none (or is mid-cast). Internal polling only; every design number is a ShamanData:: const.
    constexpr uint32 ELEMENTAL_ACQUIRE_INTERVAL_MS = 500;
    constexpr uint32 SEARING_BOLT_RETRY_MS = 250;
    constexpr uint32 CASTER_ELEMENTAL_POLL_MS = 250;

    // Earthen Wall spill: SelectMostInjured returns at most this many candidates (a full raid) before the
    // "no shield from this shaman" filter runs, so the filter never starves on a capped list.
    constexpr uint8 EARTHEN_WALL_SPILL_CANDIDATES = 40;

    // Fire/Earth elemental timers: the stock npc_pet_shaman_* values (pet_shaman.cpp).
    constexpr Milliseconds FIRE_NOVA_FIRST_MIN = 5s;
    constexpr Milliseconds FIRE_NOVA_FIRST_MAX = 20s;
    constexpr Milliseconds FIRE_NOVA_REPEAT_MIN = 8s;
    constexpr Milliseconds FIRE_NOVA_REPEAT_MAX = 15s;
    constexpr Milliseconds FIRE_BLAST_FIRST_MIN = 5s;
    constexpr Milliseconds FIRE_BLAST_FIRST_MAX = 20s;
    constexpr Milliseconds FIRE_BLAST_REPEAT_MIN = 4s;
    constexpr Milliseconds FIRE_BLAST_REPEAT_MAX = 8s;
    constexpr Milliseconds ANGERED_EARTH_REPEAT_MIN = 5s;
    constexpr Milliseconds ANGERED_EARTH_REPEAT_MAX = 20s;

    enum SearingTotemEvents : uint32
    {
        EVENT_SEARING_BOLT = 1
    };

    enum EarthenWallTotemEvents : uint32
    {
        EVENT_EARTHEN_WALL_PULSE = 1
    };

    // SetGUID id for the Earthen Wall cast target (sent by spell_sha_earthen_wall, spell_shaman_totems.cpp).
    enum EarthenWallTotemData : int32
    {
        DATA_EARTHEN_WALL_TARGET = 0
    };

    enum FireElementalEvents : uint32
    {
        EVENT_FIRE_ELEMENTAL_FIRE_NOVA = 1,
        EVENT_FIRE_ELEMENTAL_FIRE_BLAST = 2
    };

    enum EarthElementalEvents : uint32
    {
        EVENT_EARTH_ELEMENTAL_ANGERED_EARTH = 1
    };

    enum CasterElementalEvents : uint32
    {
        EVENT_CASTER_ELEMENTAL_CHASE = 1,
        EVENT_CASTER_ELEMENTAL_CAST = 2
    };

    Player* GetOwnerPlayer(Creature const* creature)
    {
        Unit* owner = creature->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    // The amount left on the aura's absorb effect(s); -1 when the aura has none.
    int32 GetRemainingAbsorb(Aura const* aura)
    {
        int32 amount = -1;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i))
                if (effect->GetAuraType() == SPELL_AURA_SCHOOL_ABSORB)
                    amount = std::max(amount, 0) + effect->GetAmount();
        return amount;
    }
}

/*
 * 300270-300273 - Earth/Fire/Water/Storm Elemental Totem. The guardian is the visible unit; the totem only holds
 * the slot (totem bar, Recall, right-click, replacement). Totem::InitStats set the race totem model before
 * IsSummonedBy runs, so this overrides it.
 */
struct npc_sha_elemental_totem : public TotemAI
{
    explicit npc_sha_elemental_totem(Creature* creature) : TotemAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->SetDisplayId(uint32(ShamanData::ELEMENTAL_TOTEM_DISPLAY_INVISIBLE));
    }
};

/*
 * 300278 - Searing Totem. TotemAI's own UpdateAI returns at once for a TOTEM_PASSIVE totem, so this drives the
 * bolt itself: first bolt on placement, then one per SEARING_BOLT_PERIOD_MS, retrying sooner while no engaged
 * enemy is in range. Never picks an idle unit (stock TotemAI's nearest-attackable search pulled packs).
 */
struct npc_sha_searing_totem : public TotemAI
{
    explicit npc_sha_searing_totem(Creature* creature) : TotemAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _boltsFired = 0;
        _targetGUID.Clear();
        events.Reset();
        events.ScheduleEvent(EVENT_SEARING_BOLT, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;

        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            if (eventId != EVENT_SEARING_BOLT)
                continue;

            if (!TryFireBolt())
                events.ScheduleEvent(EVENT_SEARING_BOLT, Milliseconds(SEARING_BOLT_RETRY_MS));
            else if (++_boltsFired < uint32(ShamanData::SEARING_BOLT_COUNT))
                events.ScheduleEvent(EVENT_SEARING_BOLT, Milliseconds(ShamanData::SEARING_BOLT_PERIOD_MS));
        }
    }

private:
    bool TryFireBolt()
    {
        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return false;

        Unit* target = Engagement::SelectEngagedTarget(me, owner, _targetGUID, ShamanData::SEARING_RANGE_YD);
        if (!target || !me->IsWithinLOSInMap(target))
        {
            _targetGUID.Clear();
            return false;
        }

        _targetGUID = target->GetGUID();
        me->SetInFront(target);
        return me->CastSpell(target, ShamanData::SPELL_SEARING_BOLT, true) == SPELL_CAST_OK;
    }

    uint32 _boltsFired = 0;
    ObjectGuid _targetGUID;
};

/*
 * 300274 - Earthen Wall Totem. spell_sha_earthen_wall hands the cast target over with
 * SetGUID(target, DATA_EARTHEN_WALL_TARGET) in the same cast, before the totem's first update. Each pulse:
 *  - target has no shield from this totem (first pulse, popped, expired): shield it;
 *  - target's shield has absorbed anything: recast, which refreshes duration and amount (SetStackAmount
 *    recalculates the amounts; shields never stack);
 *  - target's shield is still full, or the target is gone/dead/out of range: shield the lowest-health player
 *    (by percent) within EARTHEN_WALL_RANGE_YD of the totem who has no Earthen Wall shield from this shaman.
 *    Heal::SelectMostInjured returns players only (plus the shaman), so pets are never chosen.
 * The shield is cast by the totem (caster = totem; "this shaman's shield" = the aura caster is this totem or a
 * unit owned by the same shaman). Its absorb amount (owner SP x BonusMultiplier) is spell_sha_earthen_wall_shield's.
 */
struct npc_sha_earthen_wall_totem : public TotemAI
{
    explicit npc_sha_earthen_wall_totem(Creature* creature) : TotemAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _pulses = 0;
        _primaryFullAmount = 0;
        events.Reset();
        events.ScheduleEvent(EVENT_EARTHEN_WALL_PULSE, 0ms);
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == DATA_EARTHEN_WALL_TARGET)
            _primaryGUID = guid;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;

        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            if (eventId != EVENT_EARTHEN_WALL_PULSE)
                continue;

            DoPulse();
            if (++_pulses < uint32(ShamanData::EARTHEN_WALL_PULSES))
                events.ScheduleEvent(EVENT_EARTHEN_WALL_PULSE, Milliseconds(ShamanData::EARTHEN_WALL_PERIOD_MS));
        }
    }

private:
    void DoPulse()
    {
        Unit* owner = me->GetOwner();
        if (!owner)
            return;

        Unit* primary = _primaryGUID ? ObjectAccessor::GetUnit(*me, _primaryGUID) : nullptr;
        if (primary && IsValidPrimary(primary))
        {
            Aura const* shield = primary->GetAura(ShamanData::SPELL_EARTHEN_WALL_SHIELD, me->GetGUID());
            if (!shield || GetRemainingAbsorb(shield) < _primaryFullAmount)
            {
                ShieldPrimary(primary);
                return;
            }
        }

        std::vector<Unit*> candidates;
        Heal::SelectMostInjured(owner, me, ShamanData::EARTHEN_WALL_RANGE_YD, EARTHEN_WALL_SPILL_CANDIDATES,
            candidates);

        for (Unit* candidate : candidates)
        {
            if (candidate == primary || !candidate->IsAlive() || HasShieldFromOwner(candidate, owner->GetGUID()))
                continue;

            me->CastSpell(candidate, ShamanData::SPELL_EARTHEN_WALL_SHIELD, true);
            return;
        }
    }

    bool IsValidPrimary(Unit const* primary) const
    {
        return primary->IsAlive() && primary->IsInMap(me) && !me->IsHostileTo(primary) &&
            me->IsWithinDistInMap(primary, ShamanData::EARTHEN_WALL_RANGE_YD);
    }

    void ShieldPrimary(Unit* primary)
    {
        if (me->CastSpell(primary, ShamanData::SPELL_EARTHEN_WALL_SHIELD, true) != SPELL_CAST_OK)
            return;

        // The full amount this cast gave, so later pulses can tell whether the shield has absorbed anything.
        if (Aura const* shield = primary->GetAura(ShamanData::SPELL_EARTHEN_WALL_SHIELD, me->GetGUID()))
        {
            _primaryFullAmount = GetRemainingAbsorb(shield);
            if (_primaryFullAmount < 0)
                LOG_ERROR("scripts.ai", "npc_sha_earthen_wall_totem: spell {} has no SCHOOL_ABSORB effect; "
                    "refresh-if-damaged cannot work", ShamanData::SPELL_EARTHEN_WALL_SHIELD);
        }
    }

    bool HasShieldFromOwner(Unit* unit, ObjectGuid ownerGUID) const
    {
        auto const range = unit->GetAppliedAuras().equal_range(ShamanData::SPELL_EARTHEN_WALL_SHIELD);
        for (auto itr = range.first; itr != range.second; ++itr)
        {
            Aura const* aura = itr->second->GetBase();
            if (aura->GetCasterGUID() == me->GetGUID())
                return true;

            if (Unit const* caster = aura->GetCaster())
                if (caster->GetOwnerGUID() == ownerGUID)
                    return true;
        }
        return false;
    }

    uint32 _pulses = 0;
    int32 _primaryFullAmount = 0;
    ObjectGuid _primaryGUID;
};

/*
 * Shared part of the Fire/Earth guardians: the stock AIs attacked the owner's selected unit at spawn even when it
 * was idle (_initAttack) and, as REACT_AGGRESSIVE guardians, aggroed anything walking into sight. Here an idle
 * guardian polls Engagement::SelectEngagedTarget instead and proximity aggro is off. Once fighting, the stock
 * UpdateVictim/SelectVictim path (attackers of the guardian or its owner) runs unchanged.
 */
struct ShamanMeleeElementalAI : public ScriptedAI
{
    explicit ShamanMeleeElementalAI(Creature* creature) : ScriptedAI(creature) { }

    // Stock: no Reset() on AI creation.
    void InitializeAI() override { }

    // No proximity aggro: engaged-only targets.
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        scheduler.CancelAll();
        scheduler.Schedule(0ms, [this](TaskContext context)
        {
            AcquireEngagedTarget();
            context.Repeat(Milliseconds(ELEMENTAL_ACQUIRE_INTERVAL_MS));
        });
    }

    void JustDied(Unit* /*killer*/) override
    {
        Shaman::OnElementalDied(me);
    }

protected:
    void AcquireEngagedTarget()
    {
        if (!me->IsAlive() || me->GetVictim())
            return;

        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return;

        if (Unit* target = Engagement::SelectEngagedTarget(me, owner, ObjectGuid::Empty,
            ShamanData::ELEMENTAL_TARGET_RANGE_YD))
            if (me->CanCreatureAttack(target))
                AttackStart(target);
    }
};

/*
 * 15438 - Greater Fire Elemental (ScriptName override; the entry stays because Pet.cpp and spell_shaman.cpp key
 * its stats on it). Stock npc_pet_shaman_fire_elemental abilities and timers.
 */
struct npc_sha_fire_elemental_rework : public ShamanMeleeElementalAI
{
    explicit npc_sha_fire_elemental_rework(Creature* creature) : ShamanMeleeElementalAI(creature) { }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _events.Reset();
        _events.ScheduleEvent(EVENT_FIRE_ELEMENTAL_FIRE_NOVA, FIRE_NOVA_FIRST_MIN, FIRE_NOVA_FIRST_MAX);
        _events.ScheduleEvent(EVENT_FIRE_ELEMENTAL_FIRE_BLAST, FIRE_BLAST_FIRST_MIN, FIRE_BLAST_FIRST_MAX);

        me->RemoveAurasDueToSpell(ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_SHIELD);
        DoCastSelf(ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_SHIELD, true);
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);

        if (!UpdateVictim())
            return;

        _events.Update(diff);

        while (uint32 eventId = _events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_FIRE_ELEMENTAL_FIRE_NOVA:
                    DoCastSelf(ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_NOVA);
                    _events.ScheduleEvent(EVENT_FIRE_ELEMENTAL_FIRE_NOVA, FIRE_NOVA_REPEAT_MIN, FIRE_NOVA_REPEAT_MAX);
                    break;
                case EVENT_FIRE_ELEMENTAL_FIRE_BLAST:
                    DoCastVictim(ShamanData::SPELL_FIRE_ELEMENTAL_FIRE_BLAST);
                    _events.ScheduleEvent(EVENT_FIRE_ELEMENTAL_FIRE_BLAST, FIRE_BLAST_REPEAT_MIN,
                        FIRE_BLAST_REPEAT_MAX);
                    break;
                default:
                    break;
            }
        }

        DoMeleeAttackIfReady();
    }

private:
    EventMap _events;
};

/*
 * 15352 - Greater Earth Elemental (ScriptName override, entry kept for Pet.cpp's stats). Stock
 * npc_pet_shaman_earth_elemental: Angered Earth (AoE taunt) on engage, then every 5-20 sec.
 */
struct npc_sha_earth_elemental_rework : public ShamanMeleeElementalAI
{
    explicit npc_sha_earth_elemental_rework(Creature* creature) : ShamanMeleeElementalAI(creature) { }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _events.Reset();
        _events.ScheduleEvent(EVENT_EARTH_ELEMENTAL_ANGERED_EARTH, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);

        if (!UpdateVictim())
            return;

        _events.Update(diff);

        if (_events.ExecuteEvent() == EVENT_EARTH_ELEMENTAL_ANGERED_EARTH)
        {
            DoCastVictim(ShamanData::SPELL_ANGERED_EARTH);
            _events.ScheduleEvent(EVENT_EARTH_ELEMENTAL_ANGERED_EARTH, ANGERED_EARTH_REPEAT_MIN,
                ANGERED_EARTH_REPEAT_MAX);
        }

        DoMeleeAttackIfReady();
    }

private:
    EventMap _events;
};

/*
 * Shared part of the Water/Storm guardians (npc_warl_doomguard_guardian shape): REACT_PASSIVE, a target from
 * Engagement::SelectEngagedTarget (the owner's selection at summon is only a preference), chase to
 * ELEMENTAL_CHASE_RANGE_YD, a bolt whenever not casting and the target is within ELEMENTAL_TARGET_RANGE_YD and in
 * line of sight. The chase sets the victim first (Attack(target, false): no melee) and stops the follow spline
 * (bugs-and-fixes: "A guardian given MoveChase never leaves its owner"). The bolt is a plain cast (warlock P8:
 * potency runs with the guardian as caster; the owner-stat aura 202279 supplies the shaman's spell power).
 */
class ShamanCasterElementalAI : public CreatureAI
{
public:
    ShamanCasterElementalAI(Creature* creature, uint32 boltSpellId)
        : CreatureAI(creature), _boltSpellId(boltSpellId) { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        me->SetReactState(REACT_PASSIVE);

        Unit* summonerUnit = summoner ? summoner->ToUnit() : nullptr;
        Player* owner = summonerUnit ? summonerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        _targetGUID = owner->GetTarget();
        Shaman::RefreshElementalAuras(owner, me);

        events.Reset();
        events.ScheduleEvent(EVENT_CASTER_ELEMENTAL_CHASE, 0ms);
        events.ScheduleEvent(EVENT_CASTER_ELEMENTAL_CAST, 0ms);
    }

    void MoveInLineOfSight(Unit* /*who*/) override { }

    void JustDied(Unit* /*killer*/) override
    {
        Shaman::OnElementalDied(me);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;

        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_CASTER_ELEMENTAL_CHASE:
                    DoChase();
                    events.ScheduleEvent(EVENT_CASTER_ELEMENTAL_CHASE, Milliseconds(ELEMENTAL_ACQUIRE_INTERVAL_MS));
                    break;
                case EVENT_CASTER_ELEMENTAL_CAST:
                    DoCastBolt();
                    events.ScheduleEvent(EVENT_CASTER_ELEMENTAL_CAST, Milliseconds(CASTER_ELEMENTAL_POLL_MS));
                    break;
                default:
                    break;
            }
        }
    }

private:
    Unit* SelectBoltTarget(Player* owner)
    {
        Unit* target = Engagement::SelectEngagedTarget(me, owner, _targetGUID, ShamanData::ELEMENTAL_TARGET_RANGE_YD);
        _targetGUID = target ? target->GetGUID() : ObjectGuid::Empty;
        return target;
    }

    void DoChase()
    {
        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return;

        if (Unit* target = SelectBoltTarget(owner))
        {
            if (target->GetGUID() != _chasingGUID || me->GetVictim() != target)
            {
                me->Attack(target, false);
                me->StopMoving();
                me->GetMotionMaster()->MoveChase(target, ShamanData::ELEMENTAL_CHASE_RANGE_YD);
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

    void DoCastBolt()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return;

        Unit* target = SelectBoltTarget(owner);
        if (!target || !me->IsWithinLOSInMap(target))
            return;

        me->CastSpell(target, _boltSpellId, false);
    }

    uint32 _boltSpellId;
    ObjectGuid _targetGUID;
    ObjectGuid _chasingGUID;
};

/*
 * 300260 - Greater Water Elemental. Water Bolt (Frost); its heal on the 3 most injured players is
 * spell_sha_water_bolt's (spell_shaman_totems.cpp).
 */
struct npc_sha_water_elemental : public ShamanCasterElementalAI
{
    explicit npc_sha_water_elemental(Creature* creature)
        : ShamanCasterElementalAI(creature, ShamanData::SPELL_WATER_BOLT) { }
};

/*
 * 300261 - Greater Storm Elemental. Storm Bolt (Nature) is its only ability.
 */
struct npc_sha_storm_elemental : public ShamanCasterElementalAI
{
    explicit npc_sha_storm_elemental(Creature* creature)
        : ShamanCasterElementalAI(creature, ShamanData::SPELL_STORM_BOLT) { }
};

void AddSC_shaman_rework_pet_scripts()
{
    RegisterCreatureAI(npc_sha_elemental_totem);
    RegisterCreatureAI(npc_sha_searing_totem);
    RegisterCreatureAI(npc_sha_earthen_wall_totem);
    RegisterCreatureAI(npc_sha_fire_elemental_rework);
    RegisterCreatureAI(npc_sha_earth_elemental_rework);
    RegisterCreatureAI(npc_sha_water_elemental);
    RegisterCreatureAI(npc_sha_storm_elemental);
}
