"""
Lints added by shaman-rework T1 (steps 3-8, wired in step 9): check_totem_tools, check_hidden_learned_spells,
check_ground_effect_haste, check_spell_proc_rows, check_trainer_spell_level and the shaman row of the family-bit
rules. One positive and one negative case per branch, then the P0 spike and the whole declared population against
all of them (both must stay silent).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shaman_t1_lints.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, lint, source, spell_tables, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOTEM_COLUMNS = ("Totem_1", "Totem_2", "RequiredTotemCategoryID_1", "RequiredTotemCategoryID_2")


def _row(spell_id=202800, **kw) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 11, "Attributes": 0, "AttributesEx5": 0, "SpellLevel": 1, "ProcTypeMask": 0}
    row.update(kw)
    return row


def _entry(name="Test Spell") -> dict:
    return {"name": name}


def _run(check, row, *args, name="Test Spell", **kw):
    return check([_entry(name)], [row], *args, **kw)


class TotemToolsTest(unittest.TestCase):
    def test_each_tool_column_on_a_custom_shaman_spell_warns(self):
        for column in TOTEM_COLUMNS:
            with self.subTest(column=column):
                warnings = _run(lint.check_totem_tools, _row(**{column: 4}))
                self.assertEqual(len(warnings), 1)
                self.assertIn(f"{column}=4", warnings[0])
                self.assertIn("SPELL_FAILED_TOTEMS", warnings[0])

    def test_a_tool_free_custom_shaman_spell_is_silent(self):
        self.assertEqual(_run(lint.check_totem_tools, _row(**{c: 0 for c in TOTEM_COLUMNS})), [])
        self.assertEqual(_run(lint.check_totem_tools, _row()), [])  # columns absent

    def test_the_spike_shape_builds_with_all_four_columns_zero_and_is_silent(self):
        self.assertEqual(_run(lint.check_totem_tools, _row(202761, **{c: 0 for c in TOTEM_COLUMNS})), [])

    def test_another_class_set_is_out_of_scope(self):
        self.assertEqual(_run(lint.check_totem_tools, _row(SpellClassSet=7, RequiredTotemCategoryID_1=2)), [])

    def test_stock_shaman_spells_stay_quiet_by_default(self):
        self.assertEqual(lint.TOOL_FREE_CLASS_SETS, frozenset())
        self.assertEqual(_run(lint.check_totem_tools, _row(2484, RequiredTotemCategoryID_1=2)), [])

    def test_the_opt_in_widens_the_check_to_stock_spells_of_that_set(self):
        stock = _row(2484, RequiredTotemCategoryID_1=2)
        warnings = _run(lint.check_totem_tools, stock, {11})
        self.assertEqual(len(warnings), 1)
        self.assertIn("spell 2484", warnings[0])
        other_class = _row(2484, SpellClassSet=7, RequiredTotemCategoryID_1=2)
        self.assertEqual(_run(lint.check_totem_tools, other_class, {11}), [])

    def test_the_module_constant_is_the_opt_in(self):
        original = lint.TOOL_FREE_CLASS_SETS
        lint.TOOL_FREE_CLASS_SETS = frozenset({11})
        try:
            self.assertEqual(len(_run(lint.check_totem_tools, _row(2484, RequiredTotemCategoryID_1=2))), 1)
        finally:
            lint.TOOL_FREE_CLASS_SETS = original
        self.assertEqual(_run(lint.check_totem_tools, _row(2484, RequiredTotemCategoryID_1=2)), [])

    def test_the_opt_in_covers_undeclared_stock_spells_of_the_set(self):
        stock = {
            6365: _row(6365, Name_Lang_enUS="Searing Totem", RequiredTotemCategoryID_1=4),   # undeclared rank
            2484: _row(2484, Name_Lang_enUS="Earthbind Totem", RequiredTotemCategoryID_1=2),  # declared below
            100: _row(100, SpellClassSet=7, RequiredTotemCategoryID_1=2),                    # another class
            101: _row(101, Name_Lang_enUS="Clean Shaman Spell"),                              # no tool column
        }
        declared = [_row(2484, RequiredTotemCategoryID_1=2)]
        warnings = lint.check_totem_tools([_entry()], declared, {11}, stock)
        self.assertEqual(len(warnings), 2)  # 2484 (declared) once, 6365 (undeclared) once
        undeclared = [w for w in warnings if "undeclared stock" in w]
        self.assertEqual(len(undeclared), 1)
        self.assertIn("spell 6365 (Searing Totem)", undeclared[0])

    def test_undeclared_stock_spells_stay_quiet_without_the_opt_in(self):
        stock = {6365: _row(6365, RequiredTotemCategoryID_1=4)}
        self.assertEqual(lint.check_totem_tools([], [], None, stock), [])
        self.assertEqual(lint.check_totem_tools([], [], frozenset(), stock), [])

    def test_the_opt_in_also_covers_a_stripped_stock_spell_staying_quiet(self):
        self.assertEqual(_run(lint.check_totem_tools, _row(2484), {11}), [])


class HiddenLearnedSpellsTest(unittest.TestCase):
    HIDDEN = 0x80
    PASSIVE = 0x40
    SLA = [{"Spell": 202800, "SkillLine": 375}]

    def test_a_trained_hidden_spell_warns(self):
        warnings = _run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), [], {202800})
        self.assertEqual(len(warnings), 1)
        self.assertIn("DO_NOT_DISPLAY", warnings[0])
        self.assertIn("trained_by()", warnings[0])

    def test_a_hidden_spell_with_a_player_skill_line_row_warns(self):
        warnings = _run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), self.SLA)
        self.assertEqual(len(warnings), 1)
        self.assertIn("skill line 375", warnings[0])

    def test_a_hidden_talent_rank_warns(self):
        warnings = _run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), [], frozenset(), {202800})
        self.assertEqual(len(warnings), 1)
        self.assertIn("talent rank", warnings[0])

    def test_a_hidden_passive_talent_aura_is_silent(self):
        row = _row(Attributes=self.HIDDEN | self.PASSIVE)
        self.assertEqual(_run(lint.check_hidden_learned_spells, row, self.SLA, {202800}, {202800}), [])

    def test_a_hidden_script_cast_helper_nobody_learns_is_silent(self):
        self.assertEqual(_run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), []), [])
        other = [{"Spell": 202999, "SkillLine": 375}]  # another spell's row does not count
        self.assertEqual(_run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), other, {1}, {2}), [])

    def test_a_pet_line_row_is_silent(self):
        for line in (270, 209):
            with self.subTest(line=line):
                row = [{"Spell": 202800, "SkillLine": line}]
                self.assertEqual(
                    _run(lint.check_hidden_learned_spells, _row(Attributes=self.HIDDEN), row, frozenset(), frozenset(),
                         frozenset({209})),
                    [],
                )

    def test_a_visible_learned_spell_is_silent(self):
        self.assertEqual(_run(lint.check_hidden_learned_spells, _row(Attributes=0), self.SLA, {202800}), [])

    def test_stock_ids_are_out_of_scope(self):
        self.assertEqual(_run(lint.check_hidden_learned_spells, _row(2484, Attributes=self.HIDDEN), [], {2484}), [])

    def test_the_allow_set_exempts_a_listed_spell(self):
        row = _row(Attributes=self.HIDDEN)
        self.assertEqual(_run(lint.check_hidden_learned_spells, row, self.SLA, allow={202800}), [])
        self.assertEqual(len(_run(lint.check_hidden_learned_spells, row, self.SLA, allow=frozenset())), 1)

    def test_a_pure_learn_spell_carrier_is_silent(self):
        # The stock 59672 talent-rank carrier shape: every effect is LEARN_SPELL (36), hidden on purpose.
        carrier = _row(200863, Attributes=0x800080, Effect_1=36, EffectTriggerSpell_1=200835, Effect_2=36,
                       EffectTriggerSpell_2=50589)
        self.assertEqual(_run(lint.check_hidden_learned_spells, carrier, [], frozenset(), {200863}), [])
        impure = _row(200863, Attributes=0x800080, Effect_1=36, EffectTriggerSpell_1=200835, Effect_2=6)
        self.assertEqual(len(_run(lint.check_hidden_learned_spells, impure, [], frozenset(), {200863})), 1)

    def test_a_hidden_spell_learned_through_a_learn_spell_effect_warns(self):
        carrier = _row(200863, Attributes=0, Effect_1=36, EffectTriggerSpell_1=200835)
        hidden = _row(200835, Attributes=self.HIDDEN)
        warnings = lint.check_hidden_learned_spells(
            [_entry("Carrier"), _entry("Hidden form")], [carrier, hidden], [], frozenset(), {200863},
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn("LEARN_SPELL from spell 200863", warnings[0])

    def test_the_learn_spell_chain_is_followed_transitively(self):
        first = _row(200863, Effect_1=36, EffectTriggerSpell_1=200864)
        nested = _row(200864, Attributes=self.HIDDEN | 0x800000, Effect_1=36, EffectTriggerSpell_1=200865)
        leaf = _row(200865, Attributes=self.HIDDEN, Effect_1=6)
        warnings = lint.check_hidden_learned_spells(
            [_entry("A"), _entry("B"), _entry("C")], [first, nested, leaf], [], frozenset(), {200863},
        )
        self.assertEqual(len(warnings), 1)  # the nested carrier is silent, the leaf warns
        self.assertIn("spell 200865", warnings[0])

    def test_the_learn_spell_target_of_an_unlearned_spell_is_not_learned(self):
        carrier = _row(200863, Effect_1=36, EffectTriggerSpell_1=200835)
        hidden = _row(200835, Attributes=self.HIDDEN)
        warnings = lint.check_hidden_learned_spells(
            [_entry("A"), _entry("B")], [carrier, hidden], [], frozenset(), frozenset(),
        )
        self.assertEqual(warnings, [])


def _ground(effects, **kw) -> dict:
    """A row with the given [(Effect, EffectAura), ...]."""
    row = _row(**kw)
    for i, (effect, aura) in enumerate(effects, start=1):
        row[f"Effect_{i}"] = effect
        row[f"EffectAura_{i}"] = aura
    return row


class GroundEffectHasteTest(unittest.TestCase):
    PAA = 27

    def test_the_haste_affects_periodic_attribute_warns(self):
        row = _ground([(self.PAA, 4), (6, 226)], AttributesEx5=0x2000)
        warnings = _run(lint.check_ground_effect_haste, row)
        self.assertEqual(len(warnings), 1)
        self.assertIn("SPELL_HASTE_AFFECTS_PERIODIC", warnings[0])
        self.assertIn("PERIODIC_DUMMY", warnings[0])  # the message names the trigger shape

    def test_each_periodic_damage_or_heal_aura_warns(self):
        for aura in (3, 8, 20, 53, 89):
            with self.subTest(aura=aura):
                warnings = _run(lint.check_ground_effect_haste, _ground([(self.PAA, aura)]))
                self.assertEqual(len(warnings), 1)
                self.assertIn(f"[{aura}]", warnings[0])

    def test_the_aura_may_sit_on_another_effect_of_the_spell(self):
        self.assertEqual(len(_run(lint.check_ground_effect_haste, _ground([(self.PAA, 4), (6, 3)]))), 1)

    def test_the_trigger_shape_is_silent(self):
        # persistent area aura (dummy) + PERIODIC_DUMMY on the caster, no 0x2000: the Healing Rain / Earthquake shape
        dummy = _ground([(self.PAA, 4), (6, 226)], AttributesEx5=0x8000000)
        self.assertEqual(_run(lint.check_ground_effect_haste, dummy), [])
        self.assertEqual(_run(lint.check_ground_effect_haste, _ground([(self.PAA, 4), (6, 23)])), [])  # TRIGGER_SPELL

    def test_a_hasted_dot_that_is_not_a_ground_effect_is_silent(self):
        self.assertEqual(_run(lint.check_ground_effect_haste, _ground([(6, 3)], AttributesEx5=0x2000)), [])

    def test_a_stray_aura_id_on_a_non_aura_effect_does_not_count(self):
        self.assertEqual(_run(lint.check_ground_effect_haste, _ground([(self.PAA, 4), (2, 3)])), [])

    def test_stock_ids_are_out_of_scope(self):
        rain_of_fire = _ground([(self.PAA, 3)], spell_id=5740, AttributesEx5=0x2000)
        self.assertEqual(_run(lint.check_ground_effect_haste, rain_of_fire), [])

    def test_the_cores_fixed_cadence_ids_are_exempt(self):
        # Echo of Light heal / damage (IsFixedCadencePeriodic): the core never hastes their ticks.
        for spell_id in (200218, 200219):
            with self.subTest(spell_id=spell_id):
                row = _ground([(self.PAA, 3)], spell_id=spell_id, AttributesEx5=0x2000)
                self.assertEqual(_run(lint.check_ground_effect_haste, row), [])
        self.assertEqual(lint.FIXED_CADENCE_PERIODIC_SPELLS, frozenset({200218, 200219}))

    def test_the_allow_set_exempts_an_existing_ground_effect(self):
        row = _ground([(self.PAA, 3)], spell_id=200096)
        self.assertEqual(_run(lint.check_ground_effect_haste, row), [])
        self.assertEqual(len(_run(lint.check_ground_effect_haste, row, allow=frozenset())), 1)

    def test_the_p0_ground_spells_are_silent(self):
        # 202775: PERSISTENT_AREA_AURA dummy + PERIODIC_DUMMY, Ex5 0x08000000 (NO_CASTER_AURA_ICON), no 0x2000.
        healing_rain = _ground([(self.PAA, 4), (6, 226)], spell_id=202775, AttributesEx5=0x08000000)
        self.assertEqual(_run(lint.check_ground_effect_haste, healing_rain), [])


class SpellProcRowsTest(unittest.TestCase):
    MELEE_SPELL = 0x10  # PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS: in REQ_SPELL_PHASE_PROC_FLAG_MASK
    MELEE_AUTO = 0x4    # PROC_FLAG_DONE_MELEE_AUTO_ATTACK: in DONE_HIT but not SPELL_PROC_FLAG_MASK
    TAKEN_MELEE = 0x8

    def _proc(self, spell_id=202766, flags=0x10, phase=0):
        return {"SpellId": spell_id, "ProcFlags": flags, "SpellPhaseMask": phase}

    def _check(self, proc, rows=None, **kw):
        if rows is None:
            rows = {abs(proc["SpellId"]): _row(abs(proc["SpellId"]))}
        return lint.check_spell_proc_rows([proc], rows, **kw)

    SPELLMGR_H = TOOL_ROOT.parents[1] / "src" / "server" / "game" / "Spells" / "SpellMgr.h"

    @unittest.skipUnless(SPELLMGR_H.is_file(), "needs src/server/game/Spells/SpellMgr.h")
    def test_the_mask_constants_match_spellmgr_h(self):
        # Parse the enum out of the header instead of restating the values: the masks are expressions of PROC_FLAG_*.
        import re

        text = re.sub(r"//[^\n]*", "", self.SPELLMGR_H.read_text(encoding="utf-8"))
        values: dict[str, int] = {}
        for name, expression in re.findall(r"\b([A-Z_]*PROC_FLAG[A-Z_]*)\s*=\s*([^,]+?),", text):
            expression = " ".join(expression.split())
            try:
                values[name] = eval(expression, {"__builtins__": {}}, values)  # noqa: S307 - the repo's own header
            except NameError:
                continue
        for name, ours in (
            ("SPELL_PROC_FLAG_MASK", lint.SPELL_PROC_FLAG_MASK),
            ("DONE_HIT_PROC_FLAG_MASK", lint.DONE_HIT_PROC_FLAG_MASK),
            ("REQ_SPELL_PHASE_PROC_FLAG_MASK", lint.REQ_SPELL_PHASE_PROC_FLAG_MASK),
        ):
            with self.subTest(mask=name):
                self.assertEqual(ours, values[name], f"{name}: lint 0x{ours:X} header 0x{values[name]:X}")

    def test_the_masks_classify_the_example_flags(self):
        self.assertTrue(lint.REQ_SPELL_PHASE_PROC_FLAG_MASK & self.MELEE_SPELL)
        self.assertFalse(lint.REQ_SPELL_PHASE_PROC_FLAG_MASK & self.MELEE_AUTO)
        self.assertFalse(lint.REQ_SPELL_PHASE_PROC_FLAG_MASK & self.TAKEN_MELEE)

    def test_a_melee_spell_row_without_a_phase_warns(self):
        warnings = self._check(self._proc(flags=self.MELEE_SPELL, phase=0))
        self.assertEqual(len(warnings), 1)
        self.assertIn("SpellPhaseMask is 0", warnings[0])

    def test_the_same_row_with_phase_2_is_silent(self):
        self.assertEqual(self._check(self._proc(flags=self.MELEE_SPELL, phase=2)), [])

    def test_a_melee_auto_attack_row_needs_no_phase(self):
        self.assertEqual(self._check(self._proc(flags=self.MELEE_AUTO, phase=0)), [])

    def test_zero_flags_with_no_dbc_flags_warns(self):
        warnings = self._check(self._proc(flags=0))
        self.assertEqual(len(warnings), 1)
        self.assertIn("ProcFlags", warnings[0])

    def test_a_row_inheriting_dbc_flags_is_judged_on_them(self):
        rows = {202766: _row(202766, ProcTypeMask=0x14)}
        self.assertEqual(self._check(self._proc(flags=0, phase=2), rows), [])
        warnings = self._check(self._proc(flags=0, phase=0), rows)
        self.assertEqual(len(warnings), 1)
        self.assertIn("inherited from the spell's DBC ProcTypeMask", warnings[0])

    def test_a_phase_with_flags_outside_the_mask_warns(self):
        warnings = self._check(self._proc(flags=self.TAKEN_MELEE, phase=2))
        self.assertEqual(len(warnings), 1)
        self.assertIn("won't be used", warnings[0])
        self.assertEqual(len(self._check(self._proc(flags=self.MELEE_AUTO, phase=1))), 1)

    def test_a_taken_row_without_a_phase_is_silent(self):
        self.assertEqual(self._check(self._proc(flags=self.TAKEN_MELEE, phase=0)), [])

    def test_a_rank_chain_row_is_judged_on_its_base_spell(self):
        rows = {17106: _row(17106, ProcTypeMask=0x4)}
        self.assertEqual(self._check(self._proc(spell_id=-17106, flags=0, phase=0), rows), [])

    def test_zero_flags_on_an_unknown_spell_is_not_judged(self):
        self.assertEqual(self._check(self._proc(flags=0), {}), [])

    def test_the_allow_set_exempts_a_listed_row(self):
        self.assertEqual(self._check(self._proc(spell_id=33150, flags=0x14000, phase=0), {}, allow={33150: "why"}), [])
        self.assertEqual(self._check(self._proc(spell_id=-30299, flags=0x2A8, phase=2), {}, allow={-30299: "why"}), [])

    def test_spike_procs_are_silent(self):
        # 202766 Flametongue: melee-spell | melee auto with phase 2 (HIT); 202770 inherits 0x14000 from the DBC with
        # phase 1; 202771 is auto-attack only (ProcFlags 4) with no phase.
        procs = [
            {"SpellId": 202766, "ProcFlags": 0x14, "SpellPhaseMask": 2},
            {"SpellId": 202770, "ProcFlags": 0, "SpellPhaseMask": 1},
            {"SpellId": 202771, "ProcFlags": 4, "SpellPhaseMask": 0},
        ]
        rows = {202770: _row(202770, ProcTypeMask=0x14000), 202771: _row(202771, ProcTypeMask=4), 202766: _row(202766)}
        self.assertEqual(lint.check_spell_proc_rows(procs, rows), [])


class ShadowedSpellProcTest(unittest.TestCase):
    def _chains(self):
        return {spell: [1, 2, 3, 4, 5] for spell in (1, 2, 3, 4, 5)}

    def _proc(self, spell_id):
        return {"SpellId": spell_id, "ProcFlags": 4}

    def _check(self, declared, live=(), removed=frozenset(), **kw):
        return lint.check_shadowed_spell_procs(
            [self._proc(i) for i in declared], [self._proc(i) for i in live], set(removed), self._chains(),
            allow={}, **kw,
        )

    def test_a_per_rank_row_under_a_live_chain_row_warns(self):
        warnings = self._check([3], live=[-1])
        self.assertEqual(len(warnings), 1)
        self.assertIn("spell_proc 3: shadowed by the rank-chain row -1", warnings[0])
        self.assertIn("duplicate", warnings[0])

    def test_the_first_rank_row_is_shadowed_too(self):
        self.assertEqual(len(self._check([1], live=[-1])), 1)

    def test_a_declared_negative_row_shadows_a_declared_positive_one(self):
        self.assertEqual(len(self._check([-1, 4])), 1)

    def test_a_removed_chain_row_does_not_shadow(self):
        self.assertEqual(self._check([3], live=[-1], removed={-1}), [])

    def test_redeclaring_the_chain_row_still_shadows(self):
        self.assertEqual(len(self._check([-1, 3], live=[-1])), 1)

    def test_a_row_of_another_chain_or_a_standalone_spell_is_silent(self):
        self.assertEqual(self._check([77], live=[-1]), [])
        self.assertEqual(self._check([3], live=[-9]), [])
        self.assertEqual(self._check([3], live=[]), [])

    def test_a_declared_negative_row_alone_is_silent(self):
        self.assertEqual(self._check([-1]), [])

    def test_the_stock_chain_row_removed_in_the_same_run_fixes_it(self):
        # remove_spell_proc(-1) in the same output: the chain row leaves the final set
        self.assertEqual(self._check([3, 4], live=[-1], removed={-1}), [])

    def test_the_allow_set_is_the_priest_rows_with_a_reason(self):
        self.assertEqual(
            set(lint.SHADOWED_PROC_ALLOW),
            {27816, 33150, 33154, 34753, 34859, 34860, 63730, 63733, 63737, 64127, 64129, 200163},
        )
        self.assertTrue(all("priest rework" in why for why in lint.SHADOWED_PROC_ALLOW.values()))
        self.assertEqual(lint.check_shadowed_spell_procs([self._proc(33154)], [self._proc(-33150)], set(), {}), [])


class TrainerSpellLevelTest(unittest.TestCase):
    CLASS_TRAINERS = {210, 211}
    SELF_BUFF = {"Effect_1": 6, "ImplicitTargetA_1": 1}  # APPLY_AURA on the caster: goes through rank selection

    def _grant(self, spell_id=202800, trainer=210, req_level=20):
        return {"TrainerId": trainer, "SpellId": spell_id, "ReqLevel": req_level}

    def _check(self, grant, spell_level, effects=None, **kw):
        row = _row(grant["SpellId"], SpellLevel=spell_level, **(self.SELF_BUFF if effects is None else effects))
        return lint.check_trainer_spell_level([grant], {grant["SpellId"]: row}, self.CLASS_TRAINERS, **kw)

    def test_a_learn_level_below_spell_level_warns(self):
        warnings = self._check(self._grant(req_level=60), 70)
        self.assertEqual(len(warnings), 1)
        self.assertIn("SpellLevel is 70", warnings[0])
        self.assertIn("GetAuraRankForLevel", warnings[0])

    def test_equal_or_higher_learn_level_is_silent(self):
        self.assertEqual(self._check(self._grant(req_level=16), 16), [])
        self.assertEqual(self._check(self._grant(req_level=30), 1), [])

    def test_stock_wind_shear_210_at_16_is_silent(self):
        self.assertEqual(self._check(self._grant(57994, 210, 16), 16), [])

    def test_party_and_raid_area_auras_and_allies_are_rank_selected(self):
        for effects in (
            {"Effect_1": 35, "ImplicitTargetA_1": 20}, {"Effect_2": 65, "ImplicitTargetA_2": 56},
            {"Effect_1": 6, "ImplicitTargetA_1": 21}, {"Effect_3": 6, "ImplicitTargetA_3": 57},
        ):
            with self.subTest(effects=effects):
                self.assertEqual(len(self._check(self._grant(req_level=10), 22, effects)), 1)

    def test_an_attack_or_a_hostile_aura_never_reaches_rank_selection(self):
        # Savage Bite / Deep Freeze shape: damage, or an aura on an enemy, learned below SpellLevel.
        for effects in (
            {"Effect_1": 2, "ImplicitTargetA_1": 6},                      # SCHOOL_DAMAGE
            {"Effect_1": 6, "ImplicitTargetA_1": 6},                      # APPLY_AURA on the enemy (stun, bleed)
            {"Effect_1": 3, "ImplicitTargetA_1": 1},                      # not an aura-applying effect
            {},                                                           # no effects at all
        ):
            with self.subTest(effects=effects):
                self.assertEqual(self._check(self._grant(req_level=10), 22, effects), [])

    def test_the_three_exempting_attributes_silence_a_buff(self):
        for column, bit in (("Attributes", 0x02000000), ("AttributesEx2", 0x8), ("AttributesEx3", 0x08000000)):
            with self.subTest(column=column):
                self.assertEqual(self._check(self._grant(req_level=10), 22, {**self.SELF_BUFF, column: bit}), [])

    def test_a_trainer_that_is_not_a_class_trainer_is_silent(self):
        self.assertEqual(self._check(self._grant(trainer=999, req_level=10), 70), [])

    def test_a_spell_with_no_row_is_not_judged(self):
        self.assertEqual(lint.check_trainer_spell_level([self._grant()], {}, self.CLASS_TRAINERS), [])

    def test_the_allow_set_exempts_a_listed_spell(self):
        self.assertEqual(self._check(self._grant(req_level=10), 22, allow={202800: "why"}), [])
        self.assertEqual(lint.TRAINER_SPELL_LEVEL_ALLOW, {})


def _family_row(spell_id=202800, **kw) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 11, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0}
    row.update(kw)
    return row


def _family(row, name="Test Spell", procs=None, sla=None, lines=frozenset(), rules=None):
    kw = {} if rules is None else {"rules": rules}
    return lint.check_family_bit_rules([{"name": name}], [row], procs, sla, lines, **kw)


class ShamanFamilyRulesTest(unittest.TestCase):
    RULES = (lint.SHAMAN_FAMILY_RULES,)

    def test_the_shaman_row_is_registered_and_the_hunter_name_still_works(self):
        self.assertIn(lint.SHAMAN_FAMILY_RULES, lint.FAMILY_BIT_RULES)
        self.assertIn(lint.HUNTER_FAMILY_RULES, lint.FAMILY_BIT_RULES)
        self.assertIs(lint.check_hunter_family_rules, lint.check_family_bit_rules)
        rules = lint.SHAMAN_FAMILY_RULES
        self.assertEqual(rules.spell_class_set, 11)
        self.assertEqual(rules.protected_bits, (0, 0x420, 0))
        self.assertEqual(rules.forbidden_reader_bits, (0, 0, 0x80000800))
        self.assertEqual(rules.exempt_ids, frozenset())
        self.assertEqual(rules.exempt_name_prefix, "")

    # (a) the elemental shield bits d1 b5, d1 b10
    def test_a_carrier_of_a_shield_bit_warns(self):
        for bit in (0x20, 0x400, 0x420):
            with self.subTest(bit=hex(bit)):
                warnings = _family(_family_row(SpellClassMask_2=bit), rules=self.RULES)
                self.assertEqual(len(warnings), 1)
                self.assertIn("shaman family-bit rule (a)", warnings[0])
                self.assertIn("elemental shield", warnings[0])
                self.assertIn("SPELL_SPECIFIC_ELEMENTAL_SHIELD", warnings[0])

    def test_other_d1_bits_and_other_dwords_are_fine(self):
        for column, value in (("SpellClassMask_2", 0x800), ("SpellClassMask_2", 0x1), ("SpellClassMask_1", 0x420),
                              ("SpellClassMask_3", 0x420), ("SpellClassMask_1", 0x400)):
            with self.subTest(column=column, value=hex(value)):
                self.assertEqual(_family(_family_row(**{column: value}), rules=self.RULES), [])

    def test_a_listed_exempt_id_may_carry_a_shield_bit(self):
        rules = (lint.FamilyBitRules(**{**lint.SHAMAN_FAMILY_RULES.__dict__, "exempt_ids": frozenset({202800})}),)
        self.assertEqual(_family(_family_row(SpellClassMask_2=0x20), rules=rules), [])

    def test_no_name_exempts_a_shield_bit_carrier(self):
        # exempt_name_prefix="" means "no name exemption": str.startswith("") is always True, so a name test that
        # forgot to check for the empty prefix would exempt every learned spell.
        sla = [{"Spell": 202800, "SkillLine": 375}]
        for name in ("Lightning Shield", "Earth Shield", ""):
            with self.subTest(name=name):
                warnings = _family(_family_row(SpellClassMask_2=0x20), name=name, sla=sla, rules=self.RULES)
                self.assertEqual(len(warnings), 1)

    def test_an_empty_prefix_does_not_exempt_in_a_hunter_style_rule_either(self):
        rules = (lint.FamilyBitRules(
            name="x", spell_class_set=11, protected_bits=(0, 0x420, 0), exempt_name_prefix="",
        ),)
        sla = [{"Spell": 202800, "SkillLine": 375}]
        self.assertEqual(len(_family(_family_row(SpellClassMask_2=0x20), name="Anything", sla=sla, rules=rules)), 1)

    # (c) the racial bits d2 b11, d2 b31
    def test_a_reader_mask_containing_a_racial_bit_warns(self):
        for column in ("EffectSpellClassMaskA_3", "EffectSpellClassMaskB_3", "EffectSpellClassMaskC_3"):
            for bit in (0x800, 0x80000000, 0x80000800 | 0x1):
                with self.subTest(column=column, bit=hex(bit)):
                    warnings = _family(_family_row(**{column: bit}), rules=self.RULES)
                    self.assertEqual(len(warnings), 1)
                    self.assertIn("shaman family-bit rule (c)", warnings[0])
                    self.assertIn("racial", warnings[0])

    def test_effect_letter_is_the_effect_index(self):
        self.assertIn("effect 2", _family(_family_row(EffectSpellClassMaskB_3=0x800), rules=self.RULES)[0])

    def test_a_reader_on_other_d2_bits_is_silent(self):
        self.assertEqual(_family(_family_row(EffectSpellClassMaskA_3=0x1000 | 0x4000), rules=self.RULES), [])
        self.assertEqual(_family(_family_row(EffectSpellClassMaskA_2=0x800), rules=self.RULES), [])  # d1 b11, not d2

    def test_a_spell_proc_family_mask_containing_a_racial_bit_warns(self):
        for family in (11, 0):
            with self.subTest(family=family):
                proc = {"SpellId": 202766, "SpellFamilyName": family, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0,
                        "SpellFamilyMask2": 0x80000000}
                warnings = lint.check_family_bit_rules([], [], [proc], rules=self.RULES)
                self.assertEqual(len(warnings), 1)
                self.assertIn("rule (c)", warnings[0])

    def test_a_proc_of_another_family_or_a_clean_mask_is_silent(self):
        other = {
            "SpellId": 1, "SpellFamilyName": 5, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0x800,
        }
        clean = {"SpellId": 2, "SpellFamilyName": 11, "SpellFamilyMask0": 0x400, "SpellFamilyMask1": 0x800,
                 "SpellFamilyMask2": 0x1}
        self.assertEqual(lint.check_family_bit_rules([], [], [other, clean], rules=self.RULES), [])

    # zero masks make (b) and (d) no-ops
    def test_rules_b_and_d_are_no_ops_for_shaman(self):
        # d1 b0 is the hunter's poisoned bit and d2 b22 its pet group bit: harmless to a shaman.
        row = _family_row(SpellClassMask_1=0xFFFFFFFF, SpellClassMask_2=0x1, SpellClassMask_3=0x400000)
        sla = [{"Spell": 202800, "SkillLine": 270}]  # taught on a pet line
        warnings = _family(row, sla=sla, lines=frozenset({209}), rules=self.RULES)
        self.assertFalse([w for w in warnings if "rule (b)" in w or "rule (d)" in w], warnings)

    # scope
    def test_stock_ids_and_other_class_sets_are_out_of_scope(self):
        self.assertEqual(_family(_family_row(2484, SpellClassMask_2=0x20), rules=self.RULES), [])
        self.assertEqual(_family(_family_row(SpellClassSet=9, SpellClassMask_2=0x20), rules=self.RULES), [])

    def test_a_clean_shaman_spell_prints_nothing(self):
        row = _family_row(SpellClassMask_1=0x400, SpellClassMask_2=0x800, SpellClassMask_3=0x20)
        self.assertEqual(_family(row, rules=self.RULES), [])

    def test_the_default_rule_set_judges_both_classes(self):
        self.assertEqual(len(_family(_family_row(SpellClassMask_2=0x20))), 1)                      # shaman (a)
        self.assertEqual(len(_family(_family_row(SpellClassSet=9, SpellClassMask_2=0x1))), 1)      # hunter (b)

    def test_the_hunter_messages_are_unchanged(self):
        warnings = _family(_family_row(SpellClassSet=9, SpellClassMask_1=0x80000))
        self.assertEqual(len(warnings), 1)
        self.assertIn("carries an aspect bit", warnings[0])
        self.assertIn("SPELL_SPECIFIC_ASPECT and it knocks the active aspect off", warnings[0])
        warnings = _family(_family_row(SpellClassSet=9, EffectSpellClassMaskA_2=0x10000000))
        self.assertIn("contains the pet bit (d1 b28)", warnings[0])
        self.assertIn("reaches every pet ability", warnings[0])


class WiringTest(unittest.TestCase):
    """generate.py's helper runs every new lint (the --check block and the full run call it)."""

    def test_each_lint_is_reached(self):
        import generate

        entries = [_entry("Totem Spell"), _entry("Hidden"), _entry("Rain"), _entry("Early")]
        rows = [
            _row(202800, RequiredTotemCategoryID_1=4),
            _row(202801, Attributes=0x80),
            _row(202802, Effect_1=27, EffectAura_1=3),
            _row(202803, SpellLevel=60, Effect_1=6, ImplicitTargetA_1=1),
        ]
        dsl_classes = {
            "creature_template_spells": [{"CreatureID": 300270, "Index": 0, "Spell": 999999, "VerifiedBuild": 0}],
            "trainer_spells": [
                {"TrainerId": 210, "SpellId": 202801, "ReqLevel": 10},
                {"TrainerId": 210, "SpellId": 202803, "ReqLevel": 10},
            ],
            "spell_procs": [{"SpellId": 202800, "ProcFlags": 0x10, "SpellPhaseMask": 0}],
        }
        talents = {"skill_line_abilities": [], "talents": []}
        shadow = ([{"SpellId": -202800}], set(), {})
        warnings = generate._t1_content_warnings(dsl_classes, talents, entries, rows, {}, [], shadow)
        text = "\n".join(warnings)
        for needle in (
            "creature_spell(300270, 0, 999999)", "requires a totem tool", "DO_NOT_DISPLAY", "persistent area aura",
            "spell_proc 202800: ProcFlags", "spell_proc 202800: shadowed", "trained_by(spell 202803",
        ):
            self.assertIn(needle, text)


