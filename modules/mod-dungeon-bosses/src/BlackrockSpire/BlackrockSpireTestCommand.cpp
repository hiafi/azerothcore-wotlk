/*
 * mod-dungeon-bosses, Blackrock Spire: the `.dbtest brs` command shell (BlackrockSpireTestCommand.h) and WP-S0's own
 * subcommands:
 *
 *   .dbtest brs instance boss <id> <state>     set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...): doors,
 *                                              the pile, the kill flags
 *   .dbtest brs instance where                 which Blackrock Spire arenas hold the GM's position (the playtest's
 *                                              .gps checks), and whether it is the Dragonspire Hall
 *   .dbtest brs instance runes                 start the Dragonspire room check, as area trigger 2046 does
 *   .dbtest brs instance urokreset             the Urok challenge's reset, as the stock SetData(4, FAIL) sends it
 *   .dbtest brs instance pile <1|2>            the pile: 1 ready (from in use), 2 in use (from ready), as B5 sends it
 *   .dbtest brs instance flame <0-3>           Father Flame's flame: none, held, on the floor, in the brazier
 *   .dbtest brs instance horn <0|1>            Wyrmthalak's war horn (heroic, he neither fights nor is dead)
 *   .dbtest brs instance insult <0|1>          Nefarius's insult (wave 2 bound, Drakkisath not dead; saved)
 *   .dbtest brs instance army <0|1>            the General's Army (heroic, wave 2 bound, the insult saved, Drakkisath
 *                                              neither fighting nor dead)
 */

