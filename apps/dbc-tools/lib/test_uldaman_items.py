"""
The Uldaman boss list items (wave 5 dungeon items): source/items/uldaman.py.

Checks:
  - the list: 49 items on the dungeon ladder, keys `uldaman_`, one declaration per stock entry (25 `base=` items,
    24 new), the bosses' counts (Revelosh 5, the Lost Dwarves 6, Ironaya 5, the Obsidian Sentinel 5, the Ancient Stone
    Keeper 5, Galgann Firehammer 6, Grimlok 6, the Stone Keepers 5, Archaedas 6);
  - the doc's stats: each item's primary and secondaries are exactly the stats docs/dungeons/uldaman-rework.md ## Loot
    "Proposal" names for it (Stamina is everywhere, so it is left out), and the counts the doc's Coverage notes print
    (Cooldown Haste 4, Proc Chance 5); when the nested docs repo is present, the dungeon doc's table and the loot copy
    docs/dungeons/dungeon-loot-vanilla.md "### Uldaman" are parsed and compared with this file's tables (names, boss,
    call, type, slot, stats);
  - the doc's type and slot: the look donor (`like=`) or the stock entry (`base=`) has the class, subclass and
    InventoryType the doc names, and no declaration overrides one; each relic is of its own kind (libram, totem, idol);
  - the Normal level of every item: a new item takes its boss's level (the highest stock item level of the stock items
    that stay on it, the Gnomeregan G1 B rule; the two new bosses a default) and required level the item level - 5, a
    stock item keeps its stock level (none is moved), every stock entry is Rare and Bind on Pickup already;
  - the two stock Uses (Horned Viking Helmet, Olaf's All Purpose Shield) keep their stock spell on a shorter item
    cooldown (3 min, the Gnomeregan G2 A ruling) on every tier;
  - every shape the list names exists, apart from the two pending shapes the integration adds;
  - jewelry carries secondaries only, the socket picks (trinkets, jewelry and Normal tiers never), new items Bind on
    Pickup with a look, every tier above Normal Bind on Pickup, the kept effects and the stock stat spells the budget
    absorbs, the cleared stock columns (random property), the declared multipliers, the Leather Tank extra Stamina, the
    no-ammo ranged weapons;
  - the materialized rows: every doc stat has a point on every tier (the Blackrock gear review's S3).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_uldaman_items.py
"""

from __future__ import annotations

import re
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl.items import NULL_PRIMARY_SHAPE, Quality, Socket  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, materialized_tier_stats,
)

R, B = Socket.RED, Socket.BLUE

# Bosses, in the keys this file uses.
REVELOSH, DWARVES, IRONAYA, SENTINEL, KEEPER, GALGANN, GRIMLOK, KEEPERS, ARCHAEDAS = (
    "Revelosh", "Dwarves", "Ironaya", "Sentinel", "Keeper", "Galgann", "Grimlok", "Keepers", "Archaedas")
# The Normal item level of a new item per boss (the Gnomeregan G1 B rule, 2026-11-26 live item_template): the highest
# stock item level of the stock items that stay on the boss (OWN_BOSS); the Obsidian Sentinel and the Stone Keepers have
# none (designer question 1: the next boss's, and between Grimlok and Archaedas). The Lost Dwarves get no new item.
# Required level is the item level - 5.
BOSS_LEVEL = {REVELOSH: 41, IRONAYA: 42, SENTINEL: 45, KEEPER: 45, GALGANN: 47, GRIMLOK: 47, KEEPERS: 47,
              ARCHAEDAS: 49}
REQUIRED_GAP = 5
BOSS_COUNT = {REVELOSH: 5, DWARVES: 6, IRONAYA: 5, SENTINEL: 5, KEEPER: 5, GALGANN: 6, GRIMLOK: 6, KEEPERS: 5,
              ARCHAEDAS: 6}

