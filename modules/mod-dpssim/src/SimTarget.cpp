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

#include "SimTarget.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "SharedDefines.h"
#include "SimDummyAI.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>

SimTarget::~SimTarget()
{
    // M1 scope: same reasoning as SimActor's destructor - the process exits right after the sim
    // run (see DpsSimWorldScript::OnDpsSimRun()), so despawning here is best-effort tidiness
    // rather than load-bearing. UnSummon() does the right thing (removes from map, schedules its
    // own deletion) if this ever runs while the map is still ticking - e.g. a future milestone
    // that runs multiple sim iterations in one process.
    if (_summon)
        _summon->UnSummon();
}

char const* SimTarget::RankName(Rank rank)
{
    return rank == Rank::Elite ? "elite" : "boss";
}

uint32 SimTarget::EntryForLevel(uint8 level, Rank rank)
{
    bool const elite = rank == Rank::Elite;
    uint32 const entry60 = elite ? DUMMY_ENTRY_ELITE_LEVEL_60 : DUMMY_ENTRY_LEVEL_60;
    uint32 const entry70 = elite ? DUMMY_ENTRY_ELITE_LEVEL_70 : DUMMY_ENTRY_LEVEL_70;
    uint32 const entry80 = elite ? DUMMY_ENTRY_ELITE_LEVEL_80 : DUMMY_ENTRY_LEVEL_80;

    if (level == 60)
        return entry60;
    if (level == 70)
        return entry70;
    if (level == 80)
        return entry80;

    uint32 const fallback = level < 60 ? entry60 : (level < 70 ? entry70 : entry80);
    LOG_WARN("server.dpssim", "mod-dpssim: SimTarget::EntryForLevel() - no dedicated dummy entry for level {} (only 60/70/80 exist) - falling back to entry {}.",
        level, fallback);
    return fallback;
}

bool SimTarget::Create(Map* map, Position const& pos, Config const& config)
{
    uint32 const entry = EntryForLevel(config.Level, config.TargetRank);

    TempSummon* summon = map->SummonCreature(entry, pos);
    if (!summon)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimTarget::Create() - SummonCreature(entry {}) failed - check that base creature_template data is present in this DB.", entry);
        return false;
    }

    _summon = summon;

    // Passive: never aggros, never retaliates, never evades chasing the actor - a target dummy is
    // meant to stand still and absorb damage, not fight back (Phase 1 has no defensive/threat
    // testing yet - see the design doc's section 5.3).
    _summon->SetReactState(REACT_PASSIVE);

    _summon->SetLevel(config.Level);

    // Armor and max health go through the stat modifiers (and the Update* recalculation), not the raw fields: any later
    // recalculation (e.g. an armor-reducing aura such as Thrash's, or a level change) rebuilds the field from the
    // UNIT_MOD_ARMOR / UNIT_MOD_HEALTH modifiers and would otherwise restore the template's values for the rest of the
    // batch. The pct modifiers are pinned to 1 and the total flat to 0 so the result is exactly the configured value;
    // auras applied later still scale it as they do for any creature.
    _summon->SetStatFlatModifier(UNIT_MOD_ARMOR, BASE_VALUE, float(config.Armor));
    _summon->SetStatPctModifier(UNIT_MOD_ARMOR, BASE_PCT, 1.0f);
    _summon->SetStatFlatModifier(UNIT_MOD_ARMOR, TOTAL_VALUE, 0.0f);
    _summon->SetStatPctModifier(UNIT_MOD_ARMOR, TOTAL_PCT, 1.0f);
    _summon->UpdateArmor();

    _summon->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, float(config.MaxHealth));
    _summon->SetStatPctModifier(UNIT_MOD_HEALTH, BASE_PCT, 1.0f);
    _summon->SetStatFlatModifier(UNIT_MOD_HEALTH, TOTAL_VALUE, 0.0f);
    _summon->SetStatPctModifier(UNIT_MOD_HEALTH, TOTAL_PCT, 1.0f);
    _summon->UpdateMaxHealth();
    _summon->SetFullHealth();
    SimDummyAI::SetHealthDrain(config.HealthDrain);

    LOG_INFO("server.dpssim", "mod-dpssim: SimTarget created - entry {}, level {}, armor {} (configured {}), maxHealth {}.",
        entry, config.Level, _summon->GetArmor(), config.Armor, _summon->GetMaxHealth());
    return true;
}

