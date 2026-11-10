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

#include "SimBossMechanics.h"

#if DPSSIM_WITH_BOSS_MECHANICS
#include "BossMechanicsSim.h"
#include "Map.h"
#include "StringFormat.h"
#include <algorithm>
#include <atomic>
#include <iterator>
#include <optional>
#include <string>

namespace
{
    // The sim runs MapUpdate.Threads 0, so the module calls the sink on the driver's own thread; atomic anyway, as the
    // module's own sink pointer is
    std::atomic<SimMech::Sink> s_sink{ nullptr };

    void ForwardFailure(Map const* map, BossMechanics::FailureEvent const& e)
    {
        SimMech::Sink const sink = s_sink.load(std::memory_order_acquire);
        if (!sink)
            return;

        SimMech::Failure f;
        f.MapId = map ? map->GetId() : 0;
        f.Encounter = e.encounter;
        f.Player = e.player;
        f.Type = BossMechanics::FailureTypeName(e.type);
        f.Kind = BossMechanics::KindName(e.kind);
        f.MechanicId = e.mechanicId;
        f.Tag = e.tag;
        f.Damage = e.damage;
        f.AtMs = uint32(e.at.count());
        sink(f);
    }

    // MechanicBotCounters, by name. The "...Last" values are left out (a snapshot of the last solve says nothing over
    // an iteration); the Debug-only SolveStats / NavOracleStats too (BossMechanics.Bots.Debug is 0 in the sim).
    void FlattenCounters(BossMechanics::MechanicBotCounters const& c, std::vector<std::pair<std::string, uint64>>& out)
    {
        static char const* const OUTCOMES[] = { "outcomeSafe", "outcomeMove", "outcomeGraceMove", "outcomeFallback",
            "outcomeNoPath" };
        static_assert(std::size(OUTCOMES) == BossMechanics::MechanicBotCounters::kOutcomes,
            "one name per Solver::Outcome");

        out.emplace_back("solves", c.solves);
        out.emplace_back("pathChecks", c.pathChecks);
        for (size_t i = 0; i < c.outcomes.size(); ++i)
            out.emplace_back(OUTCOMES[i], c.outcomes[i]);
        out.emplace_back("tightMoves", c.tightMoves);
        out.emplace_back("pocketMoves", c.pocketMoves);
        out.emplace_back("pocketPathChecks", c.pocketPathChecks);
        out.emplace_back("lateArrivals", c.lateArrivals);
        out.emplace_back("lateFallbacks", c.lateFallbacks);
        out.emplace_back("stuckResolves", c.stuckResolves);
        out.emplace_back("releases", c.releases);
        out.emplace_back("motionStops", c.motionStops);
        out.emplace_back("reroutes", c.reroutes);
        out.emplace_back("lockBlocks", c.lockBlocks);
        out.emplace_back("lockMoves", c.lockMoves);
        out.emplace_back("lockCasts", c.lockCasts);
        out.emplace_back("castBreaks", c.castBreaks);
        out.emplace_back("wakes", c.wakes);
        out.emplace_back("descriptorWakes", c.descriptorWakes);
        out.emplace_back("solveUsMax", c.solveUsMax);
        out.emplace_back("solveUsTotal", c.solveUsTotal);
        // M5 C4: the allies' refresh before a solve, timed apart from Solver::Solve (solveUsMax no longer holds it)
        out.emplace_back("solveRefreshes", c.solveRefreshes);
        out.emplace_back("refreshUsMax", c.refreshUsMax);
        out.emplace_back("refreshUsTotal", c.refreshUsTotal);
        out.emplace_back("carrierSolves", c.carrierSolves);
        out.emplace_back("claimSolves", c.claimSolves);
        out.emplace_back("pickSolves", c.pickSolves);
        out.emplace_back("roleSolves", c.roleSolves);
        out.emplace_back("violatedPlans", c.violatedPlans);
        out.emplace_back("freezes", c.freezes);
        out.emplace_back("facingsApplied", c.facingsApplied);
        out.emplace_back("facingBlocks", c.facingBlocks);
        out.emplace_back("facingBreaks", c.facingBreaks);
        out.emplace_back("escapeFacingBlocks", c.escapeFacingBlocks);
        out.emplace_back("tankRefacings", c.tankRefacings);
        out.emplace_back("refacingStops", c.refacingStops);
        out.emplace_back("parks", c.parks);
        out.emplace_back("routesFound", c.routesFound);
        out.emplace_back("routesFailed", c.routesFailed);
        out.emplace_back("routeUsMax", c.routeUsMax);
        out.emplace_back("sightRays", c.sightRays);
        // M4 (WP-C, WP-X)
        out.emplace_back("fallbackClear", c.fallbackClear);
        out.emplace_back("fallbackHot", c.fallbackHot);
        out.emplace_back("fallbackKept", c.fallbackKept);
        out.emplace_back("routeLoops", c.routeLoops);
        out.emplace_back("regionRoutes", c.regionRoutes);
        out.emplace_back("regionRoutesFound", c.regionRoutesFound);
        out.emplace_back("msOutOfBand", c.msOutOfBand);
        out.emplace_back("msOutOfBandTask", c.msOutOfBandTask);
        out.emplace_back("pullBlocks", c.pullBlocks);
        out.emplace_back("pullsEnded", c.pullsEnded);
        out.emplace_back("landingBlocks", c.landingBlocks);
        out.emplace_back("motionEndStops", c.motionEndStops);
        out.emplace_back("moverBreaks", c.moverBreaks);
        // M4 WP-F2 (STAGE-M4-R2-REPORT M-1, m-3): melee time out of reach with the chase refused, the chase valve.
        out.emplace_back("msChaseRefused", c.msChaseRefused);
        out.emplace_back("chaseReleases", c.chaseReleases);
        out.emplace_back("chaseSolves", c.chaseSolves);
        out.emplace_back("msChaseStranded", c.msChaseStranded);
        out.emplace_back("strandRoutes", c.strandRoutes);
        out.emplace_back("forcedMoves", c.forcedMoves);
        out.emplace_back("forcedCasts", c.forcedCasts);
        out.emplace_back("forcedTurns", c.forcedTurns);
        out.emplace_back("specificBlocks", c.specificBlocks);
        out.emplace_back("doBypasses", c.doBypasses);
        out.emplace_back("unknownCasts", c.unknownCasts);
        // M5 WP-T: targets and the ignore list
        out.emplace_back("focusSwitches", c.focusSwitches);
        out.emplace_back("msLowerTarget", c.msLowerTarget);
        out.emplace_back("breakOutMsMax", c.breakOutMsMax);
        out.emplace_back("ignoredHits", c.ignoredHits);
        out.emplace_back("ignoredDamage", c.ignoredDamage);
        out.emplace_back("petIgnoredHits", c.petIgnoredHits);
        out.emplace_back("petIgnoredDamage", c.petIgnoredDamage);
        out.emplace_back("ignoreBlocks", c.ignoreBlocks);
        out.emplace_back("ignoreDrops", c.ignoreDrops);
        out.emplace_back("petRecalls", c.petRecalls);
        // M5 WP-P: dispels and purges
        out.emplace_back("urgentDispels", c.urgentDispels);
        out.emplace_back("urgentLatencyMsMax", c.urgentLatencyMsMax);
        out.emplace_back("deadlineDispels", c.deadlineDispels);
        out.emplace_back("deadlineMisses", c.deadlineMisses);
        out.emplace_back("listedDispels", c.listedDispels);
        out.emplace_back("purges", c.purges);
        out.emplace_back("dispelWrongAura", c.dispelWrongAura);     // M5 WP-F: a cure removed another aura
        // M5 WP-I: interrupts. listedMissed is counted by one bot of the group (the observer): sum it over the group.
        out.emplace_back("kicksLanded", c.kicksLanded);
        out.emplace_back("kicksWasted", c.kicksWasted);
        out.emplace_back("doNotKickKicks", c.doNotKickKicks);
        out.emplace_back("duplicateKicks", c.duplicateKicks);
        out.emplace_back("overloadHolds", c.overloadHolds);
        out.emplace_back("listedMissed", c.listedMissed);
        out.emplace_back("stockKicksDropped", c.stockKicksDropped);
        out.emplace_back("castStops", c.castStops);     // M5 WP-F: stuns and silences judged as kicks
        // A new counter: one line here (a name ending in "Max" is aggregated as a maximum, any other as a sum), then
        // tools/mechanics_sweep.py DESCRIPTOR_COUNTERS (or member_line) and the report template's `names`.
    }

