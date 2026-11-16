"""
Blackrock Spire build, WP-L-1 and WP-L-2: the real declarations in source/items/blackrock_spire_loot.py (item keys from
blackrock_spire.py and its hard mode effects, tokens from molten_set.py). LowerSpireLootTest is wave 1's (L-1),
UpperSpireLootTest wave 2's (L-2: Emberseer, Solakar, Rend, Gyth, the Beast, Drakkisath).

The Lower Spire bosses' lists (Omokk, Vosh'gajin, Voone, Smolderweb, Urok, Zigris, Halycon and Gizrul, Wyrmthalak) at
the Normal tier on the stock lootids and the Heroic tier on the heroic bodies' own lootids, the Molten Gloves and
Shoulders, Wyrmthalak's hard mode list, the flex second-roll copies (LootMode 4, the hard mode list at 8) and the cut
stock rows. The rows themselves (and their rules and rendering) are test_loot_tables.py's; the real plan (tiers, the
live stock groups) is generate.py --check's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_loot.py
"""

from __future__ import annotations

import ast
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

BRS_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_spire.py"

LIST_GROUP, HARD_MODE_GROUP, TOKEN_GROUP = 1, 2, 3
FLEX_LIST_GROUP, FLEX_HARD_MODE_GROUP, FLEX_TOKEN_GROUP = 11, 12, 13
FLEX_MODE, FLEX_HARD_MODE_MODE = 4, 8  # DungeonKit::Flex::kLootModeFlex / kLootModeFlexHardMode

HALYCON_GIZRUL = {
    "brs_slashclaw_bracers", "brs_halycons_spiked_collar", "brs_rhombeard_protector", "brs_wolfshear_leggings",
    "brs_bleak_howler_armguards", "brs_packleaders_hide_belt",
}

# name -> (normal lootid, heroic lootid, the approved list (dungeon-loot-vanilla.md, Blackrock Spire), the Molten token
# key, the stock group 1 rows the list replaces)
BOSSES = {
    "Omokk": (9196, 310199, {"brs_fist_of_omokk", "brs_tressermane_leggings", "brs_skyshroud_leggings"},
              None, {13166, 13168, 16670}),
    "Vosh'gajin": (9236, 310209, {"brs_funeral_cuffs", "brs_blackcrow", "brs_riphook", "brs_totem_of_hexed_blood"},
                   None, {13255, 13257, 16712}),
    "Voone": (9237, 310210, {"brs_keris_of_zulserak", "brs_talisman_of_evasion", "brs_brazecore_armguards",
                             "brs_flightblade_throwing_axe", "brs_war_masters_hatchet"},
              "molten_token_hands", {16676, 22231}),
    "Smolderweb": (10596, 310276, {"brs_venomspitter", "brs_smolderwebs_eye", "brs_smolderweb_silk_sash"},
                   None, {13244, 16715}),
    "Urok": (10584, 310275, {"brs_rosewine_circle", "brs_marksmans_girdle", "brs_shardlinked_coif"},
             None, {13258, 13259}),
    "Zigris": (9736, 310240, {"brs_cloudrunner_girdle", "brs_quartermasters_blunderbuss",
                              "brs_supply_sergeants_girdle"},
               None, {13253, 16716}),
    "Halycon": (10220, 310250, HALYCON_GIZRUL, None, {13210, 22313}),
    "Gizrul": (10268, 310256, HALYCON_GIZRUL, None, {16718}),
    "Wyrmthalak": (9568, 310228, {"brs_trindlehaven_staff", "brs_relentless_scythe", "brs_chillpike",
                                  "brs_heart_of_wyrmthalak", "brs_mark_of_the_dragon_lord",
                                  "brs_heart_of_the_scale"},
                   "molten_token_shoulders", {13162, 16679}),
}
WYRMTHALAK_HARD_MODE = {"brs_bloodaxe_war_horn", "brs_ward_of_the_three_tribes", "brs_shardstaff_of_stolen_power"}
# The Upper Spire's 35 list items and 3 hard mode items (wave 2, L-2's)
UPPER_SPIRE = {
    "brs_wildfire_cape", "brs_emberfury_talisman", "brs_helm_of_the_bound_flame", "brs_incarcerators_wand",
    "brs_dustfeather_sash", "brs_crystallized_girdle", "brs_feralsurge_girdle", "brs_flamewreath_legplates",
    "brs_blackhand_doomsaw", "brs_eye_of_rend", "brs_felstriker", "brs_warmaster_legguards",
    "brs_battleborn_armbraces", "brs_dalrends_sacred_charge", "brs_dalrends_tribal_guardian", "brs_gyths_skull",
    "brs_dragoneye_coif", "brs_tribal_war_feathers", "brs_finkles_skinner", "brs_blademaster_leggings",
    "brs_tristam_legguards", "brs_blackmist_armguards", "brs_bloodmoon_cloak", "brs_seeping_willow",
    "brs_idol_of_the_core_hound", "brs_blackblade_of_shahram", "brs_draconian_deflector", "brs_painweaver_band",
    "brs_tooth_of_gnarr", "brs_brigam_girdle", "brs_tome_of_the_lost", "brs_spellweavers_turban",
    "brs_draconic_infused_emblem", "brs_shadow_prowlers_cloak", "brs_libram_of_the_dragon_guard",
}
DRAKKISATH_HARD_MODE = {"brs_trophy_of_the_champion", "brs_orders_of_the_general", "brs_the_humbler"}
# The stock Tier 0 pieces of the Lower Spire bosses (sets 181-189 era Tier 0, item_template entries)
TIER_0_PIECES = {16670, 16712, 16676, 16715, 16716, 16718, 16679}
TOKEN_SLOT = {"molten_token_hands": (10,), "molten_token_shoulders": (3,)}  # InventoryTypes
# lootid -> (the group 0 rows that go)
GROUP_0_CUTS = {
    9196: {12534},  # Omokk's Head
    9236: {12654},  # Doomshot
    9237: {13175, 28972},  # Voone's Twitchbow, the Flightblade Throwing Axe's 100% row
    9568: {13143, 13148, 13164},  # Mark of the Dragon Lord, Chillpike, Heart of the Scale
}

