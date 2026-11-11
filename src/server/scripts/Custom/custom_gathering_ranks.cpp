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

// Custom: gathering ranks (crafting rework C3, .agents/plans/crafting-rework/crafting-rework.PLAN.md, DESIGN R14,
// R20, R38, R40).
//
// One rank track (0-5) per material. A material is the main item of a gathering loot: a mining or herb node
// (gameobject_loot_template of a chest whose lock needs Mining or Herbalism) or a skinning loot
// (skinning_loot_template of a creature skinned with Skinning, Herbalism or Mining; Engineering salvage and gas
// clouds, Extract Gas, are left out).
//
// - Main material: the loot's non-quest item entry with the highest chance, above the rare threshold. An entry
//   reaches it either directly or through a reference that always drops (chance 100, not grouped; one level). A
//   tie goes to the ungrouped entry, then to the lower item id. A main that does not stack is no main. A loot
//   without one has no rank track: quest gathering (Root Sample nodes), Clam nodes, Loque'nahak's Pelt.
//     Copper Vein: Copper Ore (100%, 1-4). Thorium: Thorium Ore. Black Lotus: Black Lotus. Skinning a beast whose
//     loot is one group of leathers: the most likely leather (Rugged Leather 40% over Thick Leather 27%).
// - Rare extras: every other non-quest item entry of the loot with a chance from 0 (exclusive) to
//   Custom.Gathering.RareChanceThreshold (15%, inclusive), and every reference (gem tables) with a chance up to
//   Custom.Gathering.RareReferenceThreshold. Item entries with conditions are left out. A reference counts only
//   through its "marker" items, the ones no other entry of the loot gives; a reference with no marker (Knothide
//   Leather's bonus reference) is left out.
//     Copper Vein: Malachite, Tigerseye, Shadowgem (5% each). Thorium: the gem reference (15%; 25% on Rich).
//     Felweed: Fel Lotus (2%). Purple Lotus: Wildvine, Bloodvine (15%). Rugged Leather beasts: Rugged Hide, Thick
//     Hide, Worn Dragonscale.
//
// On each gather by a player with a client (playerbots and other client-less players are skipped: no bonus, no
// rows), at the gatherer's rank r in the loot's material:
// - R20: the main material's count is rolled again, uniformly in [min + floor(r / 2), max + r] (min + 0.5 per rank,
//   max + 1 per rank, floored), replacing the loot's own roll. A 1-3 node gives 1-4 at rank 1 and 3-8 at rank 5.
// - R38/R40: each rare extra that did not drop gets an extra roll of (b * m - b) / (1 - b), b its base chance
//   (with the drop rates), m = 1 + 0.2 * r, so its total chance is b * m: rank 5 doubles it.
// - Then the rank-up roll: Custom.Gathering.RankUpChances, one chance per rank 0-4 (20/10/5/2.5/1.25%).
//
// Hook: MiscScript::OnAfterLootTemplateProcess, which Loot::FillLoot calls once per loot generation, right after
// the template rolled and before the loot reaches anyone. Reopening a node's or a skinned corpse's loot window does
// not generate the loot again, so it can neither roll again nor add items twice: no guard is needed, and the
// gatherer (the player the loot is generated for) is the only one who counts, group or not. (The plan suggested
// OnPlayerBeforeSendLoot plus a guard; this hook does the same job without one.)
//
// Loot data: the hook only gets the LootTemplate pointer, so the gathering loots' rows are read from the world DB
// at startup and matched to the stores' templates by pointer (one hash lookup per gathering loot; a non-gathering
// chest or skin also checks every cached loot id against the store). After a `.reload` of a loot table the
// templates change; the next gameobject or skinning loot notices it and reads the rows again (also `.gathering
// reload`).
//
// Storage: characters table character_gathering_rank (guid, item_entry, skill, rank), loaded at login, written on
// each rank change, deleted with the character.
//
// Feedback: a chat line on rank-up, `.gathering ranks`, the Professions page (CPROF feed, rank field = best rank
// across the skill's materials, custom_professions.cpp), sent again on rank-up, and the Gathering Ranks window
// (every material with its rank, "G1" messages under the same prefix; see SendMaterialFeed). GM test commands:
// `.gathering setrank`, `.gathering sim`, `.gathering reload`.

