"""
MPQ v1 client patch archive writer — thin wrapper around `smpq` (StormLib's
CLI archiving tool), not a hand-rolled implementation.

This used to be a from-scratch, store-only, single-unit-only MPQ writer.
Confirmed via live-client testing that it was flat-out broken: `Talent.dbc`
alone (no Spell.dbc involved at all) reproduced the exact same "every class's
talent tree renders almost empty, no client errors" failure the whole
investigation started from, while a `Talent.dbc` packed by real StormLib
(same bytes, same MPQ v1 header format, same store/single-unit settings) did
not — see docs/dbc-build-pipeline.md's "MPQ writer replaced" note for the
full story. The custom writer's own docstring admitted the real problem
retroactively: it was "enough to package a handful of small DBC files," which
was never actually verified against a live client for anything Talent.dbc's
size or structure, only round-tripped through community Python readers
(mpyq) that don't reject what a real client does.

Rather than debug a hand-rolled implementation against an undocumented,
closed-source client further, this shells out to `smpq` — built on StormLib,
the reference MPQ implementation the WoW-modding ecosystem (including
Blizzard's own tooling lineage) actually uses.

Setup: `sudo apt-get install smpq` (Debian/Ubuntu; pulls in `libstorm9`,
`libtomcrypt1`, `libtommath1` as dependencies). No `pip`/PyPI package exists
for this — it's a system binary, not a Python library. If `sudo` isn't
available, `apt-get download smpq libstorm9 libtomcrypt1 libtommath1` +
`dpkg-deb -x <pkg>.deb <dir>` per package works without root; point
`AC_SMPQ_BIN`/`LD_LIBRARY_PATH` at the extracted `usr/bin/smpq` and
`usr/lib(/x86_64-linux-gnu)` if it's not going through a normal system
install.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def _find_smpq() -> str:
    import os

    override = os.environ.get("AC_SMPQ_BIN")
    if override and Path(override).is_file():
        return override
    found = shutil.which("smpq")
    if found:
        return found
    raise RuntimeError(
        "smpq not found on PATH (and $AC_SMPQ_BIN not set). Install it: "
        "`sudo apt-get install smpq` (Debian/Ubuntu). See this file's module "
        "docstring for the no-root fallback via `apt-get download` + `dpkg-deb -x`."
    )


def write_mpq(path: Path, files: dict[str, bytes]) -> None:
    """Write `files` (archive-relative-path, backslash-separated -> bytes) as an MPQ v1 archive
    to `path`, via `smpq`. Overwrites `path` if it already exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    smpq = _find_smpq()

    with tempfile.TemporaryDirectory(prefix="dbc-patch-mpq-") as tmp:
        tmp_path = Path(tmp)
        rel_paths = []
        for name, blob in files.items():
            rel = name.replace("\\", "/")
            out = tmp_path / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(blob)
            rel_paths.append(rel)

        if path.exists():
            path.unlink()

        subprocess.run(
            [
                smpq, "-c",  # create
                "-M", "1",  # MPQ v1 header (max compatibility - 3.3.5a doesn't need v2+)
                "-C", "none",  # store, no compression - these are small/moderate DBC files
                "-O", "0",  # neutral locale
                "-q",  # quiet
                str(path.resolve()),
                *rel_paths,
            ],
            cwd=tmp_path,
            check=True,
        )
