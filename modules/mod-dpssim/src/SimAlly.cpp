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

#include "SimAlly.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "PlayerbotAIConfig.h"
#include "PlayerbotFactory.h"
#include "Playerbots.h"
#include <cmath>
#include <vector>

uint8 SimAlly::ClassFor(SimHeal::Role role, uint8 race)
{
    if (role == SimHeal::Role::Tank)
        return CLASS_WARRIOR;

    // A DPS ally is a class PlayerbotAI::IsTank(player, true) can never call a tank. A Rogue is the safe choice; a
    // Tauren or Draenei cannot be one, and an untalented Warrior falls to the Arms tab, which is not a tank either.
    return sObjectMgr->GetPlayerInfo(race, CLASS_ROGUE) ? uint8(CLASS_ROGUE) : uint8(CLASS_WARRIOR);
}

void SimAlly::PinBaseMaxHealth(Player* player, uint32 maxHealth)
{
    // Max health is pinned through the BASE part of UNIT_MOD_HEALTH alone (plan R4): Player::UpdateMaxHealth() is
    // ((BASE flat + create health) * BASE pct + TOTAL flat + stamina bonus) * TOTAL pct. The base flat value is moved so
    // that the unbuffed total is exactly maxHealth, the class's create health and base stamina included, and a
    // Fortitude, Mark of the Wild or Kings later raises Stamina on top as in game.
    float const basePct = player->GetPctModifierValue(UNIT_MOD_HEALTH, BASE_PCT);
    float const totalPct = player->GetPctModifierValue(UNIT_MOD_HEALTH, TOTAL_PCT);
    float const multiplier = basePct * totalPct;
    if (multiplier > 0.0f)
    {
        // +0.5 so the (uint32) truncation in UpdateMaxHealth() lands on the target, not one below it
        float const delta = (float(maxHealth) - float(player->GetMaxHealth()) + 0.5f) / multiplier;
        player->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE,
            player->GetFlatModifierValue(UNIT_MOD_HEALTH, BASE_VALUE) + delta);
        player->UpdateMaxHealth();
    }
    player->SetFullHealth();

    if (player->GetMaxHealth() != maxHealth)
        LOG_WARN("server.dpssim", "mod-dpssim: '{}' max health is {}, wanted {} (health modifiers: base pct {}, total "
            "pct {}).", player->GetName(), player->GetMaxHealth(), maxHealth, basePct, totalPct);
}

bool SimAlly::Create(Config const& config)
{
    SimActor::Config actorConfig;
    actorConfig.Name = config.Name;
    actorConfig.Race = config.Race;
    actorConfig.Class = ClassFor(config.AllyRole, config.Race);
    actorConfig.Gender = GENDER_MALE;
    actorConfig.Level = config.Level;
    actorConfig.HasPosition = true;
    actorConfig.PositionX = config.PositionX;
    actorConfig.PositionY = config.PositionY;
    actorConfig.PositionZ = config.PositionZ;
    actorConfig.PositionO = config.PositionO;
    if (!_actor.Create(actorConfig))
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimAlly::Create() - SimActor::Create() failed for '{}' (race {}, "
            "class {}).", config.Name, config.Race, actorConfig.Class);
        return false;
    }

    Player* player = _actor.GetPlayer();

    // The same spend SimBot::Create() does for the healer, before any AI exists
    if (!config.Talents.empty())
    {
        std::vector<std::vector<uint32>> const parsed =
            PlayerbotAIConfig::ParseTempTalentsOrder(player->getClass(), config.Talents);
        PlayerbotFactory::InitTalentsByParsedSpecLink(player, parsed, false);
        player->UpdateAllStats();
    }

    PinBaseMaxHealth(player, config.BaseMaxHealth);

    LOG_INFO("server.dpssim", "mod-dpssim: SimAlly '{}' - {} class {}, level {}, max health {}, at ({:.1f}, {:.1f}).",
        config.Name, SimHeal::RoleName(config.AllyRole), uint32(player->getClass()), uint32(player->GetLevel()),
        player->GetMaxHealth(), player->GetPositionX(), player->GetPositionY());
    return true;
}
