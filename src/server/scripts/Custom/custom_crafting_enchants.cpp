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

// Custom: crafting rework C6, Engineering tinkers (.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md
// decision 3, rulings 2026-11-11). Every enchant is an item; a tinker is an on-use enchant (type 7) that replaces the
// head or ranged enchant. Their effect spells are data (apps/dbc-tools/source/world/crafting_enchants.py,
// 207480-207483) except Force Field Lens, whose absorb is 10% of the wearer's maximum health, so it grows with gear
// like the Bulwark meta gem's shield.

#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

namespace
{
    constexpr uint32 FORCE_FIELD_HEALTH_PCT = 10;
}

// 207481 - Force Field Lens
class spell_crafting_force_field_lens : public AuraScript
{
    PrepareAuraScript(spell_crafting_force_field_lens);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* caster = GetCaster())
            amount = int32(CalculatePct(caster->GetMaxHealth(), FORCE_FIELD_HEALTH_PCT));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_crafting_force_field_lens::CalcAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

void AddSC_custom_crafting_enchants()
{
    RegisterSpellScript(spell_crafting_force_field_lens);
}
