#!/usr/bin/env python3
"""
Builds patch-W.mpq: world map (M key) maps for the vanilla dungeons and raids, which the stock 3.3.5a client does not
have. The rows and art come from the Ascension client backup, which carries the Cataclysm-era maps backported to
3.3.5a:

- DBFilesClient/WorldMapArea.dbc, DungeonMap.dbc, DungeonMapChunk.dbc: the stock files (highest-priority copy in the
  stock client's Data/enUS/patch-enUS*.MPQ / locale-enUS.MPQ) plus Ascension's rows (its patch-M.MPQ) for the maps in
  VANILLA_MAPS. Stock rows for those maps (only Wailing Caverns has any: one orphan floor, never shown because stock
  has no WorldMapArea row for it) are replaced. Column meanings are in lib/dbcfmt.py (WORLDMAPAREA, DUNGEONMAP,
  DUNGEONMAPCHUNK).
- Interface/WorldMap/<AreaName>/<AreaName><floor>_<1..12>.blp (a map without floors: <AreaName><1..12>.blp): the
  tiles every imported row needs, from Ascension's patch-A.MPQ. A missing tile stops the build.

Ids: WorldMapArea keeps the ids the rows came with (680-766) except Sunken Temple (WMA_ID_OVERRIDES); DungeonMap
floors are renumbered from 1000 and chunks from 10000 (source/ids.yaml `worldmaparea` / `dungeonmap` /
`dungeonmapchunk`), because Ascension's collide with stock. Stock rows keep their physical order and the new rows go
at the end: stock DungeonMap.dbc and DungeonMapChunk.dbc are not sorted by id, and the order is kept byte for byte.

Floor names: the level dropdown reads DUNGEON_FLOOR_<AREANAME><floor> and falls back to "Level N"
(WorldMapFrame.lua); this patch ships no names, so every imported map shows "Level 1..N".

Nothing changes server-side: AzerothCore loads WorldMapArea.dbc only for zone coordinate conversion and never loads
the other two, so the server's dbc files and the worldmaparea_dbc overlay stay stock.

Usage:
    python3 apps/dbc-tools/build_patch_w.py [--ascension-data DIR] [--stock-data DIR] [--preview DIR]
                                            [--deploy-root PATH]

    --ascension-data  Ascension backup's Data/ (default below).
    --stock-data      A stock 3.3.5a client's Data/ (default below).
    --preview         Also write one PNG per map floor (the 12 tiles stitched, 1002x668) into DIR, for a look at the
                      art without a client.
    --deploy-root     patch-service PATCH_ROOT whose Data/ receives patch-W.mpq (default: DEPLOY_ROOT from
                      lib/local_config.py; '' builds apps/dbc-tools/var/dbc-patch/patch-W.mpq only). After a deploy,
                      refresh the manifest inside the container: docker exec patch-manifest-gen python3
                      /manifest_gen.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from lib import dbcfile, dbcfmt
from lib.mpq_writer import write_mpq

ASCENSION_DATA = Path("/mnt/drive6/Permaseeds/AscensionBackup/Data")
STOCK_DATA = Path("/mnt/drive6/Permaseeds/World of Warcraft 3.3.5a/Data")
ASCENSION_DBC_MPQ = "patch-M.MPQ"  # Ascension's custom DBC archive: its world map tables win over its locale copies
ASCENSION_ART_MPQ = "patch-A.MPQ"  # every Interface/WorldMap tile it ships
# Stock client archives holding DBFilesClient, highest priority first.
STOCK_DBC_MPQS = ("enUS/patch-enUS-3.MPQ", "enUS/patch-enUS-2.MPQ", "enUS/patch-enUS.MPQ", "enUS/locale-enUS.MPQ")
LOCAL_OUT = Path(__file__).resolve().parent / "var" / "dbc-patch" / "patch-W.mpq"

try:
    from lib.local_config import DEPLOY_ROOT as DEFAULT_DEPLOY_ROOT
except ImportError:
    DEFAULT_DEPLOY_ROOT = None

# Every vanilla 5-man and raid instance map. ZF, ZG and AQ20 are outdoor terrain: one WorldMapArea row, no floors.
VANILLA_MAPS = {
    33: "Shadowfang Keep", 34: "The Stockade", 36: "The Deadmines", 43: "Wailing Caverns", 47: "Razorfen Kraul",
    48: "Blackfathom Deeps", 70: "Uldaman", 90: "Gnomeregan", 109: "Sunken Temple", 129: "Razorfen Downs",
    189: "Scarlet Monastery", 209: "Zul'Farrak", 229: "Blackrock Spire", 230: "Blackrock Depths",
    249: "Onyxia's Lair", 289: "Scholomance", 309: "Zul'Gurub", 329: "Stratholme", 349: "Maraudon",
    389: "Ragefire Chasm", 409: "Molten Core", 429: "Dire Maul", 469: "Blackwing Lair", 509: "Ruins of Ahn'Qiraj",
    531: "Temple of Ahn'Qiraj",
}

WORLDMAPAREA_ID_RANGE = (680, 769)
DUNGEONMAP_ID_START, DUNGEONMAP_ID_END = 1000, 1099
DUNGEONMAPCHUNK_ID_START, DUNGEONMAPCHUNK_ID_END = 10000, 11999

# Ascension's own WorldMapArea id for Sunken Temple, moved into the free gap of the Cataclysm-era block.
WMA_ID_OVERRIDES = {2021: 687}
# Ascension leaves Sunken Temple's floors without a parent zone map (0); the zoom-out button should go to the swamp.
# Values are stock WorldMapArea AreaNames, resolved to ids at build time.
DUNGEONMAP_PARENT_OVERRIDES = {109: "SwampOfSorrows"}

TABLES = (dbcfmt.WORLDMAPAREA, dbcfmt.DUNGEONMAP, dbcfmt.DUNGEONMAPCHUNK)
TILES_PER_FLOOR = 12  # 4 x 3 tiles of 256 x 256


def _find_smpq() -> str:
    smpq = shutil.which("smpq")
    if not smpq:
        raise SystemExit("smpq not found on PATH - see lib/mpq_writer.py's docstring for setup")
    return smpq


def list_mpq(mpq: Path) -> list[str]:
    """Archive-relative paths (as stored) of every file in `mpq`."""
    out = subprocess.run([_find_smpq(), "-l", str(mpq)], check=True, capture_output=True, text=True).stdout
    return [line.split()[-1] for line in out.splitlines() if line.strip()]


def extract(mpq: Path, paths: list[str]) -> dict[str, bytes]:
    """{path as given -> bytes} for every path in `paths`, which must exist in `mpq`."""
    with tempfile.TemporaryDirectory(prefix="patch-w-extract-") as tmp:
        tmp_path = Path(tmp)
        subprocess.run([_find_smpq(), "-x", str(mpq), *paths], cwd=tmp_path, check=True, capture_output=True,
                       text=True)
        out = {}
        for rel in paths:
            extracted = tmp_path / rel
            if not extracted.is_file():
                raise SystemExit(f"expected extracted file missing: {rel} (from {mpq})")
            out[rel] = extracted.read_bytes()
        return out


def read_rows(blob: bytes, table: dbcfmt.DbcTable) -> list[dict]:
    with tempfile.NamedTemporaryFile(suffix=".dbc") as f:
        f.write(blob)
        f.flush()
        return dbcfile.read_dbc(Path(f.name), table)


def load_stock_tables(stock_data: Path) -> dict[str, bytes]:
    """{dbc filename -> bytes}: each table's highest-priority copy in the stock client."""
    found = {}
    for rel in STOCK_DBC_MPQS:
        mpq = stock_data / rel
        listing = {p.lower(): p for p in list_mpq(mpq)}
        wanted = [listing[k] for t in TABLES if t.dbc_filename not in found
                  and (k := f"dbfilesclient/{t.dbc_filename}".lower()) in listing]
        for path, blob in extract(mpq, wanted).items():
            found[Path(path).name] = blob
    missing = [t.dbc_filename for t in TABLES if t.dbc_filename not in found]
    if missing:
        raise SystemExit(f"stock client has no {missing} under {stock_data}")
    return found


