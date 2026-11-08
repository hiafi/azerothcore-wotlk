/*
 * mod-dungeon-bosses, Shadowfang Keep: Arugal's hard mode "Face Him Alone" (WP-S10, heroic only). Build spec: SK
 * 1491-1511 (hard mode), SK 1515-1524 and 1645 (lines, gossip); handoff section 3.6 row S10.
 *
 * The whole path, and who owns each step:
 *   1. The gossip (this file): the lair prisoner (S9's npc_sfk_lair_prisoner, LairPrisoner.h) shows "Stay behind. We
 *      will face Arugal alone." on heroic while FaceHimAlone::CanChoose allows it: not chosen yet, Arugal neither
 *      fighting nor dead, the prisoner waiting by the lair door. A confirmation box guards the click.
 *   2. The choice (this file): instance->SetData(DATA_HARD_MODE, 1), then SfkLairPrisoner::LeaveForHardMode (S9: line
 *      7, Ashcrombe teleports out with 6422, Adamant walks off; both despawn). Every player in the instance is told.
 *   3. The flag (the instance, WP-K): saved; a reload keeps it and despawns a re-summoned prisoner (S9); only an
 *      instance reset clears it. While it is lit Arugal carries LOOT_MODE_HARD_MODE_1 (re-applied on every boss state
 *      change, so BossAI::_Reset's ResetLootMode is undone by the engage's IN_PROGRESS).
 *   4. The fight (S9): no ward of any kind (`ward-skipped hardmode`), so only interrupted Void Bolts keep the tank's
 *      meter down; every heroic number holds, Moonrise and its +2 per second included.
 *   5. The kill (the instance + WP-L): Unit::Kill rolls his heroic lootid 310051 with loot mode 3, so group 2
 *      (LootMode 2, the three hard mode items) rolls once on top of his heroic item; his DONE sets BOSS_FACE_HIM_ALONE
 *      (DATA_HARD_MODE_KILLED). A normal-mode kill rolls 4275's own lootid, which has no LootMode 2 row.
 *
 * `.sfktest hardmode info | choose | roll [mode] [count]` (below) checks each step in game.
 */

#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "FaceHimAloneLogic.h"
#include "InstanceScript.h"
#include "LairPrisoner.h"
#include "LootMgr.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedGossip.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "StringFormat.h"
#include <algorithm>
#include <map>
#include <string>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace FaceHimAlone;

// The pure header mirrors these engine values.
static_assert(kOptionSender == GOSSIP_SENDER_MAIN, "FaceHimAlone::kOptionSender");
static_assert(kOptionAction == uint32(GOSSIP_ACTION_INFO_DEF) + uint32(DATA_HARD_MODE), "FaceHimAlone::kOptionAction");
static_assert(kLootModeDefault == LOOT_MODE_DEFAULT && kLootModeHardMode == LOOT_MODE_HARD_MODE_1, "loot modes");
static_assert(uint8(Encounter::NotStarted) == NOT_STARTED && uint8(Encounter::InProgress) == IN_PROGRESS
    && uint8(Encounter::Fail) == FAIL && uint8(Encounter::Done) == DONE && uint8(Encounter::Special) == SPECIAL
    && uint8(Encounter::ToBeDecided) == TO_BE_DECIDED, "FaceHimAlone::Encounter mirrors EncounterState");

namespace
{
    char constexpr kLogBoss[] = "hardmode";

    Creature* LairPrisonerOf(InstanceScript* instance, WorldObject const* near)
    {
        if (!instance || !near)
            return nullptr;
        return ObjectAccessor::GetCreature(*near, instance->GetGuidData(DATA_LAIR_PRISONER_GUID));
    }