#include "Chat.h"
#include "CommandScript.h"
#include "ConditionMgr.h"
#include "Config.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "DataMap.h"
#include "GameObject.h"
#include "Log.h"
#include "LootMgr.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "StringConvert.h"
#include "StringFormat.h"
#include "Tokenize.h"
#include "World.h"
#include "WorldSession.h"
#include "custom_crafting.h"
#include <algorithm>
#include <array>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
    uint8 constexpr MaxRank = 5;
    uint8 constexpr MaxReferenceDepth = 3;
    // `.gathering sim` runs on the GM's map thread, two passes (rank 0 and the asked rank) of up to 20,000 loot
    // generations each: a few microseconds per generation, so well under a second (estimate, not measured).
    uint32 constexpr MaxSimulatedGathers = 20000;
    uint32 constexpr DefaultSimulatedGathers = 5000;

    struct GatheringSettings
    {
        bool enabled = true;
        std::array<float, MaxRank> rankUpChance = { 20.0f, 10.0f, 5.0f, 2.5f, 1.25f };
        float rareThreshold = 15.0f;
        float rareReferenceThreshold = 25.0f;
    };

    GatheringSettings Settings;

    // --- Loot data ---

    enum class GatherSource : uint8
    {
        Gameobject,
        Skinning,
    };

    struct RareExtra
    {
        uint32 itemId = 0;            // 0 for a reference
        uint32 reference = 0;
        float chance = 0.0f;          // percent, before drop rates
        uint16 lootMode = 0;
        uint8 minCount = 1;           // item: count; reference: maxCount is the multiplier
        uint8 maxCount = 1;
        std::vector<uint32> markers;  // reference: the items that show it dropped
    };

    struct GatherTemplate
    {
        uint32 lootId = 0;
        GatherSource source = GatherSource::Gameobject;
        uint16 skillId = 0;
        uint32 mainItem = 0;
        uint8 mainMin = 1;
        uint8 mainMax = 1;
        float mainChance = 0.0f;
        uint32 mainReference = 0;     // reference the main comes through, 0 if direct
        std::vector<RareExtra> rares;
    };

    // A material: the gathering skill and the sort key the Gathering Ranks window orders it by (the median required
    // skill of its nodes, or the median skinning requirement of its beasts' levels).
    struct MaterialInfo
    {
        uint16 skillId = 0;
        uint32 sortKey = 0;
    };

    struct GatherCache
    {
        std::vector<GatherTemplate> templates;
        std::unordered_map<uint32, std::size_t> gameobjectIndex; // loot id -> templates index
        std::unordered_map<uint32, std::size_t> skinningIndex;
        std::unordered_map<LootTemplate const*, std::size_t> gameobjectByTemplate; // store template -> index
        std::unordered_map<LootTemplate const*, std::size_t> skinningByTemplate;
        std::unordered_map<uint32, MaterialInfo> materials;      // main item -> skill, sort key
    };

    std::shared_ptr<GatherCache const> Cache;
    std::mutex CacheMutex;   // guards the Cache pointer
    std::mutex RebuildMutex; // one rebuild at a time

    std::shared_ptr<GatherCache const> GetCache()
    {
        std::lock_guard<std::mutex> lock(CacheMutex);
        return Cache;
    }

    struct LootRow
    {
        uint32 item = 0;
        uint32 reference = 0;
        float chance = 0.0f;
        bool quest = false;
        uint16 lootMode = 0;
        uint8 group = 0;
        uint8 minCount = 1;
        uint8 maxCount = 1;
    };

    using RowMap = std::unordered_map<uint32, std::vector<LootRow>>;

    std::string JoinIds(std::vector<uint32> const& ids)
    {
        std::string out;
        for (uint32 id : ids)
        {
            if (!out.empty())
                out += ',';
            out += std::to_string(id);
        }
        return out;
    }

    RowMap LoadRows(char const* table, std::vector<uint32> const& ids)
    {
        RowMap rows;
        if (ids.empty())
            return rows;

        QueryResult result = WorldDatabase.Query("SELECT Entry, Item, Reference, Chance, QuestRequired, LootMode, "
            "GroupId, MinCount, MaxCount FROM {} WHERE Entry IN ({})", table, JoinIds(ids));
        if (!result)
            return rows;

        do
        {
            Field* fields = result->Fetch();
            LootRow row;
            row.item = fields[1].Get<uint32>();
            row.reference = std::abs(fields[2].Get<int32>());
            row.chance = fields[3].Get<float>();
            row.quest = fields[4].Get<bool>();
            row.lootMode = fields[5].Get<uint16>();
            row.group = fields[6].Get<uint8>();
            row.minCount = fields[7].Get<uint8>();
            row.maxCount = fields[8].Get<uint8>();
            rows[fields[0].Get<uint32>()].push_back(row);
        } while (result->NextRow());
        return rows;
    }

    // Chance of each row as a share of 100, per group: an explicit chance stands; equal-chanced rows (chance 0) of a
    // group share what the explicit ones leave.
    std::vector<float> EffectiveChances(std::vector<LootRow> const& rows)
    {
        std::map<uint8, std::pair<float, uint32>> groups; // group -> (explicit total, equal-chanced count)
        for (LootRow const& row : rows)
        {
            if (!row.group || row.quest || row.reference)
                continue;
            auto& [explicitTotal, equalCount] = groups[row.group];
            if (row.chance > 0.0f)
                explicitTotal += row.chance;
            else
                ++equalCount;
        }

        std::vector<float> chances;
        chances.reserve(rows.size());
        for (LootRow const& row : rows)
        {
            float chance = std::min(row.chance, 100.0f);
            if (row.group && !row.quest && !row.reference && row.chance <= 0.0f)
            {
                auto const& [explicitTotal, equalCount] = groups[row.group];
                chance = equalCount ? std::max(0.0f, 100.0f - explicitTotal) / float(equalCount) : 0.0f;
            }
            chances.push_back(chance);
        }
        return chances;
    }

    // Every item a reference can give, nested references included.
    void CollectReferenceItems(RowMap const& references, uint32 reference, std::unordered_set<uint32>& items,
        uint8 depth = 0)
    {
        auto itr = references.find(reference);
        if (itr == references.end() || depth > MaxReferenceDepth)
            return;

        for (LootRow const& row : itr->second)
        {
            if (row.reference)
                CollectReferenceItems(references, row.reference, items, depth + 1);
            else if (!row.quest)
                items.insert(row.item);
        }
    }

    // Builds the material and rare extras of one loot; false when it has no main material.
    bool BuildTemplate(GatherTemplate& tpl, std::vector<LootRow> const& rows, RowMap const& references)
    {
        std::vector<float> const chances = EffectiveChances(rows);

        // Main material candidates: direct item rows, and the ungrouped item rows of an always-dropping reference.
        struct Candidate
        {
            uint32 item;
            float chance;
            bool grouped;
            uint8 minCount;
            uint8 maxCount;
            uint32 reference;
        };

        std::vector<Candidate> candidates;
        for (std::size_t i = 0; i < rows.size(); ++i)
        {
            LootRow const& row = rows[i];
            if (row.quest)
                continue;

            if (!row.reference)
            {
                candidates.push_back({ row.item, chances[i], row.group != 0, row.minCount, row.maxCount, 0 });
                continue;
            }

            if (row.group || row.chance < 100.0f)
                continue;

            auto refItr = references.find(row.reference);
            if (refItr == references.end())
                continue;

            for (LootRow const& refRow : refItr->second)
                if (!refRow.reference && !refRow.quest && !refRow.group)
                    candidates.push_back({ refRow.item, std::min(refRow.chance, 100.0f), false, refRow.minCount,
                        refRow.maxCount, row.reference });
        }

        Candidate const* main = nullptr;
        for (Candidate const& candidate : candidates)
        {
            if (!main || candidate.chance > main->chance ||
                (candidate.chance == main->chance && (main->grouped && !candidate.grouped)) ||
                (candidate.chance == main->chance && main->grouped == candidate.grouped && candidate.item < main->item))
                main = &candidate;
        }

        // A main material that does not stack (Loque'nahak's Pelt) could never yield more: no track.
        ItemTemplate const* mainProto = main ? sObjectMgr->GetItemTemplate(main->item) : nullptr;
        if (!main || main->chance <= Settings.rareThreshold || !mainProto || mainProto->GetMaxStackSize() <= 1)
            return false;

        tpl.mainItem = main->item;
        tpl.mainMin = main->minCount;
        tpl.mainMax = std::max(main->minCount, main->maxCount);
        tpl.mainChance = main->chance;
        tpl.mainReference = main->reference;

        // Items any non-reference row of this loot gives: a reference showing one of them cannot be told apart.
        std::unordered_set<uint32> directItems = { tpl.mainItem };
        for (LootRow const& row : rows)
            if (!row.reference)
                directItems.insert(row.item);

        for (std::size_t i = 0; i < rows.size(); ++i)
        {
            LootRow const& row = rows[i];
            if (row.quest || chances[i] <= 0.0f || chances[i] >= 100.0f)
                continue;

            RareExtra rare;
            rare.chance = chances[i];
            rare.lootMode = row.lootMode;
            rare.minCount = row.minCount;
            rare.maxCount = std::max(row.minCount, row.maxCount);

            if (row.reference)
            {
                if (row.reference == tpl.mainReference || chances[i] > Settings.rareReferenceThreshold)
                    continue;

                std::unordered_set<uint32> items;
                CollectReferenceItems(references, row.reference, items);
                for (uint32 item : items)
                    if (!directItems.count(item))
                        rare.markers.push_back(item);

                if (rare.markers.empty())
                    continue;

                std::sort(rare.markers.begin(), rare.markers.end());
                rare.reference = row.reference;
                rare.maxCount = row.maxCount;
            }
            else
            {
                if (row.item == tpl.mainItem || chances[i] > Settings.rareThreshold ||
                    !sObjectMgr->GetItemTemplate(row.item))
                    continue;
                rare.itemId = row.item;
            }
            tpl.rares.push_back(std::move(rare));
        }
        return true;
    }

    // The gathering skill a lock needs (Herbalism or Mining, else SKILL_NONE) and the skill value it requires.
    std::pair<SkillType, uint32> GatheringSkillOfLock(uint32 lockId)
    {
        LockEntry const* lock = sLockStore.LookupEntry(lockId);
        if (!lock)
            return { SKILL_NONE, 0 };

        for (uint8 i = 0; i < MAX_LOCK_CASE; ++i)
        {
            if (lock->Type[i] != LOCK_KEY_SKILL)
                continue;
            if (lock->Index[i] == LOCKTYPE_HERBALISM)
                return { SKILL_HERBALISM, lock->Skill[i] };
            if (lock->Index[i] == LOCKTYPE_MINING)
                return { SKILL_MINING, lock->Skill[i] };
        }
        return { SKILL_NONE, 0 };
    }

    // The skill Spell::EffectSkinning asks of a creature of this level.
    uint32 SkinningRequirement(uint32 level)
    {
        return level < 10 ? 0 : level < 20 ? (level - 10) * 10 : level * 5;
    }

    // A gathering loot id: its skill and the requirement of every node or beast using it.
    struct LootSource
    {
        uint16 skillId = 0;
        std::vector<uint32> requirements;
    };

    uint32 Median(std::vector<uint32> values)
    {
        if (values.empty())
            return 0;
        std::nth_element(values.begin(), values.begin() + values.size() / 2, values.end());
        return values[values.size() / 2];
    }

    std::shared_ptr<GatherCache const> BuildCache()
    {
        // Loot ids, their gathering skill and requirements.
        std::map<uint32, LootSource> gameobjectLoots;
        for (auto const& [entry, goInfo] : *sObjectMgr->GetGameObjectTemplates())
        {
            if (goInfo.type != GAMEOBJECT_TYPE_CHEST || !goInfo.GetLootId())
                continue;
            auto const [skill, requirement] = GatheringSkillOfLock(goInfo.GetLockId());
            if (!skill)
                continue;
            LootSource& source = gameobjectLoots[goInfo.GetLootId()];
            if (!source.skillId)
                source.skillId = skill;
            source.requirements.push_back(requirement);
        }

        // Engineering salvage and gas clouds (Extract Gas, aura 30427 loots the cloud's skinning loot) are not
        // gathers: a loot id any of them uses is left out.
        std::map<uint32, LootSource> skinningLoots;
        std::unordered_set<uint32> excludedLoots;
        for (auto const& [entry, creatureInfo] : *sObjectMgr->GetCreatureTemplates())
        {
            if (!creatureInfo.SkinLootId)
                continue;
            SkillType const skill = creatureInfo.GetRequiredLootSkill();
            if (skill == SKILL_ENGINEERING || creatureInfo.type == CREATURE_TYPE_GAS_CLOUD)
            {
                excludedLoots.insert(creatureInfo.SkinLootId);
                continue;
            }
            LootSource& source = skinningLoots[creatureInfo.SkinLootId];
            if (!source.skillId)
                source.skillId = skill;
            source.requirements.push_back(SkinningRequirement(creatureInfo.minlevel));
        }
        for (uint32 lootId : excludedLoots)
            skinningLoots.erase(lootId);

        auto keys = [](std::map<uint32, LootSource> const& loots)
        {
            std::vector<uint32> ids;
            ids.reserve(loots.size());
            for (auto const& [id, source] : loots)
                ids.push_back(id);
            return ids;
        };

        RowMap const gameobjectRows = LoadRows("gameobject_loot_template", keys(gameobjectLoots));
        RowMap const skinningRows = LoadRows("skinning_loot_template", keys(skinningLoots));

        // References, nested ones included.
        RowMap references;
        std::vector<uint32> pending;
        for (RowMap const* rowMap : { &gameobjectRows, &skinningRows })
            for (auto const& [id, rows] : *rowMap)
                for (LootRow const& row : rows)
                    if (row.reference)
                        pending.push_back(row.reference);

        for (uint8 depth = 0; depth <= MaxReferenceDepth && !pending.empty(); ++depth)
        {
            std::sort(pending.begin(), pending.end());
            pending.erase(std::unique(pending.begin(), pending.end()), pending.end());
            pending.erase(std::remove_if(pending.begin(), pending.end(), [&references](uint32 id)
            {
                return references.count(id) != 0;
            }), pending.end());

            RowMap loaded = LoadRows("reference_loot_template", pending);
            pending.clear();
            for (auto& [id, rows] : loaded)
            {
                for (LootRow const& row : rows)
                    if (row.reference)
                        pending.push_back(row.reference);
                references.emplace(id, std::move(rows));
            }
        }

        // Loot item rows with conditions (source type, loot id, item): neither main material nor rare extra.
        std::set<std::tuple<uint32, uint32, uint32>> conditionedRows;
        uint32 constexpr GameobjectConditions = CONDITION_SOURCE_TYPE_GAMEOBJECT_LOOT_TEMPLATE;
        uint32 constexpr SkinningConditions = CONDITION_SOURCE_TYPE_SKINNING_LOOT_TEMPLATE;
        if (QueryResult result = WorldDatabase.Query("SELECT SourceTypeOrReferenceId, SourceGroup, SourceEntry FROM "
            "conditions WHERE SourceTypeOrReferenceId IN ({}, {})", GameobjectConditions, SkinningConditions))
        {
            do
            {
                Field* fields = result->Fetch();
                conditionedRows.emplace(fields[0].Get<uint32>(), fields[1].Get<uint32>(), fields[2].Get<uint32>());
            } while (result->NextRow());
        }

        auto cache = std::make_shared<GatherCache>();
        std::unordered_map<uint32, std::vector<uint32>> materialRequirements;
        auto addLoots = [&](GatherSource source, std::map<uint32, LootSource> const& loots, RowMap const& rowMap,
            LootStore const& store, std::unordered_map<uint32, std::size_t>& index,
            std::unordered_map<LootTemplate const*, std::size_t>& byTemplate)
        {
            uint32 const conditionSource = source == GatherSource::Gameobject ?
                CONDITION_SOURCE_TYPE_GAMEOBJECT_LOOT_TEMPLATE : CONDITION_SOURCE_TYPE_SKINNING_LOOT_TEMPLATE;

            for (auto const& [lootId, lootSource] : loots)
            {
                auto rowItr = rowMap.find(lootId);
                LootTemplate const* storeTemplate = store.GetLootFor(lootId);
                if (rowItr == rowMap.end() || !storeTemplate)
                    continue;

                // Drop the item rows that carry conditions before building (they are neither main nor rare).
                std::vector<LootRow> rows;
                for (LootRow const& row : rowItr->second)
                    if (row.reference || !conditionedRows.count({ conditionSource, lootId, row.item }))
                        rows.push_back(row);

                GatherTemplate tpl;
                tpl.lootId = lootId;
                tpl.source = source;
                tpl.skillId = lootSource.skillId;
                if (!BuildTemplate(tpl, rows, references))
                    continue;

                cache->materials.emplace(tpl.mainItem, MaterialInfo{ tpl.skillId, 0 });
                auto& requirements = materialRequirements[tpl.mainItem];
                requirements.insert(requirements.end(), lootSource.requirements.begin(),
                    lootSource.requirements.end());
                index.emplace(lootId, cache->templates.size());
                byTemplate.emplace(storeTemplate, cache->templates.size());
                cache->templates.push_back(std::move(tpl));
            }
        };

        addLoots(GatherSource::Gameobject, gameobjectLoots, gameobjectRows, LootTemplates_Gameobject,
            cache->gameobjectIndex, cache->gameobjectByTemplate);
        addLoots(GatherSource::Skinning, skinningLoots, skinningRows, LootTemplates_Skinning, cache->skinningIndex,
            cache->skinningByTemplate);

        for (auto& [itemId, material] : cache->materials)
            material.sortKey = Median(materialRequirements[itemId]);

        LOG_INFO("server.loading", ">> Gathering ranks: {} node loots and {} skinning loots have a material ({} "
            "materials)", cache->gameobjectIndex.size(), cache->skinningIndex.size(), cache->materials.size());
        return cache;
    }

    // `seen`: the stale cache the caller found. Several map threads can find it stale at once; only the first rebuilds,
    // the others see a newer cache once they get the lock. nullptr (commands, config reload) always rebuilds.
    void RebuildCache(GatherCache const* seen = nullptr)
    {
        std::lock_guard<std::mutex> rebuildLock(RebuildMutex);
        if (seen && GetCache().get() != seen)
            return;

        std::shared_ptr<GatherCache const> fresh = BuildCache();
        std::lock_guard<std::mutex> lock(CacheMutex);
        Cache = std::move(fresh);
    }

    LootStore const& StoreOf(GatherSource source)
    {
        return source == GatherSource::Gameobject ? LootTemplates_Gameobject : LootTemplates_Skinning;
    }

    // The cached loot `tab` is, or nullptr. Reads the rows again if the store's templates were reloaded.
    GatherTemplate const* FindTemplate(std::shared_ptr<GatherCache const>& cache, GatherSource source,
        LootTemplate const* tab, bool allowRebuild = true)
    {
        if (!cache)
            return nullptr;

        // A hit is checked against the store by loot id (a reloaded store can give an old address to another loot).
        // A miss is the common case (chests, other skins), but it is also what every gathering loot looks like after
        // a `.reload` of the table: on a miss every cached loot id is checked against the store, so a reload is seen
        // whatever addresses the allocator hands out. If every id still has its template, the cache maps them right.
        LootStore const& store = StoreOf(source);
        auto const& byTemplate = source == GatherSource::Gameobject ? cache->gameobjectByTemplate :
            cache->skinningByTemplate;
        auto itr = byTemplate.find(tab);
        bool stale = false;
        if (itr != byTemplate.end())
        {
            GatherTemplate const& tpl = cache->templates[itr->second];
            if (store.GetLootFor(tpl.lootId) == tab)
                return &tpl;
            stale = true;
        }
        else
        {
            stale = std::any_of(byTemplate.begin(), byTemplate.end(), [&](auto const& entry)
            {
                return store.GetLootFor(cache->templates[entry.second].lootId) != entry.first;
            });
        }

        // `.reload` gave the store new templates: the rows may have changed too. Read them once again.
        if (!stale || !allowRebuild)
            return nullptr;

        RebuildCache(cache.get());
        cache = GetCache();
        return FindTemplate(cache, source, tab, false);
    }

    GatherTemplate const* FindTemplateById(GatherCache const& cache, GatherSource source, uint32 lootId)
    {
        auto const& index = source == GatherSource::Gameobject ? cache.gameobjectIndex : cache.skinningIndex;
        auto itr = index.find(lootId);
        return itr != index.end() ? &cache.templates[itr->second] : nullptr;
    }

    // --- Rolls ---

    // Base chance of a rare extra as a share of 1, drop rates applied as LootStoreItem::Roll does.
    float BaseChance(RareExtra const& rare)
    {
        float rate = 1.0f;
        if (rare.reference)
            rate = sWorld->getRate(RATE_DROP_ITEM_REFERENCED);
        else if (ItemTemplate const* proto = sObjectMgr->GetItemTemplate(rare.itemId))
        {
            static std::array<ServerConfigs, 7> constexpr QualityRates =
            {
                RATE_DROP_ITEM_POOR, RATE_DROP_ITEM_NORMAL, RATE_DROP_ITEM_UNCOMMON, RATE_DROP_ITEM_RARE,
                RATE_DROP_ITEM_EPIC, RATE_DROP_ITEM_LEGENDARY, RATE_DROP_ITEM_ARTIFACT,
            };
            if (proto->Quality < QualityRates.size())
                rate = sWorld->getRate(QualityRates[proto->Quality]);
        }
        return std::min(1.0f, rare.chance * rate / 100.0f);
    }

    bool HasItem(Loot const& loot, uint32 itemId)
    {
        return std::any_of(loot.items.begin(), loot.items.end(), [itemId](LootItem const& item)
        {
            return item.itemid == itemId;
        });
    }

    bool RareDropped(Loot const& loot, RareExtra const& rare)
    {
        if (!rare.reference)
            return HasItem(loot, rare.itemId);

        return std::any_of(rare.markers.begin(), rare.markers.end(), [&loot](uint32 itemId)
        {
            return HasItem(loot, itemId);
        });
    }

    uint32 MainCount(Loot const& loot, uint32 itemId)
    {
        uint32 count = 0;
        for (LootItem const& item : loot.items)
            if (item.itemid == itemId)
                count += item.count;
        return count;
    }

    // R20 and R38/R40 at rank `rank` on a loot that was just generated.
    void ApplyRankBonus(Loot& loot, GatherTemplate const& tpl, LootStore const& store, uint16 lootMode,
        Player const* gatherer, uint8 rank)
    {
        if (!rank)
            return;

        // R20: the main material's count is rolled again, uniformly in the widened range (the loot's own roll is
        // replaced, so rank 1 on a 1-3 node is a plain 1-4). It is the sum over every stack of the main item (Pure
        // Saronite gives more than a stack); anything above the row's maximum came from another entry (Knothide's
        // bonus reference) and is kept on top. Existing stacks are refilled up to the stack size, each keeping at
        // least 1, and what is left goes in new stacks through AddItem.
        std::vector<LootItem*> stacks;
        uint32 rolled = 0;
        for (LootItem& item : loot.items)
        {
            if (item.itemid != tpl.mainItem || item.is_looted)
                continue;
            stacks.push_back(&item);
            rolled += item.count;
        }

        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(tpl.mainItem);
        if (!stacks.empty() && proto)
        {
            uint32 const maxStack = std::max<uint32>(1, proto->GetMaxStackSize());
            uint32 const extra = rolled > tpl.mainMax ? rolled - tpl.mainMax : 0;
            uint32 total = std::max<uint32>(urand(tpl.mainMin + rank / 2, tpl.mainMax + rank) + extra,
                uint32(stacks.size()));

            for (std::size_t i = 0; i < stacks.size(); ++i)
            {
                uint32 const stacksAfter = uint32(stacks.size() - i - 1);
                uint32 const count = std::min(maxStack, total - stacksAfter);
                stacks[i]->count = count;
                total -= count;
            }
            if (total)
                loot.AddItem(LootStoreItem(tpl.mainItem, 0, 100.0f, false, LOOT_MODE_DEFAULT, 0,
                    uint8(std::min<uint32>(total, 255)), uint8(std::min<uint32>(total, 255))));
        }

        // R38/R40: each rare extra that did not drop gets an extra roll up to base * (1 + 0.2 * rank). Whether
        // each dropped is read before anything is added.
        float const multiplier = 1.0f + 0.2f * rank;
        std::vector<bool> dropped;
        dropped.reserve(tpl.rares.size());
        for (RareExtra const& rare : tpl.rares)
            dropped.push_back(RareDropped(loot, rare));

        for (std::size_t i = 0; i < tpl.rares.size(); ++i)
        {
            RareExtra const& rare = tpl.rares[i];
            if (dropped[i] || !(rare.lootMode & lootMode))
                continue;

            float const base = BaseChance(rare);
            if (base <= 0.0f || base >= 1.0f)
                continue;

            float const extra = (std::min(1.0f, base * multiplier) - base) / (1.0f - base);
            if (!roll_chance_f(extra * 100.0f))
                continue;

            if (rare.reference)
            {
                LootTemplate const* referenced = LootTemplates_Reference.GetLootFor(rare.reference);
                if (!referenced)
                    continue;

                uint32 const times = uint32(float(rare.maxCount) * sWorld->getRate(RATE_DROP_ITEM_REFERENCED_AMOUNT));
                for (uint32 loop = 0; loop < times; ++loop)
                    referenced->Process(loot, store, lootMode, gatherer, 0, false);
            }
            else
                loot.AddItem(LootStoreItem(rare.itemId, 0, 100.0f, false, rare.lootMode, 0, rare.minCount,
                    rare.maxCount));
        }
    }

    // --- Player ranks ---

    std::string const RankStateKey = "Custom_GatheringRanks.Ranks";

    struct MaterialRank
    {
        uint16 skillId = 0;
        uint8 rank = 0;
    };

    struct RankState : public DataMap::Base
    {
        std::unordered_map<uint32, MaterialRank> ranks; // material item -> rank (rank 0 has no entry)
    };

    // Playerbots (and any other player without a client) gather without ranks.
    bool IsClientless(Player const* player)
    {
        WorldSession* session = player->GetSession();
        return !session || session->IsSocketClosed();
    }

    uint8 GetRank(Player const* player, uint32 itemId)
    {
        RankState const* state = player->CustomData.Get<RankState>(RankStateKey);
        if (!state)
            return 0;

        auto itr = state->ranks.find(itemId);
        return itr != state->ranks.end() ? itr->second.rank : 0;
    }

    std::string ItemName(uint32 itemId)
    {
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(itemId);
        return proto ? proto->Name1 : Acore::StringFormat("item {}", itemId);
    }

    // --- Gathering Ranks window feed (client/ui-overrides GatheringRanksFrame.lua) ---
    //
    // Under the CPROF prefix (custom_professions.cpp), whispered to the player himself:
    //     full list  "G1;<i>/<n>;<skill>,<item>,<rank>,<sort key>;..."   chunk i of n, in order
    //     one change "G1;U;<skill>,<item>,<rank>,<sort key>"
    // Every material of the cache, rank 0 included, ordered by skill, sort key, item. A chunk's body stays under
    // MaxFeedBody so the whole addon message keeps well under the client's 255-byte limit.

    std::size_t constexpr MaxFeedBody = 200;

    std::string MaterialEntry(uint32 itemId, MaterialInfo const& material, uint8 rank)
    {
        return Acore::StringFormat("{},{},{},{}", material.skillId, itemId, rank, material.sortKey);
    }

    void SendMaterialUpdate(Player* player, uint32 itemId, uint8 rank)
    {
        std::shared_ptr<GatherCache const> cache = GetCache();
        if (!cache)
            return;

        auto itr = cache->materials.find(itemId);
        if (itr != cache->materials.end())
            CustomProfessions::SendAddonMessage(player, "G1;U;" + MaterialEntry(itemId, itr->second, rank));
    }

    void SetRank(Player* player, uint32 itemId, uint16 skillId, uint8 rank, bool announce)
    {
        RankState* state = player->CustomData.GetDefault<RankState>(RankStateKey);
        CharacterDatabasePreparedStatement* stmt;
        if (rank)
        {
            state->ranks[itemId] = { skillId, rank };
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_REP_GATHERING_RANK);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, itemId);
            stmt->SetData(2, skillId);
            stmt->SetData(3, rank);
        }
        else
        {
            state->ranks.erase(itemId);
            stmt = CharacterDatabase.GetPreparedStatement(CHAR_DEL_GATHERING_RANK);
            stmt->SetData(0, player->GetGUID().GetCounter());
            stmt->SetData(1, itemId);
        }
        CharacterDatabase.Execute(stmt);

        if (announce)
            ChatHandler(player->GetSession()).PSendSysMessage("Your {} gathering rank is now {}.", ItemName(itemId),
                rank);

        SendMaterialUpdate(player, itemId, rank);
        CustomProfessions::QueueFeed(player);
    }

    // --- Simulation (.gathering sim) ---

    // While set (on this thread), the hook uses `rank` instead of the gatherer's and counts rank-ups here instead of
    // applying them.
    struct SimulationContext
    {
        uint8 rank = 0;
        uint32 rankUps = 0;
    };

    thread_local SimulationContext* ActiveSimulation = nullptr;
}

