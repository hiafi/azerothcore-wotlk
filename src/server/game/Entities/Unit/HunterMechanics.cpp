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

#include "HunterMechanics.h"
#include "Config.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "Unit.h"
#include <algorithm>

/*
 * Hunter rework - shared mechanics (hunter-rework.SHARED.md §A5, §C4). Stage T2 holds the T2 block only.
 */
namespace Hunter
{
    bool StingsStack(SpellInfo const* a, SpellInfo const* b)
    {
        return a && b && a->GetSpellSpecific() == SPELL_SPECIFIC_STING && b->GetSpellSpecific() == SPELL_SPECIFIC_STING;
    }

    Player* GetOwningPlayer(Unit* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    Player const* GetOwningPlayer(Unit const* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    float GetProcChanceMultiplier(Unit const* unit)
    {
        Player const* owner = GetOwningPlayer(unit);
        return owner ? 1.0f + owner->GetProcChancePercentage() / 100.0f : 1.0f;
    }

    bool RollProcChance(Unit const* unit, float baseChancePct)
    {
        return roll_chance_f(baseChancePct * GetProcChanceMultiplier(unit));
    }

    void ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms)
    {
        if (!player || !ms)
            return;

        player->ModifySpellCooldown(spellId, -int32(ms));
    }

    bool IsClasslessRealm()
    {
        static bool const value = sConfigMgr->GetOption<bool>("Custom.Realm.Classless", false);
        return value;
    }

    void EnsureNoAmmoAura(Player* player)
    {
        if (!player || player->HasAura(SPELL_REQUIRES_NO_AMMO))
            return;

        // 46699 is passive and hidden, so addSpell applies the aura and nothing shows in the spellbook.
        if (!player->HasSpell(SPELL_REQUIRES_NO_AMMO))
            player->addSpell(SPELL_REQUIRES_NO_AMMO, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, SPELL_REQUIRES_NO_AMMO, true);
    }

    void ClearState(Player* /*player*/)
    {
        // Later sections add their Clear*State calls here; removal paths use find-only map access.
    }

    bool IsAspectRollSource(SpellInfo const* spellInfo)
    {
        // Hand literal until H0-P declares it: PET's strike (declared by H0-P).
        constexpr uint32 SPELL_PET_STRIKE = 201705;
        // d1 b28: every pet-cast family-9 spell carries it (SHARED §A3).
        constexpr uint32 FAMILY_FLAG1_PET_ABILITY = 0x10000000;

        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_HUNTER ||
            spellInfo->DmgClass != SPELL_DAMAGE_CLASS_RANGED)
            return false;

        // SUPPRESS_CASTER_PROCS spells (Silencing Shot, proc damage) never roll (SHARED §B6.2); the CAST-phase proc
        // call does not honour the attribute, so it is checked here.
        if (spellInfo->HasAttribute(SPELL_ATTR3_SUPPRESS_CASTER_PROCS))
            return false;

        if (spellInfo->IsPassive() || (spellInfo->SpellFamilyFlags[1] & FAMILY_FLAG1_PET_ABILITY))
            return false;

        if (spellInfo->Id == SPELL_KILL_COMMAND || spellInfo->Id == SPELL_PET_STRIKE)
            return false;

        for (SpellEffectInfo const& effect : spellInfo->Effects)
        {
            switch (effect.Effect)
            {
                case SPELL_EFFECT_SCHOOL_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                case SPELL_EFFECT_WEAPON_PERCENT_DAMAGE:
                    return true;
                case SPELL_EFFECT_APPLY_AURA:
                    if (effect.ApplyAuraName == SPELL_AURA_PERIODIC_DAMAGE)
                        return true;
                    break;
                default:
                    break;
            }
        }

        return false;
    }

    Unit* GetProcTarget(ProcEventInfo& eventInfo)
    {
        if (Unit* target = eventInfo.GetActionTarget())
            return target;

        // CAST phase: no action target yet, fall back to the proc spell's explicit unit target.
        if (Spell const* spell = eventInfo.GetProcSpell())
            return spell->m_targets.GetUnitTarget();

        return nullptr;
    }

    void OnDirectFireHit(Unit* /*attacker*/, Unit* /*target*/, SpellInfo const* /*spellInfo*/)
    {
        // Empty in H0; S3 fills the body (contract in HunterMechanics.h, SURVIVAL §0.23).
        // Callers S3 keeps in a list here: Tarred 202048's OnEffectProc (53301 hit, 202045 impact, 202051 first
        // blast, 13812 blast) and the AfterHit of every suppressed Fire source (201601 from H0; 202052, 202053,
        // 202054 from S3).
    }

    float GetShotManaPct(Unit const* caster, SpellInfo const* shot)
    {
        if (!shot)
            return 0.0f;

        return shot->Effects[EFFECT_1].CalcValue(caster) / 10.0f;
    }

    void RestoreShotMana(Player* player, SpellInfo const* shot, float multiplier)
    {
        if (!player || !shot)
            return;

        float const pct = GetShotManaPct(player, shot);
        uint32 const amount = uint32(std::max(0.0f, player->GetMaxPower(POWER_MANA) * pct / 100.0f * multiplier));
        if (!amount)
            return;

        player->EnergizeBySpell(player, shot->Id, amount, POWER_MANA);
    }
}
