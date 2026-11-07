"""
Per-tier copies of an item's effect spells (item variants, stage IV10; user ruling 2026-11-06: item effects with
damage or healing scale with the item level).

    item("dm_powder_keg_fuse", ..., ladder=VANILLA_HARD_MODE,
         spells=(use_spell(powder_keg_fuse_205400, scale="budget"),))

**What gets copied.** For every `use_spell` / `equip_spell` / `hit_spell` declared with `scale="budget"`, every tier
of the item other than its ladder's *effect reference* tier gets its own copy of the spell and of every spell it
reaches (its *family*). The reference tier keeps the declared spells (ratio 1), so the declared numbers are that tier's
numbers. A ladder names it with `ladder(..., effect_reference="<tier>")` (wave 1 integration, user intent "effects
scale with item level like the item's stats"): the vanilla dungeon ladder's is Heroic (66 Epic), so its Normal tier
gets a copy with a ratio below 1 and the empowered tiers ratios above 1, whatever the item's own Normal level; the hard
mode ladder's is its first tier (71). A ladder without one uses its first tier. A spell reaches another through:

- an effect's `trigger_spell` (or a raw `EffectTriggerSpell_N`);
- a `$<id><token>` reference in its description or aura description (`$205401d`, `$205402a1`);
- a `pot_text(...)` of the other spell in its description: the spell `pot_text()` was called for (the registry records
  each call, `_pot_text_refs`; two spells with equal potency print the same expression, so the text alone cannot tell
  them apart), else, for a text built without the registry, every spell whose tooltip expressions it contains;
- a `linked_spell(trigger, effect)` row whose trigger it is.

Only spells declared in `source/items/` are followed: a reference to a stock or class spell stays shared.

**The copy** is the declaration with a new id, its damage and healing potency (`sp_potency`, `ap_potency`,
`base_potency` and the per-combo-point ones) times the tier's ratio, the amount of every stat-like aura without potency
(`STAT_AURAS`: ratings, stats, armor and resistances, spell power, attack power, health, mana regeneration, block value,
flat absorbs) times the ratio too, rounded, every family id inside it remapped to the same tier's copy (trigger spells,
`$<id>` tokens, `pot_text` expressions, linked spells), and everything else unchanged: name, icon, visuals, durations,
cooldowns, ranges, radii, proc chance, percentages (a -10% damage taken or +30% speed stays). Its own
`{potN}` placeholders are expanded from the scaled effects by `Spell.to_entry()`, so every tooltip shows the tier's own
numbers. The rows a spell owns by id are copied too: `spell_proc`, `spell_script_names` (the same C++ script runs for
every copy), `spell_custom_attr`, `spell_linked_spell`, and the potency rows (`spell_bonus_data`,
`spell_potency_correction`) come from the copy's own `to_entry()`.

**Ratio** (one number per item tier, rounded to 4 decimals):

    ratio(tier) = budget(tier) / budget(reference tier)
    budget(t)   = item_budget_curve[ilvl_t].budget x item_quality_mult[quality_t].mult x item_slot_mult[slot].mult

the step-1 base of `item_lib.budget.compute_breakdown` / `ItemBudget::ResolveBudget` without the item's own constant
factors (`budget_mult`, the set discount: the same on every tier, so they cancel, as the slot multiplier does) and
without the socket cost (an effect does not shrink because the tier has a socket).

**Refused** (ERROR): a family effect that deals damage or heals without potency (it could not scale), a
`weapon_potency` effect, a hand `bonus_coefficients()` row on a family spell, and a scaled spell that is not declared
in source/items.

**Ids**: `source/items/item_spell_ids.lock`, append-only like `item_ids.lock`: one `<spell id> <item key> <tier> <base
spell id>` line per copy, minted from source/ids.yaml's `item_spell_copy` block (205410-205599, inside the `items`
spell reservation) after the highest id in the file, skipping every declared spell id and every live `spell_dbc` row.
A (key, tier, base) keeps its id forever. A line no declaration wants any more stops the run unless it is marked
`retired <date>` (its id is never reused; the item row of a retired tier still names it, so keep the spell declared if
players hold the item). `--check` reports the lines a full run would append and never writes.

**C++**: the copies run the same scripts, so a script that casts another family spell must cast its own tier's copy.
`render_header()` writes `ItemSpellCopies.h` (pure, constexpr; `HEADER_PATH`), whose `ItemSpellCopies::Resolve(cast
spell id, base spell id)` gives the copy of `base` in the tier of the spell being cast (the base id itself on the first
tier or for a spell that has no copies). A full run rewrites the file when it changed; `--check` errors on a stale one.
"""

