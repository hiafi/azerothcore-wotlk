/*
 * mod-dungeon-bosses, Blackrock Depths: the `.dbtest brd` command shell (BlackrockDepthsTestCommand.h) and WP-S0's own
 * subcommands:
 *
 *   .dbtest brd section <1-4>                  teleport to a Finder section's start (handoff section 3.8) and list the
 *                                              doors on its path with their states
 *   .dbtest brd instance boss <id> <state>     set a boss state (0 NOT_STARTED, 1 IN_PROGRESS, 3 DONE ...) past the
 *                                              stock-collision guard: doors, the Vault, the hard mode kills
 *   .dbtest brd instance where                 which Blackrock Depths arenas hold the GM's position (the playtest's
 *                                              .gps checks) and which section it belongs to
 *   .dbtest brd instance ring                  the Ring's saved rolls (Sentence, wave type, the champion pair), Favor
 *   .dbtest brd instance favor <0-10>          Crowd Favor (D4's meter)
 *   .dbtest brd instance banner <0|1>          the banner thrown (heroic, the Ring not DONE; saved)
 *   .dbtest brd instance burn <0|1>            the banner burned: the Encore armed (heroic, thrown; saved)
 *   .dbtest brd instance vault                 the Dark Coffer's trigger (needs Stilgiss and Verek DONE)
 *   .dbtest brd instance vaultreset            end the Vault attempt (the wipe reset)
 *   .dbtest brd instance clock <s>             the Vault's finishing time and the Safe it gives
 *   .dbtest brd instance rope <1|2>            the Guzzler rope: dropped, placed (one way only)
 *   .dbtest brd instance cinder <0|1>          the Cinder used: Lord of the Lake armed (heroic, Incendius idle)
 *   .dbtest brd instance console <0|1>         the Activation Console (heroic, wave 2 bound, Argelmach idle)
 *   .dbtest brd instance avatar <0|1>          Ragnaros Awakens (heroic, wave 2 bound, Dagran fighting)
 */

#include "BlackrockDepthsTestCommand.h"
#include "BlackrockDepthsRework.h"
#include "Chat.h"
#include "Creature.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "Player.h"
#include "StringFormat.h"
#include <string>
#include <utility>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;

