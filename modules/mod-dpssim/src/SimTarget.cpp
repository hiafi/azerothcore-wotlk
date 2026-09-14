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
#include "SharedDefines.h"
#include "TemporarySummon.h"

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

uint32 SimTarget::EntryForLevel(uint8 level)
{
    if (level == 60)
        return DUMMY_ENTRY_LEVEL_60;
    if (level == 70)
        return DUMMY_ENTRY_LEVEL_70;
    if (level == 80)
        return DUMMY_ENTRY_LEVEL_80;

    uint32 const fallback = level < 60 ? DUMMY_ENTRY_LEVEL_60 : (level < 70 ? DUMMY_ENTRY_LEVEL_70 : DUMMY_ENTRY_LEVEL_80);
    LOG_WARN("server.dpssim", "mod-dpssim: SimTarget::EntryForLevel() - no dedicated dummy entry for level {} (only 60/70/80 exist) - falling back to entry {}.",
        level, fallback);
    return fallback;
}

bool SimTarget::Create(Map* map, Position const& pos, Config const& config)
{
    uint32 const entry = EntryForLevel(config.Level);

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
    _summon->SetMaxHealth(config.MaxHealth);
    _summon->SetFullHealth();
    _summon->SetResistance(SPELL_SCHOOL_NORMAL, int32(config.Armor));

    LOG_INFO("server.dpssim", "mod-dpssim: SimTarget created - entry {}, level {}, armor {}, maxHealth {}.",
        entry, config.Level, config.Armor, config.MaxHealth);
    return true;
}

Creature* SimTarget::GetCreature() const
{
    return _summon;
}
