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

#ifndef MODULE_DPSSIM_SIMBOSSMECHANICS_H
#define MODULE_DPSSIM_SIMBOSSMECHANICS_H

#include "Define.h"
#include "ObjectGuid.h"
#include <string>
#include <utility>
#include <vector>

// The sim's side of the mod-boss-mechanics seam (that module's BossMechanicsSim.h, STAGE-M4 WP-B). mod-boss-mechanics
// is optional: a separate repo, and a module can be listed in DISABLED_AC_MODULES. All module source trees build into
// one target whose include path holds every ENABLED module's sources (modules/CMakeLists.txt), so
// `__has_include("BossMechanicsSim.h")` is true exactly when the module is built with the sim. Only
// SimBossMechanics.cpp includes the module header; everything else in mod-dpssim talks to this API, which holds no
// module types, so nothing else changes when the module is absent: every call is then a no-op that returns false
// (Available() tells the batch to refuse a mechanics run).
#if defined(__has_include)
#if __has_include("BossMechanicsSim.h")
#define DPSSIM_WITH_BOSS_MECHANICS 1
#endif
#endif
#ifndef DPSSIM_WITH_BOSS_MECHANICS
#define DPSSIM_WITH_BOSS_MECHANICS 0
#endif

class Creature;
class Player;

namespace SimMech
{
    // One FailureEvent of the module, copied into sim-side types (names, not enums). AtMs is the module's
    // GameTime::GetGameTimeMS() at the failure, which follows the sim clock.
    struct Failure
    {
        uint32 MapId = 0;
        ObjectGuid Encounter;
        ObjectGuid Player;      // empty for a group failure (MissedSoak)
        std::string Type;       // Hit, MissedSoak, MissedStack, MissedBait, Moved, OffSpot
        std::string Kind;       // Zone, Frontal, Spread, RunOut, Stack, Soak, Bait, HoldStill, Spot
        uint32 MechanicId = 0;
        uint32 Tag = 0;
        uint32 Damage = 0;
        uint32 AtMs = 0;
    };
    using Sink = void (*)(Failure const& failure);

    // One bot's module counters (Sim::BotStats), flattened into named numbers so the report writes whatever the
    // module holds without knowing its struct layout: Counters are MechanicBotCounters (outcomes as outcomeSafe,
    // outcomeMove, ...; the "...Last" fields left out), ModeMs the brain's time per mode, Cost the CostStats fields.
    // A name ending in "Max" is a maximum (the aggregate takes the max), every other count a sum.
    struct Stats
    {
        bool Valid = false;
        std::vector<std::pair<std::string, uint64>> Counters;
        std::vector<std::pair<std::string, uint64>> ModeMs;
        uint32 LeakMoves = 0;
        uint32 LeakCasts = 0;
        uint32 LeakTurns = 0;
        std::vector<std::pair<uint32, uint32>> LeakSpells;
        std::vector<std::pair<std::string, double>> Cost;
    };

    // True when the sim was built with mod-boss-mechanics
    [[nodiscard]] bool Available();

    // Sim::RegisterBotGlue: the bot glue's first-world-tick registration, now (the sim never ticks the world). True
    // when the glue is enabled (BossMechanics.Bots.Enable and playerbots).
    bool RegisterBotGlue();

    // Sim::ReconcileBot: true when the bot has the "boss mechanics" strategy afterwards
    bool ReconcileBot(Player* bot);

    // Sim::SetFailureSink with a converting adapter; nullptr removes it
    void SetSink(Sink sink);

    // Drill::ParseProgram: false with `err` for a program text the module would refuse (always false without the
    // module). `lengthMs` is when the program's last entry ends (0 for `none`).
    bool CheckProgram(std::string const& program, uint32& lengthMs, std::string& err);

    // Sim::StartProgram with the sim's options: the drill dice `seed`, flat damage `damage`, the scope player as a
    // member like the others (includeScopePlayer), and no loop (an iteration runs its program once)
    bool StartProgram(Creature* owner, ObjectGuid scopePlayer, std::string const& program, uint32 seed, int32 damage,
        std::string& err);
    void StopProgram(Creature* owner);

    // Sim::ReadBotStats / Sim::ResetBotStats
    bool ReadStats(Player const* bot, Stats& out);
    void ResetStats(Player const* bot);
}

#endif
