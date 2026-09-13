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

#include "SimDaemon.h"
#include "CastRecorder.h"
#include "Config.h"
#include "EventRecorder.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "Playerbots.h"
#include "Random.h"
#include "SimActor.h"
#include "SimBot.h"
#include "SimClock.h"
#include "SimReport.h"
#include "SimTarget.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include <algorithm>
#include <chrono>
#include <string>
#include <thread>

namespace
{
    // See SimDaemon.h's RunResult::ManaSamples doc comment for why this is a periodic sample
    // rather than a per-tick or per-event capture.
    constexpr uint32 MANA_SAMPLE_INTERVAL_MS = 500;

    // Appends a sample if at least MANA_SAMPLE_INTERVAL_MS has passed since the last one (or this
    // is the very first tick) - called once per sim-loop iteration from both RunOnce() and
    // RunPlayerbotOnce() rather than duplicated inline.
    void MaybeSampleMana(Player* actor, uint32 nowMs, uint32& lastSampleMs, bool& sampledOnce,
        std::vector<SimDaemon::RunResult::ManaSample>& samples)
    {
        if (sampledOnce && nowMs - lastSampleMs < MANA_SAMPLE_INTERVAL_MS)
            return;

        samples.push_back({nowMs, actor->GetPowerPct(POWER_MANA)});
        lastSampleMs = nowMs;
        sampledOnce = true;
    }

    // Hardcoded rotation: cast Frostbolt whenever the actor isn't already casting/channeling and
    // both the GCD and Frostbolt's own cooldown (it doesn't have one, but check anyway - Phase 2's
    // rotation engine will need a real cooldown check and this is the pattern it'll follow) are
    // clear. No trigger/relevance engine - that's Phase 2 (see the plan doc's Phase 1 scope note).
    bool RotationTick(Player* actor, Unit* target, SpellInfo const* frostbolt)
    {
        if (actor->IsNonMeleeSpellCast(false))
            return false;

        if (actor->GetGlobalCooldownMgr().HasGlobalCooldown(frostbolt))
            return false;

        if (actor->HasSpellCooldown(frostbolt->Id))
            return false;

        SpellCastResult result = actor->CastSpell(target, frostbolt->Id, false);
        if (result != SPELL_CAST_OK)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: Frostbolt cast attempt failed: SpellCastResult {}.", uint32(result));
            return false;
        }

        return true;
    }

    // Copies EventRecorder's own AuraEvent vector into RunResult's decoupled equivalent - see
    // SimDaemon.h's doc comment on RunResult::AuraEvent for why the two types aren't shared.
    std::vector<SimDaemon::RunResult::AuraEvent> ToRunResultAuraEvents(std::vector<EventRecorder::AuraEvent> const& events)
    {
        std::vector<SimDaemon::RunResult::AuraEvent> result;
        result.reserve(events.size());
        for (EventRecorder::AuraEvent const& e : events)
            result.push_back({e.TimestampMs, e.UnitGuid, e.IsActor, e.SpellId, e.StackAmount, e.Positive, e.Applied});
        return result;
    }

    // Same decoupling reasoning as ToRunResultAuraEvents() above, for CastRecorder::CastEvent.
    std::vector<SimDaemon::RunResult::CastEvent> ToRunResultCastEvents(std::vector<CastRecorder::CastEvent> const& events)
    {
        std::vector<SimDaemon::RunResult::CastEvent> result;
        result.reserve(events.size());
        for (CastRecorder::CastEvent const& e : events)
            result.push_back({e.TimestampMs, e.SpellId});
        return result;
    }
}

