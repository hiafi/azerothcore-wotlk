"""
item-tools' emitted SQL (`item_lib/emit.py`): a guarded `item_template` UPDATE on a FLOAT column passes the repo's
SQL linter (`apps/codestyle/codestyle-sql.py`) and replays the way MySQL would run it.

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import emit, overlay  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


class FloatGuardTest(unittest.TestCase):
    def test_float_guard_is_a_between(self):
        self.assertEqual(emit._guard_term("dmg_min1", 144.375), "`dmg_min1` BETWEEN 144.365 AND 144.385")
        self.assertEqual(emit._guard_term("Quality", 3), "`Quality` = 3")

    def test_emitted_float_update_passes_codestyle_and_replays(self):
        original = {"entry": 1, "dmg_min1": 144.375, "dmg_max1": 268.125, "Quality": 3}
        changes = {"dmg_min1": 181.2888, "dmg_max1": 336.6792}
        with tempfile.TemporaryDirectory() as d:
            pending = Path(d) / "data" / "sql" / "updates" / "pending_db_world"
            with mock.patch.object(overlay, "PENDING_DIR", pending):
                path = emit.write_update(1, changes, original, "item-tools test: a float-column edit")
            text = path.read_text(encoding="utf-8")
            self.assertIn("`dmg_min1` BETWEEN 144.365 AND 144.385", text)
            self.assertNotIn("ABS(", text)
            # codestyle-sql.py ends with `git fetch` + `git diff` against origin; a no-op `git` first on PATH keeps
            # this test off the network (same trick as apps/dbc-tools/lib/test_item_template.py).
            fake_bin = Path(d) / "bin"
            fake_bin.mkdir()
            (fake_bin / "git").write_text("#!/bin/sh\nexit 0\n")
            (fake_bin / "git").chmod(0o755)
            done = subprocess.run(
                [sys.executable, str(REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py")],
                cwd=d, capture_output=True, text=True, env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
            )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

        rows = {1: dict(original), 2: {**original, "entry": 2, "dmg_min1": 150.0}}
        overlay.apply_text(text, rows)
        self.assertEqual((rows[1]["dmg_min1"], rows[1]["dmg_max1"]), (181.2888, 336.6792))
        stale = {1: {**original, "dmg_min1": 144.4}}  # outside the +/-0.01 guard: no change, as in MySQL
        overlay.apply_text(text, stale)
        self.assertEqual(stale[1]["dmg_min1"], 144.4)


if __name__ == "__main__":
    unittest.main()
