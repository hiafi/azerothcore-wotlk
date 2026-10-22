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
#include "Config.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "Player.h"
#include "QueryResult.h"
#include "SimActor.h"
#include "SimDaemon.h"
#include "SimHeal.h"
#include "SimProfile.h"
#include "SimTank.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "Util.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <functional>
#include <map>
#include <string>
#include <vector>

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
    //   SpellLevel=60, MaxLevel=64 - stock Unit::CalculateLevelPenalty() would scale the
    //     coefficient by (SpellLevel+6)/CasterLevel = 66/80 = 0.825 here (the downranking
    //     penalty). This fork disables that penalty (single-rank spells: every class spell keeps
    //     rank 1's SpellLevel, so it cut nearly all player spell power scaling at 80 - see
    //     docs/bugs-and-fixes.md), so the factor is 1.0. If this test starts failing low by ~17.5%,
    //     the penalty has come back (e.g. lost in an upstream merge).
    //
    // SpellEffectInfo::CalcValue()'s dice roll (patch-3.3.3 semantics: range is [1, DieSides]) puts
    // the pre-spellpower base value at BasePoints + roll, i.e. [515, 555].
    constexpr float FROSTBOLT_BASE_MIN = 514.0f + 1.0f;
    constexpr float FROSTBOLT_BASE_MAX = 514.0f + 41.0f;
    constexpr float FROSTBOLT_COEFF = 0.857f;
    constexpr float FROSTBOLT_LEVEL_PENALTY = 1.0f;

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

    // Test 4/4: a sim actor never persists. 20 simulated minutes is past the stock 15-minute PlayerSaveInterval, the
    // threshold that made the old actor autosave orphan rows into the live characters DB. Safe even if the fix
    // regresses: the sim only runs against a throwaway characters schema (OnDpsSimRun refuses the live one).
    bool RunNoPersistTest()
    {
        SimDaemon::RunConfig config;
        config.StepMs = 1000;
        config.DurationMs = 20 * 60 * 1000;
        config.SpellPower = 0;
        config.TargetArmor = 0;

        uint32 const savesBefore = SimActor::GetSaveAttempts();
        SimDaemon::RunResult result;
        if (!SimDaemon::RunOnce(config, result))
        {
            LogVerdict("no-persist test", false, "RunOnce() failed - see preceding LOG_ERROR output.");
            return false;
        }
        uint32 const saves = SimActor::GetSaveAttempts() - savesBefore;

        // Everything under the reserved block once the actor is gone: must be zero (nothing may have saved it).
        uint64 leftovers = 0;
        for (char const* table : {"characters", "character_talent", "character_spell", "character_action",
                "character_skills", "character_aura", "character_inventory", "character_stats"})
        {
            if (QueryResult rows = CharacterDatabase.Query("SELECT COUNT(*) FROM `{}` WHERE `guid` >= {}",
                    table, SimActor::SIM_GUID_BASE))
                leftovers += rows->Fetch()[0].Get<uint64>();
        }
        if (QueryResult rows = CharacterDatabase.Query("SELECT COUNT(*) FROM `item_instance` WHERE `owner_guid` >= {}",
                SimActor::SIM_GUID_BASE))
            leftovers += rows->Fetch()[0].Get<uint64>();

        bool const passed = saves == 0 && leftovers == 0;
        LogVerdict("no-persist test", passed, Acore::StringFormat(
            "{}s simulated, {} SaveToDB() call(s) on the sim actor (expected 0), "
            "{} row(s) in the reserved guid block (expected 0).",
            config.DurationMs / 1000, saves, leftovers));
        return passed;
    }

    // ---- Healing-sim known-value tests (stage HS3; plan .agents/plans/healing-sim/healing-sim.PLAN.md) ----
    //
    // Each test runs a real heal-mode batch (SimDaemon::RunPlayerbotBatch(), one 5-man group of headless allies, the
    // Sim Raid Boss, the real damage drivers and the real recorders) with one change: RunConfig::HealStepHook replaces
    // the healer's bot AI, so the healer casts exactly what the test script says and nothing else. The healer is an
    // unglyphed, untalented, ungeared level-60 Human Priest with its mana refilled every step (InfiniteMana) and no
    // pre-pull buff phase, so no talent, gear or buff modifies a number; the expected values below come from the spell
    // data and the actor's own stats, never from a previous run.
    //
    // The target of the heals is ally 1, an untalented Rogue: it has no armor-style mitigation of magic damage, no
    // healing-taken aura and no absorb, and (pinned at 50% of a 30,000 pool) a heal lands without overheal.

    constexpr uint32 SPELL_GREATER_HEAL = 2060;
    constexpr uint32 SPELL_FLASH_HEAL = 2061;
    constexpr uint32 SPELL_RENEW = 139;
    constexpr uint32 SPELL_POWER_WORD_SHIELD = 17;

    constexpr uint32 HEAL_TEST_STEP_MS = 100;
    constexpr size_t HEAL_TEST_ALLY = 1;
    constexpr char const* HEAL_TEST_PIN_PARTY = "tank:pin:50, 3*dps:pin:50, self:pin:50";

    using HealStepHook = std::function<void(uint32, Player*, std::vector<Player*> const&)>;

    // Runs one heal-mode iteration of `durationMs` for the Priest above. `allyMaxHealthDps` is the max health of a
    // drain-mode DPS ally (a pinned target has the profile default of 30,000).
    bool RunHealScenario(char const* targetsText, uint32 durationMs, HealStepHook hook, SimDaemon::RunResult& result,
        uint32 allyMaxHealthDps = 5000)
    {
        SimDaemon::RunConfig config;
        config.RunMode = SimDaemon::Mode::Heal;
        config.StepMs = HEAL_TEST_STEP_MS;
        config.DurationMs = durationMs;
        config.ActorLevel = 60;
        config.TargetLevel = 60;
        config.ActorRace = 1 /* RACE_HUMAN */;
        config.ActorClass = CLASS_PRIEST;
        config.PlayerbotGlyphs = false;
        config.PrePullBuffMs = 0;
        config.InfiniteMana = true;
        config.HealGroupSize = SimHeal::PARTY_SIZE;
        config.AllyMaxHealthDps = allyMaxHealthDps;
        config.AllyTankTalents = SimProfile::Profile{}.AllyTankTalents;

        std::string error;
        if (!SimHeal::ParseTargets(targetsText, config.HealTargets, error) ||
            !SimHeal::Validate(config.HealGroupSize, config.HealTargets, error))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: heal test - the target list '{}' is invalid: {}", targetsText,
                error);
            return false;
        }

        config.HealStepHook = std::move(hook);

        std::vector<SimDaemon::RunResult> results;
        if (!SimDaemon::RunPlayerbotBatch(config, 1, results) || results.size() != 1 || !results[0].Success)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: heal test - RunPlayerbotBatch() failed - see preceding LOG_ERROR "
                "output.");
            return false;
        }

        result = std::move(results[0]);
        return true;
    }

    // The healer knows the spell: PlayerbotFactory::InitAvailableSpells() already taught the trainer spells, this is
    // only a guard against a rank the trainer does not list
    void EnsureSpell(Player* healer, uint32 spellId)
    {
        if (!healer->HasSpell(spellId))
            healer->learnSpell(spellId);
    }

    // The healer's spell power as Unit::SpellBaseHealingBonusDone() builds it for a Player with no healing aura:
    // flat spell power and healing, plus this fork's half a point per point of Intellect and of Spirit (the same
    // int32 truncations as the engine)
    int32 HealingPowerOf(Player* healer)
    {
        return int32(healer->GetBaseSpellPowerBonus()) + int32(healer->GetBaseSpellHealingBonus()) +
            int32(healer->GetStat(STAT_INTELLECT) / 2) + int32(healer->GetStat(STAT_SPIRIT) / 2);
    }

    // Unit::SpellHealingBonusDone() for a healer with no healing-done aura, replicated with the engine's order of
    // operations: base + int32(power * coefficient * level penalty), then the done and taken percent modifiers, which
    // are 1.0 for the unbuffed healer and an unbuffed Rogue target. The coefficient is the spell_bonus_data row when
    // there is one (it wins over the effect's own BonusMultiplier, as in the engine); the level penalty is this fork's
    // 1.0 (see the damage known-value test above).
    int32 ExpectedHealAmount(Player* healer, SpellInfo const* info, uint8 effIndex, int32 baseValue)
    {
        float coeff = info->Effects[effIndex].BonusMultiplier;
        if (SpellBonusEntry const* bonus = sSpellMgr->GetSpellBonusData(info->Id))
            coeff = bonus->direct_damage;

        // The spell mod hook of the engine multiplies and divides by 100 even with no mod, which is exact for the
        // coefficients of this data; do the same so float rounding cannot differ
        coeff *= 100.0f;
        coeff /= 100.0f;

        int32 const power = HealingPowerOf(healer);
        float const levelPenalty = 1.0f;
        return baseValue + int32(float(power) * coeff * levelPenalty);
    }

    // Heal test 1/6 (heal-flash): Flash Heal on a pinned ally. Six casts (the first at 1 s, then one every 4 s) on the
    // Rogue pinned at 50%; every recorded heal must equal the formula's amount, or its critical amount (the amount plus
    // half of it, Unit::SpellCriticalHealingBonus() for a magic-class spell), with no overheal and no absorb.
    bool RunHealFlashHealTest()
    {
        struct State
        {
            uint32 NextCastMs = 1000;
            uint32 Casts = 0;
            uint32 Failures = 0;
            SpellCastResult LastFailure = SPELL_CAST_OK;
            bool Captured = false;
            int32 BaseValue = 0;
            float Coefficient = 0.0f;
            int32 Power = 0;
            int32 Expected = 0;
            uint32 EngineDone = 0;
            uint32 EngineTaken = 0;
        } state;
        constexpr uint32 CASTS = 6;

        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_FLASH_HEAL);
        if (!info)
        {
            LogVerdict("heal-flash test", false, "Flash Heal (2061) is not in spell_dbc.");
            return false;
        }

        auto const hook = [&](uint32 elapsedMs, Player* healer, std::vector<Player*> const& members)
        {
            EnsureSpell(healer, SPELL_FLASH_HEAL);
            if (state.Casts >= CASTS || elapsedMs < state.NextCastMs || healer->IsNonMeleeSpellCast(false))
                return;

            Player* target = members[HEAL_TEST_ALLY];
            if (!state.Captured)
            {
                state.Captured = true;
                state.BaseValue = info->Effects[EFFECT_0].CalcValue(healer, nullptr, target);
                state.Coefficient = info->Effects[EFFECT_0].BonusMultiplier;
                state.Power = HealingPowerOf(healer);
                state.Expected = ExpectedHealAmount(healer, info, EFFECT_0, state.BaseValue);
                // The engine's own answer for the same inputs, logged beside the replicated one to localise a
                // disagreement (the verdict uses the replicated formula only)
                state.EngineDone = healer->SpellHealingBonusDone(target, info, uint32(std::max(state.BaseValue, 0)),
                    HEAL, EFFECT_0);
                state.EngineTaken = target->SpellHealingBonusTaken(healer, info, state.EngineDone, HEAL);
            }

            SpellCastResult const castResult = healer->CastSpell(target, SPELL_FLASH_HEAL, false);
            if (castResult == SPELL_CAST_OK)
            {
                ++state.Casts;
                state.NextCastMs = elapsedMs + 4000;
            }
            else
            {
                ++state.Failures;
                state.LastFailure = castResult;
                state.NextCastMs = elapsedMs + 1000;
            }
        };

        SimDaemon::RunResult result;
        if (!RunHealScenario(HEAL_TEST_PIN_PARTY, 30000, hook, result))
        {
            LogVerdict("heal-flash test", false, "the heal scenario did not run - see preceding LOG_ERROR output.");
            return false;
        }

        uint32 events = 0;
        uint32 crits = 0;
        uint32 violations = 0;
        uint32 overheal = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            if (e.SpellId != SPELL_FLASH_HEAL)
                continue;

            ++events;
            crits += e.Crit ? 1 : 0;
            overheal += e.Overheal;
            uint32 const expected = uint32(std::max(state.Expected, 0));
            uint32 const expectedRaw = e.Crit ? expected + expected / 2 : expected;
            bool const ok = !e.Periodic && !e.IsPet && e.TargetIndex == HEAL_TEST_ALLY && e.Raw == expectedRaw &&
                e.Effective == expectedRaw && e.Overheal == 0 && e.HealAbsorbed == 0;
            if (!ok)
            {
                ++violations;
                LOG_ERROR("server.dpssim", "mod-dpssim: heal-flash test - heal at {} ms on #{}: raw {}, effective {}, "
                    "overheal {}, absorbed {}, {}, periodic {}, pet {}; expected {} ({}).", e.TimestampMs,
                    uint32(e.TargetIndex), e.Raw, e.Effective, e.Overheal, e.HealAbsorbed, e.Crit ? "crit" : "no crit",
                    e.Periodic, e.IsPet, expectedRaw, e.Crit ? "critical" : "normal");
            }
        }

        bool const passed = state.Casts == CASTS && state.Failures == 0 && events == state.Casts && violations == 0 &&
            overheal == 0;
        LogVerdict("heal-flash test", passed, Acore::StringFormat(
            "{} Flash Heal casts ({} failed, last result {}), {} heal event(s) on the pinned Rogue ({} critical), {} "
            "outside the expected amount, {} overheal. Expected {} per normal heal = base {} + int32({} power * {} "
            "coefficient); the engine's own SpellHealingBonusDone/Taken gave {} / {}.", state.Casts, state.Failures,
            uint32(state.LastFailure), events, crits, violations, overheal, state.Expected, state.BaseValue,
            state.Power, state.Coefficient, state.EngineDone, state.EngineTaken));
        return passed;
    }

    // Heal test 2/6 (heal-drain): no healer at all, a 9,000-health Rogue draining 300 a second. Every pulse is
    // exactly the 300 asked for (the Rogue has no mitigation and no shield), the pulses are 1 s apart, and the death
    // lands on the pulse that takes the last of its health: ceil(max health / 300), which is pulse 30 for 9,000.
    bool RunHealDrainDeathTest()
    {
        constexpr uint32 DRAIN = 300;
        constexpr size_t DRAINED = 1;

        SimDaemon::RunResult result;
        auto const idle = [](uint32, Player*, std::vector<Player*> const&) { };
        if (!RunHealScenario("tank:pin:50, dps:drain:300, 2*dps:pin:50, self:pin:50", 45000, idle, result, 9000))
        {
            LogVerdict("heal-drain test", false, "the heal scenario did not run - see preceding LOG_ERROR output.");
            return false;
        }

        uint32 const maxHealth = result.HealTargetInfo.size() > DRAINED ? result.HealTargetInfo[DRAINED].MaxHealth : 0;
        uint32 const expectedPulses = (maxHealth + DRAIN - 1) / DRAIN;

        std::vector<SimHeal::DamageEvent> pulses;
        uint32 otherDamage = 0;
        for (SimHeal::DamageEvent const& e : result.DamageTakenEvents)
        {
            if (e.TargetIndex == DRAINED)
                pulses.push_back(e);
            else
                ++otherDamage;
        }

        uint32 badAmounts = 0;
        uint32 badSpacing = 0;
        for (size_t i = 0; i < pulses.size(); ++i)
        {
            SimHeal::DamageEvent const& e = pulses[i];
            if (e.Pin || e.Requested != DRAIN || e.Raw != DRAIN || e.Absorbed != 0 || e.Final != DRAIN)
            {
                ++badAmounts;
                LOG_ERROR("server.dpssim", "mod-dpssim: heal-drain test - pulse {} at {} ms: requested {}, raw {}, "
                    "absorbed {}, final {} (expected {} each).", i + 1, e.TimestampMs, e.Requested, e.Raw, e.Absorbed,
                    e.Final, DRAIN);
            }

            if (i > 0)
            {
                uint32 const gap = e.TimestampMs - pulses[i - 1].TimestampMs;
                if (gap + HEAL_TEST_STEP_MS < 1000 || gap > 1000 + HEAL_TEST_STEP_MS)
                    ++badSpacing;
            }
        }

        bool const oneDeath = result.Deaths.size() == 1 && result.Deaths[0].TargetIndex == DRAINED;
        uint32 const deathAtMs = oneDeath ? result.Deaths[0].TimestampMs : 0;
        uint32 const lastPulseMs = pulses.empty() ? 0 : pulses.back().TimestampMs;
        bool const deathOnLastPulse = oneDeath && !pulses.empty() &&
            deathAtMs + HEAL_TEST_STEP_MS >= lastPulseMs && deathAtMs <= lastPulseMs + HEAL_TEST_STEP_MS;

        bool const passed = maxHealth > 0 && pulses.size() == expectedPulses && badAmounts == 0 && badSpacing == 0 &&
            oneDeath && deathOnLastPulse && otherDamage == 0 && result.HealEvents.empty();
        LogVerdict("heal-drain test", passed, Acore::StringFormat(
            "max health {}, {} pulse(s) of {} landed (expected ceil({} / {}) = {}), {} pulse(s) with a wrong amount, "
            "{} with wrong spacing, {} death(s), the death at {} ms against the last pulse at {} ms, {} hit(s) on "
            "the other targets, {} heal event(s).", maxHealth, pulses.size(), DRAIN, maxHealth, DRAIN, expectedPulses,
            badAmounts, badSpacing, result.Deaths.size(), deathAtMs, lastPulseMs, otherDamage,
            result.HealEvents.size()));
        return passed;
    }

    // Heal test 3/6 (heal-shield): Power Word: Shield on a pinned ally. The next Pin Hit uses the whole shield up, so
    // the one recorded absorb is exactly the amount the aura was created with, credited to the priest (the recorder
    // only attributes the healer's shields) and stamped within a step of the cast.
    bool RunHealShieldTest()
    {
        struct State
        {
            bool Cast = false;
            uint32 CastMs = 0;
            SpellCastResult Result = SPELL_CAST_OK;
            int32 Amount = -1;
            uint32 Shields = 0;
        } state;

        auto const hook = [&](uint32 elapsedMs, Player* healer, std::vector<Player*> const& members)
        {
            EnsureSpell(healer, SPELL_POWER_WORD_SHIELD);
            if (state.Cast || elapsedMs < 1000 || healer->IsNonMeleeSpellCast(false))
                return;

            state.Cast = true;
            state.CastMs = elapsedMs;
            Player* target = members[HEAL_TEST_ALLY];
            state.Result = healer->CastSpell(target, SPELL_POWER_WORD_SHIELD, false);

            // An instant cast has applied the aura when CastSpell() returns: what it was created with
            for (AuraEffect const* aurEff : target->GetAuraEffectsByType(SPELL_AURA_SCHOOL_ABSORB))
                if (aurEff->GetId() == SPELL_POWER_WORD_SHIELD && aurEff->GetCasterGUID() == healer->GetGUID())
                {
                    state.Amount = aurEff->GetAmount();
                    ++state.Shields;
                }
        };

        SimDaemon::RunResult result;
        if (!RunHealScenario(HEAL_TEST_PIN_PARTY, 10000, hook, result))
        {
            LogVerdict("heal-shield test", false, "the heal scenario did not run - see preceding LOG_ERROR output.");
            return false;
        }

        uint32 absorbs = 0;
        uint32 recorded = 0;
        uint32 recordedAtMs = 0;
        bool credited = false;
        for (SimHeal::AbsorbEvent const& e : result.AbsorbEvents)
        {
            ++absorbs;
            if (e.SpellId == SPELL_POWER_WORD_SHIELD && e.TargetIndex == HEAL_TEST_ALLY)
            {
                recorded += e.Amount;
                recordedAtMs = e.TimestampMs;
                credited = !e.IsPet;
            }
        }

        bool const withinStep = recordedAtMs + HEAL_TEST_STEP_MS >= state.CastMs &&
            recordedAtMs <= state.CastMs + HEAL_TEST_STEP_MS;
        bool const passed = state.Cast && state.Result == SPELL_CAST_OK && state.Shields == 1 && state.Amount > 0 &&
            absorbs == 1 && recorded == uint32(state.Amount) && credited && withinStep;
        LogVerdict("heal-shield test", passed, Acore::StringFormat(
            "cast at {} ms (result {}), {} shield aura(s) of the priest on the Rogue, created with {}; {} absorb "
            "event(s) recorded, {} absorbed in total on the Rogue at {} ms ({}, credited to the priest: {}).",
            state.CastMs, uint32(state.Result), state.Shields, state.Amount, absorbs, recorded, recordedAtMs,
            withinStep ? "within one step of the cast" : "NOT within one step of the cast",
            credited ? "yes" : "no"));
        return passed;
    }

    // Heal test 4/6 (heal-hot): Renew on a pinned ally. Every tick is a recorded heal with the periodic flag,
    // credited to the priest, on the right target, and there are duration / amplitude of them, one amplitude apart.
    // Each tick's amount is also compared with the formula (logged, not part of the verdict: the periodic amount is
    // not the subject of this test).
    bool RunHealHotTest()
    {
        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_RENEW);
        if (!info || info->Effects[EFFECT_0].Amplitude == 0 || info->GetMaxDuration() <= 0)
        {
            LogVerdict("heal-hot test", false, "Renew (139) is missing or has no periodic effect.");
            return false;
        }

        uint32 const amplitude = info->Effects[EFFECT_0].Amplitude;
        uint32 const duration = uint32(info->GetMaxDuration());
        uint32 const expectedTicks = duration / amplitude;

        struct State
        {
            bool Cast = false;
            uint32 CastMs = 0;
            SpellCastResult Result = SPELL_CAST_OK;
            int32 AuraAmount = -1;
            int32 ExpectedTick = 0;
            uint32 AuraTicks = 0;
        } state;

        auto const hook = [&](uint32 elapsedMs, Player* healer, std::vector<Player*> const& members)
        {
            EnsureSpell(healer, SPELL_RENEW);
            if (state.Cast || elapsedMs < 1000 || healer->IsNonMeleeSpellCast(false))
                return;

            state.Cast = true;
            state.CastMs = elapsedMs;
            Player* target = members[HEAL_TEST_ALLY];
            state.Result = healer->CastSpell(target, SPELL_RENEW, false);
            if (AuraEffect const* aurEff = target->GetAuraEffect(SPELL_RENEW, EFFECT_0, healer->GetGUID()))
            {
                // The aura's amount already holds the healer's spell power (it is added when the aura is created),
                // so a tick heals exactly that, or half as much again when it crits
                state.AuraAmount = aurEff->GetAmount();
                state.AuraTicks = aurEff->GetTotalTicks();
                state.ExpectedTick = state.AuraAmount;
            }
        };

        SimDaemon::RunResult result;
        if (!RunHealScenario(HEAL_TEST_PIN_PARTY, 1000 + duration + 5000, hook, result))
        {
            LogVerdict("heal-hot test", false, "the heal scenario did not run - see preceding LOG_ERROR output.");
            return false;
        }

        uint32 ticks = 0;
        uint32 direct = 0;
        uint32 wrongFlags = 0;
        uint32 badSpacing = 0;
        uint32 tickAmountMismatch = 0;
        uint32 lastTickMs = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            if (e.SpellId != SPELL_RENEW)
                continue;

            if (!e.Periodic)
            {
                ++direct;
                continue;
            }

            if (e.IsPet || e.TargetIndex != HEAL_TEST_ALLY)
                ++wrongFlags;

            if (ticks > 0)
            {
                uint32 const gap = e.TimestampMs - lastTickMs;
                if (gap + HEAL_TEST_STEP_MS < amplitude || gap > amplitude + HEAL_TEST_STEP_MS)
                    ++badSpacing;
            }

            uint32 const expected = uint32(std::max(state.ExpectedTick, 0));
            uint32 const expectedRaw = e.Crit ? expected + expected / 2 : expected;
            if (e.Raw != expectedRaw)
                ++tickAmountMismatch;

            ++ticks;
            lastTickMs = e.TimestampMs;
        }

        bool const passed = state.Cast && state.Result == SPELL_CAST_OK && ticks == expectedTicks && direct == 0 &&
            wrongFlags == 0 && badSpacing == 0;
        LogVerdict("heal-hot test", passed, Acore::StringFormat(
            "Renew cast at {} ms (result {}), duration {} ms / amplitude {} ms = {} tick(s) expected, {} periodic "
            "heal(s) recorded for the priest on the Rogue ({} with a wrong target or owner, {} with wrong spacing), "
            "{} non-periodic heal(s); informational: the aura says {} tick(s) of {}, {} tick(s) off that amount (a "
            "critical tick is half as much again).", state.CastMs, uint32(state.Result), duration, amplitude,
            expectedTicks, ticks, wrongFlags, badSpacing, direct, state.AuraTicks, state.AuraAmount,
            tickAmountMismatch));
        return passed;
    }

    // One Greater Heal cast schedule shared by both runs of the pushback test: a cast starts whenever the healer is
    // idle and `NextMs` has come, up to `MaxCasts` times
    struct PushbackCasts
    {
        std::vector<uint32> StartMs;
        uint32 NextMs = 5000;
        uint32 MaxCasts = 3;
        uint32 Failures = 0;
    };

    struct PushbackOutcome
    {
        uint32 Casts = 0;
        uint32 Windows = 0;
        uint32 WindowsWithHit = 0;
        uint32 OnTime = 0;
        uint32 Delayed = 0;
        std::string Detail;
    };

    // Casts Greater Heal on ally 1 per `casts`, and (when `renewOnSelf`) puts a Renew on the healer so that its own
    // pin target is hit by the driver after every tick
    HealStepHook MakePushbackHook(PushbackCasts& casts, bool renewOnSelf, bool& renewCast)
    {
        return [&casts, renewOnSelf, &renewCast](uint32 elapsedMs, Player* healer, std::vector<Player*> const& members)
        {
            EnsureSpell(healer, SPELL_GREATER_HEAL);
            if (renewOnSelf)
                EnsureSpell(healer, SPELL_RENEW);

            if (renewOnSelf && !renewCast && elapsedMs >= 100 && !healer->IsNonMeleeSpellCast(false))
            {
                renewCast = healer->CastSpell(healer, SPELL_RENEW, false) == SPELL_CAST_OK;
                return;
            }

            if (casts.StartMs.size() >= casts.MaxCasts || elapsedMs < casts.NextMs ||
                healer->IsNonMeleeSpellCast(false))
                return;

            if (healer->CastSpell(members[HEAL_TEST_ALLY], SPELL_GREATER_HEAL, false) == SPELL_CAST_OK)
            {
                casts.StartMs.push_back(elapsedMs);
                casts.NextMs = elapsedMs + 3000;
            }
            else
            {
                ++casts.Failures;
                casts.NextMs = elapsedMs + 1000;
            }
        };
    }

    // Measures each Greater Heal of a finished run: start (from the script), finish (the recorded cast), and the hits
    // on the healer's own slot between them. A cast is on time when it finished within a step of start + cast time,
    // and delayed when it took at least about the 500 ms a pushback adds.
    PushbackOutcome MeasurePushback(SimDaemon::RunResult const& result, PushbackCasts const& casts, uint32 castTimeMs,
        size_t selfIndex)
    {
        PushbackOutcome outcome;
        outcome.Casts = uint32(casts.StartMs.size());

        std::vector<uint32> finishes;
        for (SimDaemon::RunResult::CastEvent const& e : result.CastEvents)
            if (e.SpellId == SPELL_GREATER_HEAL && !e.Triggered)
                finishes.push_back(e.TimestampMs);

        for (size_t i = 0; i < casts.StartMs.size() && i < finishes.size(); ++i)
        {
            ++outcome.Windows;
            uint32 const start = casts.StartMs[i];
            uint32 const finish = finishes[i];
            uint32 const took = finish >= start ? finish - start : 0;

            uint32 hits = 0;
            for (SimHeal::DamageEvent const& d : result.DamageTakenEvents)
                if (d.TargetIndex == selfIndex && d.TimestampMs > start && d.TimestampMs < finish)
                    ++hits;
            outcome.WindowsWithHit += hits > 0 ? 1 : 0;

            bool const onTime = took + HEAL_TEST_STEP_MS >= castTimeMs && took <= castTimeMs + HEAL_TEST_STEP_MS;
            bool const delayed = took + HEAL_TEST_STEP_MS >= castTimeMs + 500;
            outcome.OnTime += onTime ? 1 : 0;
            outcome.Delayed += delayed ? 1 : 0;
            outcome.Detail += Acore::StringFormat("{}[start {} ms, took {} ms, {} hit(s) on the healer]",
                outcome.Detail.empty() ? "" : " ", start, took, hits);
        }

        return outcome;
    }

    // Heal test 5/6 (heal-pushback): a pinned healer casting a cast-time heal while Sim Pin Hits land on it. The hits
    // carry SPELL_ATTR7_DONT_CAUSE_SPELL_PUSHBACK, so every Greater Heal finishes in exactly its cast time. The
    // control run shows the test can see a pushback: with the healer on the drain mode (Sim Damage Pulses, which do
    // push back) the same casts take longer.
    bool RunHealPushbackTest()
    {
        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_GREATER_HEAL);
        if (!info)
        {
            LogVerdict("heal-pushback test", false, "Greater Heal (2060) is not in spell_dbc.");
            return false;
        }

        // Pinned healer: Renew on itself ticks it above its pin every 3 s, and the driver's Pin Hit follows
        PushbackCasts pinnedCasts;
        bool pinnedRenew = false;
        SimDaemon::RunResult pinned;
        if (!RunHealScenario(HEAL_TEST_PIN_PARTY, 16000, MakePushbackHook(pinnedCasts, true, pinnedRenew), pinned))
        {
            LogVerdict("heal-pushback test", false, "the pinned scenario did not run - see preceding LOG_ERROR "
                "output.");
            return false;
        }

        // Control: the healer is a drain target, no Renew needed
        PushbackCasts drainCasts;
        bool drainRenew = false;
        SimDaemon::RunResult drained;
        if (!RunHealScenario("tank:pin:50, 3*dps:pin:50, self:drain:20", 16000,
                MakePushbackHook(drainCasts, false, drainRenew), drained))
        {
            LogVerdict("heal-pushback test", false, "the control scenario did not run - see preceding LOG_ERROR "
                "output.");
            return false;
        }

        // The cast time of the spell data (the healer has no haste)
        uint32 const castTimeMs = info->CalcCastTime();

        size_t const selfIndex = pinned.HealTargetInfo.size() - 1;
        PushbackOutcome const pinnedOutcome = MeasurePushback(pinned, pinnedCasts, castTimeMs, selfIndex);
        PushbackOutcome const controlOutcome =
            MeasurePushback(drained, drainCasts, castTimeMs, drained.HealTargetInfo.size() - 1);

        bool const pinnedOk = pinnedRenew && pinnedCasts.Failures == 0 && pinnedOutcome.Casts == pinnedCasts.MaxCasts &&
            pinnedOutcome.Windows == pinnedOutcome.Casts && pinnedOutcome.WindowsWithHit == pinnedOutcome.Windows &&
            pinnedOutcome.OnTime == pinnedOutcome.Windows;
        bool const controlOk = drainCasts.Failures == 0 && controlOutcome.Windows > 0 &&
            controlOutcome.Delayed == controlOutcome.Windows;

        bool const passed = castTimeMs > 0 && pinnedOk && controlOk;
        LogVerdict("heal-pushback test", passed, Acore::StringFormat(
            "Greater Heal cast time {} ms. Pinned healer (Renew on itself: {}): {} cast(s), {} with a Pin Hit on the "
            "healer during the cast, {} finished within one step of the cast time: {}. Control, healer on drain:20: "
            "{} cast(s), {} pushed back by at least about 500 ms: {}.", castTimeMs, pinnedRenew ? "cast" : "NOT cast",
            pinnedOutcome.Casts, pinnedOutcome.WindowsWithHit, pinnedOutcome.OnTime, pinnedOutcome.Detail,
            controlOutcome.Windows, controlOutcome.Delayed, controlOutcome.Detail));
        return passed;
    }

    // Heal test 6/6 (heal-guardian, stage HS3 part D): Guardian Spirit's heal is cast by the target itself, with the
    // priest as the original caster (spell_priest.cpp), so the recorder credits it to the priest. A Rogue draining
    // 2,000 a second under a Guardian Spirit dies on its fifth pulse, the aura answers with its heal of the spell's
    // percent of the Rogue's max health, and that heal must be in the priest's heal events.
    bool RunHealGuardianSpiritTest()
    {
        constexpr uint32 SPELL_GUARDIAN_SPIRIT = 47788;
        constexpr uint32 SPELL_GUARDIAN_SPIRIT_HEAL = 48153;
        constexpr size_t DRAINED = 1;

        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_GUARDIAN_SPIRIT);
        if (!info)
        {
            LogVerdict("heal-guardian test", false, "Guardian Spirit (47788) is not in spell_dbc.");
            return false;
        }

        struct State
        {
            bool Cast = false;
            uint32 CastMs = 0;
            SpellCastResult Result = SPELL_CAST_OK;
        } state;

        auto const hook = [&](uint32 elapsedMs, Player* healer, std::vector<Player*> const& members)
        {
            EnsureSpell(healer, SPELL_GUARDIAN_SPIRIT);
            if (state.Cast || elapsedMs < 1000 || healer->IsNonMeleeSpellCast(false))
                return;

            state.Cast = true;
            state.CastMs = elapsedMs;
            state.Result = healer->CastSpell(members[DRAINED], SPELL_GUARDIAN_SPIRIT, false);
        };

        SimDaemon::RunResult result;
        if (!RunHealScenario("tank:pin:50, dps:drain:2000, 2*dps:pin:50, self:pin:50", 12000, hook, result, 9000))
        {
            LogVerdict("heal-guardian test", false, "the heal scenario did not run - see preceding LOG_ERROR output.");
            return false;
        }

        uint32 const maxHealth = result.HealTargetInfo.size() > DRAINED ? result.HealTargetInfo[DRAINED].MaxHealth : 0;
        float const percent = float(info->Effects[EFFECT_1].CalcValue());
        uint32 const expected = uint32(float(maxHealth) * percent / 100.0f);

        uint32 events = 0;
        uint32 wrong = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            if (e.SpellId != SPELL_GUARDIAN_SPIRIT_HEAL)
                continue;

            ++events;
            if (e.IsPet || e.TargetIndex != DRAINED || e.Periodic || e.Raw != expected)
                ++wrong;
        }

        bool const passed = state.Cast && state.Result == SPELL_CAST_OK && events == 1 && wrong == 0 && maxHealth > 0;
        LogVerdict("heal-guardian test", passed, Acore::StringFormat(
            "Guardian Spirit cast at {} ms (result {}) on the draining Rogue (max health {}), {} Guardian Spirit heal "
            "event(s) credited to the priest ({} with a wrong target, owner or amount; expected {}% of max health = "
            "{}).", state.CastMs, uint32(state.Result), maxHealth, events, wrong, percent, expected));
        return passed;
    }
    // ---- Tank-sim known-value tests (stage TS3a; plan .agents/plans/tank-sim/tank-sim.PLAN.md) ----
    //
    // Each test runs one real tank-mode iteration (SimDaemon::RunPlayerbotBatch() with RunMode Tank: the tank dummy AI,
    // the damage solver, the DamageTakenRecorder) with short, fixed settings and no pre-pull buff phase. Two actors:
    //  - the Prot Warrior of conf/profiles/ProtWarriorTankSim.conf (talents, gear, stats, the dummy armor), loaded from
    //    the directory of DpsSim.Profile (falling back to the container's profile directory), Human, level 60;
    //  - a bare level-60 Human Warrior: no talents, only a one-hand sword (17015, which replaces the starter outfit),
    //    no shield, so it cannot block.
    // RunConfig::TankSilenceBot keeps the actor's bot AI quiet where the test must control everything the actor does
    // (RunConfig::TankStepHook casts what the test needs); the crit and Revenge tests run the real bot. Expected values
    // come from the core's formulas and the run's own recorded inputs, never from a previous run.

    constexpr uint32 TANK_TEST_STEP_MS = 100;
    constexpr uint32 SPELL_DEFENSIVE_STANCE = 71;
    constexpr uint32 SPELL_SUNDER_ARMOR = 7386;
    constexpr uint32 SPELL_THUNDER_CLAP = 6343;
    constexpr uint32 SPELL_REVENGE = 6572;
    constexpr uint32 SPELL_CONCUSSION_BLOW = 12809;
    constexpr uint32 SPELL_DEVASTATE = 20243;
    // The bare warrior's only item: Dark Iron Reaver, a level-60 one-hand sword (no shield, so no block)
    constexpr uint32 TANK_TEST_BARE_WEAPON = 17015;
    constexpr char const* TANK_TEST_PROFILE = "ProtWarriorTankSim.conf";
    constexpr char const* TANK_TEST_PROFILE_DIR = "/azerothcore/modules/mod-dpssim/conf/profiles";

    using TankStepHook = std::function<void(uint32, Player*, std::vector<Creature*> const&)>;

    struct TankSetup
    {
        // true: the ProtWarriorTankSim character; false: the bare warrior
        bool UseProfile = false;
        bool SilenceBot = true;
        uint32 DurationMs = 30000;
        uint32 SwingMs = 2000;
        uint32 Targets = 1;
        SimTank::HitRange Hit = SimTank::DEFAULT_BOSS_HIT;
        SimTank::HitRange PackHit = SimTank::DEFAULT_PACK_HIT;
        SimTank::Scenario Scenario = SimTank::Scenario::Dps;
        bool Crit = true;
        std::vector<uint32> PullAuras;
        TankStepHook Hook;
    };

    // ProtWarriorTankSim.conf next to the profile this test run was started with, else in the container's profile
    // directory (run-sim.sh mounts modules/ at /azerothcore/modules)
    std::string TankTestProfilePath()
    {
        std::string const current = sConfigMgr->GetOption<std::string>("DpsSim.Profile", "");
        size_t const slash = current.find_last_of('/');
        if (slash != std::string::npos)
        {
            std::string const sibling = current.substr(0, slash + 1) + TANK_TEST_PROFILE;
            if (std::ifstream(sibling).good())
                return sibling;
        }

        return std::string(TANK_TEST_PROFILE_DIR) + "/" + TANK_TEST_PROFILE;
    }

    // Runs one tank-mode iteration per `setup`. False (logged) when the profile or the batch failed.
    bool RunTankScenario(char const* testName, TankSetup const& setup, SimDaemon::RunResult& result)
    {
        SimDaemon::RunConfig config;
        config.RunMode = SimDaemon::Mode::Tank;
        config.StepMs = TANK_TEST_STEP_MS;
        config.DurationMs = setup.DurationMs;
        config.ActorLevel = 60;
        config.TargetLevel = 60;
        config.ActorRace = 1 /* RACE_HUMAN */;
        config.ActorClass = CLASS_WARRIOR;
        config.PlayerbotGlyphs = false;
        config.PrePullBuffMs = 0;
        config.TargetCount = std::max(setup.Targets, 1u);
        config.TargetRank = config.TargetCount > 1 ? SimTarget::Rank::Elite : SimTarget::Rank::Boss;

        if (setup.UseProfile)
        {
            std::string const path = TankTestProfilePath();
            SimProfile::Profile profile;
            if (!SimProfile::Load(path, profile) || profile.Class != CLASS_WARRIOR)
            {
                LogVerdict(testName, false, Acore::StringFormat("the Prot Warrior profile '{}' did not load (or is not "
                    "a warrior) - see the SimProfile::Load() error above.", path));
                return false;
            }

            config.PlayerbotTalents = profile.PlayerbotTalents;
            config.GearItemIds = profile.GearItemIds;
            config.SpellPower = profile.SpellPower;
            config.CombatRatings = profile.CombatRatings;
            config.Stats = profile.Stats;
            config.AttackPower = profile.AttackPower;
            config.TargetArmor = profile.TargetArmor;
        }
        else
            config.GearItemIds = {TANK_TEST_BARE_WEAPON};

        config.TankScenario = setup.Scenario;
        config.TankHit = setup.Hit;
        config.TankPackHit = setup.PackHit;
        config.TankSwingMs = setup.SwingMs;
        config.TankDummyCrit = setup.Crit;
        config.TankPullAuras = setup.PullAuras;
        config.TankStepHook = setup.Hook;
        config.TankSilenceBot = setup.SilenceBot;

        std::vector<SimDaemon::RunResult> results;
        if (!SimDaemon::RunPlayerbotBatch(config, 1, results) || results.size() != 1 || !results[0].Success)
        {
            LogVerdict(testName, false, "the tank iteration did not run - see preceding LOG_ERROR output.");
            return false;
        }

        result = std::move(results[0]);
        return true;
    }

    bool IsLanded(SimTank::Outcome outcome)
    {
        return outcome != SimTank::Outcome::Miss && outcome != SimTank::Outcome::Dodge &&
            outcome != SimTank::Outcome::Parry && outcome != SimTank::Outcome::Other;
    }

    // The swing timestamps of one dummy, in order
    std::vector<uint32> SwingTimes(SimDaemon::RunResult const& result, uint8 dummyIndex)
    {
        std::vector<uint32> times;
        for (SimTank::SwingEvent const& e : result.Swings)
            if (e.DummyIndex == dummyIndex)
                times.push_back(e.TimestampMs);
        return times;
    }

    // "2200:12 2400:1" - the gaps between consecutive swings and how often each occurred
    std::string GapHistogram(std::vector<uint32> const& times)
    {
        std::map<uint32, uint32> gaps;
        for (size_t i = 1; i < times.size(); ++i)
            ++gaps[times[i] - times[i - 1]];
        std::string text;
        for (auto const& [gap, count] : gaps)
            text += Acore::StringFormat("{}{}:{}", text.empty() ? "" : " ", gap, count);
        return text.empty() ? "none" : text;
    }

    // Unit::CalcArmorReducedDamage() for a creature attacker of level `attackerLevel` (no armor penetration, no target
    // resistance aura): the share of the damage armor takes off
    float ArmorReduction(uint32 armor, uint32 attackerLevel)
    {
        float levelModifier = float(attackerLevel);
        if (levelModifier > 59)
            levelModifier = levelModifier + (4.5f * (levelModifier - 59));
        float reduction = 0.1f * float(armor) / (8.5f * levelModifier + 40);
        reduction = reduction / (1.0f + reduction);
        return std::clamp(reduction, 0.0f, 0.75f);
    }

    // Tank test 1/8 (tank.outcomes): ~1,000 boss swings at the silenced Prot Warrior (shield on, so it can block).
    // Each of miss, dodge, parry and block (partial and full) must land within max(1 point, 3 sigma) of the mean
    // per-swing chance the recorder replayed from the core's roll inputs; sigma = sqrt(p (1 - p) / n), the binomial
    // standard deviation of a rate over n swings at that mean chance (the chances do not move: no stance, no Shield
    // Block, nothing cast). Crit is logged with the same tolerance but is not part of the verdict.
    bool RunTankOutcomesTest()
    {
        char const* const name = "tank.outcomes test";
        TankSetup setup;
        setup.UseProfile = true;
        setup.SwingMs = 500;
        setup.Hit = {300, 400};
        setup.DurationMs = 500 * 1000 + 1000;

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        using SimTank::Outcome;
        uint32 const n = uint32(result.Swings.size());
        double observed[5] = {};
        double expected[5] = {};
        for (SimTank::SwingEvent const& e : result.Swings)
        {
            observed[0] += e.Result == Outcome::Miss;
            observed[1] += e.Result == Outcome::Dodge;
            observed[2] += e.Result == Outcome::Parry;
            observed[3] += e.Result == Outcome::Block || e.Result == Outcome::FullBlock;
            observed[4] += e.Result == Outcome::Crit;
            expected[0] += e.ExpectedMiss;
            expected[1] += e.ExpectedDodge;
            expected[2] += e.ExpectedParry;
            expected[3] += e.ExpectedBlock;
            expected[4] += e.ExpectedCrit;
        }

        char const* const names[5] = {"miss", "dodge", "parry", "block", "crit"};
        bool ratesOk = true;
        std::string detail;
        for (size_t i = 0; i < 5; ++i)
        {
            double const obsPct = n ? 100.0 * observed[i] / n : 0.0;
            // Hundredths of a percent summed over the swings -> mean chance in percent
            double const expPct = n ? expected[i] / 100.0 / n : 0.0;
            double const p = expPct / 100.0;
            double const sigmaPct = n ? 100.0 * std::sqrt(p * (1.0 - p) / n) : 0.0;
            double const tolerance = std::max(1.0, 3.0 * sigmaPct);
            bool const ok = std::abs(obsPct - expPct) <= tolerance;
            if (i < 4)
                ratesOk = ratesOk && ok;
            detail += Acore::StringFormat("{}{} {:.2f}% vs {:.2f}% (sigma {:.2f}, tolerance {:.2f}{}{})",
                detail.empty() ? "" : "; ", names[i], obsPct, expPct, sigmaPct, tolerance, ok ? "" : ", OUTSIDE",
                i == 4 ? ", not in the verdict" : "");
        }

        bool const passed = n >= 950 && ratesOk;
        LogVerdict(name, passed, Acore::StringFormat("{} swings (expected about {}; at least 950 needed). Observed vs "
            "mean expected per swing: {}.", n, setup.DurationMs / setup.SwingMs, detail));
        return passed;
    }

    // Tank test 2/8 (tank.crit_immune): the Prot Warrior with its real bot, in Defensive Stance (the hook casts it at
    // the first step if the bot has not), at the defense its gear and AlwaysMaxSkillForLevel give it, swung at by the
    // boss with crits on. Deterministic: 0 crits, 0 crit-bug swings (a crit rolled at chance 0, the report's
    // critBugCount), the dummy's expected crit chance after the first second <= 0, no swing after the first second
    // rolled with a crit chance above 0, the actor in Defensive Stance at 1 s and its defense at least the level's cap.
    bool RunTankCritImmuneTest()
    {
        char const* const name = "tank.crit_immune test";
        struct State
        {
            bool StanceCast = false;
            bool InStanceAt1s = false;
            bool Checked = false;
        } state;

        TankSetup setup;
        setup.UseProfile = true;
        setup.SilenceBot = false;
        setup.SwingMs = 1000;
        setup.DurationMs = 60000;
        setup.Hook = [&state](uint32 elapsedMs, Player* actor, std::vector<Creature*> const&)
        {
            if (!state.StanceCast)
            {
                state.StanceCast = true;
                if (actor->GetShapeshiftForm() != FORM_DEFENSIVESTANCE)
                    actor->CastSpell(actor, SPELL_DEFENSIVE_STANCE, true);
            }
            if (!state.Checked && elapsedMs >= 1000)
            {
                state.Checked = true;
                state.InStanceAt1s = actor->GetShapeshiftForm() == FORM_DEFENSIVESTANCE;
            }
        };

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        uint32 crits = 0;
        uint32 critBugs = 0;
        uint32 rolledWithCrit = 0;
        for (SimTank::SwingEvent const& e : result.Swings)
        {
            bool const crit = e.Result == SimTank::Outcome::Crit;
            crits += crit;
            critBugs += crit && e.ExpectedCrit == 0;
            rolledWithCrit += e.TimestampMs >= 1000 && e.ExpectedCrit > 0;
        }

        float const expectedCrit = result.TankDummies.empty() ? 1.0f : result.TankDummies.front().ExpectedCritPct;
        SimTank::ActorInfo const& sheet = result.TankActor;
        bool const defenseCapped = sheet.DefenseSkill >= sheet.MaxSkillForLevel;
        bool const passed = result.Swings.size() >= 50 && crits == 0 && critBugs == 0 && expectedCrit <= 0.0f &&
            rolledWithCrit == 0 && state.InStanceAt1s && defenseCapped;
        LogVerdict(name, passed, Acore::StringFormat("{} swings, {} crit(s), {} crit-bug swing(s), dummy's expected "
            "crit chance after 1 s {:.2f}% (pull {:.2f}%), {} swing(s) after 1 s rolled with a crit chance above 0; "
            "Defensive Stance at 1 s: {}; defense {} vs the level's cap {}.", result.Swings.size(), crits, critBugs,
            expectedCrit, result.TankDummies.empty() ? 0.0f : result.TankDummies.front().ExpectedCritPct,
            rolledWithCrit, state.InStanceAt1s ? "yes" : "NO", sheet.DefenseSkill, sheet.MaxSkillForLevel));
        return passed;
    }

    // Tank test 3/8 (tank.hit_formula): the silenced Prot Warrior in Defensive Stance (cast by the hook at the first
    // step), the boss at a fixed hit (min = max), crits off. For every landed, unblocked, unabsorbed swing:
    //   PreArmor = uint32(roll x TakenMult) (+-1: the core multiplies the float roll, the recorder measured the
    //              multiplier on a 1,000,000 hit), roll = the dummy's damage field (min = max, so known);
    //   Final    = ceil(PreArmor x (1 - armor reduction)), the reduction from Unit::CalcArmorReducedDamage()'s formula
    //              with the boss's real level (63, plan T9) and the actor's armor read every step (+-1: float order).
    // Also: TakenMult < 1 on every checked swing (the stance; its range is logged), the armor the same at every step
    // after the stance.
    bool RunTankHitFormulaTest()
    {
        char const* const name = "tank.hit_formula test";
        struct State
        {
            bool StanceCast = false;
            uint32 ArmorMin = 0xFFFFFFFF;
            uint32 ArmorMax = 0;
        } state;

        TankSetup setup;
        setup.UseProfile = true;
        setup.SwingMs = 500;
        setup.Hit = {1000, 1000};
        setup.Crit = false;
        setup.DurationMs = 20000;
        setup.Hook = [&state](uint32 elapsedMs, Player* actor, std::vector<Creature*> const&)
        {
            if (!state.StanceCast)
            {
                state.StanceCast = true;
                actor->CastSpell(actor, SPELL_DEFENSIVE_STANCE, true);
                return;
            }
            if (elapsedMs >= 2 * TANK_TEST_STEP_MS)
            {
                state.ArmorMin = std::min(state.ArmorMin, actor->GetArmor());
                state.ArmorMax = std::max(state.ArmorMax, actor->GetArmor());
            }
        };

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        if (result.TankDummies.empty())
        {
            LogVerdict(name, false, "no dummy info in the result.");
            return false;
        }

        SimTank::DummyInfo const& dummy = result.TankDummies.front();
        uint32 const rollMin = uint32(dummy.FieldMin);
        uint32 const rollMax = uint32(dummy.FieldMax);
        uint32 const armor = state.ArmorMax;
        float const reduction = ArmorReduction(armor, dummy.Level);

        uint32 checked = 0;
        uint32 preViolations = 0;
        uint32 finalViolations = 0;
        uint32 skippedAbsorbed = 0;
        float multMin = 10.0f;
        float multMax = 0.0f;
        std::string firstDetail;
        for (SimTank::SwingEvent const& e : result.Swings)
        {
            if (e.Result != SimTank::Outcome::Hit || e.TimestampMs < 2 * TANK_TEST_STEP_MS)
                continue;
            if (e.Absorbed > 0 || e.Resisted > 0)
            {
                ++skippedAbsorbed;
                continue;
            }

            ++checked;
            multMin = std::min(multMin, e.TakenMult);
            multMax = std::max(multMax, e.TakenMult);

            uint32 const preLow = uint32(float(rollMin) * e.TakenMult);
            uint32 const preHigh = uint32(float(rollMax) * e.TakenMult);
            bool const preOk = e.PreArmor + 1 >= preLow && e.PreArmor <= preHigh + 1;
            uint32 const expectedFinal = uint32(std::ceil(std::max(float(e.PreArmor) * (1.0f - reduction), 0.0f)));
            bool const finalOk = e.Final + 1 >= expectedFinal && e.Final <= expectedFinal + 1 &&
                e.ArmorMitigated == e.PreArmor - e.Final;
            preViolations += !preOk;
            finalViolations += !finalOk;

            if (firstDetail.empty() || !preOk || !finalOk)
            {
                std::string const line = Acore::StringFormat("swing at {} ms: pre-armor {} (expected {}-{}), final {} "
                    "(expected {}), armor took {}", e.TimestampMs, e.PreArmor, preLow, preHigh, e.Final, expectedFinal,
                    e.ArmorMitigated);
                if (firstDetail.empty())
                    firstDetail = line;
                if (!preOk || !finalOk)
                    LOG_ERROR("server.dpssim", "mod-dpssim: tank.hit_formula test - {}.", line);
            }
        }

        bool const multOk = checked > 0 && multMax < 1.0f;
        bool const passed = dummy.Level == 63 && rollMin == rollMax && armor == state.ArmorMin && checked >= 10 &&
            preViolations == 0 && finalViolations == 0 && multOk;
        LogVerdict(name, passed, Acore::StringFormat("boss level {} (expected 63), roll {}-{} (one value expected), "
            "actor armor {}-{} over the fight -> reduction {:.4f} at level {}; damage-taken multiplier {:.4f}-{:.4f} "
            "(below 1 expected); {} landed unblocked swing(s) checked ({} skipped: absorbed), {} with a "
            "wrong pre-armor value, {} with a wrong final value. First: {}.", dummy.Level, rollMin, rollMax,
            state.ArmorMin, state.ArmorMax, reduction, dummy.Level, multMin, multMax, checked, skippedAbsorbed,
            preViolations, finalViolations, firstDetail.empty() ? "none" : firstDetail));
        return passed;
    }

    // Tank test 4/8 (tank.revenge): the Prot Warrior with its real bot, the boss swinging every second for 180 s. The
    // hook marks every step at which Revenge is usable (known, off cooldown, the dodge/parry/block aura state that
    // allows it, Defensive Stance, rage for its cost); an opportunity is a step where it becomes usable. Checked:
    //  - fast: a Revenge cast within 1.5 s (one GCD) of the opportunity, in at least 40% of the opportunities. Why 40%:
    //    the first GCD the bot gets after an avoid always starts within 1.5 s, and Revenge (relevance normal + 8.5 in
    //    data/strategies/warrior/prot.yaml) loses it only to Shield Slam (8.8) or Thunder Clap (8.7) when one of them
    //    is ready at that moment. Those two take about half of the bot's GCDs (TS1: ~22 + ~20 casts in ~80 GCDs per
    //    120 s), so about half the opportunities should be fast; 40% leaves room for the sample. The double AI tick
    //    (healing sim A.3.1) only makes the bot react sooner, so it cannot push this down.
    //  - no wrong priority: the bot never casts a lower row (Devastate 8.0/8.45, Concussion Blow 8.2, Sunder Armor)
    //    at a step where Revenge was usable, before it casts Revenge or the 1.5 s pass; at most max(1, 5%) of the
    //    opportunities, for the step race of a cast decided in the same tick as the avoid.
    bool RunTankRevengeTest()
    {
        char const* const name = "tank.revenge test";
        SpellInfo const* revenge = sSpellMgr->GetSpellInfo(SPELL_REVENGE);
        if (!revenge)
        {
            LogVerdict(name, false, "Revenge (6572) is not in spell_dbc.");
            return false;
        }

        struct State
        {
            std::vector<bool> UsableAtStep;
            std::vector<uint32> Opportunities;
            bool UsableLast = false;
        } state;

        TankSetup setup;
        setup.UseProfile = true;
        setup.SilenceBot = false;
        setup.SwingMs = 1000;
        setup.DurationMs = 180000;
        setup.Hook = [&state, revenge](uint32 elapsedMs, Player* actor, std::vector<Creature*> const&)
        {
            bool const usable = actor->HasSpell(SPELL_REVENGE) && !actor->HasSpellCooldown(SPELL_REVENGE) &&
                actor->HasAuraState(AURA_STATE_DEFENSE) && actor->GetShapeshiftForm() == FORM_DEFENSIVESTANCE &&
                int32(actor->GetPower(POWER_RAGE)) >= revenge->CalcPowerCost(actor, revenge->GetSchoolMask());
            size_t const step = elapsedMs / TANK_TEST_STEP_MS;
            if (state.UsableAtStep.size() <= step)
                state.UsableAtStep.resize(step + 1, false);
            state.UsableAtStep[step] = usable;
            if (usable && !state.UsableLast)
                state.Opportunities.push_back(elapsedMs);
            state.UsableLast = usable;
        };

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        auto const usableAt = [&state](uint32 ms)
        {
            size_t const step = ms / TANK_TEST_STEP_MS;
            return step < state.UsableAtStep.size() && state.UsableAtStep[step];
        };

        constexpr uint32 WINDOW_MS = 1500;
        uint32 fast = 0;
        uint32 wrongPriority = 0;
        std::map<uint32, uint32> delays;
        for (uint32 opportunityMs : state.Opportunities)
        {
            uint32 revengeAt = 0;
            bool found = false;
            for (SimDaemon::RunResult::CastEvent const& e : result.CastEvents)
                if (!e.Triggered && e.SpellId == SPELL_REVENGE && e.TimestampMs + TANK_TEST_STEP_MS >= opportunityMs &&
                    e.TimestampMs <= opportunityMs + WINDOW_MS)
                {
                    revengeAt = e.TimestampMs;
                    found = true;
                    break;
                }

            if (found)
            {
                ++fast;
                ++delays[(revengeAt > opportunityMs ? revengeAt - opportunityMs : 0) / 500 * 500];
            }

            uint32 const endMs = found ? revengeAt : opportunityMs + WINDOW_MS;
            for (SimDaemon::RunResult::CastEvent const& e : result.CastEvents)
                if (!e.Triggered && e.TimestampMs > opportunityMs && e.TimestampMs < endMs && usableAt(e.TimestampMs) &&
                    (e.SpellId == SPELL_DEVASTATE || e.SpellId == SPELL_CONCUSSION_BLOW ||
                     e.SpellId == SPELL_SUNDER_ARMOR))
                {
                    ++wrongPriority;
                    LOG_ERROR("server.dpssim", "mod-dpssim: tank.revenge test - spell {} cast at {} ms while Revenge "
                        "was usable (since {} ms).", e.SpellId, e.TimestampMs, opportunityMs);
                    break;
                }
        }

        uint32 revengeCasts = 0;
        for (SimDaemon::RunResult::CastEvent const& e : result.CastEvents)
            revengeCasts += !e.Triggered && e.SpellId == SPELL_REVENGE;

        uint32 const opportunities = uint32(state.Opportunities.size());
        double const fastPct = opportunities ? 100.0 * fast / opportunities : 0.0;
        uint32 const wrongAllowed = std::max(1u, opportunities / 20);
        std::string delayText;
        for (auto const& [bucket, count] : delays)
            delayText += Acore::StringFormat("{}{}-{} ms:{}", delayText.empty() ? "" : " ", bucket, bucket + 499,
                count);

        bool const passed = opportunities >= 15 && fastPct >= 40.0 && wrongPriority <= wrongAllowed;
        LogVerdict(name, passed, Acore::StringFormat("{} swings, {} Revenge opportunities (at least 15 needed), {} "
            "Revenge casts in all; {} cast within {} ms of the opportunity ({:.1f}%, at least 40% expected; delays "
            "{}); "
            "{} opportunity(ies) where a lower row was cast first (at most {}).", result.Swings.size(), opportunities,
            revengeCasts, fast, WINDOW_MS, fastPct, delayText.empty() ? "none" : delayText, wrongPriority,
            wrongAllowed));
        return passed;
    }

    // Tank test 5/8 (tank.ttd): the bare, silenced warrior (no stance, no defensives, no shield, nothing healing it)
    // in the survive scenario, the boss at a fixed 100 every second, crits off. Health only moves with the landed
    // swings, so the death is exact:
    //   D = the final damage of a landed swing (every landed swing must be the same D), k = ceil(health / D);
    //   the actor dies on its k-th landed swing: ActorDiedAtMs = that swing's tick + one step (SimTank.h time bases),
    //   and health never rises during the fight.
    // The handoff's formula, TTD = health / (average landed damage per swing / swing interval), is logged against the
    // death time twice: with the mean per-swing chances the recorder stored (the expected TTD; the death lands within
    // 3 sigma of it in swings, sigma = sqrt(k p) / (1 - p) for p the avoid chance, the spread of the swing count a
    // negative binomial gives; part of the verdict), and with the run's own average (informational).
    bool RunTankTtdTest()
    {
        char const* const name = "tank.ttd test";
        struct State
        {
            uint32 LastHealth = 0;
            uint32 Rises = 0;
        } state;

        TankSetup setup;
        setup.Scenario = SimTank::Scenario::Survive;
        setup.Hit = {100, 100};
        setup.Crit = false;
        setup.SwingMs = 1000;
        setup.DurationMs = 120000;
        setup.Hook = [&state](uint32, Player* actor, std::vector<Creature*> const&)
        {
            uint32 const health = actor->GetHealth();
            if (state.LastHealth > 0 && health > state.LastHealth)
                ++state.Rises;
            state.LastHealth = health;
        };

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        uint32 const health = result.TankActorAtPull.Health;
        uint32 damage = 0;
        bool sameDamage = true;
        uint32 landed = 0;
        uint32 cumulative = 0;
        uint32 deathSwingMs = 0;
        uint32 deathSwingIndex = 0;
        bool reached = false;
        double avoidChance = 0.0;
        for (size_t i = 0; i < result.Swings.size(); ++i)
        {
            SimTank::SwingEvent const& e = result.Swings[i];
            avoidChance += double(e.ExpectedMiss + e.ExpectedDodge + e.ExpectedParry + e.ExpectedBlock) / 10000.0;
            if (!IsLanded(e.Result))
                continue;

            ++landed;
            if (damage == 0)
                damage = e.Final;
            sameDamage = sameDamage && e.Final == damage && e.Absorbed == 0;
            cumulative += e.Final;
            if (!reached && cumulative >= health)
            {
                reached = true;
                deathSwingMs = e.TimestampMs;
                deathSwingIndex = uint32(i);
            }
        }

        uint32 const swings = uint32(result.Swings.size());
        avoidChance = swings ? avoidChance / swings : 0.0;
        uint32 const k = damage ? (health + damage - 1) / damage : 0;
        bool const deathOnKth = reached && landed == k && deathSwingIndex + 1 == swings;
        bool const deathTimeOk = result.ActorDied && result.ActorDiedAtMs + TANK_TEST_STEP_MS >= deathSwingMs &&
            result.ActorDiedAtMs <= deathSwingMs + 2 * TANK_TEST_STEP_MS;

        // The handoff's formula, with the expected avoid chance: k / (1 - p) swings, the first one interval in
        double const interval = double(setup.SwingMs);
        double const expectedSwings = (1.0 - avoidChance) > 0.0 ? double(k) / (1.0 - avoidChance) : 0.0;
        double const expectedTtd = expectedSwings * interval;
        double const sigmaSwings = (1.0 - avoidChance) > 0.0 ?
            std::sqrt(double(k) * avoidChance) / (1.0 - avoidChance) : 0.0;
        double const offSwings = (double(result.ActorDiedAtMs) - expectedTtd) / interval;
        bool const expectedOk = std::abs(offSwings) <= std::max(1.0, 3.0 * sigmaSwings);
        // ... and with the run's own average landed damage per swing (informational)
        double const observedPerSwing = swings ? double(cumulative) / swings : 0.0;
        double const observedTtd = observedPerSwing > 0.0 ? double(health) / (observedPerSwing / interval) : 0.0;

        bool const passed = health > 0 && damage > 0 && sameDamage && deathOnKth && deathTimeOk && state.Rises == 0 &&
            expectedOk;
        LogVerdict(name, passed, Acore::StringFormat("health {}, every landed swing {} ({}), k = ceil({} / {}) = {}; "
            "{} swings, {} landed, the death after landed swing {} at {} ms ({}), TTD {} ms ({}); health rose {} "
            "time(s). Handoff formula: with the expected avoid chance {:.2f}% TTD {:.0f} ms, off by {:.2f} swings "
            "(limit {:.2f}); with the run's own {:.1f} damage per swing {:.0f} ms (informational).", health, damage,
            sameDamage ? "all equal, no shields" : "NOT all equal", health, damage, k, swings, landed, landed,
            deathSwingMs, deathOnKth ? "the k-th, the last swing" : "NOT the k-th or not the last",
            result.ActorDiedAtMs, deathTimeOk ? "one step after it" : "NOT one step after it", state.Rises,
            100.0 * avoidChance, expectedTtd, offSwings, std::max(1.0, 3.0 * sigmaSwings), observedPerSwing,
            observedTtd));
        return passed;
    }

    // Tank test 6/8 (tank.survived): the bare, silenced warrior in the survive scenario, a fixed 10 every second for
    // 30 s, crits off: it lives. TankSurvived true, not dead, ElapsedMs = the duration (the report's TTD then counts
    // as the duration, plan T11), and the health it lost equals the recorded final damage exactly (nothing heals it).
    bool RunTankSurvivedTest()
    {
        char const* const name = "tank.survived test";
        struct State
        {
            uint32 Health = 0;
            uint32 MaxHealth = 0;
        } state;

        TankSetup setup;
        setup.Scenario = SimTank::Scenario::Survive;
        setup.Hit = {10, 10};
        setup.Crit = false;
        setup.SwingMs = 1000;
        setup.DurationMs = 30000;
        setup.Hook = [&state](uint32, Player* actor, std::vector<Creature*> const&)
        {
            state.Health = actor->GetHealth();
            state.MaxHealth = actor->GetMaxHealth();
        };

        SimDaemon::RunResult result;
        if (!RunTankScenario(name, setup, result))
            return false;

        uint64 taken = 0;
        for (SimTank::SwingEvent const& e : result.Swings)
            taken += e.Final;

        bool const healthOk = state.MaxHealth > 0 && uint64(state.MaxHealth - state.Health) == taken;
        bool const passed = result.TankSurvived && !result.ActorDied && result.ElapsedMs == setup.DurationMs &&
            result.Swings.size() >= 25 && taken > 0 && healthOk;
        LogVerdict(name, passed, Acore::StringFormat("survived {}, died {}, elapsed {} ms of {} ms, {} swings, {} "
            "damage recorded, health {} of {} at the end (lost {}, expected to equal the recorded damage).",
            result.TankSurvived ? "yes" : "NO", result.ActorDied ? "YES" : "no", result.ElapsedMs, setup.DurationMs,
            result.Swings.size(), taken, state.Health, state.MaxHealth, state.MaxHealth - state.Health));
        return passed;
    }

    // Tank test 7/8 (tank.thunderclap_slow): Thunder Clap cast on the boss at the pull (TankPullAuras) slows its
    // swing by its haste aura's amount: a -10 melee haste makes the attack time 2000 x (100 + 10) / 100 = 2200 ms
    // (Unit::ApplyAttackTimePercentMod), read from the aura on the dummy. The run lasts the debuff's duration (10 s in
    // the live spell_dbc), so every gap between two swings must be exactly that (2200 sits on the 100 ms step grid);
    // a control run without the debuff swings every 2000 ms exactly.
    bool RunTankThunderClapSlowTest()
    {
        char const* const name = "tank.thunderclap_slow test";
        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_THUNDER_CLAP);
        if (!info || info->GetMaxDuration() <= 0)
        {
            LogVerdict(name, false, "Thunder Clap (6343) is missing or has no duration.");
            return false;
        }

        struct State
        {
            bool Read = false;
            uint32 AttackTime = 0;
            int32 HasteAmount = 0;
        } state;

        TankSetup slowed;
        slowed.Hit = {100, 100};
        slowed.Crit = false;
        slowed.SwingMs = 2000;
        // Only while the debuff is up (applied at the pull): the swings of the run all fall inside it
        slowed.DurationMs = std::min(uint32(info->GetMaxDuration()), 25000u);
        slowed.PullAuras = {SPELL_THUNDER_CLAP};
        slowed.Hook = [&state](uint32 elapsedMs, Player*, std::vector<Creature*> const& dummies)
        {
            if (state.Read || elapsedMs < 500 || dummies.empty())
                return;
            state.Read = true;
            Creature* boss = dummies.front();
            // GetAttackTime() divides the haste out (the unhasted base); the swing timer resets to base x haste
            state.AttackTime = uint32(std::lround(boss->GetAttackTime(BASE_ATTACK) *
                boss->m_modAttackSpeedPct[BASE_ATTACK]));
            for (AuraType type : {SPELL_AURA_MOD_MELEE_HASTE, SPELL_AURA_MOD_MELEE_RANGED_HASTE})
                for (AuraEffect const* aurEff : boss->GetAuraEffectsByType(type))
                    if (aurEff->GetId() == SPELL_THUNDER_CLAP)
                        state.HasteAmount += aurEff->GetAmount();
        };

        SimDaemon::RunResult slowedResult;
        if (!RunTankScenario(name, slowed, slowedResult))
            return false;

        TankSetup control = slowed;
        control.PullAuras.clear();
        control.Hook = nullptr;
        control.DurationMs = 12000;
        SimDaemon::RunResult controlResult;
        if (!RunTankScenario(name, control, controlResult))
            return false;

        // A negative haste amount slows: the attack time is multiplied by (100 - amount) / 100
        uint32 const expected = state.HasteAmount < 0 ?
            uint32(std::lround(2000.0 * (100.0 - double(state.HasteAmount)) / 100.0)) : 0;

        auto const allGaps = [](std::vector<uint32> const& times, uint32 gap)
        {
            for (size_t i = 1; i < times.size(); ++i)
                if (times[i] - times[i - 1] != gap)
                    return false;
            return times.size() >= 3;
        };

        std::vector<uint32> const slowedTimes = SwingTimes(slowedResult, 0);
        std::vector<uint32> const controlTimes = SwingTimes(controlResult, 0);
        bool const passed = expected == 2200 && state.AttackTime == expected && allGaps(slowedTimes, expected) &&
            allGaps(controlTimes, 2000);
        LogVerdict(name, passed, Acore::StringFormat("Thunder Clap haste amount {} on the boss -> expected attack time "
            "{} ms (2200 expected), read {} ms; slowed gaps {} (first swing at {} ms); control gaps {} (all 2000 "
            "expected).", state.HasteAmount, expected, state.AttackTime, GapHistogram(slowedTimes),
            slowedTimes.empty() ? 0 : slowedTimes.front(), GapHistogram(controlTimes)));
        return passed;
    }

    // Tank test 8/8 (tank.stun_immune): Concussion Blow (triggered, from the bare silenced warrior) at 3 s.
    //  - On the boss dummy (stun immune, plan T8): it is never stunned (no stun aura, no stunned state at any step),
    //    every swing gap stays one interval (2000 ms, +-one step) and it swings during the stun's duration.
    //  - On pack dummy #0 of two (elites stay stunnable): it is stunned right after the cast, lands no swing until the
    //    stun's duration (the spell's max duration) has run, swings again afterwards; dummy #1 keeps its 2000 ms gaps.
    bool RunTankStunImmuneTest()
    {
        char const* const name = "tank.stun_immune test";
        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_CONCUSSION_BLOW);
        if (!info || info->GetMaxDuration() <= 0)
        {
            LogVerdict(name, false, "Concussion Blow (12809) is missing or has no duration.");
            return false;
        }
        uint32 const stunMs = uint32(info->GetMaxDuration());

        struct State
        {
            uint32 CastMs = 0;
            uint32 StunnedSteps = 0;
        };

        auto const makeHook = [](State& state)
        {
            return [&state](uint32 elapsedMs, Player* actor, std::vector<Creature*> const& dummies)
            {
                if (dummies.empty())
                    return;
                Creature* target = dummies.front();
                if (state.CastMs == 0 && elapsedMs >= 3000)
                {
                    state.CastMs = elapsedMs;
                    actor->CastSpell(target, SPELL_CONCUSSION_BLOW, true);
                }
                if (state.CastMs > 0 &&
                    (target->HasUnitState(UNIT_STATE_STUNNED) || target->HasAuraType(SPELL_AURA_MOD_STUN)))
                    ++state.StunnedSteps;
            };
        };

        TankSetup setup;
        setup.Hit = {100, 100};
        setup.PackHit = {100, 100};
        setup.Crit = false;
        setup.SwingMs = 2000;
        setup.DurationMs = 3000 + stunMs + 8000;

        State bossState;
        setup.Hook = makeHook(bossState);
        SimDaemon::RunResult boss;
        if (!RunTankScenario(name, setup, boss))
            return false;

        State packState;
        setup.Targets = 2;
        setup.Hook = makeHook(packState);
        SimDaemon::RunResult pack;
        if (!RunTankScenario(name, setup, pack))
            return false;

        auto const maxGap = [](std::vector<uint32> const& times)
        {
            uint32 gap = 0;
            for (size_t i = 1; i < times.size(); ++i)
                gap = std::max(gap, times[i] - times[i - 1]);
            return gap;
        };
        auto const countIn = [](std::vector<uint32> const& times, uint32 fromMs, uint32 toMs)
        {
            uint32 count = 0;
            for (uint32 t : times)
                count += t > fromMs && t < toMs;
            return count;
        };

        std::vector<uint32> const bossTimes = SwingTimes(boss, 0);
        std::vector<uint32> const packStunned = SwingTimes(pack, 0);
        std::vector<uint32> const packOther = SwingTimes(pack, 1);
        uint32 const stunEnd = packState.CastMs + stunMs;

        bool const bossOk = bossState.CastMs > 0 && bossState.StunnedSteps == 0 &&
            maxGap(bossTimes) <= 2000 + TANK_TEST_STEP_MS && countIn(bossTimes, bossState.CastMs,
            bossState.CastMs + stunMs) >= 1;
        bool const packOk = packState.CastMs > 0 && packState.StunnedSteps > 0 &&
            countIn(packStunned, packState.CastMs, stunEnd - TANK_TEST_STEP_MS) == 0 &&
            countIn(packStunned, stunEnd - TANK_TEST_STEP_MS, 0xFFFFFFFF) >= 1 &&
            maxGap(packOther) <= 2000 + TANK_TEST_STEP_MS && packOther.size() >= 3;

        bool const passed = bossOk && packOk;
        LogVerdict(name, passed, Acore::StringFormat("Concussion Blow stun {} ms. Boss (cast at {} ms): stunned at {} "
            "step(s) (0 expected), gaps {}, {} swing(s) during the stun window. Pack dummy #0 (cast at {} ms): stunned "
            "at {} step(s), {} swing(s) before {} ms (0 expected), gaps {}; dummy #1 gaps {}.", stunMs,
            bossState.CastMs, bossState.StunnedSteps, GapHistogram(bossTimes),
            countIn(bossTimes, bossState.CastMs, bossState.CastMs + stunMs), packState.CastMs, packState.StunnedSteps,
            countIn(packStunned, packState.CastMs, stunEnd - TANK_TEST_STEP_MS), stunEnd, GapHistogram(packStunned),
            GapHistogram(packOther)));
        return passed;
    }

}

