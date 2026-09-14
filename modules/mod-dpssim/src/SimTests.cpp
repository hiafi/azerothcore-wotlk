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

#include "SimTests.h"
#include "Log.h"
#include "SimDaemon.h"
#include "StringFormat.h"
#include <algorithm>
#include <cmath>

namespace
{
    // ---- Known-value test derivation (2026-09-11 - see the plan doc's session handoff for the
    // full research trail behind every constant below; nothing here is guessed) ----
    //
    // Scenario: unbuffed level-80 Troll Mage (SimDaemon::RunConfig's own default actor) vs. a
    // level-80 zero-armor/zero-resist target - exactly what the plan doc's known-value test bullet
    // asks for.
    //
    // Intellect/Spirit at level 80: this fork replaced stock AC's player_levelstats with its own
    // player_race_stats + player_class_stats tables (the custom Int/Spirit-spellpower system - see
    // ObjectMgr::LoadPlayerInfo()). Queried directly from this deployment's DB, not assumed:
    //   player_class_stats:  Mage(8)  L80  Intellect=181  Spirit=174
    //   player_race_stats:   Troll(8)      Intellect=-4   Spirit=+1
    // Player::GiveLevel() -> SetCreateStat() sums them directly (ObjectMgr::LoadPlayerInfo():
    // `levelInfo.stats[i] = class_stats[i] + raceStatModifiers[race][i]`), and with zero gear/buffs
    // Unit::GetStat() reads that sum straight back.
    constexpr float TROLL_MAGE_INTELLECT_L80 = 181.0f + (-4.0f); // = 177
    constexpr float TROLL_MAGE_SPIRIT_L80 = 174.0f + 1.0f;       // = 175

    // Frostbolt Rank 11 (spell_dbc id SimDaemon::FROSTBOLT_SPELL_ID) - queried directly from this
    // deployment's spell_dbc/spell_bonus_data tables:
    //   Effects[1] (SPELL_EFFECT_SCHOOL_DAMAGE): BasePoints=514, DieSides=41, RealPointsPerLevel=0
    //   spell_bonus_data.direct_bonus (spell power coefficient) = 0.857 - the historical Blizzard
    //     value for a 3.0s-cast direct-damage nuke; confirmed this fork's own custom balance work
    //     didn't touch it (those changes target DoTs specifically - see the plan doc's git-log
    //     note about haste/crit-scaling dots).
    //   SpellLevel=60, MaxLevel=64 - MaxLevel > SpellLevel means Unit::CalculateLevelPenalty()
    //     does *not* early-return 1.0f (that only happens when SpellLevel >= MaxLevel) and instead
    //     computes a real one: LvlFactor = (SpellLevel+6)/CasterLevel = 66/80 = 0.825, LvlPenalty=0
    //     (SpellLevel is not < 20). A level-80 caster on this MaxLevel-64 spell really does eat a
    //     ~17.5% coefficient penalty - not obvious going in, worth remembering if this ever looks
    //     like a bug later.
    //
    // SpellEffectInfo::CalcValue()'s dice roll (patch-3.3.3 semantics: range is [1, DieSides]) puts
    // the pre-spellpower base value at BasePoints + roll, i.e. [515, 555].
    constexpr float FROSTBOLT_BASE_MIN = 514.0f + 1.0f;
    constexpr float FROSTBOLT_BASE_MAX = 514.0f + 41.0f;
    constexpr float FROSTBOLT_COEFF = 0.857f;
    constexpr float FROSTBOLT_LEVEL_PENALTY = 66.0f / 80.0f;

    // Frostbolt's cast time is 3.0s (unmodified in this fork, 0 haste on a bare actor) - well
    // above the 1.5s GCD, so cast time (not GCD) is what paces the rotation. Confirmed against
    // every observed live-boot run this session: 30000ms / 3000ms = 10 casts, matching exactly.
    constexpr uint32 FROSTBOLT_CAST_TIME_MS = 3000;

