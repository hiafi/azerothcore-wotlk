#!/usr/bin/env python3
"""
item-tools web editor - a small local Flask app for browsing and editing
`item_template`, the same table `data/sql/base/db_world/item_template.sql`
(plus every migration layered on top of it) already defines. Unlike
apps/dbc-tools, there's no separate source-file format and no client patch
to build: `item_template` rows are read live off disk (base dump + merged +
pending SQL, see lib/overlay.py) and a save writes a new guarded UPDATE (or,
for a new item, an upsert INSERT) straight into
data/sql/updates/pending_db_world/ - see apps/item-tools/README.md for the
full design rationale.

Single-user LAN tool: no auth, no live database connection, no JS build
step. Run with:
  python3 apps/item-tools/webui/app.py
and reach it from any machine on the same network at
http://<this machine's LAN IP>:8601/ - see the README before exposing this
beyond a trusted home network; there's no login, so anyone who can reach the
port can edit these files.
"""

from __future__ import annotations

import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from flask import Flask, abort, flash, redirect, render_template, request, url_for  # noqa: E402

from lib import budget, budget_emit, emit, ids, item_enums, loot, schema, shapes as shape_lib  # noqa: E402
from lib.budget_overlay import get_all as get_budget_tables  # noqa: E402
from lib.overlay import REPO_ROOT, get_rows  # noqa: E402

app = Flask(__name__)
app.secret_key = "item-tools-local-only"  # no auth, no cookies leave this machine's browser

MAX_SEARCH_RESULTS = 300

# (class id, subclass id, "Class: Subclass" label), sorted for the item
# form's subclass <select> - one flat list covering every class, filtered
# down client-side (webui/static/item-form.js) when the class field
# changes. See lib/item_enums.py for where these names come from.
SUBCLASS_OPTIONS = [
    (class_id, subclass_id, f"{item_enums.ITEM_CLASS_NAMES[class_id]}: {label}")
    for class_id, subclasses in sorted(item_enums.ITEM_SUBCLASS_NAMES.items())
    for subclass_id, label in sorted(subclasses.items())
]
# A handful of real item_template rows use a (class, subclass) combination
# outside lib/item_enums.py's per-class table (verified against this repo's
# actual data - e.g. some class-12 "Quest" items use subclass 3 or 8, which
# isn't one of the values ItemSubclassQuest defines). item_form.html adds a
# fallback option for those so the field renders "(unrecognized)" and stays
# selected, rather than silently snapping to whatever option happens to be
# first in the list - which would corrupt the row on any unrelated save.
SUBCLASS_PAIRS = {(class_id, subclass_id) for class_id, subclass_id, _ in SUBCLASS_OPTIONS}


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _coerce(raw: str, reference):
    """Parse a form field back to the same python type as `reference`
    (the column's current value, which is how types are known here - see
    lib/overlay.py's read_table_dump, which already turns unquoted numeric
    literals into int/float and quoted ones into str)."""
    raw = raw.strip()
    if isinstance(reference, float):
        return float(raw) if raw else 0.0
    if isinstance(reference, int):
        return int(raw) if raw else 0
    return raw


def _row_from_form(form, columns: list[str], reference_row: dict) -> dict:
    row = {}
    for col in columns:
        raw = form.get(col, "")
        row[col] = _coerce(raw, reference_row.get(col, ""))
    return row


def _form_enum_context() -> dict:
    """Kwargs shared by both item_form.html renders (new/edit) for its
    class/subclass/stat-type <select>s - see lib/item_enums.py."""
    return {
        "item_class_names": item_enums.ITEM_CLASS_NAMES,
        "subclass_options": SUBCLASS_OPTIONS,
        "subclass_pairs": SUBCLASS_PAIRS,
        "item_mod_names": item_enums.ITEM_MOD_NAMES,
        "item_mod_custom": item_enums.ITEM_MOD_CUSTOM,
        "item_mod_deprecated": item_enums.ITEM_MOD_DEPRECATED,
        "inventory_type_names": item_enums.INVENTORY_TYPE_NAMES,
    }


