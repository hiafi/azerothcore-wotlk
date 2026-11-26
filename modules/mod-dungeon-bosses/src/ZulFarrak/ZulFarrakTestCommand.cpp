/*
 * mod-dungeon-bosses, Zul'Farrak: the `.dbtest zf` command shell (ZulFarrakTestCommand.h) and WP-S0's own
 * subcommands (handoff section 3.2 item 10):
 *
 *   .dbtest zf stage <0..4>                    the Pyramid: that stage in play and idle (4: the Pyramid DONE, the crew
 *                                              at the gather spots); a running stage is dropped (its director's OnEnd)
 *   .dbtest zf crew                            the crew's mask, modes, path, Test key and pool line
 *   .dbtest zf crew mask <0..31>               the living crew (bit 0 Bly, 1 Raven, 2 Oro, 3 Weegli, 4 Murta; Weegli is
 *                                              always alive); members that must stand are restored
 *   .dbtest zf crew path <0|1|2>               open, betrayal, Test (through the instance's rules)
 *   .dbtest zf crew mode <member> <mode>       a member (name or 0..4) to a mode (name or 0..7): caged, prisoner,
 *                                              ally, gather, boss, yielded, poolally, gone
 *   .dbtest zf door open|close                 blow / shut the End Door (shut with slot 6 DONE: the watch reopens it
 *                                              at once; the fallback is timed from the shutting)
 *   .dbtest zf test arm                        heroic: the Pyramid DONE with all five alive, so Bly offers the Test
 *   .dbtest zf test hardmode [0|1]             heroic: the hard mode flag (never while Gahz'rilla fights or is dead)
 *   .dbtest zf section <name>                  teleport: entrance, courtyard, den, bowl, top, landing, plaza, mesa,
 *                                              pool, checkpoint
 *   .dbtest zf instance boss <id> <state>      set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...)
 *   .dbtest zf instance where                  which Zul'Farrak arenas hold the GM's position (the playtest's .gps)
 */

#include "ZulFarrakTestCommand.h"
#include "Chat.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "ZulFarrakRework.h"
#include <array>
#include <cctype>
#include <optional>
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace ZfTest
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!RequireZulFarrak(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    void PrintRunState(ChatHandler* handler, InstanceScript const* instance)
    {
        uint32 const stage = instance->GetData(DATA_PYRAMID_STAGE);
        handler->PSendSysMessage("pyramid: stage {} ({}), running {}, cages {}, offerings {}, blood price {}, stock "
            "phase {}", stage, stage < kPyramidStageNames.size() ? kPyramidStageNames[stage] : "?",
            instance->GetData(DATA_PYRAMID_RUNNING), instance->GetData(DATA_PYRAMID_CAGES),
            instance->GetData(DATA_OFFERINGS), instance->GetData(DATA_BLOOD_PRICE), instance->GetData(DATA_PYRAMID));
        std::string modes;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            uint32 const mode = instance->GetData(DATA_CREW_MODE_BASE + m);
            modes += Acore::StringFormat("{}{}={}", m ? ", " : "", kCrewNames[m],
                ValidCrewMode(mode) ? kCrewModeNames[mode] : "?");
        }
        handler->PSendSysMessage("crew: alive {}, at the Pyramid's end {}, path {}, test key {}, at the pool {}; {}",
            instance->GetData(DATA_CREW_ALIVE), instance->GetData(DATA_CREW_AT_END), instance->GetData(DATA_CREW_PATH),
            instance->GetData(DATA_TEST_KEY), instance->GetData(DATA_CREW_AT_POOL), modes);
        handler->PSendSysMessage("end door {}, gahz'rilla data {}, hard mode {} (key {}, kill {})",
            instance->GetData(DATA_END_DOOR), instance->GetData(DATA_GAHZRILLA), instance->GetData(DATA_HARD_MODE),
            instance->GetData(DATA_HARD_MODE_KEY), instance->GetData(DATA_HARD_MODE_KILLED));
    }
}

namespace
{
    struct Section
    {
        char const* name;
        Point3 at;
    };

    // Where each room is entered from (section 3.8), clear of its boss; z from the mesh.
    std::array<Section, 10> constexpr kSections{ {
        { "entrance",   kFinderStart },
        { "courtyard",  { kCourtyardDisc.x, kCourtyardDisc.y, kCourtyardDisc.z, 2.2f } },
        { "den",        { kDenMouth.x, kDenMouth.y, kDenMouth.z, 4.6f } },
        { "bowl",       kCheckpoint },
        { "top",        { 1900.0f, 1300.0f, 45.9f, 3.4f } },
        { "landing",    { kLanding.x, kLanding.y, kLanding.z, 4.78f } },
        { "plaza",      { 1888.0f, 1190.0f, 8.9f, 1.5f } },
        { "mesa",       { kMesaRampHead.x, kMesaRampHead.y, kMesaRampHead.z, 3.9f } },
        { "pool",       { kGahzrillaAshore.x, kGahzrillaAshore.y, kGahzrillaAshore.z, 0.8f } },
        { "checkpoint", kCheckpoint },
    } };

    std::string Lower(std::string s)
    {
        for (char& c : s)
            c = char(std::tolower(static_cast<unsigned char>(c)));
        return s;
    }

    template <std::size_t N>
    std::optional<uint32> IndexOf(std::array<char const*, N> const& names, std::string const& what)
    {
        std::string const w = Lower(what);
        for (uint32 i = 0; i < N; ++i)
            if (w == Lower(names[i]) || w == std::to_string(i))
                return i;
        return std::nullopt;
    }

