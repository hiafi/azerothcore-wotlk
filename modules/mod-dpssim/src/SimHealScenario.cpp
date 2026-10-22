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

#include "SimHealScenario.h"
#include "AiFactory.h"
#include "Creature.h"
#include "Group.h"
#include "GroupMgr.h"
#include "HealRecorder.h"
#include "Log.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Playerbots.h"
#include "SimHealBossAI.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Timer.h"
#include <algorithm>
#include <cmath>

namespace
{
    // The boss stands this far past the centre of the group, away from the healer: close enough for a healer's DPS
    // spells (it may attack the boss; R5), far enough to read as a separate target
    constexpr float BOSS_DISTANCE_BEYOND_GROUP = 14.0f;

    // The group's centre, in front of the healer (the same 8 yd as the DPS sim's primary dummy)
    constexpr float GROUP_CENTER_DISTANCE = 8.0f;

    // Allies per ring: the inner ring holds this many, the rest stand on the outer ring
    constexpr size_t INNER_RING_CAPACITY = 8;

    // The boss's pool; the AI clamps damage to health - 1 and tops it up, so it is only for display
    constexpr float BOSS_MAX_HEALTH = 100000000.0f;

    // The extra damage a pin hit may carry to beat the 1-point truncation of a damage reduction (see Step()). Its upper
    // bound, and the most a hit can overshoot the pin by
    constexpr uint32 PIN_STUCK_MAX = 16;

    // Health a pinned target is held at: `percent` of its current max health, rounded down
    uint32 PinHealth(uint32 maxHealth, float percent)
    {
        return uint32(uint64(maxHealth) * uint64(percent) / 100);
    }

    // The damage a target's shields will still take from the Sim Pin Hit (arcane): the remaining amount of every
    // school-absorb and mana-shield effect whose school mask covers arcane. A shield for another school never takes
    // part.
    int64 AbsorbRemaining(Unit* target)
    {
        int64 total = 0;
        for (AuraType type : {SPELL_AURA_SCHOOL_ABSORB, SPELL_AURA_MANA_SHIELD})
            for (AuraEffect const* effect : target->GetAuraEffectsByType(type))
                if ((effect->GetMiscValue() & SPELL_SCHOOL_MASK_ARCANE) && effect->GetAmount() > 0)
                    total += effect->GetAmount();
        return total;
    }

    // Position on the ground at (x, y), starting from the height of `base`
    Position GroundAt(Player* healer, Position const& base, float x, float y, float facing)
    {
        float z = base.GetPositionZ();
        healer->UpdateGroundPositionZ(x, y, z);
        return Position(x, y, z, facing);
    }
}

SimHealScenario::~SimHealScenario()
{
    // The group first: it points at its members, and each ally's logout would otherwise run against a group that is
    // already half gone. The boss is despawned like SimTarget's dummy; the allies log out through ~SimActor.
    if (_group)
        _group->Disband(true);

    if (_boss)
        _boss->UnSummon();
}

Creature* SimHealScenario::GetBoss() const
{
    return _boss;
}

std::vector<ObjectGuid> SimHealScenario::GetMemberGuids() const
{
    std::vector<ObjectGuid> guids;
    guids.reserve(_members.size());
    for (Player* member : _members)
        guids.push_back(member->GetGUID());
    return guids;
}

bool SimHealScenario::Create(Player* healer, Setup const& setup)
{
    if (setup.Targets.size() != setup.GroupSize)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimHealScenario::Create() - {} target(s) for a group of {}.",
            setup.Targets.size(), setup.GroupSize);
        return false;
    }

    _specs = setup.Targets;
    _drainPulseMs = setup.DrainPulseMs;
    _pinMaxHealth = setup.PinMaxHealth;

    return CreateBoss(healer) && CreateAllies(healer, setup) && CreateGroup(healer, setup);
}

