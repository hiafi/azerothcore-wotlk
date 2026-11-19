"""
Dungeon finder declarations (lfg-classic-heroic): lib/dsl/lfg.py's lfg_group() / lfg_random() / lfg_heroic(), the rows
lib/lfg_dungeons.py builds from them, their SPELL_TABLES half (lfgdungeons_dbc, lfg_dungeon_template), the client
LFGDungeons.dbc / LFGDungeonGroup.dbc merge, the heroic final boss link, the scope reference check and the
generate.py wiring; lfg_dungeon() and last_encounter= (the Blackrock Depths sections, SectionTest); then the real
source/world/lfg_classic_heroic.py over the stock files.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_lfg_dungeons.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, dungeon_heroic, lfg_dungeons, scope, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql, generated_file, index_for, read_back, render, spec_for  # noqa: E402

IDS_CFG = {
    "lfgdungeons": {"start": 300, "end": 399}, "lfgdungeongroup": {"start": 12, "end": 31},
}
HEADER = "from lib.dsl.lfg import lfg_group, lfg_heroic, lfg_random\n"
DECLARATIONS = HEADER + (
    "lfg_group(12, name='Classic Heroic', order_index=5, type_id=5)\n"
    "lfg_group(1, order_index=6)\n"
    "lfg_random(300, 'Random Classic Heroic', group=12, like=260, expansion=0, min_level=60, max_level=62)\n"
    "lfg_heroic(301, normal=6, group=12)\n"
)
MASK = 0xFF01FE


def _load(text: str, ids_cfg: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "lfg_test.py"
        path.write_text(text)
        reg = registry.load_class_file(path, ids_cfg=IDS_CFG if ids_cfg is None else ids_cfg)
    return {key: list(getattr(reg, key)) for key in registry.MERGE_KEYS}


def _dungeon_row(id_, name, map_id, *, type_id=1, difficulty=0, group=1, texture="", expansion=0, min_level=15,
                 max_level=25, flags=3) -> dict:
    row = dbcfile.empty_row(dbcfmt.LFGDUNGEONS)
    row.update(
        ID=id_, Name_Lang_enUS=name, Name_Lang_deDE=f"{name} (de)", Name_Lang_Mask=MASK, MinLevel=min_level,
        MaxLevel=max_level, Target_Level=min_level + 4, Target_Level_Min=min_level + 2, Target_Level_Max=min_level + 5,
        MapID=map_id, Difficulty=difficulty, Flags=flags, TypeID=type_id, Faction=-1, TextureFilename=texture,
        ExpansionLevel=expansion, Group_Id=group, Description_Lang_Mask=0xFF01FC,
    )
    return row


STOCK_DUNGEONS = {
    6: _dungeon_row(6, "Deadmines", 36, texture="Deadmines"),
    40: _dungeon_row(40, "Stratholme - Main Gate", 329, texture="Stratholme", min_level=55, max_level=65),
    274: _dungeon_row(274, "Stratholme - Service Entrance", 329, texture="Stratholme", min_level=55, max_level=65),
    43: _dungeon_row(43, "Some Raid", 409, type_id=2, group=6),
    288: _dungeon_row(288, "The Crown Chemical Co.", 33, flags=15, group=11),
    260: _dungeon_row(260, "Random Burning Crusade Heroic", 0, type_id=6, difficulty=1, group=3, expansion=1,
                      min_level=70, max_level=73),
    258: _dungeon_row(258, "Random Classic Dungeon", 0, type_id=6, group=1, min_level=15, max_level=58),
}


def _group_row(id_, name, order, type_id) -> dict:
    row = dbcfile.empty_row(dbcfmt.LFGDUNGEONGROUP)
    row.update(ID=id_, Name_Lang_enUS=name, Name_Lang_Mask=MASK, OrderIndex=order, TypeID=type_id)
    return row


STOCK_GROUPS = {
    1: _group_row(1, "Classic Dungeons", 5, 1), 3: _group_row(3, "Burning Crusade Heroic", 3, 5),
    6: _group_row(6, "Classic Raid", 20, 2),
}
POSITIONS = {
    40: {"dungeonId": 40, "name": "Stratholme - Main Gate", "position_x": 3395.09, "position_y": -3380.25,
         "position_z": 142.702, "orientation": 0.1, "VerifiedBuild": 0},
}


def _heroic_dungeon(map_id: int, name: str) -> dict:
    return {"id": map_id, "map_id": map_id, "name": name, "heroic": {"encounter_ids": (1000,)}, "heroic_entries": {}}


def _credit(entry: int, normal_lfg: int, credit: int = 639) -> dict:
    return {
        "entry": entry, "creditType": 0, "creditEntry": credit, "lastEncounterDungeon": 0, "comment": "x - Heroic",
        "_normal_lfg": normal_lfg, dungeon_heroic.DERIVED: True,
    }


def _inputs(**kw) -> lfg_dungeons.LfgInputs:
    kw.setdefault("stock_dungeons", {k: dict(v) for k, v in STOCK_DUNGEONS.items()})
    kw.setdefault("stock_groups", {k: dict(v) for k, v in STOCK_GROUPS.items()})
    kw.setdefault("positions", dict(POSITIONS))
    return lfg_dungeons.LfgInputs(**kw)


def _expand(text: str = DECLARATIONS, dungeons=None, credits=None, **inputs):
    dsl = _load(text)
    dsl["dungeons"] = [_heroic_dungeon(36, "Deadmines")] if dungeons is None else dungeons
    dsl["instance_encounters"] = [_credit(1006, 6)] if credits is None else credits
    out = lfg_dungeons.expand(dsl, lambda: _inputs(**inputs))
    return dsl, out


class LayoutTest(unittest.TestCase):
    def test_lfg_dungeon_group_layout(self):
        table = dbcfmt.LFGDUNGEONGROUP
        self.assertEqual(len(table.fmt), 21)
        self.assertEqual(table.columns[:2], ("ID", "Name_Lang_enUS"))
        self.assertEqual(table.columns[17:], ("Name_Lang_Mask", "OrderIndex", "ParentGroupID", "TypeID"))
        self.assertEqual(table.sql_table, "")

    def test_lfg_dungeons_strings_are_read_as_strings(self):
        self.assertIn("TextureFilename", dbcfmt.LFGDUNGEONS.read_as_string)
        self.assertIn("Description_Lang_enUS", dbcfmt.LFGDUNGEONS.read_as_string)
        self.assertEqual(spell_tables.LFGDUNGEONS_COLUMNS, dbcfmt.LFGDUNGEONS.columns)

    def test_the_base_dump_columns_match(self):
        from lib import sql_dump, trainer_state  # noqa: PLC0415

        for table, columns in (("lfgdungeons_dbc", spell_tables.LFGDUNGEONS_COLUMNS),
                               ("lfg_dungeon_template", spell_tables.LFG_DUNGEON_TEMPLATE_COLUMNS)):
            with self.subTest(table=table):
                path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
                self.assertEqual(tuple(sql_dump.parse_create_table_columns(path, table)), columns)

    def test_client_order_keeps_type_blocks_and_order_index(self):
        rows = [dict(r) for r in STOCK_DUNGEONS.values()]
        rows.append(_dungeon_row(301, "Deadmines", 36, type_id=5, difficulty=1, group=12))
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONS, rows, rows)
        self.assertEqual([r["ID"] for r in scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONS)],
                         [6, 40, 274, 288, 43, 301, 258, 260])
        groups = [*STOCK_GROUPS.values(), _group_row(12, "Classic Heroic", 5, 5)]
        groups[0] = {**groups[0], "OrderIndex": 6}
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONGROUP, groups, groups)
        back = scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONGROUP)
        self.assertEqual([r["ID"] for r in back], [3, 12, 1, 6])
        self.assertEqual(back[1]["Name_Lang_enUS"], "Classic Heroic")


class DeclarationTest(unittest.TestCase):
    def test_declarations_register(self):
        dsl = _load(DECLARATIONS)
        self.assertEqual([d["id"] for d in dsl["lfg_group_declarations"]], [12, 1])
        self.assertEqual([(d["id"], d["kind"]) for d in dsl["lfg_dungeon_declarations"]],
                         [(300, "random"), (301, "heroic")])
        self.assertTrue(dsl["lfg_group_declarations"][0]["new"])
        self.assertFalse(dsl["lfg_group_declarations"][1]["new"])

    def test_bad_arguments_raise(self):
        for call in (
            "lfg_group(12, order_index=5)",  # a new group needs a name and a type
            "lfg_group(12, name='x', order_index=-1, type_id=5)",
            "lfg_group(0, order_index=1)",
            "lfg_random(250, 'x', group=12, like=260, expansion=0, min_level=60, max_level=62)",  # outside the block
            "lfg_random(300, '', group=12, like=260, expansion=0, min_level=60, max_level=62)",
            "lfg_random(300, 'x', group=12, like=260, expansion=3, min_level=60, max_level=62)",
            "lfg_random(300, 'x', group=12, like=260, expansion=0, min_level=63, max_level=62)",
            "lfg_random(300, 'x', group=12, like=260, expansion=0, min_level=60, max_level=62, target_level=63)",
            "lfg_random(True, 'x', group=12, like=260, expansion=0, min_level=60, max_level=62)",
            "lfg_heroic(294, normal=6, group=12)",  # a stock id, outside the block
            "lfg_heroic(301, normal=0, group=12)",
            "lfg_heroic('301', normal=6, group=12)",
        ):
            with self.subTest(call=call), self.assertRaises(ValueError):
                _load(HEADER + call + "\n")

    def test_a_missing_block_raises(self):
        with self.assertRaises(ValueError):
            _load(HEADER + "lfg_heroic(301, normal=6, group=12)\n",
                  ids_cfg={"lfgdungeongroup": {"start": 12, "end": 31}})

    def test_one_id_twice_is_a_duplicate(self):
        with self.assertRaises(registry.DuplicateIdError):
            with tempfile.TemporaryDirectory() as d:
                for name in ("a.py", "b.py"):
                    (Path(d) / name).write_text(HEADER + "lfg_heroic(301, normal=6, group=12)\n")
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)


class ExpandTest(unittest.TestCase):
    def test_rows(self):
        dsl, out = _expand()
        self.assertEqual(out.errors, [])
        random, heroic = dsl["lfg_dungeons"]
        self.assertEqual(
            {k: random[k] for k in ("ID", "Name_Lang_enUS", "Name_Lang_deDE", "Name_Lang_Mask", "MinLevel", "MaxLevel",
                                    "Target_Level", "Target_Level_Min", "Target_Level_Max", "MapID", "Difficulty",
                                    "Flags", "TypeID", "ExpansionLevel", "Group_Id", "Faction")},
            {"ID": 300, "Name_Lang_enUS": "Random Classic Heroic", "Name_Lang_deDE": "", "Name_Lang_Mask": MASK,
             "MinLevel": 60, "MaxLevel": 62, "Target_Level": 60, "Target_Level_Min": 60, "Target_Level_Max": 62,
             "MapID": 0, "Difficulty": 1, "Flags": 3, "TypeID": 6, "ExpansionLevel": 0, "Group_Id": 12, "Faction": -1},
        )
        self.assertEqual(
            {k: heroic[k] for k in ("ID", "Name_Lang_enUS", "Name_Lang_deDE", "MinLevel", "MaxLevel", "Target_Level",
                                    "Target_Level_Min", "Target_Level_Max", "MapID", "Difficulty", "Flags", "TypeID",
                                    "TextureFilename", "ExpansionLevel", "Group_Id")},
            {"ID": 301, "Name_Lang_enUS": "Deadmines", "Name_Lang_deDE": "Deadmines (de)", "MinLevel": 60,
             "MaxLevel": 62, "Target_Level": 60, "Target_Level_Min": 60, "Target_Level_Max": 62, "MapID": 36,
             "Difficulty": 1, "Flags": 3, "TypeID": 5, "TextureFilename": "Deadmines", "ExpansionLevel": 0,
             "Group_Id": 12},
        )

    def test_groups(self):
        dsl, out = _expand()
        new, classic = sorted(dsl["lfg_groups"], key=lambda r: -r["ID"])
        self.assertEqual((new["ID"], new["Name_Lang_enUS"], new["OrderIndex"], new["TypeID"], new["Name_Lang_Mask"]),
                         (12, "Classic Heroic", 5, 5, MASK))
        self.assertEqual((classic["ID"], classic["Name_Lang_enUS"], classic["OrderIndex"], classic["TypeID"]),
                         (1, "Classic Dungeons", 6, 1))
        self.assertEqual(out.warnings, [])

    def test_a_shared_order_index_warns(self):
        _dsl, out = _expand(DECLARATIONS.replace("lfg_group(1, order_index=6)\n", ""))
        self.assertTrue(any("share OrderIndex 5" in w for w in out.warnings), out.warnings)

    def test_the_final_boss_points_at_the_heroic_entry(self):
        other = _credit(1001, 0, credit=643)
        dsl, out = _expand(credits=[_credit(1006, 6), other])
        self.assertEqual(out.errors, [])
        self.assertEqual(dsl["instance_encounters"][0]["lastEncounterDungeon"], 301)
        self.assertEqual(other["lastEncounterDungeon"], 0)
        self.assertTrue(any("completes on heroic encounter 1006" in n for n in out.notes))

    def test_a_second_expand_replaces(self):
        dsl, _out = _expand()
        lfg_dungeons.expand(dsl, lambda: _inputs())
        self.assertEqual([r["ID"] for r in dsl["lfg_dungeons"]], [300, 301])
        self.assertEqual(len(dsl["lfg_groups"]), 2)
        dsl["lfg_dungeon_declarations"] = []
        dsl["lfg_group_declarations"] = []
        lfg_dungeons.expand(dsl, lambda: self.fail("nothing declared: no inputs"))
        self.assertEqual((dsl["lfg_dungeons"], dsl["lfg_groups"]), ([], []))
        self.assertEqual(dsl["instance_encounters"][0]["lastEncounterDungeon"], 0)

    def test_positions_copy_the_normal_entry(self):
        text = DECLARATIONS + "lfg_heroic(304, normal=40, group=12)\nlfg_heroic(305, normal=274, group=12)\n"
        credits = [_credit(1006, 6), _credit(1033, 40, 10813), _credit(1040, 274, 10440)]
        dsl, out = _expand(text, dungeons=[_heroic_dungeon(36, "Deadmines"), _heroic_dungeon(329, "Stratholme")],
                           credits=credits)
        self.assertEqual(out.errors, [])
        (template,) = dsl["lfg_dungeon_templates"]
        self.assertEqual({c: template[c] for c in spell_tables.LFG_DUNGEON_TEMPLATE_COLUMNS}, {
            "dungeonId": 304, "name": "Stratholme - Main Gate (Heroic)", "position_x": 3395.09,
            "position_y": -3380.25, "position_z": 142.702, "orientation": 0.1, "VerifiedBuild": 0,
        })
        self.assertEqual([c["lastEncounterDungeon"] for c in credits], [301, 304, 305])
        self.assertTrue(any("draws from 301 Deadmines, 304 Stratholme - Main Gate, 305 Stratholme - Service "
                            "Entrance" in n for n in out.notes), out.notes)

    def test_errors(self):
        cases = {
            "not a stock normal dungeon row": (DECLARATIONS.replace("normal=6", "normal=43"), {}),
            "not seasonal": (DECLARATIONS.replace("normal=6", "normal=288"), {}),
            "has no declared heroic": (DECLARATIONS, {"dungeons": []}),
            "is a stock row": (DECLARATIONS, {"stock_dungeons": {**STOCK_DUNGEONS, 301: STOCK_DUNGEONS[6]}}),
            "could never complete": (DECLARATIONS, {"credits": [_credit(1006, 0)]}),
            "all end the run": (DECLARATIONS, {"credits": [_credit(1005, 6), _credit(1006, 6)]}),
            "is not a stock random row": (DECLARATIONS.replace("like=260", "like=6"), {}),
            "has no lfg_random()": (DECLARATIONS.replace("lfg_heroic(301, normal=6, group=12)",
                                                         "lfg_heroic(301, normal=6, group=3)"), {}),
            "already has random": (DECLARATIONS + "lfg_random(302, 'Again', group=12, like=260, expansion=0, "
                                                  "min_level=60, max_level=62)\n", {}),
            "already has heroic entry": (DECLARATIONS + "lfg_heroic(302, normal=6, group=12)\n", {}),
            "neither stock nor declared": (DECLARATIONS.replace("group=12, like", "group=13, like"), {}),
            "is a stock LFGDungeonGroup id": (DECLARATIONS, {"stock_groups": {**STOCK_GROUPS, 12: STOCK_GROUPS[1]}}),
            "no stock LFGDungeonGroup row 2": (DECLARATIONS + "lfg_group(2, order_index=7)\n", {}),
            "no stock LFGDungeons.dbc": (DECLARATIONS, {"stock_dungeons": None}),
            "no stock LFGDungeonGroup.dbc": (DECLARATIONS, {"stock_groups": None}),
        }
        for expected, (text, kw) in cases.items():
            with self.subTest(expected=expected):
                _dsl, out = _expand(text, **kw)
                self.assertTrue(any(expected in e for e in out.errors), out.errors)

    def test_an_unlisted_heroic_entry_is_a_note(self):
        _dsl, out = _expand(dungeons=[_heroic_dungeon(36, "Deadmines"), _heroic_dungeon(329, "Stratholme"),
                                      _heroic_dungeon(33, "Shadowfang Keep")])
        self.assertEqual(out.errors, [])
        self.assertFalse(any("map 33" in n for n in out.notes), out.notes)  # only the seasonal 288 there
        self.assertTrue(any("Stratholme (map 329) has a heroic but no lfg_heroic() for finder entries [40, 274]" in n
                            for n in out.notes), out.notes)

    def test_client_rows_carry_only_the_file_columns(self):
        dsl, _out = _expand()
        rows = lfg_dungeons.client_dungeon_rows(dsl["lfg_dungeons"])
        self.assertEqual(sorted(rows), [300, 301])
        self.assertEqual(tuple(rows[301]), dbcfmt.LFGDUNGEONS.columns)
        groups = lfg_dungeons.client_group_rows(dsl["lfg_groups"])
        self.assertEqual(tuple(groups[12]), dbcfmt.LFGDUNGEONGROUP.columns)


OVERRIDE = (
    "lfg_override(44, type_id=1, group=1, flags=3, min_level=55, max_level=65, "
    "position=(98.25, -300.75, 63.1, 4.94))\n"
)
HEADER_OVERRIDE = "from lib.dsl.lfg import lfg_group, lfg_heroic, lfg_override, lfg_random\n"


def _ubrs_stock() -> dict:
    """The stock rows around Blackrock Spire: 32 (LBRS, a dungeon entry) and 44 (UBRS, a raid-type one)."""
    return {
        **STOCK_DUNGEONS,
        32: _dungeon_row(32, "Lower Blackrock Spire", 229, texture="BLACKROCKSPIRE", min_level=55, max_level=65),
        44: _dungeon_row(44, "Upper Blackrock Spire", 229, type_id=2, group=6, texture="BlackrockSpire", min_level=56,
                         max_level=83, flags=0),
    }


class OverrideTest(unittest.TestCase):
    """lfg_override(): an edit of a stock LFGDungeons row (Upper Blackrock Spire, raid-type, made a dungeon entry)."""

    TEXT = DECLARATIONS.replace(HEADER, HEADER_OVERRIDE) + OVERRIDE + "lfg_heroic(306, normal=44, group=12)\n"

    def _run(self, text=TEXT, **kw):
        kw.setdefault("stock_dungeons", _ubrs_stock())
        return _expand(text, dungeons=[_heroic_dungeon(36, "Deadmines"), _heroic_dungeon(229, "Blackrock Spire")],
                       credits=[_credit(1006, 6), _credit(1054, 44, 10363)], **kw)

    def test_the_declaration(self):
        dsl = _load(self.TEXT)
        decl = next(d for d in dsl["lfg_dungeon_declarations"] if d["kind"] == "override")
        self.assertEqual(decl["id"], 44)
        self.assertEqual(decl["edits"], {"type_id": 1, "group": 1, "flags": 3, "min_level": 55, "max_level": 65})
        self.assertEqual(decl["position"], (98.25, -300.75, 63.1, 4.94))

    def test_bad_arguments_raise(self):
        for call in (
            "lfg_override(44)",  # nothing to edit
            "lfg_override(0, type_id=1)",
            "lfg_override(301, type_id=1)",  # a custom id (ids.yaml block)
            "lfg_override(44, type_id=3)",
            "lfg_override(44, min_level=70, max_level=60)",
            "lfg_override(44, min_level=-1)",
            "lfg_override(44, max_level=300)",
            "lfg_override(44, flags=True)",
            "lfg_override(44, position=(1.0, 2.0, 3.0))",
            "lfg_override(44, position=(1.0, 2.0, 3.0, 'x'))",
            "lfg_override('44', type_id=1)",
        ):
            with self.subTest(call=call), self.assertRaises(ValueError):
                _load(HEADER_OVERRIDE + call + "\n")

    def test_the_stock_row_is_replaced_and_the_rest_kept(self):
        dsl, out = self._run()
        self.assertEqual(out.errors, [])
        rows = {r["ID"]: r for r in dsl["lfg_dungeons"]}
        self.assertEqual(sorted(rows), [44, 300, 301, 306])
        edited, stock = rows[44], _ubrs_stock()[44]
        self.assertEqual((edited["TypeID"], edited["Group_Id"], edited["Flags"], edited["MinLevel"],
                          edited["MaxLevel"]), (1, 1, 3, 55, 65))
        for column in ("Name_Lang_enUS", "Name_Lang_deDE", "MapID", "Difficulty", "TextureFilename", "Target_Level",
                       "Target_Level_Min", "Target_Level_Max", "ExpansionLevel", "Faction"):
            self.assertEqual(edited[column], stock[column], column)
        self.assertEqual(_ubrs_stock()[44]["TypeID"], 2)  # the stock input is not touched

    def test_a_heroic_entry_takes_the_edited_row_as_its_normal(self):
        dsl, out = self._run()
        self.assertEqual(out.errors, [])
        heroic = next(r for r in dsl["lfg_dungeons"] if r["ID"] == 306)
        self.assertEqual((heroic["TypeID"], heroic["Difficulty"], heroic["Flags"], heroic["MapID"], heroic["Group_Id"]),
                         (5, 1, 3, 229, 12))
        self.assertEqual((heroic["MinLevel"], heroic["MaxLevel"]), (60, 62))
        self.assertTrue(any("lfg_heroic(306, normal=44) completes on heroic encounter 1054" in n for n in out.notes))
        # without the edit the raid-type row is not a stock normal dungeon row
        _dsl, bad = self._run(DECLARATIONS + "lfg_heroic(306, normal=44, group=12)\n")
        self.assertTrue(any("not a stock normal dungeon row" in e for e in bad.errors), bad.errors)

    def test_the_entrance_position_goes_to_the_row_and_its_heroic_copy(self):
        dsl, out = self._run()
        self.assertEqual(out.errors, [])
        positions = {t["dungeonId"]: t for t in dsl["lfg_dungeon_templates"]}
        self.assertEqual(sorted(positions), [44, 306])
        first = positions[44]
        self.assertEqual({c: first[c] for c in spell_tables.LFG_DUNGEON_TEMPLATE_COLUMNS}, {
            "dungeonId": 44, "name": "Upper Blackrock Spire", "position_x": 98.25, "position_y": -300.75,
            "position_z": 63.1, "orientation": 4.94, "VerifiedBuild": 0,
        })
        copy = positions[306]
        self.assertEqual((copy["position_x"], copy["position_y"], copy["position_z"], copy["orientation"]),
                         (98.25, -300.75, 63.1, 4.94))
        self.assertEqual(copy["name"], "Upper Blackrock Spire (Heroic)")

    def test_an_edit_without_a_position_keeps_the_live_one(self):
        text = self.TEXT.replace(", position=(98.25, -300.75, 63.1, 4.94)", "")
        live = {44: {"dungeonId": 44, "name": "UBRS", "position_x": 1.0, "position_y": 2.0, "position_z": 3.0,
                     "orientation": 0.5, "VerifiedBuild": 0}}
        dsl, out = self._run(text, positions=live)
        self.assertEqual(out.errors, [])
        self.assertEqual([t["dungeonId"] for t in dsl["lfg_dungeon_templates"]], [306])  # 44's live row is not ours
        self.assertEqual(dsl["lfg_dungeon_templates"][0]["position_x"], 1.0)

    def test_errors(self):
        cases = {
            "no stock LFGDungeons row 999": (self.TEXT + "lfg_override(999, flags=3)\n", {}),
            "is edited twice": (self.TEXT + "lfg_override(44, flags=0)\n", {}),
            "MinLevel 90 is above MaxLevel 83": (
                self.TEXT.replace("min_level=55, max_level=65, ", "min_level=90, "), {}),
        }
        for expected, (text, kw) in cases.items():
            with self.subTest(expected=expected):
                _dsl, out = self._run(text, **kw)
                self.assertTrue(any(expected in e for e in out.errors), out.errors)

    def test_a_second_expand_replaces_the_edit(self):
        dsl, _out = self._run()
        lfg_dungeons.expand(dsl, lambda: _inputs(stock_dungeons=_ubrs_stock()))
        self.assertEqual(sorted(r["ID"] for r in dsl["lfg_dungeons"]), [44, 300, 301, 306])
        dsl["lfg_dungeon_declarations"] = []
        dsl["lfg_group_declarations"] = []
        lfg_dungeons.expand(dsl, lambda: self.fail("nothing declared: no inputs"))
        self.assertEqual((dsl["lfg_dungeons"], dsl["lfg_dungeon_templates"]), ([], []))

    def test_the_client_row_replaces_the_stock_row_in_the_merge(self):
        dsl, _out = self._run()
        rows = lfg_dungeons.client_dungeon_rows(dsl["lfg_dungeons"])
        self.assertEqual(tuple(rows[44]), dbcfmt.LFGDUNGEONS.columns)
        merged = {r["ID"]: r for r in _ubrs_stock().values()}
        merged.update(rows)
        self.assertEqual(len(merged), len(_ubrs_stock()) + 3)  # 300, 301 and 306 are new, 44 is replaced
        self.assertEqual((merged[44]["TypeID"], merged[44]["Group_Id"]), (1, 1))

    def test_the_sql_blocks_hold_row_44_and_its_start_point(self):
        dsl, _out = self._run()
        blocks = {t: render(t, index_for(t, []), dsl[spec_for(t).registry_key])
                  for t in ("lfgdungeons_dbc", "lfg_dungeon_template")}
        self.assertIn("(44)", blocks["lfgdungeons_dbc"].replace("\n", " "))
        self.assertIn("(44, 'Upper Blackrock Spire', 98.25, -300.75, 63.1, 4.94, 0)", blocks["lfg_dungeon_template"])
        done = codestyle_sql("\n\n".join(blocks.values()))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        for table, rendered in blocks.items():  # a second build over the read-back state emits nothing
            spec = spec_for(table)
            live = read_back(rendered, table, spec.columns)
            self.assertEqual(render(table, index_for(table, live), dsl[spec.registry_key]), "", table)


# Blackrock Depths (map 230): stock finder entries 30 (Prison) and 276 (Upper City), a subset of its encounters, and the
# live kill credits (227 Gerstahn ends 30, 245 the Emperor ends 276; the base dump says the same).
HEADER_SECTIONS = "from lib.dsl.lfg import lfg_dungeon, lfg_group, lfg_heroic, lfg_override, lfg_random\n"
SECTIONS = (
    "lfg_override(30, last_encounter=230)\n"
    "lfg_dungeon(308, 'Blackrock Depths - Shadowforge City', map_id=230, like=30, min_level=48, max_level=58, "
    "target_level=53, last_encounter=235, position=(595.0, -92.0, -45.0, 1.5))\n"
    "lfg_dungeon(309, 'Blackrock Depths - Manufactory', map_id=230, like=30, min_level=50, max_level=60, "
    "target_level=55, last_encounter=237, position=(607.2, -47.8, -59.8, 0.2))\n"
    "lfg_override(276, position=(843.8, -167.8, -49.7, 3.1))\n"
)
SECTION_HEROICS = (
    "lfg_heroic(310, normal=30, group=12)\nlfg_heroic(311, normal=308, group=12)\n"
    "lfg_heroic(312, normal=309, group=12)\nlfg_heroic(313, normal=276, group=12)\n"
)
BRD_TEXT = DECLARATIONS.replace(HEADER, HEADER_SECTIONS) + SECTIONS + SECTION_HEROICS
BRD_ENCOUNTERS = {
    227: "High Interrogator Gerstahn", 230: "Ring of Law", 234: "Fineous Darkvire", 235: "Bael'Gar",
    237: "Golem Lord Argelmach", 245: "Emperor Dagran Thaurissan",
}
BRD_CREDITS = {227: (9018, 30), 230: (10096, 0), 234: (9056, 0), 235: (9016, 0), 237: (8983, 0), 245: (9019, 276)}
# The heroic copies dungeon_heroic derives (heroic id = normal id + 828: 227 -> 1055 ... 245 -> 1073).
HEROIC_OFFSET = 828


def _brd_stock() -> dict:
    return {
        **STOCK_DUNGEONS,
        30: _dungeon_row(30, "Blackrock Depths - Prison", 230, texture="BLACKROCKDEPTHS", min_level=47, max_level=57),
        276: _dungeon_row(276, "Blackrock Depths - Upper City", 230, texture="BLACKROCKDEPTHS", min_level=51,
                          max_level=61),
    }


def _brd_encounters() -> dict:
    rows = {e: {"ID": e, "MapID": 230, "Difficulty": 0, "Name_Lang_enUS": n} for e, n in BRD_ENCOUNTERS.items()}
    rows[167] = {"ID": 167, "MapID": 36, "Difficulty": 0, "Name_Lang_enUS": "VanCleef"}
    return rows


def _brd_credits(links: dict | None = None) -> dict:
    links = {**{e: lfg for e, (_c, lfg) in BRD_CREDITS.items()}, **(links or {})}
    return {e: {"entry": e, "creditType": 0, "creditEntry": c, "lastEncounterDungeon": links[e],
                "comment": BRD_ENCOUNTERS[e]} for e, (c, _lfg) in BRD_CREDITS.items()}


def _brd_heroic_credits() -> list[dict]:
    """What lib/dungeon_heroic.py derives for map 230: one heroic row per normal credit, carrying the normal row's
    live link (`_normal_lfg`) and the normal encounter (`_normal_entry`)."""
    rows = []
    for entry, (credit, lfg) in BRD_CREDITS.items():
        row = _credit(entry + HEROIC_OFFSET, lfg, credit)
        row[lfg_dungeons.NORMAL_ENTRY_KEY] = entry
        rows.append(row)
    return rows


def _brd_run(text: str = BRD_TEXT, live_links: dict | None = None, **kw):
    kw.setdefault("stock_dungeons", _brd_stock())
    kw.setdefault("encounters", _brd_encounters())
    kw.setdefault("credits", _brd_credits(live_links))
    kw.setdefault("base_credits", _brd_credits())
    kw.setdefault("positions", {**POSITIONS, 30: {"dungeonId": 30, "name": "Blackrock Depths - Prison",
                                                  "position_x": 458.32, "position_y": 26.52, "position_z": -70.67,
                                                  "orientation": 4.95, "VerifiedBuild": 0}})
    dsl = _load(text)
    dsl["dungeons"] = [_heroic_dungeon(36, "Deadmines"), _heroic_dungeon(230, "Blackrock Depths")]
    dsl["instance_encounters"] = [_credit(1006, 6), *_brd_heroic_credits()]
    out = lfg_dungeons.expand(dsl, lambda: _inputs(**kw))
    return dsl, out


def _links(dsl: dict) -> dict[int, int]:
    return {r["entry"]: r["lastEncounterDungeon"] for r in dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)}


def _heroic_links(dsl: dict) -> dict[int, int]:
    return {r["entry"] - HEROIC_OFFSET: r["lastEncounterDungeon"] for r in dsl["instance_encounters"]
            if lfg_dungeons.NORMAL_ENTRY_KEY in r}


class SectionTest(unittest.TestCase):
    """lfg_dungeon() (a new normal finder entry of a map), last_encounter= on it and on lfg_override(), and
    lfg_heroic() over a declared row: the Blackrock Depths sections (handoff §3.8, §7 #3)."""

    def test_the_declarations(self):
        dsl = _load(BRD_TEXT)
        decls = {(d["id"], d["kind"]): d for d in dsl["lfg_dungeon_declarations"]}
        section = decls[(308, "dungeon")]
        self.assertEqual(
            {k: section[k] for k in ("map_id", "like", "group", "flags", "min_level", "max_level", "target_level",
                                     "target_level_min", "target_level_max", "position", "last_encounter")},
            {"map_id": 230, "like": 30, "group": 1, "flags": 3, "min_level": 48, "max_level": 58, "target_level": 53,
             "target_level_min": 51, "target_level_max": 54, "position": (595.0, -92.0, -45.0, 1.5),
             "last_encounter": 235},
        )
        self.assertEqual(decls[(30, "override")]["edits"], {})
        self.assertEqual(decls[(30, "override")]["last_encounter"], 230)
        self.assertIsNone(decls[(276, "override")]["last_encounter"])
        self.assertEqual(decls[(311, "heroic")]["normal"], 308)

    def test_bad_arguments_raise(self):
        good = ("lfg_dungeon(308, 'S', map_id=230, like=30, min_level=48, max_level=58, target_level=53, "
                "last_encounter=235)")
        for call in (
            good.replace("308", "250"),  # outside the lfgdungeons block
            good.replace("'S'", "''"),
            good.replace("map_id=230", "map_id=0"),
            good.replace("like=30", "like=True"),
            good.replace("max_level=58", "max_level=47"),
            good.replace("target_level=53", "target_level=59"),
            good.replace("last_encounter=235", "last_encounter=0"),
            good.replace("last_encounter=235", "last_encounter='235'"),
            good[:-1] + ", position=(1.0, 2.0))",
            good[:-1] + ", target_level_min=54)",
            good[:-1] + ", target_level_max=52)",
            good[:-1] + ", flags=-1)",
            good[:-1] + ", group=0)",
            good.replace(", last_encounter=235", ""),  # required
            "lfg_override(30, last_encounter=-1)",
        ):
            with self.subTest(call=call), self.assertRaises((ValueError, TypeError)):
                _load(HEADER_SECTIONS + call + "\n")
        _load(HEADER_SECTIONS + good + "\n")
        _load(HEADER_SECTIONS + "lfg_override(30, last_encounter=230)\n")  # a final-boss move alone is an edit

    def test_the_target_levels_default_to_the_stock_shape_inside_the_window(self):
        dsl = _load(HEADER_SECTIONS + "lfg_dungeon(308, 'S', map_id=230, like=30, min_level=48, max_level=58, "
                                      "target_level=48, last_encounter=235)\n")
        decl = dsl["lfg_dungeon_declarations"][0]
        self.assertEqual((decl["target_level_min"], decl["target_level_max"]), (48, 49))

    def test_the_new_rows(self):
        dsl, out = _brd_run()
        self.assertEqual(out.errors, [])
        self.assertEqual(out.warnings, [])
        rows = {r["ID"]: r for r in dsl["lfg_dungeons"]}
        # 30 and 276 only move their final boss / start: the LFGDungeons rows stay stock and are not written
        self.assertEqual(sorted(rows), [300, 301, 308, 309, 310, 311, 312, 313])
        stock = _brd_stock()[30]
        section = rows[308]
        self.assertEqual(
            {k: section[k] for k in ("Name_Lang_enUS", "Name_Lang_deDE", "Name_Lang_Mask", "MapID", "TypeID",
                                     "Difficulty", "Flags", "Group_Id", "MinLevel", "MaxLevel", "Target_Level",
                                     "Target_Level_Min", "Target_Level_Max")},
            {"Name_Lang_enUS": "Blackrock Depths - Shadowforge City", "Name_Lang_deDE": "", "Name_Lang_Mask": MASK,
             "MapID": 230, "TypeID": 1, "Difficulty": 0, "Flags": 3, "Group_Id": 1, "MinLevel": 48, "MaxLevel": 58,
             "Target_Level": 53, "Target_Level_Min": 51, "Target_Level_Max": 54},
        )
        for column in ("TextureFilename", "Faction", "ExpansionLevel", "Description_Lang_Mask", "Order_Index"):
            self.assertEqual(section[column], stock[column], column)
        self.assertEqual((rows[309]["MinLevel"], rows[309]["MaxLevel"], rows[309]["Target_Level"]), (50, 60, 55))
        # the heroic copies of a declared row and of the stock rows
        for heroic, normal in ((310, 30), (311, 308), (312, 309), (313, 276)):
            row = rows[heroic]
            self.assertEqual((row["TypeID"], row["Difficulty"], row["MapID"], row["Group_Id"], row["MinLevel"]),
                             (5, 1, 230, 12, 60))
        self.assertEqual(rows[311]["Name_Lang_enUS"], "Blackrock Depths - Shadowforge City")
        self.assertEqual(rows[313]["Name_Lang_enUS"], "Blackrock Depths - Upper City")
        self.assertEqual(rows[310]["Name_Lang_deDE"], "Blackrock Depths - Prison (de)")

    def test_the_start_points(self):
        dsl, out = _brd_run()
        self.assertEqual(out.errors, [])
        positions = {t["dungeonId"]: (t["name"], t["position_x"], t["position_y"], t["position_z"], t["orientation"])
                     for t in dsl["lfg_dungeon_templates"]}
        self.assertEqual(positions, {
            308: ("Blackrock Depths - Shadowforge City", 595.0, -92.0, -45.0, 1.5),
            309: ("Blackrock Depths - Manufactory", 607.2, -47.8, -59.8, 0.2),
            276: ("Blackrock Depths - Upper City", 843.8, -167.8, -49.7, 3.1),
            # the heroic entries copy their normal entry's start (30's is the live stock row, not written)
            310: ("Blackrock Depths - Prison (Heroic)", 458.32, 26.52, -70.67, 4.95),
            311: ("Blackrock Depths - Shadowforge City (Heroic)", 595.0, -92.0, -45.0, 1.5),
            312: ("Blackrock Depths - Manufactory (Heroic)", 607.2, -47.8, -59.8, 0.2),
            313: ("Blackrock Depths - Upper City (Heroic)", 843.8, -167.8, -49.7, 3.1),
        })

    def test_the_final_bosses_move_and_the_heroic_copies_follow(self):
        dsl, out = _brd_run()
        self.assertEqual(out.errors, [])
        # normal rows: Gerstahn gives up 30, the Ring takes it, Bael'Gar and Argelmach end the new sections
        self.assertEqual(_links(dsl), {227: 0, 230: 30, 235: 308, 237: 309})
        link_227 = next(r for r in dsl["instance_encounters"] if r.get(lfg_dungeons.LINK) and r["entry"] == 227)
        self.assertEqual((link_227["creditType"], link_227["creditEntry"], link_227["comment"]),
                         (0, 9018, "High Interrogator Gerstahn"))
        # heroic copies: each heroic entry completes on the heroic copy of its normal entry's (edited) final boss
        self.assertEqual(_heroic_links(dsl), {227: 0, 230: 310, 234: 0, 235: 311, 237: 312, 245: 313})
        for heroic, encounter in ((310, 230), (311, 235), (312, 237), (313, 245)):
            self.assertTrue(any(f"lfg_heroic({heroic}, normal=" in n and
                                f"completes on heroic encounter {encounter + HEROIC_OFFSET}" in n for n in out.notes),
                            out.notes)
        self.assertTrue(any("encounter 227 no longer ends finder entry 30" in n for n in out.notes), out.notes)

    def test_a_run_over_the_deployed_links_writes_the_same_rows_and_emits_nothing(self):
        dsl, out = _brd_run()
        first = [dict(r) for r in dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)]
        deployed = {227: 0, 230: 30, 235: 308, 237: 309}
        dsl2, out2 = _brd_run(live_links=deployed)
        self.assertEqual(out2.errors, [])
        self.assertEqual(_links(dsl2), deployed)  # 227 stays declared: the base dump still says 30
        self.assertEqual(_heroic_links(dsl2), _heroic_links(dsl))
        live = [{c: r[c] for c in spell_tables.INSTANCE_ENCOUNTERS_COLUMNS} for r in _brd_credits(deployed).values()]
        self.assertEqual(render("instance_encounters", index_for("instance_encounters", live), first), "")

    def test_the_sql_blocks(self):
        dsl, _out = _brd_run()
        live = [{c: r[c] for c in spell_tables.INSTANCE_ENCOUNTERS_COLUMNS} for r in _brd_credits().values()]
        normal = [r for r in dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)]
        blocks = {
            "instance_encounters": render("instance_encounters", index_for("instance_encounters", live), normal),
            "lfgdungeons_dbc": render("lfgdungeons_dbc", index_for("lfgdungeons_dbc", []), dsl["lfg_dungeons"]),
            "lfg_dungeon_template": render("lfg_dungeon_template", index_for("lfg_dungeon_template", []),
                                           dsl["lfg_dungeon_templates"]),
        }
        self.assertIn("(227, 0, 9018, 0, 'High Interrogator Gerstahn')", blocks["instance_encounters"])
        self.assertIn("(230, 0, 10096, 30, 'Ring of Law')", blocks["instance_encounters"])
        self.assertIn("(235, 0, 9016, 308, 'Bael''Gar')", blocks["instance_encounters"])
        self.assertNotIn("(245,", blocks["instance_encounters"])  # unchanged: nothing written
        self.assertNotIn("_lfg", "".join(blocks.values()))
        self.assertIn("'Blackrock Depths - Shadowforge City'", blocks["lfgdungeons_dbc"])
        self.assertIn("(276, 'Blackrock Depths - Upper City', 843.8, -167.8, -49.7, 3.1, 0)",
                      blocks["lfg_dungeon_template"])
        done = codestyle_sql("\n\n".join(blocks.values()))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_second_expand_replaces_and_dropping_the_declarations_clears(self):
        dsl, _out = _brd_run()
        lfg_dungeons.expand(dsl, lambda: _inputs(stock_dungeons=_brd_stock(), encounters=_brd_encounters(),
                                                 credits=_brd_credits(), base_credits=_brd_credits()))
        self.assertEqual(_links(dsl), {227: 0, 230: 30, 235: 308, 237: 309})
        self.assertEqual(len([r for r in dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)]), 4)
        dsl["lfg_dungeon_declarations"] = []
        dsl["lfg_group_declarations"] = []
        lfg_dungeons.expand(dsl, lambda: self.fail("nothing declared: no inputs"))
        self.assertEqual(_links(dsl), {})
        self.assertEqual(set(_heroic_links(dsl).values()), {0})

    def test_errors(self):
        heroics = SECTION_HEROICS
        cases = {
            "is not a normal encounter of map 230": (BRD_TEXT.replace("last_encounter=235", "last_encounter=167"), {}),
            "has no instance_encounters row": (BRD_TEXT, {"credits": {e: r for e, r in _brd_credits().items()
                                                                      if e != 237}}),
            "already ends finder entry 308": (BRD_TEXT.replace("last_encounter=237", "last_encounter=235"), {}),
            "finder entry 276 loses its final boss": (BRD_TEXT.replace("last_encounter=237", "last_encounter=245"),
                                                      {}),
            "like=276 is not a stock normal dungeon row": (BRD_TEXT, {"stock_dungeons": {
                **_brd_stock(), 276: _dungeon_row(276, "x", 230, type_id=2)}}),
            "group 7 is neither stock nor declared": (BRD_TEXT.replace("target_level=55,", "target_level=55, group=7,"),
                                                      {}),
            "LFGDungeons id 308 is a stock row": (BRD_TEXT, {"stock_dungeons": {**_brd_stock(),
                                                                                308: _brd_stock()[30]}}),
            "no stock DungeonEncounter.dbc": (BRD_TEXT, {"encounters": None}),
            "is not a stock normal dungeon row (LFGDungeons TypeID 1, Difficulty 0, not seasonal) or an lfg_dungeon()":
                (BRD_TEXT.replace(SECTIONS, "lfg_override(30, last_encounter=230)\n"
                                  "lfg_override(276, position=(843.8, -167.8, -49.7, 3.1))\n").replace(heroics, "")
                 + "lfg_heroic(311, normal=308, group=12)\n", {}),
        }
        cases["like=276 is not a stock normal dungeon row"] = (
            BRD_TEXT.replace("like=30, min_level=50", "like=276, min_level=50"),
            cases["like=276 is not a stock normal dungeon row"][1],
        )
        for expected, (text, kw) in cases.items():
            with self.subTest(expected=expected):
                _dsl, out = _brd_run(text, **kw)
                self.assertTrue(any(expected in e for e in out.errors), out.errors)

    def test_a_like_row_of_another_map_warns_and_no_position_is_a_note(self):
        text = BRD_TEXT.replace("like=30, min_level=50", "like=6, min_level=50").replace(
            ", position=(607.2, -47.8, -59.8, 0.2)", "")
        dsl, out = _brd_run(text)
        self.assertEqual(out.errors, [])
        self.assertTrue(any("like=6 is on map 36" in w for w in out.warnings), out.warnings)
        self.assertTrue(any("lfg_dungeon(309) has no position" in n for n in out.notes), out.notes)
        self.assertNotIn(309, {t["dungeonId"] for t in dsl["lfg_dungeon_templates"]})

    def test_a_cleared_row_deleted_live_stays_deleted(self):
        credits = {e: r for e, r in _brd_credits().items() if e != 227}
        dsl, out = _brd_run(credits=credits)
        self.assertEqual(out.errors, [])
        self.assertNotIn(227, _links(dsl))

    def test_the_patch_z_merge(self):
        dsl, _out = _brd_run()
        base = list(_brd_stock().values())
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(dsl["lfg_dungeons"]))
        self.assertEqual(merged[30], _brd_stock()[30])  # the stock rows 30 / 276 are not touched
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONS, list(merged.values()), base)
        back = {r["ID"]: r for r in scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONS)}
        self.assertEqual(len(back), len(base) + 8)
        self.assertEqual((back[308]["TypeID"], back[308]["Group_Id"], back[308]["MapID"], back[308]["TextureFilename"]),
                         (1, 1, 230, "BLACKROCKDEPTHS"))
        self.assertEqual(back[309]["Name_Lang_enUS"], "Blackrock Depths - Manufactory")
        self.assertEqual((back[312]["TypeID"], back[312]["Difficulty"]), (5, 1))

    def test_over_the_stock_files(self):
        dungeons_file = state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename
        groups_file = state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONGROUP.dbc_filename
        encounters_file = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        if not all(f.is_file() for f in (dungeons_file, groups_file, encounters_file)):
            self.skipTest("stock LFGDungeons / LFGDungeonGroup / DungeonEncounter.dbc not in var/extractors/dbc/")
        base = dbcfile.read_dbc(dungeons_file, dbcfmt.LFGDUNGEONS)
        encounters = {int(r["ID"]): r for r in dbcfile.read_dbc(encounters_file, dbcfmt.DUNGEONENCOUNTER)}
        credits = _brd_credits()
        for entry in range(227, 246):  # the rest of the 19, no link
            credits.setdefault(entry, {"entry": entry, "creditType": 0, "creditEntry": entry, "lastEncounterDungeon": 0,
                                       "comment": encounters[entry]["Name_Lang_enUS"]})
        dsl, out = _brd_run(stock_dungeons={int(r["ID"]): r for r in base}, encounters=encounters, credits=credits,
                            base_credits=credits,
                            stock_groups={int(r["ID"]): r for r in dbcfile.read_dbc(groups_file,
                                                                                    dbcfmt.LFGDUNGEONGROUP)})
        self.assertEqual(out.errors, [])
        self.assertEqual(out.warnings, [])
        self.assertEqual(_links(dsl), {227: 0, 230: 30, 235: 308, 237: 309})
        stock_30 = next(r for r in base if r["ID"] == 30)
        rows = {r["ID"]: r for r in dsl["lfg_dungeons"]}
        for column in ("TextureFilename", "Faction", "ExpansionLevel", "Description_Lang_Mask", "Name_Lang_Mask"):
            self.assertEqual(rows[308][column], stock_30[column], column)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(dsl["lfg_dungeons"]))
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONS, list(merged.values()), base)
        back = {r["ID"]: r for r in scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONS)}
        self.assertEqual(len(back), len(base) + 8)  # 300, 301, 308-313; no stock row written
        self.assertEqual((back[308]["Name_Lang_enUS"], back[308]["TextureFilename"], back[308]["Group_Id"]),
                         ("Blackrock Depths - Shadowforge City", "BLACKROCKDEPTHS", 1))
        self.assertEqual({c: back[30][c] for c in ("TypeID", "Group_Id", "MinLevel", "MaxLevel", "Name_Lang_enUS")},
                         {c: stock_30[c] for c in ("TypeID", "Group_Id", "MinLevel", "MaxLevel", "Name_Lang_enUS")})


