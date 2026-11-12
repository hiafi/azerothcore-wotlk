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
// ruling 6.4; data in apps/dbc-tools/lib/crafting_consumables_data.py). Inscription makes three runes. Used on a boss
// (a dungeon boss or a world/raid boss), a rune binds to that creature: the player's aura lasts until the boss dies or
// resets (at most an hour) and works only against it. One bound rune per player; the three share a 24 hour cooldown
// (the spells' category), so a rune is for pushing one boss, not every boss.
//
// - Rune of Ruin (208900): the player's damage to the bound boss +N%.
// - Rune of Warding (208901): damage the bound boss deals to the player -N%.
// - Rune of Mending (208902): the player's healing +N% while the bound boss is in combat.
// N is the aura's EFFECT_1 amount (the periodic dummy that also checks the boss every second).

#include "Creature.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <unordered_map>

namespace
{
    enum BossRune : uint32
    {
        SPELL_RUNE_OF_RUIN    = 208900,
        SPELL_RUNE_OF_WARDING = 208901,
        SPELL_RUNE_OF_MENDING = 208902,
    };

    // Player -> the boss its rune is bound to. Filled by the rune's hit, cleared when the aura goes.
    std::unordered_map<ObjectGuid, ObjectGuid> BoundBoss;

    bool IsBoss(Unit const* unit)
    {
        Creature const* creature = unit ? unit->ToCreature() : nullptr;
        return creature && !creature->IsPet() && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    // The percent of `player`'s `runeSpell` aura when it is bound to `boss`, else 0.
    int32 RunePct(Player const* player, uint32 runeSpell, Unit const* boss = nullptr)
    {
        AuraEffect const* effect = player->GetAuraEffect(runeSpell, EFFECT_1);
        if (!effect)
            return 0;
        auto itr = BoundBoss.find(player->GetGUID());
        if (itr == BoundBoss.end() || (boss && itr->second != boss->GetGUID()))
            return 0;
        return effect->GetAmount();
    }

    Player const* RuneOwner(Unit const* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    // Rune of Ruin on the attacker's side, then Rune of Warding on the target's: the damage after both.
    uint32 RuneDamage(Unit const* target, Unit const* attacker, uint32 damage)
    {
        int64 result = damage;
        if (IsBoss(target))
            if (Player const* player = RuneOwner(attacker))
                if (int32 pct = RunePct(player, SPELL_RUNE_OF_RUIN, target))
                    result += CalculatePct(result, pct);
        if (Player const* player = target->ToPlayer(); player && IsBoss(attacker))
            if (int32 pct = RunePct(player, SPELL_RUNE_OF_WARDING, attacker))
                result -= CalculatePct(result, pct);
        return uint32(std::max<int64>(0, result));
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
        {
            return SPELL_FAILED_BAD_TARGETS;
        }
        return SPELL_CAST_OK;
    }

    void HandleBind(SpellEffIndex /*effIndex*/)
    {
        if (Unit* target = GetHitUnit())
            BoundBoss[GetCaster()->GetGUID()] = target->GetGUID();
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_crafting_boss_rune::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_crafting_boss_rune::HandleBind, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

class spell_crafting_boss_rune_aura : public AuraScript
{
    PrepareAuraScript(spell_crafting_boss_rune_aura);

    // Every second: the boss must still be there, alive and not resetting.
    void HandleTick(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetTarget();
        auto itr = BoundBoss.find(owner->GetGUID());
        Creature* boss = itr != BoundBoss.end() ? ObjectAccessor::GetCreature(*owner, itr->second) : nullptr;
        if (!boss || !boss->IsAlive() || boss->IsInEvadeMode())
            Remove(AURA_REMOVE_BY_EXPIRE);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        BoundBoss.erase(GetTarget()->GetGUID());
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_crafting_boss_rune_aura::HandleTick, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_crafting_boss_rune_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

class custom_crafting_boss_rune_damage : public UnitScript
{
public:
    custom_crafting_boss_rune_damage() : UnitScript("custom_crafting_boss_rune_damage", true,
        { UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
          UNITHOOK_MODIFY_HEAL_RECEIVED }) { }

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

    void ModifyHealReceived(Unit* /*target*/, Unit* healer, uint32& heal, SpellInfo const* /*spellInfo*/) override
    {
        Player const* player = RuneOwner(healer);
        if (!player || BoundBoss.empty())
            return;
        int32 const pct = RunePct(player, SPELL_RUNE_OF_MENDING);
        if (!pct)
            return;
        auto itr = BoundBoss.find(player->GetGUID());
        Creature const* boss = ObjectAccessor::GetCreature(*player, itr->second);
        if (boss && boss->IsAlive() && boss->IsInCombat())
            heal += CalculatePct(heal, pct);
    }

private:
    static void Modify(Unit* target, Unit* attacker, uint32& damage)
    {
        if (!BoundBoss.empty() && target && attacker && damage)
            damage = RuneDamage(target, attacker, damage);
    }
};

void AddSC_custom_crafting_runes()
{
    RegisterSpellAndAuraScriptPair(spell_crafting_boss_rune, spell_crafting_boss_rune_aura);
    new custom_crafting_boss_rune_damage();
}
