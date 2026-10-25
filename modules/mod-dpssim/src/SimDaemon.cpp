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
#include "CellImpl.h"
#include "Config.h"
#include "DamageTakenRecorder.h"
#include "EventRecorder.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "HealRecorder.h"
#include "Log.h"
#include "Map.h"
#include "Pet.h"
#include "Player.h"
#include "Playerbots.h"
#include "SimActor.h"
#include "SimBot.h"
#include "SimClock.h"
#include "SimDummyAI.h"
#include "SimHealScenario.h"
#include "SimReport.h"
#include "SimTank.h"
#include "SimTankDummyAI.h"
#include "SimTarget.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Timer.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iterator>
#include <list>
#include <map>
#include <set>
#include <string>
#include <thread>

namespace
{
    // See SimDaemon.h's RunResult::ManaSamples doc comment for why this is a periodic sample
    // rather than a per-tick or per-event capture.
    constexpr uint32 MANA_SAMPLE_INTERVAL_MS = 500;
    // The same cadence for the power / rune samples (RunResult::PowerSamples, the tank run's TANK_SAMPLE_INTERVAL_MS)
    constexpr uint32 POWER_SAMPLE_INTERVAL_MS = 500;

    // Sim time skipped before each playerbot iteration (see RunPlayerbotIteration()): long enough for
    // everything time-based the iteration reset doesn't clear to age out - the GCD, queued action baskets
    // (5 s), value check intervals, the 5-second mana rule, diminishing returns,
    // and UseTrinketAction's own cooldown maps for combat trinkets (5 min or less) - so every iteration,
    // the first included, starts the same way. AllowActivity()'s cache is not left to the gap: the pre-pull buff
    // phase refills it out of combat, so SimBot::ReestablishCombatState() re-checks it at the pull. A few utility
    // trinkets (20 min to 3 h) are not covered; a
    // longer gap would cut the uint32 clock's headroom (~5,500 iterations of 180 s at this gap).
    constexpr uint32 ITERATION_GAP_MS = 10 * MINUTE * IN_MILLISECONDS;

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

    // Appends a power sample (and, for a Death Knight, the ready runes by type) if at least POWER_SAMPLE_INTERVAL_MS
    // has passed since the last one (or this is the first tick). Called next to MaybeSampleMana() by the two runs that
    // feed a DPS-shaped report: the playerbot DPS run and the tank run
    void MaybeSamplePower(Player* actor, uint32 nowMs, uint32& lastSampleMs, bool& sampledOnce,
        std::vector<SimDaemon::RunResult::PowerSample>& samples)
    {
        if (sampledOnce && nowMs - lastSampleMs < POWER_SAMPLE_INTERVAL_MS)
            return;

        SimDaemon::RunResult::PowerSample sample;
        sample.TimestampMs = nowMs;
        Powers const type = actor->getPowerType();
        sample.PowerType = uint8(type);
        sample.Power = actor->GetPower(type);
        sample.MaxPower = actor->GetMaxPower(type);
        if (actor->getClass() == CLASS_DEATH_KNIGHT)
        {
            sample.HasRunes = true;
            for (uint8 slot = 0; slot < MAX_RUNES; ++slot)
            {
                if (actor->GetRuneCooldown(slot) != 0)
                    continue;

                switch (actor->GetCurrentRune(slot))
                {
                    case RUNE_BLOOD:
                        ++sample.RunesBlood;
                        break;
                    case RUNE_FROST:
                        ++sample.RunesFrost;
                        break;
                    case RUNE_UNHOLY:
                        ++sample.RunesUnholy;
                        break;
                    case RUNE_DEATH:
                        ++sample.RunesDeath;
                        break;
                    default:
                        break;
                }
            }
        }

        samples.push_back(sample);
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
            result.push_back({e.TimestampMs, e.UnitGuid, e.IsActor, e.SpellId, e.StackAmount, e.Positive, e.Applied,
                e.TargetIndex});
        return result;
    }

    // Same decoupling reasoning as ToRunResultAuraEvents() above, for CastRecorder::CastEvent.
    std::vector<SimDaemon::RunResult::CastEvent> ToRunResultCastEvents(std::vector<CastRecorder::CastEvent> const& events)
    {
        std::vector<SimDaemon::RunResult::CastEvent> result;
        result.reserve(events.size());
        for (CastRecorder::CastEvent const& e : events)
            result.push_back({e.TimestampMs, e.SpellId, e.IsTriggered, e.TargetIndex, e.PowerCost});
        return result;
    }

    // Every dummy of a run spawns with the same settings
    SimTarget::Config MakeTargetConfig(SimDaemon::RunConfig const& config)
    {
        SimTarget::Config targetConfig;
        targetConfig.Level = uint8(config.TargetLevel);
        targetConfig.TargetRank = config.TargetRank;
        targetConfig.Armor = config.TargetArmor;
        targetConfig.HealthDrain = config.DummyHealthDrain;
        if (config.DummyMaxHealth > 0)
            targetConfig.MaxHealth = config.DummyMaxHealth;
        return targetConfig;
    }

    void RefillResources(Player* player, std::vector<Creature*> const& dummies);

    // Once per process, at the first pull: warns about units near the pack that would close the bots' AoE safety
    // gate ("unsafe aoe units" counts any attackable unit out of combat), e.g. a Wild Turkey near the race start.
    // Without this an AoE row that never fires has no visible cause.
    void WarnStrayUnitsOnce(Player* player, std::vector<Creature*> const& dummies)
    {
        static bool warned = false;
        if (warned || dummies.empty() || !dummies.front())
            return;
        warned = true;

        constexpr float STRAY_SEARCH_RANGE = 40.0f;
        Creature* primary = dummies.front();
        std::list<Unit*> units;
        Acore::AnyUnfriendlyNoTotemUnitInObjectRangeCheck check(primary, player, STRAY_SEARCH_RANGE);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyNoTotemUnitInObjectRangeCheck> searcher(primary, units, check);
        Cell::VisitObjects(primary, searcher, STRAY_SEARCH_RANGE);

        std::string list;
        for (Unit* unit : units)
        {
            if (std::find(dummies.begin(), dummies.end(), unit) != dummies.end() || !unit->IsAlive() ||
                !player->IsValidAttackTarget(unit) || unit->GetCreatureType() == CREATURE_TYPE_CRITTER ||
                unit->IsInCombat())
                continue;

            list += Acore::StringFormat("{}{} '{}' at {:.1f} yd", list.empty() ? "" : ", ", unit->GetEntry(),
                unit->GetName(), primary->GetExactDist(unit));
        }

        if (!list.empty())
            LOG_WARN("server.dpssim", "mod-dpssim: units within {:.0f} yd of the dummies that are attackable and out "
                "of combat: {}. AoE safety gates will stay closed; try another race start, e.g. Orc (2).",
                STRAY_SEARCH_RANGE, list);
    }

    // Logs the bot's own non-passive auras by spell id, so a reviewer can confirm what is up at the pull (e.g.
    // Retribution Aura 7294). Only when the set differs from the last one logged, so a long batch logs it once.
    void LogAurasAtPull(Player* player)
    {
        static std::set<uint32> lastLogged;
        static bool loggedOnce = false;

        std::set<uint32> ids;
        for (auto const& [spellId, aurApp] : player->GetAppliedAuras())
        {
            SpellInfo const* info = aurApp->GetBase()->GetSpellInfo();
            if (info && !info->IsPassive())
                ids.insert(spellId);
        }

        std::string list;
        for (uint32 id : ids)
            list += (list.empty() ? "" : ", ") + std::to_string(id);
        if (loggedOnce && ids == lastLogged)
            return;

        loggedOnce = true;
        lastLogged = ids;
        LOG_INFO("server.dpssim", "mod-dpssim: auras on the bot at the pull: [{}]", list);
    }

    // Pre-pull buff phase (SimProfile.h's PrePullBuffMs): ticks the bot on its non-combat engine, buff and pet
    // strategies only (SimBot::BeginBuffPhase()), for `buffMs` of sim time ending at `endMs`, so the measured run
    // starts exactly where it always did. Unrecorded: the caller rewinds the recorders afterwards. Ends early if
    // the bot enters combat.
    void RunBuffPhase(SimDaemon::RunConfig const& config, uint32 buffMs, uint32 endMs, Player* player, Map* map,
        SimBot& bot, CastRecorder* castRecorder)
    {
        if (!bot.BeginBuffPhase())
            LOG_WARN("server.dpssim", "mod-dpssim: pre-pull buff phase - PlayerbotAI reports the bot inactive out of "
                "combat (AllowActivity() false), so only relevance >= 100 triggers will run; set "
                "Playerbots.BotActiveAlone = 100 and Playerbots.botActiveAloneSmartScale = 0 for the sim (run-sim.sh "
                "does).");

        SimClock buffClock(config.StepMs, endMs - buffMs);
        while (buffClock.GetElapsedMs() < buffMs)
        {
            buffClock.Tick(map);
            bot.UpdateAI(config.StepMs);

            if (player->IsInCombat())
            {
                std::vector<CastRecorder::CastEvent> const& casts = castRecorder->GetCastEvents();
                Unit* with = player->GetCombatManager().GetAnyTarget();
                Pet* pet = player->GetPet();
                LOG_WARN("server.dpssim", "mod-dpssim: pre-pull buff phase ended early at {} ms - the bot entered "
                    "combat with {} (entry {}), pet in combat: {}; the bot's last cast spell {}.",
                    buffClock.GetElapsedMs(), with ? with->GetName() : "nothing", with ? with->GetEntry() : 0,
                    pet && pet->IsInCombat() ? "yes" : "no", casts.empty() ? 0 : casts.back().SpellId);
                break;
            }

            if (config.RealTimePaced)
                std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
        }

        // A cast still going at the pull (a 10 s pet summon started late) would open the measured fight, landing
        // after its cost was refilled. Cut it off: the next iteration's phase starts it again with the pet still
        // missing.
        for (CurrentSpellTypes type : {CURRENT_GENERIC_SPELL, CURRENT_CHANNELED_SPELL})
        {
            if (Spell const* spell = player->GetCurrentSpell(type))
            {
                LOG_WARN("server.dpssim", "mod-dpssim: pre-pull buff phase ended with spell {} still being cast - "
                    "interrupted; raise PrePullBuffMs if this repeats.", spell->m_spellInfo->Id);
            }
        }
        player->InterruptNonMeleeSpells(false);

        bot.EndBuffPhase();
    }

