"""
Crafting rework C7: premium enchants, flasks, Inscription raid buff scrolls, boss runes and Darkmoon tarots
(`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md` decisions 4, 5 and 6, rulings 2026-11-12, section
6.4). Pure data; declared by `source/world/crafting_consumables.py`, the items written by
`write_crafting_consumable_items.py`.

**Premium enchants** (decision 4 A): endgame only (enchant MinLevel 60), Enchanting, learned from T1 raid recipe items
(they join the T1 recipe pool). Item procs get no Proc Chance (Systems section 5): each is a flat chance with an
internal cooldown, sized near the slot's basic enchant on average. Crusader and Spellsurge buff the higher of two
primaries (`spell_crafting_premium_higher_primary`); Steelweave's absorb is a percent of maximum health
(`spell_crafting_max_health_absorb`).

**Flasks** (decision 5 A, sizes 6.4): one vanilla set for T1-T3. Titans is +60 Stamina, Supreme Power +60 Intellect,
Distilled Wisdom +60 Spirit; two new ones, Flask of Might (+40 Strength) and Flask of Grace (+40 Agility). Chromatic
Resistance stays. One hour, through death (stock flask shape), both elixir slots. Taught by the Azeroth Alchemy trainer.

**Raid buff scrolls** (6a): one per standing raid buff category (shadow resistance and the shaman-only spell haste
left out), cast on the raid in range like Gift of the Wild, one hour, at the class buff's base value, in the class
buff's spell group so the two never stack. Inscription trainer.

**Rune of Empowerment** (6b, rulings 6.4 and 2026-11-12): used on a boss (a 3 s cast at 60 yd), it gives the user a 24
hour buff against that boss (by creature entry, so every pull of it that day; real time, through death and logout):
+5% damage to it, 8% less damage from it, +5% healing while fighting it. Consumed; a 24-hour cooldown
(`custom_crafting_runes.cpp`). Inscription trainer.

**Darkmoon** (6c): a Darkmoon Tarot (Inscription trainer) opens into a random card of the four vanilla decks; a
finished deck turns into its trinket on use (the deck's Faire quest start is dropped).
"""

from __future__ import annotations

from dataclasses import dataclass

ENCHANTING, INSCRIPTION, ALCHEMY = 333, 773, 171
TRAINER = {INSCRIPTION: 121, ALCHEMY: 67}
TRAIN_COST = 50000

# Ids (decision 10): spells 208800-208999, SkillLineAbility 31950-31999, items 78800-78999, enchants 5940-5999.
ITEM_RANGE = range(78800, 79000)

# Stats (ItemModType / UnitMods misc values as the auras read them).
STAT_STRENGTH, STAT_AGILITY, STAT_STAMINA, STAT_INTELLECT, STAT_SPIRIT = 0, 1, 2, 3, 4
CR_PARRY_MASK = 1 << 3  # CombatRating CR_PARRY for SPELL_AURA_MOD_RATING
AURA_MOD_STAT, AURA_MOD_RATING, AURA_SCHOOL_ABSORB, AURA_PROC_TRIGGER_SPELL = 29, 189, 69, 42
SCHOOL_MASK_ALL = 127

# --- Premium enchants -------------------------------------------------------------------------------------------------
PROC_DONE_MELEE = 0x4 | 0x10  # auto attack, melee-class spell
PROC_DONE_SPELL = 0x4000 | 0x10000  # magic spell, positive or negative
PROC_TAKEN_MELEE = 0x8 | 0x20
PROC_PHASE_CAST, PROC_PHASE_HIT = 1, 2
FLASK_DURATION_INDEX = 42  # 1 hour (stock flasks)

# Equipped item masks (C6 lib/crafting_enchants_data.py).
ONE_HAND = (1 << 0) | (1 << 4) | (1 << 7) | (1 << 13) | (1 << 15)
TWO_HAND = (1 << 1) | (1 << 5) | (1 << 6) | (1 << 8) | (1 << 10)
STAFF = 1 << 10
ARMOR_CLOTH, ARMOR_ANY, ARMOR_SHIELD = 2, 0b11111, 1 << 6
INV_FEET, INV_BACK, INV_SHIELD = 8, 16, 14


