"""
Crafting rework C6: the enchant table (pure data, no declarations; source/world/crafting_enchants.py declares from it).

The DSL file `crafting_enchants.py` declares everything from this table, and `write_enchant_items.py` writes the enchant
items' hand-written `item_template` SQL and `items.csv` rows from it, so the two can't drift
(`lib/test_crafting_enchants.py` checks both). Lives in lib/ so the DSL file, the tests and the SQL writer import it
the same way.

Rulings: `.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md` sections 5 and 6 (user 2026-11-11).

- Every enchant is an item: a profession's create-item recipe makes it, and the item's on-use spell applies the enchant
  (SPELL_EFFECT_ENCHANT_ITEM 53 into the permanent slot). Anyone can apply it: no enchant carries a RequiredSkill.
- Two sets of **basic** options (flat stats), both taught by the profession trainers: a **leveling** set at half size
  with no level requirement, and an **endgame** set gated to level 60 (item RequiredLevel and enchant MinLevel).
  Premium options (procs, movement speed, ...) are endgame recipes for a later pass.
- Sizes (budget points, every primary and rating stat costs 1, MP5 costs 5 and rounds up like the Lustrous gem):
  endgame major 12 / medium 9 / minor 7 / two-hand 14 (two one-hand weapons); leveling 6 / 5 / 4 / 8, MP5 1.
- Slot families: P = Strength, Agility, Intellect, Spirit; T = Crit, Haste, Mastery, Versatility; no Stamina, Hit,
  Expertise or Defense. Neck and rings share one item ("Jewelry"), as ruled ("rings the same as neck").
- Engineering tinkers (endgame only): on-use enchants (type 7) in the same permanent slot, so a tinker and a normal
  enchant replace each other. Head and ranged only; anyone can use them.
- Blacksmithing belt buckle (endgame only): a prismatic socket (effect 156, enchant type 8) in its own slot.
"""

# ItemMod (lib/dsl/constants.py ItemMod; ItemTemplate.h ItemModType).
AGILITY = 3
STRENGTH = 4
INTELLECT = 5
SPIRIT = 6
DODGE = 13
PARRY = 14
BLOCK = 15
MASTERY = 22
VERSATILITY = 23
COOLDOWN_HASTE = 24
CRIT = 32
PROC_CHANCE = 33
HASTE = 36
MP5 = 43

FORBIDDEN_STATS = {7, 12, 16, 17, 18, 31, 37}  # Stamina, Defense, the three Hits, Hit Rating, Expertise

STAT_TEXT = {
    STRENGTH: "Strength", AGILITY: "Agility", INTELLECT: "Intellect", SPIRIT: "Spirit",
    CRIT: "Critical Strike Rating", HASTE: "Haste Rating", MASTERY: "Mastery Rating",
    VERSATILITY: "Versatility Rating", PROC_CHANCE: "Proc Chance Rating", COOLDOWN_HASTE: "Cooldown Haste Rating",
    MP5: "mana every 5 sec.", BLOCK: "Block Rating", DODGE: "Dodge Rating", PARRY: "Parry Rating",
}
# The stat's word in an item name.
STAT_WORD = {
    STRENGTH: "Strength", AGILITY: "Agility", INTELLECT: "Intellect", SPIRIT: "Spirit",
    CRIT: "Critical Strike", HASTE: "Haste", MASTERY: "Mastery", VERSATILITY: "Versatility",
    PROC_CHANCE: "Proc Chance", COOLDOWN_HASTE: "Cooldown Haste", MP5: "Mana Regeneration",
    BLOCK: "Block", DODGE: "Dodge", PARRY: "Parry",
}

P = (STRENGTH, AGILITY, INTELLECT, SPIRIT)
T = (CRIT, HASTE, MASTERY, VERSATILITY)

# Professions: skill line and the Azeroth trainer list (research 1.8).
ENCHANTING, TAILORING, LEATHERWORKING, ENGINEERING, INSCRIPTION, BLACKSMITHING = 333, 197, 165, 202, 773, 164
TRAINER = {ENCHANTING: 96, TAILORING: 74, LEATHERWORKING: 61, ENGINEERING: 92, INSCRIPTION: 121, BLACKSMITHING: 60}