def _describe_changes(changes: dict, original: dict) -> str:
    parts = [f"{col} ({original.get(col)!r} -> {new!r})" for col, new in changes.items()]
    return "Changed columns: " + ", ".join(parts) + "."


# --- Shape-based itemization (docs/itemization-phase-2.md) ------------------

DEFAULT_ITEMIZATION_ROW = {
    "budget_mult": 1.0, "stamina_delta": 0, "dps_delta": 0.0, "absorbed_spell_slots": 0,
    "armor_delta": 0, "primary_shape_id": 0, "secondary_shape_id": 25, "primary_share": 0,
    "block_value_delta": 0,
}  # an item with no item_itemization row yet - null primary, "Crit (Solo)" secondary, 0% share


def _shape_display(shape_id: int, shape_catalog: dict[int, dict]) -> dict:
    """A shape's info shaped for the item form's read-only display next to
    its dropdown - name, distribution, stat/% breakdown, rule summary."""
    shape = shape_catalog.get(shape_id)
    if shape is None:
        return {"name": f"(unknown shape {shape_id})", "dist_name": "", "stats": [], "rules": ""}
    return {
        "name": shape["name"],
        "dist_name": shape["dist_name"],
        "stats": [
            {"stat_type": st, "name": item_enums.ITEM_MOD_NAMES.get(st, st), "pct": pct}
            for st, pct in shape_lib.stat_percentages(shape)
        ],
        "rules": shape_lib.rule_summary(shape, item_enums.ITEM_MOD_NAMES),
    }


def _itemization_form_context(entry: int, item_row: dict, tables: dict,
                                itemization_override: dict = None, breakdown: dict = None) -> dict:
    itemization_row = itemization_override if itemization_override is not None else tables["item_itemization"].get((entry,))
    shape_catalog = shape_lib.catalog(tables)
    row = itemization_row or DEFAULT_ITEMIZATION_ROW

    absorbed_mask = row["absorbed_spell_slots"]
    spell_slots = []
    for i in range(1, 6):
        spellid = item_row.get(f"spellid_{i}", 0)
        trigger = item_row.get(f"spelltrigger_{i}", 0)
        if spellid and trigger == 1:
            spell_slots.append({"index": i, "spellid": spellid, "absorbed": bool(absorbed_mask & (1 << (i - 1)))})

    primary_options = sorted(
        (s for s in shape_catalog.values() if s["kind"] == shape_lib.KIND_PRIMARY),
        key=lambda s: s["shape_id"],
    )
    # ALL secondary shapes render as <option>s (not pre-filtered to the current primary) so
    # item-form.js can hide/show them client-side when the primary <select> changes, the same
    # pattern filterSubclassOptions() already uses for class/subclass - every option has to exist
    # in the DOM up front for that toggle to work, since a shape newly eligible after switching
    # primaries has no other way to appear without a page reload. The server re-validates the
    # actual choice on save regardless (item_itemization_save), so a stale/JS-disabled selection
    # can't silently write an invalid combination.
    secondary_options = sorted(
        (s for s in shape_catalog.values() if s["kind"] == shape_lib.KIND_SECONDARY),
        key=lambda s: s["shape_id"],
    )
    secondary_rules = {}
    for s in secondary_options:
        requires_any, forbids = shape_lib.rule_stat_lists(s)
        secondary_rules[s["shape_id"]] = {"requires": requires_any, "forbids": forbids}

    return {
        "itemization_row": itemization_row,
        "itemization_fields": row,
        "shape_catalog": shape_catalog,
        "primary_options": primary_options,
        "secondary_options": secondary_options,
        "secondary_rules": secondary_rules,
        "primary_display": _shape_display(row["primary_shape_id"], shape_catalog),
        "secondary_display": _shape_display(row["secondary_shape_id"], shape_catalog),
        "itemization_spell_slots": spell_slots,
        "itemization_breakdown": breakdown,
        # item_mod_names comes from _form_enum_context(), always spread alongside this -
        # not repeated here to avoid a duplicate-kwarg TypeError at both call sites.
    }


