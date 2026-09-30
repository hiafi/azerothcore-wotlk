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

// Custom: damageable training dummy, rebound by SQL onto every creature_template entry that used
// the stock npc_training_dummy (src/server/scripts/World/npcs_special.cpp, left untouched).
//
// The stock AI zeroes all damage in DamageTaken, which also zeroes every heal computed from the
// damage actually dealt - Drain Life and other PERIODIC_LEECH / HEALTH_LEECH effects and
// damage-based self-heal scripts heal nothing on it (docs/bugs-and-fixes.md). This AI lets the
// damage land, clamps it so the dummy never dies, and silently refills its health every 3 sec
// (SetFullHealth is a raw value set: no heal event, no combat log line, no threat). The per-attacker
// 5 sec no-damage combat timeout is kept exactly as the stock AI has it.
//
// The mod-dpssim dummies (900004-900006, npc_dpssim_training_dummy) are sim-only and keep their
// own zero-damage AI.

#include "CreatureScript.h"
#include "PassiveAI.h"
#include <unordered_map>

namespace
{
    constexpr Milliseconds TRAINING_DUMMY_HEALTH_RESET_INTERVAL = 3s;
    constexpr Milliseconds TRAINING_DUMMY_COMBAT_TIMEOUT = 5s;
}

struct npc_custom_training_dummy : NullCreatureAI
{
    explicit npc_custom_training_dummy(Creature* creature) : NullCreatureAI(creature) { }

    void Reset() override
    {
        scheduler.CancelAll();
        scheduler.Schedule(TRAINING_DUMMY_HEALTH_RESET_INTERVAL, [this](TaskContext context)
        {
            me->SetFullHealth();
            context.Repeat();
        });
    }

    void JustEnteredCombat(Unit* who) override
    {
        _combatTimer[who->GetGUID()] = TRAINING_DUMMY_COMBAT_TIMEOUT;
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType damageType, SpellSchoolMask) override
    {
        if (damage >= me->GetHealth())
            damage = me->GetHealth() - 1;

        if (!attacker || damageType == DOT)
            return;

        _combatTimer[attacker->GetGUID()] = TRAINING_DUMMY_COMBAT_TIMEOUT;

        // Pet attacks engage the owner via propagation without firing
        // JustEnteredCombat here, so track the owner's timer too.
        if (Unit* owner = attacker->GetCharmerOrOwner())
            if (me->GetCombatManager().IsInCombatWith(owner))
                _combatTimer[owner->GetGUID()] = TRAINING_DUMMY_COMBAT_TIMEOUT;
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);

        for (auto itr = _combatTimer.begin(); itr != _combatTimer.end();)
        {
            itr->second -= Milliseconds(diff);
            if (itr->second <= 0s)
            {
                // The attacker has not dealt any damage to the dummy for over 5 seconds. End combat.
                auto const& pveRefs = me->GetCombatManager().GetPvECombatRefs();
                auto it = pveRefs.find(itr->first);
                if (it != pveRefs.end())
                    it->second->EndCombat();

                itr = _combatTimer.erase(itr);
            }
            else
                ++itr;
        }
    }

private:
    std::unordered_map<ObjectGuid, Milliseconds> _combatTimer;
};

void AddSC_custom_training_dummy()
{
    RegisterCreatureAI(npc_custom_training_dummy);
}
