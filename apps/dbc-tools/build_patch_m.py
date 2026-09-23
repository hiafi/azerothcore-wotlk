#!/usr/bin/env python3
"""
Packages every DBC in the hand-maintained model/visual working copy
(apps/dbc-tools/var/model-visual-dbc/DBFilesClient/ by default), plus every model/skin asset in its
sibling SPELLS/ working copy (apps/dbc-tools/var/model-visual-dbc/SPELLS/ by default - populated by
hand via `smpq -x` against a reference client, never committed - see that directory's own
gitignore), into patch-M.mpq - the ongoing home for custom creature-display/spell-visual client
content that falls outside apps/dbc-tools/generate.py's own pipeline (which owns
Spell.dbc/Talent.dbc/etc. and ships as patch-Z.mpq - see lib/patch_out.py). patch-Y.mpq (GT
combat-rating tables, patch_gt_tables.py) and patch-I.mpq (SpellIcon.dbc + its .blp files,
build_patch_i.py) are the other legs of the same convention. SpellIcon.dbc lives in the same
working-copy directory but is deliberately NOT packed here (NOT_OURS below) - see that comment.

The SPELLS/ half only matters once a DBC row's ModelName/FileName field actually points at one of
these files (see patch_mage_vfx_models.py) - packing an asset the DBCs don't reference yet is
harmless (just unused bytes in the archive), but a DBC row referencing a file that ISN'T packed here
leaves the client with a model path pointing at nothing.

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
    python3 apps/dbc-tools/build_patch_m.py [--dbfilesclient PATH] [--spells PATH] [--deploy-root PATH]

    --dbfilesclient  DBC working-copy directory to package (default:
                      apps/dbc-tools/var/model-visual-dbc/DBFilesClient).
    --spells         Model/skin working-copy directory to package (default:
                      apps/dbc-tools/var/model-visual-dbc/SPELLS). Packed at archive path
                      "SPELLS\\<filename>", matching every FileName/ModelName this pass's DBC rows
                      reference. Skipped (with a note, not an error) if the directory doesn't exist
                      or is empty - earlier patch-M.mpq builds (pre-dating any SPELLS/ content) still
                      work with no flag needed.
    --deploy-root    patch-service PATCH_ROOT to copy patch-M.mpq's Data/ into (default: this
                      box's DEPLOY_ROOT from lib/local_config.py, or no deployment if that file
                      doesn't exist - see lib/local_config.py.example). Pass --deploy-root '' to
                      skip deployment and only (re)build apps/dbc-tools/var/dbc-patch/patch-M.mpq
                      locally.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from lib.mpq_writer import write_mpq

DEFAULT_DBFILESCLIENT = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"
DEFAULT_SPELLS = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "SPELLS"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-M.mpq"

# DBCs that share this working-copy directory but are owned (and shipped) by another patch script.
# The client loads lettered patches alphabetically with later letters overriding earlier ones, so a
# copy of one of these packed here would silently shadow the owning patch's newer copy (patch-M >
# patch-I). That's exactly what blanked every SpellIcon row minted after patch-M's last rebuild -
# see docs/bugs-and-fixes.md ("Custom SpellIcon.dbc rows added after ... render as blank").
NOT_OURS = {
    "spellicon.dbc",  # build_patch_i.py -> patch-I.mpq (must ship next to its .blp files)
}

# Operator-specific and this repo is public on GitHub, so it lives in lib/local_config.py
# (gitignored) rather than here - see that file's docstring / local_config.py.example.
try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbfilesclient", type=Path, default=DEFAULT_DBFILESCLIENT)
    parser.add_argument("--spells", type=Path, default=DEFAULT_SPELLS)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    dbc_files = sorted(p for p in args.dbfilesclient.iterdir()
                       if p.suffix.lower() == ".dbc" and p.name.lower() not in NOT_OURS)
    if not dbc_files:
        raise SystemExit(f"no .dbc files found in {args.dbfilesclient}")

    files = {f"DBFilesClient\\{p.name}": p.read_bytes() for p in dbc_files}

    spell_files = sorted(p for p in args.spells.iterdir() if p.is_file()) if args.spells.is_dir() else []
    files.update({f"SPELLS\\{p.name}": p.read_bytes() for p in spell_files})

    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes) from {len(dbc_files)} DBC + "
          f"{len(spell_files)} SPELLS asset file(s):")
    for p in dbc_files:
        print(f"  DBFilesClient\\{p.name}")
    for p in spell_files:
        print(f"  SPELLS\\{p.name}")
    if not spell_files:
        print(f"  (no SPELLS/ assets found under {args.spells} - only DBCs packed)")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-M.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("(manifest-gen container picks this up on its next timer tick - run "
              "apps/patch-service/manifest_gen.py by hand for an immediate manifest.txt refresh)")


if __name__ == "__main__":
    main()
