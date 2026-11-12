"""
Crafting rework C7, premium enchants, flasks, raid buff scrolls, boss runes and the Darkmoon tarot
(.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md decisions 4-6): the data
(lib/crafting_consumables_data.py), the declarations (source/world/crafting_consumables.py) and the item rows
(write_crafting_consumable_items.py).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_consumables.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_crafting_consumable_items as W  # noqa: E402
import write_crafting_set_items as S  # noqa: E402
from lib import crafting_consumables_data as T  # noqa: E402
from lib import source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
SOURCE_FILE = TOOL_ROOT / "source" / "world" / "crafting_consumables.py"
STOCK_GROUPS = {1, 2} | {g for s in T.SCROLLS for g in s.groups}
FORBIDDEN_STATS = {7, 12, 16, 17, 18, 31, 37}  # Stamina, Defense, the Hits, Expertise (C6)


def _in(block: dict, value: int) -> bool:
    return block["start"] <= value <= block["end"]


def _load() -> dict:
    items = {deck: {"entry": deck} for deck in T.DECKS}
    reg = registry.load_class_file(SOURCE_FILE, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, items),
                                   trainer_index=_AnyTrainer(), existing_group_ids=STOCK_GROUPS)
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class ConsumablesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dsl = _load()
        cls.spells = {s["id"]: s for s in cls.dsl["spells"]}

    def test_ids_in_blocks(self):
        crafting = IDS["reservations"]["crafting"]
        custom = [s for s in self.spells if s >= 200000]
        self.assertTrue(all(_in(crafting["spell"], s) and 208800 <= s <= 208999 for s in custom), custom)
        for row in self.dsl["skill_line_abilities"]:
            self.assertTrue(31950 <= row["id"] <= 31999, row["id"])
        for row in W.item_rows():
            self.assertIn(row["entry"], T.ITEM_RANGE)
        for row in self.dsl["spell_item_enchantments"]:
            self.assertTrue(5940 <= row["ID"] <= 5999, row["ID"])

    def test_premium_enchants(self):
        enchants = {row["ID"]: row for row in self.dsl["spell_item_enchantments"]}
        self.assertEqual(set(enchants), {p.enchant for p in T.PREMIUMS})
        for row in enchants.values():
            self.assertEqual(row["MinLevel"], T.PREMIUM_ENCHANT_MIN_LEVEL)
            for n in (1, 2, 3):
                if row.get(f"Effect_{n}") == 5:  # a stat part
                    self.assertNotIn(row[f"EffectArg_{n}"], FORBIDDEN_STATS)
        procs = {r["SpellId"]: r for r in self.dsl["spell_procs"]}
        for proc in T.PROCS.values():
            self.assertEqual((procs[proc.aura_spell]["Chance"], procs[proc.aura_spell]["Cooldown"]),
                             (proc.chance, proc.cooldown_ms))
        scripts = {(r["spell_id"], r["ScriptName"]) for r in self.dsl["spell_script_names"]}
        for key in ("crusader", "spellsurge"):
            self.assertIn((T.PROCS[key].aura_spell, "spell_crafting_premium_higher_primary"), scripts)
            # the higher-primary script casts the trigger spell or the next id: a pair of the same aura
            first = T.BUFFS[T.PROCS[key].buff]
            second = next(b for b in T.BUFFS.values() if b.spell == first.spell + 1)
            self.assertEqual((first.aura, first.amount), (second.aura, second.amount))
        self.assertIn((T.BUFFS["absorb"].spell, "spell_crafting_max_health_absorb"), scripts)
        for p in T.PREMIUMS:  # learned from raid recipes only, never trained
            self.assertNotIn(p.recipe_spell, {r["SpellId"] for r in self.dsl["trainer_spells"]})

    def test_premium_recipes_in_t1_pool(self):
        text = S.render_loot_sql()
        for p in T.PREMIUMS:
            self.assertIn(f"({S.T.RECIPE_REFERENCE['t1']}, {p.recipe_item}, 0, ", text)

    def test_flasks(self):
        groups = {(r["id"], r["spell_id"]) for r in self.dsl["spell_groups"]}
        for flask in T.FLASKS:
            spell = self.spells[flask.spell]
            self.assertEqual(spell["effect1"]["misc_value"], flask.stat)
            self.assertEqual(spell["effect1"]["base_points"] + 1, flask.amount)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x00100000, "flasks persist through death")
            if flask.sla is not None:
                self.assertTrue({(1, flask.spell), (2, flask.spell)} <= groups)
        sizes = {flask.stat: flask.amount for flask in T.FLASKS}
        self.assertEqual(sizes, {T.STAT_STRENGTH: 40, T.STAT_AGILITY: 40, T.STAT_INTELLECT: 60, T.STAT_SPIRIT: 60,
                                 T.STAT_STAMINA: 60})

    def test_scrolls_share_the_class_buff_group(self):
        groups = {(r["id"], r["spell_id"]) for r in self.dsl["spell_groups"]}
        for n, scroll in enumerate(T.SCROLLS):
            spell_id = T.scroll_ids(n)[0]
            for group in scroll.groups:
                self.assertIn((group, spell_id), groups, scroll.name)
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["implicit_target_a"], T.SCROLL_TARGET)
        self.assertEqual(len(T.SCROLLS), 17)

    def test_runes(self):
        for rune in T.RUNES:
            raw = self.spells[rune.spell]
            self.assertEqual((raw["category"], raw["category_cooldown_ms"]), (T.RUNE_CATEGORY, T.RUNE_COOLDOWN_MS))
            self.assertEqual(raw["effect2"]["base_points"] + 1, rune.pct)
        self.assertEqual({r["id"] for r in self.dsl["spell_categories"]}, {T.RUNE_CATEGORY})

    def test_decks(self):
        edits = {row["entry"]: row for row in self.dsl["item_templates"]}
        for deck, (trinket, spell_id) in T.DECKS.items():
            self.assertEqual((edits[deck]["startquest"], edits[deck]["spellid_1"]), (0, spell_id))
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["EffectItemType_1"], trinket)
        self.assertEqual(len(set(T.CARDS)), 32)

    def test_files_up_to_date_and_lint(self):
        rows = W.item_rows()
        self.assertEqual(W.SQL_PATH.read_text(), W.render_sql(rows))
        self.assertEqual(W.ITEMS_CSV.read_text(), W.render_csv(W.ITEMS_CSV.read_text(), rows))
        text = W.SQL_PATH.read_text().rstrip("\n")
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))
        result = codestyle_sql(text)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:])


if __name__ == "__main__":
    unittest.main()
