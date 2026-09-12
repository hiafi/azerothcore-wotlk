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
#include "ObjectGuid.h"
#include <map>
#include <string>
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

    // Spell 116 ("Frostbolt", no rank suffix, SpellLevel/BaseLevel 4, MaxLevel 80) - this
    // deployment's sole surviving Frostbolt rank after migrating to a single-rank spell system.
    // The higher-rank rows (7322/10179/10180/10181/FROSTBOLT_SPELL_ID above) still exist in
    // spell_dbc but are no longer taught to real characters, so this - not the constant above - is
    // what both a real player and PlayerbotFactory-driven bot actually cast. Used as
    // RunConfig::SpellId's real-world override (RunOnce()) and as SimBot's own pull spell
    // (RunPlayerbotOnce(), via SimBot.cpp) - keeping the bootstrap pull on the same spell as the
    // rest of the rotation avoids mixing an old-scaling data point into a run's per-hit output.
    constexpr uint32 SINGLE_RANK_FROSTBOLT_SPELL_ID = 116;

    // One sim job's parameters. Defaults match the M1 smoke-test job Run() has always used
    // (level-80 Troll Mage, unbuffed, vs. a level-80 zero-armor target, 30s at a 10ms step) - see
    // SimTests.cpp for the other parameter combinations the four Phase 1 tests actually run.
    struct RunConfig
    {
        uint32 RandomSeed = 12345;
        uint32 StepMs = 10;
        uint32 DurationMs = 30000;
        // Flat spell power added on top of the level/race/gear baseline - see
        // SimActor::Config::SpellPower's own doc comment for the mechanism
        // (Player::ApplySpellPowerBonus()). Both RunOnce() and RunPlayerbotOnce() honor this.
        // Comes from a loaded DpsSim.Profile's own SpellPower key when one is set (see
        // SimProfile.h) - there is no flat conf-key equivalent for the RunPlayerbot path, only
        // RunOnce()'s own test-authored values (SimTests.cpp) and profiles set this.
        int32 SpellPower = 0;
        uint32 TargetArmor = 0;
        // Caster's level - both RunOnce() and RunPlayerbotOnce() honor this. Added to test whether
        // a single-rank spell's damage actually scales with caster level under this deployment's
        // custom scaling system (see SpellId's doc comment on why RunOnce() alone was the right
        // tool for the original scaling question); threaded through RunPlayerbotOnce() too so the
        // real Engine/Strategy-driven rotation can be exercised at a specific bracket (60/70/80 -
        // see SimTarget::EntryForLevel()), not only at level 80.
        uint32 ActorLevel = 80;
        // Target dummy's level - see SimTarget::EntryForLevel() for how this picks one of the
        // three dedicated dummy entries (900001/900002/900003 for 60/70/80). Independent of
        // ActorLevel so a caller can deliberately test a level gap; the common case (testing "this
        // bracket's own rotation against this bracket's own dummy") sets both to the same value.
        uint32 TargetLevel = 80;
        // Actor's race (a RACE_* constant from SharedDefines.h). Both RunOnce() and
        // RunPlayerbotOnce() pass this straight through to SimActor::CreateInfo::Race - see that
        // field's own doc comment for why this matters beyond cosmetics: racials are real,
        // always-on passives that land in EventRecorder's aura-event stream and in the rotation
        // itself (e.g. RACE_TROLL's Berserking, a self-cast haste proc most Frost mage builds
        // would never have). Defaults to RACE_HUMAN - a mage has no race-locked spec reason to be
        // anything else, and Human carries no racial that touches damage/haste/spellpower, making
        // it the least surprising default for "what does the rotation alone look like." Confirmed
        // live (2026-09-11): the M2a harness had defaulted to RACE_TROLL since Phase 1's original
        // smoke-test job and carried that unnoticed into every Phase 2 run - Troll's Berserking
        // (spell 26297, a 10s self-haste proc on a long cooldown) was firing mid-run and is the
        // actual explanation for a cast-cadence shift (1.26s -> 1.58s) an earlier report flagged
        // as an unidentified buff. Override to test a specific race/class combo deliberately;
        // SimActor::Create() still rejects an invalid race/class pairing the same way it always
        // has (see CharacterCreateInfo's own validation).
        uint8 ActorRace = 1 /* RACE_HUMAN */;
        // Actor's class (a CLASS_* constant from SharedDefines.h). Only RunPlayerbotOnce() honors
        // this today - RunOnce()'s hardcoded RotationTick() always builds a mage regardless, since
        // it casts one fixed SpellId rather than running a real class Strategy. Comes from
        // DpsSim.Profile when set (see SimProfile.h) - a bare DpsSim.PlayerbotTalents-only setup
        // has no way to say "this is an Arcane build vs. a Frost build" since both are still
        // CLASS_MAGE either way, but a genuinely different class needs this. Note: SimBot's
        // pull-spell bootstrap (SimBot.cpp's PULL_SPELL_ID) is currently hardcoded to a mage-only
        // spell (Frostbolt) regardless of this field, so a non-mage class will fail at the pull
        // cast until that's revisited - fine for today's mage-only profiles, not yet general.
        uint8 ActorClass = 8 /* CLASS_MAGE */;
        // Positional talent string SimBot::Create() spends on the actor - see
        // DpsSim.PlayerbotTalents' own conf doc comment for the format. Comes from DpsSim.Profile
        // when set, otherwise straight from that flat conf key (DpsSim.cpp reads whichever applies
        // before calling RunPlayerbot()) - RunConfig itself doesn't care which source it came from.
        std::string PlayerbotTalents;
        // Real item ids to equip on the actor, and synthetic combat-rating top-ups on top of
        // them - see SimProfile.h's Profile::GearItemIds/CombatRatings for the full doc comment
        // on both (this is a direct, unmodified copy of a loaded profile's values; RunConfig
        // itself has no opinion on where they came from, same as PlayerbotTalents above). No flat
        // conf-key equivalent exists - gear/stats only come from a profile today.
        std::vector<uint32> GearItemIds;
        std::map<uint8, int32> CombatRatings;
        // Synthetic core-stat top-ups (Strength/Agility/Stamina/Intellect/Spirit) and flat attack
        // power - see SimProfile.h's Profile::Stats/AttackPower for the full doc comment on both.
        // Same sourcing as GearItemIds/CombatRatings above: a direct copy of a loaded profile's
        // values, no flat conf-key equivalent.
        std::map<uint8, float> Stats;
        int32 AttackPower = 0;
        // Which spell RunOnce()'s hardcoded RotationTick() teaches and casts - defaults to
        // FROSTBOLT_SPELL_ID (Rank 11, 25304) to keep every existing Phase 1 test's expectations
        // unchanged. Override this (SINGLE_RANK_FROSTBOLT_SPELL_ID above, typically) to test a
        // specific spell id directly, bypassing whatever spellbook/rank-availability rules a real
        // character or PlayerbotFactory would apply. Not used by RunPlayerbotOnce() - the real
        // Engine/Strategy decides its own spells; SimBot's own pull spell is a separate, hardcoded
        // choice (SimBot.cpp), not this field.
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

        // Per-hit sim-clock timestamp, parallel to HitDamages/HitCrits/HitSpellIds - see
        // EventRecorder::GetHitTimestamps()'s doc comment.
        std::vector<uint32> HitTimestamps;

        // One entry per aura the actor or target gained/lost during the run - a deliberately
        // separate, decoupled copy of EventRecorder::AuraEvent's fields rather than reusing that
        // type directly, so this header doesn't need to pull in EventRecorder.h (and therefore
        // ScriptMgr.h) just to describe a result struct. See EventRecorder::GetAuraEvents()'s doc
        // comment for what each field means.
        struct AuraEvent
        {
            uint32 TimestampMs = 0;
            ObjectGuid UnitGuid;
            bool IsActor = false;
            uint32 SpellId = 0;
            uint8 StackAmount = 0;
            bool Positive = false;
            bool Applied = false;
        };
        std::vector<AuraEvent> AuraEvents;
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

    // Runs one RunPlayerbotOnce() job and logs a human-readable summary, including a per-hit
    // spell-id/damage/crit breakdown so a human can see the real rotation in action rather than
    // trusting the aggregate alone. `config` defaults to RunConfig{} (level 80 vs. level 80) -
    // DpsSim.cpp passes ActorLevel/TargetLevel from DpsSim.PlayerbotLevel when set.
    // DpsSim.RunPlayerbot=1 - see DpsSim.cpp.
    void RunPlayerbot(RunConfig const& config = RunConfig{});

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
