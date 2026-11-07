/*
 * mod-dungeon-bosses, Deadmines: the `.dmtest <boss> <mechanic>` GM command shell (handoff section 7 #18), now the
 * shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 36 under "dmtest"; these wrappers keep the
 * Pilot's calls. Each boss file registers its own subcommand table from its AddSC_ function; the shell owns `.dmtest`
 * itself plus `.dmtest list` (the registered bosses and their subcommands) and `.dmtest state` (the instance's boss
 * states and the Deadmines data fields).
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleCaveIn(ChatHandler* handler)
 *         {
 *             Creature* boss = DeadminesTest::FindBoss(handler, NPC_RHAHKZOR);
 *             if (!boss)
 *                 return false;
 *             // fire one Cave In at the GM's position ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& RhahkZorTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "cavein", HandleCaveIn, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_rhahk_zor_rework()
 *     {
 *         RegisterDeadminesReworkCreatureAI(boss_rhahk_zor_rework);
 *         DeadminesTest::RegisterBoss("rhahkzor", RhahkZorTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_DEADMINES_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"

class ChatHandler;
class Creature;

namespace DeadminesTest
{
    char constexpr kCommand[] = "dmtest";

    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function: the command map is built after the scripts load.
    // A second registration of the same name is ignored with an error log.
    void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands);

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in Deadmines.
    Creature* FindBoss(ChatHandler* handler, uint32 entry);

    // Sends an error and returns false when the GM is not on map 36.
    bool RequireDeadmines(ChatHandler* handler);

    // Prints `boss`'s entry, health, instance boss state (bossStateId) and combat state: a ready-made `info`
    // subcommand body for a boss table.
    bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId);
}

#endif
