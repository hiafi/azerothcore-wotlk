"""`generate.py --class` is a scoped *check*: it must refuse every other combination before loading anything.

The refusal is tested on `parse_args` and on `main()` with `sqlcorpus.activate` booby-trapped, never by running a real
generate.py: if a refusal ever broke, a real run would write the pending SQL and deploy the patch.
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402


class ParseArgsTest(unittest.TestCase):
    def test_class_with_check_is_accepted(self):
        for args in (["--check", "--class", "warrior"], ["--class", "warrior", "--check"], ["--check", "--class=mage"]):
            with self.subTest(args=args):
                flags, name, error = generate.parse_args(args)
                self.assertIsNone(error)
                self.assertIn(name, ("warrior", "mage"))
                self.assertIn("--check", flags)

    def test_class_without_check_is_refused(self):
        for args in (
            ["--class", "warrior"], ["--class=warrior"], ["--no-cache", "--class", "warrior"],
            ["--class", "warrior", "--no-prune"], ["--class", "warrior", "--rebuild-cache"],
        ):
            with self.subTest(args=args):
                _flags, name, error = generate.parse_args(args)
                self.assertIsNone(name)
                self.assertIn("--check", error)

    def test_class_needs_exactly_one_known_name(self):
        for args, fragment in (
            (["--check", "--class"], "needs a class name"),
            (["--check", "--class", "--no-cache"], "needs a class name"),
            (["--check", "--class="], "exactly one"),
            (["--check", "--class", "warrior", "--class", "mage"], "exactly one"),
            (["--check", "--class", "nosuchclass"], "nosuchclass"),
        ):
            with self.subTest(args=args):
                _flags, name, error = generate.parse_args(args)
                self.assertIsNone(name)
                self.assertIn(fragment, error)

    def test_unknown_class_lists_the_known_ones(self):
        _flags, _name, error = generate.parse_args(["--check", "--class", "nosuchclass"])
        self.assertIn("warrior", error)

    def test_unknown_flag_is_refused(self):
        _flags, _name, error = generate.parse_args(["--check", "--bogus"])
        self.assertIn("--bogus", error)

    def test_plain_runs_have_no_class(self):
        self.assertEqual(generate.parse_args([]), (set(), None, None))
        self.assertEqual(generate.parse_args(["--check"]), ({"--check"}, None, None))


class MainRefusalTest(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["generate.py", *argv]), \
                mock.patch.object(generate.sqlcorpus, "activate", side_effect=AssertionError("loaded something")), \
                redirect_stdout(out), redirect_stderr(err):
            code = generate.main()
        return code, out.getvalue(), err.getvalue()

    def test_refusals_exit_2_before_anything_is_activated(self):
        for argv in (
            ["--class", "warrior"], ["--class=warrior"], ["--class", "warrior", "--no-prune"],
            ["--check", "--class"], ["--check", "--class", "nosuchclass"],
            ["--check", "--class", "warrior", "--class", "mage"],
        ):
            with self.subTest(argv=argv):
                code, out, err = self.run_main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn("generate.py:", err)


if __name__ == "__main__":
    unittest.main()
