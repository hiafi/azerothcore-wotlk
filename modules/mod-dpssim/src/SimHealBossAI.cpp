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

#include "SimHealBossAI.h"
#include "Creature.h"
#include "CreatureScript.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include <algorithm>

namespace
{
    // The boss's victim candidates, best first (SimHealBoss::SetVictimOrder). A process runs one healing scenario, so a
    // static is enough, like SimDummyAI's health-drain flag.
    std::vector<ObjectGuid> s_victimOrder;

    // The first living candidate, nullptr when none is alive
    Player* PickVictim()
    {
        for (ObjectGuid const& guid : s_victimOrder)
            if (Player* player = ObjectAccessor::FindPlayer(guid); player && player->IsAlive())
                return player;
        return nullptr;
    }

    // How often the boss tops its health back up to full. The creature has a huge health pool and the clamp in
    // DamageTaken below already stops it from dying, so this only keeps the health bar full for display.
    constexpr uint32 HEALTH_TOP_UP_MS = 1000;

    // The healing sim's damage source (creature entries 900015-900017, "Sim Raid Boss"; plan section 1). Hostile and
    // attackable, so the healer bot can attack it (that damage is recorded as the healer's secondary "damage done") and
    // so it can hold combat references with every group member. Its damage to the group comes only from the sim's
    // damage drivers (Sim Damage Pulse / Sim Pin Hit casts, HS1), never from melee.
    //
    // Built on NullCreatureAI, which is exactly the passive shell this stage needs: REACT_PASSIVE, no UpdateAI work, no
    // chasing (AttackStart does nothing), no melee swings (nothing calls DoMeleeAttackIfReady), and no evading back
    // home (EnterEvadeMode does nothing), so the boss stays where it was placed for the whole iteration.
    //
    // HS1 adds the victim pin to UpdateAI (Attack(victim, false) so it never swings): the main tank, or the next living
    // candidate when it is dead. Engaging the group and the drain and pin drivers live in SimHealBoss::Engage() and
    // SimHealScenario.cpp, run from the sim step.
    struct npc_healsim_boss : NullCreatureAI
    {
        explicit npc_healsim_boss(Creature* creature) : NullCreatureAI(creature) { }

        void Reset() override
        {
            // Rooted so a stray knockback or pull can't carry it away from the layout the sim built around it. The boss
            // data carries the boss immunity set, which already covers those effects; this is the second line.
            me->SetReactState(REACT_PASSIVE);
            me->SetControlled(true, UNIT_STATE_ROOT);
            _topUpTimer = HEALTH_TOP_UP_MS;
        }

        void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*damageType*/,
            SpellSchoolMask /*schoolMask*/) override
        {
            // Real damage that is shown and recorded (the healer's damage to it counts as damage done), but never
            // lethal: the same "never below 1 health" rule as the dpssim dummy's health drain (SimDummyAI.cpp).
            uint32 const health = me->GetHealth();
            damage = health > 1 ? std::min(damage, health - 1) : 0;
        }

        void UpdateAI(uint32 diff) override
        {
            // Nothing re-targets the boss (no threat-based victim selection runs for it), but an AttackStop() from
            // somewhere else in the core would leave the Holy Paladin values without a tank to find. Only while it is
            // in combat: between iterations the sim ends combat on purpose (the pre-pull buff phase).
            if (!s_victimOrder.empty() && me->IsInCombat())
                if (Player* wanted = PickVictim())
                {
                    Unit* victim = me->GetVictim();
                    if (!victim || victim->GetGUID() != wanted->GetGUID())
                    {
                        // Once per switch, even if the attack does not take
                        if (_lastLogged != wanted->GetGUID())
                        {
                            _lastLogged = wanted->GetGUID();
                            LOG_INFO("server.dpssim", "mod-dpssim: the boss's victim changes from {} to {}.",
                                victim ? victim->GetName() : std::string("nobody"), wanted->GetName());
                        }
                        me->Attack(wanted, false);
                    }
                    else
                        _lastLogged = ObjectGuid::Empty;
                }

            if (_topUpTimer > diff)
            {
                _topUpTimer -= diff;
                return;
            }

            _topUpTimer = HEALTH_TOP_UP_MS;

            if (me->GetHealth() < me->GetMaxHealth())
                me->SetFullHealth();
        }

    private:
        uint32 _topUpTimer = HEALTH_TOP_UP_MS;
        ObjectGuid _lastLogged;
    };
}

uint32 SimHealBoss::EntryForLevel(uint8 level)
{
    if (level >= 80)
        return ENTRY_LEVEL_80;

    return level >= 70 ? ENTRY_LEVEL_70 : ENTRY_LEVEL_60;
}

void SimHealBoss::SetVictimOrder(std::vector<ObjectGuid> const& order)
{
    s_victimOrder = order;
}

uint32 SimHealBoss::Engage(Creature* boss, std::vector<Player*> const& members)
{
    uint32 missing = 0;
    for (Player* member : members)
    {
        if (!member || !member->IsAlive())
            continue;

        boss->EngageWithTarget(member);
        if (!member->IsInCombatWith(boss))
            member->SetInCombatWith(boss);
        if (!member->IsInCombatWith(boss))
            ++missing;
    }

    if (Player* victim = PickVictim())
        boss->Attack(victim, false);

    return missing;
}

void AddSC_SimHealBossAI()
{
    RegisterCreatureAI(npc_healsim_boss);
}
