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
#include "SpellInfo.h"
#include "Unit.h"

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
}