void CustomGathering::SendMaterialFeed(Player* player)
{
    std::shared_ptr<GatherCache const> cache = GetCache();
    if (!cache || IsClientless(player))
        return;

    std::vector<std::tuple<uint16, uint32, uint32>> order; // skill, sort key, item
    order.reserve(cache->materials.size());
    for (auto const& [itemId, material] : cache->materials)
        order.emplace_back(material.skillId, material.sortKey, itemId);
    std::sort(order.begin(), order.end());

    std::vector<std::string> chunks(1);
    for (auto const& [skillId, sortKey, itemId] : order)
    {
        std::string const entry = MaterialEntry(itemId, cache->materials.at(itemId), GetRank(player, itemId));
        if (!chunks.back().empty() && chunks.back().size() + entry.size() + 1 > MaxFeedBody)
            chunks.emplace_back();
        chunks.back() += ';' + entry;
    }

    for (std::size_t i = 0; i < chunks.size(); ++i)
        CustomProfessions::SendAddonMessage(player, Acore::StringFormat("G1;{}/{}{}", i + 1, chunks.size(),
            chunks[i]));
}

uint8 CustomGathering::GetBestRank(Player const* player, uint32 skillId)
{
    uint8 best = 0;
    if (RankState const* state = player->CustomData.Get<RankState>(RankStateKey))
        for (auto const& [itemId, material] : state->ranks)
            if (material.skillId == skillId)
                best = std::max(best, material.rank);
    return best;
}

