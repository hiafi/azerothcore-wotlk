"""
The Zul'Farrak boss list items (wave 5 dungeon items): source/items/zul_farrak.py.

Checks:
  - the list: 62 items on the dungeon ladder, keys `zf_`, one declaration per stock entry (31 `base=` items, 31 new),
    the bosses' counts (Theka 8, Antu'sul 7, Zum'rah 7, the Pyramid 8, Bly's crew 9, Ukorz 9, Gahz'rilla 9, rares 4) and
    Sul'thraze, the join, which no boss drops;
  - the doc's stats: each item's primary and secondaries are exactly the stats docs/dungeons/zul-farrak-rework.md
    ## Loot "Loot list" names for it (Stamina is everywhere, so it is left out), and the counts the doc's Coverage
    section prints (Mastery 37, Versatility 36, Crit 17, Haste 16, Dodge 5, Parry 4, Block 1, Proc Chance 2); when the
    nested docs repo is present, the dungeon doc's table and the loot copy docs/dungeons/dungeon-loot-vanilla.md
    "### Zul'Farrak" are parsed and compared with this file's tables (names, boss, call, type, slot, stats);
  - the doc's type and slot: the look donor (`like=`) or the stock entry (`base=`) has the class, subclass and
    InventoryType the doc names (relics by name: librams, totems, idols), and no declaration overrides one;
  - the Normal level of every item: new items take their boss's item level (required level - 5), stock items keep
    their stock level except the four moved ones, Sul'thraze keeps its stock Epic 55 / 50;
  - every shape the list names exists, apart from the one pending shape the integration adds;
  - jewelry carries secondaries only, the socket picks (trinkets, jewelry, relics and Normal tiers never), new items
    Bind on Pickup with a look, every tier above Normal Bind on Pickup (Normal keeps the stock binding), the kept
    effects and the stock stat spells the budget absorbs, the cleared stock
    columns (random suffix, resistance), the declared multiplier, the Leather Tank extra Stamina, the gun's ammo;
  - the tier-matched Sul'thraze join (source/items/zul_farrak_effects.py, modules/mod-dungeon-bosses src/ZulFarrak/
    sulthraze_join.cpp, SulthrazeJoinLogic.h): both spell slots on every tier of Jang'thraze, the spell's shape and
    text against the stock 11654, the script binding, no reagent, the same budget as with the stock spells;
  - the materialized rows: every doc stat has a point on every tier (the Blackrock gear review's S3).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_items.py
"""

from __future__ import annotations

import dataclasses
import re
import sys
import unittest
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

MODULE_SRC = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src"
JOIN_HEADER = MODULE_SRC / "ZulFarrak" / "SulthrazeJoinLogic.h"
JOIN_SCRIPT = MODULE_SRC / "ZulFarrak" / "sulthraze_join.cpp"
LOADER = MODULE_SRC / "dungeon_bosses_loader.cpp"

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# Bosses, in the keys this file uses, and the item level of each boss's Normal tier (handoff section 1.2).
THEKA, ANTUSUL, ZUMRAH, PYRAMID, BLY, UKORZ, GAHZRILLA, RARES = (
    "Theka", "Antusul", "Zumrah", "Pyramid", "Bly", "Ukorz", "Gahzrilla", "Rares")
JOIN = "Join"  # not a drop: no boss's loot list holds it (Call of Sul'thraze makes it from the two halves)
BOSS_LEVEL = {THEKA: 46, ANTUSUL: 48, ZUMRAH: 47, PYRAMID: 49, BLY: 49, UKORZ: 50, GAHZRILLA: 50}
BOSS_COUNT = {THEKA: 8, ANTUSUL: 7, ZUMRAH: 7, PYRAMID: 8, BLY: 9, UKORZ: 9, GAHZRILLA: 9, RARES: 4,
              JOIN: 1}

