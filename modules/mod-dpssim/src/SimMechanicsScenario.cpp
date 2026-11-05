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

#include "SimMechanicsScenario.h"
#include "AiFactory.h"
#include "CastRecorder.h"
#include "Creature.h"
#include "DamageTakenRecorder.h"
#include "EventRecorder.h"
#include "HealRecorder.h"
#include "Group.h"
#include "GroupMgr.h"
#include "Log.h"
#include "Map.h"
#include "MapMgr.h"
#include "MotionMaster.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Playerbots.h"
#include "SimActor.h"
#include "SimBot.h"
#include "StringFormat.h"
#include "Util.h"
#include <algorithm>
#include <cmath>

char const* SimMechanics::RoleName(Role role)
{
    switch (role)
    {
        case Role::Tank:
            return "tank";
        case Role::Healer:
            return "healer";
        default:
            return "dps";
    }
}

bool SimMechanics::ParseRole(std::string const& text, Role& out)
{
    if (StringEqualI(text, "tank"))
        out = Role::Tank;
    else if (StringEqualI(text, "healer") || StringEqualI(text, "heal"))
        out = Role::Healer;
    else if (StringEqualI(text, "dps"))
        out = Role::Dps;
    else
        return false;
    return true;
}

std::string SimMechanics::FailureKey(std::string const& kind, uint32 tag)
{
    return kind + "/" + std::to_string(tag);
}

namespace
{
    // The one scenario the failure sink reports to (a process runs one mechanics batch)
    SimMechanicsScenario* s_active = nullptr;

    // Layout (see the class comment)
    constexpr float BOSS_AHEAD_YARDS = 10.0f;
    constexpr float TANK_FROM_BOSS_YARDS = 3.0f;
    constexpr float DPS_FROM_BOSS_YARDS = 12.0f;
    constexpr float HEALER_FROM_BOSS_YARDS = 18.0f;
    constexpr float ARC_STEP_DEGREES = 20.0f;
    constexpr float ARC_MAX_DEGREES = 300.0f;
    // A step in which a member moved farther than this counts as a moving step
    constexpr float MOVING_STEP_YARDS = 0.1f;

    // The ground under (x, y) near `refZ` on `map`, or `refZ` when the map has no height there
    float GroundZ(Map* map, float x, float y, float refZ)
    {
        float const z = map->GetHeight(PHASEMASK_NORMAL, x, y, refZ + 5.0f, true, 50.0f);
        return z > INVALID_HEIGHT ? z : refZ;
    }

    Position Ahead(Position const& from, float angle, float yards)
    {
        return Position(from.GetPositionX() + yards * std::cos(angle), from.GetPositionY() + yards * std::sin(angle),
            from.GetPositionZ(), 0.0f);
    }
}

std::vector<std::string> const& SimMechanicsScenario::StrippedStrategyNames()
{
    // "follow" walks a bot to its master, "stay" and "guard" hold it on a spot, "passive" stops it fighting: none of
    // them belongs to a bot that must go where its own mechanics brain sends it
    static std::vector<std::string> const names = { "follow", "stay", "guard", "passive" };
    return names;
}

SimMechanicsScenario::SimMechanicsScenario() = default;

SimMechanicsScenario::~SimMechanicsScenario()
{
    if (s_active == this)
    {
        SimMech::SetSink(nullptr);
        s_active = nullptr;
    }
    if (_tankRecorder)
        SimTankDummy::SetObserver(nullptr);

    // The bots before the players they drive, the group before its members log out (SimHealScenario's order)
    _bots.clear();
    if (_group)
        _group->Disband(true);
    _boss.reset();
    _members.clear();
}

Player* SimMechanicsScenario::GetPlayer(size_t index) const
{
    return _members[index]->GetPlayer();
}

SimBot& SimMechanicsScenario::GetBot(size_t index) const
{
    return *_bots[index];
}

EventRecorder* SimMechanicsScenario::GetRecorder(size_t index) const
{
    return _recorders[index];
}

CastRecorder* SimMechanicsScenario::GetCastRecorder(size_t index) const
{
    return _castRecorders[index];
}

HealRecorder* SimMechanicsScenario::GetHealRecorder(size_t index) const
{
    return _healRecorders[index];
}

Position const& SimMechanicsScenario::GetStart(size_t index) const
{
    return _starts[index];
}

SimMechanics::MemberSpec const& SimMechanicsScenario::GetSpec(size_t index) const
{
    return _specs[index];
}

std::vector<std::string> const& SimMechanicsScenario::GetStripped(size_t index) const
{
    return _stripped[index];
}

Creature* SimMechanicsScenario::GetBoss() const
{
    return _boss ? _boss->GetCreature() : nullptr;
}

