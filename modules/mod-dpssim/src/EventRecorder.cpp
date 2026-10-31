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
#include <utility>

EventRecorder::EventRecorder(ObjectGuid actorGuid, std::vector<ObjectGuid> targetGuids, uint32 rotationSpellId)
    : UnitScript("mod_dpssim_event_recorder", true,
                 {UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_MELEE_DAMAGE_FINAL, UNITHOOK_ON_PERIODIC_DAMAGE_FINAL,
                  UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE, UNITHOOK_ON_MELEE_OUTCOME_FINAL}),
      _actorGuid(actorGuid), _targetGuids(std::move(targetGuids)), _rotationSpellId(rotationSpellId)
{
}

int8 EventRecorder::TargetIndexOf(ObjectGuid guid) const
{
    for (size_t i = 0; i < _targetGuids.size(); ++i)
        if (_targetGuids[i] == guid)
            return int8(i);
    return -1;
}

bool EventRecorder::IsOwnedByActor(Unit* unit) const
{
    return unit->GetGUID() != _actorGuid &&
           (unit->GetOwnerGUID() == _actorGuid || unit->GetCharmerOrOwnerGUID() == _actorGuid ||
            unit->GetCreatorGUID() == _actorGuid);
}

bool EventRecorder::AttributeToActor(Unit* attacker, bool& isPet, uint32& sourceEntry) const
{
    isPet = false;
    sourceEntry = 0;
    if (attacker->GetGUID() == _actorGuid)
        return true;

    if (IsOwnedByActor(attacker))
    {
        isPet = true;
        sourceEntry = attacker->GetEntry();
        return true;
    }

    return false;
}

void EventRecorder::OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo, bool isCrit)
{
    bool isPet = false;
    uint32 sourceEntry = 0;
    int8 const targetIndex = target ? TargetIndexOf(target->GetGUID()) : -1;
    if (!attacker || targetIndex < 0 || !AttributeToActor(attacker, isPet, sourceEntry))
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

    RecordHit(spellInfo->Id, uint32(damage), isCrit, isPet, uint8(targetIndex), sourceEntry);
}

void EventRecorder::OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo, bool isCrit)
{
    bool isPet = false;
    uint32 sourceEntry = 0;
    int8 const targetIndex = target ? TargetIndexOf(target->GetGUID()) : -1;
    if (!attacker || targetIndex < 0 || !AttributeToActor(attacker, isPet, sourceEntry))
        return;

    // Same single-spell / any-spell filter as OnSpellDamageTakenFinal
    if (!spellInfo || (_rotationSpellId != 0 && spellInfo->Id != _rotationSpellId) || damage == 0)
        return;

    RecordHit(spellInfo->Id, damage, isCrit, isPet, uint8(targetIndex), sourceEntry);
}

void EventRecorder::OnMeleeDamageFinal(Unit* target, Unit* attacker, uint32 damage, bool isCrit)
{
    _pendingMeleeRow = -1;
    bool isPet = false;
    uint32 sourceEntry = 0;
    int8 const targetIndex = target ? TargetIndexOf(target->GetGUID()) : -1;
    if (!attacker || targetIndex < 0 || !AttributeToActor(attacker, isPet, sourceEntry))
        return;

    // A single-spell recorder (Phase 1 tests) ignores swings; misses, dodges and parries arrive as 0
    if (_rotationSpellId != 0 || damage == 0)
        return;

    RecordHit(isPet ? PET_MELEE_SPELL_ID : MELEE_SPELL_ID, damage, isCrit, isPet, uint8(targetIndex), sourceEntry);
    _pendingMeleeRow = int64(_hitSpellIds.size()) - 1;
}

