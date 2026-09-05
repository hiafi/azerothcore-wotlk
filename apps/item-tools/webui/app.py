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

from lib import budget, budget_emit, emit, ids, item_enums, loot, schema  # noqa: E402
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


# --- Budget templates (docs/itemization-changes.md §9.8) --------------------

def _template_ids(tables: dict) -> set[int]:
    return {tid for (tid, _st) in tables["item_budget_template"]} | {
        tid for (tid,) in tables["item_budget_template_name"]
    }


def _template_stats(template_id: int, tables: dict) -> list[dict]:
    return sorted(
        (row for (tid, _st), row in tables["item_budget_template"].items() if tid == template_id),
        key=lambda r: -r["alloc"],
    )


def _template_shape_summary(template_id: int, tables: dict) -> str:
    stats = _template_stats(template_id, tables)
    if not stats:
        return "(empty)"
    return " / ".join(
        f"{item_enums.ITEM_MOD_NAMES.get(s['stat_type'], s['stat_type'])} {s['alloc'] / 100:.1f}%"
        for s in stats
    )


def _percentages_to_alloc(raw: list[tuple[int, float]]) -> list[dict]:
    """`raw` is `(stat_type, percent)` pairs already validated to sum to
    ~100% - largest-remainder rounds each to ten-thousandths so the result
    sums to exactly 10000, same method used to hand-build this session's own
    templates (see docs/itemization-changes.md §4.5's rounding, Appendix A)."""
    exact = [(st, pct * 100.0) for st, pct in raw]
    floors = [(st, int(v), v - int(v)) for st, v in exact]
    floor_sum = sum(f for _, f, _ in floors)
    remainder = 10000 - floor_sum
    order = sorted(range(len(floors)), key=lambda i: -floors[i][2])
    allocs = [f for _, f, _ in floors]
    for i in order[:remainder]:
        allocs[i] += 1
    return [{"stat_type": st, "alloc": allocs[i]} for i, (st, _, _) in enumerate(floors)]


def _template_item_count(template_id: int, tables: dict) -> int:
    return sum(1 for (_e,), row in tables["item_budget_assign"].items() if row["template_id"] == template_id)


def _parse_percentage_stats(form) -> tuple[list[dict] | None, str | None]:
    """Reads paired `stat_type`/`alloc_pct` fields (however many rows the
    form submitted - both the standalone template form and the item page's
    inline shape editor use this same field-name pair), merges duplicate
    stat types, and validates the total is ~100%. Returns
    `(stats, None)` on success or `(None, error message)` - never raises,
    so both callers can just flash the message and redirect."""
    raw: dict[int, float] = {}
    for st_raw, pct_raw in zip(form.getlist("stat_type"), form.getlist("alloc_pct")):
        pct_raw = pct_raw.strip()
        if not st_raw or not pct_raw:
            continue
        st = int(st_raw)
        raw[st] = raw.get(st, 0.0) + float(pct_raw)

    if not raw:
        return None, "Add at least one stat."

    total_pct = sum(raw.values())
    if abs(total_pct - 100.0) > 0.1:
        return None, f"Percentages sum to {total_pct:.2f}%, not 100% - fix before saving."

    return _percentages_to_alloc(sorted(raw.items())), None


def _budget_form_context(entry: int, item_row: dict, tables: dict, assign_override: dict = None, breakdown: dict = None) -> dict:
    assign_row = assign_override if assign_override is not None else tables["item_budget_assign"].get((entry,))
    template_id = assign_row["template_id"] if assign_row else None
    template_stats = _template_stats(template_id, tables) if template_id else []
    template_name = tables["item_budget_template_name"].get((template_id,), {}).get("name", "") if template_id else ""
    item_count = _template_item_count(template_id, tables) if template_id else 0

    absorbed_mask = assign_row["absorbed_spell_slots"] if assign_row else 0
    spell_slots = []
    for i in range(1, 6):
        spellid = item_row.get(f"spellid_{i}", 0)
        trigger = item_row.get(f"spelltrigger_{i}", 0)
        if spellid and trigger == 1:
            spell_slots.append({"index": i, "spellid": spellid, "absorbed": bool(absorbed_mask & (1 << (i - 1)))})
    return {
        "budget_assign": assign_row,
        "budget_template_id": template_id,
        "budget_template_name": template_name,
        "budget_template_stats": template_stats,
        "budget_template_shared_count": item_count,  # >1 means other items use the same shape too
        "budget_spell_slots": spell_slots,
        "budget_breakdown": breakdown,
        # item_mod_names comes from _form_enum_context(), always spread alongside this -
        # not repeated here to avoid a duplicate-kwarg TypeError at both call sites.
    }


