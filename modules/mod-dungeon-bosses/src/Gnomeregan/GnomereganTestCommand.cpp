/*
 * mod-dungeon-bosses, Gnomeregan: the `.dbtest gnomer` command shell (GnomereganTestCommand.h) and WP-S0's own
 * subcommands (handoff section 3.2 item 10):
 *
 *   .dbtest gnomer section <1|2>               teleport to the Finder section's start; prints its Finder ids, its end
 *                                              boss and the doors on its path
 *   .dbtest gnomer door <shut|unlock|open>     the Workshop Door's state (sealed, unlocked, open), any direction
 *   .dbtest gnomer hardmode <arm|clear>        the hard mode flag (heroic only; never while Thermaplugg fights or is
 *                                              DONE). Arming sets the console's flag; his next pull still needs D6's
 *                                              packages (the verdict) to arm the fight
 *   .dbtest gnomer chest [0|1]                 place Crowd Pummeler's chest now (1, the default) or remove it (0)
 *                                              and hold it off until `chest 1` or a reload
 *   .dbtest gnomer endnpc <0|1|2>              summon End NPC 1 or 2 now (any difficulty), or remove both (0)
 *   .dbtest gnomer go <place>                  teleport: entrance, techbot, fallout, electro, depot, hall, pocket,
 *                                              lower, thermaplugg, console, punch-a
 *   .dbtest gnomer where                       which Gnomeregan arenas hold the GM's position (the playtest's .gps)
 *   .dbtest gnomer boss <slot> <state>         set a slot's state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...)
 */

#include "GnomereganTestCommand.h"
#include "Chat.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "GnomereganRework.h"
#include <array>
#include <cctype>
#include <optional>
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;

namespace GnomerTest
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!RequireGnomeregan(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    void PrintRunState(ChatHandler* handler, InstanceScript const* instance)
    {
        uint32 const door = instance->GetData(DATA_WORKSHOP_DOOR);
        uint32 const chest = instance->GetData(DATA_PUMMELER_CHEST);
        handler->PSendSysMessage("workshop door {} ({}), final chamber open {}, section {}", door,
            door < kWorkshopDoorNames.size() ? kWorkshopDoorNames[door] : "?", instance->GetData(DATA_FINAL_CHAMBER),
            instance->GetData(DATA_SECTION));
        handler->PSendSysMessage("hard mode: flag {}, verdict {}, kill {}, console key {}",
            instance->GetData(DATA_HARD_MODE), instance->GetData(DATA_HARD_MODE_VERDICT),
            instance->GetData(DATA_HARD_MODE_KILLED), instance->GetData(DATA_HARD_MODE_KEY));
        handler->PSendSysMessage("pummeler chest {} ({}), end npc 1 {}, end npc 2 {}", chest,
            chest < kChestNames.size() ? kChestNames[chest] : "?", instance->GetData(DATA_END_NPC_BASE + 1),
            instance->GetData(DATA_END_NPC_BASE + 2));
    }
}

namespace
{
    struct Place
    {
        char const* name;
        Point3 at;
    };

    // Where each room is entered from (section 3.8), clear of its boss; z from the mesh.
    std::array<Place, 11> constexpr kPlaces{ {
        { "entrance",    kSection1Start },
        { "techbot",     { -526.8f, -90.2f, -154.7f, 5.15f } },        // the dish's free disc, facing Techbot
        { "fallout",     { -410.0f, 112.0f, -210.8f, 0.80f } },        // short of area C
        { "electro",     kCheckpointElectrocutioner },                 // the walkway mouth
        { "depot",       kSection2Start },
        { "hall",        { -775.1f, 211.5f, -272.9f, 0.62f } },        // the hall's centroid, facing the spot
        { "pocket",      { -898.8f, 359.8f, -272.4f, 0.f } },          // the pocket's free disc, facing the glass
        { "lower",       { -860.0f, 390.0f, -316.5f, 3.14f } },        // the lower room (Punchograph D)
        { "thermaplugg", { -560.0f, 675.0f, -327.0f, 6.1f } },         // the south entrance, inside the console pack
        { "console",     { -576.0f, 680.0f, -327.0f, 3.0f } },
        { "punch-a",     { -500.0f, 70.0f, -154.8f, 2.6f } },          // beside the 3005-A copy
    } };

    std::string Lower(std::string s)
    {
        for (char& c : s)
            c = char(std::tolower(static_cast<unsigned char>(c)));
        return s;
    }

