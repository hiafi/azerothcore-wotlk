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
 * Rogue rework - ScriptMgr handlers (rogue-rework RG0a). Bodies: RogueMechanics.
 */

#include "Item.h"
#include "ItemTemplate.h"
#include "Player.h"
#include "PlayerScript.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellInfo.h"

class RoguePlayerScript : public PlayerScript
{
public:
    RoguePlayerScript() : PlayerScript("RoguePlayerScript",
        { PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_SPELL_CAST, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT }) { }

    // The energy-haste grant lives here although druids get it too: energy is a rogue resource (PLAN 1D.14) and
    // Rogue::IsEnergyUser is the one place that decides who regenerates energy faster with haste.
    void OnPlayerLogin(Player* player) override
    {
        Rogue::EnsureEnergyHaste(player);
    }

    // mod-playerbots' Randomize strips auras (and may clear spells) while a bot is in the world.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        // The recast's own triggered cast re-enters this hook before the aura exists, so only real casts re-grant.
        if (!player || !spell || spell->IsTriggered() || spell->GetSpellInfo()->Id == RogueData::SPELL_ENERGY_HASTE)
            return;

        Rogue::EnsureEnergyHaste(player);
    }

    // Poison glow (shaman imbue-glow clone): SetVisibleItemSlot (equip, swap, enchant, login inventory load) just
    // rewrote the slot's real enchant visuals; write the glow back over the temp half while a poison is up.
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* item) override
    {
        if (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND)
            return;

        if (!player || !item || item->GetTemplate()->Class != ITEM_CLASS_WEAPON)
            return;

        if (Rogue::HasAnyPoison(player))
            Rogue::WritePoisonGlow(player, slot);
    }
};

void AddSC_rogue_hooks()
{
    new RoguePlayerScript();
}