from __future__ import annotations

import dataclasses
import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import potency as _potency

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
LOCK_PATH = TOOL_ROOT / "source" / "items" / "item_spell_ids.lock"
HEADER_PATH = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Generated" / "ItemSpellCopies.h"
LOCK_BLOCK = "item_spell_copy"  # source/ids.yaml: a sub-range of `spell` and of reservations.items.spell
SOURCE_CLASS = "items"  # `_source_class` of the spells source/items declares
RATIO_DIGITS = 4
LOCK_HEADER = (
    "# Item effect spell copies (item variants IV10; lib/item_spell_copies.py): one line per (item key, tier, base\n"
    "# spell), `<spell id> <item key> <tier> <base spell id> [retired <date>]`, minted from source/ids.yaml's\n"
    "# item_spell_copy block. Every tier but the ladder's effect reference tier carries its own copy of each\n"
    "# `scale=\"budget\"` spell and of every spell it reaches, damage, healing and stat auras scaled by the tier's stat\n"
    "# budget over the reference tier's.\n"
    "# Append-only: a full generate.py run appends new lines; never reorder, renumber or delete one (an id must never\n"
    "# move or be reused). A merge conflict: keep the merged side's lines, drop the other side's new lines and delete\n"
    "# its not-yet-imported rev_*.sql, then re-run generate.py (same recovery as item_ids.lock).\n"
)

# Effects that deal damage or heal: they must carry potency to scale (lib/dsl/constants.py EffectType / AuraType).
DAMAGE_HEAL_EFFECTS = frozenset((2, 9, 10, 17, 31, 58, 121))  # school damage, leech, heal, weapon damage kinds
APPLY_AURA_EFFECTS = frozenset((6, 27, 35, 65, 119, 128, 129))  # apply aura, persistent / area auras
DAMAGE_HEAL_AURAS = frozenset((3, 8, 15, 43, 53, 69))  # periodic damage / heal, damage shield, proc damage, leech,
# absorb
SCALED_FIELDS = ("sp_potency", "ap_potency", "base_potency", "cp_sp_potency", "cp_ap_potency", "cp_base_potency")
# Stat-like aura amounts a copy scales by the ratio (SpellAuraDefines.h AuraType): flat amounts an item's stats would
# also carry. Percent auras (damage done / taken %, speed %, haste %), proc chances, durations, cooldowns and radii stay.
# An effect with potency (or potency_excluded: a script sizes it) is never touched here.
STAT_AURAS = {
    13: "MOD_DAMAGE_DONE (flat spell power)",
    22: "MOD_RESISTANCE (armor and resistances)",
    29: "MOD_STAT",
    34: "MOD_INCREASE_HEALTH",
    69: "SCHOOL_ABSORB (a flat absorb without potency)",
    83: "MOD_BASE_RESISTANCE",
    85: "MOD_POWER_REGEN (mana per 5)",
    97: "MANA_SHIELD (a flat absorb without potency)",
    99: "MOD_ATTACK_POWER",
    101: "MOD_RESISTANCE_EXCLUSIVE",
    124: "MOD_RANGED_ATTACK_POWER",
    135: "MOD_HEALING_DONE (flat healing power)",
    158: "MOD_SHIELD_BLOCKVALUE",
    189: "MOD_RATING (every combat rating, the custom stats included)",
}
TEXT_KEYS = ("Description_Lang_enUS", "AuraDescription_Lang_enUS")
_ID_TOKEN_RE = re.compile(r"\$(\d+)(?=[a-zA-Z])")
_KEY = r"[a-z][a-z0-9_]*"
_LINE_RE = re.compile(rf"^(\d+) ({_KEY}) ({_KEY}) (\d+)(?: retired (\d{{4}}-\d{{2}}-\d{{2}}))?$")


class LockError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------------------------------
# Lock


@dataclass(frozen=True)
class LockLine:
    spell_id: int
    key: str
    tier: str
    base: int
    retired: str | None = None
    number: int = 0

    @property
    def triple(self) -> tuple[str, str, int]:
        return self.key, self.tier, self.base


@dataclass
class Lock:
    lines: list[LockLine] = field(default_factory=list)
    text: str = ""

    @property
    def by_triple(self) -> dict[tuple[str, str, int], LockLine]:
        return {line.triple: line for line in self.lines}


