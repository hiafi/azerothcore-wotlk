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

#include "ProcChanceCooldown.h"
#include "Player.h"
#include "SpellAuras.h"
#include "Unit.h"

namespace ProcChanceCooldown
{
    float GetProcChancePct(Unit const* unit)
    {
        Player const* player = unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        return player ? player->GetProcChancePercentage() : 0.0f;
    }

    uint32 ScaleFor(Unit const* unit, uint32 icdMs, float listedChancePct)
    {
        return IsScaledProc(listedChancePct) ? Scale(icdMs, GetProcChancePct(unit)) : icdMs;
    }

    void ScaleMarkerAura(Aura* marker, float listedChancePct)
    {
        if (!marker || marker->GetMaxDuration() <= 0)
            return;

        int32 const duration =
            int32(ScaleFor(marker->GetCaster(), uint32(marker->GetMaxDuration()), listedChancePct));
        if (duration == marker->GetMaxDuration())
            return;

        marker->SetMaxDuration(duration);
        marker->SetDuration(duration);
    }
}
