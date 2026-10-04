"""
Retribution inert-key pytest (RETRIBUTION §12; druid `test_druid_inert_keys.py` shape).

Stock paladin hardcodes are neutralized by keeping the data they key on absent, not by editing the
C++. This loads the real paladin DSL (source/classes/paladin/) and asserts none came back:

- 201407 (Echoing Vengeance) and the Vengeance unleash DoTs 201071 / 201077 never combine icon 2292
  with SpellClassMask dword 1 bit 0x400000 (the Judgement of Vengeance DoT hardcode);
- no PASSIVE spell this rework mints (id >= 200000) uses spell icon 25 (stock pulled rows such as
  Seals of the Pure 20224-20332 and Seal of Righteousness 21084 legitimately keep their stock icon);
- Vindication ranks 9452 / 26016 / 201466 never trigger 26017 or 67 (the stock Vindication debuff);
- 31884 (Avenging Wrath) carries no `spell_pal_avenging_wrath` binding - the stock rider fires on any
  Sanctified Wrath EFFECT_2 - and the stock row's removal is declared.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_paladin_ret_inert_keys.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_paladin_spellmod_family import _load_paladin_package  # noqa: E402

JOV_ICON = 2292
JOV_D1_BIT = 0x400000  # SpellClassMask_2 (dword 1)
PASSIVE_ICON_25 = 25
ATTR_PASSIVE = 0x40
VINDICATION_RANKS = (9452, 26016, 201466)
STOCK_VINDICATION_DEBUFFS = {26017, 67}
AVENGING_WRATH = 31884
AW_STOCK_SCRIPT = "spell_pal_avenging_wrath"
CUSTOM_SPELL_ID_MIN = 200000


def _effects(entry: dict):
    for key in ("effect1", "effect2", "effect3"):
        eff = entry.get(key)
        if eff is not None:
            yield eff


def _attributes(entry: dict) -> int:
    return int((entry.get("raw_overrides") or {}).get("Attributes", entry.get("attributes", 0)) or 0)


def _spell_id_of_row(row: dict) -> int:
    return abs(int(row["spell_id"]))


class RetInertKeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_paladin_package()
        cls.by_id = {e["id"]: e for e in cls.reg.spells}

    def test_vengeance_dots_avoid_jov_hardcode(self):
        for spell_id in (201407, 201071, 201077):
            entry = self.by_id.get(spell_id)
            if entry is None:
                continue
            raw = entry.get("raw_overrides") or {}
            if entry.get("spell_icon_id") == JOV_ICON and raw.get("SpellClassMask_2", 0) & JOV_D1_BIT:
                self.fail(f"spell {spell_id} carries icon {JOV_ICON} with d1 {JOV_D1_BIT:#x} (JoV hardcode)")

    def test_no_paladin_passive_uses_icon_25(self):
        for entry in self.reg.spells:
            if entry["id"] >= CUSTOM_SPELL_ID_MIN and entry.get("spell_icon_id") == PASSIVE_ICON_25 and _attributes(entry) & ATTR_PASSIVE:
                self.fail(f"passive spell {entry['id']} ({entry.get('name')}) uses icon {PASSIVE_ICON_25}")

    def test_vindication_does_not_trigger_stock_debuffs(self):
        for spell_id in VINDICATION_RANKS:
            entry = self.by_id.get(spell_id)
            if entry is None:
                continue
            for eff in _effects(entry):
                self.assertNotIn(
                    eff.get("trigger_spell"), STOCK_VINDICATION_DEBUFFS,
                    f"Vindication rank {spell_id} triggers stock debuff {eff.get('trigger_spell')}",
                )

    def test_avenging_wrath_has_no_stock_script_binding(self):
        bound = [
            r for r in self.reg.spell_script_names
            if _spell_id_of_row(r) == AVENGING_WRATH and r["ScriptName"] == AW_STOCK_SCRIPT
        ]
        self.assertEqual(bound, [], f"{AW_STOCK_SCRIPT} is still declared on {AVENGING_WRATH}")
        removed = [
            r for r in self.reg.script_removals
            if _spell_id_of_row(r) == AVENGING_WRATH and r["ScriptName"] == AW_STOCK_SCRIPT
        ]
        self.assertTrue(removed, f"unbind_script({AVENGING_WRATH}, {AW_STOCK_SCRIPT!r}) is not declared")


if __name__ == "__main__":
    unittest.main()