# key -> (boss, stock entry or None for a new item, the doc's stats in the doc's order).
LIST = {
    # Theka the Martyr
    "zf_carapace_of_the_martyr": (THEKA, None, "Str Crit Mastery"),
    "zf_scarab_shell_bracers": (THEKA, None, "Agi Mastery Vers"),
    "zf_penitents_cord": (THEKA, None, "Spi Haste Vers"),
    "zf_blackmetal_cape": (THEKA, 9512, "Agi Crit Vers"),
    "zf_gutwrencher": (THEKA, 5616, "Agi Mastery"),
    "zf_bloodletter_scalpel": (THEKA, 9511, "Agi Crit"),
    "zf_libram_of_the_persecuted": (THEKA, None, "Str Parry Vers"),
    "zf_martyrs_reliquary": (THEKA, None, "Spi Vers"),
    # Antu'sul
    "zf_hand_of_antusul": (ANTUSUL, 9639, "Str Mastery"),
    "zf_sangthraze_the_deflector": (ANTUSUL, 9379, "Str Parry"),
    "zf_vice_grips": (ANTUSUL, 9640, "Str Mastery Vers"),
    "zf_lifeblood_amulet": (ANTUSUL, 9641, "Vers Mastery"),
    "zf_stonegaze_girdle": (ANTUSUL, None, "Agi Dodge Vers"),
    "zf_sullithuz_scale_coif": (ANTUSUL, None, "Agi Crit Vers"),
    "zf_totem_of_the_stone_servant": (ANTUSUL, None, "Int Mastery Crit"),
    # Witch Doctor Zum'rah
    "zf_jumanza_grips": (ZUMRAH, 18083, "Spi Haste Mastery"),
    "zf_zumrahs_vexing_cane": (ZUMRAH, 18082, "Int Vers Mastery"),
    "zf_brainlash": (ZUMRAH, 6440, "Mastery Proc"),
    "zf_soulbinders_mantle": (ZUMRAH, None, "Int Crit Vers Haste"),
    "zf_gravewalker_treads": (ZUMRAH, None, "Int Haste Vers"),
    "zf_idol_of_the_restless_grave": (ZUMRAH, None, "Int Vers Haste"),
    "zf_vessel_of_lost_souls": (ZUMRAH, None, "Int Mastery Vers"),
    # The Pyramid (one list, on Sezz'ziz)
    "zf_bad_mojo_mask": (PYRAMID, 9470, "Int Crit Vers"),
    "zf_jinxed_hoodoo_skin": (PYRAMID, 9473, "Int Vers Mastery"),
    "zf_jinxed_hoodoo_kilt": (PYRAMID, 9474, "Spi Crit Vers"),
    "zf_diabolic_skiver": (PYRAMID, 9475, "Agi Vers"),
    "zf_the_minotaur": (PYRAMID, 9481, "Str Mastery Vers Crit"),
    "zf_executioners_vambraces": (PYRAMID, None, "Str Parry Vers"),
    "zf_gutchewers_girdle": (PYRAMID, None, "Agi Haste Mastery"),
    "zf_totem_of_the_blood_altar": (PYRAMID, None, "Agi Mastery Haste"),
    # Sergeant Bly's crew (one list)
    "zf_troll_protector": (BLY, 2040, "Str Block Mastery"),
    "zf_eyegouger": (BLY, 9480, "Agi Dodge Mastery"),
    "zf_flaming_incinerator": (BLY, 9483, "Int Crit Vers"),
    "zf_sergeants_dented_breastplate": (BLY, None, "Str Dodge Parry Mastery"),
    "zf_ravens_soft_step_gloves": (BLY, None, "Agi Crit Vers"),
    "zf_murtas_mending_wraps": (BLY, None, "Spi Mastery Vers"),
    "zf_blastfuse_bandolier": (BLY, None, "Agi Haste Vers"),
    "zf_ill_gotten_coin": (BLY, None, "Agi Mastery Vers"),
    "zf_weeglis_blunderbuss": (BLY, None, "Agi Mastery"),
    # Chief Ukorz Sandscalp and Ruuzlu
    "zf_big_bad_pauldrons": (UKORZ, 9476, "Str Dodge Vers"),
    "zf_jangthraze_the_protector": (UKORZ, 11086, "Str Vers"),
    "zf_the_chiefs_enforcer": (UKORZ, 9477, "Agi Mastery"),
    "zf_ripsaw": (UKORZ, 9478, "Str Haste"),
    "zf_embrace_of_the_lycan": (UKORZ, 9479, "Agi Crit Mastery"),
    "zf_runed_ring": (UKORZ, 862, "Haste Mastery"),
    "zf_sandscalps_war_kilt": (UKORZ, None, "Agi Crit Mastery Vers"),
    "zf_ruuzlus_bloodied_greaves": (UKORZ, None, "Str Haste Mastery"),
    "zf_idol_of_the_lycan": (UKORZ, None, "Agi Dodge Mastery"),
    # Hydromancer Velratha and Gahz'rilla
    "zf_gahzrilla_fang": (GAHZRILLA, 9467, "Agi Vers"),
    "zf_gahzrilla_scale_armor": (GAHZRILLA, 9469, "Int Mastery Vers"),
    "zf_stormscale_spaulders": (GAHZRILLA, None, "Int Crit Haste"),
    "zf_gauntlets_of_the_sacred_pool": (GAHZRILLA, None, "Int Mastery Vers"),
    "zf_hydromancers_scepter": (GAHZRILLA, None, "Spi Vers Mastery"),
    "zf_robes_of_the_rising_water": (GAHZRILLA, None, "Spi Crit Mastery Vers"),
    "zf_stillwater_drape": (GAHZRILLA, None, "Int Mastery Vers"),
    "zf_libram_of_the_sacred_pool": (GAHZRILLA, None, "Int Haste Mastery"),
    "zf_coil_of_the_electrified_scale": (GAHZRILLA, None, "Crit Proc"),
    # The join of Jang'thraze and Sang'thraze, no boss's drop (the doc lists it with Ukorz)
    "zf_sulthraze_the_lasher": (JOIN, 9372, "Str Mastery Vers"),
    # The rares (one pool)
    "zf_desertwalker_cane": (RARES, 12471, "Spi Haste Mastery"),
    "zf_sandstalker_ankleguards": (RARES, 12470, "Agi Haste Vers"),
    "zf_witch_doctors_cane": (RARES, 9482, "Spi Mastery Crit"),
    "zf_spellshock_leggings": (RARES, 9484, "Int Mastery Haste"),
}
DOC_OWNER = {"zf_sulthraze_the_lasher": UKORZ}  # the boss the doc's table names for the join
# key -> the doc's item name (every row of the doc's Loot list, in the doc's spelling).
NAMES = {
    "zf_carapace_of_the_martyr": "Carapace of the Martyr",
    "zf_scarab_shell_bracers": "Scarab-shell Bracers",
    "zf_penitents_cord": "Penitent's Cord",
    "zf_blackmetal_cape": "Blackmetal Cape",
    "zf_gutwrencher": "Gutwrencher",
    "zf_bloodletter_scalpel": "Bloodletter Scalpel",
    "zf_libram_of_the_persecuted": "Libram of the Persecuted",
    "zf_martyrs_reliquary": "Martyr's Reliquary",
    "zf_hand_of_antusul": "The Hand of Antu'sul",
    "zf_sangthraze_the_deflector": "Sang'thraze the Deflector",
    "zf_vice_grips": "Vice Grips",
    "zf_lifeblood_amulet": "Lifeblood Amulet",
    "zf_stonegaze_girdle": "Stonegaze Girdle",
    "zf_sullithuz_scale_coif": "Sul'lithuz Scale Coif",
    "zf_totem_of_the_stone_servant": "Totem of the Stone Servant",
    "zf_jumanza_grips": "Jumanza Grips",
    "zf_zumrahs_vexing_cane": "Zum'rah's Vexing Cane",
    "zf_brainlash": "Brainlash",
    "zf_soulbinders_mantle": "Soulbinder's Mantle",
    "zf_gravewalker_treads": "Gravewalker Treads",
    "zf_idol_of_the_restless_grave": "Idol of the Restless Grave",
    "zf_vessel_of_lost_souls": "Vessel of Lost Souls",
    "zf_bad_mojo_mask": "Bad Mojo Mask",
    "zf_jinxed_hoodoo_skin": "Jinxed Hoodoo Skin",
    "zf_jinxed_hoodoo_kilt": "Jinxed Hoodoo Kilt",
    "zf_diabolic_skiver": "Diabolic Skiver",
    "zf_the_minotaur": "The Minotaur",
    "zf_executioners_vambraces": "Executioner's Vambraces",
    "zf_gutchewers_girdle": "Gutchewer's Girdle",
    "zf_totem_of_the_blood_altar": "Totem of the Blood Altar",
    "zf_troll_protector": "Troll Protector",
    "zf_eyegouger": "Eyegouger",
    "zf_flaming_incinerator": "Flaming Incinerator",
    "zf_sergeants_dented_breastplate": "Sergeant's Dented Breastplate",
    "zf_ravens_soft_step_gloves": "Raven's Soft-step Gloves",
    "zf_murtas_mending_wraps": "Murta's Mending Wraps",
    "zf_blastfuse_bandolier": "Blastfuse Bandolier",
    "zf_ill_gotten_coin": "Ill-gotten Coin",
    "zf_weeglis_blunderbuss": "Weegli's Blunderbuss",
    "zf_big_bad_pauldrons": "Big Bad Pauldrons",
    "zf_jangthraze_the_protector": "Jang'thraze the Protector",
    "zf_the_chiefs_enforcer": "The Chief's Enforcer",
    "zf_ripsaw": "Ripsaw",
    "zf_embrace_of_the_lycan": "Embrace of the Lycan",
    "zf_runed_ring": "Runed Ring",
    "zf_sandscalps_war_kilt": "Sandscalp's War Kilt",
    "zf_ruuzlus_bloodied_greaves": "Ruuzlu's Bloodied Greaves",
    "zf_idol_of_the_lycan": "Idol of the Lycan",
    "zf_sulthraze_the_lasher": "Sul'thraze the Lasher",
    "zf_gahzrilla_fang": "Gahz'rilla Fang",
    "zf_gahzrilla_scale_armor": "Gahz'rilla Scale Armor",
    "zf_stormscale_spaulders": "Stormscale Spaulders",
    "zf_gauntlets_of_the_sacred_pool": "Gauntlets of the Sacred Pool",
    "zf_hydromancers_scepter": "Hydromancer's Scepter",
    "zf_robes_of_the_rising_water": "Robes of the Rising Water",
    "zf_stillwater_drape": "Stillwater Drape",
    "zf_libram_of_the_sacred_pool": "Libram of the Sacred Pool",
    "zf_coil_of_the_electrified_scale": "Coil of the Electrified Scale",
    "zf_desertwalker_cane": "Desertwalker Cane",
    "zf_sandstalker_ankleguards": "Sandstalker Ankleguards",
    "zf_witch_doctors_cane": "Witch Doctor's Cane",
    "zf_spellshock_leggings": "Spellshock Leggings",
}
# The doc's (Type, Slot) -> the item_template (class, subclass, InventoryType) triples it allows. A chest may be a robe.
DOC_TYPES = {
    ("Plate", "Shoulder"): {(4, 4, 3)}, ("Plate", "Chest"): {(4, 4, 5)}, ("Plate", "Wrist"): {(4, 4, 9)},
    ("Plate", "Hands"): {(4, 4, 10)}, ("Plate", "Feet"): {(4, 4, 8)},
    ("Mail", "Head"): {(4, 3, 1)}, ("Mail", "Shoulder"): {(4, 3, 3)}, ("Mail", "Chest"): {(4, 3, 5)},
    ("Mail", "Wrist"): {(4, 3, 9)}, ("Mail", "Waist"): {(4, 3, 6)}, ("Mail", "Legs"): {(4, 3, 7)},
    ("Mail", "Feet"): {(4, 3, 8)},
    ("Leather", "Head"): {(4, 2, 1)}, ("Leather", "Chest"): {(4, 2, 5)}, ("Leather", "Hands"): {(4, 2, 10)},
    ("Leather", "Waist"): {(4, 2, 6)}, ("Leather", "Legs"): {(4, 2, 7)}, ("Leather", "Feet"): {(4, 2, 8)},
    ("Cloth", "Head"): {(4, 1, 1)}, ("Cloth", "Shoulder"): {(4, 1, 3)}, ("Cloth", "Chest"): {(4, 1, 5), (4, 1, 20)},
    ("Cloth", "Wrist"): {(4, 1, 9)}, ("Cloth", "Hands"): {(4, 1, 10)}, ("Cloth", "Waist"): {(4, 1, 6)},
    ("Cloth", "Legs"): {(4, 1, 7)},
    ("Cloak", "Back"): {(4, 1, 16)}, ("Neck", "Neck"): {(4, 0, 2)}, ("Ring", "Finger"): {(4, 0, 11)},
    ("Trinket", "Trinket"): {(4, 0, 12)},
    ("Relic", "Relic"): {(4, 7, 28), (4, 8, 28), (4, 9, 28)},  # librams, idols, totems: told apart by name below
    ("Sword", "Main hand"): {(2, 7, 21)}, ("Sword", "One-hand"): {(2, 7, 13)}, ("Axe", "One-hand"): {(2, 0, 13)},
    ("Dagger", "One-hand"): {(2, 15, 13)}, ("Mace", "One-hand"): {(2, 4, 13)},
    ("Axe", "Two-hand"): {(2, 1, 17)}, ("Polearm", "Two-hand"): {(2, 6, 17)}, ("Staff", "Two-hand"): {(2, 10, 17)},
    ("Sword", "Two-hand"): {(2, 8, 17)},
    ("Held in off-hand", "Off-hand"): {(4, 0, 23)}, ("Shield", "Off-hand"): {(4, 6, 14)},
    ("Wand", "Ranged"): {(2, 19, 26)}, ("Gun", "Ranged"): {(2, 3, 26)},
}
# key -> the doc's (Type, Slot).
TYPES = {
    "zf_carapace_of_the_martyr": ("Plate", "Chest"),
    "zf_scarab_shell_bracers": ("Mail", "Wrist"),
    "zf_penitents_cord": ("Cloth", "Waist"),
    "zf_blackmetal_cape": ("Cloak", "Back"),
    "zf_gutwrencher": ("Dagger", "One-hand"),
    "zf_bloodletter_scalpel": ("Sword", "One-hand"),
    "zf_libram_of_the_persecuted": ("Relic", "Relic"),
    "zf_martyrs_reliquary": ("Trinket", "Trinket"),
    "zf_hand_of_antusul": ("Mace", "One-hand"),
    "zf_sangthraze_the_deflector": ("Sword", "One-hand"),
    "zf_vice_grips": ("Plate", "Hands"),
    "zf_lifeblood_amulet": ("Neck", "Neck"),
    "zf_stonegaze_girdle": ("Leather", "Waist"),
    "zf_sullithuz_scale_coif": ("Mail", "Head"),
    "zf_totem_of_the_stone_servant": ("Relic", "Relic"),
    "zf_jumanza_grips": ("Cloth", "Hands"),
    "zf_zumrahs_vexing_cane": ("Staff", "Two-hand"),
    "zf_brainlash": ("Ring", "Finger"),
    "zf_soulbinders_mantle": ("Cloth", "Shoulder"),
    "zf_gravewalker_treads": ("Mail", "Feet"),
    "zf_idol_of_the_restless_grave": ("Relic", "Relic"),
    "zf_vessel_of_lost_souls": ("Trinket", "Trinket"),
    "zf_bad_mojo_mask": ("Cloth", "Head"),
    "zf_jinxed_hoodoo_skin": ("Leather", "Chest"),
    "zf_jinxed_hoodoo_kilt": ("Leather", "Legs"),
    "zf_diabolic_skiver": ("Polearm", "Two-hand"),
    "zf_the_minotaur": ("Axe", "Two-hand"),
    "zf_executioners_vambraces": ("Plate", "Wrist"),
    "zf_gutchewers_girdle": ("Mail", "Waist"),
    "zf_totem_of_the_blood_altar": ("Relic", "Relic"),
    "zf_troll_protector": ("Shield", "Off-hand"),
    "zf_eyegouger": ("Polearm", "Two-hand"),
    "zf_flaming_incinerator": ("Wand", "Ranged"),
    "zf_sergeants_dented_breastplate": ("Plate", "Chest"),
    "zf_ravens_soft_step_gloves": ("Leather", "Hands"),
    "zf_murtas_mending_wraps": ("Cloth", "Wrist"),
    "zf_blastfuse_bandolier": ("Mail", "Shoulder"),
    "zf_ill_gotten_coin": ("Trinket", "Trinket"),
    "zf_weeglis_blunderbuss": ("Gun", "Ranged"),
    "zf_big_bad_pauldrons": ("Plate", "Shoulder"),
    "zf_jangthraze_the_protector": ("Sword", "Main hand"),
    "zf_the_chiefs_enforcer": ("Staff", "Two-hand"),
    "zf_ripsaw": ("Axe", "One-hand"),
    "zf_embrace_of_the_lycan": ("Leather", "Head"),
    "zf_runed_ring": ("Ring", "Finger"),
    "zf_sandscalps_war_kilt": ("Mail", "Legs"),
    "zf_ruuzlus_bloodied_greaves": ("Plate", "Feet"),
    "zf_idol_of_the_lycan": ("Relic", "Relic"),
    "zf_sulthraze_the_lasher": ("Sword", "Two-hand"),
    "zf_gahzrilla_fang": ("Dagger", "One-hand"),
    "zf_gahzrilla_scale_armor": ("Mail", "Chest"),
    "zf_stormscale_spaulders": ("Mail", "Shoulder"),
    "zf_gauntlets_of_the_sacred_pool": ("Plate", "Hands"),
    "zf_hydromancers_scepter": ("Mace", "One-hand"),
    "zf_robes_of_the_rising_water": ("Cloth", "Chest"),
    "zf_stillwater_drape": ("Cloak", "Back"),
    "zf_libram_of_the_sacred_pool": ("Relic", "Relic"),
    "zf_coil_of_the_electrified_scale": ("Ring", "Finger"),
    "zf_desertwalker_cane": ("Held in off-hand", "Off-hand"),
    "zf_sandstalker_ankleguards": ("Leather", "Feet"),
    "zf_witch_doctors_cane": ("Staff", "Two-hand"),
    "zf_spellshock_leggings": ("Cloth", "Legs"),
}
# The relics, by name (the doc's Type column says only "Relic"): item_template subclass 7 libram, 8 idol, 9 totem.
RELIC_SUBCLASS = {
    "zf_libram_of_the_persecuted": 7, "zf_libram_of_the_sacred_pool": 7,
    "zf_totem_of_the_stone_servant": 9, "zf_totem_of_the_blood_altar": 9,
    "zf_idol_of_the_restless_grave": 8, "zf_idol_of_the_lycan": 8,
}
# The dungeon doc's Boss column spelling, and the loot copy's, -> this file's boss keys.
DOC_BOSS = {"Theka": THEKA, "Antu'sul": ANTUSUL, "Zum'rah": ZUMRAH, "The Pyramid": PYRAMID, "Bly's crew": BLY,
            "Ukorz": UKORZ, "Gahz'rilla": GAHZRILLA, "Rares": RARES}
