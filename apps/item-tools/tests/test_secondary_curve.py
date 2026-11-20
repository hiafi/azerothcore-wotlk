"""
Level 60 secondary stat curve (`.agents/plans/level60-stat-curve/` HANDOFF 1.2-1.4): `budget.compute_breakdown`
multiplies the exact value of each secondary-side stat with `item_stat_cost.budget_curve` 1 by
r = `item_budget_curve.secondary_budget / budget`, and rounds those stats again over the item's new exact total. Every
other number on the item must come out as it did before the curve, which these tests check against the pre-curve
`budget.py` (commit `LEGACY_COMMIT`, read with `git show`) on every itemized item at ilvl 40-101 of the real replayed
tables.

    apps/dbc-tools/.venv/bin/python3 -m pytest -q apps/item-tools/tests/test_secondary_curve.py
"""

from __future__ import annotations

import subprocess
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget, budget_overlay, overlay, shapes  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
LEGACY_COMMIT = "81d92fc05"  # Playerbot before the secondary curve (#151)
LEGACY_PATH = "apps/item-tools/item_lib/budget.py"

# Dodge, Parry, Block, Mastery, Versatility, CDH, Crit, Proc, Haste, ArP (HANDOFF 1.3 + 1.10)
SECONDARY_CURVE_STATS = {13, 14, 15, 22, 23, 24, 32, 33, 36, 44}
PRIMARY_CURVE_SECONDARIES = {43}  # MP5
DODGE, VERSATILITY, CRIT, MP5 = 13, 23, 32, 43
DODGE_VERSATILITY_ANY = 98  # secondary shape "Dodge/Versatility (Any)", Even pair
MP5_CRIT = 48  # secondary shape "MP5/Crit", Even pair (no MP5/Versatility shape exists); forbids Spirit
STRENGTH_SOLO = 22  # primary shape
INTELLECT_SOLO = 24  # primary shape, no Spirit (MP5/Crit's rule)
ARMOR, PLATE, EPIC, INV_CHEST = 4, 4, 4, 5

OFF_BUDGET_KEYS = ("final_stamina", "has_armor_curve", "final_armor", "has_block_value_curve", "final_block_value",
                   "final_dps", "dmg_min", "dmg_max", "weapon_spell_power", "budget", "effective_budget",
                   "primary_budget", "secondary_budget")


def flat_curve_tables(tables: dict) -> dict:
    """`tables` with `secondary_budget` = `budget` at every ilvl: r = 1, the formula before the secondary curve."""
    flat = dict(tables)
    flat["item_budget_curve"] = {k: {**row, "secondary_budget": row["budget"]}
                                 for k, row in tables["item_budget_curve"].items()}
    return flat


