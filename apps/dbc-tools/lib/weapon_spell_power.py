"""
Caster weapon spell power from weapon DPS (weapon-scaling plan v2, rulings 3-6, stages WS0b/WS0c): every weapon (item
class 2) with a spell power multiplier `m` > 0 carries one Spell Power stat line (`ITEM_MOD_SPELL_POWER`, 45) of
`lround(k_sp(slot) x DPS x m)`, off the stat budget like the weapon DPS itself, and no other Spell Power: the line its
shape budgets is stripped and that budget is spread over the shape's other stats.

**The constant.** `ONE_HAND_K` (spell power per point of DPS on a one-hand) times `SLOT_FACTORS` (user ruling
2026-11-17: staff 0.835 of the one-hand k since LS4, ranged slots 0) gives `K_SP`, the only table the code reads.
With `ONE_HAND_K` 0 (until WS1 calibrates it) the feature is off: every coefficient is 0, nothing is stripped, no
line is written, and every run and test is unchanged. Callers take `k=None` for `K_SP`; tests pass their own table.

**Turning it back off (open question 6 of the WS0b report, kept as is).** The coefficient is data: every generate run
writes `item_itemization.spell_power_per_dps` = k_sp(slot) x m for every weapon it covers and only the rows that
differ from the replayed table, so setting `ONE_HAND_K` back to 0 and running a full generate writes 0 back into each
row that carries a value (declared tiers through lib/item_emit.py, undeclared weapons through `undeclared_rows()`).
The materialized stats follow at the next boot. Rows of entries the generator no longer covers (a retired minted
tier, an entry a declaration dropped) keep whatever value they last got.

**No item level limit (user ruling 2026-11-20, Scarlet gear review M2).** Every weapon gets the rule, whatever its item
level: weapon spell power scales through TBC and WotLK. This replaces the 2026-11-17 WS0 review ruling, which held
weapons above item level 100 at coefficient 0 with their budgeted Spell Power (it left the vanilla hard mode ladder's
101 tier, and every TBC/WotLK caster weapon, without the line).

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

**The physical stat budget (secondary stat curve LS4, handoff 1.8, user ruling 2026-11-20).** A weapon's DPS scales its
spell power only, never its stats. Every weapon with a spell power coefficient above 0 (a one-hand, main hand, off hand
or two-hand weapon with m > 0) takes the *physical* role cell's `budget_mult` for its (slot, Quality, item level bucket)
(`PhysicalCells`; Main Hand and Off Hand use the One-Hand cell) and `dps_delta` 0: the curve DPS, no stat credit. The
caster cells' -20% DPS and their larger budget_mult are no longer read for it. Bows, guns and crossbows (item class 2,
subclass 2 / 3 / 18; InventoryType 15 / 26) get `dps_delta` 0 too and keep their physical `budget_mult`: their DPS
then feeds only the hunter's ranged attack power (`WeaponScaling.RangedApPerDps`). Wands, thrown weapons and off-hand
frills are not changed. A declared `budget_mult=` / `extra_dps=` wins; the lock file is never edited (the rule sits
beside the cells). `PhysicalCells` reads the frozen lock first and the live sample for a cell the lock lacks, never
appends to the lock, and where a cell is `none` or absent it falls back to the nearest physical cell of the same slot
(same Quality, nearest bucket, a lower bucket on a tie, then the other Qualities by distance); every fallback is kept
in `PhysicalCells.fallbacks` for the run's notes.

**The staff factor.** With `dps_delta` 0 a one-hand and a two-hand take the curve DPS of their own slot, so a staff
carries the same spell power as a main hand when its k is the main hand's times the one-hand / two-hand curve DPS
ratio. That ratio moves with item level and Quality (0.75 - 0.97 over ilvl 57-101, Rare and Epic); `SLOT_FACTORS` holds
one constant, their median 0.835 (the choice between it and a per-(ilvl, Quality) factor is the user's).
"""

from __future__ import annotations

from dataclasses import dataclass, field

ITEM_CLASS_WEAPON = 2
# Hunter ranged weapons (handoff 1.8): item class 2 subclass bow / gun / crossbow in a ranged slot. Wands (19) and
# thrown weapons (16) are not.
HUNTER_RANGED_SUBCLASSES = frozenset((2, 3, 18))
HUNTER_RANGED_INV_TYPES = frozenset((15, 26))
# The physical role cell a slot reads (handoff 1.8): Main Hand and Off Hand use the One-Hand cell.
PHYSICAL_CELL_SLOT = {13: 13, 21: 13, 22: 13, 17: 17}
ITEM_MOD_SPELL_POWER = 45
MAX_ITEM_PROTO_STATS = 10
STAT_COLUMNS = tuple(c for n in range(1, MAX_ITEM_PROTO_STATS + 1) for c in (f"stat_type{n}", f"stat_value{n}"))

