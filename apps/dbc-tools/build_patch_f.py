#!/usr/bin/env python3
"""
Bear Form appearances (docs/bear-form-appearances.md): mints the CreatureModelData.dbc /
CreatureDisplayInfo.dbc rows for the player-choosable Bear Form looks, emits their server-side SQL
overlay, and packages the underlying model/skin/anim/texture files into patch-F.mpq ("F" = forms -
Cat Form's equivalent set can join the same archive later).

Every row is cloned verbatim from the Ascension client backup's own live, working
CreatureModelData/CreatureDisplayInfo rows (its patch-M.MPQ) - only the IDs are remapped into this
project's custom range. Those rows answered what docs/ascension-asset-mining.md Part 2 left open:
artifact7-12 are not separate looks but per-colour geometry variants of the artifact3/artifact4
sets, so every mined display has a real texture on disk. Deliberately left out, each for a checked
reason:
  - Worgen bears and the Night Elf / Tauren "Epic" armored bears: Ascension has DBC rows for them
    but their .m2 files are nowhere in the backup.
  - druidbear2_Pantheon: its only display needs a custom ParticleColor.dbc row (1994) this project
    doesn't have.
  - The plain druidbear2 / druidbeartauren2 / ... base models: no Ascension display row uses them.
  - Stock bears (Night Elf 29413-29417, Tauren 2289 + 29418-29421): already in the 3.3.5a client,
    offered as-is by the NPC with no new rows.

The file list is derived, not hand-kept: for each model, its .m2 plus every NN.skin / NNNN-NN.anim
sibling, each display's TextureVariation .blp files, and every hardcoded texture path in the .m2's
own texture table (particle/reflection maps). A path found in no Ascension archive fails the run
unless it's listed in STOCK_CLIENT_FILES.

This script owns patch-F.mpq only. The two DBCs it edits live in the shared working copy that
build_patch_m.py packs into patch-M.mpq, so run build_patch_m.py afterwards to ship them.

IDs: 90100-90199 is reserved for Bear Form appearances in both tables (90001-90004 are the Mage /
Priest VFX rows). The display IDs are mirrored in src/server/scripts/Custom/
custom_shapeshift_appearance.cpp - keep the two in sync.

Usage:
    python3 apps/dbc-tools/build_patch_f.py [--sql-out PATH] [--deploy-root PATH]

    --sql-out        Write the matching server-side SQL migration (creaturemodeldata_dbc /
                     creaturedisplayinfo_dbc) to this path.
    --deploy-root    patch-service PATCH_ROOT to copy patch-F.mpq's Data/ into (default: this box's
                     DEPLOY_ROOT from lib/local_config.py). Pass --deploy-root '' to only build
                     apps/dbc-tools/var/dbc-patch/patch-F.mpq locally.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.mpq_writer import write_mpq
from lib.sql_out import _table_block

ASCENSION_DATA = Path("/mnt/drive6/Permaseeds/AscensionBackup/Data")
WORKING_DBC_DIR = Path(__file__).resolve().parent / "var" / "model-visual-dbc" / "DBFilesClient"
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-F.mpq"

try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None

# Hardcoded textures some models reference that the stock 3.3.5a client already ships.
STOCK_CLIENT_FILES = {
    "particles\\breath24.blp",  # common.MPQ
}

# Ascension CreatureModelData ID -> our CreatureModelData ID.
MODELS = {
    3517: 90100,   # Creature\DruidBearTroll\DruidBearTroll
    4665: 90101,   # Creature\DruidBearTroll\DruidBearTrollEpic
    5708: 90102,   # druidbear2_artifact1
    5709: 90103,   # druidbear2_artifact2
    5710: 90104,   # druidbear2_artifact3
    5711: 90105,   # druidbear2_artifact4
    5712: 90106,   # druidbear2_artifact5
    5707: 90107,   # druidbear2_artifact6
    5713: 90108,   # druidbear2_artifact7  (artifact4, green)
    5714: 90109,   # druidbear2_artifact8  (artifact4, blue)
    5715: 90110,   # druidbear2_artifact9  (artifact4, brown)
    5720: 90111,   # druidbear2_artifact10 (artifact3, green)
    5721: 90112,   # druidbear2_artifact11 (artifact3, purple)
    5722: 90113,   # druidbear2_artifact12 (artifact3, red)
    5733: 90114,   # druidbearkultiran
    10874: 90115,  # druidbearzandalaritroll
    5734: 90116,   # druidbearzandalaritroll_noarmor
}

# (our CreatureDisplayInfo ID, Ascension CreatureDisplayInfo ID). Append-only: the IDs are what
# character_shapeshift_appearance rows store.
DISPLAYS = (
    # Troll
    (90100, 33655), (90101, 33656), (90102, 33657), (90103, 33658), (90104, 33659),
    # Armored Troll
    (90105, 43746), (90106, 43747), (90107, 43748), (90108, 43749), (90109, 43750),
    # Claws of Ursoc I (artifact1)
    (90110, 48836), (90111, 48837), (90112, 48838), (90113, 48839),
    (90114, 48840), (90115, 48841), (90116, 48842), (90117, 48843),
    # Claws of Ursoc II (artifact2)
    (90118, 48844), (90119, 48845), (90120, 48846), (90121, 48847),
    # Claws of Ursoc III (artifact3 / 10 / 11 / 12)
    (90122, 48848), (90123, 48849), (90124, 48850), (90125, 48851),
    # Claws of Ursoc IV (artifact8 / 9 / 7 / 4)
    (90126, 48852), (90127, 48853), (90128, 48854), (90129, 48855),
    # Claws of Ursoc V (artifact5)
    (90130, 48856), (90131, 48857), (90132, 48858), (90133, 48859),
    # Claws of Ursoc VI (artifact6)
    (90134, 48832), (90135, 48833), (90136, 48834), (90137, 48835),
    # Kul Tiran
    (90138, 48895), (90139, 48896), (90140, 48897), (90141, 48898),
    # Zandalari
    (90142, 84867), (90143, 84868), (90144, 84869), (90145, 84870),
    # Zandalari, unarmored
    (90146, 48899), (90147, 48900), (90148, 48901), (90149, 48902),
)

ID_RANGE = {"start": 90100, "end": 90199}


def _smpq(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["smpq", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _archive_priority(name: str) -> tuple:
    """Client load order: base archives, numbered patches, then lettered ones - later wins."""
    base = ["common.mpq", "common-2.mpq", "expansion.mpq", "lichking.mpq", "patch.mpq"]
    lower = name.lower()
    if lower in base:
        return (0, base.index(lower), "")
    stem = lower.removeprefix("patch-").removesuffix(".mpq")
    return (1, 0, stem) if stem.isdigit() else (2, 0, stem)


def index_archives() -> dict[str, tuple[Path, str]]:
    """lowercase backslash path -> (archive, path as stored), highest-priority archive winning."""
    archives = sorted((p for p in ASCENSION_DATA.iterdir() if p.suffix.lower() == ".mpq"),
                      key=lambda p: _archive_priority(p.name))
    index = {}
    for archive in archives:
        for line in _smpq("-l", str(archive)).splitlines():
            path = line.split()[-1] if line.strip() else ""
            if path:
                index[path.replace("/", "\\").lower()] = (archive, path)
    return index


def extract(index: dict, paths: set[str], workdir: Path) -> dict[str, bytes]:
    by_archive: dict[Path, list[str]] = {}
    for path in paths:
        archive, stored = index[path]
        by_archive.setdefault(archive, []).append(stored)
    out = {}
    for archive, stored_paths in by_archive.items():
        dest = workdir / archive.name
        dest.mkdir(parents=True, exist_ok=True)
        _smpq("-x", str(archive), *stored_paths, cwd=dest)
        for stored in stored_paths:
            out[stored.replace("/", "\\")] = (dest / stored).read_bytes()
    return out


def m2_hardcoded_textures(m2: bytes) -> list[str]:
    """Filenames of type-0 (hardcoded) entries in a WotLK (v264) M2's texture table."""
    if m2[:4] != b"MD20":
        raise SystemExit("not an MD20 model")
    count, offset = struct.unpack_from("<II", m2, 80)
    names = []
    for i in range(count):
        tex_type, _flags, length, name_offset = struct.unpack_from("<IIII", m2, offset + 16 * i)
        if tex_type == 0:
            names.append(m2[name_offset:name_offset + length].rstrip(b"\0").decode("latin1"))
    return names