void SimTests::RunAll()
{
    // DpsSim.TestFilter: run only the tests whose key contains this text (case-insensitive), e.g. "heal" for the
    // healing-sim tests, "heal-shield" for one of them or "tank." for the tank-sim tests. Empty runs everything.
    std::string const filter = sConfigMgr->GetOption<std::string>("DpsSim.TestFilter", "");

    struct Test
    {
        char const* Key;
        bool (*Run)();
    };
    static Test const tests[] =
    {
        {"known-value", RunKnownValueTest},
        {"timestep", RunTimestepTest},
        {"accelerated-clock", RunAcceleratedClockTest},
        {"no-persist", RunNoPersistTest},
        {"heal-flash", RunHealFlashHealTest},
        {"heal-drain", RunHealDrainDeathTest},
        {"heal-shield", RunHealShieldTest},
        {"heal-hot", RunHealHotTest},
        {"heal-pushback", RunHealPushbackTest},
        {"heal-guardian", RunHealGuardianSpiritTest},
        {"tank.outcomes", RunTankOutcomesTest},
        {"tank.crit_immune", RunTankCritImmuneTest},
        {"tank.hit_formula", RunTankHitFormulaTest},
        {"tank.revenge", RunTankRevengeTest},
        {"tank.ttd", RunTankTtdTest},
        {"tank.survived", RunTankSurvivedTest},
        {"tank.thunderclap_slow", RunTankThunderClapSlowTest},
        {"tank.stun_immune", RunTankStunImmuneTest},
    };

    LOG_INFO("server.dpssim", "mod-dpssim: SimTests::RunAll() - running Phase 1's three required tests, the "
        "no-persist guard, the six healing-sim and the eight tank-sim known-value tests{}.",
        filter.empty() ? std::string() : Acore::StringFormat(" (filter '{}')", filter));

    uint32 ran = 0;
    uint32 passed = 0;
    for (Test const& test : tests)
    {
        if (!filter.empty() && !StringContainsStringI(test.Key, filter))
            continue;

        ++ran;
        passed += test.Run() ? 1 : 0;
    }

    LOG_INFO("server.dpssim", "mod-dpssim: SimTests::RunAll() complete - {}/{} tests passed.", passed, ran);
}