bool SimDaemon::RunOnce(RunConfig const& config, RunResult& result)
{
    result = RunResult{};

    SpellInfo const* frostbolt = sSpellMgr->GetSpellInfo(config.SpellId);
    if (!frostbolt)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunOnce() - spell {} not found in spell_dbc - aborting.", config.SpellId);
        return false;
    }

    SimActor actor;
    SimActor::Config actorConfig;
    actorConfig.Name = "SimActor";
    actorConfig.Race = config.ActorRace;
    actorConfig.Class = CLASS_MAGE;
    actorConfig.Gender = GENDER_MALE;
    actorConfig.Level = config.ActorLevel;
    actorConfig.SpellPower = config.SpellPower;
    actorConfig.GearItemIds = config.GearItemIds;
    actorConfig.CombatRatings = config.CombatRatings;
    actorConfig.Stats = config.Stats;
    actorConfig.AttackPower = config.AttackPower;
    if (!actor.Create(actorConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunOnce() - SimActor::Create() failed - aborting.");
        return false;
    }

    Player* player = actor.GetPlayer();

    // GiveLevel() takes a character to a level, it doesn't teach trainer-taught class spells -
    // the rotation's spell has to be learned explicitly, same as a real character would need a
    // trainer visit. This is the hardcoded rotation's own spell, so it's taught here rather than by
    // SimActor (which has no opinion on what spells an actor knows). learnSpell() doesn't itself
    // check spellLevel/baseLevel gating, so this works even for an actor below the spell's normal
    // learn level (config.ActorLevel = 5 against spell 116's BaseLevel = 4 is fine either way).
    player->learnSpell(config.SpellId);

    Map* map = player->GetMap();

    SimTarget target;
    SimTarget::Config targetConfig;
    targetConfig.Level = uint8(config.TargetLevel);
    targetConfig.Armor = config.TargetArmor;
    if (!target.Create(map, player->GetNearPosition(8.0f, 0.0f), targetConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunOnce() - SimTarget::Create() failed - aborting.");
        return false;
    }

    Creature* dummy = target.GetCreature();

    // Must be heap-allocated, not a local/stack object - see EventRecorder.h's doc comment.
    // Deliberately never deleted (ScriptMgr::Unload() owns it from construction onward); calling
    // RunOnce() several times in one process (as SimTests::RunAll() does) leaks one of these per
    // call for the process's remaining lifetime - documented, known, harmless. See EventRecorder.h.
    EventRecorder* recorder = new EventRecorder(player->GetGUID(), dummy->GetGUID(), config.SpellId);

    // Same heap-allocation/never-deleted rules as `recorder` above - see CastRecorder.h's doc
    // comment. Unfiltered by spell id on purpose (a cast log tracks every ability, not just the
    // rotation's one damage spell) - RunOnce()'s hardcoded RotationTick() only ever casts Frostbolt
    // anyway, so this mostly matters for RunPlayerbotOnce() below, but is added here too for symmetry.
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID());

    // Seeded here, immediately before the combat loop, rather than at the top of this function -
    // deliberately isolates the seeded window from actor/target construction above. This was a
    // real diagnostic step, not just tidiness: the plan doc's determinism test found that two
    // back-to-back RunOnce() calls with the same seed produce identical cast/crit counts but
    // different total damage, meaning something consumes a *different number* of random draws
    // between runs somewhere before this point - narrowing the seeded window to exclude
    // construction is the cheapest way to test whether construction is that something, without
    // needing to instrument every call construction makes. See the plan doc's non-determinism
    // section for what this did and didn't resolve.
    SetRandomSeed(config.RandomSeed);

    SimClock clock(config.StepMs);
    uint32 castAttempts = 0;
    uint32 lastManaSampleMs = 0;
    bool sampledManaOnce = false;
    std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
    while (clock.GetElapsedMs() < config.DurationMs)
    {
        clock.Tick(map);
        if (RotationTick(player, dummy, frostbolt))
            ++castAttempts;
        MaybeSampleMana(player, clock.GetElapsedMs(), lastManaSampleMs, sampledManaOnce, manaSamples);

        // Only for the accelerated-clock test (SimDaemon.h's RunConfig::RealTimePaced doc
        // comment) - paces the loop to real wall-clock time instead of running flat-out, so a
        // real-time-paced run can be compared against an accelerated one for identical results.
        if (config.RealTimePaced)
            std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
    }

    result.Success = true;
    result.ElapsedMs = clock.GetElapsedMs();
    result.CastAttempts = castAttempts;
    result.TotalDamage = recorder->GetTotalDamage();
    result.CastCount = recorder->GetCastCount();
    result.CritCount = recorder->GetCritCount();
    result.HitDamages = recorder->GetHitDamages();
    result.HitCrits = recorder->GetHitCrits();
    result.HitSpellIds = recorder->GetHitSpellIds();
    result.HitTimestamps = recorder->GetHitTimestamps();
    result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
    result.ManaSamples = std::move(manaSamples);
    result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());
    return true;
}