namespace BrdTest
{
    InstanceScript* GmInstance(ChatHandler* handler)
    {
        if (!RequireBlackrockDepths(handler))
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

    bool HandleSection(ChatHandler* handler, uint32 number)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        FinderSection const* section = SectionByNumber(number);
        if (!section)
        {
            handler->SendErrorMessage("Usage: .dbtest brd section <1-4>");
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
            GameObject* door = gm->FindNearestGameObject(entry, 2000.f);
            if (door)
                handler->PSendSysMessage("  door {} {}: {} at ({:.1f}, {:.1f}, {:.1f})", entry, door->GetName(),
                    GoStateName(door->GetGoState()), door->GetPositionX(), door->GetPositionY(),
                    door->GetPositionZ());
            else
                handler->PSendSysMessage("  door {}: not loaded (its grid is not active)", entry);
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

    bool HandleInstanceBoss(ChatHandler* handler, uint32 id, uint32 state)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        // TO_BE_DECIDED (5) is the loading state: a slot set to it skips the next change's save and switch.
        if (id >= kBossCount || state >= TO_BE_DECIDED)
        {
            handler->SendErrorMessage("Usage: .dbtest brd instance boss <0..{}> <0..4>", kBossCount - 1);
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
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Vec2 const p{ gm->GetPositionX(), gm->GetPositionY() };
        float const z = gm->GetPositionZ();
        bool any = false;
        for (uint32 id = 0; id < kBossCount; ++id)
        {
            if (IsHardModeSlot(id) || id == BOSS_RIBBLY || id == BOSS_PLUGGER || id == BOSS_VAULT)
                continue;       // the same arena as another slot
            if (ArenaFor(id).Contains(p, z))
            {
                handler->PSendSysMessage("inside: {} arena (section {})", kBossNames[id], SectionOf(id));
                any = true;
            }
        }
        handler->PSendSysMessage("({:.1f}, {:.1f}, {:.1f}){}", p.x, p.y, z,
            any ? "" : ": in no Blackrock Depths arena");
        return true;
    }

    std::string RingLine(InstanceScript const* instance)
    {
        uint32 const first = instance->GetData(DATA_RING_FIRST);
        uint32 const second = instance->GetData(DATA_RING_SECOND);
        uint32 const wave = instance->GetData(DATA_RING_WAVE);
        return Acore::StringFormat("Ring: sentence {}, wave {} ({}), champions {} then {} ({} then {}), Favor {}; "
            "banner thrown {}, burned {}", instance->GetData(DATA_RING_SENTENCE) + 1, wave + 1,
            kRingWaveMobs[wave % kRingWaveTypes], first + 1, second + 1, kRingChampions[first % kRingChampionCount],
            kRingChampions[second % kRingChampionCount], instance->GetData(DATA_RING_FAVOR),
            instance->GetData(DATA_BANNER_THROWN), instance->GetData(DATA_BANNER_BURNED));
    }

    bool HandleInstanceRing(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        handler->PSendSysMessage("{}", RingLine(instance));
        return true;
    }

    // A flag write through the instance's own rules, then the value it holds.
    bool SetAndShow(ChatHandler* handler, uint32 data, uint32 value, char const* name, char const* rule)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(data, value);
        handler->PSendSysMessage("{} is now {} ({}).", name, instance->GetData(data), rule);
        return true;
    }

    bool HandleInstanceFavor(ChatHandler* handler, uint32 favor)
    {
        return SetAndShow(handler, DATA_RING_FAVOR, favor, "Crowd Favor", "0-10, per attempt");
    }

    bool HandleInstanceBanner(ChatHandler* handler, uint32 lit)
    {
        return SetAndShow(handler, DATA_BANNER_THROWN, lit ? 1 : 0, "Banner thrown",
            "heroic, the Ring not DONE; saved");
    }

    bool HandleInstanceBurn(ChatHandler* handler, uint32 lit)
    {
        return SetAndShow(handler, DATA_BANNER_BURNED, lit ? 1 : 0, "Banner burned (the Encore)",
            "heroic, the banner thrown, the Ring not DONE; saved");
    }

    bool HandleInstanceVault(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_VAULT_TRIGGER, 1);
        handler->PSendSysMessage("Vault trigger sent: the Vault is {} (it starts only from NOT_STARTED with Stilgiss "
            "and Verek DONE: {}).", DungeonTest::StateName(instance->GetData(TYPE_VAULT)),
            DungeonTest::StateName(instance->GetBossState(BOSS_STILGISS_VEREK)));
        return true;
    }

