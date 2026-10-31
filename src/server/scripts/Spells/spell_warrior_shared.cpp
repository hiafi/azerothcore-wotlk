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
 * Warrior rework - shared SpellScripts (warrior-rework W0b; docs/reworks/warrior-shared-rework.md). Bodies that bots
 * or the core also need live in WarriorMechanics / LeapMechanics.
 */

#include "GameTime.h"
#include "LeapMechanics.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "MovementTypedefs.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "Unit.h"
#include "WarriorMechanics.h"
#include <algorithm>
#include <cmath>
#include <list>

namespace
{
    // Stock rows the forked Charge script casts (stock spell_warrior.cpp names them the same way).
    constexpr uint32 SPELL_CHARGE_RAGE_ENERGIZE = 34846;

    // Custom: warrior-rework S2 (D13). Juggernaut's Charge condition: farther than this or a target above this health.
    constexpr float JUGGERNAUT_CHARGE_MIN_DISTANCE_YD = 20.0f;
    constexpr float JUGGERNAUT_CHARGE_MIN_TARGET_HEALTH_PCT = 90.0f;

    // Numerical guard for the leap's horizontal speed (a zero distance would give a zero-speed spline); the spell's
    // 8 yd minimum range keeps real leaps far above it.
    constexpr float LEAP_MIN_DISTANCE_YD = 1.0f;

    // The landing slam fires only when the warrior is this close to the leap point (review R2).
    constexpr float LEAP_LANDING_SLACK_YD = 5.0f;
}

// -100 - Charge (fork of stock spell_warr_charge, which is unbound from -100). D4 / D5: usable in combat; in combat
// the rage is Warrior::ChargeCombatRage(distance at cast), out of combat stock's effect 1 value. Distance and combat
// state are read in OnCast, before the CHARGE effect's launch moves the caster. Refused while Heroic Leap's flight
// aura is up (D7: a CHARGE cast mid-leap would replace the jump spline).
// Custom: warrior-rework S2: both branches carry the effect-2 spell mods (Improved Charge's and Anger Management's
// flat ALL_EFFECTS rage, D12 / D24 / C4); the in-combat figure is run through Unit::ApplyEffectModifiers, the very
// call that builds GetEffectValue(). Anger Management's capstone buff is cast on every Charge (D12), and Juggernaut
// (D13) is granted at the cast when the charge is longer than 20 yd or the target is above 90% health.
class spell_warr_charge_rework : public SpellScript
{
    PrepareSpellScript(spell_warr_charge_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_CHARGE_RAGE_ENERGIZE, WarriorData::SPELL_LEAPING });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (caster && caster->HasAura(WarriorData::SPELL_LEAPING))
            return SPELL_FAILED_MOVING;

        return SPELL_CAST_OK;
    }

    void HandleCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !target)
            return;

        // GetDistance is edge to edge (combat reaches removed), the metric the spell's 8-25 yd range is checked with.
        _distance = caster->GetDistance(target);
        _inCombat = caster->IsInCombat();

        // Custom: warrior-rework S2 (D13): the grant rolls the rank chance inside Warrior::GrantJuggernaut.
        Player* player = caster->ToPlayer();
        if (player && (_distance > JUGGERNAUT_CHARGE_MIN_DISTANCE_YD ||
            target->GetHealthPct() > JUGGERNAUT_CHARGE_MIN_TARGET_HEALTH_PCT))
            Warrior::GrantJuggernaut(player);
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        int32 chargeBasePoints0 = GetEffectValue();
        if (_inCombat)
        {
            // Custom: warrior-rework S2 (C4): the in-combat figure ignored every spell mod; GetEffectValue() is
            // CalcValue + ApplyEffectModifiers on effect 1 (ALL_EFFECTS then EFFECT2), so run the same call on it.
            chargeBasePoints0 = int32(std::lround(caster->ApplyEffectModifiers(GetSpellInfo(), EFFECT_1,
                float(Warrior::ChargeCombatRage(_distance)))));
        }

        caster->CastCustomSpell(caster, SPELL_CHARGE_RAGE_ENERGIZE, &chargeBasePoints0, nullptr, nullptr, true);

        // Custom: warrior-rework S2 (D12): Anger Management's capstone buff on every Charge.
        if (Player* player = caster->ToPlayer())
            Warrior::GrantAngerManagementCapstone(player);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warr_charge_rework::CheckCast);
        OnCast += SpellCastFn(spell_warr_charge_rework::HandleCast);
        OnEffectHitTarget += SpellEffectFn(spell_warr_charge_rework::HandleDummy, EFFECT_1, SPELL_EFFECT_DUMMY);
    }

    float _distance = 0.0f;
    bool _inCombat = false;
};