    // The choice rule's inputs from the live objects.
    ChoiceInputs Inputs(Player const* player, Creature const* prisoner)
    {
        ChoiceInputs in;
        InstanceScript* instance = player ? player->GetInstanceScript()
            : prisoner ? prisoner->GetInstanceScript() : nullptr;
        in.instance = instance != nullptr;
        in.heroic = DungeonKit::IsHeroicMap(player ? static_cast<WorldObject const*>(player) : prisoner);
        in.lairPrisoner = SfkLairPrisoner::IsLairPrisoner(prisoner);
        // S9 removes the gossip flag when the prisoner steps in on the pull or leaves, and sets it back on a wipe.
        in.prisonerWaiting = prisoner && prisoner->IsAlive() && prisoner->HasNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        in.playerAlive = player && player->IsAlive();
        if (!instance)
            return in;
        in.chosen = instance->GetData(DATA_HARD_MODE) != 0;
        in.arugal = static_cast<Encounter>(instance->GetBossState(BOSS_ARUGAL));
        if (Creature const* arugal = instance->GetCreature(DATA_ARUGAL_GUID))
            in.arugalFighting = arugal->IsAlive() && (arugal->IsInCombat() || arugal->IsInEvadeMode());
        return in;
    }

    void TellInstance(Map* map, std::string const& text)
    {
        if (!map)
            return;
        map->DoForAllPlayers([&text](Player* p)
        {
            ChatHandler(p->GetSession()).SendSysMessage(text);
        });
    }