Map* SimMechanicsScenario::GetMap() const
{
    return _members.empty() ? nullptr : _members.front()->GetPlayer()->GetMap();
}

bool SimMechanicsScenario::Create(Setup const& setup)
{
    if (setup.Members.size() < SimMechanics::MIN_GROUP || setup.Members.size() > SimMechanics::MAX_GROUP)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::Create() - a group of {} member(s) is outside "
            "{}-{}.", setup.Members.size(), SimMechanics::MIN_GROUP, SimMechanics::MAX_GROUP);
        return false;
    }

    _specs = setup.Members;
    _actorIndex = _specs.size();
    _tankIndex = _specs.size();
    for (size_t i = 0; i < _specs.size(); ++i)
    {
        if (_specs[i].UnderTest && _actorIndex == _specs.size())
            _actorIndex = i;
        if (_specs[i].MemberRole == SimMechanics::Role::Tank && _tankIndex == _specs.size())
            _tankIndex = i;
    }
    if (_actorIndex == _specs.size())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::Create() - no member is under test.");
        return false;
    }

    if (!CreateMembers(setup) || !CreateGroup() || !CreateBoss(setup) || !CreateBots(setup))
        return false;

    _tallies.assign(_members.size(), SimMechanics::MemberResult());
    s_active = this;
    SimMech::SetSink(&SimMechanicsScenario::OnFailure);
    return true;
}

bool SimMechanicsScenario::CreateMembers(Setup const& setup)
{
    PlayerInfo const* anchorInfo = sObjectMgr->GetPlayerInfo(setup.AnchorRace, CLASS_WARRIOR);
    if (!anchorInfo)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::Create() - race {} has no Warrior start "
            "position to anchor the fight at.", uint32(setup.AnchorRace));
        return false;
    }

    _anchorMapId = anchorInfo->mapId;
    _anchor.Relocate(anchorInfo->positionX, anchorInfo->positionY, anchorInfo->positionZ, anchorInfo->orientation);
    Map* map = sMapMgr->CreateBaseMap(_anchorMapId);
    if (!map)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::Create() - map {} could not be created.",
            _anchorMapId);
        return false;
    }

    // The boss 10 yd ahead of the anchor, facing back at it
    float const facing = _anchor.GetOrientation();
    float const towardAnchor = Position::NormalizeOrientation(facing + float(M_PI));
    _bossPosition = Ahead(_anchor, facing, BOSS_AHEAD_YARDS);
    _bossPosition.m_positionZ = GroundZ(map, _bossPosition.GetPositionX(), _bossPosition.GetPositionY(),
        _anchor.GetPositionZ());
    _bossPosition.SetOrientation(towardAnchor);

    // Every non-first-tank member on an arc around the boss, centered on the anchor side
    size_t arcCount = 0;
    for (size_t i = 0; i < _specs.size(); ++i)
        if (i != _tankIndex)
            ++arcCount;
    float const stepDeg = arcCount > 1 ?
        std::min(ARC_STEP_DEGREES, ARC_MAX_DEGREES / float(arcCount - 1)) : 0.0f;

    size_t arcSlot = 0;
    for (size_t i = 0; i < _specs.size(); ++i)
    {
        SimMechanics::MemberSpec const& spec = _specs[i];
        Position pos;
        if (i == _tankIndex)
            pos = Ahead(_bossPosition, towardAnchor, TANK_FROM_BOSS_YARDS);
        else
        {
            float const offsetDeg = (float(arcSlot) - float(arcCount - 1) / 2.0f) * stepDeg;
            ++arcSlot;
            float const radius = spec.MemberRole == SimMechanics::Role::Healer ? HEALER_FROM_BOSS_YARDS :
                DPS_FROM_BOSS_YARDS;
            pos = Ahead(_bossPosition, towardAnchor + offsetDeg * float(M_PI) / 180.0f, radius);
        }
        pos.m_positionZ = GroundZ(map, pos.GetPositionX(), pos.GetPositionY(), _bossPosition.GetPositionZ());
        // Facing the boss
        pos.SetOrientation(std::atan2(_bossPosition.GetPositionY() - pos.GetPositionY(),
            _bossPosition.GetPositionX() - pos.GetPositionX()));

        SimActor::Config config;
        config.Name = Acore::StringFormat("SimMech{}", i);
        config.Race = spec.Race;
        config.Class = spec.Class;
        config.Gender = GENDER_MALE;
        config.Level = setup.Level;
        config.SpellPower = spec.SpellPower;
        config.GearItemIds = spec.GearItemIds;
        config.CombatRatings = spec.CombatRatings;
        config.Stats = spec.Stats;
        config.AttackPower = spec.AttackPower;
        config.HasPosition = true;
        config.MapId = _anchorMapId;
        config.PositionX = pos.GetPositionX();
        config.PositionY = pos.GetPositionY();
        config.PositionZ = pos.GetPositionZ();
        config.PositionO = Position::NormalizeOrientation(pos.GetOrientation());

        auto actor = std::make_unique<SimActor>();
        bool const created = actor->Create(config);
        _members.push_back(std::move(actor));
        if (!created)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::Create() - member {} ({}, race {}, class {}) "
                "could not be created.", i, spec.Profile, uint32(spec.Race), uint32(spec.Class));
            return false;
        }

        Player* player = _members.back()->GetPlayer();
        _starts.push_back(player->GetPosition());
        _indexByGuid[player->GetGUID()] = i;
    }

    return true;
}

