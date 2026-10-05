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
 * Paladin rework - Holy tree scripts
 * (.agents/plans/paladin-rework/paladin-rework.HOLY.md §2.7, behaviour in §4-§7).
 *
 * Replacement/additive classes for the Holy tree; script names must match WP-A's bindings byte for
 * byte. Stock spell_paladin.cpp stays unedited. The Paladin:: Holy section (Glimmer state, Shock
 * value helpers, pulses) is in PaladinMechanics.cpp.
 */

#include "PaladinMechanics.h"
#include "Generated/PaladinData.h"
#include "Cell.h"
#include "CellImpl.h"
#include "DynamicObject.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "HealMechanics.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <cmath>
#include <list>
#include <vector>

namespace
{
    // Stock ids the DSL never declares (hand literals, WarlockMechanics.h convention)
    enum PaladinHolyStockSpells
    {
        SPELL_PAL_LIGHT_S_BEACON_AURA   = 53651,    // area aura the beacon target projects onto the party
        SPELL_PAL_BEACON_OF_LIGHT_HS    = 53654,    // Beacon's Holy Shock copy heal
        SPELL_PAL_FLASH_OF_LIGHT_HOT    = 66922     // Infusion of Light's Flash of Light HoT
    };

    constexpr uint32 FAMILY_FLAG_HOLY_LIGHT     = 0x80000000;   // d0, stock 635
    constexpr uint32 FAMILY_FLAG_FLASH_OF_LIGHT = 0x40000000;   // d0, stock 19750
    constexpr size_t LIGHTS_HAMMER_TARGETS      = 5;            // heal tick: most injured 5
    constexpr float MERCIFUL_HEAL_RANGE         = 40.0f;
    constexpr uint8 MERCIFUL_HEAL_TARGETS       = 3;
    constexpr uint8 HEAL_CANDIDATES             = 100;          // SelectMostInjured trims before our filters
    constexpr uint8 TOLL_CANDIDATES             = HEAL_CANDIDATES;
    constexpr float OVERFLOWING_LIGHT_RANGE     = 10.0f;
    constexpr float RADIANT_CLEAVE_RANGE        = 8.0f;
    constexpr uint8 RADIANT_CLEAVE_TARGETS      = 2;
    constexpr float RADIANT_CLEAVE_PCT          = 50.0f;
    constexpr float SUNLIGHT_ECHO_CHANCE        = 10.0f;
    constexpr float DAYBREAK_CHANCE             = 10.0f;
    constexpr int32 OVERFLOWING_LAY_ON_HANDS_MS = 3000;
    constexpr int32 SPIRITUAL_FOCUS_SLACK_MS    = 100;

    Player* GetPlayerOrNull(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }

    bool IsHolyLight(SpellInfo const* info)
    {
        return info && info->SpellFamilyName == SPELLFAMILY_PALADIN &&
            (info->SpellFamilyFlags[0] & FAMILY_FLAG_HOLY_LIGHT);
    }

    bool IsFlashOfLight(SpellInfo const* info)
    {
        return info && info->SpellFamilyName == SPELLFAMILY_PALADIN &&
            (info->SpellFamilyFlags[0] & FAMILY_FLAG_FLASH_OF_LIGHT);
    }

    // Owner of a passive talent aura, only when it is also the proc's actor (CR1: NPC paladins never reach Holy state)
    Player* GetProcOwner(Unit* owner, ProcEventInfo& eventInfo)
    {
        Player* player = GetPlayerOrNull(owner);
        if (!player || eventInfo.GetActor() != player)
            return nullptr;

        return player;
    }

    // Merciful Strikes (Crusader Strike proc): heal total split evenly over <= 3 injured party/raid members
    void CastMercifulHeal(Player* caster, int32 total)
    {
        if (total <= 0)
            return;

        std::vector<Unit*> targets;
        Heal::SelectMostInjured(caster, caster, MERCIFUL_HEAL_RANGE, HEAL_CANDIDATES, targets);
        targets.erase(std::remove_if(targets.begin(), targets.end(), [](Unit const* unit)
        {
            return unit->IsFullHealth();
        }), targets.end());
        if (targets.size() > MERCIFUL_HEAL_TARGETS)
            targets.resize(MERCIFUL_HEAL_TARGETS);

        if (!targets.empty())
            Paladin::CastSplitHeal(caster, PaladinData::SPELL_MERCIFUL_STRIKES_HEAL, targets, total);
    }

    // The unit carrying `caster`'s Beacon of Light (one per caster: 53563 is ATTR5_LIMIT_N, so it sits in the
    // caster's single-cast list; a party scan is the fallback)
    Unit* FindBeaconTarget(Player* caster)
    {
        for (Aura* aura : caster->GetSingleCastAuras())
            if (aura->GetId() == PaladinData::SPELL_BEACON_OF_LIGHT)
                return aura->GetUnitOwner();

        if (Group* group = caster->GetGroup())
            for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player* member = ref->GetSource())
                    if (member->HasAura(PaladinData::SPELL_BEACON_OF_LIGHT, caster->GetGUID()))
                        return member;

