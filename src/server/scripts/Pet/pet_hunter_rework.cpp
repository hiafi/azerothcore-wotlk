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
 * Hunter rework - pet creature scripts (hunter-rework.SHARED.md §A4 / §B11 / §C4).
 */

#include "CombatManager.h"
#include "Containers.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PetDefines.h"
#include "ScriptedCreature.h"
#include "ScriptMgr.h"
#include "TemporarySummon.h"
#include <algorithm>

// Snake Trap snake health (§B11, §0.10): the snakes take the hunter's level, so the stock formula underflows below 41.
constexpr float SNAKE_HEALTH_PER_LEVEL = 1.34f;
constexpr int32 SNAKE_HEALTH_LEVEL_OFFSET = 20;
constexpr uint32 SNAKE_MIN_HEALTH = 10;

enum HunterSnakeTrapReworkSpells
{
    SPELL_SNAKE_CRIPPLING_POISON       = 30981, // Viper
    SPELL_SNAKE_DEADLY_POISON_PASSIVE  = 34657, // Venomous Snake
    SPELL_SNAKE_MIND_NUMBING_POISON    = 25810, // Viper
    SPELL_SNAKE_GLYPH_OF_SNAKE_TRAP    = 56849,
    SPELL_SNAKE_PET_SCALING            = 62915
};

// Copy of stock npc_pet_hunter_snake_trap (pet_hunter.cpp, never edited) with three changes only: the health formula,
// ApplyOwnerSting, and nothing else (the stock target rule stays; no free roaming).
struct npc_pet_hunter_snake_trap_rework : public ScriptedAI
{
    npc_pet_hunter_snake_trap_rework(Creature* creature) : ScriptedAI(creature), _isViper(false), _spellTimer(0) { }

    void JustEngagedWith(Unit* /*who*/) override { }

    void InitializeAI() override
    {
        _isViper = me->GetEntry() == NPC_VIPER;

        // Clamp in float first: converting a negative float to uint32 is undefined behaviour.
        me->SetMaxHealth(uint32(std::max(float(SNAKE_MIN_HEALTH),
            SNAKE_HEALTH_PER_LEVEL * float(int32(me->GetLevel()) - SNAKE_HEALTH_LEVEL_OFFSET))));
        me->SetFullHealth();
        // Add delta to make them not all hit the same time
        me->SetAttackTime(BASE_ATTACK, me->GetAttackTime(BASE_ATTACK) + urandms(0, 6));

        if (!_isViper && !me->HasAura(SPELL_SNAKE_DEADLY_POISON_PASSIVE))
            DoCast(me, SPELL_SNAKE_DEADLY_POISON_PASSIVE, true);

        // Glyph of Snake Trap - apply AoE damage reduction scaling
        if (Unit* owner = me->GetOwner())
            if (owner->GetAuraEffectDummy(SPELL_SNAKE_GLYPH_OF_SNAKE_TRAP))
                me->CastSpell(me, SPELL_SNAKE_PET_SCALING, true);
    }

    // Redefined for random target selection:
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Hook for S3 (Q15): the hunter's Serpent Sting with the hunter as original caster, inside Trap Mastery's Snake
    // Trap clause, Survival only. Empty in H0; S3 fills it and decides where the snake's attack calls it.
    void ApplyOwnerSting(Unit* /*victim*/) { }

