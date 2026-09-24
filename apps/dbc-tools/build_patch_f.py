#!/usr/bin/env python3
"""
Shapeshift appearances (docs/shapeshift-appearances.md): mints the CreatureModelData.dbc /
CreatureDisplayInfo.dbc rows for the player-choosable Bear, Cat and Moonkin Form looks, emits
their server-side SQL overlay, and packages the underlying model/skin/anim/texture files into patch-F.mpq
("F" = forms).

Every row is cloned verbatim from the Ascension client backup's own live, working
CreatureModelData/CreatureDisplayInfo rows (its patch-M.MPQ) - only the IDs are remapped into this
project's custom range. Those rows answered what docs/ascension-asset-mining.md Part 2 left open:
artifact7-12 are not separate looks but per-colour geometry variants of the artifact3/artifact4
sets (the cat's artifact6-8 likewise belong to artifact2), so every mined display has a real
texture on disk. Deliberately left out, each for a checked reason:
  - Worgen bears/cats and the Night Elf / Tauren "Epic" armored bears/cats: Ascension has DBC rows
    for them but their .m2 files are nowhere in the backup.
  - druidbear2_Pantheon: its only display needs a custom ParticleColor.dbc row (1994) this project
    doesn't have.
  - The plain druidbear2 / druidbeartauren2 / ... base models: no Ascension display row uses them.
  - Moonkin: the Cata black/red recolours and every "Epic" armored moonkin on the original
    DruidOwlBear model (textures / .m2 missing), and the Kul Tiran moonkin (.m2 missing). The
    Zandalari moonkin's files exist (patch-CZ) but no Ascension display row uses them. Ascension also
    ships its own copy of the stock DruidOwlBear.m2 - never packed, since nothing here references it.
  - Stock bears (Night Elf 29413-29417, Tauren 2289 + 29418-29421), stock cats (Night Elf 892 +
    29405-29408, Tauren 8571 + 29409-29412), the stock Lynx (15593 red, 18167 yellow) and stock
    moonkin (Night Elf 15374, Tauren 15375): already in the 3.3.5a client, offered as-is by the NPC
    with no new rows.

The painted Lynx is the one display built on a *stock* model (DruidCat_Legacy, 3143): Ascension
gave it a duplicate model row, but only its texture is new, so STOCK_MODELS points it back at 3143
and just the .blp ships.

The file list is derived, not hand-kept: for each model, its .m2 plus every NN.skin / NNNN-NN.anim
sibling, each display's TextureVariation .blp files, and every hardcoded texture path in the .m2's
own texture table (particle/reflection maps). A path found in no Ascension archive fails the run
unless it's listed in STOCK_CLIENT_FILES.

This script owns patch-F.mpq only. The two DBCs it edits live in the shared working copy that
build_patch_m.py packs into patch-M.mpq, so run build_patch_m.py afterwards to ship them.

IDs, in both tables: 90100-90199 Bear Form, 90200-90299 Cat Form, 90300-90399 Moonkin Form
(90001-90004 are the Mage / Priest VFX rows). The display IDs are mirrored in src/server/scripts/
Custom/custom_shapeshift_appearance.cpp - keep the two in sync. --sql-out always emits the whole
ID_RANGE, so the newest generated migration is the complete state.

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

# The stock 3.3.5a client's own archive names; Ascension's copies of these carry no custom content.
BLIZZARD_ARCHIVES = {"common.mpq", "common-2.mpq", "expansion.mpq", "lichking.mpq", "patch.mpq", "patch-2.mpq",
                     "patch-3.mpq"}

# Textures the mined models/displays reference that the stock 3.3.5a client already ships.
STOCK_CLIENT_FILES = {
    "particles\\breath24.blp",            # common.MPQ
    "creature\\druidcat\\lynxeyeglow.blp",  # common.MPQ
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

    3519: 90200,   # Creature\DruidCatTroll\DruidCatTroll
    4670: 90201,   # Creature\DruidCatTroll\DruidCatTrollEpic
    5723: 90202,   # druidcat2_artifact1
    5724: 90203,   # druidcat2_artifact2 (artifact2, blue)
    5725: 90204,   # druidcat2_artifact3
    5726: 90205,   # druidcat2_artifact4
    5727: 90206,   # druidcat2_artifact5
    5728: 90207,   # druidcat2_artifact6 (artifact2, green)
    5729: 90208,   # druidcat2_artifact7 (artifact2, purple)
    5730: 90209,   # druidcat2_artifact8 (artifact2, red)
    10990: 90210,  # druidcatkultiran
    5735: 90211,   # druidcatkultiran_noarmor
    10911: 90212,  # druidcatzandalaritroll
    5736: 90213,   # druidcatzandalaritroll_noarmor
    204963: 90214,  # druidcat2_tree

    5744: 90300,   # druidowlbear2
    5745: 90301,   # druidowlbear2\druidowlbearepic2
    5746: 90302,   # druidowlbearhmtauren2
    5747: 90303,   # druidowlbearhmtaurenepic2
    5740: 90304,   # druidowlbearkultiranepic2
    5741: 90305,   # druidowlbearzandalariepic2
    5925: 90306,   # tindralmoonkin\blue_tindralmoonkin
    5926: 90307,   # tindralmoonkin\green_tindralmoonkin
    5927: 90308,   # tindralmoonkin\purple_tindralmoonkin
    5928: 90309,   # tindralmoonkin\red_tindralmoonkin
    5929: 90310,   # tindralmoonkin\yellow_tindralmoonkin
}

# Ascension CreatureModelData ID -> the stock client model it duplicates. Displays on these keep
# pointing at the stock row; only their textures ship.
STOCK_MODELS = {
    87274: 3143,   # Creature\DRUIDCAT\DruidCat_Legacy (Lynx)
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

    # --- Cat Form ---
    # Troll
    (90200, 33665), (90201, 33666), (90202, 33667), (90203, 33668), (90204, 33669),
    # Armored Troll
    (90205, 43775), (90206, 43773), (90207, 43778), (90208, 43776), (90209, 43777),
    # Fangs of Ashamane I (artifact1)
    (90210, 48870), (90211, 48869), (90212, 48868), (90213, 48867),
    (90214, 48866), (90215, 48865), (90216, 48864),
    # Fangs of Ashamane II (artifact2 / 6 / 7 / 8)
    (90217, 48874), (90218, 48873), (90219, 48872), (90220, 48871),
    # Fangs of Ashamane III (artifact3)
    (90221, 48878), (90222, 48877), (90223, 48876), (90224, 48875),
    # Fangs of Ashamane IV (artifact4)
    (90225, 48882), (90226, 48881), (90227, 48880), (90228, 48879),
    # Fangs of Ashamane V (artifact5)
    (90229, 48886), (90230, 48885), (90231, 48884), (90232, 48883),
    # Kul Tiran
    (90233, 86100), (90234, 86524), (90235, 86525), (90236, 86526),
    # Kul Tiran, unarmored
    (90237, 48903), (90238, 48904), (90239, 48905), (90240, 48906),
    # Zandalari
    (90241, 85194), (90242, 85195), (90243, 85196), (90244, 85197),
    # Zandalari, unarmored
    (90245, 48907), (90246, 48908), (90247, 48909), (90248, 48910),
    # Treant
    (90249, 80719),
    # Lynx, painted (stock model 3143)
    (90250, 87274),

    # --- Moonkin Form ---
    # Moonkin (druidowlbear2): Night Elf, Black, Blue, Raven, Red
    (90300, 48933), (90301, 48935), (90302, 48934), (90303, 48932), (90304, 48931),
    # Armored Moonkin (druidowlbearepic2), same colours
    (90305, 48938), (90306, 48940), (90307, 48939), (90308, 48937), (90309, 48936),
    # Highmountain: unarmored, armored
    (90310, 48941), (90311, 48942),
    # Kul Tiran, armored: Black, Green, Pale, Red
    (90312, 48916), (90313, 48917), (90314, 48918), (90315, 48919),
    # Zandalari, armored
    (90316, 48920),
    # Tindral Sageswift: Blue, Green, Purple, Red, Gold (one model per colour)
    (90317, 110039), (90318, 110040), (90319, 110041), (90320, 110042), (90321, 110043),
)

ID_RANGE = {"start": 90100, "end": 90399}


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


def build_rows(asc_dir: Path) -> tuple[list[dict], list[dict], dict[int, str]]:
    """Returns (model rows, display rows, ModelName by model ID) - the last also covers the stock
    models STOCK_MODELS displays sit on, since their textures live next to that model."""
    asc_models = {r["ID"]: r for r in dbcfile.read_dbc(asc_dir / "CreatureModelData.dbc", dbcfmt.CREATUREMODELDATA)}
    asc_displays = {r["ID"]: r for r in dbcfile.read_dbc(asc_dir / "CreatureDisplayInfo.dbc", dbcfmt.CREATUREDISPLAYINFO)}
    model_rows = [{**asc_models[asc_id], "ID": our_id} for asc_id, our_id in MODELS.items()]
    model_names = {m["ID"]: m["ModelName"] for m in model_rows}
    model_names.update({stock_id: asc_models[asc_id]["ModelName"] for asc_id, stock_id in STOCK_MODELS.items()})
    display_rows = []
    for our_id, asc_id in DISPLAYS:
        row = asc_displays[asc_id]
        model_id = MODELS.get(row["ModelID"]) or STOCK_MODELS[row["ModelID"]]
        display_rows.append({**row, "ID": our_id, "ModelID": model_id})
    return model_rows, display_rows, model_names


def asset_paths(index: dict, model_rows: list[dict], display_rows: list[dict], model_names: dict[int, str],
                workdir: Path) -> set[str]:
    wanted: set[str] = set()

    for m in model_rows:
        base = os.path.splitext(m["ModelName"].lower())[0]
        m2_path = base + ".m2"
        if m2_path not in index:
            raise SystemExit(f"model {m['ID']}: {m2_path} not found in any archive")
        wanted.add(m2_path)
        # NN.skin / NNNN-NN.anim siblings - the digit check keeps druidbear2_artifact1 from also
        # sweeping in druidbear2_artifact10..12.
        wanted.update(p for p in index if p.startswith(base) and p[len(base):len(base) + 1].isdigit()
                      and p.endswith((".skin", ".anim")))
        m2 = extract(index, {m2_path}, workdir)
        wanted.update(t.lower() for t in m2_hardcoded_textures(next(iter(m2.values()))))

    # TextureVariation names resolve against the model's own folder
    for d in display_rows:
        folder = model_names[d["ModelID"]].lower().rsplit("\\", 1)[0]
        wanted.update(f"{folder}\\{d[f'TextureVariation_{i}'].lower()}.blp"
                      for i in (1, 2, 3) if d[f"TextureVariation_{i}"])

    wanted -= STOCK_CLIENT_FILES
    missing = sorted(p for p in wanted if p not in index)
    if missing:
        raise SystemExit("not found in any Ascension archive:\n  " + "\n  ".join(missing))
    # Ascension's copies of the Blizzard base archives only hold stock client files - shipping one
    # would just shadow the client's own copy. List it in STOCK_CLIENT_FILES instead.
    stock = sorted(p for p in wanted if index[p][0].name.lower() in BLIZZARD_ARCHIVES)
    if stock:
        raise SystemExit("resolved to a Blizzard base archive (add to STOCK_CLIENT_FILES?):\n  "
                         + "\n  ".join(stock))
    return wanted


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
        model_rows, display_rows, model_names = build_rows(asc_dbc / "DBFilesClient")

        index = index_archives()
        paths = asset_paths(index, model_rows, display_rows, model_names, workdir / "m2")
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
