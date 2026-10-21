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
#include <iomanip>
#include <map>
#include <set>
#include <sstream>
#include <utility>

namespace
{
    // Per-spell aggregate, built from RunResult's parallel HitSpellIds/HitDamages/HitCrits
    // vectors (castCount from CastEvents) - see SimReport.h's schema doc comment for hitCount vs. castCount.
    struct SpellAggregate
    {
        uint32 SpellId = 0;
        bool IsPet = false;
        uint32 HitCount = 0;
        uint32 CritCount = 0;
        uint64 TotalDamage = 0;
        // Casts of this spell id in the cast log, triggered included; 0 for a pet row (pet casts aren't logged)
        uint32 CastCount = 0;
        // Distinct dummy indexes this row hit
        std::set<uint8> TargetsHit;
    };

    std::vector<SpellAggregate> AggregateBySpell(SimDaemon::RunResult const& result)
    {
        // Keyed by (spell id, from a pet) so a pet's hits never merge into the bot's row for the same spell
        std::map<std::pair<uint32, bool>, SpellAggregate> byId;
        for (size_t i = 0; i < result.HitSpellIds.size(); ++i)
        {
            bool const isPet = i < result.HitIsPet.size() && result.HitIsPet[i];
            SpellAggregate& agg = byId[{result.HitSpellIds[i], isPet}];
            agg.SpellId = result.HitSpellIds[i];
            agg.IsPet = isPet;
            ++agg.HitCount;
            agg.TotalDamage += result.HitDamages[i];
            if (i < result.HitCrits.size() && result.HitCrits[i])
                ++agg.CritCount;
            if (i < result.HitTargetIndex.size())
                agg.TargetsHit.insert(result.HitTargetIndex[i]);
        }

        for (auto& entry : byId)
        {
            SpellAggregate& agg = entry.second;
            if (agg.IsPet)
                continue;

            agg.CastCount = uint32(std::count_if(result.CastEvents.begin(), result.CastEvents.end(),
                [&agg](SimDaemon::RunResult::CastEvent const& c) { return c.SpellId == agg.SpellId; }));
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
    // string value written below comes from a fixed, controlled set ("actor"/"target", "boss"/"elite") - no
    // escaping logic, because there is nothing here that could ever need escaping. If a future
    // field introduces free-form text (e.g. a spell name, once lookups move server-side), add
    // proper JSON string escaping before writing it, don't assume this stays safe.
    double const durationSeconds = double(result.ElapsedMs) / 1000.0;
    double const dps = durationSeconds > 0.0 ? double(result.TotalDamage) / durationSeconds : 0.0;
    double const critRatePct = result.CastCount > 0
        ? 100.0 * double(result.CritCount) / double(result.CastCount)
        : 0.0;
    uint32 const targetCount = std::max(config.TargetCount, 1u);

    file << "{\n";
    file << "  \"config\": {\n";
    file << "    \"actorLevel\": " << config.ActorLevel << ",\n";
    file << "    \"targetLevel\": " << config.TargetLevel << ",\n";
    file << "    \"spellPower\": " << config.SpellPower << ",\n";
    file << "    \"durationMs\": " << config.DurationMs << ",\n";
    file << "    \"targetCount\": " << config.TargetCount << ",\n";
    file << "    \"targetSpreadYards\": " << config.TargetSpreadYards << ",\n";
    file << "    \"targetRank\": \"" << SimTarget::RankName(config.TargetRank) << "\"\n";
    file << "  },\n";

    file << "  \"summary\": {\n";
    file << "    \"elapsedMs\": " << result.ElapsedMs << ",\n";
    file << "    \"totalDamage\": " << result.TotalDamage << ",\n";
    file << "    \"dps\": " << dps << ",\n";
    file << "    \"castCount\": " << result.CastCount << ",\n";
    file << "    \"critCount\": " << result.CritCount << ",\n";
    file << "    \"critRatePct\": " << critRatePct << ",\n";
    // null when the actor lived, else the sim ms it died at (elapsedMs is then the full configured duration)
    file << "    \"actorDiedAtMs\": ";
    if (result.ActorDied)
        file << result.ActorDiedAtMs;
    else
        file << "null";
    file << ",\n";
    // dps stays total damage across every dummy / duration
    file << "    \"dpsPerTarget\": " << dps / double(targetCount) << ",\n";
    file << "    \"targetSwitches\": " << result.TargetSwitches << "\n";
    file << "  },\n";

    std::vector<SpellAggregate> const spells = AggregateBySpell(result);
    file << "  \"spells\": [\n";
    for (size_t i = 0; i < spells.size(); ++i)
    {
        SpellAggregate const& s = spells[i];
        double const pctOfTotal = result.TotalDamage > 0
            ? 100.0 * double(s.TotalDamage) / double(result.TotalDamage)
            : 0.0;
        file << "    {\"spellId\": " << s.SpellId << ", \"isPet\": " << (s.IsPet ? "true" : "false")
             << ", \"hitCount\": " << s.HitCount
             << ", \"critCount\": " << s.CritCount << ", \"totalDamage\": " << s.TotalDamage
             << ", \"pctOfTotal\": " << pctOfTotal << ", \"castCount\": " << s.CastCount
             << ", \"targetsHit\": " << s.TargetsHit.size() << "}" << (i + 1 < spells.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"hits\": [\n";
    for (size_t i = 0; i < result.HitDamages.size(); ++i)
    {
        uint32 const timestamp = i < result.HitTimestamps.size() ? result.HitTimestamps[i] : 0;
        bool const crit = i < result.HitCrits.size() && result.HitCrits[i];
        bool const isPet = i < result.HitIsPet.size() && result.HitIsPet[i];
        uint32 const target = i < result.HitTargetIndex.size() ? result.HitTargetIndex[i] : 0;
        file << "    {\"timestampMs\": " << timestamp << ", \"spellId\": " << result.HitSpellIds[i]
             << ", \"damage\": " << result.HitDamages[i] << ", \"crit\": " << (crit ? "true" : "false")
             << ", \"isPet\": " << (isPet ? "true" : "false") << ", \"target\": " << target
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
             << ", \"targetIndex\": " << int32(e.TargetIndex)
             << "}" << (i + 1 < result.AuraEvents.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"manaSamples\": [\n";
    for (size_t i = 0; i < result.ManaSamples.size(); ++i)
    {
        SimDaemon::RunResult::ManaSample const& m = result.ManaSamples[i];
        file << "    {\"timestampMs\": " << m.TimestampMs << ", \"manaPct\": " << m.ManaPct
             << "}" << (i + 1 < result.ManaSamples.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"casts\": [\n";
    for (size_t i = 0; i < result.CastEvents.size(); ++i)
    {
        SimDaemon::RunResult::CastEvent const& c = result.CastEvents[i];
        file << "    {\"timestampMs\": " << c.TimestampMs << ", \"spellId\": " << c.SpellId
             << ", \"triggered\": " << (c.Triggered ? "true" : "false") << ", \"target\": " << int32(c.TargetIndex)
             << "}" << (i + 1 < result.CastEvents.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    // Damage per dummy, in index order
    std::vector<uint64> damageByTarget(targetCount, 0);
    for (size_t i = 0; i < result.HitDamages.size() && i < result.HitTargetIndex.size(); ++i)
        if (result.HitTargetIndex[i] < damageByTarget.size())
            damageByTarget[result.HitTargetIndex[i]] += result.HitDamages[i];
    file << "  \"targets\": [\n";
    for (size_t i = 0; i < damageByTarget.size(); ++i)
    {
        double const pctOfTotal = result.TotalDamage > 0
            ? 100.0 * double(damageByTarget[i]) / double(result.TotalDamage)
            : 0.0;
        file << "    {\"index\": " << i << ", \"totalDamage\": " << damageByTarget[i] << ", \"pctOfTotal\": "
             << pctOfTotal << "}" << (i + 1 < damageByTarget.size() ? ",\n" : "\n");
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

namespace
{
    char const* JsonBool(bool value)
    {
        return value ? "true" : "false";
    }

    // Per (spell id, from a pet) totals of the healer's heals, shields and casts in one heal iteration
    struct HealSpellAggregate
    {
        uint32 SpellId = 0;
        bool IsPet = false;
        uint32 Casts = 0;
        uint32 Hits = 0;
        uint32 Ticks = 0;
        uint32 Crits = 0;
        uint32 Events = 0;
        uint64 Raw = 0;
        uint64 Effective = 0;
        uint64 Overheal = 0;
        uint64 HealAbsorbed = 0;
        uint64 Absorbed = 0;
        uint64 ManaSpent = 0;
        std::set<uint8> TargetsHit;

        [[nodiscard]] uint64 Total() const { return Effective + Absorbed; }
    };

    // Per group member totals: what it received and what the boss's hits did to it
    struct HealTargetAggregate
    {
        uint64 Effective = 0;
        uint64 Absorbed = 0;
        uint64 Overheal = 0;
        uint64 DamageRequested = 0;
        uint64 DamageMitigated = 0;
        uint64 DamageAbsorbed = 0;
        uint64 DamageTaken = 0;
        uint32 Deaths = 0;
        int64 FirstDeathMs = -1;
        uint32 Samples = 0;
        uint32 SamplesBelow35 = 0;
        double PctSum = 0.0;
        double MinPct = 100.0;
    };
}

bool SimReport::WriteHealJson(std::string const& path, SimDaemon::RunConfig const& config,
    SimDaemon::RunResult const& result)
{
    std::ofstream file(path, std::ios::out | std::ios::trunc);
    if (!file.is_open())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimReport::WriteHealJson() - could not open '{}' for writing.", path);
        return false;
    }

    // Same hand-written style as WriteJson(). Every string below comes from a controlled set (role and mode names, the
    // group name, the canonical target text made of those and digits), so there is no escaping.
    size_t const targetCount = result.HealTargetInfo.size();

    std::map<std::pair<uint32, bool>, HealSpellAggregate> bySpell;
    auto const spellRow = [&bySpell](uint32 spellId, bool isPet) -> HealSpellAggregate&
    {
        HealSpellAggregate& agg = bySpell[{spellId, isPet}];
        agg.SpellId = spellId;
        agg.IsPet = isPet;
        return agg;
    };
    std::vector<HealTargetAggregate> byTarget(targetCount);

    uint64 effective = 0, raw = 0, overheal = 0, healAbsorbed = 0, absorbs = 0;
    uint32 critCount = 0, landed = 0;
    for (SimHeal::HealEvent const& e : result.HealEvents)
    {
        effective += e.Effective;
        raw += e.Raw;
        overheal += e.Overheal;
        healAbsorbed += e.HealAbsorbed;
        ++landed;
        if (e.Crit)
            ++critCount;

        HealSpellAggregate& agg = spellRow(e.SpellId, e.IsPet);
        ++agg.Events;
        if (e.Periodic)
            ++agg.Ticks;
        else
            ++agg.Hits;
        if (e.Crit)
            ++agg.Crits;
        agg.Raw += e.Raw;
        agg.Effective += e.Effective;
        agg.Overheal += e.Overheal;
        agg.HealAbsorbed += e.HealAbsorbed;
        agg.TargetsHit.insert(e.TargetIndex);

        if (e.TargetIndex < targetCount)
        {
            byTarget[e.TargetIndex].Effective += e.Effective;
            byTarget[e.TargetIndex].Overheal += e.Overheal;
        }
    }
    for (SimHeal::AbsorbEvent const& e : result.AbsorbEvents)
    {
        absorbs += e.Amount;
        HealSpellAggregate& agg = spellRow(e.SpellId, e.IsPet);
        ++agg.Events;
        agg.Absorbed += e.Amount;
        agg.TargetsHit.insert(e.TargetIndex);
        if (e.TargetIndex < targetCount)
            byTarget[e.TargetIndex].Absorbed += e.Amount;
    }

    // Casts: deliberate ones for the headline count, every cast (triggered included) for the per-spell cast count, the
    // power paid at cast time for mana. A spell that only cost mana (a buff) still gets a row.
    uint32 deliberateCasts = 0, triggeredCasts = 0;
    uint64 manaSpent = 0;
    std::map<uint32, uint32> castsById;
    std::map<uint32, uint64> manaById;
    for (SimDaemon::RunResult::CastEvent const& c : result.CastEvents)
    {
        if (c.Triggered)
            ++triggeredCasts;
        else
            ++deliberateCasts;

        uint64 const cost = c.PowerCost > 0 ? uint64(c.PowerCost) : 0;
        manaSpent += cost;
        ++castsById[c.SpellId];
        manaById[c.SpellId] += cost;
    }
    for (auto const& [spellId, mana] : manaById)
        if (mana > 0)
            spellRow(spellId, false);
    for (auto& [key, agg] : bySpell)
    {
        if (agg.IsPet)
            continue;

        agg.Casts = castsById[agg.SpellId];
        agg.ManaSpent = manaById[agg.SpellId];
    }

    for (SimHeal::DamageEvent const& e : result.DamageTakenEvents)
    {
        if (e.TargetIndex >= targetCount)
            continue;

        HealTargetAggregate& t = byTarget[e.TargetIndex];
        t.DamageRequested += e.Requested;
        t.DamageMitigated += e.Requested > e.Raw ? e.Requested - e.Raw : 0;
        t.DamageAbsorbed += e.Absorbed;
        t.DamageTaken += e.Final;
    }
    for (SimHeal::LifeEvent const& e : result.Deaths)
    {
        if (e.TargetIndex >= targetCount)
            continue;

        HealTargetAggregate& t = byTarget[e.TargetIndex];
        ++t.Deaths;
        if (t.FirstDeathMs < 0 || int64(e.TimestampMs) < t.FirstDeathMs)
            t.FirstDeathMs = e.TimestampMs;
    }
    for (SimHeal::HealthSample const& e : result.HealthSamples)
    {
        if (e.TargetIndex >= targetCount)
            continue;

        HealTargetAggregate& t = byTarget[e.TargetIndex];
        double const pct = e.MaxHealth > 0 ? 100.0 * double(e.Health) / double(e.MaxHealth) : 0.0;
        ++t.Samples;
        t.PctSum += pct;
        t.MinPct = std::min(t.MinPct, pct);
        if (pct < 35.0)
            ++t.SamplesBelow35;
    }

    // Out of mana: the first mana sample under 5% after the healer had mana (a class without a mana pool never has
    // any, so it never "runs out")
    bool oomFound = false;
    uint32 oomAtMs = 0;
    bool seenMana = false;
    for (SimDaemon::RunResult::ManaSample const& m : result.ManaSamples)
    {
        if (m.ManaPct >= 5.0f)
            seenMana = true;
        else if (seenMana)
        {
            oomFound = true;
            oomAtMs = std::max(m.TimestampMs, 1u);
            break;
        }
    }

    double const seconds = double(result.ElapsedMs) / 1000.0;
    double const hps = seconds > 0.0 ? double(effective + absorbs) / seconds : 0.0;
    double const rawHps = seconds > 0.0 ? double(raw + absorbs) / seconds : 0.0;
    double hpsBeforeOom = hps;
    if (oomFound)
    {
        uint64 before = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
            if (e.TimestampMs <= oomAtMs)
                before += e.Effective;
        for (SimHeal::AbsorbEvent const& e : result.AbsorbEvents)
            if (e.TimestampMs <= oomAtMs)
                before += e.Amount;
        hpsBeforeOom = double(before) / (double(oomAtMs) / 1000.0);
    }
    double const overhealPct = raw > 0 ? 100.0 * double(overheal) / double(raw) : 0.0;
    double const critRatePct = landed > 0 ? 100.0 * double(critCount) / double(landed) : 0.0;
    double const damageDps = seconds > 0.0 ? double(result.TotalDamage) / seconds : 0.0;

    file << std::fixed << std::setprecision(3);
    file << "{\n";
    file << "  \"kind\": \"heal\",\n";
    file << "  \"config\": {\n";
    file << "    \"actorLevel\": " << config.ActorLevel << ",\n";
    file << "    \"actorRace\": " << uint32(config.ActorRace) << ",\n";
    file << "    \"actorClass\": " << uint32(config.ActorClass) << ",\n";
    file << "    \"durationMs\": " << config.DurationMs << ",\n";
    file << "    \"stepMs\": " << config.StepMs << ",\n";
    file << "    \"group\": \"" << SimHeal::GroupName(config.HealGroupSize) << "\",\n";
    file << "    \"healTargets\": \"" << SimHeal::TargetsText(config.HealTargets) << "\",\n";
    file << "    \"infiniteMana\": " << JsonBool(config.InfiniteMana) << ",\n";
    file << "    \"pinMaxHealth\": " << config.PinMaxHealth << ",\n";
    file << "    \"allyMaxHealthTank\": " << config.AllyMaxHealthTank << ",\n";
    file << "    \"allyMaxHealthDps\": " << config.AllyMaxHealthDps << ",\n";
    file << "    \"drainPulseMs\": " << config.DrainPulseMs << ",\n";
    file << "    \"allySpreadYards\": " << config.AllySpreadYards << "\n";
    file << "  },\n";

    file << "  \"summary\": {\n";
    file << "    \"elapsedMs\": " << result.ElapsedMs << ",\n";
    file << "    \"effectiveHealing\": " << effective << ",\n";
    file << "    \"rawHealing\": " << raw << ",\n";
    file << "    \"overhealing\": " << overheal << ",\n";
    file << "    \"overhealPct\": " << overhealPct << ",\n";
    file << "    \"healAbsorbed\": " << healAbsorbed << ",\n";
    file << "    \"absorbHealing\": " << absorbs << ",\n";
    file << "    \"hps\": " << hps << ",\n";
    file << "    \"rawHps\": " << rawHps << ",\n";
    file << "    \"hpsBeforeOom\": " << hpsBeforeOom << ",\n";
    file << "    \"castCount\": " << deliberateCasts << ",\n";
    file << "    \"triggeredCasts\": " << triggeredCasts << ",\n";
    file << "    \"critRatePct\": " << critRatePct << ",\n";
    file << "    \"manaSpent\": " << manaSpent << ",\n";
    file << "    \"healingPerMana\": " << (manaSpent > 0 ? double(effective + absorbs) / double(manaSpent) : 0.0)
         << ",\n";
    file << "    \"oomAtMs\": ";
    if (oomFound)
        file << oomAtMs;
    else
        file << "null";
    file << ",\n";
    file << "    \"deaths\": " << result.Deaths.size() << ",\n";
    file << "    \"firstDeathAtMs\": ";
    if (result.Deaths.empty())
        file << "null";
    else
    {
        uint32 first = result.Deaths.front().TimestampMs;
        for (SimHeal::LifeEvent const& e : result.Deaths)
            first = std::min(first, e.TimestampMs);
        file << first;
    }
    file << ",\n";
    file << "    \"resurrections\": " << result.Resurrections.size() << ",\n";
    file << "    \"actorDiedAtMs\": ";
    if (result.ActorDied)
        file << result.ActorDiedAtMs;
    else
        file << "null";
    file << ",\n";
    file << "    \"damageDone\": " << result.TotalDamage << ",\n";
    file << "    \"dps\": " << damageDps << ",\n";
    file << "    \"wallClockMs\": " << result.WallClockMs << ",\n";
    file << "    \"pinHits\": " << result.PinHits << ",\n";
    file << "    \"pinRaises\": " << result.PinRaises << ",\n";
    file << "    \"drainHits\": " << result.DrainHits << ",\n";
    file << "    \"driverCastFailures\": " << result.DriverCastFailures << "\n";
    file << "  },\n";

    std::vector<HealSpellAggregate> spells;
    spells.reserve(bySpell.size());
    for (auto const& [key, agg] : bySpell)
        spells.push_back(agg);
    std::stable_sort(spells.begin(), spells.end(), [](HealSpellAggregate const& a, HealSpellAggregate const& b)
    {
        if (a.Total() != b.Total())
            return a.Total() > b.Total();
        return a.ManaSpent > b.ManaSpent;
    });
    uint64 const grandTotal = effective + absorbs;
    file << "  \"spells\": [\n";
    for (size_t i = 0; i < spells.size(); ++i)
    {
        HealSpellAggregate const& s = spells[i];
        file << "    {\"spellId\": " << s.SpellId << ", \"isPet\": " << JsonBool(s.IsPet)
             << ", \"casts\": " << s.Casts << ", \"hits\": " << s.Hits << ", \"ticks\": " << s.Ticks
             << ", \"crits\": " << s.Crits << ", \"effective\": " << s.Effective << ", \"overheal\": " << s.Overheal
             << ", \"overhealPct\": " << (s.Raw > 0 ? 100.0 * double(s.Overheal) / double(s.Raw) : 0.0)
             << ", \"healAbsorbed\": " << s.HealAbsorbed << ", \"absorbed\": " << s.Absorbed
             << ", \"events\": " << s.Events << ", \"total\": " << s.Total() << ", \"pctOfTotal\": "
             << (grandTotal > 0 ? 100.0 * double(s.Total()) / double(grandTotal) : 0.0)
             << ", \"avgHit\": " << (s.Events > 0 ? double(s.Total()) / double(s.Events) : 0.0)
             << ", \"manaSpent\": " << s.ManaSpent << ", \"hpm\": ";
        if (s.ManaSpent > 0)
            file << double(s.Total()) / double(s.ManaSpent);
        else
            file << "null";
        file << ", \"targetsHit\": " << s.TargetsHit.size() << "}" << (i + 1 < spells.size() ? ",\n" : "\n");
    }
    file << "  ],\n";

    file << "  \"targets\": [\n";
    for (size_t i = 0; i < targetCount; ++i)
    {
        SimHeal::TargetInfo const& info = result.HealTargetInfo[i];
        HealTargetAggregate const& t = byTarget[i];
        uint32 const pinHits = i < result.TargetPinHits.size() ? result.TargetPinHits[i] : 0;
        uint32 const pinRaises = i < result.TargetPinRaises.size() ? result.TargetPinRaises[i] : 0;
        file << "    {\"index\": " << i << ", \"role\": \"" << SimHeal::RoleName(info.Spec.TargetRole)
             << "\", \"mode\": \"" << (info.Spec.Kind == SimHeal::ModeKind::Pin ? "pin" : "drain")
             << "\", \"value\": " << info.Spec.Value << ", \"percent\": " << JsonBool(info.Spec.Percent)
             << ", \"subgroup\": " << uint32(info.Subgroup) << ", \"maxHealth\": " << info.MaxHealth
             << ", \"healingReceived\": " << t.Effective + t.Absorbed << ", \"effectiveReceived\": " << t.Effective
             << ", \"absorbReceived\": " << t.Absorbed << ", \"overheal\": " << t.Overheal
             << ", \"damageRequested\": " << t.DamageRequested << ", \"damageMitigated\": " << t.DamageMitigated
             << ", \"damageAbsorbed\": " << t.DamageAbsorbed << ", \"damageTaken\": " << t.DamageTaken
             << ", \"damagePrevented\": " << t.DamageAbsorbed + t.DamageMitigated << ", \"deaths\": " << t.Deaths
             << ", \"diedAtMs\": ";
        if (t.FirstDeathMs >= 0)
            file << t.FirstDeathMs;
        else
            file << "null";
        file << ", \"minHealthPct\": " << (t.Samples > 0 ? t.MinPct : 0.0)
             << ", \"avgHealthPct\": " << (t.Samples > 0 ? t.PctSum / double(t.Samples) : 0.0)
             << ", \"msBelow35Pct\": " << t.SamplesBelow35 * SimHeal::HEALTH_SAMPLE_INTERVAL_MS
             << ", \"pinHits\": " << pinHits << ", \"pinRaises\": " << pinRaises << "}"
             << (i + 1 < targetCount ? ",\n" : "\n");
    }
    file << "  ],\n";

    // One event per line, in recording order
    auto const writeArray = [&file](char const* name, size_t count, auto const& writeEvent, bool last = false)
    {
        file << "  \"" << name << "\": [\n";
        for (size_t i = 0; i < count; ++i)
        {
            file << "    ";
            writeEvent(i);
            file << (i + 1 < count ? ",\n" : "\n");
        }
        file << "  ]" << (last ? "\n" : ",\n");
    };

    writeArray("heals", result.HealEvents.size(), [&](size_t i)
    {
        SimHeal::HealEvent const& e = result.HealEvents[i];
        file << "{\"timestampMs\": " << e.TimestampMs << ", \"spellId\": " << e.SpellId
             << ", \"isPet\": " << JsonBool(e.IsPet) << ", \"target\": " << uint32(e.TargetIndex)
             << ", \"raw\": " << e.Raw << ", \"effective\": " << e.Effective << ", \"overheal\": " << e.Overheal
             << ", \"healAbsorbed\": " << e.HealAbsorbed << ", \"crit\": " << JsonBool(e.Crit)
             << ", \"periodic\": " << JsonBool(e.Periodic) << "}";
    });
    writeArray("absorbs", result.AbsorbEvents.size(), [&](size_t i)
    {
        SimHeal::AbsorbEvent const& e = result.AbsorbEvents[i];
        file << "{\"timestampMs\": " << e.TimestampMs << ", \"spellId\": " << e.SpellId
             << ", \"isPet\": " << JsonBool(e.IsPet) << ", \"target\": " << uint32(e.TargetIndex)
             << ", \"amount\": " << e.Amount << "}";
    });
    writeArray("damageTaken", result.DamageTakenEvents.size(), [&](size_t i)
    {
        SimHeal::DamageEvent const& e = result.DamageTakenEvents[i];
        file << "{\"timestampMs\": " << e.TimestampMs << ", \"target\": " << uint32(e.TargetIndex)
             << ", \"pin\": " << JsonBool(e.Pin) << ", \"requested\": " << e.Requested << ", \"raw\": " << e.Raw
             << ", \"absorbed\": " << e.Absorbed << ", \"final\": " << e.Final << "}";
    });
    writeArray("healthSamples", result.HealthSamples.size(), [&](size_t i)
    {
        SimHeal::HealthSample const& e = result.HealthSamples[i];
        file << "{\"timestampMs\": " << e.TimestampMs << ", \"target\": " << uint32(e.TargetIndex)
             << ", \"health\": " << e.Health << ", \"maxHealth\": " << e.MaxHealth << "}";
    });
    writeArray("deaths", result.Deaths.size(), [&](size_t i)
    {
        file << "{\"timestampMs\": " << result.Deaths[i].TimestampMs << ", \"target\": "
             << uint32(result.Deaths[i].TargetIndex) << "}";
    });
    writeArray("resurrections", result.Resurrections.size(), [&](size_t i)
    {
        file << "{\"timestampMs\": " << result.Resurrections[i].TimestampMs << ", \"target\": "
             << uint32(result.Resurrections[i].TargetIndex) << "}";
    });
    writeArray("groupAuraEvents", result.GroupAuraEvents.size(), [&](size_t i)
    {
        SimHeal::GroupAuraEvent const& e = result.GroupAuraEvents[i];
        file << "{\"timestampMs\": " << e.TimestampMs << ", \"target\": " << uint32(e.TargetIndex)
             << ", \"spellId\": " << e.SpellId << ", \"stackAmount\": " << uint32(e.StackAmount)
             << ", \"positive\": " << JsonBool(e.Positive) << ", \"applied\": " << JsonBool(e.Applied)
             << ", \"byHealer\": " << JsonBool(e.ByHealer) << "}";
    });
    writeArray("casts", result.CastEvents.size(), [&](size_t i)
    {
        SimDaemon::RunResult::CastEvent const& c = result.CastEvents[i];
        file << "{\"timestampMs\": " << c.TimestampMs << ", \"spellId\": " << c.SpellId
             << ", \"triggered\": " << JsonBool(c.Triggered) << ", \"target\": " << int32(c.TargetIndex)
             << ", \"powerCost\": " << c.PowerCost << "}";
    });
    writeArray("manaSamples", result.ManaSamples.size(), [&](size_t i)
    {
        file << "{\"timestampMs\": " << result.ManaSamples[i].TimestampMs << ", \"manaPct\": "
             << result.ManaSamples[i].ManaPct << "}";
    }, true);
    file << "}\n";

    if (!file.good())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimReport::WriteHealJson() - a write to '{}' failed partway through.",
            path);
        return false;
    }

    LOG_INFO("server.dpssim", "mod-dpssim: SimReport::WriteHealJson() - wrote '{}'.", path);
    return true;
}