def _regenerate_entries(entries: list[int], template_id: int, comment: str):
    """Recomputes and diffs every entry in `entries` still assigned to
    `template_id` (skips any that aren't - e.g. reassigned since the page
    loaded) and writes one combined guarded-UPDATE file, or None if nothing
    actually changed."""
    tables = get_budget_tables()
    items = get_rows()
    to_write = []
    for entry in entries:
        item_row = items.get(entry)
        assign_row = tables["item_budget_assign"].get((entry,))
        if not item_row or not assign_row or assign_row["template_id"] != template_id:
            continue
        try:
            b = budget.compute_breakdown(item_row, assign_row, tables)
        except budget.BudgetError:
            continue
        changes_fields = budget.materialized_item_fields(b)
        changes = emit.diff_row(item_row, changes_fields)
        if changes:
            to_write.append((entry, changes, item_row))
    return budget_emit.write_regenerate_many(to_write, comment)


@app.route("/templates")
def template_list():
    tables = get_budget_tables()
    counts: dict[int, int] = {}
    for (_entry,), row in tables["item_budget_assign"].items():
        counts[row["template_id"]] = counts.get(row["template_id"], 0) + 1
    rows = [
        {
            "template_id": tid,
            "name": tables["item_budget_template_name"].get((tid,), {}).get("name", "(unnamed)"),
            "shape": _template_shape_summary(tid, tables),
            "item_count": counts.get(tid, 0),
        }
        for tid in sorted(_template_ids(tables))
    ]
    return render_template("template_list.html", rows=rows)


def _save_template(template_id: int, is_new: bool):
    name = request.form.get("name", "").strip()
    fallback = url_for("template_new") if is_new else url_for("template_edit", template_id=template_id)
    if not name:
        flash("Template needs a name.", "error")
        return redirect(fallback)

    stats, error = _parse_percentage_stats(request.form)
    if error:
        flash(error, "error")
        return redirect(fallback)

    note = request.form.get("note", "").strip()
    if not note:
        flash("A change note is required (it becomes the pending SQL file's comment).", "error")
        return redirect(fallback)

    comment = f"item-tools: template {template_id} {name!r}. {note}"
    path = budget_emit.write_template(template_id, name, stats, comment)
    get_budget_tables(force=True)

    regen_entries = [int(e) for e in request.form.getlist("regenerate")]
    regen_path = _regenerate_entries(regen_entries, template_id, comment) if regen_entries else None
    get_rows(force=True)

    msg = f"Wrote {_display_path(path)}."
    if regen_path:
        msg += f" Regenerated {_display_path(regen_path)}."
    elif regen_entries:
        msg += " Regenerate: no item's materialized stats actually changed."
    flash(msg, "success")
    return redirect(url_for("template_edit", template_id=template_id))


@app.route("/templates/new", methods=["GET", "POST"])
def template_new():
    tables = get_budget_tables()
    existing_ids = _template_ids(tables)

    if request.method == "POST":
        try:
            template_id = int(request.form["template_id"])
        except (KeyError, ValueError):
            flash("Template ID must be a number.", "error")
            return redirect(url_for("template_new"))
        if template_id in existing_ids:
            flash(f"Template {template_id} already exists - edit it instead.", "error")
            return redirect(url_for("template_edit", template_id=template_id))
        return _save_template(template_id, is_new=True)

    suggested_id = (max(existing_ids) + 1) if existing_ids else 1
    return render_template(
        "template_form.html", template_id=None, suggested_id=suggested_id,
        name="", stats=[], is_new=True, assigned_items=[],
        item_mod_names=item_enums.ITEM_MOD_NAMES, item_mod_custom=item_enums.ITEM_MOD_CUSTOM,
    )


