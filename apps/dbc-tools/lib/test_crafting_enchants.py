"""
Crafting rework C6: the enchant table (lib/crafting_enchants_data.py), its declarations
(source/world/crafting_enchants.py), the Hit / Expertise / Defense remap (lib/crafting_hed_remap.py,
source/world/crafting_hed_remap.py) and the generated item rows (write_enchant_items.py). Rulings:
.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md sections 5 and 6 (user 2026-11-11).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_crafting_enchants.py
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_enchant_items  # noqa: E402
from lib import crafting_enchants_data as T  # noqa: E402
from lib import crafting_hed_remap as R  # noqa: E402
from lib import dbcfmt, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402
from lib.test_id_blocks import _AnyTrainer  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
WORLD = TOOL_ROOT / "source" / "world"
ENCHANT_ITEM, ADD_SOCKET, CREATE_ITEM = 53, 156, 24
STAMINA = 7


def _load(name: str, item_rows: dict | None = None, **live):
    reg = registry.load_class_file(WORLD / name, ids_cfg=IDS,
                                   live_data=spell_tables.dsl_live_data({}, item_rows or {}, **live),
                                   trainer_index=_AnyTrainer())
    return {key: getattr(reg, key) for key in registry.MERGE_KEYS}


class EnchantTableTest(unittest.TestCase):
    """The rulings, checked on the table itself."""

    def setUp(self):
        self.rows = T.enchants()

    def test_counts(self):
        self.assertEqual(Counter(r["tier"] for r in self.rows), {"leveling": 58, "endgame": 58})
        self.assertEqual(len(T.tinkers()), 4)
        self.assertEqual(len(T.items()), 116 + 4 + 1)

    def test_owner_per_slot_r23(self):
        owners = {r["slot"]: r["profession"] for r in self.rows}
        self.assertEqual(owners, {
            "head": T.ENGINEERING, "ranged": T.ENGINEERING, "shoulder": T.INSCRIPTION, "legs": T.TAILORING,
            "hands": T.LEATHERWORKING, "chest": T.ENCHANTING, "feet": T.ENCHANTING, "wrist": T.ENCHANTING,
            "back": T.ENCHANTING, "jewelry": T.ENCHANTING, "weapon": T.ENCHANTING, "twohand": T.ENCHANTING,
            "shield": T.ENCHANTING, "offhand": T.ENCHANTING,
        })

    def test_no_forbidden_stats(self):
        for r in self.rows:
            self.assertNotIn(r["stat"], T.FORBIDDEN_STATS | {STAMINA}, r["name"])

    def test_sizes(self):
        want = {"endgame": {"major": 12, "medium": 9, "minor": 7, "twohand": 14},
                "leveling": {"major": 6, "medium": 5, "minor": 4, "twohand": 8}}
        mp5 = {"endgame": {"medium": 2, "minor": 2}, "leveling": {"medium": 1, "minor": 1}}
        for r in self.rows:
            expected = (mp5 if r["stat"] == T.MP5 else want)[r["tier"]][r["size"]]
            self.assertEqual(r["amount"], expected, r["name"])

    def test_two_hand_is_two_one_hands(self):
        for tier in ("leveling", "endgame"):
            self.assertEqual(T.SIZES[tier]["twohand"], 2 * T.SIZES[tier]["minor"])

    def test_rings_share_the_neck_item(self):
        jewelry = [r for r in self.rows if r["slot"] == "jewelry"]
        self.assertEqual({r["stat"] for r in jewelry}, {T.PROC_CHANCE, T.COOLDOWN_HASTE, T.MP5, T.BLOCK})
        item_class, subclass, inv = jewelry[0]["target"]
        self.assertEqual(inv, (1 << 2) | (1 << 11))  # neck and finger

    def test_level_gates(self):
        for r in self.rows:
            gate = 60 if r["tier"] == "endgame" else 0
            self.assertEqual((r["min_level"], r["required_level"]), (gate, gate), r["name"])

    def test_weapon_masks_split(self):
        targets = {r["slot"]: r["target"] for r in self.rows}
        self.assertEqual(targets["weapon"][1] & targets["twohand"][1], 0)
        self.assertEqual(targets["ranged"][1], 0x4000C)

    def test_ids_unique_and_in_blocks(self):
        tinkers, buckle = T.tinkers(), T.BUCKLE
        enchants = [r["enchant"] for r in self.rows] + [t["enchant"] for t in tinkers] + [buckle["enchant"]]
        items = [r["item"] for r in T.items()]
        spells = ([r["use_spell"] for r in self.rows] + [r["craft_spell"] for r in self.rows]
                  + [t[k] for t in tinkers for k in ("use_spell", "craft_spell", "effect_spell")]
                  + [buckle["use_spell"], buckle["craft_spell"]])
        slas = [r["sla"] for r in self.rows] + [t["sla"] for t in tinkers] + [buckle["sla"]]
        for name, ids in (("enchants", enchants), ("items", items), ("spells", spells), ("slas", slas)):
            self.assertEqual(len(ids), len(set(ids)), name)
        self.assertTrue(all(5800 <= i <= 5999 for i in enchants))
        self.assertTrue(all(79000 <= i <= 79199 for i in items))
        self.assertLess(IDS["item_minted"]["end"], 79000)
        crafting = IDS["reservations"]["crafting"]
        self.assertTrue(all(crafting["spell"]["start"] <= i <= crafting["spell"]["end"] for i in spells))
        self.assertTrue(all(crafting["skilllineability"]["start"] <= i <= crafting["skilllineability"]["end"]
                            for i in slas))

    def test_names_unique_and_fit(self):
        names = [r["name"] for r in T.items()]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(len(n) <= 80 for n in names))

    def test_inscription_inks_by_stat_color(self):
        for r in self.rows:
            if r["profession"] == T.INSCRIPTION:
                self.assertEqual(r["reagents"][0][0], T.INK_FOR_STAT[r["stat"]], r["name"])


class EnchantDeclarationTest(unittest.TestCase):
    """What source/world/crafting_enchants.py declares."""

    @classmethod
    def setUpClass(cls):
        cls.dsl = _load("crafting_enchants.py")
        cls.enchants = {r["ID"]: r for r in cls.dsl["spell_item_enchantments"]}
        cls.spells = {s["id"]: s for s in cls.dsl["spells"]}

    def test_row_counts(self):
        self.assertEqual(len(self.enchants), 116 + 4 + 1)
        self.assertEqual(len(self.dsl["skill_line_abilities"]), 121)
        self.assertEqual(len(self.spells), 121 * 2 + 4)
        self.assertEqual(len(self.dsl["trainer_spells"]), 121)

    def test_enchant_spell_item_round_trip(self):
        items = {r["item"]: r for r in T.items()}
        for r in T.enchants():
            row = self.enchants[r["enchant"]]
            self.assertEqual((row["Effect_1"], row["EffectArg_1"], row["EffectPointsMin_1"]),
                             (5, r["stat"], r["amount"]))
            self.assertEqual((row["RequiredSkillID"], row["MinLevel"]), (0, r["min_level"]))
            use = self.spells[r["use_spell"]]["raw_overrides"]
            self.assertEqual(self.spells[r["use_spell"]]["effect1"]["type"], ENCHANT_ITEM)
            self.assertEqual(self.spells[r["use_spell"]]["effect1"]["misc_value"], r["enchant"])
            self.assertEqual((use["EquippedItemClass"], use["EquippedItemSubclass"], use["EquippedItemInvTypes"]),
                             r["target"], r["name"])
            self.assertEqual(use["Targets"], 16)
            self.assertEqual(items[r["item"]]["use_spell"], r["use_spell"])
            craft = self.spells[r["craft_spell"]]["raw_overrides"]
            self.assertEqual(craft["EffectItemType_1"], r["item"])

    def test_trainers(self):
        by_spell = {row["SpellId"]: row["TrainerId"] for row in self.dsl["trainer_spells"]}
        for r in T.enchants():
            self.assertEqual(by_spell[r["craft_spell"]], T.TRAINER[r["profession"]], r["name"])
        for t in T.tinkers():
            self.assertEqual(by_spell[t["craft_spell"]], T.TRAINER[T.ENGINEERING])
        self.assertEqual(by_spell[T.BUCKLE["craft_spell"]], T.TRAINER[T.BLACKSMITHING])

    def test_tinkers_are_use_spell_enchants(self):
        scripted = {r["spell_id"] for r in self.dsl["spell_script_names"]}
        for t in T.tinkers():
            row = self.enchants[t["enchant"]]
            self.assertEqual((row["Effect_1"], row["EffectArg_1"], row["MinLevel"]), (7, t["effect_spell"], 60))
            effect = self.spells[t["effect_spell"]]["raw_overrides"]
            self.assertEqual(effect["Category"], T.TINKER_CATEGORY)
        self.assertEqual(scripted, {207481})  # Force Field Lens
        # base_points is the raw DBC column (value - 1).
        self.assertEqual(self.spells[207480]["effect1"]["base_points"] + 1, T.HYPERSPEED_HASTE)
        self.assertEqual(self.spells[207482]["effect1"]["base_points"] + 1, T.MANA_SIPHON_PCT)
        self.assertEqual(self.spells[207483]["effect1"]["base_points"] + 1, T.TARGETING_CRIT)

    def test_buckle(self):
        row = self.enchants[T.BUCKLE["enchant"]]
        self.assertEqual((row["Effect_1"], row["EffectPointsMin_1"], row["MinLevel"]), (8, 1, 60))
        use = self.spells[T.BUCKLE["use_spell"]]
        self.assertEqual(use["effect1"]["type"], ADD_SOCKET)
        self.assertEqual(use["raw_overrides"]["EquippedItemInvTypes"], 1 << 6)


class RemapTest(unittest.TestCase):
    """The Hit / Expertise / Defense rule over the stock SpellItemEnchantment.dbc."""

    @classmethod
    def setUpClass(cls):
        cls.stock = state.load_stock_rows(dbcfmt.SPELLITEMENCHANTMENT)

    def test_every_carrier_is_remapped(self):
        changes = R.remapped(self.stock)
        self.assertEqual(len(changes), 215)
        for row_id, change in changes.items():
            row = {**self.stock[row_id], **change}
            self.assertFalse(R.carries_hed(row), row_id)

    def test_known_rows(self):
        changes = R.remapped(self.stock)
        self.assertEqual(changes[3858], {"EffectArg_1": R.CRIT, "Name_Lang_enUS": "+5 Critical Strike Rating"})
        self.assertEqual(changes[924]["EffectArg_1"], R.DODGE)
        merged = {**self.stock[2999], **changes[2999]}  # +16 Defense and +17 Dodge -> +33 Dodge
        self.assertEqual((merged["EffectArg_1"], merged["EffectPointsMin_1"], merged["Effect_2"]), (R.DODGE, 33, 0))
        self.assertEqual(merged["Name_Lang_enUS"], "+33 Dodge Rating")

    def test_declarations(self):
        elixir_item = {45621: {"entry": 45621, "name": "Elixir of Minor Accuracy"}}
        dsl = _load("crafting_hed_remap.py", elixir_item, **spell_tables.stock_enchant_loaders())
        self.assertEqual(len(dsl["spell_item_enchantments"]), 215)
        elixir = {s["id"]: s for s in dsl["spells"]}[63729]
        self.assertEqual(elixir["effect1"]["misc_value"], (1 << 8) | (1 << 9) | (1 << 10))
        renamed = {row["entry"]: row for row in dsl["item_templates"]}[45621]
        self.assertEqual((renamed["name"], renamed["_update_columns"]), ("Elixir of Minor Precision", ("name",)))

    def test_log_current(self):
        log = TOOL_ROOT.parents[1] / ".agents" / "plans" / "crafting-rework" / "crafting-rework.C6-HED-REMAP.md"
        if not log.exists():
            self.skipTest("the plan folder is not in this checkout")
        self.assertIn("\n".join(R.log_lines(self.stock)), log.read_text())


class EnchantItemFilesTest(unittest.TestCase):
    """The generated item_template SQL and items.csv rows match the table and lint clean."""

    def test_files_current(self):
        rows = write_enchant_items.item_rows()
        self.assertEqual(write_enchant_items.SQL_PATH.read_text(), write_enchant_items.render_sql(rows),
                         "rerun apps/dbc-tools/write_enchant_items.py")
        self.assertEqual(write_enchant_items.ITEMS_CSV.read_text(),
                         write_enchant_items.render_csv(write_enchant_items.ITEMS_CSV.read_text(), rows))

    def test_rows(self):
        rows = {r["entry"]: r for r in write_enchant_items.item_rows()}
        self.assertEqual(len(rows), 121)
        for item in T.items():
            row = rows[item["item"]]
            self.assertEqual((row["class"], row["subclass"], row["spellid_1"], row["spellcharges_1"], row["bonding"]),
                             (0, 6, item["use_spell"], -1, 0))
            self.assertLessEqual(row["ItemLevel"], 63)  # the AH bot's item level cap
            self.assertLessEqual(row["RequiredLevel"], 60)
            self.assertGreater(row["SellPrice"], 0)

    def test_sql_lints(self):
        text = write_enchant_items.SQL_PATH.read_text().rstrip("\n")
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))
        self.assertEqual(codestyle_sql(text).returncode, 0)


if __name__ == "__main__":
    unittest.main()
