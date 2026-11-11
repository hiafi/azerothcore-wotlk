"""
Crafting rework C4: `suffix_pool()` (lib/dsl/enchants.py), the `item_enchantment_template` SPELL_TABLES entry it feeds,
the pool checks (lib/enchant_tables.py), and the C4 declarations in source/world/crafting_suffixes.py: nine suffix
parts, 24 pair suffixes (15 throughput, 9 tank), the two pools, nine Missive buffs and their Inscription recipes.

The item and pilot rows they rely on are hand-written SQL (data/sql/updates/pending_db_world/
rev_crafting_c4_missive_items.sql, itemization_templates_v2/rev_crafting_c4_pilot.sql); the tests read those files as
text. The stock-name test is skipped when var/extractors/dbc/ItemRandomSuffix.dbc is missing.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_suffixes.py
"""

from __future__ import annotations

import csv
import itertools
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402,F401  (the module generate.py wires these tables through must import)
from lib import dbcfile, dbcfmt, enchant_tables, source, spell_tables, state, trainer_state  # noqa: E402
from lib.table_testkit import codestyle_sql, index_for, load_dsl, render, spec_for  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
CRAFTING_FILE = TOOL_ROOT / "source" / "world" / "crafting_suffixes.py"
ITEMS_CSV = TOOL_ROOT / "source" / "items.csv"
PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
MISSIVE_SQL = PENDING / "rev_crafting_c4_missive_items.sql"
PILOT_SQL = PENDING / "itemization_templates_v2" / "rev_crafting_c4_pilot.sql"

CRIT, HASTE, MASTERY, VERSATILITY, COOLDOWN, PROC = 32, 36, 22, 23, 24, 33
BLOCK, DODGE, PARRY = 15, 13, 14
THROUGHPUT = (CRIT, HASTE, MASTERY, VERSATILITY, COOLDOWN, PROC)
TANK = (BLOCK, DODGE, PARRY)
SKILL_INSCRIPTION = 773
ATTR0_PASSIVE = 0x40
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
DAY_MS = 86_400_000

HEAD = "from lib.dsl.enchants import stat_enchant, suffix, suffix_pool\nfrom lib.dsl.registry import ItemMod\n"


def _load(text: str) -> dict:
    return load_dsl(text, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, {}))


