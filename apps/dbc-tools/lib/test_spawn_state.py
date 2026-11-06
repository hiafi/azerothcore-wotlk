"""
lib/spawn_state.py (dungeon difficulties E2, WP-T2): the replayed `creature` / `gameobject` spawns the spawnMask
emitter diffs against.

Covered: the double-quote rewrite (comments and single-quoted strings untouched), the `id1` -> `id` rename, the
guid-less DELETE / UPDATE applied in file order around the guid-keyed replay (session variables carried across the
split), the projection to the kept columns, and reading back the emitter's own `spawnMask | 2` UPDATE. The real
replay against the live DB is in the E2-T2 report (no spawn, entry, map or mask difference on the 19 vanilla maps).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_spawn_state.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dungeon_heroic, spawn_state  # noqa: E402


def _replay(table: str, *files: str) -> spawn_state.SpawnState:
    state = spawn_state.SpawnState()
    with tempfile.TemporaryDirectory() as d:
        step = spawn_state.make_step(table, Path(d) / "base.sql")
        for i, text in enumerate(files):
            path = Path(d) / f"2026_01_0{i}_00.sql"
            path.write_text(text, encoding="utf-8")
            step(state, path)
    return state


class NormaliseTest(unittest.TestCase):
    def test_double_quoted_literals_become_single_quoted(self):
        text = 'INSERT INTO `gameobject` (`guid`, `ScriptName`, `Comment`) VALUES (1, "", "it\'s a ""door""");'
        self.assertEqual(
            spawn_state.normalise_text(text, "gameobject"),
            "INSERT INTO `gameobject` (`guid`, `ScriptName`, `Comment`) VALUES (1, '', 'it''s a \"door\"');",
        )

    def test_comments_and_single_quoted_strings_are_left_alone(self):
        text = "-- Gilnid's \"lever\"\n/* a \"b\" */ INSERT INTO `t` VALUES ('say \"hi\"', \"x\");"
        self.assertEqual(
            spawn_state.normalise_text(text, "gameobject"),
            "-- Gilnid's \"lever\"\n/* a \"b\" */ INSERT INTO `t` VALUES ('say \"hi\"', 'x');",
        )

    def test_a_text_without_changes_is_returned_as_is(self):
        text = "UPDATE `creature` SET `spawnMask` = 3 WHERE `id` = 1 AND `guid` = 2;"
        self.assertIs(spawn_state.normalise_text(text, "creature"), text)

    def test_id1_is_renamed_for_creature_only(self):
        self.assertEqual(spawn_state.normalise_text("WHERE `id1` = 5", "creature"), "WHERE `id` = 5")
        self.assertEqual(spawn_state.normalise_text("WHERE `id1` = 5", "gameobject"), "WHERE `id1` = 5")


class ReplayTest(unittest.TestCase):
    INSERT = (
        "INSERT INTO `creature` (`guid`, `id1`, `map`, `spawnMask`, `position_x`) VALUES\n"
        "(1, 5, 603, 1, 1.5), (2, 5, 36, 1, 2.5), (3, 7, 36, 1, 0), (4, 9, 36, 1, 0);\n"
    )

    def test_rows_keep_only_the_kept_columns_under_the_renamed_id(self):
        rows = _replay("creature", self.INSERT).by_guid()
        self.assertEqual(rows[1], {"guid": 1, "id": 5, "map": 603, "spawnMask": 1})

    def test_guidless_statements_apply_in_file_order(self):
        later = (
            "DELETE FROM `creature` WHERE `id` = 5 AND `map` = 603;\n"
            "INSERT INTO `creature` (`guid`, `id`, `map`, `spawnMask`) VALUES (5, 5, 603, 1);\n"
            "UPDATE `creature` SET `spawnMask` = 3 WHERE `id` IN (7);\n"
            "UPDATE `creature` SET `spawntimesecs` = 30 WHERE `id` = 9;\n"
        )
        state = _replay("creature", self.INSERT, later)
        rows = state.by_guid()
        self.assertNotIn(1, rows)  # deleted by entry and map
        self.assertEqual(rows[5]["map"], 603)  # inserted after the delete, so it stays
        self.assertEqual(rows[2]["spawnMask"], 1)  # same entry, other map
        self.assertEqual(rows[3]["spawnMask"], 3)
        self.assertEqual(state.skipped, [])  # the spawntimesecs update writes nothing kept: ignored, not skipped

    def test_session_variables_survive_the_split(self):
        later = (
            "SET @CGUID := 100;\n"
            "DELETE FROM `creature` WHERE `id` = 9;\n"
            "INSERT INTO `creature` (`guid`, `id`, `map`, `spawnMask`) VALUES\n"
            "(@CGUID+0, 9, 36, 1), (@CGUID+1, 9, 36, 1);\n"
        )
        rows = _replay("creature", self.INSERT, later).by_guid()
        self.assertNotIn(4, rows)
        self.assertEqual(sorted(g for g, r in rows.items() if r["id"] == 9), [100, 101])

    def test_a_double_quoted_insert_is_read(self):
        text = (
            "DELETE FROM `gameobject` WHERE (`id` IN (16399)) AND (`guid` IN (26182));\n"
            "INSERT INTO `gameobject` (`guid`, `id`, `map`, `spawnMask`, `ScriptName`, `Comment`) VALUES\n"
            "(26182, 16399, 36, 1, \"\", NULL);\n"
        )
        rows = _replay("gameobject", text).by_guid()
        self.assertEqual(rows[26182], {"guid": 26182, "id": 16399, "map": 36, "spawnMask": 1})

    def test_an_unreadable_guidless_delete_is_counted_not_guessed(self):
        state = _replay("creature", self.INSERT, "DELETE FROM `creature` WHERE `id` > 4;\n")
        self.assertEqual(len(state.by_guid()), 4)
        self.assertEqual(len(state.skipped), 1)

    def test_the_emitters_own_update_reads_back_as_heroic(self):
        rows = list(_replay("creature", self.INSERT).by_guid().values())
        block = dungeon_heroic.render_spawn_mask_update("creature", "Deadmines (map 36) heroic", [
            r for r in rows if r["map"] == 36
        ])
        rows = _replay("creature", self.INSERT, block + "\n").by_guid()
        self.assertEqual({g: r["spawnMask"] for g, r in rows.items()}, {1: 1, 2: 3, 3: 3, 4: 3})
        again = _replay("creature", self.INSERT, block + "\n", block + "\n").by_guid()
        self.assertEqual(again[2]["spawnMask"], 3)  # `| 2` is idempotent

    def test_spawn_mask_defaults_to_one(self):
        self.assertEqual(spawn_state.spawn_mask({"guid": 1}), 1)

    def test_unknown_table_raises(self):
        with self.assertRaises(ValueError):
            spawn_state.load_spawn_state("pool_creature")


if __name__ == "__main__":
    unittest.main()
