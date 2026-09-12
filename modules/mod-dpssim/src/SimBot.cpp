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
    // Bootstraps combat state - see SimBot::Create()'s doc comment for why a manual cast is needed
    // at all. Which spell this is doesn't matter for that purpose (cast at most once per SimBot,
    // before the real Engine ever runs, just to get `target->IsInCombat()` true) - but it does
    // matter for EventRecorder's per-hit output: this lands as hit #0 of every run, and
    // EventRecorder tracks it like any other hit (see SimDaemon.cpp's rotationSpellId=0 comment).
    // Using SimDaemon::SINGLE_RANK_FROSTBOLT_SPELL_ID (116) rather than the old, no-longer-taught
    // FROSTBOLT_SPELL_ID (25304, Rank 11) keeps that first data point on the same scaling as every
    // other hit the real rotation lands afterward, instead of mixing in a stale-formula outlier
    // (confirmed live: 25304 hit for ~647 damage at level 80 while every real 116 hit landed at
    // ~597-599 - not the same formula).
    constexpr uint32 PULL_SPELL_ID = SimDaemon::SINGLE_RANK_FROSTBOLT_SPELL_ID;
}

SimBot::~SimBot()
{
    delete _ai;
}

bool SimBot::Create(Player* bot, Unit* target, std::string const& playerbotTalents)
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

    // Spends the talent build passed in as `playerbotTalents` - either DpsSim.PlayerbotTalents
    // directly, or a loaded DpsSim.Profile's own PlayerbotTalents value (see DpsSim.cpp and
    // SimProfile.h) - a talent string in mod-playerbots' own dash-separated tab format
    // (AiPlayerbot.PremadeSpecLink.<cls>.<spec>.<level>'s format: "<arcane><-fire><-frost>", each
    // character a 0-9 point count for that tree's talents in row/col order), parsed via
    // PlayerbotAIConfig::ParseTempTalentsOrder() and applied via
    // PlayerbotFactory::InitTalentsByParsedSpecLink() - both public, reused, unmodified
    // mod-playerbots utilities. Deliberately NOT PlayerbotFactory::InitTalentsBySpecNo(): that
    // function looks up a level-indexed premade slot (AiPlayerbot.PremadeSpecLink.<cls>.<spec>.<lvl>)
    // and has a real, live bug (confirmed 2026-09-11, reported upstream - not fixed here) where its
    // level loop walks from the bot's own level up to a hardcoded 80 rather than stopping at the
    // bot's level, so a level-60 bot ends up with additional, higher-level entries applied on top -
    // observed live turning a "frost pve" build into 18 Arcane / 3 Frost points, which flipped
    // AiFactory::GetPlayerSpecTab() to Arcane and made the "rotation" spam Arcane Blast instead of
    // Frostbolt. Owning our own talent string here (independent of level/spec-slot indexing
    // entirely) sidesteps that bug completely rather than working around it, and is also the
    // "talent config" the plan doc's M3 section asked for - see DpsSim.PlayerbotTalents' own conf
    // doc comment for the format and how to test a different build.
    //
    // This position string is only as good as the tree it was authored against - this
    // deployment's custom, expanded talent trees (confirmed live 2026-09-11: the Frost tab alone
    // carries 31 entries against a stock WotLK Frost tree's ~20, plus extra columns/tiers) mean a
    // string authored against the stock tree lands its points on different talents than intended.
    // To get a string that's guaranteed correct for THIS tree, build the intended spec on a live
    // bot (via this same mechanism, "talents apply <link>" whispered to the bot in-game, or
    // PlayerbotFactory::InitTalentsTree()'s auto-pick) and read it back with "talents link"
    // (Ai/Base/Actions/ChangeTalentsAction.cpp's new SpecLink(), added 2026-09-11) rather than
    // hand-authoring or reusing an old string - that command serializes whatever points the bot
    // actually has spent, in the tree's current live shape, via mod-playerbots' own (previously
    // unused) TalentSpec::GetTalentLink().
    //
    // Not optional for seeing "a proper rotation with conditionals and priorities" in the first
    // place: FrostMageStrategy's proc-based triggers (Fingers of Frost, Brain Freeze) and its pet
    // triggers (no/has/new pet -> Water Elemental) all gate on talents an untalented bot simply
    // doesn't have, so without spending real points the rotation can only ever be "spam Frostbolt" -
    // which is exactly and only what a zero-talent bot showed in earlier testing.
    if (!playerbotTalents.empty())
    {
        std::vector<std::vector<uint32>> const parsed = PlayerbotAIConfig::ParseTempTalentsOrder(bot->getClass(), playerbotTalents);
        PlayerbotFactory::InitTalentsByParsedSpecLink(bot, parsed, false);
    }

    // Re-teach after spending talents, same order PlayerbotFactory::Randomize() uses for a real
    // bot (InitAvailableSpells() -> InitTalentsTree() -> InitAvailableSpells() again) - some
    // talent-unlocked spells only show up as "available" on this second pass.
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
