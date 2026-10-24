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

/*
 * Death Knight rework - shared spell scripts (death-knight-rework DK0a; docs/reworks/death-knight-shared-rework.md).
 */

#include "DeathKnightMechanics.h"
#include "EngagementMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include <list>

namespace
{
    // Stock ids the DSL does not declare (they are not edited by the rework), so DeathKnightData has no name for them.
    constexpr uint32 SPELL_DK_BLOOD_PLAGUE = 55078;
    constexpr uint32 SPELL_DK_FROST_FEVER = 55095;
}

// 49998 - Death Strike (main hand only; the off-hand 66188 has no binding and never heals). EFFECT_2 is a DUMMY whose
// value is the heal percent of the recent damage taken (shared doc "Death Strike": 25). The heal is the larger of that
// share and the minimum health share, computed by DeathKnight::ComputeDeathStrikeHeal. The dummy effect only fires on
// a hit, so a miss, dodge or parry heals nothing.
class spell_dk_death_strike_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_death_strike_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ DeathKnightData::SPELL_DEATH_STRIKE_HEAL });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || !GetHitUnit())
            return;

        int32 const heal = int32(DeathKnight::ComputeDeathStrikeHeal(player, GetEffectValue()));
        if (heal <= 0)
            return;

        player->CastCustomSpell(DeathKnightData::SPELL_DEATH_STRIKE_HEAL, SPELLVALUE_BASE_POINT0, heal, player,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_dk_death_strike_rework::HandleDummy, EFFECT_2, SPELL_EFFECT_DUMMY);
    }
};

// 48707 - Anti-Magic Shell (on self). A second script beside the stock spell_dk_anti_magic_shell_self: the damage the
// shell absorbs counts toward Death Strike's record (shared doc "Death Strike": "counts damage absorbed by the Death
// Knight's own shields"). AfterEffectAbsorb receives the amount actually absorbed after clamping to the hit.
class spell_dk_ams_damage_record : public AuraScript
{
    PrepareAuraScript(spell_dk_ams_damage_record);

    void HandleAfterAbsorb(AuraEffect* /*aurEff*/, DamageInfo& /*dmgInfo*/, uint32& absorbAmount)
    {
        if (!absorbAmount)
            return;

        Player* player = GetTarget()->ToPlayer();
        if (player && DeathKnight::TracksDamageTaken(player))
            DeathKnight::RecordDamageTaken(player, absorbAmount);
    }

    void Register() override
    {
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_dk_ams_damage_record::HandleAfterAbsorb, EFFECT_0);
    }
};

// 203001 - Death's Caress. EFFECT_0 hits the explicit target; EFFECT_1 is the extra-target area around it. The area
// keeps at most DEATHS_CARESS_EXTRA_TARGETS enemies already in combat with the Death Knight or the group, nearest to
// the explicit target first, and never the explicit target itself (EFFECT_0 owns it) or the caster. Every unit hit by
// either damage effect gets Blood Plague from the Death Knight, triggered; the helper is never cast at the caster.
class spell_dk_deaths_caress : public SpellScript
{
    PrepareSpellScript(spell_dk_deaths_caress);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DK_BLOOD_PLAGUE });
    }

    void FilterExtraTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* explicitTarget = GetExplTargetUnit();
        if (!player || !explicitTarget)
        {
            targets.clear();
            return;
        }

        targets.remove_if([player, explicitTarget](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || unit == explicitTarget || unit == player ||
                !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });

        targets.sort([explicitTarget](WorldObject const* a, WorldObject const* b)
        {
            return explicitTarget->GetExactDist(a) < explicitTarget->GetExactDist(b);
        });

        if (targets.size() > uint32(DeathKnightData::DEATHS_CARESS_EXTRA_TARGETS))
            targets.resize(uint32(DeathKnightData::DEATHS_CARESS_EXTRA_TARGETS));
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster)
            return;

        // Each unit sits in exactly one of the two damage effects; the guid set is a guard against a double apply
        if (!_infected.insert(target->GetGUID()).second)
            return;

        caster->CastSpell(target, SPELL_DK_BLOOD_PLAGUE, true);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_deaths_caress::FilterExtraTargets, EFFECT_1,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_dk_deaths_caress::HandleHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
        OnEffectHitTarget += SpellEffectFn(spell_dk_deaths_caress::HandleHit, EFFECT_1, SPELL_EFFECT_SCHOOL_DAMAGE);
    }

    GuidSet _infected;
};

