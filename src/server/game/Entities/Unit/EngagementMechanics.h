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

#ifndef __ENGAGEMENTMECHANICS_H
#define __ENGAGEMENTMECHANICS_H

#include "ObjectGuid.h"

class Creature;
class Player;
class Unit;

/*
 * Class-neutral "in combat with the owner or the owner's group" helpers for summons that must never pull idle
 * mobs (shaman-rework SH0b; T0b section 5). Append-only.
 */
namespace Engagement
{
    // True when `hostile` is in combat with `owner` or any member of the owner's group. A unit hit by the owner's
    // totem, guardian or pet counts: Unit::AtTargetAttacked also engages the attacker's owner. False on null input.
    bool IsEngagedWithOwnerOrGroup(Unit const* hostile, Player const* owner);

    // Every candidate must be alive, on the summon's map, a valid attack target for `summon`, within `range` of it
    // and engaged with the owner or group. Order: the preferred target, else the owner's current target, else the
    // nearest such hostile in line of sight of `summon`. Never pulls; nullptr when nothing qualifies (or on null
    // input).
    Unit* SelectEngagedTarget(Creature* summon, Player* owner, ObjectGuid preferred, float range);
}

#endif
