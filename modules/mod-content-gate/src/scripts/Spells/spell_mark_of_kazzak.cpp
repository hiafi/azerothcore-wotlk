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
// src/phase_00/scripts/Spells/spell_mark_of_kazzak.cpp at 8c765a1.

#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

enum Spells
{
    SPELL_MARK_OF_KAZZAK_DAMAGE = 21058
};

class spell_mark_of_kazzak : public SpellScriptLoader
{
public:
    spell_mark_of_kazzak() : SpellScriptLoader("spell_mark_of_kazzak") { }

    class spell_mark_of_kazzak_AuraScript : public AuraScript
    {
        PrepareAuraScript(spell_mark_of_kazzak_AuraScript);

        bool Validate(SpellInfo const* /*spell*/) override
        {
            if (!sSpellMgr->GetSpellInfo(SPELL_MARK_OF_KAZZAK_DAMAGE))
                return false;

            return true;
        }

        void OnPeriodic(AuraEffect const* aurEff)
        {
            Unit* target = GetTarget();

            if (target->GetPower(POWER_MANA) <= 50)
            {
                target->CastSpell(target, SPELL_MARK_OF_KAZZAK_DAMAGE, true, NULL, aurEff);
                SetDuration(0);
            }
        }

        void Register() override
        {
            OnEffectPeriodic += AuraEffectPeriodicFn(spell_mark_of_kazzak_AuraScript::OnPeriodic, EFFECT_0,
                SPELL_AURA_PERIODIC_MANA_LEECH);
        }
    };

    AuraScript* GetAuraScript() const override
    {
        return new spell_mark_of_kazzak_AuraScript();
    }
};

void AddSC_spell_mark_of_kazzak()
{
    new spell_mark_of_kazzak();
}
