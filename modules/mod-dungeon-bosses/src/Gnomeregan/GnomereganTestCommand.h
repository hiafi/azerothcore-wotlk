/*
 * mod-dungeon-bosses, Gnomeregan: the `.dbtest gnomer <key> <subcommand>` GM command shell (handoff section 3.2 item
 * 10), the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 90 under "dbtest gnomer" (nested
 * under the `.dbtest` root it shares with the other dungeons). The shell owns `.dbtest gnomer` itself plus `list` and
 * `state` (the 7 boss states, then the door, the hard mode, the chest, the End NPCs and the section); WP-S0 adds
 * `section`, `door`, `hardmode`, `chest`, `endnpc`, `go`, `where` and `boss` (GnomereganTestCommand.cpp). Each WP
 * registers its own table from its AddSC_ function under its key (the S0 stubs register `info` already):
 *
 *     techbot (D1)  fallout (D2)  electro (D3)  alert (D4)  pummeler (D5)  thermaplugg (D6)  workshop (D6Ha)
 *     schematics (D6Hb)
 *
 * A WP adds its subcommands like this (in its own .cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleLagSpike(ChatHandler* handler)
 *         {
 *             Creature* boss = GnomerTest::FindBoss(handler, NPC_TECHBOT);
 *             if (!boss)
 *                 return false;
 *             // fire Lag Spike on the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& TechbotTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
 *                 { "lagspike", HandleLagSpike, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_techbot_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_techbot_rework, GnomereganRework::kInstanceScriptName);
 *         GnomerTest::RegisterBoss("techbot", TechbotTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<uint32>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "GnomereganRework.h"

class ChatHandler;
class Creature;
class InstanceScript;

namespace GnomerTest
{
    // `key` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process (a
    // function-local static). Call from the WP's AddSC_ function.
    inline void RegisterBoss(char const* key, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(GnomereganRework::kTestCommand, key, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in Gnomeregan.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, GnomereganRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 90.
    inline bool RequireGnomeregan(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, GnomereganRework::kTestCommand);
    }

    // Prints the unit's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, GnomereganRework::kTestCommand, entry, bossStateId);
    }

    // The GM's instance script; sends an error and returns nullptr when there is none or the GM is not in Gnomeregan.
    InstanceScript* GmInstance(ChatHandler* handler);

    // The instance's lines of `.dbtest gnomer state` after the boss states.
    void PrintRunState(ChatHandler* handler, InstanceScript const* instance);
}

#endif
