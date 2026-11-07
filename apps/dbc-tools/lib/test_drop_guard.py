"""The general drop guard (lib/drop_guard.py): what counts as a drop in the SQL and in the client patch, what this
checkout "knows", and when a write run stops. The live DB is a stub; the archive is a real MPQ written with smpq."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfile, drop_guard, item_sets, mpq_writer  # noqa: E402

IDS = {
    "spell": {"start": 200000, "end": 209999},
    "talent": {"start": 60000, "end": 60799},
    "talenttab": {"start": 60800, "end": 60999},
    "skilllineability": {"start": 30400, "end": 30999},
    "item": {"start": 70000, "end": 79999},
    "item_set": {"start": 1000, "end": 1099},
    "item_extended_cost": {"start": 3000, "end": 3199},
    "creature": {"start": 300000, "end": 300999},
    "npc_tools": {"start": 900000, "end": 900099},
    "creature_heroic": {"start": 310000, "end": 311999},
}
FULL_BLOCK_SQL = (
    "DELETE FROM `spell_dbc` WHERE `ID` BETWEEN 200000 AND 200099;\n"
    "DELETE FROM `spell_dbc` WHERE `ID` BETWEEN 200101 AND 209999;\n"
    "INSERT INTO `spell_dbc` (`ID`, `x`) VALUES\n(200001, 0),\n(205214, 0);\n"
)


def _set_rows(ids) -> list[dict]:
    rows = []
    for row_id in ids:
        row = dbcfile.empty_row(item_sets.ITEMSET)
        row["ID"] = row_id
        rows.append(row)
    return rows


class SqlDropsTest(unittest.TestCase):
    def test_live_rows_the_block_deletes_and_does_not_reinsert(self):
        live = {"spell_dbc": {200001, 205214, 205282, 200100}, "creature_template": {300420}}
        self.assertEqual(drop_guard.sql_drops(FULL_BLOCK_SQL, live), {"spell_dbc": [205282]})

    def test_explicit_and_keyed_deletes(self):
        sql = ("DELETE FROM `creature_template_model` WHERE (`CreatureID`, `Idx`) IN ((300420, 0), (300421, 0));\n"
               "INSERT INTO `creature_template_model` (`CreatureID`, `Idx`) VALUES\n(300420, 0);\n"
               "DELETE FROM `item_template` WHERE `entry` IN (71000);")
        live = {"creature_template_model": {300420, 300421}, "item_template": {71000, 71001}}
        self.assertEqual(drop_guard.sql_drops(sql, live),
                         {"creature_template_model": [300421], "item_template": [71000]})

    def test_no_sql_no_drops(self):
        self.assertEqual(drop_guard.sql_drops(None, {"spell_dbc": {205282}}), {})


class KnownIdsTest(unittest.TestCase):
    def test_only_rows_this_checkout_inserted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "rev_1.sql").write_text(
                "INSERT INTO `spell_dbc` (`ID`, `x`) VALUES\n(205282, 0),\n(205283, 205304);\n"
                "INSERT INTO `spell_proc` (`SpellId`) VALUES\n(205348, 0);\n"
            )
            with mock.patch.object(drop_guard, "BASE_SQL_DIR", tmp / "base"), \
                    mock.patch.object(drop_guard.trainer_state, "update_files",
                                      lambda pending_dir=None: [tmp / "rev_1.sql"]):
                known = drop_guard.known_ids("spell_dbc", [205282, 205304, 205348], tmp)
        # 205304 only appears as a value, 205348 only in another table's INSERT
        self.assertEqual(known, {205282})


class ClientDropsTest(unittest.TestCase):
    TABLES = {"ItemSet.dbc": item_sets.ITEMSET}

    def test_full_run_and_repack(self):
        deployed = {"DBFilesClient/ItemSet.dbc": dbcfile.pack_dbc_bytes(item_sets.ITEMSET, _set_rows([1, 1000, 1001]))}
        shipped = {"ItemSet.dbc": dbcfile.pack_dbc_bytes(item_sets.ITEMSET, _set_rows([1, 1000]))}
        self.assertEqual(drop_guard.client_drops(deployed, shipped, self.TABLES, IDS, True), {"ItemSet.dbc": [1001]})
        # a full run that ships no ItemSet.dbc at all drops every custom row of it
        self.assertEqual(drop_guard.client_drops(deployed, {}, self.TABLES, IDS, True),
                         {"ItemSet.dbc": [1000, 1001]})
        # a repack leaves a member it does not replace alone
        self.assertEqual(drop_guard.client_drops(deployed, {}, self.TABLES, IDS, False), {})


class CheckTest(unittest.TestCase):
    def archive(self, tmp: Path, ids) -> Path:
        path = tmp / "patch-Z.mpq"
        mpq_writer.write_mpq(path, {"DBFilesClient\\ItemSet.dbc": dbcfile.pack_dbc_bytes(item_sets.ITEMSET,
                                                                                          _set_rows(ids))})
        return path

    def check(self, tmp, *, live=None, archive=None, shipped=None, known=(), allow=False):
        reader = (lambda command, tables, ids_cfg: {t: set(live.get(t, ())) for t in tables}) if live else None
        with mock.patch.object(drop_guard, "known_ids", lambda table, ids, pending: set(ids) & set(known)):
            return drop_guard.check(
                sql_text=FULL_BLOCK_SQL, shipped=shipped or {}, replaces_archive=True, deployed_archive=archive,
                tables={"ItemSet.dbc": item_sets.ITEMSET}, ids_cfg=IDS, pending_dir=tmp, allow=allow,
                live_command=["mysql"] if live else None, live_reader=reader or drop_guard.live_ids,
            )

    def test_stale_branch_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            try:
                archive = self.archive(tmp, [1, 1000])
            except RuntimeError as error:  # no smpq on this machine
                self.skipTest(str(error))
            result = self.check(tmp, live={"spell_dbc": {205214, 205282}}, archive=archive)
        self.assertTrue(result.refused)
        text = "\n".join(result.lines)
        self.assertIn("spell_dbc: 1 live row(s) this checkout never wrote: 205282", text)
        self.assertIn("ItemSet.dbc: 1 row(s)", text)
        self.assertIn("--allow-drop", text)

    def test_own_removals_are_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            try:
                archive = self.archive(tmp, [1, 1000])
            except RuntimeError as error:
                self.skipTest(str(error))
            result = self.check(tmp, live={"spell_dbc": {205282}}, archive=archive, known={205282, 1000})
        self.assertFalse(result.refused)
        self.assertTrue(any(line.startswith("note: drop guard: spell_dbc: deleting 1") for line in result.lines))

    def test_skips_and_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.check(Path(tmp))
            self.assertFalse(result.refused)
            self.assertEqual(len([line for line in result.lines if "skipped" in line]), 2)
            allowed = self.check(Path(tmp), live={"spell_dbc": {205282}}, allow=True)
        self.assertFalse(allowed.refused)
        self.assertIn("--allow-drop", allowed.lines[0])

    def test_a_failing_db_command_stops(self):
        def broken(command, tables, ids_cfg):
            raise drop_guard.GuardError("mysql failed (1)")

        with tempfile.TemporaryDirectory() as tmp:
            result = drop_guard.check(
                sql_text=FULL_BLOCK_SQL, shipped={}, replaces_archive=True, deployed_archive=None, tables={},
                ids_cfg=IDS, pending_dir=Path(tmp), allow=False, live_command=["mysql"], live_reader=broken,
            )
        self.assertTrue(result.refused)


class CommandTest(unittest.TestCase):
    def test_env_then_local_config(self):
        with mock.patch.dict("os.environ", {"DBC_TOOLS_MYSQL": "docker exec -i db mysql -uroot -px"}):
            self.assertEqual(drop_guard.mysql_command(), ["docker", "exec", "-i", "db", "mysql", "-uroot", "-px"])


if __name__ == "__main__":
    unittest.main()
