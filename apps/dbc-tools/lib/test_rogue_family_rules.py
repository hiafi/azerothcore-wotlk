"""
Rogue family-bit rules (Rogue T1 step 3, rogue-rework.FAMILY-BITS.md s3.3 / s6.1 C2, PLAN s1D.11).

`lint.ROGUE_FAMILY_RULES` (`SpellClassSet` 8) bans three carrier bits on a custom (>= 200000) rogue-family spell:
d0 b11 (0x800), d0 b22 (0x400000) and d0 b25 (0x2000000). Stock rogue ids and other classes' spells are never judged,
and the P0 spike spells, loaded through the real class-package path, carry none of them.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_rogue_family_rules.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, lint, spell_tables, state, test_id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

RULES = (lint.ROGUE_FAMILY_RULES,)
SPIKE_FILE = TOOL_ROOT / "source" / "classes" / "rogue" / "rogue_p0_spike.py"

STEALTH_BIT, MASTER_OF_SUBTLETY_BIT, HEMORRHAGE_BIT = 0x800, 0x400000, 0x2000000  # d0 b11, d0 b22, d0 b25


def _row(spell_id=203800, **cols) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 8, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0}
    row.update(cols)
    return row


def _check(row, name="Test Spell", procs=None, rules=RULES):
    return lint.check_family_bit_rules([{"name": name}], [row], procs, None, frozenset(), rules=rules)


class RogueFamilyRulesTest(unittest.TestCase):
    def test_the_row_is_registered_with_the_other_classes(self):
        rules = lint.ROGUE_FAMILY_RULES
        for other in (lint.HUNTER_FAMILY_RULES, lint.SHAMAN_FAMILY_RULES, lint.DEATHKNIGHT_FAMILY_RULES):
            self.assertIn(other, lint.FAMILY_BIT_RULES)
        self.assertIn(rules, lint.FAMILY_BIT_RULES)
        self.assertEqual(rules.spell_class_set, 8)
        self.assertEqual(rules.forbidden_carrier_bits, (STEALTH_BIT | MASTER_OF_SUBTLETY_BIT | HEMORRHAGE_BIT, 0, 0))
        # the other rules stay silent: the bits that depend on the spell's role are RG0's targeted tests
        self.assertEqual(rules.protected_bits, (0, 0, 0))
        self.assertEqual(rules.forbidden_reader_bits, (0, 0, 0))
        self.assertEqual(rules.pet_required_bits, (0, 0, 0))

    def test_each_forbidden_bit_on_a_custom_rogue_spell_warns(self):
        for bit in (STEALTH_BIT, MASTER_OF_SUBTLETY_BIT, HEMORRHAGE_BIT):
            with self.subTest(bit=hex(bit)):
                warnings = _check(_row(SpellClassMask_1=bit))
                self.assertEqual(len(warnings), 1)
                self.assertIn("rogue family-bit rule (b)", warnings[0])
                self.assertIn("spell 203800 (Test Spell)", warnings[0])

    def test_a_forbidden_bit_among_allowed_ones_still_warns(self):
        # 0x200 (Ambush's bit) is allowed; the b11 next to it is not
        self.assertEqual(len(_check(_row(SpellClassMask_1=0x200 | STEALTH_BIT))), 1)

    def test_the_message_names_each_cause(self):
        message = _check(_row(SpellClassMask_1=STEALTH_BIT))[0]
        for fragment in ("d0 b11", "Stealth", "d0 b22", "Master of Subtlety", "d0 b25", "Hemorrhage"):
            self.assertIn(fragment, message)

    def test_other_dwords_and_other_bits_are_silent(self):
        # the same numbers in d1 / d2 are different bits. The d0 bits below are NOT in the carrier table: 0x200 (b9,
        # Ambush) and 0x200000 (b21) are plain, while 0x1 (b0, Throw), 0x1000000 (b24, DR category) and 0x4000000 (b26,
        # dagger +50%) are never-take bits that depend on the spell's role (FAMILY-BITS s3.3): RG0's targeted tests
        for column in ("SpellClassMask_2", "SpellClassMask_3"):
            for bit in (STEALTH_BIT, MASTER_OF_SUBTLETY_BIT, HEMORRHAGE_BIT):
                self.assertEqual(_check(_row(**{column: bit})), [], (column, hex(bit)))
        for bit in (0x200, 0x1, 0x200000, 0x1000000, 0x4000000):
            self.assertEqual(_check(_row(SpellClassMask_1=bit)), [], hex(bit))

    def test_a_clean_custom_rogue_spell_is_silent(self):
        self.assertEqual(_check(_row()), [])
        self.assertEqual(_check(_row(SpellClassMask_1=0x700, SpellClassMask_2=0x80000)), [])

    def test_a_stock_rogue_id_is_never_judged(self):
        # Stealth 1784 itself carries d0 b11 and Hemorrhage 16511 carries d0 b25: stock ids are exempt
        self.assertEqual(_check(_row(1784, SpellClassMask_1=STEALTH_BIT)), [])
        self.assertEqual(_check(_row(16511, SpellClassMask_1=HEMORRHAGE_BIT)), [])
        self.assertEqual(_check(_row(199999, SpellClassMask_1=MASTER_OF_SUBTLETY_BIT)), [])
        self.assertEqual(len(_check(_row(200000, SpellClassMask_1=MASTER_OF_SUBTLETY_BIT))), 1)

    def test_another_classs_custom_spell_is_not_judged(self):
        for family in (0, 9, 11, 15):
            self.assertEqual(_check(_row(SpellClassSet=family, SpellClassMask_1=STEALTH_BIT)), [], family)

    def test_the_rule_runs_in_the_default_rule_set(self):
        # generate.py calls check_family_bit_rules with no `rules=`: --check and the full run both get the rogue row
        warnings = lint.check_family_bit_rules([{"name": "X"}], [_row(SpellClassMask_1=STEALTH_BIT)])
        self.assertEqual(len(warnings), 1)
        self.assertIn("rogue family-bit rule (b)", warnings[0])

    def test_a_spell_proc_row_is_not_judged_by_the_carrier_rule(self):
        # rule (c) is a no-op for the rogue (no forbidden reader bits): a family mask with these bits is fine
        procs = [{"SpellId": 14156, "SpellFamilyName": 8, "SpellFamilyMask0": STEALTH_BIT, "SpellFamilyMask1": 0,
                  "SpellFamilyMask2": 0}]
        self.assertEqual(_check(_row(), procs=procs), [])


class _SpikeSpells:
    """The rogue package as the generator builds it (stock-id declarations plus the P0 spike's custom spells): the real
    class-package loader, the real row builder."""

    @classmethod
    def load(cls):
        ids = test_id_blocks.IDS
        stock = {name: list(state.load_stock_rows(table).values()) for name, table in {
            "spellcasttimes": dbcfmt.SPELLCASTTIMES, "spellduration": dbcfmt.SPELLDURATION,
            "spellrange": dbcfmt.SPELLRANGE, "spellradius": dbcfmt.SPELLRADIUS}.items()}
        stock_talents = (
            state.load_stock_rows(dbcfmt.TALENT) if (state.BASE_DBC_DIR / dbcfmt.TALENT.dbc_filename).is_file() else {}
        )
        reg = registry.load_class_package(
            TOOL_ROOT / "source" / "classes" / "rogue", ids_cfg=ids, trainer_index=test_id_blocks._AnyTrainer(),
            existing_group_ids=test_id_blocks._AnySet(), shapeshift_index={},
            existing_creature_rows=test_id_blocks._AnyRows(), creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.dsl_live_data(
                stock_talents, {},
                lambda: state.load_existing_rows(dbcfmt.SKILLLINEABILITY),
                lambda: state.load_stock_rows(dbcfmt.CHRCLASSES),
                lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
            ),
        )
        reuse = ReuseContext(stock, ids)
        entries = list(reg.spells)
        return reg, entries, [build.build_spell_row(e, reuse) for e in entries]


@unittest.skipUnless(SPIKE_FILE.is_file(), "the P0 spike file is deleted at RG0 start")
class RogueFamilyRulesOnTheSpikeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg, cls.entries, cls.rows = _SpikeSpells.load()

    def test_the_spike_spells_were_loaded_and_are_rogue_family(self):
        # not vacuous: real rows, in the custom range, of SpellClassSet 8
        judged = [r for r in self.rows if int(r["ID"]) >= 200000 and int(r["SpellClassSet"]) == 8]
        self.assertGreaterEqual(len(judged), 15)
        self.assertTrue(all(204370 <= int(r["ID"]) <= 204399 for r in judged))

    def test_the_spike_spells_carry_none_of_the_forbidden_bits(self):
        # custom ids only: the lint never judges a stock id (rogue_spells.py declares the stock rows, Vanish 11327
        # carries d0 b11 as the stock spell does)
        for row in self.rows:
            if int(row["ID"]) >= 200000:
                self.assertEqual(
                    int(row["SpellClassMask_1"]) & lint.ROGUE_FAMILY_RULES.forbidden_carrier_bits[0], 0, row["ID"],
                )

    def test_the_spike_spells_are_silent(self):
        warnings = lint.check_family_bit_rules(
            self.entries, self.rows, self.reg.spell_procs, [], frozenset(), rules=RULES,
        )
        self.assertEqual(warnings, [])
        # and in the default rule set, the way generate.py calls it
        self.assertEqual(
            lint.check_family_bit_rules(self.entries, self.rows, self.reg.spell_procs, [], frozenset()), [],
        )

    def test_the_same_rows_with_one_forbidden_bit_added_do_warn(self):
        # the loaded rows are judged: poison one and exactly that one is reported
        rows = [dict(r) for r in self.rows]
        victim = next(r for r in rows if int(r["SpellClassSet"]) == 8)
        victim["SpellClassMask_1"] = int(victim["SpellClassMask_1"]) | STEALTH_BIT
        warnings = lint.check_family_bit_rules(self.entries, rows, self.reg.spell_procs, [], frozenset(), rules=RULES)
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"spell {victim['ID']}", warnings[0])


if __name__ == "__main__":
    unittest.main()
