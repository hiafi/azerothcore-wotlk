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

#ifndef MODULE_DPSSIM_DAMAGETAKENRECORDER_H
#define MODULE_DPSSIM_DAMAGETAKENRECORDER_H

#include "ObjectGuid.h"
#include "ScriptMgr.h"
#include "SimTank.h"
#include "SimTankDummyAI.h"
#include <vector>

// The tank sim's counterpart of EventRecorder and HealRecorder (plan .agents/plans/tank-sim/tank-sim.PLAN.md, section 4):
// records every swing a dummy makes at the actor. A swing passes four hooks, in this order inside one
// Unit::CalculateMeleeDamage call, and the recorder joins them into one SwingEvent:
//
//  1. ModifyMeleeDamage: the damage after the dummy's damage fields and the actor's damage-taken modifiers (Defensive
//     Stance, talents), before armor. Read only: `damage` is never changed.
//  2. OnBeforeRollMeleeOutcomeAgainst: the chances the core is about to roll, kept as the swing's "expected" side. Read
//     only, nothing in the reference parameters is touched.
//  3. OnAbsorbFinal: a shield that took damage off the actor. Melee absorbs fire BEFORE the outcome hook (the reverse of
//     the spell path HealRecorder follows), so they wait in a pending list until the swing closes.
//  4. OnMeleeOutcomeFinal (the TS0 core hook): the outcome, the block, the absorb and resist and the final damage. This
//     closes the swing.
//
// SimTankDummyAI also brackets the whole swing (SimTankSwingObserver), which is how the actor's rage across the swing is
// measured: rage is rewarded after the outcome hook, in DealMeleeDamage, so only the span of the whole swing sees it.
//
// Anything that is not a dummy hitting the actor is ignored. Same heap-allocation / never-deleted /
// constructed-at-runtime rules as EventRecorder: see its class comment.
class DamageTakenRecorder : public UnitScript, public SimTankSwingObserver
{
public:
    // `dummyGuids` are the dummies in target index order
    DamageTakenRecorder(ObjectGuid actorGuid, std::vector<ObjectGuid> dummyGuids);

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override;
    void OnBeforeRollMeleeOutcomeAgainst(Unit const* attacker, Unit const* victim, WeaponAttackType attType,
        int32& attackerMaxSkillValueForLevel, int32& victimMaxSkillValueForLevel, int32& attackerWeaponSkill,
        int32& victimDefenseSkill, int32& crit_chance, int32& miss_chance, int32& dodge_chance, int32& parry_chance,
        int32& block_chance) override;
    void OnAbsorbFinal(Unit* victim, Unit* attacker, AuraEffect const* absorbAurEff, uint32 absorbed) override;
    void OnMeleeOutcomeFinal(CalcDamageInfo const* damageInfo) override;

    void BeginSwing(Creature* dummy, Unit* victim) override;
    void EndSwing() override;

    // Clears every recorded event, between iterations (see EventRecorder::Reset())
    void Reset();

    [[nodiscard]] std::vector<SimTank::SwingEvent> const& GetSwings() const { return _swings; }
    [[nodiscard]] std::vector<SimTank::SwingAbsorb> const& GetSwingAbsorbs() const { return _absorbs; }

private:
    int8 IndexOfDummy(ObjectGuid guid) const;

    ObjectGuid _actorGuid;
    std::vector<ObjectGuid> _dummyGuids;

    std::vector<SimTank::SwingEvent> _swings;
    std::vector<SimTank::SwingAbsorb> _absorbs;

    // The swing being assembled: set by the first hook, cleared when the outcome hook closes it (or by the next swing's
    // first hook if the core returned early without closing it)
    struct OpenSwing
    {
        bool Active = false;
        uint32 PreArmor = 0;
        float TakenMult = 1.0f;
        bool HaveChances = false;
        uint16 ExpectedMiss = 0;
        uint16 ExpectedDodge = 0;
        uint16 ExpectedParry = 0;
        uint16 ExpectedBlock = 0;
        uint16 ExpectedCrit = 0;
        bool InFrontArc = true;
    };
    OpenSwing _open;

    struct PendingAbsorb
    {
        uint32 SpellId = 0;
        uint32 Amount = 0;
    };
    std::vector<PendingAbsorb> _pendingAbsorbs;

    // BeginSwing()..EndSwing(): the actor's rage before the swing (tenths), -1 when the actor has none, and the index of
    // the first swing event the bracket may add
    bool _swingBracketOpen = false;
    int32 _ragePre = -1;
    size_t _swingsAtBegin = 0;
    Unit* _bracketVictim = nullptr;
};

#endif