def parse_lock(text: str, block: dict | None = None) -> Lock:
    """Reads the lock; LockError on a malformed line, a repeated id or (key, tier, base), or an id outside `block`."""
    lock = Lock(text=text)
    ids: dict[int, int] = {}
    triples: dict[tuple[str, str, int], int] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        where = f"{LOCK_PATH.name} line {number}"
        m = _LINE_RE.match(line)
        if not m:
            raise LockError(f"{where}: expected `<spell id> <item key> <tier> <base spell id> [retired <date>]`, "
                            f"got {raw!r}")
        entry = LockLine(int(m.group(1)), m.group(2), m.group(3), int(m.group(4)), m.group(5), number)
        if entry.spell_id in ids:
            raise LockError(f"{where}: spell {entry.spell_id} is already on line {ids[entry.spell_id]}")
        if entry.triple in triples:
            raise LockError(f"{where}: {entry.key} {entry.tier} {entry.base} is already on line "
                            f"{triples[entry.triple]}")
        if block and not block["start"] <= entry.spell_id <= block["end"]:
            raise LockError(f"{where}: {entry.spell_id} is outside source/ids.yaml's {LOCK_BLOCK} block "
                            f"({block['start']}-{block['end']})")
        ids[entry.spell_id] = number
        triples[entry.triple] = number
        lock.lines.append(entry)
    return lock


def load_lock(path: Path = LOCK_PATH, block: dict | None = None) -> Lock:
    return parse_lock(path.read_text(encoding="utf-8") if path.is_file() else "", block)


def lock_text(lock: Lock, appended: list[str]) -> str:
    text = lock.text or LOCK_HEADER
    if appended:
        if not text.endswith("\n"):
            text += "\n"
        text += "".join(f"{line}\n" for line in appended)
    return text


def reservation(ids_cfg: dict) -> dict | None:
    return ids_cfg.get(LOCK_BLOCK)


# ---------------------------------------------------------------------------------------------------------------------
# Ratio


def stat_budget(tables: dict, ilvl: int, quality: int, inv_type: int) -> float | None:
    """The tier's stat budget before the item's own constant factors (see the module docstring), or None when a
    reference row is missing."""
    curve = tables["item_budget_curve"].get((ilvl,))
    qual = tables["item_quality_mult"].get((quality,))
    slot = tables["item_slot_mult"].get((inv_type,))
    if not (curve and qual and slot):
        return None
    return float(curve["budget"]) * float(qual["mult"]) * float(slot["mult"])


def tier_ratio(tables: dict, reference, tier, inv_type: int) -> float | None:
    """budget(tier) / budget(reference), rounded; None when a reference row is missing."""
    low = stat_budget(tables, reference.ilvl, reference.quality, inv_type)
    high = stat_budget(tables, tier.ilvl, tier.quality, inv_type)
    if not low or high is None:
        return None
    return round(high / low, RATIO_DIGITS)


def reference_tier(item):
    """The item's resolved tier that keeps the declared spells: its ladder's `effect_reference` tier, else its first;
    None when the ladder names a tier the item does not have."""
    name = getattr(item.decl.ladder, "effect_reference", None)
    if not name:
        return item.tiers[0]
    return next((t for t in item.tiers if t.tier == name), None)


# ---------------------------------------------------------------------------------------------------------------------
# Families


def _resolved(effect_entry: dict | None) -> tuple[_potency.ResolvedPotency, float] | None:
    """The effect's ResolvedPotency (the `_potency` stash `Spell.to_entry()` leaves on it) and its tick count."""
    pot = dict((effect_entry or {}).get("_potency") or {})
    if not pot:
        return None
    ticks = pot.pop("ticks", 1.0)
    pot.pop("spell_level", None)
    return _potency.ResolvedPotency(**pot), ticks


def tooltip_expressions(entry: dict) -> dict[int, list[str]]:
    """Per effect index, every tooltip expression a `{potN}` / `pot_text(...)` of this spell can contain (the
    minimum, the maximum, the average and the periodic total), in a fixed order, so a base spell's list lines up
    with its copy's."""
    out = {}
    for index in (1, 2, 3):
        got = _resolved(entry.get(f"effect{index}"))
        if got is None:
            continue
        resolved, ticks = got
        avg = 1.0 + (resolved.variance_pct / 200.0 if resolved.variance_pct else 0.0)
        high = 1.0 + resolved.variance_pct / 100.0
        out[index] = [
            _potency.tooltip_expression(resolved),
            _potency.tooltip_expression(resolved, scale=high),
            _potency.tooltip_expression(resolved, scale=avg),
            _potency.tooltip_expression(resolved, ticks=ticks),
        ]
    return out