def _inv(*types: int) -> int:
    mask = 0
    for t in types:
        mask |= 1 << t
    return mask


WEAPON_TARGET = (2, ONE_HAND | TWO_HAND, 0)
FEET_TARGET = (4, ARMOR_ANY, _inv(INV_FEET))
BACK_TARGET = (4, ARMOR_CLOTH, _inv(INV_BACK))
SHIELD_TARGET = (4, ARMOR_SHIELD, _inv(INV_SHIELD))


@dataclass(frozen=True)
class Buff:
    spell: int
    name: str
    aura: int
    misc: int
    amount: int
    duration_ms: int
    text: str


BUFFS = {
    "str": Buff(208810, "Crusader", AURA_MOD_STAT, STAT_STRENGTH, 60, 15000, "Strength increased by $s1."),
    "agi": Buff(208811, "Crusader", AURA_MOD_STAT, STAT_AGILITY, 60, 15000, "Agility increased by $s1."),
    "int": Buff(208812, "Spellsurge", AURA_MOD_STAT, STAT_INTELLECT, 60, 15000, "Intellect increased by $s1."),
    "spi": Buff(208813, "Spellsurge", AURA_MOD_STAT, STAT_SPIRIT, 60, 15000, "Spirit increased by $s1."),
    "parry": Buff(208814, "Blade Warding", AURA_MOD_RATING, CR_PARRY_MASK, 90, 10000, "Parry rating increased by $s1."),
    "absorb": Buff(208815, "Steelweave", AURA_SCHOOL_ABSORB, SCHOOL_MASK_ALL, 3, 10000,
                   "Absorbs damage equal to $s1% of your maximum health."),
}


@dataclass(frozen=True)
class Proc:
    aura_spell: int
    name: str
    buff: str  # BUFFS key; a higher-primary proc names the first of its pair
    proc_flags: int
    chance: float
    cooldown_ms: int
    phase: int = 0
    script: str | None = None
    description: str = ""


PROCS = {
    "crusader": Proc(208800, "Crusader", "str", PROC_DONE_MELEE, 10.0, 45000, phase=PROC_PHASE_HIT,
                     script="spell_crafting_premium_higher_primary",
                     description="Your melee attacks have a chance to increase your Strength or Agility, whichever "
                                 "is higher, by 60 for 15 sec. 45 sec internal cooldown."),
    "spellsurge": Proc(208801, "Spellsurge", "int", PROC_DONE_SPELL, 10.0, 45000, phase=PROC_PHASE_CAST,
                       script="spell_crafting_premium_higher_primary",
                       description="Your spells have a chance to increase your Intellect or Spirit, whichever is "
                                   "higher, by 60 for 15 sec. 45 sec internal cooldown."),
    "warding": Proc(208802, "Blade Warding", "parry", PROC_TAKEN_MELEE, 10.0, 45000,
                    description="When struck in melee you have a chance to gain 90 Parry Rating for 10 sec. 45 sec "
                                "internal cooldown."),
    "steelweave": Proc(208803, "Steelweave", "absorb", PROC_TAKEN_MELEE, 5.0, 30000,
                       description="When struck in melee you have a chance to absorb damage equal to 3% of your "
                                   "maximum health for 10 sec. 30 sec internal cooldown."),
}
STOCK_MINOR_SPEED = 13889  # Enchant Boots - Minor Speed's equip spell (+8% run speed)
STOCK_SUBTLETY = 25070  # Enchant Cloak - Subtlety's equip spell (2% less threat)
COOLDOWN_HASTE = 24


@dataclass(frozen=True)
class Premium:
    key: str
    enchant: int
    text: str
    proc: str | None  # PROCS key
    extra: tuple  # ("spell", id) / ("stat", stat, amount) parts besides the proc
    item: int
    use_spell: int
    recipe_spell: int
    sla: int
    recipe_item: int
    learn_spell: int
    item_name: str
    target: tuple


