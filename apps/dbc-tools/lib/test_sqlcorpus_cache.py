"""The on-disk cache (`sqlcorpus.Corpus.checkpointed`) must never turn a stale or damaged snapshot into an answer.

Every test builds a tiny corpus of SQL files in a temp directory and counts how many times the replay really ran. The
invariant under test is the one in the module docstring: a hit, an extension and a rebuild all return what a full
replay returns, and anything the cache cannot vouch for (edited file, removed file, file inserted before the end,
changed code, damaged snapshot) falls back to the full replay.
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import sql_dump, sqlcorpus, state, trainer_state  # noqa: E402
from lib.dbcfmt import DbcTable  # noqa: E402


class _Replay:
    """A replay of `INSERT INTO t VALUES (n)` rows that counts its steps and prints a line per file."""

    def __init__(self):
        self.steps: list[str] = []
        self.inits = 0

    def init(self) -> list:
        self.inits += 1
        return []

    def step(self, state_: list, path: Path) -> list:
        self.steps.append(path.name)
        print(f"read {path.name}")
        state_.extend(sql_dump.read_table_rows(path, "t", ("n",)))
        return state_


class CheckpointTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.sql = self.root / "sql"
        self.sql.mkdir()
        self.cache = self.root / "cache"
        self.version = "v1"
        self.write("a.sql", "INSERT INTO `t` VALUES (1);")
        self.write("b.sql", "INSERT INTO `t` VALUES (2);")

    def write(self, name: str, text: str, keep_mtime_of: Path | None = None) -> Path:
        path = self.sql / name
        stat = keep_mtime_of.stat() if keep_mtime_of is not None else None
        path.write_text(text, encoding="utf-8")
        if stat is not None:
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        return path

    def files(self) -> list[Path]:
        return sorted(self.sql.glob("*.sql"))

    def run_once(self, replay: _Replay | None = None, *, version: str | None = None, rebuild: bool = False,
                 params: object = None) -> tuple[list, str, _Replay, sqlcorpus.Corpus]:
        replay = replay or _Replay()
        corpus = sqlcorpus.Corpus(self.cache, version or self.version, rebuild)
        buf = io.StringIO()
        with redirect_stdout(buf):
            result, printed = corpus.checkpointed("t", params, self.files(), replay.init, replay.step)
        corpus.close()
        return result, printed, replay, corpus

    def test_second_run_is_a_hit_and_replays_the_printed_text(self):
        first, printed_first, replay1, _ = self.run_once()
        self.assertEqual([r["n"] for r in first], [1, 2])
        self.assertEqual(replay1.steps, ["a.sql", "b.sql"])
        second, printed_second, replay2, corpus = self.run_once()
        self.assertEqual(second, first)
        self.assertEqual(printed_second, printed_first)
        self.assertEqual(printed_second, "read a.sql\nread b.sql\n")
        self.assertEqual(replay2.steps, [])
        self.assertEqual(replay2.inits, 0)
        self.assertEqual(corpus.stats["hit"], 1)

    def test_edit_with_same_size_and_mtime_is_a_miss(self):
        self.run_once()
        self.write("b.sql", "INSERT INTO `t` VALUES (7);", keep_mtime_of=self.sql / "b.sql")  # same length, same time
        result, _printed, replay, corpus = self.run_once()
        self.assertEqual([r["n"] for r in result], [1, 7])
        self.assertEqual(replay.steps, ["a.sql", "b.sql"])
        self.assertEqual(corpus.stats["miss"], 1)

    def test_appended_file_extends_the_snapshot(self):
        self.run_once()
        self.write("c.sql", "INSERT INTO `t` VALUES (3);")
        result, printed, replay, corpus = self.run_once()
        self.assertEqual([r["n"] for r in result], [1, 2, 3])
        self.assertEqual(replay.steps, ["c.sql"])  # only the new file was read
        self.assertEqual(printed, "read a.sql\nread b.sql\nread c.sql\n")
        self.assertEqual(corpus.stats["extend"], 1)
        _result, _printed, replay3, corpus3 = self.run_once()
        self.assertEqual(replay3.steps, [])
        self.assertEqual(corpus3.stats["hit"], 1)

    def test_file_inserted_before_the_end_rebuilds(self):
        self.run_once()
        self.write("a2.sql", "INSERT INTO `t` VALUES (9);")  # sorts between a.sql and b.sql
        result, _printed, replay, corpus = self.run_once()
        self.assertEqual([r["n"] for r in result], [1, 9, 2])
        self.assertEqual(replay.steps, ["a.sql", "a2.sql", "b.sql"])
        self.assertEqual(corpus.stats["miss"], 1)

    def test_removed_file_rebuilds(self):
        self.run_once()
        (self.sql / "b.sql").unlink()
        result, _printed, replay, _corpus = self.run_once()
        self.assertEqual([r["n"] for r in result], [1])
        self.assertEqual(replay.steps, ["a.sql"])

    def test_changed_code_version_rebuilds(self):
        self.run_once()
        _result, _printed, replay, corpus = self.run_once(version="v2")
        self.assertEqual(replay.steps, ["a.sql", "b.sql"])
        self.assertEqual(corpus.stats["miss"], 1)

    def test_other_params_are_a_separate_snapshot(self):
        self.run_once(params="x")
        _result, _printed, replay, _corpus = self.run_once(params="y")
        self.assertEqual(replay.steps, ["a.sql", "b.sql"])
        _result, _printed, replay, _corpus = self.run_once(params="x")
        self.assertEqual(replay.steps, [])

    def test_rebuild_flag_ignores_the_cache_but_refreshes_it(self):
        self.run_once()
        _result, _printed, replay, _corpus = self.run_once(rebuild=True)
        self.assertEqual(replay.steps, ["a.sql", "b.sql"])
        _result, _printed, replay, corpus = self.run_once()
        self.assertEqual(replay.steps, [])
        self.assertEqual(corpus.stats["hit"], 1)

    def test_damaged_snapshots_fall_back_to_the_full_replay(self):
        damages = {
            "truncated": lambda blob: blob[: len(blob) // 2],
            "empty": lambda blob: b"",
            "garbage": lambda blob: b"not a cache file at all",
            "flipped payload byte": lambda blob: blob[:-5] + bytes([blob[-5] ^ 0xFF]) + blob[-4:],
            "header only": lambda blob: blob[: blob.index(b"\n", len(sqlcorpus._MAGIC)) + 1],
        }
        for name, damage in damages.items():
            with self.subTest(damage=name):
                self.run_once(rebuild=True)
                snapshots = list(self.cache.glob("snap-*.bin"))
                self.assertEqual(len(snapshots), 1)
                snapshots[0].write_bytes(damage(snapshots[0].read_bytes()))
                result, printed, replay, corpus = self.run_once()
                self.assertEqual([r["n"] for r in result], [1, 2])
                self.assertEqual(printed, "read a.sql\nread b.sql\n")
                self.assertEqual(replay.steps, ["a.sql", "b.sql"])
                self.assertEqual(corpus.stats["corrupt"], 1)
                _result, _printed, replay, corpus = self.run_once()  # and the rewritten snapshot is good again
                self.assertEqual(replay.steps, [])

    def test_snapshot_of_a_different_key_is_not_trusted(self):
        self.run_once(params="x")
        self.run_once(params="y")
        x, y = sorted(self.cache.glob("snap-*.bin"))
        x.write_bytes(y.read_bytes())  # y's contents under x's name
        _result, _printed, replay, corpus = self.run_once(params="x")
        self.assertEqual(replay.steps, ["a.sql", "b.sql"])
        self.assertEqual(corpus.stats["corrupt"], 1)

    def test_a_failing_replay_surfaces_and_writes_nothing(self):
        def boom(state_, path):
            raise RuntimeError("replay failed")

        corpus = sqlcorpus.Corpus(self.cache, self.version)
        with redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            corpus.checkpointed("t", None, self.files(), list, boom)
        self.assertEqual(list(self.cache.glob("snap-*.bin")), [])

    def test_caller_changes_after_the_call_do_not_reach_the_snapshot(self):
        result, _printed, _replay, _corpus = self.run_once()
        result.append({"n": 99})  # what a caller does when it replays pending files on top
        again, _printed, replay, _corpus = self.run_once()
        self.assertEqual([r["n"] for r in again], [1, 2])
        self.assertEqual(replay.steps, [])

    def test_unwritable_cache_dir_still_answers(self):
        blocker = self.root / "blocker"
        blocker.write_text("a file where the cache directory should be")
        corpus = sqlcorpus.Corpus(blocker / "cache", self.version)
        replay = _Replay()
        with redirect_stdout(io.StringIO()):
            result, _printed = corpus.checkpointed("t", None, self.files(), replay.init, replay.step)
        self.assertEqual([r["n"] for r in result], [1, 2])


class CacheHardeningTest(CheckpointTest):
    def test_stderr_of_the_replay_is_replayed_on_a_hit(self):
        def noisy(state_, path):
            print(f"warn {path.name}", file=sys.stderr)
            return state_

        for expect_cached in (False, True):
            corpus = sqlcorpus.Corpus(self.cache, self.version)
            err = io.StringIO()
            from contextlib import redirect_stderr

            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                corpus.checkpointed("noisy", None, self.files(), list, noisy)
            self.assertEqual(err.getvalue(), "warn a.sql\nwarn b.sql\n")
            self.assertEqual(corpus.stats["hit"], int(expect_cached))

    def test_snapshot_is_labelled_with_the_hash_of_the_text_the_replay_read(self):
        # A file rewritten after the corpus first hashed it but before the replay read it must not be stored under the
        # old hash: the next run would then take a snapshot of the new text for the old file.
        corpus = sqlcorpus.Corpus(self.cache, self.version)
        files = self.files()
        stale = corpus.digest(files[1])
        self.write("b.sql", "INSERT INTO `t` VALUES (7);")
        replay = _Replay()
        with redirect_stdout(io.StringIO()):
            result, _printed = corpus.checkpointed("t", None, files, replay.init, replay.step)
        self.assertEqual([r["n"] for r in result], [1, 7])
        snapshot = next(self.cache.glob("snap-*.bin"))
        stored = dict(sqlcorpus._unpack(snapshot.read_bytes(), {})["files"])
        self.assertNotEqual(stored[str(files[1])], stale)
        _result, _printed, replay2, corpus2 = self.run_once()
        self.assertEqual(replay2.steps, [])  # the new text is what the snapshot holds, and it matches the file

    def test_old_code_versions_are_pruned_but_one_is_kept(self):
        base = self.root / "versions"
        for name in ("v1", "v2", "v3"):
            (base / name).mkdir(parents=True)
            (base / name / "snap-x.bin").write_bytes(b"x")
            os.utime(base / name, (int(name[1]) * 1000, int(name[1]) * 1000))
        try:
            sqlcorpus.activate(base, "v4")
            self.assertEqual(sorted(p.name for p in base.iterdir()), ["v3"])
            self.assertEqual(sqlcorpus.active().cache_dir, base / "v4")
        finally:
            sqlcorpus.deactivate()

    def test_a_head_like_string_inside_a_skipped_statement_does_not_hide_the_next_head(self):
        from lib import sql_dump

        # The UPDATE is parsed and skipped; the unbalanced `INSERT INTO `t` (` inside its string, matched by the
        # one-pass head scan, would run on through the real INSERT's column list and hide it from the index.
        sql = (
            "UPDATE `t` SET `v` = 'INSERT INTO `t` (' WHERE `a` = 1;\n"
            "INSERT INTO `t` (`a`, `v`) VALUES (2, 5);\n"
        )
        path = self.sql / "tricky.sql"
        path.write_text(sql, encoding="utf-8")

        def replay():
            rows: dict = {}
            sql_dump.apply_composite_key_statements(rows, ("a", "v"), ("a",), "t", sqlcorpus.read_text(path))
            return rows

        plain = replay()
        self.assertEqual(plain, {(2,): {"a": 2, "v": 5}})
        sqlcorpus.activate(None, "test")
        try:
            self.assertEqual(replay(), plain)
        finally:
            sqlcorpus.deactivate()


class FileIndexTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.path = self.root / "f.sql"
        self.path.write_text("INSERT INTO `t` VALUES (1);\nDELETE FROM `u` WHERE `a` = 1;\n", encoding="utf-8")
        self.cache = self.root / "cache"

    def corpus(self, version="v1") -> sqlcorpus.Corpus:
        return sqlcorpus.Corpus(self.cache, version)

    def test_heads_and_mentions_persist_by_content(self):
        first = self.corpus()
        text = first.read_text(self.path)
        heads = text.head_index.heads
        self.assertTrue(first.mentions(self.path, "t"))
        self.assertFalse(first.mentions(self.path, "zzz"))
        first.close()
        second = self.corpus()
        entry = second._load_index()[second.digest(self.path)]
        self.assertEqual(entry["heads"], heads)
        self.assertEqual(entry["m"], {("t", False): True, ("zzz", False): False})

    def test_an_edited_file_gets_a_fresh_entry(self):
        first = self.corpus()
        first.read_text(self.path).head_index
        first.close()
        self.path.write_text("INSERT INTO `t` VALUES (2);\nINSERT INTO `t` VALUES (3);\n", encoding="utf-8")
        second = self.corpus()
        text = second.read_text(self.path)
        self.assertEqual([h[2] for h in text.head_index.heads], ["I", "I"])

    def test_a_corrupt_index_is_ignored(self):
        first = self.corpus()
        first.read_text(self.path).head_index
        first.close()
        index_file = self.cache / "fileindex.bin"
        index_file.write_bytes(index_file.read_bytes()[:30])
        second = self.corpus()
        text = second.read_text(self.path)
        self.assertEqual(len(text.head_index.heads), 2)
        self.assertEqual(second.stats["corrupt"], 1)

    def test_an_index_from_other_code_is_ignored(self):
        first = self.corpus("v1")
        first.read_text(self.path).head_index
        first.close()
        second = self.corpus("v2")
        self.assertEqual(second._load_index(), {})
        self.assertEqual(second.stats["corrupt"], 1)


class LoaderIntegrationTest(unittest.TestCase):
    """`state.load_existing_rows` through a real cache, on a tiny table, against the uncached answer."""

    TABLE = DbcTable(name="Widget", dbc_filename="Widget.dbc", sql_table="widget_dbc", fmt="nsi",
                     columns=("ID", "Name", "Value"))

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        (root / "base").mkdir()
        (root / "promoted").mkdir()
        (root / "dbc").mkdir()
        (root / "base" / "widget_dbc.sql").write_text(
            "INSERT INTO `widget_dbc` VALUES (1, 'one', 10), (2, 'two', 20);\n", encoding="utf-8")
        (root / "seed.sql").write_text("-- nothing\n", encoding="utf-8")
        self.promoted = root / "promoted"
        self.cache = root / "cache"
        patches = {
            state: {"BASE_SQL_DIR": root / "base", "PROMOTED_SQL_DIR": self.promoted, "BASE_DBC_DIR": root / "dbc",
                    "LIVE_SECONDARY_ROWS_SQL": root / "seed.sql"},
        }
        saved = []
        for module, values in patches.items():
            for name, value in values.items():
                saved.append((module, name, getattr(module, name)))
                setattr(module, name, value)

        def restore():
            for module, name, value in saved:
                setattr(module, name, value)
            sqlcorpus.deactivate()

        self.addCleanup(restore)
        state._promoted_sql_cache = None

    def promote(self, name: str, sql: str) -> None:
        (self.promoted / name).write_text(sql, encoding="utf-8")
        state._promoted_sql_cache = None

    def cached_load(self, version="v1") -> dict:
        corpus = sqlcorpus.activate(self.cache, version)
        try:
            return state.load_existing_rows(self.TABLE)
        finally:
            self.last_stats = dict(corpus.stats)
            sqlcorpus.deactivate()

    def plain_load(self) -> dict:
        sqlcorpus.deactivate()
        return state.load_existing_rows(self.TABLE)

    def test_cached_answers_track_the_files(self):
        self.promote("2026_01_01_00.sql", "UPDATE `widget_dbc` SET `Value` = 11 WHERE `ID` = 1;")
        self.assertEqual(self.cached_load(), self.plain_load())
        self.assertEqual(self.last_stats["miss"], 1)
        self.assertEqual(self.cached_load(), self.plain_load())
        self.assertEqual(self.last_stats["hit"], 1)
        self.promote("2026_02_01_00.sql", "DELETE FROM `widget_dbc` WHERE `ID` = 2;")  # appended
        loaded = self.cached_load()
        self.assertEqual(loaded, self.plain_load())
        self.assertEqual(self.last_stats["extend"], 1)
        self.assertEqual(set(loaded), {1})
        self.promote("2026_01_01_00.sql", "UPDATE `widget_dbc` SET `Value` = 12 WHERE `ID` = 1;")  # edited in place
        loaded = self.cached_load()
        self.assertEqual(loaded, self.plain_load())
        self.assertEqual(loaded[1]["Value"], 12)
        self.assertEqual(self.last_stats["miss"], 1)

    def test_a_file_that_does_not_mention_the_table_leaves_the_snapshot_alone(self):
        self.promote("2026_01_01_00.sql", "UPDATE `widget_dbc` SET `Value` = 11 WHERE `ID` = 1;")
        self.cached_load()
        self.promote("2026_03_01_00.sql", "UPDATE `other_table` SET `a` = 1 WHERE `id` = 1;")
        self.assertEqual(self.cached_load(), self.plain_load())
        self.assertEqual(self.last_stats["hit"], 1)


if __name__ == "__main__":
    unittest.main()
