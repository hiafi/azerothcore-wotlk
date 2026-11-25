/*
 * mod-dungeon-bosses, Ragefire Chasm: the `.dbtest rfc` command shell (RagefireChasmTestCommand.h) and WP-S0's own
 * subcommands:
 *
 *   .dbtest rfc gate open|close                set slots 0 to 2 DONE / NOT_STARTED, as three kills or none would: the
 *                                              third DONE clears Taragaman's dormant state and plays line 0 (a living
 *                                              lieutenant that resets afterwards writes his slot NOT_STARTED again)
 *   .dbtest rfc section <name>                 teleport: entrance, den, hall, ridge, plateau, shrine, pour, checkpoint
 *   .dbtest rfc instance boss <id> <state>     set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...)
 *   .dbtest rfc instance where                 which Ragefire Chasm arenas and floors hold the GM's position, and the
 *                                              rim distance on the ridge (the playtest's .gps checks)
 */

#include "RagefireChasmTestCommand.h"
#include "Chat.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "RagefireChasmRework.h"
#include <array>
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;

namespace RfcTest
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!RequireRagefireChasm(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    bool ShowHardModeInfo(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        handler->PSendSysMessage("Starving: flag {}, kill {}, Taragaman {}; gate {}, heroic {}",
            instance->GetData(DATA_HARD_MODE), DungeonTest::StateName(instance->GetBossState(BOSS_STARVING)),
            DungeonTest::StateName(instance->GetBossState(BOSS_TARAGAMAN)),
            instance->GetData(DATA_GATE_OPEN) ? "open" : "closed",
            handler->GetPlayer()->GetMap()->IsHeroic() ? "yes" : "no");
        return true;
    }

    bool ArmHardMode(ChatHandler* handler, bool lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_HARD_MODE, lit ? 1 : 0);
        if ((instance->GetData(DATA_HARD_MODE) != 0) != lit)
            handler->SendErrorMessage("Refused: heroic only, and never once Taragaman is engaged or dead.");
        return ShowHardModeInfo(handler);
    }
}

namespace
{
    struct Section
    {
        char const* name;
        Point3 at;
    };

    // Where each room is entered from (section 3.8), clear of its boss.
    std::array<Section, 8> constexpr kSections{ {
        { "entrance",   kFinderStart },
        { "den",        { kDenNeck.x, kDenNeck.y, kDenNeck.z, 1.57f } },
        { "hall",       { kHallStrip.x, kHallStrip.y, kHallStrip.z, 3.14f } },
        { "ridge",      { kRidgeNeck.x, kRidgeNeck.y, kRidgeNeck.z, 5.0f } },
        { "plateau",    { -274.0f, 147.0f, -21.8f, 0.1f } },        // the -x arm, where the ruled route arrives
        { "shrine",     { kBloodShrine.x + 2.f, kBloodShrine.y + 2.f, kBloodShrine.z, 4.0f } },
        { "pour",       { -274.0f, 147.0f, -21.8f, 4.0f } },
        { "checkpoint", kCheckpoint },
    } };

    bool HandleGate(ChatHandler* handler, std::string what)
    {
        InstanceScript* instance = RfcTest::GmInstance(handler);
        if (!instance)
            return false;
        if (what != "open" && what != "close")
        {
            handler->SendErrorMessage("Usage: .dbtest rfc gate <open|close>");
            return false;
        }
        for (uint32 id = 0; id < kGateBossCount; ++id)
            instance->SetBossState(id, what == "open" ? DONE : NOT_STARTED);
        handler->PSendSysMessage("Gate {}; Taragaman is {}.", instance->GetData(DATA_GATE_OPEN) ? "open" : "closed",
            instance->GetData(DATA_TARAGAMAN_DORMANT) ? "dormant" : "not dormant");
        return true;
    }

    ChatCommandTable const& GateTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandleGate, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleSection(ChatHandler* handler, std::string name)
    {
        if (!RfcTest::RequireRagefireChasm(handler))
            return false;
        for (Section const& section : kSections)
        {
            if (name != section.name)
                continue;
            handler->GetPlayer()->NearTeleportTo(section.at.x, section.at.y, section.at.z, section.at.o);
            handler->PSendSysMessage("{}: ({:.1f}, {:.1f}, {:.1f})", section.name, section.at.x, section.at.y,
                section.at.z);
            return true;
        }
        handler->SendErrorMessage("Usage: .dbtest rfc section "
            "<entrance|den|hall|ridge|plateau|shrine|pour|checkpoint>");
        return false;
    }

    ChatCommandTable const& SectionTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandleSection, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = RfcTest::GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest rfc instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!RfcTest::RequireRagefireChasm(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        std::array<std::pair<char const*, Arena>, 7> const places{ {
            { "Oggleflint's arena (den and neck)", OggleflintArena() },
            { "the den's floor", DenFloor() },
            { "Jergosh's arena (hall)", JergoshArena() },
            { "Bazzalan's arena (4 yd inside the rims)", BazzalanArena() },
            { "the ridge's floor", RidgeFloor() },
            { "Taragaman's arena (2 yd inside the edges)", TaragamanArena() },
            { "the plateau's floor", PlateauFloor() },
        } };
        bool any = false;
        for (auto const& [name, arena] : places)
            if (arena.Contains(p, z))
            {
                handler->PSendSysMessage("inside: {}", name);
                any = true;
            }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}; rim distance {:.1f}; hub distance {:.1f}", p.x, p.y, z,
            any ? "" : ": in no Ragefire Chasm arena", RimDistance(p), DungeonKit::Distance(p, kHub.XY()));
        return true;
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",  HandleInstanceBoss,  SEC_GAMEMASTER, Console::No },
            { "where", HandleInstanceWhere, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_rfc_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapRagefireChasm;
    shell.dungeonName = "Ragefire Chasm";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("gate {}, Taragaman {}, hard mode {}, hard mode kill {}",
            instance->GetData(DATA_GATE_OPEN) ? "open" : "closed",
            instance->GetData(DATA_TARAGAMAN_DORMANT) ? "dormant" : "not dormant",
            instance->GetData(DATA_HARD_MODE), instance->GetData(DATA_HARD_MODE_KILLED));
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    RfcTest::RegisterBoss("gate", GateTestCommands());
    RfcTest::RegisterBoss("section", SectionTestCommands());
    RfcTest::RegisterBoss("instance", InstanceTestCommands());
}