def _premium(n: int, key: str, enchant_offset: int, text: str, proc, extra, name: str, target) -> Premium:
    return Premium(key, 5940 + enchant_offset, text, proc, extra, 78800 + n, 208820 + n, 208830 + n, 31950 + n,
                   78810 + n, 208840 + n, name, target)


PREMIUMS = (
    _premium(0, "crusader", 0, "Crusader", "crusader", (), "Scroll of Enchant Weapon - Crusader", WEAPON_TARGET),
    _premium(1, "spellsurge", 1, "Spellsurge", "spellsurge", (), "Scroll of Enchant Weapon - Spellsurge",
             WEAPON_TARGET),
    _premium(2, "blade_warding", 2, "Blade Warding", "warding", (), "Scroll of Enchant Weapon - Blade Warding",
             WEAPON_TARGET),
    _premium(3, "shield_warding", 2, "Blade Warding", "warding", (), "Scroll of Enchant Shield - Blade Warding",
             SHIELD_TARGET),
    _premium(4, "swiftness", 3, "Swiftness and +4 Cooldown Haste Rating", None,
             (("spell", STOCK_MINOR_SPEED), ("stat", COOLDOWN_HASTE, 4)), "Scroll of Enchant Boots - Swiftness",
             FEET_TARGET),
    _premium(5, "subtlety", 4, "Subtlety", None, (("spell", STOCK_SUBTLETY),), "Scroll of Enchant Cloak - Subtlety",
             BACK_TARGET),
    _premium(6, "steelweave", 5, "Steelweave", "steelweave", (), "Scroll of Enchant Cloak - Steelweave",
             BACK_TARGET),
)
# Reagents of every premium enchant recipe (Enchanting at the level-60 tier, plus the T1 material).
PREMIUM_REAGENTS = ((16204, 12), (16203, 6), (14344, 4), (20725, 1), (17010, 2))  # dust, essence, shard, crystal, core
PREMIUM_ENCHANT_MIN_LEVEL = 60

# --- Flasks -----------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Flask:
    spell: int  # the buff (stock or new)
    name: str
    stat: int
    amount: int
    item: int
    recipe_spell: int  # stock or new
    sla: int | None  # None: the stock recipe's own SkillLineAbility row
    reagents: tuple = ()  # new recipes only


FLASKS = (
    Flask(17626, "Flask of the Titans", STAT_STAMINA, 60, 13510, 17635, None),
    Flask(17628, "Flask of Supreme Power", STAT_INTELLECT, 60, 13512, 17637, None),
    Flask(17627, "Flask of Distilled Wisdom", STAT_SPIRIT, 60, 13511, 17636, None),
    Flask(208850, "Flask of Might", STAT_STRENGTH, 40, 78820, 208852, 31957,
          ((13465, 7), (8846, 3), (13468, 1), (8925, 1))),  # Mountain Silversage, Gromsblood, Black Lotus, vial
    Flask(208851, "Flask of Grace", STAT_AGILITY, 40, 78821, 208853, 31958,
          ((13463, 7), (8839, 3), (13468, 1), (8925, 1))),  # Dreamfoil, Blindweed, Black Lotus, vial
)
STAT_NAME = {STAT_STRENGTH: "Strength", STAT_AGILITY: "Agility", STAT_STAMINA: "Stamina",
             STAT_INTELLECT: "Intellect", STAT_SPIRIT: "Spirit"}
FLASK_GROUPS = (1, 2)  # Battle Elixir, Guardian Elixir (a flask fills both)

# --- Raid buff scrolls ------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Scroll:
    key: str
    name: str  # the item ("Scroll of ...") and the buff
    effects: tuple  # (aura, misc, amount) each
    groups: tuple  # spell_group ids of the class buff it copies
    source: str  # the class buff it copies
    text: str  # the aura tooltip