# Spell target masks (Item::IsFitToSpellRequirements): (EquippedItemClass, EquippedItemSubclass mask,
# EquippedItemInvTypes mask).
ITEM_CLASS_WEAPON, ITEM_CLASS_ARMOR = 2, 4
ARMOR_ANY = 0b11111  # misc, cloth, leather, mail, plate (the stock thread / inscription / buckle mask 31)
ARMOR_MISC = 1  # necks, rings, held in off-hand
ARMOR_CLOTH = 2  # cloaks are cloth
ARMOR_SHIELD = 1 << 6
ONE_HAND = (1 << 0) | (1 << 4) | (1 << 7) | (1 << 13) | (1 << 15)  # axe, mace, sword, fist, dagger
TWO_HAND = (1 << 1) | (1 << 5) | (1 << 6) | (1 << 8) | (1 << 10)  # 2H axe, 2H mace, polearm, 2H sword, staff
RANGED_GUNS = (1 << 2) | (1 << 3) | (1 << 18)  # bow, gun, crossbow (the stock scope mask 0x4000C)


def _inv(*types: int) -> int:
    mask = 0
    for inventory_type in types:
        mask |= 1 << inventory_type
    return mask


# key -> slot. `size` is the size class; `form` picks the item shape and name. Order fixes the ids, never reorder.
# (key, profession, size, stats, form, slot word, target (class, subclass mask, inv mask), "Permanently ..." phrase)
SLOTS = (
    ("head", ENGINEERING, "major", P, "lens", "Head", (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(1)),
     "Permanently attach a lens to a helm"),
    ("shoulder", INSCRIPTION, "medium", T, "inscription", "Shoulder", (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(3)),
     "Permanently inscribe shoulder armor"),
    ("chest", ENCHANTING, "major", P, "scroll", "Chest", (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(5, 20)),
     "Permanently enchant chest armor"),
    ("legs", TAILORING, "major", T + (BLOCK, DODGE, PARRY), "spellthread", "Legs",
     (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(7)), "Permanently embroider spellthread into pants"),
    ("hands", LEATHERWORKING, "medium", T, "kit", "Hands", (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(10)),
     "Permanently reinforce gloves"),
    ("feet", ENCHANTING, "medium", (PROC_CHANCE, COOLDOWN_HASTE, MP5, DODGE), "scroll", "Boots",
     (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(8)), "Permanently enchant boots"),
    ("wrist", ENCHANTING, "minor", P, "scroll", "Bracer", (ITEM_CLASS_ARMOR, ARMOR_ANY, _inv(9)),
     "Permanently enchant bracers"),
    ("back", ENCHANTING, "minor", (PROC_CHANCE, COOLDOWN_HASTE, DODGE, PARRY), "scroll", "Cloak",
     (ITEM_CLASS_ARMOR, ARMOR_CLOTH, _inv(16)), "Permanently enchant a cloak"),
    ("jewelry", ENCHANTING, "minor", (PROC_CHANCE, COOLDOWN_HASTE, MP5, BLOCK), "scroll", "Jewelry",
     (ITEM_CLASS_ARMOR, ARMOR_MISC, _inv(2, 11)), "Permanently enchant a necklace or ring"),
    ("weapon", ENCHANTING, "minor", P, "scroll", "Weapon", (ITEM_CLASS_WEAPON, ONE_HAND, 0),
     "Permanently enchant a one-handed melee weapon"),
    ("twohand", ENCHANTING, "twohand", P, "scroll", "2H Weapon", (ITEM_CLASS_WEAPON, TWO_HAND, 0),
     "Permanently enchant a two-handed melee weapon"),
    ("shield", ENCHANTING, "minor", (BLOCK, DODGE, PARRY, INTELLECT), "scroll", "Shield",
     (ITEM_CLASS_ARMOR, ARMOR_SHIELD, 0), "Permanently enchant a shield"),
    ("offhand", ENCHANTING, "minor", (INTELLECT, SPIRIT, MP5), "scroll", "Off-Hand",
     (ITEM_CLASS_ARMOR, ARMOR_MISC, _inv(23)), "Permanently enchant an off-hand item"),
    ("ranged", ENGINEERING, "minor", (AGILITY, CRIT, HASTE, MASTERY), "scope", "Ranged",
     (ITEM_CLASS_WEAPON, RANGED_GUNS, 0), "Permanently attach a scope to a bow, gun or crossbow"),
)

