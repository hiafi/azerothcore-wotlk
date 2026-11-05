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

#include "ContentGate.h"
#include "Chat.h"
#include "Config.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "DisableMgr.h"
#include "GameEventMgr.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "StringFormat.h"
#include "World.h"
#include <algorithm>
#include <sstream>

namespace ContentGate
{
    namespace
    {
        // Watchdog sentinel: a loot disable on an item id that cannot exist. `.reload disables` wipes it with the
        // rest of the in-memory entries, which is how the watchdog notices.
        constexpr uint32 SENTINEL_LOOT_ENTRY = 0xFFFFFF00;

        constexpr char const* LOG_CAT = "module.content_gate";

        std::optional<MapShape> LookupMap(uint32 mapId)
        {
            MapEntry const* entry = sMapStore.LookupEntry(mapId);
            if (!entry || !entry->IsDungeon())
                return std::nullopt;

            MapShape shape;
            shape.raid = entry->IsRaid();
            shape.available = FLAG_DIFF_0;  // normal is always a valid key for DisableMgr
            for (uint8 d = 1; d < MAX_DIFFICULTY; ++d)
                if (GetMapDifficultyData(mapId, Difficulty(d)))
                    shape.available |= uint8(1 << d);
            return shape;
        }

        std::vector<std::pair<uint32_t, MapShape>> AllGateMaps()
        {
            std::vector<std::pair<uint32_t, MapShape>> maps;
            for (uint32 id = 0; id < sMapStore.GetNumRows(); ++id)
                if (std::optional<MapShape> shape = LookupMap(id))
                    maps.emplace_back(id, *shape);
            return maps;
        }

        std::vector<uint32_t> AllBattlegrounds()
        {
            std::vector<uint32_t> ids;
            for (uint32 id = 0; id < sBattlemasterListStore.GetNumRows(); ++id)
                if (sBattlemasterListStore.LookupEntry(id))
                    ids.push_back(id);
            return ids;
        }

        std::string MapName(uint32 mapId)
        {
            if (MapEntry const* entry = sMapStore.LookupEntry(mapId))
                return entry->name[0];
            return "?";
        }

        bool IsGameEventValid(uint32 eventId)
        {
            GameEventMgr::GameEventDataMap const& events = sGameEventMgr->GetEventMap();
            return eventId < events.size() && events[eventId].isValid();
        }

        bool IsKeyDisabled(DisableType type, uint32 entry)
        {
            return DisableMgr::IsDisabledFor(type, entry, nullptr);
        }

        // Closed difficulties of `mapId` that DisableMgr does not report closed.
        uint8 MissingMapFlags(uint32 mapId, uint8 flags)
        {
            uint8 missing = 0;
            for (uint8 d = 0; d < MAX_DIFFICULTY; ++d)
                if ((flags & (1 << d)) && !DisableMgr::IsDisabledFor(DISABLE_TYPE_MAP, mapId, nullptr, d))
                    missing |= uint8(1 << d);
            return missing;
        }

        uint8 ClosedMapFlags(uint32 mapId, uint8 flags)
        {
            uint8 closed = 0;
            for (uint8 d = 0; d < MAX_DIFFICULTY; ++d)
                if ((flags & (1 << d)) && DisableMgr::IsDisabledFor(DISABLE_TYPE_MAP, mapId, nullptr, d))
                    closed |= uint8(1 << d);
            return closed;
        }

        std::string JoinIds(std::set<uint32_t> const& ids)
        {
            std::string out;
            for (uint32_t id : ids)
            {
                if (!out.empty())
                    out += " ";
                out += std::to_string(id);
            }
            return out.empty() ? "-" : out;
        }

        std::string JoinNames(std::set<std::string> const& names)
        {
            std::string out;
            for (std::string const& name : names)
            {
                if (!out.empty())
                    out += " ";
                out += name;
            }
            return out.empty() ? "-" : out;
        }
    }

    Gate* Gate::instance()
    {
        static Gate instance;
        return &instance;
    }