    // The tick loop + result population shared by RunPlayerbotOnce() (one call) and
    // RunPlayerbotBatch() (one call per iteration, same actor/target/bot/recorders reused every
    // time - see that function's own doc comment). Assumes `recorder`/`castRecorder` are already
    // rewound (a fresh EventRecorder/CastRecorder for RunPlayerbotOnce(), an explicit ->Reset() call
    // for every iteration but the first in RunPlayerbotBatch()) - result population aside, the one
    // thing this function does reset itself is spell cooldowns (see below), since that has to
    // happen on every call, including RunPlayerbotBatch()'s first iteration which ResetForNextIteration()
    // never reaches.
    void RunPlayerbotIteration(SimDaemon::RunConfig const& config, Player* player,
        std::vector<Creature*> const& dummies, Map* map, SimBot& bot, EventRecorder* recorder,
        CastRecorder* castRecorder, SimDaemon::RunResult& result)
    {
        // Every iteration starts with nothing on cooldown: pre-loop casts (SimBot::Create()'s spell-teaching
        // casts, gear equip spells) and the previous iteration's cooldowns would otherwise carry over.
        player->RemoveAllSpellCooldown();

        // A hunter run keeps its pet for every iteration: revived if it died, tamed again if it is gone (the
        // iteration reset resurrects a dead actor, which drops its permanent pet). Before the pre-pull buff phase,
        // which then treats it like any other pet of the actor.
        if (!bot.EnsurePet())
            LOG_ERROR("server.dpssim", "mod-dpssim: the hunter pet could not be restored for this iteration - it runs "
                "without one.");

        // The same for aura-held proc internal cooldowns (Aura::m_procCooldown): ResetForNextIteration()
        // removes every non-passive aura, but the passive talent/racial auras stay. Proc ICDs (and the script-held
        // ones, e.g. spell_mage_biting_cold's _cooldownEnd) now run on the sim clock (Acore::Time::SteadyNow()),
        // but the clock jumps ITERATION_GAP_MS between iterations anyway - script-held ones age out by that.
        for (auto const& [spellId, aura] : player->GetOwnedAuras())
            aura->ResetProcCooldown();

        // The sim clock must never run backward. Playerbot values and triggers stamp getMSTime(), and
        // CalculatedValue::Get() compares a time_t "now" against a uint32 lastCheckTime: with a stamp in the
        // future the difference goes negative and the value is never recalculated. When every iteration
        // restarted the clock at 0, each interval-cached value froze at its end-of-previous-iteration state
        // for the whole run (2026-10-05, RetPaladinSim: iterations 2-10 locked onto one seal). So the clock
        // starts ITERATION_GAP_MS past "now" - the wall clock before the first iteration, the previous
        // iteration's last tick after that - and the recorded timestamps are rebased to the iteration start
        // below. GameTime's cached value can disagree with getMSTime() during setup (DpsSim.cpp clears the
        // override without refreshing GameTime, leaving it at 5000 ms), so "now" is the later of the two.
        uint32 const nowMs = std::max(getMSTime(), uint32(GameTime::GetGameTimeMS().count()));
        uint32 const measuredStartMs = nowMs + ITERATION_GAP_MS;

        // Pre-pull buff phase, at the end of the gap (S0b). After the cooldown reset above on purpose: cooldowns it
        // starts (an aura press) carry into the fight, as in game. Its recorder output is rewound, its resource
        // spending refilled, then the pull is exactly what ResetForNextIteration()/Create() already did.
        // The measured clock still starts at measuredStartMs, so report timestamps begin at 0 and the sim clock
        // never runs backward (the last buff tick is one step before measuredStartMs).
        if (config.PrePullBuffMs > 0)
        {
            uint32 const buffMs = std::min(config.PrePullBuffMs, ITERATION_GAP_MS);
            RunBuffPhase(config, buffMs, measuredStartMs, player, map, bot, castRecorder);
            recorder->Reset();
            castRecorder->Reset();
            // Buffs from the phase are up from the first measured ms; without these the uptime table only sees
            // auras applied during the fight
            recorder->RecordAurasPresent(player);
            for (Creature* dummy : dummies)
                recorder->RecordAurasPresent(dummy);
            RefillResources(player, dummies);
            bot.ReestablishCombatState(dummies);
        }
        LogAurasAtPull(player);
        // The primary dummy's armor at the pull: a recalculation restoring the template armor would show here.
        LOG_INFO("server.dpssim", "mod-dpssim: iteration pull - dummy armor {}, maxHealth {}.",
            dummies.front()->GetArmor(), dummies.front()->GetMaxHealth());
        WarnStrayUnitsOnce(player, dummies);

        SimClock clock(config.StepMs, measuredStartMs);
        uint32 lastManaSampleMs = 0;
        bool sampledManaOnce = false;
        std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
        uint32 lastPowerSampleMs = 0;
        bool sampledPowerOnce = false;
        std::vector<SimDaemon::RunResult::PowerSample> powerSamples;
        // The bot's own current target, seeded with the primary at the pull (D5: measured, not inferred from casts)
        ObjectGuid lastTarget = bot.GetCurrentTarget();
        uint32 targetSwitches = 0;
        while (clock.GetElapsedMs() < config.DurationMs)
        {
            clock.Tick(map);

            // A dead actor ends the iteration before auto release can run. The sim bot is registered with
            // PlayerbotsMgr, so PlayerbotsPlayerScript::OnPlayerAfterUpdate also ticks its AI inside
            // clock.Tick -> Map::Update -> Player::Update. A death from a periodic tick lands inside
            // Player::Update, before that hook; the first dead tick only switches the bot to the DEAD engine and
            // auto release (ReleaseSpiritAction -> repop at graveyard -> teleport nobody acknowledges) needs a
            // second tick, so checking after every Tick stops the iteration in time. Ending here leaves the corpse
            // in place for ResetForNextIteration() to resurrect, which also has ReestablishCombatState() switch the
            // bot back to the combat engine.
            if (!player->IsAlive())
            {
                result.ActorDied = true;
                result.ActorDiedAtMs = clock.GetElapsedMs();
                LOG_WARN("server.dpssim", "mod-dpssim: the actor DIED {} ms into the iteration - iteration ended, "
                    "its DPS counts the full {} ms.", result.ActorDiedAtMs, config.DurationMs);
                break;
            }

            bot.UpdateAI(config.StepMs);
            MaybeSampleMana(player, clock.GetElapsedMs(), lastManaSampleMs, sampledManaOnce, manaSamples);
            MaybeSamplePower(player, clock.GetElapsedMs(), lastPowerSampleMs, sampledPowerOnce, powerSamples);

            ObjectGuid const currentTarget = bot.GetCurrentTarget();
            if (!currentTarget.IsEmpty())
            {
                if (!lastTarget.IsEmpty() && currentTarget != lastTarget)
                    ++targetSwitches;
                lastTarget = currentTarget;
            }

            // Only for the accelerated-clock test - see RunConfig::RealTimePaced's doc comment.
            if (config.RealTimePaced)
                std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
        }

        // A death in the final step: the loop condition ends the loop before the check above sees it
        if (!result.ActorDied && !player->IsAlive())
        {
            result.ActorDied = true;
            result.ActorDiedAtMs = config.DurationMs;
        }

        result.Success = true;
        // Deliberate: an actor that died is charged the full configured duration, not the time it survived, so
        // dying costs DPS (a self-killing rotation must read as low DPS, not as a short burst of high DPS)
        result.ElapsedMs = result.ActorDied ? config.DurationMs : clock.GetElapsedMs();
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
        result.HitIsPet = recorder->GetHitIsPet();
        result.HitTargetIndex = recorder->GetHitTargetIndex();
        result.TargetSwitches = targetSwitches;
        result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
        result.ManaSamples = std::move(manaSamples);
        result.PowerSamples = std::move(powerSamples);
        result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());

