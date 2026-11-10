"""
Item declarations with item-level variants (item-variants plan v2, .agents/plans/item-variants/, stage IV1): one
`item(...)` per item in `source/items/*.py`, naming the loot `ladder` it climbs. `generate.py` resolves every
non-deferred tier of the ladder to an `item_template` entry (`lib/item_ids.py`, the lock file
`source/items/item_ids.lock`) and checks the declaration against the itemization catalog (`lib/item_variants.py`).
`lib/item_emit.py` (IV2) emits the rows.

    from lib.dsl.items import Quality, item, ladder, tier

    VANILLA_DUNGEON = ladder("vanilla_dungeon",
        normal=tier(step=0, label="Normal"),  # the stock row's level, quality, required level, or the item's own
        heroic=tier(step=1, ilvl=66, quality=Quality.EPIC, required_level=60, heroic_flag=True, label="Heroic"),
        empowered_1=tier(step=2, ilvl=76, quality=Quality.EPIC, required_level=60, label="Molten Empowered"),
    )

    item("dm_rhahkzors_hammer", base=5187, primary="Strength (Solo)", secondary="Crit (Solo)",
         ladder=VANILLA_DUNGEON)
    item("dm_doormans_girdle", name="Doorman's Girdle", like=6087, ilvl=20, primary="Strength (Solo)",
         secondary="Parry (Solo)", ladder=VANILLA_DUNGEON)
    item("dm_thiefs_blade", base=5192, itemization="live", ladder=VANILLA_DUNGEON)

**Ladders and tiers.** A ladder is an ordered list of named tiers. Its first tier may leave `ilvl` / `quality` /
`required_level` out: they then come from the item (the stock row of a `base=` item, or the item's own `ilvl=` /
`quality=` / `required_level=`). Every later tier gives all three, and the explicit levels strictly increase. The
label belongs to the tier, so each ladder (each expansion) names its own; `heroic_flag=True` sets the stock
`ITEM_FLAG_HEROIC_TOOLTIP` (0x8), which the client prints as "Heroic" itself, so that tier gets no label table entry
(IV4). `deferred=True` declares a tier without minting it (no id, no rows, no label); flipping it later mints it.
The first non-deferred tier is the variant base; every other tier is a variant of it (`item_budget_variant`).
`sockets=False` makes a tier drop the item's sockets and socket bonus (sockets start at Heroic, user 2026-11-06).
`step=` is the tier's `item_budget_variant.tier` number, given explicitly on every tier: the same number means the same
step on every ladder (0 Normal, 1 Heroic, 2.. the empowered tiers), so a hard mode ladder that starts at Heroic starts
at step 1, and the empowered module looks every ladder up as (base entry, step). Steps strictly increase along a
ladder; a deferred tier keeps its step, so flipping it never renumbers the others.

**Items.** `base=<entry>` takes over a stock item as the ladder's first tier (its own id, name, icon, display, slot,
set); only the higher tiers are minted. Without `base=` every tier is minted: `name=` is required, and `like=<entry>`
copies `LIKE_COLUMNS` from a stock item (or they are passed as columns). Stats are never passed (`stat_type*`,
`stat_value*`, `dmg_*`, `block`; `armor` on a slot with an armor curve): they come from the budget. Shapes are
`item_shape.name` strings, or `item_shape.shape_id` ints for a declaration read from a lock file
(source/items/quest_rewards.py); `primary=None` is the Null shape, 100% secondary; `secondary=None` gives the primary
the whole budget; checked at resolve time. `itemization="live"` adopts a stock item's live `item_itemization` row on
its first tier. Deltas are fractions of the tier's own baseline (`extra_stamina=0.25` is +25% of the tier's Stamina),
so they scale with the item level.

**Effects.** `spells=(use_spell(...), equip_spell(...), hit_spell(...))` puts the same effect on every tier, unless it
is declared with `scale="budget"` (IV10): then every tier but the ladder's effect reference tier (`ladder(...,
effect_reference=)`, else its first) carries its own copy of the spell and of every spell it reaches, damage and
healing potency and stat-like aura amounts times the tier's stat budget over the reference tier's
(`lib/item_spell_copies.py`; durations, cooldowns, chances, radii and percentages stay as declared).

**Unique-equipped across tiers** (IV10 follow-up 1, user 2026-11-06). Every tier of an item with an effect (`spells=`
with at least one spell, or a `keep_spells=True` stock item whose row has one) shares one `ItemLimitCategory`, equip
limit 1, so a player cannot wear two tiers of the same effect at once (`lib/item_limits.py`). `unique_equip=False`
turns it off, `unique_equip=True` puts it on an item without an effect; plain stat items stay unrestricted.

Registered into `Registry.item_declarations` (`id` = the key), so two `item()` calls with one key are a
`DuplicateIdError` like any other declared table.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from enum import IntEnum
from pathlib import Path

from . import registry as _registry

HEROIC_TOOLTIP_FLAG = 0x8  # ITEM_FLAG_HEROIC_TOOLTIP, ItemTemplate.h: "Makes green Heroic text appear on item"
NULL_PRIMARY_SHAPE = "Null (jewelry, 100% secondary)"  # item_shape 0, the primary of a primary-less item
PRIMARY_SHARES = (0, 4000, 6000, 8000, 10000)
DEFAULT_SHARE_BOTH = 6000
EFFECT_BUDGET_MULT = 0.7  # itemization-changes.md s3: an item with a Use or Equip effect pays for it
# Weapon roles for the weapon-tier budget defaults (lib/item_variants.py, RoleCells): the stock itemization's
# per-(role, slot) correction (itemization-changes.md, Bucket 1 "Weapon role correction").
WEAPON_ROLES = ("physical", "caster", "tank")
MAX_SPELLS = 5
MAX_SOCKETS = 3
MAX_ITEM_LEVEL = 300  # every reference curve covers 1-300
MAX_REQUIRED_LEVEL = 80
MAX_TIER_STEP = 255  # item_budget_variant.tier is a tinyint unsigned
# `use_spell(..., scale=...)` values (item variants IV10, lib/item_spell_copies.py). "budget": every tier but the
# ladder's effect reference tier gets its own copy of the effect spell and every spell it reaches, with the damage and
# healing potency and stat-like aura amounts scaled by the tier's stat budget over the reference tier's.
SPELL_SCALES = ("budget",)
NEW_ITEM_LEVEL_GAP = 5  # a new item's default required level: its item level minus this (the stock pattern)

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
LABEL_FORBIDDEN = ('"', "\\", "\n", "\r", "|")  # the label goes into a Lua string (IV4) and a tooltip line

# Columns `like=` copies from the stock item a new item looks like: what it is and how it looks and sounds. The rest
# of a new row is the schema default, the DSL's own columns and the item's explicit columns.
LIKE_COLUMNS = (
    "class", "subclass", "SoundOverrideSubclass", "displayid", "Material", "sheath", "InventoryType", "delay",
    "dmg_type1", "RangedModRange", "ammo_type", "bonding",
)

# Columns the budget writes (ItemBudget::ApplyItemizationAllocation): never passed. `armor` is checked at resolve
# time (passing it is an error only on a slot with an armor curve).
STAT_COLUMNS = frozenset(
    [f"stat_type{n}" for n in range(1, 11)] + [f"stat_value{n}" for n in range(1, 11)]
    + ["dmg_min1", "dmg_max1", "dmg_min2", "dmg_max2", "block"]
)
# Columns the DSL sets through its own keywords: pass the keyword instead.
KEYWORD_COLUMNS = {
    "entry": "the key / base=", "name": "name=", "ItemLevel": "ilvl=", "Quality": "quality=",
    "RequiredLevel": "required_level=", "socketBonus": "socket_bonus=", "ItemLimitCategory": "unique_equip=",
    **{f"socketColor_{n}": "sockets=" for n in range(1, 4)},
    **{f"socketContent_{n}": "sockets=" for n in range(1, 4)},
    **{f"spell{part}_{n}": "spells=" for n in range(1, 6) for part in (
        "id", "trigger", "charges", "ppmRate", "cooldown", "category", "categorycooldown")},
}


class Quality(IntEnum):
    POOR = 0
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    EPIC = 4
    LEGENDARY = 5
    ARTIFACT = 6
    HEIRLOOM = 7


class Socket(IntEnum):
    """`socketColor_N` values (ItemTemplate.h SocketColor)."""

    META = 1
    RED = 2
    YELLOW = 4
    BLUE = 8


class SpellTrigger(IntEnum):
    """`spelltrigger_N` values (ItemTemplate.h ItemSpelltriggerType)."""

    USE = 0
    ON_EQUIP = 1
    CHANCE_ON_HIT = 2


class ItemDeclarationError(ValueError):
    pass


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---------------------------------------------------------------------------------------------------------------------
# Tiers and ladders


@dataclass(frozen=True)
class Tier:
    """One tier of a ladder. `name` is set by `ladder()` (the keyword it was passed under)."""

    label: str | None  # None: no tooltip line (no label table row)
    ilvl: int | None = None
    quality: int | None = None
    required_level: int | None = None
    heroic_flag: bool = False
    deferred: bool = False
    sockets: bool = True
    step: int = 0  # item_budget_variant.tier: 0 Normal, 1 Heroic, 2.. empowered (explicit, see tier())
    name: str = ""

    @property
    def explicit(self) -> bool:
        return self.ilvl is not None


def tier(
    *, step: int, label: str | None, ilvl: int | None = None, quality: int | None = None,
    required_level: int | None = None, heroic_flag: bool = False, deferred: bool = False, sockets: bool = True,
) -> Tier:
    """A ladder tier. `label` is the green tooltip line under the item name ("Normal", "Molten Empowered", ...); on a
    `heroic_flag=True` tier the client prints its own "Heroic" line from flag 0x8 and the label is not written to the
    label table (IV4). `ilvl` / `quality` / `required_level` go together: all three, or (first tier only) none.
    `sockets=False` drops the item's sockets and socket bonus on this tier (and with them the budget's socket
    discount): user ruling 2026-11-06, sockets start at Heroic, a leveling Normal tier has none. `step` is the
    `item_budget_variant.tier` number (required): 0 Normal, 1 Heroic, 2.. the empowered tiers, the same number for the
    same step on every ladder (R1 N1: explicit, never derived from the tier's position). `label=None` writes no
    tooltip line at all (no label table row): a tier that needs no name, e.g. the single `quest_reward` tier (quest
    reward itemization ruling 20)."""
    if not _plain_int(step) or not 0 <= step <= MAX_TIER_STEP:
        raise ItemDeclarationError(
            f"tier(label={label!r}): step={step!r} must be an int in 0-{MAX_TIER_STEP} (item_budget_variant.tier: "
            f"0 Normal, 1 Heroic, 2.. the empowered tiers)"
        )
    if label is not None and (not isinstance(label, str) or not label.strip()):
        raise ItemDeclarationError(f"tier(label={label!r}): the label must be a non-empty string, or None for none")
    if label is not None and (label != label.strip() or any(ch in label for ch in LABEL_FORBIDDEN)):
        raise ItemDeclarationError(
            f"tier(label={label!r}): no leading or trailing space and none of {' '.join(map(repr, LABEL_FORBIDDEN))} "
            f"(it is written into a Lua string and a tooltip line)"
        )
    given = [v is not None for v in (ilvl, quality, required_level)]
    if any(given) and not all(given):
        raise ItemDeclarationError(
            f"tier(label={label!r}): give ilvl=, quality= and required_level= together (all three), or none of them "
            f"on a ladder's first tier to take the item's own"
        )
    if ilvl is not None:
        if not _plain_int(ilvl) or not 1 <= ilvl <= MAX_ITEM_LEVEL:
            raise ItemDeclarationError(f"tier(label={label!r}): ilvl={ilvl!r} must be an int in 1-{MAX_ITEM_LEVEL}")
        _check_quality(f"tier(label={label!r})", quality)
        _check_required_level(f"tier(label={label!r})", required_level)
    if not all(isinstance(v, bool) for v in (heroic_flag, deferred, sockets)):
        raise ItemDeclarationError(f"tier(label={label!r}): heroic_flag=, deferred= and sockets= are True or False")
    return Tier(label=label, ilvl=ilvl, quality=None if quality is None else int(quality),
                required_level=required_level, heroic_flag=heroic_flag, deferred=deferred, sockets=sockets, step=step)


def _check_quality(where: str, quality) -> None:
    if not _plain_int(quality) or quality not in tuple(Quality):
        raise ItemDeclarationError(f"{where}: quality={quality!r} must be a Quality (0-7)")


def _check_required_level(where: str, level) -> None:
    if not _plain_int(level) or not 0 <= level <= MAX_REQUIRED_LEVEL:
        raise ItemDeclarationError(f"{where}: required_level={level!r} must be an int in 0-{MAX_REQUIRED_LEVEL}")


@dataclass(frozen=True)
class Ladder:
    name: str
    tiers: tuple[Tier, ...]
    # The tier whose item level the per-tier effect copies are measured against (IV10, lib/item_spell_copies.py): it
    # keeps the declared spells, every other tier gets a copy scaled by budget(tier) / budget(reference). None: the
    # first tier.
    effect_reference: str | None = None

    def tier(self, name: str) -> Tier | None:
        return next((t for t in self.tiers if t.name == name), None)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(t.name for t in self.tiers)


def ladder(name: str, *, effect_reference: str | None = None, **tiers: Tier) -> Ladder:
    """An ordered loot ladder: `ladder("vanilla_dungeon", normal=tier(...), heroic=tier(...), ...)`. Tier names are
    the lock file's tier column, so a shipped tier keeps its name forever (renaming one retires its ids). Only the
    first tier may take the item's own level; the explicit item levels and the steps strictly increase.

    `effect_reference="<tier>"` names the tier a `scale="budget"` effect's declared numbers belong to (IV10; wave 1
    integration): every other tier's copy is scaled by its stat budget over that tier's, so a ladder whose first tier
    takes each item's own (stock) level still scales effects from one fixed level. It must be a tier with an explicit
    item level (or the first tier); left out, the first tier is the reference."""
    if not isinstance(name, str) or not _KEY_RE.match(name):
        raise ItemDeclarationError(f"ladder({name!r}): the name must match {_KEY_RE.pattern}")
    if not tiers:
        raise ItemDeclarationError(f"ladder({name!r}): needs at least one tier")
    named = []
    for index, (tier_name, spec) in enumerate(tiers.items()):
        if not isinstance(spec, Tier):
            raise ItemDeclarationError(f"ladder({name!r}): {tier_name}= must be a tier(...), got {spec!r}")
        if not _KEY_RE.match(tier_name):
            raise ItemDeclarationError(f"ladder({name!r}): tier name {tier_name!r} must match {_KEY_RE.pattern}")
        if index and not spec.explicit:
            raise ItemDeclarationError(
                f"ladder({name!r}): tier {tier_name!r} has no ilvl=/quality=/required_level=; only the first tier "
                f"may take the item's own"
            )
        named.append(replace(spec, name=tier_name))
    explicit = [t for t in named if t.explicit]
    for low, high in zip(explicit, explicit[1:]):
        if high.ilvl <= low.ilvl:
            raise ItemDeclarationError(
                f"ladder({name!r}): item levels must strictly increase, but {high.name!r} ({high.ilvl}) follows "
                f"{low.name!r} ({low.ilvl})"
            )
    for low, high in zip(named, named[1:]):
        if high.step <= low.step:
            raise ItemDeclarationError(
                f"ladder({name!r}): tier steps must strictly increase, but {high.name!r} (step {high.step}) follows "
                f"{low.name!r} (step {low.step})"
            )
    labels = [t.label for t in named if t.label is not None]
    if len(set(labels)) != len(labels):
        raise ItemDeclarationError(f"ladder({name!r}): two tiers share a label ({labels})")
    if effect_reference is not None:
        reference = next((t for t in named if t.name == effect_reference), None)
        if reference is None:
            raise ItemDeclarationError(
                f"ladder({name!r}): effect_reference={effect_reference!r} names no tier ({[t.name for t in named]})"
            )
        if reference.deferred or not (reference.explicit or reference is named[0]):
            raise ItemDeclarationError(
                f"ladder({name!r}): effect_reference={effect_reference!r} must be a minted tier with its own ilvl= "
                f"(or the first tier)"
            )
    return Ladder(name=name, tiers=tuple(named), effect_reference=effect_reference)


# ---------------------------------------------------------------------------------------------------------------------
# Item effects


@dataclass(frozen=True)
class ItemSpell:
    spell_id: int
    trigger: int
    charges: int = 0
    ppm: float = 0.0
    cooldown: int = -1
    category: int = 0
    category_cooldown: int = -1
    # IV10: "budget" mints per-tier copies of the spell (lib/item_spell_copies.py); `spell` is the declared Spell
    # the copies are built from (bookkeeping, not part of the row).
    scale: str | None = None
    spell: object | None = field(default=None, compare=False, repr=False)

    def with_spell_id(self, spell_id: int) -> ItemSpell:
        """The same effect on another spell id (a tier's copy)."""
        return replace(self, spell_id=spell_id)

    def columns(self, slot: int) -> dict:
        """The `item_template` spell columns of slot `slot` (1-5)."""
        return {
            f"spellid_{slot}": self.spell_id, f"spelltrigger_{slot}": self.trigger,
            f"spellcharges_{slot}": self.charges, f"spellppmRate_{slot}": self.ppm,
            f"spellcooldown_{slot}": self.cooldown, f"spellcategory_{slot}": self.category,
            f"spellcategorycooldown_{slot}": self.category_cooldown,
        }


def _spell_id(spell) -> int:
    spell_id = getattr(spell, "id", spell)
    if not _plain_int(spell_id) or spell_id <= 0:
        raise ItemDeclarationError(f"item spell {spell!r}: expected a spell id or a declared Spell")
    return spell_id


def _scale(caller: str, spell, scale) -> dict:
    """The `scale=` fields of an ItemSpell. "budget" needs the declared Spell (not a bare id): the copies are built
    from its declaration."""
    if scale is None:
        return {}
    if scale not in SPELL_SCALES:
        raise ItemDeclarationError(f"{caller}({spell!r}): scale={scale!r} must be one of {SPELL_SCALES} or None")
    from .model import Spell  # noqa: PLC0415

    if not isinstance(spell, Spell):
        raise ItemDeclarationError(
            f"{caller}({spell!r}): scale={scale!r} copies the spell's declaration per tier, so pass the declared "
            f"spell(...) object, not a bare id"
        )
    return {"scale": scale, "spell": spell}


def use_spell(spell, cooldown: int = -1, category: int = 0, category_cooldown: int = -1, charges: int = 0,
              scale: str | None = None) -> ItemSpell:
    """A "Use:" effect (`spelltrigger` 0). Cooldowns in milliseconds, -1 = the spell's own. `scale="budget"` gives
    every tier but the ladder's effect reference tier its own copy of the spell, damage, healing and stat auras scaled
    by the tier's stat budget over the reference tier's (IV10, lib/item_spell_copies.py)."""
    return ItemSpell(_spell_id(spell), SpellTrigger.USE, charges=charges, cooldown=cooldown, category=category,
                     category_cooldown=category_cooldown, **_scale("use_spell", spell, scale))


def equip_spell(spell, scale: str | None = None) -> ItemSpell:
    """An "Equip:" effect (`spelltrigger` 1). `scale=` as in `use_spell`."""
    return ItemSpell(_spell_id(spell), SpellTrigger.ON_EQUIP, **_scale("equip_spell", spell, scale))


def hit_spell(spell, ppm: float = 0.0, scale: str | None = None) -> ItemSpell:
    """A "Chance on hit:" effect (`spelltrigger` 2), `ppm` procs per minute (0 = the spell's own proc data).
    `scale=` as in `use_spell`."""
    if not _number(ppm) or ppm < 0:
        raise ItemDeclarationError(f"hit_spell({spell!r}): ppm={ppm!r} must be a number >= 0")
    return ItemSpell(_spell_id(spell), SpellTrigger.CHANCE_ON_HIT, ppm=float(ppm),
                     **_scale("hit_spell", spell, scale))


# ---------------------------------------------------------------------------------------------------------------------
# Items


@dataclass(frozen=True)
class ItemDecl:
    key: str
    ladder: Ladder
    base: int | None = None
    name: str | None = None
    like: int | None = None
    ilvl: int | None = None
    quality: int | None = None
    required_level: int | None = None
    primary: str | int | None = None  # an item_shape name, or its shape_id (a lock-driven declaration)
    secondary: str | int | None = None
    primary_share: int | None = None
    budget_mult: float | None = None
    itemization: str | None = None
    extra_stamina: float = 0.0
    extra_armor: float = 0.0
    extra_dps: float | None = None  # None: a weapon takes its role cell's median DPS adjustment (item_variants)
    extra_block: float = 0.0
    # True: the DPS above the role cell's (extra_dps= minus the cell's fraction) is funded by raising budget_mult, so
    # the stats stay the role-cell version's (lib/item_variants.py `_free_dps_mult`).
    free_dps: bool = False
    weapon_role: str | None = None
    spells: tuple[ItemSpell, ...] | None = None
    keep_spells: bool = False
    sockets: tuple[int, ...] | None = None
    socket_bonus: int | None = None
    overrides: tuple[tuple[str, tuple[tuple[str, object], ...]], ...] = ()
    columns: tuple[tuple[str, object], ...] = ()
    unique_equip: bool | None = None  # None: True when the item has an effect (IV10 follow-up 1, lib/item_limits.py)

    @property
    def where(self) -> str:
        return f"item {self.key!r}"

    def override_columns(self, tier_name: str) -> dict:
        return dict(dict(self.overrides).get(tier_name, ()))


def item(
    key: str, *, ladder: Ladder, base: int | None = None, name: str | None = None, like: int | None = None,
    ilvl: int | None = None, quality: int | None = None, required_level: int | None = None,
    primary: str | int | None = None, secondary: str | int | None = None, primary_share: int | None = None,
    budget_mult: float | None = None, itemization: str | None = None,
    extra_stamina: float = 0.0, extra_armor: float = 0.0, extra_dps: float | None = None, extra_block: float = 0.0,
    free_dps: bool = False, weapon_role: str | None = None, spells=None, keep_spells: bool = False, sockets=None,
    socket_bonus: int | None = None, overrides: dict | None = None, unique_equip: bool | None = None, **columns,
) -> ItemDecl:
    """Declares an item on `ladder` (see the module docstring). `key` names it in the lock file forever: the ids of
    its tiers stay with the key whatever its name, level or shapes later become. `columns` are other `item_template`
    columns for every tier (a new item's look when there is no `like=`, `Flags`, `bonding`, ...); `overrides=
    {"heroic": {...}}` sets columns on one tier (e.g. `itemset` 0 above Normal). On a weapon-tier slot (weapons,
    shields, held in off-hand) `budget_mult` and `extra_dps` default to the median of live items of the same role,
    slot, quality and item level bucket (R1 S1, `lib/item_variants.py` RoleCells); the role comes from the shapes,
    or `weapon_role=` ("physical", "caster", "tank") overrides it. `free_dps=True` (needs `extra_dps=` and a role
    cell) funds the DPS difference between `extra_dps=` and the role cell's DPS fraction by raising `budget_mult`, so
    the item keeps the role-cell version's stats with the declared DPS (quest reward ruling 40: full-strength wands
    at the caster cell's stats). Checks here are the ones that need no live data;
    `lib/item_variants.py` checks the rest when generate.py resolves the item."""
    where = f"item({key!r})"
    if not isinstance(key, str) or not _KEY_RE.match(key):
        raise ItemDeclarationError(f"{where}: the key must match {_KEY_RE.pattern}")
    if not isinstance(ladder, Ladder):
        raise ItemDeclarationError(f"{where}: ladder= must be a ladder(...), got {ladder!r}")
    if base is not None and (not _plain_int(base) or base <= 0):
        raise ItemDeclarationError(f"{where}: base={base!r} must be a stock item_template entry")
    if like is not None and (not _plain_int(like) or like <= 0):
        raise ItemDeclarationError(f"{where}: like={like!r} must be a stock item_template entry")
    first = ladder.tiers[0]
    if base is not None:
        if like is not None:
            raise ItemDeclarationError(f"{where}: base= and like= exclude each other (a base= item is the stock row)")
        if first.explicit or first.deferred:
            raise ItemDeclarationError(
                f"{where}: base= makes the stock item the ladder's first tier, so ladder {ladder.name!r}'s first tier "
                f"{first.name!r} must take the item's own level and must not be deferred"
            )
    elif not isinstance(name, str) or not name.strip():
        raise ItemDeclarationError(f"{where}: a new item (no base=) needs name=")
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise ItemDeclarationError(f"{where}: name={name!r} must be a non-empty string")
    if first.explicit:
        for keyword, value in (("ilvl", ilvl), ("quality", quality), ("required_level", required_level)):
            if value is not None:
                raise ItemDeclarationError(
                    f"{where}: ladder {ladder.name!r} sets every tier's level, so {keyword}= has nothing to set"
                )
    else:
        if base is None and ilvl is None:
            raise ItemDeclarationError(f"{where}: a new item on ladder {ladder.name!r} needs ilvl= for its first tier")
        if ilvl is not None and (not _plain_int(ilvl) or not 1 <= ilvl <= MAX_ITEM_LEVEL):
            raise ItemDeclarationError(f"{where}: ilvl={ilvl!r} must be an int in 1-{MAX_ITEM_LEVEL}")
        if quality is not None:
            _check_quality(where, quality)
        if required_level is not None:
            _check_required_level(where, required_level)
    if itemization is not None:
        if itemization != "live":
            raise ItemDeclarationError(f"{where}: itemization={itemization!r}; the only value is \"live\"")
        if base is None:
            raise ItemDeclarationError(f"{where}: itemization=\"live\" adopts a stock row, so it needs base=")
        given = [k for k, v in (("primary", primary), ("secondary", secondary), ("primary_share", primary_share),
                                ("budget_mult", budget_mult)) if v is not None]
        given += [k for k, v in (("extra_stamina", extra_stamina), ("extra_armor", extra_armor),
                                 ("extra_dps", extra_dps), ("extra_block", extra_block),
                                 ("free_dps", free_dps)) if v]
        if given:
            raise ItemDeclarationError(
                f"{where}: itemization=\"live\" keeps the live row's shapes, share, multiplier and deltas; drop "
                f"{', '.join(given)}"
            )
    else:
        for keyword, value in (("primary", primary), ("secondary", secondary)):
            if value is not None and not ((isinstance(value, str) and value)
                                          or (_plain_int(value) and value > 0)):
                raise ItemDeclarationError(f"{where}: {keyword}={value!r} must be an item_shape name or shape_id")
        if primary is None and secondary is None:
            raise ItemDeclarationError(f"{where}: give primary= and/or secondary= (or itemization=\"live\")")
        if primary_share is not None and primary_share not in PRIMARY_SHARES:
            raise ItemDeclarationError(f"{where}: primary_share={primary_share!r} must be one of {PRIMARY_SHARES}")
        if primary is None and primary_share not in (None, 0):
            raise ItemDeclarationError(f"{where}: no primary shape means primary_share 0, not {primary_share}")
        if secondary is None and primary_share not in (None, 10000):
            raise ItemDeclarationError(f"{where}: no secondary shape means primary_share 10000, not {primary_share}")
        if budget_mult is not None and (not _number(budget_mult) or not 0 < budget_mult <= 2):
            raise ItemDeclarationError(f"{where}: budget_mult={budget_mult!r} must be a number in (0, 2]")
    if unique_equip is not None and not isinstance(unique_equip, bool):
        raise ItemDeclarationError(f"{where}: unique_equip= is True, False or None (None: True for an effect item)")
    if not isinstance(free_dps, bool):
        raise ItemDeclarationError(f"{where}: free_dps= is True or False")
    if free_dps and extra_dps is None:
        raise ItemDeclarationError(
            f"{where}: free_dps=True funds the DPS of extra_dps= over the role cell's; declare extra_dps="
        )
    if weapon_role is not None and weapon_role not in WEAPON_ROLES:
        raise ItemDeclarationError(f"{where}: weapon_role={weapon_role!r} must be one of {WEAPON_ROLES}")
    for keyword, value in (("extra_stamina", extra_stamina), ("extra_armor", extra_armor),
                           ("extra_dps", extra_dps), ("extra_block", extra_block)):
        if keyword == "extra_dps" and value is None:
            continue
        if not _number(value) or not -1 < value <= 2:
            raise ItemDeclarationError(
                f"{where}: {keyword}={value!r} is a fraction of the tier's baseline (e.g. 0.25 for +25%), in (-1, 2]"
            )
    spell_tuple = _check_spells(where, base, spells, keep_spells)
    socket_tuple = _check_sockets(where, sockets, socket_bonus)
    columns = _check_columns(where, columns)
    override_tuple = ()
    if overrides is not None:
        if not isinstance(overrides, dict):
            raise ItemDeclarationError(f"{where}: overrides= is a {{tier name: {{column: value}}}} dict")
        pairs = []
        for tier_name, cols in overrides.items():
            spec = ladder.tier(tier_name)
            if spec is None:
                raise ItemDeclarationError(
                    f"{where}: overrides names tier {tier_name!r}, which ladder {ladder.name!r} does not have "
                    f"({', '.join(ladder.names)})"
                )
            if spec.deferred:
                raise ItemDeclarationError(f"{where}: overrides names tier {tier_name!r}, which is deferred")
            if base is not None and spec is ladder.tiers[0]:
                raise ItemDeclarationError(
                    f"{where}: tier {tier_name!r} is the stock row itself; pass its columns to item() instead"
                )
            if not isinstance(cols, dict) or not cols:
                raise ItemDeclarationError(f"{where}: overrides[{tier_name!r}] must be a non-empty column dict")
            pairs.append((tier_name, tuple(sorted(_check_columns(f"{where} overrides[{tier_name!r}]", cols).items()))))
        override_tuple = tuple(pairs)
    decl = ItemDecl(
        key=key, ladder=ladder, base=base, name=name, like=like, ilvl=ilvl,
        quality=None if quality is None else int(quality), required_level=required_level,
        primary=primary, secondary=secondary, primary_share=primary_share,
        budget_mult=None if budget_mult is None else float(budget_mult), itemization=itemization,
        extra_stamina=float(extra_stamina), extra_armor=float(extra_armor),
        extra_dps=None if extra_dps is None else float(extra_dps), extra_block=float(extra_block),
        free_dps=free_dps, weapon_role=weapon_role, spells=spell_tuple, keep_spells=keep_spells, sockets=socket_tuple,
        socket_bonus=socket_bonus, overrides=override_tuple, columns=tuple(sorted(columns.items())),
        unique_equip=unique_equip,
    )
    active = _registry._active
    if active is not None:
        if any(entry["id"] == key for entry in active.item_declarations):
            raise _registry.DuplicateIdError(f"{where}: the key is declared twice")
        active.item_declarations.append({"id": key, "_decl": decl})
    return decl


def load_items_dir(dir_path: Path, **kwargs) -> dict:
    """Loads `source/items/*.py` as one package (so `deadmines.py` can `from .ladders import VANILLA_DUNGEON`) and
    returns the merged-dict shape `registry.load_classes_dir` returns, for `generate.py` to merge like source/world.
    A missing directory, or one with no `*.py` (only the lock), declares nothing. `kwargs` go to
    `registry.load_class_package` (`ids_cfg`, `live_data`, ...)."""
    merged: dict = {key: [] for key in _registry.MERGE_KEYS}
    merged["spell_var_names"] = {}
    merged["creature_var_names"] = {}
    if not dir_path.is_dir() or not any(p for p in dir_path.glob("*.py") if not p.name.startswith("_")):
        return merged
    reg = _registry.load_class_package(dir_path, **kwargs)
    for key in _registry.MERGE_KEYS:
        seen = set()
        for entry in getattr(reg, key):
            dedup_id = entry.get("_dedup_id", entry.get("id"))
            if dedup_id in seen:
                raise _registry.DuplicateIdError(f"{key} entry {dedup_id!r} appears twice in source/items/")
            seen.add(dedup_id)
            entry.setdefault("_source_class", "items")
            merged[key].append(entry)
    merged["spell_var_names"].update(reg.spell_var_names)
    merged["creature_var_names"].update(reg.creature_var_names)
    return merged


ITEMS_DIR = Path(__file__).resolve().parents[2] / "source" / "items"


def declared_item_bases(dir_path: Path = ITEMS_DIR) -> frozenset[int]:
    """The stock entries `source/items/*.py` takes over with `item(..., base=<entry>)`, read from the files' syntax
    trees without running them. A source/world file that edits stock items in bulk (ranged_weapons.py) skips these:
    one owner per entry, and the item declaration carries the columns itself. Only a literal int `base=` counts; any
    other form is not seen here, and the item resolver's one-owner check then reports the clash."""
    import ast

    bases: set[int] = set()
    if not dir_path.is_dir():
        return frozenset()
    for path in sorted(dir_path.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name != "item":
                continue
            for keyword in node.keywords:
                value = keyword.value
                if (keyword.arg == "base" and isinstance(value, ast.Constant) and isinstance(value.value, int)
                        and not isinstance(value.value, bool)):
                    bases.add(value.value)
    return frozenset(bases)


def item_owned_entries(dir_path: Path = ITEMS_DIR) -> frozenset[int]:
    """Every `item_template` entry source/items owns: the stock `base=` entries (`declared_item_bases`), every
    entry of `item_ids.lock` (the minted tiers, the recorded bases, retired lines included) and every entry of
    `quest_rewards.lock` (the quest rewards source/items/quest_rewards.py takes over). Once a write run has
    minted a ranged weapon's tiers they are live rows too, so a bulk `item_template()` editor (ranged_weapons.py) skips
    all of these."""
    owned = set(declared_item_bases(dir_path))
    # item_ids.lock, and quest_rewards.lock: source/items/quest_rewards.py declares one item(base=<entry>) per line of
    # it in a loop, which declared_item_bases' syntax read cannot see.
    for name in ("item_ids.lock", "quest_rewards.lock"):
        lock = dir_path / name
        if lock.is_file():
            for raw in lock.read_text(encoding="utf-8").splitlines():
                token = raw.split("#", 1)[0].split()[:1]
                if token and token[0].isdigit():
                    owned.add(int(token[0]))
    return frozenset(owned)


def _check_spells(where: str, base, spells, keep_spells) -> tuple[ItemSpell, ...] | None:
    if not isinstance(keep_spells, bool):
        raise ItemDeclarationError(f"{where}: keep_spells= is True or False")
    if keep_spells and base is None:
        raise ItemDeclarationError(f"{where}: keep_spells=True keeps a stock item's spells, so it needs base=")
    if spells is None:
        return None
    if keep_spells:
        raise ItemDeclarationError(f"{where}: spells= replaces the stock spells; drop keep_spells=True")
    spells = tuple(spells)
    if len(spells) > MAX_SPELLS:
        raise ItemDeclarationError(f"{where}: at most {MAX_SPELLS} spells, got {len(spells)}")
    for spell in spells:
        if not isinstance(spell, ItemSpell):
            raise ItemDeclarationError(
                f"{where}: spells= takes use_spell(...) / equip_spell(...) / hit_spell(...), got {spell!r}"
            )
    return spells


def _check_sockets(where: str, sockets, socket_bonus) -> tuple[int, ...] | None:
    if sockets is None:
        if socket_bonus is not None:
            raise ItemDeclarationError(f"{where}: socket_bonus= without sockets=")
        return None
    sockets = tuple(sockets)
    if len(sockets) > MAX_SOCKETS:
        raise ItemDeclarationError(f"{where}: at most {MAX_SOCKETS} sockets, got {len(sockets)}")
    for color in sockets:
        if not _plain_int(color) or color not in tuple(Socket):
            raise ItemDeclarationError(f"{where}: socket {color!r} must be a Socket (META/RED/YELLOW/BLUE)")
    if socket_bonus is not None and (not _plain_int(socket_bonus) or socket_bonus < 0):
        raise ItemDeclarationError(f"{where}: socket_bonus={socket_bonus!r} must be a SpellItemEnchantment id")
    return tuple(int(c) for c in sockets)


def _check_columns(where: str, columns: dict) -> dict:
    stats = sorted(c for c in columns if c in STAT_COLUMNS)
    if stats:
        raise ItemDeclarationError(
            f"{where}: {', '.join(stats)} come from the itemization budget and cannot be passed (set shapes, "
            f"primary_share, budget_mult or an extra_* fraction instead)"
        )
    keyword = sorted(c for c in columns if c in KEYWORD_COLUMNS)
    if keyword:
        raise ItemDeclarationError(
            f"{where}: " + "; ".join(f"{c} is set with {KEYWORD_COLUMNS[c]}" for c in keyword)
        )
    flags = columns.get("Flags")
    if flags is not None and (not _plain_int(flags) or flags & HEROIC_TOOLTIP_FLAG):
        raise ItemDeclarationError(
            f"{where}: Flags={flags!r}: the Heroic tooltip flag 0x8 belongs to the ladder tier (heroic_flag=True)"
        )
    return dict(columns)