def build_rows(asc_dir: Path) -> tuple[list[dict], list[dict]]:
    asc_models = {r["ID"]: r for r in dbcfile.read_dbc(asc_dir / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA)}
    asc_displays = {r["ID"]: r for r in dbcfile.read_dbc(asc_dir / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO)}
    model_rows = [{**asc_models[asc_id], "ID": our_id} for asc_id, our_id in MODELS.items()]
    display_rows = []
    for our_id, asc_id in DISPLAYS:
        row = asc_displays[asc_id]
        display_rows.append({**row, "ID": our_id, "ModelID": MODELS[row["ModelID"]]})
    return model_rows, display_rows


def asset_paths(index: dict, model_rows: list[dict], display_rows: list[dict], workdir: Path) -> set[str]:
    wanted: set[str] = set()
    textures_by_model: dict[int, set[str]] = {}
    for d in display_rows:
        textures_by_model.setdefault(d["ModelID"], set()).update(
            d[f"TextureVariation_{i}"] for i in (1, 2, 3) if d[f"TextureVariation_{i}"])

    for m in model_rows:
        base = os.path.splitext(m["ModelName"].lower())[0]
        folder = base.rsplit("\\", 1)[0]
        m2_path = base + ".m2"
        if m2_path not in index:
            raise SystemExit(f"model {m['ID']}: {m2_path} not found in any archive")
        wanted.add(m2_path)
        # NN.skin / NNNN-NN.anim siblings - the digit check keeps druidbear2_artifact1 from also
        # sweeping in druidbear2_artifact10..12.
        wanted.update(p for p in index if p.startswith(base) and p[len(base):len(base) + 1].isdigit()
                      and p.endswith((".skin", ".anim")))
        wanted.update(f"{folder}\\{t.lower()}.blp" for t in textures_by_model[m["ID"]])
        m2 = extract(index, {m2_path}, workdir)
        wanted.update(t.lower() for t in m2_hardcoded_textures(next(iter(m2.values()))))

    missing = sorted(p for p in wanted - STOCK_CLIENT_FILES if p not in index)
    if missing:
        raise SystemExit("not found in any Ascension archive:\n  " + "\n  ".join(missing))
    return wanted - STOCK_CLIENT_FILES