@app.route("/shapes")
def shape_list():
    """Read-only browse of the fixed shape catalog - primary shapes (role-lock
    stats) and secondary shapes (universal stats), for reference while filling
    in an item's Itemization section. Not editable here: shapes are authored
    by hand-written regression-backed migrations, same as item_budget_curve -
    see lib/shapes.py's module docstring."""
    tables = get_budget_tables()
    catalog = shape_lib.catalog(tables)
    counts: dict[int, int] = {"primary": {}, "secondary": {}}
    for (_entry,), row in tables["item_itemization"].items():
        counts["primary"][row["primary_shape_id"]] = counts["primary"].get(row["primary_shape_id"], 0) + 1
        counts["secondary"][row["secondary_shape_id"]] = counts["secondary"].get(row["secondary_shape_id"], 0) + 1

    def _row(shape):
        sid = shape["shape_id"]
        kind = "primary" if shape["kind"] == shape_lib.KIND_PRIMARY else "secondary"
        return {
            "shape_id": sid,
            "name": shape["name"],
            "dist_name": shape["dist_name"],
            "stats": " / ".join(
                f"{item_enums.ITEM_MOD_NAMES.get(st, st)} {pct:.2f}%"
                for st, pct in shape_lib.stat_percentages(shape)
            ) or "(none)",
            "rules": shape_lib.rule_summary(shape, item_enums.ITEM_MOD_NAMES) or "(none)",
            "item_count": counts[kind].get(sid, 0),
        }

    primary_rows = [_row(s) for s in sorted(catalog.values(), key=lambda s: s["shape_id"]) if s["kind"] == shape_lib.KIND_PRIMARY]
    secondary_rows = [_row(s) for s in sorted(catalog.values(), key=lambda s: s["shape_id"]) if s["kind"] == shape_lib.KIND_SECONDARY]
    return render_template("shape_list.html", primary_rows=primary_rows, secondary_rows=secondary_rows)


