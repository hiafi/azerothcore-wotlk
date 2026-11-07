/*
 * mod-dungeon-bosses, Deadmines: the `.dmtest` command shell (DeadminesTestCommand.h), registered on the shared kit's
 * generic shell (Kit/DungeonTestCommand.h). The messages, the boss names and the `state` lines are the Pilot's.
 */

#include "DeadminesTestCommand.h"
#include "Chat.h"
#include "DeadminesRework.h"
#include "InstanceScript.h"

using namespace Acore::ChatCommands;

namespace DeadminesTest
{
    void RegisterBoss(char const* boss, ChatCommandTable const& subcommands)
    {
        DungeonTest::RegisterBoss(kCommand, boss, subcommands);
    }

    bool RequireDeadmines(ChatHandler* handler)
    {
        return DungeonTest::RequireMap(handler, kCommand);
    }

    Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        return DungeonTest::FindBoss(handler, kCommand, entry);
    }

    bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        return DungeonTest::ShowBossInfo(handler, kCommand, entry, bossStateId);
    }
}

// Called from the loader after the boss files (they register their tables from their AddSC_ functions; the order no
// longer matters, the tables are built when the command map loads).
void AddSC_dungeon_bosses_dmtest_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = DeadminesTest::kCommand;
    shell.mapId = DeadminesRework::kMapDeadmines;
    shell.dungeonName = "the Deadmines";
    shell.bossNames = { "Rhahk'Zor", "Miner Johnson", "Sneed", "Gilnid", "Mr. Smite", "Cookie", "Captain Greenskin",
        "Edwin VanCleef", "Burn It Down (hard mode)" };
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("cannon {}, hard mode {}, hard mode kill {}, Johnson roll {} (0 unrolled, 1 present, "
            "2 absent)", instance->GetData(DeadminesRework::DATA_CANNON),
            instance->GetData(DeadminesRework::DATA_HARD_MODE),
            instance->GetData(DeadminesRework::DATA_HARD_MODE_KILLED),
            instance->GetData(DeadminesRework::DATA_JOHNSON_ROLL));
    };
    DungeonTest::RegisterDungeon(std::move(shell));
}