class Custom_GatheringRanksWorld : public WorldScript
{
public:
    Custom_GatheringRanksWorld() : WorldScript("Custom_GatheringRanksWorld",
        { WORLDHOOK_ON_AFTER_CONFIG_LOAD, WORLDHOOK_ON_STARTUP }) { }

    void OnAfterConfigLoad(bool reload) override
    {
        Settings.enabled = sConfigMgr->GetOption<bool>("Custom.Gathering.Enable", true);

        float const threshold = sConfigMgr->GetOption<float>("Custom.Gathering.RareChanceThreshold", 15.0f);
        Settings.rareThreshold = std::clamp(threshold, 0.0f, 100.0f);
        float const referenceThreshold = sConfigMgr->GetOption<float>("Custom.Gathering.RareReferenceThreshold",
            25.0f);
        Settings.rareReferenceThreshold = std::clamp(referenceThreshold, 0.0f, 100.0f);

        std::string const chances = sConfigMgr->GetOption<std::string>("Custom.Gathering.RankUpChances",
            "20 10 5 2.5 1.25");
        std::vector<std::string_view> const tokens = Acore::Tokenize(chances, ' ', false);
        std::array<float, MaxRank> parsed = { };
        bool valid = tokens.size() == MaxRank;
        for (std::size_t i = 0; valid && i < MaxRank; ++i)
        {
            Optional<float> value = Acore::StringTo<float>(tokens[i]);
            valid = value && *value >= 0.0f && *value <= 100.0f;
            if (valid)
                parsed[i] = *value;
        }

        if (valid)
            Settings.rankUpChance = parsed;
        else
            LOG_ERROR("server.loading", "Custom.Gathering.RankUpChances = \"{}\" is not {} chances from 0 to 100 "
                "separated by spaces; keeping the previous ones", chances, MaxRank);

        // The thresholds pick the materials and rare extras: `.reload config` reads the loot rows again. At startup
        // OnStartup does it, once the loot templates are loaded.
        if (reload)
            RebuildCache();
    }

