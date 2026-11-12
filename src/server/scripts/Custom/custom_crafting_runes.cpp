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

// Custom: crafting rework C7 boss runes (.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decision 6b,
// rulings 6.4 and 2026-11-12; data in apps/dbc-tools/lib/crafting_consumables_data.py). Inscription makes three runes.
// Used on a boss (a dungeon boss or a world/raid boss; a 3 s cast at 60 yd that pulls nothing), a rune gives the user a
// 24 hour buff against that boss: every creature of the selected boss's entry, so every pull of it that day. The three
// share a 24 hour cooldown (the spells' category), so a rune is for pushing one boss, not every boss.
//
// - Rune of Empowerment (208900): the user's damage to the selected boss +N%.
// - Rune of Warding (208901): damage the selected boss deals to the user -N%.
// - Rune of Mending (208902): the user's healing +N% while in combat with the selected boss (EFFECT_2, a healing done
//   percent aura the one second tick switches between N and 0).
//
// N is the spell's EFFECT_1 value. After the cast EFFECT_1's amount holds the selected boss's creature entry and is
// marked not recalculated, so it is saved with the aura and survives logout and death.

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
    enum BossRune : uint32
    {
        SPELL_RUNE_OF_EMPOWERMENT = 208900,
        SPELL_RUNE_OF_WARDING     = 208901,
        SPELL_RUNE_OF_MENDING     = 208902,
    };

    bool IsBoss(Unit const* unit)
    {
        Creature const* creature = unit ? unit->ToCreature() : nullptr;
        return creature && !creature->IsPet() && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    // The selected boss entry of `unit`'s `runeSpell` aura (0 when it has none or the cast never selected one), and
    // the rune's percent.
    uint32 SelectedBoss(Unit const* unit, uint32 runeSpell, int32& pct)
    {
        AuraEffect const* effect = unit->GetAuraEffect(runeSpell, EFFECT_1);
        if (!effect || effect->CanBeRecalculated())
            return 0;
        pct = effect->GetSpellInfo()->Effects[EFFECT_1].CalcValue();
        return uint32(effect->GetAmount());
    }

    bool IsSelected(Unit const* player, uint32 runeSpell, Unit const* boss, int32& pct)
    {
        Creature const* creature = boss ? boss->ToCreature() : nullptr;
        return creature && !creature->GetOwnerGUID().IsPlayer() &&
            SelectedBoss(player, runeSpell, pct) == creature->GetEntry();
    }

    // Empowerment on the attacker's side, then Warding on the target's: the damage after both.
    uint32 RuneDamage(Unit const* target, Unit const* attacker, uint32 damage)
    {
        int64 result = damage;
        int32 pct = 0;
        if (Player const* player = attacker->GetCharmerOrOwnerPlayerOrPlayerItself())
            if (IsSelected(player, SPELL_RUNE_OF_EMPOWERMENT, target, pct))
                result += CalculatePct(result, pct);
        if (Player const* player = target->ToPlayer())
            if (IsSelected(player, SPELL_RUNE_OF_WARDING, attacker, pct))
                result -= CalculatePct(result, pct);
        return uint32(std::max<int64>(0, result));
    }

    bool InCombatWith(Unit* unit, uint32 entry)
    {
        for (auto const& [guid, ref] : unit->GetCombatManager().GetPvECombatRefs())
            if (Unit* other = ref->GetOther(unit); other && other->GetEntry() == entry && other->IsCreature())
                return true;
        return false;
    }
}

// 208900, 208901, 208902 - the boss runes
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

    // Every second: Rune of Mending's healing aura is on only while the user fights the selected boss.
    void HandleTick(AuraEffect const* aurEff)
    {
        if (GetId() != SPELL_RUNE_OF_MENDING || aurEff->CanBeRecalculated())
            return;
        AuraEffect* healing = GetAura()->GetEffect(EFFECT_2);
        if (!healing)
            return;
        int32 const want = InCombatWith(GetTarget(), uint32(aurEff->GetAmount()))
            ? aurEff->GetSpellInfo()->Effects[EFFECT_1].CalcValue() : 0;
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
