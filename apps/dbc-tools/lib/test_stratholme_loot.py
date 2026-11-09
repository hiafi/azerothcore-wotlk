"""
Stratholme build WPs L-1 and L-2: the real declarations in source/items/stratholme_loot.py (item keys from
stratholme.py, tokens from haunted_set.py).

Wave 1 (L-1): the Service Entrance bosses' lists (Barthilas, Baroness Anastari, Nerub'enkan, Maleki, Ramstein, Baron
Rivendare), the Haunted Bracers and Leggings, the Baron's hard mode group and Deathcharger's Reins (1% normal, 2%
heroic, 10% hard mode through `loot_chance()`), the ziggurat novelty drops, the Baron's removed pool and the trash
Tier 0 rows. Wave 2 (L-2, `MainGateLootTest`): the Main Gate bosses' lists (The Unforgiven, Forresten, Timmy, Malor,
Willey, Galford, Balnazzar), the Haunted Boots and Chestpiece, Balnazzar's two picks and hard mode group, Forresten's
removed tree, Willey's and Balnazzar's removed pools and Malor's relic share. The rows themselves (and their rules
and rendering) are test_loot_tables.py's.

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
# The Main Gate (wave 2, L-2): normal lootid -> heroic lootid, and the stock pools and tree it removes or replaces
MAIN_GATE = {
    10516: 310163, 10558: 310164, 10808: 310166, 10811: 310168, 10997: 310173, 10813: 310170, 11032: 310175,
}
MAIN_GATE_LOOTIDS = set(MAIN_GATE) | set(MAIN_GATE.values())
MAIN_GATE_POOLS = {35026, 35027}


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
        cls.wave_1 = wave_1 = [
            d for d in cls.decls if d.lootid not in MAIN_GATE_LOOTIDS and d.reference not in MAIN_GATE_POOLS
        ]
        cls.lists = [d for d in wave_1 if d.listing and d.chance is None and not d.removal]
        cls.chances = [d for d in wave_1 if d.chance is not None]
        cls.row_removals = {(d.lootid, d.group): d for d in wave_1 if d.row_removal}
        cls.pool_removals = [d for d in wave_1 if d.pool_removal]

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
        lootids = {d.lootid for d in self.wave_1 if d.listing}
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
        # no boss lootid is touched here: the Main Gate bosses' Tier 0 pieces are cut by their lists (wave 2)
        boss_lootids = {lootid for lootid, *_ in BOSSES.values()}
        self.assertFalse(boss_lootids & {lootid for lootid, _g in trash})
        self.assertFalse(set(MAIN_GATE) & {lootid for lootid, _g in trash})

    def test_pools_come_from_1700006_and_stay_inside_the_block(self):
        pools = [d.reference for d in self.wave_1 if d.reference and d.pool_removal is False]
        self.assertEqual(sorted(pools), [1700006, 1700007, 1700008])

    def test_stock_resistances_and_random_properties_are_cleared_on_every_tier(self):
        # The list names a primary and a secondary only; the budget neither prices nor scales the stock extras, so a
        # minted tier would copy them for free (the Scholomance precedent, scholomance.py docstring). The pairs are
        # what `generate.py --check` warned about on the unedited declarations.
        cleared = {
            "strat_wailing_nightbane_pauldrons": ("shadow_res",),
            "strat_plaguebat_fur_gloves": ("shadow_res",),
            "strat_archivist_cape": ("RandomProperty",),
            "strat_foresight_girdle": ("RandomProperty",),
            "strat_grand_crusaders_helm": ("shadow_res",),
            "strat_banshee_finger": ("frost_res",),
            "strat_windshrieker_pauldrons": ("arcane_res",),
            "strat_banshees_touch": ("frost_res", "arcane_res"),
            "strat_screeching_bow": ("shadow_res",),
            "strat_shadowy_laced_handwraps": ("shadow_res",),
            "strat_husk_of_nerubenkan": ("nature_res",),
            "strat_darkspinner_claws": ("nature_res", "shadow_res"),
            "strat_acid_etched_pauldrons": ("nature_res",),
            "strat_skull_of_burning_shadows": ("fire_res", "shadow_res"),
            "strat_darkbind_fingers": ("shadow_res",),
            "strat_flamescarred_girdle": ("fire_res",),
            "strat_pale_moon_cloak": ("shadow_res",),
        }
        decls = {e["id"]: e["_decl"] for e in self.merged["item_declarations"] if e["id"].startswith("strat_")}
        for key, columns in cleared.items():
            with self.subTest(item=key):
                declared = dict(decls[key].columns)
                for column in columns:
                    self.assertEqual(declared.get(column), 0, column)


# --- Wave 2: the Main Gate (L-2) -----------------------------------------------------------------------------------

# normal lootid -> (name, the list, the Haunted token key, the stock group 1 rows the list replaces)
MAIN_GATE_LISTS = {
    10516: ("The Unforgiven", {"strat_mask_of_the_unforgiven", "strat_wailing_nightbane_pauldrons",
                               "strat_soul_breaker", "strat_shroud_of_the_last_soul"},
            None, {13409, 16717}),
    10558: ("Forresten", {"strat_piccolo_of_the_flaming_fire", "strat_rainbow_girdle",
                          "strat_hearthsingers_tuning_fork", "strat_songbird_sash", "strat_plaguebat_fur_gloves"},
            "haunted_token_feet", {13378, 13383, 16682}),
    10808: ("Timmy", {"strat_the_cruel_hand_of_timmy", "strat_grimgore_noose", "strat_freeze_tag_mittens"},
            None, {13400, 13402, 16724}),
    10811: ("Galford", {"strat_archivist_cape", "strat_foresight_girdle", "strat_pyrewatch_coif",
                        "strat_tome_of_knowledge"},
            None, {16692, 18716}),
    10997: ("Willey", {"strat_willeys_portable_howitzer", "strat_cannonball_runner", "strat_barrage_girdle",
                       "strat_dianas_pearl_necklace", "strat_mantle_of_the_scarlet_crusade",
                       "strat_helm_of_the_new_moon", "strat_scarlet_throwing_axes"},
            None, set()),
    10813: ("Balnazzar", {"strat_star_of_mystaria", "strat_demonshear", "strat_wyrmtongue_shoulders",
                          "strat_crown_of_tyranny", "strat_gift_of_the_elven_magi",
                          "strat_hammer_of_the_grand_crusader", "strat_grand_crusaders_helm",
                          "strat_shroud_of_the_nathrezim", "strat_book_of_the_dead"},
            "haunted_token_chest", set()),
    11032: ("Malor", {"strat_gauntlets_of_the_zealot", "strat_inquisitors_girdle", "strat_libram_of_zeal",
                      "strat_totem_of_the_storm", "strat_idol_of_the_moon"},
            None, set()),
}
BALNAZZAR_HARD_MODE = {"strat_carrion_signet", "strat_dust_of_the_nathrezim", "strat_two_faced_tome"}
TIER_0_BOSS_PIECES = {16717, 16682, 16724, 16692, 16708, 16725}  # Wildheart Gloves ... Lightforge Boots


class MainGateLootTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, decls = _declarations()
        cls.items = {e["id"] for e in cls.merged["item_declarations"] if e["id"].startswith("strat_")}
        cls.tokens = {e["id"][1] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.decls = [d for d in decls if d.lootid in MAIN_GATE_LOOTIDS or d.reference in MAIN_GATE_POOLS]
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and d.chance is None and not d.removal}
        cls.chances = [d for d in cls.decls if d.chance is not None]
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.pool_removals = {d.reference: d for d in cls.decls if d.pool_removal}

    def list_group(self, lootid: int) -> int:
        return 2 if lootid == 11032 else 1  # Malor's group 1 is his shared world pools

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        self.assertEqual(sum(len(v[1]) for v in MAIN_GATE_LISTS.values()), 37)
        for normal, (name, keys, _token, _cut) in MAIN_GATE_LISTS.items():
            picks = 2 if normal == 10813 else 1
            group = self.list_group(normal)
            for lootid, tier in ((normal, "normal"), (MAIN_GATE[normal], "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, group)]
                    self.assertEqual((decl.tier, decl.picks, decl.loot_mode), (tier, picks, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= self.items)
                    self.assertEqual(decl.reference is not None, picks > 1)

    def test_every_main_gate_item_has_a_drop(self):
        # the 37 list items plus the three hard mode items are the 40 Main Gate items of W1 that a boss drops (the
        # Militia Shoulderguard drops from Malor's stock 0.02% row, the Plaguebat Fur Gloves also from the BoE pool)
        listed = {key for v in MAIN_GATE_LISTS.values() for key in v[1]}
        main_gate_items = {k for k in self.items} - {k for v in LISTS.values() for k in v} - HARD_MODE
        self.assertEqual(main_gate_items - listed - BALNAZZAR_HARD_MODE, {"strat_stratholme_militia_shoulderguard"})
        self.assertTrue(BALNAZZAR_HARD_MODE <= self.items)

    def test_the_heroic_lootids_are_the_bosses_own_heroic_entries(self):
        text = ST_DUNGEON.read_text(encoding="utf-8")
        for normal, heroic in MAIN_GATE.items():
            with self.subTest(boss=MAIN_GATE_LISTS[normal][0]):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in stratholme.py")
        self.assertRegex(text, r"10812: _boss\(340_000\)")  # Dathrohan has no loot of his own

    def test_the_cut_stock_rows_are_named_and_only_on_the_normal_lootids(self):
        for normal, (name, _keys, _token, cut) in MAIN_GATE_LISTS.items():
            with self.subTest(boss=name):
                decl = self.lists[(normal, self.list_group(normal))]
                self.assertEqual(set(decl.replaces_items), cut)
                heroic = self.lists[(MAIN_GATE[normal], self.list_group(normal))]
                self.assertEqual((heroic.replaces_items, heroic.replaces_references), ((), ()))
        # the four Tier 0 boss pieces in a group 1 list are cut by it; the other two are in the deleted pools
        named = {item for v in MAIN_GATE_LISTS.values() for item in v[3]}
        self.assertEqual(TIER_0_BOSS_PIECES & named, {16717, 16682, 16724, 16692})

    def test_willey_and_balnazzar_replace_their_two_rolls_and_the_pools_go(self):
        willey = self.lists[(10997, 1)]
        balnazzar = self.lists[(10813, 1)]
        self.assertEqual(willey.replaces_references, (35026,))
        self.assertEqual(balnazzar.replaces_references, (35027,))
        self.assertEqual(sorted(self.pool_removals), [35026, 35027])
        # the cut pieces and the Tier 0 ones (Shadowcraft Spaulders, Lightforge Boots) leave with the pools
        self.assertIsNone(self.lists[(310173, 1)].reference)
        self.assertEqual(willey.picks, 1)
        self.assertEqual((balnazzar.reference, self.lists[(310170, 1)].reference), (1700009, 1700010))

    def test_the_haunted_boots_and_chestpiece_drop_at_the_kills_tier(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == 3}
        self.assertEqual(sorted(by_key), [(10558, 3), (10813, 3), (310164, 3), (310170, 3)])
        for normal, (name, _keys, token, _cut) in MAIN_GATE_LISTS.items():
            if token is None:
                self.assertNotIn((normal, 3), by_key, name)
                continue
            self.assertIn(token, self.tokens)
            for lootid, tier in ((normal, "normal"), (MAIN_GATE[normal], "heroic")):
                decl = by_key[(lootid, 3)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode), ((token,), tier, 1, 1), name)

    def test_balnazzars_hard_mode_is_group_two_of_his_heroic_lootid_only_at_loot_mode_2(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == 2}
        self.assertEqual(sorted(by_key), [(11032, 2), (310170, 2), (310175, 2)])  # the two others are Malor's list
        decl = by_key[(310170, 2)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, BALNAZZAR_HARD_MODE))
        self.assertFalse(any(d.loot_mode != L.LOOT_MODE_DEFAULT for k, d in self.lists.items() if k != (310170, 2)))

    def test_forrestens_tree_row_is_removed_and_the_shared_pool_stays(self):
        removal = self.row_removals[(10558, 5)]
        self.assertEqual((removal.rows, removal.ref_rows), ((), (1000357,)))
        self.assertNotIn(1000357, self.pool_removals)  # dozens of creatures roll the tree
        self.assertNotIn((10558, 5), self.lists)

    def test_malors_list_is_a_group_of_its_own_and_the_relics_leave_the_world_pool_share(self):
        self.assertNotIn((11032, 1), self.lists)  # his group 1 (the shared world pools) is never declared
        removal = self.row_removals[(11032, 1)]
        self.assertEqual((removal.rows, removal.ref_rows), ((), (24021,)))
        self.assertNotIn(24021, self.pool_removals)
        libram = {d.lootid: d for d in self.chances}
        self.assertEqual(sorted(libram), [11032, 310175])
        for d in libram.values():
            self.assertEqual((d.item_entry, d.group, d.chance, d.loot_mode, d.reference), (23203, 6, 0.17, 1, None))
        self.assertIn("strat_totem_of_the_storm", MAIN_GATE_LISTS[11032][1])
        self.assertIn("strat_idol_of_the_moon", MAIN_GATE_LISTS[11032][1])

    def test_no_new_group_collides_with_a_stock_group_that_stays(self):
        # Forresten's lists/tokens (groups 1, 3) and Balnazzar's (1, 2, 3) sit beside the kept group 0 rows; Malor's
        # groups 2 and 6 beside his kept group 1; nothing declares group 0 or reuses a kept group
        kept = {10558: {0}, 10811: {0}, 10813: {0}, 11032: {0, 1}, 10997: {0}, 10516: {0}, 10808: {0}}
        for (lootid, group) in list(self.lists) + [(d.lootid, d.group) for d in self.chances]:
            normal = lootid if lootid in MAIN_GATE else next(n for n, h in MAIN_GATE.items() if h == lootid)
            with self.subTest(lootid=lootid, group=group):
                self.assertNotIn(group, kept[normal])
                self.assertGreaterEqual(group, 1)

    def test_the_pools_continue_from_1700009(self):
        pools = [d.reference for d in self.decls if d.reference and not d.pool_removal]
        self.assertEqual(sorted(pools), [1700009, 1700010])


if __name__ == "__main__":
    unittest.main()