bool SimHealScenario::CreateBoss(Player* healer)
{
    uint32 const entry = SimHealBoss::EntryForLevel(uint8(healer->GetLevel()));
    Position const center = healer->GetNearPosition(GROUP_CENTER_DISTANCE, 0.0f);
    float const away = healer->GetAbsoluteAngle(center);

    float const x = center.GetPositionX() + BOSS_DISTANCE_BEYOND_GROUP * std::cos(away);
    float const y = center.GetPositionY() + BOSS_DISTANCE_BEYOND_GROUP * std::sin(away);
    // Faces back at the group
    Position const pos = GroundAt(healer, center, x, y, away + float(M_PI));

    TempSummon* boss = healer->GetMap()->SummonCreature(entry, pos);
    if (!boss)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimHealScenario::CreateBoss() - SummonCreature(entry {}) failed - is "
            "the HS0 creature data (900015-900017) imported?", entry);
        return false;
    }

    _boss = boss;
    _boss->SetReactState(REACT_PASSIVE);
    _boss->SetLevel(healer->GetLevel());
    _boss->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, BOSS_MAX_HEALTH);
    _boss->SetStatPctModifier(UNIT_MOD_HEALTH, BASE_PCT, 1.0f);
    _boss->SetStatFlatModifier(UNIT_MOD_HEALTH, TOTAL_VALUE, 0.0f);
    _boss->SetStatPctModifier(UNIT_MOD_HEALTH, TOTAL_PCT, 1.0f);
    _boss->UpdateMaxHealth();
    _boss->SetFullHealth();

    LOG_INFO("server.dpssim", "mod-dpssim: SimHealScenario - boss entry {} level {} at ({:.1f}, {:.1f}), {:.1f} yd "
        "from the healer, maxHealth {}, hostile to the healer: {}.", entry, uint32(_boss->GetLevel()),
        _boss->GetPositionX(), _boss->GetPositionY(), healer->GetExactDist(_boss), _boss->GetMaxHealth(),
        healer->IsValidAttackTarget(_boss) ? "yes" : "NO");
    return true;
}

bool SimHealScenario::CreateAllies(Player* healer, Setup const& setup)
{
    size_t const size = setup.Targets.size();
    for (size_t i = 0; i < size; ++i)
        if (setup.Targets[i].TargetRole == SimHeal::Role::Self)
            _selfIndex = i;

    // The first tank is the main tank: it stands at the centre of the group and is the boss's victim
    size_t mainTankIndex = size;
    for (size_t i = 0; i < size; ++i)
        if (setup.Targets[i].TargetRole == SimHeal::Role::Tank)
        {
            mainTankIndex = i;
            break;
        }

    Position const center = healer->GetNearPosition(GROUP_CENTER_DISTANCE, 0.0f);
    float const away = healer->GetAbsoluteAngle(center);

    // The other allies, in index order, on an inner ring of up to 8 and an outer ring for the rest. Ring radii are a
    // quarter and half of the spread, so every ally is within the spread of every other
    std::vector<size_t> others;
    for (size_t i = 0; i < size; ++i)
        if (i != _selfIndex && i != mainTankIndex)
            others.push_back(i);
    size_t const innerCount = std::min(others.size(), INNER_RING_CAPACITY);
    size_t const outerCount = others.size() - innerCount;

    _members.assign(size, nullptr);
    _members[_selfIndex] = healer;
    _allies.clear();
    size_t slot = 0;
    for (size_t i = 0; i < size; ++i)
    {
        if (i == _selfIndex)
            continue;

        float x = center.GetPositionX();
        float y = center.GetPositionY();
        if (i != mainTankIndex)
        {
            bool const inner = slot < innerCount;
            size_t const ringCount = inner ? innerCount : outerCount;
            size_t const ringSlot = inner ? slot : slot - innerCount;
            float const radius = setup.SpreadYards * (inner ? 0.25f : 0.5f);
            float const angle = away + float(ringSlot) * 2.0f * float(M_PI) / float(ringCount);
            x += radius * std::cos(angle);
            y += radius * std::sin(angle);
            ++slot;
        }

        SimAlly::Config config;
        config.AllyRole = setup.Targets[i].TargetRole;
        config.Race = healer->getRace();
        config.Level = uint8(healer->GetLevel());
        config.Name = Acore::StringFormat("SimAlly{}", i);
        bool const tank = config.AllyRole == SimHeal::Role::Tank;
        config.Talents = tank ? setup.AllyTankTalents : std::string();
        config.BaseMaxHealth = setup.Targets[i].Kind == SimHeal::ModeKind::Pin
            ? setup.PinMaxHealth : (tank ? setup.AllyMaxHealthTank : setup.AllyMaxHealthDps);
        Position const pos = GroundAt(healer, center, x, y, away + float(M_PI));
        config.PositionX = pos.GetPositionX();
        config.PositionY = pos.GetPositionY();
        config.PositionZ = pos.GetPositionZ();
        config.PositionO = pos.GetOrientation();

        auto ally = std::make_unique<SimAlly>();
        if (!ally->Create(config))
            return false;

        _members[i] = ally->GetPlayer();
        _allies.push_back(std::move(ally));
    }

    _mainTank = _members[mainTankIndex];

    // The boss's victim: the main tank, the other tanks in index order when it is dead, then anyone alive
    std::vector<ObjectGuid> victimOrder;
    victimOrder.push_back(_mainTank->GetGUID());
    for (size_t i = 0; i < size; ++i)
        if (_members[i] != _mainTank && setup.Targets[i].TargetRole == SimHeal::Role::Tank)
            victimOrder.push_back(_members[i]->GetGUID());
    for (size_t i = 0; i < size; ++i)
        if (std::find(victimOrder.begin(), victimOrder.end(), _members[i]->GetGUID()) == victimOrder.end())
            victimOrder.push_back(_members[i]->GetGUID());
    SimHealBoss::SetVictimOrder(victimOrder);
    return true;
}

