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
#include <set>
#include <tuple>
#include <unordered_map>

namespace
{
    // Weapon DPS "hand category": paired-slot weapons (One-Hand/Main Hand/Off Hand) share their
    // budget with a second item in the other hand; single-slot weapons (Two-Hand/Ranged/Thrown/
    // Relic) are the whole story for their damage-dealing slot and, per real WotLK itemization,
    // run consistently ~1.30x the DPS of a paired-slot weapon at the same ilvl/quality -- a
    // deliberate design constant, not noise (confirmed via regression against 1,048 real
    // Str/Agi/AttackPower weapons, ratio ~1.30 flat across the whole ilvl range). Pooling both
    // categories into one curve (as this table originally did) makes every single-slot weapon
    // look "above curve" and every paired-slot weapon look "at or below curve" -- with
    // item_weapon_dps_cost this steep, that made real Two-Hand weapons rout their entire stat
    // budget to zero just to pay for DPS they already have baked into the curve's own median.
    bool IsSingleSlotWeapon(uint32 invType)
    {
        return invType == INVTYPE_2HWEAPON || invType == INVTYPE_RANGED || invType == INVTYPE_RANGEDRIGHT ||
            invType == INVTYPE_THROWN || invType == INVTYPE_RELIC;
    }

    struct ItemizationRow
    {
        float BudgetMult = 1.0f;
        int32 StaminaDelta = 0;
        float DpsDelta = 0.0f;
        uint32 AbsorbedSpellSlots = 0; // bitmask, bit i = clear Spells[i] at materialization
        int32 ArmorDelta = 0;          // raw armor points, +/- -- NOT funded from budget, itemization-changes.md §9.3a
        uint32 PrimaryShapeId = 0;
        uint32 SecondaryShapeId = 0;
        uint32 PrimaryShare = 6000;    // ten-thousandths
        int32 BlockValueDelta = 0;     // shields only, NOT funded from budget, docs/itemization-phase-2.md §7.4
    };

    struct StatCostRow
    {
        float Cost = 1.0f;
        bool IsPrimary = false;
        uint32 ShapeSide = 0; // 0 = never in a shape, 1 = primary side, 2 = secondary side
    };

    struct ShapeRow
    {
        uint32 Kind = 0;   // 0 = primary, 1 = secondary
        uint32 DistId = 0;
    };

    struct ShapeRuleRow
    {
        uint32 RuleType = 0; // 1 = requires_any, 2 = forbids
        uint32 StatType = 0;
    };

    // Reference data, loaded once at startup and kept resident for the lifetime of the
    // process -- both ApplyItemizationAllocation() and the `.item budget` debug command read
    // from these.
    std::unordered_map<uint32, ItemizationRow> _itemization;
    std::unordered_map<uint32, uint32> _budgetCurve;      // ilvl -> budget
    std::unordered_map<uint32, uint32> _staminaCurve;     // ilvl -> stamina
    std::map<std::tuple<uint32, uint32, bool>, float> _weaponDpsCurve; // (ilvl, quality, isSingleSlot) -> dps
    float _weaponDpsCost = 0.0f;
    float _weaponDpsSpread = 0.3f;
    std::unordered_map<uint32, float> _slotMult;          // InventoryType -> mult
    std::unordered_map<uint32, float> _qualityMult;       // Quality -> mult
    std::unordered_map<uint32, StatCostRow> _statCost;    // ItemModType -> {cost, isPrimary, shapeSide}
    float _setDiscount = 1.0f;
    std::unordered_map<uint32, uint32> _variantBase;      // entry -> base_entry, bookkeeping only

    std::map<std::pair<uint32, uint32>, uint32> _armorCurve; // (ilvl, armor_class) -> armor
    std::unordered_map<uint32, float> _armorSlotMult;         // InventoryType -> mult
    std::unordered_map<uint32, float> _armorQualityMult;      // Quality -> mult

    std::unordered_map<uint32, float> _gemValueCurve;         // ilvl -> budget units one socket is worth, §7.5
    std::map<std::pair<uint32, uint32>, float> _blockValueCurve; // (ilvl, quality) -> block value, shields only, §7.4

