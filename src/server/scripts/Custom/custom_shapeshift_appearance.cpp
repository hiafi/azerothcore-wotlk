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

// Custom: player-chosen Bear Form appearance (docs/bear-form-appearances.md).
//
// npc_bear_appearance (creature_template 900012) offers a catalogue of bear models via gossip. The
// choice is stored in characters.character_shapeshift_appearance and set on the Player, where
// ObjectMgr::GetModelForShapeshift picks it up ahead of the race/hair-colour defaults - so every
// path that re-derives the form model (shifting, relog, death, transform auras ending) uses it.
//
// It is loaded in OnPlayerLoadFromDB, which runs before the saved auras are re-applied: a player who
// logged out in bear form comes back in the chosen model without any refresh.
//
// Display IDs 90100-90149 are minted by apps/dbc-tools/build_patch_f.py (client files ship in
// patch-F.mpq, DBC rows in patch-M.mpq); the Night Elf / Tauren entries are stock client displays.

#include "Chat.h"
#include "CreatureScript.h"
#include "DatabaseEnv.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptedGossip.h"
#include <array>
#include <string>
#include <vector>

namespace
{
    constexpr uint32 NPC_TEXT_BEAR_APPEARANCE = 900012;

    enum BearAppearanceGossip
    {
        SENDER_MENU                 = GOSSIP_SENDER_MAIN,
        SENDER_CATEGORY,            // action = category index
        SENDER_APPEARANCE,          // action = display id

        ACTION_SHOW_CATEGORIES      = GOSSIP_ACTION_INFO_DEF,
        ACTION_RESET
    };

    // Dire Bear Form shares Bear Form's choice; it is stored once, under FORM_BEAR.
    constexpr std::array<ShapeshiftForm, 2> BEAR_FORMS = { FORM_BEAR, FORM_DIREBEAR };

    struct BearAppearance
    {
        uint32 DisplayId;
        char const* Name;
    };

    struct BearAppearanceCategory
    {
        char const* Name;
        std::vector<BearAppearance> Appearances;
    };

    std::vector<BearAppearanceCategory> const BearAppearanceCategories =
    {
        { "Night Elf", { { 29413, "Purple" }, { 29414, "Black" }, { 29415, "Blue" }, { 29416, "White" },
                         { 29417, "Red" } } },
        { "Tauren", { { 2289, "Brown" }, { 29418, "Black" }, { 29419, "Silver" }, { 29420, "Yellow" },
                      { 29421, "White" } } },
        { "Troll", { { 90100, "Blue" }, { 90101, "Purple" }, { 90102, "Red" }, { 90103, "White" },
                     { 90104, "Yellow" } } },
        { "Armored Troll", { { 90105, "Blue" }, { 90106, "Purple" }, { 90107, "Red" }, { 90108, "White" },
                             { 90109, "Yellow" } } },
        { "Claws of Ursoc I", { { 90110, "Black" }, { 90111, "Blue" }, { 90112, "Brown" }, { 90113, "Burgundy" },
                                { 90114, "Gold" }, { 90115, "Purple" }, { 90116, "White" },
                                { 90117, "Val'sharah" } } },
        { "Claws of Ursoc II", { { 90118, "Cool" }, { 90119, "Dark" }, { 90120, "Green" }, { 90121, "Pink" } } },
        { "Claws of Ursoc III", { { 90122, "Blue" }, { 90123, "Green" }, { 90124, "Purple" }, { 90125, "Red" } } },
        { "Claws of Ursoc IV", { { 90126, "Blue" }, { 90127, "Brown" }, { 90128, "Green" }, { 90129, "Red" } } },
        { "Claws of Ursoc V", { { 90130, "Black" }, { 90131, "Brown" }, { 90132, "Red" }, { 90133, "White" } } },
        { "Claws of Ursoc VI", { { 90134, "White" }, { 90135, "Brown" }, { 90136, "Blonde" }, { 90137, "Black" } } },
        { "Kul Tiran", { { 90138, "Brown" }, { 90139, "Dark" }, { 90140, "Green" }, { 90141, "Light" } } },
        { "Zandalari", { { 90142, "Blue" }, { 90143, "Dark" }, { 90144, "Green" }, { 90145, "White" } } },
        { "Zandalari, Unarmored", { { 90146, "Black" }, { 90147, "Blue" }, { 90148, "Green" }, { 90149, "White" } } },
    };

    std::pair<BearAppearanceCategory const*, BearAppearance const*> FindBearAppearance(uint32 displayId)
    {
        for (BearAppearanceCategory const& category : BearAppearanceCategories)
            for (BearAppearance const& appearance : category.Appearances)
                if (appearance.DisplayId == displayId)
                    return { &category, &appearance };

        return { nullptr, nullptr };
    }

    bool IsBearForm(ShapeshiftForm form)
    {
        return form == FORM_BEAR || form == FORM_DIREBEAR;
    }

    // displayId 0 restores the race/hair-colour default.
    void SetBearAppearance(Player* player, uint32 displayId)
    {
        for (ShapeshiftForm form : BEAR_FORMS)
            player->SetShapeshiftAppearance(form, displayId);

        CharacterDatabasePreparedStatement* stmt;
        if (displayId)
        {
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_REP_SHAPESHIFT_APPEARANCE);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, uint8(FORM_BEAR));
            stmt->SetData(2, displayId);
        }
        else
        {
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_DEL_SHAPESHIFT_APPEARANCE);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, uint8(FORM_BEAR));
        }
        CharacterDatabase.Execute(stmt);

        // Already shifted: re-derive the model now (same precedence rules as an aura ending)
        if (IsBearForm(player->GetShapeshiftForm()))
            player->RestoreDisplayId();
    }
}

