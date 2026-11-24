"""
Scarlet Monastery build WP-D10, Drillmaster Corin Halden: source/npcs/scarlet_monastery/halden.py (his template, the
Drill Recruit and the spells 212950-212958), data/sql/updates/pending_db_world/rev_halden_scarlet_monastery.sql (his
texts and his spawn), and the C++ they must agree with (modules/mod-dungeon-bosses src/ScarletMonastery/HaldenLogic.h
and boss_drillmaster_corin_halden_rework.cpp).

Checks:
  - the nine spells sit in the D10 slice and the C++ names the same ids; the hits the registry lands are Physical
    resolve copies; Javelins is an interruptible 2 s cast; the looks use the V constants and the javelin's flight speed
    is the header's;
  - the two creatures: his columns (level 37 warrior, 60k, immunity 1972, INSTANCE_BIND, the heroic entry of WP-H's
    table, the script name behind the wave switch, display 2514); the recruit an unselectable, unattackable helper on
    display 2522 with no heroic template;
  - the SQL: ten texts (groups 0-9 of 300942, the fumble a boss emote), his spawn at the header's spot on both
    difficulties;
  - the numbers the dbc-tools file pins are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_halden.py
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
LOGIC = MDB / "src" / "ScarletMonastery" / "HaldenLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_drillmaster_corin_halden_rework.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_halden_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "halden.py"
HEROIC_TABLE = TOOL_ROOT / "source" / "world" / "dungeons" / "scarlet_monastery.py"

SLICE = range(212950, 212980)
FIRST = 212950
NAMES = ("SPELL_MA_CHARGE", "SPELL_MA_CHARGE_LOOK", "SPELL_MA_SPEARS", "SPELL_MA_SPEARS_LOOK", "SPELL_MA_JAVELINS",
         "SPELL_MA_JAVELIN", "SPELL_MA_JAVELIN_LOOK", "SPELL_MA_CLOSE_RANKS", "SPELL_MA_CLOSE_RANKS_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY = 2, 3
SCHOOL_PHYSICAL = 1
TARGET_UNIT_CASTER, TARGET_DEST_DEST = 1, 87
TARGET_FLAG_DEST_LOCATION = 0x40
HALDEN, RECRUIT = 300942, 300943
HALDEN_HEROIC = 310477


class HaldenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.reg = reg
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
        return match.group(1)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d10_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsHalden{ 212950, 212979 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_MA_CLOSE_RANKS_LOOK <= kSpellSlice\.last")

    def test_the_registry_hits_are_physical_resolve_copies(self):
        for offset in (0, 2, 5, 7):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)    # rule 2
        # The script hands each hit its own spell and the build spec's percents.
        for name in ("SPELL_MA_CHARGE", "SPELL_MA_SPEARS", "SPELL_MA_JAVELIN", "SPELL_MA_CLOSE_RANKS"):
            self.assertIn(f".Spell({name})", self.script, name)
        self.assertEqual(self._const("kHitPct").replace(" ", ""), "30.f,45.f")
        self.assertEqual(self._const("kRingPct").replace(" ", ""), "10.f,12.f")

    def test_javelins_is_an_interruptible_2_s_cast(self):
        cast = self.spells[FIRST + 4]
        self.assertEqual(cast["cast_time_ms"], 2000)
        self.assertEqual(int(self._const("kJavelinCastMs")), 2000)
        raw = cast["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))     # a kick and a silence
        self.assertEqual(cast["effect1"]["type"], EFFECT_DUMMY)
        self.assertEqual(cast["effect1"]["implicit_target_a"], TARGET_UNIT_CASTER)
        self.assertFalse(any(spell_id == FIRST + 4 for spell_id, _ in self.scripts))     # no spell script
        self.assertIn("me->CastSpell(me, SPELL_MA_JAVELINS, false)", self.script)          # not triggered: a bar
        self.assertIn("OnSpellFailed", self.script)

    def test_the_looks_use_the_v_constants(self):
        for offset, visual in ((1, visuals.MA_CHARGE), (3, visuals.MA_SPEARS), (8, visuals.MA_CLOSE_RANKS)):
            spell = self.spells[FIRST + offset]
            self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visual, offset)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, offset)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_UNIT_CASTER, offset)
        look = self.spells[FIRST + 6]
        self.assertEqual(look["raw_overrides"]["SpellVisualID_1"], visuals.MA_JAVELIN)
        self.assertEqual(look["effect1"]["type"], EFFECT_DUMMY)
        self.assertEqual(look["effect1"]["implicit_target_a"], TARGET_DEST_DEST)
        self.assertEqual(look["raw_overrides"]["Targets"], TARGET_FLAG_DEST_LOCATION)
        self.assertEqual(float(look["raw_overrides"]["Speed"]), 18.0)
        self.assertEqual(self._const("kJavelinSpeed"), "18.f")
        # VR's picks (Charge 100, Thrust 62544, Throw Javelin 62778, Shield Wall 871)
        self.assertEqual((visuals.MA_CHARGE, visuals.MA_SPEARS, visuals.MA_JAVELIN, visuals.MA_CLOSE_RANKS),
                         (867, 13365, 11993, 345))

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.creatures[HALDEN]
        self.assertEqual(c["name"], "Drillmaster Corin Halden")
        self.assertEqual(c["subname"], "Master-at-Arms")
        self.assertEqual(c["ScriptName"], "boss_drillmaster_corin_halden_rework" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"], c["rank"]), (37, 37, 1, 67, 1))
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["flags_extra"], 1)               # INSTANCE_BIND: FD-SM's credit_creature(300942)
        self.assertEqual(c["lootid"], HALDEN)
        self.assertEqual(c["difficulty_entry_1"], HALDEN_HEROIC)
        # 60k on the level 37 warrior class base 1,336 (S0's table: 44.910)
        self.assertAlmostEqual(c["HealthModifier"] * 1336, 60000, delta=10)
        self.assertEqual(int(self._const("kHaldenHealthNormal")), 60000)
        self.assertEqual(int(self._const("kHaldenHealthHeroic")), 300000)
        self.assertEqual(self.models[HALDEN]["CreatureDisplayID"], 2514)
        self.assertEqual(visuals.DISPLAY_HALDEN, 2514)

    def test_wave_2_binds_his_script_behind_the_switch(self):
        self.assertIn("'ScriptName': SCRIPT_NAME if BIND_WAVE_2 else ''", self.dt)
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\("
                                      r"boss_drillmaster_corin_halden_rework,")
        self.assertRegex(self.script, r'SmTest::RegisterBoss\("halden",')
        self.assertIn("creature_template(300942, ", self.dt)       # H finds the kit units by this literal pattern
        self.assertIn("creature_template(300943, ", self.dt)

    def test_the_heroic_table_has_him_and_not_the_recruit(self):
        text = HEROIC_TABLE.read_text(encoding="utf-8")
        self.assertRegex(text, r"300942: _boss\(300_000, 310477\)")
        self.assertNotRegex(text, r"\n\s*300943:")
        self.assertIn("credit=_credit(300942)", text)

    def test_the_recruit_is_an_unharmable_helper(self):
        c = self.creatures[RECRUIT]
        self.assertEqual(c["name"], "Drill Recruit")
        self.assertEqual(c["ScriptName"], "")
        flags = 0x2 | 0x100 | 0x200 | 0x02000000      # not attackable, immune to players and NPCs, not selectable
        self.assertEqual(c["unit_flags"] & flags, flags)
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertEqual(c["flags_extra"], 0x40)
        self.assertEqual(c["faction"], 67)
        self.assertEqual(self.models[RECRUIT]["CreatureDisplayID"], 2522)
        self.assertEqual(visuals.DISPLAY_DRILL_RECRUIT, 2522)
        self.assertFalse(c.get("difficulty_entry_1"))
        # The descriptor ignores them (not selectable: bots never pick them).
        self.assertIn("d.ignores.emplace_back(NPC_SM_DRILL_RECRUIT)", self.script)

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"creature": [HALDEN, RECRUIT]}), [])
        for name, value in (("NPC_SM_HALDEN", HALDEN), ("NPC_SM_DRILL_RECRUIT", RECRUIT)):
            self.assertRegex(self.header, rf"{name}\s*=\s*{value},")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_ten_texts(self):
        rows = re.findall(r"^\(300942, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows],
                         [(0, 0, 14, 0), (1, 0, 14, 0), (2, 0, 14, 0), (3, 0, 14, 0), (4, 0, 14, 0), (5, 0, 41, 3),
                          (6, 0, 14, 0), (7, 0, 14, 0), (8, 0, 14, 0), (9, 0, 14, 0)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts, ["Fall in! Today's lesson is live targets!", "Charge!", "Spears, level!", "Javelins!",
                                 "Close ranks!", "The recruits fumble their javelins!", "Dismissed.",
                                 "Hold... the line...", "Charge, then spears!", "Javelins, then close ranks!"])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 300942 AND `GroupID` BETWEEN 0 AND 9;",
                      self.sql)
        for name, group in (("SAY_PULL", 0), ("SAY_CHARGE", 1), ("SAY_SPEARS", 2), ("SAY_JAVELINS", 3),
                            ("SAY_CLOSE_RANKS", 4), ("EMOTE_FUMBLE", 5), ("SAY_KILL", 6), ("SAY_DEATH", 7),
                            ("SAY_PAIR_CHARGE", 8), ("SAY_PAIR_JAVELINS", 9)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_SM_HALDEN, 0, 9, 0 \}")

    def test_his_spawn_is_the_header_spot_on_both_difficulties(self):
        row = re.search(r"^\(3009420, 300942, 189, 0, 0, (\d+), 1, 0, ([-\d.]+), ([-\d.]+), ([-\d.]+), ([\d.]+), "
                        r"(\d+), 0,", self.sql, re.M)
        self.assertIsNotNone(row)
        self.assertEqual(int(row.group(1)), 3)              # normal and heroic (rule 14)
        x, y, z = (float(row.group(i)) for i in (2, 3, 4))
        spot = re.search(r"kHaldenSpot\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.header)
        self.assertEqual((x, y, z), tuple(float(spot.group(i)) for i in (1, 2, 3)))
        self.assertAlmostEqual(float(row.group(5)), 3.14159, places=4)     # facing south, toward the storeroom
        self.assertEqual(int(row.group(6)), 86400)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 300942 AND `guid` = 3009420;", self.sql)
        # No recruit spawn: he summons them.
        self.assertNotIn("300943", self.sql.split("-- Drillmaster Corin Halden's spawn")[1])

    # --- the numbers the dbc-tools file pins --------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        self.assertEqual(int(re.search(r"^JAVELINS_CAST_MS = (\d+)", self.dt, re.M).group(1)),
                         int(self._const("kJavelinCastMs")))
        self.assertEqual(float(re.search(r"^JAVELIN_SPEED = ([\d.]+)", self.dt, re.M).group(1)), 18.0)
        self.assertEqual(self._const("kRecruits").replace(" ", ""), "5,7")
        self.assertEqual(self._const("kRankSpacingYd").replace(" ", ""), "8.f,7.f")
        self.assertEqual(self._const("kRingMs").replace(" ", ""), "6000,8000")
        self.assertEqual((self._const("kRingInnerYd"), self._const("kRingOuterYd")), ("5.f", "11.f"))
        self.assertEqual((self._const("kChargeWidthYd"), self._const("kChargeLengthYd")), ("4.f", "35.f"))
        self.assertEqual((self._const("kSpearsAngleDeg"), self._const("kSpearsLengthYd")), ("60.f", "10.f"))
        self.assertEqual((self._const("kJavelinRadiusYd"), self._const("kJavelinOffsetYd")), ("5.f", "5.f"))
        self.assertEqual((int(self._const("kReadyMs")), int(self._const("kJavelinFlightMs")),
                          int(self._const("kSecondVolleyWarnMs"))), (2500, 2500, 1500))


if __name__ == "__main__":
    unittest.main()