def select_rows(asc: dict[str, list[dict]], stock_wma: list[dict]) -> dict[str, list[dict]]:
    """Ascension's rows for VANILLA_MAPS, renumbered into this project's id blocks. `asc` and the result are keyed by
    table name. Raises SystemExit on anything that would ship a broken map."""
    stock_wma_ids = {r["ID"] for r in stock_wma}
    stock_area_ids = {r["AreaID"] for r in stock_wma}
    stock_by_name = {r["AreaName"]: r["ID"] for r in stock_wma}

    wma = []
    for r in sorted((r for r in asc["WorldMapArea"] if r["MapID"] in VANILLA_MAPS), key=lambda r: r["MapID"]):
        r = dict(r, ID=WMA_ID_OVERRIDES.get(r["ID"], r["ID"]))
        lo, hi = WORLDMAPAREA_ID_RANGE
        if not lo <= r["ID"] <= hi or r["ID"] in stock_wma_ids:
            raise SystemExit(f"WorldMapArea {r['ID']} ({r['AreaName']}) is outside {lo}-{hi} or a stock id")
        if r["AreaID"] in stock_area_ids:
            raise SystemExit(f"WorldMapArea {r['ID']}: area {r['AreaID']} already has a stock map")
        if r["ParentWorldMapID"] not in (0, -1) and r["ParentWorldMapID"] not in stock_wma_ids:
            raise SystemExit(f"WorldMapArea {r['ID']}: parent map {r['ParentWorldMapID']} is not a stock map")
        wma.append(r)
    missing_maps = sorted(set(VANILLA_MAPS) - {r["MapID"] for r in wma})
    if missing_maps:
        raise SystemExit(f"no Ascension WorldMapArea row for map(s) {missing_maps}")
    if len({r["MapID"] for r in wma}) != len(wma):
        raise SystemExit("more than one Ascension WorldMapArea row for one map")

    floors = sorted((r for r in asc["DungeonMap"] if r["MapID"] in VANILLA_MAPS),
                    key=lambda r: (r["MapID"], r["FloorIndex"], r["ID"]))
    if DUNGEONMAP_ID_START + len(floors) - 1 > DUNGEONMAP_ID_END:
        raise SystemExit(f"{len(floors)} floors do not fit the dungeonmap block")
    dm, new_floor_id = [], {}
    for new_id, r in enumerate(floors, DUNGEONMAP_ID_START):
        new_floor_id[r["ID"]] = new_id
        parent = r["ParentWorldMapID"]
        if r["MapID"] in DUNGEONMAP_PARENT_OVERRIDES:
            parent = stock_by_name[DUNGEONMAP_PARENT_OVERRIDES[r["MapID"]]]
        if parent not in stock_wma_ids:
            raise SystemExit(f"DungeonMap {r['ID']} (map {r['MapID']}): parent map {parent} is not a stock map")
        dm.append(dict(r, ID=new_id, ParentWorldMapID=parent))

    floor_map = {r["ID"]: r["MapID"] for r in floors}
    chunks = sorted((r for r in asc["DungeonMapChunk"] if r["MapID"] in VANILLA_MAPS),
                    key=lambda r: (r["MapID"], r["WMOGroupID"], r["MinZ"], r["ID"]))
    if DUNGEONMAPCHUNK_ID_START + len(chunks) - 1 > DUNGEONMAPCHUNK_ID_END:
        raise SystemExit(f"{len(chunks)} chunks do not fit the dungeonmapchunk block")
    dmc = []
    for new_id, r in enumerate(chunks, DUNGEONMAPCHUNK_ID_START):
        if floor_map.get(r["DungeonMapID"]) != r["MapID"]:
            raise SystemExit(f"DungeonMapChunk {r['ID']} points at floor {r['DungeonMapID']}, not one of map "
                             f"{r['MapID']}'s")
        dmc.append(dict(r, ID=new_id, DungeonMapID=new_floor_id[r["DungeonMapID"]]))

    return {"WorldMapArea": wma, "DungeonMap": dm, "DungeonMapChunk": dmc}


