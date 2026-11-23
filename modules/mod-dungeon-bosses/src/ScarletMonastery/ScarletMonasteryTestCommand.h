/*
 * mod-dungeon-bosses, Scarlet Monastery: the `.dbtest sm <boss> <mechanic>` GM command shell (handoff section 3.2
 * item 5), the shared kit's generic shell (Kit/DungeonTestCommand.h) registered for map 189 under "dbtest sm" (the
 * chat command map splits the name at the space, so the shell nests under the `.dbtest` root it shares with
 * `.dbtest scholo`, `.dbtest strat`, `.dbtest brs` and `.dbtest brd`). The shell owns `.dbtest sm` itself plus `list`
 * and `state` (the 18 boss states, then the stock data mirrors, the Cathedral stage, the hard mode flags, the private
 * Horseman field, the portals, the wave); WP-S0 adds `.dbtest sm instance ...`, `.dbtest sm section <1-4>` and
 * `.dbtest sm portal <1-4> [go]` (ScarletMonasteryTestCommand.cpp). Each boss file registers its own table from its
 * AddSC_ function, under the names below (one per WP; the S0 stubs register `info` already, the four end bosses also
 * `hardmode`: the GM arming of their hard mode, handoff section 3.7):
 *
 *     wave 1: vishas  ironspine  council (`champion` inside)  thalnos  desecration (D4H)  loksey  kell  hollis
 *             doan  heresy (D8H)
 *     wave 2: crell  halden  herod  calltoarms (D11H)  thorne  laststand  whitemane  truth (D14H)
 *
 * A boss WP adds its subcommands like this (in its own boss_<name>_rework.cpp):
 *
 *     using namespace Acore::ChatCommands;
 *     namespace
 *     {
 *         bool HandleTorment(ChatHandler* handler)
 *         {
 *             Creature* boss = SmTest::FindBoss(handler, NPC_VISHAS);
 *             if (!boss)
 *                 return false;
 *             // fire one Torment at the GM ...
 *             return true;
 *         }
 *
 *         ChatCommandTable const& VishasTestCommands()
 *         {
 *             static ChatCommandTable const commands =
 *             {
 *                 { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
 *                 { "torment", HandleTorment, SEC_GAMEMASTER, Console::No },
 *             };
 *             return commands;
 *         }
 *     }
 *
 *     void AddSC_boss_interrogator_vishas_rework()
 *     {
 *         RegisterDungeonReworkCreatureAI(boss_interrogator_vishas_rework,
 *             ScarletMonasteryRework::kInstanceScriptName);
 *         SmTest::RegisterBoss("vishas", VishasTestCommands());
 *     }
 *
 * Handlers are plain functions (ChatCommandBuilder takes a function reference), with typed arguments after the
 * ChatHandler* as in any AzerothCore command (Optional<float>, Tail, ...).
 */

#ifndef MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_TEST_COMMAND_H
#define MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_TEST_COMMAND_H

#include "ChatCommand.h"
#include "Define.h"
#include "DungeonTestCommand.h"
#include "ScarletMonasteryRework.h"

class ChatHandler;
class Creature;
class InstanceScript;

namespace SmTest
{
    // `boss` must be a string literal (the command map keeps the pointer); `subcommands` must live for the process
    // (a function-local static). Call from the boss's AddSC_ function.
    inline void RegisterBoss(char const* boss, Acore::ChatCommands::ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(ScarletMonasteryRework::kTestCommand, boss, subcommands);
    }

    // The creature a subcommand acts on: the selected creature when its entry is `entry`, else the nearest one alive
    // within 200 yd of the GM. Sends an error and returns nullptr when there is none or the GM is not in the
    // Monastery.
    inline Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, ScarletMonasteryRework::kTestCommand, entry);
    }

    // Sends an error and returns false when the GM is not on map 189.
    inline bool RequireScarletMonastery(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, ScarletMonasteryRework::kTestCommand);
    }

    // Prints the boss's entry, health, boss state (bossStateId) and combat state: a ready-made `info` body.
    inline bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, ScarletMonasteryRework::kTestCommand, entry, bossStateId);
    }

    // The GM's instance script on map 189 (an error and nullptr elsewhere).
    InstanceScript* GmInstance(ChatHandler* handler);

    // A hard mode WP's ready-made `info` body: the flag (GetData(flagData)), its kill slot and its boss's state.
    bool ShowHardModeInfo(ChatHandler* handler, char const* name, uint32 flagData, uint32 killSlot);

    // An end boss's `hardmode` body: arms the kill slot's flag past the trigger rules (DATA_GM_HARD_MODE), then shows
    // it as ShowHardModeInfo does.
    bool ArmHardMode(ChatHandler* handler, uint32 killSlot);
}

#endif
