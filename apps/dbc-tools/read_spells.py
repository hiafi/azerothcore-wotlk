#!/usr/bin/env python3
"""
Print a class's source/spells/<class>.csv, sorted by learn level (BaseLevel), to eyeball
whether the leveling curve is front-loaded, back-loaded, or has big unlearned gaps.

Usage:
  python3 apps/dbc-tools/read_spells.py priest
  python3 apps/dbc-tools/read_spells.py priest --gap-threshold 6
  python3 apps/dbc-tools/read_spells.py npc          # works on any source/spells/*.csv file
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
SPELLS_DIR = TOOL_ROOT / "source" / "spells"

# SpellSchoolMask bits (src/server/shared/SharedDefines.h). These CSVs only ever carry a
# single-bit value in practice (never a real multi-school mask), so a flat lookup is enough.
SCHOOL_NAMES = {
    0: "Physical", 1: "Physical", 2: "Holy", 4: "Fire", 8: "Nature",
    16: "Frost", 32: "Shadow", 64: "Arcane",
}


def school_name(value: int) -> str:
    return SCHOOL_NAMES.get(value, f"Mixed({value})")


def load_rows(class_name: str) -> list[dict]:
    path = SPELLS_DIR / f"{class_name}.csv"
    if not path.is_file():
        available = sorted(p.stem for p in SPELLS_DIR.glob("*.csv"))
        sys.exit(f"no such file: {path}\navailable: {', '.join(available)}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tag_for(notes: str) -> str:
    if "single-rank bootstrap" in notes:
        return "bootstrapped"
    if "superseded rank kept" in notes:
        return "kept (item/quest, not trainer-taught)"
    if "reclassified from" in notes:
        return "reclassified"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("class_name", help="class file stem under source/spells/, e.g. priest")
    ap.add_argument(
        "--gap-threshold", type=int, default=4,
        help="flag a gap between two consecutive learn levels this wide or more (default: 4)",
    )
    args = ap.parse_args()

    rows = load_rows(args.class_name)

    entries = []
    for r in rows:
        overrides = json.loads(r["raw_overrides"]) if r.get("raw_overrides") else {}
        base_level = overrides.get("BaseLevel", 0) or 0  # 0 is a legitimate value, not "missing"
        entries.append({
            "id": int(r["id"]),
            "name": r["name"],
            "base_level": base_level,
            "school": school_name(int(r["school"] or 0)),
            "cast_time_ms": int(r["cast_time_ms"] or 0),
            "mana_cost_pct": int(r["mana_cost_pct"] or 0),
            "tag": tag_for(r["notes"]),
        })

    entries.sort(key=lambda e: (e["base_level"], e["name"]))

    id_w = max((len(str(e["id"])) for e in entries), default=2)
    name_w = max((len(e["name"]) for e in entries), default=4)
    school_w = max((len(e["school"]) for e in entries), default=6)

    header = (f"{'lvl':>3}  {'id':<{id_w}}  {'name':<{name_w}}  {'school':<{school_w}}  "
              f"{'cast':>6}  {'mana%':>5}  tag")
    print(header)
    print("-" * len(header))

    prev_level = None
    for e in entries:
        if prev_level is not None:
            gap = e["base_level"] - prev_level
            if gap >= args.gap_threshold:
                print(f"      {'':<{id_w}}  ... {gap}-level gap, nothing new learned ...")
        cast = "instant" if e["cast_time_ms"] == 0 else f"{e['cast_time_ms']}ms"
        print(f"{e['base_level']:>3}  {e['id']:<{id_w}}  {e['name']:<{name_w}}  "
              f"{e['school']:<{school_w}}  {cast:>6}  {e['mana_cost_pct']:>4}%  {e['tag']}")
        prev_level = e["base_level"]

    print()
    print(f"{len(entries)} spell(s) total, "
          f"levels {entries[0]['base_level']}-{entries[-1]['base_level']}" if entries else "0 spells")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
