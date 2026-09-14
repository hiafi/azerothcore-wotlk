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

#ifndef MODULE_DPSSIM_SIMTESTS_H
#define MODULE_DPSSIM_SIMTESTS_H

// Phase 1's three required tests (known-value, timestep, accelerated-clock - see the plan doc's
// Phase 1 task list and "Definition of done"), all built on SimDaemon::RunOnce(). A fourth,
// determinism, was dropped along with SetRandomSeed() itself: seeding a run never actually made it
// reproducible (something before the combat loop consumed a different number of random draws
// between runs even with an identical seed, never root-caused), so the seeding code was removed as
// unreliable rather than kept around backing a guarantee it didn't meet. Not wired into `ctest`:
// the daemon needs the full worldserver boot (DB + client data, ~15s), which doesn't fit
// src/test/'s headless unit-test harness - see this bullet's own note in the plan doc. Run
// manually via DpsSim.RunTests=1 (alongside DpsSim.Enabled=1) - see dpssim.conf.dist.
namespace SimTests
{
    // Runs all three tests in one process boot (each construct-and-tear-down actor/target pair is
    // independent - see SimDaemon::RunOnce()'s own doc comment on why this is safe to call
    // repeatedly) and logs a PASS/FAIL verdict for each plus a final summary line.
    void RunAll();
}

#endif