COPY_BOSS = {"Theka the Martyr": THEKA, "Antu'sul": ANTUSUL, "Witch Doctor Zum'rah": ZUMRAH,
             "The Pyramid (one list, on Sezz'ziz)": PYRAMID, "Sergeant Bly's crew (one list)": BLY,
             "Chief Ukorz Sandscalp and Ruuzlu": UKORZ, "Hydromancer Velratha and Gahz'rilla": GAHZRILLA,
             "The rares (one pool) (rare)": RARES}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
# The doc's stat spelling -> this file's short names.
DOC_STATS = {"Strength": "Str", "Agility": "Agi", "Intellect": "Int", "Spirit": "Spi", "Crit": "Crit", "Haste": "Haste",
             "Mastery": "Mastery", "Versatility": "Vers", "Proc Chance": "Proc", "Dodge": "Dodge", "Parry": "Parry",
             "Block": "Block"}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}
# The doc's Coverage section (62 list items): secondary counts.
COVERAGE = {"Mastery": 37, "Vers": 36, "Crit": 17, "Haste": 16, "Dodge": 5, "Parry": 4, "Block": 1, "Proc": 2}

# The one shape the list needs that does not exist yet: the integration adds it in the pending itemization file. It
# models Block/Mastery/Versatility 97 (an Even trio that requires a Strength primary) with the stats Dodge, Parry,
# Mastery.
PENDING_SHAPES = {"Dodge/Parry/Mastery": (("Block/Mastery/Versatility",), [13, 14, 22])}

