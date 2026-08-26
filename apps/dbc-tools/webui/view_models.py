"""Conversion between lib/source.py's entry dicts (the shape generate.py
consumes) and plain-string form field values (the shape Flask's request.form
gives us). Kept separate from app.py so the routing stays readable.

Nothing here talks to the filesystem — that's app.py's job, via lib/source.py.
"""

from __future__ import annotations

import gamedata
from lib.source import SPELL_CSV_FIELDNAMES, SPELL_CSV_FLOAT_FIELDS, SPELL_CSV_INT_FIELDS

# (value, label) pairs, sorted, for the <select> dropdowns in spell_form.html
# — see gamedata.py for where each of these actually comes from.
SCHOOL_OPTIONS = sorted(gamedata.SCHOOL_MASK_NAMES.items())
POWER_TYPE_OPTIONS = sorted(gamedata.POWER_TYPE_NAMES.items())


def effect_type_options() -> list[tuple[int, str]]:
    return sorted(gamedata.spell_effect_names().items())

# Order matches lib/reverse.py's per-effect dict construction (and therefore
# the key order already live in source/spells/*.csv, modulo json.dumps's
# alphabetical sort_keys=True on disk).
EFFECT_FIELDS = (
    "type", "base_points", "points_per_level", "die_sides", "mechanic",
    "implicit_target_a", "implicit_target_b", "apply_aura", "amplitude",
    "misc_value", "trigger_spell", "chain_targets", "radius_yards",
)
EFFECT_INT_FIELDS = {
    "type", "base_points", "die_sides", "mechanic", "implicit_target_a",
    "implicit_target_b", "apply_aura", "amplitude", "misc_value",
    "trigger_spell", "chain_targets",
}
EFFECT_FLOAT_FIELDS = {"points_per_level", "radius_yards"}

# "notes" gets its own <textarea> in the template rather than sitting in the
# generic plain-fields grid, so it's excluded here too.
SPELL_PLAIN_FIELDS = tuple(
    f for f in SPELL_CSV_FIELDNAMES
    if f not in ("effect1", "effect2", "effect3", "raw_overrides", "notes")
)


def _blank(s: str | None) -> bool:
    return s is None or s.strip() == ""


def parse_scalar(text: str):
    """Best-effort typed parse for one raw_overrides value: int, then float,
    then true/false/null, else the literal string. Matches the kinds of
    values raw_overrides actually holds (mostly ints/floats, a handful of
    text strings like a Description_Lang_enUS — some of those legitimately
    empty, e.g. "NameSubtext_Lang_enUS": "" — so a blank box means empty
    string, not null; type the literal word "null" for that."""
    text = text.strip()
    if text == "":
        return ""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null":
        return None
    return text


