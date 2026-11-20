"""
Blackrock Depths build WP-IT, the event items: source/items/blackrock_depths_event_items.py (the table),
source/npcs/blackrock_depths/event_items.py (the use spells 211260 / 211261), the client Item.dbc rows
(source/items.csv 70620-70623) and the SQL rev (data/sql/updates/pending_db_world/rev_event_items_blackrock_depths.sql).

Checks:
  - the four items and the two spells sit in the `blackrock_depths` reservation (items 70620-70629, the event items'
    spell slice 211260-211269);
  - every item has a client Item.dbc row (source/items.csv) and an item_template row (the SQL rev) that agree on the
    class, subclass, display, material, inventory type and the use spell (a custom item needs both, memory
    dbc-tools-item-support), and the table matches both;
  - the bags: green, flag 4 (opens with a right click), 20 to 60 gold, loot over the 37 C5 rare cuts (one gem roll on
    70620, two on 70623), the Cinder green / unique / no bind / non-equippable / consumed on use / not map-limited, the
    rope non-equippable / consumed on use / limited to map 230;
  - the use spells: DUMMY on the user, no cast time, no cooldown, scripted by the names the boss WPs register;
  - the stock keys: Relic Coffer Key 11078 and Dark Keeper Key 11197 to green, the Relic Coffer Key drops at 1% (100%
    from the six Dark Keepers), the Dark Keepers' Dark Keeper Key rows removed, no Item.dbc row for either (quality is
    no Item.dbc field).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_event_items.py
"""

from __future__ import annotations

import csv
import re
import runpy
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import crafting_gems_data as gems_data  # noqa: E402
from lib import source  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

TABLE_FILE = TOOL_ROOT / "source" / "items" / "blackrock_depths_event_items.py"
SPELLS_PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
ITEMS_CSV = TOOL_ROOT / "source" / "items.csv"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_event_items_blackrock_depths.sql"

BAG, CINDER, ROPE, BAG_HEROIC = 70620, 70621, 70622, 70623
SPELL_CINDER, SPELL_ROPE = 211260, 211261
EVENT_SPELL_SLICE = range(211260, 211270)
ITEM_FLAG_HAS_LOOT = 4
QUALITY_POOR, QUALITY_COMMON, QUALITY_UNCOMMON = 0, 1, 2
MAP_BLACKROCK_DEPTHS = 230
DARK_KEEPERS = (9437, 9438, 9439, 9441, 9442, 9443)
SPELL_EFFECT_DUMMY = 3
TARGET_UNIT_CASTER = 1

ITEM_COLUMNS = (
    "entry", "class", "subclass", "SoundOverrideSubclass", "name", "displayid", "Quality", "Flags", "BuyCount",
    "BuyPrice", "SellPrice", "InventoryType", "AllowableClass", "AllowableRace", "ItemLevel", "RequiredLevel",
    "maxcount", "stackable", "spellid_1", "spelltrigger_1", "spellcharges_1", "spellppmRate_1", "spellcooldown_1",
    "spellcategory_1", "spellcategorycooldown_1", "bonding", "description", "Material", "sheath", "minMoneyLoot",
    "maxMoneyLoot", "Map", "VerifiedBuild",
)


def _load_npcs():
    t = id_blocks
    return registry.load_class_package(
        SPELLS_PACKAGE, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=t.spell_tables.dsl_live_data(
            {}, t.spell_tables.load_live_item_template_rows,
            lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
            lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
            lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
        ),
    )


