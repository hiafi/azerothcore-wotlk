"""
Crafting rework C7 follow-up (user 2026-11-12): the stock utility enchants as scrolls
(lib/crafting_utility_enchants_data.py, source/world/crafting_utility_enchants.py).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_utility_enchants.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import crafting_utility_enchants_data as U  # noqa: E402
from lib import source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
SOURCE_FILE = TOOL_ROOT / "source" / "world" / "crafting_utility_enchants.py"
SQUISH_FILE = TOOL_ROOT / "source" / "world" / "crafting_squish.py"
OLD_MATERIALS = set(U.SURVIVOR) | set(U.OUTLAND)


def _load() -> dict:
    items = {u.scroll: {"entry": u.scroll} for u in U.UTILITY}
    reg = registry.load_class_file(SOURCE_FILE, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, items),
                                   trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class UtilityEnchantsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dsl = _load()
        cls.spells = {s["id"]: s for s in cls.dsl["spells"]}

    def test_rows(self):
        self.assertEqual(len(U.UTILITY), 27)
        self.assertEqual(len({u.recipe for u in U.UTILITY}), 27)
        self.assertEqual(len({u.scroll for u in U.UTILITY}), 27)
        self.assertNotIn(25084, {u.recipe for u in U.UTILITY})  # retired: the T1 premium Subtlety
        for u in U.UTILITY:
            self.assertTrue(u.name.startswith("Enchant "), u.name)
            self.assertIn(u.slot, {"Boots", "Chest", "Cloak", "Gloves", "Shield"}, u.name)

    def test_recipes_create_the_scroll(self):
        for u in U.UTILITY:
            raw = self.spells[u.recipe]
            self.assertEqual(raw["effect1"]["type"], 24, u.name)
            self.assertEqual(raw["name"], f"Scroll of {u.name}")
            self.assertEqual(raw["raw_overrides"]["EffectItemType_1"], u.scroll, u.name)
            self.assertEqual(raw["raw_overrides"]["EquippedItemClass"], -1, u.name)
            self.assertNotIn("Targets", raw["raw_overrides"])  # no item target: no vellum
            reagents = {raw["raw_overrides"][f"Reagent_{n}"] for n in range(1, 9)
                        if raw["raw_overrides"].get(f"Reagent_{n}")}
            self.assertEqual(reagents, {item for item, _count in u.reagents}, u.name)
            self.assertFalse(reagents & OLD_MATERIALS, u.name)  # nothing that no longer drops

    def test_use_spells(self):
        edits = {row["entry"]: row for row in self.dsl["item_templates"]}
        for n, u in enumerate(U.UTILITY):
            use = U.use_spell(n)
            self.assertTrue(209000 <= use <= 209099)
            raw = self.spells[use]
            self.assertEqual((raw["effect1"]["type"], raw["effect1"]["misc_value"]), (53, u.enchant), u.name)
            self.assertEqual((raw["raw_overrides"]["EquippedItemClass"], raw["raw_overrides"]["EquippedItemSubclass"],
                              raw["raw_overrides"]["EquippedItemInvTypes"]), u.target, u.name)
            self.assertEqual(edits[u.scroll]["spellid_1"], use, u.name)
        crafting = IDS["reservations"]["crafting"]["spell"]
        self.assertTrue(all(crafting["start"] <= s <= crafting["end"] for s in self.spells if s >= 200000))

    def test_survivor_copy_matches_the_squish(self):
        text = SQUISH_FILE.read_text()
        block = text[text.index("SURVIVOR = {"):text.index("}", text.index("SURVIVOR = {"))]
        self.assertEqual(set(int(k) for k in re.findall(r"(\d+): ", block)), set(U.SURVIVOR))

    def test_not_declared_twice(self):
        text = SQUISH_FILE.read_text()
        for u in U.UTILITY:
            self.assertNotIn(f"    id={u.recipe},\n", text, u.name)


if __name__ == "__main__":
    unittest.main()
