"""
spell_rune_cost() (Death Knight T1, step 2): the helper, the `spellrunecost_dbc` SPELL_TABLES entry, the client
SpellRuneCost.dbc merge and the three lints.

Covered, per the handoff: each validation raise; `runic_power=20` stores 200; a declared (0, 1, 1, 20) row renders
DELETE-then-INSERT in Blood / Unholy / Frost order and passes the real codestyle-sql.py; convergence through the real
readers (hunter T1-1); a dropped declaration is pruned; the client merge keeps every stock row byte-identical; the
base-error message; every lint branch positive and negative, stock 47541 (power 6 / cost 422) silent, the P0 spike
spells silent (they set RuneCostID 0).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_spell_rune_cost.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import build, dbcfile, dbcfmt, lint, source, spell_tables, state  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TABLE = "spellrunecost_dbc"
COLUMNS = spell_tables.SPELLRUNECOST_COLUMNS
IDS_CFG = {"spellrunecost": {"start": 2600, "end": 2629}}
STOCK_FILE = state.BASE_DBC_DIR / dbcfmt.SPELLRUNECOST.dbc_filename

# Four stock rows as the real file has them: Icy Touch, Frost Presence, 797, Empower Rune Weapon.
STOCK_COSTS = {
    241: {"ID": 241, "Blood": 0, "Unholy": 0, "Frost": 1, "RunicPower": 100},
    482: {"ID": 482, "Blood": 0, "Unholy": 0, "Frost": 1, "RunicPower": 0},
    797: {"ID": 797, "Blood": 0, "Unholy": 1, "Frost": 1, "RunicPower": 150},
    1144: {"ID": 1144, "Blood": 0, "Unholy": 0, "Frost": 0, "RunicPower": 250},
}

CLASS_FILE = '''
from lib.dsl.registry import spell_rune_cost

spell_rune_cost(2600, unholy=1, frost=1, runic_power=20, comment="Marrowrend")
spell_rune_cost(2601, blood=1, frost=1, runic_power=15)
'''


def _load(body: str = CLASS_FILE, ids_cfg=IDS_CFG) -> dict:
    return load_dsl(body, ids_cfg=ids_cfg)


def _raises(call: str, pattern: str, exc=ValueError) -> None:
    with unittest.TestCase().assertRaisesRegex(exc, pattern):
        _load(f"from lib.dsl.registry import spell_rune_cost\n{call}\n")


class HelperTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()

    def test_runic_power_is_stored_times_ten(self):
        row = {r["ID"]: r for r in self.dsl["spell_rune_costs"]}[2600]
        self.assertEqual(row["RunicPower"], 200)

    def test_the_row_is_blood_unholy_frost(self):
        row = {r["ID"]: r for r in self.dsl["spell_rune_costs"]}[2600]
        self.assertEqual((row["Blood"], row["Unholy"], row["Frost"]), (0, 1, 1))
        row = {r["ID"]: r for r in self.dsl["spell_rune_costs"]}[2601]
        self.assertEqual((row["Blood"], row["Unholy"], row["Frost"], row["RunicPower"]), (1, 0, 1, 150))
        self.assertEqual(row["id"], 2601)

    def test_the_table_columns_are_in_dbc_order(self):
        self.assertEqual(COLUMNS, ("ID", "Blood", "Unholy", "Frost", "RunicPower"))

    def test_the_arguments_are_keyword_only(self):
        with self.assertRaises(TypeError):
            _load("from lib.dsl.registry import spell_rune_cost\nspell_rune_cost(2602, 1, 1, 0, 20)\n")

    def test_id_outside_the_block_raises(self):
        for cost_id in (241, 2599, 2630, 99999):
            with self.subTest(cost_id=cost_id):
                _raises(f"spell_rune_cost({cost_id}, frost=1)", "outside source/ids.yaml's spellrunecost")

    def test_a_missing_block_raises(self):
        with self.assertRaisesRegex(ValueError, "needs source/ids.yaml's `spellrunecost` block"):
            _load("from lib.dsl.registry import spell_rune_cost\nspell_rune_cost(2600, frost=1)\n", ids_cfg={})

    def test_rune_counts_outside_0_to_2_raise(self):
        for kwarg in ("blood", "unholy", "frost"):
            for bad in (3, -1):
                with self.subTest(kwarg=kwarg, bad=bad):
                    _raises(f"spell_rune_cost(2600, {kwarg}={bad})", f"{kwarg} must be an int in 0..2")

    def test_non_int_and_bool_raise(self):
        for bad in ("1", 1.0, True, None):
            with self.subTest(bad=bad):
                _raises(f"spell_rune_cost(2600, frost={bad!r})", "frost must be an int")
                _raises(f"spell_rune_cost(2600, frost=1, runic_power={bad!r})", "runic_power must be a whole int")
        _raises("spell_rune_cost('2600', frost=1)", "outside source/ids.yaml's spellrunecost")
        _raises("spell_rune_cost(True, frost=1)", "outside source/ids.yaml's spellrunecost")

    def test_runic_power_outside_0_to_100_raises(self):
        for bad in (-1, 101, 250):
            with self.subTest(bad=bad):
                _raises(f"spell_rune_cost(2600, frost=1, runic_power={bad})", "runic_power must be a whole int")

    def test_the_maximum_100_rp_is_allowed(self):
        dsl = _load("from lib.dsl.registry import spell_rune_cost\nspell_rune_cost(2600, runic_power=100)\n")
        self.assertEqual(dsl["spell_rune_costs"][0]["RunicPower"], 1000)

    def test_an_all_zero_row_raises(self):
        _raises("spell_rune_cost(2600)", "all-zero row is a free cast")

    def test_outside_a_load_the_helper_raises(self):
        with self.assertRaises(RuntimeError):
            registry.spell_rune_cost(2600, frost=1)

    def test_the_same_id_twice_is_a_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text(
                    "from lib.dsl.registry import spell_rune_cost\nspell_rune_cost(2600, frost=1)\n"
                )
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), ids_cfg=IDS_CFG)

    def test_the_docstring_states_the_trap_and_the_units(self):
        doc = registry.spell_rune_cost.__doc__
        self.assertIn("DBCStructure.h:1843", doc)
        self.assertIn("Blood, Unholy, Frost", doc)
        self.assertIn("x10", doc)
        self.assertIn("PowerType", doc)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load()
        self.block = render(TABLE, index_for(TABLE, []), self.dsl["spell_rune_costs"])

    def test_the_row_renders_delete_then_insert_in_blood_unholy_frost_order(self):
        self.assertTrue(self.block.startswith("DELETE FROM `spellrunecost_dbc` WHERE (`ID`) IN ("))
        self.assertIn(
            "INSERT INTO `spellrunecost_dbc` (`ID`, `Blood`, `Unholy`, `Frost`, `RunicPower`) VALUES", self.block,
        )
        self.assertIn("(2600, 0, 1, 1, 200)", self.block)
        self.assertIn("(2601, 1, 0, 1, 150)", self.block)

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        done = codestyle_sql(self.block)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_declaration_equal_to_live_is_not_re_emitted(self):
        live = [{"ID": 2600, "Blood": 0, "Unholy": 1, "Frost": 1, "RunicPower": 200}]
        rows = index_for(TABLE, live).rows_to_emit(spec_for(TABLE), self.dsl["spell_rune_costs"])
        self.assertEqual([r["ID"] for r in rows], [2601])


class ConvergenceTest(unittest.TestCase):
    """Hunter T1-1: what is rendered must be read back by the reader the diff uses, so a rerun emits nothing."""

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, []), dsl["spell_rune_costs"])
        self.assertTrue(first)
        live = read_back(first, TABLE, COLUMNS)
        self.assertEqual({r["ID"] for r in live}, {2600, 2601})
        self.assertEqual(render(TABLE, index_for(TABLE, live), dsl["spell_rune_costs"]), "")

    def test_the_generated_file_replay_sees_the_emitted_rows(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, []), dsl["spell_rune_costs"])
        with generated_file(first):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        self.assertEqual({r["ID"] for r in emitted}, {2600, 2601})

    def test_a_dropped_declaration_is_pruned(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, []), dsl["spell_rune_costs"])
        with generated_file(first):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        index = index_for(TABLE, emitted, emitted=emitted)
        kept = [r for r in dsl["spell_rune_costs"] if r["ID"] == 2601]
        result = index.rows_to_prune(spec_for(TABLE), kept)
        self.assertEqual(result.keys, [(2600.0,)])
        self.assertEqual(result.base_blocked, [])

    def test_dropping_the_last_declaration_still_prunes_the_table(self):
        dsl = _load()
        first = render(TABLE, index_for(TABLE, []), dsl["spell_rune_costs"])
        with generated_file(first):
            emitted = spell_tables.load_generated_table_rows(TABLE, spec_for(TABLE).key_columns)
        result = index_for(TABLE, emitted, emitted=emitted).rows_to_prune(spec_for(TABLE), [])
        self.assertEqual(result.keys, [(2600.0,), (2601.0,)])
        self.assertFalse(result.breaker_tripped)


@unittest.skipUnless(STOCK_FILE.is_file(), "var/extractors/dbc/SpellRuneCost.dbc is not extracted")
class ClientMergeTest(unittest.TestCase):
    def test_the_stock_file_has_the_rows_the_handoff_quotes(self):
        stock = {r["ID"]: r for r in dbcfile.read_dbc(STOCK_FILE, dbcfmt.SPELLRUNECOST)}
        self.assertEqual(len(stock), 475)
        self.assertEqual(max(stock), 2513)
        for cost_id, expected in STOCK_COSTS.items():
            self.assertEqual(stock[cost_id], expected)

    def test_the_merged_file_round_trips_the_declared_row_and_keeps_every_stock_row(self):
        dsl = _load()
        base_rows = dbcfile.read_dbc(STOCK_FILE, dbcfmt.SPELLRUNECOST)
        merged = {row["ID"]: row for row in base_rows}
        declared = generate._spell_rune_cost_rows(dsl["spell_rune_costs"])
        merged.update(declared)
        packed = dbcfile.pack_client_dbc(dbcfmt.SPELLRUNECOST, list(merged.values()), base_rows)
        with tempfile.TemporaryDirectory() as d:
            copy = Path(d) / "SpellRuneCost.dbc"
            copy.write_bytes(packed)
            back = {r["ID"]: r for r in dbcfile.read_dbc(copy, dbcfmt.SPELLRUNECOST)}
        self.assertEqual(len(back), 475 + 2)
        self.assertEqual(back[2600], {"ID": 2600, "Blood": 0, "Unholy": 1, "Frost": 1, "RunicPower": 200})
        for row in base_rows:
            self.assertEqual(back[row["ID"]], row)
        # an empty merge reproduces the stock file byte for byte (the file is all integers)
        self.assertEqual(
            dbcfile.pack_client_dbc(dbcfmt.SPELLRUNECOST, base_rows, base_rows), STOCK_FILE.read_bytes(),
        )


class BaseErrorTest(unittest.TestCase):
    def test_declared_rows_without_a_stock_file_name_the_file(self):
        rows = generate._spell_rune_cost_rows(_load()["spell_rune_costs"])
        with tempfile.TemporaryDirectory() as d:
            message = generate._spell_rune_cost_base_error(rows, Path(d))
        self.assertIn("spell_rune_cost() declared (2600, 2601)", message)
        self.assertIn("SpellRuneCost.dbc", message)
        self.assertIn("ac-worldserver", message)

    def test_no_declaration_or_a_present_file_is_fine(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(generate._spell_rune_cost_base_error({}, Path(d)))
            (Path(d) / "SpellRuneCost.dbc").write_bytes(b"")
            rows = generate._spell_rune_cost_rows(_load()["spell_rune_costs"])
            self.assertIsNone(generate._spell_rune_cost_base_error(rows, Path(d)))

    def test_the_rows_are_the_dbc_shape(self):
        rows = generate._spell_rune_cost_rows(_load()["spell_rune_costs"])
        self.assertEqual(rows[2601], {"ID": 2601, "Blood": 1, "Unholy": 0, "Frost": 1, "RunicPower": 150})


def _entry(spell_id: int, cost_id: int | None, power_type: int = 5, name: str = "Test") -> tuple[dict, dict]:
    raw = {} if cost_id is None else {"RuneCostID": cost_id}
    return (
        {"id": spell_id, "name": name, "raw_overrides": raw, "power_type": power_type},
        {"ID": spell_id, "RuneCostID": cost_id or 0, "PowerType": power_type},
    )


class UndeclaredCostLintTest(unittest.TestCase):
    BLOCK = IDS_CFG["spellrunecost"]

    def test_a_cost_in_the_block_without_a_declaration_is_an_error(self):
        entry, _ = _entry(203125, 2602)
        errors = lint.check_undeclared_spell_rune_costs([entry], {2600, 2601}, self.BLOCK)
        self.assertEqual(len(errors), 1)
        self.assertIn("RuneCostID 2602", errors[0])
        self.assertIn("spell_rune_cost(2602)", errors[0])

    def test_a_declared_cost_is_silent(self):
        entry, _ = _entry(203125, 2600)
        self.assertEqual(lint.check_undeclared_spell_rune_costs([entry], {2600}, self.BLOCK), [])

    def test_a_stock_cost_outside_the_block_is_never_checked(self):
        entry, _ = _entry(203125, 241)
        self.assertEqual(lint.check_undeclared_spell_rune_costs([entry], set(), self.BLOCK), [])

    def test_no_cost_and_no_block_are_silent(self):
        entry, _ = _entry(203125, None)
        self.assertEqual(lint.check_undeclared_spell_rune_costs([entry], set(), self.BLOCK), [])
        entry, _ = _entry(203125, 2602)
        self.assertEqual(lint.check_undeclared_spell_rune_costs([entry], set(), None), [])

    def test_the_generate_helper_wires_the_block_and_the_declarations(self):
        entry, _ = _entry(203125, 2602)
        dsl_classes = {"spell_rune_costs": _load()["spell_rune_costs"]}
        errors = generate._rune_cost_errors([entry], dsl_classes, IDS_CFG)
        self.assertTrue(any("RuneCostID 2602" in e for e in errors))
        entry, _ = _entry(203125, 2600)
        self.assertEqual(
            [e for e in generate._rune_cost_errors([entry], dsl_classes, IDS_CFG) if "RuneCostID" in e], [],
        )


class CostWarningLintTest(unittest.TestCase):
    DECLARED = [
        {"ID": 2600, "Blood": 0, "Unholy": 1, "Frost": 1, "RunicPower": 200},
        {"ID": 2601, "Blood": 1, "Unholy": 0, "Frost": 1, "RunicPower": 150},
    ]

    def _run(self, pairs, stock=STOCK_COSTS, declared=None):
        entries = [p[0] for p in pairs]
        rows = [p[1] for p in pairs]
        return lint.check_spell_rune_costs(entries, rows, stock, self.DECLARED if declared is None else declared)

    def test_a_cost_on_a_non_rune_spell_warns(self):
        warnings = self._run([_entry(203125, 2600, power_type=0)])
        self.assertEqual(len(warnings), 1)
        self.assertIn("PowerType 0", warnings[0])
        self.assertIn("ignored", warnings[0])

    def test_a_cost_on_a_rune_spell_is_silent(self):
        self.assertEqual(self._run([_entry(203125, 2600), _entry(203126, 241)]), [])

    def test_a_spell_without_a_cost_is_silent_whatever_its_power_type(self):
        self.assertEqual(self._run([_entry(203125, None, power_type=5), _entry(203126, None, power_type=0)]), [])

    def test_stock_death_coil_with_power_6_and_cost_422_is_silent(self):
        # 168 stock spells carry a RuneCostID with another PowerType: inert, only custom ids are linted
        entry = {"id": 47541, "name": "Death Coil", "raw_overrides": {"RuneCostID": 422}}
        row = {"ID": 47541, "RuneCostID": 422, "PowerType": 6}
        self.assertEqual(lint.check_spell_rune_costs([entry], [row], STOCK_COSTS, []), [])

    def test_an_unknown_cost_id_warns_as_a_free_cast(self):
        warnings = self._run([_entry(203125, 2605)])
        self.assertEqual(len(warnings), 1)
        self.assertIn("RuneCostID 2605", warnings[0])
        self.assertIn("free", warnings[0])

    def test_a_stock_or_declared_cost_id_is_known(self):
        self.assertEqual(self._run([_entry(203125, 797), _entry(203126, 2601)]), [])

    def test_a_declared_row_equal_to_a_stock_row_names_the_stock_id(self):
        declared = [{"ID": 2602, "Blood": 0, "Unholy": 0, "Frost": 1, "RunicPower": 100}]
        warnings = self._run([_entry(203125, 2602)], declared=declared)
        self.assertEqual(len(warnings), 1)
        self.assertIn("stock SpellRuneCost row 241", warnings[0])
        self.assertIn("RuneCostID 241", warnings[0])

    def test_a_declared_row_that_is_new_is_silent(self):
        self.assertEqual(self._run([_entry(203125, 2600)]), [])

    def test_without_the_stock_file_one_warning_and_no_per_spell_noise(self):
        pairs = [_entry(203125, 2600), _entry(203126, 2601), _entry(203127, 2605)]
        warnings = self._run(pairs, stock=None)
        self.assertEqual(len(warnings), 1)
        self.assertIn("no stock SpellRuneCost.dbc", warnings[0])

    def test_without_the_stock_file_and_nothing_to_judge_it_is_silent(self):
        self.assertEqual(self._run([_entry(203125, None)], stock=None, declared=[]), [])

    def test_the_power_type_warning_survives_a_missing_stock_file(self):
        warnings = self._run([_entry(203125, 2600, power_type=0)], stock=None)
        self.assertEqual(len(warnings), 2)
        self.assertIn("PowerType 0", warnings[0])

    def test_stock_spells_below_the_custom_block_are_not_linted(self):
        entry = {"id": 49998, "name": "Death Strike", "raw_overrides": {"RuneCostID": 99999}}
        row = {"ID": 49998, "RuneCostID": 99999, "PowerType": 0}
        self.assertEqual(lint.check_spell_rune_costs([entry], [row], STOCK_COSTS, []), [])


class SpikeSpellsTest(unittest.TestCase):
    """The P0 spike's spells set RuneCostID 0 (PowerType 5, no cost, D5): no rune lint fires on them."""

    SPIKE_FILE = TOOL_ROOT / "source" / "classes" / "deathknight" / "deathknight_p0_spike.py"

    @unittest.skipUnless(SPIKE_FILE.is_file(), "the P0 spike package is gone")
    def test_the_spike_spells_are_silent(self):
        from lib.test_id_blocks import _AnyRows, _AnySet, _AnyTrainer  # noqa: PLC0415

        ids = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        reg = registry.load_class_package(
            TOOL_ROOT / "source" / "classes" / "deathknight", ids_cfg=ids, trainer_index=_AnyTrainer(),
            existing_group_ids=_AnySet(), shapeshift_index={}, existing_creature_rows=_AnyRows(),
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.dsl_live_data(state.load_stock_rows(dbcfmt.TALENT), {}),
        )
        spikes = [e for e in reg.spells if 203680 <= int(e["id"]) <= 203699]
        self.assertTrue(spikes)
        reuse = ReuseContext(
            {name: list(state.load_stock_rows(table).values()) for name, table in generate.SECONDARY_TABLES.items()},
            ids,
        )
        rows = [build.build_spell_row(e, reuse) for e in spikes]
        self.assertTrue(all(int(r["RuneCostID"]) == 0 for r in rows))
        self.assertEqual(lint.check_spell_rune_costs(spikes, rows, STOCK_COSTS, []), [])
        self.assertEqual(lint.check_undeclared_spell_rune_costs(spikes, set(), IDS_CFG["spellrunecost"]), [])


if __name__ == "__main__":
    unittest.main()
