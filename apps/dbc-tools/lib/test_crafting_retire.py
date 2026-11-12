"""
Crafting rework C7, recipe retirement (.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decision 1, ruled
2026-11-12): the data (lib/crafting_retire_data.py), the declarations (source/world/crafting_retire.py) and the
hand-written SQL (write_crafting_retire.py).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_retire.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_crafting_retire as W  # noqa: E402
from lib import crafting_retire_data as R  # noqa: E402
from lib import source, spell_tables  # noqa: E402
from lib.dbcfile import read_dbc  # noqa: E402
from lib.dbcfmt import SKILLLINEABILITY  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
RETIRE_FILE = TOOL_ROOT / "source" / "world" / "crafting_retire.py"
SQUISH_FILE = TOOL_ROOT / "source" / "world" / "crafting_squish.py"
SLA_DBC = TOOL_ROOT.parents[1] / "var" / "extractors" / "dbc" / "SkillLineAbility.dbc"
REASONS = {"gear", "stat enchant", "enchant item", "glyph", "ammo"}
CRAFTING_SKILLS = {164, 165, 171, 197, 202, 333, 755, 773}
# The C6 utility enchants that stay on trainer 96 (crafting_squish.KEPT) and the Engineering gadgets (ruling 1a).
KEPT_SPOT_CHECKS = {13890, 20014, 7426, 8895, 12905, 12907, 3971, 3969}


def _load():
    sla_rows = {r["ID"]: r for r in read_dbc(SLA_DBC, SKILLLINEABILITY)}
    item_rows = {item: {"entry": item} for item in R.RECIPE_ITEMS}
    live = spell_tables.dsl_live_data({}, item_rows, skilllineability_rows=sla_rows,
                                      skilllineability_stock_rows=sla_rows)
    reg = registry.load_class_file(RETIRE_FILE, ids_cfg=IDS, live_data=live, trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}, sla_rows


class RetireDataTest(unittest.TestCase):
    """The retired list hangs together."""

    def test_data_consistency(self):
        self.assertEqual(len(R.RETIRED), 882)
        for spell, (prof, name, reason) in R.RETIRED.items():
            self.assertLess(spell, 200000, f"{spell} {name}: a C4-C6 custom recipe is never retired")
            self.assertIn(reason, REASONS, name)
            self.assertTrue(prof and name)
        self.assertLessEqual(set(R.TRAINERS), set(R.RETIRED))
        self.assertLessEqual({spell for spell, _name in R.RECIPE_ITEMS.values()}, set(R.RETIRED))
        self.assertLessEqual(set(R.STARTER_SLA.values()), set(R.RETIRED))
        self.assertEqual(len(R.DISABLED_QUESTS), 44)
        self.assertFalse(KEPT_SPOT_CHECKS & set(R.RETIRED))

    def test_retired_spells_are_crafting_recipes(self):
        sla_rows = {r["ID"]: r for r in read_dbc(SLA_DBC, SKILLLINEABILITY)}
        skills = {}
        for row in sla_rows.values():
            skills.setdefault(row["Spell"], set()).add(row["SkillLine"])
        for spell, (_prof, name, _reason) in R.RETIRED.items():
            self.assertTrue(skills.get(spell, set()) & CRAFTING_SKILLS, f"{spell} {name}: no crafting skill line")

    def test_squish_untrains_disjoint(self):
        """C6 took the stock stat enchants off trainer 96; C7 must not declare the same removal twice."""
        text = SQUISH_FILE.read_text()
        block = text[text.index("UNTRAINED = {"):text.index("KEPT = {")]
        untrained = {int(n) for n in re.findall(r"^\s+(\d+):", block, re.M)}
        self.assertTrue(untrained)
        self.assertFalse({spell for spell, trainers in R.TRAINERS.items() if 96 in trainers} & untrained)


class RetireDeclarationsTest(unittest.TestCase):
    """source/world/crafting_retire.py."""

    @classmethod
    def setUpClass(cls):
        cls.dsl, cls.sla_rows = _load()

    def test_trainer_removals(self):
        removed = {(r["TrainerId"], r["SpellId"]) for r in self.dsl["trainer_removals"]}
        expected = {(t, s) for s, trainers in R.TRAINERS.items() for t in trainers}
        self.assertEqual(removed, expected)

    def test_starter_recipes(self):
        rows = {r["id"]: r for r in self.dsl["skill_line_abilities"]}
        self.assertEqual(set(rows), set(R.STARTER_SLA))
        for sla_id, spell in R.STARTER_SLA.items():
            self.assertEqual(rows[sla_id]["acquire_method"], 0)
            self.assertEqual(rows[sla_id]["spell_id"], spell)

    def test_recipe_items_neutered(self):
        rows = {r["entry"]: r for r in self.dsl["item_templates"]}
        self.assertEqual(set(rows), set(R.RECIPE_ITEMS))
        for row in rows.values():
            self.assertEqual((row["spellid_1"], row["spellid_2"], row["Quality"]), (0, 0, 0))
            self.assertEqual(set(row["_update_columns"]), {"spellid_1", "spellid_2", "Quality", "description"})


class RetireSqlTest(unittest.TestCase):
    """write_crafting_retire.py's files."""

    def test_files_up_to_date(self):
        self.assertEqual(W.WORLD_SQL.read_text(), W.world_sql())
        self.assertEqual(W.CHARACTERS_SQL.read_text(), W.characters_sql())

    def test_lints(self):
        for path in (W.WORLD_SQL, W.CHARACTERS_SQL):
            text = path.read_text().rstrip("\n")
            self.assertTrue(all(len(line) <= 120 for line in text.splitlines()), path.name)
            result = codestyle_sql(text)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:])

    def test_every_retired_spell_disabled_and_deleted(self):
        world, characters = W.world_sql(), W.characters_sql()
        for spell in R.RETIRED:
            self.assertIn(f"(0, {spell}, 1, ", world)
            self.assertRegex(characters, rf"[( ]{spell}[,)]")
        for quest in R.DISABLED_QUESTS:
            self.assertIn(f"(1, {quest}, 0, ", world)


if __name__ == "__main__":
    unittest.main()