        return nullptr;
    }

    // Divine Toll target pick (HOLY §6.2 step 2). The selected unit goes first if it matches the type (exempt from
    // the combat filter); auto-picked enemies must be in combat with the caster.
    std::vector<ObjectGuid> PickTollTargets(Player* caster, Paladin::ShockType type, Unit* selected)
    {
        float const range = Paladin::DIVINE_TOLL_RANGE;
        uint8 const maxTargets = Paladin::DIVINE_TOLL_MAX_TARGETS;
        std::vector<ObjectGuid> result;

        auto usable = [&](Unit* unit)
        {
            return unit && unit->IsAlive() && caster->IsWithinDist(unit, range) && caster->IsWithinLOSInMap(unit);
        };

        if (type == Paladin::ShockType::Heal)
        {
            bool const selectedOk = selected && caster->IsFriendlyTo(selected) && usable(selected);
            if (selectedOk)
                result.push_back(selected->GetGUID());

            std::vector<Unit*> candidates;
            // SelectMostInjured trims to `count` before the LoS filter, so over-ask and trim afterwards
            Heal::SelectMostInjured(caster, caster, range, TOLL_CANDIDATES, candidates,
                selectedOk ? selected : nullptr);
            for (Unit* unit : candidates)
            {
                if (result.size() >= maxTargets)
                    break;

                if (caster->IsWithinLOSInMap(unit))
                    result.push_back(unit->GetGUID());
            }

            return result;
        }

        bool const selectedOk = selected && caster->IsValidAttackTarget(selected) && usable(selected);
        if (selectedOk)
            result.push_back(selected->GetGUID());

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(caster, caster, range);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, range);

        std::vector<Unit*> enemies;
        for (Unit* unit : nearby)
            if ((!selectedOk || unit != selected) && caster->IsValidAttackTarget(unit) &&
                unit->IsInCombatWith(caster) && caster->IsWithinLOSInMap(unit))
                enemies.push_back(unit);

        std::sort(enemies.begin(), enemies.end(), [caster](Unit const* a, Unit const* b)
        {
            return caster->GetDistance(a) < caster->GetDistance(b);
        });

        for (Unit* unit : enemies)
        {
            if (result.size() >= maxTargets)
                break;

            result.push_back(unit->GetGUID());
        }

        return result;
    }

    Paladin::ShockType FlipShockType(Paladin::ShockType type)
    {
        return type == Paladin::ShockType::Heal ? Paladin::ShockType::Damage : Paladin::ShockType::Heal;
    }
}

// ===========================================================================================
// HOLY §6.1 - Holy Shock
// ===========================================================================================

// 20473 - Holy Shock (replaces stock spell_pal_holy_shock, unbound by WP-A)
class spell_pal_holy_shock_holy : public SpellScript
{
    PrepareSpellScript(spell_pal_holy_shock_holy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_SHOCK_25912, PaladinData::SPELL_HOLY_SHOCK_25914 });
    }

    SpellCastResult CheckCast()
    {
        // Stock check, unchanged: friendly targets always fine, enemies must be attackable and in front
        Unit* caster = GetCaster();
        if (Unit* target = GetExplTargetUnit())
        {
            if (!caster->IsFriendlyTo(target))
            {
                if (!caster->IsValidAttackTarget(target))
                    return SPELL_FAILED_BAD_TARGETS;

                if (!caster->isInFront(target))
                    return SPELL_FAILED_UNIT_NOT_INFRONT;
            }
        }
        else
            return SPELL_FAILED_BAD_TARGETS;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        bool const heal = caster->IsFriendlyTo(target);

        // Step 1: store the type before the triggered cast, so a missed Shock still sets Divine Toll's type
        if (Player* player = GetPlayerOrNull(caster))
            Paladin::SetLastShockType(player, heal ? Paladin::ShockType::Heal : Paladin::ShockType::Damage);

        // Step 2: the real heal / damage is the triggered pair; the resolver (201206) runs steps 3-5 on its hit
        caster->CastSpell(target, heal ? PaladinData::SPELL_HOLY_SHOCK_25914 : PaladinData::SPELL_HOLY_SHOCK_25912,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_pal_holy_shock_holy::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_pal_holy_shock_holy::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 25912, 25914 - Holy Shock damage / heal: Glimmer of Light rank 3 term (the done multiplier, Mastery read live)
class spell_pal_holy_shock_hit : public SpellScript
{
    PrepareSpellScript(spell_pal_holy_shock_hit);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_SHOCK_25914,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_TALENT_R3 });
    }

    void HandleHit()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3
        if (!player)
            return;

        float const mult = Paladin::GetGlimmerShockMultiplier(player);
        if (mult == 1.0f)
            return;

        // OnHit sees the value after done and %-taken mods and before crit, so a multiplier is exact
        if (GetSpellInfo()->Id == PaladinData::SPELL_HOLY_SHOCK_25914)
            SetHitHeal(int32(float(GetHitHeal()) * mult));
        else
            SetHitDamage(int32(float(GetHitDamage()) * mult));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_holy_shock_hit::HandleHit);
    }
};

// 201206 - Holy Shock (resolver): hidden passive, HIT-phase proc on 25912 / 25914 (HOLY §6.1 steps 3-5).
// Depends on NOT_A_PROC (0x200 AttributesEx3) staying on both Shock spells (HOLY §11 risk 2).
class spell_pal_holy_shock_resolver : public AuraScript
{
    PrepareAuraScript(spell_pal_holy_shock_resolver);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        // Reached through Paladin::ApplyGlimmer / PulseGlimmers / ApplyHolyGuidance / RunShockCastHooks
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_SHOCK_25912, PaladinData::SPELL_HOLY_SHOCK_25914,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_ALLY, PaladinData::SPELL_GLIMMER_OF_LIGHT_ENEMY,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_HEAL_PULSE, PaladinData::SPELL_GLIMMER_OF_LIGHT_DAMAGE_PULSE,
            PaladinData::SPELL_AWE, PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R1, PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R2,
            PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R3, PaladinData::SPELL_MERCIFUL_STRIKES_WINDOW_R1,
            PaladinData::SPELL_MERCIFUL_STRIKES_WINDOW_R2, PaladinData::SPELL_MERCIFUL_STRIKES_WINDOW_R3,
            PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R1, PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R2,
            PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R3, PaladinData::SPELL_HOLY_GUIDANCE_EXPOSED,
            PaladinData::SPELL_HOLY_GUIDANCE_GUIDED, PaladinData::SPELL_INFUSION_OF_LIGHT_53672,
            PaladinData::SPELL_INFUSION_OF_LIGHT_54149 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetProcOwner(GetTarget(), eventInfo);
        SpellInfo const* info = eventInfo.GetSpellInfo();
        if (!owner || !info || !eventInfo.GetActionTarget())
            return false;

