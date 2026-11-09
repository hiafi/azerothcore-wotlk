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
 * stacks, splits, a percent that changes during the fight. The periodic script caches its per-stack amount, so a
 * recalculation after the caster despawned (a stack change, a one-stack dispel) keeps the tick (R-1-KIT F1).
 */

#include "DungeonKit.h"
#include "DungeonKitFlow.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"
#include <array>
#include <optional>

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

    // R-1-KIT F1: `amount` arrives as the raw hundredths on every (re)calculation, and the engine multiplies the
    // result by the stack count. A stack change or a one-stack dispel after the caster despawned recalculates without
    // a caster, so the per-stack amount is cached per effect (DungeonKit::PerStackAmount) and reused then; with no
    // cache yet it is computed from the aura's owner (same dungeon map, same reference row), never the raw value.
    void CalcAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        if (!aurEff || aurEff->GetEffIndex() >= MAX_SPELL_EFFECTS)
            return;
        uint8 const effIndex = aurEff->GetEffIndex();
        Unit* caster = GetCaster();
        Unit* owner = GetUnitOwner();
        std::optional<int32> withCaster;
        std::optional<int32> fromOwner;
        if (caster)
            withCaster = static_cast<int32>(DungeonKit::RefFlatOn(caster, owner,
                PercentOf(GetSpellInfo(), effIndex, caster)));
        else if (owner)
            fromOwner = static_cast<int32>(DungeonKit::RefFlatOn(owner, owner,
                PercentOf(GetSpellInfo(), effIndex, owner)));
        amount = _perStack[effIndex].Resolve(withCaster, fromOwner);
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dungeon_refflat_periodic::CalcAmount, EFFECT_ALL,
            SPELL_AURA_PERIODIC_DAMAGE);
    }

    std::array<DungeonKit::PerStackAmount, MAX_SPELL_EFFECTS> _perStack;
};

void AddSC_dungeon_kit_spells()
{
    RegisterSpellScript(spell_dungeon_refflat_damage);
    RegisterSpellScript(spell_dungeon_refflat_periodic);
}