def _expression_re(expressions) -> re.Pattern | None:
    unique = sorted(set(expressions), key=len, reverse=True)
    if not unique:
        return None
    return re.compile(r"\$\{(" + "|".join(re.escape(e) for e in unique) + r")(?=[}*])")


def _texts(spell) -> dict[str, str]:
    raw = spell.raw_overrides or {}
    return {k: raw[k] for k in TEXT_KEYS if isinstance(raw.get(k), str)}


def _direct_refs(spell, linked: dict[int, set[int]]) -> set[int]:
    refs = set()
    for effect in spell.effects:
        if effect is not None and effect.trigger_spell:
            refs.add(int(effect.trigger_spell))
    raw = spell.raw_overrides or {}
    for n in (1, 2, 3):
        if raw.get(f"EffectTriggerSpell_{n}"):
            refs.add(int(raw[f"EffectTriggerSpell_{n}"]))
    for text in _texts(spell).values():
        refs.update(int(m) for m in _ID_TOKEN_RE.findall(text))
    refs.update(linked.get(int(spell.id), ()))
    return refs


@dataclass
class SpellIndex:
    """The source/items spells a family may reach: Spell objects, entries, and which spell each tooltip expression
    belongs to."""

    spells: dict[int, object] = field(default_factory=dict)
    entries: dict[int, dict] = field(default_factory=dict)
    expression_owner: dict[str, set[int]] = field(default_factory=dict)
    linked: dict[int, set[int]] = field(default_factory=dict)

    @classmethod
    def build(cls, dsl_classes: dict) -> SpellIndex:
        index = cls()
        for entry in dsl_classes["spells"]:
            spell = entry.get("_spell")
            if spell is None or entry.get("_source_class") != SOURCE_CLASS or entry.get("_item_copy_of"):
                continue
            index.spells[int(entry["id"])] = spell
            index.entries[int(entry["id"])] = entry
            for expressions in tooltip_expressions(entry).values():
                for expression in expressions:
                    index.expression_owner.setdefault(expression, set()).add(int(entry["id"]))
        for row in dsl_classes.get("linked_spells", []):
            index.linked.setdefault(abs(int(row["spell_trigger"])), set()).add(abs(int(row["spell_effect"])))
        return index

    def refs(self, spell_id: int) -> set[int]:
        spell = self.spells[spell_id]
        refs = _direct_refs(spell, self.linked)
        # pot_text() calls the registry recorded for this spell's texts name their spell exactly; only text they do not
        # cover falls back to matching tooltip expressions (equal potency, equal expression: ambiguous).
        recorded = self.entries[spell_id].get("_pot_text_refs") or ()
        refs.update(int(source) for _, source in recorded)
        pattern = _expression_re(self.expression_owner)
        if pattern is not None:
            for text in _texts(spell).values():
                for snippet, _ in recorded:
                    text = text.replace(snippet, "")
                for m in pattern.finditer(text):
                    refs.update(self.expression_owner[m.group(1)])
        refs.discard(spell_id)
        return {r for r in refs if r in self.spells}

    def family(self, root: int) -> list[int]:
        """`root` and every source/items spell it reaches, sorted."""
        seen, todo = {root}, [root]
        while todo:
            for ref in sorted(self.refs(todo.pop())):
                if ref not in seen:
                    seen.add(ref)
                    todo.append(ref)
        return sorted(seen)


def family_problems(index: SpellIndex, family: list[int], dsl_classes: dict, where: str) -> list[str]:
    problems = []
    family_set = set(family)
    for spell_id in family:
        spell = index.spells[spell_id]
        for n, effect in enumerate(spell.effects, 1):
            if effect is None:
                continue
            if effect.weapon_potency is not None:
                problems.append(f"{where}: spell {spell_id} effect {n} is a weapon_potency strike; scale=\"budget\" "
                                f"scales spell and attack power potency only")
                continue
            damage = int(effect.type) in DAMAGE_HEAL_EFFECTS or (
                int(effect.type) in APPLY_AURA_EFFECTS and int(effect.apply_aura) in DAMAGE_HEAL_AURAS)
            if damage and not effect.has_potency and not effect.potency_excluded:
                problems.append(f"{where}: spell {spell_id} effect {n} deals damage or heals without potency, so "
                                f"scale=\"budget\" cannot scale it (declare sp_potency / ap_potency)")
    for row in dsl_classes["spell_bonus_data"]:
        if int(row["entry"]) not in family_set:
            continue
        generated = index.spells[int(row["entry"])].potency_bonus_row or {}
        if not generated or any(row.get(k) != v for k, v in generated.items()):
            problems.append(f"{where}: spell {row['entry']} has a hand bonus_coefficients() row, which a per-tier "
                            f"copy cannot scale; use potency")
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# Copies


