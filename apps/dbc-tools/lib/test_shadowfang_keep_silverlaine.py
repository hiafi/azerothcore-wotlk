"""
Shadowfang Keep build WP-S3, Baron Silverlaine: source/npcs/shadowfang_keep/baron_silverlaine.py against its C++
(modules/mod-dungeon-bosses src/ShadowfangKeep/SilverlaineLogic.h, boss_baron_silverlaine_rework.cpp).

Checks:
  - the spells sit in Silverlaine's slice (205945-205964) and SilverlaineLogic.h names the same ids;
  - the echoes 300503-300505 sit in the `shadowfang_keep` creature slice with the stock bosses' looks, the echo script,
    1,200 health on normal, their heroic templates (STAGE-H: 310058-310060), no loot or XP, stunnable;
  - Accursed Veil: a 1.5 s interruptible Curse, 12 s, a 2 s periodic tick set by its SpellScript, healing received
    -50%, ignores caster modifiers; the pulse's resolve copy;
  - the echo's Maul: 1.5 s stun + a 20% bleed in 0.5 s ticks on S5's generic spell_sfk_hunt_maul (registered by Odo's
    script, not again here);
  - the spectral aura is shown (not passive) and carries Ghost Visual's SpellVisual;
  - 3887 is bound to boss_baron_silverlaine_rework with SmartAI off, HealthModifier 25 and immunity set 1972.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_silverlaine.py
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
from lib.test_shadowfang_keep_rethilgore import _load, _raw  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ShadowfangKeep"
HEADER = MODULE_DIR / "SilverlaineLogic.h"
SCRIPT = MODULE_DIR / "boss_baron_silverlaine_rework.cpp"
HUNT = MODULE_DIR / "Hunt.cpp"

SLICE = range(205945, 205965)
VEIL, VEIL_SPREAD, MAUL, SPECTRAL, ARRIVAL = range(205945, 205950)
ECHOES = {300503: (524, 310058), 300504: (524, 310059), 300505: (522, 310060)}
SILVERLAINE = 3887

APPLY_AURA = 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_HEALING_PCT = 4, 3, 12, 118
DISPEL_CURSE = 2
ATTR0_PASSIVE = 0x00000040
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CREATURE_FLAG_EXTRA_NO_XP = 0x40
UNIT_FLAG_NOT_SELECTABLE = 0x02000000


class SilverlaineDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in ECHOES}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in ECHOES}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == SILVERLAINE]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        self.assertEqual(sorted(self.spells), list(range(VEIL, ARRIVAL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"spell": sorted(self.spells)}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(self.spells))

    def test_the_echoes(self):
        self.assertEqual(sorted(self.creatures), sorted(ECHOES))
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"creature": sorted(self.creatures)}), [])
        for entry, (display, heroic) in ECHOES.items():
            echo = self.creatures[entry]
            self.assertEqual(self.models[entry]["CreatureDisplayID"], display)
            self.assertEqual(echo["ScriptName"], "npc_sfk_echo")
            self.assertEqual(echo["difficulty_entry_1"], heroic)
            self.assertEqual(round(echo["HealthModifier"] * 484), 1200)
            self.assertEqual(echo["lootid"], 0)
            self.assertTrue(echo["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
            self.assertFalse(echo["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
            self.assertEqual(echo["CreatureImmunitiesId"], 0)      # kit adds stay stunnable
            self.assertEqual((echo["minlevel"], echo["maxlevel"]), (20, 20))
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sfk_echo,", self.cpp)

    def test_accursed_veil(self):
        veil = self.spells[VEIL]
        self.assertEqual(veil["cast_time_ms"], 1500)
        self.assertEqual(veil["duration_ms"], 12000)
        self.assertEqual(veil["dispel"], DISPEL_CURSE)
        self.assertEqual(_raw(veil, "InterruptFlags"), 15)
        self.assertEqual(_raw(veil, "PreventionType"), 1)
        self.assertTrue(_raw(veil, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(veil, "SpellVisualID_1"), 561)
        tick, healing = veil["effect1"], veil["effect2"]
        self.assertEqual((tick["type"], tick["apply_aura"], tick["amplitude"]),
                         (APPLY_AURA, AURA_PERIODIC_DAMAGE, 2000))
        self.assertEqual((healing["type"], healing["apply_aura"]), (APPLY_AURA, AURA_MOD_HEALING_PCT))
        self.assertEqual(healing["base_points"] + healing.get("die_sides", 1), -50)
        self.assertTrue(tick.get("_potency_excluded") and healing.get("_potency_excluded"))
        self.assertIn((VEIL, "spell_sfk_silverlaine_accursed_veil"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sfk_silverlaine_accursed_veil)", self.cpp)
        self.assertIn((VEIL_SPREAD, "spell_boss_mechanics_resolve"), self.scripts)

    def test_the_echo_maul_reuses_the_hunt_script(self):
        maul = self.spells[MAUL]
        self.assertEqual(maul["duration_ms"], 1500)
        stun, bleed = maul["effect1"], maul["effect2"]
        self.assertEqual((stun["type"], stun["apply_aura"]), (APPLY_AURA, AURA_MOD_STUN))
        self.assertEqual((bleed["type"], bleed["apply_aura"]), (APPLY_AURA, AURA_PERIODIC_DAMAGE))
        self.assertEqual((bleed["base_points"], bleed["die_sides"], bleed["amplitude"]), (20, 0, 500))
        self.assertTrue(_raw(maul, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((MAUL, "spell_sfk_hunt_maul"), self.scripts)
        # Registered once, by the Hunt (Odo's AddSC); never again here.
        self.assertIn("RegisterSpellScript(spell_sfk_hunt_maul)", HUNT.read_text(encoding="utf-8"))
        self.assertNotIn("spell_sfk_hunt_maul", self.cpp)

    def test_looks(self):
        spectral = self.spells[SPECTRAL]
        self.assertEqual(spectral["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(spectral["duration_ms"], -1)
        self.assertFalse(int(spectral.get("attributes") or 0) & ATTR0_PASSIVE)
        self.assertEqual(_raw(spectral, "SpellVisualID_1"), 886)
        self.assertEqual(_raw(self.spells[ARRIVAL], "SpellVisualID_1"), 4490)
        own = {name for _, name in self.scripts if name != "spell_boss_mechanics_resolve"}
        self.assertEqual(own, {"spell_sfk_silverlaine_accursed_veil", "spell_sfk_hunt_maul"})

    def test_silverlaine_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_baron_silverlaine_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 25)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_baron_silverlaine_rework,", self.cpp)


if __name__ == "__main__":
    unittest.main()
