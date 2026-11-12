"""
Crafting rework C6 material squish (`.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md` decision 13b): the
`disenchant_loot_template` entry and `RequiredDisenchantSkill` a vanilla item gets from its quality, item level and
class, so a minted item disenchants by its own level instead of the `like=` item's.

The entries are the stock bands (what stock vanilla items carry), and
`data/sql/updates/pending_db_world/rev_crafting_c6_squish_loot.sql` gives them their squished loot:

- Uncommon: armor 1-11, weapons 21-31, one entry per five item levels (<= 15 is 1, 16-20 2, ... 61+ 11);
- Rare: 41 (<= 25), 42-46 (26-50 in steps of five), 47 (51-55), 48 (56-65), 49 (66+);
- Epic: 61 (<= 45), 62 (46-50), 63 (51-55), 64 (56-60), 65 (61-80), 70 (81+, 1-2 Nexus Crystals; a new entry).

Only vanilla items (RequiredLevel <= 60) are mapped; Outland and Northrend items keep what they have until their own
squish (decision 13f). The skill is the stock value of the band; professions sit at the cap (300), so it only matters
that it's within reach.
"""

from __future__ import annotations

QUALITY_UNCOMMON, QUALITY_RARE, QUALITY_EPIC = 2, 3, 4
ITEM_CLASS_WEAPON, ITEM_CLASS_ARMOR = 2, 4
VANILLA_MAX_REQUIRED_LEVEL = 60
EPIC_HIGH_ENTRY = 70  # 1-2 Nexus Crystals, item level 81+

# (highest item level of the band, entry, RequiredDisenchantSkill), first match wins; the last band is open-ended.
_UNCOMMON = ((15, 1, 1), (20, 2, 1), (25, 3, 25), (30, 4, 50), (35, 5, 75), (40, 6, 100), (45, 7, 125), (50, 8, 150),
             (55, 9, 175), (60, 10, 200), (None, 11, 225))
_RARE = ((25, 41, 25), (30, 42, 50), (35, 43, 75), (40, 44, 100), (45, 45, 125), (50, 46, 150), (55, 47, 175),
         (65, 48, 200), (None, 49, 225))
_EPIC = ((45, 61, 125), (50, 62, 150), (55, 63, 175), (60, 64, 200), (80, 65, 225), (None, EPIC_HIGH_ENTRY, 300))
WEAPON_OFFSET = 20  # uncommon weapons use 21-31


def disenchant_columns(item_class: int, quality: int, item_level: int, required_level: int) -> dict | None:
    """`{"DisenchantID": ..., "RequiredDisenchantSkill": ...}` for a vanilla weapon or armor piece of Uncommon, Rare
    or Epic quality, else None (the row keeps its columns)."""
    if item_class not in (ITEM_CLASS_WEAPON, ITEM_CLASS_ARMOR) or required_level > VANILLA_MAX_REQUIRED_LEVEL:
        return None
    bands = {QUALITY_UNCOMMON: _UNCOMMON, QUALITY_RARE: _RARE, QUALITY_EPIC: _EPIC}.get(quality)
    if bands is None:
        return None
    for highest, entry, skill in bands:
        if highest is None or item_level <= highest:
            if quality == QUALITY_UNCOMMON and item_class == ITEM_CLASS_WEAPON:
                entry += WEAPON_OFFSET
            return {"DisenchantID": entry, "RequiredDisenchantSkill": skill}
    raise AssertionError("the last band is open-ended")
