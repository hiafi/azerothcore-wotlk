/*
 * mod-dungeon-bosses, Scarlet Monastery: the `.dbtest sm` command shell (ScarletMonasteryTestCommand.h) and WP-S0's own
 * subcommands:
 *
 *   .dbtest sm section <1-4>                   teleport to a Finder section's start (handoff section 3.8) and list the
 *                                              doors on its path with their states
 *   .dbtest sm portal <1-4> [go]               stand wing portal n (1 P1, 2 P1h, 3 P2, 4 P3) now and move the GM onto
 *                                              it; `go` also uses it (the GM and the group near it move on)
 *   .dbtest sm instance boss <id> <state>      set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...) past the
 *                                              slot 6 guard: doors, portals, the hard mode kills
 *   .dbtest sm instance where                  which Scarlet Monastery arenas and wing hold the GM's position (the
 *                                              playtest's .gps checks)
 *   .dbtest sm instance door                   the Chapel Door's start, as if it was used (wave 2 bound)
 *   .dbtest sm instance laststand <state>      D13's protocol: 3 DONE (Mograine fell), 2 FAIL (a wipe), 1 start
 *   .dbtest sm instance ashbringer             fire the Ashbringer event (SetData(2, 1)), through its guard
 *   .dbtest sm instance horseman <state>       hallows_end.cpp's SetData(5, x); shows GetData(5) (always 0)
 *   .dbtest sm instance touch <0-3>            touch Desecration gravestone n (heroic, the council DONE)
 *   .dbtest sm instance page <0-3>             read Doan's evidence page n (heroic)
 *   .dbtest sm instance taunt                  Herod's /taunt trigger (heroic, wave 2 bound)
 *   .dbtest sm instance torch                  the Torch trigger (heroic, wave 2 bound, the Last Stand DONE)
 */

#include "ScarletMonasteryTestCommand.h"
#include "Chat.h"
#include "Creature.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "ScarletMonasteryRework.h"
#include "StringFormat.h"
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;

namespace SmTest
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!RequireScarletMonastery(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    bool ShowHardModeInfo(ChatHandler* handler, char const* name, uint32 flagData, uint32 killSlot)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        handler->PSendSysMessage("{}: flag {}, kill {}, boss {} ({}); heroic {}, wave 2 {}", name,
            instance->GetData(flagData), DungeonTest::StateName(instance->GetBossState(killSlot)),
            kBossNames[HardModeBoss(killSlot)], DungeonTest::StateName(instance->GetBossState(HardModeBoss(killSlot))),
            handler->GetPlayer()->GetMap()->IsHeroic() ? "yes" : "no", kWave2Bound ? "bound" : "stock");
        return true;
    }

    bool ArmHardMode(ChatHandler* handler, uint32 killSlot)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance || !IsHardModeSlot(killSlot))
            return false;
        instance->SetData(DATA_GM_HARD_MODE, killSlot);
        return ShowHardModeInfo(handler, kBossNames[killSlot], HardModeFlagData(killSlot), killSlot);
    }
}

namespace
{
    char const* GoStateName(GOState state)
    {
        switch (state)
        {
            case GO_STATE_ACTIVE:               return "open";
            case GO_STATE_READY:                return "closed";
            case GO_STATE_ACTIVE_ALTERNATIVE:   return "open (alternative)";
            default:                            return "?";
        }
    }

    void ShowDoor(ChatHandler* handler, Player* gm, uint32 entry)
    {
        if (GameObject* door = gm->FindNearestGameObject(entry, 2000.f))
            handler->PSendSysMessage("  door {} {}: {}{} at ({:.1f}, {:.1f}, {:.1f})", entry, door->GetName(),
                GoStateName(door->GetGoState()), door->HasGameObjectFlag(GO_FLAG_LOCKED) ? ", locked" : "",
                door->GetPositionX(), door->GetPositionY(), door->GetPositionZ());
        else
            handler->PSendSysMessage("  door {}: not loaded (its grid is not active, or it is not built yet)", entry);
    }

