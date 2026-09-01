"""
`item_template` enum labels, read straight from
`src/server/game/Entities/Item/ItemTemplate.h` (this repo's own source, not
stock AzerothCore/wowhead - re-check that file if any of this looks stale,
especially the stat types this fork has repurposed).

- `ItemClass` -> `ITEM_CLASS_NAMES`
- Each `ItemSubclass*` enum -> `ITEM_SUBCLASS_NAMES[class id]`
- `ItemModType` -> `ITEM_MOD_NAMES` (also used by lib/loot.py's drop
  summaries, so the item form's stat_typeN dropdowns and the dungeon
  browser's stat summaries can never drift apart from each other).
- `InventoryType` -> `INVENTORY_TYPE_NAMES`
"""

from __future__ import annotations

# ItemClass
ITEM_CLASS_NAMES = {
    0: "Consumable", 1: "Container", 2: "Weapon", 3: "Gem", 4: "Armor",
    5: "Reagent", 6: "Projectile", 7: "Trade Goods", 8: "Generic",
    9: "Recipe", 10: "Money", 11: "Quiver", 12: "Quest", 13: "Key",
    14: "Permanent", 15: "Misc", 16: "Glyph",
}

# The two ItemClass values whose subclass names a "type" column (the item
# list, item_list.html) is worth showing - every other class's subclass
# doesn't read as a meaningful "type" the way a weapon/armor one does.
WEAPON_ARMOR_CLASSES = {2, 4}

# ItemSubclass* (one enum per ItemClass value above).
ITEM_SUBCLASS_NAMES = {
    0: {  # ItemSubclassConsumable
        0: "Consumable", 1: "Potion", 2: "Elixir", 3: "Flask", 4: "Scroll",
        5: "Food", 6: "Item Enhancement", 7: "Bandage", 8: "Other",
    },
    1: {  # ItemSubclassContainer
        0: "Container", 1: "Soul Bag", 2: "Herb Bag", 3: "Enchanting Bag",
        4: "Engineering Bag", 5: "Gem Bag", 6: "Mining Bag",
        7: "Leatherworking Bag", 8: "Inscription Bag",
    },
    2: {  # ItemSubclassWeapon
        0: "Axe (1H)", 1: "Axe (2H)", 2: "Bow", 3: "Gun", 4: "Mace (1H)",
        5: "Mace (2H)", 6: "Polearm", 7: "Sword (1H)", 8: "Sword (2H)",
        9: "(obsolete)", 10: "Staff", 11: "Exotic (1H)", 12: "Exotic (2H)",
        13: "Fist Weapon", 14: "Misc", 15: "Dagger", 16: "Thrown",
        17: "Spear", 18: "Crossbow", 19: "Wand", 20: "Fishing Pole",
    },
    3: {  # ItemSubclassGem
        0: "Red", 1: "Blue", 2: "Yellow", 3: "Purple", 4: "Green",
        5: "Orange", 6: "Meta", 7: "Simple", 8: "Prismatic",
    },
    4: {  # ItemSubclassArmor
        0: "Misc", 1: "Cloth", 2: "Leather", 3: "Mail", 4: "Plate",
        5: "Buckler", 6: "Shield", 7: "Libram", 8: "Idol", 9: "Totem",
        10: "Sigil",
    },
    5: {0: "Reagent"},  # ItemSubclassReagent
    6: {  # ItemSubclassProjectile
        0: "Wand", 1: "Bolt", 2: "Arrow", 3: "Bullet", 4: "Thrown",
    },
    7: {  # ItemSubclassTradeGoods
        0: "Trade Goods", 1: "Parts", 2: "Explosives", 3: "Devices",
        4: "Jewelcrafting", 5: "Cloth", 6: "Leather", 7: "Metal & Stone",
        8: "Meat", 9: "Herb", 10: "Elemental", 11: "Other",
        12: "Enchanting", 13: "Material", 14: "Armor Enchantment",
        15: "Weapon Enchantment",
    },
    8: {0: "Generic"},  # ItemSubclassGeneric
    9: {  # ItemSubclassRecipe
        0: "Book", 1: "Leatherworking Pattern", 2: "Tailoring Pattern",
        3: "Engineering Schematic", 4: "Blacksmithing", 5: "Cooking Recipe",
        6: "Alchemy Recipe", 7: "First Aid Manual", 8: "Enchanting Formula",
        9: "Fishing Manual", 10: "Jewelcrafting Recipe",
    },
    10: {0: "Money"},  # ItemSubclassMoney
    11: {  # ItemSubclassQuiver
        0: "(obsolete Quiver0)", 1: "(obsolete Quiver1)", 2: "Quiver",
        3: "Ammo Pouch",
    },
    12: {0: "Quest"},  # ItemSubclassQuest
    13: {0: "Key", 1: "Lockpick"},  # ItemSubclassKey
    14: {0: "Permanent"},  # ItemSubclassPermanent
    15: {  # ItemSubclassJunk
        0: "Junk", 1: "Reagent", 2: "Pet", 3: "Holiday", 4: "Other",
        5: "Mount",
    },
    16: {  # ItemSubclassGlyph
        1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest",
        6: "Death Knight", 7: "Shaman", 8: "Mage", 9: "Warlock", 11: "Druid",
    },
}