# Spell power per point of weapon DPS on a one-hand weapon (user ruling 2026-11-20, level60-stat-curve 1.9: 3.75;
# 7.5 before). 0 = the feature is off.
ONE_HAND_K = 3.75
# Each slot kind's k as a fraction of the one-hand k (user ruling 2026-11-17, WS0b report "Slot parity"): a staff
# carries the one-hand / two-hand curve DPS ratio, so it gives the spell power of a main hand (0.835: the median of
# item_weapon_dps_curve's 1H / 2H over ilvl 57-101, Rare and Epic; LS4 2026-11-20, was 0.82 from the caster cells' -20%
# DPS; one constant, the ratio itself runs 0.75-0.97). Ranged slots get 0 (user ruling 2026-11-17, after
# WS1: weapon spell power goes on actual weapons, not wands; a wand keeps its budgeted stats, Spell Power included).
SLOT_FACTORS = {
    "one_hand": 1.0,  # One-Hand (13), Main Hand (21), Off Hand (22)
    "two_hand": 0.835,  # Two-Hand (17): staves, two-hand maces and swords, polearms
    "ranged": 0.0,  # Ranged (15), Thrown (25), Ranged Right (26): wands (and a caster bow or gun) get none
}



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


def coefficient(item_class: int, inv_type: int, mult: float, k: dict | None = None) -> float:
    """`k_sp(slot) x m`, rounded to `COEFFICIENT_DIGITS`: spell power per point of the weapon's DPS (0 for a
    non-weapon, a slot without a k, m 0 or the feature off). Any item level (user ruling 2026-11-20)."""
    table = _table(k)
    if int(item_class) != ITEM_CLASS_WEAPON or not mult:
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


def takes_physical_budget(item_class: int, inv_type: int, mult: float, k: dict | None = None) -> bool:
    """True when the weapon's DPS feeds spell power (a coefficient above 0): it takes the physical role cell's
    budget_mult and a `dps_delta` of 0 (handoff 1.8)."""
    return coefficient(item_class, inv_type, mult, k) > 0


def is_hunter_ranged(item_class: int, subclass: int, inv_type: int) -> bool:
    """A bow, gun or crossbow: its DPS feeds only the hunter's ranged attack power, so `dps_delta` is 0."""
    return (int(item_class) == ITEM_CLASS_WEAPON and int(subclass) in HUNTER_RANGED_SUBCLASSES
            and int(inv_type) in HUNTER_RANGED_INV_TYPES)


QUALITY_ORDER_MAX = 6


@dataclass
class PhysicalCells:
    """The physical role cells' `budget_mult` for caster weapons (handoff 1.8). Read-only: the frozen lock first (a
    `none` line is a miss), the live sample for a cell the lock lacks (`item_variants.RoleCells.lookup`), never an
    append to the lock. A miss falls back to the nearest physical cell of the same slot: the same Quality at the nearest
    bucket (the lower one on a tie), then the other Qualities by distance. `fallbacks` records each one."""

    frozen: dict  # item_variants.parse_cells_lock(): {(role, inv_type, quality, bucket): (mult, fraction, where)|None}
    live: object  # item_variants.RoleCells
    fallbacks: dict = field(default_factory=dict)  # (slot, quality, bucket) -> "text"
    _memo: dict = field(default_factory=dict)

    def _cell(self, slot: int, quality: int, bucket: int, ilvl: int) -> tuple[float, str] | None:
        key = ("physical", slot, quality, bucket)
        if key in self.frozen:
            value = self.frozen[key]
            return None if value is None else (value[0], f"physical {slot} Quality {quality} bucket {bucket} (frozen)")
        found = self.live.lookup("physical", slot, quality, ilvl)
        return None if found is None else (found[0], found[2])

    def lookup(self, inv_type: int, quality: int, ilvl: int) -> tuple[float, str] | None:
        """(budget_mult, where) of the physical cell for the caster weapon's slot, Quality and item level, or None
        when the slot has no physical cell at all."""
        from . import item_variants  # noqa: PLC0415

        slot = PHYSICAL_CELL_SLOT.get(int(inv_type))
        if slot is None:
            return None
        last = len(item_variants.ROLE_CELL_BUCKETS) - 1
        low = item_variants.ROLE_CELL_BUCKETS[0][0]
        high = item_variants.ROLE_CELL_BUCKETS[last][1]
        level = min(max(int(ilvl), low), high)
        bucket = item_variants._bucket(level)
        memo_key = (slot, int(quality), bucket)
        if memo_key in self._memo:
            return self._memo[memo_key]
        result = self._cell(slot, int(quality), bucket, level)
        if result is None:
            qualities = sorted(range(QUALITY_ORDER_MAX + 1), key=lambda q: (abs(q - int(quality)), q))
            buckets = sorted(range(last + 1), key=lambda b: (abs(b - bucket), b))
            for q in qualities:
                for b in buckets:
                    if (q, b) == (int(quality), bucket):
                        continue
                    span = item_variants.ROLE_CELL_BUCKETS[b]
                    found = self._cell(slot, q, b, span[0])
                    if found is not None:
                        result = (found[0], f"fallback: {found[1]}")
                        wanted = "-".join(map(str, item_variants.ROLE_CELL_BUCKETS[bucket]))
                        self.fallbacks[memo_key] = (
                            f"physical {slot} Quality {quality} {wanted} -> Quality {q} "
                            f"{'-'.join(map(str, span))} ({found[0]:.4f})")
                        break
                if result is not None:
                    break
        self._memo[memo_key] = result
        return result

    def notes(self) -> list[str]:
        if not self.fallbacks:
            return []
        shown = "; ".join(f"{t}" for _, t in sorted(self.fallbacks.items()))
        return [f"weapon spell power: {len(self.fallbacks)} physical cell fallback(s): {shown}"]


