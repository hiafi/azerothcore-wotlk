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
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "Timer.h"
#include "Unit.h"

EventRecorder::EventRecorder(ObjectGuid actorGuid, ObjectGuid targetGuid, uint32 rotationSpellId)
    : UnitScript("mod_dpssim_event_recorder", true,
                 {UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE}),
      _actorGuid(actorGuid), _targetGuid(targetGuid), _rotationSpellId(rotationSpellId)
{
}

void EventRecorder::OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo, bool isCrit)
{
    if (!attacker || !target || attacker->GetGUID() != _actorGuid || target->GetGUID() != _targetGuid)
        return;

    // Fires from Unit::CalculateSpellDamageTaken, upstream of Unit::DealDamage - `damage` here is
    // the real, un-zeroed, fully mitigated hit (armor reduction and crit multiplier both already
    // applied - see OnSpellDamageTakenFinal's doc comment in UnitScript.h, and the 2026-09-12
    // root-cause note on this class's doc comment for why this hook replaced ModifySpellDamageTaken
    // here), and this hook structurally only fires for direct spell hits, never periodic DoT ticks -
    // see this class's doc comment.
    // _rotationSpellId == 0 means "any spell" - see the constructor's doc comment.
    if (!spellInfo || (_rotationSpellId != 0 && spellInfo->Id != _rotationSpellId) || damage <= 0)
        return;

    _totalDamage += uint64(damage);
    _hitDamages.push_back(uint32(damage));
    _hitSpellIds.push_back(spellInfo->Id);
    _hitTimestamps.push_back(getMSTime());

    ++_castCount;
    _hitCrits.push_back(isCrit);
    if (isCrit)
        ++_critCount;
}

void EventRecorder::Reset()
{
    _totalDamage = 0;
    _castCount = 0;
    _critCount = 0;
    _hitDamages.clear();
    _hitCrits.clear();
    _hitSpellIds.clear();
    _hitTimestamps.clear();
    _auraEvents.clear();
}

void EventRecorder::OnAuraApply(Unit* unit, Aura* aura)
{
    if (!unit || !aura)
        return;

    ObjectGuid const guid = unit->GetGUID();
    if (guid != _actorGuid && guid != _targetGuid)
        return;

    SpellInfo const* spellInfo = aura->GetSpellInfo();
    _auraEvents.push_back(AuraEvent{
        getMSTime(), guid, guid == _actorGuid, aura->GetId(), aura->GetStackAmount(),
        spellInfo && spellInfo->IsPositive(), true});
}

void EventRecorder::OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode /*mode*/)
{
    if (!unit || !aurApp || !aurApp->GetBase())
        return;

    ObjectGuid const guid = unit->GetGUID();
    if (guid != _actorGuid && guid != _targetGuid)
        return;

    Aura const* aura = aurApp->GetBase();
    SpellInfo const* spellInfo = aura->GetSpellInfo();
    _auraEvents.push_back(AuraEvent{
        getMSTime(), guid, guid == _actorGuid, aura->GetId(), aura->GetStackAmount(),
        spellInfo && spellInfo->IsPositive(), false});
}
