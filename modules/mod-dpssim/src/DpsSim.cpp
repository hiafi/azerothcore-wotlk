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

#include "Config.h"
#include "DpsSim.h"
#include "GameTime.h"
#include "Log.h"
#include "Player.h"
#include "SimActor.h"
#include "SimDaemon.h"
#include "SimProfile.h"
#include "SimReport.h"
#include "SimTests.h"
#include "StringFormat.h"
#include "Timer.h"
#include "Util.h"
#include <algorithm>
#include <sstream>

namespace
{
    // Derives iteration i's own report path from the single DpsSim.ReportPath the conf gives -
    // "<base>.json" -> "<base>.iter<i>.json" (or "<base>.iter<i>" if ReportPath didn't end in
    // ".json" to begin with, though by convention it always does - see that key's own conf doc
    // comment). modules/mod-dpssim/tools/run-sim.sh globs for exactly this pattern after a
    // DpsSim.Iterations > 1 run to collect every iteration's file - see its own comment on that.
    std::string IterationReportPath(std::string const& basePath, uint32 iteration)
    {
        std::string const suffix = ".json";
        std::string const iterTag = ".iter" + std::to_string(iteration);
        if (basePath.size() >= suffix.size() && basePath.compare(basePath.size() - suffix.size(), suffix.size(), suffix) == 0)
            return basePath.substr(0, basePath.size() - suffix.size()) + iterTag + suffix;
        return basePath + iterTag;
    }

    // CharacterDatabaseInfo is "host;port;user;password;database"; AC_CHARACTER_DATABASE_INFO overrides it. Returns
    // the database name, or an empty string if the value is malformed.
    std::string CharactersDatabaseName()
    {
        std::string const info = sConfigMgr->GetOption<std::string>("CharacterDatabaseInfo", "");
        size_t const lastSep = info.rfind(';');
        return lastSep == std::string::npos ? std::string() : info.substr(lastSep + 1);
    }
}

DpsSimWorldScript::DpsSimWorldScript() : WorldScript(MODULE_STRING, {WORLDHOOK_ON_DPS_SIM_RUN}) { }

