#!/usr/bin/env python3
"""
Patches GtCombatRatings.dbc / GtOCTClassCombatRatingScalar.dbc so the client's own
GetCombatRatingBonus() returns the same percentage the server computes for the 4 custom stats
this fork repurposes onto legacy combat-rating slots (Mastery, Versatility, Cooldown Haste,
Proc Rate - see lib/gt_dbc.py's CUSTOM_COMBAT_RATINGS and Unit.h's CombatRating enum).

Why this is needed at all: Player::GetRatingMultiplier (server) and the client's native
GetCombatRatingBonus() use the *same formula* over these two DBCs, but the client's own copy
(baked into its MPQ archives) still has the *stock* Blizzard values for these 4 rows - which
meant something else entirely in retail (weapon-skill-point equivalents, hit-avoidance points),
not the clean percentage curve the server now applies to them.

The server's *values* don't come from a binary DBC file, though - confirmed by pulling the real
gtCombatRatings.dbc out of a live worldserver's DataDir: it's byte-identical in shape to a real
stock 3.3.5a client's copy (same header, same field_count=1 - "just a float per record, no ID
column" is how Blizzard genuinely ships this particular table, not a corruption), and AzerothCore's
own `DBCfmt.h` expects 2 fields for it, so the C++ loader's `AutoProduceData` silently produces
*zero* rows from that binary file (see lib/gt_dbc.py's docstring). The server's own
`sGtCombatRatingsStore`/`sGtOCTClassCombatRatingScalarStore` end up 100% populated by AzerothCore's
SQL overlay instead (`gtcombatratings_dbc`/`gtoctclasscombatratingscalar_dbc` in `acore_world` -
see DBCDatabaseLoader) - confirmed by querying a live server and finding those exact numbers match
what this was written to reproduce. So the input here is a plain (table, id, value) export of
those two SQL tables, not another binary DBC.

Usage:
    python3 apps/dbc-tools/patch_gt_tables.py --server-values /path/to/values.tsv

  --server-values  TSV file with columns `table<TAB>id<TAB>value`, one line per row, e.g.:
                        gtcombatratings_dbc	2000	0.538462
                        gtoctclasscombatratingscalar_dbc	12	1
                    Only needs to cover the ~440 (table, id) pairs this script actually asks for
                    (see report_*() below) - extras are ignored, missing ones are a hard error.
                    Generate it straight from the live server, e.g.:
                        docker exec -e MYSQL_PWD=<pw> <db-container> mysql -N -u root -e "
                          SELECT 'gtcombatratings_dbc', ID, Data FROM gtcombatratings_dbc
                          UNION ALL
                          SELECT 'gtoctclasscombatratingscalar_dbc', ID, Data
                          FROM gtoctclasscombatratingscalar_dbc" acore_world > values.tsv
                    Required.
  --client-dbc     Directory holding the *stock client's* copies of the same two files, extracted
                   from DBFilesClient\\ the same way apps/dbc-tools/README.md's Setup section has
                   you do for Spell.dbc et al. Defaults to var/extractors/dbc (same directory), so
                   dropping the two Gt*.dbc files in there alongside the existing extracted files
                   needs no extra flag.
  --deploy         Where to write this patch's own MPQ - a *separate* archive from dbc-tools' own
                   patch-Z.mpq, not merged into it. The 3.3.5a client loads any number of
                   patch[-2..9,A..Z].mpq archives it finds in Data\\, so a second, independently
                   named one works exactly the same as folding these two files into the first - no
                   client-side reason to combine them. Pass an empty string to skip writing it.
  --check          Report what would change without writing anything - use this first.

Output (unless --check):
  - loose files under var/dbc-patch/gt-tables/DBFilesClient/*.dbc, for inspection/diffing.
  - a second, independent patch MPQ (just these two files) at --deploy.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import gt_dbc  # noqa: E402
from lib.mpq_writer import write_mpq  # noqa: E402

DEFAULT_CLIENT_DBC_DIR = REPO_ROOT / "var" / "extractors" / "dbc"
GT_OUT_DIR = REPO_ROOT / "var" / "dbc-patch" / "gt-tables"
GT_LOOSE_DIR = GT_OUT_DIR / "DBFilesClient"

# This machine's patch-distribution root (see the patcher util that serves it) - not a repo path,
# just this box's deploy target. Named -Y, not -Z, specifically so it doesn't collide with
# dbc-tools' own patch-Z.mpq sitting in the same directory. Override with --deploy if you're
# running this somewhere else, or want a different free letter.
DEFAULT_DEPLOY_MPQ = Path("/home/plex/wow_server/patch-root/Data/patch-Y.mpq")

TABLE_COMBAT_RATINGS = "gtcombatratings_dbc"
TABLE_CLASS_SCALAR = "gtoctclasscombatratingscalar_dbc"

# Sanity-check checkpoints, purely for the printed report - not used by the patch logic itself.
CHECK_LEVELS = (60, 70, 80)


def combat_ratings_indices() -> list[int]:
    return [
        gt_dbc.combat_ratings_index(cr, level)
        for cr in gt_dbc.CUSTOM_COMBAT_RATINGS.values()
        for level in range(1, gt_dbc.GT_MAX_LEVEL + 1)
    ]


def class_scalar_indices() -> list[int]:
    return [
        gt_dbc.class_scalar_index(class_id, cr)
        for cr in gt_dbc.CUSTOM_COMBAT_RATINGS.values()
        for class_id in gt_dbc.WOTLK_CLASS_IDS
    ]


def load_server_values(path: Path) -> dict[str, dict[int, float]]:
    if not path.is_file():
        raise SystemExit(f"error: --server-values file not found: {path}")
    values: dict[str, dict[int, float]] = {TABLE_COMBAT_RATINGS: {}, TABLE_CLASS_SCALAR: {}}
    with path.open(newline="") as f:
        for lineno, row in enumerate(csv.reader(f, delimiter="\t"), start=1):
            if not row or not row[0].strip():
                continue
            if len(row) != 3:
                raise SystemExit(f"error: {path}:{lineno}: expected 3 tab-separated columns, got {row!r}")
            table, id_str, value_str = row
            if table not in values:
                continue  # a table we don't care about - fine, extras are allowed
            values[table][int(id_str)] = float(value_str)
    return values


def _client_bytes(client_dbc_dir: Path, filename: str) -> bytes:
    path = client_dbc_dir / filename
    if not path.is_file():
        raise SystemExit(
            f"error: client {filename} not found: {path}\n"
            "See this script's module docstring (--client-dbc) for what belongs there."
        )
    return path.read_bytes()


def report_combat_ratings(changes: list[gt_dbc.Change]) -> None:
    by_index = {c.index: c for c in changes}
    print("GtCombatRatings.dbc:")
    for label, cr in gt_dbc.CUSTOM_COMBAT_RATINGS.items():
        print(f"  {label} (CR {cr}):")
        for level in CHECK_LEVELS:
            c = by_index[gt_dbc.combat_ratings_index(cr, level)]
            print(f"    level {level}: {c.old_value:.4f} -> {c.new_value:.4f}  (1% = {c.new_value:.2f} rating)")
    print(f"  {len(changes)} rows patched total (4 stats x {gt_dbc.GT_MAX_LEVEL} levels).")


def report_class_scalar(changes: list[gt_dbc.Change]) -> None:
    by_index = {c.index: c for c in changes}
    print("GtOCTClassCombatRatingScalar.dbc:")
    for label, cr in gt_dbc.CUSTOM_COMBAT_RATINGS.items():
        print(f"  {label} (CR {cr}):")
        for class_id in gt_dbc.WOTLK_CLASS_IDS:
            c = by_index[gt_dbc.class_scalar_index(class_id, cr)]
            marker = "  (!) changed" if c.old_value != c.new_value else ""
            print(f"    class {class_id}: {c.old_value:.4f} -> {c.new_value:.4f}{marker}")
    print(f"  {len(changes)} rows patched total (4 stats x {len(gt_dbc.WOTLK_CLASS_IDS)} classes).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--server-values", required=True, type=Path,
                         help="TSV export of gtcombatratings_dbc/gtoctclasscombatratingscalar_dbc - see module docstring")
    parser.add_argument("--client-dbc", type=Path, default=DEFAULT_CLIENT_DBC_DIR,
                         help=f"Directory with the stock client's Gt*.dbc files (default: {DEFAULT_CLIENT_DBC_DIR})")
    parser.add_argument("--deploy", type=str, default=str(DEFAULT_DEPLOY_MPQ),
                         help=f"This patch's own MPQ output path, or \"\" to skip it (default: {DEFAULT_DEPLOY_MPQ})")
    parser.add_argument("--check", action="store_true", help="Report changes without writing any output")
    args = parser.parse_args()

    server_values = load_server_values(args.server_values)
    patched: dict[str, bytes] = {}

    client_bytes = _client_bytes(args.client_dbc, "GtCombatRatings.dbc")
    out_bytes, changes = gt_dbc.patch_values(client_bytes, server_values[TABLE_COMBAT_RATINGS], combat_ratings_indices())
    report_combat_ratings(changes)
    patched["GtCombatRatings.dbc"] = out_bytes

    print()

    client_bytes = _client_bytes(args.client_dbc, "GtOCTClassCombatRatingScalar.dbc")
    out_bytes, changes = gt_dbc.patch_values(client_bytes, server_values[TABLE_CLASS_SCALAR], class_scalar_indices())
    report_class_scalar(changes)
    patched["GtOCTClassCombatRatingScalar.dbc"] = out_bytes

    if args.check:
        print("\n--check: nothing written.")
        return 0

    print()
    GT_LOOSE_DIR.mkdir(parents=True, exist_ok=True)
    for filename, blob in patched.items():
        out = GT_LOOSE_DIR / filename
        out.write_bytes(blob)
        print(f"wrote {out}")

    if not args.deploy:
        print("\n--deploy \"\": skipped patch MPQ.")
        return 0

    deploy_path = Path(args.deploy)
    write_mpq(deploy_path, {f"DBFilesClient\\{name}": blob for name, blob in patched.items()})
    print(f"wrote {deploy_path} ({', '.join(sorted(patched))})")
    print("Drop this alongside dbc-tools' own patch-Z.mpq in the client's Data\\ - the client "
          "loads any number of patch[-2..9,A..Z].mpq archives it finds there.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