        return info->Id == PaladinData::SPELL_HOLY_SHOCK_25912 || info->Id == PaladinData::SPELL_HOLY_SHOCK_25914;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* player = GetPlayerOrNull(GetTarget());
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        bool const heal = eventInfo.GetSpellInfo()->Id == PaladinData::SPELL_HOLY_SHOCK_25914;
        Paladin::ShockType const type = heal ? Paladin::ShockType::Heal : Paladin::ShockType::Damage;
        bool const crit = (eventInfo.GetHitMask() & PROC_HIT_CRITICAL) != 0;

        // Step 3 / 5: marker and Holy Guidance are target bound (a killing blow leaves a corpse: skipped)
        if (target->IsAlive())
            Paladin::ApplyGlimmer(player, target);

        // Step 4: every owned Glimmer pulses once
        Paladin::PulseGlimmers(player, crit, Paladin::GLIMMER_PULSE_PCT);

        if (target->IsAlive())
            Paladin::ApplyHolyGuidance(player, target, type);

        // Step 5: Dawn before Dusk, Merciful window, Shock and Awe, Infusion / Awe roll - once per Shock
        Paladin::RunShockCastHooks(player, type);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_holy_shock_resolver::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_holy_shock_resolver::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// HOLY §6.2 - Glimmer of Light and Divine Toll
// ===========================================================================================

// 201207, 201208 - Glimmer of Light markers (ally / enemy)
class spell_pal_glimmer_marker : public AuraScript
{
    PrepareAuraScript(spell_pal_glimmer_marker);

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // Every removal mode; the Paladin:: side is find-only (CR5) and never casts
        if (Unit* target = GetTarget())
            Paladin::OnGlimmerRemoved(GetCasterGUID(), target->GetGUID(), GetSpellInfo()->Id);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_glimmer_marker::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 201203 - Divine Toll
class spell_pal_divine_toll : public SpellScript
{
    PrepareSpellScript(spell_pal_divine_toll);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_DIVINE_TOLL_HEAL_SHOCK,
            PaladinData::SPELL_DIVINE_TOLL_DAMAGE_SHOCK, PaladinData::SPELL_BEACON_OF_LIGHT,
            SPELL_PAL_LIGHT_S_BEACON_AURA, SPELL_PAL_BEACON_OF_LIGHT_HS, PaladinData::SPELL_HOLY_SHOCK_25912,
            PaladinData::SPELL_HOLY_SHOCK_25914, PaladinData::SPELL_GLIMMER_OF_LIGHT_ALLY,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_ENEMY, PaladinData::SPELL_GLIMMER_OF_LIGHT_HEAL_PULSE,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_DAMAGE_PULSE, PaladinData::SPELL_HOLY_GUIDANCE_EXPOSED,
            PaladinData::SPELL_HOLY_GUIDANCE_GUIDED });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetPlayerOrNull(GetCaster()); // CR3
        if (!caster)
            return;

        // 201203 targets the caster (implicit 1): "selected" is the player's own selection, not the spell target
        Unit* selected = caster->GetSelectedUnit();

        // Step 1: the last Holy Shock's type; none yet -> the selected unit's type, else heal; flip if nobody fits
        Paladin::ShockType type = Paladin::GetLastShockType(caster);
        if (type == Paladin::ShockType::None)
            type = (selected && caster->IsValidAttackTarget(selected)) ? Paladin::ShockType::Damage
                                                                       : Paladin::ShockType::Heal;

        std::vector<ObjectGuid> targets = PickTollTargets(caster, type, selected);
        if (targets.empty())
        {
            type = FlipShockType(type);
            targets = PickTollTargets(caster, type, selected);
            if (targets.empty())
                return;
        }

        bool const heal = type == Paladin::ShockType::Heal;
        uint32 const carrier = heal ? PaladinData::SPELL_DIVINE_TOLL_HEAL_SHOCK
                                    : PaladinData::SPELL_DIVINE_TOLL_DAMAGE_SHOCK;
        size_t const count = targets.size();

        // Step 3: 10 Shocks round-robin; each target's first Shock is full strength and places Glimmer / Guidance
        bool anyLanded = false;
        bool firstCrit = false;
        int32 firstValue = 0;
        ObjectGuid firstGuid;
        for (uint8 i = 0; i < Paladin::DIVINE_TOLL_SHOCKS; ++i)
        {
            ObjectGuid const guid = targets[i % count];
            Unit* target = ObjectAccessor::GetUnit(*caster, guid);
            if (!target)
                continue;

            bool const first = i < count;
            bool const crit = Paladin::RollShockCrit(caster, target, type); // H2: every Shock rolls its own crit
            int32 value = Paladin::ComputeShockValue(caster, target, type, crit);
            if (!first)
                value = int32(float(value) * Paladin::DIVINE_TOLL_REPEAT_PCT / 100.0f);

            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT0, value);
            values.AddSpellMod(SPELLVALUE_FORCED_CRIT_RESULT, int32(crit));
            if (caster->CastCustomSpell(carrier, values, target, TRIGGERED_FULL_MASK) == SPELL_CAST_OK)
                anyLanded = true;

            if (i == 0)
            {
                firstCrit = crit;
                firstValue = value;
                firstGuid = guid;
            }

