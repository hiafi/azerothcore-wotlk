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
    // POWER_RAGE and POWER_RUNIC_POWER are stored x10 by the core; every other power is stored as it reads
    double TankPowerDisplay(uint8 powerType, uint32 value)
    {
        constexpr uint8 POWER_TYPE_RAGE = 1;
        constexpr uint8 POWER_TYPE_RUNIC_POWER = 6;
        return (powerType == POWER_TYPE_RAGE || powerType == POWER_TYPE_RUNIC_POWER) ? double(value) / 10.0 :
            double(value);
    }

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

namespace
{
    // The tank section of a tank report; defined with the other tank-mode helpers below
    void WriteTankSection(std::ofstream& file, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result);
}

// The DPS report; a tank report is the same file with "kind": "tank" first and a "tank" section last (plan T5: tank
// runs are DPS runs, so every tool that reads a DPS report reads a tank one). With `tank` false this writes exactly
// what SimReport::WriteJson() always has.
static bool WriteDpsReport(std::string const& path, SimDaemon::RunConfig const& config,
    SimDaemon::RunResult const& result, bool tank)
{
    char const* const writer = tank ? "SimReport::WriteTankJson()" : "SimReport::WriteJson()";
    std::ofstream file(path, std::ios::out | std::ios::trunc);
    if (!file.is_open())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: {} - could not open '{}' for writing.", writer, path);
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
    if (tank)
        file << "  \"kind\": \"tank\",\n";
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

    // The actor's class power every 500 ms and, for a Death Knight, its ready runes by type (RunResult::PowerSamples);
    // power and maxPower are as the player reads them (rage and runic power divided by ten)
    file << "  \"powerSamples\": [\n";
    for (size_t i = 0; i < result.PowerSamples.size(); ++i)
    {
        SimDaemon::RunResult::PowerSample const& sample = result.PowerSamples[i];
        file << "    {\"timestampMs\": " << sample.TimestampMs << ", \"powerType\": " << uint32(sample.PowerType)
             << ", \"power\": " << TankPowerDisplay(sample.PowerType, sample.Power) << ", \"maxPower\": "
             << TankPowerDisplay(sample.PowerType, sample.MaxPower);
        if (sample.HasRunes)
            file << ", \"runes\": {\"blood\": " << uint32(sample.RunesBlood) << ", \"frost\": "
                 << uint32(sample.RunesFrost) << ", \"unholy\": " << uint32(sample.RunesUnholy) << ", \"death\": "
                 << uint32(sample.RunesDeath) << "}";
        file << "}" << (i + 1 < result.PowerSamples.size() ? ",\n" : "\n");
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
    file << "  ]" << (tank ? ",\n" : "\n");
    if (tank)
        WriteTankSection(file, config, result);
    file << "}\n";

    if (!file.good())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: {} - a write to '{}' failed partway through.", writer, path);
        return false;
    }

    LOG_INFO("server.dpssim", "mod-dpssim: {} - wrote '{}'.", writer, path);
    return true;
}

bool SimReport::WriteJson(std::string const& path, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result)
{
    return WriteDpsReport(path, config, result, false);
}