class SuffixPoolDslTest(unittest.TestCase):
    TWO = HEAD + (
        "a = stat_enchant(5000, ItemMod.CRIT_RATING)\n"
        "b = stat_enchant(5001, ItemMod.HASTE_RATING)\n"
        "s1 = suffix(1000, 'of A', 'A', (a, 5000), (b, 5000))\n"
        "s2 = suffix(1001, 'of B', 'B', (a, 5000))\n"
        "s3 = suffix(1002, 'of C', 'C', (b, 5000))\n"
    )

    def test_one_row_per_suffix_at_equal_chances_summing_to_at_least_100(self):
        rows = _load(self.TWO + "suffix_pool(9000, s1, s2, s3)\n")["item_enchantment_pools"]
        self.assertEqual([(r["entry"], r["ench"]) for r in rows], [(9000, 1000), (9000, 1001), (9000, 1002)])
        self.assertEqual({r["chance"] for r in rows}, {33.3334})
        self.assertGreaterEqual(sum(r["chance"] for r in rows), 100.0)

    def test_ids_or_rows_and_stock_suffixes_are_accepted(self):
        rows = _load(self.TWO + "suffix_pool(9000, 1000, 5)\n")["item_enchantment_pools"]
        self.assertEqual([r["ench"] for r in rows], [1000, 5])
        self.assertEqual(rows[0]["chance"], 50.0)

    def test_errors(self):
        for line, message in (
            ("suffix_pool(8675, s1)\n", "item_enchantment_pool"),  # a stock pool entry
            ("suffix_pool(9000)\n", "at least one"),
            ("suffix_pool(9000, s1, 1000)\n", "twice"),
            ("suffix_pool(9000, 40000)\n", "32767"),
        ):
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, message):
                _load(self.TWO + line)

    def test_a_pool_declared_twice_is_a_duplicate(self):
        with self.assertRaises(Exception):
            _load(self.TWO + "suffix_pool(9000, s1)\nsuffix_pool(9000, s1)\n")

    def test_rendered_block_passes_the_sql_linter_and_converges(self):
        rows = _load(self.TWO + "suffix_pool(9000, s1, s2)\n")["item_enchantment_pools"]
        block = render("item_enchantment_template", index_for("item_enchantment_template", []), rows)
        self.assertIn("DELETE FROM `item_enchantment_template`", block)
        self.assertIn("(9000, 1000, 50", block)
        done = codestyle_sql(block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        live = [{"entry": 9000, "ench": 1000, "chance": 50.0}, {"entry": 9000, "ench": 1001, "chance": 50.0}]
        spec = spec_for("item_enchantment_template")
        self.assertEqual(index_for("item_enchantment_template", live).rows_to_emit(spec, rows), [])

    def test_a_dropped_pool_prunes_but_a_stock_pool_never_does(self):
        spec = spec_for("item_enchantment_template")
        emitted = [{"entry": 9000, "ench": 1000}]
        index = index_for("item_enchantment_template", emitted, emitted=emitted)
        self.assertEqual(index.rows_to_prune(spec, []).keys, [(9000.0, 1000.0)])
        stock = [{"entry": 61, "ench": 5}]
        index = index_for("item_enchantment_template", stock, emitted=stock, base=stock)
        self.assertEqual(index.rows_to_prune(spec, []).keys, [])


class PoolCheckTest(unittest.TestCase):
    def test_declared_pools_replace_their_live_rows(self):
        live = [{"entry": 61, "ench": 5}, {"entry": 9000, "ench": 1999}]
        declared = [{"entry": 9000, "ench": 1000, "chance": 100.0}]
        merged = enchant_tables.merged_pool_rows(live, declared)
        self.assertEqual(sorted((r["entry"], r["ench"]) for r in merged), [(61, 5), (9000, 1000)])

    def test_an_item_naming_a_pool_with_no_rows_is_reported(self):
        (problem,) = enchant_tables.suffix_pool_problems([{"entry": 9000, "ench": 1000}], {9000, 9001}, {1000})
        self.assertIn("RandomSuffix 9001", problem)


class CraftingSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsl = load_dsl(CRAFTING_FILE.read_text(), ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, {}))
        cls.parts = {r["ID"]: r for r in cls.dsl["spell_item_enchantments"]}
        cls.suffixes = {r["ID"]: r for r in cls.dsl["item_random_suffixes"]}
        cls.spells = {s["id"]: s for s in cls.dsl["spells"]}

    def _stats(self, suffix_row):
        return tuple(self.parts[suffix_row[f"Enchantment_{n}"]]["EffectArg_1"] for n in (1, 2))

    def _pool(self, entry):
        return [r for r in self.dsl["item_enchantment_pools"] if r["entry"] == entry]

    def test_nine_suffix_parts_one_per_stat_scaled_by_the_factor(self):
        self.assertEqual(sorted(self.parts), list(range(5000, 5009)))
        self.assertEqual({r["EffectArg_1"] for r in self.parts.values()}, set(THROUGHPUT + TANK))
        for row in self.parts.values():
            self.assertEqual((row["Effect_1"], row["EffectPointsMin_1"], row["EffectPointsMax_1"]), (5, 0, 0))
            self.assertTrue(row["Name_Lang_enUS"].startswith("+$i "))
        names = {r["EffectArg_1"]: r["Name_Lang_enUS"] for r in self.parts.values()}
        self.assertEqual(names[MASTERY], "+$i Mastery Rating")
        self.assertEqual(names[VERSATILITY], "+$i Versatility Rating")
        self.assertEqual(names[COOLDOWN], "+$i Cooldown Haste Rating")
        self.assertEqual(names[PROC], "+$i Proc Chance Rating")

    def test_throughput_pool_holds_every_pair_of_the_six_once(self):
        pool = self._pool(9000)
        pairs = [frozenset(self._stats(self.suffixes[r["ench"]])) for r in pool]
        self.assertEqual(sorted(map(sorted, pairs)), sorted(map(sorted, map(frozenset,
                                                                             itertools.combinations(THROUGHPUT, 2)))))

    def test_tank_pool_is_ruling_c3(self):
        pairs = {frozenset(self._stats(self.suffixes[r["ench"]])) for r in self._pool(9001)}
        expected = {frozenset(p) for p in itertools.combinations(TANK, 2)}
        expected |= {frozenset((tank, other)) for tank in TANK for other in (MASTERY, VERSATILITY)}
        self.assertEqual(pairs, expected)
        self.assertEqual(len(self._pool(9001)), 9)

    def test_24_suffixes_two_parts_each_at_5000_over_the_stat_cost(self):
        self.assertEqual(sorted(self.suffixes), list(range(1000, 1024)))
        costs = {int(r["stat_type"]): float(r["cost"]) for r in trainer_state.load_table_rows("item_stat_cost")}
        for row in self.suffixes.values():
            with self.subTest(suffix=row["ID"]):
                self.assertTrue(row["Name_Lang_enUS"].startswith("of the "))
                self.assertEqual(row["Enchantment_3"], 0)
                for n in (1, 2):
                    stat = self.parts[row[f"Enchantment_{n}"]]["EffectArg_1"]
                    self.assertEqual(row[f"AllocationPct_{n}"], round(5000 / costs[stat]))
        names = [r["Name_Lang_enUS"] for r in self.suffixes.values()]
        self.assertEqual(len(set(names)), len(names))

    @unittest.skipUnless((state.BASE_DBC_DIR / "ItemRandomSuffix.dbc").is_file(), "no stock ItemRandomSuffix.dbc")
    def test_no_name_repeats_a_stock_suffix(self):
        stock = {r["Name_Lang_enUS"] for r in dbcfile.read_dbc(state.BASE_DBC_DIR / "ItemRandomSuffix.dbc",
                                                               dbcfmt.ITEMRANDOMSUFFIX)}
        self.assertFalse(stock & {r["Name_Lang_enUS"] for r in self.suffixes.values()})

    def test_pool_chances_sum_to_100_or_just_over(self):
        for entry in (9000, 9001):
            total = sum(r["chance"] for r in self._pool(entry))
            self.assertGreaterEqual(total, 100.0)
            self.assertLess(total, 100.01)

    def test_missive_buffs(self):
        bound = {r["spell_id"] for r in self.dsl["spell_script_names"] if r["ScriptName"] == "spell_crafting_missive"}
        self.assertEqual(bound, set(range(207000, 207009)))
        stats = set()
        for spell_id in bound:
            entry = self.spells[spell_id]
            with self.subTest(spell=spell_id):
                effect = entry["effect1"]
                self.assertIsNone(entry["effect2"])
                self.assertEqual((effect["type"], effect["apply_aura"], effect["implicit_target_a"]), (6, 4, 1))
                stats.add(effect["misc_value"])
                self.assertEqual(entry["duration_ms"], DAY_MS)
                self.assertFalse(entry["attributes"] & ATTR0_PASSIVE)
                raw = entry["raw_overrides"]
                self.assertTrue(raw["AttributesEx3"] & ATTR3_ALLOW_AURA_WHILE_DEAD)
                # kept on arena entry, and no AURA_EXPIRES_OFFLINE (0x08): the 24 h count play time only
                self.assertEqual(raw["AttributesEx4"], 0x00200000)
                self.assertTrue(raw["AuraDescription_Lang_enUS"].startswith("Your next crafted item gains "))
        self.assertEqual(stats, set(THROUGHPUT + TANK))

    def test_every_missive_stat_has_a_pair_in_some_pool(self):
        pooled = {s for r in self.dsl["item_enchantment_pools"] for s in self._stats(self.suffixes[r["ench"]])}
        self.assertEqual(pooled, set(THROUGHPUT + TANK))

    def test_recipes_create_the_missive_items_and_are_learned_by_inscription(self):
        buffs = {s["effect1"]["misc_value"]: s["id"] for s in self.spells.values() if s["id"] < 207010}
        slas = {r["spell_id"]: r for r in self.dsl["skill_line_abilities"]}
        self.assertEqual(set(slas), set(range(207010, 207019)))
        for offset in range(9):
            recipe = self.spells[207010 + offset]
            raw = recipe["raw_overrides"]
            with self.subTest(recipe=recipe["id"]):
                self.assertEqual(recipe["effect1"]["type"], 24)  # SPELL_EFFECT_CREATE_ITEM
                self.assertEqual(raw["EffectItemType_1"], 70710 + offset)
                self.assertTrue(recipe["attributes"] & 0x20)  # SPELL_ATTR0_IS_TRADESKILL
                self.assertEqual((raw["Reagent_1"], raw["ReagentCount_1"], raw["Reagent_2"], raw["ReagentCount_2"]),
                                 (43116, 2, 39354, 1))
                sla = slas[recipe["id"]]
                self.assertEqual((sla["skill_line"], sla["min_skill_line_rank"], sla["acquire_method"]),
                                 (SKILL_INSCRIPTION, 1, 1))
                self.assertEqual(sla["id"], 30900 + offset)
        self.assertEqual(len(buffs), 9)

    def test_ids_sit_in_their_reservations(self):
        res = IDS["reservations"]["crafting"]
        for spell_id in self.spells:
            self.assertTrue(res["spell"]["start"] <= spell_id <= res["spell"]["end"])
        for row in self.dsl["skill_line_abilities"]:
            self.assertTrue(res["skilllineability"]["start"] <= row["id"] <= res["skilllineability"]["end"])


