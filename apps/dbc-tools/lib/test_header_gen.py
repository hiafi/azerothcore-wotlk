"""
Unit tests for lib/header_gen.py (PLAN P2b - the generated per-class C++ constants header).
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from lib import header_gen


def _dsl_classes(**overrides):
    base = {
        "spells": [],
        "creature_templates": [],
        "consts": [],
        "spell_var_names": {},
        "creature_var_names": {},
    }
    base.update(overrides)
    return base


class DeriveConstNameTest(unittest.TestCase):
    def test_strips_trailing_id_and_uppercases(self):
        self.assertEqual(header_gen._derive_const_name("shadow_bolt_686", "SPELL_"), "SPELL_SHADOW_BOLT")

    def test_no_trailing_id(self):
        self.assertEqual(header_gen._derive_const_name("imp_firebolt", "SPELL_"), "SPELL_IMP_FIREBOLT")

    def test_npc_prefix(self):
        self.assertEqual(header_gen._derive_const_name("wild_imp_300150", "NPC_"), "NPC_WILD_IMP")


class BuildHeaderTest(unittest.TestCase):
    def test_no_content_returns_none(self):
        self.assertIsNone(header_gen.build_header("warlock", _dsl_classes()))

    def test_spell_ids_rendered(self):
        dsl = _dsl_classes(
            spells=[
                {"id": 686, "name": "Shadow Bolt", "_source_class": "warlock"},
                {"id": 1454, "name": "Life Tap", "_source_class": "warlock"},
            ],
            spell_var_names={686: "shadow_bolt_686", 1454: "life_tap_1454"},
        )
        text = header_gen.build_header("warlock", dsl)
        self.assertIn("namespace WarlockData", text)
        self.assertIn("constexpr uint32 SPELL_SHADOW_BOLT = 686;", text)
        self.assertIn("constexpr uint32 SPELL_LIFE_TAP = 1454;", text)
        self.assertTrue(text.startswith(header_gen.GENERATED_HEADER_MARKER))

    def test_other_classes_ignored(self):
        dsl = _dsl_classes(
            spells=[{"id": 116, "name": "Frostbolt", "_source_class": "mage"}],
            spell_var_names={116: "frostbolt_116"},
        )
        self.assertIsNone(header_gen.build_header("warlock", dsl))

    def test_creature_ids_rendered(self):
        dsl = _dsl_classes(
            creature_templates=[{"entry": 300150, "name": "Wild Imp", "_source_class": "warlock"}],
            creature_var_names={300150: "wild_imp_300150"},
        )
        text = header_gen.build_header("warlock", dsl)
        self.assertIn("constexpr uint32 NPC_WILD_IMP = 300150;", text)

    def test_multi_rank_name_collision_falls_back_to_full_var_name(self):
        # Real-world shape: nightfall_18094, nightfall_18095, nightfall_200766 (PLAN P2b - found
        # against the real warlock source, 100+ such collisions on the first real generate.py run).
        dsl = _dsl_classes(
            spells=[
                {"id": 18094, "name": "Nightfall", "_source_class": "warlock"},
                {"id": 18095, "name": "Nightfall", "_source_class": "warlock"},
                {"id": 200766, "name": "Nightfall", "_source_class": "warlock"},
            ],
            spell_var_names={18094: "nightfall_18094", 18095: "nightfall_18095", 200766: "nightfall_200766"},
        )
        text = header_gen.build_header("warlock", dsl)
        self.assertIn("constexpr uint32 SPELL_NIGHTFALL = 18094;", text)
        self.assertIn("constexpr uint32 SPELL_NIGHTFALL_18095 = 18095;", text)
        self.assertIn("constexpr uint32 SPELL_NIGHTFALL_200766 = 200766;", text)
        # No duplicate constant names anywhere - this is what would otherwise fail to compile.
        names = re.findall(r"constexpr uint32 (\S+) =", text)
        self.assertEqual(len(names), len(set(names)))

    def test_missing_var_name_is_skipped_not_fatal(self):
        dsl = _dsl_classes(spells=[{"id": 686, "name": "Shadow Bolt", "_source_class": "warlock"}])
        text = header_gen.build_header("warlock", dsl)
        self.assertIsNone(text)  # no var name found anywhere -> nothing to emit for it

    def test_consts_rendered_with_types(self):
        dsl = _dsl_classes(
            consts=[
                {"name": "WARLOCK_SOUL_SHARD_CAP", "value": 5, "doc": "max shards", "cpp_type": "int32", "_source_class": "warlock"},
                {"name": "WARLOCK_BACKLASH_PCT", "value": 0.25, "doc": "", "cpp_type": "float", "_source_class": "warlock"},
            ]
        )
        text = header_gen.build_header("warlock", dsl)
        self.assertIn("constexpr int32 WARLOCK_SOUL_SHARD_CAP = 5; // max shards", text)
        self.assertIn("constexpr float WARLOCK_BACKLASH_PCT = 0.25f;", text)

    def test_talent_ids_never_emitted(self):
        # header_gen has no code path that reads "talents" at all - this just documents the
        # deliberate omission (see the module docstring) stays true even if a future edit adds a
        # talents list to the input dict.
        dsl = _dsl_classes()
        dsl["talents"] = [{"id": 60000, "_source_class": "warlock"}]
        self.assertIsNone(header_gen.build_header("warlock", dsl))


class WriteAndCheckHeadersTest(unittest.TestCase):
    def test_write_then_check_is_clean(self):
        dsl = _dsl_classes(
            spells=[{"id": 686, "name": "Shadow Bolt", "_source_class": "warlock"}],
            spell_var_names={686: "shadow_bolt_686"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            written = header_gen.write_headers(dsl, out_dir, ("warlock",))
            self.assertEqual(len(written), 1)
            self.assertTrue((out_dir / "WarlockData.h").exists())
            problems = header_gen.check_headers(dsl, out_dir, ("warlock",))
            self.assertEqual(problems, [])

    def test_check_detects_stale_file(self):
        dsl = _dsl_classes(
            spells=[{"id": 686, "name": "Shadow Bolt", "_source_class": "warlock"}],
            spell_var_names={686: "shadow_bolt_686"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            header_gen.write_headers(dsl, out_dir, ("warlock",))
            # Source changes (a new spell) without regenerating.
            dsl["spells"].append({"id": 1454, "name": "Life Tap", "_source_class": "warlock"})
            dsl["spell_var_names"][1454] = "life_tap_1454"
            problems = header_gen.check_headers(dsl, out_dir, ("warlock",))
            self.assertEqual(len(problems), 1)
            self.assertIn("stale", problems[0])

    def test_check_detects_missing_file(self):
        dsl = _dsl_classes(
            spells=[{"id": 686, "name": "Shadow Bolt", "_source_class": "warlock"}],
            spell_var_names={686: "shadow_bolt_686"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            problems = header_gen.check_headers(dsl, out_dir, ("warlock",))
            self.assertEqual(len(problems), 1)
            self.assertIn("doesn't exist", problems[0])


if __name__ == "__main__":
    unittest.main()
