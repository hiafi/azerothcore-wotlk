"""
Loads and type-converts the hand-authored source files:
  source/ids.yaml       - reserved ID blocks
  source/spells/*.csv   - new/changed Spell.dbc rows, one file per class (plus
                          npc.csv / generic.csv) so no single file grows huge
  source/talents/*.yaml - new/changed Talent.dbc + TalentTab.dbc rows, one
                          file per class

Splitting by file is purely an authoring convenience — every file shares
the same schema and they're all merged into one list before anything in
build.py/reuse.py ever sees them. See apps/dbc-tools/README.md for the
per-file convention (which class gets which spells, where old ranks go once
docs/single-rank-spell-system.md lands).
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import yaml
from ruamel.yaml import YAML

# Round-trip (not safe_load/safe_dump) so a talents/*.yaml file's inline
# comments — "# minted, source/ids.yaml talent block ... - Flurry" and the
# like — survive a load+dump unmodified, instead of PyYAML's safe_* pair
# silently discarding every comment on the next write. Confirmed
# byte-identical against every source/talents/*.yaml file with these
# defaults (no explicit width/indent tuning needed) before relying on it here.
_talents_yaml = YAML()
_talents_yaml.preserve_quotes = True

SPELL_CSV_FIELDNAMES = (
    "id", "name", "school", "dispel", "mechanic", "attributes", "category",
    "cast_time_ms", "cooldown_ms", "category_cooldown_ms", "power_type",
    "mana_cost", "mana_cost_pct", "range_yards", "radius_yards", "duration_ms",
    "effect1", "effect2", "effect3", "spell_icon_id", "spell_weight",
    "coeff_weight", "raw_overrides", "notes",
)
SPELL_CSV_INT_FIELDS = (
    "id", "school", "dispel", "mechanic", "attributes", "category",
    "cast_time_ms", "cooldown_ms", "category_cooldown_ms", "power_type",
    "mana_cost", "mana_cost_pct", "duration_ms", "spell_icon_id",
)
SPELL_CSV_FLOAT_FIELDS = ("range_yards", "radius_yards", "spell_weight", "coeff_weight")
SPELL_CSV_JSON_FIELDS = ("effect1", "effect2", "effect3", "raw_overrides")


class DuplicateIdError(ValueError):
    pass


def _blank(v: str | None) -> bool:
    return v is None or v.strip() == ""


def load_ids(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def in_range(entry_id: int, id_range: dict) -> bool:
    return id_range["start"] <= entry_id <= id_range["end"]


def partition_by_range(entries: list[dict], id_range: dict) -> tuple[list[dict], list[dict]]:
    """Split entries into (in the reserved block, outside it).

    Only the first list should ever be built/emitted — see generate.py's
    "reference-only" filtering and the "Corollary" in
    docs/dbc-build-pipeline.md: pulling an existing stock row into source/
    (via pull.py/pull_talents.py) is for reading/editing convenience, not an
    invitation to re-emit it at its original ID. A pulled row only starts
    being generated once its `id` is changed to a fresh one from
    source/ids.yaml."""
    inside, outside = [], []
    for entry in entries:
        (inside if in_range(entry["id"], id_range) else outside).append(entry)
    return inside, outside


def _parse_spell_csv_file(path: Path) -> list[dict]:
    entries = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if not raw.get("id") or raw["id"].strip().startswith("#"):
                continue  # blank/comment row
            entry = dict(raw)
            for field in SPELL_CSV_INT_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else int(v)
            for field in SPELL_CSV_FLOAT_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else float(v)
            for field in SPELL_CSV_JSON_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else json.loads(v)
            entry["_source_file"] = path.name
            entries.append(entry)
    return entries


def load_one_spell_file(path: Path) -> list[dict]:
    """Parse a single source/spells/*.csv file on its own, with no
    cross-file duplicate-ID check — for callers (the webui) that want just
    one file's rows and shouldn't blow up over a duplicate that lives
    entirely in some other file. Use load_spells_csv for anything that needs
    the whole merged, validated picture (generate.py, ID allocation, ...)."""
    return _parse_spell_csv_file(path)


def load_one_spell_file_raw(path: Path) -> list[dict]:
    """Like load_one_spell_file, but with no int/float/JSON type conversion —
    every field stays exactly the string it was on disk. Used by the webui to
    patch a single row: reload the file this way, replace/append just the one
    row that actually changed (as a spell_entry_to_csv_row(...) dict, which is
    already string-valued), and rewrite via write_spells_csv_rows_file. Every
    *other* row's text survives byte-for-byte — round-tripping it through
    load_one_spell_file's int/float parsing would quietly renormalize things
    like a hand-typed "40" in a float column into "40.0", turning an edit to
    one row into a diff across the whole file."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if not raw.get("id") or raw["id"].strip().startswith("#"):
                continue
            rows.append(dict(raw))
    return rows


def load_spells_csv(dir_path: Path) -> list[dict]:
    """Merge every source/spells/*.csv file into one list, in sorted
    filename order (so merge order — and therefore any error message about
    a duplicate ID — is deterministic)."""
    entries = []
    seen: dict[int, str] = {}
    for path in sorted(Path(dir_path).glob("*.csv")):
        for entry in _parse_spell_csv_file(path):
            if entry["id"] in seen:
                raise DuplicateIdError(
                    f"spell ID {entry['id']} appears in both "
                    f"{seen[entry['id']]!r} and {path.name!r}"
                )
            seen[entry["id"]] = path.name
            entries.append(entry)
    return entries


def split_leading_comments(text: str) -> tuple[str, str]:
    """Split off a file's leading `#`-comment/blank-line block (the
    hand-written schema/example doc at the top of each talents/*.yaml) from
    the actual YAML content after it. Returns (header, remainder) — header
    includes its trailing blank line(s) verbatim, remainder is what
    `yaml.safe_load` should see. Used so pulling new rows into a file can
    rewrite just the data half without clobbering the human-written part."""
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#") or lines[i].strip() == ""):
        i += 1
    return "".join(lines[:i]), "".join(lines[i:])


TALENTS_YAML_KEYS = ("tabs", "talents", "skill_line_abilities")


def load_talents_yaml_file(path: Path) -> dict:
    """Returns a ruamel.yaml round-trip object (CommentedMap, behaves like a
    plain dict for every read this codebase does) rather than a plain dict —
    load_talents_yaml_file/write_talents_yaml_file is the pair a caller
    should use together when it intends to write the file back, so per-entry
    comments survive; see write_talents_yaml_file."""
    with open(path, encoding="utf-8") as f:
        _, remainder = split_leading_comments(f.read())
    data = _talents_yaml.load(remainder)
    if data is None:
        data = {}
    for key in TALENTS_YAML_KEYS:
        data.setdefault(key, [])
    return data


def spell_entry_to_csv_row(entry: dict) -> dict:
    """Serialize a spell entry (the dict shape load_spells_csv/_parse_spell_csv_file
    produce) back into a flat dict of strings ready for csv.DictWriter — the
    save-side counterpart to _parse_spell_csv_file. None round-trips to ""; each
    SPELL_CSV_JSON_FIELDS value goes through json.dumps(sort_keys=True), matching
    the alphabetical key order already committed throughout source/spells/*.csv."""
    row = {}
    for field in SPELL_CSV_FIELDNAMES:
        value = entry.get(field)
        if field in SPELL_CSV_JSON_FIELDS:
            row[field] = "" if value is None else json.dumps(value, sort_keys=True)
        else:
            row[field] = "" if value is None else value
    return row


def write_spells_csv_rows_file(path: Path, rows: list[dict]) -> None:
    """Rewrite one source/spells/*.csv file from already string-valued row
    dicts (load_one_spell_file_raw's shape, or spell_entry_to_csv_row's) — the
    low-level half of write_spells_csv_file, split out so a caller that only
    changed one row (the webui) can pass every other row through verbatim
    instead of round-tripping it through int/float/JSON parsing again. Writes
    to a sibling .tmp file first and os.replace()s it into place, so a crash
    mid-write can't leave a truncated CSV behind."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        # lineterminator="\n": csv's default dialect writes "\r\n", but the
        # repo's .gitattributes forces "* text eol=lf" — without this override
        # a full-file rewrite would flip every existing LF-ending row to CRLF,
        # turning a one-row edit into a whole-file diff.
        writer = csv.DictWriter(f, fieldnames=SPELL_CSV_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, path)


def write_spells_csv_file(path: Path, entries: list[dict]) -> None:
    """Rewrite one source/spells/*.csv file from scratch with `entries` (each
    already in load_spells_csv's dict shape) — e.g. pull.py appending a fresh
    batch it just built from live DBC data, where there's no "other rows"
    formatting to preserve. See write_spells_csv_rows_file's docstring for why
    the webui uses that lower-level entry point instead."""
    write_spells_csv_rows_file(path, [spell_entry_to_csv_row(e) for e in entries])


def talent_entry_to_yaml_safe(entry: dict) -> dict:
    """Drop None-valued optional fields so the YAML stays terse — the
    save-side counterpart to load_talents_yaml_file. raw_overrides of None
    means "no overrides", so it's fine to omit entirely."""
    return {k: v for k, v in entry.items() if v is not None}


def write_talents_yaml_file(path: Path, header: str, data: dict) -> None:
    """Rewrite one source/talents/*.yaml file: `header` verbatim (the
    hand-written schema/example comment block split_leading_comments peeled
    off), then `data`'s tabs/talents/skill_line_abilities lists as YAML via
    the ruamel round-trip dumper. Pass the same object load_talents_yaml_file
    gave you (only mutated in place — e.g. one list item replaced or
    appended, not the whole dict rebuilt) so every untouched entry's inline
    comments round-trip unchanged; dumping a plain dict built from scratch
    would lose them same as PyYAML's safe_dump did. Atomic, same as
    write_spells_csv_rows_file."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(header)
        _talents_yaml.dump(data, f)
    os.replace(tmp_path, path)


def load_talents_yaml(dir_path: Path) -> dict:
    """Merge every source/talents/*.yaml file's tabs/talents/skill_line_abilities
    lists into one dict, in sorted filename order."""
    merged = {key: [] for key in TALENTS_YAML_KEYS}
    seen: dict[str, dict[int, str]] = {key: {} for key in TALENTS_YAML_KEYS}
    for path in sorted(Path(dir_path).glob("*.yaml")):
        data = load_talents_yaml_file(path)
        for key in TALENTS_YAML_KEYS:
            for entry in data[key]:
                if entry["id"] in seen[key]:
                    raise DuplicateIdError(
                        f"{key} entry ID {entry['id']} appears in both "
                        f"{seen[key][entry['id']]!r} and {path.name!r}"
                    )
                seen[key][entry["id"]] = path.name
                merged[key].append(entry)
    return merged
