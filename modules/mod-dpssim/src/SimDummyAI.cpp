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

#include "SimDummyAI.h"
#include "CreatureScript.h"
#include "PassiveAI.h"

namespace
{
    // A sim-exclusive training dummy AI (entry 900004+, data/sql/updates/pending_db_world - see
    // that migration's own doc comment) - identical to the shared npc_training_dummy
    // (src/server/scripts/World/npcs_special.cpp) except it drops that AI's 5-second no-damage
    // combat timeout entirely, keeping only the "zero all damage taken" behavior every dummy needs
    // to never actually die.
    //
    // Why this needs to exist at all: npc_training_dummy's timeout is correct for a real player
    // (who might genuinely step away mid-test and should have combat end), but it's a bad fit for
    // SimDaemon::RunPlayerbotBatch()'s reused-actor-across-iterations design - confirmed via
    // diagnostic logging (see docs/bugs-and-fixes.md's "iteration 1 lands hits, every iteration
    // after it doesn't" entry) that this timeout expiring for real (Unit::IsInCombat() going
    // false, not just some AI-side cache) is what silently breaks a batch partway through, and
    // that refreshing it at each iteration boundary (SimBot::ReestablishCombatState()) only
    // narrows the failure window rather than closing it - the bot's own decision latency plus a
    // real cast time can still exceed 5 simulated seconds before the first hit of a new iteration
    // lands. Removing the timeout at its source, for this sim-exclusive entry only, closes that
    // window entirely instead of racing it.
    //
    // Deliberately a NEW entry (900004, then 900005/900006 once this is confirmed working) rather
    // than changing npc_training_dummy itself or 900001-900003's own AIName: those three are real,
    // permanently world-spawned dummies real players use for testing too (see the base migration's
    // own `creature` INSERT) - changing their AI would change live player-facing behavior, not
    // just this sim's.
    struct npc_dpssim_training_dummy : NullCreatureAI
    {
        npc_dpssim_training_dummy(Creature* creature) : NullCreatureAI(creature) { }

        void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*damageType*/, SpellSchoolMask /*schoolMask*/) override
        {
            damage = 0;
        }
    };
}

void AddSC_SimDummyAI()
{
    RegisterCreatureAI(npc_dpssim_training_dummy);
}
