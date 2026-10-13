"""
GCD-haste aura generator tests (lib/gcd_haste.py, .agents/plans/melee-haste-gcd/melee-haste-gcd.PLAN.md T1).
Fixtures only: no DBC files, no source tree.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gcd_haste.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, gcd_haste, lint, trainer_state  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

WARRIOR, PALADIN, HUNTER, PRIEST = 4, 10, 9, 6
PASSIVE = gcd_haste.ATTR0_PASSIVE
ABILITY = gcd_haste.ATTR0_IS_ABILITY
RANGED_SLOT = gcd_haste.ATTR0_USES_RANGED_SLOT
MELEE_CLASS, RANGED_CLASS, MAGIC_CLASS = 2, 3, 1


def make_policy(**overrides) -> gcd_haste.Policy:
    args = dict(
        aura_ids={WARRIOR: 900000, PALADIN: 900001, HUNTER: 900002},
        exclude={}, tick_ms=500, placeholder_ms=-495, pet_skill_lines=(),
    )
    args.update(overrides)
    return gcd_haste.Policy(**args)


def spell(spell_id: int, family: int, flags=(0, 0, 0), dmg_class=MAGIC_CLASS, attributes=0, name="", **columns) -> dict:
    row = dbcfile.empty_row(dbcfmt.SPELL)
    row.update(
        ID=spell_id, SpellClassSet=family, DefenseType=dmg_class, Attributes=attributes,
        StartRecoveryCategory=133, StartRecoveryTime=1500, Name_Lang_enUS=name or f"spell {spell_id}",
        SpellClassMask_1=flags[0], SpellClassMask_2=flags[1], SpellClassMask_3=flags[2],
    )
    row.update(columns)
    return row


def run(
    rows: list[dict], learnable: set[int] | None = None, policy: gcd_haste.Policy | None = None, superseded=(),
):
    spells = {r["ID"]: r for r in rows}
    return gcd_haste.compute(
        spells, set(spells) if learnable is None else learnable, policy or make_policy(), superseded,
    )


class CandidateTests(unittest.TestCase):
    def test_melee_strike_and_ability_utility_are_candidates_but_a_plain_spell_is_not(self):
        result = run([
            spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY, name="Strike"),
            spell(2, WARRIOR, (0x2, 0, 0), attributes=ABILITY, name="Shout"),
            spell(3, WARRIOR, (0x4, 0, 0), name="Plain spell the core already hastes"),
        ])
        self.assertEqual([c.spell_id for c in result.families[WARRIOR].candidates], [1, 2])
        self.assertEqual(result.families[WARRIOR].melee, (0x3, 0, 0))
        self.assertEqual(result.errors, [])

    def test_a_spell_must_be_1500ms_category_133_nonpassive_in_the_family_and_learnable(self):
        rows = [
            spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY, StartRecoveryTime=1000),
            spell(2, WARRIOR, (0x2, 0, 0), attributes=ABILITY, StartRecoveryCategory=0),
            spell(3, WARRIOR, (0x4, 0, 0), attributes=ABILITY | PASSIVE),
            spell(4, 999, (0x8, 0, 0), attributes=ABILITY),
            spell(5, WARRIOR, (0x10, 0, 0), attributes=ABILITY),
            spell(6, WARRIOR, (0x20, 0, 0), attributes=ABILITY),
        ]
        result = run(rows, learnable={1, 2, 3, 4, 5})
        self.assertEqual([c.spell_id for c in result.families[WARRIOR].candidates], [5])

    def test_haste_source_rule(self):
        def source(family, **kwargs):
            return gcd_haste.haste_source(spell(1, family, **kwargs), family)

        self.assertEqual(source(WARRIOR, dmg_class=MELEE_CLASS), gcd_haste.MELEE)
        self.assertEqual(source(HUNTER, dmg_class=MELEE_CLASS), gcd_haste.MELEE)  # Mongoose Bite
        self.assertEqual(source(HUNTER, dmg_class=RANGED_CLASS), gcd_haste.RANGED)
        self.assertEqual(source(PALADIN, dmg_class=RANGED_CLASS), gcd_haste.RANGED)
        self.assertEqual(source(HUNTER, attributes=RANGED_SLOT), gcd_haste.RANGED)
        self.assertEqual(source(WARRIOR, attributes=RANGED_SLOT), gcd_haste.RANGED)

    def test_utility_ability_is_ranged_for_a_hunter_and_melee_for_everyone_else(self):
        result = run([
            spell(1, HUNTER, (0x1, 0, 0), attributes=ABILITY, name="Hunter utility"),
            spell(2, PALADIN, (0x2, 0, 0), attributes=ABILITY, name="Paladin seal"),
        ])
        self.assertEqual(result.families[HUNTER].ranged, (0x1, 0, 0))
        self.assertEqual(result.families[HUNTER].melee, (0, 0, 0))
        self.assertEqual(result.families[PALADIN].melee, (0x2, 0, 0))
        self.assertEqual(result.families[PALADIN].ranged, (0, 0, 0))

    def test_pet_skill_line_and_pet_talent_spells_are_not_learnable_even_if_a_dsl_copy_looks_castable(self):
        policy = make_policy(pet_skill_lines=(209,))
        abilities = [{"Spell": 1, "SkillLine": 209}, {"Spell": 2, "SkillLine": 50}]
        talents = [{"TabID": 410, "SpellRank_1": 3}, {"TabID": 361, "SpellRank_1": 4}]
        learnable = gcd_haste.learnable_spell_ids(abilities, talents, dsl_player_castable={1, 3, 5}, policy=policy,
                                                  pet_tabs={410})
        self.assertEqual(learnable, {2, 4, 5})

    def test_superseded_and_not_castable_spells_are_not_learnable(self):
        policy = make_policy(not_castable={7: "retired"})
        learnable = gcd_haste.learnable_spell_ids(
            [{"Spell": n, "SkillLine": 50} for n in (5, 6, 7)], [], (), policy, superseded={6},
        )
        self.assertEqual(learnable, {5})


class ConflictTests(unittest.TestCase):
    def test_a_bit_shared_with_a_spell_the_core_hastes_is_an_error(self):
        result = run([
            spell(1, HUNTER, (0x80, 0, 0), dmg_class=RANGED_CLASS, name="Black Arrow"),
            spell(2, HUNTER, (0x80, 0, 0), name="Freezing Trap"),
        ])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("ranged bit 7", result.errors[0])
        self.assertIn("Black Arrow", result.errors[0])
        self.assertIn("Freezing Trap", result.errors[0])

    def test_a_nonoverlapping_hasted_spell_is_fine(self):
        result = run([
            spell(1, HUNTER, (0x80, 0, 0), dmg_class=RANGED_CLASS),
            spell(2, HUNTER, (0x100, 0, 0)),
        ])
        self.assertEqual(result.errors, [])

    def test_the_conflict_is_found_in_the_servers_view_of_the_flags(self):
        policy = make_policy(server_flag_fixes={2: (0x80, None, None)})
        result = run([
            spell(1, HUNTER, (0x80, 0, 0), dmg_class=RANGED_CLASS),
            spell(2, HUNTER, (0x100, 0, 0), name="rewritten at load"),
        ], policy=policy)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("server flags", result.errors[0])

    def test_a_bit_in_both_the_melee_and_the_ranged_mask_is_an_error(self):
        result = run([
            spell(1, HUNTER, (0x1, 0, 0), dmg_class=MELEE_CLASS, name="melee user"),
            spell(2, HUNTER, (0x1, 0, 0), dmg_class=RANGED_CLASS, name="ranged user"),
        ])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("both the melee and the ranged mask", result.errors[0])

    def test_exclude_removes_a_conflict_and_its_bits(self):
        rows = [
            spell(1, HUNTER, (0x80, 0, 0), dmg_class=RANGED_CLASS, name="Black Arrow"),
            spell(2, HUNTER, (0x80, 0, 0), name="Freezing Trap"),
            spell(3, HUNTER, (0x2, 0, 0), dmg_class=RANGED_CLASS, name="Arcane Shot"),
        ]
        result = run(rows, policy=make_policy(exclude={1: "shares a bit with the traps"}))
        self.assertEqual(result.errors, [])
        plan = result.families[HUNTER]
        self.assertEqual(plan.ranged, (0x2, 0, 0))
        self.assertEqual(plan.excluded, [(1, "Black Arrow", "shares a bit with the traps")])
        self.assertEqual([c.spell_id for c in plan.candidates], [3])

    def test_not_castable_removes_a_retired_hasted_spell_from_the_conflict(self):
        rows = [
            spell(1, PALADIN, (0x8000000, 0, 0), attributes=ABILITY, name="Seal of Righteousness"),
            spell(2, PALADIN, (0x8000000, 0, 0), name="Seal of Righteousness rank 2"),
        ]
        self.assertEqual(len(run(rows).errors), 1)
        result = run(rows, learnable={1}, policy=make_policy(not_castable={2: "retired"}))
        self.assertEqual(result.errors, [])
        self.assertEqual(result.families[PALADIN].melee, (0x8000000, 0, 0))

    def test_not_castable_is_what_removes_the_retired_spell_from_learnable(self):
        # learnable built the way generate.py builds it: without NOT_CASTABLE spell 2 stays on the conflict side
        rows = [
            spell(1, PALADIN, (0x8000000, 0, 0), attributes=ABILITY, name="Seal of Righteousness"),
            spell(2, PALADIN, (0x8000000, 0, 0), name="Seal of Righteousness rank 2"),
        ]
        abilities = [{"Spell": 1, "SkillLine": 50}, {"Spell": 2, "SkillLine": 50}]
        without = make_policy()
        learnable = gcd_haste.learnable_spell_ids(abilities, [], (), without)
        self.assertEqual(len(run(rows, learnable, without).errors), 1)
        with_policy = make_policy(not_castable={2: "retired"})
        learnable = gcd_haste.learnable_spell_ids(abilities, [], (), with_policy)
        result = run(rows, learnable, with_policy)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.assumed_untrainable, {2: "NOT_CASTABLE (retired)"})

    def test_core_hasted_spells_at_1000_to_1499ms_are_on_the_conflict_side(self):
        # StartRecoveryTime 1000-1499 is clamped/hasted by the core too; the check must not be `== 1500`
        for recovery in (1000, 1250, 1499):
            result = run([
                spell(1, HUNTER, (0x80, 0, 0), dmg_class=RANGED_CLASS, name="Shot"),
                spell(2, HUNTER, (0x80, 0, 0), name="Short-GCD trap", StartRecoveryTime=recovery),
            ])
            self.assertEqual(len(result.errors), 1, recovery)
            self.assertIn("Short-GCD trap", result.errors[0])

    def test_a_superseded_rank_that_shares_a_bit_is_recorded_as_assumed_untrainable(self):
        rows = [
            spell(1, PALADIN, (0x10, 0, 0), attributes=ABILITY, name="Seal"),
            spell(2, PALADIN, (0x10, 0, 0), name="Old rank"),
            spell(3, PALADIN, (0x20, 0, 0), name="Unrelated old rank"),
        ]
        result = run(rows, learnable={1}, superseded={2, 3})
        self.assertEqual(result.errors, [])
        self.assertEqual(result.assumed_untrainable, {2: "superseded rank"})


class UntrainableAssumptionTests(unittest.TestCase):
    ASSUMED = {53407: "NOT_CASTABLE (retired)"}

    def index(self, reachable: bool) -> trainer_state.TrainerIndex:
        return trainer_state.TrainerIndex(
            [{"CreatureId": 100, "TrainerId": 5}] if reachable else [],
            [], [{"entry": 100, "npcflag": 0x10}], [{"id1": 100, "id2": 0, "id3": 0}],
        )

    def check(self, live, reachable=True, declared=()):
        index = self.index(reachable)
        return gcd_haste.untrainable_errors(
            self.ASSUMED, live, lambda tid: not index.trainer_problems(tid), declared,
        )

    def test_a_live_row_of_a_reachable_trainer_is_an_error(self):
        errors = self.check([(5, 53407)])
        self.assertEqual(len(errors), 1)
        self.assertIn("trainer 5", errors[0])

    def test_a_live_row_of_an_orphan_trainer_is_fine(self):
        self.assertEqual(self.check([(5, 53407)], reachable=False), [])

    def test_a_trained_by_declaration_is_an_error(self):
        errors = self.check([], declared=[53407])
        self.assertEqual(len(errors), 1)
        self.assertIn("trained_by()", errors[0])

    def test_unrelated_rows_and_declarations_are_fine(self):
        self.assertEqual(self.check([(5, 1)], declared=[2]), [])

    def test_a_candidate_with_an_all_zero_mask_is_an_error_unless_excluded(self):
        rows = [spell(1, WARRIOR, (0, 0, 0), attributes=ABILITY, name="Unflagged")]
        self.assertIn("all-zero SpellClassMask", run(rows).errors[0])
        self.assertEqual(run(rows, policy=make_policy(exclude={1: "no flags"})).errors, [])

    def test_exclude_naming_a_missing_spell_is_an_error(self):
        result = run([spell(1, WARRIOR, (1, 0, 0), attributes=ABILITY)], policy=make_policy(exclude={42: "typo"}))
        self.assertTrue(any("EXCLUDE names spell 42" in e for e in result.errors))

    def test_a_stale_exclude_is_a_warning(self):
        rows = [
            spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY, name="Still a candidate"),
            spell(2, WARRIOR, (0x2, 0, 0), name="Reworked into a hasted spell"),
        ]
        result = run(rows, policy=make_policy(exclude={1: "kept", 2: "stale"}))
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("EXCLUDE[2]", result.warnings[0])

    def test_server_and_client_views_both_widen_the_mask_and_are_reported(self):
        policy = make_policy(server_flag_fixes={1: (None, None, 0x10)})
        result = run([spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY, name="Rewritten")], policy=policy)
        self.assertEqual(result.families[WARRIOR].melee, (0x1, 0, 0x10))
        self.assertEqual(len(result.families[WARRIOR].view_differences), 1)
        self.assertEqual(result.errors, [])


class AuraEntryTests(unittest.TestCase):
    def build_row(self, entry: dict) -> dict:
        return build.build_spell_row(entry, ReuseContext({}, _ids_cfg()))

    def entry_for(self, rows: list[dict], family: int) -> dict:
        policy = make_policy()
        result = run(rows, policy=policy)
        self.assertEqual(result.errors, [])
        return next(e for e in gcd_haste.aura_entries(result, policy) if e["raw_overrides"]["SpellClassSet"] == family)

    def test_mask_columns_use_the_effect_index_as_the_letter(self):
        self.assertEqual(gcd_haste.mask_column(0, 0), "EffectSpellClassMaskA_1")
        self.assertEqual(gcd_haste.mask_column(0, 2), "EffectSpellClassMaskA_3")
        self.assertEqual(gcd_haste.mask_column(1, 0), "EffectSpellClassMaskB_1")
        self.assertEqual(gcd_haste.mask_column(1, 1), "EffectSpellClassMaskB_2")

    def test_melee_mask_is_effect_0_letter_a_and_ranged_mask_is_effect_1_letter_b(self):
        entry = self.entry_for([
            spell(1, HUNTER, (0x1, 0x2, 0x4), dmg_class=MELEE_CLASS, attributes=ABILITY),
            spell(2, HUNTER, (0x10, 0x20, 0x40), dmg_class=RANGED_CLASS),
        ], HUNTER)
        row = self.build_row(entry)
        self.assertEqual([row[f"EffectSpellClassMaskA_{n}"] for n in (1, 2, 3)], [0x1, 0x2, 0x4])
        self.assertEqual([row[f"EffectSpellClassMaskB_{n}"] for n in (1, 2, 3)], [0x10, 0x20, 0x40])
        self.assertEqual([row[f"EffectSpellClassMaskC_{n}"] for n in (1, 2, 3)], [0, 0, 0])
        self.assertEqual([row[f"Effect_{n}"] for n in (1, 2, 3)], [6, 6, 6])
        self.assertEqual([row[f"EffectAura_{n}"] for n in (1, 2, 3)], [107, 107, 226])
        self.assertEqual([row[f"EffectMiscValue_{n}"] for n in (1, 2)], [21, 21])
        self.assertEqual(row["EffectAuraPeriod_3"], 500)
        self.assertEqual(row["SpellClassSet"], HUNTER)

    def test_empty_ranged_mask_leaves_effect_1_out_entirely(self):
        entry = self.entry_for([spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY)], WARRIOR)
        row = self.build_row(entry)
        self.assertEqual((row["Effect_2"], row["EffectAura_2"], row["EffectMiscValue_2"]), (0, 0, 0))
        self.assertEqual([row[f"EffectSpellClassMaskB_{n}"] for n in (1, 2, 3)], [0, 0, 0])
        self.assertEqual(row["EffectAura_1"], 107)
        self.assertEqual(row["EffectAura_3"], 226)

    def test_empty_melee_mask_leaves_effect_0_out_entirely(self):
        entry = self.entry_for([spell(1, HUNTER, (0x1, 0, 0), dmg_class=RANGED_CLASS)], HUNTER)
        row = self.build_row(entry)
        self.assertEqual((row["Effect_1"], row["EffectAura_1"]), (0, 0))
        self.assertEqual(row["EffectAura_2"], 107)
        self.assertEqual(row["EffectSpellClassMaskB_1"], 0x1)

    def test_placeholder_amount_is_stored_as_basepoints_minus_one(self):
        entry = self.entry_for([spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY)], WARRIOR)
        self.assertEqual(self.build_row(entry)["EffectBasePoints_1"], -496)  # test policy uses -495

    def test_row_is_a_hidden_passive_with_no_cost_cast_time_cooldown_or_gcd(self):
        entry = self.entry_for([spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY)], WARRIOR)
        row = self.build_row(entry)
        self.assertTrue(row["Attributes"] & PASSIVE)
        self.assertTrue(row["Attributes"] & gcd_haste.ATTR0_DO_NOT_DISPLAY)
        self.assertEqual(
            (row["ManaCost"], row["RecoveryTime"], row["CategoryRecoveryTime"], row["StartRecoveryCategory"],
             row["StartRecoveryTime"]),
            (0, 0, 0, 0, 0),
        )
        self.assertEqual(row["EquippedItemClass"], -1)

    def test_aura_school_is_physical_like_heart_of_the_crusader(self):
        entry = self.entry_for([spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY)], WARRIOR)
        self.assertEqual(self.build_row(entry)["SchoolMask"], 1)

    def test_the_classmask_scoping_lint_is_clean_on_a_generated_row(self):
        for rows, family in (
            ([spell(1, WARRIOR, (0x1, 0, 0), dmg_class=MELEE_CLASS, attributes=ABILITY)], WARRIOR),
            ([spell(1, HUNTER, (0x1, 0, 0), dmg_class=RANGED_CLASS)], HUNTER),
            ([spell(1, HUNTER, (0, 0x1, 0), dmg_class=MELEE_CLASS, attributes=ABILITY),
              spell(2, HUNTER, (0x1, 0, 0), dmg_class=RANGED_CLASS)], HUNTER),
        ):
            entry = self.entry_for(rows, family)
            self.assertEqual(lint.check_classmask_scoping([entry], [self.build_row(entry)]), [])

    def test_a_family_with_bits_but_no_aura_id_is_an_error(self):
        policy = make_policy(aura_ids={})
        result = run([spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY)], policy=policy)
        with self.assertRaises(gcd_haste.GcdHasteError):
            gcd_haste.aura_entries(result, policy)

    def test_only_families_with_bits_get_an_aura(self):
        policy = make_policy()
        result = run(
            [spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY), spell(2, PALADIN, (0x1, 0, 0))], policy=policy,
        )
        self.assertEqual([e["id"] for e in gcd_haste.aura_entries(result, policy)], [900000])

    def test_every_generated_aura_is_bound_to_the_runtime_script(self):
        policy = make_policy()
        result = run(
            [spell(1, WARRIOR, (0x1, 0, 0), attributes=ABILITY), spell(2, PALADIN, (0x1, 0, 0), attributes=ABILITY)],
            policy=policy,
        )
        rows = gcd_haste.script_rows(gcd_haste.aura_entries(result, policy))
        self.assertEqual(
            [(r["spell_id"], r["ScriptName"]) for r in rows],
            [(900000, "spell_custom_haste_gcd"), (900001, "spell_custom_haste_gcd")],
        )


class PolicyTests(unittest.TestCase):
    def test_the_real_policy_file_loads(self):
        policy = gcd_haste.load_policy()
        self.assertEqual(policy.placeholder_ms, 0)
        self.assertEqual(policy.tick_ms, 500)
        self.assertEqual(len(set(policy.aura_ids.values())), len(policy.aura_ids))

    def test_a_reasonless_exclude_is_rejected(self):
        with self.assertRaises(gcd_haste.GcdHasteError):
            make_policy(exclude={1: " "})

    def test_the_icy_touch_rule_extends_dk_flags_for_the_servers_view(self):
        policy = gcd_haste.load_policy()
        icy = spell(45477, 15, (0x2, 0, 0), SpellIconID=2721)
        self.assertEqual(gcd_haste.client_flags(icy), (0x2, 0, 0))
        self.assertEqual(gcd_haste.server_flags(icy, policy), (0x42, 0, 0))

    def test_a_rule_sees_the_row_after_the_table_fix_for_the_same_spell(self):
        # SpellInfoCorrections.cpp applies its fixes in order, so a later rewrite works on the earlier one's result
        policy = make_policy(
            server_flag_fixes={1: (0x2, None, None)},
            server_flag_rules=(
                lambda row: (row["SpellClassMask_1"] | 0x40, 0, 0) if row["SpellClassMask_1"] & 0x2 else None,
            ),
        )
        row = spell(1, 15, (0x0, 0, 0))
        self.assertEqual(gcd_haste.server_flags(row, policy), (0x42, 0, 0))

    def test_ebon_plague_rewrite_replaces_only_the_third_dword(self):
        policy = gcd_haste.load_policy()
        plague = spell(51735, 15, (0x5, 0x6, 0x7))
        self.assertEqual(gcd_haste.server_flags(plague, policy), (0x5, 0x6, 0x10))


def _ids_cfg() -> dict:
    block = {"start": 1, "end": 1000}
    return {name: dict(block) for name in ("spellcasttimes", "spellduration", "spellrange", "spellradius")}


if __name__ == "__main__":
    unittest.main()