def _scaled_amount(effect, ratio: float) -> dict:
    """A stat aura's new `base_points` / `die_sides` (the amount is BasePoints + 1..DieSides), or {} to keep it."""
    if (int(effect.type) not in APPLY_AURA_EFFECTS or int(effect.apply_aura) not in STAT_AURAS or effect.has_potency
            or effect.potency_excluded):
        return {}
    offset = 1 if effect.die_sides >= 1 else 0
    low = effect.base_points + offset
    changes = {"base_points": int(round(low * ratio)) - offset}
    if effect.die_sides > 1:
        changes["die_sides"] = max(1, int(round(effect.die_sides * ratio)))
    return {k: v for k, v in changes.items() if v != getattr(effect, k)}


def _scaled_effect(effect, ratio: float, remap: dict[int, int]):
    if effect is None:
        return None
    changes = {}
    for name in SCALED_FIELDS:
        value = getattr(effect, name)
        if value:
            changes[name] = value * ratio
    changes.update(_scaled_amount(effect, ratio))
    if effect.trigger_spell and int(effect.trigger_spell) in remap:
        changes["trigger_spell"] = remap[int(effect.trigger_spell)]
    return dataclasses.replace(effect, **changes) if changes else effect


def _remap_text(text: str, remap: dict[int, int], expressions: dict[str, str]) -> str:
    text = _ID_TOKEN_RE.sub(lambda m: f"${remap.get(int(m.group(1)), int(m.group(1)))}", text)
    pattern = _expression_re(expressions)
    if pattern is not None:
        text = pattern.sub(lambda m: "${" + expressions[m.group(1)], text)
    return text


def build_copies(index: SpellIndex, family: list[int], remap: dict[int, int], ratio: float, note: str) -> dict:
    """The copies of `family` (base id -> copy Spell), `remap` base id -> copy id. Two passes: the scaled effects
    first (their tooltip expressions are what the texts point at), then the texts."""
    copies = {}
    for base in family:
        spell = index.spells[base]
        copies[base] = dataclasses.replace(
            spell, id=remap[base], effects=[_scaled_effect(e, ratio, remap) for e in spell.effects],
        )
    expressions: dict[str, str] = {}
    for base, copy in copies.items():
        base_expr = tooltip_expressions(index.entries[base])
        copy_expr = tooltip_expressions(copy.to_entry())
        for n, exprs in base_expr.items():
            expressions.update(zip(exprs, copy_expr.get(n, exprs)))
    for base, copy in copies.items():
        raw = dict(copy.raw_overrides or {})
        for key in TEXT_KEYS:
            if isinstance(raw.get(key), str):
                raw[key] = _remap_text(raw[key], remap, expressions)
        for n in (1, 2, 3):
            trigger = raw.get(f"EffectTriggerSpell_{n}")
            if trigger and int(trigger) in remap:
                raw[f"EffectTriggerSpell_{n}"] = remap[int(trigger)]
        notes = f"{note}: copy of {base} ({copy.name}), damage and healing potency and stat aura amounts x {ratio:g}."
        if copy.notes:
            notes += f" Base notes: {copy.notes}"
        copies[base] = dataclasses.replace(copy, raw_overrides=raw or None, notes=notes)
    return copies


@dataclass
class TierCopies:
    key: str
    tier: str
    entry: int  # the item tier's item_template entry
    ratio: float
    remap: dict[int, int]  # base spell id -> copy id


