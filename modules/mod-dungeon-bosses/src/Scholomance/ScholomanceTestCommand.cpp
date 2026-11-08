/*
 * mod-dungeon-bosses, Scholomance: the `.dbtest scholo` command shell (ScholomanceTestCommand.h) and WP-KS's own
 * subcommands:
 *
 *   .dbtest scholo instance boss <id> <state>       set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...):
 *                                                   gates, Gandling's reveal (six instructors DONE), the kill flags
 *   .dbtest scholo instance where                   which Scholomance arenas hold the GM's position (the playtest's
 *                                                   .gps checks)
 *   .dbtest scholo instance page <1|2|3>            Ras's keepsake: a page found (heroic, as S12's page GO sets it)
 *   .dbtest scholo instance bind                    bind the keepsake (all three pages, heroic)
 *   .dbtest scholo instance hardmode <ras|gandling> <0|1>
 *                                                   the hard mode flags, as the alchemy table / the honors paper
 *                                                   set them
 *   .dbtest scholo instance grade <instructor>      award that Passing Grade to the selected player (or the GM;
 *                                                   heroic):
 *                                                   malicia krastinov polkelt ravenian alexei illucia, or all
 *   .dbtest scholo instance grades [clear]          list the Passing Grades (or clear them all)
 *   .dbtest scholo instance gate <room> <0|1>       close or open a classroom gate by hand (room 0-5 in the stock
 *                                                   order: Shadow Vault, Barov Vault, Ravenian, Hall of Secrets, Hall
 *                                                   of the Damned, Coven)
 *   .dbtest scholo instance kirtonos                start Kirtonos as the brazier does (SetData(0, IN_PROGRESS))
 */

#include "ScholomanceTestCommand.h"
#include "Chat.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Player.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <cctype>
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;

