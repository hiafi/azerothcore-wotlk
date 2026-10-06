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
                 {UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_MELEE_DAMAGE_FINAL, UNITHOOK_ON_PERIODIC_DAMAGE_FINAL,
                  UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE}),
      _actorGuid(actorGuid), _targetGuid(targetGuid), _rotationSpellId(rotationSpellId)
{
}

bool EventRecorder::AttributeToActor(Unit* attacker, bool& isPet) const
{
    isPet = false;
    if (attacker->GetGUID() == _actorGuid)
        return true;

    if (attacker->GetOwnerGUID() == _actorGuid || attacker->GetCharmerOrOwnerGUID() == _actorGuid ||
        attacker->GetCreatorGUID() == _actorGuid)
    {
        isPet = true;
        return true;
    }

    return false;
}

void EventRecorder::OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo, bool isCrit)
{
    bool isPet = false;
    if (!attacker || !target || target->GetGUID() != _targetGuid || !AttributeToActor(attacker, isPet))
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

    RecordHit(spellInfo->Id, uint32(damage), isCrit, isPet);
}

void EventRecorder::OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo, bool isCrit)
{
    bool isPet = false;
    if (!attacker || !target || target->GetGUID() != _targetGuid || !AttributeToActor(attacker, isPet))
        return;

    // Same single-spell / any-spell filter as OnSpellDamageTakenFinal
    if (!spellInfo || (_rotationSpellId != 0 && spellInfo->Id != _rotationSpellId) || damage == 0)
        return;

    RecordHit(spellInfo->Id, damage, isCrit, isPet);
}

void EventRecorder::OnMeleeDamageFinal(Unit* target, Unit* attacker, uint32 damage, bool isCrit)
{
    bool isPet = false;
    if (!attacker || !target || target->GetGUID() != _targetGuid || !AttributeToActor(attacker, isPet))
        return;

    // A single-spell recorder (Phase 1 tests) ignores swings; misses, dodges and parries arrive as 0
    if (_rotationSpellId != 0 || damage == 0)
        return;

    RecordHit(isPet ? PET_MELEE_SPELL_ID : MELEE_SPELL_ID, damage, isCrit, isPet);
}

void EventRecorder::RecordHit(uint32 spellId, uint32 damage, bool isCrit, bool isPet)
{
    _totalDamage += uint64(damage);
    _hitDamages.push_back(damage);
    _hitSpellIds.push_back(spellId);
    _hitTimestamps.push_back(getMSTime());
    _hitIsPet.push_back(isPet);

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
    _hitIsPet.clear();
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

void EventRecorder::RecordAurasPresent(Unit* unit)
{
    if (!unit)
        return;

    ObjectGuid const guid = unit->GetGUID();
    if (guid != _actorGuid && guid != _targetGuid)
        return;

    uint32 const now = getMSTime();
    for (auto const& [spellId, aurApp] : unit->GetAppliedAuras())
    {
        Aura const* aura = aurApp->GetBase();
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (!spellInfo || spellInfo->IsPassive())
            continue;

        _auraEvents.push_back(AuraEvent{
            now, guid, guid == _actorGuid, spellId, aura->GetStackAmount(), spellInfo->IsPositive(), true});
    }
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
