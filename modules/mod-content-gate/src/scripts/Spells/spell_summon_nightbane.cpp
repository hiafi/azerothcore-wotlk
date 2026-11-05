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

// Ported from mod-progression by Revision <tkn963@gmail.com> (GPL-2):
// src/phase_00/scripts/Spells/spell_summon_nightbane.cpp at 8c765a1.

#include "InstanceScript.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

enum
{
    DATA_NIGHTBANE      = 11,
    ACTION_START_INTRO  = 0
};

class spell_summon_nightbane : public SpellScript
{
    PrepareSpellScript(spell_summon_nightbane);

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (InstanceScript* instance = GetCaster()->GetInstanceScript())
            if (instance->GetBossState(DATA_NIGHTBANE) == NOT_STARTED)
                if (Creature* nightbane = instance->GetCreature(DATA_NIGHTBANE))
                    if (nightbane->IsAlive())
                        nightbane->AI()->DoAction(ACTION_START_INTRO);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_summon_nightbane::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

void AddSC_spell_summon_nightbane()
{
    RegisterSpellScript(spell_summon_nightbane);
}
