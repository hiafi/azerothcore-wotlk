/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "CastRecorder.h"
#include "SpellInfo.h"
#include "Timer.h"
#include "Unit.h"

CastRecorder::CastRecorder(ObjectGuid actorGuid)
    : AllSpellScript("mod_dpssim_cast_recorder", {ALLSPELLHOOK_ON_CAST}), _actorGuid(actorGuid)
{
}

void CastRecorder::OnSpellCast(Spell* /*spell*/, Unit* caster, SpellInfo const* spellInfo, bool /*skipCheck*/)
{
    if (!caster || caster->GetGUID() != _actorGuid || !spellInfo)
        return;

    _castEvents.push_back({getMSTime(), spellInfo->Id});
}
