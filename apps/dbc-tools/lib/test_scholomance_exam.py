"""
Scholomance build WP-S13, the Graduate Exam: source/npcs/scholomance/graduate_exam.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/GraduateExamLogic.h, graduate_exam.cpp, the instructors' examiner
registrations) and its SQL rev.

Checks:
  - the six Passing Grade auras sit in the slice, match GraduateExamLogic.h, follow the Instructor order and WP-V's
    icons, and are visible, not cancellable, kept through death and dropped on a map change;
  - the seven examiners bind their separate npc_sc_examiner_* names, each registered behind kWaveCBound in its
    instructor's file; their health is the build spec's (HealthModifier x class base = ExaminerHealth); heroic only:
    no difficulty_entry_1 and no override in source/world/dungeons/scholomance.py;
  - the paper's script is registered; the SQL rev spawns 301153 heroic only, tints every examiner and copies the
    Krastinov and Alexei texts.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_exam.py
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
HEADER = MODULE_DIR / "GraduateExamLogic.h"
SCRIPT = MODULE_DIR / "graduate_exam.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "scholomance.py"
PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"

SLICE = range(206365, 206385)
GRADES = range(206365, 206371)
ICONS = (92, 2741, 339, 221, 2319, 48)      # _visuals.py PASSING_GRADE_ICONS, Instructor order
CLASS_BASE = {1: 3052, 2: 2442, 8: 2136}    # level 60 elite class bases (exp 0)

ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
AURA_DUMMY = 4

# Examiner entry: (ScriptName, the instructor file registering it, ExaminerHealth).
EXAMINERS = {
    300548: ("npc_sc_examiner_malicia", "boss_instructor_malicia_rework.cpp", 80000),
    300549: ("npc_sc_examiner_krastinov", "boss_doctor_theolen_krastinov_rework.cpp", 80000),
    300550: ("npc_sc_examiner_polkelt", "boss_lorekeeper_polkelt_rework.cpp", 80000),
    300551: ("npc_sc_examiner_ravenian", "boss_the_ravenian_rework.cpp", 60000),
    300552: ("npc_sc_examiner_corvane", "boss_the_ravenian_rework.cpp", 20000),
    300553: ("npc_sc_examiner_alexei", "boss_lord_alexei_barov_rework.cpp", 80000),
    300554: ("npc_sc_examiner_illucia", "boss_lady_illucia_barov_rework.cpp", 80000),
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


def _sql_rev() -> str:
    for path in sorted(PENDING.glob("rev_*.sql")):
        text = path.read_text(encoding="utf-8")
        if "Scholomance build WP-S13" in text:
            return text
    raise AssertionError("no WP-S13 SQL rev in pending_db_world")


class GraduateExamDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates}
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_the_grades_sit_in_the_slice_and_match_the_header(self):
        self.assertEqual(sorted(self.spells), list(GRADES))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": sorted(self.spells)}), [])
        header_ids = [int(v) for v in re.findall(r"SPELL_GE_GRADE_\w+\s*=\s*(\d+),", self.header)]
        self.assertEqual(header_ids, list(GRADES))

    def test_the_grade_auras_are_displays(self):
        for spell_id, icon in zip(GRADES, ICONS):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(int(spell["spell_icon_id"]), icon)
                self.assertEqual(int(spell["duration_ms"]), -1)
                self.assertEqual(int(spell["effect1"]["apply_aura"]), AURA_DUMMY)
                self.assertTrue(int(spell["attributes"]) & ATTR0_NO_AURA_CANCEL)
                self.assertFalse(int(spell["attributes"]) & 0x40)        # not passive: the client must see it
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_ALLOW_AURA_WHILE_DEAD)
                self.assertTrue(_raw(spell, "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP)
                self.assertEqual(_raw(spell, "AttributesEx7") & 0x10000000, 0)      # never consolidated
                self.assertNotIn("$", (spell.get("raw_overrides") or {}).get("AuraDescription_Lang_enUS", ""))
                self.assertTrue(spell["name"].startswith("Passing Grade: "))

    def test_the_examiners(self):
        heroic = HEROIC.read_text(encoding="utf-8")
        for entry, (script, owner, health) in EXAMINERS.items():
            with self.subTest(entry=entry):
                t = self.templates[entry]
                self.assertEqual(t["ScriptName"], script)
                self.assertEqual(int(t["rank"]), 1)
                self.assertEqual(int(t["minlevel"]), 60)
                self.assertEqual(int(t["CreatureImmunitiesId"]), 1972)
                self.assertEqual(int(t["lootid"]), 0)
                self.assertEqual(int(t.get("difficulty_entry_1", 0) or 0), 0)
                self.assertAlmostEqual(CLASS_BASE[int(t["unit_class"])] * float(t["HealthModifier"]), health, delta=1)
                # Heroic only: no heroic template, no override.
                self.assertNotRegex(heroic, rf"\n\s*{entry}\s*:")
                cpp = (MODULE_DIR / owner).read_text(encoding="utf-8")
                self.assertRegex(cpp, rf"if \(kWaveCBound\)\s*(\n\s*|.)*RegisterDungeonReworkCreatureAI\({script},")
        self.assertEqual(int(self.templates[300552]["unit_flags"]) & 0x02000002, 0x02000002)    # seated first

    def test_the_paper_and_the_sql_rev(self):
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_sc_honors_paper,", self.cpp)
        text = _sql_rev()
        self.assertRegex(text, r"\(301153, 10, 210, '[^']+', '', '', '', 1, (0, ){24}'', 'go_sc_honors_paper', 0\)")
        # Heroic only, at kHonorsPaper.
        self.assertIn("(3011530, 301153, 289, 0, 0, 2, 1, 171.0, 8.0, 116.0,", text)
        self.assertIn("kHonorsPaper{ 171.0f, 8.0f, 116.0f }",
                      (MODULE_DIR / "ScholomanceRework.h").read_text(encoding="utf-8"))
        tinted = {int(e) for e in re.findall(r"^\((3005\d\d), 0, 0, 0, 0, 0, 3, '9617'\)", text, re.MULTILINE)}
        self.assertEqual(tinted, set(EXAMINERS))
        self.assertEqual({int(g) for g in re.findall(r"^\(300549, (\d+), 0, '", text, re.MULTILINE)}, {4, 5, 6, 7})
        self.assertEqual({int(g) for g in re.findall(r"^\(300553, (\d+), 0, '", text, re.MULTILINE)}, set(range(1, 8)))


if __name__ == "__main__":
    unittest.main()