class RenderTest(unittest.TestCase):
    TABLES = ("lfgdungeons_dbc", "lfg_dungeon_template", "instance_encounters")

    def setUp(self):
        text = DECLARATIONS + "lfg_heroic(304, normal=40, group=12)\n"
        self.dsl, out = _expand(text, dungeons=[_heroic_dungeon(36, "Deadmines"), _heroic_dungeon(329, "Strat")],
                                credits=[_credit(1006, 6), _credit(1033, 40, 10813)])
        self.assertEqual(out.errors, [])
        self.blocks = {t: render(t, index_for(t, []), self.dsl[spec_for(t).registry_key]) for t in self.TABLES}

    def test_blocks(self):
        self.assertIn("DELETE FROM `lfgdungeons_dbc` WHERE (`ID`) IN ((300), (301), (304));",
                      self.blocks["lfgdungeons_dbc"].replace("\n", " ").replace("  ", " "))
        self.assertIn("'Random Classic Heroic'", self.blocks["lfgdungeons_dbc"])
        self.assertIn("(304, 'Stratholme - Main Gate (Heroic)', 3395.09, -3380.25, 142.702, 0.1, 0)",
                      self.blocks["lfg_dungeon_template"])
        self.assertIn("(1006, 0, 639, 301, 'x - Heroic')", self.blocks["instance_encounters"])
        self.assertNotIn("_normal_lfg", "".join(self.blocks.values()))

    def test_the_blocks_pass_the_real_sql_codestyle_check(self):
        done = codestyle_sql("\n\n".join(self.blocks.values()))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        for table, rendered in self.blocks.items():
            with self.subTest(table=table):
                spec = spec_for(table)
                live = read_back(rendered, table, spec.columns)
                self.assertEqual(len(live), len(self.dsl[spec.registry_key]))
                self.assertEqual(render(table, index_for(table, live), self.dsl[spec.registry_key]), "")

    def test_dropping_the_declarations_prunes_the_rows(self):
        for table in ("lfgdungeons_dbc", "lfg_dungeon_template"):
            with self.subTest(table=table), generated_file(self.blocks[table]):
                spec = spec_for(table)
                emitted = spell_tables.load_generated_table_rows(table, spec.key_columns)
                result = index_for(table, emitted, emitted=emitted).rows_to_prune(spec, [])
                self.assertEqual(len(result.keys), len(self.dsl[spec.registry_key]))
                self.assertFalse(result.breaker_tripped)


