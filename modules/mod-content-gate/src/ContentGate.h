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

/*
 * mod-content-gate: engine glue. Feeds DisableMgr in memory from the conf (no `disables` table writes), loads the
 * bundle tables, starts/stops bundle events, re-applies after `.reload config` / `.reload disables`, and answers the
 * continent guard and other modules (IsInstanceOpen). Every DisableMgr / GameEventMgr write happens on the world
 * thread (boot hooks or WorldScript::OnUpdate, after the map threads have finished their tick).
 */

#ifndef MOD_CONTENT_GATE_H
#define MOD_CONTENT_GATE_H

#include "ContentGateRules.h"
#include "Define.h"
#include <atomic>
#include <mutex>
#include <string>
#include <vector>

class ChatHandler;

namespace ContentGate
{
    class Gate
    {
    public:
        static Gate* instance();

        // WorldScript::OnAfterConfigLoad: cache the raw conf (parsed once the DBC stores exist), set the
        // Wintergrasp override, and on a reload queue a full re-apply for the next world tick.
        void LoadConfig(bool reload);

        // DatabaseScript::OnAfterDatabaseLoadCreatureTemplates (after LoadDisables, before LoadQuests, the game
        // event start and OPvP init): maps, outdoor PvP, events and bundle members. Acts once.
        void ApplyAtBoot();

        // WorldScript::OnBeforeWorldInitialized (after the battleground templates exist): battlegrounds, sentinel,
        // bundle validation and the boot summary line.
        void FinishBoot();

        // WorldScript::OnUpdate (world thread, map threads idle): queued re-applies and the watchdog.
        void Update(uint32 diff);

        // `.gate reload`: re-read the bundle tables and re-apply the cached conf on the next world tick.
        void RequestReapply() { _reapplyRequested = true; }

        void PrintStatus(ChatHandler* handler);

        [[nodiscard]] bool IsEnabled() const { return _enabled; }
        [[nodiscard]] bool IsOutlandOpen() const { return _outlandOpen; }
        [[nodiscard]] bool IsNorthrendOpen() const { return _northrendOpen; }
        [[nodiscard]] bool IsDebug() const { return _debug; }

        // For other modules (dungeon difficulties WP-H): is this map difficulty open in the gate? Maps that are not
        // dungeons or raids are always open here. Any thread.
        [[nodiscard]] bool IsInstanceOpen(uint32 mapId, uint8 difficulty);

    private:
        Gate() = default;

        enum class Scope : uint8
        {
            BootEarly,      // maps, outdoor PvP, events, members
            BootLate,       // battlegrounds, sentinel
            Full            // everything (reload, watchdog)
        };

        void ParseAndLoad(bool loadBundles);
        void LoadBundles();
        void ValidateBundles();
        void Apply(Scope scope);
        void FullReapply(char const* reason);
        void RestartOpenedEvents(ClosedSetDiff const& diff);
        void LogConfigErrors() const;

        std::recursive_mutex _lock;             // guards the state below except the atomics; recursive because
                                                // starting or stopping an event spawns objects whose AI may
                                                // call IsInstanceOpen (go_scarab_gate) on this thread
        RawConfig _raw;
        Config _config;
        std::vector<Bundle> _bundles;
        std::vector<std::string> _bundleErrors;
        ClosedSet _closed;                      // what is applied now
        std::vector<std::string> _conflicts;    // DB `disables` rows that shadow the conf (cutover leftovers)
        std::vector<std::string> _restartNotes; // live changes the engine only reads at boot
        bool _bootApplied = false;
        bool _bootFinished = false;
        bool _bundleTablesPresent = false;
        uint32 _wintergraspAtBoot = 0;
        uint32 _watchdogTimer = 0;
        uint32 _watchdogTrips = 0;

        std::atomic<bool> _enabled{ false };
        std::atomic<bool> _outlandOpen{ true };
        std::atomic<bool> _northrendOpen{ true };
        std::atomic<bool> _debug{ false };
        std::atomic<bool> _reloadRequested{ false };
        std::atomic<bool> _reapplyRequested{ false };
    };
}

#define sContentGate ContentGate::Gate::instance()

#endif
