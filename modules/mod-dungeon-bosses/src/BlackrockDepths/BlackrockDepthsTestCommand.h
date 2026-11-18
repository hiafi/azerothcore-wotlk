/*
 * mod-dungeon-bosses, Blackrock Depths: the `.dbtest brd <boss> <mechanic>` GM command shell (handoff section 3.2
 * item 5), the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 230 under "dbtest brd" (the
 * chat command map splits the name at the space, so the shell nests under the `.dbtest` root it shares with
 * `.dbtest scholo`, `.dbtest strat` and `.dbtest brs`). The shell owns `.dbtest brd` itself plus `list` and `state`
 * (the 24 boss states, then the stock TYPE mirrors, the Ring's rolls and Favor, the banner, rope, Cinder, console and
 * Avatar flags, the Vault's clock, the bar fields, the wave); WP-S0 adds `.dbtest brd instance ...` and
 * `.dbtest brd section <1-4>` (BlackrockDepthsTestCommand.cpp). Each boss file registers its own table from its AddSC_
 * function, under the names below (one per WP; the S0 stubs register `info` already):
 *
 *     wave 1: gerstahn  roccor  grebmar  ring (D4)  champions (D5)  encore (D6, the Ring's hard mode)  loregrain
 *             stilgiss (`verek info` inside)  vault  fineous  incendius  lake (D12, Incendius's hard mode)  baelgar
 *     wave 2: angerforge  argelmach  prototype (D16)  guzzler (D17)  hurley  phalanx  flamelash  seven  magmus
 *             emperor  avatar (D24)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleMindFlay(ChatHandler* handler)
 *         {
 *             Creature* boss = BrdTest::FindBoss(handler, NPC_GERSTAHN);
 *             if (!boss)
 *                 return false;
 *             // fire one Mind Flay at the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& GerstahnTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
 *                 { "mindflay", HandleMindFlay, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_high_interrogator_gerstahn_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_high_interrogator_gerstahn_rework,
 *             BlackrockDepthsRework::kInstanceScriptName);
 *         BrdTest::RegisterBoss("gerstahn", GerstahnTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_TEST_COMMAND_H

#include "BlackrockDepthsRework.h"
#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"

class ChatHandler;
class Creature;
class InstanceScript;

namespace BrdTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(BlackrockDepthsRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in the Depths.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, BlackrockDepthsRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 230.
    inline bool RequireBlackrockDepths(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, BlackrockDepthsRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, BlackrockDepthsRework::kTestCommand, entry, bossStateId);
    }

    // The GM's instance script on map 230 (an error and nullptr elsewhere).
    InstanceScript* GmInstance(ChatHandler* handler);

    // A hard mode WP's ready-made `info` body: the flag (GetData(flagData)), its kill slot and its boss's state.
    bool ShowHardModeInfo(ChatHandler* handler, char const* name, uint32 flagData, uint32 killSlot);
}

#endif
