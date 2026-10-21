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

#include "HealRecorder.h"
#include "SimHeal.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "Timer.h"
#include "Unit.h"
#include <utility>

HealRecorder::HealRecorder(ObjectGuid actorGuid, std::vector<ObjectGuid> groupGuids)
    : UnitScript("mod_dpssim_heal_recorder", true,
                 {UNITHOOK_ON_HEAL_FINAL, UNITHOOK_ON_ABSORB_FINAL, UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL,
                  UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE}),
      _actorGuid(actorGuid), _groupGuids(std::move(groupGuids))
{
}

int8 HealRecorder::IndexOf(ObjectGuid guid) const
{
    for (size_t i = 0; i < _groupGuids.size(); ++i)
        if (_groupGuids[i] == guid)
            return int8(i);
    return -1;
}

bool HealRecorder::AttributeToActor(Unit* unit, bool& isPet) const
{
    isPet = false;
    if (!unit)
        return false;

    if (unit->GetGUID() == _actorGuid)
        return true;

    if (unit->GetOwnerGUID() == _actorGuid || unit->GetCharmerOrOwnerGUID() == _actorGuid ||
        unit->GetCreatorGUID() == _actorGuid)
    {
        isPet = true;
        return true;
    }

    return false;
}

void HealRecorder::OnHealFinal(Unit* healer, Unit* target, SpellInfo const* spellInfo, uint32 heal, uint32 effective,
    uint32 healAbsorbed, bool isCrit, bool isPeriodic)
{
    // A zero heal is a shield-converted one (Spirit Shell): the absorb it became is an absorb event
    if (heal == 0 && effective == 0)
        return;

    bool isPet = false;
    int8 const targetIndex = target ? IndexOf(target->GetGUID()) : -1;
    if (targetIndex < 0 || !AttributeToActor(healer, isPet))
        return;

    uint32 const overheal = heal > effective + healAbsorbed ? heal - effective - healAbsorbed : 0;
    _healEvents.push_back({getMSTime(), spellInfo ? spellInfo->Id : NO_SPELL_ID, isPet, uint8(targetIndex), heal,
        effective, overheal, healAbsorbed, isCrit, isPeriodic});
}

void HealRecorder::OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
    bool /*isCrit*/)
{
    if (!spellInfo || !target || !attacker)
        return;

    bool const pin = spellInfo->Id == SimHeal::SPELL_PIN_HIT;
    if (!pin && spellInfo->Id != SimHeal::SPELL_DAMAGE_PULSE)
        return;

    int8 const targetIndex = IndexOf(target->GetGUID());
    if (targetIndex < 0)
        return;

    uint32 const raw = damage > 0 ? uint32(damage) : 0;
    _damageEvents.push_back({getMSTime(), uint8(targetIndex), pin, raw, 0, raw});
    _openDamage = int32(_damageEvents.size()) - 1;
}

void HealRecorder::OnAbsorbFinal(Unit* victim, Unit* attacker, AuraEffect const* absorbAurEff, uint32 absorbed)
{
    int8 const targetIndex = victim ? IndexOf(victim->GetGUID()) : -1;
    if (targetIndex < 0 || !absorbAurEff || absorbed == 0)
        return;

    // The shield belongs to the damage event the same call just recorded, whoever cast it
    if (_openDamage >= 0 && attacker)
    {
        SimHeal::DamageEvent& damage = _damageEvents[_openDamage];
        if (damage.TargetIndex == uint8(targetIndex))
        {
            damage.Absorbed += absorbed;
            damage.Final = damage.Raw > damage.Absorbed ? damage.Raw - damage.Absorbed : 0;
        }
    }

    // Attribution goes through the shield's caster; a caster that already despawned (a totem) can only be matched by
    // GUID against the healer itself
    bool isPet = false;
    Unit* caster = absorbAurEff->GetCaster();
    if (caster ? !AttributeToActor(caster, isPet) : absorbAurEff->GetCasterGUID() != _actorGuid)
        return;

    _absorbEvents.push_back({getMSTime(), absorbAurEff->GetId(), isPet, uint8(targetIndex), absorbed});
}

void HealRecorder::OnAuraApply(Unit* unit, Aura* aura)
{
    int8 const targetIndex = (unit && aura) ? IndexOf(unit->GetGUID()) : -1;
    if (targetIndex < 0)
        return;

    SpellInfo const* spellInfo = aura->GetSpellInfo();
    if (!spellInfo || spellInfo->IsPassive())
        return;

    bool isPet = false;
    _auraEvents.push_back({getMSTime(), uint8(targetIndex), aura->GetId(), aura->GetStackAmount(),
        spellInfo->IsPositive(), true, AttributeToActor(aura->GetCaster(), isPet)});
}

void HealRecorder::OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode /*mode*/)
{
    int8 const targetIndex = (unit && aurApp && aurApp->GetBase()) ? IndexOf(unit->GetGUID()) : -1;
    if (targetIndex < 0)
        return;

    Aura const* aura = aurApp->GetBase();
    SpellInfo const* spellInfo = aura->GetSpellInfo();
    if (!spellInfo || spellInfo->IsPassive())
        return;

    bool isPet = false;
    _auraEvents.push_back({getMSTime(), uint8(targetIndex), aura->GetId(), aura->GetStackAmount(),
        spellInfo->IsPositive(), false, AttributeToActor(aura->GetCaster(), isPet)});
}

void HealRecorder::RecordAurasPresent(Unit* unit)
{
    int8 const targetIndex = unit ? IndexOf(unit->GetGUID()) : -1;
    if (targetIndex < 0)
        return;

    uint32 const now = getMSTime();
    for (auto const& [spellId, aurApp] : unit->GetAppliedAuras())
    {
        Aura const* aura = aurApp->GetBase();
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (!spellInfo || spellInfo->IsPassive())
            continue;

        bool isPet = false;
        _auraEvents.push_back({now, uint8(targetIndex), spellId, aura->GetStackAmount(), spellInfo->IsPositive(),
            true, AttributeToActor(aura->GetCaster(), isPet)});
    }
}

void HealRecorder::Reset()
{
    _healEvents.clear();
    _absorbEvents.clear();
    _damageEvents.clear();
    _auraEvents.clear();
    _openDamage = -1;
}
