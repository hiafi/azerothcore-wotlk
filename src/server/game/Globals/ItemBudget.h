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

#ifndef AC_ITEM_BUDGET_H
#define AC_ITEM_BUDGET_H

#include "ItemTemplate.h"
#include <vector>

// Percentage-allocation itemization system. See docs/itemization-changes.md.
//
// Items assigned in `item_budget_assign` store no literal stats of their
// own in the materialized ItemTemplate -- their stat line is computed from
// item level, slot, quality, and an allocation template, then overwritten
// into ItemTemplate::ItemStat[]/StatsCount (and Damage[] for weapons) once,
// at startup. Everything downstream (item query packets, tooltips, the
// auction house, loot windows) reads the materialized result and has no
// idea this system exists.
namespace ItemBudget
{
    // Called once from ObjectMgr::LoadItemTemplates(), after the main load
    // loop and the _itemTemplateStoreFast rebuild. Loads the reference
    // tables and template/assignment data, validates it (logs and skips
    // what it can't resolve), and overwrites every assigned item's stats
    // in place.
    void LoadAndApply(ItemTemplateContainer& itemTemplateStore);

    // One resolved stat allocation, for the `.item budget` debug command.
    struct AllocationDetail
    {
        uint32 StatType = 0;
        bool IsPrimary = false;
        uint32 Alloc = 0;      // ten-thousandths, from the template
        float RawValue = 0.0f; // before rounding
        int32 RoundedValue = 0;
    };

    // Full breakdown of one item's resolved budget. Recomputed on demand
    // from the same resident reference data the startup pass used --
    // nothing here is cached from materialization time.
    struct Breakdown
    {
        bool Found = false;
        bool Assigned = false; // false if the entry has no item_budget_assign row
        uint32 Entry = 0;
        uint32 TemplateId = 0;
        uint32 ItemLevel = 0;
        uint32 Quality = 0;
        uint32 InventoryType = 0;
        bool IsWeapon = false;

        float SlotMult = 0.0f;
        float QualityMult = 0.0f;
        float BudgetMult = 0.0f;     // author-set base, from item_budget_assign
        uint32 SocketCount = 0;
        float SocketDiscount = 1.0f; // product of per-socket discounts
        bool IsSetPiece = false;
        float SetDiscount = 1.0f;
        float EffectiveMult = 0.0f;  // BudgetMult * SocketDiscount * SetDiscount
        int32 Budget = 0;            // curve(ilvl) * SlotMult * QualityMult * EffectiveMult

        int32 StaminaDelta = 0;
        int32 BaselineStamina = 0;
        int32 FinalStamina = 0;

        // Armor: off-budget like Stamina, but never funded from the item's
        // budget -- see §9.3. HasArmorCurve is false for items whose
        // class/subclass has no item_armor_curve entry (non-armor-class
        // items, shields, rings/necks/trinkets) -- Armor is left untouched
        // for those, same as any unassigned item.
        bool HasArmorCurve = false;
        uint32 ArmorClass = 0;
        int32 ArmorDelta = 0;
        int32 BaselineArmor = 0;
        int32 FinalArmor = 0;

        float DpsDelta = 0.0f;
        float BaselineDps = 0.0f;
        float FinalDps = 0.0f;
        float DmgMin = 0.0f;
        float DmgMax = 0.0f;

        int32 EffectiveBudget = 0;   // Budget minus the cost of every applicable delta

        std::vector<AllocationDetail> Allocations;
        int32 RoundingRemainderPoints = 0; // how many points largest-remainder distributed

        // Bitmask, bit i = Spells[i] (spellid_(i+1) in item_template) gets
        // cleared at materialization time -- its effect has been folded
        // into a plain stat above instead. See §9.8's "absorbing" an
        // on-equip spell into the stat block.
        uint32 AbsorbedSpellSlots = 0;
    };

    // Read-only recompute for the debug command. Does not require the item
    // to have already been materialized this session.
    Breakdown ComputeBreakdown(uint32 entry);
}

#endif
