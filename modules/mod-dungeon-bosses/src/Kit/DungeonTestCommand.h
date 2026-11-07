/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): the `.<x>test <boss> <mechanic>` GM command shell, generalized
 * from the Deadmines Pilot's `.dmtest`. Each reworked dungeon registers one shell (its command name, map, boss state
 * names and an optional extra state printer) from its instance or test-command AddSC_ function; each boss file
 * registers its own subcommand table under that command. A shell owns `.<x>test` itself plus `.<x>test list` (the
 * registered bosses) and `.<x>test state` (the instance's boss states, then the dungeon's extra lines).
 *
 *     // once per dungeon (e.g. ShadowfangKeepTestCommand.cpp):
 *     DungeonTest::DungeonShell shell;
 *     shell.command = "sfktest";
 *     shell.mapId = 33;
 *     shell.dungeonName = "Shadowfang Keep";
 *     shell.bossNames = { "Rethilgore", "Razorclaw", ... };
 *     shell.printState = [](ChatHandler* handler, InstanceScript const* instance) { ... };     // optional
 *     DungeonTest::RegisterDungeon(shell);
 *
 *     // per boss file, from its AddSC_ function:
 *     DungeonTest::RegisterBoss("sfktest", "odo", OdoTestCommands());
 *     // in a handler:
 *     Creature* boss = DungeonTest::FindBoss(handler, "sfktest", NPC_ODO);
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...). Registration order does not matter: the
 * command tables are built when the command map loads, after every script's AddSC_.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include <functional>
#include <string>
#include <vector>

class ChatHandler;
class Creature;
class InstanceScript;

namespace DungeonTest
{
    struct DungeonShell
    {
        std::string command;                        // "dmtest" (typed as ".dmtest")
        uint32 mapId = 0;
        std::string dungeonName;                    // "the Deadmines": "... works inside <name> (map <id>) only."
        std::vector<std::string> bossNames;         // by boss state id, for `.<x>test state`
        // Extra `.<x>test state` lines after the boss states (instance data fields).
        std::function<void(ChatHandler*, InstanceScript const*)> printState;
    };

    // Registers a dungeon's shell (creates its command script). A second shell with the same command is ignored with
    // an error log.
    void RegisterDungeon(DungeonShell shell);

    // `command` and `boss` must be string literals (the command map keeps the pointer); `subcommands` must live for the
    // process (a function-local static). Call from the boss's AddSC_ function. A second registration of the same boss
    // name under one command (or a reserved name: list, state) is ignored with an error log.
    void RegisterBoss(char const* command, char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands);

    // Sends an error and returns false when the GM is not on `command`'s map.
    bool RequireMap(ChatHandler* handler, char const* command);

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not on the map.
    Creature* FindBoss(ChatHandler* handler, char const* command, uint32 entry);

    // Prints `boss`'s entry, health, instance boss state (bossStateId) and combat state: a ready-made `info`
    // subcommand body for a boss table.
    bool ShowBossInfo(ChatHandler* handler, char const* command, uint32 entry, uint32 bossStateId);

    // NOT_STARTED, IN_PROGRESS, ... for a state value.
    char const* StateName(uint32 state);
}

#endif
