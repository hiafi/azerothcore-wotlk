/*
 * mod-dungeon-bosses, Shadowfang Keep: the `.sfktest` command shell (ShadowfangKeepTestCommand.h) and WP-K's own
 * subcommands:
 *
 *   .sfktest instance captain <present|absent>   force the Deathsworn Captain's saved roll (takes effect when he next
 *                                                spawns: an instance reset, or `.npc add 3872`)
 *   .sfktest instance prisoner <0|1|2>           DATA_PRISONER (0 unknown, 1 Ashcrombe, 2 Adamant)
 *   .sfktest instance hardmode <0|1>             DATA_HARD_MODE (Face Him Alone), as S10's gossip sets it
 *   .sfktest instance boss <id> <state>          set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...): doors,
 *                                                the lair prisoner, the hard mode flag
 *   .sfktest instance where                      which SFK arenas hold the GM's position (the playtest's .gps checks)
 *   .sfktest cells los                           per cell: its door's state, whether the GM is inside, and line of
 *                                                sight from the GM to the cell's landing point (handoff section 7 #6:
 *                                                does a closed cell door, display 411, block LoS?)
 *   .sfktest cells open|close <s|m|n|all>        open or close cell doors
 */

#include "ShadowfangKeepTestCommand.h"
#include "Chat.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Player.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <cctype>
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

namespace
{
    std::array<uint32, kCellCount> constexpr kCellDoorData{ { DATA_CELL_DOOR_S_GUID, DATA_CELL_DOOR_M_GUID,
        DATA_CELL_DOOR_N_GUID } };
    std::array<char const*, kCellCount> constexpr kCellNames{ { "S", "M", "N" } };
    std::array<char const*, kCellCount> constexpr kCellKeys{ { "s", "m", "n" } };

    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    char const* PrisonerName(uint32 prisoner)
    {
        switch (prisoner)
        {
            case Prisoner::Ashcrombe:
                return "Ashcrombe";
            case Prisoner::Adamant:
                return "Adamant";
            default:
                return "unknown";
        }
    }

    char const* RollName(uint32 roll)
    {
        switch (roll)
        {
            case DungeonKit::Roll::Present:
                return "present";
            case DungeonKit::Roll::Absent:
                return "absent";
            default:
                return "unrolled";
        }
    }

