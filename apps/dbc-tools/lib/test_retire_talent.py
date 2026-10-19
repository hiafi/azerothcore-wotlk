"""
retire_talent() and the holding tab, plus order_talent_rows' final-TabID rule (hunter-rework SHARED §C7.7,
§C7.9; T1 steps 2-3). Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_retire_talent.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt  # noqa: E402
from lib.dsl import registry  # noqa: E402

TAB = registry.RETIRED_TAB_ID


def _talent(row_id: int, tab: int, tier: int, column: int, **extra) -> dict:
    row = dbcfile.empty_row(dbcfmt.TALENT)
    row.update(ID=row_id, TabID=tab, TierID=tier, ColumnIndex=column, **extra)
    return row


# Dash (a pet talent whose rank spell is also a pet ability) with prerequisites, flags and a category mask.
LIVE = {
    2110: _talent(
        2110, 409, 3, 1, SpellRank_1=61684, SpellRank_2=61685, PrereqTalent_1=2109, PrereqRank_1=1,
        PrereqTalent_2=2108, PrereqRank_2=2, Flags=1, RequiredSpellID=5, CategoryMask_1=0x10, CategoryMask_2=0x20,
    ),
}


def _load(source: str, live=LIVE) -> registry.Registry:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "hunter.py"
        path.write_text(source)
        return registry.load_class_file(path, live_data={"talent_rows": live})


class RetireTalentTest(unittest.TestCase):
    def test_emitted_row_is_the_live_row_moved_to_the_holding_tab(self):
        reg = _load("from lib.dsl.registry import retire_talent\nretire_talent(2110)\n")
        self.assertEqual([r["id"] for r in reg.retired_talents], [2110])
        row = build.build_talent_row(reg.talents[0])
        expected = _talent(2110, TAB, 0, 0, RequiredSpellID=5)
        self.assertEqual(row, expected)
        for column in ("SpellRank_1", "SpellRank_2", "PrereqTalent_1", "PrereqRank_1", "PrereqTalent_2",
                       "PrereqRank_2", "CategoryMask_1", "CategoryMask_2", "Flags", "TierID", "ColumnIndex"):
            self.assertEqual(row[column], 0, column)
        self.assertEqual(row["TabID"], 60800)

    def test_non_live_id_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "no live Talent.dbc row"):
            _load("from lib.dsl.registry import retire_talent\nretire_talent(999999)\n")

    def test_missing_live_data_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "hunter.py"
            path.write_text("from lib.dsl.registry import retire_talent\nretire_talent(2110)\n")
            with self.assertRaisesRegex(RuntimeError, "live talent rows"):
                registry.load_class_file(path)

    def test_missing_holding_tab_is_an_error_at_build_time(self):
        reg = _load("from lib.dsl.registry import retire_talent\nretire_talent(2110)\n")
        merged = {"retired_talents": reg.retired_talents, "tabs": reg.tabs}
        with self.assertRaises(registry.MissingRetiredTabError):
            registry.check_retired_talent_tab(merged)

    def test_declared_holding_tab_passes(self):
        reg = _load(
            "from lib.dsl.registry import retire_talent, tab\n"
            "tab(id=60800, name='Retired', class_mask=0, pet_talent_mask=0)\n"
            "retire_talent(2110)\n"
        )
        registry.check_retired_talent_tab({"retired_talents": reg.retired_talents, "tabs": reg.tabs})

    def test_no_retirement_needs_no_tab(self):
        registry.check_retired_talent_tab({"retired_talents": [], "tabs": []})


class OrderTalentRowsTest(unittest.TestCase):
    def setUp(self):
        # Base file: tab 362 (rows 10, 11), tab 363 (rows 20, 21), tab 409 (row 30).
        self.base = [
            _talent(10, 362, 0, 0), _talent(11, 362, 1, 0),
            _talent(20, 363, 0, 0), _talent(21, 363, 2, 1),
            _talent(30, 409, 0, 0),
        ]

    def _order(self, rows):
        return [r["ID"] for r in dbcfile.order_talent_rows(rows, self.base)]

    def test_untouched_file_keeps_its_physical_order(self):
        self.assertEqual(self._order([dict(r) for r in self.base]), [10, 11, 20, 21, 30])

    def test_retired_rows_land_in_one_trailing_holding_block(self):
        rows = [dict(r) for r in self.base]
        for r in rows:
            if r["ID"] in (11, 20):
                r.update(TabID=TAB, TierID=0, ColumnIndex=0)
        self.assertEqual(self._order(rows), [10, 21, 30, 11, 20])  # 362, 363, 409 blocks, then 60800

    def test_holding_block_follows_every_base_block_even_for_new_rows(self):
        rows = [dict(r) for r in self.base] + [_talent(60000, 362, 4, 0), _talent(60001, TAB, 0, 0)]
        rows[0].update(TabID=TAB)
        self.assertEqual(self._order(rows), [11, 60000, 20, 21, 30, 10, 60001])

    def test_row_moved_to_another_tab_sorts_inside_the_new_block(self):
        # Sniper Training shape: row 11 (362) -> tab 363 at tier 1, between rows 20 (tier 0) and 21 (tier 2).
        rows = [dict(r) for r in self.base]
        rows[1].update(TabID=363, TierID=1, ColumnIndex=0)
        self.assertEqual(self._order(rows), [10, 20, 11, 21, 30])

    def test_untouched_tab_block_is_byte_identical(self):
        # Packed through the same path generate.py uses: an untouched file repacks as the base did, and a
        # move between 362 and 363 leaves the 409 block's rows exactly where they were.
        table = dbcfmt.TALENT
        base_bytes = dbcfile.pack_dbc_bytes(table, self.base, sort=False)
        self.assertEqual(dbcfile.pack_client_dbc(table, [dict(r) for r in self.base], self.base), base_bytes)
        rows = [dict(r) for r in self.base]
        rows[1].update(TabID=363, TierID=1)
        moved = dbcfile.order_talent_rows(rows, self.base)
        self.assertEqual(moved[-1], self.base[4])
        self.assertEqual([r["TabID"] for r in moved], [362, 363, 363, 363, 409])

    def test_all_rows_are_kept(self):
        rows = [dict(r) for r in self.base]
        rows[2].update(TabID=TAB)
        self.assertEqual(sorted(self._order(rows)), [10, 11, 20, 21, 30])


if __name__ == "__main__":
    unittest.main()
