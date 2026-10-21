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

#ifndef SCRIPT_OBJECT_UNIT_SCRIPT_H_
#define SCRIPT_OBJECT_UNIT_SCRIPT_H_

#include "ScriptObject.h"
#include <vector>

enum UnitHook
{
    UNITHOOK_ON_HEAL,
    UNITHOOK_ON_DAMAGE,
    UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
    UNITHOOK_MODIFY_MELEE_DAMAGE,
    UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
    UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL,
    UNITHOOK_ON_MELEE_DAMAGE_FINAL,
    UNITHOOK_ON_PERIODIC_DAMAGE_FINAL,
    UNITHOOK_ON_HEAL_FINAL,
    UNITHOOK_ON_ABSORB_FINAL,
    UNITHOOK_ON_MELEE_OUTCOME_FINAL,
    UNITHOOK_MODIFY_HEAL_RECEIVED,
    UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST,
    UNITHOOK_ON_AURA_APPLY,
    UNITHOOK_ON_AURA_REMOVE,
    UNITHOOK_IF_NORMAL_REACTION,
    UNITHOOK_CAN_SET_PHASE_MASK,
    UNITHOOK_IS_CUSTOM_BUILD_VALUES_UPDATE,
    UNITHOOK_SHOULD_TRACK_VALUES_UPDATE_POS_BY_INDEX,
    UNITHOOK_ON_PATCH_VALUES_UPDATE,
    UNITHOOK_ON_UNIT_UPDATE,
    UNITHOOK_ON_DISPLAYID_CHANGE,
    UNITHOOK_ON_UNIT_ENTER_EVADE_MODE,
    UNITHOOK_ON_UNIT_ENTER_COMBAT,
    UNITHOOK_ON_UNIT_EXIT_COMBAT,
    UNITHOOK_ON_UNIT_DEATH,
    UNITHOOK_ON_UNIT_SET_SHAPESHIFT_FORM,
    UNITHOOK_END
};

enum ReputationRank : uint8;
class AuraEffect;
class ByteBuffer;
struct BuildValuesCachePosPointers;
struct CalcDamageInfo;

class UnitScript : public ScriptObject
{
protected:
    UnitScript(char const* name, bool addToScripts = true, std::vector<uint16> enabledHooks = std::vector<uint16>());

public:
    // Called when a unit deals healing to another unit
    virtual void OnHeal(Unit* /*healer*/, Unit* /*reciever*/, uint32& /*gain*/) { }

    // Called when a unit deals damage to another unit
    virtual void OnDamage(Unit* /*attacker*/, Unit* /*victim*/, uint32& /*damage*/) { }

    // Called when DoT's Tick Damage is being Dealt
    // Attacker can be nullptr if he is despawned while the aura still exists on target
    virtual void ModifyPeriodicDamageAurasTick(Unit* /*target*/, Unit* /*attacker*/, uint32& /*damage*/, SpellInfo const* /*spellInfo*/) { }

    // Called when Melee Damage is being Dealt
    virtual void ModifyMeleeDamage(Unit* /*target*/, Unit* /*attacker*/, uint32& /*damage*/) { }

    // Called when Spell Damage is being Dealt
    virtual void ModifySpellDamageTaken(Unit* /*target*/, Unit* /*attacker*/, int32& /*damage*/, SpellInfo const* /*spellInfo*/) { }

    // Called from Unit::CalculateSpellDamageTaken() once `damage` has its final, landed value -
    // after per-class mitigation (armor reduction, crit bonus, block/resilience) but before
    // absorb/resist accounting. Unlike ModifySpellDamageTaken above (which fires *before* that
    // mitigation, so scripts can influence it), `damage` here is not by-reference: this hook is
    // purely observational, not a modification point. Added so a crit-aware damage observer (e.g.
    // mod-dpssim's EventRecorder) can read a hit's true, multiplier-applied value - fires upstream
    // of Unit::DealDamage, so unlike OnDamage it isn't affected by a target's own DamageTaken() AI
    // potentially zeroing `damage` first (see SimTarget's class comment for a concrete example).
    virtual void OnSpellDamageTakenFinal(Unit* /*target*/, Unit* /*attacker*/, int32 /*damage*/, SpellInfo const* /*spellInfo*/, bool /*isCrit*/) { }

    // Custom: the melee (auto-attack) twin of OnSpellDamageTakenFinal - fires from
    // Unit::CalculateMeleeDamage with a swing's total after armor, the crit/glancing/crushing/block outcome and
    // resilience, before absorb/resist. Purely observational, for mod-dpssim's EventRecorder: ModifyMeleeDamage
    // fires before armor and the outcome roll, and OnDamage can't tell a swing from a spell.
    virtual void OnMeleeDamageFinal(Unit* /*target*/, Unit* /*attacker*/, uint32 /*damage*/, bool /*isCrit*/) { }

    // Custom: the periodic (DoT tick) twin of OnSpellDamageTakenFinal - fires from
    // AuraEffect::HandlePeriodicDamageAurasTick and HandlePeriodicHealthLeechAuraTick with a tick's amount after
    // crit, armor and resilience, with absorb/resist added back (pre-absorb, like the other two *Final hooks).
    // Purely observational, for mod-dpssim's EventRecorder: ModifyPeriodicDamageAurasTick fires before crit and
    // mitigation. `attacker` can be nullptr if the caster despawned while the aura still exists on the target.
    virtual void OnPeriodicDamageFinal(Unit* /*target*/, Unit* /*attacker*/, uint32 /*damage*/, SpellInfo const* /*spellInfo*/, bool /*isCrit*/) { }

