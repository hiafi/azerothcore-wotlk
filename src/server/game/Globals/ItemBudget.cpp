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

#include "ItemBudget.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "ObjectMgr.h"
#include "QueryResult.h"
#include "Timer.h"
#include <algorithm>
#include <cmath>
#include <map>
#include <numeric>
#include <unordered_map>

namespace
{
    struct TemplateStat
    {
        uint32 StatType = 0;
        uint32 Alloc = 0; // ten-thousandths
    };

    struct AssignRow
    {
        uint32 TemplateId = 0;
        float BudgetMult = 1.0f;
        int32 StaminaDelta = 0;
        float DpsDelta = 0.0f;
        uint32 AbsorbedSpellSlots = 0; // bitmask, bit i = clear Spells[i] at materialization
        int32 ArmorDelta = 0;          // raw armor points, +/- -- NOT funded from budget, see §9.3
    };

    struct StatCostRow
    {
        float Cost = 1.0f;
        bool IsPrimary = false;
    };

    // Reference data, loaded once at startup and kept resident for the
    // lifetime of the process -- both ApplyItemBudgetAllocation() and the
    // `.item budget` debug command read from these.
    std::unordered_map<uint32, std::vector<TemplateStat>> _templates;
    std::unordered_map<uint32, AssignRow> _assign;
    std::unordered_map<uint32, uint32> _budgetCurve;      // ilvl -> budget
    std::unordered_map<uint32, uint32> _staminaCurve;     // ilvl -> stamina
    std::map<std::pair<uint32, uint32>, float> _weaponDpsCurve; // (ilvl, quality) -> dps
    float _weaponDpsCost = 0.0f;
    float _weaponDpsSpread = 0.3f;
    std::unordered_map<uint32, float> _slotMult;          // InventoryType -> mult
    std::unordered_map<uint32, float> _qualityMult;       // Quality -> mult
    std::unordered_map<uint32, StatCostRow> _statCost;    // ItemModType -> {cost, isPrimary}
    std::unordered_map<uint32, float> _socketCost;        // SOCKET_COLOR_* -> discount
    float _setDiscount = 1.0f;
    std::unordered_map<uint32, uint32> _variantBase;      // entry -> base_entry, bookkeeping only

    std::map<std::pair<uint32, uint32>, uint32> _armorCurve; // (ilvl, armor_class) -> armor
    std::unordered_map<uint32, float> _armorSlotMult;         // InventoryType -> mult
    std::unordered_map<uint32, float> _armorQualityMult;      // Quality -> mult

    bool _loaded = false;

