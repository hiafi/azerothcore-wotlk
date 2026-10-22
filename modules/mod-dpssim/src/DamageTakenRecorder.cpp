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

#include "DamageTakenRecorder.h"
#include "Creature.h"
#include "Log.h"
#include "CreatureData.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "Timer.h"
#include "Unit.h"
#include <algorithm>
#include <utility>

namespace
{
    // Hundredths of a percent as the 16 bits SwingEvent keeps (the core's chances are int32 hundredths, at most 10000)
    uint16 ToHundredths(int32 value)
    {
        return uint16(std::clamp(value, 0, 10000));
    }

    SimTank::Outcome OutcomeOf(CalcDamageInfo const* info)
    {
        switch (info->hitOutCome)
        {
            case MELEE_HIT_MISS:
                return SimTank::Outcome::Miss;
            case MELEE_HIT_DODGE:
                return SimTank::Outcome::Dodge;
            case MELEE_HIT_PARRY:
                return SimTank::Outcome::Parry;
            case MELEE_HIT_BLOCK:
                return info->TargetState == VICTIMSTATE_BLOCKS ? SimTank::Outcome::FullBlock : SimTank::Outcome::Block;
            case MELEE_HIT_CRIT:
                return SimTank::Outcome::Crit;
            case MELEE_HIT_CRUSHING:
                return SimTank::Outcome::Crush;
            case MELEE_HIT_GLANCING:
                return SimTank::Outcome::Glancing;
            case MELEE_HIT_NORMAL:
                return SimTank::Outcome::Hit;
            default:
                return SimTank::Outcome::Other;
        }
    }
}

DamageTakenRecorder::DamageTakenRecorder(ObjectGuid actorGuid, std::vector<ObjectGuid> dummyGuids, bool unkillable)
    : UnitScript("mod_dpssim_damage_taken_recorder", true,
                 {UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST,
                  UNITHOOK_ON_ABSORB_FINAL, UNITHOOK_ON_MELEE_OUTCOME_FINAL, UNITHOOK_ON_DAMAGE}),
      _actorGuid(actorGuid), _dummyGuids(std::move(dummyGuids)), _unkillable(unkillable)
{
}

int8 DamageTakenRecorder::IndexOfDummy(ObjectGuid guid) const
{
    for (size_t i = 0; i < _dummyGuids.size(); ++i)
        if (_dummyGuids[i] == guid)
            return int8(i);
    return -1;
}

void DamageTakenRecorder::ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage)
{
    // Read only, and only a dummy's swing at the actor: the actor's own swings and everything else pass by
    if (!target || !attacker || target->GetGUID() != _actorGuid || IndexOfDummy(attacker->GetGUID()) < 0)
        return;

    // A swing the core abandoned before its outcome hook leaves a stale open one; the new swing replaces it
    _open = OpenSwing{};
    _open.Active = true;
    _open.PreArmor = damage;
    // The same function the core just ran on the swing, on a large hit so the flat part washes out: the multiplier
    _open.TakenMult = float(target->MeleeDamageBonusTaken(attacker, 1000000, BASE_ATTACK, nullptr,
        SPELL_SCHOOL_MASK_NORMAL)) / 1000000.0f;
    _pendingAbsorbs.clear();
}

