"""
Scarlet Monastery build WP-D9, Forgemaster Gideon Crell: source/npcs/scarlet_monastery/crell.py (his template, the
Scarlet Recruit and the spells 212900-212923), data/sql/updates/pending_db_world/rev_crell_scarlet_monastery.sql (his
texts, the forge / anvil / trough templates and spawns, his spawn), and the C++ they must agree with
(modules/mod-dungeon-bosses src/ScarletMonastery/CrellLogic.h and boss_forgemaster_gideon_crell_rework.cpp).

Checks:
  - the twenty-four spells sit in the D9 slice and the C++ names the same ids; the registry's hits are resolve copies in
    their schools; the cleave's tank hit carries 15 / 25 in hundredths and binds the kit's percent script; the Temper
    is an interruptible 2.5 s Fire cast and the Hammer's bar is not (and not Fire); the plate is an all-school absorb
    bound to its AuraScript; the looks use the V constants;
  - the two creatures: Crell level 37 warrior, 54k, immunity 1972, INSTANCE_BIND, display 3278, his heroic entry, his
    ScriptName only once wave 2 binds; the recruit unselectable, unattackable, walking 1.5 yd/s, no heroic entry;
  - the SQL: eight texts, three GENERIC not-selectable objects on the V displays, their spawns and his on both
    difficulties at the header's spots;
  - the wave gate: the AI registers behind kWave2Bound; the AuraScript and `.dbtest sm crell` always.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_crell.py
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
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from source.npcs.scarlet_monastery import _common as common  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "CrellLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_forgemaster_gideon_crell_rework.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_crell_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "crell.py"

SLICE = range(212900, 212950)
FIRST = 212900
NAMES = ("SPELL_AR_SPARK", "SPELL_AR_SPARK_LOOK", "SPELL_AR_SLAG", "SPELL_AR_SLAG_LOOK", "SPELL_AR_HAMMER_CAST",
         "SPELL_AR_HAMMER_RING", "SPELL_AR_HAMMER_BURST", "SPELL_AR_ANVIL_STRIKE_LOOK", "SPELL_AR_STEAM",
         "SPELL_AR_STEAM_LOOK", "SPELL_AR_SLAG_BURST", "SPELL_AR_SLAG_BURST_LOOK", "SPELL_AR_TEMPER",
         "SPELL_AR_FLAWED", "SPELL_AR_MASTERWORK", "SPELL_AR_FORGED_BLADE", "SPELL_AR_CLEAVE", "SPELL_AR_CLEAVE_TANK",
         "SPELL_AR_PROVING_STRIKE", "SPELL_AR_DASH_LOOK", "SPELL_AR_RED_HOT_PLATE", "SPELL_AR_PLATE_BURN",
         "SPELL_AR_RIVET", "SPELL_AR_RIVET_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_SCHOOL_ABSORB = 4, 69
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
TARGET_DEST_DEST = 87
CRELL, RECRUIT = 300940, 300941
GO_DISPLAYS = {301325: visuals.GODI_FORGE, 301326: visuals.GODI_ANVIL, 301327: visuals.GODI_TROUGH}


class CrellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    def _point(self, name: str) -> tuple[float, float, float]:
        match = re.search(rf"Point3 {name}\{{ ([-\d.]+)f, ([-\d.]+)f, ([-\w.]+) \}}", self.logic)
        self.assertIsNotNone(match, name)
        z = 8.0 if match.group(3) == "kFloorZ" else float(match.group(3).rstrip("f"))
        return float(match.group(1)), float(match.group(2)), z

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d9_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsCrell{ 212900, 212949 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_AR_RIVET_LOOK <= kSpellSlice\.last")

    def test_the_registry_hits_are_resolve_copies_in_their_schools(self):
        for offset, school in ((0, SCHOOL_FIRE), (2, SCHOOL_FIRE), (5, SCHOOL_PHYSICAL), (6, SCHOOL_PHYSICAL),
                               (8, SCHOOL_FIRE), (10, SCHOOL_FIRE), (16, SCHOOL_PHYSICAL), (18, SCHOOL_PHYSICAL),
                               (22, SCHOOL_FIRE)):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)    # rule 2

    def test_the_cleave_tank_hit_binds_the_kit_script(self):
        spell = self.spells[FIRST + 17]
        effect = spell["effect1"]
        self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], 1500)
        self.assertEqual(spell["raw_overrides"]["EffectMiscValueB_1"], 2500)
        self.assertIn((FIRST + 17, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000)
        self.assertEqual(self._const("kCleaveTankPct"), "15.f,25.f")

    def test_the_header_percents_are_the_build_spec(self):
        for name, value in (("kSparkPct", "30.f,45.f"), ("kHammerPct", "30.f,45.f"), ("kSteamPct", "8.f,12.f"),
                            ("kCleavePct", "30.f,45.f"), ("kStrikeFirstPct", "30.f,45.f"),
                            ("kStrikeNextPct", "20.f,30.f"), ("kRivetPct", "30.f,45.f"), ("kSlagPct", "10.f"),
                            ("kSlagBurstPct", "45.f"), ("kSparkCount", "10,16"), ("kSparkRadiusYd", "5.f,4.f"),
                            ("kRivetStep", "1250,3125"), ("kHammerFollowUpMs", "2000,1500"),
                            ("kIssueAtMs", "15000,12500")):
            self.assertEqual(self._const(name), value, name)

    def test_the_temper_is_interruptible_and_the_hammer_bar_is_not(self):
        temper = self.spells[FIRST + 12]
        self.assertEqual(temper["school"], SCHOOL_FIRE)
        self.assertEqual(temper["cast_time_ms"], 2500)
        self.assertEqual(int(self._const("kTemperCastMs")), 2500)
        self.assertEqual((temper["raw_overrides"]["InterruptFlags"], temper["raw_overrides"]["PreventionType"]),
                         (15, 1))
        hammer = self.spells[FIRST + 4]
        self.assertEqual(hammer["cast_time_ms"], 2500)
        self.assertEqual(int(self._const("kHammerCastMs")), 2500)
        self.assertEqual((hammer["raw_overrides"]["InterruptFlags"], hammer["raw_overrides"]["PreventionType"]),
                         (0, 0))
        self.assertNotEqual(hammer["school"], temper["school"])        # rule 5
        self.assertRegex(self.script, r"d\.interrupts\.emplace_back\(NPC_SM_CRELL, SPELL_AR_TEMPER, 3,")

    def test_the_plate_is_an_all_school_absorb_bound_to_its_script(self):
        plate = self.spells[FIRST + 20]
        effect = plate["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"], effect["misc_value"]),
                         (EFFECT_APPLY_AURA, AURA_SCHOOL_ABSORB, 127))
        self.assertEqual(plate["duration_ms"], -1)
        self.assertEqual(plate["dispel"], 0)
        self.assertEqual(plate["raw_overrides"]["SpellVisualID_1"], visuals.AR_PLATE)
        self.assertIn((FIRST + 20, "spell_sm_crell_red_hot_plate"), self.scripts)
        self.assertRegex(self.script, r"class spell_sm_crell_red_hot_plate : public AuraScript")
        self.assertRegex(self.script, r"RegisterSpellScript\(spell_sm_crell_red_hot_plate\)")
        burn = self.spells[FIRST + 21]
        self.assertEqual((burn["school"], burn["effect1"]["type"]), (SCHOOL_FIRE, EFFECT_SCHOOL_DAMAGE))
        self.assertTrue(burn["raw_overrides"]["AttributesEx3"] & 0x20000000)
        self.assertEqual((self._const("kBurnBackPct"), self._const("kArmorTear")), ("20.f", "500"))

    def test_the_looks_use_the_v_constants(self):
        for offset, visual in ((1, visuals.AR_SPARKS), (7, visuals.AR_ANVIL_STRIKE), (11, visuals.AR_SLAG_BURST),
                               (23, visuals.AR_RIVET)):
            spell = self.spells[FIRST + offset]
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, offset)
            self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visual, offset)
        for offset, visual in ((3, visuals.AR_SLAG), (9, visuals.AR_STEAM), (19, visuals.AR_DASH),
                               (16, visuals.AR_CLEAVE), (17, visuals.AR_CLEAVE)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        self.assertGreater(self.spells[FIRST + 23]["raw_overrides"]["Speed"], 0)     # the rivet flies
        # the VR corrections: never the doc's one-shot / wrong looks
        self.assertEqual((visuals.AR_STEAM, visuals.AR_RIVET, visuals.AR_PLATE), (8657, 67, 1946))

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.creatures[CRELL]
        self.assertEqual((c["name"], c["subname"]), ("Forgemaster Gideon Crell", "Armorer of the Crusade"))
        self.assertEqual(c["ScriptName"], "boss_forgemaster_gideon_crell_rework" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"], c["rank"]), (37, 37, 1, 67, 1))
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["flags_extra"], 1)               # INSTANCE_BIND: FD-SM's credit_creature(300940)
        self.assertEqual(c["lootid"], CRELL)
        # R-2-FW MN-1: below the 10.4 / 11 yd of the nearest pre-cleared Guardsmen
        self.assertEqual(c["detection_range"], 9.0)
        # WP-H's mint table: 310476 once every lower kit unit is declared (CRELL_HEROIC; until then unset)
        self.assertIn(c.get("difficulty_entry_1") or 0, (0, 310476))
        self.assertIn("CRELL_HEROIC_PLANNED = 310476", self.dt)
        self.assertAlmostEqual(c["HealthModifier"] * 1336, 54000, delta=5)
        self.assertEqual(self.models[CRELL]["CreatureDisplayID"], visuals.DISPLAY_CRELL)
        self.assertEqual(visuals.DISPLAY_CRELL, 3278)
        self.assertEqual(int(self._const("kCrellHealthNormal")), 54000)
        self.assertEqual(int(self._const("kCrellHealthHeroic")), 270000)

    def test_the_recruit_is_set_dressing(self):
        c = self.creatures[RECRUIT]
        self.assertEqual(c["ScriptName"], "")
        self.assertEqual(c["faction"], 67)
        self.assertEqual(c["unit_flags"], 0x2 | 0x100 | 0x200 | 0x02000000)
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertEqual(c["flags_extra"], 0x40)
        self.assertAlmostEqual(c["speed_walk"] * 2.5, float(self._const("kRecruitWalkYdPerS").rstrip("f")), 3)
        self.assertNotIn("difficulty_entry_1", {k for k, v in c.items() if v})
        self.assertEqual(self.models[RECRUIT]["CreatureDisplayID"], visuals.DISPLAY_SCARLET_TRAINEE)

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [CRELL, RECRUIT],
                                                       "gameobject": sorted(GO_DISPLAYS)}), [])
        for name, value in (("NPC_SM_CRELL", CRELL), ("NPC_SM_SCARLET_RECRUIT", RECRUIT), ("GO_SM_FORGE", 301325),
                            ("GO_SM_ANVIL", 301326), ("GO_SM_QUENCH_TROUGH", 301327), ("GO_ARMOR_CRATE", 3703)):
            self.assertRegex(self.header, rf"{name}\s*=\s*{value},")

    def test_the_wave_gate(self):
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\("
                                      r"boss_forgemaster_gideon_crell_rework,")
        self.assertRegex(self.script, r'\n    SmTest::RegisterBoss\("crell",')
        self.assertIn("creature_template(300940, ", self.dt)       # H finds the kit units by this literal pattern
        self.assertIn("creature_template(300941, ", self.dt)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_eight_texts(self):
        rows = re.findall(r"^\(300940, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(t), int(r)) for g, _, _, t, r in rows],
                         [(0, 14, 0), (1, 14, 0), (2, 14, 0), (3, 41, 3), (4, 14, 0), (5, 41, 3), (6, 14, 0),
                          (7, 14, 0)])
        self.assertEqual([t.replace("''", "'") for _, _, t, _, _ in rows],
                         ["Out of uniform, are we? I'll fit you myself!", "A blade for the Crusade!",
                          "Plate for the faithful!", "%s begins to temper the piece!", "Let's test the edge!",
                          "%s hands the finished piece to a Scarlet Recruit.", "Next!",
                          "Who... will keep... the stores..."])
        for name, group in (("SAY_PULL", 0), ("SAY_ORDER_BLADE", 1), ("SAY_ORDER_PLATE", 2), ("EMOTE_TEMPER", 3),
                            ("SAY_PROVING_STRIKE", 4), ("EMOTE_HAND_OVER", 5), ("SAY_KILL", 6), ("SAY_DEATH", 7)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_SM_CRELL, 0, 7, 0 \}")

    def test_the_objects_are_generic_not_selectable_on_the_v_displays(self):
        for entry, display in GO_DISPLAYS.items():
            self.assertIsNotNone(re.search(rf"^\({entry}, 5, {display}, '", self.sql, re.M), entry)
            self.assertIsNotNone(re.search(rf"^\({entry}, 0, 16, 0, 0, 0, 0, 0, 0\)", self.sql, re.M), entry)
        self.assertEqual((visuals.GODI_FORGE, visuals.GODI_ANVIL, visuals.GODI_TROUGH), (7044, 273, 216))

    def test_the_spawns_are_the_header_spots_on_both_difficulties(self):
        for guid, entry, name in ((3013250, 301325, "kForge"), (3013260, 301326, "kAnvil"),
                                  (3013270, 301327, "kTrough")):
            row = re.search(rf"^\({guid}, {entry}, 189, 0, 0, (\d+), 1, ([-\d.]+), ([-\d.]+), ([-\d.]+),", self.sql,
                            re.M)
            self.assertIsNotNone(row, guid)
            self.assertEqual(int(row.group(1)), 3)
            got = tuple(float(row.group(i)) for i in (2, 3, 4))
            if name == "kAnvil":
                spot = re.search(r"kCrellAnvil\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.header)
                self.assertEqual(got, tuple(float(spot.group(i)) for i in (1, 2, 3)))
            else:
                self.assertEqual(got, self._point(name))
        row = re.search(r"^\(3009400, 300940, 189, 0, 0, (\d+), 1, 0, ([-\d.]+), ([-\d.]+), ([-\d.]+), ([\d.]+), "
                        r"(\d+), 0,", self.sql, re.M)
        self.assertIsNotNone(row)
        self.assertEqual(int(row.group(1)), 3)
        self.assertEqual(tuple(float(row.group(i)) for i in (2, 3, 4)), self._point("kCrellSpawn"))
        self.assertEqual(float(row.group(5)), float(self._const("kCrellSpawnFacing").rstrip("f")))
        self.assertEqual(int(row.group(6)), 86400)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 300940 AND `guid` = 3009400;", self.sql)


if __name__ == "__main__":
    unittest.main()
