"""
Crafting rework C7, crafted sets (.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decisions 2 and 3,
ruled 2026-11-12): the data (lib/crafting_sets_data.py), the item and recipe declarations
(source/items/crafting_sets.py, source/world/crafting_sets.py) and the hand-written rows (write_crafting_set_items.py).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_sets.py
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_crafting_set_items as W  # noqa: E402
from lib import crafting_sets_data as T  # noqa: E402
from lib import item_key_refs, source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
ITEMS_FILE = TOOL_ROOT / "source" / "items" / "crafting_sets.py"
RECIPES_FILE = TOOL_ROOT / "source" / "world" / "crafting_sets.py"
PER_SET = 10 * 8 + len(T.OTHERS)


def _in(block: dict, value: int) -> bool:
    return block["start"] <= value <= block["end"]


def _load(path: Path) -> dict:
    reg = registry.load_class_file(path, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, {}),
                                   trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class SetsDataTest(unittest.TestCase):
    """The catalog."""

    @classmethod
    def setUpClass(cls):
        cls.items = T.items()

    def test_catalog_size(self):
        self.assertEqual(len(self.items), 7 * PER_SET)
        self.assertEqual(len({i.key for i in self.items}), len(self.items))
        self.assertEqual(Counter(i.set.key for i in self.items), {s.key: PER_SET for s in T.SETS})
        for craft_set in T.SETS:
            for arch in T.ARCHETYPES:
                slots = {i.slot for i in self.items if i.set is craft_set and i.key.endswith(
                    tuple(f"_{arch.key}_{slot}" for slot in T.ARMOR_SLOTS))}
                self.assertEqual(slots, set(T.ARMOR_SLOTS), (craft_set.key, arch.key))

    def test_owners_per_slot(self):
        """R23: the armor type's profession makes the main slots; Leatherworking every Waist, Blacksmithing every
        Wrist, Tailoring every Back."""
        for item in self.items:
            if item.armor is None:
                continue
            want = {"waist": T.LEATHERWORKING, "wrist": T.BLACKSMITHING}.get(item.slot,
                                                                              T.ARMOR_PROFESSION[item.armor])
            self.assertEqual(item.profession, want, item.key)
        for item in self.items:
            if item.slot.startswith("back_"):
                self.assertEqual(item.profession, T.TAILORING, item.key)

    def test_stats_rules(self):
        for item in self.items:
            self.assertEqual(item.pool, T.POOL_TANK if item.tank else T.POOL_THROUGHPUT, item.key)
            self.assertEqual(item.extra_stamina, T.TANK_EXTRA_STAMINA if item.tank else 0.0, item.key)
            if item.slot.startswith("jc_"):
                self.assertIsNone(item.primary, f"{item.key}: rings and necks carry secondary stats only")
            else:
                self.assertIn(item.primary, (T.STRENGTH, T.AGILITY, T.INTELLECT, T.SPIRIT), item.key)
            if item.set.raid:
                self.assertTrue(item.sockets and item.socket_bonus, item.key)
                self.assertEqual(item.sockets[0] == T.SOCKET_META, item.head, item.key)
            else:
                self.assertEqual((item.sockets, item.socket_bonus), ((), None), item.key)

    def test_reagents(self):
        for item in self.items:
            reagents = dict(T.reagents(item))
            self.assertTrue(reagents and all(count > 0 for count in reagents.values()), item.key)
            self.assertLessEqual(len(reagents), 8, item.key)
            self.assertEqual(T.TIER_MATERIAL.get(item.set.key) in reagents, item.set.raid, item.key)

    def test_ids_in_blocks(self):
        crafting = IDS["reservations"]["crafting"]
        for row in T.recipes():
            self.assertTrue(_in(crafting["spell"], row.spell), row.spell)
            self.assertTrue(_in(crafting["skilllineability"], row.sla), row.sla)
        recipe_items = T.raid_recipe_items()
        for recipe in recipe_items:
            self.assertTrue(_in(crafting["spell"], recipe.learn_spell), recipe.learn_spell)
            self.assertTrue(78000 <= recipe.entry <= 78999, recipe.entry)
            self.assertFalse(_in(IDS["item_minted"], recipe.entry), recipe.entry)
        spells = [r.spell for r in T.recipes()] + [r.learn_spell for r in recipe_items]
        self.assertEqual(len(spells), len(set(spells)))
        for pool in T.RECIPE_REFERENCE.values():
            self.assertTrue(_in(IDS["crafting_loot_reference"], pool), pool)

    def test_every_raid_recipe_taught_once(self):
        taught = Counter(row.spell for recipe in T.raid_recipe_items() for row in recipe.teaches)
        raid = {row.spell for row in T.recipes() if row.item.set.raid}
        self.assertEqual(set(taught), raid)
        self.assertEqual(set(taught.values()), {1})
        for recipe in T.raid_recipe_items():
            self.assertLessEqual(len(recipe.teaches), 3, recipe.name)  # three learn effects at most
            self.assertEqual({row.item.profession for row in recipe.teaches}, {recipe.profession}, recipe.name)
            self.assertEqual({row.item.set.key for row in recipe.teaches}, {recipe.set.key}, recipe.name)


class SetsDeclarationsTest(unittest.TestCase):
    """The item and recipe declarations."""

    @classmethod
    def setUpClass(cls):
        cls.items = _load(ITEMS_FILE)
        cls.recipes = _load(RECIPES_FILE)

    def test_items(self):
        decls = {entry["id"]: entry["_decl"] for entry in self.items["item_declarations"]}
        self.assertEqual(set(decls), {i.key for i in T.items()})
        for item in T.items():
            decl = decls[item.key]
            self.assertEqual((decl.ilvl, decl.quality, decl.required_level), (item.set.ilvl, item.set.quality,
                                                                               item.set.level))
            self.assertEqual((decl.suffix_pool, decl.secondary, decl.primary), (item.pool, None, item.primary))
            self.assertEqual(decl.sockets, item.sockets or None)

    def test_recipes_round_trip(self):
        spells = {s["id"]: s for s in self.recipes["spells"]}
        for row in T.recipes():
            raw = spells[row.spell]["raw_overrides"]
            self.assertEqual(item_key_refs.parse(raw["EffectItemType_1"]), (row.item.key, "normal"))
            reagents = tuple((raw[f"Reagent_{n}"], raw[f"ReagentCount_{n}"]) for n in range(1, 9)
                             if raw.get(f"Reagent_{n}"))
            self.assertEqual(reagents, T.reagents(row.item))
        sla = {r["id"]: r for r in self.recipes["skill_line_abilities"]}
        for row in T.recipes():
            self.assertEqual((sla[row.sla]["spell_id"], sla[row.sla]["skill_line"]), (row.spell, row.item.profession))
        trained = {(r["TrainerId"], r["SpellId"]) for r in self.recipes["trainer_spells"]}
        want = {(T.TRAINER[r.item.profession], r.spell) for r in T.recipes() if not r.item.set.raid}
        self.assertEqual(trained, want)
        for recipe in T.raid_recipe_items():
            learn = spells[recipe.learn_spell]
            taught = [learn[f"effect{n}"]["trigger_spell"] for n in (1, 2, 3) if learn.get(f"effect{n}")]
            self.assertEqual(taught, [r.spell for r in recipe.teaches])


class SetsSqlTest(unittest.TestCase):
    """write_crafting_set_items.py's files."""

    def test_files_up_to_date(self):
        rows = W.item_rows()
        self.assertEqual(W.ITEMS_SQL.read_text(), W.render_items_sql(rows))
        self.assertEqual(W.LOOT_SQL.read_text(), W.render_loot_sql())
        self.assertEqual(W.ITEMS_CSV.read_text(), W.render_csv(W.ITEMS_CSV.read_text(), rows))

    def test_lints(self):
        for path in (W.ITEMS_SQL, W.LOOT_SQL):
            text = path.read_text().rstrip("\n")
            self.assertTrue(all(len(line) <= 120 for line in text.splitlines()), path.name)
            result = codestyle_sql(text)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:])

    def test_every_tier_boss_rolls_its_pool(self):
        text = W.render_loot_sql()
        for tier, bosses in T.RAID_BOSSES.items():
            pool = T.RECIPE_REFERENCE[tier]
            for lootid in bosses:
                self.assertIn(f"({lootid}, {pool}, {pool}, ", text)
                self.assertIn(f"({lootid}, {T.TIER_MATERIAL[tier]}, 0, ", text)


if __name__ == "__main__":
    unittest.main()
