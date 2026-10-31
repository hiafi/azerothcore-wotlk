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

#ifndef __LEAPMECHANICS_H
#define __LEAPMECHANICS_H

#include "Define.h"

class Unit;

/*
 * Class-neutral rules for ground-targeted leaps (warrior Heroic Leap, rogue Grappling Hook; warrior-rework W0b).
 * Append-only: later stages add their declarations together with their bodies and never retype an existing signature.
 * Lives in game/Entities/Unit/ (core), not scripts/, so bots (mod-playerbots) can call the same test the SpellScripts
 * use.
 */
namespace Leap
{
    // True when `caster` could land on the world point (x, y, z): there is ground within a couple of yards of z
    // (a wall face, an overhang or open air has none), and on a map with mmaps loaded there is a walkable navmesh
    // polygon next to that ground (steep slopes and wall tops are not on it). A point on a swimmable water surface
    // passes (the caster lands swimming); magma and slime do not. The point may lie at most MAX_CLIMB_YD above the
    // caster (any drop is fine), and a caster on a transport (ship, zeppelin) never lands anywhere: its jump spline
    // would be built in transport space. Read-only. A spell's CheckCast answers a false with SPELL_FAILED_NOPATH.
    constexpr float MAX_CLIMB_YD = 15.0f;

    bool IsLandablePoint(Unit const* caster, float x, float y, float z);
}

#endif
