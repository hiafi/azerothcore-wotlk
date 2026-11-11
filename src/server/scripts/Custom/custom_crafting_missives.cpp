/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// Custom: crafting rework C4, Missives (.agents/plans/crafting-rework/crafting-rework.PLAN.md "C4 rulings").
//
// Crafted gear whose secondaries come from its random suffix (item_itemization.secondary_shape_id 0, so
// ItemBudget::GetSuffixFactor is nonzero) rolls a stat pair from its pool (item_template.RandomSuffix) at creation,
// like any suffix item. A Missive (an Inscription consumable) puts a 24 h buff on the player; the next such piece he
// crafts takes the buff's stat plus a random partner, drawn from the pairs of the item's pool that contain the stat,
// and the buff goes. A Missive whose stat has no pair in that pool stays active (ruling F1). One Missive at a time:
// using a second while one is active is refused and the item is not spent.
//
// Data: the buff spells are the spells bound to `spell_crafting_missive` in spell_script_names, and each buff's
// EffectMiscValue_1 is its ItemMod stat (apps/dbc-tools/source/world/crafting_suffixes.py declares both). A suffix's
// stat pair is read from its ItemRandomSuffix row's enchants (each a stat enchant).
//
// The suffix is set from OnPlayerStoreNewItem, not OnPlayerCreateItem: Spell::DoCreateItem sends the "You create:"
// item push (SendNewItem) before OnPlayerCreateItem, so the chat link would show the random roll. The hook has no spell
// context, so it is gated on the player's generic spell being a trade skill recipe that creates this item and is
// executing right now. Every craft of "Create All" is its own cast and passes through here once per item; only the
// first piece that qualifies spends the buff, and consumables (no budget-sized suffix) never do.

