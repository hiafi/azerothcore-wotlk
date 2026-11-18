"""
Blackrock Depths build WP-D13, Bael'Gar and the Fallen Boulder: source/npcs/blackrock_depths/baelgar.py (his template
columns and the spells 211230-211242), data/sql/updates/pending_db_world/rev_baelgar_blackrock_depths.sql (his four
texts and the Boulder's gameobject template), and the C++ side they must agree with (modules/mod-dungeon-bosses
src/BlackrockDepths/BaelgarLogic.h and boss_baelgar_rework.cpp).

Checks:
  - the thirteen spells sit in the D13 slice and the C++ names the same ids; Magma Splash is a Fire hit, a 30 s Fire
    DoT and -250 armor whose percents ride in the effects (normal and EffectMiscValueB heroic) and bind the kit's two
    percent scripts; the five hits are resolve copies in the right schools; the two cast bars are 5 s and 2 s and not
    interruptible; the four looks are dest-targeted look-only spells with the V-1 visuals and the lava look a lasting
    aura on a stalker;
  - his creature columns: the script, SmartAI off, 200,000 normal health on the level 52 warrior base, Fire and stun
    immunity (1973), INSTANCE_BIND, the stock DamageModifier;
  - the SQL: four texts (a boss emote and three emotes, map-wide), the Boulder a generic, non-selectable object whose
    display is the C++ constant and the V-1 constant, ids in the reservation;
  - the numbers the dbc-tools file pins (Magma Splash, the cast times) are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_baelgar.py
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
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "BaelgarLogic.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_baelgar_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_baelgar_blackrock_depths.sql"

SLICE = range(211230, 211260)
(SPELL_MAGMA, SPELL_ROCKFALL, SPELL_BOULDER, SPELL_FURNACE_CAST, SPELL_FURNACE, SPELL_FISSURE_CAST, SPELL_FISSURE,
 SPELL_LAVA, SPELL_ROCKFALL_LOOK, SPELL_LAND_LOOK, SPELL_MELT_LOOK, SPELL_BURST_LOOK, SPELL_LAVA_LOOK) = range(
    211230, 211243)
NAMES = ("SPELL_BG_MAGMA_SPLASH", "SPELL_BG_ROCKFALL", "SPELL_BG_FALLING_BOULDER", "SPELL_BG_MOLTEN_FURNACE_CAST",
         "SPELL_BG_MOLTEN_FURNACE", "SPELL_BG_FISSURE_CAST", "SPELL_BG_FISSURE", "SPELL_BG_FISSURE_LAVA",
         "SPELL_BG_ROCKFALL_LOOK", "SPELL_BG_BOULDER_LAND_LOOK", "SPELL_BG_BOULDER_MELT_LOOK",
         "SPELL_BG_FISSURE_BURST_LOOK", "SPELL_BG_FISSURE_LAVA_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_RESISTANCE = 4, 3, 22
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
TARGET_DEST_DEST = 87
TARGET_FLAG_DEST_LOCATION = 0x40
BOULDER_GO = 301281
GENERIC = 5
GO_FLAG_NOT_SELECTABLE = 16
BAELGAR = 9016
STALKER = 300796
SV_HEAT_WAVE, SV_ROCK_SHOWER, SV_BOULDER_IMPACT = 3119, 12855, 12714
SV_BOULDER_MELT, SV_FISSURE_BURST, SV_MAGMA = 8097, 10917, 3221


class BaelgarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names}
        cls.columns = next(e for e in npcs.creature_template_edits if int(e["entry"]) == BAELGAR)
        cls.creatures = {int(e["entry"]) for e in npcs.creature_templates}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d13_slice(self):
        self.assertEqual(sorted(self.spells), list(range(211230, 211243)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsBaelgar{ 211230, 211259 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_BG_FISSURE_LAVA_LOOK;")

    def test_magma_splash_is_a_fire_hit_a_dot_and_armor(self):
        spell = self.spells[SPELL_MAGMA]
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["duration_ms"], 30000)
        hit, dot, armor = spell["effect1"], spell["effect2"], spell["effect3"]
        self.assertEqual(hit["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(dot["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(dot["amplitude"], 3000)
        self.assertEqual((armor["apply_aura"], armor["misc_value"], armor["base_points"]),
                         (AURA_MOD_RESISTANCE, 1, -250))
        # the percents: hundredths, normal in the effect (base points + 1 for the die), heroic in EffectMiscValueB
        raw = spell["raw_overrides"]
        self.assertEqual(hit["base_points"] + hit["die_sides"], 1000)
        self.assertEqual(raw["EffectMiscValueB_1"], 1500)
        self.assertEqual(dot["base_points"], 150)
        self.assertEqual(raw["EffectMiscValueB_2"], 250)
        self.assertIn((SPELL_MAGMA, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertIn((SPELL_MAGMA, "spell_dungeon_refflat_periodic"), self.scripts)
        # the header says the same
        self.assertEqual(self._const("kMagmaSplashHitPct").replace(" ", ""), "10.f,15.f")
        self.assertEqual(self._const("kMagmaSplashTickPct").replace(" ", ""), "1.5f,2.5f")
        self.assertEqual(self._const("kMagmaSplashTickMs"), "3000")
        self.assertEqual(self._const("kMagmaSplashDotMs"), "30000")
        self.assertEqual(self._const("kMagmaSplashArmor"), "-250")
        self.assertEqual(raw["SpellVisualID_1"], SV_MAGMA)
        # ignores his modifiers (rule 2), always hits
        self.assertTrue(raw["AttributesEx3"] & 0x20000000)
        # not dispellable, no mechanic (stock)
        self.assertEqual((spell["dispel"], spell["mechanic"]), (0, 0))
        # a copy in the slice, never the stock id (rule 15)
        self.assertNotIn(13880, self.spells)

    def test_the_hits_are_resolve_copies_in_their_schools(self):
        for spell_id, school in ((SPELL_ROCKFALL, SCHOOL_PHYSICAL), (SPELL_BOULDER, SCHOOL_PHYSICAL),
                                 (SPELL_FURNACE, SCHOOL_FIRE), (SPELL_FISSURE, SCHOOL_FIRE), (SPELL_LAVA, SCHOOL_FIRE)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)
        # the Furnace plays Heat Wave's look on its targets (the breath and the burning state)
        self.assertEqual(self.spells[SPELL_FURNACE]["raw_overrides"]["SpellVisualID_1"], SV_HEAT_WAVE)
        self.assertEqual(visuals.BG_MOLTEN_FURNACE, SV_HEAT_WAVE)

    def test_the_cast_bars_are_not_interruptible(self):
        for spell_id, cast_ms, header_name in ((SPELL_FURNACE_CAST, 5000, "kFurnaceCastMs"),
                                               (SPELL_FISSURE_CAST, 2000, "kFissureWarnMs")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["cast_time_ms"], cast_ms, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, spell_id)
            raw = spell["raw_overrides"]
            self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (0, 0), spell_id)
            self.assertEqual(int(self._const(header_name)), cast_ms, header_name)
            self.assertFalse([s for s in self.scripts if s[0] == spell_id], spell_id)

    def test_the_looks_are_dest_targeted_and_use_the_v1_visuals(self):
        for spell_id, visual in ((SPELL_ROCKFALL_LOOK, SV_ROCK_SHOWER), (SPELL_LAND_LOOK, SV_BOULDER_IMPACT),
                                 (SPELL_MELT_LOOK, SV_BOULDER_MELT), (SPELL_BURST_LOOK, SV_FISSURE_BURST)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, spell_id)
            raw = spell["raw_overrides"]
            self.assertEqual(raw["SpellVisualID_1"], visual, spell_id)
            self.assertEqual(raw["Targets"], TARGET_FLAG_DEST_LOCATION, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
        self.assertEqual((visuals.BG_ROCKFALL, visuals.BG_BOULDER_LAND, visuals.BG_BOULDER_MELT,
                          visuals.BG_FISSURE_BURST), (SV_ROCK_SHOWER, SV_BOULDER_IMPACT, SV_BOULDER_MELT,
                                                      SV_FISSURE_BURST))

    def test_the_lava_look_is_a_lasting_aura_on_a_stalker(self):
        spell = self.spells[SPELL_LAVA_LOOK]
        self.assertEqual(spell["duration_ms"], -1)
        self.assertEqual((spell["effect1"]["type"], spell["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visuals.BG_FISSURE_LAVA)
        # the shipped 4 yd lava pool state, one every 6 yd
        self.assertEqual(visuals.BG_FISSURE_LAVA, visuals.SHIPPED_LAVA_POOL[4])
        self.assertEqual(self._const("kLavaLookEveryYd"), "6.f")
        # the stalker is the shared generic one the orchestrator declared
        self.assertRegex(self.header, rf"NPC_BRD_STALKER\s*=\s*{STALKER},")
        self.assertIn(STALKER, self.creatures)

    # --- the creature -------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.columns
        self.assertEqual(c["ScriptName"], "boss_baelgar_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], 1973)      # 1972 plus the Fire school (section 7 #10)
        self.assertEqual(c["flags_extra"], 1)
        self.assertEqual(c["DamageModifier"], 3.5)
        # 200,000 on the level 52 warrior class base 2,371 (spec "Build spec": about 84.4)
        self.assertAlmostEqual(c["HealthModifier"] * 2371, 200000, delta=10)

    def test_no_boss_kit_add_is_declared(self):
        # the Spawn of Bael'Gar 9436 is retired and the Boulder is an object: nothing of this WP is a creature
        self.assertNotIn(9436, self.creatures)
        # 300828 is D12's Hand of Incendius (the Lord of the Lake's stand-in), not this WP's
        self.assertFalse([e for e in self.creatures if 300797 <= e <= 300829 and e != 300828])

    def test_the_boulder_carrier_is_never_the_tank(self):
        # R-1-B m11 (orchestrator default): the carrier pick excludes the tank, the Rockfall circles do not.
        self.assertRegex(self.logic, r"kBoulderCarrierNonTank = true;")
        self.assertRegex(self.logic, r"kRockfallNonTank = false;")
        self.assertIn("FightPlayers({}, 1, kBoulderCarrierNonTank)", self.script)
        self.assertIn("FightPlayers(exclude, wanted, kRockfallNonTank)", self.script)

    def test_the_script_name_is_the_one_the_cpp_registers(self):
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(boss_baelgar_rework,")
        self.assertRegex(self.script, r'BrdTest::RegisterBoss\("baelgar",')

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_four_texts(self):
        rows = re.findall(r"^\(9016, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows],
                         [(0, 0, 41, 3), (1, 0, 16, 3), (2, 0, 16, 3), (3, 0, 16, 3)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts[0], "%s stokes the Molten Furnace! Get out of sight!")
        self.assertEqual(texts[1], "The boulders melt into slag!")
        self.assertEqual(texts[2], "%s slams the ground and the floor cracks open!")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9016 AND `GroupID` BETWEEN 0 AND 3;", self.sql)
        # the C++ names the same groups, inside the header's range 0-3
        for name, group in (("EMOTE_BAELGAR_FURNACE", 0), ("EMOTE_BAELGAR_MELT", 1), ("EMOTE_BAELGAR_FISSURE", 2),
                            ("EMOTE_BAELGAR_BOULDER", 3)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_BAELGAR, 0, 3, 0 \}")

    def test_the_boulder_is_a_generic_not_selectable_object(self):
        row = re.search(r"^\(301281, (\d+), (\d+), 'Fallen Boulder', '', '', '', ([\d.]+),", self.sql, re.M)
        self.assertIsNotNone(row)
        self.assertEqual((int(row.group(1)), int(row.group(2)), float(row.group(3))), (GENERIC, 3711, 1.0))
        addon = re.search(r"^\(301281, 0, (\d+), 0, 0, 0, 0, 0, 0\);", self.sql, re.M)
        self.assertEqual(int(addon.group(1)), GO_FLAG_NOT_SELECTABLE)
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"gameobject": [BOULDER_GO]}), [])
        self.assertIn("DELETE FROM `gameobject_template_addon` WHERE `entry` = 301281;", self.sql)
        self.assertRegex(self.header, rf"GO_BRD_FALLEN_BOULDER\s*=\s*{BOULDER_GO},")
        # no spawn: the script summons it
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)

    def test_one_display_everywhere(self):
        # the C++ constant decides the model; the template's displayId and the V-1 constant equal it
        self.assertEqual(int(self._const("kBoulderDisplay")), 3711)
        self.assertEqual(visuals.GODI_FALLEN_BOULDER, 3711)
        self.assertEqual(visuals.GODI_FALLEN_BOULDER_ALT, 5736)        # the fallback, one constant away
        self.assertRegex(self.sql, r"\(301281, 5, 3711, 'Fallen Boulder'")
        self.assertIn("kBoulderDisplay", self.script)

    def test_the_hide_tag_is_the_drills(self):
        # BM MechanicDrill.h kBrdTagHide = 16 (the `hide` row of blackrock-depths-shapes, gated at 0)
        self.assertRegex(self.logic, r"TAG_BG_FURNACE\s*=\s*16,")
        self.assertIn("Mechanic::Hide(me, spec, Ms(kFurnaceCastMs))", self.script)

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("kRockfallPct", "15.f,25.f"), ("kBoulderPct", "40.f,60.f"),
                               ("kFurnacePct", "80.f,95.f"), ("kFissurePct", "25.f,40.f"),
                               ("kLavaPctPerTick", "6.f,6.f"), ("kRockfallEveryMs", "15000,12000"),
                               ("kFurnaceEveryMs", "40000,35000"), ("kFissureEveryMs", "30000,20000")):
            self.assertEqual(self._const(name).replace(" ", ""), expected, name)
        for name, expected in (("kRockfallFirstMs", "5000"), ("kFurnaceFirstMs", "40000"),
                               ("kFissureFirstMs", "15000"), ("kRockfallWarnMs", "1500"), ("kBoulderWarnMs", "3000"),
                               ("kRockfallCircles", "5")):
            self.assertEqual(self._const(name), expected, name)


if __name__ == "__main__":
    unittest.main()