            if (first && target->IsAlive())
            {
                Paladin::ApplyGlimmer(caster, target);
                Paladin::ApplyHolyGuidance(caster, target, type);
            }
        }

        // Step 5: pulse once, at full value, with the first Shock's crit
        Paladin::PulseGlimmers(caster, firstCrit, Paladin::GLIMMER_PULSE_PCT);

        // Step 6: once-per-cast hooks, one seal stack if at least one Shock landed
        Paladin::RunShockCastHooks(caster, type);
        if (anyLanded)
            Paladin::AddSealStacks(caster, 1, PaladinData::SPELL_DIVINE_TOLL, false);

        // Beacon copies only the first Shock (heal type), skipping a Beacon target that is the first target itself
        if (heal && firstValue > 0)
            CastBeaconCopy(caster, firstGuid, firstValue);

        Paladin::SetLastShockType(caster, type);
    }

    static void CastBeaconCopy(Player* caster, ObjectGuid firstGuid, int32 firstValue)
    {
        Unit* first = ObjectAccessor::GetUnit(*caster, firstGuid);
        Unit* beaconTarget = FindBeaconTarget(caster);
        if (!first || !beaconTarget || beaconTarget == first || !beaconTarget->IsAlive())
            return;

        // The stock 60 yd area condition: the first target carries the beacon target's Light's Beacon
        if (!first->HasAura(SPELL_PAL_LIGHT_S_BEACON_AURA, beaconTarget->GetGUID()))
            return;

        SpellInfo const* beaconInfo = sSpellMgr->GetSpellInfo(PaladinData::SPELL_BEACON_OF_LIGHT);
        if (!beaconInfo)
            return;

        int32 const copy = CalculatePct(firstValue, beaconInfo->Effects[EFFECT_0].CalcValue());
        if (copy > 0)
            caster->CastCustomSpell(SPELL_PAL_BEACON_OF_LIGHT_HS, SPELLVALUE_BASE_POINT0, copy, beaconTarget,
                TRIGGERED_FULL_MASK, nullptr, nullptr, caster->GetGUID());
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pal_divine_toll::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// ===========================================================================================
// HOLY §6.3 - Light's Hammer (Rain of Fire / Consecration snapshot pattern)
// ===========================================================================================

// 201200 - Light's Hammer
class spell_pal_lights_hammer : public SpellScript
{
    PrepareSpellScript(spell_pal_lights_hammer);

    void RemoveExisting()
    {
        // One Light's Hammer per caster: a recast tears down the earlier ground effect first
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->RemoveDynObject(PaladinData::SPELL_LIGHT_S_HAMMER);
        caster->RemoveAurasDueToSpell(PaladinData::SPELL_LIGHT_S_HAMMER, caster->GetGUID());
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pal_lights_hammer::RemoveExisting);
    }
};

class spell_pal_lights_hammer_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_lights_hammer_aura);

    int32 _healSnapshot = 0;
    int32 _damageSnapshot = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_LIGHT_S_HAMMER_HEAL_TICK,
            PaladinData::SPELL_LIGHT_S_HAMMER_DAMAGE_TICK, PaladinData::SPELL_LIGHT_S_HAMMER_HEAL_SOURCE,
            PaladinData::SPELL_LIGHT_S_HAMMER_DAMAGE_SOURCE });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        // Both values frozen once from the hidden sources (they carry the potency and the LH bit, so Healing Light,
        // Illumination, spell power and every done mod are captured); the ticks are pure carriers
        SpellInfo const* healSource = sSpellMgr->GetSpellInfo(PaladinData::SPELL_LIGHT_S_HAMMER_HEAL_SOURCE);
        SpellInfo const* damageSource = sSpellMgr->GetSpellInfo(PaladinData::SPELL_LIGHT_S_HAMMER_DAMAGE_SOURCE);
        if (!healSource || !damageSource)
            return;

        int32 const healBase = healSource->Effects[EFFECT_0].CalcValue(caster);
        int32 const damageBase = damageSource->Effects[EFFECT_0].CalcValue(caster);
        _healSnapshot = int32(caster->SpellHealingBonusDone(caster, healSource, uint32(std::max(0, healBase)), HEAL,
            EFFECT_0));
        _damageSnapshot = int32(caster->SpellDamageBonusDone(caster, damageSource, uint32(std::max(0, damageBase)),
            SPELL_DIRECT_DAMAGE, EFFECT_0));
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        DynamicObject* dynObj = caster->GetDynObject(PaladinData::SPELL_LIGHT_S_HAMMER);
        if (!dynObj)
            return;

        // Partial final tick when hasted, same multiplier on both
        float const mult = aurEff->GetFinalTickBonusMultiplier();
        CastTick(caster, dynObj, PaladinData::SPELL_LIGHT_S_HAMMER_HEAL_TICK,
            int32(float(_healSnapshot) * mult), aurEff);
        CastTick(caster, dynObj, PaladinData::SPELL_LIGHT_S_HAMMER_DAMAGE_TICK,
            int32(float(_damageSnapshot) * mult), aurEff);
    }

    static void CastTick(Unit* caster, DynamicObject* dynObj, uint32 tickId, int32 amount, AuraEffect const* aurEff)
    {
        SpellInfo const* tickInfo = sSpellMgr->GetSpellInfo(tickId);
        if (!tickInfo)
            return;

        SpellCastTargets targets;
        targets.SetDst(*dynObj);

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, amount);

        caster->CastSpell(targets, tickInfo, &values, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(PaladinData::SPELL_LIGHT_S_HAMMER);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_lights_hammer_aura::HandleApply, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pal_lights_hammer_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_lights_hammer_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 201201 - Light's Hammer heal tick: party / raid only, most injured first (the engine's MaxTargets trim is a random
// resize that runs after this hook, so the hook resizes itself)
class spell_pal_lights_hammer_tick : public SpellScript
{
    PrepareSpellScript(spell_pal_lights_hammer_tick);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        targets.remove_if(Acore::RaidCheck(caster, false));
        targets.sort(Acore::HealthPctOrderPred());
        if (targets.size() > LIGHTS_HAMMER_TARGETS)
            targets.resize(LIGHTS_HAMMER_TARGETS);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_lights_hammer_tick::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ALLY);
    }
};

// ===========================================================================================
// HOLY §6.5 - other scripted clauses
// ===========================================================================================

// 20207 - Spiritual Focus rank 3 (capstone): damage taken while casting Holy Light buffs that Holy Light's crit
class spell_pal_spiritual_focus_capstone : public AuraScript
{
    PrepareAuraScript(spell_pal_spiritual_focus_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SPIRITUAL_FOCUS_CRIT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        if (!owner)
            return false;

        Spell* current = owner->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        if (!current || current->getState() != SPELL_STATE_PREPARING || !IsHolyLight(current->GetSpellInfo()))
            return false;

        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        return damageInfo && damageInfo->GetDamage() > 0;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        if (!owner)
            return;

        Spell* current = owner->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        if (!current)
            return;

        // The ICD (10 s) is the proc row's Cooldown; the buff only has to outlast this Holy Light's cast
        int32 const duration = current->GetCastTimeRemaining() + SPIRITUAL_FOCUS_SLACK_MS;
        owner->CastSpell(owner, PaladinData::SPELL_SPIRITUAL_FOCUS_CRIT, TRIGGERED_FULL_MASK);
        if (Aura* buff = owner->GetAura(PaladinData::SPELL_SPIRITUAL_FOCUS_CRIT, owner->GetGUID()))
        {
            buff->SetMaxDuration(duration);
            buff->SetDuration(duration);
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_spiritual_focus_capstone::CheckProc);
        OnProc += AuraProcFn(spell_pal_spiritual_focus_capstone::HandleProc);
    }
};

