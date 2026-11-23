"""
Scarlet Monastery build WP-D6, Ambrose Kell: source/npcs/scarlet_monastery/kell.py (his template, the relic trigger,
the Gallery Skeleton and the spells 212570-212587), data/sql/updates/pending_db_world/rev_kell_scarlet_monastery.sql
(his texts, the case objects' templates, his spawn), and the C++ they must agree with (modules/mod-dungeon-bosses
src/ScarletMonastery/KellLogic.h and boss_ambrose_kell_rework.cpp).

Checks:
  - the eighteen spells sit in the D6 slice and the C++ names the same ids; the percent spells carry their numbers in
    hundredths (normal in the effect, heroic in EffectMiscValueB) and bind the kit's percent script; the hits the
    registry lands are resolve copies in the right schools; the Torrent is an interruptible 3 s cast and the Unseal
    bar is not; Bone Curse is a Magic debuff of 8 s bound to the script; the looks use the V constants;
  - the three creatures: Kell's script, level 34 mage, 44k, immunity 1972, INSTANCE_BIND, display 2524; the invisible
    unselectable trigger; the level 33 warrior skeleton of 1.2k on display 9786;
  - the SQL: seven texts (groups 0-6 of 300910, the emotes boss emotes), the four GENERIC not-selectable objects whose
    displays are the C++ constants and the V constants, his spawn inside the arena on both difficulties;
  - the numbers the dbc-tools file pins are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_kell.py
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
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "KellLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_ambrose_kell_rework.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_kell_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "kell.py"

SLICE = range(212570, 212610)
FIRST = 212570
NAMES = ("SPELL_AN_UNSEAL_CAST", "SPELL_AN_UNSEAL_SHATTER", "SPELL_AN_PLAGUE_CLOUD", "SPELL_AN_PLAGUE_CLOUD_LOOK",
         "SPELL_AN_ARCANE_LINE", "SPELL_AN_ARCANE_LINE_LOOK", "SPELL_AN_RAISE_SKELETON_LOOK", "SPELL_AN_GILDED_CANE",
         "SPELL_AN_PLAGUE_FLASK", "SPELL_AN_PLAGUE_FLASK_POOL", "SPELL_AN_PLAGUE_FLASK_THROW",
         "SPELL_AN_PLAGUE_FLASK_POOL_LOOK", "SPELL_AN_ARCANE_TORRENT", "SPELL_AN_BONE_CURSE", "SPELL_AN_BONE_BURST",
         "SPELL_AN_TROPHY_CASK", "SPELL_AN_TROPHY_STAFF", "SPELL_AN_TROPHY_SKULL")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY = 4
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_SHADOW, SCHOOL_ARCANE = 1, 8, 32, 64
TARGET_DEST_DEST = 87
TARGET_FLAG_DEST_LOCATION = 0x40
KELL, TRIGGER, SKELETON = 300910, 300911, 300912
GENERIC = 5
GO_FLAG_NOT_SELECTABLE = 16
GO_COLUMN_COUNT = 35        # entry, type, displayId, name, IconName, castBarCaption, unk1, size, Data0-23, 3 trailing


class KellTest(unittest.TestCase):
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

    def test_the_spells_sit_in_the_d6_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsKell{ 212570, 212609 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_AN_TROPHY_SKULL <= kSpellSlice\.last")

    def test_the_registry_hits_are_resolve_copies_in_their_schools(self):
        for offset, school in ((2, SCHOOL_NATURE), (4, SCHOOL_ARCANE), (8, SCHOOL_NATURE), (9, SCHOOL_NATURE)):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)

    def test_the_percent_spells_bind_the_kit_script(self):
        # Cane 20 / 30, Torrent 40 / 40, Bone Burst 25 / 25: hundredths, normal in the effect, heroic in MiscValueB
        for offset, normal, heroic, header_name in ((7, 2000, 3000, "kCanePct"), (12, 4000, 4000, "kTorrentPct"),
                                                    (14, 2500, 2500, "kBurstPct")):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual(effect["base_points"] + effect["die_sides"], normal, spell_id)
            self.assertEqual(spell["raw_overrides"]["EffectMiscValueB_1"], heroic, spell_id)
            self.assertIn((spell_id, "spell_dungeon_refflat_damage"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)    # rule 2
            header_value = self._const(header_name).replace(" ", "")
            self.assertIn(header_value, (f"{normal // 100}.f,{heroic // 100}.f", f"{normal // 100}.f"), header_name)
        # the Torrent and the burst are one value on both difficulties, so the header holds one number
        self.assertEqual(self._const("kTorrentPct"), "40.f")
        self.assertEqual(self._const("kBurstPct"), "25.f")
        self.assertEqual(self._const("kCanePct").replace(" ", ""), "20.f,30.f")
        self.assertEqual(self._const("kCloudPct").replace(" ", ""), "6.f,10.f")
        self.assertEqual(self._const("kLinePct").replace(" ", ""), "35.f,45.f")
        self.assertEqual(self._const("kFlaskPct"), "40.f")
        self.assertEqual(self._const("kPoolPct"), "8.f")

    def test_the_torrent_is_an_interruptible_cast_and_the_unseal_bar_is_not(self):
        torrent = self.spells[FIRST + 12]
        self.assertEqual(torrent["school"], SCHOOL_ARCANE)
        self.assertEqual(torrent["cast_time_ms"], 3000)
        self.assertEqual(int(self._const("kTorrentCastMs")), 3000)
        raw = torrent["raw_overrides"]
        self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))     # a kick and a silence
        self.assertEqual(torrent["effect1"]["implicit_target_a"], 22)                 # SRC_CASTER
        self.assertEqual(torrent["effect1"]["implicit_target_b"], 15)                 # SRC_AREA_ENEMY
        unseal = self.spells[FIRST]
        self.assertEqual(unseal["cast_time_ms"], 2000)
        self.assertEqual(int(self._const("kUnsealCastMs")), 2000)
        self.assertEqual((unseal["raw_overrides"]["InterruptFlags"], unseal["raw_overrides"]["PreventionType"]),
                         (0, 0))
        # rule 5: the must-play bar's school is not the interruptible cast's
        self.assertNotEqual(unseal["school"], torrent["school"])
        self.assertEqual(unseal["school"], SCHOOL_PHYSICAL)
        self.assertEqual(unseal["effect1"]["type"], EFFECT_DUMMY)

    def test_bone_curse_is_a_magic_debuff_of_8_s_bound_to_the_script(self):
        curse = self.spells[FIRST + 13]
        self.assertEqual(curse["dispel"], 1)                                          # Magic
        self.assertEqual(curse["duration_ms"], 8000)
        self.assertEqual(int(self._const("kCurseMs")), 8000)
        self.assertEqual((curse["effect1"]["type"], curse["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertTrue(curse["attributes"] & 0x04000000)                             # a debuff
        self.assertEqual(curse["raw_overrides"]["SpellVisualID_1"], visuals.AN_BONE_CURSE)
        self.assertIn((FIRST + 13, "spell_sm_kell_bone_curse"), self.scripts)
        self.assertRegex(self.script, r"class spell_sm_kell_bone_curse : public AuraScript")
        self.assertRegex(self.script, r"RegisterSpellScript\(spell_sm_kell_bone_curse\)")
        self.assertEqual(self.spells[FIRST + 14]["raw_overrides"]["SpellVisualID_1"], visuals.AN_BONE_CURSE_BURST)

    def test_the_looks_use_the_v_constants(self):
        for offset, visual in ((1, visuals.AN_SHATTER), (3, visuals.AN_PLAGUE_CLOUD), (6, visuals.AN_SKELETON),
                               (11, visuals.AN_PLAGUE_FLASK_POOL), (12, visuals.AN_ARCANE_TORRENT),
                               (15, visuals.AN_TROPHY_CASK), (16, visuals.AN_TROPHY_STAFF),
                               (17, visuals.AN_TROPHY_SKULL)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        for offset, visual in ((5, visuals.AN_STAFF_LINE), (10, visuals.AN_PLAGUE_FLASK)):
            spell = self.spells[FIRST + offset]
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, offset)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, offset)
            self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visual, offset)
            self.assertEqual(spell["raw_overrides"]["Targets"], TARGET_FLAG_DEST_LOCATION, offset)
        # the lasting looks are auras with no duration on the helper
        for offset in (3, 11, 15, 16, 17):
            self.assertEqual(self.spells[FIRST + offset]["duration_ms"], -1, offset)
        # the VR picks: the stock numbers and the tuple of the three trophies are distinct
        self.assertEqual((visuals.AN_SHATTER, visuals.AN_STAFF_LINE, visuals.AN_SKELETON, visuals.AN_ARCANE_TORRENT),
                         (7984, 9947, 2596, 7346))
        self.assertEqual(len({visuals.AN_TROPHY_CASK, visuals.AN_TROPHY_STAFF, visuals.AN_TROPHY_SKULL}), 3)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.creatures[KELL]
        self.assertEqual(c["name"], "Ambrose Kell")
        self.assertEqual(c["subname"], "Master of Antiquities")
        self.assertEqual(c["ScriptName"], "boss_ambrose_kell_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"]), (34, 34, 8, 67))
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["flags_extra"], 1)               # INSTANCE_BIND: FD-SM's credit_creature(300910)
        self.assertEqual(c["lootid"], KELL)
        # 44k on the level 34 mage class base 867 (S0's table: 50.749)
        self.assertAlmostEqual(c["HealthModifier"] * 867, 44000, delta=10)
        self.assertEqual(self.models[KELL]["CreatureDisplayID"], 2524)
        self.assertEqual(visuals.DISPLAY_KELL, 2524)

    def test_the_trigger_is_an_invisible_unselectable_helper(self):
        c = self.creatures[TRIGGER]
        self.assertEqual(c["ScriptName"], "")
        self.assertEqual(c["unit_flags"], 0x2 | 0x02000000)
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertEqual(c["flags_extra"], 0x40)
        self.assertEqual(self.models[TRIGGER]["CreatureDisplayID"], 11686)
        self.assertNotIn("difficulty_entry_1", {k for k, v in c.items() if v})

    def test_the_skeleton(self):
        c = self.creatures[SKELETON]
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"], c["type"]),
                         (33, 33, 1, 21, 6))
        # 1.2k on the level 33 warrior class base 1,110
        self.assertAlmostEqual(c["HealthModifier"] * 1110, 1200, delta=3)
        self.assertEqual(c["lootid"], 0)
        self.assertEqual(c["flags_extra"], 0x40)            # no XP
        self.assertEqual(self.models[SKELETON]["CreatureDisplayID"], 9786)
        self.assertEqual(visuals.DISPLAY_KELL_SKELETON, 9786)
        self.assertEqual(int(self._const("kSkeletonHealthNormal")), 1200)
        self.assertEqual(int(self._const("kSkeletonHealthHeroic")), 6000)
        self.assertEqual(int(self._const("kKellHealthNormal")), 44000)
        self.assertEqual(int(self._const("kKellHealthHeroic")), 240000)

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [KELL, TRIGGER, SKELETON],
                                                       "gameobject": [301315, 301316, 301317, 301318]}), [])
        for name, value in (("NPC_SM_KELL", KELL), ("NPC_SM_RELIC_TRIGGER", TRIGGER),
                            ("NPC_SM_GALLERY_SKELETON", SKELETON), ("GO_SM_RELIC_PEDESTAL", 301315),
                            ("GO_SM_RELIC_CASK", 301316), ("GO_SM_RELIC_STAFF", 301317),
                            ("GO_SM_RELIC_SKULL", 301318)):
            self.assertRegex(self.header, rf"{name}\s*=\s*{value},")

    def test_the_binding_switch_is_flipped_with_the_declaration(self):
        self.assertRegex(self.logic, r"constexpr bool kBound = true;")
        self.assertRegex(self.script,
                         r"if \(SmKell::kBound\)\s*RegisterDungeonReworkCreatureAI\(boss_ambrose_kell_rework,")
        self.assertRegex(self.script, r'SmTest::RegisterBoss\("kell",')
        self.assertIn("creature_template(300910, ", self.dt)       # H finds the kit adds by this literal pattern
        self.assertIn("creature_template(300912, ", self.dt)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_seven_texts(self):
        rows = re.findall(r"^\(300910, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), int(t), int(r)) for g, i, _, t, r in rows],
                         [(0, 0, 14, 0), (1, 0, 41, 3), (2, 0, 41, 3), (3, 0, 41, 3), (4, 0, 14, 0), (5, 0, 41, 3),
                          (6, 0, 14, 0)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts, ["Hands off the collection!", "%s unseals the Plague Cask!",
                                 "%s unseals the Kirin Tor Staff!", "%s unseals the Necromancer's Skull!",
                                 "Yes... I hear it now. Its power is mine!", "%s begins to channel the staff's power!",
                                 "The collection... must be... preserved..."])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 300910 AND `GroupID` BETWEEN 0 AND 6;",
                      self.sql)
        for name, group in (("SAY_PULL", 0), ("EMOTE_UNSEAL_CASK", 1), ("EMOTE_UNSEAL_STAFF", 2),
                            ("EMOTE_UNSEAL_SKULL", 3), ("SAY_TROPHY", 4), ("EMOTE_TORRENT", 5), ("SAY_DEATH", 6)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_SM_KELL, 0, 6, 0 \}")

    def test_the_case_objects_are_generic_not_selectable_and_use_one_display_each(self):
        expected = {301315: (7695, "kPedestalDisplay", visuals.GODI_RELIC_PEDESTAL),
                    301316: (288, "kCaskDisplay", visuals.GODI_RELIC_CASK),
                    301317: (1708, "kStaffDisplay", visuals.GODI_RELIC_STAFF),
                    301318: (217, "kSkullDisplay", visuals.GODI_RELIC_SKULL)}
        block = re.search(r"INSERT INTO `gameobject_template`.*?VALUES\n(.*?)\nON DUPLICATE KEY", self.sql, re.S)
        self.assertIsNotNone(block)
        rows = {}
        for match in re.finditer(r"^\((\d+),(?:.|\n)*?\)(?=,\n\(|\Z)", block.group(1), re.M):
            fields = event_items_test._split_tuple(match.group(0)[1:-1])
            self.assertEqual(len(fields), GO_COLUMN_COUNT, fields[:4])
            rows[fields[0]] = fields
        self.assertEqual(sorted(rows), sorted(expected))
        for entry, (display, const, visual) in expected.items():
            fields = rows[entry]
            self.assertEqual(fields[1], GENERIC, entry)
            self.assertEqual(fields[2], display, entry)
            self.assertEqual(fields[7], 1, entry)       # size: the template's `size` is index 7 after the 3 strings
            self.assertEqual(int(self._const(const)), display, const)
            self.assertEqual(visual, display, const)
        addon = re.findall(r"^\((\d+), 0, (\d+), 0, 0, 0, 0, 0, 0\)[,;]", self.sql, re.M)
        self.assertEqual([(int(e), int(f)) for e, f in addon], [(e, GO_FLAG_NOT_SELECTABLE) for e in sorted(expected)])
        self.assertIn("DELETE FROM `gameobject_template_addon` WHERE `entry` BETWEEN 301315 AND 301318;", self.sql)
        # no spawn: the boss summons the objects
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)
        self.assertIn("SummonGameObject(entry", self.script)

    def test_his_spawn_is_in_the_arena_on_both_difficulties(self):
        row = re.search(r"^\(3009100, 300910, 189, 0, 0, (\d+), 1, 0, ([-\d.]+), ([-\d.]+), ([-\d.]+), ([\d.]+), "
                        r"(\d+), 0,", self.sql, re.M)
        self.assertIsNotNone(row)
        self.assertEqual(int(row.group(1)), 3)              # normal and heroic (rule 14)
        x, y, z = (float(row.group(i)) for i in (2, 3, 4))
        spot = re.search(r"kKellSpot\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.header)
        self.assertEqual((x, y, z), tuple(float(spot.group(i)) for i in (1, 2, 3)))
        self.assertEqual(int(row.group(6)), 86400)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 300910 AND `guid` = 3009100;", self.sql)

    # --- the numbers the dbc-tools file pins --------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("UNSEAL_CAST_MS", "kUnsealCastMs"), ("TORRENT_CAST_MS", "kTorrentCastMs"),
                               ("CURSE_MS", "kCurseMs")):
            dt_value = int(re.search(rf"^{name} = (\d+)", self.dt, re.M).group(1))
            self.assertEqual(dt_value, int(self._const(expected)), name)
        for name, expected in (("kUnsealBeat", "{10000,20000},{8000,15000}"),
                               ("kStaffBeat", "{2000,8000},{2000,8000}"),
                               ("kSkullBeat", "{2000,12000},{2000,12000}"),
                               ("kCaneBeat", "{5000,10000},{5000,10000}")):
            found = re.search(rf"NH<Beat> {name}\{{(.*?)\}};", self.logic)
            self.assertIsNotNone(found, name)
            self.assertEqual(found.group(1).replace(" ", ""), expected, name)
        self.assertEqual(self._const("kSkeletonCap").replace(" ", ""), "4,0")
        self.assertEqual((self._const("kCloudRadiusYd"), self._const("kFlaskRadiusYd"), self._const("kLineWidthYd"),
                          self._const("kLineLengthYd")), ("8.f", "4.f", "4.f", "40.f"))
        self.assertEqual((int(self._const("kPoolMs")), int(self._const("kFlaskFlightMs")),
                          int(self._const("kLineWarnMs"))), (15000, 2000, 2000))


if __name__ == "__main__":
    unittest.main()