# ---------------------------------------------------------------------------------------------------------------------
# Undeclared weapons


@dataclass
class UndeclaredResult:
    rows: list[dict] = field(default_factory=list)  # item_itemization rows whose coefficient changes
    covered: list[int] = field(default_factory=list)  # every undeclared weapon with a coefficient above 0
    unclassifiable: list[tuple[int, str]] = field(default_factory=list)  # caster-lead weapons with no itemization row
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    # One tuple per row that changes: (entry, InventoryType, subclass, ItemLevel, Quality, kind, old budget_mult, new
    # budget_mult, old dps_delta, new dps_delta, cell text), kind "caster" or "hunter ranged".
    stat_budget: list[tuple] = field(default_factory=list)


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
                    k: dict | None = None, cells: PhysicalCells | None = None) -> UndeclaredResult:
    """The `item_itemization` rows of every itemized weapon in `live_rows` that `owned` (the entries the item
    declarations write themselves) leaves out and whose `spell_power_per_dps` should change: k_sp(slot) x the role
    default m, against the replayed row's value. With the feature off and no value in the table this is empty. Each
    changed row is checked the way ItemBudget.cpp checks it (the budget resolves, the stat lines fit 10 slots).

    The physical stat budget (handoff 1.8): a weapon with a coefficient above 0 also takes `cells`' physical
    `budget_mult` and `dps_delta` 0 (`cells` None: the budget_mult stays, the rule is off); a bow, gun or crossbow
    takes `dps_delta` 0 and keeps its budget_mult."""
    from . import item_variants  # noqa: PLC0415

    budget, _ = item_variants._item_lib()
    out = UndeclaredResult()
    owned = set(owned)
    itemization = tables.get("item_itemization", {})
    for entry in sorted(live_rows):
        row = live_rows[entry]
        if _int(row.get("class")) != ITEM_CLASS_WEAPON or entry in owned:
            continue
        item_row = itemization.get((entry,))
        if item_row is None:
            if enabled(k) and literal_caster_lead(row):
                out.unclassifiable.append((entry, str(row.get("name") or "")))
            continue
        role = item_variants.shape_role(catalog.get(_int(item_row.get("primary_shape_id"))),
                                        catalog.get(_int(item_row.get("secondary_shape_id"))))
        inv_type, subclass = _int(row.get("InventoryType")), _int(row.get("subclass"))
        coef = coefficient(ITEM_CLASS_WEAPON, inv_type, default_mult(role), k)
        if coef > 0:
            out.covered.append(entry)
        new_values = {"spell_power_per_dps": coef}
        kind = cell_text = None
        if coef > 0 and cells is not None:
            found = cells.lookup(inv_type, _int(row.get("Quality")), _int(row.get("ItemLevel")))
            if found is None:
                out.errors.append(f"weapon spell power: item {entry} ({row.get('name')}): no physical role cell for "
                                  f"InventoryType {inv_type}, not even by fallback")
                continue
            new_values.update(budget_mult=found[0], dps_delta=0.0)
            kind, cell_text = "caster", found[1]
        elif is_hunter_ranged(ITEM_CLASS_WEAPON, subclass, inv_type):
            new_values.update(dps_delta=0.0)
            kind, cell_text = "hunter ranged", "budget_mult kept"
        if all(abs(float(item_row.get(c) or 0.0) - v) < (1e-6 if c == "spell_power_per_dps" else 1e-5)
               for c, v in new_values.items()):
            continue
        new_row = {c: item_row.get(c, 0) for c in item_row}
        new_row.update(entry=entry, **new_values)
        if kind is not None and any(c in new_values and abs(float(item_row.get(c) or 0.0) - new_values[c]) >= 1e-5
                                    for c in ("budget_mult", "dps_delta")):
            out.stat_budget.append((entry, inv_type, subclass, _int(row.get("ItemLevel")), _int(row.get("Quality")),
                                    kind, float(item_row.get("budget_mult") or 0.0),
                                    float(new_values.get("budget_mult", item_row.get("budget_mult") or 0.0)),
                                    float(item_row.get("dps_delta") or 0.0), float(new_values["dps_delta"]),
                                    cell_text))
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
    if out.stat_budget:
        out.notes.append(f"weapon spell power: {len(out.stat_budget)} undeclared weapon row(s) change budget_mult or "
                         f"dps_delta (physical stat budget: caster weapons and bows / guns / crossbows)")
    if cells is not None:
        out.notes += cells.notes()
    return out
