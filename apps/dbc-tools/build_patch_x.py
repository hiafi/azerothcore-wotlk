#!/usr/bin/env python3
"""
Packs the client UI overrides (client/ui-overrides/Interface/**) into patch-X.mpq and deploys it.

patch-X is the one archive for every whole-file FrameXML override (UI-unlocked Wow.exe only; the stock exe rejects
modified FrameXML - see client/ui-overrides/README.md): UnitPopup.lua (level-60 dungeon/raid difficulty menu), the item
tier label hook ItemTierLabel.lua, its generated table ItemTierLabels.lua (generate.py writes it, lib/item_labels.py)
and the FrameXML.toc override that loads the two after the tooltip frames. It replaces the hand `smpq -c` line the
README used to carry. Everything under Interface/ is packed at its path relative to the source directory; other files
there (README.md) are not.

Same packer and archive settings as the other build_patch_*.py (lib/mpq_writer.write_mpq: MPQ v1, stored, neutral
locale), so the hand-built archive and this one differ only in file order.

Usage:
    python3 apps/dbc-tools/build_patch_x.py [--source DIR] [--out PATH] [--deploy-root PATH]

    --source       UI override tree to pack (default: client/ui-overrides).
    --out          Where to write the archive (default: apps/dbc-tools/var/dbc-patch/patch-X.mpq).
    --deploy-root  patch-service PATCH_ROOT to copy patch-X.mpq's Data/ into (default: this box's DEPLOY_ROOT from
                    lib/local_config.py, or no deployment if that file doesn't exist - see
                    lib/local_config.py.example). Pass --deploy-root '' to only build.

After a deploy, refresh the patch manifest inside the container (host-side manifest_gen.py writes the wrong place, see
docs/bugs-and-fixes.md): `docker exec patch-manifest-gen python3 /manifest_gen.py`. Test on one client before the
refresh: a Lua error in FrameXML breaks that player's whole UI.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from lib.mpq_writer import write_mpq

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "client" / "ui-overrides"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-X.mpq"
TOC = "Interface/FrameXML/FrameXML.toc"
# Files the toc override must list when they exist: a Lua file the toc forgets never loads, silently.
TOC_LISTED = ("ItemTierLabels.lua", "ItemTierLabel.lua")

try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None


def collect(source: Path) -> dict[str, bytes]:
    """Archive path (backslash-separated) -> bytes for every file under `source`/Interface."""
    interface = source / "Interface"
    if not interface.is_dir():
        raise SystemExit(f"no Interface/ directory under {source}")
    files = {
        "\\".join(p.relative_to(source).parts): p.read_bytes()
        for p in sorted(interface.rglob("*")) if p.is_file()
    }
    if not files:
        raise SystemExit(f"no files under {interface}")
    return files


def check_toc(source: Path, files: dict[str, bytes]) -> list[str]:
    """Problems with the toc override: a listed-when-present Lua file missing from it, or a toc entry with no file."""
    toc = files.get(TOC.replace("/", "\\"))
    if toc is None:
        return []
    listed = {line.strip() for line in toc.decode("utf-8").splitlines()}
    framexml = source / "Interface" / "FrameXML"
    problems = []
    for name in TOC_LISTED:
        present = (framexml / name).is_file()
        if present and name not in listed:
            problems.append(f"{TOC} does not list {name}")
        if name in listed and not present:
            problems.append(f"{TOC} lists {name}, which is not in {framexml}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=LOCAL_OUT)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    files = collect(args.source)
    problems = check_toc(args.source, files)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    write_mpq(args.out, files)
    print(f"built {args.out} ({args.out.stat().st_size} bytes) from {len(files)} file(s):")
    for name in files:
        print(f"  {name}")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-X.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.out, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("refresh the manifest: docker exec patch-manifest-gen python3 /manifest_gen.py")
    else:
        print("not deployed (no lib/local_config.py DEPLOY_ROOT and no --deploy-root)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