bool SimDaemon::RunPlayerbotOnce(RunConfig const& config, RunResult& result)
{
    result = RunResult{};

    SimActor actor;
    SimActor::Config actorConfig;
    actorConfig.Name = "SimBot";
    actorConfig.Race = config.ActorRace;
    actorConfig.Class = config.ActorClass;
    actorConfig.Gender = GENDER_MALE;
    actorConfig.Level = uint8(config.ActorLevel);
    actorConfig.SpellPower = config.SpellPower;
    actorConfig.GearItemIds = config.GearItemIds;
    actorConfig.CombatRatings = config.CombatRatings;
    actorConfig.Stats = config.Stats;
    actorConfig.AttackPower = config.AttackPower;
    if (!actor.Create(actorConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimActor::Create() failed - aborting.");
        return false;
    }

    Player* player = actor.GetPlayer();
    Map* map = player->GetMap();

    SimTarget target;
    SimTarget::Config targetConfig;
    targetConfig.Level = uint8(config.TargetLevel);
    targetConfig.Armor = config.TargetArmor;
    if (!target.Create(map, player->GetNearPosition(8.0f, 0.0f), targetConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimTarget::Create() failed - aborting.");
        return false;
    }

    Creature* dummy = target.GetCreature();

    // rotationSpellId defaults to 0 ("track any spell") - see EventRecorder.h's doc comment - since
    // a real Engine/Strategy casts a whole rotation, not Phase 1's one hardcoded Frostbolt.
    EventRecorder* recorder = new EventRecorder(player->GetGUID(), dummy->GetGUID());

    // Same heap-allocation/never-deleted rules as `recorder` above - see CastRecorder.h's doc
    // comment. This is the recorder that actually matters: a real Engine/Strategy casts a whole
    // rotation, including non-damage abilities (Evocation, self-buffs, ...) EventRecorder has no
    // way to see at all.
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID());

    // SimBot::Create() teaches the bot's class spells and "pulls" `dummy` with one manual cast to
    // bootstrap combat state - see its own doc comment for why that's needed. This happens before
    // SetRandomSeed() below on purpose, same reasoning as RunOnce()'s own reseed placement: keeps
    // the seeded window covering only what the real Engine/Strategy does each tick.
    SimBot bot;
    if (!bot.Create(player, dummy, config.PlayerbotTalents))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimBot::Create() failed - aborting.");
        return false;
    }

    SetRandomSeed(config.RandomSeed);

    SimClock clock(config.StepMs);
    uint32 lastManaSampleMs = 0;
    bool sampledManaOnce = false;
    std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
    while (clock.GetElapsedMs() < config.DurationMs)
    {
        clock.Tick(map);
        bot.UpdateAI(config.StepMs);
        MaybeSampleMana(player, clock.GetElapsedMs(), lastManaSampleMs, sampledManaOnce, manaSamples);

        // Only for the accelerated-clock test - see RunConfig::RealTimePaced's doc comment.
        if (config.RealTimePaced)
            std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
    }

    result.Success = true;
    result.ElapsedMs = clock.GetElapsedMs();
    // No separate "cast attempts" counter here, unlike RunOnce()'s hardcoded rotation: the real
    // Engine decides what to cast and when internally, with no equivalent hook exposed for
    // "attempted but didn't land" bookkeeping. CastCount (landed hits) is the meaningful number.
    result.CastAttempts = recorder->GetCastCount();
    result.TotalDamage = recorder->GetTotalDamage();
    result.CastCount = recorder->GetCastCount();
    result.CritCount = recorder->GetCritCount();
    result.HitDamages = recorder->GetHitDamages();
    result.HitCrits = recorder->GetHitCrits();
    result.HitSpellIds = recorder->GetHitSpellIds();
    result.HitTimestamps = recorder->GetHitTimestamps();
    result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
    result.ManaSamples = std::move(manaSamples);
    result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());
    return true;
}

void SimDaemon::Run()
{
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::Run() - M1 harness, hardcoded Frostbolt-only rotation.");

    RunResult result;
    if (!RunOnce(RunConfig{}, result))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::Run() - RunOnce() failed - aborting.");
        return;
    }

    double const durationSeconds = double(result.ElapsedMs) / 1000.0;
    double const dps = double(result.TotalDamage) / durationSeconds;
    double const critRate = result.CastCount > 0
        ? 100.0 * double(result.CritCount) / double(result.CastCount)
        : 0.0;

    // CastAttempts (CastSpell() calls that returned SPELL_CAST_OK) and CastCount (landed hits
    // EventRecorder actually observed) can differ by one at the tail end of the run: a cast
    // started just before the duration completes its ~3s cast time slightly after the loop above
    // stops ticking, so its damage event never fires within this run. Logging both makes that
    // visible instead of silently picking one.
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::Run() complete - {}ms sim time, {} cast attempts, {} landed hits ({} crit, {:.1f}% crit rate), {} total damage, {:.1f} DPS.",
        result.ElapsedMs, result.CastAttempts, result.CastCount, result.CritCount, critRate, result.TotalDamage, dps);
}

