"""
Scarlet Monastery build WP-D8, Arcanist Doan: source/npcs/scarlet_monastery/doan.py (his template columns, the Arcane
Anchor and the spells 212670-212686), data/sql/updates/pending_db_world/rev_doan_scarlet_monastery.sql (his new texts,
the Chamber Seal's object template), and the C++ they must agree with (modules/mod-dungeon-bosses
src/ScarletMonastery/DoanLogic.h and boss_arcanist_doan_rework.cpp).

Checks:
  - the eighteen spells sit in the D8 slice and the C++ names the same ids; the hits the registry lands are resolve
    copies in their schools; Flamestrike is the only interruptible cast, Fire, bound to the kit's percent script; the
    bars are Arcane and not interruptible (rule 5); the bubble is a school immunity, Overloaded +50% damage taken for
    10 s, the beam a channel that ignores the bubble; the looks use the V constants (never SV 6742);
  - the anchor: its script, level 34 warrior, 1.2k (HANDOFF s10 option D), no melee, immunity 1972, no loot or XP, display 24813; Doan's
    columns (script, 46k, INSTANCE_BIND);
  - the SQL: groups 4-5 of 6487 (boss emotes, map-wide), never the stock 0-1 or D8H's 2-3; the seal's DOOR template on
    GODI 523 at the C++ size, locked and not selectable, no spawn;
  - the numbers the dbc-tools file pins are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_doan.py
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
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "DoanLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_arcanist_doan_rework.cpp"
FIGHT = MDB / "src" / "ScarletMonastery" / "DoanFight.h"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_doan_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "doan.py"

SLICE = range(212670, 212710)
FIRST = 212670
NAMES = ("SPELL_DN_ARCANE_BUBBLE", "SPELL_DN_DETONATION_CAST", "SPELL_DN_DETONATION", "SPELL_DN_ANCHOR_BEAM",
         "SPELL_DN_OVERLOADED", "SPELL_DN_SCORCHED", "SPELL_DN_SCORCHED_LOOK", "SPELL_DN_EXPLOSION_CAST",
         "SPELL_DN_ARCANE_EXPLOSION", "SPELL_DN_EXPLOSION_LOOK", "SPELL_DN_MARK", "SPELL_DN_MARK_BURST",
         "SPELL_DN_MARK_SELF", "SPELL_DN_MARK_BURST_LOOK", "SPELL_DN_POOL", "SPELL_DN_POOL_LOOK",
         "SPELL_DN_FLAMESTRIKE", "SPELL_DN_DETONATION_CAST_HEROIC")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_SCHOOL_IMMUNITY, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 39, 87
SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_ARCANE = 1, 4, 64
DOAN, ANCHOR, SEAL = 6487, 300919, 301319
DOOR = 0
GO_COLUMN_COUNT = 35        # entry, type, displayId, name, IconName, castBarCaption, unk1, size, Data0-23, 3 trailing


def _split_values(text: str) -> list:
    """A VALUES tuple's fields: quoted strings (with '' escapes), ints and floats."""
    out: list = []
    for match in re.finditer(r"'((?:[^']|'')*)'|(-?\d+\.\d+)|(-?\d+)", text):
        quoted, real, whole = match.groups()
        out.append(quoted.replace("''", "'") if quoted is not None else float(real) if real is not None
                   else int(whole))
    return out


