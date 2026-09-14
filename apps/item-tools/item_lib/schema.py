"""
Groups `item_template`'s ~140 columns into form sections. The grouping is
static (hand-written below) but checked at import time against the live
column list from `lib.overlay.item_columns()` - see `_SECTIONS` and the
`assert` at the bottom - so a schema change (a column added/removed/renamed
in a future migration) fails loudly here instead of that column silently
falling out of every form.
"""

from __future__ import annotations

from .overlay import item_columns

# (section title, [column names in display order])
_SECTIONS: list[tuple[str, list[str]]] = [
    ("Identity", [
        "entry", "name", "class", "subclass", "SoundOverrideSubclass", "displayid",
        "Quality", "Flags", "FlagsExtra",
    ]),
    ("Economy", ["BuyCount", "BuyPrice", "SellPrice", "InventoryType"]),
    ("Requirements", [
        "AllowableClass", "AllowableRace", "ItemLevel", "RequiredLevel",
        "RequiredSkill", "RequiredSkillRank", "requiredspell", "requiredhonorrank",
        "RequiredCityRank", "RequiredReputationFaction", "RequiredReputationRank",
    ]),
    ("Stacking", ["maxcount", "stackable", "ContainerSlots"]),
    ("Stats", [
        f"stat_{part}{n}" for n in range(1, 11) for part in ("type", "value")
    ] + ["ScalingStatDistribution", "ScalingStatValue"]),
    ("Damage", [
        "dmg_min1", "dmg_max1", "dmg_type1", "dmg_min2", "dmg_max2", "dmg_type2",
    ]),
    ("Resistances", [
        "armor", "holy_res", "fire_res", "nature_res", "frost_res", "shadow_res", "arcane_res",
    ]),
    ("Ranged", ["delay", "ammo_type", "RangedModRange"]),
    ("Spell triggers", [
        col
        for n in range(1, 6)
        for col in (
            f"spellid_{n}", f"spelltrigger_{n}", f"spellcharges_{n}", f"spellppmRate_{n}",
            f"spellcooldown_{n}", f"spellcategory_{n}", f"spellcategorycooldown_{n}",
        )
    ]),
    ("Sockets", [
        "socketColor_1", "socketContent_1", "socketColor_2", "socketContent_2",
        "socketColor_3", "socketContent_3", "socketBonus", "GemProperties",
        "RequiredDisenchantSkill", "ArmorDamageModifier",
    ]),
    ("Misc", [
        "bonding", "description", "PageText", "LanguageID", "PageMaterial", "startquest",
        "lockid", "Material", "sheath", "RandomProperty", "RandomSuffix", "block", "itemset",
        "MaxDurability", "area", "Map", "BagFamily", "TotemCategory",
    ]),
    ("Other", [
        "duration", "ItemLimitCategory", "HolidayId", "ScriptName", "DisenchantID",
        "FoodType", "minMoneyLoot", "maxMoneyLoot", "flagsCustom", "VerifiedBuild",
    ]),
]

# Columns shown on the search/list page.
LIST_COLUMNS = ["entry", "name", "class", "subclass", "Quality", "ItemLevel", "RequiredLevel"]


def sections() -> list[tuple[str, list[str]]]:
    return _SECTIONS


def _check_schema_coverage() -> None:
    grouped = [col for _, cols in _SECTIONS for col in cols]
    grouped_set = set(grouped)
    if len(grouped) != len(grouped_set):
        seen = set()
        dupes = {c for c in grouped if c in seen or seen.add(c)}
        raise AssertionError(f"lib/schema.py: column(s) listed in more than one section: {dupes}")
    actual = set(item_columns())
    missing = actual - grouped_set
    extra = grouped_set - actual
    if missing or extra:
        raise AssertionError(
            "lib/schema.py's section groupings are out of sync with item_template's real columns "
            f"(from data/sql/base/db_world/item_template.sql) - missing from a section: {sorted(missing)}; "
            f"listed but not a real column: {sorted(extra)}. Update _SECTIONS to match."
        )


_check_schema_coverage()