    // Loot templates, gameobject and creature templates and Lock.dbc are all loaded by now.
    void OnStartup() override
    {
        RebuildCache();
    }
};

class Custom_GatheringRanksLoot : public MiscScript
{
public:
    Custom_GatheringRanksLoot() : MiscScript("Custom_GatheringRanksLoot",
        { MISCHOOK_ON_AFTER_LOOT_TEMPLATE_PROCESS }) { }

    // Called once per loot generation (Loot::FillLoot), before the loot is sent or shared.
    void OnAfterLootTemplateProcess(Loot* loot, LootTemplate const* tab, LootStore const& store, Player* gatherer,
        bool /*personal*/, bool /*noEmptyError*/, uint16 lootMode) override
    {
        if (!Settings.enabled || !loot || !tab || !gatherer)
            return;

        GatherSource source;
        if (&store == &LootTemplates_Gameobject)
            source = GatherSource::Gameobject;
        else if (&store == &LootTemplates_Skinning)
            source = GatherSource::Skinning;
        else
            return;

        SimulationContext* simulation = ActiveSimulation;
        if (!simulation && IsClientless(gatherer))
            return;

        std::shared_ptr<GatherCache const> cache = GetCache();
        GatherTemplate const* tpl = FindTemplate(cache, source, tab);
        if (!tpl)
            return;

        uint8 const rank = simulation ? simulation->rank : GetRank(gatherer, tpl->mainItem);
        ApplyRankBonus(*loot, *tpl, store, lootMode, gatherer, rank);

        if (rank >= MaxRank || !roll_chance_f(Settings.rankUpChance[rank]))
            return;

        if (simulation)
            ++simulation->rankUps;
        else
            SetRank(gatherer, tpl->mainItem, tpl->skillId, rank + 1, true);
    }
};

