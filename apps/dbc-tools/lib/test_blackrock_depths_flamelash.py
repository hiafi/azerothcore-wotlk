"""
Blackrock Depths build WP-D20, Ambassador Flamelash, his Burning Spirits and the Portal Anchor:
source/npcs/blackrock_depths/flamelash.py (the unit columns, the anchor's template and the spells 211490-211499),
data/sql/updates/pending_db_world/rev_flamelash_blackrock_depths.sql (his three new texts), and the C++ side they must
agree with (modules/mod-dungeon-bosses src/BlackrockDepths/FlamelashLogic.h and boss_ambassador_flamelash_rework.cpp).

The file declares the wave 2 unit columns only while BIND_WAVE_2 is on (_common.py); this test loads the declaration
file twice from a scratch copy of the package (the gate off, then on) so every check runs whatever the real switch says.

Checks:
  - the ten spells sit in the D20 slice and the C++ names the same ids; Fire Blast is the copy of the stock 13342 (Fire,
    20 yd, 15% / 20% of the row through the script, never the shared id), the two Kindling ticks are 8% / 12% and 3% /
    5% Fire hits on the same script, the stack aura is +10% damage and +5% size, 30 s, ten at most, the channel is a
    real channel nothing interrupts, the looks are the V-1 visuals, the trail patch a Fire resolve copy;
  - the creatures: Flamelash's columns (script, SmartAI off, 150,000, stun immunity 1972, INSTANCE_BIND), the Burning
    Spirit's (script, 3,000 health, no Fire immunity, standing still), the Portal Anchor (8,000, no melee, stun
    immunity, the invisible display, the heroic link 310416); with the gate off the first two are stock and the anchor
    and the spells are declared anyway;
  - the SQL: three new texts for 9156 (a yell, a boss emote, a yell), the stock aggro line left alone;
  - the numbers the dbc-tools file pins are the header's, and no literal visual id sits in the file (rule 4).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_flamelash.py
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "FlamelashLogic.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_ambassador_flamelash_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_flamelash_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
DT_FILE = PACKAGE / "flamelash.py"

SLICE = range(211490, 211520)
(SPELL_PORTAL, SPELL_STACK, SPELL_ARRIVAL, SPELL_BLAST, SPELL_KINDLING, SPELL_KINDLED, SPELL_BURN_OTHERS,
 SPELL_BURN_SELF, SPELL_TRAIL_LOOK, SPELL_TRAIL) = range(211490, 211500)
NAMES = ("SPELL_FL_PORTAL", "SPELL_FL_BURNING_SPIRIT", "SPELL_FL_ARRIVAL_LOOK", "SPELL_FL_FIRE_BLAST",
         "SPELL_FL_KINDLING", "SPELL_FL_KINDLED", "SPELL_FL_KINDLING_BURN", "SPELL_FL_KINDLING_SELF",
         "SPELL_FL_TRAIL_LOOK", "SPELL_FL_TRAIL")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_SCALE = 4, 79, 61
SCHOOL_FIRE = 4
FLAMELASH, SPIRIT, ANCHOR, STALKER = 9156, 9178, 300842, 300796
ATTR1_IS_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
IMMUNITY_BOSS_STUN = 1972
DISPLAY_INVISIBLE_STALKER = 11686
STOCK_FIRE_BLAST = 13342


def _load(bound: bool):
    """The declaration package as the registry loads it with BIND_WAVE_2 forced to `bound`: a scratch copy of
    _common.py (the switch rewritten), _visuals.py and flamelash.py."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "blackrock_depths"
        root.mkdir()
        common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        common, count = re.subn(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", f"BIND_WAVE_2 = {bound}", common, flags=re.M)
        assert count == 1
        (root / "_common.py").write_text(common, encoding="utf-8")
        for name in ("_visuals.py", "flamelash.py"):
            shutil.copy(PACKAGE / name, root / name)
        t = id_blocks
        return registry.load_class_package(
            root, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
            shapeshift_index={}, existing_creature_rows=t._AnyRows(),
            creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=t.spell_tables.dsl_live_data(
                {}, t.spell_tables.load_live_item_template_rows,
                lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
                lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
                lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
            ),
        )


class FlamelashTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bound = _load(True)
        cls.unbound = _load(False)
        cls.spells = {int(e["id"]): e for e in cls.bound.spells}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in cls.bound.spell_script_names}
        cls.edits = {int(e["entry"]): e for e in cls.bound.creature_template_edits}
        cls.creatures = {int(e["entry"]): e for e in cls.bound.creature_templates}
        cls.models = [e for e in cls.bound.creature_template_models]
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.source = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d20_slice(self):
        self.assertEqual(sorted(self.spells), list(range(211490, 211500)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsFlamelash{ 211490, 211519 }", re.sub(r"\s+", " ", self.header))

    def test_the_gate_does_not_hide_the_spells(self):
        self.assertEqual(sorted(int(e["id"]) for e in self.unbound.spells), list(range(211490, 211500)))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_FL_TRAIL;")

    def test_fire_blast_is_a_copy_of_the_stock_spell_scaled_by_the_script(self):
        spell = self.spells[SPELL_BLAST]
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["cast_time_ms"], 0)
        self.assertNotIn(STOCK_FIRE_BLAST, self.spells)             # rule 15: a copy, never the shared id
        self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        raw = spell["raw_overrides"]
        # the percent in hundredths: normal in the effect (base points + the die), heroic in EffectMiscValueB
        self.assertEqual(spell["effect1"]["base_points"] + spell["effect1"]["die_sides"], 1500)
        self.assertEqual(raw["EffectMiscValueB_1"], 2000)
        self.assertEqual(self._const("kFireBlastPct").replace(" ", ""), "15.f,20.f")
        self.assertEqual(self._const("kFireBlastRangeYd"), "20.f")
        self.assertEqual(spell["range_yards"], 20.0)
        self.assertIn((SPELL_BLAST, "spell_brd_flamelash_damage"), self.scripts)
        # ignores his modifiers (rule 2), nothing interrupts an instant
        self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (0, 0))
        self.assertEqual((spell["dispel"], spell["mechanic"]), (0, 0))

    def test_the_two_kindling_ticks_are_fire_hits_on_the_scripts_percent(self):
        for spell_id, hundredths, heroic, name in ((SPELL_BURN_OTHERS, 800, 1200, "kKindlingOthersPct"),
                                                   (SPELL_BURN_SELF, 300, 500, "kKindlingSelfPct")):
            spell = self.spells[spell_id]
            raw = spell["raw_overrides"]
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"] + spell["effect1"]["die_sides"], hundredths, spell_id)
            self.assertEqual(raw["EffectMiscValueB_1"], heroic, spell_id)
            self.assertEqual(self._const(name).replace(" ", ""), f"{hundredths // 100}.f,{heroic // 100}.f", name)
            self.assertIn((spell_id, "spell_brd_flamelash_damage"), self.scripts, spell_id)
            self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
        # the target burns less than the others
        self.assertLess(self.spells[SPELL_BURN_SELF]["effect1"]["base_points"],
                        self.spells[SPELL_BURN_OTHERS]["effect1"]["base_points"])

    def test_the_stack_is_plus_ten_percent_damage_and_five_percent_size_ten_at_most(self):
        spell = self.spells[SPELL_STACK]
        self.assertEqual(spell["duration_ms"], 30000)
        self.assertEqual(self._const("kStackLifeMs"), "30000")
        damage, size = spell["effect1"], spell["effect2"]
        self.assertEqual((damage["apply_aura"], damage["base_points"], damage["misc_value"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, 10, 127))
        self.assertEqual((size["apply_aura"], size["base_points"]), (AURA_MOD_SCALE, 5))
        self.assertEqual(self._const("kStackDamagePctPerStack"), "10.f")
        self.assertEqual(self._const("kStackSizePctPerStack"), "5.f")
        self.assertEqual(spell["raw_overrides"]["CumulativeAura"], 10)
        self.assertEqual(self._const("kStackCap"), "10")
        self.assertEqual((spell["dispel"], spell["mechanic"]), (0, 0))

    def test_kindling_is_a_real_channel_nothing_interrupts(self):
        spell = self.spells[SPELL_KINDLING]
        raw = spell["raw_overrides"]
        self.assertTrue(raw["AttributesEx"] & ATTR1_IS_CHANNELED)
        self.assertEqual(spell["duration_ms"], 8000)
        self.assertEqual(int(self._const("kKindlingMs")), 8000)
        self.assertEqual((raw["ChannelInterruptFlags"], raw["InterruptFlags"], raw["PreventionType"]), (0, 0, 0))
        self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(raw["SpellVisualID_1"], visuals.FL_KINDLING_CHANNEL)
        # the mark on the target: an Ignite state for the same 8 s
        mark = self.spells[SPELL_KINDLED]
        self.assertEqual(mark["duration_ms"], 8000)
        self.assertEqual(mark["raw_overrides"]["SpellVisualID_1"], visuals.FL_KINDLING_STATE)
        self.assertEqual((mark["dispel"], mark["mechanic"]), (0, 0))
        # his immunity set holds no interrupt, so the channel's own flags are what protect it
        self.assertEqual(self.edits[FLAMELASH]["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)

    def test_the_looks_use_the_v1_visuals(self):
        self.assertEqual(self.spells[SPELL_PORTAL]["raw_overrides"]["SpellVisualID_1"], visuals.FL_PORTAL_ANCHOR)
        self.assertEqual(visuals.FL_PORTAL_ANCHOR, 90658)
        self.assertEqual(self.spells[SPELL_ARRIVAL]["raw_overrides"]["SpellVisualID_1"],
                         visuals.FL_BURNING_SPIRIT_STACK)
        self.assertEqual(visuals.FL_BURNING_SPIRIT_STACK, 3321)
        self.assertEqual(self.spells[SPELL_TRAIL_LOOK]["raw_overrides"]["SpellVisualID_1"], visuals.FL_BURNING_TRAIL)
        # the shipped 4 yd lava pool state (a rung of Blackrock Spire's ladder)
        self.assertEqual(visuals.FL_BURNING_TRAIL, visuals.SHIPPED_LAVA_POOL[4])
        for spell_id in (SPELL_PORTAL, SPELL_TRAIL_LOOK):
            self.assertEqual(self.spells[spell_id]["duration_ms"], -1, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_DUMMY, spell_id)
        # Kindling's channel is never the blue Fire Beam (V-1: SV 10856), the portal never the 12 yd fallback
        self.assertNotEqual(visuals.FL_KINDLING_CHANNEL, 10856)
        self.assertNotEqual(visuals.FL_PORTAL_ANCHOR, visuals.FL_PORTAL_ANCHOR_ALT)
        # a look spell is cast on the caster (an aura on the stalker or the anchor itself)
        self.assertEqual(self.spells[SPELL_ARRIVAL]["effect1"]["type"], EFFECT_DUMMY)

    def test_the_trail_patch_is_a_fire_resolve_copy(self):
        spell = self.spells[SPELL_TRAIL]
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertIn((SPELL_TRAIL, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(self._const("kTrailPctPerTick"), "8.f")
        self.assertEqual(self._const("kTrailLifeMs"), "15000")
        self.assertEqual(self._const("kTrailRadius"), "4.f")
        self.assertEqual(self._const("kTrailMax"), "4")

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.edits[FLAMELASH]
        self.assertEqual(c["ScriptName"], "boss_ambassador_flamelash_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)     # the stock -251 goes
        self.assertEqual(c["flags_extra"], 1)
        self.assertEqual(c["DamageModifier"], 3.5)
        # 150,000 on the level 55 warrior class base 2,614 (spec "Build spec": about 57.4)
        self.assertAlmostEqual(c["HealthModifier"] * 2614, 150000, delta=10)

    def test_the_spirits_columns(self):
        c = self.edits[SPIRIT]
        self.assertEqual(c["ScriptName"], "npc_burning_spirit_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], 0)      # no Fire immunity: a must-kill add (handoff s7 #10)
        self.assertEqual(c["MovementType"], 0)
        # 3,000 on the level 30 warrior class base 955
        self.assertAlmostEqual(c["HealthModifier"] * 955, 3000, delta=1)
        self.assertNotIn("flags_extra", c)                  # not an encounter boss

    def test_the_gate_holds_the_stock_units_back(self):
        edits = {int(e["entry"]) for e in self.unbound.creature_template_edits}
        self.assertNotIn(FLAMELASH, edits)
        self.assertNotIn(SPIRIT, edits)
        self.assertIn(ANCHOR, {int(e["entry"]) for e in self.unbound.creature_templates})

    def test_the_portal_anchor(self):
        c = self.creatures[ANCHOR]
        self.assertEqual(c["ScriptName"], "npc_brd_portal_anchor_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["rank"], c["unit_class"]), (55, 55, 1, 1))
        self.assertAlmostEqual(c["HealthModifier"] * 2614, 8000, delta=3)
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertEqual(c["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(c["MovementType"], 0)
        self.assertEqual((c["lootid"], c["mingold"], c["maxgold"], c["ExperienceModifier"]), (0, 0, 0, 0.0))
        self.assertEqual(c["unit_flags"], 0)                # attackable and selectable: the group destroys it
        self.assertEqual(c["difficulty_entry_1"], 310416)   # STAGE-H-REPORT section 3
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"creature": [ANCHOR]}), [])
        self.assertRegex(self.header, rf"NPC_BRD_PORTAL_ANCHOR\s*=\s*{ANCHOR},")

    def test_the_portal_anchors_display_is_the_invisible_stalker(self):
        self.assertEqual(visuals.DISPLAY_INVISIBLE_STALKER, DISPLAY_INVISIBLE_STALKER)
        models = [m for m in self.models if int(m["CreatureID"]) == ANCHOR]
        self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [DISPLAY_INVISIBLE_STALKER])

    def test_the_script_names_are_the_ones_the_cpp_registers(self):
        for ai in ("boss_ambassador_flamelash_rework", "npc_burning_spirit_rework", "npc_brd_portal_anchor_rework"):
            self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({ai},", ai)
        self.assertRegex(self.script, r"RegisterSpellScript\(spell_brd_flamelash_damage\)")
        self.assertRegex(self.script, r'BrdTest::RegisterBoss\("flamelash",')
        # the three AIs register only once wave 2 binds (an unbound name logs "not assigned" at boot)
        for ai in ("boss_ambassador_flamelash_rework", "npc_burning_spirit_rework", "npc_brd_portal_anchor_rework"):
            self.assertRegex(re.sub(r"\s+", " ", self.script),
                             rf"if \(kWave2Bound\) RegisterDungeonReworkCreatureAI\({ai},")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_three_new_texts(self):
        rows = re.findall(r"^\(9156, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows],
                         [(1, 0, 14, 0), (2, 0, 41, 3), (3, 0, 14, 0)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts[0], "The Firelands answer their master's call!")
        self.assertEqual(texts[1], "%s kindles $n!")
        self.assertEqual(texts[2], "Ragnaros... will hear of this...")
        # the stock aggro line (group 0) is left alone
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9156 AND `GroupID` BETWEEN 1 AND 3;", self.sql)
        self.assertNotRegex(self.sql, r"\(9156, 0, ")
        for name, group in (("SAY_PORTAL", 1), ("EMOTE_KINDLING", 2), ("SAY_DEATH", 3)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_FLAMELASH, 0, 3, 1 \}")

    def test_the_rev_adds_no_spawn_and_no_smart_script(self):
        # rule 14 only bites a rev that inserts spawns or SmartAI rows: this one does neither
        self.assertNotRegex(self.sql, r"INSERT INTO `(creature|smart_scripts)`")

    # --- the numbers --------------------------------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("kPortalFirstMs", "10000,10000"), ("kPortalEveryMs", "30000,20000"),
                               ("kSpillEveryMs", "3000,2000"), ("kKindlingEveryMs", "25000,20000"),
                               ("kKindlingRadius", "8.f,10.f"), ("kKindlingOthersPct", "8.f,12.f"),
                               ("kKindlingSelfPct", "3.f,5.f")):
            self.assertEqual(self._const(name).replace(" ", ""), expected, name)
        for name, expected in (("kKindlingFirstMs", "15000"), ("kKindlingTickMs", "1000"),
                               ("kTrailEveryMs", "2000"), ("kFireBlastFirstMs", "2000"),
                               ("kFireBlastEveryMs", "7000")):
            self.assertEqual(self._const(name), expected, name)

    def test_the_spirit_boss_and_anchor_healths_match_the_build_spec(self):
        # 150k boss / 8k anchor / 3k spirit (handoff 3.6), heroic 210k / 12k / 4.5k are WP-H's overrides
        self.assertAlmostEqual(self.edits[FLAMELASH]["HealthModifier"] * 2614, 150000, delta=10)
        self.assertAlmostEqual(self.creatures[ANCHOR]["HealthModifier"] * 2614, 8000, delta=3)
        self.assertAlmostEqual(self.edits[SPIRIT]["HealthModifier"] * 955, 3000, delta=1)

    def test_no_literal_visual_id_sits_in_the_file(self):
        # rule 4: _visuals.py constants only
        self.assertNotRegex(self.source, r"SpellVisualID_\d\s*=\s*\d")
        self.assertNotRegex(self.source, r"display_id\s*=\s*\d")

    def test_the_stalker_the_trail_uses_is_the_orchestrators_generic_one(self):
        self.assertRegex(self.header, rf"NPC_BRD_STALKER\s*=\s*{STALKER},")
        self.assertRegex(self.script, r"NPC_BRD_STALKER")


if __name__ == "__main__":
    unittest.main()