#include "BlackrockSpireTestCommand.h"
#include "BlackrockSpireRework.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKitFlex.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "StringFormat.h"
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest brs instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        bool any = false;
        for (uint32 id = 0; id < kBossCount; ++id)
        {
            if (IsHardModeSlot(id) || id == BOSS_GIZRUL || id == BOSS_GYTH)
                continue;       // the same arena as another slot
            if (ArenaFor(id).Contains(p, z))
            {
                handler->PSendSysMessage("inside: {} arena", kBossNames[id]);
                any = true;
            }
        }
        if (InDragonspireHall(p.x, p.y, z))
        {
            handler->PSendSysMessage("inside: the Dragonspire Hall (the room check's self-start box)");
            any = true;
        }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}", p.x, p.y, z, any ? "" : ": in no Blackrock Spire arena");
        return true;
    }

    bool HandleInstanceRunes(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_ROOM_CHECK, 1);
        handler->PSendSysMessage("Room check started (runes done mask {:#x}; room {}). The store runs in 1 s.",
            instance->GetData(DATA_HALL_RUNES_DONE),
            DungeonTest::StateName(instance->GetBossState(BOSS_DRAGONSPIRE_ROOM)));
        return true;
    }

    bool HandleInstanceUrokReset(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_UROK_EVENT, FAIL);
        handler->PSendSysMessage("Urok challenge reset; pile: {}", UrokPileName(instance->GetData(DATA_UROK_PILE)));
        return true;
    }

    bool HandleInstancePile(ChatHandler* handler, uint32 pile)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_UROK_PILE, pile);
        handler->PSendSysMessage("Urok pile: {} (1 ready only from in use, 2 in use only from ready).",
            UrokPileName(instance->GetData(DATA_UROK_PILE)));
        return true;
    }

    bool HandleInstanceFlame(ChatHandler* handler, uint32 flame)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_SOLAKAR_FLAME, flame);
        handler->PSendSysMessage("Father Flame's flame: {}", SolakarFlameName(instance->GetData(DATA_SOLAKAR_FLAME)));
        return true;
    }

    bool HandleInstanceHorn(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_WAR_HORN, lit ? 1 : 0);
        handler->PSendSysMessage("War horn is now {} (lit only on heroic, while Wyrmthalak neither fights nor is dead; "
            "per pull).", instance->GetData(DATA_WAR_HORN) ? "blown" : "off");
        return true;
    }

    bool HandleInstanceInsult(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_NEF_INSULTED, lit ? 1 : 0);
        handler->PSendSysMessage("Insult is now {} (set only once wave 2 is bound, while Drakkisath neither fights nor "
            "is dead; saved).", instance->GetData(DATA_NEF_INSULTED) ? "given" : "not given");
        return true;
    }

    bool HandleInstanceArmy(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GENERALS_ARMY, lit ? 1 : 0);
        handler->PSendSysMessage("General's Army is now {} (armed only on heroic, once wave 2 is bound, with the "
            "insult saved, while Drakkisath neither fights nor is dead; per pull).",
            instance->GetData(DATA_GENERALS_ARMY) ? "armed" : "off");
        return true;
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",      HandleInstanceBoss,      SEC_GAMEMASTER, Console::No },
            { "where",     HandleInstanceWhere,     SEC_GAMEMASTER, Console::No },
            { "runes",     HandleInstanceRunes,     SEC_GAMEMASTER, Console::No },
            { "urokreset", HandleInstanceUrokReset, SEC_GAMEMASTER, Console::No },
            { "pile",      HandleInstancePile,      SEC_GAMEMASTER, Console::No },
            { "flame",     HandleInstanceFlame,     SEC_GAMEMASTER, Console::No },
            { "horn",      HandleInstanceHorn,      SEC_GAMEMASTER, Console::No },
            { "insult",    HandleInstanceInsult,    SEC_GAMEMASTER, Console::No },
            { "army",      HandleInstanceArmy,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }

    // `.dbtest brs state`'s flex line: the count each boss on the map holds for its fight (0: not held).
    std::string FlexLine(InstanceScript const* instance)
    {
        std::string line;
        for (uint32 id = 0; id < kBossCount; ++id)
        {
            if (!IsEncounterSlot(id))
                continue;
            Creature* boss = instance->instance->GetCreature(instance->GetGuidData(id));
            if (!boss)
                continue;
            uint8 const held = DungeonKit::Flex::Held(boss);
            if (!held && !boss->IsInCombat())
                continue;
            line += Acore::StringFormat("{}{} {} (max {})", line.empty() ? "" : "; ", kBossNames[id], held,
                boss->GetMaxHealth());
        }
        return line.empty() ? "no boss holds a count (none engaged)" : line;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_brs_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapBlackrockSpire;
    shell.dungeonName = "Blackrock Spire";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("flex held: {}", FlexLine(instance));
        handler->PSendSysMessage("Dragonspire room {} (runes done {:#x}, check {}); Urok pile {}; Solakar event {}, "
            "flame {}", DungeonTest::StateName(instance->GetBossState(BOSS_DRAGONSPIRE_ROOM)),
            instance->GetData(DATA_HALL_RUNES_DONE), instance->GetData(DATA_ROOM_CHECK) ? "running" : "idle",
            UrokPileName(instance->GetData(DATA_UROK_PILE)),
            DungeonTest::StateName(instance->GetData(DATA_SOLAKAR_EVENT)),
            SolakarFlameName(instance->GetData(DATA_SOLAKAR_FLAME)));
        handler->PSendSysMessage("war horn {} (kill {}); insult {}; General's Army {} (kill {}); Vaelastrasz {}; "
            "wave 2 {}", instance->GetData(DATA_WAR_HORN),
            DungeonTest::StateName(instance->GetBossState(BOSS_WAR_HORN)), instance->GetData(DATA_NEF_INSULTED),
            instance->GetData(DATA_GENERALS_ARMY), DungeonTest::StateName(instance->GetBossState(BOSS_GENERALS_ARMY)),
            DungeonTest::StateName(instance->GetData(DATA_VAELASTRASZ)), kWave2Bound ? "bound" : "stock");
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    BrsTest::RegisterBoss("instance", InstanceTestCommands());
}