    bool HandleStage(ChatHandler* handler, uint32 stage)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        if (stage > PYRAMID_STAGE_DONE)
        {
            handler->SendErrorMessage("Usage: .dbtest zf stage <0..4> (none, block, stair, altar, done)");
            return false;
        }
        instance->SetData(DATA_GM_STAGE, stage);
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    ChatCommandTable const& StageTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandleStage, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleCrewShow(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleCrewMask(ChatHandler* handler, uint32 mask)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        if (mask > kCrewAll)
        {
            handler->SendErrorMessage("Usage: .dbtest zf crew mask <0..31> (bit 0 Bly, 1 Raven, 2 Oro, 3 Weegli, 4 "
                "Murta)");
            return false;
        }
        instance->SetData(DATA_GM_CREW_MASK, mask);
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleCrewPath(ChatHandler* handler, uint32 path)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_CREW_PATH, path);
        if (instance->GetData(DATA_CREW_PATH) != path)
            handler->SendErrorMessage("Refused: betrayal needs the Pyramid DONE; the Test also heroic and all five "
                "alive at its end; never once the fight runs or is DONE.");
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleCrewMode(ChatHandler* handler, std::string member, std::string mode)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        std::optional<uint32> const m = IndexOf(kCrewNames, member);
        std::optional<uint32> const value = IndexOf(kCrewModeNames, mode);
        if (!m || !value)
        {
            handler->SendErrorMessage("Usage: .dbtest zf crew mode <bly|raven|oro|weegli|murta> "
                "<caged|prisoner|ally|gather|boss|yielded|poolally|gone>");
            return false;
        }
        instance->SetData(DATA_CREW_MODE_BASE + *m, *value);
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    ChatCommandTable const& CrewTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "",     HandleCrewShow, SEC_GAMEMASTER, Console::No },
            { "mask", HandleCrewMask, SEC_GAMEMASTER, Console::No },
            { "path", HandleCrewPath, SEC_GAMEMASTER, Console::No },
            { "mode", HandleCrewMode, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleDoor(ChatHandler* handler, std::string what)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        what = Lower(what);
        if (what != "open" && what != "close")
        {
            handler->SendErrorMessage("Usage: .dbtest zf door <open|close>");
            return false;
        }
        instance->SetData(DATA_GM_DOOR, what == "open" ? 1 : 0);
        handler->PSendSysMessage("End Door data {}", instance->GetData(DATA_END_DOOR));
        return true;
    }

    ChatCommandTable const& DoorTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandleDoor, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleTestArm(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GM_TEST_ARM, 1);
        if (!instance->GetData(DATA_TEST_KEY))
            handler->SendErrorMessage("Refused: heroic only, and never once the crew's fight runs or is DONE.");
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleTestHardMode(ChatHandler* handler, Optional<uint32> lit)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        uint32 const value = lit.value_or(1) ? 1 : 0;
        instance->SetData(DATA_GM_HARD_MODE, value);
        if (instance->GetData(DATA_HARD_MODE) != value)
            handler->SendErrorMessage("Refused: heroic only to arm, never while Gahz'rilla fights or is dead.");
        ZfTest::PrintRunState(handler, instance);
        return true;
    }

    ChatCommandTable const& TestTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "arm",      HandleTestArm,      SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleTestHardMode, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleSection(ChatHandler* handler, std::string name)
    {
        if (!ZfTest::RequireZulFarrak(handler))
            return false;
        name = Lower(name);
        for (Section const& section : kSections)
        {
            if (name != section.name)
                continue;
            handler->GetPlayer()->NearTeleportTo(section.at.x, section.at.y, section.at.z, section.at.o);
            handler->PSendSysMessage("{}: ({:.1f}, {:.1f}, {:.1f})", section.name, section.at.x, section.at.y,
                section.at.z);
            return true;
        }
        handler->SendErrorMessage("Usage: .dbtest zf section "
            "<entrance|courtyard|den|bowl|top|landing|plaza|mesa|pool|checkpoint>");
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
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest zf instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!ZfTest::RequireZulFarrak(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        std::array<std::pair<char const*, Arena>, 10> const places{ {
            { "Theka's courtyard", CourtyardArena() },
            { "Antu'sul's den", DenArena() },
            { "Zum'rah's bowl", BowlArena() },
            { "the Pyramid top", PyramidTopArena() },
            { "the landing", LandingArena() },
            { "the stair", StairArena() },
            { "the plaza", PlazaArena() },
            { "Ukorz's mesa", MesaArena() },
            { "the pool (shore and water)", PoolArena() },
            { "the pool's water", PoolWater() },
        } };
        bool any = false;
        for (auto const& [name, arena] : places)
            if (arena.Contains(p, z))
            {
                handler->PSendSysMessage("inside: {}", name);
                any = true;
            }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}; Pyramid region {}", p.x, p.y, z,
            any ? "" : ": in no Zul'Farrak arena", InPyramidRegion(p) ? "yes" : "no");
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
void AddSC_dungeon_bosses_zf_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapZulFarrak;
    shell.dungeonName = "Zul'Farrak";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        ZfTest::PrintRunState(handler, instance);
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    ZfTest::RegisterBoss("stage", StageTestCommands());
    ZfTest::RegisterBoss("crew", CrewTestCommands());
    ZfTest::RegisterBoss("door", DoorTestCommands());
    ZfTest::RegisterBoss("test", TestTestCommands());
    ZfTest::RegisterBoss("section", SectionTestCommands());
    ZfTest::RegisterBoss("instance", InstanceTestCommands());
}
