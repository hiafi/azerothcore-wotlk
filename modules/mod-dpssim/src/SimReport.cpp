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

#include "SimReport.h"
#include "Log.h"
#include <algorithm>
#include <fstream>
#include <map>
#include <sstream>

namespace
{
    // Per-spell aggregate, built from RunResult's parallel HitSpellIds/HitDamages/HitCrits
    // vectors - see SimReport.h's schema doc comment for why hitCount doubles as cast count today.
    struct SpellAggregate
    {
        uint32 SpellId = 0;
        uint32 HitCount = 0;
        uint32 CritCount = 0;
        uint64 TotalDamage = 0;
    };

    std::vector<SpellAggregate> AggregateBySpell(SimDaemon::RunResult const& result)
    {
        std::map<uint32, SpellAggregate> byId;
        for (size_t i = 0; i < result.HitSpellIds.size(); ++i)
        {
            SpellAggregate& agg = byId[result.HitSpellIds[i]];
            agg.SpellId = result.HitSpellIds[i];
            ++agg.HitCount;
            agg.TotalDamage += result.HitDamages[i];
            if (i < result.HitCrits.size() && result.HitCrits[i])
                ++agg.CritCount;
        }

        std::vector<SpellAggregate> aggregates;
        aggregates.reserve(byId.size());
        for (auto const& [id, agg] : byId)
            aggregates.push_back(agg);

        std::sort(aggregates.begin(), aggregates.end(),
            [](SpellAggregate const& a, SpellAggregate const& b) { return a.TotalDamage > b.TotalDamage; });
        return aggregates;
    }
}

bool SimReport::WriteJson(std::string const& path, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result)
{
    std::ofstream file(path, std::ios::out | std::ios::trunc);
    if (!file.is_open())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimReport::WriteJson() - could not open '{}' for writing.", path);
        return false;
    }

    // Hand-written, not built with a JSON library - this repo has none vendored (checked before
    // adding one; not worth the dependency for a flat, fully-known schema like this one). Every
    // string value written below comes from a fixed, controlled set ("actor"/"target" only) - no
    // escaping logic, because there is nothing here that could ever need escaping. If a future
    // field introduces free-form text (e.g. a spell name, once lookups move server-side), add
    // proper JSON string escaping before writing it, don't assume this stays safe.
    double const durationSeconds = double(result.ElapsedMs) / 1000.0;
    double const dps = durationSeconds > 0.0 ? double(result.TotalDamage) / durationSeconds : 0.0;
    double const critRatePct = result.CastCount > 0
        ? 100.0 * double(result.CritCount) / double(result.CastCount)
        : 0.0;

    file << "{\n";
    file << "  \"config\": {\n";
    file << "    \"actorLevel\": " << config.ActorLevel << ",\n";
    file << "    \"targetLevel\": " << config.TargetLevel << ",\n";
    file << "    \"spellPower\": " << config.SpellPower << ",\n";
    file << "    \"durationMs\": " << config.DurationMs << ",\n";
    file << "    \"randomSeed\": " << config.RandomSeed << "\n";
    file << "  },\n";

    file << "  \"summary\": {\n";
    file << "    \"elapsedMs\": " << result.ElapsedMs << ",\n";
    file << "    \"totalDamage\": " << result.TotalDamage << ",\n";
    file << "    \"dps\": " << dps << ",\n";
    file << "    \"castCount\": " << result.CastCount << ",\n";
    file << "    \"critCount\": " << result.CritCount << ",\n";
    file << "    \"critRatePct\": " << critRatePct << "\n";
    file << "  },\n";

    std::vector<SpellAggregate> const spells = AggregateBySpell(result);
    file << "  \"spells\": [\n";
    for (size_t i = 0; i < spells.size(); ++i)
    {
        SpellAggregate const& s = spells[i];
        double const pctOfTotal = result.TotalDamage > 0
            ? 100.0 * double(s.TotalDamage) / double(result.TotalDamage)
            : 0.0;
        file << "    {\"spellId\": " << s.SpellId << ", \"hitCount\": " << s.HitCount
             << ", \"critCount\": " << s.CritCount << ", \"totalDamage\": " << s.TotalDamage
             << ", \"pctOfTotal\": " << pctOfTotal << "}" << (i + 1 < spells.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"hits\": [\n";
    for (size_t i = 0; i < result.HitDamages.size(); ++i)
    {
        uint32 const timestamp = i < result.HitTimestamps.size() ? result.HitTimestamps[i] : 0;
        bool const crit = i < result.HitCrits.size() && result.HitCrits[i];
        file << "    {\"timestampMs\": " << timestamp << ", \"spellId\": " << result.HitSpellIds[i]
             << ", \"damage\": " << result.HitDamages[i] << ", \"crit\": " << (crit ? "true" : "false")
             << "}" << (i + 1 < result.HitDamages.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"auraEvents\": [\n";
    for (size_t i = 0; i < result.AuraEvents.size(); ++i)
    {
        SimDaemon::RunResult::AuraEvent const& e = result.AuraEvents[i];
        file << "    {\"timestampMs\": " << e.TimestampMs << ", \"unit\": \"" << (e.IsActor ? "actor" : "target")
             << "\", \"spellId\": " << e.SpellId << ", \"stackAmount\": " << uint32(e.StackAmount)
             << ", \"positive\": " << (e.Positive ? "true" : "false") << ", \"applied\": " << (e.Applied ? "true" : "false")
             << "}" << (i + 1 < result.AuraEvents.size() ? ",\n" : "\n");
    }
    file << "  ]\n";
    file << "}\n";

    if (!file.good())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimReport::WriteJson() - a write to '{}' failed partway through.", path);
        return false;
    }

    LOG_INFO("server.dpssim", "mod-dpssim: SimReport::WriteJson() - wrote '{}'.", path);
    return true;
}