#include "Chat.h"
#include "CommandScript.h"
#include "Containers.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "Item.h"
#include "ItemBudget.h"
#include "ItemEnchantmentMgr.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "QueryResult.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringConvert.h"
#include "StringFormat.h"
#include "WorldSession.h"
#include <algorithm>
#include <map>
#include <set>
#include <sstream>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
    constexpr char const* MissiveScriptName = "spell_crafting_missive";
    constexpr uint32 DefaultRolls = 1000;
    constexpr uint32 MaxRolls = 100000;

    struct SuffixPair
    {
        uint32 suffixId = 0;
        uint32 statA = 0;
        uint32 statB = 0;

        bool Has(uint32 stat) const { return statA == stat || statB == stat; }
    };

    // Built once at startup (OnStartup: the DBC stores, spell_script_names, item templates and the itemization budget
    // are all loaded by then) and read-only after, so the map threads can read it without a lock.
    struct MissiveData
    {
        std::map<uint32, uint32> missiveStat;                       // buff spell -> ItemMod stat
        std::unordered_map<uint32, std::vector<SuffixPair>> pools;  // item_enchantment_template entry -> pairs
    };

    MissiveData Data;

    char const* StatName(uint32 stat)
    {
        switch (stat)
        {
            case ITEM_MOD_CRIT_RATING:        return "Critical Strike Rating";
            case ITEM_MOD_HASTE_RATING:       return "Haste Rating";
            case ITEM_MOD_MASTERY_RATING:     return "Mastery Rating";
            case ITEM_MOD_VERSATILITY_RATING: return "Versatility Rating";
            case ITEM_MOD_COOLDOWN_RATING:    return "Cooldown Haste Rating";
            case ITEM_MOD_PROC_RATING:        return "Proc Chance Rating";
            case ITEM_MOD_BLOCK_RATING:       return "Block Rating";
            case ITEM_MOD_DODGE_RATING:       return "Dodge Rating";
            case ITEM_MOD_PARRY_RATING:       return "Parry Rating";
            default:                          return "an unknown stat";
        }
    }

    std::string SpellName(uint32 spellId)
    {
        SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
        return info ? info->SpellName[0] : Acore::StringFormat("spell {}", spellId);
    }

    // The suffix's stats, in part order, from its stat enchants. Empty if a part is not a single stat.
    std::vector<uint32> SuffixStats(ItemRandomSuffixEntry const* suffix)
    {
        std::vector<uint32> stats;
        for (uint32 enchantId : suffix->Enchantment)
        {
            if (!enchantId)
                continue;

            SpellItemEnchantmentEntry const* enchant = sSpellItemEnchantmentStore.LookupEntry(enchantId);
            if (!enchant || enchant->type[0] != ITEM_ENCHANTMENT_TYPE_STAT)
                return { };

            stats.push_back(enchant->spellid[0]);
        }
        return stats;
    }

    void LoadMissiveSpells(MissiveData& data)
    {
        QueryResult result = WorldDatabase.Query("SELECT spell_id FROM spell_script_names WHERE ScriptName = '{}'",
            MissiveScriptName);
        if (!result)
            return;

        do
        {
            uint32 const spellId = result->Fetch()[0].Get<int32>();
            SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId);
            if (!info)
            {
                LOG_ERROR("server.loading", "Crafting Missives: spell {} is bound to {} but does not exist", spellId,
                    MissiveScriptName);
                continue;
            }

            SpellEffectInfo const& effect = info->GetEffect(EFFECT_0);
            if (effect.Effect != SPELL_EFFECT_APPLY_AURA || effect.ApplyAuraName != SPELL_AURA_DUMMY ||
                effect.MiscValue <= 0 || effect.MiscValue >= MAX_ITEM_MOD)
            {
                LOG_ERROR("server.loading", "Crafting Missives: spell {} ({}) needs a dummy aura in effect 0 "
                    "whose misc value is the ItemMod stat it picks; skipped", spellId, info->SpellName[0]);
                continue;
            }

            data.missiveStat[spellId] = uint32(effect.MiscValue);
        } while (result->NextRow());
    }

    // The pools of every item whose suffix carries its secondaries, as stat pairs.
    void LoadPools(MissiveData& data)
    {
        std::set<uint32> entries;
        for (auto const& [itemId, proto] : *sObjectMgr->GetItemTemplateStore())
            if (proto.RandomSuffix && ItemBudget::GetSuffixFactor(itemId))
                entries.insert(proto.RandomSuffix);

        if (entries.empty())
            return;

        std::ostringstream list;
        for (uint32 entry : entries)
            list << (list.tellp() > 0 ? "," : "") << entry;

        QueryResult result = WorldDatabase.Query(
            "SELECT entry, ench FROM item_enchantment_template WHERE entry IN ({})", list.str());
        if (!result)
            return;

        do
        {
            Field* fields = result->Fetch();
            uint32 const entry = fields[0].Get<uint32>();
            uint32 const suffixId = fields[1].Get<uint32>();

            ItemRandomSuffixEntry const* suffix = sItemRandomSuffixStore.LookupEntry(suffixId);
            std::vector<uint32> const stats = suffix ? SuffixStats(suffix) : std::vector<uint32>();
            if (stats.size() != 2)
            {
                LOG_ERROR("server.loading", "Crafting Missives: pool {} suffix {} is not a pair of stat enchants; "
                    "Missives never pick it", entry, suffixId);
                continue;
            }

            data.pools[entry].push_back({ suffixId, stats[0], stats[1] });
        } while (result->NextRow());
    }

    void LoadData()
    {
        MissiveData data;
        LoadMissiveSpells(data);
        LoadPools(data);

        std::size_t pairs = 0;
        for (auto const& [entry, poolPairs] : data.pools)
            pairs += poolPairs.size();

        LOG_INFO("server.loading", ">> Crafting Missives: {} Missive buff(s), {} suffix pool(s) with {} pair(s)",
            data.missiveStat.size(), data.pools.size(), pairs);
        Data = std::move(data);
    }

    std::vector<SuffixPair> const* PoolPairs(ItemTemplate const* proto)
    {
        auto itr = Data.pools.find(proto->RandomSuffix);
        return itr != Data.pools.end() ? &itr->second : nullptr;
    }

    uint32 ActiveMissive(Unit const* unit)
    {
        for (auto const& [spellId, stat] : Data.missiveStat)
            if (unit->HasAura(spellId))
                return spellId;
        return 0;
    }

    // The pairs of `pairs` a Missive of `stat` may give.
    std::vector<SuffixPair> MissivePairs(std::vector<SuffixPair> const& pairs, uint32 stat)
    {
        std::vector<SuffixPair> fitting;
        for (SuffixPair const& pair : pairs)
            if (pair.Has(stat))
                fitting.push_back(pair);
        return fitting;
    }

    // True while the player's current trade skill recipe that creates `itemId` executes (Spell::_cast sets the spell
    // non-interruptable for exactly that span), so loot, mail, vendors and quest rewards never spend a Missive.
    bool IsCraftingNow(Player* player, uint32 itemId)
    {
        Spell* spell = player->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        if (!spell || spell->IsInterruptable())
            return false;

        SpellInfo const* info = spell->GetSpellInfo();
        if (!info->HasAttribute(SPELL_ATTR0_IS_TRADESKILL))
            return false;

        for (SpellEffectInfo const& effect : info->GetEffects())
            if (effect.Effect == SPELL_EFFECT_CREATE_ITEM && effect.ItemType == itemId)
                return true;
        return false;
    }

    std::string ItemLink(Item const* item)
    {
        ItemTemplate const* proto = item->GetTemplate();
        std::string name = proto->Name1;
        int32 const randomId = item->GetItemRandomPropertyId();
        if (randomId < 0)
            if (ItemRandomSuffixEntry const* suffix = sItemRandomSuffixStore.LookupEntry(-randomId))
                name = Acore::StringFormat("{} {}", name, suffix->Name[0]);

        return Acore::StringFormat("|c{:08x}|Hitem:{}:0:0:0:0:0:{}:{}:0|h[{}]|h|r", ItemQualityColors[proto->Quality],
            proto->ItemId, randomId, item->GetItemSuffixFactor(), name);
    }
}

