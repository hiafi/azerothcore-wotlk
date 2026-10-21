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
#include "DatabaseEnv.h"
#include "Log.h"
#include "Player.h"
#include "QueryResult.h"
#include "SimActor.h"
#include "SimDaemon.h"
#include "SimHeal.h"
#include "SimProfile.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "Util.h"
#include <algorithm>
#include <cmath>
#include <functional>
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
}

void SimTests::RunAll()
{
    // DpsSim.TestFilter: run only the tests whose key contains this text (case-insensitive), e.g. "heal" for the
    // healing-sim tests or "heal-shield" for one of them. Empty runs everything.
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
    };

    LOG_INFO("server.dpssim", "mod-dpssim: SimTests::RunAll() - running Phase 1's three required tests, the "
        "no-persist guard and the six healing-sim known-value tests{}.",
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