def merge(stock: list[dict], new: list[dict]) -> list[dict]:
    """Stock rows in their physical order, minus those on the imported maps, then the new rows."""
    replaced = {r["MapID"] for r in new}
    kept = [r for r in stock if r["MapID"] not in replaced]
    clash = {r["ID"] for r in kept} & {r["ID"] for r in new}
    if clash:
        raise SystemExit(f"new rows reuse stock ids {sorted(clash)[:10]}")
    return kept + new


def tile_names(wma: list[dict], dm: list[dict]) -> dict[str, list[str]]:
    """{AreaName -> the tile file names (no folder) the client loads for that map}."""
    out = {}
    for r in wma:
        floors = sorted(d["FloorIndex"] for d in dm if d["MapID"] == r["MapID"])
        prefixes = [f"{r['AreaName']}{f}_" for f in floors] or [r["AreaName"]]
        out[r["AreaName"]] = [f"{p}{t}.blp" for p in prefixes for t in range(1, TILES_PER_FLOOR + 1)]
    return out


def resolve_art(tiles: dict[str, list[str]], listing: list[str]) -> dict[str, str]:
    """{archive path in the Ascension art MPQ -> path to pack as}, matched case-insensitively (MPQ lookups are). The
    packed path uses the AreaName's casing, the one the client asks for."""
    by_lower = {p.replace("\\", "/").lower(): p for p in listing}
    out, missing = {}, []
    for area, names in tiles.items():
        for name in names:
            src = by_lower.get(f"interface/worldmap/{area}/{name}".lower())
            if src is None:
                missing.append(f"{area}/{name}")
            else:
                out[src] = f"Interface\\WorldMap\\{area}\\{name}"
    if missing:
        raise SystemExit(f"{len(missing)} map tile(s) missing from the Ascension art, e.g. {missing[:5]}")
    return out


