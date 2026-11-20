"""
Blackrock Depths build WP-D22, Magmus and the Ironhand Guardians: source/npcs/blackrock_depths/magmus.py (the spells
211580-211591 and the two creature bindings), data/sql/updates/pending_db_world/rev_magmus_blackrock_depths.sql (his
three new texts), and the C++ side they must agree with (modules/mod-dungeon-bosses src/BlackrockDepths/
MagmusLogic.h and boss_magmus_rework.cpp).

Checks:
  - the twelve spells sit in the D22 slice and the C++ names the same ids; War Stomp is a 5 yd Physical hit whose
    percents ride in the effect (normal and EffectMiscValueB heroic) with a 2 s stun, bound to the kit's percent script;
    the five hits are resolve copies in the Fire school; the Fiery Burst bar is 2 s, 40 yd and interruptible; the looks
    are dest-targeted look-only spells with the V-1 visuals, the statue glow a 3 s aura and the pool look a lasting one;
  - the bindings (they are held back until BIND_WAVE_2 flips, so the columns are checked from the declaration's own
    call and, with the gate on, from the registry): the script names, SmartAI off, 170,000 normal health on the level
    56 warrior base, the stun set, INSTANCE_BIND, the stock DamageModifier; the statues keep their template;
  - the SQL: three texts (a boss emote and two yells, map-wide), no spawn and no SmartAI row;
  - the numbers the dbc-tools file pins (the stun, the percents, the radii, the glow) are the header's, and the registry
    tags are G2's drill rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_magmus.py
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
from source.npcs.blackrock_depths import _common as common  # noqa: E402
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "MagmusLogic.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_magmus_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_magmus_blackrock_depths.sql"
DECLARATION = TOOL_ROOT / "source" / "npcs" / "blackrock_depths" / "magmus.py"
# The BM drill (G2): present in the orchestrator's layout, absent elsewhere (the cross-check then skips).
BM_DRILL = Path("/home/plex/wow_server/worktrees/boss-mechanics-brd/src/MechanicDrill.h")

SLICE = range(211580, 211610)
(SPELL_STOMP, SPELL_BURST_CAST, SPELL_BURST, SPELL_BURST_LOOK, SPELL_IGNITION, SPELL_BURN, SPELL_WALL, SPELL_POOL,
 SPELL_GLOW, SPELL_BREATH, SPELL_END_LOOK, SPELL_POOL_LOOK) = range(211580, 211592)
NAMES = ("SPELL_MG_WAR_STOMP", "SPELL_MG_FIERY_BURST_CAST", "SPELL_MG_FIERY_BURST", "SPELL_MG_FIERY_BURST_LOOK",
         "SPELL_MG_CROSSFIRE_IGNITION", "SPELL_MG_CROSSFIRE_BURN", "SPELL_MG_FLAME_WALL", "SPELL_MG_DRIPPING_MAGMA",
         "SPELL_MG_STATUE_GLOW", "SPELL_MG_STATUE_BREATH", "SPELL_MG_CROSSFIRE_END_LOOK", "SPELL_MG_POOL_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_MOD_STUN = 4, 12
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY, TARGET_UNIT_TARGET_ENEMY, TARGET_DEST_DEST = 22, 15, 6, 87
TARGET_FLAG_DEST_LOCATION = 0x40
MECHANIC_STUN = 12
MAGMUS = 9938
STATUE = 8982
STALKER = 300796
# The stock looks the visuals name (read from the client Spell.dbc 2026-11-17): Flame Wreath 29947, Gout of Flame 15538,
# Flame Jets 62680, Fiery Burst 15668, War Stomp 15593, the shipped 4 yd lava pool state.
SV_FLAME_WREATH, SV_GOUT_OF_FLAME, SV_FLAME_JETS, SV_FIERY_BURST, SV_WAR_STOMP, SV_LAVA_POOL_4 = (
    4101, 3642, 13233, 516, 2355, 90606)


class MagmusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.npcs = npcs
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in npcs.creature_template_edits}
        cls.creatures = {int(e["entry"]) for e in npcs.creature_templates}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.declaration = DECLARATION.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d22_slice(self):
        self.assertEqual(sorted(self.spells), list(range(211580, 211592)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsMagmus{ 211580, 211609 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_MG_POOL_LOOK;")

    def test_war_stomp_is_a_physical_hit_and_a_two_second_stun(self):
        spell = self.spells[SPELL_STOMP]
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(spell["mechanic"], MECHANIC_STUN)
        self.assertEqual(spell["duration_ms"], 2000)           # the stock 8 s drops to 2 s (ruling 76)
        self.assertEqual(spell["cast_time_ms"], 0)
        hit, stun = spell["effect1"], spell["effect2"]
        self.assertEqual(hit["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual((hit["implicit_target_a"], hit["implicit_target_b"]),
                         (TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY))
        self.assertEqual(hit["radius_yards"], 5.0)
        self.assertEqual((stun["type"], stun["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_STUN))
        self.assertEqual((stun["implicit_target_a"], stun["implicit_target_b"]),
                         (TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY))
        self.assertEqual(stun["radius_yards"], 5.0)
        # the percents: hundredths, normal in the effect (base points + 1 for the die), heroic in EffectMiscValueB
        raw = spell["raw_overrides"]
        self.assertEqual(hit["base_points"] + hit["die_sides"], 1200)
        self.assertEqual(raw["EffectMiscValueB_1"], 1500)
        self.assertIn((SPELL_STOMP, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertEqual(self._const("kStompPct").replace(" ", ""), "12.f,15.f")
        self.assertEqual(self._const("kStompStunMs"), "2000")
        self.assertEqual(self._const("kStompRadiusYd"), "5.f")
        # ignores his modifiers (rule 2), always hits, cannot crit; the stock look
        self.assertTrue(raw["AttributesEx3"] & 0x20000000)
        self.assertEqual(raw["SpellVisualID_1"], SV_WAR_STOMP)
        # a copy in the slice, never the stock id (rule 15)
        self.assertNotIn(15593, self.spells)

    def test_the_fiery_burst_bar_is_two_seconds_and_interruptible(self):
        spell = self.spells[SPELL_BURST_CAST]
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["cast_time_ms"], 2000)
        self.assertEqual(spell["range_yards"], 40.0)
        self.assertEqual((spell["effect1"]["type"], spell["effect1"]["implicit_target_a"]),
                         (EFFECT_DUMMY, TARGET_UNIT_TARGET_ENEMY))
        raw = spell["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
        self.assertTrue(raw["AttributesEx2"] & 0x4)             # ignores line of sight
        self.assertFalse([s for s in self.scripts if s[0] == SPELL_BURST_CAST])
        self.assertEqual(int(self._const("kBurstCastMs")), 2000)
        self.assertEqual(self._const("kBurstRangeYd"), "40.f")
        self.assertEqual(self._const("kBurstRadiusYd"), "8.f")
        # the bots read it as the descriptor's kick
        self.assertIn("SPELL_MG_FIERY_BURST_CAST", self.script)
        self.assertRegex(self.script, r"d\.interrupts\.emplace_back\(NPC_MAGMUS, SPELL_MG_FIERY_BURST_CAST,")

    def test_the_hits_are_fire_resolve_copies(self):
        for spell_id in (SPELL_BURST, SPELL_IGNITION, SPELL_BURN, SPELL_WALL, SPELL_POOL):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)

    def test_the_looks_are_dest_targeted_and_use_the_v1_visuals(self):
        for spell_id, visual in ((SPELL_BURST_LOOK, SV_FIERY_BURST), (SPELL_BREATH, SV_GOUT_OF_FLAME),
                                 (SPELL_END_LOOK, SV_FLAME_JETS)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, spell_id)
            raw = spell["raw_overrides"]
            self.assertEqual(raw["SpellVisualID_1"], visual, spell_id)
            self.assertEqual(raw["Targets"], TARGET_FLAG_DEST_LOCATION, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
        self.assertEqual((visuals.MG_FIERY_BURST, visuals.MG_CROSSFIRE_BREATH, visuals.MG_CROSSFIRE_END),
                         (SV_FIERY_BURST, SV_GOUT_OF_FLAME, SV_FLAME_JETS))
        # the stomp's stock look is the Ring's Grizzle one (the same War Stomp visual): a shared-file request asks V-1
        # for an MG_ name
        self.assertEqual(visuals.GZ_EARTHSHAKER_STOMP, SV_WAR_STOMP)

    def test_the_statue_glow_and_the_pool_look_are_self_auras(self):
        glow = self.spells[SPELL_GLOW]
        self.assertEqual((glow["effect1"]["type"], glow["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(glow["duration_ms"], 3000)
        self.assertEqual(glow["raw_overrides"]["SpellVisualID_1"], SV_FLAME_WREATH)
        self.assertEqual(visuals.MG_STATUE_GLOW, SV_FLAME_WREATH)
        self.assertEqual(int(self._const("kGlowMs")), glow["duration_ms"])
        pool = self.spells[SPELL_POOL_LOOK]
        self.assertEqual((pool["effect1"]["type"], pool["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(pool["duration_ms"], -1)
        self.assertEqual(pool["raw_overrides"]["SpellVisualID_1"], visuals.MG_DRIPPING_MAGMA)
        self.assertEqual(visuals.MG_DRIPPING_MAGMA, SV_LAVA_POOL_4)
        self.assertEqual(visuals.MG_DRIPPING_MAGMA, visuals.SHIPPED_LAVA_POOL[4])
        # the stalker is the shared generic one the orchestrator declared
        self.assertRegex(self.header, rf"NPC_BRD_STALKER\s*=\s*{STALKER},")
        self.assertIn(STALKER, self.creatures)

    def test_no_wrong_listed_look_is_wired(self):
        # the Gout of Flame statue glow SV 3640 has only an animation (VISUALS report, Magmus): never the glow
        for spell in self.spells.values():
            self.assertNotEqual(spell["raw_overrides"].get("SpellVisualID_1"), 3640, spell["id"])

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = common.boss_columns("boss_magmus_rework", 62.986, damage_modifier=3.5)
        self.assertRegex(self.declaration, r"boss_columns\('boss_magmus_rework', 62\.986, damage_modifier=3\.5\)")
        self.assertEqual(c["ScriptName"], "boss_magmus_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], 1972)       # the kit's stun set (section 7 #10), not 1973
        self.assertEqual(c["flags_extra"], 1)
        self.assertEqual(c["DamageModifier"], 3.5)
        # 170,000 on the level 56 warrior class base 2,699 (spec "Build spec": about 63.0)
        self.assertAlmostEqual(c["HealthModifier"] * 2699, 170000, delta=10)

    def test_the_statues_are_rebound_and_nothing_else(self):
        self.assertIn("IRONHAND_COLUMNS = {'ScriptName': 'npc_ironhand_guardian_rework', 'AIName': ''}",
                      self.declaration)
        self.assertRegex(self.declaration, r"creature_template_columns\(8982, \*\*IRONHAND_COLUMNS\)")
        self.assertRegex(self.declaration, r"creature_template_columns\(9938, \*\*MAGMUS_COLUMNS\)")

    @unittest.skipUnless(common.BIND_WAVE_2, "the bindings register only while BIND_WAVE_2 is on")
    def test_the_bindings_register_with_the_gate_on(self):
        self.assertEqual(self.edits[MAGMUS]["ScriptName"], "boss_magmus_rework")
        self.assertEqual(self.edits[MAGMUS]["AIName"], "")
        self.assertEqual(self.edits[STATUE]["ScriptName"], "npc_ironhand_guardian_rework")
        self.assertEqual(self.edits[STATUE]["AIName"], "")

    @unittest.skipIf(common.BIND_WAVE_2, "with the gate on the bindings are registered (the test above)")
    def test_nothing_is_bound_with_the_gate_off(self):
        self.assertNotIn(MAGMUS, self.edits)
        self.assertNotIn(STATUE, self.edits)

    def test_no_boss_kit_add_is_declared(self):
        # the statues are stock scenery (6 spawns), the pools are stalker looks: no creature of this WP
        self.assertFalse([e for e in self.creatures if e in (MAGMUS, STATUE)])

    def test_the_script_names_are_the_ones_the_cpp_registers(self):
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(boss_magmus_rework,")
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(npc_ironhand_guardian_rework,")
        self.assertRegex(self.script, r'BrdTest::RegisterBoss\("magmus",')
        self.assertRegex(self.script, r"struct boss_magmus_rework : public BossAI")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_three_texts(self):
        rows = re.findall(r"^\(9938, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows],
                         [(1, 0, 41, 3), (2, 0, 14, 3), (3, 0, 14, 3)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts[0], "%s raises his fist, and the Ironhand Guardians turn!")
        self.assertEqual(texts[1], "Burn in the Emperor's hall!")
        self.assertEqual(texts[2], "The Emperor... will not... be disturbed...")
        # group 0 (the braziers yell) is the stock row and untouched
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9938 AND `GroupID` BETWEEN 1 AND 3;", self.sql)
        for name, group in (("EMOTE_MAGMUS_FIST", 1), ("YELL_MAGMUS_WALL", 2), ("YELL_MAGMUS_DEATH", 3),
                            ("SAY_MAGMUS_BRAZIERS_LIT", 0)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_MAGMUS, 0, 3, 1 \}")
        # the script says them
        for name in ("EMOTE_MAGMUS_FIST", "YELL_MAGMUS_WALL", "YELL_MAGMUS_DEATH"):
            self.assertIn(f"Talk({name})", self.script)

    def test_the_rev_adds_no_spawn_and_no_smartai(self):
        # rule 14: a rev that inserted spawns or SmartAI rows would have to set the heroic spawn mask / event flags
        self.assertNotIn("INSERT INTO `creature` ", self.sql)
        self.assertNotIn("smart_scripts", self.sql.replace("smart_scripts row", "").replace("smart_scripts` row", ""))

    # --- the numbers the spec names ----------------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("kBurstPct", "25.f,40.f"), ("kCrossfireIgnitionPct", "30.f,45.f"),
                               ("kCrossfireBurnPct", "10.f,15.f"), ("kWallPct", "10.f,15.f"),
                               ("kCrossfireEveryMs", "15000,12000"), ("kWallEveryMs", "30000,25000")):
            self.assertEqual(self._const(name).replace(" ", ""), expected, name)
        for name, expected in (("kBurstFirstMs", "6000"), ("kBurstEveryMs", "10000"), ("kCrossfireFirstMs", "8000"),
                               ("kWallFirstMs", "20000"), ("kLaneWidthYd", "10.f"), ("kWallStripYd", "12.f"),
                               ("kPoolPct", "8.f"), ("kPoolRadiusYd", "4.f"), ("kPoolLifeMs", "30000"),
                               ("kPoolEveryMs", "3000"), ("kPoolCap", "6")):
            self.assertEqual(self._const(name), expected, name)

    def test_the_tags_are_g2s_drill_rows(self):
        for name, value in (("TAG_MG_CROSSFIRE_IGNITION", 25), ("TAG_MG_CROSSFIRE_BURN", 26),
                            ("TAG_MG_FLAME_WALL", 27)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{value},", name)
        if not BM_DRILL.exists():
            self.skipTest("the BM drill source is not in this layout")
        drill = BM_DRILL.read_text(encoding="utf-8")
        self.assertRegex(drill, r"kBrd2BarTags\[\]\s*=\s*\{ 22, 25, 26, 27 \}")
        # the drill rows: the ignition at 3 s, the burn from 4 s for 5 s, the wall 8 s; width 10 and 12
        compact = re.sub(r'"\s*\n\s*"', "", drill)
        self.assertIn('"line 39 3000 width=10 offset=90 at=target shift=-19.5:0 school=fire pct=45 weak=1 '
                      'cycle=1/2 tag=25"', compact)
        self.assertIn('"line 39 4000 width=10 offset=90 at=target shift=-19.5:0 persist=5000 tick=1000 '
                      'school=fire pct=15 cycle=1/2 tag=26"', compact)
        self.assertIn('"line 40 3000 width=12 at=target shift=-20:13.5 persist=8000 tick=1000 school=fire pct=15 '
                      'cycle=1/2 tag=27"', compact)
        self.assertEqual(self._const("kGlowMs"), "3000")
        self.assertEqual(self._const("kBurnWarnMs"), "4000")
        self.assertEqual(self._const("kBurnLifeMs"), "5000")
        self.assertEqual(self._const("kBurnTickMs"), "1000")
        self.assertEqual(self._const("kWallLifeMs"), "8000")
        self.assertEqual(self._const("kWallTickMs"), "1000")
        # the script registers them on those timings
        self.assertIn("Ms(kGlowMs));", self.script)
        self.assertIn("Ms(kBurnWarnMs));", self.script)
        self.assertIn("Persistent(Ms(kBurnLifeMs), Ms(kBurnTickMs))", self.script)
        self.assertIn("Persistent(Ms(kWallLifeMs), Ms(kWallTickMs))", self.script)


if __name__ == "__main__":
    unittest.main()
