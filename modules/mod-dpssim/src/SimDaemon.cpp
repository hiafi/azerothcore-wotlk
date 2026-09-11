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
#include "EventRecorder.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include "Playerbots.h"
#include "Random.h"
#include "SimActor.h"
#include "SimBot.h"
#include "SimClock.h"
#include "SimTarget.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include <chrono>
#include <thread>

namespace
{
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
    actorConfig.Race = RACE_TROLL;
    actorConfig.Class = CLASS_MAGE;
    actorConfig.Gender = GENDER_MALE;
    actorConfig.Level = config.ActorLevel;
    actorConfig.SpellPower = config.SpellPower;
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
    targetConfig.Level = 80;
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
    while (clock.GetElapsedMs() < config.DurationMs)
    {
        clock.Tick(map);
        if (RotationTick(player, dummy, frostbolt))
            ++castAttempts;

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
    return true;
}

bool SimDaemon::RunPlayerbotOnce(RunConfig const& config, RunResult& result)
{
    result = RunResult{};

    SimActor actor;
    SimActor::Config actorConfig;
    actorConfig.Name = "SimBot";
    actorConfig.Race = RACE_TROLL;
    actorConfig.Class = CLASS_MAGE;
    actorConfig.Gender = GENDER_MALE;
    actorConfig.Level = 80;
    actorConfig.SpellPower = config.SpellPower;
    if (!actor.Create(actorConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimActor::Create() failed - aborting.");
        return false;
    }

    Player* player = actor.GetPlayer();
    Map* map = player->GetMap();

    SimTarget target;
    SimTarget::Config targetConfig;
    targetConfig.Level = 80;
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

    // SimBot::Create() teaches the bot's class spells and "pulls" `dummy` with one manual cast to
    // bootstrap combat state - see its own doc comment for why that's needed. This happens before
    // SetRandomSeed() below on purpose, same reasoning as RunOnce()'s own reseed placement: keeps
    // the seeded window covering only what the real Engine/Strategy does each tick.
    SimBot bot;
    if (!bot.Create(player, dummy))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimBot::Create() failed - aborting.");
        return false;
    }

    SetRandomSeed(config.RandomSeed);

    SimClock clock(config.StepMs);
    while (clock.GetElapsedMs() < config.DurationMs)
    {
        clock.Tick(map);
        bot.UpdateAI(config.StepMs);

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

void SimDaemon::RunPlayerbot()
{
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() - M2a harness, real mod-playerbots Engine/Strategy selector.");

    RunResult result;
    if (!RunPlayerbotOnce(RunConfig{}, result))
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

    // Per-hit breakdown - the actual point of this run: proving the real rotation casts a variety
    // of spells on its own, not just repeating one hardcoded id.
    for (size_t i = 0; i < result.HitDamages.size(); ++i)
    {
        LOG_INFO("server.dpssim", "mod-dpssim:   hit #{} - spell {} - {} damage{}",
            i, result.HitSpellIds[i], result.HitDamages[i], result.HitCrits[i] ? " (crit)" : "");
    }
}

namespace
{
    // Spell 116 - "Frostbolt", no rank suffix, SpellLevel/BaseLevel 4, MaxLevel 80 - this
    // deployment's sole surviving Frostbolt rank after the migration to a single-rank spell
    // system (see RunConfig::SpellId's doc comment). Deliberately not FROSTBOLT_SPELL_ID (25304,
    // Rank 11): that spell still exists in spell_dbc but is no longer taught, so it's not what a
    // real character actually casts anymore.
    constexpr uint32 SINGLE_RANK_FROSTBOLT_SPELL_ID = 116;
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
