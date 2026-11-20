"""
Crafting rework C4 (A1): an item whose `item_itemization.secondary_shape_id` is 0 and whose `item_template.RandomSuffix`
names a pool gets its secondaries from the random suffix. `budget.compute_breakdown` leaves the secondary budget
unspent and returns it as `suffix_factor` = 2 * round(S * r / 2), mirroring ItemBudget.cpp's ResolveBudget() (the
factor `GenerateEnchSuffixFactor` returns). Each half of a 5000/5000 suffix pair is then round(S * r / 2). r is the
level 60 secondary stat curve's ratio (`item_budget_curve.secondary_budget / budget`,
`.agents/plans/level60-stat-curve/`).

The r = 1 sizes are the ones `.agents/plans/crafting-rework/crafting-rework.C4-RESEARCH.md` section 7.1 computed from
the live curve (real reference tables, replayed from the repo, with `secondary_budget` set back to `budget`); the
secondary-curve sizes are the same items on the real tables.

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget, budget_overlay, shapes  # noqa: E402


def flat_curve_tables(tables: dict) -> dict:
    """`tables` with `item_budget_curve.secondary_budget` = `budget` at every ilvl (r = 1: the pre-curve formula)."""
    flat = dict(tables)
    flat["item_budget_curve"] = {k: {**row, "secondary_budget": row["budget"]}
                                 for k, row in tables["item_budget_curve"].items()}
    return flat

ARMOR, WEAPON = 4, 2
CLOTH, PLATE = 1, 4
RARE, EPIC = 3, 4
INV_CHEST, INV_WRIST, INV_FINGER, INV_WEAPON = 5, 9, 11, 13
NULL_SHAPE = 0
INT_SPIRIT_SP_INT_LEAD = 8  # a real primary shape
STRENGTH_SOLO = 22
CRIT_SOLO = 25  # a real secondary shape
POOL = 9000
TANK_POOL = 9001
BLOCK, DODGE, PARRY = 15, 13, 14


def _item(ilvl, quality, inv_type, item_class=ARMOR, subclass=CLOTH, random_suffix=POOL):
    return {
        "entry": 1, "ItemLevel": ilvl, "Quality": quality, "InventoryType": inv_type, "class": item_class,
        "subclass": subclass, "itemset": 0, "delay": 2600 if item_class == WEAPON else 0, "ArmorDamageModifier": 0,
        "RandomSuffix": random_suffix,
    }


def _itemization(primary=INT_SPIRIT_SP_INT_LEAD, secondary=NULL_SHAPE, share=6000):
    return {
        "entry": 1, "budget_mult": 1.0, "stamina_delta": 0, "dps_delta": 0.0, "absorbed_spell_slots": 0,
        "armor_delta": 0, "primary_shape_id": primary, "secondary_shape_id": secondary, "primary_share": share,
        "block_value_delta": 0,
    }


class SuffixFactorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = budget_overlay.get_all()
        cls.flat_tables = flat_curve_tables(cls.tables)
        cls.catalog = shapes.catalog(cls.tables)

    def _breakdown(self, item_row, itemization_row, flat=False):
        return budget.compute_breakdown(item_row, itemization_row, self.flat_tables if flat else self.tables,
                                        self.catalog)

    def test_marked_item_leaves_the_secondary_budget_for_the_suffix(self):
        b = self._breakdown(_item(60, EPIC, INV_CHEST), _itemization())
        self.assertTrue(b["suffix_secondaries"])
        self.assertEqual(b["suffix_ratio"], b["secondary_ratio"])  # the throughput pool rides the secondary curve
        self.assertEqual(b["suffix_factor"], 2 * budget._round(b["secondary_budget"] * b["secondary_ratio"] / 2.0))
        self.assertFalse([a for a in b["allocations"] if not a["is_primary"]], "shape 0 allocates no secondary")
        self.assertTrue([a for a in b["allocations"] if a["is_primary"]], "the primaries are still allocated")
        self.assertEqual(budget.suffix_stat_amount(b), b["suffix_factor"] // 2)

    def test_factor_is_even_and_each_half_rounds_the_half_share(self):
        for ilvl in (20, 35, 50, 60, 66, 76, 86, 96):
            for quality in (RARE, EPIC):
                b = self._breakdown(_item(ilvl, quality, INV_CHEST), _itemization())
                self.assertEqual(b["suffix_factor"] % 2, 0)
                half = b["secondary_budget"] * b["secondary_ratio"] / 2.0
                self.assertLessEqual(abs(budget.suffix_stat_amount(b) - half), 0.5 + 1e-9, (ilvl, quality))

    def test_sizes_match_the_research_table(self):
        # (ilvl, quality, slot) -> suffix stat total (both halves), primary_share 6000: C4-RESEARCH section 7.1 at
        # r = 1, then on the secondary curve.
        cases = [
            (20, RARE, INV_CHEST, 2, 4), (20, RARE, INV_WRIST, 2, 2), (35, EPIC, INV_CHEST, 8, 10),
            (35, EPIC, INV_WRIST, 4, 6), (50, RARE, INV_CHEST, 10, 14), (50, RARE, INV_WRIST, 6, 8),
            (60, EPIC, INV_CHEST, 18, 26), (60, EPIC, INV_WRIST, 10, 14), (76, EPIC, INV_CHEST, 22, 42),
            (76, EPIC, INV_WRIST, 12, 24), (96, EPIC, INV_CHEST, 26, 78), (96, EPIC, INV_WRIST, 14, 44),
        ]
        for ilvl, quality, inv_type, flat_total, total in cases:
            b = self._breakdown(_item(ilvl, quality, inv_type), _itemization(), flat=True)
            self.assertEqual(2 * budget.suffix_stat_amount(b), flat_total, (ilvl, quality, inv_type))
            b = self._breakdown(_item(ilvl, quality, inv_type), _itemization())
            self.assertEqual(2 * budget.suffix_stat_amount(b), total, (ilvl, quality, inv_type))

    def test_ring_suffix_is_the_whole_rounded_budget(self):
        # A ring (null primary, share 0) puts its whole budget in the suffix. The budget is rounded to a whole point
        # before the split (ResolveBudget's lround), so these differ from the research table, which used the
        # unrounded share: 35 Epic 10.7 -> budget 11 -> 12 (table 10), 50 Rare 14.7 -> 15 -> 16 (table 14). Second
        # number: on the secondary curve.
        for ilvl, quality, flat_total, total in ((20, RARE, 4, 6), (35, EPIC, 12, 16), (50, RARE, 16, 20),
                                                 (60, EPIC, 26, 36), (76, EPIC, 32, 58), (96, EPIC, 36, 110)):
            for flat, expected in ((True, flat_total), (False, total)):
                b = self._breakdown(_item(ilvl, quality, INV_FINGER), _itemization(primary=NULL_SHAPE, share=0),
                                    flat=flat)
                self.assertEqual(b["secondary_budget"], b["effective_budget"])
                self.assertEqual(2 * budget.suffix_stat_amount(b), expected, (ilvl, quality, flat))

    def test_one_hand_weapon_follows_the_budget_not_rand_prop_points(self):
        for flat, total in ((True, 10), (False, 14)):  # research 7.1: 1H at 60 E -> 10 at r = 1
            b = self._breakdown(_item(60, EPIC, INV_WEAPON, item_class=WEAPON, subclass=0),
                                _itemization(primary=STRENGTH_SOLO), flat=flat)
            self.assertTrue(b["suffix_secondaries"])
            self.assertEqual(2 * budget.suffix_stat_amount(b), total, flat)

    def test_no_suffix_pool_means_no_factor(self):
        b = self._breakdown(_item(60, EPIC, INV_CHEST, random_suffix=0), _itemization())
        self.assertFalse(b["suffix_secondaries"])
        self.assertEqual(b["suffix_factor"], 0)
        self.assertEqual(budget.suffix_stat_amount(b), 0)

    def test_real_secondary_shape_keeps_its_allocation_and_no_factor(self):
        b = self._breakdown(_item(60, EPIC, INV_CHEST), _itemization(secondary=CRIT_SOLO))
        self.assertFalse(b["suffix_secondaries"])
        self.assertEqual(b["suffix_factor"], 0)
        self.assertTrue([a for a in b["allocations"] if not a["is_primary"]])

    def test_primary_share_moves_the_suffix(self):
        sizes = {}
        for share in (4000, 6000, 8000):
            b = self._breakdown(_item(60, EPIC, INV_CHEST), _itemization(share=share))
            sizes[share] = b["suffix_factor"]
        self.assertGreater(sizes[4000], sizes[6000])
        self.assertGreater(sizes[6000], sizes[8000])
        self.assertGreater(sizes[8000], 0)

    def test_a_tiny_secondary_budget_still_gets_one_point_per_stat(self):
        # ilvl 1 Uncommon wrist: the secondary share is well below one point.
        b = self._breakdown(_item(1, 2, INV_WRIST), _itemization())
        self.assertLess(b["secondary_budget"], 1.0)
        self.assertEqual(b["suffix_factor"], 2)
        self.assertEqual(budget.suffix_stat_amount(b), 1)

    def test_pool_stats(self):
        self.assertEqual(budget.suffix_pool_stats(POOL, self.tables), {32, 36, 22, 23, 24, 33})
        self.assertEqual(budget.suffix_pool_stats(TANK_POOL, self.tables), {BLOCK, DODGE, PARRY, 22, 23})
        self.assertTrue(budget.suffix_pool_rides_secondary_curve(POOL, self.tables))
        # The tank pool mixes Block / Dodge / Parry (flag 0) with Mastery / Versatility: the conservative reading keeps
        # the whole pool on the primary curve (level 60 secondary curve, LS1b).
        self.assertFalse(budget.suffix_pool_rides_secondary_curve(TANK_POOL, self.tables))
        self.assertFalse(budget.suffix_pool_rides_secondary_curve(123456, self.tables))  # no such pool

    def test_tank_pool_keeps_todays_factor(self):
        for ilvl in (35, 60, 76, 96):
            for inv_type in (INV_CHEST, INV_WRIST):
                item = _item(ilvl, EPIC, inv_type, subclass=PLATE, random_suffix=TANK_POOL)
                b = self._breakdown(item, _itemization(primary=STRENGTH_SOLO))
                flat = self._breakdown(item, _itemization(primary=STRENGTH_SOLO), flat=True)
                self.assertEqual(b["suffix_ratio"], 1.0)
                self.assertGreater(b["secondary_ratio"], 1.0)
                self.assertEqual(b["suffix_factor"], flat["suffix_factor"], (ilvl, inv_type))
                self.assertEqual(b["suffix_factor"], max(2, 2 * budget._round(b["secondary_budget"] / 2.0)))

    def test_only_a_pure_secondary_curve_pool_scales(self):
        # A hand-built pool: one suffix of Crit + Haste (scales), then the same pool with the Dodge/Parry suffix added
        # (does not), then that suffix at chance 0 (never rolled, LoadRandomEnchantmentsTable: scales again).
        def pool(*rows):
            return {**self.tables, "item_enchantment_template": {
                (1, ench): {"entry": 1, "ench": ench, "chance": chance} for ench, chance in rows}}

        self.assertTrue(budget.suffix_pool_rides_secondary_curve(1, pool((1000, 50.0))))
        self.assertFalse(budget.suffix_pool_rides_secondary_curve(1, pool((1000, 50.0), (1017, 50.0))))
        self.assertTrue(budget.suffix_pool_rides_secondary_curve(1, pool((1000, 50.0), (1017, 0.0))))

    def test_a_suffix_missing_from_the_dbc_table_is_refused(self):
        missing = {(1, 99999): {"entry": 1, "ench": 99999, "chance": 100.0}}
        tables = {**self.tables, "item_enchantment_template": missing}
        with self.assertRaises(budget.BudgetError):
            budget.suffix_pool_stats(1, tables)

    def test_rounding_is_half_away_from_zero(self):
        # The C++ uses std::lround; budget._round mirrors it (Python's round() is half-to-even).
        self.assertEqual(budget._round(2.5), 3)
        self.assertEqual(budget._round(3.5), 4)
        self.assertEqual(budget._round(0.49), 0)


if __name__ == "__main__":
    unittest.main()