    void LoadItemBudgetData()
    {
        _templates.clear();
        _assign.clear();
        _budgetCurve.clear();
        _staminaCurve.clear();
        _weaponDpsCurve.clear();
        _slotMult.clear();
        _qualityMult.clear();
        _statCost.clear();
        _socketCost.clear();
        _variantBase.clear();
        _armorCurve.clear();
        _armorSlotMult.clear();
        _armorQualityMult.clear();

        if (QueryResult result = WorldDatabase.Query("SELECT template_id, stat_type, alloc FROM item_budget_template"))
        {
            do
            {
                Field* fields = result->Fetch();
                TemplateStat stat;
                stat.StatType = fields[1].Get<uint32>();
                stat.Alloc = fields[2].Get<uint32>();
                _templates[fields[0].Get<uint32>()].push_back(stat);
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT entry, template_id, budget_mult, stamina_delta, dps_delta, absorbed_spell_slots, armor_delta FROM item_budget_assign"))
        {
            do
            {
                Field* fields = result->Fetch();
                AssignRow row;
                row.TemplateId = fields[1].Get<uint32>();
                row.BudgetMult = fields[2].Get<float>();
                row.StaminaDelta = fields[3].Get<int32>();
                row.DpsDelta = fields[4].Get<float>();
                row.AbsorbedSpellSlots = fields[5].Get<uint8>();
                row.ArmorDelta = fields[6].Get<int32>();
                _assign[fields[0].Get<uint32>()] = row;
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, budget FROM item_budget_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _budgetCurve[fields[0].Get<uint32>()] = fields[1].Get<uint32>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, stamina FROM item_stamina_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _staminaCurve[fields[0].Get<uint32>()] = fields[1].Get<uint32>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, quality, dps FROM item_weapon_dps_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _weaponDpsCurve[{fields[0].Get<uint32>(), fields[1].Get<uint32>()}] = fields[2].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT cost FROM item_weapon_dps_cost WHERE id = 1"))
        {
            _weaponDpsCost = result->Fetch()[0].Get<float>();
        }

        if (QueryResult result = WorldDatabase.Query("SELECT spread FROM item_weapon_dps_spread WHERE id = 1"))
        {
            _weaponDpsSpread = result->Fetch()[0].Get<float>();
        }

        if (QueryResult result = WorldDatabase.Query("SELECT inv_type, mult FROM item_slot_mult"))
        {
            do
            {
                Field* fields = result->Fetch();
                _slotMult[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT quality, mult FROM item_quality_mult"))
        {
            do
            {
                Field* fields = result->Fetch();
                _qualityMult[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT stat_type, cost, is_primary FROM item_stat_cost"))
        {
            do
            {
                Field* fields = result->Fetch();
                StatCostRow row;
                row.Cost = fields[1].Get<float>();
                row.IsPrimary = fields[2].Get<bool>();
                _statCost[fields[0].Get<uint32>()] = row;
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT socket_color, discount FROM item_budget_socket_cost"))
        {
            do
            {
                Field* fields = result->Fetch();
                _socketCost[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT discount FROM item_budget_set_discount WHERE id = 1"))
        {
            _setDiscount = result->Fetch()[0].Get<float>();
        }

        if (QueryResult result = WorldDatabase.Query("SELECT entry, base_entry FROM item_budget_variant"))
        {
            do
            {
                Field* fields = result->Fetch();
                _variantBase[fields[0].Get<uint32>()] = fields[1].Get<uint32>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, armor_class, armor FROM item_armor_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _armorCurve[{fields[0].Get<uint32>(), fields[1].Get<uint32>()}] = fields[2].Get<uint32>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT inv_type, mult FROM item_armor_slot_mult"))
        {
            do
            {
                Field* fields = result->Fetch();
                _armorSlotMult[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT quality, mult FROM item_armor_quality_mult"))
        {
            do
            {
                Field* fields = result->Fetch();
                _armorQualityMult[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        LOG_INFO("server.loading", ">> Loaded {} item budget templates, {} assignments, {} curve entries", _templates.size(), _assign.size(), _budgetCurve.size());
    }

    // Validates the loaded reference/content data against ItemTemplate.
    // Logs every problem found (every one of these is expected to fire at
    // least once during content authoring, per design) and removes the
    // offending `item_budget_assign` row so the apply pass simply leaves
    // that one item unmaterialized rather than crashing the world.
    void ValidateItemBudgetData(ItemTemplateContainer const& itemTemplateStore)
    {
        for (auto const& [templateId, stats] : _templates)
        {
            uint32 sum = 0;
            for (TemplateStat const& stat : stats)
                sum += stat.Alloc;

            if (sum != 10000)
                LOG_ERROR("server.loading", "item_budget_template {} allocations sum to {}, not 10000", templateId, sum);

            if (stats.size() > static_cast<size_t>(MAX_ITEM_PROTO_STATS) - 1) // one slot reserved for off-budget stamina
                LOG_ERROR("server.loading", "item_budget_template {} has {} stats, exceeding the {} usable slots", templateId, stats.size(), MAX_ITEM_PROTO_STATS - 1);

            for (TemplateStat const& stat : stats)
                if (!_statCost.contains(stat.StatType))
                    LOG_ERROR("server.loading", "item_budget_template {} allocates to stat_type {}, missing from item_stat_cost", templateId, stat.StatType);
        }

        std::vector<uint32> badEntries;
        for (auto const& [entry, row] : _assign)
        {
            bool ok = true;

            auto itemIt = itemTemplateStore.find(entry);
            if (itemIt == itemTemplateStore.end())
            {
                LOG_ERROR("server.loading", "item_budget_assign entry {} does not exist in item_template", entry);
                ok = false;
            }

            if (!_templates.contains(row.TemplateId))
            {
                LOG_ERROR("server.loading", "item_budget_assign entry {} references template_id {}, which does not exist", entry, row.TemplateId);
                ok = false;
            }

            if (ok)
            {
                ItemTemplate const& tpl = itemIt->second;

                if (!_budgetCurve.contains(tpl.ItemLevel))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: ItemLevel {} missing from item_budget_curve", entry, tpl.ItemLevel);
                    ok = false;
                }

                if (!_staminaCurve.contains(tpl.ItemLevel))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: ItemLevel {} missing from item_stamina_curve", entry, tpl.ItemLevel);
                    ok = false;
                }

                if (!_slotMult.contains(tpl.InventoryType))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: InventoryType {} missing from item_slot_mult", entry, tpl.InventoryType);
                    ok = false;
                }

                if (!_qualityMult.contains(tpl.Quality))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: Quality {} missing from item_quality_mult", entry, tpl.Quality);
                    ok = false;
                }

                for (uint8 i = 0; i < MAX_ITEM_PROTO_SOCKETS; ++i)
                    if (tpl.Socket[i].Color && !_socketCost.contains(tpl.Socket[i].Color))
                    {
                        LOG_ERROR("server.loading", "item_budget_assign entry {}: socket color {} missing from item_budget_socket_cost", entry, tpl.Socket[i].Color);
                        ok = false;
                    }

                if (tpl.Class == ITEM_CLASS_WEAPON && !_weaponDpsCurve.contains({tpl.ItemLevel, tpl.Quality}))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: no item_weapon_dps_curve entry for (ilvl {}, quality {})", entry, tpl.ItemLevel, tpl.Quality);
                    ok = false;
                }

                if (row.DpsDelta != 0.0f && tpl.Class != ITEM_CLASS_WEAPON)
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: dps_delta set on a non-weapon item", entry);
                    ok = false;
                }

                bool hasArmorCurve = _armorCurve.contains({tpl.ItemLevel, tpl.SubClass}) && _armorSlotMult.contains(tpl.InventoryType) && _armorQualityMult.contains(tpl.Quality);
                if (row.ArmorDelta != 0 && !(tpl.Class == ITEM_CLASS_ARMOR && hasArmorCurve))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: armor_delta set on an item with no item_armor_curve/item_armor_slot_mult/item_armor_quality_mult entry to apply it to", entry);
                    ok = false;
                }

                if (row.AbsorbedSpellSlots >= (1u << MAX_ITEM_PROTO_SPELLS))
                {
                    LOG_ERROR("server.loading", "item_budget_assign entry {}: absorbed_spell_slots {} has a bit set past the {} available spell slots", entry, row.AbsorbedSpellSlots, MAX_ITEM_PROTO_SPELLS);
                    ok = false;
                }
                else
                {
                    for (uint8 i = 0; i < MAX_ITEM_PROTO_SPELLS; ++i)
                        if ((row.AbsorbedSpellSlots & (1u << i)) && tpl.Spells[i].SpellId == 0)
                            LOG_ERROR("server.loading", "item_budget_assign entry {}: absorbed_spell_slots marks slot {} but it has no spell to absorb -- check the bitmask", entry, i);
                }

                // Uncommon eligibility: primary stats plus at most one non-primary.
                if (tpl.Quality == ITEM_QUALITY_UNCOMMON)
                {
                    uint32 nonPrimaryCount = 0;
                    for (TemplateStat const& stat : _templates.at(row.TemplateId))
                    {
                        auto costIt = _statCost.find(stat.StatType);
                        if (costIt == _statCost.end() || !costIt->second.IsPrimary)
                            ++nonPrimaryCount;
                    }

                    if (nonPrimaryCount > 1)
                    {
                        LOG_ERROR("server.loading", "item_budget_assign entry {}: Uncommon item's template {} allocates to {} non-primary stats, more than the 1 allowed", entry, row.TemplateId, nonPrimaryCount);
                        ok = false;
                    }
                }
            }

            if (!ok)
                badEntries.push_back(entry);
        }

        for (uint32 entry : badEntries)
            _assign.erase(entry);

        for (auto const& [entry, baseEntry] : _variantBase)
        {
            if (!itemTemplateStore.contains(baseEntry))
                LOG_ERROR("server.loading", "item_budget_variant entry {}: base_entry {} does not exist in item_template", entry, baseEntry);

            if (!_assign.contains(entry))
                LOG_ERROR("server.loading", "item_budget_variant entry {} has no item_budget_assign row -- a variant materializes like any other assigned item", entry);
        }

        if (!badEntries.empty())
            LOG_ERROR("server.loading", ">> {} item_budget_assign row(s) failed validation and will keep their unmaterialized item_template stats", badEntries.size());
    }

    // Shared by the apply pass and the debug command. Read-only on `tpl`.
    // Returns false only if reference data required for this item is
    // missing -- should not happen for anything that survived validation.
    bool ResolveBudget(ItemTemplate const& tpl, AssignRow const& assign, uint32 templateId, ItemBudget::Breakdown& b)
    {
        b.Found = true;
        b.Assigned = true;
        b.Entry = tpl.ItemId;
        b.TemplateId = templateId;
        b.ItemLevel = tpl.ItemLevel;
        b.Quality = tpl.Quality;
        b.InventoryType = tpl.InventoryType;
        b.IsWeapon = (tpl.Class == ITEM_CLASS_WEAPON);

        auto slotIt = _slotMult.find(tpl.InventoryType);
        auto qualIt = _qualityMult.find(tpl.Quality);
        auto curveIt = _budgetCurve.find(tpl.ItemLevel);
        auto staminaCurveIt = _staminaCurve.find(tpl.ItemLevel);
        auto templIt = _templates.find(templateId);

        if (slotIt == _slotMult.end() || qualIt == _qualityMult.end() || curveIt == _budgetCurve.end() ||
            staminaCurveIt == _staminaCurve.end() || templIt == _templates.end())
            return false;

        b.SlotMult = slotIt->second;
        b.QualityMult = qualIt->second;
        b.BudgetMult = assign.BudgetMult;
        b.AbsorbedSpellSlots = assign.AbsorbedSpellSlots;

        b.SocketCount = 0;
        b.SocketDiscount = 1.0f;
        for (uint8 i = 0; i < MAX_ITEM_PROTO_SOCKETS; ++i)
        {
            uint32 color = tpl.Socket[i].Color;
            if (!color)
                continue;

            ++b.SocketCount;
            auto costIt = _socketCost.find(color);
            b.SocketDiscount *= (costIt != _socketCost.end()) ? costIt->second : 1.0f;
        }

        b.IsSetPiece = (tpl.ItemSet != 0);
        b.SetDiscount = b.IsSetPiece ? _setDiscount : 1.0f;

        b.EffectiveMult = b.BudgetMult * b.SocketDiscount * b.SetDiscount;
        b.Budget = static_cast<int32>(std::lround(curveIt->second * b.SlotMult * b.QualityMult * b.EffectiveMult));

        float staminaCost = 1.0f;
        if (auto statCostIt = _statCost.find(ITEM_MOD_STAMINA); statCostIt != _statCost.end())
            staminaCost = statCostIt->second.Cost;

        b.BaselineStamina = static_cast<int32>(std::lround(staminaCurveIt->second * b.SlotMult * b.QualityMult));
        b.StaminaDelta = assign.StaminaDelta;
        b.FinalStamina = std::max(0, b.BaselineStamina + b.StaminaDelta);

        // Armor: off-budget like Stamina, but with its own slot/quality
        // multipliers and never funded from the budget -- see §9.3.
        b.ArmorDelta = assign.ArmorDelta;
        auto armorCurveIt = _armorCurve.find({tpl.ItemLevel, tpl.SubClass});
        auto armorSlotIt = _armorSlotMult.find(tpl.InventoryType);
        auto armorQualIt = _armorQualityMult.find(tpl.Quality);
        b.HasArmorCurve = (tpl.Class == ITEM_CLASS_ARMOR && armorCurveIt != _armorCurve.end() &&
                            armorSlotIt != _armorSlotMult.end() && armorQualIt != _armorQualityMult.end());
        if (b.HasArmorCurve)
        {
            b.ArmorClass = tpl.SubClass;
            b.BaselineArmor = static_cast<int32>(std::lround(armorCurveIt->second * armorSlotIt->second * armorQualIt->second));
            b.FinalArmor = std::max(0, b.BaselineArmor + b.ArmorDelta);
        }

        float effectiveBudget = static_cast<float>(b.Budget) - (b.StaminaDelta * staminaCost);

        b.DpsDelta = 0.0f;
        b.BaselineDps = 0.0f;
        b.FinalDps = 0.0f;
        b.DmgMin = 0.0f;
        b.DmgMax = 0.0f;
        if (b.IsWeapon)
        {
            if (auto dpsIt = _weaponDpsCurve.find({tpl.ItemLevel, tpl.Quality}); dpsIt != _weaponDpsCurve.end())
            {
                b.BaselineDps = dpsIt->second;
                b.DpsDelta = assign.DpsDelta;
                b.FinalDps = std::max(0.0f, b.BaselineDps + b.DpsDelta);
                effectiveBudget -= (b.DpsDelta * _weaponDpsCost);

                float avgDamage = b.FinalDps * (static_cast<float>(tpl.Delay) / 1000.0f);
                b.DmgMin = avgDamage * (1.0f - _weaponDpsSpread / 2.0f);
                b.DmgMax = avgDamage * (1.0f + _weaponDpsSpread / 2.0f);
            }
        }

        if (effectiveBudget < 0.0f)
            effectiveBudget = 0.0f;

        b.EffectiveBudget = static_cast<int32>(std::lround(effectiveBudget));

        struct Working
        {
            uint32 StatType;
            bool IsPrimary;
            uint32 Alloc;
            float Exact;
            int32 Floor;
            float Remainder;
        };

        std::vector<Working> working;
        working.reserve(templIt->second.size());
        int32 floorSum = 0;
        float exactSum = 0.0f;

        for (TemplateStat const& stat : templIt->second)
        {
            float cost = 1.0f;
            bool isPrimary = false;
            if (auto costIt = _statCost.find(stat.StatType); costIt != _statCost.end())
            {
                cost = costIt->second.Cost;
                isPrimary = costIt->second.IsPrimary;
            }

            float rawBudget = effectiveBudget * (static_cast<float>(stat.Alloc) / 10000.0f);
            float exact = cost > 0.0f ? rawBudget / cost : 0.0f;
            int32 flr = static_cast<int32>(std::floor(exact));

            working.push_back({stat.StatType, isPrimary, stat.Alloc, exact, flr, exact - static_cast<float>(flr)});
            floorSum += flr;
            exactSum += exact;
        }

        int32 target = static_cast<int32>(std::lround(exactSum));
        int32 remainder = std::max(0, target - floorSum);
        b.RoundingRemainderPoints = remainder;

        std::vector<size_t> order(working.size());
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&working](size_t lhs, size_t rhs)
        {
            return working[lhs].Remainder > working[rhs].Remainder;
        });

        for (int32 i = 0; i < remainder && i < static_cast<int32>(order.size()); ++i)
            working[order[i]].Floor += 1;

        b.Allocations.clear();
        b.Allocations.reserve(working.size());
        for (Working const& w : working)
        {
            ItemBudget::AllocationDetail detail;
            detail.StatType = w.StatType;
            detail.IsPrimary = w.IsPrimary;
            detail.Alloc = w.Alloc;
            detail.RawValue = w.Exact;
            detail.RoundedValue = w.Floor;
            b.Allocations.push_back(detail);
        }

        return true;
    }

    void ApplyItemBudgetAllocation(ItemTemplateContainer& itemTemplateStore)
    {
        uint32 applied = 0;

        for (auto const& [entry, assign] : _assign)
        {
            auto itemIt = itemTemplateStore.find(entry);
            if (itemIt == itemTemplateStore.end())
                continue; // already logged during validation

            ItemBudget::Breakdown b;
            if (!ResolveBudget(itemIt->second, assign, assign.TemplateId, b))
            {
                LOG_ERROR("server.loading", "item_budget: could not resolve entry {}, leaving its item_template stats unmaterialized", entry);
                continue;
            }

            ItemTemplate& tpl = itemIt->second;

            if (b.Allocations.size() + 1 > static_cast<size_t>(MAX_ITEM_PROTO_STATS)) // +1 for off-budget stamina
            {
                LOG_ERROR("server.loading", "item_budget: entry {} resolves to {} stats plus stamina, exceeding the {} available slots -- skipped", entry, b.Allocations.size(), MAX_ITEM_PROTO_STATS);
                continue;
            }

            uint32 slot = 0;
            for (ItemBudget::AllocationDetail const& alloc : b.Allocations)
            {
                tpl.ItemStat[slot].ItemStatType = alloc.StatType;
                tpl.ItemStat[slot].ItemStatValue = alloc.RoundedValue;
                ++slot;
            }

            tpl.ItemStat[slot].ItemStatType = ITEM_MOD_STAMINA;
            tpl.ItemStat[slot].ItemStatValue = b.FinalStamina;
            ++slot;

            for (uint32 clear = slot; clear < static_cast<uint32>(MAX_ITEM_PROTO_STATS); ++clear)
            {
                tpl.ItemStat[clear].ItemStatType = 0;
                tpl.ItemStat[clear].ItemStatValue = 0;
            }

            tpl.StatsCount = slot;

            if (b.IsWeapon && (b.DmgMin > 0.0f || b.DmgMax > 0.0f))
            {
                tpl.Damage[0].DamageMin = b.DmgMin;
                tpl.Damage[0].DamageMax = b.DmgMax;
            }

            if (b.HasArmorCurve)
                tpl.Armor = static_cast<uint32>(b.FinalArmor);

            // Clear any on-equip spell whose effect got folded into the
            // plain stat block above, so it isn't granted twice.
            for (uint8 i = 0; i < MAX_ITEM_PROTO_SPELLS; ++i)
            {
                if (!(b.AbsorbedSpellSlots & (1u << i)))
                    continue;

                tpl.Spells[i].SpellId = 0;
                tpl.Spells[i].SpellTrigger = 0;
                tpl.Spells[i].SpellCharges = 0;
                tpl.Spells[i].SpellPPMRate = 0.0f;
                tpl.Spells[i].SpellCooldown = -1;
                tpl.Spells[i].SpellCategory = 0;
                tpl.Spells[i].SpellCategoryCooldown = -1;
            }

            ++applied;
        }

        LOG_INFO("server.loading", ">> Materialized {} item budget assignment(s)", applied);
    }
}

namespace ItemBudget
{
    void LoadAndApply(ItemTemplateContainer& itemTemplateStore)
    {
        uint32 oldMSTime = getMSTime();

        LoadItemBudgetData();
        ValidateItemBudgetData(itemTemplateStore);
        ApplyItemBudgetAllocation(itemTemplateStore);

        _loaded = true;

        LOG_INFO("server.loading", ">> Item budget system ready in {} ms", GetMSTimeDiffToNow(oldMSTime));
        LOG_INFO("server.loading", " ");
    }

    Breakdown ComputeBreakdown(uint32 entry)
    {
        Breakdown b;

        if (!_loaded)
            return b;

        ItemTemplate const* tpl = sObjectMgr->GetItemTemplate(entry);
        if (!tpl)
            return b;

        b.Found = true;
        b.Entry = entry;

        auto assignIt = _assign.find(entry);
        if (assignIt == _assign.end())
            return b; // Found but not Assigned -- caller reports "not a budget item"

        ResolveBudget(*tpl, assignIt->second, assignIt->second.TemplateId, b);
        return b;
    }
}
