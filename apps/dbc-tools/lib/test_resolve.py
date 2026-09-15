"""Unit tests for `lib/resolve.py` - `resolve_rows`'s existing new/edited/
unchanged split, and `reserved_range_changed`, which decides whether a
table's DELETE+INSERT block would actually change anything live (see its
own docstring - this is what lets `generate.py` skip emitting an unchanged
table's block instead of re-emitting identical content every single run).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_resolve.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import resolve  # noqa: E402

ID_RANGE = {"start": 200000, "end": 200099}


class ResolveRowsTest(unittest.TestCase):
    def test_in_range_entry_always_kept_even_if_unchanged(self):
        entries = [{"id": 200000, "v": 1}]
        existing = {200000: {"id": 200000, "v": 1}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, entries)
        self.assertEqual(r.edited_ids, [])
        self.assertEqual(r.unchanged, 0)

    def test_out_of_range_unchanged_entry_is_skipped(self):
        entries = [{"id": 116, "v": 1}]
        existing = {116: {"id": 116, "v": 1}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, [])
        self.assertEqual(r.unchanged, 1)

    def test_out_of_range_changed_entry_is_an_edit(self):
        entries = [{"id": 116, "v": 2}]
        existing = {116: {"id": 116, "v": 1}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, entries)
        self.assertEqual(r.edited_ids, [116])

    def test_none_vs_empty_string_is_not_a_change(self):
        # build_spell_row writes None for an unset locale field; the base DBC's string block has
        # no NULL concept, so the same "no override" value reads back as '' - not a real edit.
        entries = [{"id": 116, "v": None}]
        existing = {116: {"id": 116, "v": ""}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, [])
        self.assertEqual(r.unchanged, 1)

    def test_crlf_vs_lf_is_not_a_change(self):
        # A chunk of source/spells/*.csv's raw_overrides text has literal \r\n baked into the
        # JSON string (Windows-authored copy/paste); live data only ever has bare \n.
        entries = [{"id": 116, "v": "line one\r\nline two"}]
        existing = {116: {"id": 116, "v": "line one\nline two"}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, [])
        self.assertEqual(r.unchanged, 1)

    def test_a_real_value_change_alongside_a_none_vs_empty_field_is_still_an_edit(self):
        entries = [{"id": 116, "v": None, "w": 2}]
        existing = {116: {"id": 116, "v": "", "w": 1}}
        r = resolve.resolve_rows(entries, ID_RANGE, existing, lambda e: e)
        self.assertEqual(r.entries, entries)
        self.assertEqual(r.edited_ids, [116])


class ReservedRangeChangedTest(unittest.TestCase):
    def test_no_edits_and_identical_reserved_content_is_unchanged(self):
        rows = [{"ID": 200000, "v": 1}, {"ID": 200001, "v": 2}]
        existing = {200000: {"ID": 200000, "v": 1}, 200001: {"ID": 200001, "v": 2}}
        self.assertFalse(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_edited_ids_non_empty_is_always_a_change(self):
        # Even if the reserved-range content happens to be identical, a real edit outside the
        # block (edited_ids) means the block's DELETE ... WHERE ID IN (edited_ids) + reinsert
        # would do real work.
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}}
        self.assertTrue(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [116], existing))

    def test_changed_field_value_is_a_change(self):
        rows = [{"ID": 200000, "v": 99}]
        existing = {200000: {"ID": 200000, "v": 1}}
        self.assertTrue(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_new_row_not_in_existing_is_a_change(self):
        rows = [{"ID": 200000, "v": 1}, {"ID": 200001, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}}
        self.assertTrue(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_removed_row_still_in_existing_is_a_change(self):
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}, 200001: {"ID": 200001, "v": 1}}
        self.assertTrue(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_existing_rows_outside_the_range_are_ignored(self):
        # A stock/reference row that happens to sit outside this table's reserved block (e.g.
        # existing_rows for the whole table, not pre-filtered) must never make this look changed.
        rows = [{"ID": 200000, "v": 1}]
        existing = {200000: {"ID": 200000, "v": 1}, 116: {"ID": 116, "v": 999}}
        self.assertFalse(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_empty_reserved_content_matching_empty_existing_is_unchanged(self):
        self.assertFalse(resolve.reserved_range_changed([], "ID", ID_RANGE, [], {}))

    def test_none_vs_empty_string_in_reserved_block_is_not_a_change(self):
        rows = [{"ID": 200000, "v": None}]
        existing = {200000: {"ID": 200000, "v": ""}}
        self.assertFalse(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))

    def test_crlf_vs_lf_in_reserved_block_is_not_a_change(self):
        rows = [{"ID": 200000, "v": "line one\r\nline two"}]
        existing = {200000: {"ID": 200000, "v": "line one\nline two"}}
        self.assertFalse(resolve.reserved_range_changed(rows, "ID", ID_RANGE, [], existing))


if __name__ == "__main__":
    unittest.main()
