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

#ifndef MODULE_DPSSIM_SIMTANKDUMMYAI_H
#define MODULE_DPSSIM_SIMTANKDUMMYAI_H

#include "PassiveAI.h"
#include "SimTank.h"
#include <vector>

class Creature;
class Player;
class Unit;

// Told by the tank dummy AI around each swing it makes: DamageTakenRecorder uses it to measure the actor's rage across
// the swing. A swing is synchronous (AttackerStateUpdate -> CalculateMeleeDamage -> DealMeleeDamage -> RewardRage), so
// everything the swing did to the actor happened between the two calls.
class SimTankSwingObserver
{
public:
    virtual ~SimTankSwingObserver() = default;
    virtual void BeginSwing(Creature* dummy, Unit* victim) = 0;
    virtual void EndSwing() = 0;
};

// The tank sim's dummy brain (plan .agents/plans/tank-sim/tank-sim.PLAN.md, section 1 and risks R1, R2, R5). The dummies
// are the same creature entries the DPS sim uses (900004-900009), whose AI is the passive npc_dpssim_training_dummy; in
// tank mode the batch swaps this AI in on the summoned creatures at run time (Creature::AIM_Initialize), so a DPS or
// heal run never sees it and no creature data changed. The summons live for the whole process and a tank batch is its
// own process, so the swap is never undone: the process ends with the batch.
//
// It does exactly what the passive dummy did (never evades or leashes, never chases, never dies: DamageTaken is the same
// rule) plus one thing: after BeginFight() it keeps the actor as its victim and swings at it every swing interval with
// the core's own melee path. Rooted and passive, so it never moves; it only swings while in melee range of the actor.
// Before BeginFight() (the pre-pull buff phase) and after EndFight() it does nothing at all.
class SimTankDummyAI : public NullCreatureAI
{
public:
    explicit SimTankDummyAI(Creature* creature) : NullCreatureAI(creature) { }

    void Reset() override;
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType damageType, SpellSchoolMask schoolMask) override;
    void UpdateAI(uint32 diff) override;

    // The pull: attacks `victim` (melee) and starts the swing timer, so the first swing lands one swing interval later
    void BeginFight(Unit* victim);

    // The end of an iteration: stops attacking, resets the swing timer and drops the threat
    void EndFight();

    [[nodiscard]] bool IsFighting() const { return _fighting; }

private:
    bool _fighting = false;
    ObjectGuid _victim;
};

namespace SimTankDummy
{
    // What the dummies of a run are told to do
    struct Settings
    {
        SimTank::HitRange Hit;
        uint32 SwingMs = SimTank::DEFAULT_SWING_MS;
        bool Crit = true;
        bool ParryHaste = true;
    };

    // The observer every dummy's swing is reported to (nullptr = none). A process runs one tank batch, so a static is
    // enough, like SimDummyAI's health-drain flag.
    void SetObserver(SimTankSwingObserver* observer);

    // Swaps SimTankDummyAI in on each dummy, sets the swing interval and applies the crit and parry-haste switches (the
    // creature template's flags_extra: CREATURE_FLAG_EXTRA_NO_CRIT / NO_PARRY_HASTEN, read through the template by the
    // core, so the switch is per entry; these entries are only ever the sim's dummies and the process is the batch's own).
    // False (logged) if a swap was refused.
    bool Install(std::vector<Creature*> const& dummies, Settings const& settings);

    // Solves the dummy's base weapon damage so its undebuffed swing lands in `range` before the victim's damage-taken
    // modifiers and armor (plan R2). The attack power stays in the formula, so an attack-power debuff still lowers the
    // hit. Returns what the damage fields are made of. Run at the pull; running it again with the same range is a no-op
    // apart from the same result.
    SimTank::DummyInfo SolveHit(Creature* dummy, SimTank::HitRange const& range, uint32 swingMs);

    // Pull / reset every dummy of the run (they must have been installed). BeginFight solves the damage first (every
    // dummy gets `settings.Hit`: the caller picks the boss or the pack range). The returned vector has one entry per
    // dummy, in order, with the expected crit chance against `actor`.
    std::vector<SimTank::DummyInfo> BeginFight(std::vector<Creature*> const& dummies, Player* actor,
        Settings const& settings);
    void EndFight(std::vector<Creature*> const& dummies);
}

#endif
