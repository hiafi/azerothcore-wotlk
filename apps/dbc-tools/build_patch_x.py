#!/usr/bin/env python3
"""
Packs the client UI overrides (client/ui-overrides/Interface/**) into patch-X.mpq; deploys it only with --deploy.

patch-X is the one archive for every whole-file FrameXML override (UI-unlocked Wow.exe only; the stock exe rejects
modified FrameXML - see client/ui-overrides/README.md): UnitPopup.lua (level-60 dungeon/raid difficulty menu), the item
tier label hook ItemTierLabel.lua, its generated table ItemTierLabels.lua (generate.py writes it, lib/item_labels.py)
and the FrameXML.toc override that loads the two after the tooltip frames. It replaces the hand `smpq -c` line the
README used to carry. Every UI file under Interface/ (PACKED_SUFFIXES: .lua .xml .toc .blp .tga) is packed at its path
relative to the source directory; dotfiles, editor swap and backup files (.swp, .orig, ~) and files outside
Interface/ (README.md) are not.

Same packer and archive settings as the other build_patch_*.py (lib/mpq_writer.write_mpq: MPQ v1, stored, neutral
locale), so the hand-built archive and this one differ only in file order.

Usage:
    python3 apps/dbc-tools/build_patch_x.py [--source DIR] [--out PATH] [--deploy [--deploy-root PATH]]

    --source       UI override tree to pack (default: client/ui-overrides).
    --out          Where to write the archive (default: apps/dbc-tools/var/dbc-patch/patch-X.mpq).
    --deploy       Also copy the archive into the patch-service root, so every client downloads it on the next
                   manifest tick. Without it the archive is only built (R1 S4): test it on one client first.
    --deploy-root  With --deploy: the patch-service PATCH_ROOT whose Data/ receives patch-X.mpq (default: this box's
                   DEPLOY_ROOT from lib/local_config.py; --deploy without either is an error).

A Lua error in FrameXML breaks a player's whole UI, and patch-manifest-gen ships whatever sits in patch-root/Data on
its timer. So: build (no --deploy), copy the archive into ONE client's Data/ by hand, start that client, check the
tooltips and the Lua error frame, and only then run with --deploy and refresh the manifest inside the container
(host-side manifest_gen.py writes the wrong place, see docs/bugs-and-fixes.md):
`docker exec patch-manifest-gen python3 /manifest_gen.py`.
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
# What a UI override can be (R1 N11): anything else under Interface/ (swap files, .orig, notes) is left out.
PACKED_SUFFIXES = (".lua", ".xml", ".toc", ".blp", ".tga")

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
        for p in sorted(interface.rglob("*")) if p.is_file() and packable(p.relative_to(source))
    }
    if not files:
        raise SystemExit(f"no files under {interface}")
    return files


def packable(relative: Path) -> bool:
    """A UI file to pack: no dotfile or dot directory on the way, and a UI file suffix (so no .swp, .orig, ~)."""
    if any(part.startswith(".") for part in relative.parts):
        return False
    return relative.suffix.lower() in PACKED_SUFFIXES


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
    parser.add_argument("--deploy", action="store_true", help="also copy the archive into the patch-service root")
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()
    if args.deploy and not args.deploy_root:
        print("ERROR: --deploy needs a patch-service root: lib/local_config.py DEPLOY_ROOT or --deploy-root",
              file=sys.stderr)
        return 2

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

    if args.deploy:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-X.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.out, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("refresh the manifest: docker exec patch-manifest-gen python3 /manifest_gen.py")
    else:
        print("not deployed (build only). Test it on one client first:")
        print(f"  1. copy {args.out} into that client's Data/ folder (as patch-X.mpq) and start it")
        print("  2. hover items with and without a tier label, open the Lua error frame (/console scriptErrors 1)")
        print("  3. then: build_patch_x.py --deploy, and docker exec patch-manifest-gen python3 /manifest_gen.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
