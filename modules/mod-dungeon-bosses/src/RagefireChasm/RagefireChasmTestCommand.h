/*
 * mod-dungeon-bosses, Ragefire Chasm: the `.dbtest rfc <boss> <mechanic>` GM command shell (handoff section 3.2 item
 * 6), the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 389 under "dbtest rfc" (nested under
 * the `.dbtest` root it shares with the other dungeons). The shell owns `.dbtest rfc` itself plus `list` and `state`
 * (the 5 boss states, the gate, Taragaman's dormant state, the hard mode flag and kill); WP-S0 adds
 * `.dbtest rfc gate <open|close>`, `.dbtest rfc section <name>` and `.dbtest rfc instance ...`
 * (RagefireChasmTestCommand.cpp). Each boss file registers its own table from its AddSC_ function, under the names
 * below (one per WP; the S0 stubs register `info` already, Taragaman's also `hardmode`):
 *
 *     oggleflint (D1)  jergosh (D2)  bazzalan (D3)  taragaman (D4)  starving (D4H)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleHunt(ChatHandler* handler)
 *         {
 *             Creature* boss = RfcTest::FindBoss(handler, NPC_OGGLEFLINT);
 *             if (!boss)
 *                 return false;
 *             // send one Borer after the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& OggleflintTestCommands()
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
 *     void AddSC_boss_oggleflint_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_oggleflint_rework, RagefireChasmRework::kInstanceScriptName);
 *         RfcTest::RegisterBoss("oggleflint", OggleflintTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "RagefireChasmRework.h"

class ChatHandler;
class Creature;
class InstanceScript;

namespace RfcTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(RagefireChasmRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in the Chasm.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, RagefireChasmRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 389.
    inline bool RequireRagefireChasm(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, RagefireChasmRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, RagefireChasmRework::kTestCommand, entry, bossStateId);
    }

    // The GM's instance script; sends an error and returns nullptr when there is none or the GM is not in the Chasm.
    InstanceScript* GmInstance(ChatHandler* handler);

    // The hard mode's flag, kill slot, gate and Taragaman's state (`starving info`, `state`).
    bool ShowHardModeInfo(ChatHandler* handler);

    // `.dbtest rfc taragaman hardmode [0|1]` (handoff section 3.7): DATA_HARD_MODE past the shrine and the pour,
    // through the instance's own rules (heroic only, not once he is engaged or dead).
    bool ArmHardMode(ChatHandler* handler, bool lit);
}

#endif