def _merge(path: Path, table: dbcfmt.DbcTable, new_rows: list[dict]) -> bool:
    """Make our ID range hold exactly new_rows (idempotent reruns; drops rows retired from here)."""
    existing = dbcfile.read_dbc(path, table)
    in_range = [r for r in existing if ID_RANGE["start"] <= r["ID"] <= ID_RANGE["end"]]
    key = lambda r: r["ID"]  # noqa: E731
    if sorted(in_range, key=key) == sorted(new_rows, key=key):
        return False
    kept = [r for r in existing if not ID_RANGE["start"] <= r["ID"] <= ID_RANGE["end"]]
    dbcfile.write_dbc(path, table, kept + new_rows)
    return True


def _signed(value):
    """creaturedisplayinfo_dbc's integer columns are signed `int`; Ascension stores -1 sentinels
    (BloodLevel on most of its rows) as 0xFFFFFFFF, which MySQL rejects as out of range."""
    return value - (1 << 32) if isinstance(value, int) and value > 0x7FFFFFFF else value


def build_pending_sql(model_rows: list[dict], display_rows: list[dict]) -> str:
    sql_display_rows = [{k: _signed(v) for k, v in r.items()} for r in display_rows]
    blocks = [
        _table_block(dbcfmt.CREATUREMODELDATA, ID_RANGE, model_rows, []),
        _table_block(dbcfmt.CREATUREDISPLAYINFO, ID_RANGE, sql_display_rows, []),
    ]
    return "\n\n".join(blocks) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sql-out", type=Path, default=None)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        asc_dbc = workdir / "ascension-dbc"
        asc_dbc.mkdir()
        _smpq("-x", str(ASCENSION_DATA / "patch-M.MPQ"),
              "DBFilesClient/CreatureModelData.dbc", "DBFilesClient/CreatureDisplayInfo.dbc", cwd=asc_dbc)
        model_rows, display_rows = build_rows(asc_dbc / "DBFilesClient")

        index = index_archives()
        paths = asset_paths(index, model_rows, display_rows, workdir / "m2")
        files = extract(index, paths, workdir / "assets")

    changed = _merge(WORKING_DBC_DIR / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA, model_rows)
    changed |= _merge(WORKING_DBC_DIR / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO, display_rows)
    print(f"{len(model_rows)} model + {len(display_rows)} display row(s) "
          f"{'written to' if changed else 'already current in'} {WORKING_DBC_DIR} "
          f"- run build_patch_m.py to ship them")

    if args.sql_out:
        args.sql_out.write_text(build_pending_sql(model_rows, display_rows))
        print(f"wrote server-side SQL -> {args.sql_out}")

    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes) from {len(files)} asset file(s)")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-F.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")


if __name__ == "__main__":
    main()
