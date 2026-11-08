/*
 * mod-dungeon-bosses, Scholomance: the `.dbtest scholo <boss> <mechanic>` GM command shell (handoff section 7 #25),
 * the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 289 under "dbtest scholo" (the chat
 * command map splits the name at the space, so the shell nests under a `.dbtest` root other dungeons can share). The
 * shell owns `.dbtest scholo` itself plus `list` and `state` (the 11 boss states and the Scholomance data fields);
 * WP-KS adds `.dbtest scholo instance ...` (ScholomanceTestCommand.cpp). Each boss file registers its own table from
 * its AddSC_ function, under the names below (one per WP; the KS stubs register `info` already):
 *
 *     jandice  rattlegore  marduk  ras  malicia  krastinov  polkelt  ravenian  alexei  illucia  gandling
 *     keepsake (S12, Ras's hard mode)  exam (S13, Gandling's hard mode)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleSigils(ChatHandler* handler)
 *         {
 *             Creature* boss = ScholoTest::FindBoss(handler, NPC_JANDICE);
 *             if (!boss)
 *                 return false;
 *             // fire one Blood Sigil round on the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& JandiceTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
 *                 { "sigils", HandleSigils, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_jandice_barov_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_jandice_barov_rework, ScholomanceRework::kInstanceScriptName);
 *         ScholoTest::RegisterBoss("jandice", JandiceTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "ScholomanceRework.h"

class ChatHandler;
class Creature;

namespace ScholoTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(ScholomanceRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in Scholomance.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, ScholomanceRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 289.
    inline bool RequireScholomance(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, ScholomanceRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, ScholomanceRework::kTestCommand, entry, bossStateId);
    }
}

#endif