        // Recorders stamp raw getMSTime(); reports count from the iteration start. An event recorded before
        // the first tick (setup, e.g. SimBot::Create()'s spell-teaching casts and talent passive auras)
        // clamps to 0.
        uint32 const startMs = clock.GetStartMs();
        auto const rebase = [startMs](uint32& timestampMs)
        {
            timestampMs = timestampMs >= startMs ? timestampMs - startMs : 0;
        };
        for (uint32& timestampMs : result.HitTimestamps)
            rebase(timestampMs);
        for (SimDaemon::RunResult::AuraEvent& e : result.AuraEvents)
            rebase(e.TimestampMs);
        for (SimDaemon::RunResult::CastEvent& e : result.CastEvents)
            rebase(e.TimestampMs);
    }

    // Health and every power type back to the class's starting value, for the bot, its pet and (with health drain
    // on) every dummy. Run by ResetForNextIteration() and again after the pre-pull buff phase, so the buff casts'
    // mana/rage/energy costs never reach the fight.
    void RefillResources(Player* player, std::vector<Creature*> const& dummies)
    {
        player->SetFullHealth();
        player->SetPower(POWER_MANA, player->GetMaxPower(POWER_MANA));

        // The other power types back to the class's starting value: full for energy and focus, empty for rage and
        // runic power (a class lacking a type has max 0 there, so setting it is a no-op), runes ready, combo
        // points cleared. Without this a rage/runic-power spec started every iteration after the first with
        // whatever the last fight left behind.
        player->SetPower(POWER_ENERGY, player->GetMaxPower(POWER_ENERGY));
        player->SetPower(POWER_FOCUS, player->GetMaxPower(POWER_FOCUS));
        player->SetPower(POWER_RAGE, 0);
        player->SetPower(POWER_RUNIC_POWER, 0);
        if (player->getClass() == CLASS_DEATH_KNIGHT)
            for (uint8 rune = 0; rune < MAX_RUNES; ++rune)
            {
                player->SetRuneCooldown(rune, 0);
                player->SetGracePeriod(rune, 0);
            }
        player->ClearComboPoints();

        // The bot's pet: health and power full (rage/runic power empty)
        if (Pet* pet = player->GetPet())
        {
            pet->SetFullHealth();
            for (uint8 power : {POWER_MANA, POWER_FOCUS, POWER_ENERGY})
                pet->SetPower(Powers(power), pet->GetMaxPower(Powers(power)));
            pet->SetPower(POWER_RAGE, 0);
            pet->SetPower(POWER_RUNIC_POWER, 0);
            pet->ClearComboPoints();
        }

        // Dummy health drain (SimProfile.h's DummyHealthDrain): the dummy takes real damage now, so it starts every
        // iteration at full health. Off, the dummy never loses health and there is nothing to reset.
        if (SimDummyAI::IsHealthDrainEnabled())
            for (Creature* dummy : dummies)
                dummy->SetFullHealth();
    }

    // Between-iteration reset for RunPlayerbotBatch() - see that function's doc comment (SimDaemon.h)
    // for the full reasoning, especially the passive-aura carve-out and SimBot::ReestablishCombatState()'s
    // own doc comment for the real failure this also guards against (a batch's first iteration
    // landing real hits, then every iteration after it landing zero, forever). The target dummies' health is only
    // refilled with health drain on (otherwise its AI zeroes all damage taken, so it never drops); the global
    // cooldown is left alone (RunPlayerbotIteration() starts each iteration ITERATION_GAP_MS later, by which time
    // it has long expired).
    void ResetForNextIteration(Player* player, std::vector<Creature*> const& dummies, SimBot& bot,
        EventRecorder* recorder, CastRecorder* castRecorder, Position const& startPosition)
    {
        // The actor can die (a rotation that hurts itself, e.g. Shadow Word: Death backlash).
        // RunPlayerbotIteration() ends the iteration the moment it does, before the AI's auto release can repop it,
        // so it is normally still a corpse in place here. The safety net: if a release teleport did start, the sim
        // bot (in no PlayerbotHolder) would never acknowledge it, IsBeingTeleported() would stay true and
        // PlayerbotAI::UpdateAI() would return early for the rest of the batch - so acknowledge it and drop the
        // corpse before resurrecting. RefillResources() below brings health and mana back to full.
        // A dead player also loses its permanent pet (warlock/hunter...); only the pre-pull buff phase brings it
        // back, so a pet class that died runs the next iteration petless unless that phase summons it.
        bool const releaseTeleportStarted = player->IsBeingTeleported();
        if (releaseTeleportStarted)
        {
            LOG_WARN("server.dpssim", "mod-dpssim: the actor was mid-teleport at the iteration reset - the death "
                "check in RunPlayerbotIteration() failed to stop the auto release in time; acknowledging it.");
            bot.HandleTeleportAck();
        }
        if (!player->IsAlive())
        {
            // false: no ghost/aura rows - the actor has no characters row (SimActor.cpp, zero SQL)
            if (player->GetCorpse())
                player->SpawnCorpseBones(false);
            player->ResurrectPlayer(1.0f);
        }
        if (releaseTeleportStarted)
        {
            // Back from the graveyard to where the iteration started
            player->NearTeleportTo(startPosition.GetPositionX(), startPosition.GetPositionY(),
                startPosition.GetPositionZ(), startPosition.GetOrientation());
            bot.HandleTeleportAck();
        }

        // Nothing the last fight left running reaches the next one: a cast in progress, totems, ground effects
        // (DynamicObjects; a Lightwell is a totem) and temporary guardians (Wild Imps, Treants...). The permanent
        // pet stays and is reset below.
        player->InterruptNonMeleeSpells(false);
        player->UnsummonAllTotems();
        player->RemoveAllDynObjects();
        std::vector<TempSummon*> guardians;
        for (Unit* unit : player->m_Controlled)
            if (unit && unit->IsGuardian() && !unit->IsPet())
                guardians.push_back(unit->ToTempSummon());
        for (TempSummon* guardian : guardians)
            if (guardian)
                guardian->UnSummon();

        // Every aura the fight put on, and nothing the character is: non-passive auras, plus passive-flagged ones with
        // a duration. A timed passive is a spell's delay holder, never a talent or an item's equip aura (those are
        // permanent), and it would fire into the next iteration: Thunderstruck's echo holder (200066,
        // SPELL_ATTR0_PASSIVE, 3 s PERIODIC_TRIGGER_SPELL of Thunder Clap Echo 200065) applied in the last 3 s of a
        // fight survived the reset, ticked during the next pre-pull buff phase and put the bot in combat there ("ended
        // early ... last cast spell 200065"). Removing an aura does not run its periodic trigger, so nothing it holds
        // goes off.
        auto removeNonPassive = [](AuraApplication const* aurApp)
        {
            Aura const* aura = aurApp->GetBase();
            SpellInfo const* info = aura->GetSpellInfo();
            return !info || !info->IsPassive() || !aura->IsPermanent();
        };
        player->RemoveAppliedAuras(removeNonPassive);
        for (Creature* dummy : dummies)
            dummy->RemoveAppliedAuras(removeNonPassive);

        // Not resetting cooldowns here - RunPlayerbotIteration() itself now does that
        // unconditionally at the start of every call, including this one.

        // The bot's pet (warlock/hunter/DK/mage elemental...): same fresh start as the bot - cooldowns and spell
        // school lockouts gone, non-passive auras off (health and power are refilled by RefillResources() below).
        if (Pet* pet = player->GetPet())
        {
            pet->m_CreatureSpellCooldowns.clear();
            std::fill(std::begin(pet->m_ProhibitSchoolTime), std::end(pet->m_ProhibitSchoolTime), 0u);
            pet->RemoveAppliedAuras(removeNonPassive);
        }

        RefillResources(player, dummies);

        bot.ReestablishCombatState(dummies);

        recorder->Reset();
        castRecorder->Reset();
    }

    // ---- Heal mode (the heal branch of RunPlayerbotBatch(); plan .agents/plans/healing-sim/healing-sim.PLAN.md) ----

    // One heal-mode iteration, the counterpart of RunPlayerbotIteration(): the same pre-pull buff phase and sim clock
    // rules, then the pull (SimHealScenario::Pull()) and a tick loop in which the scenario's drivers damage the group
    // and the healer's bot heals it. Assumes the recorders are rewound (ResetForNextIteration() does that between
    // iterations; the first iteration has nothing recorded yet) and the allies reset (SimHealScenario::ResetAllies()).
    void RunHealIteration(SimDaemon::RunConfig const& config, Player* player, Map* map, SimBot& bot,
        SimHealScenario& scenario, EventRecorder* recorder, CastRecorder* castRecorder, HealRecorder* healRecorder,
        SimDaemon::RunResult& result)
    {
        auto const wallStart = std::chrono::steady_clock::now();
        Creature* boss = scenario.GetBoss();
        std::vector<Creature*> const bossList = {boss};

        // Same start-of-iteration housekeeping as RunPlayerbotIteration()
        player->RemoveAllSpellCooldown();
        if (!bot.EnsurePet())
            LOG_ERROR("server.dpssim", "mod-dpssim: the hunter pet could not be restored for this iteration - it runs "
                "without one.");
        for (auto const& [spellId, aura] : player->GetOwnedAuras())
            aura->ResetProcCooldown();

        uint32 const nowMs = std::max(getMSTime(), uint32(GameTime::GetGameTimeMS().count()));
        uint32 const measuredStartMs = nowMs + ITERATION_GAP_MS;

        // The buff phase needs the whole group out of combat: a buff on an ally that is in combat pulls the healer into
        // combat (Spell::DoSpellHitOnUnit's assist rule) and ends the phase early. Afterwards the healer buffed the
        // group as it would in game; the recorders are rewound, its spending refilled and the pull engages everyone.
        if (config.PrePullBuffMs > 0)
        {
            scenario.EndCombat();
            uint32 const buffMs = std::min(config.PrePullBuffMs, ITERATION_GAP_MS);
            RunBuffPhase(config, buffMs, measuredStartMs, player, map, bot, castRecorder);
            recorder->Reset();
            castRecorder->Reset();
            healRecorder->Reset();
            recorder->RecordAurasPresent(player);
            recorder->RecordAurasPresent(boss);
            RefillResources(player, bossList);
            bot.ReestablishCombatState(bossList);
        }
        else
            healRecorder->Reset();

        // The auras on the group at the pull, with or without a buff phase, so uptime counts from the pull
        for (Player* member : scenario.GetMembers())
            healRecorder->RecordAurasPresent(member);

        scenario.Pull();
        LogAurasAtPull(player);

        // A scripted healer (tests): its AI must not act in the first Tick(), before the hook has run once
        if (config.HealStepHook)
            bot.SilenceAI();

        // Once per process: whether the bot's heal-target value can see the whole group (plan section 7, R2)
        static bool loggedVisibility = false;
        if (!loggedVisibility)
        {
            loggedVisibility = true;
            bot.LogHealTargetVisibility(scenario.GetMembers());
        }

        SimClock clock(config.StepMs, measuredStartMs);
        uint32 lastManaSampleMs = 0;
        bool sampledManaOnce = false;
        std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
        auto const noteActorDeath = [&](uint32 atMs)
        {
            result.ActorDied = true;
            result.ActorDiedAtMs = atMs;
            // Whatever found the death, the healer's slot is in Deaths
            scenario.RecordDeath(scenario.GetSelfIndex());
            LOG_WARN("server.dpssim", "mod-dpssim: the healer DIED {} ms into the iteration - iteration ended, its "
                "healing counts the full {} ms.", atMs, config.DurationMs);
        };

        while (clock.GetElapsedMs() < config.DurationMs)
        {
            clock.Tick(map);

            // The existing actor-death rule (RunPlayerbotIteration()): check after every Tick, before the AI's auto
            // release can run, and once more after the drivers, which can kill the healer when it is a drain target
            if (!player->IsAlive())
            {
                noteActorDeath(clock.GetElapsedMs());
                break;
            }

            scenario.Step(clock.GetElapsedMs());
            if (!player->IsAlive())
            {
                noteActorDeath(clock.GetElapsedMs());
                break;
            }

            // InfiniteMana: the healer starts every step with a full pool, so a cast is never refused for mana and
            // the mana samples stay near 100% (a pure-throughput run, plan D8)
            if (config.InfiniteMana)
                player->SetPower(POWER_MANA, player->GetMaxPower(POWER_MANA));

            if (config.HealStepHook)
            {
                bot.SilenceAI();
                config.HealStepHook(clock.GetElapsedMs(), player, scenario.GetMembers());
            }
            else
                bot.UpdateAI(config.StepMs);
            MaybeSampleMana(player, clock.GetElapsedMs(), lastManaSampleMs, sampledManaOnce, manaSamples);

            if (config.RealTimePaced)
                std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
        }

        if (!result.ActorDied && !player->IsAlive())
            noteActorDeath(config.DurationMs);

        result.Success = true;
        result.HealMode = true;
        result.ElapsedMs = result.ActorDied ? config.DurationMs : clock.GetElapsedMs();

        // The healer's damage to the boss (secondary), by the same recorder the DPS sim uses
        result.CastAttempts = recorder->GetCastCount();
        result.TotalDamage = recorder->GetTotalDamage();
        result.CastCount = recorder->GetCastCount();
        result.CritCount = recorder->GetCritCount();
        result.HitDamages = recorder->GetHitDamages();
        result.HitCrits = recorder->GetHitCrits();
        result.HitSpellIds = recorder->GetHitSpellIds();
        result.HitTimestamps = recorder->GetHitTimestamps();
        result.HitIsPet = recorder->GetHitIsPet();
        result.HitTargetIndex = recorder->GetHitTargetIndex();
        result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
        result.ManaSamples = std::move(manaSamples);
        result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());

        result.HealTargetInfo = scenario.GetTargetInfo();
        result.HealEvents = healRecorder->GetHealEvents();
        result.AbsorbEvents = healRecorder->GetAbsorbEvents();
        result.DamageTakenEvents = healRecorder->GetDamageEvents();
        result.GroupAuraEvents = healRecorder->GetAuraEvents();
        result.HealthSamples = scenario.GetHealthSamples();
        result.Deaths = scenario.GetDeaths();
        result.Resurrections = scenario.GetResurrections();
        result.PinHits = scenario.GetPinHits();
        result.PinRaises = scenario.GetPinRaises();
        result.DrainHits = scenario.GetDrainHits();
        result.DriverCastFailures = scenario.GetCastFailures();
        result.TargetPinHits = scenario.GetTargetPinHits();
        result.TargetPinRaises = scenario.GetTargetPinRaises();

        // Recorders stamp raw getMSTime(); reports count from the iteration start, and events before it clamp to 0
        uint32 const startMs = clock.GetStartMs();
        auto const rebase = [startMs](uint32& timestampMs)
        {
            timestampMs = timestampMs >= startMs ? timestampMs - startMs : 0;
        };
        for (uint32& timestampMs : result.HitTimestamps)
            rebase(timestampMs);
        for (SimDaemon::RunResult::AuraEvent& e : result.AuraEvents)
            rebase(e.TimestampMs);
        for (SimDaemon::RunResult::CastEvent& e : result.CastEvents)
            rebase(e.TimestampMs);
        for (SimHeal::HealEvent& e : result.HealEvents)
            rebase(e.TimestampMs);
        for (SimHeal::AbsorbEvent& e : result.AbsorbEvents)
            rebase(e.TimestampMs);
        for (SimHeal::DamageEvent& e : result.DamageTakenEvents)
            rebase(e.TimestampMs);
        for (SimHeal::GroupAuraEvent& e : result.GroupAuraEvents)
            rebase(e.TimestampMs);
        for (SimHeal::HealthSample& e : result.HealthSamples)
            rebase(e.TimestampMs);
        for (SimHeal::LifeEvent& e : result.Deaths)
            rebase(e.TimestampMs);
        for (SimHeal::LifeEvent& e : result.Resurrections)
            rebase(e.TimestampMs);

        result.WallClockMs = uint32(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - wallStart).count());
    }

    // One summary line per iteration plus a per-spell and a per-target line: HPS (effective healing plus absorbs, over
    // the full duration), effective, overheal, absorbs, deaths, the top 5 spells and the healing each target received.
    // HS1 is validated from these lines; HS2 writes the JSON report.
    void LogHealSummary(SimDaemon::RunResult const& result, uint32 iteration, uint32 iterations)
    {
        struct SpellTotals
        {
            uint64 Effective = 0;
            uint64 Overheal = 0;
            uint64 Absorbed = 0;
            uint32 Events = 0;
        };
        std::map<uint32, SpellTotals> spells;
        std::vector<uint64> received(result.HealTargetInfo.size(), 0);
        uint64 effective = 0, overheal = 0, absorbs = 0, raw = 0;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            effective += e.Effective;
            overheal += e.Overheal;
            raw += e.Raw;
            SpellTotals& totals = spells[e.SpellId];
            totals.Effective += e.Effective;
            totals.Overheal += e.Overheal;
            ++totals.Events;
            if (e.TargetIndex < received.size())
                received[e.TargetIndex] += e.Effective;
        }
        for (SimHeal::AbsorbEvent const& e : result.AbsorbEvents)
        {
            absorbs += e.Amount;
            SpellTotals& totals = spells[e.SpellId];
            totals.Absorbed += e.Amount;
            ++totals.Events;
            if (e.TargetIndex < received.size())
                received[e.TargetIndex] += e.Amount;
        }

        double const seconds = double(result.ElapsedMs) / 1000.0;
        double const hps = seconds > 0.0 ? double(effective + absorbs) / seconds : 0.0;
        double const overhealPct = raw > 0 ? 100.0 * double(overheal) / double(raw) : 0.0;

        uint32 oomAtMs = 0;
        for (SimDaemon::RunResult::ManaSample const& sample : result.ManaSamples)
            if (sample.ManaPct < 5.0f)
            {
                oomAtMs = std::max(sample.TimestampMs, 1u);
                break;
            }
        float const endMana = result.ManaSamples.empty() ? 0.0f : result.ManaSamples.back().ManaPct;

        std::string deaths;
        for (SimHeal::LifeEvent const& e : result.Deaths)
            deaths += Acore::StringFormat("{}#{}@{}ms", deaths.empty() ? "" : ", ", uint32(e.TargetIndex),
                e.TimestampMs);

        LOG_INFO("server.dpssim", "mod-dpssim:   heal iteration {}/{} - {} ms ({} wall ms): HPS {:.1f}, effective {}, "
            "overheal {} ({:.1f}%), absorbs {}, {} heal event(s), {} deaths [{}], {} resurrection(s), healer "
            "died: {}, OOM at {} ms, end mana {:.0f}%, {} damage to the boss.", iteration, iterations, result.ElapsedMs,
            result.WallClockMs, hps, effective, overheal, overhealPct, absorbs, result.HealEvents.size(),
            result.Deaths.size(), deaths, result.Resurrections.size(), result.ActorDied ? "yes" : "no", oomAtMs,
            endMana, result.TotalDamage);

        std::vector<std::pair<uint32, SpellTotals>> sorted(spells.begin(), spells.end());
        std::stable_sort(sorted.begin(), sorted.end(), [](auto const& a, auto const& b)
        {
            return a.second.Effective + a.second.Absorbed > b.second.Effective + b.second.Absorbed;
        });
        std::string top;
        for (size_t i = 0; i < sorted.size() && i < 5; ++i)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(sorted[i].first);
            top += Acore::StringFormat("{}{} ({}): {} eff + {} abs, {} over", top.empty() ? "" : "; ",
                info ? info->SpellName[0] : "melee", sorted[i].first, sorted[i].second.Effective,
                sorted[i].second.Absorbed, sorted[i].second.Overheal);
        }
        LOG_INFO("server.dpssim", "mod-dpssim:     top spells: {}", top.empty() ? std::string("none") : top);

        // Every spell with its event count (hits and ticks), and the auras the healer put on the group: the evidence
        // that a Prayer of Mending jumps, a Renew ticks or a shield was applied and consumed
        std::string all;
        for (auto const& [spellId, totals] : sorted)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
            all += Acore::StringFormat("{}{} ({}) x{}", all.empty() ? "" : "; ", info ? info->SpellName[0] : "melee",
                spellId, totals.Events);
        }
        LOG_INFO("server.dpssim", "mod-dpssim:     all healing spells (events): {}",
            all.empty() ? std::string("none") : all);

        std::map<uint32, uint32> applied;
        for (SimHeal::GroupAuraEvent const& e : result.GroupAuraEvents)
            if (e.Applied && e.ByHealer)
                ++applied[e.SpellId];
        std::string auras;
        for (auto const& [spellId, count] : applied)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
            auras += Acore::StringFormat("{}{} ({}) x{}", auras.empty() ? "" : "; ", info ? info->SpellName[0] : "?",
                spellId, count);
        }
        LOG_INFO("server.dpssim", "mod-dpssim:     auras the healer applied to the group: {}",
            auras.empty() ? std::string("none") : auras);

        // The first two shields of every shield spell: when the aura went on and when it first took damage (the evidence
        // that a shield is used up by the next hit, whatever else is healed)
        std::string shields;
        std::map<uint32, uint32> shieldsPerSpell;
        for (SimHeal::AbsorbEvent const& absorb : result.AbsorbEvents)
        {
            if (shieldsPerSpell[absorb.SpellId] >= 2)
                continue;

            SimHeal::GroupAuraEvent const* applied = nullptr;
            for (SimHeal::GroupAuraEvent const& e : result.GroupAuraEvents)
                if (e.Applied && e.TargetIndex == absorb.TargetIndex && e.SpellId == absorb.SpellId &&
                    e.TimestampMs <= absorb.TimestampMs)
                    applied = &e;
            if (!applied)
                continue;

            ++shieldsPerSpell[absorb.SpellId];
            shields += Acore::StringFormat("{}spell {} on #{}: applied {} ms, absorbed {} at {} ms", shields.empty() ?
                "" : "; ", absorb.SpellId, uint32(absorb.TargetIndex), applied->TimestampMs, absorb.Amount,
                absorb.TimestampMs);
        }
        if (!shields.empty())
            LOG_INFO("server.dpssim", "mod-dpssim:     first shields: {}", shields);

        std::string perTarget;
        for (size_t i = 0; i < received.size(); ++i)
            perTarget += Acore::StringFormat("{}#{} {} {}: {}", i == 0 ? "" : "; ", i,
                SimHeal::RoleName(result.HealTargetInfo[i].Spec.TargetRole),
                SimHeal::ModeText(result.HealTargetInfo[i].Spec), received[i]);
        LOG_INFO("server.dpssim", "mod-dpssim:     healing received per target: {}", perTarget);

        // The boss's damage and each target's health range: the evidence for the known-value and pin-hold checks
        struct TargetDamage
        {
            uint32 Hits = 0;
            uint32 PinHits = 0;
            uint64 Requested = 0;
            uint64 Raw = 0;
            uint64 Absorbed = 0;
            uint32 MinHit = 0;
            uint32 MaxHit = 0;
            uint32 MinHealth = 0xFFFFFFFF;
            uint32 MaxHealth = 0;
        };
        std::vector<TargetDamage> damage(result.HealTargetInfo.size());
        for (SimHeal::DamageEvent const& e : result.DamageTakenEvents)
        {
            if (e.TargetIndex >= damage.size())
                continue;
            TargetDamage& d = damage[e.TargetIndex];
            d.MinHit = d.Hits == 0 ? e.Raw : std::min(d.MinHit, e.Raw);
            d.MaxHit = std::max(d.MaxHit, e.Raw);
            ++d.Hits;
            d.PinHits += e.Pin ? 1 : 0;
            d.Requested += e.Requested;
            d.Raw += e.Raw;
            d.Absorbed += e.Absorbed;
        }
        for (SimHeal::HealthSample const& e : result.HealthSamples)
            if (e.TargetIndex < damage.size())
            {
                damage[e.TargetIndex].MinHealth = std::min(damage[e.TargetIndex].MinHealth, e.Health);
                damage[e.TargetIndex].MaxHealth = std::max(damage[e.TargetIndex].MaxHealth, e.Health);
            }
        std::string damageText;
        for (size_t i = 0; i < damage.size(); ++i)
            damageText += Acore::StringFormat("{}#{} max {}: {} hit(s) ({} pin) requested {} raw {} (each {}-{}) "
                "absorbed {}, health {}-{}", i == 0 ? "" : "; ", i, result.HealTargetInfo[i].MaxHealth, damage[i].Hits,
                damage[i].PinHits, damage[i].Requested, damage[i].Raw, damage[i].MinHit, damage[i].MaxHit,
                damage[i].Absorbed, damage[i].MinHealth == 0xFFFFFFFF ? 0 : damage[i].MinHealth, damage[i].MaxHealth);
        LOG_INFO("server.dpssim", "mod-dpssim:     damage taken per target: {}", damageText);

        LOG_INFO("server.dpssim", "mod-dpssim:     drivers - {} pin hit(s), {} pin raise(s) by SetHealth, {} drain "
            "hit(s), {} failed cast(s); {} damage event(s).", result.PinHits, result.PinRaises, result.DrainHits,
            result.DriverCastFailures, result.DamageTakenEvents.size());
    }

    // RunPlayerbotBatch()'s heal branch: one healer bot, one group and boss for every iteration (the group persists),
    // the per-iteration reset of the healer (ResetForNextIteration(), exactly as in a DPS batch) and of the allies
    bool RunHealBatch(SimDaemon::RunConfig const& config, uint32 iterations,
        std::vector<SimDaemon::RunResult>& results)
    {
        // A dead ally releases its spirit after 6 minutes (SimHeal::MAX_HEAL_DURATION_MS)
        if (config.DurationMs > SimHeal::MAX_HEAL_DURATION_MS)
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunHealBatch() - a heal run of {} ms is over the {} ms "
                "limit (a dead ally would release its spirit and leave its slot) - aborting.", config.DurationMs,
                SimHeal::MAX_HEAL_DURATION_MS);
            return false;
        }

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
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunHealBatch() - SimActor::Create() failed - aborting.");
            return false;
        }

        Player* player = actor.GetPlayer();
        Map* map = player->GetMap();

        // The group exists before the bot does, as it does for a live healer: strategy resolution sees a grouped bot
        SimHealScenario scenario;
        SimHealScenario::Setup setup;
        setup.GroupSize = config.HealGroupSize;
        setup.Targets = config.HealTargets;
        setup.AllyMaxHealthTank = config.AllyMaxHealthTank;
        setup.AllyMaxHealthDps = config.AllyMaxHealthDps;
        setup.PinMaxHealth = config.PinMaxHealth;
        setup.AllyTankTalents = config.AllyTankTalents;
        setup.SpreadYards = config.AllySpreadYards;
        setup.DrainPulseMs = config.DrainPulseMs;
        if (!scenario.Create(player, setup))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunHealBatch() - building the group failed - aborting.");
            return false;
        }

        Creature* boss = scenario.GetBoss();
        std::vector<Creature*> const bossList = {boss};

        // The healer's damage goes through the existing recorder, pointed at the boss. The cast log's target index is
        // the group member the cast was aimed at.
        EventRecorder* recorder = new EventRecorder(player->GetGUID(), {boss->GetGUID()});
        CastRecorder* castRecorder = new CastRecorder(player->GetGUID(), scenario.GetMemberGuids());
        HealRecorder* healRecorder = new HealRecorder(player->GetGUID(), scenario.GetMemberGuids());
        scenario.SetRecorder(healRecorder);

        SimBot bot;
        if (!bot.Create(player, bossList, config.PlayerbotTalents, config.PlayerbotGlyphs, config.PetCreatureEntry))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunHealBatch() - SimBot::Create() failed - aborting.");
            return false;
        }

        bot.ResolveGroupMaster();
        // After the bot spent its talents (stamina talents move max health): the healer's own pinned slot
        scenario.PinHealerMaxHealth();

        // The role table, now that the healer's talents are spent: its own row reads its real spec tab
        scenario.LogRoles();

        Position const startPosition = player->GetPosition();

        for (uint32 i = 0; i < iterations; ++i)
        {
            if (i > 0)
            {
                ResetForNextIteration(player, bossList, bot, recorder, castRecorder, startPosition);
                scenario.ResetAllies();
                healRecorder->Reset();
            }

            SimDaemon::RunResult result;
            RunHealIteration(config, player, map, bot, scenario, recorder, castRecorder, healRecorder, result);
            LogHealSummary(result, i + 1, iterations);

            results.push_back(std::move(result));
        }

        return true;
    }

    // ---- Tank mode (the tank branch of RunPlayerbotBatch(); plan .agents/plans/tank-sim/tank-sim.PLAN.md) ----

    // What the dummies are told at the pull: the boss range for a 1-target run, the pack range for each dummy of 2+
    SimTankDummy::Settings MakeTankSettings(SimDaemon::RunConfig const& config)
    {
        SimTankDummy::Settings settings;
        settings.Hit = config.TargetCount > 1 ? config.TankPackHit : config.TankHit;
        settings.SwingMs = config.TankSwingMs;
        settings.Crit = config.TankDummyCrit;
        return settings;
    }

    // One health / class power sample of the actor
    SimTank::Sample SampleTankActor(Player* actor, uint32 nowMs)
    {
        SimTank::Sample sample;
        sample.TimestampMs = nowMs;
        sample.Health = actor->GetHealth();
        sample.MaxHealth = actor->GetMaxHealth();
        Powers const type = actor->getPowerType();
        sample.PowerType = uint8(type);
        sample.Power = actor->GetPower(type);
        sample.MaxPower = actor->GetMaxPower(type);
        if (Aura const* bulwark = actor->GetAura(SimTank::SPELL_BULWARK))
            sample.BulwarkStacks = bulwark->GetStackAmount();
        return sample;
    }

    // The actor's character sheet, from the core's own getters (taken at the pull and again after the first second)
    SimTank::ActorInfo DescribeTankActor(Player* actor, Creature* primary, float primaryExpectedCrit)
    {
        SimTank::ActorInfo info;
        info.Level = actor->GetLevel();
        info.Health = actor->GetMaxHealth();
        info.Armor = actor->GetArmor();
        info.DefenseSkill = actor->GetDefenseSkillValue(primary);
        info.MaxSkillForLevel = actor->GetMaxSkillValueForLevel();
        info.Dodge = actor->GetUnitDodgeChance();
        info.Parry = actor->GetUnitParryChance();
        info.Block = actor->GetUnitBlockChance();
        info.BlockValue = actor->GetShieldBlockValue();
        info.CritImmune = primaryExpectedCrit <= 0.0f;
        return info;
    }

    // One tank-mode iteration, the counterpart of RunPlayerbotIteration(): the same housekeeping, pre-pull buff phase
    // and sim clock rules, then the pull (the dummies attack the actor) and a tick loop in which the dummies swing, the
    // bot tanks, and in the dps scenario the actor's health is refilled after every step. Assumes the recorders are
    // rewound (ResetForNextIteration() does that between iterations; the first iteration has nothing recorded yet).
    void RunTankIteration(SimDaemon::RunConfig const& config, Player* player, std::vector<Creature*> const& dummies,
        Map* map, SimBot& bot, EventRecorder* recorder, CastRecorder* castRecorder, HealRecorder* healRecorder,
        DamageTakenRecorder* damageRecorder, SimDaemon::RunResult& result)
    {
        auto const wallStart = std::chrono::steady_clock::now();

        // Same start-of-iteration housekeeping as RunPlayerbotIteration()
        player->RemoveAllSpellCooldown();
        if (!bot.EnsurePet())
            LOG_ERROR("server.dpssim", "mod-dpssim: the hunter pet could not be restored for this iteration - it runs "
                "without one.");
        for (auto const& [spellId, aura] : player->GetOwnedAuras())
            aura->ResetProcCooldown();

        // The dummies hit the armor, so gear wears down: free repairs, so a long batch never runs on broken gear
        player->DurabilityRepairAll(false, 0.0f, false);

        // The dummies stay idle until the pull (plan R5): the pre-pull buff phase runs its full length untouched
        SimTankDummy::EndFight(dummies);

        uint32 const nowMs = std::max(getMSTime(), uint32(GameTime::GetGameTimeMS().count()));
        uint32 const measuredStartMs = nowMs + ITERATION_GAP_MS;

        if (config.PrePullBuffMs > 0)
        {
            uint32 const buffMs = std::min(config.PrePullBuffMs, ITERATION_GAP_MS);
            RunBuffPhase(config, buffMs, measuredStartMs, player, map, bot, castRecorder);
            recorder->Reset();
            castRecorder->Reset();
            healRecorder->Reset();
            damageRecorder->Reset();
            recorder->RecordAurasPresent(player);
            for (Creature* dummy : dummies)
                recorder->RecordAurasPresent(dummy);
            RefillResources(player, dummies);
            bot.ReestablishCombatState(dummies);
        }
        else
        {
            healRecorder->Reset();
            damageRecorder->Reset();
        }

        // The pull: the dummies attack the actor and start their swing timers; the damage is solved first (plan R2)
        SimTankDummy::Settings const settings = MakeTankSettings(config);
        result.TankDummies = SimTankDummy::BeginFight(dummies, player, settings);
        result.TankActorAtPull = DescribeTankActor(player, dummies.front(), result.TankDummies.front().ExpectedCritPct);
        // Replaced after the first second (stance and buffs up); the pull's stays in TankActorAtPull
        result.TankActor = result.TankActorAtPull;
        result.TankMode = true;
        result.TankScenario = config.TankScenario;

        // Known-value runs: debuffs on every dummy from the pull (the solver above ran undebuffed)
        for (uint32 spellId : config.TankPullAuras)
            for (Creature* dummy : dummies)
                player->CastSpell(dummy, spellId, true);
        if (!config.TankPullAuras.empty())
        {
            Creature* first = dummies.front();
            // The attack time with the haste aura in it (what the swing timer resets to), not the unhasted base
            LOG_INFO("server.dpssim", "mod-dpssim:   pull auras cast on the dummies; dummy #0 now: attack time {} ms, "
                "attack power {:.0f}, damage fields {:.1f}-{:.1f}.",
                uint32(std::lround(first->GetAttackTime(BASE_ATTACK) * first->m_modAttackSpeedPct[BASE_ATTACK])),
                first->GetTotalAttackPowerValue(BASE_ATTACK), first->GetFloatValue(UNIT_FIELD_MINDAMAGE),
                first->GetFloatValue(UNIT_FIELD_MAXDAMAGE));
        }

        LogAurasAtPull(player);
        LOG_INFO("server.dpssim", "mod-dpssim: iteration pull - dummy armor {}, maxHealth {}.",
            dummies.front()->GetArmor(), dummies.front()->GetMaxHealth());
        WarnStrayUnitsOnce(player, dummies);

        {
            // The actor's damage-taken multiplier on a physical melee hit (Defensive Stance, talents), the reason a
            // recorded pre-armor value sits below the solved range; measured on a large hit through the core's function
            LOG_INFO("server.dpssim", "mod-dpssim:   actor's damage-taken multiplier on a physical melee hit at the "
                "pull: {:.4f}.", float(player->MeleeDamageBonusTaken(dummies.front(), 1000000, BASE_ATTACK, nullptr,
                SPELL_SCHOOL_MASK_NORMAL)) / 1000000.0f);
            SimTank::ActorInfo const& a = result.TankActorAtPull;
            std::string layout;
            for (size_t i = 0; i < dummies.size(); ++i)
                layout += Acore::StringFormat("{}#{} {:.1f} yd{}{}", i == 0 ? "" : ", ", i,
                    player->GetExactDist(dummies[i]),
                    player->IsWithinMeleeRange(dummies[i]) ? "" : " OUT OF MELEE RANGE",
                    player->HasInArc(M_PI, dummies[i]) ? "" : " OUTSIDE THE FRONT ARC");
            LOG_INFO("server.dpssim", "mod-dpssim:   tank pull - scenario {}, {} dummy(ies): {}; attackers on the "
                "actor: {} (bot's \"my attacker count\": {}).", SimTank::ScenarioName(config.TankScenario),
                dummies.size(), layout, player->getAttackers().size(), bot.GetMyAttackerCount());
            LOG_INFO("server.dpssim", "mod-dpssim:   actor level {}, {} health, armor {}, defense {} (max for level vs "
                "the primary {}; AlwaysMaxSkillForLevel {}), dodge {:.2f}% parry {:.2f}% block {:.2f}% (value {}), "
                "primary expected crit chance {:.2f}%{}.", a.Level, a.Health, a.Armor, a.DefenseSkill,
                a.MaxSkillForLevel, sConfigMgr->GetOption<bool>("AlwaysMaxSkillForLevel", false) ? "on" : "off",
                a.Dodge, a.Parry, a.Block, a.BlockValue, result.TankDummies.front().ExpectedCritPct,
                a.CritImmune ? " (CRIT IMMUNE)" : "");
            SimTank::DummyInfo const& d = result.TankDummies.front();
            LOG_INFO("server.dpssim", "mod-dpssim:   dummy damage solver - asked {}, swing {} ms, weapon damage "
                "{:.2f}-{:.2f}, attack power {:.0f}, DamageModifier {:.2f}, base pct {:.4f} -> damage fields "
                "{:.1f}-{:.1f} (dummy level {}, fights the actor as level {}).", SimTank::HitRangeText(d.Hit),
                d.SwingMs, d.WeaponMin, d.WeaponMax, d.AttackPower, d.DamageModifier, d.BasePct, d.FieldMin,
                d.FieldMax, d.Level, d.LevelForTarget);
        }

        // A silenced bot (tests): its AI must not act in the first Tick(), before the loop silences it every step
        if (config.TankSilenceBot)
            bot.SilenceAI();

        SimClock clock(config.StepMs, measuredStartMs);
        uint32 lastManaSampleMs = 0;
        bool sampledManaOnce = false;
        std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
        uint32 lastPowerSampleMs = 0;
        bool sampledPowerOnce = false;
        std::vector<SimDaemon::RunResult::PowerSample> powerSamples;
        ObjectGuid lastTarget = bot.GetCurrentTarget();
        uint32 targetSwitches = 0;
        uint32 lastTankSampleMs = 0;
        bool sampledTankOnce = false;
        uint32 lastThreatSampleMs = 0;
        bool sampledThreatOnce = false;
        float minHealthPct = 100.0f;
        bool critRefreshed = false;
        uint32 minAttackers = 0xFFFFFFFF;
        bool const refill = config.TankScenario == SimTank::Scenario::Dps;

        auto const sampleThreat = [&](uint32 atMs)
        {
            for (size_t i = 0; i < dummies.size(); ++i)
                result.ThreatSamples.push_back({atMs, uint8(i), dummies[i]->GetThreatMgr().GetThreat(player)});
        };

        while (clock.GetElapsedMs() < config.DurationMs)
        {
            clock.Tick(map);

            // The existing actor-death rule (RunPlayerbotIteration()): check after every Tick, before the AI's auto
            // release can run. In the survive scenario the time of death is the headline (ActorDiedAtMs).
            if (!player->IsAlive())
            {
                result.ActorDied = true;
                result.ActorDiedAtMs = clock.GetElapsedMs();
                // The killing tick is not sampled below: the lowest health is the death's
                minHealthPct = 0.0f;
                LOG_WARN("server.dpssim", "mod-dpssim: the actor DIED {} ms into the tank iteration - iteration ended, "
                    "its DPS counts the full {} ms.", result.ActorDiedAtMs, config.DurationMs);
                break;
            }

            // After the swings of this tick, before the AI heals and before the refill: the actor's lowest health
            if (player->GetMaxHealth() > 0)
                minHealthPct = std::min(minHealthPct,
                    100.0f * float(player->GetHealth()) / float(player->GetMaxHealth()));

            if (!sampledTankOnce || clock.GetElapsedMs() - lastTankSampleMs >= SimTank::TANK_SAMPLE_INTERVAL_MS)
            {
                result.TankSamples.push_back(SampleTankActor(player, clock.GetElapsedMs()));
                lastTankSampleMs = clock.GetElapsedMs();
                sampledTankOnce = true;
            }
            if (!sampledThreatOnce || clock.GetElapsedMs() - lastThreatSampleMs >= SimTank::THREAT_SAMPLE_INTERVAL_MS)
            {
                sampleThreat(clock.GetElapsedMs());
                lastThreatSampleMs = clock.GetElapsedMs();
                sampledThreatOnce = true;
            }

            // Tests (SimTests.cpp): the scripted part of the step, then the bot's AI unless the test silenced it
            if (config.TankStepHook)
                config.TankStepHook(clock.GetElapsedMs(), player, dummies);
            if (config.TankSilenceBot)
                bot.SilenceAI();
            else
                bot.UpdateAI(config.StepMs);
            MaybeSampleMana(player, clock.GetElapsedMs(), lastManaSampleMs, sampledManaOnce, manaSamples);
            MaybeSamplePower(player, clock.GetElapsedMs(), lastPowerSampleMs, sampledPowerOnce, powerSamples);

            // The crit chance the dummies have once the bot has acted (its stance, its first buffs): the pull value was
            // taken before any of that
            if (!critRefreshed && clock.GetElapsedMs() >= 1000)
            {
                critRefreshed = true;
                std::string chances;
                for (size_t i = 0; i < dummies.size(); ++i)
                {
                    result.TankDummies[i].ExpectedCritPct = dummies[i]->GetUnitCriticalChance(BASE_ATTACK, player);
                    chances += Acore::StringFormat("{}{:.2f}%", i == 0 ? "" : ", ",
                        result.TankDummies[i].ExpectedCritPct);
                }
                // The character sheet with the stance and the first buffs up: this is the one the report shows
                result.TankActor = DescribeTankActor(player, dummies.front(),
                    result.TankDummies.front().ExpectedCritPct);
                SimTank::ActorInfo const& a = result.TankActor;
                LOG_INFO("server.dpssim", "mod-dpssim:   dummies' expected crit chance against the actor after the "
                    "first second (stance, buffs up): {}{}.", chances, a.CritImmune ? " (CRIT IMMUNE)" : "");
                LOG_INFO("server.dpssim", "mod-dpssim:   actor after the first second - {} health, armor {}, "
                    "defense {}, dodge {:.2f}% parry {:.2f}% block {:.2f}% (value {}).", a.Health, a.Armor,
                    a.DefenseSkill, a.Dodge, a.Parry, a.Block, a.BlockValue);
            }
            minAttackers = std::min(minAttackers, uint32(bot.GetMyAttackerCount()));

            ObjectGuid const currentTarget = bot.GetCurrentTarget();
            if (!currentTarget.IsEmpty())
            {
                if (!lastTarget.IsEmpty() && currentTarget != lastTarget)
                    ++targetSwitches;
                lastTarget = currentTarget;
            }

            // dps scenario: the hits are real and recorded, but the actor never dies. After the step, so the bot's next
            // decisions see the health the hits left (a cooldown gated on low health can still fire)
            if (refill && player->IsAlive())
                player->SetFullHealth();

            if (config.RealTimePaced)
                std::this_thread::sleep_for(std::chrono::milliseconds(config.StepMs));
        }

        // A death in the final step: the loop condition ends the loop before the check above sees it
        if (!result.ActorDied && !player->IsAlive())
        {
            result.ActorDied = true;
            result.ActorDiedAtMs = config.DurationMs;
            minHealthPct = 0.0f;
        }

        // Plan T11: a survive run the actor lived through to the end; its TTD counts as the full duration
        result.TankSurvived = config.TankScenario == SimTank::Scenario::Survive && !result.ActorDied;

        // A dead actor holds no threat any more: the last sample taken while it lived stands
        if (!result.ActorDied)
            sampleThreat(clock.GetElapsedMs());
        LOG_INFO("server.dpssim", "mod-dpssim:   bot's \"my attacker count\" over the fight: lowest {}, at the end {}.",
            minAttackers == 0xFFFFFFFF ? 0 : minAttackers, bot.GetMyAttackerCount());

        result.Success = true;
        // Deliberate, as in a DPS run: a dead actor is charged the full duration for DPS; the time of death is
        // ActorDiedAtMs (the survive scenario's TTD)
        result.ElapsedMs = result.ActorDied ? config.DurationMs : clock.GetElapsedMs();
        result.CastAttempts = recorder->GetCastCount();
        result.TotalDamage = recorder->GetTotalDamage();
        result.CastCount = recorder->GetCastCount();
        result.CritCount = recorder->GetCritCount();
        result.HitDamages = recorder->GetHitDamages();
        result.HitCrits = recorder->GetHitCrits();
        result.HitSpellIds = recorder->GetHitSpellIds();
        result.HitTimestamps = recorder->GetHitTimestamps();
        result.HitIsPet = recorder->GetHitIsPet();
        result.HitTargetIndex = recorder->GetHitTargetIndex();
        result.TargetSwitches = targetSwitches;
        result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
        result.ManaSamples = std::move(manaSamples);
        result.PowerSamples = std::move(powerSamples);
        result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());

        // The actor's own healing and shields (heal-mode structs, target index 0 = the actor), and the incoming swings
        result.HealEvents = healRecorder->GetHealEvents();
        result.AbsorbEvents = healRecorder->GetAbsorbEvents();
        if (damageRecorder->GetSavedHits() > 0)
            LOG_INFO("server.dpssim", "mod-dpssim:   dps scenario: {} lethal hits refilled to full health, {} of them "
                "clamped to max health - 1.", damageRecorder->GetSavedHits(), damageRecorder->GetClampedHits());
        result.Swings = damageRecorder->GetSwings();
        result.SwingAbsorbs = damageRecorder->GetSwingAbsorbs();
        result.TankMinHealthPct = minHealthPct;

        // Recorders stamp raw getMSTime(); reports count from the iteration start. The samples already use clock time.
        uint32 const startMs = clock.GetStartMs();
        auto const rebase = [startMs](uint32& timestampMs)
        {
            timestampMs = timestampMs >= startMs ? timestampMs - startMs : 0;
        };
        for (uint32& timestampMs : result.HitTimestamps)
            rebase(timestampMs);
        for (SimDaemon::RunResult::AuraEvent& e : result.AuraEvents)
            rebase(e.TimestampMs);
        for (SimDaemon::RunResult::CastEvent& e : result.CastEvents)
            rebase(e.TimestampMs);
        for (SimHeal::HealEvent& e : result.HealEvents)
            rebase(e.TimestampMs);
        for (SimHeal::AbsorbEvent& e : result.AbsorbEvents)
            rebase(e.TimestampMs);
        for (SimTank::SwingEvent& e : result.Swings)
            rebase(e.TimestampMs);
        for (SimTank::SwingAbsorb& e : result.SwingAbsorbs)
            rebase(e.TimestampMs);

        result.WallClockMs = uint32(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - wallStart).count());
    }

    // One summary line per iteration plus detail lines. TS1 is validated from these lines; TS2 writes the JSON report.
    void LogTankSummary(SimDaemon::RunConfig const& config, SimDaemon::RunResult const& result, uint32 iteration,
        uint32 iterations)
    {
        using SimTank::Outcome;
        constexpr size_t OUTCOMES = size_t(Outcome::Other) + 1;

        // The seconds the tank metrics divide by: the fight to the death in survive, the full duration otherwise. DPS
        // keeps the full duration (a dead actor is charged all of it, as everywhere).
        double const fullSeconds = double(result.ElapsedMs) / 1000.0;
        double const fightSeconds = result.ActorDied ? double(result.ActorDiedAtMs) / 1000.0 : fullSeconds;
        double const dps = fullSeconds > 0.0 ? double(result.TotalDamage) / fullSeconds : 0.0;

        // Threat: the last sample of every dummy
        std::vector<float> threat(result.TankDummies.size(), 0.0f);
        uint32 lastThreatMs = 0;
        for (SimTank::ThreatSample const& sample : result.ThreatSamples)
            if (sample.DummyIndex < threat.size())
            {
                threat[sample.DummyIndex] = sample.Threat;
                lastThreatMs = std::max(lastThreatMs, sample.TimestampMs);
            }
        double totalThreat = 0.0;
        float lowestThreat = threat.empty() ? 0.0f : threat.front();
        for (float value : threat)
        {
            totalThreat += double(value);
            lowestThreat = std::min(lowestThreat, value);
        }
        double const tps = lastThreatMs > 0 ? totalThreat / (double(lastThreatMs) / 1000.0) : 0.0;

        // The swings
        uint32 counts[OUTCOMES] = {};
        uint64 preArmorSum = 0, armorSum = 0, blockedSum = 0, absorbedSum = 0, resistedSum = 0, finalSum = 0;
        uint64 landedPreArmor = 0;
        uint32 preMin = 0xFFFFFFFF, preMax = 0, landed = 0;
        double expMiss = 0.0, expDodge = 0.0, expParry = 0.0, expBlock = 0.0, expCrit = 0.0;
        int64 rageTenths = 0;
        uint32 rageSwings = 0, avoidRageSwings = 0, behindSwings = 0;
        std::vector<uint32> swingsPerDummy(result.TankDummies.size(), 0);
        std::vector<uint32> avoidsPerDummy(result.TankDummies.size(), 0);
        std::vector<uint32> critTimes;
        double baseRollMin = 1e18, baseRollMax = 0.0;
        for (SimTank::SwingEvent const& swing : result.Swings)
        {
            ++counts[size_t(swing.Result)];
            if (swing.PreArmor > 0 && swing.TakenMult > 0.0f)
            {
                // The dummy's own roll: the recorded value with the actor's damage-taken multiplier taken back out
                double const base = double(swing.PreArmor) / double(swing.TakenMult);
                baseRollMin = std::min(baseRollMin, base);
                baseRollMax = std::max(baseRollMax, base);
            }
            preArmorSum += swing.PreArmor;
            if (swing.PreArmor > 0)
            {
                preMin = std::min(preMin, swing.PreArmor);
                preMax = std::max(preMax, swing.PreArmor);
            }
            expMiss += swing.ExpectedMiss;
            expDodge += swing.ExpectedDodge;
            expParry += swing.ExpectedParry;
            expBlock += swing.ExpectedBlock;
            expCrit += swing.ExpectedCrit;
            if (!swing.InFrontArc)
                ++behindSwings;
            // Swings that took no damage through: rage on one of them is a proc, not damage-taken rage
            bool const avoided = swing.Result == Outcome::Dodge || swing.Result == Outcome::Parry ||
                swing.Result == Outcome::FullBlock;
            if (swing.DummyIndex < swingsPerDummy.size())
            {
                ++swingsPerDummy[swing.DummyIndex];
                if (swing.Result == Outcome::Dodge || swing.Result == Outcome::Parry)
                    ++avoidsPerDummy[swing.DummyIndex];
            }
            if (swing.Result != Outcome::Miss && swing.Result != Outcome::Dodge && swing.Result != Outcome::Parry &&
                swing.Result != Outcome::Other)
            {
                ++landed;
                landedPreArmor += swing.PreArmor;
                armorSum += swing.ArmorMitigated;
            }
            blockedSum += swing.Blocked;
            absorbedSum += swing.Absorbed;
            resistedSum += swing.Resisted;
            finalSum += swing.Final;
            if (swing.RageGained >= 0)
            {
                rageTenths += swing.RageGained;
                ++rageSwings;
                if (avoided && swing.RageGained > 0)
                    ++avoidRageSwings;
            }
            if (swing.Result == Outcome::Crit)
                critTimes.push_back(swing.TimestampMs);
        }

        uint32 const swings = uint32(result.Swings.size());
        auto const pct = [swings](uint32 n) { return swings > 0 ? 100.0 * double(n) / double(swings) : 0.0; };
        auto const meanPct = [swings](double hundredths)
        {
            return swings > 0 ? hundredths / 100.0 / double(swings) : 0.0;
        };
        uint32 const avoids = counts[size_t(Outcome::Miss)] + counts[size_t(Outcome::Dodge)] +
            counts[size_t(Outcome::Parry)];

        // Self-healing and shields: the actor's own, by spell (HealRecorder with the actor as the whole group)
        uint64 healEffective = 0, healOverheal = 0, selfAbsorb = 0;
        std::map<uint32, uint64> healBySpell;
        for (SimHeal::HealEvent const& e : result.HealEvents)
        {
            healEffective += e.Effective;
            healOverheal += e.Overheal;
            healBySpell[e.SpellId] += e.Effective;
        }
        for (SimHeal::AbsorbEvent const& e : result.AbsorbEvents)
        {
            selfAbsorb += e.Amount;
            healBySpell[e.SpellId] += e.Amount;
        }
        double const damageTakenDtps = fightSeconds > 0.0 ? double(finalSum) / fightSeconds : 0.0;
        double const grossDtps = fightSeconds > 0.0 ? double(finalSum + absorbedSum) / fightSeconds : 0.0;
        double const netDtps = fightSeconds > 0.0 ? (double(finalSum) - double(healEffective)) / fightSeconds : 0.0;
        double const selfHps = fightSeconds > 0.0 ? double(healEffective) / fightSeconds : 0.0;

        // Crit-immune bug flag (plan section 5): a crit while the expected chance was zero
        bool const critImmuneAtPull = !result.TankDummies.empty() && result.TankDummies.front().ExpectedCritPct <= 0.0f;
        uint32 critWithZeroChance = 0;
        for (SimTank::SwingEvent const& swing : result.Swings)
            if (swing.Result == Outcome::Crit && swing.ExpectedCrit == 0)
                ++critWithZeroChance;

        // TTD: the time of death; a survive run that lived to the end counts the full duration and says so (plan T11);
        // the dps scenario refills health, so it has none
        std::string ttdText = "n/a";
        if (result.ActorDied)
            ttdText = Acore::StringFormat("{} ms", result.ActorDiedAtMs);
        else if (result.TankSurvived)
            ttdText = Acore::StringFormat("{} ms (survived)", result.ElapsedMs);

        LOG_INFO("server.dpssim", "mod-dpssim:   tank iteration {}/{} ({}) - {} ms ({} wall ms): DPS {:.1f}, TPS "
            "{:.1f}, {} swings, hit {:.1f}% crit {:.1f}% crush {:.1f}% block {:.1f}% (full {}) dodge {:.1f}% parry "
            "{:.1f}% miss {:.1f}% (avoided {:.1f}%), damage taken {} (+{} absorbed), DTPS {:.1f}, self-healing {} "
            "effective / {} overheal (HPS {:.1f}) + {} self-shields, net DTPS {:.1f}, TTD {}, survived {}, min HP "
            "{:.1f}%, rage from hits {:.1f} ({} swings measured), expected vs observed crit {:.2f}% / {:.2f}%.",
            iteration, iterations, SimTank::ScenarioName(config.TankScenario), result.ElapsedMs, result.WallClockMs,
            dps, tps, swings,
            pct(counts[size_t(Outcome::Hit)]), pct(counts[size_t(Outcome::Crit)]), pct(counts[size_t(Outcome::Crush)]),
            pct(counts[size_t(Outcome::Block)] + counts[size_t(Outcome::FullBlock)]),
            counts[size_t(Outcome::FullBlock)], pct(counts[size_t(Outcome::Dodge)]),
            pct(counts[size_t(Outcome::Parry)]), pct(counts[size_t(Outcome::Miss)]), pct(avoids), finalSum, absorbedSum,
            damageTakenDtps, healEffective, healOverheal, selfHps, selfAbsorb, netDtps, ttdText,
            result.TankSurvived ? "yes" : "no", result.TankMinHealthPct, double(rageTenths) / 10.0, rageSwings,
            meanPct(expCrit), pct(counts[size_t(Outcome::Crit)]));

        // Expected (what the core rolled, per swing) vs observed outcome rates, and the armor reduction
        double const armorPctObserved = landedPreArmor > 0 ? 100.0 * double(armorSum) / double(landedPreArmor) : 0.0;
        // Swing intervals per dummy, rounded to 100 ms: the swing speed and a slow (Thunder Clap)
        std::map<uint32, uint32> intervals;
        std::vector<uint32> lastSwing(result.TankDummies.size(), 0);
        std::vector<bool> haveLast(result.TankDummies.size(), false);
        for (SimTank::SwingEvent const& swing : result.Swings)
            if (swing.DummyIndex < lastSwing.size())
            {
                if (haveLast[swing.DummyIndex])
                    ++intervals[(swing.TimestampMs - lastSwing[swing.DummyIndex] + 50) / 100 * 100];
                lastSwing[swing.DummyIndex] = swing.TimestampMs;
                haveLast[swing.DummyIndex] = true;
            }
        std::string intervalText;
        for (auto const& [ms, count] : intervals)
            intervalText += Acore::StringFormat("{}{}:{}", intervalText.empty() ? "" : " ", ms, count);
        float expectedArmorPct = 0.0f;
        if (!result.TankDummies.empty())
        {
            float levelModifier = float(result.TankDummies.front().Level);
            if (levelModifier > 59)
                levelModifier += 4.5f * (levelModifier - 59);
            float reduction = 0.1f * float(result.TankActor.Armor) / (8.5f * levelModifier + 40);
            expectedArmorPct = 100.0f * std::min(reduction / (1.0f + reduction), 0.75f);
        }
        std::string firstSwings;
        for (size_t i = 0; i < result.Swings.size() && i < 6; ++i)
            firstSwings += Acore::StringFormat("{}{}", firstSwings.empty() ? "" : " ", result.Swings[i].TimestampMs);
        LOG_INFO("server.dpssim", "mod-dpssim:     first swings at (ms) {}.",
            firstSwings.empty() ? std::string("none") : firstSwings);
        LOG_INFO("server.dpssim", "mod-dpssim:     swing intervals (ms:count) {}; armor formula at the pull says "
            "{:.2f}%; dummy rolls {:.0f}-{:.0f} with the actor's damage-taken multiplier taken back out (damage "
            "fields at the pull {:.0f}-{:.0f}).", intervalText.empty() ? std::string("none") : intervalText,
            expectedArmorPct, baseRollMax > 0.0 ? baseRollMin : 0.0, baseRollMax,
            result.TankDummies.empty() ? 0.0f : result.TankDummies.front().FieldMin,
            result.TankDummies.empty() ? 0.0f : result.TankDummies.front().FieldMax);

        LOG_INFO("server.dpssim", "mod-dpssim:     outcomes observed vs expected (percent): miss {:.2f} / {:.2f}, "
            "dodge {:.2f} / {:.2f}, parry {:.2f} / {:.2f}, block {:.2f} / {:.2f}, crit {:.2f} / {:.2f}; {} swing(s) "
            "from outside the front arc; pre-armor {}-{} (mean {:.0f}); armor took {:.2f}% of the landed swings' "
            "pre-armor ({} total), blocks took {}, shields {}, resists {}.", pct(counts[size_t(Outcome::Miss)]),
            meanPct(expMiss), pct(counts[size_t(Outcome::Dodge)]), meanPct(expDodge),
            pct(counts[size_t(Outcome::Parry)]), meanPct(expParry),
            pct(counts[size_t(Outcome::Block)] + counts[size_t(Outcome::FullBlock)]), meanPct(expBlock),
            pct(counts[size_t(Outcome::Crit)]), meanPct(expCrit), behindSwings, preMin == 0xFFFFFFFF ? 0 : preMin,
            preMax, swings > 0 ? double(preArmorSum) / double(swings) : 0.0, armorPctObserved, armorSum, blockedSum,
            absorbedSum, resistedSum);

        if (critWithZeroChance > 0 || (critImmuneAtPull && counts[size_t(Outcome::Crit)] > 0))
        {
            std::string when;
            for (size_t i = 0; i < critTimes.size() && i < 10; ++i)
                when += Acore::StringFormat("{}{} ms", when.empty() ? "" : ", ", critTimes[i]);
            LOG_ERROR("server.dpssim", "mod-dpssim:     BUG: {} crit(s) taken ({} of them with an expected crit chance "
                "of 0; expected chance at the pull {:.2f}%, crit immune: {}) at {}{}.", counts[size_t(Outcome::Crit)],
                critWithZeroChance, result.TankDummies.empty() ? 0.0f : result.TankDummies.front().ExpectedCritPct,
                critImmuneAtPull ? "yes" : "no", when, critTimes.size() > 10 ? " ..." : "");
        }

        // Per dummy: swings, avoids by dodge or parry (a dummy with none is outside the front arc), threat
        std::string perDummy;
        for (size_t i = 0; i < swingsPerDummy.size(); ++i)
            perDummy += Acore::StringFormat("{}#{}: {} swings, {} dodge/parry, threat {:.0f}", i == 0 ? "" : "; ", i,
                swingsPerDummy[i], avoidsPerDummy[i], threat[i]);
        LOG_INFO("server.dpssim", "mod-dpssim:     per dummy - {}; lowest threat {:.0f}; rage swings measured {} "
            "(dodged, parried or fully blocked swings that gave rage: {}).", perDummy, lowestThreat, rageSwings,
            avoidRageSwings);

        // The actor's own heals and shields by spell, the casts by spell and the auras it gained
        auto const spellName = [](uint32 spellId) -> std::string
        {
            if (spellId == 0)
                return "melee";
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
            return Acore::StringFormat("{} ({})", info ? info->SpellName[0] : "?", spellId);
        };

        std::string heals;
        for (auto const& [spellId, amount] : healBySpell)
            heals += Acore::StringFormat("{}{}: {}", heals.empty() ? "" : "; ", spellName(spellId), amount);
        LOG_INFO("server.dpssim", "mod-dpssim:     self-healing and shields by spell: {}",
            heals.empty() ? std::string("none") : heals);

        std::map<uint32, uint32> casts;
        for (SimDaemon::RunResult::CastEvent const& e : result.CastEvents)
            if (!e.Triggered)
                ++casts[e.SpellId];
        std::vector<std::pair<uint32, uint32>> sortedCasts(casts.begin(), casts.end());
        std::stable_sort(sortedCasts.begin(), sortedCasts.end(), [](auto const& a, auto const& b)
        {
            return a.second > b.second;
        });
        std::string castText;
        for (auto const& [spellId, count] : sortedCasts)
            castText += Acore::StringFormat("{}{} x{}", castText.empty() ? "" : "; ", spellName(spellId), count);
        LOG_INFO("server.dpssim", "mod-dpssim:     casts: {}", castText.empty() ? std::string("none") : castText);

        std::map<uint32, uint32> gained;
        uint32 dazes = 0;
        for (SimDaemon::RunResult::AuraEvent const& e : result.AuraEvents)
            if (e.IsActor && e.Applied)
            {
                ++gained[e.SpellId];
                if (e.SpellId == 1604)
                    ++dazes;
            }
        std::string auraText;
        for (auto const& [spellId, count] : gained)
        {
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
            if (info && !info->IsPassive() && info->IsPositive())
                auraText += Acore::StringFormat("{}{} x{}", auraText.empty() ? "" : "; ", spellName(spellId), count);
        }
        LOG_INFO("server.dpssim", "mod-dpssim:     buffs the actor gained (applications): {}; Dazed (1604) applied {} "
            "time(s).", auraText.empty() ? std::string("none") : auraText, dazes);
    }

    // The whole batch in one line: outcome rates over every swing of every iteration, observed against what the core
    // rolled (the mean of the per-swing expectations), the check that the sim lands the character sheet's numbers
    void LogTankBatchSummary(std::vector<SimDaemon::RunResult> const& results)
    {
        using SimTank::Outcome;
        uint64 swings = 0, miss = 0, dodge = 0, parry = 0, block = 0, crit = 0;
        double expMiss = 0, expDodge = 0, expParry = 0, expBlock = 0, expCrit = 0;
        uint32 survived = 0, died = 0;
        for (SimDaemon::RunResult const& result : results)
        {
            survived += result.TankSurvived;
            died += result.ActorDied;
            for (SimTank::SwingEvent const& swing : result.Swings)
            {
                ++swings;
                miss += swing.Result == Outcome::Miss;
                dodge += swing.Result == Outcome::Dodge;
                parry += swing.Result == Outcome::Parry;
                block += swing.Result == Outcome::Block || swing.Result == Outcome::FullBlock;
                crit += swing.Result == Outcome::Crit;
                expMiss += swing.ExpectedMiss;
                expDodge += swing.ExpectedDodge;
                expParry += swing.ExpectedParry;
                expBlock += swing.ExpectedBlock;
                expCrit += swing.ExpectedCrit;
            }
        }
        if (swings == 0)
        {
            LOG_INFO("server.dpssim", "mod-dpssim: tank batch complete - {} iteration(s), no swings.", results.size());
            return;
        }
        double const n = double(swings);
        auto const pct = [n](uint64 count) { return 100.0 * double(count) / n; };
        auto const mean = [n](double hundredths) { return hundredths / 100.0 / n; };
        LOG_INFO("server.dpssim", "mod-dpssim: tank batch complete - {} iteration(s), {} swings; observed / expected "
            "percent: miss {:.2f} / {:.2f}, dodge {:.2f} / {:.2f}, parry {:.2f} / {:.2f}, block {:.2f} / {:.2f}, crit "
            "{:.2f} / {:.2f}; the actor survived {} and died in {} iteration(s).", results.size(), swings, pct(miss),
            mean(expMiss), pct(dodge), mean(expDodge), pct(parry), mean(expParry), pct(block), mean(expBlock),
            pct(crit), mean(expCrit), survived, died);
    }

    // RunPlayerbotBatch()'s tank branch: the DPS batch with the dummies swinging at the actor. One actor, one set of
    // dummies (installed with the tank AI) and one bot for every iteration, the per-iteration reset of
    // ResetForNextIteration() as in a DPS batch, and tank recorders next to the DPS ones.
    bool RunTankBatch(SimDaemon::RunConfig const& config, uint32 iterations,
        std::vector<SimDaemon::RunResult>& results)
    {
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
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunTankBatch() - SimActor::Create() failed - aborting.");
            return false;
        }

        Player* player = actor.GetPlayer();
        Map* map = player->GetMap();

        // The tank layout: every dummy within melee reach, in front of the actor, facing it (plan R3)
        SimTargetGroup targets;
        if (!targets.Create(player, config.TargetCount, config.TargetSpreadYards, MakeTargetConfig(config),
            SimTargetGroup::Layout::Tank))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunTankBatch() - SimTarget::Create() failed - "
                "aborting.");
            return false;
        }

        std::vector<Creature*> const dummies = targets.GetCreatures();

        // The tank AI goes on the summoned dummies now, before the bot engages them; DPS and heal runs never reach here
        if (!SimTankDummy::Install(dummies, player, MakeTankSettings(config)))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunTankBatch() - installing the tank AI failed - "
                "aborting.");
            return false;
        }

        EventRecorder* recorder = new EventRecorder(player->GetGUID(), targets.GetGuids());
        CastRecorder* castRecorder = new CastRecorder(player->GetGUID(), targets.GetGuids());
        // The actor's own healing: the heal recorder with the actor as the whole group
        HealRecorder* healRecorder = new HealRecorder(player->GetGUID(), {player->GetGUID()});
        // The dps scenario never lets the actor die (OnDamage refills it); survive runs leave the core's kill alone
        DamageTakenRecorder* damageRecorder = new DamageTakenRecorder(player->GetGUID(), targets.GetGuids(),
            config.TankScenario == SimTank::Scenario::Dps);
        SimTankDummy::SetObserver(damageRecorder);

        SimBot bot;
        if (!bot.Create(player, dummies, config.PlayerbotTalents, config.PlayerbotGlyphs, config.PetCreatureEntry))
        {
            LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunTankBatch() - SimBot::Create() failed - aborting.");
            return false;
        }

        LOG_INFO("server.dpssim", "mod-dpssim: tank mode - scenario {}, boss hit {}, pack hit {}, swing {} ms, dummy "
            "crit {}.", SimTank::ScenarioName(config.TankScenario), SimTank::HitRangeText(config.TankHit),
            SimTank::HitRangeText(config.TankPackHit), config.TankSwingMs, config.TankDummyCrit ? "on" : "off");

        Position const startPosition = player->GetPosition();

        for (uint32 i = 0; i < iterations; ++i)
        {
            if (i > 0)
            {
                // The dummies stop first: a resurrected actor must not be swung at before the iteration's pull
                SimTankDummy::EndFight(dummies);
                ResetForNextIteration(player, dummies, bot, recorder, castRecorder, startPosition);
                healRecorder->Reset();
                damageRecorder->Reset();
            }

            SimDaemon::RunResult result;
            RunTankIteration(config, player, dummies, map, bot, recorder, castRecorder, healRecorder, damageRecorder,
                result);
            LogTankSummary(config, result, i + 1, iterations);
            if (player->GetPosition().GetExactDist(startPosition) > 1.0f)
                LOG_WARN("server.dpssim", "mod-dpssim: the actor ended the iteration {:.1f} yd from where it started.",
                    player->GetPosition().GetExactDist(startPosition));

            results.push_back(std::move(result));
        }

        SimTankDummy::SetObserver(nullptr);
        LogTankBatchSummary(results);
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

    // Always one dummy: the hardcoded rotation casts at a single target
    SimTargetGroup targets;
    if (!targets.Create(player, 1, config.TargetSpreadYards, MakeTargetConfig(config)))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunOnce() - SimTarget::Create() failed - aborting.");
        return false;
    }

    Creature* dummy = targets.GetPrimary();

    // Must be heap-allocated, not a local/stack object - see EventRecorder.h's doc comment.
    // Deliberately never deleted (ScriptMgr::Unload() owns it from construction onward); calling
    // RunOnce() several times in one process (as SimTests::RunAll() does) leaks one of these per
    // call for the process's remaining lifetime - documented, known, harmless. See EventRecorder.h.
    EventRecorder* recorder = new EventRecorder(player->GetGUID(), targets.GetGuids(), config.SpellId);

    // Same heap-allocation/never-deleted rules as `recorder` above - see CastRecorder.h's doc
    // comment. Unfiltered by spell id on purpose (a cast log tracks every ability, not just the
    // rotation's one damage spell) - RunOnce()'s hardcoded RotationTick() only ever casts Frostbolt
    // anyway, so this mostly matters for RunPlayerbotOnce() below, but is added here too for symmetry.
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID(), targets.GetGuids());

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
    result.HitIsPet = recorder->GetHitIsPet();
    result.HitTargetIndex = recorder->GetHitTargetIndex();
    result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
    result.ManaSamples = std::move(manaSamples);
    result.CastEvents = ToRunResultCastEvents(castRecorder->GetCastEvents());
    return true;
}

