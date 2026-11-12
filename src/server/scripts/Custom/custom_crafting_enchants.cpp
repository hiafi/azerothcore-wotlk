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
#include "SpellMgr.h"
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

// Custom: crafting rework C7 premium enchants (.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decision 4;
// data in apps/dbc-tools/lib/crafting_consumables_data.py). Crusader (208800) and Spellsurge (208801) buff the higher
// of two primaries: the proc aura triggers spell T (the first stat, its MiscValue) and T + 1 is the second; the proc
// casts whichever stat the wearer has more of. The chance and internal cooldown are the aura's spell_proc row.
class spell_crafting_premium_higher_primary : public AuraScript
{
    PrepareAuraScript(spell_crafting_premium_higher_primary);

    bool Validate(SpellInfo const* spellInfo) override
    {
        uint32 const first = spellInfo->Effects[EFFECT_0].TriggerSpell;
        return ValidateSpellInfo({ first, first + 1 });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        Unit* owner = GetTarget();
        uint32 const first = aurEff->GetSpellInfo()->Effects[EFFECT_0].TriggerSpell;
        SpellInfo const* firstInfo = sSpellMgr->GetSpellInfo(first);
        SpellInfo const* secondInfo = sSpellMgr->GetSpellInfo(first + 1);
        if (!firstInfo || !secondInfo)
            return;

        auto statOf = [owner](SpellInfo const* info)
        {
            return owner->GetStat(Stats(info->Effects[EFFECT_0].MiscValue));
        };
        uint32 const buff = statOf(secondInfo) > statOf(firstInfo) ? first + 1 : first;
        owner->CastSpell(owner, buff, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_crafting_premium_higher_primary::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 208815 - Steelweave: the absorb's declared amount is a percent of the wearer's maximum health.
class spell_crafting_max_health_absorb : public AuraScript
{
    PrepareAuraScript(spell_crafting_max_health_absorb);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* caster = GetCaster())
            amount = int32(CalculatePct(caster->GetMaxHealth(), amount));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_crafting_max_health_absorb::CalcAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// Crafting rework C7: the learn spell of a raid recipe or premium formula item (208600-208725, 208840-208846) is
// refused when the player already knows every recipe it teaches, so the item is not used up for nothing.
class spell_crafting_recipe_learn : public SpellScript
{
    PrepareSpellScript(spell_crafting_recipe_learn);

    SpellCastResult CheckCast()
    {
        Player* player = GetCaster()->ToPlayer();
        if (!player)
            return SPELL_FAILED_DONT_REPORT;
        for (SpellEffectInfo const& effect : GetSpellInfo()->Effects)
        {
            uint32 const recipe = effect.TriggerSpell;
            if (effect.Effect == SPELL_EFFECT_LEARN_SPELL && recipe && !player->HasSpell(recipe))
                return SPELL_CAST_OK;
        }
        return SPELL_FAILED_SPELL_LEARNED;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_crafting_recipe_learn::CheckCast);
    }
};

void AddSC_custom_crafting_enchants()
{
    RegisterSpellScript(spell_crafting_force_field_lens);
    RegisterSpellScript(spell_crafting_premium_higher_primary);
    RegisterSpellScript(spell_crafting_max_health_absorb);
    RegisterSpellScript(spell_crafting_recipe_learn);
}
