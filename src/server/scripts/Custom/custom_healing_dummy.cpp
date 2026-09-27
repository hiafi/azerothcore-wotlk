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
//
// Combat variant (entry 900013, npc_healing_dummy_combat): same 30% pin, but healing it also puts
// the healer in combat for a fixed 2 minutes (then combat ends; the next heal starts a fresh
// window), so in-combat-only effects (spirit regen, 5-second rule, combat-gated procs/talents) can
// be tested. The dummy itself is friendly and can't hold combat with a player
// (CombatManager::CanBeginCombat rejects friendly pairs), so it summons an invisible, unselectable,
// passive hostile "anchor" (entry 900014) that holds the actual PvE combat reference with each
// healer. The anchor never attacks and despawns 10s after its last combat reference ends.

#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "TemporarySummon.h"
#include <unordered_map>

namespace
{
    constexpr int32 HEALING_DUMMY_TARGET_PCT = 30;
    constexpr uint32 HEALING_DUMMY_RESET_INTERVAL_MS = 1000;

    constexpr uint32 NPC_HEALING_DUMMY_COMBAT_ANCHOR = 900014;
    constexpr Milliseconds HEALING_DUMMY_COMBAT_DURATION = 2min;
    constexpr uint32 HEALING_DUMMY_ANCHOR_DESPAWN_MS = 10 * IN_MILLISECONDS;
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

class npc_healing_dummy_combat : public npc_healing_dummy
{
public:
    explicit npc_healing_dummy_combat(Creature* creature) : npc_healing_dummy(creature) { }

    void HealReceived(Unit* doneBy, uint32& /*addhealth*/) override
    {
        Player* player = doneBy ? doneBy->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        if (!player || _combatTimers.contains(player->GetGUID()))
            return;

        Creature* anchor = GetOrSummonAnchor();
        if (!anchor)
            return;

        anchor->SetInCombatWith(player);
        if (anchor->IsInCombatWith(player))
            _combatTimers[player->GetGUID()] = HEALING_DUMMY_COMBAT_DURATION;
    }

    void UpdateAI(uint32 diff) override
    {
        npc_healing_dummy::UpdateAI(diff);

        if (_combatTimers.empty())
            return;

        Creature* anchor = ObjectAccessor::GetCreature(*me, _anchorGuid);
        if (!anchor)
        {
            _combatTimers.clear();
            return;
        }

        auto const& pveRefs = anchor->GetCombatManager().GetPvECombatRefs();
        for (auto itr = _combatTimers.begin(); itr != _combatTimers.end();)
        {
            itr->second -= Milliseconds(diff);

            // Combat already ended some other way (death, teleport, out of range): just stop
            // tracking so the next heal starts a fresh window.
            auto ref = pveRefs.find(itr->first);
            if (ref == pveRefs.end())
            {
                itr = _combatTimers.erase(itr);
                continue;
            }

            if (itr->second <= 0s)
            {
                ref->second->EndCombat();
                itr = _combatTimers.erase(itr);
            }
            else
                ++itr;
        }
    }

private:
    Creature* GetOrSummonAnchor()
    {
        if (Creature* anchor = ObjectAccessor::GetCreature(*me, _anchorGuid))
            return anchor;

        TempSummon* anchor = me->SummonCreature(NPC_HEALING_DUMMY_COMBAT_ANCHOR, *me,
            TEMPSUMMON_TIMED_DESPAWN_OUT_OF_COMBAT, HEALING_DUMMY_ANCHOR_DESPAWN_MS);
        _anchorGuid = anchor ? anchor->GetGUID() : ObjectGuid::Empty;
        return anchor;
    }

    ObjectGuid _anchorGuid;
    std::unordered_map<ObjectGuid, Milliseconds> _combatTimers;
};

// Invisible combat partner for npc_healing_dummy_combat. Must have a script: a creature without
// one gets a default aggressive AI whose UpdateVictim() would evade (and drop combat) immediately,
// since the anchor never has anyone on its threat list. Must NOT be flagged
// CREATURE_FLAG_EXTRA_TRIGGER: NullCreatureAI's constructor marks triggers combat-disallowed.
struct npc_healing_dummy_combat_anchor : public NullCreatureAI
{
    explicit npc_healing_dummy_combat_anchor(Creature* creature) : NullCreatureAI(creature) { }
};

void AddSC_custom_healing_dummy()
{
    RegisterCreatureAI(npc_healing_dummy);
    RegisterCreatureAI(npc_healing_dummy_combat);
    RegisterCreatureAI(npc_healing_dummy_combat_anchor);
}
