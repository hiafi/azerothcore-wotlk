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
#include "GameTime.h"
#include "Log.h"
#include "Map.h"
#include "Pet.h"
#include "Player.h"
#include "Playerbots.h"
#include "SimActor.h"
#include "SimBot.h"
#include "SimClock.h"
#include "SimDummyAI.h"
#include "SimReport.h"
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
#include <iterator>
#include <set>
#include <string>
#include <thread>

namespace
{
    // See SimDaemon.h's RunResult::ManaSamples doc comment for why this is a periodic sample
    // rather than a per-tick or per-event capture.
    constexpr uint32 MANA_SAMPLE_INTERVAL_MS = 500;

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
            result.push_back({e.TimestampMs, e.SpellId, e.IsTriggered});
        return result;
    }

    void RefillResources(Player* player, Creature* dummy);

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
                "AiPlayerbot.BotActiveAlone = 100 and AiPlayerbot.botActiveAloneSmartScale = 0 for the sim (run-sim.sh "
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
    void RunPlayerbotIteration(SimDaemon::RunConfig const& config, Player* player, Creature* dummy, Map* map,
        SimBot& bot, EventRecorder* recorder, CastRecorder* castRecorder, SimDaemon::RunResult& result)
    {
        // Every iteration starts with nothing on cooldown: pre-loop casts (SimBot::Create()'s spell-teaching
        // casts, gear equip spells) and the previous iteration's cooldowns would otherwise carry over.
        player->RemoveAllSpellCooldown();

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
            recorder->RecordAurasPresent(dummy);
            RefillResources(player, dummy);
            bot.ReestablishCombatState(dummy);
        }
        LogAurasAtPull(player);

        SimClock clock(config.StepMs, measuredStartMs);
        uint32 lastManaSampleMs = 0;
        bool sampledManaOnce = false;
        std::vector<SimDaemon::RunResult::ManaSample> manaSamples;
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
        result.AuraEvents = ToRunResultAuraEvents(recorder->GetAuraEvents());
        result.ManaSamples = std::move(manaSamples);
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
    // on) the dummy. Run by ResetForNextIteration() and again after the pre-pull buff phase, so the buff casts'
    // mana/rage/energy costs never reach the fight.
    void RefillResources(Player* player, Creature* dummy)
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
            dummy->SetFullHealth();
    }

    // Between-iteration reset for RunPlayerbotBatch() - see that function's doc comment (SimDaemon.h)
    // for the full reasoning, especially the passive-aura carve-out and SimBot::ReestablishCombatState()'s
    // own doc comment for the real failure this also guards against (a batch's first iteration
    // landing real hits, then every iteration after it landing zero, forever). The target dummy's health is only
    // refilled with health drain on (otherwise its AI zeroes all damage taken, so it never drops); the global
    // cooldown is left alone (RunPlayerbotIteration() starts each iteration ITERATION_GAP_MS later, by which time
    // it has long expired).
    void ResetForNextIteration(Player* player, Creature* dummy, SimBot& bot, EventRecorder* recorder, CastRecorder* castRecorder,
        Position const& startPosition)
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

        auto removeNonPassive = [](AuraApplication const* aurApp)
        {
            SpellInfo const* info = aurApp->GetBase()->GetSpellInfo();
            return !info || !info->IsPassive();
        };
        player->RemoveAppliedAuras(removeNonPassive);
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

        RefillResources(player, dummy);

        bot.ReestablishCombatState(dummy);

        recorder->Reset();
        castRecorder->Reset();
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
    targetConfig.HealthDrain = config.DummyHealthDrain;
    if (config.DummyMaxHealth > 0)
        targetConfig.MaxHealth = config.DummyMaxHealth;
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
    targetConfig.HealthDrain = config.DummyHealthDrain;
    if (config.DummyMaxHealth > 0)
        targetConfig.MaxHealth = config.DummyMaxHealth;
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

    // SimBot::Create() teaches the bot's class spells and "pulls" `dummy` (puts both in combat, no
    // spell cast) to bootstrap combat state - see its own doc comment for why that's needed.
    SimBot bot;
    if (!bot.Create(player, dummy, config.PlayerbotTalents, config.PlayerbotGlyphs))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotOnce() - SimBot::Create() failed - aborting.");
        return false;
    }

    RunPlayerbotIteration(config, player, dummy, map, bot, recorder, castRecorder, result);
    return true;
}

bool SimDaemon::RunPlayerbotBatch(RunConfig const& config, uint32 iterations, std::vector<RunResult>& results)
{
    results.clear();
    if (iterations == 0)
        return true;
    results.reserve(iterations);

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

    SimTarget target;
    SimTarget::Config targetConfig;
    targetConfig.Level = uint8(config.TargetLevel);
    targetConfig.Armor = config.TargetArmor;
    targetConfig.HealthDrain = config.DummyHealthDrain;
    if (config.DummyMaxHealth > 0)
        targetConfig.MaxHealth = config.DummyMaxHealth;
    if (!target.Create(map, player->GetNearPosition(8.0f, 0.0f), targetConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - SimTarget::Create() failed - aborting.");
        return false;
    }

    Creature* dummy = target.GetCreature();

    EventRecorder* recorder = new EventRecorder(player->GetGUID(), dummy->GetGUID());
    CastRecorder* castRecorder = new CastRecorder(player->GetGUID());

    SimBot bot;
    if (!bot.Create(player, dummy, config.PlayerbotTalents, config.PlayerbotGlyphs))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimDaemon::RunPlayerbotBatch() - SimBot::Create() failed - aborting.");
        return false;
    }

    Position const startPosition = player->GetPosition();

    for (uint32 i = 0; i < iterations; ++i)
    {
        if (i > 0)
            ResetForNextIteration(player, dummy, bot, recorder, castRecorder, startPosition);

        RunResult result;
        RunPlayerbotIteration(config, player, dummy, map, bot, recorder, castRecorder, result);

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
