/*
 * mod-dungeon-bosses, the shared dungeon kit: the generic percent spells (Stratholme WP-KT-1, handoff section 3.11
 * #17). A custom dungeon spell whose damage is a percent of the reference health row binds one of these by name
 * (dbc-tools `scripted_by`) instead of a SpellScript of its own:
 *
 *   spell_dungeon_refflat_damage    every SPELL_EFFECT_SCHOOL_DAMAGE effect: SetEffectValue(RefFlatOn) at launch
 *   spell_dungeon_refflat_periodic  every SPELL_AURA_PERIODIC_DAMAGE effect: each tick's amount = RefFlatOn
 *
 * The percent rides in the effect, in hundredths (DungeonKitFlow.h EffectPercent): the shown value on normal
 * (EffectBasePoints + 1 as stored: 3000 = 30%), EffectMiscValueB on heroic (0: the normal value). RefFlatOn picks the
 * tank row for the tank, so a combat log spot check matches the registry's own hits. The spell still needs
 * SPELL_ATTR3_IGNORE_CASTER_MODIFIERS (and a target-side school of its own); nothing here sets attributes. A per-boss
 * SpellScript calling RefFlatOn (the SFK / Scholomance precedent) remains the way for anything these do not cover:
 * stacks, splits, a percent that changes during the fight.
 */

#include "DungeonKit.h"
#include "DungeonKitFlow.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

namespace
{
    float PercentOf(SpellInfo const* info, uint8 effIndex, WorldObject const* where)
    {
        if (!info || effIndex >= MAX_SPELL_EFFECTS)
            return 0.f;
        SpellEffectInfo const& effect = info->Effects[effIndex];
        return DungeonKit::EffectPercent(DungeonKit::EffectShownValue(effect.BasePoints, effect.DieSides),
            effect.MiscValueB, DungeonKit::IsHeroicMap(where));
    }
}

class spell_dungeon_refflat_damage : public SpellScript
{
    PrepareSpellScript(spell_dungeon_refflat_damage);

    void SetDamage(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = PercentOf(GetSpellInfo(), static_cast<uint8>(effIndex), caster);
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_dungeon_refflat_damage::SetDamage, EFFECT_ALL,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

class spell_dungeon_refflat_periodic : public AuraScript
{
    PrepareAuraScript(spell_dungeon_refflat_periodic);

    void CalcAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        Unit* caster = GetCaster();
        Unit* owner = GetUnitOwner();
        if (!caster || !aurEff)
            return;
        float const pct = PercentOf(GetSpellInfo(), aurEff->GetEffIndex(), caster);
        amount = static_cast<int32>(DungeonKit::RefFlatOn(caster, owner, pct));
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dungeon_refflat_periodic::CalcAmount, EFFECT_ALL,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

void AddSC_dungeon_kit_spells()
{
    RegisterSpellScript(spell_dungeon_refflat_damage);
    RegisterSpellScript(spell_dungeon_refflat_periodic);
}
