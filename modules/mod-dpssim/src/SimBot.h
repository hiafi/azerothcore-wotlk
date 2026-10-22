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

#ifndef MODULE_DPSSIM_SIMBOT_H
#define MODULE_DPSSIM_SIMBOT_H

#include "Define.h"
#include "ObjectGuid.h"
#include <string>
#include <vector>

class Creature;
class Player;
class PlayerbotAI;
class Unit;

// Wraps a real mod-playerbots PlayerbotAI on top of an existing SimActor's Player, so the sim's
// hardcoded Phase 1 rotation (SimDaemon.cpp's RotationTick()) can be replaced with
// mod-playerbots' actual, unmodified Engine/Strategy/TriggerNode selector - see the plan doc's
// Phase 2 (M2a) task list. This class only wires the AI up and drives it each tick; it has no
// opinion on which strategy ends up active - that is entirely AiFactory::createCombatEngine()'s
// own per-class, per-spec-tab default (AiFactory.cpp's AddDefaultCombatStrategies(): with zero
// talent points spent anywhere, AiFactory::GetPlayerSpecTab() falls through to a per-class
// hardcoded default, MAGE_TAB_FROST for a mage - exactly the FrostMageStrategy pilot this phase
// targets, with no talent-point spending needed to get there).
//
// DOES register with PlayerbotsMgr (via AddPlayerbotData(), same entry point a real bot login
// uses) - Create() only holds a borrowed pointer to the PlayerbotAI that call produces, it does not
// construct one directly. An earlier version of this class deliberately skipped registration, on
// the theory that this sim actor only ever needs to run its own Engine against its own target and
// never needs other code to look it up via GET_PLAYERBOT_AI(). That theory was live-tested and
// found wrong: mod-playerbots' own internal logic calls GET_PLAYERBOT_AI(bot) on itself -
// AttackersValue::IsPossibleTarget() (the function backing the "current target"/"invalid target"
// trigger) opens with `if (!GET_PLAYERBOT_AI(bot)) return false;`, so an unregistered bot sees
// every target - including its own seeded one - as invalid, and the "invalid target" trigger fires
// "drop target" (relevance 99, beating every FrostMageStrategy default action) the first time it
// gets evaluated, permanently ending the rotation. See Create()'s own comment for the full causal
// chain. PlayerbotAI's destructor still calls PlayerbotsMgr::instance().RemovePlayerBotData()
// unconditionally, so ~SimBot()'s plain `delete _ai` remains correct with no extra bookkeeping.
class SimBot
{
public:
    ~SimBot();

    // Builds a PlayerbotAI on `bot` - first teaching it every trainer-taught spell appropriate to
    // its class/level via PlayerbotFactory::InitAvailableSpells() (the same, unmodified utility a
    // real random bot uses; needed because FrostMageStrategy's actions reference several spells,
    // not the one hardcoded id Phase 1's rotation used) - then "pulls" every dummy in `targets` (index 0, the
    // primary, becomes the "current target") with no spell cast: each dummy engages the bot
    // (Unit::EngageWithTarget(), a zero-threat entry on the bot's threat list plus combat; see EngageTargets())
    // to bootstrap combat state. That pull
    // is necessary, not just convenient:
    // PlayerbotAI::DoNextAction() only switches to the combat engine (and therefore to
    // FrostMageStrategy's triggers) once `bot->IsInCombat()` is true, and a Player's Attack() call
    // alone does not flag combat immediately for a player-controlled unit - real combat entry
    // happens "on contact" (a landed swing or spell hit), and the non-combat engine has no
    // automatic engage/pull action for a masterless bot. Once combat is set, control passes
    // entirely to the real Engine from the next UpdateAI() tick onward. Returns false (logging
    // why) on failure.
    //
    // `playerbotTalents` is the same positional talent string DpsSim.PlayerbotTalents takes (see
    // its conf doc comment for the format) - passed in explicitly (from RunConfig::
    // PlayerbotTalents, itself either the flat conf key or a loaded SimProfile's value) rather
    // than read from sConfigMgr directly in here, so this class has no opinion on where the
    // string came from. Empty = no talents spent. `playerbotGlyphs` applies the class's premade glyphs after the
    // talents (RunConfig::PlayerbotGlyphs). `petCreatureEntry` is a hunter profile's PetCreatureEntry
    // (SimProfile.h): non-zero tames that beast for the actor after the talents and glyphs, the way
    // PlayerbotFactory::InitPet() would (and spends its talent points like InitPetTalents()), and makes
    // EnsurePet() keep it alive and present for the rest of the run. 0 = no pet. A hunter also gets the
    // "Requires No Ammo" aura here (PlayerbotFactory::InitAmmo()), so a ranged weapon needs no arrows.
    bool Create(Player* bot, std::vector<Creature*> const& targets, std::string const& playerbotTalents,
        bool playerbotGlyphs, uint32 petCreatureEntry = 0);

    // Called at the start of every iteration of a run with a pet: returns true if the actor has a living pet.
    // A dead pet is revived in place (Revive Pet's own steps), a missing one (removed after a death, or the
    // actor's own death) is tamed again from the profile's PetCreatureEntry. Does nothing, returning true, for
    // a run with no pet. Neither path adds a database save of its own (the core and the factory save a new
    // pet, to the throwaway sim characters schema only - see README.md).
    bool EnsurePet();