    bool HandleSection(ChatHandler* handler, uint32 number)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        FinderSection const* section = SectionByNumber(number);
        if (!section)
        {
            handler->SendErrorMessage("Usage: .dbtest gnomer section <1|2>");
            return false;
        }
        Player* gm = handler->GetPlayer();
        gm->NearTeleportTo(section->start.x, section->start.y, section->start.z, section->start.o);
        handler->PSendSysMessage("Section {} {} (Finder {} / heroic {}): start ({:.1f}, {:.1f}, {:.1f}); ends on {} "
            "({}); run section now {}", section->number, section->name, section->lfgNormal, section->lfgHeroic,
            section->start.x, section->start.y, section->start.z, kBossNames[section->endSlot],
            DungeonTest::StateName(instance->GetBossState(section->endSlot)), instance->GetData(DATA_SECTION));
        for (uint32 entry : section->doors)
        {
            if (!entry)
                continue;
            GameObject* door = gm->FindNearestGameObject(entry, 2000.f);
            if (door)
                handler->PSendSysMessage("  door {} {}: state {} at ({:.1f}, {:.1f}, {:.1f})", entry, door->GetName(),
                    uint32(door->GetGoState()), door->GetPositionX(), door->GetPositionY(), door->GetPositionZ());
            else
                handler->PSendSysMessage("  door {}: not loaded (its grid is not active)", entry);
        }
        return true;
    }

    bool HandleDoor(ChatHandler* handler, std::string what)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        what = Lower(what);
        std::optional<uint32> state;
        if (what == "shut" || what == "sealed" || what == "0")
            state = WORKSHOP_DOOR_SEALED;
        else if (what == "unlock" || what == "unlocked" || what == "1")
            state = WORKSHOP_DOOR_UNLOCKED;
        else if (what == "open" || what == "2")
            state = WORKSHOP_DOOR_OPEN;
        if (!state)
        {
            handler->SendErrorMessage("Usage: .dbtest gnomer door <shut|unlock|open>");
            return false;
        }
        instance->SetData(DATA_GM_DOOR, *state);
        GnomerTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleHardMode(ChatHandler* handler, std::string what)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        what = Lower(what);
        if (what != "arm" && what != "clear")
        {
            handler->SendErrorMessage("Usage: .dbtest gnomer hardmode <arm|clear>");
            return false;
        }
        uint32 const value = what == "arm" ? 1 : 0;
        instance->SetData(DATA_GM_HARD_MODE, value);
        if (instance->GetData(DATA_HARD_MODE) != value)
            handler->SendErrorMessage("Refused: heroic only to arm, never while Thermaplugg fights or is DONE.");
        GnomerTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleChest(ChatHandler* handler, Optional<uint32> place)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GM_CHEST, place.value_or(1) ? 1 : 0);
        GnomerTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleEndNpc(ChatHandler* handler, uint32 which)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        if (which > kEndNpcCount)
        {
            handler->SendErrorMessage("Usage: .dbtest gnomer endnpc <0|1|2> (0 removes both)");
            return false;
        }
        instance->SetData(DATA_GM_END_NPC, which);
        GnomerTest::PrintRunState(handler, instance);
        return true;
    }

    bool HandleGo(ChatHandler* handler, std::string name)
    {
        if (!GnomerTest::RequireGnomeregan(handler))
            return false;
        name = Lower(name);
        for (Place const& place : kPlaces)
        {
            if (name != place.name)
                continue;
            handler->GetPlayer()->NearTeleportTo(place.at.x, place.at.y, place.at.z, place.at.o);
            handler->PSendSysMessage("{}: ({:.1f}, {:.1f}, {:.1f})", place.name, place.at.x, place.at.y, place.at.z);
            return true;
        }
        handler->SendErrorMessage("Usage: .dbtest gnomer go <entrance|techbot|fallout|electro|depot|hall|pocket|lower|"
            "thermaplugg|console|punch-a>");
        return false;
    }

    bool HandleWhere(ChatHandler* handler)
    {
        if (!GnomerTest::RequireGnomeregan(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        std::array<std::pair<char const*, Arena>, 7> const places{ {
            { "Techbot's dish", DishArena() },
            { "Viscous Fallout's cave", CaveArena() },
            { "Electrocutioner's platform", PlatformArena() },
            { "the platform's pick disc (21 yd)", PlatformPickArena() },
            { "the Alert hall", HallArena() },
            { "Crowd Pummeler's pocket", PocketArena() },
            { "Thermaplugg's room", RoomArena() },
        } };
        bool any = false;
        for (auto const& [name, arena] : places)
            if (arena.Contains(p, z))
            {
                handler->PSendSysMessage("inside: {}", name);
                any = true;
            }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}; pocket box {}", p.x, p.y, z,
            any ? "" : ": in no Gnomeregan arena", InPocketBox(p.x, p.y, z) ? "yes" : "no");
        return true;
    }

    bool HandleBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = GnomerTest::GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest gnomer boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    template <auto Handler>
    ChatCommandTable const& Single()
    {
        static ChatCommandTable const commands =
        {
            { "", *Handler, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_gnomer_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapGnomeregan;
    shell.dungeonName = "Gnomeregan";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        GnomerTest::PrintRunState(handler, instance);
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    GnomerTest::RegisterBoss("section", Single<HandleSection>());
    GnomerTest::RegisterBoss("door", Single<HandleDoor>());
    GnomerTest::RegisterBoss("hardmode", Single<HandleHardMode>());
    GnomerTest::RegisterBoss("chest", Single<HandleChest>());
    GnomerTest::RegisterBoss("endnpc", Single<HandleEndNpc>());
    GnomerTest::RegisterBoss("go", Single<HandleGo>());
    GnomerTest::RegisterBoss("where", Single<HandleWhere>());
    GnomerTest::RegisterBoss("boss", Single<HandleBoss>());
}
