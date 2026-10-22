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
}

void SimTankDummyAI::Reset()
{
    // Passive and rooted: it never chases, never repositions (MoveBackwardsChecks and MoveCircleChecks return early for
    // a rooted creature) and a stray knockback or pull cannot carry it out of the layout the sim built
    me->SetReactState(REACT_PASSIVE);
    me->SetControlled(true, UNIT_STATE_ROOT);
}

void SimTankDummyAI::DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*damageType*/,
    SpellSchoolMask /*schoolMask*/)
{
    // The passive dummy's rule (SimDummyAI.cpp): all damage zeroed, or with health drain real damage that never takes
    // it below 1 health
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

    // Threat counts from the pull only: EndFight() dropped it before the pre-pull buff phase, and whatever the buff
    // phase added (a stray proc, a pet) goes too
    me->GetThreatMgr().ResetAllThreat();

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
    // A root aura on the dummy that expired cleared the root state, the AI's own included (Unit::SetControlled(false,
    // UNIT_STATE_ROOT) when the last root effect goes): put it back, or a pack dummy that is not the bot's target would
    // start circling the actor
    if (!me->HasUnitState(UNIT_STATE_ROOT))
        me->SetControlled(true, UNIT_STATE_ROOT);

    // Before the pull and after the iteration the dummy does nothing: the buff phase must run untouched (plan R5)
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

bool SimTankDummy::Install(std::vector<Creature*> const& dummies, Player* actor, Settings const& settings)
{
    bool ok = true;
    for (Creature* dummy : dummies)
    {
        // The AI first: nothing below changes a dummy that refused it. AIM_Initialize only refuses (an AI update in
        // progress) before it takes the new AI, which then is still ours to delete.
        SimTankDummyAI* ai = new SimTankDummyAI(dummy);
        if (!dummy->AIM_Initialize(ai))
        {
            delete ai;
            LOG_ERROR("server.dpssim", "mod-dpssim: SimTankDummy::Install() - dummy {} refused the AI swap "
                "(AIM_Initialize failed).", dummy->GetGUID().ToString());
            ok = false;
            continue;
        }

        // The swing interval: the base attack time field the core's timers and the creature damage formula both read
        dummy->SetAttackTime(BASE_ATTACK, settings.SwingMs);

        // The crit switch is a creature template flag the core reads through the template
        // (Unit::RollMeleeOutcomeAgainst). Entries 900004-900009 only exist as the sim's dummies, and this process is
        // the batch's own, so changing the template changes nothing outside the run.
        CreatureTemplate* tmpl = const_cast<CreatureTemplate*>(dummy->GetCreatureTemplate());
        if (settings.Crit)
            tmpl->flags_extra &= ~uint32(CREATURE_FLAG_EXTRA_NO_CRIT);
        else
            tmpl->flags_extra |= uint32(CREATURE_FLAG_EXTRA_NO_CRIT);
        // Attack() calls for assistance from friendly creatures nearby (faction 31 is shared with critters): the
        // dummies must not pull a stray critter into the fight
        tmpl->flags_extra |= uint32(CREATURE_FLAG_EXTRA_DONT_CALL_ASSISTANCE);

        if (!dummy->isWorldBoss())
            continue;

        // The boss dummy is a raid boss to the actor (plan T8, T9). Its real level becomes the level it already
        // fights the actor at: for a BOSS_MOB Creature::getLevelForTarget() is the *target's* level +
        // CONFIG_WORLD_BOSS_LEVEL_DIFF, whatever the creature's own level, so after SetLevel() the outcome roll
        // (hit, crit, skill) stays at actor + 3 while armor reduction (Unit::CalcArmorReducedDamage, the attacker's
        // GetLevel()) moves from the actor's level to it. Nothing else of the dummy follows the level: SetLevel()
        // only writes the field (the attack power stays the template's, the solver runs after this), and armor and
        // max health are pinned in the stat modifiers by SimTarget::Create(), recalculated here as a level change
        // there would be.
        uint8 const bossLevel = dummy->getLevelForTarget(actor);
        uint8 const oldLevel = dummy->GetLevel();
        dummy->SetLevel(bossLevel);
        dummy->UpdateArmor();
        dummy->UpdateMaxHealth();
        dummy->SetFullHealth();

        // Concussion Blow, Hammer of Justice, Bash...: a raid boss shrugs them off; the pack stays stunnable
        dummy->ApplySpellImmune(0, IMMUNITY_MECHANIC, MECHANIC_STUN, true);

        LOG_INFO("server.dpssim", "mod-dpssim: boss dummy {} - level {} -> {} (fights the actor, level {}, as level "
            "{}), armor {}, max health {}, stun immune.", dummy->GetGUID().ToString(), oldLevel, dummy->GetLevel(),
            actor->GetLevel(), dummy->getLevelForTarget(actor), dummy->GetArmor(), dummy->GetMaxHealth());
    }

    return ok;
}

SimTank::DummyInfo SimTankDummy::SolveHit(Creature* dummy, SimTank::HitRange const& range, uint32 swingMs)
{
    Solved& cached = s_solved[dummy->GetGUID()];
    if (cached.SwingMs == swingMs && cached.Range == range && cached.Info.FieldMax > 0.0f)
    {
        // Same weapon damage and multiplier as solved; the rest is read live, so the pull log shows this iteration's
        // dummy (an aura left over from the previous iteration would show here), not the first iteration's
        SimTank::DummyInfo info = cached.Info;
        info.Level = dummy->GetLevel();
        info.Armor = dummy->GetArmor();
        info.AttackPower = dummy->GetTotalAttackPowerValue(BASE_ATTACK);
        info.FieldMin = dummy->GetFloatValue(UNIT_FIELD_MINDAMAGE);
        info.FieldMax = dummy->GetFloatValue(UNIT_FIELD_MAXDAMAGE);
        return info;
    }

    CreatureTemplate const* tmpl = dummy->GetCreatureTemplate();
    dummy->SetAttackTime(BASE_ATTACK, swingMs);

    // The creature formula (Creature::CalculateMinMaxDamage), mainhand:
    //   hit = ((weapon + baseFlat + AP / 14 * variance) * DamageModifier * basePct * speed + totalFlat) * totalPct
    // with speed = the attack time in seconds. The weapon damage and the base pct are set; everything else is read: AP,
    // the template multiplier and the other modifier groups, so an aura later on re-runs the same formula.
    float const ap = dummy->GetTotalAttackPowerValue(BASE_ATTACK);
    float const apTerm = ap / 14.0f * tmpl->BaseVariance;
    // UNIT_MOD_DAMAGE_MAINHAND BASE_VALUE: added next to the AP term (0 on the dummies; read so an aura adding it
    // cannot shift the solved range)
    float const baseFlat = dummy->GetFlatModifierValue(UNIT_MOD_DAMAGE_MAINHAND, BASE_VALUE);
    float const speed = float(dummy->GetAttackTime(BASE_ATTACK)) / 1000.0f;
    float const damageMod = tmpl->DamageModifier;
    float const totalFlat = dummy->GetFlatModifierValue(UNIT_MOD_DAMAGE_MAINHAND, TOTAL_VALUE);
    float const totalPct = std::max(dummy->GetPctModifierValue(UNIT_MOD_DAMAGE_MAINHAND, TOTAL_PCT), 0.0001f);
    float basePct = dummy->GetPctModifierValue(UNIT_MOD_DAMAGE_MAINHAND, BASE_PCT);

    float const minInner = float(range.Min) / totalPct - totalFlat;
    float const maxInner = float(range.Max) / totalPct - totalFlat;

    // The attack power makes up exactly AP_SHARE_OF_MIN of the minimum hit (plan T10): the base multiplier is set so
    // apTerm x DamageModifier x basePct x speed = share x minimum, and the weapon damage carries the rest. At the
    // dummies' own AP the unscaled AP term alone is ~50% of the minimum (more for a pack's smaller hit), so this always
    // scales down; with no attack power at all there is nothing to scale and the base pct stays as it is.
    if (apTerm > 0.0f && damageMod > 0.0f && speed > 0.0f && minInner > 0.0f)
    {
        basePct = AP_SHARE_OF_MIN * minInner / (apTerm * damageMod * speed);
        dummy->SetStatPctModifier(UNIT_MOD_DAMAGE_MAINHAND, BASE_PCT, basePct);
    }

    float const k = damageMod * basePct * speed;
    float weaponMin = 0.0f;
    float weaponMax = 0.0f;
    if (k > 0.0f)
    {
        weaponMin = std::max(minInner / k - apTerm - baseFlat, 0.0f);
        weaponMax = std::max(maxInner / k - apTerm - baseFlat, weaponMin);
    }
    else
        LOG_ERROR("server.dpssim", "mod-dpssim: SimTankDummy::SolveHit() - dummy {}: DamageModifier {} x base pct {} "
            "x speed {} is not positive, the hit cannot be solved.", dummy->GetGUID().ToString(), damageMod, basePct,
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
