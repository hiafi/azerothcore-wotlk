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

#ifndef MODULE_DPSSIM_SIMCLOCK_H
#define MODULE_DPSSIM_SIMCLOCK_H

#include "Define.h"

class Map;

// Fixed-timestep sim clock (see docs/dps-sim-module.md section 5.4 - "fixed timestep" is M1's
// correctness oracle; adaptive timestep is a later milestone). Each Tick() call keeps three
// things in lockstep: the core's sim-clock override (core patch 2, Timer.h - what makes
// getMSTime()/GameTime read sim time instead of the real wall clock), GameTime's own cached
// value, and the actual Map::Update() call - so the sim runs at whatever pace the caller drives
// this from (real-time or, per Phase 1's actual point, drastically accelerated), independent of
// wall-clock speed.
class SimClock
{
public:
    explicit SimClock(uint32 stepMs) : _stepMs(stepMs) { }

    // Sets the sim-clock override to the current elapsed time (representing "now" at the start of
    // this tick, matching the real server's own GameTime-then-diff convention), refreshes
    // GameTime's cached value from it, ticks `map` by one full fixed step (both Map::Update()
    // diff arguments equal to the step - see the plan doc's SimClock task note for why: passing
    // t_diff == 0 makes Map::Update() skip creature/respawn/non-player-object processing
    // entirely, which is not what a deterministic per-tick sim wants), then advances elapsed time
    // by that step. Returns the elapsed sim time in ms *after* this tick.
    uint32 Tick(Map* map);

    [[nodiscard]] uint32 GetElapsedMs() const { return _elapsedMs; }
    [[nodiscard]] uint32 GetStepMs() const { return _stepMs; }

private:
    uint32 _stepMs;
    uint32 _elapsedMs = 0;
};

#endif