// 201246, 201247, 201248 - Illuminated Steel: melee crit = rank % of the spell crit gained from Intellect
class spell_pal_illuminated_steel : public AuraScript
{
    PrepareAuraScript(spell_pal_illuminated_steel);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = 0;
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player)
            return;

        // Effect 1 is the rank percent; read it from the spell data (the AuraEffect does not exist yet while
        // effect 0 is being calculated)
        int32 const pct = GetSpellInfo()->Effects[EFFECT_1].CalcValue(player);
        amount = int32(std::lround(float(pct) * Paladin::GetSpellCritFromIntellectOnly(player) / 100.0f));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_illuminated_steel::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_WEAPON_CRIT_PERCENT);
    }
};

// 201249, 201250, 201251 - Merciful Strikes (Crusader Strike half; Judgement's half is Paladin::OnJudgementCastHoly)
class spell_pal_merciful_strikes : public AuraScript
{
    PrepareAuraScript(spell_pal_merciful_strikes);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_MERCIFUL_STRIKES_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* player = GetPlayerOrNull(GetTarget());
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        AuraEffect const* healEff = aurEff->GetBase()->GetEffect(EFFECT_1);
        if (!player || !damageInfo || !healEff)
            return;

        CastMercifulHeal(player, CalculatePct(int32(damageInfo->GetDamage()), healEff->GetAmount()));
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_merciful_strikes::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_merciful_strikes::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201252, 201253 - Zealous Exorcism: melee crits cut Exorcism's remaining cooldown (real seconds)
class spell_pal_zealous_exorcism : public AuraScript
{
    PrepareAuraScript(spell_pal_zealous_exorcism);

    Spell const* _lastSpell = nullptr;
    uint32 _lastMs = 0;

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!GetProcOwner(GetTarget(), eventInfo))
            return false;

        // Once-per-cast guard: a multi-target melee spell cuts once per cast, not once per critted target
        // (auto attacks have no proc spell and always pass)
        Spell const* procSpell = eventInfo.GetProcSpell();
        if (!procSpell)
            return true;

        uint32 const now = uint32(GameTime::GetGameTimeMS().count());
        if (procSpell == _lastSpell && now == _lastMs)
            return false;

        _lastSpell = procSpell;
        _lastMs = now;
        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        Player* player = GetPlayerOrNull(GetTarget());
        if (player && aurEff->GetAmount() > 0 && player->HasSpellCooldown(PaladinData::SPELL_EXORCISM))
            player->ModifySpellCooldown(PaladinData::SPELL_EXORCISM, -aurEff->GetAmount());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_zealous_exorcism::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_zealous_exorcism::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 201232, 201233 - Sunlight hit / echo: rank scaling (33 / 66 / 100%) and the rank 3 echo
class spell_pal_sunlight_hit : public SpellScript
{
    PrepareSpellScript(spell_pal_sunlight_hit);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SUNLIGHT_ECHO, PaladinData::SPELL_SUNLIGHT_TALENT_R1,
            PaladinData::SPELL_SUNLIGHT_TALENT_R2, PaladinData::SPELL_SUNLIGHT_TALENT_R3 });
    }

    void HandleHit()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3
        if (!player)
            return;

        int32 const pct = Paladin::GetRankAmount(player, { PaladinData::SPELL_SUNLIGHT_TALENT_R3,
            PaladinData::SPELL_SUNLIGHT_TALENT_R2, PaladinData::SPELL_SUNLIGHT_TALENT_R1 }, EFFECT_1);
        if (pct > 0)
            SetHitDamage(CalculatePct(GetHitDamage(), pct));
    }

    void HandleAfterHit()
    {
        // The echo never echoes
        if (GetSpellInfo()->Id != PaladinData::SPELL_SUNLIGHT_HIT)
            return;

        Player* player = GetPlayerOrNull(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || !target->IsAlive() || !player->HasAura(PaladinData::SPELL_SUNLIGHT_TALENT_R3))
            return;

        if (Paladin::RollScriptedChance(player, SUNLIGHT_ECHO_CHANCE))
            player->CastSpell(target, PaladinData::SPELL_SUNLIGHT_ECHO, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_sunlight_hit::HandleHit);
        AfterHit += SpellHitFn(spell_pal_sunlight_hit::HandleAfterHit);
    }
};

// 1022, 1038, 1044, 6940 - Hand of Protection / Salvation / Freedom / Sacrifice: Blessed Hands capstone buff
// (additive to the stock Hand scripts)
class spell_pal_blessed_hands_capstone : public AuraScript
{
    PrepareAuraScript(spell_pal_blessed_hands_capstone);