    void Gate::LoadConfig(bool reload)
    {
        RawConfig raw;
        raw.enable = sConfigMgr->GetOption<bool>("ContentGate.Enable", true);
        for (std::string const& key : sConfigMgr->GetKeysByString("ContentGate.Open.Instances"))
            raw.openInstances.push_back(sConfigMgr->GetOption<std::string>(key, ""));
        raw.openBattlegrounds = sConfigMgr->GetOption<std::string>("ContentGate.Open.Battlegrounds", "");
        raw.openOutdoorPvP = sConfigMgr->GetOption<std::string>("ContentGate.Open.OutdoorPvP", "");
        raw.outlandOpen = sConfigMgr->GetOption<bool>("ContentGate.Open.Outland", false);
        raw.northrendOpen = sConfigMgr->GetOption<bool>("ContentGate.Open.Northrend", false);
        raw.closedEvents = sConfigMgr->GetOption<std::string>("ContentGate.Closed.Events", "");
        raw.openBundles = sConfigMgr->GetOption<std::string>("ContentGate.Open.Bundles", "");
        raw.wintergraspFollowsNorthrend = sConfigMgr->GetOption<bool>("ContentGate.Wintergrasp.FollowNorthrend", true);
        raw.watchdogMs = sConfigMgr->GetOption<uint32>("ContentGate.WatchdogMs", 5000);
        raw.debug = sConfigMgr->GetOption<bool>("ContentGate.Debug", false);

        // Wintergrasp is a battlefield, not a disable: keep all its processing off while Northrend is closed.
        // worldserver.conf was re-read just before this hook, so an open Northrend gets the file value back.
        if (raw.enable && raw.wintergraspFollowsNorthrend && !raw.northrendOpen)
            sWorld->setIntConfig(CONFIG_WINTERGRASP_ENABLE, 2);
        uint32 const wintergrasp = sWorld->getIntConfig(CONFIG_WINTERGRASP_ENABLE);

        _debug = raw.debug;

        std::lock_guard<std::recursive_mutex> guard(_lock);
        _raw = raw;
        if (!reload)
        {
            _wintergraspAtBoot = wintergrasp;
            return;
        }

        if (wintergrasp != _wintergraspAtBoot)
            _restartNotes.push_back(Acore::StringFormat("Wintergrasp.Enable is {} now but {} at boot: the battlefield "
                "only changes at the next restart.", wintergrasp, _wintergraspAtBoot));
        _reloadRequested = true;
    }

    void Gate::LoadBundles()
    {
        _bundles.clear();
        _bundleErrors.clear();

        QueryResult present = WorldDatabase.Query("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = "
            "DATABASE() AND TABLE_NAME IN ('content_gate_bundle', 'content_gate_bundle_disable')");
        _bundleTablesPresent = present && present->Fetch()[0].Get<uint64>() == 2;
        if (!_bundleTablesPresent)
        {
            _bundleErrors.push_back("bundle tables missing (module SQL not applied): no bundles loaded");
            return;
        }

        MapLookup const lookup = LookupMap;
        std::map<std::string, std::size_t> byName;
        std::map<uint32, std::string> eventOwner;

        if (QueryResult result = WorldDatabase.Query("SELECT `name`, `gameEvent`, `opensWith` "
            "FROM `content_gate_bundle` ORDER BY `name`"))
        {
            do
            {
                Field* fields = result->Fetch();
                Bundle bundle;
                bundle.name = fields[0].Get<std::string>();
                bundle.gameEvent = fields[1].Get<uint8>();
                bundle.opensWithText = fields[2].Get<std::string>();

                if (!IsValidBundleName(bundle.name))
                {
                    _bundleErrors.push_back("bundle '" + bundle.name + "': bad name ([a-z0-9_], 1-32), skipped");
                    continue;
                }

                std::string error;
                std::optional<OpensWith> atom = ParseOpensWith(bundle.opensWithText, lookup, error);
                if (!atom)
                {
                    // A bad atom must not open anything: the bundle stays closed unless opened by name.
                    _bundleErrors.push_back("bundle '" + bundle.name + "': " + error + " (opens by name only)");
                    atom = OpensWith();
                }
                bundle.opensWith = *atom;

                if (bundle.gameEvent)
                {
                    auto const [itr, inserted] = eventOwner.emplace(bundle.gameEvent, bundle.name);
                    if (!inserted)
                    {
                        _bundleErrors.push_back(Acore::StringFormat("bundle '{}': game event {} already belongs to "
                            "bundle '{}', event ignored", bundle.name, bundle.gameEvent, itr->second));
                        bundle.gameEvent = 0;
                    }
                }

                byName[bundle.name] = _bundles.size();
                _bundles.push_back(std::move(bundle));
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT `bundle`, `sourceType`, `entry` FROM "
            "`content_gate_bundle_disable` ORDER BY `bundle`, `sourceType`, `entry`"))
        {
            do
            {
                Field* fields = result->Fetch();
                std::string const name = fields[0].Get<std::string>();
                uint8 const type = fields[1].Get<uint8>();
                uint32 const entry = fields[2].Get<uint32>();

                auto const itr = byName.find(name);
                if (itr == byName.end())
                {
                    _bundleErrors.push_back(Acore::StringFormat("member ({}, {}) names unknown bundle '{}', skipped",
                        type, entry, name));
                    continue;
                }
                if (!IsAllowedMemberType(type))
                {
                    _bundleErrors.push_back(Acore::StringFormat("bundle '{}': member sourceType {} (entry {}) is not "
                        "1, 4 or 10, skipped", name, type, entry));
                    continue;
                }
                _bundles[itr->second].members.emplace_back(type, entry);
            } while (result->NextRow());
        }
    }