class Custom_GatheringRanksPlayer : public PlayerScript
{
public:
    Custom_GatheringRanksPlayer() : PlayerScript("Custom_GatheringRanksPlayer",
        { PLAYERHOOK_ON_LOAD_FROM_DB, PLAYERHOOK_ON_DELETE_FROM_DB }) { }

    void OnPlayerLoadFromDB(Player* player) override
    {
        if (IsClientless(player))
            return;

        CharacterDatabasePreparedStatement* stmt = CharacterDatabase.GetPreparedStatement(CHAR_SEL_GATHERING_RANKS);
        stmt->SetData(0, player->GetGUID().GetCounter());
        PreparedQueryResult result = CharacterDatabase.Query(stmt);
        if (!result)
            return;

        RankState* state = player->CustomData.GetDefault<RankState>(RankStateKey);
        do
        {
            Field* fields = result->Fetch();
            uint8 const rank = std::min(fields[2].Get<uint8>(), MaxRank);
            if (rank)
                state->ranks[fields[0].Get<uint32>()] = { fields[1].Get<uint16>(), rank };
        } while (result->NextRow());
    }

    void OnPlayerDeleteFromDB(CharacterDatabaseTransaction trans, uint32 guid) override
    {
        CharacterDatabasePreparedStatement* stmt = CharacterDatabase.GetPreparedStatement(CHAR_DEL_GATHERING_RANKS);
        stmt->SetData(0, guid);
        trans->Append(stmt);
    }
};

