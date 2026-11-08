/*
 * mod-dungeon-bosses, Shadowfang Keep: the `.sfktest <boss> <mechanic>` GM command shell (handoff section 7 #27), the
 * shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 33 under "sfktest". The shell owns
 * `.sfktest` itself plus `.sfktest list` and `.sfktest state` (the 11 boss states and the SFK data fields); WP-K adds
 * `.sfktest instance ...` and `.sfktest cells ...` (ShadowfangKeepTestCommand.cpp). Each boss file registers its own
 * table from its AddSC_ function, under the boss names below (one per boss WP; the stubs register `info` already):
 *
 *     rethilgore  razorclaw  silverlaine  springvale  odo  captain  fenrus  nandos  arugal  hardmode
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleHunt(ChatHandler* handler)
 *         {
 *             Creature* boss = SfkTest::FindBoss(handler, NPC_ODO);
 *             if (!boss)
 *                 return false;
 *             // fire one Hunt on the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& OdoTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
 *                 { "hunt", HandleHunt, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_odo_the_blindwatcher_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_odo_the_blindwatcher_rework, ShadowfangKeepRework::kInstanceScriptName);
 *         SfkTest::RegisterBoss("odo", OdoTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_SHADOWFANG_KEEP_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_SHADOWFANG_KEEP_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "ShadowfangKeepRework.h"

class ChatHandler;
class Creature;

namespace SfkTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(ShadowfangKeepRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in SFK.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, ShadowfangKeepRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 33.
    inline bool RequireShadowfangKeep(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, ShadowfangKeepRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, ShadowfangKeepRework::kTestCommand, entry, bossStateId);
    }
}

#endif
