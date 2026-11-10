/*
 * mod-dungeon-bosses, Stratholme: the `.dbtest strat <boss> <mechanic>` GM command shell (handoff section 3.2 item 4),
 * the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 329 under "dbtest strat" (the chat
 * command map splits the name at the space, so the shell nests under the `.dbtest` root it shares with
 * `.dbtest scholo`). The shell owns `.dbtest strat` itself plus `list` and `state` (the 17 boss states and the
 * Stratholme data fields); WP-S0 adds `.dbtest strat instance ...` (StratholmeTestCommand.cpp). Each boss file
 * registers its own table from its AddSC_ function, under the names below (one per WP; the S0 stubs register `info`
 * already):
 *
 *     wave 1: barthilas  baroness  nerubenkan  maleki  ramstein  baron  ultimatum (S15, the Baron's hard mode)
 *     wave 2: unforgiven  forresten  timmy  malor  willey  galford  balnazzar  grandlie (S8, Balnazzar's hard mode)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleCough(ChatHandler* handler)
 *         {
 *             Creature* boss = StratTest::FindBoss(handler, NPC_BARTHILAS);
 *             if (!boss)
 *                 return false;
 *             // fire one cough on the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& BarthilasTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",  HandleInfo,  SEC_GAMEMASTER, Console::No },
 *                 { "cough", HandleCough, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_magistrate_barthilas_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_magistrate_barthilas_rework, StratholmeRework::kInstanceScriptName);
 *         StratTest::RegisterBoss("barthilas", BarthilasTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "StratholmeRework.h"

class ChatHandler;
class Creature;

namespace StratTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(StratholmeRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in Stratholme.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, StratholmeRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 329.
    inline bool RequireStratholme(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, StratholmeRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, StratholmeRework::kTestCommand, entry, bossStateId);
    }
}

#endif