    // Needs quests, items and game events loaded: called from FinishBoot and on every reload after boot.
    void Gate::ValidateBundles()
    {
        for (Bundle const& bundle : _bundles)
        {
            if (bundle.gameEvent && !IsGameEventValid(bundle.gameEvent))
                _bundleErrors.push_back(Acore::StringFormat("bundle '{}': game event {} does not exist",
                    bundle.name, bundle.gameEvent));
            for (auto const& [type, entry] : bundle.members)
            {
                bool exists = true;
                if (type == DT_QUEST)
                    exists = sObjectMgr->GetQuestTemplate(entry) != nullptr;
                else if (type == DT_ACHIEVEMENT_CRITERIA)
                    exists = sAchievementCriteriaStore.LookupEntry(entry) != nullptr;
                else if (type == DT_LOOT)
                    exists = sObjectMgr->GetItemTemplate(entry) != nullptr;
                if (!exists)
                    _bundleErrors.push_back(Acore::StringFormat("bundle '{}': member ({}, {}) does not exist",
                        bundle.name, type, entry));
            }
        }
        for (std::string const& name : _config.openBundles)
            if (std::none_of(_bundles.begin(), _bundles.end(), [&](Bundle const& b) { return b.name == name; }))
                _bundleErrors.push_back("Open.Bundles names unknown bundle '" + name + "'");
    }

    void Gate::ParseAndLoad(bool loadBundles)
    {
        _config = ParseConfig(_raw, LookupMap);
        if (loadBundles)
            LoadBundles();
    }

    void Gate::LogConfigErrors() const
    {
        for (std::string const& error : _config.errors)
            LOG_ERROR(LOG_CAT, "[content-gate] conf: {}", error);
        for (std::string const& error : _bundleErrors)
            LOG_ERROR(LOG_CAT, "[content-gate] bundles: {}", error);
    }

