/*
 * mod-dungeon-bosses, the shared dungeon kit: the `.<x>test` command shell (DungeonTestCommand.h), the Deadmines
 * Pilot's `.dmtest` shell with the map, the command name and the boss names as parameters.
 */

#include "DungeonTestCommand.h"
#include "Chat.h"
#include "CommandScript.h"
#include "Creature.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "Player.h"
#include <algorithm>
#include <array>
#include <cstring>
#include <deque>
#include <utility>

using namespace Acore::ChatCommands;

namespace
{
    float constexpr kFindRange = 200.f;

    struct RegisteredBoss
    {
        std::string command;
        char const* name;
        ChatCommandTable const* subcommands;
    };

    std::vector<RegisteredBoss>& Bosses()
    {
        static std::vector<RegisteredBoss> bosses;
        return bosses;
    }

    // Stable addresses: each shell's command script keeps a pointer to its entry.
    std::deque<DungeonTest::DungeonShell>& Shells()
    {
        static std::deque<DungeonTest::DungeonShell> shells;
        return shells;
    }

    DungeonTest::DungeonShell const* FindShell(char const* command)
    {
        for (DungeonTest::DungeonShell const& shell : Shells())
            if (shell.command == command)
                return &shell;
        return nullptr;
    }

    InstanceScript* ShellInstance(ChatHandler* handler, char const* command)
    {
        if (!DungeonTest::RequireMap(handler, command))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    class dungeon_bosses_test_commandscript : public CommandScript
    {
    public:
        explicit dungeon_bosses_test_commandscript(DungeonTest::DungeonShell const* shell)
            : CommandScript(("dungeon_bosses_" + shell->command + "_commandscript").c_str()), _shell(shell) { }

        ChatCommandTable GetCommands() const override
        {
            // Built once, after every boss file registered its table (the command map loads after the scripts).
            if (_table.empty())
            {
                _table.emplace_back("list", *_list, SEC_GAMEMASTER, Console::No);
                _table.emplace_back("state", *_state, SEC_GAMEMASTER, Console::No);
                for (RegisteredBoss const& boss : Bosses())
                    if (boss.command == _shell->command)
                        _table.emplace_back(boss.name, *boss.subcommands);
            }
            if (_root.empty())
                _root.emplace_back(_shell->command.c_str(), _table);
            return _root;
        }

    private:
        // The chat command builders take plain functions (no captures), so each shell gets its own `list` and `state`
        // handlers from a fixed table of per-index thunks (Shells() is a deque: an index and a pointer stay valid).
        static bool List(ChatHandler* handler, DungeonTest::DungeonShell const* shell)
        {
            bool any = false;
            for (RegisteredBoss const& boss : Bosses())
                if (boss.command == shell->command)
                {
                    handler->PSendSysMessage(".{} {} (type it alone for its subcommands)", shell->command, boss.name);
                    any = true;
                }
            if (!any)
                handler->PSendSysMessage("No boss has registered .{} subcommands yet.", shell->command);
            return true;
        }

        static bool State(ChatHandler* handler, DungeonTest::DungeonShell const* shell)
        {
            InstanceScript* instance = ShellInstance(handler, shell->command.c_str());
            if (!instance)
                return false;
            for (uint32 id = 0; id < shell->bossNames.size(); ++id)
                handler->PSendSysMessage("boss {} {}: {}", id, shell->bossNames[id],
                    DungeonTest::StateName(instance->GetBossState(id)));
            if (shell->printState)
                shell->printState(handler, instance);
            return true;
        }

        template <std::size_t I>
        static bool ListThunk(ChatHandler* handler)
        {
            return I < Shells().size() && List(handler, &Shells()[I]);
        }

        template <std::size_t I>
        static bool StateThunk(ChatHandler* handler)
        {
            return I < Shells().size() && State(handler, &Shells()[I]);
        }

    public:
        static std::size_t constexpr kMaxShells = 8;

        template <std::size_t... I>
        static auto ListThunks(std::index_sequence<I...>)
        {
            return std::array<bool (*)(ChatHandler*), sizeof...(I)>{ &ListThunk<I>... };
        }

        template <std::size_t... I>
        static auto StateThunks(std::index_sequence<I...>)
        {
            return std::array<bool (*)(ChatHandler*), sizeof...(I)>{ &StateThunk<I>... };
        }

        void Bind(std::size_t index)
        {
            static auto const lists = ListThunks(std::make_index_sequence<kMaxShells>{});
            static auto const states = StateThunks(std::make_index_sequence<kMaxShells>{});
            _list = lists[index];
            _state = states[index];
        }

    private:
        DungeonTest::DungeonShell const* _shell;
        bool (*_list)(ChatHandler*) = nullptr;
        bool (*_state)(ChatHandler*) = nullptr;
        mutable ChatCommandTable _table;
        mutable ChatCommandTable _root;
    };
}

namespace DungeonTest
{
    void RegisterDungeon(DungeonShell shell)
    {
        if (shell.command.empty() || FindShell(shell.command.c_str()))
        {
            LOG_ERROR("module.dungeonbosses", "test command shell .{} registered twice (or unnamed); ignored",
                shell.command);
            return;
        }
        if (Shells().size() >= dungeon_bosses_test_commandscript::kMaxShells)
        {
            LOG_ERROR("module.dungeonbosses", "test command shell .{}: more than {} shells; ignored", shell.command,
                dungeon_bosses_test_commandscript::kMaxShells);
            return;
        }
        Shells().push_back(std::move(shell));
        auto* script = new dungeon_bosses_test_commandscript(&Shells().back());
        script->Bind(Shells().size() - 1);
    }