SIZES = {
    "endgame": {"major": 12, "medium": 9, "minor": 7, "twohand": 14},
    "leveling": {"major": 6, "medium": 5, "minor": 4, "twohand": 8},
}
MP5_SIZES = {
    "endgame": {"major": 3, "medium": 2, "minor": 2, "twohand": 3},
    "leveling": {"major": 1, "medium": 1, "minor": 1, "twohand": 1},
}
TIER_WORD = {"leveling": "Lesser", "endgame": "Greater"}

# --- ids (research section 6, decision 14; a hand-picked item block, see source/ids.yaml) -----------------------------
# Per set, the n-th (slot, stat) in SLOTS order takes base + n.
ENCHANT_BASE = {"leveling": 5800, "endgame": 5860}
ITEM_BASE = {"leveling": 79000, "endgame": 79060}
USE_SPELL_BASE = {"leveling": 207200, "endgame": 207260}
CRAFT_SPELL_BASE = {"leveling": 207340, "endgame": 207400}
SLA_BASE = {"leveling": 31020, "endgame": 31080}

# --- reagents (stock items) -------------------------------------------------------------------------------------------
ILLUSION_DUST, LESSER_ETERNAL, GREATER_ETERNAL, LARGE_BRILLIANT = 16204, 16202, 16203, 14344
RUNECLOTH, RUNE_THREAD, MAGEWEAVE, HEAVY_SILKEN_THREAD = 14047, 14341, 4338, 8343
RUGGED_LEATHER, ENCHANTED_LEATHER, THICK_LEATHER = 8170, 12810, 4304
THORIUM_BAR, THORIUM_WIDGET, ARCANITE_BAR, MITHRIL_BAR, MITHRIL_CASING = 12359, 15994, 12360, 3860, 10561
LIONS_INK, FIERY_INK, INK_OF_THE_SKY, JADEFIRE_INK, ROYAL_INK = 43116, 43121, 43123, 43118, 43119
LIGHT_PARCHMENT = 39354

# Inscription uses one ink per stat color (the squish: pigments by herb color, research 13d): Crit red, Haste yellow,
# Mastery blue, Versatility green; the endgame recipe adds the rare ink.
INK_FOR_STAT = {CRIT: FIERY_INK, HASTE: LIONS_INK, MASTERY: INK_OF_THE_SKY, VERSATILITY: JADEFIRE_INK}

_SIZE_STEP = {"minor": 0, "medium": 1, "major": 2, "twohand": 2}


def reagents(profession: int, tier: str, size: str, stat: int) -> tuple[tuple[int, int], ...]:
    """The recipe's reagents: the profession's level-60 materials (endgame) or mid-level ones (leveling), more for
    bigger slots. Enchanting uses the squished survivors only (one dust and two essences, research 13a)."""
    step = _SIZE_STEP[size]
    endgame = tier == "endgame"
    if profession == ENCHANTING:
        if endgame:
            out = [(ILLUSION_DUST, 4 + 2 * step), (GREATER_ETERNAL, 1 + (step > 0))]
            if step == 2:
                out.append((LARGE_BRILLIANT, 1))
            return tuple(out)
        return ((ILLUSION_DUST, 2 + step), (LESSER_ETERNAL, 1 + (step == 2)))
    if profession == TAILORING:
        return ((RUNECLOTH, 6), (RUNE_THREAD, 2)) if endgame else ((MAGEWEAVE, 6), (HEAVY_SILKEN_THREAD, 2))
    if profession == LEATHERWORKING:
        return ((RUGGED_LEATHER, 4), (ENCHANTED_LEATHER, 1)) if endgame else ((THICK_LEATHER, 4), (LESSER_ETERNAL, 1))
    if profession == ENGINEERING:
        if endgame:
            return ((THORIUM_WIDGET, 1 + (step == 2)), (THORIUM_BAR, 2))
        return ((MITHRIL_CASING, 1), (MITHRIL_BAR, 2))
    if profession == INSCRIPTION:
        ink = INK_FOR_STAT[stat]
        if endgame:
            return ((ink, 3), (ROYAL_INK, 1), (LIGHT_PARCHMENT, 1))
        return ((ink, 2), (LIGHT_PARCHMENT, 1))
    raise ValueError(f"no reagents for profession {profession}")