    // Unit::SpellDamageBonusDone()'s formula, replicated here with the same int32-truncation order
    // the engine uses (Unit.cpp, near "Check for table values" at the time of writing):
    //   DoneAdvertisedBenefit = int32(Int/2) + int32(Spirit/2)          [SpellBaseDamageBonusDone]
    //   DoneTotal = int32(DoneAdvertisedBenefit * coeff * levelPenalty)
    //   damage = pdamage + DoneTotal   [DoneTotalMod ~= 1.0: no % damage auras on a bare actor]
    // A zero-armor, zero-resist, level-matched target adds no further mitigation on top of this -
    // see SimTarget.h and the plan doc for why boss-mode hit/dodge/parry doesn't need modelling
    // here either.
    int32 ExpectedNonCritDamage(float baseDamage)
    {
        int32 const doneAdvertisedBenefit = int32(TROLL_MAGE_INTELLECT_L80 / 2.0f) + int32(TROLL_MAGE_SPIRIT_L80 / 2.0f);
        int32 const doneTotal = int32(float(doneAdvertisedBenefit) * FROSTBOLT_COEFF * FROSTBOLT_LEVEL_PENALTY);
        return int32(baseDamage) + doneTotal;
    }

    void LogVerdict(char const* testName, bool passed, std::string const& detail)
    {
        if (passed)
            LOG_INFO("server.dpssim", "mod-dpssim: [PASS] {} - {}", testName, detail);
        else
            LOG_ERROR("server.dpssim", "mod-dpssim: [FAIL] {} - {}", testName, detail);
    }

    bool WithinPct(uint64 a, uint64 b, double pct)
    {
        if (a == 0 && b == 0)
            return true;
        double const diff = std::abs(double(a) - double(b));
        double const base = std::max(double(a), double(b));
        return base > 0.0 && (diff / base) <= pct;
    }

    // Test 1/3: unbuffed Frostbolt vs. a zero-armor level-80 target, hand-computed expected
    // damage compared to sim output - every landed hit is checked individually against a
    // hand-derived bound (see the constants above), not just the aggregate total: a compensating
    // pair of bugs (e.g. wrong cast time and wrong per-hit damage) can land on the right total DPS
    // by accident, which is exactly what this bullet in the plan doc warns against.
    bool RunKnownValueTest()
    {
        SimDaemon::RunConfig config;
        config.StepMs = 10;
        config.DurationMs = 60000; // longer than the smoke-test default - more samples to check
        config.SpellPower = 0;
        config.TargetArmor = 0;

        SimDaemon::RunResult result;
        if (!SimDaemon::RunOnce(config, result))
        {
            LogVerdict("known-value test", false, "RunOnce() failed - see preceding LOG_ERROR output.");
            return false;
        }

        int32 const nonCritMin = ExpectedNonCritDamage(FROSTBOLT_BASE_MIN);
        int32 const nonCritMax = ExpectedNonCritDamage(FROSTBOLT_BASE_MAX);
        // Small margin on the non-crit bound for the one thing not traced to certainty in the
        // derivation above (partial-resist mitigation against a 0-resistance, level-matched
        // target should be ~0, but wasn't independently verified roll-by-roll) - not a margin for
        // being wrong about the formula itself.
        int32 const nonCritMinTol = int32(float(nonCritMin) * 0.95f);
        int32 const nonCritMaxTol = int32(float(nonCritMax) * 1.05f);

        if (result.HitDamages.size() != result.HitCrits.size())
        {
            LogVerdict("known-value test", false, Acore::StringFormat(
                "HitDamages ({}) and HitCrits ({}) sizes disagree - EventRecorder's per-hit vectors (see its class doc comment) are out of sync.",
                result.HitDamages.size(), result.HitCrits.size()));
            return false;
        }

        uint32 violations = 0;
        for (size_t i = 0; i < result.HitDamages.size(); ++i)
        {
            uint32 const dmg = result.HitDamages[i];
            bool const crit = result.HitCrits[i];
            // Crit bound is deliberately loose (>max, <=3x max) - the exact crit multiplier
            // wasn't independently re-derived this session (see the plan doc's non-determinism
            // note for what's still open), so this only catches a badly broken crit path, not a
            // precisely wrong multiplier.
            bool const ok = crit
                ? (int32(dmg) > nonCritMaxTol && int32(dmg) <= nonCritMaxTol * 3)
                : (int32(dmg) >= nonCritMinTol && int32(dmg) <= nonCritMaxTol);
            if (!ok)
            {
                ++violations;
                LOG_ERROR("server.dpssim", "mod-dpssim: known-value test - hit #{} damage {} ({}) outside expected bounds (non-crit [{},{}]).",
                    i, dmg, crit ? "crit" : "non-crit", nonCritMinTol, nonCritMaxTol);
            }
        }

        // +1 allows for the tail-end partial cast SimDaemon::Run()'s own log comment describes.
        uint32 const expectedCasts = config.DurationMs / FROSTBOLT_CAST_TIME_MS;
        bool const castCountOk = result.CastCount + 1 >= expectedCasts && result.CastCount <= expectedCasts;

        bool const passed = violations == 0 && castCountOk && !result.HitDamages.empty();
        LogVerdict("known-value test", passed, Acore::StringFormat(
            "{} hits checked ({} outside bounds), expected non-crit range [{},{}] (tolerance [{},{}]), {} casts observed (expected ~{}), {} total damage.",
            result.HitDamages.size(), violations, nonCritMin, nonCritMax, nonCritMinTol, nonCritMaxTol,
            result.CastCount, expectedCasts, result.TotalDamage));
        return passed;
    }