    // The choice itself (the gossip's select and `.sfktest hardmode choose`). Returns the refusal (None = chosen).
    Refusal Choose(Player* player, Creature* prisoner)
    {
        Refusal const refusal = CanChoose(Inputs(player, prisoner));
        if (refusal != Refusal::None)
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "refused", Acore::StringFormat("reason={} player={}",
                RefusalName(refusal), player ? player->GetName() : "?"));
            return refusal;
        }
        InstanceScript* instance = prisoner->GetInstanceScript();
        instance->SetData(DATA_HARD_MODE, 1);
        if (!instance->GetData(DATA_HARD_MODE))
        {
            // The instance refused (Arugal DONE in between): nothing changes.
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "refused", "reason=instance");
            return Refusal::ArugalDead;
        }
        bool const left = SfkLairPrisoner::LeaveForHardMode(prisoner);
        TellInstance(prisoner->GetMap(), Acore::StringFormat("{} has chosen to face Archmage Arugal alone: no wards in "
            "his fight (hard mode).", player->GetName()));
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "chosen", Acore::StringFormat("player={} prisoner={} left={}",
            player->GetName(), prisoner->GetEntry(), left ? 1 : 0));
        return Refusal::None;
    }

    void OnHello(Player* player, Creature* prisoner)
    {
        if (Offered(Inputs(player, prisoner)))
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, kOptionText, kOptionSender, kOptionAction, kConfirmText, 0,
                false);
    }

    bool OnSelect(Player* player, Creature* prisoner, uint32 sender, uint32 action)
    {
        if (sender != kOptionSender || action != kOptionAction)
            return false;
        Refusal const refusal = Choose(player, prisoner);
        CloseGossipMenuFor(player);
        if (refusal != Refusal::None)
            if (char const* notice = Notice(refusal); notice && *notice)
                ChatHandler(player->GetSession()).SendSysMessage(notice);
        return true;
    }

    // ---- .sfktest hardmode ------------------------------------------------------------------------------------------

    InstanceScript* RequireInstance(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return nullptr;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
            handler->SendErrorMessage("No instance script on this map.");
        return instance;
    }

    // The flag, the kill flag, Arugal's state and loot mode against the rule, the prisoner and the choice verdict.
    bool HandleInfo(ChatHandler* handler)
    {
        InstanceScript* instance = RequireInstance(handler);
        if (!instance)
            return false;
        Player* gm = handler->GetPlayer();
        bool const chosen = instance->GetData(DATA_HARD_MODE) != 0;
        EncounterState const state = instance->GetBossState(BOSS_ARUGAL);
        handler->PSendSysMessage("Face Him Alone: chosen {}, kill flag {}, heroic map {}, Arugal state {}",
            chosen ? 1 : 0, instance->GetData(DATA_HARD_MODE_KILLED), DungeonKit::IsHeroicMap(gm) ? "yes" : "no",
            uint32(state));
        if (Creature* arugal = instance->GetCreature(DATA_ARUGAL_GUID))
        {
            uint16 const expected = KillLootMode(chosen, state == DONE);
            handler->PSendSysMessage("Arugal: entry {} template {} lootid {}, loot mode {} (expected {}), group {} "
                "rolls {}, alive {}, in combat {}", arugal->GetEntry(), arugal->GetCreatureTemplate()->Entry,
                arugal->GetCreatureTemplate()->lootid, arugal->GetLootMode(), expected, kHardModeLootGroup,
                RowRolls(kLootModeHardMode, arugal->GetLootMode()) ? "yes" : "no", arugal->IsAlive() ? 1 : 0,
                arugal->IsInCombat() ? 1 : 0);
        }
        else
            handler->PSendSysMessage("Arugal: not loaded");
        Creature* prisoner = LairPrisonerOf(instance, gm);
        if (prisoner)
            handler->PSendSysMessage("Lair prisoner: entry {}, gossip flag {}", prisoner->GetEntry(),
                prisoner->HasNpcFlag(UNIT_NPC_FLAG_GOSSIP) ? 1 : 0);
        else
            handler->PSendSysMessage("Lair prisoner: none (not summoned, or gone for the hard mode)");
        handler->PSendSysMessage("Choice for you now: {}", RefusalName(CanChoose(Inputs(gm, prisoner))));
        return true;
    }

    // The gossip's select as the GM, through the same rule (no menu needed).
    bool HandleChoose(ChatHandler* handler)
    {
        InstanceScript* instance = RequireInstance(handler);
        if (!instance)
            return false;
        Player* gm = handler->GetPlayer();
        Creature* prisoner = LairPrisonerOf(instance, gm);
        Refusal const refusal = Choose(gm, prisoner);
        handler->PSendSysMessage("Face Him Alone: {}", refusal == Refusal::None ? "chosen" : RefusalName(refusal));
        return refusal == Refusal::None;
    }

    // Rolls Arugal's own lootid `count` times with loot mode `mode` (default: his current one) into a scratch loot
    // and lists every item and how often it dropped: mode 1 and mode 3 side by side show the hard mode group.
    bool HandleRoll(ChatHandler* handler, Optional<uint32> mode, Optional<uint32> count)
    {
        Creature* arugal = SfkTest::FindBoss(handler, NPC_ARUGAL);
        if (!arugal)
            return false;
        uint32 const lootId = arugal->GetCreatureTemplate()->lootid;
        uint16 const lootMode = uint16(mode.value_or(arugal->GetLootMode()));
        uint32 const rolls = std::min<uint32>(count.value_or(100), 1000);
        if (!lootId || !LootTemplates_Creature.HaveLootFor(lootId))
        {
            handler->SendErrorMessage("Arugal's lootid {} has no loot rows.", lootId);
            return false;
        }
        std::map<uint32, uint32> drops;
        for (uint32 i = 0; i < rolls; ++i)
        {
            Loot loot;
            loot.FillLoot(lootId, LootTemplates_Creature, handler->GetPlayer(), true, true, lootMode, arugal);
            for (LootItem const& item : loot.items)
                ++drops[item.itemid];
        }
        handler->PSendSysMessage("lootid {} mode {}: {} rolls", lootId, lootMode, rolls);
        for (auto const& [itemId, n] : drops)
            handler->PSendSysMessage("  item {}: {}", itemId, n);
        return true;
    }

    ChatCommandTable const& FaceHimAloneTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "choose", HandleChoose, SEC_GAMEMASTER, Console::No },
            { "roll", HandleRoll, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sfk_face_him_alone()
{
    SfkLairPrisoner::SetGossipHooks({ OnHello, OnSelect });
    SfkTest::RegisterBoss("hardmode", FaceHimAloneTestCommands());
}
