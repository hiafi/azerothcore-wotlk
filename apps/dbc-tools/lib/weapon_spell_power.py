"""
Caster weapon spell power from weapon DPS (weapon-scaling plan v2, rulings 3-6, stages WS0b/WS0c): every weapon (item
class 2) with a spell power multiplier `m` > 0 carries one Spell Power stat line (`ITEM_MOD_SPELL_POWER`, 45) of
`lround(k_sp(slot) x DPS x m)`, off the stat budget like the weapon DPS itself, and no other Spell Power: the line its
shape budgets is stripped and that budget is spread over the shape's other stats.

**The constant.** `ONE_HAND_K` (spell power per point of DPS on a one-hand) times `SLOT_FACTORS` (user ruling
2026-11-17: staff 0.82, wand 0.85 of the one-hand k) gives `K_SP`, the only table the code reads. With `ONE_HAND_K` 0
(until WS1 calibrates it) the feature is off: every coefficient is 0, nothing is stripped, no line is written, and
every run and test is unchanged. Callers take `k=None` for `K_SP`; tests pass their own table.

**Turning it back off (open question 6 of the WS0b report, kept as is).** The coefficient is data: every generate run
writes `item_itemization.spell_power_per_dps` = k_sp(slot) x m for every weapon it covers and only the rows that
differ from the replayed table, so setting `ONE_HAND_K` back to 0 and running a full generate writes 0 back into each
row that carries a value (declared tiers through lib/item_emit.py, undeclared weapons through `undeclared_rows()`).
The materialized stats follow at the next boot. Rows of entries the generator no longer covers (a retired minted
tier, an entry a declaration dropped) keep whatever value they last got.

**Item level limit (user ruling 2026-11-17, WS0 review).** Only a weapon of item level `MAX_ITEM_LEVEL` (100) and
below gets the rule: above it the coefficient is 0 (a declared tier per its own item level, an undeclared weapon per
its ItemLevel), so a TBC/WotLK weapon keeps its budgeted Spell Power until those tiers get their own pass.

**The multiplier `m`.** `item(..., weapon_spell_power_mult=)` declares it (a number in [0, 2]); undeclared it is the
role default (`ROLE_DEFAULT_MULT`: caster 1.0, physical and tank 0). The role is the item generator's own rule
(`item_variants.shape_role`: a Dodge / Parry / Block / Defense secondary = tank, else an Intellect / Spirit / Spell
Power lead primary = caster), or `weapon_role=`. It is read from the shapes as recorded (they are never changed), so a
weapon whose primary leads with Spell Power stays a caster weapon. Every tier of a ladder carries its item's m. A
physical weapon whose shape budgets Spell Power (37 hybrids) keeps it: m is 0 there.

**Where the line is made.** The coefficient goes into the item's `item_itemization.spell_power_per_dps` column. The
worldserver (`ItemBudget.cpp` `ResolveBudget` / `ApplyItemizationAllocation`) and its Python mirror
(`item_lib.budget.compute_breakdown` / `materialized_item_fields`) read it: Spell Power leaves each side of the shape
allocation (the side spreads the dropped share over its other stats in proportion to their own shares; a Spell
Power-only primary hands its whole budget to the secondary shape), and `weapon_spell_power = lround(coef x final
DPS)` is written as the stat line after Stamina. The budget never prices it: it is not an allocation, so
`item_stat_cost` never sees it.

**Undeclared weapons (ruling A).** `undeclared_rows()` applies the same rule to every itemized weapon no item
declaration owns: the role comes from its `item_itemization` row's shapes (the stock conversion's record) and its row
is rewritten with the coefficient (the `item_itemization` keyed block lib/item_emit.py renders). A weapon without an
itemization row has no shape, so neither a role nor a budget to spread: a caster-lead one (literal first stat
Intellect / Spirit / Spell Power) is listed as unclassifiable and left as it is (user ruling 2026-11-17).
"""

from __future__ import annotations

from dataclasses import dataclass, field

ITEM_CLASS_WEAPON = 2
ITEM_MOD_SPELL_POWER = 45
MAX_ITEM_PROTO_STATS = 10
STAT_COLUMNS = tuple(c for n in range(1, MAX_ITEM_PROTO_STATS + 1) for c in (f"stat_type{n}", f"stat_value{n}"))

