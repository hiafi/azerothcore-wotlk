#!/usr/bin/env python3
"""
DBC build pipeline — reverse entry point: pull existing spell rows into
source/spells/*.csv as a starting baseline (see docs/dbc-build-pipeline.md,
"pull.py — building a baseline from existing data").

Reads the merged base-DBC ⊕ current-overlay view (same one generate.py
reads) for the requested IDs, reverses each row through lib/reverse.py, and
appends the results to the matching per-class file — ready to hand-edit and
regenerate. The destination file is auto-detected from the spell's
`SpellClassSet` (SPELLFAMILY_* in src/server/shared/SharedDefines.h), unless
`--dest` is given explicitly — see apps/dbc-tools/README.md for the mapping.
A class-family match with no `trainer_spell`/`spell_ranks` evidence of being
real player content (a boss/creature clone that merely shares the class's
SpellClassSet) is routed to `npc.csv` instead, regardless of `SpellClassSet`
— see `detect_dest`/`_load_player_spell_ids` below.

Usage:
  python3 apps/dbc-tools/pull.py --spell 116,120,10
  python3 apps/dbc-tools/pull.py --spell 100-200        # inclusive range
  python3 apps/dbc-tools/pull.py --spell 100 --dest npc # force destination
  python3 apps/dbc-tools/pull.py --class mage           # every spell whose
                                                         # SpellClassSet is
                                                         # that class
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

from lib import dbcfmt, reverse, source, sql_dump, state  # noqa: E402
from lib.source import SPELL_CSV_FIELDNAMES, SPELL_CSV_JSON_FIELDS  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
SPELLS_DIR = SOURCE_DIR / "spells"

# Column orders transcribed verbatim from the `CREATE TABLE` in
# data/sql/base/db_world/{trainer_spell,spell_ranks}.sql — needed because
# neither file's INSERT statements list column names explicitly, unlike the
# `spell_dbc`-style dumps lib/dbcfmt.py already models via DbcTable.
_TRAINER_SPELL_COLUMNS = (
    "TrainerId", "SpellId", "MoneyCost", "ReqSkillLine", "ReqSkillRank",
    "ReqAbility1", "ReqAbility2", "ReqAbility3", "ReqLevel", "VerifiedBuild",
)
_SPELL_RANKS_COLUMNS = ("first_spell_id", "spell_id", "rank")


def _load_player_spell_ids() -> set[int]:
    """Every spell ID with real player-facing evidence: taught by a trainer,
    or a member of a rank chain (spell_ranks carries a row — rank 1 included
    — for every genuine player ability, not just multi-rank ones). Used to
    keep `detect_dest` from routing a boss/creature-only clone that merely
    shares a player class's SpellClassSet into that class's file — see
    README.md's "a boss ability that happens to share a player class's
    SpellClassSet usually belongs in npc.csv" note, now automated instead of
    relying on a human to catch it during pull/review."""
    ids: set[int] = set()
    trainer_path = state.BASE_SQL_DIR / "trainer_spell.sql"
    if trainer_path.is_file():
        ids.update(
            row["SpellId"]
            for row in sql_dump.read_table_rows(trainer_path, "trainer_spell", _TRAINER_SPELL_COLUMNS)
        )
    ranks_path = state.BASE_SQL_DIR / "spell_ranks.sql"
    if ranks_path.is_file():
        ids.update(
            row["spell_id"]
            for row in sql_dump.read_table_rows(ranks_path, "spell_ranks", _SPELL_RANKS_COLUMNS)
        )
    return ids

# SPELLFAMILY_* values, from src/server/shared/SharedDefines.h. Anything not
# listed here (0 generic, 1 events/holidays, 12/13 potion-ish, 17 pet, or a
# value with no player class at all) falls back to "generic".
SPELLFAMILY_TO_FILE = {
    3: "mage", 4: "warrior", 5: "warlock", 6: "priest", 7: "druid",
    8: "rogue", 9: "hunter", 10: "paladin", 11: "shaman", 15: "deathknight",
}
FILE_TO_SPELLFAMILY = {v: k for k, v in SPELLFAMILY_TO_FILE.items()}


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


def detect_dest(row: dict, player_spell_ids: set[int]) -> str:
    dest = SPELLFAMILY_TO_FILE.get(row.get("SpellClassSet"), "generic")
    # A class-family match with no trainer/rank-chain evidence is a
    # boss/creature clone that happens to share the class's SpellClassSet
    # (school/mechanic tagging), not real player content — send it to
    # npc.csv instead. Leave the "generic" fallback alone: that's already
    # its own bucket (trinket procs, test content) for a different reason
    # (no player class at all), not something this check should touch.
    if dest != "generic" and row["ID"] not in player_spell_ids:
        return "npc"
    return dest


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
        "--class", dest="klass", choices=sorted(FILE_TO_SPELLFAMILY),
        help="pull every existing spell whose SpellClassSet matches this class",
    )
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
    elif args.klass:
        family = FILE_TO_SPELLFAMILY[args.klass]
        wanted_ids = sorted(
            i for i, row in existing_spells.items() if row.get("SpellClassSet") == family
        )
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
    player_spell_ids = _load_player_spell_ids()

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
        dest = args.dest or detect_dest(row, player_spell_ids)
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