bool SimMechanicsScenario::CreateGroup()
{
    Player* leader = _members.front()->GetPlayer();
    _group = new Group();
    if (!_group->Create(leader))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::CreateGroup() - Group::Create() failed.");
        delete _group;
        _group = nullptr;
        return false;
    }
    sGroupMgr->AddGroup(_group);

    if (_members.size() > 5)
        _group->ConvertToRaid();

    for (size_t i = 1; i < _members.size(); ++i)
        if (!_group->AddMember(_members[i]->GetPlayer()))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::CreateGroup() - Group::AddMember() failed "
                "for member {}.", i);
            return false;
        }

    return true;
}

bool SimMechanicsScenario::CreateBoss(Setup const& setup)
{
    _boss = std::make_unique<SimTarget>();
    if (!_boss->Create(GetMap(), _bossPosition, setup.BossConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::CreateBoss() - the boss stand-in could not be "
            "spawned.");
        return false;
    }

    Creature* boss = _boss->GetCreature();
    _bossList = { boss };

    // The tank sim's AI on the boss before any bot engages it (RunTankBatch's order), swinging at the first tank
    _bossSwings = setup.BossSwings && _tankIndex < _members.size();
    _bossSettings = setup.BossSettings;
    if (setup.BossSwings && !_bossSwings)
        LOG_WARN("server.dpssim", "mod-dpssim: the mechanics group has no tank - the boss stand-in never swings.");
    if (_bossSwings)
    {
        Player* tank = _members[_tankIndex]->GetPlayer();
        if (!SimTankDummy::Install(_bossList, tank, _bossSettings))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::CreateBoss() - installing the tank AI on the "
                "boss stand-in failed.");
            return false;
        }

        // Unkillable tank (the tank sim's dps scenario): a lethal swing is turned into a refill and counted
        _tankRecorder = new DamageTakenRecorder(tank->GetGUID(), { boss->GetGUID() }, true);
        SimTankDummy::SetObserver(_tankRecorder);
    }

    LOG_INFO("server.dpssim", "mod-dpssim: mechanics boss stand-in - entry {} level {} at map {} ({:.1f}, {:.1f}, "
        "{:.1f}), armor {}, swings at the tank: {}.", boss->GetEntry(), uint32(boss->GetLevel()), _anchorMapId,
        _bossPosition.GetPositionX(), _bossPosition.GetPositionY(), _bossPosition.GetPositionZ(), boss->GetArmor(),
        _bossSwings ? "yes" : "no");
    return true;
}

bool SimMechanicsScenario::CreateBots(Setup const& /*setup*/)
{
    Creature* boss = GetBoss();
    // Every member is a heal target of every recorder (target index = member index)
    std::vector<ObjectGuid> memberGuids;
    for (auto const& member : _members)
        memberGuids.push_back(member->GetPlayer()->GetGUID());
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* player = _members[i]->GetPlayer();
        // Heap-allocated and never deleted, as every recorder (EventRecorder.h)
        _recorders.push_back(new EventRecorder(player->GetGUID(), { boss->GetGUID() }));
        _castRecorders.push_back(new CastRecorder(player->GetGUID(), { boss->GetGUID() }));
        _healRecorders.push_back(new HealRecorder(player->GetGUID(), memberGuids, true));
    }

    // The group exists before the bots, as it does for a live group: strategy resolution sees a grouped bot
    for (size_t i = 0; i < _members.size(); ++i)
    {
        SimMechanics::MemberSpec const& spec = _specs[i];
        auto bot = std::make_unique<SimBot>();
        bool const created = bot->Create(_members[i]->GetPlayer(), _bossList, spec.Talents, spec.Glyphs,
            spec.PetCreatureEntry);
        _bots.push_back(std::move(bot));
        if (!created)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimMechanicsScenario::CreateBots() - SimBot::Create() failed for "
                "member {} ({}).", i, spec.Profile);
            return false;
        }

        _stripped.push_back(_bots.back()->RemoveStrategies(StrippedStrategyNames()));
        std::string removed;
        for (std::string const& name : _stripped.back())
            removed += (removed.empty() ? "" : ", ") + name;
        LOG_INFO("server.dpssim", "mod-dpssim: mechanics member {} ({} {}{}) - strategies {}; removed [{}].", i,
            SimMechanics::RoleName(spec.MemberRole), spec.Profile, spec.UnderTest ? ", under test" : "",
            _bots.back()->DescribeStrategies(), removed);
    }

    return true;
}

