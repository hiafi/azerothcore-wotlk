"""
Scarlet Monastery gear: the real repo's budget replay sees the four shapes the Scarlet Monastery list items and the
Zealot's set need (pending itemization_templates_v2 SQL, ids 96-99): two Even trios and two Even pairs with the stock
avoidance rules (Parry and Block Strength, the Dodge "Any" copy no rule).

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests -p 'test_shapes_scarlet.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, shapes  # noqa: E402

STR, AGI, INT, SPI = 4, 3, 5, 6
DODGE, PARRY, BLOCK, MASTERY, VERS, CDH = 13, 14, 15, 22, 23, 24

TRIOS = {
    96: ("Block/Parry/Versatility", [BLOCK, PARRY, VERS]),
    97: ("Block/Mastery/Versatility", [BLOCK, MASTERY, VERS]),
}
PAIRS = {
    98: ("Dodge/Versatility (Any)", [DODGE, VERS]),
    99: ("Parry/CDH", [PARRY, CDH]),
}


class ScarletShapesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = shapes.catalog(budget_overlay.get_all())

    def test_the_trios(self):
        for shape_id, (name, stats) in TRIOS.items():
            shape = self.catalog[shape_id]
            self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]),
                             (name, shapes.KIND_SECONDARY, "Even trio"), shape_id)
            self.assertEqual(shape["stats"], stats, shape_id)
            self.assertEqual(shape["dist_id"], self.catalog[42]["dist_id"], shape_id)

    def test_the_pairs(self):
        for shape_id, (name, stats) in PAIRS.items():
            shape = self.catalog[shape_id]
            self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]),
                             (name, shapes.KIND_SECONDARY, "Even pair"), shape_id)
            self.assertEqual(shape["stats"], stats, shape_id)
            self.assertEqual(shape["dist_id"], self.catalog[33]["dist_id"], shape_id)

    def test_primary_rules_match_the_stock_shapes(self):
        for shape_id in (96, 97, 99):  # Parry and Block: Strength, like 60 and 61
            self.assertTrue(shapes.rules_satisfied(self.catalog[shape_id], {STR}), shape_id)
            for primary in ({AGI}, {INT}, {SPI}, set()):
                self.assertFalse(shapes.rules_satisfied(self.catalog[shape_id], primary), shape_id)
        for primary in (set(), {SPI}, {STR}, {AGI}, {INT}):  # the "Any" copy: no rule
            self.assertTrue(shapes.rules_satisfied(self.catalog[98], primary))


if __name__ == "__main__":
    unittest.main()