Creature* SimTarget::GetCreature() const
{
    return _summon;
}

bool SimTargetGroup::Create(Player* actor, uint32 count, float spreadYards, SimTarget::Config const& config,
    Layout layout)
{
    count = std::max(count, 1u);
    Map* map = actor->GetMap();

    std::vector<Position> positions;
    if (layout == Layout::Tank)
    {
        // Index 0 dead ahead; the others alternate +1, -1, +2, -2 ... steps off the facing, spread over the half arc
        float const maxAngle = TANK_PACK_HALF_ARC_DEGREES * float(M_PI) / 180.0f;
        uint32 const perSide = (count - 1 + 1) / 2;
        float const step = perSide > 0 ? maxAngle / float(perSide) : 0.0f;
        for (uint32 k = 0; k < count; ++k)
        {
            float const offset = k == 0 ? 0.0f : float((k + 1) / 2) * step * (k % 2 == 1 ? 1.0f : -1.0f);
            float const distance = count == 1 ? TANK_BOSS_YARDS : TANK_PACK_YARDS;
            Position const ahead = actor->GetNearPosition(distance, offset);
            float z = ahead.GetPositionZ();
            actor->UpdateGroundPositionZ(ahead.GetPositionX(), ahead.GetPositionY(), z);
            // Facing the actor
            float const facing = std::atan2(actor->GetPositionY() - ahead.GetPositionY(),
                actor->GetPositionX() - ahead.GetPositionX());
            positions.emplace_back(ahead.GetPositionX(), ahead.GetPositionY(), z, facing);
        }
    }
    else
    {
        // The primary, exactly where the single dummy has always gone
        Position const primaryPos = actor->GetNearPosition(8.0f, 0.0f);
        // Direction from the actor to the primary: ring slot 0 sits directly behind the primary
        float const away = actor->GetAbsoluteAngle(primaryPos);

        positions.push_back(primaryPos);
        for (uint32 k = 0; k + 1 < count; ++k)
        {
            float const angle = away + float(k) * 2.0f * float(M_PI) / float(count - 1);
            float const x = primaryPos.GetPositionX() + spreadYards * std::cos(angle);
            float const y = primaryPos.GetPositionY() + spreadYards * std::sin(angle);
            float z = primaryPos.GetPositionZ();
            actor->UpdateGroundPositionZ(x, y, z);
            positions.emplace_back(x, y, z, primaryPos.GetOrientation());
        }
    }

    _targets.clear();
    for (Position const& pos : positions)
    {
        auto target = std::make_unique<SimTarget>();
        if (!target->Create(map, pos, config))
            return false;

        _targets.push_back(std::move(target));
    }

    std::string list;
    for (size_t i = 0; i < _targets.size(); ++i)
    {
        Creature const* creature = _targets[i]->GetCreature();
        list += Acore::StringFormat("{}#{} {} at {:.1f} yd", list.empty() ? "" : ", ", i,
            creature->GetGUID().ToString(), actor->GetExactDist(creature));
    }
    LOG_INFO("server.dpssim", "mod-dpssim: {} target dummies (entry {}, {}, {}): {}.", _targets.size(),
        _targets.front()->GetCreature()->GetEntry(), SimTarget::RankName(config.TargetRank),
        layout == Layout::Tank ? std::string("tank layout") : Acore::StringFormat("spread {:.1f} yd", spreadYards),
        list);
    return true;
}

std::vector<Creature*> SimTargetGroup::GetCreatures() const
{
    std::vector<Creature*> creatures;
    creatures.reserve(_targets.size());
    for (auto const& target : _targets)
        creatures.push_back(target->GetCreature());
    return creatures;
}

Creature* SimTargetGroup::GetPrimary() const
{
    return _targets.empty() ? nullptr : _targets.front()->GetCreature();
}

std::vector<ObjectGuid> SimTargetGroup::GetGuids() const
{
    std::vector<ObjectGuid> guids;
    guids.reserve(_targets.size());
    for (auto const& target : _targets)
        guids.push_back(target->GetCreature()->GetGUID());
    return guids;
}