    // Test 2/3: run the identical job at 10ms/50ms/1ms steps, confirm agreement - the correctness
    // oracle for picking 10ms as the default step (design doc section 5.4).
    bool RunTimestepTest()
    {
        SimDaemon::RunConfig config;
        config.DurationMs = 30000;
        config.SpellPower = 0;
        config.TargetArmor = 0;

        config.StepMs = 10;
        SimDaemon::RunResult r10;
        bool const ok10 = SimDaemon::RunOnce(config, r10);

        config.StepMs = 50;
        SimDaemon::RunResult r50;
        bool const ok50 = SimDaemon::RunOnce(config, r50);

        config.StepMs = 1;
        SimDaemon::RunResult r1;
        bool const ok1 = SimDaemon::RunOnce(config, r1);

        if (!ok10 || !ok50 || !ok1)
        {
            LogVerdict("timestep test", false, "one or more RunOnce() calls failed - see preceding LOG_ERROR output.");
            return false;
        }

        bool const castCountsAgree = r10.CastCount == r50.CastCount && r10.CastCount == r1.CastCount;
        bool const damageAgrees = WithinPct(r10.TotalDamage, r50.TotalDamage, 0.05) && WithinPct(r10.TotalDamage, r1.TotalDamage, 0.05);

        bool const passed = castCountsAgree && damageAgrees;
        LogVerdict("timestep test", passed, Acore::StringFormat(
            "10ms: {} casts/{} dmg, 50ms: {} casts/{} dmg, 1ms: {} casts/{} dmg (cast counts {}, damage within 5% {}).",
            r10.CastCount, r10.TotalDamage, r50.CastCount, r50.TotalDamage, r1.CastCount, r1.TotalDamage,
            castCountsAgree ? "agree" : "DISAGREE", damageAgrees ? "yes" : "NO"));
        return passed;
    }

    // Test 3/3: run the identical job at real wall-clock pace and at accelerated (flat-out) pace,
    // confirm identical cast count - the test that actually proves core patch 2's getMSTime()
    // override works, per the plan doc's "Critical finding" section: GCD/cast-time gating is
    // exactly the mechanism that silently breaks under acceleration if the patch is wrong.
    bool RunAcceleratedClockTest()
    {
        SimDaemon::RunConfig config;
        config.StepMs = 10;
        config.DurationMs = 5000; // kept short - RealTimePaced actually sleeps this many real ms

        config.RealTimePaced = false;
        SimDaemon::RunResult accelerated;
        bool const okAccel = SimDaemon::RunOnce(config, accelerated);

        config.RealTimePaced = true;
        SimDaemon::RunResult realTime;
        bool const okReal = SimDaemon::RunOnce(config, realTime);

        if (!okAccel || !okReal)
        {
            LogVerdict("accelerated-clock test", false, "one or more RunOnce() calls failed - see preceding LOG_ERROR output.");
            return false;
        }

        bool const passed = accelerated.CastCount == realTime.CastCount;
        LogVerdict("accelerated-clock test", passed, Acore::StringFormat(
            "accelerated (no sleep): {} casts/{} dmg, real-time-paced ({}ms of actual sleep): {} casts/{} dmg.",
            accelerated.CastCount, accelerated.TotalDamage, config.DurationMs, realTime.CastCount, realTime.TotalDamage));
        return passed;
    }
}

void SimTests::RunAll()
{
    LOG_INFO("server.dpssim", "mod-dpssim: SimTests::RunAll() - running Phase 1's three required tests.");

    uint32 passed = 0;
    passed += RunKnownValueTest() ? 1 : 0;
    passed += RunTimestepTest() ? 1 : 0;
    passed += RunAcceleratedClockTest() ? 1 : 0;

    LOG_INFO("server.dpssim", "mod-dpssim: SimTests::RunAll() complete - {}/3 tests passed.", passed);
}
