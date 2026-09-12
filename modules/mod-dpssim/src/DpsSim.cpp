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
#include "Random.h"
#include "SimDaemon.h"
#include "SimProfile.h"
#include "SimTests.h"
#include "Timer.h"

DpsSimWorldScript::DpsSimWorldScript() : WorldScript(MODULE_STRING, {WORLDHOOK_ON_DPS_SIM_RUN}) { }

void DpsSimWorldScript::OnDpsSimRun()
{
    // M1 skeleton: this is not the sim daemon yet (SimDaemon/SimActor/SimTarget/SimClock land in
    // follow-up work on this same module, once this foundation is confirmed to boot, build, and
    // link correctly). What this smoke-tests, end to end, in one run:
    //   - the Main.cpp sim-mode branch actually reaches this hook (core patch 4);
    //   - core patch 1 (RNG seed setter) produces a reproducible roll sequence;
    //   - core patch 2 (Timer.h sim-clock override) decouples GameTime/getMSTime() from the real
    //     wall clock, which is the load-bearing fix the "Critical finding" section of the plan
    //     doc is about.
    LOG_INFO("server.dpssim", "mod-dpssim: OnDpsSimRun() reached - sim-mode boot branch is working.");

    SetRandomSeed(12345);
    LOG_INFO("server.dpssim", "mod-dpssim: seeded urand(1,100) x5 = {}, {}, {}, {}, {}",
        urand(1, 100), urand(1, 100), urand(1, 100), urand(1, 100), urand(1, 100));

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

        // DpsSim.Profile - see SimProfile.h and dpssim.conf.dist's own doc comment. When set, it
        // owns ActorClass/PlayerbotTalents/GearItemIds/SpellPower/CombatRatings/Stats/AttackPower outright (a bad
        // profile aborts the job rather than silently falling back to the flat keys below, so a
        // typo'd profile path never quietly reruns whatever the flat keys happen to say instead).
        // When unset, behavior is unchanged from before profiles existed: DpsSim.PlayerbotTalents
        // directly, ActorClass/GearItemIds/SpellPower/CombatRatings/Stats/AttackPower all at their RunConfig{}
        // defaults (CLASS_MAGE, no gear, no stats - a naked caster) - gear/stats have no flat
        // conf-key equivalent, they only exist via a profile.
        bool ready = true;
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
                LOG_INFO("server.dpssim",
                    "mod-dpssim: loaded DpsSim.Profile '{}' (class {}, {} gear item(s), spellPower {}, attackPower {}, "
                    "{} synthetic rating(s), {} synthetic stat(s)).",
                    profilePath, profile.Class, profile.GearItemIds.size(), profile.SpellPower, profile.AttackPower,
                    profile.CombatRatings.size(), profile.Stats.size());
            }
        }
        else
            config.PlayerbotTalents = sConfigMgr->GetOption<std::string>("DpsSim.PlayerbotTalents", "");

        if (ready)
            SimDaemon::RunPlayerbot(config);
    }
    else if (sConfigMgr->GetOption<bool>("DpsSim.RunLevelCheck", false))
        SimDaemon::RunLevelScalingCheck();
    else
        SimDaemon::Run();

    LOG_INFO("server.dpssim", "mod-dpssim: OnDpsSimRun() complete, exiting.");
}

void AddSC_DpsSim()
{
    new DpsSimWorldScript();
}