NORMAL_LOOTIDS = {name: v[0] for name, v in BOSSES.items()}
HEROIC_LOOTIDS = {name: v[1] for name, v in BOSSES.items()}
ALL_LOOTIDS = set(NORMAL_LOOTIDS.values()) | set(HEROIC_LOOTIDS.values())

# --- wave 2: the Upper Spire (L-2) ----------------------------------------------------------------------------------

REND_GYTH = {
    "brs_blackhand_doomsaw", "brs_eye_of_rend", "brs_felstriker", "brs_warmaster_legguards",
    "brs_battleborn_armbraces", "brs_dalrends_sacred_charge", "brs_dalrends_tribal_guardian", "brs_gyths_skull",
    "brs_dragoneye_coif", "brs_tribal_war_feathers",
}
BEAST = {
    "brs_finkles_skinner", "brs_blademaster_leggings", "brs_tristam_legguards", "brs_blackmist_armguards",
    "brs_bloodmoon_cloak", "brs_seeping_willow", "brs_idol_of_the_core_hound",
}
DRAKKISATH = {
    "brs_blackblade_of_shahram", "brs_draconian_deflector", "brs_painweaver_band", "brs_tooth_of_gnarr",
    "brs_brigam_girdle", "brs_tome_of_the_lost", "brs_spellweavers_turban", "brs_draconic_infused_emblem",
    "brs_shadow_prowlers_cloak", "brs_libram_of_the_dragon_guard",
}
# name -> (normal lootid, heroic lootid, the approved list, the Molten token key, the stock group 1 rows the list
# replaces, the stock pool references it replaces, picks, the four pool ids: normal, heroic, flex normal, flex heroic)
UPPER_BOSSES = {
    "Emberseer": (9816, 310241, {"brs_wildfire_cape", "brs_emberfury_talisman", "brs_helm_of_the_bound_flame",
                                 "brs_incarcerators_wand"},
                  None, {12926, 12927, 16672}, set(), 1, None),
    "Solakar": (10264, 310255, {"brs_dustfeather_sash", "brs_crystallized_girdle", "brs_feralsurge_girdle",
                                "brs_flamewreath_legplates"},
                None, {12603, 12609, 16695}, set(), 1, None),
    "Rend": (10429, 310270, REND_GYTH, "molten_token_feet", set(), {35022}, 1, None),
    "Gyth": (10339, 310262, REND_GYTH, None, {16669, 22225}, set(), 1, None),
    "Beast": (10430, 310271, BEAST, None, set(), {35023}, 2, (1700011, 1700012, 1700013, 1700014)),
    "Drakkisath": (10363, 310263, DRAKKISATH, "molten_token_chest",
                   {16666, 16674, 16688, 16690, 16700, 16706, 16721, 16726, 16730}, set(), 2,
                   (1700015, 1700016, 1700017, 1700018)),
}
DRAKKISATH_HARD_MODE_LOOTID = 310263
UPPER_NORMAL_LOOTIDS = {name: v[0] for name, v in UPPER_BOSSES.items()}
UPPER_HEROIC_LOOTIDS = {name: v[1] for name, v in UPPER_BOSSES.items()}
UPPER_LOOTIDS = set(UPPER_NORMAL_LOOTIDS.values()) | set(UPPER_HEROIC_LOOTIDS.values())
ALL_BOSSES = {**BOSSES, **UPPER_BOSSES}
STOCK_POOLS = {35022, 35023, 35025}
TOKEN_SLOT_UPPER = {"molten_token_feet": (8,), "molten_token_chest": (5, 20)}  # InventoryTypes
# The quest, recipe, pool and reagent rows of the six Upper Spire lootids that stay (Head of Rend Blackhand, Blackrock
# Bracer, Black Dragonspawn Eye, Blood of the Black Dragon Champion, Eye of the Emberseer, Ember of Emberseer, Core of
# Elements, Tablet of Flame Shock VI, Schematic: Hyper-Radiant Flame Reflector, Chromatic Carapace, Recipe: Flask of
# Chromatic Resistance, Ace of Beasts, Book of Ferocious Bite V, Recipe: Flask of the Titans, runecloth, coal, pitch)
UPPER_KEEP = {12630, 22138, 16786, 16663, 17322, 21988, 22527, 23320, 18657, 12871, 13522, 19227, 24101, 13519,
              14047, 3857, 4787, 4460}
