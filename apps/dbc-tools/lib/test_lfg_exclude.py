"""
lfg_exclude() tests: the `disables` sourceType 8 rows it declares, their emission/prune through
SPELL_TABLES, and lint.check_lfg_exclusions against LFGDungeons.dbc. Fixtures only.

Run directly:

    python3 apps/dbc-tools/lib/test_lfg_exclude.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, lint, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

DISABLES_BASE = (
    "CREATE TABLE `disables` (\n"
    "  `sourceType` int unsigned NOT NULL,\n"
    "  `entry` int unsigned NOT NULL,\n"
    "  `flags` tinyint unsigned NOT NULL DEFAULT '0',\n"
    "  `params_0` varchar(255) NOT NULL DEFAULT '',\n"
    "  `params_1` varchar(255) NOT NULL DEFAULT '',\n"
    "  `comment` varchar(255) NOT NULL DEFAULT '',\n"
    "  PRIMARY KEY (`sourceType`,`entry`)\n"
    ") ENGINE=InnoDB;\n"
    "INSERT INTO `disables` VALUES (2, 230, 3, '', '', 'stock map disable, different sourceType');\n"
)

BRD = "from lib.dsl.registry import lfg_exclude\nlfg_exclude(230, 'Blackrock Depths')\n"


def _load(source: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "lfg.py"
        path.write_text(source)
        reg = registry.load_class_file(path)
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


def _dungeon(id_, name, map_id, type_id=1, min_level=47, max_level=57) -> dict:
    return {
        "ID": id_, "Name_Lang_enUS": name, "MapID": map_id, "TypeID": type_id,
        "MinLevel": min_level, "MaxLevel": max_level,
    }


class LfgExcludeRegistryTest(unittest.TestCase):
    def test_declares_lfg_map_row_with_normal_flag(self):
        (row,) = _load(BRD)["lfg_disables"]
        self.assertEqual(
            {c: row[c] for c in spell_tables.DISABLES_COLUMNS},
            {"sourceType": 8, "entry": 230, "flags": 1, "params_0": "", "params_1": "",
             "comment": "Blackrock Depths"},
        )

    def test_bad_arguments_raise(self):
        for call in ("lfg_exclude(-1, 'x')", "lfg_exclude('230', 'x')", "lfg_exclude(True, 'x')",
                     "lfg_exclude(230, '')"):
            with self.assertRaises(ValueError, msg=call):
                _load(f"from lib.dsl.registry import lfg_exclude\n{call}\n")

    def test_duplicate_declaration_across_files_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(BRD)
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


class LfgExcludeEmissionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.base, self.promoted, self.pending = root / "base", root / "promoted", root / "pending"
        for d in (self.base, self.promoted, self.pending):
            d.mkdir()
        (self.base / "disables.sql").write_text(DISABLES_BASE)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = self.base
        trainer_state.PROMOTED_SQL_DIR = self.promoted
        trainer_state.PENDING_SQL_DIR = self.pending

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _write_generated(self, blocks):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self.promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")

    def _blocks(self, dsl):
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), dsl)

    def test_emits_delete_then_insert_on_composite_key(self):
        (block,) = self._blocks(_load(BRD))
        self.assertIn("DELETE FROM `disables` WHERE (`sourceType`, `entry`) IN ((8, 230));", block)
        self.assertIn("(8, 230, 1, '', '', 'Blackrock Depths')", block)
        self.assertLess(block.index("DELETE"), block.index("INSERT"))

    def test_rerun_unchanged_is_silent(self):
        self._write_generated(self._blocks(_load(BRD)))
        self.assertEqual(self._blocks(_load(BRD)), [])

    def test_removing_last_exclusion_is_pruned_not_breaker_blocked(self):
        self._write_generated(self._blocks(_load(BRD)))
        blocks, report = spell_tables.render_prune_blocks(spell_tables.load_spell_table_index(), _load(""))
        (block,) = blocks
        self.assertIn("DELETE FROM `disables` WHERE (`sourceType`, `entry`) IN ((8, 230));", block)
        self.assertFalse(any("SKIPPED disables" in line for line in report))

    def test_other_tables_keep_the_breaker(self):
        spec = next(s for s in spell_tables.SPELL_TABLES if s.name == "spell_script_names")
        self.assertFalse(spec.prune_when_empty)


class LfgExclusionCheckTest(unittest.TestCase):
    DUNGEONS = {
        30: _dungeon(30, "Blackrock Depths - Prison", 230),
        276: _dungeon(276, "Blackrock Depths - Upper City", 230, min_level=51, max_level=61),
        258: _dungeon(258, "Random Classic Dungeon", 0, type_id=6),
        999: _dungeon(999, "Some Zone Event", 1, type_id=4),
    }

    def test_note_lists_every_entry_on_the_map(self):
        errors, (note,) = lint.check_lfg_exclusions(_load(BRD)["lfg_disables"], self.DUNGEONS)
        self.assertEqual(errors, [])
        self.assertIn("30 Blackrock Depths - Prison (dungeon, 47-57)", note)
        self.assertIn("276 Blackrock Depths - Upper City", note)

    def test_map_without_instance_entry_is_an_error(self):
        for map_id in (999, 0, 1):  # unknown, random entries' map, a zone event's map
            rows = _load(f"from lib.dsl.registry import lfg_exclude\nlfg_exclude({map_id}, 'x')\n")["lfg_disables"]
            errors, notes = lint.check_lfg_exclusions(rows, self.DUNGEONS)
            self.assertEqual(len(errors), 1, map_id)
            self.assertEqual(notes, [])

    def test_missing_stock_dbc_is_an_error_only_when_declared(self):
        (error,), _ = lint.check_lfg_exclusions(_load(BRD)["lfg_disables"], None)
        self.assertIn("LFGDungeons.dbc", error)
        self.assertEqual(lint.check_lfg_exclusions([], None), ([], []))


class LfgDungeonsFormatTest(unittest.TestCase):
    TABLE = dbcfmt.LFGDUNGEONS

    def test_round_trips_the_columns_the_check_reads(self):
        row = {c: 0 for c in self.TABLE.columns}
        row.update({c: "" for c, f in zip(self.TABLE.columns, self.TABLE.fmt) if f == "s"})
        row.update(ID=30, Name_Lang_enUS="Blackrock Depths - Prison", MapID=230, TypeID=1, MinLevel=47)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / self.TABLE.dbc_filename
            path.write_bytes(dbcfile.pack_dbc_bytes(self.TABLE, [row]))
            (out,) = dbcfile.read_dbc(path, self.TABLE)
        self.assertEqual(
            (out["ID"], out["Name_Lang_enUS"], out["MapID"], out["TypeID"], out["MinLevel"]),
            (30, "Blackrock Depths - Prison", 230, 1, 47),
        )

    @unittest.skipUnless((state.BASE_DBC_DIR / "LFGDungeons.dbc").is_file(), "stock LFGDungeons.dbc not extracted")
    def test_stock_file_reads(self):
        rows = state.load_stock_rows(self.TABLE)
        self.assertEqual(rows[30]["MapID"], 230)
        self.assertEqual(rows[30]["Name_Lang_enUS"], "Blackrock Depths - Prison")


if __name__ == "__main__":
    unittest.main()
