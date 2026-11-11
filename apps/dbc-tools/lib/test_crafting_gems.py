"""
Crafting rework C5: the gem table (lib/crafting_gems_data.py), its declarations (source/world/crafting_gems.py) and the
generated item rows (write_gem_items.py -> data/sql/updates/pending_db_world/rev_crafting_c5_gem_items.sql and
source/items.csv). Rulings: .agents/plans/crafting-rework/crafting-rework.C5-RESEARCH.md (user 2026-11-11).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_gems.py
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_gem_items  # noqa: E402
from lib import crafting_gems_data as T  # noqa: E402
from lib import source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
GEMS_FILE = TOOL_ROOT / "source" / "world" / "crafting_gems.py"


def _load():
    reg = registry.load_class_file(GEMS_FILE, ids_cfg=IDS, live_data=spell_tables.dsl_live_data({}, {}),
                                   trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class GemTableTest(unittest.TestCase):
    """The rulings, checked on the table itself."""

    def setUp(self):
        self.gems = T.gems()
        self.by_kind = Counter(g["kind"] for g in self.gems)

    def test_counts(self):
        self.assertEqual(self.by_kind, {"rare": 37, "epic": 37, "leveling": 10, "meta": 5})

    def test_rare_colors_r39(self):
        colors = Counter(g["color"] for g in self.gems if g["kind"] == "rare")
        self.assertEqual(colors, {T.RED: 4, T.YELLOW: 4, T.BLUE: 6, T.ORANGE: 9, T.PURPLE: 6, T.GREEN: 8})

    def test_no_stamina(self):
        stamina = 7
        for g in self.gems:
            self.assertNotIn(stamina, [s for s, _a in g["stats"]], g["name"])
        self.assertNotIn(stamina, T.SOCKET_BONUS_STATS)

    def test_sizes(self):
        for g in self.gems:
            amounts = [a for s, a in g["stats"] if s != T.MP5]
            if not amounts or g["kind"] == "meta":
                continue  # pure MP5 (test_mp5_priced_at_five) or a meta (no stats)
            if g["kind"] == "leveling":
                self.assertEqual(amounts, [4], g["name"])
            elif g["kind"] == "rare":
                self.assertEqual(amounts, [8] if len(g["stats"]) == 1 else [4] * len(amounts), g["name"])
            elif g["kind"] == "epic":
                self.assertEqual(amounts, [10] if len(g["stats"]) == 1 else [5] * len(amounts), g["name"])

    def test_mp5_priced_at_five(self):
        mp5 = {(g["kind"], g["name"].split()[0]): dict(g["stats"])[T.MP5] for g in self.gems
               if T.MP5 in dict(g["stats"])}
        self.assertEqual(mp5[("rare", "Lustrous")], 2)
        self.assertEqual(mp5[("epic", "Lustrous")], 2)  # decision 1 A
        self.assertEqual(mp5[("rare", "Royal")], 1)

    def test_leveling_stats_user_ruling(self):
        want = {T.STRENGTH, T.AGILITY, T.INTELLECT, T.SPIRIT, T.CRIT, T.HASTE, T.MASTERY, T.DODGE, T.BLOCK,
                T.PARRY}
        leveling = [g for g in self.gems if g["kind"] == "leveling"]
        self.assertEqual({g["stats"][0][0] for g in leveling}, want)
        self.assertTrue(all(g["color"] in (T.RED, T.YELLOW, T.BLUE) for g in leveling))
        self.assertTrue(all(g["quality"] == T.QUALITY_UNCOMMON and g["level_gate"] == 0 for g in leveling))

    def test_level_gate(self):
        for g in self.gems:
            self.assertEqual(g["level_gate"], 0 if g["kind"] == "leveling" else 60, g["name"])

    def test_metas_from_azerothian_diamond(self):
        metas = [g for g in self.gems if g["kind"] == "meta"]
        self.assertEqual({g["raw"] for g in metas}, {T.AZEROTHIAN_DIAMOND})
        self.assertTrue(all(g["quality"] == T.QUALITY_RARE and g["color"] == T.META for g in metas))

    def test_rare_raws_are_the_thorium_six(self):
        rare_raws = {g["color"]: g["raw"] for g in self.gems if g["kind"] == "rare"}
        self.assertEqual(set(rare_raws.values()), {T.STAR_RUBY, T.AZEROTHIAN_DIAMOND, T.BLUE_SAPPHIRE, T.LARGE_OPAL,
                                                   T.HUGE_EMERALD, T.ARCANE_CRYSTAL})

    def test_ids_unique_and_in_blocks(self):
        for key, block in (("item", "item"), ("enchant", "spellitemenchantment"), ("gemprop", "gemproperties"),
                           ("cut", "spell"), ("sla", "skilllineability")):
            ids = [g[key] for g in self.gems]
            self.assertEqual(len(ids), len(set(ids)), key)
            lo, hi = IDS[block]["start"], IDS[block]["end"]
            self.assertTrue(all(lo <= i <= hi for i in ids), key)
        items = [g["item"] for g in self.gems] + [r["item"] for r in T.epic_raws()]
        self.assertEqual(len(items), len(set(items)))
        self.assertTrue(all(70720 <= i <= 70899 for i in items))
        crafting = IDS["reservations"]["crafting"]
        self.assertTrue(all(crafting["spell"]["start"] <= g["cut"] <= crafting["spell"]["end"] for g in self.gems))
        self.assertTrue(all(crafting["skilllineability"]["start"] <= g["sla"] <= crafting["skilllineability"]["end"]
                            for g in self.gems))

    def test_names_unique(self):
        names = [g["name"] for g in self.gems] + [r["name"] for r in T.epic_raws()]
        self.assertEqual(len(names), len(set(names)))

    def test_enchant_text_fits(self):
        for g in self.gems:
            if g["kind"] != "meta":
                self.assertLessEqual(len(T.enchant_text(g["stats"])), 100, g["name"])
        for _key, _name, _display, text, _extra in T.METAS:
            self.assertLessEqual(len(text), 100)


class GemDeclarationTest(unittest.TestCase):
    """What source/world/crafting_gems.py declares."""

    @classmethod
    def setUpClass(cls):
        cls.dsl = _load()
        cls.gems = {g["item"]: g for g in T.gems()}

    def test_row_counts(self):
        self.assertEqual(len(self.dsl["gem_properties"]), 89)
        self.assertEqual(len(self.dsl["spell_item_enchantments"]), 89 + len(T.SOCKET_BONUS_STATS))
        self.assertEqual(len(self.dsl["skill_line_abilities"]), 89)
        self.assertEqual(len(self.dsl["spells"]), 89 + 10)
        self.assertEqual(len(self.dsl["spell_procs"]), 3)

    def test_enchant_round_trip(self):
        enchants = {r["ID"]: r for r in self.dsl["spell_item_enchantments"]}
        for prop in self.dsl["gem_properties"]:
            gem = next(g for g in self.gems.values() if g["gemprop"] == prop["ID"])
            self.assertEqual(prop["Type"], gem["color"])
            enchant = enchants[prop["Enchant_Id"]]
            self.assertEqual(enchant["Src_ItemID"], gem["item"])  # meta counting needs the round trip (C1)
            self.assertEqual(enchant["MinLevel"], gem["level_gate"])

    def test_stat_enchants_match_table(self):
        enchants = {r["ID"]: r for r in self.dsl["spell_item_enchantments"]}
        for gem in self.gems.values():
            if gem["kind"] == "meta":
                continue
            row = enchants[gem["enchant"]]
            got = [(row[f"EffectArg_{i}"], row[f"EffectPointsMin_{i}"]) for i in (1, 2, 3) if row[f"Effect_{i}"]]
            self.assertEqual(got, list(gem["stats"]), gem["name"])

    def test_meta_enchants_cast_scripted_spells(self):
        enchants = {r["ID"]: r for r in self.dsl["spell_item_enchantments"]}
        scripted = {r["spell_id"] for r in self.dsl["spell_script_names"]}
        for gem in (g for g in self.gems.values() if g["kind"] == "meta"):
            row = enchants[gem["enchant"]]
            spells = [row[f"EffectArg_{i}"] for i in (1, 2, 3) if row[f"Effect_{i}"] == 3]  # EQUIP_SPELL
            self.assertTrue(spells, gem["name"])
            self.assertTrue(all(s in scripted for s in spells), gem["name"])

    def test_cuts(self):
        spells = {s["id"]: s for s in self.dsl["spells"]}
        for gem in self.gems.values():
            raw = spells[gem["cut"]]["raw_overrides"]
            self.assertEqual(raw["EffectItemType_1"], gem["item"], gem["name"])
            self.assertEqual((raw["Reagent_1"], raw["ReagentCount_1"]), (gem["raw"], 1), gem["name"])

    def test_trainer_teaches_rare_leveling_and_meta_only(self):
        taught = {r["SpellId"] for r in self.dsl["trainer_spells"]}
        self.assertEqual({r["TrainerId"] for r in self.dsl["trainer_spells"]}, {113})
        for gem in self.gems.values():
            self.assertEqual(gem["cut"] in taught, gem["kind"] != "epic", gem["name"])

    def test_procs(self):
        procs = {r["SpellId"]: r for r in self.dsl["spell_procs"]}
        self.assertEqual((procs[207150]["Chance"], procs[207150]["Cooldown"]), (10, 45000))
        self.assertEqual((procs[207156]["Chance"], procs[207156]["Cooldown"]), (15, 30000))
        self.assertEqual((procs[207158]["Chance"], procs[207158]["Cooldown"]), (100, 6000))

    def test_socket_bonuses(self):
        enchants = {r["ID"]: r for r in self.dsl["spell_item_enchantments"]}
        for index, stat in enumerate(T.SOCKET_BONUS_STATS):
            row = enchants[T.SOCKET_BONUS_ENCHANT + index]
            self.assertEqual((row["EffectArg_1"], row["EffectPointsMin_1"]), (stat, 4))


class GemItemFilesTest(unittest.TestCase):
    """The generated item_template SQL and items.csv rows match the table and lint clean."""

    def test_files_current(self):
        rows = write_gem_items.item_rows()
        self.assertEqual(write_gem_items.SQL_PATH.read_text(), write_gem_items.render_sql(rows),
                         "rerun apps/dbc-tools/write_gem_items.py")
        self.assertEqual(write_gem_items.ITEMS_CSV.read_text(),
                         write_gem_items.render_csv(write_gem_items.ITEMS_CSV.read_text(), rows))

    def test_rows(self):
        rows = {r["entry"]: r for r in write_gem_items.item_rows()}
        self.assertEqual(len(rows), 95)
        # Socketing destroys the gem with DestroyItem, the whole stack: cut gems must not stack (stock: 1).
        self.assertTrue(all(rows[g["item"]]["stackable"] == 1 for g in T.gems()))
        self.assertTrue(all(rows[r["item"]]["stackable"] == 20 for r in T.epic_raws()))
        for gem in T.gems():
            row = rows[gem["item"]]
            self.assertEqual((row["class"], row["GemProperties"], row["Quality"]), (3, gem["gemprop"], gem["quality"]))
            self.assertEqual(row["subclass"], T.GEM_SUBCLASS[gem["color"]])
        for raw in T.epic_raws():
            self.assertEqual(rows[raw["item"]]["GemProperties"], 0)

    def test_sql_lints(self):
        text = write_gem_items.SQL_PATH.read_text().rstrip("\n")
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))
        self.assertEqual(codestyle_sql(text).returncode, 0)


if __name__ == "__main__":
    unittest.main()
