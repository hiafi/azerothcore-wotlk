/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "SimTankDummyAI.h"
#include "Creature.h"
#include "CreatureData.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SimDummyAI.h"
#include "ThreatManager.h"
#include <algorithm>
#include <map>

namespace
{
    SimTankSwingObserver* s_observer = nullptr;

    // What the solver last did for a dummy, so a run with the same range and swing interval does not solve again
    struct Solved
    {
        SimTank::HitRange Range;
        uint32 SwingMs = 0;
        SimTank::DummyInfo Info;
    };
    std::map<ObjectGuid, Solved> s_solved;

    // How much of the minimum hit the attack power may provide before the solver scales the damage multiplier instead.
    // The creature formula adds AP / 14 * variance to the base weapon damage and multiplies the lot by DamageModifier (35
    // on the sim dummies) and the swing time in seconds, so at 2 s the level-63 dummy's own attack power is already ~1,300
    // of a 2,250 minimum. If the AP alone would exceed the minimum, the weapon damage would have to go negative.
    constexpr float MAX_AP_SHARE_OF_MIN = 0.5f;
}

void SimTankDummyAI::Reset()
{
    // Passive and rooted: it never chases, never repositions (MoveBackwardsChecks and MoveCircleChecks return early for a
    // rooted creature) and a stray knockback or pull cannot carry it out of the layout the sim built
    me->SetReactState(REACT_PASSIVE);
    me->SetControlled(true, UNIT_STATE_ROOT);
}

void SimTankDummyAI::DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*damageType*/,
    SpellSchoolMask /*schoolMask*/)
{
    // The passive dummy's rule (SimDummyAI.cpp): all damage zeroed, or with health drain real damage that never takes it
    // below 1 health
    if (SimDummyAI::IsHealthDrainEnabled())
    {
        uint32 const health = me->GetHealth();
        damage = health > 1 ? std::min(damage, health - 1) : 0;
        return;
    }

    damage = 0;
}

void SimTankDummyAI::BeginFight(Unit* victim)
{
    _victim = victim->GetGUID();
    _fighting = true;

    if (!me->Attack(victim, true))
        LOG_WARN("server.dpssim", "mod-dpssim: dummy {} could not start attacking '{}' (Unit::Attack refused).",
            me->GetGUID().ToString(), victim->GetName());

    // The first swing lands one swing interval after the pull, then every interval
    me->resetAttackTimer();
}

void SimTankDummyAI::EndFight()
{
    _fighting = false;
    _victim = ObjectGuid::Empty;
    me->AttackStop();
    me->resetAttackTimer();
    me->GetThreatMgr().ResetAllThreat();
}

void SimTankDummyAI::UpdateAI(uint32 /*diff*/)
{
    // Before the pull and after the iteration the dummy does nothing: the pre-pull buff phase must run untouched (plan R5)
    if (!_fighting)
        return;

    Unit* victim = me->GetVictim();
    if (!victim || victim->GetGUID() != _victim)
    {
        // Something dropped the attack (a combat stop, a taunt effect on the dummy): take the actor up again
        Unit* actor = ObjectAccessor::GetUnit(*me, _victim);
        if (!actor || !me->Attack(actor, true))
            return;
        victim = actor;
    }

    // The conditions DoMeleeAttackIfReady() checks before it swings, so the observer only brackets real swings
    if (me->IsActionPreventedByCasting() || !victim->IsInWorld() || !me->isAttackReady() ||
        !me->IsWithinMeleeRange(victim))
        return;

    if (s_observer)
        s_observer->BeginSwing(me, victim);
    DoMeleeAttackIfReady();
    if (s_observer)
        s_observer->EndSwing();
}

void SimTankDummy::SetObserver(SimTankSwingObserver* observer)
{
    s_observer = observer;
}

bool SimTankDummy::Install(std::vector<Creature*> const& dummies, Settings const& settings)
{
    bool ok = true;
    for (Creature* dummy : dummies)
    {
        // The swing interval: the base attack time field the core's timers and the creature damage formula both read
        dummy->SetAttackTime(BASE_ATTACK, settings.SwingMs);

        // The crit and parry-haste switches are creature template flags the core reads through the template
        // (Unit::RollMeleeOutcomeAgainst and Unit::DealMeleeDamage). Entries 900004-900009 only exist as the sim's
        // dummies, and this process is the batch's own, so changing the template changes nothing outside the run.
        CreatureTemplate* tmpl = const_cast<CreatureTemplate*>(dummy->GetCreatureTemplate());
        if (settings.Crit)
            tmpl->flags_extra &= ~uint32(CREATURE_FLAG_EXTRA_NO_CRIT);
        else
            tmpl->flags_extra |= uint32(CREATURE_FLAG_EXTRA_NO_CRIT);
        // Attack() calls for assistance from friendly creatures nearby (faction 31 is shared with critters): the dummies
        // must not pull a stray critter into the fight
        tmpl->flags_extra |= uint32(CREATURE_FLAG_EXTRA_DONT_CALL_ASSISTANCE);
        if (settings.ParryHaste)
            tmpl->flags_extra &= ~uint32(CREATURE_FLAG_EXTRA_NO_PARRY_HASTEN);
        else
            tmpl->flags_extra |= uint32(CREATURE_FLAG_EXTRA_NO_PARRY_HASTEN);

        if (!dummy->AIM_Initialize(new SimTankDummyAI(dummy)))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimTankDummy::Install() - dummy {} refused the AI swap "
                "(AIM_Initialize failed).", dummy->GetGUID().ToString());
            ok = false;
        }
    }

    return ok;
}