    // One UsHistogram as summable numbers: <name>Count, <name>Total (us), <name>Max (us) and the bucket counts
    // <name>B00..B15 (bucket 0 is [0, 2) us, bucket b [2^b, 2^(b+1)) us, the last one 32,768 us and up), so the
    // aggregate and the sweep can read quantiles over every iteration
    void FlattenHistogram(char const* name, BossMechanics::UsHistogram const& h,
        std::vector<std::pair<std::string, double>>& out)
    {
        std::string const base(name);
        out.emplace_back(base + "Count", double(h.count));
        out.emplace_back(base + "Total", double(h.total));
        out.emplace_back(base + "Max", double(h.max));
        for (size_t b = 0; b < h.buckets.size(); ++b)
            out.emplace_back(base + (b < 10 ? "B0" : "B") + std::to_string(b), double(h.buckets[b]));
    }

    // CostStats (STAGE-M4 §3.6, MechanicCost.h), by name. A name ending in "Max" is aggregated as a maximum, every
    // other as a sum; add a line here when the struct grows.
    void FlattenCost(BossMechanics::CostStats const& cost, std::vector<std::pair<std::string, double>>& out)
    {
        FlattenHistogram("pathUs", cost.pathUs, out);
        FlattenHistogram("probeUs", cost.probeUs, out);
        FlattenHistogram("sightUs", cost.sightUs, out);
        FlattenHistogram("solveUs", cost.solveUs, out);
        FlattenHistogram("routeUs", cost.routeUs, out);
        FlattenHistogram("brainUs", cost.brainUs, out);
        out.emplace_back("laneSolves", double(cost.laneSolves));
        out.emplace_back("laneCandidates", double(cost.laneCandidates));
        out.emplace_back("lanePathCalls", double(cost.lanePathCalls));

        // Per mechanic: the folded ones plus the ones still live when the stats were read
        uint32 mechanics = 0;
        uint32 maxCalls = 0;
        double meanCalls = 0.0;
        cost.PerMechanic(mechanics, maxCalls, meanCalls);
        out.emplace_back("mechanicsSeen", double(mechanics));
        out.emplace_back("mechanicPathCallsMax", double(maxCalls));
        uint64 totalCalls = cost.mechanicPathCallsTotal;
        for (auto const& [mechanicId, calls] : cost.livePathCalls)
            totalCalls += calls;
        out.emplace_back("mechanicPathCallsTotal", double(totalCalls));
        out.emplace_back("pathCallsUnattributed", double(cost.pathCallsUnattributed));

        out.emplace_back("mapUpdates", double(cost.mapUpdates));
        out.emplace_back("mapBrainUsMax", double(cost.mapBrainUsMax));
        out.emplace_back("mapBrainUsTotal", double(cost.mapBrainUsTotal));
    }
}