bool SimReport::WriteTankJson(std::string const& path, SimDaemon::RunConfig const& config,
    SimDaemon::RunResult const& result)
{
    return WriteDpsReport(path, config, result, true);
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

// ---- Tank mode (kind "tank"; plan .agents/plans/tank-sim/tank-sim.PLAN.md, sections 4 and 5) ----

namespace
{
    constexpr size_t TANK_OUTCOMES = size_t(SimTank::Outcome::Other) + 1;
    // JSON keys of SimTank::Outcome, in enum order
    constexpr char const* TANK_OUTCOME_KEYS[TANK_OUTCOMES] = {"miss", "dodge", "parry", "block", "fullBlock", "crit",
        "crush", "hit", "glancing", "other"};

    double SafeDivide(double numerator, double denominator)
    {
        return denominator > 0.0 ? numerator / denominator : 0.0;
    }

    struct TankOutcomeCounts
    {
        uint32 Count[TANK_OUTCOMES] = {};
        uint32 Total = 0;

        void Add(SimTank::Outcome outcome)
        {
            ++Count[size_t(outcome)];
            ++Total;
        }

        [[nodiscard]] uint32 Of(SimTank::Outcome outcome) const { return Count[size_t(outcome)]; }
        [[nodiscard]] uint32 Avoided() const
        {
            return Of(SimTank::Outcome::Miss) + Of(SimTank::Outcome::Dodge) + Of(SimTank::Outcome::Parry);
        }
    };

    // {"miss": n, ...}
    void WriteOutcomeCounts(std::ofstream& file, TankOutcomeCounts const& counts)
    {
        file << "{";
        for (size_t i = 0; i < TANK_OUTCOMES; ++i)
            file << (i ? ", " : "") << "\"" << TANK_OUTCOME_KEYS[i] << "\": " << counts.Count[i];
        file << "}";
    }

    // {"miss": percent of all swings, ...}
    void WriteOutcomePercents(std::ofstream& file, TankOutcomeCounts const& counts)
    {
        file << "{";
        for (size_t i = 0; i < TANK_OUTCOMES; ++i)
            file << (i ? ", " : "") << "\"" << TANK_OUTCOME_KEYS[i] << "\": "
                 << 100.0 * SafeDivide(double(counts.Count[i]), double(counts.Total));
        file << "}";
    }

    void WriteHitRange(std::ofstream& file, SimTank::HitRange const& range)
    {
        file << "{\"min\": " << range.Min << ", \"max\": " << range.Max << "}";
    }

    void WriteActorInfo(std::ofstream& file, SimTank::ActorInfo const& a)
    {
        file << "{\"level\": " << a.Level << ", \"health\": " << a.Health << ", \"armor\": " << a.Armor
             << ", \"defenseSkill\": " << a.DefenseSkill << ", \"maxSkillForLevel\": " << a.MaxSkillForLevel
             << ", \"dodgePct\": " << a.Dodge << ", \"parryPct\": " << a.Parry << ", \"blockPct\": " << a.Block
             << ", \"blockValue\": " << a.BlockValue << ", \"critImmune\": " << JsonBool(a.CritImmune) << "}";
    }

    // Per (spell id, from a pet) self-healing of the actor in one tank iteration
    struct TankHealRow
    {
        uint32 SpellId = 0;
        bool IsPet = false;
        uint32 Casts = 0;
        uint32 Hits = 0;
        uint32 Ticks = 0;
        uint32 Crits = 0;
        uint64 Raw = 0;
        uint64 Effective = 0;
        uint64 Overheal = 0;
        uint64 HealAbsorbed = 0;
    };

    // Per dummy totals
    struct TankDummyRow
    {
        TankOutcomeCounts Outcomes;
        uint64 PreArmor = 0;
        uint64 Taken = 0;
        uint32 OutsideArc = 0;
        float Threat = 0.0f;
    };

    void WriteTankSection(std::ofstream& file, SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result)
    {
        using SimTank::Outcome;
        bool const survive = result.TankScenario == SimTank::Scenario::Survive;
        size_t const dummyCount = result.TankDummies.size();

        // ---- Swings ----
        TankOutcomeCounts outcomes;
        std::vector<TankDummyRow> perDummy(dummyCount);
        uint64 avoidedDamage = 0, armorDamage = 0, blockedDamage = 0, absorbedDamage = 0, resistedDamage = 0;
        uint64 takenDamage = 0, preArmorTotal = 0;
        uint64 expMiss = 0, expDodge = 0, expParry = 0, expBlock = 0, expCrit = 0;
        uint32 landed = 0, outsideArc = 0, critBugCount = 0;
        std::vector<uint32> critBugAt;
        int64 rageTenths = 0;
        uint32 rageSwings = 0, avoidSwings = 0, avoidSwingsWithRage = 0;
        for (SimTank::SwingEvent const& swing : result.Swings)
        {
            outcomes.Add(swing.Result);
            preArmorTotal += swing.PreArmor;
            expMiss += swing.ExpectedMiss;
            expDodge += swing.ExpectedDodge;
            expParry += swing.ExpectedParry;
            expBlock += swing.ExpectedBlock;
            expCrit += swing.ExpectedCrit;
            if (!swing.InFrontArc)
                ++outsideArc;

            bool const rolledAvoid = swing.Result == Outcome::Miss || swing.Result == Outcome::Dodge ||
                swing.Result == Outcome::Parry;
            bool const didLand = !rolledAvoid && swing.Result != Outcome::Other;
            if (rolledAvoid)
                avoidedDamage += swing.PreArmor;
            if (didLand)
            {
                ++landed;
                armorDamage += swing.ArmorMitigated;
            }
            blockedDamage += swing.Blocked;
            absorbedDamage += swing.Absorbed;
            resistedDamage += swing.Resisted;
            takenDamage += swing.Final;

            // A crit on a swing whose rolled chance was 0 (a crit-immune tank): a bug
            if (swing.Result == Outcome::Crit && swing.ExpectedCrit == 0)
            {
                ++critBugCount;
                critBugAt.push_back(swing.TimestampMs);
            }

            if (swing.RageGained >= 0)
            {
                rageTenths += swing.RageGained;
                ++rageSwings;
                // Swings that took no damage through: rage on one of them is a proc (R7: Shield Specialization)
                if (rolledAvoid || swing.Result == Outcome::FullBlock)
                {
                    ++avoidSwings;
                    if (swing.RageGained > 0)
                        ++avoidSwingsWithRage;
                }
            }

            if (swing.DummyIndex < dummyCount)
            {
                TankDummyRow& row = perDummy[swing.DummyIndex];
                row.Outcomes.Add(swing.Result);
                row.PreArmor += swing.PreArmor;
                row.Taken += swing.Final;
                if (!swing.InFrontArc)
                    ++row.OutsideArc;
            }
        }
        uint32 const swingCount = uint32(result.Swings.size());
        uint64 const grossDamage = avoidedDamage + armorDamage + blockedDamage + absorbedDamage + resistedDamage +
            takenDamage;

        // ---- Self-healing, by spell (HealRecorder with the actor as the whole group) ----
        // The shields the actor casts on itself are NOT added here: what they absorbed is already out of every swing's
        // Final (damage taken is post-absorb), so subtracting them from damage taken again would count them twice
        // (review of TS1, question 4). The absorbs that were used are in absorbsBySpell, from the swings.
        std::map<std::pair<uint32, bool>, TankHealRow> healRows;
        uint64 healEffective = 0, healOverheal = 0, healRaw = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            healEffective += e.Effective;
            healOverheal += e.Overheal;
            healRaw += e.Raw;
            TankHealRow& row = healRows[{e.SpellId, e.IsPet}];
            row.SpellId = e.SpellId;
            row.IsPet = e.IsPet;
            if (e.Periodic)
                ++row.Ticks;
            else
                ++row.Hits;
            if (e.Crit)
                ++row.Crits;
            row.Raw += e.Raw;
            row.Effective += e.Effective;
            row.Overheal += e.Overheal;
            row.HealAbsorbed += e.HealAbsorbed;
        }
        std::map<uint32, uint32> castsById;
        for (SimDaemon::RunResult::CastEvent const& c : result.CastEvents)
            ++castsById[c.SpellId];
        std::vector<TankHealRow> heals;
        for (auto& [key, row] : healRows)
        {
            if (!row.IsPet)
                row.Casts = castsById[row.SpellId];
            heals.push_back(row);
        }
        std::stable_sort(heals.begin(), heals.end(), [](TankHealRow const& a, TankHealRow const& b)
        {
            return a.Effective > b.Effective;
        });

        // ---- Shields that took damage off the swings, by spell (SwingAbsorbs only; AbsorbEvents overlap them) ----
        struct AbsorbRow
        {
            uint64 Amount = 0;
            uint32 Events = 0;
        };
        std::map<uint32, AbsorbRow> absorbRows;
        uint64 absorbsAttributed = 0;
        for (SimTank::SwingAbsorb const& e : result.SwingAbsorbs)
        {
            AbsorbRow& row = absorbRows[e.SpellId];
            row.Amount += e.Amount;
            ++row.Events;
            absorbsAttributed += e.Amount;
        }
        std::vector<std::pair<uint32, AbsorbRow>> absorbs(absorbRows.begin(), absorbRows.end());
        std::stable_sort(absorbs.begin(), absorbs.end(), [](auto const& a, auto const& b)
        {
            return a.second.Amount > b.second.Amount;
        });

        // ---- Time bases ----
        // Rates divide by the time of death in the survive scenario (the fight ended there) and by the full duration
        // otherwise. A survive run that lived counts its TTD as the duration (plan T11).
        bool const diedInSurvive = survive && result.ActorDied;
        uint32 const rateMs = diedInSurvive ? result.ActorDiedAtMs : result.ElapsedMs;
        double const rateSeconds = double(rateMs) / 1000.0;
        double const dtps = SafeDivide(double(takenDamage), rateSeconds);
        double const netDtps = SafeDivide(double(takenDamage) - double(healEffective), rateSeconds);

        // ---- Health and power over time ----
        // Each sample stands for the time up to the next one (the last one for one sample interval), never past the
        // end of the run (the time of death, else the duration: rateMs)
        uint64 msUnder35 = 0;
        for (size_t i = 0; i < result.TankSamples.size(); ++i)
        {
            SimTank::Sample const& sample = result.TankSamples[i];
            if (sample.MaxHealth == 0 || double(sample.Health) / double(sample.MaxHealth) >= 0.35)
                continue;
            uint32 const nextMs = i + 1 < result.TankSamples.size() ?
                result.TankSamples[i + 1].TimestampMs : sample.TimestampMs + SimTank::TANK_SAMPLE_INTERVAL_MS;
            uint32 const endMs = std::min(nextMs, std::max(rateMs, sample.TimestampMs));
            msUnder35 += endMs - sample.TimestampMs;
        }
        // The power type most samples were in (a druid shifts into bear form after the first sample); ties go to
        // the type that reached the count first
        uint8 powerType = 0;
        {
            std::map<uint8, uint32> powerTypeSamples;
            uint32 best = 0;
            for (SimTank::Sample const& sample : result.TankSamples)
            {
                uint32 const n = ++powerTypeSamples[sample.PowerType];
                if (n > best)
                {
                    best = n;
                    powerType = sample.PowerType;
                }
            }
        }

        // ---- Threat: the last sample of every dummy; TPS is their sum over the time base of every rate ----
        for (SimTank::ThreatSample const& sample : result.ThreatSamples)
        {
            if (sample.DummyIndex < dummyCount)
                perDummy[sample.DummyIndex].Threat = sample.Threat;
        }
        double totalThreat = 0.0;
        float lowestThreat = 0.0f;
        int lowestDummy = -1;
        for (size_t i = 0; i < dummyCount; ++i)
        {
            totalThreat += double(perDummy[i].Threat);
            if (lowestDummy < 0 || perDummy[i].Threat < lowestThreat)
            {
                lowestThreat = perDummy[i].Threat;
                lowestDummy = int(i);
            }
        }
        double const tps = SafeDivide(totalThreat, rateSeconds);

        // ---- Write ----
        // Hundredths of a percent -> percent, averaged over the swings
        auto const meanExpectedPct = [swingCount](uint64 hundredths)
        {
            return SafeDivide(double(hundredths) / 100.0, double(swingCount));
        };
        auto const pctOfGross = [grossDamage](uint64 amount)
        {
            return 100.0 * SafeDivide(double(amount), double(grossDamage));
        };

        file << std::fixed << std::setprecision(4);
        file << "  \"tank\": {\n";

        file << "    \"config\": {\n";
        file << "      \"scenario\": \"" << SimTank::ScenarioName(result.TankScenario) << "\",\n";
        file << "      \"hitDamage\": ";
        WriteHitRange(file, config.TankHit);
        file << ",\n      \"packHitDamage\": ";
        WriteHitRange(file, config.TankPackHit);
        file << ",\n";
        file << "      \"dummyKind\": \"" << (config.TargetCount > 1 ? "pack" : "boss") << "\",\n";
        file << "      \"dummyCount\": " << dummyCount << ",\n";
        file << "      \"swingMs\": " << config.TankSwingMs << ",\n";
        file << "      \"dummyCrit\": " << JsonBool(config.TankDummyCrit) << ",\n";
        file << "      \"stepMs\": " << config.StepMs << ",\n";
        file << "      \"pullAuras\": [";
        for (size_t i = 0; i < config.TankPullAuras.size(); ++i)
            file << (i ? ", " : "") << config.TankPullAuras[i];
        file << "],\n";
        file << "      \"dummies\": [\n";
        for (size_t i = 0; i < dummyCount; ++i)
        {
            SimTank::DummyInfo const& d = result.TankDummies[i];
            file << "        {\"index\": " << i << ", \"hitMin\": " << d.Hit.Min << ", \"hitMax\": " << d.Hit.Max
                 << ", \"swingMs\": " << d.SwingMs << ", \"level\": " << d.Level << ", \"levelForTarget\": "
                 << d.LevelForTarget << ", \"armor\": " << d.Armor << ", \"expectedCritPct\": " << d.ExpectedCritPct
                 << ", \"weaponMin\": " << d.WeaponMin << ", \"weaponMax\": " << d.WeaponMax
                 << ", \"attackPower\": " << d.AttackPower << ", \"damageModifier\": " << d.DamageModifier
                 << ", \"basePct\": " << d.BasePct << ", \"fieldMin\": " << d.FieldMin << ", \"fieldMax\": "
                 << d.FieldMax << "}" << (i + 1 < dummyCount ? ",\n" : "\n");
        }
        file << "      ]\n";
        file << "    },\n";

        file << "    \"actor\": {\"afterFirstSecond\": ";
        WriteActorInfo(file, result.TankActor);
        file << ", \"atPull\": ";
        WriteActorInfo(file, result.TankActorAtPull);
        file << "},\n";

        file << "    \"summary\": {\n";
        file << "      \"scenario\": \"" << SimTank::ScenarioName(result.TankScenario) << "\",\n";
        file << "      \"rateBaseMs\": " << rateMs << ",\n";
        file << "      \"swings\": " << swingCount << ",\n";
        file << "      \"swingsLanded\": " << landed << ",\n";
        file << "      \"swingsOutsideFrontArc\": " << outsideArc << ",\n";
        file << "      \"outcomes\": ";
        WriteOutcomeCounts(file, outcomes);
        file << ",\n      \"outcomePct\": ";
        WriteOutcomePercents(file, outcomes);
        file << ",\n";
        file << "      \"blockAnyPct\": " << 100.0 * SafeDivide(double(outcomes.Of(Outcome::Block) +
            outcomes.Of(Outcome::FullBlock)), double(swingCount)) << ",\n";
        file << "      \"avoidancePct\": " << 100.0 * SafeDivide(double(outcomes.Avoided()), double(swingCount))
             << ",\n";
        file << "      \"expectedPct\": {\"miss\": " << meanExpectedPct(expMiss) << ", \"dodge\": "
             << meanExpectedPct(expDodge) << ", \"parry\": " << meanExpectedPct(expParry) << ", \"block\": "
             << meanExpectedPct(expBlock) << ", \"crit\": " << meanExpectedPct(expCrit) << "},\n";
        file << "      \"expectedCritPct\": " << meanExpectedPct(expCrit) << ",\n";
        file << "      \"observedCritPct\": " << 100.0 * SafeDivide(double(outcomes.Of(Outcome::Crit)),
            double(swingCount)) << ",\n";
        file << "      \"critBugCount\": " << critBugCount << ",\n";
        file << "      \"critBugAtMs\": [";
        for (size_t i = 0; i < critBugAt.size(); ++i)
            file << (i ? ", " : "") << critBugAt[i];
        file << "],\n";
        file << "      \"mitigation\": {\"avoided\": " << avoidedDamage << ", \"armor\": " << armorDamage
             << ", \"block\": " << blockedDamage << ", \"absorb\": " << absorbedDamage << ", \"resist\": "
             << resistedDamage << ", \"taken\": " << takenDamage << ", \"gross\": " << grossDamage << "},\n";
        file << "      \"mitigationPct\": {\"avoided\": " << pctOfGross(avoidedDamage) << ", \"armor\": "
             << pctOfGross(armorDamage) << ", \"block\": " << pctOfGross(blockedDamage) << ", \"absorb\": "
             << pctOfGross(absorbedDamage) << ", \"resist\": " << pctOfGross(resistedDamage) << ", \"taken\": "
             << pctOfGross(takenDamage) << "},\n";
        file << "      \"preArmorDamage\": " << preArmorTotal << ",\n";
        file << "      \"damageTaken\": " << takenDamage << ",\n";
        file << "      \"damageAbsorbed\": " << absorbedDamage << ",\n";
        file << "      \"dtps\": " << dtps << ",\n";
        file << "      \"dtpsBeforeShields\": " << SafeDivide(double(takenDamage + absorbedDamage), rateSeconds)
             << ",\n";
        file << "      \"selfHealEffective\": " << healEffective << ",\n";
        file << "      \"selfHealOverheal\": " << healOverheal << ",\n";
        file << "      \"selfHealOverhealPct\": " << 100.0 * SafeDivide(double(healOverheal), double(healRaw))
             << ",\n";
        file << "      \"selfHps\": " << SafeDivide(double(healEffective), rateSeconds) << ",\n";
        file << "      \"netDtps\": " << netDtps << ",\n";
        file << "      \"ttdMs\": ";
        if (!survive)
            file << "null";
        else if (result.ActorDied)
            file << result.ActorDiedAtMs;
        else
            file << result.ElapsedMs;
        file << ",\n";
        file << "      \"survived\": " << JsonBool(result.TankSurvived) << ",\n";
        file << "      \"died\": " << JsonBool(result.ActorDied) << ",\n";
        file << "      \"minHealthPct\": " << result.TankMinHealthPct << ",\n";
        file << "      \"msUnder35Pct\": " << msUnder35 << ",\n";
        file << "      \"powerType\": " << uint32(powerType) << ",\n";
        // Rage only (SwingEvent::RageGained reads POWER_RAGE): 0 for a tank on another resource, which the page hides
        file << "      \"rageGained\": " << double(rageTenths) / 10.0 << ",\n";
        file << "      \"rageGainedPerSec\": " << SafeDivide(double(rageTenths) / 10.0, rateSeconds) << ",\n";
        file << "      \"rageSwingsMeasured\": " << rageSwings << ",\n";
        file << "      \"avoidedSwingsMeasured\": " << avoidSwings << ",\n";
        file << "      \"avoidedSwingsWithRage\": " << avoidSwingsWithRage << ",\n";
        file << "      \"tps\": " << tps << ",\n";
        // Damage dealt and threat built over the time the tank was alive (the time of death, or the duration when it
        // lived): summary.dps divides by the full duration even for a tank that died early (a dead tank is charged
        // the whole fight for DPS), which understates what it did while it lived
        file << "      \"dpsAlive\": " << SafeDivide(double(result.TotalDamage), rateSeconds) << ",\n";
        file << "      \"tpsAlive\": " << SafeDivide(totalThreat, rateSeconds) << ",\n";
        file << "      \"totalThreat\": " << totalThreat << ",\n";
        file << "      \"lowestThreat\": " << lowestThreat << ",\n";
        file << "      \"lowestThreatDummy\": ";
        if (lowestDummy >= 0)
            file << lowestDummy;
        else
            file << "null";
        file << "\n    },\n";

        // One event per line, in recording order
        auto const writeArray = [&file](char const* name, size_t count, auto const& writeEvent, bool last = false)
        {
            file << "    \"" << name << "\": [\n";
            for (size_t i = 0; i < count; ++i)
            {
                file << "      ";
                writeEvent(i);
                file << (i + 1 < count ? ",\n" : "\n");
            }
            file << "    ]" << (last ? "\n" : ",\n");
        };

        writeArray("perDummy", dummyCount, [&](size_t i)
        {
            TankDummyRow const& row = perDummy[i];
            file << "{\"index\": " << i << ", \"swings\": " << row.Outcomes.Total << ", \"outcomes\": ";
            WriteOutcomeCounts(file, row.Outcomes);
            file << ", \"outcomePct\": ";
            WriteOutcomePercents(file, row.Outcomes);
            file << ", \"preArmorDamage\": " << row.PreArmor << ", \"damageTaken\": " << row.Taken
                 << ", \"swingsOutsideFrontArc\": " << row.OutsideArc << ", \"threat\": " << row.Threat << "}";
        });

        writeArray("absorbsBySpell", absorbs.size(), [&](size_t i)
        {
            file << "{\"spellId\": " << absorbs[i].first << ", \"amount\": " << absorbs[i].second.Amount
                 << ", \"events\": " << absorbs[i].second.Events << ", \"pctOfAbsorbed\": "
                 << 100.0 * SafeDivide(double(absorbs[i].second.Amount), double(absorbsAttributed)) << "}";
        });

        writeArray("selfHeals", heals.size(), [&](size_t i)
        {
            TankHealRow const& h = heals[i];
            file << "{\"spellId\": " << h.SpellId << ", \"isPet\": " << JsonBool(h.IsPet) << ", \"casts\": "
                 << h.Casts << ", \"hits\": " << h.Hits << ", \"ticks\": " << h.Ticks << ", \"crits\": " << h.Crits
                 << ", \"effective\": " << h.Effective << ", \"overheal\": " << h.Overheal << ", \"overhealPct\": "
                 << 100.0 * SafeDivide(double(h.Overheal), double(h.Raw)) << ", \"healAbsorbed\": "
                 << h.HealAbsorbed << "}";
        });

        writeArray("swings", result.Swings.size(), [&](size_t i)
        {
            SimTank::SwingEvent const& s = result.Swings[i];
            file << "{\"timestampMs\": " << s.TimestampMs << ", \"dummy\": " << uint32(s.DummyIndex)
                 << ", \"outcome\": \"" << TANK_OUTCOME_KEYS[size_t(s.Result)] << "\", \"preArmor\": " << s.PreArmor
                 << ", \"armor\": " << s.ArmorMitigated << ", \"blocked\": " << s.Blocked << ", \"absorbed\": "
                 << s.Absorbed << ", \"resisted\": " << s.Resisted << ", \"final\": " << s.Final
                 << ", \"rageTenths\": ";
            if (s.RageGained >= 0)
                file << s.RageGained;
            else
                file << "null";
            file << ", \"expected\": {\"miss\": " << double(s.ExpectedMiss) / 100.0 << ", \"dodge\": "
                 << double(s.ExpectedDodge) / 100.0 << ", \"parry\": " << double(s.ExpectedParry) / 100.0
                 << ", \"block\": " << double(s.ExpectedBlock) / 100.0 << ", \"crit\": "
                 << double(s.ExpectedCrit) / 100.0 << "}, \"inFrontArc\": " << JsonBool(s.InFrontArc)
                 << ", \"takenMult\": " << s.TakenMult << "}";
        });

        writeArray("samples", result.TankSamples.size(), [&](size_t i)
        {
            SimTank::Sample const& s = result.TankSamples[i];
            file << "{\"timestampMs\": " << s.TimestampMs << ", \"health\": " << s.Health << ", \"maxHealth\": "
                 << s.MaxHealth << ", \"powerType\": " << uint32(s.PowerType) << ", \"power\": "
                 << TankPowerDisplay(s.PowerType, s.Power) << ", \"maxPower\": "
                 << TankPowerDisplay(s.PowerType, s.MaxPower) << ", \"bulwarkStacks\": "
                 << uint32(s.BulwarkStacks) << "}";
        });

        // Threat over time, one series per dummy: [[timestampMs, threat], ...]
        writeArray("threat", dummyCount, [&](size_t i)
        {
            file << "{\"dummy\": " << i << ", \"samples\": [";
            bool first = true;
            for (SimTank::ThreatSample const& t : result.ThreatSamples)
                if (t.DummyIndex == i)
                {
                    file << (first ? "" : ", ") << "[" << t.TimestampMs << ", " << t.Threat << "]";
                    first = false;
                }
            file << "]}";
        }, true);

        file << "  }\n";
    }
}