    static constexpr uint32 HANDS[] = { PaladinData::SPELL_HAND_OF_PROTECTION, PaladinData::SPELL_HAND_OF_SALVATION,
        PaladinData::SPELL_HAND_OF_FREEDOM, PaladinData::SPELL_HAND_OF_SACRIFICE };

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BLESSED_HANDS_BUFF, PaladinData::SPELL_BLESSED_HANDS_TALENT_R3 });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* caster = GetPlayerOrNull(GetCaster());
        Unit* target = GetTarget();
        if (!caster || !target || !caster->HasAura(PaladinData::SPELL_BLESSED_HANDS_TALENT_R3))
            return;

        // Longest remaining Hand wins when a second Hand lands on the same target
        Aura const* existing = target->GetAura(PaladinData::SPELL_BLESSED_HANDS_BUFF, caster->GetGUID());
        int32 const previous = existing ? existing->GetDuration() : 0;

        caster->CastSpell(target, PaladinData::SPELL_BLESSED_HANDS_BUFF, TRIGGERED_FULL_MASK);
        if (Aura* buff = target->GetAura(PaladinData::SPELL_BLESSED_HANDS_BUFF, caster->GetGUID()))
        {
            int32 const duration = std::max(previous, GetAura()->GetDuration());
            buff->SetMaxDuration(duration);
            buff->SetDuration(duration);
        }
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target)
            return;

        // Another Hand from the same paladin keeps the buff alive
        ObjectGuid const casterGuid = GetCasterGUID();
        for (uint32 hand : HANDS)
            if (hand != GetSpellInfo()->Id && target->HasAura(hand, casterGuid))
                return;

        target->RemoveAurasDueToSpell(PaladinData::SPELL_BLESSED_HANDS_BUFF, casterGuid);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_blessed_hands_capstone::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_blessed_hands_capstone::HandleRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 4987, 1152 - Cleanse / Purify: Pure of Heart mana and the Sacred Cleansing capstone Glimmer
class spell_pal_cleanse_holy : public SpellScript
{
    PrepareSpellScript(spell_pal_cleanse_holy);

    uint32 _diseasePoisonBefore = 0;
    uint32 _allBefore = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_PURE_OF_HEART_MANA, PaladinData::SPELL_PURE_OF_HEART,
            PaladinData::SPELL_PURE_OF_HEART_31823, PaladinData::SPELL_PURE_OF_HEART_TALENT_R3,
            PaladinData::SPELL_SACRED_CLEANSING_53553, PaladinData::SPELL_GLIMMER_OF_LIGHT_ALLY,
            PaladinData::SPELL_GLIMMER_OF_LIGHT_ENEMY });
    }

    // No dispel hit-mask exists, hence a before / after count of stacks (or charges) of the negative dispellable
    // auras: a partial dispel (one stack of several) lowers the sum too
    static void Count(Unit const* target, uint32& diseasePoison, uint32& all)
    {
        diseasePoison = 0;
        all = 0;
        for (auto const& pair : target->GetAppliedAuras())
        {
            AuraApplication const* aurApp = pair.second;
            if (aurApp->IsPositive())
                continue;

            Aura const* aura = aurApp->GetBase();
            uint32 const weight = std::max<uint32>(1, aura->GetStackAmount() > 1 ? aura->GetStackAmount()
                                                                                  : aura->GetCharges());
            switch (aura->GetSpellInfo()->Dispel)
            {
                case DISPEL_DISEASE:
                case DISPEL_POISON:
                    diseasePoison += weight;
                    all += weight;
                    break;
                case DISPEL_MAGIC:
                    all += weight;
                    break;
                default:
                    break;
            }
        }
    }

    void HandleBeforeHit(SpellMissInfo /*missInfo*/)
    {
        if (Unit* target = GetHitUnit())
            Count(target, _diseasePoisonBefore, _allBefore);
    }

    void HandleAfterHit()
    {
        Player* caster = GetPlayerOrNull(GetCaster()); // CR3
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        uint32 diseasePoison = 0;
        uint32 all = 0;
        Count(target, diseasePoison, all);

        if (diseasePoison < _diseasePoisonBefore)
        {
            int32 const pct = Paladin::GetRankAmount(caster, { PaladinData::SPELL_PURE_OF_HEART_TALENT_R3,
                PaladinData::SPELL_PURE_OF_HEART_31823, PaladinData::SPELL_PURE_OF_HEART }, EFFECT_0);
            int32 const perSecond = CalculatePct(int32(caster->GetStat(STAT_INTELLECT)), pct);
            if (pct > 0 && perSecond > 0) // [TUNE] rank % x Intellect per second for 5 s; same caster refreshes
                caster->CastCustomSpell(PaladinData::SPELL_PURE_OF_HEART_MANA, SPELLVALUE_BASE_POINT0, perSecond,
                    caster, TRIGGERED_FULL_MASK);
        }

        // Sacred Cleansing capstone: Cleanse (only) that removed anything also places Glimmer (no pulse)
        if (GetSpellInfo()->Id == PaladinData::SPELL_CLEANSE && all < _allBefore &&
            caster->HasAura(PaladinData::SPELL_SACRED_CLEANSING_53553))
            Paladin::ApplyGlimmer(caster, target);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_pal_cleanse_holy::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_pal_cleanse_holy::HandleAfterHit);
    }
};

// 201260, 201261 - Light's Fervor: Holy Light / Flash of Light cut Holy Shock and Crusader Strike cooldowns;
// rank 2 also rolls Daybreak on Holy Light / Flash of Light / Crusader Strike
class spell_pal_lights_fervor : public AuraScript
{
    PrepareAuraScript(spell_pal_lights_fervor);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_SHOCK, PaladinData::SPELL_CRUSADER_STRIKE,
            PaladinData::SPELL_DAYBREAK, PaladinData::SPELL_LIGHT_S_FERVOR_R2 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* player = GetPlayerOrNull(GetTarget());
        SpellInfo const* info = eventInfo.GetSpellInfo();
        if (!player || !info)
            return;

        if (IsHolyLight(info) || IsFlashOfLight(info))
        {
            AuraEffect const* csEff = aurEff->GetBase()->GetEffect(EFFECT_1);
            if (aurEff->GetAmount() > 0 && player->HasSpellCooldown(PaladinData::SPELL_HOLY_SHOCK))
                player->ModifySpellCooldown(PaladinData::SPELL_HOLY_SHOCK, -aurEff->GetAmount());
            if (csEff && csEff->GetAmount() > 0 && player->HasSpellCooldown(PaladinData::SPELL_CRUSADER_STRIKE))
                player->ModifySpellCooldown(PaladinData::SPELL_CRUSADER_STRIKE, -csEff->GetAmount());
        }

