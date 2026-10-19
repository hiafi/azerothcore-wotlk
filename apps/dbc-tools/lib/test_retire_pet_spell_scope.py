"""
retire_pet_spell() scoped to families, CreatureSpellData record shared with a family that keeps the spell
(hunter-rework H0-P1 review P1-3). Fixtures only.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_retire_pet_spell_scope.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, superseded_ranks as sr  # noqa: E402

LEARN = sr.SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN
BITE, SPIT = 17253, 24455
WOLF, CHIMAERA = 1, 38
WOLF_LINE, CHIMAERA_LINE, SHARED = 208, 767, 270
LINES = {WOLF: (WOLF_LINE, SHARED), CHIMAERA: (CHIMAERA_LINE, SHARED)}


def _sla(row_id: int, spell: int, line: int, acquire: int = LEARN) -> dict:
    row = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
    row.update(ID=row_id, SkillLine=line, Spell=spell, AcquireMethod=acquire)
    return row


def _csd(row_id: int, *spells: int) -> dict:
    row = dbcfile.empty_row(dbcfmt.CREATURESPELLDATA)
    for i, spell in enumerate(spells, start=1):
        row[f"Spells_{i}"] = spell
        row[f"Availability_{i}"] = 100
    row["ID"] = row_id
    return row


CREATURES = {
    1: {"family": WOLF, "PetSpellDataId": 5953},
    2: {"family": CHIMAERA, "PetSpellDataId": 5953},
}
STOCK = {5953: _csd(5953, 17259, 24603)}
SUPERSEDED = {17259: BITE}
RETIREMENT = [{"id": "bite", "spell_id": BITE, "families": (CHIMAERA,)}]


def _strips(effective: dict[int, dict]):
    return sr.spell_data_strips(RETIREMENT, CREATURES, STOCK, SUPERSEDED, LINES, effective)


class SharedRecordStripTest(unittest.TestCase):
    def test_wolf_keeps_bite_so_the_shared_record_is_stripped_silently(self):
        effective = {1: _sla(1, BITE, WOLF_LINE), 2: _sla(2, BITE, CHIMAERA_LINE, acquire=0)}
        strips, warnings = _strips(effective)
        self.assertEqual(strips, {5953: {BITE}})
        self.assertEqual(warnings, [])
        applied = sr.creaturespelldata_overrides(SUPERSEDED, STOCK, strips=strips).rows
        self.assertEqual([r["Spells_1"] for r in applied if r["ID"] == 5953], [0])

    def test_wolf_learning_bite_on_the_shared_line_counts(self):
        strips, warnings = _strips({1: _sla(1, BITE, SHARED)})
        self.assertEqual((strips, warnings), ({5953: {BITE}}, []))

    def test_other_family_without_bite_in_its_level_up_set_still_warns(self):
        # the wolf's row is retired too (AcquireMethod 0): stripping would take Bite from wolves entirely
        effective = {1: _sla(1, BITE, WOLF_LINE, acquire=0)}
        strips, warnings = _strips(effective)
        self.assertEqual(strips, {})
        self.assertEqual(len(warnings), 1)
        self.assertIn("CreatureSpellData 5953", warnings[0])

    def test_other_family_teaching_a_different_spell_still_warns(self):
        strips, warnings = _strips({1: _sla(1, SPIT, WOLF_LINE)})
        self.assertEqual((strips, len(warnings)), ({}, 1))

    def test_without_the_context_behaviour_is_unchanged(self):
        strips, warnings = sr.spell_data_strips(RETIREMENT, CREATURES, STOCK, SUPERSEDED)
        self.assertEqual((strips, len(warnings)), ({}, 1))

    def test_every_other_family_must_keep_it(self):
        creatures = {**CREATURES, 3: {"family": 5, "PetSpellDataId": 5953}}
        lines = {**LINES, 5: (210,)}
        effective = {1: _sla(1, BITE, WOLF_LINE)}   # family 5 has no Bite row
        strips, warnings = sr.spell_data_strips(RETIREMENT, creatures, STOCK, SUPERSEDED, lines, effective)
        self.assertEqual((strips, len(warnings)), ({}, 1))
        effective[2] = _sla(2, BITE, 210)
        strips, warnings = sr.spell_data_strips(RETIREMENT, creatures, STOCK, SUPERSEDED, lines, effective)
        self.assertEqual((strips, warnings), ({5953: {BITE}}, []))


if __name__ == "__main__":
    unittest.main()
