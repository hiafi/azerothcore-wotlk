"""
item-tools' whole-table check (`replay_check.py`) without a database: a duplicate replayed key fails the check
(dbc-replay-fix review N6).

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import replay_check  # noqa: E402
from item_lib import replay  # noqa: E402


class DuplicateKeysTest(unittest.TestCase):
    def run_check(self, replayed: dict) -> tuple[int, str]:
        schema = replay.Schema(("entry", "v"), ("entry",), {}, frozenset())
        live = [{"entry": "1", "v": "2"}]
        out = io.StringIO()
        with mock.patch.object(replay_check, "CHECKED_TABLES", {"item_template": ("entry",)}), \
                mock.patch.object(replay_check, "run_sql", side_effect=[[{"name": "a.sql"}], live]), \
                mock.patch.object(replay_check.replay_diff, "load_allowed", return_value={}), \
                mock.patch.object(replay, "table_schema", return_value=schema), \
                mock.patch.object(replay, "load_table", return_value=replayed), \
                mock.patch.object(replay, "contributing_files", return_value=[]), \
                mock.patch.object(replay, "final_columns", return_value=["entry", "v"]), \
                mock.patch.object(replay.sqlcorpus, "activate"), \
                contextlib.redirect_stdout(out):
            rc = replay_check.main(["--mysql", "mysql", "--tables", "item_template"])
        return rc, out.getvalue()

    def test_clean_run_exits_0(self):
        self.assertEqual(self.run_check({(1,): {"entry": 1, "v": 2}})[0], 0)

    def test_a_duplicate_replayed_key_exits_1(self):
        # Two rows filed under different dict keys that hold the same key values: the replay is wrong somewhere.
        rc, out = self.run_check({(1,): {"entry": 1, "v": 2}, (9,): {"entry": 1, "v": 2}})
        self.assertEqual(rc, 1)
        self.assertIn("DUPLICATE KEYS: item_template", out)


if __name__ == "__main__":
    unittest.main()