class npc_bear_appearance : public CreatureScript
{
public:
    npc_bear_appearance() : CreatureScript("npc_bear_appearance") { }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        SendCategoryMenu(player, creature);
        return true;
    }

    bool OnGossipSelect(Player* player, Creature* creature, uint32 sender, uint32 action) override
    {
        ClearGossipMenuFor(player);

        switch (sender)
        {
            case SENDER_CATEGORY:
                if (action < BearAppearanceCategories.size())
                    SendAppearanceMenu(player, creature, action);
                else
                    CloseGossipMenuFor(player);
                break;
            case SENDER_APPEARANCE:
            {
                auto [category, appearance] = FindBearAppearance(action);
                if (!appearance)
                {
                    CloseGossipMenuFor(player);
                    break;
                }

                SetBearAppearance(player, appearance->DisplayId);
                ChatHandler(player->GetSession()).PSendSysMessage("Your bear form now takes the shape of: {} - {}.",
                    category->Name, appearance->Name);
                // Stay on the same page so a shifted player can flick through colours
                SendAppearanceMenu(player, creature, uint32(category - BearAppearanceCategories.data()));
                break;
            }
            case SENDER_MENU:
            default:
                if (action == ACTION_RESET)
                {
                    SetBearAppearance(player, 0);
                    ChatHandler(player->GetSession()).SendSysMessage(
                        "Your bear form has returned to its natural shape.");
                }
                SendCategoryMenu(player, creature);
                break;
        }

        return true;
    }

private:
    static void SendCategoryMenu(Player* player, Creature* creature)
    {
        ClearGossipMenuFor(player);

        uint32 const current = player->GetShapeshiftAppearance(FORM_BEAR);
        for (uint32 i = 0; i < BearAppearanceCategories.size(); ++i)
        {
            BearAppearanceCategory const& category = BearAppearanceCategories[i];
            bool const isCurrent = current && FindBearAppearance(current).first == &category;
            std::string const text = isCurrent ? Acore::StringFormat("{} (current)", category.Name) : category.Name;
            AddGossipItemFor(player, GOSSIP_ICON_TABARD, text, SENDER_CATEGORY, i);
        }

        if (current)
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Restore my natural bear form.", SENDER_MENU, ACTION_RESET);

        SendGossipMenuFor(player, NPC_TEXT_BEAR_APPEARANCE, creature);
    }

    static void SendAppearanceMenu(Player* player, Creature* creature, uint32 categoryIndex)
    {
        ClearGossipMenuFor(player);

        uint32 const current = player->GetShapeshiftAppearance(FORM_BEAR);
        for (BearAppearance const& appearance : BearAppearanceCategories[categoryIndex].Appearances)
        {
            bool const isCurrent = appearance.DisplayId == current;
            std::string const text = isCurrent ? Acore::StringFormat("{} (current)", appearance.Name) : appearance.Name;
            AddGossipItemFor(player, GOSSIP_ICON_INTERACT_1, text, SENDER_APPEARANCE, appearance.DisplayId);
        }

        AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Back", SENDER_MENU, ACTION_SHOW_CATEGORIES);
        SendGossipMenuFor(player, NPC_TEXT_BEAR_APPEARANCE, creature);
    }
};

class ShapeshiftAppearance_PlayerScript : public PlayerScript
{
public:
    ShapeshiftAppearance_PlayerScript() : PlayerScript("ShapeshiftAppearance_PlayerScript",
        { PLAYERHOOK_ON_LOAD_FROM_DB, PLAYERHOOK_ON_DELETE_FROM_DB }) { }

    // Synchronous on purpose: this has to land before LoadFromDB re-applies a saved bear form aura.
    void OnPlayerLoadFromDB(Player* player) override
    {
        CharacterDatabasePreparedStatement* stmt =
            CharacterDatabase.GetPreparedStatement(CHAR_SEL_SHAPESHIFT_APPEARANCES);
        stmt->SetData(0, player->GetGUID().GetCounter());
        PreparedQueryResult result = CharacterDatabase.Query(stmt);
        if (!result)
            return;

        do
        {
            Field* fields = result->Fetch();
            uint8 const form = fields[0].Get<uint8>();
            uint32 const displayId = fields[1].Get<uint32>();

            if (form != FORM_BEAR || !FindBearAppearance(displayId).second)
            {
                LOG_WARN("entities.player",
                    "character_shapeshift_appearance: {} has unknown form {} / display {}, ignored",
                    player->GetGUID().ToString(), form, displayId);
                continue;
            }

            for (ShapeshiftForm bearForm : BEAR_FORMS)
                player->SetShapeshiftAppearance(bearForm, displayId);
        } while (result->NextRow());
    }

    void OnPlayerDeleteFromDB(CharacterDatabaseTransaction trans, uint32 guid) override
    {
        CharacterDatabasePreparedStatement* stmt =
            CharacterDatabase.GetPreparedStatement(CHAR_DEL_SHAPESHIFT_APPEARANCES);
        stmt->SetData(0, guid);
        trans->Append(stmt);
    }
};

void AddSC_custom_shapeshift_appearance()
{
    new npc_bear_appearance();
    new ShapeshiftAppearance_PlayerScript();
}
