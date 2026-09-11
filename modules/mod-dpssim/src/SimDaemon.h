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

#ifndef MODULE_DPSSIM_SIMDAEMON_H
#define MODULE_DPSSIM_SIMDAEMON_H

#include "Define.h"
#include <vector>

// M1 in-process entry point: wires SimActor + SimTarget + SimClock + the hardcoded Frostbolt
// rotation + EventRecorder together into one fixed-timestep sim run.
//
// Deliberately not yet the job-socket-protocol daemon the design doc's file layout names it after
// (docs/dps-sim-module.md section 4) - Phase 1's own task list says "a single in-process call is
// enough for M1"; the JSON job protocol is M3+ work. Kept the name anyway since this is the
// module's one entry point today and is expected to grow into that daemon rather than be replaced
// by it.
namespace SimDaemon
{
    // Frostbolt Rank 11 (spell_dbc id 25304) - the max rank in a WotLK 3.3.5 client: Blizzard
    // stopped adding new Frostbolt ranks after Rank 11 (learnable at level 60) and let the
    // TBC-era spell-power-coefficient scaling carry it the rest of the way to level 80, rather
    // than shipping a Rank 12+. Confirmed against this deployment's own spell_dbc table rather
    // than assumed. Exposed here (not just SimDaemon.cpp's anonymous namespace) because
    // SimTests.cpp needs it too, for its hand-computed known-value expectations.
    constexpr uint32 FROSTBOLT_SPELL_ID = 25304;

    // One sim job's parameters. Defaults match the M1 smoke-test job Run() has always used
    // (level-80 Troll Mage, unbuffed, vs. a level-80 zero-armor target, 30s at a 10ms step) - see
    // SimTests.cpp for the other parameter combinations the four Phase 1 tests actually run.
    struct RunConfig
    {
        uint32 RandomSeed = 12345;
        uint32 StepMs = 10;
        uint32 DurationMs = 30000;
        int32 SpellPower = 0;
        uint32 TargetArmor = 0;
        // Caster's level - RunOnce() only, not yet threaded through RunPlayerbotOnce() (SimBot's
        // PlayerbotFactory-driven spellbook setup would need its own look at level-gating before
        // that's meaningful). Added to test whether a single-rank spell's damage actually scales
        // with caster level under this deployment's custom scaling system (see SpellId's doc
        // comment on why RunOnce() rather than RunPlayerbotOnce() is the right tool for that).
        uint32 ActorLevel = 80;
        // Which spell RunOnce()'s hardcoded RotationTick() teaches and casts - defaults to
        // FROSTBOLT_SPELL_ID (Rank 11, 25304) to keep every existing Phase 1 test's expectations
        // unchanged. Override this to test a specific spell id directly, bypassing whatever
        // spellbook/rank-availability rules a real character or PlayerbotFactory would apply -
        // e.g. spell 116 ("Frostbolt", no rank suffix, SpellLevel/BaseLevel 4, MaxLevel 80) is this
        // deployment's sole surviving Frostbolt rank post-migration to a single-rank spell system;
        // the higher-rank rows (7322/10179/10180/10181/25304) still exist in spell_dbc but are no
        // longer taught, so testing "does the live spell scale with caster level" means testing 116
        // specifically, not the constant below.
        uint32 SpellId = FROSTBOLT_SPELL_ID;
        // Paces the loop to real wall-clock time (sleeps StepMs of real time per tick) instead of
        // running flat-out. Only meant for the accelerated-clock test (SimTests.cpp), which needs
        // an actual real-time-paced run to compare against an accelerated one. Never use this for
        // anything else: at a 10ms step it makes a 30s sim job take 30 real seconds.
        bool RealTimePaced = false;
    };

    // One sim job's result. HitDamages/HitCrits are parallel vectors, one entry per landed hit, in
    // landing order - see EventRecorder's doc comment for why total damage and crit info come
    // from two different hooks and how RunOnce() correlates them back into per-hit pairs.
    struct RunResult
    {
        bool Success = false;
        uint32 ElapsedMs = 0;
        uint32 CastAttempts = 0;
        uint64 TotalDamage = 0;
        uint32 CastCount = 0;
        uint32 CritCount = 0;
        std::vector<uint32> HitDamages;
        std::vector<bool> HitCrits;
        std::vector<uint32> HitSpellIds;
    };

    // Runs one sim job per `config` and fills `result`. Returns false (result.Success also false)
    // if actor/target construction failed - check LOG_ERROR output for why rather than assuming a
    // false return means the hardcoded rotation itself is broken.
    bool RunOnce(RunConfig const& config, RunResult& result);

    // Phase 2 (M2a) version of RunOnce(): same actor/target/clock setup, but drives a real
    // mod-playerbots Engine/Strategy (via SimBot) each tick instead of the hardcoded Frostbolt-only
    // RotationTick(). Reuses RunConfig/RunResult unchanged - neither struct had anything
    // Frostbolt-specific in it. See SimBot.h for what strategy ends up driving the actor (an
    // untalented mage defaults to Frost) and why a manual "pull" cast is needed to bootstrap combat.
    bool RunPlayerbotOnce(RunConfig const& config, RunResult& result);

    // Runs the M1 smoke-test job (RunConfig{} defaults) and logs a human-readable summary. This is
    // what DpsSimWorldScript::OnDpsSimRun() calls by default (DpsSim.Enabled=1 alone) - see
    // DpsSim.cpp. SimTests::RunAll() (DpsSim.RunTests=1 too) is the test-suite entry point.
    void Run();

    // Runs one RunPlayerbotOnce() job (RunConfig{} defaults) and logs a human-readable summary,
    // including a per-hit spell-id/damage/crit breakdown so a human can see the real rotation in
    // action rather than trusting the aggregate alone. DpsSim.RunPlayerbot=1 - see DpsSim.cpp.
    void RunPlayerbot();

    // One-off diagnostic (not part of the M1/M2a milestones): runs RunOnce() twice, back to back,
    // with everything held constant except RunConfig::ActorLevel, and logs both runs' per-hit
    // damage so a human can see directly whether this deployment's single-rank spell system
    // actually scales a spell's damage with the caster's level (as opposed to relying on the old
    // per-level rank spells, which this deployment has moved away from - see RunConfig::SpellId's
    // doc comment). DpsSim.RunLevelCheck=1 - see DpsSim.cpp. Candidate for deletion or promotion to
    // a permanent, parameterized test once this specific question is answered - ask before either.
    void RunLevelScalingCheck();
}

#endif
