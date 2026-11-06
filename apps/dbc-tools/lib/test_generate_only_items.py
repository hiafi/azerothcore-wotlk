"""`generate.py --only items` argument handling and its up-front refusal (item variants IV3).

Like test_generate_class_flag.py, no real generate.py run happens here: the loaders are booby-trapped, so a refusal
that stopped working fails the test instead of writing a pending SQL file or a patch.
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402
from lib import patch_out  # noqa: E402


class Loaded(Exception):
    """Raised by the booby-trapped loader: the run got past the refusal."""


class ParseArgsTest(unittest.TestCase):
    def test_only_items_is_accepted_in_both_spellings(self):
        for args in (
            ["--only", "items"], ["--only=items"], ["--only", "items", "--check"], ["--check", "--only=items"],
        ):
            with self.subTest(args=args):
                flags, name, error = generate.parse_args(args)
                self.assertIsNone(error)
                self.assertIsNone(name)
                self.assertIn("--only=items", flags)

    def test_only_needs_exactly_one_known_scope(self):
        for args in (["--only"], ["--only", "--check"], ["--only", "spells"], ["--only="],
                     ["--only", "items", "--only", "items"]):
            with self.subTest(args=args):
                _flags, _name, error = generate.parse_args(args)
                self.assertIn("--only", error)

    def test_only_and_class_cannot_be_combined(self):
        _flags, name, error = generate.parse_args(["--check", "--class", "warrior", "--only", "items"])
        self.assertIsNone(name)
        self.assertIn("cannot be combined", error)

    def test_plain_runs_have_no_only_flag(self):
        flags, _name, _error = generate.parse_args(["--check"])
        self.assertNotIn("--only=items", flags)


class RefusalTest(unittest.TestCase):
    def run_only_items(self, argv: list[str]) -> tuple[int | None, str]:
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["generate.py", *argv]), \
                mock.patch.object(generate.source, "load_ids", side_effect=Loaded), redirect_stdout(out):
            try:
                code = generate._run(mock.Mock(), only_items=True)
            except Loaded:
                code = None
        return code, out.getvalue()

    def test_write_run_without_local_config_stops_before_loading(self):
        with mock.patch.object(patch_out, "DEPLOY_ROOT", None):
            code, out = self.run_only_items(["--only", "items"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR: --only items:", out)
        self.assertIn("local_config.py", out)

    def test_write_run_without_deployed_archive_names_the_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(patch_out, "DEPLOY_ROOT", Path(tmp)):
            code, out = self.run_only_items(["--only", "items"])
        self.assertEqual(code, 1)
        self.assertIn(str(Path(tmp) / "Data" / "patch-Z.mpq"), out)

    def test_check_run_only_warns_and_carries_on(self):
        with mock.patch.object(patch_out, "DEPLOY_ROOT", None):
            code, out = self.run_only_items(["--check", "--only", "items"])
        self.assertIsNone(code)  # reached the (trapped) loader
        self.assertIn("WARNING: --only items:", out)
        self.assertIn("a write run would refuse", out)


class ItemDropGuardTest(unittest.TestCase):
    """R1 B1 / S5: a run whose Item.dbc lacks custom ids the deployed patch-Z holds stops before writing, unless
    --allow-item-drop; --check only warns."""

    IDS = {"item": {"start": 70000, "end": 79999}}

    def guard(self, argv, ids_in_build, dropped):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["generate.py", *argv]), \
                mock.patch.object(generate.patch_repack, "dropped_item_ids", return_value=dropped) as probe, \
                redirect_stdout(out):
            with mock.patch.object(Path, "is_file", return_value=True):
                rc = generate._item_dbc_drop_guard([{"id": i} for i in ids_in_build], self.IDS, Path("/x/patch-Z.mpq"))
        probe.assert_called_once()
        return rc, out.getvalue()

    def test_write_run_stops(self):
        rc, text = self.guard([], [70100], [71000, 71001])
        self.assertEqual(rc, 1)
        self.assertIn("ERROR: items:", text)
        self.assertIn("71000, 71001", text)
        self.assertIn("--allow-item-drop", text)

    def test_override_and_check_only_warn(self):
        for argv in (["--allow-item-drop"], ["--check"], ["--only", "items", "--check"]):
            with self.subTest(argv=argv):
                rc, text = self.guard(argv, [70100], [71000])
                self.assertEqual(rc, 0)
                self.assertIn("WARNING: items:", text)

    def test_nothing_dropped_is_silent(self):
        rc, text = self.guard([], [70100, 71000], [])
        self.assertEqual((rc, text), (0, ""))

    def test_no_deployed_archive_is_skipped(self):
        with mock.patch.object(patch_out, "DEPLOY_MPQ", None), \
                mock.patch.object(generate.patch_repack, "dropped_item_ids") as probe:
            self.assertEqual(generate._item_dbc_drop_guard([], self.IDS, None), 0)
        probe.assert_not_called()

    def test_flag_is_known(self):
        self.assertIsNone(generate.parse_args(["--allow-item-drop"])[2])


if __name__ == "__main__":
    unittest.main()
