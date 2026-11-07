"""
Item variants IV0: the real repo's budget replay sees the three Solo shapes added by the IV0 pending migration and the
`item_budget_variant.tier` column.

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, shapes  # noqa: E402

STAT_SPIRIT, STAT_CDH, STAT_PROC = 6, 24, 33


class Iv0ShapesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = shapes.catalog(budget_overlay.get_all())

    def _solo(self, shape_id, name, kind, stat):
        shape = self.catalog[shape_id]
        self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]), (name, kind, "Solo"))
        self.assertEqual((shape["stats"], shape["alloc"], shape["rules"]), ([stat], [10000], []))

    def test_spirit_solo_is_a_primary_shape_like_strength_solo(self):
        self._solo(71, "Spirit (Solo)", shapes.KIND_PRIMARY, STAT_SPIRIT)
        self.assertIn(71, shapes.primary_shapes(budget_overlay.get_all()))
        self.assertEqual(self.catalog[22]["dist_id"], self.catalog[71]["dist_id"])

    def test_cdh_and_proc_solo_are_secondary_shapes_like_crit_solo(self):
        self._solo(72, "CDH (Solo)", shapes.KIND_SECONDARY, STAT_CDH)
        self._solo(73, "Proc (Solo)", shapes.KIND_SECONDARY, STAT_PROC)
        secondary = shapes.secondary_shapes(budget_overlay.get_all())
        self.assertIn(72, secondary)
        self.assertIn(73, secondary)
        self.assertEqual(self.catalog[25]["dist_id"], self.catalog[72]["dist_id"])

    def test_the_new_secondary_shapes_are_open_to_every_primary(self):
        for shape_id in (72, 73):
            for primary in (set(), {STAT_SPIRIT}, {4}, {5}):
                self.assertTrue(shapes.rules_satisfied(self.catalog[shape_id], primary))

    def test_shape_ids_are_unique_and_the_old_catalog_is_intact(self):
        self.assertGreaterEqual(max(self.catalog), 73)  # later stages add shapes above 73 (74 wave 1, 75-78 Haunted)
        for shape_id in range(0, 74):
            self.assertIn(shape_id, self.catalog)

    def test_item_budget_variant_has_the_tier_column(self):
        self.assertEqual(budget_overlay.table_columns("item_budget_variant"), ["entry", "base_entry", "tier"])


if __name__ == "__main__":
    unittest.main()