# Spell power per point of weapon DPS on a one-hand weapon. 0 = the feature is off (WS1 calibrates it, WS2 sets it).
ONE_HAND_K = 0.0
# Each slot kind's k as a fraction of the one-hand k (user ruling 2026-11-17, WS0b report "Slot parity"): a staff
# carries the caster cells' one-hand / two-hand DPS ratio (~0.82), a wand 0.85 (its DPS sits on the two-hand curve,
# so this keeps its Spell Power near its budget share of a one-hand's).
SLOT_FACTORS = {
    "one_hand": 1.0,  # One-Hand (13), Main Hand (21), Off Hand (22)
    "two_hand": 0.82,  # Two-Hand (17): staves, two-hand maces and swords, polearms
    "ranged": 0.85,  # Ranged (15), Thrown (25), Ranged Right (26): wands (a caster bow or gun takes it too)
}


# Only weapons of this item level and below get the rule (user ruling 2026-11-17, WS0 review): a TBC/WotLK weapon
# keeps coefficient 0 and its budgeted Spell Power until those tiers get their own pass.
MAX_ITEM_LEVEL = 100


def _check_k(where: str, table: dict) -> dict:
    """Refuses a negative k (ItemBudget.cpp refuses a negative `spell_power_per_dps` and leaves the item
    unmaterialized, so a typo must stop the run instead)."""
    for kind, value in table.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not value >= 0:
            raise ValueError(f"weapon spell power: {where}: k_sp[{kind!r}] = {value!r} must be a number >= 0")
    return table


def k_table(one_hand_k: float) -> dict:
    """The per-slot k table for a one-hand k (`K_SP` is `k_table(ONE_HAND_K)`). A negative k or slot factor
    raises."""
    _check_k("SLOT_FACTORS", SLOT_FACTORS)
    _check_k("ONE_HAND_K", {"one_hand": one_hand_k})
    return {kind: one_hand_k * factor for kind, factor in SLOT_FACTORS.items()}


K_SP = k_table(ONE_HAND_K)
SLOT_KINDS = {13: "one_hand", 21: "one_hand", 22: "one_hand", 17: "two_hand", 15: "ranged", 25: "ranged",
              26: "ranged"}
MULT_MIN, MULT_MAX = 0.0, 2.0
ROLE_DEFAULT_MULT = {"caster": 1.0, "physical": 0.0, "tank": 0.0}
CASTER_LEAD_STATS = frozenset((5, 6, 45))  # Intellect, Spirit, Spell Power (item_variants.CASTER_LEAD_STATS)
# item_itemization.spell_power_per_dps is a FLOAT column read through MySQL's text protocol: 4 decimals keep a
# coefficient below 100 within 6 significant digits, so its text round trip gives the C++ the float Python uses.
COEFFICIENT_DIGITS = 4


def _table(k: dict | None) -> dict:
    return K_SP if k is None else _check_k("k", k)


def enabled(k: dict | None = None) -> bool:
    """True when any slot's k_sp is above 0 (the feature is on)."""
    return any(value > 0 for value in _table(k).values())


def slot_kind(inv_type: int) -> str | None:
    return SLOT_KINDS.get(int(inv_type))


def default_mult(role: str) -> float:
    """The role default of m (ruling 5): caster 1.0, physical and tank 0."""
    return ROLE_DEFAULT_MULT.get(role, 0.0)


def resolve_mult(declared: float | None, role: str) -> float:
    """A declared m wins; else the role's default."""
    return float(declared) if declared is not None else default_mult(role)


def coefficient(item_class: int, inv_type: int, mult: float, k: dict | None = None, *, item_level: int) -> float:
    """`k_sp(slot) x m`, rounded to `COEFFICIENT_DIGITS`: spell power per point of the weapon's DPS (0 for a
    non-weapon, a slot without a k, m 0, an item level above `MAX_ITEM_LEVEL` or the feature off)."""
    table = _table(k)
    if int(item_class) != ITEM_CLASS_WEAPON or not mult or int(item_level) > MAX_ITEM_LEVEL:
        return 0.0
    kind = slot_kind(inv_type)
    if kind is None:
        return 0.0
    return round(float(table.get(kind, 0.0)) * float(mult), COEFFICIENT_DIGITS)


