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

#ifndef MODULE_DPSSIM_SIMALLY_H
#define MODULE_DPSSIM_SIMALLY_H

#include "Define.h"
#include "SimActor.h"
#include "SimHeal.h"
#include <string>

class Player;

// A group member of the healing sim that is not the healer (plan .agents/plans/healing-sim/healing-sim.PLAN.md,
// section 1): a headless Player made through SimActor (no SQL, a guid from SIM_GUID_BASE, a socketless session), with
// no PlayerbotAI and no movement. It stands where it was placed and only has health done to it. Tanks are Warriors with
// the profile's AllyTankTalents spent, so PlayerbotAI::IsTank(bySpec) calls them tanks; DPS allies are untalented
// Rogues (or Warriors, for a race that cannot be a Rogue), which that function can never call a tank.
class SimAlly
{
public:
    struct Config
    {
        SimHeal::Role AllyRole = SimHeal::Role::Dps;
        // The healer's race, so the ally is in the healer's faction (heals need a friendly target) and starts on the
        // same map; only the class differs
        uint8 Race = 1;
        uint8 Level = 60;
        std::string Name = "SimAlly";
        // Positional talent string (tanks only; empty = none)
        std::string Talents;
        // Max health with no buffs: only the BASE part of the health modifier is pinned to reach it (plan R4)
        uint32 BaseMaxHealth = 5000;
        float PositionX = 0.0f;
        float PositionY = 0.0f;
        float PositionZ = 0.0f;
        float PositionO = 0.0f;
    };

    // The class an ally of `role` gets for `race`: Warrior for a tank, Rogue for a DPS (Warrior when the race cannot be
    // a Rogue)
    static uint8 ClassFor(SimHeal::Role role, uint8 race);

    // Moves the BASE part of `player`'s health modifier so that its unbuffed max health is exactly `maxHealth` (plan
    // R4), and fills it. Also used for the healer's own slot.
    static void PinBaseMaxHealth(Player* player, uint32 maxHealth);

    // Builds the Player, spends the talents, pins the base max health and fills it. False (logging why) on failure.
    bool Create(Config const& config);

    [[nodiscard]] Player* GetPlayer() const { return _actor.GetPlayer(); }

    // If the ally is no longer standing at its slot on its start map (a teleport nobody acknowledged, or a spirit that
    // released at a graveyard), acknowledges any pending teleport, puts it back and logs a warning. Dead or ghost, it
    // is left for the caller to resurrect. True when it had to be moved.
    bool ReturnToSlot();

private:
    // The teleport acknowledgements a client would send; the ally has no client and no PlayerbotAI
    void AcknowledgeTeleport();

    SimActor _actor;
    uint32 _slotMapId = 0;
    float _slotX = 0.0f;
    float _slotY = 0.0f;
    float _slotZ = 0.0f;
    float _slotO = 0.0f;
};

#endif