@app.route("/templates/<int:template_id>", methods=["GET", "POST"])
def template_edit(template_id: int):
    if request.method == "POST":
        return _save_template(template_id, is_new=False)

    tables = get_budget_tables()
    stats = _template_stats(template_id, tables)
    name_row = tables["item_budget_template_name"].get((template_id,))
    if not stats and not name_row:
        abort(404)

    items = get_rows()
    assigned_items = sorted(
        (
            {"entry": entry, "name": items[entry]["name"]}
            for (entry,), row in tables["item_budget_assign"].items()
            if row["template_id"] == template_id and entry in items
        ),
        key=lambda r: r["name"],
    )

    return render_template(
        "template_form.html", template_id=template_id, suggested_id=None,
        name=name_row["name"] if name_row else "", stats=stats, is_new=False,
        assigned_items=assigned_items,
        item_mod_names=item_enums.ITEM_MOD_NAMES, item_mod_custom=item_enums.ITEM_MOD_CUSTOM,
    )


def _tables_with_template_override(tables: dict, template_id: int, stats: list[dict]) -> dict:
    """Shallow copy of `tables` with `item_budget_template`'s rows for
    `template_id` replaced by `stats` - lets `budget.compute_breakdown()`
    preview/save against a shape just edited on the item page, before (or
    without) actually writing it."""
    overridden = {k: v for k, v in tables["item_budget_template"].items() if k[0] != template_id}
    for s in stats:
        overridden[(template_id, s["stat_type"])] = {"template_id": template_id, "stat_type": s["stat_type"], "alloc": s["alloc"]}
    return {**tables, "item_budget_template": overridden}


@app.route("/items/<int:entry>/budget", methods=["POST"])
def item_budget_save(entry: int):
    items = get_rows()
    item_row = items.get(entry)
    if item_row is None:
        abort(404)
    tables = get_budget_tables()
    action = request.form.get("action", "save")

    existing_assign = tables["item_budget_assign"].get((entry,))
    existing_template_id = existing_assign["template_id"] if existing_assign else None
    is_shared = existing_template_id is not None and _template_item_count(existing_template_id, tables) > 1

    template_to_write = None  # (template_id, name, stats), or None if this save doesn't touch a shape
    if is_shared:
        # The item page shows this shape read-only when it's shared with
        # other items (edit it at /templates/<id> instead - see
        # item_form.html) - keep using it exactly as-is.
        template_id = existing_template_id
    else:
        stats, error = _parse_percentage_stats(request.form)
        if error:
            flash(error, "error")
            return redirect(url_for("item_edit", entry=entry))
        template_name = request.form.get("template_name", "").strip() or f"{item_row.get('name') or entry} shape"
        if existing_template_id is not None:
            template_id = existing_template_id  # exclusively this item's own shape - overwrite in place
        else:
            existing_ids = _template_ids(tables)
            template_id = (max(existing_ids) + 1) if existing_ids else 1
        template_to_write = (template_id, template_name, stats)
        tables = _tables_with_template_override(tables, template_id, stats)

    def _f(name, cast, default):
        raw = request.form.get(name, "").strip()
        return cast(raw) if raw else default

    absorbed = 0
    for i in range(1, 6):
        if request.form.get(f"absorb_{i}"):
            absorbed |= 1 << (i - 1)

    assign_fields = {
        "entry": entry,
        "template_id": template_id,
        "budget_mult": _f("budget_mult", float, 1.0),
        "stamina_delta": _f("stamina_delta", int, 0),
        "dps_delta": _f("dps_delta", float, 0.0),
        "absorbed_spell_slots": absorbed,
        "armor_delta": _f("armor_delta", int, 0),
    }

    try:
        breakdown = budget.compute_breakdown(item_row, assign_fields, tables)
    except budget.BudgetError as e:
        flash(f"Can't compute this item's budget: {e}", "error")
        return redirect(url_for("item_edit", entry=entry))

    if action == "preview":
        return render_template(
            "item_form.html", entry=entry, row=item_row, sections=schema.sections(),
            is_new=False, custom_range=ids.item_range(), **_form_enum_context(),
            **_budget_form_context(entry, item_row, tables, assign_fields, breakdown),
        )

    note = request.form.get("note", "").strip()
    if not note:
        flash("A change note is required (it becomes the pending SQL file's comment).", "error")
        return redirect(url_for("item_edit", entry=entry))

    changes = budget.materialized_item_fields(breakdown)
    changes.update(budget.absorb_spell_fields(absorbed))
    item_changes = emit.diff_row(item_row, changes)

    name = item_row.get("name") or f"entry {entry}"
    comment = f"item-tools: {name!r} ({entry}) budget assignment -> template {template_id}. {note}"
    path = budget_emit.write_assign_and_regenerate(entry, assign_fields, item_changes, item_row, comment,
                                                     template=template_to_write)
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
        **_budget_form_context(entry, original, get_budget_tables()),
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
