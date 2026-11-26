"""
Zul'Farrak build, WP L-1: the declarations in source/items/zul_farrak_loot.py (item keys from zul_farrak.py and
zul_farrak_hard_mode.py, the gear stage merged as #161) and the chest rev data/sql/updates/pending_db_world/
rev_loot_zul_farrak.sql.

Theka (group 2: his group 1 is nine world reference pools), Antu'sul, Zum'rah, Sezz'ziz (the Pyramid's list), Ukorz and
Gahz'rilla: each list at the Normal tier on the stock lootid and the Heroic tier on the heroic body's own lootid, the
stock items kept in place (`item(base=)`), Antu'sul's and Ukorz's emptied group 2, the cut group 0 rows of the moved
items, the shared rare list 1209000 emptied (its 13 users, then the pool), the rares' one pool of four at 35% and
Gahz'rilla's three hard mode items at LootMode 2. Bly's crew drops from the stash chest (gameobject 301360 normal /
301361 heroic, hand SQL): the crew list, the Divino-matic Rod and the members' own small tables, with the BRD
duplicate-item rule (`test_no_chest_lists_an_item_twice`). The rows themselves (and their rules and rendering) are
test_loot_tables.py's; the real plan (tiers, the live stock groups) is `generate.py --check`'s.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_loot.py
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

from lib import test_zul_farrak_items as gear  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.heroic_templates import LOCK_PATH, parse_lock  # noqa: E402

ZF_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "zul_farrak.py"
LOOT_FILE = TOOL_ROOT / "source" / "items" / "zul_farrak_loot.py"
ITEM_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
CHEST_REV = PENDING / "rev_loot_zul_farrak.sql"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak" / "ZulFarrakRework.h"

THEKA, ANTUSUL, ZUMRAH, PYRAMID, BLY, UKORZ, GAHZRILLA, RARES = (
    gear.THEKA, gear.ANTUSUL, gear.ZUMRAH, gear.PYRAMID, gear.BLY, gear.UKORZ, gear.GAHZRILLA, gear.RARES)

# Theka's group 1 is nine world reference pools (24025 to 24046): his list is group 2. Every other list is group 1.
LIST_GROUP = {THEKA: 2, ANTUSUL: 1, ZUMRAH: 1, PYRAMID: 1, UKORZ: 1, GAHZRILLA: 1}
RARE_GROUP = 1
HARD_MODE_GROUP = 2

# boss -> (stock lootid, heroic lootid). Sezz'ziz carries the Pyramid's list. Bly's crew (7604-7608) and Velratha
# (7795) have no list on a creature lootid.
LOOTIDS = {
    THEKA: (7272, 310512), ANTUSUL: (8127, 310532), ZUMRAH: (7271, 310511), PYRAMID: (7275, 310515),
    UKORZ: (7267, 310508), GAHZRILLA: (7273, 310513),
}
GAHZRILLA_HEROIC = LOOTIDS[GAHZRILLA][1]
RARE_LOOTIDS = ((10080, 310536), (10081, 310537), (10082, 310538))  # Sandarr, Dustwraith, Zerillis
CREW_LOOTIDS = (7604, 7605, 7606, 7607, 7608)  # Bly, Raven, Oro, Weegli, Murta: their bodies carry nothing
HARD_MODE = {"zf_scale_of_the_storm_god", "zf_stormcharged_fang", "zf_sergeants_whistle"}
CHESTS = {"normal": 301360, "heroic": 301361}

SHARED_RARE_LIST = 1209000
SHARED_RARE_LIST_USERS = {5648, 5649, 5650, 7246, 7247, 7268, 7274, 7286, 8095, 8120, 10080, 10081, 10082}
# The ten items of reference 1209000 (live SELECT 2026-11-25) and the lists they went to.
SHARED_RARE_LIST_ITEMS = {
    2040: BLY, 5616: THEKA, 6440: ZUMRAH, 9480: BLY, 9481: PYRAMID, 9482: RARES, 9483: BLY, 9484: RARES,
    9511: THEKA, 9512: THEKA,
}
# Gutwrencher, Witch Doctor's Cane, Bloodletter Scalpel and Blackmetal Cape: group 0 rows of the crew that are on
# other lists now, so the chest does not hold them.
CREW_ROWS_ON_LISTS = {5616, 9482, 9511, 9512}
# The quest rows, cloth and keys that stay as stock rows no declaration may name.
KEPT_ROWS = {
    9523,  # Troll Temper (quest-required)
    10660, 10661,  # the First and Second Mosh'aru Tablets
    9234,  # Tiara of the Deep
    9471,  # Nekrum's Medallion
    8444,  # Executioner's Key
    8707,  # Gahz'rilla's Electrified Scale
    9238,  # Uncracked Scarab Shell
    4306, 4338,  # silk and mageweave
}
ROD = 8548  # Bly's Divino-matic Rod (quest 2768), in both chests at 100%, QuestRequired
STASH_REFERENCES = {24036, 24039, 24040, 24041, 24042, 24043, 24044, 24045, 24080, 24081}  # the members' world pools


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
                if Path(registry.declared_in(e) or "").name == "zul_farrak_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


def _boss_keys(boss: str) -> set[str]:
    return {key for key, (owner, _stock, _stats) in gear.LIST.items() if owner == boss}


class LootDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, cls.decls = _declarations()
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("zf_")}
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
                    decl = self.lists[(lootid, LIST_GROUP[boss])]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes_are_the_docs_boss_list_rows(self):
        sizes = {boss: len(self.lists[(normal, LIST_GROUP[boss])].items) for boss, (normal, _h) in LOOTIDS.items()}
        self.assertEqual(sizes, {THEKA: 8, ANTUSUL: 7, ZUMRAH: 7, PYRAMID: 8, UKORZ: 9, GAHZRILLA: 9})
        self.assertEqual(sum(sizes.values()), 48)
        for boss, size in sizes.items():
            self.assertEqual(gear.BOSS_COUNT[boss], size, boss)

    def test_theka_keeps_his_world_references_in_group_one_and_the_list_is_group_two(self):
        # Theka holds nine generic world reference pools in group 1 (24025 to 24046): the list is group 2 so a generic
        # pool rolls on top, never instead. His group 1 is never declared.
        for lootid in LOOTIDS[THEKA]:
            self.assertNotIn((lootid, 1), self.lists)
            self.assertIn((lootid, 2), self.lists)
        for boss in (ANTUSUL, ZUMRAH, PYRAMID, UKORZ, GAHZRILLA):
            for lootid in LOOTIDS[boss]:
                self.assertIn((lootid, 1), self.lists, boss)
        for boss in (ANTUSUL, ZUMRAH, PYRAMID, UKORZ):  # no group 2 list (Antu'sul's and Ukorz's stock group is cut)
            for lootid in LOOTIDS[boss]:
                self.assertNotIn((lootid, 2), self.lists, boss)

    def test_stock_items_keep_their_stock_entries_as_the_normal_tier(self):
        bases = {decl.base for decl in self.items.values() if decl.base}
        self.assertEqual(bases, gear.STOCK_ENTRIES)
        for boss, (normal, _heroic) in LOOTIDS.items():
            on_list = {self.items[k].base for k in self.lists[(normal, LIST_GROUP[boss])].items
                       if self.items[k].base}
            self.assertEqual(on_list, {s for _k, (b, s, _st) in gear.LIST.items() if b == boss and s is not None},
                             boss)

    def test_sulthraze_the_lasher_is_no_ones_drop(self):
        # the join of Jang'thraze and Sang'thraze (Call of Sul'thraze); gear REVIEW n6: off Ukorz's list too
        for decl in self.decls:
            self.assertNotIn("zf_sulthraze_the_lasher", decl.items)
        self.assertNotIn(9372, {item for d in self.row_removals.values() for item in d.rows})
        self.assertNotIn(9372, {d.item_entry for d in self.chances})

    def test_no_declaration_names_a_quest_row_cloth_or_a_crew_lootid(self):
        for decl in self.decls:
            self.assertNotIn(decl.lootid, CREW_LOOTIDS, decl.where)
            self.assertFalse(set(decl.rows) & KEPT_ROWS, decl.where)
            self.assertFalse({d for d in decl.replaces_items} & KEPT_ROWS, decl.where)
        self.assertNotIn(7795, {d.lootid for d in self.decls if d.listing and not d.row_removal})

    # --- the cut stock rows and the shared rare list ---------------------------------------------------------------

    def test_antusuls_and_ukorzs_group_two_are_removed(self):
        self.assertEqual(sorted(self.group_removals), [(7267, 2), (8127, 2)])
        for key in ((8127, 2), (7267, 2)):
            self.assertTrue(self.group_removals[key].why)

    def test_group_zero_rows_of_the_moved_items_are_cut_from_the_bosses_that_had_them(self):
        cuts = {lootid: set(d.rows) for (lootid, group), d in self.row_removals.items() if group == 0 and d.rows}
        self.assertEqual(cuts[7272], {2040, 5616, 9480, 9482, 9483, 9511, 9512})  # Theka
        self.assertEqual(cuts[7796], {9480, 9482, 9511})  # Nekrum
        self.assertEqual(cuts[7795], {5616, 9481, 9483, 9512})  # Velratha
        self.assertEqual(cuts[7797], {5616, 6440, 9511, 9512})  # Ruuzlu
        self.assertEqual(cuts[10081], {12471})  # Dustwraith's own Desertwalker Cane
        self.assertEqual(cuts[10082], {12470})  # Zerillis's own Sandstalker Ankleguards
        self.assertEqual(sorted(cuts), [7272, 7795, 7796, 7797, 10081, 10082])
        # every cut item is on a list now
        listed = {self.items[k].base for k in self.items if self.items[k].base}
        for lootid, rows in cuts.items():
            self.assertTrue(rows <= listed, (lootid, rows - listed))

    def test_the_shared_rare_list_is_emptied_and_removed(self):
        users = {lootid for (lootid, group), d in self.row_removals.items()
                 if group == 0 and SHARED_RARE_LIST in d.ref_rows}
        self.assertEqual(users, SHARED_RARE_LIST_USERS)
        self.assertEqual(len(users), 13)
        self.assertEqual([d.reference for d in self.pool_removals], [SHARED_RARE_LIST])
        self.assertTrue(self.pool_removals[0].why)

    def test_every_item_of_the_shared_rare_list_has_a_boss_a_chest_or_the_rares(self):
        by_base = {decl.base: key for key, decl in self.items.items() if decl.base}
        self.assertEqual(set(SHARED_RARE_LIST_ITEMS), set(by_base) & set(SHARED_RARE_LIST_ITEMS))
        for item, boss in SHARED_RARE_LIST_ITEMS.items():
            self.assertEqual(gear.LIST[by_base[item]][0], boss, (item, by_base[item]))

    # --- the rares -------------------------------------------------------------------------------------------------

    def test_the_rares_share_one_pool_of_four_at_35_percent_each(self):
        pool = {key: (gear.LIST[key][1], self.lock[(key, "heroic")]) for key in _boss_keys(RARES)}
        self.assertEqual(len(pool), 4)
        for normal, heroic in RARE_LOOTIDS:
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(lootid=lootid):
                    rows = sorted((d.item_entry, d.chance, d.group, d.loot_mode, d.reference)
                                  for d in self.chances if d.lootid == lootid)
                    want = sorted((stock if tier == "normal" else heroic_entry, 8.75, RARE_GROUP,
                                   L.LOOT_MODE_DEFAULT, None) for stock, heroic_entry in pool.values())
                    self.assertEqual(rows, want)
                    self.assertAlmostEqual(sum(r[1] for r in rows), 35.0)
        self.assertEqual({d.lootid for d in self.chances}, {x for pair in RARE_LOOTIDS for x in pair})

    def test_the_rares_pool_is_the_docs_four_items_on_the_dungeon_ladder(self):
        keys = _boss_keys(RARES)
        self.assertEqual(keys, {"zf_desertwalker_cane", "zf_sandstalker_ankleguards", "zf_witch_doctors_cane",
                                "zf_spellshock_leggings"})
        for key in keys:
            self.assertEqual(self.items[key].ladder.name, "vanilla_dungeon", key)
            self.assertEqual(self.lock[(key, "normal")], gear.LIST[key][1], key)  # a stock row: the base tier

    # --- the hard mode list ----------------------------------------------------------------------------------------

    def test_the_hard_mode_list_is_group_two_of_gahzrillas_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(GAHZRILLA_HEROIC, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, HARD_MODE, False))
        self.assertEqual(len(decl.items), 3)
        names = sorted(self.items[k].name for k in HARD_MODE)
        self.assertEqual(names, ["Scale of the Storm God", "Sergeant's Whistle", "Stormcharged Fang"])
        # the heroic list stays: a lit kill adds one of the three on top of it
        self.assertIn((GAHZRILLA_HEROIC, LIST_GROUP[GAHZRILLA]), self.lists)
        # the normal lootid gets none (heroic only: the Test is offered on heroic)
        self.assertNotIn((LOOTIDS[GAHZRILLA][0], HARD_MODE_GROUP), self.lists)

    def test_only_that_one_group_rolls_at_loot_mode_2(self):
        modes = sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1)
        self.assertEqual(modes, [(GAHZRILLA_HEROIC, 2)])
        self.assertFalse([d for d in self.chances if d.loot_mode != L.LOOT_MODE_DEFAULT])

    def test_the_hard_mode_items_are_on_the_hard_mode_ladder(self):
        for key in HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    def test_the_hard_mode_loot_bit_is_the_one_the_instance_sets(self):
        kit = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Kit" / "DungeonKit.cpp"
        if kit.is_file():
            self.assertIn("AddLootMode(LOOT_MODE_HARD_MODE_1)", kit.read_text(encoding="utf-8"))
        self.assertEqual(L.LOOT_MODE_HARD_MODE_1, 2)

    # --- groups and counts -----------------------------------------------------------------------------------------

    def test_no_flex_groups_no_tokens_and_no_picks(self):
        self.assertTrue(all(d.picks == 1 and d.reference is None for d in self.decls if d.listing))
        self.assertFalse([d for d in self.decls if d.loot_mode & 0x8])
        self.assertEqual({group for _lootid, group in self.lists}, {1, 2})

    def test_declaration_counts(self):
        # 6 bosses x 2 lootids (list) + the hard mode group; 2 emptied groups; 4 + 13 group 0 cuts; 1 pool; 3 rares x 2
        # lootids x 4 pool rows
        self.assertEqual(len(self.lists), 6 * 2 + 1)
        self.assertEqual(len(self.group_removals), 2)
        self.assertEqual(len(self.row_removals), 4 + 13)  # Theka, Nekrum, Velratha, Ruuzlu + the 13 pool users
        self.assertEqual(len(self.pool_removals), 1)
        self.assertEqual(len(self.chances), 3 * 2 * 4)
        self.assertEqual(len(self.decls), 13 + 2 + 17 + 1 + 24)

    # --- one item, one row -----------------------------------------------------------------------------------------

    def test_no_loot_table_lists_an_item_twice(self):
        # creature_loot_template is keyed (Entry, Item, Reference, GroupId) and the engine's group roll skips an
        # equippable the loot already holds: a duplicate item in one lootid fails db-import partway (BRD LESSONS)
        by_lootid: dict[int, list] = {}
        for (lootid, _group), decl in self.lists.items():
            by_lootid.setdefault(lootid, []).extend(decl.items)
        for decl in self.chances:
            by_lootid.setdefault(decl.lootid, []).append(decl.item_entry)
        for lootid, keys in by_lootid.items():
            with self.subTest(lootid=lootid):
                self.assertEqual(len(keys), len(set(keys)), keys)
                bases = [self.items[k].base for k in keys if k in self.items and self.items[k].base]
                self.assertEqual(len(bases), len(set(bases)), bases)

    def test_no_item_drops_from_two_places(self):
        seen: dict[str, str] = {}
        for boss, (normal, _h) in LOOTIDS.items():
            for key in self.lists[(normal, LIST_GROUP[boss])].items:
                self.assertNotIn(key, seen, f"{key} on {boss} and {seen.get(key)}")
                seen[key] = boss
        rare_keys = {key for key, (b, _s, _st) in gear.LIST.items() if b == RARES}
        for key in rare_keys:
            self.assertNotIn(key, seen, key)
            seen[key] = RARES
        for key in _boss_keys(BLY):  # the chest
            self.assertNotIn(key, seen, key)
            seen[key] = BLY
        self.assertFalse(set(seen) & HARD_MODE)

    def test_every_gear_stage_item_is_dropped_by_someone_but_the_join(self):
        listed = set().union(*(self.lists[(n, LIST_GROUP[b])].items for b, (n, _h) in LOOTIDS.items()))
        listed |= _boss_keys(RARES) | _boss_keys(BLY)
        self.assertEqual(len(listed), 61)
        self.assertEqual(listed | HARD_MODE | {"zf_sulthraze_the_lasher"}, set(self.items),
                         "a zf_ item() that no boss drops, or a list key without an item()")

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


class ChestRevTest(unittest.TestCase):
    """rev_loot_zul_farrak.sql: the crew's stash chest (GO 301360 normal / 301361 heroic) and the empty crew bodies."""

    @classmethod
    def setUpClass(cls):
        cls.text = CHEST_REV.read_text(encoding="utf-8")
        cls.lock = _lock_entries()
        ints = r"(\d+), "  # a value row: entry, item, reference, chance, quest, mode, group, min, max, comment
        pattern = re.compile(rf"^\({ints * 3}([\d.]+), {ints * 5}'(.*)'\)[,;]$", re.M)
        cls.rows: dict[int, list[dict]] = {}
        for m in pattern.finditer(cls.text):
            entry, item, ref = int(m[1]), int(m[2]), int(m[3])
            quest, mode, group, mn, mx = (int(m[i]) for i in range(5, 10))
            cls.rows.setdefault(entry, []).append(dict(item=item, ref=ref, chance=float(m[4]), quest=quest,
                                                       mode=mode, group=group, min=mn, max=mx, comment=m[10]))

    def test_the_two_chests_are_the_headers_ids(self):
        self.assertEqual(sorted(self.rows), sorted(CHESTS.values()))
        if HEADER.is_file():
            header = HEADER.read_text(encoding="utf-8")
            self.assertRegex(header, r"GO_ZF_CREW_STASH\s*=\s*301360")
            self.assertRegex(header, r"GO_ZF_CREW_STASH_HEROIC\s*=\s*301361")

    def test_each_chest_list_is_the_crews_list_at_its_tier(self):
        keys = _boss_keys(BLY)
        self.assertEqual(len(keys), 9)
        for tier, chest in CHESTS.items():
            with self.subTest(chest=chest):
                listed = [r["item"] for r in self.rows[chest] if r["group"] == 1]
                self.assertEqual(sorted(listed), sorted(self.lock[(key, tier)] for key in keys))
                self.assertEqual(len(listed), 9)

    def test_the_list_is_one_equal_chance_group_and_the_stock_entries_are_the_normal_tier(self):
        for chest, rows in self.rows.items():
            for r in rows:
                if r["group"] == 1:
                    self.assertEqual((r["ref"], r["chance"], r["quest"], r["mode"], r["min"], r["max"]),
                                     (0, 0, 0, 1, 1, 1), (chest, r))
        normal = {r["item"] for r in self.rows[CHESTS["normal"]] if r["group"] == 1}
        self.assertTrue({2040, 9480, 9483} <= normal)  # Troll Protector, Eyegouger, Flaming Incinerator
        heroic = {r["item"] for r in self.rows[CHESTS["heroic"]] if r["group"] == 1}
        self.assertFalse(normal & heroic)

    def test_the_rod_is_in_both_chests_as_a_quest_required_sure_drop(self):
        for chest, rows in self.rows.items():
            rod = [r for r in rows if r["item"] == ROD]
            self.assertEqual(len(rod), 1, chest)
            self.assertEqual((rod[0]["chance"], rod[0]["quest"], rod[0]["group"], rod[0]["ref"]), (100.0, 1, 0, 0))

    def test_the_two_chests_hold_the_same_small_tables(self):
        def small(chest):
            return sorted((r["item"], r["chance"], r["quest"], r["group"], r["min"], r["max"])
                          for r in self.rows[chest] if r["group"] != 1)
        self.assertEqual(small(CHESTS["normal"]), small(CHESTS["heroic"]))

    def test_the_members_world_pools_are_group_two_and_the_only_group_two(self):
        for chest, rows in self.rows.items():
            pools = [r for r in rows if r["group"] == 2]
            self.assertEqual({r["item"] for r in pools}, STASH_REFERENCES, chest)
            for r in pools:
                self.assertEqual((r["item"], r["min"], r["max"], r["quest"]), (r["ref"], 1, 1, 0), (chest, r))
            self.assertLessEqual(sum(r["chance"] for r in pools), 100, chest)
            # an explicit-chance group never mixes with a zero-chance one (the engine would roll the chances first)
            self.assertTrue(all(r["chance"] > 0 for r in pools))

    def test_no_chest_lists_an_item_twice(self):
        # gameobject_loot_template is keyed (Entry, Item): a duplicate fails db-import partway (BRD LESSONS section 5).
        # The glob cannot see a generated `rev_<digits>.sql`: no declaration names a reference pool of this dungeon.
        for entry, rows in self.rows.items():
            items = [row["item"] for row in rows]
            self.assertEqual(len(items), len(set(items)), entry)
        row = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*,")
        for path in sorted(PENDING.glob("*zul_farrak*.sql")):
            text = path.read_text(encoding="utf-8")
            for table in ("gameobject_loot_template", "item_loot_template", "reference_loot_template"):
                seen: set[tuple[str, str]] = set()
                for statement in re.findall(rf"INSERT INTO `{table}`[^;]*;", text, re.S):
                    values = statement.split("VALUES", 1)[-1]
                    for entry, item in row.findall(values):
                        self.assertNotIn((entry, item), seen, f"{path.name}: {table} ({entry}, {item}) twice")
                        seen.add((entry, item))

    def test_the_chest_holds_no_item_of_a_creature_list_and_no_item_a_list_took(self):
        chest_items = {r["item"] for rows in self.rows.values() for r in rows}
        self.assertFalse(chest_items & CREW_ROWS_ON_LISTS)
        self.assertFalse(chest_items & KEPT_ROWS - {4306, 4338})  # the quest rows of other bosses (cloth is fine)
        _, decls = _declarations()
        for decl in decls:
            if decl.listing and not decl.removal and decl.chance is None and decl.lootid not in CHESTS.values():
                for key in decl.items:
                    for tier in ("normal", "heroic", "heroic_hm"):
                        if (key, tier) in self.lock:
                            self.assertNotIn(self.lock[(key, tier)], chest_items, key)

    def test_the_chest_rows_are_deleted_first_and_the_five_crew_bodies_are_emptied(self):
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301360, 301361);", self.text)
        self.assertLess(self.text.index("DELETE FROM `gameobject_loot_template`"), self.text.index("INSERT INTO"))
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` IN (7604, 7605, 7606, 7607, 7608);",
                      self.text)
        for lootid in CREW_LOOTIDS:
            self.assertIn(str(lootid), self.text)

    def test_every_row_has_the_loot_mode_a_chest_can_use(self):
        for entry, rows in self.rows.items():
            for row in rows:
                self.assertEqual(row["mode"], 1, (entry, row))

    def test_the_chest_templates_sort_before_the_loot_when_d5_makes_them(self):
        # WP-D5's rev holds the gameobject_template rows (Data1 = the loot entry); it needs no order against this rev
        for path in sorted(PENDING.glob("rev_*zul_farrak*.sql")):
            text = path.read_text(encoding="utf-8")
            if "`gameobject_template`" in text and "301360" in text:
                self.assertRegex(text, r"\(301360, 3, \d+, '[^']+', '', '', '', [\d.]+, \d+, 301360,")
                self.assertRegex(text, r"\(301361, 3, \d+, '[^']+', '', '', '', [\d.]+, \d+, 301361,")

    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for number, line in enumerate(self.text.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)
        self.assertTrue(self.text.endswith("\n"))


class HeroicLootidTest(unittest.TestCase):
    """The heroic bodies' own lootids: the dungeon file's `_boss(...)` overrides, the lock's predictions, the flag."""

    @classmethod
    def setUpClass(cls):
        cls.text = ZF_DUNGEON.read_text(encoding="utf-8")
        found = re.search(r"^_HEROIC_ID = (\{.*?\n\})", cls.text, re.M | re.S)
        cls.heroic_id = ast.literal_eval(found[1].replace("\n", " ")) if found else {}

    def test_the_dungeon_file_flag_is_on(self):
        self.assertRegex(self.text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")

    def test_every_bosss_heroic_lootid_is_its_own_predicted_heroic_entry(self):
        for boss, (normal, heroic) in LOOTIDS.items():
            self.assertEqual(self.heroic_id.get(normal), heroic, boss)
        for normal, heroic in RARE_LOOTIDS:
            self.assertEqual(self.heroic_id.get(normal), heroic, normal)

    def test_the_dungeon_file_gives_the_six_bosses_their_own_lootid(self):
        found = re.search(r"^_HEROIC_LOOTID = \{[^}]*for entry in \(([\d, ]+)\)\}", self.text, re.M)
        self.assertIsNotNone(found, "_HEROIC_LOOTID")
        self.assertEqual({int(x) for x in found[1].split(",")}, {n for n, _h in LOOTIDS.values()})

    def test_the_three_rares_get_their_own_heroic_lootid(self):
        # a rare is a trash body: `_boss()` is not used for it, so its override sets the column itself
        self.assertRegex(self.text, r'dict\(columns=\{"lootid": _HEROIC_ID\[entry\]\}\) for entry in '
                                    r'\(10080, 10081, 10082\)')

    def test_every_heroic_boss_with_its_own_lootid_is_declared(self):
        # lib/loot_tables.py `_check_creatures`: a heroic boss on its own lootid with no declaration drops nothing
        _, mine = _declarations()
        declared = {d.lootid for d in mine}
        for heroic in [h for _n, h in LOOTIDS.values()] + [h for _n, h in RARE_LOOTIDS]:
            self.assertIn(heroic, declared, heroic)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/zul_farrak.py `_HEROIC_ID`, BOSS_LISTS and RARES in
        source/items/zul_farrak_loot.py, LOOTIDS and RARE_LOOTIDS above): the first write run mints the heroic entries
        in normal-entry order from 310501 (test_zul_farrak_heroic.py recomputes the table). If another branch appended
        lines to source/world/heroic_ids.lock first, the mint shifts and every heroic lootid points at another
        creature's heroic entry: this test fails loudly BEFORE the write run."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        fix = ("The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic "
               "entry of each unit from source/world/heroic_ids.lock and update ALL FOUR places: `_HEROIC_ID` in "
               "source/world/dungeons/zul_farrak.py, BOSS_LISTS and RARES in source/items/zul_farrak_loot.py, LOOTIDS "
               "and RARE_LOOTIDS in this test and the heroic tier ids of RARE_POOL if the items moved.")
        pairs = {n: h for n, h in LOOTIDS.values()} | dict(RARE_LOOTIDS)
        ours = {normal: lock.pairs[normal] for normal in pairs if normal in lock.pairs}
        if ours:  # after the write run: the lock is the truth
            for normal, heroic in pairs.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"creature {normal}: lock says {ours[normal]}. {fix}")
        else:  # before it: nothing of ours is in the lock and the first mint is 310501
            taken = sorted(h for h in lock.pairs.values() if h >= 310501)
            self.assertEqual(taken, [], f"the lock already holds ids from 310501 ({taken[:3]}...) but none of the "
                                        f"Zul'Farrak creatures. {fix}")


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (LOOT_FILE, Path(__file__)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")


if __name__ == "__main__":
    unittest.main()
