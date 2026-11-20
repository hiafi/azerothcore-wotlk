"""
Blackrock Depths build, WP-L-1: the wave 1 declarations in source/items/blackrock_depths_loot.py (item keys from
blackrock_depths.py and its hard mode effects, tokens from molten_set.py) and the gameobject loot rev
data/sql/updates/pending_db_world/rev_loot_wave_1_blackrock_depths.sql.

Sections 1 and 2: the bosses' lists (Gerstahn, Roccor, Grebmar, the six Ring champions, Loregrain, Stilgiss and Verek,
Doomgrip, Incendius, Bael'Gar, Fineous and Panzor the Invincible) at the Normal tier on the stock lootids and the Heroic
tier on the heroic bodies' own lootids, the Ring's Molten legs token at LootMode 4, Incendius's wrist token, the
Encore's and the Lord of the Lake's hard mode lists, the 5% Dark Keeper Key rows and the cut stock rows. The rows
themselves (and their rules and rendering) are test_loot_tables.py's; the real plan (tiers, the live stock groups) is
`generate.py --check --only items`'s.

`WaveOneLootTest` / `GameObjectLootRevTest` are WP-L-1's (sections 1 and 2; they look at the wave 1 declarations only,
`WAVE_2_LOOTIDS` are filtered out). `WaveTwoLootTest` / `WaveTwoGameObjectLootRevTest` are WP-L-2's: sections 3 and 4
(Angerforge, Argelmach, Hurley, Ribbly, Plugger, Phalanx, Flamelash, Magmus, the Emperor, Moira's emptied lootid, the
Chest of The Seven rev), and the rule that every heroic boss on its own lootid has a declaration (R-1-LOOT M-1).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_loot.py
"""

from __future__ import annotations

import re
import runpy
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.heroic_templates import LOCK_PATH, parse_lock  # noqa: E402

BRD_DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"
SQL_REV = (TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"
           / "rev_loot_wave_1_blackrock_depths.sql")
RING_CHAMPIONS_LOGIC = (TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
                        / "RingChampionsLogic.h")

LIST_GROUP, HARD_MODE_GROUP, TOKEN_GROUP, KEY_GROUP = 1, 2, 3, 4
TITLE_HOLDER_MODE = 4  # RingChampionsLogic.h kTitleHolderLootMode
DARK_KEEPER_KEY = 11197

MINOR_POOL = {
    "brd_hurleys_tankard", "brd_coal_miner_boots", "brd_firemoss_boots", "brd_mixologists_tunic",
    "brd_barman_shanker", "brd_rock_golem_bulwark", "brd_stone_of_the_earth", "brd_shalehusk_boots",
}
VAULT_FOUR = {
    "brd_black_steel_bindings", "brd_wand_of_eternal_light", "brd_magma_forged_band", "brd_mana_shaping_handwraps",
}

# name -> (normal lootid, heroic lootid, the approved list (blackrock-depths-rework.md ## Loot, Sections 1 and 2), the
# Molten token key, the stock group 1 rows the list replaces, the token's loot mode, the 5% Dark Keeper Key)
BOSSES = {
    "Gerstahn": (9018, 310343, {"brd_kentic_amice", "brd_greaves_of_withering_despair", "brd_blackveil_cape"},
                 None, {11625}, 1, True),
    "Roccor": (9025, 310346, {"brd_stoneshell_guard", "brd_earthslag_shoulders", "brd_idol_of_ferocity"},
               None, {22234}, 1, False),
    "Grebmar": (9319, 310366, {"brd_houndmasters_bow", "brd_fleetfoot_greaves", "brd_spritecaster_cape"},
                None, {11629}, 1, True),
    "Gorosh": (9027, 310347, {"brd_savage_gladiator_chain", "brd_bloodclot_band"}, "molten_token_legs",
               {22266, 22271}, TITLE_HOLDER_MODE, False),
    "Grizzle": (9028, 310348, {"brd_entrenching_boots", "brd_grizzles_skinner"}, "molten_token_legs",
                {11703, 11722}, TITLE_HOLDER_MODE, False),
    "Eviscerator": (9029, 310349, {"brd_savage_gladiator_grips", "brd_spell_eaters_choker"}, "molten_token_legs",
                    {11679, 11685, 11686}, TITLE_HOLDER_MODE, False),
    "Ok'thor": (9030, 310350, {"brd_cyclopean_band", "brd_ogreseer_fists"}, "molten_token_legs",
                {11662, 11728}, TITLE_HOLDER_MODE, False),
    "Anub'shiah": (9031, 310351, {"brd_carapace_of_anubshiah", "brd_graverot_cape"}, "molten_token_legs",
                   {11675, 11731}, TITLE_HOLDER_MODE, False),
    "Hedrum": (9032, 310352, {"brd_hookfang_shanker", "brd_spiderfang_carapace"}, "molten_token_legs",
               {11634, 11729}, TITLE_HOLDER_MODE, False),
    "Loregrain": (9024, 310345, {"brd_kindling_stave", "brd_flamestrider_robes", "brd_dregmetal_spaulders"},
                  None, {11748, 11749}, 1, True),
    "Stilgiss": (9041, 310361, {"brd_boreal_mantle", "brd_arbiters_blade", "brd_dark_warders_pauldrons",
                                "brd_vereks_collar"}, None, {11783}, 1, True),
    "Doomgrip": (9476, 310375, VAULT_FOUR, None, set(), 1, True),
    "Incendius": (9017, 310342, {"brd_undying_ember", "brd_anvilfire_grips", "brd_robe_of_the_elemental_lord"},
                  "molten_token_wrist", {11764, 11765, 11766, 11767}, 1, False),
    "Bael'Gar": (9016, 310341, {"brd_rubidium_hammer", "brd_force_of_magma", "brd_magmaheart_mantle"},
                 None, {11802, 11807}, 1, False),
    "Fineous": (9056, 310363, MINOR_POOL, None, {11839, 11841, 11842, 22223}, 1, True),
}
PANZOR = (8923, MINOR_POOL, {22245})  # normal lootid only (no heroic template)
CHAMPIONS = ("Gorosh", "Grizzle", "Eviscerator", "Ok'thor", "Anub'shiah", "Hedrum")
DWARF_BOSSES = ("Gerstahn", "Grebmar", "Loregrain", "Stilgiss", "Doomgrip", "Fineous")  # wave 1's (ruling 36)
TOKEN_SLOT = {"molten_token_legs": (7,), "molten_token_wrist": (9,)}  # InventoryTypes
THELDREN_HEROIC = 310390
THELDREN_NORMAL = 16059
ENCORE_HARD_MODE = {"brd_theldrens_executioner", "brd_leftys_shiv", "brd_korvs_spirit_fetish"}
LAKE_HARD_MODE = {"brd_black_anvil_bulwark", "brd_fist_of_the_lake_lord", "brd_scepter_of_the_molten_lake"}

VERIFIED_STOCK_REPLACED_REFERENCES = {24024, 24025, 24027, 24029, 24030, 24031, 24033, 24036, 24043, 24045, 24086}
DOOMGRIP_GROUP_0_CUTS = {
    11920, 11923, 11926, 11929, 22205, 22254, 22255, 22256,
    12527, 12528, 12547, 12550, 12552, 17413, 17414, 17682, 17683, 18600, 19272, 19283, 22393,
}

