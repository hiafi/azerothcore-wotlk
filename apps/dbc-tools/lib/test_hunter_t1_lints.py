"""
Lints added by hunter-rework T1: check_talent_tab_refs (SHARED §C7.10), check_item_dbc_consistency and
check_ranged_ammo_type (§C7.3), check_hunter_family_rules (§C7.6). One positive and one negative case per rule
branch. Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_hunter_t1_lints.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import lint  # noqa: E402


class TalentTabRefsTest(unittest.TestCase):
    TABS = [{"ID": 361}, {"ID": 60800}]

    def test_row_on_the_declared_holding_tab_passes(self):
        self.assertEqual(lint.check_talent_tab_refs([{"ID": 2110, "TabID": 60800}, {"ID": 1, "TabID": 361}], self.TABS), [])

    def test_row_on_tab_zero_is_an_error(self):
        errors = lint.check_talent_tab_refs([{"ID": 2110, "TabID": 0}], self.TABS)
        self.assertEqual(len(errors), 1)
        self.assertIn("TabID 0", errors[0])
        self.assertIn("2110", errors[0])

    def test_row_on_an_undeclared_tab_is_an_error(self):
        errors = lint.check_talent_tab_refs([{"ID": 2110, "TabID": 60801}], self.TABS)
        self.assertIn("TabID 60801", errors[0])

    def test_holding_tab_not_declared_is_the_usual_failure(self):
        errors = lint.check_talent_tab_refs([{"ID": 2110, "TabID": 60800}], [{"ID": 361}])
        self.assertIn("TabID 60800", errors[0])
        self.assertIn("hunter_retired_tab.py", errors[0])

    def test_long_lists_are_truncated(self):
        errors = lint.check_talent_tab_refs([{"ID": i, "TabID": 7} for i in range(30)], self.TABS)
        self.assertEqual(len(errors), 1)
        self.assertIn("30 in all", errors[0])


class ItemDbcConsistencyTest(unittest.TestCase):
    def _template(self, **kw):
        return {"entry": 2101, "name": "Light Quiver", "class": 1, "subclass": 0, **kw}

    def test_matching_class_and_subclass_is_silent(self):
        self.assertEqual(
            lint.check_item_dbc_consistency([self._template()], {2101: {"ClassID": 1, "SubclassID": 0}}), [],
        )

    def test_class_mismatch_warns(self):
        warnings = lint.check_item_dbc_consistency([self._template()], {2101: {"ClassID": 11, "SubclassID": 2}})
        self.assertEqual(len(warnings), 1)
        self.assertIn("1/0", warnings[0])
        self.assertIn("11/2", warnings[0])
        self.assertIn("EnforceItemAttributes", warnings[0])

    def test_subclass_only_mismatch_warns(self):
        self.assertEqual(
            len(lint.check_item_dbc_consistency([self._template()], {2101: {"ClassID": 1, "SubclassID": 2}})), 1,
        )

    def test_item_without_an_item_dbc_row_is_not_judged(self):
        self.assertEqual(lint.check_item_dbc_consistency([self._template()], {}), [])


class RangedAmmoTypeTest(unittest.TestCase):
    def _bow(self, entry=18323, **kw):
        return {"entry": entry, "name": "Satyr's Bow", "class": 2, "subclass": 2, "ammo_type": 0, **kw}

    def test_declared_bow_with_no_ammo_is_silent(self):
        self.assertEqual(lint.check_ranged_ammo_type([self._bow()], [], {}), [])

    def test_declared_ranged_weapon_still_needing_ammo_warns(self):
        for subclass in (2, 3, 18):
            warnings = lint.check_ranged_ammo_type([self._bow(subclass=subclass, ammo_type=2)], [], {})
            self.assertEqual(len(warnings), 1, subclass)
            self.assertIn("ammo_type 2", warnings[0])

    def test_declared_non_ranged_weapon_is_not_judged(self):
        sword = self._bow(subclass=7, ammo_type=2)   # a one-handed sword; the column means nothing there
        thrown = self._bow(entry=2, subclass=16, ammo_type=3)
        self.assertEqual(lint.check_ranged_ammo_type([sword, thrown], [], {}), [])

    def test_custom_items_csv_ranged_weapon_with_live_ammo_type_warns(self):
        entry = {"id": 70200, "class_id": 2, "subclass_id": 3}
        live = {70200: {"entry": 70200, "name": "Test Gun", "ammo_type": 3}}
        warnings = lint.check_ranged_ammo_type([], [entry], live)
        self.assertEqual(len(warnings), 1)
        self.assertIn("70200", warnings[0])

    def test_custom_items_csv_ranged_weapon_with_no_ammo_is_silent(self):
        entry = {"id": 70200, "class_id": 2, "subclass_id": 3}
        self.assertEqual(lint.check_ranged_ammo_type([], [entry], {70200: {"name": "G", "ammo_type": 0}}), [])

    def test_custom_row_uses_its_declaration_over_the_live_row(self):
        entry = {"id": 70200, "class_id": 2, "subclass_id": 18}
        declared = {"entry": 70200, "name": "Test Crossbow", "class": 2, "subclass": 18, "ammo_type": 0}
        live = {70200: {"name": "Test Crossbow", "ammo_type": 2}}
        self.assertEqual(lint.check_ranged_ammo_type([declared], [entry], live), [])

    def test_stock_items_csv_row_is_not_a_custom_weapon(self):
        entry = {"id": 18323, "class_id": 2, "subclass_id": 2}
        self.assertEqual(lint.check_ranged_ammo_type([], [entry], {18323: {"name": "Satyr's Bow", "ammo_type": 2}}), [])

    def test_a_declared_weapon_is_reported_once(self):
        entry = {"id": 70200, "class_id": 2, "subclass_id": 2}
        declared = {"entry": 70200, "name": "B", "class": 2, "subclass": 2, "ammo_type": 2}
        self.assertEqual(len(lint.check_ranged_ammo_type([declared], [entry], {})), 1)

    def test_custom_item_with_no_item_template_row_is_not_judged(self):
        self.assertEqual(lint.check_ranged_ammo_type([], [{"id": 70200, "class_id": 2, "subclass_id": 2}], {}), [])


def _row(spell_id=200100, **kw) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 9, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0}
    row.update(kw)
    return row


def _check(row, name="Test Spell", procs=None, sla=None, lines=frozenset()):
    return lint.check_hunter_family_rules([{"name": name}], [row], procs, sla, lines)


class HunterFamilyRulesTest(unittest.TestCase):
    # (a) aspect bits
    def test_a_non_aspect_with_an_aspect_bit_warns(self):
        for column, value in (("SpellClassMask_1", 0x80000), ("SpellClassMask_2", 0x40000), ("SpellClassMask_3", 0x10)):
            warnings = _check(_row(**{column: value}))
            self.assertEqual(len(warnings), 1, column)
            self.assertIn("rule (a)", warnings[0])

    def test_an_aspect_carries_its_bit(self):
        sla = [{"Spell": 200100, "SkillLine": 163}]
        self.assertEqual(_check(_row(SpellClassMask_1=0x100000), name="Aspect of the Hawk", sla=sla), [])

    def test_a_same_named_triggered_aura_is_not_exempt(self):
        # A helper named like an aspect, with an aspect bit, that no player learns: still a rule (a) hit.
        warnings = _check(_row(SpellClassMask_1=0x100000), name="Aspect of the Dragonhawk")
        self.assertEqual(len(warnings), 1)
        self.assertIn("rule (a)", warnings[0])
        sla = [{"Spell": 200999, "SkillLine": 163}]   # another spell's row does not count
        self.assertEqual(len(_check(_row(SpellClassMask_1=0x100000), name="Aspect of the Dragonhawk", sla=sla)), 1)

    def test_an_explicit_exempt_id_still_works(self):
        rules = (lint.FamilyBitRules(**{**lint.HUNTER_FAMILY_RULES.__dict__, "exempt_ids": frozenset({200100})}),)
        self.assertEqual(
            lint.check_hunter_family_rules([{"name": "Aspect of X"}], [_row(SpellClassMask_1=0x100000)], rules=rules), [],
        )

    def test_a_non_aspect_without_aspect_bits_is_silent(self):
        self.assertEqual(_check(_row(SpellClassMask_1=0x1000, SpellClassMask_3=0x20)), [])

    # (b) d1 b0
    def test_a_carrier_of_d1_b0_warns(self):
        warnings = _check(_row(SpellClassMask_2=0x1))
        self.assertEqual(len(warnings), 1)
        self.assertIn("rule (b)", warnings[0])

    def test_other_d1_bits_are_fine(self):
        self.assertEqual(_check(_row(SpellClassMask_2=0x2)), [])

    # (c) readers
    def test_an_effect_reader_mask_containing_d1_b28_warns(self):
        warnings = _check(_row(EffectSpellClassMaskA_2=0x10000000, EffectSpellClassMaskA_3=0x800000))
        self.assertEqual(len(warnings), 1)
        self.assertIn("rule (c)", warnings[0])
        self.assertIn("effect 1", warnings[0])

    def test_effect_letter_is_the_effect_index(self):
        warnings = _check(_row(EffectSpellClassMaskC_2=0x10000001))
        self.assertIn("effect 3", warnings[0])

    def test_a_reader_on_the_pet_groups_d2_bit_alone_is_silent(self):
        self.assertEqual(_check(_row(EffectSpellClassMaskA_3=0x800000)), [])

    def test_a_spell_proc_family_mask_containing_d1_b28_warns(self):
        proc = {"SpellId": 200101, "SpellFamilyName": 9, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x10000000,
                "SpellFamilyMask2": 0x800000}
        warnings = lint.check_hunter_family_rules([], [], [proc])
        self.assertEqual(len(warnings), 1)
        self.assertIn("rule (c)", warnings[0])

    def test_a_spell_proc_on_the_d2_bit_or_another_family_is_silent(self):
        ok = {"SpellId": 200101, "SpellFamilyName": 9, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0x800000}
        other_family = {"SpellId": 200102, "SpellFamilyName": 5, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x10000000, "SpellFamilyMask2": 0}
        self.assertEqual(lint.check_hunter_family_rules([], [], [ok, other_family]), [])

    def test_a_declared_proc_on_a_stock_id_is_judged_too(self):
        stock = {"SpellId": -34497, "SpellFamilyName": 9, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x10000000, "SpellFamilyMask2": 0}
        self.assertEqual(len(lint.check_hunter_family_rules([], [], [stock])), 1)

    def test_a_family_zero_proc_with_the_pet_bit_warns(self):
        # SpellFamilyName 0 matches the mask against any family's spells.
        proc = {"SpellId": 13165, "SpellFamilyName": 0, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x10000000, "SpellFamilyMask2": 0}
        self.assertEqual(len(lint.check_hunter_family_rules([], [], [proc])), 1)
        empty = {**proc, "SpellFamilyMask1": 0}
        self.assertEqual(lint.check_hunter_family_rules([], [], [empty]), [])

    # (d) inverted: pet-cast spells need the pet bit
    def test_a_pet_group_carrier_without_the_pet_bit_warns(self):
        for bit in (0x400000, 0x800000, 0x1000000):
            warnings = _check(_row(SpellClassMask_3=bit))
            self.assertEqual(len(warnings), 1, hex(bit))
            self.assertIn("rule (d)", warnings[0])

    def test_a_spell_taught_on_a_pet_skill_line_without_the_pet_bit_warns(self):
        sla = [{"Spell": 200100, "SkillLine": 270}]
        self.assertIn("rule (d)", _check(_row(), sla=sla)[0])
        sla = [{"Spell": 200100, "SkillLine": 209}]
        self.assertIn("rule (d)", _check(_row(), sla=sla, lines=frozenset({209}))[0])

    def test_a_spell_taught_on_a_player_line_is_not_pet_cast(self):
        self.assertEqual(_check(_row(), sla=[{"Spell": 200100, "SkillLine": 163}], lines=frozenset({209})), [])

    def test_the_pet_bit_with_a_pet_group_is_silent(self):
        self.assertEqual(_check(_row(SpellClassMask_2=0x10000000, SpellClassMask_3=0x800000)), [])

    def test_a_ranged_pet_spit_with_the_pet_bit_never_warns(self):
        # DmgClass RANGED (DefenseType 3) + d1 b28 + a pet group bit + taught on 270: all intended.
        row = _row(SpellClassMask_2=0x10000000, SpellClassMask_3=0x800000, DefenseType=3, DmgClass=3)
        self.assertEqual(_check(row, name="Venom Spit", sla=[{"Spell": 200100, "SkillLine": 270}]), [])

    # scope
    def test_stock_ids_and_other_families_are_out_of_scope(self):
        self.assertEqual(_check(_row(spell_id=17253, SpellClassMask_2=0x1)), [])
        self.assertEqual(_check(_row(SpellClassSet=5, SpellClassMask_2=0x1)), [])

    def test_a_clean_spell_prints_nothing(self):
        self.assertEqual(_check(_row(SpellClassMask_1=0x2, SpellClassMask_2=0x200, SpellClassMask_3=0x20)), [])


if __name__ == "__main__":
    unittest.main()
