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
from pathlib import Path

import yaml

SPELL_CSV_FIELDNAMES = (
    "id", "name", "school", "dispel", "mechanic", "attributes", "category",
    "cast_time_ms", "cooldown_ms", "category_cooldown_ms", "power_type",
    "mana_cost", "range_yards", "radius_yards", "duration_ms",
    "effect1", "effect2", "effect3", "spell_icon_id", "spell_weight",
    "coeff_weight", "raw_overrides", "notes",
)
SPELL_CSV_INT_FIELDS = (
    "id", "school", "dispel", "mechanic", "attributes", "category",
    "cast_time_ms", "cooldown_ms", "category_cooldown_ms", "power_type",
    "mana_cost", "duration_ms", "spell_icon_id",
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


def _load_talents_yaml_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("tabs", [])
    data.setdefault("talents", [])
    return data


def load_talents_yaml(dir_path: Path) -> dict:
    """Merge every source/talents/*.yaml file's tabs/talents lists into one
    dict, in sorted filename order."""
    merged = {"tabs": [], "talents": []}
    seen: dict[str, dict[int, str]] = {"tabs": {}, "talents": {}}
    for path in sorted(Path(dir_path).glob("*.yaml")):
        data = _load_talents_yaml_file(path)
        for key in ("tabs", "talents"):
            for entry in data[key]:
                if entry["id"] in seen[key]:
                    raise DuplicateIdError(
                        f"{key[:-1]} ID {entry['id']} appears in both "
                        f"{seen[key][entry['id']]!r} and {path.name!r}"
                    )
                seen[key][entry["id"]] = path.name
                merged[key].append(entry)
    return merged