# key -> (boss, stock entry or None for a new item, the doc's stats in the doc's order).
LIST = {
    "uldaman_reveloshs_boots": (REVELOSH, 9387, "Str Haste Vers"),
    "uldaman_reveloshs_armguards": (REVELOSH, 9388, "Int Crit Proc"),
    "uldaman_reveloshs_spaulders": (REVELOSH, 9389, "Agi Mastery Crit"),
    "uldaman_reveloshs_gloves": (REVELOSH, 9390, "Int Proc"),
    "uldaman_wand_of_the_wild_surge": (REVELOSH, None, "Int Crit Haste"),
    "uldaman_baelogs_shortbow": (DWARVES, 9400, "Agi Crit"),
    "uldaman_nordic_longshank": (DWARVES, 9401, "Agi Haste Mastery"),
    "uldaman_horned_viking_helmet": (DWARVES, 9394, "Str Crit Mastery"),
    "uldaman_worn_running_boots": (DWARVES, 9398, "Agi Haste Vers"),
    "uldaman_olafs_all_purpose_shield": (DWARVES, 9404, "Str Block Vers"),
    "uldaman_battered_viking_shield": (DWARVES, 9403, "Int Haste Mastery"),
    "uldaman_stoneweaver_leggings": (IRONAYA, 9407, "Spi Haste Mastery"),
    "uldaman_ironshod_bludgeon": (IRONAYA, 9408, "Agi Dodge Vers"),
    "uldaman_ironayas_bracers": (IRONAYA, 9409, "Agi Crit Mastery"),
    "uldaman_girdle_of_the_makers_hammer": (IRONAYA, None, "Int Crit Mastery"),
    "uldaman_pendant_of_two_lights": (IRONAYA, None, "Haste Proc"),
    "uldaman_glass_black_greaves": (SENTINEL, None, "Str Parry Mastery Vers"),
    "uldaman_mirrorglass_mantle": (SENTINEL, None, "Int Vers Haste"),
    "uldaman_obsidian_shardblade": (SENTINEL, None, "Int Mastery Vers"),
    "uldaman_reforged_splinter": (SENTINEL, None, "Vers CDH"),
    "uldaman_directive_core": (SENTINEL, None, "Str CDH"),
    "uldaman_cragfists": (KEEPER, 9410, "Str Dodge Vers"),
    "uldaman_rockshard_pauldrons": (KEEPER, 9411, "Int Haste Crit"),
    "uldaman_duststorm_cloak": (KEEPER, None, "Agi Haste Crit"),
    "uldaman_sandscoured_wraps": (KEEPER, None, "Spi Crit Vers"),
    "uldaman_totem_of_the_turning_wind": (KEEPER, None, "Agi Haste"),
    "uldaman_galganns_fireblaster": (GALGANN, 9412, "Agi Haste"),
    "uldaman_galganns_firehammer": (GALGANN, 9419, "Int Haste Crit"),
    "uldaman_flameseer_mantle": (GALGANN, 11310, "Spi Crit Haste"),
    "uldaman_emberscale_cape": (GALGANN, 11311, "Int Crit CDH"),
    "uldaman_shadowforge_blast_vest": (GALGANN, None, "Agi Dodge Vers"),
    "uldaman_fuse_cutters_girdle": (GALGANN, None, "Agi Haste Mastery"),
    "uldaman_oilskin_leggings": (GRIMLOK, 9414, "Agi Crit Vers"),
    "uldaman_grimloks_tribal_vestments": (GRIMLOK, 9415, "Int Haste Vers"),
    "uldaman_grimloks_charge": (GRIMLOK, 9416, "Agi Haste Crit"),
    "uldaman_totemcarvers_gloves": (GRIMLOK, None, "Spi Haste Crit"),
    "uldaman_jadespine_collar": (GRIMLOK, None, "CDH Proc"),
    "uldaman_totem_of_the_trogg_king": (GRIMLOK, None, "Spi Haste"),
    "uldaman_breastplate_of_the_restless_ring": (KEEPERS, None, "Str Mastery Vers Crit"),
    "uldaman_granite_shell_bracers": (KEEPERS, None, "Str Parry Vers"),
    "uldaman_fault_line_sash": (KEEPERS, None, "Spi Mastery Vers"),
    "uldaman_keeper_trod_sabatons": (KEEPERS, None, "Agi Crit Vers"),
    "uldaman_idol_of_the_inheritance": (KEEPERS, None, "Agi Dodge"),
    "uldaman_the_rockpounder": (ARCHAEDAS, 9413, "Str Crit Haste"),
    "uldaman_stoneslayer": (ARCHAEDAS, 9418, "Str Mastery Vers Proc"),
    "uldaman_archaedic_stone": (ARCHAEDAS, 11118, "Crit Mastery"),
    "uldaman_disk_keepers_helm": (ARCHAEDAS, None, "Int Mastery Haste Crit"),
    "uldaman_hallshapers_chisel": (ARCHAEDAS, None, "Spi Crit Mastery"),
    "uldaman_libram_of_the_awakened_hall": (ARCHAEDAS, None, "Int Haste"),
}
NAMES = {
    "uldaman_reveloshs_boots": "Revelosh's Boots",
    "uldaman_reveloshs_armguards": "Revelosh's Armguards",
    "uldaman_reveloshs_spaulders": "Revelosh's Spaulders",
    "uldaman_reveloshs_gloves": "Revelosh's Gloves",
    "uldaman_wand_of_the_wild_surge": "Wand of the Wild Surge",
    "uldaman_baelogs_shortbow": "Baelog's Shortbow",
    "uldaman_nordic_longshank": "Nordic Longshank",
    "uldaman_horned_viking_helmet": "Horned Viking Helmet",
    "uldaman_worn_running_boots": "Worn Running Boots",
    "uldaman_olafs_all_purpose_shield": "Olaf's All Purpose Shield",
    "uldaman_battered_viking_shield": "Battered Viking Shield",
    "uldaman_stoneweaver_leggings": "Stoneweaver Leggings",
    "uldaman_ironshod_bludgeon": "Ironshod Bludgeon",
    "uldaman_ironayas_bracers": "Ironaya's Bracers",
    "uldaman_girdle_of_the_makers_hammer": "Girdle of the Makers' Hammer",
    "uldaman_pendant_of_two_lights": "Pendant of Two Lights",
    "uldaman_glass_black_greaves": "Glass-black Greaves",
    "uldaman_mirrorglass_mantle": "Mirrorglass Mantle",
    "uldaman_obsidian_shardblade": "Obsidian Shardblade",
    "uldaman_reforged_splinter": "Reforged Splinter",
    "uldaman_directive_core": "Directive Core",
    "uldaman_cragfists": "Cragfists",
    "uldaman_rockshard_pauldrons": "Rockshard Pauldrons",
    "uldaman_duststorm_cloak": "Duststorm Cloak",
    "uldaman_sandscoured_wraps": "Sandscoured Wraps",
    "uldaman_totem_of_the_turning_wind": "Totem of the Turning Wind",
    "uldaman_galganns_fireblaster": "Galgann's Fireblaster",
    "uldaman_galganns_firehammer": "Galgann's Firehammer",
    "uldaman_flameseer_mantle": "Flameseer Mantle",
    "uldaman_emberscale_cape": "Emberscale Cape",
    "uldaman_shadowforge_blast_vest": "Shadowforge Blast Vest",
    "uldaman_fuse_cutters_girdle": "Fuse-cutter's Girdle",
    "uldaman_oilskin_leggings": "Oilskin Leggings",
    "uldaman_grimloks_tribal_vestments": "Grimlok's Tribal Vestments",
    "uldaman_grimloks_charge": "Grimlok's Charge",
    "uldaman_totemcarvers_gloves": "Totemcarver's Gloves",
    "uldaman_jadespine_collar": "Jadespine Collar",
    "uldaman_totem_of_the_trogg_king": "Totem of the Trogg King",
    "uldaman_breastplate_of_the_restless_ring": "Breastplate of the Restless Ring",
    "uldaman_granite_shell_bracers": "Granite-shell Bracers",
    "uldaman_fault_line_sash": "Fault Line Sash",
    "uldaman_keeper_trod_sabatons": "Keeper-trod Sabatons",
    "uldaman_idol_of_the_inheritance": "Idol of the Inheritance",
    "uldaman_the_rockpounder": "The Rockpounder",
    "uldaman_stoneslayer": "Stoneslayer",
    "uldaman_archaedic_stone": "Archaedic Stone",
    "uldaman_disk_keepers_helm": "Disk-keeper's Helm",
    "uldaman_hallshapers_chisel": "Hallshaper's Chisel",
    "uldaman_libram_of_the_awakened_hall": "Libram of the Awakened Hall",
}
TYPES = {
    "uldaman_reveloshs_boots": ("Plate", "Feet"),
    "uldaman_reveloshs_armguards": ("Mail", "Wrist"),
    "uldaman_reveloshs_spaulders": ("Leather", "Shoulder"),
    "uldaman_reveloshs_gloves": ("Cloth", "Hands"),
    "uldaman_wand_of_the_wild_surge": ("Wand", "Ranged"),
    "uldaman_baelogs_shortbow": ("Bow", "Ranged"),
    "uldaman_nordic_longshank": ("Sword", "One-hand"),
    "uldaman_horned_viking_helmet": ("Plate", "Head"),
    "uldaman_worn_running_boots": ("Leather", "Feet"),
    "uldaman_olafs_all_purpose_shield": ("Shield", "Off-hand"),
    "uldaman_battered_viking_shield": ("Shield", "Off-hand"),
    "uldaman_stoneweaver_leggings": ("Cloth", "Legs"),
    "uldaman_ironshod_bludgeon": ("Staff", "Two-hand"),
    "uldaman_ironayas_bracers": ("Mail", "Wrist"),
    "uldaman_girdle_of_the_makers_hammer": ("Plate", "Waist"),
    "uldaman_pendant_of_two_lights": ("Neck", "Neck"),
    "uldaman_glass_black_greaves": ("Plate", "Legs"),
    "uldaman_mirrorglass_mantle": ("Cloth", "Shoulder"),
    "uldaman_obsidian_shardblade": ("Dagger", "One-hand"),
    "uldaman_reforged_splinter": ("Ring", "Finger"),
    "uldaman_directive_core": ("Trinket", "Trinket"),
    "uldaman_cragfists": ("Plate", "Hands"),
    "uldaman_rockshard_pauldrons": ("Mail", "Shoulder"),
    "uldaman_duststorm_cloak": ("Cloak", "Back"),
    "uldaman_sandscoured_wraps": ("Leather", "Wrist"),
    "uldaman_totem_of_the_turning_wind": ("Relic", "Relic"),
    "uldaman_galganns_fireblaster": ("Gun", "Ranged"),
    "uldaman_galganns_firehammer": ("Mace", "One-hand"),
    "uldaman_flameseer_mantle": ("Cloth", "Shoulder"),
    "uldaman_emberscale_cape": ("Cloak", "Back"),
    "uldaman_shadowforge_blast_vest": ("Leather", "Chest"),
    "uldaman_fuse_cutters_girdle": ("Mail", "Waist"),
    "uldaman_oilskin_leggings": ("Leather", "Legs"),
    "uldaman_grimloks_tribal_vestments": ("Cloth", "Chest"),
    "uldaman_grimloks_charge": ("Polearm", "Two-hand"),
    "uldaman_totemcarvers_gloves": ("Leather", "Hands"),
    "uldaman_jadespine_collar": ("Neck", "Neck"),
    "uldaman_totem_of_the_trogg_king": ("Relic", "Relic"),
    "uldaman_breastplate_of_the_restless_ring": ("Plate", "Chest"),
    "uldaman_granite_shell_bracers": ("Plate", "Wrist"),
    "uldaman_fault_line_sash": ("Leather", "Waist"),
    "uldaman_keeper_trod_sabatons": ("Mail", "Feet"),
    "uldaman_idol_of_the_inheritance": ("Relic", "Relic"),
    "uldaman_the_rockpounder": ("Mace", "Two-hand"),
    "uldaman_stoneslayer": ("Sword", "Two-hand"),
    "uldaman_archaedic_stone": ("Ring", "Finger"),
    "uldaman_disk_keepers_helm": ("Mail", "Head"),
    "uldaman_hallshapers_chisel": ("Mace", "One-hand"),
    "uldaman_libram_of_the_awakened_hall": ("Relic", "Relic"),
}
# The doc's (Type, Slot) -> the item_template (class, subclass, InventoryType) triples it allows.
DOC_TYPES = {
    ("Plate", "Head"): {(4, 4, 1)}, ("Plate", "Chest"): {(4, 4, 5)}, ("Plate", "Waist"): {(4, 4, 6)},
    ("Plate", "Legs"): {(4, 4, 7)}, ("Plate", "Feet"): {(4, 4, 8)}, ("Plate", "Wrist"): {(4, 4, 9)},
    ("Plate", "Hands"): {(4, 4, 10)},
    ("Mail", "Head"): {(4, 3, 1)}, ("Mail", "Shoulder"): {(4, 3, 3)}, ("Mail", "Wrist"): {(4, 3, 9)},
    ("Mail", "Waist"): {(4, 3, 6)}, ("Mail", "Feet"): {(4, 3, 8)},
    ("Leather", "Shoulder"): {(4, 2, 3)}, ("Leather", "Chest"): {(4, 2, 5)}, ("Leather", "Wrist"): {(4, 2, 9)},
    ("Leather", "Hands"): {(4, 2, 10)}, ("Leather", "Legs"): {(4, 2, 7)}, ("Leather", "Feet"): {(4, 2, 8)},
    ("Leather", "Waist"): {(4, 2, 6)},
    ("Cloth", "Shoulder"): {(4, 1, 3)}, ("Cloth", "Chest"): {(4, 1, 5), (4, 1, 20)}, ("Cloth", "Hands"): {(4, 1, 10)},
    ("Cloth", "Legs"): {(4, 1, 7)},
    ("Cloak", "Back"): {(4, 1, 16)}, ("Neck", "Neck"): {(4, 0, 2)}, ("Ring", "Finger"): {(4, 0, 11)},
    ("Trinket", "Trinket"): {(4, 0, 12)},
    ("Sword", "One-hand"): {(2, 7, 13)}, ("Dagger", "One-hand"): {(2, 15, 13)}, ("Mace", "One-hand"): {(2, 4, 13)},
    ("Mace", "Two-hand"): {(2, 5, 17)}, ("Sword", "Two-hand"): {(2, 8, 17)}, ("Staff", "Two-hand"): {(2, 10, 17)},
    ("Polearm", "Two-hand"): {(2, 6, 17)},
    ("Shield", "Off-hand"): {(4, 6, 14)},
    ("Wand", "Ranged"): {(2, 19, 26)}, ("Gun", "Ranged"): {(2, 3, 26)}, ("Bow", "Ranged"): {(2, 2, 15)},
    ("Relic", "Relic"): {(4, 7, 28), (4, 8, 28), (4, 9, 28)},
}
# The relics, by kind (item_template subclass): libram 7, idol 8, totem 9.
RELICS = {
    "uldaman_totem_of_the_turning_wind": 9, "uldaman_totem_of_the_trogg_king": 9,
    "uldaman_idol_of_the_inheritance": 8, "uldaman_libram_of_the_awakened_hall": 7,
}
# The dungeon doc's and the loot copy's Boss column spelling -> this file's boss keys (the two docs agree).
DOC_BOSS = {"Revelosh": REVELOSH, "The Lost Dwarves (one list)": DWARVES, "Ironaya": IRONAYA,
            "Obsidian Sentinel": SENTINEL, "Ancient Stone Keeper": KEEPER, "Galgann Firehammer": GALGANN,
            "Grimlok": GRIMLOK, "The Stone Keepers": KEEPERS, "Archaedas": ARCHAEDAS}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
