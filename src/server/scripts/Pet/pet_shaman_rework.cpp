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
 *    EARTHEN_WALL_PERIOD_MS (A32). With Earthen Bulwark (S2a) each pulse also shields the other players nearby.
 *  - npc_sha_undulating_currents_totem (Restoration, S2a): empty m_spells[0]; casts the Chain Heal of the totem on the
 *    most injured player in range from placement, UCT_CASTS casts, every UCT_INTERVAL_MS.
 *  - npc_sha_spirit_link_totem (Restoration, S2a): empty m_spells[0]; from placement, every SPIRIT_LINK_INTERVAL_MS,
 *    refreshes the Spirit Link aura on the players around it and sets them all to the average health percent.
 *
 * Guardians (owner = the shaman: Spell::SummonGuardian remaps the totem caster to its owner):
 *  - npc_sha_fire_elemental_rework (15438), npc_sha_earth_elemental_rework (15352): the stock pet_shaman.cpp AIs,
 *    except that targets come from Engagement::SelectEngagedTarget (no _initAttack pull of an idle unit, no
 *    proximity aggro) and death empties the totem slot.
 *  - npc_sha_water_elemental (300260), npc_sha_storm_elemental (300261): ranged casters, Doomguard shape
 *    (pet_warlock_rework.cpp): back-to-back 2 sec bolts, chase to ELEMENTAL_CHASE_RANGE_YD.
 *
 * Elemental Spirit wolves (Enhancement, S3a; docs/reworks/shaman-enhancement-rework.md "Elemental Spirit wolves"):
 *  - ShamanSpiritWolfPetScript: the stock Feral Spirit wolf setup (Pet.cpp:1310-1328) for entries 300262-300265 under
 *    a player owner of any class (Classless), through PetScript::OnInitStatsForLevel (no core edit).
 *  - npc_sha_fire_spirit (300262), npc_sha_frost_spirit (300263), npc_sha_wind_spirit (300264),
 *    npc_sha_rock_spirit (300265): one melee base (targets from Engagement::SelectEngagedTarget, never an idle pull);
 *    melee hits are queued from DamageDealt and acted on from UpdateAI (never a cast inside DealDamage). Fire casts
 *    Spirit Flame Shock on every bite; Frost has no AI of its own (Shaman::OnStormstrikeLanded makes it cast the
 *    Stormstrike copy); Wind rolls a Gust cast by the shaman; Rock taunts on summon and grants the shaman 1
 *    Stoneskin per bite. Wolves build no Elemental Charge and roll none of the shaman's procs: every wolf spell is a
 *    plain triggered cast by the wolf, and the Gust is a triggered cast by the shaman.
 *
 * Every damage/heal here is cast by the totem or guardian itself with no original-caster GUID, so none of the
 * shaman's procs roll (A11). A missing or non-player owner never crashes: the AI just stays idle.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "EngagementMechanics.h"
#include "EventMap.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "HealMechanics.h"
#include "Log.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PetDefines.h"
#include "PetScript.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "ShamanMechanics.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TaskScheduler.h"
#include "TemporarySummon.h"
#include "Totem.h"
#include "TotemAI.h"
#include "Unit.h"
#include <algorithm>
#include <list>
#include <vector>

namespace
{
    // How often an idle guardian looks for an engaged target, and how soon a totem/caster retries when it found
    // none (or is mid-cast). Internal polling only; every design number is a ShamanData:: const.
    constexpr uint32 ELEMENTAL_ACQUIRE_INTERVAL_MS = 500;
    constexpr uint32 SEARING_BOLT_RETRY_MS = 250;
    constexpr uint32 CASTER_ELEMENTAL_POLL_MS = 250;

    // Earthen Wall spill: SelectMostInjured returns at most this many candidates (a full raid) before the
    // "no shield from this shaman" filter runs, so the filter never starves on a capped list. The Bulwark and Spirit
    // Link area picks use the same cap (a full raid).
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

    enum UndulatingCurrentsTotemEvents : uint32
    {
        EVENT_UNDULATING_CURRENTS_CAST = 1
    };

