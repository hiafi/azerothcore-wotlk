"""check_pending.py (R-S1 B1): unapplied pending revs judged against a stubbed live DB and a temporary SQL history."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_pending  # noqa: E402
from lib import drop_guard  # noqa: E402

WRITER = "INSERT INTO `spell_dbc` (`ID`, `Attributes`) VALUES\n(205282, 1),\n(205283, 1);\n"
STALE = "DELETE FROM `spell_dbc` WHERE `ID` BETWEEN 205200 AND 205399;\n" \
        "INSERT INTO `spell_dbc` (`ID`, `Attributes`) VALUES\n(205283, 0);\n"


class CheckPendingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        patcher = mock.patch.object(drop_guard, "BASE_SQL_DIR", self.tmp / "base")
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_check(self, files: dict[str, str], applied: set[str], argv=()):
        for name, text in files.items():
            (self.tmp / name).write_text(text)
        paths = sorted(self.tmp / n for n in files)
        lines: list[str] = []
        live_rows = {205282: {"ID": "205282", "Attributes": "1"}, 205283: {"ID": "205283", "Attributes": "1"}}
        with mock.patch.object(check_pending.trainer_state, "update_files", lambda pending_dir=None: paths), \
                mock.patch.object(check_pending.trainer_state, "second_pass_files", lambda pending_dir=None: paths):
            code = check_pending.run(
                list(argv), command=["mysql"], applied_reader=lambda: applied,
                live_reader=lambda c, tables, ids_cfg: {t: ({205282, 205283} if t == "spell_dbc" else set())
                                                        for t in tables},
                rows_reader=lambda c, table, ids: {i: live_rows[i] for i in ids if i in live_rows},
                out=lines.append,
            )
        return code, "\n".join(lines)

    def test_stale_rev_named_before_the_writer_is_refused(self):
        code, text = self.run_check({"rev_100.sql": STALE, "rev_200.sql": WRITER}, applied={"rev_200.sql"})
        self.assertEqual(code, 1)
        self.assertIn("1 live row(s) deleted, written by rev_200.sql", text)  # 205282
        self.assertIn("1 live row(s) rewritten, written by rev_200.sql", text)  # 205283 back to 0

    def test_a_later_rev_is_this_checkouts_own_change(self):
        code, text = self.run_check({"rev_100.sql": WRITER, "rev_300.sql": STALE}, applied={"rev_100.sql"})
        self.assertEqual(code, 0, text)
        self.assertIn("deleting 1 live row(s)", text)

    def test_unknown_live_rows_and_override(self):
        code, text = self.run_check({"rev_300.sql": STALE}, applied=set())
        self.assertEqual(code, 1)
        self.assertIn("no SQL file of this checkout wrote", text)
        code, _text = self.run_check({"rev_300.sql": STALE}, applied=set(), argv=["--allow-drop"])
        self.assertEqual(code, 0)

    def test_nothing_unapplied(self):
        code, text = self.run_check({"rev_100.sql": WRITER}, applied={"rev_100.sql"})
        self.assertEqual(code, 0)
        self.assertIn("nothing to check", text)


if __name__ == "__main__":
    unittest.main()
