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

// Custom: the links between the crafting rework scripts (custom_professions.cpp, custom_gathering_ranks.cpp).

#ifndef CUSTOM_CRAFTING_H
#define CUSTOM_CRAFTING_H

#include "Define.h"
#include <string>

class Player;

namespace CustomProfessions
{
    // Sends the Professions page feed (CPROF) on the player's next update. No-op for players without a client.
    void QueueFeed(Player* player);

    // Whispers `body` to the player himself under the CPROF prefix (an addon message). No-op without a client.
    void SendAddonMessage(Player* player, std::string const& body);
}

namespace CustomGathering
{
    // The player's best gathering rank (0-5) across the materials of a gathering skill (Herbalism, Mining,
    // Skinning), for the Professions page. 0 when he has none.
    uint8 GetBestRank(Player const* player, uint32 skillId);

    // Sends the Gathering Ranks window every material and the player's rank in it ("G1" messages, CPROF prefix).
    void SendMaterialFeed(Player* player);
}

#endif