    enum SpiritLinkTotemEvents : uint32
    {
        EVENT_SPIRIT_LINK_PULSE = 1
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

    // Elemental Spirit wolves. Stock Feral Spirit weapon damage is (4L - L)..(4L + L) at attack time 1500
    // (Pet.cpp:1310-1328, template BaseAttackTime); the wolf hook uses half of it (1.5L..2.5L, S3 trim 2026-10-22).
    constexpr float WOLF_DAMAGE_MIN_PER_LEVEL = 1.5f;
    constexpr float WOLF_DAMAGE_MAX_PER_LEVEL = 2.5f;
    constexpr uint32 WOLF_ATTACK_TIME_MS = 1500;

    // Queue cap (a wolf bites once per 1.5 s and the queue drains every update; the cap only bounds a stalled AI).
    constexpr size_t WOLF_HIT_QUEUE_CAP = 8;

    Player* GetOwnerPlayer(Creature const* creature)
    {
        Unit* owner = creature->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    bool IsSpiritWolfEntry(uint32 entry)
    {
        return entry == uint32(ShamanData::NPC_FIRE_SPIRIT) || entry == uint32(ShamanData::NPC_FROST_SPIRIT) ||
            entry == uint32(ShamanData::NPC_WIND_SPIRIT) || entry == uint32(ShamanData::NPC_ROCK_SPIRIT);
    }

    // True when any effect of `spellInfo` is immune on `target` (taunt: IMMUNITY_EFFECT ATTACK_ME or IMMUNITY_STATE
    // MOD_TAUNT, set by flags_extra or creature_immunities rows; S3a-0VERIFY C10). Never a flags_extra test.
    bool IsImmuneToAnyEffect(Unit const* target, SpellInfo const* spellInfo, WorldObject const* caster)
    {
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (spellInfo->Effects[i].Effect && target->IsImmunedToSpellEffect(spellInfo, i, caster))
                return true;

        return false;
    }

    bool HasPowerOfTheElements(Player const* owner)
    {
        return Shaman::GetTalentRank(owner, { ShamanData::SPELL_POWER_OF_THE_ELEMENTS }) != 0;
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

        PulseMainShield(owner);
        PulseBulwark(owner);
    }

    void PulseMainShield(Unit* owner)
    {
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

    // Earthen Bulwark: every pulse also shields each other player within BULWARK_RADIUS_YD of the totem (never one
    // holding a shield of this shaman's wall, so the main shield's holder is skipped, and never a pet) for BULWARK_PCT
    // of the main shield. The main amount is the shared helper's (Totemic Resonance included), so the Bulwark
    // shield, which carries no engine healing bonus, is not multiplied a second time.
    void PulseBulwark(Unit* owner)
    {
        Player* player = owner->ToPlayer();
        if (!player || !Shaman::GetTalentRank(player, { ShamanData::SPELL_EARTHEN_BULWARK }))
            return;

        SpellInfo const* mainShield = sSpellMgr->GetSpellInfo(ShamanData::SPELL_EARTHEN_WALL_SHIELD);
        if (!mainShield)
            return;

        int32 const amount = int32(CalculatePct(Shaman::GetEarthenWallAbsorb(player, mainShield, EFFECT_0),
            ShamanData::BULWARK_PCT));
        if (amount <= 0)
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(owner, me, ShamanData::BULWARK_RADIUS_YD, EARTHEN_WALL_SPILL_CANDIDATES, allies);
        for (Unit* ally : allies)
        {
            if (!ally->IsAlive() || HasShieldFromOwner(ally, owner->GetGUID()))
                continue;

            me->CastCustomSpell(ShamanData::SPELL_EARTHEN_BULWARK_SHIELD, SPELLVALUE_BASE_POINT0, amount, ally, true);
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
 * Undulating Currents Totem (Restoration, Fire slot). TotemAI's UpdateAI does nothing for a totem with no spell, so
 * this drives itself like the Earthen Wall: the first cast on placement, then one per UCT_INTERVAL_MS, UCT_CASTS casts
 * in all. Each cast is the totem's own Chain Heal (the UCT heal, which has no Chain Heal talents and rolls none of the
 * shaman's procs: cast by the totem with no owner GUID, A11) at the lowest-health-percent player within UCT_RANGE_YD
 * of the totem. Heal::SelectMostInjured returns players only, so pets are never picked; the jumps are filtered by the
 * heal's own script. The Lightwell shape (pet_priest.cpp), a counted cast loop.
 */
struct npc_sha_undulating_currents_totem : public TotemAI
{
    explicit npc_sha_undulating_currents_totem(Creature* creature) : TotemAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _casts = 0;
        events.Reset();
        events.ScheduleEvent(EVENT_UNDULATING_CURRENTS_CAST, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;

        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            if (eventId != EVENT_UNDULATING_CURRENTS_CAST)
                continue;

            DoCast();
            if (++_casts < uint32(ShamanData::UCT_CASTS))
                events.ScheduleEvent(EVENT_UNDULATING_CURRENTS_CAST, Milliseconds(ShamanData::UCT_INTERVAL_MS));
        }
    }

private:
    void DoCast()
    {
        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return;

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(owner, me, ShamanData::UCT_RANGE_YD, 1, allies);
        if (allies.empty())
            return;

        if (me->CastSpell(allies.front(), ShamanData::SPELL_UNDULATING_CURRENTS_HEAL, TRIGGERED_FULL_MASK) !=
            SPELL_CAST_OK)
            LOG_ERROR("scripts.ai", "npc_sha_undulating_currents_totem: cast of {} at {} failed",
                uint32(ShamanData::SPELL_UNDULATING_CURRENTS_HEAL), allies.front()->GetGUID().ToString());
    }

    uint32 _casts = 0;
};

/*
 * Spirit Link Totem (Restoration, Air slot). From placement and then every SPIRIT_LINK_INTERVAL_MS until the totem
 * expires: every player (party and raid members, the shaman included; never a pet) within SPIRIT_LINK_RADIUS_YD of the
 * totem gets the Spirit Link aura refreshed (damage taken reduced, short duration so it ends soon after the totem or a
 * step out of range) and all of them are set to the same health percent, the average of their current percents. This
 * is a plain SetHealth, not a heal: no heal event, so no healing bonus, no Cloudburst store and no procs.
 */
struct npc_sha_spirit_link_totem : public TotemAI
{
    explicit npc_sha_spirit_link_totem(Creature* creature) : TotemAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        events.Reset();
        events.ScheduleEvent(EVENT_SPIRIT_LINK_PULSE, 0ms);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsAlive())
            return;

        events.Update(diff);

        while (uint32 eventId = events.ExecuteEvent())
        {
            if (eventId != EVENT_SPIRIT_LINK_PULSE)
                continue;

            DoLink();
            events.ScheduleEvent(EVENT_SPIRIT_LINK_PULSE, Milliseconds(ShamanData::SPIRIT_LINK_INTERVAL_MS));
        }
    }

private:
    void DoLink()
    {
        Player* owner = GetOwnerPlayer(me);
        if (!owner)
            return;

        std::vector<Unit*> linked;
        Heal::SelectMostInjured(owner, me, ShamanData::SPIRIT_LINK_RADIUS_YD, EARTHEN_WALL_SPILL_CANDIDATES, linked);
        linked.erase(std::remove_if(linked.begin(), linked.end(), [](Unit const* unit)
        {
            return !unit->IsAlive() || unit->GetMaxHealth() == 0;
        }), linked.end());
        if (linked.empty())
            return;

        float total = 0.0f;
        for (Unit const* unit : linked)
            total += unit->GetHealthPct();
        float const average = total / float(linked.size());

        for (Unit* unit : linked)
        {
            me->CastSpell(unit, ShamanData::SPELL_SPIRIT_LINK_AURA, true);

            uint32 const maxHealth = unit->GetMaxHealth();
            uint32 const health = std::clamp<uint32>(uint32(float(maxHealth) * average / 100.0f + 0.5f), 1, maxHealth);
            if (health != unit->GetHealth())
                unit->SetHealth(health);
        }
    }
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
 * npc_pet_shaman_earth_elemental: Angered Earth (AoE taunt) on engage, then every 5-20 sec. With the owner's Power of
 * the Elements it never taunts: the cast is skipped (the zero-threat aura is the owner's, Shaman::OnElementalAdded).
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
            // Checked on every cast, so learning or respeccing Power of the Elements mid-fight takes effect
            Player const* owner = GetOwnerPlayer(me);
            if (!owner || !HasPowerOfTheElements(owner))
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

/*
 * 300262-300265 - Elemental Spirit wolf stats. The new entries get none of the stock Feral Spirit setup that
 * Guardian::InitStatsForLevel hardcodes on NPC_FERAL_SPIRIT (Pet.cpp:1310-1328), so it is replicated here: weapon
 * damage 1.5L..2.5L at attack time 1500, the avoidance and hit/expertise auras, the three Feral Spirit scaling auras
 * (spell_sha_feral_spirit_scaling reads the owner, never the entry) and the Orc racial. Not given: Spirit Hunt, Bash,
 * Spirit Walk, Twin Howl (S3-NOTES D2). The hook runs after the entry switch and before UpdateAllStats(), so no stat
 * update call is needed. Filtered on the four entries and a player owner.
 */
class ShamanSpiritWolfPetScript : public PetScript
{
public:
    ShamanSpiritWolfPetScript() : PetScript("ShamanSpiritWolfPetScript", { PETHOOK_ON_INIT_STATS_FOR_LEVEL }) { }

    void OnInitStatsForLevel(Guardian* guardian, uint8 petlevel) override
    {
        if (!guardian || !IsSpiritWolfEntry(guardian->GetEntry()))
            return;

        // Minion::GetOwner uses the owner GUID stored at construction, valid before SetMinion.
        Unit* ownerUnit = guardian->GetOwner();
        Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        guardian->SetAttackTime(BASE_ATTACK, WOLF_ATTACK_TIME_MS);
        guardian->SetBaseWeaponDamage(BASE_ATTACK, MINDAMAGE, float(petlevel) * WOLF_DAMAGE_MIN_PER_LEVEL);
        guardian->SetBaseWeaponDamage(BASE_ATTACK, MAXDAMAGE, float(petlevel) * WOLF_DAMAGE_MAX_PER_LEVEL);

        guardian->AddAura(SPELL_PET_AVOIDANCE, guardian);
        guardian->AddAura(SPELL_HUNTER_PET_SCALING_04, guardian);
        guardian->AddAura(SPELL_FERAL_SPIRIT_SCALING_01, guardian);
        guardian->AddAura(SPELL_FERAL_SPIRIT_SCALING_02, guardian);
        guardian->AddAura(SPELL_FERAL_SPIRIT_SCALING_03, guardian);

        if (owner->getRace() == RACE_ORC)
            guardian->CastSpell(guardian, SPELL_ORC_RACIAL_COMMAND_SHAMAN, true, nullptr, nullptr, owner->GetGUID());
    }
};

/*
 * Shared part of the four wolves: the Fire/Earth elemental shape (ShamanMeleeElementalAI: engaged-only targets, no
 * proximity aggro, stock UpdateVictim once fighting) without the totem slot, plus a bite queue.
 *
 * The bite hook: DamageDealt runs inside Unit::DealDamage, before the victim's health changes, so nothing is cast
 * there. A melee auto attack is the only DIRECT_DAMAGE the wolf deals (its spells are SPELL_DIRECT_DAMAGE/DOT), so
 * DIRECT_DAMAGE marks a bite. Each bite queues the victim's GUID and the next UpdateAI hands it to OnBite().
 *
 * Every hook checks the creature entry (the ScriptName could be set on another entry) and a player owner
 * (L-12); a wolf without one stays idle.
 */
class ShamanSpiritWolfAI : public ScriptedAI
{
public:
    ShamanSpiritWolfAI(Creature* creature, uint32 entry) : ScriptedAI(creature), _entry(entry) { }

    // Stock: no Reset() on AI creation.
    void InitializeAI() override { }

    // No proximity aggro: engaged-only targets.
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        _hits.clear();
        scheduler.CancelAll();
        scheduler.Schedule(0ms, [this](TaskContext context)
        {
            AcquireEngagedTarget();
            context.Repeat(Milliseconds(ELEMENTAL_ACQUIRE_INTERVAL_MS));
        });

        OnWolfSummoned();
    }

    void DamageDealt(Unit* victim, uint32& /*damage*/, DamageEffectType damageType,
        SpellSchoolMask /*damageSchoolMask*/) override
    {
        if (damageType != DIRECT_DAMAGE || !victim || _hits.size() >= WOLF_HIT_QUEUE_CAP)
            return;

        _hits.push_back(victim->GetGUID());
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
        DrainHits();

        if (!UpdateVictim())
            return;

        DoMeleeAttackIfReady();
    }

protected:
    // The player owner while this is the right entry and the wolf is alive; nullptr otherwise. Any class owns a wolf
    // (Classless: another class can take Elemental Spirits); a wolf with no player owner stays idle.
    Player* GetActiveOwner() const
    {
        if (!me->IsAlive() || me->GetEntry() != _entry)
            return nullptr;

        return GetOwnerPlayer(me);
    }

    // Once, from the first update after the summon (the owner's summon spell has finished by then).
    virtual void OnWolfSummoned() { }

    // One landed bite. `victim` is null when it died or left the map since the bite.
    virtual void OnBite(Player* /*owner*/, Unit* /*victim*/) { }

    void AcquireEngagedTarget()
    {
        if (!me->IsAlive() || me->GetVictim())
            return;

        Player* owner = GetActiveOwner();
        if (!owner)
            return;

        if (Unit* target = Engagement::SelectEngagedTarget(me, owner, ObjectGuid::Empty,
            ShamanData::ELEMENTAL_TARGET_RANGE_YD))
            if (me->CanCreatureAttack(target))
                AttackStart(target);
    }

private:
    void DrainHits()
    {
        if (_hits.empty())
            return;

        std::vector<ObjectGuid> hits;
        hits.swap(_hits);

        Player* owner = GetActiveOwner();
        if (!owner)
            return;

        for (ObjectGuid const& guid : hits)
        {
            Unit* victim = ObjectAccessor::GetUnit(*me, guid);
            if (victim && (!victim->IsAlive() || !victim->IsInMap(me)))
                victim = nullptr;

            OnBite(owner, victim);
        }
    }

    uint32 _entry;
    std::vector<ObjectGuid> _hits;
};

/*
 * 300262 - Fire Spirit. Every bite casts Spirit Flame Shock (a separate spell from the shaman's Flame Shock, never
 * d0 b28: it stacks with it and refreshes only its own copy). Cast by the wolf, so it rolls none of the shaman's
 * procs; the owner's Fire/Elemental Ascendance bonus is fixed at apply by spell_sha_enh_spirit_flame_shock.
 */
struct npc_sha_fire_spirit : public ShamanSpiritWolfAI
{
    explicit npc_sha_fire_spirit(Creature* creature)
        : ShamanSpiritWolfAI(creature, uint32(ShamanData::NPC_FIRE_SPIRIT)) { }

protected:
    void OnBite(Player* /*owner*/, Unit* victim) override
    {
        if (victim)
            me->CastSpell(victim, ShamanData::SPELL_SPIRIT_FLAME_SHOCK, true);
    }
};

/*
 * 300263 - Frost Spirit. Copies each Stormstrike the shaman lands at FROST_COPY_PCT of the landed damage, but the
 * copy is cast by Shaman::OnStormstrikeLanded (ShamanMechanics.cpp: it finds the shaman's Frost Spirits in m_Controlled
 * and casts Frost Spirit Copy from each, script-sized, no Nature bonus, no Improved Stormstrike), so the wolf itself
 * is the shared melee base only. Its own bites do nothing extra.
 */
struct npc_sha_frost_spirit : public ShamanSpiritWolfAI
{
    explicit npc_sha_frost_spirit(Creature* creature)
        : ShamanSpiritWolfAI(creature, uint32(ShamanData::NPC_FROST_SPIRIT)) { }
};

/*
 * 300264 - Wind Spirit. Each bite rolls GUST_CHANCE x the owner's Proc Chance; a success makes the SHAMAN cast Gust at
 * the wolf's target (owner attack power and talents, S3-NOTES D8). The cast is triggered, so the Gust rolls nothing
 * of the shaman's procs. The victim is the wolf's own (engaged) target.
 */
struct npc_sha_wind_spirit : public ShamanSpiritWolfAI
{
    explicit npc_sha_wind_spirit(Creature* creature)
        : ShamanSpiritWolfAI(creature, uint32(ShamanData::NPC_WIND_SPIRIT)) { }

protected:
    void OnBite(Player* owner, Unit* victim) override
    {
        if (!victim || !owner->IsAlive() || !Shaman::RollProcChance(owner, float(ShamanData::GUST_CHANCE)))
            return;

        owner->CastSpell(victim, ShamanData::SPELL_GUST, true);
    }
};

/*
 * 300265 - Rock Spirit (replaces the Wind Spirit while Rockbiter is active, chosen at the cast by
 * spell_sha_enh_elemental_spirits). On summon: Rock Spirit Taunt on every enemy within ROCK_TAUNT_RADIUS_YD of the
 * wolf in line of sight (all enemies in the area, not engaged-only: S3-NOTES section 4), skipping targets with no
 * threat list and targets immune to the taunt's effects (the Sim Raid Boss and level-63 raid bosses). Each bite
 * grants the shaman ROCK_SPIRIT_STONESKIN_PER_HIT Stoneskin (Shaman::AddStoneskin needs Rockbiter itself) - the one
 * named exception to guardian damage granting nothing. Gains no Ascendance.
 */
struct npc_sha_rock_spirit : public ShamanSpiritWolfAI
{
    explicit npc_sha_rock_spirit(Creature* creature)
        : ShamanSpiritWolfAI(creature, uint32(ShamanData::NPC_ROCK_SPIRIT)) { }

protected:
    void OnWolfSummoned() override
    {
        scheduler.Schedule(0ms, [this](TaskContext /*context*/)
        {
            TauntNearbyEnemies();
        });
    }

    void OnBite(Player* owner, Unit* /*victim*/) override
    {
        Shaman::AddStoneskin(owner, uint32(ShamanData::ROCK_SPIRIT_STONESKIN_PER_HIT));
    }

private:
    void TauntNearbyEnemies()
    {
        if (!GetActiveOwner())
            return;

        SpellInfo const* tauntInfo = sSpellMgr->GetSpellInfo(ShamanData::SPELL_ROCK_SPIRIT_TAUNT);
        if (!tauntInfo)
            return;

        float const radius = ShamanData::ROCK_TAUNT_RADIUS_YD;
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(me, me, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(me, nearby, check);
        Cell::VisitObjects(me, searcher, radius);

        for (Unit* enemy : nearby)
        {
            if (!enemy->IsAlive() || !enemy->CanHaveThreatList() || !me->IsValidAttackTarget(enemy) ||
                !me->IsWithinLOSInMap(enemy) || IsImmuneToAnyEffect(enemy, tauntInfo, me))
                continue;

            me->CastSpell(enemy, ShamanData::SPELL_ROCK_SPIRIT_TAUNT, true);
        }
    }
};

void AddSC_shaman_rework_pet_scripts()
{
    RegisterCreatureAI(npc_sha_elemental_totem);
    RegisterCreatureAI(npc_sha_searing_totem);
    RegisterCreatureAI(npc_sha_earthen_wall_totem);
    RegisterCreatureAI(npc_sha_undulating_currents_totem);
    RegisterCreatureAI(npc_sha_spirit_link_totem);
    RegisterCreatureAI(npc_sha_fire_elemental_rework);
    RegisterCreatureAI(npc_sha_earth_elemental_rework);
    RegisterCreatureAI(npc_sha_water_elemental);
    RegisterCreatureAI(npc_sha_storm_elemental);
    RegisterCreatureAI(npc_sha_fire_spirit);
    RegisterCreatureAI(npc_sha_frost_spirit);
    RegisterCreatureAI(npc_sha_wind_spirit);
    RegisterCreatureAI(npc_sha_rock_spirit);
    new ShamanSpiritWolfPetScript();
}
