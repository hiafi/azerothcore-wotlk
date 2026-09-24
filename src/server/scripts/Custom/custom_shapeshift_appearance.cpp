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

// Custom: player-chosen shapeshift appearance - Bear Form and Cat Form (docs/shapeshift-appearances.md).
//
// npc_shapeshift_appearance (creature_template 900012) offers a catalogue of models per form via
// gossip. The choice is stored in characters.character_shapeshift_appearance and set on the Player,
// where ObjectMgr::GetModelForShapeshift picks it up ahead of the race/hair-colour defaults - so every
// path that re-derives the form model (shifting, relog, death, transform auras ending) uses it.
//
// It is loaded in OnPlayerLoadFromDB, which runs before the saved auras are re-applied: a player who
// logged out shifted comes back in the chosen model without any refresh.
//
// Display IDs 901xx (bear) / 902xx (cat) are minted by apps/dbc-tools/build_patch_f.py (client files
// ship in patch-F.mpq, DBC rows in patch-M.mpq); every other ID below is a stock client display.

#include "Chat.h"
#include "CreatureScript.h"
#include "DatabaseEnv.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptedGossip.h"
#include <string>
#include <vector>

namespace
{
    constexpr uint32 NPC_TEXT_SHAPESHIFT_APPEARANCE = 900012;

    enum ShapeshiftAppearanceGossip
    {
        SENDER_MAIN_MENU            = GOSSIP_SENDER_MAIN,
        SENDER_FORM,                // action = set index
        SENDER_CATEGORY,            // action = set index * CATEGORY_STRIDE + category index
        SENDER_APPEARANCE,          // action = display id
        SENDER_RESET                // action = set index
    };

    constexpr uint32 CATEGORY_STRIDE = 100;

    struct Appearance
    {
        uint32 DisplayId;
        char const* Name;
    };

    struct AppearanceCategory
    {
        char const* Name;
        std::vector<Appearance> Appearances;
    };

    struct AppearanceSet
    {
        char const* Name;                   // menu label
        char const* Noun;                   // chat messages
        ShapeshiftForm StorageForm;         // the choice is stored once, under this form
        std::vector<ShapeshiftForm> Forms;  // ...and applies to all of these
        std::vector<AppearanceCategory> Categories;
    };

    std::vector<AppearanceSet> const AppearanceSets =
    {
        { "Bear Form", "bear form", FORM_BEAR, { FORM_BEAR, FORM_DIREBEAR },
        {
            { "Night Elf", { { 29413, "Purple" }, { 29414, "Black" }, { 29415, "Blue" }, { 29416, "White" },
                             { 29417, "Red" } } },
            { "Tauren", { { 2289, "Brown" }, { 29418, "Black" }, { 29419, "Silver" }, { 29420, "Yellow" },
                          { 29421, "White" } } },
            { "Troll", { { 90100, "Blue" }, { 90101, "Purple" }, { 90102, "Red" }, { 90103, "White" },
                         { 90104, "Yellow" } } },
            { "Armored Troll", { { 90105, "Blue" }, { 90106, "Purple" }, { 90107, "Red" }, { 90108, "White" },
                                 { 90109, "Yellow" } } },
            { "Claws of Ursoc I", { { 90110, "Black" }, { 90111, "Blue" }, { 90112, "Brown" },
                                    { 90113, "Burgundy" }, { 90114, "Gold" }, { 90115, "Purple" },
                                    { 90116, "White" }, { 90117, "Val'sharah" } } },
            { "Claws of Ursoc II", { { 90118, "Cool" }, { 90119, "Dark" }, { 90120, "Green" }, { 90121, "Pink" } } },
            { "Claws of Ursoc III", { { 90122, "Blue" }, { 90123, "Green" }, { 90124, "Purple" },
                                      { 90125, "Red" } } },
            { "Claws of Ursoc IV", { { 90126, "Blue" }, { 90127, "Brown" }, { 90128, "Green" }, { 90129, "Red" } } },
            { "Claws of Ursoc V", { { 90130, "Black" }, { 90131, "Brown" }, { 90132, "Red" }, { 90133, "White" } } },
            { "Claws of Ursoc VI", { { 90134, "White" }, { 90135, "Brown" }, { 90136, "Blonde" },
                                     { 90137, "Black" } } },
            { "Kul Tiran", { { 90138, "Brown" }, { 90139, "Dark" }, { 90140, "Green" }, { 90141, "Light" } } },
            { "Zandalari", { { 90142, "Blue" }, { 90143, "Dark" }, { 90144, "Green" }, { 90145, "White" } } },
            { "Zandalari, Unarmored", { { 90146, "Black" }, { 90147, "Blue" }, { 90148, "Green" },
                                        { 90149, "White" } } },
        } },
        { "Cat Form", "cat form", FORM_CAT, { FORM_CAT },
        {
            { "Night Elf", { { 892, "Black" }, { 29405, "Violet" }, { 29406, "Purple" }, { 29407, "Dark Blue" },
                             { 29408, "White" } } },
            { "Tauren", { { 8571, "Brown" }, { 29409, "White" }, { 29410, "Yellow" }, { 29411, "Red" },
                          { 29412, "Black" } } },
            { "Lynx", { { 15593, "Red" }, { 18167, "Yellow" }, { 90250, "Painted" } } },
            { "Troll", { { 90200, "Black" }, { 90201, "Blue" }, { 90202, "Green" }, { 90203, "Red" },
                         { 90204, "White" } } },
            { "Armored Troll", { { 90205, "Black" }, { 90206, "Blue" }, { 90207, "Green" }, { 90208, "Red" },
                                 { 90209, "White" } } },
            { "Fangs of Ashamane I", { { 90210, "Black" }, { 90211, "Blue" }, { 90212, "Brown" },
                                       { 90213, "Orange" }, { 90214, "Purple" }, { 90215, "Val'sharah" },
                                       { 90216, "White" } } },
            { "Fangs of Ashamane II", { { 90217, "Blue" }, { 90218, "Green" }, { 90219, "Purple" },
                                        { 90220, "Red" } } },
            { "Fangs of Ashamane III", { { 90221, "Blue" }, { 90222, "Green" }, { 90223, "Orange" },
                                         { 90224, "White" } } },
            { "Fangs of Ashamane IV", { { 90225, "Green" }, { 90226, "Orange" }, { 90227, "Purple" },
                                        { 90228, "White" } } },
            { "Fangs of Ashamane V", { { 90229, "Blue" }, { 90230, "Green" }, { 90231, "Orange" },
                                       { 90232, "Red" } } },
            { "Kul Tiran", { { 90233, "Brown" }, { 90234, "Dark" }, { 90235, "Green" }, { 90236, "Light" } } },
            { "Kul Tiran, Unarmored", { { 90237, "Brown" }, { 90238, "Dark" }, { 90239, "Green" },
                                        { 90240, "Light" } } },
            { "Zandalari", { { 90241, "Black" }, { 90242, "Blue" }, { 90243, "Green" }, { 90244, "White" } } },
            { "Zandalari, Unarmored", { { 90245, "Black" }, { 90246, "Blue" }, { 90247, "Green" },
                                        { 90248, "White" } } },
            { "Treant", { { 90249, "Bark" } } },
        } },
    };