void SimDaemon::RunPlayerbot(RunConfig const& config)
{
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() - M2a harness, real mod-playerbots Engine/Strategy selector, actor level {} vs. target level {}.",
        config.ActorLevel, config.TargetLevel);

    RunResult result;
    if (!RunPlayerbotOnce(config, result))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() - RunPlayerbotOnce() failed - aborting.");
        return;
    }

    double const durationSeconds = double(result.ElapsedMs) / 1000.0;
    double const dps = double(result.TotalDamage) / durationSeconds;
    double const critRate = result.CastCount > 0
        ? 100.0 * double(result.CritCount) / double(result.CastCount)
        : 0.0;

    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() complete - {}ms sim time, {} landed hits ({} crit, {:.1f}% crit rate), {} total damage, {:.1f} DPS.",
        result.ElapsedMs, result.CastCount, result.CritCount, critRate, result.TotalDamage, dps);

    LOG_INFO("server.dpssim", "mod-dpssim:   {} aura events (buffs/debuffs gained or lost by the actor or target).",
        result.AuraEvents.size());

    // Merged, timestamp-sorted timeline of every hit and aura event - added 2026-09-11 to directly
    // observe whether talent-gated procs (Fingers of Frost, Brain Freeze, Arcane Blast stacks, ...)
    // actually fire, rather than inferring it from which spells get cast. A first step toward M3's
    // full timeline report, not that report itself (no HTML, no per-spell aggregation yet).
    struct TimelineEntry
    {
        uint32 TimestampMs;
        std::string Text;
    };
    std::vector<TimelineEntry> timeline;
    timeline.reserve(result.HitDamages.size() + result.AuraEvents.size());
    for (size_t i = 0; i < result.HitDamages.size(); ++i)
    {
        timeline.push_back({result.HitTimestamps[i], Acore::StringFormat(
            "hit - spell {} - {} damage{}", result.HitSpellIds[i], result.HitDamages[i],
            result.HitCrits[i] ? " (crit)" : "")});
    }
    for (RunResult::AuraEvent const& e : result.AuraEvents)
    {
        timeline.push_back({e.TimestampMs, Acore::StringFormat(
            "aura {} - spell {} on {} (stack {}){}", e.Applied ? "gained" : "lost", e.SpellId,
            e.IsActor ? "actor" : "target", e.StackAmount, e.Positive ? "" : " (debuff)")});
    }
    std::stable_sort(timeline.begin(), timeline.end(),
        [](TimelineEntry const& a, TimelineEntry const& b) { return a.TimestampMs < b.TimestampMs; });

    for (TimelineEntry const& entry : timeline)
        LOG_INFO("server.dpssim", "mod-dpssim:   t={}ms {}", entry.TimestampMs, entry.Text);

    // Opt-in JSON export for the M3 HTML report - off by default like every other DpsSim.* flag in
    // this module. Deliberately no spell-name resolution here - see SimReport.h's doc comment for
    // why that happens outside this process, against the DB directly, when the report is built.
    std::string const reportPath = sConfigMgr->GetOption<std::string>("DpsSim.ReportPath", "");
    if (!reportPath.empty())
        SimReport::WriteJson(reportPath, config, result);
}

void SimDaemon::RunLevelScalingCheck()
{
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunLevelScalingCheck() - does spell {} scale with caster level?",
        SINGLE_RANK_FROSTBOLT_SPELL_ID);

    // Same seed, same target (level 80, 0 armor - RunConfig's own defaults, held constant on
    // purpose so caster level is the only thing that differs between the two runs), only
    // ActorLevel changes. RunOnce() rather than RunPlayerbotOnce(): the hardcoded RotationTick()
    // casts one spell id directly regardless of spellbook/level-availability rules, which is
    // exactly what answering "does this spell scale with level" needs - RunPlayerbotOnce()'s real
    // Engine/PlayerbotFactory path would introduce spellbook-by-level as a confound.
    for (uint32 const level : {5u, 60u})
    {
        RunConfig config;
        config.ActorLevel = level;
        config.SpellId = SINGLE_RANK_FROSTBOLT_SPELL_ID;

        RunResult result;
        if (!RunOnce(config, result))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunLevelScalingCheck() - RunOnce() failed for level {} - aborting.", level);
            return;
        }

        double const avgDamage = result.CastCount > 0
            ? double(result.TotalDamage) / double(result.CastCount)
            : 0.0;

        LOG_INFO("server.dpssim", "mod-dpssim: level {} - {} cast attempts, {} landed hits, {} total damage, {:.1f} average damage per hit.",
            level, result.CastAttempts, result.CastCount, result.TotalDamage, avgDamage);

        for (size_t i = 0; i < result.HitDamages.size(); ++i)
        {
            LOG_INFO("server.dpssim", "mod-dpssim:   level {} hit #{} - {} damage{}",
                level, i, result.HitDamages[i], result.HitCrits[i] ? " (crit)" : "");
        }
    }
}