NORMAL_LOOTIDS = {name: v[0] for name, v in BOSSES.items()}
HEROIC_LOOTIDS = {name: v[1] for name, v in BOSSES.items()}
ALL_LOOTIDS = ({*NORMAL_LOOTIDS.values(), *HEROIC_LOOTIDS.values(), THELDREN_HEROIC, PANZOR[0]})
# The wave 2 (sections 3 and 4) lootids L-2 owns: bosses, Moira's and the High Priestess's, the minor pool's wave 2
# members, the Seven (lootid 0 on the ghosts).
WAVE_2_LOOTIDS = {9033, 8983, 9537, 9543, 9499, 9502, 9156, 9938, 9019, 8929, 10076,
                  310353, 310340, 310378, 310380, 310376, 310377, 310364, 310382, 310344}
# The quest, key, reagent and trophy rows of the wave 1 lootids that stay.
STOCK_KEEP = {11140, 11446, 14047, 18945, 22528, 8150, 11129, 22527, 11630, 10999, 11078, 11468, 11840, 11126, 21987,
              19268, 3857, 4337, 10285, 1074, 4585, 12205, 14227, 22525, 12203, 12208, 4583, 4584, 22047, 24024,
              13446, 13443, 8766, 8950}

SQL_REV_2 = (TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"
             / "rev_loot_wave_2_blackrock_depths.sql")
ITEM_LOCK = TOOL_ROOT / "source" / "items" / "item_ids.lock"
IDS_YAML = TOOL_ROOT / "source" / "ids.yaml"
MOLTEN_TOKENS = {"molten_token_legs", "molten_token_wrist", "molten_token_waist", "molten_token_head"}

# Wave 2, sections 3 and 4 (docs/dungeons/blackrock-depths-rework.md ## Loot, Sections 3 and 4): name -> (normal
# lootid, heroic lootid, the approved list, the Molten token key, the stock group 1 rows the list replaces, the 5%
# Dark Keeper Key).
WAVE_2_BOSSES = {
    "Angerforge": (9033, 310353, {"brd_angerforges_battle_axe", "brd_lord_generals_sword", "brd_royal_decorated_armor"},
                   None, {11810, 11821}, True),
    "Argelmach": (8983, 310340, {"brd_second_wind", "brd_naglering", "brd_omnicast_boots"}, "molten_token_waist",
                  {11823}, True),
    "Hurley": (9537, 310378, MINOR_POOL, None, {11735}, True),
    "Phalanx": (9502, 310377, {"brd_bloodfist", "brd_fists_of_phalanx", "brd_golem_fitted_pauldrons"}, None,
                {11743}, False),
    "Flamelash": (9156, 310364, {"brd_flame_wrath", "brd_burst_of_knowledge", "brd_molten_fists"}, None,
                  {11808, 11812}, False),
    "Magmus": (9938, 310382, {"brd_magmus_stone", "brd_totem_of_rage", "brd_libram_of_truth"}, None,
               {11746, 22208}, False),
}
RIBBLY = (9543, 310380)
PLUGGER = (9499, 310376)
EMPEROR = (9019, 310344)
SIDE_POOL_GROUP = 5
EMPEROR_LIST = {
    "brd_hand_of_justice", "brd_robes_of_the_royal_crown", "brd_thaurissans_royal_scepter",
    "brd_the_emperors_new_cape", "brd_imperial_jewel", "brd_hands_of_the_exalted_herald", "brd_high_priestess_boots",
    "brd_idol_of_the_wayward_princess",
}
ARGELMACH_HARD_MODE = {"brd_prototype_power_core", "brd_golemwrights_mending_rod", "brd_electrons_lethal_coil"}
AVATAR_HARD_MODE = {"brd_ironfoe", "brd_volcanic_heartstone", "brd_orb_of_the_sorcerer_thane"}
CHEST_SEVEN = ("brd_wraith_scythe", "brd_blood_etched_blade", "brd_the_hammer_of_grace",
               "brd_deathdealer_breastplate", "brd_ebonsteel_spaulders", "brd_swiftwalker_boots")
CHEST_NORMAL_ENTRIES = {11920, 11922, 11923, 11926, 12557, 12553}  # the stock bases of the six
WAVE_2_DWARF_BOSSES = ("Angerforge", "Argelmach", "Hurley")  # plus Plugger and the Emperor below
MOIRA = 8929
EMPEROR_STOCK_REFERENCE = 35014
# Ribbly's and Plugger's stock group 1 rows that are no gear and no cut, and stay; Plugger's two pool items leave it
RIBBLY_KEPT = {2663, 2662, 11742}
PLUGGER_SCHEMATIC = 18653
PLUGGER_POOL_ROWS = {12793, 12791}
# The quest, key, reagent and trophy rows of the wave 2 lootids that stay.
WAVE_2_STOCK_KEEP = {11464, 11465, 11268, 11468, 11446, 14047, 18945, 22528, 11078, 11312, 11313, 11129, 7912, 4552,
                     8150, 11370, 4554, 4787, 3857, 12033, 18653, 2663, 2662, 11742}


def _declarations() -> tuple[dict, list[L.LootDecl]]:
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == "blackrock_depths_loot.py"]
    finally:
        registry.stop_provenance()
    return merged, mine


class WaveOneLootTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        cls.decls = [d for d in every if d.lootid not in WAVE_2_LOOTIDS and not d.pool_removal]  # wave 1's only
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("brd_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls
                     if d.listing and d.chance is None and not d.removal}
        cls.chances = [d for d in cls.decls if d.chance is not None]
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.group_removals = {(d.lootid, d.group): d for d in cls.decls if d.removal}

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, keys, _token, _cut, _mode, _key) in BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), set(keys))
                    self.assertEqual(len(decl.items), len(keys))
                    self.assertTrue(set(keys) <= set(self.items))

    def test_list_sizes(self):
        sizes = {name: len(v[2]) for name, v in BOSSES.items()}
        self.assertEqual(sizes, {
            "Gerstahn": 3, "Roccor": 3, "Grebmar": 3, "Gorosh": 2, "Grizzle": 2, "Eviscerator": 2, "Ok'thor": 2,
            "Anub'shiah": 2, "Hedrum": 2, "Loregrain": 3, "Stilgiss": 4, "Doomgrip": 4, "Incendius": 3, "Bael'Gar": 3,
            "Fineous": 8,
        })

    def test_the_ring_drops_one_of_two_from_each_champion_and_the_twelve_are_distinct(self):
        # SP structure: each champion drops 1 from its own list of 2 (ruling 86), 2 per Ring run, 12 in all
        listed = [key for name in CHAMPIONS for key in sorted(BOSSES[name][2])]
        self.assertEqual(len(listed), 12)
        self.assertEqual(len(set(listed)), 12)
        for name in CHAMPIONS:
            decl = self.lists[(BOSSES[name][0], LIST_GROUP)]
            self.assertEqual((len(decl.items), decl.picks), (2, 1), name)

    def test_the_wave_1_section_lists_hold_the_approved_item_counts(self):
        # section 1: 3 + 3 + 3 + 12 = 21 list items; section 2 without the minor pool: 3 + 4 + 4 + 3 + 3 = 17
        section_1 = set().union(*(BOSSES[n][2] for n in ("Gerstahn", "Roccor", "Grebmar", *CHAMPIONS)))
        section_2 = set().union(*(BOSSES[n][2] for n in ("Loregrain", "Stilgiss", "Doomgrip", "Incendius",
                                                          "Bael'Gar")))
        self.assertEqual((len(section_1), len(section_2)), (21, 17))
        self.assertFalse(section_1 & section_2)
        self.assertFalse((section_1 | section_2) & MINOR_POOL)

    def test_stilgiss_carries_the_one_list_of_four_and_verek_drops_none_of_it(self):
        # one encounter, one list of 4 on Stilgiss; Verek's own group 1 goes (the Collar moved, the Leash is cut)
        self.assertEqual(len(self.lists[(9041, LIST_GROUP)].items), 4)
        removal = self.group_removals[(9042, LIST_GROUP)]
        self.assertEqual(removal.replaces_items, (22242,))
        self.assertIn("brd_vereks_collar", BOSSES["Stilgiss"][2])
        # Verek has no heroic lootid of his own (STAGE-H): the stock lootid serves both difficulties
        self.assertNotIn(9042, {v[0] for v in BOSSES.values()})
        self.assertFalse([d for d in self.decls if d.lootid == 9042 and d is not removal])

    def test_doomgrips_list_is_the_vault_four_and_the_strays_leave(self):
        for lootid, tier in ((9476, "normal"), (310375, "heroic")):
            self.assertEqual((self.lists[(lootid, LIST_GROUP)].tier, set(self.lists[(lootid, LIST_GROUP)].items)),
                             (tier, VAULT_FOUR))
        normal = self.lists[(9476, LIST_GROUP)]
        self.assertEqual(set(normal.replaces_references), VERIFIED_STOCK_REPLACED_REFERENCES)
        self.assertEqual(normal.replaces_items, ())
        self.assertEqual(set(self.row_removals[(9476, 0)].rows), DOOMGRIP_GROUP_0_CUTS)
        self.assertFalse(self.row_removals[(9476, 0)].ref_rows)
        # the Vault four's Normal ids are the stock ids the Safe script reads (STAGE-D9 4.4): 22205 22254 22255 22256
        self.assertEqual({self.items[key].base for key in VAULT_FOUR}, {22205, 22254, 22255, 22256})
        self.assertTrue({22205, 22254, 22255, 22256} <= DOOMGRIP_GROUP_0_CUTS)  # the stock group 0 rows go

    def test_the_minor_pool_is_the_same_eight_on_fineous_and_panzor(self):
        for lootid, tier in ((9056, "normal"), (310363, "heroic"), (PANZOR[0], "normal")):
            decl = self.lists[(lootid, LIST_GROUP)]
            self.assertEqual((set(decl.items), len(decl.items), decl.tier), (MINOR_POOL, 8, tier), lootid)
        self.assertNotIn((PANZOR[0], TOKEN_GROUP), self.lists)
        # Panzor has no heroic template (STAGE-H skip=): no declaration on any heroic lootid of his
        self.assertEqual({d.lootid for d in self.decls if d.lootid == PANZOR[0]}, {PANZOR[0]})
        self.assertEqual(self.lists[(PANZOR[0], LIST_GROUP)].replaces_items, (22245,))
        # the pool's eight come from Hurley, Plugger and Panzor (ruling 86, SP Section 4): Coal Miner Boots is the
        # dungeon's one Leather Tank piece
        self.assertIn("brd_coal_miner_boots", MINOR_POOL)

    # --- the heroic lootids ----------------------------------------------------------------------------------------

    def test_heroic_lootids_are_the_bosses_own_heroic_entries(self):
        text = BRD_DUNGEON.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^_HEROIC_BOSS_OWN_LOOT\s*=\s*True\s*$")
        for name, (normal, heroic, *_rest) in BOSSES.items():
            with self.subTest(boss=name):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in blackrock_depths.py")
        self.assertIsNotNone(re.search(rf"^\s*16059: _boss\([\d_]+, {THELDREN_HEROIC}",
                                       text, re.M))
        lootids = {d.lootid for d in self.lists.values()}
        self.assertEqual(lootids, ALL_LOOTIDS)

    def test_the_predicted_heroic_lootids_still_hold(self):
        """The heroic lootids are PREDICTIONS (source/world/dungeons/blackrock_depths.py `_boss(...)`, BOSS_LISTS in
        source/items/blackrock_depths_loot.py, BOSSES above): the first write run mints the heroic entries from 310301
        in normal-entry order (test_blackrock_depths_heroic.py::test_the_predicted_lock_lines pins the order). If
        another branch appended lines to source/world/heroic_ids.lock first, the mint shifts and every heroic lootid
        points at another creature's heroic entry: this test fails loudly BEFORE the write run."""
        lock = parse_lock(LOCK_PATH.read_text(encoding="utf-8"))
        fix = (
            "The heroic lootids are hard-coded predictions and the mint has shifted. Fix: take the real heroic entry "
            "of each boss from source/world/heroic_ids.lock (or, before the write run, 310301 + the boss's index in "
            "normal-entry order after the lock's last line) and update ALL THREE places: the `_boss(..., <lootid>)` "
            "overrides in source/world/dungeons/blackrock_depths.py, BOSS_LISTS (and THELDREN_HEROIC) in source/items/"
            "blackrock_depths_loot.py and BOSSES in this test (and HEROIC_LOOTID in test_blackrock_depths_heroic.py); "
            "then rerun lib/test_blackrock_depths_heroic.py and this file."
        )
        pairs = {v[0]: v[1] for v in BOSSES.values()}
        pairs[THELDREN_NORMAL] = THELDREN_HEROIC
        ours = {normal: lock.pairs[normal] for normal in pairs if normal in lock.pairs}
        if ours:  # after the write run: the lock is the truth
            for normal, heroic in pairs.items():
                if normal in ours:
                    self.assertEqual(ours[normal], heroic, f"creature {normal}: lock says {ours[normal]}. {fix}")
        else:  # before it: nothing of ours is in the lock and the next free id is the first predicted one
            taken = sorted(h for h in lock.pairs.values() if h >= 310301)
            self.assertEqual(taken, [], f"the lock already holds ids from 310301 ({taken[:3]}...) but none of the "
                                        f"Blackrock Depths bosses. {fix}")
            foreign_top = max((h for h in lock.pairs.values() if h < 310301), default=0)
            self.assertEqual(foreign_top, 310300, f"the lock's last id below the first predicted one is "
                                                  f"{foreign_top}, not 310300: lines were added or removed. {fix}")

    # --- the cuts --------------------------------------------------------------------------------------------------

    def test_the_cut_stock_group_one_rows_are_named_and_only_on_the_normal_lootids(self):
        for name, (normal, heroic, keys, _token, cut, _mode, _key) in BOSSES.items():
            with self.subTest(boss=name):
                decl = self.lists[(normal, LIST_GROUP)]
                self.assertEqual(set(decl.replaces_items), cut)
                other = self.lists[(heroic, LIST_GROUP)]
                self.assertEqual((other.replaces_items, other.replaces_references), ((), ()))
                # a replaced row is never a list item's own stock entry
                stock = {self.items[key].base for key in keys if self.items[key].base}
                self.assertFalse(cut & stock)

    def test_the_savage_gladiator_set_and_the_token_slot_pieces_are_the_cut_ones(self):
        cut_all = set().union(*(v[4] for v in BOSSES.values())) | PANZOR[2]
        # head, legs, greaves of the Savage Gladiator set and Incendius's four bracers go; chest, grips are list items
        for entry in (11729, 11728, 11731, 22271, 11764, 11765, 11766, 11767, 11839, 11841, 11842, 22223):
            self.assertIn(entry, cut_all)
        self.assertEqual({self.items["brd_savage_gladiator_chain"].base, self.items["brd_savage_gladiator_grips"].base},
                         {11726, 11730})

    def test_anubshiahs_stock_group_two_row_goes_so_the_carapace_drops_once(self):
        removal = self.row_removals[(9031, 2)]
        self.assertEqual((removal.rows, removal.group), ((11678,), 2))
        self.assertEqual(self.items["brd_carapace_of_anubshiah"].base, 11678)
        self.assertNotIn((9031, 2), self.lists)

    def test_group_zero_cuts_are_doomgrips_only(self):
        zero = {key: d for key, d in self.row_removals.items() if key[1] == 0}
        self.assertEqual(sorted(zero), [(9476, 0)])
        self.assertEqual({lootid for lootid, _g in self.row_removals} & ALL_LOOTIDS - {9476, 9031}, set())

    def test_the_stock_quest_key_and_reagent_rows_are_never_named(self):
        named = set()
        for d in self.decls:
            named |= set(d.rows) | set(d.replaces_items)
        self.assertFalse(STOCK_KEEP & named)
        # the Relic Coffer Key's 1% and the Dark Keepers' swap are IT's hand SQL: no declaration touches 11078
        self.assertNotIn(11078, named)
        self.assertNotIn(11197, named)

    # --- the Molten tokens -----------------------------------------------------------------------------------------

    def test_the_legs_token_drops_from_every_champion_lootid_at_the_title_holders_loot_mode(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP}
        for name in CHAMPIONS:
            normal, heroic, _keys, token, _cut, mode, _key = BOSSES[name]
            self.assertEqual((token, mode), ("molten_token_legs", TITLE_HOLDER_MODE))
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                decl = by_key[(lootid, TOKEN_GROUP)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode),
                                 (("molten_token_legs",), tier, 1, TITLE_HOLDER_MODE), (name, lootid))
        self.assertEqual(self.tokens["molten_token_legs"].slots, TOKEN_SLOT["molten_token_legs"])

    def test_the_title_holder_loot_mode_is_the_bit_the_ring_champion_script_adds(self):
        text = RING_CHAMPIONS_LOGIC.read_text(encoding="utf-8") if RING_CHAMPIONS_LOGIC.is_file() else ""
        if text:
            self.assertRegex(text, rf"kTitleHolderLootMode\s*=\s*{TITLE_HOLDER_MODE}\b")

    def test_incendius_drops_the_wrist_token_at_every_difficulty(self):
        by_key = {k: d for k, d in self.lists.items() if k[1] == TOKEN_GROUP and k[0] in (9017, 310342)}
        self.assertEqual(sorted(by_key), [(9017, 3), (310342, 3)])
        for (lootid, _g), decl in by_key.items():
            self.assertEqual((decl.items, decl.loot_mode, decl.tier),
                             (("molten_token_wrist",), 1, "normal" if lootid == 9017 else "heroic"))
        self.assertEqual(self.tokens["molten_token_wrist"].slots, TOKEN_SLOT["molten_token_wrist"])

    def test_no_other_wave_1_lootid_carries_a_token_and_waist_and_head_are_wave_2s(self):
        token_lootids = {k[0] for k in self.lists if k[1] == TOKEN_GROUP}
        champions = {BOSSES[n][i] for n in CHAMPIONS for i in (0, 1)}
        self.assertEqual(token_lootids, champions | {9017, 310342})
        used = {key for d in self.lists.values() if d.group == TOKEN_GROUP for key in d.items}
        self.assertEqual(used, {"molten_token_legs", "molten_token_wrist"})

    # --- the hard mode lists ---------------------------------------------------------------------------------------

    def test_the_encore_list_is_group_two_of_theldrens_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(THELDREN_HEROIC, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, ENCORE_HARD_MODE))
        self.assertEqual(len(decl.items), 3)
        # Theldren's normal lootid and the other four members' (lootid 0, STAGE-D6) get no declaration
        self.assertFalse([d for d in self.decls if d.lootid == THELDREN_NORMAL])
        self.assertEqual({d.lootid for d in self.decls if d.group == HARD_MODE_GROUP and d.listing
                          and d.chance is None}, {THELDREN_HEROIC, 310342})

    def test_the_lake_lords_list_is_group_two_of_incendius_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(310342, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, LAKE_HARD_MODE))
        # the list on the heroic lootid stays: a hard mode kill adds the three on top of it
        self.assertEqual(set(self.lists[(310342, LIST_GROUP)].items), BOSSES["Incendius"][2])
        self.assertNotIn((9017, HARD_MODE_GROUP), self.lists)

    def test_only_the_two_hard_mode_groups_roll_at_loot_mode_2(self):
        modes = sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1)
        self.assertEqual(modes, [(310342, 2), (310390, 2)])

    def test_the_hard_mode_items_are_on_the_hard_mode_ladder(self):
        for key in ENCORE_HARD_MODE | LAKE_HARD_MODE:
            self.assertEqual(self.items[key].ladder.name, "vanilla_hard_mode", key)

    # --- the keys --------------------------------------------------------------------------------------------------

    def test_the_dark_keeper_key_is_five_percent_on_the_six_wave_1_dwarf_bosses_on_both_lootids(self):
        rows = {(d.lootid, d.group): d for d in self.chances}
        expected = {(BOSSES[name][i], KEY_GROUP) for name in DWARF_BOSSES for i in (0, 1)}
        self.assertEqual(set(rows), expected)
        for key, decl in rows.items():
            self.assertEqual((decl.item_entry, decl.chance, decl.loot_mode, decl.reference),
                             (DARK_KEEPER_KEY, 5.0, L.LOOT_MODE_DEFAULT, None), key)
        self.assertEqual({name for name, v in BOSSES.items() if v[6]}, set(DWARF_BOSSES))
        # not on the Ring, Roccor, Incendius, Bael'Gar (ruling 36), nor on Verek or Panzor
        self.assertFalse({9042, 8923, 9025, 9017, 9016} & {d.lootid for d in self.chances})

    # --- groups and counts -----------------------------------------------------------------------------------------

    def test_no_flex_groups_blackrock_depths_is_not_flex(self):
        groups = {group for _lootid, group in self.lists} | {d.group for d in self.chances}
        self.assertEqual(groups, {1, 2, 3, 4})
        self.assertNotIn(0, groups)
        self.assertFalse({11, 12, 13} & groups)
        self.assertFalse([d for d in self.decls if d.loot_mode & 0x8])  # no flex hard mode bit either

    def test_loot_modes_are_only_1_2_and_4(self):
        for key, decl in self.lists.items():
            with self.subTest(group=key):
                champion_token = key[1] == TOKEN_GROUP and key[0] in {BOSSES[n][i] for n in CHAMPIONS for i in (0, 1)}
                expected = {LIST_GROUP: 1, TOKEN_GROUP: TITLE_HOLDER_MODE if champion_token else 1,
                            HARD_MODE_GROUP: 2}[key[1]]
                self.assertEqual(decl.loot_mode, expected)

    def test_declaration_counts(self):
        # 15 bosses x 2 lootids (list) + Panzor's + 6 champions x 2 legs tokens + Incendius's 2 wrist tokens + the two
        # hard mode groups; 6 dwarf bosses x 2 key rows; the cuts: Verek's group, Anub'shiah's row, Doomgrip's strays
        self.assertEqual(len(self.lists), 15 * 2 + 1 + 6 * 2 + 2 + 2)
        self.assertEqual(len(self.chances), 6 * 2)
        self.assertEqual(len(self.row_removals), 2)
        self.assertEqual(len(self.group_removals), 1)
        self.assertEqual(len(self.decls), len(self.lists) + len(self.chances) + len(self.row_removals)
                         + len(self.group_removals))
        # no reference pool: no picks list in this half (the loot_reference block still starts at 1700019)
        self.assertEqual([d for d in self.decls if d.reference is not None], [])

    def test_wave_1_declares_no_section_3_or_4_lootid(self):
        self.assertEqual({d.lootid for d in self.decls} - ALL_LOOTIDS - {9042}, set())  # 9042: Verek's removal

    # --- the items the lists name ----------------------------------------------------------------------------------

    def test_every_wave_1_item_is_declared_and_the_split_with_wave_2_is_exact(self):
        listed = set().union(*(v[2] for v in BOSSES.values()))
        self.assertEqual(len(listed), 21 + 17 + 8)
        hard_mode = ENCORE_HARD_MODE | LAKE_HARD_MODE
        self.assertTrue(listed <= set(self.items))
        self.assertTrue(hard_mode <= set(self.items))
        # the 87 items of the gear stage: 75 list items + 12 hard mode; wave 2 owns the rest
        self.assertEqual(len(self.items), 87)
        self.assertEqual(len(set(self.items) - listed - hard_mode), 29 + 6)

    def test_list_items_are_on_the_dungeon_ladder_and_every_declared_tier_exists(self):
        for decl in self.decls:
            if not decl.listing or decl.chance is not None:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                if decl.tier in ("normal", "heroic"):
                    self.assertEqual(ladder.name, "vanilla_dungeon", key)


