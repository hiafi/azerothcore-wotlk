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
 * mod-content-gate: pure rules (no server headers). Conf parsing, mode -> difficulty flags per map, the closed set the
 * module feeds to DisableMgr, bundle `opensWith` resolution, reload diffs and the continent zone lists. Host-tested by
 * tests/run.sh; the engine glue (ContentGate.cpp) only translates these results into DisableMgr / GameEventMgr calls.
 */

#ifndef MOD_CONTENT_GATE_RULES_H
#define MOD_CONTENT_GATE_RULES_H

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace ContentGate
{
    // Difficulty bits, identical to DisableMgr's map flags: bit d is set for Difficulty d
    // (5-man: 1 normal, 2 heroic; raid: 1 10N, 2 25N, 4 10H, 8 25H).
    constexpr uint8_t FLAG_DIFF_0 = 0x1;
    constexpr uint8_t FLAG_DIFF_1 = 0x2;
    constexpr uint8_t FLAG_DIFF_2 = 0x4;
    constexpr uint8_t FLAG_DIFF_3 = 0x8;
    constexpr uint8_t FLAG_ALL = 0xF;

    // DisableType values the module uses (DisableMgr.h); repeated here so the rules stay server-free.
    constexpr uint8_t DT_QUEST = 1;
    constexpr uint8_t DT_ACHIEVEMENT_CRITERIA = 4;
    constexpr uint8_t DT_LOOT = 10;

    constexpr uint32_t MAP_EASTERN_KINGDOMS = 0;
    constexpr uint32_t MAP_KALIMDOR = 1;
    constexpr uint32_t MAP_OUTLAND = 530;
    constexpr uint32_t MAP_NORTHREND = 571;

    constexpr uint32_t MAX_OUTDOOR_PVP_TYPE = 7;    // OutdoorPvPTypes 1..7
    constexpr uint32_t BG_ALL_ARENAS = 6;           // BattlemasterList "All Arenas" (BATTLEGROUND_AA)

    // A map the gate knows about: every Map.dbc map with IsDungeon(). `available` has bit d set for each
    // difficulty d with a MapDifficulty row.
    struct MapShape
    {
        bool raid = false;
        uint8_t available = 0;
    };

    // Returns the shape of a dungeon or raid map, or nullopt for any other map id.
    using MapLookup = std::function<std::optional<MapShape>(uint32_t)>;

    inline std::string Upper(std::string_view text)
    {
        std::string out(text);
        std::transform(out.begin(), out.end(), out.begin(), [](unsigned char c) { return std::toupper(c); });
        return out;
    }

    inline std::string Lower(std::string_view text)
    {
        std::string out(text);
        std::transform(out.begin(), out.end(), out.begin(), [](unsigned char c) { return std::tolower(c); });
        return out;
    }

    // Splits on any of `separators`, dropping empty pieces.
    inline std::vector<std::string> Split(std::string_view text, std::string_view separators)
    {
        std::vector<std::string> out;
        std::string current;
        for (char c : text)
        {
            if (separators.find(c) != std::string_view::npos)
            {
                if (!current.empty())
                    out.push_back(current);
                current.clear();
            }
            else
                current.push_back(c);
        }
        if (!current.empty())
            out.push_back(current);
        return out;
    }

    inline std::optional<uint32_t> ParseUInt(std::string_view text)
    {
        if (text.empty() || text.size() > 10)
            return std::nullopt;
        uint64_t value = 0;
        for (char c : text)
        {
            if (c < '0' || c > '9')
                return std::nullopt;
            value = value * 10 + uint64_t(c - '0');
        }
        if (value > 0xFFFFFFFFull)
            return std::nullopt;
        return uint32_t(value);
    }

    // One mode token -> difficulty bit. 5-man: N, H. Raid: N (= 10N), 10N, 25N, 10H, 25H.
    inline std::optional<uint8_t> ModeFlag(std::string_view token, bool raid)
    {
        std::string const mode = Upper(token);
        if (!raid)
        {
            if (mode == "N")
                return FLAG_DIFF_0;
            if (mode == "H")
                return FLAG_DIFF_1;
            return std::nullopt;
        }
        if (mode == "N" || mode == "10N")
            return FLAG_DIFF_0;
        if (mode == "25N")
            return FLAG_DIFF_1;
        if (mode == "10H")
            return FLAG_DIFF_2;
        if (mode == "25H")
            return FLAG_DIFF_3;
        return std::nullopt;
    }

    // Flags -> "N,H" / "10N,25N,10H,25H" for status output.
    inline std::string FlagsToModes(uint8_t flags, bool raid)
    {
        static char const* const fiveMan[] = { "N", "H", "?", "?" };
        static char const* const raidModes[] = { "10N", "25N", "10H", "25H" };
        std::string out;
        for (uint8_t d = 0; d < 4; ++d)
        {
            if (!(flags & (1 << d)))
                continue;
            if (!out.empty())
                out += ",";
            out += raid ? raidModes[d] : fiveMan[d];
        }
        return out;
    }

    // `ContentGate.Open.Instances.*`: space separated `<map>:<modes>`, modes comma separated, `*` = every difficulty
    // the map has. Bad entries are reported in `errors` and skipped; the rest still apply.
    inline void ParseInstances(std::string_view text, MapLookup const& lookup, std::map<uint32_t, uint8_t>& open,
        std::vector<std::string>& errors)
    {
        for (std::string const& entry : Split(text, " \t"))
        {
            std::size_t const colon = entry.find(':');
            if (colon == std::string::npos)
            {
                errors.push_back("instance entry '" + entry + "' has no ':<modes>' part");
                continue;
            }
            std::optional<uint32_t> const mapId = ParseUInt(std::string_view(entry).substr(0, colon));
            if (!mapId)
            {
                errors.push_back("instance entry '" + entry + "' has a bad map id");
                continue;
            }
            std::optional<MapShape> const shape = lookup(*mapId);
            if (!shape)
            {
                errors.push_back("instance entry '" + entry + "': map " + std::to_string(*mapId) +
                    " is not a dungeon or raid map");
                continue;
            }
            std::vector<std::string> const modes = Split(std::string_view(entry).substr(colon + 1), ",");
            if (modes.empty())
            {
                errors.push_back("instance entry '" + entry + "' lists no modes");
                continue;
            }
            for (std::string const& mode : modes)
            {
                if (mode == "*")
                {
                    open[*mapId] |= shape->available;
                    continue;
                }
                std::optional<uint8_t> const flag = ModeFlag(mode, shape->raid);
                if (!flag)
                {
                    errors.push_back("instance entry '" + entry + "': mode '" + mode + "' is not valid for a " +
                        (shape->raid ? "raid (use N, 10N, 25N, 10H, 25H)" : "5-man (use N, H)"));
                    continue;
                }
                if (!(shape->available & *flag))
                {
                    errors.push_back("instance entry '" + entry + "': map " + std::to_string(*mapId) +
                        " has no " + Upper(mode) + " difficulty (no MapDifficulty row)");
                    continue;
                }
                open[*mapId] |= *flag;
            }
        }
    }

    // Space or comma separated unsigned ids.
    inline std::set<uint32_t> ParseIdList(std::string_view text, std::string_view what,
        std::vector<std::string>& errors)
    {
        std::set<uint32_t> out;
        for (std::string const& token : Split(text, " \t,"))
        {
            if (std::optional<uint32_t> const id = ParseUInt(token))
                out.insert(*id);
            else
                errors.push_back(std::string(what) + ": '" + token + "' is not a number");
        }
        return out;
    }

    inline bool IsValidBundleName(std::string_view name)
    {
        if (name.empty() || name.size() > 32)
            return false;
        return std::all_of(name.begin(), name.end(),
            [](char c) { return (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_'; });
    }

    // What a bundle (or a linked stock event) opens with.
    struct OpensWith
    {
        enum class Kind : uint8_t
        {
            None,           // only by name in ContentGate.Open.Bundles
            Map,            // map:<id>:<mode>
            Battleground,   // bg:<BattlemasterList id>
            Outland,
            Northrend
        };

        Kind kind = Kind::None;
        uint32_t id = 0;
        uint8_t flag = 0;
    };

    inline std::optional<OpensWith> ParseOpensWith(std::string_view text, MapLookup const& lookup, std::string& error)
    {
        std::string const atom = Lower(text);
        OpensWith out;
        if (atom.empty())
            return out;
        if (atom == "outland")
        {
            out.kind = OpensWith::Kind::Outland;
            return out;
        }
        if (atom == "northrend")
        {
            out.kind = OpensWith::Kind::Northrend;
            return out;
        }
        std::vector<std::string> const parts = Split(atom, ":");
        if (parts.size() == 2 && parts[0] == "bg")
        {
            if (std::optional<uint32_t> const id = ParseUInt(parts[1]))
            {
                out.kind = OpensWith::Kind::Battleground;
                out.id = *id;
                return out;
            }
            error = "opensWith '" + std::string(text) + "': bad battleground id";
            return std::nullopt;
        }
        if (parts.size() == 3 && parts[0] == "map")
        {
            std::optional<uint32_t> const mapId = ParseUInt(parts[1]);
            if (!mapId)
            {
                error = "opensWith '" + std::string(text) + "': bad map id";
                return std::nullopt;
            }
            std::optional<MapShape> const shape = lookup(*mapId);
            if (!shape)
            {
                error = "opensWith '" + std::string(text) + "': map " + parts[1] + " is not a dungeon or raid map";
                return std::nullopt;
            }
            std::optional<uint8_t> const flag = ModeFlag(parts[2], shape->raid);
            if (!flag || !(shape->available & *flag))
            {
                error = "opensWith '" + std::string(text) + "': map " + parts[1] + " has no mode '" +
                    Upper(parts[2]) + "'";
                return std::nullopt;
            }
            out.kind = OpensWith::Kind::Map;
            out.id = *mapId;
            out.flag = *flag;
            return out;
        }
        error = "opensWith '" + std::string(text) + "': expected map:<id>:<mode>, bg:<id>, outland, northrend or empty";
        return std::nullopt;
    }

    // Parsed module conf.
    struct Config
    {
        bool enable = true;
        std::map<uint32_t, uint8_t> openInstances;      // map -> open difficulty flags
        std::set<uint32_t> openBattlegrounds;           // BattlemasterList ids
        std::set<uint32_t> openOutdoorPvP;              // OutdoorPvPTypes
        bool outlandOpen = false;
        bool northrendOpen = false;
        std::set<uint32_t> closedEvents;                // extra stock game events kept closed
        std::set<std::string> openBundles;              // bundles opened by name
        bool wintergraspFollowsNorthrend = true;
        uint32_t watchdogMs = 5000;
        bool debug = false;
        std::vector<std::string> errors;
    };

    // Raw conf strings, as read from sConfigMgr (or written by a test).
    struct RawConfig
    {
        bool enable = true;
        std::vector<std::string> openInstances;         // every ContentGate.Open.Instances.* value
        std::string openBattlegrounds;
        std::string openOutdoorPvP;
        bool outlandOpen = false;
        bool northrendOpen = false;
        std::string closedEvents;
        std::string openBundles;
        bool wintergraspFollowsNorthrend = true;
        uint32_t watchdogMs = 5000;
        bool debug = false;
    };

    inline Config ParseConfig(RawConfig const& raw, MapLookup const& lookup)
    {
        Config cfg;
        cfg.enable = raw.enable;
        for (std::string const& value : raw.openInstances)
            ParseInstances(value, lookup, cfg.openInstances, cfg.errors);
        cfg.openBattlegrounds = ParseIdList(raw.openBattlegrounds, "Open.Battlegrounds", cfg.errors);
        cfg.openOutdoorPvP = ParseIdList(raw.openOutdoorPvP, "Open.OutdoorPvP", cfg.errors);
        for (auto itr = cfg.openOutdoorPvP.begin(); itr != cfg.openOutdoorPvP.end();)
        {
            if (*itr == 0 || *itr > MAX_OUTDOOR_PVP_TYPE)
            {
                cfg.errors.push_back("Open.OutdoorPvP: " + std::to_string(*itr) + " is not an outdoor PvP type (1-7)");
                itr = cfg.openOutdoorPvP.erase(itr);
            }
            else
                ++itr;
        }
        cfg.outlandOpen = raw.outlandOpen;
        cfg.northrendOpen = raw.northrendOpen;
        cfg.closedEvents = ParseIdList(raw.closedEvents, "Closed.Events", cfg.errors);
        for (std::string const& name : Split(raw.openBundles, " \t,"))
        {
            std::string const lowered = Lower(name);
            if (IsValidBundleName(lowered))
                cfg.openBundles.insert(lowered);
            else
                cfg.errors.push_back("Open.Bundles: '" + name + "' is not a valid bundle name ([a-z0-9_], 1-32)");
        }
        cfg.wintergraspFollowsNorthrend = raw.wintergraspFollowsNorthrend;
        cfg.watchdogMs = std::max<uint32_t>(raw.watchdogMs, 1000);
        cfg.debug = raw.debug;
        return cfg;
    }

    inline bool IsAtomOpen(OpensWith const& atom, Config const& cfg)
    {
        switch (atom.kind)
        {
            case OpensWith::Kind::None:
                return false;
            case OpensWith::Kind::Map:
            {
                auto const itr = cfg.openInstances.find(atom.id);
                return itr != cfg.openInstances.end() && (itr->second & atom.flag);
            }
            case OpensWith::Kind::Battleground:
                return cfg.openBattlegrounds.count(atom.id) != 0;
            case OpensWith::Kind::Outland:
                return cfg.outlandOpen;
            case OpensWith::Kind::Northrend:
                return cfg.northrendOpen;
        }
        return false;
    }

    // One bundle as loaded from content_gate_bundle + content_gate_bundle_disable.
    struct Bundle
    {
        std::string name;
        uint32_t gameEvent = 0;                                 // 0 = no event
        std::string opensWithText;
        OpensWith opensWith;
        std::vector<std::pair<uint8_t, uint32_t>> members;      // (DisableType, entry) applied while closed
    };

    inline bool IsBundleOpen(Bundle const& bundle, Config const& cfg)
    {
        return cfg.openBundles.count(bundle.name) != 0 || IsAtomOpen(bundle.opensWith, cfg);
    }

    inline bool IsAllowedMemberType(uint8_t type)
    {
        return type == DT_QUEST || type == DT_ACHIEVEMENT_CRITERIA || type == DT_LOOT;
    }

    // Stock game events that follow a switch instead of being listed (Call to Arms follows its battleground, the
    // arena seasons follow "All Arenas", the Northrend and Quel'Danas events follow their continent).
    struct LinkedEvent
    {
        uint32_t event;
        OpensWith atom;
        char const* name;
    };

    inline std::vector<LinkedEvent> const& LinkedEvents()
    {
        using K = OpensWith::Kind;
        static std::vector<LinkedEvent> const events = []
        {
            std::vector<LinkedEvent> v = {
                { 18, { K::Battleground, 1, 0 }, "Call to Arms: Alterac Valley" },
                { 19, { K::Battleground, 2, 0 }, "Call to Arms: Warsong Gulch" },
                { 20, { K::Battleground, 3, 0 }, "Call to Arms: Arathi Basin" },
                { 21, { K::Battleground, 7, 0 }, "Call to Arms: Eye of the Storm" },
                { 53, { K::Battleground, 9, 0 }, "Call to Arms: Strand of the Ancients" },
                { 54, { K::Battleground, 30, 0 }, "Call to Arms: Isle of Conquest" },
                { 76, { K::Battleground, BG_ALL_ARENAS, 0 }, "Arena Season 2" },
                { 63, { K::Northrend, 0, 0 }, "Kalu'ak Fishing Derby Turn-ins" },
                { 64, { K::Northrend, 0, 0 }, "Kalu'ak Fishing Derby Fishing Pools" },
            };
            for (uint32_t season = 55; season <= 60; ++season)
                v.push_back({ season, { K::Battleground, BG_ALL_ARENAS, 0 }, "Arena Season 3-8" });
            for (uint32_t phase = 101; phase <= 115; ++phase)
                v.push_back({ phase, { K::Outland, 0, 0 }, "Sun's Reach Reclamation" });
            return v;
        }();
        return events;
    }

    // Everything the module keeps closed for one config + bundle set.
    struct ClosedSet
    {
        std::map<uint32_t, uint8_t> maps;                   // map -> closed difficulty flags (never 0)
        std::set<uint32_t> battlegrounds;
        std::set<uint32_t> outdoorPvP;
        std::set<uint32_t> events;
        std::set<std::pair<uint8_t, uint32_t>> members;     // closed bundles' member disables
        std::set<std::string> openBundles;
        std::set<std::string> closedBundles;
        bool outlandClosed = true;
        bool northrendClosed = true;

        uint32_t ClosedDifficultyCount() const
        {
            uint32_t count = 0;
            for (auto const& [mapId, flags] : maps)
                for (uint8_t d = 0; d < 4; ++d)
                    if (flags & (1 << d))
                        ++count;
            return count;
        }
    };

    inline ClosedSet ComputeClosedSet(Config const& cfg, std::vector<std::pair<uint32_t, MapShape>> const& allMaps,
        std::vector<uint32_t> const& allBattlegrounds, std::vector<Bundle> const& bundles)
    {
        ClosedSet out;
        for (auto const& [mapId, shape] : allMaps)
        {
            uint8_t open = 0;
            if (auto const itr = cfg.openInstances.find(mapId); itr != cfg.openInstances.end())
                open = itr->second;
            uint8_t const closed = shape.available & uint8_t(~open);
            if (closed)
                out.maps[mapId] = closed;
        }
        for (uint32_t bg : allBattlegrounds)
            if (!cfg.openBattlegrounds.count(bg))
                out.battlegrounds.insert(bg);
        for (uint32_t type = 1; type <= MAX_OUTDOOR_PVP_TYPE; ++type)
            if (!cfg.openOutdoorPvP.count(type))
                out.outdoorPvP.insert(type);
        out.events = cfg.closedEvents;
        for (LinkedEvent const& linked : LinkedEvents())
            if (!IsAtomOpen(linked.atom, cfg))
                out.events.insert(linked.event);
        for (Bundle const& bundle : bundles)
        {
            if (IsBundleOpen(bundle, cfg))
            {
                out.openBundles.insert(bundle.name);
                continue;
            }
            out.closedBundles.insert(bundle.name);
            if (bundle.gameEvent)
                out.events.insert(bundle.gameEvent);
            for (auto const& member : bundle.members)
                out.members.insert(member);
        }
        out.outlandClosed = !cfg.outlandOpen;
        out.northrendClosed = !cfg.northrendOpen;
        return out;
    }

    // What changed between two applied sets (reload reporting and event restarts).
    struct ClosedSetDiff
    {
        std::set<uint32_t> openedEvents;        // closed before, open now: the glue restarts them if due
        std::set<uint32_t> closedEvents;
        std::set<std::string> openedBundles;
        std::set<std::string> closedBundles;
        bool outdoorPvPChanged = false;         // the engine reads OPvP disables at boot only
        bool questMembersOpened = false;        // opened quests miss boot post-processing until a restart
    };

    inline ClosedSetDiff Diff(ClosedSet const& before, ClosedSet const& after)
    {
        ClosedSetDiff diff;
        for (uint32_t event : before.events)
            if (!after.events.count(event))
                diff.openedEvents.insert(event);
        for (uint32_t event : after.events)
            if (!before.events.count(event))
                diff.closedEvents.insert(event);
        for (std::string const& name : before.closedBundles)
            if (after.openBundles.count(name))
                diff.openedBundles.insert(name);
        for (std::string const& name : before.openBundles)
            if (after.closedBundles.count(name))
                diff.closedBundles.insert(name);
        diff.outdoorPvPChanged = before.outdoorPvP != after.outdoorPvP;
        for (auto const& member : before.members)
            if (member.first == DT_QUEST && !after.members.count(member))
                diff.questMembersOpened = true;
        return diff;
    }

    // Outland proper on map 530: every zone but the Blood Elf and Draenei starting zones and their cities.
    // Isle of Quel'Danas counts as Outland (TBC content).
    inline bool IsOutlandProperZone(uint32_t zoneId)
    {
        switch (zoneId)
        {
            case 3483:  // Hellfire Peninsula
            case 3518:  // Nagrand
            case 3519:  // Terokkar Forest
            case 3520:  // Shadowmoon Valley
            case 3521:  // Zangarmarsh
            case 3522:  // Blade's Edge Mountains
            case 3523:  // Netherstorm
            case 3703:  // Shattrath City
            case 4080:  // Isle of Quel'Danas
                return true;
            default:
                return false;
        }
    }

    enum class Continent : uint8_t
    {
        Allowed,
        Outland,
        Northrend
    };

    // Which closed continent (if any) a position on `mapId` in `zoneId` belongs to.
    inline Continent ClosedContinentAt(uint32_t mapId, uint32_t zoneId, bool outlandOpen, bool northrendOpen)
    {
        if (mapId == MAP_NORTHREND && !northrendOpen)
            return Continent::Northrend;
        if (mapId == MAP_OUTLAND && !outlandOpen && IsOutlandProperZone(zoneId))
            return Continent::Outland;
        return Continent::Allowed;
    }

    struct Spot
    {
        uint32_t map;
        float x, y, z, o;
    };

    // Old-world docks of the Northrend transports (dockmaster / zeppelin master stand positions): a passenger the
    // gate refuses at the map hop is put back here.
    struct Dock
    {
        uint32_t transportEntry;
        Spot spot;
        char const* name;
    };

    inline std::vector<Dock> const& NorthrendDocks()
    {
        static std::vector<Dock> const docks = {
            { 181688, { MAP_EASTERN_KINGDOMS, -3726.6f, -576.8f, 4.6f, 4.17f }, "Menethil Harbor (Northspear)" },
            { 181689, { MAP_EASTERN_KINGDOMS, 2058.0f, 357.8f, 82.6f, 5.35f }, "Tirisfal tower (Cloudkisser)" },
            { 186238, { MAP_KALIMDOR, 1174.1f, -4152.4f, 51.7f, 3.33f }, "Orgrimmar zeppelin tower (The Mighty Wind)" },
            { 190536, { MAP_EASTERN_KINGDOMS, -8302.7f, 1402.0f, 5.3f, 5.36f }, "Stormwind (Stormwind's Pride)" },
        };
        return docks;
    }

    inline std::optional<Spot> DockForTransport(uint32_t transportEntry)
    {
        for (Dock const& dock : NorthrendDocks())
            if (dock.transportEntry == transportEntry)
                return dock.spot;
        return std::nullopt;
    }

    // Blasted Lands side of the Dark Portal (the stock areatrigger 4352 target).
    constexpr Spot DARK_PORTAL_BLASTED_LANDS = { MAP_EASTERN_KINGDOMS, -11877.7f, -3204.49f, -18.49f, 0.23f };
    // Last-resort bounce targets when a player's homebind is itself behind a closed gate.
    constexpr Spot STORMWIND = { MAP_EASTERN_KINGDOMS, -8833.38f, 628.628f, 94.0066f, 1.06535f };
    constexpr Spot ORGRIMMAR = { MAP_KALIMDOR, 1629.85f, -4373.64f, 31.5573f, 3.69762f };
}

#endif
