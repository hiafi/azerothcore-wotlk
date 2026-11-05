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

#ifndef MODULE_DPSSIM_SIMMECHANICSCONFIG_H
#define MODULE_DPSSIM_SIMMECHANICSCONFIG_H

#include "SimDaemon.h"
#include "SimMechanics.h"
#include "SimProfile.h"
#include <string>
#include <vector>

// Builds a mechanics run (SimDaemon::Mode::Mechanics) from the profile under test and the DpsSim.Mechanics* conf keys
// (dpssim.conf.dist documents every key):
//
//  - The slot of the profile under test: `Mode = Mechanics` reads its MechanicsRole; any other profile run with
//    DpsSim.MechanicsMode = 1 takes the tank slot for `Mode = Tank`, the healer slot for `Mode = Heal`, a DPS slot
//    otherwise. DpsSim.MechanicsRole overrides both.
//  - The group (DpsSim.MechanicsGroup, default 5): 1 tank (2 above 10), 1 healer (2 for 6-10, 4 above 10; none for a
//    group of 2), the rest DPS; the role under test always has a slot. The other slots are the fixed reference
//    profiles (DpsSim.MechanicsTankProfiles / HealerProfiles / DpsProfiles, each list cycled in order and skipping
//    the profile under test), loaded from the directory of DpsSim.Profile, so every spec of a sweep runs beside the
//    same group.
//  - Races: every member is Horde, so the group can heal and buff itself and the Horde start it stands at is friendly:
//    HordeRaceFor() per class (the profile's own race is not a profile key; DpsSim.PlayerbotRace is ignored here).
//  - Programs (DpsSim.MechanicsPrograms, ';'-separated, each checked by the module's Drill::ParseProgram), or the
//    baseline (DpsSim.MechanicsBaseline = 1: every iteration runs `none`). Seed, damage, anchor race and the boss's
//    swings: DpsSim.MechanicsSeed / Damage / AnchorRace / BossSwings; the swing numbers come from the first tank's
//    profile (its Tank* keys) when it is a Tank profile, the tank sim's defaults otherwise.
namespace SimMechanicsConfig
{
    // The Horde race a member of `playerClass` is created as (a valid race/class pair; 0 for an unknown class)
    uint8 HordeRaceFor(uint8 playerClass);

    // `text` split at `separator`, each piece trimmed of blanks, empty pieces dropped
    std::vector<std::string> SplitList(std::string const& text, char separator);

    // The path of reference profile `name` next to `profilePath` ("<dir>/<name>.conf"); a name holding a '/' or
    // ending in ".conf" is taken as a path as is
    std::string ResolveProfilePath(std::string const& profilePath, std::string const& name);

    // Fills config.MechMembers, MechPrograms, MechSeed, MechDamage, MechAnchorRace and the boss settings, and sets
    // config.RunMode = Mode::Mechanics. False with `error` on a bad key, a reference profile that fails to load, or a
    // program the module refuses.
    bool Build(std::string const& profilePath, SimProfile::Profile const& actor, SimDaemon::RunConfig& config,
        std::string& error);
}

#endif
