"""
Scarlet Monastery build, WP L-1: the wave 1 declarations in source/items/scarlet_monastery_loot.py (item keys from
scarlet_monastery.py and scarlet_monastery_hard_mode.py, the Zealot's Helm from zealot_set.py).

Sections 1 and 2: the lists of Vishas, Ironspine, the council's one pool (on the Fallen Champion), Thalnos,
Loksey, Kell, Hollis Grey and Doan at the Normal tier on the normal lootids and the Heroic tier on the heroic
bodies' own lootids, the cut stock rows, Azshir's emptied group and his heroic copy, the Zealot's Helm on Doan's
heroic lootid only and the Desecration's and the Heresy's hard mode lists at LootMode 2. The rows themselves (and
their rules and rendering) are test_loot_tables.py's; the real plan (tiers, the live stock groups) is
`generate.py --check`'s.

`WaveOneLootTest` looks at wave 1's declarations only: the file's wave 2 block (WP L-2, `WAVE_2_LOOTIDS`) is filtered
out. `WaveTwoLootTest` (WP L-2) covers sections 3 and 4: Crell, Halden, Herod, Thorne and Whitemane's lists, the two
Zealot's tokens, the Call to Arms and the Truth, Mograine's and Fairbanks's emptied stock groups; `ChestRevTest` is
the Last Stand chest's gameobject loot (rev_loot_wave_2_scarlet_monastery.sql), with the BRD duplicate-item rule.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_loot.py
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

SM_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "scarlet_monastery.py"
COMMON = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "_common.py"
CHEST_REV = (TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"
             / "rev_loot_wave_2_scarlet_monastery.sql")
D13_REV = (TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"
           / "rev_last_stand_scarlet_monastery.sql")
ITEM_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
LOOT_FILE = TOOL_ROOT / "source" / "items" / "scarlet_monastery_loot.py"

LIST_GROUP, HARD_MODE_GROUP, TOKEN_GROUP = 1, 2, 3
SILK_CLOTH, HEART_OF_ZEAL = 4306, 5805  # the kept stock group 0 rows (the quest item and the cloth)

# scarlet-monastery-rework.md ## Loot "Boss lists" (ruling 58), copied (docs/ is not in every checkout): the doc's
# item names per boss, in the doc's order. The council is one pool.
DOC_LISTS = {
    "Vishas": ("Bloody Brass Knuckles", "Torturing Poker", "Branded Leather Bracers", "Confessor's Gloves",
               "Interrogator's Thumbscrews"),
    "Ironspine": ("Ironspine's Eye", "Ironspine's Fist", "Bonecrawler Boots", "Bone-link Legguards",
                  "Cloak of Knitted Bone"),
    "Council": ("Necrotic Wand", "Blighted Leggings", "Ghostshard Talisman", "Morbid Dawn", "Ebon Vise",
                "Vigil-keeper's Gauntlets"),
    "Thalnos": ("Orb of the Forgotten Seer", "Bloodmage's Handwraps", "Bloodstained Cloak", "Bloodletting Kris",
                "Sanguine Signet"),
    "Loksey": ("Dog Training Gloves", "Loksey's Training Stick", "Dog Whistle", "Kennelmaster's Crossbow",
               "Leash-scarred Gauntlets"),
    "Kell": ("Dusty Mail Boots", "Antiquarian's Signet", "Kirin Tor Spellblade", "Necromancer's Skull"),
    "Hollis Grey": ("Index-keeper's Bindings", "Lector's Sash", "Forbidden Tome", "Burning Page"),
    "Doan": ("Illusionary Rod", "Hypnotic Blade", "Deadman's Hand", "Arcanist's Cord", "Totem of Righteous Fire"),
}
# The stock entries of the doc's Alter / Keep rows (the stock table of the doc's "Stock loot", `item(base=)`).
STOCK_BASE = {
    "Bloody Brass Knuckles": 7683, "Torturing Poker": 7682, "Branded Leather Bracers": 19508,
    "Ironspine's Eye": 7686, "Ironspine's Fist": 7687, "Necrotic Wand": 7708, "Blighted Leggings": 7709,
    "Ghostshard Talisman": 7731, "Morbid Dawn": 7689, "Ebon Vise": 7690, "Orb of the Forgotten Seer": 7685,
    "Dog Training Gloves": 7756, "Loksey's Training Stick": 7710, "Dog Whistle": 3456, "Dusty Mail Boots": 19509,
    "Illusionary Rod": 7713, "Hypnotic Blade": 7714, "Deadman's Hand": 34227,
}

# name -> (normal lootid, heroic lootid, the doc list's key, the list (item() keys), the family token key (None: no
# token), the stock group 1 rows the list replaces (item_template entries))
BOSSES = {
    "Vishas": (3983, 310424, "Vishas", {
        "sm_bloody_brass_knuckles", "sm_torturing_poker", "sm_branded_leather_bracers", "sm_confessors_gloves",
        "sm_interrogators_thumbscrews"}, None, set()),
    "Ironspine": (6489, 310453, "Ironspine", {
        "sm_ironspines_eye", "sm_ironspines_fist", "sm_bonecrawler_boots", "sm_bone_link_legguards",
        "sm_cloak_of_knitted_bone"}, None, {7688}),
    "Fallen Champion": (6488, 310452, "Council", {
        "sm_necrotic_wand", "sm_blighted_leggings", "sm_ghostshard_talisman", "sm_morbid_dawn", "sm_ebon_vise",
        "sm_vigil_keepers_gauntlets"}, None, {7691}),
    "Thalnos": (4543, 310448, "Thalnos", {
        "sm_orb_of_the_forgotten_seer", "sm_bloodmages_handwraps", "sm_bloodstained_cloak", "sm_bloodletting_kris",
        "sm_sanguine_signet"}, None, {7684}),
    "Loksey": (3974, 310420, "Loksey", {
        "sm_dog_training_gloves", "sm_loksey_training_stick", "sm_dog_whistle", "sm_kennelmasters_crossbow",
        "sm_leash_scarred_gauntlets"}, None, set()),
    "Kell": (300910, 310467, "Kell", {
        "sm_dusty_mail_boots", "sm_antiquarians_signet", "sm_kirin_tor_spellblade", "sm_necromancers_skull"},
        None, set()),
    "Hollis Grey": (300913, 310469, "Hollis Grey", {
        "sm_index_keepers_bindings", "sm_lectors_sash", "sm_forbidden_tome", "sm_burning_page"}, None, set()),
    "Doan": (6487, 310451, "Doan", {
        "sm_illusionary_rod", "sm_hypnotic_blade", "sm_deadmans_hand", "sm_arcanists_cord",
        "sm_totem_of_righteous_fire"}, "zealot_token_head", {7711, 7712}),
}
AZSHIR = (6490, 310454)
THALNOS_HEROIC, DOAN_HEROIC = 310448, 310451
DESECRATION = {"sm_purebloods_rallying_standard", "sm_fairbells_censer", "sm_voss_blessed_signet"}
HERESY = {"sm_shard_of_the_phylactery", "sm_heretics_wand", "sm_fissure_touched_grips"}

NORMAL_LOOTIDS = {name: v[0] for name, v in BOSSES.items()}
HEROIC_LOOTIDS = {name: v[1] for name, v in BOSSES.items()}
ALL_LOOTIDS = {*NORMAL_LOOTIDS.values(), *HEROIC_LOOTIDS.values()}
# The wave 2 (sections 3 and 4) lootids L-2 owns: Crell, Halden, Herod, Thorne, Mograine, Whitemane and Fairbanks,
# normal and heroic. Wave 1's tests do not look at them.
WAVE_2_LOOTIDS = {300940, 300942, 3975, 300946, 3976, 3977, 4542,
                  310476, 310477, 310421, 310478, 310479, 310423}

# Stock group 0 rows and the world-drop references that stay (not named by any declaration).
STOCK_KEEP = {SILK_CLOTH, HEART_OF_ZEAL}
WORLD_DROP_REFERENCES = {1189000, 1000332}


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "scarlet_monastery_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


class WaveOneLootTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        cls.every = every
        cls.decls = [d for d in every if d.lootid not in WAVE_2_LOOTIDS]  # wave 1's only
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("sm_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and not d.removal}
        cls.group_removals = {(d.lootid, d.group): d for d in cls.decls if d.removal}
        cls.copies = {d.lootid: d for d in cls.decls if d.copy_only}

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, _doc, keys, _token, _cut) in BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes_are_the_docs_boss_list_rows(self):
        sizes = {name: len(v[3]) for name, v in BOSSES.items()}
        self.assertEqual(sizes, {"Vishas": 5, "Ironspine": 5, "Fallen Champion": 6, "Thalnos": 5, "Loksey": 5,
                                 "Kell": 4, "Hollis Grey": 4, "Doan": 5})
        for name, (_n, _h, doc, keys, _t, _c) in BOSSES.items():
            self.assertEqual(len(DOC_LISTS[doc]), len(keys), name)

    def test_every_list_item_is_the_docs_item_by_name_or_stock_entry(self):
        for name, (_n, _h, doc, keys, _t, _c) in BOSSES.items():
            names_by_key = {}
            for key in keys:
                decl = self.items[key]
                if decl.base:
                    stock = {v: k for k, v in STOCK_BASE.items()}
                    self.assertIn(decl.base, stock, f"{name}: {key} base {decl.base} is not a doc stock item")
                    names_by_key[key] = stock[decl.base]
                else:
                    names_by_key[key] = decl.name
            self.assertEqual(sorted(names_by_key.values()), sorted(DOC_LISTS[doc]), name)

    def test_the_council_is_one_pool_on_the_fallen_champion_and_azshir_drops_none_of_it(self):
        champion = self.lists[(6488, LIST_GROUP)]
        self.assertEqual(len(champion.items), 6)
        removal = self.group_removals[(AZSHIR[0], LIST_GROUP)]
        self.assertEqual(set(removal.replaces_items), {7708, 7709, 7731})
        # no list on Azshir's normal or heroic lootid; his heroic body copies his normal silk and world drops
        self.assertFalse([k for k in self.lists if k[0] in AZSHIR])
        self.assertEqual(set(self.copies), {AZSHIR[1]})
        # the three stock entries of the removed group are the pool's bases
        bases = {self.items[key].base for key in champion.items if self.items[key].base}
        self.assertTrue({7708, 7709, 7731} <= bases)

    def test_fairbanks_moved_items_are_on_vishas_and_kell(self):
        self.assertIn("sm_branded_leather_bracers", self.lists[(3983, LIST_GROUP)].items)
        self.assertIn("sm_dusty_mail_boots", self.lists[(300910, LIST_GROUP)].items)
        self.assertEqual((self.items["sm_branded_leather_bracers"].base, self.items["sm_dusty_mail_boots"].base),
                         (19508, 19509))
        # Fairbanks's stock table (4542) is L-2's (remove_loot_group): this file's wave 1 block never names it
        self.assertFalse([d for d in self.every if d.lootid == 4542 and d.where.startswith("boss_loot")
                          and d.tier == "normal" and d.items and "sm_dusty_mail_boots" in d.items])

    def test_the_new_bosses_have_no_stock_rows_to_replace(self):
        for lootid in (300910, 300913):
            self.assertEqual(self.lists[(lootid, LIST_GROUP)].replaces_items, ())
        self.assertEqual(NORMAL_LOOTIDS["Kell"], 300910)
        self.assertEqual(NORMAL_LOOTIDS["Hollis Grey"], 300913)

    # --- the cuts --------------------------------------------------------------------------------------------------

    def test_the_cut_stock_group_one_rows_are_named_and_only_on_the_normal_lootids(self):
        for name, (normal, heroic, _doc, keys, _token, cut) in BOSSES.items():
            with self.subTest(boss=name):
                decl = self.lists[(normal, LIST_GROUP)]
                self.assertEqual(set(decl.replaces_items), cut)
                other = self.lists[(heroic, LIST_GROUP)]
                self.assertEqual((other.replaces_items, other.replaces_references), ((), ()))
                # a replaced row is never a list item's own stock entry
                stock = {self.items[key].base for key in keys if self.items[key].base}
                self.assertFalse(cut & stock)

    def test_the_approved_cuts(self):
        # Embalmed Shroud, Bloodmage Mantle (token slots, no set), Ironspine's Ribcage, Robe and Mantle of Doan (set
        # pieces of the Zealot's family): the SP "Structure" 3
        cut_all = set().union(*(v[5] for v in BOSSES.values()))
        self.assertEqual(cut_all, {7691, 7684, 7688, 7711, 7712})
        self.assertEqual(self.lists[(6489, LIST_GROUP)].replaces_items, (7688,))

    def test_the_stock_quest_cloth_and_world_drop_rows_are_never_named(self):
        named = set()
        for d in self.decls:
            named |= set(d.rows) | set(d.replaces_items)
            self.assertFalse(WORLD_DROP_REFERENCES & set(d.replaces_references), d.where)
        self.assertFalse(STOCK_KEEP & named)
        self.assertFalse([d for d in self.decls if d.row_removal or d.pool_removal])

    # --- the Zealot's Helm -----------------------------------------------------------------------------------------

    def test_the_helm_token_is_group_three_of_doans_heroic_lootid_only(self):
        tokens = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP}
        self.assertEqual(sorted(tokens), [(DOAN_HEROIC, TOKEN_GROUP)])
        decl = tokens[(DOAN_HEROIC, TOKEN_GROUP)]
        self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode),
                         (("zealot_token_head",), "heroic", 1, L.LOOT_MODE_DEFAULT))
        self.assertIn("zealot_token_head", self.tokens)
        self.assertEqual(self.tokens["zealot_token_head"].ladder.name, "vanilla_heroic_set")
        # the family is heroic-only: no normal lootid and no Graveyard boss carries a token
        self.assertNotIn((6487, TOKEN_GROUP), self.lists)
        self.assertEqual({k[0] for k in tokens} & {v[0] for v in BOSSES.values()}, set())

    # --- the hard mode lists ---------------------------------------------------------------------------------------

    def test_the_hard_mode_lists_are_group_two_of_the_heroic_lootids_at_loot_mode_2(self):
        for lootid, keys in ((THALNOS_HEROIC, DESECRATION), (DOAN_HEROIC, HERESY)):
            decl = self.lists[(lootid, HARD_MODE_GROUP)]
            self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                             (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, keys, False))
            self.assertEqual(len(decl.items), 3)
            # the list stays: a lit kill adds the three on top of it
            self.assertIn((lootid, LIST_GROUP), self.lists)
        # Thalnos's normal lootid and Doan's get nothing (heroic only)
        self.assertNotIn((4543, HARD_MODE_GROUP), self.lists)
        self.assertNotIn((6487, HARD_MODE_GROUP), self.lists)

    def test_only_the_two_hard_mode_groups_roll_at_loot_mode_2(self):
        modes = sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1)
        self.assertEqual(set(modes), {(THALNOS_HEROIC, 2), (DOAN_HEROIC, 2)})
        for key in modes:
            self.assertEqual(self.lists[key].loot_mode, 2)

    def test_the_hard_mode_items_are_on_the_hard_mode_ladder(self):
        for key in DESECRATION | HERESY:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    def test_the_hard_mode_loot_bit_is_the_one_the_instance_sets(self):
        kit = (TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "Kit" / "DungeonKit.cpp")
        if kit.is_file():
            self.assertIn("AddLootMode(LOOT_MODE_HARD_MODE_1)", kit.read_text(encoding="utf-8"))
        self.assertEqual(L.LOOT_MODE_HARD_MODE_1, 2)

    # --- groups and counts -----------------------------------------------------------------------------------------

    def test_no_flex_groups_and_no_chance_rows(self):
        groups = {group for _lootid, group in self.lists}
        self.assertEqual(groups, {1, 2, 3})
        self.assertFalse({11, 12, 13} & groups)
        self.assertFalse([d for d in self.decls if d.loot_mode & 0x8 or d.chance is not None])
        self.assertEqual([d for d in self.decls if d.reference is not None], [])

    def test_declaration_counts(self):
        # 8 bosses x 2 lootids (list) + the Helm + the two hard mode groups; Azshir's group removal and heroic copy
        self.assertEqual(len(self.lists), 8 * 2 + 1 + 2)
        self.assertEqual(len(self.group_removals), 1)
        self.assertEqual(len(self.copies), 1)
        self.assertEqual(len(self.decls), len(self.lists) + 1 + 1)

    def test_wave_1_declares_no_section_3_or_4_lootid(self):
        lootids = {d.lootid for d in self.decls}
        self.assertEqual(lootids - ALL_LOOTIDS - {AZSHIR[0], AZSHIR[1]}, set())

    # --- one item, one row ------------------------------------------------------------------------------------------

    def test_no_loot_table_lists_an_item_twice(self):
        # creature_loot_template is keyed (Entry, Item, Reference, GroupId) and the engine's group roll skips an
        # equippable the loot already holds: a duplicate item in one lootid fails db-import partway (BRD LESSONS).
        # Resolved by key and by stock entry: the lists, the hard mode lists and the token of one lootid share nothing
        # with each other nor with the group 0 rows that stay (Silk Cloth, Heart of Zeal).
        by_lootid: dict[int, list[str]] = {}
        for (lootid, _group), decl in self.lists.items():
            by_lootid.setdefault(lootid, []).extend(decl.items)
        for lootid, keys in by_lootid.items():
            with self.subTest(lootid=lootid):
                self.assertEqual(len(keys), len(set(keys)), keys)
                bases = [self.items[k].base for k in keys if k in self.items and self.items[k].base]
                self.assertEqual(len(bases), len(set(bases)), bases)
                self.assertFalse(STOCK_KEEP & set(bases))

    def test_no_item_drops_from_two_bosses_of_the_dungeon(self):
        # SP: "no duplicate in wave 3" (a list item is one boss's), the council being one pool on one lootid
        seen: dict[str, str] = {}
        for name, (_n, _h, _doc, keys, _t, _c) in BOSSES.items():
            for key in keys:
                self.assertNotIn(key, seen, f"{key} on {name} and {seen.get(key)}")
                seen[key] = name
        for keys in (DESECRATION, HERESY):
            self.assertFalse(set(seen) & keys)
        self.assertFalse(DESECRATION & HERESY)

    def test_the_replaced_stock_entries_are_not_any_boss_lists_stock_entry(self):
        cuts = set().union(*(v[5] for v in BOSSES.values()))
        bases = {self.items[key].base for v in BOSSES.values() for key in v[3] if self.items[key].base}
        self.assertFalse(cuts & bases)

    # --- the items the lists name -----------------------------------------------------------------------------------

    def test_list_items_are_on_the_dungeon_ladder_and_every_declared_tier_exists(self):
        for decl in self.decls:
            if not decl.listing or decl.removal:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                if decl.tier in ("normal", "heroic") and key in self.items:
                    self.assertEqual(ladder.name, "vanilla_dungeon", key)

    def test_every_wave_1_list_item_of_the_gear_stage_is_dropped_by_someone(self):
        listed = set().union(*(v[3] for v in BOSSES.values()))
        # the gear stage's 64 list items: 39 of wave 1's bosses (5+5+6+5+5+4+4+5) and 25 of wave 2's (L-2)
        self.assertEqual(len(listed), 39)
        hard_mode = DESECRATION | HERESY
        self.assertTrue(listed <= set(self.items))
        self.assertTrue(hard_mode <= set(self.items))


# --- wave 2 (WP L-2) ------------------------------------------------------------------------------------------------

# scarlet-monastery-rework.md ## Loot "Boss lists" and "Hard mode lists", copied: the doc's item names per boss.
DOC_LISTS_2 = {
    "Crell": ("Proving Blade", "Red-Hot Gauntlets", "Tempered Girdle", "Forge-tempered Buckler"),
    "Halden": ("Drillmaster's Girdle", "Drillmaster's Longbow", "Drillfield Cape", "Medal of the Proving Ground"),
    "Herod": ("Ravager", "Whirlwind Legplates", "Blade-dancer's Treads", "Pendant of the Scarlet Champion"),
    "Thorne": ("Furrowed Boots", "Waterbearer's Girdle", "Idol of the Harvest", "Pruning Scythe"),
    "Last Stand": ("Aegis of the Scarlet Commander", "Mograine's Might", "Gauntlets of Divinity",
                   "Captain's Legguards", "Libram of the Last Stand"),
    "Whitemane": ("Triune Amulet", "Hand of Righteousness", "Cinch of the Faithful", "Whitemane's Vigil Candle"),
}
DOC_HARD_MODE_2 = {
    "Herod": ("Scarlet Garrison Rifle", "Garrison Bulwark", "Staff of the Consecrated Hall"),
    "Whitemane": ("Father's Verdict", "Treads of Denial", "Inquisitor's Rosary"),
}
STOCK_BASE_2 = {"Ravager": 7717, "Aegis of the Scarlet Commander": 7726, "Mograine's Might": 7723,
                "Gauntlets of Divinity": 7724, "Triune Amulet": 7722, "Hand of Righteousness": 7721}

# name -> (normal lootid, heroic lootid, doc list key, the list (item() keys), the family token (None), the stock
# group 1 rows the list replaces, is the heroic lootid behind BIND_WAVE_2)
WAVE_2_BOSSES = {
    "Crell": (300940, 310476, "Crell", {
        "sm_proving_blade", "sm_red_hot_gauntlets", "sm_tempered_girdle", "sm_forge_tempered_buckler"},
        None, set(), False),
    "Halden": (300942, 310477, "Halden", {
        "sm_drillmasters_girdle", "sm_drillmasters_longbow", "sm_drillfield_cape", "sm_medal_of_the_proving_ground"},
        None, set(), False),
    "Herod": (3975, 310421, "Herod", {
        "sm_ravager", "sm_whirlwind_legplates", "sm_blade_dancers_treads", "sm_pendant_of_the_scarlet_champion"},
        "zealot_token_shoulders", {7718, 7719, 10330}, True),
    "Thorne": (300946, 310479, "Thorne", {
        "sm_furrowed_boots", "sm_waterbearers_girdle", "sm_idol_of_the_harvest", "sm_pruning_scythe"},
        None, set(), False),
    "Whitemane": (3977, 310423, "Whitemane", {
        "sm_triune_amulet", "sm_hand_of_righteousness", "sm_cinch_of_the_faithful", "sm_whitemanes_vigil_candle"},
        "zealot_token_chest", {7720}, True),
}
LAST_STAND = {
    "sm_aegis_of_the_scarlet_commander", "sm_mograines_might", "sm_gauntlets_of_divinity", "sm_captains_legguards",
    "sm_libram_of_the_last_stand"}
CALL_TO_ARMS = {"sm_scarlet_garrison_rifle", "sm_garrison_bulwark", "sm_staff_of_the_consecrated_hall"}
TRUTH = {"sm_fathers_verdict", "sm_treads_of_denial", "sm_inquisitors_rosary"}
MOGRAINE, FAIRBANKS = 3976, 4542
CHESTS = {"normal": 301330, "heroic": 301331}


def _wave_2_bound() -> bool:
    m = re.search(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", COMMON.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


def _lock_entries() -> dict[tuple[str, str], int]:
    entries = {}
    for line in ITEM_LOCK.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit() and "retired" not in parts:
            entries[(parts[1], parts[2])] = int(parts[0])
    return entries


class WaveTwoLootTest(unittest.TestCase):
    """Sections 3 and 4 in source/items/scarlet_monastery_loot.py (the wave 2 block)."""

    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        cls.bound = _wave_2_bound()
        cls.decls = [d for d in every if d.lootid in WAVE_2_LOOTIDS]
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("sm_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and not d.removal and d.chance is None}
        cls.group_removals = {(d.lootid, d.group): d for d in cls.decls if d.removal}
        cls.copies = {d.lootid: d for d in cls.decls if d.copy_only}

    def _heroic_declared(self, name) -> bool:
        return self.bound or not WAVE_2_BOSSES[name][6]

    def _names(self, keys, doc_key):
        out = []
        for key in keys:
            decl = self.items[key]
            if decl.base:
                stock = {v: k for k, v in STOCK_BASE_2.items()}
                self.assertIn(decl.base, stock, f"{key} base {decl.base} is not a doc stock item")
                out.append(stock[decl.base])
            else:
                out.append(decl.name)
        return sorted(out)

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, _doc, keys, _token, _cut, _switch) in WAVE_2_BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                if tier == "heroic" and not self._heroic_declared(name):
                    self.assertNotIn((lootid, LIST_GROUP), self.lists, f"{name}: behind BIND_WAVE_2")
                    continue
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_items_are_the_docs_items_by_name_or_stock_entry(self):
        for name, (_n, _h, doc, keys, *_rest) in WAVE_2_BOSSES.items():
            with self.subTest(boss=name):
                self.assertEqual(self._names(keys, doc), sorted(DOC_LISTS_2[doc]))
        self.assertEqual(self._names(LAST_STAND, "Last Stand"), sorted(DOC_LISTS_2["Last Stand"]))
        for name, keys in (("Herod", CALL_TO_ARMS), ("Whitemane", TRUTH)):
            self.assertEqual(self._names(keys, name), sorted(DOC_HARD_MODE_2[name]))

    def test_list_sizes_are_the_docs_boss_list_rows(self):
        self.assertEqual({k: len(v[3]) for k, v in WAVE_2_BOSSES.items()},
                         {"Crell": 4, "Halden": 4, "Herod": 4, "Thorne": 4, "Whitemane": 4})
        self.assertEqual(len(LAST_STAND), 5)
        # the gear stage's 64 list items: 39 of wave 1's bosses, 20 here and the Last Stand's 5
        self.assertEqual(39 + sum(len(v[3]) for v in WAVE_2_BOSSES.values()) + len(LAST_STAND), 64)

    def test_the_new_bosses_have_no_stock_rows_to_replace(self):
        for name in ("Crell", "Halden", "Thorne"):
            normal = WAVE_2_BOSSES[name][0]
            self.assertEqual(self.lists[(normal, LIST_GROUP)].replaces_items, ())

    # --- the cuts --------------------------------------------------------------------------------------------------

    def test_the_approved_cuts(self):
        # Herod's Shoulder and the Raging Berserker's Helm (Plate Strength set pieces), the Scarlet Leggings (a stock
        # Scarlet set piece: they leave group 1 on both bosses, but Herod keeps them as a group 4 chance row, see
        # test_herods_scarlet_leggings_...), Whitemane's Chapeau (Cloth Spirit head): the SP "Structure" 3
        self.assertEqual(set(self.lists[(3975, LIST_GROUP)].replaces_items), {7718, 7719, 10330})
        self.assertEqual(self.lists[(3977, LIST_GROUP)].replaces_items, (7720,))
        self.assertEqual(self.group_removals[(MOGRAINE, LIST_GROUP)].replaces_items, (10330,))
        self.assertEqual(self.group_removals[(FAIRBANKS, LIST_GROUP)].replaces_items, (19507,))

    def test_cuts_are_named_only_on_normal_lootids_and_never_collide_with_the_list(self):
        for name, (normal, heroic, _doc, keys, _token, cut, _switch) in WAVE_2_BOSSES.items():
            with self.subTest(boss=name):
                stock = {self.items[key].base for key in keys if self.items[key].base}
                self.assertFalse(cut & stock)
                self.assertEqual(set(self.lists[(normal, LIST_GROUP)].replaces_items), cut)
                if (heroic, LIST_GROUP) in self.lists:
                    self.assertEqual(self.lists[(heroic, LIST_GROUP)].replaces_items, ())

    def test_mograines_group_is_emptied_and_the_stock_quest_and_cloth_rows_are_never_named(self):
        removal = self.group_removals[(MOGRAINE, LIST_GROUP)]
        self.assertIn(removal.lootid, WAVE_2_LOOTIDS)
        # the three stock entries of his group are the chest's Normal tier (item(base=)): no list on his lootids
        bases = {self.items[key].base for key in LAST_STAND if self.items[key].base}
        self.assertEqual(bases, {7726, 7723, 7724})
        self.assertFalse([k for k in self.lists if k[0] == MOGRAINE])
        named = set()
        for d in self.decls:
            named |= set(d.rows) | set(d.replaces_items)
            self.assertFalse(WORLD_DROP_REFERENCES & set(d.replaces_references), d.where)
        self.assertFalse(STOCK_KEEP & named)
        self.assertFalse([d for d in self.decls if d.row_removal or d.pool_removal])

    def test_fairbanks_group_is_emptied_for_both_difficulties_and_his_moved_items_are_not_cut_twice(self):
        removal = self.group_removals[(FAIRBANKS, LIST_GROUP)]
        self.assertEqual(removal.replaces_items, (19507,))
        # 19508 / 19509 are wave 1 list items (Vishas, Kell): item() entries, so the removal need not name them
        wave_one = {self.items[k].base for k in ("sm_branded_leather_bracers", "sm_dusty_mail_boots")}
        self.assertEqual(wave_one, {19508, 19509})
        # the heroic Fairbanks row keeps lootid 4542 (the dungeon file's override states columns only): one removal
        text = SM_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"4542: dict\(columns=_NO_BIND\)")
        self.assertFalse([k for k in self.lists if k[0] == FAIRBANKS])
        self.assertFalse([k for k in self.copies if k == FAIRBANKS])

    # --- the Zealot's Mantle and Chestguard ------------------------------------------------------------------------

    def test_the_tokens_are_group_three_of_the_heroic_lootids_only(self):
        tokens = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP}
        expected = {(WAVE_2_BOSSES[n][1], TOKEN_GROUP): WAVE_2_BOSSES[n][4] for n in ("Herod", "Whitemane")
                    if self._heroic_declared(n)}
        self.assertEqual({k: d.items for k, d in tokens.items()}, {k: (v,) for k, v in expected.items()})
        for decl in tokens.values():
            self.assertEqual((decl.tier, decl.picks, decl.loot_mode), ("heroic", 1, L.LOOT_MODE_DEFAULT))
            self.assertEqual(self.tokens[decl.items[0]].ladder.name, "vanilla_heroic_set")
        # the family is heroic-only: no normal lootid carries a token
        self.assertFalse([k for k in tokens if k[0] in {v[0] for v in WAVE_2_BOSSES.values()}])
        self.assertEqual({"zealot_token_shoulders", "zealot_token_chest"} - set(self.tokens), set())

    # --- the hard mode lists ---------------------------------------------------------------------------------------

    def test_the_hard_mode_lists_are_group_two_of_the_heroic_lootids_at_loot_mode_2(self):
        for name, keys in (("Herod", CALL_TO_ARMS), ("Whitemane", TRUTH)):
            heroic = WAVE_2_BOSSES[name][1]
            normal = WAVE_2_BOSSES[name][0]
            self.assertNotIn((normal, HARD_MODE_GROUP), self.lists)  # heroic only
            if not self.bound:
                self.assertNotIn((heroic, HARD_MODE_GROUP), self.lists)
                continue
            decl = self.lists[(heroic, HARD_MODE_GROUP)]
            self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                             (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, keys, False))
            self.assertEqual(len(decl.items), 3)
            self.assertIn((heroic, LIST_GROUP), self.lists)  # on top of the default list
            for key in keys:
                self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    def test_no_other_wave_2_group_rolls_at_loot_mode_2(self):
        modes = {k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1}
        expected = {(WAVE_2_BOSSES[n][1], HARD_MODE_GROUP) for n in ("Herod", "Whitemane")} if self.bound else set()
        self.assertEqual(modes, expected)

    # --- shape -----------------------------------------------------------------------------------------------------

    def test_no_flex_groups_no_copies_and_one_chance_row(self):
        # the only chance row is Herod's kept Scarlet Leggings (STAGE-R-2-LOOT m-1, the next test)
        self.assertEqual([d.where for d in self.decls if d.chance is not None],
                         ["loot_chance(3975, 10330, group=4)"])
        self.assertEqual(self.copies, {})
        self.assertLessEqual({k[1] for k in self.lists}, {LIST_GROUP, HARD_MODE_GROUP, TOKEN_GROUP})

    def test_herods_scarlet_leggings_stay_on_the_normal_lootid_only(self):
        # STAGE-R-2-LOOT m-1 (handoff 10): 10330 is dropped by Herod and Mograine only (live), so cutting both would
        # leave the stock Scarlet set (163) incompletable. Herod keeps it at the stock 25% as a group 4 chance row
        # on his normal lootid; the heroic lootid gets none; Mograine's stays cut.
        rows = [d for d in self.decls if d.chance is not None]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row.lootid, row.item_entry, row.chance, row.group, row.loot_mode),
                         (3975, 10330, 25.0, 4, L.LOOT_MODE_DEFAULT))
        self.assertEqual(row.replaces_items, ())
        self.assertNotIn(10330, {self.items[k].base for k in WAVE_2_BOSSES["Herod"][3]})
        # no declaration of any heroic lootid or of Mograine / Whitemane names it as a kept row
        self.assertFalse([d for d in self.decls if d.chance is not None and d.lootid != 3975])
        self.assertEqual(self.group_removals[(MOGRAINE, LIST_GROUP)].replaces_items, (10330,))

    def test_declaration_counts(self):
        # 5 bosses' normal lists, the 3 new bosses' heroic lists and (bound) Herod's and Whitemane's heroic list,
        # token and hard mode group; Mograine's and Fairbanks's removals
        expected = 5 + 3 + (2 * 3 if self.bound else 0)
        self.assertEqual(len(self.lists), expected)
        self.assertEqual(len(self.group_removals), 2)
        self.assertEqual(len(self.decls), expected + 2 + 1)  # + Herod's Scarlet Leggings chance row

    def test_the_lootids_are_the_wave_two_ones_and_the_normal_templates_name_them(self):
        self.assertEqual({d.lootid for d in self.decls} - WAVE_2_LOOTIDS, set())
        npcs = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
        for name, file in (("Crell", "crell.py"), ("Halden", "halden.py"), ("Thorne", "thorne.py")):
            text = (npcs / file).read_text(encoding="utf-8")
            self.assertRegex(text, rf"'lootid': {WAVE_2_BOSSES[name][0]}\b", name)

    # --- one item, one row -----------------------------------------------------------------------------------------

    def test_no_loot_table_lists_an_item_twice(self):
        by_lootid: dict[int, list[str]] = {}
        for (lootid, _group), decl in self.lists.items():
            by_lootid.setdefault(lootid, []).extend(decl.items)
        for lootid, keys in by_lootid.items():
            with self.subTest(lootid=lootid):
                self.assertEqual(len(keys), len(set(keys)), keys)
                bases = [self.items[k].base for k in keys if k in self.items and self.items[k].base]
                self.assertEqual(len(bases), len(set(bases)), bases)
                self.assertFalse(STOCK_KEEP & set(bases))

    def test_no_item_drops_from_two_bosses_or_a_boss_and_the_chest(self):
        seen: dict[str, str] = {}
        for name, (_n, _h, _d, keys, *_rest) in WAVE_2_BOSSES.items():
            for key in keys:
                self.assertNotIn(key, seen, f"{key} on {name} and {seen.get(key)}")
                seen[key] = name
        for key in LAST_STAND:
            self.assertNotIn(key, seen, f"{key} on the chest and {seen.get(key)}")
            seen[key] = "chest"
        for keys in (CALL_TO_ARMS, TRUTH):
            self.assertFalse(set(seen) & keys)
        self.assertFalse(CALL_TO_ARMS & TRUTH)
        # nothing of wave 1's bosses either
        wave_one = set().union(*(v[3] for v in BOSSES.values())) | DESECRATION | HERESY
        self.assertFalse(wave_one & set(seen))

    def test_the_replaced_stock_entries_are_not_any_boss_lists_stock_entry(self):
        cuts = set().union(*(v[5] for v in WAVE_2_BOSSES.values())) | {19507}
        bases = {self.items[k].base for v in WAVE_2_BOSSES.values() for k in v[3] if self.items[k].base}
        bases |= {self.items[k].base for k in LAST_STAND if self.items[k].base}
        self.assertFalse(cuts & bases)

    def test_list_items_are_on_the_dungeon_ladder_and_every_declared_tier_exists(self):
        for decl in self.decls:
            if not decl.listing or decl.removal:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                if decl.tier in ("normal", "heroic") and key in self.items:
                    self.assertEqual(ladder.name, "vanilla_dungeon", key)

    def test_the_64_gear_stage_list_items_are_all_dropped_somewhere(self):
        listed = set().union(*(v[3] for v in BOSSES.values()))
        listed |= set().union(*(v[3] for v in WAVE_2_BOSSES.values())) | LAST_STAND
        self.assertEqual(len(listed), 64)
        gear_stage = {k for k, d in self.items.items() if d.ladder.name == "vanilla_dungeon"}
        self.assertEqual(listed, gear_stage)

    def test_the_heroic_lootids_follow_the_dungeon_file(self):
        text = SM_DUNGEON.read_text(encoding="utf-8")
        for name, (normal, heroic, *_rest) in WAVE_2_BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in scarlet_monastery.py")
        # Mograine's heroic body states no heroic lootid: it shares 3976 (no corpse, his real death drops cloth)
        self.assertRegex(text, r"3976: _boss\(250_000\)")

    def test_every_heroic_boss_with_its_own_lootid_is_declared(self):
        # lib/loot_tables.py `_check_creatures`: a heroic boss on its own lootid with no declaration drops nothing
        declared = {d.lootid for d in self.decls}
        for name, (_n, heroic, *_rest) in WAVE_2_BOSSES.items():
            if self._heroic_declared(name):
                self.assertIn(heroic, declared, name)


class ChestRevTest(unittest.TestCase):
    """rev_loot_wave_2_scarlet_monastery.sql: the Chest of the Last Stand (GO 301330 normal / 301331 heroic)."""

    @classmethod
    def setUpClass(cls):
        cls.text = CHEST_REV.read_text(encoding="utf-8")
        cls.lock = _lock_entries()
        pattern = re.compile(r"^\((\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), '(.*)'\)[,;]$", re.M)
        cls.rows: dict[int, list[dict]] = {}
        for m in pattern.finditer(cls.text):
            entry, item, ref, chance, quest, mode, group, mn, mx = map(int, m.groups()[:9])
            cls.rows.setdefault(entry, []).append(dict(item=item, ref=ref, chance=chance, quest=quest, mode=mode,
                                                       group=group, min=mn, max=mx, comment=m.group(10)))

    def test_each_chest_is_the_approved_list_at_its_tier(self):
        for tier, chest in CHESTS.items():
            with self.subTest(chest=chest):
                items = [r["item"] for r in self.rows[chest]]
                self.assertEqual(sorted(items), sorted(self.lock[(key, tier)] for key in LAST_STAND))
                self.assertEqual(len(items), 5)

    def test_one_item_per_kill_equal_chance_one_group_default_loot_mode(self):
        for chest, rows in self.rows.items():
            for r in rows:
                self.assertEqual((r["ref"], r["chance"], r["quest"], r["mode"], r["group"], r["min"], r["max"]),
                                 (0, 0, 0, 1, 1, 1, 1), (chest, r))

    def test_the_stock_entries_are_the_normal_tier(self):
        # the three stock items are the Normal tier (item(base=)); the two new ones have their own lock entries
        normal = {r["item"] for r in self.rows[CHESTS["normal"]]}
        self.assertTrue({7726, 7723, 7724} <= normal)
        heroic = {r["item"] for r in self.rows[CHESTS["heroic"]]}
        self.assertFalse(normal & heroic)

    def test_the_entries_are_real_templates_of_the_two_chests(self):
        self.assertEqual(sorted(self.rows), [301330, 301331])
        d13 = D13_REV.read_text(encoding="utf-8")
        for chest in CHESTS.values():
            self.assertIn(f"({chest}, 3, 1387, 'Chest of the Last Stand'", d13)
            self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301330, 301331);", self.text)
        # D13's placeholder rows are replaced: the rev sorts after D13's and deletes the entries first
        self.assertGreater(CHEST_REV.name, D13_REV.name)
        self.assertLess(self.text.index("DELETE FROM `gameobject_loot_template`"), self.text.index("INSERT INTO"))

    def test_no_chest_lists_an_item_twice(self):
        # gameobject_loot_template is keyed (Entry, Item): a duplicate fails db-import partway (BRD LESSONS)
        for entry, rows in self.rows.items():
            items = [row["item"] for row in rows]
            self.assertEqual(len(items), len(set(items)), entry)

    def test_the_chest_has_no_cloth_and_no_item_of_the_creature_lists(self):
        chest_items = {r["item"] for rows in self.rows.values() for r in rows}
        self.assertFalse(chest_items & {SILK_CLOTH, HEART_OF_ZEAL, 14047})
        for key, tier in ((k, t) for k in LAST_STAND for t in ("normal", "heroic")):
            self.assertIn(self.lock[(key, tier)], chest_items)

    def test_every_row_has_the_loot_mode_a_chest_can_use(self):
        for entry, rows in self.rows.items():
            for row in rows:
                self.assertIn(row["mode"], (1, 2, 3), (entry, row))

    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for number, line in enumerate(self.text.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)
        self.assertTrue(self.text.endswith("\n"))


class HeroicLootidTest(unittest.TestCase):
    """The heroic bodies' own lootids: the dungeon file's `_boss(...)` overrides, the lock's predictions, the flag."""

    def test_the_dungeon_file_gives_every_wave_1_boss_its_own_heroic_lootid(self):
        text = SM_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")
        for name, (normal, heroic, *_rest) in BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in scarlet_monastery.py")
        self.assertIsNotNone(re.search(rf"^\s*{AZSHIR[0]}: _boss\([\d_]+, {AZSHIR[1]}[,)]", text, re.M))

    def test_every_heroic_boss_with_its_own_lootid_is_declared(self):
        # lib/loot_tables.py `_check_creatures`: a heroic boss on its own lootid with no declaration drops nothing
        _, mine = _declarations()
        declared = {d.lootid for d in mine}
        for name, (_n, heroic, *_rest) in BOSSES.items():
            self.assertIn(heroic, declared, name)
        self.assertIn(AZSHIR[1], declared)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/scarlet_monastery.py `_boss(...)`, BOSS_LISTS in
        source/items/scarlet_monastery_loot.py, BOSSES above): the first write run mints the heroic entries from 310419
        in normal-entry order (test_scarlet_monastery_heroic.py pins the order). If another branch appended lines to
        source/world/heroic_ids.lock first, the mint shifts and every heroic lootid points at another creature's
        heroic entry: this test fails loudly BEFORE the write run."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        fix = (
            "The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic entry "
            "of each boss from source/world/heroic_ids.lock (or, before the write run, 310419 + the boss's index in "
            "normal-entry order after the lock's last line) and update ALL THREE places: the `_boss(..., <lootid>)` "
            "overrides in source/world/dungeons/scarlet_monastery.py, BOSS_LISTS (and THALNOS_HEROIC, DOAN_HEROIC, "
            "AZSHIR_HEROIC) in source/items/scarlet_monastery_loot.py and BOSSES in this test (and HEROIC_LOOTID in "
            "test_scarlet_monastery_heroic.py); then rerun lib/test_scarlet_monastery_heroic.py and this file."
        )
        pairs = {v[0]: v[1] for v in BOSSES.values()}
        pairs[AZSHIR[0]] = AZSHIR[1]
        ours = {normal: lock.pairs[normal] for normal in pairs if normal in lock.pairs}
        if ours:  # after the write run: the lock is the truth
            for normal, heroic in pairs.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"creature {normal}: lock says {ours[normal]}. {fix}")
        else:  # before it: nothing of ours is in the lock and the next free id is the first predicted one
            taken = sorted(h for h in lock.pairs.values() if h >= 310419)
            self.assertEqual(taken, [], f"the lock already holds ids from 310419 ({taken[:3]}...) but none of the "
                                        f"Scarlet Monastery bosses. {fix}")
            foreign_top = max((h for h in lock.pairs.values() if h < 310419), default=0)
            self.assertEqual(foreign_top, 310418, f"the lock's last id below the first predicted one is "
                                                  f"{foreign_top}, not 310418: lines were added or removed. {fix}")


class StyleTest(unittest.TestCase):
    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for path in (LOOT_FILE, Path(__file__)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{number}")
                self.assertEqual(line, line.rstrip(), f"{path.name}:{number} trailing whitespace")


if __name__ == "__main__":
    unittest.main()
