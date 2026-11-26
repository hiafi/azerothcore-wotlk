"""
The Gnomeregan boss list items (wave 5 dungeon items): source/items/gnomeregan.py.

Checks:
  - the list: 48 items on the dungeon ladder, keys `gnomer_`, one declaration per stock entry (28 `base=` items,
    20 new), the bosses' counts (Techbot 7, Viscous Fallout 7, Electrocutioner 6000 7, the Mobile Alert System 7,
    Crowd Pummeler 9-60 8, Mekgineer Thermaplugg 9, the Dark Iron Ambassador 3);
  - the doc's stats: each item's primary and secondaries are exactly the stats docs/dungeons/gnomeregan-rework.md
    ## Loot "Loot list" names for it (Stamina is everywhere, so it is left out), and the counts the doc's Coverage
    section prints (Crit 17, Haste 23, Versatility 16, Mastery 16, Cooldown Haste 10, Proc Chance 1); when the nested
    docs repo is present, the dungeon doc's table and the loot copy docs/dungeons/dungeon-loot-vanilla.md
    "### Gnomeregan" are parsed and compared with this file's tables (names, boss, call, type, slot, stats);
  - the doc's type and slot: the look donor (`like=`) or the stock entry (`base=`) has the class, subclass and
    InventoryType the doc names, and no declaration overrides one;
  - the Normal level of every item: a new item and a stock item moved onto another boss take the boss's level (the
    highest stock item level of the stock items that stay on it; designer ruling G1 B) and required level the item
    level - 5, a stock item on its own boss keeps its stock level, and the three white and green entries become Rare;
  - the two stock Uses (Manual Crowd Pummeler, Gigaflux Reactivator) keep their stock spell on a shorter item cooldown
    (3 min, 5 min; designer ruling G2 A) on every tier;
  - every shape the list names exists, apart from the one pending shape the integration adds;
  - jewelry carries secondaries only (and the Ringside Bell, a trinket with no primary), the socket picks (trinkets,
    jewelry and Normal tiers never), new items Bind on Pickup with a look, every tier above Normal Bind on Pickup
    (Normal keeps the stock binding), the kept effects and the stock stat spells the budget absorbs, the cleared stock
    columns (random property, resistance), the declared multipliers, the Leather Tank extra Stamina, the no-ammo ranged
    weapons;
  - the materialized rows: every doc stat has a point on every tier (the Blackrock gear review's S3).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_items.py
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
TECHBOT, FALLOUT, ELECTRO, ALERT, PUMMELER, THERMAPLUGG, AMBASSADOR = (
    "Techbot", "Fallout", "Electro", "Alert", "Pummeler", "Thermaplugg", "Ambassador")
# The Normal item level of a new or moved item per boss (designer ruling G1 B, 2026-11-25): the highest stock item
# level of the stock items that stay on the boss (OWN_BOSS); the Mobile Alert System has none, so its moved-in stock's
# highest. The Ambassador's rare list is stock only. Required level is the item level - 5.
BOSS_LEVEL = {TECHBOT: 26, FALLOUT: 32, ELECTRO: 34, ALERT: 31, PUMMELER: 34, THERMAPLUGG: 37}
REQUIRED_GAP = 5
BOSS_COUNT = {TECHBOT: 7, FALLOUT: 7, ELECTRO: 7, ALERT: 7, PUMMELER: 8, THERMAPLUGG: 9, AMBASSADOR: 3}

# key -> (boss, stock entry or None for a new item, the doc's stats in the doc's order).
LIST = {
    # Techbot
    "gnomer_techbot_cpu_shell": (TECHBOT, 9444, "Str Block Vers"),
    "gnomer_oscillating_power_hammer": (TECHBOT, 9488, "Str Dodge"),
    "gnomer_hi_tech_supergun": (TECHBOT, 9487, "Str Haste Vers"),
    "gnomer_hotshot_pilots_gloves": (TECHBOT, 9491, "Int Haste Vers"),
    "gnomer_grounded_sabatons": (TECHBOT, None, "Str Parry Mastery"),
    "gnomer_tech_support_headset": (TECHBOT, None, "Int Mastery CDH"),
    "gnomer_backup_drive": (TECHBOT, None, "Int CDH Haste"),
    # Viscous Fallout
    "gnomer_hydrocane": (FALLOUT, 9452, "Int Haste Crit"),
    "gnomer_toxic_revenger": (FALLOUT, 9453, "Agi Haste"),
    "gnomer_acidic_walkers": (FALLOUT, 9454, "Spi Mastery Vers"),
    "gnomer_grubbis_paws": (FALLOUT, 9445, "Agi Crit Haste"),
    "gnomer_caverndeep_trudgers": (FALLOUT, 9510, "Agi Mastery Vers"),
    "gnomer_lead_plated_legguards": (FALLOUT, None, "Int Haste Vers"),
    "gnomer_hazmat_drape": (FALLOUT, None, "Spi Mastery CDH"),
    # Electrocutioner 6000
    "gnomer_electrocutioner_leg": (ELECTRO, 9446, "Str Haste"),
    "gnomer_electrocutioner_lagnut": (ELECTRO, 9447, "Crit Vers"),
    "gnomer_spidertank_oilrag": (ELECTRO, 9448, "Spi Haste CDH"),
    "gnomer_supercharger_battle_axe": (ELECTRO, 9486, "Agi Vers"),
    "gnomer_insulated_chain_leggings": (ELECTRO, None, "Int Crit Haste"),
    "gnomer_conductive_hauberk": (ELECTRO, None, "Agi Haste Mastery Crit"),
    "gnomer_6000_volt_capacitor": (ELECTRO, None, "Str Crit Proc"),
    # The Mobile Alert System
    "gnomer_gnomeregan_amulet": (ALERT, 10299, "Crit CDH"),
    "gnomer_gyromatic_icemaker": (ALERT, 9489, "Spi Haste"),
    "gnomer_vibroblade": (ALERT, 9485, "Agi Mastery"),
    "gnomer_petrolspill_leggings": (ALERT, 9509, "Agi Crit Vers"),
    "gnomer_security_repeater": (ALERT, None, "Agi Vers"),
    "gnomer_night_watch_mantle": (ALERT, None, "Int Crit Mastery"),
    "gnomer_security_chiefs_girdle": (ALERT, None, "Str Dodge Mastery"),
    # Crowd Pummeler 9-60
    "gnomer_manual_crowd_pummeler": (PUMMELER, 9449, "Agi Crit"),
    "gnomer_gnomebot_operating_boots": (PUMMELER, 9450, "Spi Haste Vers"),
    "gnomer_gizmotron_megachopper": (PUMMELER, 9490, "Str Haste Mastery"),
    "gnomer_piston_driven_legplates": (PUMMELER, None, "Str Crit Vers Mastery"),
    "gnomer_shock_absorber_pads": (PUMMELER, None, "Agi Dodge Vers"),
    "gnomer_grease_monkeys_jerkin": (PUMMELER, None, "Agi Haste CDH"),
    "gnomer_piston_fist": (PUMMELER, None, "Agi Haste Crit"),
    "gnomer_ringside_bell": (PUMMELER, None, "Dodge Vers"),
    # Mekgineer Thermaplugg
    "gnomer_electromagnetic_gigaflux_reactivator": (THERMAPLUGG, 9492, "Int Haste Mastery"),
    "gnomer_thermapluggs_left_arm": (THERMAPLUGG, 9459, "Str Haste Crit Mastery"),
    "gnomer_thermapluggs_central_core": (THERMAPLUGG, 9458, "Spi Haste Mastery"),
    "gnomer_charged_gear": (THERMAPLUGG, 9461, "Haste CDH"),
    "gnomer_mechbuilders_overalls": (THERMAPLUGG, 9508, "Int Crit CDH Vers"),
    "gnomer_mekgineers_blast_visor": (THERMAPLUGG, None, "Str Dodge Parry"),
    "gnomer_girdle_of_spare_fuses": (THERMAPLUGG, None, "Str Haste CDH"),
    "gnomer_mekgineers_arc_welder": (THERMAPLUGG, None, "Int Crit CDH"),
    "gnomer_rolled_workshop_schematics": (THERMAPLUGG, None, "Int Crit Mastery"),
    # The Dark Iron Ambassador (rare)
    "gnomer_emissary_cuffs": (AMBASSADOR, 9455, "Agi Haste Mastery"),
    "gnomer_glass_shooter": (AMBASSADOR, 9456, "Agi Crit"),
    "gnomer_royal_diplomatic_scepter": (AMBASSADOR, 9457, "Int Vers Haste"),
}
# key -> the doc's item name (every row of the doc's Loot list, in the doc's spelling).
NAMES = {
    "gnomer_techbot_cpu_shell": "Techbot CPU Shell",
    "gnomer_oscillating_power_hammer": "Oscillating Power Hammer",
    "gnomer_hi_tech_supergun": "Hi-tech Supergun",
    "gnomer_hotshot_pilots_gloves": "Hotshot Pilot's Gloves",
    "gnomer_grounded_sabatons": "Grounded Sabatons",
    "gnomer_tech_support_headset": "Tech Support Headset",
    "gnomer_backup_drive": "Backup Drive",
    "gnomer_hydrocane": "Hydrocane",
    "gnomer_toxic_revenger": "Toxic Revenger",
    "gnomer_acidic_walkers": "Acidic Walkers",
    "gnomer_grubbis_paws": "Grubbis Paws",
    "gnomer_caverndeep_trudgers": "Caverndeep Trudgers",
    "gnomer_lead_plated_legguards": "Lead-plated Legguards",
    "gnomer_hazmat_drape": "Hazmat Drape",
    "gnomer_electrocutioner_leg": "Electrocutioner Leg",
    "gnomer_electrocutioner_lagnut": "Electrocutioner Lagnut",
    "gnomer_spidertank_oilrag": "Spidertank Oilrag",
    "gnomer_supercharger_battle_axe": "Supercharger Battle Axe",
    "gnomer_insulated_chain_leggings": "Insulated Chain Leggings",
    "gnomer_conductive_hauberk": "Conductive Hauberk",
    "gnomer_6000_volt_capacitor": "6000 Volt Capacitor",
    "gnomer_gnomeregan_amulet": "Gnomeregan Amulet",
    "gnomer_gyromatic_icemaker": "Gyromatic Icemaker",
    "gnomer_vibroblade": "Vibroblade",
    "gnomer_petrolspill_leggings": "Petrolspill Leggings",
    "gnomer_security_repeater": "Security Repeater",
    "gnomer_night_watch_mantle": "Night Watch Mantle",
    "gnomer_security_chiefs_girdle": "Security Chief's Girdle",
    "gnomer_manual_crowd_pummeler": "Manual Crowd Pummeler",
    "gnomer_gnomebot_operating_boots": "Gnomebot Operating Boots",
    "gnomer_gizmotron_megachopper": "Gizmotron Megachopper",
    "gnomer_piston_driven_legplates": "Piston-driven Legplates",
    "gnomer_shock_absorber_pads": "Shock Absorber Pads",
    "gnomer_grease_monkeys_jerkin": "Grease Monkey's Jerkin",
    "gnomer_piston_fist": "Piston Fist",
    "gnomer_ringside_bell": "Ringside Bell",
    "gnomer_electromagnetic_gigaflux_reactivator": "Electromagnetic Gigaflux Reactivator",
    "gnomer_thermapluggs_left_arm": "Thermaplugg's Left Arm",
    "gnomer_thermapluggs_central_core": "Thermaplugg's Central Core",
    "gnomer_charged_gear": "Charged Gear",
    "gnomer_mechbuilders_overalls": "Mechbuilder's Overalls",
    "gnomer_mekgineers_blast_visor": "Mekgineer's Blast Visor",
    "gnomer_girdle_of_spare_fuses": "Girdle of Spare Fuses",
    "gnomer_mekgineers_arc_welder": "Mekgineer's Arc Welder",
    "gnomer_rolled_workshop_schematics": "Rolled Workshop Schematics",
    "gnomer_emissary_cuffs": "Emissary Cuffs",
    "gnomer_glass_shooter": "Glass Shooter",
    "gnomer_royal_diplomatic_scepter": "Royal Diplomatic Scepter",
}
# The doc's (Type, Slot) -> the item_template (class, subclass, InventoryType) triples it allows. A chest may be a robe.
DOC_TYPES = {
    ("Plate", "Head"): {(4, 4, 1)}, ("Plate", "Waist"): {(4, 4, 6)}, ("Plate", "Legs"): {(4, 4, 7)},
    ("Plate", "Feet"): {(4, 4, 8)},
    ("Mail", "Head"): {(4, 3, 1)}, ("Mail", "Hands"): {(4, 3, 10)}, ("Mail", "Chest"): {(4, 3, 5)},
    ("Mail", "Legs"): {(4, 3, 7)}, ("Mail", "Feet"): {(4, 3, 8)},
    ("Leather", "Shoulder"): {(4, 2, 3)}, ("Leather", "Chest"): {(4, 2, 5)}, ("Leather", "Wrist"): {(4, 2, 9)},
    ("Leather", "Legs"): {(4, 2, 7)}, ("Leather", "Feet"): {(4, 2, 8)},
    ("Cloth", "Head"): {(4, 1, 1)}, ("Cloth", "Chest"): {(4, 1, 5), (4, 1, 20)}, ("Cloth", "Wrist"): {(4, 1, 9)},
    ("Cloth", "Hands"): {(4, 1, 10)}, ("Cloth", "Feet"): {(4, 1, 8)},
    ("Cloak", "Back"): {(4, 1, 16)}, ("Neck", "Neck"): {(4, 0, 2)}, ("Ring", "Finger"): {(4, 0, 11)},
    ("Trinket", "Trinket"): {(4, 0, 12)},
    ("Sword", "One-hand"): {(2, 7, 13)}, ("Axe", "One-hand"): {(2, 0, 13)}, ("Dagger", "One-hand"): {(2, 15, 13)},
    ("Mace", "One-hand"): {(2, 4, 13)}, ("Fist weapon", "One-hand"): {(2, 13, 13)},
    ("Axe", "Two-hand"): {(2, 1, 17)}, ("Mace", "Two-hand"): {(2, 5, 17)}, ("Sword", "Two-hand"): {(2, 8, 17)},
    ("Staff", "Two-hand"): {(2, 10, 17)},
    ("Held in off-hand", "Off-hand"): {(4, 0, 23)}, ("Shield", "Off-hand"): {(4, 6, 14)},
    ("Wand", "Ranged"): {(2, 19, 26)}, ("Gun", "Ranged"): {(2, 3, 26)}, ("Crossbow", "Ranged"): {(2, 18, 26)},
}
# key -> the doc's (Type, Slot).
TYPES = {
    "gnomer_techbot_cpu_shell": ("Shield", "Off-hand"),
    "gnomer_oscillating_power_hammer": ("Mace", "One-hand"),
    "gnomer_hi_tech_supergun": ("Gun", "Ranged"),
    "gnomer_hotshot_pilots_gloves": ("Cloth", "Hands"),
    "gnomer_grounded_sabatons": ("Plate", "Feet"),
    "gnomer_tech_support_headset": ("Mail", "Head"),
    "gnomer_backup_drive": ("Trinket", "Trinket"),
    "gnomer_hydrocane": ("Staff", "Two-hand"),
    "gnomer_toxic_revenger": ("Dagger", "One-hand"),
    "gnomer_acidic_walkers": ("Cloth", "Feet"),
    "gnomer_grubbis_paws": ("Mail", "Hands"),
    "gnomer_caverndeep_trudgers": ("Mail", "Feet"),
    "gnomer_lead_plated_legguards": ("Plate", "Legs"),
    "gnomer_hazmat_drape": ("Cloak", "Back"),
    "gnomer_electrocutioner_leg": ("Sword", "One-hand"),
    "gnomer_electrocutioner_lagnut": ("Ring", "Finger"),
    "gnomer_spidertank_oilrag": ("Cloth", "Wrist"),
    "gnomer_supercharger_battle_axe": ("Axe", "Two-hand"),
    "gnomer_insulated_chain_leggings": ("Mail", "Legs"),
    "gnomer_conductive_hauberk": ("Mail", "Chest"),
    "gnomer_6000_volt_capacitor": ("Trinket", "Trinket"),
    "gnomer_gnomeregan_amulet": ("Neck", "Neck"),
    "gnomer_gyromatic_icemaker": ("Wand", "Ranged"),
    "gnomer_vibroblade": ("Axe", "One-hand"),
    "gnomer_petrolspill_leggings": ("Leather", "Legs"),
    "gnomer_security_repeater": ("Crossbow", "Ranged"),
    "gnomer_night_watch_mantle": ("Leather", "Shoulder"),
    "gnomer_security_chiefs_girdle": ("Plate", "Waist"),
    "gnomer_manual_crowd_pummeler": ("Mace", "Two-hand"),
    "gnomer_gnomebot_operating_boots": ("Leather", "Feet"),
    "gnomer_gizmotron_megachopper": ("Sword", "Two-hand"),
    "gnomer_piston_driven_legplates": ("Plate", "Legs"),
    "gnomer_shock_absorber_pads": ("Leather", "Shoulder"),
    "gnomer_grease_monkeys_jerkin": ("Leather", "Chest"),
    "gnomer_piston_fist": ("Fist weapon", "One-hand"),
    "gnomer_ringside_bell": ("Trinket", "Trinket"),
    "gnomer_electromagnetic_gigaflux_reactivator": ("Cloth", "Head"),
    "gnomer_thermapluggs_left_arm": ("Axe", "Two-hand"),
    "gnomer_thermapluggs_central_core": ("Shield", "Off-hand"),
    "gnomer_charged_gear": ("Ring", "Finger"),
    "gnomer_mechbuilders_overalls": ("Cloth", "Chest"),
    "gnomer_mekgineers_blast_visor": ("Plate", "Head"),
    "gnomer_girdle_of_spare_fuses": ("Plate", "Waist"),
    "gnomer_mekgineers_arc_welder": ("Dagger", "One-hand"),
    "gnomer_rolled_workshop_schematics": ("Held in off-hand", "Off-hand"),
    "gnomer_emissary_cuffs": ("Leather", "Wrist"),
    "gnomer_glass_shooter": ("Gun", "Ranged"),
    "gnomer_royal_diplomatic_scepter": ("Mace", "One-hand"),
}
# The dungeon doc's and the loot copy's Boss column spelling -> this file's boss keys (the two docs agree).
DOC_BOSS = {"Techbot": TECHBOT, "Viscous Fallout": FALLOUT, "Electrocutioner 6000": ELECTRO,
            "The Mobile Alert System": ALERT, "Crowd Pummeler 9-60": PUMMELER, "Mekgineer Thermaplugg": THERMAPLUGG,
            "Dark Iron Ambassador (rare)": AMBASSADOR}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
# The doc's stat spelling -> this file's short names.
DOC_STATS = {"Strength": "Str", "Agility": "Agi", "Intellect": "Int", "Spirit": "Spi", "Crit": "Crit", "Haste": "Haste",
             "Mastery": "Mastery", "Versatility": "Vers", "Cooldown Haste": "CDH", "Proc Chance": "Proc",
             "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}
# The doc's Coverage section (48 list items): secondary counts. Dodge, Parry and Block are not in the doc; they are the
# list's own (the Hammer, Security Chief's Girdle, Shock Absorber Pads, Blast Visor and Ringside Bell; Sabatons and the
# Visor; the CPU Shell).
COVERAGE = {"Crit": 17, "Haste": 23, "Vers": 16, "Mastery": 16, "CDH": 10, "Proc": 1, "Dodge": 5, "Parry": 2,
            "Block": 1}

# The one shape the list needs that does not exist yet: the integration adds it in the pending itemization file. It
# models Crit/Haste/Versatility 44 (an Even trio, no rule) with the stats Crit, Cooldown Haste, Versatility.
PENDING_SHAPES = {"Crit/CDH/Versatility": (("Crit/Haste/Versatility",), [32, 24, 23])}

# The 28 stock entries keep their stock row as the Normal tier.
STOCK_ENTRIES = {stock for _, stock, _ in LIST.values() if stock is not None}
# The Normal level (item level, required level) of every stock entry, from the live rows 2026-11-25.
STOCK_LEVELS = {
    9444: (26, 21), 9488: (28, 23), 9487: (29, 24), 9491: (32, 27), 9452: (32, 27), 9453: (32, 27), 9454: (32, 27),
    9445: (34, 29), 9510: (32, 27), 9446: (34, 28), 9447: (34, 28), 9448: (33, 28), 9486: (28, 23), 10299: (31, 26),
    9489: (31, 26), 9485: (30, 25), 9509: (30, 25), 9449: (34, 28), 9450: (33, 28), 9490: (29, 24), 9492: (37, 28),
    9459: (37, 28), 9458: (37, 28), 9461: (37, 28), 9508: (31, 26), 9455: (33, 28), 9456: (35, 30), 9457: (35, 30),
}
# The stock entries that stay on their own boss (the stock game drops them there); every other stock entry is moved.
OWN_BOSS = {
    "gnomer_techbot_cpu_shell", "gnomer_hydrocane", "gnomer_toxic_revenger", "gnomer_acidic_walkers",
    "gnomer_electrocutioner_leg", "gnomer_electrocutioner_lagnut", "gnomer_spidertank_oilrag",
    "gnomer_manual_crowd_pummeler", "gnomer_gnomebot_operating_boots", "gnomer_electromagnetic_gigaflux_reactivator",
    "gnomer_thermapluggs_left_arm", "gnomer_thermapluggs_central_core", "gnomer_charged_gear", "gnomer_emissary_cuffs",
    "gnomer_glass_shooter", "gnomer_royal_diplomatic_scepter",
}
# The moved stock entries whose stock level is not their new boss's: they declare ilvl= and required_level=.
# Caverndeep Trudgers (32 / 27, Viscous Fallout), the Gnomeregan Amulet and the Gyromatic Icemaker (31 / 26, the Alert
# System) already sit on it.
MOVED = {
    "gnomer_oscillating_power_hammer", "gnomer_hi_tech_supergun", "gnomer_hotshot_pilots_gloves",
    "gnomer_grubbis_paws", "gnomer_supercharger_battle_axe", "gnomer_vibroblade", "gnomer_petrolspill_leggings",
    "gnomer_gizmotron_megachopper", "gnomer_mechbuilders_overalls",
}
# The stock quality of the white and green entries (every other stock entry is Rare).
STOCK_QUALITY = {9444: 1, 9489: 2, 10299: 2}
# The stock entries that are not Bind on Pickup: the unbound white shield and the nine shared rare list blues (Bind on
# Equip). Normal stays so, every higher tier is Bind on Pickup.
STOCK_NOT_BOP = {9444, 9485, 9486, 9487, 9488, 9490, 9491, 9508, 9509, 9510}

# One socketed standalone piece per boss (the doc names none: designer question). The first socket is red, blue on tank
# gear; the bonuses are stock +4 ratings (2874 Crit, 3267 Haste, 2871 Dodge). The Ambassador's rare holds none.
SOCKETS = {
    "gnomer_tech_support_headset": (R,),          # Techbot, Mail Intellect head
    "gnomer_lead_plated_legguards": (R,),         # Viscous Fallout, Plate Intellect legs
    "gnomer_conductive_hauberk": (R,),            # Electrocutioner, Mail Agility chest
    "gnomer_security_chiefs_girdle": (B,),        # the Alert System, Plate Tank waist
    "gnomer_piston_driven_legplates": (R,),       # Crowd Pummeler, Plate Strength legs
    "gnomer_mekgineers_blast_visor": (B,),        # Thermaplugg, Plate Tank head
}
BONUS = {
    "gnomer_tech_support_headset": 3267, "gnomer_lead_plated_legguards": 3267, "gnomer_conductive_hauberk": 3267,
    "gnomer_security_chiefs_girdle": 2871, "gnomer_piston_driven_legplates": 2874,
    "gnomer_mekgineers_blast_visor": 2871,
}
TRINKETS = {"gnomer_backup_drive", "gnomer_6000_volt_capacitor", "gnomer_ringside_bell"}
# Rings and the neck: secondaries only. The Ringside Bell is a trinket with no primary (the Deadman's Hand precedent).
JEWELRY = {"gnomer_electrocutioner_lagnut", "gnomer_charged_gear", "gnomer_gnomeregan_amulet"}
NO_PRIMARY = JEWELRY | {"gnomer_ringside_bell"}
# Kept stock effects: key -> ((spell id, trigger) per slot), the live item_template 2026-11-25 (trigger 0 Use, 1 Equip,
# 2 Chance on hit).
KEPT_EFFECTS = {
    "gnomer_hydrocane": ((11789, 1),),                  # Equip, Water Breathing
    "gnomer_toxic_revenger": ((11790, 2),),             # Chance on hit, Poison Cloud
    "gnomer_electrocutioner_leg": ((13482, 2),),        # Chance on hit, Lightning Bolt
    "gnomer_supercharger_battle_axe": ((13527, 2),),    # Chance on hit, Lightning Bolt
    "gnomer_vibroblade": ((11791, 2),),                 # Chance on hit, Puncture Armor
    "gnomer_manual_crowd_pummeler": ((13494, 0),),      # Use, Haste
    "gnomer_electromagnetic_gigaflux_reactivator": ((11826, 0),),  # Use, lightning cone and barrier
}
# The two stock Uses declared again with a shorter item cooldown (designer ruling G2 A): key -> the slot's item_template
# columns (spellcooldown, spellcategory, spellcategorycooldown) on every tier. The stock rows: 3,600,000 / 0 / 0 and
# 1,800,000 / 1141 / 10,000; the category stays stock.
USE_COOLDOWNS = {
    "gnomer_manual_crowd_pummeler": (180000, 0, 0),
    "gnomer_electromagnetic_gigaflux_reactivator": (300000, 1141, 10000),
}
# Stock stat spells the budget absorbs (the default): key -> the spell id (Increased Mana Regen, the dead MP5).
ABSORBED = {"gnomer_spidertank_oilrag": 21361, "gnomer_gnomebot_operating_boots": 21618}
# Columns the declaration clears or sets beyond the look (key -> columns), besides `bonding` on a new item.
CLEARED = {
    "gnomer_hydrocane": {"frost_res": 0}, "gnomer_acidic_walkers": {"nature_res": 0},
    "gnomer_gnomeregan_amulet": {"RandomProperty": 0}, "gnomer_gyromatic_icemaker": {"frost_res": 0},
    "gnomer_charged_gear": {"RandomProperty": 0, "nature_res": 0, "arcane_res": 0},
    "gnomer_mechbuilders_overalls": {"arcane_res": 0},
    "gnomer_emissary_cuffs": {"RandomProperty": 0, "arcane_res": 0},
    "gnomer_hi_tech_supergun": {"ammo_type": 0}, "gnomer_security_repeater": {"ammo_type": 0},
    "gnomer_glass_shooter": {"ammo_type": 0},
}
# The caster one-hand main-hands (their level is below 60): the 60-100 physical cell on every tier.
DECLARED_MULTS = {"gnomer_mekgineers_arc_welder": 0.445, "gnomer_royal_diplomatic_scepter": 0.445}
EXTRA_STAMINA = {"gnomer_shock_absorber_pads": 0.25}  # the Leather Tank piece

RESISTANCES = ("holy_res", "fire_res", "nature_res", "frost_res", "shadow_res", "arcane_res")
TIERS = {"normal", "heroic", "empowered_1", "empowered_2", "empowered_3"}


def _boss_levels(boss: str) -> tuple[int, int]:
    """(item level, required level) of a new or moved item on `boss`."""
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


class GnomereganItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations
                     if e["id"].startswith("gnomer_") and e["_decl"].ladder.name == "vanilla_dungeon"}
        cls.rows = id_blocks.spell_tables.load_live_item_template_rows()

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(LIST))
        self.assertEqual(set(self.decls), set(NAMES))
        self.assertEqual(set(self.decls), set(TYPES))
        self.assertEqual(len(self.decls), 48)
        counts = {}
        for boss, _, _ in LIST.values():
            counts[boss] = counts.get(boss, 0) + 1
        self.assertEqual(counts, BOSS_COUNT)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))  # one declaration per stock entry
        self.assertEqual(set(bases), STOCK_ENTRIES)
        self.assertEqual(len(bases), 28)
        self.assertEqual(len(self.decls) - len(bases), 20)  # 20 new items
        for key, decl in self.decls.items():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon", key)
            self.assertEqual(decl.base, LIST[key][1], key)

    def test_no_other_gnomer_declaration(self):
        """Every `gnomer_` key of this file is on the dungeon ladder; the hard mode items are another file's."""
        other = [e["id"] for e in self.reg.item_declarations
                 if e["id"].startswith("gnomer_") and e["_decl"].ladder.name != "vanilla_dungeon"]
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
        """The doc's Coverage section: Crit 17, Haste 23, Versatility 16, Mastery 16, Cooldown Haste 10, Proc Chance 1
        over the 48 list items (the doc prints no Dodge, Parry and Block count: the list's own)."""
        counts = {}
        for _, _, stats in LIST.values():
            for stat in stats.split():
                if stat in COVERAGE:
                    counts[stat] = counts.get(stat, 0) + 1
        self.assertEqual(counts, COVERAGE)

    def test_the_doc_tables_when_present(self):
        """The dungeon doc's Loot list and the dungeon-loot copy, parsed: names, boss, call, type, slot and stats equal
        this file's tables. The docs/ checkout is a nested private repo and may be absent (CI): a skip."""
        main = REPO_ROOT / "docs" / "dungeons" / "gnomeregan-rework.md"
        copy = REPO_ROOT / "docs" / "dungeons" / "dungeon-loot-vanilla.md"
        if not main.is_file() or not copy.is_file():
            self.skipTest("docs/dungeons/gnomeregan-rework.md is not checked out here")
        by_name = {name: key for key, name in NAMES.items()}
        # both tables: Boss | Item | Call | Type | Slot | Stats
        parsed = {}
        for cells in _table(main, r"^### Loot list \(approved", r"^\*\*Hard mode", 6):
            boss, item, call, kind, slot, stats = cells[:6]
            parsed[item.strip("*")] = (DOC_BOSS[boss], call, kind, slot, _short(stats), item.startswith("**"))
        self.assertEqual(set(parsed), set(by_name))
        copied = {}
        for cells in _table(copy, r"^### Gnomeregan\s*$", r"^\*\*Hard mode", 6):
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
        no declaration overrides one."""
        for key, decl in self.decls.items():
            row = self.rows[decl.base if decl.base is not None else decl.like]
            got = (int(row["class"]), int(row["subclass"]), int(row["InventoryType"]))
            self.assertIn(got, DOC_TYPES[TYPES[key]], key)
            self.assertFalse({"class", "subclass", "InventoryType"} & set(dict(decl.columns)), key)

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
        """A stock item on its own boss keeps its stock level, required level and quality; one moved onto another boss
        takes the boss's level / the level - 5 (declared only when that differs); the white and green entries become
        Rare."""
        self.assertEqual(set(STOCK_LEVELS), STOCK_ENTRIES)
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            row = self.rows[decl.base]
            stock = (int(row["ItemLevel"]), int(row["RequiredLevel"]))
            boss = LIST[key][0]
            if key in MOVED and stock == _boss_levels(boss):
                stock = STOCK_LEVELS[decl.base]  # after the write run the live row already has the moved level
            self.assertEqual(stock, STOCK_LEVELS[decl.base], key)  # the stock row is what this file expects
            if key in MOVED:
                self.assertEqual((decl.ilvl, decl.required_level), _boss_levels(boss), key)
                self.assertNotEqual(stock, _boss_levels(boss), key)  # a declaration that changes nothing is noise
            else:
                self.assertIsNone(decl.ilvl, key)
                self.assertIsNone(decl.required_level, key)
            wanted_quality = STOCK_QUALITY.get(decl.base)
            if wanted_quality is None:
                self.assertEqual(int(row["Quality"]), 3, key)
                self.assertIsNone(decl.quality, key)  # the quality is the stock row's
            else:
                if int(row["Quality"]) != 3:  # after the write run the live row is already Rare
                    self.assertEqual(int(row["Quality"]), wanted_quality, key)
                self.assertEqual(decl.quality, Quality.RARE, key)
        # the moved set is exactly the stock entries off their own boss whose level is not the new boss's
        self.assertLessEqual(OWN_BOSS, {k for k, (_, s, _) in LIST.items() if s is not None})
        self.assertEqual({k for k, (b, s, _) in LIST.items() if s is not None and k not in OWN_BOSS
                          and STOCK_LEVELS[s] != _boss_levels(b)}, MOVED)
        self.assertEqual((len(OWN_BOSS), len(MOVED)), (16, 9))

    def test_boss_levels(self):
        """Each boss's level is the highest stock level of its own stock items (the Alert System: its moved-in
        stock's); the Ambassador's rare list holds only its own stock items."""
        for boss, level in BOSS_LEVEL.items():
            own = [STOCK_LEVELS[s][0] for k, (b, s, _) in LIST.items() if b == boss and k in OWN_BOSS]
            moved_in = [STOCK_LEVELS[s][0] for k, (b, s, _) in LIST.items()
                        if b == boss and s is not None and k not in OWN_BOSS]
            self.assertEqual(level, max(own) if own else max(moved_in), boss)
        self.assertEqual({k for k, (b, _, _) in LIST.items() if b == AMBASSADOR},
                         {k for k in OWN_BOSS if LIST[k][0] == AMBASSADOR})

    def test_resolved_normal_level(self):
        """Each Normal tier row: item level and required level as the rule says, quality Rare."""
        with _with_pending_shapes():
            rows = resolved_tier_rows(self.decls)
        for key, decl in self.decls.items():
            normal = rows[key]["normal"]
            if decl.base is None or key in MOVED:
                want = _boss_levels(LIST[key][0])
            else:
                want = STOCK_LEVELS[decl.base]
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
        self.assertEqual({d.key for d in self.decls.values() if d.secondary in PENDING_SHAPES},
                         {"gnomer_mechbuilders_overalls"})

    def test_jewelry(self):
        for key in NO_PRIMARY:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
        for key in JEWELRY:
            self.assertNotRegex(self.decls[key].secondary, r"Dodge|Parry|Block|MP5", key)
        for key, decl in self.decls.items():
            if decl.primary is None:
                self.assertIn(key, NO_PRIMARY, key)
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)
            self.assertEqual(TYPES[key][1] in ("Finger", "Neck"), key in JEWELRY, key)

    def test_tank_pieces(self):
        """Dodge, Parry and Block go on tank gear only: strength or agility primary (the shape rules check the rest);
        the one exception is the Ringside Bell, a trinket with no primary."""
        for key, decl in self.decls.items():
            if re.search(r"Dodge|Parry|Block", decl.secondary):
                if key == "gnomer_ringside_bell":
                    self.assertIsNone(decl.primary, key)
                else:
                    self.assertIn(decl.primary, ("Strength (Solo)", "Agility (Solo)"), key)
        self.assertEqual(self.decls["gnomer_shock_absorber_pads"].secondary, "Dodge/Versatility")
        self.assertEqual(self.decls["gnomer_security_chiefs_girdle"].secondary, "Dodge/Mastery")
        self.assertEqual(self.decls["gnomer_mekgineers_blast_visor"].secondary, "Dodge/Parry")
        self.assertEqual(self.decls["gnomer_techbot_cpu_shell"].secondary, "Block/Versatility")
        self.assertEqual(self.decls["gnomer_ringside_bell"].secondary, "Dodge/Versatility (Any)")

    # --- sockets, columns, effects --------------------------------------------------------------------------------

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        self.assertEqual({k: d.socket_bonus for k, d in self.decls.items() if d.sockets}, BONUS)
        for key in TRINKETS | JEWELRY:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets and jewelry never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
            if decl.sockets:
                self.assertIn(decl.socket_bonus, (2874, 3267, 2871), key)  # a stock +4 Crit, Haste or Dodge rating
        # exactly one socketed piece per boss, none on the Ambassador's rare
        per_boss = {}
        for key in SOCKETS:
            per_boss[LIST[key][0]] = per_boss.get(LIST[key][0], 0) + 1
        self.assertEqual(per_boss, {boss: 1 for boss in BOSS_COUNT if boss != AMBASSADOR})
        # the tank pieces are blue, the damage and healing pieces red; no piece carries a second socket
        for key, sockets in SOCKETS.items():
            blue = key in ("gnomer_security_chiefs_girdle", "gnomer_mekgineers_blast_visor")
            self.assertEqual(sockets, (B,) if blue else (R,), key)

    def test_column_edits(self):
        """The list changes no stock entry's class, subclass or slot; the only columns a declaration sets are the
        cleared ones (a random property, a resistance, a ranged weapon's ammo) and, on a new item, Bind on Pickup (a new
        crossbow also no ammo)."""
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
                if column not in CLEARED.get(key, {}):
                    self.assertEqual(int(row[column]), 0, f"{key} {column}")
        # the cleared ones are real stock values (a stale clear would go unnoticed)
        if not _minted_entries():  # after the write run the live rows are already cleared
            self.assertEqual(int(self.rows[9455]["RandomProperty"]), 1072)
            self.assertEqual(int(self.rows[9461]["RandomProperty"]), 3481)
            self.assertEqual(int(self.rows[10299]["RandomProperty"]), 3506)
            self.assertEqual(int(self.rows[9452]["frost_res"]), 15)
            self.assertEqual(int(self.rows[9489]["frost_res"]), 5)
            self.assertEqual(int(self.rows[9454]["nature_res"]), 5)
            self.assertEqual(int(self.rows[9461]["nature_res"]), 5)
            self.assertEqual(int(self.rows[9461]["arcane_res"]), 5)
            self.assertEqual(int(self.rows[9455]["arcane_res"]), 5)
            self.assertEqual(int(self.rows[9508]["arcane_res"]), 5)
        self.assertEqual({k: d.extra_stamina for k, d in self.decls.items() if d.extra_stamina}, EXTRA_STAMINA)

    def test_binding(self):
        """Bind on Pickup from Heroic up (user 2026-11-06, R1 N5): the resolved row of every tier above Normal binds
        when picked up, Normal keeps the stock binding (a new item: Bind on Pickup). Only the stock entries that are not
        Bind on Pickup carry the override."""
        with _with_pending_shapes():
            rows = resolved_tier_rows(self.decls)
        for key, decl in self.decls.items():
            self.assertEqual(set(rows[key]), TIERS, key)
            stock = 1 if decl.base is None else int(self.rows[decl.base]["bonding"])
            for tier, row in rows[key].items():
                self.assertEqual(int(row["bonding"]), stock if tier == "normal" else 1, f"{key} {tier}")
        self.assertEqual({d.base for d in self.decls.values()
                          if d.base is not None and int(self.rows[d.base]["bonding"]) != 1}, STOCK_NOT_BOP)
        for key, decl in self.decls.items():
            wanted = {} if decl.base not in STOCK_NOT_BOP else {
                tier: {"bonding": 1} for tier in ("heroic", "empowered_1", "empowered_2", "empowered_3")}
            self.assertEqual({tier: dict(columns) for tier, columns in decl.overrides}, wanted, key)

    def test_ranged_weapons_need_no_ammo(self):
        """The two stock guns and the new crossbow set ammo_type 0 (hunter rework Q3); the wand needs none."""
        for key in ("gnomer_hi_tech_supergun", "gnomer_glass_shooter", "gnomer_security_repeater"):
            decl = self.decls[key]
            self.assertEqual(dict(decl.columns)["ammo_type"], 0, key)
            row = self.rows[decl.base if decl.base is not None else decl.like]
            self.assertIn(int(row["subclass"]), (3, 18), key)  # gun, crossbow
        ranged = {k for k, d in self.decls.items() if TYPES[k][1] == "Ranged"}
        self.assertEqual(ranged, {"gnomer_hi_tech_supergun", "gnomer_glass_shooter", "gnomer_security_repeater",
                                  "gnomer_gyromatic_icemaker"})

    def test_kept_effects(self):
        """Seven stock effects are kept (the stock spells, same on every tier); the two stock stat spells fold into the
        budget; no declaration writes its own spells."""
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

    def test_the_spell_slots_on_every_tier(self):
        """Every tier: a kept effect is the stock slot (id and trigger) and keeps its slot (nothing absorbed), the dead
        MP5 stat spell of Oilrag and the Boots is absorbed into the budget (`absorbed_spell_slots` 1); a kept effect
        item pays less than the full budget for its effect (`budget_mult` below its no-effect twin)."""
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
                        self.assertLess(float(a["budget_mult"]), float(b["budget_mult"]), key)  # the effect discount
                    else:
                        self.assertEqual(a["absorbed_spell_slots"], 1, key)

    def test_declared_multipliers(self):
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)
        # the caster one-hand main-hands are the only ones: InventoryType 13, Intellect primary, no tank or off-hand
        for key in DECLARED_MULTS:
            decl = self.decls[key]
            row = self.rows[decl.base if decl.base is not None else decl.like]
            self.assertEqual(int(row["InventoryType"]), 13, key)
            self.assertEqual(decl.primary, "Intellect (Solo)", key)

    def test_look_donors_are_not_reused(self):
        """No two new items copy one donor's look, and no donor is another source file's (the earlier lists did not
        reuse a donor either)."""
        donors = [d.like for d in self.decls.values() if d.like is not None]
        self.assertEqual(len(donors), len(set(donors)))
        self.assertEqual(len(donors), 20)
        mine = Path(__file__).resolve().parents[1] / "source" / "items" / "gnomeregan.py"
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
            if key.startswith("gnomer_")}


if __name__ == "__main__":
    unittest.main()
