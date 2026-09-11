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

#include "EventRecorder.h"
#include "SpellInfo.h"
#include "Unit.h"

EventRecorder::EventRecorder(ObjectGuid actorGuid, ObjectGuid targetGuid, uint32 rotationSpellId)
    : UnitScript("mod_dpssim_event_recorder", true, {UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN}),
      _actorGuid(actorGuid), _targetGuid(targetGuid), _rotationSpellId(rotationSpellId)
{
}

void EventRecorder::ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo, bool isCrit)
{
    if (!attacker || !target || attacker->GetGUID() != _actorGuid || target->GetGUID() != _targetGuid)
        return;

    // Fires from Unit::CalculateSpellDamageTaken, upstream of Unit::DealDamage - `damage` here is
    // the real, un-zeroed hit (already crit-adjusted upstream; CalculateSpellDamageTaken's own
    // caller guarantees damage >= 0 before this hook runs), and this hook structurally only fires
    // for direct spell hits, never periodic DoT ticks - see this class's doc comment.
    // _rotationSpellId == 0 means "any spell" - see the constructor's doc comment.
    if (!spellInfo || (_rotationSpellId != 0 && spellInfo->Id != _rotationSpellId) || damage <= 0)
        return;

    _totalDamage += uint64(damage);
    _hitDamages.push_back(uint32(damage));
    _hitSpellIds.push_back(spellInfo->Id);

    ++_castCount;
    _hitCrits.push_back(isCrit);
    if (isCrit)
        ++_critCount;
}