bool SimMech::Available()
{
    return true;
}

bool SimMech::RegisterBotGlue()
{
    return BossMechanics::Sim::RegisterBotGlue();
}

bool SimMech::ReconcileBot(Player* bot)
{
    return BossMechanics::Sim::ReconcileBot(bot);
}

void SimMech::SetSink(Sink sink)
{
    s_sink.store(sink, std::memory_order_release);
    BossMechanics::Sim::SetFailureSink(sink ? &ForwardFailure : nullptr);
}

bool SimMech::CheckProgram(std::string const& program, uint32 fightMs, uint32& lengthMs,
    std::vector<std::string>& lateEntries, std::string& err)
{
    std::optional<BossMechanics::Drill::Program> const parsed = BossMechanics::Drill::ParseProgram(program, err);
    if (!parsed)
        return false;

    // The end of the last entry (loopMs adds the quiet gap after it)
    lengthMs = 0;
    lateEntries.clear();
    for (size_t i = 0; i < parsed->entries.size(); ++i)
    {
        BossMechanics::Drill::ProgramEntry const& entry = parsed->entries[i];
        lengthMs = std::max(lengthMs, entry.startMs + entry.lengthMs);
        if (entry.startMs >= fightMs)
            lateEntries.push_back(Acore::StringFormat("{} at {} s", entry.drill ? std::string(entry.drill->name)
                : Acore::StringFormat("entry {}", i + 1), entry.startMs / 1000));
    }
    return true;
}