# The 31 stock entries keep their stock row as the Normal tier.
STOCK_ENTRIES = {stock for _, stock, _ in LIST.values() if stock is not None}
# Stock entries that take a new boss's level: key -> (item level, required level).
MOVED_LEVELS = {
    "zf_gutwrencher": (46, 41), "zf_brainlash": (47, 42), "zf_troll_protector": (49, 44), "zf_eyegouger": (49, 44),
}
# The Normal level (item level, required level) of every stock entry, from the live rows 2026-11-25 (and of the four
# moved ones, the stock row they leave).
STOCK_LEVELS = {
    9512: (46, 41), 5616: (47, 42), 9511: (46, 41), 9639: (48, 43), 9379: (49, 44), 9640: (48, 43), 9641: (48, 43),
    18083: (47, 42), 18082: (47, 42), 6440: (48, 43), 9470: (49, 44), 9473: (49, 44), 9474: (49, 44), 9475: (49, 44),
    9481: (49, 44), 2040: (48, 43), 9480: (48, 43), 9483: (49, 44), 9476: (50, 45), 11086: (50, 45), 9477: (50, 45),
    9478: (50, 45), 9479: (50, 45), 862: (50, 45), 9372: (55, 50), 9467: (47, 42), 9469: (48, 43), 12471: (47, 42),
    12470: (47, 42), 9482: (47, 42), 9484: (50, 45),
}
# The stock Bind on Equip entries: Normal stays so, every higher tier is Bind on Pickup.
STOCK_BOE = {9512, 5616, 9511, 6440, 9481, 2040, 9480, 9483, 862, 9482, 9484}
STOCK_EPIC = {9372}  # Sul'thraze keeps its stock quality; every other stock entry is Rare