    bool HandleInstanceVaultReset(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_VAULT_RESET, 1);
        handler->PSendSysMessage("Vault reset sent: the Vault is {}.",
            DungeonTest::StateName(instance->GetData(TYPE_VAULT)));
        return true;
    }

    // Section 10: the Ring gallery's stand-down for a section 2 start (stands it down now, then shows the flags).
    bool HandleInstanceGallery(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GALLERY_STOOD_DOWN, 1);
        handler->PSendSysMessage("Gallery stood down {}; Encore running {}, won {}; Doomgrip's item {}.",
            instance->GetData(DATA_GALLERY_STOOD_DOWN), instance->GetData(DATA_ENCORE_RUNNING),
            instance->GetData(DATA_ENCORE_WON), instance->GetData(DATA_VAULT_DOOMGRIP_ITEM));
        return true;
    }

    bool HandleInstanceClock(ChatHandler* handler, uint32 seconds)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_VAULT_CLOCK, seconds);
        VaultSafe const safe = VaultSafeFor(instance->GetData(DATA_VAULT_CLOCK));
        handler->PSendSysMessage("Vault clock {} s: the Safe holds the Cinder {}, gear {}, {} bag(s).",
            instance->GetData(DATA_VAULT_CLOCK), safe.cinder ? "yes" : "no", safe.gear ? "yes" : "no", safe.bags);
        return true;
    }

    bool HandleInstanceRope(ChatHandler* handler, uint32 rope)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_GUZZLER_ROPE, rope);
        handler->PSendSysMessage("Guzzler rope: {} (1 dropped, 2 placed; one way only; saved).",
            RopeStateName(instance->GetData(DATA_GUZZLER_ROPE)));
        return true;
    }

    bool HandleInstanceCinder(ChatHandler* handler, uint32 lit)
    {
        return SetAndShow(handler, DATA_CINDER_USED, lit ? 1 : 0, "Cinder used (Lord of the Lake)",
            "heroic, Incendius neither fighting nor dead; saved until the kill");
    }

    bool HandleInstanceConsole(ChatHandler* handler, uint32 lit)
    {
        return SetAndShow(handler, DATA_CONSOLE_ARMED, lit ? 1 : 0, "Activation Console (the Prototype)",
            "heroic, wave 2 bound, Argelmach neither fighting nor dead; per pull");
    }

    bool HandleInstanceAvatar(ChatHandler* handler, uint32 lit)
    {
        return SetAndShow(handler, DATA_AVATAR, lit ? 1 : 0, "Ragnaros Awakens (the Avatar)",
            "heroic, wave 2 bound, Dagran fighting; per pull");
    }

    ChatCommandTable const& InstanceTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "boss",       HandleInstanceBoss,         SEC_GAMEMASTER, Console::No },
            { "where",      HandleInstanceWhere,        SEC_GAMEMASTER, Console::No },
            { "ring",       HandleInstanceRing,         SEC_GAMEMASTER, Console::No },
            { "favor",      HandleInstanceFavor,        SEC_GAMEMASTER, Console::No },
            { "banner",     HandleInstanceBanner,       SEC_GAMEMASTER, Console::No },
            { "burn",       HandleInstanceBurn,         SEC_GAMEMASTER, Console::No },
            { "vault",      HandleInstanceVault,        SEC_GAMEMASTER, Console::No },
            { "vaultreset", HandleInstanceVaultReset,   SEC_GAMEMASTER, Console::No },
            { "clock",      HandleInstanceClock,        SEC_GAMEMASTER, Console::No },
            { "gallery",    HandleInstanceGallery,      SEC_GAMEMASTER, Console::No },
            { "rope",       HandleInstanceRope,         SEC_GAMEMASTER, Console::No },
            { "cinder",     HandleInstanceCinder,       SEC_GAMEMASTER, Console::No },
            { "console",    HandleInstanceConsole,      SEC_GAMEMASTER, Console::No },
            { "avatar",     HandleInstanceAvatar,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

// Called from the loader after the boss files (the order does not matter: the tables are built when the command map
// loads, after every script's AddSC_).
void AddSC_dungeon_bosses_brd_commandscript()
{
    DungeonTest::DungeonShell shell;
    shell.command = kTestCommand;
    shell.mapId = kMapBlackrockDepths;
    shell.dungeonName = "Blackrock Depths";
    shell.bossNames.assign(kBossNames.begin(), kBossNames.end());
    shell.printState = [](ChatHandler* handler, InstanceScript const* instance)
    {
        handler->PSendSysMessage("stock mirrors: ring of law {}, vault {}, bar {} (ales: SPECIAL at 3), tomb {}, "
            "lyceum {}, iron hall {}", DungeonTest::StateName(instance->GetData(TYPE_RING_OF_LAW)),
            DungeonTest::StateName(instance->GetData(TYPE_VAULT)), DungeonTest::StateName(instance->GetData(TYPE_BAR)),
            DungeonTest::StateName(instance->GetData(TYPE_TOMB_OF_SEVEN)),
            DungeonTest::StateName(instance->GetData(TYPE_LYCEUM)),
            DungeonTest::StateName(instance->GetData(TYPE_IRON_HALL)));
        handler->PSendSysMessage("{}", RingLine(instance));
        VaultSafe const safe = VaultSafeFor(instance->GetData(DATA_VAULT_CLOCK));
        handler->PSendSysMessage("vault clock {} s (Safe: Cinder {}, gear {}, bags {}); coffer doors opened {}; "
            "rope {}; cinder {}; console {}; avatar {}; moira saved {}", instance->GetData(DATA_VAULT_CLOCK),
            safe.cinder ? 1 : 0, safe.gear ? 1 : 0, safe.bags, instance->GetData(DATA_COFFER_DOORS_OPENED),
            RopeStateName(instance->GetData(DATA_GUZZLER_ROPE)), instance->GetData(DATA_CINDER_USED),
            instance->GetData(DATA_CONSOLE_ARMED), instance->GetData(DATA_AVATAR), instance->GetData(DATA_MOIRA_SAVED));
        handler->PSendSysMessage("phalanx activated {}, love potion {}; wave 2 {}",
            DungeonTest::StateName(instance->GetData(DATA_PHALANX_ACTIVATED)),
            DungeonTest::StateName(instance->GetData(DATA_LOVE_POTION_EVENT)), kWave2Bound ? "bound" : "stock");
    };
    DungeonTest::RegisterDungeon(std::move(shell));
    BrdTest::RegisterBoss("instance", InstanceTestCommands());
    BrdTest::RegisterBoss("section", SectionTestCommands());
}
