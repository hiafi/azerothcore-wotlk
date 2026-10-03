"""tooltip_vars() and its builders (potency-system.PLAN.md P9.2): rendering, declaration-time
errors, the spell(tooltip_vars=) wiring, and lint.check_tooltip_vars (D12)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import lint  # noqa: E402
from lib.dsl import model, registry, tooltip  # noqa: E402

IDS_CFG = {"spelldescriptionvariables": {"start": 1000, "end": 1999}}

# Stock entry 167 (Frostbolt's talent chain), trimmed.
STOCK_167 = "$piercing1=$?s11151[${1.02}][${1}]\r\n$mult=${$<piercing1>}"


class BuilderRenderTest(unittest.TestCase):
    def test_talent_mult_renders_rank_chain_highest_rank_last(self):
        entry = tooltip.render_entry(1000, {"piercing": tooltip.talent_mult([11151, 12952, 12953])})
        self.assertEqual(entry.text.split("\r\n"), [
            "$piercing1=$?s11151[${$11151m1*0.01+1}][${1}]",
            "$piercing2=$?s12952[${$12952m1*0.01+1}][${$<piercing1>}]",
            "$piercing=$?s12953[${$12953m1*0.01+1}][${$<piercing2>}]",
        ])
        self.assertEqual(entry.names, {"piercing", "piercing1", "piercing2"})

    def test_talent_mult_single_rank_effect_and_object_inputs(self):
        talent = SimpleNamespace(rank_spell_ids=[31674])
        entry = tooltip.render_entry(1000, {"arctic": tooltip.talent_mult(talent, effect=2)})
        self.assertEqual(entry.text, "$arctic=$?s31674[${$31674m2*0.01+1}][${1}]")
        spells = [SimpleNamespace(id=200001), SimpleNamespace(id=200002)]
        entry = tooltip.render_entry(1000, {"t": tooltip.talent_mult(spells)})
        self.assertIn("$t=$?s200002[${$200002m1*0.01+1}][${$<t1>}]", entry.text)

    def test_conditions_and_product(self):
        entry = tooltip.render_entry(1000, {
            "base": "${$m1*2}",
            "glyph": tooltip.has_aura(63279, "$<base>*1.2", "$<base>"),
            "known": tooltip.knows(SimpleNamespace(id=55441), 1.5),
            "mult": tooltip.product("glyph", "known", 1.1),
        })
        self.assertEqual(entry.text.split("\r\n"), [
            "$base=${$m1*2}",
            "$glyph=$?a63279[${$<base>*1.2}][${$<base>}]",
            "$known=$?s55441[${1.5}][${1}]",
            "$mult=${$<glyph>*$<known>*1.1}",
        ])

    def test_defined_names_reads_stock_text(self):
        self.assertEqual(tooltip.defined_names(STOCK_167), {"piercing1", "mult"})


class RenderErrorsTest(unittest.TestCase):
    def assertRejects(self, variables, fragment):
        with self.assertRaises(ValueError) as ctx:
            tooltip.render_entry(1000, variables)
        self.assertIn(fragment, str(ctx.exception))

    def test_reference_must_be_defined_earlier(self):
        self.assertRejects({"mult": tooltip.product("a", "b"), "a": "${1}", "b": "${2}"},
                           "isn't defined earlier")

    def test_s_read_is_rejected(self):
        self.assertRejects({"x": "${$11151s1*0.01+1}"}, "use $11151m<n> instead")

    def test_duplicate_name_from_chain_helper(self):
        self.assertRejects({"p1": "${1}", "p": tooltip.talent_mult([1, 2])}, "defined twice")

    def test_bad_name_empty_and_too_long(self):
        self.assertRejects({"Mult": "${1}"}, "must be lowercase")
        self.assertRejects({}, "at least one variable")
        self.assertRejects({"x": "${" + "1*" * 600 + "1}"}, "over the 1024 limit")

    def test_builder_argument_errors(self):
        with self.assertRaises(ValueError):
            tooltip.talent_mult([])
        with self.assertRaises(ValueError):
            tooltip.talent_mult([1], effect=4)
        with self.assertRaises(ValueError):
            tooltip.product("a")


DECLARING_FILE = '''
from lib.dsl.registry import spell, talent_mult, tooltip_vars

frost = tooltip_vars(1000, "Frost talents", piercing=talent_mult([11151, 12952]))
frostbolt = spell(id=116, name="Frostbolt", tooltip_vars=frost,
                  raw_overrides={"Description_Lang_enUS": "Deals ${100*$<piercing>} damage."})
'''

SECOND_FILE_SAME_ID = '''
from lib.dsl.registry import tooltip_vars

other = tooltip_vars(1000, "clash", x="${1}")
'''


class RegistryTest(unittest.TestCase):
    def _load(self, source: str, ids_cfg=IDS_CFG):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(source)
            return registry.load_class_file(path, ids_cfg=ids_cfg)

    def test_declares_entry_and_sets_spell_id(self):
        reg = self._load(DECLARING_FILE)
        self.assertEqual(len(reg.tooltip_vars), 1)
        self.assertEqual(reg.tooltip_vars[0]["id"], 1000)
        self.assertTrue(reg.tooltip_vars[0]["Variables"].startswith("$piercing1=$?s11151["))
        self.assertEqual(reg.spells[0]["raw_overrides"]["SpellDescriptionVariableID"], 1000)

    def test_id_outside_block_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self._load(DECLARING_FILE.replace("tooltip_vars(1000", "tooltip_vars(167"))
        self.assertIn("spelldescriptionvariables block (1000-1999)", str(ctx.exception))

    def test_same_id_in_two_files_raises(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(DECLARING_FILE)
            (Path(d) / "zzz.py").write_text(SECOND_FILE_SAME_ID)
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)

    def test_tooltip_vars_and_raw_override_conflict(self):
        handle = tooltip.render_entry(1000, {"x": "${1}"})
        with self.assertRaises(ValueError):
            model.Spell(id=1, name="x", tooltip_vars=handle,
                        raw_overrides={"SpellDescriptionVariableID": 167}).to_entry()


def _spell(spell_id, entry_id=0, desc="", aura=""):
    raw = {"Description_Lang_enUS": desc, "AuraDescription_Lang_enUS": aura}
    if entry_id:
        raw["SpellDescriptionVariableID"] = entry_id
    return {"id": spell_id, "name": f"s{spell_id}", "raw_overrides": raw}


class LintTest(unittest.TestCase):
    DECLARED = [{"id": 1000, "Variables": "$mult=$?s11151[${$11151m1*0.01+1}][${1}]"}]
    STOCK = {167: STOCK_167}
    KNOWN = {116, 11151}

    def check(self, spells, declared=None, stock=STOCK, known=KNOWN):
        return lint.check_tooltip_vars(spells, self.DECLARED if declared is None else declared, stock, known)

    def test_clean_spells_pass(self):
        errors, notes = self.check([_spell(116, 1000, "x ${100*$<mult>}"), _spell(10, 167, aura="$<mult>")])
        self.assertEqual((errors, notes), ([], []))

    def test_undefined_variable(self):
        errors, _ = self.check([_spell(116, 1000, "$<nope>")])
        self.assertIn("doesn't define", errors[0])

    def test_variable_without_entry(self):
        errors, _ = self.check([_spell(116, 0, "$<mult>")])
        self.assertIn("has no SpellDescriptionVariableID", errors[0])

    def test_missing_entry_id(self):
        errors, _ = self.check([_spell(116, 1500, "$<mult>")])
        self.assertIn("1500 doesn't exist", errors[0])

    def test_stock_entry_skipped_without_stock_file(self):
        errors, _ = self.check([_spell(10, 167, "$<mult>")], stock=None)
        self.assertEqual(errors, [])

    def test_unknown_spell_reference(self):
        errors, _ = self.check([], known={116})
        self.assertIn("references spell 11151", errors[0])

    def test_unused_entry_is_a_note_only(self):
        errors, notes = self.check([_spell(116, 1000, "plain text"), _spell(117, 4294967295)])
        self.assertEqual(errors, [])
        self.assertEqual(len(notes), 1)
        self.assertIn(": 116", notes[0])


class PotencyPlaceholderTest(unittest.TestCase):
    """P9.3 end to end: a potency spell whose description multiplies its range by a tooltip
    variable (`{pot1*mult}`) passes the lint with tooltip_vars= and fails it without."""

    def _bolt(self, **kwargs):
        return model.Spell(
            id=90000, name="Test Bolt", cast_time_ms=3000,
            effects=[model.Effect(type=2, sp_potency=100, potency_kind="direct")],
            raw_overrides={"SpellLevel": 1, "Description_Lang_enUS": "Deals {pot1*mult} damage."},
            **kwargs,
        ).to_entry()

    def test_lint_passes_with_entry_and_fails_without(self):
        handle = tooltip.render_entry(1000, {"mult": tooltip.talent_mult([11151])})
        declared = [{"id": 1000, "Variables": handle.text}]
        errors, _ = lint.check_tooltip_vars([self._bolt(tooltip_vars=handle)], declared, {}, {11151})
        self.assertEqual(errors, [])
        errors, _ = lint.check_tooltip_vars([self._bolt()], declared, {}, {11151})
        self.assertIn("has no SpellDescriptionVariableID", errors[0])


class PotTextTest(unittest.TestCase):
    """registry.pot_text: another spell's {pot1} text, for a description that shows a trigger
    spell's value (Stoneclaw Totem 5730 showing 55328's absorb)."""

    def _absorb(self, **effect):
        return model.Spell(
            id=90001, name="Test Absorb", duration_ms=15000,
            effects=[model.Effect(type=77, potency_kind="absorb", **effect)],
            raw_overrides={"SpellLevel": 1, "Description_Lang_enUS": "Absorbs {pot1} damage."},
        )

    def test_matches_the_source_spells_own_placeholder(self):
        source = self._absorb(base_potency=50.0)
        own = source.to_entry()["raw_overrides"]["Description_Lang_enUS"]
        self.assertEqual(f"Absorbs {registry.pot_text(source)} damage.", own)
        self.assertNotIn("$SP", registry.pot_text(source))  # base_potency only: no SP term

    def test_rejects_an_effect_without_potency_and_a_bad_variant(self):
        with self.assertRaises(ValueError):
            registry.pot_text(self._absorb(base_potency=50.0), effect=2)
        with self.assertRaises(ValueError):
            registry.pot_text(self._absorb(base_potency=50.0), variant="max")


if __name__ == "__main__":
    unittest.main()