    // Drives the real Engine/Strategy selector for one tick - call this from the SimClock loop
    // instead of a hardcoded RotationTick(). `diff` is not a wall-clock read: PlayerbotAIBase's
    // own throttling (PlayerbotAIConfig.reactDelay - how often a bot actually "thinks") is driven
    // purely by the `diff` values passed in here (see PlayerbotAIBase::UpdateAI()/YieldThread()),
    // so it respects the sim clock the same way GCD/cooldowns do (core patch 2) - confirmed by
    // reading its implementation, not assumed.
    void UpdateAI(uint32 diff);

    // Tests only (RunConfig::HealStepHook): makes the bot's AI do nothing. PlayerbotAI::UpdateAI() is also driven by
    // mod-playerbots' own PlayerScript::OnPlayerAfterUpdate() on every Player::Update(), not only by UpdateAI() above,
    // so simply not calling UpdateAI() leaves the healer casting. A next-check delay that long (the AI counts it down
    // by the diffs of both callers) keeps both quiet for the rest of the run.
    void SilenceAI();

    // Acknowledges a teleport the sim bot's own death started (the engine's auto release repops it at a graveyard).
    // Live bots get this from PlayerbotHolder::UpdateSessions, which the sim bot is not in; without it
    // IsBeingTeleported() stays true and PlayerbotAI::UpdateAI() returns early forever.
    void HandleTeleportAck();

    // Re-establishes combat state between iterations of SimDaemon::RunPlayerbotBatch() - added
    // 2026-09-13 after a real, reproduced failure: a batch's very first iteration would land real
    // hits, then every iteration after it would land zero casts for the rest of the batch, forever.
    // Root-caused and fixed the same day - see this method's own .cpp doc comment for the full
    // three-attempt history (two earlier ones that didn't work, one of which made things
    // measurably worse and was reverted) and the confirmed mechanism (Unit::IsInCombat() itself
    // going false for real - most likely npc_training_dummy's own no-damage combat timeout ending
    // combat between iterations - not anything PlayerbotAI caches on its own side).
    void ReestablishCombatState(std::vector<Creature*> const& targets);

    // Tank mode: the bot's own "my attacker count" value (what the tanking triggers read), 0 without an AI
    [[nodiscard]] uint8 GetMyAttackerCount() const;

    // The GUID of the AI's "current target" value (empty when it has none), sampled every tick to count target
    // switches (SimDaemon::RunResult::TargetSwitches)
    [[nodiscard]] ObjectGuid GetCurrentTarget() const;

    // Pre-pull buff phase (S0b, 2026-10-05): a real bot presses its aura, self-buffs and summons its pet on its
    // non-combat engine before a pull, but the sim bot starts every iteration already in combat and never runs
    // that engine. BeginBuffPhase() ends combat with the dummies, drops the "current target", strips the non-combat
    // engine down to the buff and pet strategies (see kBuffPhaseStrategies in SimBot.cpp for the rule) and
    // switches to it; the caller then ticks UpdateAI() for a while. EndBuffPhase() puts the stripped strategies
    // back. The pull itself is ReestablishCombatState(), exactly as before. Returns false when PlayerbotAI would
    // park the bot in "minimal" mode out of combat (AllowActivity() false), in which case the phase does nothing.
    bool BeginBuffPhase();
    void EndBuffPhase();

    // Heal mode, once after Create(): gives the bot the master PlayerbotAI::UpdateAIGroupMaster() would give it on its
    // first tick, now. The healer leads the group (plan R1) but the headless allies are group members without a
    // PlayerbotAI, so FindNewMaster() takes the first of them as "the real player" and resets the bot's strategies (a
    // "follow" included). Left to the first tick, that reset would land inside the first iteration's pre-pull buff
    // phase, after BeginBuffPhase() trimmed the strategies, and make iteration 1 differ from the rest. The master is a
    // headless, stationary ally, as a human's client-less stand-in. The buff phase strips "follow" and EndBuffPhase()
    // puts it back, so it is active again during the measured fight; that is harmless, because the bot stays in
    // combat (Step re-engages everyone) and the non-combat engine that follows the master never runs, and the master
    // does not move anyway.
    void ResolveGroupMaster();

    // Heal mode: the unit the bot's "party member to heal" value picks right now (nullptr when none, or without an AI).
    // It only returns the single best candidate, so SimHealScenario::Pull() checks it once next to
    // LogHealTargetVisibility().
    [[nodiscard]] Unit* GetPartyMemberToHeal() const;

    // Heal mode, logged once at the pull: how many of `members` meet the conditions PartyMemberToHeal::Check() puts on
    // a heal target (same map, not charmed, alive, within 2 * AiPlayerbot.HealDistance, in line of sight), and what the
    // value picks
    void LogHealTargetVisibility(std::vector<Player*> const& members) const;

private:
    // Every enemy count the bot strategies use is built from the bot's threat list ("attackers" walks
    // ThreatManager::GetThreatenedByMeList()), and Unit::SetInCombatWith() only makes a combat reference: a dummy
    // engaged that way counts as an enemy only once it is hit, and an extra dummy never hit would never open an AoE
    // row. So each dummy engages the bot. Returns false if a dummy is still not in combat with the bot after the
    // SetInCombatWith() fallback.
    bool EngageTargets(std::vector<Creature*> const& targets);

    PlayerbotAI* _ai = nullptr;

    // The hunter pet the profile asked for (SimProfile.h's PetCreatureEntry), 0 = none
    uint32 _petCreatureEntry = 0;

    // Non-combat strategies BeginBuffPhase() removed, restored by EndBuffPhase()
    std::vector<std::string> _removedStrategies;
    bool _loggedBuffStrategies = false;
};

#endif