bool SimDaemon::RunPlayerbotOnce(RunConfig const& config, RunResult& result)
{
    result = RunResult{};

    if (config.RunMode != Mode::Dps)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - a heal-mode or tank-mode profile runs "
            "through RunPlayerbotBatch() only.");
        return false;
    }

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

    SimTargetGroup targets;
    if (!targets.Create(player, config.TargetCount, config.TargetSpreadYards, MakeTargetConfig(config)))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimTarget::Create() failed - aborting.");
        return false;
    }

    std::vector<Creature*> const dummies = targets.GetCreatures();

    // rotationSpellId defaults to 0 ("track any spell") - see EventRecorder.h's doc comment - since
    // a real Engine/Strategy casts a whole rotation, not Phase 1's one hardcoded Frostbolt.
    EventRecorder* recorder = new EventRecorder(player->GetGUID(), targets.GetGuids());

    // Same heap-allocation/never-deleted rules as `recorder` above - see CastRecorder.h's doc
    // comment. This is the recorder that actually matters: a real Engine/Strategy casts a whole
    // rotation, including non-damage abilities (Evocation, self-buffs, ...) EventRecorder has no
    // way to see at all.
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID(), targets.GetGuids());

    // SimBot::Create() teaches the bot's class spells and "pulls" every dummy (each engages the bot, no
    // spell cast) to bootstrap combat state - see its own doc comment for why that's needed.
    SimBot bot;
    if (!bot.Create(player, dummies, config.PlayerbotTalents, config.PlayerbotGlyphs, config.PetCreatureEntry))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimBot::Create() failed - aborting.");
        return false;
    }

    RunPlayerbotIteration(config, player, dummies, map, bot, recorder, castRecorder, result);
    return true;
}