    void Gate::Apply(Scope scope)
    {
        bool const early = scope == Scope::BootEarly || scope == Scope::Full;
        bool const late = scope == Scope::BootLate || scope == Scope::Full;
        if (early)
            _conflicts.clear();

        if (early)
        {
            for (auto const& [mapId, flags] : _closed.maps)
            {
                bool const dbRow = ClosedMapFlags(mapId, FLAG_ALL) != 0;
                sDisableMgr->AddDisable(DISABLE_TYPE_MAP, mapId, flags, "", "");
                if (uint8 const missing = MissingMapFlags(mapId, flags))
                    _conflicts.push_back(Acore::StringFormat("map {} ({}): a DB disables row keeps {} OPEN although "
                        "the conf closes it", mapId, MapName(mapId),
                        FlagsToModes(missing, sMapStore.LookupEntry(mapId)->IsRaid())));
                else if (dbRow)
                    _conflicts.push_back(Acore::StringFormat("map {} ({}): a DB disables row owns the key (cutover "
                        "should delete it)", mapId, MapName(mapId)));
            }
            for (auto const& [mapId, flags] : _config.openInstances)
                if (uint8 const shut = ClosedMapFlags(mapId, flags))
                    _conflicts.push_back(Acore::StringFormat("map {} ({}): open in the conf but {} closed by a DB "
                        "disables row", mapId, MapName(mapId),
                        FlagsToModes(shut, sMapStore.LookupEntry(mapId)->IsRaid())));

            for (uint32 type : _closed.outdoorPvP)
            {
                if (IsKeyDisabled(DISABLE_TYPE_OUTDOORPVP, type))
                    _conflicts.push_back(Acore::StringFormat("outdoor PvP {}: a DB disables row owns the key", type));
                sDisableMgr->AddDisable(DISABLE_TYPE_OUTDOORPVP, type, 0, "", "");
            }
            for (uint32 type : _config.openOutdoorPvP)
                if (IsKeyDisabled(DISABLE_TYPE_OUTDOORPVP, type))
                    _conflicts.push_back(Acore::StringFormat("outdoor PvP {}: open in the conf but closed by a DB "
                        "disables row", type));

            for (uint32 eventId : _closed.events)
                sDisableMgr->AddDisable(DISABLE_TYPE_GAME_EVENT, eventId, 0, "", "");
            for (LinkedEvent const& linked : LinkedEvents())
                if (!_closed.events.count(linked.event) && IsKeyDisabled(DISABLE_TYPE_GAME_EVENT, linked.event))
                    _conflicts.push_back(Acore::StringFormat("event {} ({}): opens with its switch but a DB disables "
                        "row keeps it closed", linked.event, linked.name));

            for (auto const& [type, entry] : _closed.members)
                sDisableMgr->AddDisable(DisableType(type), entry, 0, "", "");

            for (Bundle const& bundle : _bundles)
            {
                if (!_closed.openBundles.count(bundle.name))
                    continue;
                if (bundle.gameEvent && IsKeyDisabled(DISABLE_TYPE_GAME_EVENT, bundle.gameEvent))
                    _conflicts.push_back(Acore::StringFormat("bundle '{}' is open but a DB disables row keeps its "
                        "event {} closed", bundle.name, bundle.gameEvent));
                for (auto const& [type, entry] : bundle.members)
                    if (IsKeyDisabled(DisableType(type), entry))
                        _conflicts.push_back(Acore::StringFormat("bundle '{}' is open but a DB disables row keeps "
                            "member ({}, {}) closed", bundle.name, type, entry));
            }
        }

        if (late)
        {
            for (uint32 bg : _closed.battlegrounds)
            {
                if (IsKeyDisabled(DISABLE_TYPE_BATTLEGROUND, bg))
                    _conflicts.push_back(Acore::StringFormat("battleground {}: a DB disables row owns the key", bg));
                sDisableMgr->AddDisable(DISABLE_TYPE_BATTLEGROUND, bg, 0, "", "");
            }
            for (uint32 bg : _config.openBattlegrounds)
                if (IsKeyDisabled(DISABLE_TYPE_BATTLEGROUND, bg))
                    _conflicts.push_back(Acore::StringFormat("battleground {}: open in the conf but closed by a DB "
                        "disables row (a DB-closed battleground also has no template until a restart)", bg));

            sDisableMgr->AddDisable(DISABLE_TYPE_LOOT, SENTINEL_LOOT_ENTRY, 0, "", "");
        }

        _outlandOpen = !_closed.outlandClosed;
        _northrendOpen = !_closed.northrendClosed;
    }

    void Gate::ApplyAtBoot()
    {
        std::lock_guard<std::recursive_mutex> guard(_lock);
        if (_bootApplied)
            return;
        _bootApplied = true;

        _enabled = _raw.enable;
        if (!_raw.enable)
        {
            _outlandOpen = true;
            _northrendOpen = true;
            LOG_INFO(LOG_CAT, "[content-gate] disabled (ContentGate.Enable = 0): nothing is gated");
            return;
        }

        ParseAndLoad(true);
        _closed = ComputeClosedSet(_config, AllGateMaps(), AllBattlegrounds(), _bundles);
        Apply(Scope::BootEarly);
    }

