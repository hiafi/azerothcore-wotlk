"""
Blackrock Depths build WP-D10, Fineous Darkvire and the Guzzler rope: source/npcs/blackrock_depths/fineous.py (his
template columns and the spells 211120-211123), data/sql/updates/pending_db_world/rev_fineous_blackrock_depths.sql (the
Franclorn line, the two gameobjects and the hanging rope's spawn), and the C++ side they must agree with
(modules/mod-dungeon-bosses src/BlackrockDepths/FineousLogic.h and npc_fineous_darkvire_rework.cpp).

Checks:
  - the four spells sit in the D10 slice and the C++ names the same ids; the collapse is a resolve copy, Holy Light a
    2.5 s interruptible heal of 4% of the target's health, the two looks dest-targeted look-only spells with the V-1
    visuals;
  - his creature columns: the script, SmartAI off, 50,000 normal health on the level 53 paladin base, stun immunity;
  - the script names the C++ registers (the creature, the GO, the use spell WP-IT bound) match the data;
  - the SQL: Franclorn's group 1 line, the two gameobject templates (the rope a goober with the script, the pillar a
    non-selectable generic), the rope's one spawn at the climb spot on both difficulties, ids in the reservation;
  - the climb spot, the landing and the rope's hang point in C++ and in the SQL are the same numbers.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_fineous.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_blackrock_depths_event_items as event_items_test  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "FineousLogic.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "npc_fineous_darkvire_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_fineous_blackrock_depths.sql"

SLICE = range(211120, 211140)
SPELL_COLLAPSE, SPELL_HOLY_LIGHT, SPELL_RISE, SPELL_DUST = 211120, 211121, 211122, 211123
SPELL_ROPE = 211261
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_HEAL_PCT = 2, 3, 136
TARGET_UNIT_TARGET_ALLY, TARGET_DEST_DEST = 21, 87
TARGET_FLAG_DEST_LOCATION = 0x40
SCHOOL_PHYSICAL, SCHOOL_HOLY = 1, 2
FD_PILLAR_SPAWN_BURST, FD_COLLAPSE_DUST = 12718, 12855
ROPE_GO, PILLAR_GO = 301282, 301283
GOOBER, GENERIC = 10, 5
GO_FLAG_NOT_SELECTABLE = 16
FRANCLORN = 9542


class FineousTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names}
        cls.columns = next(e for e in npcs.creature_template_edits if int(e["entry"]) == 9056)
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d10_slice(self):
        self.assertEqual(sorted(self.spells), [SPELL_COLLAPSE, SPELL_HOLY_LIGHT, SPELL_RISE, SPELL_DUST])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsFineous{ 211120, 211139 }", self.header.replace("  ", " ").replace("  ", " "))

    def test_the_cpp_names_the_same_ids(self):
        for name, offset in (("SPELL_FD_SHODDY_COLLAPSE", 0), ("SPELL_FD_HOLY_LIGHT", 1), ("SPELL_FD_PILLAR_RISE", 2),
                             ("SPELL_FD_COLLAPSE_DUST", 3)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertEqual(SLICE.start, 211120)

    def test_the_collapse_is_a_resolve_copy_of_physical_damage(self):
        spell = self.spells[SPELL_COLLAPSE]
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertIn((SPELL_COLLAPSE, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertEqual(spell["cast_time_ms"], 0)

    def test_holy_light_is_a_2_5_s_interruptible_four_percent_heal(self):
        spell = self.spells[SPELL_HOLY_LIGHT]
        self.assertEqual((spell["school"], spell["cast_time_ms"]), (SCHOOL_HOLY, 2500))
        effect = spell["effect1"]
        self.assertEqual(effect["type"], EFFECT_HEAL_PCT)
        self.assertEqual(effect["base_points"] + effect["die_sides"], 4)        # BasePoints 3 + DieSides 1 = 4%
        self.assertEqual(effect["implicit_target_a"], TARGET_UNIT_TARGET_ALLY)
        raw = spell["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
        self.assertEqual(raw["CastingTimeIndex"], 20)                           # 2.5 s
        # the C++ heals the same percent: the pure header says 4
        self.assertRegex(self.logic, r"kHolyLightHealPct = 4\.f;")
        self.assertRegex(self.logic, r"kHolyLightCastMs = 2500;")
        # not a script-bound shared spell, and not the stock id
        self.assertNotIn(15493, self.spells)
        self.assertFalse([s for s in self.scripts if s[0] == SPELL_HOLY_LIGHT])

    def test_the_looks_are_dest_targeted_and_use_the_v1_visuals(self):
        for spell_id, visual in ((SPELL_RISE, FD_PILLAR_SPAWN_BURST), (SPELL_DUST, FD_COLLAPSE_DUST)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, spell_id)
            raw = spell["raw_overrides"]
            self.assertEqual(raw["SpellVisualID_1"], visual, spell_id)
            self.assertEqual(raw["Targets"], TARGET_FLAG_DEST_LOCATION, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)

    # --- the creature -------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.columns
        self.assertEqual(c["ScriptName"], "npc_fineous_darkvire_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["flags_extra"], 0)  # no encounter credit (234 dropped): no INSTANCE_BIND
        # 50,000 on the level 53 paladin class base 1,962 (spec "Build spec": about 25.5)
        self.assertAlmostEqual(c["HealthModifier"] * 1962, 50000, delta=10)

    def test_the_script_name_is_the_one_the_cpp_registers(self):
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(npc_fineous_darkvire_rework,")
        self.assertRegex(self.script, r"RegisterDungeonReworkGameObjectAI\(go_brd_hanging_rope,")
        self.assertRegex(self.script, r"RegisterSpellScript\(spell_brd_guzzler_rope\)")
        self.assertIn((SPELL_ROPE, "spell_brd_guzzler_rope"), self.scripts)
        self.assertIn("'go_brd_hanging_rope'", self.sql)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_franclorns_line_is_group_1_of_the_spirit(self):
        match = re.search(r"INSERT INTO `creature_text`.*?VALUES\n\((\d+), (\d+), (\d+), '([^']*(?:''[^']*)*)', (\d+),",
                          self.sql, re.S)
        self.assertIsNotNone(match)
        creature, group, text_id, text, kind = match.groups()
        self.assertEqual((int(creature), int(group), int(text_id)), (FRANCLORN, 1, 0))
        self.assertEqual(text, "Ironfel... return it to my statue, friends.")
        self.assertEqual(int(kind), 12)         # a say
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9542 AND `GroupID` = 1;", self.sql)
        self.assertRegex(self.logic, r"TEXT_FRANCLORN_IRONFEL = 1;")

    def test_the_two_gameobjects(self):
        entries = [int(v) for v in re.findall(r"^\((30128[23]), \d+, \d+, '", self.sql, re.M)]
        self.assertEqual(entries, [ROPE_GO, PILLAR_GO])
        rope = re.search(r"^\(301282, (\d+), (\d+), 'Hanging Rope', '', '', '', ([\d.]+),", self.sql, re.M)
        self.assertEqual((int(rope.group(1)), int(rope.group(2)), float(rope.group(3))), (GOOBER, 7717, 0.5))
        pillar = re.search(r"^\(301283, (\d+), (\d+), 'Shoddy Pillar', '', '', '', ([\d.]+),", self.sql, re.M)
        self.assertEqual((int(pillar.group(1)), int(pillar.group(2)), float(pillar.group(3))), (GENERIC, 5073, 1.0))
        addon = dict(re.findall(r"^\((30128[23]), \d+, (\d+), 0, 0, 0, 0, 0, 0\)", self.sql, re.M))
        self.assertEqual(addon, {"301282": "0", "301283": str(GO_FLAG_NOT_SELECTABLE)})
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"gameobject": [ROPE_GO, PILLAR_GO]}), [])
        self.assertIn("DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301282, 301283);", self.sql)

    def test_the_rope_spawn_is_the_climb_spot_on_both_difficulties(self):
        spawn = re.search(r"^\((\d+), (\d+), (\d+), 0, 0, (\d+), (\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+),",
                          self.sql, re.M)
        self.assertIsNotNone(spawn)
        guid, entry, map_id, mask, phase, x, y, z, o = spawn.groups()
        self.assertEqual((int(guid), int(entry), int(map_id), int(mask), int(phase)), (3012820, ROPE_GO, 230, 3, 1))
        spot = re.search(r"kRopeClimbSpot\{ ([\d.]+)f, (-[\d.]+)f, (-[\d.]+)f \}", self.header)
        self.assertEqual((float(x), float(y), float(z)), tuple(float(v) for v in spot.groups()))
        hang = re.search(r"kRopeHang\{ ([\d.]+)f, (-[\d.]+)f, (-[\d.]+)f, ([\d.]+)f \}", self.logic)
        self.assertEqual((float(x), float(y), float(z), float(o)), tuple(float(v) for v in hang.groups()))
        self.assertIn("DELETE FROM `gameobject` WHERE `id` = 301282 AND `guid` = 3012820;", self.sql)

    def test_the_landing_is_the_navmesh_top(self):
        top = re.search(r"kRopeTop\{ ([\d.]+)f, (-[\d.]+)f, (-[\d.]+)f \}", self.header)
        landing = re.search(r"kRopeLanding\{ ([\d.]+)f, (-[\d.]+)f, (-[\d.]+)f, [\d.]+f \}", self.logic)
        self.assertEqual(top.groups(), landing.groups())
        self.assertEqual(tuple(float(v) for v in landing.groups()), (878.5, -222.5, -49.8))

    def test_the_pillar_and_collapse_numbers(self):
        self.assertRegex(self.logic, r"kShoddyPct\{ 25\.f, 40\.f \}")
        self.assertRegex(self.logic, r"kShoddyEveryMs\{ 15000, 12000 \}")
        self.assertRegex(self.logic, r"kShoddyWarnMs = 3000;")
        self.assertRegex(self.logic, r"kShoddyRadiusYd = 6\.f;")
        # Ruling 88 (R-1-A n7): the tank takes the collapse on its own row.
        self.assertRegex(self.script, r"\.Damage\(kShoddyPct\(heroic\)\)\.TankDamage\(kShoddyPct\(heroic\)\)")

    def test_the_rope_is_free_for_all(self):
        # HANDOFF section 10: anyone in the group may loot the rope (not the round-robin looter alone, often a bot).
        self.assertIn(".freeforall = true;", self.script)
        self.assertNotIn("is_underthreshold = true", self.script)
        self.assertIn("FillNotNormalLootFor(member)", self.script)


if __name__ == "__main__":
    unittest.main()
