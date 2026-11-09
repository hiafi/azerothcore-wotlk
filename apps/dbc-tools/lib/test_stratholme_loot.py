"""
Stratholme build WP-L-1: the real declarations in source/items/stratholme_loot.py (item keys from stratholme.py, tokens
from haunted_set.py): the Service Entrance bosses' lists (Barthilas, Baroness Anastari, Nerub'enkan, Maleki, Ramstein,
Baron Rivendare), the Haunted Bracers and Leggings, the Baron's hard mode group and Deathcharger's Reins (1% normal, 2%
heroic, 10% hard mode through `loot_chance()`), the ziggurat novelty drops, the Baron's removed pool and the trash
Tier 0 rows. The rows themselves (and their rules and rendering) are test_loot_tables.py's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_loot.py
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

ST_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "stratholme.py"

# normal lootid -> (heroic lootid, the list, the Haunted token key, 2 picks)
BOSSES = {
    "Barthilas": (10435, 310155, 5, None),
    "Baroness": (10436, 310156, 6, None),
    "Nerub'enkan": (10437, 310157, 5, None),
    "Maleki": (10438, 310158, 5, None),
    "Ramstein": (10439, 310159, 5, "haunted_token_wrist"),
    "Baron": (10440, 310160, 9, "haunted_token_legs"),
}
LISTS = {
    10435: {"strat_royal_tribunal_cloak", "strat_death_grips", "strat_peacemaker", "strat_crimson_felt_hat",
            "strat_idol_of_brutality"},
    10436: {"strat_banshee_finger", "strat_windshrieker_pauldrons", "strat_banshees_touch", "strat_anastari_heirloom",
            "strat_screeching_bow", "strat_shadowy_laced_handwraps"},
    10437: {"strat_husk_of_nerubenkan", "strat_darkspinner_claws", "strat_acid_etched_pauldrons",
            "strat_carapace_spine_crossbow", "strat_thuzadin_sash"},
    10438: {"strat_skull_of_burning_shadows", "strat_darkbind_fingers", "strat_flamescarred_girdle",
            "strat_pale_moon_cloak", "strat_bone_slicing_hatchet"},
    10439: {"strat_slavedrivers_cane", "strat_band_of_flesh", "strat_soulstealer_mantle", "strat_crest_of_retribution",
            "strat_ramsteins_lightning_bolts"},
    10440: {"strat_cape_of_the_black_baron", "strat_dracorian_gauntlets", "strat_seal_of_rivendare",
            "strat_scepter_of_the_unholy", "strat_gauntlets_of_deftness", "strat_helm_of_the_executioner",
            "strat_skullforge_reaver", "strat_bonescraper", "strat_runeblade_of_baron_rivendare"},
}
HARD_MODE = {"strat_ysidas_locket", "strat_blade_of_the_condemned", "strat_deathchargers_spur"}
TIER_0_ITEMS = set(range(16666, 16738))  # sets 181-189 (Tier 0), stock item_template entries
REINS = 13335


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "stratholme_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


class StratholmeLootSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, cls.decls = _declarations()
        cls.items = {e["id"] for e in cls.merged["item_declarations"] if e["id"].startswith("strat_")}
        cls.tokens = {e["id"][1] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = [d for d in cls.decls if d.listing and d.chance is None and not d.removal]
        cls.chances = [d for d in cls.decls if d.chance is not None]
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.pool_removals = [d for d in cls.decls if d.pool_removal]

    def groups(self, group: int) -> dict[tuple[int, int], L.LootDecl]:
        return {(d.lootid, d.group): d for d in self.lists if d.group == group}

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        by_key = self.groups(1)
        self.assertEqual(sum(len(v) for v in LISTS.values()), 35)
        for name, (normal, heroic, size, _token) in BOSSES.items():
            picks = 2 if name == "Baron" else 1
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = by_key[(lootid, 1)]
                    self.assertEqual((decl.tier, len(decl.items), decl.picks, decl.loot_mode),
                                     (tier, size, picks, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), LISTS[normal])
                    self.assertEqual(decl.reference is not None, picks > 1)
        self.assertEqual(sorted(d.reference for d in by_key.values() if d.reference), [1700006, 1700007])
        self.assertEqual(by_key[(10440, 1)].reference, 1700006)  # normal
        self.assertEqual(by_key[(310160, 1)].reference, 1700007)  # heroic

    def test_every_section_2_item_has_a_drop(self):
        listed = {key for keys in LISTS.values() for key in keys}
        self.assertEqual(len(listed), 35)
        self.assertEqual(len(listed & HARD_MODE), 0)
        self.assertTrue((listed | HARD_MODE) <= self.items)

    def test_heroic_lootids_are_the_bosses_own_heroic_entries(self):
        text = ST_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")
        for name, (normal, heroic, _size, _token) in BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in stratholme.py")
        lootids = {d.lootid for d in self.decls if d.listing}
        self.assertEqual({heroic for _n, heroic, *_ in BOSSES.values()} - lootids, set())

    def test_the_haunted_bracers_and_leggings_drop_at_the_kills_tier(self):
        by_key = self.groups(3)
        for name, (normal, heroic, _size, token) in BOSSES.items():
            if token is None:
                self.assertNotIn((normal, 3), by_key, name)
                continue
            self.assertIn(token, self.tokens)
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                decl = by_key[(lootid, 3)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode), ((token,), tier, 1, 1), name)
        self.assertEqual(len(by_key), 4)

    def test_hard_mode_is_group_two_of_the_barons_heroic_lootid_only(self):
        by_key = self.groups(2)
        self.assertEqual(sorted(by_key), [(310160, 2)])
        decl = by_key[(310160, 2)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, HARD_MODE))
        self.assertFalse(any(d.loot_mode != L.LOOT_MODE_DEFAULT for d in self.lists if d.group != 2))

    def test_deathchargers_reins_are_1_2_and_10_percent_in_one_group_at_most_one_drop(self):
        reins = [d for d in self.chances if d.item_entry == REINS]
        self.assertEqual({d.group for d in reins}, {4})
        by_lootid = {}
        for d in reins:
            by_lootid.setdefault(d.lootid, []).append(d)
        self.assertEqual(sorted(by_lootid), [10440, 310160])
        (normal,) = by_lootid[10440]
        self.assertEqual((normal.chance, normal.loot_mode, normal.reference), (1.0, L.LOOT_MODE_DEFAULT, None))
        plain, hard = sorted(by_lootid[310160], key=lambda d: d.loot_mode)
        self.assertEqual((plain.chance, plain.loot_mode, plain.reference), (2.0, L.LOOT_MODE_DEFAULT, None))
        self.assertEqual((hard.chance, hard.loot_mode, hard.reference),
                         (8.0, L.LOOT_MODE_HARD_MODE_1, 1700008))
        # a hard mode kill carries both loot mode bits: 2% + 8% in one group (one drop at most), a plain heroic 2%
        self.assertEqual(plain.chance + hard.chance, 10.0)
        # the stock 1% row (group 0) and the Cape in it (a list item now) leave the Baron's ungrouped rows with the
        # stock two rolls on pool 35028, which the list replaces
        removal = self.row_removals[(10440, 0)]
        self.assertEqual((set(removal.rows), removal.ref_rows), ({REINS, 13340}, (35028,)))
        self.assertEqual([d.reference for d in self.pool_removals], [35028])

    def test_the_ziggurat_novelty_items_keep_their_stock_rate_in_group_two(self):
        rows = {(d.lootid, d.item_entry): d for d in self.chances if d.group == 2}
        self.assertEqual(sorted(rows), [(10436, 13514), (10437, 13508), (10438, 13509),
                                        (310156, 13514), (310157, 13508), (310158, 13509)])
        self.assertTrue(all(d.chance == 20 and d.loot_mode == 1 and d.reference is None for d in rows.values()))
        # the six cut greens leave the normal lootids' stock group 2 (the two list items in it are declared items)
        cut = {d.lootid: set(d.replaces_items) for d in rows.values() if d.replaces_items}
        self.assertEqual(cut, {10436: {13535, 13537}, 10437: {13530, 13531}, 10438: {13527, 13528}})

    def test_the_cut_stock_group_one_rows(self):
        normal = self.groups(1)
        replaced = {lootid: set(d.replaces_items) for (lootid, _g), d in normal.items() if d.replaces_items}
        self.assertEqual(replaced, {
            10435: {18726}, 10436: {16704}, 10437: {16675, 18739}, 10438: {16691, 18735}, 10439: {16737, 18723},
            10440: {16668, 16678, 16687, 16694, 16699, 16709, 16719, 16728, 16732},
        })
        self.assertFalse(any(d.replaces_items or d.replaces_references for d in self.lists if d.tier != "normal"))

    def test_trash_tier_0_rows_go_from_24_lootids_and_only_tier_0(self):
        trash = {k: v for k, v in self.row_removals.items() if k[0] != 10440}
        self.assertEqual(len(trash), 24)
        self.assertTrue(all(group == 0 for _lootid, group in trash))
        for (lootid, _group), decl in sorted(trash.items()):
            with self.subTest(lootid=lootid):
                self.assertTrue(set(decl.rows) <= TIER_0_ITEMS, decl.rows)
                self.assertEqual(decl.ref_rows, ())
        # section 1 bosses and Willey keep their Tier 0 rows until wave 2 (L-2); no boss lootid is touched here
        boss_lootids = {lootid for lootid, *_ in BOSSES.values()}
        self.assertFalse(boss_lootids & {lootid for lootid, _g in trash})
        self.assertFalse({10516, 10558, 10808, 10811, 10997, 10813} & {lootid for lootid, _g in trash})

    def test_pools_come_from_1700006_and_stay_inside_the_block(self):
        pools = [d.reference for d in self.decls if d.reference and d.pool_removal is False]
        self.assertEqual(sorted(pools), [1700006, 1700007, 1700008])


if __name__ == "__main__":
    unittest.main()
