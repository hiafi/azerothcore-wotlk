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

#ifndef MODULE_DPSSIM_SIMHEALSCENARIO_H
#define MODULE_DPSSIM_SIMHEALSCENARIO_H

#include "Define.h"
#include "ObjectGuid.h"
#include "SimAlly.h"
#include "SimHeal.h"
#include <memory>
#include <string>
#include <vector>

class Creature;
class Group;
class Player;
class TempSummon;
class Unit;

// Everything around the healer in a healing-sim run (plan .agents/plans/healing-sim/healing-sim.PLAN.md, sections 1-2
// and
// HS1 handoff): the group of headless allies, the boss that damages it, and the damage drivers.
//
//  - Group: a real in-memory Group with the healer as leader (plan R1), so the bot's PartyMemberToHeal sees every
//  member.
//    A party is the healer and 4 allies; raid10/raid20 are raids whose first subgroup is the healer, the main tank and
//    3 DPS. The healer is one of the targets: its index is the `self` slot of HealTargets, and the other slots are
//    SimAlly players in index order.
//  - Boss: one "Sim Raid Boss" (SimHealBossAI.cpp) standing past the group. At each pull it engages the healer and
//  every
//    ally and keeps the first tank as its victim.
//  - Drivers, run from the sim step (never from inside a hook callback, HS0 report section 4): the drain driver casts
//  the
//    Sim Damage Pulse on every living draining target each DrainPulseMs; the pin driver casts the Sim Pin Hit on every
//    pinned target above its pin, with exactly enough damage to bring it to the pin through its shields.
//  - Bookkeeping: health samples, deaths and resurrections, and the driver counters.
class SimHealScenario
{
public:
    struct Setup
    {
        uint32 GroupSize = SimHeal::PARTY_SIZE;
        // One per group member in index order, the self slot included
        std::vector<SimHeal::TargetSpec> Targets;
        uint32 AllyMaxHealthTank = 9000;
        uint32 AllyMaxHealthDps = 5000;
        // Max health of every pinned target (profile PinMaxHealth); AllyMaxHealth.* then only applies to drain targets
        uint32 PinMaxHealth = 30000;
        std::string AllyTankTalents;
        float SpreadYards = 10.0f;
        uint32 DrainPulseMs = 1000;
    };

    ~SimHealScenario();

    // Spawns the boss and the allies around `healer` (on its map), builds the group and logs the roles table. False
    // (logging why) on failure; the half-built scenario is torn down by the destructor.
    bool Create(Player* healer, Setup const& setup);

    [[nodiscard]] Creature* GetBoss() const;
    // The group in target index order, the healer in its self slot
    [[nodiscard]] std::vector<Player*> const& GetMembers() const { return _members; }
    [[nodiscard]] std::vector<ObjectGuid> GetMemberGuids() const;
    [[nodiscard]] Player* GetMainTank() const { return _mainTank; }
    [[nodiscard]] size_t GetSelfIndex() const { return _selfIndex; }

    // Pins the healer's own max health when its slot is a pinned one (after the bot spent its talents)
    void PinHealerMaxHealth();

    // Between iterations: revives the dead allies, strips every non-passive aura and fills health. The healer is reset
    // by the caller, like the DPS sim's actor.
    void ResetAllies();

    // Ends combat between the boss and the whole group, before the pre-pull buff phase (buffing allies that are in
    // combat
    // would pull the healer into combat and cut the phase short)
    void EndCombat();

    // The pull, after the buff phase: records each target's max health, sets pinned targets to their pin and drain
    // targets
    // to full health, engages the healer and every ally with the boss, and zeroes the per-iteration counters and logs
    void Pull();

    // One sim step, `elapsedMs` into the iteration: accepts resurrections, re-engages anyone out of combat with the
    // boss, runs the drain pulse and the pin driver, records deaths and resurrections, samples health
    void Step(uint32 elapsedMs);

    // ---- Per-iteration results ----
    [[nodiscard]] std::vector<SimHeal::TargetInfo> const& GetTargetInfo() const { return _targetInfo; }
    [[nodiscard]] std::vector<SimHeal::HealthSample> const& GetHealthSamples() const { return _healthSamples; }
    [[nodiscard]] std::vector<SimHeal::LifeEvent> const& GetDeaths() const { return _deaths; }
    [[nodiscard]] std::vector<SimHeal::LifeEvent> const& GetResurrections() const { return _resurrections; }
    // Pin Hits cast (all targets), raw SetHealth raises after a hit left a target below its pin, drain pulses cast
    // (all targets), and spell casts that did not return SPELL_CAST_OK
    [[nodiscard]] uint32 GetPinHits() const { return _pinHits; }
    [[nodiscard]] uint32 GetPinRaises() const { return _pinRaises; }
    [[nodiscard]] uint32 GetDrainHits() const { return _drainHits; }
    [[nodiscard]] uint32 GetCastFailures() const { return _castFailures; }
    // Per target: Pin Hits received and raw raises
    [[nodiscard]] std::vector<uint32> const& GetTargetPinHits() const { return _targetPinHits; }
    [[nodiscard]] std::vector<uint32> const& GetTargetPinRaises() const { return _targetPinRaises; }

private:
    bool CreateBoss(Player* healer);
    bool CreateAllies(Player* healer, Setup const& setup);
    bool CreateGroup(Player* healer, Setup const& setup);
    void LogRoles() const;

    // The drivers' shared cast: the boss casts `spellId` at `target` for `amount`, as HS0 section 4 prescribes
    void CastHit(uint32 spellId, Player* target, int32 amount);
    void UpdateLife();
    void SampleHealth();
    [[nodiscard]] uint32 DrainAmount(SimHeal::TargetSpec const& spec, Player* target) const;

    TempSummon* _boss = nullptr;
    Group* _group = nullptr;
    std::vector<std::unique_ptr<SimAlly>> _allies;
    std::vector<Player*> _members;
    std::vector<SimHeal::TargetSpec> _specs;
    Player* _mainTank = nullptr;
    size_t _selfIndex = 0;
    uint32 _drainPulseMs = 1000;
    uint32 _pinMaxHealth = 30000;

    // Per iteration
    std::vector<SimHeal::TargetInfo> _targetInfo;
    std::vector<SimHeal::HealthSample> _healthSamples;
    std::vector<SimHeal::LifeEvent> _deaths;
    std::vector<SimHeal::LifeEvent> _resurrections;
    std::vector<bool> _wasAlive;
    std::vector<uint32> _targetPinHits;
    std::vector<uint32> _targetPinRaises;
    uint32 _nextDrainMs = 0;
    uint32 _nextSampleMs = 0;
    uint32 _pinHits = 0;
    uint32 _pinRaises = 0;
    uint32 _drainHits = 0;
    uint32 _castFailures = 0;
    bool _loggedPull = false;
    // Per target: the steps in a row a pin hit did not move it
    std::vector<uint32> _pinStuck;
};

#endif
