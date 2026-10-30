"""
Death Knight T1, step 6 and the `--check` wiring: the GCD-haste dry run (`generate._gcd_haste_check_warnings`) and the
new lints reaching the shared `_t1_content_warnings` (which both `--check` and the full run call, hunter T1-10).

The dry run exists because the first P0 deploy stopped at `ERROR: gcd haste: Death Knight: 203684 ... all-zero
SpellClassMask`, which `--check` could not show. It is wired into `--check` with the superseded-rank map the full run
passes (without it the stock inputs print six unrelated Paladin / Hunter lines on today's tree; see
`_gcd_haste_check_warnings`). Covered: a declared learnable family-15 GCD melee spell with an
all-zero class mask produces the WARNING; the same spell with a class-mask bit produces nothing; the policy's own
exclusions are honoured; nothing else is printed.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dk_t1_check.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import build, dbcfmt, source, state  # noqa: E402
from lib.table_testkit import load_dsl  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
HAVE_SPELL_DBC = (state.BASE_DBC_DIR / dbcfmt.SPELL.dbc_filename).is_file()
PREFIX = "gcd haste (--check, stock approximation): "

STRIKE = '''
from lib.dsl.registry import skill_line_ability, spell

strike = spell(
    id=203690, name="Test Strike", cast_time_ms=0, cooldown_ms=6000,
    raw_overrides={{'SpellClassSet': 15, 'DefenseType': 2, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
                    {mask}}},
)
skill_line_ability(id=30790, skill_line=770, spell_id=strike.id, class_mask=32)
'''


def _declared(mask_overrides: str) -> tuple[list[dict], dict, dict]:
    dsl = load_dsl(STRIKE.format(mask=mask_overrides), ids_cfg=IDS)
    talents = {"tabs": [], "talents": [], "skill_line_abilities": list(dsl["skill_line_abilities"])}
    return list(dsl["spells"]), talents, dsl


@unittest.skipUnless(HAVE_SPELL_DBC, "var/extractors/dbc/Spell.dbc is not extracted")
class GcdHasteDryRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock_spells = state.load_stock_rows(dbcfmt.SPELL)

    def _run(self, mask_overrides: str) -> list[str]:
        entries, talents, dsl = _declared(mask_overrides)
        messages = generate._gcd_haste_check_warnings(entries, talents, dsl, self.stock_spells, IDS)
        # The stock population alone (no Hunter rework laid over it) has its own stock-only conflicts; the Death
        # Knight family is what this fixture declares, so judge that family.
        return [m for m in messages if "Death Knight" in m]

    def test_a_learnable_family_15_gcd_spell_with_an_all_zero_class_mask_warns(self):
        messages = self._run("'SpellClassMask_1': 0")
        self.assertEqual(len(messages), 1, messages)
        self.assertTrue(messages[0].startswith(PREFIX), messages[0])
        self.assertIn("Death Knight: 203690", messages[0])
        self.assertIn("all-zero", messages[0])

    def test_the_same_spell_with_a_class_mask_bit_is_silent(self):
        # a Death Knight family bit no stock GCD spell carries: the candidate gets a mask and nothing conflicts
        self.assertEqual(self._run("'SpellClassMask_2': 1 << 22"), [])

    def test_the_stock_death_knight_population_alone_is_silent(self):
        messages = generate._gcd_haste_check_warnings(
            [], {"tabs": [], "talents": [], "skill_line_abilities": []}, {"spells": [], "trainer_spells": []},
            self.stock_spells, IDS,
        )
        self.assertEqual([m for m in messages if "Death Knight" in m], [])
        self.assertTrue(all(m.startswith(PREFIX) for m in messages))

    def test_the_superseded_rank_map_the_full_run_uses_is_passed_through(self):
        # Without it the stock rows still list the collapsed ranks (Retribution Aura 10298, Mongoose Bite 14269) as
        # learnable and the committed tree prints six conflicts under --check; with it, none.
        from unittest import mock  # noqa: PLC0415

        survivor = {"id": 101, "notes": "single-rank bootstrap"}
        with mock.patch.object(generate, "load_spell_ranks_chains", return_value={100: [(100, 1), (101, 2)]}):
            fake_result = mock.Mock(errors=[], warnings=[])
            with mock.patch.object(generate, "_gcd_haste_entries", return_value=([], fake_result)) as run:
                generate._gcd_haste_check_warnings(
                    [], {"tabs": [], "talents": [], "skill_line_abilities": []},
                    {"spells": [survivor], "trainer_spells": []}, {}, IDS,
                )
        self.assertEqual(run.call_args.args[3], {100: 101})

    def test_main_wires_the_dry_run_into_check_as_a_warning(self):
        import inspect  # noqa: PLC0415

        text = inspect.getsource(generate._run)  # main() only parses flags and hands over to _run
        tail = text.split("_gcd_haste_check_warnings(")[1][:300]
        self.assertIn('print(f"WARNING: {warning}")', tail)

    def test_every_message_is_prefixed_so_it_can_only_be_printed_as_a_warning(self):
        entries, talents, dsl = _declared("'SpellClassMask_1': 0")
        messages = generate._gcd_haste_check_warnings(entries, talents, dsl, self.stock_spells, IDS)
        self.assertTrue(messages)
        self.assertTrue(all(m.startswith(PREFIX) and "ERROR" not in m.split(":")[0] for m in messages))


@unittest.skipUnless(HAVE_SPELL_DBC, "var/extractors/dbc/Spell.dbc is not extracted")
class SharedLintWiringTest(unittest.TestCase):
    """The new lints run through `_t1_content_warnings`, which `--check` and the full run both call."""

    @classmethod
    def setUpClass(cls):
        cls.stock_spells = state.load_stock_rows(dbcfmt.SPELL)

    def _warnings(self, class_source: str) -> list[str]:
        dsl = load_dsl(class_source, ids_cfg=IDS)
        entries = list(dsl["spells"])
        reuse = ReuseContext(
            {name: list(state.load_stock_rows(table).values()) for name, table in generate.SECONDARY_TABLES.items()},
            IDS,
        )
        rows = [build.build_spell_row(e, reuse) for e in entries]
        talents = {"tabs": [], "talents": [], "skill_line_abilities": []}
        full = {key: [] for key in registry.MERGE_KEYS} | dsl
        return generate._t1_content_warnings(full, talents, entries, rows, self.stock_spells, [])

    def test_unknown_spells_in_threat_and_creation_rows_warn(self):
        warnings = self._warnings(
            "from lib.dsl.registry import creation_action, creation_cast, spell_threat\n"
            "spell_threat(203999)\ncreation_action(1, 6, 0, 203998)\ncreation_cast(203997, 32)\n"
        )
        text = "\n".join(warnings)
        self.assertIn("spell_threat(203999)", text)
        self.assertIn("creation_action(1, 6, 0, 203998)", text)
        self.assertIn("creation_cast(203997, 32, 0)", text)

    def test_a_cost_on_a_non_rune_spell_warns(self):
        warnings = self._warnings(
            "from lib.dsl.registry import spell, spell_rune_cost\n"
            "spell_rune_cost(2600, unholy=1, frost=1, runic_power=20)\n"
            "spell(id=203600, name='Test Rune Spell', cast_time_ms=0, raw_overrides={'RuneCostID': 2600})\n"
        )
        self.assertTrue(any("RuneCostID 2600 with PowerType 0" in w for w in warnings), warnings)

    def test_a_clean_declaration_set_is_silent_for_the_new_lints(self):
        warnings = self._warnings(
            "from lib.dsl.registry import creation_action, creation_cast, spell, spell_rune_cost, spell_threat\n"
            "spell_rune_cost(2600, unholy=1, frost=1, runic_power=20)\n"
            "s = spell(id=203600, name='Test Rune Spell', cast_time_ms=0, power_type=5,"
            " raw_overrides={'RuneCostID': 2600})\n"
            "spell_threat(s, pct_mod=1.9)\ncreation_action(1, 6, 0, 6603)\ncreation_cast(s, 32)\n"
        )
        keywords = ("spell_threat", "creation_", "RuneCostID", "SpellRuneCost")
        noisy = [w for w in warnings if any(k in w for k in keywords)]
        self.assertEqual(noisy, [])


if __name__ == "__main__":
    unittest.main()