    std::unordered_map<uint32, std::vector<uint32>> _dist;       // dist_id -> alloc, ordered by rank
    std::unordered_map<uint32, ShapeRow> _shapes;                 // shape_id -> {kind, dist_id}
    std::unordered_map<uint32, std::vector<uint32>> _shapeStats;  // shape_id -> stat_type, ordered by rank
    std::unordered_map<uint32, std::vector<ShapeRuleRow>> _shapeRules; // shape_id -> rules (secondary shapes only)

    // Allowed primary_share values, docs/itemization-phase-2.md §5.5.
    constexpr uint32 ALLOWED_PRIMARY_SHARES[] = {0, 4000, 6000, 8000, 10000};

    bool _loaded = false;

    void LoadItemizationData()
    {
        _itemization.clear();
        _budgetCurve.clear();
        _staminaCurve.clear();
        _weaponDpsCurve.clear();
        _slotMult.clear();
        _qualityMult.clear();
        _statCost.clear();
        _variantBase.clear();
        _armorCurve.clear();
        _armorSlotMult.clear();
        _armorQualityMult.clear();
        _gemValueCurve.clear();
        _blockValueCurve.clear();
        _dist.clear();
        _shapes.clear();
        _shapeStats.clear();
        _shapeRules.clear();

        if (QueryResult result = WorldDatabase.Query(
            "SELECT entry, budget_mult, stamina_delta, dps_delta, absorbed_spell_slots, armor_delta, "
            "primary_shape_id, secondary_shape_id, primary_share, block_value_delta FROM item_itemization"))
        {
            do
            {
                Field* fields = result->Fetch();
                ItemizationRow row;
                row.BudgetMult = fields[1].Get<float>();
                row.StaminaDelta = fields[2].Get<int32>();
                row.DpsDelta = fields[3].Get<float>();
                row.AbsorbedSpellSlots = fields[4].Get<uint8>();
                row.ArmorDelta = fields[5].Get<int32>();
                row.PrimaryShapeId = fields[6].Get<uint32>();
                row.SecondaryShapeId = fields[7].Get<uint32>();
                row.PrimaryShare = fields[8].Get<uint32>();
                row.BlockValueDelta = fields[9].Get<int32>();
                _itemization[fields[0].Get<uint32>()] = row;
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

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, quality, is_single_slot, dps FROM item_weapon_dps_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _weaponDpsCurve[{fields[0].Get<uint32>(), fields[1].Get<uint32>(), fields[2].Get<bool>()}] = fields[3].Get<float>();
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

        if (QueryResult result = WorldDatabase.Query("SELECT stat_type, cost, is_primary, shape_side FROM item_stat_cost"))
        {
            do
            {
                Field* fields = result->Fetch();
                StatCostRow row;
                row.Cost = fields[1].Get<float>();
                row.IsPrimary = fields[2].Get<bool>();
                row.ShapeSide = fields[3].Get<uint8>();
                _statCost[fields[0].Get<uint32>()] = row;
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

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, gem_budget FROM item_gem_value_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _gemValueCurve[fields[0].Get<uint32>()] = fields[1].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT ilvl, quality, block_value FROM item_block_value_curve"))
        {
            do
            {
                Field* fields = result->Fetch();
                _blockValueCurve[{fields[0].Get<uint32>(), fields[1].Get<uint32>()}] = fields[2].Get<float>();
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT dist_id, `rank`, alloc FROM item_alloc_dist ORDER BY dist_id, `rank`"))
        {
            do
            {
                Field* fields = result->Fetch();
                _dist[fields[0].Get<uint32>()].push_back(fields[2].Get<uint32>());
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT shape_id, kind, dist_id FROM item_shape"))
        {
            do
            {
                Field* fields = result->Fetch();
                ShapeRow row;
                row.Kind = fields[1].Get<uint8>();
                row.DistId = fields[2].Get<uint32>();
                _shapes[fields[0].Get<uint32>()] = row;
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT shape_id, `rank`, stat_type FROM item_shape_stat ORDER BY shape_id, `rank`"))
        {
            do
            {
                Field* fields = result->Fetch();
                _shapeStats[fields[0].Get<uint32>()].push_back(fields[2].Get<uint32>());
            } while (result->NextRow());
        }

        if (QueryResult result = WorldDatabase.Query("SELECT shape_id, rule_type, stat_type FROM item_shape_rule"))
        {
            do
            {
                Field* fields = result->Fetch();
                ShapeRuleRow rule;
                rule.RuleType = fields[1].Get<uint8>();
                rule.StatType = fields[2].Get<uint32>();
                _shapeRules[fields[0].Get<uint32>()].push_back(rule);
            } while (result->NextRow());
        }

        LOG_INFO("server.loading", ">> Loaded {} item_itemization row(s), {} shape(s), {} distribution(s)", _itemization.size(), _shapes.size(), _dist.size());
    }

    // Validates the shape catalog itself (docs/itemization-phase-2.md §8, checks 1-6) --
    // config-level problems, independent of any one item. Logged, not fatal: a badly-configured
    // shape produces bad numbers for every item that uses it, which is already visible in the
    // log, same philosophy as the rest of this validation pass.
    void ValidateShapeCatalog()
    {
        for (auto const& [shapeId, shape] : _shapes)
        {
            // shape_id 0 is the null shape by design (docs/itemization-phase-2.md §5.2) -- no
            // item_shape_stat rows, used by rings/necks. Exempt from check 1.
            if (shapeId == 0)
                continue;

            auto distIt = _dist.find(shape.DistId);
            if (distIt == _dist.end())
            {
                LOG_ERROR("server.loading", "item_shape {}: dist_id {} has no item_alloc_dist rows", shapeId, shape.DistId);
                continue;
            }

            auto statsIt = _shapeStats.find(shapeId);
            size_t rankCount = (statsIt != _shapeStats.end()) ? statsIt->second.size() : 0;

            // Check 1: rank count in item_shape_stat equals rank count in the shape's dist_id.
            if (rankCount != distIt->second.size())
                LOG_ERROR("server.loading", "item_shape {}: {} item_shape_stat row(s), but dist_id {} has {} rank(s)", shapeId, rankCount, shape.DistId, distIt->second.size());

            // Check 3: item_shape_stat.stat_type has shape_side matching its shape's kind
            // (1 for primary/kind 0, 2 for secondary/kind 1).
            if (statsIt != _shapeStats.end())
            {
                uint32 expectedShapeSide = shape.Kind + 1;
                for (uint32 statType : statsIt->second)
                {
                    auto costIt = _statCost.find(statType);
                    if (costIt == _statCost.end() || costIt->second.ShapeSide != expectedShapeSide)
                        LOG_ERROR("server.loading", "item_shape {} (kind {}): stat_type {} has shape_side {}, expected {}",
                            shapeId, shape.Kind, statType, (costIt != _statCost.end()) ? costIt->second.ShapeSide : 0, expectedShapeSide);
                }
            }
        }

        // Check 2: item_alloc_dist.alloc sums to exactly 10000 per dist_id.
        for (auto const& [distId, allocs] : _dist)
        {
            uint32 sum = std::accumulate(allocs.begin(), allocs.end(), 0u);
            if (sum != 10000)
                LOG_ERROR("server.loading", "item_alloc_dist {}: allocations sum to {}, not 10000", distId, sum);
        }

        // Checks 4-6: item_shape_rule.
        for (auto const& [shapeId, rules] : _shapeRules)
        {
            auto shapeIt = _shapes.find(shapeId);

            // Check 5: item_shape_rule.shape_id references a shape with kind = 1 (secondary);
            // rules on a primary shape are inert and silently do nothing.
            if (shapeIt == _shapes.end() || shapeIt->second.Kind != 1)
                LOG_ERROR("server.loading", "item_shape_rule shape_id {}: not a secondary (kind 1) shape -- these rules are inert", shapeId);

            for (ShapeRuleRow const& rule : rules)
            {
                // Check 6: FK to item_stat_cost.
                auto costIt = _statCost.find(rule.StatType);
                if (costIt == _statCost.end())
                {
                    LOG_ERROR("server.loading", "item_shape_rule shape_id {}: stat_type {} is not in item_stat_cost", shapeId, rule.StatType);
                    continue;
                }

                // Check 4: item_shape_rule.stat_type has shape_side = 1 -- rules only ever test
                // a primary stat set.
                if (costIt->second.ShapeSide != 1)
                    LOG_ERROR("server.loading", "item_shape_rule shape_id {}: stat_type {} has shape_side {}, expected 1 (primary)", shapeId, rule.StatType, costIt->second.ShapeSide);
            }
        }
    }

    // A secondary shape's rules, evaluated against a primary shape's stat set (§6, §8 check 9).
    // All requires_any rows for the shape form a single disjunction; all forbids rows must be
    // absent. A secondary shape with no rules at all always passes.
    bool SecondaryShapeRulesSatisfied(uint32 secondaryShapeId, std::set<uint32> const& primaryStatSet)
    {
        auto rulesIt = _shapeRules.find(secondaryShapeId);
        if (rulesIt == _shapeRules.end())
            return true;

        bool hasRequiresAny = false;
        bool anyRequiredMatched = false;

        for (ShapeRuleRow const& rule : rulesIt->second)
        {
            if (rule.RuleType == 1) // requires_any
            {
                hasRequiresAny = true;
                if (primaryStatSet.contains(rule.StatType))
                    anyRequiredMatched = true;
            }
            else if (rule.RuleType == 2) // forbids
            {
                if (primaryStatSet.contains(rule.StatType))
                    return false;
            }
        }

        return !hasRequiresAny || anyRequiredMatched;
    }

    // Validates the loaded reference/content data against ItemTemplate. Logs every problem
    // found (every one of these is expected to fire at least once during content authoring, per
    // design) and removes the offending `item_itemization` row so the apply pass simply leaves
    // that one item unmaterialized rather than crashing the world.
    void ValidateItemizationData(ItemTemplateContainer const& itemTemplateStore)
    {
        ValidateShapeCatalog();

        std::vector<uint32> badEntries;
        for (auto const& [entry, row] : _itemization)
        {
            bool ok = true;

            auto itemIt = itemTemplateStore.find(entry);
            if (itemIt == itemTemplateStore.end())
            {
                LOG_ERROR("server.loading", "item_itemization entry {} does not exist in item_template", entry);
                ok = false;
            }

            if (!_shapes.contains(row.PrimaryShapeId))
            {
                LOG_ERROR("server.loading", "item_itemization entry {} references primary_shape_id {}, which does not exist", entry, row.PrimaryShapeId);
                ok = false;
            }

            if (!_shapes.contains(row.SecondaryShapeId))
            {
                LOG_ERROR("server.loading", "item_itemization entry {} references secondary_shape_id {}, which does not exist", entry, row.SecondaryShapeId);
                ok = false;
            }

            // Check 7: primary_share is one of the allowed values.
            if (std::find(std::begin(ALLOWED_PRIMARY_SHARES), std::end(ALLOWED_PRIMARY_SHARES), row.PrimaryShare) == std::end(ALLOWED_PRIMARY_SHARES))
            {
                LOG_ERROR("server.loading", "item_itemization entry {}: primary_share {} is not an allowed value", entry, row.PrimaryShare);
                ok = false;
            }

            // Check 8: primary_shape_id = 0 implies primary_share = 0 (shape 0 has no stat rows,
            // so any nonzero share on it would just fund nothing). The reverse is NOT required:
            // primary_shape_id != 0 with primary_share = 0 is a deliberate, valid state -- a
            // nominal primary assigned purely so a secondary shape's rule (e.g. Dodge/Parry/
            // Block's "requires Str") can pass against an item with no real primary stat history,
            // not a real budget allocation (docs/itemization-phase-2.md §9.1's "nominal Str
            // primary" -- confirmed real: 145 real items use exactly this, entries 868/943 among
            // them). An earlier, stricter iff version of this check flagged all 145 as
            // inconsistent before this was caught on the first real boot against migrated data.
            if (row.PrimaryShapeId == 0 && row.PrimaryShare != 0)
            {
                LOG_ERROR("server.loading", "item_itemization entry {}: primary_share {} is nonzero but primary_shape_id is 0 (the null shape has no stats to fund)", entry, row.PrimaryShare);
                ok = false;
            }

            if (ok)
            {
                ItemTemplate const& tpl = itemIt->second;

                if (!_budgetCurve.contains(tpl.ItemLevel))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: ItemLevel {} missing from item_budget_curve", entry, tpl.ItemLevel);
                    ok = false;
                }

                if (!_staminaCurve.contains(tpl.ItemLevel))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: ItemLevel {} missing from item_stamina_curve", entry, tpl.ItemLevel);
                    ok = false;
                }

                if (!_slotMult.contains(tpl.InventoryType))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: InventoryType {} missing from item_slot_mult", entry, tpl.InventoryType);
                    ok = false;
                }

                if (!_qualityMult.contains(tpl.Quality))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: Quality {} missing from item_quality_mult", entry, tpl.Quality);
                    ok = false;
                }

                bool hasSockets = false;
                for (uint8 i = 0; i < MAX_ITEM_PROTO_SOCKETS; ++i)
                    if (tpl.Socket[i].Color)
                        hasSockets = true;

                if (hasSockets && !_gemValueCurve.contains(tpl.ItemLevel))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: has socket(s) but ItemLevel {} missing from item_gem_value_curve", entry, tpl.ItemLevel);
                    ok = false;
                }

                if (tpl.Class == ITEM_CLASS_WEAPON && !_weaponDpsCurve.contains({tpl.ItemLevel, tpl.Quality, IsSingleSlotWeapon(tpl.InventoryType)}))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: no item_weapon_dps_curve entry for (ilvl {}, quality {}, single-slot {})", entry, tpl.ItemLevel, tpl.Quality, IsSingleSlotWeapon(tpl.InventoryType));
                    ok = false;
                }

                if (row.DpsDelta != 0.0f && tpl.Class != ITEM_CLASS_WEAPON)
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: dps_delta set on a non-weapon item", entry);
                    ok = false;
                }

                bool hasArmorCurve = _armorCurve.contains({tpl.ItemLevel, tpl.SubClass}) && _armorSlotMult.contains(tpl.InventoryType) && _armorQualityMult.contains(tpl.Quality);
                if (row.ArmorDelta != 0 && !(tpl.Class == ITEM_CLASS_ARMOR && hasArmorCurve))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: armor_delta set on an item with no item_armor_curve/item_armor_slot_mult/item_armor_quality_mult entry to apply it to", entry);
                    ok = false;
                }

                bool isShield = (tpl.Class == ITEM_CLASS_ARMOR && tpl.SubClass == ITEM_SUBCLASS_ARMOR_SHIELD);
                if (row.BlockValueDelta != 0 && !(isShield && _blockValueCurve.contains({tpl.ItemLevel, tpl.Quality})))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: block_value_delta set on an item with no item_block_value_curve entry to apply it to (shields only)", entry);
                    ok = false;
                }

                if (row.AbsorbedSpellSlots >= (1u << MAX_ITEM_PROTO_SPELLS))
                {
                    LOG_ERROR("server.loading", "item_itemization entry {}: absorbed_spell_slots {} has a bit set past the {} available spell slots", entry, row.AbsorbedSpellSlots, MAX_ITEM_PROTO_SPELLS);
                    ok = false;
                }
                else
                {
                    for (uint8 i = 0; i < MAX_ITEM_PROTO_SPELLS; ++i)
                        if ((row.AbsorbedSpellSlots & (1u << i)) && tpl.Spells[i].SpellId == 0)
                            LOG_ERROR("server.loading", "item_itemization entry {}: absorbed_spell_slots marks slot {} but it has no spell to absorb -- check the bitmask", entry, i);
                }

                // Check 9: this row's secondary shape's rules, evaluated against its primary
                // shape's stat set.
                if (ok)
                {
                    std::set<uint32> primaryStatSet;
                    if (auto statsIt = _shapeStats.find(row.PrimaryShapeId); statsIt != _shapeStats.end())
                        primaryStatSet.insert(statsIt->second.begin(), statsIt->second.end());

                    if (!SecondaryShapeRulesSatisfied(row.SecondaryShapeId, primaryStatSet))
                    {
                        LOG_ERROR("server.loading", "item_itemization entry {}: secondary_shape_id {} rules are not satisfied by primary_shape_id {}", entry, row.SecondaryShapeId, row.PrimaryShapeId);
                        ok = false;
                    }
                }
            }

            if (!ok)
                badEntries.push_back(entry);
        }

        for (uint32 entry : badEntries)
            _itemization.erase(entry);

        for (auto const& [entry, baseEntry] : _variantBase)
        {
            if (!itemTemplateStore.contains(baseEntry))
                LOG_ERROR("server.loading", "item_budget_variant entry {}: base_entry {} does not exist in item_template", entry, baseEntry);

            if (!_itemization.contains(entry))
                LOG_ERROR("server.loading", "item_budget_variant entry {} has no item_itemization row -- a variant materializes like any other assigned item", entry);
        }

        if (!badEntries.empty())
            LOG_ERROR("server.loading", ">> {} item_itemization row(s) failed validation and will keep their unmaterialized item_template stats", badEntries.size());
    }

    // Shared by the apply pass and the debug command. Read-only on `tpl`. Returns false only if
    // reference data required for this item is missing -- should not happen for anything that
    // survived validation.
    bool ResolveBudget(ItemTemplate const& tpl, ItemizationRow const& row, ItemBudget::Breakdown& b)
    {
        b.Found = true;
        b.Assigned = true;
        b.Entry = tpl.ItemId;
        b.PrimaryShapeId = row.PrimaryShapeId;
        b.SecondaryShapeId = row.SecondaryShapeId;
        b.PrimaryShare = row.PrimaryShare;
        b.ItemLevel = tpl.ItemLevel;
        b.Quality = tpl.Quality;
        b.InventoryType = tpl.InventoryType;
        b.IsWeapon = (tpl.Class == ITEM_CLASS_WEAPON);

        auto slotIt = _slotMult.find(tpl.InventoryType);
        auto qualIt = _qualityMult.find(tpl.Quality);
        auto curveIt = _budgetCurve.find(tpl.ItemLevel);
        auto staminaCurveIt = _staminaCurve.find(tpl.ItemLevel);
        auto primaryShapeIt = _shapes.find(row.PrimaryShapeId);
        auto secondaryShapeIt = _shapes.find(row.SecondaryShapeId);

        if (slotIt == _slotMult.end() || qualIt == _qualityMult.end() || curveIt == _budgetCurve.end() ||
            staminaCurveIt == _staminaCurve.end() || primaryShapeIt == _shapes.end() || secondaryShapeIt == _shapes.end())
            return false;

        b.SlotMult = slotIt->second;
        b.QualityMult = qualIt->second;
        b.BudgetMult = row.BudgetMult;
        b.AbsorbedSpellSlots = row.AbsorbedSpellSlots;

        b.IsSetPiece = (tpl.ItemSet != 0);
        b.SetDiscount = b.IsSetPiece ? _setDiscount : 1.0f;

        // Step 1 (docs/itemization-phase-2.md §4): base.
        double base = static_cast<double>(curveIt->second) * b.SlotMult * b.QualityMult * b.BudgetMult * b.SetDiscount;

        // Step 2: budget = base - socket_count * GemValueCurve(ilvl) - socket_bonus_value.
        b.SocketCount = 0;
        for (uint8 i = 0; i < MAX_ITEM_PROTO_SOCKETS; ++i)
            if (tpl.Socket[i].Color)
                ++b.SocketCount;

        float gemValue = 0.0f;
        if (b.SocketCount > 0)
        {
            auto gemIt = _gemValueCurve.find(tpl.ItemLevel);
            gemValue = (gemIt != _gemValueCurve.end()) ? gemIt->second : 0.0f;
        }
        b.SocketBudgetCost = static_cast<float>(b.SocketCount) * gemValue;

        // socketBonus pricing (resolving the granted SpellItemEnchantment through
        // item_stat_cost, §7.5) is not implemented -- SpellItemEnchantment DBC data isn't
        // resident in this database (spellitemenchantment_dbc is unpopulated here). Always 0
        // for now; every item's socketBonus enchant remains unpriced free value, same as before
        // this rewrite.
        b.SocketBonusValue = 0;

        b.Budget = static_cast<int32>(std::lround(base - b.SocketBudgetCost - b.SocketBonusValue));

        // Off-budget baselines: Stamina, Armor, Block Value. None of these are funded from the
        // budget computed above -- itemization-changes.md §9.3/§9.3a, docs/itemization-phase-2.md §7.4.
        float staminaCost = 1.0f;
        if (auto statCostIt = _statCost.find(ITEM_MOD_STAMINA); statCostIt != _statCost.end())
            staminaCost = statCostIt->second.Cost;

        b.BaselineStamina = static_cast<int32>(std::lround(staminaCurveIt->second * b.SlotMult * b.QualityMult));
        b.StaminaDelta = row.StaminaDelta;
        b.FinalStamina = std::max(0, b.BaselineStamina + b.StaminaDelta);

        b.ArmorDelta = row.ArmorDelta;
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

        b.BlockValueDelta = row.BlockValueDelta;
        auto blockValueIt = _blockValueCurve.find({tpl.ItemLevel, tpl.Quality});
        b.HasBlockValueCurve = (tpl.Class == ITEM_CLASS_ARMOR && tpl.SubClass == ITEM_SUBCLASS_ARMOR_SHIELD && blockValueIt != _blockValueCurve.end());
        if (b.HasBlockValueCurve)
        {
            b.BaselineBlockValue = static_cast<int32>(std::lround(blockValueIt->second));
            b.FinalBlockValue = std::max(0, b.BaselineBlockValue + b.BlockValueDelta);
        }

        // Deltas that fund themselves out of the item's own budget (unlike Armor/Block Value's
        // deltas above, which are free additive knobs).
        double effectiveBudget = static_cast<double>(b.Budget) - (b.StaminaDelta * staminaCost);

        b.DpsDelta = 0.0f;
        b.BaselineDps = 0.0f;
        b.FinalDps = 0.0f;
        b.DmgMin = 0.0f;
        b.DmgMax = 0.0f;
        if (b.IsWeapon)
        {
            if (auto dpsIt = _weaponDpsCurve.find({tpl.ItemLevel, tpl.Quality, IsSingleSlotWeapon(tpl.InventoryType)}); dpsIt != _weaponDpsCurve.end())
            {
                b.BaselineDps = dpsIt->second;
                b.DpsDelta = row.DpsDelta;
                b.FinalDps = std::max(0.0f, b.BaselineDps + b.DpsDelta);
                effectiveBudget -= (b.DpsDelta * _weaponDpsCost);

                float avgDamage = b.FinalDps * (static_cast<float>(tpl.Delay) / 1000.0f);
                b.DmgMin = avgDamage * (1.0f - _weaponDpsSpread / 2.0f);
                b.DmgMax = avgDamage * (1.0f + _weaponDpsSpread / 2.0f);
            }
        }

        if (effectiveBudget < 0.0)
            effectiveBudget = 0.0;

        b.EffectiveBudget = static_cast<int32>(std::lround(effectiveBudget));

        // Step 3: two-sided split. secondary_budget is the exact complement of primary_budget
        // (not independently recomputed from a "secondary share"), per §4 step 3 literally --
        // guarantees the two sides always sum back to effectiveBudget with no rounding leak.
        double primaryBudget = effectiveBudget * static_cast<double>(row.PrimaryShare) / 10000.0;
        double secondaryBudget = effectiveBudget - primaryBudget;
        b.PrimaryBudget = static_cast<float>(primaryBudget);
        b.SecondaryBudget = static_cast<float>(secondaryBudget);

        // Step 4: allocate each side against its shape's ordered stat list and distribution.
        // Every rank of a given (alloc, cost) pair goes through this exact same formula in the
        // same order, so two ranks that are supposed to tie (e.g. Even trio's/Lead-plus-two's
        // equal-alloc ranks) produce bit-identical `double`s -- see §4.1: the real risk this
        // guards against is a *should-be* tie silently not registering as one because two
        // "equal" values took different computation paths, not raw floating-point noise.
        struct Working
        {
            uint32 StatType;
            bool IsPrimary;
            uint32 Alloc;
            double Exact;
            int32 Floor;
            double Remainder;
        };

        std::vector<Working> working;

        auto allocateSide = [&working](uint32 shapeId, double sideBudget, bool isPrimarySide)
        {
            auto shapeIt = _shapes.find(shapeId);
            if (shapeIt == _shapes.end())
                return;

            auto allocIt = _dist.find(shapeIt->second.DistId);
            auto statsIt = _shapeStats.find(shapeId);
            if (allocIt == _dist.end() || statsIt == _shapeStats.end())
                return; // shape 0 (null shape) has no stat rows -- nothing to allocate, by design

            std::vector<uint32> const& allocs = allocIt->second;
            std::vector<uint32> const& stats = statsIt->second;
            size_t n = std::min(allocs.size(), stats.size()); // a mismatch is already logged, §8 check 1

            for (size_t i = 0; i < n; ++i)
            {
                uint32 statType = stats[i];
                uint32 alloc = allocs[i];

                float cost = 1.0f;
                if (auto costIt = _statCost.find(statType); costIt != _statCost.end())
                    cost = costIt->second.Cost;

                double raw = sideBudget * (static_cast<double>(alloc) / 10000.0);
                double exact = (cost > 0.0f) ? raw / cost : 0.0;
                int32 flr = static_cast<int32>(std::floor(exact));

                working.push_back({statType, isPrimarySide, alloc, exact, flr, exact - static_cast<double>(flr)});
            }
        };

        allocateSide(row.PrimaryShapeId, primaryBudget, true);
        allocateSide(row.SecondaryShapeId, secondaryBudget, false);

        int32 floorSum = 0;
        double exactSum = 0.0;
        for (Working const& w : working)
        {
            floorSum += w.Floor;
            exactSum += w.Exact;
        }

        int32 target = static_cast<int32>(std::lround(exactSum));
        int32 remainder = std::max(0, target - floorSum);
        b.RoundingRemainderPoints = remainder;

        // Step 5: largest-remainder rounding, ONCE over the merged list of both sides. Explicit
        // tiebreak -- ascending stat_type -- as a secondary sort key: ties are common (any Even
        // pair/Lead-plus-two/Even trio shape produces exactly equal remainders on its
        // equal-allocation ranks), and std::sort does not preserve original order for equal
        // keys, so leaving this implicit would make the result depend on the sort
        // implementation rather than on this rule. §4.1.
        std::vector<size_t> order(working.size());
        std::iota(order.begin(), order.end(), 0);
        std::sort(order.begin(), order.end(), [&working](size_t lhs, size_t rhs)
        {
            if (working[lhs].Remainder != working[rhs].Remainder)
                return working[lhs].Remainder > working[rhs].Remainder;
            return working[lhs].StatType < working[rhs].StatType;
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
            detail.RawValue = static_cast<float>(w.Exact);
            detail.RoundedValue = w.Floor;
            b.Allocations.push_back(detail);
        }

        return true;
    }

    void ApplyItemizationAllocation(ItemTemplateContainer& itemTemplateStore)
    {
        uint32 applied = 0;

        for (auto const& [entry, row] : _itemization)
        {
            auto itemIt = itemTemplateStore.find(entry);
            if (itemIt == itemTemplateStore.end())
                continue; // already logged during validation

            ItemBudget::Breakdown b;
            if (!ResolveBudget(itemIt->second, row, b))
            {
                LOG_ERROR("server.loading", "item_itemization: could not resolve entry {}, leaving its item_template stats unmaterialized", entry);
                continue;
            }

            ItemTemplate& tpl = itemIt->second;

            if (b.Allocations.size() + 1 > static_cast<size_t>(MAX_ITEM_PROTO_STATS)) // +1 for off-budget stamina
            {
                LOG_ERROR("server.loading", "item_itemization: entry {} resolves to {} stats plus stamina, exceeding the {} available slots -- skipped", entry, b.Allocations.size(), MAX_ITEM_PROTO_STATS);
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

            if (b.HasBlockValueCurve)
                tpl.Block = static_cast<uint32>(b.FinalBlockValue);

            // Clear any on-equip spell whose effect got folded into the plain stat block above,
            // so it isn't granted twice.
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

        LOG_INFO("server.loading", ">> Materialized {} item itemization assignment(s)", applied);
    }
}

namespace ItemBudget
{
    void LoadAndApply(ItemTemplateContainer& itemTemplateStore)
    {
        uint32 oldMSTime = getMSTime();

        LoadItemizationData();
        ValidateItemizationData(itemTemplateStore);
        ApplyItemizationAllocation(itemTemplateStore);

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

        auto itemizationIt = _itemization.find(entry);
        if (itemizationIt == _itemization.end())
            return b; // Found but not Assigned -- caller reports "not a budget item"

        ResolveBudget(*tpl, itemizationIt->second, b);
        return b;
    }
}
