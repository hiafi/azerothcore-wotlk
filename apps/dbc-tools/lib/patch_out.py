"""
Places already-built DBC binaries (see dbcfile.write_dbc) into the client
patch outputs. See docs/dbc-build-pipeline.md, "Client patch delivery
decision": both loose files and an MPQ are produced every run, not either/or.
"""

from __future__ import annotations

from pathlib import Path

from .mpq_writer import write_mpq

PATCH_ROOT = Path("var/dbc-patch")
LOOSE_DIR = PATCH_ROOT / "DBFilesClient"
MPQ_PATH = PATCH_ROOT / "patch-Z.mpq"
ENV_DBC_DIR = Path("env/dist/data/dbc")


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
