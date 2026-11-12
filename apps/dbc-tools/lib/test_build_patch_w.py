"""build_patch_w.py (vanilla dungeon maps): row selection, renumbering, the stock merge and the tile list.

Pure functions on synthetic rows; no MPQ is read. The real build checks the same things on the real data and stops on
any of them (missing map, stray parent, missing tile, id clash).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_build_patch_w.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_patch_w as w  # noqa: E402
from lib import dbcfile, dbcfmt  # noqa: E402

STOCK_WMA = [
    {"ID": 38, "MapID": 0, "AreaID": 8, "AreaName": "SwampOfSorrows", "ParentWorldMapID": -1},
    {"ID": 39, "MapID": 0, "AreaID": 40, "AreaName": "Westfall", "ParentWorldMapID": -1},
]


def wma(id_, map_id, area_id, name, parent=0):
    return {"ID": id_, "MapID": map_id, "AreaID": area_id, "AreaName": name, "LocLeft": 1.0, "LocRight": 0.0,
            "LocTop": 1.0, "LocBottom": 0.0, "DisplayMapID": -1, "DefaultDungeonFloor": 0, "ParentWorldMapID": parent}


def floor(id_, map_id, index, parent=39):
    return {"ID": id_, "MapID": map_id, "FloorIndex": index, "MinX": 0.0, "MaxX": 1.0, "MinY": 0.0, "MaxY": 1.0,
            "ParentWorldMapID": parent}


def chunk(id_, map_id, group, floor_id):
    return {"ID": id_, "MapID": map_id, "WMOGroupID": group, "DungeonMapID": floor_id, "MinZ": -500.0}


def ascension(maps=None):
    """One WorldMapArea row per vanilla map (Deadmines with two floors), plus a non-vanilla row that must be skipped."""
    rows = [wma(700 + i, m, 5000 + m, f"Map{m}") for i, m in enumerate(maps or w.VANILLA_MAPS)]
    rows.append(wma(780, 532, 3457, "Karazhan"))
    return {
        "WorldMapArea": rows,
        "DungeonMap": [floor(14, 36, 2), floor(13, 36, 1), floor(77, 532, 1), floor(50, 109, 1, parent=0)],
        "DungeonMapChunk": [chunk(11, 36, 501, 13), chunk(12, 36, 502, 14), chunk(13, 532, 900, 77),
                            chunk(14, 109, 600, 50)],
    }


class SelectRowsTest(unittest.TestCase):
    def test_vanilla_only_and_renumbered(self):
        new = w.select_rows(ascension(), STOCK_WMA)
        self.assertEqual({r["MapID"] for r in new["WorldMapArea"]}, set(w.VANILLA_MAPS))
        self.assertEqual([(r["ID"], r["MapID"], r["FloorIndex"]) for r in new["DungeonMap"]],
                         [(1000, 36, 1), (1001, 36, 2), (1002, 109, 1)])
        self.assertEqual([(r["ID"], r["WMOGroupID"], r["DungeonMapID"]) for r in new["DungeonMapChunk"]],
                         [(10000, 501, 1000), (10001, 502, 1001), (10002, 600, 1002)])

    def test_sunken_temple_overrides(self):
        asc = ascension()
        asc["WorldMapArea"] = [dict(r, ID=2021) if r["MapID"] == 109 else r for r in asc["WorldMapArea"]]
        new = w.select_rows(asc, STOCK_WMA)
        self.assertEqual(next(r["ID"] for r in new["WorldMapArea"] if r["MapID"] == 109), 687)
        self.assertEqual(next(r["ParentWorldMapID"] for r in new["DungeonMap"] if r["MapID"] == 109), 38)

    def test_missing_map_stops(self):
        with self.assertRaises(SystemExit):
            w.select_rows(ascension([m for m in w.VANILLA_MAPS if m != 230]), STOCK_WMA)

    def test_unknown_parent_stops(self):
        asc = ascension()
        asc["DungeonMap"][0] = floor(14, 36, 2, parent=9999)
        with self.assertRaises(SystemExit):
            w.select_rows(asc, STOCK_WMA)

    def test_chunk_on_another_maps_floor_stops(self):
        asc = ascension()
        asc["DungeonMapChunk"].append(chunk(15, 36, 503, 50))
        with self.assertRaises(SystemExit):
            w.select_rows(asc, STOCK_WMA)

    def test_stock_area_clash_stops(self):
        with self.assertRaises(SystemExit):
            w.select_rows(ascension(), STOCK_WMA + [dict(STOCK_WMA[0], ID=99, AreaID=5036)])


class MergeTest(unittest.TestCase):
    def test_keeps_stock_order_and_replaces_imported_maps(self):
        stock = [floor(28, 43, 1), floor(2, 600, 1), floor(1, 601, 1)]
        new = [floor(1000, 43, 1)]
        self.assertEqual([r["ID"] for r in w.merge(stock, new)], [2, 1, 1000])

    def test_id_clash_stops(self):
        with self.assertRaises(SystemExit):
            w.merge([floor(1000, 600, 1)], [floor(1000, 43, 1)])

    def test_merged_file_round_trips(self):
        rows = w.merge([floor(28, 43, 1), floor(2, 600, 1)], [floor(1000, 36, 1)])
        blob = dbcfile.pack_dbc_bytes(dbcfmt.DUNGEONMAP, rows, sort=False)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "DungeonMap.dbc"
            path.write_bytes(blob)
            self.assertEqual(dbcfile.read_dbc(path, dbcfmt.DUNGEONMAP), rows)


class TilesTest(unittest.TestCase):
    def test_floor_and_floorless_names(self):
        tiles = w.tile_names([wma(756, 36, 1581, "TheDeadmines"), wma(686, 209, 1176, "ZulFarrak")],
                             [floor(1000, 36, 1), floor(1001, 36, 2)])
        self.assertEqual(len(tiles["TheDeadmines"]), 24)
        self.assertEqual(tiles["TheDeadmines"][0], "TheDeadmines1_1.blp")
        self.assertEqual(tiles["TheDeadmines"][-1], "TheDeadmines2_12.blp")
        self.assertEqual(tiles["ZulFarrak"], [f"ZulFarrak{t}.blp" for t in range(1, 13)])

    def test_art_matched_case_insensitively(self):
        tiles = {"thetempleofatalhakkar": [f"thetempleofatalhakkar1_{t}.blp" for t in range(1, 13)]}
        listing = [f"Interface/WorldMap/TheTempleOfAtalHakkar/TheTempleOfAtalHakkar1_{t}.blp" for t in range(1, 13)]
        art = w.resolve_art(tiles, listing)
        self.assertEqual(art[listing[0]], "Interface\\WorldMap\\thetempleofatalhakkar\\thetempleofatalhakkar1_1.blp")

    def test_missing_tile_stops(self):
        tiles = {"Ragefire": [f"Ragefire1_{t}.blp" for t in range(1, 13)]}
        listing = [f"Interface/WorldMap/Ragefire/Ragefire1_{t}.blp" for t in range(1, 12)]
        with self.assertRaises(SystemExit):
            w.resolve_art(tiles, listing)


if __name__ == "__main__":
    unittest.main()
