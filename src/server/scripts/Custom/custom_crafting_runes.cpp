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

// Custom: crafting rework C7 Rune of Empowerment (.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decision
// 6b, rulings 6.4 and 2026-11-12; data in apps/dbc-tools/lib/crafting_consumables_data.py). Inscription makes it. Used
// on a boss (a dungeon boss or a world/raid boss; a 3 s cast at 60 yd that pulls nothing), it gives the user a 24 hour
// buff against that boss: every creature of the selected boss's entry, so every pull of it that day. A 24 hour
// cooldown (the spell's category) makes it a tool for pushing one boss, not every boss. Each role uses its part:
//
// - EFFECT_0's value: damage the selected boss deals to the user -N%;
// - EFFECT_1's value: the user's damage to the selected boss +N%;
// - EFFECT_2: healing done +N% while the user is in combat with the selected boss (the one second tick switches the
//   aura between its value and 0).
//
// After the cast EFFECT_1's amount holds the selected boss's creature entry and is marked not recalculated, so it is
// saved with the aura and survives logout and death.

#include "CombatManager.h"
#include "Creature.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>

namespace
{
    constexpr uint32 SPELL_RUNE_OF_EMPOWERMENT = 208900;

    bool IsBoss(Unit const* unit)
    {
        Creature const* creature = unit ? unit->ToCreature() : nullptr;
        return creature && !creature->IsPet() && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    // The rune aura's EFFECT_1 once the cast has stored the selected boss in it, else nullptr.
    AuraEffect const* RuneEffect(Unit const* unit)
    {
        AuraEffect const* effect = unit ? unit->GetAuraEffect(SPELL_RUNE_OF_EMPOWERMENT, EFFECT_1) : nullptr;
        return effect && !effect->CanBeRecalculated() ? effect : nullptr;
    }

    bool IsSelected(AuraEffect const* effect, Unit const* boss)
    {
        Creature const* creature = boss ? boss->ToCreature() : nullptr;
        return creature && !creature->GetOwnerGUID().IsPlayer() && uint32(effect->GetAmount()) == creature->GetEntry();
    }

    // The damage after the attacker's rune (more damage to its boss) and the target's (less damage from its boss).
    uint32 RuneDamage(Unit const* target, Unit const* attacker, uint32 damage)
    {
        int64 result = damage;
        if (AuraEffect const* effect = RuneEffect(attacker->GetCharmerOrOwnerPlayerOrPlayerItself()))
            if (IsSelected(effect, target))
                result += CalculatePct(result, effect->GetSpellInfo()->Effects[EFFECT_1].CalcValue());
        if (AuraEffect const* effect = RuneEffect(target->ToPlayer()))
            if (IsSelected(effect, attacker))
                result -= CalculatePct(result, effect->GetSpellInfo()->Effects[EFFECT_0].CalcValue());
        return uint32(std::max<int64>(0, result));
    }

    bool InCombatWith(Unit* unit, uint32 entry)
    {
        for (auto const& [guid, ref] : unit->GetCombatManager().GetPvECombatRefs())
            if (Unit* other = ref->GetOther(unit); other && other->IsCreature() && other->GetEntry() == entry)
                return true;
        return false;
    }
}

// 208900 - Rune of Empowerment
class spell_crafting_boss_rune : public SpellScript
{
    PrepareSpellScript(spell_crafting_boss_rune);

    SpellCastResult CheckCast()
    {
        if (!GetCaster()->IsPlayer())
            return SPELL_FAILED_DONT_REPORT;
        Unit* target = GetExplTargetUnit();
        if (!IsBoss(target) || !target->IsAlive())
            return SPELL_FAILED_BAD_TARGETS;
        _bossEntry = target->GetEntry();
        return SPELL_CAST_OK;
    }

    // Store the selected boss in the user's aura (EFFECT_1), kept through logout.
    void HandleAfterCast()
    {
        AuraEffect* effect = GetCaster()->GetAuraEffect(GetSpellInfo()->Id, EFFECT_1);
        if (!effect || !_bossEntry)
            return;
        effect->ChangeAmount(int32(_bossEntry));
        effect->SetCanBeRecalculated(false);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_crafting_boss_rune::CheckCast);
        AfterCast += SpellCastFn(spell_crafting_boss_rune::HandleAfterCast);
    }

private:
    uint32 _bossEntry = 0;
};

class spell_crafting_boss_rune_aura : public AuraScript
{
    PrepareAuraScript(spell_crafting_boss_rune_aura);

    // Every second: the healing part is on only while the user fights the selected boss.
    void HandleTick(AuraEffect const* aurEff)
    {
        AuraEffect* healing = GetAura()->GetEffect(EFFECT_2);
        if (!healing)
            return;
        bool const fighting = !aurEff->CanBeRecalculated() && InCombatWith(GetTarget(), uint32(aurEff->GetAmount()));
        int32 const want = fighting ? GetSpellInfo()->Effects[EFFECT_2].CalcValue() : 0;
        if (healing->GetAmount() != want)
            healing->ChangeAmount(want);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_crafting_boss_rune_aura::HandleTick, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

class custom_crafting_boss_rune_damage : public UnitScript
{
public:
    custom_crafting_boss_rune_damage() : UnitScript("custom_crafting_boss_rune_damage", true,
        { UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
          UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK }) { }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        Modify(target, attacker, damage);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* /*spellInfo*/) override
    {
        if (damage > 0)
        {
            uint32 amount = uint32(damage);
            Modify(target, attacker, amount);
            damage = int32(amount);
        }
    }

    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
        SpellInfo const* /*spellInfo*/) override
    {
        Modify(target, attacker, damage);
    }

private:
    static void Modify(Unit* target, Unit* attacker, uint32& damage)
    {
        if (target && attacker && damage)
            damage = RuneDamage(target, attacker, damage);
    }
};

void AddSC_custom_crafting_runes()
{
    RegisterSpellAndAuraScriptPair(spell_crafting_boss_rune, spell_crafting_boss_rune_aura);
    new custom_crafting_boss_rune_damage();
}