    void Gate::FinishBoot()
    {
        std::lock_guard<std::recursive_mutex> guard(_lock);
        if (_bootFinished)
            return;
        _bootFinished = true;
        if (!_enabled)
            return;

        if (!_bootApplied)
        {
            // The creature template hook did not run (should not happen): fall back to a full apply.
            LOG_ERROR(LOG_CAT, "[content-gate] boot hook missed; applying now (quests miss boot post-processing)");
            _bootApplied = true;
            ParseAndLoad(true);
            _closed = ComputeClosedSet(_config, AllGateMaps(), AllBattlegrounds(), _bundles);
            Apply(Scope::Full);
        }
        else
            Apply(Scope::BootLate);

        ValidateBundles();
        LogConfigErrors();
        for (std::string const& conflict : _conflicts)
            LOG_WARN(LOG_CAT, "[content-gate] conflict: {}", conflict);

        LOG_INFO(LOG_CAT, "[content-gate] {} instance difficulties closed, {} bundles open ({} closed), "
            "{} battlegrounds closed, {} outdoor PvP closed, {} events closed, Outland {}, Northrend {}",
            _closed.ClosedDifficultyCount(), _closed.openBundles.size(), _closed.closedBundles.size(),
            _closed.battlegrounds.size(), _closed.outdoorPvP.size(), _closed.events.size(),
            _closed.outlandClosed ? "closed" : "open", _closed.northrendClosed ? "closed" : "open");
    }

    void Gate::RestartOpenedEvents(ClosedSetDiff const& diff)
    {
        for (uint32 eventId : diff.openedEvents)
        {
            if (!IsGameEventValid(eventId) || IsKeyDisabled(DISABLE_TYPE_GAME_EVENT, eventId))
                continue;
            if (sGameEventMgr->IsActiveEvent(eventId) || !sGameEventMgr->CheckOneGameEvent(eventId))
                continue;
            sGameEventMgr->StartEvent(eventId);
            LOG_INFO(LOG_CAT, "[content-gate] started game event {} (opened)", eventId);
        }
    }

    void Gate::FullReapply(char const* reason)
    {
        std::lock_guard<std::recursive_mutex> guard(_lock);

        ClosedSet before = _closed;
        if (!_enabled)
        {
            before = ClosedSet();
            before.outlandClosed = false;
            before.northrendClosed = false;
        }

        _enabled = _raw.enable;
        ClosedSet after;
        after.outlandClosed = false;
        after.northrendClosed = false;
        if (_raw.enable)
        {
            ParseAndLoad(true);
            ValidateBundles();
            after = ComputeClosedSet(_config, AllGateMaps(), AllBattlegrounds(), _bundles);
        }

        // DisableMgr has no remove: rebuild the DB rows, then add the module's set on top.
        sDisableMgr->LoadDisables();
        sDisableMgr->CheckQuestDisables();
        _closed = after;
        if (_raw.enable)
            Apply(Scope::Full);
        else
        {
            _conflicts.clear();
            _outlandOpen = true;
            _northrendOpen = true;
        }

        ClosedSetDiff const diff = Diff(before, after);
        RestartOpenedEvents(diff);
        if (diff.outdoorPvPChanged)
            _restartNotes.push_back("outdoor PvP changed: OutdoorPvPMgr reads its disables at boot only, restart to "
                "apply");
        if (diff.questMembersOpened)
            _restartNotes.push_back("bundle quests opened live: they miss the boot quest post-processing until the "
                "next restart");

        LogConfigErrors();
        for (std::string const& conflict : _conflicts)
            LOG_WARN(LOG_CAT, "[content-gate] conflict: {}", conflict);
        LOG_INFO(LOG_CAT, "[content-gate] re-applied ({}): {} instance difficulties closed, {} bundles open "
            "({} closed), opened bundles: {}, closed bundles: {}, opened events: {}, closed events: {}", reason,
            _closed.ClosedDifficultyCount(), _closed.openBundles.size(), _closed.closedBundles.size(),
            JoinNames(diff.openedBundles), JoinNames(diff.closedBundles), JoinIds(diff.openedEvents),
            JoinIds(diff.closedEvents));
    }