    bool HandleInstanceCaptain(ChatHandler* handler, std::string roll)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        uint32 value = DungeonKit::Roll::Unrolled;
        if (roll == "present")
            value = DungeonKit::Roll::Present;
        else if (roll == "absent")
            value = DungeonKit::Roll::Absent;
        else
        {
            handler->SendErrorMessage("Usage: .sfktest instance captain <present|absent>");
            return false;
        }
        instance->SetData(DATA_CAPTAIN_ROLL, value);
        handler->PSendSysMessage("Deathsworn Captain roll is now {} (applies when he next spawns).",
            RollName(instance->GetData(DATA_CAPTAIN_ROLL)));
        return true;
    }

    bool HandleInstancePrisoner(ChatHandler* handler, uint32 prisoner)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        if (prisoner > Prisoner::Adamant)
        {
            handler->SendErrorMessage("Usage: .sfktest instance prisoner <0|1|2> (unknown, Ashcrombe, Adamant)");
            return false;
        }
        instance->SetData(DATA_PRISONER, prisoner);
        handler->PSendSysMessage("Prisoner is now {}.", PrisonerName(instance->GetData(DATA_PRISONER)));
        return true;
    }

    bool HandleInstanceHardMode(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_HARD_MODE, lit ? 1 : 0);
        handler->PSendSysMessage("Face Him Alone (hard mode) is now {} (not lit while Arugal fights, ignored once "
            "he is dead).", instance->GetData(DATA_HARD_MODE) ? "chosen" : "off");
        return true;
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch (R1 N-6).
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .sfktest instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id], DungeonTest::StateName(
            instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        std::array<std::pair<char const*, Arena>, 12> const arenas{ {
            { "Rethilgore (corridor + cells)", RethilgoreArena() },
            { "cell S", CellArena(CELL_S) },
            { "cell M", CellArena(CELL_M) },
            { "cell N", CellArena(CELL_N) },
            { "Razorclaw", RazorclawArena() },
            { "Silverlaine", SilverlaineArena() },
            { "Springvale", SpringvaleArena() },
            { "Odo", OdoArena() },
            { "Deathsworn Captain", DeathswornCaptainArena() },
            { "Fenrus", FenrusArena() },
            { "Nandos", NandosArena() },
            { "Arugal", ArugalArena() },
        } };
        bool any = false;
        for (auto const& [name, arena] : arenas)
            if (arena.Contains(p, z))
            {
                handler->PSendSysMessage("inside: {}", name);
                any = true;
            }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}", p.x, p.y, z, any ? "" : ": in no SFK arena");
        return true;
    }

    bool HandleCellsLos(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        for (std::size_t i = 0; i < kCellCount; ++i)
        {
            GameObject* door = instance->GetGameObject(kCellDoorData[i]);
            Point3 const& landing = kCellLandings[i];
            bool const los = gm->IsWithinLOS(landing.x, landing.y, landing.z + 1.f);
            handler->PSendSysMessage("cell {}: door {}, you are {} it, LoS to its landing point: {}", kCellNames[i],
                !door ? "not loaded" : door->GetGoState() == GO_STATE_READY ? "closed" : "open",
                CellArena(CellId(i)).Contains(p, gm->GetPositionZ()) ? "inside" : "outside", los ? "yes" : "NO");
        }
        return true;
    }

    bool SetCells(ChatHandler* handler, std::string which, bool open)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        std::transform(which.begin(), which.end(), which.begin(),
            [](unsigned char c) { return char(std::tolower(c)); });
        bool any = false;
        for (std::size_t i = 0; i < kCellCount; ++i)
        {
            if (which != "all" && which != kCellKeys[i])
                continue;
            if (GameObject* door = instance->GetGameObject(kCellDoorData[i]))
            {
                door->SetGoState(open ? GO_STATE_ACTIVE : GO_STATE_READY);
                handler->PSendSysMessage("cell {} door {}.", kCellNames[i], open ? "opened" : "closed");
                any = true;
            }
        }
        if (!any)
            handler->SendErrorMessage("Usage: .sfktest cells {} <s|m|n|all> (the door must be loaded)",
                open ? "open" : "close");
        return any;
    }

    bool HandleCellsOpen(ChatHandler* handler, std::string which)
    {
        return SetCells(handler, std::move(which), true);
    }

    bool HandleCellsClose(ChatHandler* handler, std::string which)
    {
        return SetCells(handler, std::move(which), false);
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "captain",  HandleInstanceCaptain,  SEC_GAMEMASTER, Console::No },
            { "prisoner", HandleInstancePrisoner, SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleInstanceHardMode, SEC_GAMEMASTER, Console::No },
            { "boss",     HandleInstanceBoss,     SEC_GAMEMASTER, Console::No },
            { "where",    HandleInstanceWhere,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    ChatCommandTable const& CellsTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "los",   HandleCellsLos,   SEC_GAMEMASTER, Console::No },
            { "open",  HandleCellsOpen,  SEC_GAMEMASTER, Console::No },
            { "close", HandleCellsClose, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_sfktest_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapShadowfangKeep;
    shell.dungeonName = "Shadowfang Keep";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("courtyard {}, prisoner {}, hard mode {}, hard mode kill {}, Captain roll {}",
            DungeonTest::StateName(instance->GetData(DATA_COURTYARD)), PrisonerName(instance->GetData(DATA_PRISONER)),
            instance->GetData(DATA_HARD_MODE), instance->GetData(DATA_HARD_MODE_KILLED),
            RollName(instance->GetData(DATA_CAPTAIN_ROLL)));
        handler->PSendSysMessage("lair prisoner {}", instance->GetGuidData(DATA_LAIR_PRISONER_GUID).ToString());
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    SfkTest::RegisterBoss("instance", InstanceTestCommands());
    SfkTest::RegisterBoss("cells", CellsTestCommands());
}
