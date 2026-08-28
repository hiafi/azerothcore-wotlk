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

from lib import emit, ids, item_enums, loot, schema  # noqa: E402
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
