#!/usr/bin/env python3
"""
Packages every DBC in the hand-maintained model/visual working copy
(apps/dbc-tools/var/model-visual-dbc/DBFilesClient/ by default) into patch-M.mpq - the ongoing
home for custom creature-display/spell-visual client content that falls outside
apps/dbc-tools/generate.py's own pipeline (which owns Spell.dbc/Talent.dbc/etc. and ships as
patch-Z.mpq - see lib/patch_out.py). patch-Y.mpq (GT combat-rating tables, patch_gt_tables.py) is
the third leg of the same convention.

The working copy used to live at client/AscensionFiles/enUS/DBFilesClient/ - a full extracted
client copy, multiple GB, kept around solely so these two scripts had loose .dbc files to read.
That's wasteful for the ~7 files (a few MB total) actually touched here, and it's what got deleted
during a disk-space crunch (2026-08-31), breaking this script with no obvious way to regenerate it
short of a full client re-extraction. Replaced with a purpose-built, lightweight extraction of just
the needed files (see this repo's own docs/agent notes for the exact `smpq -x` invocation against
a reference client's Data/enUS/patch-enUS*.MPQ, in ascending patch-priority order so later patches
correctly override earlier ones) - regenerate that directory the same way if it's ever missing;
this script only reads/writes it, it doesn't know how to produce it from scratch.

Whichever script edits a DBC in that working copy (patch_frozen_orb_model.py today; anything future
that touches CreatureModelData/CreatureDisplayInfo/GameObjectDisplayInfo/SpellVisual*) should be run
first; this script just re-packages whatever's currently sitting there and drops the result into the
patch-service's PATCH_ROOT so the timer-driven manifest_gen.py container picks it up on its next
pass (or immediately, if run by hand - see apps/patch-service/README.md).

Usage:
    python3 apps/dbc-tools/build_patch_m.py [--dbfilesclient PATH] [--deploy-root PATH]

    --dbfilesclient  Working-copy directory to package (default:
                      apps/dbc-tools/var/model-visual-dbc/DBFilesClient).
    --deploy-root    patch-service PATCH_ROOT to copy patch-M.mpq's Data/ into (default:
                      /home/plex/wow_server/patch-root). Pass --deploy-root '' to skip deployment
                      and only (re)build apps/dbc-tools/var/dbc-patch/patch-M.mpq locally.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from lib.mpq_writer import write_mpq

DEFAULT_DBFILESCLIENT = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-M.mpq"
DEFAULT_DEPLOY_ROOT = Path("/home/plex/wow_server/patch-root")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbfilesclient", type=Path, default=DEFAULT_DBFILESCLIENT)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT))
    args = parser.parse_args()

    dbc_files = sorted(p for p in args.dbfilesclient.iterdir() if p.suffix.lower() == ".dbc")
    if not dbc_files:
        raise SystemExit(f"no .dbc files found in {args.dbfilesclient}")

    files = {f"DBFilesClient\\{p.name}": p.read_bytes() for p in dbc_files}
    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes) from {len(dbc_files)} file(s):")
    for p in dbc_files:
        print(f"  {p.name}")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-M.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("(manifest-gen container picks this up on its next timer tick - run "
              "apps/patch-service/manifest_gen.py by hand for an immediate manifest.txt refresh)")


if __name__ == "__main__":
    main()
