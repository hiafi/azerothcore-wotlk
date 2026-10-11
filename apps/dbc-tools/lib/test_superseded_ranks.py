"""
Superseded-rank SkillLineAbility and CreatureSpellData override tests (lib/superseded_ranks.py,
.agents/plans/pet-stale-ranks/pet-stale-ranks.PLAN.md Part A and the review's B1/S1). Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_superseded_ranks.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, sql_dump, sql_out, superseded_ranks  # noqa: E402

LEARN = superseded_ranks.SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN

# Imp Firebolt: 3110 survives, 7799/7800 are superseded. Shadow Bolt 686 has no tagged survivor.
CHAINS = {
    3110: [(3110, 1), (7799, 2), (7800, 3)],
    686: [(686, 1), (695, 2)],
}
SPELLS = [
    {"id": 3110, "notes": "pulled from existing data; single-rank bootstrap: BasePoints kept from rank 1"},
    {"id": 686, "notes": "pulled from existing data"},
]


def _sla(row_id: int, spell: int, acquire: int, superseded_by: int = 0, skill_line: int = 188) -> dict:
    row = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
    row.update(
        ID=row_id, SkillLine=skill_line, Spell=spell, MinSkillLineRank=1, SupercededBySpell=superseded_by,
        AcquireMethod=acquire, TrivialSkillLineRankHigh=5, TrivialSkillLineRankLow=3,
    )
    return row


def _stock() -> dict[int, dict]:
    rows = [
        _sla(2487, 3110, LEARN, superseded_by=7799),  # survivor's own row
        _sla(4371, 7799, LEARN, superseded_by=7800),  # superseded, learned with the skill
        _sla(4372, 7800, 0),                           # superseded, not auto-learned
        _sla(500, 695, LEARN, skill_line=354),         # rank 2 of a chain with no survivor
    ]
    return {r["ID"]: r for r in rows}


class SupersededRanksTest(unittest.TestCase):
    def test_superseded_ranks_map_to_the_tagged_survivor(self):
        survivors = superseded_ranks.survivor_ids(SPELLS)
        self.assertEqual(survivors, {3110})
        self.assertEqual(superseded_ranks.superseded_ranks(CHAINS, survivors), {7799: 3110, 7800: 3110})

    def test_superseded_learn_on_skill_row_is_overridden(self):
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, _stock(), [])
        self.assertEqual([e["id"] for e in result.entries], [4371])

    def test_override_is_the_stock_row_with_acquire_method_zero(self):
        stock = _stock()
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, stock, [])
        built = build.build_skilllineability_row(result.entries[0])
        self.assertEqual(built, {**stock[4371], "AcquireMethod": 0})

    def test_survivor_row_untouched(self):
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, _stock(), [])
        self.assertNotIn(2487, [e["id"] for e in result.entries])

    def test_acquire_method_zero_untouched(self):
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, _stock(), [])
        self.assertNotIn(4372, [e["id"] for e in result.entries])

    def test_chain_without_survivor_untouched(self):
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, _stock(), [])
        self.assertNotIn(500, [e["id"] for e in result.entries])

    def test_declared_row_wins_and_is_reported(self):
        declared = [{"id": 4371, "skill_line": 188, "spell_id": 7799}]
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, _stock(), declared)
        self.assertEqual(result.entries, [])
        self.assertEqual(len(result.collisions), 1)
        self.assertIn("4371", result.collisions[0])

    def test_promoted_change_is_warned(self):
        stock = _stock()
        existing = {**stock, 4371: {**stock[4371], "MinSkillLineRank": 7}}
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, stock, [], existing)
        self.assertEqual([e["id"] for e in result.entries], [4371])
        self.assertEqual(len(result.warnings), 1)

    def test_unchanged_existing_is_silent(self):
        stock = _stock()
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, stock, [], dict(stock))
        self.assertEqual(result.warnings, [])

    def test_promoted_override_is_silent(self):
        # Review S1: once a migration carrying the override is promoted, existing_rows reads it back.
        stock = _stock()
        existing = {**stock, 4371: {**stock[4371], "AcquireMethod": 0}}
        result = superseded_ranks.skilllineability_overrides(CHAINS, SPELLS, stock, [], existing)
        self.assertEqual([e["id"] for e in result.entries], [4371])
        self.assertEqual(result.warnings, [])


SUPERSEDED = {7799: 3110, 7800: 3110, 16829: 16827}


def _csd(row_id: int, *spells: int) -> dict:
    row = dbcfile.empty_row(dbcfmt.CREATURESPELLDATA)
    for i, spell in enumerate(spells, start=1):
        row[f"Spells_{i}"] = spell
        row[f"Availability_{i}"] = 100
    row["ID"] = row_id
    return row


def _csd_stock() -> dict[int, dict]:
    rows = [
        _csd(9477, 16829, 24450),  # Ghost Saber: Claw rank 3 + Prowl survivor
        _csd(5943, 17253),         # survivor only
        _csd(100, 7799, 7800),     # two superseded ranks of one chain
    ]
    return {r["ID"]: r for r in rows}


class CreatureSpellDataOverridesTest(unittest.TestCase):
    def test_superseded_rank_becomes_survivor(self):
        stock = _csd_stock()
        result = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock)
        self.assertEqual([r["ID"] for r in result.rows], [100, 9477])
        self.assertEqual(result.rows[1], {**stock[9477], "Spells_1": 16827})
        self.assertEqual(result.rows[0], {**stock[100], "Spells_1": 3110, "Spells_2": 3110})

    def test_availability_and_other_slots_stay_stock(self):
        stock = _csd_stock()
        row = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock).rows[1]
        for column in ("Spells_2", "Spells_3", "Spells_4", *(f"Availability_{i}" for i in range(1, 5))):
            self.assertEqual(row[column], stock[9477][column])

    def test_record_without_superseded_rank_untouched(self):
        result = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, _csd_stock())
        self.assertNotIn(5943, [r["ID"] for r in result.rows])

    def test_not_live_rows_are_emitted(self):
        stock = _csd_stock()
        result = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock, dict(stock))
        self.assertEqual(result.to_emit, result.rows)
        self.assertEqual(result.warnings, [])

    def test_promoted_block_is_silent_and_emits_nothing(self):
        # Round trip through the block generate.py writes and the replay state.load_existing_rows uses.
        stock = _csd_stock()
        first = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock, dict(stock))
        table = dbcfmt.CREATURESPELLDATA
        block = sql_out.render_generic_table_block(table.sql_table, table.columns, ("ID",), first.to_emit)
        existing = {k: dict(v) for k, v in stock.items()}
        sql_dump.apply_statements(existing, table, block)
        rerun = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock, existing)
        self.assertEqual(rerun.rows, first.rows)
        self.assertEqual(rerun.to_emit, [])
        self.assertEqual(rerun.warnings, [])

    def test_promoted_change_is_warned(self):
        stock = _csd_stock()
        existing = {**stock, 9477: {**stock[9477], "Spells_2": 1}}
        result = superseded_ranks.creaturespelldata_overrides(SUPERSEDED, stock, existing)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("9477", result.warnings[0])
        self.assertIn(9477, [r["ID"] for r in result.to_emit])


if __name__ == "__main__":
    unittest.main()