void SimMechanicsScenario::LogRoles() const
{
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* member = _members[i]->GetPlayer();
        LOG_INFO("server.dpssim", "mod-dpssim: mechanics member {} - {} {} (race {}, class {}), spec tab {}, "
            "IsTank(bySpec) {}, IsHeal(bySpec) {}, IsDps(bySpec) {}, {:.1f} yd from the boss.", i,
            SimMechanics::RoleName(_specs[i].MemberRole), _specs[i].Profile, uint32(member->getRace()),
            uint32(member->getClass()), uint32(AiFactory::GetPlayerSpecTab(member)),
            PlayerbotAI::IsTank(member, true) ? "true" : "false", PlayerbotAI::IsHeal(member, true) ? "true" : "false",
            PlayerbotAI::IsDps(member, true) ? "true" : "false", member->GetExactDist(GetBoss()));
    }
}

void SimMechanicsScenario::BeginIteration(uint32 measuredStartMs)
{
    _measuredStartMs = measuredStartMs;
    _recording = true;
    _tallies.assign(_members.size(), SimMechanics::MemberResult());
    _groupFailures.clear();
    _failureLog.clear();
    _failuresDropped = 0;
    _strayFailures = 0;
    _lastPositions.clear();
    for (std::unique_ptr<SimActor> const& member : _members)
        _lastPositions.push_back(member->GetPlayer()->GetPosition());
}

void SimMechanicsScenario::EndIteration()
{
    _recording = false;
}

void SimMechanicsScenario::Step(uint32 elapsedMs, uint32 stepMs)
{
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* player = _members[i]->GetPlayer();
        SimMechanics::MemberResult& tally = _tallies[i];
        if (!player->IsAlive())
        {
            if (!tally.Died)
            {
                tally.Died = true;
                tally.DiedAtMs = elapsedMs;
                LOG_WARN("server.dpssim", "mod-dpssim: mechanics member {} ({}) DIED {} ms into the iteration.", i,
                    _specs[i].Profile, elapsedMs);
            }
            continue;
        }

        float const moved = player->GetExactDist(_lastPositions[i]);
        if (moved > MOVING_STEP_YARDS)
        {
            tally.MovingMs += stepMs;
            tally.DistanceYd += moved;
        }
        _lastPositions[i] = player->GetPosition();
    }
}

void SimMechanicsScenario::ReturnToStart()
{
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* player = _members[i]->GetPlayer();
        if (!player->IsAlive() || player->IsBeingTeleported())
            continue;

        Position const& start = _starts[i];
        player->GetMotionMaster()->Clear();
        player->StopMoving();
        if (player->GetExactDist(start) > 0.5f)
        {
            player->NearTeleportTo(start.GetPositionX(), start.GetPositionY(), start.GetPositionZ(),
                start.GetOrientation());
            _bots[i]->HandleTeleportAck();
        }
        else
            player->SetFacingTo(start.GetOrientation());
    }
}

void SimMechanicsScenario::OnFailure(SimMech::Failure const& failure)
{
    if (s_active)
        s_active->Record(failure);
}

void SimMechanicsScenario::Record(SimMech::Failure const& f)
{
    if (!_recording || f.AtMs < _measuredStartMs)
        return;

    int32 member = -1;
    if (!f.Player.IsEmpty())
    {
        auto const it = _indexByGuid.find(f.Player);
        if (it == _indexByGuid.end() || f.MapId != _anchorMapId)
        {
            ++_strayFailures;
            return;
        }
        member = int32(it->second);
    }
    else if (f.MapId != _anchorMapId)
    {
        ++_strayFailures;
        return;
    }

    std::string const key = SimMechanics::FailureKey(f.Kind, f.Tag);
    if (member < 0)
        ++_groupFailures[f.Type][key];
    else
    {
        SimMechanics::MemberResult& tally = _tallies[size_t(member)];
        ++tally.Failures[f.Type][key];
        ++tally.FailureTotal;
        if (f.Type == "Hit")
        {
            ++tally.Hits;
            tally.HitDamage += f.Damage;
        }
    }

    if (_failureLog.size() < SimMechanics::MAX_FAILURE_LOG)
        _failureLog.push_back({ f.AtMs - _measuredStartMs, member, f.Type, f.Kind, f.Tag, f.MechanicId, f.Damage });
    else
        ++_failuresDropped;
}