class GameObjectLootRevTest(unittest.TestCase):
    """rev_loot_wave_1_blackrock_depths.sql: the Secret Safe, the Relic Coffers and the Dark Coffer."""

    RARE_CUTS = set(range(70720, 70757))
    EPIC_CUTS = set(range(70760, 70797))
    WEAPON_SCROLLS = set(range(79099, 79107))
    FLASKS = {13510, 13511, 13512, 78820, 78821}
    LIBRAM_QUEST_ITEMS = (11751, 11752, 11753)
    CINDER = 70621

    @classmethod
    def setUpClass(cls):
        cls.text = SQL_REV.read_text(encoding="utf-8")
        cls.rows = {}
        pattern = re.compile(r"^\((\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), '(.*)'\)[,;]$", re.M)
        for m in pattern.finditer(cls.text):
            entry, item, ref, chance, quest, mode, group, mn, mx = map(int, m.groups()[:9])
            cls.rows.setdefault(entry, []).append(dict(item=item, ref=ref, chance=chance, quest=quest, mode=mode,
                                                       group=group, min=mn, max=mx, comment=m.group(10)))

    def _groups(self, entry):
        out = {}
        for row in self.rows[entry]:
            out.setdefault((row["group"], row["mode"]), []).append(row["item"])
        return out

    def test_the_secret_safe_keeps_exactly_one_row_the_cinder_at_100_percent(self):
        # STAGE-D9 4.4: an empty table never runs the fill hook
        self.assertEqual(len(self.rows[161495]), 1)
        row = self.rows[161495][0]
        self.assertEqual((row["item"], row["chance"], row["group"], row["mode"], row["ref"]),
                         (self.CINDER, 100, 0, 1, 0))
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` = 161495;", self.text)
        # the Safe has no gold
        self.assertNotIn("`entry` = 161495", self.text.split("-- 4.")[-1])

    def test_the_cinder_is_the_event_item(self):
        table = runpy.run_path(str(TOOL_ROOT / "source" / "items" / "blackrock_depths_event_items.py"))
        self.assertEqual(table["EVENT_ITEMS"][self.CINDER]["name"], "Cinder of the Firelord")

    def test_the_relic_coffer_gives_one_rare_gem_and_one_consumable_on_both_difficulties(self):
        groups = self._groups(11105)
        self.assertEqual(sorted(groups), [(1, 1), (2, 1)])
        self.assertEqual(set(groups[(1, 1)]), self.RARE_CUTS)
        self.assertEqual(len(groups[(1, 1)]), 37)
        self.assertEqual(len(groups[(2, 1)]), len(set(groups[(2, 1)])))
        self.assertFalse(set(groups[(2, 1)]) & (self.RARE_CUTS | self.EPIC_CUTS))
        for row in self.rows[11105]:
            self.assertEqual((row["chance"], row["quest"], row["ref"], row["min"], row["max"]), (0, 0, 0, 1, 1))
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` = 11105;", self.text)

    def test_the_dark_coffer_gives_a_rare_gem_on_normal_and_an_epic_one_on_heroic(self):
        groups = self._groups(11103)
        # group 1 rolls at the default mode (normal), group 2 only at loot mode 2 (heroic: the instance sets it)
        self.assertEqual(set(groups[(1, 1)]), self.RARE_CUTS)
        self.assertEqual(set(groups[(2, 2)]), self.EPIC_CUTS)
        # every other group rolls under either mode (3 = 1 | 2)
        self.assertEqual(sorted(groups), [(0, 3), (1, 1), (2, 2), (3, 3), (4, 3)])
        self.assertEqual(set(groups[(3, 3)]), self.WEAPON_SCROLLS)
        self.assertEqual(set(groups[(4, 3)]), self.FLASKS)
        # the two supply rolls: one reference row rolled twice (the key is (Entry, Item): an item cannot sit in two
        # groups of one chest), its pool the Relic Coffer's consumables at LootMode 3
        ref = [row for row in self.rows[11103] if row["ref"]]
        self.assertEqual([(r["item"], r["ref"], r["chance"], r["mode"], r["group"], r["min"], r["max"]) for r in ref],
                         [(1701101, 1701101, 100, 3, 0, 2, 2)])
        pool = self.rows[1701101]
        self.assertEqual({row["item"] for row in pool}, {row["item"] for row in self.rows[11105] if row["group"] == 2})
        self.assertEqual({(r["mode"], r["group"], r["chance"], r["min"], r["max"]) for r in pool}, {(3, 1, 0, 1, 1)})
        self.assertIn("DELETE FROM `reference_loot_template` WHERE `Entry` = 1701101;", self.text)

    def test_no_chest_lists_an_item_twice(self):
        # item_loot_template / gameobject_loot_template / reference_loot_template are keyed (Entry, Item)
        for entry, rows in self.rows.items():
            items = [row["item"] for row in rows]
            self.assertEqual(len(items), len(set(items)), entry)

    def test_the_dark_coffer_keeps_the_three_libram_quest_items(self):
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` = 11103 AND `Item` NOT IN (11751, 11752, "
                      "11753);", self.text)
        self.assertEqual([row["item"] for row in self.rows[11103] if row["item"] in self.LIBRAM_QUEST_ITEMS], [])
        # R-2-LOOT m-1: the stock rows roll under either mode (the heroic coffer is mode 2)
        self.assertIn("UPDATE `gameobject_loot_template` SET `LootMode` = 3 WHERE `Entry` = 11103 AND `Item` IN "
                      "(11751, 11752, 11753);", self.text)

    def test_the_coffer_gold(self):
        self.assertIn("UPDATE `gameobject_template_addon` SET `mingold` = 100000, `maxgold` = 500000 "
                      "WHERE `entry` = 160836;", self.text)
        self.assertIn("UPDATE `gameobject_template_addon` SET `mingold` = 500000, `maxgold` = 2000000 "
                      "WHERE `entry` = 160845;", self.text)

    def test_every_row_has_the_loot_modes_a_chest_can_use(self):
        for entry, rows in self.rows.items():
            for row in rows:
                self.assertIn(row["mode"], (1, 2, 3), (entry, row))

    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for number, line in enumerate(self.text.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)
        self.assertTrue(self.text.endswith("\n"))


class WaveTwoLootTest(unittest.TestCase):
    """WP-L-2: sections 3 and 4 in source/items/blackrock_depths_loot.py (wave 2 section)."""

    @classmethod
    def setUpClass(cls):
        cls.merged, every = _declarations()
        cls.every = every
        cls.decls = [d for d in every if d.lootid in WAVE_2_LOOTIDS or d.pool_removal]
        cls.items = {e["id"]: e["_decl"] for e in cls.merged["item_declarations"] if e["id"].startswith("brd_")}
        cls.tokens = {e["id"][1]: e["_decl"] for e in cls.merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = {(d.lootid, d.group): d for d in cls.decls
                     if d.listing and d.chance is None and not d.removal}
        cls.chances = [d for d in cls.decls if d.chance is not None]
        cls.row_removals = {(d.lootid, d.group): d for d in cls.decls if d.row_removal}
        cls.group_removals = {(d.lootid, d.group): d for d in cls.decls if d.removal}
        cls.pool_removals = [d for d in cls.decls if d.pool_removal]

    # --- the lists -------------------------------------------------------------------------------------------------

    def test_each_boss_list_is_the_approved_one_at_both_difficulties(self):
        for name, (normal, heroic, keys, _token, _cut, _key) in WAVE_2_BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = self.lists[(lootid, LIST_GROUP)]
                    self.assertEqual((decl.tier, decl.picks, decl.reference, decl.loot_mode),
                                     (tier, 1, None, L.LOOT_MODE_DEFAULT))
                    self.assertEqual(set(decl.items), set(keys))
                    self.assertEqual(len(decl.items), len(set(keys)))
                    self.assertTrue(set(keys) <= set(self.items))

    def test_list_sizes(self):
        self.assertEqual({n: len(v[2]) for n, v in WAVE_2_BOSSES.items()},
                         {"Angerforge": 3, "Argelmach": 3, "Hurley": 8, "Phalanx": 3, "Flamelash": 3, "Magmus": 3})

    def test_the_cut_stock_group_one_rows_are_named_on_the_normal_lootids_only(self):
        for name, (normal, heroic, _keys, _token, cut, _key) in WAVE_2_BOSSES.items():
            with self.subTest(boss=name):
                self.assertEqual(set(self.lists[(normal, LIST_GROUP)].replaces_items), cut)
                self.assertEqual(self.lists[(heroic, LIST_GROUP)].replaces_items, ())
                self.assertEqual(self.lists[(normal, LIST_GROUP)].replaces_references, ())

    def test_the_section_cuts_of_the_approved_doc_are_the_replaced_rows(self):
        # docs/dungeons/blackrock-depths-rework.md Section 3 and 4 "Cut:" lists (the ones that sit in a boss's group 1;
        # Rockfist, Circle of Flame, Cape of the Fire Salamander, Golem Skull Helm, Lavastone Hammer, Force of Will,
        # Warstrife Leggings, Luminary Kilt, Ragefury Eyepatch). The Emperor's and the chest's cuts go with their pools
        # (below); Impervious Giant, Ghostshroud, the Legplates and the Specter Leggings are the chest pool's.
        cut = set().union(*(v[4] for v in WAVE_2_BOSSES.values()))
        self.assertEqual(cut, {11810, 11821, 11823, 11735, 11743, 11808, 11812, 11746, 22208})

    def test_every_wave_2_list_item_is_on_the_dungeon_ladder_and_the_hard_mode_items_on_the_hard_mode_one(self):
        for decl in self.decls:
            if not decl.listing or decl.chance is not None:
                continue
            for key in decl.items:
                ladder = (self.items[key] if key in self.items else self.tokens[key]).ladder
                self.assertIsNotNone(ladder.tier(decl.tier), (key, decl.tier))
                self.assertEqual(ladder.name, "vanilla_hard_mode" if decl.tier == "heroic_hm" else "vanilla_dungeon",
                                 (decl.lootid, key))

    # --- Argelmach -------------------------------------------------------------------------------------------------

    def test_argelmach_drops_the_waist_token_at_every_difficulty(self):
        for lootid, tier in ((8983, "normal"), (310340, "heroic")):
            decl = self.lists[(lootid, TOKEN_GROUP)]
            self.assertEqual((decl.items, decl.tier, decl.loot_mode, decl.picks),
                             (("molten_token_waist",), tier, 1, 1), lootid)
        self.assertEqual(self.tokens["molten_token_waist"].slots, (6,))

    def test_the_prototype_list_is_group_two_of_argelmachs_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(310340, HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items), decl.hard_mode_only),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, ARGELMACH_HARD_MODE, False))
        self.assertEqual(len(decl.items), 3)
        # his normal lootid has no hard mode group (heroic only); the list on 310340 stays under it
        self.assertNotIn((8983, HARD_MODE_GROUP), self.lists)
        self.assertEqual(set(self.lists[(310340, LIST_GROUP)].items), WAVE_2_BOSSES["Argelmach"][2])

    # --- the minor pool: Hurley, Ribbly, Plugger -------------------------------------------------------------------

    def test_hurley_drops_the_minor_pool_in_group_one(self):
        for lootid, tier in ((9537, "normal"), (310378, "heroic")):
            decl = self.lists[(lootid, LIST_GROUP)]
            self.assertEqual((set(decl.items), len(decl.items), decl.tier), (MINOR_POOL, 8, tier), lootid)

    def test_ribbly_and_plugger_drop_the_minor_pool_in_group_five_beside_their_stock_non_gear_rows(self):
        for lootid, tier in ((RIBBLY[0], "normal"), (RIBBLY[1], "heroic"), (PLUGGER[0], "normal"),
                             (PLUGGER[1], "heroic")):
            decl = self.lists[(lootid, SIDE_POOL_GROUP)]
            self.assertEqual((set(decl.items), len(decl.items), decl.tier, decl.replaces_items),
                             (MINOR_POOL, 8, tier, ()), lootid)
            # group 1 is stock (Ribbly's bags, Plugger's Schematic): never declared as a list
            self.assertNotIn((lootid, LIST_GROUP), self.lists)
        # Plugger's two pool items leave his stock group 1, the Schematic stays; Ribbly loses nothing
        removal = self.row_removals[(PLUGGER[0], LIST_GROUP)]
        self.assertEqual(set(removal.rows), PLUGGER_POOL_ROWS)
        self.assertNotIn(PLUGGER_SCHEMATIC, removal.rows)
        self.assertFalse([d for d in self.decls if d.lootid == RIBBLY[0] and d.row_removal])
        self.assertFalse(RIBBLY_KEPT & PLUGGER_POOL_ROWS)

    def test_the_minor_pool_is_the_same_eight_on_all_five_bosses(self):
        wave_1 = {9056, 310363, 8923}
        pools = set()
        for lootid in (9537, 310378, RIBBLY[0], RIBBLY[1], PLUGGER[0], PLUGGER[1]):
            group = LIST_GROUP if lootid in (9537, 310378) else SIDE_POOL_GROUP
            pools.add(frozenset(self.lists[(lootid, group)].items))
        self.assertEqual(pools, {frozenset(MINOR_POOL)})
        self.assertFalse(wave_1 & {d.lootid for d in self.decls})

    # --- the Emperor and Moira -------------------------------------------------------------------------------------

    def test_the_emperor_drops_two_distinct_of_his_eight_from_a_reference_pool(self):
        for lootid, tier, reference in ((EMPEROR[0], "normal", 1700019), (EMPEROR[1], "heroic", 1700020)):
            decl = self.lists[(lootid, LIST_GROUP)]
            self.assertEqual((set(decl.items), len(decl.items), decl.tier, decl.picks, decl.reference),
                             (EMPEROR_LIST, 8, tier, 2, reference), lootid)
        normal = self.lists[(EMPEROR[0], LIST_GROUP)]
        self.assertEqual(normal.replaces_references, (EMPEROR_STOCK_REFERENCE,))
        self.assertEqual(normal.replaces_items, ())
        self.assertEqual(self.lists[(EMPEROR[1], LIST_GROUP)].replaces_references, ())

    def test_the_emperors_stock_pool_of_eleven_is_removed_with_its_row(self):
        self.assertEqual([d.reference for d in self.pool_removals], [EMPEROR_STOCK_REFERENCE])
        # the pool is in the stock range, outside the loot_reference block the DSL owns
        self.assertLess(EMPEROR_STOCK_REFERENCE, 1700000)

    def test_the_emperor_drops_the_head_token_at_every_difficulty(self):
        for lootid, tier in ((EMPEROR[0], "normal"), (EMPEROR[1], "heroic")):
            decl = self.lists[(lootid, TOKEN_GROUP)]
            self.assertEqual((decl.items, decl.tier, decl.loot_mode), (("molten_token_head",), tier, 1), lootid)
        self.assertEqual(self.tokens["molten_token_head"].slots, (1,))

    def test_the_avatar_list_is_group_two_of_the_emperors_heroic_lootid_at_loot_mode_2(self):
        decl = self.lists[(EMPEROR[1], HARD_MODE_GROUP)]
        self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                         (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, AVATAR_HARD_MODE))
        self.assertNotIn((EMPEROR[0], HARD_MODE_GROUP), self.lists)
        self.assertEqual(self.items["brd_ironfoe"].ladder.name, "vanilla_hard_mode")

    def test_the_dark_keeper_key_is_a_sure_drop_on_a_lit_avatar_kill_and_never_two(self):
        rows = [d for d in self.chances if d.lootid == EMPEROR[1]]
        by_mode = {d.loot_mode: d for d in rows}
        self.assertEqual(sorted(by_mode), [1, 2])
        self.assertEqual((by_mode[1].item_entry, by_mode[1].chance, by_mode[1].reference),
                         (DARK_KEEPER_KEY, 5.0, None))
        self.assertEqual((by_mode[2].item_entry, by_mode[2].chance, by_mode[2].reference),
                         (DARK_KEEPER_KEY, 95.0, 1700021))
        self.assertTrue(all(d.group == KEY_GROUP for d in rows))
        # a lit kill (loot mode 1 | 2) rolls both rows in turn: the chances sum to exactly 100 and the group yields one
        self.assertEqual(sum(d.chance for d in rows if d.loot_mode & 3), 100.0)
        # the normal difficulty's Emperor has the 5% row only
        normal = [d for d in self.chances if d.lootid == EMPEROR[0]]
        self.assertEqual([(d.chance, d.loot_mode) for d in normal], [(5.0, 1)])

    def test_moiras_stock_list_is_emptied_and_nothing_else_of_hers_is_touched(self):
        removal = self.group_removals[(MOIRA, LIST_GROUP)]
        self.assertEqual(set(removal.replaces_items), {12556, 12554, 12553, 12557})
        self.assertEqual([d for d in self.decls if d.lootid in (MOIRA, 10076) and d is not removal], [])
        # her four pieces are in the Emperor's list (two) and the Chest of The Seven (two)
        self.assertTrue({"brd_hands_of_the_exalted_herald", "brd_high_priestess_boots"} <= EMPEROR_LIST)
        self.assertEqual({12553, 12557} & CHEST_NORMAL_ENTRIES, {12553, 12557})

    # --- the keys --------------------------------------------------------------------------------------------------

    def test_the_dark_keeper_key_is_five_percent_on_the_five_wave_2_dwarf_bosses_on_both_lootids(self):
        rows = {(d.lootid, d.group): d for d in self.chances if d.loot_mode == 1}
        dwarves = [WAVE_2_BOSSES[n][:2] for n in WAVE_2_DWARF_BOSSES] + [PLUGGER, EMPEROR]
        expected = {(lootid, KEY_GROUP) for pair in dwarves for lootid in pair}
        self.assertEqual(set(rows), expected)
        for key, decl in rows.items():
            self.assertEqual((decl.item_entry, decl.chance, decl.reference), (DARK_KEEPER_KEY, 5.0, None), key)
        # not on Phalanx, Flamelash, Magmus, Ribbly or Moira (ruling 36); with wave 1's six that is the eleven bosses
        self.assertFalse({9502, 9156, 9938, RIBBLY[0], MOIRA} & {k[0] for k in rows})
        self.assertEqual(len(expected) // 2 + len(DWARF_BOSSES), 11)

    # --- the wave 2 rule (R-1-LOOT M-1) -----------------------------------------------------------------------------

    def test_every_heroic_boss_on_its_own_lootid_has_a_declaration(self):
        """Once BIND_WAVE_2 flips each `_boss(health, entry)` boss points at its own heroic lootid; a lootid with no
        declaration drops nothing at all (and lib/loot_tables.py errors on it). The nine wave 2 bosses are all here."""
        text = BRD_DUNGEON.read_text(encoding="utf-8")
        own = {int(m.group(1)) for m in re.finditer(r"\b\d+: _boss\([\d_]+, (\d+)[,)]", text)}
        declared = {d.lootid for d in self.every if not d.removal and d.listing or d.chance is not None}
        wave_1 = {v[1] for v in BOSSES.values()} | {THELDREN_HEROIC}
        wave_2 = {v[1] for v in WAVE_2_BOSSES.values()} | {RIBBLY[1], PLUGGER[1], EMPEROR[1]}
        self.assertEqual(wave_2, {310353, 310340, 310378, 310380, 310376, 310377, 310364, 310382, 310344})
        self.assertEqual(own, wave_1 | wave_2, "every `_boss(..., entry)` heroic boss is one of the 25 declared here")
        self.assertEqual(own - declared, set())

    def test_the_predicted_heroic_lootids_are_the_bosses_own_entries_in_blackrock_depths_py(self):
        text = BRD_DUNGEON.read_text(encoding="utf-8")
        pairs = {v[0]: v[1] for v in WAVE_2_BOSSES.values()}
        pairs.update({RIBBLY[0]: RIBBLY[1], PLUGGER[0]: PLUGGER[1], EMPEROR[0]: EMPEROR[1]})
        for normal, heroic in pairs.items():
            with self.subTest(normal=normal):
                m = re.search(rf"^\s*{normal}: _boss\([\d_]+, {heroic}[,)]", text, re.M)
                self.assertIsNotNone(m, f"{normal} -> lootid {heroic} in blackrock_depths.py")
        # the same numbers test_blackrock_depths_heroic.py pins (HEROIC_LOOTID) and the loot file's constants
        loot_text = (TOOL_ROOT / "source" / "items" / "blackrock_depths_loot.py").read_text(encoding="utf-8")
        for normal, heroic in pairs.items():
            self.assertRegex(loot_text, rf"\(?{normal}, {heroic}\b|{normal}_HEROIC|{heroic}", normal)

    def test_the_seven_and_the_priestess_have_no_loot_declaration(self):
        # the ghosts' lootid is 0; the High Priestess shares Moira's 8929 (emptied above)
        ghosts = {0, 9034, 9035, 9036, 9037, 9038, 9039, 9040, 10076}
        self.assertFalse({d.lootid for d in self.every if not d.pool_removal} & ghosts)

    # --- groups, references, counts --------------------------------------------------------------------------------

    def test_the_groups_and_loot_modes_of_wave_2(self):
        for key, decl in self.lists.items():
            with self.subTest(group=key):
                expected = {LIST_GROUP: 1, SIDE_POOL_GROUP: 1, TOKEN_GROUP: 1, HARD_MODE_GROUP: 2}[key[1]]
                self.assertEqual(decl.loot_mode, expected)
        groups = {g for _l, g in self.lists} | {d.group for d in self.chances}
        self.assertEqual(groups, {1, 2, 3, 4, 5})
        self.assertFalse({11, 12, 13} & groups)  # BRD is not flex
        self.assertEqual(sorted(k for k, d in self.lists.items() if d.loot_mode & L.LOOT_MODE_HARD_MODE_1),
                         [(310340, 2), (310344, 2)])

    def test_the_reference_pools_are_the_next_free_ids_of_the_loot_reference_block(self):
        used = sorted({d.reference for d in self.decls if d.reference is not None and not d.pool_removal})
        self.assertEqual(used, [1700019, 1700020, 1700021])
        text = IDS_YAML.read_text(encoding="utf-8")
        m = re.search(r"(?m)^loot_reference:\s*\n\s+start:\s*(\d+)\s*\n\s+end:\s*(\d+)", text)
        self.assertIsNotNone(m)
        self.assertTrue(int(m.group(1)) <= 1700019 and 1700021 <= int(m.group(2)))
        # nothing else in source/items takes them (BRS ends at 1700018)
        for path in sorted((TOOL_ROOT / "source" / "items").glob("*_loot.py")):
            if path.name == "blackrock_depths_loot.py":
                continue
            self.assertNotRegex(path.read_text(encoding="utf-8"), r"\b17000(19|20|21)\b", path.name)

    def test_declaration_counts(self):
        # lists: 6 bosses x 2 + Ribbly 2 + Plugger 2 + Emperor 2 = 18; tokens: Argelmach 2 + Emperor 2; hard mode 2
        self.assertEqual(len(self.lists), 18 + 4 + 2)
        # keys: Angerforge, Argelmach, Hurley, Plugger, Emperor x 2 lootids + the Avatar's hard mode row
        self.assertEqual(len(self.chances), 5 * 2 + 1)
        self.assertEqual(len(self.row_removals), 1)  # Plugger's group 1 rows
        self.assertEqual(len(self.group_removals), 1)  # Moira
        self.assertEqual(len(self.pool_removals), 1)  # the Emperor's stock reference 35014
        self.assertEqual(len(self.decls), len(self.lists) + len(self.chances) + 1 + 1 + 1)

    def test_the_stock_quest_key_and_reagent_rows_are_never_named(self):
        for d in self.decls:
            for entry in (*d.replaces_items, *d.rows):
                with self.subTest(decl=d.where, item=entry):
                    self.assertNotIn(entry, WAVE_2_STOCK_KEEP - PLUGGER_POOL_ROWS)

    def test_the_whole_dungeon_is_declared_between_both_waves_and_the_chest(self):
        """Every one of the 87 gear stage items is dropped somewhere: a creature list or hard mode group, or the Chest
        of The Seven (hand SQL, below); the split with L-1 is the approved 87."""
        declared = set()
        for decl in self.every:
            if decl.listing and decl.chance is None and not decl.removal:
                declared.update(k for k in decl.items if k in self.items)
        self.assertEqual(declared | set(CHEST_SEVEN), set(self.items))
        self.assertEqual(len(self.items), 87)
        self.assertEqual(len(declared), 81)
        self.assertFalse(declared & set(CHEST_SEVEN))
        wave_2_items = set().union(*(v[2] for v in WAVE_2_BOSSES.values()), EMPEROR_LIST, ARGELMACH_HARD_MODE,
                                   AVATAR_HARD_MODE, CHEST_SEVEN) - set(MINOR_POOL)
        self.assertEqual(len(wave_2_items), 29 + 6)  # the approved split: 29 list items + 6 hard mode, wave 2's own


def _lock_entries() -> dict[tuple[str, str], int]:
    entries = {}
    for line in ITEM_LOCK.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit() and "retired" not in parts:
            entries[(parts[1], parts[2])] = int(parts[0])
    return entries


class WaveTwoGameObjectLootRevTest(unittest.TestCase):
    """rev_loot_wave_2_blackrock_depths.sql: the Chest of The Seven (loot 12260, reference pool 12005)."""

    @classmethod
    def setUpClass(cls):
        cls.text = SQL_REV_2.read_text(encoding="utf-8")
        cls.lock = _lock_entries()
        pattern = re.compile(r"^\((\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+), '(.*)'\)[,;]$", re.M)
        cls.rows = []
        for m in pattern.finditer(cls.text):
            entry, item, ref, chance, quest, mode, group, mn, mx = map(int, m.groups()[:9])
            cls.rows.append(dict(entry=entry, item=item, ref=ref, chance=chance, quest=quest, mode=mode, group=group,
                                 min=mn, max=mx, comment=m.group(10)))

    def test_the_chest_pool_is_the_approved_six_at_both_tiers(self):
        pool = [r for r in self.rows if r["entry"] == 12005]
        normal = {r["item"] for r in pool if r["group"] == 1}
        heroic = {r["item"] for r in pool if r["group"] == 2}
        self.assertEqual(normal, CHEST_NORMAL_ENTRIES)
        self.assertEqual(normal, {self.lock[(key, "normal")] for key in CHEST_SEVEN})
        self.assertEqual(heroic, {self.lock[(key, "heroic")] for key in CHEST_SEVEN})
        self.assertEqual(len(pool), 12)
        for r in pool:
            self.assertEqual((r["ref"], r["chance"], r["quest"], r["min"], r["max"]), (0, 0, 0, 1, 1), r)
            self.assertEqual(r["mode"], r["group"], r)  # group 1 rolls at mode 1 (Normal), group 2 at mode 2 (Heroic)

    def test_the_cut_chest_items_are_gone(self):
        pool = {r["item"] for r in self.rows if r["entry"] == 12005}
        self.assertFalse(pool & {11921, 11925, 11927, 11929})  # Impervious Giant, Ghostshroud, Legplates, Leggings
        self.assertIn("DELETE FROM `reference_loot_template` WHERE `Entry` = 12005;", self.text)

    def test_the_chest_rolls_the_pool_twice_under_either_loot_mode(self):
        rows = [r for r in self.rows if r["entry"] == 12260]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["item"], r["ref"], r["chance"], r["mode"], r["group"], r["min"], r["max"]),
                         (12005, 12005, 0, 3, 1, 2, 2))
        self.assertIn("DELETE FROM `gameobject_loot_template` WHERE `Entry` = 12260;", self.text)

    def test_the_six_are_a_pool_of_at_least_two_equippable_distinct_items_per_tier(self):
        # two distinct picks need a pool of >= 2 per tier (lint_rows applies the same rule to DSL pools)
        for group in (1, 2):
            self.assertGreaterEqual(len([r for r in self.rows if r["entry"] == 12005 and r["group"] == group]), 2)

    def test_the_rev_matches_the_instance_loot_mode_request_in_its_comment(self):
        self.assertIn("SetLootMode", self.text)
        self.assertIn("GO_CHEST_SEVEN", self.text)

    def test_no_line_is_over_120_columns_and_there_is_no_trailing_whitespace(self):
        for number, line in enumerate(self.text.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)
        self.assertTrue(self.text.endswith("\n"))


if __name__ == "__main__":
    unittest.main()
