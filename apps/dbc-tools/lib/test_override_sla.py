"""
override_skill_line_ability() (Death Knight T1, step 5): re-declare a live SkillLineAbility row with only the named
columns changed.

Covered, per the handoff: equivalence with the P0 spike's hand-built `_stock_sla_unlearned` rows (the five stock rows
at AcquireMethod 0), 19182 -> `acquire_method=2, class_mask=32` changes those two columns only, an unknown column or
id raises, a missing live bundle raises, and the entry is exactly what skill_line_ability() builds (so the
superseded-ranks "a declared row wins" path keeps working).

The live rows here are the stock client file (the spike copied its columns from the deployed file, and no migration
touches these five ids); tests that need it are skipped when var/extractors/dbc/SkillLineAbility.dbc is missing.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_override_sla.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, source, spell_tables, state, superseded_ranks  # noqa: E402
from lib.table_testkit import load_dsl  # noqa: E402
from lib.dsl import registry  # noqa: E402

STOCK_FILE = state.BASE_DBC_DIR / dbcfmt.SKILLLINEABILITY.dbc_filename
SPIKE_DIR = TOOL_ROOT / "source" / "classes" / "deathknight"
SPIKE_FILE = SPIKE_DIR / "deathknight_p0_spike.py"
SPIKE_IDS = (16231, 16433, 17101, 17016, 19184)  # Icy Touch, Death Coil, Death Grip, Blood Presence, Riding

# A minimal live row, for the tests that do not need the real file.
ROW = {
    "ID": 7, "SkillLine": 770, "Spell": 100, "RaceMask": 0, "ClassMask": 32, "ExcludeRace": 0, "ExcludeClass": 0,
    "MinSkillLineRank": 1, "SupercededBySpell": 101, "AcquireMethod": 2, "TrivialSkillLineRankHigh": 0,
    "TrivialSkillLineRankLow": 0, "CharacterPoints_1": 0, "CharacterPoints_2": 0,
}


def _bundle(rows: dict[int, dict] | None = None) -> dict:
    return spell_tables.dsl_live_data({}, {}, skilllineability_rows={7: ROW} if rows is None else rows)


def _override(call: str, rows: dict[int, dict] | None = None) -> list[dict]:
    dsl = load_dsl(f"from lib.dsl.registry import override_skill_line_ability\n{call}\n", live_data=_bundle(rows))
    return dsl["skill_line_abilities"]


def _built(entry: dict) -> dict:
    return build.build_skilllineability_row(entry)


class FixtureTest(unittest.TestCase):
    def test_only_the_named_columns_change(self):
        (entry,) = _override("override_skill_line_ability(7, acquire_method=0)")
        built = _built(entry)
        self.assertEqual({c for c in ROW if built[c] != ROW[c]}, {"AcquireMethod"})
        self.assertEqual(built["AcquireMethod"], 0)
        self.assertEqual(built["SupercededBySpell"], 101)

    def test_typed_and_raw_names_are_both_accepted(self):
        (typed,) = _override("override_skill_line_ability(7, class_mask=1, race_mask=2, min_skill_line_rank=5)")
        (raw,) = _override("override_skill_line_ability(7, ClassMask=1, RaceMask=2, MinSkillLineRank=5)")
        self.assertEqual(_built(typed), _built(raw))
        self.assertEqual((typed["class_mask"], typed["race_mask"], typed["min_skill_line_rank"]), (1, 2, 5))
        (entry,) = _override("override_skill_line_ability(7, superseded_by=0, ExcludeClass=9, skill_line=771)")
        built = _built(entry)
        self.assertEqual((built["SupercededBySpell"], built["ExcludeClass"], built["SkillLine"]), (0, 9, 771))

    def test_the_entry_is_what_skill_line_ability_builds(self):
        (entry,) = _override("override_skill_line_ability(7, acquire_method=0)")
        dsl = load_dsl(
            "from lib.dsl.registry import skill_line_ability\n"
            "skill_line_ability(id=7, skill_line=770, spell_id=100, class_mask=32, race_mask=0, min_skill_line_rank=1,"
            " acquire_method=0, superseded_by=101, raw_overrides={'ExcludeRace': 0, 'ExcludeClass': 0,"
            " 'TrivialSkillLineRankHigh': 0, 'TrivialSkillLineRankLow': 0, 'CharacterPoints_1': 0,"
            " 'CharacterPoints_2': 0})\n"
        )
        self.assertEqual(entry, dsl["skill_line_abilities"][0])

    def test_unknown_column_unknown_id_and_id_change_raise(self):
        with self.assertRaisesRegex(KeyError, "no such column"):
            _override("override_skill_line_ability(7, acquire=0)")
        with self.assertRaisesRegex(ValueError, "no live SkillLineAbility.dbc row with that ID"):
            _override("override_skill_line_ability(99999, acquire_method=0)")
        with self.assertRaisesRegex(ValueError, "ID column is the key"):
            _override("override_skill_line_ability(7, ID=8)")

    def test_the_base_is_the_stock_row_so_dropping_a_keyword_restores_it(self):
        promoted = {**ROW, "ClassMask": 32, "AcquireMethod": 2}  # a promoted override of the stock row
        stock = {**ROW, "ClassMask": 0, "AcquireMethod": 1}
        live = spell_tables.dsl_live_data(
            {}, {}, skilllineability_rows={7: promoted}, skilllineability_stock_rows={7: stock},
        )
        source_text = "from lib.dsl.registry import override_skill_line_ability\n{}\n"
        (kept,) = load_dsl(source_text.format("override_skill_line_ability(7, acquire_method=2)"), live_data=live)[
            "skill_line_abilities"
        ]
        self.assertEqual((_built(kept)["ClassMask"], _built(kept)["AcquireMethod"]), (0, 2))
        # a row only a migration added has no stock row: the live row is the base
        live_only = spell_tables.dsl_live_data(
            {}, {}, skilllineability_rows={7: promoted}, skilllineability_stock_rows={},
        )
        (entry,) = load_dsl(source_text.format("override_skill_line_ability(7, acquire_method=0)"), live_data=live_only)[
            "skill_line_abilities"
        ]
        self.assertEqual((_built(entry)["ClassMask"], _built(entry)["AcquireMethod"]), (32, 0))

    def test_a_missing_live_bundle_raises(self):
        source_text = "from lib.dsl.registry import override_skill_line_ability\noverride_skill_line_ability(7)\n"
        with self.assertRaisesRegex(RuntimeError, "override_skill_line_ability\\(\\) needs the live skilllineability"):
            load_dsl(source_text)
        with self.assertRaisesRegex(RuntimeError, "needs the live skilllineability rows"):
            load_dsl(source_text, live_data=spell_tables.dsl_live_data({}, {}))

    def test_outside_a_load_the_helper_raises(self):
        with self.assertRaises(RuntimeError):
            registry.override_skill_line_ability(7, acquire_method=0)

    def test_a_declared_row_wins_over_the_superseded_rank_override(self):
        (entry,) = _override("override_skill_line_ability(7, acquire_method=2)")
        chains = {100: [(100, 1), (101, 2)]}
        spells = [{"id": 101, "notes": "single-rank bootstrap"}]
        result = superseded_ranks.skilllineability_overrides(chains, spells, {7: ROW}, [entry])
        self.assertEqual(result.entries, [])
        self.assertEqual(len(result.collisions), 1)
        self.assertIn("declared in source", result.collisions[0])
        # without the declaration the pet-stale-ranks rule would have overridden the same id
        self.assertEqual(len(superseded_ranks.skilllineability_overrides(chains, spells, {7: ROW}, []).entries), 1)

    def test_the_lazy_bundle_entry_is_not_loaded_unless_the_helper_runs(self):
        def boom():
            raise AssertionError("the SkillLineAbility replay must not run when no file overrides a row")

        live = spell_tables.dsl_live_data({}, {}, skilllineability_rows=boom)
        load_dsl("from lib.dsl.registry import spell\nspell(id=200001, name='x', cast_time_ms=0)\n", live_data=live)

    def test_the_default_bundle_keeps_every_older_caller_working(self):
        live = spell_tables.dsl_live_data({}, {})
        self.assertIsNone(live["skilllineability_rows"])
        self.assertIsNone(live["chrclasses_rows"])
        self.assertEqual(set(live), {
            "talent_rows", "item_template_rows", "item_template_columns", "item_template_defaults",
            "skilllineability_rows", "chrclasses_rows", "skilllineability_stock_rows",
        })


@unittest.skipUnless(STOCK_FILE.is_file(), "var/extractors/dbc/SkillLineAbility.dbc is not extracted")
class StockRowsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stock = state.load_stock_rows(dbcfmt.SKILLLINEABILITY)

    def _entries(self, call: str) -> list[dict]:
        return _override(call, self.stock)

    @unittest.skipUnless(SPIKE_FILE.is_file(), "the P0 spike package is gone")
    def test_equivalent_to_the_spikes_hand_built_rows(self):
        from lib.test_id_blocks import _AnyRows, _AnySet, _AnyTrainer  # noqa: PLC0415

        reg = registry.load_class_package(
            SPIKE_DIR, ids_cfg=source.load_ids(TOOL_ROOT / "source" / "ids.yaml"), trainer_index=_AnyTrainer(),
            existing_group_ids=_AnySet(), shapeshift_index={}, existing_creature_rows=_AnyRows(),
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.dsl_live_data(state.load_stock_rows(dbcfmt.TALENT), {}),
        )
        hand = {e["id"]: e for e in reg.skill_line_abilities if e["id"] in SPIKE_IDS}
        self.assertEqual(set(hand), set(SPIKE_IDS))
        mine = {e["id"]: e for e in self._entries("\n".join(
            f"override_skill_line_ability({row_id}, acquire_method=0)" for row_id in SPIKE_IDS
        ))}
        self.assertEqual(set(mine), set(SPIKE_IDS))
        for row_id in SPIKE_IDS:
            with self.subTest(sla=row_id):
                self.assertEqual(_built(mine[row_id]), _built(hand[row_id]))
                self.assertEqual(mine[row_id], hand[row_id])  # typed fields and raw_overrides agree as well

    def test_every_override_differs_from_the_stock_row_in_acquire_method_only(self):
        for row_id in SPIKE_IDS:
            with self.subTest(sla=row_id):
                (entry,) = self._entries(f"override_skill_line_ability({row_id}, acquire_method=0)")
                built = _built(entry)
                stock = self.stock[row_id]
                self.assertLessEqual({c for c in stock if built[c] != stock[c]}, {"AcquireMethod"})
                self.assertEqual(built["AcquireMethod"], 0)

    def test_heart_strike_19182_changes_acquire_method_and_class_mask_only(self):
        stock = self.stock[19182]
        (entry,) = self._entries("override_skill_line_ability(19182, acquire_method=2, class_mask=32)")
        built = _built(entry)
        self.assertEqual(built["AcquireMethod"], 2)
        self.assertEqual(built["ClassMask"], 32)
        changed = {c for c in stock if built[c] != stock[c]}
        self.assertTrue(changed <= {"AcquireMethod", "ClassMask"}, changed)
        # the other columns, including the ones the typed names do not cover, are the stock values
        for column in ("ID", "SkillLine", "Spell", "RaceMask", "MinSkillLineRank", "SupercededBySpell",
                       "ExcludeRace", "ExcludeClass", "TrivialSkillLineRankHigh", "TrivialSkillLineRankLow"):
            self.assertEqual(built[column], stock[column], column)

    def test_a_nonexistent_row_raises(self):
        with self.assertRaisesRegex(ValueError, "no live SkillLineAbility.dbc row"):
            self._entries("override_skill_line_ability(1, acquire_method=0)")


if __name__ == "__main__":
    unittest.main()
