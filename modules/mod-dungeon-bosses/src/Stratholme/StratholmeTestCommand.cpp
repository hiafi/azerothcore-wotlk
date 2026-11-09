/*
 * mod-dungeon-bosses, Stratholme: the `.dbtest strat` command shell (StratholmeTestCommand.h) and WP-S0's own
 * subcommands:
 *
 *   .dbtest strat instance boss <id> <state>        set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...):
 *                                                   doors, ziggurats, the kill flags
 *   .dbtest strat instance where                    which Stratholme arenas hold the GM's position (the playtest's
 *                                                   .gps checks)
 *   .dbtest strat instance ziggurat <1-3> <1|2>     a ziggurat write, as a boss's death (1) or its crystal (2) sends it
 *                                                   (the softlock fix: a 2 before the 1 is remembered)
 *   .dbtest strat instance baronrun                 start the Baron Run, as the Gauntlet Gate does (SetData(0, 1))
 *   .dbtest strat instance clock <minutes>          set the Baron Run's minutes left (1-45; while it runs)
 *   .dbtest strat instance ultimatum <0|1>          the Baron's hard mode flag, as Ysida's gossip sets it (heroic, the
 *                                                   clock running, the Baron not fighting and not dead)
 *   .dbtest strat instance grandlie <0|1>           Balnazzar's hard mode flag, as the Letter of Proof sets it (heroic,
 *                                                   wave 2 bound, Balnazzar not fighting and not dead)
 */

#include "StratholmeTestCommand.h"
#include "Chat.h"
#include "InstanceScript.h"
#include "Player.h"
#include "StratholmeRework.h"
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    char const* SlaughterStageName(uint32 stage)
    {
        switch (stage)
        {
            case SLAUGHTER_ABOMINATIONS:    return "abominations";
            case SLAUGHTER_RAMSTEIN:        return "Ramstein";
            case SLAUGHTER_MINDLESS_UNDEAD: return "Mindless Undead (retired)";
            case SLAUGHTER_BLACK_GUARD:     return "Black Guards";
            case SLAUGHTER_COMPLETE:        return "complete";
            default:                        return "?";
        }
    }

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest strat instance boss <0..{}> <0..4>", kBossCount - 1);
            return false;
        }
        instance->SetBossState(id, EncounterState(state));
        handler->PSendSysMessage("boss {} {}: {}", id, kBossNames[id],
            DungeonTest::StateName(instance->GetBossState(id)));
        return true;
    }

    bool HandleInstanceWhere(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        bool any = false;
        for (uint32 id = 0; id < kBossCount; ++id)
        {
            if (IsHardModeSlot(id))
                continue;       // the same arena as its boss
            if (ArenaFor(id).Contains(p, z))
            {
                handler->PSendSysMessage("inside: {} arena", kBossNames[id]);
                any = true;
            }
        }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}", p.x, p.y, z, any ? "" : ": in no Stratholme arena");
        return true;
    }

    bool HandleInstanceZiggurat(ChatHandler* handler, uint32 ziggurat, uint32 data)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        if (ziggurat < 1 || ziggurat > kZigguratCount || data < kZigguratBossDead || data > kZigguratCrystalBroken)
        {
            handler->SendErrorMessage("Usage: .dbtest strat instance ziggurat <1-3> <1 boss dead | 2 crystal>");
            return false;
        }
        uint32 const type = DATA_ZIGGURAT1 + ziggurat - 1;
        instance->SetData(type, data);
        handler->PSendSysMessage("ziggurat {}: state {}{}", ziggurat, instance->GetData(type),
            (instance->GetData(DATA_ZIGGURAT_PENDING) & (1u << (ziggurat - 1))) ? " (crystal pending)" : "");
        return true;
    }

    bool HandleInstanceBaronRun(ChatHandler* handler)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_BARON_RUN, 1);
        handler->PSendSysMessage("Baron Run: {} min left (it starts once per instance).",
            instance->GetData(DATA_BARON_RUN_MINUTES));
        return true;
    }

    bool HandleInstanceClock(ChatHandler* handler, uint32 minutes)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_BARON_RUN_MINUTES, minutes);
        handler->PSendSysMessage("Baron Run: {} min left (set only while it runs; 1-{}).",
            instance->GetData(DATA_BARON_RUN_MINUTES), kBaronRunMinutes);
        return true;
    }

    bool HandleInstanceUltimatum(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_ULTIMATUM, lit ? 1 : 0);
        handler->PSendSysMessage("Ultimatum is now {} (lit only on heroic, with the clock running, while the Baron "
            "neither fights nor is dead).", instance->GetData(DATA_ULTIMATUM) ? "lit" : "off");
        return true;
    }

    bool HandleInstanceGrandLie(ChatHandler* handler, uint32 lit)
    {
        InstanceScript* instance = GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GRAND_LIE, lit ? 1 : 0);
        handler->PSendSysMessage("Grand Lie is now {} (lit only on heroic, once wave 2 is bound, while Balnazzar "
            "neither fights nor is dead).", instance->GetData(DATA_GRAND_LIE) ? "lit" : "off");
        return true;
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",      HandleInstanceBoss,      SEC_GAMEMASTER, Console::No },
            { "where",     HandleInstanceWhere,     SEC_GAMEMASTER, Console::No },
            { "ziggurat",  HandleInstanceZiggurat,  SEC_GAMEMASTER, Console::No },
            { "baronrun",  HandleInstanceBaronRun,  SEC_GAMEMASTER, Console::No },
            { "clock",     HandleInstanceClock,     SEC_GAMEMASTER, Console::No },
            { "ultimatum", HandleInstanceUltimatum, SEC_GAMEMASTER, Console::No },
            { "grandlie",  HandleInstanceGrandLie,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_strat_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapStratholme;
    shell.dungeonName = "Stratholme";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        uint32 const pending = instance->GetData(DATA_ZIGGURAT_PENDING);
        handler->PSendSysMessage("Baron Run {} ({} min left); ziggurats {}{} / {}{} / {}{}; slaughter: {}",
            instance->GetData(DATA_BARON_RUN) ? "started" : "not started", instance->GetData(DATA_BARON_RUN_MINUTES),
            instance->GetData(DATA_ZIGGURAT1), (pending & 1u) ? "p" : "", instance->GetData(DATA_ZIGGURAT2),
            (pending & 2u) ? "p" : "", instance->GetData(DATA_ZIGGURAT3), (pending & 4u) ? "p" : "",
            SlaughterStageName(instance->GetData(DATA_SLAUGHTER_STAGE)));
        handler->PSendSysMessage("Ultimatum {} (kill {}); Grand Lie {} (kill {}); postboxes {}; wave 2 {}",
            instance->GetData(DATA_ULTIMATUM), DungeonTest::StateName(instance->GetBossState(BOSS_ULTIMATUM)),
            instance->GetData(DATA_GRAND_LIE), DungeonTest::StateName(instance->GetBossState(BOSS_GRAND_LIE)),
            instance->GetData(DATA_MALLOW), kWave2Bound ? "bound" : "stock");
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    StratTest::RegisterBoss("instance", InstanceTestCommands());
}