    void Gate::Update(uint32 diff)
    {
        if (!_bootFinished)
            return;

        if (_reloadRequested.exchange(false))
        {
            _reapplyRequested = false;
            FullReapply(".reload config");
            _watchdogTimer = 0;
            return;
        }
        if (_reapplyRequested.exchange(false))
        {
            FullReapply(".gate reload");
            _watchdogTimer = 0;
            return;
        }

        if (!_enabled)
            return;

        _watchdogTimer += diff;
        if (_watchdogTimer < _config.watchdogMs)
            return;
        _watchdogTimer = 0;

        if (IsKeyDisabled(DISABLE_TYPE_LOOT, SENTINEL_LOOT_ENTRY))
            return;

        // Someone ran `.reload disables` (or anything else that calls LoadDisables): the DB rows are back, ours
        // are gone. Put ours back on top; no LoadDisables needed.
        std::lock_guard<std::recursive_mutex> guard(_lock);
        ++_watchdogTrips;
        LOG_WARN(LOG_CAT, "[content-gate] watchdog: in-memory disables were reloaded, re-applying the gate");
        Apply(Scope::Full);
    }

    bool Gate::IsInstanceOpen(uint32 mapId, uint8 difficulty)
    {
        if (!_enabled)
            return true;
        std::lock_guard<std::recursive_mutex> guard(_lock);
        auto const itr = _closed.maps.find(mapId);
        if (itr == _closed.maps.end())
            return true;
        Difficulty diff = Difficulty(difficulty);
        GetDownscaledMapDifficultyData(mapId, diff);
        return !(itr->second & (1 << diff));
    }

    void Gate::PrintStatus(ChatHandler* handler)
    {
        std::lock_guard<std::recursive_mutex> guard(_lock);
        bool const sentinel = IsKeyDisabled(DISABLE_TYPE_LOOT, SENTINEL_LOOT_ENTRY);
        handler->PSendSysMessage("Content gate: {}; sentinel {}; watchdog re-applies since boot: {}",
            _enabled ? "enabled" : "DISABLED", sentinel ? "present" : "MISSING", _watchdogTrips);
        if (!_enabled)
            return;

        std::string open;
        for (auto const& [mapId, flags] : _config.openInstances)
        {
            MapEntry const* entry = sMapStore.LookupEntry(mapId);
            open += Acore::StringFormat("{}{}:{}", open.empty() ? "" : " ", mapId,
                FlagsToModes(flags, entry && entry->IsRaid()));
        }
        handler->PSendSysMessage("Open instances: {}", open.empty() ? "-" : open);
        handler->PSendSysMessage("Closed: {} instance difficulties on {} maps", _closed.ClosedDifficultyCount(),
            _closed.maps.size());
        handler->PSendSysMessage("Battlegrounds open: {} | closed: {}", JoinIds(_config.openBattlegrounds),
            JoinIds(_closed.battlegrounds));
        handler->PSendSysMessage("Outdoor PvP open: {} | Outland: {} | Northrend: {} | Wintergrasp.Enable: {}",
            JoinIds(_config.openOutdoorPvP), _closed.outlandClosed ? "closed" : "open",
            _closed.northrendClosed ? "closed" : "open", sWorld->getIntConfig(CONFIG_WINTERGRASP_ENABLE));
        handler->PSendSysMessage("Events closed: {}", JoinIds(_closed.events));

        if (!_bundleTablesPresent)
            handler->PSendSysMessage("Bundles: tables missing (module SQL not applied)");
        for (Bundle const& bundle : _bundles)
        {
            bool const isOpen = _closed.openBundles.count(bundle.name) != 0;
            bool const active = bundle.gameEvent && sGameEventMgr->IsActiveEvent(bundle.gameEvent);
            handler->PSendSysMessage("Bundle {}: {} (opensWith '{}'{}), event {} {}, {} members", bundle.name,
                isOpen ? "OPEN" : "closed", bundle.opensWithText,
                _config.openBundles.count(bundle.name) ? ", opened by name" : "", bundle.gameEvent,
                bundle.gameEvent ? (active ? "active" : "inactive") : "-", bundle.members.size());
        }

        for (std::string const& error : _config.errors)
            handler->PSendSysMessage("Conf error: {}", error);
        for (std::string const& error : _bundleErrors)
            handler->PSendSysMessage("Bundle error: {}", error);
        for (std::string const& conflict : _conflicts)
            handler->PSendSysMessage("Conflict: {}", conflict);
        for (std::string const& note : _restartNotes)
            handler->PSendSysMessage("Restart needed: {}", note);
    }
}