# One socketed standalone piece per boss (the doc names none: designer question). The first socket is red, blue on
# tank gear; the bonuses are stock +4 ratings (2874 Crit, 3267 Haste, 3359 Parry). The rares' pool holds none.
SOCKETS = {
    "zf_carapace_of_the_martyr": (R,),          # Theka, Plate Strength chest
    "zf_sullithuz_scale_coif": (R,),            # Antu'sul, Mail Agility head
    "zf_soulbinders_mantle": (R,),              # Zum'rah, Cloth Intellect shoulder
    "zf_gutchewers_girdle": (R,),               # the Pyramid, Mail Agility waist
    "zf_sergeants_dented_breastplate": (B,),    # Bly's crew, Plate Tank chest
    "zf_sandscalps_war_kilt": (R,),             # Ukorz, Mail Agility legs
    "zf_gauntlets_of_the_sacred_pool": (R,),    # Gahz'rilla, Plate Intellect hands
}
BONUS = {
    "zf_carapace_of_the_martyr": 2874, "zf_sullithuz_scale_coif": 2874, "zf_soulbinders_mantle": 2874,
    "zf_gutchewers_girdle": 3267, "zf_sergeants_dented_breastplate": 3359, "zf_sandscalps_war_kilt": 2874,
    "zf_gauntlets_of_the_sacred_pool": 3267,
}
TRINKETS = {"zf_martyrs_reliquary", "zf_vessel_of_lost_souls", "zf_ill_gotten_coin"}
RELICS = set(RELIC_SUBCLASS)
# Rings and the neck: secondaries only.
JEWELRY = {"zf_lifeblood_amulet", "zf_brainlash", "zf_runed_ring", "zf_coil_of_the_electrified_scale"}
# Kept stock effects: key -> the stock row's spell ids, slot order (live item_template, 2026-11-25).
KEPT_EFFECTS = {
    "zf_hand_of_antusul": (13532,),        # Chance on hit, Thunder Clap
    "zf_gutwrencher": (16406,),            # Chance on hit, Rend
    "zf_bloodletter_scalpel": (13486,),    # Chance on hit, Wound
    "zf_gahzrilla_fang": (3742,),          # Chance on hit, Static Electricity
    "zf_diabolic_skiver": (18206,),        # Chance on hit, Fatal Wound
    "zf_ripsaw": (16405,),                 # Chance on hit, Wound
    "zf_the_chiefs_enforcer": (56,),       # Chance on hit, Stun (3 sec)
    "zf_sulthraze_the_lasher": (11658,),   # Chance on hit, Sul'thraze
}
# The one item that declares its spells: the stock slot 1 held Call of Sul'thraze 11654 (it names the Normal entries),
# the declaration puts the tier-matched join there; slot 2 (a Chance on hit absorb) is the stock slot.
JANGTHRAZE = "zf_jangthraze_the_protector"
CALL_STOCK, CALL_JOIN, JANGTHRAZE_ABSORB = 11654, 213808, 11657
# Stock stat spells the budget absorbs (the default): key -> the spell id.
ABSORBED = {"zf_embrace_of_the_lycan": 15807, "zf_vice_grips": 9142, "zf_gahzrilla_scale_armor": 21631}
# Columns the declaration clears or sets beyond the look (key -> columns), besides `bonding` on a new item.
CLEARED = {
    "zf_vice_grips": {"RandomProperty": 0}, "zf_runed_ring": {"RandomProperty": 0},
    "zf_flaming_incinerator": {"fire_res": 0}, "zf_weeglis_blunderbuss": {"ammo_type": 0},
}
# The caster one-hand mace (its level is below 60): the 60-100 physical cell on every tier.
DECLARED_MULTS = {"zf_hydromancers_scepter": 0.445}
EXTRA_STAMINA = {"zf_stonegaze_girdle": 0.25}  # the Leather Tank piece

RESISTANCES = ("holy_res", "fire_res", "nature_res", "frost_res", "shadow_res", "arcane_res")


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
    """{short stat names} of a doc stats cell ("Strength, Mastery; keeps its proc" -> {Str, Mastery})."""
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


class ZulFarrakItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations
                     if e["id"].startswith("zf_") and e["_decl"].ladder.name == "vanilla_dungeon"}
        cls.rows = id_blocks.spell_tables.load_live_item_template_rows()

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(LIST))
        self.assertEqual(set(self.decls), set(NAMES))
        self.assertEqual(set(self.decls), set(TYPES))
        self.assertEqual(len(self.decls), 62)
        counts = {}
        for boss, _, _ in LIST.values():
            counts[boss] = counts.get(boss, 0) + 1
        self.assertEqual(counts, BOSS_COUNT)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))  # one declaration per stock entry
        self.assertEqual(set(bases), STOCK_ENTRIES)
        self.assertEqual(len(bases), 31)
        self.assertEqual(len(self.decls) - len(bases), 31)  # 31 new items
        for key, decl in self.decls.items():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon", key)
            self.assertEqual(decl.base, LIST[key][1], key)

    def test_the_doc_stats(self):
        for key, (_, _, stats) in LIST.items():
            wanted = {STAT_NAMES[s] for s in stats.split()}
            decl = self.decls[key]
            self.assertEqual(stat_names(decl), wanted, key)
            # a primary shape names exactly one primary; a secondary shape only secondaries
            if decl.primary is not None:
                self.assertEqual(len(stat_names(decl) & PRIMARIES), 1, key)
            self.assertFalse(
                set(decl.secondary.replace(" (Solo)", "").replace(" (Any)", "").split("/")) & PRIMARIES, key)

    def test_the_doc_coverage_counts(self):
        """The doc's Coverage section: Mastery 37, Versatility 36, Crit 17, Haste 16, Dodge 5, Parry 4, Block 1, Proc
        Chance 2 over the 62 list items."""
        counts = {}
        for _, _, stats in LIST.values():
            for stat in stats.split():
                if stat in COVERAGE:
                    counts[stat] = counts.get(stat, 0) + 1
        self.assertEqual(counts, COVERAGE)

    def test_the_doc_tables_when_present(self):
        """The dungeon doc's Loot list and the dungeon-loot copy, parsed: names, boss, call, type, slot and stats equal
        this file's tables. The docs/ checkout is a nested private repo and may be absent (CI): a skip."""
        main = REPO_ROOT / "docs" / "dungeons" / "zul-farrak-rework.md"
        copy = REPO_ROOT / "docs" / "dungeons" / "dungeon-loot-vanilla.md"
        if not main.is_file() or not copy.is_file():
            self.skipTest("docs/dungeons/zul-farrak-rework.md is not checked out here")
        by_name = {name: key for key, name in NAMES.items()}
        # the dungeon doc: Slot | Type | Stats | Item | Call | Boss
        parsed = {}
        for cells in _table(main, r"^### Loot list \(approved", r"^\*\*Hard mode", 6):
            slot, kind, stats, item, call, boss = cells[:6]
            parsed[item.strip("*")] = (DOC_BOSS[boss], call, kind, slot, _short(stats), item.startswith("**"))
        self.assertEqual(set(parsed), set(by_name))
        # the loot copy: Boss | Item | Call | Type | Slot | Stats
        copied = {}
        for cells in _table(copy, r"^### Zul'Farrak\s*$", r"^\*\*Hard mode", 6):
            boss, item, call, kind, slot, stats = cells[:6]
            copied[item.strip("*")] = (COPY_BOSS[boss], call, kind, slot, _short(stats), item.startswith("**"))
        self.assertEqual(parsed, copied)  # the two docs agree on every row
        for name, (boss, call, kind, slot, stats, bold) in parsed.items():
            key = by_name[name]
            self.assertEqual(boss, DOC_OWNER.get(key, LIST[key][0]), key)
            self.assertEqual(call == "Alter", LIST[key][1] is not None, key)
            self.assertEqual(bold, LIST[key][1] is None, key)  # the new items are the bold rows
            self.assertEqual((kind, slot), TYPES[key], key)
            self.assertEqual(stats, set(LIST[key][2].split()), key)

    def test_type_and_slot(self):
        """like= and base= bring class, subclass and InventoryType: every donor or stock row is of the doc's type, the
        relics by name, and no declaration overrides one."""
        for key, decl in self.decls.items():
            row = self.rows[decl.base if decl.base is not None else decl.like]
            got = (int(row["class"]), int(row["subclass"]), int(row["InventoryType"]))
            self.assertIn(got, DOC_TYPES[TYPES[key]], key)
            if key in RELIC_SUBCLASS:
                self.assertEqual(got[1], RELIC_SUBCLASS[key], key)
                kind = {7: "Libram", 8: "Idol", 9: "Totem"}[got[1]]
                self.assertTrue(NAMES[key].startswith(kind), key)
            self.assertFalse({"class", "subclass", "InventoryType"} & set(dict(decl.columns)), key)

    def test_stock_names(self):
        """A stock entry's live name is the doc's; a new item's name is free in the live item_template."""
        names = {row["name"] for row in self.rows.values()}
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
            self.assertEqual(decl.ilvl, BOSS_LEVEL[LIST[key][0]], key)  # the boss's item level
            self.assertIsNone(decl.required_level, key)  # defaults to the item level - 5
            self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_stock_levels(self):
        """A stock item keeps its stock level, required level and quality, except the four that move to another boss
        (they take that boss's level, required level - 5); Sul'thraze keeps its stock Epic quality."""
        self.assertEqual(set(STOCK_LEVELS), STOCK_ENTRIES)
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            row = self.rows[decl.base]
            stock = (int(row["ItemLevel"]), int(row["RequiredLevel"]))
            self.assertEqual(stock, STOCK_LEVELS[decl.base], key)  # the stock row is what this file expects
            self.assertEqual(int(row["Quality"]), 4 if decl.base in STOCK_EPIC else 3, key)
            self.assertIsNone(decl.quality, key)  # the quality is the stock row's
            if key in MOVED_LEVELS:
                self.assertEqual((decl.ilvl, decl.required_level), MOVED_LEVELS[key], key)
                boss_level = BOSS_LEVEL[LIST[key][0]]
                self.assertEqual(MOVED_LEVELS[key], (boss_level, boss_level - 5), key)
                self.assertNotEqual(stock, MOVED_LEVELS[key], key)  # a declaration that changes nothing is noise
            else:
                self.assertIsNone(decl.ilvl, key)
                self.assertIsNone(decl.required_level, key)
        # the stock levels against the bosses: only the moved entries and the rares differ from their boss's level
        for key, (boss, stock, _) in LIST.items():
            if stock is None or key in MOVED_LEVELS or boss == RARES:
                continue
            level = STOCK_LEVELS[stock][0]
            if boss == JOIN or stock == 862:  # Sul'thraze (no boss, Epic 55), Runed Ring (two bosses): stock level
                continue
            self.assertLessEqual(abs(level - BOSS_LEVEL[boss]), 3, key)

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
        self.assertEqual({d.key for d in self.decls.values() if d.secondary in PENDING_SHAPES},
                         {"zf_sergeants_dented_breastplate"})

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

    def test_tank_pieces(self):
        """Dodge, Parry and Block go on tank gear only: strength or agility primary (the shape rules check the rest)."""
        for key, decl in self.decls.items():
            if re.search(r"Dodge|Parry|Block", decl.secondary):
                self.assertIn(decl.primary, ("Strength (Solo)", "Agility (Solo)"), key)
        self.assertEqual(self.decls["zf_stonegaze_girdle"].secondary, "Dodge/Versatility")
        self.assertEqual(self.decls["zf_sergeants_dented_breastplate"].secondary, "Dodge/Parry/Mastery")
        self.assertEqual(self.decls["zf_troll_protector"].secondary, "Block/Mastery")

    # --- sockets, columns, effects --------------------------------------------------------------------------------

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        self.assertEqual({k: d.socket_bonus for k, d in self.decls.items() if d.sockets}, BONUS)
        for key in TRINKETS | JEWELRY | RELICS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets, jewelry and relics never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
            if decl.sockets:
                self.assertIn(decl.socket_bonus, (2874, 3267, 3359), key)  # a stock +4 Crit, Haste or Parry rating
        # exactly one socketed piece per boss, none in the rares' pool
        per_boss = {}
        for key in SOCKETS:
            per_boss[LIST[key][0]] = per_boss.get(LIST[key][0], 0) + 1
        self.assertEqual(per_boss, {boss: 1 for boss in BOSS_LEVEL})
        # the tank piece is blue and takes the Parry bonus, the damage and healing pieces are red
        self.assertEqual(SOCKETS["zf_sergeants_dented_breastplate"], (B,))
        for key, sockets in SOCKETS.items():
            if key != "zf_sergeants_dented_breastplate":
                self.assertEqual(sockets, (R,), key)
        self.assertNotIn(Y, [c for s in SOCKETS.values() for c in s])  # no two-hander carries sockets, no second one

    def test_column_edits(self):
        """The list changes no stock entry's class, subclass or slot; the only columns a declaration sets are the
        cleared ones (a random suffix, a resistance, a gun's ammo) and, on a new item, Bind on Pickup."""
        for key, decl in self.decls.items():
            columns = dict(decl.columns)
            if decl.base is not None:
                self.assertEqual(columns, CLEARED.get(key, {}), key)
            else:
                self.assertEqual(columns, {"bonding": 1, **CLEARED.get(key, {})}, key)
        # every other stock row has no random property, suffix, resistance, set or limit category to clear
        for key, decl in self.decls.items():
            if decl.base is None or key in CLEARED:
                continue
            row = self.rows[decl.base]
            self.assertEqual(int(row["RandomProperty"]), 0, key)
            self.assertEqual(int(row["RandomSuffix"]), 0, key)
            self.assertEqual(int(row["itemset"]), 0, key)
            self.assertEqual(int(row["ItemLimitCategory"]), 0, key)
            for column in RESISTANCES:
                self.assertEqual(int(row[column]), 0, f"{key} {column}")
        # the cleared ones are real stock values (a stale clear would go unnoticed)
        self.assertEqual(int(self.rows[9640]["RandomProperty"]), 783)
        self.assertEqual(int(self.rows[862]["RandomProperty"]), 3253)
        self.assertEqual(int(self.rows[9483]["fire_res"]), 8)
        self.assertEqual({k: d.extra_stamina for k, d in self.decls.items() if d.extra_stamina}, EXTRA_STAMINA)

    def test_binding(self):
        """Bind on Pickup from Heroic up (user 2026-11-06, R1 N5): the resolved row of every tier above Normal binds
        when picked up, Normal keeps the stock binding (a new item: Bind on Pickup). Only the stock Bind on Equip
        entries carry the override."""
        with _with_pending_shapes():
            rows = resolved_tier_rows(self.decls)
        for key, decl in self.decls.items():
            self.assertEqual(set(rows[key]), {"normal", "heroic", "empowered_1", "empowered_2", "empowered_3"}, key)
            stock = 1 if decl.base is None else int(self.rows[decl.base]["bonding"])
            for tier, row in rows[key].items():
                self.assertEqual(int(row["bonding"]), stock if tier == "normal" else 1, f"{key} {tier}")
        self.assertEqual({d.base for d in self.decls.values()
                          if d.base is not None and int(self.rows[d.base]["bonding"]) != 1}, STOCK_BOE)
        for key, decl in self.decls.items():
            wanted = {} if decl.base not in STOCK_BOE else {
                tier: {"bonding": 1} for tier in ("heroic", "empowered_1", "empowered_2", "empowered_3")}
            self.assertEqual({tier: dict(columns) for tier, columns in decl.overrides}, wanted, key)

    def test_gun_needs_no_ammo(self):
        self.assertEqual(int(self.rows[self.decls["zf_weeglis_blunderbuss"].like]["subclass"]), 3)  # a gun donor
        self.assertEqual(dict(self.decls["zf_weeglis_blunderbuss"].columns)["ammo_type"], 0)

    def test_kept_effects(self):
        """Eight stock procs are kept (the stock spells, same on every tier); the three stock stat spells fold into the
        budget; only Jang'thraze writes its own spells (the join, test_the_join_is_on_every_tier_of_jangthraze)."""
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, set(KEPT_EFFECTS))
        self.assertEqual({k for k, d in self.decls.items() if d.spells is not None}, {JANGTHRAZE})
        for key, decl in self.decls.items():
            if decl.base is None or key == JANGTHRAZE:
                continue
            row = self.rows[decl.base]
            spells = tuple(int(row[f"spellid_{n}"]) for n in range(1, 6) if int(row[f"spellid_{n}"]))
            if key in KEPT_EFFECTS:
                self.assertEqual(spells, KEPT_EFFECTS[key], key)
            elif key in ABSORBED:
                self.assertEqual(spells, (ABSORBED[key],), key)  # absorbed by the budget (the default)
            else:
                self.assertEqual(spells, (), key)  # nothing to absorb or keep
        # the procs are what the doc says ("keeps its proc"): trigger 2 (on hit)
        for key, spells in KEPT_EFFECTS.items():
            row = self.rows[self.decls[key].base]
            self.assertEqual([int(row[f"spelltrigger_{n}"]) for n in range(1, len(spells) + 1)], [2], key)

    # --- the Sul'thraze join -------------------------------------------------------------------------------------

    def test_sulthraze_join_items(self):
        """The three swords are on one ladder, so each has the same five tiers (item_budget_variant steps 0-4, which
        the script matches); Sul'thraze keeps its stock Epic 55 / 50."""
        jang, sang, sul = (self.decls[k] for k in (
            JANGTHRAZE, "zf_sangthraze_the_deflector", "zf_sulthraze_the_lasher"))
        self.assertEqual((jang.base, sang.base, sul.base), (11086, 9379, 9372))
        self.assertEqual(int(self.rows[9372]["Quality"]), 4)
        self.assertEqual((sul.ilvl, sul.quality, sul.required_level), (None, None, None))
        self.assertEqual({jang.ladder.name, sang.ladder.name, sul.ladder.name}, {"vanilla_dungeon"})
        self.assertEqual([t.step for t in jang.ladder.tiers], [0, 1, 2, 3, 4])
        # the other half and the result have no Use of their own, and stock's is one the join replaces
        self.assertEqual((sang.spells, sang.keep_spells, sul.spells, sul.keep_spells), (None, False, None, True))

    def test_the_join_is_on_every_tier_of_jangthraze(self):
        """Every tier's resolved row: slot 1 the join as a Use with charges -1 (the engine uses the sword up), slot 2
        the stock absorb proc, the other slots empty."""
        with _with_pending_shapes():
            rows = resolved_tier_rows({JANGTHRAZE: self.decls[JANGTHRAZE]})[JANGTHRAZE]
        self.assertEqual(set(rows), {"normal", "heroic", "empowered_1", "empowered_2", "empowered_3"})
        parts = ("id", "trigger", "charges", "cooldown", "category", "categorycooldown")
        for tier, row in rows.items():
            slots = [tuple(int(row[f"spell{part}_{n}"]) for part in parts) for n in range(1, 6)]
            self.assertEqual(slots[0], (CALL_JOIN, 0, -1, -1, 0, -1), tier)
            self.assertEqual(slots[1], (JANGTHRAZE_ABSORB, 2, 0, -1, 0, -1), tier)
            self.assertEqual([slot[0] for slot in slots[2:]], [0, 0, 0], tier)
            self.assertEqual(float(row["spellppmRate_2"]), 1.2, tier)
            self.assertEqual([int(row[c]) for c in ("stackable", "maxcount")], [1, 0], tier)

    def test_only_the_use_spell_differs_from_the_stock_item(self):
        """The change from keep_spells=True is the one id: the stats, the budget row and every other column of each
        tier are what the stock spells gave (same 0.7 discount, limit category and absorbed slots)."""
        from lib import item_variants  # noqa: PLC0415

        decl = self.decls[JANGTHRAZE]
        before = dataclasses.replace(decl, spells=None, keep_spells=True)
        with _with_pending_shapes():
            stats_now, stats_before = (materialized_tier_stats({JANGTHRAZE: d}) for d in (decl, before))
            rows_now, rows_before = (resolved_tier_rows({JANGTHRAZE: d})[JANGTHRAZE] for d in (decl, before))
            tables, catalog = item_variants.load_itemization_tables()
        self.assertEqual(stats_now, stats_before)
        for tier, row in rows_now.items():
            changed = {c for c, value in row.items() if value != rows_before[tier][c] and c != "spellppmRate_1"
                       and float(value) != float(rows_before[tier][c])}
            self.assertEqual(changed, {"spellid_1"}, tier)
            self.assertEqual(int(rows_before[tier]["spellid_1"]), CALL_STOCK, tier)
        cells = item_variants.FrozenRoleCells(
            item_variants.RoleCells(), item_variants.parse_cells_lock(item_variants.CELLS_LOCK_PATH.read_text()))
        index = item_variants._shape_index(catalog)
        columns = tuple(id_blocks.spell_tables.ITEM_TEMPLATE_COLUMNS)
        resolved = [item_variants._resolve_item(d, self.rows, tables, catalog, index, columns, [], [], cells)[1]
                    for d in (decl, before)]
        self.assertEqual([p["itemization"] for p in resolved[0]], [p["itemization"] for p in resolved[1]])
        self.assertTrue(all(float(p["itemization"]["budget_mult"]) > 0 for p in resolved[0]))

    def test_the_join_spell(self):
        """213808: the stock Call of Sul'thraze without its Create Item and without a reagent, one DUMMY on the caster,
        bound to its script, sharing nothing with the stock id."""
        spell = next(e for e in self.reg.spells if int(e["id"]) == CALL_JOIN)
        raw = spell["raw_overrides"]
        self.assertEqual(spell["name"], "Call of Sul'thraze")
        self.assertEqual((spell["cast_time_ms"], spell["cooldown_ms"], spell["attributes"], spell["spell_icon_id"],
                          raw["InterruptFlags"], raw["SpellVisualID_1"], raw["EquippedItemClass"]),
                         (10000, 0, 0x100, 2667, 15, 76, -1))          # 11654's
        self.assertEqual((spell["effect1"]["type"], spell["effect1"]["implicit_target_a"]), (3, 1))  # DUMMY, the caster
        self.assertFalse(spell.get("effect2") or spell.get("effect3"))
        self.assertFalse([c for c in raw if c.startswith("Reagent")])  # the client would enforce one tier's entry
        self.assertEqual(raw["Description_Lang_enUS"],
                         "Combines Jang'thraze with a Sang'thraze of the same tier to form the mighty sword, "
                         "Sul'thraze. Both halves are used up.")
        self.assertNotRegex(raw["Description_Lang_enUS"], r"[$0-9]")
        bound = [r["ScriptName"] for r in self.reg.spell_script_names if int(r["spell_id"]) == CALL_JOIN]
        self.assertEqual(bound, ["spell_zf_call_of_sulthraze"])
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak_items", {"spell": {CALL_JOIN}}), [])
        # the stock spell is nobody's declaration and no declared item casts it
        self.assertNotIn(CALL_STOCK, {int(e["id"]) for e in self.reg.spells})
        used = {s.spell_id for e in self.reg.item_declarations for s in (e["_decl"].spells or ())}
        self.assertNotIn(CALL_STOCK, used)
        self.assertIn(CALL_JOIN, used)

    def test_the_join_script(self):
        """The script registers the bound name, the header names the spell and the three base entries, and the rules a
        playtest cannot see: the check at both ends, the effect without a target, Jang'thraze kept when nothing is
        made."""
        header, source, loader = (path.read_text() for path in (JOIN_HEADER, JOIN_SCRIPT, LOADER))
        self.assertIn(f"SPELL_CALL_OF_SULTHRAZE = {CALL_JOIN};", header)
        self.assertEqual(re.findall(r"\{ (\d+), Blade::(\w+) \}", header),
                         [("11086", "Jangthraze"), ("9379", "Sangthraze"), ("9372", "Sulthraze")])
        self.assertEqual(re.findall(r"RegisterSpellScript\((\w+)\)", source), ["spell_zf_call_of_sulthraze"])
        self.assertEqual(loader.count("AddSC_zf_sulthraze_join();"), 2)
        self.assertIn("OnCheckCast += SpellCheckCastFn(spell_zf_call_of_sulthraze::CheckJoin)", source)
        self.assertIn("OnEffectHit += SpellEffectFn(spell_zf_call_of_sulthraze::HandleJoin, EFFECT_0, "
                      "SPELL_EFFECT_DUMMY)", source)
        effect = source.split("void HandleJoin(", 1)[1].split("\n    }\n", 1)[0]
        self.assertLess(effect.index("KeepCastItem(spell)"), effect.index("DestroyItem("))
        self.assertLess(effect.index("DestroyItem("), effect.index("StoreNewItem("))
        self.assertIn("TRIGGERED_IGNORE_CAST_ITEM", source)
        # the lines whose loss no lint sees: each one alone would eat a half, hand out nothing or only join Normal
        keep = source.split("static void KeepCastItem(", 1)[1].split("\n    }\n", 1)[0]
        self.assertIn("spell->m_CastItem = nullptr;", keep)
        self.assertIn("spell->m_castItemGUID.Clear();", keep)
        startup = source.split("void OnStartup() override", 1)[1].split("\n    }\n", 1)[0]
        self.assertIn("LoadJoinTable();", startup)
        self.assertIn('"SELECT entry, base_entry, tier FROM item_budget_variant "', source)
        for line in ("uint32 const entry = fields[0].Get<uint32>();", "uint32 const step = fields[2].Get<uint8>();",
                     "sJoinTable.AddVariant(entry, fields[1].Get<uint32>(), step)",
                     "return plan.Ready() ? SPELL_CAST_OK : Refuse(plan);",
                     "plan.storeError = plan.player->CanStoreNewItem(NULL_BAG, NULL_SLOT, plan.dest, "
                     "plan.decision.sulthraze, 1);",
                     "return decision.verdict == JoinVerdict::Join && sangthraze && storeError == EQUIP_ERR_OK "
                     "&& !dest.empty();",
                     "if (item->GetEntry() == plan.decision.sangthraze)",
                     "|| plan.player->GetItemByGuid(castItem->GetGUID()) != castItem "
                     "|| !IsCarried(plan.player, castItem))",
                     "return !(trade && trade->HasItem(item->GetGUID()))",
                     "(item->IsEquipped() || Player::IsInventoryPos(item->GetBagSlot(), item->GetSlot()));"):
            self.assertIn(line, source)
        self.assertEqual(re.findall(r"DestroyItem\(.*", source),
                         ["DestroyItem(plan.sangthraze->GetBagSlot(), plan.sangthraze->GetSlot(), true);"])
        self.assertIn("player->StoreNewItem(plan.dest, plan.decision.sulthraze, true);", effect)
        self.assertEqual(effect.count("KeepCastItem(spell);"), 2)

    def test_declared_multipliers(self):
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)
        # the caster one-hand weapon is the only caster main-hand: InventoryType 13, a mace, Spirit primary
        scepter = self.rows[self.decls["zf_hydromancers_scepter"].like]
        self.assertEqual((int(scepter["class"]), int(scepter["subclass"]), int(scepter["InventoryType"])), (2, 4, 13))

    def test_look_donors_are_not_reused(self):
        """No two new items copy one donor's look (the earlier lists did not reuse a donor either)."""
        donors = [d.like for d in self.decls.values() if d.like is not None]
        self.assertEqual(len(donors), len(set(donors)))
        self.assertEqual(len(donors), 31)

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
            self.assertEqual(set(stats[key]), {"normal", "heroic", "empowered_1", "empowered_2", "empowered_3"}, key)
            for tier, got in stats[key].items():
                self.assertFalse(sorted(wanted - set(got)), f"{key} {tier}: a shape stat rounds to 0 ({got})")


if __name__ == "__main__":
    unittest.main()