        // Rank 2 capstone: Daybreak roll (Proc Chance applies)
        if (GetSpellInfo()->Id == PaladinData::SPELL_LIGHT_S_FERVOR_R2 &&
            Paladin::RollScriptedChance(player, DAYBREAK_CHANCE))
            player->CastSpell(player, PaladinData::SPELL_DAYBREAK, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_lights_fervor::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_lights_fervor::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 31833, 31835, 31836 - Light's Grace: Holy Light buffs the next Flash of Light, Flash of Light the next Holy Light
class spell_pal_lights_grace_holy : public AuraScript
{
    PrepareAuraScript(spell_pal_lights_grace_holy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R1, PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R2,
            PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R3, PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R1,
            PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R2, PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R3 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr;
    }

    uint8 GetRank()
    {
        switch (GetSpellInfo()->Id)
        {
            case PaladinData::SPELL_LIGHT_S_GRACE_31836: return 2;
            case PaladinData::SPELL_LIGHT_S_GRACE_31835: return 1;
            default: return 0;
        }
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5: else the default handler still casts the retired 31834

        Player* player = GetPlayerOrNull(GetTarget());
        SpellInfo const* info = eventInfo.GetSpellInfo();
        if (!player || !info)
            return;

        static constexpr uint32 FLASH_BUFFS[] = { PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R1,
            PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R2, PaladinData::SPELL_LIGHT_S_GRACE_FLASH_R3 };
        static constexpr uint32 HOLY_LIGHT_BUFFS[] = { PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R1,
            PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R2, PaladinData::SPELL_LIGHT_S_GRACE_HOLY_LIGHT_R3 };

        // Casting refreshes a live buff
        if (IsHolyLight(info))
            player->CastSpell(player, FLASH_BUFFS[GetRank()], TRIGGERED_FULL_MASK);
        else if (IsFlashOfLight(info))
            player->CastSpell(player, HOLY_LIGHT_BUFFS[GetRank()], TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_lights_grace_holy::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_lights_grace_holy::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201262, 201263, 201264 - Dawn before Dusk: Holy Light / Flash of Light casts add a stack (Holy Shock: resolver)
class spell_pal_dawn_before_dusk : public AuraScript
{
    PrepareAuraScript(spell_pal_dawn_before_dusk);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        // Paladin::AddDawnBeforeDuskStack picks the buff by rank
        return ValidateSpellInfo({ PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R1,
            PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R2, PaladinData::SPELL_DAWN_BEFORE_DUSK_BUFF_R3 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        // The crit was pre-rolled at launch, before this CAST-phase proc, so each cast reads the stacks it found
        if (Player* player = GetPlayerOrNull(GetTarget()))
            Paladin::AddDawnBeforeDuskStack(player);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_dawn_before_dusk::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_dawn_before_dusk::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 879 - Exorcism: Radiant Exorcism capstone cleave (beside S1's spell_pal_seal_builder)
class spell_pal_exorcism_radiant : public SpellScript
{
    PrepareSpellScript(spell_pal_exorcism_radiant);

    int32 _kept = 0;
    bool _cleaved = false;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_RADIANT_EXORCISM_CLEAVE,
            PaladinData::SPELL_RADIANT_EXORCISM_TALENT_R3 });
    }

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        // GetHitDamage() is post-done and post-taken: divide the main target's %-taken factor back out so the
        // cleave targets apply only their own taken mods
        float factor =
            float(target->SpellDamageBonusTaken(caster, GetSpellInfo(), 10000, SPELL_DIRECT_DAMAGE)) / 10000.0f;
        if (factor <= 0.0f)
            factor = 1.0f;

        _kept = int32(float(GetHitDamage()) / factor);
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3
        Unit* target = GetHitUnit();
        if (!player || !target || _cleaved || _kept <= 0 ||
            !player->HasAura(PaladinData::SPELL_RADIANT_EXORCISM_TALENT_R3))
            return;

        _cleaved = true;

        // Up to 2 other enemies near the target (a killing blow anchors on the corpse), nearest first
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(target, player, RADIANT_CLEAVE_RANGE);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(target, nearby, check);
        Cell::VisitObjects(target, searcher, RADIANT_CLEAVE_RANGE);

        std::vector<Unit*> enemies;
        for (Unit* unit : nearby)
            if (unit != target && player->IsValidAttackTarget(unit) && unit->IsInCombatWith(player))
                enemies.push_back(unit);

        std::sort(enemies.begin(), enemies.end(), [target](Unit const* a, Unit const* b)
        {
            return target->GetDistance(a) < target->GetDistance(b);
        });

        if (enemies.size() > RADIANT_CLEAVE_TARGETS)
            enemies.resize(RADIANT_CLEAVE_TARGETS);

        int32 const cleave = int32(float(_kept) * RADIANT_CLEAVE_PCT / 100.0f);
        for (Unit* enemy : enemies)
            player->CastCustomSpell(PaladinData::SPELL_RADIANT_EXORCISM_CLEAVE, SPELLVALUE_BASE_POINT0, cleave, enemy,
                TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_exorcism_radiant::HandleHit);
        AfterHit += SpellHitFn(spell_pal_exorcism_radiant::HandleAfterHit);
    }
};

// 201214, 201215, 201216 - Shock and Awe buffs: the threat reduction is off while Righteous Fury is up
class spell_pal_shock_and_awe_buff : public AuraScript
{
    PrepareAuraScript(spell_pal_shock_and_awe_buff);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        if (caster && caster->HasAura(PaladinData::SPELL_RIGHTEOUS_FURY))
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_shock_and_awe_buff::CalculateAmount, EFFECT_1,
            SPELL_AURA_MOD_THREAT);
    }
};

// 25780 - Righteous Fury (additive to the fork class): re-evaluate a live Shock and Awe buff on apply / remove
class spell_pal_righteous_fury_shock_and_awe : public AuraScript
{
    PrepareAuraScript(spell_pal_righteous_fury_shock_and_awe);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R1, PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R2,
            PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R3 });
    }

    void Recalculate(AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target)
            return;

