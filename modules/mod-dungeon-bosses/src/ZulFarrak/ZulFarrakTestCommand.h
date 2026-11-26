/*
 * mod-dungeon-bosses, Zul'Farrak: the `.dbtest zf <key> <subcommand>` GM command shell (handoff section 3.2 item 10),
 * the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 209 under "dbtest zf" (nested under the
 * `.dbtest` root it shares with the other dungeons). The shell owns `.dbtest zf` itself plus `list` and `state` (the 9
 * boss states, then the Pyramid, the crew, the door and the hard mode); WP-S0 adds `stage`, `crew`, `door`, `test`,
 * `section` and `instance` (ZulFarrakTestCommand.cpp). Each WP registers its own table from its AddSC_ function under
 * its key (the S0 stubs register `info` already):
 *
 *     theka (D1)  antusul (D2)  zumrah (D3)  block (D4a)  stair (D4b)  band (CR)  blyfight (D5)  ukorz (D6)
 *     pool (D7)  poolcrew (D7Ha)  deluge (D7Hb)
 *
 * A WP adds its subcommands like this (in its own .cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandlePlague(ChatHandler* handler)
 *         {
 *             Creature* boss = ZfTest::FindBoss(handler, NPC_THEKA);
 *             if (!boss)
 *                 return false;
 *             // cast Fevered Plague on the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& ThekaTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
 *                 { "plague", HandlePlague, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_theka_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_theka_rework, ZulFarrakRework::kInstanceScriptName);
 *         ZfTest::RegisterBoss("theka", ThekaTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<uint32>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_ZUL_FARRAK_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_ZUL_FARRAK_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "ZulFarrakRework.h"

class ChatHandler;
class Creature;
class InstanceScript;

namespace ZfTest
{
    // `key` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process (a
    // function-local static). Call from the WP's AddSC_ function.
    inline void RegisterBoss(char const* key, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(ZulFarrakRework::kTestCommand, key, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in Zul'Farrak.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, ZulFarrakRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 209.
    inline bool RequireZulFarrak(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, ZulFarrakRework::kTestCommand);
    }

    // Prints the unit's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, ZulFarrakRework::kTestCommand, entry, bossStateId);
    }

    // The GM's instance script; sends an error and returns nullptr when there is none or the GM is not in Zul'Farrak.
    InstanceScript* GmInstance(ChatHandler* handler);

    // The Pyramid's and the crew's lines of `.dbtest zf state` (also `.dbtest zf crew`).
    void PrintRunState(ChatHandler* handler, InstanceScript const* instance);
}

#endif