@dataclass
class SpellCopyExpansion:
    tiers: list[TierCopies] = field(default_factory=list)
    spells: list[dict] = field(default_factory=list)  # spell entries of the copies
    spell_bonus_data: list[dict] = field(default_factory=list)
    potency_corrections: list[dict] = field(default_factory=list)
    spell_procs: list[dict] = field(default_factory=list)
    spell_script_names: list[dict] = field(default_factory=list)
    custom_attrs: list[dict] = field(default_factory=list)
    linked_spells: list[dict] = field(default_factory=list)
    lock_appended: list[str] = field(default_factory=list)
    lock_text: str = ""
    header_text: str = ""
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def copy_ids(self) -> list[int]:
        return sorted(c for t in self.tiers for c in t.remap.values())

    def apply(self, dsl_classes: dict, spell_entries: list[dict] | None = None) -> None:
        """Adds the copies to the run's declarations (and to `spell_entries`, the merged spell list generate.py
        builds Spell.dbc from, which already holds the DSL spells)."""
        dsl_classes["spells"].extend(self.spells)
        if spell_entries is not None and spell_entries is not dsl_classes["spells"]:
            spell_entries.extend(self.spells)
        for key in ("spell_bonus_data", "potency_corrections", "spell_procs", "spell_script_names", "custom_attrs",
                    "linked_spells"):
            dsl_classes[key].extend(getattr(self, key))


def _copy_rows(rows: list[dict], key_field: str, base: int, copy: int, make_id) -> list[dict]:
    out = []
    for row in rows:
        if int(row[key_field]) == base:
            new = {k: v for k, v in row.items() if k != "_source_class"}
            new[key_field] = copy
            new["id"] = make_id(new)
            new["_source_class"] = SOURCE_CLASS
            out.append(new)
    return out


