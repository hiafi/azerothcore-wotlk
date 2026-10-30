"""`generate.py --class` is a scoped *check*: it must refuse every other combination before loading anything."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class ClassFlagRefusalTest(unittest.TestCase):
    """`generate.py --class` is a scoped *check*: any write run with it must stop before doing anything."""

    GENERATE = Path(__file__).resolve().parents[1] / "generate.py"

    def run_generate(self, *args: str):
        import subprocess

        return subprocess.run([sys.executable, str(self.GENERATE), *args], capture_output=True, text=True, timeout=60)

    def test_class_without_check_is_refused(self):
        result = self.run_generate("--class", "warrior")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--class", result.stderr)
        self.assertIn("--check", result.stderr)
        self.assertEqual(result.stdout, "")  # nothing was loaded, let alone written

    def test_class_with_other_write_flags_is_refused(self):
        for flags in (["--class", "warrior", "--no-prune"], ["--class=warrior"], ["--no-cache", "--class", "warrior"]):
            with self.subTest(flags=flags):
                result = self.run_generate(*flags)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_class_needs_a_name(self):
        result = self.run_generate("--check", "--class")
        self.assertEqual(result.returncode, 2)
        self.assertIn("needs a class name", result.stderr)

    def test_unknown_class_is_refused_with_the_known_names(self):
        result = self.run_generate("--check", "--class", "nosuchclass")
        self.assertEqual(result.returncode, 2)
        self.assertIn("nosuchclass", result.stderr)
        self.assertIn("warrior", result.stderr)

    def test_two_classes_are_refused(self):
        result = self.run_generate("--check", "--class", "warrior", "--class", "mage")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
