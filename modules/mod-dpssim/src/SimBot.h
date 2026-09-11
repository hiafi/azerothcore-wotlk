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
    // not the one hardcoded id Phase 1's rotation used) - then "pulls" `target` with one
    // manually-cast spell to bootstrap combat state. That pull is necessary, not just convenient:
    // PlayerbotAI::DoNextAction() only switches to the combat engine (and therefore to
    // FrostMageStrategy's triggers) once `bot->IsInCombat()` is true, and a Player's Attack() call
    // alone does not flag combat immediately for a player-controlled unit - real combat entry
    // happens "on contact" (a landed swing or spell hit), and the non-combat engine has no
    // automatic engage/pull action for an unconfigured mage by default. Once that first hit lands,
    // control passes entirely to the real Engine from the next UpdateAI() tick onward. Returns
    // false (logging why) on failure.
    bool Create(Player* bot, Unit* target);

    // Drives the real Engine/Strategy selector for one tick - call this from the SimClock loop
    // instead of a hardcoded RotationTick(). `diff` is not a wall-clock read: PlayerbotAIBase's
    // own throttling (PlayerbotAIConfig.reactDelay - how often a bot actually "thinks") is driven
    // purely by the `diff` values passed in here (see PlayerbotAIBase::UpdateAI()/YieldThread()),
    // so it respects the sim clock the same way GCD/cooldowns do (core patch 2) - confirmed by
    // reading its implementation, not assumed.
    void UpdateAI(uint32 diff);

private:
    PlayerbotAI* _ai = nullptr;
};

#endif
