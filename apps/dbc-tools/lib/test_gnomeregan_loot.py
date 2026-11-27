"""
Gnomeregan build, WP L-1: the declarations in source/items/gnomeregan_loot.py (item keys from gnomeregan.py and
gnomeregan_hard_mode.py, the gear stage merged as #162) and the hand rev data/sql/updates/pending_db_world/
rev_loot_gnomeregan.sql.

Techbot (301105), Viscous Fallout, Electrocutioner 6000, the Mobile Alert System (301110), Mekgineer Thermaplugg and
the Dark Iron Ambassador: each list at the Normal tier on the normal lootid and the Heroic tier on the heroic body's
own lootid, the stock items kept in place (`item(base=)`), the shared rare list 1090000 emptied (its 20 users, then the
pool), the cut rows of the moved items and Thermaplugg's three hard mode items at LootMode 2. Crowd Pummeler 9-60 drops
from his chest (gameobject 301380 normal / 301381 heroic, hand SQL): the list and the rows his body held, with the BRD
duplicate-item rule (`test_no_chest_lists_an_item_twice`). The rev also writes Techbot's own table, the Sparklematic
box cut (G27 A), the White Punch Card rows (#43 A) and the Grime-Encrusted Ring rows (#44 A). The rows themselves (and
their rules and rendering) are test_loot_tables.py's; the real plan (tiers, the live stock groups) is
`generate.py --check`'s.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_loot.py
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_gnomeregan_items as gear  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.heroic_templates import LOCK_PATH, parse_lock  # noqa: E402

GN_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "gnomeregan.py"
LOOT_FILE = TOOL_ROOT / "source" / "items" / "gnomeregan_loot.py"
ITEM_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
NPCS = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
REV = PENDING / "rev_loot_gnomeregan.sql"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan" / "GnomereganRework.h"

TECHBOT, FALLOUT, ELECTRO, ALERT, PUMMELER, THERMAPLUGG, AMBASSADOR = (
    gear.TECHBOT, gear.FALLOUT, gear.ELECTRO, gear.ALERT, gear.PUMMELER, gear.THERMAPLUGG, gear.AMBASSADOR)

LIST_GROUP = 1
HARD_MODE_GROUP = 4

# boss -> (normal lootid, heroic lootid). Techbot and the Alert System are the new bosses (their own entries are their
# lootids); Pummeler's body carries nothing (his chest does).
LOOTIDS = {
    TECHBOT: (301105, 310575), FALLOUT: (7079, 310567), ELECTRO: (6235, 310562), ALERT: (301110, 310577),
    THERMAPLUGG: (7800, 310571), AMBASSADOR: (6228, 310556),
}
THERMAPLUGG_HEROIC = LOOTIDS[THERMAPLUGG][1]
PUMMELER_BODY = 6229
CHESTS = {"normal": 301380, "heroic": 301381}
HARD_MODE = {"gnomer_leaking_reactor_core", "gnomer_walking_bomb_launcher", "gnomer_master_punch_card"}
SIZES = {TECHBOT: 7, FALLOUT: 7, ELECTRO: 7, ALERT: 7, THERMAPLUGG: 9, AMBASSADOR: 3}

SHARED_RARE_LIST = 1090000
SHARED_RARE_LIST_USERS = {
    6206, 6211, 6212, 6218, 6219, 6220, 6223, 6225, 6226, 6227, 6228, 6230, 6232, 6233, 6234, 6329, 6391, 6392, 6407,
    7079,
}
# The ten items of reference 1090000 (live SELECT 2026-11-26) and where they went.
SHARED_RARE_LIST_ITEMS = {
    9485: ALERT, 9486: ELECTRO, 9487: TECHBOT, 9488: TECHBOT, 9489: ALERT, 9490: PUMMELER, 9491: TECHBOT,
    9508: THERMAPLUGG, 9509: ALERT, 9510: FALLOUT,
}
# creature_loot_template group 0 cuts (live SELECT 2026-11-26): the ruled ones (#42 A), then the three the ruling did
# not name (Grubbis's Paws, the Ambusher's seven 0.02% rows, the Amulet's rows on inside trash).
CUTS = {
    6231: {9486, 9487, 9488}, 6215: {9485, 9486, 9510}, 7849: {10299}, 7361: {9445},
    6207: {9485, 9486, 9487, 9488, 9490, 9509, 10299}, 6224: {10299},
    6206: {10299}, 6211: {10299}, 6212: {10299}, 6329: {10299}, 6392: {10299},
}
# The quest rows, keys, cloth and schematics that stay as stock rows no declaration may name.
KEPT_ROWS = {
    9277, 9309, 9327,  # the Memory Core, Guts and DELTA card
    6893,  # the Workshop Key
    9299,  # Thermaplugg's Safe Combination
    11827, 11828, 4411, 4413, 7742,  # the schematics
    9308, 9326, 9279,  # the Grime-Encrusted Object and Ring, the White Punch Card
    7070, 9451,  # Fallout's waters
}
WHITE_CARD, RING = 9279, 9326
CARD_DROPPERS = {6206, 6207, 6211, 6329}
RING_DROPPERS = {6206, 6211}
PUMMELER_BODY_ROWS = {9309: (5.0, 1, 8, 10), 9327: (1.0, 0, 1, 1), 11827: (50.0, 0, 1, 1)}  # chance, quest, min, max
TECHBOT_OUTSIDE = 6231


def _lock_entries() -> dict[tuple[str, str], int]:
    entries = {}
    for line in ITEM_LOCK.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit() and "retired" not in parts:
            entries[(parts[1], parts[2])] = int(parts[0])
    return entries


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "gnomeregan_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


def _boss_keys(boss: str) -> set[str]:
    return {key for key, (owner, _stock, _stats) in gear.LIST.items() if owner == boss}


def _statements(text: str, table: str) -> list[str]:
    return re.findall(rf"INSERT INTO `{table}`[^;]*;", text, re.S)


_ROW = re.compile(r"^\((\d+), (\d+), (\d+), ([\d.]+), (\d+), (\d+), (\d+), (\d+), (\d+), '(.*)'\)[,;]$", re.M)


def _loot_rows(text: str, table: str) -> dict[int, list[dict]]:
    """The value rows of every `INSERT INTO <loot table>` of the rev, by Entry."""
    rows: dict[int, list[dict]] = {}
    for statement in _statements(text, table):
        for m in _ROW.finditer(statement):
            rows.setdefault(int(m[1]), []).append(dict(
                item=int(m[2]), ref=int(m[3]), chance=float(m[4]), quest=int(m[5]), mode=int(m[6]), group=int(m[7]),
                min=int(m[8]), max=int(m[9]), comment=m[10]))
    return rows


class LootDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, cls.decls = _declarations()
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("gnomer_")}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and not d.removal and d.chance is None}
        cls.group_removals = {(d.lootid, d.group): d for d in cls.decls if d.removal}
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.chances = [d for d in cls.decls if d.chance is not None]
        cls.pool_removals = [d for d in cls.decls if d.pool_removal]
        cls.lock = _lock_entries()

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for boss, (normal, heroic) in LOOTIDS.items():
            keys = _boss_keys(boss)
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=boss, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes_are_the_docs_boss_list_rows(self):
        sizes = {boss: len(self.lists[(normal, LIST_GROUP)].items) for boss, (normal, _h) in LOOTIDS.items()}
        self.assertEqual(sizes, SIZES)
        self.assertEqual(sum(sizes.values()), 40)  # plus Pummeler's 8 in the chest: the 48 of the doc
        for boss, size in sizes.items():
            self.assertEqual(gear.BOSS_COUNT[boss], size, boss)
        self.assertEqual(gear.BOSS_COUNT[PUMMELER], 8)

    def test_only_group_one_and_the_hard_mode_group_are_declared(self):
        self.assertEqual({group for _lootid, group in self.lists}, {LIST_GROUP, HARD_MODE_GROUP})
        for lootid in [x for pair in LOOTIDS.values() for x in pair]:
            self.assertIn((lootid, LIST_GROUP), self.lists)

    def test_stock_items_keep_their_stock_entries_as_the_normal_tier(self):
        bases = {decl.base for decl in self.items.values() if decl.base}
        self.assertEqual(bases, gear.STOCK_ENTRIES)
        for boss, (normal, _heroic) in LOOTIDS.items():
            on_list = {self.items[k].base for k in self.lists[(normal, LIST_GROUP)].items if self.items[k].base}
            self.assertEqual(on_list, {s for _k, (b, s, _st) in gear.LIST.items() if b == boss and s is not None},
                             boss)

    def test_no_declaration_names_a_quest_row_cloth_or_the_pummelers_body(self):
        for decl in self.decls:
            self.assertNotEqual(decl.lootid, PUMMELER_BODY, decl.where)
            self.assertFalse(set(decl.rows) & KEPT_ROWS, decl.where)
            self.assertFalse(set(decl.replaces_items) & KEPT_ROWS, decl.where)

    # --- the cut stock rows and the shared rare list ---------------------------------------------------------------

    def test_no_stock_group_is_removed_outright(self):
        self.assertEqual(self.group_removals, {})  # every stock group is replaced in place by its list

    def test_the_group_zero_cuts_are_exactly_the_live_rows_of_moved_items(self):
        cuts = {lootid: set(d.rows) for (lootid, group), d in self.row_removals.items()
                if group == 0 and d.rows and lootid not in SHARED_RARE_LIST_USERS}
        self.assertEqual(cuts, {lootid: rows for lootid, rows in CUTS.items() if lootid not in SHARED_RARE_LIST_USERS})
        # the six users that also carry the Amulet cut it in the same call (one declaration per lootid and group)
        for lootid in (6206, 6211, 6212, 6329, 6392):
            self.assertEqual(set(self.row_removals[(lootid, 0)].rows), CUTS[lootid], lootid)
        # every cut item is on a list or in the chest
        listed = {self.items[k].base for k in self.items if self.items[k].base}
        for lootid, rows in CUTS.items():
            self.assertTrue(rows <= listed, (lootid, rows - listed))
        for d in self.row_removals.values():
            self.assertTrue(d.why, d.where)

    def test_the_ruled_cuts_are_in(self):
        # handoff 7 #42 A: the outside Techbot's and Chomper's three rows each, the Alert System trash's Amulet
        self.assertEqual(set(self.row_removals[(6231, 0)].rows), {9486, 9487, 9488})
        self.assertEqual(set(self.row_removals[(6215, 0)].rows), {9485, 9486, 9510})
        self.assertEqual(set(self.row_removals[(7849, 0)].rows), {10299})

    def test_the_shared_rare_list_is_emptied_and_removed(self):
        users = {lootid for (lootid, group), d in self.row_removals.items()
                 if group == 0 and SHARED_RARE_LIST in d.ref_rows}
        self.assertEqual(users, SHARED_RARE_LIST_USERS)
        self.assertEqual(len(users), 20)
        self.assertEqual([d.reference for d in self.pool_removals], [SHARED_RARE_LIST])
        self.assertTrue(self.pool_removals[0].why)

    def test_every_item_of_the_shared_rare_list_has_a_boss_or_the_chest(self):
        by_base = {decl.base: key for key, decl in self.items.items() if decl.base}
        self.assertEqual(set(SHARED_RARE_LIST_ITEMS), set(by_base) & set(SHARED_RARE_LIST_ITEMS))
        self.assertEqual(len(SHARED_RARE_LIST_ITEMS), 10)
        for item, boss in SHARED_RARE_LIST_ITEMS.items():
            self.assertEqual(gear.LIST[by_base[item]][0], boss, (item, by_base[item]))

    def test_the_other_ref_users_carry_only_the_reference_row(self):
        for lootid in SHARED_RARE_LIST_USERS - set(CUTS):
            self.assertEqual(self.row_removals[(lootid, 0)].rows, (), lootid)

    # --- the hard mode list ----------------------------------------------------------------------------------------

    def test_the_hard_mode_list_is_group_four_of_thermapluggs_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(THERMAPLUGG_HEROIC, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, HARD_MODE, False))
        self.assertEqual(len(decl.items), 3)
        names = sorted(self.merged_item_name(k) for k in HARD_MODE)
        self.assertEqual(names, ["Leaking Reactor Core", "Master Punch Card", "Walking Bomb Launcher"])
        # the heroic list stays: a lit kill adds one of the three on top of it
        self.assertIn((THERMAPLUGG_HEROIC, LIST_GROUP), self.lists)
        # the normal lootid gets none (heroic only: the console is offered on heroic)
        self.assertNotIn((LOOTIDS[THERMAPLUGG][0], HARD_MODE_GROUP), self.lists)

    def merged_item_name(self, key: str) -> str:
        return self.items[key].name

    def test_only_that_one_group_rolls_at_loot_mode_2(self):
        modes = sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1)
        self.assertEqual(modes, [(THERMAPLUGG_HEROIC, HARD_MODE_GROUP)])

    def test_the_hard_mode_group_does_not_collide_with_a_stock_group_of_thermaplugg(self):
        # live groups of 7800: 0 (key, Guts, DELTA, Safe Combination), 1 (the list), 2 (three schematics at 2%), 3 (Pet
        # Bombling at 90%); the heroic copy takes 0, 2 and 3 and the DSL owns 1 and 4
        self.assertNotIn(HARD_MODE_GROUP, (0, 1, 2, 3))

    def test_the_hard_mode_items_are_on_the_hard_mode_ladder(self):
        for key in HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    def test_the_hard_mode_loot_bit_is_the_one_the_instance_sets(self):
        kit = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Kit" / "DungeonKit.cpp"
        if kit.is_file():
            self.assertIn("AddLootMode(LOOT_MODE_HARD_MODE_1)", kit.read_text(encoding="utf-8"))
        self.assertEqual(L.LOOT_MODE_HARD_MODE_1, 2)

    # --- groups and counts -----------------------------------------------------------------------------------------

    def test_no_flex_groups_no_tokens_no_picks_and_no_chance_rows(self):
        self.assertTrue(all(d.picks == 1 and d.reference is None for d in self.decls if d.listing))
        self.assertFalse([d for d in self.decls if d.loot_mode & 0x8])
        self.assertEqual(self.chances, [])

    def test_declaration_counts(self):
        # 6 bosses x 2 lootids + the hard mode group; the row cuts of 20 users and 6 other creatures; 1 pool
        others = {lootid for lootid in CUTS if lootid not in SHARED_RARE_LIST_USERS}
        self.assertEqual(len(self.lists), 6 * 2 + 1)
        self.assertEqual(len(self.row_removals), 20 + len(others))
        self.assertEqual(len(others), 6)  # 6231, 6215, 7849, 7361, 6207, 6224
        self.assertEqual(len(self.pool_removals), 1)
        self.assertEqual(len(self.decls), 13 + 26 + 1)

    # --- one item, one row -----------------------------------------------------------------------------------------

    def test_no_loot_table_lists_an_item_twice(self):
        # creature_loot_template is keyed (Entry, Item, Reference, GroupId) and the engine's group roll skips an
        # equippable the loot already holds: a duplicate item in one lootid fails db-import partway (BRD LESSONS)
        by_lootid: dict[int, list] = {}
        for (lootid, _group), decl in self.lists.items():
            by_lootid.setdefault(lootid, []).extend(decl.items)
        for lootid, keys in by_lootid.items():
            with self.subTest(lootid=lootid):
                self.assertEqual(len(keys), len(set(keys)), keys)
                bases = [self.items[k].base for k in keys if k in self.items and self.items[k].base]
                self.assertEqual(len(bases), len(set(bases)), bases)

    def test_no_item_drops_from_two_places(self):
        seen: dict[str, str] = {}
        for boss, (normal, _h) in LOOTIDS.items():
            for key in self.lists[(normal, LIST_GROUP)].items:
                self.assertNotIn(key, seen, f"{key} on {boss} and {seen.get(key)}")
                seen[key] = boss
        for key in _boss_keys(PUMMELER):  # the chest
            self.assertNotIn(key, seen, key)
            seen[key] = PUMMELER
        self.assertFalse(set(seen) & HARD_MODE)

    def test_every_gear_stage_item_is_dropped_by_someone(self):
        listed = set().union(*(self.lists[(n, LIST_GROUP)].items for n, _h in LOOTIDS.values()))
        listed |= _boss_keys(PUMMELER)
        self.assertEqual(len(listed), 48)
        self.assertEqual(listed | HARD_MODE, set(self.items),
                         "a gnomer_ item() that no boss drops, or a list key without an item()")

    # --- the items the lists name ----------------------------------------------------------------------------------

    def test_list_items_are_on_the_dungeon_ladder_and_every_declared_tier_exists(self):
        for decl in self.decls:
            if not decl.listing or decl.removal or decl.chance is not None or decl.row_removal:
                continue
            for key in decl.items:
                ladder = self.items[key].ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                if decl.tier in ("normal", "heroic"):
                    self.assertEqual(ladder.name, "vanilla_dungeon", key)


class RevTest(unittest.TestCase):
    """rev_loot_gnomeregan.sql: Pummeler's chest and his emptied body, Techbot's own table, the box cut, the cards."""

    @classmethod
    def setUpClass(cls):
        cls.text = REV.read_text(encoding="utf-8")
        cls.lock = _lock_entries()
        cls.chest = _loot_rows(cls.text, "gameobject_loot_template")
        cls.creature = _loot_rows(cls.text, "creature_loot_template")

    # --- Pummeler's chest ------------------------------------------------------------------------------------------

    def test_the_two_chests_are_the_headers_ids_and_d5s_templates(self):
        self.assertEqual(sorted(self.chest), sorted(CHESTS.values()))
        if HEADER.is_file():
            header = HEADER.read_text(encoding="utf-8")
            self.assertRegex(header, r"GO_PUMMELER_CHEST\s*=\s*301380")
            self.assertRegex(header, r"GO_PUMMELER_CHEST_HEROIC\s*=\s*301381")
        d5 = (PENDING / "rev_crowd_pummeler_gnomeregan.sql").read_text(encoding="utf-8")
        self.assertRegex(d5, r"\(301380, 3, \d+, '[^']+', '', '', '', [\d.]+, \d+, 301380,")
        self.assertRegex(d5, r"\(301381, 3, \d+, '[^']+', '', '', '', [\d.]+, \d+, 301381,")

    def test_each_chest_list_is_pummelers_list_at_its_tier(self):
        keys = _boss_keys(PUMMELER)
        self.assertEqual(len(keys), 8)
        for tier, chest in CHESTS.items():
            with self.subTest(chest=chest):
                listed = [r["item"] for r in self.chest[chest] if r["group"] == 1]
                self.assertEqual(sorted(listed), sorted(self.lock[(key, tier)] for key in keys))
                self.assertEqual(len(listed), 8)

    def test_the_list_is_one_equal_chance_group_and_the_stock_entries_are_the_normal_tier(self):
        for chest, rows in self.chest.items():
            for r in rows:
                if r["group"] == 1:
                    self.assertEqual((r["ref"], r["chance"], r["quest"], r["mode"], r["min"], r["max"]),
                                     (0, 0, 0, 1, 1, 1), (chest, r))
        normal = {r["item"] for r in self.chest[CHESTS["normal"]] if r["group"] == 1}
        self.assertTrue({9449, 9450, 9490} <= normal)  # Manual Crowd Pummeler, Operating Boots, Megachopper
        heroic = {r["item"] for r in self.chest[CHESTS["heroic"]] if r["group"] == 1}
        self.assertFalse(normal & heroic)

    def test_the_chests_hold_the_rows_his_body_held_once_each(self):
        for chest, rows in self.chest.items():
            body = {r["item"]: (r["chance"], r["quest"], r["min"], r["max"]) for r in rows if r["group"] == 0}
            self.assertEqual(body, PUMMELER_BODY_ROWS, chest)
            self.assertEqual({r["group"] for r in rows}, {0, 1}, chest)

    def test_no_chest_lists_an_item_twice(self):
        # gameobject_loot_template is keyed (Entry, Item): a duplicate fails db-import partway (BRD LESSONS section 5).
        # The glob cannot see a generated `rev_<digits>.sql`: no declaration names a reference pool of this dungeon.
        for entry, rows in self.chest.items():
            items = [row["item"] for row in rows]
            self.assertEqual(len(items), len(set(items)), entry)
        row = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*,")
        for path in sorted(PENDING.glob("*gnomeregan*.sql")):
            text = path.read_text(encoding="utf-8")
            for table in ("gameobject_loot_template", "item_loot_template", "reference_loot_template"):
                seen: set[tuple[str, str]] = set()
                for statement in re.findall(rf"INSERT INTO `{table}`[^;]*;", text, re.S):
                    values = statement.split("VALUES", 1)[-1]
                    for entry, item in row.findall(values):
                        self.assertNotIn((entry, item), seen, f"{path.name}: {table} ({entry}, {item}) twice")
                        seen.add((entry, item))

    def test_the_chest_holds_no_item_of_a_creature_list(self):
        chest_items = {r["item"] for rows in self.chest.values() for r in rows if r["group"] == 1}
        _, decls = _declarations()
        for decl in decls:
            if decl.listing and not decl.removal and decl.chance is None:
                for key in decl.items:
                    for tier in ("normal", "heroic", "heroic_hm"):
                        if (key, tier) in self.lock:
                            self.assertNotIn(self.lock[(key, tier)], chest_items, key)

    def test_every_chest_row_has_the_loot_mode_a_chest_can_use(self):
        for entry, rows in self.chest.items():
            for row in rows:
                self.assertEqual(row["mode"], 1, (entry, row))

    def test_the_chest_rows_are_deleted_first(self):
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301380, 301381);", self.text)
        self.assertLess(self.text.index("DELETE FROM `gameobject_loot_template`"),
                        self.text.index("INSERT INTO `gameobject_loot_template`"))

    # --- Pummeler's body -------------------------------------------------------------------------------------------

    def test_his_body_carries_nothing_and_no_money(self):
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` = 6229;", self.text)
        self.assertRegex(self.text, r"UPDATE `creature_template` SET `lootid` = 0, `mingold` = 0, `maxgold` = 0 "
                                    r"WHERE `entry` = 6229;")
        self.assertNotIn(PUMMELER_BODY, self.creature)  # nothing inserted for him
        # his heroic copy reads the replayed normal row: no own-loot column for 6229
        found = re.search(r"^_HEROIC_LOOTID = \(([\d, ]+)\)", GN_DUNGEON.read_text(encoding="utf-8"), re.M)
        self.assertNotIn(PUMMELER_BODY, {int(x) for x in found[1].split(",")})

    def test_the_normal_rows_name_a_lootid_that_has_a_table(self):
        # RB-28 for every carrier: a lootid with no table is a boot ERROR, an emptied one must be zeroed
        techbot = (NPCS / "techbot.py").read_text(encoding="utf-8")
        self.assertRegex(techbot, r"boss_301105 = creature_template\(\s*TECHBOT, 'Techbot',[^)]*?lootid=TECHBOT,")
        alert = (NPCS / "mobile_alert_system.py").read_text(encoding="utf-8")
        self.assertRegex(alert, r"boss_301110 = creature_template\(\s*301110, 'Mobile Alert System',[^)]*?"
                                r"lootid=301110,")
        self.assertRegex(techbot, r"(?m)^TECHBOT = 301105$")

    def test_no_gold_on_the_new_bosses_and_the_chest(self):
        for path in (NPCS / "techbot.py", NPCS / "mobile_alert_system.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("mingold=0, maxgold=0", text)
        d5 = (PENDING / "rev_crowd_pummeler_gnomeregan.sql").read_text(encoding="utf-8")
        self.assertIn("(301380, 0, 0, 0, 0, 0, 0, 0, 0)", d5)  # gameobject_template_addon: no gold
        self.assertIn("(301381, 0, 0, 0, 0, 0, 0, 0, 0)", d5)

    # --- Techbot (301105) ------------------------------------------------------------------------------------------

    def test_techbots_table_is_the_outside_techbots_less_the_list_and_the_cuts(self):
        rows = self.creature[301105]
        self.assertEqual({r["group"] for r in rows}, {0, 5})  # the DSL owns group 1
        by_item = {r["item"]: r for r in rows if not r["ref"]}
        for item in (9277, 9309):  # the Memory Core (quest 2922) and the Guts (quest 2928)
            self.assertEqual((by_item[item]["chance"], by_item[item]["quest"], by_item[item]["min"],
                              by_item[item]["max"], by_item[item]["group"]), (100.0, 1, 1, 1, 0), item)
        self.assertEqual({r["item"] for r in rows if r["ref"]}, {1})
        self.assertEqual({r["ref"] for r in rows if r["ref"]}, {1000026})  # the world loot reference, group 5
        self.assertFalse(set(by_item) & {9444, 9486, 9487, 9488})  # the shell is the list's; the 0.04% rows are cut
        self.assertEqual(sorted(by_item), [4363, 4364, 4371, 4377, 4382, 9277, 9309])
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` = 301105 AND `GroupId` IN (0, 5);", self.text)

    def test_techbots_questitem_glow_matches_the_stock_rows(self):
        self.assertIn("DELETE FROM `creature_questitem` WHERE `CreatureEntry` = 301105;", self.text)
        self.assertRegex(self.text, r"INSERT INTO `creature_questitem`[^;]*\(301105, 0, 9277, 0\),\s*"
                                    r"\(301105, 1, 9309, 0\);")

    # --- the box, the White card and the ring ----------------------------------------------------------------------

    def test_the_amulet_leaves_the_sparklematic_box_and_the_band_stays(self):
        self.assertIn("DELETE FROM `item_loot_template` WHERE `Entry` = 9363 AND `Item` = 10299;", self.text)
        self.assertNotIn("10298", re.sub(r"--[^\n]*", "", self.text))

    def test_the_white_card_drops_at_its_stock_ten_percent_from_the_four_inside_kin(self):
        cards = {entry: [r for r in rows if r["item"] == WHITE_CARD] for entry, rows in self.creature.items()
                 if any(r["item"] == WHITE_CARD for r in rows)}
        self.assertEqual(set(cards), CARD_DROPPERS)
        for entry, rows in cards.items():
            self.assertEqual(len(rows), 1, entry)
            r = rows[0]
            self.assertEqual((r["chance"], r["quest"], r["group"], r["ref"], r["min"], r["max"]),
                             (10.0, 0, 0, 0, 1, 1), entry)

    def test_the_ring_drops_at_the_agents_stock_eight_percent_from_burrowers_and_reavers(self):
        rings = {entry for entry, rows in self.creature.items() if any(r["item"] == RING for r in rows)}
        self.assertEqual(rings, RING_DROPPERS)
        for entry in RING_DROPPERS:
            r = [r for r in self.creature[entry] if r["item"] == RING][0]
            self.assertEqual((r["chance"], r["quest"], r["group"]), (8.0, 0, 0))
        self.assertNotIn(6212, self.creature)  # the Agents keep their own row

    def test_the_card_and_ring_rows_are_deleted_before_they_are_inserted(self):
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` IN (6206, 6207, 6211, 6329) "
                      "AND `Item` = 9279;", self.text)
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` IN (6206, 6211) AND `Item` = 9326;",
                      self.text)

    def test_every_insert_has_a_delete_before_it(self):
        for table in ("creature_loot_template", "gameobject_loot_template", "creature_questitem"):
            inserts = [m.start() for m in re.finditer(rf"INSERT INTO `{table}`", self.text)]
            deletes = [m.start() for m in re.finditer(rf"DELETE FROM `{table}`", self.text)]
            self.assertGreaterEqual(len(deletes), len(inserts), table)  # Pummeler's body is a delete with no insert
            for insert in inserts:
                self.assertTrue([d for d in deletes if d < insert], table)

    def test_the_rev_names_no_row_a_declaration_cuts_or_a_moved_item_a_second_time(self):
        moved = {9444, 9445, 9485, 9486, 9487, 9488, 9489, 9490, 9491, 9508, 9509, 9510, 10299}
        for entry, rows in self.creature.items():
            for r in rows:
                self.assertNotIn(r["item"], moved, (entry, r))

    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for number, line in enumerate(self.text.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)
        self.assertTrue(self.text.endswith("\n"))
        self.assertNotIn("\n\n\n", self.text)
        self.assertNotIn(";;", self.text)


class HeroicLootidTest(unittest.TestCase):
    """The heroic bodies' own lootids: the dungeon file's `_boss(...)` overrides, the lock's predictions, the flag."""

    @classmethod
    def setUpClass(cls):
        cls.text = GN_DUNGEON.read_text(encoding="utf-8")
        found = re.search(r"^_HEROIC_ID = (\{.*?\n\})", cls.text, re.M | re.S)
        cls.heroic_id = ast.literal_eval(found[1].replace("\n", " ")) if found else {}

    def test_the_dungeon_file_flag_is_on(self):
        self.assertRegex(self.text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")

    def test_every_bosss_heroic_lootid_is_its_own_predicted_heroic_entry(self):
        for boss, (normal, heroic) in LOOTIDS.items():
            self.assertEqual(self.heroic_id.get(normal), heroic, boss)

    def test_the_dungeon_file_gives_the_six_carriers_their_own_lootid(self):
        found = re.search(r"^_HEROIC_LOOTID = \(([\d, ]+)\)", self.text, re.M)
        self.assertIsNotNone(found, "_HEROIC_LOOTID")
        self.assertEqual({int(x) for x in found[1].split(",")}, {n for n, _h in LOOTIDS.values()})

    def test_the_ambassadors_override_carries_the_lootid_column_through_own_loot(self):
        # `6228: dict(health=260_000, **({"columns": _own_loot(6228)} ...))`: the flag turns it on
        self.assertRegex(self.text, r'6228: dict\(health=260_000, \*\*\(\{"columns": _own_loot\(6228\)\}')
        self.assertRegex(self.text, r"def _own_loot\(entry: int\) -> dict:")
        self.assertIn('{"lootid": _HEROIC_ID[entry]} if _HEROIC_BOSS_OWN_LOOT and entry in _HEROIC_LOOTID', self.text)

    def test_pummelers_heroic_copy_gets_no_loot_column(self):
        self.assertRegex(self.text, r"6229: _boss\(6229, 373_333\)")

    def test_every_heroic_boss_with_its_own_lootid_is_declared(self):
        # lib/loot_tables.py `_check_creatures`: a heroic boss on its own lootid with no declaration drops nothing
        _, mine = _declarations()
        declared = {d.lootid for d in mine}
        for heroic in [h for _n, h in LOOTIDS.values()]:
            self.assertIn(heroic, declared, heroic)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/gnomeregan.py `_HEROIC_ID`, BOSS_LISTS in
        source/items/gnomeregan_loot.py, LOOTIDS in this test): the first write run mints the heroic entries in
        normal-entry order from 310543 (test_gnomeregan_heroic.py recomputes the table). If another branch appended
        lines to source/world/heroic_ids.lock first, the mint shifts and every heroic lootid points at another
        creature's heroic entry: this test fails loudly BEFORE the write run."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        fix = ("The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic "
               "entry of each unit from source/world/heroic_ids.lock and update ALL THREE places: `_HEROIC_ID` in "
               "source/world/dungeons/gnomeregan.py, BOSS_LISTS and THERMAPLUGG_HEROIC in "
               "source/items/gnomeregan_loot.py and LOOTIDS in this test.")
        pairs = {n: h for n, h in LOOTIDS.values()}
        ours = {normal: lock.pairs[normal] for normal in pairs if normal in lock.pairs}
        if ours:  # after the write run: the lock is the truth
            for normal, heroic in pairs.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"creature {normal}: lock says {ours[normal]}. {fix}")
        else:  # before it: nothing of ours is in the lock and the first mint is 310543
            taken = sorted(h for h in lock.pairs.values() if h >= 310543)
            self.assertEqual(taken, [], f"the lock already holds ids from 310543 ({taken[:3]}...) but none of the "
                                        f"Gnomeregan creatures. {fix}")


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (LOOT_FILE, Path(__file__)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")

    def test_us_spelling(self):
        # F-1e (R-1-LOOT n-3): gray / canceled, never the UK forms (the pattern is split so this file stays clean).
        bad = re.compile(r"\b(gr" + r"e(y|yed)|cance" + r"lled)\b", re.IGNORECASE)
        for path in (LOOT_FILE, Path(__file__), REV):
            self.assertIsNone(bad.search(path.read_text(encoding="utf-8")), path.name)

    def test_the_docstring_names_the_instance_as_the_one_who_sets_the_hard_mode_loot_bit(self):
        # F-1e (R-1-LOOT n-1): the arming at the pull never set it; ApplyHardModeLoot does, at the armed verdict.
        doc = LOOT_FILE.read_text(encoding="utf-8")
        self.assertIn("ApplyHardModeLoot", doc)
        self.assertNotIn("AddLootMode", doc)

    def test_the_heroic_techbot_needs_no_questitem_row_of_its_own(self):
        # F-1e (R-1-LOOT n-2): a heroic creature keeps its normal entry as its object entry; 301105's rows serve both.
        text = REV.read_text(encoding="utf-8")
        self.assertNotIn("310575, 0, 9277", text)
        self.assertIn("client queries 301105", text)

    def test_no_em_dashes_and_no_tabs(self):
        for path in (LOOT_FILE, Path(__file__), REV):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(chr(0x2014), text, path.name)
            self.assertNotIn("\t", text, path.name)


if __name__ == "__main__":
    unittest.main()