bool SimDaemon::RunPlayerbotBatch(RunConfig const& config, uint32 iterations, std::vector<RunResult>& results)
{
    results.clear();
    if (iterations == 0)
        return true;
    results.reserve(iterations);

    // The healing sim shares the batch contract (one process, the actor and the recorders reused, `iterations` results)
    // but not the setup or the loop; the DPS path below is untouched
    if (config.RunMode == Mode::Heal)
        return RunHealBatch(config, iterations, results);
    if (config.RunMode == Mode::Tank)
        return RunTankBatch(config, iterations, results);

    // Identical setup to RunPlayerbotOnce() above - see its own inline comments for what each step
    // does. Done once here rather than once per iteration - see this function's own doc comment
    // (SimDaemon.h) for why that's the entire point of this function existing.
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
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - SimActor::Create() failed - aborting.");
        return false;
    }

    Player* player = actor.GetPlayer();
    Map* map = player->GetMap();

    SimTargetGroup targets;
    if (!targets.Create(player, config.TargetCount, config.TargetSpreadYards, MakeTargetConfig(config)))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - SimTarget::Create() failed - aborting.");
        return false;
    }

    std::vector<Creature*> const dummies = targets.GetCreatures();

    EventRecorder* recorder = new EventRecorder(player->GetGUID(), targets.GetGuids());
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID(), targets.GetGuids());

    SimBot bot;
    if (!bot.Create(player, dummies, config.PlayerbotTalents, config.PlayerbotGlyphs, config.PetCreatureEntry))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - SimBot::Create() failed - aborting.");
        return false;
    }

    Position const startPosition = player->GetPosition();

    for (uint32 i = 0; i < iterations; ++i)
    {
        if (i > 0)
            ResetForNextIteration(player, dummies, bot, recorder, castRecorder, startPosition);

        RunResult result;
        RunPlayerbotIteration(config, player, dummies, map, bot, recorder, castRecorder, result);

        results.push_back(std::move(result));
    }

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
    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() - M2a harness, real mod-playerbots "
        "Engine/Strategy selector, actor level {} vs. target level {}, {} target(s) ({}, spread {:.1f} yd).",
        config.ActorLevel, config.TargetLevel, config.TargetCount, SimTarget::RankName(config.TargetRank),
        config.TargetSpreadYards);

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

    LOG_INFO("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbot() complete - {} target(s) ({}, spread {:.1f} yd), "
        "{}ms sim time, {} landed hits ({} crit, {:.1f}% crit rate), {} total damage, {:.1f} DPS, {} target switches.",
        config.TargetCount, SimTarget::RankName(config.TargetRank), config.TargetSpreadYards, result.ElapsedMs,
        result.CastCount, result.CritCount, critRate, result.TotalDamage, dps, result.TargetSwitches);

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
