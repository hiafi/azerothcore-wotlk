"""
lib/item_key_refs.py (crafting rework C7): recipe spells name the minted item they create by its item() key.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_key_refs.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import item_ids, item_key_refs  # noqa: E402


def _lock() -> item_ids.Lock:
    return item_ids.Lock(lines=[item_ids.LockLine(72200, "locked_key", "normal"),
                                item_ids.LockLine(72201, "gone_key", "normal", retired="2026-11-12")])


class ItemKeyRefsTest(unittest.TestCase):
    def test_resolve(self):
        spells = [
            {"id": 1, "name": "A", "raw_overrides": {"EffectItemType_1": item_key_refs.ref("new_key")}},
            {"id": 2, "name": "B", "raw_overrides": {"EffectItemType_2": item_key_refs.ref("locked_key")}},
            {"id": 3, "name": "C", "raw_overrides": {"EffectItemType_1": 12345}},
            {"id": 4, "name": "D"},
        ]
        errors = item_key_refs.resolve(spells, {("new_key", "normal"): 72300}, lock_loader=_lock)
        self.assertEqual(errors, [])
        self.assertEqual(spells[0]["raw_overrides"]["EffectItemType_1"], 72300)
        self.assertEqual(spells[1]["raw_overrides"]["EffectItemType_2"], 72201 - 1)
        self.assertEqual(spells[2]["raw_overrides"]["EffectItemType_1"], 12345)

    def test_unresolved_and_retired(self):
        for key in ("missing_key", "gone_key"):
            spells = [{"id": 9, "name": "X", "raw_overrides": {"EffectItemType_1": item_key_refs.ref(key)}}]
            errors = item_key_refs.resolve(spells, None, lock_loader=_lock)
            self.assertEqual(len(errors), 1)
            self.assertIn(key, errors[0])

    def test_ref_round_trip(self):
        self.assertEqual(item_key_refs.parse(item_key_refs.ref("k", "heroic")), ("k", "heroic"))
        self.assertFalse(item_key_refs.is_ref(5))


if __name__ == "__main__":
    unittest.main()
