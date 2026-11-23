"""
Scarlet Monastery build WP-D8H, Arcanist Doan's hard mode (the Kel'Thuzad Heresy):
source/npcs/scarlet_monastery/doan_hard_mode.py (the Phylactery Shard, the Risen Purged and the spells 212710-212715),
data/sql/updates/pending_db_world/rev_doan_hard_mode_scarlet_monastery.sql (Doan's lines 2-3, the four evidence pages:
page_text, gameobject templates and heroic spawns), and the C++ they must agree with (modules/mod-dungeon-bosses
src/ScarletMonastery/DoanHardModeLogic.h and doan_hard_mode.cpp).

Checks:
  - the six spells sit in the D8H slice and the C++ names the same ids; Icy Death is a Curse (8 s, 60% slow, 3% Frost a
    second through the kit's periodic percent script, ignores his modifiers); the red aura stays after combat; the
    shard's ward is a school immunity; the fissure is a Shadow resolve copy; every look is a V constant, none WRONG;
  - the shard and the Risen Purged: scripts, level 60, the hard mode health, H's heroic entries, displays;
  - the SQL: groups 2-3 of 6487 only (the spec's lines), the four pages' text (the designer's lines), the goober
    templates showing their page and bound to go_sm_evidence_page, the heroic-only spawns on the header's spots;
  - the numbers the dbc-tools file pins are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_doan_hard_mode.py
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
from lib import test_scarlet_monastery_vfx as vfx_test  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "DoanHardModeLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "doan_hard_mode.cpp"
DOAN_LOGIC = MDB / "src" / "ScarletMonastery" / "DoanLogic.h"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_doan_hard_mode_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "doan_hard_mode.py"

SLICE = range(212710, 212750)
FIRST = 212710
NAMES = ("SPELL_HERESY_ICY_DEATH", "SPELL_HERESY_AURA", "SPELL_HERESY_SHARD_WARD", "SPELL_HERESY_FISSURE",
         "SPELL_HERESY_FISSURE_LOOK", "SPELL_HERESY_RAISE_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_DECREASE_SPEED, AURA_SCHOOL_IMMUNITY = 4, 3, 33, 39
SCHOOL_FROST, SCHOOL_SHADOW = 16, 32
DISPEL_CURSE = 2
ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
SHARD, RISEN, DOAN = 300920, 300921, 6487
PAGES = (301320, 301321, 301322, 301323)
GOOBER = 10
GO_COLUMN_COUNT = 35        # entry, type, displayId, name, IconName, castBarCaption, unk1, size, Data0-23, 3 trailing

# LIB "Trigger, the evidence trail": the designer's lines, each page in order.
PAGE_LINES = (
    "By the Arcanist's order, six of the purged sent up to the Athenaeum. Unburned.",
    "Item 113. Phylactery shard, Stratholme. On loan to Arcanist Doan. Not returned.",
    "Kel'Thuzad and the Forming of the Scourge. Condemned, to be burned. Withheld by order of the Arcanist.",
    "He was not wrong.",
)


def _split_values(text: str) -> list:
    """A VALUES tuple's fields: quoted strings (with '' escapes), ints and floats."""
    out: list = []
    for match in re.finditer(r"'((?:[^']|'')*)'|(-?\d+\.\d+)|(-?\d+)", text):
        quoted, real, whole = match.groups()
        out.append(quoted.replace("''", "'") if quoted is not None else float(real) if real is not None
                   else int(whole))
    return out


class DoanHardModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.models = {}
        for e in reg.creature_template_models:
            cls.models.setdefault(int(e["CreatureID"]), []).append(e)
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.doan_logic = DOAN_LOGIC.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str, text: str | None = None) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", text or self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def _dt_int(self, name: str) -> int:
        match = re.search(rf"^{name} = (\d+)", self.dt, re.M)
        self.assertIsNotNone(match, name)
        return int(match.group(1))

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d8h_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsHeresy{ 212710, 212749 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_HERESY_RAISE_LOOK <= kSpellSlice\.last")

    def test_icy_death_is_a_curse_slow_and_frost_dot(self):
        icy = self.spells[FIRST]
        self.assertEqual(icy["school"], SCHOOL_FROST)
        self.assertEqual(icy["dispel"], DISPEL_CURSE)                               # a reward to remove
        self.assertEqual(icy["duration_ms"], 8000)
        self.assertEqual(int(self._const("kIcyDeathMs")), 8000)
        self.assertTrue(icy["attributes"] & 0x04000000)                            # a debuff
        slow, dot = icy["effect1"], icy["effect2"]
        self.assertEqual((slow["type"], slow["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_DECREASE_SPEED))
        self.assertEqual(slow["base_points"] + slow["die_sides"], -60)
        self.assertEqual(int(self._const("kIcyDeathSlowPct")), 60)
        self.assertEqual((dot["type"], dot["apply_aura"]), (EFFECT_APPLY_AURA, AURA_PERIODIC_DAMAGE))
        self.assertEqual(dot["base_points"] + dot["die_sides"], 300)              # 3% in hundredths
        self.assertEqual(dot["amplitude"], 1000)
        self.assertEqual(int(self._const("kIcyDeathHundredths")), 300)
        self.assertEqual(int(self._const("kIcyDeathTickMs")), 1000)
        raw = icy["raw_overrides"]
        self.assertEqual(raw["EffectMiscValueB_2"], 300)                           # heroic: the same
        self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)       # rule 2
        self.assertIn((FIRST, "spell_dungeon_refflat_periodic"), self.scripts)
        self.assertEqual(raw["SpellVisualID_1"], visuals.HM_ICY_DEATH)
        self.assertEqual(visuals.HM_ICY_DEATH, 2837)                                # Frostbite's state, never SV 13
        # the C++ rides it on the spec's five hits
        self.assertRegex(self.script,
                         r"IcyDeathRides\(static_cast<RiddenHit>\(hit\)\) \? uint32\(SPELL_HERESY_ICY_DEATH\)")
        self.assertIn(".Rider(SPELL_HERESY_ICY_DEATH)", self.script)               # Shadow Fissure

    def test_the_red_aura_holds_a_wipe(self):
        aura = self.spells[FIRST + 1]
        self.assertEqual((aura["effect1"]["type"], aura["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(aura["duration_ms"], -1)
        self.assertTrue(aura["raw_overrides"]["AttributesEx"] & ATTR1_AURA_STAYS_AFTER_COMBAT)
        self.assertEqual(aura["raw_overrides"]["SpellVisualID_1"], visuals.HM_RED_AURA)
        self.assertEqual(visuals.HM_RED_AURA, visuals.SV_RED_AURA)

    def test_the_shard_ward_and_the_fissure(self):
        ward = self.spells[FIRST + 2]
        self.assertEqual((ward["effect1"]["type"], ward["effect1"]["apply_aura"]),
                         (EFFECT_APPLY_AURA, AURA_SCHOOL_IMMUNITY))
        self.assertEqual(ward["effect1"]["misc_value"], 127)
        self.assertEqual((ward["dispel"], ward["mechanic"]), (0, 0))
        self.assertEqual(ward["duration_ms"], -1)
        self.assertIn("Condition::HasAura(SPELL_HERESY_SHARD_WARD)", self.script)  # the bots ignore it warded
        fissure = self.spells[FIRST + 3]
        self.assertEqual(fissure["school"], SCHOOL_SHADOW)
        self.assertEqual(fissure["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertIn((FIRST + 3, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertTrue(fissure["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(self._const("kFissurePct"), "60.f")
        self.assertEqual(self._const("kFissureRadiusYd"), "6.f")

    def test_the_looks_use_the_v_constants_and_none_is_wrong(self):
        for offset, visual in ((0, visuals.HM_ICY_DEATH), (1, visuals.HM_RED_AURA), (2, visuals.DN_BUBBLE),
                               (4, visuals.HM_FISSURE_ALT), (5, visuals.HM_RAISE)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        for spell_id, spell in self.spells.items():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1", 0), vfx_test.WRONG_SPELL_VISUALS,
                             spell_id)
        self.assertEqual(self.spells[FIRST + 4]["duration_ms"], -1)              # a stalker's lasting look

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_phylactery_shard(self):
        c = self.creatures[SHARD]
        self.assertEqual(c["name"], "Phylactery Shard")
        self.assertEqual(c["ScriptName"], "npc_sm_phylactery_shard")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"]), (60, 60, 1, 67))
        self.assertAlmostEqual(c["HealthModifier"] * 3052, 15625, delta=5)     # HANDOFF s10 option D (spec 25k)
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["unit_flags"], 0)
        self.assertEqual((c["lootid"], c["flags_extra"]), (0, 0x40))
        self.assertIn(c["difficulty_entry_1"], (0, 310474))                         # H's table, once it settles
        self.assertEqual([m["CreatureDisplayID"] for m in self.models[SHARD]], [visuals.DISPLAY_PHYLACTERY_SHARD])
        self.assertEqual(visuals.DISPLAY_PHYLACTERY_SHARD, 24889)
        self.assertIn("creature_template(300920, ", self.dt)        # H finds the kit adds by this literal pattern
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(npc_sm_phylactery_shard, "
                                      r"ScarletMonasteryRework::kInstanceScriptName\)")
        # relative to D8's heroic anchor (5k, HANDOFF s10 option D): 1.25 x and 2.5 x
        self.assertEqual(self._const("kAnchorScale"), "1.25f")
        self.assertEqual(self._const("kShardToAnchor"), "2.5f")
        heroic_anchor = int(self._const("kAnchorHealthHeroic", self.doan_logic))
        self.assertEqual(heroic_anchor * 1.25 * 2.5, self._dt_int("SHARD_HEALTH"))

    def test_the_risen_purged(self):
        c = self.creatures[RISEN]
        self.assertEqual(c["name"], "Risen Purged")
        self.assertEqual(c["ScriptName"], "npc_sm_risen_purged")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["faction"], c["type"]), (60, 60, 67, 6))
        self.assertAlmostEqual(c["HealthModifier"] * 3052, 6000, delta=5)
        self.assertEqual(int(self._const("kRisenHealth")), self._dt_int("RISEN_HEALTH"))
        self.assertEqual(c["CreatureImmunitiesId"], 0)                              # a slow or a root holds them
        self.assertEqual((c["lootid"], c["flags_extra"]), (0, 0x40))
        self.assertIn(c["difficulty_entry_1"], (0, 310475))                         # H's table, once it settles
        self.assertEqual(sorted(m["CreatureDisplayID"] for m in self.models[RISEN]),
                         sorted((visuals.DISPLAY_RISEN_PURGED, visuals.DISPLAY_RISEN_PURGED_ALT)))
        self.assertIn("creature_template(300921, ", self.dt)
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(npc_sm_risen_purged, "
                                      r"ScarletMonasteryRework::kInstanceScriptName\)")

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [SHARD, RISEN], "gameobject": list(PAGES)}), [])
        self.assertRegex(self.header, r"NPC_SM_PHYLACTERY_SHARD\s*=\s*300920,")
        self.assertRegex(self.header, r"NPC_SM_RISEN_PURGED\s*=\s*300921,")
        for n, entry in enumerate(PAGES, 1):
            self.assertRegex(self.header, rf"GO_SM_EVIDENCE_PAGE_{n}\s*=\s*{entry},")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_two_lines(self):
        rows = re.findall(r"^\(6487, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(i), t.replace("''", "'"), int(ty), int(r)) for g, i, t, ty, r in rows], [
            (2, 0, "Found my secrets, have you? Let me show you the result!", 14, 2),
            (3, 0, "Rise, my purged! The Light never wanted you!", 14, 0),
        ])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 6487 AND `GroupID` BETWEEN 2 AND 3;",
                      self.sql)
        self.assertRegex(self.doan_logic, r"SAY_HERESY\s*=\s*2,")
        self.assertRegex(self.doan_logic, r"SAY_RISE_PURGED\s*=\s*3,")
        self.assertIn("doan->AI()->Talk(SmDoan::SAY_HERESY)", self.script)
        self.assertIn("doan->AI()->Talk(SmDoan::SAY_RISE_PURGED)", self.script)

    def test_the_page_texts(self):
        flat = self.sql.replace("''", "'")
        for entry, line in zip(PAGES, PAGE_LINES):
            match = re.search(rf"^\({entry}, CONCAT\((.*?)\), 0, 0\)", flat, re.M | re.S)
            self.assertIsNotNone(match, entry)
            self.assertIn(line, match.group(1), entry)
        self.assertIn("DELETE FROM `page_text` WHERE `ID` BETWEEN 301320 AND 301323;", self.sql)

    def test_the_page_templates_are_goobers_that_show_their_page(self):
        block = re.search(r"INSERT INTO `gameobject_template`.*?VALUES\n(.*?)\nON DUPLICATE KEY", self.sql, re.S)
        self.assertIsNotNone(block)
        tuples = re.findall(r"\((\d+, .*?)\)(?:,|$)", block.group(1).replace("\n", " "))
        self.assertEqual(len(tuples), 4)
        books = {301320, 301323}
        for text in tuples:
            fields = _split_values(text)
            self.assertEqual(len(fields), GO_COLUMN_COUNT)
            entry = fields[0]
            self.assertIn(entry, PAGES)
            self.assertEqual(fields[1], GOOBER)
            self.assertEqual(fields[2], visuals.GODI_EVIDENCE_BOOK if entry in books else visuals.GODI_EVIDENCE_SCROLL)
            self.assertEqual(fields[8], 0)                                  # Data0: no lock
            self.assertEqual(fields[8 + 7], entry)                         # Data7: the page_text id
            self.assertEqual(fields[8 + 10], 0)                            # Data10: no spell
            self.assertEqual(fields[-2], "go_sm_evidence_page")
        self.assertRegex(self.script, r"RegisterDungeonReworkGameObjectAI\(go_sm_evidence_page, "
                                      r"ScarletMonasteryRework::kInstanceScriptName\)")

    def test_the_spawns_are_heroic_only_on_the_header_spots(self):
        spots = {}
        for m in re.finditer(r"\{ ScarletMonasteryRework::GO_SM_EVIDENCE_PAGE_(\d), (\d+), "
                             r"\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.logic):
            spots[int(m.group(2))] = (float(m.group(3)), float(m.group(4)), float(m.group(5)))
        self.assertEqual(sorted(spots), list(PAGES))
        rows = re.findall(r"^\((\d+), (3013\d\d), 189, 0, 0, (\d), 1, ([-\d.]+), ([-\d.]+), ([-\d.]+), ", self.sql,
                          re.M)
        self.assertEqual(len(rows), 4)
        for guid, entry, mask, x, y, z in rows:
            self.assertEqual(int(guid), int(entry) * 10)
            self.assertEqual(int(mask), 2)                                  # heroic only
            self.assertEqual((float(x), float(y), float(z)), spots[int(entry)])
        # section 7 #27 A
        self.assertEqual(spots[301320], (156.0, -241.0, 19.2))
        self.assertEqual(spots[301322], (276.2, -428.2, 18.7))
        self.assertEqual(spots[301323][:2], (219.0, -424.0))

    def test_no_line_over_120_columns(self):
        for path in (SQL, DT_FILE, LOGIC, SCRIPT):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{n}")


if __name__ == "__main__":
    unittest.main()
