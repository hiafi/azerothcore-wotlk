"""
Dungeon finder declarations (lfg-classic-heroic): lib/dsl/lfg.py's lfg_group() / lfg_random() / lfg_heroic(), the rows
lib/lfg_dungeons.py builds from them, their SPELL_TABLES half (lfgdungeons_dbc, lfg_dungeon_template), the client
LFGDungeons.dbc / LFGDungeonGroup.dbc merge, the heroic final boss link, the scope reference check and the
generate.py wiring; then the real source/world/lfg_classic_heroic.py over the stock files.

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
    """source/world/lfg_classic_heroic.py with the real ids.yaml, over the stock files when they are extracted."""

    @classmethod
    def setUpClass(cls):
        cls.ids_cfg = source.load_ids(generate.SOURCE_DIR / "ids.yaml")
        reg = registry.load_class_file(generate.SOURCE_DIR / "world" / "lfg_classic_heroic.py", ids_cfg=cls.ids_cfg)
        cls.dsl = {key: list(getattr(reg, key)) for key in registry.MERGE_KEYS}

    def test_the_declarations(self):
        self.assertEqual([(d["id"], d["kind"], d.get("normal")) for d in self.dsl["lfg_dungeon_declarations"]], [
            (300, "random", None), (301, "heroic", 6), (302, "heroic", 8), (303, "heroic", 2), (304, "heroic", 40),
            (305, "heroic", 274),
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
                                                               (289, "Scholomance"), (329, "Stratholme"))]
        dsl["instance_encounters"] = [_credit(1006, 6), _credit(1014, 8), _credit(1027, 2), _credit(1033, 40),
                                      _credit(1040, 274)]
        out = lfg_dungeons.expand(dsl, lambda: lfg_dungeons.LfgInputs(
            stock_dungeons={int(r["ID"]): r for r in dbcfile.read_dbc(dungeons_file, dbcfmt.LFGDUNGEONS)},
            stock_groups={int(r["ID"]): r for r in dbcfile.read_dbc(groups_file, dbcfmt.LFGDUNGEONGROUP)},
            positions=dict(POSITIONS),
        ))
        self.assertEqual(out.errors, [])
        self.assertEqual(out.warnings, [])
        names = {r["ID"]: (r["Name_Lang_enUS"], r["MapID"], r["TypeID"], r["Difficulty"], r["Group_Id"])
                 for r in dsl["lfg_dungeons"]}
        self.assertEqual(names, {
            300: ("Random Classic Heroic", 0, 6, 1, 12), 301: ("Deadmines", 36, 5, 1, 12),
            302: ("Shadowfang Keep", 33, 5, 1, 12), 303: ("Scholomance", 289, 5, 1, 12),
            304: ("Stratholme - Main Gate", 329, 5, 1, 12), 305: ("Stratholme - Service Entrance", 329, 5, 1, 12),
        })
        self.assertEqual([c["lastEncounterDungeon"] for c in dsl["instance_encounters"]], [301, 302, 303, 304, 305])
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
        self.assertEqual(len(back), len(base) + 6)


if __name__ == "__main__":
    unittest.main()
