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

#include "SimBot.h"
#include "Log.h"
#include "Player.h"
#include "PlayerbotFactory.h"
#include "Playerbots.h"
#include "SimDaemon.h"

namespace
{
    // Reuses Phase 1's own pilot spell (Frostbolt Rank 11 - see SimDaemon.h's doc comment on
    // FROSTBOLT_SPELL_ID) purely to bootstrap combat state - see SimBot::Create()'s doc comment
    // for why a manual cast is needed at all. Not load-bearing which spell this is: cast at most
    // once per SimBot, before the real Engine ever runs, just to get `target->IsInCombat()` true.
    constexpr uint32 PULL_SPELL_ID = SimDaemon::FROSTBOLT_SPELL_ID;
}

SimBot::~SimBot()
{
    delete _ai;
}

bool SimBot::Create(Player* bot, Unit* target)
{
    if (!bot || !target)
        return false;

    // Teaches every trainer-taught spell appropriate to the bot's class/level - the same,
    // unmodified utility a real random bot uses (PlayerbotFactory::InitAvailableSpells(),
    // src/Bot/Factory/PlayerbotFactory.cpp). Touches zero SQL: it self-casts a "teach spell"
    // trigger spell per learnable spell, same mechanism as SimActor's own learnSpell() calls (see
    // that class's doc comment) - just iterated over every spell the bot's trainers would teach
    // instead of one hardcoded id, since FrostMageStrategy's actions reference several spells
    // (Frostbolt, Ice Lance, Fire Blast, Frost Nova, ...).
    PlayerbotFactory factory(bot, bot->GetLevel());
    factory.InitAvailableSpells();

    // Build the PlayerbotAI through PlayerbotsMgr::AddPlayerbotData() - the same entry point a
    // real bot login uses - rather than `new PlayerbotAI(bot)` directly, and keep only a borrowed
    // pointer to it (~SimBot() still owns cleanup via delete, same as before; see its comment).
    // This class's original design deliberately skipped PlayerbotsMgr registration on the theory
    // that nothing would ever need to look this bot up via GET_PLAYERBOT_AI(). That assumption was
    // wrong: mod-playerbots' OWN internal logic calls GET_PLAYERBOT_AI(bot) on itself, not just for
    // external lookups by a master. Concretely, AttackersValue::IsPossibleTarget() - the function
    // backing the "current target"/"invalid target" trigger - opens with
    // `if (!GET_PLAYERBOT_AI(bot)) return false;`. Unregistered, that always returns false, so
    // every target (including our own seeded one) reads as impossible, the "invalid target"
    // trigger fires "drop target" (relevance 99, beating every default-action relevance in
    // FrostMageStrategy, which top out at 10), and the bot permanently loses its target the first
    // time that trigger gets evaluated - which is itself throttled to only happen once `minimal`
    // mode clears (see AllowActivity()/BotActiveAlone below), explaining why this looked like a
    // silent "the queue never runs anything" bug rather than an obvious immediate failure.
    // Confirmed via live instrumentation, not guessed.
    PlayerbotsMgr::instance().AddPlayerbotData(bot, true);
    _ai = PlayerbotsMgr::instance().GetPlayerbotAI(bot);
    if (!_ai)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimBot::Create() - PlayerbotsMgr::AddPlayerbotData() did not produce a PlayerbotAI.");
        return false;
    }

    // Seed the AiObjectContext's own "current target" value. This is NOT the same as
    // bot->SetSelection() - CurrentTargetValue (Ai/Base/Value/CurrentTargetValue.cpp) keeps its
    // own internal GUID (`selection`), set only via this Value's own Set(), never read from the
    // Player's live selection. CastSpellAction::GetTargetName() (the base class every class's
    // "cast this spell" action derives from, including CastFrostboltAction) resolves its target
    // through exactly this value ({ return "current target"; }) - without seeding it, every such
    // action has no target to act on and silently reports itself not possible/useful, which is
    // why the real rotation did nothing at all in the first live test of this class (confirmed via
    // a live diagnostic: bot->IsInCombat() read true for 5 real seconds with zero action taken).
    _ai->GetAiObjectContext()->GetValue<Unit*>("current target")->Set(target);

    // Bootstrap combat - see this class's doc comment on Create() for why this is needed rather
    // than just calling bot->Attack(target, true) and waiting.
    SpellCastResult result = bot->CastSpell(target, PULL_SPELL_ID, false);
    if (result != SPELL_CAST_OK)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimBot::Create() - pull cast failed: SpellCastResult {}.", uint32(result));
        return false;
    }

    // The pull cast alone is not enough: PlayerbotAI::DoNextAction() never switches
    // currentEngine to BOT_STATE_COMBAT on its own just because bot->IsInCombat() is true - that
    // switch only happens from inside specific actions (AttackAction/PullActions, both call
    // ChangeEngine(BOT_STATE_COMBAT) themselves), which are normally reached via a master's
    // "attack" command or a non-combat "being attacked" trigger, neither of which applies to an
    // autonomous, masterless bot pulling a passive, never-retaliating target dummy. Confirmed by
    // a live diagnostic run: bot->IsInCombat() read true for a full 5 seconds after the pull
    // landed (matching the training dummy's own 5s combat-timeout - see SimTarget.h) while
    // GetState() stayed BOT_STATE_NON_COMBAT the entire time, so the engine never got a chance to
    // act on it - Engine::DoNextAction() was never called on the combat engine at all. We are
    // standing in for "the thing that decided to pull" here, so it's our job to do what a real
    // pull action would have done: flip the engine ourselves, once, right after the pull lands.
    _ai->ChangeEngine(BOT_STATE_COMBAT);

    return true;
}

void SimBot::UpdateAI(uint32 diff)
{
    if (_ai)
        _ai->UpdateAI(diff);
}