    bool HandleSection(ChatHandler* handler, uint32 number)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        FinderSection const* section = SectionByNumber(number);
        if (!section)
        {
            handler->SendErrorMessage("Usage: .dbtest sm section <1-4>");
            return false;
        }
        Player* gm = handler->GetPlayer();
        gm->NearTeleportTo(section->start.x, section->start.y, section->start.z, section->start.o);
        handler->PSendSysMessage("Section {} {} (Finder {} / heroic {}): start ({:.1f}, {:.1f}, {:.1f}); ends on {} "
            "({})", section->number, section->name, section->lfgNormal, section->lfgHeroic, section->start.x,
            section->start.y, section->start.z, kBossNames[section->endSlot],
            DungeonTest::StateName(instance->GetBossState(section->endSlot)));
        bool any = false;
        for (uint32 entry : section->doors)
        {
            if (!entry)
                continue;
            any = true;
            ShowDoor(handler, gm, entry);
        }
        if (!any)
            handler->PSendSysMessage("  no door on the path (section 3.8)");
        return true;
    }

    ChatCommandTable const& SectionTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandleSection, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandlePortal(ChatHandler* handler, uint32 id, Optional<std::string> go)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        WingPortal const* portal = PortalById(id);
        if (!portal)
        {
            handler->SendErrorMessage("Usage: .dbtest sm portal <1-4> [go] (1 P1, 2 P1h, 3 P2, 4 P3)");
            return false;
        }
        Player* gm = handler->GetPlayer();
        gm->NearTeleportTo(portal->spot.x + 2.f, portal->spot.y, portal->spot.z, portal->spot.o);
        instance->SetData(DATA_GM_PORTAL, id);
        FinderSection const* to = SectionByNumber(portal->toSection);
        handler->PSendSysMessage("Portal {} at ({:.1f}, {:.1f}, {:.1f}) to section {} ({}); standing portals mask {}.",
            portal->name, portal->spot.x, portal->spot.y, portal->spot.z, portal->toSection, to ? to->name : "?",
            instance->GetData(DATA_PORTALS));
        if (go && *go == "go")
        {
            GameObject* object = gm->FindNearestGameObject(GO_SM_WING_PORTAL, 10.f);
            if (!object)
            {
                handler->SendErrorMessage("The portal is not standing yet (its grid loads with you): retry in a "
                    "second.");
                return false;
            }
            object->Use(gm);
        }
        return true;
    }

    ChatCommandTable const& PortalTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "", HandlePortal, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest sm instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetData(DATA_GM_SLOT_WRITE, 1);
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!SmTest::RequireScarletMonastery(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        bool any = false;
        for (uint32 id = 0; id < kBossCount; ++id)
        {
            if (IsHardModeSlot(id) && id != BOSS_DESECRATION)
                continue;       // the same arena as its boss
            if (ArenaFor(id).Contains(p, z))
            {
                handler->PSendSysMessage("inside: {} arena (section {})", kBossNames[id], SectionOf(id));
                any = true;
            }
        }
        uint32 const wing = WingOf(p);
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}; wing {}{}", p.x, p.y, z,
            any ? "" : ": in no Scarlet Monastery arena", wing, InCrossingLine(p, z) ? "; on the crossing line" : "");
        return true;
    }

    bool HandleInstanceDoor(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_CHAPEL_DOOR_OPENED, 1);
        handler->PSendSysMessage("Chapel Door start sent: the Last Stand is {} (needs wave 2 bound, no Ashbringer; "
            "wave 2 {}).", DungeonTest::StateName(instance->GetData(DATA_LAST_STAND)),
            kWave2Bound ? "bound" : "stock");
        return true;
    }

    bool HandleInstanceLastStand(ChatHandler* handler, uint32 state)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_LAST_STAND, state);
        handler->PSendSysMessage("The Last Stand is {}; the Cathedral stage {}.",
            DungeonTest::StateName(instance->GetData(DATA_LAST_STAND)), instance->GetData(DATA_CATHEDRAL_STAGE));
        return true;
    }

    bool HandleInstanceAshbringer(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(TYPE_ASHBRINGER_EVENT, IN_PROGRESS);
        handler->PSendSysMessage("Ashbringer event sent: GetData(2) = {} (refused so far: {}).",
            instance->GetData(TYPE_ASHBRINGER_EVENT), instance->GetData(DATA_ASHBRINGER_REFUSED));
        return true;
    }

    bool HandleInstanceHorseman(ChatHandler* handler, uint32 state)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(kHallowsEndHorsemanData, state);
        handler->PSendSysMessage("SetData(5, {}): GetData(5) = {} (live: always 0), private field {}.", state,
            instance->GetData(kHallowsEndHorsemanData), instance->GetData(DATA_HORSEMAN_PRIVATE));
        return true;
    }

    bool HandleInstanceTouch(ChatHandler* handler, uint32 stone)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_DESECRATION_TOUCH, stone);
        handler->PSendSysMessage("Gravestone {}: touches {}, verdict {} (0 none, 1 right, 2 wrong, 3 refused, 4 "
            "repeat); the Desecration {}.", stone, instance->GetData(DATA_DESECRATION_TOUCH),
            instance->GetData(DATA_DESECRATION_RESULT), instance->GetData(DATA_HARD_MODE_THALNOS));
        return true;
    }

    bool HandleInstancePage(ChatHandler* handler, uint32 page)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_DOAN_PAGE_READ, page);
        handler->PSendSysMessage("Page {}: {} of 4 read (mask {}); the Heresy {}.", page,
            instance->GetData(DATA_DOAN_PAGE_READ), instance->GetData(DATA_DOAN_PAGES_MASK),
            instance->GetData(DATA_HARD_MODE_DOAN));
        return true;
    }

    bool HandleInstanceTaunt(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_HARD_MODE_HEROD, 1);
        return SmTest::ShowHardModeInfo(handler, "Call to Arms", DATA_HARD_MODE_HEROD, BOSS_CALL_TO_ARMS);
    }

    bool HandleInstanceTorch(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_HARD_MODE_WHITEMANE, 1);
        return SmTest::ShowHardModeInfo(handler, "The Truth", DATA_HARD_MODE_WHITEMANE, BOSS_THE_TRUTH);
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",       HandleInstanceBoss,         SEC_GAMEMASTER, Console::No },
            { "where",      HandleInstanceWhere,        SEC_GAMEMASTER, Console::No },
            { "door",       HandleInstanceDoor,         SEC_GAMEMASTER, Console::No },
            { "laststand",  HandleInstanceLastStand,    SEC_GAMEMASTER, Console::No },
            { "ashbringer", HandleInstanceAshbringer,   SEC_GAMEMASTER, Console::No },
            { "horseman",   HandleInstanceHorseman,     SEC_GAMEMASTER, Console::No },
            { "touch",      HandleInstanceTouch,        SEC_GAMEMASTER, Console::No },
            { "page",       HandleInstancePage,         SEC_GAMEMASTER, Console::No },
            { "taunt",      HandleInstanceTaunt,        SEC_GAMEMASTER, Console::No },
            { "torch",      HandleInstanceTorch,        SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_sm_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapScarletMonastery;
    shell.dungeonName = "Scarlet Monastery";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("stock data: 1 (the Cathedral pair) {}, 2 (Ashbringer) {}, 5 (the Horseman, live 0) "
            "{}, 6 {}; private Horseman field {}; Ashbringer refused {}",
            DungeonTest::StateName(instance->GetData(TYPE_MOGRAINE_AND_WHITE_EVENT)),
            instance->GetData(TYPE_ASHBRINGER_EVENT), instance->GetData(kHallowsEndHorsemanData),
            DungeonTest::StateName(instance->GetData(DATA_HORSEMAN_EVENT)), instance->GetData(DATA_HORSEMAN_PRIVATE),
            instance->GetData(DATA_ASHBRINGER_REFUSED));
        handler->PSendSysMessage("cathedral stage {} (0 before, 1 stand, 2 vigil, 3 done); last stand {}",
            instance->GetData(DATA_CATHEDRAL_STAGE), DungeonTest::StateName(instance->GetData(DATA_LAST_STAND)));
        handler->PSendSysMessage("hard modes: desecration {} (touches {}, verdict {}), heresy {} (pages {}, mask {}), "
            "herod {}, torch {}", instance->GetData(DATA_HARD_MODE_THALNOS),
            instance->GetData(DATA_DESECRATION_TOUCH), instance->GetData(DATA_DESECRATION_RESULT),
            instance->GetData(DATA_HARD_MODE_DOAN), instance->GetData(DATA_DOAN_PAGE_READ),
            instance->GetData(DATA_DOAN_PAGES_MASK), instance->GetData(DATA_HARD_MODE_HEROD),
            instance->GetData(DATA_HARD_MODE_WHITEMANE));
        handler->PSendSysMessage("portals mask {} (1 P1, 2 P1h, 4 P2, 8 P3); wave 2 {}",
            instance->GetData(DATA_PORTALS), kWave2Bound ? "bound" : "stock");
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    SmTest::RegisterBoss("instance", InstanceTestCommands());
    SmTest::RegisterBoss("section", SectionTestCommands());
    SmTest::RegisterBoss("portal", PortalTestCommands());
}
