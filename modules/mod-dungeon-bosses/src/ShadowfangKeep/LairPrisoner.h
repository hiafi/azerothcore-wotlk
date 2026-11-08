/*
 * mod-dungeon-bosses, Shadowfang Keep: the lair prisoner's hooks (WP-S9 owns them; WP-S10, Face Him Alone, uses them).
 *
 * The lair prisoner (300513 Sorcerer Ashcrombe / 300514 Deathstalker Adamant, npc_sfk_lair_prisoner in
 * boss_archmage_arugal_rework.cpp) waits by the lair door once Nandos is dead (the instance's summon). Its gossip is a
 * C++ menu on its own gossip_menu (300513 / 300514, WP-S9's SQL rev: the body text of SK's "Gossip" line, no option).
 * Arugal walks it in on his pull and it places the wards; nothing else about it is S10's.
 *
 * S10 adds the heroic "Stay behind" option through these hooks, set once from its AddSC_ function:
 *
 *     SfkLairPrisoner::SetGossipHooks({
 *         [](Player* player, Creature* prisoner)                  // every hello, after the menu is prepared
 *         {
 *             if (prisoner->GetMap()->IsHeroic())
 *                 AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Stay behind. We will face Arugal alone.",
 *                     GOSSIP_SENDER_MAIN, GOSSIP_ACTION_INFO_DEF + 1);
 *         },
 *         [](Player* player, Creature* prisoner, uint32 sender, uint32 action)   // true: handled
 *         {
 *             ... instance->SetData(DATA_HARD_MODE, 1); SfkLairPrisoner::LeaveForHardMode(prisoner);
 *             CloseGossipMenuFor(player);
 *             return true;
 *         } });
 *
 * The menu's DB options (gossip_menu_option rows on the prisoner's menu, with their conditions) still show: the
 * prisoner's hello prepares the menu from the DB first, then calls `onHello`; a selection `onSelect` does not handle
 * goes to the core's DB handling.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_LAIR_PRISONER_H
#define MOD_DUNGEON_BOSSES_SFK_LAIR_PRISONER_H

#include "Define.h"
#include <functional>

class Creature;
class Player;

namespace SfkLairPrisoner
{
    // The prisoners' gossip menus and their body texts (npc_text), WP-S9's SQL rev.
    uint32 constexpr kGossipMenuAshcrombe = 300513;
    uint32 constexpr kGossipMenuAdamant = 300514;

    struct GossipHooks
    {
        // Adds options to the prepared menu (AddGossipItemFor) before it is sent; called on every hello.
        std::function<void(Player* player, Creature* prisoner)> onHello;
        // A selected option; true when handled (the hook closes the menu or sends another one).
        std::function<bool(Player* player, Creature* prisoner, uint32 sender, uint32 action)> onSelect;
    };

    // Replaces the hooks (S10 calls it once, at load).
    void SetGossipHooks(GossipHooks hooks);

    // Face Him Alone chosen: the prisoner says its hard mode line (creature_text group 7) and leaves for good:
    // Ashcrombe with his stock teleport (6422), Adamant out through the lair door. It never walks in on the pull. The
    // caller sets DATA_HARD_MODE first. False when `prisoner` is not a lair prisoner running this script.
    bool LeaveForHardMode(Creature* prisoner);

    // `creature` is a lair prisoner (300513 / 300514).
    bool IsLairPrisoner(Creature const* creature);
}

#endif