def write_previews(out_dir: Path, tiles: dict[str, list[str]], art: dict[str, bytes]) -> int:
    """One PNG per floor: the 4 x 3 tiles stitched and cropped to the 1002 x 668 the map frame shows."""
    from io import BytesIO

    from PIL import Image

    by_name = {dst.rsplit("\\", 1)[-1].lower(): blob for dst, blob in art.items()}
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for area, names in tiles.items():
        for i in range(0, len(names), TILES_PER_FLOOR):
            floor = names[i:i + TILES_PER_FLOOR]
            sheet = Image.new("RGB", (1024, 768))
            for t, name in enumerate(floor):
                # Sunken Temple's tiles are 512 x 512; the client scales every tile into its 256 x 256 slot
                tile = Image.open(BytesIO(by_name[name.lower()])).convert("RGB").resize((256, 256))
                sheet.paste(tile, ((t % 4) * 256, (t // 4) * 256))
            stem = floor[0][: -len("1.blp")].rstrip("_")
            sheet.crop((0, 0, 1002, 668)).save(out_dir / f"{stem}.png")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ascension-data", type=Path, default=ASCENSION_DATA)
    parser.add_argument("--stock-data", type=Path, default=STOCK_DATA)
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--deploy-root", type=str, default=str(DEFAULT_DEPLOY_ROOT) if DEFAULT_DEPLOY_ROOT else "")
    args = parser.parse_args()

    stock_blobs = load_stock_tables(args.stock_data)
    stock = {t.name: read_rows(stock_blobs[t.dbc_filename], t) for t in TABLES}
    for t in TABLES:  # the merge keeps stock bytes only if a plain repack does
        if dbcfile.pack_dbc_bytes(t, stock[t.name], sort=False) != stock_blobs[t.dbc_filename]:
            raise SystemExit(f"stock {t.dbc_filename} does not repack byte for byte")

    asc_mpq = args.ascension_data / ASCENSION_DBC_MPQ
    asc_blobs = extract(asc_mpq, [f"DBFilesClient/{t.dbc_filename}" for t in TABLES])
    asc = {t.name: read_rows(asc_blobs[f"DBFilesClient/{t.dbc_filename}"], t) for t in TABLES}

    new = select_rows(asc, stock["WorldMapArea"])
    files = {}
    for t in TABLES:
        rows = merge(stock[t.name], new[t.name])
        files[f"DBFilesClient\\{t.dbc_filename}"] = dbcfile.pack_dbc_bytes(t, rows, sort=False)
        print(f"{t.dbc_filename}: {len(stock[t.name])} stock + {len(new[t.name])} new = {len(rows)} rows")

    tiles = tile_names(new["WorldMapArea"], new["DungeonMap"])
    art_mpq = args.ascension_data / ASCENSION_ART_MPQ
    sources = resolve_art(tiles, list_mpq(art_mpq))
    blobs = extract(art_mpq, list(sources))
    art = {sources[src]: blob for src, blob in blobs.items()}
    files.update(art)
    print(f"{len(art)} map tile(s) from {art_mpq}")

    for r in new["WorldMapArea"]:
        floors = sum(1 for d in new["DungeonMap"] if d["MapID"] == r["MapID"])
        print(f"  map {r['MapID']:>3} {VANILLA_MAPS[r['MapID']]:<20} WorldMapArea {r['ID']} {r['AreaName']}, "
              f"{floors or 'no'} floor(s)")

    if args.preview:
        print(f"wrote {write_previews(args.preview, tiles, art)} preview PNG(s) into {args.preview}")

    LOCAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    write_mpq(LOCAL_OUT, files)
    print(f"built {LOCAL_OUT} ({LOCAL_OUT.stat().st_size} bytes, {len(files)} files)")

    if args.deploy_root:
        deploy_path = Path(args.deploy_root) / "Data" / "patch-W.mpq"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LOCAL_OUT, deploy_path)
        print(f"deployed -> {deploy_path}")
        print("refresh the manifest: docker exec patch-manifest-gen python3 /manifest_gen.py")


if __name__ == "__main__":
    main()
