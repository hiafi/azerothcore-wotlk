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

#ifndef __KILLREWARDMECHANICS_H
#define __KILLREWARDMECHANICS_H

class Unit;

/*
 * Custom kill-reward rules hooked into KillRewarder. Append-only.
 */
namespace KillReward
{
    // True when a dead group member still earns XP and kill credit for this kill: the victim is a boss
    // (isWorldBoss() or IsDungeonBoss()) killed inside a dungeon or raid, so dying (or releasing) mid-fight
    // does not cost the boss reward. Stock rewards neither once the member is dead (XP) or released (credit).
    bool RewardsDeadGroupMembers(Unit const* victim);
}

#endif