bool SimHealScenario::CreateGroup(Player* healer, Setup const& setup)
{
    // The healer leads (plan R1): a non-bot leader could become the bot's "master"
    _group = new Group();
    if (!_group->Create(healer))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimHealScenario::CreateGroup() - Group::Create() failed.");
        delete _group;
        _group = nullptr;
        return false;
    }
    sGroupMgr->AddGroup(_group);

    bool const raid = setup.GroupSize > SimHeal::PARTY_SIZE;
    if (raid)
        _group->ConvertToRaid();

    // Join order. A party joins in index order. A raid fills its first subgroup first (the healer, the main tank and 3
    // DPS), so those join before the rest, which follow in index order: AddMember() puts each in the first subgroup
    // with room.
    std::vector<size_t> order;
    auto const add = [&](size_t i)
    {
        if (i != _selfIndex && std::find(order.begin(), order.end(), i) == order.end())
            order.push_back(i);
    };
    if (raid)
    {
        for (size_t i = 0; i < _members.size(); ++i)
            if (_members[i] == _mainTank)
                add(i);

        size_t dps = 0;
        for (size_t i = 0; i < _members.size() && dps < 3; ++i)
            if (_specs[i].TargetRole == SimHeal::Role::Dps)
            {
                add(i);
                ++dps;
            }
    }
    for (size_t i = 0; i < _members.size(); ++i)
        add(i);

    for (size_t i : order)
        if (!_group->AddMember(_members[i]))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimHealScenario::CreateGroup() - Group::AddMember() failed for "
                "target {}.", i);
            return false;
        }

    _targetInfo.assign(_members.size(), SimHeal::TargetInfo());
    for (size_t i = 0; i < _members.size(); ++i)
    {
        if (_members[i]->GetGroup() != _group)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimHealScenario::CreateGroup() - target {} is not in the group.",
                i);
            return false;
        }

        _targetInfo[i].Spec = _specs[i];
        _targetInfo[i].Subgroup = raid ? _members[i]->GetSubGroup() : 0;
    }

    return true;
}

