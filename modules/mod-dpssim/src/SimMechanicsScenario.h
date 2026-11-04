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

#ifndef MODULE_DPSSIM_SIMMECHANICSSCENARIO_H
#define MODULE_DPSSIM_SIMMECHANICSSCENARIO_H

#include "Define.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "SimMechanics.h"
#include "SimTankDummyAI.h"
#include "SimTarget.h"
#include <map>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

class CastRecorder;
class Creature;
class DamageTakenRecorder;
class EventRecorder;
class Group;
class Map;
class Player;
class SimActor;
class SimBot;

// Everything around the group in a mechanics-sim run (STAGE-M4-HANDOFF section 3.4; decision 7.3: all real bots):
//
//  - Members: one SimActor + SimBot per member, every one a real PlayerbotAI (heal mode's allies are headless; here
//    every body has to move for a spread or a soak). Each is created from its own profile (SimMechanics::MemberSpec),
//    in its role's slot: the tanks first, then the healers, then the DPS.
//  - Place: the open world (STAGE-M4-0-REPORT answer 8, option B: the module's gate installs the strategy for a
//    group that holds a scope player of a live encounter that wants bots), at the start of `AnchorRace` (Orc by
//    default: the Human start has an attackable Wild Turkey that keeps the AoE gates closed). Every member is moved to
//    that map, whatever its race starts on, and every member is Horde (DpsSim.cpp picks the races) so they can heal
//    and buff each other. The boss stand-in stands 10 yd ahead of the anchor, facing it; the first tank 3 yd in front
//    of the boss, the others on an arc around the boss on the anchor side (DPS 12 yd, healers 18 yd out).
//  - Group: a real in-memory Group, the first member (a tank) leading, a raid above 5. No member is a real player, so
//    PlayerbotAI::FindNewMaster() finds no master and no bot is told to follow another; the follow-type strategies
//    are removed anyway (STAGE-M4-0-REPORT answer 7), and SimBot::ResolveGroupMaster() is never called.
//  - Boss: the DPS sim's boss dummy (SimTarget, 900004-900006) at the run's target level and the actor's profile
//    armor. With BossSwings it runs the tank sim's AI (SimTankDummyAI) and swings at the first tank, so the tank has
//    something to tank and the healer something to heal; the tank is unkillable (DamageTakenRecorder, as the tank
//    sim's dps scenario), so a healer's failure shows as `tankSaves`, not as a wiped run. It is the drills' owner and
//    their selected creature (SimMech::StartProgram).
//  - Recorders: per member an EventRecorder (damage to the boss, the member's pet included) and a CastRecorder; the
//    failures come from the module's global failure sink (SimMech::SetSink), counted per member by type and
//    "<Kind>/<tag>", group failures (MissedSoak) by key.
class SimMechanicsScenario
{
public:
    struct Setup
    {
        std::vector<SimMechanics::MemberSpec> Members;
        uint8 Level = 60;
        // The race whose start position (with a Warrior) anchors the fight
        uint8 AnchorRace = 2;
        SimTarget::Config BossConfig;
        bool BossSwings = true;
        SimTankDummy::Settings BossSettings;
    };

    // The strategies RemoveStrategies() takes off every member
    static std::vector<std::string> const& StrippedStrategyNames();

    SimMechanicsScenario();
    ~SimMechanicsScenario();
    SimMechanicsScenario(SimMechanicsScenario const&) = delete;
    SimMechanicsScenario& operator=(SimMechanicsScenario const&) = delete;

    // Builds the members, the group, the boss, the recorders and the bots. False (logging why) on failure; the
    // half-built scenario is torn down by the destructor. Registers this scenario as the failure sink's target.
    bool Create(Setup const& setup);

