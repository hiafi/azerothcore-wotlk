"""
Item variants, Haunted dungeon set: the real repo's budget replay sees the four two-secondary shapes the Haunted set
pieces need (pending itemization_templates_v2 SQL): Mastery/Proc (75), Parry/Mastery (76), Parry/Proc (77) and
Dodge/Proc (78), Even distribution, with the stock avoidance rules (Parry needs Strength, Dodge Agility or Strength).

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests -p 'test_shapes_haunted.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget_overlay, shapes  # noqa: E402

STR, AGI, INT, SPI = 4, 3, 5, 6
DODGE, PARRY, MASTERY, PROC = 13, 14, 22, 33


class HauntedShapesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = shapes.catalog(budget_overlay.get_all())

    def _pair(self, shape_id, name, stats):
        shape = self.catalog[shape_id]
        self.assertEqual((shape["name"], shape["kind"], shape["dist_name"]), (name, shapes.KIND_SECONDARY, "Even pair"))
        self.assertEqual(shape["stats"], stats)
        self.assertEqual(shape["dist_id"], self.catalog[33]["dist_id"])  # Haste/Mastery, the stock pair

    def test_the_four_shapes(self):
        self._pair(75, "Mastery/Proc", [MASTERY, PROC])
        self._pair(76, "Parry/Mastery", [PARRY, MASTERY])
        self._pair(77, "Parry/Proc", [PARRY, PROC])
        self._pair(78, "Dodge/Proc", [DODGE, PROC])

    def test_avoidance_rules_match_the_stock_shapes(self):
        rules = {sid: shapes.rules_satisfied(self.catalog[sid], {STR}) for sid in (60, 76, 77)}
        self.assertTrue(all(rules.values()))
        for primary in ({AGI}, {INT}, {SPI}, set()):
            self.assertFalse(shapes.rules_satisfied(self.catalog[76], primary))
            self.assertFalse(shapes.rules_satisfied(self.catalog[77], primary))
        for primary in ({AGI}, {STR}):
            self.assertTrue(shapes.rules_satisfied(self.catalog[78], primary))
        for primary in ({INT}, {SPI}, set()):
            self.assertFalse(shapes.rules_satisfied(self.catalog[78], primary))
        for primary in (set(), {SPI}, {STR}, {AGI}, {INT}):
            self.assertTrue(shapes.rules_satisfied(self.catalog[75], primary))


if __name__ == "__main__":
    unittest.main()
