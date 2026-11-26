"""
Gnomeregan build WP-D4, the Mobile Alert System: source/npcs/gnomeregan/mobile_alert_system.py (the boss's row, the
Security Assistant 301111, the Security Defender 301112, the light stalker 301113, the spells 214420-214428),
data/sql/updates/pending_db_world/rev_mobile_alert_system_gnomeregan.sql (the texts, the Defender's gun), and the C++
they must agree with (modules/mod-dungeon-bosses src/Gnomeregan/MobileAlertSystemLogic.h,
boss_mobile_alert_system_rework.cpp, MobileAlertSystemMachine.cpp).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_alert.py
"""

from __future__ import annotations

import ast
import math
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_gnomeregan_npcs as skeleton  # noqa: E402
from lib import test_gnomeregan_vfx as vfx  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402
from source.npcs.gnomeregan import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
LOGIC = MDB / "MobileAlertSystemLogic.h"
SCRIPT = MDB / "boss_mobile_alert_system_rework.cpp"
MACHINE = MDB / "MobileAlertSystemMachine.cpp"
HEADER = MDB / "GnomereganRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_mobile_alert_system_gnomeregan.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "gnomeregan" / "mobile_alert_system.py"


def _dt_constants() -> SimpleNamespace:
    """mobile_alert_system.py's top-level literal constants (the module itself only loads inside the registry)."""
    tree = ast.parse(DT_FILE.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return SimpleNamespace(**values)


dt = _dt_constants()

FIRST = 214420
SLICE = range(214420, 214460)
NAMES = ("SPELL_MA_SPOTTED", "SPELL_MA_ALARM", "SPELL_MA_ALARM_LOOK", "SPELL_MA_LOCK_ON", "SPELL_MA_SPOTTED_BEAM",
         "SPELL_MA_SELF_DESTRUCT", "SPELL_MA_BLAST_LOOK", "SPELL_MA_NET", "SPELL_MA_NETTING")
(SPOTTED, ALARM, ALARM_LOOK, LOCK_ON, BEAM, SELF_DESTRUCT, BLAST, NET, NETTING) = range(FIRST, FIRST + len(NAMES))
BOSS, ASSISTANT, DEFENDER, STALKER = 301110, 301111, 301112, 301113
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_DUMMY, AURA_MOD_ROOT = 4, 26
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 8, 64
MECHANIC_ROOT = 7
IGNORE_CASTER_MODIFIERS = 0x20000000
NO_IMMUNITIES = 0x20000000
BASE_HEALTH_28 = 853
NOT_SELECTABLE_NOT_ATTACKABLE = 0x2 | 0x02000000

# creature_text 301110: group -> (type, the header's enum name)
TEXTS = {
    0: (14, "YELL_MA_ALARM"), 1: (41, "EMOTE_MA_LOCK_ON"), 2: (41, "EMOTE_MA_SPOTTED"), 3: (41, "EMOTE_MA_REVERSE"),
    4: (14, "YELL_MA_SELF_DESTRUCT"), 5: (14, "YELL_MA_TWENTY"), 6: (41, "EMOTE_MA_SKIPS_AHEAD"),
    7: (14, "YELL_MA_CANCELED"), 8: (41, "EMOTE_MA_CAMERAS"),
}


class AlertSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = skeleton._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.models = [e for e in reg.creature_template_models]
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.machine = MACHINE.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.tune = cls.logic[cls.logic.index("namespace Tune"):cls.logic.index("// Values the build spec leaves open")]

    def _tune(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*(?:=\s*|\{{)([^;}}]+?)\s*(?:;|\}};)", self.tune)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    def _health(self, name: str) -> int:
        found = re.findall(rf"NH<std::uint32_t> constexpr {name}\{{ (\d+), (\d+) \}};", self.header)
        self.assertEqual(len(found), 1, name)
        return int(found[0][0])

    def _models(self, entry: int) -> list[int]:
        return [int(m["CreatureDisplayID"]) for m in sorted(self.models, key=lambda m: int(m["Idx"]))
                if int(m["CreatureID"]) == entry]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d4_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsAlertSystem{ 214420, 214459 }", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)

    def test_the_registry_hits_are_resolve_copies(self):
        for spell_id, school in ((SPOTTED, SCHOOL_ARCANE), (ALARM, SCHOOL_NATURE)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS, spell_id)
        self.assertIn("hit.spellId = SPELL_MA_SPOTTED;", self.script)
        self.assertIn("hit.spellId = SPELL_MA_ALARM;", self.script)
        # rule 17: the tank's own row on both; no Weakened on the pulse
        self.assertEqual(self.script.count("hit.tankPct = hit.pct;"), 2)
        self.assertIn("hit.weakened = kSpottedWeakened(_heroic);", self.script)
        self.assertIn("hit.weakened = false;", self.script)

    def test_nothing_is_kickable_or_dispellable(self):
        # The kick and dispel table: the Alert System and its adds have no kickable cast and no dispellable debuff.
        for spell_id, spell in self.spells.items():
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertEqual(spell["dispel"], 0, spell_id)
        net = self.spells[NET]
        self.assertEqual(net["school"], SCHOOL_PHYSICAL)
        self.assertEqual(net["mechanic"], MECHANIC_ROOT)
        self.assertEqual(net["effect1"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(net["duration_ms"], dt.NET_MS)
        self.assertEqual(net["range_yards"], dt.NET_RANGE)
        self.assertEqual(self.spells[NETTING]["duration_ms"], dt.NET_MS)

    def test_the_looks_are_the_visual_constants(self):
        wanted = {ALARM_LOOK: visuals.MA_ALARM_PULSE, LOCK_ON: visuals.MA_LOCK_PILLAR, BEAM: visuals.MA_SPOTTED,
                  SELF_DESTRUCT: visuals.MA_SELF_DESTRUCT, BLAST: visuals.MA_SELF_DESTRUCT, NET: visuals.MA_NET}
        for spell_id, visual in wanted.items():
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)
        for spell_id, spell in self.spells.items():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1"), set(vfx.WRONG_SPELL_VISUALS), spell_id)

    def test_the_auras_he_relies_on_land_through_immunities(self):
        # rule 27: the clock on him (immunity 1972) and the lock-on warning are not stripped by a bubble
        for spell_id in (SELF_DESTRUCT, LOCK_ON):
            self.assertTrue(self.spells[spell_id]["attributes"] & NO_IMMUNITIES, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_DUMMY, spell_id)
        self.assertEqual(self.spells[SELF_DESTRUCT]["duration_ms"], dt.SELF_DESTRUCT_MS)
        self.assertEqual(self.spells[LOCK_ON]["duration_ms"], dt.LOCK_ON_MS)

    def test_the_dt_numbers_are_the_headers(self):
        self.assertEqual(dt.SELF_DESTRUCT_MS, int(self._tune("kSelfDestructMs")))
        self.assertEqual(dt.NET_MS, int(self._tune("kNetMs")))
        self.assertEqual(dt.NET_RANGE, float(self._tune("kNetRangeYd").rstrip("f")))
        self.assertEqual(dt.LOCK_ON_MS, int(self._tune("kSearchDimMs")) + int(self._tune("kSearchSweepMs")))
        self.assertEqual(dt.ALERT_SCALE, visuals.ALERT_SCALE)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_adds_are_declared_bound_and_sized(self):
        for entry, script, health, modifier, rank, displays in (
                (ASSISTANT, "npc_gnomer_security_assistant", "kSecurityAssistant", dt.ASSISTANT_HEALTH_MODIFIER, 0,
                 [visuals.DISPLAY_ASSISTANT, visuals.DISPLAY_ASSISTANT_2]),
                (DEFENDER, "npc_gnomer_security_defender", "kSecurityDefender", dt.DEFENDER_HEALTH_MODIFIER, 1,
                 [visuals.DISPLAY_DEFENDER, visuals.DISPLAY_DEFENDER_2])):
            with self.subTest(entry=entry):
                row = self.creatures[entry]
                self.assertEqual(row["ScriptName"], script)
                self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({script},")
                self.assertEqual((int(row["minlevel"]), int(row["maxlevel"]), int(row["rank"])), (28, 28, rank))
                self.assertEqual(int(row["faction"]), 63)
                self.assertEqual(float(row["HealthModifier"]), modifier)
                # the engine's rounding (CreatureData.h GenerateHealth: ceil of base x float(mod))
                self.assertEqual(math.ceil(BASE_HEALTH_28 * modifier), self._health(health))
                self.assertEqual(int(row["lootid"]), 0)
                self.assertEqual(self._models(entry), displays)

    def test_the_light_stalker_is_passive_and_invisible(self):
        row = self.creatures[STALKER]
        self.assertEqual(int(row["unit_flags"]) & NOT_SELECTABLE_NOT_ATTACKABLE, NOT_SELECTABLE_NOT_ATTACKABLE)
        self.assertEqual(row["AIName"], "NullCreatureAI")
        self.assertEqual(row["ScriptName"], "")
        self.assertEqual(self._models(STALKER), [visuals.DISPLAY_INVISIBLE_STALKER])
        self.assertIn("NPC_LIGHT_STALKER           = 301113", self.header)
        # the machine summons it (KT-G TurningLights' stalkerEntry)
        self.assertIn("GnomereganRework::NPC_LIGHT_STALKER", (MDB / "MobileAlertSystemMachine.h").read_text())

    def test_the_boss_row(self):
        row = self.creatures[BOSS]
        self.assertEqual(row["ScriptName"], "boss_mobile_alert_system_rework")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(self._models(BOSS), [visuals.DISPLAY_ALERT])
        self.assertEqual(math.ceil(BASE_HEALTH_28 * float(row["HealthModifier"])), self._health("kAlertSystem"))

    # --- the texts and the gun ----------------------------------------------------------------------------------------

    def test_the_texts(self):
        rows = re.findall(r"\(301110, (\d+), 0, '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, (\d+),\s*(\d+), 0,", self.sql)
        found = {int(g): (int(t), int(sound), int(broadcast), text) for g, text, t, sound, broadcast in rows}
        self.assertEqual(sorted(found), sorted(TEXTS))
        for group, (text_type, name) in TEXTS.items():
            self.assertEqual(found[group][0], text_type, group)
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},")
        self.assertEqual(found[0][1], visuals.MA_ALARM_VOICE)      # the alert bot's voice on the alarm line
        self.assertEqual(found[0][2], 4142)                         # 7849's line
        self.assertEqual((found[4][2], found[5][2]), (3927, 3949))  # 7897's lines
        for group in (1, 2, 8):
            self.assertIn("$n", found[group][3], group)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 301110 AND `GroupID` BETWEEN 0 AND 8;",
                      self.sql)

    def test_the_defender_carries_the_stock_gun(self):
        self.assertIn("DELETE FROM `creature_equip_template` WHERE `CreatureID` = 301112;", self.sql)
        self.assertIn("(301112, 1, 1905, 0, 2552, 0);", self.sql)

    # --- the C++ rules ------------------------------------------------------------------------------------------------

    def test_the_drill_tags(self):
        # mod-boss-mechanics MechanicDrill.h gnomeregan-shapes row 6 (LESSONS A.3 #4)
        for name, value in (("TAG_MA_SEARCHLIGHT", 50), ("TAG_MA_SEARCHLIGHT_FLOOR", 51), ("TAG_MA_LIGHTS", 52),
                            ("TAG_MA_LIGHTS_FLOOR", 53), ("TAG_MA_CAMERAS", 54)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{value},")

    def test_the_spec_numbers(self):
        self.assertEqual(self._tune("kSpottedPct"), "20.f,50.f")
        self.assertEqual(self._tune("kAlarmPct"), "5.f,8.f")
        self.assertEqual(self._tune("kPatrolEveryMs"), "30000,20000")
        self.assertEqual(self._tune("kSearchConeDeg"), "40.f")
        self.assertEqual(self._tune("kSearchSweepDeg"), "60.f")
        self.assertEqual(self._tune("kLightsConeDeg"), "30.f")
        self.assertEqual(self._tune("kLightsDegPerSec"), "12.f")
        self.assertEqual(self._tune("kLightsSpeedUpPct"), "10.f")
        self.assertEqual(self._tune("kDefenderCapNormal"), "4")
        self.assertEqual(self._tune("kSpottedLatchMs"), "3000")
        # R-1-B m1: the bots' band starts past a hunter's too-close line; his reach is 0.8 x the DT scale.
        self.assertEqual((self._tune("kBandMinYd"), self._tune("kBandMaxYd")), ("11.f", "16.f"))
        self.assertAlmostEqual(float(self._tune("kCombatReachYd").rstrip("f")), 0.8 * dt.ALERT_SCALE, places=3)

    def test_the_boss_holds_and_never_melees(self):
        self.assertIn("me->SetControlled(true, UNIT_STATE_ROOT);", self.script)
        self.assertIn("me->SetCombatMovement(false);", self.script)
        boss = self.script[self.script.index("struct boss_mobile_alert_system_rework"):
                           self.script.index("struct npc_gnomer_alert_add")]
        self.assertNotIn("DoMeleeAttackIfReady", boss)
        self.assertIn("GnomereganRework::NoAssist(me);", boss)

    def test_the_machine_replaces_the_stub(self):
        self.assertNotIn("StubLightsMachine", self.machine)
        self.assertIn("std::unique_ptr<LightsMachine> MakeLightsMachine(", self.machine)
        self.assertIn("DungeonKit::TurningLights _kit;", self.machine)


if __name__ == "__main__":
    unittest.main()