class ScopeTest(unittest.TestCase):
    def test_tables_and_spaces(self):
        self.assertEqual(scope.TABLE_IDS["lfgdungeons_dbc"], ("ID", "lfgdungeons"))
        self.assertEqual(scope.TABLE_IDS["lfg_dungeon_template"], ("dungeonId", "lfgdungeons"))
        self.assertEqual(scope.DBC_SPACES["LFGDungeons"], "lfgdungeons")
        self.assertEqual(scope.DBC_SPACES["LFGDungeonGroup"], "lfgdungeongroup")

    def test_a_scoped_final_boss_needs_its_finder_entry_live(self):
        own = scope.Ownership(frozenset({"deadmines"}))
        sql = ("INSERT INTO `instance_encounters` (`entry`, `creditType`, `creditEntry`, `lastEncounterDungeon`, "
               "`comment`) VALUES\n(1006, 0, 639, 301, 'Edwin VanCleef - Heroic');")
        errors = scope.reference_errors([], own, {}, sql, {"lfgdungeons": {301}})
        self.assertEqual(len(errors), 1)
        self.assertIn("instance_encounters 1006 needs lfgdungeons 301", errors[0])
        self.assertEqual(scope.reference_errors([], own, {}, sql, {}), [])  # live already: fine

    def test_full_run_inserts_are_seen(self):
        sql = ("INSERT INTO `lfgdungeons_dbc` (`ID`, `MapID`) VALUES\n(301, 36);")
        self.assertEqual(scope.inserted_ids(sql), {"lfgdungeons": {301}})


