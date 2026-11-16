"""
Blackrock gear: the real repo's budget replay sees the twelve shapes the Blackrock Spire, Blackrock Depths and Molten
set items need (pending itemization_templates_v2 SQL, ids 84-95): Even pairs (and one Even trio) with the stock
avoidance rules (Dodge needs Agility or Strength, Parry and Block Strength).

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests -p 'test_shapes_blackrock.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, shapes  # noqa: E402

STR, AGI, INT, SPI = 4, 3, 5, 6
DODGE, PARRY, BLOCK, MASTERY, VERS, CDH, PROC, HASTE = 13, 14, 15, 22, 23, 24, 33, 36

PAIRS = {
    84: ("Mastery/CDH", [MASTERY, CDH]),
    85: ("Versatility/Proc", [VERS, PROC]),
    86: ("Proc/CDH", [PROC, CDH]),
    87: ("Dodge/Versatility", [DODGE, VERS]),
    88: ("Dodge/CDH", [DODGE, CDH]),
    89: ("Dodge/Mastery (Any)", [DODGE, MASTERY]),
    90: ("Parry/Haste", [PARRY, HASTE]),
    91: ("Block/Versatility", [BLOCK, VERS]),
    92: ("Block/CDH", [BLOCK, CDH]),
    93: ("Block/Mastery", [BLOCK, MASTERY]),
    94: ("Block/Haste", [BLOCK, HASTE]),
}


class BlackrockShapesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = shapes.catalog(budget_overlay.get_all())

    def test_the_pairs(self):
        for shape_id, (name, stats) in PAIRS.items():
            shape = self.catalog[shape_id]
            self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]),
                             (name, shapes.KIND_SECONDARY, "Even pair"), shape_id)
            self.assertEqual(shape["stats"], stats, shape_id)
            self.assertEqual(shape["dist_id"], self.catalog[33]["dist_id"], shape_id)

    def test_the_trio(self):
        shape = self.catalog[95]
        self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]),
                         ("Haste/Mastery/Proc", shapes.KIND_SECONDARY, "Even trio"))
        self.assertEqual(shape["stats"], [HASTE, MASTERY, PROC])
        self.assertEqual(shape["dist_id"], self.catalog[42]["dist_id"])

    def test_primary_rules_match_the_stock_shapes(self):
        for shape_id in (87, 88):  # Dodge: Agility or Strength, like 57-59
            for primary in ({AGI}, {STR}):
                self.assertTrue(shapes.rules_satisfied(self.catalog[shape_id], primary), shape_id)
            for primary in ({INT}, {SPI}, set()):
                self.assertFalse(shapes.rules_satisfied(self.catalog[shape_id], primary), shape_id)
        for shape_id in (90, 91, 92, 93, 94):  # Parry and Block: Strength, like 60 and 61
            self.assertTrue(shapes.rules_satisfied(self.catalog[shape_id], {STR}), shape_id)
            for primary in ({AGI}, {INT}, {SPI}, set()):
                self.assertFalse(shapes.rules_satisfied(self.catalog[shape_id], primary), shape_id)
        for shape_id in (84, 85, 86, 89, 95):  # no rule: jewelry and the "Any" copy
            for primary in (set(), {SPI}, {STR}, {AGI}, {INT}):
                self.assertTrue(shapes.rules_satisfied(self.catalog[shape_id], primary), shape_id)


if __name__ == "__main__":
    unittest.main()