class spell_crafting_missive : public SpellScript
{
    PrepareSpellScript(spell_crafting_missive);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        uint32 const active = caster ? ActiveMissive(caster) : 0;
        if (!active)
            return SPELL_CAST_OK;

        if (Player* player = caster->ToPlayer())
            ChatHandler(player->GetSession()).SendNotification(Acore::StringFormat(
                "{} is still active: craft a piece first, or cancel it.", SpellName(active)));
        return SPELL_FAILED_DONT_REPORT;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_crafting_missive::CheckCast);
    }
};

class Custom_CraftingMissivesWorld : public WorldScript
{
public:
    Custom_CraftingMissivesWorld() : WorldScript("Custom_CraftingMissivesWorld", { WORLDHOOK_ON_STARTUP }) { }

    void OnStartup() override
    {
        LoadData();
    }
};

class Custom_CraftingMissivesPlayer : public PlayerScript
{
public:
    Custom_CraftingMissivesPlayer() : PlayerScript("Custom_CraftingMissivesPlayer",
        { PLAYERHOOK_ON_STORE_NEW_ITEM }) { }

    void OnPlayerStoreNewItem(Player* player, Item* item, uint32 /*count*/) override
    {
        if (!item || Data.missiveStat.empty())
            return;

        ItemTemplate const* proto = item->GetTemplate();
        if (!proto->RandomSuffix || !ItemBudget::GetSuffixFactor(proto->ItemId))
            return;

        uint32 const missive = ActiveMissive(player);
        if (!missive || !IsCraftingNow(player, proto->ItemId))
            return;

        std::vector<SuffixPair> const* pairs = PoolPairs(proto);
        uint32 const stat = Data.missiveStat.at(missive);
        std::vector<SuffixPair> const fitting = pairs ? MissivePairs(*pairs, stat) : std::vector<SuffixPair>();
        ChatHandler chat(player->GetSession());
        if (fitting.empty())
        {
            chat.PSendSysMessage("{} does not fit {}: it has no {} pairing. Its stats are random, and the "
                "Missive stays active.", SpellName(missive), ItemLink(item), StatName(stat));
            return;
        }

        SuffixPair const& pick = Acore::Containers::SelectRandomContainerElement(fitting);
        item->SetItemRandomProperties(-int32(pick.suffixId));
        player->RemoveAurasDueToSpell(missive);
        chat.PSendSysMessage("{} shapes {}.", SpellName(missive), ItemLink(item));
    }
};

class Custom_CraftingMissivesCommands : public CommandScript
{
public:
    Custom_CraftingMissivesCommands() : CommandScript("Custom_CraftingMissivesCommands") { }

    ChatCommandTable GetCommands() const override
    {
        // Test commands (crafting rework C4).
        static ChatCommandTable missiveCommandTable =
        {
            { "roll", HandleRollCommand, SEC_GAMEMASTER, Console::Yes },
            { "info", HandleInfoCommand, SEC_GAMEMASTER, Console::Yes },
        };
        static ChatCommandTable commandTable =
        {
            { "missive", missiveCommandTable },
        };
        return commandTable;
    }

    // A stat by ItemMod number or name (crit, haste, mastery, versatility, cooldown, proc, block, dodge, parry).
    static uint32 ParseStat(std::string const& text)
    {
        static std::map<std::string, uint32> const names =
        {
            { "crit", ITEM_MOD_CRIT_RATING }, { "haste", ITEM_MOD_HASTE_RATING },
            { "mastery", ITEM_MOD_MASTERY_RATING }, { "versatility", ITEM_MOD_VERSATILITY_RATING },
            { "vers", ITEM_MOD_VERSATILITY_RATING }, { "cooldown", ITEM_MOD_COOLDOWN_RATING },
            { "cdh", ITEM_MOD_COOLDOWN_RATING }, { "proc", ITEM_MOD_PROC_RATING },
            { "block", ITEM_MOD_BLOCK_RATING }, { "dodge", ITEM_MOD_DODGE_RATING }, { "parry", ITEM_MOD_PARRY_RATING },
        };
        if (auto itr = names.find(text); itr != names.end())
            return itr->second;
        return Acore::StringTo<uint32>(text).value_or(0);
    }