def _split_tuple(text: str) -> list:
    """A SQL value tuple's fields: numbers as int, quoted strings unescaped ('' -> ')."""
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch in " ,\n\t":
            i += 1
        elif ch == "'":
            j = i + 1
            buf = []
            while True:
                if text[j] == "'" and j + 1 < n and text[j + 1] == "'":
                    buf.append("'")
                    j += 2
                elif text[j] == "'":
                    break
                else:
                    buf.append(text[j])
                    j += 1
            out.append("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ", \n\t":
                j += 1
            out.append(int(text[i:j]))
            i = j
    return out


def _item_template_rows(sql: str) -> dict[int, dict]:
    block = re.search(r"INSERT INTO `item_template`.*?VALUES\n(.*?)\n\s+ON DUPLICATE KEY", sql, re.S)
    assert block, "item_template insert"
    rows = {}
    for match in re.finditer(r"^\((\d+),(?:.|\n)*?\)(?=,\n\(|\Z)", block.group(1), re.M):
        fields = _split_tuple(match.group(0)[1:-1])
        assert len(fields) == len(ITEM_COLUMNS), (len(fields), fields[:5])
        rows[fields[0]] = dict(zip(ITEM_COLUMNS, fields))
    return rows


class EventItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = runpy.run_path(str(TABLE_FILE))
        cls.items = cls.table["EVENT_ITEMS"]
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.rows = _item_template_rows(cls.sql)
        with open(ITEMS_CSV, newline="", encoding="utf-8") as f:
            cls.csv_rows = {int(r["id"]): r for r in csv.DictReader(f) if r.get("id", "").strip().isdigit()}
        npcs = _load_npcs()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in EVENT_SPELL_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names
                       if int(e["spell_id"]) in EVENT_SPELL_SLICE}

    # --- ids -------------------------------------------------------------------------------------------------------

    def test_the_items_sit_in_the_reservation(self):
        self.assertEqual(sorted(self.items), [BAG, CINDER, ROPE, BAG_HEROIC])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"item": list(self.items)}), [])

    def test_the_spells_sit_in_the_event_items_slice(self):
        self.assertEqual(sorted(self.spells), [SPELL_CINDER, SPELL_ROPE])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])

    # --- Item.dbc and item_template agree --------------------------------------------------------------------------

    def test_every_item_has_a_client_row_and_a_server_row_that_agree(self):
        self.assertEqual(sorted(self.rows), sorted(self.items))
        for entry, item in self.items.items():
            row, csv_row = self.rows[entry], self.csv_rows.get(entry)
            self.assertIsNotNone(csv_row, f"{entry} has no source/items.csv (Item.dbc) row")
            self.assertEqual(
                (int(csv_row["class_id"]), int(csv_row["subclass_id"]), int(csv_row["material"]),
                 int(csv_row["display_info_id"]), int(csv_row["inventory_type"]), int(csv_row["sheathe_type"])),
                (row["class"], row["subclass"], row["Material"], row["displayid"], row["InventoryType"], row["sheath"]),
                f"{entry}: Item.dbc row vs item_template row")
            self.assertEqual(
                (item["klass"], item["subclass"], item["material"], item["display"], item["inventory_type"],
                 item["sheath"], item["name"], item["quality"], item["flags"], item["bonding"], item["maxcount"],
                 item["stackable"], item["item_level"], item["sell_price"], item["map"], item["spell"], item["charges"],
                 item["money"][0], item["money"][1], item["description"]),
                (row["class"], row["subclass"], row["Material"], row["displayid"], row["InventoryType"], row["sheath"],
                 row["name"], row["Quality"], row["Flags"], row["bonding"], row["maxcount"], row["stackable"],
                 row["ItemLevel"], row["SellPrice"], row["Map"], row["spellid_1"], row["spellcharges_1"],
                 row["minMoneyLoot"], row["maxMoneyLoot"], row["description"]),
                f"{entry}: table vs item_template row")

    def test_nothing_is_equippable(self):
        for entry, row in self.rows.items():
            self.assertEqual(row["InventoryType"], 0, entry)

    def test_the_use_items_cast_on_use_and_are_consumed(self):
        for entry, spell_id in ((CINDER, SPELL_CINDER), (ROPE, SPELL_ROPE)):
            row = self.rows[entry]
            self.assertEqual((row["spellid_1"], row["spelltrigger_1"], row["spellcharges_1"]), (spell_id, 0, -1), entry)
            self.assertEqual((row["spellcooldown_1"], row["spellcategory_1"], row["spellcategorycooldown_1"]),
                             (-1, 0, -1), entry)
        for entry in (BAG, BAG_HEROIC):
            self.assertEqual(self.rows[entry]["spellid_1"], 0)

    # --- the bags ---------------------------------------------------------------------------------------------------

    def test_the_bags_open_and_pay_20_to_60_gold(self):
        for entry in (BAG, BAG_HEROIC):
            row = self.rows[entry]
            self.assertEqual(row["Quality"], QUALITY_UNCOMMON, entry)
            self.assertEqual(row["Flags"], ITEM_FLAG_HAS_LOOT, entry)
            self.assertEqual((row["minMoneyLoot"], row["maxMoneyLoot"]), (20 * 10000, 60 * 10000), entry)
            self.assertEqual(row["Map"], 0, entry)
        # the stock sacks they copy
        self.assertEqual(self.csv_rows[BAG]["display_info_id"], "1168")
        self.assertEqual(self.csv_rows[BAG_HEROIC]["display_info_id"], "4056")

    def test_the_bag_loot_is_one_gem_roll_and_the_heroic_bag_two(self):
        cuts = [g for g in gems_data.gems() if g["kind"] == "rare"]
        self.assertEqual(len(cuts), 37)
        first, last = self.table["RARE_CUT_FIRST"], self.table["RARE_CUT_LAST"]
        self.assertEqual([g["item"] for g in cuts], list(range(first, last + 1)))
        # one shared pool (reference 1701100), rolled once by the normal bag and twice by the heroic bag:
        # item_loot_template's key is (Entry, Item), so a gem cannot sit in two groups of one bag
        pool = [int(i) for i in re.findall(r"^\(1701100, (\d+), 0, 0, 0, 1, 1, 1, 1, '", self.sql, re.M)]
        self.assertEqual(pool, [g["item"] for g in cuts])
        refs = re.findall(r"^\((70620|70623), 1701100, 1701100, 100, 0, 1, 0, (\d), (\d), '", self.sql, re.M)
        self.assertEqual(sorted(refs), [("70620", "1", "1"), ("70623", "2", "2")])  # MinCount = MaxCount
        self.assertIsNone(re.search(r"^\((70620|70623), 707\d\d,", self.sql, re.M))
        ids = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")["event_loot_reference"]
        self.assertTrue(ids["start"] <= 1701100 <= ids["end"])
        self.assertEqual(self.items[BAG]["gems"], 1)
        self.assertEqual(self.items[BAG_HEROIC]["gems"], 2)
        self.assertIn("DELETE FROM `item_loot_template` WHERE `Entry` IN (70620, 70623);", self.sql)
        self.assertIn("DELETE FROM `reference_loot_template` WHERE `Entry` = 1701100;", self.sql)

    # --- the Cinder and the rope --------------------------------------------------------------------------------------

    def test_the_cinder_is_green_unique_unbound_and_travels(self):
        row = self.rows[CINDER]
        self.assertEqual((row["Quality"], row["bonding"], row["maxcount"], row["Map"]), (QUALITY_UNCOMMON, 0, 1, 0))
        self.assertEqual(row["name"], "Cinder of the Firelord")

    def test_the_rope_is_limited_to_the_dungeon(self):
        row = self.rows[ROPE]
        self.assertEqual((row["Map"], row["Quality"], row["bonding"]), (MAP_BLACKROCK_DEPTHS, QUALITY_COMMON, 0))

    # --- the use spells -----------------------------------------------------------------------------------------------

    def test_the_use_spells_are_self_cast_dummies(self):
        for spell_id in (SPELL_CINDER, SPELL_ROPE):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual((effect["type"], effect["implicit_target_a"]), (SPELL_EFFECT_DUMMY, TARGET_UNIT_CASTER),
                             spell_id)
            self.assertIsNone(spell["effect2"])
            self.assertEqual(spell["range_yards"], "self", spell_id)
            self.assertEqual(spell["raw_overrides"]["CastingTimeIndex"], 1, spell_id)       # instant
            self.assertEqual(spell["raw_overrides"]["EquippedItemClass"], -1, spell_id)
            for column in ("cooldown_ms", "category_cooldown_ms", "mana_cost", "mana_cost_pct", "duration_ms"):
                self.assertEqual(spell.get(column, 0), 0, f"{spell_id} {column}")

    def test_the_spells_are_bound_to_the_boss_wp_script_names(self):
        self.assertEqual(self.scripts, {
            (SPELL_CINDER, "spell_brd_cinder_of_the_firelord"),
            (SPELL_ROPE, "spell_brd_guzzler_rope"),
        })

    def test_the_table_names_the_spells(self):
        self.assertEqual(self.table["SPELL_CINDER"], SPELL_CINDER)
        self.assertEqual(self.table["SPELL_ROPE"], SPELL_ROPE)
        self.assertEqual(self.items[CINDER]["spell"], SPELL_CINDER)
        self.assertEqual(self.items[ROPE]["spell"], SPELL_ROPE)

    # --- the stock keys -----------------------------------------------------------------------------------------------

    def test_the_stock_keys_go_green(self):
        self.assertIn("UPDATE `item_template` SET `Quality` = 2 WHERE `entry` IN (11078, 11197);", self.sql)
        self.assertEqual(set(self.table["STOCK_KEYS"]), {11078, 11197})
        for entry in (11078, 11197):    # quality is no Item.dbc field: no client row
            self.assertNotIn(entry, self.csv_rows)
        self.assertNotIn("`item_template` SET `bonding`", self.sql)   # they still do not bind

    def test_the_relic_coffer_key_drops_at_one_percent_and_the_dark_keepers_at_hundred(self):
        keepers = ", ".join(str(k) for k in DARK_KEEPERS)
        self.assertEqual(tuple(self.table["DARK_KEEPERS"]), DARK_KEEPERS)
        self.assertEqual(self.table["RELIC_COFFER_KEY_DROP_PCT"], 1)
        self.assertIn("UPDATE `creature_loot_template` SET `Chance` = 1 WHERE `Item` = 11078 AND `Reference` = 0\n"
                      f"    AND `Entry` NOT IN ({keepers});", self.sql)
        self.assertIn("UPDATE `creature_loot_template` SET `Chance` = 100 WHERE `Item` = 11078 AND `Reference` = 0\n"
                      f"    AND `Entry` IN ({keepers});", self.sql)
        self.assertIn(f"DELETE FROM `creature_loot_template` WHERE `Item` = 11197 AND `Entry` IN ({keepers});",
                      self.sql)

    # --- hygiene ------------------------------------------------------------------------------------------------------

    def test_the_sql_rev_never_deletes_item_templates_and_stays_in_120_columns(self):
        self.assertNotIn("DELETE FROM `item_template`", self.sql)
        for number, line in enumerate(self.sql.splitlines(), 1):
            self.assertLessEqual(len(line), 120, f"line {number}")
            self.assertEqual(line, line.rstrip(), f"trailing whitespace, line {number}")


if __name__ == "__main__":
    unittest.main()