class DoanTest(unittest.TestCase):
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
        cls.fight = FIGHT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d8_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsDoan{ 212670, 212709 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_DN_DETONATION_CAST_HEROIC <= kSpellSlice\.last")

    def test_the_registry_hits_are_resolve_copies_in_their_schools(self):
        for offset, school in ((2, SCHOOL_FIRE), (5, SCHOOL_FIRE), (8, SCHOOL_ARCANE), (11, SCHOOL_FIRE),
                               (12, SCHOOL_FIRE), (14, SCHOOL_FIRE)):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)

    def test_flamestrike_is_the_only_interruptible_cast_and_the_bars_are_arcane(self):
        flame = self.spells[FIRST + 16]
        self.assertEqual(flame["school"], SCHOOL_FIRE)
        self.assertEqual(flame["cast_time_ms"], 2500)
        self.assertEqual(int(self._const("kFlamestrikeCastMs")), 2500)
        raw = flame["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))     # a kick and a silence
        effect = flame["effect1"]
        self.assertEqual((effect["implicit_target_a"], effect["implicit_target_b"]), (22, 15))
        self.assertEqual(effect["base_points"] + effect["die_sides"], 4000)
        self.assertEqual(raw["EffectMiscValueB_1"], 4000)
        self.assertEqual(self._const("kFlamestrikePct"), "40.f")
        self.assertIn((FIRST + 16, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(raw["AttributesEx3"] & 0x20000000)                           # rule 2
        for offset, cast_ms, header_name in ((1, 10000, "kDetonationCastMs"), (7, 2000, "kExplosionCastMs"),
                                             (17, 14000, "kDetonationCastMsHeroic")):
            bar = self.spells[FIRST + offset]
            self.assertEqual(bar["cast_time_ms"], cast_ms, offset)
            self.assertEqual(int(self._const(header_name)), cast_ms, header_name)
            self.assertEqual((bar["raw_overrides"]["InterruptFlags"], bar["raw_overrides"]["PreventionType"]), (0, 0))
            self.assertEqual(bar["effect1"]["type"], EFFECT_DUMMY, offset)
            # rule 5: a must-play bar never shares the interruptible cast's school
            self.assertEqual(bar["school"], SCHOOL_ARCANE, offset)
            self.assertNotEqual(bar["school"], flame["school"], offset)
        # every other spell of the slice has no cast time (triggered hits and looks)
        for spell_id, spell in self.spells.items():
            if spell_id not in (FIRST + 1, FIRST + 7, FIRST + 16, FIRST + 17):
                self.assertEqual(spell["cast_time_ms"], 0, spell_id)

    def test_the_bubble_overloaded_and_the_beam(self):
        bubble = self.spells[FIRST]
        self.assertEqual((bubble["effect1"]["type"], bubble["effect1"]["apply_aura"]),
                         (EFFECT_APPLY_AURA, AURA_SCHOOL_IMMUNITY))
        self.assertEqual(bubble["effect1"]["misc_value"], 127)                      # every school
        self.assertEqual((bubble["dispel"], bubble["mechanic"]), (0, 0))           # no Mass Dispel, no Spellsteal
        self.assertEqual(bubble["duration_ms"], -1)
        self.assertEqual(bubble["raw_overrides"]["SpellVisualID_1"], visuals.DN_BUBBLE)
        over = self.spells[FIRST + 4]
        effect = over["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_TAKEN))
        self.assertEqual(effect["base_points"] + effect["die_sides"], 50)
        self.assertEqual(effect["misc_value"], 127)
        self.assertEqual(over["duration_ms"], 10000)
        self.assertEqual(over["dispel"], 0)
        self.assertEqual(int(self._const("kOverloadedMs")), 10000)
        self.assertEqual(self._const("kOverloadedDamageTakenPct"), "50.f")
        beam = self.spells[FIRST + 3]
        self.assertTrue(beam["raw_overrides"]["AttributesEx"] & 0x4)                # channeled
        self.assertTrue(beam["attributes"] & 0x20000000)                            # ignores the bubble's immunity
        self.assertEqual(beam["raw_overrides"]["SpellVisualID_1"], visuals.DN_ANCHOR_BEAM)
        self.assertNotEqual(visuals.DN_ANCHOR_BEAM, 6742)                           # VR: SV 6742 has no beam

    def test_the_mark_is_a_5_s_debuff_nobody_dispels(self):
        mark = self.spells[FIRST + 10]
        self.assertEqual(mark["duration_ms"], 5000)
        self.assertEqual(int(self._const("kMarkMs")), 5000)
        self.assertEqual(mark["dispel"], 0)
        self.assertTrue(mark["attributes"] & 0x04000000)                            # a debuff
        self.assertEqual((mark["effect1"]["type"], mark["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(mark["raw_overrides"]["SpellVisualID_1"], visuals.DN_MARK)

    def test_the_looks_use_the_v_constants(self):
        for offset, visual in ((1, visuals.DN_DETONATION), (6, visuals.DN_SCORCHED), (9, visuals.DN_EXPLOSION),
                               (13, visuals.DN_MARK_BURST), (15, visuals.DN_POOL), (16, visuals.DN_FLAMESTRIKE),
                               (4, visuals.DN_OVERLOADED), (17, visuals.DN_DETONATION)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        # the lasting looks on stalkers have no duration
        for offset in (6, 15):
            self.assertEqual(self.spells[FIRST + offset]["duration_ms"], -1, offset)
        # the VR picks: the stock numbers, the shipped lava rungs at 5 and 4 yd
        self.assertEqual((visuals.DN_BUBBLE, visuals.DN_ANCHOR_BEAM, visuals.DN_DETONATION, visuals.DN_EXPLOSION,
                          visuals.DN_MARK, visuals.DN_MARK_BURST, visuals.DN_FLAMESTRIKE),
                         (968, 8795, 1585, 965, 10692, 10693, 10383))
        self.assertEqual((visuals.DN_SCORCHED, visuals.DN_POOL),
                         (visuals.SHIPPED_LAVA_POOL[5], visuals.SHIPPED_LAVA_POOL[4]))

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_anchor(self):
        c = self.creatures[ANCHOR]
        self.assertEqual(c["name"], "Arcane Anchor")
        self.assertEqual(c["ScriptName"], "npc_sm_arcane_anchor")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"]), (34, 34, 1, 67))
        # 1.2k on the level 34 warrior class base 1,163 (HANDOFF s10 option D; the spec's 1.7k)
        self.assertAlmostEqual(c["HealthModifier"] * 1163, 1200, delta=3)
        self.assertEqual(c["DamageModifier"], 0.0)          # never attacks
        self.assertEqual(c["CreatureImmunitiesId"], 1972)   # never feared off its spot, never banished
        self.assertEqual(c["unit_flags"], 0)                # attackable and selectable: a kill target
        self.assertEqual(c["lootid"], 0)
        self.assertEqual(c["flags_extra"], 0x40)            # no XP
        self.assertEqual(self.models[ANCHOR]["CreatureDisplayID"], visuals.DISPLAY_DOAN_ANCHOR)
        self.assertEqual(visuals.DISPLAY_DOAN_ANCHOR, 24813)
        self.assertEqual(int(self._const("kAnchorHealthNormal")), 1200)
        self.assertEqual(int(self._const("kAnchorHealthHeroic")), 5000)
        self.assertIn("creature_template(300919, ", self.dt)        # H finds the kit adds by this literal pattern
        self.assertRegex(self.script,
                         r"RegisterDungeonReworkCreatureAI\(npc_sm_arcane_anchor, ScarletMonasteryRework::"
                         r"kInstanceScriptName\)")

    def test_doans_columns(self):
        self.assertRegex(self.dt, r"creature_template_columns\(6487, \*\*boss_columns\(\s*'boss_arcanist_doan_rework', "
                                  r"50\.998, damage_modifier=2\.4,")
        self.assertAlmostEqual(50.998 * 902, 46000, delta=5)
        self.assertEqual(int(self._const("kDoanHealthNormal")), 46000)
        self.assertEqual(int(self._const("kDoanHealthHeroic")), 230000)
        self.assertRegex(self.script,
                         r"RegisterDungeonReworkCreatureAI\(boss_arcanist_doan_rework, ScarletMonasteryRework::"
                         r"kInstanceScriptName\)")
        self.assertRegex(self.script, r'SmTest::RegisterBoss\("doan",')

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [ANCHOR], "gameobject": [SEAL]}), [])
        self.assertRegex(self.header, r"NPC_SM_ARCANE_ANCHOR\s*=\s*300919,")
        self.assertRegex(self.header, r"GO_SM_CHAMBER_SEAL\s*=\s*301319,")
        self.assertRegex(self.header, r"NPC_DOAN\s*=\s*6487,")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_two_texts(self):
        rows = re.findall(r"^\(6487, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows], [(4, 0, 41, 3), (5, 0, 41, 3)])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 6487 AND `GroupID` BETWEEN 4 AND 5;",
                      self.sql)
        for name, group in (("SAY_AGGRO", 0), ("SAY_BUBBLE", 1), ("SAY_HERESY", 2), ("SAY_RISE_PURGED", 3),
                            ("EMOTE_SEAL", 4), ("EMOTE_OVERLOADED", 5)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        # the seal's close says the emote; the stock groups 0-1 and D8H's 2-3 are never touched here
        self.assertIn("spec.emoteGroup = EMOTE_SEAL;", self.script)
        self.assertNotRegex(self.sql, r"GroupID` (?:BETWEEN [0-3]|= [0-3])")

    def test_the_seal_is_a_locked_door_on_godi_523_at_the_cpp_size(self):
        block = re.search(r"INSERT INTO `gameobject_template`.*?VALUES\n(.*?)\nON DUPLICATE KEY", self.sql, re.S)
        self.assertIsNotNone(block)
        fields = _split_values(block.group(1).strip()[1:-1])
        self.assertEqual(len(fields), GO_COLUMN_COUNT)
        self.assertEqual(fields[0], SEAL)
        self.assertEqual(fields[1], DOOR)
        self.assertEqual(fields[2], visuals.GODI_CHAMBER_BARRIER)
        self.assertEqual(fields[2], int(self._const("kSealDisplay")))
        self.assertAlmostEqual(float(fields[7]), float(self._const("kSealSize").rstrip("f")), places=3)
        self.assertEqual(fields[8:10], [0, 0])              # Data0 starts closed, Data1 no lock id
        addon = re.search(r"^\(301319, (\d+), (\d+), 0, 0, 0, 0, 0, 0\);", self.sql, re.M)
        self.assertIsNotNone(addon)
        self.assertEqual(int(addon.group(2)), 0x2 | 0x10 | 0x20)
        self.assertIn("DELETE FROM `gameobject_template_addon` WHERE `entry` = 301319;", self.sql)
        # no spawn: the kit's SealedArena summons it at the close and despawns it on the release
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)
        self.assertNotIn("INSERT INTO `creature` ", self.sql)
        self.assertIn("spec.sealEntry = GO_SM_CHAMBER_SEAL;", self.script)

    # --- the numbers the dbc-tools file pins --------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("DETONATION_CAST_MS", "kDetonationCastMs"),
                               ("DETONATION_CAST_MS_HEROIC", "kDetonationCastMsHeroic"),
                               ("EXPLOSION_CAST_MS", "kExplosionCastMs"),
                               ("MARK_MS", "kMarkMs"), ("OVERLOADED_MS", "kOverloadedMs"),
                               ("FLAMESTRIKE_CAST_MS", "kFlamestrikeCastMs")):
            dt_value = int(re.search(rf"^{name} = (\d+)", self.dt, re.M).group(1))
            self.assertEqual(dt_value, int(self._const(expected)), name)
        for name, expected in (("kBubbleBeat", "{20000,35000},{20000,30000}"),
                               ("kExplosionBeat", "{8000,12000},{8000,12000}"),
                               ("kMarkBeat", "{15000,20000},{15000,20000}")):
            found = re.search(rf"NH<Beat> {name}\{{(.*?)\}};", self.logic)
            self.assertIsNotNone(found, name)
            self.assertEqual(found.group(1).replace(" ", ""), expected, name)
        for name, expected in (("kDetonationPct", "75.f,130.f"), ("kExplosionPct", "30.f,45.f"),
                               ("kMarkOthersPct", "35.f,45.f"), ("kMarkSelfPct", "15.f,20.f"),
                               ("kScorchedPct", "6.f,10.f"), ("kAnchorsBase", "3,4"), ("kAnchorCap", "5,0"),
                               ("kPatchCap", "4,0"), ("kMarkCount", "2,3")):
            self.assertEqual(self._const(name).replace(" ", ""), expected, name)
        self.assertEqual(self._const("kPoolPct"), "10.f")

    def test_heroic_uses_the_14_s_bar(self):
        # HANDOFF s10 option D: the script's clock and the bar spell come from the same difficulty switch
        self.assertIn("return DetonationCastMsFor(_heroic);", self.script)
        self.assertIn("return DetonationBarSpellFor(_heroic);", self.script)
        self.assertRegex(self.logic, r"heroic \? kDetonationCastMsHeroic : kDetonationCastMs;")
        self.assertRegex(self.logic, r"heroic \? SPELL_DN_DETONATION_CAST_HEROIC : SPELL_DN_DETONATION_CAST;")
        self.assertEqual(self.spells[FIRST + 17]["name"], self.spells[FIRST + 1]["name"])

    def test_the_hard_mode_hooks_exist(self):
        # D8H attaches through DoanFight.h only (section 3.7): the factory, the bubble hooks, the tuning overrides
        for hook in ("RegisterDoanHardMode", "OnBubbleStart", "OnBubbleEnd", "OnAnchorRaised", "AddBubbleAnchor",
                     "AddNextBubbleAnchors", "RiderFor", "BubbleEveryMs", "MarkEveryMs", "PoolLifeMs",
                     "DetonationPct", "DescribeExtra"):
            self.assertIn(hook, self.fight, hook)
        self.assertIn("CreateDoanHardMode(me)", self.script)
        self.assertIn("DATA_HARD_MODE_DOAN", self.script)


if __name__ == "__main__":
    unittest.main()
