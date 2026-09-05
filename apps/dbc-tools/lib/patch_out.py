"""
Places already-built DBC binaries (see dbcfile.write_dbc) into the client
patch outputs. See docs/dbc-build-pipeline.md, "Client patch delivery
decision": both loose files and an MPQ are produced every run, not either/or.
"""

from __future__ import annotations

import shutil
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

# This machine's patch-distribution root (see apps/patch-service/README.md) - not a repo path,
# just this box's deploy target so testers' patch-client.bat picks up a fresh patch-Z.mpq via
# patch-service's timer-driven manifest_gen.py, without anyone manually copying the file over.
# Same DEFAULT_DEPLOY_ROOT convention apps/dbc-tools/build_patch_m.py and patch_gt_tables.py
# already use for their own patch-M.mpq/patch-Y.mpq in the same Data/ directory - patch-Z is the
# one this pipeline (generate.py) owns, so it deploys unconditionally here rather than needing a
# --deploy-root flag like those two standalone scripts (generate.py takes no CLI args at all).
# Guarded by an existence check, not created if missing, so a checkout on a machine without this
# host's patch-service setup doesn't fail or scatter a stray directory.
DEPLOY_ROOT = Path("/home/plex/wow_server/patch-root")
DEPLOY_MPQ = DEPLOY_ROOT / "Data" / "patch-Z.mpq"


def write_patch(dbc_files: dict[str, bytes]) -> dict:
    """`dbc_files`: {"Spell.dbc": bytes, ...}. Returns a small report dict of
    what was written, for generate.py to print."""
    report = {"loose": [], "mpq": None, "env_dbc": [], "deploy_mpq": None}

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

    if DEPLOY_ROOT.is_dir():
        DEPLOY_MPQ.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MPQ_PATH, DEPLOY_MPQ)
        report["deploy_mpq"] = str(DEPLOY_MPQ)

    return report