    static std::string SuffixLabel(uint32 suffixId)
    {
        ItemRandomSuffixEntry const* suffix = sItemRandomSuffixStore.LookupEntry(suffixId);
        return Acore::StringFormat("{} '{}'", suffixId, suffix ? suffix->Name[0] : "?");
    }

    // .missive info <item>: the item's pool, suffix factor and the amount each pair grants.
    static bool HandleInfoCommand(ChatHandler* handler, uint32 itemId)
    {
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(itemId);
        if (!proto)
        {
            handler->SendErrorMessage("Item {} does not exist.", itemId);
            return false;
        }

        uint32 const factor = GenerateEnchSuffixFactor(itemId);
        handler->PSendSysMessage("{} ({}): ilvl {}, quality {}, pool {}, suffix factor {} ({}), budget-sized {}.",
            proto->Name1, itemId, proto->ItemLevel, proto->Quality, proto->RandomSuffix, factor,
            ItemBudget::GetSuffixFactor(itemId) ? "from the item budget" : "RandPropPoints",
            ItemBudget::GetSuffixFactor(itemId) ? "yes" : "no");

        std::vector<SuffixPair> const* pairs = PoolPairs(proto);
        if (!pairs)
        {
            handler->PSendSysMessage("  no Missive pool (not a budget-sized suffix item, or the pool has no pairs).");
            return true;
        }

        for (SuffixPair const& pair : *pairs)
        {
            ItemRandomSuffixEntry const* suffix = sItemRandomSuffixStore.LookupEntry(pair.suffixId);
            handler->PSendSysMessage("  {}: +{} {}, +{} {}", SuffixLabel(pair.suffixId),
                suffix ? suffix->AllocationPct[0] * factor / 10000 : 0, StatName(pair.statA),
                suffix ? suffix->AllocationPct[1] * factor / 10000 : 0, StatName(pair.statB));
        }

        handler->PSendSysMessage("  Missive buffs: {}", Data.missiveStat.size());
        return true;
    }

    // .missive roll <item> [count] [stat]: rolls the item's suffix `count` times as a craft would, with no Missive
    // (the engine's own pool roll) or with a Missive of `stat` (the script's pick), and reports the distribution.
    static bool HandleRollCommand(ChatHandler* handler, uint32 itemId, Optional<uint32> countArg,
        Optional<std::string> statArg)
    {
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(itemId);
        if (!proto || !proto->RandomSuffix)
        {
            handler->SendErrorMessage("Item {} does not exist or has no RandomSuffix pool.", itemId);
            return false;
        }

        uint32 const count = std::clamp<uint32>(countArg.value_or(DefaultRolls), 1, MaxRolls);
        uint32 const stat = statArg ? ParseStat(*statArg) : 0;
        if (statArg && !stat)
        {
            handler->SendErrorMessage("Unknown stat '{}'.", *statArg);
            return false;
        }

        std::vector<SuffixPair> fitting;
        if (stat)
        {
            std::vector<SuffixPair> const* pairs = PoolPairs(proto);
            fitting = pairs ? MissivePairs(*pairs, stat) : std::vector<SuffixPair>();
            if (fitting.empty())
            {
                handler->PSendSysMessage("A Missive of {} does not fit {} (pool {}): the craft would roll at "
                    "random and keep the buff.", StatName(stat), proto->Name1, proto->RandomSuffix);
                return true;
            }
        }

        // A pool with no rows logs an error at every roll: try one first.
        if (!stat && !GetItemEnchantMod(proto->RandomSuffix))
        {
            handler->SendErrorMessage("Pool {} rolled nothing: it has no item_enchantment_template rows.",
                proto->RandomSuffix);
            return false;
        }

        std::map<uint32, uint32> tally;
        for (uint32 i = 0; i < count; ++i)
        {
            uint32 const suffixId = stat ? Acore::Containers::SelectRandomContainerElement(fitting).suffixId :
                GetItemEnchantMod(proto->RandomSuffix);
            ++tally[suffixId];
        }

        handler->PSendSysMessage("{} ({}), pool {}, {} rolls, {}:", proto->Name1, itemId, proto->RandomSuffix, count,
            stat ? Acore::StringFormat("Missive of {}", StatName(stat)) : std::string("no Missive"));
        for (auto const& [suffixId, times] : tally)
            handler->PSendSysMessage("  {}: {} ({:.1f}%)", SuffixLabel(suffixId), times, 100.0 * times / count);
        return true;
    }
};

void AddSC_custom_crafting_missives()
{
    RegisterSpellScript(spell_crafting_missive);
    new Custom_CraftingMissivesWorld();
    new Custom_CraftingMissivesPlayer();
    new Custom_CraftingMissivesCommands();
}
