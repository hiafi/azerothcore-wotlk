/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// Custom: Healing Training Dummy (creature_template entry 900011, see
// data/sql/updates/pending_db_world/ for the migration). Keeps itself pinned at 30% of max health
// - set on spawn and re-forced every 1 sec regardless of what happened to it in between - so a
// healer can repeatedly land a heal, read the real amount/overheal off the combat log in the brief
// window before the next tick, and immediately go again without manually re-damaging it first.
// SetHealth() is a raw value set (no heal/damage event, no combat log line, no threat) - only the
// player's own actual heal casts produce visible combat log entries; the periodic reset itself is
// silent.

#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureScript.h"

namespace
{
    constexpr int32 HEALING_DUMMY_TARGET_PCT = 30;
    constexpr uint32 HEALING_DUMMY_RESET_INTERVAL_MS = 1000;
}

class npc_healing_dummy : public CreatureAI
{
public:
    explicit npc_healing_dummy(Creature* creature) : CreatureAI(creature) { }

    void Reset() override
    {
        me->SetHealth(me->CountPctFromMaxHealth(HEALING_DUMMY_TARGET_PCT));
        _resetTimer = HEALING_DUMMY_RESET_INTERVAL_MS;
    }

    void UpdateAI(uint32 diff) override
    {
        if (_resetTimer <= diff)
        {
            me->SetHealth(me->CountPctFromMaxHealth(HEALING_DUMMY_TARGET_PCT));
            _resetTimer = HEALING_DUMMY_RESET_INTERVAL_MS;
        }
        else
            _resetTimer -= diff;
    }

private:
    uint32 _resetTimer = HEALING_DUMMY_RESET_INTERVAL_MS;
};

void AddSC_custom_healing_dummy()
{
    RegisterCreatureAI(npc_healing_dummy);
}