def legacy_budget_module():
    """The pre-curve `item_lib/budget.py`, loaded from git as `item_lib._budget_legacy` (None without git)."""
    try:
        source = subprocess.run(["git", "show", f"{LEGACY_COMMIT}:{LEGACY_PATH}"], cwd=REPO_ROOT, check=True,
                                capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    module = types.ModuleType("item_lib._budget_legacy")
    module.__package__ = "item_lib"
    exec(compile(source, f"{LEGACY_COMMIT}:{LEGACY_PATH}", "exec"), module.__dict__)  # noqa: S102
    return module


def _has_sockets(item_row: dict) -> bool:
    return any(item_row.get(f"socketColor_{n}") for n in (1, 2, 3))


class SecondaryCurveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = legacy_budget_module()
        cls.tables = budget_overlay.get_all()
        cls.flat_tables = flat_curve_tables(cls.tables)
        cls.catalog = shapes.catalog(cls.tables)
        items = overlay.get_rows()
        cls.sample = []
        for (entry,), itemization in sorted(cls.tables["item_itemization"].items()):
            item_row = items.get(entry)
            if item_row is None or not 40 <= int(item_row["ItemLevel"]) <= 101:
                continue
            try:
                budget.compute_breakdown(item_row, itemization, cls.tables, cls.catalog)
            except budget.BudgetError:
                continue
            cls.sample.append((item_row, itemization))

    def setUp(self):
        if self.legacy is None:
            self.skipTest(f"git show {LEGACY_COMMIT} is not available")

    def _pairs(self):
        for item_row, itemization in self.sample:
            new = budget.compute_breakdown(item_row, itemization, self.tables, self.catalog)
            old = self.legacy.compute_breakdown(item_row, itemization, self.tables, self.catalog)
            yield item_row, itemization, new, old

    def test_the_sample_covers_every_case(self):
        rows = [(item, itemization) for item, itemization in self.sample]
        self.assertGreaterEqual(len(rows), 200)
        cases = {
            "sockets": any(_has_sockets(item) for item, _ in rows),
            "stamina_delta": any(z["stamina_delta"] for _, z in rows),
            "dps_delta": any(z["dps_delta"] for _, z in rows),
            "spell power stripped": any((z.get("spell_power_per_dps") or 0) > 0 for _, z in rows),
            "random suffix": any(z["secondary_shape_id"] == 0 and item.get("RandomSuffix") for item, z in rows),
            "a scaled stat": any(set(self.catalog[z["secondary_shape_id"]]["stats"]) & SECONDARY_CURVE_STATS
                                 for _, z in rows if z["secondary_shape_id"] in self.catalog),
            "a flag-0 secondary": any(set(self.catalog[z["secondary_shape_id"]]["stats"]) & PRIMARY_CURVE_SECONDARIES
                                      for _, z in rows if z["secondary_shape_id"] in self.catalog),
        }
        self.assertEqual([name for name, found in cases.items() if not found], [])

    def test_primary_side_and_flag_0_stats_are_unchanged(self):
        for item_row, _, new, old in self._pairs():
            entry = item_row["entry"]
            self.assertEqual(len(new["allocations"]), len(old["allocations"]), entry)
            for a_new, a_old in zip(new["allocations"], old["allocations"]):
                self.assertEqual((a_new["stat_type"], a_new["is_primary"]), (a_old["stat_type"], a_old["is_primary"]))
                if a_new["scaled"]:
                    continue
                self.assertEqual(a_new["rounded"], a_old["rounded"], (entry, a_new["stat_type"]))
                self.assertEqual(a_new["raw"], a_old["raw"], (entry, a_new["stat_type"]))
            for key in OFF_BUDGET_KEYS:
                self.assertEqual(new.get(key), old.get(key), (entry, key))

    def test_only_secondary_curve_stats_on_the_secondary_side_scale(self):
        for item_row, _, new, _old in self._pairs():
            for a in new["allocations"]:
                expected = not a["is_primary"] and a["stat_type"] in SECONDARY_CURVE_STATS
                self.assertEqual(a["scaled"], expected, (item_row["entry"], a["stat_type"]))

    def test_scaled_stats_follow_r(self):
        for item_row, _, new, old in self._pairs():
            ratio = new["secondary_ratio"]
            self.assertEqual(ratio, new["curve_secondary_budget"] / new["curve_budget"])
            for a_new, a_old in zip(new["allocations"], old["allocations"]):
                if a_new["scaled"]:
                    self.assertEqual(a_new["raw"], a_old["raw"] * ratio, item_row["entry"])
                    self.assertLess(abs(a_new["rounded"] - a_new["raw"]), 1.0, item_row["entry"])

    def test_scaled_stats_round_their_own_exact_total(self):
        for item_row, _, new, _old in self._pairs():
            scaled = [a for a in new["allocations"] if a["scaled"]]
            if not scaled:
                continue
            floors = sum(int(a["raw"] // 1) for a in scaled)
            exact = 0.0
            for a in scaled:  # a plain left-to-right sum, as the C++ adds (Python 3.12's sum() compensates)
                exact += a["raw"]
            self.assertEqual(sum(a["rounded"] for a in scaled), max(floors, budget._round(exact)), item_row["entry"])

    def test_r_1_reproduces_the_old_formula_exactly(self):
        for item_row, itemization in self.sample:
            new = budget.compute_breakdown(item_row, itemization, self.flat_tables, self.catalog)
            old = self.legacy.compute_breakdown(item_row, itemization, self.tables, self.catalog)
            self.assertEqual(new["secondary_ratio"], 1.0)
            self.assertEqual([(a["stat_type"], a["raw"], a["rounded"]) for a in new["allocations"]],
                             [(a["stat_type"], a["raw"], a["rounded"]) for a in old["allocations"]], item_row["entry"])
            self.assertEqual(new["suffix_factor"], old["suffix_factor"], item_row["entry"])
            self.assertEqual(budget.materialized_item_fields(new), self.legacy.materialized_item_fields(old),
                             item_row["entry"])

    def test_suffix_factor_scales_by_r(self):
        suffix_items = [(item, z) for item, z in self.sample
                        if z["secondary_shape_id"] == 0 and item.get("RandomSuffix")]
        self.assertTrue(suffix_items)
        for item_row, itemization in suffix_items:
            b = budget.compute_breakdown(item_row, itemization, self.tables, self.catalog)
            # Both pools grant only secondary-curve stats since HANDOFF 1.10 (the tank pool 9001: Block, Dodge, Parry,
            # Mastery, Versatility), so both take r.
            self.assertIn(item_row["RandomSuffix"], (9000, 9001), item_row["entry"])
            ratio = b["secondary_ratio"]
            self.assertEqual(b["suffix_ratio"], ratio, item_row["entry"])
            self.assertEqual(b["suffix_factor"], max(2, 2 * budget._round(b["secondary_budget"] * ratio / 2.0)))

    def _ilvl_96_chest(self, primary, secondary, flat=False):
        item_row = {
            "entry": 1, "ItemLevel": 96, "Quality": EPIC, "InventoryType": INV_CHEST, "class": ARMOR,
            "subclass": PLATE, "itemset": 0, "delay": 0, "ArmorDamageModifier": 0, "RandomSuffix": 0,
        }
        itemization = {
            "entry": 1, "budget_mult": 1.0, "stamina_delta": 0, "dps_delta": 0.0, "absorbed_spell_slots": 0,
            "armor_delta": 0, "primary_shape_id": primary, "secondary_shape_id": secondary,
            "primary_share": 6000, "block_value_delta": 0,
        }
        b = budget.compute_breakdown(item_row, itemization, self.flat_tables if flat else self.tables, self.catalog)
        return b, {a["stat_type"]: a for a in b["allocations"] if not a["is_primary"]}

    def test_mp5_crit_scales_only_the_crit(self):
        # MP5 is the one flag-0 secondary left (HANDOFF 1.10): it keeps today's points beside a scaled stat.
        self.assertEqual(self.catalog[MP5_CRIT]["stats"], [MP5, CRIT])
        new, values = self._ilvl_96_chest(INTELLECT_SOLO, MP5_CRIT)
        _flat, flat_values = self._ilvl_96_chest(INTELLECT_SOLO, MP5_CRIT, flat=True)
        self.assertAlmostEqual(new["secondary_ratio"], 194 / 64)
        self.assertEqual(values[MP5]["rounded"], flat_values[MP5]["rounded"])
        self.assertFalse(values[MP5]["scaled"])
        self.assertTrue(values[CRIT]["scaled"])
        self.assertEqual(values[CRIT]["raw"], flat_values[CRIT]["raw"] * new["secondary_ratio"])
        self.assertGreater(values[CRIT]["rounded"], 2.9 * flat_values[CRIT]["rounded"])

    def test_dodge_versatility_scales_both(self):
        # Dodge, Parry and Block ride the secondary curve since HANDOFF 1.10.
        self.assertEqual(self.catalog[DODGE_VERSATILITY_ANY]["stats"], [DODGE, VERSATILITY])
        new, values = self._ilvl_96_chest(STRENGTH_SOLO, DODGE_VERSATILITY_ANY)
        _flat, flat_values = self._ilvl_96_chest(STRENGTH_SOLO, DODGE_VERSATILITY_ANY, flat=True)
        for stat in (DODGE, VERSATILITY):
            self.assertTrue(values[stat]["scaled"], stat)
            self.assertEqual(values[stat]["raw"], flat_values[stat]["raw"] * new["secondary_ratio"], stat)
            self.assertGreater(values[stat]["rounded"], 2.9 * flat_values[stat]["rounded"], stat)

    def test_curve_spot_values(self):
        curve = self.tables["item_budget_curve"]
        spots = {59: 54, 60: 65, 66: 78, 76: 105, 86: 143, 96: 194, 101: 226, 115: 226, 120: 251, 165: 646,
                 171: 733, 187: 733, 200: 937, 245: 2198, 251: 2464}
        for ilvl, value in spots.items():
            self.assertLessEqual(abs(curve[(ilvl,)]["secondary_budget"] - value), 1, ilvl)
        self.assertEqual(len(curve), 300)
        self.assertTrue(all(row["secondary_budget"] > 0 for row in curve.values()))

    def test_stat_flags(self):
        flags = {k[0]: row["budget_curve"] for k, row in self.tables["item_stat_cost"].items()}
        self.assertEqual({stat for stat, flag in flags.items() if flag == 1}, SECONDARY_CURVE_STATS)


if __name__ == "__main__":
    unittest.main()
