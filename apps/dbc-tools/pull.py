#!/usr/bin/env python3
"""
DBC build pipeline — reverse entry point: pull existing spell rows into
source/spells/*.csv as a starting baseline (see docs/dbc-build-pipeline.md,
"pull.py — building a baseline from existing data").

Reads the merged base-DBC ⊕ current-overlay view (same one generate.py
reads) for the requested IDs, reverses each row through lib/reverse.py, and
appends the results to the matching per-class file — ready to hand-edit and
regenerate. The destination file is auto-detected from the spell's
`SpellClassSet` (SPELLFAMILY_* in src/server/shared/SharedDefines.h) unless
`--dest` is given explicitly — see apps/dbc-tools/README.md for the mapping
and when to override it (e.g. a boss-only ability with a class family still
usually belongs in npc.csv, not that class's file).

Usage:
  python3 apps/dbc-tools/pull.py --spell 116,120,10
  python3 apps/dbc-tools/pull.py --spell 100-200        # inclusive range
  python3 apps/dbc-tools/pull.py --spell 100 --dest npc # force destination
  python3 apps/dbc-tools/pull.py --all                  # every spell_dbc
                                                         # overlay row: the
                                                         # tool's own
                                                         # round-trip self-test
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, reverse, source, state  # noqa: E402
from lib.source import SPELL_CSV_FIELDNAMES, SPELL_CSV_JSON_FIELDS  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
SPELLS_DIR = SOURCE_DIR / "spells"

# SPELLFAMILY_* values, from src/server/shared/SharedDefines.h. Anything not
# listed here (0 generic, 1 events/holidays, 12/13 potion-ish, 17 pet, or a
# value with no player class at all) falls back to "generic".
SPELLFAMILY_TO_FILE = {
    3: "mage", 4: "warrior", 5: "warlock", 6: "priest", 7: "druid",
    8: "rogue", 9: "hunter", 10: "paladin", 11: "shaman", 15: "deathknight",
}


def parse_id_spec(spec: str) -> list[int]:
    ids: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.extend(range(int(lo), int(hi) + 1))
        else:
            ids.append(int(part))
    return ids


def detect_dest(row: dict) -> str:
    return SPELLFAMILY_TO_FILE.get(row.get("SpellClassSet"), "generic")


def entry_to_csv_row(entry: dict) -> dict:
    row = {}
    for field in SPELL_CSV_FIELDNAMES:
        if field == "notes":
            row[field] = "pulled from existing data"
            continue
        value = entry.get(field)
        if field in SPELL_CSV_JSON_FIELDS:
            row[field] = "" if value is None else json.dumps(value, sort_keys=True)
        elif value is None:
            row[field] = ""
        else:
            row[field] = value
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--spell", help="comma-separated IDs and/or ranges, e.g. 116,120,10-15")
    group.add_argument(
        "--all", action="store_true",
        help="pull every row currently in the spell_dbc overlay (round-trip self-test)",
    )
    ap.add_argument(
        "--dest",
        help="force a destination file stem (e.g. 'npc') instead of auto-detecting "
             "from SpellClassSet, for every ID this run pulls",
    )
    args = ap.parse_args()

    existing_spells = state.load_existing_rows(dbcfmt.SPELL)
    if args.all:
        wanted_ids = sorted(existing_spells)
    else:
        wanted_ids = parse_id_spec(args.spell)

    secondary_table_by_key = {
        "spellcasttimes": dbcfmt.SPELLCASTTIMES, "spellduration": dbcfmt.SPELLDURATION,
        "spellrange": dbcfmt.SPELLRANGE, "spellradius": dbcfmt.SPELLRADIUS,
    }
    secondary_rows = {
        name: state.load_existing_rows(table) for name, table in secondary_table_by_key.items()
    }

    already = {e["id"] for e in source.load_spells_csv(SPELLS_DIR)} if SPELLS_DIR.is_dir() else set()

    new_rows_by_dest: dict[str, list[dict]] = {}
    missing = []
    for spell_id in wanted_ids:
        row = existing_spells.get(spell_id)
        if not row:
            missing.append(spell_id)
            continue
        if spell_id in already:
            print(f"skip {spell_id}: already present in source/spells/")
            continue
        entry = reverse.reverse_spell_row(row, secondary_rows)
        dest = args.dest or detect_dest(row)
        new_rows_by_dest.setdefault(dest, []).append(entry_to_csv_row(entry))

    if missing:
        print(f"not found in spell_dbc (base DBC + overlay): {missing}")

    if not new_rows_by_dest:
        print("nothing new to pull")
        return 0

    for dest, rows in new_rows_by_dest.items():
        out_path = SPELLS_DIR / f"{dest}.csv"
        file_exists = out_path.is_file()
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=SPELL_CSV_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)
        print(f"pulled {len(rows)} row(s) into {out_path.relative_to(TOOL_ROOT.parent.parent)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