HAVE_REAL_DATA = all(
    (state.BASE_DBC_DIR / table.dbc_filename).is_file()
    for table in (dbcfmt.SPELL, dbcfmt.TALENT, dbcfmt.SPELLCASTTIMES, dbcfmt.SPELLDURATION, dbcfmt.SPELLRANGE,
                  dbcfmt.SPELLRADIUS, dbcfmt.SPELLSHAPESHIFTFORM)
)


class _AnyRows(dict):
    def __contains__(self, key):
        return True


class _AnySet(set):
    def __contains__(self, key):
        return True


class _AnyTrainer:
    def trainer_problems(self, trainer_id):
        return []


@unittest.skipUnless(HAVE_REAL_DATA, "needs the extracted base client DBCs (var/extractors/dbc)")
class RealPopulationTest(unittest.TestCase):
    """The declared population (CSV + every source/classes and source/npcs file), built the way --check builds it,
    against every new lint. The allow sets must cover today's hits, and the shaman source (the P0 spike while it
    exists) must be silent without them."""

    @classmethod
    def setUpClass(cls):
        import generate

        cls.generate = generate
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_entries = source.load_spells_csv(generate.SOURCE_DIR / "spells")
        talents = source.load_talents_yaml(generate.SOURCE_DIR / "talents")
        kwargs = dict(
            ids_cfg=ids_cfg, trainer_index=_AnyTrainer(), existing_group_ids=_AnySet(),
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM), existing_creature_rows=_AnyRows(),
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.dsl_live_data(state.load_stock_rows(dbcfmt.TALENT), {}),
        )
        dsl = registry.load_classes_dir(generate.SOURCE_DIR / "classes", **kwargs)
        generate._merge_npc_declarations(dsl, registry.load_classes_dir(generate.SOURCE_DIR / "npcs", **kwargs))
        generate._merge_dsl_sources(spell_entries, talents, dsl)
        reuse = ReuseContext(
            {name: list(state.load_stock_rows(table).values()) for name, table in generate.SECONDARY_TABLES.items()},
            ids_cfg,
        )
        cls.entries, cls.talents, cls.dsl = spell_entries, talents, dsl
        cls.rows = [build.build_spell_row(e, reuse) for e in spell_entries]
        cls.stock = state.load_stock_rows(dbcfmt.SPELL)

    def test_the_declared_population_is_silent(self):
        shadow = self.generate._proc_shadow_inputs(
            spell_tables.SpellTableIndex({}), self.dsl, self.talents, state.load_existing_rows(dbcfmt.TALENT),
        )
        warnings = self.generate._t1_content_warnings(
            self.dsl, self.talents, self.entries, self.rows, self.stock, [], shadow,
        )
        self.assertEqual(warnings, [])

    def test_the_shadowed_proc_allow_set_is_exactly_what_the_lint_finds(self):
        shadow = self.generate._proc_shadow_inputs(
            spell_tables.SpellTableIndex({}), self.dsl, self.talents, state.load_existing_rows(dbcfmt.TALENT),
        )
        found = lint.check_shadowed_spell_procs(self.dsl["spell_procs"], *shadow, allow={})
        self.assertEqual({int(w.split()[1].rstrip(":")) for w in found}, set(lint.SHADOWED_PROC_ALLOW))

    def test_the_family_bit_rules_are_silent_on_the_declared_population(self):
        sla = [
            {"Spell": int(e["spell_id"]), "SkillLine": int(e["skill_line"])}
            for e in self.talents["skill_line_abilities"]
        ]
        warnings = lint.check_family_bit_rules(
            self.entries, self.rows, self.dsl["spell_procs"], sla, self.generate._pet_skill_lines(),
        )
        self.assertEqual(warnings, [])

    def test_the_shaman_spells_are_silent_without_any_allow_set(self):
        shaman = [(e, r) for e, r in zip(self.entries, self.rows) if e.get("_source_class") == "shaman"]
        self.assertTrue(shaman)
        entries, rows = [e for e, _ in shaman], [r for _, r in shaman]
        self.assertEqual(lint.check_totem_tools(entries, rows), [])
        self.assertEqual(lint.check_ground_effect_haste(entries, rows, allow=frozenset()), [])
        # real learn inputs: the shaman SkillLineAbility rows, trained_by() rows and talent ranks
        sla = [
            {"Spell": int(e["spell_id"]), "SkillLine": int(e["skill_line"])}
            for e in self.talents["skill_line_abilities"]
        ]
        trained = {int(r["SpellId"]) for r in self.dsl["trainer_spells"]}
        ranks = {int(r) for t in self.talents["talents"] for r in (t.get("rank_spell_ids") or []) if r}
        self.assertEqual(
            lint.check_hidden_learned_spells(
                entries, rows, sla, trained, ranks, self.generate._pet_skill_lines(), allow=frozenset(),
            ), [],
        )
        ids = {int(r["ID"]) for r in rows}
        procs = [p for p in self.dsl["spell_procs"] if abs(int(p["SpellId"])) in ids]
        lookup = {int(r["ID"]): r for r in rows}
        self.assertEqual(lint.check_spell_proc_rows(procs, lookup, allow={}), [])

    def test_the_stock_family_11_spells_that_still_hold_a_totem_tool(self):
        # The strip list for SH0: every declared stock family-11 spell with a tool column, from the same data.
        held = {
            int(r["ID"]): {c: int(r[c]) for c in TOTEM_COLUMNS if int(r.get(c) or 0)}
            for r in self.rows if int(r.get("SpellClassSet") or 0) == 11 and int(r["ID"]) < 200000
            and any(int(r.get(c) or 0) for c in TOTEM_COLUMNS)
        }
        self.assertTrue(held)
        self.assertEqual({c for cols in held.values() for c in cols}, {"RequiredTotemCategoryID_1"})
        self.assertEqual(len(lint.check_totem_tools(self.entries, self.rows, {11})), len(held))

    def test_the_full_strip_list_is_every_stock_family_11_spell_with_a_tool_column(self):
        # Widened over the stock client rows too: the declared 42 plus the undeclared higher ranks.
        stock = {i: r for i, r in self.stock.items() if int(r.get("SpellClassSet") or 0) == 11}
        expected = {i for i, r in stock.items() if any(int(r.get(c) or 0) for c in TOTEM_COLUMNS) and i < 200000}
        warnings = lint.check_totem_tools(self.entries, self.rows, {11}, self.stock)
        self.assertEqual({int(w.split()[1]) for w in warnings if int(w.split()[1]) < 200000}, expected)
        self.assertGreater(len(expected), len({i for i in expected if any(
            int(r["ID"]) == i for r in self.rows)}))  # there are undeclared rows to catch


if __name__ == "__main__":
    unittest.main()