void EventRecorder::OnMeleeOutcomeFinal(CalcDamageInfo const* damageInfo)
{
    // The row of this very swing (OnMeleeDamageFinal runs immediately before this hook in CalculateMeleeDamage); none
    // when that hook recorded nothing, so a miss, a foreign swing or a single-spell recorder falls through here
    int64 const row = _pendingMeleeRow;
    _pendingMeleeRow = -1;
    if (!damageInfo || row < 0 || row >= int64(_hitSpellIds.size()) || damageInfo->attackType != OFF_ATTACK)
        return;

    // Only the actor's own off-hand white swing is re-tagged; a pet keeps PET_MELEE_SPELL_ID
    if (_hitIsPet[row] || _hitSpellIds[row] != MELEE_SPELL_ID)
        return;

    _hitSpellIds[row] = OFFHAND_MELEE_SPELL_ID;
}

void EventRecorder::RecordHit(uint32 spellId, uint32 damage, bool isCrit, bool isPet, uint8 targetIndex,
    uint32 sourceEntry)
{
    _totalDamage += uint64(damage);
    _hitDamages.push_back(damage);
    _hitSpellIds.push_back(spellId);
    _hitTimestamps.push_back(getMSTime());
    _hitIsPet.push_back(isPet);
    _hitTargetIndex.push_back(targetIndex);
    _hitSourceEntries.push_back(sourceEntry);

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
    _hitTargetIndex.clear();
    _hitSourceEntries.clear();
    _auraEvents.clear();
    _pendingMeleeRow = -1;
}

void EventRecorder::OnAuraApply(Unit* unit, Aura* aura)
{
    if (!unit || !aura)
        return;

    ObjectGuid const guid = unit->GetGUID();
    int8 const targetIndex = TargetIndexOf(guid);
    bool const isPet = guid != _actorGuid && targetIndex < 0 && IsOwnedByActor(unit);
    if (guid != _actorGuid && targetIndex < 0 && !isPet)
        return;

    SpellInfo const* spellInfo = aura->GetSpellInfo();
    // A minion's passive auras (its stat inheritance) are noise: the ones worth reading, Shadow Infusion and
    // Dark Transformation, are not passive
    if (isPet && (!spellInfo || spellInfo->IsPassive()))
        return;

    _auraEvents.push_back(AuraEvent{
        getMSTime(), guid, guid == _actorGuid, aura->GetId(), aura->GetStackAmount(),
        spellInfo && spellInfo->IsPositive(), true, targetIndex, isPet, unit->GetEntry()});
}

void EventRecorder::RecordAurasPresent(Unit* unit)
{
    if (!unit)
        return;

    ObjectGuid const guid = unit->GetGUID();
    int8 const targetIndex = TargetIndexOf(guid);
    bool const isPet = guid != _actorGuid && targetIndex < 0 && IsOwnedByActor(unit);
    if (guid != _actorGuid && targetIndex < 0 && !isPet)
        return;

    uint32 const now = getMSTime();
    for (auto const& [spellId, aurApp] : unit->GetAppliedAuras())
    {
        Aura const* aura = aurApp->GetBase();
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (!spellInfo || spellInfo->IsPassive())
            continue;

        _auraEvents.push_back(AuraEvent{
            now, guid, guid == _actorGuid, spellId, aura->GetStackAmount(), spellInfo->IsPositive(), true,
            targetIndex, isPet, unit->GetEntry()});
    }
}

void EventRecorder::OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode /*mode*/)
{
    if (!unit || !aurApp || !aurApp->GetBase())
        return;

    ObjectGuid const guid = unit->GetGUID();
    int8 const targetIndex = TargetIndexOf(guid);
    bool const isPet = guid != _actorGuid && targetIndex < 0 && IsOwnedByActor(unit);
    if (guid != _actorGuid && targetIndex < 0 && !isPet)
        return;

    Aura const* aura = aurApp->GetBase();
    SpellInfo const* spellInfo = aura->GetSpellInfo();
    if (isPet && (!spellInfo || spellInfo->IsPassive()))
        return;

    _auraEvents.push_back(AuraEvent{
        getMSTime(), guid, guid == _actorGuid, aura->GetId(), aura->GetStackAmount(),
        spellInfo && spellInfo->IsPositive(), false, targetIndex, isPet, unit->GetEntry()});
}
