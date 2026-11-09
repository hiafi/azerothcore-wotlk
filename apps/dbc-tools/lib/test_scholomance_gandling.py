"""
Scholomance build WP-S11, Darkmaster Gandling: source/npcs/scholomance/darkmaster_gandling.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/GandlingLogic.h, boss_darkmaster_gandling_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Gandling's slice and GandlingLogic.h names the same ids;
  - Honor Roll is the 15 s, +100% damage and healing buff (kHonorRollMs);
  - the lane hit and the linger are resolve copies (the registry deals them), the bars are not interruptible;
  - the Expelled Student 300544 links to its heroic 310119 and runs npc_sc_expelled_student;
  - the echo and both stalkers are helpers (not selectable or attackable, hostile faction 14), the stalkers TRIGGER
    with their do-nothing scripts, the echo with none (S8's contract);
  - 1853 is bound with SmartAI off; every ScriptName of this file is registered in the C++;
  - the SQL rev drops his SmartAI as a full block and adds texts 1-6 and the Expelled Student's rise;
  - every classroom has a lesson registered by its instructor's file.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_gandling.py
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
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "GandlingLogic.h"
SCRIPT = MODULE_DIR / "boss_darkmaster_gandling_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"
PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"

SLICE = range(206330, 206365)
DETENTION_CAST, PORTAL_FLASH, HONOR_ROLL, VOLLEY_CAST, VOLLEY_HIT, VOLLEY_STREAM, VOLLEY_LINGER, EXPELLED_GROWTH, \
    TRANSFER_MARK, VOLLEY_STREAM_GROUND = range(206330, 206340)
GANDLING = 1853
EXPELLED = 300544
EXPELLED_HEROIC = 310119
ECHO = 300545
LESSON_STALKER = 300546
PORTAL_STALKER = 300547

RESOLVE_SCRIPT = "spell_boss_mechanics_resolve"
AURA_MOD_DAMAGE_PERCENT_DONE = 79
AURA_MOD_HEALING_DONE_PERCENT = 136
UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
FLAGS_EXTRA_TRIGGER = 0x80

# The instructor files and the room each one registers a lesson for.
LESSONS = {
    "boss_instructor_malicia_rework.cpp": "Coven",
    "boss_doctor_theolen_krastinov_rework.cpp": "HallOfTheDamned",
    "boss_lorekeeper_polkelt_rework.cpp": "HallOfSecrets",
    "boss_the_ravenian_rework.cpp": "RavenianVault",
    "boss_lord_alexei_barov_rework.cpp": "BarovVault",
    "boss_lady_illucia_barov_rework.cpp": "ShadowVault",
}


def _load():
    t = id_blocks
    return registry.load_class_package(
        PACKAGE, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
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


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_number(name: str, text: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", text)
    assert match, name
    return float(match.group(1))


def _sql_rev() -> str:
    for path in sorted(PENDING.glob("rev_*.sql")):
        text = path.read_text(encoding="utf-8")
        if "Scholomance build WP-S11" in text:
            return text
    raise AssertionError("no WP-S11 SQL rev in pending_db_world")


class GandlingDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == GANDLING]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DETENTION_CAST, VOLLEY_STREAM_GROUND + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_GD_\w+\s*=\s*(\d+),", self.header)}
        self.assertEqual(header_ids, set(mine))

    def test_honor_roll(self):
        honor = self.spells[HONOR_ROLL]
        self.assertEqual(honor["duration_ms"], int(_header_number("kHonorRollMs", self.header)))
        self.assertEqual(honor["duration_ms"], 15000)
        auras = {(int(honor[k]["apply_aura"]), int(honor[k]["base_points"])) for k in ("effect1", "effect2")}
        self.assertEqual(auras, {(AURA_MOD_DAMAGE_PERCENT_DONE, 100), (AURA_MOD_HEALING_DONE_PERCENT, 100)})
        # Number-free aura text (custom-spells.md: $s1 did not render in game).
        self.assertNotIn("$", (honor.get("raw_overrides") or {}).get("AuraDescription_Lang_enUS", ""))

    def test_the_registry_deals_the_lanes(self):
        for spell_id in (VOLLEY_HIT, VOLLEY_LINGER):
            with self.subTest(spell=spell_id):
                self.assertIn((spell_id, RESOLVE_SCRIPT), self.scripts)
        for spell_id, ms in ((DETENTION_CAST, "kDetentionCastMs"), (VOLLEY_CAST, "kVolleyCastMs")):
            with self.subTest(bar=spell_id):
                self.assertEqual(self.spells[spell_id]["cast_time_ms"], int(_header_number(ms, self.header)))
                self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
        # The looks have a missile speed (a missile with no speed draws nothing).
        for spell_id in (VOLLEY_STREAM, VOLLEY_STREAM_GROUND):
            self.assertGreater(float((self.spells[spell_id].get("raw_overrides") or {}).get("Speed", 0)), 0)

    def test_the_expelled_student(self):
        expelled = self.templates[EXPELLED]
        self.assertEqual(int(expelled["difficulty_entry_1"]), EXPELLED_HEROIC)
        self.assertEqual(expelled["ScriptName"], "npc_sc_expelled_student")
        self.assertEqual(int(expelled["rank"]), 1)
        self.assertAlmostEqual(3052 * float(expelled["HealthModifier"]), 15000, delta=1)
        self.assertEqual(_raw(self.spells[EXPELLED_GROWTH], "CumulativeAura"), 99)

    def test_helpers(self):
        for entry in (ECHO, LESSON_STALKER, PORTAL_STALKER):
            with self.subTest(entry=entry):
                t = self.templates[entry]
                flags = int(t["unit_flags"])
                self.assertTrue(flags & UNIT_FLAG_NON_ATTACKABLE and flags & UNIT_FLAG_NOT_SELECTABLE)
                self.assertEqual(int(t["faction"]), 14)       # hostile: the lesson's spells hit the student
                self.assertEqual(int(t.get("difficulty_entry_1", 0) or 0), 0)
        self.assertEqual(self.templates[ECHO]["ScriptName"], "")
        for entry, name in ((LESSON_STALKER, "npc_sc_lesson_stalker"), (PORTAL_STALKER, "npc_sc_portal_stalker")):
            self.assertEqual(self.templates[entry]["ScriptName"], name)
            self.assertTrue(int(self.templates[entry]["flags_extra"]) & FLAGS_EXTRA_TRIGGER)

    def test_gandling_is_bound_and_every_script_registered(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_darkmaster_gandling_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(int(edit["CreatureImmunitiesId"]), 1972)
        for name in ("boss_darkmaster_gandling_rework", "npc_sc_expelled_student", "npc_sc_lesson_stalker",
                     "npc_sc_portal_stalker"):
            with self.subTest(script=name):
                self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)

    def test_the_sql_rev(self):
        text = _sql_rev()
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 1853 AND `source_type` = 0;", text)
        self.assertNotIn("INSERT INTO `smart_scripts`", text)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 1853 AND `GroupID` BETWEEN 1 AND 6;", text)
        groups = {int(g) for g in re.findall(r"^\(1853, (\d+), 0,", text, re.MULTILINE)}
        self.assertEqual(groups, set(range(1, 7)))
        self.assertRegex(text, r"\(1853, 2, 0, '[^']*', 41,")      # mechanic emotes are boss emotes
        self.assertRegex(text, r"\(1853, 3, 0, '[^']*', 41,")
        self.assertRegex(text, r"\(300544, 0, 0, .*, 41,")
        # R-C EXAM SF-2: the Volley and Transfer emotes reach the gauntlet's classrooms (TextRange 3, the map).
        for group in (2, 3):
            with self.subTest(group=group):
                self.assertRegex(text, rf"\(1853, {group}, 0, '[^']*', 41, 0, 100, 0, 0, 0, 0, 3,")

    def test_every_classroom_has_a_lesson(self):
        for name, room in LESSONS.items():
            with self.subTest(file=name):
                cpp = (MODULE_DIR / name).read_text(encoding="utf-8")
                self.assertRegex(cpp, rf"RegisterSoloLesson\(\s*Classroom::{room}\b")


if __name__ == "__main__":
    unittest.main()