def _amount(tier: str, size: str, stat: int) -> int:
    return (MP5_SIZES if stat == MP5 else SIZES)[tier][size]


def item_name(tier: str, form: str, slot_word: str, stat: int) -> str:
    tier_word, stat_word = TIER_WORD[tier], STAT_WORD[stat]
    if form == "scroll":
        return f"Scroll of Enchant {slot_word} - {tier_word} {stat_word}"
    if form == "lens":
        return f"{tier_word} {stat_word} Lens"
    if form == "inscription":
        return f"{tier_word} Inscription of {stat_word}"
    if form == "spellthread":
        return f"{tier_word} {stat_word} Spellthread"
    if form == "kit":
        return f"{tier_word} {stat_word} Armor Kit"
    if form == "scope":
        return f"{tier_word} {stat_word} Scope"
    raise ValueError(form)


def enchant_text(stat: int, amount: int) -> str:
    """The enchant's tooltip line, as the gems write it."""
    return f"+{amount} {STAT_TEXT[stat]}"


def use_text(phrase: str, stat: int, amount: int) -> str:
    """The use spell's description (the item's "Use:" line)."""
    if stat == MP5:
        return f"{phrase} to restore {amount} mana every 5 sec."
    return f"{phrase} to increase {STAT_TEXT[stat]} by {amount}."


# Item looks (stock displays): the WotLK enchanting scroll, armor kit, spellthread (Mystic for leveling, Brilliant for
# endgame), focusing lens, Greater Inscription, scope and Eternal Belt Buckle.
DISPLAY = {"scroll": 811, "kit": 26388, "lens": 22651, "inscription": 55782, "scope": 7326}
SPELLTHREAD_DISPLAY = {"leveling": 42716, "endgame": 42717}
BUCKLE_DISPLAY = 53111
QUALITY = {"leveling": 1, "endgame": 2}  # Common / Uncommon
ITEM_LEVEL = {"leveling": 30, "endgame": 60}
REQUIRED_LEVEL = {"leveling": 0, "endgame": 60}
MIN_LEVEL = {"leveling": 0, "endgame": 60}
PRICE = {"leveling": (4000, 1000), "endgame": (20000, 5000)}  # (BuyPrice, SellPrice) copper
TRAIN_COST = {"leveling": 1000, "endgame": 50000}  # 10 s / 5 g, the C5 precedent


def enchants() -> list[dict]:
    """Every basic enchant, leveling first, each with its ids, stats, names, reagents and target."""
    out = []
    for tier in ("leveling", "endgame"):
        index = 0
        for key, profession, size, stats, form, slot_word, target, phrase in SLOTS:
            for stat in stats:
                amount = _amount(tier, size, stat)
                out.append({
                    "tier": tier, "slot": key, "stat": stat, "amount": amount, "size": size, "profession": profession,
                    "form": form, "target": target,
                    "enchant": ENCHANT_BASE[tier] + index, "item": ITEM_BASE[tier] + index,
                    "use_spell": USE_SPELL_BASE[tier] + index, "craft_spell": CRAFT_SPELL_BASE[tier] + index,
                    "sla": SLA_BASE[tier] + index,
                    "name": item_name(tier, form, slot_word, stat), "text": enchant_text(stat, amount),
                    "description": use_text(phrase, stat, amount),
                    "reagents": reagents(profession, tier, size, stat),
                    "display": SPELLTHREAD_DISPLAY[tier] if form == "spellthread" else DISPLAY[form],
                    "quality": QUALITY[tier], "item_level": ITEM_LEVEL[tier],
                    "required_level": REQUIRED_LEVEL[tier], "min_level": MIN_LEVEL[tier],
                    "buy": PRICE[tier][0], "sell": PRICE[tier][1], "train_cost": TRAIN_COST[tier],
                })
                index += 1
    return out