def check_mult(where: str, value) -> str | None:
    """The DSL check of `weapon_spell_power_mult=` (None: fine)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not MULT_MIN <= value <= MULT_MAX:
        return f"{where}: weapon_spell_power_mult={value!r} must be a number in [{MULT_MIN:g}, {MULT_MAX:g}]"
    return None


# ---------------------------------------------------------------------------------------------------------------------
# Undeclared weapons


@dataclass
class UndeclaredResult:
    rows: list[dict] = field(default_factory=list)  # item_itemization rows whose coefficient changes
    covered: list[int] = field(default_factory=list)  # every undeclared weapon with a coefficient above 0
    unclassifiable: list[tuple[int, str]] = field(default_factory=list)  # caster-lead weapons with no itemization row
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


_BREAKDOWN_INT_COLUMNS = (
    "entry", "ItemLevel", "Quality", "InventoryType", "class", "subclass", "itemset", "delay",
    "socketColor_1", "socketColor_2", "socketColor_3",
)


def literal_caster_lead(row: dict) -> bool:
    """The row's own first stat line is Intellect, Spirit or Spell Power (and no tank stat is on it)."""
    stats = [_int(row.get(f"stat_type{n}")) for n in range(1, MAX_ITEM_PROTO_STATS + 1)]
    stats = [s for s in stats if s]
    return bool(stats) and stats[0] in CASTER_LEAD_STATS and not {12, 13, 14, 15, 48} & set(stats)


def undeclared_rows(live_rows: dict[int, dict], owned, tables: dict, catalog: dict, *,
                    k: dict | None = None) -> UndeclaredResult:
    """The `item_itemization` rows of every itemized weapon in `live_rows` that `owned` (the entries the item
    declarations write themselves) leaves out and whose `spell_power_per_dps` should change: k_sp(slot) x the role
    default m, against the replayed row's value. With the feature off and no value in the table this is empty. Each
    changed row is checked the way ItemBudget.cpp checks it (the budget resolves, the stat lines fit 10 slots)."""
    from . import item_variants  # noqa: PLC0415

    budget, _ = item_variants._item_lib()
    out = UndeclaredResult()
    owned = set(owned)
    itemization = tables.get("item_itemization", {})
    for entry in sorted(live_rows):
        row = live_rows[entry]
        if _int(row.get("class")) != ITEM_CLASS_WEAPON or entry in owned:
            continue
        item_level = _int(row.get("ItemLevel"))
        item_row = itemization.get((entry,))
        if item_row is None:
            if enabled(k) and item_level <= MAX_ITEM_LEVEL and literal_caster_lead(row):
                out.unclassifiable.append((entry, str(row.get("name") or "")))
            continue
        role = item_variants.shape_role(catalog.get(_int(item_row.get("primary_shape_id"))),
                                        catalog.get(_int(item_row.get("secondary_shape_id"))))
        coef = coefficient(ITEM_CLASS_WEAPON, _int(row.get("InventoryType")), default_mult(role), k,
                           item_level=item_level)
        if coef > 0:
            out.covered.append(entry)
        if abs(float(item_row.get("spell_power_per_dps") or 0.0) - coef) < 1e-6:
            continue
        new_row = {c: item_row.get(c, 0) for c in item_row}
        new_row.update(entry=entry, spell_power_per_dps=coef)
        stand_in = dict(row)
        for column in _BREAKDOWN_INT_COLUMNS:
            stand_in[column] = _int(stand_in.get(column))
        try:
            breakdown = budget.compute_breakdown(stand_in, new_row, tables, catalog)
        except budget.BudgetError as error:
            out.errors.append(f"weapon spell power: item {entry} ({row.get('name')}): the budget does not resolve: "
                              f"{error}")
            continue
        # ItemBudget.cpp's slot check: every allocation (zero ones too) plus Stamina plus the Spell Power line.
        lines = budget.stat_line_count(breakdown)
        if lines > MAX_ITEM_PROTO_STATS:
            out.errors.append(f"weapon spell power: item {entry} ({row.get('name')}): {lines} stat lines with the "
                              f"Spell Power line exceed the {MAX_ITEM_PROTO_STATS} stat slots")
            continue
        out.rows.append(new_row)
    if out.unclassifiable:
        shown = ", ".join(str(e) for e, _ in out.unclassifiable[:20])
        out.notes.append(
            f"weapon spell power: {len(out.unclassifiable)} caster-lead weapon(s) have no item_itemization row, so no "
            f"shape or budget to spread; left unchanged ({shown}{' ...' if len(out.unclassifiable) > 20 else ''})"
        )
    if out.covered or out.rows:
        out.notes.append(f"weapon spell power: {len(out.covered)} undeclared weapon(s) covered, {len(out.rows)} "
                         f"item_itemization row(s) change")
    return out
