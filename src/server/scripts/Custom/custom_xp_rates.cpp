/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// Custom: dungeon boss kills grant bonus XP on top of Rate.XP.Kill.
// Quest XP is boosted separately via Rate.XP.Quest / Rate.XP.Quest.DF in worldserver.conf - no
// script needed there, since that rate already only applies to quest rewards. Rate.XP.Kill, on
// the other hand, applies to every creature kill, so a plain rate bump would also buff trash
// mobs. This script instead multiplies only kills of creatures flagged as dungeon bosses
// (Creature::IsDungeonBoss(), set dynamically for creatures registered as instance boss data).

#include "Config.h"
#include "Creature.h"
#include "Player.h"
#include "ScriptMgr.h"

class Custom_XPRates : public PlayerScript
{
public:
    Custom_XPRates() : PlayerScript("Custom_XPRates") { }

    void OnPlayerGiveXP(Player* /*player*/, uint32& amount, Unit* victim, uint8 xpSource) override
    {
        if (xpSource != PlayerXPSource::XPSOURCE_KILL || !victim)
        {
            return;
        }

        Creature const* creature = victim->ToCreature();
        if (!creature || !creature->IsDungeonBoss())
        {
            return;
        }

        static float const rate = sConfigMgr->GetOption<float>("Custom.XP.DungeonBoss.Rate", 10.0f);
        amount = uint32(amount * rate);
    }
};

void AddSC_custom_xp_rates()
{
    new Custom_XPRates();
}