    void RegisterBoss(char const* command, char const* boss, ChatCommandTable const& subcommands)
    {
        std::vector<RegisteredBoss>& bosses = Bosses();
        bool const taken = std::any_of(bosses.begin(), bosses.end(), [command, boss](RegisteredBoss const& b)
        {
            return b.command == command && std::strcmp(b.name, boss) == 0;
        });
        if (taken || !std::strcmp(boss, "list") || !std::strcmp(boss, "state"))
        {
            LOG_ERROR("module.dungeonbosses", ".{} {} registered twice (or a reserved name); ignored", command, boss);
            return;
        }
        bosses.push_back({ command, boss, &subcommands });
    }

    bool RequireMap(ChatHandler* handler, char const* command)
    {
        DungeonShell const* shell = FindShell(command);
        Player* gm = handler->GetPlayer();
        if (!shell || !gm || gm->GetMapId() != shell->mapId)
        {
            if (shell)
                handler->SendErrorMessage(".{} works inside {} (map {}) only.", shell->command, shell->dungeonName,
                    shell->mapId);
            else
                handler->SendErrorMessage(".{} has no registered dungeon.", command);
            return false;
        }
        return true;
    }

    Creature* FindBoss(ChatHandler* handler, char const* command, uint32 entry)
    {
        if (!RequireMap(handler, command))
            return nullptr;
        if (Creature* selected = handler->getSelectedCreature())
            if (selected->GetEntry() == entry)
                return selected;
        Creature* nearest = handler->GetPlayer()->FindNearestCreature(entry, kFindRange, true);
        if (!nearest)
            handler->SendErrorMessage("No live creature {} within {} yd; select it or move closer.", entry, kFindRange);
        return nearest;
    }

    bool ShowBossInfo(ChatHandler* handler, char const* command, uint32 entry, uint32 bossStateId)
    {
        Creature* boss = FindBoss(handler, command, entry);
        if (!boss)
            return false;
        InstanceScript* instance = boss->GetInstanceScript();
        uint32 const state = instance ? uint32(instance->GetBossState(bossStateId)) : uint32(TO_BE_DECIDED);
        handler->PSendSysMessage("{} ({}): {} / {} health, level {}, {}, boss state {} = {}, heroic map: {}",
            boss->GetName(), entry, boss->GetHealth(), boss->GetMaxHealth(), boss->GetLevel(),
            boss->IsInCombat() ? "in combat" : "out of combat", bossStateId, StateName(state),
            boss->GetMap()->IsHeroic() ? "yes" : "no");
        return true;
    }

    char const* StateName(uint32 state)
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
}