SCROLLS = (
    Scroll("kings", "Scroll of Kings", ((137, -1, 10),), (1391,), "Blessing of Kings",
           "All stats increased by $s1%."),
    Scroll("wild", "Scroll of the Wild", ((22, 1, 410), (29, -1, 19), (143, 126, 28)), (1089,), "Gift of the Wild",
           "Armor increased by $s1, all attributes by $s2 and all resistances by $s3."),
    Scroll("fortitude", "Scroll of Fortitude", ((29, STAT_STAMINA, 54),), (1084,), "Prayer of Fortitude",
           "Stamina increased by $s1."),
    Scroll("command", "Scroll of Command", ((230, 0, 297),), (1093,), "Commanding Shout",
           "Maximum health increased by $s1."),
    Scroll("brilliance", "Scroll of Brilliance", ((29, STAT_INTELLECT, 31),), (1083,), "Arcane Brilliance",
           "Intellect increased by $s1."),
    Scroll("devotion", "Scroll of Devotion", ((29, STAT_SPIRIT, 40),), (1085,), "Prayer of Spirit",
           "Spirit increased by $s1."),
    Scroll("winter", "Scroll of Winter's Horn", ((29, STAT_STRENGTH, 86), (29, STAT_AGILITY, 86)), (1088, 1253),
           "Horn of Winter", "Strength and Agility increased by $s1."),
    Scroll("stoneskin", "Scroll of Stoneskin", ((22, 1, 913),), (1086,), "Devotion Aura", "Armor increased by $s1."),
    Scroll("battle", "Scroll of Battle", ((99, 0, 414), (124, 0, 414)), (1004,), "Battle Shout",
           "Attack power increased by $s1."),
    Scroll("trueshot", "Scroll of True Aim", ((166, 0, 10), (167, 0, 10)), (1390,), "Trueshot Aura",
           "Attack power increased by $s1%."),
    Scroll("tempest", "Scroll of the Tempest", ((138, 0, 10), (140, 0, 10)), (1022,), "Air Attunement",
           "Melee and ranged attack speed increased by $s1%."),
    Scroll("alacrity", "Scroll of Alacrity", ((193, 0, 3),), (1054,), "Improved Moonkin Form",
           "Haste increased by $s1%."),
    Scroll("insight", "Scroll of Insight", ((57, 0, 5),), (1036,), "Moonkin Aura",
           "Spell critical strike chance increased by $s1%."),
    Scroll("pack", "Scroll of the Pack", ((52, 0, 5),), (1025,), "Leader of the Pack",
           "Melee and ranged critical strike chance increased by $s1%."),
    Scroll("flame", "Scroll of Flame", ((13, 126, 140), (135, 127, 140)), (1048,), "Fire Attunement",
           "Spell power increased by $s1."),
    Scroll("empowerment", "Scroll of Empowerment", ((79, 127, 3),), (1056,), "Arcane Empowerment",
           "Damage done increased by $s1%."),
    Scroll("wisdom", "Scroll of Wisdom", ((85, 0, 67),), (1105,), "Blessing of Wisdom",
           "Restores $s1 mana every 5 sec."),
)
# A scroll never joins a stack-rule-1 (exclusive) class group: landing on a raid member, it would remove their own
# aura, a passive talent aura (Abomination's Might, Unleashed Rage) until they relog (review B1). Those categories get
# a wrapper group of their own, stack rule 3 (only the highest of each aura type counts), holding the class group and
# the scroll: new group -> (nested class group, its name).
EXCLUSIVE_CLASS_GROUPS = (1006, 1029)  # All Stats Percentage, Percentage AP Buffs (stack rule 1)
WRAPPER_GROUPS = {
    1390: (-1029, "Percentage AP Buffs and the Scroll of True Aim: the highest counts"),
    1391: (-1006, "All Stats Percentage and the Scroll of Kings: the highest counts"),
}
STACK_RULE_SAME_EFFECT = 3
SCROLL_SPELL_BASE, SCROLL_RECIPE_BASE, SCROLL_SLA_BASE, SCROLL_ITEM_BASE = 208860, 208880, 31960, 78830
SCROLL_DURATION_MS = 3600000
SCROLL_TARGET, SCROLL_RADIUS_INDEX = 56, 30301  # TARGET_UNIT_CASTER_AREA_RAID and Gift of the Wild's radius
SCROLL_REAGENTS = ((43116, 2), (43123, 2), (39354, 1))  # Lion's Ink, Ink of the Sky, Light Parchment


