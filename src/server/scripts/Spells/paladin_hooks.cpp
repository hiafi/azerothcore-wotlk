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

/*
 * Paladin rework - ScriptMgr handlers (paladin-rework.SHARED.md A4 / B6 item 4): logout cleanup
 * of the per-player seal/Ret/Holy state. Holy adds its own handlers in S2. Every handler checks
 * for a paladin first (these run for every class).
 */

#include "PaladinMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"

class PaladinHooksPlayer : public PlayerScript
{
public:
    PaladinHooksPlayer() : PlayerScript("PaladinHooksPlayer", { PLAYERHOOK_ON_LOGOUT }) { }

    void OnPlayerLogout(Player* player) override
    {
        if (player && player->getClass() == CLASS_PALADIN)
            Paladin::ClearState(player);
    }
};

void AddSC_paladin_hooks()
{
    new PaladinHooksPlayer();
    Paladin::LogRegistrySizes();   // after AddSC_paladin_retribution_spell_scripts() (loader order)
}
