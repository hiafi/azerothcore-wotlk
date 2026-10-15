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
 * Hunter rework - pet spell scripts (hunter-rework.SHARED.md §A4 / §C4).
 * Skeleton created by stage T2; H0-P1 adds Bloodthirsty (PET.md 7.5) and Web Pull (PET.md 8.3).
 */

#include "Creature.h"
#include "HunterMechanics.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

enum HunterPetSpells
{
    SPELL_HUN_DEATH_GRIP_JUMP = 57604 // stock Death Grip jump, not in the hunter DSL
};

// 53186, 53187 - Bloodthirsty (PET.md 7.5)
// Bound on both rank ids (no rank chain exists for pet spells). The aura's caster is the pet, so spell_proc applies
// no Proc Chance; the roll goes through Hunter::RollProcChance. Effect 0 still triggers the heal (54131).
class spell_hun_pet_bloodthirsty : public AuraScript
{
    PrepareAuraScript(spell_hun_pet_bloodthirsty);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_BLOODTHIRSTY_54131 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || damageInfo->GetDamage() == 0)
            return false;

        Unit* pet = GetUnitOwner();
        if (!pet || !pet->IsAlive() || eventInfo.GetActor() != pet)
            return false;

        // CR3: only a hunter's pet acts
        Player* owner = Hunter::GetOwningPlayer(pet);
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return false;

        // Effect 1 is a plain DUMMY (not an aura effect), so the aura has no AuraEffect for it: read the spell's value.
        float const chance = float(GetSpellInfo()->Effects[EFFECT_1].CalcValue(pet));
        return Hunter::RollProcChance(pet, chance);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_pet_bloodthirsty::CheckProc);
    }
};

// 201718 - Web Pull (PET.md 8.3)
class spell_hun_pet_web_pull : public SpellScript
{
    PrepareSpellScript(spell_hun_pet_web_pull);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_HUN_DEATH_GRIP_JUMP });
    }

    SpellCastResult CheckCast()
    {
        // CR3 / L6: gate here so a non-hunter pet pays no cooldown for a no-op
        Player* owner = Hunter::GetOwningPlayer(GetCaster());
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return SPELL_FAILED_DONT_REPORT;

        Unit* target = GetExplTargetUnit();
        if (!target)
            return SPELL_FAILED_BAD_TARGETS;

        // Death Grip's boss rule (spell_dk.cpp)
        if (Creature* creature = target->ToCreature())
            if (creature->isWorldBoss() || creature->IsDungeonBoss())
                return SPELL_FAILED_BAD_TARGETS;

        if (Player* player = target->ToPlayer())
            if (player->InArena() || player->InBattleground())
                return SPELL_FAILED_BAD_TARGETS;

        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* pet = GetCaster();
        Unit* target = GetHitUnit();
        if (!pet || !target || pet == target || !pet->IsAlive() || !target->IsAlive())
            return;

        // L6: the target may have died or turned friendly since the cast started
        if (!pet->IsValidAttackTarget(target))
            return;

        SpellInfo const* gripJump = sSpellMgr->GetSpellInfo(SPELL_HUN_DEATH_GRIP_JUMP);
        if (!gripJump)
            return;

        // Deterrence (deflect) stops the pull, as it does for Death Grip
        if (target->HasDetectSpellsAura() && !target->HasUnitState(UNIT_STATE_STUNNED))
            return;

        // Interrupt like Death Grip (immunity is checked against the Rogue Kick, as there)
        if (!target->IsImmunedToSpellEffect(sSpellMgr->GetSpellInfo(1766), EFFECT_0))
            target->InterruptNonMeleeSpells(false, 0, false);

        // Land just in front of the pet: its reach plus the target's, with a small margin
        float const dist = pet->GetCombatReach() + target->GetCombatReach() + 1.0f;
        Position const dest = pet->GetFirstCollisionPosition(dist, 0.0f);
        target->CastSpell(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), SPELL_HUN_DEATH_GRIP_JUMP, true);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_hun_pet_web_pull::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_hun_pet_web_pull::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

void AddSC_hunter_pet_spell_scripts()
{
    RegisterSpellScript(spell_hun_pet_bloodthirsty);
    RegisterSpellScript(spell_hun_pet_web_pull);
}