SimTank::DummyInfo SimTankDummy::SolveHit(Creature* dummy, SimTank::HitRange const& range, uint32 swingMs)
{
    Solved& cached = s_solved[dummy->GetGUID()];
    if (cached.SwingMs == swingMs && cached.Range == range && cached.Info.FieldMax > 0.0f)
        return cached.Info;

    CreatureTemplate const* tmpl = dummy->GetCreatureTemplate();
    dummy->SetAttackTime(BASE_ATTACK, swingMs);

    // The creature formula (Creature::CalculateMinMaxDamage), mainhand:
    //   hit = ((weapon + AP / 14 * variance) * DamageModifier * basePct * speed + totalFlat) * totalPct
    // with speed = the attack time in seconds. Everything except the weapon damage is read, not changed: AP, the template
    // multiplier and the modifier groups, so an aura later on re-runs the same formula with the same weapon damage.
    float const ap = dummy->GetTotalAttackPowerValue(BASE_ATTACK);
    float const apTerm = ap / 14.0f * tmpl->BaseVariance;
    float const speed = float(dummy->GetAttackTime(BASE_ATTACK)) / 1000.0f;
    float const damageMod = tmpl->DamageModifier;
    float const totalFlat = dummy->GetFlatModifierValue(UNIT_MOD_DAMAGE_MAINHAND, TOTAL_VALUE);
    float const totalPct = std::max(dummy->GetPctModifierValue(UNIT_MOD_DAMAGE_MAINHAND, TOTAL_PCT), 0.0001f);
    float basePct = dummy->GetPctModifierValue(UNIT_MOD_DAMAGE_MAINHAND, BASE_PCT);

    float const minInner = float(range.Min) / totalPct - totalFlat;
    float const maxInner = float(range.Max) / totalPct - totalFlat;

    // The attack power's share of the minimum hit would overshoot it: scale the base multiplier down so AP stays at
    // MAX_AP_SHARE_OF_MIN of it (the weapon damage then carries the rest, and a debuff still lowers the AP part)
    if (apTerm > 0.0f && damageMod > 0.0f && speed > 0.0f && apTerm * damageMod * basePct * speed >
        MAX_AP_SHARE_OF_MIN * minInner)
    {
        basePct = MAX_AP_SHARE_OF_MIN * minInner / (apTerm * damageMod * speed);
        dummy->SetStatPctModifier(UNIT_MOD_DAMAGE_MAINHAND, BASE_PCT, basePct);
    }

    float const k = damageMod * basePct * speed;
    float weaponMin = 0.0f;
    float weaponMax = 0.0f;
    if (k > 0.0f)
    {
        weaponMin = std::max(minInner / k - apTerm, 0.0f);
        weaponMax = std::max(maxInner / k - apTerm, weaponMin);
    }
    else
        LOG_ERROR("server.dpssim", "mod-dpssim: SimTankDummy::SolveHit() - dummy {}: DamageModifier {} x base pct {} x "
            "speed {} is not positive, the hit cannot be solved.", dummy->GetGUID().ToString(), damageMod, basePct,
            speed);

    dummy->SetBaseWeaponDamage(BASE_ATTACK, MINDAMAGE, weaponMin);
    dummy->SetBaseWeaponDamage(BASE_ATTACK, MAXDAMAGE, weaponMax);
    dummy->UpdateAttackPowerAndDamage(false);

    SimTank::DummyInfo info;
    info.Hit = range;
    info.SwingMs = swingMs;
    info.Level = dummy->GetLevel();
    info.Armor = dummy->GetArmor();
    info.WeaponMin = weaponMin;
    info.WeaponMax = weaponMax;
    info.AttackPower = ap;
    info.DamageModifier = damageMod;
    info.BasePct = basePct;
    info.FieldMin = dummy->GetFloatValue(UNIT_FIELD_MINDAMAGE);
    info.FieldMax = dummy->GetFloatValue(UNIT_FIELD_MAXDAMAGE);

    cached.Range = range;
    cached.SwingMs = swingMs;
    cached.Info = info;
    return info;
}

std::vector<SimTank::DummyInfo> SimTankDummy::BeginFight(std::vector<Creature*> const& dummies, Player* actor,
    Settings const& settings)
{
    std::vector<SimTank::DummyInfo> infos;
    infos.reserve(dummies.size());
    for (Creature* dummy : dummies)
    {
        SimTank::DummyInfo info = SolveHit(dummy, settings.Hit, settings.SwingMs);
        info.LevelForTarget = dummy->getLevelForTarget(actor);
        info.ExpectedCritPct = dummy->GetUnitCriticalChance(BASE_ATTACK, actor);
        infos.push_back(info);

        if (auto* ai = dynamic_cast<SimTankDummyAI*>(dummy->AI()))
            ai->BeginFight(actor);
        else
            LOG_ERROR("server.dpssim", "mod-dpssim: SimTankDummy::BeginFight() - dummy {} does not run the tank AI.",
                dummy->GetGUID().ToString());
    }

    return infos;
}

void SimTankDummy::EndFight(std::vector<Creature*> const& dummies)
{
    for (Creature* dummy : dummies)
        if (auto* ai = dynamic_cast<SimTankDummyAI*>(dummy->AI()))
            ai->EndFight();
}
