"""
Scholomance build WP-S6, Doctor Theolen Krastinov: source/npcs/scholomance/doctor_theolen_krastinov.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/KrastinovLogic.h, boss_doctor_theolen_krastinov_rework.cpp) and its SQL
rev (data/sql/updates/pending_db_world/rev_1794146498261709659.sql). R-B lead S-4.

Checks:
  - the spells sit in Krastinov's slice (206225-206241) and KrastinovLogic.h names the same ids;
  - the Work Bench 300538 is a VehicleId 6 prop (npc_sc_work_bench) whose slot 0 is Wrench Free 206227, the button the
    bot strategy (WP-PB) and the client bar read: 3 s cooldown, no GCD, bound to its spell script;
  - Saw Descending 206231 is the 1.5 s cut window (the Incision bar's length); the stacking auras' caps;
  - the scripted hits ignore caster modifiers; Stitched Wound is never saved; Backhand's range matches the header;
  - the Failed Patient 300539 links to its heroic 310115 and runs at the header's pace (about 6 s to the bench);
  - 11261 is bound with SmartAI off; the examiner script is registered only with wave C;
  - the seat's exit (vehicle_seat_addon 441) is the header's absolute spot.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_krastinov.py
"""

from __future__ import annotations

import math
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
HEADER = MODULE_DIR / "KrastinovLogic.h"
ROOM_HEADER = MODULE_DIR / "ScholomanceRework.h"
SCRIPT = MODULE_DIR / "boss_doctor_theolen_krastinov_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_1794146498261709659.sql"

SLICE = range(206225, 206250)
(HOOK, STRAPPED_DOWN, WRENCH_FREE, WRENCH_IMPACT, INCISION, INCISION_HIT, SAW_DESCENDING, SCALPEL_STAB,
 STITCHED_WOUND, KILLING_FRENZY, GRAFTED_EYES, GRAFTED_HEART_HEAL, GRAFTED_HEART, BACKHAND, BUTCHERS_REND,
 INFECTED_CLAWS, CLAW_AT_STRAPS) = range(206225, 206242)
KRASTINOV = 11261
WORK_BENCH = 300538
FAILED_PATIENT = 300539
FAILED_PATIENT_HEROIC = 310115

ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CU_AURA_CANNOT_BE_SAVED = 0x01000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
BASE_RUN_YD_PER_SEC = 7.0


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


def _header_number(name: str, text: str | None = None) -> float:
    text = HEADER.read_text(encoding="utf-8") if text is None else text
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", text)
    assert match, name
    return float(match.group(1))


def _header_point(name: str, text: str) -> tuple[float, ...]:
    match = re.search(rf"\b{name}\{{\s*([^}}]*)\}}", text)
    assert match, name
    return tuple(float(v.strip().rstrip("f")) for v in match.group(1).split(","))


class KrastinovDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.custom_attrs = {int(e["spell_id"]): int(e["attributes"]) for e in reg.custom_attrs
                            if int(e["spell_id"]) in SLICE}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates}
        cls.creature_spells = {(int(e["CreatureID"]), int(e["Index"])): int(e["Spell"])
                               for e in reg.creature_template_spells}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == KRASTINOV]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.room = ROOM_HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HOOK, CLAW_AT_STRAPS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_KR_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({SLICE.start + i for i in header_ids}, set(mine))

    def test_the_work_bench_is_the_vehicle_with_wrench_free_in_slot_zero(self):
        bench = self.templates[WORK_BENCH]
        self.assertEqual(int(bench["VehicleId"]), int(_header_number("kBenchVehicleId")))
        self.assertEqual(int(bench["VehicleId"]), 6)
        self.assertEqual(bench["ScriptName"], "npc_sc_work_bench")
        # A prop: the ArenaGuard nobody-inside check skips it while a patient's threat sits on it (R-B K-2).
        flags = int(bench["unit_flags"])
        self.assertTrue(flags & UNIT_FLAG_NON_ATTACKABLE and flags & UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(self.creature_spells[(WORK_BENCH, 0)], WRENCH_FREE)
        self.assertEqual(int(_header_number("kBenchSeat")), 0)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_work_bench,", self.cpp)

    def test_wrench_free_is_a_three_second_button_with_no_gcd(self):
        wrench = self.spells[WRENCH_FREE]
        self.assertEqual(wrench["cooldown_ms"], int(_header_number("kWrenchFreeCooldownMs")))
        self.assertEqual(wrench["cooldown_ms"], 3000)
        self.assertEqual(wrench["cast_time_ms"], 0)
        self.assertEqual(_raw(wrench, "StartRecoveryTime"), 0)
        self.assertEqual(_raw(wrench, "StartRecoveryCategory"), 0)
        self.assertIn((WRENCH_FREE, "spell_sc_krastinov_wrench_free"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sc_krastinov_wrench_free)", self.cpp)

    def test_the_cut_window_is_the_incision_bar(self):
        cast_ms = int(_header_number("kIncisionCastMs"))
        self.assertEqual(cast_ms, 1500)
        self.assertEqual(self.spells[SAW_DESCENDING]["duration_ms"], cast_ms)
        self.assertEqual(self.spells[INCISION]["cast_time_ms"], cast_ms)
        self.assertEqual(_raw(self.spells[INCISION], "InterruptFlags"), 0)     # not the group's kick

    def test_stacking_auras(self):
        self.assertEqual(_raw(self.spells[STRAPPED_DOWN], "CumulativeAura"), 4)     # 4 straps after the eyes
        self.assertEqual(_raw(self.spells[STITCHED_WOUND], "CumulativeAura"), 10)
        self.assertEqual(_raw(self.spells[GRAFTED_HEART], "CumulativeAura"), 10)
        self.assertEqual(_raw(self.spells[BUTCHERS_REND], "CumulativeAura"), int(_header_number("kRendMaxStacks")))

    def test_scripted_hits_ignore_caster_modifiers(self):
        for spell_id in (INCISION_HIT, SCALPEL_STAB, GRAFTED_HEART_HEAL, BACKHAND, BUTCHERS_REND, INFECTED_CLAWS):
            with self.subTest(spell=spell_id):
                self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        for spell_id in (INCISION_HIT, BACKHAND):
            self.assertIn((spell_id, "spell_sc_krastinov_ref_hit"), self.scripts)
        for spell_id in (BUTCHERS_REND, INFECTED_CLAWS):
            self.assertIn((spell_id, "spell_sc_krastinov_ref_dot"), self.scripts)

    def test_stitched_wound_is_never_saved(self):
        self.assertEqual(self.spells[STITCHED_WOUND]["duration_ms"], -1)
        self.assertTrue(self.custom_attrs.get(STITCHED_WOUND, 0) & CU_AURA_CANNOT_BE_SAVED)

    def test_backhand_range_matches_the_header(self):
        backhand = self.spells[BACKHAND]
        self.assertEqual(backhand["range_yards"], _header_number("kBackhandRangeYd"))
        self.assertGreaterEqual(backhand["range_yards"], 40.0)
        self.assertEqual(backhand["cast_time_ms"], int(_header_number("kBackhandCastMs")))
        self.assertIn("result == SPELL_CAST_OK", self.cpp)

    def test_the_failed_patient(self):
        ghoul = self.templates[FAILED_PATIENT]
        self.assertEqual(int(ghoul["difficulty_entry_1"]), FAILED_PATIENT_HEROIC)
        self.assertEqual(ghoul["ScriptName"], "npc_sc_failed_patient")
        # The chase runs, so speed_run sets the pace: about 6 s over the rise spot -> bench distance.
        pace = float(ghoul["speed_run"]) * BASE_RUN_YD_PER_SEC
        self.assertAlmostEqual(pace, _header_number("kFailedPatientYdPerSec"), delta=0.05)
        bench = _header_point("kWorkBenchGo", self.room)
        rise = _header_point("kFailedPatientRise", self.room)
        seconds = math.dist(bench[:2], rise[:2]) / pace
        self.assertTrue(5.0 < seconds < 7.0, seconds)
        self.assertNotIn("SetWalk(true)", self.cpp)

    def test_krastinov_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_doctor_theolen_krastinov_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 52.425)
        self.assertEqual(int(edit["flags_extra"]), 3)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_doctor_theolen_krastinov_rework,", self.cpp)

    def test_the_examiner_waits_for_wave_c(self):
        self.assertIn("struct npc_sc_examiner_krastinov : public ScriptedAI", self.cpp)
        self.assertRegex(self.cpp, r"if \(kWaveCBound\)\s*\n\s*RegisterDungeonReworkCreatureAI\("
                                   r"npc_sc_examiner_krastinov,")
        self.assertNotIn("RegisterKrastinovExaminer", self.cpp)
        self.assertEqual(int(_header_number("kExaminerHealth")), 80000)

    def test_the_lesson_is_registered(self):
        self.assertIn("RegisterSoloLesson(Classroom::HallOfTheDamned,", self.cpp)

    def test_the_seat_exit_is_the_absolute_spot(self):
        sql = SQL_REV.read_text(encoding="utf-8")
        match = re.search(r"INSERT INTO `vehicle_seat_addon` \([^)]*\) VALUES\s*\n\((\d+), ([^)]*)\);", sql)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), int(_header_number("kBenchVehicleSeatEntry")))
        _, x, y, z, _, value = (float(v) for v in match.group(2).split(","))
        self.assertEqual(int(value), 2)             # VehicleExitParamDest: an absolute spot
        self.assertEqual((x, y, z), _header_point("kBenchExit", self.header))


if __name__ == "__main__":
    unittest.main()