def expand(
    item_expansion, dsl_classes: dict, ids_cfg: dict, *, lock: Lock | None = None, lock_path: Path | None = None,
    taken_loader=None, today: str | None = None,
) -> SpellCopyExpansion:
    """The copies every `scale=` item spell needs (see the module docstring). `taken_loader` gives the live
    `spell_dbc` ids a new id must skip (called only when an id is minted). Never raises for a content problem."""
    out = SpellCopyExpansion()
    block = reservation(ids_cfg)
    try:
        lock = load_lock(lock_path or LOCK_PATH, block) if lock is None else parse_lock(lock.text, block)
    except LockError as error:
        out.errors.append(f"items: {error}")
        return out
    out.lock_text = lock.text
    scaled_items = [item for item in item_expansion.items
                    if any(s.scale for s in (item.decl.spells or ()))]
    if not scaled_items and not lock.lines:
        out.header_text = render_header([])
        return out
    if block is None:
        out.errors.append(f"items: source/ids.yaml has no {LOCK_BLOCK} block - item spell copies are minted from it")
        return out
    index = SpellIndex.build(dsl_classes)
    tables = item_expansion.tables or {}

    # (key, tier, base) -> what it needs, in declaration order: items, tiers, family ids.
    wanted: list[tuple[str, str, int]] = []
    plans = []
    for item in scaled_items:
        decl = item.decl
        if len(item.tiers) < 2:
            continue
        reference = reference_tier(item)
        if reference is None:
            out.errors.append(f"{decl.where}: ladder {decl.ladder.name!r} scales effects against its "
                              f"{decl.ladder.effect_reference!r} tier, which this item does not have")
            continue
        families: dict[int, list[int]] = {}
        for item_spell in decl.spells:
            if not item_spell.scale:
                continue
            where = f"{decl.where} spell {item_spell.spell_id}"
            if item_spell.spell_id not in index.spells:
                out.errors.append(f"{where}: scale=\"budget\" needs the spell declared in source/items/")
                continue
            family = index.family(item_spell.spell_id)
            out.errors += family_problems(index, family, dsl_classes, where)
            families[item_spell.spell_id] = family
        members = sorted({s for family in families.values() for s in family})
        for tier in item.tiers:
            if tier is reference:
                continue
            ratio = tier_ratio(tables, reference, tier, item.inventory_type)
            if ratio is None:
                out.errors.append(f"{decl.where} tier {tier.tier!r}: no stat budget for ilvl {tier.ilvl} / quality "
                                  f"{tier.quality} (or the reference tier's), so its spells cannot be scaled")
                continue
            plans.append((item, tier, ratio, members))
            wanted += [(decl.key, tier.tier, base) for base in members]

    # Ids.
    by_triple = lock.by_triple
    declared = {int(e["id"]) for e in dsl_classes["spells"]}
    in_lock = {line.spell_id for line in lock.lines}
    next_id = max([block["start"] - 1, *in_lock]) + 1
    taken: set[int] | None = None
    ids: dict[tuple[str, str, int], int] = {}
    full = False
    for triple in wanted:
        line = by_triple.get(triple)
        if line is not None:
            if line.retired:
                out.errors.append(f"items: {triple[0]} {triple[1]} spell {triple[2]}: its copy {line.spell_id} was "
                                  f"retired on {line.retired} ({LOCK_PATH.name} line {line.number}); a retired id is "
                                  f"never reused - give the item a new key")
                continue
            ids[triple] = line.spell_id
            continue
        if taken is None:
            taken = declared | in_lock | set(int(i) for i in (taken_loader() if taken_loader else ()))
        while next_id in taken or next_id in ids.values():
            next_id += 1
        if next_id > block["end"]:
            if not full:
                out.errors.append(f"items: source/ids.yaml's {LOCK_BLOCK} block "
                                  f"({block['start']}-{block['end']}) is full; widen it")
                full = True
            continue
        ids[triple] = next_id
        out.lock_appended.append(f"{next_id} {triple[0]} {triple[1]} {triple[2]}")
        next_id += 1
    wanted_set = set(wanted)
    for line in lock.lines:
        if line.triple in wanted_set or line.retired:
            continue
        stamp = today or datetime.date.today().isoformat()
        out.errors.append(
            f"items: {line.key} {line.tier} copy {line.spell_id} of spell {line.base} ({LOCK_PATH.name} line "
            f"{line.number}) is no longer wanted; a spell id is never reused. Declare it again, or retire it by "
            f"replacing the line with `{line.spell_id} {line.key} {line.tier} {line.base} retired {stamp}`"
        )
    if out.errors:
        return out

    # Rows.
    for item, tier, ratio, members in plans:
        decl = item.decl
        remap = {base: ids[(decl.key, tier.tier, base)] for base in members}
        note = f"Item variants IV10, {decl.key} tier {tier.tier} (ilvl {tier.ilvl})"
        copies = build_copies(index, members, remap, ratio, note)
        for base, copy in copies.items():
            try:
                entry = copy.to_entry()
            except ValueError as error:
                out.errors.append(f"{decl.where} tier {tier.tier!r}: copy {copy.id} of spell {base}: {error}")
                continue
            entry.update(_spell=copy, _source_class=SOURCE_CLASS, _item_copy_of=base)
            out.spells.append(entry)
            if copy.potency_bonus_row is not None:
                out.spell_bonus_data.append({**copy.potency_bonus_row, "_source_class": SOURCE_CLASS})
            out.potency_corrections += [{**r, "_source_class": SOURCE_CLASS} for r in copy.potency_correction_rows]
            c = remap[base]
            out.spell_procs += _copy_rows(dsl_classes["spell_procs"], "SpellId", base, c, lambda r: r["SpellId"])
            out.spell_script_names += _copy_rows(dsl_classes["spell_script_names"], "spell_id", base, c,
                                                 lambda r: f"{r['spell_id']}:{r['ScriptName']}")
            out.custom_attrs += _copy_rows(dsl_classes["custom_attrs"], "spell_id", base, c, lambda r: r["spell_id"])
        for row in dsl_classes["linked_spells"]:
            trigger, effect = int(row["spell_trigger"]), int(row["spell_effect"])
            if abs(trigger) not in remap:
                continue
            new_trigger = remap[abs(trigger)] * (1 if trigger >= 0 else -1)
            new_effect = remap.get(abs(effect), abs(effect)) * (1 if effect >= 0 else -1)
            out.linked_spells.append({
                **{k: v for k, v in row.items() if k != "_source_class"}, "spell_trigger": new_trigger,
                "spell_effect": new_effect, "id": f"{new_trigger}:{new_effect}:{row['type']}",
                "comment": f"{row.get('comment') or ''} (item tier copy)".strip(), "_source_class": SOURCE_CLASS,
            })
        tier.spells = tuple(
            s.with_spell_id(remap[s.spell_id]) if s.scale and s.spell_id in remap else s for s in decl.spells
        )
        out.tiers.append(TierCopies(decl.key, tier.tier, tier.entry, ratio, remap))
    if out.errors:
        return out
    out.lock_text = lock_text(lock, out.lock_appended)
    out.header_text = render_header(out.tiers)
    if out.tiers:
        out.notes.append(
            f"items: {len(out.spells)} item effect spell copies on {len(out.tiers)} item tier(s) "
            f"(ratios: " + ", ".join(sorted({f'{t.ratio:g}' for t in out.tiers}, key=float)) + ")"
        )
    if out.lock_appended:
        out.notes.append(f"items: {len(out.lock_appended)} new item spell copy id(s) for {LOCK_PATH.name} (a full run "
                         f"appends them; commit the file)")
    return out


