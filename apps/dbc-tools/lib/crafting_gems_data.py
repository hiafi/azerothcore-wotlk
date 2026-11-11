"""
Crafting rework C5: the gem table (pure data, no declarations; source/world/crafting_gems.py declares from it).

The DSL file `crafting_gems.py` declares everything from this table, and `write_gem_items.py` writes the gem items'
hand-written `item_template` SQL and `items.csv` rows from it, so the two can't drift (`lib/test_crafting_gems.py`
checks both). Lives in lib/ so the DSL file, the tests and the SQL writer import it the same way.

Rulings: `.agents/plans/crafting-rework/crafting-rework.C5-RESEARCH.md` sections 2, 3, 5 and 6 (user 2026-11-11).

- Leveling gems (Uncommon): pure red, yellow and blue, +4, no level gate. 10 stats.
- Rare gems: +8 single stat, +4/+4 hybrids, cut from the six Thorium vein gems, enchant gated to level 60.
- Epic gems: +10, +5/+5 hybrids, cut from six new epic raw gems (raid drops later), gated to level 60.
- MP5 costs 5 budget points per point (item_stat_cost): a pure MP5 gem is 2 in both qualities (decision 1 A: 10
  budget, 8 rounds up to 2 and 10 is exactly 2), a hybrid carries 1.
- Meta gems: five scripted metas, one Rare each, cut from an Azerothian Diamond, gated to level 60.
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

STAT_TEXT = {
    STRENGTH: "Strength", AGILITY: "Agility", INTELLECT: "Intellect", SPIRIT: "Spirit",
    CRIT: "Critical Strike Rating", HASTE: "Haste Rating", MASTERY: "Mastery Rating",
    VERSATILITY: "Versatility Rating", PROC_CHANCE: "Proc Chance Rating", COOLDOWN_HASTE: "Cooldown Haste Rating",
    MP5: "mana every 5 sec.", BLOCK: "Block Rating", DODGE: "Dodge Rating", PARRY: "Parry Rating",
}

# GemProperties.Type / socket color bits (ItemTemplate.h SocketColor).
META, RED, YELLOW, BLUE = 1, 2, 4, 8
ORANGE, PURPLE, GREEN = RED | YELLOW, RED | BLUE, YELLOW | BLUE

# item_template.subclass for class 3 (Gem): ItemTemplate.h ItemSubclassGem.
GEM_SUBCLASS = {RED: 0, BLUE: 1, YELLOW: 2, PURPLE: 3, GREEN: 4, ORANGE: 5, META: 6}
COLOR_TEXT = {
    RED: "Matches a Red Socket.", YELLOW: "Matches a Yellow Socket.", BLUE: "Matches a Blue Socket.",
    ORANGE: "Matches a Red or Yellow Socket.", PURPLE: "Matches a Red or Blue Socket.",
    GREEN: "Matches a Yellow or Blue Socket.", META: "Only fits in a meta gem slot.",
}

# (word, color, ((stat, rare, epic), ...)) - the 37 rare/epic gems (R39). Amounts are per quality.
STAT_GEMS = (
    # Red: primary
    ("Bold", RED, ((STRENGTH, 8, 10),)),
    ("Delicate", RED, ((AGILITY, 8, 10),)),
    ("Brilliant", RED, ((INTELLECT, 8, 10),)),
    ("Sparkling", RED, ((SPIRIT, 8, 10),)),
    # Yellow: throughput
    ("Smooth", YELLOW, ((CRIT, 8, 10),)),
    ("Quick", YELLOW, ((HASTE, 8, 10),)),
    ("Fractured", YELLOW, ((MASTERY, 8, 10),)),
    ("Mystic", YELLOW, ((VERSATILITY, 8, 10),)),
    # Blue: utility and defense
    ("Fortunate", BLUE, ((PROC_CHANCE, 8, 10),)),
    ("Tireless", BLUE, ((COOLDOWN_HASTE, 8, 10),)),
    ("Lustrous", BLUE, ((MP5, 2, 2),)),
    ("Shielded", BLUE, ((BLOCK, 8, 10),)),
    ("Subtle", BLUE, ((DODGE, 8, 10),)),
    ("Flashing", BLUE, ((PARRY, 8, 10),)),
    # Orange: primary + throughput (no Versatility, no Spirit)
    ("Inscribed", ORANGE, ((STRENGTH, 4, 5), (CRIT, 4, 5))),
    ("Fierce", ORANGE, ((STRENGTH, 4, 5), (HASTE, 4, 5))),
    ("Etched", ORANGE, ((STRENGTH, 4, 5), (MASTERY, 4, 5))),
    ("Deadly", ORANGE, ((AGILITY, 4, 5), (CRIT, 4, 5))),
    ("Deft", ORANGE, ((AGILITY, 4, 5), (HASTE, 4, 5))),
    ("Glinting", ORANGE, ((AGILITY, 4, 5), (MASTERY, 4, 5))),
    ("Potent", ORANGE, ((INTELLECT, 4, 5), (CRIT, 4, 5))),
    ("Reckless", ORANGE, ((INTELLECT, 4, 5), (HASTE, 4, 5))),
    ("Luminous", ORANGE, ((INTELLECT, 4, 5), (MASTERY, 4, 5))),
    # Purple: role gems
    ("Stalwart", PURPLE, ((STRENGTH, 4, 5), (BLOCK, 4, 5))),
    ("Defender's", PURPLE, ((STRENGTH, 4, 5), (PARRY, 4, 5))),
    ("Nimble", PURPLE, ((AGILITY, 4, 5), (DODGE, 4, 5))),
    ("Regal", PURPLE, ((AGILITY, 4, 5), (PARRY, 4, 5))),
    ("Royal", PURPLE, ((INTELLECT, 4, 5), (MP5, 1, 1))),
    ("Purified", PURPLE, ((SPIRIT, 4, 5), (MP5, 1, 1))),
    # Green: utility throughput
    ("Jagged", GREEN, ((PROC_CHANCE, 4, 5), (CRIT, 4, 5))),
    ("Forceful", GREEN, ((PROC_CHANCE, 4, 5), (HASTE, 4, 5))),
    ("Radiant", GREEN, ((PROC_CHANCE, 4, 5), (MASTERY, 4, 5))),
    ("Vivid", GREEN, ((PROC_CHANCE, 4, 5), (VERSATILITY, 4, 5))),
    ("Misty", GREEN, ((COOLDOWN_HASTE, 4, 5), (CRIT, 4, 5))),
    ("Energized", GREEN, ((COOLDOWN_HASTE, 4, 5), (HASTE, 4, 5))),
    ("Intricate", GREEN, ((COOLDOWN_HASTE, 4, 5), (MASTERY, 4, 5))),
    ("Steady", GREEN, ((COOLDOWN_HASTE, 4, 5), (VERSATILITY, 4, 5))),
)

# (word, color, stat) - the 10 leveling gems (user 2026-11-11), +4 each.
LEVELING_GEMS = (
    ("Bold", RED, STRENGTH), ("Delicate", RED, AGILITY), ("Brilliant", RED, INTELLECT), ("Sparkling", RED, SPIRIT),
    ("Smooth", YELLOW, CRIT), ("Quick", YELLOW, HASTE), ("Fractured", YELLOW, MASTERY),
    ("Shielded", BLUE, BLOCK), ("Subtle", BLUE, DODGE), ("Flashing", BLUE, PARRY),
)
LEVELING_AMOUNT = 4

# Raw gems (stock vanilla, Thorium vein reference 12900) and the cut gem's base name per color and quality.
STAR_RUBY, AZEROTHIAN_DIAMOND, BLUE_SAPPHIRE, LARGE_OPAL, HUGE_EMERALD, ARCANE_CRYSTAL = (
    7910, 12800, 12361, 12799, 12364, 12363)
CITRINE, AQUAMARINE = 3864, 7909

RARE_BASE = {  # color -> (raw gem entry, base name, cut display)
    RED: (STAR_RUBY, "Star Ruby", 39926), YELLOW: (AZEROTHIAN_DIAMOND, "Azerothian Diamond", 39925),
    BLUE: (BLUE_SAPPHIRE, "Blue Sapphire", 39927), ORANGE: (LARGE_OPAL, "Large Opal", 39931),
    PURPLE: (ARCANE_CRYSTAL, "Arcane Crystal", 39929), GREEN: (HUGE_EMERALD, "Huge Emerald", 39930),
}
LEVELING_BASE = {  # Star Ruby is the only red raw gem in the leveling range (research section 6)
    RED: (STAR_RUBY, "Ruby Shard", 35930), YELLOW: (CITRINE, "Citrine", 35848), BLUE: (AQUAMARINE, "Aquamarine", 35852),
}

# The six epic raw gems (new items, raid drops later; user 2026-11-11): color -> (entry, name, raw display, cut display)
EPIC_RAW = {
    RED: (70820, "Bloodfire Ruby", 44919, 44920), YELLOW: (70821, "Sunfire Citrine", 44925, 44926),
    BLUE: (70822, "Tidal Sapphire", 44929, 44930), ORANGE: (70823, "Dawnfire Opal", 44928, 44927),
    PURPLE: (70824, "Twilight Amethyst", 44923, 44924), GREEN: (70825, "Wildheart Emerald", 44922, 44921),
}

# Meta gems: (key, name, display, enchant text). The effects are spells in crafting_gems.py, scripted in
# src/server/scripts/Custom/custom_crafting_gems.cpp.
METAS = (
    ("kaleidoscope", "Kaleidoscopic Azerothian Diamond", 54469,
     "Chance on damage or healing to gain 6 rating per socketed gem for 15 sec",
     "Red Haste, yellow Crit, blue Mastery, orange Versatility, green Proc Chance, purple Cooldown Haste."),
    ("purist", "Purist's Azerothian Diamond", 39205,
     "+1% Strength, Agility, Intellect and Spirit per 2 pure red gems", ""),
    ("relentless", "Relentless Azerothian Diamond", 39203,
     "+1% critical strike damage per yellow gem", ""),
    ("bulwark", "Bulwark Azerothian Diamond", 54467,
     "Chance when hit to absorb 1% of your maximum health per blue gem", ""),
    ("wellspring", "Wellspring Azerothian Diamond", 54468,
     "Critical heals restore 0.1% of your maximum mana per blue gem", ""),
)
# Meta tuple: (key, item name, display, enchant text (<= 100 chars, the tooltip line), item description replacing
# the stock "Only fits in a meta gem slot." when set; it must fit one 120-column SQL line).
# Proc details (chance, internal cooldown, duration) live in the spells; see source/world/crafting_gems.py.

# --- IDs (source/ids.yaml blocks; crafting reservation) ---------------------------------------------------------------
RARE_ITEM, EPIC_ITEM, LEVELING_ITEM, META_ITEM = 70720, 70760, 70800, 70810
RARE_ENCHANT, EPIC_ENCHANT, LEVELING_ENCHANT, META_ENCHANT = 5100, 5140, 5180, 5190
RARE_GEMPROP, EPIC_GEMPROP, LEVELING_GEMPROP, META_GEMPROP = 2000, 2040, 2080, 2090
RARE_CUT, EPIC_CUT, LEVELING_CUT, META_CUT = 207050, 207090, 207130, 207140
RARE_SLA, EPIC_SLA, LEVELING_SLA, META_SLA = 30920, 30960, 31000, 31010
SOCKET_BONUS_ENCHANT = 5600

GEM_LEVEL_GATE = 60  # rare, epic and meta enchants (SpellItemEnchantment.MinLevel)

# Socket bonuses for the stats stock has no +4 bonus for (decision 2 A: flat +4, unpriced).
SOCKET_BONUS_STATS = (STRENGTH, AGILITY, INTELLECT, SPIRIT, MASTERY, VERSATILITY, COOLDOWN_HASTE, PROC_CHANCE)
SOCKET_BONUS_AMOUNT = 4

# item_template values per kind: (Quality, ItemLevel, BuyPrice, SellPrice)
QUALITY_UNCOMMON, QUALITY_RARE, QUALITY_EPIC = 2, 3, 4
ITEM_VALUES = {
    "leveling": (QUALITY_UNCOMMON, 50, 10000, 2500),
    "rare": (QUALITY_RARE, 60, 60000, 15000),
    "epic": (QUALITY_EPIC, 66, 0, 40000),
    "meta": (QUALITY_RARE, 60, 80000, 20000),
    "epic_raw": (QUALITY_EPIC, 66, 0, 30000),
}


def enchant_text(stats) -> str:
    """The gem enchant's tooltip line: "+8 Strength", "+4 Agility and +4 Critical Strike Rating", "+1 mana every 5
    sec." (stock wording for MP5)."""
    parts = [f"+{amount} {STAT_TEXT[stat]}" for stat, amount in stats]
    return " and ".join(parts)