void DpsSimWorldScript::OnDpsSimRun()
{
    // Fail closed: the sim creates level-up mail, pets and items that draw ids from sequences shared with the live
    // server, so it may only ever run on a disposable characters schema (run-sim.sh creates acore_characters_sim_*).
    // A sim pointed at the live DB, or at a conf with no readable name, refuses to start.
    std::string const charactersDb = CharactersDatabaseName();
    if (charactersDb.empty() || charactersDb == "acore_characters" ||
        charactersDb.rfind("acore_characters_sim", 0) != 0)
    {
        LOG_FATAL("server.dpssim", "mod-dpssim: refusing to run: the characters database is '{}', not a throwaway "
            "'acore_characters_sim*' schema. Use modules/mod-dpssim/tools/run-sim.sh.", charactersDb);
        return;
    }

    // M1 skeleton: this is not the sim daemon yet (SimDaemon/SimActor/SimTarget/SimClock land in
    // follow-up work on this same module, once this foundation is confirmed to boot, build, and
    // link correctly). What this smoke-tests, end to end, in one run:
    //   - the Main.cpp sim-mode branch actually reaches this hook (core patch 4);
    //   - core patch 2 (Timer.h sim-clock override) decouples GameTime/getMSTime() from the real
    //     wall clock, which is the load-bearing fix the "Critical finding" section of the plan
    //     doc is about.
    LOG_INFO("server.dpssim", "mod-dpssim: OnDpsSimRun() reached - sim-mode boot branch is working.");

    // Advance the sim clock in large (accelerated) steps and confirm GameTime/getMSTime() track
    // the override rather than real elapsed wall time - the actual point of core patch 2.
    for (uint32 simMs = 0; simMs <= 5000; simMs += 1000)
    {
        Acore::Time::SetSimClockOverride(Milliseconds(simMs));
        GameTime::UpdateGameTimers();
        LOG_INFO("server.dpssim", "mod-dpssim: sim clock override={}ms -> getMSTime()={}ms, GameTime::GetGameTimeMS()={}ms",
            simMs, getMSTime(), uint32(GameTime::GetGameTimeMS().count()));
    }

    Acore::Time::ClearSimClockOverride();
    LOG_INFO("server.dpssim", "mod-dpssim: M1 skeleton smoke test complete.");

    // DpsSim.RunTests=1 runs Phase 1's four required tests (SimTests::RunAll()); DpsSim.RunPlayerbot=1
    // runs the Phase 2 (M2a) harness instead (SimDaemon::RunPlayerbot() - a real mod-playerbots
    // Engine/Strategy selector driving the actor, see SimBot.h); neither set runs the Phase 1
    // hardcoded-Frostbolt smoke-test job (SimDaemon::Run()) by default. See dpssim.conf.dist,
    // SimTests.h, SimDaemon.h. Read once here rather than cached at LoadConfigSettings() time like
    // a normal hot-path config value would be (per .agents/docs/cpp-guidelines.md) - this only ever
    // runs once per process, at the very end of a one-shot sim-mode boot, so there's no hot path to
    // worry about.
    if (sConfigMgr->GetOption<bool>("DpsSim.RunTests", false))
        SimTests::RunAll();
    else if (sConfigMgr->GetOption<bool>("DpsSim.RunPlayerbot", false))
    {
        // DpsSim.PlayerbotLevel drives both actor and target level (the common case: exercise a
        // bracket's own rotation against that bracket's own dummy - see
        // SimTarget::EntryForLevel()). Defaults to 80, matching RunConfig{}'s own default, so
        // leaving this unset changes nothing about existing behavior.
        SimDaemon::RunConfig config;
        uint32 const level = sConfigMgr->GetOption<uint32>("DpsSim.PlayerbotLevel", 80);
        config.ActorLevel = level;
        config.TargetLevel = level;
        // DpsSim.PlayerbotRace - see RunConfig::ActorRace's own doc comment for why this exists
        // at all (a real, previously-hardcoded RACE_TROLL was firing Berserking mid-run and
        // showing up as an unidentified haste buff in reports before this was found, 2026-09-11).
        config.ActorRace = uint8(sConfigMgr->GetOption<uint32>("DpsSim.PlayerbotRace", 1 /* RACE_HUMAN */));

        // DpsSim.DurationSeconds - overrides RunConfig{}'s own 30s (30000ms) default. Independent
        // of DpsSim.Profile (a profile owns class/talents/gear/stats, never run length).
        config.DurationMs = sConfigMgr->GetOption<uint32>("DpsSim.DurationSeconds", 30) * 1000;

        // DpsSim.StepMs - overrides RunConfig{}'s own 10ms default fixed-timestep size (see
        // SimClock.h). Added 2026-09-13 to make a batch of many iterations (run-sim.sh's
        // [iterations]/stat_weights.py) cheaper to run: fewer, larger Map::Update() calls for the
        // same simulated duration. SimTests::RunTimestepTest() already found 10ms/50ms/1ms agree
        // (exact cast counts, damage within 5%) - but only for Phase 1's hardcoded-Frostbolt
        // RunOnce() rotation, never for the real Engine/Strategy-driven RunPlayerbotOnce() path
        // this key actually affects, so treat a non-default value here as unverified for accuracy
        // until checked against a matching 10ms run.
        config.StepMs = sConfigMgr->GetOption<uint32>("DpsSim.StepMs", 10);

        // DpsSim.TargetCount / TargetSpreadYards / TargetRank - multi-target runs, see RunConfig::TargetCount and
        // dpssim.conf.dist. Run settings like the duration, so the same profile runs at any count.
        bool ready = true;
        uint32 const targetCount = sConfigMgr->GetOption<uint32>("DpsSim.TargetCount", 1);
        config.TargetCount = std::clamp(targetCount, 1u, 10u);
        if (config.TargetCount != targetCount)
            LOG_WARN("server.dpssim", "mod-dpssim: DpsSim.TargetCount {} is outside 1-10 - using {}.", targetCount,
                config.TargetCount);

        // 5 yd is the smallest AoE cluster radius any bot strategy uses (Fire's Flamestrike), so a wider ring would
        // leave dummies outside it
        float const spread = sConfigMgr->GetOption<float>("DpsSim.TargetSpreadYards", 3.0f);
        config.TargetSpreadYards = std::clamp(spread, 0.0f, 5.0f);
        if (config.TargetSpreadYards != spread)
            LOG_WARN("server.dpssim", "mod-dpssim: DpsSim.TargetSpreadYards {} is outside 0-5 - using {}.", spread,
                config.TargetSpreadYards);

        // auto: the boss dummy for one target, so single-target baselines are untouched; elite pack dummies for 2+
        std::string const rank = sConfigMgr->GetOption<std::string>("DpsSim.TargetRank", "auto");
        if (StringEqualI(rank, "boss"))
            config.TargetRank = SimTarget::Rank::Boss;
        else if (StringEqualI(rank, "elite"))
            config.TargetRank = SimTarget::Rank::Elite;
        else if (StringEqualI(rank, "auto"))
            config.TargetRank = config.TargetCount > 1 ? SimTarget::Rank::Elite : SimTarget::Rank::Boss;
        else
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: DpsSim.TargetRank '{}' is not auto, boss or elite - aborting "
                "DpsSim.RunPlayerbot job.", rank);
            ready = false;
        }

        // DpsSim.Profile - see SimProfile.h and dpssim.conf.dist's own doc comment. When set, it
        // owns ActorClass/PlayerbotTalents/PlayerbotGlyphs/GearItemIds/SpellPower/CombatRatings/Stats/AttackPower,
        // the hunter pet, the dummy and pre-pull settings outright (a bad
        // profile aborts the job rather than silently falling back to the flat keys below, so a
        // typo'd profile path never quietly reruns whatever the flat keys happen to say instead).
        // When unset, behavior is unchanged from before profiles existed: DpsSim.PlayerbotTalents
        // directly, ActorClass/GearItemIds/SpellPower/CombatRatings/Stats/AttackPower all at their RunConfig{}
        // defaults (CLASS_MAGE, no gear, no stats - a naked caster) - gear/stats have no flat
        // conf-key equivalent, they only exist via a profile.
        std::string const profilePath = sConfigMgr->GetOption<std::string>("DpsSim.Profile", "");
        if (!profilePath.empty())
        {
            SimProfile::Profile profile;
            if (!SimProfile::Load(profilePath, profile))
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: DpsSim.Profile '{}' failed to load - aborting DpsSim.RunPlayerbot job "
                    "(see SimProfile::Load()'s own error above for why).", profilePath);
                ready = false;
            }
            else
            {
                config.ActorClass = profile.Class;
                config.PlayerbotTalents = profile.PlayerbotTalents;
                config.GearItemIds = profile.GearItemIds;
                config.SpellPower = profile.SpellPower;
                config.CombatRatings = profile.CombatRatings;
                config.Stats = profile.Stats;
                config.AttackPower = profile.AttackPower;
                config.DummyHealthDrain = profile.DummyHealthDrain;
                config.DummyMaxHealth = profile.DummyMaxHealth;
                config.TargetArmor = profile.TargetArmor;
                config.PrePullBuffMs = profile.PrePullBuffMs;
                config.PlayerbotGlyphs = profile.PlayerbotGlyphs;
                config.PetCreatureEntry = profile.PetCreatureEntry;
                if (profile.HealMode)
                {
                    // DpsSim.HealGroup / DpsSim.HealTargets in the conf override the profile's HealGroup / HealTargets
                    // (run-sim.sh sets them per run, so one profile covers every scenario)
                    std::string groupText = sConfigMgr->GetOption<std::string>("DpsSim.HealGroup", "");
                    std::string targetsText = sConfigMgr->GetOption<std::string>("DpsSim.HealTargets", "");
                    if (groupText.empty())
                        groupText = profile.HealGroup;
                    if (targetsText.empty())
                        targetsText = profile.HealTargets;

                    std::string error;
                    bool valid = !groupText.empty() && !targetsText.empty();
                    if (!valid)
                        error = "a Heal profile needs HealGroup and HealTargets (in the profile or as "
                            "DpsSim.HealGroup / DpsSim.HealTargets)";
                    else
                        valid = SimHeal::ParseGroup(groupText, config.HealGroupSize, error) &&
                            SimHeal::ParseTargets(targetsText, config.HealTargets, error) &&
                            SimHeal::Validate(config.HealGroupSize, config.HealTargets, error);
                    if (valid && profile.AllyTankTalents.empty())
                    {
                        valid = false;
                        error = "AllyTankTalents is empty - the tank allies need a Protection talent string";
                    }

                    if (valid && config.DurationMs > SimHeal::MAX_HEAL_DURATION_MS)
                    {
                        // A dead ally releases its spirit after 6 minutes and leaves its slot
                        valid = false;
                        error = Acore::StringFormat("DpsSim.DurationSeconds {} is over the {} s limit of a heal run (a "
                            "dead ally would release its spirit after 6 minutes)", config.DurationMs / 1000,
                            SimHeal::MAX_HEAL_DURATION_MS / 1000);
                    }

                    if (!valid)
                    {
                        LOG_ERROR("server.dpssim", "mod-dpssim: DpsSim.Profile '{}': {} - aborting DpsSim.RunPlayerbot "
                            "job.", profilePath, error);
                        ready = false;
                    }

                    config.RunMode = SimDaemon::Mode::Heal;
                    config.AllyMaxHealthTank = profile.AllyMaxHealthTank;
                    config.AllyMaxHealthDps = profile.AllyMaxHealthDps;
                    config.PinMaxHealth = profile.PinMaxHealth;
                    config.AllyTankTalents = profile.AllyTankTalents;
                    config.AllySpreadYards = profile.AllySpreadYards;
                    config.DrainPulseMs = profile.DrainPulseMs;

                    // DpsSim.InfiniteMana (true/false) overrides the profile's InfiniteMana; empty = the profile's
                    config.InfiniteMana = profile.InfiniteMana;
                    std::string const manaText = sConfigMgr->GetOption<std::string>("DpsSim.InfiniteMana", "");
                    if (StringEqualI(manaText, "1") || StringEqualI(manaText, "true"))
                        config.InfiniteMana = true;
                    else if (StringEqualI(manaText, "0") || StringEqualI(manaText, "false"))
                        config.InfiniteMana = false;
                    else if (!manaText.empty())
                    {
                        LOG_ERROR("server.dpssim", "mod-dpssim: DpsSim.InfiniteMana '{}' is not true or false - "
                            "aborting DpsSim.RunPlayerbot job.", manaText);
                        ready = false;
                    }

                    LOG_INFO("server.dpssim", "mod-dpssim: heal mode - group '{}' ({} members), targets '{}', "
                        "infinite mana {}.", groupText, config.HealGroupSize, targetsText,
                        config.InfiniteMana ? "on" : "off");
                }
                else if (!sConfigMgr->GetOption<std::string>("DpsSim.InfiniteMana", "").empty())
                {
                    // A DPS run has no mana to refill: refuse rather than silently ignore the override
                    LOG_ERROR("server.dpssim", "mod-dpssim: DpsSim.InfiniteMana is set but profile '{}' is not a "
                        "Heal profile (Mode = Heal) - aborting DpsSim.RunPlayerbot job.", profilePath);
                    ready = false;
                }
                // Tank mode: the profile's Tank* keys, each overridden by the DpsSim.Tank* conf key of the same name when it
                // is set (run-sim.sh sets them per run, so one profile covers every scenario). A DPS or heal profile refuses
                // them, as it refuses DpsSim.InfiniteMana without Heal.
                static char const* const TANK_CONF_KEYS[] = {"DpsSim.TankScenario", "DpsSim.TankHitDamage",
                    "DpsSim.TankPackHitDamage", "DpsSim.TankSwingMs", "DpsSim.TankDummyCrit", "DpsSim.TankDummyParryHaste",
                    "DpsSim.TankPullAuras"};
                if (profile.TankMode)
                {
                    config.RunMode = SimDaemon::Mode::Tank;
                    config.TankScenario = profile.TankScenario;
                    config.TankHit = profile.TankHitDamage;
                    config.TankPackHit = profile.TankPackHitDamage;
                    config.TankSwingMs = profile.TankSwingMs;
                    config.TankDummyCrit = profile.TankDummyCrit;
                    config.TankDummyParryHaste = profile.TankDummyParryHaste;

                    std::string error;
                    auto const text = [](char const* key) { return sConfigMgr->GetOption<std::string>(key, ""); };
                    if (std::string v = text("DpsSim.TankScenario"); !v.empty() &&
                        !SimTank::ParseScenario(v, config.TankScenario, error))
                        error = "DpsSim.TankScenario: " + error;
                    else if (std::string v2 = text("DpsSim.TankHitDamage"); error.empty() && !v2.empty() &&
                        !SimTank::ParseHitRange(v2, config.TankHit, error))
                        error = "DpsSim.TankHitDamage: " + error;
                    else if (std::string v3 = text("DpsSim.TankPackHitDamage"); error.empty() && !v3.empty() &&
                        !SimTank::ParseHitRange(v3, config.TankPackHit, error))
                        error = "DpsSim.TankPackHitDamage: " + error;

                    if (error.empty())
                    {
                        std::string const swing = text("DpsSim.TankSwingMs");
                        if (!swing.empty())
                        {
                            uint32 value = 0;
                            if (swing.find_first_not_of("0123456789") != std::string::npos ||
                                (value = uint32(std::stoul(swing))) < SimTank::MIN_SWING_MS ||
                                value > SimTank::MAX_SWING_MS)
                                error = Acore::StringFormat("DpsSim.TankSwingMs '{}' is not a whole number of {}-{} ms",
                                    swing, SimTank::MIN_SWING_MS, SimTank::MAX_SWING_MS);
                            else
                                config.TankSwingMs = value;
                        }
                    }

                    auto const applyFlag = [&](char const* key, bool& target)
                    {
                        std::string const flag = text(key);
                        if (!error.empty() || flag.empty())
                            return;
                        if (StringEqualI(flag, "1") || StringEqualI(flag, "true"))
                            target = true;
                        else if (StringEqualI(flag, "0") || StringEqualI(flag, "false"))
                            target = false;
                        else
                            error = Acore::StringFormat("{} '{}' is not true or false", key, flag);
                    };
                    // DpsSim.TankPullAuras = "6343, 1160": spells the actor casts on every dummy at the pull
                    {
                        std::istringstream ids(text("DpsSim.TankPullAuras"));
                        std::string token;
                        while (std::getline(ids, token, ','))
                        {
                            size_t const first = token.find_first_not_of(" \t");
                            if (first == std::string::npos)
                                continue;
                            token = token.substr(first, token.find_last_not_of(" \t") - first + 1);
                            if (token.find_first_not_of("0123456789") != std::string::npos)
                                error = Acore::StringFormat("DpsSim.TankPullAuras entry '{}' is not a spell id", token);
                            else
                                config.TankPullAuras.push_back(uint32(std::stoul(token)));
                        }
                    }
                    applyFlag("DpsSim.TankDummyCrit", config.TankDummyCrit);
                    applyFlag("DpsSim.TankDummyParryHaste", config.TankDummyParryHaste);

                    if (!error.empty())
                    {
                        LOG_ERROR("server.dpssim", "mod-dpssim: DpsSim.Profile '{}': {} - aborting DpsSim.RunPlayerbot "
                            "job.", profilePath, error);
                        ready = false;
                    }

                    LOG_INFO("server.dpssim", "mod-dpssim: tank mode - scenario {}, boss hit {}, pack hit {}, swing {} ms, "
                        "dummy crit {}, dummy parry haste {}.", SimTank::ScenarioName(config.TankScenario),
                        SimTank::HitRangeText(config.TankHit), SimTank::HitRangeText(config.TankPackHit),
                        config.TankSwingMs, config.TankDummyCrit ? "on" : "off",
                        config.TankDummyParryHaste ? "on" : "off");
                }
                else
                    for (char const* key : TANK_CONF_KEYS)
                        if (!sConfigMgr->GetOption<std::string>(key, "").empty())
                        {
                            LOG_ERROR("server.dpssim", "mod-dpssim: {} is set but profile '{}' is not a Tank profile "
                                "(Mode = Tank) - aborting DpsSim.RunPlayerbot job.", key, profilePath);
                            ready = false;
                        }

                LOG_INFO("server.dpssim",
                    "mod-dpssim: loaded DpsSim.Profile '{}' (class {}, {} gear item(s), spellPower {}, attackPower {}, "
                    "{} synthetic rating(s), {} synthetic stat(s)).",
                    profilePath, profile.Class, profile.GearItemIds.size(), profile.SpellPower, profile.AttackPower,
                    profile.CombatRatings.size(), profile.Stats.size());
            }
        }
        else
            config.PlayerbotTalents = sConfigMgr->GetOption<std::string>("DpsSim.PlayerbotTalents", "");

        // DpsSim.Iterations - added 2026-09-13 alongside SimDaemon::RunPlayerbotBatch(). 1 (the
        // default) keeps today's exact single-run behavior (SimDaemon::RunPlayerbot(), unchanged,
        // including its own detailed timeline log and single DpsSim.ReportPath write). >1 runs the
        // whole batch in this one process (see RunPlayerbotBatch()'s own doc comment for why that's
        // dramatically cheaper than modules/mod-dpssim/tools/run-sim.sh's old per-iteration
        // container approach) and writes one report per iteration via IterationReportPath() above,
        // logging only a one-line summary per iteration rather than RunPlayerbot()'s full per-hit
        // timeline - that much log detail times a real iteration count would be unreadable.
        uint32 const iterations = sConfigMgr->GetOption<uint32>("DpsSim.Iterations", 1);

        // A heal-mode job always runs as a batch (the group persists across iterations); it logs its own summary lines
        bool const heal = config.RunMode == SimDaemon::Mode::Heal;
        // A tank-mode job is a batch too (it logs its own summaries); its results are DPS-kind reports, written below
        bool const tank = config.RunMode == SimDaemon::Mode::Tank;
        if (ready && iterations <= 1 && !heal && !tank)
            SimDaemon::RunPlayerbot(config);
        else if (ready)
        {
            LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - running {} iterations in-process, "
                "actor level {} vs. target level {}, {} target(s) ({}, spread {:.1f} yd).", iterations,
                config.ActorLevel, config.TargetLevel, config.TargetCount, SimTarget::RankName(config.TargetRank),
                config.TargetSpreadYards);

            std::vector<SimDaemon::RunResult> results;
            if (!SimDaemon::RunPlayerbotBatch(config, iterations, results))
            {
                LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() failed - aborting DpsSim.RunPlayerbot job.");
                return;
            }

            std::string const reportPath = sConfigMgr->GetOption<std::string>("DpsSim.ReportPath", "");

            // The heal summaries are logged by RunHealBatch(); the JSON report is one file per iteration, named the
            // way a DPS run's are (the bare path for a single iteration)
            if (heal)
            {
                LOG_INFO("server.dpssim", "mod-dpssim: heal batch complete - {} iteration(s).", results.size());
                if (!reportPath.empty())
                    for (size_t i = 0; i < results.size(); ++i)
                        SimReport::WriteHealJson(results.size() == 1 ? reportPath :
                            IterationReportPath(reportPath, uint32(i + 1)), config, results[i]);

                results.clear();
            }

            for (size_t i = 0; i < results.size(); ++i)
            {
                SimDaemon::RunResult const& result = results[i];
                double const durationSeconds = double(result.ElapsedMs) / 1000.0;
                double const dps = durationSeconds > 0.0 ? double(result.TotalDamage) / durationSeconds : 0.0;
                double const critRate = result.CastCount > 0
                    ? 100.0 * double(result.CritCount) / double(result.CastCount)
                    : 0.0;
                LOG_INFO("server.dpssim", "mod-dpssim:   iteration {}/{} - {} target(s) ({}, spread {:.1f} yd), {} "
                    "landed hits ({} crit, {:.1f}% crit rate), {} total damage, {:.1f} DPS, {} target switches.", i + 1,
                    results.size(), config.TargetCount, SimTarget::RankName(config.TargetRank),
                    config.TargetSpreadYards, result.CastCount, result.CritCount, critRate, result.TotalDamage, dps,
                    result.TargetSwitches);

                if (!reportPath.empty())
                    SimReport::WriteJson(tank && results.size() == 1 ? reportPath :
                        IterationReportPath(reportPath, uint32(i + 1)), config, result);
            }
        }
    }
    else if (sConfigMgr->GetOption<bool>("DpsSim.RunLevelCheck", false))
        SimDaemon::RunLevelScalingCheck();
    else
        SimDaemon::Run();

    LOG_INFO("server.dpssim", "mod-dpssim: OnDpsSimRun() complete, exiting.");
}

DpsSimPlayerScript::DpsSimPlayerScript() : PlayerScript(MODULE_STRING, {PLAYERHOOK_ON_SAVE}) { }

void DpsSimPlayerScript::OnPlayerSave(Player* player)
{
    if (SimActor::IsSimGuid(player->GetGUID()))
        SimActor::NoteSaveAttempt(player->GetGUID());
}

void AddSC_DpsSim()
{
    new DpsSimWorldScript();
    new DpsSimPlayerScript();
}
