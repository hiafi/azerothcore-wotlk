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

#ifndef __TANKCRITIMMUNITY_H
#define __TANKCRITIMMUNITY_H

#include "Define.h"
#include <array>

class Unit;

/*
 * Shared tank crit immunity 200000 (apps/dbc-tools/source/spells/generic.csv). Several tank auras grant the same
 * aura, and a Classless character can hold more than one of them at once (a stance or form, Righteous Fury and a
 * presence), so the aura is never added or removed directly: every source calls Refresh from both its apply and its
 * remove hook, and Refresh keeps 200000 exactly while at least one source is still applied.
 *
 * The reworks that came later give each tank aura its own crit-immunity child instead (Blood Presence 203000,
 * Enforcer Stance 203721, Rockbiter 202200); those are separate auras and are not listed here.
 */
namespace TankCritImmunity
{
    constexpr uint32 SPELL_CRIT_IMMUNITY = 200000;

    // Every aura that grants 200000: Defensive Stance, Righteous Fury, Bear Form, Dire Bear Form, Frost Presence,
    // Dark Apotheosis. A new source is added here and calls Refresh from its own apply and remove hooks.
    constexpr std::array<uint32, 6> SOURCE_AURAS = { 71, 25780, 5487, 9634, 48263, 200835 };

    // True while `unit` has any SOURCE_AURAS aura applied. An aura being removed is already out of the applied list
    // when its AfterEffectRemove hook runs, so it does not count itself.
    bool HasSourceAura(Unit const* unit);

    // Adds 200000 when a source aura is applied and it is missing, removes it when no source aura is left.
    void Refresh(Unit* unit);
}

#endif