bool SimMech::StartProgram(Creature* owner, ObjectGuid scopePlayer, std::string const& program, uint32 seed,
    int32 damage, std::string& err)
{
    BossMechanics::DrillOptions opt;
    opt.seed = seed;
    opt.dmg = damage;
    opt.includeScopePlayer = true;
    opt.loop = false;
    return BossMechanics::Sim::StartProgram(owner, scopePlayer, program, opt, err);
}

void SimMech::StopProgram(Creature* owner)
{
    BossMechanics::Sim::StopProgram(owner);
}

uint32 SimMech::TakeProgramErrors(Creature const* owner, std::vector<std::string>& messages)
{
    BossMechanics::Sim::ProgramErrors errors = BossMechanics::Sim::TakeProgramErrors(owner);
    messages = std::move(errors.messages);
    return errors.count;
}

bool SimMech::ReadStats(Player const* bot, Stats& out)
{
    out = Stats();
    BossMechanics::Sim::BotStats stats;
    if (!BossMechanics::Sim::ReadBotStats(bot, stats))
        return false;

    out.Valid = true;
    FlattenCounters(stats.counters, out.Counters);
    out.ModeMs = {
        { "idle", stats.msIdle }, { "watch", stats.msWatch }, { "escape", stats.msEscape }, { "hold", stats.msHold },
        { "freeze", stats.msFreeze }, { "released", stats.msReleased },
    };
    out.LeakMoves = stats.leakMoves;
    out.LeakCasts = stats.leakCasts;
    out.LeakTurns = stats.leakTurns;
    out.LeakSpells = stats.leakSpells;
    FlattenCost(stats.cost, out.Cost);
    return true;
}

void SimMech::ResetStats(Player const* bot)
{
    BossMechanics::Sim::ResetBotStats(bot);
}

#else

// Built without mod-boss-mechanics: every call is a no-op, and the mechanics batch refuses to start (Available())

bool SimMech::Available()
{
    return false;
}

bool SimMech::RegisterBotGlue()
{
    return false;
}

bool SimMech::ReconcileBot(Player* /*bot*/)
{
    return false;
}

void SimMech::SetSink(Sink /*sink*/)
{
}

bool SimMech::CheckProgram(std::string const& /*program*/, uint32 /*fightMs*/, uint32& lengthMs,
    std::vector<std::string>& lateEntries, std::string& err)
{
    lengthMs = 0;
    lateEntries.clear();
    err = "mod-boss-mechanics is not built with this worldserver";
    return false;
}

bool SimMech::StartProgram(Creature* /*owner*/, ObjectGuid /*scopePlayer*/, std::string const& /*program*/,
    uint32 /*seed*/, int32 /*damage*/, std::string& err)
{
    err = "mod-boss-mechanics is not built with this worldserver";
    return false;
}

void SimMech::StopProgram(Creature* /*owner*/)
{
}

uint32 SimMech::TakeProgramErrors(Creature const* /*owner*/, std::vector<std::string>& messages)
{
    messages.clear();
    return 0;
}

bool SimMech::ReadStats(Player const* /*bot*/, Stats& out)
{
    out = Stats();
    return false;
}

void SimMech::ResetStats(Player const* /*bot*/)
{
}

#endif
