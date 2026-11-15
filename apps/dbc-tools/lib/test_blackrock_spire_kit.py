"""
Blackrock Spire build WP-S0, the data skeleton: source/npcs/blackrock_spire/ against the Blackrock Spire skeleton's
C++ (modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h and the boss files).

Checks:
  - the wave switch agrees on both sides (BIND_WAVE_2 in _common.py, kWave2Bound in BlackrockSpireRework.h);
  - each of the fifteen reworked boss entries is bound by a creature_template_columns() edit to a script name that a
    src/BlackrockSpire/*.cpp registers (RegisterDungeonReworkCreatureAI), with SmartAI off, immunity 1972 (Emberseer
    1973), INSTANCE_BIND and a DamageModifier; a wave 2 boss is not edited while its wave is unbound;
  - its normal HealthModifier times its class base (level, unit_class; creature_classlevelstats basehp0) is the build
    spec's normal health at 5 players (handoff s3.6);
  - BlackrockSpireRework.h's spell slices tile the `blackrock_spire` spell reservation, and its new creature and
    gameobject ids sit in the reservation's blocks, wave 1 creatures below wave 2's;
  - a wave 2 script registers its AI only behind kWave2Bound (an unbound registered name logs "not assigned");
  - the Upper Spire Finder start (lfg_override(44) in source/world/lfg_classic_heroic.py), its entrance checkpoint
    (mod-dungeon-checkpoint's u_dungeon_checkpoint_2026_11_15_00.sql) and kUbrsFinderStart in BlackrockSpireRework.h
    are one spot, inside the rune-room self-start box kDragonspireHall (R-1-KIT K-m3: arrivals start the room check).

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_kit.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "BlackrockSpireRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

IMMUNITY_BOSS_STUN = 1972
IMMUNITY_EMBERSEER = 1973
INSTANCE_BIND = 0x1

# entry: (script name, normal health at 5 players, level, class base basehp0 at that level and unit_class, wave; live
# 2026-11-15)
BOSSES = {
    9196: ("boss_highlord_omokk_rework", 175_000, 57, 2784, 1),
    9236: ("boss_shadow_hunter_voshgajin_rework", 174_000, 58, 2297, 1),
    9237: ("boss_warmaster_voone_rework", 174_000, 58, 2871, 1),
    10596: ("boss_mother_smolderweb_rework", 165_000, 59, 2961, 1),
    10584: ("boss_urok_doomhowl_rework", 150_000, 60, 2442, 1),
    9736: ("boss_quartermaster_zigris_rework", 140_000, 59, 2961, 1),
    10220: ("boss_halycon_gizrul_rework", 120_000, 59, 2961, 1),
    10268: ("boss_halycon_gizrul_rework", 120_000, 60, 3052, 1),
    9568: ("boss_overlord_wyrmthalak_rework", 200_000, 60, 3052, 1),
    9816: ("boss_pyroguard_emberseer_rework", 175_000, 60, 3052, 2),
    10264: ("boss_solakar_flamewreath_rework", 175_000, 60, 3052, 2),
    10339: ("boss_gyth_rework", 140_000, 62, 3237, 2),
    10429: ("boss_rend_blackhand_rework", 160_000, 62, 3237, 2),
    10430: ("boss_the_beast_rework", 220_000, 62, 3237, 2),
    10363: ("boss_drakkisath_rework", 260_000, 62, 3237, 2),
}


def _dt_switch() -> bool:
    text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    found = re.findall(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", text, re.M)
    assert len(found) == 1, found
    return found[0] == "True"


def _cpp_switch() -> bool:
    found = re.findall(r"constexpr bool kWave2Bound = (true|false);", HEADER.read_text())
    assert len(found) == 1, found
    return found[0] == "true"


def _bound(entry: int) -> bool:
    return BOSSES[entry][4] == 1 or _dt_switch()


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


def _gated_scripts() -> set[str]:
    """Script names registered behind `if (kWave2Bound)`."""
    names = set()
    for path in MODULE_DIR.glob("*.cpp"):
        names.update(re.findall(r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\((\w+),", path.read_text()))
    return names


LFG_SOURCE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
CHECKPOINT_SQL = (REPO_ROOT / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"
                  / "u_dungeon_checkpoint_2026_11_15_00.sql")
_FLOAT = r"(-?\d+(?:\.\d*)?)f?"


def _ubrs_start_points() -> dict[str, tuple[float, float, float]]:
    """The UBRS start spot as each of its three copies states it (x, y, z)."""
    header = HEADER.read_text()
    cpp = re.findall(rf"Point3 constexpr kUbrsFinderStart\{{ {_FLOAT}, {_FLOAT}, {_FLOAT} \}};", header)
    lfg = re.findall(rf"lfg_override\(44,.*?position=\({_FLOAT}, {_FLOAT}, {_FLOAT},", LFG_SOURCE.read_text())
    sql = re.findall(rf"\(229, 0, 1, 0, {_FLOAT}, {_FLOAT}, {_FLOAT},", CHECKPOINT_SQL.read_text())
    out = {}
    for name, found in (("cpp", cpp), ("lfg", lfg), ("checkpoint", sql)):
        assert len(found) == 1, (name, found)
        out[name] = tuple(float(v) for v in found[0])
    return out


def _hall_box() -> tuple[float, float, float, float, float, float]:
    header = HEADER.read_text()
    box = re.findall(rf"Box2 constexpr kDragonspireHall\{{ {_FLOAT}, {_FLOAT}, {_FLOAT}, {_FLOAT} \}};", header)
    zmin = re.findall(rf"float constexpr kDragonspireHallZMin = {_FLOAT};", header)
    zmax = re.findall(rf"float constexpr kDragonspireHallZMax = {_FLOAT};", header)
    assert len(box) == 1 and len(zmin) == 1 and len(zmax) == 1, (box, zmin, zmax)
    min_x, max_x, min_y, max_y = (float(v) for v in box[0])
    return min_x, max_x, min_y, max_y, float(zmin[0]), float(zmax[0])


def _header_ints(pattern: str) -> list[int]:
    return [int(v) for v in re.findall(pattern, HEADER.read_text())]


class BlackrockSpireSkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.scripts = _registered_scripts()

    def test_the_wave_switch_agrees(self):
        self.assertEqual(_dt_switch(), _cpp_switch())

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _level, _base, _wave) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                if not _bound(entry):
                    self.assertIsNone(row, "a wave 2 boss stays stock until its wave")
                    continue
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                want_immunity = IMMUNITY_EMBERSEER if entry == 9816 else IMMUNITY_BOSS_STUN
                self.assertEqual(row["CreatureImmunitiesId"], want_immunity)
                self.assertEqual(row["flags_extra"], INSTANCE_BIND)
                self.assertGreater(float(row["DamageModifier"]), 0)

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, _level, base, _wave) in BOSSES.items():
            if not _bound(entry):
                continue
            with self.subTest(entry=entry):
                got = float(self.edits[entry]["HealthModifier"]) * base
                self.assertLessEqual(abs(got - health), 2, f"{got:.0f} vs {health}")

    def test_wave_1_declares_no_wave_2_entry(self):
        if _dt_switch():
            self.skipTest("wave 2 is bound")
        wave2 = {entry for entry, row in BOSSES.items() if row[4] == 2}
        self.assertFalse(wave2 & set(self.edits))

    def test_wave_2_scripts_register_only_when_bound(self):
        gated = _gated_scripts()
        for entry, (script, _health, _level, _base, wave) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertEqual(script in gated, wave == 2, "wave 2 registers behind kWave2Bound, wave 1 always")

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["blackrock_spire"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["blackrock_spire"]
        creatures = _header_ints(r"NPC_BRS_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_BRS_\w+\s*=\s*(\d+)")
        self.assertEqual(len(creatures), 26)
        self.assertEqual(len(gameobjects), 6)
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)
        # The heroic mint order (Scholomance R-A N-2): every wave 1 add below every wave 2 add.
        self.assertLess(max(v for v in creatures if v < 300730), min(v for v in creatures if v >= 300730))
        self.assertTrue(all(v <= 300729 or v >= 300730 for v in creatures))

    def test_the_ubrs_start_is_one_spot_inside_the_self_start_box(self):
        points = _ubrs_start_points()
        self.assertEqual(points["cpp"], points["lfg"])
        self.assertEqual(points["cpp"], points["checkpoint"])
        x, y, z = points["cpp"]
        min_x, max_x, min_y, max_y, z_min, z_max = _hall_box()
        # Inside on purpose (the self-start fires on arrival); a nudge across the west edge must be a deliberate edit.
        self.assertTrue(min_x <= x <= max_x and min_y <= y <= max_y and z_min <= z <= z_max, (points, _hall_box()))
        self.assertAlmostEqual(x - min_x, 0.25, places=4)


if __name__ == "__main__":
    unittest.main()