    struct AppearanceLookup
    {
        AppearanceSet const* Set = nullptr;
        AppearanceCategory const* Category = nullptr;
        Appearance const* Entry = nullptr;
    };

    // Display IDs are unique across sets, so the ID alone identifies the form it belongs to.
    AppearanceLookup FindAppearance(uint32 displayId)
    {
        for (AppearanceSet const& set : AppearanceSets)
            for (AppearanceCategory const& category : set.Categories)
                for (Appearance const& appearance : category.Appearances)
                    if (appearance.DisplayId == displayId)
                        return { &set, &category, &appearance };

        return { };
    }

    bool SetHasForm(AppearanceSet const& set, ShapeshiftForm form)
    {
        for (ShapeshiftForm setForm : set.Forms)
            if (setForm == form)
                return true;

        return false;
    }

    void ApplyAppearance(Player* player, AppearanceSet const& set, uint32 displayId)
    {
        for (ShapeshiftForm form : set.Forms)
            player->SetShapeshiftAppearance(form, displayId);
    }

    // displayId 0 restores the race/hair-colour default.
    void SetAppearance(Player* player, AppearanceSet const& set, uint32 displayId)
    {
        ApplyAppearance(player, set, displayId);

        CharacterDatabasePreparedStatement* stmt;
        if (displayId)
        {
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_REP_SHAPESHIFT_APPEARANCE);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, uint8(set.StorageForm));
            stmt->SetData(2, displayId);
        }
        else
        {
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_DEL_SHAPESHIFT_APPEARANCE);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, uint8(set.StorageForm));
        }
        CharacterDatabase.Execute(stmt);

        // Already shifted: re-derive the model now (same precedence rules as an aura ending)
        if (SetHasForm(set, player->GetShapeshiftForm()))
            player->RestoreDisplayId();
    }

    std::string MarkCurrent(char const* name, bool isCurrent)
    {
        return isCurrent ? Acore::StringFormat("{} (current)", name) : name;
    }
}