// 50842 - Pestilence (replaces the stock spell_dk_pestilence). EFFECT_2 is the 10 yd script-effect area around the
// target. The area keeps only enemies already in combat with the Death Knight or the group (never pulls). For each such
// unit other than the primary target, every disease the Death Knight has on the primary is copied fresh (triggered, at
// the Death Knight's current stats) unless that unit already carries the Death Knight's own copy: a copy never
// overwrites or refreshes. No Glyph of Disease refresh (glyphs are retired). Then DeathKnight::OnPestilenceCopy, once
// per enemy reached (wound copies and On a Pale Horse hang off it in S3).
class spell_dk_pestilence_rework : public SpellScript
{
    PrepareSpellScript(spell_dk_pestilence_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DK_BLOOD_PLAGUE, SPELL_DK_FROST_FEVER });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
        {
            targets.clear();
            return;
        }

        Unit* primary = GetExplTargetUnit();
        targets.remove_if([player, primary](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            if (!unit)
                return true;

            // The primary target is the one the player chose; it is not copied onto, so leave it alone
            return unit != primary && !Engagement::IsEngagedWithOwnerOrGroup(unit, player);
        });
    }

    void HandleScriptEffect(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        Unit* primary = GetExplTargetUnit();
        Unit* hitUnit = GetHitUnit();
        if (!player || !primary || !hitUnit || hitUnit == primary)
            return;

        for (uint32 const disease : { SPELL_DK_BLOOD_PLAGUE, SPELL_DK_FROST_FEVER })
        {
            if (!primary->HasAura(disease, player->GetGUID()) || hitUnit->HasAura(disease, player->GetGUID()))
                continue;

            player->CastSpell(hitUnit, disease, true);
        }

        DeathKnight::OnPestilenceCopy(player, primary, hitUnit);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_dk_pestilence_rework::FilterTargets, EFFECT_2,
            TARGET_UNIT_DEST_AREA_ENEMY);
        OnEffectHitTarget += SpellEffectFn(spell_dk_pestilence_rework::HandleScriptEffect, EFFECT_2,
            SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// 50461 - Anti-Magic Zone (the aura on each party member, cast by the zone creature; the DK is the zone's owner).
// Each member's copy is unlimited (amount -1): the shared pool lives on the zone (DeathKnight::ConsumeZoneAbsorb),
// so the area aura re-applying a copy never refills it. AMZ_SPELL_REDUCTION_PCT% of every hit it covers is wanted;
// the pool decides how much of that is absorbed, and unsummons the zone when it runs dry.
class spell_dk_anti_magic_zone_rework : public AuraScript
{
    PrepareAuraScript(spell_dk_anti_magic_zone_rework);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = -1;
    }

    void HandleAbsorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        absorbAmount = 0;

        Unit* zone = GetCaster();
        Unit* ownerUnit = zone ? zone->GetOwner() : nullptr;
        Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr;
        if (!owner)
            return;

        uint32 const wanted = CalculatePct(dmgInfo.GetDamage(), DeathKnightData::AMZ_SPELL_REDUCTION_PCT);
        if (!wanted)
            return;

        absorbAmount = DeathKnight::ConsumeZoneAbsorb(zone, owner, wanted);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_dk_anti_magic_zone_rework::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_dk_anti_magic_zone_rework::HandleAbsorb, EFFECT_0);
    }
};

void AddSC_deathknight_shared_spell_scripts()
{
    RegisterSpellScript(spell_dk_death_strike_rework);
    RegisterSpellScript(spell_dk_ams_damage_record);
    RegisterSpellScript(spell_dk_deaths_caress);
    RegisterSpellScript(spell_dk_pestilence_rework);
    RegisterSpellScript(spell_dk_anti_magic_zone_rework);
}
