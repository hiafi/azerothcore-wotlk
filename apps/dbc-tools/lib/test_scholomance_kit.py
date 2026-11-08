"""
Scholomance build WP-KS, the data skeleton: source/npcs/scholomance/ against the Scholomance kit's C++
(modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h and the boss files).

Checks:
  - each of the twelve reworked bosses is bound by a creature_template_columns() edit to a script name that a
    src/Scholomance/*.cpp registers (RegisterDungeonReworkCreatureAI), with SmartAI off, stun immunity 1972 and
    INSTANCE_BIND (Krastinov keeps CIVILIAN too: 3);
  - its normal HealthModifier times its class base (level, unit_class; creature_classlevelstats basehp0) is the build
    spec's normal health (handoff s3.6; Marduk and Vectus each carry the shared pool's 300k);
  - ScholomanceRework.h's spell slices tile the `scholomance` spell reservation, and its new creature and gameobject
    ids sit in the reservation's blocks.

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_kit.py
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
HEADER = MODULE_DIR / "ScholomanceRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND, CIVILIAN = 0x1, 0x2

# entry: (script name, normal health, level, class base basehp0 at that level and unit_class; live 2026-11-08)
BOSSES = {
    10503: ("boss_jandice_barov_rework", 175_000, 61, 2515),
    11622: ("boss_rattlegore_rework", 185_000, 61, 2515),
    10433: ("boss_marduk_blackpool_rework", 300_000, 58, 2297),
    10432: ("boss_vectus_rework", 300_000, 60, 2442),
    10508: ("boss_ras_frostwhisper_rework", 195_000, 62, 2590),
    10505: ("boss_instructor_malicia_rework", 160_000, 60, 2442),
    11261: ("boss_doctor_theolen_krastinov_rework", 160_000, 60, 3052),
    10901: ("boss_lorekeeper_polkelt_rework", 175_000, 60, 3052),
    10507: ("boss_the_ravenian_rework", 160_000, 60, 3052),
    10504: ("boss_lord_alexei_barov_rework", 160_000, 60, 3052),
    10502: ("boss_lady_illucia_barov_rework", 160_000, 60, 2442),
    1853: ("boss_darkmaster_gandling_rework", 280_000, 61, 2515),
}

# The wave that binds each boss (R-A S-11): the six instructors are wave B, Gandling wave C.
WAVE = {10505: "B", 11261: "B", 10901: "B", 10507: "B", 10504: "B", 10502: "B", 1853: "C"}


def _dt_switches() -> dict[str, bool]:
    text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    return {w: v == "True" for w, v in re.findall(r"^BIND_WAVE_([BC])\s*=\s*(True|False)\s*$", text, re.M)}


def _cpp_switches() -> dict[str, bool]:
    return {w: v == "true" for w, v in re.findall(r"constexpr bool kWave([BC])Bound = (true|false);",
                                                   HEADER.read_text())}


def _bound(entry: int) -> bool:
    wave = WAVE.get(entry, "A")
    return wave == "A" or _dt_switches().get(wave, False)


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


def _registered_scripts() -> set[str]:
    names = set()
    for path in MODULE_DIR.glob("*.cpp"):
        names.update(re.findall(r"RegisterDungeonReworkCreatureAI\((\w+),", path.read_text()))
    return names


def _header_ints(pattern: str) -> list[int]:
    return [int(v) for v in re.findall(pattern, HEADER.read_text())]


class ScholomanceSkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.scripts = _registered_scripts()

    def test_the_wave_switches_agree(self):
        # R-A S-11: the DT side (BIND_WAVE_B / BIND_WAVE_C) and the C++ side (kWaveBBound / kWaveCBound) flip together.
        self.assertEqual(_dt_switches(), _cpp_switches())
        self.assertEqual(set(_dt_switches()), {"B", "C"})

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _level, _base) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                if not _bound(entry):
                    self.assertIsNone(row, "a later wave's boss stays stock until its wave")
                    continue
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                want = INSTANCE_BIND | (CIVILIAN if entry == 11261 else 0)
                self.assertEqual(row["flags_extra"], want)

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, _level, base) in BOSSES.items():
            if not _bound(entry):
                continue
            with self.subTest(entry=entry):
                got = float(self.edits[entry]["HealthModifier"]) * base
                self.assertLessEqual(abs(got - health), 2, f"{got:.0f} vs {health}")

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["scholomance"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["scholomance"]
        creatures = _header_ints(r"NPC_SC_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_SC_\w+\s*=\s*(\d+)")
        self.assertEqual(len(creatures), 25)
        self.assertEqual(len(gameobjects), 5)
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)


if __name__ == "__main__":
    unittest.main()
