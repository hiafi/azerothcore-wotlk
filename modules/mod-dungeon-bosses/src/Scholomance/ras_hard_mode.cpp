/*
 * mod-dungeon-bosses, Scholomance S12:
 * Ras Frostwhisper's hard mode, "the Torn Keepsake" (heroic only).
 * STUB written by WP-KS (the Scholomance kit); WP-S12 owns this file from now on.
 *
 * What WP-KS built for it (the instance, instance_scholomance_rework.cpp; ScholomanceRework.h):
 * - DATA_KEEPSAKE_PAGE: SetData(20, page 0..2) collects a page (heroic, once each, before Ras dies); GetData = the
 *   mask, DATA_KEEPSAKE_PAGE_COUNT the count; saved.
 * - DATA_KEEPSAKE_BOUND: SetData(22, 1) binds the book with all three pages; saved.
 * - DATA_RAS_HARD_MODE: SetData(23, 1) starts the hard mode (bound book, heroic, Ras not fighting and not dead); 0
 *   clears it before his death; saved. The loot bit (LOOT_MODE_HARD_MODE_1) rides Ras while it is lit.
 * - DATA_RAS_HARD_MODE_KILLED: set when Ras dies with the flag; saved.
 * - The user's spots (handoff section 10): kKeepsakePages (3 pages), kKeepsakeBook, kHardModeTable (a clickable
 *   alchemy table starts the hard mode, in place of the Embalming Fluid's click); entries GO_SC_TORN_PAGE 301150,
 *   GO_SC_KEEPSAKE_BOOK 301151 / GO_SC_KEEPSAKE_BOOK_BOUND 301152, GO_SC_ALCHEMY_TABLE 301154.
 * - `.dbtest scholo instance page|bind|hardmode ras` drive the same data by hand.
 *
 * TODO(WP-S12):
 * - SC 1087-1121, 1207-1209; handoff section 3.5 row S12 (lich 400k, human 400k by script; Ice Tomb 300535, 12k).
 * - Data (your SQL rev and source/npcs/scholomance/ras_hard_mode.py): the GO templates 301150-301152 and 301154 and
 *   their spawns (heroic spawnMask 2) at the spots above, the Ice Tomb 300535.
 * - GO scripts (here): go_sc_torn_page (SetData(DATA_KEEPSAKE_PAGE, its index by spawn position) then despawn),
 *   go_sc_keepsake_book (shows the count; SetData(DATA_KEEPSAKE_BOUND, 1) at 3; swaps to the bound look),
 *   go_sc_alchemy_table (SetData(DATA_RAS_HARD_MODE, 1) when bound; the start yell / emote).
 * - The fight on S4's Ras AI: the permanent tomb, the transition (display 3975, check `.morph 3975` first), Siphon
 *   Warmth, Mortal Decay; spells in kSpellsRasHardMode. A wipe keeps the flag lit (the group tries again).
 * - Bots never click the pages, the book or the table (no DungeonEvent; handoff section 3.12).
 */

#include "Chat.h"
#include "InstanceScript.h"
#include "Player.h"
#include "RasHardModeLogic.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            return false;
        handler->PSendSysMessage("The Torn Keepsake: pages {}/{} (mask {}), bound {}, hard mode {}, killed {}",
            instance->GetData(DATA_KEEPSAKE_PAGE_COUNT), kKeepsakePageCount, instance->GetData(DATA_KEEPSAKE_PAGE),
            instance->GetData(DATA_KEEPSAKE_BOUND), instance->GetData(DATA_RAS_HARD_MODE),
            instance->GetData(DATA_RAS_HARD_MODE_KILLED));
        return true;
    }

    ChatCommandTable const& KeepsakeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_scholo_ras_hard_mode()
{
    ScholoTest::RegisterBoss("keepsake", KeepsakeTestCommands());
}
