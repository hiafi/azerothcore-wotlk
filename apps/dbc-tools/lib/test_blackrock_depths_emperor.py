"""
Blackrock Depths build WP-D23, Emperor Dagran Thaurissan and Princess Moira: source/npcs/blackrock_depths/emperor.py
(the spells 211610-211631, the Imperial Guard 300843 and the Twilight's Hammer Ambassador 300844, the three bosses'
bindings), data/sql/updates/pending_db_world/rev_emperor_blackrock_depths.sql (the texts), and the C++ side they must
agree with (modules/mod-dungeon-bosses src/BlackrockDepths/EmperorLogic.h, boss_emperor_dagran_thaurissan_rework.cpp,
boss_moira_bronzebeard_rework.cpp).

Checks:
  - the 22 spells sit in the D23 slice and the C++ names the same ids; the copies of stock spells (Hand of Thaurissan,
    Mind Blast) carry their percents in the effect (normal) and EffectMiscValueB (heroic) on the kit's percent script,
    with the rescaled stun and cast; Necrosis is a Magic DoT on the periodic percent script; the two channels are not
    interruptible; the registry hits are resolve copies in their school; the heals are exact (base point 0); the
    enrage aura has no immunity; the looks use V-2's visuals and no WRONG-listed one;
  - the adds: their columns, models, the heroic lock lines (WP-H) and the scripts the C++ registers;
  - the bindings (held back until BIND_WAVE_2 flips): the script names, SmartAI off, the spec's normal health, 1972,
    INSTANCE_BIND, the stock DamageModifier;
  - the SQL: Dagran's six new texts (three yells, three boss emotes), the Nemesis emote on Moira and the Priestess, no
    spawn and no SmartAI row;
  - the numbers the dbc-tools file pins are the header's, and the beam is G2's drill row (tag 21).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_emperor.py
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
LOGIC = MDB / "src" / "BlackrockDepths" / "EmperorLogic.h"
FIGHT = MDB / "src" / "BlackrockDepths" / "EmperorFight.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_emperor_dagran_thaurissan_rework.cpp"
MOIRA_SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_moira_bronzebeard_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_emperor_blackrock_depths.sql"
DECLARATION = TOOL_ROOT / "source" / "npcs" / "blackrock_depths" / "emperor.py"
BM_DRILL = Path("/home/plex/wow_server/worktrees/boss-mechanics-brd/src/MechanicDrill.h")

SLICE = range(211610, 211660)
NAMES = ("SPELL_EM_HAND_OF_THAURISSAN", "SPELL_EM_NEMESIS", "SPELL_EM_RADIANT_BURN", "SPELL_EM_NEMESIS_HEAL",
         "SPELL_EM_MIND_BLAST", "SPELL_EM_NECROSIS", "SPELL_EM_TWILIGHT_TETHER", "SPELL_EM_TWILIGHT_BURN",
         "SPELL_EM_TETHER_HEAL", "SPELL_EM_FLAMESTRIKE", "SPELL_EM_FLAMESTRIKE_BURN", "SPELL_EM_FLAMESTRIKE_LOOK",
         "SPELL_EM_FLAMESTRIKE_GROUND", "SPELL_EM_AVATAR_OF_FLAME", "SPELL_EM_FLAMES", "SPELL_EM_FIRESTORM",
         "SPELL_EM_FIRESTORM_LOOK", "SPELL_EM_HAMMER_SLAM_CAST", "SPELL_EM_HAMMER_SLAM", "SPELL_EM_HAMMER_SLAM_LOOK",
         "SPELL_EM_MOIRA_CAGE", "SPELL_EM_MOIRA_CAGE_WHIRL")
(HAND, NEMESIS, RADIANT_BURN, NEMESIS_HEAL, MIND_BLAST, NECROSIS, TETHER, TETHER_BURN, TETHER_HEAL, FLAMESTRIKE,
 FLAMESTRIKE_BURN, FLAMESTRIKE_LOOK, FLAMESTRIKE_GROUND, AVATAR, FLAMES, FIRESTORM, FIRESTORM_LOOK, SLAM_CAST, SLAM,
 SLAM_LOOK, CAGE, CAGE_WHIRL) = range(211610, 211632)
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY, EFFECT_HEAL = 2, 6, 3, 10
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_SCALE, AURA_DAMAGE_DONE, AURA_SCHOOL_IMMUNITY = (
    4, 3, 12, 61, 79, 39)
SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_SHADOW = 1, 2, 4, 32
ATTR1_IS_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
DAGRAN, MOIRA, PRIESTESS, GUARD, AMBASSADOR = 9019, 8929, 10076, 300843, 300844
# The stock looks (client Spell.dbc 2026-11-17): Hand of Thaurissan 17492, Mind Blast 15587, Shadow Word: Pain 15654,
# Avatar of Flame 15636, Flames 15643.
SV_HAND, SV_MIND_BLAST, SV_SWP, SV_AVATAR, SV_FLAMES = 143, 3057, 71, 46, 2519
# The VISUALS report's WRONG picks for this fight: Holy Channeling and Penance draw no beam, Volcanic Geyser is blue,
# Eruption draws nothing.
WRONG = {11274, 10980, 9466, 5043}


class EmperorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.npcs = npcs
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in npcs.creature_template_edits}
        cls.creatures = {int(e["entry"]): e for e in npcs.creature_templates}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.fight = FIGHT.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.moira_script = MOIRA_SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.declaration = DECLARATION.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def _hundredths(self, spell_id: int, effect: str = "effect1", misc: str = "EffectMiscValueB_1"):
        spell = self.spells[spell_id]
        e = spell[effect]
        normal = e["base_points"] + e["die_sides"] if e["type"] == EFFECT_SCHOOL_DAMAGE else e["base_points"]
        return normal, spell["raw_overrides"][misc]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d23_slice(self):
        self.assertEqual(sorted(self.spells), list(range(211610, 211632)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsEmperor{ 211610, 211659 }", re.sub(r"\s+", " ", self.header))
        for stock in (17492, 15587, 15636, 15643, 15586, 8362, 15654, 15537):
            self.assertNotIn(stock, self.spells)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_EM_MOIRA_CAGE_WHIRL;")

    def test_hand_of_thaurissan_is_a_fire_hit_and_a_two_second_stun(self):
        spell = self.spells[HAND]
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["duration_ms"], 2000)            # the stock 5 s drops to 2 s (ruling 78)
        self.assertEqual(spell["range_yards"], 30.0)
        self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual((spell["effect2"]["type"], spell["effect2"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_STUN))
        self.assertEqual(self._hundredths(HAND), (1200, 1500))
        self.assertIn((HAND, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], SV_HAND)
        self.assertEqual(self._const("kHandPct").replace(" ", ""), "12.f,15.f")
        self.assertEqual(self._const("kHandStunMs"), "2000")
        self.assertEqual(self._const("kHandRangeYd"), "30.f")

    def test_nemesis_is_an_uninterruptible_holy_channel_with_the_gold_beam(self):
        spell = self.spells[NEMESIS]
        self.assertEqual(spell["school"], SCHOOL_HOLY)
        self.assertEqual(spell["duration_ms"], 8000)
        raw = spell["raw_overrides"]
        self.assertTrue(raw["AttributesEx"] & ATTR1_IS_CHANNELED)
        self.assertEqual((raw["InterruptFlags"], raw["ChannelInterruptFlags"]), (0, 0))
        self.assertEqual(raw["SpellVisualID_1"], visuals.EM_NEMESIS_BEAM)
        self.assertEqual(visuals.EM_NEMESIS_BEAM, 11500)
        self.assertEqual((spell["effect1"]["type"], spell["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(self._const("kNemesisChannelMs"), "8000")
        # rule 5: a kick on her Shadow Mind Blast must never lock this must-play channel
        self.assertNotEqual(spell["school"], self.spells[MIND_BLAST]["school"])
        burn = self.spells[RADIANT_BURN]
        self.assertEqual(burn["school"], SCHOOL_HOLY)
        self.assertEqual(self._hundredths(RADIANT_BURN), (500, 800))
        self.assertIn((RADIANT_BURN, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertEqual(self._const("kRadiantBurnPct").replace(" ", ""), "5.f,8.f")

    def test_the_heals_are_exact(self):
        for spell_id in (NEMESIS_HEAL, TETHER_HEAL):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], EFFECT_HEAL, spell_id)
            self.assertEqual(spell["effect1"]["base_points"], 0, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], 21, spell_id)    # an ally: him, or her own
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertFalse([s for s in self.scripts if s[0] == spell_id], spell_id)
        self.assertEqual(self._const("kNemesisHealPct"), "1.5f")
        self.assertEqual(self._const("kTetherHealPct"), "0.5f")

    def test_mind_blast_is_the_kickable_copy(self):
        spell = self.spells[MIND_BLAST]
        self.assertEqual(spell["school"], SCHOOL_SHADOW)
        self.assertEqual(spell["cast_time_ms"], 1500)
        self.assertEqual(spell["range_yards"], 30.0)
        raw = spell["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
        self.assertEqual(raw["SpellVisualID_1"], SV_MIND_BLAST)
        self.assertEqual(self._hundredths(MIND_BLAST), (1000, 1200))
        self.assertIn((MIND_BLAST, "spell_dungeon_refflat_damage"), self.scripts)
        # the bots read it as the descriptor's kick, on both princesses
        self.assertIn("d.interrupts.emplace_back(NPC_MOIRA, SPELL_EM_MIND_BLAST, 1,", self.script)
        self.assertIn("d.interrupts.emplace_back(NPC_PRIESTESS, SPELL_EM_MIND_BLAST, 1,", self.script)

    def test_necrosis_is_a_magic_dot_on_the_dispel_list(self):
        spell = self.spells[NECROSIS]
        self.assertEqual(spell["school"], SCHOOL_SHADOW)
        self.assertEqual(spell["dispel"], 1)                    # Magic
        self.assertEqual(spell["duration_ms"], 10000)
        e = spell["effect1"]
        self.assertEqual((e["type"], e["apply_aura"], e["amplitude"]), (EFFECT_APPLY_AURA, AURA_PERIODIC_DAMAGE, 1000))
        self.assertEqual((e["base_points"], spell["raw_overrides"]["EffectMiscValueB_1"]), (600, 600))
        self.assertIn((NECROSIS, "spell_dungeon_refflat_periodic"), self.scripts)
        self.assertEqual(self._const("kNecrosisTickPct"), "6.f")
        self.assertIn("d.dispels.emplace_back(SPELL_EM_NECROSIS, 2);", self.script)

    def test_the_tether(self):
        spell = self.spells[TETHER]
        self.assertEqual(spell["school"], SCHOOL_SHADOW)
        raw = spell["raw_overrides"]
        self.assertTrue(raw["AttributesEx"] & ATTR1_IS_CHANNELED)
        self.assertEqual((raw["InterruptFlags"], raw["ChannelInterruptFlags"]), (0, 0))
        self.assertEqual(raw["SpellVisualID_1"], visuals.EM_TWILIGHT_TETHER)
        self.assertEqual(self._hundredths(TETHER_BURN), (300, 300))
        self.assertEqual(self._const("kTetherBurnPct"), "3.f")

    def test_the_registry_hits_are_resolve_copies(self):
        for spell_id, school in ((FLAMESTRIKE, SCHOOL_FIRE), (FLAMESTRIKE_BURN, SCHOOL_FIRE), (FIRESTORM, SCHOOL_FIRE),
                                 (SLAM, SCHOOL_PHYSICAL)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)

    def test_the_enrage_has_no_immunity(self):
        spell = self.spells[AVATAR]
        auras = [spell[f"effect{i}"]["apply_aura"] for i in (1, 2) if spell.get(f"effect{i}")]
        self.assertEqual(auras, [AURA_DAMAGE_DONE, AURA_MOD_SCALE])
        self.assertNotIn(AURA_SCHOOL_IMMUNITY, auras)
        self.assertEqual((spell["effect1"]["base_points"], spell["effect2"]["base_points"]), (25, 60))
        self.assertEqual(spell["duration_ms"], -1)
        self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], SV_AVATAR)
        self.assertEqual(self._hundredths(FLAMES), (400, 500))
        self.assertEqual(self.spells[FLAMES]["raw_overrides"]["SpellVisualID_1"], SV_FLAMES)
        self.assertEqual(self._const("kEnrageDamagePct"), "25.f")

    def test_the_hammer_slam_bar_is_physical(self):
        spell = self.spells[SLAM_CAST]
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(spell["cast_time_ms"], 1500)
        self.assertEqual(spell["raw_overrides"]["InterruptFlags"], 0)
        self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visuals.EM_HAMMER_SLAM_WINDUP)
        self.assertEqual(self._const("kHammerSlamCastMs"), "1500")

    def test_the_looks_use_the_v2_visuals(self):
        for spell_id, visual in ((FLAMESTRIKE_LOOK, visuals.EM_FLAMESTRIKE_CAST),
                                 (FLAMESTRIKE_GROUND, visuals.EM_FLAMESTRIKE_BURN),
                                 (FIRESTORM_LOOK, visuals.EM_FIRESTORM), (SLAM_LOOK, visuals.EM_HAMMER_SLAM_CRACK),
                                 (CAGE, visuals.MO_FIRE_CAGE), (CAGE_WHIRL, visuals.MO_FIRE_CAGE_WHIRL),
                                 (RADIANT_BURN, visuals.EM_RADIANT_BURN)):
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)
        self.assertEqual(visuals.MO_FIRE_CAGE, visuals.SV_MOIRA_FIRE_CAGE)
        self.assertEqual(visuals.SV_MOIRA_FIRE_CAGE, 90652)
        self.assertEqual(visuals.EM_FLAMESTRIKE_BURN, visuals.SHIPPED_LAVA_POOL[6])
        for spell_id in (CAGE, CAGE_WHIRL, FLAMESTRIKE_GROUND):
            self.assertEqual(self.spells[spell_id]["duration_ms"], -1, spell_id)

    def test_no_wrong_listed_look_is_wired(self):
        for spell in self.spells.values():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1"), WRONG, spell["id"])

    # --- the adds -----------------------------------------------------------------------------------------------------

    def test_the_adds(self):
        guard = self.creatures[GUARD]
        self.assertEqual((guard["minlevel"], guard["rank"], guard["unit_class"]), (55, 1, 1))
        self.assertAlmostEqual(guard["HealthModifier"] * 2614, 8000, delta=3)
        self.assertEqual(guard["difficulty_entry_1"], 310417)
        self.assertEqual(guard["lootid"], 0)
        amb = self.creatures[AMBASSADOR]
        self.assertEqual((amb["minlevel"], amb["rank"], amb["unit_class"]), (55, 1, 2))
        self.assertAlmostEqual(amb["HealthModifier"] * 2091, 10000, delta=3)
        self.assertEqual(amb["difficulty_entry_1"], 310418)
        self.assertEqual(amb["name"], "Twilight's Hammer Ambassador")
        scripts = {GUARD: "npc_brd_imperial_guard", AMBASSADOR: "npc_brd_twilight_ambassador"}
        for add in (guard, amb):
            self.assertEqual(add["faction"], 54)
            self.assertEqual(add["flags_extra"] & 0x40, 0x40)
            self.assertEqual(add["ScriptName"], scripts[int(add["entry"])] if common.BIND_WAVE_2 else "")
        self.assertIn("ADD_SCRIPTS = {GUARD: 'npc_brd_imperial_guard', AMBASSADOR: 'npc_brd_twilight_ambassador'}",
                      self.declaration)
        self.assertRegex(self.header, r"NPC_BRD_IMPERIAL_GUARD\s*=\s*300843,")
        self.assertRegex(self.header, r"NPC_BRD_TWILIGHT_AMBASSADOR\s*=\s*300844,")
        self.assertEqual((visuals.DISPLAY_IMPERIAL_GUARD, visuals.DISPLAY_TWILIGHT_AMBASSADOR), (8750, 8778))

    def test_the_script_names_are_the_ones_the_cpp_registers(self):
        for name in ("boss_emperor_dagran_thaurissan_rework", "npc_brd_imperial_guard", "npc_brd_twilight_ambassador"):
            self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({name},")
        self.assertRegex(self.moira_script, r"RegisterDungeonReworkCreatureAI\(boss_moira_bronzebeard_rework,")
        self.assertRegex(self.script, r'BrdTest::RegisterBoss\("emperor",')
        self.assertRegex(self.moira_script, r'BrdTest::RegisterBoss\("moira",')

    # --- the bindings -------------------------------------------------------------------------------------------------

    def test_the_boss_columns(self):
        # INSTANCE_BIND only on the credit carrier (handoff section 10): Dagran binds, Moira and the Priestess do not
        for name, entry, script, hm, dm, base, health, bind in (
                ("DAGRAN", 9019, "boss_emperor_dagran_thaurissan_rework", 59.281, 3.5, 2699, 160000, True),
                ("MOIRA", 8929, "boss_moira_bronzebeard_rework", 27.322, 3.5, 1830, 50000, False),
                ("PRIESTESS", 10076, "boss_moira_bronzebeard_rework", 27.322, 7.5, 1830, 50000, False)):
            self.assertRegex(self.declaration, rf"{name}_COLUMNS = boss_columns\('{script}', {hm}, damage_modifier={dm}"
                                               + ("\\)" if bind else r",\s+instance_bind=False\)"))
            self.assertIn(f"creature_template_columns({entry}, **{name}_COLUMNS)", self.declaration)
            columns = common.boss_columns(script, hm, damage_modifier=dm, instance_bind=bind)
            self.assertEqual(columns["ScriptName"], script)
            self.assertEqual(columns["AIName"], "")
            self.assertEqual(columns["CreatureImmunitiesId"], 1972)
            self.assertEqual(columns["flags_extra"], 1 if bind else 0)
            self.assertEqual(entry in common.NO_INSTANCE_BIND, not bind)
            self.assertEqual((columns["HealthModifier"], columns["DamageModifier"]), (hm, dm))
            self.assertAlmostEqual(columns["HealthModifier"] * base, health, delta=10)

    @unittest.skipUnless(common.BIND_WAVE_2, "the bindings register only while BIND_WAVE_2 is on")
    def test_the_bindings_register_with_the_gate_on(self):
        self.assertEqual(self.edits[DAGRAN]["ScriptName"], "boss_emperor_dagran_thaurissan_rework")
        self.assertEqual(self.edits[MOIRA]["ScriptName"], "boss_moira_bronzebeard_rework")
        self.assertEqual(self.edits[PRIESTESS]["ScriptName"], "boss_moira_bronzebeard_rework")

    @unittest.skipIf(common.BIND_WAVE_2, "with the gate on the bindings are registered (the test above)")
    def test_nothing_is_bound_with_the_gate_off(self):
        for entry in (DAGRAN, MOIRA, PRIESTESS):
            self.assertNotIn(entry, self.edits)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def _texts(self, entry: int):
        rows = re.findall(rf"^\({entry}, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0,\s*0, (\d+),", self.sql,
                          re.M)
        return [(int(g), int(t), int(r), text.replace("''", "'")) for g, _, text, t, r in rows]

    def test_dagrans_texts(self):
        rows = self._texts(DAGRAN)
        self.assertEqual([(g, t, r) for g, t, r, _ in rows],
                         [(8, 14, 3), (9, 14, 3), (10, 14, 3), (11, 41, 3), (12, 41, 3), (13, 41, 3)])
        texts = [text for *_, text in rows]
        self.assertEqual(texts[0], "Guards! Defend your Emperor!")
        self.assertEqual(texts[1], "You will pay for her with fire!")
        self.assertEqual(texts[2], "Ragnaros! Your servant calls! Lend me your fury!")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9019 AND `GroupID` BETWEEN 8 AND 13;", self.sql)
        for name, group in (("YELL_EM_GUARDS", 8), ("YELL_EM_ENRAGE", 9), ("YELL_EM_RAGNAROS_AWAKENS", 10),
                            ("EMOTE_EM_MAGMA_CLAP", 11), ("EMOTE_EM_VOLCANIC_BLAST", 12), ("EMOTE_EM_HAMMER_SLAM", 13)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        for name in ("YELL_EM_GUARDS", "YELL_EM_ENRAGE", "YELL_EM_RAGNAROS_AWAKENS", "EMOTE_EM_HAMMER_SLAM"):
            self.assertIn(f"Talk({name})", self.script)

    def test_the_nemesis_emote_on_both_princesses(self):
        for entry in (MOIRA, PRIESTESS):
            self.assertEqual(self._texts(entry),
                             [(1, 41, 3, "%s channels a beam of holy fire into the Emperor!")], entry)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` IN (8929, 10076) AND `GroupID` = 1;", self.sql)
        self.assertIn("Talk(EMOTE_MOIRA_NEMESIS)", self.moira_script)

    def test_the_rev_adds_no_spawn_and_no_smartai(self):
        self.assertNotIn("INSERT INTO `creature` ", self.sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", self.sql)
        self.assertNotIn("DELETE FROM `smart_scripts`", self.sql)

    # --- the hooks and the drill --------------------------------------------------------------------------------------

    def test_the_hooks_for_d24(self):
        for name in ("class EmperorFight", "class EmperorHardMode", "void RegisterEmperorHardMode(",
                     "bool HasEmperorHardMode()", "CreateEmperorHardMode(Creature* boss)", "virtual void OnAwaken(",
                     "virtual void OnRise(", "virtual void OnEnd(", "virtual bool AvatarBeat(",
                     "virtual void CageMoira("):
            self.assertIn(name, self.fight, name)
        self.assertIn("SetData(DATA_AVATAR, 1)", self.script)

    def test_a_refused_awakening_latches_for_the_pull(self):
        # R-2-C m1: the refusal sets the latch, DamageTaken reads it, the pull and the cleanup clear it.
        self.assertIn("_phase, _awakenRefused))", self.script)
        self.assertRegex(self.script, r'_awakenRefused = true;\s*LogEm\("awaken-refused"')
        self.assertEqual(len(re.findall(r"^\s+_awakenRefused = false;$", self.script, re.M)), 2)

    def test_moira_first_zones_the_room(self):
        # R-2-C m3: her own pull puts the room on her threat list (her evade takes Dagran home).
        engage = self.moira_script[self.moira_script.index("void JustEngagedWith("):
                                   self.moira_script.index("void EnterEvadeMode(")]
        self.assertIn("DoZoneInCombat(me, kPullZoneYd);", engage)

    def test_the_test_clear_evades_an_engaged_emperor(self):
        # R-2-C n2: `.dbtest brd emperor clear` mid-pull evades him instead of leaving him idle in combat.
        start = self.script.index("case TestKind::Clear:")
        clear = self.script[start:self.script.index("return {};", start)]
        self.assertIn("EnterEvadeMode(EVADE_REASON_OTHER);", clear)

    def test_the_beam_is_g2s_drill_row(self):
        self.assertRegex(self.logic, r"TAG_EM_NEMESIS\s*=\s*21,")
        self.assertEqual(self._const("kBeamWidthYd"), "2.f")
        self.assertEqual(self._const("kNemesisSoakWarnMs"), "3000")
        if not BM_DRILL.exists():
            self.skipTest("the BM drill source is not in this layout")
        drill = re.sub(r'"\s*\n\s*"', "", BM_DRILL.read_text(encoding="utf-8"))
        self.assertRegex(drill, r"kBrd2GroupTags\[\]\s*=\s*\{ 21 \}")
        self.assertRegex(drill, r'"soak 2 3000 shape=line to=target[^"]*need=1 persist=5000 tick=1000')


if __name__ == "__main__":
    unittest.main()
