"""
Ragefire Chasm build, WP L-1: the declarations in source/items/ragefire_chasm_loot.py (item keys from ragefire_chasm.py
and ragefire_chasm_hard_mode.py, the gear stage folded into this build).

Oggleflint, Jergosh the Invoker, Bazzalan and Taragaman the Hungerer: each list at the Normal tier on the stock lootid
and the Heroic tier on the heroic body's own lootid, the six stock items kept in place (`item(base=)`), the world drop
references that stay in group 1 of Oggleflint and Bazzalan (the list is group 2), Taragaman's Heart (a stock group 0
quest row that is never named) and the three Starving items at LootMode 2 on Taragaman's heroic lootid. The rows
themselves (and their rules and rendering) are test_loot_tables.py's; the real plan (tiers, the live stock groups) is
`generate.py --check`'s.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_loot.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.heroic_templates import LOCK_PATH, parse_lock  # noqa: E402

RFC_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "ragefire_chasm.py"
LOOT_FILE = TOOL_ROOT / "source" / "items" / "ragefire_chasm_loot.py"
PENDING = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"

# Oggleflint and Bazzalan keep six generic world drop references in group 1; their list is group 2.
LIST_GROUP = {"Oggleflint": 2, "Jergosh": 1, "Bazzalan": 2, "Taragaman": 1}
HARD_MODE_GROUP = 2
TARAGAMAN_HEROIC = 310499
HEART_OF_TARAGAMAN = 14540  # the stock group 0 quest row ("Slaying the Beast"): never named by a declaration

# ragefire-chasm-rework.md ## Loot "Final list" (ruling 13), copied (docs/ is not in every checkout): the doc's item
# names per boss. The hard mode list is the doc's "Hard mode: Taragaman the Hungerer, Starving".
DOC_LISTS = {
    "Oggleflint": ("Tunneler's Hide Cap", "Chieftain's Rockplate Pauldrons", "Borer-chased Treads", "Ring of the Cleft",
                   "Eye of the Earthborer", "Oggleflint's Skullthumper"),
    "Jergosh": ("Robe of Evocation", "Cavedweller Bracers", "Searing Blade Ritual Leggings",
                "Shard of the Blood Filled Orb", "Chanting Blade", "Invoker's Staff of Embers"),
    "Bazzalan": ("Satyrhide Mantle", "Cleft of Shadow Grips", "Felhoof Kilt", "Shadowstep Slippers", "Satyr's Kris",
                 "Idol of the Corrupted Grove"),
    "Taragaman": ("Crested Helm of the Beast", "Crystalline Cuffs", "Hungerer's Legplates", "Subterranean Cape",
                  "Searing Blade Talisman", "Cursed Felblade", "Libram of the Hungerer"),
}
HARD_MODE_NAMES = ("Taragaman's Fang", "Heart of the Starving", "Felstorm Greatblade")
# The stock entries of the doc's Alter rows (`item(base=)`).
STOCK_BASE = {
    "Robe of Evocation": 14150, "Cavedweller Bracers": 14147, "Chanting Blade": 14151,
    "Crystalline Cuffs": 14148, "Subterranean Cape": 14149, "Cursed Felblade": 14145,
}

# name -> (normal lootid, heroic lootid, the list (item() keys))
BOSSES = {
    "Oggleflint": (11517, 310496, {
        "rfc_tunnelers_hide_cap", "rfc_chieftains_rockplate_pauldrons", "rfc_borer_chased_treads",
        "rfc_ring_of_the_cleft", "rfc_eye_of_the_earthborer", "rfc_oggleflints_skullthumper"}),
    "Jergosh": (11518, 310497, {
        "rfc_robe_of_evocation", "rfc_cavedweller_bracers", "rfc_searing_blade_ritual_leggings",
        "rfc_shard_of_the_blood_filled_orb", "rfc_chanting_blade", "rfc_invokers_staff_of_embers"}),
    "Bazzalan": (11519, 310498, {
        "rfc_satyrhide_mantle", "rfc_cleft_of_shadow_grips", "rfc_felhoof_kilt", "rfc_shadowstep_slippers",
        "rfc_satyrs_kris", "rfc_idol_of_the_corrupted_grove"}),
    "Taragaman": (11520, TARAGAMAN_HEROIC, {
        "rfc_crested_helm_of_the_beast", "rfc_crystalline_cuffs", "rfc_hungerers_legplates",
        "rfc_subterranean_cape", "rfc_searing_blade_talisman", "rfc_cursed_felblade",
        "rfc_libram_of_the_hungerer"}),
}
HARD_MODE = {"rfc_taragamans_fang", "rfc_heart_of_the_starving", "rfc_felstorm_greatblade"}
NORMAL_LOOTIDS = {name: v[0] for name, v in BOSSES.items()}
HEROIC_LOOTIDS = {name: v[1] for name, v in BOSSES.items()}
ALL_LOOTIDS = {*NORMAL_LOOTIDS.values(), *HEROIC_LOOTIDS.values()}


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "ragefire_chasm_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


class LootDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, cls.decls = _declarations()
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("rfc_")}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and not d.removal}

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, keys) in BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP[name])]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes_are_the_docs_boss_list_rows(self):
        sizes = {name: len(v[2]) for name, v in BOSSES.items()}
        self.assertEqual(sizes, {"Oggleflint": 6, "Jergosh": 6, "Bazzalan": 6, "Taragaman": 7})
        self.assertEqual(sum(sizes.values()), 25)
        for name, (_n, _h, keys) in BOSSES.items():
            self.assertEqual(len(DOC_LISTS[name]), len(keys), name)

    def test_every_list_item_is_the_docs_item_by_name_or_stock_entry(self):
        stock = {v: k for k, v in STOCK_BASE.items()}
        for name, (_n, _h, keys) in BOSSES.items():
            names = []
            for key in keys:
                decl = self.items[key]
                if decl.base:
                    self.assertIn(decl.base, stock, f"{name}: {key} base {decl.base} is not a doc stock item")
                    names.append(stock[decl.base])
                else:
                    names.append(decl.name)
            self.assertEqual(sorted(names), sorted(DOC_LISTS[name]), name)

    def test_the_six_stock_items_keep_their_stock_entries_as_the_normal_tier(self):
        bases = {decl.base for key, decl in self.items.items() if decl.base}
        self.assertEqual(bases, set(STOCK_BASE.values()))
        # Jergosh's three and Taragaman's three, all on a list of the boss that held them
        for name, entries in (("Jergosh", (14150, 14147, 14151)), ("Taragaman", (14148, 14149, 14145))):
            on_list = {self.items[k].base for k in BOSSES[name][2] if self.items[k].base}
            self.assertEqual(on_list, set(entries), name)

    def test_the_world_drop_references_stay_in_group_one_and_the_list_is_group_two(self):
        # Oggleflint and Bazzalan hold six generic references in group 1 (24060, 24070, 24075-24078): the list is
        # group 2 so a generic pool rolls on top, never instead. Their group 1 is never declared.
        for name in ("Oggleflint", "Bazzalan"):
            for lootid in (BOSSES[name][0], BOSSES[name][1]):
                self.assertNotIn((lootid, 1), self.lists, name)
                self.assertIn((lootid, 2), self.lists, name)
        for name in ("Jergosh", "Taragaman"):
            for lootid in (BOSSES[name][0], BOSSES[name][1]):
                self.assertIn((lootid, 1), self.lists, name)

    def test_no_declaration_names_the_quest_item_cloth_or_a_reference_pool(self):
        # Taragaman's Heart, the linen cloth, the food and the consumables are stock group 0 rows that stay (and copy
        # to the heroic body); a reference pool is never named either
        for decl in self.decls:
            self.assertEqual((decl.replaces_items, decl.replaces_references, decl.row_removal, decl.pool_removal,
                              decl.removal, decl.chance, decl.reference), ((), (), False, False, False, None, None))

    # --- the hard mode list ----------------------------------------------------------------------------------------

    def test_the_hard_mode_list_is_group_two_of_taragamans_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(TARAGAMAN_HEROIC, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, HARD_MODE, False))
        self.assertEqual(len(decl.items), 3)
        # the heroic list stays: a lit kill adds one of the three on top of it
        self.assertIn((TARAGAMAN_HEROIC, LIST_GROUP["Taragaman"]), self.lists)
        # the doc's three names
        names = sorted(self.items[k].name for k in HARD_MODE)
        self.assertEqual(names, sorted(HARD_MODE_NAMES))
        # the normal lootid gets none (heroic only: the shrine is spawned on heroic alone)
        self.assertNotIn((11520, HARD_MODE_GROUP), self.lists)

    def test_only_that_one_group_rolls_at_loot_mode_2(self):
        modes = sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1)
        self.assertEqual(modes, [(TARAGAMAN_HEROIC, 2)])
        self.assertEqual(self.lists[modes[0]].loot_mode, 2)

    def test_the_hard_mode_items_are_on_the_hard_mode_ladder(self):
        for key in HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    def test_the_hard_mode_loot_bit_is_the_one_the_instance_sets(self):
        kit = TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "Kit" / "DungeonKit.cpp"
        if kit.is_file():
            self.assertIn("AddLootMode(LOOT_MODE_HARD_MODE_1)", kit.read_text(encoding="utf-8"))
        self.assertEqual(L.LOOT_MODE_HARD_MODE_1, 2)

    # --- groups and counts -----------------------------------------------------------------------------------------

    def test_no_flex_groups_no_tokens_no_chance_rows_and_no_pools(self):
        groups = {group for _lootid, group in self.lists}
        self.assertEqual(groups, {1, 2})
        self.assertFalse([d for d in self.decls if d.loot_mode & 0x8 or d.chance is not None])
        self.assertEqual([d for d in self.decls if d.reference is not None], [])
        self.assertTrue(all(d.picks == 1 for d in self.decls))

    def test_declaration_counts(self):
        # 4 bosses x 2 lootids (list) + the hard mode group; nothing else
        self.assertEqual(len(self.lists), 4 * 2 + 1)
        self.assertEqual(len(self.decls), len(self.lists))
        self.assertEqual({d.lootid for d in self.decls}, ALL_LOOTIDS)

    # --- one item, one row -----------------------------------------------------------------------------------------

    def test_no_loot_table_lists_an_item_twice(self):
        # creature_loot_template is keyed (Entry, Item, Reference, GroupId) and the engine's group roll skips an
        # equippable the loot already holds: a duplicate item in one lootid fails db-import partway (BRD LESSONS)
        by_lootid: dict[int, list[str]] = {}
        for (lootid, _group), decl in self.lists.items():
            by_lootid.setdefault(lootid, []).extend(decl.items)
        for lootid, keys in by_lootid.items():
            with self.subTest(lootid=lootid):
                self.assertEqual(len(keys), len(set(keys)), keys)
                bases = [self.items[k].base for k in keys if k in self.items and self.items[k].base]
                self.assertEqual(len(bases), len(set(bases)), bases)
                self.assertNotIn(HEART_OF_TARAGAMAN, bases)

    def test_no_item_drops_from_two_bosses_of_the_dungeon(self):
        seen: dict[str, str] = {}
        for name, (_n, _h, keys) in BOSSES.items():
            for key in keys:
                self.assertNotIn(key, seen, f"{key} on {name} and {seen.get(key)}")
                seen[key] = name
        self.assertFalse(set(seen) & HARD_MODE)

    def test_no_chest_lists_an_item_twice(self):
        # Ragefire Chasm has no chest loot (the stock rows are creature loot and the boss kit's shrine and pour GOs
        # give none): no pending rev of the dungeon may hold a `gameobject_loot_template` / `item_loot_template` /
        # `reference_loot_template` insert whose (Entry, Item) pair repeats (the tables are keyed (Entry, Item): a
        # duplicate fails db-import partway, BRD LESSONS). Vacuous today; it holds the line for a later chest. The glob
        # cannot see a generated `rev_<digits>.sql`, where a declared pool would land: no declaration names one.
        self.assertEqual([d.where for d in self.decls if d.reference is not None or d.pool_removal], [])
        row = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*,")
        for path in sorted(PENDING.glob("*ragefire*.sql")):
            text = path.read_text(encoding="utf-8")
            for table in ("gameobject_loot_template", "item_loot_template", "reference_loot_template"):
                seen: set[tuple[str, str]] = set()
                for statement in re.findall(rf"INSERT INTO `{table}`[^;]*;", text, re.S):
                    values = statement.split("VALUES", 1)[-1]
                    for entry, item in row.findall(values):
                        self.assertNotIn((entry, item), seen, f"{path.name}: {table} ({entry}, {item}) twice")
                        seen.add((entry, item))

    # --- the items the lists name ----------------------------------------------------------------------------------

    def test_list_items_are_on_the_dungeon_ladder_and_every_declared_tier_exists(self):
        for decl in self.decls:
            for key in decl.items:
                ladder = self.items[key].ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                if decl.tier in ("normal", "heroic"):
                    self.assertEqual(ladder.name, "vanilla_dungeon", key)

    def test_every_gear_stage_item_is_dropped_by_someone(self):
        listed = set().union(*(v[2] for v in BOSSES.values()))
        self.assertEqual(len(listed), 25)
        self.assertEqual(listed | HARD_MODE, set(self.items), "an rfc_ item() that no boss drops, or a list key "
                                                              "without an item()")


class HeroicLootidTest(unittest.TestCase):
    """The heroic bodies' own lootids: the dungeon file's `_boss(...)` overrides, the lock's predictions, the flag."""

    def test_the_dungeon_file_flag_is_on_and_gives_every_boss_its_own_heroic_lootid(self):
        text = RFC_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")
        found = re.search(r"^_HEROIC_LOOTID = (\{[^}]*\})", text, re.M)
        self.assertIsNotNone(found)
        self.assertEqual(eval(found[1]), {v[0]: v[1] for v in BOSSES.values()})  # noqa: S307 - literal dict

    def test_every_heroic_boss_with_its_own_lootid_is_declared(self):
        # lib/loot_tables.py `_check_creatures`: a heroic boss on its own lootid with no declaration drops nothing
        _, mine = _declarations()
        declared = {d.lootid for d in mine}
        for name, (_n, heroic, _keys) in BOSSES.items():
            self.assertIn(heroic, declared, name)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/ragefire_chasm.py `_HEROIC_LOOTID`, BOSS_LISTS in
        source/items/ragefire_chasm_loot.py, BOSSES above): the first write run mints the heroic entries from 310488
        (8996) in normal-entry order, the four bosses at 310496-310499 (test_ragefire_chasm_heroic.py pins the order).
        If another branch appended lines to source/world/heroic_ids.lock first, the mint shifts and every heroic
        lootid points at another creature's heroic entry: this test fails loudly BEFORE the write run."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        fix = (
            "The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic entry "
            "of each boss from source/world/heroic_ids.lock (or, before the write run, 310488 + the creature's index "
            "in normal-entry order after the lock's last line) and update ALL FOUR places: `_HEROIC_LOOTID` in "
            "source/world/dungeons/ragefire_chasm.py, BOSS_LISTS and TARAGAMAN_HEROIC in "
            "source/items/ragefire_chasm_loot.py, BOSSES in this test and HEROIC_LOOTID in "
            "test_ragefire_chasm_heroic.py; then rerun both files."
        )
        pairs = {v[0]: v[1] for v in BOSSES.values()}
        ours = {normal: lock.pairs[normal] for normal in pairs if normal in lock.pairs}
        if ours:  # after the write run: the lock is the truth
            for normal, heroic in pairs.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"creature {normal}: lock says {ours[normal]}. {fix}")
        else:  # before it: nothing of ours is in the lock and the next free id is the first predicted one
            taken = sorted(h for h in lock.pairs.values() if h >= 310488)
            self.assertEqual(taken, [], f"the lock already holds ids from 310488 ({taken[:3]}...) but none of the "
                                        f"Ragefire Chasm bosses. {fix}")
            foreign_top = max((h for h in lock.pairs.values() if h < 310488), default=0)
            self.assertEqual(foreign_top, 310487, f"the lock's last id below the first predicted one is "
                                                  f"{foreign_top}, not 310487: lines were added or removed. {fix}")


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (LOOT_FILE, Path(__file__)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")


if __name__ == "__main__":
    unittest.main()
