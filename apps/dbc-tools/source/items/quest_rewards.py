"""
Quest rewards on the item stat system (docs/plans/quest-reward-itemization/, stage QR1): one `item(base=<entry>)` per
line of `quest_rewards.lock` (lib/quest_rewards.py has the rules that seeded it and the line format), on the one-tier
`quest_reward` ladder (ladders.py; no tooltip line, ruling 20).

Each stock reward keeps its id, name, look, slot, set and resistances; the declaration sets its item level and
quality (the lock's), required level 0 (ruling 10: the quests already gate by level) and its shapes and primary share
(by shape id). Stock spells: `-` absorbs every stock spell slot (the item() default: plain stat Equip spells fold
into the budget), `all` keeps them (`keep_spells=True`), a slot list keeps those slots and drops the others (`spells=`
re-declares the kept ones from the live row). A kept effect gives the item the DSL's `budget_mult` 0.7 default.

`unique_equip=False`: one tier means no two tiers of the same effect to wear together, and a limit category would
need a client ItemLimitCategory.dbc row (quest rewards ship as server data only). Bows, guns and crossbows state
`ammo_type` 0 themselves: source/world/ranged_weapons.py skips every entry source/items owns (this lock included).

Keys are `qr_<entry>`. One owner per entry: to move a reward into a dungeon's item list, delete its lock line first.

Green weapons (and the white ones that become green) resolve their DPS against the Quality 2 rows of
`item_weapon_dps_curve` (ruling 21, stage QR1b's pending SQL).
"""

from lib.dsl.items import ItemSpell, item
from lib.dsl.registry import live_item_templates
from lib.quest_rewards import LOCK_PATH, parse_lock

from .ladders import QUEST_REWARD

REQUIRED_LEVEL = 0  # ruling 10
NO_AMMO = 0
ITEM_CLASS_WEAPON = 2
AMMO_WEAPON_SUBCLASSES = (2, 3, 18)  # bow, gun, crossbow (source/world/ranged_weapons.py)


def _int(value) -> int:
    return int(float(value or 0))


def _stock_spell(row: dict, slot: int) -> ItemSpell:
    """The live row's spell in `slot`, every column as it is."""
    return ItemSpell(
        spell_id=_int(row[f"spellid_{slot}"]), trigger=_int(row[f"spelltrigger_{slot}"]),
        charges=_int(row[f"spellcharges_{slot}"]), ppm=float(row[f"spellppmRate_{slot}"] or 0),
        cooldown=_int(row[f"spellcooldown_{slot}"]), category=_int(row[f"spellcategory_{slot}"]),
        category_cooldown=_int(row[f"spellcategorycooldown_{slot}"]),
    )


try:
    _ROWS = live_item_templates()
except RuntimeError:
    # Loaded without the live rows (a unit test loading source/items for another file's items): the declarations
    # need each item's live row (its class and subclass, its spell columns), so this file declares nothing.
    # generate.py always passes them.
    _ROWS = None

for _line in parse_lock(LOCK_PATH.read_text(encoding="utf-8")).values() if _ROWS is not None else ():
    _row = _ROWS.get(_line.entry, {})
    _ranged = _int(_row.get("class")) == ITEM_CLASS_WEAPON and _int(_row.get("subclass")) in AMMO_WEAPON_SUBCLASSES
    _extra: dict = {}
    _kept = _line.kept_slots
    if _kept is None:
        _extra["keep_spells"] = True
    elif _kept:
        _extra["spells"] = tuple(_stock_spell(_row, slot) for slot in _kept)
    if _ranged:
        _extra["ammo_type"] = NO_AMMO
    item(_line.key, base=_line.entry, ladder=QUEST_REWARD, ilvl=_line.ilvl, quality=_line.quality,
         required_level=REQUIRED_LEVEL, primary=_line.primary or None, secondary=_line.secondary,
         primary_share=_line.share, unique_equip=False, **_extra)
