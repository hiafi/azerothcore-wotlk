#!/usr/bin/env python3
"""
dbc-tools web editor — a small local Flask app for editing the same
source/spells/*.csv and source/talents/*.yaml files generate.py reads,
instead of hand-editing them in a text editor. CSV/YAML stay the source of
truth (see apps/dbc-tools/README.md's design rationale) — every route here
only ever reads/writes those files through lib/source.py, the same module
pull.py/pull_talents.py/generate.py already share.

Single-user LAN tool: no auth, no database, no JS build step. Run with:
  python3 apps/dbc-tools/webui/app.py
and reach it from any machine on the same network at
http://<this-machine's-LAN-IP>:8600/ — see the README's "Web UI" section
before exposing this beyond a trusted home network; there's no login, so
anyone who can reach the port can edit these files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for  # noqa: E402

import gamedata  # noqa: E402
import view_models  # noqa: E402
from lib import source  # noqa: E402
from lib.ids import NoFreeIdError, next_free_id  # noqa: E402
from lib.source import DuplicateIdError  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
SPELLS_DIR = SOURCE_DIR / "spells"
TALENTS_DIR = SOURCE_DIR / "talents"
IDS_PATH = SOURCE_DIR / "ids.yaml"

app = Flask(__name__)
app.secret_key = "dbc-tools-webui"  # local single-user tool, not internet-facing


def spell_csv_path(file: str) -> Path:
    path = SPELLS_DIR / f"{file}.csv"
    if not path.is_file():
        abort(404, f"no source/spells/{file}.csv")
    return path


def talent_yaml_path(file: str) -> Path:
    path = TALENTS_DIR / f"{file}.yaml"
    if not path.is_file():
        abort(404, f"no source/talents/{file}.yaml")
    return path


# -- dashboard --------------------------------------------------------------


@app.route("/")
def index():
    spell_files = []
    for path in sorted(SPELLS_DIR.glob("*.csv")):
        try:
            count = len(source.load_one_spell_file(path))
            error = None
        except Exception as exc:  # noqa: BLE001 - surface any parse error inline, don't 500 the dashboard
            count, error = None, str(exc)
        spell_files.append({"stem": path.stem, "count": count, "error": error})

    talent_files = []
    for path in sorted(TALENTS_DIR.glob("*.yaml")):
        try:
            data = source.load_talents_yaml_file(path)
            counts = {key: len(data[key]) for key in source.TALENTS_YAML_KEYS}
            error = None
        except Exception as exc:  # noqa: BLE001
            counts, error = None, str(exc)
        talent_files.append({"stem": path.stem, "counts": counts, "error": error})

    return render_template("index.html", spell_files=spell_files, talent_files=talent_files)


@app.route("/generate", methods=["POST"])
def run_generate():
    result = subprocess.run(
        [sys.executable, str(TOOL_ROOT / "generate.py")],
        cwd=TOOL_ROOT, capture_output=True, text=True,
    )
    return render_template("generate_result.html", result=result)


# -- spells -------------------------------------------------------------


@app.route("/spells/<file>")
def spell_list(file: str):
    path = spell_csv_path(file)
    entries = sorted(source.load_one_spell_file(path), key=lambda e: e["id"])
    return render_template("spell_list.html", file=file, entries=entries)


@app.route("/spells/<file>/new")
def spell_new(file: str):
    spell_csv_path(file)
    ids_cfg = source.load_ids(IDS_PATH)
    used_ids = {e["id"] for e in source.load_spells_csv(SPELLS_DIR)}
    try:
        suggested_id = next_free_id(ids_cfg, "spell", used_ids)
    except NoFreeIdError as exc:
        flash(str(exc), "error")
        suggested_id = ""
    ctx = view_models.spell_entry_to_form_context({"id": suggested_id})
    return render_template("spell_form.html", file=file, original_id="", ctx=ctx, **_spell_form_kwargs(ctx))


@app.route("/spells/<file>/<int:spell_id>/edit")
def spell_edit(file: str, spell_id: int):
    path = spell_csv_path(file)
    entries = source.load_one_spell_file(path)
    entry = next((e for e in entries if e["id"] == spell_id), None)
    if entry is None:
        abort(404, f"spell {spell_id} not found in source/spells/{file}.csv")
    ctx = view_models.spell_entry_to_form_context(entry)
    return render_template("spell_form.html", file=file, original_id=spell_id, ctx=ctx, **_spell_form_kwargs(ctx))


def _spell_form_kwargs(ctx: dict) -> dict:
    icon_id = int(ctx["spell_icon_id"]) if ctx["spell_icon_id"] else None
    return {
        "plain_fields": view_models.SPELL_PLAIN_FIELDS,
        "effect_fields": view_models.EFFECT_FIELDS,
        "school_options": view_models.SCHOOL_OPTIONS,
        "power_type_options": view_models.POWER_TYPE_OPTIONS,
        "effect_type_options": view_models.effect_type_options(),
        "icon_url": gamedata.icon_url(icon_id),
    }


@app.route("/api/icon-url/<int:icon_id>")
def api_icon_url(icon_id: int):
    url = gamedata.icon_url(icon_id)
    if url is None:
        abort(404)
    return jsonify(url=url)


@app.route("/api/spell-info/<int:spell_id>")
def api_spell_info(spell_id: int):
    try:
        entries = source.load_spells_csv(SPELLS_DIR)
    except DuplicateIdError:
        entries = []
    info = gamedata.spell_summary(spell_id, entries)
    if info is None:
        abort(404)
    return jsonify(info)


@app.route("/spells/<file>/save", methods=["POST"])
def spell_save(file: str):
    path = spell_csv_path(file)
    original_id = request.form.get("original_id", "").strip()

    try:
        entry = view_models.spell_entry_from_form(request.form)
    except ValueError as exc:
        flash(f"Couldn't save: {exc}", "error")
        return redirect(request.referrer or url_for("spell_list", file=file))

    try:
        all_entries = source.load_spells_csv(SPELLS_DIR)
    except DuplicateIdError as exc:
        flash(f"Couldn't save: source/spells/ already has a conflict: {exc}", "error")
        return redirect(request.referrer or url_for("spell_list", file=file))

    filename = path.name
    other_ids = {e["id"] for e in all_entries if e["_source_file"] != filename}
    if entry["id"] in other_ids:
        flash(f"Spell ID {entry['id']} is already used in another source file.", "error")
        return redirect(request.referrer or url_for("spell_list", file=file))

    # Read this file's rows as raw strings (not load_spells_csv's typed
    # entries) and patch just the one row that changed, so every other row's
    # exact original text — including numeric formatting like a hand-typed
    # "40" in a float column, which int/float round-tripping would otherwise
    # quietly renormalize to "40.0" — survives byte-for-byte. Also preserves
    # the file's existing row order (hand-curated, e.g. a spell kept next to
    # its sub-effect spells, not numeric) rather than append+sort.
    raw_rows = source.load_one_spell_file_raw(path)
    idx = None
    if original_id:
        orig_id = int(original_id)
        idx = next((i for i, r in enumerate(raw_rows) if int(r["id"]) == orig_id), None)
    if any(i != idx and int(r["id"]) == entry["id"] for i, r in enumerate(raw_rows)):
        flash(f"Spell ID {entry['id']} already exists in this file.", "error")
        return redirect(request.referrer or url_for("spell_list", file=file))
    new_row = source.spell_entry_to_csv_row(entry)
    if idx is None:
        raw_rows.append(new_row)
    else:
        raw_rows[idx] = new_row
    source.write_spells_csv_rows_file(path, raw_rows)
    flash(f"Saved spell {entry['id']}.", "success")
    return redirect(url_for("spell_list", file=file))


@app.route("/spells/<file>/<int:spell_id>/delete", methods=["POST"])
def spell_delete(file: str, spell_id: int):
    path = spell_csv_path(file)
    rows = [r for r in source.load_one_spell_file_raw(path) if int(r["id"]) != spell_id]
    source.write_spells_csv_rows_file(path, rows)
    flash(f"Deleted spell {spell_id}.", "success")
    return redirect(url_for("spell_list", file=file))


# -- talents --------------------------------------------------------------


def _load_talent_file(file: str):
    path = talent_yaml_path(file)
    header, _ = source.split_leading_comments(path.read_text(encoding="utf-8"))
    data = source.load_talents_yaml_file(path)
    return path, header, data


@app.route("/talents/<file>")
def talent_list(file: str):
    _, _, data = _load_talent_file(file)
    try:
        spell_entries = source.load_spells_csv(SPELLS_DIR)
    except DuplicateIdError:
        spell_entries = []
    talents = []
    for e in sorted(data["talents"], key=lambda e: (e["tab_id"], e["tier"], e["column"])):
        rank_ids = e.get("rank_spell_ids") or []
        info = gamedata.spell_summary(rank_ids[-1], spell_entries) if rank_ids else None
        talents.append({**e, "name": info["name"] if info else ""})
    return render_template(
        "talent_list.html", file=file,
        tabs=sorted(data["tabs"], key=lambda e: e["id"]),
        talents=talents,
        abilities=sorted(data["skill_line_abilities"], key=lambda e: e["id"]),
    )


def _used_ids(kind: str) -> set[int]:
    merged = source.load_talents_yaml(TALENTS_DIR)
    key = {"talenttab": "tabs", "talent": "talents", "skilllineability": "skill_line_abilities"}[kind]
    return {e["id"] for e in merged[key]}


def _suggest_id(kind: str):
    ids_cfg = source.load_ids(IDS_PATH)
    try:
        return next_free_id(ids_cfg, kind, _used_ids(kind))
    except NoFreeIdError as exc:
        flash(str(exc), "error")
        return ""


def _save_talent_entry(file: str, key: str, kind: str, original_id: str, entry: dict, redirect_endpoint: str):
    path, header, data = _load_talent_file(file)
    try:
        merged = source.load_talents_yaml(TALENTS_DIR)
    except DuplicateIdError as exc:
        flash(f"Couldn't save: source/talents/ already has a conflict: {exc}", "error")
        return redirect(url_for(redirect_endpoint, file=file))

    this_file_ids = {e["id"] for e in data[key]}
    other_ids = {e["id"] for e in merged[key]} - this_file_ids
    if entry["id"] in other_ids:
        flash(f"ID {entry['id']} is already used in another talent file.", "error")
        return redirect(url_for(redirect_endpoint, file=file))

    # Replace in place, preserving existing row order — same reasoning as
    # spell_save: append+sort would reshuffle the whole file over one edit.
    rows = data[key]
    idx = None
    if original_id:
        orig_id = int(original_id)
        idx = next((i for i, r in enumerate(rows) if r["id"] == orig_id), None)
    if any(i != idx and r["id"] == entry["id"] for i, r in enumerate(rows)):
        flash(f"ID {entry['id']} already exists in this file.", "error")
        return redirect(url_for(redirect_endpoint, file=file))
    safe_entry = source.talent_entry_to_yaml_safe(entry)
    if idx is None:
        rows.append(safe_entry)
    else:
        rows[idx] = safe_entry
    data[key] = rows
    source.write_talents_yaml_file(path, header, data)
    flash(f"Saved {kind} {entry['id']}.", "success")
    return redirect(url_for(redirect_endpoint, file=file))


# tabs

@app.route("/talents/<file>/tabs/new")
def tab_new(file: str):
    talent_yaml_path(file)
    ctx = view_models.tab_entry_to_form_context({"id": _suggest_id("talenttab")})
    return render_template("tab_form.html", file=file, original_id="", ctx=ctx)


@app.route("/talents/<file>/tabs/<int:tab_id>/edit")
def tab_edit(file: str, tab_id: int):
    _, _, data = _load_talent_file(file)
    entry = next((e for e in data["tabs"] if e["id"] == tab_id), None)
    if entry is None:
        abort(404, f"tab {tab_id} not found in source/talents/{file}.yaml")
    ctx = view_models.tab_entry_to_form_context(entry)
    return render_template("tab_form.html", file=file, original_id=tab_id, ctx=ctx)


@app.route("/talents/<file>/tabs/save", methods=["POST"])
def tab_save(file: str):
    original_id = request.form.get("original_id", "").strip()
    try:
        entry = view_models.tab_entry_from_form(request.form)
    except ValueError as exc:
        flash(f"Couldn't save: {exc}", "error")
        return redirect(url_for("talent_list", file=file))
    return _save_talent_entry(file, "tabs", "talenttab", original_id, entry, "talent_list")


@app.route("/talents/<file>/tabs/<int:tab_id>/delete", methods=["POST"])
def tab_delete(file: str, tab_id: int):
    path, header, data = _load_talent_file(file)
    data["tabs"] = [e for e in data["tabs"] if e["id"] != tab_id]
    source.write_talents_yaml_file(path, header, data)
    flash(f"Deleted tab {tab_id}.", "success")
    return redirect(url_for("talent_list", file=file))


# talents

@app.route("/talents/<file>/talents/new")
def talent_new(file: str):
    talent_yaml_path(file)
    ctx = view_models.talent_entry_to_form_context({"id": _suggest_id("talent")})
    return render_template(
        "talent_form.html", file=file, original_id="", ctx=ctx, last_rank_info=None,
    )


@app.route("/talents/<file>/talents/<int:talent_id>/edit")
def talent_edit(file: str, talent_id: int):
    _, _, data = _load_talent_file(file)
    entry = next((e for e in data["talents"] if e["id"] == talent_id), None)
    if entry is None:
        abort(404, f"talent {talent_id} not found in source/talents/{file}.yaml")
    ctx = view_models.talent_entry_to_form_context(entry)
    return render_template(
        "talent_form.html", file=file, original_id=talent_id, ctx=ctx,
        last_rank_info=_last_rank_info(entry.get("rank_spell_ids")),
    )


def _last_rank_info(rank_spell_ids) -> dict | None:
    if not rank_spell_ids:
        return None
    try:
        entries = source.load_spells_csv(SPELLS_DIR)
    except DuplicateIdError:
        return None
    return gamedata.spell_summary(rank_spell_ids[-1], entries)


@app.route("/talents/<file>/talents/save", methods=["POST"])
def talent_save(file: str):
    original_id = request.form.get("original_id", "").strip()
    try:
        entry = view_models.talent_entry_from_form(request.form)
    except ValueError as exc:
        flash(f"Couldn't save: {exc}", "error")
        return redirect(url_for("talent_list", file=file))
    return _save_talent_entry(file, "talents", "talent", original_id, entry, "talent_list")


@app.route("/talents/<file>/talents/<int:talent_id>/delete", methods=["POST"])
def talent_delete(file: str, talent_id: int):
    path, header, data = _load_talent_file(file)
    data["talents"] = [e for e in data["talents"] if e["id"] != talent_id]
    source.write_talents_yaml_file(path, header, data)
    flash(f"Deleted talent {talent_id}.", "success")
    return redirect(url_for("talent_list", file=file))


# skill line abilities

@app.route("/talents/<file>/abilities/new")
def ability_new(file: str):
    talent_yaml_path(file)
    ctx = view_models.ability_entry_to_form_context({"id": _suggest_id("skilllineability")})
    return render_template("skilllineability_form.html", file=file, original_id="", ctx=ctx)


@app.route("/talents/<file>/abilities/<int:ability_id>/edit")
def ability_edit(file: str, ability_id: int):
    _, _, data = _load_talent_file(file)
    entry = next((e for e in data["skill_line_abilities"] if e["id"] == ability_id), None)
    if entry is None:
        abort(404, f"skill line ability {ability_id} not found in source/talents/{file}.yaml")
    ctx = view_models.ability_entry_to_form_context(entry)
    return render_template("skilllineability_form.html", file=file, original_id=ability_id, ctx=ctx)


@app.route("/talents/<file>/abilities/save", methods=["POST"])
def ability_save(file: str):
    original_id = request.form.get("original_id", "").strip()
    try:
        entry = view_models.ability_entry_from_form(request.form)
    except ValueError as exc:
        flash(f"Couldn't save: {exc}", "error")
        return redirect(url_for("talent_list", file=file))
    return _save_talent_entry(
        file, "skill_line_abilities", "skilllineability", original_id, entry, "talent_list",
    )


@app.route("/talents/<file>/abilities/<int:ability_id>/delete", methods=["POST"])
def ability_delete(file: str, ability_id: int):
    path, header, data = _load_talent_file(file)
    data["skill_line_abilities"] = [e for e in data["skill_line_abilities"] if e["id"] != ability_id]
    source.write_talents_yaml_file(path, header, data)
    flash(f"Deleted skill line ability {ability_id}.", "success")
    return redirect(url_for("talent_list", file=file))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8600, debug=False)
