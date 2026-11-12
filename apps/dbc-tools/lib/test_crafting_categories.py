"""
Crafting rework C7-UI, the trade skill category table (write_crafting_categories.py): one header per set and
profession, in level order (user 2026-11-12: Wool first, Runecloth last), every set recipe in it.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_categories.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_crafting_categories as W  # noqa: E402
from lib import crafting_sets_data as T  # noqa: E402


def _headers(table: dict, profession: int) -> list[str]:
    """The profession's headers in the order the client override shows them (lowest order first)."""
    first: dict[str, int] = {}
    for row in T.recipes():
        if row.item.profession == profession:
            name, order = table[row.spell]
            first[name] = min(order, first.get(name, order))
    return sorted(first, key=first.get)


class CategoriesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.table = W.categories()

    def test_every_recipe_has_a_category(self):
        self.assertEqual(set(self.table), {row.spell for row in T.recipes()})
        orders = [order for _name, order in self.table.values()]
        self.assertEqual(sorted(orders), list(range(1, len(orders) + 1)))

    def test_headers_in_level_order(self):
        self.assertEqual(_headers(self.table, T.TAILORING),
                         ["Wool", "Silk", "Mageweave", "Runecloth", "Molten", "Draconic", "Chthonic"])
        self.assertEqual(_headers(self.table, T.LEATHERWORKING)[:4],
                         ["Medium Leather", "Heavy Leather", "Thick Leather", "Rugged Leather"])
        self.assertEqual(_headers(self.table, T.BLACKSMITHING)[:4], ["Bronze", "Steel", "Mithril", "Thorium"])
        for profession in T.CATEGORY_NAME:
            self.assertEqual(len(_headers(self.table, profession)), len(T.SETS), profession)

    def test_a_header_holds_one_set(self):
        for row in T.recipes():
            name, _order = self.table[row.spell]
            self.assertEqual(name, T.category_name(row.item.profession, row.item.set.key))

    def test_own_armor_first(self):
        """Leatherworking's leather and mail come before the cloth and plate waists, the backs after the cloth."""
        in_set = [row for row in T.recipes() if row.item.set.key == "s15" and row.item.profession == T.LEATHERWORKING]
        ordered = sorted(in_set, key=lambda row: self.table[row.spell][1])
        armors = [row.item.armor for row in ordered]
        self.assertEqual(armors[0], "leather")
        self.assertEqual(armors[-5:], ["cloth"] * 2 + ["plate"] * 3)  # two cloth and three plate archetypes
        tailoring = sorted((row for row in T.recipes() if row.item.set.key == "s15"
                            and row.item.profession == T.TAILORING), key=lambda row: self.table[row.spell][1])
        self.assertIsNotNone(tailoring[0].item.armor)
        self.assertIsNone(tailoring[-1].item.armor)

    def test_render(self):
        text = W.render_lua(self.table)
        self.assertIn('    [207600] = { "', text)
        self.assertTrue(text.startswith("-- Generated"))
        self.assertTrue(text.endswith("}\n"))
        self.assertNotIn("\r", text)
        with self.assertRaises(ValueError):
            W.render_lua({1: ('bad"name', 1)})


if __name__ == "__main__":
    unittest.main()
