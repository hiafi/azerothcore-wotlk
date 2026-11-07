"""`generate.py --scope`, `--deployed-patch` and `--allow-drop`: argument handling and the up-front refusal of a scoped
write run with nothing to repack. Like test_generate_only_items.py, the loaders are booby-trapped, so no real run
happens."""

from __future__ import annotations

import io
import sys
import tempfile
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
    def test_scope_in_both_spellings(self):
        for args in (["--scope", "deadmines"], ["--scope=deadmines"], ["--scope", "deadmines,warrior"]):
            with self.subTest(args=args):
                flags, name, error = generate.parse_args(args)
                self.assertIsNone(error)
                self.assertIsNone(name)
                self.assertEqual(generate._flag_value(flags, "--scope"), args[-1].removeprefix("--scope="))

    def test_scope_items_is_only_items(self):
        flags, _name, error = generate.parse_args(["--scope", "items"])
        self.assertIsNone(error)
        self.assertIn("--only=items", flags)
        self.assertIsNone(generate._flag_value(flags, "--scope"))
        flags, _name, error = generate.parse_args(["--check", "--scope", "items"])
        self.assertIsNone(error)
        self.assertIn("--only=items", flags)

    def test_refusals(self):
        for args, needle in (
            (["--scope"], "needs a value"),
            (["--scope", "nowhere"], "unknown scope"),
            (["--scope", "deadmines,deadmines"], "distinct"),
            (["--scope", "items,deadmines"], "cannot be combined"),
            (["--check", "--scope", "deadmines"], "write runs"),
            (["--scope", "deadmines", "--only", "items"], "cannot be combined"),
            (["--check", "--class", "warrior", "--scope", "warrior"], "cannot be combined"),
            (["--scope", "a", "--scope", "b"], "one value"),
            (["--deployed-patch"], "needs a value"),
        ):
            with self.subTest(args=args):
                _flags, _name, error = generate.parse_args(args)
                self.assertIsNotNone(error)
                self.assertIn(needle, error)

    def test_other_flags(self):
        flags, _name, error = generate.parse_args(["--allow-drop", "--deployed-patch", "/x/patch-Z.mpq"])
        self.assertIsNone(error)
        self.assertIn("--allow-drop", flags)
        self.assertEqual(generate._flag_value(flags, "--deployed-patch"), "/x/patch-Z.mpq")


class RefusalTest(unittest.TestCase):
    def run_scope(self, argv: list[str], deployed_patch=None) -> tuple[int | None, str]:
        self.addCleanup(generate.dsl_registry.stop_provenance)  # main() stops it; the trapped _run never returns
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["generate.py", *argv]), \
                mock.patch.object(generate.source, "load_spells_csv", side_effect=Loaded), redirect_stdout(out):
            try:
                code = generate._run(mock.Mock(), scope_names=["deadmines"], deployed_patch=deployed_patch)
            except Loaded:
                code = None
        return code, out.getvalue()

    def test_no_deployed_archive_stops_before_loading(self):
        with mock.patch.object(patch_out, "DEPLOY_ROOT", None):
            code, out = self.run_scope(["--scope", "deadmines"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR: --scope:", out)

    def test_deployed_patch_is_the_base(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(patch_out, "DEPLOY_ROOT", None):
            base = Path(tmp) / "patch-Z.mpq"
            base.write_bytes(b"MPQ")
            with mock.patch.object(generate.patch_repack.mpq_writer, "_find_smpq", return_value="smpq"):
                code, out = self.run_scope(["--scope", "deadmines"], deployed_patch=base)
        self.assertIsNone(code)  # reached the (trapped) loader
        self.assertIn(f"note: scope: deadmines (patch base {base})", out)


if __name__ == "__main__":
    unittest.main()