@app.route("/items/<int:entry>/itemization", methods=["POST"])
def item_itemization_save(entry: int):
    items = get_rows()
    item_row = items.get(entry)
    if item_row is None:
        abort(404)
    tables = get_budget_tables()
    shape_catalog = shape_lib.catalog(tables)
    action = request.form.get("action", "save")

    def _f(name, cast, default):
        raw = request.form.get(name, "").strip()
        return cast(raw) if raw else default

    absorbed = 0
    for i in range(1, 6):
        if request.form.get(f"absorb_{i}"):
            absorbed |= 1 << (i - 1)

    primary_shape_id = _f("primary_shape_id", int, 0)
    secondary_shape_id = _f("secondary_shape_id", int, 25)

    primary_shape = shape_catalog.get(primary_shape_id)
    secondary_shape = shape_catalog.get(secondary_shape_id)
    if primary_shape is None or primary_shape["kind"] != shape_lib.KIND_PRIMARY:
        flash(f"{primary_shape_id} isn't a real primary shape - pick one from the list.", "error")
        return redirect(url_for("item_edit", entry=entry))
    if secondary_shape is None or secondary_shape["kind"] != shape_lib.KIND_SECONDARY:
        flash(f"{secondary_shape_id} isn't a real secondary shape - pick one from the list.", "error")
        return redirect(url_for("item_edit", entry=entry))
    if not shape_lib.rules_satisfied(secondary_shape, set(primary_shape["stats"])):
        flash(f"{secondary_shape['name']!r} isn't eligible for primary shape {primary_shape['name']!r} "
              f"({shape_lib.rule_summary(secondary_shape, item_enums.ITEM_MOD_NAMES)}) - pick a different one.",
              "error")
        return redirect(url_for("item_edit", entry=entry))

    itemization_fields = {
        "entry": entry,
        "budget_mult": _f("budget_mult", float, 1.0),
        "stamina_delta": _f("stamina_delta", int, 0),
        "dps_delta": _f("dps_delta", float, 0.0),
        "absorbed_spell_slots": absorbed,
        "armor_delta": _f("armor_delta", int, 0),
        "primary_shape_id": primary_shape_id,
        "secondary_shape_id": secondary_shape_id,
        "primary_share": _f("primary_share", int, 0),
        "block_value_delta": _f("block_value_delta", int, 0),
    }

    try:
        breakdown = budget.compute_breakdown(item_row, itemization_fields, tables, shape_catalog)
    except budget.BudgetError as e:
        flash(f"Can't compute this item's budget: {e}", "error")
        return redirect(url_for("item_edit", entry=entry))

    if action == "preview":
        return render_template(
            "item_form.html", entry=entry, row=item_row, sections=schema.sections(),
            is_new=False, custom_range=ids.item_range(), **_form_enum_context(),
            **_itemization_form_context(entry, item_row, tables, itemization_fields, breakdown),
        )

    note = request.form.get("note", "").strip()
    if not note:
        flash("A change note is required (it becomes the pending SQL file's comment).", "error")
        return redirect(url_for("item_edit", entry=entry))

    changes = budget.materialized_item_fields(breakdown)
    changes.update(budget.absorb_spell_fields(absorbed))
    item_changes = emit.diff_row(item_row, changes)

    name = item_row.get("name") or f"entry {entry}"
    comment = (f"item-tools: {name!r} ({entry}) itemization -> primary {primary_shape['name']!r} "
               f"/ secondary {secondary_shape['name']!r}. {note}")
    path = budget_emit.write_itemization_and_regenerate(entry, itemization_fields, item_changes, item_row, comment)
    get_budget_tables(force=True)
    get_rows(force=True)
    flash(f"Wrote {_display_path(path)}. Run .reload item_template in-game (or restart worldserver) to see it live.",
          "success")
    return redirect(url_for("item_edit", entry=entry))


@app.route("/")
def index():
    rows = get_rows()
    custom_range = ids.item_range()
    custom_entries = sorted(
        e for e in rows if custom_range["start"] <= e <= custom_range["end"]
    )
    return render_template(
        "index.html",
        total=len(rows),
        custom_entries=[rows[e] for e in custom_entries],
        custom_range=custom_range,
    )


@app.route("/items")
def item_list():
    q = request.args.get("q", "").strip()
    rows = get_rows()
    results = []
    if q:
        q_lower = q.lower()
        q_int = int(q) if q.isdigit() else None
        for row in rows.values():
            if q_int is not None and row["entry"] == q_int:
                results.append(row)
                continue
            if q_lower in row["name"].lower():
                results.append(row)
        results.sort(key=lambda r: (r["entry"] != q_int, r["name"]))
    truncated = len(results) > MAX_SEARCH_RESULTS
    return render_template(
        "item_list.html",
        q=q,
        results=results[:MAX_SEARCH_RESULTS],
        truncated=truncated,
        total_matches=len(results),
        columns=schema.LIST_COLUMNS,
        item_subclass_names=item_enums.ITEM_SUBCLASS_NAMES,
        weapon_armor_classes=item_enums.WEAPON_ARMOR_CLASSES,
    )


