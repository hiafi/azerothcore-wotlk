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

#ifndef MODULE_DPSSIM_HEALRECORDER_H
#define MODULE_DPSSIM_HEALRECORDER_H

#include "ObjectGuid.h"
#include "ScriptMgr.h"
#include "SimHeal.h"
#include <vector>

// The healing sim's counterpart of EventRecorder (plan .agents/plans/healing-sim/healing-sim.PLAN.md, section 4):
// records what the healer, its pets, guardians and totems do for the group, and what the boss does to it.
//
//  - Heals: OnHealFinal (UNITHOOK_ON_HEAL_FINAL, the HS0 core hook), one event per direct heal or HoT tick from the
//    healer side to a group member, with the amount before heal-absorb, the effective amount, the overheal and the
//    crit/periodic flags. Zero-amount events (a Spirit Shell style shield-converted heal) are skipped. Heals to
//    anything outside the group (the boss, a pet) are ignored.
//  - Absorbs: OnAbsorbFinal (UNITHOOK_ON_ABSORB_FINAL), one event per shield that took damage off a group member,
//    attributed through the shield's caster. Counted as healing in the headline, as meters do.
//  - Damage taken: OnSpellDamageTakenFinal for the boss's two spells only (Sim Damage Pulse / Sim Pin Hit), with the
//    amount the driver asked for (BeginHit) and the shield absorption of the same hit added from the absorb events that
//    follow it in the same call (Unit::CalculateSpellDamageTaken fires the damage hook, then runs the absorb loop).
//  - Auras applied to and removed from group members, for HoT and shield uptime.
//
// Attribution to the healer follows EventRecorder::AttributeToActor(): the actor itself, or anything it owns, charms or
// created (pets, guardians, totems), the latter flagged `IsPet`.
//
// Same heap-allocation / never-deleted / constructed-at-runtime rules as EventRecorder: see its class comment.
class HealRecorder : public UnitScript
{
public:
    // `groupGuids` are the group's members in target index order (the healer's own slot included)
    HealRecorder(ObjectGuid actorGuid, std::vector<ObjectGuid> groupGuids);

    void OnHealFinal(Unit* healer, Unit* target, SpellInfo const* spellInfo, uint32 heal, uint32 effective,
        uint32 healAbsorbed, bool isCrit, bool isPeriodic) override;
    void OnAbsorbFinal(Unit* victim, Unit* attacker, AuraEffect const* absorbAurEff, uint32 absorbed) override;
    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool isCrit) override;
    void OnAuraApply(Unit* unit, Aura* aura) override;
    void OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode mode) override;

    // The scenario's hit driver brackets each cast of the Sim Damage Pulse / Sim Pin Hit: BeginHit() tells the recorder
    // which target the hit is aimed at and how much damage was asked for (stored as DamageEvent::Requested), EndHit()
    // closes the hit, so an absorb that comes later cannot be linked to its damage event
    void BeginHit(uint8 targetIndex, uint32 requested);
    void EndHit();

    // Clears every recorded event, between iterations (see EventRecorder::Reset())
    void Reset();

    // An "applied" event, stamped now, for every non-passive aura already on `unit` (a group member), so uptime is
    // measured from the pull
    void RecordAurasPresent(Unit* unit);

    // Pseudo spell id for a heal with no spell (the melee leech stat)
    static constexpr uint32 NO_SPELL_ID = 0;

    [[nodiscard]] std::vector<SimHeal::HealEvent> const& GetHealEvents() const { return _healEvents; }
    [[nodiscard]] std::vector<SimHeal::AbsorbEvent> const& GetAbsorbEvents() const { return _absorbEvents; }
    [[nodiscard]] std::vector<SimHeal::DamageEvent> const& GetDamageEvents() const { return _damageEvents; }
    [[nodiscard]] std::vector<SimHeal::GroupAuraEvent> const& GetAuraEvents() const { return _auraEvents; }

private:
    bool AttributeToActor(Unit* unit, bool& isPet) const;
    int8 IndexOf(ObjectGuid guid) const;

    ObjectGuid _actorGuid;
    std::vector<ObjectGuid> _groupGuids;
    std::vector<SimHeal::HealEvent> _healEvents;
    std::vector<SimHeal::AbsorbEvent> _absorbEvents;
    std::vector<SimHeal::DamageEvent> _damageEvents;
    std::vector<SimHeal::GroupAuraEvent> _auraEvents;

    // The damage event the absorb events that follow it belong to: set by a boss hit, read by the absorbs of the same
    // CalculateSpellDamageTaken call, -1 otherwise (cleared by the next damage hook of any spell, and by EndHit())
    int32 _openDamage = -1;

    // The hit BeginHit() announced: its target and requested amount, valid until EndHit()
    bool _hitOpen = false;
    uint8 _hitTarget = 0;
    uint32 _hitRequested = 0;
};

#endif