# The doc's stat spelling -> this file's short names.
DOC_STATS = {"Strength": "Str", "Agility": "Agi", "Intellect": "Int", "Spirit": "Spi", "Crit": "Crit", "Haste": "Haste",
             "Mastery": "Mastery", "Versatility": "Vers", "Cooldown Haste": "CDH", "Proc Chance": "Proc",
             "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}
# The doc's Coverage notes: "more Cooldown Haste (4 items) and Proc Chance (5) than any wave 3 list". Block, Dodge and
# Parry are the list's own (Olaf's shield; the Bludgeon, Cragfists, the Vest and the Idol; the Greaves and the Bracers).
COVERAGE = {"CDH": 4, "Proc": 5, "Dodge": 4, "Parry": 2, "Block": 1}

# The two shapes the list needs that do not exist yet: the integration adds them in the pending itemization file. Each
# models an existing shape (the rules and the Even trio distribution come with it): Parry/Mastery/Versatility models
# Dodge/Parry/Mastery 100 (a Parry rule: a Strength primary), Mastery/Versatility/Proc models Haste/Mastery/Proc 95.
PENDING_SHAPES = {
    "Parry/Mastery/Versatility": (("Dodge/Parry/Mastery",), [14, 22, 23]),
    "Mastery/Versatility/Proc": (("Haste/Mastery/Proc",), [22, 23, 33]),
}
PENDING_USERS = {"Parry/Mastery/Versatility": {"uldaman_glass_black_greaves"},
                 "Mastery/Versatility/Proc": {"uldaman_stoneslayer"}}

# The 25 stock entries keep their stock row as the Normal tier.
STOCK_ENTRIES = {stock for _, stock, _ in LIST.values() if stock is not None}
# The Normal level (item level, required level) of every stock entry, from the live rows 2026-11-26 (handoff 1.2).
STOCK_LEVELS = {
    9387: (41, 40), 9388: (40, 35), 9389: (41, 36), 9390: (40, 35),
    9400: (41, 36), 9401: (43, 38), 9394: (42, 40), 9398: (40, 35), 9403: (40, 35), 9404: (42, 37),
    9407: (40, 35), 9408: (42, 37), 9409: (42, 37),
    9410: (45, 40), 9411: (45, 40),
    9412: (47, 40), 9419: (46, 40), 11310: (47, 40), 11311: (46, 40),
    9414: (46, 40), 9415: (47, 40), 9416: (47, 40),
    9413: (49, 40), 9418: (49, 40), 11118: (47, 40),
}
# The stock entries that carry a random property today (cleared: the shape gives the stats): entry -> property id.
STOCK_RANDOM_PROPERTY = {9387: 863, 9388: 1094, 9389: 1157, 9390: 716, 9409: 1096, 9410: 782, 11118: 3484}

# One socketed standalone piece per boss (the doc names none: designer question). The first socket is red, blue on tank
# gear; the bonuses are stock +4 ratings (2874 Crit, 3267 Haste, 2871 Dodge, 3359 Parry).
SOCKETS = {
    "uldaman_reveloshs_spaulders": (R,),          # Revelosh, Leather Agility shoulder
    "uldaman_worn_running_boots": (R,),           # the Lost Dwarves, Leather Agility feet
    "uldaman_girdle_of_the_makers_hammer": (R,),  # Ironaya, Plate Intellect waist
    "uldaman_glass_black_greaves": (B,),          # the Obsidian Sentinel, Plate Tank legs
    "uldaman_rockshard_pauldrons": (R,),          # the Ancient Stone Keeper, Mail Intellect shoulder
    "uldaman_shadowforge_blast_vest": (B,),       # Galgann, Leather Tank chest
    "uldaman_totemcarvers_gloves": (R,),          # Grimlok, Leather Spirit hands
    "uldaman_breastplate_of_the_restless_ring": (R,),  # the Stone Keepers, Plate Strength chest
    "uldaman_disk_keepers_helm": (R,),            # Archaedas, Mail Intellect head
}
BONUS = {
    "uldaman_reveloshs_spaulders": 2874, "uldaman_worn_running_boots": 3267,
    "uldaman_girdle_of_the_makers_hammer": 2874, "uldaman_glass_black_greaves": 3359,
    "uldaman_rockshard_pauldrons": 2874, "uldaman_shadowforge_blast_vest": 2871,
    "uldaman_totemcarvers_gloves": 3267, "uldaman_breastplate_of_the_restless_ring": 2874,
    "uldaman_disk_keepers_helm": 3267,
}
TANK_SOCKETS = {"uldaman_glass_black_greaves", "uldaman_shadowforge_blast_vest"}
TRINKETS = {"uldaman_directive_core"}
# Rings and the two necks: secondaries only.
JEWELRY = {"uldaman_pendant_of_two_lights", "uldaman_reforged_splinter", "uldaman_jadespine_collar",
           "uldaman_archaedic_stone"}
RELIC_KEYS = set(RELICS)
# Kept stock effects: key -> ((spell id, trigger) per slot), the live item_template 2026-11-26 (trigger 0 Use, 1 Equip,
# 2 Chance on hit).
KEPT_EFFECTS = {
    "uldaman_galganns_fireblaster": ((29633, 1),),     # Equip, Fire Blast (a ranged proc passive, 3 ppm)
    "uldaman_galganns_firehammer": ((18083, 2),),      # Chance on hit, Firebolt
    "uldaman_stoneslayer": ((12731, 2),),              # Chance on hit, Strength of Stone
    "uldaman_horned_viking_helmet": ((22641, 0),),     # Use, Reckless Charge
    "uldaman_olafs_all_purpose_shield": ((12438, 0),),  # Use, Slow Fall
}
# The two stock Uses declared again with a shorter item cooldown (the Gnomeregan G2 A ruling): key -> the slot's
# item_template columns (spellcooldown, spellcategory, spellcategorycooldown) on every tier. The stock rows:
# 1,800,000 / 0 / 0 and 3,600,000 / 0 / 0.
USE_COOLDOWNS = {
    "uldaman_horned_viking_helmet": (180000, 0, 0),
    "uldaman_olafs_all_purpose_shield": (180000, 0, 0),
}
# Stock stat spells the budget absorbs (the default): key -> the spell id (Attack Power, the dead stat).
ABSORBED = {"uldaman_rockshard_pauldrons": 9335, "uldaman_grimloks_charge": 9331}
# Columns the declaration sets beyond the look (key -> columns), besides `bonding` on a new item.
CLEARED = {
    **{f"uldaman_{name}": {"RandomProperty": 0} for name in (
        "reveloshs_boots", "reveloshs_armguards", "reveloshs_spaulders", "reveloshs_gloves", "ironayas_bracers",
        "cragfists", "archaedic_stone")},
    "uldaman_baelogs_shortbow": {"ammo_type": 0}, "uldaman_galganns_fireblaster": {"ammo_type": 0},
}
# The three caster one-hand main-hands (their level is below 60) take the 60-100 physical cell on every tier, the
# Firehammer times the effect discount; the bow (below 60) takes the 60-100 bow cell.
DECLARED_MULTS = {
    "uldaman_obsidian_shardblade": 0.445, "uldaman_hallshapers_chisel": 0.445, "uldaman_galganns_firehammer": 0.3115,
    "uldaman_baelogs_shortbow": 0.405,
}
CASTER_MAIN_HANDS = {"uldaman_obsidian_shardblade", "uldaman_hallshapers_chisel", "uldaman_galganns_firehammer"}
EXTRA_STAMINA = {"uldaman_shadowforge_blast_vest": 0.25}  # the Leather Tank piece

RESISTANCES = ("holy_res", "fire_res", "nature_res", "frost_res", "shadow_res", "arcane_res")
TIERS = {"normal", "heroic", "empowered_1", "empowered_2", "empowered_3"}


def _boss_levels(boss: str) -> tuple[int, int]:
    """(item level, required level) of a new item on `boss`."""
    return BOSS_LEVEL[boss], BOSS_LEVEL[boss] - REQUIRED_GAP


def stat_names(decl) -> set[str]:
    """The stats a declaration's shapes name, as the doc spells them (Stamina left out)."""
    names = set()
    for shape in (decl.primary, decl.secondary):
        if shape is None or shape == NULL_PRIMARY_SHAPE:
            continue
        for part in shape.replace(" (Solo)", "").replace(" (Any)", "").split("/"):
            names.add(part.strip())
    return names


def _short(stats_cell: str) -> set[str]:
    """{short stat names} of a doc stats cell ("Strength, Haste; keeps its proc" -> {Str, Haste})."""
    return {DOC_STATS[s.strip()] for s in stats_cell.split(";")[0].split(",")}


def _table(path: Path, start_re: str, stop_re: str, width: int) -> list[list[str]]:
    """The rows (cell lists) of the markdown table that follows the line matching `start_re`."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if re.match(start_re, line))
    rows = []
    for line in lines[start + 1:]:
        if re.match(stop_re, line):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < width or cells[0] in ("Slot", "Boss", "Item") or set(cells[0]) <= {"-", " "}:
            continue
        rows.append(cells)
    return rows


def _with_pending_shapes():
    """`item_variants.load_itemization_tables` as it is, plus the pending shapes (PENDING_SHAPES) that the catalog does
    not have yet, modeled on an existing shape. After the integration adds them this changes nothing."""
    from lib import item_variants  # noqa: PLC0415

    real = item_variants.load_itemization_tables

    def patched():
        tables, catalog = real()
        names = {shape["name"] for shape in catalog.values()}
        for name, (model_names, stats) in PENDING_SHAPES.items():
            if name in names:
                continue
            model = next(shape for shape in catalog.values() if shape["name"] in model_names)
            shape_id = max(catalog) + 1
            catalog[shape_id] = {**model, "shape_id": shape_id, "name": name, "stats": list(stats)}
        return tables, catalog

    return mock.patch.object(item_variants, "load_itemization_tables", patched)


def resolved_tier_rows(decls: dict) -> dict:
    """{item key: {tier name: item_template row}}: each tier's row before the stats, as generate.py builds it from the
    stock row or the look, the declared columns and the tier's overrides (`item_emit._tier_row`; no id is minted)."""
    from lib import item_emit, item_variants  # noqa: PLC0415

    tables, catalog = item_variants.load_itemization_tables()
    live_rows = id_blocks.spell_tables.load_live_item_template_rows()
    cells = item_variants.FrozenRoleCells(
        item_variants.RoleCells(), item_variants.parse_cells_lock(item_variants.CELLS_LOCK_PATH.read_text()),
    )
    shape_index = item_variants._shape_index(catalog)
    columns = tuple(id_blocks.spell_tables.ITEM_TEMPLATE_COLUMNS)
    defaults = id_blocks.spell_tables.ITEM_TEMPLATE_DEFAULTS
    out = {}
    for key, decl in decls.items():
        errors = []
        result = item_variants._resolve_item(decl, live_rows, tables, catalog, shape_index, columns, errors, [], cells)
        if result is None or errors:
            raise AssertionError(f"{key}: does not resolve: {errors}")
        item, plans = result
        out[key] = {}
        for plan in plans:
            spec = plan["spec"]
            tier = item_variants.ResolvedTier(
                key=key, tier=spec.name, label=spec.label, entry=decl.base if plan["first"] and decl.base else 0,
                stock=plan["first"] and decl.base is not None, ilvl=plan["ilvl"], quality=plan["quality"],
                required_level=plan["required"], heroic_flag=spec.heroic_flag, variant_base=None,
                itemization=plan["itemization"], columns=plan["columns"], sockets=plan["sockets"])
            out[key][spec.name], _ = item_emit._tier_row(item, tier, defaults, columns)
    return out


class UldamanItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations
                     if e["id"].startswith("uldaman_") and e["_decl"].ladder.name == "vanilla_dungeon"}
        cls.rows = id_blocks.spell_tables.load_live_item_template_rows()

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(LIST))
        self.assertEqual(set(self.decls), set(NAMES))
        self.assertEqual(set(self.decls), set(TYPES))
        self.assertEqual(len(self.decls), 49)
        counts = {}
        for boss, _, _ in LIST.values():
            counts[boss] = counts.get(boss, 0) + 1
        self.assertEqual(counts, BOSS_COUNT)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))  # one declaration per stock entry
        self.assertEqual(set(bases), STOCK_ENTRIES)
        self.assertEqual(len(bases), 25)
        self.assertEqual(len(self.decls) - len(bases), 24)  # 24 new items
        for key, decl in self.decls.items():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon", key)
            self.assertEqual(decl.base, LIST[key][1], key)

    def test_no_other_list_declaration(self):
        """Every list key is on the dungeon ladder; the hard mode items are another file's."""
        other = [e["id"] for e in self.reg.item_declarations
                 if e["id"].startswith("uldaman_") and e["_decl"].ladder.name != "vanilla_dungeon"]
        for key in other:
            self.assertNotIn(key, LIST)

    def test_the_doc_stats(self):
        for key, (_, _, stats) in LIST.items():
            wanted = {STAT_NAMES[s] for s in stats.split()}
            decl = self.decls[key]
            self.assertEqual(stat_names(decl), wanted, key)
            # a primary shape names exactly one primary; a secondary shape only secondaries
            if decl.primary is not None:
                self.assertEqual(len(stat_names(decl) & PRIMARIES), 1, key)
            else:
                self.assertEqual(len(stat_names(decl) & PRIMARIES), 0, key)
            self.assertFalse(
                set(decl.secondary.replace(" (Solo)", "").replace(" (Any)", "").split("/")) & PRIMARIES, key)

    def test_the_doc_coverage_counts(self):
        """The doc's Coverage notes: Cooldown Haste 4 items and Proc Chance 5 (the rest are this list's own counts)."""
        counts = {}
        for _, _, stats in LIST.values():
            for stat in stats.split():
                if stat in COVERAGE:
                    counts[stat] = counts.get(stat, 0) + 1
        self.assertEqual(counts, COVERAGE)

    def test_the_doc_tables_when_present(self):
        """The dungeon doc's Proposal table and the dungeon-loot copy, parsed: names, boss, call, type, slot and stats
        equal this file's tables. The docs/ checkout is a nested private repo and may be absent (CI): a skip."""
        main = REPO_ROOT / "docs" / "dungeons" / "uldaman-rework.md"
        copy = REPO_ROOT / "docs" / "dungeons" / "dungeon-loot-vanilla.md"
        if not main.is_file() or not copy.is_file():
            self.skipTest("docs/dungeons/uldaman-rework.md is not checked out here")
        by_name = {name: key for key, name in NAMES.items()}
        # both tables: Boss | Item | Call | Type | Slot | Stats
        parsed = {}
        for cells in _table(main, r"^### Proposal \(approved", r"^\*\*Hard mode", 6):
            boss, item, call, kind, slot, stats = cells[:6]
            parsed[item.strip("*")] = (DOC_BOSS[boss], call, kind, slot, _short(stats), item.startswith("**"))
        self.assertEqual(set(parsed), set(by_name))
        copied = {}
        for cells in _table(copy, r"^### Uldaman\s*$", r"^\*\*Hard mode", 6):
            boss, item, call, kind, slot, stats = cells[:6]
            copied[item.strip("*")] = (DOC_BOSS[boss], call, kind, slot, _short(stats), item.startswith("**"))
        self.assertEqual(parsed, copied)  # the two docs agree on every row
        for name, (boss, call, kind, slot, stats, bold) in parsed.items():
            key = by_name[name]
            self.assertEqual(boss, LIST[key][0], key)
            self.assertEqual(call == "Alter", LIST[key][1] is not None, key)
            self.assertEqual(bold, LIST[key][1] is None, key)  # the new items are the bold rows
            self.assertEqual((kind, slot), TYPES[key], key)
            self.assertEqual(stats, set(LIST[key][2].split()), key)

    def test_type_and_slot(self):
        """like= and base= bring class, subclass and InventoryType: every donor or stock row is of the doc's type, and
        no declaration overrides one. Each relic is of its own kind."""
        for key, decl in self.decls.items():
            row = self.rows[decl.base if decl.base is not None else decl.like]
            got = (int(row["class"]), int(row["subclass"]), int(row["InventoryType"]))
            self.assertIn(got, DOC_TYPES[TYPES[key]], key)
            self.assertFalse({"class", "subclass", "InventoryType"} & set(dict(decl.columns)), key)
            if key in RELICS:
                self.assertEqual(got[1], RELICS[key], key)
        self.assertEqual({k for k, t in TYPES.items() if t == ("Relic", "Relic")}, RELIC_KEYS)

    def test_stock_names(self):
        """A stock entry's live name is the doc's; a new item's name is free in the live item_template."""
        minted = _minted_entries()  # after the write run the new items are live under their own names
        names = {row["name"] for entry, row in self.rows.items() if entry not in minted}
        for key, decl in self.decls.items():
            if decl.base is not None:
                self.assertEqual(self.rows[decl.base]["name"], NAMES[key], key)
            else:
                self.assertNotIn(NAMES[key], names, key)

    # --- levels ---------------------------------------------------------------------------------------------------

    def test_new_items(self):
        for key, decl in self.decls.items():
            if decl.base is not None:
                continue
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # a new boss item binds on pickup
            self.assertIsNotNone(decl.like, key)
            self.assertEqual(decl.name, NAMES[key], key)
            self.assertEqual(decl.ilvl, BOSS_LEVEL[LIST[key][0]], key)  # the boss's level (G1 B)
            self.assertIsNone(decl.required_level, key)  # defaults to the item level - 5
            self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_stock_levels(self):
        """A stock item keeps its stock level, required level and quality: none is moved, so no declaration sets a level
        or a quality; every stock row is Rare and Bind on Pickup already."""
        self.assertEqual(set(STOCK_LEVELS), STOCK_ENTRIES)
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            row = self.rows[decl.base]
            self.assertEqual((int(row["ItemLevel"]), int(row["RequiredLevel"])), STOCK_LEVELS[decl.base], key)
            self.assertIsNone(decl.ilvl, key)
            self.assertIsNone(decl.required_level, key)
            self.assertIsNone(decl.quality, key)
            self.assertEqual(int(row["Quality"]), 3, key)
            self.assertEqual(int(row["bonding"]), 1, key)
            self.assertEqual(decl.overrides, (), key)  # nothing to turn into Bind on Pickup on the higher tiers

    def test_boss_levels(self):
        """Each boss's level is the highest stock level of its own stock items; the two new bosses have none (the
        defaults: the Obsidian Sentinel the Ancient Stone Keeper's 45, the Stone Keepers 47 between Grimlok and
        Archaedas); the Lost Dwarves get no new item."""
        for boss, level in BOSS_LEVEL.items():
            own = [STOCK_LEVELS[s][0] for k, (b, s, _) in LIST.items() if b == boss and s is not None]
            if own:
                self.assertEqual(level, max(own), boss)
        self.assertEqual({b for b, s, _ in LIST.values() if s is None}, set(BOSS_LEVEL))
        self.assertNotIn(DWARVES, BOSS_LEVEL)
        self.assertEqual(BOSS_LEVEL[SENTINEL], BOSS_LEVEL[KEEPER])
        self.assertTrue(BOSS_LEVEL[GRIMLOK] <= BOSS_LEVEL[KEEPERS] <= BOSS_LEVEL[ARCHAEDAS])

    def test_resolved_normal_level(self):
        """Each Normal tier row: item level and required level as the rule says, quality Rare."""
        with _with_pending_shapes():
            rows = resolved_tier_rows(self.decls)
        for key, decl in self.decls.items():
            normal = rows[key]["normal"]
            want = _boss_levels(LIST[key][0]) if decl.base is None else STOCK_LEVELS[decl.base]
            self.assertEqual((int(normal["ItemLevel"]), int(normal["RequiredLevel"])), want, key)
            self.assertEqual(int(normal["Quality"]), 3, key)
            self.assertEqual({tier: int(row["ItemLevel"]) for tier, row in rows[key].items() if tier != "normal"},
                             {"heroic": 66, "empowered_1": 76, "empowered_2": 86, "empowered_3": 96}, key)

    # --- shapes, jewelry ------------------------------------------------------------------------------------------

    def test_shapes_exist(self):
        from lib import item_variants  # noqa: PLC0415

        _, catalog = item_variants.load_itemization_tables()
        known = {shape["name"] for shape in catalog.values()} | set(PENDING_SHAPES)
        used = set()
        for key, decl in self.decls.items():
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    self.assertIn(name, known, f"{key}: {name}")
                    used.add(name)
        # every pending shape is used by the list (a dead entry would hide a typo) and nothing else is missing
        self.assertTrue(set(PENDING_SHAPES) <= used)
        for name, users in PENDING_USERS.items():
            self.assertEqual({k for k, d in self.decls.items() if d.secondary == name}, users, name)

    def test_secondary_split(self):
        """The doc's script check (ruling 35): 17% one secondary, 73% two, 10% three over the 52 items with the hard
        mode list (the three hard mode items: 1, 2 and 3 secondaries). Printed by the report; asserted as the count
        of the list's own items by number of secondaries (Stamina is not one)."""
        by_count = {}
        for key, (_, _, stats) in LIST.items():
            secondaries = [s for s in stats.split() if s not in ("Str", "Agi", "Int", "Spi")]
            by_count.setdefault(len(secondaries), []).append(key)
        # the hard mode items add one 1-secondary (Waking Stone), one 2 (Choker) and one 3 (Fragment of the Disks)
        total = len(LIST) + 3
        self.assertEqual(total, 52)
        one, two, three = (len(by_count.get(n, [])) for n in (1, 2, 3))
        self.assertEqual(one + two + three, len(LIST))
        self.assertEqual((round(100 * (one + 1) / total), round(100 * (two + 1) / total),
                          round(100 * (three + 1) / total)), (17, 73, 10))

    def test_jewelry(self):
        for key in JEWELRY:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
            self.assertNotRegex(decl.secondary, r"Dodge|Parry|Block|MP5", key)
        for key, decl in self.decls.items():
            if decl.primary is None:
                self.assertIn(key, JEWELRY, key)
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)
            self.assertEqual(TYPES[key][1] in ("Finger", "Neck"), key in JEWELRY, key)
        for key in TRINKETS:  # the one trinket is stat-only with the doc's primary
            self.assertEqual(self.decls[key].primary, "Strength (Solo)", key)
            self.assertEqual(self.decls[key].secondary, "CDH (Solo)", key)
            self.assertIsNone(self.decls[key].spells, key)

    def test_tank_pieces(self):
        """Dodge, Parry and Block go on tank gear only: strength or agility primary (the shape rules check the rest)."""
        tank = set()
        for key, decl in self.decls.items():
            if re.search(r"Dodge|Parry|Block", decl.secondary):
                tank.add(key)
                self.assertIn(decl.primary, ("Strength (Solo)", "Agility (Solo)"), key)
        self.assertEqual(tank, {
            "uldaman_olafs_all_purpose_shield", "uldaman_ironshod_bludgeon", "uldaman_glass_black_greaves",
            "uldaman_cragfists", "uldaman_shadowforge_blast_vest", "uldaman_granite_shell_bracers",
            "uldaman_idol_of_the_inheritance"})
        # the stock fixes the doc names: Defense goes (Cragfists, Olaf's shield, the Battered shield), the Plate Agility
        # helm is Strength, the Strength staff the Agility tank staff, the shield pair a tank and a caster shield
        self.assertEqual(self.decls["uldaman_horned_viking_helmet"].primary, "Strength (Solo)")
        self.assertEqual(self.decls["uldaman_ironshod_bludgeon"].primary, "Agility (Solo)")
        self.assertEqual(self.decls["uldaman_ironshod_bludgeon"].secondary, "Dodge/Versatility")
        self.assertEqual(self.decls["uldaman_olafs_all_purpose_shield"].secondary, "Block/Versatility")
        self.assertEqual(self.decls["uldaman_battered_viking_shield"].primary, "Intellect (Solo)")

    # --- sockets, columns, effects --------------------------------------------------------------------------------

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        self.assertEqual({k: d.socket_bonus for k, d in self.decls.items() if d.sockets}, BONUS)
        for key in TRINKETS | JEWELRY | RELIC_KEYS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets, jewelry and relics never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
            if decl.sockets:
                self.assertIn(decl.socket_bonus, (2874, 3267, 2871, 3359), key)  # a stock +4 Crit/Haste/Dodge/Parry
                self.assertEqual(len(decl.sockets), 1, key)  # no two-hander is socketed: one socket each
                self.assertNotIn(TYPES[key][1], ("Two-hand", "Off-hand"), key)
        # exactly one socketed piece per boss
        per_boss = {}
        for key in SOCKETS:
            per_boss[LIST[key][0]] = per_boss.get(LIST[key][0], 0) + 1
        self.assertEqual(per_boss, {boss: 1 for boss in BOSS_COUNT})
        # the tank pieces are blue, the damage and healing pieces red
        for key, sockets in SOCKETS.items():
            self.assertEqual(sockets, (B,) if key in TANK_SOCKETS else (R,), key)

    def test_column_edits(self):
        """The list changes no stock entry's class, subclass or slot; the only columns a declaration sets are the
        cleared ones (a random property, a ranged weapon's ammo) and, on a new item, Bind on Pickup."""
        for key, decl in self.decls.items():
            columns = dict(decl.columns)
            if decl.base is not None:
                self.assertEqual(columns, CLEARED.get(key, {}), key)
            else:
                self.assertEqual(columns, {"bonding": 1, **CLEARED.get(key, {})}, key)
        # every other stock row has no random property, suffix, resistance, set or limit category to clear
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            row = self.rows[decl.base]
            if "RandomProperty" not in CLEARED.get(key, {}):
                self.assertEqual(int(row["RandomProperty"]), 0, key)
            self.assertEqual(int(row["RandomSuffix"]), 0, key)
            self.assertEqual(int(row["itemset"]), 0, key)
            # 0 before the write run; after it, the category the run minted for the item
            self.assertGreaterEqual(int(row["ItemLimitCategory"]), 0, key)
            for column in RESISTANCES:
                self.assertEqual(int(row[column]), 0, f"{key} {column}")
        # the seven cleared random properties are exactly the stock rows that carry one
        self.assertEqual({d.base for k, d in self.decls.items() if "RandomProperty" in CLEARED.get(k, {})},
                         set(STOCK_RANDOM_PROPERTY))
        if not _minted_entries():  # after the write run the live rows are already cleared
            for entry, value in STOCK_RANDOM_PROPERTY.items():
                self.assertEqual(int(self.rows[entry]["RandomProperty"]), value, entry)
        self.assertEqual({k: d.extra_stamina for k, d in self.decls.items() if d.extra_stamina}, EXTRA_STAMINA)

    def test_stoneslayer_class_mask_restricts_nothing(self):
        """Stoneslayer's stock AllowableClass 1535 is the all-classes mask (every WotLK class bit: 1-9 and 11), so the
        item stays as stock; no other list row carries a class restriction."""
        all_classes = sum(1 << (c - 1) for c in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11))
        self.assertEqual(all_classes, 1535)
        self.assertEqual(int(self.rows[9418]["AllowableClass"]), 1535)
        for key, decl in self.decls.items():
            if decl.base is not None:
                self.assertIn(int(self.rows[decl.base]["AllowableClass"]), (-1, 1535), key)
            self.assertNotIn("AllowableClass", dict(decl.columns), key)

    def test_binding(self):
        """Bind on Pickup on every tier: the stock rows already are, a new item is declared so, and no declaration needs
        a per-tier override."""
        with _with_pending_shapes():
            rows = resolved_tier_rows(self.decls)
        for key, decl in self.decls.items():
            self.assertEqual(set(rows[key]), TIERS, key)
            for tier, row in rows[key].items():
                self.assertEqual(int(row["bonding"]), 1, f"{key} {tier}")

    def test_ranged_weapons_need_no_ammo(self):
        """The stock bow and gun set ammo_type 0 (hunter rework Q3); the wand needs none."""
        for key in ("uldaman_baelogs_shortbow", "uldaman_galganns_fireblaster"):
            decl = self.decls[key]
            self.assertEqual(dict(decl.columns)["ammo_type"], 0, key)
            self.assertIn(int(self.rows[decl.base]["subclass"]), (2, 3), key)  # bow, gun
        ranged = {k for k, t in TYPES.items() if t[1] == "Ranged"}
        self.assertEqual(ranged, {"uldaman_baelogs_shortbow", "uldaman_galganns_fireblaster",
                                  "uldaman_wand_of_the_wild_surge"})

    def test_kept_effects(self):
        """Five stock effects are kept (the stock spells, same on every tier): three through `keep_spells`, the two Uses
        declared again with a shorter item cooldown; the two stock Attack Power spells fold into the budget; no other
        declaration writes its own spells."""
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, set(KEPT_EFFECTS) - set(USE_COOLDOWNS))
        self.assertEqual({k for k, d in self.decls.items() if d.spells is not None}, set(USE_COOLDOWNS))
        for key in USE_COOLDOWNS:  # the stock spell and trigger, nothing scaled
            self.assertEqual(tuple((s.spell_id, int(s.trigger)) for s in self.decls[key].spells), KEPT_EFFECTS[key])
            self.assertTrue(all(s.scale is None and s.charges == 0 for s in self.decls[key].spells), key)
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            row = self.rows[decl.base]
            spells = tuple((int(row[f"spellid_{n}"]), int(row[f"spelltrigger_{n}"])) for n in range(1, 6)
                           if int(row[f"spellid_{n}"]))
            if key in KEPT_EFFECTS:
                self.assertEqual(spells, KEPT_EFFECTS[key], key)
            elif key in ABSORBED:
                self.assertEqual(spells, ((ABSORBED[key], 1),), key)  # absorbed by the budget (the default)
            else:
                self.assertEqual(spells, (), key)  # nothing to absorb or keep
        for key in USE_COOLDOWNS:  # the stock cooldowns are the long ones (30 and 60 minutes)
            self.assertEqual(int(self.rows[self.decls[key].base]["spellcooldown_1"]),
                             {"uldaman_horned_viking_helmet": 1800000,
                              "uldaman_olafs_all_purpose_shield": 3600000}[key], key)
        # the new items carry no effect (stat-only trinket and relics included)
        for key, decl in self.decls.items():
            if decl.base is None:
                self.assertIsNone(decl.spells, key)
                self.assertFalse(decl.keep_spells, key)

    def test_the_spell_slots_on_every_tier(self):
        """Every tier: a kept effect is the stock slot (id and trigger) and keeps its slot (nothing absorbed), the stock
        Attack Power spell of the Pauldrons and the Charge is absorbed into the budget (`absorbed_spell_slots` 1); a
        kept effect item pays less than the full budget for its effect (`budget_mult` below its no-effect twin), apart
        from the Firehammer, whose declared multiplier already is the discounted cell."""
        from lib import item_variants  # noqa: PLC0415

        picked = {k: self.decls[k] for k in (*KEPT_EFFECTS, *ABSORBED)}
        with _with_pending_shapes():
            rows = resolved_tier_rows(picked)
            tables, catalog = item_variants.load_itemization_tables()
            cells = item_variants.FrozenRoleCells(
                item_variants.RoleCells(),
                item_variants.parse_cells_lock(item_variants.CELLS_LOCK_PATH.read_text()))
            index = item_variants._shape_index(catalog)
            columns = tuple(id_blocks.spell_tables.ITEM_TEMPLATE_COLUMNS)

            def plans(decl):
                errors = []
                result = item_variants._resolve_item(
                    decl, self.rows, tables, catalog, index, columns, errors, [], cells)
                self.assertEqual(errors, [])
                return [p["itemization"] for p in result[1]]

            for key, decl in picked.items():
                with_effect = plans(decl)
                twin = plans(replace(decl, keep_spells=False, spells=None))  # the stock spells absorbed instead
                for tier, row in rows[key].items():
                    got = tuple((int(row[f"spellid_{n}"]), int(row[f"spelltrigger_{n}"])) for n in range(1, 6)
                                if int(row[f"spellid_{n}"]))
                    if key in KEPT_EFFECTS:
                        self.assertEqual(got, KEPT_EFFECTS[key], f"{key} {tier}")
                    if key in USE_COOLDOWNS:
                        self.assertEqual((int(row["spellcooldown_1"]), int(row["spellcategory_1"]),
                                          int(row["spellcategorycooldown_1"])), USE_COOLDOWNS[key], f"{key} {tier}")
                for a, b in zip(with_effect, twin):
                    if key in KEPT_EFFECTS:
                        self.assertEqual(a["absorbed_spell_slots"], 0, key)
                        self.assertEqual(b["absorbed_spell_slots"], 1, key)
                        if decl.budget_mult is None:
                            self.assertLess(float(a["budget_mult"]), float(b["budget_mult"]), key)  # the discount
                        else:
                            self.assertEqual(float(a["budget_mult"]), decl.budget_mult, key)
                    else:
                        self.assertEqual(a["absorbed_spell_slots"], 1, key)

    def test_declared_multipliers(self):
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)
        # the caster one-hand main-hands (InventoryType 13, a caster primary) take the 60-100 physical cell (the
        # Firehammer times the 0.7 effect discount); the bow (InventoryType 15) takes the 60-100 bow cell
        for key in CASTER_MAIN_HANDS:
            decl = self.decls[key]
            row = self.rows[decl.base if decl.base is not None else decl.like]
            self.assertEqual(int(row["InventoryType"]), 13, key)
            self.assertIn(decl.primary, ("Intellect (Solo)", "Spirit (Solo)"), key)
        self.assertEqual(round(0.445 * 0.7, 4), DECLARED_MULTS["uldaman_galganns_firehammer"])
        self.assertEqual(int(self.rows[9400]["InventoryType"]), 15)
        # no other one-hand main-hand is a caster weapon (the Longshank is Agility)
        for key, decl in self.decls.items():
            row = self.rows[decl.base if decl.base is not None else decl.like]
            if int(row["InventoryType"]) == 13 and key not in CASTER_MAIN_HANDS:
                self.assertEqual(decl.primary, "Agility (Solo)", key)

    def test_look_donors_are_not_reused(self):
        """No two new items copy one donor's look, and no donor is another source file's (the earlier lists did not
        reuse a donor either)."""
        donors = [d.like for d in self.decls.values() if d.like is not None]
        self.assertEqual(len(donors), len(set(donors)))
        self.assertEqual(len(donors), 24)
        mine = Path(__file__).resolve().parents[1] / "source" / "items" / "uldaman.py"
        taken = set()
        for path in mine.parent.glob("*.py"):
            if path != mine:
                taken |= {int(x) for x in re.findall(r"like=(\d+)", path.read_text(encoding="utf-8"))}
        self.assertEqual(set(donors) & taken, set())

    # --- materialized ---------------------------------------------------------------------------------------------

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows, not the declaration: every stat of the item's shapes has at least one point on every
        tier (blackrock gear REVIEW S3: the declaration named the stat, the thin budget dropped it)."""
        from lib import item_variants  # noqa: PLC0415

        with _with_pending_shapes():
            _, catalog = item_variants.load_itemization_tables()
            by_name = {shape["name"]: shape for shape in catalog.values()}
            stats = materialized_tier_stats(self.decls)
        for key, decl in self.decls.items():
            wanted = set()
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    wanted |= set(by_name[name]["stats"])
            self.assertEqual(set(stats[key]), TIERS, key)
            for tier, got in stats[key].items():
                self.assertFalse(sorted(wanted - set(got)), f"{key} {tier}: a shape stat rounds to 0 ({got})")


def _minted_entries() -> set[int]:
    """Entries item_ids.lock holds for this file's keys (empty before the write run)."""
    lock = Path(__file__).resolve().parents[1] / "source" / "items" / "item_ids.lock"
    return {int(entry) for entry, key, *_ in (line.split() for line in lock.read_text().splitlines() if line.strip())
            if key in LIST}


if __name__ == "__main__":
    unittest.main()