    [[nodiscard]] size_t Size() const { return _members.size(); }
    [[nodiscard]] Player* GetPlayer(size_t index) const;
    [[nodiscard]] SimBot& GetBot(size_t index) const;
    [[nodiscard]] EventRecorder* GetRecorder(size_t index) const;
    [[nodiscard]] CastRecorder* GetCastRecorder(size_t index) const;
    [[nodiscard]] Position const& GetStart(size_t index) const;
    [[nodiscard]] SimMechanics::MemberSpec const& GetSpec(size_t index) const;
    [[nodiscard]] std::vector<std::string> const& GetStripped(size_t index) const;
    // The member under test (DpsSim.Profile), the program's scope player
    [[nodiscard]] size_t GetActorIndex() const { return _actorIndex; }
    // The first tank, the boss's victim; Size() when the group has no tank (then the boss never swings)
    [[nodiscard]] size_t GetTankIndex() const { return _tankIndex; }
    [[nodiscard]] Creature* GetBoss() const;
    [[nodiscard]] std::vector<Creature*> const& GetBossList() const { return _bossList; }
    [[nodiscard]] Map* GetMap() const;
    [[nodiscard]] bool BossSwings() const { return _bossSwings; }
    [[nodiscard]] SimTankDummy::Settings const& GetBossSettings() const { return _bossSettings; }
    [[nodiscard]] DamageTakenRecorder* GetTankRecorder() const { return _tankRecorder; }
    [[nodiscard]] Position const& GetAnchor() const { return _anchor; }
    [[nodiscard]] uint32 GetAnchorMapId() const { return _anchorMapId; }

    // Logs every member's slot, class, spec tab and IsTank/IsHeal/IsDps (after the bots spent their talents)
    void LogRoles() const;

    // ---- Per iteration ----
    // Clears the failure tallies, deaths and movement, and starts counting failures stamped at or after
    // `measuredStartMs` (the sim clock of the first measured ms)
    void BeginIteration(uint32 measuredStartMs);
    // Stops counting failures (the program is stopped after this)
    void EndIteration();
    // After every step: movement since the last step (more than 0.1 yd counts the step as moving) and deaths
    void Step(uint32 elapsedMs, uint32 stepMs);
    // Puts every member back on its start spot (the fight moved them), before the next iteration
    void ReturnToStart();

    [[nodiscard]] SimMechanics::MemberResult const& GetTally(size_t index) const { return _tallies[index]; }
    [[nodiscard]] std::map<std::string, std::map<std::string, uint32>> const& GetGroupFailures() const
    {
        return _groupFailures;
    }
    [[nodiscard]] std::vector<SimMechanics::FailureRecord> const& GetFailureLog() const { return _failureLog; }
    [[nodiscard]] uint32 GetFailuresDropped() const { return _failuresDropped; }
    // Failures the sink saw for a player outside the group, or on another map (should stay 0)
    [[nodiscard]] uint32 GetStrayFailures() const { return _strayFailures; }

private:
    static void OnFailure(SimMech::Failure const& failure);
    void Record(SimMech::Failure const& failure);

    bool CreateMembers(Setup const& setup);
    bool CreateGroup();
    bool CreateBoss(Setup const& setup);
    bool CreateBots(Setup const& setup);

    std::vector<SimMechanics::MemberSpec> _specs;
    std::vector<std::unique_ptr<SimActor>> _members;
    std::vector<std::unique_ptr<SimBot>> _bots;
    std::vector<EventRecorder*> _recorders;
    std::vector<CastRecorder*> _castRecorders;
    std::vector<Position> _starts;
    std::vector<std::vector<std::string>> _stripped;
    std::unordered_map<ObjectGuid, size_t> _indexByGuid;
    size_t _actorIndex = 0;
    size_t _tankIndex = 0;
    uint32 _anchorMapId = 0;
    Position _anchor;
    Position _bossPosition;

    Group* _group = nullptr;
    std::unique_ptr<SimTarget> _boss;
    std::vector<Creature*> _bossList;
    bool _bossSwings = false;
    SimTankDummy::Settings _bossSettings;
    DamageTakenRecorder* _tankRecorder = nullptr;

    // Per iteration
    bool _recording = false;
    uint32 _measuredStartMs = 0;
    std::vector<SimMechanics::MemberResult> _tallies;
    std::vector<Position> _lastPositions;
    std::map<std::string, std::map<std::string, uint32>> _groupFailures;
    std::vector<SimMechanics::FailureRecord> _failureLog;
    uint32 _failuresDropped = 0;
    uint32 _strayFailures = 0;
};

#endif