void SimHealScenario::LogRoles() const
{
    // The role table the plan asks for: IsTank(bySpec) must be true for the tanks and false for everyone else, or
    // the bot (and the Holy Paladin values) would misread the group
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* member = _members[i];
        LOG_INFO("server.dpssim", "mod-dpssim: group member {} - {} {} (class {}), subgroup {}, spec tab {}, "
            "IsTank(bySpec) {}, IsTank {}, IsHeal(bySpec) {}, IsDps(bySpec) {}.", i,
            SimHeal::RoleName(_specs[i].TargetRole),
            SimHeal::ModeText(_specs[i]), uint32(member->getClass()), uint32(_targetInfo[i].Subgroup),
            uint32(AiFactory::GetPlayerSpecTab(member)), PlayerbotAI::IsTank(member, true) ? "true" : "false",
            PlayerbotAI::IsTank(member, false) ? "true" : "false", PlayerbotAI::IsHeal(member, true) ? "true" : "false",
            PlayerbotAI::IsDps(member, true) ? "true" : "false");
    }
}

void SimHealScenario::PinHealerMaxHealth()
{
    if (_specs[_selfIndex].Kind == SimHeal::ModeKind::Pin)
        SimAlly::PinBaseMaxHealth(_members[_selfIndex], _pinMaxHealth);
}

void SimHealScenario::ResetAllies()
{
    // Non-passive auras plus timed passive ones (a delay holder), as ResetForNextIteration() does for the healer
    auto const removeNonPassive = [](AuraApplication const* aurApp)
    {
        Aura const* aura = aurApp->GetBase();
        SpellInfo const* info = aura->GetSpellInfo();
        return !info || !info->IsPassive() || !aura->IsPermanent();
    };

    for (std::unique_ptr<SimAlly> const& ally : _allies)
    {
        Player* player = ally->GetPlayer();

        // A dead ally that stayed dead for 6 minutes released its spirit (the run length guard keeps that from
        // happening; this is the net under it): back to its slot before anything else
        ally->ReturnToSlot();

        if (!player->IsAlive())
        {
            // false: no ghost/aura rows - the ally has no characters row (SimActor.cpp, zero SQL)
            if (player->GetCorpse())
                player->SpawnCorpseBones(false);
            player->ResurrectPlayer(1.0f);
        }

        player->InterruptNonMeleeSpells(false);
        player->RemoveAppliedAuras(removeNonPassive);
        player->SetFullHealth();
    }
}

void SimHealScenario::RecordDeath(size_t index)
{
    if (index >= _wasAlive.size() || !_wasAlive[index])
        return;

    _deaths.push_back({getMSTime(), uint8(index)});
    _wasAlive[index] = false;
}

void SimHealScenario::EndCombat()
{
    _boss->CombatStop(true);
    for (Player* member : _members)
        member->CombatStop(true);
}

