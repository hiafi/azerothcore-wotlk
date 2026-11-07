/*
 * mod-dungeon-bosses, Deadmines: the `.dmtest` command shell (DeadminesTestCommand.h).
 */

#include "DeadminesTestCommand.h"
#include "Chat.h"
#include "CommandScript.h"
#include "Creature.h"
#include "DeadminesRework.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include <algorithm>
#include <cstring>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
    struct RegisteredBoss
    {
        char const* name;
        ChatCommandTable const* subcommands;
    };

    std::vector<RegisteredBoss>& Registry()
    {
        static std::vector<RegisteredBoss> bosses;
        return bosses;
    }

    float constexpr kFindRange = 200.f;

    char const* const kBossNames[DeadminesRework::kBossCount] =
    {
        "Rhahk'Zor", "Miner Johnson", "Sneed", "Gilnid", "Mr. Smite", "Cookie", "Captain Greenskin",
        "Edwin VanCleef", "Burn It Down (hard mode)",
    };

    char const* StateName(EncounterState state)
    {
        switch (state)
        {
            case NOT_STARTED:
                return "NOT_STARTED";
            case IN_PROGRESS:
                return "IN_PROGRESS";
            case FAIL:
                return "FAIL";
            case DONE:
                return "DONE";
            case SPECIAL:
                return "SPECIAL";
            default:
                return "TO_BE_DECIDED";
        }
    }

    InstanceScript* DeadminesInstance(ChatHandler* handler)
    {
        if (!DeadminesTest::RequireDeadmines(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }
}

namespace DeadminesTest
{
    void RegisterBoss(char const* boss, ChatCommandTable const& subcommands)
    {
        std::vector<RegisteredBoss>& bosses = Registry();
        bool const taken = std::any_of(bosses.begin(), bosses.end(),
            [boss](RegisteredBoss const& b) { return std::strcmp(b.name, boss) == 0; });
        if (taken || !std::strcmp(boss, "list") || !std::strcmp(boss, "state"))
        {
            LOG_ERROR("module.dungeonbosses", ".dmtest {} registered twice (or a reserved name); ignored", boss);
            return;
        }
        bosses.push_back({ boss, &subcommands });
    }

    bool RequireDeadmines(ChatHandler* handler)
    {
        Player* gm = handler->GetPlayer();
        if (!gm || gm->GetMapId() != DeadminesRework::kMapDeadmines)
        {
            handler->SendErrorMessage(".dmtest works inside the Deadmines (map 36) only.");
            return false;
        }
        return true;
    }

    Creature* FindBoss(ChatHandler* handler, uint32 entry)
    {
        if (!RequireDeadmines(handler))
            return nullptr;
        if (Creature* selected = handler->getSelectedCreature())
            if (selected->GetEntry() == entry)
                return selected;
        Creature* nearest = handler->GetPlayer()->FindNearestCreature(entry, kFindRange, true);
        if (!nearest)
            handler->SendErrorMessage("No live creature {} within {} yd; select it or move closer.", entry, kFindRange);
        return nearest;
    }

    bool ShowBossInfo(ChatHandler* handler, uint32 entry, uint32 bossStateId)
    {
        Creature* boss = FindBoss(handler, entry);
        if (!boss)
            return false;
        InstanceScript* instance = boss->GetInstanceScript();
        EncounterState const state = instance ? instance->GetBossState(bossStateId) : TO_BE_DECIDED;
        handler->PSendSysMessage("{} ({}): {} / {} health, level {}, {}, boss state {} = {}, heroic map: {}",
            boss->GetName(), entry, boss->GetHealth(), boss->GetMaxHealth(), boss->GetLevel(),
            boss->IsInCombat() ? "in combat" : "out of combat", bossStateId, StateName(state),
            boss->GetMap()->IsHeroic() ? "yes" : "no");
        return true;
    }
}

class dungeon_bosses_dmtest_commandscript : public CommandScript
{
public:
    dungeon_bosses_dmtest_commandscript() : CommandScript("dungeon_bosses_dmtest_commandscript") { }

    ChatCommandTable GetCommands() const override
    {
        // Built once, after every boss file registered its table (the command map loads after the scripts).
        static ChatCommandTable dmtestTable;
        if (dmtestTable.empty())
        {
            dmtestTable.emplace_back("list", HandleList, SEC_GAMEMASTER, Console::No);
            dmtestTable.emplace_back("state", HandleState, SEC_GAMEMASTER, Console::No);
            for (RegisteredBoss const& boss : Registry())
                dmtestTable.emplace_back(boss.name, *boss.subcommands);
        }
        static ChatCommandTable commandTable =
        {
            { "dmtest", dmtestTable },
        };
        return commandTable;
    }

    static bool HandleList(ChatHandler* handler)
    {
        if (Registry().empty())
        {
            handler->SendSysMessage("No boss has registered .dmtest subcommands yet.");
            return true;
        }
        for (RegisteredBoss const& boss : Registry())
            handler->PSendSysMessage(".dmtest {} (type it alone for its subcommands)", boss.name);
        return true;
    }

    static bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = DeadminesInstance(handler);
        if (!instance)
            return false;
        for (uint32 id = 0; id < DeadminesRework::kBossCount; ++id)
            handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id], StateName(instance->GetBossState(id)));
        handler->PSendSysMessage("cannon {}, hard mode {}, hard mode kill {}, Johnson roll {} (0 unrolled, 1 present, "
            "2 absent)", instance->GetData(DeadminesRework::DATA_CANNON),
            instance->GetData(DeadminesRework::DATA_HARD_MODE),
            instance->GetData(DeadminesRework::DATA_HARD_MODE_KILLED),
            instance->GetData(DeadminesRework::DATA_JOHNSON_ROLL));
        return true;
    }
};

void AddSC_dungeon_bosses_dmtest_commandscript()
{
    new dungeon_bosses_dmtest_commandscript();
}