def number_free(text: str) -> str:
    """An aura tooltip with its `$sN` numbers taken out (.agents/docs/systems/custom-spells.md: aura text placeholders
    do not render reliably in-game, so aura texts stay number-free)."""
    import re  # noqa: PLC0415

    text = re.sub(r" equal to \$s\d+%? of your maximum health", "", text)
    text = re.sub(r"Armor increased by \$s1, all attributes by \$s2 and all resistances by \$s3",
                  "Armor, all attributes and all resistances increased", text)
    text = re.sub(r" (by|to) \$s\d+%?", "", text)
    text = re.sub(r"\$s\d+%? ?", "", text)
    return re.sub(r"\s+", " ", text).strip()


def scroll_ids(n: int) -> tuple[int, int, int, int]:
    """(buff spell, recipe spell, SkillLineAbility, item) of SCROLLS[n]."""
    return SCROLL_SPELL_BASE + n, SCROLL_RECIPE_BASE + n, SCROLL_SLA_BASE + n, SCROLL_ITEM_BASE + n


# --- Boss runes -------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Rune:
    name: str
    spell: int
    recipe_spell: int
    sla: int
    item: int
    warding_pct: int  # EFFECT_0 (the dummy on the boss): less damage taken from the boss
    damage_pct: int  # EFFECT_1 (the periodic dummy that holds the boss entry after the cast): more damage to it
    healing_pct: int  # EFFECT_2 (healing done percent, on only while fighting the boss)
    text: str


# One rune with all three effects (user 2026-11-12, replacing Ruin / Warding / Mending): each role uses the part it
# needs.
RUNE = Rune("Rune of Empowerment", 208900, 208905, 31980, 78850, 8, 5, 5,
            "you deal $s2% increased damage to the selected boss, take $s1% less damage from it and heal for $s3% "
            "more while fighting it.")
RUNE_CATEGORY = 1310  # spellcategory_dbc (ids.yaml spellcategory); the rune's 24 hour cooldown
RUNE_COOLDOWN_MS = 86400000
RUNE_DURATION_MS = 86400000  # a 24 hour buff on the user, real time (user 2026-11-12)
# A 3 s cast (move or press Escape to cancel a wrong target; the rune is spent and the cooldown starts only when the
# cast finishes) at 60 yd, so it can be bound from outside the pull (user 2026-11-12).
RUNE_CAST_MS, RUNE_RANGE_YARDS = 3000, 60.0
AURA_MOD_HEALING_DONE_PERCENT = 136  # the rune's EFFECT_2, switched by the script's tick (review B3)
RUNE_REAGENTS = ((43119, 2), (43121, 4), (39354, 2))  # Royal Ink, Fiery Ink, Light Parchment

# --- Darkmoon ---------------------------------------------------------------------------------------------------------
TAROT_ITEM, TAROT_RECIPE, TAROT_SLA = 78860, 208910, 31985
TAROT_REAGENTS = ((43119, 1), (43116, 3), (43123, 3), (39354, 2))
# Deck item -> (its trinket, the use spell that makes it).
DECKS = {19228: (19288, 208911), 19257: (19287, 208912), 19267: (19289, 208913), 19277: (19290, 208914)}
DECK_NAMES = {19228: "Beasts Deck", 19257: "Warlords Deck", 19267: "Elementals Deck", 19277: "Portals Deck"}
CARDS = (
    19227, 19230, 19231, 19232, 19233, 19234, 19235, 19236,  # Beasts, Ace to Eight
    19258, 19259, 19260, 19261, 19262, 19263, 19264, 19265,  # Warlords
    19268, 19269, 19270, 19271, 19272, 19273, 19274, 19275,  # Elementals
    19276, 19278, 19279, 19280, 19281, 19282, 19283, 19284,  # Portals
)
