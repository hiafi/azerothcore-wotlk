#!/usr/bin/env python3
"""
Print ready-to-paste DSL `spell(...)` declarations for existing spell IDs -
the `source/classes/*` counterpart of `pull.py` (which still appends to the
legacy `source/spells/*.csv` files that no class uses any more). Same
reversal (`lib/reverse.py`) and the same "untouched reference copy is
silently skipped by generate.py" contract: paste the output into the right
`<class>_spells.py`/`<class>_trigger_spells.py`, edit what you mean to
change, run `generate.py`, and only the fields you changed become an edit.

Usage:
    python3 apps/dbc-tools/pull_dsl.py 12654 48108            # explicit IDs
    python3 apps/dbc-tools/pull_dsl.py 12654 --constants     # also run
                                                              # backfill_constants'
                                                              # int -> enum pass

Output goes to stdout only - it never writes into a class file itself, since
which file (castable vs trigger) and where in it are a human's call. Prints
nothing for an ID that's already declared somewhere under source/classes/
(re-pulling one would just be a duplicate-ID load error).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from csv_to_dsl import _slug, _spell_call_lines  # noqa: E402
from lib import dbcfmt, reverse, source, state, trainer_state  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="+", type=int, help="spell IDs to print DSL declarations for")
    ap.add_argument("--constants", action="store_true",
                    help="run backfill_constants' int->enum rewrite over the output too")
    args = ap.parse_args(argv)

    dsl = dsl_registry.load_classes_dir(
        SOURCE_DIR / "classes", ids_cfg=source.load_ids(SOURCE_DIR / "ids.yaml"),
        trainer_index=trainer_state.load_trainer_index(),
    )
    declared = {e["id"] for e in dsl["spells"]}
    # The legacy CSVs (source/spells/npc.csv, generic.csv) still count - generate.py refuses an
    # ID declared in both, so warn here rather than hand over a declaration that can't be used
    # until the CSV row is removed.
    legacy_dir = SOURCE_DIR / "spells"
    legacy = {e["id"]: e.get("_source_file", "?") for e in source.load_spells_csv(legacy_dir)} if legacy_dir.is_dir() else {}
    existing = state.load_existing_rows(dbcfmt.SPELL)
    secondary = {
        name: state.load_existing_rows(table) for name, table in (
            ("spellcasttimes", dbcfmt.SPELLCASTTIMES), ("spellduration", dbcfmt.SPELLDURATION),
            ("spellrange", dbcfmt.SPELLRANGE), ("spellradius", dbcfmt.SPELLRADIUS),
        )
    }
    chunks = []
    for spell_id in args.ids:
        if spell_id in declared:
            print(f"# skip {spell_id}: already declared under source/classes/", file=sys.stderr)
            continue
        if spell_id in legacy:
            print(
                f"# note {spell_id}: also present as a legacy CSV row in {legacy[spell_id]} - delete that "
                f"row when you paste this, generate.py rejects an ID declared in both",
                file=sys.stderr,
            )
        row = existing.get(spell_id)
        if not row:
            print(f"# {spell_id}: no such spell in base DBC or overlay", file=sys.stderr)
            continue
        entry = reverse.reverse_spell_row(row, secondary)
        entry["notes"] = "pulled from existing data"
        chunks.append("\n".join(_spell_call_lines(entry, _slug(entry["name"], spell_id))))
    text = "\n\n\n".join(chunks) + ("\n" if chunks else "")
    if args.constants and text:
        from backfill_constants import backfill
        text, _ = backfill(text)
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
