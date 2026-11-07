"""build_patch_x.py (R1 S4 / N11): only UI files are packed, and nothing is deployed without --deploy.

Everything is written under a temp dir (a scratch UI tree, archive and patch root).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_patch_x  # noqa: E402
from lib import mpq_writer  # noqa: E402

try:
    mpq_writer._find_smpq()
    HAVE_SMPQ = True
except RuntimeError:
    HAVE_SMPQ = False


class PackableTest(unittest.TestCase):
    def test_only_ui_files(self):
        for name, ok in (
            ("Interface/FrameXML/ItemTierLabel.lua", True),
            ("Interface/FrameXML/FrameXML.toc", True),
            ("Interface/AddOns/X/x.xml", True),
            ("Interface/Icons/a.blp", True),
            ("Interface/FrameXML/.ItemTierLabel.lua.swp", False),
            ("Interface/FrameXML/ItemTierLabel.lua.orig", False),
            ("Interface/FrameXML/ItemTierLabel.lua~", False),
            ("Interface/.git/config", False),
            ("Interface/FrameXML/notes.md", False),
        ):
            with self.subTest(name=name):
                self.assertEqual(build_patch_x.packable(Path(name)), ok)


@unittest.skipUnless(HAVE_SMPQ, "smpq not installed")
class DeployFlagTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        framexml = self.tmp / "src" / "Interface" / "FrameXML"
        framexml.mkdir(parents=True)
        (framexml / "UnitPopup.lua").write_text("-- popup\n")
        (framexml / "UnitPopup.lua.orig").write_text("-- backup\n")
        self.root = self.tmp / "patch-root"
        self.out = self.tmp / "patch-X.mpq"

    def main(self, *extra):
        argv = ["build_patch_x.py", "--source", str(self.tmp / "src"), "--out", str(self.out),
                "--deploy-root", str(self.root), *extra]
        with mock.patch.object(sys, "argv", argv):
            return build_patch_x.main()

    def test_build_only_by_default(self):
        self.assertEqual(self.main(), 0)
        self.assertTrue(self.out.is_file())
        self.assertFalse((self.root / "Data" / "patch-X.mpq").exists())
        self.assertEqual(sorted(build_patch_x.collect(self.tmp / "src")), ["Interface\\FrameXML\\UnitPopup.lua"])

    def test_deploy_flag_copies(self):
        self.assertEqual(self.main("--deploy"), 0)
        self.assertEqual((self.root / "Data" / "patch-X.mpq").read_bytes(), self.out.read_bytes())

    def test_deploy_without_a_root_is_refused(self):
        argv = ["build_patch_x.py", "--source", str(self.tmp / "src"), "--out", str(self.out), "--deploy-root", "",
                "--deploy"]
        with mock.patch.object(sys, "argv", argv):
            self.assertEqual(build_patch_x.main(), 2)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