def summary_notes(expansion: SpellCopyExpansion, check: bool) -> list[str]:
    notes = list(expansion.notes)
    if check:
        notes += [f"items: would append to {LOCK_PATH.name}: {line}" for line in expansion.lock_appended]
    return notes


# ---------------------------------------------------------------------------------------------------------------------
# The C++ header


def render_header(tiers: list[TierCopies]) -> str:
    """`ItemSpellCopies.h`: one `{copy, base, group}` row per copy, `group` the smallest copy id of its (item, tier),
    sorted by copy id, and the constexpr lookups the scripts use."""
    rows = []
    for t in tiers:
        group = min(t.remap.values())
        rows += [(copy, base, group, f"{t.key} {t.tier}") for base, copy in t.remap.items()]
    rows.sort()
    lines = [
        "/*",
        " * Generated by apps/dbc-tools/generate.py (lib/item_spell_copies.py) from source/items/item_spell_ids.lock -",
        " * DO NOT hand-edit. Item variants IV10: every tier but the ladder's effect reference tier carries its own",
        " * copy of each scale=\"budget\" effect spell and of every spell it reaches. A script bound to a copy casts its",
        " * own tier's copies: Resolve(the id of the spell being cast or the aura, the base id it would cast).",
        " *",
        " * Pure (no engine headers), so host tests can include it.",
        " */",
        "",
        "#ifndef MOD_DUNGEON_BOSSES_ITEM_SPELL_COPIES_H",
        "#define MOD_DUNGEON_BOSSES_ITEM_SPELL_COPIES_H",
        "",
        "#include <cstddef>",
        "#include <cstdint>",
        "",
        "namespace ItemSpellCopies",
        "{",
        "    struct Copy",
        "    {",
        "        std::uint32_t copy;     // the copy's spell id",
        "        std::uint32_t base;     // the declared spell it copies",
        "        std::uint32_t group;    // the smallest copy id of its item tier (one group = one item tier)",
        "    };",
        "",
    ]
    if rows:
        lines.append("    inline constexpr Copy kCopies[] =")
        lines.append("    {")
        for copy, base, group, what in rows:
            lines.append(f"        {{ {copy}, {base}, {group} }},  // {what}")
        lines.append("    };")
        lines.append(f"    inline constexpr std::size_t kCopyCount = {len(rows)};")
    else:
        lines.append("    inline constexpr Copy kCopies[] = { { 0, 0, 0 } };  // no copies (a placeholder row)")
        lines.append("    inline constexpr std::size_t kCopyCount = 0;")
    lines += [
        "",
        "    // The group of `spellId` when it is a copy, else 0.",
        "    constexpr std::uint32_t GroupOf(std::uint32_t spellId)",
        "    {",
        "        for (std::size_t i = 0; i < kCopyCount; ++i)",
        "            if (kCopies[i].copy == spellId)",
        "                return kCopies[i].group;",
        "        return 0;",
        "    }",
        "",
        "    // The spell to cast for `baseId` from `castId` (the spell or aura the script runs for): the copy of",
        "    // `baseId` in castId's item tier, else `baseId` itself (castId is a base spell, or `baseId` has no copy",
        "    // in that tier).",
        "    constexpr std::uint32_t Resolve(std::uint32_t castId, std::uint32_t baseId)",
        "    {",
        "        std::uint32_t const group = GroupOf(castId);",
        "        if (!group)",
        "            return baseId;",
        "        for (std::size_t i = 0; i < kCopyCount; ++i)",
        "            if (kCopies[i].group == group && kCopies[i].base == baseId)",
        "                return kCopies[i].copy;",
        "        return baseId;",
        "    }",
        "}",
        "",
        "#endif",
        "",
    ]
    return "\n".join(lines)


def header_problem(text: str, path: Path = HEADER_PATH) -> str | None:
    on_disk = path.read_text(encoding="utf-8") if path.is_file() else None
    if on_disk == text:
        return None
    if on_disk is None:
        return f"{path.relative_to(REPO_ROOT)} doesn't exist - run generate.py to create it"
    return f"{path.relative_to(REPO_ROOT)} is stale - run generate.py to regenerate it"


def write_header(text: str, path: Path = HEADER_PATH) -> bool:
    """Writes the header when it changed; True when it wrote."""
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True
