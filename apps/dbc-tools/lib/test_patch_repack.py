"""lib/patch_repack.py: the deployed patch-Z is repacked with only Item.dbc replaced (item variants IV3).

Real `smpq` archives of a few small files; skipped without smpq. Everything is written under a temp dir and the
`patch_out` paths are redirected there, so nothing touches var/dbc-patch or a deployed patch-root.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import mpq_writer, patch_out, patch_repack  # noqa: E402

try:
    mpq_writer._find_smpq()
    HAVE_SMPQ = True
except RuntimeError:
    HAVE_SMPQ = False

FILES = {
    "DBFilesClient\\Spell.dbc": b"spell rows in flight" * 50,
    "DBFilesClient\\Talent.dbc": b"talent rows" * 20,
    "DBFilesClient\\Item.dbc": b"old item rows" * 30,
}
NEW_ITEM = b"new item rows" * 40


def _archive(path: Path, files: dict[str, bytes] = FILES) -> Path:
    mpq_writer.write_mpq(path, files)
    return path


@unittest.skipUnless(HAVE_SMPQ, "smpq not installed")
class RepackTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def members(self, archive: Path) -> dict[str, bytes]:
        dest = self.tmp / f"x{len(list(self.tmp.iterdir()))}"
        dest.mkdir()
        return patch_repack.extract_all(archive, dest)

    def test_replaces_only_item_dbc(self):
        base = _archive(self.tmp / "base.mpq")
        out = self.tmp / "out.mpq"
        changed = patch_repack.repack(base, {patch_repack.ITEM_DBC: NEW_ITEM}, out)
        self.assertEqual(changed, ["DBFilesClient/Item.dbc"])
        got = self.members(out)
        self.assertEqual({n.lower() for n in got}, {n.replace("\\", "/").lower() for n in FILES})
        self.assertEqual(got["DBFilesClient/Item.dbc"], NEW_ITEM)
        self.assertEqual(got["DBFilesClient/Spell.dbc"], FILES["DBFilesClient\\Spell.dbc"])
        self.assertEqual(got["DBFilesClient/Talent.dbc"], FILES["DBFilesClient\\Talent.dbc"])
        self.assertEqual(self.members(base)["DBFilesClient/Item.dbc"], FILES["DBFilesClient\\Item.dbc"])

    def test_identical_bytes_write_nothing(self):
        base = _archive(self.tmp / "base.mpq")
        out = self.tmp / "out.mpq"
        changed = patch_repack.repack(base, {patch_repack.ITEM_DBC: FILES["DBFilesClient\\Item.dbc"]}, out)
        self.assertEqual(changed, [])
        self.assertFalse(out.exists())

    def test_absent_member_is_added(self):
        base = _archive(self.tmp / "base.mpq", {"DBFilesClient\\Spell.dbc": b"s" * 10})
        out = self.tmp / "out.mpq"
        changed = patch_repack.repack(base, {patch_repack.ITEM_DBC: NEW_ITEM}, out)
        self.assertEqual(changed, ["DBFilesClient/Item.dbc"])
        got = self.members(out)
        self.assertEqual(got["DBFilesClient/Item.dbc"], NEW_ITEM)
        self.assertEqual(got["DBFilesClient/Spell.dbc"], b"s" * 10)

    def test_describe_lists_every_member_and_the_date(self):
        base = _archive(self.tmp / "base.mpq")
        text = "\n".join(patch_repack.describe(base))
        self.assertIn(str(base), text)
        self.assertIn("modified 20", text)
        for name in ("Spell.dbc", "Talent.dbc", "Item.dbc"):
            self.assertIn(f"DBFilesClient/{name}", text)

    def test_install_touches_only_item_dbc_and_the_archive(self):
        root = self.tmp / "patch-root"
        (root / "Data").mkdir(parents=True)
        base = _archive(root / "Data" / "patch-Z.mpq")
        new = self.tmp / "new.mpq"
        patch_repack.repack(base, {patch_repack.ITEM_DBC: NEW_ITEM}, new)
        local = self.tmp / "var"
        loose = local / "DBFilesClient"
        loose.mkdir(parents=True)
        (loose / "Spell.dbc").write_bytes(b"left alone")
        with mock.patch.object(patch_out, "DEPLOY_ROOT", root), \
                mock.patch.object(patch_out, "LOOSE_DIR", loose), \
                mock.patch.object(patch_out, "MPQ_PATH", local / "patch-Z.mpq"), \
                mock.patch.object(patch_out, "ENV_DBC_DIR", self.tmp / "no-env"):
            report = patch_repack.install(new, {"Item.dbc": NEW_ITEM})
        self.assertEqual(report["deploy_mpq"], str(root / "Data" / "patch-Z.mpq"))
        self.assertEqual((loose / "Item.dbc").read_bytes(), NEW_ITEM)
        self.assertEqual((loose / "Spell.dbc").read_bytes(), b"left alone")
        self.assertEqual(self.members(root / "Data" / "patch-Z.mpq")["DBFilesClient/Item.dbc"], NEW_ITEM)
        self.assertEqual(self.members(local / "patch-Z.mpq")["DBFilesClient/Spell.dbc"],
                         FILES["DBFilesClient\\Spell.dbc"])
        self.assertEqual([p.name for p in (root / "Data").iterdir()], ["patch-Z.mpq"])


class DeployedBaseTest(unittest.TestCase):
    def test_no_local_config_is_refused_by_name(self):
        with mock.patch.object(patch_out, "DEPLOY_ROOT", None):
            with self.assertRaises(patch_repack.PatchBaseError) as ctx:
                patch_repack.deployed_base()
        self.assertIn("local_config.py", str(ctx.exception))

    @unittest.skipUnless(HAVE_SMPQ, "smpq not installed")
    def test_missing_archive_is_refused_with_its_path(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(patch_out, "DEPLOY_ROOT", Path(tmp)):
            with self.assertRaises(patch_repack.PatchBaseError) as ctx:
                patch_repack.deployed_base()
            self.assertIn(str(Path(tmp) / "Data" / "patch-Z.mpq"), str(ctx.exception))

    @unittest.skipUnless(HAVE_SMPQ, "smpq not installed")
    def test_deployed_archive_is_the_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Data").mkdir()
            archive = _archive(Path(tmp) / "Data" / "patch-Z.mpq")
            with mock.patch.object(patch_out, "DEPLOY_ROOT", Path(tmp)):
                self.assertEqual(patch_repack.deployed_base(), archive)


if __name__ == "__main__":
    unittest.main()