BOSS_SCRIPT_DIR = Path(TOOL_ROOT).parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "blackrock_spire_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


class LowerSpireLootTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        # wave 1's declarations (the Upper Spire's are UpperSpireLootTest's)
        cls.decls = [d for d in every if d.lootid in ALL_LOOTIDS]
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("brs_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and d.chance is None and not d.removal}
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, keys, _token, _cut) in BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes(self):
        sizes = {name: len(v[2]) for name, v in BOSSES.items()}
        self.assertEqual(sizes, {"Omokk": 3, "Vosh'gajin": 4, "Voone": 5, "Smolderweb": 3, "Urok": 3, "Zigris": 3,
                                 "Halycon": 6, "Gizrul": 6, "Wyrmthalak": 6})

    def test_every_lower_spire_item_has_a_drop_and_the_split_with_the_upper_spire_is_exact(self):
        listed = set().union(*(v[2] for v in BOSSES.values()))
        self.assertEqual(len(listed), 33)
        self.assertEqual(len(UPPER_SPIRE), 35)
        self.assertFalse(listed & UPPER_SPIRE)
        self.assertFalse(listed & (WYRMTHALAK_HARD_MODE | DRAKKISATH_HARD_MODE))
        # the 68 list items + 6 hard mode items of the gear stage, nothing else
        self.assertEqual(listed | UPPER_SPIRE | WYRMTHALAK_HARD_MODE | DRAKKISATH_HARD_MODE, set(self.items))
        self.assertEqual(len(self.items), 74)

    def test_halycon_and_gizrul_share_one_list_and_each_wolf_drops_one_item_of_it(self):
        # SP Loot, Structure 3: two items per kill of the pair, "one per wolf, stock": the wolves keep their own
        # lootids and both declare the one six-item list at one pick (no reference pool: the two rolls cannot be
        # distinct across two corpses)
        for name in ("Halycon", "Gizrul"):
            for lootid in (NORMAL_LOOTIDS[name], HEROIC_LOOTIDS[name]):
                decl = self.lists[(lootid, LIST_GROUP)]
                self.assertEqual((set(decl.items), decl.picks, decl.reference), (HALYCON_GIZRUL, 1, None))
        self.assertEqual(self.lists[(10220, LIST_GROUP)].items, self.lists[(10268, LIST_GROUP)].items)

    def test_no_declaration_uses_a_reference_pool(self):
        self.assertEqual([d for d in self.decls if d.reference is not None], [])

    # --- the heroic lootids ----------------------------------------------------------------------------------------

    def test_heroic_lootids_are_the_bosses_own_heroic_entries(self):
        text = BRS_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")
        for name, (normal, heroic, *_rest) in BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in blackrock_spire.py")
        lootids = {d.lootid for d in self.lists.values()}
        self.assertEqual(lootids, ALL_LOOTIDS)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/blackrock_spire.py `_boss(...)`, BOSS_LISTS in
        source/items/blackrock_spire_loot.py, BOSSES above): the first write run mints the BRS heroic entries
        310195 on in normal-entry order (test_blackrock_spire_heroic.py::test_the_predicted_lock_lines pins the
        order). If another branch appended lines to source/world/heroic_ids.lock first, the mint shifts and every
        heroic lootid below points at another creature's heroic entry: this test fails loudly BEFORE the write run.
        """
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        # all fifteen Blackrock Spire bosses (the Upper Spire's six are L-2's: UPPER_BOSSES)
        ours = {v[0]: lock.pairs[v[0]] for v in ALL_BOSSES.values() if v[0] in lock.pairs}
        fix = (
            "The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic entry "
            "of each boss from source/world/heroic_ids.lock (or, before the write run, 310195 + the boss's index in "
            "normal-entry order after the lock's last line) and update ALL THREE places: the `_boss(..., <lootid>)` "
            "overrides in source/world/dungeons/blackrock_spire.py, BOSS_LISTS in source/items/"
            "blackrock_spire_loot.py and BOSSES in this test (and HEROIC_LOOTID in test_blackrock_spire_heroic.py); "
            "then rerun lib/test_blackrock_spire_heroic.py and this file."
        )
        if ours:  # after the write run: the lock is the truth
            for name, (normal, heroic, *_rest) in ALL_BOSSES.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"{name} ({normal}): lock says {ours[normal]}. {fix}")
        else:  # before it: nothing else may have taken ids below the predicted first one
            foreign_top = max((h for h in lock.pairs.values() if h < 310195), default=0)
            taken = sorted(h for h in lock.pairs.values() if h >= 310195)
            self.assertEqual(taken, [], f"the lock already holds ids from 310195 ({taken[:3]}...) but none of the "
                                        f"Blackrock Spire bosses. {fix}")

            self.assertEqual(foreign_top, 310194, f"the lock's last id below the first predicted one is {foreign_top}, "
                                                  f"not 310194: lines were added or removed. {fix}")

    # --- the cuts --------------------------------------------------------------------------------------------------

    def test_the_cut_stock_group_one_rows_are_named_and_only_on_the_normal_lootids(self):
        for name, (normal, heroic, keys, _token, cut) in BOSSES.items():
            with self.subTest(boss=name):
                decl = self.lists[(normal, LIST_GROUP)]
                self.assertEqual(set(decl.replaces_items), cut)
                self.assertEqual(decl.replaces_references, ())
                other = self.lists[(heroic, LIST_GROUP)]
                self.assertEqual((other.replaces_items, other.replaces_references), ((), ()))
                # a replaced row is never a list item's own stock entry
                stock = {self.items[key].base for key in keys if self.items[key].base}
                self.assertFalse(cut & stock)
        self.assertEqual(TIER_0_PIECES & set().union(*(v[4] for v in BOSSES.values())), TIER_0_PIECES)

    def test_the_flex_and_token_groups_name_no_replaced_rows(self):
        for (lootid, group), decl in self.lists.items():
            if group != LIST_GROUP:
                self.assertEqual((decl.replaces_items, decl.replaces_references), ((), ()), (lootid, group))

    def test_group_zero_cuts_omokks_head_doomshot_twitchbow_axe_row_and_wyrmthalaks_three_rares(self):
        self.assertEqual({lootid: set(d.rows) for (lootid, group), d in self.row_removals.items() if group == 0},
                         GROUP_0_CUTS)
        self.assertEqual({group for _lootid, group in self.row_removals}, {0})
        self.assertFalse([d for d in self.row_removals.values() if d.ref_rows])
        self.assertFalse({lootid for lootid, _g in self.row_removals} & set(HEROIC_LOOTIDS.values()))
        # the removed rows of Voone and Wyrmthalak are on their lists (or cut), so they would drop twice otherwise
        self.assertIn("brs_flightblade_throwing_axe", BOSSES["Voone"][2])
        self.assertTrue({"brs_chillpike", "brs_mark_of_the_dragon_lord", "brs_heart_of_the_scale"}
                        <= BOSSES["Wyrmthalak"][2])

    def test_the_stock_quest_and_reagent_rows_are_never_named(self):
        # Gemstones, Snakestone, Blackrock Bracer, Warosh's Mojo, Ogre Warbeads, Black Dragonspawn Eye, Unadorned Seal,
        # runecloth, Dark Iron Scraps, potions, the Smolderweb reagents stay
        keep = {12336, 12335, 12337, 13352, 22138, 12712, 21982, 16786, 12219, 14047, 22528, 13444, 13446, 12780,
                14227, 12205, 4337, 10285, 1074, 4585, 18784}
        named = set()
        for d in self.decls:
            named |= set(d.rows) | set(d.replaces_items)
        self.assertFalse(keep & named)

    # --- the Molten tokens -----------------------------------------------------------------------------------------

    def test_molten_gloves_and_shoulders_drop_at_the_kills_tier_on_voone_and_wyrmthalak_only(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP}
        self.assertEqual(sorted(by_key), sorted([(9237, 3), (310210, 3), (9568, 3), (310228, 3)]))
        for name, (normal, heroic, _keys, token, _cut) in BOSSES.items():
            if token is None:
                self.assertNotIn((normal, TOKEN_GROUP), by_key, name)
                continue
            self.assertIn(token, self.tokens)
            self.assertEqual(self.tokens[token].slots, TOKEN_SLOT[token])
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                decl = by_key[(lootid, TOKEN_GROUP)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode), ((token,), tier, 1, 1), name)
        self.assertEqual(by_key[(9237, 3)].items, ("molten_token_hands",))
        self.assertEqual(by_key[(9568, 3)].items, ("molten_token_shoulders",))

    # --- the hard mode list ----------------------------------------------------------------------------------------

    def test_wyrmthalaks_hard_mode_is_group_two_of_his_heroic_lootid_only_at_loot_mode_2(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == HARD_MODE_GROUP}
        self.assertEqual(sorted(by_key), [(310228, 2)])
        decl = by_key[(310228, 2)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, WYRMTHALAK_HARD_MODE))
        self.assertEqual(len(decl.items), 3)
        # every other group at LootMode 2 is none: a hard mode kill only adds the list
        self.assertFalse([k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1
                          and k != (310228, 2)])

    # --- the flex second roll --------------------------------------------------------------------------------------

    def test_every_list_has_a_copy_at_loot_mode_4_on_both_lootids(self):
        for name, (normal, heroic, keys, _token, _cut) in BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    copy = self.lists[(lootid, FLEX_LIST_GROUP)]
                    base = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((copy.items, copy.tier, copy.picks, copy.reference, copy.loot_mode),
                                     (base.items, tier, 1, None, FLEX_MODE))

    def test_every_token_has_a_copy_at_loot_mode_4_on_both_lootids(self):
        copies = {k: d for k, d in self.lists.items() if k[1] == FLEX_TOKEN_GROUP}
        self.assertEqual(sorted(copies), sorted([(9237, 13), (310210, 13), (9568, 13), (310228, 13)]))
        for (lootid, _group), copy in copies.items():
            base = self.lists[(lootid, TOKEN_GROUP)]
            self.assertEqual((copy.items, copy.tier, copy.loot_mode), (base.items, base.tier, FLEX_MODE), lootid)

    def test_the_hard_mode_list_has_a_copy_at_loot_mode_8_on_the_heroic_lootid_only(self):
        copies = {k: d for k, d in self.lists.items() if k[1] == FLEX_HARD_MODE_GROUP}
        self.assertEqual(sorted(copies), [(310228, 12)])
        copy, base = copies[(310228, 12)], self.lists[(310228, HARD_MODE_GROUP)]
        self.assertEqual((copy.items, copy.tier, copy.picks, copy.loot_mode),
                         (base.items, "heroic_hm", 1, FLEX_HARD_MODE_MODE))

    def test_loot_modes_are_only_1_2_4_and_8_and_never_mixed_with_the_default_bit(self):
        for key, decl in self.lists.items():
            with self.subTest(group=key):
                expected = {LIST_GROUP: 1, TOKEN_GROUP: 1, HARD_MODE_GROUP: 2, FLEX_LIST_GROUP: 4,
                            FLEX_TOKEN_GROUP: 4, FLEX_HARD_MODE_GROUP: 8}[key[1]]
                self.assertEqual(decl.loot_mode, expected)
        # the flex bits are the kit's (DungeonKitFlexRules.h kLootModeFlex / kLootModeFlexHardMode)
        kit = Path(TOOL_ROOT).parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "Kit" / "DungeonKitFlexRules.h"
        if kit.is_file():
            text = kit.read_text(encoding="utf-8")
            self.assertRegex(text, r"kLootModeFlex\s*=\s*0x04")
            self.assertRegex(text, r"kLootModeFlexHardMode\s*=\s*0x08")

    def test_groups_are_distinct_from_the_stock_groups_that_stay(self):
        # the stock lootids hold groups 0 (the pools, quest items and reagents) and 1 (the list); nothing declared
        # is group 0, and the copies sit in groups of their own (a group is a table key)
        groups = {group for _lootid, group in self.lists}
        self.assertEqual(groups, {1, 2, 3, 11, 12, 13})
        self.assertNotIn(0, groups)
        self.assertEqual(len({(d.lootid, d.group) for d in self.decls if d.listing}),
                         len([d for d in self.decls if d.listing]))

    def test_declaration_counts(self):
        # 9 bosses x 2 lootids x (list + flex list) + 2 tokens x 2 lootids x 2 + the hard mode pair + 4 cut groups
        self.assertEqual(len(self.lists), 9 * 2 * 2 + 2 * 2 * 2 + 2)
        self.assertEqual(len(self.row_removals), 4)
        self.assertEqual(len(self.decls), len(self.lists) + len(self.row_removals))

    # --- the items the lists name ----------------------------------------------------------------------------------

    def test_list_items_are_on_the_dungeon_ladder_and_hard_mode_items_on_the_hard_mode_ladder(self):
        for keys in [v[2] for v in BOSSES.values()]:
            for key in keys:
                self.assertEqual(self.items[key].ladder.name, "vanilla_dungeon", key)
        for key in WYRMTHALAK_HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)
        # the ladder tiers the declarations name exist on each ladder
        for decl in self.decls:
            if not decl.listing:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))


class UpperSpireLootTest(unittest.TestCase):
    """WP-L-2: Emberseer, Solakar, Rend, Gyth, the Beast and Drakkisath."""

    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        cls.every = every
        cls.decls = [d for d in every if d.lootid in UPPER_LOOTIDS or d.pool_removal]
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("brs_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls if d.listing and d.chance is None and not d.removal}
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.pool_removals = {d.reference: d for d in cls.decls if d.pool_removal}

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, keys, _token, _cut, _pools, picks, refs) in UPPER_BOSSES.items():
            for index, (lootid, tier) in enumerate(((normal, "normal"), (heroic, "heroic"))):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, picks, refs[index] if refs else None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), keys)
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(keys <= set(self.items))

    def test_list_sizes_and_the_35_item_split_with_the_lower_spire(self):
        sizes = {name: len(v[2]) for name, v in UPPER_BOSSES.items()}
        self.assertEqual(sizes, {"Emberseer": 4, "Solakar": 4, "Rend": 10, "Gyth": 10, "Beast": 7, "Drakkisath": 10})
        listed = set().union(*(v[2] for v in UPPER_BOSSES.values()))
        self.assertEqual(len(listed), 35)
        self.assertEqual(listed, UPPER_SPIRE)
        self.assertFalse(listed & set().union(*(v[2] for v in BOSSES.values())))

    def test_rend_and_gyth_each_drop_one_item_of_one_shared_list(self):
        # SP Loot, Structure 3: two items per kill of the pair, as Halycon and Gizrul: two lootids, one pick each (no
        # reference pool: two corpses cannot roll distinct items), the one ten item list on both
        for name in ("Rend", "Gyth"):
            for lootid in (UPPER_NORMAL_LOOTIDS[name], UPPER_HEROIC_LOOTIDS[name]):
                decl = self.lists[(lootid, LIST_GROUP)]
                self.assertEqual((set(decl.items), decl.picks, decl.reference), (REND_GYTH, 1, None))
        self.assertEqual(self.lists[(10429, LIST_GROUP)].items, self.lists[(10339, LIST_GROUP)].items)

    def test_the_beast_and_drakkisath_drop_two_distinct_items_from_pools_of_their_own(self):
        refs = [d.reference for d in self.decls if d.listing and d.reference is not None]
        # 2 bosses x (list + flex list) x 2 lootids, every pool its own, in the loot_reference block after wave 1
        self.assertEqual(sorted(refs), list(range(1700011, 1700019)))
        for name in ("Beast", "Drakkisath"):
            decl = self.lists[(UPPER_NORMAL_LOOTIDS[name], LIST_GROUP)]
            self.assertEqual(decl.picks, 2)
            self.assertLessEqual(decl.picks, len(decl.items))
        for name in ("Emberseer", "Solakar", "Rend", "Gyth"):
            for lootid in (UPPER_NORMAL_LOOTIDS[name], UPPER_HEROIC_LOOTIDS[name]):
                for group in (LIST_GROUP, FLEX_LIST_GROUP):
                    self.assertIsNone(self.lists[(lootid, group)].reference, (name, lootid, group))

    def test_the_pool_ids_are_in_the_reserved_block_and_clear_of_wave_1(self):
        ids_text = (TOOL_ROOT / "source" / "ids.yaml").read_text(encoding="utf-8")
        m = re.search(r"(?m)^loot_reference:\s*\n\s+start:\s*(\d+)\s*\n\s+end:\s*(\d+)", ids_text)
        self.assertIsNotNone(m)
        low, high = int(m.group(1)), int(m.group(2))
        for d in self.decls:
            if d.reference is not None and d.listing:
                self.assertTrue(low <= d.reference <= high, d.reference)
        wave_1 = {d.reference for d in self.every if d.lootid in ALL_LOOTIDS and d.reference is not None}
        self.assertEqual(wave_1, set())

    # --- the heroic lootids ----------------------------------------------------------------------------------------

    def test_heroic_lootids_are_the_bosses_own_heroic_entries(self):
        text = BRS_DUNGEON.read_text(encoding="utf-8")
        for name, (normal, heroic, *_rest) in UPPER_BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in blackrock_spire.py (the wave 2 overrides)")
        self.assertEqual({d.lootid for d in self.lists.values()}, UPPER_LOOTIDS)

    def test_the_heroic_lootids_are_the_heroic_tests_predictions(self):
        # test_blackrock_spire_heroic.py pins the same table against the mint order (entries, the lock)
        text = (TOOL_ROOT / "lib" / "test_blackrock_spire_heroic.py").read_text(encoding="utf-8")
        m = re.search(r"(?s)^HEROIC_LOOTID = (\{.*?\})\n", text, re.M)
        self.assertIsNotNone(m)
        predicted = ast.literal_eval(m.group(1))
        self.assertEqual({v[0]: v[1] for v in ALL_BOSSES.values()}, predicted)

    def test_the_predicted_heroic_lootids_still_hold_against_the_lock(self):
        """Wave 2's six are the same predictions as wave 1's (LowerSpireLootTest.test_the_predicted_heroic_lootids_
        still_hold covers all fifteen before the write run); after the write run the lock is the truth."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        for name, (normal, heroic, *_rest) in UPPER_BOSSES.items():
            if normal in lock.pairs:
                self.assertEqual(lock.pairs[normal], heroic,
                                 f"{name} ({normal}): the lock says {lock.pairs[normal]}; update UPPER_BOSS_LISTS, "
                                 f"UPPER_BOSSES, blackrock_spire.py's wave 2 overrides and the heroic test's table")
        # the minted order: every wave 2 boss follows its position among the fifteen in normal-entry order
        order = sorted(v[0] for v in ALL_BOSSES.values())
        by_entry = {v[0]: v[1] for v in ALL_BOSSES.values()}
        self.assertEqual(len(order), 15)
        self.assertEqual([by_entry[n] for n in order], sorted(by_entry.values()))

    # --- the cuts --------------------------------------------------------------------------------------------------

    def test_the_cut_stock_rows_are_named_and_only_on_the_normal_lootids(self):
        for name, (normal, heroic, keys, _token, cut, pools, _picks, _refs) in UPPER_BOSSES.items():
            with self.subTest(boss=name):
                decl = self.lists[(normal, LIST_GROUP)]
                self.assertEqual(set(decl.replaces_items), cut)
                self.assertEqual(set(decl.replaces_references), pools)
                other = self.lists[(heroic, LIST_GROUP)]
                self.assertEqual((other.replaces_items, other.replaces_references), ((), ()))
                # a replaced row is never a list item's own stock entry
                stock = {self.items[key].base for key in keys if self.items[key].base}
                self.assertFalse(cut & stock)

    def test_the_tier_0_pieces_are_all_gone(self):
        # Emberseer's Gauntlets of Elements, Solakar's Devout Mantle, Gyth's Pauldrons of Elements and Drakkisath's nine
        # chests (SP says 8 and lists 8 sets: the live group holds Elements, Beaststalker's, Magister's, Devout,
        # Dreadmist, Wildheart, Shadowcraft, Lightforge and Valor)
        tier_0 = {16672, 16695, 16669} | UPPER_BOSSES["Drakkisath"][4]
        named = set().union(*(set(d.replaces_items) for d in self.decls))
        self.assertEqual(tier_0 & named, tier_0)
        self.assertEqual(len(UPPER_BOSSES["Drakkisath"][4]), 9)

    def test_the_two_roll_pools_are_replaced_and_deleted(self):
        self.assertEqual(sorted(self.pool_removals), sorted(STOCK_POOLS))
        # Rend's and the Beast's rolls are group 1 rows (replaces_references), Drakkisath's a group 0 row (removal)
        self.assertEqual(self.lists[(10429, LIST_GROUP)].replaces_references, (35022,))
        self.assertEqual(self.lists[(10430, LIST_GROUP)].replaces_references, (35023,))
        removal = self.row_removals[(10363, 0)]
        self.assertEqual((removal.rows, removal.ref_rows), ((), (35025,)))
        # no list names a pool that is not deleted
        named = {r for d in self.decls for r in d.replaces_references} | {r for d in self.decls for r in d.ref_rows}
        self.assertEqual(named, STOCK_POOLS)

    def test_group_zero_cuts_only_bonespike_shoulder_and_drakkisaths_pool_row(self):
        self.assertEqual({(lootid, group) for (lootid, group) in self.row_removals}, {(10429, 0), (10363, 0)})
        self.assertEqual(set(self.row_removals[(10429, 0)].rows), {12588})  # Bonespike Shoulder
        self.assertFalse(set(self.row_removals[(10429, 0)].ref_rows))
        self.assertFalse({lootid for lootid, _g in self.row_removals} & set(UPPER_HEROIC_LOOTIDS.values()))

    def test_the_stock_quest_recipe_and_pool_rows_are_never_named(self):
        named = set()
        for d in self.decls:
            named |= set(d.rows) | set(d.replaces_items)
        self.assertFalse(UPPER_KEEP & named)
        # Emberseer's world drop tree (group 5, reference 1000260) is nobody's declaration
        self.assertFalse(1000260 in {r for d in self.decls for r in d.replaces_references + d.ref_rows})
        self.assertFalse(any(d.group == 5 for d in self.decls))
        self.assertFalse(any(d.group == 0 and d.listing for d in self.decls))

    # --- the Molten tokens -----------------------------------------------------------------------------------------

    def test_molten_boots_on_rend_and_the_chestpiece_on_drakkisath_at_the_kills_tier(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP}
        self.assertEqual(sorted(by_key), sorted([(10429, 3), (310270, 3), (10363, 3), (310263, 3)]))
        for name, (normal, heroic, _keys, token, *_rest) in UPPER_BOSSES.items():
            if token is None:
                self.assertNotIn((normal, TOKEN_GROUP), by_key, name)
                continue
            self.assertIn(token, self.tokens)
            self.assertEqual(self.tokens[token].slots, TOKEN_SLOT_UPPER[token])
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                decl = by_key[(lootid, TOKEN_GROUP)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode), ((token,), tier, 1, 1), name)
        self.assertEqual(by_key[(10429, 3)].items, ("molten_token_feet",))
        self.assertEqual(by_key[(10363, 3)].items, ("molten_token_chest",))
        # Gyth drops list items and no token: one pair of boots per full clear
        self.assertNotIn((10339, TOKEN_GROUP), by_key)
        self.assertNotIn((310262, TOKEN_GROUP), by_key)

    # --- the hard mode list ----------------------------------------------------------------------------------------

    def test_drakkisaths_hard_mode_is_group_two_of_his_heroic_lootid_only_at_loot_mode_2(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == HARD_MODE_GROUP}
        self.assertEqual(sorted(by_key), [(DRAKKISATH_HARD_MODE_LOOTID, 2)])
        decl = by_key[(DRAKKISATH_HARD_MODE_LOOTID, 2)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, decl.reference, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, None, DRAKKISATH_HARD_MODE))
        self.assertEqual(len(decl.items), 3)
        # the hard mode list is Wyrmthalak's rule: the same loot mode bit, one item on top of the heroic items; no
        # other Upper Spire group is at LootMode 2
        self.assertFalse([k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1
                          and k != (DRAKKISATH_HARD_MODE_LOOTID, 2)])

    # --- the flex second roll --------------------------------------------------------------------------------------

    def test_every_list_has_a_copy_at_loot_mode_4_on_both_lootids_with_a_pool_of_its_own(self):
        for name, (normal, heroic, keys, _token, _cut, _pools, picks, refs) in UPPER_BOSSES.items():
            for index, (lootid, tier) in enumerate(((normal, "normal"), (heroic, "heroic")), start=0):
                with self.subTest(boss=name, lootid=lootid):
                    copy = self.lists[(lootid, FLEX_LIST_GROUP)]
                    base = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((copy.items, copy.tier, copy.picks, copy.loot_mode),
                                     (base.items, tier, picks, FLEX_MODE))
                    self.assertEqual(copy.reference, refs[2 + index] if refs else None)
                    self.assertEqual((copy.replaces_items, copy.replaces_references), ((), ()))
                    if refs:
                        self.assertNotEqual(copy.reference, base.reference)

    def test_every_token_has_a_copy_at_loot_mode_4_on_both_lootids(self):
        copies = {k: d for k, d in self.lists.items() if k[1] == FLEX_TOKEN_GROUP}
        self.assertEqual(sorted(copies), sorted([(10429, 13), (310270, 13), (10363, 13), (310263, 13)]))
        for (lootid, _group), copy in copies.items():
            base = self.lists[(lootid, TOKEN_GROUP)]
            self.assertEqual((copy.items, copy.tier, copy.loot_mode), (base.items, base.tier, FLEX_MODE), lootid)

    def test_the_hard_mode_list_has_a_copy_at_loot_mode_8_on_the_heroic_lootid_only(self):
        copies = {k: d for k, d in self.lists.items() if k[1] == FLEX_HARD_MODE_GROUP}
        self.assertEqual(sorted(copies), [(DRAKKISATH_HARD_MODE_LOOTID, 12)])
        copy, base = copies[(DRAKKISATH_HARD_MODE_LOOTID, 12)], self.lists[(DRAKKISATH_HARD_MODE_LOOTID, 2)]
        self.assertEqual((copy.items, copy.tier, copy.picks, copy.loot_mode),
                         (base.items, "heroic_hm", 1, FLEX_HARD_MODE_MODE))

    def test_loot_modes_follow_the_group_and_the_groups_are_the_wave_1_ones(self):
        for key, decl in self.lists.items():
            with self.subTest(group=key):
                expected = {LIST_GROUP: 1, TOKEN_GROUP: 1, HARD_MODE_GROUP: 2, FLEX_LIST_GROUP: 4,
                            FLEX_TOKEN_GROUP: 4, FLEX_HARD_MODE_GROUP: 8}[key[1]]
                self.assertEqual(decl.loot_mode, expected)
        self.assertEqual({group for _lootid, group in self.lists}, {1, 2, 3, 11, 12, 13})

    def test_declaration_counts(self):
        # 6 bosses x 2 lootids x (list + flex list) + 2 tokens x 2 lootids x 2 + the hard mode pair, 2 group 0 cuts,
        # 3 pool removals
        self.assertEqual(len(self.lists), 6 * 2 * 2 + 2 * 2 * 2 + 2)
        self.assertEqual(len(self.row_removals), 2)
        self.assertEqual(len(self.pool_removals), 3)
        self.assertEqual(len(self.decls), len(self.lists) + 2 + 3)
        # nothing in the file names a lootid outside the fifteen bosses (and their heroic copies)
        self.assertEqual({d.lootid for d in self.every if not d.pool_removal}, ALL_LOOTIDS | UPPER_LOOTIDS)

    # --- the items the lists name ----------------------------------------------------------------------------------

    def test_list_items_are_on_the_dungeon_ladder_and_hard_mode_items_on_the_hard_mode_ladder(self):
        for keys in [v[2] for v in UPPER_BOSSES.values()]:
            for key in keys:
                self.assertEqual(self.items[key].ladder.name, "vanilla_dungeon", key)
        for key in DRAKKISATH_HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)
        for decl in self.decls:
            if not decl.listing:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))

    # --- the boss scripts light the loot bits ----------------------------------------------------------------------

    def test_every_upper_spire_boss_script_sets_the_flex_loot_bits_at_the_pull(self):
        # Flex::OnPull (via BlackrockSpireRework::OnBossPull) holds the count and sets LootMode 4 / 8 at the pull: the
        # loot is filled in Unit::Kill, before JustDied
        if not BOSS_SCRIPT_DIR.is_dir():
            self.skipTest("modules/mod-dungeon-bosses is not beside this checkout")
        files = {
            "Emberseer": "boss_pyroguard_emberseer_rework.cpp", "Solakar": "boss_solakar_flamewreath_rework.cpp",
            "Rend": "boss_rend_blackhand_rework.cpp", "Gyth": "boss_gyth_rework.cpp",
            "Beast": "boss_the_beast_rework.cpp", "Drakkisath": "boss_drakkisath_rework.cpp",
        }
        for name, filename in files.items():
            with self.subTest(boss=name):
                text = (BOSS_SCRIPT_DIR / filename).read_text(encoding="utf-8")
                self.assertRegex(text, r"OnBossPull\(me, \w+")
        # Drakkisath passes the hard mode flag (his heroic hard mode's LootMode bit 2 and the flex hard mode bit 8)
        self.assertRegex((BOSS_SCRIPT_DIR / files["Drakkisath"]).read_text(encoding="utf-8"),
                         r"OnBossPull\(me, \w+, hardMode\)")


if __name__ == "__main__":
    unittest.main()
