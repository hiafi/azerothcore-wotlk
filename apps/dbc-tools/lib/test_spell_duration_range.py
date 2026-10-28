"""
SpellDuration rows with a minimum and a maximum (Rogue T1 step 2, rogue-rework.PLAN.md s1D.12).

`Spell(duration_ms=4000, max_duration_ms=24000)` is a row with `Duration 4000, MaxDuration 24000`: the core scales
the aura between the two by the caster's combo points (`WorldObject::CalcSpellDuration`, Object.cpp:3377-3394:
`min + (max - min) * comboPoints / 5`, only for a caster with combo points, `min != -1` and `min != max`).

Checks: the model's validation (every raise), find-or-mint through `ReuseContext.duration_index` (one minted row,
reused by a second spell with the same pair, a stock row with the pair reused, never minted), the min == max path
that still hits the old row, and the minted row rendered to SQL, read back through the real readers
(`sql_dump.apply_statements`, `state`-style overlay) and into a DBC, then re-run: nothing is minted and the
reserved block is unchanged (the converge test the DK T1 review asked for).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_spell_duration_range.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, lint, resolve, sql_dump, sql_out, state  # noqa: E402
from lib.dsl import model  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TABLE = dbcfmt.SPELLDURATION
BLOCK = {"start": 30100, "end": 30199}
SECONDARY = ("spellcasttimes", "spellduration", "spellrange", "spellradius")

# Rows shaped like SpellDuration.dbc's: 185 is a real stock row with a minimum and a maximum (6 s to 21 s).
PERMANENT = {"ID": 21, "Duration": -1, "DurationPerLevel": 0, "MaxDuration": -1}
EIGHT_SECONDS = {"ID": 8, "Duration": 8000, "DurationPerLevel": 0, "MaxDuration": 8000}
STOCK_RANGE = {"ID": 185, "Duration": 6000, "DurationPerLevel": 0, "MaxDuration": 21000}
# 35 is a real stock row, a flat 4 s: with it in the fixture a spell whose max is dropped on the way to the row builder
# reuses 35 instead of minting, so the DurationIndex assertions fail as well as the MaxDuration ones.
FOUR_SECONDS = {"ID": 35, "Duration": 4000, "DurationPerLevel": 0, "MaxDuration": 4000}
STOCK_DURATIONS = [PERMANENT, EIGHT_SECONDS, FOUR_SECONDS, STOCK_RANGE]


def _ids_cfg() -> dict:
    other = {"start": 30000, "end": 30099}
    return {name: (dict(BLOCK) if name == "spellduration" else dict(other)) for name in SECONDARY}


def _reuse(duration_rows: list[dict] | None = None) -> ReuseContext:
    rows = {name: [] for name in SECONDARY}
    rows["spellduration"] = [dict(r) for r in (STOCK_DURATIONS if duration_rows is None else duration_rows)]
    return ReuseContext(rows, _ids_cfg())


def _entry(spell_id: int = 203800, **kwargs) -> dict:
    return model.Spell(id=spell_id, name="Test Spell", **kwargs).to_entry()


class MaxDurationModelTest(unittest.TestCase):
    def test_default_is_unset_and_the_entry_is_unchanged(self):
        # an unset max leaves the entry dict exactly what it was: no new key for any existing spell
        self.assertNotIn("max_duration_ms", _entry(duration_ms=8000))
        self.assertNotIn("max_duration_ms", _entry())

    def test_a_declared_max_is_carried_into_the_entry(self):
        entry = _entry(duration_ms=4000, max_duration_ms=24000)
        self.assertEqual((entry["duration_ms"], entry["max_duration_ms"]), (4000, 24000))

    def test_a_max_without_a_duration_raises(self):
        for duration in (None, 0):
            with self.subTest(duration=duration):
                with self.assertRaisesRegex(ValueError, "positive duration_ms"):
                    _entry(duration_ms=duration, max_duration_ms=24000)

    def test_a_max_on_a_permanent_duration_raises(self):
        with self.assertRaisesRegex(ValueError, "positive duration_ms"):
            _entry(duration_ms=-1, max_duration_ms=24000)

    def test_a_max_equal_to_the_minimum_raises(self):
        # equal is just duration_ms: the core skips the combo-point scaling when min == max, so it is a no-op
        with self.assertRaisesRegex(ValueError, "just duration_ms"):
            _entry(duration_ms=8000, max_duration_ms=8000)

    def test_a_max_with_a_raw_duration_index_override_raises(self):
        # raw_overrides are applied last: the raw index would win and the ranged row would be an orphan
        with self.assertRaisesRegex(ValueError, "DurationIndex.*contradict"):
            _entry(duration_ms=4000, max_duration_ms=24000, raw_overrides={"DurationIndex": 35})
        # a raw override of another column, or a raw index without a max, is fine
        _entry(duration_ms=4000, max_duration_ms=24000, raw_overrides={"Attributes": 1})
        _entry(duration_ms=4000, raw_overrides={"DurationIndex": 35})

    def test_a_max_below_the_minimum_raises(self):
        with self.assertRaisesRegex(ValueError, "greater than duration_ms"):
            _entry(duration_ms=8000, max_duration_ms=4000)

    def test_a_minus_one_max_raises(self):
        with self.assertRaisesRegex(ValueError, "-1"):
            _entry(duration_ms=4000, max_duration_ms=-1)

    def test_the_error_names_the_spell(self):
        with self.assertRaisesRegex(ValueError, r"spell 203800 \(Test Spell\)"):
            _entry(duration_ms=8000, max_duration_ms=8000)


class MaxDurationReuseTest(unittest.TestCase):
    def test_a_declared_pair_mints_one_row_with_both_values(self):
        reuse = _reuse()
        index = reuse.duration_index(4000, 24000)
        self.assertEqual(index, 30100)
        self.assertEqual(
            reuse.minted["spellduration"],
            [{"ID": 30100, "Duration": 4000, "DurationPerLevel": 0, "MaxDuration": 24000}],
        )

    def test_a_second_spell_with_the_same_pair_reuses_the_row(self):
        reuse = _reuse()
        first = reuse.duration_index(4000, 24000)
        second = reuse.duration_index(4000, 24000)
        self.assertEqual(first, second)
        self.assertEqual(len(reuse.minted["spellduration"]), 1)

    def test_a_different_pair_mints_a_second_row(self):
        reuse = _reuse()
        a, b = reuse.duration_index(4000, 24000), reuse.duration_index(4000, 20000)
        self.assertNotEqual(a, b)
        self.assertEqual(len(reuse.minted["spellduration"]), 2)

    def test_an_existing_stock_row_with_the_pair_is_reused_not_minted(self):
        reuse = _reuse()
        self.assertEqual(reuse.duration_index(6000, 21000), 185)
        self.assertNotIn("spellduration", reuse.minted)

    def test_the_real_stock_row_185_is_the_pair_the_fixture_claims(self):
        if not (state.BASE_DBC_DIR / TABLE.dbc_filename).is_file():
            self.skipTest("no stock SpellDuration.dbc")
        stock = state.load_stock_rows(TABLE)
        self.assertEqual({k: v for k, v in stock[185].items() if k != "ID"}, {
            "Duration": 6000, "DurationPerLevel": 0, "MaxDuration": 21000,
        })
        reuse = ReuseContext({**{name: [] for name in SECONDARY}, "spellduration": list(stock.values())}, _ids_cfg())
        self.assertEqual(reuse.duration_index(6000, 21000), 185)
        self.assertNotIn("spellduration", reuse.minted)

    def test_min_equal_to_max_still_hits_the_old_row(self):
        reuse = _reuse()
        self.assertEqual(reuse.duration_index(8000), 8)
        self.assertEqual(reuse.duration_index(8000, None), 8)
        self.assertNotIn("spellduration", reuse.minted)

    def test_the_old_one_argument_call_still_mints_a_flat_row(self):
        reuse = _reuse()
        index = reuse.duration_index(12000)
        self.assertEqual(
            reuse.minted["spellduration"],
            [{"ID": index, "Duration": 12000, "DurationPerLevel": 0, "MaxDuration": 12000}],
        )

    def test_a_ranged_row_is_never_taken_for_a_flat_duration(self):
        # 6000 is the minimum of stock row 185 (6000 / 21000): a flat 6000 must not land on it
        reuse = _reuse()
        index = reuse.duration_index(6000)
        self.assertNotEqual(index, 185)
        self.assertEqual(reuse.minted["spellduration"][0]["MaxDuration"], 6000)

    def test_the_permanent_path_is_unchanged(self):
        reuse = _reuse()
        for falsy in (None, 0):
            self.assertEqual(reuse.duration_index(falsy), 21)
        self.assertEqual(reuse.duration_index(None, None), 21)
        self.assertNotIn("spellduration", reuse.minted)

    def test_a_permanent_duration_ignores_a_stray_max(self):
        # the model refuses this combination; the reuse layer keeps its old falsy-means-permanent behaviour
        self.assertEqual(_reuse().duration_index(None, 24000), 21)


class MaxDurationBuildTest(unittest.TestCase):
    """`build_spell_row` is the only path generate.py uses, so these assert the row the built index points at."""

    @staticmethod
    def _row_for(reuse: ReuseContext, index: int) -> dict:
        rows = reuse.minted.get("spellduration", [])
        return next(r for r in rows if r["ID"] == index)

    def test_build_spell_row_points_at_a_minted_row_with_both_values(self):
        reuse = _reuse()
        row = build.build_spell_row(_entry(duration_ms=4000, max_duration_ms=24000), reuse)
        # not 35 (the flat 4 s stock row) and not a flat row minted for the minimum alone
        self.assertEqual(row["DurationIndex"], 30100)
        self.assertEqual(
            self._row_for(reuse, row["DurationIndex"]),
            {"ID": 30100, "Duration": 4000, "DurationPerLevel": 0, "MaxDuration": 24000},
        )
        self.assertEqual(len(reuse.minted["spellduration"]), 1)

    def test_a_flat_spell_beside_it_still_reuses_the_flat_row(self):
        reuse = _reuse()
        ranged = build.build_spell_row(_entry(duration_ms=4000, max_duration_ms=24000), reuse)
        flat = build.build_spell_row(_entry(spell_id=203801, duration_ms=4000), reuse)
        self.assertEqual(flat["DurationIndex"], 35)
        self.assertNotEqual(ranged["DurationIndex"], flat["DurationIndex"])
        self.assertEqual(len(reuse.minted["spellduration"]), 1)

    def test_two_spells_with_the_same_pair_share_one_row_through_build(self):
        reuse = _reuse()
        a = build.build_spell_row(_entry(203800, duration_ms=4000, max_duration_ms=24000), reuse)
        b = build.build_spell_row(_entry(203801, duration_ms=4000, max_duration_ms=24000), reuse)
        self.assertEqual(a["DurationIndex"], b["DurationIndex"])
        self.assertEqual(self._row_for(reuse, a["DurationIndex"])["MaxDuration"], 24000)
        self.assertEqual(len(reuse.minted["spellduration"]), 1)

    def test_a_stock_ranged_row_is_reused_through_build(self):
        reuse = _reuse()
        row = build.build_spell_row(_entry(duration_ms=6000, max_duration_ms=21000), reuse)
        self.assertEqual(row["DurationIndex"], 185)
        self.assertNotIn("spellduration", reuse.minted)

    def test_the_typed_vs_raw_override_lint_reads_the_minimum(self):
        # lint.check_raw_override_typed_mismatch compares duration_ms with the raw DurationIndex row's `Duration`
        # column, i.e. the minimum of a ranged row. It cannot see max_duration_ms, which is why the model refuses a
        # declared max next to a raw DurationIndex (test_a_max_with_a_raw_duration_index_override_raises).
        index_tables = {"spellduration": {r["ID"]: r for r in STOCK_DURATIONS}}
        ok = _entry(duration_ms=6000, raw_overrides={"DurationIndex": 185})
        self.assertEqual(lint.check_raw_override_typed_mismatch([ok], index_tables), [])
        bad = _entry(duration_ms=4000, raw_overrides={"DurationIndex": 185})
        self.assertEqual(len(lint.check_raw_override_typed_mismatch([bad], index_tables)), 1)


class MaxDurationConvergenceTest(unittest.TestCase):
    """Render the minted row, read it back the way the next run reads live state, and re-run."""

    def _render(self, reuse: ReuseContext) -> str:
        return sql_out._table_block(TABLE, BLOCK, reuse.reserved_rows.get("spellduration", []), [])

    def test_rendered_sql_reads_back_through_the_real_reader(self):
        reuse = _reuse([])
        reuse.duration_index(4000, 24000)
        sql = self._render(reuse)
        self.assertIn("30100, 4000, 0, 24000", sql)
        rows: dict[int, dict] = {}
        sql_dump.apply_statements(rows, TABLE, sql)
        self.assertEqual(rows, {30100: {"ID": 30100, "Duration": 4000, "DurationPerLevel": 0, "MaxDuration": 24000}})

    def test_a_rerun_over_the_read_back_state_mints_nothing_and_re_renders_empty(self):
        first = _reuse([])
        first.duration_index(4000, 24000)
        first.duration_index(4000, 20000)
        sql = self._render(first)
        live: dict[int, dict] = {}
        sql_dump.apply_statements(live, TABLE, sql)

        second = _reuse(list(live.values()))
        self.assertEqual(second.duration_index(4000, 24000), 30100)
        self.assertEqual(second.duration_index(4000, 20000), 30101)
        self.assertEqual(second.minted, {})  # nothing re-minted: the readback row is found, not duplicated
        # what generate.py's _drop_unchanged_blocks asks: would the block change anything live? No.
        self.assertFalse(
            resolve.reserved_range_changed(second.reserved_rows["spellduration"], "ID", BLOCK, [], live)
        )

    def test_a_third_pair_added_later_changes_the_block_and_keeps_the_old_rows(self):
        first = _reuse([])
        first.duration_index(4000, 24000)
        live: dict[int, dict] = {}
        sql_dump.apply_statements(live, TABLE, self._render(first))
        second = _reuse(list(live.values()))
        self.assertEqual(second.duration_index(4000, 24000), 30100)
        self.assertEqual(second.duration_index(6000, 36000), 30101)
        rows = second.reserved_rows["spellduration"]
        self.assertEqual({r["ID"] for r in rows}, {30100, 30101})
        self.assertTrue(resolve.reserved_range_changed(rows, "ID", BLOCK, [], live))

    def test_the_minted_row_round_trips_through_a_dbc(self):
        reuse = _reuse([])
        reuse.duration_index(4000, 24000)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "SpellDuration.dbc"
            dbcfile.write_dbc(path, TABLE, reuse.reserved_rows["spellduration"])
            back = dbcfile.read_dbc(path, TABLE)
        self.assertEqual(back, [{"ID": 30100, "Duration": 4000, "DurationPerLevel": 0, "MaxDuration": 24000}])


if __name__ == "__main__":
    unittest.main()