    void UpdateAI(uint32 diff) override
    {
        if (me->GetVictim() && me->GetVictim()->HasBreakableByDamageCrowdControlAura(me))
        {
            me->GetThreatMgr().ClearFixate();
            me->InterruptNonMeleeSpells(false);
            me->AttackStop();
            return;
        }

        if (me->IsSummon() && !me->GetThreatMgr().GetFixateTarget())
        {
            Unit* summoner = me->ToTempSummon()->GetSummonerUnit();
            if (summoner)
            {
                std::vector<Unit*> targets;

                auto addTargetIfValid = [this, &targets, summoner](CombatReference* ref) mutable
                {
                    Unit* enemy = ref->GetOther(summoner);
                    if (!enemy->HasBreakableByDamageCrowdControlAura(me) && me->CanCreatureAttack(enemy) &&
                        me->IsWithinDistInMap(enemy, me->GetAttackDistance(enemy)))
                        targets.push_back(enemy);
                };

                for (auto const& [guid, ref] : summoner->GetCombatManager().GetPvPCombatRefs())
                    addTargetIfValid(ref);

                if (targets.empty())
                    for (auto const& [guid, ref] : summoner->GetCombatManager().GetPvECombatRefs())
                        addTargetIfValid(ref);

                for (Unit* target : targets)
                    me->EngageWithTarget(target);

                if (!targets.empty())
                {
                    Unit* target = Acore::Containers::SelectRandomContainerElement(targets);
                    me->GetThreatMgr().FixateTarget(target);
                }
            }
        }

        if (!UpdateVictim())
            return;

        // Viper
        if (_isViper)
        {
            if (_spellTimer <= diff)
            {
                if (!urand(0, 2)) // 33% chance to cast
                    DoCastVictim(RAND(SPELL_SNAKE_MIND_NUMBING_POISON, SPELL_SNAKE_CRIPPLING_POISON));

                _spellTimer = 3000;
            }
            else
                _spellTimer -= diff;
        }

        DoMeleeAttackIfReady();
    }

private:
    bool _isViper;
    uint32 _spellTimer;
};

enum HunterStampedeBeastData
{
    DATA_STAMPEDE_TARGET = 0 // SetGUID id: the Stampede cast's target (spell_hun_stampede)
};

// 300200-300207 - Stampede beasts (BEAST-MASTERY.md §4.6, PET.md §9.1). SummonProperties 1021 guardians summoned by
// spell_hun_stampede through Map::SummonCreature. Melee only, explicit targeting, deaf to pet commands and
// Kill Command. The three guardian traps (docs/bugs-and-fixes.md):
// - "Infernal walks back to the warlock...": "when replacing a moving generator with MoveChase, stop the old spline,
//   or a chase that starts in range will ride it off." -> StopMoving() before every MoveChase, and no follow motion
//   is ever issued (no MoveFollow anywhere, not even without a target).
// - "A guardian given MoveChase never leaves its owner...": "any scripted MoveChase needs GetVictim() to equal the
//   chase target." -> Attack(target, true) before MoveChase, and again whenever the victim was cleared.
// - "A plain summoned Creature can't attack faction-neutral targets...": "Explicitly
//   me->SetUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED) on the summon (e.g. in its IsSummonedBy override)." A 1021 Guardian
//   already gets it from SetMinion; setting it again is harmless.
struct npc_hun_stampede_beast : public CreatureAI
{
    explicit npc_hun_stampede_beast(Creature* creature) : CreatureAI(creature) { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        // Guardian::InitStats ends with SetReactState(REACT_AGGRESSIVE); InitSummon (this hook) runs after it.
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED);
        // No MoveFollow/MoveChase here: UpdateAI picks the target and starts the chase.
    }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id == DATA_STAMPEDE_TARGET)
            _targetGUID = guid;
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (Unit* target = ResolveTarget())
        {
            if (me->GetVictim() != target && me->Attack(target, true))
            {
                me->StopMoving();
                me->GetMotionMaster()->MoveChase(target);
            }
        }
        else if (me->GetVictim())
            me->AttackStop();

        DoMeleeAttackIfReady();
    }

private:
    bool IsUsableTarget(Unit* unit) const
    {
        return unit && unit->IsAlive() && me->IsInMap(unit) && me->IsValidAttackTarget(unit);
    }

    // The stored Stampede target, else the owner's victim, else the owner's pet's victim. Re-resolved every tick.
    Unit* ResolveTarget() const
    {
        if (!_targetGUID.IsEmpty())
            if (Unit* stored = ObjectAccessor::GetUnit(*me, _targetGUID))
                if (IsUsableTarget(stored))
                    return stored;

        Unit* owner = me->GetOwner();
        if (!owner)
            return nullptr;

        if (Unit* ownerVictim = owner->GetVictim())
            if (IsUsableTarget(ownerVictim))
                return ownerVictim;

        if (Unit* pet = ObjectAccessor::GetUnit(*owner, owner->GetPetGUID()))
            if (Unit* petVictim = pet->GetVictim())
                if (IsUsableTarget(petVictim))
                    return petVictim;

        return nullptr;
    }

    ObjectGuid _targetGUID;
};

void AddSC_hunter_rework_pet_scripts()
{
    RegisterCreatureAI(npc_pet_hunter_snake_trap_rework);
    RegisterCreatureAI(npc_hun_stampede_beast);
}