def gems():
    """Every gem as a dict: kind, index, item entry, name, color, stats ((stat, amount), ...), display, raw gem entry,
    enchant id, GemProperties id, cut spell id, SkillLineAbility id, quality/level/prices."""
    out = []
    for index, (word, color, stats) in enumerate(STAT_GEMS):
        raw, base, display = RARE_BASE[color]
        out.append(_gem("rare", index, f"{word} {base}", color, tuple((s, r) for s, r, _e in stats), display, raw,
                        RARE_ITEM, RARE_ENCHANT, RARE_GEMPROP, RARE_CUT, RARE_SLA))
        epic_raw, epic_base, _raw_display, epic_display = EPIC_RAW[color]
        out.append(_gem("epic", index, f"{word} {epic_base}", color, tuple((s, e) for s, _r, e in stats),
                        epic_display, epic_raw, EPIC_ITEM, EPIC_ENCHANT, EPIC_GEMPROP, EPIC_CUT, EPIC_SLA))
    for index, (word, color, stat) in enumerate(LEVELING_GEMS):
        raw, base, display = LEVELING_BASE[color]
        out.append(_gem("leveling", index, f"{word} {base}", color, ((stat, LEVELING_AMOUNT),), display, raw,
                        LEVELING_ITEM, LEVELING_ENCHANT, LEVELING_GEMPROP, LEVELING_CUT, LEVELING_SLA))
    for index, (key, name, display, _text, _extra) in enumerate(METAS):
        gem = _gem("meta", index, name, META, (), display, AZEROTHIAN_DIAMOND,
                   META_ITEM, META_ENCHANT, META_GEMPROP, META_CUT, META_SLA)
        gem["meta_key"] = key
        out.append(gem)
    return sorted(out, key=lambda g: g["item"])


def _gem(kind, index, name, color, stats, display, raw, item, enchant, gemprop, cut, sla):
    quality, item_level, buy, sell = ITEM_VALUES[kind]
    return {
        "kind": kind, "index": index, "item": item + index, "name": name, "color": color, "stats": stats,
        "display": display, "raw": raw, "enchant": enchant + index, "gemprop": gemprop + index, "cut": cut + index,
        "sla": sla + index, "quality": quality, "item_level": item_level, "buy": buy, "sell": sell,
        "level_gate": 0 if kind == "leveling" else GEM_LEVEL_GATE,
    }


def epic_raws():
    """The six epic raw gems as dicts (entry, name, color, display, quality/level/prices)."""
    quality, item_level, buy, sell = ITEM_VALUES["epic_raw"]
    return [{"item": entry, "name": name, "color": color, "display": display, "quality": quality,
             "item_level": item_level, "buy": buy, "sell": sell}
            for color, (entry, name, display, _cut) in sorted(EPIC_RAW.items(), key=lambda kv: kv[1][0])]
