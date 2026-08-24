"""
Places already-built DBC binaries (see dbcfile.write_dbc) into the client
patch outputs. See docs/dbc-build-pipeline.md, "Client patch delivery
decision": both loose files and an MPQ are produced every run, not either/or.
"""

from __future__ import annotations

from pathlib import Path

from .mpq_writer import write_mpq

# Anchored to the repo root (matching state.py's REPO_ROOT), not left as a bare
# relative path: a bare "var/dbc-patch" resolves against the *current working
# directory* generate.py happens to be invoked from, not the repo — running it
# via `python3 apps/dbc-tools/generate.py` from the repo root vs. `cd
# apps/dbc-tools && python3 generate.py` silently wrote to two different
# directories (apps/dbc-tools/var/dbc-patch/ vs. var/dbc-patch/), and a stale
# copy in the former sat undetected as the one actually getting deployed to a
# client. See docs/single-rank-spell-system.md's tooltip-corruption note.
REPO_ROOT = Path(__file__).resolve().parents[3]
PATCH_ROOT = REPO_ROOT / "var" / "dbc-patch"
LOOSE_DIR = PATCH_ROOT / "DBFilesClient"
MPQ_PATH = PATCH_ROOT / "patch-Z.mpq"
ENV_DBC_DIR = REPO_ROOT / "env" / "dist" / "data" / "dbc"


def write_patch(dbc_files: dict[str, bytes]) -> dict:
    """`dbc_files`: {"Spell.dbc": bytes, ...}. Returns a small report dict of
    what was written, for generate.py to print."""
    report = {"loose": [], "mpq": None, "env_dbc": []}

    for filename, blob in dbc_files.items():
        out = LOOSE_DIR / filename
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(blob)
        report["loose"].append(str(out))

    write_mpq(MPQ_PATH, {f"DBFilesClient\\{name}": blob for name, blob in dbc_files.items()})
    report["mpq"] = str(MPQ_PATH)

    if ENV_DBC_DIR.is_dir():
        for filename, blob in dbc_files.items():
            out = ENV_DBC_DIR / filename
            out.write_bytes(blob)
            report["env_dbc"].append(str(out))

    return report