void DamageTakenRecorder::OnBeforeRollMeleeOutcomeAgainst(Unit const* attacker, Unit const* victim,
    WeaponAttackType /*attType*/, int32& /*attackerMaxSkillValueForLevel*/, int32& victimMaxSkillValueForLevel,
    int32& attackerWeaponSkill, int32& victimDefenseSkill, int32& crit_chance, int32& miss_chance,
    int32& dodge_chance, int32& parry_chance, int32& block_chance)
{
    if (!_open.Active || !attacker || !victim || victim->GetGUID() != _actorGuid ||
        IndexOfDummy(attacker->GetGUID()) < 0)
        return;

    // What Unit::RollMeleeOutcomeAgainst does with these numbers, replayed read-only: the skill difference lowers each
    // avoidance chance (0.04% per point), the arc and casting rules switch them off, and a creature attacker's
    // expertise lowers dodge and parry. Everything here is a local copy.
    int32 const skillBonus = 4 * (attackerWeaponSkill - victimMaxSkillValueForLevel);
    int32 const expertise = attacker->GetTotalAuraModifier(SPELL_AURA_MOD_EXPERTISE) * 25;
    bool const inFront = victim->HasInArc(M_PI, attacker);
    bool const cannotAvoid = victim->IsNonMeleeSpellCast(false, false, true) ||
        victim->HasUnitState(UNIT_STATE_CONTROLLED);

    auto const avoid = [&](int32 chance, bool allowed) -> int32
    {
        if (!allowed || cannotAvoid || chance <= 0)
            return 0;
        chance -= skillBonus;
        return std::max(chance, 0);
    };

    // The outcomes share one 0-10000 roll, in this order (miss, dodge, parry, block, then crit), so a later one only
    // has what the earlier ones left: Shield Block pushes the block chance past 100%, and everything after it gets 0
    int32 const miss = std::min(std::max(miss_chance, 0), 10000);
    int32 const dodge = std::min(avoid(dodge_chance - expertise, inFront), 10000 - miss);
    int32 const parry = std::min(avoid(parry_chance - expertise, inFront), 10000 - miss - dodge);
    int32 const block = std::min(avoid(block_chance, inFront), 10000 - miss - dodge - parry);

    // A crit is rolled after miss, dodge, parry and block took their share of the same 0-10000 roll; a creature with
    // CREATURE_FLAG_EXTRA_NO_CRIT never turns the roll into one
    int32 crit = std::max(crit_chance, 0);
    if (attacker->IsCreature() && attacker->ToCreature()->HasFlagsExtra(CREATURE_FLAG_EXTRA_NO_CRIT))
        crit = 0;
    crit = std::min(crit, std::max(10000 - miss - dodge - parry - block, 0));

    static bool loggedFirstRoll = false;
    if (!loggedFirstRoll)
    {
        loggedFirstRoll = true;
        LOG_INFO("server.dpssim", "mod-dpssim: first dummy swing's roll inputs (hundredths of a percent): crit {}, "
            "miss {}, dodge {}, parry {}, block {}; attacker weapon skill {}, actor max skill {}, defense {}; "
            "effective: crit {}, miss {}, dodge {}, parry {}, block {}; actor in front arc: {}.", crit_chance,
            miss_chance, dodge_chance, parry_chance, block_chance, attackerWeaponSkill, victimMaxSkillValueForLevel,
            victimDefenseSkill, crit, miss, dodge, parry, block, inFront ? "yes" : "no");
    }

    _open.HaveChances = true;
    _open.ExpectedMiss = ToHundredths(miss);
    _open.ExpectedDodge = ToHundredths(dodge);
    _open.ExpectedParry = ToHundredths(parry);
    _open.ExpectedBlock = ToHundredths(block);
    _open.ExpectedCrit = ToHundredths(crit);
    _open.InFrontArc = inFront;
}

void DamageTakenRecorder::OnAbsorbFinal(Unit* victim, Unit* attacker, AuraEffect const* absorbAurEff, uint32 absorbed)
{
    if (!_open.Active || !victim || victim->GetGUID() != _actorGuid || !attacker ||
        IndexOfDummy(attacker->GetGUID()) < 0 || !absorbAurEff || absorbed == 0)
        return;

    _pendingAbsorbs.push_back({absorbAurEff->GetId(), absorbed});
}

