"""
Unit tests for `lib/header_gen.py`'s X2 short-name-loss warning (paladin-rework SHARED B6 item 7).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_header_gen_warnings.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import header_gen  # noqa: E402


def _classes(spells: dict[int, tuple[str, str]]) -> dict:
    """{id: (var_name, spell_name)} -> a minimal dsl_classes for class 'paladin'."""
    return {
        "spells": [{"id": i, "name": n, "_source_class": "paladin"} for i, (_, n) in spells.items()],
        "spell_var_names": {i: v for i, (v, _) in spells.items()},
        "creature_templates": [], "creature_var_names": {}, "consts": [],
    }


class HeaderShortNameWarningTest(unittest.TestCase):
    def test_custom_id_losing_short_name_warns(self):
        dsl = _classes({201069: ("unleash_201069", "Judgement"), 201075: ("unleash_201075", "Deliverance")})
        warnings = header_gen.collect_warnings(dsl, ("paladin",))
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0].startswith("header:"))
        self.assertIn("201075", warnings[0])
        self.assertIn("SPELL_UNLEASH", warnings[0])

    def test_stock_rank_siblings_stay_quiet(self):
        dsl = _classes({18094: ("nightfall_18094", "Nightfall"), 18095: ("nightfall_18095", "Nightfall")})
        self.assertEqual(header_gen.collect_warnings(dsl, ("paladin",)), [])

    def test_stock_non_rank_clash_warns(self):
        dsl = _classes({100: ("smite_100", "Smite"), 200: ("smite_200", "Holy Fire")})
        self.assertEqual(len(header_gen.collect_warnings(dsl, ("paladin",))), 1)

    def test_custom_rank_siblings_stay_quiet(self):
        dsl = _classes({67: ("vindication_67", "Vindication"), 201466: ("vindication_201466", "Vindication")})
        self.assertEqual(header_gen.collect_warnings(dsl, ("paladin",)), [])

    def test_unique_names_no_warning(self):
        dsl = _classes({201069: ("unleash_justice_201069", "A"), 201075: ("unleash_justice_aoe_201075", "B")})
        self.assertEqual(header_gen.collect_warnings(dsl, ("paladin",)), [])

    def test_warning_does_not_change_header_text(self):
        dsl = _classes({201069: ("unleash_201069", "A"), 201075: ("unleash_201075", "B")})
        self.assertEqual(header_gen.build_header("paladin", dsl), header_gen.build_header("paladin", dsl, []))

    def test_class_outside_warn_classes_is_silent(self):
        dsl = _classes({201069: ("unleash_201069", "A"), 201075: ("unleash_201075", "B")})
        for spell in dsl["spells"]:
            spell["_source_class"] = "warlock"
        self.assertEqual(header_gen.collect_warnings(dsl, ("warlock",)), [])

    def test_class_with_no_declarations_is_fine(self):
        dsl = _classes({})
        self.assertEqual(header_gen.collect_warnings(dsl, ("paladin",)), [])
        self.assertIsNone(header_gen.build_header("paladin", dsl))


if __name__ == "__main__":
    unittest.main()
