"""
Warrior family-bit rules (Warrior T1 WP2, warrior-rework.FAMILY-BITS.md s3.3 / s5 / s6.2).

`lint.WARRIOR_FAMILY_RULES` (`SpellClassSet` 4) bans seven carrier bits on a custom (>= 200000) warrior-family spell
(d0 b0 / b1 / b17 / b24, d1 b5 / b6, d2 b31) and the Draenei racial's bit d2 b31 in any reader mask. Stock warrior ids
and other classes' spells are never judged, and the real warrior package (the September Protection build plus the P0
spike), loaded through the real class-package path, carries none of the banned bits.
`source/classes/warrior/_masks.py` holds the same masks as named constants; the lint cannot import it (a lint must not
import the thing it checks), so these tests assert the two agree.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_warrior_family_rules.py
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, lint, spell_tables, state, test_id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

RULES = (lint.WARRIOR_FAMILY_RULES,)
CLASS_DIR = TOOL_ROOT / "source" / "classes" / "warrior"
SPIKE_FILE = CLASS_DIR / "warrior_p0_spike.py"
MASKS_FILE = CLASS_DIR / "_masks.py"

# (column, bit mask, cause fragment the message must name): every banned carrier bit
BANNED_CARRIERS = (
    ("SpellClassMask_1", 0x1, "d0 b0 Charge"),
    ("SpellClassMask_1", 0x2, "d0 b1 / b24 diminishing"),
    ("SpellClassMask_1", 0x20000, "d0 b17 / d1 b5 the Shout CC marker"),
    ("SpellClassMask_1", 0x1000000, "d0 b1 / b24 diminishing"),
    ("SpellClassMask_2", 0x20, "d0 b17 / d1 b5 the Shout CC marker"),
    ("SpellClassMask_2", 0x40, "d1 b6 Devastate"),
    ("SpellClassMask_3", 0x80000000, "d2 b31 the Draenei racial"),
)
# allowed bits the lint must stay silent on: the role bits (W0b / the spec stages pin them with targeted tests) and the
# FAMILY-BITS s5 allocation
ALLOWED = (
    ("SpellClassMask_1", 0x80),         # d0 b7: Thunder Clap and its echo
    ("SpellClassMask_1", 0x400),        # d0 b10: Revenge
    ("SpellClassMask_1", 0x800000),     # d0 b23: stances
    ("SpellClassMask_2", 0x100),        # d1 b8: Victory Rush
    ("SpellClassMask_2", 0x200),        # d1 b9: Shield Slam
    ("SpellClassMask_2", 0x40000),      # d1 b18: Victorious
    ("SpellClassMask_3", 0x1), ("SpellClassMask_3", 0x2), ("SpellClassMask_3", 0x4), ("SpellClassMask_3", 0x8),
    ("SpellClassMask_3", 0x10000000), ("SpellClassMask_3", 0x20000000), ("SpellClassMask_3", 0x40000000),  # d2 b28-b30
)


def _row(spell_id=204500, **cols) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 4, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0}
    row.update(cols)
    return row


def _check(row, name="Test Spell", procs=None, rules=RULES):
    return lint.check_family_bit_rules([{"name": name}], [row], procs, None, frozenset(), rules=rules)


def _proc(family, d0=0, d1=0, d2=0, spell_id=12797) -> dict:
    return {"SpellId": spell_id, "SpellFamilyName": family, "SpellFamilyMask0": d0, "SpellFamilyMask1": d1,
            "SpellFamilyMask2": d2}


def _load_masks():
    """`_masks.py` the way the class loader would reach it (by path: the leading underscore keeps it out of the
    package scan, and `source/classes/warrior/` is not an importable package on sys.path)."""
    spec = importlib.util.spec_from_file_location("warrior_masks_under_test", MASKS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WarriorFamilyRulesTest(unittest.TestCase):
    def test_the_row_is_registered_with_the_other_classes(self):
        rules = lint.WARRIOR_FAMILY_RULES
        for other in (lint.HUNTER_FAMILY_RULES, lint.SHAMAN_FAMILY_RULES, lint.DEATHKNIGHT_FAMILY_RULES,
                      lint.ROGUE_FAMILY_RULES):
            self.assertIn(other, lint.FAMILY_BIT_RULES)
        self.assertIn(rules, lint.FAMILY_BIT_RULES)
        self.assertEqual(len(lint.FAMILY_BIT_RULES), 5)
        self.assertEqual(rules.name, "warrior")
        self.assertEqual(rules.spell_class_set, 4)
        # the rules that need a role (protected / pet) stay silent
        self.assertEqual(rules.protected_bits, (0, 0, 0))
        self.assertEqual(rules.pet_required_bits, (0, 0, 0))
        self.assertEqual(rules.pet_group_bits, (0, 0, 0))

    def test_the_lint_masks_agree_with_the_masks_module(self):
        masks = _load_masks()
        rules = lint.WARRIOR_FAMILY_RULES
        self.assertEqual(rules.forbidden_carrier_bits, (masks.FORBIDDEN_D0, masks.FORBIDDEN_D1, masks.FORBIDDEN_D2))
        self.assertEqual(rules.forbidden_reader_bits, (0, 0, masks.FORBIDDEN_D2))
        # and the table above names exactly the bits of those masks (so a bit added to one place is noticed)
        by_column = {"SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0}
        for column, bit, _cause in BANNED_CARRIERS:
            by_column[column] |= bit
        self.assertEqual(
            tuple(by_column[c] for c in ("SpellClassMask_1", "SpellClassMask_2", "SpellClassMask_3")),
            rules.forbidden_carrier_bits,
        )

    def test_each_banned_carrier_bit_on_a_custom_warrior_spell_warns_once(self):
        for column, bit, cause in BANNED_CARRIERS:
            with self.subTest(column=column, bit=hex(bit)):
                warnings = _check(_row(**{column: bit}))
                self.assertEqual(len(warnings), 1)
                self.assertIn("warrior family-bit rule (b)", warnings[0])
                self.assertIn("spell 204500 (Test Spell)", warnings[0])
                self.assertIn(cause, warnings[0])

    def test_a_banned_bit_among_allowed_ones_still_warns(self):
        # 0x80 | 0x400 (Thunder Clap's bit and Revenge's) are allowed; the b17 next to them is not
        self.assertEqual(len(_check(_row(SpellClassMask_1=0x80 | 0x400 | 0x20000))), 1)
        self.assertEqual(len(_check(_row(SpellClassMask_3=0x8 | 0x80000000))), 1)

    def test_the_message_names_each_cause(self):
        message = _check(_row(SpellClassMask_1=0x1))[0]
        for fragment in ("d0 b0 Charge", "Improved Charge", "Glyph of Charge", "Juggernaut", "d0 b1 / b24",
                         "d0 b17 / d1 b5", "d1 b6 Devastate", "d2 b31"):
            self.assertIn(fragment, message)

    def test_the_same_numbers_in_a_dword_that_does_not_ban_them_are_silent(self):
        # 0x20 / 0x40 are banned in d1 only (d0 b5 / b6 are plain), 0x20000 / 0x1000000 / 0x1 / 0x2 in d0 only, and
        # 0x80000000 in d2 only (d0 b31 and d1 b31 are free)
        for column, bit in (("SpellClassMask_1", 0x20), ("SpellClassMask_1", 0x40), ("SpellClassMask_1", 0x80000000),
                            ("SpellClassMask_2", 0x1), ("SpellClassMask_2", 0x2), ("SpellClassMask_2", 0x20000),
                            ("SpellClassMask_2", 0x1000000), ("SpellClassMask_2", 0x80000000),
                            ("SpellClassMask_3", 0x20), ("SpellClassMask_3", 0x40), ("SpellClassMask_3", 0x20000),
                            ("SpellClassMask_3", 0x1000000)):
            with self.subTest(column=column, bit=hex(bit)):
                self.assertEqual(_check(_row(**{column: bit})), [])

    def test_allowed_bits_are_silent(self):
        for column, bit in ALLOWED:
            with self.subTest(column=column, bit=hex(bit)):
                self.assertEqual(_check(_row(**{column: bit})), [])
        self.assertEqual(_check(_row()), [])

    def test_a_stock_warrior_id_is_never_judged(self):
        # Gift of the Naaru 28880 carries d2 b31 and Charge 100 carries d0 b0: stock ids are exempt
        self.assertEqual(_check(_row(28880, SpellClassMask_3=0x80000000)), [])
        self.assertEqual(_check(_row(100, SpellClassMask_1=0x1)), [])
        self.assertEqual(_check(_row(199999, SpellClassMask_1=0x1)), [])
        self.assertEqual(len(_check(_row(200000, SpellClassMask_1=0x1))), 1)

    def test_another_classs_custom_spell_is_not_judged(self):
        for family in (0, 3, 8, 9, 15):
            self.assertEqual(
                _check(_row(SpellClassSet=family, SpellClassMask_1=0x1, SpellClassMask_3=0x80000000)), [], family,
            )

    def test_a_d2_b31_reader_on_an_effect_mask_warns(self):
        for letter in "ABC":
            with self.subTest(effect=letter):
                warnings = _check(_row(**{f"EffectSpellClassMask{letter}_3": 0x80000000}))
                self.assertEqual(len(warnings), 1)
                self.assertIn("warrior family-bit rule (c)", warnings[0])
                self.assertIn("Gift of the Naaru", warnings[0])
        # the other d2 bits (the new allocation) and the other dwords are readable
        self.assertEqual(_check(_row(EffectSpellClassMaskA_3=0x1 | 0x2 | 0x4 | 0x8)), [])
        self.assertEqual(_check(_row(EffectSpellClassMaskA_1=0x80000000, EffectSpellClassMaskA_2=0x80000000)), [])

    def test_a_d2_b31_reader_in_a_spell_proc_row_warns_for_family_4_and_family_0(self):
        for family in (4, 0):
            with self.subTest(family=family):
                warnings = _check(_row(), procs=[_proc(family, d2=0x80000000)])
                self.assertEqual(len(warnings), 1)
                self.assertIn("spell_proc 12797: warrior family-bit rule (c)", warnings[0])
        # another family's proc row is not ours to judge
        self.assertEqual(_check(_row(), procs=[_proc(8, d2=0x80000000)]), [])

    def test_a_stock_family_4_reader_is_silent(self):
        # Improved Revenge 12797 reads d0 b10 (0x400); the Thunderstruck-style reader d0 b7 likewise
        self.assertEqual(_check(_row(), procs=[_proc(4, d0=0x400), _proc(4, d0=0x80, spell_id=200052)]), [])
        self.assertEqual(_check(_row(EffectSpellClassMaskA_1=0x400, EffectSpellClassMaskB_1=0x80)), [])

    def test_the_rule_runs_in_the_default_rule_set(self):
        # generate.py calls check_family_bit_rules with no `rules=`: --check (generate.py:596) and the full run
        # (:966, over the same declared population) both get the warrior row
        warnings = lint.check_family_bit_rules([{"name": "X"}], [_row(SpellClassMask_1=0x1)])
        self.assertEqual(len(warnings), 1)
        self.assertIn("warrior family-bit rule (b)", warnings[0])
        warnings = lint.check_family_bit_rules([{"name": "X"}], [_row(SpellClassMask_3=0x80000000)])
        self.assertEqual(len(warnings), 1)  # d2 b31 as a carrier: only the warrior row is in family 4


class _WarriorSpells:
    """The warrior package as the generator builds it (the September Protection build plus the P0 spike): the real
    class-package loader, the real row builder (test_rogue_family_rules._SpikeSpells is the rogue's twin)."""

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
            CLASS_DIR, ids_cfg=ids, trainer_index=test_id_blocks._AnyTrainer(),
            existing_group_ids=test_id_blocks._AnySet(), shapeshift_index={},
            existing_creature_rows=test_id_blocks._AnyRows(), creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.dsl_live_data(
                stock_talents, spell_tables.load_live_item_template_rows,
                lambda: state.load_existing_rows(dbcfmt.SKILLLINEABILITY),
                lambda: state.load_stock_rows(dbcfmt.CHRCLASSES),
                lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
            ),
        )
        reuse = ReuseContext(stock, ids)
        entries = list(reg.spells)
        return reg, entries, [build.build_spell_row(e, reuse) for e in entries]


class WarriorFamilyRulesOnTheRealPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg, cls.entries, cls.rows = _WarriorSpells.load()
        cls.judged = [r for r in cls.rows if int(r["ID"]) >= 200000 and int(r["SpellClassSet"]) == 4]

    def _warnings(self, rows):
        return lint.check_family_bit_rules(self.entries, rows, self.reg.spell_procs, [], frozenset(), rules=RULES)

    def test_the_package_was_loaded_and_the_check_is_not_vacuous(self):
        # the 37 September Protection spells are warrior family; with the spike (31 more) there are 68 judged rows
        self.assertGreaterEqual(len(self.judged), 30)
        self.assertTrue(all(int(r["SpellClassSet"]) == 4 for r in self.judged))

    @unittest.skipUnless(SPIKE_FILE.is_file(), "the P0 spike file is deleted at W0a start")
    def test_the_spike_adds_to_the_judged_rows(self):
        self.assertGreaterEqual(len(self.judged), 60)
        self.assertTrue(any(204869 <= int(r["ID"]) <= 204899 for r in self.judged))

    def test_the_real_package_is_silent(self):
        self.assertEqual(self._warnings(self.rows), [])
        # and in the default rule set, the way generate.py calls it
        self.assertEqual(
            lint.check_family_bit_rules(self.entries, self.rows, self.reg.spell_procs, [], frozenset()), [],
        )

    def test_no_loaded_custom_row_carries_a_banned_bit(self):
        banned = lint.WARRIOR_FAMILY_RULES.forbidden_carrier_bits
        for row in self.judged:
            for n, bits in zip((1, 2, 3), banned):
                self.assertEqual(int(row[f"SpellClassMask_{n}"]) & bits, 0, (row["ID"], n))

    def test_the_same_rows_with_one_banned_bit_added_do_warn(self):
        # positive control: poison one loaded row and exactly that row is reported
        rows = [dict(r) for r in self.rows]
        victim = next(r for r in rows if int(r["ID"]) >= 200000 and int(r["SpellClassSet"]) == 4)
        victim["SpellClassMask_1"] = int(victim["SpellClassMask_1"]) | 0x1
        warnings = self._warnings(rows)
        self.assertEqual(len(warnings), 1)
        self.assertIn(f"spell {victim['ID']} ", warnings[0])
        self.assertIn("rule (b)", warnings[0])


class MasksModuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.masks = _load_masks()

    def test_the_four_allocated_bits_are_distinct_single_d2_bits_below_b8(self):
        bits = [self.masks.HEROIC_LEAP, self.masks.COLOSSUS_SMASH, self.masks.RAMPAGE,
                self.masks.DAMAGING_ABILITY_GROUP]
        self.assertEqual(bits, [0x1, 0x2, 0x4, 0x8])  # FAMILY-BITS s5: d2 b0, b1, b2, b3
        for bit in bits:
            self.assertEqual(bit & (bit - 1), 0, hex(bit))  # one bit
            self.assertLess(bit, 0x100, hex(bit))  # b4-b7 stay reserved, b8+ spare
        self.assertEqual(len(set(bits)), 4)

    def test_no_allocated_bit_overlaps_a_forbidden_mask(self):
        for name in ("HEROIC_LEAP", "COLOSSUS_SMASH", "RAMPAGE", "DAMAGING_ABILITY_GROUP"):
            self.assertEqual(getattr(self.masks, name) & self.masks.FORBIDDEN_D2, 0, name)
        self.assertEqual(self.masks.FORBIDDEN_D2, 0x80000000)  # never d2 b31

    def test_the_forbidden_masks_are_the_family_bits_section_3_3_bits(self):
        self.assertEqual(self.masks.FORBIDDEN_D0, 0x01020003)   # d0 b0, b1, b17, b24
        self.assertEqual(self.masks.FORBIDDEN_D1, 0x60)         # d1 b5, b6

    def test_no_stock_family_4_row_carries_an_allocated_d2_bit(self):
        # the claim behind "all new bits go in d2" (FAMILY-BITS s3.1): the only stock family-4 d2 carrier is Gift of the
        # Naaru 28880 on b31. Read from the stock client Spell.dbc.
        fam4 = [r for r in state.load_stock_rows(dbcfmt.SPELL).values() if int(r["SpellClassSet"]) == 4]
        self.assertGreater(len(fam4), 500)  # not vacuous: the stock warrior family was read
        self.assertEqual([(int(r["ID"]), int(r["SpellClassMask_3"])) for r in fam4 if int(r["SpellClassMask_3"])],
                         [(28880, 0x80000000)])


if __name__ == "__main__":
    unittest.main()
