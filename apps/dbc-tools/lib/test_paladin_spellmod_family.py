"""
Paladin SpellMod family gate (RETRIBUTION §3 item 10, REVIEW X3).

`SpellInfo::IsAffected` returns true for every spell when a SpellMod's `SpellFamilyName` is 0
(SpellInfo.cpp:1359-1371), so a paladin aura-107/108 carrier left at `SpellClassSet 0` leaks into
every spell in the game. `check_classmask_scoping` only catches an all-zero mask. This loads the
real paladin DSL (source/classes/paladin/) and asserts every declared spell with an
ADD_FLAT_MODIFIER (107) / ADD_PCT_MODIFIER (108) effect has `SpellClassSet == 10`.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_paladin_spellmod_family.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
PALADIN_DIR = TOOL_ROOT / "source" / "classes" / "paladin"

SPELLFAMILY_PALADIN = 10
SPELLMOD_AURAS = {107, 108}  # ADD_FLAT_MODIFIER, ADD_PCT_MODIFIER


def _load_paladin_package():
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    spell_table_index = spell_tables.load_spell_table_index()
    return registry.load_class_package(
        PALADIN_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
        existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
        shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
    )


def _spellmod_carriers_without_family(entries: list[dict]) -> list[tuple[int, str, object]]:
    bad = []
    for entry in entries:
        carries = any(
            (eff := entry.get(key)) is not None and eff.get("apply_aura") in SPELLMOD_AURAS
            for key in ("effect1", "effect2", "effect3")
        )
        family = (entry.get("raw_overrides") or {}).get("SpellClassSet", 0)
        if carries and family != SPELLFAMILY_PALADIN:
            bad.append((entry["id"], entry.get("name", "?"), family))
    return bad


class PaladinSpellModFamilyTest(unittest.TestCase):
    def test_every_spellmod_carrier_is_paladin_family(self):
        bad = _spellmod_carriers_without_family(_load_paladin_package().spells)
        self.assertEqual(
            bad, [],
            "aura 107/108 carriers with SpellClassSet != 10 match every spell in the game "
            "(SpellInfo::IsAffected, family 0): " + ", ".join(f"{i} {n} (set {f})" for i, n, f in bad),
        )

    def test_gate_catches_a_family_zero_carrier(self):
        carrier = {"id": 1, "name": "x", "effect1": {"apply_aura": 107}, "raw_overrides": {}}
        fixed = {"id": 2, "name": "y", "effect2": {"apply_aura": 108}, "raw_overrides": {"SpellClassSet": 10}}
        other = {"id": 3, "name": "z", "effect1": {"apply_aura": 4}, "raw_overrides": {}}
        self.assertEqual(_spellmod_carriers_without_family([carrier, fixed, other]), [(1, "x", 0)])


if __name__ == "__main__":
    unittest.main()
