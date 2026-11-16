/*
 * mod-dungeon-bosses, Blackrock Spire: the `.dbtest brs <boss> <mechanic>` GM command shell (handoff section 3.2 item
 * 4), the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 229 under "dbtest brs" (the chat
 * command map splits the name at the space, so the shell nests under the `.dbtest` root it shares with
 * `.dbtest scholo` and `.dbtest strat`). The shell owns `.dbtest brs` itself plus `list` and `state` (the 28 boss
 * states, then the held flex count per boss, the room, the insult, the pile, the Solakar event and flame, the hard
 * mode flags); WP-S0 adds `.dbtest brs instance ...` (BlackrockSpireTestCommand.cpp). Each boss file registers its own
 * table from its AddSC_ function, under the names below (one per WP; the S0 stubs register `info` already):
 *
 *     wave 1: omokk  voshgajin  voone  smolderweb  urok  zigris  halycon (`gizrul info` inside)  wyrmthalak
 *             warhorn (B9, Wyrmthalak's hard mode)
 *     wave 2: emberseer  solakar  rend  gyth  beast  drakkisath  army (B15, Drakkisath's hard mode)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleHaymaker(ChatHandler* handler)
 *         {
 *             Creature* boss = BrsTest::FindBoss(handler, NPC_OMOKK);
 *             if (!boss)
 *                 return false;
 *             // fire one Haymaker at the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& OmokkTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
 *                 { "haymaker", HandleHaymaker, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_highlord_omokk_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_highlord_omokk_rework, BlackrockSpireRework::kInstanceScriptName);
 *         BrsTest::RegisterBoss("omokk", OmokkTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_TEST_COMMAND_H

#include "BlackrockSpireRework.h"
#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"

class ChatHandler;
class Creature;

namespace BrsTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(BlackrockSpireRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in the Spire.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, BlackrockSpireRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 229.
    inline bool RequireBlackrockSpire(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, BlackrockSpireRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, BlackrockSpireRework::kTestCommand, entry, bossStateId);
    }
}

#endif
