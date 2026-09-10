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

#include "DpsSim.h"
#include "GameTime.h"
#include "Log.h"
#include "Random.h"
#include "Timer.h"

DpsSimWorldScript::DpsSimWorldScript() : WorldScript(MODULE_STRING, {WORLDHOOK_ON_DPS_SIM_RUN}) { }

void DpsSimWorldScript::OnDpsSimRun()
{
    // M1 skeleton: this is not the sim daemon yet (SimDaemon/SimActor/SimTarget/SimClock land in
    // follow-up work on this same module, once this foundation is confirmed to boot, build, and
    // link correctly). What this smoke-tests, end to end, in one run:
    //   - the Main.cpp sim-mode branch actually reaches this hook (core patch 4);
    //   - core patch 1 (RNG seed setter) produces a reproducible roll sequence;
    //   - core patch 2 (Timer.h sim-clock override) decouples GameTime/getMSTime() from the real
    //     wall clock, which is the load-bearing fix the "Critical finding" section of the plan
    //     doc is about.
    LOG_INFO("server.dpssim", "mod-dpssim: OnDpsSimRun() reached - sim-mode boot branch is working.");

    SetRandomSeed(12345);
    LOG_INFO("server.dpssim", "mod-dpssim: seeded urand(1,100) x5 = {}, {}, {}, {}, {}",
        urand(1, 100), urand(1, 100), urand(1, 100), urand(1, 100), urand(1, 100));

    // Advance the sim clock in large (accelerated) steps and confirm GameTime/getMSTime() track
    // the override rather than real elapsed wall time - the actual point of core patch 2.
    for (uint32 simMs = 0; simMs <= 5000; simMs += 1000)
    {
        Acore::Time::SetSimClockOverride(Milliseconds(simMs));
        GameTime::UpdateGameTimers();
        LOG_INFO("server.dpssim", "mod-dpssim: sim clock override={}ms -> getMSTime()={}ms, GameTime::GetGameTimeMS()={}ms",
            simMs, getMSTime(), uint32(GameTime::GetGameTimeMS().count()));
    }

    Acore::Time::ClearSimClockOverride();
    LOG_INFO("server.dpssim", "mod-dpssim: M1 skeleton smoke test complete, exiting.");
}

void AddSC_DpsSim()
{
    new DpsSimWorldScript();
}
