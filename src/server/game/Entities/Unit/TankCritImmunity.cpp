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

#include "TankCritImmunity.h"
#include "Unit.h"

namespace TankCritImmunity
{
    bool HasSourceAura(Unit const* unit)
    {
        for (uint32 spellId : SOURCE_AURAS)
            if (unit->HasAura(spellId))
                return true;

        return false;
    }

    void Refresh(Unit* unit)
    {
        if (!unit)
            return;

        if (HasSourceAura(unit))
        {
            if (!unit->HasAura(SPELL_CRIT_IMMUNITY))
                unit->CastSpell(unit, SPELL_CRIT_IMMUNITY, true);
        }
        else
            unit->RemoveAurasDueToSpell(SPELL_CRIT_IMMUNITY);
    }
}