# --- Engineering tinkers (endgame, research 3b) -----------------------------------------------------------------------
# A tinker's enchant is type 7 (USE_SPELL): right-clicking the gear piece casts the effect spell. All four share the
# stock tinker category 1141 (10 s category lockout, so two can't fire together); items never get Cooldown Haste.
TINKER_CATEGORY = 1141
TINKER_CATEGORY_COOLDOWN_MS = 10000
# key -> (enchant, item, use spell, craft spell, SLA, effect spell, name, slot key, cooldown ms, effect text)
TINKERS = (
    ("hyperspeed", 5920, 79120, 207320, 207460, 31140, 207480, "Hyperspeed Lens", "head", 60000,
     "Increases your Haste Rating by $s1 for $d."),
    ("force_field", 5921, 79121, 207321, 207461, 31141, 207481, "Force Field Lens", "head", 60000,
     "Surrounds you with a force field that absorbs damage equal to 10% of your maximum health for $d."),
    ("mana_siphon", 5922, 79122, 207322, 207462, 31142, 207482, "Mana Siphon Lens", "head", 120000,
     "Restores $s1% of your maximum mana."),
    ("targeting", 5923, 79123, 207323, 207463, 31143, 207483, "Targeting Scope", "ranged", 60000,
     "Increases your Critical Strike Rating by $s1 for $d."),
)
# The tinker item's own "Use:" text (the item's use spell can't read the effect spell's $s1 / $d).
TINKER_ITEM_TEXT = {
    "hyperspeed": "Increases your Haste Rating by 60 for 12 sec. (1 Min Cooldown)",
    "force_field": "Absorbs damage equal to 10% of your maximum health for 10 sec. (1 Min Cooldown)",
    "mana_siphon": "Restores 2% of your maximum mana. (2 Min Cooldown)",
    "targeting": "Increases your Critical Strike Rating by 35 for 12 sec. (1 Min Cooldown)",
}
HYPERSPEED_HASTE = 60  # 60 x 12 s / 60 s = 12, the head enchant's size
TARGETING_CRIT = 35  # 35 x 12 s / 60 s = 7, the ranged enchant's size
FORCE_FIELD_PCT = 10  # of max health, 10 s
MANA_SIPHON_PCT = 2  # of max mana
TINKER_BUFF_MS = 12000
FORCE_FIELD_MS = 10000
TINKER_REAGENTS = ((THORIUM_WIDGET, 2), (THORIUM_BAR, 2), (ARCANITE_BAR, 1))

# --- Blacksmithing belt buckle (endgame) ------------------------------------------------------------------------------
# key -> (enchant, item, use spell, craft spell, SLA)
BUCKLE = {"enchant": 5930, "item": 79130, "use_spell": 207330, "craft_spell": 207470, "sla": 31145,
          "name": "Thorium Belt Buckle", "text": "Prismatic Socket",
          "description": "Permanently attach a thorium belt buckle onto a belt, adding a prismatic socket to the belt.",
          "reagents": ((THORIUM_BAR, 4), (ARCANITE_BAR, 1))}


def tinkers() -> list[dict]:
    slot_targets = {key: target for key, _p, _s, _st, _f, _w, target, _ph in SLOTS}
    out = []
    for key, enchant_id, item, use, craft, sla, effect, name, slot, cooldown, text in TINKERS:
        out.append({"key": key, "enchant": enchant_id, "item": item, "use_spell": use, "craft_spell": craft,
                    "sla": sla, "effect_spell": effect, "name": name, "slot": slot, "target": slot_targets[slot],
                    "cooldown_ms": cooldown, "effect_text": text})
    return out


def items() -> list[dict]:
    """Every C6 item (basic enchants, tinkers, buckle) as the item writer needs it."""
    out = []
    for row in enchants():
        out.append({"item": row["item"], "name": row["name"], "display": row["display"], "quality": row["quality"],
                    "item_level": row["item_level"], "required_level": row["required_level"], "buy": row["buy"],
                    "sell": row["sell"], "use_spell": row["use_spell"]})
    for row in tinkers():
        out.append({"item": row["item"], "name": row["name"],
                    "display": DISPLAY["scope"] if row["slot"] == "ranged" else DISPLAY["lens"], "quality": 2,
                    "item_level": 60, "required_level": 60, "buy": 40000, "sell": 10000, "use_spell": row["use_spell"]})
    out.append({"item": BUCKLE["item"], "name": BUCKLE["name"], "display": BUCKLE_DISPLAY, "quality": 2,
                "item_level": 60, "required_level": 60, "buy": 40000, "sell": 10000, "use_spell": BUCKLE["use_spell"]})
    return sorted(out, key=lambda row: row["item"])