class Custom_GatheringRanksCommands : public CommandScript
{
public:
    Custom_GatheringRanksCommands() : CommandScript("Custom_GatheringRanksCommands") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable gatheringCommandTable =
        {
            { "ranks",   HandleRanksCommand,   SEC_PLAYER,     Console::No },
            // Test commands (crafting rework C3), removable.
            { "setrank", HandleSetRankCommand, SEC_GAMEMASTER, Console::No },
            { "sim",     HandleSimCommand,     SEC_GAMEMASTER, Console::No },
            { "reload",  HandleReloadCommand,  SEC_GAMEMASTER, Console::Yes },
        };
        static ChatCommandTable commandTable =
        {
            { "gathering", gatheringCommandTable },
        };
        return commandTable;
    }

    static char const* SkillName(uint16 skillId)
    {
        switch (skillId)
        {
            case SKILL_HERBALISM: return "Herbalism";
            case SKILL_MINING:    return "Mining";
            case SKILL_SKINNING:  return "Skinning";
            default:              return "Other";
        }
    }

    // A GM sees his target's ranks; a player his own.
    static bool HandleRanksCommand(ChatHandler* handler)
    {
        Player* player = handler->GetPlayer();
        if (handler->GetSession()->GetSecurity() >= SEC_GAMEMASTER)
            if (Player* target = handler->getSelectedPlayerOrSelf())
                player = target;

        RankState const* state = player->CustomData.Get<RankState>(RankStateKey);
        if (!state || state->ranks.empty())
        {
            handler->PSendSysMessage("{} has no gathering ranks yet. Every gather of a material can raise its rank "
                "(up to {}).", player->GetName(), MaxRank);
            return true;
        }

        std::vector<std::tuple<std::string, std::string, uint8>> lines;
        for (auto const& [itemId, material] : state->ranks)
            lines.emplace_back(SkillName(material.skillId), ItemName(itemId), material.rank);
        std::sort(lines.begin(), lines.end());

        handler->PSendSysMessage("Gathering ranks of {}:", player->GetName());
        for (auto const& [skill, item, rank] : lines)
            handler->PSendSysMessage("  {} - {}: {}/{}", skill, item, rank, MaxRank);
        return true;
    }

    static bool HandleSetRankCommand(ChatHandler* handler, uint32 itemId, uint8 rank)
    {
        Player* player = handler->getSelectedPlayerOrSelf();
        if (!player)
            return false;

        if (IsClientless(player))
        {
            handler->SendErrorMessage("{} has no client (playerbot): bots have no gathering ranks.",
                player->GetName());
            return false;
        }

        std::shared_ptr<GatherCache const> cache = GetCache();
        uint16 skillId = 0;
        if (cache)
            if (auto itr = cache->materials.find(itemId); itr != cache->materials.end())
                skillId = itr->second.skillId;

        if (!skillId)
        {
            handler->SendErrorMessage("Item {} is not the material of any gathering loot.", itemId);
            return false;
        }

        rank = std::min(rank, MaxRank);
        SetRank(player, itemId, skillId, rank, false);
        handler->PSendSysMessage("{}'s {} gathering rank set to {}.", player->GetName(), ItemName(itemId), rank);
        return true;
    }

    static bool HandleReloadCommand(ChatHandler* handler)
    {
        RebuildCache();
        handler->SendGlobalGMSysMessage("Gathering rank loot data reloaded.");
        return true;
    }

    struct SimulationTally
    {
        uint32 gathers = 0;
        uint32 rankUps = 0;
        uint64 mainTotal = 0;
        uint32 mainMin = std::numeric_limits<uint32>::max();
        uint32 mainMax = 0;
        std::map<uint32, uint32> mainCounts;  // count -> gathers
        std::vector<uint32> rareDrops;
    };

    static SimulationTally Simulate(Player* player, GatherTemplate const& tpl, uint8 rank, uint32 gathers)
    {
        SimulationTally tally;
        tally.rareDrops.assign(tpl.rares.size(), 0);

        SimulationContext context;
        context.rank = rank;
        ActiveSimulation = &context;

        Loot loot;
        for (uint32 i = 0; i < gathers; ++i)
        {
            loot.clear();
            loot.FillLoot(tpl.lootId, StoreOf(tpl.source), player, true, true, LOOT_MODE_DEFAULT);

            uint32 const count = MainCount(loot, tpl.mainItem);
            if (count)
            {
                tally.mainTotal += count;
                tally.mainMin = std::min(tally.mainMin, count);
                tally.mainMax = std::max(tally.mainMax, count);
            }
            ++tally.mainCounts[count];

            for (std::size_t r = 0; r < tpl.rares.size(); ++r)
                if (RareDropped(loot, tpl.rares[r]))
                    ++tally.rareDrops[r];
        }
        loot.clear();

        ActiveSimulation = nullptr;
        tally.gathers = gathers;
        tally.rankUps = context.rankUps;
        return tally;
    }

    static std::string Percent(uint32 part, uint32 whole)
    {
        return Acore::StringFormat("{:.2f}%", whole ? 100.0 * part / whole : 0.0);
    }

    // .gathering sim <gameobject|skinning> <loot id> <rank> [gathers]: generates the loot `gathers` times at rank 0
    // and at `rank` (nothing is given, no rank changes) and compares the main material's count, each rare extra's
    // rate and the rank-up rate with what they should be.
    static bool HandleSimCommand(ChatHandler* handler, std::string source, uint32 lootId, uint8 rank,
        Optional<uint32> gathersArg)
    {
        Player* player = handler->GetPlayer();
        GatherSource gatherSource;
        if (source == "gameobject" || source == "go" || source == "node")
            gatherSource = GatherSource::Gameobject;
        else if (source == "skinning" || source == "skin")
            gatherSource = GatherSource::Skinning;
        else
        {
            handler->SendErrorMessage("Source must be gameobject or skinning.");
            return false;
        }

        std::shared_ptr<GatherCache const> cache = GetCache();
        GatherTemplate const* tpl = cache ? FindTemplateById(*cache, gatherSource, lootId) : nullptr;
        if (!tpl)
        {
            handler->SendErrorMessage("{} loot {} is not a gathering loot with a material.", source, lootId);
            return false;
        }

        if (!Settings.enabled)
            handler->PSendSysMessage("Custom.Gathering.Enable is 0: no bonus will show.");

        rank = std::min(rank, MaxRank);
        uint32 const gathers = std::clamp<uint32>(gathersArg.value_or(DefaultSimulatedGathers), 1, MaxSimulatedGathers);

        SimulationTally const base = Simulate(player, *tpl, 0, gathers);
        SimulationTally const ranked = Simulate(player, *tpl, rank, gathers);

        handler->PSendSysMessage("Sim {} loot {}: {} ({}), {} gathers at rank 0 and rank {}.", source, lootId,
            ItemName(tpl->mainItem), SkillName(tpl->skillId), gathers, rank);

        auto mainLine = [&](char const* label, SimulationTally const& tally, uint32 low, uint32 high)
        {
            uint32 const withMain = gathers - (tally.mainCounts.count(0) ? tally.mainCounts.at(0) : 0);
            std::string histogram;
            for (auto const& [count, times] : tally.mainCounts)
                histogram += Acore::StringFormat(" {}:{}", count, times);
            handler->PSendSysMessage("  {} main: avg {:.2f} when it drops ({} of {}), seen {}-{}, rule {}-{}; "
                "counts{}", label, withMain ? double(tally.mainTotal) / withMain : 0.0, withMain, gathers,
                withMain ? tally.mainMin : 0, tally.mainMax, low, high, histogram);
        };
        mainLine("rank 0", base, tpl->mainMin, tpl->mainMax);
        mainLine(Acore::StringFormat("rank {}", rank).c_str(), ranked, tpl->mainMin + rank / 2, tpl->mainMax + rank);

        float const multiplier = 1.0f + 0.2f * rank;
        for (std::size_t r = 0; r < tpl->rares.size(); ++r)
        {
            RareExtra const& rare = tpl->rares[r];
            std::string const name = rare.reference ? Acore::StringFormat("reference {} ({} markers)", rare.reference,
                rare.markers.size()) : ItemName(rare.itemId);
            float const chance = BaseChance(rare) * 100.0f;
            handler->PSendSysMessage("  rare {}: rank 0 {} (base {:.2f}%), rank {} {} (expected {:.2f}%), ratio {:.2f}",
                name, Percent(base.rareDrops[r], gathers), chance, rank, Percent(ranked.rareDrops[r], gathers),
                std::min(100.0f, chance * multiplier), base.rareDrops[r] ?
                double(ranked.rareDrops[r]) / base.rareDrops[r] : 0.0);
        }
        if (tpl->rares.empty())
            handler->PSendSysMessage("  no rare extras");

        if (rank < MaxRank)
            handler->PSendSysMessage("  rank-up at rank {}: {} of {} = {} (table {:.2f}%); at rank 0: {} (table "
                "{:.2f}%)", rank, ranked.rankUps, gathers, Percent(ranked.rankUps, gathers),
                Settings.rankUpChance[rank], Percent(base.rankUps, gathers), Settings.rankUpChance[0]);
        else
            handler->PSendSysMessage("  rank {} is the top: {} rank-ups (must be 0); at rank 0: {} (table {:.2f}%)",
                rank, ranked.rankUps, Percent(base.rankUps, gathers), Settings.rankUpChance[0]);
        return true;
    }
};

void AddSC_custom_gathering_ranks()
{
    new Custom_GatheringRanksWorld();
    new Custom_GatheringRanksLoot();
    new Custom_GatheringRanksPlayer();
    new Custom_GatheringRanksCommands();
}