void DamageTakenRecorder::OnMeleeOutcomeFinal(CalcDamageInfo const* info)
{
    if (!info || !info->attacker || !info->target || info->target->GetGUID() != _actorGuid)
        return;

    int8 const dummyIndex = IndexOfDummy(info->attacker->GetGUID());
    if (dummyIndex < 0)
        return;

    SimTank::SwingEvent swing;
    swing.TimestampMs = getMSTime();
    swing.DummyIndex = uint8(dummyIndex);
    swing.Result = OutcomeOf(info);

    // Only the primary damage index: creatures have no secondary one
    uint32 const final = info->damages[0].damage;
    uint32 const absorbed = info->damages[0].absorb;
    uint32 const resisted = info->damages[0].resist;
    swing.Final = final;
    swing.Absorbed = absorbed;
    swing.Resisted = resisted;

    // The pre-armor value comes from the swing's ModifyMeleeDamage call; without one (not expected) it is unknown and
    // the armor and block splits stay zero
    if (_open.Active)
    {
        swing.PreArmor = _open.PreArmor;
        swing.TakenMult = _open.TakenMult;
        if (_open.HaveChances)
        {
            swing.ExpectedMiss = _open.ExpectedMiss;
            swing.ExpectedDodge = _open.ExpectedDodge;
            swing.ExpectedParry = _open.ExpectedParry;
            swing.ExpectedBlock = _open.ExpectedBlock;
            swing.ExpectedCrit = _open.ExpectedCrit;
            swing.InFrontArc = _open.InFrontArc;
        }

        bool const landed = swing.Result != SimTank::Outcome::Miss && swing.Result != SimTank::Outcome::Dodge &&
            swing.Result != SimTank::Outcome::Parry && swing.Result != SimTank::Outcome::Other;
        if (landed)
        {
            // The same function the core called, on the same inputs: what armor took off the swing
            uint32 afterArmor = swing.PreArmor;
            if (info->damages[0].damageSchoolMask & SPELL_SCHOOL_MASK_NORMAL)
                afterArmor = Unit::CalcArmorReducedDamage(info->attacker, info->target, swing.PreArmor, nullptr, 0,
                    info->attackType);
            swing.ArmorMitigated = swing.PreArmor > afterArmor ? swing.PreArmor - afterArmor : 0;

            // What the block step took off the post-armor damage (the 20% cut, the block value, Critical Block)
            if (swing.Result == SimTank::Outcome::Block || swing.Result == SimTank::Outcome::FullBlock)
            {
                uint32 const beforeShield = final + absorbed + resisted;
                swing.Blocked = afterArmor > beforeShield ? afterArmor - beforeShield : 0;
            }
        }
    }

    // The shields of this swing, split by the absorbing aura
    uint32 const swingIndex = uint32(_swings.size());
    for (PendingAbsorb const& pending : _pendingAbsorbs)
        _absorbs.push_back({swing.TimestampMs, swingIndex, pending.SpellId, pending.Amount});

    // Rage: filled by EndSwing() once the swing is complete (-1 until then, and for an actor with no rage)
    _swings.push_back(swing);

    _open = OpenSwing{};
    _pendingAbsorbs.clear();
}

void DamageTakenRecorder::OnDamage(Unit* attacker, Unit* victim, uint32& damage)
{
    // The dps scenario only, and only a hit that would kill the actor (Unit::DealDamage kills at health <= damage)
    if (!_unkillable || !victim || victim->GetGUID() != _actorGuid || !victim->IsAlive() || damage == 0 ||
        damage < victim->GetHealth())
        return;

    // Refill first: this also covers several swings landing inside one clock step, which a per-step refill misses
    uint32 const maxHealth = victim->GetMaxHealth();
    victim->SetHealth(maxHealth);
    ++_savedHits;

    if (damage < maxHealth)
        return;

    // A single hit that outweighs the whole health bar: the core would still kill from full health, so cut it to
    // max - 1. The cut part is no damage taken any more, so its rage is credited here the way DealDamage's own
    // "rage from damage received" would have (Unit::RewardRage(damage, 0, false) is linear in damage), which keeps the
    // run's total rage from damage taken equal to the unclamped one (to within the 0.1 rage RewardRage truncates per
    // call). The credit sits here, before the core's own credit for the rest, on the same alive path.
    uint32 const cut = damage - (maxHealth - 1);
    damage = maxHealth - 1;
    ++_clampedHits;
    if (attacker != victim && victim->HasActivePowerType(POWER_RAGE))
        victim->RewardRage(cut, 0, false);
}

void DamageTakenRecorder::BeginSwing(Creature* /*dummy*/, Unit* victim)
{
    _swingBracketOpen = true;
    _bracketVictim = victim;
    _swingsAtBegin = _swings.size();
    _ragePre = victim && victim->GetMaxPower(POWER_RAGE) > 0 ? int32(victim->GetPower(POWER_RAGE)) : -1;
}

void DamageTakenRecorder::EndSwing()
{
    if (!_swingBracketOpen)
        return;
    _swingBracketOpen = false;

    // Each swing is one bracket, so at most one event was added; a swing the core dropped (pacified, no line of sight)
    // added none
    if (_swings.size() > _swingsAtBegin && _ragePre >= 0 && _bracketVictim)
    {
        int32 const ragePost = int32(_bracketVictim->GetPower(POWER_RAGE));
        _swings.back().RageGained = ragePost - _ragePre;
    }
    _bracketVictim = nullptr;
}

void DamageTakenRecorder::Reset()
{
    _savedHits = 0;
    _clampedHits = 0;
    _swings.clear();
    _absorbs.clear();
    _open = OpenSwing{};
    _pendingAbsorbs.clear();
    _swingBracketOpen = false;
    _ragePre = -1;
    _swingsAtBegin = 0;
    _bracketVictim = nullptr;
}