void SimHealScenario::Pull()
{
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* member = _members[i];
        if (!member->IsAlive())
            continue;

        _targetInfo[i].MaxHealth = member->GetMaxHealth();
        if (_specs[i].Kind == SimHeal::ModeKind::Pin)
            member->SetHealth(PinHealth(member->GetMaxHealth(), _specs[i].Value));
        else
            member->SetFullHealth();
    }

    std::vector<Player*> engaged;
    for (Player* member : _members)
        engaged.push_back(member);
    uint32 const missing = SimHealBoss::Engage(_boss, engaged);

    _healthSamples.clear();
    _deaths.clear();
    _resurrections.clear();
    _wasAlive.assign(_members.size(), true);
    _targetPinHits.assign(_members.size(), 0);
    _targetPinRaises.assign(_members.size(), 0);
    _pinStuck.assign(_members.size(), 0);
    _pinHits = _pinRaises = _drainHits = _castFailures = 0;
    _nextDrainMs = _drainPulseMs;
    SampleHealth();
    _nextSampleMs = SimHeal::HEALTH_SAMPLE_INTERVAL_MS;

    Unit* victim = _boss->GetVictim();
    LOG_INFO("server.dpssim", "mod-dpssim: iteration pull - boss engaged {} of {} members, victim {}, boss in combat "
        "with the healer: {}.", _members.size() - missing, _members.size(),
        victim ? victim->GetName() : std::string("nobody"), _members[_selfIndex]->IsInCombatWith(_boss) ? "yes" : "NO");

    if (!_loggedPull)
    {
        _loggedPull = true;
        for (size_t i = 0; i < _members.size(); ++i)
            LOG_INFO("server.dpssim", "mod-dpssim:   target {} - {} {}, subgroup {}, health {}/{}, {:.1f} yd from the "
                "healer.", i, SimHeal::RoleName(_specs[i].TargetRole), SimHeal::ModeText(_specs[i]),
                uint32(_targetInfo[i].Subgroup), _members[i]->GetHealth(), _members[i]->GetMaxHealth(),
                _members[_selfIndex]->GetExactDist(_members[i]));
    }
}

uint32 SimHealScenario::DrainAmount(SimHeal::TargetSpec const& spec, Player* target) const
{
    if (spec.Percent)
        return std::max(1u, uint32(float(target->GetMaxHealth()) * spec.Value / 100.0f + 0.5f));

    return std::max(1u, uint32(spec.Value + 0.5f));
}

bool SimHealScenario::CastHit(uint32 spellId, size_t targetIndex, int32 amount)
{
    Player* target = _members[targetIndex];

    // The recorder learns the request, so a damage event can tell mitigation from the hit the driver asked for
    if (_recorder)
        _recorder->BeginHit(uint8(targetIndex), uint32(std::max(amount, 0)));

    // HS0 report section 4: the full triggered mask minus DISALLOW_PROC_EVENTS, so the victim's taken-damage procs
    // (Prayer of Mending, Earth Shield, ...) fire as they would from a real boss cast
    SpellCastResult const result = _boss->CastCustomSpell(spellId, SPELLVALUE_BASE_POINT0, amount, target,
        TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_DISALLOW_PROC_EVENTS));

    if (_recorder)
        _recorder->EndHit();

    if (result == SPELL_CAST_OK)
        return true;

    if (++_castFailures <= 5)
        LOG_WARN("server.dpssim", "mod-dpssim: the boss's cast of spell {} on '{}' for {} failed: SpellCastResult {}.",
            spellId, target->GetName(), amount, uint32(result));
    return false;
}

void SimHealScenario::UpdateLife()
{
    uint32 const now = getMSTime();
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* member = _members[i];

        // A resurrection the bot cast waits for the target to accept it; the allies have no client to answer. Taken as
        // accepted, coming back at half health.
        if (!member->IsAlive() && member->isResurrectRequested())
        {
            member->clearResurrectRequestData();
            member->ResurrectPlayer(0.5f);
        }

        bool const alive = member->IsAlive();
        if (_wasAlive[i] && !alive)
            _deaths.push_back({now, uint8(i)});
        else if (!_wasAlive[i] && alive)
            _resurrections.push_back({now, uint8(i)});
        _wasAlive[i] = alive;
    }
}

void SimHealScenario::SampleHealth()
{
    uint32 const now = getMSTime();
    for (size_t i = 0; i < _members.size(); ++i)
        _healthSamples.push_back({now, uint8(i), _members[i]->IsAlive() ? _members[i]->GetHealth() : 0,
            _members[i]->GetMaxHealth()});
}