@app.route("/items/new", methods=["GET", "POST"])
def item_new():
    rows = get_rows()
    columns = [c for _, cols in schema.sections() for c in cols]
    sample = next(iter(rows.values()))

    if request.method == "POST":
        try:
            entry = int(request.form["entry"])
        except (KeyError, ValueError):
            flash("Entry must be a number.", "error")
            return redirect(url_for("item_new"))
        if entry in rows:
            flash(f"Entry {entry} already exists - edit it instead of creating it.", "error")
            return redirect(url_for("item_edit", entry=entry))
        note = request.form.get("note", "").strip()
        if not note:
            flash("A change note is required (it becomes the pending SQL file's comment).", "error")
            return redirect(url_for("item_new"))
        row = _row_from_form(request.form, columns, sample)
        row["entry"] = entry
        name = row.get("name") or f"entry {entry}"
        comment = f"item-tools: new item {name!r} (entry {entry}). {note}"
        path = emit.write_insert(entry, row, comment)
        get_rows(force=True)
        flash(f"Wrote {_display_path(path)}.", "success")
        return redirect(url_for("item_edit", entry=entry))

    blank = {col: ("" if isinstance(sample.get(col), str) else 0) for col in columns}
    blank["entry"] = ids.suggest_new_id(rows.keys())
    return render_template(
        "item_form.html",
        entry=None,
        row=blank,
        sections=schema.sections(),
        is_new=True,
        custom_range=ids.item_range(),
        **_form_enum_context(),
    )


@app.route("/items/<int:entry>", methods=["GET", "POST"])
def item_edit(entry: int):
    rows = get_rows()
    original = rows.get(entry)
    if original is None:
        abort(404)
    columns = [c for _, cols in schema.sections() for c in cols]

    if request.method == "POST":
        edited = _row_from_form(request.form, columns, original)
        changes = emit.diff_row(original, edited)
        changes.pop("entry", None)
        if not changes:
            flash("No changes to save.", "success")
            return redirect(url_for("item_edit", entry=entry))
        note = request.form.get("note", "").strip()
        if not note:
            flash("A change note is required (it becomes the pending SQL file's comment).", "error")
            return redirect(url_for("item_edit", entry=entry))
        name = original.get("name") or f"entry {entry}"
        comment = f"item-tools: {name!r} ({entry}). {note} {_describe_changes(changes, original)}"
        path = emit.write_update(entry, changes, original, comment)
        get_rows(force=True)
        flash(f"Wrote {_display_path(path)} ({len(changes)} column(s) changed). "
              "Run .reload item_template in-game (or restart worldserver) to see it live.",
              "success")
        return redirect(url_for("item_edit", entry=entry))

    return render_template(
        "item_form.html",
        entry=entry,
        row=original,
        sections=schema.sections(),
        is_new=False,
        custom_range=ids.item_range(),
        **_form_enum_context(),
        **_itemization_form_context(entry, original, get_budget_tables()),
    )


DEFAULT_MIN_QUALITY = 2  # Uncommon (green) and up - see lib/loot.QUALITY_NAMES


@app.route("/dungeons")
def dungeon_list():
    min_quality = request.args.get("min_quality", DEFAULT_MIN_QUALITY, type=int)
    maps = loot.dungeon_maps()
    rows = []
    for map_id, name in sorted(maps.items(), key=lambda kv: kv[1]):
        summary = loot.dungeon_summary(map_id, min_quality=min_quality)
        trash_creatures = {c for item in summary["trash"] for c in item["creatures"]}
        rows.append({
            "map_id": map_id, "name": name,
            "creature_count": len(summary["bosses"]) + len(trash_creatures),
            "item_count": sum(len(b["drops"]) for b in summary["bosses"]) + len(summary["trash"]),
        })
    rows.sort(key=lambda r: (-r["item_count"], r["name"]))
    return render_template(
        "dungeon_list.html", rows=rows, min_quality=min_quality,
        quality_names=loot.QUALITY_NAMES,
    )


@app.route("/dungeons/<int:map_id>")
def dungeon_detail(map_id: int):
    maps = loot.dungeon_maps()
    if map_id not in maps:
        abort(404)
    min_quality = request.args.get("min_quality", DEFAULT_MIN_QUALITY, type=int)
    summary = loot.dungeon_summary(map_id, min_quality=min_quality)
    return render_template(
        "dungeon_detail.html",
        map_id=map_id, name=maps[map_id], summary=summary, min_quality=min_quality,
        quality_names=loot.QUALITY_NAMES, rank_name=loot.rank_name,
        quality_name=loot.quality_name, summarize_stats=loot.summarize_stats,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8601, debug=False)
