"""
dungeon() / heroic() (dungeon difficulties E1, WP-T1): the declaration, the `mapdifficulty_dbc` and
`dungeon_access_template` SPELL_TABLES entries, the client MapDifficulty.dbc merge and the generate.py ERRORs.

Covered: each validation raise; the heroic row matches Utgarde Keep's stock heroic row 143 in every column but the ids,
the map and the level in the message; both tables render DELETE-then-INSERT, pass the real codestyle-sql.py, converge
through the real readers and prune when the declaration goes; the merge over the stock file keeps every stock row and
the stock (MapID, Difficulty) order, and an empty merge is byte-identical; every lint branch; the Deadmines file.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dungeon_difficulty.py
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402,F401 - generate.py wires dungeon_checks; importing it proves the wiring loads
from lib import dbcfile, dbcfmt, dungeon_checks, source, spell_tables, sql_dump, state, trainer_state  # noqa: E402
from lib.dsl import dungeon as dungeon_dsl  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    REPO_ROOT, codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)

MD = "mapdifficulty_dbc"
ACCESS = "dungeon_access_template"
IDS_CFG = {"mapdifficulty": {"start": 1000, "end": 1099}, "dungeon_access": {"start": 122, "end": 199}}
STOCK_FILE = state.BASE_DBC_DIR / dbcfmt.MAPDIFFICULTY.dbc_filename

DEADMINES = '''
from lib.dsl.dungeon import dungeon, heroic

dungeon(36, "Deadmines", heroic=heroic(map_difficulty_id=1000, access_id=122, min_level=60))
dungeon(48, "Blackfathom Deeps")
'''


def _load(body: str = DEADMINES, ids_cfg=IDS_CFG) -> dict:
    return load_dsl(body, ids_cfg=ids_cfg)


def _raises(call: str, pattern: str, exc=ValueError) -> None:
    with unittest.TestCase().assertRaisesRegex(exc, pattern):
        _load(f"from lib.dsl.dungeon import dungeon, heroic\n{call}\n")


class LayoutTest(unittest.TestCase):
    def test_fmt_is_dbcfmt_h_with_the_index_written_n(self):
        text = (REPO_ROOT / "src/server/shared/DataStores/DBCfmt.h").read_text()
        stock = re.search(r'MapDifficultyEntryfmt\[\] = "([a-z]+)"', text).group(1)
        self.assertEqual(stock, "diisxxxxxxxxxxxxxxxxiix")
        self.assertEqual(dbcfmt.MAPDIFFICULTY.fmt, "n" + stock[1:])
        self.assertEqual(dbcfmt.MAPDIFFICULTY.index_column, "ID")

    def test_columns_are_the_base_dump_create_tables(self):
        base = trainer_state.BASE_SQL_DIR
        self.assertEqual(
            tuple(sql_dump.parse_create_table_columns(base / f"{MD}.sql", MD)), spell_tables.MAPDIFFICULTY_COLUMNS,
        )
        self.assertEqual(
            tuple(sql_dump.parse_create_table_columns(base / f"{ACCESS}.sql", ACCESS)),
            spell_tables.DUNGEON_ACCESS_TEMPLATE_COLUMNS,
        )

    def test_both_tables_are_keyed_on_their_id_and_prune_when_empty(self):
        self.assertEqual(spec_for(MD).key_columns, ("ID",))
        self.assertEqual(spec_for(ACCESS).key_columns, ("id",))
        self.assertTrue(spec_for(MD).prune_when_empty)
        self.assertTrue(spec_for(ACCESS).prune_when_empty)

    def test_mapdifficulty_is_not_an_all_tables_entry(self):
        # the SQL half goes out through SPELL_TABLES; ALL_TABLES would emit it a second time
        self.assertNotIn(dbcfmt.MAPDIFFICULTY, dbcfmt.ALL_TABLES)


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()

    def test_one_bookkeeping_entry_per_dungeon(self):
        entries = {e["id"]: e for e in self.dsl["dungeons"]}
        self.assertEqual(set(entries), {36, 48})
        self.assertEqual(entries[36]["name"], "Deadmines")
        self.assertEqual(entries[36]["heroic"]["map_difficulty_id"], 1000)
        self.assertEqual(entries[36]["heroic"]["access_id"], 122)
        self.assertIsNone(entries[48]["heroic"])

    def test_a_dungeon_without_heroic_emits_nothing(self):
        self.assertEqual([r["MapID"] for r in self.dsl["map_difficulties"]], [36])
        self.assertEqual([r["map_id"] for r in self.dsl["dungeon_access"]], [36])

    def test_the_heroic_row(self):
        row = self.dsl["map_difficulties"][0]
        self.assertEqual(row["id"], 1000)
        self.assertEqual(
            {c: row[c] for c in ("ID", "MapID", "Difficulty", "RaidDuration", "MaxPlayers")},
            {"ID": 1000, "MapID": 36, "Difficulty": 1, "RaidDuration": 86400, "MaxPlayers": 5},
        )
        self.assertEqual(row["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(row["Message_Lang_Mask"], 0xFF01FE)
        self.assertEqual(row["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        self.assertTrue(set(spell_tables.MAPDIFFICULTY_COLUMNS) <= set(row))
        for locale in dbcfmt.LOCALE_SUFFIXES[1:]:
            self.assertEqual(row[f"Message_Lang_{locale}"], "")

    def test_the_access_row(self):
        self.assertEqual(self.dsl["dungeon_access"], [{
            "id": 122, "map_id": 36, "difficulty": 1, "min_level": 60, "max_level": 0, "min_avg_item_level": 0,
            "comment": "Deadmines - Heroic",
        }])

    def test_overrides_reach_both_rows(self):
        dsl = _load(
            "from lib.dsl.dungeon import dungeon, heroic\n"
            "dungeon(36, 'Deadmines', heroic=heroic(map_difficulty_id=1001, access_id=123, min_level=58,\n"
            "        max_level=60, min_item_level=55, reset_seconds=3 * 86400, max_players=10, message='Go away.'))\n"
        )
        md, access = dsl["map_difficulties"][0], dsl["dungeon_access"][0]
        self.assertEqual((md["RaidDuration"], md["MaxPlayers"], md["Message_Lang_enUS"]), (259200, 10, "Go away."))
        self.assertEqual((access["min_level"], access["max_level"], access["min_avg_item_level"]), (58, 60, 55))

    def test_the_default_message_names_the_level(self):
        self.assertEqual(
            dungeon_dsl.heroic(map_difficulty_id=1000, access_id=122, min_level=42).message,
            "Heroic Difficulty requires you to be level 42.",
        )

    def test_heroic_arguments_are_keyword_only(self):
        with self.assertRaises(TypeError):
            dungeon_dsl.heroic(1000, 122, 60)

    def test_bad_heroic_values_raise(self):
        base = "map_difficulty_id=1000, access_id=122"
        for args, pattern in (
            (f"{base}, min_level=0", "min_level must be an int in 1..80"),
            (f"{base}, min_level=81", "min_level must be an int in 1..80"),
            (f"{base}, min_level=True", "min_level must be an int"),
            (f"{base}, min_level=60, max_level=59", "max_level must be 0"),
            (f"{base}, min_level=60, max_level=81", "max_level must be 0"),
            (f"{base}, min_level=60, min_item_level=-1", "min_item_level must be an int"),
            (f"{base}, min_level=60, min_item_level=65536", "min_item_level must be an int"),
            (f"{base}, min_level=60, reset_seconds=0", "reset_seconds must be a positive int"),
            (f"{base}, min_level=60, max_players=0", "max_players must be an int in 1..40"),
            (f"{base}, min_level=60, max_players=41", "max_players must be an int in 1..40"),
            (f"{base}, min_level=60, message=''", "message must be a non-empty string"),
            (f"{base}, min_level=60, message='x' * 201", "message must be a non-empty string"),
            ("map_difficulty_id='1000', access_id=122, min_level=60", "map_difficulty_id must be an int"),
            ("map_difficulty_id=1000, access_id=None, min_level=60", "access_id must be an int"),
        ):
            with self.subTest(args=args):
                _raises(f"heroic({args})", pattern)

    def test_bad_dungeon_values_raise(self):
        _raises("dungeon(0, 'X')", "map_id must be a Map.dbc id")
        _raises("dungeon('36', 'X')", "map_id must be a Map.dbc id")
        _raises("dungeon(36, '')", "name")
        _raises("dungeon(36, 'X', heroic={'min_level': 60})", "heroic must come from heroic")

    def test_ids_outside_their_blocks_raise(self):
        for args, pattern in (
            ("map_difficulty_id=753, access_id=122", "outside source/ids.yaml's mapdifficulty"),
            ("map_difficulty_id=1100, access_id=122", "outside source/ids.yaml's mapdifficulty"),
            ("map_difficulty_id=1000, access_id=121", "outside source/ids.yaml's dungeon_access"),
            ("map_difficulty_id=1000, access_id=200", "outside source/ids.yaml's dungeon_access"),
        ):
            with self.subTest(args=args):
                _raises(f"dungeon(36, 'X', heroic=heroic({args}, min_level=60))", pattern)

    def test_a_missing_block_raises(self):
        with self.assertRaisesRegex(ValueError, "needs source/ids.yaml's `mapdifficulty` block"):
            _load(ids_cfg={})

    def test_outside_a_load_dungeon_raises(self):
        with self.assertRaises(RuntimeError):
            dungeon_dsl.dungeon(36, "Deadmines")

    def test_a_map_declared_twice_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text("from lib.dsl.dungeon import dungeon\ndungeon(36, 'Deadmines')\n")
            (Path(d) / "b.py").write_text("from lib.dsl.dungeon import dungeon\ndungeon(36, 'The Deadmines')\n")
            with self.assertRaisesRegex(registry.DuplicateIdError, "dungeons entry 36"):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)

    def test_one_id_on_two_maps_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name, map_id in (("a.py", 36), ("b.py", 48)):
                (Path(d) / name).write_text(
                    "from lib.dsl.dungeon import dungeon, heroic\n"
                    f"dungeon({map_id}, 'X', heroic=heroic(map_difficulty_id=1000, access_id={120 + map_id // 12},"
                    " min_level=60))\n"
                )
            with self.assertRaisesRegex(registry.DuplicateIdError, "map_difficulties entry 1000"):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)


@unittest.skipUnless(STOCK_FILE.is_file(), "var/extractors/dbc/MapDifficulty.dbc is not extracted")
class StockRowTest(unittest.TestCase):
    def setUp(self):
        self.stock = {r["ID"]: r for r in dbcfile.read_dbc(STOCK_FILE, dbcfmt.MAPDIFFICULTY)}

    def test_the_stock_file_has_the_rows_the_handoff_quotes(self):
        self.assertEqual(len(self.stock), 187)
        self.assertEqual(max(self.stock), 753)
        self.assertEqual(
            [(r["ID"], r["Difficulty"], r["MaxPlayers"], r["RaidDuration"]) for r in self.stock.values()
             if r["MapID"] == 36],
            [(10, 0, 5, 0)],
        )
        uk = self.stock[143]
        self.assertEqual((uk["MapID"], uk["Difficulty"]), (574, 1))
        self.assertEqual(uk["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 80.")

    def test_the_declared_row_is_utgarde_keeps_heroic_row_but_for_map_ids_and_level(self):
        declared = dungeon_checks.map_difficulty_client_rows(_load()["map_difficulties"])[1000]
        uk = self.stock[143]
        differing = {c for c in dbcfmt.MAPDIFFICULTY.columns if declared[c] != uk[c]}
        self.assertEqual(differing, {"ID", "MapID", "Message_Lang_enUS"})
        self.assertEqual(declared["Message_Lang_enUS"], uk["Message_Lang_enUS"].replace("80", "60"))


@unittest.skipUnless(STOCK_FILE.is_file(), "var/extractors/dbc/MapDifficulty.dbc is not extracted")
class ClientMergeTest(unittest.TestCase):
    def setUp(self):
        self.base_rows = dbcfile.read_dbc(STOCK_FILE, dbcfmt.MAPDIFFICULTY)

    def _merged(self) -> bytes:
        merged = {row["ID"]: row for row in self.base_rows}
        merged.update(dungeon_checks.map_difficulty_client_rows(_load()["map_difficulties"]))
        return dbcfile.pack_client_dbc(dbcfmt.MAPDIFFICULTY, list(merged.values()), self.base_rows)

    def test_an_empty_merge_is_the_stock_file_byte_for_byte(self):
        self.assertEqual(
            dbcfile.pack_client_dbc(dbcfmt.MAPDIFFICULTY, self.base_rows, self.base_rows), STOCK_FILE.read_bytes(),
        )

    def test_the_stock_file_is_ordered_by_map_and_difficulty_not_id(self):
        order = [(r["MapID"], r["Difficulty"]) for r in self.base_rows]
        self.assertEqual(order, sorted(order))
        ids = [r["ID"] for r in self.base_rows]
        self.assertNotEqual(ids, sorted(ids))

    def test_the_merged_file_round_trips_and_keeps_every_stock_row(self):
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "MapDifficulty.dbc"
            copy.write_bytes(self._merged())
            back = dbcfile.read_dbc(copy, dbcfmt.MAPDIFFICULTY)
        by_id = {r["ID"]: r for r in back}
        self.assertEqual(len(back), 188)
        for row in self.base_rows:
            self.assertEqual(by_id[row["ID"]], row)
        declared = dungeon_checks.map_difficulty_client_rows(_load()["map_difficulties"])[1000]
        self.assertEqual(by_id[1000], declared)
        # the new row sits right after Deadmines' normal row, as Onyxia's 323 sits after its 26
        position = [r["ID"] for r in back].index(1000)
        self.assertEqual(back[position - 1]["ID"], 10)
        self.assertEqual(back[position + 1]["MapID"], 37)

    def test_the_merged_file_is_a_valid_wdbc_of_the_server_layout(self):
        packed = self._merged()
        self.assertEqual(packed[:4], b"WDBC")
        self.assertEqual(int.from_bytes(packed[8:12], "little"), 23)  # fields, as MapDifficultyEntryfmt
        self.assertEqual(int.from_bytes(packed[12:16], "little"), 92)  # record size


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()
        self.md = render(MD, index_for(MD, []), self.dsl["map_difficulties"])
        self.access = render(ACCESS, index_for(ACCESS, []), self.dsl["dungeon_access"])

    def test_the_rows_render_delete_then_insert(self):
        self.assertTrue(self.md.startswith("DELETE FROM `mapdifficulty_dbc` WHERE (`ID`) IN ((1000));"))
        self.assertIn(
            "(1000, 36, 1, 'Heroic Difficulty requires you to be level 60.', '', '', '', '', '', '', '', '', '', '', "
            "'', '', '', '', '', 16712190, 86400, 5, 'DUNGEON_DIFFICULTY_5PLAYER_HEROIC');",
            self.md,
        )
        self.assertTrue(self.access.startswith("DELETE FROM `dungeon_access_template` WHERE (`id`) IN ((122));"))
        self.assertIn("(122, 36, 1, 60, 0, 0, 'Deadmines - Heroic');", self.access)

    def test_the_blocks_pass_the_real_sql_codestyle_check(self):
        done = codestyle_sql(self.md + "\n\n" + self.access)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        for table, columns, key, rendered in (
            (MD, spell_tables.MAPDIFFICULTY_COLUMNS, "map_difficulties", self.md),
            (ACCESS, spell_tables.DUNGEON_ACCESS_TEMPLATE_COLUMNS, "dungeon_access", self.access),
        ):
            with self.subTest(table=table):
                live = read_back(rendered, table, columns)
                self.assertEqual(len(live), 1)
                self.assertEqual(render(table, index_for(table, live), self.dsl[key]), "")

    def test_a_changed_declaration_is_re_emitted(self):
        live = read_back(self.access, ACCESS, spell_tables.DUNGEON_ACCESS_TEMPLATE_COLUMNS)
        changed = [dict(self.dsl["dungeon_access"][0], min_level=58)]
        self.assertIn("(122, 36, 1, 58, 0, 0, 'Deadmines - Heroic');", render(ACCESS, index_for(ACCESS, live), changed))

    def test_dropping_the_declaration_prunes_both_rows(self):
        for table, rendered in ((MD, self.md), (ACCESS, self.access)):
            with self.subTest(table=table), generated_file(rendered):
                emitted = spell_tables.load_generated_table_rows(table, spec_for(table).key_columns)
                result = index_for(table, emitted, emitted=emitted).rows_to_prune(spec_for(table), [])
                self.assertEqual(len(result.keys), 1)
                self.assertFalse(result.breaker_tripped)


class LintTest(unittest.TestCase):
    STOCK = {
        10: {"ID": 10, "MapID": 36, "Difficulty": 0},
        143: {"ID": 143, "MapID": 574, "Difficulty": 1},
        67: {"ID": 67, "MapID": 574, "Difficulty": 0},
    }

    def setUp(self):
        self.dsl = _load()

    def _check(self, md=None, access=None, stock=STOCK, live_md=(), live_access=()):
        return dungeon_checks.check_dungeons(
            self.dsl["map_difficulties"] if md is None else md,
            self.dsl["dungeon_access"] if access is None else access,
            stock, list(live_md), list(live_access),
        )

    def test_the_deadmines_declaration_is_clean(self):
        self.assertEqual(self._check(), [])

    def test_its_own_earlier_output_is_not_a_clash(self):
        live_md = [{"ID": 1000, "MapID": 36, "Difficulty": 1}]
        live_access = [{"id": 122, "map_id": 36, "difficulty": 1}, {"id": 3, "map_id": 36, "difficulty": 0}]
        self.assertEqual(self._check(live_md=live_md, live_access=live_access), [])

    def test_a_map_with_no_stock_row_is_an_error(self):
        md = [dict(self.dsl["map_difficulties"][0], MapID=1)]
        errors = self._check(md=md)
        self.assertEqual(len(errors), 1)
        self.assertIn("map 1 has no stock MapDifficulty row", errors[0])

    def test_a_pair_stock_already_has_is_an_error(self):
        md = [dict(self.dsl["map_difficulties"][0], MapID=574)]
        errors = self._check(md=md)
        self.assertEqual(len(errors), 1)
        self.assertIn("already has row 143", errors[0])

    def test_a_live_overlay_row_for_the_pair_is_an_error(self):
        errors = self._check(live_md=[{"ID": 1050, "MapID": 36, "Difficulty": 1}])
        self.assertEqual(len(errors), 1)
        self.assertIn("mapdifficulty_dbc row(s) [1050]", errors[0])

    def test_a_live_access_row_for_the_pair_is_an_error(self):
        errors = self._check(live_access=[{"id": 99, "map_id": 36, "difficulty": 1}, {"id": 5, "map_id": None}])
        self.assertEqual(len(errors), 1)
        self.assertIn("dungeon_access_template 122", errors[0])
        self.assertIn("[99]", errors[0])

    def test_without_the_stock_file_the_stock_checks_are_skipped(self):
        md = [dict(self.dsl["map_difficulties"][0], MapID=1)]
        self.assertEqual(self._check(md=md, stock=None), [])

    def test_the_stock_file_error_names_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            message = dungeon_checks.stock_file_error(self.dsl["map_difficulties"], Path(d))
            self.assertIn("MapDifficulty row(s) 1000", message)
            self.assertIn("ac-worldserver", message)
            self.assertIsNone(dungeon_checks.stock_file_error([], Path(d)))

    def test_errors_for_run_wires_the_index_and_the_stock_file(self):
        class _Index:
            def __init__(self, md, access):
                self.rows = {MD: md, ACCESS: access}

            def live_rows(self, table):
                return self.rows[table]

        with tempfile.TemporaryDirectory() as d:
            errors = dungeon_checks.errors_for_run(self.dsl, _Index([], [{"id": 9, "map_id": 36, "difficulty": 1}]),
                                                   Path(d))
        self.assertEqual(len(errors), 2)
        self.assertIn("no stock MapDifficulty.dbc", errors[0])
        self.assertIn("[9]", errors[1])

    def test_the_summary_names_both_ids(self):
        notes = dungeon_checks.summary_notes(self.dsl["dungeons"])
        self.assertEqual(len(notes), 1)
        self.assertIn("Deadmines (map 36) heroic - MapDifficulty 1000", notes[0])
        self.assertIn("dungeon_access_template 122 (level 60+", notes[0])


class DeadminesFileTest(unittest.TestCase):
    """source/world/dungeons/deadmines.py, as generate.py loads it (source/world/ with the real ids.yaml)."""

    def test_the_real_declaration(self):
        ids = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=ids)
        deadmines = {e["map_id"]: e for e in reg.dungeons}[36]
        self.assertEqual(deadmines["name"], "Deadmines")
        md = {r["ID"]: r for r in reg.map_difficulties}[1000]
        self.assertEqual(
            (md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"], md["Message_Lang_Mask"]),
            (36, 1, 86400, 5, 0xFF01FE),
        )
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in reg.dungeon_access}[122]
        self.assertEqual(
            (access["map_id"], access["difficulty"], access["min_level"], access["max_level"],
             access["min_avg_item_level"]),
            (36, 1, 60, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