        for (uint32 buffId : { PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R1, PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R2,
                               PaladinData::SPELL_SHOCK_AND_AWE_BUFF_R3 })
            if (Aura* buff = target->GetAura(buffId))
                if (AuraEffect* eff = buff->GetEffect(EFFECT_1))
                    eff->RecalculateAmount();
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes mode)
    {
        Recalculate(mode);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes mode)
    {
        // The removed aura is already out of the unit's applied map, so HasAura(25780) reads false here
        Recalculate(mode);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_righteous_fury_shock_and_awe::HandleApply, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_righteous_fury_shock_and_awe::HandleRemove, EFFECT_0,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 201274, 201275, 201276 - Overflowing Light: a Holy Light / Flash of Light crit splashes onto the most injured
// ally near the target; rank 3 also cuts Lay on Hands on Holy Light crits
class spell_pal_overflowing_light : public AuraScript
{
    PrepareAuraScript(spell_pal_overflowing_light);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_OVERFLOWING_LIGHT_SPLASH, PaladinData::SPELL_LAY_ON_HANDS,
            PaladinData::SPELL_OVERFLOWING_LIGHT_TALENT_R3 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* player = GetPlayerOrNull(GetTarget());
        SpellInfo const* info = eventInfo.GetSpellInfo();
        HealInfo* healInfo = eventInfo.GetHealInfo();
        Unit* procTarget = eventInfo.GetActionTarget();
        if (!player || !info || !healInfo || !procTarget)
            return;

        int32 const splash = CalculatePct(int32(healInfo->GetHeal()), aurEff->GetAmount());
        if (splash > 0)
        {
            std::vector<Unit*> allies;
            Heal::SelectMostInjured(player, procTarget, OVERFLOWING_LIGHT_RANGE, 1, allies, procTarget);
            if (!allies.empty() && !allies.front()->IsFullHealth())
                player->CastCustomSpell(PaladinData::SPELL_OVERFLOWING_LIGHT_SPLASH, SPELLVALUE_BASE_POINT0, splash,
                    allies.front(), TRIGGERED_FULL_MASK);
        }

        // Rank 3 capstone: Holy Light crits cut Lay on Hands (real seconds)
        if (GetSpellInfo()->Id == PaladinData::SPELL_OVERFLOWING_LIGHT_TALENT_R3 && IsHolyLight(info) &&
            player->HasSpellCooldown(PaladinData::SPELL_LAY_ON_HANDS))
            player->ModifySpellCooldown(PaladinData::SPELL_LAY_ON_HANDS, -OVERFLOWING_LAY_ON_HANDS_MS);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_overflowing_light::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_overflowing_light::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 53569, 53576 - Infusion of Light (replaces stock spell_pal_infusion_of_light, unbound by WP-A): the Flash of Light
// HoT on a target with Sacred Shield. The Shock roll that grants 53672 / 54149 is in Paladin::RunShockCastHooks.
class spell_pal_infusion_of_light_holy : public AuraScript
{
    PrepareAuraScript(spell_pal_infusion_of_light_holy);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SACRED_SHIELD, SPELL_PAL_FLASH_OF_LIGHT_HOT });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return GetProcOwner(GetTarget(), eventInfo) != nullptr && IsFlashOfLight(eventInfo.GetSpellInfo());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5: else every Flash heal would cast the old trigger 53672 / 54149

        Player* player = GetPlayerOrNull(GetTarget());
        HealInfo* healInfo = eventInfo.GetHealInfo();
        Unit* procTarget = eventInfo.GetActionTarget();
        AuraEffect const* hotEff = aurEff->GetBase()->GetEffect(EFFECT_1); // the HoT percent
        if (!player || !healInfo || !healInfo->GetHeal() || !procTarget || !hotEff)
            return;

        // Any caster's Sacred Shield on the target qualifies
        if (!procTarget->HasAura(PaladinData::SPELL_SACRED_SHIELD))
            return;

        SpellInfo const* hotInfo = sSpellMgr->GetSpellInfo(SPELL_PAL_FLASH_OF_LIGHT_HOT);
        int32 const duration = hotInfo ? hotInfo->GetMaxDuration() / 1000 : 0;
        if (duration <= 0)
            return;

        int32 const perTick = CalculatePct(int32(healInfo->GetHeal()) / duration, hotEff->GetAmount());
        if (perTick > 0)
            player->CastCustomSpell(SPELL_PAL_FLASH_OF_LIGHT_HOT, SPELLVALUE_BASE_POINT0, perTick, procTarget,
                TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_infusion_of_light_holy::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_infusion_of_light_holy::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

void AddSC_paladin_holy_spell_scripts()
{
    RegisterSpellScript(spell_pal_holy_shock_holy);
    RegisterSpellScript(spell_pal_holy_shock_hit);
    RegisterSpellScript(spell_pal_holy_shock_resolver);
    RegisterSpellScript(spell_pal_glimmer_marker);
    RegisterSpellScript(spell_pal_divine_toll);
    RegisterSpellAndAuraScriptPair(spell_pal_lights_hammer, spell_pal_lights_hammer_aura);
    RegisterSpellScript(spell_pal_lights_hammer_tick);
    RegisterSpellScript(spell_pal_spiritual_focus_capstone);
    RegisterSpellScript(spell_pal_illuminated_steel);
    RegisterSpellScript(spell_pal_merciful_strikes);
    RegisterSpellScript(spell_pal_zealous_exorcism);
    RegisterSpellScript(spell_pal_sunlight_hit);
    RegisterSpellScript(spell_pal_blessed_hands_capstone);
    RegisterSpellScript(spell_pal_cleanse_holy);
    RegisterSpellScript(spell_pal_lights_fervor);
    RegisterSpellScript(spell_pal_lights_grace_holy);
    RegisterSpellScript(spell_pal_dawn_before_dusk);
    RegisterSpellScript(spell_pal_exorcism_radiant);
    RegisterSpellScript(spell_pal_shock_and_awe_buff);
    RegisterSpellScript(spell_pal_righteous_fury_shock_and_awe);
    RegisterSpellScript(spell_pal_overflowing_light);
    RegisterSpellScript(spell_pal_infusion_of_light_holy);
}