def format_scalar(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def overrides_to_pairs(raw_overrides: dict | None) -> list[tuple[str, str]]:
    if not raw_overrides:
        return []
    return [(k, format_scalar(v)) for k, v in raw_overrides.items()]


def overrides_from_form(keys: list[str], values: list[str]) -> dict | None:
    result = {}
    for key, value in zip(keys, values):
        key = key.strip()
        if not key:
            continue
        result[key] = parse_scalar(value)
    return result or None


def effect_to_form_values(effect: dict | None) -> dict[str, str]:
    if not effect:
        return {field: "" for field in EFFECT_FIELDS}
    return {field: format_scalar(effect.get(field)) for field in EFFECT_FIELDS}


def effect_from_form(form, prefix: str) -> dict | None:
    """Builds one effectN dict from `{prefix}_{field}` form inputs. An empty
    "type" field means "no effect in this slot" (every real effect has a
    type), matching how effect1-3 are already null in source/spells/*.csv for
    unused slots."""
    type_value = (form.get(f"{prefix}_type") or "").strip()
    if type_value == "":
        return None
    effect = {}
    for field in EFFECT_FIELDS:
        raw = (form.get(f"{prefix}_{field}") or "").strip()
        if raw == "":
            effect[field] = None
            continue
        if field in EFFECT_INT_FIELDS:
            effect[field] = int(raw)
        elif field in EFFECT_FLOAT_FIELDS:
            effect[field] = float(raw)
        else:
            effect[field] = raw
    return effect


def spell_entry_to_form_context(entry: dict) -> dict:
    ctx = {field: format_scalar(entry.get(field)) for field in SPELL_PLAIN_FIELDS}
    ctx["notes"] = entry.get("notes") or ""
    for i in (1, 2, 3):
        ctx[f"effect{i}"] = effect_to_form_values(entry.get(f"effect{i}"))
    ctx["overrides"] = overrides_to_pairs(entry.get("raw_overrides"))
    return ctx


def spell_entry_from_form(form) -> dict:
    entry = {}
    for field in SPELL_PLAIN_FIELDS:
        raw = (form.get(field) or "").strip()
        if field == "id":
            entry[field] = int(raw)  # required, let a blank/bad id raise
        elif field == "name":
            entry[field] = raw
        elif raw == "":
            entry[field] = None
        elif field in SPELL_CSV_INT_FIELDS:
            entry[field] = int(raw)
        elif field in SPELL_CSV_FLOAT_FIELDS:
            entry[field] = float(raw)
        else:
            entry[field] = raw
    entry["notes"] = (form.get("notes") or "").strip()
    for i in (1, 2, 3):
        entry[f"effect{i}"] = effect_from_form(form, f"effect{i}")
    entry["raw_overrides"] = overrides_from_form(
        form.getlist("override_key"), form.getlist("override_value"),
    )
    return entry


# -- talents --------------------------------------------------------------

TAB_FIELDS = ("id", "name", "class_mask", "pet_talent_mask", "order_index", "spell_icon_id")

ABILITY_FIELDS = ("id", "skill_line", "spell_id", "class_mask", "min_skill_line_rank")


def tab_entry_to_form_context(entry: dict) -> dict:
    ctx = {field: format_scalar(entry.get(field)) for field in TAB_FIELDS}
    ctx["overrides"] = overrides_to_pairs(entry.get("raw_overrides"))
    return ctx


def tab_entry_from_form(form) -> dict:
    entry = {}
    for field in TAB_FIELDS:
        raw = (form.get(field) or "").strip()
        if field == "name":
            entry[field] = raw
        elif field == "id":
            entry[field] = int(raw)  # required, let a blank/bad id raise
        else:
            entry[field] = int(raw) if raw else 0
    entry["raw_overrides"] = overrides_from_form(
        form.getlist("override_key"), form.getlist("override_value"),
    )
    return entry


def talent_entry_to_form_context(entry: dict) -> dict:
    depends_on = entry.get("depends_on") or {"talent_id": 0, "rank": 0}
    return {
        "id": format_scalar(entry.get("id")),
        "tab_id": format_scalar(entry.get("tab_id")),
        "tier": format_scalar(entry.get("tier")),
        "column": format_scalar(entry.get("column")),
        "flags": format_scalar(entry.get("flags", 0)),
        "rank_spell_ids": [format_scalar(v) for v in entry.get("rank_spell_ids") or []],
        "depends_on_talent_id": format_scalar(depends_on.get("talent_id", 0)),
        "depends_on_rank": format_scalar(depends_on.get("rank", 0)),
    }


def talent_entry_from_form(form) -> dict:
    # Key order matches source/talents/mage.yaml's schema comment
    # (id/tab_id/tier/column/rank_spell_ids/depends_on/flags) so an edited
    # entry's field order stays consistent with every untouched sibling.
    entry = {field: int(form.get(field)) for field in ("id", "tab_id", "tier", "column")}
    entry["rank_spell_ids"] = [
        int(v) for v in form.getlist("rank_spell_id") if v.strip() != ""
    ]
    entry["depends_on"] = {
        "talent_id": int(form.get("depends_on_talent_id") or 0),
        "rank": int(form.get("depends_on_rank") or 0),
    }
    entry["flags"] = int(form.get("flags") or 0)
    return entry


def ability_entry_to_form_context(entry: dict) -> dict:
    return {field: format_scalar(entry.get(field)) for field in ABILITY_FIELDS}


def ability_entry_from_form(form) -> dict:
    return {field: int(form.get(field)) for field in ABILITY_FIELDS}