class WiringTest(unittest.TestCase):
    def test_generate_wiring(self):
        text = (TOOL_ROOT / "generate.py").read_text()
        self.assertIn("lfg_finder.expand(dsl_classes, lambda: lfg_finder.load_inputs(spell_table_index))", text)
        self.assertIn("dungeon_expansion.errors += lfg_expansion.errors", text)
        self.assertIn("dbcfmt.LFGDUNGEONS: lfg_finder.client_dungeon_rows(", text)
        self.assertIn("dbcfmt.LFGDUNGEONGROUP: lfg_finder.client_group_rows(", text)
        names = [spec.name for spec in spell_tables.SPELL_TABLES]
        self.assertIn("lfgdungeons_dbc", names)
        self.assertIn("lfg_dungeon_template", names)

    def test_the_heroic_encounter_rows_carry_the_normal_link(self):
        stock = {
            167: {"ID": 167, "MapID": 36, "Difficulty": 0, "OrderIndex": 6, "Bit": 6, "Name_Lang_enUS": "VanCleef"},
        }
        dsl = {key: [] for key in registry.MERGE_KEYS}
        dsl["dungeons"] = [{"id": 36, "map_id": 36, "name": "Deadmines", "heroic_entries": {},
                            "heroic": {"encounter_ids": (1006,), "spawn_mask": False, "event_spawns": False}}]
        out = dungeon_heroic.expand(dsl, lambda: dungeon_heroic.LiveWorld(
            creature_templates={}, stock_encounters=stock, instance_encounters={
                167: {"entry": 167, "creditType": 0, "creditEntry": 639, "lastEncounterDungeon": 6, "comment": "V"}},
        ))
        self.assertEqual(out.errors, [])
        (credit,) = dsl["instance_encounters"]
        self.assertEqual((credit["lastEncounterDungeon"], credit["_normal_lfg"]), (0, 6))