void SimHealScenario::Step(uint32 elapsedMs)
{
    UpdateLife();

    // Anyone out of combat with the boss (a resurrected ally; combat ending for any reason) is engaged again, so every
    // target stays in combat and unable to regenerate for the whole iteration (plan R3)
    std::vector<Player*> outOfCombat;
    for (Player* member : _members)
        if (member->IsAlive() && !member->IsInCombatWith(_boss))
            outOfCombat.push_back(member);
    if (!outOfCombat.empty())
        SimHealBoss::Engage(_boss, outOfCombat);

    // Drain: every DrainPulseMs, the Sim Damage Pulse on every living draining target. A step longer than the pulse
    // interval delivers every pulse that fell due in it.
    while (elapsedMs >= _nextDrainMs)
    {
        _nextDrainMs += _drainPulseMs;
        for (size_t i = 0; i < _members.size(); ++i)
        {
            Player* member = _members[i];
            if (_specs[i].Kind != SimHeal::ModeKind::Drain || !member->IsAlive())
                continue;

            if (CastHit(SimHeal::SPELL_DAMAGE_PULSE, i, int32(DrainAmount(_specs[i], member))))
                ++_drainHits;
        }
    }

    // Pin: every step, each living pinned target above its pin, or with a shield still on it, takes the Sim Pin Hit for
    // the distance to the pin plus the shields it has, so the hit uses every shield up (ruling D2) and lands the target
    // on the pin. Damage reduction or resilience can leave it above the pin, and the next step hits again; an
    // overestimate that leaves it below the pin is lifted back with a raw SetHealth, which no recorder sees (counted in
    // _pinRaises).
    for (size_t i = 0; i < _members.size(); ++i)
    {
        Player* member = _members[i];
        if (_specs[i].Kind != SimHeal::ModeKind::Pin || !member->IsAlive())
            continue;

        uint32 const pin = PinHealth(member->GetMaxHealth(), _specs[i].Value);
        uint32 const excess = member->GetHealth() > pin ? member->GetHealth() - pin : 0;
        int64 const shields = AbsorbRemaining(member);
        if (excess == 0 && shields <= 0)
        {
            // At (or below) the pin with nothing to consume: nothing to do, and nothing left to be stuck on
            _pinStuck[i] = 0;
            continue;
        }

        // The request is the distance to the pin plus the shields, plus up to PIN_STUCK_MAX more points while hits make
        // no progress: a 3% damage reduction truncates a 1-point hit to 0 and would leave the target one point above
        // its pin for ever. The extra is bounded three ways (the clamp, the cap below, and half the pin) so it can only
        // overshoot into a small SetHealth raise, never into a death, whatever the target does meanwhile (an immune
        // target that cannot be hit builds the counter up to the clamp and stops there). A hit that comes up short by
        // the reduction is simply repeated by the next step. (The share that got through is not learned from the
        // health change: a taken-damage proc such as Prayer of Mending heals the target inside the same cast.)
        uint32 const stuck = std::min({_pinStuck[i], PIN_STUCK_MAX, pin / 2});
        int64 const cap = std::min<int64>(int64(excess) + shields + PIN_STUCK_MAX, INT32_MAX);
        int32 const amount = int32(std::min<int64>(int64(excess) + shields + stuck, cap));
        uint32 const before = member->GetHealth();
        if (!CastHit(SimHeal::SPELL_PIN_HIT, i, amount))
            continue;

        ++_pinHits;
        ++_targetPinHits[i];

        // Progress: health went down, or a shield took part of the hit. Only a hit that moved neither counts as stuck
        uint32 const delivered = member->IsAlive() && before > member->GetHealth() ? before - member->GetHealth() : 0;
        bool const progress = delivered > 0 || !member->IsAlive() || AbsorbRemaining(member) < shields;
        _pinStuck[i] = progress ? 0 : std::min(_pinStuck[i] + 1, PIN_STUCK_MAX);

        if (member->IsAlive() && member->GetHealth() < pin)
        {
            member->SetHealth(pin);
            ++_pinRaises;
            ++_targetPinRaises[i];
        }
    }

    UpdateLife();

    while (elapsedMs >= _nextSampleMs)
    {
        SampleHealth();
        _nextSampleMs += SimHeal::HEALTH_SAMPLE_INTERVAL_MS;
    }
}