    // Custom: the healing twin of OnSpellDamageTakenFinal - fires once per heal event from Unit::HealBySpell (direct
    // heals; also the health leech and health funnel tick heals, which reach it with `isPeriodic` false),
    // AuraEffect::HandlePeriodicHealAurasTick (HoT ticks, `isPeriodic` true) and the leech-stat heal in
    // Unit::DealDamage, after crit and every healing modifier. `heal` is the amount before heal-absorb, `effective` is what landed on the
    // target (capped by missing health) and `healAbsorbed` is what a heal-absorb aura took, so
    // overheal = heal - effective - healAbsorbed. `healer` can be nullptr if the caster despawned while the aura
    // still exists on the target. `spellInfo` is nullptr only for a melee auto-attack's leech heal
    // (SPELL_AURA_MOD_LEECH_PCT). Purely observational, for mod-dpssim's heal mode: OnHeal has no spell, no crit and
    // only the effective amount, and ModifyHealReceived fires before heal-absorb and the other modifiers.
    virtual void OnHealFinal(Unit* /*healer*/, Unit* /*target*/, SpellInfo const* /*spellInfo*/, uint32 /*heal*/, uint32 /*effective*/, uint32 /*healAbsorbed*/, bool /*isCrit*/, bool /*isPeriodic*/) { }

    // Custom: fires from Unit::CalcAbsorbResist right after a school-absorb or mana-shield aura took `absorbed` (> 0)
    // out of an incoming hit. The shield's caster (for attribution) is absorbAurEff->GetCasterGUID(); the effect is
    // still valid during the call (an exhausted shield is removed afterwards). `attacker` can be nullptr. Purely
    // observational, for mod-dpssim's heal mode, which counts absorbed damage as healing done by the shield's caster.
    virtual void OnAbsorbFinal(Unit* /*victim*/, Unit* /*attacker*/, AuraEffect const* /*absorbAurEff*/, uint32 /*absorbed*/) { }

    // Custom: fires from Unit::CalculateMeleeDamage right after OnMeleeDamageFinal, with the whole swing: hitOutCome,
    // TargetState (VICTIMSTATE_BLOCKS = full block), blocked_amount, cleanDamage (armor + block + avoided) and each
    // damage index's final damage/absorb/resist. Absorbs have already fired OnAbsorbFinal by this point. Purely
    // observational, for mod-dpssim's tank mode: OnMeleeDamageFinal has no outcome, block or mitigation split.
    virtual void OnMeleeOutcomeFinal(CalcDamageInfo const* /*damageInfo*/) { }

    // Called when Heal is Recieved
    virtual void ModifyHealReceived(Unit* /*target*/, Unit* /*healer*/, uint32& /*heal*/, SpellInfo const* /*spellInfo*/) { }

    //Called when Damage is Dealt
    virtual uint32 DealDamage(Unit* /*AttackerUnit*/, Unit* /*pVictim*/, uint32 damage, DamageEffectType /*damagetype*/) { return damage; }

    virtual void OnBeforeRollMeleeOutcomeAgainst(Unit const* /*attacker*/, Unit const* /*victim*/, WeaponAttackType /*attType*/, int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/, int32& /*attackerWeaponSkill*/, int32& /*victimDefenseSkill*/, int32& /*crit_chance*/, int32& /*miss_chance*/, int32& /*dodge_chance*/, int32& /*parry_chance*/, int32& /*block_chance*/ ) {   };

    virtual void OnAuraApply(Unit* /*unit*/, Aura* /*aura*/) { }

    virtual void OnAuraRemove(Unit* /*unit*/, AuraApplication* /*aurApp*/, AuraRemoveMode /*mode*/) { }

    [[nodiscard]] virtual bool IfNormalReaction(Unit const* /*unit*/, Unit const* /*target*/, ReputationRank& /*repRank*/) { return true; }

    [[nodiscard]] virtual bool CanSetPhaseMask(Unit const* /*unit*/, uint32 /*newPhaseMask*/, bool /*update*/) { return true; }

    [[nodiscard]] virtual bool IsCustomBuildValuesUpdate(Unit const* /*unit*/, uint8 /*updateType*/, ByteBuffer& /*fieldBuffer*/, Player const* /*target*/, uint16 /*index*/) { return false; }

    [[nodiscard]] virtual bool ShouldTrackValuesUpdatePosByIndex(Unit const* /*unit*/, uint8 /*updateType*/, uint16 /*index*/) { return false; }

    virtual void OnPatchValuesUpdate(Unit const* /*unit*/, ByteBuffer& /*valuesUpdateBuf*/, BuildValuesCachePosPointers& /*posPointers*/, Player* /*target*/) { }

    /**
     * @brief This hook runs in Unit::Update
     *
     * @param unit Contains information about the Unit
     * @param diff Contains information about the diff time
     */
    virtual void OnUnitUpdate(Unit* /*unit*/, uint32 /*diff*/) { }

    virtual void OnDisplayIdChange(Unit* /*unit*/, uint32 /*displayId*/) { }

    virtual void OnUnitEnterEvadeMode(Unit* /*unit*/, uint8 /*evadeReason*/) { }
    virtual void OnUnitEnterCombat(Unit* /*unit*/, Unit* /*victim*/) { }
    virtual void OnUnitExitCombat(Unit* /*unit*/) { }
    virtual void OnUnitDeath(Unit* /*unit*/, Unit* /*killer*/) { }
    virtual void OnUnitSetShapeshiftForm(Unit* /*unit*/, uint8 /*form*/) { }
};

#endif