class npc_shapeshift_appearance : public CreatureScript
{
public:
    npc_shapeshift_appearance() : CreatureScript("npc_shapeshift_appearance") { }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        SendFormMenu(player, creature);
        return true;
    }

    bool OnGossipSelect(Player* player, Creature* creature, uint32 sender, uint32 action) override
    {
        ClearGossipMenuFor(player);

        switch (sender)
        {
            case SENDER_FORM:
                if (action < AppearanceSets.size())
                    SendCategoryMenu(player, creature, action);
                else
                    CloseGossipMenuFor(player);
                break;
            case SENDER_CATEGORY:
            {
                uint32 const setIndex = action / CATEGORY_STRIDE;
                uint32 const categoryIndex = action % CATEGORY_STRIDE;
                if (setIndex < AppearanceSets.size() && categoryIndex < AppearanceSets[setIndex].Categories.size())
                    SendAppearanceMenu(player, creature, setIndex, categoryIndex);
                else
                    CloseGossipMenuFor(player);
                break;
            }
            case SENDER_APPEARANCE:
            {
                AppearanceLookup const lookup = FindAppearance(action);
                if (!lookup.Entry)
                {
                    CloseGossipMenuFor(player);
                    break;
                }

                SetAppearance(player, *lookup.Set, lookup.Entry->DisplayId);
                ChatHandler(player->GetSession()).PSendSysMessage("Your {} now takes the shape of: {} - {}.",
                    lookup.Set->Noun, lookup.Category->Name, lookup.Entry->Name);
                // Stay on the same page so a shifted player can flick through colours
                SendAppearanceMenu(player, creature, uint32(lookup.Set - AppearanceSets.data()),
                    uint32(lookup.Category - lookup.Set->Categories.data()));
                break;
            }
            case SENDER_RESET:
                if (action < AppearanceSets.size())
                {
                    AppearanceSet const& set = AppearanceSets[action];
                    SetAppearance(player, set, 0);
                    ChatHandler(player->GetSession()).PSendSysMessage("Your {} has returned to its natural shape.",
                        set.Noun);
                    SendCategoryMenu(player, creature, action);
                }
                else
                    CloseGossipMenuFor(player);
                break;
            case SENDER_MAIN_MENU:
            default:
                SendFormMenu(player, creature);
                break;
        }

        return true;
    }

private:
    static void SendFormMenu(Player* player, Creature* creature)
    {
        ClearGossipMenuFor(player);

        for (uint32 i = 0; i < AppearanceSets.size(); ++i)
            AddGossipItemFor(player, GOSSIP_ICON_TABARD, AppearanceSets[i].Name, SENDER_FORM, i);

        SendGossipMenuFor(player, NPC_TEXT_SHAPESHIFT_APPEARANCE, creature);
    }

    static void SendCategoryMenu(Player* player, Creature* creature, uint32 setIndex)
    {
        ClearGossipMenuFor(player);

        AppearanceSet const& set = AppearanceSets[setIndex];
        uint32 const current = player->GetShapeshiftAppearance(set.StorageForm);
        AppearanceCategory const* currentCategory = current ? FindAppearance(current).Category : nullptr;
        for (uint32 i = 0; i < set.Categories.size(); ++i)
        {
            AppearanceCategory const& category = set.Categories[i];
            AddGossipItemFor(player, GOSSIP_ICON_TABARD, MarkCurrent(category.Name, &category == currentCategory),
                SENDER_CATEGORY, setIndex * CATEGORY_STRIDE + i);
        }

        if (current)
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, Acore::StringFormat("Restore my natural {}.", set.Noun),
                SENDER_RESET, setIndex);

        AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Back", SENDER_MAIN_MENU, 0);
        SendGossipMenuFor(player, NPC_TEXT_SHAPESHIFT_APPEARANCE, creature);
    }

    static void SendAppearanceMenu(Player* player, Creature* creature, uint32 setIndex, uint32 categoryIndex)
    {
        ClearGossipMenuFor(player);

        AppearanceSet const& set = AppearanceSets[setIndex];
        uint32 const current = player->GetShapeshiftAppearance(set.StorageForm);
        for (Appearance const& appearance : set.Categories[categoryIndex].Appearances)
        {
            std::string const text = MarkCurrent(appearance.Name, appearance.DisplayId == current);
            AddGossipItemFor(player, GOSSIP_ICON_INTERACT_1, text, SENDER_APPEARANCE, appearance.DisplayId);
        }

        AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Back", SENDER_FORM, setIndex);
        SendGossipMenuFor(player, NPC_TEXT_SHAPESHIFT_APPEARANCE, creature);
    }
};

class ShapeshiftAppearance_PlayerScript : public PlayerScript
{
public:
    ShapeshiftAppearance_PlayerScript() : PlayerScript("ShapeshiftAppearance_PlayerScript",
        { PLAYERHOOK_ON_LOAD_FROM_DB, PLAYERHOOK_ON_DELETE_FROM_DB }) { }

    // Synchronous on purpose: this has to land before LoadFromDB re-applies a saved shapeshift aura.
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

            AppearanceLookup const lookup = FindAppearance(displayId);
            if (!lookup.Set || lookup.Set->StorageForm != form)
            {
                LOG_WARN("entities.player",
                    "character_shapeshift_appearance: {} has unknown form {} / display {}, ignored",
                    player->GetGUID().ToString(), form, displayId);
                continue;
            }

            ApplyAppearance(player, *lookup.Set, displayId);
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
    new npc_shapeshift_appearance();
    new ShapeshiftAppearance_PlayerScript();
}