class RealSourceTest(unittest.TestCase):
    """source/world/lfg_classic_heroic.py and lfg_classic_sections.py with the real ids.yaml, over the stock files when
    they are extracted."""

    @classmethod
    def setUpClass(cls):
        cls.ids_cfg = source.load_ids(generate.SOURCE_DIR / "ids.yaml")
        # generate.py loads source/world/*.py in file order: the heroic file, then the Blackrock Depths sections
        regs = [registry.load_class_file(generate.SOURCE_DIR / "world" / name, ids_cfg=cls.ids_cfg)
                for name in ("lfg_classic_heroic.py", "lfg_classic_sections.py")]
        cls.dsl = {key: [row for reg in regs for row in getattr(reg, key)] for key in registry.MERGE_KEYS}

    def test_the_declarations(self):
        self.assertEqual([(d["id"], d["kind"], d.get("normal")) for d in self.dsl["lfg_dungeon_declarations"]], [
            (300, "random", None), (301, "heroic", 6), (302, "heroic", 8), (303, "heroic", 2), (304, "heroic", 40),
            (305, "heroic", 274), (44, "override", None), (306, "heroic", 32), (307, "heroic", 44),
            # Blackrock Depths: the four heroic entries (310-313), then the normal side (sections file)
            (310, "heroic", 30), (311, "heroic", 308), (312, "heroic", 309), (313, "heroic", 276),
            (30, "override", None), (308, "dungeon", None), (309, "dungeon", None), (276, "override", None),
        ])
        random = self.dsl["lfg_dungeon_declarations"][0]
        self.assertEqual((random["min_level"], random["max_level"], random["group"]), (60, 62, 12))

    def test_over_the_stock_files(self):
        dungeons_file = state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename
        groups_file = state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONGROUP.dbc_filename
        if not (dungeons_file.is_file() and groups_file.is_file()):
            self.skipTest("stock LFGDungeons.dbc / LFGDungeonGroup.dbc not in var/extractors/dbc/")
        dsl = {k: list(v) for k, v in self.dsl.items()}
        dsl["dungeons"] = [_heroic_dungeon(m, n) for m, n in ((36, "Deadmines"), (33, "Shadowfang Keep"),
                                                               (289, "Scholomance"), (329, "Stratholme"),
                                                               (229, "Blackrock Spire"),
                                                               (230, "Blackrock Depths"))]
        dsl["instance_encounters"] = [_credit(1006, 6), _credit(1014, 8), _credit(1027, 2), _credit(1033, 40),
                                      _credit(1040, 274), _credit(1049, 32, 9568), _credit(1054, 44, 10363),
                                      *_brd_heroic_credits()]
        out = lfg_dungeons.expand(dsl, lambda: lfg_dungeons.LfgInputs(
            stock_dungeons={int(r["ID"]): r for r in dbcfile.read_dbc(dungeons_file, dbcfmt.LFGDUNGEONS)},
            stock_groups={int(r["ID"]): r for r in dbcfile.read_dbc(groups_file, dbcfmt.LFGDUNGEONGROUP)},
            positions={**POSITIONS, 32: {"dungeonId": 32, "name": "Lower Blackrock Spire", "position_x": 78.5083,
                                         "position_y": -225.044, "position_z": 49.839, "orientation": 5.1,
                                         "VerifiedBuild": 0},
                       30: {"dungeonId": 30, "name": "Blackrock Depths - Prison", "position_x": 458.32,
                            "position_y": 26.52, "position_z": -70.67, "orientation": 4.95, "VerifiedBuild": 0},
                       276: {"dungeonId": 276, "name": "Blackrock Depths - Upper City", "position_x": 458.32,
                             "position_y": 26.52, "position_z": -70.67, "orientation": 4.95, "VerifiedBuild": 0}},
            encounters=_brd_encounters(), credits=_brd_credits(), base_credits=_brd_credits(),
        ))
        self.assertEqual(out.errors, [])
        self.assertEqual(out.warnings, [])
        names = {r["ID"]: (r["Name_Lang_enUS"], r["MapID"], r["TypeID"], r["Difficulty"], r["Group_Id"])
                 for r in dsl["lfg_dungeons"]}
        self.assertEqual(names, {
            300: ("Random Classic Heroic", 0, 6, 1, 12), 301: ("Deadmines", 36, 5, 1, 12),
            302: ("Shadowfang Keep", 33, 5, 1, 12), 303: ("Scholomance", 289, 5, 1, 12),
            304: ("Stratholme - Main Gate", 329, 5, 1, 12), 305: ("Stratholme - Service Entrance", 329, 5, 1, 12),
            306: ("Lower Blackrock Spire", 229, 5, 1, 12), 307: ("Upper Blackrock Spire", 229, 5, 1, 12),
            # the stock raid-type row 44, edited into a Classic dungeon entry (the Blackrock Spire build)
            44: ("Upper Blackrock Spire", 229, 1, 0, 1),
            # Blackrock Depths: two new normal sections and the four heroic entries (the Blackrock Depths build)
            308: ("Blackrock Depths - Shadowforge City", 230, 1, 0, 1),
            309: ("Blackrock Depths - Manufactory", 230, 1, 0, 1),
            310: ("Blackrock Depths - Prison", 230, 5, 1, 12),
            311: ("Blackrock Depths - Shadowforge City", 230, 5, 1, 12),
            312: ("Blackrock Depths - Manufactory", 230, 5, 1, 12),
            313: ("Blackrock Depths - Upper City", 230, 5, 1, 12),
        })
        self.assertEqual([c["lastEncounterDungeon"] for c in dsl["instance_encounters"][:7]],
                         [301, 302, 303, 304, 305, 306, 307])
        # each heroic section completes on the heroic copy of its last boss (227 Gerstahn 0, 230 Ring 310, 235 Bael'Gar
        # 311, 237 Argelmach 312, 245 the Emperor 313); the normal links follow (227 -> 0, 230 -> 30, 235 -> 308,
        # 237 -> 309, 245 stays 276)
        self.assertEqual(_heroic_links(dsl), {227: 0, 230: 310, 234: 0, 235: 311, 237: 312, 245: 313})
        self.assertEqual(_links(dsl), {227: 0, 230: 30, 235: 308, 237: 309})
        # row 44: a dungeon entry (Flags 3, levels 55-65), the rest of the stock row kept; row 307 copies it
        edited = next(r for r in dsl["lfg_dungeons"] if r["ID"] == 44)
        stock_44 = next(r for r in dbcfile.read_dbc(dungeons_file, dbcfmt.LFGDUNGEONS) if r["ID"] == 44)
        self.assertEqual(
            (edited["TypeID"], edited["Group_Id"], edited["Flags"], edited["MinLevel"], edited["MaxLevel"]),
            (1, 1, 3, 55, 65),
        )
        for column in ("MapID", "Difficulty", "TextureFilename", "ExpansionLevel", "Target_Level", "Name_Lang_enUS"):
            self.assertEqual(edited[column], stock_44[column], column)
        heroic_307 = next(r for r in dsl["lfg_dungeons"] if r["ID"] == 307)
        self.assertEqual((heroic_307["Flags"], heroic_307["Difficulty"], heroic_307["TypeID"], heroic_307["MinLevel"],
                          heroic_307["MaxLevel"]), (3, 1, 5, 60, 62))
        # the start point: 44 gets the declared one (short of the Dragonspire Hall trigger); 306 and 307 copy theirs
        positions = {t["dungeonId"]: (t["position_x"], t["position_y"], t["position_z"], t["orientation"])
                     for t in dsl["lfg_dungeon_templates"]}
        self.assertEqual(positions[44], (98.25, -300.75, 63.1, 4.94))
        self.assertEqual(positions[307], positions[44])
        self.assertEqual(positions[306], (78.5083, -225.044, 49.839, 5.1))
        # the Blackrock Depths starts (handoff 3.8): the three moved or new ones, each copied by its heroic entry
        self.assertEqual(positions[308], (544.0, -181.3, -36.0, 5.18))
        self.assertEqual(positions[309], (607.2, -47.8, -59.8, 6.05))
        self.assertEqual(positions[276], (843.8, -167.8, -49.7, 4.64))
        self.assertEqual((positions[311], positions[312], positions[313]),
                         (positions[308], positions[309], positions[276]))
        self.assertEqual(positions[310], (458.32, 26.52, -70.67, 4.95))  # section 1 keeps the dungeon entrance
        self.assertGreater(((98.25 - 102.43) ** 2 + (-300.75 + 319.17) ** 2 + (63.1 - 65.4635) ** 2) ** 0.5, 10 + 5)
        # Random 260's shape: Difficulty 1, Flags 3; our window and expansion.
        random = next(r for r in dsl["lfg_dungeons"] if r["ID"] == 300)
        self.assertEqual((random["Flags"], random["ExpansionLevel"], random["MinLevel"], random["MaxLevel"]),
                         (3, 0, 60, 62))
        # The merged client files: Classic Heroic lists right above Classic Dungeons.
        base = dbcfile.read_dbc(groups_file, dbcfmt.LFGDUNGEONGROUP)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_group_rows(dsl["lfg_groups"]))
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONGROUP, list(merged.values()), base)
        order = [r["ID"] for r in scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONGROUP)]
        self.assertEqual(order[:7], [5, 4, 3, 2, 12, 1, 9])
        base = dbcfile.read_dbc(dungeons_file, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(dsl["lfg_dungeons"]))
        blob = dbcfile.pack_client_dbc(dbcfmt.LFGDUNGEONS, list(merged.values()), base)
        back = {r["ID"]: r for r in scope.read_dbc_bytes(blob, dbcfmt.LFGDUNGEONS)}
        self.assertEqual(back[301]["TextureFilename"], back[6]["TextureFilename"])
        self.assertEqual(back[300]["Name_Lang_enUS"], "Random Classic Heroic")
        self.assertEqual(len(back), len(base) + 14)  # fourteen new ids (300-313); row 44 replaces a stock row
        self.assertEqual((back[44]["TypeID"], back[44]["Group_Id"], back[44]["Flags"]), (1, 1, 3))


if __name__ == "__main__":
    unittest.main()
