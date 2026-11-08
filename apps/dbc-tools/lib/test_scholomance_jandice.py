"""
Scholomance build WP-S1, Jandice Barov: source/npcs/scholomance/jandice_barov.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/JandiceLogic.h, boss_jandice_barov_rework.cpp).

Checks:
  - the spells sit in Jandice's slice (206110-206129) and JandiceLogic.h names the same ids;
  - 10503 is bound with SmartAI off, 175k normal health, stun immunity 1972, INSTANCE_BIND and DamageModifier 3.5;
  - the Shell Game copy 11439 looks exactly like her (name, class, flags, mana, immunity set, the same health on the
    template), stands still, never regenerates or melees, and runs npc_sc_shell_game_copy;
  - the Reflection 300530 sits in the `scholomance` creature slice, is not selectable or attackable, has her look and
    runs npc_sc_jandice_reflection;
  - Curse of Blood: a 2 s Curse, 10 yd, physical damage taken +20% for 30 s; Unmasked +20% for 8 s;
  - the damage spells ignore caster modifiers and are set by their scripts; the resolve copies are bound to the
    registry's resolve script; every script name a spell names is registered in the C++.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_jandice.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.test_scholomance_kit import _load  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "JandiceLogic.h"
SCRIPT = MODULE_DIR / "boss_jandice_barov_rework.cpp"

SLICE = range(206110, 206130)
(CURSE, SHELL_GAME, SHATTER, SHATTER_LOOK, UNMASKED, BLOOD_SIGIL, BLOODLINES, BLOOD_PRICE, POOF, BURST, FAKE_POP,
 THREAD, BEAM) = range(206110, 206123)
JANDICE, COPY, REFLECTION = 10503, 11439, 300530

APPLY_AURA, SCHOOL_DAMAGE = 6, 2
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 87
DISPEL_CURSE = 2
ATTR0_PASSIVE = 0x00000040
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
JANDICE_UNIT_FLAGS = 32832
HEALTH_BASE_61_PALADIN = 2515


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


class JandiceDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (JANDICE, COPY)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == REFLECTION}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) == REFLECTION}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        self.assertEqual(sorted(self.spells), list(range(CURSE, BEAM + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": sorted(self.spells)}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_JB_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(self.spells))

    def test_jandice_is_bound(self):
        edit = self.edits[JANDICE]
        self.assertEqual(edit["ScriptName"], "boss_jandice_barov_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"], 1)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertLessEqual(abs(edit["HealthModifier"] * HEALTH_BASE_61_PALADIN - 175_000), 2)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_jandice_barov_rework,", self.cpp)

    def test_the_copy_looks_like_her(self):
        copy, boss = self.edits[COPY], self.edits[JANDICE]
        self.assertEqual(copy["name"], "Jandice Barov")
        self.assertEqual(copy["ScriptName"], "npc_sc_shell_game_copy")
        self.assertEqual(copy["AIName"], "")
        self.assertEqual(copy["unit_class"], 2)
        self.assertEqual(copy["unit_flags"], JANDICE_UNIT_FLAGS)
        self.assertEqual(copy["HealthModifier"], boss["HealthModifier"])
        self.assertEqual(copy["ManaModifier"], 3.0)
        self.assertEqual(copy["CreatureImmunitiesId"], boss["CreatureImmunitiesId"])
        self.assertEqual((copy["MovementType"], copy["RegenHealth"], copy["DamageModifier"]), (0, 0, 0.0))
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_shell_game_copy,", self.cpp)

    def test_the_reflection(self):
        self.assertEqual(sorted(self.creatures), [REFLECTION])
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"creature": [REFLECTION]}), [])
        r = self.creatures[REFLECTION]
        self.assertEqual(r["ScriptName"], "npc_sc_jandice_reflection")
        self.assertEqual(r["name"], "Reflection of Jandice Barov")
        self.assertTrue(r["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE and r["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
        self.assertEqual((r["minlevel"], r["maxlevel"]), (61, 61))
        self.assertEqual(r["lootid"], 0)
        self.assertEqual(r["difficulty_entry_1"], 0)    # not a combat add: no heroic template (WP-H)
        self.assertEqual(self.models[REFLECTION]["CreatureDisplayID"], 11073)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_jandice_reflection,", self.cpp)

    def test_curse_and_unmasked(self):
        curse = self.spells[CURSE]
        self.assertEqual((curse["cast_time_ms"], curse["duration_ms"], curse["dispel"]), (2000, 30000, DISPEL_CURSE))
        eff = curse["effect1"]
        self.assertEqual((eff["type"], eff["apply_aura"], eff["misc_value"]), (APPLY_AURA,
                         AURA_MOD_DAMAGE_PERCENT_TAKEN, 1))
        self.assertEqual(eff["base_points"] + eff["die_sides"], 20)
        self.assertEqual(eff["radius_yards"], 10.0)
        self.assertEqual(_raw(curse, "InterruptFlags"), 15)
        unmasked = self.spells[UNMASKED]
        self.assertEqual(unmasked["duration_ms"], 8000)
        ueff = unmasked["effect1"]
        self.assertEqual((ueff["apply_aura"], ueff["misc_value"]), (AURA_MOD_DAMAGE_PERCENT_TAKEN, 127))
        self.assertEqual(ueff["base_points"] + ueff["die_sides"], 20)

    def test_damage_spells(self):
        for sid, script in ((SHATTER, "spell_sc_jandice_shatter"), (BLOOD_PRICE, "spell_sc_jandice_blood_price")):
            with self.subTest(spell=sid):
                s = self.spells[sid]
                self.assertEqual(s["effect1"]["type"], SCHOOL_DAMAGE)
                self.assertTrue(_raw(s, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
                self.assertTrue(s["effect1"].get("_potency_excluded"))
                self.assertIn((sid, script), self.scripts)
                self.assertIn(f"RegisterSpellScript({script})", self.cpp)
        for sid in (BLOOD_SIGIL, BLOODLINES):
            self.assertIn((sid, "spell_boss_mechanics_resolve"), self.scripts)
            self.assertTrue(_raw(self.spells[sid], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        own = {name for _, name in self.scripts if name != "spell_boss_mechanics_resolve"}
        self.assertEqual(own, {"spell_sc_jandice_shatter", "spell_sc_jandice_blood_price"})

    def test_looks(self):
        expected = {SHELL_GAME: 11181, SHATTER_LOOK: 11222, POOF: 2046, BURST: 9312, FAKE_POP: 255, THREAD: 14876,
                    BEAM: 15275, BLOOD_PRICE: 11117, SHATTER: 9312, BLOOD_SIGIL: 9312, BLOODLINES: 9312}
        for sid, visual in expected.items():
            with self.subTest(spell=sid):
                self.assertEqual(_raw(self.spells[sid], "SpellVisualID_1"), visual)
        for sid in (THREAD, BEAM):
            s = self.spells[sid]
            self.assertEqual(s["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertFalse(int(s.get("attributes") or 0) & ATTR0_PASSIVE)
        self.assertEqual(self.spells[THREAD]["duration_ms"], 1000)
        self.assertEqual(self.spells[BEAM]["duration_ms"], -1)


if __name__ == "__main__":
    unittest.main()