class MissiveItemRowsTest(unittest.TestCase):
    def test_items_csv_has_the_nine_scroll_rows(self):
        with ITEMS_CSV.open(newline="") as f:
            rows = {int(r["id"]): r for r in csv.DictReader(f)}
        for entry in range(70710, 70719):
            row = rows[entry]
            self.assertEqual((row["class_id"], row["subclass_id"], row["display_info_id"], row["inventory_type"]),
                             ("0", "4", "3018", "0"))

    def test_item_template_rows_use_their_buff_and_match_items_csv(self):
        text = MISSIVE_SQL.read_text()
        done = codestyle_sql(text.rstrip("\n"))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        found = re.findall(r"\((707\d\d), 0, 4, -1, '([^']+)', 3018,.*?(20700\d), 0, -1,", text, re.S)
        self.assertEqual([(int(e), int(s)) for e, _n, s in found], [(70710 + i, 207000 + i) for i in range(9)])


class PilotSqlTest(unittest.TestCase):
    def test_the_pilot_points_at_the_two_pools_and_passes_the_linter(self):
        text = PILOT_SQL.read_text()
        done = codestyle_sql(text.rstrip("\n"))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        pools = {int(e): int(p) for p, e in re.findall(r"SET `RandomSuffix` = (900\d), `ItemLevel` = 60,.*?WHERE\s+"
                                                       r"`entry` = (\d+);", text, re.S)}
        self.assertEqual(pools, {14138: 9000, 18409: 9000, 15059: 9000, 18506: 9000, 15047: 9000, 12633: 9000,
                                 19057: 9000, 12618: 9001})
        # every item_itemization row: secondary_shape_id 0, primary_share 6000 (the last four values but one)
        rows = re.findall(r"VALUES \((\d+), ([^)]*)\);", text)
        self.assertEqual(sorted(int(e) for e, _v in rows), sorted(pools))
        for entry, values in rows:
            secondary, share = [v.strip() for v in values.split(",")][6:8]
            self.assertEqual((secondary, share), ("0", "6000"), entry)

if __name__ == "__main__":
    unittest.main()
