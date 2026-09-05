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

#include "WarriorMechanics.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "Unit.h"
#include "Util.h"

namespace Warrior
{
    namespace
    {
        // Bare icon literal, not an enum shared with spell_warrior.cpp - this core file has no
        // access to that scripts/ file's WarriorSpellIcons enum. Keep in sync with
        // WARRIOR_ICON_ID_CRITICAL_BLOCK (spell_warrior.cpp) if it ever changes.
        constexpr uint32 ICON_CRITICAL_BLOCK = 2778;
    }

    void ApplyBlockDamageReduction(Unit* defender, uint32& damage)
    {
        if (Player const* player = defender->ToPlayer())
            if (AuraEffect const* aurEff = player->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_WARRIOR, ICON_CRITICAL_BLOCK, EFFECT_1))
                AddPct(damage, -int32(aurEff->GetAmount()));
    }
}