# ItemModType. Slots 22/23/24/33 are this fork's own repurposing (see the
# enum's inline comments in ItemTemplate.h) - stock AzerothCore/wowhead
# label these ITEM_MOD_HIT_TAKEN_MELEE/RANGED/SPELL_RATING and
# ITEM_MOD_HIT_TAKEN_RATING instead. Don't copy those stock names in from
# memory or an external item database; this fork's values are different.
# `ITEM_MOD_CUSTOM`/`ITEM_MOD_DEPRECATED` flag which entries need a caller
# to annotate that (kept out of the name itself so lib/loot.py's compact
# one-line stat summaries don't have to carry the annotation too).
ITEM_MOD_NAMES = {
    0: "Mana", 1: "Health", 3: "Agility", 4: "Strength", 5: "Intellect",
    6: "Spirit", 7: "Stamina", 12: "Defense Rating", 13: "Dodge Rating",
    14: "Parry Rating", 15: "Block Rating", 16: "Melee Hit Rating",
    17: "Ranged Hit Rating", 18: "Spell Hit Rating", 19: "Melee Crit Rating",
    20: "Ranged Crit Rating", 21: "Spell Crit Rating", 22: "Mastery Rating",
    23: "Versatility Rating", 24: "Cooldown Rating",
    25: "Crit Taken Melee Rating", 26: "Crit Taken Ranged Rating",
    27: "Crit Taken Spell Rating", 28: "Melee Haste Rating",
    29: "Ranged Haste Rating", 30: "Spell Haste Rating", 31: "Hit Rating",
    32: "Crit Rating", 33: "Proc Rating", 34: "Crit Taken Rating",
    35: "Resilience Rating", 36: "Haste Rating", 37: "Expertise Rating",
    38: "Attack Power", 39: "Ranged Attack Power",
    41: "Spell Healing Done", 42: "Spell Damage Done", 43: "Mana Regen",
    44: "Armor Penetration Rating", 45: "Spell Power", 46: "Health Regen",
    47: "Spell Penetration", 48: "Block Value",
}

ITEM_MOD_CUSTOM = {22, 23, 24, 33}
ITEM_MOD_DEPRECATED = {41, 42}

# InventoryType (ItemTemplate.h).
INVENTORY_TYPE_NAMES = {
    0: "Non-equip", 1: "Head", 2: "Neck", 3: "Shoulders", 4: "Body (shirt)",
    5: "Chest", 6: "Waist", 7: "Legs", 8: "Feet", 9: "Wrists", 10: "Hands",
    11: "Finger", 12: "Trinket", 13: "Weapon (1H)", 14: "Shield",
    15: "Ranged", 16: "Cloak", 17: "Weapon (2H)", 18: "Bag", 19: "Tabard",
    20: "Robe (chest)", 21: "Main Hand", 22: "Off Hand", 23: "Holdable",
    24: "Ammo", 25: "Thrown", 26: "Ranged (right)", 27: "Quiver",
    28: "Relic",
}