namespace
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    std::string Lower(std::string s)
    {
        std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return char(std::tolower(c)); });
        return s;
    }

    std::optional<Instructor> ParseInstructor(std::string const& name)
    {
        std::string const n = Lower(name);
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            if (n == Lower(kInstructorNames[i]))
                return Instructor(i);
        return std::nullopt;
    }

    char const* GateName(uint32 v)
    {
        return v == 1 ? "open" : v == 0 ? "closed" : "not loaded";
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest scholo instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id], DungeonTest::StateName(
            instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        bool any = false;
        for (uint32 id = 0; id < kBossCount; ++id)
            if (ArenaFor(id).Contains(p, z))
            {
                handler->PSendSysMessage("inside: {} arena", kBossNames[id]);
                any = true;
            }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}", p.x, p.y, z, any ? "" : ": in no Scholomance arena");
        return true;
    }

    bool HandleInstancePage(ChatHandler* handler, uint32 page)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        if (page < 1 || page > kKeepsakePageCount)
        {
            handler->SendErrorMessage("Usage: .dbtest scholo instance page <1|2|3>");
            return false;
        }
        instance->SetData(DATA_KEEPSAKE_PAGE, page - 1);
        handler->PSendSysMessage("Keepsake pages: {} of {} (mask {}; pages count on heroic only, before Ras dies).",
            instance->GetData(DATA_KEEPSAKE_PAGE_COUNT), kKeepsakePageCount, instance->GetData(DATA_KEEPSAKE_PAGE));
        return true;
    }

    bool HandleInstanceBind(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_KEEPSAKE_BOUND, 1);
        handler->PSendSysMessage("Keepsake {} (needs all three pages, heroic, Ras alive).",
            instance->GetData(DATA_KEEPSAKE_BOUND) ? "bound" : "NOT bound");
        return true;
    }

    bool HandleInstanceHardMode(ChatHandler* handler, std::string which, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        which = Lower(which);
        uint32 type = 0;
        if (which == "ras")
            type = DATA_RAS_HARD_MODE;
        else if (which == "gandling")
            type = DATA_GANDLING_HARD_MODE;
        else
        {
            handler->SendErrorMessage("Usage: .dbtest scholo instance hardmode <ras|gandling> <0|1>");
            return false;
        }
        instance->SetData(type, lit ? 1 : 0);
        handler->PSendSysMessage("{} hard mode is now {} (lit only on heroic, with the bound keepsake / the honors "
            "program open, while the boss neither fights nor is dead).", which, instance->GetData(type) ? "lit"
            : "off");
        return true;
    }

    bool HandleInstanceGrade(ChatHandler* handler, std::string name)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        Player* target = handler->getSelectedPlayer();
        if (!target)
            target = handler->GetPlayer();
        bool const all = Lower(name) == "all";
        std::optional<Instructor> const one = ParseInstructor(name);
        if (!all && !one)
        {
            handler->SendErrorMessage("Usage: .dbtest scholo instance grade <malicia|krastinov|polkelt|ravenian|"
                "alexei|illucia|all>");
            return false;
        }
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            if (all || Instructor(i) == *one)
                instance->SetGuidData(DataPassingGrade(Instructor(i)), target->GetGUID());
        handler->PSendSysMessage("{}: Passing Grades awarded where allowed (heroic only); honors program {}.",
            target->GetName(), instance->GetData(DATA_HONORS_OPEN) ? "OPEN" : "closed");
        return true;
    }

    bool HandleInstanceGrades(ChatHandler* handler, Optional<std::string> clear)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        InstanceApi* api = GetInstanceApi(instance);
        if (!api)
        {
            handler->SendErrorMessage("This is not the Scholomance rework instance.");
            return false;
        }
        if (clear && Lower(*clear) == "clear")
        {
            api->ClearGrades();
            handler->PSendSysMessage("{}", "Passing Grades cleared.");
            return true;
        }
        for (PassingGrades::Slot const& slot : api->Grades().Slots())
        {
            if (!slot.player)
                continue;
            std::string held;
            for (std::size_t i = 0; i < kInstructorCount; ++i)
                if (slot.mask & (1u << i))
                    held += std::string(held.empty() ? "" : " ") + kInstructorNames[i];
            handler->PSendSysMessage("player {}: {}", slot.player, held);
        }
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            handler->PSendSysMessage("{}: {} holder(s)", kInstructorNames[i],
                instance->GetData(DataGradeHolders(Instructor(i))));
        handler->PSendSysMessage("honors program {} (every instructor needs {} holders)",
            instance->GetData(DATA_HONORS_OPEN) ? "OPEN" : "closed", kHonorsMinHolders);
        return true;
    }

    bool HandleInstanceGate(ChatHandler* handler, uint32 room, uint32 open)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        if (room >= kClassroomCount)
        {
            handler->SendErrorMessage("Usage: .dbtest scholo instance gate <0..5> <0|1>");
            return false;
        }
        instance->SetData(DataClassroomGate(Classroom(room)), open ? 1 : 0);
        handler->PSendSysMessage("{} gate: {}", kClassroomNames[room],
            GateName(instance->GetData(DataClassroomGate(Classroom(room)))));
        return true;
    }

    bool HandleInstanceKirtonos(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_KIRTONOS_THE_HERALD, IN_PROGRESS);
        handler->PSendSysMessage("Kirtonos: {} (summoned only from NOT_STARTED).",
            DungeonTest::StateName(instance->GetData(DATA_KIRTONOS_THE_HERALD)));
        return true;
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",     HandleInstanceBoss,     SEC_GAMEMASTER, Console::No },
            { "where",    HandleInstanceWhere,    SEC_GAMEMASTER, Console::No },
            { "page",     HandleInstancePage,     SEC_GAMEMASTER, Console::No },
            { "bind",     HandleInstanceBind,     SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleInstanceHardMode, SEC_GAMEMASTER, Console::No },
            { "grade",    HandleInstanceGrade,    SEC_GAMEMASTER, Console::No },
            { "grades",   HandleInstanceGrades,   SEC_GAMEMASTER, Console::No },
            { "gate",     HandleInstanceGate,     SEC_GAMEMASTER, Console::No },
            { "kirtonos", HandleInstanceKirtonos, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_scholo_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapScholomance;
    shell.dungeonName = "Scholomance";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("Kirtonos {}, instructors done {}/{}, Gandling {}",
            DungeonTest::StateName(instance->GetData(DATA_KIRTONOS_THE_HERALD)), instance->GetData(DATA_MINI_BOSSES),
            kInstructorCount, instance->GetData(DATA_GANDLING_REVEALED) ? "revealed" : "hidden");
        handler->PSendSysMessage("keepsake pages {}/{} bound {}; Ras hard mode {} (kill {}); Gandling hard mode {} "
            "(kill {}); honors program {}", instance->GetData(DATA_KEEPSAKE_PAGE_COUNT), kKeepsakePageCount,
            instance->GetData(DATA_KEEPSAKE_BOUND), instance->GetData(DATA_RAS_HARD_MODE),
            instance->GetData(DATA_RAS_HARD_MODE_KILLED), instance->GetData(DATA_GANDLING_HARD_MODE),
            instance->GetData(DATA_GANDLING_HARD_MODE_KILLED), instance->GetData(DATA_HONORS_OPEN) ? "open" : "closed");
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            handler->PSendSysMessage("{}: gate {}, detained {}", kClassroomNames[i],
                GateName(instance->GetData(DataClassroomGate(Classroom(i)))),
                instance->GetGuidData(DataDetained(Classroom(i))).ToString());
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    ScholoTest::RegisterBoss("instance", InstanceTestCommands());
}
