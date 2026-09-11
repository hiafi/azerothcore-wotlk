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

#include "SimActor.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "WorldSession.h"

SimActor::~SimActor()
{
    // WorldSession::LogoutPlayer() is the one correct teardown path for a live Player - it runs
    // the full script-hook chain (OnPlayerBeforeLogout et al - real modules like mod-dungeon-clear
    // depend on this firing before the Player disappears), CleanupsBeforeDelete(), and
    // Map::RemovePlayerFromMap(), and it deletes _player itself (see its "pointer already
    // deleted" comment before SetPlayer(nullptr)).
    //
    // Do NOT also delete _player here: an earlier version of this destructor did exactly that,
    // then called `delete _session`, whose own destructor unconditionally calls LogoutPlayer(true)
    // again on the (now-dangling) _player pointer - script hooks like DcSpectator::Stop() dereference
    // it and it crashes. Calling LogoutPlayer(false) ourselves first (save=false, since this actor
    // was never in the characters table - see Create()'s "zero SQL" construction) leaves _session's
    // own _player null, so ~WorldSession()'s internal LogoutPlayer(true) call becomes a no-op guard
    // hit rather than a second teardown.
    //
    // redirecting=true (LogoutPlayer's second param) skips its `if (!redirecting)` block -
    // SendFriendStatus/RemovePlayerSocial (via sSocialMgr) and the OnPlayerLogout hook. Required,
    // not just an optimization: SendFriendStatus dereferences player->GetSocial(), which is only
    // ever populated by a real DB login's _LoadSocialList() (Player::m_social defaults to
    // nullptr - see Player.cpp) - this synthetic actor never runs that, so without redirecting=true
    // SocialMgr::GetFriendInfo() null-derefs and crashes. OnPlayerBeforeLogout (the hook
    // DcSpectator::Stop needs) fires unconditionally earlier in LogoutPlayer, before this guard -
    // skipping the redirecting-guarded block does not skip that.
    if (_session && _session->GetPlayer())
        _session->LogoutPlayer(false, true);

    delete _session;
}

bool SimActor::Create(Config const& config)
{
    // accountId 0, no name, no socket, isBot = true: WorldSession's constructor special-cases
    // exactly this (no LoginDatabase touch, m_Address = "bot") - see the Phase 0 spike write-up
    // in the plan doc.
    _session = new WorldSession(0, "", 0x0, nullptr, SEC_PLAYER, EXPANSION_WRATH_OF_THE_LICH_KING,
        time_t(0), LOCALE_enUS, 0, false, false, 0, /*isBot=*/true);

    CharacterCreateInfo createInfo(config.Name, config.Race, config.Class, config.Gender,
        /*skin*/0, /*face*/0, /*hairStyle*/0, /*hairColor*/0, /*facialHair*/0);

    _player = new Player(_session);
    _player->GetMotionMaster()->Initialize();
    if (!_player->Create(sObjectMgr->GetGenerator<HighGuid::Player>().Generate(), &createInfo))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimActor::Create() - Player::Create() failed (race {}, class {}) - check the race/class combo is valid.",
            config.Race, config.Class);
        delete _player;
        _player = nullptr;
        delete _session;
        _session = nullptr;
        return false;
    }

    _session->SetPlayer(_player);
    _player->setCinematic(2);
    _player->SetAtLoginFlag(AT_LOGIN_NONE);

    // GiveLevel() takes the character from its level-1 creation baseline to Config.Level using
    // the same PlayerLevelInfo/PlayerClassLevelInfo tables a real level-up uses, ending with a
    // full UpdateAllStats()/SetFullHealth()/full-mana call already built in.
    _player->GiveLevel(config.Level);
    _player->InitTalentForLevel();

    if (config.SpellPower != 0)
    {
        // Order matters: ApplySpellPowerBonus() only bumps the internal m_baseSpellPower
        // accumulator: the UpdateAllStats() call below is what actually bakes it into the damage
        // formula (Unit::SpellBaseDamageBonusDone() reads m_baseSpellPower fresh each time it's
        // called from UpdateSpellDamageAndHealingBonus()).
        _player->ApplySpellPowerBonus(config.SpellPower, true);
        _player->UpdateAllStats();
        _player->SetFullHealth();
        _player->SetPower(POWER_MANA, _player->GetMaxPower(POWER_MANA));
    }

    ObjectAccessor::AddObject(_player);
    if (!_player->GetMap()->AddPlayerToMap(_player))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimActor::Create() - AddPlayerToMap() failed.");
        return false;
    }

    LOG_INFO("server.dpssim", "mod-dpssim: SimActor created - '{}' (race {}, class {}, level {}), map {}, spellPower {}.",
        config.Name, config.Race, config.Class, config.Level, _player->GetMapId(), config.SpellPower);
    return true;
}
