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

#ifndef MODULE_DPSSIM_H
#define MODULE_DPSSIM_H

#include "ScriptMgr.h"

#define MODULE_STRING "mod-dpssim"

// Entry point: bound to WorldScript::OnDpsSimRun(), which Main.cpp calls instead of the normal
// real-time WorldUpdateLoop() when DpsSim.Enabled = 1 (see WorldScript.h's doc comment on the
// hook, and .agents/plans/dps-sim-module/dps-sim-module.PLAN.md for the whole architecture).
class DpsSimWorldScript : public WorldScript
{
public:
    DpsSimWorldScript();

    void OnDpsSimRun() override;
};

#endif
