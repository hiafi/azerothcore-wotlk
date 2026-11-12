"""
Crafting rework C6, material squish (.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md decisions 12 and
13, user 2026-11-11): the disenchant bands (lib/disenchant.py), the recipe and trainer declarations
(source/world/crafting_squish.py) and the hand-written loot (rev_crafting_c6_squish_loot.sql).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_squish.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import disenchant, source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
SQUISH_FILE = TOOL_ROOT / "source" / "world" / "crafting_squish.py"
LOOT_SQL = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world" / "rev_crafting_c6_squish_loot.sql"
# The vanilla dusts, essences and shards the squish retires, and the pigments that no longer drop.
OLD_ENCHANTING_MATS = {10940, 11083, 11137, 11176, 10938, 10998, 11134, 11174, 10939, 11082, 11135, 11175, 10978, 11138,
                       11177, 11084, 11139, 11178}
OLD_PIGMENTS = {39151, 39334, 43103, 43104, 39340, 39341}


def _load():
    reg = registry.load_class_file(SQUISH_FILE, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, {}),
                                   trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class SquishTest(unittest.TestCase):
    """The disenchant bands and the squish declarations."""

    def test_disenchant_bands(self):
        cases = {(4, 2, 15): 1, (2, 2, 20): 22, (2, 2, 25): 23, (4, 2, 45): 7, (4, 2, 62): 11, (4, 3, 50): 46,
                 (4, 3, 51): 47,
                 (4, 3, 70): 49, (4, 4, 66): 65, (4, 4, 80): 65, (4, 4, 81): disenchant.EPIC_HIGH_ENTRY}
        for (item_class, quality, item_level), entry in cases.items():
            got = disenchant.disenchant_columns(item_class, quality, item_level, 60)
            self.assertEqual(got["DisenchantID"], entry, (item_class, quality, item_level))
        self.assertIsNone(disenchant.disenchant_columns(4, 4, 115, 70))  # Outland keeps its own
        self.assertIsNone(disenchant.disenchant_columns(0, 2, 30, 0))

    def test_squish_declarations(self):
        dsl = _load()
        removed = {(r["TrainerId"], r["SpellId"]) for r in dsl["trainer_removals"]}
        self.assertEqual(len(removed), 49)
        self.assertTrue(all(trainer == 96 for trainer, _spell in removed))
        old = OLD_ENCHANTING_MATS | OLD_PIGMENTS
        for s in dsl["spells"]:
            raw = s["raw_overrides"]
            reagents = [raw.get(f"Reagent_{k}") for k in range(1, 9) if raw.get(f"Reagent_{k}")]
            self.assertFalse(set(reagents) & old, s["name"])
            self.assertTrue(reagents, s["name"])
        inks = {s["id"]: s["raw_overrides"] for s in dsl["spells"]}
        self.assertEqual((inks[57712]["Reagent_1"], inks[57712]["ReagentCount_1"]), (43107, 2))  # Ink of the Sky
        self.assertEqual((inks[57709]["Reagent_1"], inks[57709]["Reagent_2"]), (43106, 43107))  # Celestial


    def test_loot_sql_lints(self):
        text = LOOT_SQL.read_text().rstrip("\n")
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))
        self.assertEqual(codestyle_sql(text).returncode, 0)


if __name__ == "__main__":
    unittest.main()