// 3411 - Intervene (replaces stock spell_warr_intervene, which is unbound: no 59667 threat drop, D6). Refuses the
// caster as its own target and refuses while Heroic Leap's flight aura is up (D7).
class spell_warr_intervene_rework : public SpellScript
{
    PrepareSpellScript(spell_warr_intervene_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_LEAPING });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return SPELL_CAST_OK;

        Unit* target = GetExplTargetUnit();
        if (!target || target == caster)
            return SPELL_FAILED_BAD_TARGETS;

        if (caster->HasAura(WarriorData::SPELL_LEAPING))
            return SPELL_FAILED_MOVING;

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warr_intervene_rework::CheckCast);
    }
};

// 34428 - Victory Rush, the heal (bound next to stock spell_warr_victory_rush, which keeps removing Victorious). D14: a
// hidden HEAL_PCT helper cast on the caster once per cast, not an effect of 34428 itself (a self-targeted effect would
// make the caster a second target of the strike: bug log "Arcane Blast grants 2 stacks"). Only a landed strike heals
// (user 2026-10-29): effect handlers run only on a hit target, unlike AfterCast / AfterHit, which also run on a miss.
class spell_warr_victory_rush_heal : public SpellScript
{
    PrepareSpellScript(spell_warr_victory_rush_heal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_VICTORY_RUSH_204409 });
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            caster->CastSpell(caster, WarriorData::SPELL_VICTORY_RUSH_204409, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_warr_victory_rush_heal::HandleHit, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 204400 - Heroic Leap: a DUMMY on the clicked ground point (A 28) and a MoveJump there (P0 item 3 shape: air time
// HEROIC_LEAP_AIR_MS whatever the distance, apex HEROIC_LEAP_APEX_YD). The flight aura 204402 is up while airborne;
// at arrival the landing 204401 is cast triggered on the point. CheckCast order (D7, D10): rooted, charging (Charge or
// Intervene moving the warrior), already leaping, then the point must be landable (Leap::IsLandablePoint).
class spell_warr_heroic_leap : public SpellScript
{
    PrepareSpellScript(spell_warr_heroic_leap);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_HEROIC_LEAP_204401, WarriorData::SPELL_LEAPING });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return SPELL_CAST_OK;

        // The core refuses a rooted caster only for CHARGE / JUMP effects.
        if (caster->HasUnitState(UNIT_STATE_ROOT))
            return SPELL_FAILED_ROOTED;

        if (caster->HasUnitState(UNIT_STATE_CHARGING))
            return SPELL_FAILED_MOVING;

        if (caster->HasAura(WarriorData::SPELL_LEAPING))
            return SPELL_FAILED_MOVING;

        WorldLocation const* dest = GetExplTargetDest();
        if (!dest)
            return SPELL_FAILED_BAD_TARGETS;

        if (!Leap::IsLandablePoint(caster, dest->GetPositionX(), dest->GetPositionY(), dest->GetPositionZ()))
            return SPELL_FAILED_NOPATH;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        WorldLocation const* dest = GetHitDest();
        if (!player || !dest)
            return;

        float const x = dest->GetPositionX();
        float const y = dest->GetPositionY();
        float const z = dest->GetPositionZ();
        float const distance = player->GetExactDist(x, y, z);
        float const speedXY = std::max(distance, LEAP_MIN_DISTANCE_YD) * 1000.0f /
            float(WarriorData::HEROIC_LEAP_AIR_MS);
        float const speedZ = float(std::sqrt(2.0 * Movement::gravity * double(WarriorData::HEROIC_LEAP_APEX_YD)));

        // As the core jump and charge effects: the fall starts at the launch height, not wherever an earlier fall did.
        player->SetFallInformation(GameTime::GetGameTime().count(), player->GetPositionZ());
        player->AddAura(WarriorData::SPELL_LEAPING, player);
        player->SetCanTeleport(true);
        sScriptMgr->AnticheatSetUnderACKmount(player);
        player->GetMotionMaster()->MoveJump(x, y, z, speedXY, speedZ);

        // The controlled slot is the top one, so the spline is launched inside MoveJump; land when it ends.
        int32 const airMs = player->movespline->Finalized() ? int32(WarriorData::HEROIC_LEAP_AIR_MS) :
            std::max<int32>(player->movespline->Duration(), 1);

        ObjectGuid const playerGuid = player->GetGUID();
        uint32 const mapId = player->GetMapId();
        uint32 const instanceId = player->GetInstanceId();
        player->m_Events.AddEventAtOffset([playerGuid, mapId, instanceId, x, y, z]()
        {
            Player* warrior = ObjectAccessor::FindPlayer(playerGuid);
            if (!warrior || warrior->GetMapId() != mapId || warrior->GetInstanceId() != instanceId)
                return;

            warrior->RemoveAurasDueToSpell(WarriorData::SPELL_LEAPING);
            if (!warrior->IsAlive())
                return;

            // Something ended the jump early (a fear, a knockback, a teleport): no slam at a point the warrior is not
            // at. 5 yd allows for the event firing the tick before the spline finishes.
            if (warrior->GetExactDist(x, y, z) > LEAP_LANDING_SLACK_YD)
                return;

            // triggered = TRIGGERED_FULL_MASK; the landing row has 50000 yd range (script-cast, D9).
            warrior->CastSpell(x, y, z, WarriorData::SPELL_HEROIC_LEAP_204401, true);
        }, Milliseconds(airMs));
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_warr_heroic_leap::CheckCast);
        OnEffectHit += SpellEffectFn(spell_warr_heroic_leap::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 204405 - Skull Banner: eff0 summons the Alliance banner 300370 by data; a Horde caster's summon is replaced by the
// helper 204408 (the Horde banner 300371) at the same point (D12). eff1 (A 56, 40 yd) buffs every player in range at
// the moment of the cast who is neither Rallied nor already buffed; A 56 selects pets through their owner, so
// non-players are dropped (D13). Buff and Rallied go on with AddAura (bug 1067; P0 item 4 shape).
class spell_warr_skull_banner : public SpellScript
{
    PrepareSpellScript(spell_warr_skull_banner);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ WarriorData::SPELL_SKULL_BANNER_204406, WarriorData::SPELL_RALLIED,
            WarriorData::SPELL_SKULL_BANNER_204408 });
    }

    void HandleSummon(SpellEffIndex effIndex)
    {
        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        WorldLocation const* dest = GetHitDest();
        if (!player || !dest || player->GetTeamId() != TEAM_HORDE)
            return;

        PreventHitDefaultEffect(effIndex);
        player->CastSpell(dest->GetPositionX(), dest->GetPositionY(), dest->GetPositionZ(),
            WarriorData::SPELL_SKULL_BANNER_204408, true);
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if([](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            if (!unit || !unit->IsPlayer())
                return true;

            return unit->HasAura(WarriorData::SPELL_RALLIED) || unit->HasAura(WarriorData::SPELL_SKULL_BANNER_204406);
        });
    }

    void HandleBuff(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        caster->AddAura(WarriorData::SPELL_SKULL_BANNER_204406, target);
        target->AddAura(WarriorData::SPELL_RALLIED, target);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_warr_skull_banner::HandleSummon, EFFECT_0, SPELL_EFFECT_SUMMON);
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_warr_skull_banner::FilterTargets, EFFECT_1,
            TARGET_UNIT_CASTER_AREA_RAID);
        OnEffectHitTarget += SpellEffectFn(spell_warr_skull_banner::HandleBuff, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

void AddSC_warrior_shared_spell_scripts()
{
    RegisterSpellScript(spell_warr_charge_rework);
    RegisterSpellScript(spell_warr_intervene_rework);
    RegisterSpellScript(spell_warr_victory_rush_heal);
    RegisterSpellScript(spell_warr_heroic_leap);
    RegisterSpellScript(spell_warr_skull_banner);
}
